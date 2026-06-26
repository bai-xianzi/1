from __future__ import annotations

import copy
import tempfile
import unittest
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from a_stock_quant.data_contracts import DataContractError
from a_stock_quant.dolphindb_daily_funds_service import (
    DailyFundsReadRequest,
    DolphinDBDailyFundsCanonicalService,
    provisional_node_id,
    validate_daily_funds_service_contract,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class FakeAdapter:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self.rows = rows
        self.scripts: list[str] = []

    def run_readonly_query(self, script: str) -> Any:
        self.scripts.append(script)
        return copy.deepcopy(self.rows)


def common_row(
    dataset_id: str,
    snapshot_date: date = date(2025, 11, 20),
    *,
    source_hash: str = "a" * 64,
    row_number: int = 1,
    ingested_at: datetime | None = None,
) -> dict[str, Any]:
    return {
        "dataset_id": dataset_id,
        "snapshot_date": snapshot_date,
        "snapshot_phase": "CLOSE",
        "schema_version": f"{dataset_id}_raw_v1",
        "entity_key": "entity",
        "source_row_number": row_number,
        "source_file_name": f"{dataset_id}.xls",
        "source_file_relative_path": f"20251120/{dataset_id}.xls",
        "source_file_size_bytes": 100,
        "source_file_mtime_utc": datetime(2025, 11, 20, 10, 0),
        "source_file_sha256": source_hash,
        "row_sha256": "b" * 64,
        "ingest_batch_id": "batch1",
        "ingested_at_utc": ingested_at or datetime(2025, 11, 20, 11, 0),
        "quality_status": "PASSED",
        "raw_row_json": "{}",
    }


class Task017CDailyFundsServiceTests(unittest.TestCase):
    def service(self, rows: list[dict[str, Any]]) -> DolphinDBDailyFundsCanonicalService:
        return DolphinDBDailyFundsCanonicalService(
            FakeAdapter(rows),
            project_root=PROJECT_ROOT,
        )

    def test_local_service_contract_passes(self) -> None:
        result = validate_daily_funds_service_contract(PROJECT_ROOT)
        self.assertEqual(result["overall_status"], "PASSED_WITH_WARNINGS")
        self.assertEqual(result["dataset_count"], 7)
        self.assertEqual(result["raw_table_count"], 3)
        self.assertEqual(result["canonical_object_count"], 4)
        self.assertEqual(result["issues"], [])

    def test_hq_maps_volume_and_lineage(self) -> None:
        row = common_row("hq")
        row.update(
            {
                "instrument_id": "000001",
                "prev_close": 10.0,
                "open_price": 10.1,
                "high_price": 10.5,
                "low_price": 9.9,
                "last_price": 10.2,
                "avg_price": 10.15,
                "total_volume_lot": 123.0,
                "amount_cny": 124_845.0,
                "price_change": 0.2,
                "pct_change": 2.0,
                "amplitude_pct": 6.0,
                "turnover_pct": 1.2,
                "float_market_cap_cny": 1_000_000.0,
                "total_market_cap_cny": 2_000_000.0,
                "instrument_name": "平安银行",
            }
        )
        service = self.service([row])
        batch = service.read(
            DailyFundsReadRequest(
                dataset_id="hq",
                entity_ids=("000001",),
                start_date=date(2025, 11, 20),
                end_date=date(2025, 11, 20),
            )
        )
        self.assertEqual(batch.canonical_object, "DailyBar")
        self.assertEqual(len(batch.records), 1)
        record = batch.records[0]
        self.assertEqual(record.values["volume_lots"], 123.0)
        self.assertEqual(record.values["volume_shares"], 12_300)
        self.assertEqual(record.primary_key["instrument_id"], "000001")
        self.assertIn("instrument_name", record.source_extensions)
        self.assertTrue(
            any(
                item["canonical_field"] == "volume_shares"
                and item["transform_id"] == "multiply_100"
                for item in record.lineage
            )
        )
        script = service.adapter.scripts[0]
        self.assertTrue(script.startswith("select"))
        self.assertIn("dataset_id=`hq", script)
        self.assertNotIn("insert", script.lower())

    def test_kphq_keeps_time_null_and_date_only_precision(self) -> None:
        row = common_row("kphq")
        row.update(
            {
                "snapshot_phase": "OPENING_AUCTION",
                "instrument_id": "000001",
                "last_price": 10.1,
                "open_price": 10.2,
                "total_volume_lot": 50.0,
                "amount_cny": 51_000.0,
                "order_imbalance_pct": -25.0,
                "volume_ratio": 1.1,
                "turnover_pct": 0.2,
                "pct_change": 2.0,
            }
        )
        service = self.service([row])
        batch = service.read(
            DailyFundsReadRequest(
                dataset_id="kphq",
                entity_ids=("000001",),
                start_date=date(2025, 11, 20),
                end_date=date(2025, 11, 20),
            )
        )
        values = batch.records[0].values
        self.assertIsNone(values["snapshot_time"])
        self.assertEqual(values["snapshot_time_precision"], "DATE_ONLY")
        self.assertEqual(values["order_imbalance_ratio"], -0.25)
        self.assertNotEqual(values.get("snapshot_time"), row["source_file_mtime_utc"])

    def test_classification_uses_node_identity_not_instrument(self) -> None:
        row = common_row("hy")
        row.update(
            {
                "classification_type": "INDUSTRY",
                "node_name_raw": "银行",
                "pct_change": 1.2,
                "return_3d_pct": 2.0,
                "speed_pct": 0.1,
                "leading_stock_name": "平安银行",
                "up_count": 10,
                "down_count": 2,
                "breadth_ratio": 5.0,
                "breadth_status": "NORMAL",
                "limit_up_count": 1,
                "turnover_pct": 0.5,
                "volume_ratio": 1.0,
                "turnover_3d_pct": 1.5,
                "return_5d_pct": 3.0,
                "return_10d_pct": 4.0,
                "return_20d_pct": 5.0,
                "volume_lot": 1000.0,
                "amount_cny": 1_000_000.0,
                "total_market_cap_cny": 10_000_000.0,
                "float_market_cap_cny": 8_000_000.0,
                "average_return_pct": 1.1,
                "average_shares": 123.0,
                "pe_ratio": 6.0,
            }
        )
        service = self.service([row])
        batch = service.read(
            DailyFundsReadRequest(
                dataset_id="hy",
                entity_ids=("银行",),
                start_date=date(2025, 11, 20),
                end_date=date(2025, 11, 20),
            )
        )
        record = batch.records[0]
        expected_id = provisional_node_id("INDUSTRY", "银行")
        self.assertEqual(record.canonical_object, "ClassificationMarketSnapshot")
        self.assertEqual(record.values["node_id"], expected_id)
        self.assertNotIn("instrument_id", record.primary_key)
        self.assertEqual(record.source_extensions["average_shares"], 123.0)
        self.assertNotIn("银行", service.adapter.scripts[0])

    def test_classification_can_query_by_provisional_id(self) -> None:
        row = common_row("gn")
        row.update(
            {
                "classification_type": "CONCEPT",
                "node_name_raw": "人工智能",
                "breadth_status": "UNKNOWN",
            }
        )
        selector = provisional_node_id("CONCEPT", "人工智能")
        assert selector is not None
        service = self.service([row])
        batch = service.read(
            DailyFundsReadRequest(
                dataset_id="gn",
                entity_ids=(selector,),
                start_date=date(2025, 11, 20),
                end_date=date(2025, 11, 20),
            )
        )
        self.assertEqual(len(batch.records), 1)
        self.assertEqual(batch.records[0].values["node_name_cn"], "人工智能")

    def test_money_flow_preserves_sign_and_sums_buckets(self) -> None:
        row = common_row("zj")
        row.update(
            {
                "instrument_id": "000001",
                "main_net_inflow_cny": -10.0,
                "super_large_net_cny": -100.0,
                "large_net_cny": 20.0,
                "medium_net_cny": -5.0,
                "small_net_cny": 1.0,
                "super_large_outflow_cny": -300.0,
                "large_outflow_cny": -50.0,
                "instrument_name": "平安银行",
            }
        )
        service = self.service([row])
        batch = service.read(
            DailyFundsReadRequest(
                dataset_id="zj",
                entity_ids=("000001",),
                start_date=date(2025, 11, 20),
                end_date=date(2025, 11, 20),
            )
        )
        values = batch.records[0].values
        self.assertEqual(values["net_inflow_total_cny"], -84.0)
        self.assertEqual(values["net_inflow_super_large_cny"], -100.0)
        self.assertEqual(
            batch.records[0].source_extensions["super_large_outflow_cny"],
            -300.0,
        )

    def test_latest_raw_revision_wins(self) -> None:
        older = common_row(
            "hq",
            source_hash="a" * 64,
            ingested_at=datetime(2025, 11, 20, 11, 0),
        )
        newer = common_row(
            "hq",
            source_hash="c" * 64,
            ingested_at=datetime(2025, 11, 20, 12, 0),
        )
        for row, close in ((older, 10.0), (newer, 11.0)):
            row.update(
                {
                    "instrument_id": "000001",
                    "last_price": close,
                }
            )
        service = self.service([older, newer])
        batch = service.read(
            DailyFundsReadRequest(
                dataset_id="hq",
                entity_ids=("000001",),
                start_date=date(2025, 11, 20),
                end_date=date(2025, 11, 20),
            )
        )
        self.assertEqual(len(batch.records), 1)
        self.assertEqual(batch.records[0].values["close_raw_cny"], 11.0)
        self.assertIn("COLLAPSED_RAW_REVISIONS:1", batch.warnings)

    def test_known_quarantine_is_reported(self) -> None:
        service = self.service([])
        batch = service.read(
            DailyFundsReadRequest(
                dataset_id="kphq",
                entity_ids=("000001",),
                start_date=date(2025, 12, 23),
                end_date=date(2025, 12, 23),
            )
        )
        self.assertTrue(
            any(
                item.startswith("KNOWN_QUARANTINED_SOURCE_DATE:kphq")
                for item in batch.warnings
            )
        )
        self.assertIn("NO_DATA_FOR_ENTITY:000001", batch.warnings)

    def test_request_rejects_out_of_coverage(self) -> None:
        service = self.service([])
        with self.assertRaises(DataContractError):
            service.read(
                DailyFundsReadRequest(
                    dataset_id="hq",
                    entity_ids=("000001",),
                    start_date=date(2025, 11, 19),
                    end_date=date(2025, 11, 20),
                )
            )

    def test_security_query_rejects_non_six_digit_id(self) -> None:
        service = self.service([])
        with self.assertRaises(DataContractError):
            service.read(
                DailyFundsReadRequest(
                    dataset_id="hq",
                    entity_ids=("银行'; dropDatabase",),
                    start_date=date(2025, 11, 20),
                    end_date=date(2025, 11, 20),
                )
            )

    def test_no_data_warning_is_explicit(self) -> None:
        service = self.service([])
        batch = service.read(
            DailyFundsReadRequest(
                dataset_id="zj",
                entity_ids=("000001",),
                start_date=date(2025, 11, 20),
                end_date=date(2025, 11, 20),
            )
        )
        self.assertEqual(batch.records, ())
        self.assertIn("NO_DATA_FOR_ENTITY:000001", batch.warnings)

    def test_mapping_source_drift_fails_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            temp_root = Path(tmp)
            for rel in (
                "configs/datasets/a_stock_daily_funds_standard_service.yaml",
                "configs/mappings/a_stock_daily_funds_canonical_v0.yaml",
                "schemas/canonical_fields.yaml",
                "schemas/enum_definitions.yaml",
            ):
                source = PROJECT_ROOT / rel
                target = temp_root / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
            mapping_path = (
                temp_root
                / "configs/mappings/a_stock_daily_funds_canonical_v0.yaml"
            )
            payload = yaml.safe_load(mapping_path.read_text(encoding="utf-8"))
            payload["datasets"]["hq"]["mappings"][0]["source"] = "not_a_raw_field"
            mapping_path.write_text(
                yaml.safe_dump(payload, allow_unicode=True, sort_keys=False),
                encoding="utf-8",
            )
            result = validate_daily_funds_service_contract(temp_root)
        self.assertEqual(result["overall_status"], "FAILED")
        self.assertIn(
            "MAPPING_SOURCE_FIELD_NOT_IN_RAW_SCHEMA",
            {item["code"] for item in result["issues"]},
        )


if __name__ == "__main__":
    unittest.main()
