"""TASK_019C真实市场状态特征验收的只读计划与报告合同。"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from .data_contracts import DataContractError
from .standard_data_service import (
    ENTITY_SELECTOR_MODE,
    INSTRUMENT_SELECTOR_MODE,
    StandardDataQuery,
    StandardDataUsage,
)


REAL_FEATURE_ACCEPTANCE_PLAN_VERSION = "0.1.0"
REAL_FEATURE_ACCEPTANCE_MODE = (
    "REAL_READONLY_MARKET_STATE_FEATURE_ACCEPTANCE"
)
REAL_FEATURE_ACCEPTANCE_UNIVERSE_SCOPE = (
    "DETERMINISTIC_CAPPED_REAL_QUERY_UNIVERSE"
)


def _require_text(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DataContractError(f"{field_name}不能为空。")
    return value.strip()


def _require_positive_int(value: int, field_name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise DataContractError(f"{field_name}必须是正整数。")
    return value


def _coerce_date(value: Any) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    converted = getattr(value, "to_pydatetime", lambda: None)()
    if isinstance(converted, datetime):
        return converted.date()
    if isinstance(converted, date):
        return converted
    text = str(value).strip().replace(".", "-")
    try:
        return date.fromisoformat(text[:10])
    except ValueError as exc:
        raise DataContractError(f"无法解析日期：{value!r}") from exc


def _ddb_date_literal(value: date) -> str:
    if not isinstance(value, date):
        raise DataContractError("DolphinDB日期必须是date。")
    return value.strftime("%Y.%m.%d")


def _safe_identifier(value: str, field_name: str) -> str:
    text = _require_text(value, field_name)
    if not all(char.isalnum() or char == "_" for char in text):
        raise DataContractError(f"{field_name}不是安全标识符。")
    return text


def _safe_database_uri(value: str) -> str:
    text = _require_text(value, "database_uri")
    if '"' in text or "\n" in text or "\r" in text:
        raise DataContractError("database_uri包含不安全字符。")
    return text


def _safe_filter(value: str | None) -> str | None:
    if value is None:
        return None
    text = _require_text(value, "dataset_filter")
    forbidden = (";", "\n", "\r", "drop ", "delete ", "update ", "insert ")
    lowered = text.lower()
    if any(token in lowered for token in forbidden):
        raise DataContractError("dataset_filter包含不安全内容。")
    return text


@dataclass(frozen=True, slots=True)
class RealFeatureDatasetPlan:
    dataset_id: str
    canonical_object: str
    selector_mode: str
    selector_limit: int
    minimum_result_count: int
    limit_per_selector: int

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "dataset_id",
            _require_text(self.dataset_id, "dataset_id"),
        )
        object.__setattr__(
            self,
            "canonical_object",
            _require_text(
                self.canonical_object,
                "canonical_object",
            ),
        )
        mode = _require_text(
            self.selector_mode,
            "selector_mode",
        ).upper()
        if mode not in {
            INSTRUMENT_SELECTOR_MODE,
            ENTITY_SELECTOR_MODE,
        }:
            raise DataContractError("selector_mode不受支持。")
        object.__setattr__(self, "selector_mode", mode)
        object.__setattr__(
            self,
            "selector_limit",
            _require_positive_int(
                self.selector_limit,
                "selector_limit",
            ),
        )
        object.__setattr__(
            self,
            "minimum_result_count",
            _require_positive_int(
                self.minimum_result_count,
                "minimum_result_count",
            ),
        )
        object.__setattr__(
            self,
            "limit_per_selector",
            _require_positive_int(
                self.limit_per_selector,
                "limit_per_selector",
            ),
        )
        if self.limit_per_selector > 5_000:
            raise DataContractError(
                "limit_per_selector不能超过5000。"
            )


@dataclass(frozen=True, slots=True)
class RealFeatureAcceptancePlan:
    contract_version: str
    task_id: str
    mode: str
    as_of_date: date
    external_evidence_config: str
    readiness_policy: str
    evidence_rules: str
    market_state_input_contract: str
    market_state_feature_spec: str
    required_datasets: tuple[RealFeatureDatasetPlan, ...]
    candidate_dataset_id: str
    candidate_date_row_scan_limit: int
    maximum_candidate_dates_to_check: int
    common_date_policy: str
    universe_scope: str
    selector_order: str
    claim_full_market_coverage: bool
    acceptance_invariants: Mapping[str, Any]

    def __post_init__(self) -> None:
        for field_name in (
            "contract_version",
            "task_id",
            "mode",
            "external_evidence_config",
            "readiness_policy",
            "evidence_rules",
            "market_state_input_contract",
            "market_state_feature_spec",
            "candidate_dataset_id",
            "common_date_policy",
            "universe_scope",
            "selector_order",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_text(
                    getattr(self, field_name),
                    field_name,
                ),
            )
        if self.contract_version != REAL_FEATURE_ACCEPTANCE_PLAN_VERSION:
            raise DataContractError("TASK_019C验收计划版本不兼容。")
        if self.task_id != "TASK_019C":
            raise DataContractError("TASK_019C验收计划task_id异常。")
        if self.mode != REAL_FEATURE_ACCEPTANCE_MODE:
            raise DataContractError("TASK_019C验收模式异常。")
        if not isinstance(self.as_of_date, date):
            raise DataContractError("as_of_date必须是date。")
        if len(self.required_datasets) != 2:
            raise DataContractError("TASK_019C必须且只能登记两个必需数据集。")
        ids = {item.dataset_id for item in self.required_datasets}
        if ids != {"a_stock_daily_k", "hy"}:
            raise DataContractError("TASK_019C必需数据集必须是日K和行业快照。")
        if self.candidate_dataset_id != "hy":
            raise DataContractError("共同日期候选必须来自hy。")
        object.__setattr__(
            self,
            "candidate_date_row_scan_limit",
            _require_positive_int(
                self.candidate_date_row_scan_limit,
                "candidate_date_row_scan_limit",
            ),
        )
        object.__setattr__(
            self,
            "maximum_candidate_dates_to_check",
            _require_positive_int(
                self.maximum_candidate_dates_to_check,
                "maximum_candidate_dates_to_check",
            ),
        )
        if self.common_date_policy != "LATEST_COMMON_TRADE_DATE":
            raise DataContractError("共同日期政策异常。")
        if self.universe_scope != REAL_FEATURE_ACCEPTANCE_UNIVERSE_SCOPE:
            raise DataContractError("验收证券集合范围异常。")
        if self.selector_order != "SOURCE_ENTITY_ID_ASC":
            raise DataContractError("选择器排序政策异常。")
        if self.claim_full_market_coverage:
            raise DataContractError(
                "TASK_019C验收集合不得声明全市场覆盖。"
            )
        if not isinstance(self.acceptance_invariants, Mapping):
            raise DataContractError("acceptance_invariants必须是对象。")

    def dataset(self, dataset_id: str) -> RealFeatureDatasetPlan:
        key = _require_text(dataset_id, "dataset_id")
        for item in self.required_datasets:
            if item.dataset_id == key:
                return item
        raise DataContractError(f"验收计划未登记数据集：{key}")


@dataclass(frozen=True, slots=True)
class ReadonlySourceDescriptor:
    dataset_id: str
    database_uri: str
    table_name: str
    entity_field: str
    date_field: str
    dataset_filter: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "dataset_id",
            _require_text(self.dataset_id, "dataset_id"),
        )
        object.__setattr__(
            self,
            "database_uri",
            _safe_database_uri(self.database_uri),
        )
        object.__setattr__(
            self,
            "table_name",
            _safe_identifier(self.table_name, "table_name"),
        )
        object.__setattr__(
            self,
            "entity_field",
            _safe_identifier(self.entity_field, "entity_field"),
        )
        object.__setattr__(
            self,
            "date_field",
            _safe_identifier(self.date_field, "date_field"),
        )
        object.__setattr__(
            self,
            "dataset_filter",
            _safe_filter(self.dataset_filter),
        )

    @property
    def table_ref(self) -> str:
        return (
            f'loadTable("{self.database_uri}", '
            f'`{self.table_name})'
        )


def load_real_feature_acceptance_plan(
    path: str | Path,
) -> RealFeatureAcceptancePlan:
    plan_path = Path(path)
    try:
        raw = json.loads(plan_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DataContractError(
            f"无法加载TASK_019C验收计划：{plan_path}"
        ) from exc
    if not isinstance(raw, dict):
        raise DataContractError("TASK_019C验收计划根节点必须是对象。")
    discovery = raw["common_date_discovery"]
    universe = raw["universe_policy"]
    return RealFeatureAcceptancePlan(
        contract_version=str(raw["contract_version"]),
        task_id=str(raw["task_id"]),
        mode=str(raw["mode"]),
        as_of_date=_coerce_date(raw["as_of_date"]),
        external_evidence_config=str(
            raw["external_evidence_config"]
        ),
        readiness_policy=str(raw["readiness_policy"]),
        evidence_rules=str(raw["evidence_rules"]),
        market_state_input_contract=str(
            raw["market_state_input_contract"]
        ),
        market_state_feature_spec=str(
            raw["market_state_feature_spec"]
        ),
        required_datasets=tuple(
            RealFeatureDatasetPlan(
                dataset_id=str(item["dataset_id"]),
                canonical_object=str(item["canonical_object"]),
                selector_mode=str(item["selector_mode"]),
                selector_limit=int(item["selector_limit"]),
                minimum_result_count=int(
                    item["minimum_result_count"]
                ),
                limit_per_selector=int(
                    item["limit_per_selector"]
                ),
            )
            for item in raw["required_datasets"]
        ),
        candidate_dataset_id=str(
            discovery["candidate_dataset_id"]
        ),
        candidate_date_row_scan_limit=int(
            discovery["candidate_date_row_scan_limit"]
        ),
        maximum_candidate_dates_to_check=int(
            discovery["maximum_candidate_dates_to_check"]
        ),
        common_date_policy=str(discovery["policy"]),
        universe_scope=str(universe["scope"]),
        selector_order=str(universe["selector_order"]),
        claim_full_market_coverage=bool(
            universe["claim_full_market_coverage"]
        ),
        acceptance_invariants=dict(raw["acceptance_invariants"]),
    )


def build_recent_date_rows_query(
    source: ReadonlySourceDescriptor,
    row_limit: int,
) -> str:
    limit = _require_positive_int(row_limit, "row_limit")
    where = (
        f" where {source.dataset_filter}"
        if source.dataset_filter
        else ""
    )
    return (
        f"select top {limit} {source.date_field} "
        f"from {source.table_ref}"
        f"{where} "
        f"order by {source.date_field} desc"
    )


def build_date_presence_query(
    source: ReadonlySourceDescriptor,
    target_date: date,
) -> str:
    where_parts = [
        f"{source.date_field} = {_ddb_date_literal(target_date)}"
    ]
    if source.dataset_filter:
        where_parts.insert(0, source.dataset_filter)
    return (
        f"select top 1 {source.date_field} "
        f"from {source.table_ref} "
        f"where {' and '.join(where_parts)}"
    )


def build_selector_rows_query(
    source: ReadonlySourceDescriptor,
    target_date: date,
    selector_limit: int,
) -> str:
    limit = _require_positive_int(
        selector_limit,
        "selector_limit",
    )
    where_parts = [
        f"{source.date_field} = {_ddb_date_literal(target_date)}"
    ]
    if source.dataset_filter:
        where_parts.insert(0, source.dataset_filter)
    return (
        f"select top {limit} {source.entity_field} "
        f"from {source.table_ref} "
        f"where {' and '.join(where_parts)} "
        f"order by {source.entity_field}"
    )


def assert_readonly_query(script: str) -> None:
    text = _require_text(script, "script")
    lowered = " ".join(text.lower().split())
    if not lowered.startswith("select "):
        raise DataContractError("TASK_019C只允许SELECT查询。")
    forbidden = (
        " insert ",
        " update ",
        " delete ",
        " drop ",
        " create ",
        " alter ",
        " append!",
        " tableinsert",
        " save",
        " write",
    )
    padded = f" {lowered} "
    if any(token in padded for token in forbidden):
        raise DataContractError("查询包含潜在写操作。")


def unique_dates_from_rows(
    rows: Sequence[Mapping[str, Any]],
    date_field: str,
    maximum_count: int,
) -> tuple[date, ...]:
    field = _safe_identifier(date_field, "date_field")
    maximum = _require_positive_int(
        maximum_count,
        "maximum_count",
    )
    values: list[date] = []
    seen: set[date] = set()
    for row in rows:
        if field not in row or row[field] is None:
            continue
        value = _coerce_date(row[field])
        if value in seen:
            continue
        seen.add(value)
        values.append(value)
        if len(values) >= maximum:
            break
    return tuple(sorted(values, reverse=True))


def unique_selectors_from_rows(
    rows: Sequence[Mapping[str, Any]],
    entity_field: str,
    maximum_count: int,
) -> tuple[str, ...]:
    field = _safe_identifier(entity_field, "entity_field")
    maximum = _require_positive_int(
        maximum_count,
        "maximum_count",
    )
    values: list[str] = []
    seen: set[str] = set()
    for row in rows:
        raw = row.get(field)
        if raw is None:
            continue
        text = str(raw).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        values.append(text)
        if len(values) >= maximum:
            break
    return tuple(values)


def build_feature_acceptance_query(
    dataset_plan: RealFeatureDatasetPlan,
    selectors: Sequence[str],
    common_date: date,
    as_of_date: date,
) -> StandardDataQuery:
    selector_values = tuple(
        _require_text(value, "selector")
        for value in selectors
    )
    if not selector_values:
        raise DataContractError("真实验收选择器不能为空。")
    if len(selector_values) > dataset_plan.selector_limit:
        raise DataContractError("选择器数量超过验收计划限制。")
    if common_date > as_of_date:
        raise DataContractError("共同交易日不能晚于as_of_date。")
    instrument_ids = (
        selector_values
        if dataset_plan.selector_mode
        == INSTRUMENT_SELECTOR_MODE
        else ()
    )
    entity_ids = (
        selector_values
        if dataset_plan.selector_mode
        == ENTITY_SELECTOR_MODE
        else ()
    )
    return StandardDataQuery(
        dataset_id=dataset_plan.dataset_id,
        canonical_object=dataset_plan.canonical_object,
        instrument_ids=instrument_ids,
        entity_ids=entity_ids,
        start_date=common_date,
        end_date=common_date,
        as_of_date=as_of_date,
        usage=StandardDataUsage.CURRENT_SNAPSHOT_RESEARCH,
        limit_per_instrument=dataset_plan.limit_per_selector,
        include_source_extensions=True,
        include_quality_flags=True,
        include_lineage=True,
    )


def validate_real_feature_acceptance_report(
    report: Mapping[str, Any],
    plan: RealFeatureAcceptancePlan,
) -> tuple[str, ...]:
    issues: list[str] = []
    expected = plan.acceptance_invariants

    checks = (
        (report.get("task_id") == plan.task_id, "task_id"),
        (report.get("mode") == plan.mode, "mode"),
        (
            int(report.get("required_dataset_count", -1))
            == int(expected["required_dataset_count"]),
            "required_dataset_count",
        ),
        (
            int(report.get("required_feature_family_count", -1))
            == int(expected["required_feature_family_count"]),
            "required_feature_family_count",
        ),
        (
            int(report.get("feature_definition_count", -1))
            == int(expected["feature_definition_count"]),
            "feature_definition_count",
        ),
        (
            int(report.get("generated_feature_count", -1))
            == int(expected["generated_feature_count"]),
            "generated_feature_count",
        ),
        (
            int(report.get("unique_source_query_id_count", -1))
            == int(expected["unique_source_query_id_count"]),
            "unique_source_query_id_count",
        ),
        (
            bool(report.get("database_connection_attempted"))
            is bool(expected["database_connection_attempted"]),
            "database_connection_attempted",
        ),
        (
            bool(report.get("database_readonly_query_mode"))
            is bool(expected["database_readonly_query_mode"]),
            "database_readonly_query_mode",
        ),
        (
            int(report.get("write_operation_count", -1))
            == int(expected["database_write_operation_count"]),
            "write_operation_count",
        ),
        (
            bool(report.get("manual_decision_allowed"))
            is bool(expected["manual_decision_allowed"]),
            "manual_decision_allowed",
        ),
        (
            bool(report.get("official_market_state_allowed"))
            is bool(expected["official_market_state_allowed"]),
            "official_market_state_allowed",
        ),
        (
            report.get("regime_label") is expected["regime_label"],
            "regime_label",
        ),
        (
            report.get("universe_scope") == plan.universe_scope,
            "universe_scope",
        ),
        (
            report.get("claim_full_market_coverage") is False,
            "claim_full_market_coverage",
        ),
        (
            report.get("input_assessment_status")
            in {"READY", "READY_WITH_WARNINGS"},
            "input_assessment_status",
        ),
        (
            report.get("feature_snapshot_status")
            in {"READY", "READY_WITH_WARNINGS"},
            "feature_snapshot_status",
        ),
        (
            bool(report.get("research_feature_build_allowed")),
            "research_feature_build_allowed",
        ),
        (
            bool(report.get("common_trade_date")),
            "common_trade_date",
        ),
    )
    for passed, name in checks:
        if not passed:
            issues.append(name)

    query_summaries = report.get("query_summaries", [])
    if not isinstance(query_summaries, list):
        issues.append("query_summaries")
    else:
        by_dataset = {
            str(item.get("dataset_id")): item
            for item in query_summaries
            if isinstance(item, Mapping)
        }
        for dataset_plan in plan.required_datasets:
            summary = by_dataset.get(dataset_plan.dataset_id)
            if summary is None:
                issues.append(
                    f"query_summary:{dataset_plan.dataset_id}"
                )
                continue
            if int(summary.get("result_count", -1)) < (
                dataset_plan.minimum_result_count
            ):
                issues.append(
                    f"minimum_result_count:{dataset_plan.dataset_id}"
                )
            if bool(summary.get("blocks_downstream")):
                issues.append(
                    f"query_blocked:{dataset_plan.dataset_id}"
                )

    features = report.get("features", [])
    if not isinstance(features, list):
        issues.append("features")
    else:
        feature_ids = [
            str(item.get("feature_id"))
            for item in features
            if isinstance(item, Mapping)
        ]
        if len(feature_ids) != len(set(feature_ids)):
            issues.append("duplicate_feature_ids")
        if any(
            item.get("regime_label") is not None
            for item in features
            if isinstance(item, Mapping)
        ):
            issues.append("feature_regime_label")

    return tuple(dict.fromkeys(issues))


def report_to_json_safe(value: Any) -> Any:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, tuple):
        return [report_to_json_safe(item) for item in value]
    if isinstance(value, list):
        return [report_to_json_safe(item) for item in value]
    if isinstance(value, Mapping):
        return {
            str(key): report_to_json_safe(item)
            for key, item in value.items()
        }
    return value
