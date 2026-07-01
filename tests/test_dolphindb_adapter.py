"""测试 DolphinDB 只读适配器。"""
# 测试模块总览：验证 `test_dolphindb_adapter` 对应功能的合同、边界和历史回归行为。
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
    QualityStatus,
    SourceType,
)
from a_stock_quant.dolphindb_adapter import (
    DolphinDBConnectionSettings,
    DolphinDBDataSourceAdapter,
)


# 测试类 `FakeSession`：集中验证 `test_dolphindb_adapter` 相关合同、边界条件和回归行为。
# - 输入：测试夹具、构造样例以及被测模块公开接口。
# - 处理：按独立场景组织断言，覆盖正常路径、失败门禁和关键边界。
# - 输出：通过或失败的单元测试结果，不产生正式业务数据。
# - 为什么这样写：把同一职责的回归场景集中管理，便于定位失败并防止后续修改破坏既有合同。
class FakeSession:
    """用于测试的假DolphinDB会话。"""

    # 测试函数 `__init__`：封装 `__init__` 测试辅助步骤，减少重复样例和断言准备。
    # - 输入：run_result、run_error。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def __init__(
        self,
        run_result: Any = None,
        run_error: Exception | None = None,
    ) -> None:
        self.run_result = run_result
        self.run_error = run_error
        self.connected = False
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
        self.connected = True
        return True

    # 测试函数 `run`：封装 `run` 测试辅助步骤，减少重复样例和断言准备。
    # - 输入：script。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def run(self, script: str) -> Any:
        self.last_script = script

        # 测试分支：根据 `self.run_error is not None` 选择对应断言或样例路径。
        # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
        # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
        if self.run_error is not None:
            raise self.run_error

        return self.run_result


# 测试类 `TestDolphinDBConnectionSettings`：集中验证 `test_dolphindb_adapter` 相关合同、边界条件和回归行为。
# - 输入：测试夹具、构造样例以及被测模块公开接口。
# - 处理：按独立场景组织断言，覆盖正常路径、失败门禁和关键边界。
# - 输出：通过或失败的单元测试结果，不产生正式业务数据。
# - 为什么这样写：把同一职责的回归场景集中管理，便于定位失败并防止后续修改破坏既有合同。
class TestDolphinDBConnectionSettings(unittest.TestCase):
    """测试连接参数。"""

    # 测试函数 `test_invalid_port_raises_error`：验证 `invalid、port、raises、error` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_invalid_port_raises_error(self) -> None:
        # 测试上下文：通过 `self.assertRaises(DataContractError)` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
        with self.assertRaises(DataContractError):
            DolphinDBConnectionSettings(
                host="127.0.0.1",
                port=70000,
                username="admin",
                password="123456",
            )


# 测试类 `TestDolphinDBDataSourceAdapter`：集中验证 `test_dolphindb_adapter` 相关合同、边界条件和回归行为。
# - 输入：测试夹具、构造样例以及被测模块公开接口。
# - 处理：按独立场景组织断言，覆盖正常路径、失败门禁和关键边界。
# - 输出：通过或失败的单元测试结果，不产生正式业务数据。
# - 为什么这样写：把同一职责的回归场景集中管理，便于定位失败并防止后续修改破坏既有合同。
class TestDolphinDBDataSourceAdapter(unittest.TestCase):
    """测试只读适配器。"""

    # 测试函数 `_settings`：封装 `_settings` 测试辅助步骤，减少重复样例和断言准备。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def _settings(self) -> DolphinDBConnectionSettings:
        return DolphinDBConnectionSettings(
            host="127.0.0.1",
            port=8848,
            username="admin",
            password="123456",
        )

    # 测试函数 `test_health_check_passes`：验证 `health、check、passes` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_health_check_passes(self) -> None:
        session = FakeSession(run_result=2)
        adapter = DolphinDBDataSourceAdapter(
            settings=self._settings(),
            session_factory=lambda: session,
        )

        result = adapter.health_check()

        self.assertEqual(result.status, QualityStatus.PASSED)
        self.assertFalse(result.blocks_downstream)
        self.assertTrue(session.connected)
        self.assertEqual(session.last_script, "1 + 1")

    # 测试函数 `test_health_check_failure_is_structured`：验证 `health、check、failure、is、structured` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_health_check_failure_is_structured(self) -> None:
        session = FakeSession(run_error=RuntimeError("server unavailable"))
        adapter = DolphinDBDataSourceAdapter(
            settings=self._settings(),
            session_factory=lambda: session,
        )

        result = adapter.health_check()

        self.assertEqual(result.status, QualityStatus.FAILED)
        self.assertTrue(result.blocks_downstream)

    # 测试函数 `test_read_raw_returns_batch`：验证 `read、raw、returns、batch` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_read_raw_returns_batch(self) -> None:
        session = FakeSession(
            run_result=[
                {
                    "symbol": "000001.SZ",
                    "trade_date": "2026-06-20",
                    "close": 12.34,
                },
                {
                    "symbol": "000002.SZ",
                    "trade_date": "2026-06-20",
                    "close": 8.76,
                },
            ]
        )
        adapter = DolphinDBDataSourceAdapter(
            settings=self._settings(),
            session_factory=lambda: session,
        )

        batch = adapter.read_raw(
            "stock_daily_k",
            database_uri="dfs://A_STOCK_DAILY_K_DB",
            limit=2,
        )

        self.assertEqual(batch.source_type, SourceType.DOLPHINDB)
        self.assertEqual(batch.row_count, 2)
        self.assertEqual(
            batch.raw_fields,
            ["symbol", "trade_date", "close"],
        )
        self.assertIn("select top 2", session.last_script or "")
        self.assertIn("loadTable", session.last_script or "")

    # 测试函数 `test_invalid_table_name_is_rejected`：验证 `invalid、table、name、is、rejected` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_invalid_table_name_is_rejected(self) -> None:
        adapter = DolphinDBDataSourceAdapter(
            settings=self._settings(),
            session_factory=lambda: FakeSession([]),
        )

        # 测试上下文：通过 `self.assertRaises(DataContractError)` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
        with self.assertRaises(DataContractError):
            adapter.read_raw(
                "stock_daily_k;drop database",
                database_uri="dfs://A_STOCK_DAILY_K_DB",
            )

    # 测试函数 `test_invalid_limit_is_rejected`：验证 `invalid、limit、is、rejected` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_invalid_limit_is_rejected(self) -> None:
        adapter = DolphinDBDataSourceAdapter(
            settings=self._settings(),
            session_factory=lambda: FakeSession([]),
        )

        # 测试上下文：通过 `self.assertRaises(DataContractError)` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
        with self.assertRaises(DataContractError):
            adapter.read_raw(
                "stock_daily_k",
                database_uri="dfs://A_STOCK_DAILY_K_DB",
                limit=0,
            )


if __name__ == "__main__":
    unittest.main()
