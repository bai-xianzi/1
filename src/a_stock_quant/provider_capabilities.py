"""TASK_020A：供应商能力矩阵与单机资源档案合同。"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

from .data_contracts import DataContractError


class ProviderLifecycle(str, Enum):
    IMPLEMENTED_FOUNDATION = "IMPLEMENTED_FOUNDATION"
    REGISTERED_TARGET = "REGISTERED_TARGET"
    DISCOVERY_COMPLETE = "DISCOVERY_COMPLETE"
    ADAPTER_IMPLEMENTED = "ADAPTER_IMPLEMENTED"
    REAL_ACCEPTED = "REAL_ACCEPTED"
    ACTIVATED = "ACTIVATED"
    SUSPENDED = "SUSPENDED"


class ProviderDiscoveryStatus(str, Enum):
    VERIFIED_IN_PROJECT = "VERIFIED_IN_PROJECT"
    DISCOVERY_REQUIRED = "DISCOVERY_REQUIRED"
    DISCOVERY_PARTIAL = "DISCOVERY_PARTIAL"
    DISCOVERY_COMPLETE = "DISCOVERY_COMPLETE"


class CapabilityImplementationStatus(str, Enum):
    IMPLEMENTED = "IMPLEMENTED"
    VERIFIED = "VERIFIED"
    DECLARED_UNVERIFIED = "DECLARED_UNVERIFIED"
    NOT_AVAILABLE = "NOT_AVAILABLE"


def _require_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DataContractError(f"{field_name}不能为空。")
    return value.strip()


def _positive_int(value: Any, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise DataContractError(f"{field_name}必须是正整数。")
    return value


def _nonnegative_number(value: Any, field_name: str) -> float:
    if isinstance(value, bool):
        raise DataContractError(f"{field_name}必须是非负有限数。")
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise DataContractError(
            f"{field_name}必须是非负有限数。"
        ) from exc
    if not math.isfinite(result) or result < 0:
        raise DataContractError(f"{field_name}必须是非负有限数。")
    return result


@dataclass(frozen=True, slots=True)
class ProviderTarget:
    provider_id: str
    display_name: str
    provider_kind: str
    lifecycle: ProviderLifecycle
    integration_mode: str
    authentication_mode: str
    discovery_status: ProviderDiscoveryStatus
    capabilities: Mapping[str, CapabilityImplementationStatus]
    license_review_required: bool
    execution_capability: bool
    notes: str

    def __post_init__(self) -> None:
        for field_name in (
            "provider_id",
            "display_name",
            "provider_kind",
            "integration_mode",
            "authentication_mode",
            "notes",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_text(getattr(self, field_name), field_name),
            )
        lifecycle = self.lifecycle
        if isinstance(lifecycle, str):
            lifecycle = ProviderLifecycle(lifecycle)
        object.__setattr__(self, "lifecycle", lifecycle)
        discovery = self.discovery_status
        if isinstance(discovery, str):
            discovery = ProviderDiscoveryStatus(discovery)
        object.__setattr__(self, "discovery_status", discovery)
        capabilities = {
            _require_text(key, "capability"): (
                value
                if isinstance(value, CapabilityImplementationStatus)
                else CapabilityImplementationStatus(value)
            )
            for key, value in self.capabilities.items()
        }
        object.__setattr__(self, "capabilities", capabilities)
        if (
            discovery is ProviderDiscoveryStatus.DISCOVERY_REQUIRED
            and capabilities
        ):
            raise DataContractError(
                "待发现Provider不得预填具体能力。"
            )
        if (
            lifecycle is ProviderLifecycle.ACTIVATED
            and discovery
            is not ProviderDiscoveryStatus.DISCOVERY_COMPLETE
        ):
            raise DataContractError(
                "未完成能力发现的Provider不得激活。"
            )


@dataclass(frozen=True, slots=True)
class ProviderCapabilityMatrix:
    task_id: str
    matrix_version: str
    matrix_status: str
    provider_neutral: bool
    automatic_activation_allowed: bool
    secret_storage_allowed: bool
    core_system_may_import_vendor_sdk: bool
    upper_layers_may_depend_on_vendor_fields: bool
    required_adapter_contracts: tuple[str, ...]
    capability_catalog: tuple[str, ...]
    provider_targets: tuple[ProviderTarget, ...]
    routing_rules: tuple[str, ...]

    def __post_init__(self) -> None:
        for field_name in ("task_id", "matrix_version", "matrix_status"):
            object.__setattr__(
                self,
                field_name,
                _require_text(getattr(self, field_name), field_name),
            )
        if self.task_id != "TASK_020A":
            raise DataContractError("能力矩阵task_id异常。")
        if not self.provider_neutral:
            raise DataContractError("能力矩阵必须保持供应商中立。")
        if any(
            (
                self.automatic_activation_allowed,
                self.secret_storage_allowed,
                self.core_system_may_import_vendor_sdk,
                self.upper_layers_may_depend_on_vendor_fields,
            )
        ):
            raise DataContractError("供应商隔离硬约束被破坏。")
        for field_name in (
            "required_adapter_contracts",
            "capability_catalog",
            "routing_rules",
        ):
            values = tuple(
                _require_text(value, field_name)
                for value in getattr(self, field_name)
            )
            if not values or len(values) != len(set(values)):
                raise DataContractError(
                    f"{field_name}必须非空且唯一。"
                )
            object.__setattr__(self, field_name, values)
        ids = [item.provider_id for item in self.provider_targets]
        if not ids or len(ids) != len(set(ids)):
            raise DataContractError(
                "provider_targets必须非空且provider_id唯一。"
            )
        required_targets = {
            "local_dolphindb",
            "wind",
            "ifind",
            "galaxy_xingyao",
        }
        if not required_targets.issubset(ids):
            raise DataContractError("缺少强制供应商目标。")
        catalog = set(self.capability_catalog)
        for target in self.provider_targets:
            unknown = set(target.capabilities) - catalog
            if unknown:
                raise DataContractError(
                    f"{target.provider_id}包含未登记能力：{sorted(unknown)}"
                )

    def provider(self, provider_id: str) -> ProviderTarget:
        key = _require_text(provider_id, "provider_id")
        for target in self.provider_targets:
            if target.provider_id == key:
                return target
        raise DataContractError(f"未登记Provider：{key}")

    def eligible_providers(
        self,
        capability: str,
    ) -> tuple[ProviderTarget, ...]:
        key = _require_text(capability, "capability")
        if key not in self.capability_catalog:
            raise DataContractError(f"未登记标准能力：{key}")
        allowed_lifecycle = {
            ProviderLifecycle.REAL_ACCEPTED,
            ProviderLifecycle.ACTIVATED,
        }
        allowed_status = {
            CapabilityImplementationStatus.IMPLEMENTED,
            CapabilityImplementationStatus.VERIFIED,
        }
        return tuple(
            target
            for target in self.provider_targets
            if target.lifecycle in allowed_lifecycle
            and target.discovery_status
            in {
                ProviderDiscoveryStatus.VERIFIED_IN_PROJECT,
                ProviderDiscoveryStatus.DISCOVERY_COMPLETE,
            }
            and target.capabilities.get(key) in allowed_status
        )


@dataclass(frozen=True, slots=True)
class SingleMachineResourceProfile:
    task_id: str
    profile_version: str
    profile_status: str
    profile_id: str
    operating_system: str
    physical_core_count: int
    logical_thread_count: int
    memory_gib: int
    gpu_memory_gib: int
    architecture_mode: str
    max_parallel_provider_calls: int
    max_parallel_cpu_jobs: int
    max_parallel_database_queries: int
    default_batch_rows: int
    large_batch_rows: int
    maximum_batch_rows_without_override: int
    maximum_in_memory_result_mib: int
    process_memory_soft_limit_mib: int
    minimum_free_space_gib: float
    temporary_directory_quota_gib: float
    cache_quota_gib: float
    large_download_threshold_gib: float
    automatic_35gb_minute_data_import_allowed: bool
    gpu_enabled_by_default: bool
    hard_rules: tuple[str, ...]

    def __post_init__(self) -> None:
        for field_name in (
            "task_id",
            "profile_version",
            "profile_status",
            "profile_id",
            "operating_system",
            "architecture_mode",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_text(getattr(self, field_name), field_name),
            )
        if self.task_id != "TASK_020A":
            raise DataContractError("资源档案task_id异常。")
        for field_name in (
            "physical_core_count",
            "logical_thread_count",
            "memory_gib",
            "gpu_memory_gib",
            "max_parallel_provider_calls",
            "max_parallel_cpu_jobs",
            "max_parallel_database_queries",
            "default_batch_rows",
            "large_batch_rows",
            "maximum_batch_rows_without_override",
            "maximum_in_memory_result_mib",
            "process_memory_soft_limit_mib",
        ):
            object.__setattr__(
                self,
                field_name,
                _positive_int(getattr(self, field_name), field_name),
            )
        if self.logical_thread_count < self.physical_core_count:
            raise DataContractError("逻辑线程不能少于物理核心。")
        if self.max_parallel_provider_calls > 2:
            raise DataContractError("当前单机Provider并发不得超过2。")
        if self.max_parallel_cpu_jobs > 2:
            raise DataContractError("当前单机CPU并行任务不得超过2。")
        if self.max_parallel_database_queries > 2:
            raise DataContractError("当前单机数据库并发不得超过2。")
        if not (
            self.default_batch_rows
            <= self.large_batch_rows
            <= self.maximum_batch_rows_without_override
        ):
            raise DataContractError("批次行数层级异常。")
        for field_name in (
            "minimum_free_space_gib",
            "temporary_directory_quota_gib",
            "cache_quota_gib",
            "large_download_threshold_gib",
        ):
            object.__setattr__(
                self,
                field_name,
                _nonnegative_number(
                    getattr(self, field_name),
                    field_name,
                ),
            )
        if self.automatic_35gb_minute_data_import_allowed:
            raise DataContractError("不得自动导入35GB分钟线。")
        if self.gpu_enabled_by_default:
            raise DataContractError("GPU不得默认启用。")
        rules = tuple(
            _require_text(value, "hard_rules")
            for value in self.hard_rules
        )
        if not rules or len(rules) != len(set(rules)):
            raise DataContractError("hard_rules必须非空且唯一。")
        object.__setattr__(self, "hard_rules", rules)

    def choose_batch_rows(
        self,
        requested_rows: int | None = None,
    ) -> int:
        if requested_rows is None:
            return self.default_batch_rows
        value = _positive_int(requested_rows, "requested_rows")
        if value > self.maximum_batch_rows_without_override:
            raise DataContractError(
                "请求批次超过单机无人工覆盖上限。"
            )
        return value

    def assert_storage_safe(
        self,
        free_space_gib: float,
        planned_download_gib: float = 0,
    ) -> None:
        free_value = _nonnegative_number(
            free_space_gib,
            "free_space_gib",
        )
        planned_value = _nonnegative_number(
            planned_download_gib,
            "planned_download_gib",
        )
        remaining = free_value - planned_value
        if remaining < self.minimum_free_space_gib:
            raise DataContractError(
                "计划任务会使磁盘空间低于安全阈值。"
            )
        if planned_value > self.large_download_threshold_gib:
            raise DataContractError(
                "大文件下载必须取得人工覆盖授权。"
            )


def load_provider_capability_matrix(
    path: str | Path,
) -> ProviderCapabilityMatrix:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise DataContractError("能力矩阵根节点必须是对象。")
    targets = tuple(
        ProviderTarget(
            provider_id=str(item["provider_id"]),
            display_name=str(item["display_name"]),
            provider_kind=str(item["provider_kind"]),
            lifecycle=ProviderLifecycle(str(item["lifecycle"])),
            integration_mode=str(item["integration_mode"]),
            authentication_mode=str(item["authentication_mode"]),
            discovery_status=ProviderDiscoveryStatus(
                str(item["discovery_status"])
            ),
            capabilities={
                str(key): CapabilityImplementationStatus(str(value))
                for key, value in item["capabilities"].items()
            },
            license_review_required=bool(
                item["license_review_required"]
            ),
            execution_capability=bool(
                item["execution_capability"]
            ),
            notes=str(item["notes"]),
        )
        for item in raw["provider_targets"]
    )
    return ProviderCapabilityMatrix(
        task_id=str(raw["task_id"]),
        matrix_version=str(raw["matrix_version"]),
        matrix_status=str(raw["matrix_status"]),
        provider_neutral=bool(raw["provider_neutral"]),
        automatic_activation_allowed=bool(
            raw["automatic_activation_allowed"]
        ),
        secret_storage_allowed=bool(raw["secret_storage_allowed"]),
        core_system_may_import_vendor_sdk=bool(
            raw["core_system_may_import_vendor_sdk"]
        ),
        upper_layers_may_depend_on_vendor_fields=bool(
            raw["upper_layers_may_depend_on_vendor_fields"]
        ),
        required_adapter_contracts=tuple(
            str(value) for value in raw["required_adapter_contracts"]
        ),
        capability_catalog=tuple(
            str(value) for value in raw["capability_catalog"]
        ),
        provider_targets=targets,
        routing_rules=tuple(
            str(value) for value in raw["routing_rules"]
        ),
    )


def load_single_machine_resource_profile(
    path: str | Path,
) -> SingleMachineResourceProfile:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise DataContractError("资源档案根节点必须是对象。")
    machine = raw["machine"]
    execution = raw["default_execution"]
    storage = raw["storage_safety"]
    gpu = raw["gpu_policy"]
    return SingleMachineResourceProfile(
        task_id=str(raw["task_id"]),
        profile_version=str(raw["profile_version"]),
        profile_status=str(raw["profile_status"]),
        profile_id=str(raw["profile_id"]),
        operating_system=str(machine["operating_system"]),
        physical_core_count=int(machine["physical_core_count"]),
        logical_thread_count=int(machine["logical_thread_count"]),
        memory_gib=int(machine["memory_gib"]),
        gpu_memory_gib=int(machine["gpu_memory_gib"]),
        architecture_mode=str(raw["architecture_mode"]),
        max_parallel_provider_calls=int(
            execution["max_parallel_provider_calls"]
        ),
        max_parallel_cpu_jobs=int(
            execution["max_parallel_cpu_jobs"]
        ),
        max_parallel_database_queries=int(
            execution["max_parallel_database_queries"]
        ),
        default_batch_rows=int(execution["default_batch_rows"]),
        large_batch_rows=int(execution["large_batch_rows"]),
        maximum_batch_rows_without_override=int(
            execution["maximum_batch_rows_without_override"]
        ),
        maximum_in_memory_result_mib=int(
            execution["maximum_in_memory_result_mib"]
        ),
        process_memory_soft_limit_mib=int(
            execution["process_memory_soft_limit_mib"]
        ),
        minimum_free_space_gib=float(
            storage["minimum_free_space_gib"]
        ),
        temporary_directory_quota_gib=float(
            storage["temporary_directory_quota_gib"]
        ),
        cache_quota_gib=float(storage["cache_quota_gib"]),
        large_download_threshold_gib=float(
            storage["large_download_threshold_gib"]
        ),
        automatic_35gb_minute_data_import_allowed=bool(
            storage[
                "automatic_35gb_minute_data_import_allowed"
            ]
        ),
        gpu_enabled_by_default=bool(gpu["enabled_by_default"]),
        hard_rules=tuple(str(value) for value in raw["hard_rules"]),
    )
