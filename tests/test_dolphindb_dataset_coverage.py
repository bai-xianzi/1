"""测试DolphinDB数据集覆盖边界核验。"""

from __future__ import annotations

import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from a_stock_quant.data_contracts import (
    DataContractError,
    QualityStatus,
)
from a_stock_quant.dolphindb_dataset_coverage import (
    DolphinDBDatasetCoverageVerifier,
    _extract_date_from_filename,
)


class FakeCoverageAdapter:
    def __init__(
        self,
        max_date: str = "2026-05-29",
    ) -> None:
        self.max_date = max_date
        self.scripts: list[str] = []

    def _validate_database_uri(self, value: str) -> None:
        if not value.startswith("dfs://"):
            raise DataContractError("bad uri")

    def _validate_table_name(self, value: str) -> None:
        if not value.replace("_", "").isalnum():
            raise DataContractError("bad name")

    def run_readonly_query(self, script: str) -> Any:
        self.scripts.append(script)
        normalized = " ".join(script.split())

        if "min(trade_date)" in normalized:
            return [{
                "row_count": 16_548_275,
                "min_data_date": "1990-12-19",
                "max_data_date": self.max_date,
            }]

        if "select distinct stock_code" in normalized:
            return [{"entity_count": 5_523}]

        raise AssertionError(f"未识别的查询：{normalized}")


class TestDatasetCoverageVerifier(unittest.TestCase):
    def _verifier(
        self,
        *,
        max_date: str = "2026-05-29",
        cutoff: date = date(2026, 5, 29),
        source_dirs=(),
        import_logs=(),
    ) -> DolphinDBDatasetCoverageVerifier:
        return DolphinDBDatasetCoverageVerifier(
            adapter=FakeCoverageAdapter(max_date),
            dataset_id="a_stock_daily_k",
            database_uri="dfs://A_STOCK_DAILY_K_DB",
            table_name="stock_daily_k",
            date_field="trade_date",
            entity_field="stock_code",
            declared_cutoff_date=cutoff,
            source_dirs=source_dirs,
            import_logs=import_logs,
        )

    def test_matching_snapshot_cutoff_passes(self) -> None:
        report = self._verifier().collect()

        self.assertEqual(
            report.overall_status,
            QualityStatus.PASSED,
        )
        self.assertFalse(report.blocks_downstream)
        self.assertEqual(
            report.coverage_evaluation["coverage_version"],
            "a_stock_daily_k@2026-05-29",
        )

    def test_calendar_lag_is_informational_only(self) -> None:
        report = self._verifier().collect()

        self.assertFalse(
            report.coverage_evaluation[
                "calendar_lag_is_blocking"
            ]
        )
        self.assertFalse(report.blocks_downstream)

    def test_database_before_declared_cutoff_fails(self) -> None:
        report = self._verifier(
            max_date="2026-05-28",
        ).collect()

        self.assertEqual(
            report.overall_status,
            QualityStatus.FAILED,
        )
        self.assertTrue(report.blocks_downstream)

    def test_database_after_declared_cutoff_warns(self) -> None:
        report = self._verifier(
            max_date="2026-05-30",
        ).collect()

        self.assertEqual(
            report.overall_status,
            QualityStatus.WARNING,
        )
        self.assertFalse(report.blocks_downstream)

    def test_source_inventory_detects_pending_date(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "daily_2026-05-29.csv").write_text(
                "x",
                encoding="utf-8",
            )
            (root / "daily_20260530.xlsx").write_text(
                "x",
                encoding="utf-8",
            )

            report = self._verifier(
                source_dirs=[directory],
            ).collect()

        self.assertTrue(
            report.coverage_evaluation[
                "pending_import_detected"
            ]
        )
        self.assertEqual(
            report.overall_status,
            QualityStatus.WARNING,
        )

    def test_import_log_inventory_reads_last_line(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "import_success.csv"
            path.write_text(
                "file,status\nold.csv,ok\nnew.csv,ok\n",
                encoding="utf-8",
            )

            report = self._verifier(
                import_logs=[str(path)],
            ).collect()

        self.assertEqual(
            report.import_log_inventory[0][
                "last_nonempty_line"
            ],
            "new.csv,ok",
        )

    def test_filename_date_extractor(self) -> None:
        self.assertEqual(
            _extract_date_from_filename(
                "A股日K_2026年5月29日.xlsx"
            ),
            date(2026, 5, 29),
        )
        self.assertEqual(
            _extract_date_from_filename("daily_20260530.csv"),
            date(2026, 5, 30),
        )

    def test_entity_count_uses_separate_query(self) -> None:
        adapter = FakeCoverageAdapter()
        report = DolphinDBDatasetCoverageVerifier(
            adapter=adapter,
            dataset_id="a_stock_daily_k",
            database_uri="dfs://A_STOCK_DAILY_K_DB",
            table_name="stock_daily_k",
            date_field="trade_date",
            entity_field="stock_code",
            declared_cutoff_date=date(2026, 5, 29),
        ).collect()

        self.assertEqual(
            report.database_summary["entity_count"],
            5_523,
        )
        self.assertEqual(len(adapter.scripts), 2)
        self.assertNotIn(
            "count(distinct",
            " ".join(adapter.scripts).lower(),
        )
        self.assertIn(
            "select distinct stock_code",
            " ".join(adapter.scripts).lower(),
        )

    def test_invalid_identifier_is_rejected(self) -> None:
        with self.assertRaises(DataContractError):
            DolphinDBDatasetCoverageVerifier(
                adapter=FakeCoverageAdapter(),
                dataset_id="a_stock_daily_k",
                database_uri="dfs://A_STOCK_DAILY_K_DB",
                table_name="stock_daily_k",
                date_field="trade_date;drop",
                entity_field="stock_code",
                declared_cutoff_date=date(2026, 5, 29),
            )


if __name__ == "__main__":
    unittest.main()
