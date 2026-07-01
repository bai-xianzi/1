# 测试模块总览：验证 `test_daily_funds_standard_provider` 对应功能的合同、边界和历史回归行为。
# - 输入：构造样例、测试夹具、临时文件以及被测模块公开接口。
# - 处理：只执行测试和断言，不修改生产算法、金融语义或正式数据库。
# - 输出：可重复的通过/失败证据，供全量回归和任务验收使用。
# - 为什么这样写：把业务要求固化为自动测试，使后续注释迁移和重构能够证明行为未变化。
from __future__ import annotations

import unittest
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from a_stock_quant.data_contracts import DataContractError, QualityStatus
from a_stock_quant.daily_funds_standard_provider import (
    DailyFundsStandardDataProvider,
    build_daily_funds_standard_providers,
    register_daily_funds_standard_providers,
)
from a_stock_quant.dolphindb_daily_funds_service import (
    DailyFundsCanonicalRecord,
    DailyFundsStandardBatch,
)
from a_stock_quant.standard_data_service import (
    ENTITY_SELECTOR_MODE,
    INSTRUMENT_SELECTOR_MODE,
    StandardDataQuery,
    StandardDataService,
    StandardDataUsage,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


# 测试类 `FakeCanonicalService`：集中验证 `test_daily_funds_standard_provider` 相关合同、边界条件和回归行为。
# - 输入：测试夹具、构造样例以及被测模块公开接口。
# - 处理：按独立场景组织断言，覆盖正常路径、失败门禁和关键边界。
# - 输出：通过或失败的单元测试结果，不产生正式业务数据。
# - 为什么这样写：把同一职责的回归场景集中管理，便于定位失败并防止后续修改破坏既有合同。
class FakeCanonicalService:
    coverage_version = "daily-funds-test"
    mapping_version = "0.2.0"
    dictionary_revision = "0.6.0"

    # 测试函数 `__init__`：封装 `__init__` 测试辅助步骤，减少重复样例和断言准备。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def __init__(self) -> None:
        self.requests: list[Any] = []
        self.profiles = {
            "hq": {"canonical_object": "DailyBar", "selector_mode": "INSTRUMENT_ID"},
            "kphq": {"canonical_object": "AuctionSnapshot", "selector_mode": "INSTRUMENT_ID"},
            "hy": {"canonical_object": "ClassificationMarketSnapshot", "selector_mode": "NODE_NAME_OR_PROVISIONAL_ID"},
            "gn": {"canonical_object": "ClassificationMarketSnapshot", "selector_mode": "NODE_NAME_OR_PROVISIONAL_ID"},
            "kphy": {"canonical_object": "ClassificationMarketSnapshot", "selector_mode": "NODE_NAME_OR_PROVISIONAL_ID"},
            "kpgn": {"canonical_object": "ClassificationMarketSnapshot", "selector_mode": "NODE_NAME_OR_PROVISIONAL_ID"},
            "zj": {"canonical_object": "MoneyFlowSnapshot", "selector_mode": "INSTRUMENT_ID"},
        }

    # 测试函数 `dataset_profile`：封装 `dataset_profile` 测试辅助步骤，减少重复样例和断言准备。
    # - 输入：dataset_id。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def dataset_profile(self, dataset_id: str) -> dict[str, Any]:
        return dict(self.profiles[dataset_id])

    # 测试函数 `available_fields`：封装 `available_fields` 测试辅助步骤，减少重复样例和断言准备。
    # - 输入：dataset_id。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def available_fields(self, dataset_id: str) -> tuple[str, ...]:
        object_name = self.profiles[dataset_id]["canonical_object"]
        # 测试分支：根据 `object_name == 'DailyBar'` 选择对应断言或样例路径。
        # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
        # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
        if object_name == "DailyBar":
            return ("instrument_id", "trade_date", "close_raw_cny")
        # 测试分支：根据 `object_name == 'AuctionSnapshot'` 选择对应断言或样例路径。
        # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
        # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
        if object_name == "AuctionSnapshot":
            return ("instrument_id", "trade_date", "snapshot_time_precision")
        # 测试分支：根据 `object_name == 'ClassificationMarketSnapshot'` 选择对应断言或样例路径。
        # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
        # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
        if object_name == "ClassificationMarketSnapshot":
            return ("node_id", "node_name_cn", "trade_date")
        return ("instrument_id", "trade_date", "net_inflow_total_cny")

    # 测试函数 `read`：封装 `read` 测试辅助步骤，减少重复样例和断言准备。
    # - 输入：request。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def read(self, request: Any) -> DailyFundsStandardBatch:
        self.requests.append(request)
        object_name = self.profiles[request.dataset_id]["canonical_object"]
        selector = request.entity_ids[0]
        # 测试分支：根据 `object_name == 'ClassificationMarketSnapshot'` 选择对应断言或样例路径。
        # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
        # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
        if object_name == "ClassificationMarketSnapshot":
            primary_key = {"node_id": selector, "trade_date": request.end_date, "snapshot_phase": "CLOSE", "classification_system": "SOURCE_VENDOR", "classification_type": "INDUSTRY"}
            values = {"node_id": selector, "node_name_cn": "银行", "trade_date": request.end_date}
        else:
            primary_key = {"instrument_id": selector, "trade_date": request.end_date}
            values = {"instrument_id": selector, "trade_date": request.end_date}
            # 测试分支：根据 `object_name == 'DailyBar'` 选择对应断言或样例路径。
            # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
            # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
            if object_name == "DailyBar":
                values["close_raw_cny"] = 10.0
            # 测试分支：根据 `object_name == 'AuctionSnapshot'` 选择对应断言或样例路径。
            # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
            # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
            elif object_name == "AuctionSnapshot":
                values["snapshot_time_precision"] = "DATE_ONLY"
            else:
                values["net_inflow_total_cny"] = 1.0
        record = DailyFundsCanonicalRecord(
            dataset_id=request.dataset_id,
            canonical_object=object_name,
            primary_key=primary_key,
            values=values,
            source_record_id=f"{request.dataset_id}:hash:1",
            source_extensions={"raw": "value"},
            quality_flags=("SOURCE_WARNING",),
            lineage=({"canonical_field": next(iter(values)), "source_fields": ["x"]},),
            snapshot_date=request.end_date,
        )
        return DailyFundsStandardBatch(
            dataset_id=request.dataset_id,
            canonical_object=object_name,
            coverage_version=self.coverage_version,
            mapping_version=self.mapping_version,
            dictionary_revision=self.dictionary_revision,
            scanned_source_row_count=1,
            source_row_count=1,
            records=(record,),
            warnings=(),
        )


# 测试类 `Task017DStandardProviderTests`：集中验证 `test_daily_funds_standard_provider` 相关合同、边界条件和回归行为。
# - 输入：测试夹具、构造样例以及被测模块公开接口。
# - 处理：按独立场景组织断言，覆盖正常路径、失败门禁和关键边界。
# - 输出：通过或失败的单元测试结果，不产生正式业务数据。
# - 为什么这样写：把同一职责的回归场景集中管理，便于定位失败并防止后续修改破坏既有合同。
class Task017DStandardProviderTests(unittest.TestCase):
    # 测试函数 `test_legacy_instrument_query_remains_supported`：验证 `legacy、instrument、query、remains、supported` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_legacy_instrument_query_remains_supported(self) -> None:
        query = StandardDataQuery(
            dataset_id="hq",
            canonical_object="DailyBar",
            instrument_ids=("000001",),
            start_date=date(2025, 11, 20),
            end_date=date(2025, 11, 20),
        )
        self.assertEqual(query.selector_mode, INSTRUMENT_SELECTOR_MODE)
        self.assertEqual(query.selector_ids, ("000001",))
        self.assertEqual(query.entity_ids, ())

    # 测试函数 `test_generic_entity_query_is_supported`：验证 `generic、entity、query、is、supported` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_generic_entity_query_is_supported(self) -> None:
        query = StandardDataQuery(
            dataset_id="hy",
            canonical_object="ClassificationMarketSnapshot",
            instrument_ids=(),
            entity_ids=("SOURCE_VENDOR:INDUSTRY:ABC",),
            start_date=date(2025, 11, 20),
            end_date=date(2025, 11, 20),
        )
        self.assertEqual(query.selector_mode, ENTITY_SELECTOR_MODE)
        self.assertEqual(query.selector_ids, query.entity_ids)

    # 测试函数 `test_exactly_one_selector_is_required`：验证 `exactly、one、selector、is、required` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_exactly_one_selector_is_required(self) -> None:
        kwargs = dict(
            dataset_id="hq",
            canonical_object="DailyBar",
            start_date=date(2025, 11, 20),
            end_date=date(2025, 11, 20),
        )
        # 测试上下文：通过 `self.assertRaises(DataContractError)` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
        with self.assertRaises(DataContractError):
            StandardDataQuery(instrument_ids=(), **kwargs)
        # 测试上下文：通过 `self.assertRaises(DataContractError)` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
        with self.assertRaises(DataContractError):
            StandardDataQuery(
                instrument_ids=("000001",),
                entity_ids=("node",),
                **kwargs,
            )

    # 测试函数 `test_builds_seven_providers_with_correct_modes`：验证 `builds、seven、providers、with、correct、modes` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_builds_seven_providers_with_correct_modes(self) -> None:
        providers = build_daily_funds_standard_providers(
            FakeCanonicalService(),
            project_root=PROJECT_ROOT,
        )
        self.assertEqual(len(providers), 7)
        modes = {p.dataset_id: p.descriptor.selector_mode for p in providers}
        self.assertEqual(modes["hq"], INSTRUMENT_SELECTOR_MODE)
        self.assertEqual(modes["hy"], ENTITY_SELECTOR_MODE)

    # 测试函数 `test_registers_seven_providers`：验证 `registers、seven、providers` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_registers_seven_providers(self) -> None:
        standard = StandardDataService()
        descriptors = register_daily_funds_standard_providers(
            standard,
            FakeCanonicalService(),
            project_root=PROJECT_ROOT,
        )
        self.assertEqual(len(descriptors), 7)
        self.assertEqual(len(standard.list_datasets()), 7)

    # 测试函数 `test_security_provider_uses_instrument_selector`：验证 `security、provider、uses、instrument、selector` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_security_provider_uses_instrument_selector(self) -> None:
        canonical = FakeCanonicalService()
        standard = StandardDataService()
        register_daily_funds_standard_providers(
            standard, canonical, project_root=PROJECT_ROOT
        )
        result = standard.query(
            StandardDataQuery(
                dataset_id="hq",
                canonical_object="DailyBar",
                instrument_ids=("000001",),
                start_date=date(2025, 11, 20),
                end_date=date(2025, 11, 20),
            )
        )
        self.assertEqual(canonical.requests[-1].entity_ids, ("000001",))
        self.assertEqual(result.metadata.status, QualityStatus.WARNING)
        self.assertFalse(result.metadata.blocks_downstream)

    # 测试函数 `test_classification_provider_uses_entity_selector`：验证 `classification、provider、uses、entity、selector` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_classification_provider_uses_entity_selector(self) -> None:
        canonical = FakeCanonicalService()
        standard = StandardDataService()
        register_daily_funds_standard_providers(
            standard, canonical, project_root=PROJECT_ROOT
        )
        result = standard.query(
            StandardDataQuery(
                dataset_id="hy",
                canonical_object="ClassificationMarketSnapshot",
                instrument_ids=(),
                entity_ids=("SOURCE_VENDOR:INDUSTRY:ABC",),
                start_date=date(2025, 11, 20),
                end_date=date(2025, 11, 20),
            )
        )
        self.assertEqual(result.records[0].primary_key["node_id"], "SOURCE_VENDOR:INDUSTRY:ABC")
        self.assertNotIn("instrument_id", result.records[0].primary_key)

    # 测试函数 `test_selector_mismatch_is_rejected_by_standard_service`：验证 `selector、mismatch、is、rejected、by、standard、service` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_selector_mismatch_is_rejected_by_standard_service(self) -> None:
        standard = StandardDataService()
        register_daily_funds_standard_providers(
            standard, FakeCanonicalService(), project_root=PROJECT_ROOT
        )
        # 测试上下文：通过 `self.assertRaises(DataContractError)` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
        with self.assertRaises(DataContractError):
            standard.query(
                StandardDataQuery(
                    dataset_id="hy",
                    canonical_object="ClassificationMarketSnapshot",
                    instrument_ids=("000001",),
                    start_date=date(2025, 11, 20),
                    end_date=date(2025, 11, 20),
                )
            )

    # 测试函数 `test_field_projection_and_optional_payloads`：验证 `field、projection、and、optional、payloads` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_field_projection_and_optional_payloads(self) -> None:
        provider = DailyFundsStandardDataProvider(
            FakeCanonicalService(), "hq", project_root=PROJECT_ROOT
        )
        result = provider.query(
            StandardDataQuery(
                dataset_id="hq",
                canonical_object="DailyBar",
                instrument_ids=("000001",),
                start_date=date(2025, 11, 20),
                end_date=date(2025, 11, 20),
                fields=("close_raw_cny",),
                include_source_extensions=False,
                include_quality_flags=False,
                include_lineage=False,
            )
        )
        record = result.records[0]
        self.assertEqual(record.values, {"close_raw_cny": 10.0})
        self.assertEqual(record.source_extensions, {})
        self.assertEqual(record.quality_flags, ())
        self.assertEqual(record.lineage, ())

    # 测试函数 `test_strict_historical_usage_is_blocked`：验证 `strict、historical、usage、is、blocked` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_strict_historical_usage_is_blocked(self) -> None:
        provider = DailyFundsStandardDataProvider(
            FakeCanonicalService(), "hq", project_root=PROJECT_ROOT
        )
        result = provider.query(
            StandardDataQuery(
                dataset_id="hq",
                canonical_object="DailyBar",
                instrument_ids=("000001",),
                start_date=date(2025, 11, 20),
                end_date=date(2025, 11, 20),
                usage=StandardDataUsage.STRICT_HISTORICAL_BACKTEST,
            )
        )
        self.assertTrue(result.metadata.blocks_downstream)
        self.assertEqual(result.metadata.status, QualityStatus.FAILED)
        # 测试上下文：通过 `self.assertRaises(DataContractError)` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
        with self.assertRaises(DataContractError):
            result.assert_usable()

    # 测试函数 `test_same_day_manual_decision_is_blocked`：验证 `same、day、manual、decision、is、blocked` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_same_day_manual_decision_is_blocked(self) -> None:
        provider = DailyFundsStandardDataProvider(
            FakeCanonicalService(), "hq", project_root=PROJECT_ROOT
        )
        result = provider.query(
            StandardDataQuery(
                dataset_id="hq",
                canonical_object="DailyBar",
                instrument_ids=("000001",),
                start_date=date(2025, 11, 20),
                end_date=date(2025, 11, 20),
                usage=StandardDataUsage.MANUAL_DECISION_SUPPORT,
                decision_time=datetime(2025, 11, 20, 15, 0, tzinfo=timezone.utc),
            )
        )
        self.assertTrue(result.metadata.blocks_downstream)

    # 测试函数 `test_unknown_field_is_rejected`：验证 `unknown、field、is、rejected` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_unknown_field_is_rejected(self) -> None:
        provider = DailyFundsStandardDataProvider(
            FakeCanonicalService(), "hq", project_root=PROJECT_ROOT
        )
        # 测试上下文：通过 `self.assertRaises(DataContractError)` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
        with self.assertRaises(DataContractError):
            provider.query(
                StandardDataQuery(
                    dataset_id="hq",
                    canonical_object="DailyBar",
                    instrument_ids=("000001",),
                    start_date=date(2025, 11, 20),
                    end_date=date(2025, 11, 20),
                    fields=("not_a_field",),
                )
            )


if __name__ == "__main__":
    unittest.main()
