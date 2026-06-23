"""测试基本面Provider与用途级时点门禁。"""

from __future__ import annotations

import json
import sys
import unittest
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from a_stock_quant.data_contracts import DataContractError, QualityStatus
from a_stock_quant.dataset_registry import DatasetRegistration
from a_stock_quant.dolphindb_fundamental_service import (
    DolphinDBFundamentalStandardizedService,
)
from a_stock_quant.fundamental_standard_provider import (
    FundamentalStandardDataProvider,
)
from a_stock_quant.standard_data_service import (
    StandardDataQuery,
    StandardDataService,
    StandardDataUsage,
)


CONFIG_PATH = (
    PROJECT_ROOT
    / "configs"
    / "datasets"
    / "a_stock_fundamental_snapshot.json"
)


class FakeAdapter:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self.rows = rows

    def run_readonly_query(self, script: str) -> Any:
        return list(self.rows)


def load_registration() -> DatasetRegistration:
    return DatasetRegistration.from_dict(
        json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    )


def make_row(**overrides: Any) -> dict[str, Any]:
    values: dict[str, Any] = {
        "stock_code": "000001",
        "snapshot_date": date(2026, 6, 19),
        "update_date": date(2026, 4, 25),
        "report_period": 3,
        "total_shares": 1_940_591.87,
        "circulating_a_shares": 1_940_560.12,
        "shareholder_count": 457_610,
        "eps": 0.67,
        "adjusted_nav_per_share": 23.91,
        "total_assets": 6_033_961_984.0,
        "net_assets": 544_083_008.0,
        "operating_revenue": 35_277_000.0,
        "operating_cost": 17_888_000.0,
        "accounts_receivable": 0.0,
        "operating_profit": 17_389_000.0,
        "operating_cash_flow": 10_000_000.0,
        "inventory": 0.0,
        "total_profit": 17_399_000.0,
        "after_tax_profit": 14_523_000.0,
        "net_profit": 14_523_000.0,
        "market": "sz",
        "stock_name": "平安银行",
        "listing_date": date(1991, 4, 3),
        "imported_at": datetime(2026, 6, 19, 19, 36, 51),
        "source_file": "fundamental.xlsx",
    }
    values.update(overrides)
    return values


def make_provider(
    rows: list[dict[str, Any]] | None = None,
) -> FundamentalStandardDataProvider:
    service = DolphinDBFundamentalStandardizedService(
        FakeAdapter(rows or [make_row()]),
        load_registration(),
        allow_disabled_for_acceptance=True,
    )
    return FundamentalStandardDataProvider(service)


def make_query(**overrides: Any) -> StandardDataQuery:
    values = {
        "dataset_id": "a_stock_fundamental_snapshot",
        "canonical_object": "FundamentalSnapshot",
        "instrument_ids": ("000001",),
        "start_date": date(2026, 6, 19),
        "end_date": date(2026, 6, 19),
        "as_of_date": date(2026, 6, 20),
        "usage": StandardDataUsage.CURRENT_SNAPSHOT_RESEARCH,
    }
    values.update(overrides)
    return StandardDataQuery(**values)


