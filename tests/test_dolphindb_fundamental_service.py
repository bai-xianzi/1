"""测试基本面标准化读取服务。"""

from __future__ import annotations

import json
import sys
import unittest
from datetime import date, datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from a_stock_quant.data_contracts import DataContractError
from a_stock_quant.dataset_registry import DatasetRegistration
from a_stock_quant.dolphindb_fundamental_service import (
    DolphinDBFundamentalStandardizedService,
    FundamentalReadRequest,
    derive_report_period,
)


CONFIG_PATH = (
    PROJECT_ROOT
    / "configs"
    / "datasets"
    / "a_stock_fundamental_snapshot.json"
)
SCHEMA_PATH = PROJECT_ROOT / "schemas" / "canonical_fields.yaml"


class FakeAdapter:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self.rows = rows
        self.scripts: list[str] = []

    def run_readonly_query(self, script: str) -> Any:
        self.scripts.append(script)
        return list(self.rows)


def load_registration(*, enabled: bool = False) -> DatasetRegistration:
    value = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    value["enabled"] = enabled
    return DatasetRegistration.from_dict(value)


def load_authority_catalog() -> dict[str, set[str]]:
    catalog: dict[str, set[str]] = {}
    current_object: str | None = None
    for raw_line in SCHEMA_PATH.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.strip()
        if stripped.startswith("canonical_object:"):
            current_object = stripped.split(":", 1)[1].strip()
            catalog.setdefault(current_object, set())
        elif stripped.startswith("- canonical_name:") and current_object:
            name = stripped.split(":", 1)[1].strip()
            catalog[current_object].add(name)
    return catalog


def make_row(**overrides: Any) -> dict[str, Any]:
    values: dict[str, Any] = {
        "stock_code": "000001",
        "snapshot_date": date(2026, 6, 19),
        "update_date": date(2026, 4, 25),
        "report_period": 3,
        "total_shares": 1_940_591.87,
        "b_shares": 0.0,
        "h_shares": 0.0,
        "circulating_a_shares": 1_940_560.12,
        "shareholder_count": 457_610,
        "eps": 0.67,
        "adjusted_nav_per_share": 23.91,
        "zpg": None,
        "total_assets": 6_033_961_984.0,
        "current_assets": 0.0,
        "fixed_assets": 0.0,
        "intangible_assets": 0.0,
        "current_liabilities": 0.0,
        "long_term_liabilities": 0.0,
        "capital_reserve": 0.0,
        "net_assets": 544_083_008.0,
        "operating_revenue": 35_277_000.0,
        "operating_cost": 17_888_000.0,
        "accounts_receivable": 0.0,
        "operating_profit": 17_389_000.0,
        "investment_income": 0.0,
        "operating_cash_flow": 10_000_000.0,
        "total_cash_flow": 0.0,
        "inventory": 0.0,
        "total_profit": 17_399_000.0,
        "after_tax_profit": 14_523_000.0,
        "net_profit": 14_523_000.0,
        "undistributed_profit": 0.0,
        "region_code": 1,
        "source_industry_code": 1,
        "market": "sz",
        "stock_name": "平安银行",
        "pinyin": "PAYH",
        "listing_date": date(1991, 4, 3),
        "source_file": "fundamental.xlsx",
        "imported_at": datetime(2026, 6, 19, 19, 36, 51),
        "sw_code": "801780",
        "source_industry_level1_code": "10",
        "source_industry_level2_code": "1010",
        "source_detail_code": "101010",
        "source_sector": "金融",
        "source_industry": "银行",
        "source_subindustry": "股份制银行",
        "tdx_industry_code": "T001",
        "sw_sector_code": "801780",
        "sw_industry_code": "80178001",
        "sw_subindustry_code": "8017800101",
        "sw_sector": "银行",
        "sw_industry": "股份制银行",
        "sw_subindustry": "股份制银行",
    }
    values.update(overrides)
    return values


