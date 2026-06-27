"""真实报告、交易日时效和启用配置到统一就绪度证据的覆盖层。

TASK_018B 已经能够从 StandardQueryResult 生成八维证据，但其中覆盖、
数据集级时效和生产启用状态需要独立证据。本模块只读取仓库内已提交的
JSON 报告和启用配置，将 COVERAGE、FRESHNESS、ACTIVATION 三个维度
替换为可审计的真实外部证据。

本模块不连接 DolphinDB，不读取 Raw 表，不执行数据库写入。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from enum import Enum
import json
from pathlib import Path
import re
from typing import Any, Iterable, Mapping

from .data_contracts import DataContractError
from .data_readiness import (
    EvidenceStatus,
    ReadinessDimension,
    ReadinessEvidence,
)
from .data_readiness_evidence import (
    EvidenceBuildContext,
    StandardQueryEvidenceBuilder,
)
from .standard_data_service import (
    ProviderDescriptor,
    StandardDataUsage,
    StandardQueryResult,
)

EXTERNAL_EVIDENCE_VERSION = "0.1.0"


def _require_text(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DataContractError(f"{field_name}不能为空。")
    return value.strip()


def _parse_date(value: Any, field_name: str) -> date:
    if isinstance(value, date):
        return value
    if not isinstance(value, str) or not value.strip():
        raise DataContractError(f"{field_name}不是有效日期。")
    try:
        return date.fromisoformat(value.strip()[:10])
    except ValueError as exc:
        raise DataContractError(
            f"{field_name}不是ISO日期：{value}"
        ) from exc


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DataContractError(f"无法加载JSON：{path}") from exc
    if not isinstance(payload, dict):
        raise DataContractError(f"JSON根节点必须是对象：{path}")
    return payload


def _json_path(
    payload: Mapping[str, Any],
    path: str,
) -> Any:
    current: Any = payload
    for part in _require_text(path, "json_path").split("."):
        if not isinstance(current, Mapping) or part not in current:
            raise DataContractError(
                f"报告缺少JSON路径：{path}"
            )
        current = current[part]
    return current


class ReportKind(str, Enum):
    DAILY_K_COVERAGE = "DAILY_K_COVERAGE"
    FUNDAMENTAL_PROFILE = "FUNDAMENTAL_PROFILE"
    DAILY_FUNDS_ACCEPTANCE = "DAILY_FUNDS_ACCEPTANCE"


@dataclass(frozen=True, slots=True)
class TradingCalendar:
    """A股交易日日历；周末关闭，节假日由权威配置给出。"""

    calendar_id: str
    year: int
    closed_dates: frozenset[date]
    source_title: str
    source_url: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "calendar_id",
            _require_text(self.calendar_id, "calendar_id"),
        )
        object.__setattr__(
            self,
            "source_title",
            _require_text(self.source_title, "source_title"),
        )
        object.__setattr__(
            self,
            "source_url",
            _require_text(self.source_url, "source_url"),
        )
        if not isinstance(self.year, int) or self.year < 1990:
            raise DataContractError("year无效。")
        for value in self.closed_dates:
            if not isinstance(value, date):
                raise DataContractError(
                    "closed_dates必须全部为date。"
                )
            if value.year != self.year:
                raise DataContractError(
                    "closed_dates只能包含配置年度日期。"
                )

    def is_trading_day(self, value: date) -> bool:
        if value.year != self.year:
            raise DataContractError(
                f"日期超出交易日历年度：{value}"
            )
        return (
            value.weekday() < 5
            and value not in self.closed_dates
        )

    def latest_trading_day(self, as_of_date: date) -> date:
        if as_of_date.year != self.year:
            raise DataContractError(
                "as_of_date超出交易日历年度。"
            )
        candidate = as_of_date
        for _ in range(370):
            if self.is_trading_day(candidate):
                return candidate
            candidate -= timedelta(days=1)
        raise DataContractError("无法解析最近交易日。")

    def trading_sessions_after(
        self,
        start_exclusive: date,
        end_inclusive: date,
    ) -> int:
        if end_inclusive.year != self.year:
            raise DataContractError(
                "交易日时效结束日期必须位于配置年度。"
            )
        if end_inclusive <= start_exclusive:
            return 0
        if start_exclusive.year == self.year:
            cursor = start_exclusive + timedelta(days=1)
        elif start_exclusive == date(self.year - 1, 12, 31):
            # 允许从上一年最后一天跨入当前年度。这样可处理
            # daily-funds-raw@2025-11-20..2025-12-31
            # 到2026证据截止日的交易日滞后，而不伪造2025节假日。
            cursor = date(self.year, 1, 1)
        else:
            raise DataContractError(
                "跨年度时效仅支持以上一年12月31日为起点。"
            )
        count = 0
        while cursor <= end_inclusive:
            if self.is_trading_day(cursor):
                count += 1
            cursor += timedelta(days=1)
        return count


@dataclass(frozen=True, slots=True)
class ActivationEntry:
    dataset_id: str
    enabled: bool
    activation_state: str
    allowed_usages: frozenset[StandardDataUsage]
    effective_from: date
    evidence_note: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "dataset_id",
            _require_text(self.dataset_id, "dataset_id"),
        )
        object.__setattr__(
            self,
            "activation_state",
            _require_text(
                self.activation_state,
                "activation_state",
            ),
        )
        object.__setattr__(
            self,
            "evidence_note",
            _require_text(
                self.evidence_note,
                "evidence_note",
            ),
        )
        usages: set[StandardDataUsage] = set()
        for value in self.allowed_usages:
            try:
                usage = (
                    value
                    if isinstance(value, StandardDataUsage)
                    else StandardDataUsage(value)
                )
            except ValueError as exc:
                raise DataContractError(
                    f"不支持的allowed_usage：{value}"
                ) from exc
            usages.add(usage)
        object.__setattr__(
            self,
            "allowed_usages",
            frozenset(usages),
        )


@dataclass(frozen=True, slots=True)
class DatasetEvidenceConfig:
    dataset_id: str
    report_kind: ReportKind
    report_paths: tuple[str, ...]
    coverage_scope: str
    max_current_lag_sessions: int
    max_manual_lag_sessions: int

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "dataset_id",
            _require_text(self.dataset_id, "dataset_id"),
        )
        kind = self.report_kind
        if isinstance(kind, str):
            try:
                kind = ReportKind(kind)
            except ValueError as exc:
                raise DataContractError(
                    f"不支持的report_kind：{kind}"
                ) from exc
        object.__setattr__(self, "report_kind", kind)
        paths = tuple(
            _require_text(item, "report_paths")
            for item in self.report_paths
        )
        if not paths or len(paths) != len(set(paths)):
            raise DataContractError(
                "report_paths不能为空或重复。"
            )
        object.__setattr__(self, "report_paths", paths)
        object.__setattr__(
            self,
            "coverage_scope",
            _require_text(
                self.coverage_scope,
                "coverage_scope",
            ),
        )
        if self.max_current_lag_sessions < 0:
            raise DataContractError(
                "max_current_lag_sessions不能为负。"
            )
        if self.max_manual_lag_sessions < 0:
            raise DataContractError(
                "max_manual_lag_sessions不能为负。"
            )


@dataclass(frozen=True, slots=True)
class ExternalEvidenceConfig:
    contract_version: str
    snapshot_id: str
    as_of_date: date
    calendar_path: str
    activation_path: str
    datasets: tuple[DatasetEvidenceConfig, ...]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "contract_version",
            _require_text(
                self.contract_version,
                "contract_version",
            ),
        )
        if self.contract_version != EXTERNAL_EVIDENCE_VERSION:
            raise DataContractError(
                "外部证据合同版本不兼容。"
            )
        object.__setattr__(
            self,
            "snapshot_id",
            _require_text(self.snapshot_id, "snapshot_id"),
        )
        object.__setattr__(
            self,
            "calendar_path",
            _require_text(self.calendar_path, "calendar_path"),
        )
        object.__setattr__(
            self,
            "activation_path",
            _require_text(
                self.activation_path,
                "activation_path",
            ),
        )
        ids = [item.dataset_id for item in self.datasets]
        if not ids or len(ids) != len(set(ids)):
            raise DataContractError(
                "datasets不能为空或dataset_id重复。"
            )

    def dataset(
        self,
        dataset_id: str,
    ) -> DatasetEvidenceConfig:
        key = _require_text(dataset_id, "dataset_id")
        for item in self.datasets:
            if item.dataset_id == key:
                return item
        raise DataContractError(
            f"外部证据配置未登记数据集：{key}"
        )


def load_trading_calendar(path: str | Path) -> TradingCalendar:
    calendar_path = Path(path)
    raw = _load_json(calendar_path)
    year = int(raw["year"])
    closed_dates: set[date] = set()
    for period in raw["closed_periods"]:
        start = _parse_date(period["start"], "closed_period.start")
        end = _parse_date(period["end"], "closed_period.end")
        if start > end:
            raise DataContractError(
                "交易所休市区间起止日期无效。"
            )
        cursor = start
        while cursor <= end:
            closed_dates.add(cursor)
            cursor += timedelta(days=1)
    return TradingCalendar(
        calendar_id=str(raw["calendar_id"]),
        year=year,
        closed_dates=frozenset(closed_dates),
        source_title=str(raw["source"]["title"]),
        source_url=str(raw["source"]["url"]),
    )


def load_activation_registry(
    path: str | Path,
) -> dict[str, ActivationEntry]:
    registry_path = Path(path)
    raw = _load_json(registry_path)
    entries: dict[str, ActivationEntry] = {}
    for item in raw["datasets"]:
        entry = ActivationEntry(
            dataset_id=str(item["dataset_id"]),
            enabled=bool(item["enabled"]),
            activation_state=str(item["activation_state"]),
            allowed_usages=frozenset(
                StandardDataUsage(value)
                for value in item["allowed_usages"]
            ),
            effective_from=_parse_date(
                item["effective_from"],
                "effective_from",
            ),
            evidence_note=str(item["evidence_note"]),
        )
        if entry.dataset_id in entries:
            raise DataContractError(
                f"启用配置dataset_id重复：{entry.dataset_id}"
            )
        entries[entry.dataset_id] = entry
    return entries


def load_external_evidence_config(
    path: str | Path,
) -> ExternalEvidenceConfig:
    config_path = Path(path)
    raw = _load_json(config_path)
    datasets = tuple(
        DatasetEvidenceConfig(
            dataset_id=str(item["dataset_id"]),
            report_kind=ReportKind(item["report_kind"]),
            report_paths=tuple(item["report_paths"]),
            coverage_scope=str(item["coverage_scope"]),
            max_current_lag_sessions=int(
                item["max_current_lag_sessions"]
            ),
            max_manual_lag_sessions=int(
                item["max_manual_lag_sessions"]
            ),
        )
        for item in raw["datasets"]
    )
    return ExternalEvidenceConfig(
        contract_version=str(raw["contract_version"]),
        snapshot_id=str(raw["snapshot_id"]),
        as_of_date=_parse_date(
            raw["as_of_date"],
            "as_of_date",
        ),
        calendar_path=str(raw["calendar_path"]),
        activation_path=str(raw["activation_path"]),
        datasets=datasets,
    )


class ReportBackedEvidenceResolver:
    """把已提交真实报告转换为覆盖、交易日时效和启用证据。"""

    def __init__(
        self,
        *,
        project_root: str | Path,
        config: ExternalEvidenceConfig,
        calendar: TradingCalendar,
        activations: Mapping[str, ActivationEntry],
    ) -> None:
        self.project_root = Path(project_root).resolve()
        self.config = config
        self.calendar = calendar
        self.activations = dict(activations)
        config_ids = {
            item.dataset_id
            for item in self.config.datasets
        }
        if config_ids != set(self.activations):
            raise DataContractError(
                "外部证据配置与启用注册表数据集集合不一致。"
            )
        self._reports: dict[str, dict[str, Any]] = {}

    @classmethod
    def from_project(
        cls,
        *,
        project_root: str | Path,
        config_path: str | Path,
    ) -> "ReportBackedEvidenceResolver":
        root = Path(project_root).resolve()
        config_file = Path(config_path)
        if not config_file.is_absolute():
            config_file = root / config_file
        config = load_external_evidence_config(config_file)
        calendar = load_trading_calendar(
            root / config.calendar_path
        )
        activations = load_activation_registry(
            root / config.activation_path
        )
        return cls(
            project_root=root,
            config=config,
            calendar=calendar,
            activations=activations,
        )

    def _report(self, relative_path: str) -> dict[str, Any]:
        key = _require_text(relative_path, "report_path")
        if key not in self._reports:
            self._reports[key] = _load_json(
                self.project_root / key
            )
        return self._reports[key]

    @staticmethod
    def _dataset_row(
        report: Mapping[str, Any],
        dataset_id: str,
    ) -> Mapping[str, Any]:
        rows = report.get("datasets")
        if not isinstance(rows, list):
            raise DataContractError(
                "验收报告datasets不是列表。"
            )
        matches = [
            row
            for row in rows
            if isinstance(row, Mapping)
            and str(row.get("dataset_id")) == dataset_id
        ]
        if len(matches) != 1:
            raise DataContractError(
                f"验收报告中{dataset_id}应恰好出现一次。"
            )
        return matches[0]

    def _refs(
        self,
        dataset: DatasetEvidenceConfig,
        extra: Iterable[str] = (),
    ) -> tuple[str, ...]:
        refs = [
            f"external_snapshot:{self.config.snapshot_id}",
            f"calendar:{self.calendar.calendar_id}",
            *(
                f"report:{path}"
                for path in dataset.report_paths
            ),
            *extra,
        ]
        return tuple(dict.fromkeys(refs))

    def coverage_evidence(
        self,
        dataset_id: str,
    ) -> ReadinessEvidence:
        dataset = self.config.dataset(dataset_id)

        if dataset.report_kind is ReportKind.DAILY_K_COVERAGE:
            report = self._report(dataset.report_paths[0])
            summary = report["database_summary"]
            evaluation = report["coverage_evaluation"]
            passed = (
                report.get("overall_status") == "PASSED"
                and not bool(report.get("blocks_downstream"))
                and bool(
                    evaluation.get(
                        "database_matches_declared_cutoff"
                    )
                )
                and int(summary.get("row_count", 0)) > 0
                and int(summary.get("entity_count", 0)) > 0
            )
            status = (
                EvidenceStatus.PASSED
                if passed
                else EvidenceStatus.FAILED
            )
            code = (
                "FULL_DATABASE_SNAPSHOT_COVERAGE_PROVEN"
                if passed
                else "DAILY_K_COVERAGE_REPORT_FAILED"
            )
            message = (
                "日K数据库边界、实体数和声明截止日由真实覆盖报告证明。"
                if passed
                else "日K真实覆盖报告未通过。"
            )
            metrics = {
                "coverage_scope": dataset.coverage_scope,
                "row_count": int(summary.get("row_count", 0)),
                "entity_count": int(
                    summary.get("entity_count", 0)
                ),
                "min_data_date": summary.get("min_data_date"),
                "max_data_date": summary.get("max_data_date"),
                "declared_cutoff_date": evaluation.get(
                    "declared_cutoff_date"
                ),
                "database_matches_declared_cutoff": bool(
                    evaluation.get(
                        "database_matches_declared_cutoff"
                    )
                ),
            }

        elif (
            dataset.report_kind
            is ReportKind.FUNDAMENTAL_PROFILE
        ):
            report = self._report(dataset.report_paths[0])
            summary = report["summary"]
            duplicate = report["duplicate_summary"]
            passed = (
                bool(report.get("allows_current_snapshot_research"))
                and int(summary.get("row_count", 0)) > 0
                and int(summary.get("stock_count", 0)) > 0
                and int(
                    duplicate.get(
                        "duplicate_extra_row_count",
                        -1,
                    )
                )
                == 0
            )
            status = (
                EvidenceStatus.PASSED
                if passed
                else EvidenceStatus.FAILED
            )
            code = (
                "CURRENT_FUNDAMENTAL_SNAPSHOT_COVERAGE_PROVEN"
                if passed
                else "FUNDAMENTAL_COVERAGE_REPORT_FAILED"
            )
            message = (
                "基本面当前快照的股票数、行数和主键唯一性已由真实剖析报告证明。"
                if passed
                else "基本面当前快照覆盖报告未通过。"
            )
            metrics = {
                "coverage_scope": dataset.coverage_scope,
                "row_count": int(summary.get("row_count", 0)),
                "entity_count": int(
                    summary.get("stock_count", 0)
                ),
                "min_snapshot_date": summary.get(
                    "min_snapshot_date"
                ),
                "max_snapshot_date": summary.get(
                    "max_snapshot_date"
                ),
                "profile_status": report.get("overall_status"),
                "allows_current_snapshot_research": bool(
                    report.get(
                        "allows_current_snapshot_research"
                    )
                ),
                "duplicate_extra_row_count": int(
                    duplicate.get(
                        "duplicate_extra_row_count",
                        -1,
                    )
                ),
            }

        else:
            canonical_report = self._report(
                dataset.report_paths[0]
            )
            service_report = self._report(
                dataset.report_paths[1]
            )
            canonical_row = self._dataset_row(
                canonical_report,
                dataset_id,
            )
            service_row = self._dataset_row(
                service_report,
                dataset_id,
            )
            accepted = (
                canonical_report.get("overall_status")
                == "PASSED_WITH_WARNINGS"
                and service_report.get("overall_status")
                == "PASSED_WITH_WARNINGS"
                and int(canonical_row.get("result_count", 0))
                > 0
                and int(service_row.get("result_count", 0))
                > 0
            )
            status = (
                EvidenceStatus.WARNING
                if accepted
                else EvidenceStatus.FAILED
            )
            code = (
                "DATE_RANGE_AND_REAL_SAMPLE_ACCEPTED"
                if accepted
                else "DAILY_FUNDS_ACCEPTANCE_FAILED"
            )
            message = (
                "七类快照已通过真实Canonical和统一入口抽样验收，"
                "但尚无完整实体全集覆盖证明。"
                if accepted
                else "七类快照真实验收未通过。"
            )
            metrics = {
                "coverage_scope": dataset.coverage_scope,
                "coverage_version": canonical_report.get(
                    "coverage_version"
                ),
                "canonical_result_count": int(
                    canonical_row.get("result_count", 0)
                ),
                "unified_result_count": int(
                    service_row.get("result_count", 0)
                ),
                "selector_mode": service_row.get(
                    "selector_mode"
                ),
                "exhaustive_entity_coverage_proven": False,
            }

        return ReadinessEvidence(
            dimension=ReadinessDimension.COVERAGE,
            status=status,
            code=code,
            message=message,
            metrics=metrics,
            evidence_refs=self._refs(dataset),
        )

    def _latest_available_date(
        self,
        dataset: DatasetEvidenceConfig,
    ) -> date:
        if dataset.report_kind is ReportKind.DAILY_K_COVERAGE:
            report = self._report(dataset.report_paths[0])
            return _parse_date(
                _json_path(
                    report,
                    "coverage_evaluation.database_max_date",
                ),
                "daily_k.database_max_date",
            )

        if (
            dataset.report_kind
            is ReportKind.FUNDAMENTAL_PROFILE
        ):
            report = self._report(dataset.report_paths[0])
            return _parse_date(
                _json_path(
                    report,
                    "summary.max_snapshot_date",
                ),
                "fundamental.max_snapshot_date",
            )

        report = self._report(dataset.report_paths[0])
        coverage_version = str(report["coverage_version"])
        match = re.search(
            r"@(\d{4}-\d{2}-\d{2})\.\.(\d{4}-\d{2}-\d{2})$",
            coverage_version,
        )
        if match is None:
            raise DataContractError(
                "无法从七类快照coverage_version解析截止日。"
            )
        return _parse_date(
            match.group(2),
            "daily_funds.coverage_end_date",
        )

    def freshness_evidence(
        self,
        dataset_id: str,
        usage: StandardDataUsage,
        as_of_date: date,
    ) -> ReadinessEvidence:
        dataset = self.config.dataset(dataset_id)
        latest = self._latest_available_date(dataset)
        expected = self.calendar.latest_trading_day(as_of_date)

        historical = usage in {
            StandardDataUsage.STRICT_HISTORICAL_BACKTEST,
            StandardDataUsage.HISTORICAL_MODEL_TRAINING,
        }
        if historical:
            return ReadinessEvidence(
                dimension=ReadinessDimension.FRESHNESS,
                status=EvidenceStatus.PASSED,
                code=(
                    "FIXED_HISTORICAL_RANGE_CURRENT_FRESHNESS_"
                    "NOT_APPLICABLE"
                ),
                message=(
                    "固定历史区间的准入由覆盖、时点和语义证据决定，"
                    "不以当前数据是否最新作为阻断条件。"
                ),
                metrics={
                    "latest_available_date": latest,
                    "expected_latest_trading_date": expected,
                    "trading_session_lag": (
                        self.calendar.trading_sessions_after(
                            latest,
                            expected,
                        )
                    ),
                    "usage": usage.value,
                },
                evidence_refs=self._refs(dataset),
            )

        lag = self.calendar.trading_sessions_after(
            latest,
            expected,
        )
        threshold = (
            dataset.max_manual_lag_sessions
            if usage
            is StandardDataUsage.MANUAL_DECISION_SUPPORT
            else dataset.max_current_lag_sessions
        )
        passed = latest <= expected and lag <= threshold
        status = (
            EvidenceStatus.PASSED
            if passed
            else EvidenceStatus.WARNING
        )
        code = (
            "TRADING_SESSION_FRESHNESS_WITHIN_SLA"
            if passed
            else "TRADING_SESSION_LAG_EXCEEDS_SLA"
        )
        message = (
            "真实报告截止日满足交易日时效阈值。"
            if passed
            else "真实报告截止日落后于用途对应的交易日时效阈值。"
        )
        return ReadinessEvidence(
            dimension=ReadinessDimension.FRESHNESS,
            status=status,
            code=code,
            message=message,
            metrics={
                "latest_available_date": latest,
                "expected_latest_trading_date": expected,
                "trading_session_lag": lag,
                "maximum_allowed_trading_session_lag": (
                    threshold
                ),
                "usage": usage.value,
                "calendar_source_title": (
                    self.calendar.source_title
                ),
            },
            evidence_refs=self._refs(dataset),
        )

    def activation_evidence(
        self,
        dataset_id: str,
        usage: StandardDataUsage,
        as_of_date: date,
    ) -> ReadinessEvidence:
        try:
            entry = self.activations[dataset_id]
        except KeyError as exc:
            raise DataContractError(
                f"启用注册表未登记数据集：{dataset_id}"
            ) from exc

        effective = entry.effective_from <= as_of_date
        allowed = (
            entry.enabled
            and effective
            and usage in entry.allowed_usages
        )
        status = (
            EvidenceStatus.PASSED
            if allowed
            else EvidenceStatus.FAILED
        )
        code = (
            "DATASET_USAGE_ACTIVATION_VERIFIED"
            if allowed
            else "DATASET_USAGE_NOT_ACTIVATED"
        )
        message = (
            "独立启用注册表确认该数据集可用于当前用途。"
            if allowed
            else "独立启用注册表未批准该数据集用于当前用途。"
        )
        dataset = self.config.dataset(dataset_id)
        return ReadinessEvidence(
            dimension=ReadinessDimension.ACTIVATION,
            status=status,
            code=code,
            message=message,
            metrics={
                "enabled": entry.enabled,
                "effective": effective,
                "activation_state": entry.activation_state,
                "allowed_usages": sorted(
                    item.value
                    for item in entry.allowed_usages
                ),
                "requested_usage": usage.value,
                "effective_from": entry.effective_from,
                "evidence_note": entry.evidence_note,
            },
            evidence_refs=self._refs(
                dataset,
                (
                    "config:"
                    + self.config.activation_path,
                ),
            ),
        )

    def resolve(
        self,
        *,
        dataset_id: str,
        usage: StandardDataUsage,
        as_of_date: date | None = None,
    ) -> tuple[ReadinessEvidence, ...]:
        resolved_as_of = as_of_date or self.config.as_of_date
        return (
            self.coverage_evidence(dataset_id),
            self.freshness_evidence(
                dataset_id,
                usage,
                resolved_as_of,
            ),
            self.activation_evidence(
                dataset_id,
                usage,
                resolved_as_of,
            ),
        )


class ExternalEvidenceOverlayBuilder(
    StandardQueryEvidenceBuilder
):
    """在TASK_018B八维证据上覆盖三项真实外部证据。"""

    def __init__(
        self,
        *,
        base_rules: Any,
        resolver: ReportBackedEvidenceResolver,
    ) -> None:
        super().__init__(base_rules)
        self.resolver = resolver

    def build(
        self,
        result: StandardQueryResult,
        descriptor: ProviderDescriptor,
        context: EvidenceBuildContext | None = None,
    ) -> tuple[ReadinessEvidence, ...]:
        base = list(
            super().build(result, descriptor, context)
        )
        overrides = {
            item.dimension: item
            for item in self.resolver.resolve(
                dataset_id=result.query.dataset_id,
                usage=result.query.usage,
                as_of_date=result.query.as_of_date,
            )
        }
        output = tuple(
            overrides.get(item.dimension, item)
            for item in base
        )
        dimensions = {
            item.dimension
            for item in output
        }
        if dimensions != set(ReadinessDimension):
            raise DataContractError(
                "外部证据覆盖后必须完整保留八个维度。"
            )
        return output
