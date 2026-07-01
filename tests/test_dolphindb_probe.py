"""测试DolphinDB真实环境只读探测命令。"""
# 测试模块总览：验证 `test_dolphindb_probe` 对应功能的合同、边界和历史回归行为。
# - 输入：构造样例、测试夹具、临时文件以及被测模块公开接口。
# - 处理：只执行测试和断言，不修改生产算法、金融语义或正式数据库。
# - 输出：可重复的通过/失败证据，供全量回归和任务验收使用。
# - 为什么这样写：把业务要求固化为自动测试，使后续注释迁移和重构能够证明行为未变化。

from __future__ import annotations

import argparse
import io
import os
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from a_stock_quant.data_contracts import (
    DataQualityResult,
    QualityLevel,
    QualityStatus,
    RawDataBatch,
    SourceType,
)
from a_stock_quant.dolphindb_probe import (
    build_parser,
    resolve_password,
    run_probe,
)


# 测试类 `FakeAdapter`：集中验证 `test_dolphindb_probe` 相关合同、边界条件和回归行为。
# - 输入：测试夹具、构造样例以及被测模块公开接口。
# - 处理：按独立场景组织断言，覆盖正常路径、失败门禁和关键边界。
# - 输出：通过或失败的单元测试结果，不产生正式业务数据。
# - 为什么这样写：把同一职责的回归场景集中管理，便于定位失败并防止后续修改破坏既有合同。
class FakeAdapter:
    """用于探测命令测试的假适配器。"""

    # 测试函数 `__init__`：封装 `__init__` 测试辅助步骤，减少重复样例和断言准备。
    # - 输入：health、batch。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def __init__(
        self,
        health: DataQualityResult,
        batch: RawDataBatch | None = None,
    ) -> None:
        self.health = health
        self.batch = batch
        self.read_called = False

    # 测试函数 `health_check`：封装 `health_check` 测试辅助步骤，减少重复样例和断言准备。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def health_check(self) -> DataQualityResult:
        return self.health

    # 测试函数 `read_raw`：封装 `read_raw` 测试辅助步骤，减少重复样例和断言准备。
    # - 输入：source_object_name、**kwargs。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def read_raw(
        self,
        source_object_name: str,
        **kwargs: object,
    ) -> RawDataBatch:
        self.read_called = True

        # 测试分支：根据 `self.batch is None` 选择对应断言或样例路径。
        # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
        # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
        if self.batch is None:
            raise AssertionError("测试未提供batch。")

        return self.batch


# 测试函数 `make_args`：封装 `make_args` 测试辅助步骤，减少重复样例和断言准备。
# - 输入：**overrides。
# - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
# - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
# - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
def make_args(**overrides: object) -> argparse.Namespace:
    """生成测试用参数。"""

    values = {
        "host": "127.0.0.1",
        "port": 8848,
        "username": "admin",
        "database_uri": "dfs://A_STOCK_DAILY_K_DB",
        "table": "stock_daily_k",
        "limit": 2,
        "preview_rows": 1,
        "health_only": False,
    }
    values.update(overrides)
    return argparse.Namespace(**values)


# 测试函数 `passed_health`：封装 `passed_health` 测试辅助步骤，减少重复样例和断言准备。
# - 输入：测试对象状态、固定样例或当前测试夹具。
# - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
# - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
# - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
def passed_health() -> DataQualityResult:
    return DataQualityResult(
        check_name="DolphinDB连接健康检查",
        level=QualityLevel.INFO,
        status=QualityStatus.PASSED,
        checked_row_count=1,
        failed_row_count=0,
        blocking=False,
        description="正常",
    )


# 测试函数 `failed_health`：封装 `failed_health` 测试辅助步骤，减少重复样例和断言准备。
# - 输入：测试对象状态、固定样例或当前测试夹具。
# - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
# - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
# - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
def failed_health() -> DataQualityResult:
    return DataQualityResult(
        check_name="DolphinDB连接健康检查",
        level=QualityLevel.CRITICAL,
        status=QualityStatus.FAILED,
        checked_row_count=1,
        failed_row_count=1,
        blocking=True,
        description="失败",
    )


# 测试函数 `sample_batch`：封装 `sample_batch` 测试辅助步骤，减少重复样例和断言准备。
# - 输入：测试对象状态、固定样例或当前测试夹具。
# - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
# - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
# - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
def sample_batch() -> RawDataBatch:
    return RawDataBatch(
        source_id="dolphindb_primary",
        source_type=SourceType.DOLPHINDB,
        source_object_name="stock_daily_k",
        raw_fields=["symbol", "trade_date", "close"],
        records=[
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
        ],
        source_location=(
            "dfs://A_STOCK_DAILY_K_DB/stock_daily_k"
        ),
    )