class TestFundamentalReadRequest(unittest.TestCase):
    def test_rejects_invalid_stock_code(self) -> None:
        with self.assertRaises(DataContractError):
            FundamentalReadRequest(
                instrument_ids=("000001.SZ",),
                start_date=date(2026, 6, 19),
                end_date=date(2026, 6, 19),
            )

    def test_rejects_duplicate_stock_code(self) -> None:
        with self.assertRaises(DataContractError):
            FundamentalReadRequest(
                instrument_ids=("000001", "000001"),
                start_date=date(2026, 6, 19),
                end_date=date(2026, 6, 19),
            )


class TestReportPeriodDerivation(unittest.TestCase):
    def test_derives_current_year_q1(self) -> None:
        result = derive_report_period(date(2026, 4, 25), 3)
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.report_period, date(2026, 3, 31))
        self.assertEqual(result.period_type, "QUARTERLY")
        self.assertEqual(result.fiscal_quarter, 1)

    def test_derives_previous_year_q3(self) -> None:
        result = derive_report_period(date(2026, 4, 29), 9)
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.report_period, date(2025, 9, 30))

    def test_derives_previous_year_annual(self) -> None:
        result = derive_report_period(date(2026, 4, 29), 12)
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.report_period, date(2025, 12, 31))
        self.assertEqual(result.period_type, "ANNUAL")
        self.assertEqual(result.fiscal_quarter, 4)


