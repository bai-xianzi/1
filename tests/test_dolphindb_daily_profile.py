"""测试DolphinDB日K只读画像。"""
# 测试模块总览：验证 `test_dolphindb_daily_profile` 对应功能的合同、边界和历史回归行为。
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


# 测试类 `FakeSession`：集中验证 `test_dolphindb_daily_profile` 相关合同、边界条件和回归行为。
# - 输入：测试夹具、构造样例以及被测模块公开接口。
# - 处理：按独立场景组织断言，覆盖正常路径、失败门禁和关键边界。
# - 输出：通过或失败的单元测试结果，不产生正式业务数据。
# - 为什么这样写：把同一职责的回归场景集中管理，便于定位失败并防止后续修改破坏既有合同。
class FakeSession:
    # 测试函数 `__init__`：封装 `__init__` 测试辅助步骤，减少重复样例和断言准备。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def __init__(self) -> None:
        self.last_script: str | None = None

    # 测试函数 `connect`：封装 `connect` 测试辅助步骤，减少重复样例和断言准备。
    # - 输入：host、port、user_id、password。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def connect(
        self,
        host: str,
        port: int,
        user_id: str,
        password: str,
    ) -> bool:
        return True

    # 测试函数 `run`：封装 `run` 测试辅助步骤，减少重复样例和断言准备。
    # - 输入：script。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def run(self, script: str) -> Any:
        self.last_script = script
        return [{"row_count": 1}]


# 测试类 `FakeProfileAdapter`：集中验证 `test_dolphindb_daily_profile` 相关合同、边界条件和回归行为。
# - 输入：测试夹具、构造样例以及被测模块公开接口。
# - 处理：按独立场景组织断言，覆盖正常路径、失败门禁和关键边界。
# - 输出：通过或失败的单元测试结果，不产生正式业务数据。
# - 为什么这样写：把同一职责的回归场景集中管理，便于定位失败并防止后续修改破坏既有合同。
class FakeProfileAdapter:
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

    # 测试函数 `read_raw`：封装 `read_raw` 测试辅助步骤，减少重复样例和断言准备。
    # - 输入：source_object_name、**kwargs。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
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

    # 测试函数 `run_readonly_query`：封装 `run_readonly_query` 测试辅助步骤，减少重复样例和断言准备。
    # - 输入：script。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def run_readonly_query(self, script: str) -> Any:
        normalized = " ".join(script.split())

        # 测试分支：根据 `'nunique(stock_code' in normalized` 选择对应断言或样例路径。
        # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
        # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
        if "nunique(stock_code" in normalized:
            return [{
                "row_count": 100,
                "stock_count": 2,
                "min_trade_date": "1990-12-19",
                "max_trade_date": "2026-06-20",
            }]

        # 测试分支：根据 `'stock_code_null_count' in normalized` 选择对应断言或样例路径。
        # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
        # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
        if "stock_code_null_count" in normalized:
            return [{
                "stock_code_null_count": 0,
                "trade_date_null_count": 0,
            }]

        # 测试分支：根据 `'duplicate_group_count' in normalized` 选择对应断言或样例路径。
        # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
        # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
        if "duplicate_group_count" in normalized:
            return [{
                "duplicate_group_count": 0,
                "duplicate_extra_row_count": 0,
            }]

        # 测试分支：根据 `'count(*) as duplicate_count' in normalized and 'top 20' in normalized` 选择对应断言或样例路径。
        # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
        # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
        if (
            "count(*) as duplicate_count" in normalized
            and "top 20" in normalized
        ):
            return []

        # 测试分支：根据 `'open_nonpositive_count' in normalized` 选择对应断言或样例路径。
        # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
        # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
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

        # 测试分支：根据 `'price_change_mismatch_count' in normalized` 选择对应断言或样例路径。
        # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
        # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
        if "price_change_mismatch_count" in normalized:
            return [{
                "comparable_row_count": 98,
                "price_change_mismatch_count": 0,
                "pct_change_standard_mismatch_count": 90,
                "pct_change_inverse_mismatch_count": 80,
                "pct_change_negated_standard_mismatch_count": 0,
            }]

        # 测试分支：根据 `'expected_standard_pct_change' in normalized` 选择对应断言或样例路径。
        # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
        # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
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

        # 测试分支：根据 `'avg_amount_per_volume' in normalized` 选择对应断言或样例路径。
        # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
        # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
        if "avg_amount_per_volume" in normalized:
            return [{
                "comparable_row_count": 100,
                "min_amount_per_volume": 7.4,
                "avg_amount_per_volume": 8.0,
                "max_amount_per_volume": 10.0,
            }]

        # 测试分支：根据 `'adj_factor_non_one_count' in normalized` 选择对应断言或样例路径。
        # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
        # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
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


