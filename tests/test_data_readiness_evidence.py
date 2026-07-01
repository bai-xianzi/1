# 测试模块总览：验证 `test_data_readiness_evidence` 对应功能的合同、边界和历史回归行为。
# - 输入：构造样例、测试夹具、临时文件以及被测模块公开接口。
# - 处理：只执行测试和断言，不修改生产算法、金融语义或正式数据库。
# - 输出：可重复的通过/失败证据，供全量回归和任务验收使用。
# - 为什么这样写：把业务要求固化为自动测试，使后续注释迁移和重构能够证明行为未变化。
from __future__ import annotations

from datetime import date, datetime, timezone
import json
from pathlib import Path
import unittest

from a_stock_quant.data_contracts import DataContractError, QualityStatus
from a_stock_quant.data_readiness import (
    DataReadinessEngine,
    EvidenceStatus,
    ReadinessDimension,
    ReadinessStatus,
    load_data_readiness_policy,
)
from a_stock_quant.data_readiness_evidence import (
    EvidenceBuildContext,
    StandardQueryEvidenceBuilder,
    StandardQueryReadinessService,
    load_evidence_rule_config,
)
from a_stock_quant.standard_data_service import (
    ProviderDescriptor,
    StandardDataQuery,
    StandardDataRecord,
    StandardDataUsage,
    StandardQueryMetadata,
    StandardQueryResult,
)

ROOT = Path(__file__).resolve().parents[1]
RULES = ROOT / 'configs/quality/data_readiness_evidence_rules_v0.json'
POLICY = ROOT / 'configs/quality/data_readiness_policy_v0.json'


# 测试函数 `descriptor`：封装 `descriptor` 测试辅助步骤，减少重复样例和断言准备。
# - 输入：dataset_id、provider_id。
# - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
# - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
# - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
def descriptor(dataset_id: str = 'a_stock_daily_k', provider_id: str = 'provider') -> ProviderDescriptor:
    return ProviderDescriptor(provider_id, dataset_id, ('DailyBar',), 'coverage-v1', 'mapping-v1', '0.6.0')


# 测试函数 `result`：封装 `result` 测试辅助步骤，减少重复样例和断言准备。
# - 输入：status、blocks、records、warnings、as_of、usage、provider_id。
# - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
# - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
# - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
def result(*, status: QualityStatus = QualityStatus.PASSED, blocks: bool = False, records: tuple[StandardDataRecord, ...] | None = None, warnings: tuple[str, ...] = (), as_of: date | None = date(2026, 6, 27), usage: StandardDataUsage = StandardDataUsage.CURRENT_SNAPSHOT_RESEARCH, provider_id: str = 'provider') -> StandardQueryResult:
    # 测试分支：根据 `records is None` 选择对应断言或样例路径。
    # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
    # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
    if records is None:
        records = (StandardDataRecord('DailyBar', {'instrument_id':'000001','trade_date':date(2026,6,27)}, {'instrument_id':'000001','trade_date':date(2026,6,27),'close_raw_cny':10.0}, 'source:1', {}, (), ({'canonical_field':'close_raw_cny','source_fields':['close']},)),)
    q = StandardDataQuery('a_stock_daily_k','DailyBar',('000001',),date(2026,6,27),date(2026,6,27),as_of_date=as_of,usage=usage,decision_time=(datetime(2026,6,27,15,0,tzinfo=timezone.utc) if usage is StandardDataUsage.MANUAL_DECISION_SUPPORT else None))
    m = StandardQueryMetadata('a_stock_daily_k','DailyBar',provider_id,'coverage-v1','mapping-v1','0.6.0',len(records),len(records),status,blocks,warnings,{},sum(len(r.lineage) for r in records))
    return StandardQueryResult(q,m,records)


