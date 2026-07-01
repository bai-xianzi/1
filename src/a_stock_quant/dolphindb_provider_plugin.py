"""TASK_020C：现有DolphinDB Adapter的通用Provider插件薄桥接。

本模块只负责协议编排，不重新实现：
- DolphinDB连接；
- 只读脚本安全检查；
- 原始表读取；
- DolphinDB返回值标准化。

上述行为全部委托给DolphinDBDataSourceAdapter。
"""
from __future__ import annotations

import importlib.metadata
import importlib.util
import json
import os
import platform
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterator, Mapping

from .data_contracts import DataContractError
from .dolphindb_adapter import DolphinDBDataSourceAdapter
from .provider_capabilities import CapabilityImplementationStatus
from .provider_plugin_protocol import (
    AuthenticationReference,
    AuthenticationReferenceKind,
    BatchPolicy,
    DiscoveryOutcome,
    LicenseBoundary,
    LicenseDecision,
    PaginationMode,
    PaginationPolicy,
    PluginRegistrationStatus,
    PolicyEvidenceStatus,
    ProviderDiscoveryResult,
    ProviderHealthSnapshot,
    ProviderHealthStatus,
    ProviderQueryBatch,
    ProviderQueryRequest,
    ProviderRegistryEntry,
    ProviderSubscriptionRequest,
    RateLimitPolicy,
    RetryPolicy,
    SdkRuntimeDescriptor,
    SubscriptionMode,
    SubscriptionPolicy,
)


RuntimeProbe = Callable[[], Mapping[str, Any]]


def _require_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DataContractError(f"{field_name}不能为空。")
    return value.strip()


