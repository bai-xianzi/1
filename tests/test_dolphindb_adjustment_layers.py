"""测试DolphinDB日K复权字段分层核验。"""
# 测试模块总览：验证 `test_dolphindb_adjustment_layers` 对应功能的合同、边界和历史回归行为。
# - 输入：构造样例、测试夹具、临时文件以及被测模块公开接口。
# - 处理：只执行测试和断言，不修改生产算法、金融语义或正式数据库。
# - 输出：可重复的通过/失败证据，供全量回归和任务验收使用。
# - 为什么这样写：把业务要求固化为自动测试，使后续注释迁移和重构能够证明行为未变化。

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


# 测试类 `FakeAdjustmentAdapter`：集中验证 `test_dolphindb_adjustment_layers` 相关合同、边界条件和回归行为。
# - 输入：测试夹具、构造样例以及被测模块公开接口。
# - 处理：按独立场景组织断言，覆盖正常路径、失败门禁和关键边界。
# - 输出：通过或失败的单元测试结果，不产生正式业务数据。
# - 为什么这样写：把同一职责的回归场景集中管理，便于定位失败并防止后续修改破坏既有合同。
class FakeAdjustmentAdapter:
    # 测试函数 `__init__`：封装 `__init__` 测试辅助步骤，减少重复样例和断言准备。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def __init__(self) -> None:
        self.factor_summary_calls = 0
        self.layer_calls = 0
        self.transient_failures_remaining = 0

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

        # 测试分支：根据 `self.transient_failures_remaining > 0 and 'max(trade_date)' in normalized` 选择对应断言或样例路径。
        # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
        # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
        if (
            self.transient_failures_remaining > 0
            and "max(trade_date)" in normalized
        ):
            self.transient_failures_remaining -= 1
            raise DataContractError(
                "DolphinDB只读查询失败：Can't open file"
            )

        # 测试分支：根据 `'max(trade_date)' in normalized` 选择对应断言或样例路径。
        # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
        # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
        if "max(trade_date)" in normalized:
            return [{"max_trade_date": "2026-06-20"}]

        # 测试分支：根据 `'select distinct stock_code' in normalized` 选择对应断言或样例路径。
        # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
        # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
        if "select distinct stock_code" in normalized:
            return [
                {"stock_code": "000001"},
                {"stock_code": "000002"},
                {"stock_code": "000003"},
            ]

        # 测试分支：根据 `'deduct_zero_action_zero_comparable_row_count' in normalized` 选择对应断言或样例路径。
        # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
        # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
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

        # 测试分支：根据 `'as factor_change_count' in normalized` 选择对应断言或样例路径。
        # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
        # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
        if "as factor_change_count" in normalized:
            self.factor_summary_calls += 1
            return [{
                "factor_change_count": 2,
                "factor_change_deduct_nonzero_count": 2,
                "factor_change_action_nonzero_count": 1,
                "factor_change_adj_price_equal_close_count": 0,
            }]

        # 测试分支：根据 `'select top 3' in normalized` 选择对应断言或样例路径。
        # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
        # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
        if "select top 3" in normalized:
            return [{
                "stock_code": "000001",
                "trade_date": "2026-05-20",
                "prev_adj_factor": 10.0,
                "adj_factor": 11.0,
            }]

        raise AssertionError(f"未识别的查询：{normalized}")


# 测试类 `TestAdjustmentLayerProfiler`：集中验证 `test_dolphindb_adjustment_layers` 相关合同、边界条件和回归行为。
# - 输入：测试夹具、构造样例以及被测模块公开接口。
# - 处理：按独立场景组织断言，覆盖正常路径、失败门禁和关键边界。
# - 输出：通过或失败的单元测试结果，不产生正式业务数据。
# - 为什么这样写：把同一职责的回归场景集中管理，便于定位失败并防止后续修改破坏既有合同。
class TestAdjustmentLayerProfiler(unittest.TestCase):
    # 测试函数 `_profiler`：封装 `_profiler` 测试辅助步骤，减少重复样例和断言准备。
    # - 输入：adapter。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def _profiler(self, adapter=None):
        return DolphinDBAdjustmentLayerProfiler(
            adapter=adapter or FakeAdjustmentAdapter(),
            factor_chunk_size=2,
        )

    # 测试函数 `_report`：封装 `_report` 测试辅助步骤，减少重复样例和断言准备。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def _report(self):
        return self._profiler().collect()

    # 测试函数 `test_collects_four_layers`：验证 `collects、four、layers` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_collects_four_layers(self) -> None:
        report = self._report()
        self.assertEqual(len(report.formula_layers), 4)

    # 测试函数 `test_formula_layers_are_chunked_and_merged`：验证 `formula、layers、are、chunked、and、merged` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
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

    # 测试函数 `test_zero_deduct_layer_can_be_confirmed`：验证 `zero、deduct、layer、can、be、confirmed` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
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

    # 测试函数 `test_nonzero_deduct_layer_stays_pending`：验证 `nonzero、deduct、layer、stays、pending` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
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

    # 测试函数 `test_factor_changes_are_chunked_and_merged`：验证 `factor、changes、are、chunked、and、merged` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_factor_changes_are_chunked_and_merged(self) -> None:
        report = self._report()
        summary = report.factor_change_summary
        self.assertEqual(summary["stock_code_count"], 3)
        self.assertEqual(summary["chunk_count"], 2)
        self.assertEqual(summary["factor_change_count"], 4)

    # 测试函数 `test_duplicate_samples_are_removed`：验证 `duplicate、samples、are、removed` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_duplicate_samples_are_removed(self) -> None:
        report = self._report()
        self.assertEqual(len(report.factor_change_samples), 1)

    # 测试函数 `test_transient_file_open_error_is_retried`：验证 `transient、file、open、error、is、retried` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_transient_file_open_error_is_retried(self) -> None:
        adapter = FakeAdjustmentAdapter()
        adapter.transient_failures_remaining = 1
        report = self._profiler(adapter).collect()
        self.assertEqual(
            str(report.latest_trade_date),
            "2026-06-20",
        )

    # 测试函数 `test_persistent_file_open_error_is_raised`：验证 `persistent、file、open、error、is、raised` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_persistent_file_open_error_is_raised(self) -> None:
        adapter = FakeAdjustmentAdapter()
        adapter.transient_failures_remaining = 5

        # 测试上下文：通过 `self.assertRaises(DataContractError)` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
        with self.assertRaises(DataContractError):
            self._profiler(adapter).collect()

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
            DolphinDBAdjustmentLayerProfiler(
                adapter=FakeAdjustmentAdapter(),
                factor_chunk_size=0,
            )

    # 测试函数 `test_best_candidate_handles_empty_input`：验证 `best、candidate、handles、empty、input` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_best_candidate_handles_empty_input(self) -> None:
        name, coverage = (
            DolphinDBAdjustmentLayerProfiler._best_candidate({})
        )
        self.assertIsNone(name)
        self.assertIsNone(coverage)


if __name__ == "__main__":
    unittest.main()
