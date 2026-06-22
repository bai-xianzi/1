"""测试DolphinDB日K字段语义核验。"""

from __future__ import annotations

import sys
import unittest
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from a_stock_quant.data_contracts import DataContractError
from a_stock_quant.dolphindb_daily_semantics import (
    DolphinDBDailyKSemanticProfiler,
)


class FakeSemanticAdapter:
    def __init__(self) -> None:
        self.chunk_summary_calls = 0

    def _validate_database_uri(self, value: str) -> None:
        if not value.startswith("dfs://"):
            raise DataContractError("bad uri")

    def _validate_table_name(self, value: str) -> None:
        if not value.replace("_", "").isalnum():
            raise DataContractError("bad table")

    def run_readonly_query(self, script: str) -> Any:
        normalized = " ".join(script.split())

        if "max(trade_date)" in normalized:
            return [{"max_trade_date": "2026-05-29"}]

        if "volume_share_float_10k_percent_match_count" in normalized:
            return [{
                "comparable_row_count": 1000,
                "volume_share_float_10k_percent_match_count": 999,
                "volume_lot_float_10k_percent_match_count": 10,
                "same_unit_percent_match_count": 0,
            }]

        if "scale_1_1_close_match_count" in normalized:
            return [{
                "comparable_row_count": 1000,
                "scale_1_1_close_match_count": 100,
                "scale_1_100_close_match_count": 10,
                "scale_100_1_close_match_count": 300,
                "scale_10000_1_close_match_count": 20,
                "scale_100_1_adj_price_match_count": 400,
            }]

        if "close_multiply_factor_match_count" in normalized:
            return [{
                "comparable_row_count": 1000,
                "close_multiply_factor_match_count": 100,
                "close_divide_factor_match_count": 50,
                "close_multiply_factor_minus_deduct_match_count": 1000,
                "close_minus_deduct_multiply_factor_match_count": 80,
                "close_multiply_factor_plus_deduct_match_count": 30,
                "close_plus_deduct_multiply_factor_match_count": 20,
                "deduct_value_nonzero_count": 900,
            }]

        if "select distinct stock_code" in normalized:
            return [
                {"stock_code": "000001"},
                {"stock_code": "000002"},
                {"stock_code": "000003"},
            ]

        if "as anomaly_row_count" in normalized:
            self.chunk_summary_calls += 1

            if self.chunk_summary_calls == 1:
                return [{
                    "total_context_row_count": 600,
                    "comparable_row_count": 598,
                    "anomaly_row_count": 1,
                    "anomaly_adj_factor_changed_count": 1,
                    "anomaly_dividend_present_count": 1,
                    "anomaly_dividend_nonzero_count": 1,
                    "anomaly_bonus_share_present_count": 0,
                    "anomaly_bonus_share_nonzero_count": 0,
                    "anomaly_convert_share_present_count": 0,
                    "anomaly_convert_share_nonzero_count": 0,
                    "anomaly_allot_share_present_count": 0,
                    "anomaly_allot_share_nonzero_count": 0,
                    "anomaly_allot_price_present_count": 0,
                    "anomaly_allot_price_nonzero_count": 0,
                    "pct_change_negated_formula_exception_count": 1,
                }]

            return [{
                "total_context_row_count": 400,
                "comparable_row_count": 400,
                "anomaly_row_count": 1,
                "anomaly_adj_factor_changed_count": 1,
                "anomaly_dividend_present_count": 1,
                "anomaly_dividend_nonzero_count": 1,
                "anomaly_bonus_share_present_count": 1,
                "anomaly_bonus_share_nonzero_count": 1,
                "anomaly_convert_share_present_count": 0,
                "anomaly_convert_share_nonzero_count": 0,
                "anomaly_allot_share_present_count": 0,
                "anomaly_allot_share_nonzero_count": 0,
                "anomaly_allot_price_present_count": 0,
                "anomaly_allot_price_nonzero_count": 0,
                "pct_change_negated_formula_exception_count": 1,
            }]

        if "select top 5" in normalized:
            return [{
                "stock_code": "000001",
                "trade_date": "1991-04-04",
                "prev_close": 49.0,
                "close": 48.76,
                "price_change": -0.24,
                "expected_price_change": -0.24,
                "price_change_error": 0.5,
                "pct_change": 0.49,
                "expected_negated_pct_change": 0.49,
                "prev_adj_factor": 1.0,
                "adj_factor": 1.1,
            }]

        raise AssertionError(f"未识别的查询：{normalized}")


