"""TASK_020B：通用Provider插件协议、发现结果和多来源路由。"""
from __future__ import annotations

import json
import math
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping, Protocol, runtime_checkable

from .data_contracts import DataContractError
from .provider_capabilities import (
    CapabilityImplementationStatus,
    ProviderCapabilityMatrix,
    ProviderDiscoveryStatus,
    ProviderLifecycle,
)


SECRET_REFERENCE_PREFIXES = (
    "none://",
    "env://",
    "keyring://",
    "secret-manager://",
    "interactive://",
)

_EXECUTION_CAPABILITIES = {
    "ORDER_SUBMIT",
    "ORDER_CANCEL",
    "TRADE_CONFIRMATION",
}


class PluginRegistrationStatus(str, Enum):
    REGISTERED_TARGET = "REGISTERED_TARGET"
    LEGACY_BRIDGE_REQUIRED = "LEGACY_BRIDGE_REQUIRED"
    DISCOVERY_PENDING = "DISCOVERY_PENDING"
    DISCOVERY_COMPLETE = "DISCOVERY_COMPLETE"
    AVAILABLE = "AVAILABLE"
    SUSPENDED = "SUSPENDED"
    FAILED = "FAILED"


class DiscoveryOutcome(str, Enum):
    NOT_RUN = "NOT_RUN"
    PARTIAL = "PARTIAL"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"


class AuthenticationReferenceKind(str, Enum):
    NONE = "NONE"
    ENVIRONMENT_VARIABLE = "ENVIRONMENT_VARIABLE"
    OS_KEYRING = "OS_KEYRING"
    EXTERNAL_SECRET_MANAGER = "EXTERNAL_SECRET_MANAGER"
    INTERACTIVE_SESSION = "INTERACTIVE_SESSION"


class PolicyEvidenceStatus(str, Enum):
    UNKNOWN = "UNKNOWN"
    CONTRACT = "CONTRACT"
    OBSERVED = "OBSERVED"
    VENDOR_DOCUMENTATION = "VENDOR_DOCUMENTATION"


class PaginationMode(str, Enum):
    NONE = "NONE"
    PAGE_NUMBER = "PAGE_NUMBER"
    OFFSET_LIMIT = "OFFSET_LIMIT"
    CURSOR = "CURSOR"
    ITERATOR = "ITERATOR"


class SubscriptionMode(str, Enum):
    NONE = "NONE"
    POLLING = "POLLING"
    CALLBACK = "CALLBACK"
    STREAM = "STREAM"


class LicenseDecision(str, Enum):
    UNKNOWN = "UNKNOWN"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    ALLOWED = "ALLOWED"
    DENIED = "DENIED"


class ProviderHealthStatus(str, Enum):
    UNKNOWN = "UNKNOWN"
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    UNAVAILABLE = "UNAVAILABLE"


class RouteDecision(str, Enum):
    ELIGIBLE = "ELIGIBLE"
    INELIGIBLE = "INELIGIBLE"


def _require_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DataContractError(f"{field_name}不能为空。")
    return value.strip()


def _optional_text(value: Any, field_name: str) -> str | None:
    if value is None:
        return None
    return _require_text(value, field_name)


