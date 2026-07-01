# 本脚本核心功能：验证任务020bProvider插件协议的合同、配置和结果。
# - 输入：命令行参数、项目配置、数据服务结果以及已有验收文件。
# - 处理：按既定任务顺序执行读取、校验、汇总和失败门禁，不改变核心金融算法。
# - 输出：终端信息、报告内容或进程退出码，供后续人工验收和自动化流程判断。
# - 为什么这样写：把运维与验收编排集中在脚本层，避免环境操作混入核心业务模块。
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


# 函数 `require`：完成强制校验相关处理。
# - 输入：condition、message。
# - 处理：完成强制校验相关处理，并按现有异常和门禁规则保留失败证据。
# - 输出：返回类型约定为 `None`。
# - 为什么这样写：把独立步骤封装为清晰逻辑边界，便于复用、测试和定位验收失败。
def require(condition: bool, message: str) -> None:
    # 条件分支：检查 `not condition` 后选择对应处理路径。
    # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
    # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
    if not condition:
        # 失败门禁：抛出 `RuntimeError(message)`，立即终止当前不可信路径。
        # - 为什么这样写：验收或合同不满足时必须失败保守，不能静默生成正式结果。
        raise RuntimeError(message)


# 函数 `main`：组织命令行入口、依次执行本脚本的核心步骤并返回进程退出状态。
# - 输入：无显式参数，使用模块配置、环境或闭包状态。
# - 处理：组织命令行入口、依次执行本脚本的核心步骤并返回进程退出状态，并按现有异常和门禁规则保留失败证据。
# - 输出：返回类型约定为 `int`。
# - 为什么这样写：把独立步骤封装为清晰逻辑边界，便于复用、测试和定位验收失败。
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
    # 输出结果：返回 `0` 给调用方。
    # - 为什么这样写：明确函数边界的最终状态，便于上层继续汇总或设置退出码。
    return 0


# 脚本入口门禁：仅在本文件被直接运行时启动主流程。
# - 处理：作为模块导入时不自动执行，直接运行时调用main并传递退出状态。
# - 为什么这样写：区分可复用导入与命令行执行，避免测试或其他脚本导入时产生副作用。
if __name__ == "__main__":
    # 进程退出：使用 `SystemExit(main())` 把主流程状态返回给命令行调用方。
    # - 为什么这样写：明确成功或失败退出码，便于PowerShell、CI和人工验收判断运行结果。
    raise SystemExit(main())
