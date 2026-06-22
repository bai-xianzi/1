"""测试 DolphinDB 只读适配器。"""

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


class FakeSession:
    """用于测试的假DolphinDB会话。"""

    def __init__(
        self,
        run_result: Any = None,
        run_error: Exception | None = None,
    ) -> None:
        self.run_result = run_result
        self.run_error = run_error
        self.connected = False
        self.last_script: str | None = None

    def connect(
        self,
        host: str,
        port: int,
        user_id: str,
        password: str,
    ) -> bool:
        self.connected = True
        return True

    def run(self, script: str) -> Any:
        self.last_script = script

        if self.run_error is not None:
            raise self.run_error

        return self.run_result


class TestDolphinDBConnectionSettings(unittest.TestCase):
    """测试连接参数。"""

    def test_invalid_port_raises_error(self) -> None:
        with self.assertRaises(DataContractError):
            DolphinDBConnectionSettings(
                host="127.0.0.1",
                port=70000,
                username="admin",
                password="123456",
            )


class TestDolphinDBDataSourceAdapter(unittest.TestCase):
    """测试只读适配器。"""

    def _settings(self) -> DolphinDBConnectionSettings:
        return DolphinDBConnectionSettings(
            host="127.0.0.1",
            port=8848,
            username="admin",
            password="123456",
        )

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

    def test_health_check_failure_is_structured(self) -> None:
        session = FakeSession(run_error=RuntimeError("server unavailable"))
        adapter = DolphinDBDataSourceAdapter(
            settings=self._settings(),
            session_factory=lambda: session,
        )

        result = adapter.health_check()

        self.assertEqual(result.status, QualityStatus.FAILED)
        self.assertTrue(result.blocks_downstream)

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

    def test_invalid_table_name_is_rejected(self) -> None:
        adapter = DolphinDBDataSourceAdapter(
            settings=self._settings(),
            session_factory=lambda: FakeSession([]),
        )

        with self.assertRaises(DataContractError):
            adapter.read_raw(
                "stock_daily_k;drop database",
                database_uri="dfs://A_STOCK_DAILY_K_DB",
            )

    def test_invalid_limit_is_rejected(self) -> None:
        adapter = DolphinDBDataSourceAdapter(
            settings=self._settings(),
            session_factory=lambda: FakeSession([]),
        )

        with self.assertRaises(DataContractError):
            adapter.read_raw(
                "stock_daily_k",
                database_uri="dfs://A_STOCK_DAILY_K_DB",
                limit=0,
            )


if __name__ == "__main__":
    unittest.main()
