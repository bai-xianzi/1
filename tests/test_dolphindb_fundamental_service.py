"""测试基本面标准化读取服务。"""
# 测试模块总览：验证 `test_dolphindb_fundamental_service` 对应功能的合同、边界和历史回归行为。
# - 输入：构造样例、测试夹具、临时文件以及被测模块公开接口。
# - 处理：只执行测试和断言，不修改生产算法、金融语义或正式数据库。
# - 输出：可重复的通过/失败证据，供全量回归和任务验收使用。
# - 为什么这样写：把业务要求固化为自动测试，使后续注释迁移和重构能够证明行为未变化。

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


# 测试类 `FakeAdapter`：集中验证 `test_dolphindb_fundamental_service` 相关合同、边界条件和回归行为。
# - 输入：测试夹具、构造样例以及被测模块公开接口。
# - 处理：按独立场景组织断言，覆盖正常路径、失败门禁和关键边界。
# - 输出：通过或失败的单元测试结果，不产生正式业务数据。
# - 为什么这样写：把同一职责的回归场景集中管理，便于定位失败并防止后续修改破坏既有合同。
class FakeAdapter:
    # 测试函数 `__init__`：封装 `__init__` 测试辅助步骤，减少重复样例和断言准备。
    # - 输入：rows。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self.rows = rows
        self.scripts: list[str] = []

    # 测试函数 `run_readonly_query`：封装 `run_readonly_query` 测试辅助步骤，减少重复样例和断言准备。
    # - 输入：script。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def run_readonly_query(self, script: str) -> Any:
        self.scripts.append(script)
        return list(self.rows)


# 测试函数 `load_registration`：封装 `load_registration` 测试辅助步骤，减少重复样例和断言准备。
# - 输入：enabled。
# - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
# - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
# - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
def load_registration(*, enabled: bool = False) -> DatasetRegistration:
    value = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    value["enabled"] = enabled
    return DatasetRegistration.from_dict(value)


# 测试函数 `load_authority_catalog`：封装 `load_authority_catalog` 测试辅助步骤，减少重复样例和断言准备。
# - 输入：测试对象状态、固定样例或当前测试夹具。
# - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
# - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
# - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
def load_authority_catalog() -> dict[str, set[str]]:
    catalog: dict[str, set[str]] = {}
    current_object: str | None = None
    # 参数化循环：逐项使用 `SCHEMA_PATH.read_text(encoding='utf-8').splitlines()` 验证同一合同。
    # - 处理：每轮保留原样例、顺序和断言，便于定位具体失败项。
    # - 为什么这样写：用一致规则覆盖多组输入，减少复制测试并提高边界覆盖率。
    for raw_line in SCHEMA_PATH.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.strip()
        # 测试分支：根据 `stripped.startswith('canonical_object:')` 选择对应断言或样例路径。
        # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
        # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
        if stripped.startswith("canonical_object:"):
            current_object = stripped.split(":", 1)[1].strip()
            catalog.setdefault(current_object, set())
        # 测试分支：根据 `stripped.startswith('- canonical_name:') and current_object` 选择对应断言或样例路径。
        # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
        # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
        elif stripped.startswith("- canonical_name:") and current_object:
            name = stripped.split(":", 1)[1].strip()
            catalog[current_object].add(name)
    return catalog


# 测试函数 `make_row`：封装 `make_row` 测试辅助步骤，减少重复样例和断言准备。
# - 输入：**overrides。
# - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
# - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
# - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
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


# 测试类 `TestFundamentalReadRequest`：集中验证 `test_dolphindb_fundamental_service` 相关合同、边界条件和回归行为。
# - 输入：测试夹具、构造样例以及被测模块公开接口。
# - 处理：按独立场景组织断言，覆盖正常路径、失败门禁和关键边界。
# - 输出：通过或失败的单元测试结果，不产生正式业务数据。
# - 为什么这样写：把同一职责的回归场景集中管理，便于定位失败并防止后续修改破坏既有合同。
class TestFundamentalReadRequest(unittest.TestCase):
    # 测试函数 `test_rejects_invalid_stock_code`：验证 `rejects、invalid、stock、code` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_rejects_invalid_stock_code(self) -> None:
        # 测试上下文：通过 `self.assertRaises(DataContractError)` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
        with self.assertRaises(DataContractError):
            FundamentalReadRequest(
                instrument_ids=("000001.SZ",),
                start_date=date(2026, 6, 19),
                end_date=date(2026, 6, 19),
            )

    # 测试函数 `test_rejects_duplicate_stock_code`：验证 `rejects、duplicate、stock、code` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_rejects_duplicate_stock_code(self) -> None:
        # 测试上下文：通过 `self.assertRaises(DataContractError)` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
        with self.assertRaises(DataContractError):
            FundamentalReadRequest(
                instrument_ids=("000001", "000001"),
                start_date=date(2026, 6, 19),
                end_date=date(2026, 6, 19),
            )


