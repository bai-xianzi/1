# 测试模块总览：验证 `test_readiness_gated_data_service` 对应功能的合同、边界和历史回归行为。
# - 输入：构造样例、测试夹具、临时文件以及被测模块公开接口。
# - 处理：只执行测试和断言，不修改生产算法、金融语义或正式数据库。
# - 输出：可重复的通过/失败证据，供全量回归和任务验收使用。
# - 为什么这样写：把业务要求固化为自动测试，使后续注释迁移和重构能够证明行为未变化。
from __future__ import annotations

from datetime import date
import json
from pathlib import Path
import unittest

from a_stock_quant.data_contracts import (
    DataContractError,
    QualityStatus,
)
from a_stock_quant.data_readiness import (
    DataReadinessEngine,
    EvidenceStatus,
    ReadinessDimension,
    ReadinessEvidence,
    ReadinessStatus,
    load_data_readiness_policy,
)
from a_stock_quant.data_readiness_evidence import (
    EvidenceRuleConfig,
    StandardQueryEvidenceBuilder,
    StandardQueryReadinessService,
)
from a_stock_quant.readiness_gated_data_service import (
    READINESS_GATED_SERVICE_VERSION,
    ReadinessGatedStandardDataService,
)
from a_stock_quant.standard_data_service import (
    ProviderDescriptor,
    StandardDataQuery,
    StandardDataRecord,
    StandardDataService,
    StandardDataUsage,
    StandardDatasetProvider,
    StandardQueryMetadata,
    StandardQueryResult,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = (
    PROJECT_ROOT
    / "configs"
    / "quality"
    / "data_readiness_policy_v0.json"
)


# 测试类 `FakeProvider`：集中验证 `test_readiness_gated_data_service` 相关合同、边界条件和回归行为。
# - 输入：测试夹具、构造样例以及被测模块公开接口。
# - 处理：按独立场景组织断言，覆盖正常路径、失败门禁和关键边界。
# - 输出：通过或失败的单元测试结果，不产生正式业务数据。
# - 为什么这样写：把同一职责的回归场景集中管理，便于定位失败并防止后续修改破坏既有合同。
class FakeProvider(StandardDatasetProvider):
    # 测试函数 `__init__`：封装 `__init__` 测试辅助步骤，减少重复样例和断言准备。
    # - 输入：status、blocks_downstream、warnings。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def __init__(
        self,
        *,
        status: QualityStatus = QualityStatus.PASSED,
        blocks_downstream: bool = False,
        warnings: tuple[str, ...] = (),
    ) -> None:
        self.status = status
        self.blocks_downstream = blocks_downstream
        self.warnings = warnings

    # 测试函数 `descriptor`：封装 `descriptor` 测试辅助步骤，减少重复样例和断言准备。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    @property
    def descriptor(self) -> ProviderDescriptor:
        return ProviderDescriptor(
            provider_id="dolphindb_daily_k_standard_provider",
            dataset_id="a_stock_daily_k",
            supported_objects=("DailyBar",),
            coverage_version="daily-k@2026-05-29",
            mapping_version="test-mapping",
            dictionary_revision="0.6.0",
        )

    # 测试函数 `query`：封装 `query` 测试辅助步骤，减少重复样例和断言准备。
    # - 输入：request。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def query(
        self,
        request: StandardDataQuery,
    ) -> StandardQueryResult:
        record = StandardDataRecord(
            canonical_object="DailyBar",
            primary_key={
                "instrument_id": request.instrument_ids[0],
                "trade_date": request.end_date,
            },
            values={
                "instrument_id": request.instrument_ids[0],
                "trade_date": request.end_date,
                "close": 10.0,
            },
            source_record_id=(
                f"{request.instrument_ids[0]}|"
                f"{request.end_date.isoformat()}"
            ),
            lineage=(
                {
                    "target_object": "DailyBar",
                    "canonical_field": "close",
                    "source_fields": ["close"],
                    "transform_id": "identity",
                },
            ),
        )
        return StandardQueryResult(
            query=request,
            metadata=StandardQueryMetadata(
                dataset_id=request.dataset_id,
                canonical_object=request.canonical_object,
                provider_id=self.descriptor.provider_id,
                coverage_version=self.descriptor.coverage_version,
                mapping_version=self.descriptor.mapping_version,
                dictionary_revision=self.descriptor.dictionary_revision,
                source_row_count=1,
                result_count=1,
                status=self.status,
                blocks_downstream=self.blocks_downstream,
                warnings=self.warnings,
                lineage_item_count=1,
            ),
            records=(record,),
        )