def _positive_int(value: Any, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise DataContractError(f"{field_name}必须是正整数。")
    return value


def _nonnegative_int(value: Any, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise DataContractError(f"{field_name}必须是非负整数。")
    return value


def _finite(value: Any, field_name: str) -> float:
    if isinstance(value, bool):
        raise DataContractError(f"{field_name}必须是有限数。")
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise DataContractError(f"{field_name}必须是有限数。") from exc
    if not math.isfinite(result):
        raise DataContractError(f"{field_name}必须是有限数。")
    return result


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


def _coerce_datetime(value: Any, field_name: str) -> datetime:
    if isinstance(value, datetime):
        return value
    text = _require_text(value, field_name)
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise DataContractError(f"{field_name}不是ISO时间。") from exc


def _looks_like_secret(value: str) -> bool:
    text = value.strip()
    if not text:
        return False
    if re.fullmatch(r"[A-Za-z0-9_\-]{32,}", text):
        return True
    lowered = text.lower()
    forbidden_fragments = (
        "password=",
        "passwd=",
        "token=",
        "secret=",
        "api_key=",
        "apikey=",
        "private_key=",
    )
    return any(fragment in lowered for fragment in forbidden_fragments)


@dataclass(frozen=True, slots=True)
class AuthenticationReference:
    reference_id: str
    kind: AuthenticationReferenceKind
    locator: str
    scopes: tuple[str, ...] = ()
    interactive_login_required: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "reference_id",
            _require_text(self.reference_id, "reference_id"),
        )
        kind = self.kind
        if isinstance(kind, str):
            kind = AuthenticationReferenceKind(kind)
        object.__setattr__(self, "kind", kind)
        locator = _require_text(self.locator, "locator")
        if not locator.startswith(SECRET_REFERENCE_PREFIXES):
            raise DataContractError("认证locator必须是受支持的引用URI。")
        if _looks_like_secret(locator):
            raise DataContractError("认证引用疑似包含秘密材料。")
        expected_prefix = {
            AuthenticationReferenceKind.NONE: "none://",
            AuthenticationReferenceKind.ENVIRONMENT_VARIABLE: "env://",
            AuthenticationReferenceKind.OS_KEYRING: "keyring://",
            AuthenticationReferenceKind.EXTERNAL_SECRET_MANAGER: (
                "secret-manager://"
            ),
            AuthenticationReferenceKind.INTERACTIVE_SESSION: (
                "interactive://"
            ),
        }[kind]
        if not locator.startswith(expected_prefix):
            raise DataContractError("认证类型与locator前缀不一致。")
        object.__setattr__(self, "locator", locator)
        object.__setattr__(
            self,
            "scopes",
            _unique_texts(self.scopes, "scopes"),
        )


@dataclass(frozen=True, slots=True)
class SdkRuntimeDescriptor:
    provider_id: str
    runtime_id: str
    operating_systems: tuple[str, ...]
    python_versions: tuple[str, ...]
    architecture: str
    client_name: str | None
    client_version: str | None
    sdk_name: str | None
    sdk_version: str | None
    installed: bool
    installation_probe: str
    notes: str

    def __post_init__(self) -> None:
        for field_name in (
            "provider_id",
            "runtime_id",
            "architecture",
            "installation_probe",
            "notes",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_text(getattr(self, field_name), field_name),
            )
        object.__setattr__(
            self,
            "operating_systems",
            _unique_texts(
                self.operating_systems,
                "operating_systems",
                allow_empty=False,
            ),
        )
        object.__setattr__(
            self,
            "python_versions",
            _unique_texts(self.python_versions, "python_versions"),
        )
        for field_name in (
            "client_name",
            "client_version",
            "sdk_name",
            "sdk_version",
        ):
            object.__setattr__(
                self,
                field_name,
                _optional_text(getattr(self, field_name), field_name),
            )
        if self.installed and not (self.client_name or self.sdk_name):
            raise DataContractError(
                "已安装运行时必须声明client_name或sdk_name。"
            )


@dataclass(frozen=True, slots=True)
class RateLimitPolicy:
    requests_per_period: int | None
    period_seconds: int | None
    burst_size: int | None
    maximum_concurrency: int
    evidence_status: PolicyEvidenceStatus
    evidence_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.requests_per_period is not None:
            _positive_int(
                self.requests_per_period,
                "requests_per_period",
            )
        if self.period_seconds is not None:
            _positive_int(self.period_seconds, "period_seconds")
        if (self.requests_per_period is None) != (
            self.period_seconds is None
        ):
            raise DataContractError(
                "requests_per_period和period_seconds必须同时存在。"
            )
        if self.burst_size is not None:
            _positive_int(self.burst_size, "burst_size")
        _positive_int(self.maximum_concurrency, "maximum_concurrency")
        status = self.evidence_status
        if isinstance(status, str):
            status = PolicyEvidenceStatus(status)
        object.__setattr__(self, "evidence_status", status)
        refs = _unique_texts(self.evidence_refs, "evidence_refs")
        if status is not PolicyEvidenceStatus.UNKNOWN and not refs:
            raise DataContractError("非UNKNOWN限频政策必须有证据引用。")
        object.__setattr__(self, "evidence_refs", refs)


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    maximum_attempts: int
    backoff_seconds: tuple[int, ...]
    retryable_error_codes: tuple[str, ...]

    def __post_init__(self) -> None:
        _positive_int(self.maximum_attempts, "maximum_attempts")
        if len(self.backoff_seconds) != max(
            0,
            self.maximum_attempts - 1,
        ):
            raise DataContractError("退避次数必须等于最大尝试次数减一。")
        for value in self.backoff_seconds:
            _nonnegative_int(value, "backoff_seconds")
        object.__setattr__(
            self,
            "retryable_error_codes",
            _unique_texts(
                self.retryable_error_codes,
                "retryable_error_codes",
            ),
        )


@dataclass(frozen=True, slots=True)
class BatchPolicy:
    recommended_entities_per_request: int
    maximum_entities_per_request: int
    recommended_rows_per_batch: int
    maximum_rows_per_batch: int
    supports_date_range: bool
    supports_parallel_requests: bool

    def __post_init__(self) -> None:
        for field_name in (
            "recommended_entities_per_request",
            "maximum_entities_per_request",
            "recommended_rows_per_batch",
            "maximum_rows_per_batch",
        ):
            _positive_int(getattr(self, field_name), field_name)
        if (
            self.recommended_entities_per_request
            > self.maximum_entities_per_request
        ):
            raise DataContractError("推荐实体数不能超过最大实体数。")
        if (
            self.recommended_rows_per_batch
            > self.maximum_rows_per_batch
        ):
            raise DataContractError("推荐批次不能超过最大批次。")


@dataclass(frozen=True, slots=True)
class PaginationPolicy:
    mode: PaginationMode
    default_page_size: int | None
    maximum_page_size: int | None
    maximum_pages: int | None
    cursor_field: str | None

    def __post_init__(self) -> None:
        mode = self.mode
        if isinstance(mode, str):
            mode = PaginationMode(mode)
        object.__setattr__(self, "mode", mode)
        for field_name in (
            "default_page_size",
            "maximum_page_size",
            "maximum_pages",
        ):
            value = getattr(self, field_name)
            if value is not None:
                _positive_int(value, field_name)
        if (
            self.default_page_size is not None
            and self.maximum_page_size is not None
            and self.default_page_size > self.maximum_page_size
        ):
            raise DataContractError("默认分页大小不能超过最大分页大小。")
        cursor_field = _optional_text(self.cursor_field, "cursor_field")
        object.__setattr__(self, "cursor_field", cursor_field)
        if mode is PaginationMode.CURSOR and cursor_field is None:
            raise DataContractError("CURSOR分页必须声明cursor_field。")
        if mode is PaginationMode.NONE and any(
            value is not None
            for value in (
                self.default_page_size,
                self.maximum_page_size,
                self.maximum_pages,
                self.cursor_field,
            )
        ):
            raise DataContractError("NONE分页不得携带分页参数。")


@dataclass(frozen=True, slots=True)
class SubscriptionPolicy:
    mode: SubscriptionMode
    maximum_symbols: int | None
    heartbeat_seconds: int | None
    reconnect_supported: bool
    replay_supported: bool

    def __post_init__(self) -> None:
        mode = self.mode
        if isinstance(mode, str):
            mode = SubscriptionMode(mode)
        object.__setattr__(self, "mode", mode)
        if self.maximum_symbols is not None:
            _positive_int(self.maximum_symbols, "maximum_symbols")
        if self.heartbeat_seconds is not None:
            _positive_int(self.heartbeat_seconds, "heartbeat_seconds")
        if mode is SubscriptionMode.NONE and any(
            (
                self.maximum_symbols is not None,
                self.heartbeat_seconds is not None,
                self.reconnect_supported,
                self.replay_supported,
            )
        ):
            raise DataContractError("NONE订阅不得声明订阅参数。")


@dataclass(frozen=True, slots=True)
class LicenseBoundary:
    decision: LicenseDecision
    permitted_usages: tuple[str, ...]
    cache_allowed: bool
    persistent_storage_allowed: bool
    redistribution_allowed: bool
    maximum_retention_days: int | None
    evidence_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        decision = self.decision
        if isinstance(decision, str):
            decision = LicenseDecision(decision)
        object.__setattr__(self, "decision", decision)
        usages = _unique_texts(
            self.permitted_usages,
            "permitted_usages",
        )
        refs = _unique_texts(self.evidence_refs, "evidence_refs")
        object.__setattr__(self, "permitted_usages", usages)
        object.__setattr__(self, "evidence_refs", refs)
        if self.maximum_retention_days is not None:
            _nonnegative_int(
                self.maximum_retention_days,
                "maximum_retention_days",
            )
        if decision is LicenseDecision.ALLOWED:
            if not usages or not refs:
                raise DataContractError(
                    "ALLOWED许可证必须声明用途和证据。"
                )
        if decision is not LicenseDecision.ALLOWED and any(
            (
                self.cache_allowed,
                self.persistent_storage_allowed,
                self.redistribution_allowed,
            )
        ):
            raise DataContractError(
                "未放行许可证不得允许缓存、持久化或再分发。"
            )


@dataclass(frozen=True, slots=True)
class ProviderHealthSnapshot:
    status: ProviderHealthStatus
    checked_at: datetime
    latency_ms: float | None
    message: str
    evidence_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        status = self.status
        if isinstance(status, str):
            status = ProviderHealthStatus(status)
        object.__setattr__(self, "status", status)
        object.__setattr__(
            self,
            "checked_at",
            _coerce_datetime(self.checked_at, "checked_at"),
        )
        if self.latency_ms is not None:
            latency = _finite(self.latency_ms, "latency_ms")
            if latency < 0:
                raise DataContractError("latency_ms不能为负。")
            object.__setattr__(self, "latency_ms", latency)
        object.__setattr__(
            self,
            "message",
            _require_text(self.message, "message"),
        )
        object.__setattr__(
            self,
            "evidence_refs",
            _unique_texts(self.evidence_refs, "evidence_refs"),
        )


@dataclass(frozen=True, slots=True)
class ProviderDiscoveryResult:
    discovery_id: str
    provider_id: str
    plugin_id: str
    outcome: DiscoveryOutcome
    discovered_at: datetime
    runtime: SdkRuntimeDescriptor
    authentication_reference: AuthenticationReference
    capabilities: Mapping[str, CapabilityImplementationStatus]
    rate_limit_policy: RateLimitPolicy
    retry_policy: RetryPolicy
    batch_policy: BatchPolicy
    pagination_policy: PaginationPolicy
    subscription_policy: SubscriptionPolicy
    license_boundary: LicenseBoundary
    health: ProviderHealthSnapshot
    warnings: tuple[str, ...]
    errors: tuple[str, ...]

    def __post_init__(self) -> None:
        for field_name in ("discovery_id", "provider_id", "plugin_id"):
            object.__setattr__(
                self,
                field_name,
                _require_text(getattr(self, field_name), field_name),
            )
        outcome = self.outcome
        if isinstance(outcome, str):
            outcome = DiscoveryOutcome(outcome)
        object.__setattr__(self, "outcome", outcome)
        object.__setattr__(
            self,
            "discovered_at",
            _coerce_datetime(self.discovered_at, "discovered_at"),
        )
        if self.runtime.provider_id != self.provider_id:
            raise DataContractError("运行时provider_id不一致。")
        capabilities = {
            _require_text(key, "capability"): (
                value
                if isinstance(value, CapabilityImplementationStatus)
                else CapabilityImplementationStatus(value)
            )
            for key, value in self.capabilities.items()
        }
        object.__setattr__(self, "capabilities", capabilities)
        object.__setattr__(
            self,
            "warnings",
            _unique_texts(self.warnings, "warnings"),
        )
        object.__setattr__(
            self,
            "errors",
            _unique_texts(self.errors, "errors"),
        )
        if outcome is DiscoveryOutcome.COMPLETE:
            if not self.runtime.installed:
                raise DataContractError("完整发现必须确认运行时已安装。")
            if not capabilities:
                raise DataContractError("完整发现必须包含能力结果。")
            if self.errors:
                raise DataContractError("完整发现不得包含errors。")
        if outcome is DiscoveryOutcome.FAILED and not self.errors:
            raise DataContractError("失败发现必须记录errors。")


@dataclass(frozen=True, slots=True)
class ProviderRegistryEntry:
    provider_id: str
    plugin_id: str
    registration_status: PluginRegistrationStatus
    entrypoint: str | None
    priority: int
    enabled_for_routing: bool
    discovery_result_ref: str | None
    authentication_reference_ref: str | None
    notes: str

    def __post_init__(self) -> None:
        for field_name in ("provider_id", "plugin_id", "notes"):
            object.__setattr__(
                self,
                field_name,
                _require_text(getattr(self, field_name), field_name),
            )
        status = self.registration_status
        if isinstance(status, str):
            status = PluginRegistrationStatus(status)
        object.__setattr__(self, "registration_status", status)
        object.__setattr__(
            self,
            "entrypoint",
            _optional_text(self.entrypoint, "entrypoint"),
        )
        _nonnegative_int(self.priority, "priority")
        object.__setattr__(
            self,
            "discovery_result_ref",
            _optional_text(
                self.discovery_result_ref,
                "discovery_result_ref",
            ),
        )
        auth_ref = _optional_text(
            self.authentication_reference_ref,
            "authentication_reference_ref",
        )
        if auth_ref is not None:
            if not auth_ref.startswith(SECRET_REFERENCE_PREFIXES):
                raise DataContractError(
                    "注册表认证引用必须使用受支持的URI。"
                )
            if _looks_like_secret(auth_ref):
                raise DataContractError("注册表认证引用疑似包含秘密材料。")
        object.__setattr__(
            self,
            "authentication_reference_ref",
            auth_ref,
        )
        if self.enabled_for_routing:
            if status not in {
                PluginRegistrationStatus.DISCOVERY_COMPLETE,
                PluginRegistrationStatus.AVAILABLE,
            }:
                raise DataContractError(
                    "未完成发现的插件不得启用路由。"
                )
            if self.entrypoint is None or self.discovery_result_ref is None:
                raise DataContractError(
                    "启用路由必须具有entrypoint和发现结果引用。"
                )


@dataclass(frozen=True, slots=True)
class ProviderPluginRegistry:
    task_id: str
    registry_version: str
    registry_status: str
    automatic_activation_allowed: bool
    entries: tuple[ProviderRegistryEntry, ...]
    hard_rules: tuple[str, ...]

    def __post_init__(self) -> None:
        for field_name in (
            "task_id",
            "registry_version",
            "registry_status",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_text(getattr(self, field_name), field_name),
            )
        if self.task_id != "TASK_020B":
            raise DataContractError("注册表task_id异常。")
        if self.automatic_activation_allowed:
            raise DataContractError("注册表不得自动激活插件。")
        provider_ids = [entry.provider_id for entry in self.entries]
        plugin_ids = [entry.plugin_id for entry in self.entries]
        if not provider_ids or len(provider_ids) != len(set(provider_ids)):
            raise DataContractError("provider_id必须非空且唯一。")
        if len(plugin_ids) != len(set(plugin_ids)):
            raise DataContractError("plugin_id必须唯一。")
        object.__setattr__(
            self,
            "hard_rules",
            _unique_texts(
                self.hard_rules,
                "hard_rules",
                allow_empty=False,
            ),
        )

    def entry(self, provider_id: str) -> ProviderRegistryEntry:
        key = _require_text(provider_id, "provider_id")
        for entry in self.entries:
            if entry.provider_id == key:
                return entry
        raise DataContractError(f"注册表未登记Provider：{key}")


@dataclass(frozen=True, slots=True)
class ProviderQueryRequest:
    request_id: str
    provider_id: str
    capability: str
    operation: str
    usage: str
    parameters: Mapping[str, Any]
    maximum_rows: int

    def __post_init__(self) -> None:
        for field_name in (
            "request_id",
            "provider_id",
            "capability",
            "operation",
            "usage",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_text(getattr(self, field_name), field_name),
            )
        _positive_int(self.maximum_rows, "maximum_rows")
        if not isinstance(self.parameters, Mapping):
            raise DataContractError("parameters必须是映射。")


@dataclass(frozen=True, slots=True)
class ProviderQueryBatch:
    request_id: str
    provider_id: str
    capability: str
    records: tuple[Mapping[str, Any], ...]
    next_cursor: str | None
    source_request_id: str
    warnings: tuple[str, ...]

    def __post_init__(self) -> None:
        for field_name in (
            "request_id",
            "provider_id",
            "capability",
            "source_request_id",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_text(getattr(self, field_name), field_name),
            )
        if any(not isinstance(item, Mapping) for item in self.records):
            raise DataContractError("records必须由映射组成。")
        object.__setattr__(
            self,
            "next_cursor",
            _optional_text(self.next_cursor, "next_cursor"),
        )
        object.__setattr__(
            self,
            "warnings",
            _unique_texts(self.warnings, "warnings"),
        )


@dataclass(frozen=True, slots=True)
class ProviderSubscriptionRequest:
    subscription_id: str
    provider_id: str
    capability: str
    symbols: tuple[str, ...]
    fields: tuple[str, ...]

    def __post_init__(self) -> None:
        for field_name in (
            "subscription_id",
            "provider_id",
            "capability",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_text(getattr(self, field_name), field_name),
            )
        object.__setattr__(
            self,
            "symbols",
            _unique_texts(
                self.symbols,
                "symbols",
                allow_empty=False,
            ),
        )
        object.__setattr__(
            self,
            "fields",
            _unique_texts(
                self.fields,
                "fields",
                allow_empty=False,
            ),
        )


@runtime_checkable
class ProviderPlugin(Protocol):
    """所有具体厂商插件必须满足的结构化协议。"""

    def describe(self) -> ProviderRegistryEntry:
        ...

    def discover(self) -> ProviderDiscoveryResult:
        ...

    def health_check(self) -> ProviderHealthSnapshot:
        ...

    def open_session(
        self,
        authentication_reference: AuthenticationReference,
    ) -> None:
        ...

    def close_session(self) -> None:
        ...

    def query_batch(
        self,
        request: ProviderQueryRequest,
    ) -> ProviderQueryBatch:
        ...

    def iter_pages(
        self,
        request: ProviderQueryRequest,
    ) -> Iterator[ProviderQueryBatch]:
        ...

    def subscribe(
        self,
        request: ProviderSubscriptionRequest,
    ) -> str:
        ...

    def unsubscribe(self, subscription_id: str) -> None:
        ...


@dataclass(frozen=True, slots=True)
class ProviderRouteRequest:
    capability: str
    usage: str
    requires_realtime: bool = False
    requires_execution: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "capability",
            _require_text(self.capability, "capability"),
        )
        object.__setattr__(
            self,
            "usage",
            _require_text(self.usage, "usage"),
        )