# 测试类 `TestReportPeriodDerivation`：集中验证 `test_dolphindb_fundamental_service` 相关合同、边界条件和回归行为。
# - 输入：测试夹具、构造样例以及被测模块公开接口。
# - 处理：按独立场景组织断言，覆盖正常路径、失败门禁和关键边界。
# - 输出：通过或失败的单元测试结果，不产生正式业务数据。
# - 为什么这样写：把同一职责的回归场景集中管理，便于定位失败并防止后续修改破坏既有合同。
class TestReportPeriodDerivation(unittest.TestCase):
    # 测试函数 `test_derives_current_year_q1`：验证 `derives、current、year、q1` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_derives_current_year_q1(self) -> None:
        result = derive_report_period(date(2026, 4, 25), 3)
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.report_period, date(2026, 3, 31))
        self.assertEqual(result.period_type, "QUARTERLY")
        self.assertEqual(result.fiscal_quarter, 1)

    # 测试函数 `test_derives_previous_year_q3`：验证 `derives、previous、year、q3` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_derives_previous_year_q3(self) -> None:
        result = derive_report_period(date(2026, 4, 29), 9)
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.report_period, date(2025, 9, 30))

    # 测试函数 `test_derives_previous_year_annual`：验证 `derives、previous、year、annual` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_derives_previous_year_annual(self) -> None:
        result = derive_report_period(date(2026, 4, 29), 12)
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.report_period, date(2025, 12, 31))
        self.assertEqual(result.period_type, "ANNUAL")
        self.assertEqual(result.fiscal_quarter, 4)


# 测试类 `TestFundamentalStandardizedService`：集中验证 `test_dolphindb_fundamental_service` 相关合同、边界条件和回归行为。
# - 输入：测试夹具、构造样例以及被测模块公开接口。
# - 处理：按独立场景组织断言，覆盖正常路径、失败门禁和关键边界。
# - 输出：通过或失败的单元测试结果，不产生正式业务数据。
# - 为什么这样写：把同一职责的回归场景集中管理，便于定位失败并防止后续修改破坏既有合同。
class TestFundamentalStandardizedService(unittest.TestCase):
    # 测试函数 `make_service`：封装 `make_service` 测试辅助步骤，减少重复样例和断言准备。
    # - 输入：rows。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
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

    # 测试函数 `make_request`：封装 `make_request` 测试辅助步骤，减少重复样例和断言准备。
    # - 输入：instrument_id。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    @staticmethod
    def make_request(instrument_id: str = "000001") -> FundamentalReadRequest:
        return FundamentalReadRequest(
            instrument_ids=(instrument_id,),
            start_date=date(2026, 6, 19),
            end_date=date(2026, 6, 19),
        )

    # 测试函数 `test_disabled_registration_requires_explicit_acceptance`：验证 `disabled、registration、requires、explicit、acceptance` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_disabled_registration_requires_explicit_acceptance(self) -> None:
        # 测试上下文：通过 `self.assertRaises(DataContractError)` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
        with self.assertRaises(DataContractError):
            DolphinDBFundamentalStandardizedService(
                FakeAdapter([make_row()]),
                load_registration(),
            )

    # 测试函数 `test_enabled_registration_does_not_need_override`：验证 `enabled、registration、does、not、need、override` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_enabled_registration_does_not_need_override(self) -> None:
        service = DolphinDBFundamentalStandardizedService(
            FakeAdapter([make_row()]),
            load_registration(enabled=True),
        )
        self.assertEqual(service.registration.mapping_version, "0.2.0-rc2")

    # 测试函数 `test_query_is_readonly_registered_and_filtered`：验证 `query、is、readonly、registered、and、filtered` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
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

    # 测试函数 `test_scales_money_and_shares`：验证 `scales、money、and、shares` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
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

    # 测试函数 `test_only_emits_authoritative_canonical_fields`：验证 `only、emits、authoritative、canonical、fields` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_only_emits_authoritative_canonical_fields(self) -> None:
        service, _ = self.make_service()
        batch = service.read(self.make_request())
        catalog = load_authority_catalog()
        # 参数化循环：逐项使用 `batch.records` 验证同一合同。
        # - 处理：每轮保留原样例、顺序和断言，便于定位具体失败项。
        # - 为什么这样写：用一致规则覆盖多组输入，减少复制测试并提高边界覆盖率。
        for record in batch.records:
            self.assertTrue(
                set(record.values).issubset(catalog[record.canonical_object]),
                (record.canonical_object, set(record.values) - catalog[record.canonical_object]),
            )

    # 测试函数 `test_registration_mapped_targets_exist_in_authority_catalog`：验证 `registration、mapped、targets、exist、in、authority、catalog` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_registration_mapped_targets_exist_in_authority_catalog(self) -> None:
        registration = load_registration()
        catalog = load_authority_catalog()
        # 参数化循环：逐项使用 `registration.field_mappings` 验证同一合同。
        # - 处理：每轮保留原样例、顺序和断言，便于定位具体失败项。
        # - 为什么这样写：用一致规则覆盖多组输入，减少复制测试并提高边界覆盖率。
        for rule in registration.field_mappings:
            # 测试分支：根据 `rule.canonical_target is None` 选择对应断言或样例路径。
            # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
            # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
            if rule.canonical_target is None:
                continue
            assert rule.target_object is not None
            assert rule.canonical_field is not None
            self.assertIn(rule.target_object, catalog)
            self.assertIn(rule.canonical_field, catalog[rule.target_object])
        self.assertTrue(registration.mapping_coverage()["all_source_fields_accounted"])

    # 测试函数 `test_produces_derived_report_period_and_raw_extensions`：验证 `produces、derived、report、period、and、raw、extensions` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
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

    # 测试函数 `test_empty_financial_payload_is_not_zero_filled`：验证 `empty、financial、payload、is、not、zero、filled` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
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

    # 测试函数 `test_incomplete_identity_is_preserved_with_warning`：验证 `incomplete、identity、is、preserved、with、warning` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
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

    # 测试函数 `test_instrument_uses_authoritative_enums`：验证 `instrument、uses、authoritative、enums` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
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

    # 测试函数 `test_classification_records_use_authoritative_names`：验证 `classification、records、use、authoritative、names` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
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