# 测试类 `FixedEvidenceBuilder`：集中验证 `test_readiness_gated_data_service` 相关合同、边界条件和回归行为。
# - 输入：测试夹具、构造样例以及被测模块公开接口。
# - 处理：按独立场景组织断言，覆盖正常路径、失败门禁和关键边界。
# - 输出：通过或失败的单元测试结果，不产生正式业务数据。
# - 为什么这样写：把同一职责的回归场景集中管理，便于定位失败并防止后续修改破坏既有合同。
class FixedEvidenceBuilder(StandardQueryEvidenceBuilder):
    # 测试函数 `__init__`：封装 `__init__` 测试辅助步骤，减少重复样例和断言准备。
    # - 输入：overrides。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def __init__(
        self,
        overrides: dict[
            ReadinessDimension,
            EvidenceStatus,
        ] | None = None,
    ) -> None:
        super().__init__(
            EvidenceRuleConfig(
                rules_version="test-rules",
                entity_key_candidates=("instrument_id",),
                date_field_candidates=("trade_date",),
                temporal_warning_markers=("TEMPORAL",),
            )
        )
        self.overrides = overrides or {}

    # 测试函数 `build`：封装 `build` 测试辅助步骤，减少重复样例和断言准备。
    # - 输入：result、descriptor、context。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def build(
        self,
        result: StandardQueryResult,
        descriptor: ProviderDescriptor,
        context=None,
    ) -> tuple[ReadinessEvidence, ...]:
        evidence: list[ReadinessEvidence] = []
        # 参数化循环：逐项使用 `ReadinessDimension` 验证同一合同。
        # - 处理：每轮保留原样例、顺序和断言，便于定位具体失败项。
        # - 为什么这样写：用一致规则覆盖多组输入，减少复制测试并提高边界覆盖率。
        for dimension in ReadinessDimension:
            status = self.overrides.get(
                dimension,
                EvidenceStatus.PASSED,
            )
            evidence.append(
                ReadinessEvidence(
                    dimension=dimension,
                    status=status,
                    code=(
                        "TEST_PASSED"
                        if status is EvidenceStatus.PASSED
                        else "TEST_WARNING"
                    ),
                    message="门禁组合测试证据。",
                    evidence_refs=(
                        f"query:{result.metadata.query_id}",
                    ),
                )
            )
        return tuple(evidence)


