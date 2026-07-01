"""测试DolphinDB日K字段语义核验。"""
# 测试模块总览：验证 `test_dolphindb_daily_semantics` 对应功能的合同、边界和历史回归行为。
# - 输入：构造样例、测试夹具、临时文件以及被测模块公开接口。
# - 处理：只执行测试和断言，不修改生产算法、金融语义或正式数据库。
# - 输出：可重复的通过/失败证据，供全量回归和任务验收使用。
# - 为什么这样写：把业务要求固化为自动测试，使后续注释迁移和重构能够证明行为未变化。

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


# 测试类 `FakeSemanticAdapter`：集中验证 `test_dolphindb_daily_semantics` 相关合同、边界条件和回归行为。
# - 输入：测试夹具、构造样例以及被测模块公开接口。
# - 处理：按独立场景组织断言，覆盖正常路径、失败门禁和关键边界。
# - 输出：通过或失败的单元测试结果，不产生正式业务数据。
# - 为什么这样写：把同一职责的回归场景集中管理，便于定位失败并防止后续修改破坏既有合同。
class FakeSemanticAdapter:
    # 测试函数 `__init__`：封装 `__init__` 测试辅助步骤，减少重复样例和断言准备。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def __init__(self) -> None:
        self.chunk_summary_calls = 0

    # 测试函数 `_validate_database_uri`：封装 `_validate_database_uri` 测试辅助步骤，减少重复样例和断言准备。
    # - 输入：value。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def _validate_database_uri(self, value: str) -> None:
        # 测试分支：根据 `not value.startswith('dfs://')` 选择对应断言或样例路径。
        # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
        # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
        if not value.startswith("dfs://"):
            raise DataContractError("bad uri")

    # 测试函数 `_validate_table_name`：封装 `_validate_table_name` 测试辅助步骤，减少重复样例和断言准备。
    # - 输入：value。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def _validate_table_name(self, value: str) -> None:
        # 测试分支：根据 `not value.replace('_', '').isalnum()` 选择对应断言或样例路径。
        # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
        # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
        if not value.replace("_", "").isalnum():
            raise DataContractError("bad table")

    # 测试函数 `run_readonly_query`：封装 `run_readonly_query` 测试辅助步骤，减少重复样例和断言准备。
    # - 输入：script。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def run_readonly_query(self, script: str) -> Any:
        normalized = " ".join(script.split())

        # 测试分支：根据 `'max(trade_date)' in normalized` 选择对应断言或样例路径。
        # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
        # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
        if "max(trade_date)" in normalized:
            return [{"max_trade_date": "2026-05-29"}]

        # 测试分支：根据 `'volume_share_float_10k_percent_match_count' in normalized` 选择对应断言或样例路径。
        # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
        # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
        if "volume_share_float_10k_percent_match_count" in normalized:
            return [{
                "comparable_row_count": 1000,
                "volume_share_float_10k_percent_match_count": 999,
                "volume_lot_float_10k_percent_match_count": 10,
                "same_unit_percent_match_count": 0,
            }]

        # 测试分支：根据 `'scale_1_1_close_match_count' in normalized` 选择对应断言或样例路径。
        # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
        # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
        if "scale_1_1_close_match_count" in normalized:
            return [{
                "comparable_row_count": 1000,
                "scale_1_1_close_match_count": 100,
                "scale_1_100_close_match_count": 10,
                "scale_100_1_close_match_count": 300,
                "scale_10000_1_close_match_count": 20,
                "scale_100_1_adj_price_match_count": 400,
            }]

        # 测试分支：根据 `'close_multiply_factor_match_count' in normalized` 选择对应断言或样例路径。
        # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
        # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
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

        # 测试分支：根据 `'select distinct stock_code' in normalized` 选择对应断言或样例路径。
        # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
        # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
        if "select distinct stock_code" in normalized:
            return [
                {"stock_code": "000001"},
                {"stock_code": "000002"},
                {"stock_code": "000003"},
            ]

        # 测试分支：根据 `'as anomaly_row_count' in normalized` 选择对应断言或样例路径。
        # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
        # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
        if "as anomaly_row_count" in normalized:
            self.chunk_summary_calls += 1

            # 测试分支：根据 `self.chunk_summary_calls == 1` 选择对应断言或样例路径。
            # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
            # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
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

        # 测试分支：根据 `'select top 5' in normalized` 选择对应断言或样例路径。
        # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
        # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
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


