"""TASK_019D：研究级可解释市场状态评分。

所有锚点与阈值都是未验证研究假设。模块只生成候选状态，
不生成正式市场状态、仓位或交易信号。
"""
from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import Any, Iterable, Mapping

from .data_contracts import DataContractError
from .market_state_inputs import MarketStateFeatureFamily


SCORING_POLICY_STATUS = "RESEARCH_HYPOTHESIS_UNVALIDATED"


class ScoringFeatureRole(str, Enum):
    SCORE = "SCORE"
    CONTEXT_ONLY = "CONTEXT_ONLY"
    QUALITY_GATE = "QUALITY_GATE"


class ScoringOrientation(str, Enum):
    POSITIVE = "POSITIVE"
    STRESS = "STRESS"
    NONE = "NONE"


class ResearchMarketStateCandidate(str, Enum):
    BULLISH_CANDIDATE = "BULLISH_CANDIDATE"
    BALANCED_CANDIDATE = "BALANCED_CANDIDATE"
    BEARISH_CANDIDATE = "BEARISH_CANDIDATE"
    VOLATILE_TRANSITION_CANDIDATE = (
        "VOLATILE_TRANSITION_CANDIDATE"
    )
    STALE_INPUT_INDETERMINATE = "STALE_INPUT_INDETERMINATE"


class ResearchMarketStateScoreStatus(str, Enum):
    READY_WITH_WARNINGS = "READY_WITH_WARNINGS"
    BLOCKED = "BLOCKED"


def _require_text(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DataContractError(f"{field_name}不能为空。")
    return value.strip()


def _require_finite(value: Any, field_name: str) -> float:
    if isinstance(value, bool):
        raise DataContractError(f"{field_name}必须是有限数。")
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise DataContractError(
            f"{field_name}必须是有限数。"
        ) from exc
    if not math.isfinite(result):
        raise DataContractError(f"{field_name}必须是有限数。")
    return result


def _coerce_date(value: Any, field_name: str) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = _require_text(str(value), field_name)
    try:
        return date.fromisoformat(text[:10])
    except ValueError as exc:
        raise DataContractError(
            f"{field_name}不是有效ISO日期。"
        ) from exc


def _normalise_texts(
    values: Iterable[str],
    field_name: str,
    *,
    allow_empty: bool = False,
) -> tuple[str, ...]:
    result = tuple(_require_text(value, field_name) for value in values)
    if not allow_empty and not result:
        raise DataContractError(f"{field_name}不能为空。")
    if len(result) != len(set(result)):
        raise DataContractError(f"{field_name}不允许重复。")
    return result


def _piecewise_score(
    value: float,
    low_anchor: float,
    neutral_anchor: float,
    high_anchor: float,
) -> float:
    if not low_anchor < neutral_anchor < high_anchor:
        raise DataContractError("评分锚点必须严格递增。")
    if value <= low_anchor:
        return 0.0
    if value < neutral_anchor:
        return (
            50.0
            * (value - low_anchor)
            / (neutral_anchor - low_anchor)
        )
    if value < high_anchor:
        return (
            50.0
            + 50.0
            * (value - neutral_anchor)
            / (high_anchor - neutral_anchor)
        )
    return 100.0


@dataclass(frozen=True, slots=True)
class ScoringFeatureRule:
    feature_id: str
    family: MarketStateFeatureFamily
    role: ScoringFeatureRole
    orientation: ScoringOrientation
    weight: float
    hypothesis: str
    low_anchor: float | None = None
    neutral_anchor: float | None = None
    high_anchor: float | None = None
    minimum_value: float | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "feature_id",
            _require_text(self.feature_id, "feature_id"),
        )
        family = self.family
        if isinstance(family, str):
            family = MarketStateFeatureFamily(family)
        object.__setattr__(self, "family", family)
        role = self.role
        if isinstance(role, str):
            role = ScoringFeatureRole(role)
        object.__setattr__(self, "role", role)
        orientation = self.orientation
        if isinstance(orientation, str):
            orientation = ScoringOrientation(orientation)
        object.__setattr__(self, "orientation", orientation)
        object.__setattr__(
            self,
            "hypothesis",
            _require_text(self.hypothesis, "hypothesis"),
        )
        weight = _require_finite(self.weight, "weight")
        if weight < 0:
            raise DataContractError("weight不能为负。")
        object.__setattr__(self, "weight", weight)

        if role is ScoringFeatureRole.SCORE:
            if orientation not in {
                ScoringOrientation.POSITIVE,
                ScoringOrientation.STRESS,
            }:
                raise DataContractError(
                    "评分特征必须声明POSITIVE或STRESS。"
                )
            anchors = (
                self.low_anchor,
                self.neutral_anchor,
                self.high_anchor,
            )
            if any(value is None for value in anchors):
                raise DataContractError("评分特征必须提供三个锚点。")
            low, neutral, high = (
                _require_finite(value, "anchor")
                for value in anchors
            )
            if not low < neutral < high:
                raise DataContractError("评分锚点必须严格递增。")
            if weight <= 0:
                raise DataContractError("评分特征权重必须为正。")
        elif role is ScoringFeatureRole.QUALITY_GATE:
            if self.minimum_value is None:
                raise DataContractError(
                    "质量门禁必须提供minimum_value。"
                )
            _require_finite(self.minimum_value, "minimum_value")
            if orientation is not ScoringOrientation.NONE:
                raise DataContractError(
                    "质量门禁orientation必须为NONE。"
                )
        else:
            if orientation is not ScoringOrientation.NONE:
                raise DataContractError(
                    "上下文特征orientation必须为NONE。"
                )

    def normalise(self, value: float) -> float:
        if self.role is not ScoringFeatureRole.SCORE:
            raise DataContractError("非评分特征不能标准化。")
        return _piecewise_score(
            _require_finite(value, self.feature_id),
            float(self.low_anchor),
            float(self.neutral_anchor),
            float(self.high_anchor),
        )


