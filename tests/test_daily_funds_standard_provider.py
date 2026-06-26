from __future__ import annotations

import unittest
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from a_stock_quant.data_contracts import DataContractError, QualityStatus
from a_stock_quant.daily_funds_standard_provider import (
    DailyFundsStandardDataProvider,
    build_daily_funds_standard_providers,
    register_daily_funds_standard_providers,
)
from a_stock_quant.dolphindb_daily_funds_service import (
    DailyFundsCanonicalRecord,
    DailyFundsStandardBatch,
)
from a_stock_quant.standard_data_service import (
    ENTITY_SELECTOR_MODE,
    INSTRUMENT_SELECTOR_MODE,
    StandardDataQuery,
    StandardDataService,
    StandardDataUsage,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class FakeCanonicalService:
    coverage_version = "daily-funds-test"
    mapping_version = "0.2.0"
    dictionary_revision = "0.6.0"

    def __init__(self) -> None:
        self.requests: list[Any] = []
        self.profiles = {
            "hq": {"canonical_object": "DailyBar", "selector_mode": "INSTRUMENT_ID"},
            "kphq": {"canonical_object": "AuctionSnapshot", "selector_mode": "INSTRUMENT_ID"},
            "hy": {"canonical_object": "ClassificationMarketSnapshot", "selector_mode": "NODE_NAME_OR_PROVISIONAL_ID"},
            "gn": {"canonical_object": "ClassificationMarketSnapshot", "selector_mode": "NODE_NAME_OR_PROVISIONAL_ID"},
            "kphy": {"canonical_object": "ClassificationMarketSnapshot", "selector_mode": "NODE_NAME_OR_PROVISIONAL_ID"},
            "kpgn": {"canonical_object": "ClassificationMarketSnapshot", "selector_mode": "NODE_NAME_OR_PROVISIONAL_ID"},
            "zj": {"canonical_object": "MoneyFlowSnapshot", "selector_mode": "INSTRUMENT_ID"},
        }

    def dataset_profile(self, dataset_id: str) -> dict[str, Any]:
        return dict(self.profiles[dataset_id])

    def available_fields(self, dataset_id: str) -> tuple[str, ...]:
        object_name = self.profiles[dataset_id]["canonical_object"]
        if object_name == "DailyBar":
            return ("instrument_id", "trade_date", "close_raw_cny")
        if object_name == "AuctionSnapshot":
            return ("instrument_id", "trade_date", "snapshot_time_precision")
        if object_name == "ClassificationMarketSnapshot":
            return ("node_id", "node_name_cn", "trade_date")
        return ("instrument_id", "trade_date", "net_inflow_total_cny")

    def read(self, request: Any) -> DailyFundsStandardBatch:
        self.requests.append(request)
        object_name = self.profiles[request.dataset_id]["canonical_object"]
        selector = request.entity_ids[0]
        if object_name == "ClassificationMarketSnapshot":
            primary_key = {"node_id": selector, "trade_date": request.end_date, "snapshot_phase": "CLOSE", "classification_system": "SOURCE_VENDOR", "classification_type": "INDUSTRY"}
            values = {"node_id": selector, "node_name_cn": "银行", "trade_date": request.end_date}
        else:
            primary_key = {"instrument_id": selector, "trade_date": request.end_date}
            values = {"instrument_id": selector, "trade_date": request.end_date}
            if object_name == "DailyBar":
                values["close_raw_cny"] = 10.0
            elif object_name == "AuctionSnapshot":
                values["snapshot_time_precision"] = "DATE_ONLY"
            else:
                values["net_inflow_total_cny"] = 1.0
        record = DailyFundsCanonicalRecord(
            dataset_id=request.dataset_id,
            canonical_object=object_name,
            primary_key=primary_key,
            values=values,
            source_record_id=f"{request.dataset_id}:hash:1",
            source_extensions={"raw": "value"},
            quality_flags=("SOURCE_WARNING",),
            lineage=({"canonical_field": next(iter(values)), "source_fields": ["x"]},),
            snapshot_date=request.end_date,
        )
        return DailyFundsStandardBatch(
            dataset_id=request.dataset_id,
            canonical_object=object_name,
            coverage_version=self.coverage_version,
            mapping_version=self.mapping_version,
            dictionary_revision=self.dictionary_revision,
            scanned_source_row_count=1,
            source_row_count=1,
            records=(record,),
            warnings=(),
        )


class Task017DStandardProviderTests(unittest.TestCase):
    def test_legacy_instrument_query_remains_supported(self) -> None:
        query = StandardDataQuery(
            dataset_id="hq",
            canonical_object="DailyBar",
            instrument_ids=("000001",),
            start_date=date(2025, 11, 20),
            end_date=date(2025, 11, 20),
        )
        self.assertEqual(query.selector_mode, INSTRUMENT_SELECTOR_MODE)
        self.assertEqual(query.selector_ids, ("000001",))
        self.assertEqual(query.entity_ids, ())

    def test_generic_entity_query_is_supported(self) -> None:
        query = StandardDataQuery(
            dataset_id="hy",
            canonical_object="ClassificationMarketSnapshot",
            instrument_ids=(),
            entity_ids=("SOURCE_VENDOR:INDUSTRY:ABC",),
            start_date=date(2025, 11, 20),
            end_date=date(2025, 11, 20),
        )
        self.assertEqual(query.selector_mode, ENTITY_SELECTOR_MODE)
        self.assertEqual(query.selector_ids, query.entity_ids)

    def test_exactly_one_selector_is_required(self) -> None:
        kwargs = dict(
            dataset_id="hq",
            canonical_object="DailyBar",
            start_date=date(2025, 11, 20),
            end_date=date(2025, 11, 20),
        )
        with self.assertRaises(DataContractError):
            StandardDataQuery(instrument_ids=(), **kwargs)
        with self.assertRaises(DataContractError):
            StandardDataQuery(
                instrument_ids=("000001",),
                entity_ids=("node",),
                **kwargs,
            )

    def test_builds_seven_providers_with_correct_modes(self) -> None:
        providers = build_daily_funds_standard_providers(
            FakeCanonicalService(),
            project_root=PROJECT_ROOT,
        )
        self.assertEqual(len(providers), 7)
        modes = {p.dataset_id: p.descriptor.selector_mode for p in providers}
        self.assertEqual(modes["hq"], INSTRUMENT_SELECTOR_MODE)
        self.assertEqual(modes["hy"], ENTITY_SELECTOR_MODE)

    def test_registers_seven_providers(self) -> None:
        standard = StandardDataService()
        descriptors = register_daily_funds_standard_providers(
            standard,
            FakeCanonicalService(),
            project_root=PROJECT_ROOT,
        )
        self.assertEqual(len(descriptors), 7)
        self.assertEqual(len(standard.list_datasets()), 7)

    def test_security_provider_uses_instrument_selector(self) -> None:
        canonical = FakeCanonicalService()
        standard = StandardDataService()
        register_daily_funds_standard_providers(
            standard, canonical, project_root=PROJECT_ROOT
        )
        result = standard.query(
            StandardDataQuery(
                dataset_id="hq",
                canonical_object="DailyBar",
                instrument_ids=("000001",),
                start_date=date(2025, 11, 20),
                end_date=date(2025, 11, 20),
            )
        )
        self.assertEqual(canonical.requests[-1].entity_ids, ("000001",))
        self.assertEqual(result.metadata.status, QualityStatus.WARNING)
        self.assertFalse(result.metadata.blocks_downstream)

    def test_classification_provider_uses_entity_selector(self) -> None:
        canonical = FakeCanonicalService()
        standard = StandardDataService()
        register_daily_funds_standard_providers(
            standard, canonical, project_root=PROJECT_ROOT
        )
        result = standard.query(
            StandardDataQuery(
                dataset_id="hy",
                canonical_object="ClassificationMarketSnapshot",
                instrument_ids=(),
                entity_ids=("SOURCE_VENDOR:INDUSTRY:ABC",),
                start_date=date(2025, 11, 20),
                end_date=date(2025, 11, 20),
            )
        )
        self.assertEqual(result.records[0].primary_key["node_id"], "SOURCE_VENDOR:INDUSTRY:ABC")
        self.assertNotIn("instrument_id", result.records[0].primary_key)

    def test_selector_mismatch_is_rejected_by_standard_service(self) -> None:
        standard = StandardDataService()
        register_daily_funds_standard_providers(
            standard, FakeCanonicalService(), project_root=PROJECT_ROOT
        )
        with self.assertRaises(DataContractError):
            standard.query(
                StandardDataQuery(
                    dataset_id="hy",
                    canonical_object="ClassificationMarketSnapshot",
                    instrument_ids=("000001",),
                    start_date=date(2025, 11, 20),
                    end_date=date(2025, 11, 20),
                )
            )

    def test_field_projection_and_optional_payloads(self) -> None:
        provider = DailyFundsStandardDataProvider(
            FakeCanonicalService(), "hq", project_root=PROJECT_ROOT
        )
        result = provider.query(
            StandardDataQuery(
                dataset_id="hq",
                canonical_object="DailyBar",
                instrument_ids=("000001",),
                start_date=date(2025, 11, 20),
                end_date=date(2025, 11, 20),
                fields=("close_raw_cny",),
                include_source_extensions=False,
                include_quality_flags=False,
                include_lineage=False,
            )
        )
        record = result.records[0]
        self.assertEqual(record.values, {"close_raw_cny": 10.0})
        self.assertEqual(record.source_extensions, {})
        self.assertEqual(record.quality_flags, ())
        self.assertEqual(record.lineage, ())

    def test_strict_historical_usage_is_blocked(self) -> None:
        provider = DailyFundsStandardDataProvider(
            FakeCanonicalService(), "hq", project_root=PROJECT_ROOT
        )
        result = provider.query(
            StandardDataQuery(
                dataset_id="hq",
                canonical_object="DailyBar",
                instrument_ids=("000001",),
                start_date=date(2025, 11, 20),
                end_date=date(2025, 11, 20),
                usage=StandardDataUsage.STRICT_HISTORICAL_BACKTEST,
            )
        )
        self.assertTrue(result.metadata.blocks_downstream)
        self.assertEqual(result.metadata.status, QualityStatus.FAILED)
        with self.assertRaises(DataContractError):
            result.assert_usable()

    def test_same_day_manual_decision_is_blocked(self) -> None:
        provider = DailyFundsStandardDataProvider(
            FakeCanonicalService(), "hq", project_root=PROJECT_ROOT
        )
        result = provider.query(
            StandardDataQuery(
                dataset_id="hq",
                canonical_object="DailyBar",
                instrument_ids=("000001",),
                start_date=date(2025, 11, 20),
                end_date=date(2025, 11, 20),
                usage=StandardDataUsage.MANUAL_DECISION_SUPPORT,
                decision_time=datetime(2025, 11, 20, 15, 0, tzinfo=timezone.utc),
            )
        )
        self.assertTrue(result.metadata.blocks_downstream)

    def test_unknown_field_is_rejected(self) -> None:
        provider = DailyFundsStandardDataProvider(
            FakeCanonicalService(), "hq", project_root=PROJECT_ROOT
        )
        with self.assertRaises(DataContractError):
            provider.query(
                StandardDataQuery(
                    dataset_id="hq",
                    canonical_object="DailyBar",
                    instrument_ids=("000001",),
                    start_date=date(2025, 11, 20),
                    end_date=date(2025, 11, 20),
                    fields=("not_a_field",),
                )
            )


if __name__ == "__main__":
    unittest.main()