@dataclass(frozen=True, slots=True)
class ProviderRouteCandidate:
    provider_id: str
    plugin_id: str
    decision: RouteDecision
    score: float
    score_breakdown: Mapping[str, float]
    reasons: tuple[str, ...]
    warnings: tuple[str, ...]

    def __post_init__(self) -> None:
        for field_name in ("provider_id", "plugin_id"):
            object.__setattr__(
                self,
                field_name,
                _require_text(getattr(self, field_name), field_name),
            )
        decision = self.decision
        if isinstance(decision, str):
            decision = RouteDecision(decision)
        object.__setattr__(self, "decision", decision)
        score = _finite(self.score, "score")
        if score < 0 or score > 100:
            raise DataContractError("路由得分必须位于0到100。")
        object.__setattr__(self, "score", score)
        breakdown = {
            _require_text(key, "score_breakdown_key"): _finite(
                value,
                "score_breakdown_value",
            )
            for key, value in self.score_breakdown.items()
        }
        if any(value < 0 for value in breakdown.values()):
            raise DataContractError("评分分解不得为负。")
        object.__setattr__(self, "score_breakdown", breakdown)
        object.__setattr__(
            self,
            "reasons",
            _unique_texts(self.reasons, "reasons"),
        )
        object.__setattr__(
            self,
            "warnings",
            _unique_texts(self.warnings, "warnings"),
        )
        if decision is RouteDecision.ELIGIBLE and self.reasons:
            raise DataContractError("合格候选不得包含阻断原因。")
        if decision is RouteDecision.INELIGIBLE and not self.reasons:
            raise DataContractError("不合格候选必须说明原因。")