# 测试类 `TestPasswordResolution`：集中验证 `test_dolphindb_probe` 相关合同、边界条件和回归行为。
# - 输入：测试夹具、构造样例以及被测模块公开接口。
# - 处理：按独立场景组织断言，覆盖正常路径、失败门禁和关键边界。
# - 输出：通过或失败的单元测试结果，不产生正式业务数据。
# - 为什么这样写：把同一职责的回归场景集中管理，便于定位失败并防止后续修改破坏既有合同。
class TestPasswordResolution(unittest.TestCase):
    """测试密码读取方式。"""

    # 测试函数 `test_environment_password_has_priority`：验证 `environment、password、has、priority` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_environment_password_has_priority(self) -> None:
        # 测试上下文：通过 `patch.dict(os.environ, {'DOLPHINDB_PASSWORD': 'secret'}, clear=False)` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
        with patch.dict(
            os.environ,
            {"DOLPHINDB_PASSWORD": "secret"},
            clear=False,
        ):
            password = resolve_password(
                lambda prompt: self.fail("不应调用密码提示")
            )

        self.assertEqual(password, "secret")

    # 测试函数 `test_prompt_is_used_when_environment_missing`：验证 `prompt、is、used、when、environment、missing` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_prompt_is_used_when_environment_missing(self) -> None:
        # 测试上下文：通过 `patch.dict(os.environ, {}, clear=True)` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
        with patch.dict(os.environ, {}, clear=True):
            password = resolve_password(lambda prompt: "prompt-secret")

        self.assertEqual(password, "prompt-secret")


# 测试类 `TestProbeCommand`：集中验证 `test_dolphindb_probe` 相关合同、边界条件和回归行为。
# - 输入：测试夹具、构造样例以及被测模块公开接口。
# - 处理：按独立场景组织断言，覆盖正常路径、失败门禁和关键边界。
# - 输出：通过或失败的单元测试结果，不产生正式业务数据。
# - 为什么这样写：把同一职责的回归场景集中管理，便于定位失败并防止后续修改破坏既有合同。
class TestProbeCommand(unittest.TestCase):
    """测试健康检查和抽样流程。"""

    # 测试函数 `test_parser_defaults`：验证 `parser、defaults` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_parser_defaults(self) -> None:
        # 测试上下文：通过 `patch.dict(os.environ, {}, clear=True)` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
        with patch.dict(os.environ, {}, clear=True):
            args = build_parser().parse_args([])

        self.assertEqual(args.host, "127.0.0.1")
        self.assertEqual(args.port, 8848)
        self.assertEqual(args.limit, 5)

    # 测试函数 `test_successful_probe_reads_sample`：验证 `successful、probe、reads、sample` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_successful_probe_reads_sample(self) -> None:
        adapter = FakeAdapter(
            health=passed_health(),
            batch=sample_batch(),
        )
        output = io.StringIO()

        # 测试上下文：通过 `patch.dict(os.environ, {}, clear=True)` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
        with patch.dict(os.environ, {}, clear=True):
            # 测试上下文：通过 `redirect_stdout(output)` 管理异常断言、临时资源或子测试范围。
            # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
            # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
            with redirect_stdout(output):
                code = run_probe(
                    make_args(),
                    adapter_factory=lambda settings: adapter,
                    password_provider=lambda prompt: "secret",
                )

        self.assertEqual(code, 0)
        self.assertTrue(adapter.read_called)
        self.assertIn("读取行数：2", output.getvalue())
        self.assertIn("000001.SZ", output.getvalue())

    # 测试函数 `test_failed_health_does_not_read`：验证 `failed、health、does、not、read` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_failed_health_does_not_read(self) -> None:
        adapter = FakeAdapter(health=failed_health())
        output = io.StringIO()

        # 测试上下文：通过 `patch.dict(os.environ, {}, clear=True)` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
        with patch.dict(os.environ, {}, clear=True):
            # 测试上下文：通过 `redirect_stdout(output)` 管理异常断言、临时资源或子测试范围。
            # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
            # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
            with redirect_stdout(output):
                code = run_probe(
                    make_args(),
                    adapter_factory=lambda settings: adapter,
                    password_provider=lambda prompt: "secret",
                )

        self.assertEqual(code, 1)
        self.assertFalse(adapter.read_called)
        self.assertIn("停止读取", output.getvalue())

    # 测试函数 `test_health_only_does_not_read`：验证 `health、only、does、not、read` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_health_only_does_not_read(self) -> None:
        adapter = FakeAdapter(
            health=passed_health(),
            batch=sample_batch(),
        )

        # 测试上下文：通过 `patch.dict(os.environ, {}, clear=True)` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
        with patch.dict(os.environ, {}, clear=True):
            code = run_probe(
                make_args(health_only=True),
                adapter_factory=lambda settings: adapter,
                password_provider=lambda prompt: "secret",
            )

        self.assertEqual(code, 0)
        self.assertFalse(adapter.read_called)

    # 测试函数 `test_invalid_limit_returns_error`：验证 `invalid、limit、returns、error` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_invalid_limit_returns_error(self) -> None:
        output = io.StringIO()

        # 测试上下文：通过 `redirect_stdout(output)` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
        with redirect_stdout(output):
            code = run_probe(
                make_args(limit=0),
                password_provider=lambda prompt: "secret",
            )

        self.assertEqual(code, 2)
        self.assertIn("limit", output.getvalue())


if __name__ == "__main__":
    unittest.main()
