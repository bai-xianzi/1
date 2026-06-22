"""测试DolphinDB真实环境只读探测命令。"""

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


class FakeAdapter:
    """用于探测命令测试的假适配器。"""

    def __init__(
        self,
        health: DataQualityResult,
        batch: RawDataBatch | None = None,
    ) -> None:
        self.health = health
        self.batch = batch
        self.read_called = False

    def health_check(self) -> DataQualityResult:
        return self.health

    def read_raw(
        self,
        source_object_name: str,
        **kwargs: object,
    ) -> RawDataBatch:
        self.read_called = True

        if self.batch is None:
            raise AssertionError("测试未提供batch。")

        return self.batch


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


class TestPasswordResolution(unittest.TestCase):
    """测试密码读取方式。"""

    def test_environment_password_has_priority(self) -> None:
        with patch.dict(
            os.environ,
            {"DOLPHINDB_PASSWORD": "secret"},
            clear=False,
        ):
            password = resolve_password(
                lambda prompt: self.fail("不应调用密码提示")
            )

        self.assertEqual(password, "secret")

    def test_prompt_is_used_when_environment_missing(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            password = resolve_password(lambda prompt: "prompt-secret")

        self.assertEqual(password, "prompt-secret")


class TestProbeCommand(unittest.TestCase):
    """测试健康检查和抽样流程。"""

    def test_parser_defaults(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            args = build_parser().parse_args([])

        self.assertEqual(args.host, "127.0.0.1")
        self.assertEqual(args.port, 8848)
        self.assertEqual(args.limit, 5)

    def test_successful_probe_reads_sample(self) -> None:
        adapter = FakeAdapter(
            health=passed_health(),
            batch=sample_batch(),
        )
        output = io.StringIO()

        with patch.dict(os.environ, {}, clear=True):
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

    def test_failed_health_does_not_read(self) -> None:
        adapter = FakeAdapter(health=failed_health())
        output = io.StringIO()

        with patch.dict(os.environ, {}, clear=True):
            with redirect_stdout(output):
                code = run_probe(
                    make_args(),
                    adapter_factory=lambda settings: adapter,
                    password_provider=lambda prompt: "secret",
                )

        self.assertEqual(code, 1)
        self.assertFalse(adapter.read_called)
        self.assertIn("停止读取", output.getvalue())

    def test_health_only_does_not_read(self) -> None:
        adapter = FakeAdapter(
            health=passed_health(),
            batch=sample_batch(),
        )

        with patch.dict(os.environ, {}, clear=True):
            code = run_probe(
                make_args(health_only=True),
                adapter_factory=lambda settings: adapter,
                password_provider=lambda prompt: "secret",
            )

        self.assertEqual(code, 0)
        self.assertFalse(adapter.read_called)

    def test_invalid_limit_returns_error(self) -> None:
        output = io.StringIO()

        with redirect_stdout(output):
            code = run_probe(
                make_args(limit=0),
                password_provider=lambda prompt: "secret",
            )

        self.assertEqual(code, 2)
        self.assertIn("limit", output.getvalue())


if __name__ == "__main__":
    unittest.main()
