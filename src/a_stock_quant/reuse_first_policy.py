"""复用优先开发政策和可审计决策合同。"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Iterable, Mapping

from .data_contracts import DataContractError


class ReuseCandidateType(str, Enum):
    EXISTING_PROJECT_COMPONENT = "EXISTING_PROJECT_COMPONENT"
    OFFICIAL_VENDOR_SDK = "OFFICIAL_VENDOR_SDK"
    OPEN_STANDARD_PROTOCOL = "OPEN_STANDARD_PROTOCOL"
    MATURE_OPEN_SOURCE_LIBRARY = "MATURE_OPEN_SOURCE_LIBRARY"
    REFERENCE_IMPLEMENTATION = "REFERENCE_IMPLEMENTATION"
    THIN_ADAPTER_OR_BRIDGE = "THIN_ADAPTER_OR_BRIDGE"
    CUSTOM_IMPLEMENTATION = "CUSTOM_IMPLEMENTATION"


class ReuseDecisionType(str, Enum):
    REUSE_AS_IS = "REUSE_AS_IS"
    WRAP_WITH_THIN_ADAPTER = "WRAP_WITH_THIN_ADAPTER"
    EXTEND_EXISTING_COMPONENT = "EXTEND_EXISTING_COMPONENT"
    DEFER_PENDING_DISCOVERY = "DEFER_PENDING_DISCOVERY"
    CUSTOM_BUILD_APPROVED = "CUSTOM_BUILD_APPROVED"
    REJECT = "REJECT"


class ReviewStatus(str, Enum):
    NOT_REVIEWED = "NOT_REVIEWED"
    PASSED = "PASSED"
    PASSED_WITH_WARNINGS = "PASSED_WITH_WARNINGS"
    BLOCKED = "BLOCKED"


def _require_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DataContractError(f"{field_name}不能为空。")
    return value.strip()


def _optional_text(value: Any, field_name: str) -> str | None:
    if value is None:
        return None
    return _require_text(value, field_name)


def _unique_texts(
    values: Iterable[Any],
    field_name: str,
    *,
    allow_empty: bool = True,
) -> tuple[str, ...]:
    result = tuple(_require_text(value, field_name) for value in values)
    if not allow_empty and not result:
        raise DataContractError(f"{field_name}不能为空。")
    if len(result) != len(set(result)):
        raise DataContractError(f"{field_name}不允许重复。")
    return result


@dataclass(frozen=True, slots=True)
class ReuseCandidateAssessment:
    candidate_id: str
    candidate_type: ReuseCandidateType
    name: str
    source_ref: str
    version: str | None
    license_id: str | None
    license_status: ReviewStatus
    security_status: ReviewStatus
    maintenance_status: ReviewStatus
    compatibility_status: ReviewStatus
    semantic_gap_status: ReviewStatus
    supported_requirements: tuple[str, ...]
    gaps: tuple[str, ...]
    warnings: tuple[str, ...]
    evidence_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        for field_name in (
            "candidate_id",
            "name",
            "source_ref",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_text(getattr(self, field_name), field_name),
            )
        candidate_type = self.candidate_type
        if isinstance(candidate_type, str):
            candidate_type = ReuseCandidateType(candidate_type)
        object.__setattr__(self, "candidate_type", candidate_type)
        for field_name in ("version", "license_id"):
            object.__setattr__(
                self,
                field_name,
                _optional_text(getattr(self, field_name), field_name),
            )
        for field_name in (
            "license_status",
            "security_status",
            "maintenance_status",
            "compatibility_status",
            "semantic_gap_status",
        ):
            value = getattr(self, field_name)
            if isinstance(value, str):
                value = ReviewStatus(value)
            object.__setattr__(self, field_name, value)
        for field_name in (
            "supported_requirements",
            "gaps",
            "warnings",
            "evidence_refs",
        ):
            object.__setattr__(
                self,
                field_name,
                _unique_texts(
                    getattr(self, field_name),
                    field_name,
                ),
            )
        if self.license_status in {
            ReviewStatus.PASSED,
            ReviewStatus.PASSED_WITH_WARNINGS,
        } and self.license_id is None:
            raise DataContractError(
                "许可证通过时必须记录license_id。"
            )
        if self.candidate_type is not ReuseCandidateType.CUSTOM_IMPLEMENTATION:
            if not self.evidence_refs:
                raise DataContractError(
                    "复用候选必须包含证据引用。"
                )

    @property
    def blocked(self) -> bool:
        return any(
            status is ReviewStatus.BLOCKED
            for status in (
                self.license_status,
                self.security_status,
                self.maintenance_status,
                self.compatibility_status,
                self.semantic_gap_status,
            )
        )

    @property
    def reusable(self) -> bool:
        accepted = {
            ReviewStatus.PASSED,
            ReviewStatus.PASSED_WITH_WARNINGS,
        }
        return (
            not self.blocked
            and self.license_status in accepted
            and self.security_status in accepted
            and self.maintenance_status in accepted
            and self.compatibility_status in accepted
            and self.semantic_gap_status in accepted
        )


@dataclass(frozen=True, slots=True)
class ReuseDecisionRecord:
    decision_id: str
    problem_statement: str
    requirements: tuple[str, ...]
    candidates: tuple[ReuseCandidateAssessment, ...]
    decision: ReuseDecisionType
    selected_candidate_id: str | None
    rationale: str
    custom_build_evidence: Mapping[str, str]
    maintenance_owner: str | None
    test_plan_ref: str | None
    migration_path: str | None
    evidence_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        for field_name in (
            "decision_id",
            "problem_statement",
            "rationale",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_text(getattr(self, field_name), field_name),
            )
        object.__setattr__(
            self,
            "requirements",
            _unique_texts(
                self.requirements,
                "requirements",
                allow_empty=False,
            ),
        )
        if not self.candidates:
            raise DataContractError("至少需要一个候选方案。")
        candidate_ids = [item.candidate_id for item in self.candidates]
        if len(candidate_ids) != len(set(candidate_ids)):
            raise DataContractError("candidate_id不允许重复。")
        decision = self.decision
        if isinstance(decision, str):
            decision = ReuseDecisionType(decision)
        object.__setattr__(self, "decision", decision)
        selected = _optional_text(
            self.selected_candidate_id,
            "selected_candidate_id",
        )
        object.__setattr__(self, "selected_candidate_id", selected)
        object.__setattr__(
            self,
            "maintenance_owner",
            _optional_text(self.maintenance_owner, "maintenance_owner"),
        )
        object.__setattr__(
            self,
            "test_plan_ref",
            _optional_text(self.test_plan_ref, "test_plan_ref"),
        )
        object.__setattr__(
            self,
            "migration_path",
            _optional_text(self.migration_path, "migration_path"),
        )
        object.__setattr__(
            self,
            "evidence_refs",
            _unique_texts(
                self.evidence_refs,
                "evidence_refs",
                allow_empty=False,
            ),
        )
        custom_evidence = {
            _require_text(key, "custom_build_evidence_key"): _require_text(
                value,
                "custom_build_evidence_value",
            )
            for key, value in self.custom_build_evidence.items()
        }
        object.__setattr__(
            self,
            "custom_build_evidence",
            custom_evidence,
        )

        selected_candidate = None
        if selected is not None:
            for item in self.candidates:
                if item.candidate_id == selected:
                    selected_candidate = item
                    break
            if selected_candidate is None:
                raise DataContractError("selected_candidate_id不存在。")

        selection_decisions = {
            ReuseDecisionType.REUSE_AS_IS,
            ReuseDecisionType.WRAP_WITH_THIN_ADAPTER,
            ReuseDecisionType.EXTEND_EXISTING_COMPONENT,
            ReuseDecisionType.CUSTOM_BUILD_APPROVED,
        }
        if decision in selection_decisions and selected_candidate is None:
            raise DataContractError("该决策必须选择候选方案。")

        if decision in {
            ReuseDecisionType.REUSE_AS_IS,
            ReuseDecisionType.WRAP_WITH_THIN_ADAPTER,
            ReuseDecisionType.EXTEND_EXISTING_COMPONENT,
        }:
            if selected_candidate is None or not selected_candidate.reusable:
                raise DataContractError("选中的复用候选未通过评审。")
            if (
                selected_candidate.candidate_type
                is ReuseCandidateType.CUSTOM_IMPLEMENTATION
            ):
                raise DataContractError("复用决策不能选择自研候选。")

        if decision is ReuseDecisionType.CUSTOM_BUILD_APPROVED:
            if (
                selected_candidate is None
                or selected_candidate.candidate_type
                is not ReuseCandidateType.CUSTOM_IMPLEMENTATION
            ):
                raise DataContractError(
                    "自研批准必须选择CUSTOM_IMPLEMENTATION。"
                )
            required_keys = {
                "documented_functional_gap",
                "documented_candidate_comparison",
                "documented_license_or_security_blocker",
                "documented_maintenance_owner",
                "documented_test_plan",
                "documented_migration_or_replacement_path",
            }
            if set(custom_evidence) != required_keys:
                raise DataContractError("自研证据集合不完整。")
            if not all(
                (
                    self.maintenance_owner,
                    self.test_plan_ref,
                    self.migration_path,
                )
            ):
                raise DataContractError(
                    "自研批准必须记录维护、测试和迁移信息。"
                )

    def to_dict(self) -> dict[str, Any]:
        def convert(value: Any) -> Any:
            if isinstance(value, Enum):
                return value.value
            if isinstance(value, tuple):
                return [convert(item) for item in value]
            if isinstance(value, list):
                return [convert(item) for item in value]
            if isinstance(value, Mapping):
                return {
                    str(key): convert(item)
                    for key, item in value.items()
                }
            return value
        return convert(asdict(self))


@dataclass(frozen=True, slots=True)
class ReuseFirstPolicy:
    task_id: str
    policy_version: str
    policy_status: str
    principle: str
    custom_implementation_default_allowed: bool
    unknown_license_reuse_allowed: bool
    copy_without_provenance_allowed: bool
    vendor_sdk_reimplementation_allowed: bool
    reuse_order: tuple[str, ...]
    required_assessment_sections: tuple[str, ...]
    required_custom_build_evidence: tuple[str, ...]
    adapter_specific_rules: tuple[str, ...]
    hard_rules: tuple[str, ...]

    def __post_init__(self) -> None:
        for field_name in (
            "task_id",
            "policy_version",
            "policy_status",
            "principle",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_text(getattr(self, field_name), field_name),
            )
        if self.task_id != "TASK_020B_REUSE":
            raise DataContractError("复用政策task_id异常。")
        if self.principle != "REUSE_FIRST_CUSTOM_BUILD_LAST":
            raise DataContractError("复用政策原则异常。")
        if any(
            (
                self.custom_implementation_default_allowed,
                self.unknown_license_reuse_allowed,
                self.copy_without_provenance_allowed,
                self.vendor_sdk_reimplementation_allowed,
            )
        ):
            raise DataContractError("复用优先硬约束被破坏。")
        for field_name in (
            "reuse_order",
            "required_assessment_sections",
            "required_custom_build_evidence",
            "adapter_specific_rules",
            "hard_rules",
        ):
            object.__setattr__(
                self,
                field_name,
                _unique_texts(
                    getattr(self, field_name),
                    field_name,
                    allow_empty=False,
                ),
            )
        if self.reuse_order[-1] != "CUSTOM_IMPLEMENTATION_LAST_RESORT":
            raise DataContractError("自研必须位于复用顺序最后。")


def load_reuse_first_policy(path: str | Path) -> ReuseFirstPolicy:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise DataContractError("复用政策根节点必须是对象。")
    return ReuseFirstPolicy(
        task_id=str(raw["task_id"]),
        policy_version=str(raw["policy_version"]),
        policy_status=str(raw["policy_status"]),
        principle=str(raw["principle"]),
        custom_implementation_default_allowed=bool(
            raw["custom_implementation_default_allowed"]
        ),
        unknown_license_reuse_allowed=bool(
            raw["unknown_license_reuse_allowed"]
        ),
        copy_without_provenance_allowed=bool(
            raw["copy_without_provenance_allowed"]
        ),
        vendor_sdk_reimplementation_allowed=bool(
            raw["vendor_sdk_reimplementation_allowed"]
        ),
        reuse_order=tuple(str(value) for value in raw["reuse_order"]),
        required_assessment_sections=tuple(
            str(value)
            for value in raw["required_assessment_sections"]
        ),
        required_custom_build_evidence=tuple(
            str(value)
            for value in raw["required_custom_build_evidence"]
        ),
        adapter_specific_rules=tuple(
            str(value) for value in raw["adapter_specific_rules"]
        ),
        hard_rules=tuple(str(value) for value in raw["hard_rules"]),
    )
