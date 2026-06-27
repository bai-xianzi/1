"""TASK_019B：可解释市场状态研究特征。

本模块只生成可追溯的研究特征快照，不计算市场状态标签，
不生成仓位或交易建议。
"""
from __future__ import annotations

import json
import math
import statistics
from dataclasses import asdict, dataclass
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from .data_contracts import DataContractError
from .market_state_inputs import (
    MarketStateFeatureFamily,
    MarketStateInputContractEngine,
    MarketStateInputStatus,
)
from .standard_data_service import StandardDataUsage


MARKET_STATE_FEATURE_SPEC_VERSION = "0.1.0"


class MarketStateFeatureStatus(str, Enum):
    READY = "READY"
    READY_WITH_WARNINGS = "READY_WITH_WARNINGS"
    BLOCKED = "BLOCKED"


def _require_text(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DataContractError(f"{field_name}不能为空。")
    return value.strip()


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


def _coerce_date(value: Any) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str) and value.strip():
        text = value.strip()
        try:
            return date.fromisoformat(text[:10])
        except ValueError:
            return None
    return None


def _to_float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(result):
        return None
    return result


def _record_trade_date(record: Any) -> date | None:
    values = getattr(record, "values", {})
    primary_key = getattr(record, "primary_key", {})
    return _coerce_date(
        values.get("trade_date", primary_key.get("trade_date"))
    )


def _records_on_date(records: Sequence[Any], target: date) -> tuple[Any, ...]:
    return tuple(
        record
        for record in records
        if _record_trade_date(record) == target
    )


def _numeric_values(records: Sequence[Any], field_name: str) -> list[float]:
    result: list[float] = []
    for record in records:
        value = _to_float(getattr(record, "values", {}).get(field_name))
        if value is not None:
            result.append(value)
    return result


@dataclass(frozen=True, slots=True)
class MarketStateFeatureDefinition:
    feature_id: str
    family: MarketStateFeatureFamily
    unit: str
    source_dataset_ids: tuple[str, ...]
    required_fields: tuple[str, ...]
    minimum_observation_count: int
    formula: str
    interpretation: str

    def __post_init__(self) -> None:
        for field_name in (
            "feature_id",
            "unit",
            "formula",
            "interpretation",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_text(getattr(self, field_name), field_name),
            )
        family = self.family
        if isinstance(family, str):
            family = MarketStateFeatureFamily(family)
        object.__setattr__(self, "family", family)
        object.__setattr__(
            self,
            "source_dataset_ids",
            _normalise_texts(
                self.source_dataset_ids,
                "source_dataset_ids",
            ),
        )
        object.__setattr__(
            self,
            "required_fields",
            _normalise_texts(
                self.required_fields,
                "required_fields",
            ),
        )
        if (
            not isinstance(self.minimum_observation_count, int)
            or self.minimum_observation_count < 1
        ):
            raise DataContractError(
                "minimum_observation_count必须是正整数。"
            )


@dataclass(frozen=True, slots=True)
class MarketStateFeatureSpec:
    task_id: str
    spec_version: str
    input_contract_version: str
    output_object: str
    output_scope: str
    allowed_usage: StandardDataUsage
    manual_decision_allowed: bool
    official_market_state_allowed: bool
    regime_label_allowed: bool
    date_alignment_policy: str
    required_source_datasets: tuple[str, ...]
    required_feature_families: tuple[MarketStateFeatureFamily, ...]
    feature_definitions: tuple[MarketStateFeatureDefinition, ...]
    hard_rules: tuple[str, ...]

    def __post_init__(self) -> None:
        for field_name in (
            "task_id",
            "spec_version",
            "input_contract_version",
            "output_object",
            "output_scope",
            "date_alignment_policy",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_text(getattr(self, field_name), field_name),
            )
        usage = self.allowed_usage
        if isinstance(usage, str):
            usage = StandardDataUsage(usage)
        if usage is not StandardDataUsage.CURRENT_SNAPSHOT_RESEARCH:
            raise DataContractError(
                "TASK_019B只允许CURRENT_SNAPSHOT_RESEARCH。"
            )
        object.__setattr__(self, "allowed_usage", usage)
        if (
            self.manual_decision_allowed
            or self.official_market_state_allowed
            or self.regime_label_allowed
        ):
            raise DataContractError(
                "TASK_019B不得启用决策、正式状态或状态标签。"
            )
        if self.date_alignment_policy != "LATEST_COMMON_TRADE_DATE":
            raise DataContractError("不支持的日期对齐政策。")
        object.__setattr__(
            self,
            "required_source_datasets",
            _normalise_texts(
                self.required_source_datasets,
                "required_source_datasets",
            ),
        )
        families = tuple(
            item if isinstance(item, MarketStateFeatureFamily)
            else MarketStateFeatureFamily(item)
            for item in self.required_feature_families
        )
        if not families or len(families) != len(set(families)):
            raise DataContractError(
                "required_feature_families必须非空且唯一。"
            )
        object.__setattr__(self, "required_feature_families", families)
        if not self.feature_definitions:
            raise DataContractError("feature_definitions不能为空。")
        feature_ids = [item.feature_id for item in self.feature_definitions]
        if len(feature_ids) != len(set(feature_ids)):
            raise DataContractError("feature_id不允许重复。")
        covered = {item.family for item in self.feature_definitions}
        if not set(families).issubset(covered):
            raise DataContractError("必需特征族未被定义覆盖。")
        object.__setattr__(
            self,
            "hard_rules",
            _normalise_texts(self.hard_rules, "hard_rules"),
        )

    def definition(self, feature_id: str) -> MarketStateFeatureDefinition:
        key = _require_text(feature_id, "feature_id")
        for item in self.feature_definitions:
            if item.feature_id == key:
                return item
        raise DataContractError(f"未登记市场状态特征：{key}")