@dataclass(frozen=True, slots=True)
class ProviderPluginProtocolConfig:
    task_id: str
    protocol_version: str
    protocol_status: str
    provider_neutral: bool
    vendor_sdk_import_boundary: str
    automatic_plugin_activation_allowed: bool
    secret_material_allowed: bool
    network_probe_during_validation_allowed: bool
    database_probe_during_validation_allowed: bool
    required_plugin_methods: tuple[str, ...]
    required_discovery_sections: tuple[str, ...]
    authentication_reference_prefixes: tuple[str, ...]
    registration_statuses_eligible_for_routing: tuple[
        PluginRegistrationStatus,
        ...,
    ]
    discovery_outcomes_eligible_for_routing: tuple[
        DiscoveryOutcome,
        ...,
    ]
    health_statuses_eligible_for_routing: tuple[
        ProviderHealthStatus,
        ...,
    ]
    capability_statuses_eligible_for_routing: tuple[
        CapabilityImplementationStatus,
        ...,
    ]
    license_decisions_eligible_for_routing: tuple[
        LicenseDecision,
        ...,
    ]
    route_score_weights: Mapping[str, float]
    hard_rules: tuple[str, ...]

    def __post_init__(self) -> None:
        for field_name in (
            "task_id",
            "protocol_version",
            "protocol_status",
            "vendor_sdk_import_boundary",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_text(getattr(self, field_name), field_name),
            )
        if self.task_id != "TASK_020B":
            raise DataContractError("协议task_id异常。")
        if not self.provider_neutral:
            raise DataContractError("协议必须保持供应商中立。")
        if any(
            (
                self.automatic_plugin_activation_allowed,
                self.secret_material_allowed,
                self.network_probe_during_validation_allowed,
                self.database_probe_during_validation_allowed,
            )
        ):
            raise DataContractError("TASK_020B安全边界被破坏。")
        for field_name in (
            "required_plugin_methods",
            "required_discovery_sections",
            "authentication_reference_prefixes",
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
        if set(self.authentication_reference_prefixes) != set(
            SECRET_REFERENCE_PREFIXES
        ):
            raise DataContractError("认证引用前缀合同异常。")
        weights = {
            _require_text(key, "route_score_weight"): _finite(
                value,
                "route_score_weight",
            )
            for key, value in self.route_score_weights.items()
        }
        if set(weights) != {
            "capability",
            "discovery",
            "health",
            "license",
            "priority",
            "exact_usage",
        }:
            raise DataContractError("路由权重维度异常。")
        if not math.isclose(sum(weights.values()), 100.0, abs_tol=1e-9):
            raise DataContractError("路由权重之和必须为100。")
        object.__setattr__(self, "route_score_weights", weights)


def load_provider_plugin_protocol_config(
    path: str | Path,
) -> ProviderPluginProtocolConfig:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise DataContractError("插件协议根节点必须是对象。")
    return ProviderPluginProtocolConfig(
        task_id=str(raw["task_id"]),
        protocol_version=str(raw["protocol_version"]),
        protocol_status=str(raw["protocol_status"]),
        provider_neutral=bool(raw["provider_neutral"]),
        vendor_sdk_import_boundary=str(
            raw["vendor_sdk_import_boundary"]
        ),
        automatic_plugin_activation_allowed=bool(
            raw["automatic_plugin_activation_allowed"]
        ),
        secret_material_allowed=bool(raw["secret_material_allowed"]),
        network_probe_during_validation_allowed=bool(
            raw["network_probe_during_validation_allowed"]
        ),
        database_probe_during_validation_allowed=bool(
            raw["database_probe_during_validation_allowed"]
        ),
        required_plugin_methods=tuple(
            str(value) for value in raw["required_plugin_methods"]
        ),
        required_discovery_sections=tuple(
            str(value) for value in raw["required_discovery_sections"]
        ),
        authentication_reference_prefixes=tuple(
            str(value)
            for value in raw["authentication_reference_prefixes"]
        ),
        registration_statuses_eligible_for_routing=tuple(
            PluginRegistrationStatus(str(value))
            for value in raw[
                "registration_statuses_eligible_for_routing"
            ]
        ),
        discovery_outcomes_eligible_for_routing=tuple(
            DiscoveryOutcome(str(value))
            for value in raw[
                "discovery_outcomes_eligible_for_routing"
            ]
        ),
        health_statuses_eligible_for_routing=tuple(
            ProviderHealthStatus(str(value))
            for value in raw[
                "health_statuses_eligible_for_routing"
            ]
        ),
        capability_statuses_eligible_for_routing=tuple(
            CapabilityImplementationStatus(str(value))
            for value in raw[
                "capability_statuses_eligible_for_routing"
            ]
        ),
        license_decisions_eligible_for_routing=tuple(
            LicenseDecision(str(value))
            for value in raw[
                "license_decisions_eligible_for_routing"
            ]
        ),
        route_score_weights={
            str(key): float(value)
            for key, value in raw["route_score_weights"].items()
        },
        hard_rules=tuple(str(value) for value in raw["hard_rules"]),
    )


def load_provider_plugin_registry(
    path: str | Path,
) -> ProviderPluginRegistry:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise DataContractError("插件注册表根节点必须是对象。")
    entries = tuple(
        ProviderRegistryEntry(
            provider_id=str(item["provider_id"]),
            plugin_id=str(item["plugin_id"]),
            registration_status=PluginRegistrationStatus(
                str(item["registration_status"])
            ),
            entrypoint=(
                str(item["entrypoint"])
                if item["entrypoint"] is not None
                else None
            ),
            priority=int(item["priority"]),
            enabled_for_routing=bool(item["enabled_for_routing"]),
            discovery_result_ref=(
                str(item["discovery_result_ref"])
                if item["discovery_result_ref"] is not None
                else None
            ),
            authentication_reference_ref=(
                str(item["authentication_reference_ref"])
                if item["authentication_reference_ref"] is not None
                else None
            ),
            notes=str(item["notes"]),
        )
        for item in raw["entries"]
    )
    return ProviderPluginRegistry(
        task_id=str(raw["task_id"]),
        registry_version=str(raw["registry_version"]),
        registry_status=str(raw["registry_status"]),
        automatic_activation_allowed=bool(
            raw["automatic_activation_allowed"]
        ),
        entries=entries,
        hard_rules=tuple(str(value) for value in raw["hard_rules"]),
    )


def build_provider_route_candidates(
    *,
    matrix: ProviderCapabilityMatrix,
    registry: ProviderPluginRegistry,
    protocol: ProviderPluginProtocolConfig,
    discovery_results: Mapping[str, ProviderDiscoveryResult],
    request: ProviderRouteRequest,
) -> tuple[ProviderRouteCandidate, ...]:
    if request.capability not in matrix.capability_catalog:
        raise DataContractError(
            f"能力矩阵未登记请求能力：{request.capability}"
        )

    candidates: list[ProviderRouteCandidate] = []
    for entry in registry.entries:
        target = matrix.provider(entry.provider_id)
        discovery = discovery_results.get(entry.provider_id)
        reasons: list[str] = []
        warnings: list[str] = []
        breakdown = {
            key: 0.0 for key in protocol.route_score_weights
        }

        if not entry.enabled_for_routing:
            reasons.append("REGISTRY_ROUTING_DISABLED")
        if entry.registration_status not in (
            protocol.registration_statuses_eligible_for_routing
        ):
            reasons.append("REGISTRATION_STATUS_NOT_ELIGIBLE")
        if entry.entrypoint is None:
            reasons.append("PLUGIN_ENTRYPOINT_MISSING")
        if discovery is None:
            reasons.append("DISCOVERY_RESULT_MISSING")
        else:
            if discovery.provider_id != entry.provider_id:
                reasons.append("DISCOVERY_PROVIDER_MISMATCH")
            if discovery.plugin_id != entry.plugin_id:
                reasons.append("DISCOVERY_PLUGIN_MISMATCH")
            if discovery.outcome not in (
                protocol.discovery_outcomes_eligible_for_routing
            ):
                reasons.append("DISCOVERY_OUTCOME_NOT_ELIGIBLE")
            else:
                breakdown["discovery"] = protocol.route_score_weights[
                    "discovery"
                ]

            capability_status = discovery.capabilities.get(
                request.capability
            )
            if capability_status not in (
                protocol.capability_statuses_eligible_for_routing
            ):
                reasons.append("CAPABILITY_NOT_VERIFIED")
            else:
                breakdown["capability"] = protocol.route_score_weights[
                    "capability"
                ]

            if discovery.health.status not in (
                protocol.health_statuses_eligible_for_routing
            ):
                reasons.append("HEALTH_NOT_ELIGIBLE")
            elif discovery.health.status is ProviderHealthStatus.HEALTHY:
                breakdown["health"] = protocol.route_score_weights[
                    "health"
                ]
            else:
                breakdown["health"] = (
                    protocol.route_score_weights["health"] * 0.5
                )
                warnings.append("PROVIDER_HEALTH_DEGRADED")

            license_boundary = discovery.license_boundary
            if license_boundary.decision not in (
                protocol.license_decisions_eligible_for_routing
            ):
                reasons.append("LICENSE_NOT_ALLOWED")
            elif request.usage not in license_boundary.permitted_usages:
                reasons.append("USAGE_NOT_LICENSED")
            else:
                breakdown["license"] = protocol.route_score_weights[
                    "license"
                ]
                breakdown["exact_usage"] = (
                    protocol.route_score_weights["exact_usage"]
                )

            if (
                request.requires_realtime
                and discovery.subscription_policy.mode
                is SubscriptionMode.NONE
            ):
                reasons.append("REALTIME_SUBSCRIPTION_NOT_SUPPORTED")

        if request.requires_execution:
            if request.capability not in _EXECUTION_CAPABILITIES:
                reasons.append("EXECUTION_REQUEST_CAPABILITY_MISMATCH")
            if not target.execution_capability:
                reasons.append("PROVIDER_NOT_EXECUTION_CAPABLE")
        elif request.capability in _EXECUTION_CAPABILITIES:
            reasons.append("EXECUTION_CAPABILITY_REQUIRES_EXPLICIT_FLAG")

        if target.lifecycle not in {
            ProviderLifecycle.REAL_ACCEPTED,
            ProviderLifecycle.ACTIVATED,
        }:
            reasons.append("PROVIDER_LIFECYCLE_NOT_ACCEPTED")

        if target.discovery_status not in {
            ProviderDiscoveryStatus.VERIFIED_IN_PROJECT,
            ProviderDiscoveryStatus.DISCOVERY_COMPLETE,
        }:
            reasons.append("MATRIX_DISCOVERY_NOT_COMPLETE")

        priority_score = protocol.route_score_weights["priority"] * (
            max(0.0, 100.0 - float(entry.priority)) / 100.0
        )
        breakdown["priority"] = priority_score

        reasons = list(dict.fromkeys(reasons))
        warnings = list(dict.fromkeys(warnings))
        if reasons:
            decision = RouteDecision.INELIGIBLE
            score = 0.0
            breakdown = {key: 0.0 for key in breakdown}
        else:
            decision = RouteDecision.ELIGIBLE
            score = sum(breakdown.values())

        candidates.append(
            ProviderRouteCandidate(
                provider_id=entry.provider_id,
                plugin_id=entry.plugin_id,
                decision=decision,
                score=score,
                score_breakdown=breakdown,
                reasons=tuple(reasons),
                warnings=tuple(warnings),
            )
        )

    return tuple(
        sorted(
            candidates,
            key=lambda item: (
                item.decision is not RouteDecision.ELIGIBLE,
                -item.score,
                item.provider_id,
            ),
        )
    )


def dataclass_to_json_safe(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, tuple):
        return [dataclass_to_json_safe(item) for item in value]
    if isinstance(value, list):
        return [dataclass_to_json_safe(item) for item in value]
    if isinstance(value, Mapping):
        return {
            str(key): dataclass_to_json_safe(item)
            for key, item in value.items()
        }
    return value


def object_to_dict(value: Any) -> dict[str, Any]:
    if not hasattr(value, "__dataclass_fields__"):
        raise DataContractError("对象不是dataclass。")
    return dataclass_to_json_safe(asdict(value))
