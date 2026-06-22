"""测试真实日K标准化抽样验收分析器。"""

from __future__ import annotations

import sys
import unittest
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from a_stock_quant.data_contracts import MappingStatus, SourceType
from a_stock_quant.dataset_registry import (
    DatasetRegistration,
    FieldMappingRule,
)
from a_stock_quant.dolphindb_daily_k_acceptance import (
    AcceptanceThresholds,
    DailyKAcceptanceAnalyzer,
    _json_safe,
)


@dataclass
class FakeRecord:
    source_record_id: str
    canonical_objects: dict[str, dict[str, Any]]
    source_extensions: dict[str, Any]
    quality_flags: list[str]
    lineage: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_record_id": self.source_record_id,
            "canonical_objects": self.canonical_objects,
            "source_extensions": self.source_extensions,
            "quality_flags": self.quality_flags,
            "lineage": self.lineage,
        }


@dataclass
class FakeBatch:
    dataset_id: str
    coverage_version: str
    mapping_version: str
    dictionary_revision: str
    request: dict[str, Any]
    source_row_count: int
    standardized_record_count: int
    records: list[FakeRecord]
    warnings: list[str]


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
        primary_key_fields=("stock_code", "trade_date"),
        source_fields=(
            "stock_code",
            "trade_date",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "amount",
            "float_shares",
            "total_shares",
            "pct_change",
            "adj_price",
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
                source_fields=("pct_change",),
                status=MappingStatus.PENDING_CONFIRMATION,
                target_object="DailyBar",
                canonical_field="pct_change_pct",
            ),
            FieldMappingRule(
                source_fields=("adj_price",),
                status=MappingStatus.PENDING_CONFIRMATION,
            ),
        ),
    )


def make_record(
    *,
    quality_flags: list[str] | None = None,
    missing_daily_field: str | None = None,
    computed_mismatch: bool = False,
    pending_missing: bool = False,
    invalid_lineage: bool = False,
) -> FakeRecord:
    daily = {
        "instrument_id": "000001",
        "trade_date": date(2026, 5, 29),
        "open_raw_cny": 10.0,
        "high_raw_cny": 11.5,
        "low_raw_cny": 9.8,
        "close_raw_cny": 11.0,
        "pre_close_raw_cny": 10.0,
        "pct_change_pct": 10.0,
        "volume_shares": 1_000.0,
        "volume_lots": 10.0,
        "amount_cny": 11_000.0,
        "vwap_raw_cny": 11.0,
        "float_market_cap_cny": 11_000_000.0,
        "total_market_cap_cny": 22_000_000.0,
    }
    ownership = {
        "instrument_id": "000001",
        "as_of_date": date(2026, 5, 29),
        "float_shares": 1_000_000.0,
        "total_shares": 2_000_000.0,
    }

    if missing_daily_field is not None:
        daily.pop(missing_daily_field)

    if computed_mismatch:
        daily["volume_lots"] = 99.0

    lineage = [{
        "target_object": "DailyBar",
        "canonical_field": "close_raw_cny",
        "source_fields": ["close"],
        "transform_id": "identity",
        "transform_params": {},
        "mapping_version": (
            "bad" if invalid_lineage else "0.2.0"
        ),
        "dictionary_revision": "0.5",
    }]

    extensions = {
        "pct_change": -10.0,
        "adj_price": 23.0,
    }
    if pending_missing:
        extensions.pop("adj_price")

    return FakeRecord(
        source_record_id="000001|2026-05-29",
        canonical_objects={
            "DailyBar": daily,
            "OwnershipSnapshot": ownership,
        },
        source_extensions=extensions,
        quality_flags=quality_flags or [
            "SOURCE_PCT_CHANGE_SIGN_INVERTED"
        ],
        lineage=lineage,
    )