class TestFundamentalStandardizedService(unittest.TestCase):
    def make_service(
        self,
        rows: list[dict[str, Any]] | None = None,
    ) -> tuple[DolphinDBFundamentalStandardizedService, FakeAdapter]:
        adapter = FakeAdapter(rows or [make_row()])
        service = DolphinDBFundamentalStandardizedService(
            adapter,
            load_registration(),
            allow_disabled_for_acceptance=True,
        )
        return service, adapter

    @staticmethod
    def make_request(instrument_id: str = "000001") -> FundamentalReadRequest:
        return FundamentalReadRequest(
            instrument_ids=(instrument_id,),
            start_date=date(2026, 6, 19),
            end_date=date(2026, 6, 19),
        )

    def test_disabled_registration_requires_explicit_acceptance(self) -> None:
        with self.assertRaises(DataContractError):
            DolphinDBFundamentalStandardizedService(
                FakeAdapter([make_row()]),
                load_registration(),
            )

    def test_enabled_registration_does_not_need_override(self) -> None:
        service = DolphinDBFundamentalStandardizedService(
            FakeAdapter([make_row()]),
            load_registration(enabled=True),
        )
        self.assertEqual(service.registration.mapping_version, "0.2.0-rc2")

    def test_query_is_readonly_registered_and_filtered(self) -> None:
        service, adapter = self.make_service()
        service.read(self.make_request())
        self.assertEqual(len(adapter.scripts), 1)
        script = adapter.scripts[0]
        self.assertTrue(script.startswith("select stock_code"))
        self.assertNotIn("select *", script)
        self.assertIn("stock_code in symbol", script)
        self.assertIn("snapshot_date >= 2026.06.19", script)
        self.assertNotIn(";", script)
        self.assertNotIn("D:\\Users\\Administrator\\Desktop", script)

    def test_scales_money_and_shares(self) -> None:
        service, _ = self.make_service()
        batch = service.read(self.make_request())
        fundamental = next(
            item for item in batch.records
            if item.canonical_object == "FundamentalSnapshot"
        )
        ownership = next(
            item for item in batch.records
            if item.canonical_object == "OwnershipSnapshot"
        )
        self.assertEqual(
            fundamental.values["revenue_cny"],
            35_277_000_000.0,
        )
        self.assertEqual(
            ownership.values["total_shares"],
            19_405_918_700,
        )
        self.assertIsInstance(ownership.values["total_shares"], int)
        self.assertEqual(
            ownership.values["float_shares"],
            19_405_601_200,
        )

    def test_only_emits_authoritative_canonical_fields(self) -> None:
        service, _ = self.make_service()
        batch = service.read(self.make_request())
        catalog = load_authority_catalog()
        for record in batch.records:
            self.assertTrue(
                set(record.values).issubset(catalog[record.canonical_object]),
                (record.canonical_object, set(record.values) - catalog[record.canonical_object]),
            )

    def test_registration_mapped_targets_exist_in_authority_catalog(self) -> None:
        registration = load_registration()
        catalog = load_authority_catalog()
        for rule in registration.field_mappings:
            if rule.canonical_target is None:
                continue
            assert rule.target_object is not None
            assert rule.canonical_field is not None
            self.assertIn(rule.target_object, catalog)
            self.assertIn(rule.canonical_field, catalog[rule.target_object])
        self.assertTrue(registration.mapping_coverage()["all_source_fields_accounted"])

    def test_produces_derived_report_period_and_raw_extensions(self) -> None:
        service, _ = self.make_service()
        batch = service.read(self.make_request())
        record = next(
            item for item in batch.records
            if item.canonical_object == "FundamentalSnapshot"
        )
        self.assertEqual(record.values["report_period"], date(2026, 3, 31))
        self.assertIn("REPORT_PERIOD_DERIVED", record.quality_flags)
        self.assertEqual(record.source_extensions["report_period"], 3)
        self.assertEqual(
            record.source_extensions["operating_revenue"],
            35_277_000.0,
        )
        self.assertEqual(
            record.source_extensions["raw_unit_contract"]["money_fields"]["canonical_factor"],
            1_000,
        )

    def test_empty_financial_payload_is_not_zero_filled(self) -> None:
        empty = make_row(
            stock_code="001248",
            stock_name="华润新能",
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
        service, _ = self.make_service([empty])
        batch = service.read(self.make_request("001248"))
        objects = {item.canonical_object for item in batch.records}
        self.assertIn("Instrument", objects)
        self.assertNotIn("FundamentalSnapshot", objects)
        self.assertNotIn("OwnershipSnapshot", objects)
        self.assertIn("001248 没有可用财务载荷。", batch.warnings)

    def test_incomplete_identity_is_preserved_with_warning(self) -> None:
        row = make_row(
            stock_code="001235",
            market=None,
            stock_name=None,
            listing_date=None,
            update_date=None,
            report_period=None,
            total_assets=None,
            operating_revenue=None,
            net_profit=None,
        )
        service, _ = self.make_service([row])
        batch = service.read(self.make_request("001235"))
        instrument = next(
            item for item in batch.records
            if item.canonical_object == "Instrument"
        )
        self.assertIsNone(instrument.values["exchange_code"])
        self.assertIsNone(instrument.values["market_code"])
        self.assertIn(
            "INCOMPLETE_INSTRUMENT_IDENTITY",
            instrument.quality_flags,
        )

    def test_instrument_uses_authoritative_enums(self) -> None:
        service, _ = self.make_service()
        batch = service.read(self.make_request())
        instrument = next(
            item for item in batch.records
            if item.canonical_object == "Instrument"
        )
        self.assertEqual(instrument.values["exchange_code"], "SZSE")
        self.assertEqual(instrument.values["asset_class"], "EQUITY")
        self.assertEqual(instrument.values["security_type"], "COMMON_STOCK")
        self.assertEqual(instrument.values["trading_status"], "UNKNOWN")

    def test_classification_records_use_authoritative_names(self) -> None:
        service, _ = self.make_service()
        batch = service.read(self.make_request())
        classifications = [
            item for item in batch.records
            if item.canonical_object == "ClassificationMembership"
        ]
        self.assertGreaterEqual(len(classifications), 6)
        first = classifications[0]
        self.assertIn("node_id", first.values)
        self.assertIn("node_name_cn", first.values)
        self.assertIn("node_level", first.values)
        self.assertIsInstance(first.values["effective_from"], datetime)
        self.assertIn(
            "CLASSIFICATION_VERSION_UNKNOWN",
            first.quality_flags,
        )


if __name__ == "__main__":
    unittest.main()
