"""测试基本面Provider与用途级时点门禁。"""
# 测试模块总览：验证 `test_fundamental_standard_provider` 对应功能的合同、边界和历史回归行为。
# - 输入：构造样例、测试夹具、临时文件以及被测模块公开接口。
# - 处理：只执行测试和断言，不修改生产算法、金融语义或正式数据库。
# - 输出：可重复的通过/失败证据，供全量回归和任务验收使用。
# - 为什么这样写：把业务要求固化为自动测试，使后续注释迁移和重构能够证明行为未变化。

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


# 测试类 `FakeAdapter`：集中验证 `test_fundamental_standard_provider` 相关合同、边界条件和回归行为。
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

    # 测试函数 `run_readonly_query`：封装 `run_readonly_query` 测试辅助步骤，减少重复样例和断言准备。
    # - 输入：script。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def run_readonly_query(self, script: str) -> Any:
        return list(self.rows)


# 测试函数 `load_registration`：封装 `load_registration` 测试辅助步骤，减少重复样例和断言准备。
# - 输入：测试对象状态、固定样例或当前测试夹具。
# - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
# - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
# - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
def load_registration() -> DatasetRegistration:
    return DatasetRegistration.from_dict(
        json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    )


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


# 测试函数 `make_provider`：封装 `make_provider` 测试辅助步骤，减少重复样例和断言准备。
# - 输入：rows。
# - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
# - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
# - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
def make_provider(
    rows: list[dict[str, Any]] | None = None,
) -> FundamentalStandardDataProvider:
    service = DolphinDBFundamentalStandardizedService(
        FakeAdapter(rows or [make_row()]),
        load_registration(),
        allow_disabled_for_acceptance=True,
    )
    return FundamentalStandardDataProvider(service)


# 测试函数 `make_query`：封装 `make_query` 测试辅助步骤，减少重复样例和断言准备。
# - 输入：**overrides。
# - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
# - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
# - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
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


# 测试类 `TestFundamentalProvider`：集中验证 `test_fundamental_standard_provider` 相关合同、边界条件和回归行为。
# - 输入：测试夹具、构造样例以及被测模块公开接口。
# - 处理：按独立场景组织断言，覆盖正常路径、失败门禁和关键边界。
# - 输出：通过或失败的单元测试结果，不产生正式业务数据。
# - 为什么这样写：把同一职责的回归场景集中管理，便于定位失败并防止后续修改破坏既有合同。
class TestFundamentalProvider(unittest.TestCase):
    # 测试函数 `test_registers_with_standard_data_service`：验证 `registers、with、standard、data、service` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_registers_with_standard_data_service(self) -> None:
        service = StandardDataService()
        service.register_provider(make_provider())
        descriptor = service.list_datasets()[0]
        self.assertEqual(descriptor.dataset_id, "a_stock_fundamental_snapshot")
        self.assertEqual(descriptor.mapping_version, "0.2.0-rc2")
        self.assertEqual(descriptor.dictionary_revision, "0.5")
        self.assertIn("FundamentalSnapshot", descriptor.supported_objects)

    # 测试函数 `test_current_snapshot_research_is_warning_not_blocked`：验证 `current、snapshot、research、is、warning、not、blocked` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_current_snapshot_research_is_warning_not_blocked(self) -> None:
        result = make_provider().query(make_query())
        self.assertEqual(result.metadata.status, QualityStatus.WARNING)
        self.assertFalse(result.metadata.blocks_downstream)
        self.assertEqual(len(result.records), 1)

    # 测试函数 `test_historical_backtest_is_blocked`：验证 `historical、backtest、is、blocked` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_historical_backtest_is_blocked(self) -> None:
        result = make_provider().query(
            make_query(usage=StandardDataUsage.STRICT_HISTORICAL_BACKTEST)
        )
        self.assertEqual(result.metadata.status, QualityStatus.FAILED)
        self.assertTrue(result.metadata.blocks_downstream)
        # 测试上下文：通过 `self.assertRaises(DataContractError)` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
        with self.assertRaises(DataContractError):
            result.assert_usable()

    # 测试函数 `test_historical_training_is_blocked`：验证 `historical、training、is、blocked` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_historical_training_is_blocked(self) -> None:
        result = make_provider().query(
            make_query(usage=StandardDataUsage.HISTORICAL_MODEL_TRAINING)
        )
        self.assertTrue(result.metadata.blocks_downstream)

    # 测试函数 `test_precoverage_query_is_blocked`：验证 `precoverage、query、is、blocked` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
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

    # 测试函数 `test_decision_time_requires_timezone`：验证 `decision、time、requires、timezone` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_decision_time_requires_timezone(self) -> None:
        # 测试上下文：通过 `self.assertRaises(DataContractError)` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
        with self.assertRaises(DataContractError):
            make_query(decision_time=datetime(2026, 6, 20, 9, 0))

    # 测试函数 `test_manual_decision_requires_decision_time`：验证 `manual、decision、requires、decision、time` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_manual_decision_requires_decision_time(self) -> None:
        # 测试上下文：通过 `self.assertRaises(DataContractError)` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
        with self.assertRaises(DataContractError):
            make_query(usage=StandardDataUsage.MANUAL_DECISION_SUPPORT)

    # 测试函数 `test_manual_decision_next_day_is_allowed_with_warning`：验证 `manual、decision、next、day、is、allowed、with、warning` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
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

    # 测试函数 `test_manual_decision_same_day_is_blocked_without_timezone_proof`：验证 `manual、decision、same、day、is、blocked、without、timezone、proof` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
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

    # 测试函数 `test_missing_imported_at_is_blocked`：验证 `missing、imported、at、is、blocked` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
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

    # 测试函数 `test_empty_financial_payload_blocks_fundamental_query`：验证 `empty、financial、payload、blocks、fundamental、query` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
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

    # 测试函数 `test_empty_financial_payload_still_exposes_instrument_candidate`：验证 `empty、financial、payload、still、exposes、instrument、candidate` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
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

    # 测试函数 `test_field_projection_and_lineage`：验证 `field、projection、and、lineage` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
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

    # 测试函数 `test_unknown_field_is_rejected`：验证 `unknown、field、is、rejected` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_unknown_field_is_rejected(self) -> None:
        # 测试上下文：通过 `self.assertRaises(DataContractError)` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
        with self.assertRaises(DataContractError):
            make_provider().query(make_query(fields=("unknown",)))

    # 测试函数 `test_source_extensions_are_opt_in`：验证 `source、extensions、are、opt、in` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
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

    # 测试函数 `test_authoritative_classification_projection`：验证 `authoritative、classification、projection` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
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
