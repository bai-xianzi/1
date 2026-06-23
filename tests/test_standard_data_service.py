"""测试统一标准数据服务与标准查询结果合同。"""

from __future__ import annotations

import sys
import unittest
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from a_stock_quant.data_contracts import (
    DataContractError,
    MappingStatus,
    QualityStatus,
    SourceType,
)
from a_stock_quant.dataset_registry import (
    DatasetRegistration,
    FieldMappingRule,
)
from a_stock_quant.daily_k_standard_provider import (
    DailyKStandardDataProvider,
)
from a_stock_quant.standard_data_service import (
    ProviderDescriptor,
    StandardDataQuery,
    StandardDataRecord,
    StandardDataUsage,
    StandardDatasetProvider,
    StandardDataService,
    StandardQueryMetadata,
    StandardQueryResult,
)


@dataclass
class FakeSourceRecord:
    source_record_id: str
    primary_key: dict[str, Any]
    canonical_objects: dict[str, dict[str, Any]]
    source_extensions: dict[str, Any]
    quality_flags: list[str]
    lineage: list[dict[str, Any]]


@dataclass
class FakeSourceBatch:
    dataset_id: str
    coverage_version: str
    mapping_version: str
    dictionary_revision: str
    request: dict[str, Any]
    source_row_count: int
    standardized_record_count: int
    records: list[FakeSourceRecord]
    warnings: list[str]


class FakeDailyKService:
    def __init__(
        self,
        *,
        quality_flags: list[str] | None = None,
        warnings: list[str] | None = None,
    ) -> None:
        self.registration = make_registration()
        self.quality_flags = quality_flags or [
            "SOURCE_PCT_CHANGE_SIGN_INVERTED"
        ]
        self.warnings = warnings or []
        self.requests: list[Any] = []

    def read(self, request: Any) -> FakeSourceBatch:
        self.requests.append(request)

        record = FakeSourceRecord(
            source_record_id="000001|2026-05-29",
            primary_key={
                "instrument_id": "000001",
                "trade_date": date(2026, 5, 29),
            },
            canonical_objects={
                "DailyBar": {
                    "instrument_id": "000001",
                    "trade_date": date(2026, 5, 29),
                    "close_raw_cny": 11.0,
                    "pct_change_pct": 10.0,
                },
                "OwnershipSnapshot": {
                    "instrument_id": "000001",
                    "as_of_date": date(2026, 5, 29),
                    "float_shares": 1_000_000.0,
                },
            },
            source_extensions={
                "pct_change": -10.0,
                "BS": "B",
            },
            quality_flags=list(self.quality_flags),
            lineage=[
                {
                    "target_object": "DailyBar",
                    "canonical_field": "instrument_id",
                    "source_fields": ["stock_code"],
                    "transform_id": "identity",
                    "transform_params": {},
                    "mapping_version": "0.2.0",
                    "dictionary_revision": "0.5",
                },
                {
                    "target_object": "DailyBar",
                    "canonical_field": "close_raw_cny",
                    "source_fields": ["close"],
                    "transform_id": "identity",
                    "transform_params": {},
                    "mapping_version": "0.2.0",
                    "dictionary_revision": "0.5",
                },
                {
                    "target_object":
                        "OwnershipSnapshot",
                    "canonical_field": "float_shares",
                    "source_fields": ["float_shares"],
                    "transform_id": "multiply",
                    "transform_params": {
                        "factor": 10_000
                    },
                    "mapping_version": "0.2.0",
                    "dictionary_revision": "0.5",
                },
            ],
        )

        return FakeSourceBatch(
            dataset_id="a_stock_daily_k",
            coverage_version=
                "a_stock_daily_k@2026-05-29",
            mapping_version="0.2.0",
            dictionary_revision="0.5",
            request={},
            source_row_count=1,
            standardized_record_count=1,
            records=[record],
            warnings=list(self.warnings),
        )


