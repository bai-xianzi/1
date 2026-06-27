"""统一数据质量门禁与数据就绪度合同。

本模块只定义来源无关的就绪度证据、用途级政策和确定性决策引擎。
它不连接数据库，不执行查询，也不替代数据集专属 Provider 的语义判断。

设计目标：
1. 把来源质量状态统一为 PASSED / WARNING / BLOCKED；
2. 对覆盖、时效、血缘、时点安全和语义置信度分别给出证据；
3. 同一份证据在不同用途下可以得到不同的准入结果；
4. 缺少关键证据时安全失败，禁止下游绕过门禁；
5. 为后续市场状态与风险仓位模块提供唯一的数据准入合同。
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timezone
from enum import Enum
import json
from pathlib import Path
from typing import Any, Iterable, Mapping
from uuid import uuid4

from .data_contracts import DataContractError
from .standard_data_service import StandardDataUsage

READINESS_CONTRACT_VERSION = "0.1.0"


class ReadinessStatus(str, Enum):
    """统一数据就绪度决策。"""

    PASSED = "PASSED"
    WARNING = "WARNING"
    BLOCKED = "BLOCKED"


class EvidenceStatus(str, Enum):
    """单项证据状态。"""

    PASSED = "PASSED"
    WARNING = "WARNING"
    FAILED = "FAILED"
    UNKNOWN = "UNKNOWN"


class ReadinessDimension(str, Enum):
    """统一数据就绪度维度。"""

    CONTRACT = "CONTRACT"
    QUERY_EXECUTION = "QUERY_EXECUTION"
    COVERAGE = "COVERAGE"
    FRESHNESS = "FRESHNESS"
    LINEAGE = "LINEAGE"
    TEMPORAL_SAFETY = "TEMPORAL_SAFETY"
    SEMANTIC_CONFIDENCE = "SEMANTIC_CONFIDENCE"
    ACTIVATION = "ACTIVATION"


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
        return {
            str(key): _json_safe(item)
            for key, item in value.items()
        }
    if isinstance(value, (tuple, list, set, frozenset)):
        return [_json_safe(item) for item in value]
    return value


@dataclass(frozen=True, slots=True)
class ReadinessEvidence:
    """一个就绪度维度的可审计证据。"""

    dimension: ReadinessDimension
    status: EvidenceStatus
    code: str
    message: str
    metrics: dict[str, Any] = field(default_factory=dict)
    evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        dimension = self.dimension
        if isinstance(dimension, str):
            try:
                dimension = ReadinessDimension(dimension)
            except ValueError as exc:
                raise DataContractError(
                    f"不支持的就绪度维度：{dimension}"
                ) from exc
        if not isinstance(dimension, ReadinessDimension):
            raise DataContractError(
                "dimension必须是ReadinessDimension。"
            )
        object.__setattr__(self, "dimension", dimension)

        status = self.status
        if isinstance(status, str):
            try:
                status = EvidenceStatus(status)
            except ValueError as exc:
                raise DataContractError(
                    f"不支持的证据状态：{status}"
                ) from exc
        if not isinstance(status, EvidenceStatus):
            raise DataContractError(
                "status必须是EvidenceStatus。"
            )
        object.__setattr__(self, "status", status)

        object.__setattr__(
            self,
            "code",
            _require_text(self.code, "code").upper(),
        )
        object.__setattr__(
            self,
            "message",
            _require_text(self.message, "message"),
        )
        if not isinstance(self.metrics, dict):
            raise DataContractError("metrics必须是字典。")
        refs = tuple(
            _require_text(item, "evidence_refs")
            for item in self.evidence_refs
        )
        if len(refs) != len(set(refs)):
            raise DataContractError(
                "evidence_refs不允许重复。"
            )
        object.__setattr__(self, "evidence_refs", refs)

    def to_dict(self) -> dict[str, Any]:
        return _json_safe(asdict(self))


@dataclass(frozen=True, slots=True)
class DatasetCatalogEntry:
    """统一就绪度政策覆盖的数据集目录项。"""

    dataset_id: str
    family: str
    provider_id: str
    selector_mode: str
    canonical_objects: tuple[str, ...]

    def __post_init__(self) -> None:
        for field_name in (
            "dataset_id",
            "family",
            "provider_id",
            "selector_mode",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_text(
                    getattr(self, field_name),
                    field_name,
                ),
            )
        selector_mode = self.selector_mode.upper()
        if selector_mode not in {
            "INSTRUMENT_ID",
            "ENTITY_ID",
        }:
            raise DataContractError(
                "selector_mode只支持INSTRUMENT_ID或ENTITY_ID。"
            )
        object.__setattr__(
            self,
            "selector_mode",
            selector_mode,
        )
        objects = tuple(
            _require_text(item, "canonical_objects")
            for item in self.canonical_objects
        )
        if not objects:
            raise DataContractError(
                "canonical_objects至少包含一个对象。"
            )
        if len(objects) != len(set(objects)):
            raise DataContractError(
                "canonical_objects不允许重复。"
            )
        object.__setattr__(
            self,
            "canonical_objects",
            objects,
        )

    def to_dict(self) -> dict[str, Any]:
        return _json_safe(asdict(self))


@dataclass(frozen=True, slots=True)
class UsageReadinessPolicy:
    """一个StandardDataUsage对应的门禁政策。"""

    usage: StandardDataUsage
    required_dimensions: tuple[ReadinessDimension, ...]
    blocked_statuses: dict[
        ReadinessDimension,
        frozenset[EvidenceStatus],
    ]

    def __post_init__(self) -> None:
        usage = self.usage
        if isinstance(usage, str):
            try:
                usage = StandardDataUsage(usage)
            except ValueError as exc:
                raise DataContractError(
                    f"不支持的数据用途：{usage}"
                ) from exc
        if not isinstance(usage, StandardDataUsage):
            raise DataContractError(
                "usage必须是StandardDataUsage。"
            )
        object.__setattr__(self, "usage", usage)

        dimensions: list[ReadinessDimension] = []
        for value in self.required_dimensions:
            try:
                dimension = (
                    value
                    if isinstance(value, ReadinessDimension)
                    else ReadinessDimension(value)
                )
            except ValueError as exc:
                raise DataContractError(
                    f"不支持的必需维度：{value}"
                ) from exc
            dimensions.append(dimension)
        if not dimensions:
            raise DataContractError(
                "required_dimensions不能为空。"
            )
        if len(dimensions) != len(set(dimensions)):
            raise DataContractError(
                "required_dimensions不允许重复。"
            )
        object.__setattr__(
            self,
            "required_dimensions",
            tuple(dimensions),
        )

        normalised: dict[
            ReadinessDimension,
            frozenset[EvidenceStatus],
        ] = {}
        for dimension in dimensions:
            raw_statuses = self.blocked_statuses.get(
                dimension,
                self.blocked_statuses.get(dimension.value),
            )
            if raw_statuses is None:
                raise DataContractError(
                    f"{usage.value}/{dimension.value}"
                    "缺少blocked_statuses。"
                )
            statuses: set[EvidenceStatus] = set()
            for value in raw_statuses:
                try:
                    status = (
                        value
                        if isinstance(value, EvidenceStatus)
                        else EvidenceStatus(value)
                    )
                except ValueError as exc:
                    raise DataContractError(
                        f"不支持的阻断证据状态：{value}"
                    ) from exc
                statuses.add(status)
            if EvidenceStatus.PASSED in statuses:
                raise DataContractError(
                    "PASSED不能被配置为阻断状态。"
                )
            normalised[dimension] = frozenset(statuses)
        object.__setattr__(
            self,
            "blocked_statuses",
            normalised,
        )


@dataclass(frozen=True, slots=True)
class DataReadinessPolicy:
    """完整就绪度政策。"""

    contract_version: str
    policy_version: str
    dataset_catalog: tuple[DatasetCatalogEntry, ...]
    usage_policies: dict[
        StandardDataUsage,
        UsageReadinessPolicy,
    ]
    raw_access_forbidden: bool = True
    standard_data_service_required: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "contract_version",
            _require_text(
                self.contract_version,
                "contract_version",
            ),
        )
        if self.contract_version != READINESS_CONTRACT_VERSION:
            raise DataContractError(
                "就绪度合同版本不兼容："
                f"{self.contract_version}"
            )
        object.__setattr__(
            self,
            "policy_version",
            _require_text(
                self.policy_version,
                "policy_version",
            ),
        )

        catalog = tuple(self.dataset_catalog)
        dataset_ids = [
            item.dataset_id
            for item in catalog
        ]
        if not catalog:
            raise DataContractError(
                "dataset_catalog不能为空。"
            )
        if len(dataset_ids) != len(set(dataset_ids)):
            raise DataContractError(
                "dataset_catalog中的dataset_id不允许重复。"
            )
        object.__setattr__(
            self,
            "dataset_catalog",
            catalog,
        )

        policies: dict[
            StandardDataUsage,
            UsageReadinessPolicy,
        ] = {}
        for usage in StandardDataUsage:
            policy = self.usage_policies.get(
                usage,
                self.usage_policies.get(usage.value),
            )
            if policy is None:
                raise DataContractError(
                    f"缺少用途政策：{usage.value}"
                )
            if policy.usage is not usage:
                raise DataContractError(
                    f"用途政策键值不一致：{usage.value}"
                )
            policies[usage] = policy
        object.__setattr__(
            self,
            "usage_policies",
            policies,
        )

    def dataset(self, dataset_id: str) -> DatasetCatalogEntry:
        key = _require_text(dataset_id, "dataset_id")
        for item in self.dataset_catalog:
            if item.dataset_id == key:
                return item
        raise DataContractError(
            f"就绪度政策未登记数据集：{key}"
        )

    def usage_policy(
        self,
        usage: StandardDataUsage,
    ) -> UsageReadinessPolicy:
        resolved = usage
        if isinstance(resolved, str):
            try:
                resolved = StandardDataUsage(resolved)
            except ValueError as exc:
                raise DataContractError(
                    f"不支持的数据用途：{usage}"
                ) from exc
        try:
            return self.usage_policies[resolved]
        except KeyError as exc:
            raise DataContractError(
                f"缺少用途政策：{resolved}"
            ) from exc


@dataclass(frozen=True, slots=True)
class DataReadinessRequest:
    """数据集级就绪度评估请求。"""

    dataset_id: str
    usage: StandardDataUsage
    evidence: tuple[ReadinessEvidence, ...]
    as_of_date: date | None = None
    decision_time: datetime | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "dataset_id",
            _require_text(self.dataset_id, "dataset_id"),
        )
        usage = self.usage
        if isinstance(usage, str):
            try:
                usage = StandardDataUsage(usage)
            except ValueError as exc:
                raise DataContractError(
                    f"不支持的数据用途：{usage}"
                ) from exc
        if not isinstance(usage, StandardDataUsage):
            raise DataContractError(
                "usage必须是StandardDataUsage。"
            )
        object.__setattr__(self, "usage", usage)

        evidence = tuple(self.evidence)
        dimensions = [
            item.dimension
            for item in evidence
        ]
        if len(dimensions) != len(set(dimensions)):
            raise DataContractError(
                "同一就绪度维度只能提供一项证据。"
            )
        object.__setattr__(self, "evidence", evidence)

        if (
            self.as_of_date is not None
            and not isinstance(self.as_of_date, date)
        ):
            raise DataContractError(
                "as_of_date必须是date。"
            )
        if self.decision_time is not None:
            if not isinstance(self.decision_time, datetime):
                raise DataContractError(
                    "decision_time必须是datetime。"
                )
            if (
                self.decision_time.tzinfo is None
                or self.decision_time.utcoffset() is None
            ):
                raise DataContractError(
                    "decision_time必须携带时区。"
                )
        if (
            usage
            is StandardDataUsage.MANUAL_DECISION_SUPPORT
            and self.decision_time is None
        ):
            raise DataContractError(
                "MANUAL_DECISION_SUPPORT必须提供decision_time。"
            )


@dataclass(frozen=True, slots=True)
class DimensionReadinessDecision:
    """单一维度的门禁结果。"""

    dimension: ReadinessDimension
    evidence_status: EvidenceStatus
    evidence_code: str
    message: str
    blocked: bool
    metrics: dict[str, Any] = field(default_factory=dict)
    evidence_refs: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return _json_safe(asdict(self))


@dataclass(frozen=True, slots=True)
class DatasetReadinessDecision:
    """数据集级统一就绪度结果。"""

    dataset_id: str
    usage: StandardDataUsage
    status: ReadinessStatus
    blocks_downstream: bool
    policy_version: str
    contract_version: str
    dimensions: tuple[DimensionReadinessDecision, ...]
    blocking_reasons: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    assessment_id: str = field(
        default_factory=lambda: str(uuid4())
    )
    generated_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    as_of_date: date | None = None
    decision_time: datetime | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "dataset_id",
            _require_text(self.dataset_id, "dataset_id"),
        )
        if (
            self.status is ReadinessStatus.BLOCKED
            and not self.blocks_downstream
        ):
            raise DataContractError(
                "BLOCKED决策必须阻断下游。"
            )
        if (
            self.status is not ReadinessStatus.BLOCKED
            and self.blocks_downstream
        ):
            raise DataContractError(
                "只有BLOCKED决策可以阻断下游。"
            )

    def assert_usable(self) -> None:
        if self.blocks_downstream:
            reasons = ", ".join(self.blocking_reasons)
            raise DataContractError(
                "数据集未通过统一数据就绪度门禁："
                f"{reasons}"
            )

    def to_dict(self) -> dict[str, Any]:
        return _json_safe(asdict(self))


class DataReadinessEngine:
    """基于政策和证据生成确定性的用途级就绪度决策。"""

    def __init__(self, policy: DataReadinessPolicy) -> None:
        self.policy = policy

    def evaluate(
        self,
        request: DataReadinessRequest,
    ) -> DatasetReadinessDecision:
        self.policy.dataset(request.dataset_id)
        usage_policy = self.policy.usage_policy(
            request.usage
        )
        evidence_by_dimension = {
            item.dimension: item
            for item in request.evidence
        }

        decisions: list[DimensionReadinessDecision] = []
        blocking_reasons: list[str] = []
        warnings: list[str] = []

        for dimension in usage_policy.required_dimensions:
            evidence = evidence_by_dimension.get(dimension)
            if evidence is None:
                evidence = ReadinessEvidence(
                    dimension=dimension,
                    status=EvidenceStatus.UNKNOWN,
                    code="EVIDENCE_MISSING",
                    message=(
                        "缺少必需的就绪度证据，"
                        "按安全失败处理。"
                    ),
                )

            blocked = (
                evidence.status
                in usage_policy.blocked_statuses[dimension]
            )
            decision = DimensionReadinessDecision(
                dimension=dimension,
                evidence_status=evidence.status,
                evidence_code=evidence.code,
                message=evidence.message,
                blocked=blocked,
                metrics=dict(evidence.metrics),
                evidence_refs=evidence.evidence_refs,
            )
            decisions.append(decision)

            reason = (
                f"{dimension.value}:{evidence.code}"
            )
            if blocked:
                blocking_reasons.append(reason)
            elif evidence.status is not EvidenceStatus.PASSED:
                warnings.append(reason)

        if blocking_reasons:
            status = ReadinessStatus.BLOCKED
        elif warnings:
            status = ReadinessStatus.WARNING
        else:
            status = ReadinessStatus.PASSED

        return DatasetReadinessDecision(
            dataset_id=request.dataset_id,
            usage=request.usage,
            status=status,
            blocks_downstream=(
                status is ReadinessStatus.BLOCKED
            ),
            policy_version=self.policy.policy_version,
            contract_version=self.policy.contract_version,
            dimensions=tuple(decisions),
            blocking_reasons=tuple(blocking_reasons),
            warnings=tuple(warnings),
            as_of_date=request.as_of_date,
            decision_time=request.decision_time,
        )


def _load_catalog(
    raw_items: Iterable[Mapping[str, Any]],
) -> tuple[DatasetCatalogEntry, ...]:
    return tuple(
        DatasetCatalogEntry(
            dataset_id=str(item["dataset_id"]),
            family=str(item["family"]),
            provider_id=str(item["provider_id"]),
            selector_mode=str(item["selector_mode"]),
            canonical_objects=tuple(
                str(value)
                for value in item["canonical_objects"]
            ),
        )
        for item in raw_items
    )


def _load_usage_policies(
    raw_policies: Mapping[str, Any],
) -> dict[StandardDataUsage, UsageReadinessPolicy]:
    policies: dict[
        StandardDataUsage,
        UsageReadinessPolicy,
    ] = {}
    for usage in StandardDataUsage:
        try:
            raw = raw_policies[usage.value]
        except KeyError as exc:
            raise DataContractError(
                f"配置缺少用途政策：{usage.value}"
            ) from exc
        required_dimensions = tuple(
            ReadinessDimension(value)
            for value in raw["required_dimensions"]
        )
        blocked_statuses = {
            ReadinessDimension(dimension): frozenset(
                EvidenceStatus(status)
                for status in statuses
            )
            for dimension, statuses
            in raw["blocked_statuses"].items()
        }
        policies[usage] = UsageReadinessPolicy(
            usage=usage,
            required_dimensions=required_dimensions,
            blocked_statuses=blocked_statuses,
        )
    return policies


def load_data_readiness_policy(
    path: str | Path,
) -> DataReadinessPolicy:
    """从JSON加载并验证统一数据就绪度政策。"""

    policy_path = Path(path)
    if not policy_path.exists():
        raise DataContractError(
            f"就绪度政策文件不存在：{policy_path}"
        )
    try:
        raw = json.loads(
            policy_path.read_text(encoding="utf-8")
        )
    except (OSError, json.JSONDecodeError) as exc:
        raise DataContractError(
            f"无法加载就绪度政策：{policy_path}"
        ) from exc
    if not isinstance(raw, dict):
        raise DataContractError(
            "就绪度政策根节点必须是对象。"
        )

    declared_dimensions = tuple(
        ReadinessDimension(value)
        for value in raw.get("dimensions", ())
    )
    if set(declared_dimensions) != set(ReadinessDimension):
        raise DataContractError(
            "政策声明的dimensions必须完整覆盖统一维度。"
        )
    if len(declared_dimensions) != len(
        set(declared_dimensions)
    ):
        raise DataContractError(
            "政策声明的dimensions不允许重复。"
        )

    decision_statuses = set(
        raw.get("decision_statuses", ())
    )
    if decision_statuses != {
        item.value
        for item in ReadinessStatus
    }:
        raise DataContractError(
            "decision_statuses必须完整覆盖"
            "PASSED/WARNING/BLOCKED。"
        )

    evidence_statuses = set(
        raw.get("evidence_statuses", ())
    )
    if evidence_statuses != {
        item.value
        for item in EvidenceStatus
    }:
        raise DataContractError(
            "evidence_statuses必须完整覆盖"
            "PASSED/WARNING/FAILED/UNKNOWN。"
        )

    access_policy = raw.get(
        "source_access_policy",
        {},
    )
    if not isinstance(access_policy, dict):
        raise DataContractError(
            "source_access_policy必须是对象。"
        )

    return DataReadinessPolicy(
        contract_version=str(raw["contract_version"]),
        policy_version=str(raw["policy_version"]),
        dataset_catalog=_load_catalog(
            raw["dataset_catalog"]
        ),
        usage_policies=_load_usage_policies(
            raw["usage_policies"]
        ),
        raw_access_forbidden=bool(
            access_policy.get(
                "raw_access_forbidden",
                True,
            )
        ),
        standard_data_service_required=bool(
            access_policy.get(
                "standard_data_service_required",
                True,
            )
        ),
    )
