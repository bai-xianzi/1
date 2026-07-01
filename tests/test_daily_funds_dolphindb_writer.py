# 测试模块总览：验证 `test_daily_funds_dolphindb_writer` 对应功能的合同、边界和历史回归行为。
# - 输入：构造样例、测试夹具、临时文件以及被测模块公开接口。
# - 处理：只执行测试和断言，不修改生产算法、金融语义或正式数据库。
# - 输出：可重复的通过/失败证据，供全量回归和任务验收使用。
# - 为什么这样写：把业务要求固化为自动测试，使后续注释迁移和重构能够证明行为未变化。
from __future__ import annotations

import csv
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from a_stock_quant.daily_funds_dolphindb_writer import (
    DATABASE_URI,
    SECURITY_COLUMNS,
    TABLE_NAMES,
    TABLE_SCHEMAS,
    DailyFundsDolphinDBError,
    DolphinDBWriteSettings,
    build_create_database_script,
    decide_file_write_action,
    load_normalized_file_rows,
    prepare_dataframe,
    probe_dolphindb_environment,
    validate_local_contract,
)
from a_stock_quant.daily_funds_ingest import (
    load_daily_funds_contract,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = (
    PROJECT_ROOT
    / "configs"
    / "datasets"
    / "a_stock_daily_funds_raw.yaml"
)


# 测试类 `FakeSession`：集中验证 `test_daily_funds_dolphindb_writer` 相关合同、边界条件和回归行为。
# - 输入：测试夹具、构造样例以及被测模块公开接口。
# - 处理：按独立场景组织断言，覆盖正常路径、失败门禁和关键边界。
# - 输出：通过或失败的单元测试结果，不产生正式业务数据。
# - 为什么这样写：把同一职责的回归场景集中管理，便于定位失败并防止后续修改破坏既有合同。
class FakeSession:
    # 测试函数 `__init__`：封装 `__init__` 测试辅助步骤，减少重复样例和断言准备。
    # - 输入：database_exists、tables。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def __init__(
        self,
        database_exists: bool = False,
        tables: set[str] | None = None,
    ) -> None:
        self.database_exists = database_exists
        self.tables = tables or set()
        self.connected = False
        self.scripts: list[str] = []

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
        self.scripts.append(script)
        # 测试分支：根据 `script == '1 + 1'` 选择对应断言或样例路径。
        # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
        # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
        if script == "1 + 1":
            return 2
        # 测试分支：根据 `script == 'version()'` 选择对应断言或样例路径。
        # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
        # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
        if script == "version()":
            return "3.00.test"
        # 测试分支：根据 `script.startswith('existsDatabase')` 选择对应断言或样例路径。
        # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
        # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
        if script.startswith("existsDatabase"):
            return self.database_exists
        # 测试分支：根据 `script.startswith('existsTable')` 选择对应断言或样例路径。
        # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
        # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
        if script.startswith("existsTable"):
            # 参数化循环：逐项使用 `self.tables` 验证同一合同。
            # - 处理：每轮保留原样例、顺序和断言，便于定位具体失败项。
            # - 为什么这样写：用一致规则覆盖多组输入，减少复制测试并提高边界覆盖率。
            for table_name in self.tables:
                # 测试分支：根据 `f'`{table_name}' in script` 选择对应断言或样例路径。
                # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
                # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
                if f"`{table_name}" in script:
                    return True
            return False
        raise AssertionError(f"Unexpected script: {script}")


