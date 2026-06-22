"""测试通用数据集注册表与标准字段映射引擎。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from a_stock_quant.data_contracts import (
    DataContractError,
    MappingStatus,
    SourceType,
)
from a_stock_quant.dataset_registry import (
    CanonicalFieldCatalog,
    CanonicalMappingEngine,
    DatasetRegistration,
    DatasetRegistry,
    FieldMappingRule,
)


def make_registration() -> DatasetRegistration:
    return DatasetRegistration(
        dataset_id="demo_daily",
        source_type=SourceType.DOLPHINDB,
        source_locator={
            "database_uri": "dfs://DEMO",
            "table_name": "daily",
        },
        dataset_mode="SNAPSHOT",
        coverage_version="demo_daily@2026-05-29",
        schema_version="1.0.0",
        mapping_version="1.0.0",
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
            "source_signal",
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
                required=True,
            ),
            FieldMappingRule(
                source_fields=("trade_date",),
                status=MappingStatus.MAPPED,
                target_object="DailyBar",
                canonical_field="trade_date",
                required=True,
            ),
            FieldMappingRule(
                source_fields=("close",),
                status=MappingStatus.MAPPED,
                target_object="DailyBar",
                canonical_field="close_raw_cny",
            ),
            FieldMappingRule(
                source_fields=("float_shares",),
                status=MappingStatus.MAPPED,
                target_object="OwnershipSnapshot",
                canonical_field="float_shares",
                transform_id="multiply",
                transform_params={"factor": 10000},
            ),
            FieldMappingRule(
                source_fields=("source_signal",),
                status=MappingStatus.PENDING_CONFIRMATION,
                notes="来源专有信号。",
            ),
        ),
    )


class TestDatasetRegistration(unittest.TestCase):
    def test_all_source_fields_are_accounted(self) -> None:
        coverage = make_registration().mapping_coverage()

        self.assertTrue(
            coverage["all_source_fields_accounted"]
        )
        self.assertEqual(
            coverage["pending_fields"],
            ["source_signal"],
        )

    def test_unknown_mapping_source_is_rejected(self) -> None:
        with self.assertRaises(DataContractError):
            DatasetRegistration(
                dataset_id="bad",
                source_type=SourceType.DOLPHINDB,
                source_locator={},
                dataset_mode="SNAPSHOT",
                coverage_version="bad@1",
                schema_version="1",
                mapping_version="1",
                dictionary_revision="0.5",
                date_field=None,
                entity_field=None,
                primary_key_fields=(),
                source_fields=("a",),
                canonical_objects=("DailyBar",),
                field_mappings=(
                    FieldMappingRule(
                        source_fields=("missing",),
                        status=MappingStatus.MAPPED,
                        target_object="DailyBar",
                        canonical_field="trade_date",
                    ),
                ),
            )

    def test_primary_key_must_be_source_field(self) -> None:
        value = make_registration().to_dict()
        value["primary_key_fields"] = ["missing"]

        with self.assertRaises(DataContractError):
            DatasetRegistration.from_dict(value)

    def test_round_trip_dict(self) -> None:
        original = make_registration()
        restored = DatasetRegistration.from_dict(
            original.to_dict()
        )

        self.assertEqual(restored, original)


class TestCanonicalFieldCatalog(unittest.TestCase):
    def test_valid_registration_passes(self) -> None:
        catalog = CanonicalFieldCatalog({
            "DailyBar": {
                "instrument_id",
                "trade_date",
                "close_raw_cny",
            },
            "OwnershipSnapshot": {
                "float_shares",
            },
        })

        catalog.assert_valid(make_registration())

    def test_unknown_canonical_field_fails(self) -> None:
        catalog = CanonicalFieldCatalog({
            "DailyBar": {
                "instrument_id",
                "trade_date",
            },
            "OwnershipSnapshot": {
                "float_shares",
            },
        })

        with self.assertRaises(DataContractError):
            catalog.assert_valid(make_registration())


class TestDatasetRegistry(unittest.TestCase):
    def test_register_and_filter(self) -> None:
        registry = DatasetRegistry()
        registration = make_registration()
        registry.register(registration)

        self.assertEqual(
            registry.get("demo_daily"),
            registration,
        )
        self.assertEqual(
            len(
                registry.list(
                    canonical_object="DailyBar"
                )
            ),
            1,
        )

    def test_duplicate_registration_rejected(self) -> None:
        registry = DatasetRegistry()
        registration = make_registration()
        registry.register(registration)

        with self.assertRaises(DataContractError):
            registry.register(registration)

    def test_load_json(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "demo.json"
            path.write_text(
                json.dumps(
                    make_registration().to_dict(),
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            registry = DatasetRegistry()
            loaded = registry.load_json(path)

        self.assertEqual(loaded.dataset_id, "demo_daily")


class TestCanonicalMappingEngine(unittest.TestCase):
    def test_maps_multiple_standard_objects(self) -> None:
        result = CanonicalMappingEngine().map_record(
            make_registration(),
            {
                "stock_code": "000001",
                "trade_date": "2026-05-29",
                "close": 10.5,
                "float_shares": 123.4,
                "source_signal": "X",
            },
        )

        self.assertEqual(
            result.outputs["DailyBar"][
                "close_raw_cny"
            ],
            10.5,
        )
        self.assertEqual(
            result.outputs["OwnershipSnapshot"][
                "float_shares"
            ],
            1_234_000.0,
        )
        self.assertEqual(
            result.source_extensions["source_signal"],
            "X",
        )

    def test_required_missing_field_fails(self) -> None:
        with self.assertRaises(DataContractError):
            CanonicalMappingEngine().map_record(
                make_registration(),
                {
                    "trade_date": "2026-05-29",
                    "close": 10.5,
                    "float_shares": 123.4,
                },
            )

    def test_pct_change_transform_uses_context(self) -> None:
        rule = FieldMappingRule(
            source_fields=("close",),
            status=MappingStatus.MAPPED,
            target_object="DailyBar",
            canonical_field="pct_change_pct",
            transform_id="pct_change_from_prev_close",
            transform_params={"precision": 2},
        )
        value = make_registration().to_dict()
        value["field_mappings"].append(
            rule.to_dict()
        )
        registration = DatasetRegistration.from_dict(value)

        result = CanonicalMappingEngine().map_record(
            registration,
            {
                "stock_code": "000001",
                "trade_date": "2026-05-29",
                "close": 11.0,
                "float_shares": 100.0,
                "source_signal": None,
            },
            context={"prev_close": 10.0},
        )

        self.assertEqual(
            result.outputs["DailyBar"][
                "pct_change_pct"
            ],
            10.0,
        )


if __name__ == "__main__":
    unittest.main()