class TestDailyKSemanticProfiler(unittest.TestCase):
    def _report(self):
        return DolphinDBDailyKSemanticProfiler(
            adapter=FakeSemanticAdapter(),
            anomaly_chunk_size=2,
        ).collect()

    def test_turnover_candidate_is_confirmed(self) -> None:
        report = self._report()
        conclusion = next(
            item
            for item in report.conclusions
            if item["topic"] == "TURNOVER_AND_SHARE_UNIT"
        )

        self.assertEqual(
            conclusion["candidate"],
            "volume_share_float_10k_turnover_percent",
        )
        self.assertTrue(conclusion["confirmed"])

    def test_amount_candidate_remains_pending(self) -> None:
        report = self._report()
        conclusion = next(
            item
            for item in report.conclusions
            if item["topic"] == "AMOUNT_VOLUME_SCALE"
        )

        self.assertEqual(conclusion["coverage"], 0.4)
        self.assertFalse(conclusion["confirmed"])

    def test_adjustment_formula_is_confirmed(self) -> None:
        report = self._report()
        conclusion = next(
            item
            for item in report.conclusions
            if item["topic"] == "ADJUSTMENT_FORMULA"
        )

        self.assertEqual(
            conclusion["candidate"],
            "adj_price_equals_close_multiply_factor_minus_deduct",
        )
        self.assertTrue(conclusion["confirmed"])

    def test_price_change_exceptions_are_retained(self) -> None:
        report = self._report()

        self.assertEqual(
            report.price_change_anomaly_summary[
                "anomaly_row_count"
            ],
            2,
        )
        self.assertEqual(
            len(report.price_change_anomaly_samples),
            1,
        )
        self.assertTrue(report.blocks_downstream)

    def test_anomaly_event_counts_are_conditional(self) -> None:
        report = self._report()
        summary = report.price_change_anomaly_summary

        self.assertEqual(summary["anomaly_row_count"], 2)
        self.assertEqual(
            summary["anomaly_adj_factor_changed_count"],
            2,
        )
        self.assertEqual(
            summary["anomaly_dividend_nonzero_count"],
            2,
        )

    def test_calendar_lag_is_calculated(self) -> None:
        utc_today = datetime.now(timezone.utc).date()
        lag = DolphinDBDailyKSemanticProfiler._calendar_lag_days(
            utc_today
        )
        self.assertEqual(lag, 0)

    def test_best_candidate_handles_empty_input(self) -> None:
        name, coverage = (
            DolphinDBDailyKSemanticProfiler._best_candidate({})
        )
        self.assertIsNone(name)
        self.assertIsNone(coverage)

    def test_anomaly_query_is_chunked(self) -> None:
        report = self._report()
        summary = report.price_change_anomaly_summary

        self.assertEqual(summary["stock_code_count"], 3)
        self.assertEqual(summary["chunk_count"], 2)
        self.assertEqual(summary["comparable_row_count"], 998)
        self.assertEqual(summary["anomaly_row_count"], 2)

    def test_invalid_chunk_size_raises_error(self) -> None:
        with self.assertRaises(DataContractError):
            DolphinDBDailyKSemanticProfiler(
                adapter=FakeSemanticAdapter(),
                anomaly_chunk_size=0,
            )


if __name__ == "__main__":
    unittest.main()
