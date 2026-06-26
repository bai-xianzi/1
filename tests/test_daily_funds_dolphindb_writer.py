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


class FakeSession:
    def __init__(
        self,
        database_exists: bool = False,
        tables: set[str] | None = None,
    ) -> None:
        self.database_exists = database_exists
        self.tables = tables or set()
        self.connected = False
        self.scripts: list[str] = []

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
        self.scripts.append(script)
        if script == "1 + 1":
            return 2
        if script == "version()":
            return "3.00.test"
        if script.startswith("existsDatabase"):
            return self.database_exists
        if script.startswith("existsTable"):
            for table_name in self.tables:
                if f"`{table_name}" in script:
                    return True
            return False
        raise AssertionError(f"Unexpected script: {script}")


class Task016BWriterTests(unittest.TestCase):
    def test_contract_matches_six_physical_tables(self) -> None:
        result = validate_local_contract(CONTRACT_PATH)
        self.assertEqual(result["overall_status"], "PASSED")
        self.assertEqual(result["dataset_count"], 7)
        self.assertEqual(result["physical_table_count"], 6)

    def test_ddl_is_non_destructive_and_uses_tsdb(self) -> None:
        script = build_create_database_script()
        self.assertIn('"TSDB"', script)
        self.assertIn("LAST", script)
        self.assertNotIn("dropDatabase", script)
        self.assertNotIn("dropTable", script)
        self.assertNotIn(" as exists", script)
        self.assertIn("table_exists", script)
        for table_name in TABLE_SCHEMAS:
            self.assertIn(table_name, script)

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
        with self.assertRaises(
            DailyFundsDolphinDBError
        ):
            decide_file_write_action(-1, 100)

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

    def test_strict_file_normalization(self) -> None:
        contract = load_daily_funds_contract(
            CONTRACT_PATH
        )
        dataset = contract.datasets["hq"]
        schema = dataset.schemas[0]

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
