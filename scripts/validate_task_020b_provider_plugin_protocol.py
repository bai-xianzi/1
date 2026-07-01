from __future__ import annotations

import argparse
import json
from pathlib import Path

from a_stock_quant.provider_capabilities import (
    load_provider_capability_matrix,
    load_single_machine_resource_profile,
)
from a_stock_quant.provider_plugin_protocol import (
    PluginRegistrationStatus,
    load_provider_plugin_protocol_config,
    load_provider_plugin_registry,
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    args = parser.parse_args()
    root = Path(args.project_root).resolve()

    matrix = load_provider_capability_matrix(
        root
        / "configs"
        / "providers"
        / "provider_capability_matrix_v0.json"
    )
    profile = load_single_machine_resource_profile(
        root
        / "configs"
        / "runtime"
        / "windows_single_machine_resource_profile_v0.json"
    )
    protocol = load_provider_plugin_protocol_config(
        root
        / "configs"
        / "providers"
        / "provider_plugin_protocol_v0.json"
    )
    registry = load_provider_plugin_registry(
        root
        / "configs"
        / "providers"
        / "provider_plugin_registry_v0.json"
    )

    matrix_ids = {
        target.provider_id for target in matrix.provider_targets
    }
    registry_ids = {
        entry.provider_id for entry in registry.entries
    }

    require(matrix_ids == registry_ids, "注册表与能力矩阵目标不一致")
    require(len(protocol.required_plugin_methods) == 9, "插件方法数量异常")
    require(
        len(protocol.required_discovery_sections) == 12,
        "发现结果分区数量异常",
    )
    require(
        all(not entry.enabled_for_routing for entry in registry.entries),
        "种子注册表错误启用了路由",
    )
    require(
        all(
            entry.registration_status
            in {
                PluginRegistrationStatus.REGISTERED_TARGET,
                PluginRegistrationStatus.LEGACY_BRIDGE_REQUIRED,
            }
            for entry in registry.entries
        ),
        "种子注册表包含超前生命周期",
    )
    require(
        registry.entry("wind").entrypoint is None,
        "Wind被错误声明为已实现插件",
    )
    require(
        registry.entry("ifind").entrypoint is None,
        "iFinD被错误声明为已实现插件",
    )
    require(
        registry.entry("galaxy_xingyao").entrypoint is None,
        "银河星耀数智被错误声明为已实现插件",
    )
    require(
        profile.max_parallel_provider_calls <= 2,
        "插件协议未遵守单机并发边界",
    )
    require(
        profile.maximum_batch_rows_without_override == 100000,
        "插件协议未遵守单机批次边界",
    )

    output = {
        "task_id": "TASK_020B",
        "overall_status": "PASSED",
        "protocol_version": protocol.protocol_version,
        "registry_version": registry.registry_version,
        "provider_target_count": len(registry.entries),
        "required_plugin_method_count": len(
            protocol.required_plugin_methods
        ),
        "required_discovery_section_count": len(
            protocol.required_discovery_sections
        ),
        "route_score_weight_total": sum(
            protocol.route_score_weights.values()
        ),
        "enabled_seed_route_count": sum(
            entry.enabled_for_routing
            for entry in registry.entries
        ),
        "registered_target_count": sum(
            entry.registration_status
            is PluginRegistrationStatus.REGISTERED_TARGET
            for entry in registry.entries
        ),
        "legacy_bridge_required_count": sum(
            entry.registration_status
            is PluginRegistrationStatus.LEGACY_BRIDGE_REQUIRED
            for entry in registry.entries
        ),
        "provider_neutral": protocol.provider_neutral,
        "automatic_plugin_activation_allowed": (
            protocol.automatic_plugin_activation_allowed
        ),
        "secret_material_allowed": protocol.secret_material_allowed,
        "network_probe_during_validation_allowed": (
            protocol.network_probe_during_validation_allowed
        ),
        "database_probe_during_validation_allowed": (
            protocol.database_probe_during_validation_allowed
        ),
        "max_parallel_provider_calls": (
            profile.max_parallel_provider_calls
        ),
        "maximum_batch_rows_without_override": (
            profile.maximum_batch_rows_without_override
        ),
        "database_connection_attempted": False,
        "commercial_sdk_import_attempted": False,
        "write_operation_count": 0,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
