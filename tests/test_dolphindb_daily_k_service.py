"""测试A股日K标准映射插件与读取服务。"""

from __future__ import annotations

import json
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

from a_stock_quant.data_contracts import DataContractError
from a_stock_quant.dataset_registry import (
    DatasetRegistration,
)
from a_stock_quant.dolphindb_daily_k_service import (
    DailyKReadRequest,
    DolphinDBDailyKStandardizedService,
)


CONFIG_PATH = (
    PROJECT_ROOT
    / "configs"
    / "datasets"
    / "a_stock_daily_k.json"
)


class FakeDailyKAdapter:
    def __init__(self) -> None:
        self.scripts: list[str] = []

    def _validate_database_uri(self, value: str) -> None:
        if not value.startswith("dfs://"):
            raise DataContractError("bad uri")

    def _validate_table_name(self, value: str) -> None:
        if not value.replace("_", "").isalnum():
            raise DataContractError("bad table")

    def run_readonly_query(self, script: str) -> Any:
        self.scripts.append(script)
        normalized = " ".join(script.split())

        if "select top 1 close" in normalized:
            if '"000001"' in normalized:
                return [{"close": 10.0}]
            return []

        if "select top" in normalized and "stock_code" in normalized:
            if '"000001"' in normalized:
                return [
                    self._row(
                        stock_code="000001",
                        trade_date="2026-05-28",
                        close=11.0,
                        price_change=1.0,
                        pct_change=-10.0,
                    ),
                    self._row(
                        stock_code="000001",
                        trade_date="2026-05-29",
                        close=12.1,
                        price_change=1.1,
                        pct_change=-10.0,
                    ),
                ]

            if '"000002"' in normalized:
                return [
                    self._row(
                        stock_code="000002",
                        trade_date="2026-05-29",
                        close=20.0,
                        price_change=0.0,
                        pct_change=0.0,
                    )
                ]

        raise AssertionError(f"未识别的查询：{normalized}")

    @staticmethod
    def _row(
        *,
        stock_code: str,
        trade_date: str,
        close: float,
        price_change: float,
        pct_change: float,
    ) -> dict[str, Any]:
        row = {
            "stock_code": stock_code,
            "trade_date": trade_date,
            "open": close - 0.2,
            "high": close + 0.3,
            "low": close - 0.4,
            "close": close,
            "amount": close * 1_000,
            "volume": 1_000,
            "BS": "B",
            "chanlun": "X",
            "turnover_rate": 0.1,
            "pct_change": pct_change,
            "price_change": price_change,
            "pct_3d": None,
            "pct_5d": None,
            "pct_10d": None,
            "pct_20d": None,
            "pct_30d": None,
            "ma5": close,
            "ma10": close,
            "ma20": close,
            "ma30": close,
            "ma60": close,
            "ma120": close,
            "ma250": close,
            "macd": 0.1,
            "dif": 0.1,
            "dea": 0.1,
            "k": 50.0,
            "d": 50.0,
            "j": 50.0,
            "rsi6": 50.0,
            "rsi12": 50.0,
            "rsi24": 50.0,
            "bias": 0.0,
            "boll": close,
            "boll_up": close + 1,
            "boll_down": close - 1,
            "float_shares": 100.0,
            "total_shares": 200.0,
            "adj_factor": 2.0,
            "deduct_value": 1.0,
            "adj_price": close * 2.0 + 1.0,
            "dividend": None,
            "bonus_share": None,
            "convert_share": None,
            "allot_share": None,
            "allot_price": None,
        }
        return row


def load_registration() -> DatasetRegistration:
    return DatasetRegistration.from_dict(
        json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    )


class TestDailyKReadRequest(unittest.TestCase):
    def test_rejects_duplicate_instruments(self) -> None:
        with self.assertRaises(DataContractError):
            DailyKReadRequest(
                instrument_ids=("000001", "000001"),
                start_date=date(2026, 5, 1),
                end_date=date(2026, 5, 29),
            )

    def test_rejects_invalid_date_range(self) -> None:
        with self.assertRaises(DataContractError):
            DailyKReadRequest(
                instrument_ids=("000001",),
                start_date=date(2026, 5, 30),
                end_date=date(2026, 5, 29),
            )


