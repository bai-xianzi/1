# 本脚本核心功能：验证任务020cDolphinDB插件桥接的合同、配置和结果。
# - 输入：命令行参数、项目配置、数据服务结果以及已有验收文件。
# - 处理：按既定任务顺序执行读取、校验、汇总和失败门禁，不改变核心金融算法。
# - 输出：终端信息、报告内容或进程退出码，供后续人工验收和自动化流程判断。
# - 为什么这样写：把运维与验收编排集中在脚本层，避免环境操作混入核心业务模块。
from __future__ import annotations

import argparse
import json
from pathlib import Path

from a_stock_quant.dolphindb_provider_plugin import (
    load_dolphindb_provider_plugin_bridge_config,
)
from a_stock_quant.provider_capabilities import (
    CapabilityImplementationStatus,
    load_provider_capability_matrix,
    load_single_machine_resource_profile,
)
from a_stock_quant.provider_plugin_protocol import (
    PluginRegistrationStatus,
    load_provider_plugin_protocol_config,
    load_provider_plugin_registry,
)
from a_stock_quant.reuse_first_policy import (
    ReuseDecisionType,
    ReviewStatus,
    ReuseCandidateAssessment,
    ReuseCandidateType,
    ReuseDecisionRecord,
    load_reuse_first_policy,
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

    config = load_dolphindb_provider_plugin_bridge_config(
        root
        / "configs"
        / "providers"
        / "dolphindb_provider_plugin_bridge_v0.json"
    )
    matrix = load_provider_capability_matrix(
        root
        / "configs"
        / "providers"
        / "provider_capability_matrix_v0.json"
    )
    registry = load_provider_plugin_registry(
        root
        / "configs"
        / "providers"
        / "provider_plugin_registry_v0.json"
    )
    protocol = load_provider_plugin_protocol_config(
        root
        / "configs"
        / "providers"
        / "provider_plugin_protocol_v0.json"
    )
    profile = load_single_machine_resource_profile(
        root
        / "configs"
        / "runtime"
        / "windows_single_machine_resource_profile_v0.json"
    )
    reuse_policy = load_reuse_first_policy(
        root
        / "configs"
        / "engineering"
        / "reuse_first_policy_v0.json"
    )

    local_target = matrix.provider("local_dolphindb")
    local_entry = registry.entry("local_dolphindb")

    require(
        local_entry.registration_status
        is PluginRegistrationStatus.LEGACY_BRIDGE_REQUIRED,
        "真实验收前种子注册表状态应保持LEGACY_BRIDGE_REQUIRED",
    )
    require(
        not local_entry.enabled_for_routing,
        "真实验收前不得启用DolphinDB插件路由",
    )
    require(
        config.provider_id == local_target.provider_id,
        "桥接配置与能力矩阵provider_id不一致",
    )
    require(
        set(config.capabilities).issubset(
            set(matrix.capability_catalog)
        ),
        "桥接配置包含未登记标准能力",
    )
    require(
        config.capabilities["EOD_MARKET_DATA"]
        is CapabilityImplementationStatus.VERIFIED,
        "日K能力没有标记为VERIFIED",
    )
    require(
        config.batch_policy.maximum_rows_per_batch
        <= profile.maximum_batch_rows_without_override,
        "桥接批次超过单机资源上限",
    )
    require(
        config.rate_limit_policy.maximum_concurrency
        <= profile.max_parallel_provider_calls,
        "桥接并发超过单机资源上限",
    )
    require(
        len(protocol.required_plugin_methods) == 9,
        "ProviderPlugin方法合同异常",
    )
    require(
        reuse_policy.principle
        == "REUSE_FIRST_CUSTOM_BUILD_LAST",
        "复用优先政策未生效",
    )
    require(
        config.reuse_strategy == "WRAP_WITH_THIN_ADAPTER",
        "桥接没有采用薄适配策略",
    )
    require(
        not config.custom_query_engine_implemented,
        "桥接错误重写查询引擎",
    )
    require(
        not config.custom_session_engine_implemented,
        "桥接错误重写会话引擎",
    )
    require(
        not config.custom_dolphindb_protocol_implemented,
        "桥接错误重写DolphinDB协议",
    )
    require(
        (
            root
            / "reports"
            / "task_020c_dolphindb_bridge_reuse_decision.json"
        ).exists(),
        "缺少复用决策证据",
    )

    existing = ReuseCandidateAssessment(
        candidate_id="existing-dolphindb-adapter",
        candidate_type=(
            ReuseCandidateType.EXISTING_PROJECT_COMPONENT
        ),
        name="DolphinDBDataSourceAdapter",
        source_ref="repo:src/a_stock_quant/dolphindb_adapter.py",
        version="current-main",
        license_id="PROJECT_INTERNAL",
        license_status=ReviewStatus.PASSED,
        security_status=ReviewStatus.PASSED,
        maintenance_status=ReviewStatus.PASSED,
        compatibility_status=ReviewStatus.PASSED,
        semantic_gap_status=ReviewStatus.PASSED_WITH_WARNINGS,
        supported_requirements=(
            "health_check",
            "read_raw",
            "run_readonly_query",
        ),
        gaps=("provider_plugin_protocol",),
        warnings=("thin_bridge_required",),
        evidence_refs=(
            "repo:src/a_stock_quant/dolphindb_adapter.py",
        ),
    )
    decision = ReuseDecisionRecord(
        decision_id="reuse:task_020c:dolphindb_adapter_bridge",
        problem_statement="Bridge existing adapter.",
        requirements=("provider_plugin_protocol",),
        candidates=(existing,),
        decision=ReuseDecisionType.WRAP_WITH_THIN_ADAPTER,
        selected_candidate_id=existing.candidate_id,
        rationale="Reuse existing adapter logic.",
        custom_build_evidence={},
        maintenance_owner=None,
        test_plan_ref="tests/test_dolphindb_provider_plugin.py",
        migration_path="replace adapter behind plugin boundary",
        evidence_refs=(
            "policy:configs/engineering/reuse_first_policy_v0.json",
        ),
    )
    require(
        decision.decision
        is ReuseDecisionType.WRAP_WITH_THIN_ADAPTER,
        "复用决策合同异常",
    )

    output = {
        "task_id": "TASK_020C",
        "overall_status": "PASSED",
        "bridge_version": config.bridge_version,
        "provider_id": config.provider_id,
        "plugin_id": config.plugin_id,
        "reuse_strategy": config.reuse_strategy,
        "legacy_adapter_class": config.legacy_adapter_class,
        "capability_count": len(config.capabilities),
        "supported_operation_count": len(
            config.supported_operations
        ),
        "maximum_rows_per_batch": (
            config.batch_policy.maximum_rows_per_batch
        ),
        "maximum_concurrency": (
            config.rate_limit_policy.maximum_concurrency
        ),
        "seed_registry_status": (
            local_entry.registration_status.value
        ),
        "seed_registry_route_enabled": (
            local_entry.enabled_for_routing
        ),
        "custom_query_engine_implemented": (
            config.custom_query_engine_implemented
        ),
        "custom_session_engine_implemented": (
            config.custom_session_engine_implemented
        ),
        "custom_dolphindb_protocol_implemented": (
            config.custom_dolphindb_protocol_implemented
        ),
        "network_connection_attempted": False,
        "database_connection_attempted": False,
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