# 测试类 `TestDailyKSemanticProfiler`：集中验证 `test_dolphindb_daily_semantics` 相关合同、边界条件和回归行为。
# - 输入：测试夹具、构造样例以及被测模块公开接口。
# - 处理：按独立场景组织断言，覆盖正常路径、失败门禁和关键边界。
# - 输出：通过或失败的单元测试结果，不产生正式业务数据。
# - 为什么这样写：把同一职责的回归场景集中管理，便于定位失败并防止后续修改破坏既有合同。
class TestDailyKSemanticProfiler(unittest.TestCase):
    # 测试函数 `_report`：封装 `_report` 测试辅助步骤，减少重复样例和断言准备。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def _report(self):
        return DolphinDBDailyKSemanticProfiler(
            adapter=FakeSemanticAdapter(),
            anomaly_chunk_size=2,
        ).collect()

    # 测试函数 `test_turnover_candidate_is_confirmed`：验证 `turnover、candidate、is、confirmed` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
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

    # 测试函数 `test_amount_candidate_remains_pending`：验证 `amount、candidate、remains、pending` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_amount_candidate_remains_pending(self) -> None:
        report = self._report()
        conclusion = next(
            item
            for item in report.conclusions
            if item["topic"] == "AMOUNT_VOLUME_SCALE"
        )

        self.assertEqual(conclusion["coverage"], 0.4)
        self.assertFalse(conclusion["confirmed"])

    # 测试函数 `test_adjustment_formula_is_confirmed`：验证 `adjustment、formula、is、confirmed` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
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

    # 测试函数 `test_price_change_exceptions_are_retained`：验证 `price、change、exceptions、are、retained` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
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

    # 测试函数 `test_anomaly_event_counts_are_conditional`：验证 `anomaly、event、counts、are、conditional` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
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

    # 测试函数 `test_calendar_lag_is_calculated`：验证 `calendar、lag、is、calculated` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_calendar_lag_is_calculated(self) -> None:
        utc_today = datetime.now(timezone.utc).date()
        lag = DolphinDBDailyKSemanticProfiler._calendar_lag_days(
            utc_today
        )
        self.assertEqual(lag, 0)

    # 测试函数 `test_best_candidate_handles_empty_input`：验证 `best、candidate、handles、empty、input` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_best_candidate_handles_empty_input(self) -> None:
        name, coverage = (
            DolphinDBDailyKSemanticProfiler._best_candidate({})
        )
        self.assertIsNone(name)
        self.assertIsNone(coverage)

    # 测试函数 `test_anomaly_query_is_chunked`：验证 `anomaly、query、is、chunked` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_anomaly_query_is_chunked(self) -> None:
        report = self._report()
        summary = report.price_change_anomaly_summary

        self.assertEqual(summary["stock_code_count"], 3)
        self.assertEqual(summary["chunk_count"], 2)
        self.assertEqual(summary["comparable_row_count"], 998)
        self.assertEqual(summary["anomaly_row_count"], 2)

    # 测试函数 `test_invalid_chunk_size_raises_error`：验证 `invalid、chunk、size、raises、error` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_invalid_chunk_size_raises_error(self) -> None:
        # 测试上下文：通过 `self.assertRaises(DataContractError)` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
        with self.assertRaises(DataContractError):
            DolphinDBDailyKSemanticProfiler(
                adapter=FakeSemanticAdapter(),
                anomaly_chunk_size=0,
            )


if __name__ == "__main__":
    unittest.main()