class TestDailyKStandardizedService(unittest.TestCase):
    def setUp(self) -> None:
        self.adapter = FakeDailyKAdapter()
        self.service = DolphinDBDailyKStandardizedService(
            self.adapter,
            load_registration(),
        )

    def test_reads_and_maps_daily_bar(self) -> None:
        batch = self.service.read(
            DailyKReadRequest(
                instrument_ids=("000001",),
                start_date=date(2026, 5, 28),
                end_date=date(2026, 5, 29),
            )
        )

        self.assertEqual(batch.source_row_count, 2)
        self.assertEqual(
            batch.standardized_record_count,
            2,
        )
        first = batch.records[0]
        daily = first.canonical_objects["DailyBar"]

        self.assertEqual(daily["instrument_id"], "000001")
        self.assertEqual(
            daily["trade_date"],
            date(2026, 5, 28),
        )
        self.assertEqual(daily["pre_close_raw_cny"], 10.0)
        self.assertEqual(daily["pct_change_pct"], 10.0)
        self.assertEqual(daily["volume_lots"], 10.0)
        self.assertEqual(daily["vwap_raw_cny"], 11.0)

    def test_maps_ownership_and_market_cap(self) -> None:
        batch = self.service.read(
            DailyKReadRequest(
                instrument_ids=("000001",),
                start_date=date(2026, 5, 28),
                end_date=date(2026, 5, 28),
            )
        )
        first = batch.records[0]
        ownership = first.canonical_objects[
            "OwnershipSnapshot"
        ]
        daily = first.canonical_objects["DailyBar"]

        self.assertEqual(
            ownership["float_shares"],
            1_000_000.0,
        )
        self.assertEqual(
            ownership["total_shares"],
            2_000_000.0,
        )
        self.assertEqual(
            daily["float_market_cap_cny"],
            11_000_000.0,
        )
        self.assertEqual(
            daily["total_market_cap_cny"],
            22_000_000.0,
        )

    def test_keeps_pending_fields_in_source_extensions(self) -> None:
        batch = self.service.read(
            DailyKReadRequest(
                instrument_ids=("000001",),
                start_date=date(2026, 5, 28),
                end_date=date(2026, 5, 28),
            )
        )
        extensions = batch.records[0].source_extensions

        self.assertEqual(extensions["pct_change"], -10.0)
        self.assertEqual(extensions["adj_price"], 23.0)
        self.assertEqual(extensions["BS"], "B")
        self.assertEqual(extensions["ma5"], 11.0)

    def test_marks_known_source_pct_semantics(self) -> None:
        batch = self.service.read(
            DailyKReadRequest(
                instrument_ids=("000001",),
                start_date=date(2026, 5, 28),
                end_date=date(2026, 5, 28),
            )
        )
        flags = batch.records[0].quality_flags

        self.assertIn(
            "SOURCE_PCT_CHANGE_SIGN_INVERTED",
            flags,
        )
        self.assertNotIn(
            "SOURCE_PRICE_CHANGE_MISMATCH",
            flags,
        )
        self.assertNotIn(
            "SOURCE_ADJ_FORMULA_MISMATCH",
            flags,
        )

    def test_context_rolls_forward_between_rows(self) -> None:
        batch = self.service.read(
            DailyKReadRequest(
                instrument_ids=("000001",),
                start_date=date(2026, 5, 28),
                end_date=date(2026, 5, 29),
            )
        )
        second = batch.records[1]
        daily = second.canonical_objects["DailyBar"]

        self.assertEqual(daily["pre_close_raw_cny"], 11.0)
        self.assertEqual(daily["pct_change_pct"], 10.0)

    def test_multiple_instruments_are_supported(self) -> None:
        batch = self.service.read(
            DailyKReadRequest(
                instrument_ids=("000001", "000002"),
                start_date=date(2026, 5, 29),
                end_date=date(2026, 5, 29),
            )
        )

        self.assertEqual(
            batch.standardized_record_count,
            3,
        )
        ids = [
            item.primary_key["instrument_id"]
            for item in batch.records
        ]
        self.assertEqual(
            ids,
            ["000001", "000001", "000002"],
        )

    def test_first_record_without_history_gets_flag(self) -> None:
        batch = self.service.read(
            DailyKReadRequest(
                instrument_ids=("000002",),
                start_date=date(2026, 5, 29),
                end_date=date(2026, 5, 29),
            )
        )

        self.assertIn(
            "MISSING_PRE_CLOSE",
            batch.records[0].quality_flags,
        )
        self.assertIsNone(
            batch.records[0]
            .canonical_objects["DailyBar"][
                "pct_change_pct"
            ]
        )

    def test_request_cannot_exceed_coverage_end(self) -> None:
        with self.assertRaises(DataContractError):
            self.service.read(
                DailyKReadRequest(
                    instrument_ids=("000001",),
                    start_date=date(2026, 5, 29),
                    end_date=date(2026, 5, 30),
                )
            )

    def test_lineage_contains_mapping_versions(self) -> None:
        batch = self.service.read(
            DailyKReadRequest(
                instrument_ids=("000001",),
                start_date=date(2026, 5, 28),
                end_date=date(2026, 5, 28),
            )
        )
        lineage = batch.records[0].lineage

        self.assertTrue(lineage)
        self.assertTrue(
            all(
                item["mapping_version"] == "0.2.0"
                for item in lineage
            )
        )
        self.assertTrue(
            all(
                item["dictionary_revision"] == "0.5"
                for item in lineage
            )
        )


if __name__ == "__main__":
    unittest.main()
