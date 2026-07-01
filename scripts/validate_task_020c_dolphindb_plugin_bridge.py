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


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