# 测试类 `EvidenceAdapterTests`：集中验证 `test_data_readiness_evidence` 相关合同、边界条件和回归行为。
# - 输入：测试夹具、构造样例以及被测模块公开接口。
# - 处理：按独立场景组织断言，覆盖正常路径、失败门禁和关键边界。
# - 输出：通过或失败的单元测试结果，不产生正式业务数据。
# - 为什么这样写：把同一职责的回归场景集中管理，便于定位失败并防止后续修改破坏既有合同。
class EvidenceAdapterTests(unittest.TestCase):
    # 测试函数 `setUp`：准备本组测试共享的对象、样例和环境状态。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def setUp(self) -> None:
        self.rules = load_evidence_rule_config(RULES)
        self.builder = StandardQueryEvidenceBuilder(self.rules)
        self.engine = DataReadinessEngine(load_data_readiness_policy(POLICY))
        self.service = StandardQueryReadinessService(self.engine, self.builder)

    # 测试函数 `evidence`：封装 `evidence` 测试辅助步骤，减少重复样例和断言准备。
    # - 输入：dimension、source、context。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def evidence(self, dimension: ReadinessDimension, *, source=None, context=None):
        items = self.builder.build(source or result(), descriptor(), context)
        return next(x for x in items if x.dimension is dimension)

    # 测试函数 `test_contract_passes_when_versions_match`：验证 `contract、passes、when、versions、match` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_contract_passes_when_versions_match(self):
        self.assertEqual(self.evidence(ReadinessDimension.CONTRACT).status, EvidenceStatus.PASSED)

    # 测试函数 `test_contract_mismatch_fails`：验证 `contract、mismatch、fails` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_contract_mismatch_fails(self):
        e = self.evidence(ReadinessDimension.CONTRACT, source=result(provider_id='other'))
        self.assertEqual(e.status, EvidenceStatus.FAILED)

    # 测试函数 `test_query_warning_maps_to_warning`：验证 `query、warning、maps、to、warning` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_query_warning_maps_to_warning(self):
        e = self.evidence(ReadinessDimension.QUERY_EXECUTION, source=result(status=QualityStatus.WARNING))
        self.assertEqual(e.status, EvidenceStatus.WARNING)

    # 测试函数 `test_blocked_query_maps_to_failed`：验证 `blocked、query、maps、to、failed` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_blocked_query_maps_to_failed(self):
        e = self.evidence(ReadinessDimension.QUERY_EXECUTION, source=result(status=QualityStatus.FAILED, blocks=True))
        self.assertEqual(e.status, EvidenceStatus.FAILED)

    # 测试函数 `test_empty_result_fails_coverage`：验证 `empty、result、fails、coverage` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_empty_result_fails_coverage(self):
        e = self.evidence(ReadinessDimension.COVERAGE, source=result(records=()))
        self.assertEqual(e.status, EvidenceStatus.FAILED)

    # 测试函数 `test_query_scope_coverage_is_warning`：验证 `query、scope、coverage、is、warning` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_query_scope_coverage_is_warning(self):
        e = self.evidence(ReadinessDimension.COVERAGE)
        self.assertEqual(e.status, EvidenceStatus.WARNING)
        self.assertEqual(e.code, 'QUERY_SCOPE_COVERAGE_ONLY')

    # 测试函数 `test_proven_coverage_passes`：验证 `proven、coverage、passes` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_proven_coverage_passes(self):
        e = self.evidence(ReadinessDimension.COVERAGE, context=EvidenceBuildContext(coverage_scope_proven=True))
        self.assertEqual(e.status, EvidenceStatus.PASSED)

    # 测试函数 `test_partial_coverage_warns`：验证 `partial、coverage、warns` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_partial_coverage_warns(self):
        e = self.evidence(ReadinessDimension.COVERAGE, context=EvidenceBuildContext(expected_entity_count=2, observed_entity_count=1, coverage_scope_proven=True))
        self.assertEqual(e.status, EvidenceStatus.WARNING)

    # 测试函数 `test_query_scope_freshness_is_warning`：验证 `query、scope、freshness、is、warning` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_query_scope_freshness_is_warning(self):
        e = self.evidence(ReadinessDimension.FRESHNESS)
        self.assertEqual(e.status, EvidenceStatus.WARNING)

    # 测试函数 `test_proven_freshness_passes`：验证 `proven、freshness、passes` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_proven_freshness_passes(self):
        e = self.evidence(ReadinessDimension.FRESHNESS, context=EvidenceBuildContext(expected_through_date=date(2026,6,27),latest_available_date=date(2026,6,27),freshness_scope_proven=True))
        self.assertEqual(e.status, EvidenceStatus.PASSED)

    # 测试函数 `test_stale_freshness_warns`：验证 `stale、freshness、warns` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_stale_freshness_warns(self):
        e = self.evidence(ReadinessDimension.FRESHNESS, context=EvidenceBuildContext(expected_through_date=date(2026,6,27),latest_available_date=date(2026,6,25),freshness_scope_proven=True))
        self.assertEqual(e.status, EvidenceStatus.WARNING)

    # 测试函数 `test_complete_lineage_passes`：验证 `complete、lineage、passes` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_complete_lineage_passes(self):
        self.assertEqual(self.evidence(ReadinessDimension.LINEAGE).status, EvidenceStatus.PASSED)

    # 测试函数 `test_missing_lineage_fails`：验证 `missing、lineage、fails` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_missing_lineage_fails(self):
        r = StandardDataRecord('DailyBar', {'instrument_id':'000001','trade_date':date(2026,6,27)}, {'instrument_id':'000001','trade_date':date(2026,6,27)}, None, {}, (), ())
        self.assertEqual(self.evidence(ReadinessDimension.LINEAGE, source=result(records=(r,))).status, EvidenceStatus.FAILED)

    # 测试函数 `test_as_of_boundary_passes_temporal`：验证 `as、of、boundary、passes、temporal` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_as_of_boundary_passes_temporal(self):
        self.assertEqual(self.evidence(ReadinessDimension.TEMPORAL_SAFETY).status, EvidenceStatus.PASSED)

    # 测试函数 `test_temporal_warning_marker_warns`：验证 `temporal、warning、marker、warns` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_temporal_warning_marker_warns(self):
        e = self.evidence(ReadinessDimension.TEMPORAL_SAFETY, source=result(warnings=('SOURCE_SNAPSHOT_TIME_UNAVAILABLE',)))
        self.assertEqual(e.status, EvidenceStatus.WARNING)

    # 测试函数 `test_explicit_temporal_unknown_is_used`：验证 `explicit、temporal、unknown、is、used` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_explicit_temporal_unknown_is_used(self):
        e = self.evidence(ReadinessDimension.TEMPORAL_SAFETY, context=EvidenceBuildContext(temporal_status=EvidenceStatus.UNKNOWN))
        self.assertEqual(e.status, EvidenceStatus.UNKNOWN)

    # 测试函数 `test_quality_flag_warns_semantic`：验证 `quality、flag、warns、semantic` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_quality_flag_warns_semantic(self):
        rec = result().records[0]
        flagged = StandardDataRecord(rec.canonical_object, rec.primary_key, rec.values, rec.source_record_id, {}, ('UNIT_UNCONFIRMED',), rec.lineage)
        self.assertEqual(self.evidence(ReadinessDimension.SEMANTIC_CONFIDENCE, source=result(records=(flagged,))).status, EvidenceStatus.WARNING)

    # 测试函数 `test_clean_semantics_pass`：验证 `clean、semantics、pass` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_clean_semantics_pass(self):
        self.assertEqual(self.evidence(ReadinessDimension.SEMANTIC_CONFIDENCE).status, EvidenceStatus.PASSED)

    # 测试函数 `test_unverified_activation_warns`：验证 `unverified、activation、warns` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_unverified_activation_warns(self):
        self.assertEqual(self.evidence(ReadinessDimension.ACTIVATION).status, EvidenceStatus.WARNING)

    # 测试函数 `test_verified_activation_passes`：验证 `verified、activation、passes` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_verified_activation_passes(self):
        e = self.evidence(ReadinessDimension.ACTIVATION, context=EvidenceBuildContext(activation_verified=True))
        self.assertEqual(e.status, EvidenceStatus.PASSED)

    # 测试函数 `test_current_snapshot_is_warning_but_usable`：验证 `current、snapshot、is、warning、but、usable` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_current_snapshot_is_warning_but_usable(self):
        snap = self.service.assess(result(), descriptor())
        self.assertEqual(snap.decision.status, ReadinessStatus.WARNING)
        self.assertFalse(snap.decision.blocks_downstream)
        snap.assert_usable()

    # 测试函数 `test_strict_historical_is_blocked_by_unproven_scope`：验证 `strict、historical、is、blocked、by、unproven、scope` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_strict_historical_is_blocked_by_unproven_scope(self):
        snap = self.service.assess(result(usage=StandardDataUsage.STRICT_HISTORICAL_BACKTEST), descriptor())
        self.assertEqual(snap.decision.status, ReadinessStatus.BLOCKED)
        # 测试上下文：通过 `self.assertRaises(DataContractError)` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
        with self.assertRaises(DataContractError): snap.assert_usable()

    # 测试函数 `test_all_external_evidence_can_pass`：验证 `all、external、evidence、can、pass` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_all_external_evidence_can_pass(self):
        ctx = EvidenceBuildContext(coverage_scope_proven=True,freshness_scope_proven=True,activation_verified=True,temporal_status=EvidenceStatus.PASSED,semantic_status=EvidenceStatus.PASSED)
        snap = self.service.assess(result(), descriptor(), ctx)
        self.assertEqual(snap.decision.status, ReadinessStatus.PASSED)

    # 测试函数 `test_snapshot_contains_eight_dimensions_and_serialises`：验证 `snapshot、contains、eight、dimensions、and、serialises` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_snapshot_contains_eight_dimensions_and_serialises(self):
        snap = self.service.assess(result(), descriptor())
        self.assertEqual(len(snap.evidence), 8)
        json.dumps(snap.to_dict(), ensure_ascii=False)


if __name__ == '__main__': unittest.main()