def _positive_int(value: Any, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise DataContractError(f"{field_name}必须是正整数。")
    return value


def _normalise_records_with_legacy_adapter(
    adapter: DolphinDBDataSourceAdapter,
    result: Any,
) -> tuple[list[str], list[dict[str, Any]]]:
    normaliser = getattr(adapter, "_normalise_records", None)
    if not callable(normaliser):
        raise DataContractError(
            "现有DolphinDB Adapter缺少结果标准化能力。"
        )
    fields, records = normaliser(result)
    return list(fields), [dict(item) for item in records]


@dataclass(frozen=True, slots=True)
class DolphinDBProviderPluginBridgeConfig:
    task_id: str
    bridge_version: str
    bridge_status: str
    provider_id: str
    plugin_id: str
    entrypoint: str
    legacy_adapter_class: str
    reuse_strategy: str
    custom_query_engine_implemented: bool
    custom_session_engine_implemented: bool
    custom_dolphindb_protocol_implemented: bool
    authentication_reference: AuthenticationReference
    operating_systems: tuple[str, ...]
    architecture: str
    sdk_name: str
    installation_probe: str
    capabilities: Mapping[
        str,
        CapabilityImplementationStatus,
    ]
    permitted_usages: tuple[str, ...]
    rate_limit_policy: RateLimitPolicy
    retry_policy: RetryPolicy
    batch_policy: BatchPolicy
    pagination_policy: PaginationPolicy
    subscription_policy: SubscriptionPolicy
    license_boundary: LicenseBoundary
    supported_operations: tuple[str, ...]
    activation_policy: Mapping[str, bool]
    hard_rules: tuple[str, ...]

    def __post_init__(self) -> None:
        for field_name in (
            "task_id",
            "bridge_version",
            "bridge_status",
            "provider_id",
            "plugin_id",
            "entrypoint",
            "legacy_adapter_class",
            "reuse_strategy",
            "architecture",
            "sdk_name",
            "installation_probe",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_text(getattr(self, field_name), field_name),
            )
        if self.task_id != "TASK_020C":
            raise DataContractError("桥接配置task_id异常。")
        if self.provider_id != "local_dolphindb":
            raise DataContractError("桥接配置provider_id异常。")
        if self.reuse_strategy != "WRAP_WITH_THIN_ADAPTER":
            raise DataContractError("DolphinDB必须使用薄桥接复用策略。")
        if any(
            (
                self.custom_query_engine_implemented,
                self.custom_session_engine_implemented,
                self.custom_dolphindb_protocol_implemented,
            )
        ):
            raise DataContractError("桥接层不得重写DolphinDB核心能力。")
        if (
            self.authentication_reference.kind
            is not AuthenticationReferenceKind.ENVIRONMENT_VARIABLE
        ):
            raise DataContractError("DolphinDB密码必须使用环境变量引用。")
        if not self.authentication_reference.locator.startswith("env://"):
            raise DataContractError("DolphinDB认证引用必须使用env://。")
        operating_systems = tuple(
            _require_text(value, "operating_systems")
            for value in self.operating_systems
        )
        if not operating_systems:
            raise DataContractError("operating_systems不能为空。")
        object.__setattr__(
            self,
            "operating_systems",
            operating_systems,
        )
        capabilities = {
            _require_text(key, "capability"): (
                value
                if isinstance(value, CapabilityImplementationStatus)
                else CapabilityImplementationStatus(str(value))
            )
            for key, value in self.capabilities.items()
        }
        if "EOD_MARKET_DATA" not in capabilities:
            raise DataContractError("桥接配置必须包含EOD_MARKET_DATA。")
        object.__setattr__(self, "capabilities", capabilities)
        usages = tuple(
            _require_text(value, "permitted_usages")
            for value in self.permitted_usages
        )
        if not usages or len(usages) != len(set(usages)):
            raise DataContractError("permitted_usages必须非空且唯一。")
        object.__setattr__(self, "permitted_usages", usages)
        operations = tuple(
            _require_text(value, "supported_operations")
            for value in self.supported_operations
        )
        expected_operations = {
            "READ_RAW_TABLE",
            "RUN_READONLY_QUERY",
        }
        if set(operations) != expected_operations:
            raise DataContractError("桥接支持操作集合异常。")
        object.__setattr__(self, "supported_operations", operations)
        if self.pagination_policy.mode is not PaginationMode.NONE:
            raise DataContractError("当前薄桥接不得虚构分页能力。")
        if self.subscription_policy.mode is not SubscriptionMode.NONE:
            raise DataContractError("当前薄桥接不得虚构订阅能力。")
        if self.batch_policy.maximum_rows_per_batch > 100000:
            raise DataContractError("桥接批次超过现有Adapter上限。")
        required_activation_keys = {
            "modify_registry_during_acceptance",
            "modify_capability_matrix_during_acceptance",
            "automatic_activation_allowed",
            "activation_requires_verified_report",
        }
        if set(self.activation_policy) != required_activation_keys:
            raise DataContractError("activation_policy字段异常。")
        if any(
            (
                self.activation_policy[
                    "modify_registry_during_acceptance"
                ],
                self.activation_policy[
                    "modify_capability_matrix_during_acceptance"
                ],
                self.activation_policy[
                    "automatic_activation_allowed"
                ],
            )
        ):
            raise DataContractError("真实验收不得自动修改或激活路由。")
        if not self.activation_policy[
            "activation_requires_verified_report"
        ]:
            raise DataContractError("激活必须要求验收报告。")


def load_dolphindb_provider_plugin_bridge_config(
    path: str | Path,
) -> DolphinDBProviderPluginBridgeConfig:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise DataContractError("DolphinDB桥接配置根节点必须是对象。")
    auth = raw["authentication_reference"]
    runtime = raw["runtime"]
    rate = raw["rate_limit_policy"]
    retry = raw["retry_policy"]
    batch = raw["batch_policy"]
    pagination = raw["pagination_policy"]
    subscription = raw["subscription_policy"]
    license_raw = raw["license_boundary"]
    return DolphinDBProviderPluginBridgeConfig(
        task_id=str(raw["task_id"]),
        bridge_version=str(raw["bridge_version"]),
        bridge_status=str(raw["bridge_status"]),
        provider_id=str(raw["provider_id"]),
        plugin_id=str(raw["plugin_id"]),
        entrypoint=str(raw["entrypoint"]),
        legacy_adapter_class=str(raw["legacy_adapter_class"]),
        reuse_strategy=str(raw["reuse_strategy"]),
        custom_query_engine_implemented=bool(
            raw["custom_query_engine_implemented"]
        ),
        custom_session_engine_implemented=bool(
            raw["custom_session_engine_implemented"]
        ),
        custom_dolphindb_protocol_implemented=bool(
            raw["custom_dolphindb_protocol_implemented"]
        ),
        authentication_reference=AuthenticationReference(
            reference_id=str(auth["reference_id"]),
            kind=AuthenticationReferenceKind(str(auth["kind"])),
            locator=str(auth["locator"]),
            scopes=tuple(str(value) for value in auth["scopes"]),
        ),
        operating_systems=tuple(
            str(value) for value in runtime["operating_systems"]
        ),
        architecture=str(runtime["architecture"]),
        sdk_name=str(runtime["sdk_name"]),
        installation_probe=str(runtime["installation_probe"]),
        capabilities={
            str(key): CapabilityImplementationStatus(str(value))
            for key, value in raw["capabilities"].items()
        },
        permitted_usages=tuple(
            str(value) for value in raw["permitted_usages"]
        ),
        rate_limit_policy=RateLimitPolicy(
            requests_per_period=rate["requests_per_period"],
            period_seconds=rate["period_seconds"],
            burst_size=rate["burst_size"],
            maximum_concurrency=int(rate["maximum_concurrency"]),
            evidence_status=PolicyEvidenceStatus(
                str(rate["evidence_status"])
            ),
            evidence_refs=tuple(
                str(value) for value in rate["evidence_refs"]
            ),
        ),
        retry_policy=RetryPolicy(
            maximum_attempts=int(retry["maximum_attempts"]),
            backoff_seconds=tuple(
                int(value) for value in retry["backoff_seconds"]
            ),
            retryable_error_codes=tuple(
                str(value)
                for value in retry["retryable_error_codes"]
            ),
        ),
        batch_policy=BatchPolicy(
            recommended_entities_per_request=int(
                batch["recommended_entities_per_request"]
            ),
            maximum_entities_per_request=int(
                batch["maximum_entities_per_request"]
            ),
            recommended_rows_per_batch=int(
                batch["recommended_rows_per_batch"]
            ),
            maximum_rows_per_batch=int(
                batch["maximum_rows_per_batch"]
            ),
            supports_date_range=bool(batch["supports_date_range"]),
            supports_parallel_requests=bool(
                batch["supports_parallel_requests"]
            ),
        ),
        pagination_policy=PaginationPolicy(
            mode=PaginationMode(str(pagination["mode"])),
            default_page_size=pagination["default_page_size"],
            maximum_page_size=pagination["maximum_page_size"],
            maximum_pages=pagination["maximum_pages"],
            cursor_field=pagination["cursor_field"],
        ),
        subscription_policy=SubscriptionPolicy(
            mode=SubscriptionMode(str(subscription["mode"])),
            maximum_symbols=subscription["maximum_symbols"],
            heartbeat_seconds=subscription["heartbeat_seconds"],
            reconnect_supported=bool(
                subscription["reconnect_supported"]
            ),
            replay_supported=bool(subscription["replay_supported"]),
        ),
        license_boundary=LicenseBoundary(
            decision=LicenseDecision(str(license_raw["decision"])),
            permitted_usages=tuple(
                str(value)
                for value in license_raw["permitted_usages"]
            ),
            cache_allowed=bool(license_raw["cache_allowed"]),
            persistent_storage_allowed=bool(
                license_raw["persistent_storage_allowed"]
            ),
            redistribution_allowed=bool(
                license_raw["redistribution_allowed"]
            ),
            maximum_retention_days=license_raw[
                "maximum_retention_days"
            ],
            evidence_refs=tuple(
                str(value)
                for value in license_raw["evidence_refs"]
            ),
        ),
        supported_operations=tuple(
            str(value) for value in raw["supported_operations"]
        ),
        activation_policy={
            str(key): bool(value)
            for key, value in raw["activation_policy"].items()
        },
        hard_rules=tuple(str(value) for value in raw["hard_rules"]),
    )


def default_dolphindb_runtime_probe() -> Mapping[str, Any]:
    spec = importlib.util.find_spec("dolphindb")
    installed = spec is not None
    version = None
    if installed:
        try:
            version = importlib.metadata.version("dolphindb")
        except importlib.metadata.PackageNotFoundError:
            version = "unknown"
    return {
        "installed": installed,
        "sdk_version": version,
        "python_version": (
            f"{sys.version_info.major}.{sys.version_info.minor}"
        ),
        "operating_system": platform.system() or "Unknown",
        "architecture": platform.machine() or "unknown",
        "probe": "importlib.util.find_spec + importlib.metadata.version",
    }


class DolphinDBProviderPluginBridge:
    """复用DolphinDBDataSourceAdapter的通用Provider插件桥。"""

    def __init__(
        self,
        *,
        adapter: DolphinDBDataSourceAdapter,
        config: DolphinDBProviderPluginBridgeConfig,
        runtime_probe: RuntimeProbe | None = None,
    ) -> None:
        if adapter is None:
            raise DataContractError("adapter不能为空。")
        if not isinstance(config, DolphinDBProviderPluginBridgeConfig):
            raise DataContractError("config类型异常。")
        self._adapter = adapter
        self.config = config
        self._runtime_probe = (
            runtime_probe or default_dolphindb_runtime_probe
        )
        self._session_open = False

    @property
    def adapter(self) -> DolphinDBDataSourceAdapter:
        return self._adapter

    def describe(self) -> ProviderRegistryEntry:
        return ProviderRegistryEntry(
            provider_id=self.config.provider_id,
            plugin_id=self.config.plugin_id,
            registration_status=(
                PluginRegistrationStatus.DISCOVERY_PENDING
            ),
            entrypoint=self.config.entrypoint,
            priority=10,
            enabled_for_routing=False,
            discovery_result_ref=None,
            authentication_reference_ref=(
                self.config.authentication_reference.locator
            ),
            notes=(
                "薄桥接复用DolphinDBDataSourceAdapter；"
                "真实验收前不启用路由。"
            ),
        )

    def health_check(self) -> ProviderHealthSnapshot:
        started = time.perf_counter()
        result = self._adapter.health_check()
        latency_ms = (time.perf_counter() - started) * 1000.0
        status_value = getattr(
            getattr(result, "status", None),
            "value",
            str(getattr(result, "status", "")),
        ).upper()
        blocking = bool(getattr(result, "blocking", False))
        if status_value == "PASSED" and not blocking:
            status = ProviderHealthStatus.HEALTHY
        elif status_value in {"WARNING", "WARN"} and not blocking:
            status = ProviderHealthStatus.DEGRADED
        else:
            status = ProviderHealthStatus.UNAVAILABLE
        description = str(
            getattr(result, "description", "DolphinDB health check")
        ).strip() or "DolphinDB health check"
        return ProviderHealthSnapshot(
            status=status,
            checked_at=datetime.now(timezone.utc),
            latency_ms=latency_ms,
            message=description,
            evidence_refs=(
                "legacy-adapter:DolphinDBDataSourceAdapter.health_check",
            ),
        )

    def discover(self) -> ProviderDiscoveryResult:
        runtime_raw = dict(self._runtime_probe())
        installed = bool(runtime_raw.get("installed"))
        health = self.health_check()
        errors: list[str] = []
        warnings: list[str] = [
            "LEGACY_ADAPTER_BRIDGE",
            "REGISTRY_ACTIVATION_REQUIRES_SEPARATE_TASK",
        ]
        if not installed:
            errors.append("DOLPHINDB_PYTHON_CLIENT_NOT_INSTALLED")
        if health.status is ProviderHealthStatus.UNAVAILABLE:
            errors.append("DOLPHINDB_HEALTH_UNAVAILABLE")
        outcome = (
            DiscoveryOutcome.COMPLETE
            if not errors
            else DiscoveryOutcome.FAILED
        )
        runtime = SdkRuntimeDescriptor(
            provider_id=self.config.provider_id,
            runtime_id=(
                f"runtime:{self.config.provider_id}:"
                f"{runtime_raw.get('sdk_version') or 'unknown'}"
            ),
            operating_systems=(
                str(
                    runtime_raw.get("operating_system")
                    or self.config.operating_systems[0]
                ),
            ),
            python_versions=(
                str(
                    runtime_raw.get("python_version")
                    or f"{sys.version_info.major}."
                    f"{sys.version_info.minor}"
                ),
            ),
            architecture=str(
                runtime_raw.get("architecture")
                or self.config.architecture
            ),
            client_name="Local DolphinDB Server",
            client_version=None,
            sdk_name=self.config.sdk_name,
            sdk_version=(
                str(runtime_raw["sdk_version"])
                if runtime_raw.get("sdk_version") is not None
                else None
            ),
            installed=installed,
            installation_probe=str(
                runtime_raw.get("probe")
                or self.config.installation_probe
            ),
            notes=(
                "仅探测Python客户端并复用现有Adapter；"
                "不重新实现DolphinDB协议。"
            ),
        )
        return ProviderDiscoveryResult(
            discovery_id=(
                f"discovery:{self.config.provider_id}:"
                f"{datetime.now(timezone.utc).isoformat()}"
            ),
            provider_id=self.config.provider_id,
            plugin_id=self.config.plugin_id,
            outcome=outcome,
            discovered_at=datetime.now(timezone.utc),
            runtime=runtime,
            authentication_reference=(
                self.config.authentication_reference
            ),
            capabilities=self.config.capabilities,
            rate_limit_policy=self.config.rate_limit_policy,
            retry_policy=self.config.retry_policy,
            batch_policy=self.config.batch_policy,
            pagination_policy=self.config.pagination_policy,
            subscription_policy=self.config.subscription_policy,
            license_boundary=self.config.license_boundary,
            health=health,
            warnings=tuple(warnings),
            errors=tuple(errors),
        )

    def open_session(
        self,
        authentication_reference: AuthenticationReference,
    ) -> None:
        if (
            authentication_reference.reference_id
            != self.config.authentication_reference.reference_id
            or authentication_reference.kind
            is not self.config.authentication_reference.kind
            or authentication_reference.locator
            != self.config.authentication_reference.locator
        ):
            raise DataContractError("认证引用与桥接配置不一致。")
        env_name = authentication_reference.locator.removeprefix(
            "env://"
        )
        if not env_name or not os.environ.get(env_name):
            raise DataContractError(
                f"环境变量未设置：{env_name or '<empty>'}"
            )
        self._session_open = True

    def close_session(self) -> None:
        close_method = getattr(self._adapter, "close", None)
        if callable(close_method):
            close_method()
        self._session_open = False

    def _assert_request(self, request: ProviderQueryRequest) -> None:
        if not self._session_open:
            raise DataContractError("Provider插件会话尚未打开。")
        if request.provider_id != self.config.provider_id:
            raise DataContractError("请求provider_id与插件不一致。")
        if request.capability not in self.config.capabilities:
            raise DataContractError("请求能力未在桥接配置中登记。")
        capability_status = self.config.capabilities[
            request.capability
        ]
        if capability_status not in {
            CapabilityImplementationStatus.IMPLEMENTED,
            CapabilityImplementationStatus.VERIFIED,
        }:
            raise DataContractError("请求能力尚未实现或验证。")
        if request.usage not in self.config.permitted_usages:
            raise DataContractError("请求用途不在本地数据许可范围。")
        if (
            request.maximum_rows
            > self.config.batch_policy.maximum_rows_per_batch
        ):
            raise DataContractError("请求行数超过桥接批次上限。")
        if request.operation not in self.config.supported_operations:
            raise DataContractError("桥接不支持请求操作。")

    def query_batch(
        self,
        request: ProviderQueryRequest,
    ) -> ProviderQueryBatch:
        self._assert_request(request)
        warnings = ["LEGACY_ADAPTER_BRIDGE"]
        if request.operation == "READ_RAW_TABLE":
            source_object_name = _require_text(
                request.parameters.get("source_object_name"),
                "source_object_name",
            )
            database_uri = _require_text(
                request.parameters.get("database_uri"),
                "database_uri",
            )
            raw_batch = self._adapter.read_raw(
                source_object_name,
                database_uri=database_uri,
                limit=request.maximum_rows,
            )
            records = tuple(
                dict(item) for item in raw_batch.records
            )
            source_request_id = (
                f"{database_uri}/{source_object_name}"
            )
        elif request.operation == "RUN_READONLY_QUERY":
            script = _require_text(
                request.parameters.get("script"),
                "script",
            )
            result = self._adapter.run_readonly_query(script)
            _, normalised = _normalise_records_with_legacy_adapter(
                self._adapter,
                result,
            )
            if len(normalised) > request.maximum_rows:
                raise DataContractError(
                    "只读查询返回行数超过请求maximum_rows；"
                    "请在查询中显式限制结果。"
                )
            records = tuple(normalised)
            source_request_id = request.request_id
            warnings.append(
                "RESULT_NORMALISED_BY_LEGACY_ADAPTER"
            )
        else:
            raise DataContractError("桥接不支持请求操作。")

        return ProviderQueryBatch(
            request_id=request.request_id,
            provider_id=self.config.provider_id,
            capability=request.capability,
            records=records,
            next_cursor=None,
            source_request_id=source_request_id,
            warnings=tuple(warnings),
        )

    def iter_pages(
        self,
        request: ProviderQueryRequest,
    ) -> Iterator[ProviderQueryBatch]:
        yield self.query_batch(request)

    def subscribe(
        self,
        request: ProviderSubscriptionRequest,
    ) -> str:
        del request
        raise DataContractError(
            "当前DolphinDB薄桥接不支持实时订阅。"
        )

    def unsubscribe(self, subscription_id: str) -> None:
        _require_text(subscription_id, "subscription_id")
        raise DataContractError(
            "当前DolphinDB薄桥接不支持实时订阅。"
        )