@dataclass(frozen=True, slots=True)
class ResearchMarketStateScoringPolicy:
    task_id: str
    policy_version: str
    policy_status: str
    source_task_id: str
    input_feature_spec_version: str
    output_object: str
    output_scope: str
    manual_decision_allowed: bool
    official_market_state_allowed: bool
    trade_execution_allowed: bool
    regime_label_allowed: bool
    candidate_state_allowed: bool
    maximum_calendar_age_days_for_candidate: int
    minimum_amount_field_coverage_ratio: float
    required_feature_count: int
    scored_feature_count: int
    context_feature_count: int
    quality_gate_feature_count: int
    direction_dimension_weights: Mapping[
        MarketStateFeatureFamily,
        float,
    ]
    candidate_thresholds: Mapping[str, float]
    feature_rules: tuple[ScoringFeatureRule, ...]
    hard_rules: tuple[str, ...]

    def __post_init__(self) -> None:
        for field_name in (
            "task_id",
            "policy_version",
            "policy_status",
            "source_task_id",
            "input_feature_spec_version",
            "output_object",
            "output_scope",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_text(
                    getattr(self, field_name),
                    field_name,
                ),
            )
        if self.task_id != "TASK_019D":
            raise DataContractError("评分政策task_id异常。")
        if self.policy_status != SCORING_POLICY_STATUS:
            raise DataContractError("评分政策状态异常。")
        if self.source_task_id != "TASK_019C":
            raise DataContractError("评分来源任务异常。")
        if any(
            (
                self.manual_decision_allowed,
                self.official_market_state_allowed,
                self.trade_execution_allowed,
                self.regime_label_allowed,
            )
        ):
            raise DataContractError(
                "TASK_019D不得启用决策、正式状态、交易或正式标签。"
            )
        if not self.candidate_state_allowed:
            raise DataContractError("研究候选状态必须显式允许。")
        if (
            not isinstance(
                self.maximum_calendar_age_days_for_candidate,
                int,
            )
            or isinstance(
                self.maximum_calendar_age_days_for_candidate,
                bool,
            )
            or self.maximum_calendar_age_days_for_candidate < 0
        ):
            raise DataContractError("最大日历滞后必须为非负整数。")
        minimum_coverage = _require_finite(
            self.minimum_amount_field_coverage_ratio,
            "minimum_amount_field_coverage_ratio",
        )
        if not 0 <= minimum_coverage <= 1:
            raise DataContractError("最小覆盖率必须位于0到1。")
        ids = [rule.feature_id for rule in self.feature_rules]
        if len(ids) != len(set(ids)):
            raise DataContractError("评分规则feature_id不允许重复。")
        if len(ids) != self.required_feature_count:
            raise DataContractError("评分规则数量与required_feature_count不一致。")
        role_counts = {
            role: sum(rule.role is role for rule in self.feature_rules)
            for role in ScoringFeatureRole
        }
        if (
            role_counts[ScoringFeatureRole.SCORE]
            != self.scored_feature_count
            or role_counts[ScoringFeatureRole.CONTEXT_ONLY]
            != self.context_feature_count
            or role_counts[ScoringFeatureRole.QUALITY_GATE]
            != self.quality_gate_feature_count
        ):
            raise DataContractError("评分规则角色数量异常。")

        weights: dict[MarketStateFeatureFamily, float] = {}
        for raw_family, raw_weight in self.direction_dimension_weights.items():
            family = (
                raw_family
                if isinstance(raw_family, MarketStateFeatureFamily)
                else MarketStateFeatureFamily(str(raw_family))
            )
            weight = _require_finite(raw_weight, "dimension_weight")
            if weight <= 0:
                raise DataContractError("方向维度权重必须为正。")
            weights[family] = weight
        expected = {
            MarketStateFeatureFamily.TREND,
            MarketStateFeatureFamily.BREADTH,
            MarketStateFeatureFamily.LIQUIDITY,
            MarketStateFeatureFamily.SECTOR_DIFFUSION,
        }
        if set(weights) != expected:
            raise DataContractError("方向得分维度集合异常。")
        if not math.isclose(sum(weights.values()), 1.0, abs_tol=1e-9):
            raise DataContractError("方向维度权重之和必须为1。")
        object.__setattr__(
            self,
            "direction_dimension_weights",
            weights,
        )
        object.__setattr__(
            self,
            "hard_rules",
            _normalise_texts(self.hard_rules, "hard_rules"),
        )

    def rule(self, feature_id: str) -> ScoringFeatureRule:
        key = _require_text(feature_id, "feature_id")
        for rule in self.feature_rules:
            if rule.feature_id == key:
                return rule
        raise DataContractError(f"未登记评分特征：{key}")