class FakeProvider(StandardDatasetProvider):
    def __init__(self) -> None:
        self.requests: list[StandardDataQuery] = []

    @property
    def descriptor(self) -> ProviderDescriptor:
        return ProviderDescriptor(
            provider_id="fake",
            dataset_id="demo",
            supported_objects=("DailyBar",),
            coverage_version="demo@2026-05-29",
            mapping_version="1.0.0",
            dictionary_revision="0.5",
        )

    def query(
        self,
        request: StandardDataQuery,
    ) -> StandardQueryResult:
        self.requests.append(request)
        record = StandardDataRecord(
            canonical_object="DailyBar",
            primary_key={
                "instrument_id": "000001",
                "trade_date": request.end_date,
            },
            values={"close_raw_cny": 10.0},
        )
        metadata = StandardQueryMetadata(
            dataset_id="demo",
            canonical_object="DailyBar",
            provider_id="fake",
            coverage_version="demo@2026-05-29",
            mapping_version="1.0.0",
            dictionary_revision="0.5",
            source_row_count=1,
            result_count=1,
            status=QualityStatus.PASSED,
            blocks_downstream=False,
        )
        return StandardQueryResult(
            query=request,
            metadata=metadata,
            records=(record,),
        )


def make_registration() -> DatasetRegistration:
    return DatasetRegistration(
        dataset_id="a_stock_daily_k",
        source_type=SourceType.DOLPHINDB,
        source_locator={
            "database_uri": "dfs://TEST",
            "table_name": "daily",
        },
        dataset_mode="SNAPSHOT",
        coverage_version="a_stock_daily_k@2026-05-29",
        schema_version="1.0.0",
        mapping_version="0.2.0",
        dictionary_revision="0.5",
        date_field="trade_date",
        entity_field="stock_code",
        primary_key_fields=(
            "stock_code",
            "trade_date",
        ),
        source_fields=(
            "stock_code",
            "trade_date",
            "close",
            "float_shares",
            "pct_change",
        ),
        canonical_objects=(
            "DailyBar",
            "OwnershipSnapshot",
        ),
        field_mappings=(
            FieldMappingRule(
                source_fields=("stock_code",),
                status=MappingStatus.MAPPED,
                target_object="DailyBar",
                canonical_field="instrument_id",
            ),
            FieldMappingRule(
                source_fields=("trade_date",),
                status=MappingStatus.MAPPED,
                target_object="DailyBar",
                canonical_field="trade_date",
            ),
            FieldMappingRule(
                source_fields=("close",),
                status=MappingStatus.MAPPED,
                target_object="DailyBar",
                canonical_field="close_raw_cny",
            ),
            FieldMappingRule(
                source_fields=("close",),
                status=MappingStatus.MAPPED,
                target_object="DailyBar",
                canonical_field="pct_change_pct",
            ),
            FieldMappingRule(
                source_fields=("stock_code",),
                status=MappingStatus.MAPPED,
                target_object="OwnershipSnapshot",
                canonical_field="instrument_id",
            ),
            FieldMappingRule(
                source_fields=("trade_date",),
                status=MappingStatus.MAPPED,
                target_object="OwnershipSnapshot",
                canonical_field="as_of_date",
            ),
            FieldMappingRule(
                source_fields=("float_shares",),
                status=MappingStatus.MAPPED,
                target_object="OwnershipSnapshot",
                canonical_field="float_shares",
            ),
            FieldMappingRule(
                source_fields=("pct_change",),
                status=MappingStatus.PENDING_CONFIRMATION,
            ),
        ),
    )


def make_query(**overrides: Any) -> StandardDataQuery:
    values = {
        "dataset_id": "a_stock_daily_k",
        "canonical_object": "DailyBar",
        "instrument_ids": ("000001",),
        "start_date": date(2026, 5, 29),
        "end_date": date(2026, 5, 29),
    }
    values.update(overrides)
    return StandardDataQuery(**values)


