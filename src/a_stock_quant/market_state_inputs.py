"""市场状态MVP输入合同与统一门禁后的输入装配。

TASK_019A只负责定义输入边界，不计算牛熊状态，不产生交易信号。
所有输入必须来自ReadinessGatedStandardDataService的组合结果。
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

from .data_contracts import DataContractError
from .standard_data_service import StandardDataUsage


MARKET_STATE_INPUT_CONTRACT_VERSION = "0.1.0"


class MarketStateFeatureFamily(str, Enum):
    TREND = "TREND"
    BREADTH = "BREADTH"
    LIQUIDITY = "LIQUIDITY"
    VOLATILITY = "VOLATILITY"
    SECTOR_DIFFUSION = "SECTOR_DIFFUSION"
    CAPITAL_FLOW = "CAPITAL_FLOW"
    AUCTION_CONFIRMATION = "AUCTION_CONFIRMATION"
    FUNDAMENTAL_CONTEXT = "FUNDAMENTAL_CONTEXT"


class MarketStateDatasetRole(str, Enum):
    PRIMARY = "PRIMARY"
    SUPPLEMENTAL = "SUPPLEMENTAL"
    OPTIONAL = "OPTIONAL"
    CONTEXT = "CONTEXT"


class MarketStateInputStatus(str, Enum):
    READY = "READY"
    READY_WITH_WARNINGS = "READY_WITH_WARNINGS"
    BLOCKED = "BLOCKED"


def _require_text(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DataContractError(f"{field_name}不能为空。")
    return value.strip()


def _normalise_texts(
    values: tuple[str, ...] | list[str],
    field_name: str,
    *,
    allow_empty: bool = False,
) -> tuple[str, ...]:
    result = tuple(_require_text(item, field_name) for item in values)
    if not allow_empty and not result:
        raise DataContractError(f"{field_name}不能为空。")
    if len(result) != len(set(result)):
        raise DataContractError(f"{field_name}不允许重复。")
    return result


def _enum_value(value: Any) -> str:
    if isinstance(value, Enum):
        return str(value.value)
    return str(value)


@dataclass(frozen=True, slots=True)
class MarketStateDatasetRequirement:
    dataset_id: str
    canonical_object: str
    selector_mode: str
    role: MarketStateDatasetRole
    required: bool
    allow_warning: bool
    feature_families: tuple[MarketStateFeatureFamily, ...]
    required_fields: tuple[str, ...]
    notes: str

    def __post_init__(self) -> None:
        for name in ("dataset_id", "canonical_object", "selector_mode", "notes"):
            object.__setattr__(self, name, _require_text(getattr(self, name), name))
        role = self.role
        if isinstance(role, str):
            role = MarketStateDatasetRole(role)
        object.__setattr__(self, "role", role)
        families = tuple(
            item if isinstance(item, MarketStateFeatureFamily)
            else MarketStateFeatureFamily(item)
            for item in self.feature_families
        )
        if len(families) != len(set(families)):
            raise DataContractError("feature_families不允许重复。")
        object.__setattr__(self, "feature_families", families)
        object.__setattr__(
            self,
            "required_fields",
            _normalise_texts(self.required_fields, "required_fields"),
        )
        mode = self.selector_mode.upper()
        if mode not in {"INSTRUMENT_ID", "ENTITY_ID"}:
            raise DataContractError("selector_mode不受支持。")
        object.__setattr__(self, "selector_mode", mode)


@dataclass(frozen=True, slots=True)
class MarketStateInputContract:
    contract_version: str
    task_id: str
    allowed_usage: StandardDataUsage
    output_scope: str
    manual_decision_allowed: bool
    official_market_state_allowed: bool
    required_feature_families: tuple[MarketStateFeatureFamily, ...]
    dataset_requirements: tuple[MarketStateDatasetRequirement, ...]
    hard_rules: tuple[str, ...]

    def __post_init__(self) -> None:
        for name in ("contract_version", "task_id", "output_scope"):
            object.__setattr__(self, name, _require_text(getattr(self, name), name))
        usage = self.allowed_usage
        if isinstance(usage, str):
            usage = StandardDataUsage(usage)
        if usage is not StandardDataUsage.CURRENT_SNAPSHOT_RESEARCH:
            raise DataContractError(
                "TASK_019A只允许CURRENT_SNAPSHOT_RESEARCH用途。"
            )
        object.__setattr__(self, "allowed_usage", usage)
        families = tuple(
            item if isinstance(item, MarketStateFeatureFamily)
            else MarketStateFeatureFamily(item)
            for item in self.required_feature_families
        )
        if not families or len(families) != len(set(families)):
            raise DataContractError("required_feature_families必须非空且唯一。")
        object.__setattr__(self, "required_feature_families", families)
        if not self.dataset_requirements:
            raise DataContractError("dataset_requirements不能为空。")
        ids = [item.dataset_id for item in self.dataset_requirements]
        if len(ids) != len(set(ids)):
            raise DataContractError("dataset_requirements存在重复dataset_id。")
        required_ids = {item.dataset_id for item in self.dataset_requirements if item.required}
        if "a_stock_daily_k" not in required_ids or "hy" not in required_ids:
            raise DataContractError("日K和行业快照必须是TASK_019A必需输入。")
        if self.manual_decision_allowed or self.official_market_state_allowed:
            raise DataContractError("TASK_019A不得开启人工决策或正式状态发布。")
        object.__setattr__(self, "hard_rules", _normalise_texts(self.hard_rules, "hard_rules"))

    def requirement(self, dataset_id: str) -> MarketStateDatasetRequirement:
        key = _require_text(dataset_id, "dataset_id")
        for item in self.dataset_requirements:
            if item.dataset_id == key:
                return item
        raise DataContractError(f"市场状态输入合同未登记数据集：{key}")


@dataclass(frozen=True, slots=True)
class MarketStateDatasetInputSummary:
    dataset_id: str
    canonical_object: str
    provider_id: str
    query_id: str
    result_count: int
    role: MarketStateDatasetRole
    feature_families: tuple[MarketStateFeatureFamily, ...]
    readiness_status: str
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name in ("dataset_id", "canonical_object", "provider_id", "query_id", "readiness_status"):
            object.__setattr__(self, name, _require_text(getattr(self, name), name))
        if self.result_count < 0:
            raise DataContractError("result_count不能为负。")
        object.__setattr__(self, "warnings", _normalise_texts(self.warnings, "warnings", allow_empty=True))


@dataclass(frozen=True, slots=True)
class MarketStateInputAssessment:
    status: MarketStateInputStatus
    contract_version: str
    usage: StandardDataUsage
    research_feature_build_allowed: bool
    manual_decision_allowed: bool
    official_market_state_allowed: bool
    dataset_summaries: tuple[MarketStateDatasetInputSummary, ...]
    missing_required_datasets: tuple[str, ...] = ()
    blocked_datasets: tuple[str, ...] = ()
    missing_feature_families: tuple[MarketStateFeatureFamily, ...] = ()
    warnings: tuple[str, ...] = ()

    @property
    def blocks_downstream(self) -> bool:
        return self.status is MarketStateInputStatus.BLOCKED

    def assert_research_usable(self) -> None:
        if self.blocks_downstream:
            details = ", ".join(
                (
                    *self.missing_required_datasets,
                    *self.blocked_datasets,
                    *(item.value for item in self.missing_feature_families),
                )
            )
            raise DataContractError(
                "市场状态研究输入未通过门禁：" + details
            )

    def to_dict(self) -> dict[str, Any]:
        def convert(value: Any) -> Any:
            if isinstance(value, Enum):
                return value.value
            if isinstance(value, tuple):
                return [convert(item) for item in value]
            if isinstance(value, list):
                return [convert(item) for item in value]
            if isinstance(value, dict):
                return {str(k): convert(v) for k, v in value.items()}
            return value
        return convert(asdict(self))


def load_market_state_input_contract(
    path: str | Path,
) -> MarketStateInputContract:
    contract_path = Path(path)
    try:
        raw = json.loads(contract_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DataContractError(
            f"无法加载市场状态输入合同：{contract_path}"
        ) from exc
    if not isinstance(raw, dict):
        raise DataContractError("市场状态输入合同根节点必须是对象。")
    requirements = tuple(
        MarketStateDatasetRequirement(
            dataset_id=str(item["dataset_id"]),
            canonical_object=str(item["canonical_object"]),
            selector_mode=str(item["selector_mode"]),
            role=MarketStateDatasetRole(str(item["role"])),
            required=bool(item["required"]),
            allow_warning=bool(item["allow_warning"]),
            feature_families=tuple(
                MarketStateFeatureFamily(str(value))
                for value in item["feature_families"]
            ),
            required_fields=tuple(str(value) for value in item["required_fields"]),
            notes=str(item["notes"]),
        )
        for item in raw["dataset_requirements"]
    )
    return MarketStateInputContract(
        contract_version=str(raw["contract_version"]),
        task_id=str(raw["task_id"]),
        allowed_usage=StandardDataUsage(str(raw["allowed_usage"])),
        output_scope=str(raw["output_scope"]),
        manual_decision_allowed=bool(raw["manual_decision_allowed"]),
        official_market_state_allowed=bool(raw["official_market_state_allowed"]),
        required_feature_families=tuple(
            MarketStateFeatureFamily(str(value))
            for value in raw["required_feature_families"]
        ),
        dataset_requirements=requirements,
        hard_rules=tuple(str(value) for value in raw["hard_rules"]),
    )


class MarketStateInputContractEngine:
    """验证统一门禁查询结果能否组成市场状态研究输入包。"""

    def __init__(self, contract: MarketStateInputContract) -> None:
        if not isinstance(contract, MarketStateInputContract):
            raise DataContractError("contract必须是MarketStateInputContract。")
        self.contract = contract

    @staticmethod
    def _validate_gated_shape(result: Any) -> None:
        required_attrs = (
            "standard_result",
            "readiness_snapshot",
            "assert_usable",
        )
        missing = [name for name in required_attrs if not hasattr(result, name)]
        if missing:
            raise DataContractError(
                "市场状态输入必须来自ReadinessGatedStandardDataService："
                + ", ".join(missing)
            )

    def evaluate(
        self,
        results: Mapping[str, Any],
    ) -> MarketStateInputAssessment:
        if not isinstance(results, Mapping):
            raise DataContractError("results必须是dataset_id到门禁结果的映射。")

        summaries: list[MarketStateDatasetInputSummary] = []
        missing_required: list[str] = []
        blocked: list[str] = []
        warnings: list[str] = []
        covered_families: set[MarketStateFeatureFamily] = set()

        for requirement in self.contract.dataset_requirements:
            result = results.get(requirement.dataset_id)
            if result is None:
                if requirement.required:
                    missing_required.append(requirement.dataset_id)
                continue

            try:
                self._validate_gated_shape(result)
                standard = result.standard_result
                snapshot = result.readiness_snapshot
                query = standard.query
                metadata = standard.metadata

                if query.dataset_id != requirement.dataset_id:
                    raise DataContractError("dataset_id与输入合同不一致。")
                if query.canonical_object != requirement.canonical_object:
                    raise DataContractError("canonical_object与输入合同不一致。")
                if query.usage is not self.contract.allowed_usage:
                    raise DataContractError("市场状态输入用途不受允许。")
                if metadata.result_count <= 0 and requirement.required:
                    raise DataContractError("必需数据集查询结果为空。")

                result.assert_usable()

                readiness_status = _enum_value(snapshot.decision.status)
                item_warnings = list(metadata.warnings)
                item_warnings.extend(snapshot.decision.warnings)

                if readiness_status != "PASSED":
                    item_warnings.append(
                        f"READINESS_STATUS:{readiness_status}"
                    )
                item_warnings = list(dict.fromkeys(item_warnings))

                if item_warnings and not requirement.allow_warning:
                    raise DataContractError("该数据集合同不允许WARNING。")

                covered_families.update(requirement.feature_families)
                warnings.extend(
                    f"{requirement.dataset_id}:{item}"
                    for item in item_warnings
                )

                summaries.append(
                    MarketStateDatasetInputSummary(
                        dataset_id=requirement.dataset_id,
                        canonical_object=requirement.canonical_object,
                        provider_id=metadata.provider_id,
                        query_id=metadata.query_id,
                        result_count=metadata.result_count,
                        role=requirement.role,
                        feature_families=requirement.feature_families,
                        readiness_status=readiness_status,
                        warnings=tuple(item_warnings),
                    )
                )
            except (DataContractError, AttributeError, TypeError) as exc:
                blocked.append(requirement.dataset_id)
                warnings.append(
                    f"{requirement.dataset_id}:BLOCKED:{exc}"
                )

        missing_families = tuple(
            family
            for family in self.contract.required_feature_families
            if family not in covered_families
        )

        blocked_flag = bool(
            missing_required or blocked or missing_families
        )
        if blocked_flag:
            status = MarketStateInputStatus.BLOCKED
        elif warnings:
            status = MarketStateInputStatus.READY_WITH_WARNINGS
        else:
            status = MarketStateInputStatus.READY

        return MarketStateInputAssessment(
            status=status,
            contract_version=self.contract.contract_version,
            usage=self.contract.allowed_usage,
            research_feature_build_allowed=not blocked_flag,
            manual_decision_allowed=False,
            official_market_state_allowed=False,
            dataset_summaries=tuple(summaries),
            missing_required_datasets=tuple(missing_required),
            blocked_datasets=tuple(blocked),
            missing_feature_families=missing_families,
            warnings=tuple(dict.fromkeys(warnings)),
        )
