"""测试DolphinDB日K复权字段分层核验。"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from a_stock_quant.data_contracts import DataContractError
from a_stock_quant.dolphindb_adjustment_layers import (
    DolphinDBAdjustmentLayerProfiler,
)


class FakeAdjustmentAdapter:
    def __init__(self) -> None:
        self.factor_summary_calls = 0
        self.layer_calls = 0
        self.transient_failures_remaining = 0

    def _validate_database_uri(self, value: str) -> None:
        if not value.startswith("dfs://"):
            raise DataContractError("bad uri")

    def _validate_table_name(self, value: str) -> None:
        if not value.replace("_", "").isalnum():
            raise DataContractError("bad table")

    def run_readonly_query(self, script: str) -> Any:
        normalized = " ".join(script.split())

        if (
            self.transient_failures_remaining > 0
            and "max(trade_date)" in normalized
        ):
            self.transient_failures_remaining -= 1
            raise DataContractError(
                "DolphinDB只读查询失败：Can't open file"
            )

        if "max(trade_date)" in normalized:
            return [{"max_trade_date": "2026-06-20"}]

        if "select distinct stock_code" in normalized:
            return [
                {"stock_code": "000001"},
                {"stock_code": "000002"},
                {"stock_code": "000003"},
            ]

        if (
            "deduct_zero_action_zero_comparable_row_count"
            in normalized
        ):
            self.layer_calls += 1
            multiplier = 1 if self.layer_calls == 1 else 2

            return [{
                "row_count": 500 * multiplier,
                "adj_factor_equal_one_count": 100 * multiplier,
                "deduct_zero_count": 400 * multiplier,
                "deduct_nonzero_count": 100 * multiplier,
                "adj_price_equal_close_count": 50 * multiplier,
                "corporate_action_nonzero_count": 25 * multiplier,

                "deduct_zero_action_zero_comparable_row_count":
                    300 * multiplier,
                "deduct_zero_action_zero_adj_price_equals_close_multiply_factor_match_count":
                    300 * multiplier,
                "deduct_zero_action_zero_adj_price_equals_close_divide_factor_match_count":
                    0,
                "deduct_zero_action_zero_adj_price_equals_close_multiply_factor_plus_deduct_match_count":
                    0,
                "deduct_zero_action_zero_adj_price_equals_close_plus_deduct_multiply_factor_match_count":
                    0,
                "deduct_zero_action_zero_adj_price_equals_close_multiply_factor_minus_deduct_match_count":
                    0,
                "deduct_zero_action_zero_adj_price_equals_close_minus_deduct_multiply_factor_match_count":
                    0,

                "deduct_zero_action_nonzero_comparable_row_count":
                    100 * multiplier,
                "deduct_zero_action_nonzero_adj_price_equals_close_multiply_factor_match_count":
                    100 * multiplier,
                "deduct_zero_action_nonzero_adj_price_equals_close_divide_factor_match_count":
                    0,
                "deduct_zero_action_nonzero_adj_price_equals_close_multiply_factor_plus_deduct_match_count":
                    0,
                "deduct_zero_action_nonzero_adj_price_equals_close_plus_deduct_multiply_factor_match_count":
                    0,
                "deduct_zero_action_nonzero_adj_price_equals_close_multiply_factor_minus_deduct_match_count":
                    0,
                "deduct_zero_action_nonzero_adj_price_equals_close_minus_deduct_multiply_factor_match_count":
                    0,

                "deduct_nonzero_action_zero_comparable_row_count":
                    80 * multiplier,
                "deduct_nonzero_action_zero_adj_price_equals_close_multiply_factor_match_count":
                    32 * multiplier,
                "deduct_nonzero_action_zero_adj_price_equals_close_divide_factor_match_count":
                    0,
                "deduct_nonzero_action_zero_adj_price_equals_close_multiply_factor_plus_deduct_match_count":
                    0,
                "deduct_nonzero_action_zero_adj_price_equals_close_plus_deduct_multiply_factor_match_count":
                    0,
                "deduct_nonzero_action_zero_adj_price_equals_close_multiply_factor_minus_deduct_match_count":
                    0,
                "deduct_nonzero_action_zero_adj_price_equals_close_minus_deduct_multiply_factor_match_count":
                    0,

                "deduct_nonzero_action_nonzero_comparable_row_count":
                    20 * multiplier,
                "deduct_nonzero_action_nonzero_adj_price_equals_close_multiply_factor_match_count":
                    8 * multiplier,
                "deduct_nonzero_action_nonzero_adj_price_equals_close_divide_factor_match_count":
                    0,
                "deduct_nonzero_action_nonzero_adj_price_equals_close_multiply_factor_plus_deduct_match_count":
                    0,
                "deduct_nonzero_action_nonzero_adj_price_equals_close_plus_deduct_multiply_factor_match_count":
                    0,
                "deduct_nonzero_action_nonzero_adj_price_equals_close_multiply_factor_minus_deduct_match_count":
                    0,
                "deduct_nonzero_action_nonzero_adj_price_equals_close_minus_deduct_multiply_factor_match_count":
                    0,
            }]

        if "as factor_change_count" in normalized:
            self.factor_summary_calls += 1
            return [{
                "factor_change_count": 2,
                "factor_change_deduct_nonzero_count": 2,
                "factor_change_action_nonzero_count": 1,
                "factor_change_adj_price_equal_close_count": 0,
            }]

        if "select top 3" in normalized:
            return [{
                "stock_code": "000001",
                "trade_date": "2026-05-20",
                "prev_adj_factor": 10.0,
                "adj_factor": 11.0,
            }]

        raise AssertionError(f"未识别的查询：{normalized}")


class TestAdjustmentLayerProfiler(unittest.TestCase):
    def _profiler(self, adapter=None):
        return DolphinDBAdjustmentLayerProfiler(
            adapter=adapter or FakeAdjustmentAdapter(),
            factor_chunk_size=2,
        )

    def _report(self):
        return self._profiler().collect()

    def test_collects_four_layers(self) -> None:
        report = self._report()
        self.assertEqual(len(report.formula_layers), 4)

    def test_formula_layers_are_chunked_and_merged(self) -> None:
        report = self._report()
        self.assertEqual(report.global_layers["chunk_count"], 2)
        self.assertEqual(report.global_layers["row_count"], 1500)

        layer = next(
            item
            for item in report.formula_layers
            if item["layer_name"]
            == "deduct_zero_action_zero"
        )
        self.assertEqual(layer["comparable_row_count"], 900)
        self.assertEqual(layer["chunk_count"], 2)

    def test_zero_deduct_layer_can_be_confirmed(self) -> None:
        report = self._report()
        layer = next(
            item
            for item in report.formula_layers
            if item["layer_name"]
            == "deduct_zero_action_zero"
        )
        self.assertEqual(
            layer["best_candidate"],
            "adj_price_equals_close_multiply_factor",
        )
        self.assertEqual(layer["best_coverage"], 1.0)

    def test_nonzero_deduct_layer_stays_pending(self) -> None:
        report = self._report()
        layer = next(
            item
            for item in report.formula_layers
            if item["layer_name"]
            == "deduct_nonzero_action_zero"
        )
        self.assertEqual(layer["best_coverage"], 0.4)
        self.assertTrue(report.blocks_downstream)

    def test_factor_changes_are_chunked_and_merged(self) -> None:
        report = self._report()
        summary = report.factor_change_summary
        self.assertEqual(summary["stock_code_count"], 3)
        self.assertEqual(summary["chunk_count"], 2)
        self.assertEqual(summary["factor_change_count"], 4)

    def test_duplicate_samples_are_removed(self) -> None:
        report = self._report()
        self.assertEqual(len(report.factor_change_samples), 1)

    def test_transient_file_open_error_is_retried(self) -> None:
        adapter = FakeAdjustmentAdapter()
        adapter.transient_failures_remaining = 1
        report = self._profiler(adapter).collect()
        self.assertEqual(
            str(report.latest_trade_date),
            "2026-06-20",
        )

    def test_persistent_file_open_error_is_raised(self) -> None:
        adapter = FakeAdjustmentAdapter()
        adapter.transient_failures_remaining = 5

        with self.assertRaises(DataContractError):
            self._profiler(adapter).collect()

    def test_invalid_chunk_size_raises_error(self) -> None:
        with self.assertRaises(DataContractError):
            DolphinDBAdjustmentLayerProfiler(
                adapter=FakeAdjustmentAdapter(),
                factor_chunk_size=0,
            )

    def test_best_candidate_handles_empty_input(self) -> None:
        name, coverage = (
            DolphinDBAdjustmentLayerProfiler._best_candidate({})
        )
        self.assertIsNone(name)
        self.assertIsNone(coverage)


if __name__ == "__main__":
    unittest.main()