# 测试类 `Task016BWriterTests`：集中验证 `test_daily_funds_dolphindb_writer` 相关合同、边界条件和回归行为。
# - 输入：测试夹具、构造样例以及被测模块公开接口。
# - 处理：按独立场景组织断言，覆盖正常路径、失败门禁和关键边界。
# - 输出：通过或失败的单元测试结果，不产生正式业务数据。
# - 为什么这样写：把同一职责的回归场景集中管理，便于定位失败并防止后续修改破坏既有合同。
class Task016BWriterTests(unittest.TestCase):
    # 测试函数 `test_contract_matches_six_physical_tables`：验证 `contract、matches、six、physical、tables` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_contract_matches_six_physical_tables(self) -> None:
        result = validate_local_contract(CONTRACT_PATH)
        self.assertEqual(result["overall_status"], "PASSED")
        self.assertEqual(result["dataset_count"], 7)
        self.assertEqual(result["physical_table_count"], 6)

    # 测试函数 `test_ddl_is_non_destructive_and_uses_tsdb`：验证 `ddl、is、non、destructive、and、uses、tsdb` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_ddl_is_non_destructive_and_uses_tsdb(self) -> None:
        script = build_create_database_script()
        self.assertIn('"TSDB"', script)
        self.assertIn("LAST", script)
        self.assertNotIn("dropDatabase", script)
        self.assertNotIn("dropTable", script)
        self.assertNotIn(" as exists", script)
        self.assertIn("table_exists", script)
        # 参数化循环：逐项使用 `TABLE_SCHEMAS` 验证同一合同。
        # - 处理：每轮保留原样例、顺序和断言，便于定位具体失败项。
        # - 为什么这样写：用一致规则覆盖多组输入，减少复制测试并提高边界覆盖率。
        for table_name in TABLE_SCHEMAS:
            self.assertIn(table_name, script)

    # 测试函数 `test_probe_is_read_only`：验证 `probe、is、read、only` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_probe_is_read_only(self) -> None:
        fake = FakeSession(database_exists=False)
        settings = DolphinDBWriteSettings(
            password="secret"
        )
        result = probe_dolphindb_environment(
            settings,
            session_factory=lambda: fake,
            runtime_info_provider=lambda: {
                "python_client_version": "test",
                "table_appender_available": True,
            },
        )
        self.assertEqual(
            result["readiness"],
            "READY_TO_CREATE",
        )
        self.assertEqual(
            result["overall_status"],
            "PASSED",
        )
        joined = "\n".join(fake.scripts)
        self.assertNotIn("createPartitionedTable", joined)
        self.assertNotIn("database(", joined)
        self.assertNotIn("drop", joined.lower())

    # 测试函数 `test_idempotent_action_decision`：验证 `idempotent、action、decision` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_idempotent_action_decision(self) -> None:
        self.assertEqual(
            decide_file_write_action(0, 100),
            "WRITE_NEW",
        )
        self.assertEqual(
            decide_file_write_action(100, 100),
            "SKIP_IDEMPOTENT",
        )
        self.assertEqual(
            decide_file_write_action(20, 100),
            "RECOVER_PARTIAL",
        )
        # 测试上下文：通过 `self.assertRaises(DailyFundsDolphinDBError)` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
        with self.assertRaises(
            DailyFundsDolphinDBError
        ):
            decide_file_write_action(-1, 100)

    # 测试函数 `test_dataframe_column_order_and_types`：验证 `dataframe、column、order、and、types` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_dataframe_column_order_and_types(self) -> None:
        row = {
            name: None
            for name, _ in SECURITY_COLUMNS
        }
        row.update(
            {
                "dataset_id": "hq",
                "snapshot_date": "2025-11-20",
                "snapshot_month": "2025-11",
                "snapshot_phase": "CLOSE",
                "schema_version": "hq_raw_v1",
                "entity_key": "000001",
                "source_row_number": 1,
                "source_file_name": "hq.xls",
                "source_file_relative_path": "20251120/hq.xls",
                "source_file_size_bytes": 100,
                "source_file_mtime_utc": (
                    "2025-11-20T10:00:00+00:00"
                ),
                "source_file_sha256": "a" * 64,
                "row_sha256": "b" * 64,
                "ingest_batch_id": "batch1",
                "ingested_at_utc": (
                    "2025-11-20T11:00:00+00:00"
                ),
                "quality_status": "PASSED",
                "raw_row_json": "{}",
                "instrument_id": "000001",
                "market_candidate": "SZ",
                "instrument_name": "测试",
                "last_price": 10.0,
                "consecutive_up_days": 2,
                "source_volume_unit": "LOT_CANDIDATE",
                "canonical_volume_transform": (
                    "multiply_by_100"
                ),
                "source_amount_unit": "CNY",
            }
        )
        frame = prepare_dataframe(
            [row],
            SECURITY_COLUMNS,
        )
        self.assertEqual(
            list(frame.columns),
            [name for name, _ in SECURITY_COLUMNS],
        )
        self.assertEqual(
            str(frame["source_row_number"].dtype),
            "Int32",
        )
        self.assertEqual(
            str(frame["source_file_size_bytes"].dtype),
            "Int64",
        )
        self.assertEqual(
            str(frame["last_price"].dtype),
            "float64",
        )

    # 测试函数 `test_strict_file_normalization`：验证 `strict、file、normalization` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_strict_file_normalization(self) -> None:
        contract = load_daily_funds_contract(
            CONTRACT_PATH
        )
        dataset = contract.datasets["hq"]
        schema = dataset.schemas[0]

        # 测试上下文：通过 `tempfile.TemporaryDirectory()` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
        with tempfile.TemporaryDirectory() as tmp:
            date_dir = Path(tmp) / "20251120"
            date_dir.mkdir()
            file_path = date_dir / "hq.xls"

            values = ["—"] * len(schema.headers)
            index = {
                name: position
                for position, name in enumerate(
                    schema.headers
                )
            }
            values[index["序"]] = "1"
            values[index["代码"]] = '="000001"'
            values[index["名称"]] = "测试股票"
            values[index["最新"]] = "10.25"
            values[index["金额"]] = "1.5亿"
            values[index["总量"]] = "100万"

            # 测试上下文：通过 `file_path.open('w', encoding='gb18030', newline='')` 管理异常断言、临时资源或子测试范围。
            # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
            # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
            with file_path.open(
                "w",
                encoding="gb18030",
                newline="",
            ) as handle:
                writer = csv.writer(
                    handle,
                    delimiter="\t",
                    lineterminator="\n",
                )
                writer.writerow(schema.headers)
                writer.writerow(values)

            rows = load_normalized_file_rows(
                file_path=file_path,
                dataset=dataset,
                contract=contract,
                ingest_batch_id="batch1",
                ingested_at=datetime.now(
                    timezone.utc
                ),
            )
            self.assertEqual(len(rows), 1)
            self.assertEqual(
                rows[0]["instrument_id"],
                "000001",
            )
            self.assertEqual(
                rows[0]["amount_cny"],
                150_000_000.0,
            )
            self.assertEqual(
                rows[0]["total_volume_lot"],
                1_000_000.0,
            )


if __name__ == "__main__":
    unittest.main()
