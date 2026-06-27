"""StandardDataService查询结果到统一数据就绪度证据的适配层。

本模块只消费统一查询合同、Provider描述和显式补充上下文，生成八维证据与
DatasetReadinessDecision。它不连接数据库，不访问Raw表，也不替代Provider的
来源专属语义判断。
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timezone
from enum import Enum
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from .data_contracts import DataContractError, QualityStatus
from .data_readiness import (
    DataReadinessEngine,
    DataReadinessRequest,
    DatasetReadinessDecision,
    EvidenceStatus,
    ReadinessDimension,
    ReadinessEvidence,
)
from .standard_data_service import (
    ProviderDescriptor,
    StandardDataQuery,
    StandardDataRecord,
    StandardDataUsage,
    StandardQueryResult,
)

EVIDENCE_ADAPTER_VERSION = "0.1.0"


def _require_text(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DataContractError(f"{field_name}不能为空。")
    return value.strip()


def _json_safe(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Mapping):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (tuple, list, set, frozenset)):
        return [_json_safe(item) for item in value]
    return value


@dataclass(frozen=True, slots=True)
class EvidenceRuleConfig:
    """证据适配器的可维护规则。"""

    rules_version: str
    entity_key_candidates: tuple[str, ...]
    date_field_candidates: tuple[str, ...]
    temporal_warning_markers: tuple[str, ...]
    default_minimum_coverage_ratio: float = 1.0
    default_max_freshness_lag_days: int = 0
    coverage_scope_requires_external_evidence: bool = True
    freshness_scope_requires_external_evidence: bool = True
    activation_requires_external_verification: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, 'rules_version', _require_text(self.rules_version, 'rules_version'))
        for field_name in ('entity_key_candidates','date_field_candidates','temporal_warning_markers'):
            values = tuple(_require_text(v, field_name) for v in getattr(self, field_name))
            if not values or len(values) != len(set(values)):
                raise DataContractError(f'{field_name}不能为空或重复。')
            object.__setattr__(self, field_name, values)
        if not 0 < self.default_minimum_coverage_ratio <= 1:
            raise DataContractError('default_minimum_coverage_ratio必须在(0,1]。')
        if self.default_max_freshness_lag_days < 0:
            raise DataContractError('default_max_freshness_lag_days不能为负。')


@dataclass(frozen=True, slots=True)
class EvidenceBuildContext:
    """Provider查询结果以外的显式证据上下文。"""

    expected_entity_count: int | None = None
    observed_entity_count: int | None = None
    minimum_coverage_ratio: float | None = None
    coverage_scope_proven: bool = False
    expected_through_date: date | None = None
    latest_available_date: date | None = None
    max_freshness_lag_days: int | None = None
    freshness_scope_proven: bool = False
    stale_is_failure: bool = False
    temporal_status: EvidenceStatus | None = None
    temporal_code: str | None = None
    temporal_message: str | None = None
    semantic_status: EvidenceStatus | None = None
    semantic_code: str | None = None
    semantic_message: str | None = None
    activation_status: EvidenceStatus | None = None
    activation_code: str | None = None
    activation_message: str | None = None
    activation_verified: bool = False
    evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name in ('expected_entity_count','observed_entity_count','max_freshness_lag_days'):
            value = getattr(self, name)
            if value is not None and value < 0:
                raise DataContractError(f'{name}不能为负。')
        if self.minimum_coverage_ratio is not None and not 0 < self.minimum_coverage_ratio <= 1:
            raise DataContractError('minimum_coverage_ratio必须在(0,1]。')
        if self.latest_available_date and self.expected_through_date:
            if not isinstance(self.latest_available_date, date) or not isinstance(self.expected_through_date, date):
                raise DataContractError('新鲜度日期必须是date。')
        refs = tuple(_require_text(v, 'evidence_refs') for v in self.evidence_refs)
        if len(refs) != len(set(refs)):
            raise DataContractError('evidence_refs不允许重复。')
        object.__setattr__(self, 'evidence_refs', refs)


@dataclass(frozen=True, slots=True)
class DatasetReadinessSnapshot:
    """一次标准查询对应的可审计就绪度快照。"""

    dataset_id: str
    canonical_object: str
    provider_id: str
    query_id: str
    usage: StandardDataUsage
    adapter_version: str
    rules_version: str
    evidence: tuple[ReadinessEvidence, ...]
    decision: DatasetReadinessDecision
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        for name in ('dataset_id','canonical_object','provider_id','query_id','adapter_version','rules_version'):
            object.__setattr__(self, name, _require_text(getattr(self, name), name))
        if self.decision.dataset_id != self.dataset_id:
            raise DataContractError('快照与决策dataset_id不一致。')
        if self.decision.usage is not self.usage:
            raise DataContractError('快照与决策usage不一致。')
        dimensions = {item.dimension for item in self.evidence}
        if dimensions != set(ReadinessDimension):
            raise DataContractError('快照必须完整包含八个就绪度维度。')

    def assert_usable(self) -> None:
        self.decision.assert_usable()

    def to_dict(self) -> dict[str, Any]:
        return _json_safe(asdict(self))


def load_evidence_rule_config(path: str | Path) -> EvidenceRuleConfig:
    rule_path = Path(path)
    try:
        raw = json.loads(rule_path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as exc:
        raise DataContractError(f'无法加载证据规则：{rule_path}') from exc
    if not isinstance(raw, dict):
        raise DataContractError('证据规则根节点必须是对象。')
    return EvidenceRuleConfig(
        rules_version=str(raw['rules_version']),
        entity_key_candidates=tuple(raw['entity_key_candidates']),
        date_field_candidates=tuple(raw['date_field_candidates']),
        temporal_warning_markers=tuple(raw['temporal_warning_markers']),
        default_minimum_coverage_ratio=float(raw.get('default_minimum_coverage_ratio', 1.0)),
        default_max_freshness_lag_days=int(raw.get('default_max_freshness_lag_days', 0)),
        coverage_scope_requires_external_evidence=bool(raw.get('coverage_scope_requires_external_evidence', True)),
        freshness_scope_requires_external_evidence=bool(raw.get('freshness_scope_requires_external_evidence', True)),
        activation_requires_external_verification=bool(raw.get('activation_requires_external_verification', True)),
    )


class StandardQueryEvidenceBuilder:
    """把统一查询结果确定性地映射为八维证据。"""

    def __init__(self, rules: EvidenceRuleConfig) -> None:
        self.rules = rules

    def build(
        self,
        result: StandardQueryResult,
        descriptor: ProviderDescriptor,
        context: EvidenceBuildContext | None = None,
    ) -> tuple[ReadinessEvidence, ...]:
        ctx = context or EvidenceBuildContext()
        return (
            self._contract(result, descriptor, ctx),
            self._query_execution(result, ctx),
            self._coverage(result, ctx),
            self._freshness(result, ctx),
            self._lineage(result, ctx),
            self._temporal(result, ctx),
            self._semantic(result, ctx),
            self._activation(result, descriptor, ctx),
        )

    def _refs(self, result: StandardQueryResult, ctx: EvidenceBuildContext, *extra: str) -> tuple[str, ...]:
        refs = [f'query:{result.metadata.query_id}', f'provider:{result.metadata.provider_id}', *ctx.evidence_refs, *extra]
        return tuple(dict.fromkeys(refs))

    def _contract(self, result: StandardQueryResult, descriptor: ProviderDescriptor, ctx: EvidenceBuildContext) -> ReadinessEvidence:
        failures: list[str] = []
        pairs = (
            ('dataset_id', result.metadata.dataset_id, descriptor.dataset_id),
            ('provider_id', result.metadata.provider_id, descriptor.provider_id),
            ('coverage_version', result.metadata.coverage_version, descriptor.coverage_version),
            ('mapping_version', result.metadata.mapping_version, descriptor.mapping_version),
            ('dictionary_revision', result.metadata.dictionary_revision, descriptor.dictionary_revision),
        )
        for name, actual, expected in pairs:
            if actual != expected:
                failures.append(f'{name}:{actual}!={expected}')
        if result.query.canonical_object not in descriptor.supported_objects:
            failures.append('canonical_object_not_supported')
        if result.query.selector_mode != descriptor.selector_mode:
            failures.append('selector_mode_mismatch')
        status = EvidenceStatus.FAILED if failures else EvidenceStatus.PASSED
        return ReadinessEvidence(
            dimension=ReadinessDimension.CONTRACT,
            status=status,
            code='CONTRACT_MISMATCH' if failures else 'CONTRACT_MATCHED',
            message='统一查询合同与Provider描述不一致。' if failures else '统一查询合同、版本和Provider描述一致。',
            metrics={'failures': failures, 'supported_objects': list(descriptor.supported_objects), 'selector_mode': descriptor.selector_mode},
            evidence_refs=self._refs(result, ctx, f'coverage:{descriptor.coverage_version}', f'mapping:{descriptor.mapping_version}', f'dictionary:{descriptor.dictionary_revision}'),
        )

    def _query_execution(self, result: StandardQueryResult, ctx: EvidenceBuildContext) -> ReadinessEvidence:
        quality = result.metadata.status
        if result.metadata.blocks_downstream or quality is QualityStatus.FAILED:
            status, code = EvidenceStatus.FAILED, 'QUERY_BLOCKED'
        elif quality in {QualityStatus.WARNING, QualityStatus.PENDING_CONFIRMATION}:
            status, code = EvidenceStatus.WARNING, 'QUERY_COMPLETED_WITH_WARNINGS'
        else:
            status, code = EvidenceStatus.PASSED, 'QUERY_COMPLETED'
        return ReadinessEvidence(
            dimension=ReadinessDimension.QUERY_EXECUTION,
            status=status,
            code=code,
            message='标准查询已完成并生成结构化结果。' if status is not EvidenceStatus.FAILED else '标准查询结果被Provider质量门禁阻断。',
            metrics={'quality_status': quality.value, 'blocks_downstream': result.metadata.blocks_downstream, 'source_row_count': result.metadata.source_row_count, 'result_count': result.metadata.result_count},
            evidence_refs=self._refs(result, ctx),
        )

    def _entity_values(self, records: Iterable[StandardDataRecord]) -> set[str]:
        values: set[str] = set()
        for record in records:
            combined = {**record.values, **record.primary_key}
            for key in self.rules.entity_key_candidates:
                value = combined.get(key)
                if value is not None and str(value).strip():
                    values.add(str(value).strip())
                    break
        return values

    def _coverage(self, result: StandardQueryResult, ctx: EvidenceBuildContext) -> ReadinessEvidence:
        expected = ctx.expected_entity_count
        if expected is None:
            expected = len(result.query.selector_ids)
        observed = ctx.observed_entity_count
        if observed is None:
            observed = len(self._entity_values(result.records))
        ratio = 0.0 if expected == 0 else min(observed / expected, 1.0)
        threshold = ctx.minimum_coverage_ratio or self.rules.default_minimum_coverage_ratio
        metrics = {'expected_entity_count': expected, 'observed_entity_count': observed, 'coverage_ratio': ratio, 'minimum_coverage_ratio': threshold, 'scope_proven': ctx.coverage_scope_proven, 'result_count': result.metadata.result_count}
        if result.metadata.result_count == 0 or observed == 0:
            status, code, message = EvidenceStatus.FAILED, 'COVERAGE_EMPTY', '查询范围没有返回可用标准记录。'
        elif ratio < threshold:
            status, code, message = EvidenceStatus.WARNING, 'COVERAGE_BELOW_THRESHOLD', '查询实体覆盖低于阈值。'
        elif ctx.coverage_scope_proven or not self.rules.coverage_scope_requires_external_evidence:
            status, code, message = EvidenceStatus.PASSED, 'COVERAGE_PROVEN', '外部覆盖证据和查询结果满足阈值。'
        else:
            status, code, message = EvidenceStatus.WARNING, 'QUERY_SCOPE_COVERAGE_ONLY', '当前只能证明本次查询实体覆盖，尚不能证明数据集级完整覆盖。'
        return ReadinessEvidence(ReadinessDimension.COVERAGE, status, code, message, metrics, self._refs(result, ctx))

    @staticmethod
    def _as_date(value: Any) -> date | None:
        if isinstance(value, datetime): return value.date()
        if isinstance(value, date): return value
        if isinstance(value, str):
            try: return date.fromisoformat(value[:10])
            except ValueError: return None
        return None

    def _latest_record_date(self, records: Iterable[StandardDataRecord]) -> date | None:
        dates: list[date] = []
        for record in records:
            combined = {**record.values, **record.primary_key}
            for key in self.rules.date_field_candidates:
                parsed = self._as_date(combined.get(key))
                if parsed is not None:
                    dates.append(parsed)
        return max(dates) if dates else None

    def _freshness(self, result: StandardQueryResult, ctx: EvidenceBuildContext) -> ReadinessEvidence:
        latest = ctx.latest_available_date or self._latest_record_date(result.records)
        expected = ctx.expected_through_date or result.query.end_date
        limit = ctx.max_freshness_lag_days
        if limit is None: limit = self.rules.default_max_freshness_lag_days
        metrics: dict[str, Any] = {'latest_available_date': latest, 'expected_through_date': expected, 'max_freshness_lag_days': limit, 'scope_proven': ctx.freshness_scope_proven}
        if latest is None:
            status, code, message = EvidenceStatus.UNKNOWN, 'FRESHNESS_DATE_MISSING', '无法从结果或补充上下文确认最新可用日期。'
        elif latest > expected:
            status, code, message = EvidenceStatus.WARNING, 'FUTURE_DATED_OBSERVATION', '最新观测日期晚于期望截止日期，需要检查时点边界。'
            metrics['lag_days'] = (expected - latest).days
        else:
            lag = (expected - latest).days
            metrics['lag_days'] = lag
            if lag > limit:
                status = EvidenceStatus.FAILED if ctx.stale_is_failure else EvidenceStatus.WARNING
                code, message = 'FRESHNESS_STALE', '最新观测日期落后于允许阈值。'
            elif ctx.freshness_scope_proven or not self.rules.freshness_scope_requires_external_evidence:
                status, code, message = EvidenceStatus.PASSED, 'FRESHNESS_PROVEN', '外部时效证据证明数据达到期望截止日期。'
            else:
                status, code, message = EvidenceStatus.WARNING, 'QUERY_SCOPE_FRESHNESS_ONLY', '当前只能证明本次结果日期，尚不能证明数据集级最新状态。'
        return ReadinessEvidence(ReadinessDimension.FRESHNESS, status, code, message, metrics, self._refs(result, ctx))

    def _lineage(self, result: StandardQueryResult, ctx: EvidenceBuildContext) -> ReadinessEvidence:
        total = len(result.records)
        source_ids = sum(bool(r.source_record_id) for r in result.records)
        records_with_lineage = sum(bool(r.lineage) for r in result.records)
        calculated_items = sum(len(r.lineage) for r in result.records)
        metrics = {'record_count': total, 'source_record_id_count': source_ids, 'records_with_lineage': records_with_lineage, 'metadata_lineage_item_count': result.metadata.lineage_item_count, 'calculated_lineage_item_count': calculated_items}
        if total == 0 or source_ids == 0 or calculated_items == 0:
            status, code, message = EvidenceStatus.FAILED, 'LINEAGE_MISSING', '结果缺少来源记录标识或字段血缘。'
        elif source_ids < total or records_with_lineage < total or calculated_items != result.metadata.lineage_item_count:
            status, code, message = EvidenceStatus.WARNING, 'LINEAGE_PARTIAL', '部分记录血缘缺失或元数据计数不一致。'
        else:
            status, code, message = EvidenceStatus.PASSED, 'LINEAGE_COMPLETE', '所有标准记录均包含来源标识和字段血缘。'
        return ReadinessEvidence(ReadinessDimension.LINEAGE, status, code, message, metrics, self._refs(result, ctx, *(f'source:{r.source_record_id}' for r in result.records if r.source_record_id)))

    def _temporal_markers(self, result: StandardQueryResult) -> list[str]:
        texts = list(result.metadata.warnings)
        for record in result.records: texts.extend(record.quality_flags)
        markers: list[str] = []
        for text in texts:
            upper = text.upper()
            if any(marker in upper for marker in self.rules.temporal_warning_markers):
                markers.append(text)
        return list(dict.fromkeys(markers))

    def _explicit(self, dimension: ReadinessDimension, status: EvidenceStatus | None, code: str | None, message: str | None, result: StandardQueryResult, ctx: EvidenceBuildContext) -> ReadinessEvidence | None:
        if status is None: return None
        return ReadinessEvidence(dimension, status, code or f'{dimension.value}_EXPLICIT', message or '使用显式补充证据。', {}, self._refs(result, ctx))

    def _temporal(self, result: StandardQueryResult, ctx: EvidenceBuildContext) -> ReadinessEvidence:
        explicit = self._explicit(ReadinessDimension.TEMPORAL_SAFETY, ctx.temporal_status, ctx.temporal_code, ctx.temporal_message, result, ctx)
        if explicit: return explicit
        markers = self._temporal_markers(result)
        metrics = {'as_of_date': result.query.as_of_date, 'decision_time': result.query.decision_time, 'temporal_markers': markers}
        if result.metadata.blocks_downstream:
            status, code, message = EvidenceStatus.FAILED, 'PROVIDER_TEMPORAL_GATE_BLOCKED', 'Provider已阻断当前用途或时点。'
        elif markers:
            status, code, message = EvidenceStatus.WARNING, 'TEMPORAL_WARNING_PRESENT', '结果包含无法证明精确可见时间的警告。'
        elif result.query.as_of_date is not None:
            status, code, message = EvidenceStatus.PASSED, 'AS_OF_BOUNDARY_ENFORCED', '查询显式携带并通过as_of_date边界。'
        else:
            status, code, message = EvidenceStatus.UNKNOWN, 'TEMPORAL_EVIDENCE_MISSING', '查询未提供足够的时点安全证据。'
        return ReadinessEvidence(ReadinessDimension.TEMPORAL_SAFETY, status, code, message, metrics, self._refs(result, ctx))

    def _semantic(self, result: StandardQueryResult, ctx: EvidenceBuildContext) -> ReadinessEvidence:
        explicit = self._explicit(ReadinessDimension.SEMANTIC_CONFIDENCE, ctx.semantic_status, ctx.semantic_code, ctx.semantic_message, result, ctx)
        if explicit: return explicit
        flags: list[str] = []
        for record in result.records: flags.extend(record.quality_flags)
        flags = list(dict.fromkeys(flags))
        warnings = list(result.metadata.warnings)
        metrics = {'quality_flags': flags, 'warnings': warnings, 'quality_status': result.metadata.status.value}
        if result.metadata.status is QualityStatus.FAILED:
            status, code, message = EvidenceStatus.FAILED, 'SEMANTIC_PROVIDER_FAILED', 'Provider报告语义或质量失败。'
        elif flags or warnings or result.metadata.status in {QualityStatus.WARNING, QualityStatus.PENDING_CONFIRMATION}:
            status, code, message = EvidenceStatus.WARNING, 'SEMANTIC_WARNINGS_PRESENT', '标准结果仍包含来源语义或质量警告。'
        else:
            status, code, message = EvidenceStatus.PASSED, 'SEMANTIC_CHECKS_PASSED', 'Provider未报告语义警告。'
        return ReadinessEvidence(ReadinessDimension.SEMANTIC_CONFIDENCE, status, code, message, metrics, self._refs(result, ctx))

    def _activation(self, result: StandardQueryResult, descriptor: ProviderDescriptor, ctx: EvidenceBuildContext) -> ReadinessEvidence:
        explicit = self._explicit(ReadinessDimension.ACTIVATION, ctx.activation_status, ctx.activation_code, ctx.activation_message, result, ctx)
        if explicit: return explicit
        matched = descriptor.provider_id == result.metadata.provider_id and descriptor.dataset_id == result.metadata.dataset_id
        metrics = {'provider_registered': matched, 'activation_verified': ctx.activation_verified}
        if not matched:
            status, code, message = EvidenceStatus.FAILED, 'PROVIDER_REGISTRATION_MISMATCH', '查询结果与Provider登记不一致。'
        elif ctx.activation_verified or not self.rules.activation_requires_external_verification:
            status, code, message = EvidenceStatus.PASSED, 'DATASET_ACTIVATION_VERIFIED', '数据集和Provider启用状态已由外部配置确认。'
        else:
            status, code, message = EvidenceStatus.WARNING, 'PROVIDER_REGISTERED_ACTIVATION_UNVERIFIED', 'Provider已登记且可查询，但尚未由独立启用配置证明生产激活状态。'
        return ReadinessEvidence(ReadinessDimension.ACTIVATION, status, code, message, metrics, self._refs(result, ctx))


class StandardQueryReadinessService:
    """组合证据适配器和DataReadinessEngine生成就绪度快照。"""

    def __init__(self, engine: DataReadinessEngine, builder: StandardQueryEvidenceBuilder) -> None:
        self.engine = engine
        self.builder = builder

    def assess(self, result: StandardQueryResult, descriptor: ProviderDescriptor, context: EvidenceBuildContext | None = None) -> DatasetReadinessSnapshot:
        evidence = self.builder.build(result, descriptor, context)
        request = DataReadinessRequest(
            dataset_id=result.query.dataset_id,
            usage=result.query.usage,
            evidence=evidence,
            as_of_date=result.query.as_of_date,
            decision_time=result.query.decision_time,
        )
        decision = self.engine.evaluate(request)
        return DatasetReadinessSnapshot(
            dataset_id=result.query.dataset_id,
            canonical_object=result.query.canonical_object,
            provider_id=descriptor.provider_id,
            query_id=result.metadata.query_id,
            usage=result.query.usage,
            adapter_version=EVIDENCE_ADAPTER_VERSION,
            rules_version=self.builder.rules.rules_version,
            evidence=evidence,
            decision=decision,
        )