@dataclass(frozen=True, slots=True)
class FeatureScoreContribution:
    feature_id: str
    family: MarketStateFeatureFamily
    role: ScoringFeatureRole
    orientation: ScoringOrientation
    raw_value: float
    normalised_score: float | None
    weight: float
    weighted_score: float | None
    hypothesis: str


@dataclass(frozen=True, slots=True)
class DimensionScore:
    family: MarketStateFeatureFamily
    score: float
    feature_count: int
    contributions: tuple[FeatureScoreContribution, ...]


@dataclass(frozen=True, slots=True)
class ResearchMarketStateScoreSnapshot:
    status: ResearchMarketStateScoreStatus
    policy_version: str
    policy_status: str
    source_task_id: str
    source_feature_spec_version: str
    source_common_trade_date: date | None
    source_as_of_date: date | None
    calendar_age_days: int | None
    stale_input: bool
    candidate_state: ResearchMarketStateCandidate | None
    directional_score: float | None
    volatility_stress_score: float | None
    stability_score: float | None
    dimension_scores: tuple[DimensionScore, ...]
    context_features: tuple[FeatureScoreContribution, ...]
    quality_gate_features: tuple[FeatureScoreContribution, ...]
    warnings: tuple[str, ...]
    blocking_reasons: tuple[str, ...]
    research_score_allowed: bool
    candidate_state_actionable: bool
    manual_decision_allowed: bool
    official_market_state_allowed: bool
    trade_execution_allowed: bool
    regime_label: None = None

    @property
    def blocks_downstream(self) -> bool:
        return self.status is ResearchMarketStateScoreStatus.BLOCKED

    def assert_research_usable(self) -> None:
        if self.blocks_downstream:
            raise DataContractError(
                "研究市场状态评分被阻断："
                + ", ".join(self.blocking_reasons)
            )

    def to_dict(self) -> dict[str, Any]:
        def convert(value: Any) -> Any:
            if isinstance(value, Enum):
                return value.value
            if isinstance(value, (date, datetime)):
                return value.isoformat()
            if isinstance(value, tuple):
                return [convert(item) for item in value]
            if isinstance(value, list):
                return [convert(item) for item in value]
            if isinstance(value, dict):
                return {str(k): convert(v) for k, v in value.items()}
            return value
        return convert(asdict(self))