@dataclass(frozen=True, slots=True)
class MarketStateFeatureObservation:
    feature_id: str
    family: MarketStateFeatureFamily
    value: float
    unit: str
    as_of_date: date
    formula: str
    interpretation: str
    source_dataset_ids: tuple[str, ...]
    source_query_ids: tuple[str, ...]
    source_record_count: int
    valid_observation_count: int
    missing_observation_count: int
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for field_name in (
            "feature_id",
            "unit",
            "formula",
            "interpretation",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_text(getattr(self, field_name), field_name),
            )
        if not isinstance(self.as_of_date, date):
            raise DataContractError("as_of_date必须是date。")
        if not math.isfinite(float(self.value)):
            raise DataContractError("特征值必须是有限数。")
        if self.source_record_count < 0:
            raise DataContractError("source_record_count不能为负。")
        if self.valid_observation_count < 0:
            raise DataContractError(
                "valid_observation_count不能为负。"
            )
        if self.missing_observation_count < 0:
            raise DataContractError(
                "missing_observation_count不能为负。"
            )
        object.__setattr__(
            self,
            "source_dataset_ids",
            _normalise_texts(
                self.source_dataset_ids,
                "source_dataset_ids",
            ),
        )
        object.__setattr__(
            self,
            "source_query_ids",
            _normalise_texts(
                self.source_query_ids,
                "source_query_ids",
            ),
        )
        object.__setattr__(
            self,
            "warnings",
            _normalise_texts(
                self.warnings,
                "warnings",
                allow_empty=True,
            ),
        )


@dataclass(frozen=True, slots=True)
class MarketStateFeatureSnapshot:
    status: MarketStateFeatureStatus
    feature_spec_version: str
    input_contract_version: str
    usage: StandardDataUsage
    as_of_date: date | None
    input_assessment_status: str
    features: tuple[MarketStateFeatureObservation, ...]
    missing_required_features: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    research_feature_build_allowed: bool = False
    manual_decision_allowed: bool = False
    official_market_state_allowed: bool = False
    regime_label: str | None = None

    @property
    def blocks_downstream(self) -> bool:
        return self.status is MarketStateFeatureStatus.BLOCKED

    def assert_research_usable(self) -> None:
        if self.blocks_downstream:
            raise DataContractError(
                "市场状态特征快照被阻断："
                + ", ".join(self.missing_required_features)
            )

    def feature(self, feature_id: str) -> MarketStateFeatureObservation:
        key = _require_text(feature_id, "feature_id")
        for item in self.features:
            if item.feature_id == key:
                return item
        raise DataContractError(f"特征快照中不存在：{key}")

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


