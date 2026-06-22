"""测试DolphinDB日K只读画像。"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from a_stock_quant.data_contracts import (
    DataContractError,
    RawDataBatch,
    SourceType,
)
from a_stock_quant.dolphindb_adapter import (
    DolphinDBConnectionSettings,
    DolphinDBDataSourceAdapter,
)
from a_stock_quant.dolphindb_daily_profile import (
    DolphinDBDailyKProfiler,
    _json_safe,
)


class FakeSession:
    def __init__(self) -> None:
        self.last_script: str | None = None

    def connect(
        self,
        host: str,
        port: int,
        user_id: str,
        password: str,
    ) -> bool:
        return True

    def run(self, script: str) -> Any:
        self.last_script = script
        return [{"row_count": 1}]


class FakeProfileAdapter:
    def _validate_database_uri(self, value: str) -> None:
        if not value.startswith("dfs://"):
            raise DataContractError("bad uri")

    def _validate_table_name(self, value: str) -> None:
        if not value.replace("_", "").isalnum():
            raise DataContractError("bad table")

    def read_raw(
        self,
        source_object_name: str,
        **kwargs: Any,
    ) -> RawDataBatch:
        fields = [
            "stock_code",
            "trade_date",
            "open",
            "high",
            "low",
            "close",
            "amount",
            "volume",
            "price_change",
            "pct_change",
            "adj_factor",
            "adj_price",
            "float_shares",
            "total_shares",
        ]
        return RawDataBatch(
            source_id="fake",
            source_type=SourceType.DOLPHINDB,
            source_object_name=source_object_name,
            raw_fields=fields,
            records=[],
        )

    def run_readonly_query(self, script: str) -> Any:
        normalized = " ".join(script.split())

        if "nunique(stock_code" in normalized:
            return [{
                "row_count": 100,
                "stock_count": 2,
                "min_trade_date": "1990-12-19",
                "max_trade_date": "2026-06-20",
            }]

        if "stock_code_null_count" in normalized:
            return [{
                "stock_code_null_count": 0,
                "trade_date_null_count": 0,
            }]

        if "duplicate_group_count" in normalized:
            return [{
                "duplicate_group_count": 0,
                "duplicate_extra_row_count": 0,
            }]

        if (
            "count(*) as duplicate_count" in normalized
            and "top 20" in normalized
        ):
            return []

        if "open_nonpositive_count" in normalized:
            return [{
                "checked_row_count": 100,
                "open_null_count": 0,
                "high_null_count": 0,
                "low_null_count": 0,
                "close_null_count": 0,
                "open_nonpositive_count": 0,
                "high_nonpositive_count": 0,
                "low_nonpositive_count": 0,
                "close_nonpositive_count": 0,
                "high_below_low_count": 0,
                "high_below_open_count": 0,
                "high_below_close_count": 0,
                "low_above_open_count": 0,
                "low_above_close_count": 0,
            }]

        if "price_change_mismatch_count" in normalized:
            return [{
                "comparable_row_count": 98,
                "price_change_mismatch_count": 0,
                "pct_change_standard_mismatch_count": 90,
                "pct_change_inverse_mismatch_count": 80,
                "pct_change_negated_standard_mismatch_count": 0,
            }]

        if "expected_standard_pct_change" in normalized:
            return [{
                "stock_code": "600601",
                "trade_date": "1990-12-20",
                "prev_close": 185.3,
                "close": 194.6,
                "price_change": 9.3,
                "expected_price_change": 9.3,
                "pct_change": -5.02,
                "expected_standard_pct_change": 5.02,
                "expected_inverse_pct_change": -4.78,
                "expected_negated_standard_pct_change": -5.02,
            }]

        if "avg_amount_per_volume" in normalized:
            return [{
                "comparable_row_count": 100,
                "min_amount_per_volume": 7.4,
                "avg_amount_per_volume": 8.0,
                "max_amount_per_volume": 10.0,
            }]

        if "adj_factor_non_one_count" in normalized:
            return [{
                "row_count": 100,
                "adj_factor_null_count": 0,
                "adj_factor_equal_one_count": 80,
                "adj_factor_non_one_count": 20,
                "adj_price_null_count": 0,
                "adj_price_equal_close_count": 80,
                "adj_price_close_difference_count": 20,
            }]

        raise AssertionError(f"未识别的查询：{normalized}")


class TestReadonlyQuerySafety(unittest.TestCase):
    def _adapter(self, session: FakeSession) -> DolphinDBDataSourceAdapter:
        settings = DolphinDBConnectionSettings(
            host="127.0.0.1",
            port=8848,
            username="admin",
            password="secret",
        )
        return DolphinDBDataSourceAdapter(
            settings=settings,
            session_factory=lambda: session,
        )

    def test_select_query_is_allowed(self) -> None:
        result = self._adapter(FakeSession()).run_readonly_query(
            "select count(*) from loadTable("
            '"dfs://A_STOCK_DAILY_K_DB", `stock_daily_k)'
        )
        self.assertEqual(result, [{"row_count": 1}])

    def test_update_query_is_rejected(self) -> None:
        with self.assertRaises(DataContractError):
            self._adapter(FakeSession()).run_readonly_query(
                "update t set close = 1"
            )

    def test_semicolon_is_rejected(self) -> None:
        with self.assertRaises(DataContractError):
            self._adapter(FakeSession()).run_readonly_query(
                "select count(*) from t; drop table t"
            )


class TestDailyKProfiler(unittest.TestCase):
    def test_collect_builds_report(self) -> None:
        report = DolphinDBDailyKProfiler(
            adapter=FakeProfileAdapter(),
        ).collect()

        self.assertEqual(report.summary["row_count"], 100)
        self.assertEqual(report.summary["stock_count"], 2)
        self.assertEqual(
            report.duplicate_summary["duplicate_extra_row_count"],
            0,
        )
        self.assertTrue(report.blocks_downstream)
        self.assertEqual(
            report.overall_status.value,
            "PENDING_CONFIRMATION",
        )

    def test_pending_confirmations_are_created(self) -> None:
        report = DolphinDBDailyKProfiler(
            adapter=FakeProfileAdapter(),
        ).collect()

        categories = {
            item["category"]
            for item in report.pending_confirmations
        }
        self.assertIn("PCT_CHANGE_FORMULA", categories)
        self.assertIn("ADJUSTMENT_METHOD", categories)
        self.assertIn("VOLUME_UNIT", categories)
        self.assertIn("AMOUNT_UNIT", categories)

    def test_required_fields_pass(self) -> None:
        report = DolphinDBDailyKProfiler(
            adapter=FakeProfileAdapter(),
        ).collect()

        check = next(
            item
            for item in report.checks
            if item["check_name"] == "必需字段完整性"
        )
        self.assertEqual(check["status"], "PASSED")

    def test_json_safe_converts_nan(self) -> None:
        self.assertIsNone(_json_safe({"x": float("nan")})["x"])

    def test_nan_duplicate_count_is_normalized_to_zero(self) -> None:
        profiler = DolphinDBDailyKProfiler(
            adapter=FakeProfileAdapter(),
        )
        self.assertEqual(profiler._as_int(float("nan")), 0)

    def test_negated_standard_formula_is_recorded(self) -> None:
        report = DolphinDBDailyKProfiler(
            adapter=FakeProfileAdapter(),
        ).collect()

        self.assertEqual(
            report.change_formula_summary[
                "pct_change_negated_standard_mismatch_count"
            ],
            0,
        )

    def test_adjustment_equal_counts_are_recorded(self) -> None:
        report = DolphinDBDailyKProfiler(
            adapter=FakeProfileAdapter(),
        ).collect()

        self.assertEqual(
            report.adjustment_summary[
                "adj_factor_equal_one_count"
            ],
            80,
        )
        self.assertEqual(
            report.adjustment_summary[
                "adj_price_equal_close_count"
            ],
            80,
        )


if __name__ == "__main__":
    unittest.main()