def load_market_state_scoring_policy(
    path: str | Path,
) -> ResearchMarketStateScoringPolicy:
    policy_path = Path(path)
    try:
        raw = json.loads(policy_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DataContractError(
            f"无法加载市场状态评分政策：{policy_path}"
        ) from exc
    if not isinstance(raw, dict):
        raise DataContractError("评分政策根节点必须是对象。")
    rules = tuple(
        ScoringFeatureRule(
            feature_id=str(item["feature_id"]),
            family=MarketStateFeatureFamily(str(item["family"])),
            role=ScoringFeatureRole(str(item["role"])),
            orientation=ScoringOrientation(str(item["orientation"])),
            weight=float(item["weight"]),
            hypothesis=str(item["hypothesis"]),
            low_anchor=(
                float(item["low_anchor"])
                if "low_anchor" in item
                else None
            ),
            neutral_anchor=(
                float(item["neutral_anchor"])
                if "neutral_anchor" in item
                else None
            ),
            high_anchor=(
                float(item["high_anchor"])
                if "high_anchor" in item
                else None
            ),
            minimum_value=(
                float(item["minimum_value"])
                if "minimum_value" in item
                else None
            ),
        )
        for item in raw["feature_rules"]
    )
    return ResearchMarketStateScoringPolicy(
        task_id=str(raw["task_id"]),
        policy_version=str(raw["policy_version"]),
        policy_status=str(raw["policy_status"]),
        source_task_id=str(raw["source_task_id"]),
        input_feature_spec_version=str(
            raw["input_feature_spec_version"]
        ),
        output_object=str(raw["output_object"]),
        output_scope=str(raw["output_scope"]),
        manual_decision_allowed=bool(
            raw["manual_decision_allowed"]
        ),
        official_market_state_allowed=bool(
            raw["official_market_state_allowed"]
        ),
        trade_execution_allowed=bool(
            raw["trade_execution_allowed"]
        ),
        regime_label_allowed=bool(raw["regime_label_allowed"]),
        candidate_state_allowed=bool(
            raw["candidate_state_allowed"]
        ),
        maximum_calendar_age_days_for_candidate=int(
            raw["maximum_calendar_age_days_for_candidate"]
        ),
        minimum_amount_field_coverage_ratio=float(
            raw["minimum_amount_field_coverage_ratio"]
        ),
        required_feature_count=int(raw["required_feature_count"]),
        scored_feature_count=int(raw["scored_feature_count"]),
        context_feature_count=int(raw["context_feature_count"]),
        quality_gate_feature_count=int(
            raw["quality_gate_feature_count"]
        ),
        direction_dimension_weights={
            MarketStateFeatureFamily(str(key)): float(value)
            for key, value in raw[
                "direction_dimension_weights"
            ].items()
        },
        candidate_thresholds={
            str(key): float(value)
            for key, value in raw["candidate_thresholds"].items()
        },
        feature_rules=rules,
        hard_rules=tuple(str(value) for value in raw["hard_rules"]),
    )


class ExplainableResearchMarketStateScorer:
    """从TASK_019C特征报告生成研究级候选评分。"""

    def __init__(
        self,
        policy: ResearchMarketStateScoringPolicy,
    ) -> None:
        if not isinstance(policy, ResearchMarketStateScoringPolicy):
            raise DataContractError(
                "policy必须是ResearchMarketStateScoringPolicy。"
            )
        self.policy = policy

    def _blocked(
        self,
        reasons: Iterable[str],
        warnings: Iterable[str],
    ) -> ResearchMarketStateScoreSnapshot:
        return ResearchMarketStateScoreSnapshot(
            status=ResearchMarketStateScoreStatus.BLOCKED,
            policy_version=self.policy.policy_version,
            policy_status=self.policy.policy_status,
            source_task_id=self.policy.source_task_id,
            source_feature_spec_version=(
                self.policy.input_feature_spec_version
            ),
            source_common_trade_date=None,
            source_as_of_date=None,
            calendar_age_days=None,
            stale_input=False,
            candidate_state=None,
            directional_score=None,
            volatility_stress_score=None,
            stability_score=None,
            dimension_scores=(),
            context_features=(),
            quality_gate_features=(),
            warnings=tuple(dict.fromkeys(warnings)),
            blocking_reasons=tuple(dict.fromkeys(reasons)),
            research_score_allowed=False,
            candidate_state_actionable=False,
            manual_decision_allowed=False,
            official_market_state_allowed=False,
            trade_execution_allowed=False,
            regime_label=None,
        )

    def score(
        self,
        feature_report: Mapping[str, Any],
    ) -> ResearchMarketStateScoreSnapshot:
        if not isinstance(feature_report, Mapping):
            raise DataContractError("feature_report必须是对象。")

        reasons: list[str] = []
        warnings = list(feature_report.get("warnings") or ())
        warnings.append("SCORING_POLICY_UNVALIDATED_RESEARCH_HYPOTHESIS")

        if feature_report.get("task_id") != self.policy.source_task_id:
            reasons.append("SOURCE_TASK_ID_MISMATCH")
        if feature_report.get("issues") not in ([], None):
            reasons.append("SOURCE_REPORT_HAS_ISSUES")
        if not bool(feature_report.get("research_feature_build_allowed")):
            reasons.append("SOURCE_RESEARCH_FEATURE_BUILD_BLOCKED")
        if bool(feature_report.get("manual_decision_allowed")):
            reasons.append("SOURCE_MANUAL_DECISION_UNEXPECTEDLY_ALLOWED")
        if bool(feature_report.get("official_market_state_allowed")):
            reasons.append("SOURCE_OFFICIAL_STATE_UNEXPECTEDLY_ALLOWED")
        if feature_report.get("regime_label") is not None:
            reasons.append("SOURCE_REGIME_LABEL_UNEXPECTED")

        raw_features = feature_report.get("features")
        if not isinstance(raw_features, list):
            reasons.append("FEATURES_NOT_A_LIST")
            raw_features = []

        feature_by_id: dict[str, Mapping[str, Any]] = {}
        duplicate_ids: set[str] = set()
        for item in raw_features:
            if not isinstance(item, Mapping):
                reasons.append("FEATURE_ITEM_NOT_OBJECT")
                continue
            feature_id = str(item.get("feature_id", "")).strip()
            if not feature_id:
                reasons.append("FEATURE_ID_EMPTY")
                continue
            if feature_id in feature_by_id:
                duplicate_ids.add(feature_id)
            feature_by_id[feature_id] = item
        if duplicate_ids:
            reasons.append(
                "DUPLICATE_FEATURE_IDS:" + ",".join(sorted(duplicate_ids))
            )

        required_ids = {
            rule.feature_id for rule in self.policy.feature_rules
        }
        missing_ids = sorted(required_ids - set(feature_by_id))
        if missing_ids:
            reasons.append(
                "MISSING_REQUIRED_FEATURES:" + ",".join(missing_ids)
            )
        unexpected_ids = sorted(set(feature_by_id) - required_ids)
        if unexpected_ids:
            warnings.append(
                "UNREGISTERED_FEATURES_IGNORED:"
                + ",".join(unexpected_ids)
            )

        if reasons:
            return self._blocked(reasons, warnings)

        common_date = _coerce_date(
            feature_report.get("common_trade_date"),
            "common_trade_date",
        )
        as_of_date = _coerce_date(
            feature_report.get("as_of_date"),
            "as_of_date",
        )
        if common_date > as_of_date:
            return self._blocked(
                ("COMMON_DATE_AFTER_AS_OF_DATE",),
                warnings,
            )
        calendar_age_days = (as_of_date - common_date).days
        stale_input = (
            calendar_age_days
            > self.policy.maximum_calendar_age_days_for_candidate
        )
        if stale_input:
            warnings.append(
                "STALE_INPUT_EXCEEDS_MAX_CALENDAR_AGE"
            )

        scored_by_family: dict[
            MarketStateFeatureFamily,
            list[FeatureScoreContribution],
        ] = {}
        context: list[FeatureScoreContribution] = []
        gates: list[FeatureScoreContribution] = []

        for rule in self.policy.feature_rules:
            item = feature_by_id[rule.feature_id]
            value = _require_finite(
                item.get("value"),
                rule.feature_id,
            )
            if rule.role is ScoringFeatureRole.SCORE:
                normalised = rule.normalise(value)
                contribution = FeatureScoreContribution(
                    feature_id=rule.feature_id,
                    family=rule.family,
                    role=rule.role,
                    orientation=rule.orientation,
                    raw_value=value,
                    normalised_score=normalised,
                    weight=rule.weight,
                    weighted_score=normalised * rule.weight,
                    hypothesis=rule.hypothesis,
                )
                scored_by_family.setdefault(
                    rule.family,
                    [],
                ).append(contribution)
            elif rule.role is ScoringFeatureRole.QUALITY_GATE:
                contribution = FeatureScoreContribution(
                    feature_id=rule.feature_id,
                    family=rule.family,
                    role=rule.role,
                    orientation=rule.orientation,
                    raw_value=value,
                    normalised_score=None,
                    weight=0.0,
                    weighted_score=None,
                    hypothesis=rule.hypothesis,
                )
                gates.append(contribution)
                if value < float(rule.minimum_value):
                    reasons.append(
                        f"QUALITY_GATE_FAILED:{rule.feature_id}"
                    )
            else:
                context.append(
                    FeatureScoreContribution(
                        feature_id=rule.feature_id,
                        family=rule.family,
                        role=rule.role,
                        orientation=rule.orientation,
                        raw_value=value,
                        normalised_score=None,
                        weight=0.0,
                        weighted_score=None,
                        hypothesis=rule.hypothesis,
                    )
                )

        if reasons:
            return self._blocked(reasons, warnings)

        dimension_scores: list[DimensionScore] = []
        for family in (
            MarketStateFeatureFamily.TREND,
            MarketStateFeatureFamily.BREADTH,
            MarketStateFeatureFamily.LIQUIDITY,
            MarketStateFeatureFamily.VOLATILITY,
            MarketStateFeatureFamily.SECTOR_DIFFUSION,
        ):
            contributions = tuple(scored_by_family.get(family, ()))
            if not contributions:
                return self._blocked(
                    (f"MISSING_DIMENSION_SCORE:{family.value}",),
                    warnings,
                )
            total_weight = sum(item.weight for item in contributions)
            score = (
                sum(
                    float(item.weighted_score)
                    for item in contributions
                )
                / total_weight
            )
            dimension_scores.append(
                DimensionScore(
                    family=family,
                    score=score,
                    feature_count=len(contributions),
                    contributions=contributions,
                )
            )

        dimension_by_family = {
            item.family: item.score for item in dimension_scores
        }
        directional_score = sum(
            dimension_by_family[family] * weight
            for family, weight
            in self.policy.direction_dimension_weights.items()
        )
        volatility_stress_score = dimension_by_family[
            MarketStateFeatureFamily.VOLATILITY
        ]
        stability_score = 100.0 - volatility_stress_score

        thresholds = self.policy.candidate_thresholds
        if stale_input:
            candidate = (
                ResearchMarketStateCandidate
                .STALE_INPUT_INDETERMINATE
            )
        elif (
            volatility_stress_score
            >= thresholds[
                "volatile_transition_min_stress_score"
            ]
            and thresholds[
                "volatile_transition_direction_lower"
            ]
            <= directional_score
            <= thresholds[
                "volatile_transition_direction_upper"
            ]
        ):
            candidate = (
                ResearchMarketStateCandidate
                .VOLATILE_TRANSITION_CANDIDATE
            )
        elif (
            directional_score
            >= thresholds["bullish_min_direction_score"]
        ):
            candidate = (
                ResearchMarketStateCandidate.BULLISH_CANDIDATE
            )
        elif (
            directional_score
            <= thresholds["bearish_max_direction_score"]
        ):
            candidate = (
                ResearchMarketStateCandidate.BEARISH_CANDIDATE
            )
        else:
            candidate = (
                ResearchMarketStateCandidate.BALANCED_CANDIDATE
            )

        return ResearchMarketStateScoreSnapshot(
            status=(
                ResearchMarketStateScoreStatus
                .READY_WITH_WARNINGS
            ),
            policy_version=self.policy.policy_version,
            policy_status=self.policy.policy_status,
            source_task_id=self.policy.source_task_id,
            source_feature_spec_version=(
                self.policy.input_feature_spec_version
            ),
            source_common_trade_date=common_date,
            source_as_of_date=as_of_date,
            calendar_age_days=calendar_age_days,
            stale_input=stale_input,
            candidate_state=candidate,
            directional_score=directional_score,
            volatility_stress_score=volatility_stress_score,
            stability_score=stability_score,
            dimension_scores=tuple(dimension_scores),
            context_features=tuple(context),
            quality_gate_features=tuple(gates),
            warnings=tuple(dict.fromkeys(warnings)),
            blocking_reasons=(),
            research_score_allowed=True,
            candidate_state_actionable=False,
            manual_decision_allowed=False,
            official_market_state_allowed=False,
            trade_execution_allowed=False,
            regime_label=None,
        )