def load_market_state_feature_spec(
    path: str | Path,
) -> MarketStateFeatureSpec:
    spec_path = Path(path)
    try:
        raw = json.loads(spec_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DataContractError(
            f"无法加载市场状态特征规范：{spec_path}"
        ) from exc
    if not isinstance(raw, dict):
        raise DataContractError("特征规范根节点必须是对象。")
    definitions = tuple(
        MarketStateFeatureDefinition(
            feature_id=str(item["feature_id"]),
            family=MarketStateFeatureFamily(str(item["family"])),
            unit=str(item["unit"]),
            source_dataset_ids=tuple(
                str(value) for value in item["source_dataset_ids"]
            ),
            required_fields=tuple(
                str(value) for value in item["required_fields"]
            ),
            minimum_observation_count=int(
                item["minimum_observation_count"]
            ),
            formula=str(item["formula"]),
            interpretation=str(item["interpretation"]),
        )
        for item in raw["feature_definitions"]
    )
    return MarketStateFeatureSpec(
        task_id=str(raw["task_id"]),
        spec_version=str(raw["spec_version"]),
        input_contract_version=str(raw["input_contract_version"]),
        output_object=str(raw["output_object"]),
        output_scope=str(raw["output_scope"]),
        allowed_usage=StandardDataUsage(str(raw["allowed_usage"])),
        manual_decision_allowed=bool(raw["manual_decision_allowed"]),
        official_market_state_allowed=bool(
            raw["official_market_state_allowed"]
        ),
        regime_label_allowed=bool(raw["regime_label_allowed"]),
        date_alignment_policy=str(raw["date_alignment_policy"]),
        required_source_datasets=tuple(
            str(value) for value in raw["required_source_datasets"]
        ),
        required_feature_families=tuple(
            MarketStateFeatureFamily(str(value))
            for value in raw["required_feature_families"]
        ),
        feature_definitions=definitions,
        hard_rules=tuple(str(value) for value in raw["hard_rules"]),
    )


class ExplainableMarketStateFeatureCalculator:
    """从通过TASK_019A门禁的结果构建可解释研究特征。"""

    def __init__(
        self,
        input_engine: MarketStateInputContractEngine,
        feature_spec: MarketStateFeatureSpec,
    ) -> None:
        if not isinstance(input_engine, MarketStateInputContractEngine):
            raise DataContractError(
                "input_engine必须是MarketStateInputContractEngine。"
            )
        if not isinstance(feature_spec, MarketStateFeatureSpec):
            raise DataContractError(
                "feature_spec必须是MarketStateFeatureSpec。"
            )
        if (
            input_engine.contract.contract_version
            != feature_spec.input_contract_version
        ):
            raise DataContractError(
                "输入合同版本与特征规范不一致。"
            )
        self.input_engine = input_engine
        self.feature_spec = feature_spec

    @staticmethod
    def _standard_result(gated_result: Any) -> Any:
        if not hasattr(gated_result, "standard_result"):
            raise DataContractError("缺少standard_result。")
        return gated_result.standard_result

    def _blocked_snapshot(
        self,
        input_status: str,
        warnings: Iterable[str],
        missing_features: Iterable[str] = (),
    ) -> MarketStateFeatureSnapshot:
        return MarketStateFeatureSnapshot(
            status=MarketStateFeatureStatus.BLOCKED,
            feature_spec_version=self.feature_spec.spec_version,
            input_contract_version=(
                self.feature_spec.input_contract_version
            ),
            usage=self.feature_spec.allowed_usage,
            as_of_date=None,
            input_assessment_status=input_status,
            features=(),
            missing_required_features=tuple(
                dict.fromkeys(missing_features)
            ),
            warnings=tuple(dict.fromkeys(warnings)),
            research_feature_build_allowed=False,
            manual_decision_allowed=False,
            official_market_state_allowed=False,
            regime_label=None,
        )

    def _latest_common_date(
        self,
        results: Mapping[str, Any],
    ) -> date | None:
        date_sets: list[set[date]] = []
        for dataset_id in self.feature_spec.required_source_datasets:
            gated = results.get(dataset_id)
            if gated is None:
                return None
            standard = self._standard_result(gated)
            dates = {
                item
                for item in (
                    _record_trade_date(record)
                    for record in standard.records
                )
                if item is not None
            }
            if not dates:
                return None
            date_sets.append(dates)
        common = set.intersection(*date_sets)
        return max(common) if common else None

    def _observe(
        self,
        feature_id: str,
        value: float | None,
        *,
        as_of_date: date,
        source_records: Sequence[Any],
        valid_count: int,
        query_ids: tuple[str, ...],
        warnings: Iterable[str] = (),
    ) -> MarketStateFeatureObservation | None:
        definition = self.feature_spec.definition(feature_id)
        if value is None:
            return None
        if valid_count < definition.minimum_observation_count:
            return None
        source_count = len(source_records)
        return MarketStateFeatureObservation(
            feature_id=definition.feature_id,
            family=definition.family,
            value=float(value),
            unit=definition.unit,
            as_of_date=as_of_date,
            formula=definition.formula,
            interpretation=definition.interpretation,
            source_dataset_ids=definition.source_dataset_ids,
            source_query_ids=query_ids,
            source_record_count=source_count,
            valid_observation_count=valid_count,
            missing_observation_count=max(
                source_count - valid_count,
                0,
            ),
            warnings=tuple(dict.fromkeys(warnings)),
        )

    def calculate(
        self,
        results: Mapping[str, Any],
    ) -> MarketStateFeatureSnapshot:
        input_assessment = self.input_engine.evaluate(results)
        input_status = input_assessment.status.value
        propagated_warnings = list(input_assessment.warnings)

        if input_assessment.blocks_downstream:
            missing = [
                *input_assessment.missing_required_datasets,
                *input_assessment.blocked_datasets,
                *(
                    family.value
                    for family in input_assessment.missing_feature_families
                ),
            ]
            return self._blocked_snapshot(
                input_status,
                propagated_warnings,
                missing,
            )

        common_date = self._latest_common_date(results)
        if common_date is None:
            propagated_warnings.append(
                "NO_COMMON_TRADE_DATE_FOR_REQUIRED_DATASETS"
            )
            return self._blocked_snapshot(
                input_status,
                propagated_warnings,
                ("LATEST_COMMON_TRADE_DATE",),
            )

        daily_result = self._standard_result(
            results["a_stock_daily_k"]
        )
        industry_result = self._standard_result(results["hy"])
        daily_records = _records_on_date(
            daily_result.records,
            common_date,
        )
        industry_records = _records_on_date(
            industry_result.records,
            common_date,
        )
        daily_query_ids = (daily_result.metadata.query_id,)
        industry_query_ids = (industry_result.metadata.query_id,)

        observations: list[MarketStateFeatureObservation] = []

        daily_returns = _numeric_values(
            daily_records,
            "pct_change_pct",
        )
        amounts = _numeric_values(daily_records, "amount_cny")
        turnover_rates = _numeric_values(
            daily_records,
            "turnover_rate_pct",
        )
        intraday_ranges: list[float] = []
        for record in daily_records:
            values = record.values
            high = _to_float(values.get("high_raw_cny"))
            low = _to_float(values.get("low_raw_cny"))
            close = _to_float(values.get("close_raw_cny"))
            if (
                high is not None
                and low is not None
                and close is not None
                and close > 0
                and high >= low
            ):
                intraday_ranges.append(
                    (high - low) / close * 100.0
                )

        up_counts = _numeric_values(industry_records, "up_count")
        down_counts = _numeric_values(
            industry_records,
            "down_count",
        )
        limit_up_counts = _numeric_values(
            industry_records,
            "limit_up_count",
        )
        breadth_ratios = _numeric_values(
            industry_records,
            "breadth_ratio",
        )
        industry_returns = _numeric_values(
            industry_records,
            "pct_change_pct",
        )
        average_returns = _numeric_values(
            industry_records,
            "average_return_pct",
        )

        def add(item: MarketStateFeatureObservation | None) -> None:
            if item is not None:
                observations.append(item)

        add(self._observe(
            "daily_positive_return_ratio",
            (
                sum(value > 0 for value in daily_returns)
                / len(daily_returns)
                if daily_returns else None
            ),
            as_of_date=common_date,
            source_records=daily_records,
            valid_count=len(daily_returns),
            query_ids=daily_query_ids,
        ))
        add(self._observe(
            "daily_mean_return_pct",
            statistics.fmean(daily_returns)
            if daily_returns else None,
            as_of_date=common_date,
            source_records=daily_records,
            valid_count=len(daily_returns),
            query_ids=daily_query_ids,
        ))
        add(self._observe(
            "daily_median_return_pct",
            statistics.median(daily_returns)
            if daily_returns else None,
            as_of_date=common_date,
            source_records=daily_records,
            valid_count=len(daily_returns),
            query_ids=daily_query_ids,
        ))

        total_up = sum(up_counts)
        total_down = sum(down_counts)
        comparable_total = total_up + total_down
        breadth_valid_count = min(
            len(up_counts),
            len(down_counts),
        )
        add(self._observe(
            "industry_advance_ratio",
            total_up / comparable_total
            if comparable_total > 0 else None,
            as_of_date=common_date,
            source_records=industry_records,
            valid_count=breadth_valid_count,
            query_ids=industry_query_ids,
        ))
        add(self._observe(
            "industry_breadth_ratio_median",
            statistics.median(breadth_ratios)
            if breadth_ratios else None,
            as_of_date=common_date,
            source_records=industry_records,
            valid_count=len(breadth_ratios),
            query_ids=industry_query_ids,
        ))
        limit_share_warnings: list[str] = []
        if total_up > 0:
            limit_share = sum(limit_up_counts) / total_up
        elif up_counts and limit_up_counts:
            limit_share = 0.0
            limit_share_warnings.append(
                "ZERO_TOTAL_UP_COUNT_INTERPRETED_AS_ZERO_SHARE"
            )
        else:
            limit_share = None
        add(self._observe(
            "industry_limit_up_share_of_up",
            limit_share,
            as_of_date=common_date,
            source_records=industry_records,
            valid_count=min(len(limit_up_counts), len(up_counts)),
            query_ids=industry_query_ids,
            warnings=limit_share_warnings,
        ))

        add(self._observe(
            "market_amount_total_cny",
            sum(amounts) if amounts else None,
            as_of_date=common_date,
            source_records=daily_records,
            valid_count=len(amounts),
            query_ids=daily_query_ids,
            warnings=(
                "QUERY_UNIVERSE_TOTAL_NOT_PROVEN_FULL_MARKET",
            ),
        ))
        add(self._observe(
            "turnover_rate_median_pct",
            statistics.median(turnover_rates)
            if turnover_rates else None,
            as_of_date=common_date,
            source_records=daily_records,
            valid_count=len(turnover_rates),
            query_ids=daily_query_ids,
        ))
        add(self._observe(
            "amount_field_coverage_ratio",
            len(amounts) / len(daily_records)
            if daily_records else None,
            as_of_date=common_date,
            source_records=daily_records,
            valid_count=len(amounts),
            query_ids=daily_query_ids,
        ))

        add(self._observe(
            "cross_section_return_std_pct",
            statistics.pstdev(daily_returns)
            if len(daily_returns) >= 2 else None,
            as_of_date=common_date,
            source_records=daily_records,
            valid_count=len(daily_returns),
            query_ids=daily_query_ids,
        ))
        add(self._observe(
            "intraday_range_median_pct",
            statistics.median(intraday_ranges)
            if intraday_ranges else None,
            as_of_date=common_date,
            source_records=daily_records,
            valid_count=len(intraday_ranges),
            query_ids=daily_query_ids,
        ))
        absolute_returns = [abs(value) for value in daily_returns]
        add(self._observe(
            "absolute_return_median_pct",
            statistics.median(absolute_returns)
            if absolute_returns else None,
            as_of_date=common_date,
            source_records=daily_records,
            valid_count=len(absolute_returns),
            query_ids=daily_query_ids,
        ))

        add(self._observe(
            "positive_industry_ratio",
            (
                sum(value > 0 for value in industry_returns)
                / len(industry_returns)
                if industry_returns else None
            ),
            as_of_date=common_date,
            source_records=industry_records,
            valid_count=len(industry_returns),
            query_ids=industry_query_ids,
        ))
        add(self._observe(
            "industry_return_std_pct",
            statistics.pstdev(industry_returns)
            if len(industry_returns) >= 2 else None,
            as_of_date=common_date,
            source_records=industry_records,
            valid_count=len(industry_returns),
            query_ids=industry_query_ids,
        ))
        add(self._observe(
            "positive_average_return_ratio",
            (
                sum(value > 0 for value in average_returns)
                / len(average_returns)
                if average_returns else None
            ),
            as_of_date=common_date,
            source_records=industry_records,
            valid_count=len(average_returns),
            query_ids=industry_query_ids,
        ))

        observed_ids = {item.feature_id for item in observations}
        required_ids = {
            item.feature_id
            for item in self.feature_spec.feature_definitions
            if item.family in self.feature_spec.required_feature_families
        }
        missing = tuple(sorted(required_ids - observed_ids))

        if missing:
            status = MarketStateFeatureStatus.BLOCKED
            propagated_warnings.append(
                "REQUIRED_FEATURES_MISSING_OR_INSUFFICIENT"
            )
            research_allowed = False
        elif (
            input_assessment.status
            is MarketStateInputStatus.READY_WITH_WARNINGS
            or propagated_warnings
            or any(item.warnings for item in observations)
        ):
            status = MarketStateFeatureStatus.READY_WITH_WARNINGS
            research_allowed = True
        else:
            status = MarketStateFeatureStatus.READY
            research_allowed = True

        return MarketStateFeatureSnapshot(
            status=status,
            feature_spec_version=self.feature_spec.spec_version,
            input_contract_version=(
                self.feature_spec.input_contract_version
            ),
            usage=self.feature_spec.allowed_usage,
            as_of_date=common_date,
            input_assessment_status=input_status,
            features=tuple(observations),
            missing_required_features=missing,
            warnings=tuple(dict.fromkeys(propagated_warnings)),
            research_feature_build_allowed=research_allowed,
            manual_decision_allowed=False,
            official_market_state_allowed=False,
            regime_label=None,
        )