# 测试类 `TestReadonlyQuerySafety`：集中验证 `test_dolphindb_daily_profile` 相关合同、边界条件和回归行为。
# - 输入：测试夹具、构造样例以及被测模块公开接口。
# - 处理：按独立场景组织断言，覆盖正常路径、失败门禁和关键边界。
# - 输出：通过或失败的单元测试结果，不产生正式业务数据。
# - 为什么这样写：把同一职责的回归场景集中管理，便于定位失败并防止后续修改破坏既有合同。
class TestReadonlyQuerySafety(unittest.TestCase):
    # 测试函数 `_adapter`：封装 `_adapter` 测试辅助步骤，减少重复样例和断言准备。
    # - 输入：session。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
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

    # 测试函数 `test_select_query_is_allowed`：验证 `select、query、is、allowed` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_select_query_is_allowed(self) -> None:
        result = self._adapter(FakeSession()).run_readonly_query(
            "select count(*) from loadTable("
            '"dfs://A_STOCK_DAILY_K_DB", `stock_daily_k)'
        )
        self.assertEqual(result, [{"row_count": 1}])

    # 测试函数 `test_update_query_is_rejected`：验证 `update、query、is、rejected` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_update_query_is_rejected(self) -> None:
        # 测试上下文：通过 `self.assertRaises(DataContractError)` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
        with self.assertRaises(DataContractError):
            self._adapter(FakeSession()).run_readonly_query(
                "update t set close = 1"
            )

    # 测试函数 `test_semicolon_is_rejected`：验证 `semicolon、is、rejected` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_semicolon_is_rejected(self) -> None:
        # 测试上下文：通过 `self.assertRaises(DataContractError)` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
        with self.assertRaises(DataContractError):
            self._adapter(FakeSession()).run_readonly_query(
                "select count(*) from t; drop table t"
            )


# 测试类 `TestDailyKProfiler`：集中验证 `test_dolphindb_daily_profile` 相关合同、边界条件和回归行为。
# - 输入：测试夹具、构造样例以及被测模块公开接口。
# - 处理：按独立场景组织断言，覆盖正常路径、失败门禁和关键边界。
# - 输出：通过或失败的单元测试结果，不产生正式业务数据。
# - 为什么这样写：把同一职责的回归场景集中管理，便于定位失败并防止后续修改破坏既有合同。
class TestDailyKProfiler(unittest.TestCase):
    # 测试函数 `test_collect_builds_report`：验证 `collect、builds、report` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
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

    # 测试函数 `test_pending_confirmations_are_created`：验证 `pending、confirmations、are、created` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
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

    # 测试函数 `test_required_fields_pass`：验证 `required、fields、pass` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
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

    # 测试函数 `test_json_safe_converts_nan`：验证 `json、safe、converts、nan` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_json_safe_converts_nan(self) -> None:
        self.assertIsNone(_json_safe({"x": float("nan")})["x"])

    # 测试函数 `test_nan_duplicate_count_is_normalized_to_zero`：验证 `nan、duplicate、count、is、normalized、to、zero` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_nan_duplicate_count_is_normalized_to_zero(self) -> None:
        profiler = DolphinDBDailyKProfiler(
            adapter=FakeProfileAdapter(),
        )
        self.assertEqual(profiler._as_int(float("nan")), 0)

    # 测试函数 `test_negated_standard_formula_is_recorded`：验证 `negated、standard、formula、is、recorded` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
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

    # 测试函数 `test_adjustment_equal_counts_are_recorded`：验证 `adjustment、equal、counts、are、recorded` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
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