class TestFundamentalProvider(unittest.TestCase):
    def test_registers_with_standard_data_service(self) -> None:
        service = StandardDataService()
        service.register_provider(make_provider())
        descriptor = service.list_datasets()[0]
        self.assertEqual(descriptor.dataset_id, "a_stock_fundamental_snapshot")
        self.assertEqual(descriptor.mapping_version, "0.2.0-rc2")
        self.assertEqual(descriptor.dictionary_revision, "0.5")
        self.assertIn("FundamentalSnapshot", descriptor.supported_objects)

    def test_current_snapshot_research_is_warning_not_blocked(self) -> None:
        result = make_provider().query(make_query())
        self.assertEqual(result.metadata.status, QualityStatus.WARNING)
        self.assertFalse(result.metadata.blocks_downstream)
        self.assertEqual(len(result.records), 1)

    def test_historical_backtest_is_blocked(self) -> None:
        result = make_provider().query(
            make_query(usage=StandardDataUsage.STRICT_HISTORICAL_BACKTEST)
        )
        self.assertEqual(result.metadata.status, QualityStatus.FAILED)
        self.assertTrue(result.metadata.blocks_downstream)
        with self.assertRaises(DataContractError):
            result.assert_usable()

    def test_historical_training_is_blocked(self) -> None:
        result = make_provider().query(
            make_query(usage=StandardDataUsage.HISTORICAL_MODEL_TRAINING)
        )
        self.assertTrue(result.metadata.blocks_downstream)

    def test_precoverage_query_is_blocked(self) -> None:
        result = make_provider().query(
            make_query(
                start_date=date(2026, 6, 18),
                end_date=date(2026, 6, 18),
                as_of_date=date(2026, 6, 18),
            )
        )
        self.assertEqual(result.records, ())
        self.assertTrue(result.metadata.blocks_downstream)
        self.assertEqual(result.metadata.status, QualityStatus.FAILED)

    def test_decision_time_requires_timezone(self) -> None:
        with self.assertRaises(DataContractError):
            make_query(decision_time=datetime(2026, 6, 20, 9, 0))

    def test_manual_decision_requires_decision_time(self) -> None:
        with self.assertRaises(DataContractError):
            make_query(usage=StandardDataUsage.MANUAL_DECISION_SUPPORT)

    def test_manual_decision_next_day_is_allowed_with_warning(self) -> None:
        result = make_provider().query(
            make_query(
                usage=StandardDataUsage.MANUAL_DECISION_SUPPORT,
                decision_time=datetime(
                    2026, 6, 20, 9, 0, tzinfo=timezone.utc
                ),
            )
        )
        self.assertFalse(result.metadata.blocks_downstream)
        self.assertEqual(result.metadata.status, QualityStatus.WARNING)

    def test_manual_decision_same_day_is_blocked_without_timezone_proof(self) -> None:
        result = make_provider().query(
            make_query(
                as_of_date=date(2026, 6, 19),
                usage=StandardDataUsage.MANUAL_DECISION_SUPPORT,
                decision_time=datetime(
                    2026, 6, 19, 23, 0, tzinfo=timezone.utc
                ),
            )
        )
        self.assertEqual(result.records, ())
        self.assertTrue(result.metadata.blocks_downstream)
        self.assertEqual(
            result.metadata.quality_flag_counts[
                "VISIBILITY_SAME_DAY_TIMEZONE_UNPROVEN"
            ],
            1,
        )

    def test_missing_imported_at_is_blocked(self) -> None:
        result = make_provider([make_row(imported_at=None)]).query(make_query())
        self.assertEqual(result.records, ())
        self.assertTrue(result.metadata.blocks_downstream)
        self.assertEqual(
            result.metadata.quality_flag_counts[
                "VISIBILITY_AVAILABLE_AT_MISSING"
            ],
            1,
        )

    def test_empty_financial_payload_blocks_fundamental_query(self) -> None:
        empty = make_row(
            stock_code="001248",
            update_date=None,
            report_period=None,
            total_shares=None,
            circulating_a_shares=None,
            shareholder_count=None,
            eps=None,
            adjusted_nav_per_share=None,
            total_assets=None,
            net_assets=None,
            operating_revenue=None,
            operating_cost=None,
            accounts_receivable=None,
            operating_profit=None,
            operating_cash_flow=None,
            inventory=None,
            total_profit=None,
            after_tax_profit=None,
            net_profit=None,
        )
        result = make_provider([empty]).query(
            make_query(instrument_ids=("001248",))
        )
        self.assertEqual(result.records, ())
        self.assertTrue(result.metadata.blocks_downstream)
        self.assertEqual(result.metadata.status, QualityStatus.FAILED)

    def test_empty_financial_payload_still_exposes_instrument_candidate(self) -> None:
        empty = make_row(
            stock_code="001248",
            update_date=None,
            report_period=None,
            total_shares=None,
            circulating_a_shares=None,
            shareholder_count=None,
            eps=None,
            adjusted_nav_per_share=None,
            total_assets=None,
            net_assets=None,
            operating_revenue=None,
            operating_cost=None,
            accounts_receivable=None,
            operating_profit=None,
            operating_cash_flow=None,
            inventory=None,
            total_profit=None,
            after_tax_profit=None,
            net_profit=None,
        )
        result = make_provider([empty]).query(
            make_query(
                canonical_object="Instrument",
                instrument_ids=("001248",),
            )
        )
        self.assertEqual(len(result.records), 1)
        self.assertFalse(result.metadata.blocks_downstream)

    def test_field_projection_and_lineage(self) -> None:
        result = make_provider().query(
            make_query(fields=("revenue_cny",))
        )
        self.assertEqual(
            result.records[0].values,
            {"revenue_cny": 35_277_000_000.0},
        )
        self.assertEqual(len(result.records[0].lineage), 1)
        self.assertEqual(
            result.records[0].lineage[0]["canonical_field"],
            "revenue_cny",
        )

    def test_unknown_field_is_rejected(self) -> None:
        with self.assertRaises(DataContractError):
            make_provider().query(make_query(fields=("unknown",)))

    def test_source_extensions_are_opt_in(self) -> None:
        hidden = make_provider().query(make_query())
        visible = make_provider().query(
            make_query(include_source_extensions=True)
        )
        self.assertEqual(hidden.records[0].source_extensions, {})
        self.assertEqual(visible.records[0].source_extensions["report_period"], 3)
        self.assertEqual(
            visible.records[0].source_extensions["operating_revenue"],
            35_277_000.0,
        )

    def test_authoritative_classification_projection(self) -> None:
        row = make_row(
            sw_sector_code="801780",
            sw_sector="银行",
        )
        result = make_provider([row]).query(
            make_query(
                canonical_object="ClassificationMembership",
                fields=("node_id", "node_name_cn", "effective_from"),
            )
        )
        self.assertGreaterEqual(len(result.records), 1)
        self.assertIn("node_id", result.records[0].values)
        self.assertNotIn("classification_node_id", result.records[0].values)


if __name__ == "__main__":
    unittest.main()