class TestStandardDataQuery(unittest.TestCase):
    def test_as_of_date_defaults_to_end_date(self) -> None:
        query = make_query()
        self.assertEqual(
            query.as_of_date,
            date(2026, 5, 29),
        )

    def test_end_date_after_as_of_is_rejected(self) -> None:
        with self.assertRaises(DataContractError):
            make_query(
                end_date=date(2026, 5, 29),
                as_of_date=date(2026, 5, 28),
            )

    def test_duplicate_instruments_are_rejected(self) -> None:
        with self.assertRaises(DataContractError):
            make_query(
                instrument_ids=("000001", "000001")
            )

    def test_duplicate_fields_are_rejected(self) -> None:
        with self.assertRaises(DataContractError):
            make_query(
                fields=(
                    "close_raw_cny",
                    "close_raw_cny",
                )
            )

    def test_usage_string_is_normalized(self) -> None:
        query = make_query(
            usage="MANUAL_DECISION_SUPPORT",
            decision_time=datetime(
                2026, 5, 29, 9, 0, tzinfo=timezone.utc
            ),
        )
        self.assertEqual(
            query.usage,
            StandardDataUsage.MANUAL_DECISION_SUPPORT,
        )

    def test_unknown_usage_is_rejected(self) -> None:
        with self.assertRaises(DataContractError):
            make_query(usage="UNKNOWN")

    def test_manual_usage_requires_decision_time(self) -> None:
        with self.assertRaises(DataContractError):
            make_query(usage="MANUAL_DECISION_SUPPORT")

    def test_decision_time_requires_timezone(self) -> None:
        with self.assertRaises(DataContractError):
            make_query(
                decision_time=datetime(
                    2026, 5, 29, 9, 0
                )
            )

    def test_decision_time_is_serialized(self) -> None:
        query = make_query(
            decision_time=datetime(
                2026,
                5,
                29,
                9,
                0,
                tzinfo=timezone.utc,
            )
        )
        value = query.to_dict()
        self.assertEqual(
            value["usage"],
            "CURRENT_SNAPSHOT_RESEARCH",
        )
        self.assertEqual(
            value["decision_time"],
            "2026-05-29T09:00:00+00:00",
        )


class TestStandardDataService(unittest.TestCase):
    def test_register_and_query_provider(self) -> None:
        service = StandardDataService()
        provider = FakeProvider()
        service.register_provider(provider)

        query = StandardDataQuery(
            dataset_id="demo",
            canonical_object="DailyBar",
            instrument_ids=("000001",),
            start_date=date(2026, 5, 29),
            end_date=date(2026, 5, 29),
        )
        result = service.query(query)

        self.assertEqual(
            result.records[0].values["close_raw_cny"],
            10.0,
        )
        self.assertEqual(provider.requests, [query])

    def test_duplicate_provider_is_rejected(self) -> None:
        service = StandardDataService()
        provider = FakeProvider()
        service.register_provider(provider)

        with self.assertRaises(DataContractError):
            service.register_provider(provider)

    def test_unknown_dataset_is_rejected(self) -> None:
        service = StandardDataService()

        with self.assertRaises(DataContractError):
            service.query(
                StandardDataQuery(
                    dataset_id="missing",
                    canonical_object="DailyBar",
                    instrument_ids=("000001",),
                    start_date=date(2026, 5, 29),
                    end_date=date(2026, 5, 29),
                )
            )

    def test_dataset_descriptors_are_listed(self) -> None:
        service = StandardDataService()
        service.register_provider(FakeProvider())

        descriptors = service.list_datasets()

        self.assertEqual(len(descriptors), 1)
        self.assertEqual(
            descriptors[0].dataset_id,
            "demo",
        )


