from __future__ import annotations

from datetime import date, datetime, timezone
import json
from pathlib import Path
import unittest

from a_stock_quant.data_contracts import DataContractError, QualityStatus
from a_stock_quant.data_readiness import (
    DataReadinessEngine,
    EvidenceStatus,
    ReadinessDimension,
    ReadinessStatus,
    load_data_readiness_policy,
)
from a_stock_quant.data_readiness_evidence import (
    EvidenceBuildContext,
    StandardQueryEvidenceBuilder,
    StandardQueryReadinessService,
    load_evidence_rule_config,
)
from a_stock_quant.standard_data_service import (
    ProviderDescriptor,
    StandardDataQuery,
    StandardDataRecord,
    StandardDataUsage,
    StandardQueryMetadata,
    StandardQueryResult,
)

ROOT = Path(__file__).resolve().parents[1]
RULES = ROOT / 'configs/quality/data_readiness_evidence_rules_v0.json'
POLICY = ROOT / 'configs/quality/data_readiness_policy_v0.json'


def descriptor(dataset_id: str = 'a_stock_daily_k', provider_id: str = 'provider') -> ProviderDescriptor:
    return ProviderDescriptor(provider_id, dataset_id, ('DailyBar',), 'coverage-v1', 'mapping-v1', '0.6.0')


def result(*, status: QualityStatus = QualityStatus.PASSED, blocks: bool = False, records: tuple[StandardDataRecord, ...] | None = None, warnings: tuple[str, ...] = (), as_of: date | None = date(2026, 6, 27), usage: StandardDataUsage = StandardDataUsage.CURRENT_SNAPSHOT_RESEARCH, provider_id: str = 'provider') -> StandardQueryResult:
    if records is None:
        records = (StandardDataRecord('DailyBar', {'instrument_id':'000001','trade_date':date(2026,6,27)}, {'instrument_id':'000001','trade_date':date(2026,6,27),'close_raw_cny':10.0}, 'source:1', {}, (), ({'canonical_field':'close_raw_cny','source_fields':['close']},)),)
    q = StandardDataQuery('a_stock_daily_k','DailyBar',('000001',),date(2026,6,27),date(2026,6,27),as_of_date=as_of,usage=usage,decision_time=(datetime(2026,6,27,15,0,tzinfo=timezone.utc) if usage is StandardDataUsage.MANUAL_DECISION_SUPPORT else None))
    m = StandardQueryMetadata('a_stock_daily_k','DailyBar',provider_id,'coverage-v1','mapping-v1','0.6.0',len(records),len(records),status,blocks,warnings,{},sum(len(r.lineage) for r in records))
    return StandardQueryResult(q,m,records)


class EvidenceAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.rules = load_evidence_rule_config(RULES)
        self.builder = StandardQueryEvidenceBuilder(self.rules)
        self.engine = DataReadinessEngine(load_data_readiness_policy(POLICY))
        self.service = StandardQueryReadinessService(self.engine, self.builder)

    def evidence(self, dimension: ReadinessDimension, *, source=None, context=None):
        items = self.builder.build(source or result(), descriptor(), context)
        return next(x for x in items if x.dimension is dimension)

    def test_contract_passes_when_versions_match(self):
        self.assertEqual(self.evidence(ReadinessDimension.CONTRACT).status, EvidenceStatus.PASSED)

    def test_contract_mismatch_fails(self):
        e = self.evidence(ReadinessDimension.CONTRACT, source=result(provider_id='other'))
        self.assertEqual(e.status, EvidenceStatus.FAILED)

    def test_query_warning_maps_to_warning(self):
        e = self.evidence(ReadinessDimension.QUERY_EXECUTION, source=result(status=QualityStatus.WARNING))
        self.assertEqual(e.status, EvidenceStatus.WARNING)

    def test_blocked_query_maps_to_failed(self):
        e = self.evidence(ReadinessDimension.QUERY_EXECUTION, source=result(status=QualityStatus.FAILED, blocks=True))
        self.assertEqual(e.status, EvidenceStatus.FAILED)

    def test_empty_result_fails_coverage(self):
        e = self.evidence(ReadinessDimension.COVERAGE, source=result(records=()))
        self.assertEqual(e.status, EvidenceStatus.FAILED)

    def test_query_scope_coverage_is_warning(self):
        e = self.evidence(ReadinessDimension.COVERAGE)
        self.assertEqual(e.status, EvidenceStatus.WARNING)
        self.assertEqual(e.code, 'QUERY_SCOPE_COVERAGE_ONLY')

    def test_proven_coverage_passes(self):
        e = self.evidence(ReadinessDimension.COVERAGE, context=EvidenceBuildContext(coverage_scope_proven=True))
        self.assertEqual(e.status, EvidenceStatus.PASSED)

    def test_partial_coverage_warns(self):
        e = self.evidence(ReadinessDimension.COVERAGE, context=EvidenceBuildContext(expected_entity_count=2, observed_entity_count=1, coverage_scope_proven=True))
        self.assertEqual(e.status, EvidenceStatus.WARNING)

    def test_query_scope_freshness_is_warning(self):
        e = self.evidence(ReadinessDimension.FRESHNESS)
        self.assertEqual(e.status, EvidenceStatus.WARNING)

    def test_proven_freshness_passes(self):
        e = self.evidence(ReadinessDimension.FRESHNESS, context=EvidenceBuildContext(expected_through_date=date(2026,6,27),latest_available_date=date(2026,6,27),freshness_scope_proven=True))
        self.assertEqual(e.status, EvidenceStatus.PASSED)

    def test_stale_freshness_warns(self):
        e = self.evidence(ReadinessDimension.FRESHNESS, context=EvidenceBuildContext(expected_through_date=date(2026,6,27),latest_available_date=date(2026,6,25),freshness_scope_proven=True))
        self.assertEqual(e.status, EvidenceStatus.WARNING)

    def test_complete_lineage_passes(self):
        self.assertEqual(self.evidence(ReadinessDimension.LINEAGE).status, EvidenceStatus.PASSED)

    def test_missing_lineage_fails(self):
        r = StandardDataRecord('DailyBar', {'instrument_id':'000001','trade_date':date(2026,6,27)}, {'instrument_id':'000001','trade_date':date(2026,6,27)}, None, {}, (), ())
        self.assertEqual(self.evidence(ReadinessDimension.LINEAGE, source=result(records=(r,))).status, EvidenceStatus.FAILED)

    def test_as_of_boundary_passes_temporal(self):
        self.assertEqual(self.evidence(ReadinessDimension.TEMPORAL_SAFETY).status, EvidenceStatus.PASSED)

    def test_temporal_warning_marker_warns(self):
        e = self.evidence(ReadinessDimension.TEMPORAL_SAFETY, source=result(warnings=('SOURCE_SNAPSHOT_TIME_UNAVAILABLE',)))
        self.assertEqual(e.status, EvidenceStatus.WARNING)

    def test_explicit_temporal_unknown_is_used(self):
        e = self.evidence(ReadinessDimension.TEMPORAL_SAFETY, context=EvidenceBuildContext(temporal_status=EvidenceStatus.UNKNOWN))
        self.assertEqual(e.status, EvidenceStatus.UNKNOWN)

    def test_quality_flag_warns_semantic(self):
        rec = result().records[0]
        flagged = StandardDataRecord(rec.canonical_object, rec.primary_key, rec.values, rec.source_record_id, {}, ('UNIT_UNCONFIRMED',), rec.lineage)
        self.assertEqual(self.evidence(ReadinessDimension.SEMANTIC_CONFIDENCE, source=result(records=(flagged,))).status, EvidenceStatus.WARNING)

    def test_clean_semantics_pass(self):
        self.assertEqual(self.evidence(ReadinessDimension.SEMANTIC_CONFIDENCE).status, EvidenceStatus.PASSED)

    def test_unverified_activation_warns(self):
        self.assertEqual(self.evidence(ReadinessDimension.ACTIVATION).status, EvidenceStatus.WARNING)

    def test_verified_activation_passes(self):
        e = self.evidence(ReadinessDimension.ACTIVATION, context=EvidenceBuildContext(activation_verified=True))
        self.assertEqual(e.status, EvidenceStatus.PASSED)

    def test_current_snapshot_is_warning_but_usable(self):
        snap = self.service.assess(result(), descriptor())
        self.assertEqual(snap.decision.status, ReadinessStatus.WARNING)
        self.assertFalse(snap.decision.blocks_downstream)
        snap.assert_usable()

    def test_strict_historical_is_blocked_by_unproven_scope(self):
        snap = self.service.assess(result(usage=StandardDataUsage.STRICT_HISTORICAL_BACKTEST), descriptor())
        self.assertEqual(snap.decision.status, ReadinessStatus.BLOCKED)
        with self.assertRaises(DataContractError): snap.assert_usable()

    def test_all_external_evidence_can_pass(self):
        ctx = EvidenceBuildContext(coverage_scope_proven=True,freshness_scope_proven=True,activation_verified=True,temporal_status=EvidenceStatus.PASSED,semantic_status=EvidenceStatus.PASSED)
        snap = self.service.assess(result(), descriptor(), ctx)
        self.assertEqual(snap.decision.status, ReadinessStatus.PASSED)

    def test_snapshot_contains_eight_dimensions_and_serialises(self):
        snap = self.service.assess(result(), descriptor())
        self.assertEqual(len(snap.evidence), 8)
        json.dumps(snap.to_dict(), ensure_ascii=False)


if __name__ == '__main__': unittest.main()
