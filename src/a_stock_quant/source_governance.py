"""来源中立的数据源治理合同。

本模块只定义长期稳定的数据源、能力、绑定和路由合同。
它不直接连接 Wind、iFinD、券商、DolphinDB 或文件系统，
也不保存任何账号、密码、Token 或本机路径。

设计目标：
1. 下游继续只依赖逻辑 dataset_id 和 StandardDataService；
2. 新来源通过 SourceDescriptor 和 DatasetSourceBinding 接入；
3. 主来源、备用来源、实时来源、归档来源和对账来源显式区分；
4. 来源能力显式声明，避免在业务代码中写 vendor if/else；
5. 尚未开通的 Wind、iFinD 和券商接口可以先完成离线合同和测试。
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any, Iterable

from .data_contracts import DataContractError


def _require_text(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DataContractError(f"{field_name} 不能为空。")
    return value.strip()


def _unique_enum_tuple(
    values: Iterable[Enum],
    enum_type: type[Enum],
    field_name: str,
) -> tuple[Enum, ...]:
    resolved: list[Enum] = []
    for value in values:
        if isinstance(value, str):
            try:
                value = enum_type(value)
            except ValueError as exc:
                raise DataContractError(
                    f"{field_name} 包含不支持的值：{value}"
                ) from exc
        if not isinstance(value, enum_type):
            raise DataContractError(
                f"{field_name} 必须由 {enum_type.__name__} 组成。"
            )
        resolved.append(value)

    if len(set(resolved)) != len(resolved):
        raise DataContractError(f"{field_name} 不允许重复。")
    return tuple(resolved)


def _json_safe(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, dict):
        return {
            str(key): _json_safe(item)
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_json_safe(item) for item in value]
    return value


class SourceProtocol(str, Enum):
    DATABASE = "DATABASE"
    FILE = "FILE"
    SDK = "SDK"
    HTTP = "HTTP"
    STREAM = "STREAM"
    BROKER = "BROKER"


class SourceRole(str, Enum):
    PRIMARY = "PRIMARY"
    FALLBACK = "FALLBACK"
    RECONCILIATION = "RECONCILIATION"
    REALTIME = "REALTIME"
    ARCHIVE = "ARCHIVE"


class SourceCapability(str, Enum):
    TIME_SERIES = "TIME_SERIES"
    CROSS_SECTION = "CROSS_SECTION"
    HISTORICAL_QUOTES = "HISTORICAL_QUOTES"
    REALTIME_QUOTES = "REALTIME_QUOTES"
    HIGH_FREQUENCY = "HIGH_FREQUENCY"
    SNAPSHOT = "SNAPSHOT"
    FUNDAMENTAL = "FUNDAMENTAL"
    CLASSIFICATION = "CLASSIFICATION"
    MONEY_FLOW = "MONEY_FLOW"
    MACRO = "MACRO"
    REPORTS = "REPORTS"
    NEWS_EVENTS = "NEWS_EVENTS"
    TRADING_CALENDAR = "TRADING_CALENDAR"
    PORTFOLIO_ANALYTICS = "PORTFOLIO_ANALYTICS"
    INCREMENTAL_SYNC = "INCREMENTAL_SYNC"
    POINT_IN_TIME = "POINT_IN_TIME"
    ORDERS = "ORDERS"
    POSITIONS = "POSITIONS"
    ACCOUNT = "ACCOUNT"


class SourceOperationalStatus(str, Enum):
    DISABLED = "DISABLED"
    CONFIGURED = "CONFIGURED"
    AVAILABLE = "AVAILABLE"
    DEGRADED = "DEGRADED"
    UNAVAILABLE = "UNAVAILABLE"


class ConflictStatus(str, Enum):
    MATCHED = "MATCHED"
    WITHIN_TOLERANCE = "WITHIN_TOLERANCE"
    CONFLICT = "CONFLICT"
    PENDING_REVIEW = "PENDING_REVIEW"
    RESOLVED = "RESOLVED"


@dataclass(frozen=True, slots=True)
class CredentialReference:
    reference_id: str
    environment_variable: str
    required: bool = True
    description: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "reference_id",
            _require_text(self.reference_id, "reference_id"),
        )
        object.__setattr__(
            self,
            "environment_variable",
            _require_text(
                self.environment_variable,
                "environment_variable",
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return _json_safe(asdict(self))


@dataclass(frozen=True, slots=True)
class RateLimitPolicy:
    request_max_rows_hint: int | None = None
    quota_unit: str | None = None
    quota_limit_hint: int | None = None
    quota_window_seconds: int | None = None
    account_specific: bool = True
    hard_enforcement_enabled: bool = False

    def __post_init__(self) -> None:
        for field_name in (
            "request_max_rows_hint",
            "quota_limit_hint",
            "quota_window_seconds",
        ):
            value = getattr(self, field_name)
            if value is not None and (
                not isinstance(value, int) or value <= 0
            ):
                raise DataContractError(
                    f"{field_name} 必须是正整数或None。"
                )

        if (
            self.hard_enforcement_enabled
            and self.quota_limit_hint is None
        ):
            raise DataContractError(
                "启用硬配额时必须提供quota_limit_hint。"
            )

    def to_dict(self) -> dict[str, Any]:
        return _json_safe(asdict(self))


@dataclass(frozen=True, slots=True)
class SourceDescriptor:
    source_id: str
    vendor_name: str
    protocol: SourceProtocol
    capabilities: tuple[SourceCapability, ...]
    enabled: bool = False
    operational_status: SourceOperationalStatus = (
        SourceOperationalStatus.DISABLED
    )
    credential_references: tuple[
        CredentialReference, ...
    ] = ()
    rate_limit_policy: RateLimitPolicy | None = None
    timezone: str = "Asia/Shanghai"
    documentation_status: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "source_id",
            _require_text(self.source_id, "source_id"),
        )
        object.__setattr__(
            self,
            "vendor_name",
            _require_text(self.vendor_name, "vendor_name"),
        )
        protocol = self.protocol
        if isinstance(protocol, str):
            try:
                protocol = SourceProtocol(protocol)
            except ValueError as exc:
                raise DataContractError(
                    "protocol不是受支持的来源协议。"
                ) from exc
        object.__setattr__(self, "protocol", protocol)

        object.__setattr__(
            self,
            "capabilities",
            _unique_enum_tuple(
                self.capabilities,
                SourceCapability,
                "capabilities",
            ),
        )

        status = self.operational_status
        if isinstance(status, str):
            try:
                status = SourceOperationalStatus(status)
            except ValueError as exc:
                raise DataContractError(
                    "operational_status不是受支持的状态。"
                ) from exc

        if not self.enabled and status is not (
            SourceOperationalStatus.DISABLED
        ):
            raise DataContractError(
                "未启用来源的operational_status必须为DISABLED。"
            )

        object.__setattr__(
            self,
            "operational_status",
            status,
        )

        credential_ids = [
            item.reference_id
            for item in self.credential_references
        ]
        if len(set(credential_ids)) != len(credential_ids):
            raise DataContractError(
                "credential_references不允许重复reference_id。"
            )

        object.__setattr__(
            self,
            "timezone",
            _require_text(self.timezone, "timezone"),
        )

    def supports(
        self,
        required_capabilities: Iterable[
            SourceCapability
        ],
    ) -> bool:
        required = set(
            _unique_enum_tuple(
                required_capabilities,
                SourceCapability,
                "required_capabilities",
            )
        )
        return required.issubset(set(self.capabilities))

    def to_dict(self) -> dict[str, Any]:
        return _json_safe(asdict(self))

    @classmethod
    def from_dict(
        cls,
        payload: dict[str, Any],
    ) -> "SourceDescriptor":
        credentials = tuple(
            CredentialReference(**item)
            for item in payload.get(
                "credential_references",
                [],
            )
        )
        rate_payload = payload.get("rate_limit_policy")
        rate_policy = (
            RateLimitPolicy(**rate_payload)
            if rate_payload
            else None
        )
        return cls(
            source_id=payload["source_id"],
            vendor_name=payload["vendor_name"],
            protocol=SourceProtocol(payload["protocol"]),
            capabilities=tuple(
                SourceCapability(item)
                for item in payload.get(
                    "capabilities",
                    [],
                )
            ),
            enabled=bool(payload.get("enabled", False)),
            operational_status=SourceOperationalStatus(
                payload.get(
                    "operational_status",
                    "DISABLED",
                )
            ),
            credential_references=credentials,
            rate_limit_policy=rate_policy,
            timezone=payload.get(
                "timezone",
                "Asia/Shanghai",
            ),
            documentation_status=payload.get(
                "documentation_status",
                "",
            ),
            metadata=dict(payload.get("metadata", {})),
        )


@dataclass(frozen=True, slots=True)
class DatasetSourceBinding:
    dataset_id: str
    source_id: str
    role: SourceRole
    priority: int
    source_locator: dict[str, Any]
    mapping_version: str
    source_schema_version: str
    required_capabilities: tuple[
        SourceCapability, ...
    ] = ()
    enabled: bool = False
    effective_from: date | None = None
    effective_to: date | None = None
    notes: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "dataset_id",
            _require_text(self.dataset_id, "dataset_id"),
        )
        object.__setattr__(
            self,
            "source_id",
            _require_text(self.source_id, "source_id"),
        )
        role = self.role
        if isinstance(role, str):
            try:
                role = SourceRole(role)
            except ValueError as exc:
                raise DataContractError(
                    "role不是受支持的来源角色。"
                ) from exc
        object.__setattr__(self, "role", role)

        if not isinstance(self.priority, int) or self.priority < 1:
            raise DataContractError(
                "priority必须是大于等于1的整数。"
            )

        object.__setattr__(
            self,
            "mapping_version",
            _require_text(
                self.mapping_version,
                "mapping_version",
            ),
        )
        object.__setattr__(
            self,
            "source_schema_version",
            _require_text(
                self.source_schema_version,
                "source_schema_version",
            ),
        )
        object.__setattr__(
            self,
            "required_capabilities",
            _unique_enum_tuple(
                self.required_capabilities,
                SourceCapability,
                "required_capabilities",
            ),
        )

        if (
            self.effective_from is not None
            and self.effective_to is not None
            and self.effective_from > self.effective_to
        ):
            raise DataContractError(
                "effective_from不能晚于effective_to。"
            )

    def is_effective_on(self, target_date: date) -> bool:
        if self.effective_from and target_date < self.effective_from:
            return False
        if self.effective_to and target_date > self.effective_to:
            return False
        return True

    def to_dict(self) -> dict[str, Any]:
        return _json_safe(asdict(self))


@dataclass(frozen=True, slots=True)
class ConflictRecord:
    dataset_id: str
    canonical_object: str
    primary_key: dict[str, Any]
    field_name: str
    observation_time: datetime | date
    primary_source_id: str
    comparison_source_id: str
    primary_value: Any
    comparison_value: Any
    difference: Any = None
    tolerance: Any = None
    status: ConflictStatus = ConflictStatus.PENDING_REVIEW
    resolution_note: str = ""

    def __post_init__(self) -> None:
        for field_name in (
            "dataset_id",
            "canonical_object",
            "field_name",
            "primary_source_id",
            "comparison_source_id",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_text(
                    getattr(self, field_name),
                    field_name,
                ),
            )

        if (
            self.primary_source_id
            == self.comparison_source_id
        ):
            raise DataContractError(
                "冲突比较必须来自两个不同来源。"
            )

        status = self.status
        if isinstance(status, str):
            try:
                status = ConflictStatus(status)
            except ValueError as exc:
                raise DataContractError(
                    "status不是受支持的冲突状态。"
                ) from exc
        object.__setattr__(self, "status", status)

    def to_dict(self) -> dict[str, Any]:
        return _json_safe(asdict(self))


@dataclass(frozen=True, slots=True)
class SourceRoute:
    binding: DatasetSourceBinding
    source: SourceDescriptor

    def to_dict(self) -> dict[str, Any]:
        return {
            "binding": self.binding.to_dict(),
            "source": self.source.to_dict(),
        }


class SourceCatalog:
    """来源和逻辑数据集绑定注册表。

    当前只负责静态选择顺序，不执行网络请求和自动故障转移。
    自动故障转移必须在未来引入健康检查、幂等和审计后再启用。
    """

    def __init__(self) -> None:
        self._sources: dict[str, SourceDescriptor] = {}
        self._bindings: list[DatasetSourceBinding] = []

    def register_source(
        self,
        source: SourceDescriptor,
    ) -> None:
        if source.source_id in self._sources:
            raise DataContractError(
                f"来源已注册：{source.source_id}"
            )
        self._sources[source.source_id] = source

    def register_binding(
        self,
        binding: DatasetSourceBinding,
    ) -> None:
        if binding.source_id not in self._sources:
            raise DataContractError(
                f"来源未注册：{binding.source_id}"
            )

        duplicate = any(
            item.dataset_id == binding.dataset_id
            and item.source_id == binding.source_id
            and item.role == binding.role
            for item in self._bindings
        )
        if duplicate:
            raise DataContractError(
                "同一dataset/source/role绑定不允许重复。"
            )

        source = self._sources[binding.source_id]
        if not source.supports(
            binding.required_capabilities
        ):
            raise DataContractError(
                "来源能力不能满足绑定要求。"
            )

        self._bindings.append(binding)

    def get_source(
        self,
        source_id: str,
    ) -> SourceDescriptor:
        try:
            return self._sources[source_id]
        except KeyError as exc:
            raise DataContractError(
                f"未知来源：{source_id}"
            ) from exc

    def list_sources(self) -> tuple[SourceDescriptor, ...]:
        return tuple(
            self._sources[key]
            for key in sorted(self._sources)
        )

    def routes_for(
        self,
        dataset_id: str,
        required_capabilities: Iterable[
            SourceCapability
        ] = (),
        *,
        roles: Iterable[SourceRole] | None = None,
        target_date: date | None = None,
        include_disabled: bool = False,
    ) -> tuple[SourceRoute, ...]:
        dataset_id = _require_text(
            dataset_id,
            "dataset_id",
        )
        required = tuple(required_capabilities)
        role_filter = (
            set(
                _unique_enum_tuple(
                    roles,
                    SourceRole,
                    "roles",
                )
            )
            if roles is not None
            else None
        )

        routes: list[SourceRoute] = []
        for binding in self._bindings:
            if binding.dataset_id != dataset_id:
                continue
            if role_filter is not None and (
                binding.role not in role_filter
            ):
                continue
            if target_date is not None and (
                not binding.is_effective_on(target_date)
            ):
                continue

            source = self._sources[binding.source_id]
            if not include_disabled and (
                not source.enabled
                or not binding.enabled
            ):
                continue
            if not source.supports(required):
                continue

            routes.append(
                SourceRoute(
                    binding=binding,
                    source=source,
                )
            )

        role_order = {
            SourceRole.PRIMARY: 0,
            SourceRole.REALTIME: 1,
            SourceRole.FALLBACK: 2,
            SourceRole.RECONCILIATION: 3,
            SourceRole.ARCHIVE: 4,
        }
        routes.sort(
            key=lambda route: (
                role_order[route.binding.role],
                route.binding.priority,
                route.source.source_id,
            )
        )
        return tuple(routes)

    def primary_route(
        self,
        dataset_id: str,
        required_capabilities: Iterable[
            SourceCapability
        ] = (),
        *,
        target_date: date | None = None,
    ) -> SourceRoute:
        routes = self.routes_for(
            dataset_id,
            required_capabilities,
            roles=(SourceRole.PRIMARY,),
            target_date=target_date,
        )
        if not routes:
            raise DataContractError(
                f"没有可用主来源：{dataset_id}"
            )
        return routes[0]