class TestDailyKStandardDataProvider(unittest.TestCase):
    def test_daily_bar_is_returned(self) -> None:
        provider = DailyKStandardDataProvider(
            FakeDailyKService()
        )
        result = provider.query(make_query())

        self.assertEqual(
            result.records[0].canonical_object,
            "DailyBar",
        )
        self.assertEqual(
            result.records[0].values[
                "close_raw_cny"
            ],
            11.0,
        )
        self.assertEqual(
            result.metadata.status,
            QualityStatus.PASSED,
        )

    def test_field_projection_is_applied(self) -> None:
        provider = DailyKStandardDataProvider(
            FakeDailyKService()
        )
        result = provider.query(
            make_query(fields=("close_raw_cny",))
        )

        self.assertEqual(
            result.records[0].values,
            {"close_raw_cny": 11.0},
        )

    def test_unknown_field_is_rejected(self) -> None:
        provider = DailyKStandardDataProvider(
            FakeDailyKService()
        )

        with self.assertRaises(DataContractError):
            provider.query(
                make_query(fields=("not_a_field",))
            )

    def test_source_extensions_are_opt_in(self) -> None:
        provider = DailyKStandardDataProvider(
            FakeDailyKService()
        )

        hidden = provider.query(make_query())
        visible = provider.query(
            make_query(
                include_source_extensions=True
            )
        )

        self.assertEqual(
            hidden.records[0].source_extensions,
            {},
        )
        self.assertEqual(
            visible.records[0].source_extensions[
                "pct_change"
            ],
            -10.0,
        )

    def test_lineage_is_filtered_by_projection(self) -> None:
        provider = DailyKStandardDataProvider(
            FakeDailyKService()
        )
        result = provider.query(
            make_query(fields=("close_raw_cny",))
        )

        self.assertEqual(
            len(result.records[0].lineage),
            1,
        )
        self.assertEqual(
            result.records[0].lineage[0][
                "canonical_field"
            ],
            "close_raw_cny",
        )

    def test_versions_are_preserved(self) -> None:
        provider = DailyKStandardDataProvider(
            FakeDailyKService()
        )
        metadata = provider.query(
            make_query()
        ).metadata

        self.assertEqual(
            metadata.coverage_version,
            "a_stock_daily_k@2026-05-29",
        )
        self.assertEqual(
            metadata.mapping_version,
            "0.2.0",
        )
        self.assertEqual(
            metadata.dictionary_revision,
            "0.5",
        )

    def test_blocking_quality_flag_blocks_result(self) -> None:
        provider = DailyKStandardDataProvider(
            FakeDailyKService(
                quality_flags=[
                    "SOURCE_ADJ_FORMULA_MISMATCH"
                ]
            )
        )
        result = provider.query(make_query())

        self.assertEqual(
            result.metadata.status,
            QualityStatus.FAILED,
        )
        self.assertTrue(
            result.metadata.blocks_downstream
        )

        with self.assertRaises(DataContractError):
            result.assert_usable()

    def test_ownership_snapshot_is_supported(self) -> None:
        provider = DailyKStandardDataProvider(
            FakeDailyKService()
        )
        result = provider.query(
            make_query(
                canonical_object=
                    "OwnershipSnapshot",
                fields=("float_shares",),
            )
        )

        self.assertEqual(
            result.records[0].primary_key[
                "as_of_date"
            ],
            date(2026, 5, 29),
        )
        self.assertEqual(
            result.records[0].values[
                "float_shares"
            ],
            1_000_000.0,
        )

    def test_batch_warning_produces_warning_status(self) -> None:
        provider = DailyKStandardDataProvider(
            FakeDailyKService(
                warnings=["000002 在请求范围内没有数据。"]
            )
        )
        result = provider.query(make_query())

        self.assertEqual(
            result.metadata.status,
            QualityStatus.WARNING,
        )
        self.assertFalse(
            result.metadata.blocks_downstream
        )


class TestStandardQueryResult(unittest.TestCase):
    def test_to_dict_serializes_dates_and_enums(self) -> None:
        provider = DailyKStandardDataProvider(
            FakeDailyKService()
        )
        value = provider.query(make_query()).to_dict()

        self.assertEqual(
            value["query"]["end_date"],
            "2026-05-29",
        )
        self.assertEqual(
            value["metadata"]["status"],
            "PASSED",
        )
        self.assertEqual(
            value["records"][0]["primary_key"][
                "trade_date"
            ],
            "2026-05-29",
        )


if __name__ == "__main__":
    unittest.main()