def make_batch(record: FakeRecord) -> FakeBatch:
    return FakeBatch(
        dataset_id="a_stock_daily_k",
        coverage_version="a_stock_daily_k@2026-05-29",
        mapping_version="0.2.0",
        dictionary_revision="0.5",
        request={
            "instrument_ids": ["000001"],
            "start_date": date(2026, 5, 29),
            "end_date": date(2026, 5, 29),
        },
        source_row_count=1,
        standardized_record_count=1,
        records=[record],
        warnings=[],
    )


class TestAcceptanceThresholds(unittest.TestCase):
    def test_invalid_coverage_rejected(self) -> None:
        with self.assertRaises(Exception):
            AcceptanceThresholds(
                minimum_daily_bar_coverage=1.1
            )


class TestDailyKAcceptanceAnalyzer(unittest.TestCase):
    def setUp(self) -> None:
        self.analyzer = DailyKAcceptanceAnalyzer(
            make_registration()
        )

    def test_valid_batch_passes(self) -> None:
        report = self.analyzer.analyze(
            make_batch(make_record())
        )

        self.assertEqual(report["overall_status"], "PASSED")
        self.assertFalse(report["blocks_downstream"])
        self.assertEqual(
            report["computed_consistency"][
                "total_mismatch_count"
            ],
            0,
        )

    def test_known_sign_inversion_is_informational(self) -> None:
        report = self.analyzer.analyze(
            make_batch(make_record())
        )

        self.assertEqual(
            report["quality_flag_summary"][
                "blocking_flag_count"
            ],
            0,
        )
        self.assertEqual(
            report["quality_flag_summary"][
                "informational_flag_count"
            ],
            1,
        )

    def test_missing_daily_field_fails(self) -> None:
        report = self.analyzer.analyze(
            make_batch(
                make_record(
                    missing_daily_field="close_raw_cny"
                )
            )
        )

        self.assertEqual(report["overall_status"], "FAILED")
        self.assertTrue(report["blocks_downstream"])

    def test_computed_mismatch_fails(self) -> None:
        report = self.analyzer.analyze(
            make_batch(
                make_record(computed_mismatch=True)
            )
        )

        self.assertGreater(
            report["computed_consistency"][
                "total_mismatch_count"
            ],
            0,
        )
        self.assertEqual(report["overall_status"], "FAILED")

    def test_blocking_quality_flag_fails(self) -> None:
        report = self.analyzer.analyze(
            make_batch(
                make_record(
                    quality_flags=[
                        "SOURCE_ADJ_FORMULA_MISMATCH"
                    ]
                )
            )
        )

        self.assertEqual(
            report["quality_flag_summary"][
                "blocking_flag_count"
            ],
            1,
        )
        self.assertEqual(report["overall_status"], "FAILED")

    def test_pending_extension_missing_fails(self) -> None:
        report = self.analyzer.analyze(
            make_batch(
                make_record(pending_missing=True)
            )
        )

        self.assertLess(
            report["pending_extension_coverage"][
                "coverage"
            ],
            1.0,
        )
        self.assertEqual(report["overall_status"], "FAILED")

    def test_invalid_lineage_fails(self) -> None:
        report = self.analyzer.analyze(
            make_batch(
                make_record(invalid_lineage=True)
            )
        )

        self.assertEqual(
            report["lineage_coverage"][
                "invalid_lineage_count"
            ],
            1,
        )
        self.assertEqual(report["overall_status"], "FAILED")

    def test_json_safe_converts_non_finite_numbers(self) -> None:
        value = _json_safe({
            "nan": float("nan"),
            "positive_infinity": float("inf"),
            "negative_infinity": float("-inf"),
            "normal": 1.25,
        })

        self.assertIsNone(value["nan"])
        self.assertIsNone(value["positive_infinity"])
        self.assertIsNone(value["negative_infinity"])
        self.assertEqual(value["normal"], 1.25)

    def test_json_safe_converts_nested_dates(self) -> None:
        value = _json_safe({
            "a": date(2026, 5, 29),
            "b": [date(2026, 5, 28)],
        })

        self.assertEqual(value["a"], "2026-05-29")
        self.assertEqual(value["b"], ["2026-05-28"])


if __name__ == "__main__":
    unittest.main()
