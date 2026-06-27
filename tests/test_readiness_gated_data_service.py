from __future__ import annotations

from datetime import date
import json
from pathlib import Path
import unittest

from a_stock_quant.data_contracts import (
    DataContractError,
    QualityStatus,
)
from a_stock_quant.data_readiness import (
    DataReadinessEngine,
    EvidenceStatus,
    ReadinessDimension,
    ReadinessEvidence,
    ReadinessStatus,
    load_data_readiness_policy,
)
from a_stock_quant.data_readiness_evidence import (
    EvidenceRuleConfig,
    StandardQueryEvidenceBuilder,
    StandardQueryReadinessService,
)
from a_stock_quant.readiness_gated_data_service import (
    READINESS_GATED_SERVICE_VERSION,
    ReadinessGatedStandardDataService,
)
from a_stock_quant.standard_data_service import (
    ProviderDescriptor,
    StandardDataQuery,
    StandardDataRecord,
    StandardDataService,
    StandardDataUsage,
    StandardDatasetProvider,
    StandardQueryMetadata,
    StandardQueryResult,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = (
    PROJECT_ROOT
    / "configs"
    / "quality"
    / "data_readiness_policy_v0.json"
)


class FakeProvider(StandardDatasetProvider):
    def __init__(
        self,
        *,
        status: QualityStatus = QualityStatus.PASSED,
        blocks_downstream: bool = False,
        warnings: tuple[str, ...] = (),
    ) -> None:
        self.status = status
        self.blocks_downstream = blocks_downstream
        self.warnings = warnings

    @property
    def descriptor(self) -> ProviderDescriptor:
        return ProviderDescriptor(
            provider_id="dolphindb_daily_k_standard_provider",
            dataset_id="a_stock_daily_k",
            supported_objects=("DailyBar",),
            coverage_version="daily-k@2026-05-29",
            mapping_version="test-mapping",
            dictionary_revision="0.6.0",
        )

    def query(
        self,
        request: StandardDataQuery,
    ) -> StandardQueryResult:
        record = StandardDataRecord(
            canonical_object="DailyBar",
            primary_key={
                "instrument_id": request.instrument_ids[0],
                "trade_date": request.end_date,
            },
            values={
                "instrument_id": request.instrument_ids[0],
                "trade_date": request.end_date,
                "close": 10.0,
            },
            source_record_id=(
                f"{request.instrument_ids[0]}|"
                f"{request.end_date.isoformat()}"
            ),
            lineage=(
                {
                    "target_object": "DailyBar",
                    "canonical_field": "close",
                    "source_fields": ["close"],
                    "transform_id": "identity",
                },
            ),
        )
        return StandardQueryResult(
            query=request,
            metadata=StandardQueryMetadata(
                dataset_id=request.dataset_id,
                canonical_object=request.canonical_object,
                provider_id=self.descriptor.provider_id,
                coverage_version=self.descriptor.coverage_version,
                mapping_version=self.descriptor.mapping_version,
                dictionary_revision=self.descriptor.dictionary_revision,
                source_row_count=1,
                result_count=1,
                status=self.status,
                blocks_downstream=self.blocks_downstream,
                warnings=self.warnings,
                lineage_item_count=1,
            ),
            records=(record,),
        )


class FixedEvidenceBuilder(StandardQueryEvidenceBuilder):
    def __init__(
        self,
        overrides: dict[
            ReadinessDimension,
            EvidenceStatus,
        ] | None = None,
    ) -> None:
        super().__init__(
            EvidenceRuleConfig(
                rules_version="test-rules",
                entity_key_candidates=("instrument_id",),
                date_field_candidates=("trade_date",),
                temporal_warning_markers=("TEMPORAL",),
            )
        )
        self.overrides = overrides or {}

    def build(
        self,
        result: StandardQueryResult,
        descriptor: ProviderDescriptor,
        context=None,
    ) -> tuple[ReadinessEvidence, ...]:
        evidence: list[ReadinessEvidence] = []
        for dimension in ReadinessDimension:
            status = self.overrides.get(
                dimension,
                EvidenceStatus.PASSED,
            )
            evidence.append(
                ReadinessEvidence(
                    dimension=dimension,
                    status=status,
                    code=(
                        "TEST_PASSED"
                        if status is EvidenceStatus.PASSED
                        else "TEST_WARNING"
                    ),
                    message="门禁组合测试证据。",
                    evidence_refs=(
                        f"query:{result.metadata.query_id}",
                    ),
                )
            )
        return tuple(evidence)


class ReadinessGatedServiceTests(unittest.TestCase):
    def request(
        self,
        usage: StandardDataUsage = (
            StandardDataUsage.CURRENT_SNAPSHOT_RESEARCH
        ),
    ) -> StandardDataQuery:
        return StandardDataQuery(
            dataset_id="a_stock_daily_k",
            canonical_object="DailyBar",
            instrument_ids=("000001",),
            start_date=date(2026, 5, 29),
            end_date=date(2026, 5, 29),
            as_of_date=date(2026, 6, 27),
            usage=usage,
        )

    def service(
        self,
        *,
        provider: FakeProvider | None = None,
        builder: FixedEvidenceBuilder | None = None,
    ) -> ReadinessGatedStandardDataService:
        standard = StandardDataService()
        standard.register_provider(provider or FakeProvider())
        readiness = StandardQueryReadinessService(
            DataReadinessEngine(
                load_data_readiness_policy(POLICY_PATH)
            ),
            builder or FixedEvidenceBuilder(),
        )
        return ReadinessGatedStandardDataService(
            standard,
            readiness,
        )

    def test_all_passed_is_usable(self) -> None:
        result = self.service().query(self.request())
        self.assertFalse(result.blocks_downstream)
        self.assertEqual(
            result.readiness_snapshot.decision.status,
            ReadinessStatus.PASSED,
        )
        result.assert_usable()

    def test_current_research_warning_is_usable(self) -> None:
        service = self.service(
            builder=FixedEvidenceBuilder(
                {
                    ReadinessDimension.SEMANTIC_CONFIDENCE:
                    EvidenceStatus.WARNING,
                }
            )
        )
        result = service.query(self.request())
        self.assertFalse(result.blocks_downstream)
        self.assertEqual(
            result.readiness_snapshot.decision.status,
            ReadinessStatus.WARNING,
        )
        result.assert_usable()

    def test_strict_historical_warning_is_blocked(self) -> None:
        service = self.service(
            builder=FixedEvidenceBuilder(
                {
                    ReadinessDimension.SEMANTIC_CONFIDENCE:
                    EvidenceStatus.WARNING,
                }
            )
        )
        result = service.query(
            self.request(
                StandardDataUsage.STRICT_HISTORICAL_BACKTEST
            )
        )
        self.assertTrue(result.blocks_downstream)
        self.assertEqual(
            result.readiness_snapshot.decision.status,
            ReadinessStatus.BLOCKED,
        )
        with self.assertRaises(DataContractError):
            result.assert_usable()

    def test_provider_block_cannot_be_bypassed(self) -> None:
        service = self.service(
            provider=FakeProvider(
                status=QualityStatus.FAILED,
                blocks_downstream=True,
                warnings=("provider blocked",),
            )
        )
        result = service.query(self.request())
        self.assertTrue(result.blocks_downstream)
        with self.assertRaises(DataContractError):
            result.assert_usable()

    def test_readiness_failure_cannot_be_bypassed(self) -> None:
        service = self.service(
            builder=FixedEvidenceBuilder(
                {
                    ReadinessDimension.LINEAGE:
                    EvidenceStatus.FAILED,
                }
            )
        )
        result = service.query(self.request())
        self.assertTrue(result.blocks_downstream)
        with self.assertRaises(DataContractError):
            result.assert_usable()

    def test_query_id_is_preserved(self) -> None:
        result = self.service().query(self.request())
        self.assertEqual(
            result.standard_result.metadata.query_id,
            result.readiness_snapshot.query_id,
        )

    def test_provider_id_is_preserved(self) -> None:
        result = self.service().query(self.request())
        self.assertEqual(
            result.standard_result.metadata.provider_id,
            result.readiness_snapshot.provider_id,
        )

    def test_to_dict_is_json_serialisable(self) -> None:
        result = self.service().query(self.request())
        payload = result.to_dict()
        json.dumps(payload, ensure_ascii=False)
        self.assertEqual(
            payload["service_version"],
            READINESS_GATED_SERVICE_VERSION,
        )
        self.assertFalse(payload["blocks_downstream"])

    def test_wrong_standard_service_type_is_rejected(self) -> None:
        readiness = StandardQueryReadinessService(
            DataReadinessEngine(
                load_data_readiness_policy(POLICY_PATH)
            ),
            FixedEvidenceBuilder(),
        )
        with self.assertRaises(DataContractError):
            ReadinessGatedStandardDataService(
                object(),  # type: ignore[arg-type]
                readiness,
            )

    def test_wrong_readiness_service_type_is_rejected(self) -> None:
        standard = StandardDataService()
        with self.assertRaises(DataContractError):
            ReadinessGatedStandardDataService(
                standard,
                object(),  # type: ignore[arg-type]
            )


if __name__ == "__main__":
    unittest.main()