# 测试类 `ReadinessGatedServiceTests`：集中验证 `test_readiness_gated_data_service` 相关合同、边界条件和回归行为。
# - 输入：测试夹具、构造样例以及被测模块公开接口。
# - 处理：按独立场景组织断言，覆盖正常路径、失败门禁和关键边界。
# - 输出：通过或失败的单元测试结果，不产生正式业务数据。
# - 为什么这样写：把同一职责的回归场景集中管理，便于定位失败并防止后续修改破坏既有合同。
class ReadinessGatedServiceTests(unittest.TestCase):
    # 测试函数 `request`：封装 `request` 测试辅助步骤，减少重复样例和断言准备。
    # - 输入：usage。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def request(
        self,
        usage: StandardDataUsage = (
            StandardDataUsage.CURRENT_SNAPSHOT_RESEARCH
        ),
    ) -> StandardDataQuery:
        return StandardDataQuery(
            dataset_id="a_stock_daily_k",
            canonical_object="DailyBar",
            instrument_ids=("000001",),
            start_date=date(2026, 5, 29),
            end_date=date(2026, 5, 29),
            as_of_date=date(2026, 6, 27),
            usage=usage,
        )

    # 测试函数 `service`：封装 `service` 测试辅助步骤，减少重复样例和断言准备。
    # - 输入：provider、builder。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def service(
        self,
        *,
        provider: FakeProvider | None = None,
        builder: FixedEvidenceBuilder | None = None,
    ) -> ReadinessGatedStandardDataService:
        standard = StandardDataService()
        standard.register_provider(provider or FakeProvider())
        readiness = StandardQueryReadinessService(
            DataReadinessEngine(
                load_data_readiness_policy(POLICY_PATH)
            ),
            builder or FixedEvidenceBuilder(),
        )
        return ReadinessGatedStandardDataService(
            standard,
            readiness,
        )

    # 测试函数 `test_all_passed_is_usable`：验证 `all、passed、is、usable` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_all_passed_is_usable(self) -> None:
        result = self.service().query(self.request())
        self.assertFalse(result.blocks_downstream)
        self.assertEqual(
            result.readiness_snapshot.decision.status,
            ReadinessStatus.PASSED,
        )
        result.assert_usable()

    # 测试函数 `test_current_research_warning_is_usable`：验证 `current、research、warning、is、usable` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_current_research_warning_is_usable(self) -> None:
        service = self.service(
            builder=FixedEvidenceBuilder(
                {
                    ReadinessDimension.SEMANTIC_CONFIDENCE:
                    EvidenceStatus.WARNING,
                }
            )
        )
        result = service.query(self.request())
        self.assertFalse(result.blocks_downstream)
        self.assertEqual(
            result.readiness_snapshot.decision.status,
            ReadinessStatus.WARNING,
        )
        result.assert_usable()

    # 测试函数 `test_strict_historical_warning_is_blocked`：验证 `strict、historical、warning、is、blocked` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_strict_historical_warning_is_blocked(self) -> None:
        service = self.service(
            builder=FixedEvidenceBuilder(
                {
                    ReadinessDimension.SEMANTIC_CONFIDENCE:
                    EvidenceStatus.WARNING,
                }
            )
        )
        result = service.query(
            self.request(
                StandardDataUsage.STRICT_HISTORICAL_BACKTEST
            )
        )
        self.assertTrue(result.blocks_downstream)
        self.assertEqual(
            result.readiness_snapshot.decision.status,
            ReadinessStatus.BLOCKED,
        )
        # 测试上下文：通过 `self.assertRaises(DataContractError)` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
        with self.assertRaises(DataContractError):
            result.assert_usable()

    # 测试函数 `test_provider_block_cannot_be_bypassed`：验证 `provider、block、cannot、be、bypassed` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_provider_block_cannot_be_bypassed(self) -> None:
        service = self.service(
            provider=FakeProvider(
                status=QualityStatus.FAILED,
                blocks_downstream=True,
                warnings=("provider blocked",),
            )
        )
        result = service.query(self.request())
        self.assertTrue(result.blocks_downstream)
        # 测试上下文：通过 `self.assertRaises(DataContractError)` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
        with self.assertRaises(DataContractError):
            result.assert_usable()

    # 测试函数 `test_readiness_failure_cannot_be_bypassed`：验证 `readiness、failure、cannot、be、bypassed` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_readiness_failure_cannot_be_bypassed(self) -> None:
        service = self.service(
            builder=FixedEvidenceBuilder(
                {
                    ReadinessDimension.LINEAGE:
                    EvidenceStatus.FAILED,
                }
            )
        )
        result = service.query(self.request())
        self.assertTrue(result.blocks_downstream)
        # 测试上下文：通过 `self.assertRaises(DataContractError)` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
        with self.assertRaises(DataContractError):
            result.assert_usable()

    # 测试函数 `test_query_id_is_preserved`：验证 `query、id、is、preserved` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_query_id_is_preserved(self) -> None:
        result = self.service().query(self.request())
        self.assertEqual(
            result.standard_result.metadata.query_id,
            result.readiness_snapshot.query_id,
        )

    # 测试函数 `test_provider_id_is_preserved`：验证 `provider、id、is、preserved` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_provider_id_is_preserved(self) -> None:
        result = self.service().query(self.request())
        self.assertEqual(
            result.standard_result.metadata.provider_id,
            result.readiness_snapshot.provider_id,
        )

    # 测试函数 `test_to_dict_is_json_serialisable`：验证 `to、dict、is、json、serialisable` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_to_dict_is_json_serialisable(self) -> None:
        result = self.service().query(self.request())
        payload = result.to_dict()
        json.dumps(payload, ensure_ascii=False)
        self.assertEqual(
            payload["service_version"],
            READINESS_GATED_SERVICE_VERSION,
        )
        self.assertFalse(payload["blocks_downstream"])

    # 测试函数 `test_wrong_standard_service_type_is_rejected`：验证 `wrong、standard、service、type、is、rejected` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_wrong_standard_service_type_is_rejected(self) -> None:
        readiness = StandardQueryReadinessService(
            DataReadinessEngine(
                load_data_readiness_policy(POLICY_PATH)
            ),
            FixedEvidenceBuilder(),
        )
        # 测试上下文：通过 `self.assertRaises(DataContractError)` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
        with self.assertRaises(DataContractError):
            ReadinessGatedStandardDataService(
                object(),  # type: ignore[arg-type]
                readiness,
            )

    # 测试函数 `test_wrong_readiness_service_type_is_rejected`：验证 `wrong、readiness、service、type、is、rejected` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_wrong_readiness_service_type_is_rejected(self) -> None:
        standard = StandardDataService()
        # 测试上下文：通过 `self.assertRaises(DataContractError)` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
        with self.assertRaises(DataContractError):
            ReadinessGatedStandardDataService(
                standard,
                object(),  # type: ignore[arg-type]
            )


if __name__ == "__main__":
    unittest.main()
