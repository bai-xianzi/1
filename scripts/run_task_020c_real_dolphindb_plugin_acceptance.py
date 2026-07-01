"""TASK_020C真实DolphinDB Provider插件桥只读验收。"""
# 本脚本核心功能：执行任务020c真实DolphinDB插件验收的真实运行或验收流程。
# - 输入：命令行参数、项目配置、数据服务结果以及已有验收文件。
# - 处理：按既定任务顺序执行读取、校验、汇总和失败门禁，不改变核心金融算法。
# - 输出：终端信息、报告内容或进程退出码，供后续人工验收和自动化流程判断。
# - 为什么这样写：把运维与验收编排集中在脚本层，避免环境操作混入核心业务模块。
from __future__ import annotations

import argparse
import json
import os
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from a_stock_quant.dolphindb_adapter import (
    DolphinDBConnectionSettings,
    DolphinDBDataSourceAdapter,
)
from a_stock_quant.dolphindb_provider_plugin import (
    DolphinDBProviderPluginBridge,
    load_dolphindb_provider_plugin_bridge_config,
)
from a_stock_quant.provider_capabilities import (
    ProviderCapabilityMatrix,
    ProviderDiscoveryStatus,
    ProviderLifecycle,
    load_provider_capability_matrix,
)
from a_stock_quant.provider_plugin_protocol import (
    PluginRegistrationStatus,
    ProviderPluginRegistry,
    ProviderQueryRequest,
    ProviderRouteRequest,
    RouteDecision,
    build_provider_route_candidates,
    load_provider_plugin_protocol_config,
    load_provider_plugin_registry,
    object_to_dict,
)


# 函数 `_markdown`：完成markdown相关处理。
# - 输入：report。
# - 处理：完成markdown相关处理，并按现有异常和门禁规则保留失败证据。
# - 输出：返回类型约定为 `str`。
# - 为什么这样写：把独立步骤封装为清晰逻辑边界，便于复用、测试和定位验收失败。
def _markdown(report: Mapping[str, Any]) -> str:
    lines = [
        "# TASK_020C DolphinDB Provider插件桥真实验收",
        "",
        f"- 状态：**{report['overall_status']}**",
        f"- Provider：`{report['provider_id']}`",
        f"- 插件：`{report['plugin_id']}`",
        f"- 复用策略：`{report['reuse_strategy']}`",
        f"- 发现结果：`{report['discovery_outcome']}`",
        f"- 健康状态：`{report['health_status']}`",
        f"- 真实返回记录：{report['query_result_count']}",
        f"- 路由候选：`{report['route_decision']}`",
        f"- 路由得分：{report['route_score']:.4f}",
        "",
        "## 安全边界",
        "",
        "- 使用现有DolphinDBDataSourceAdapter；",
        "- 仅执行健康检查和有限只读查询；",
        "- 未修改真实Provider注册表；",
        "- 未修改真实能力矩阵；",
        "- 未执行数据库写入；",
        "- 未在报告中保存密码。",
        "",
    ]
    # 条件分支：检查 `report['warnings']` 后选择对应处理路径。
    # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
    # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
    if report["warnings"]:
        lines.extend(["## 警告", ""])
        lines.extend(
            f"- `{warning}`" for warning in report["warnings"]
        )
        lines.append("")
    # 条件分支：检查 `report['issues']` 后选择对应处理路径。
    # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
    # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
    if report["issues"]:
        lines.extend(["## 问题", ""])
        lines.extend(f"- `{issue}`" for issue in report["issues"])
        lines.append("")
    # 输出结果：返回 `'\n'.join(lines)` 给调用方。
    # - 为什么这样写：明确函数边界的最终状态，便于上层继续汇总或设置退出码。
    return "\n".join(lines)


# 函数 `build_parser`：完成构建parser相关处理。
# - 输入：无显式参数，使用模块配置、环境或闭包状态。
# - 处理：完成构建parser相关处理，并按现有异常和门禁规则保留失败证据。
# - 输出：返回类型约定为 `argparse.ArgumentParser`。
# - 为什么这样写：把独立步骤封装为清晰逻辑边界，便于复用、测试和定位验收失败。
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8848)
    parser.add_argument("--username", default="admin")
    parser.add_argument(
        "--password-env",
        default="DOLPHINDB_PASSWORD",
    )
    parser.add_argument(
        "--database-uri",
        default="dfs://A_STOCK_DAILY_K_DB",
    )
    parser.add_argument(
        "--table-name",
        default="stock_daily_k",
    )
    parser.add_argument("--limit", type=int, default=5)
    # 输出结果：返回 `parser` 给调用方。
    # - 为什么这样写：明确函数边界的最终状态，便于上层继续汇总或设置退出码。
    return parser


# 函数 `main`：组织命令行入口、依次执行本脚本的核心步骤并返回进程退出状态。
# - 输入：argv。
# - 处理：组织命令行入口、依次执行本脚本的核心步骤并返回进程退出状态，并按现有异常和门禁规则保留失败证据。
# - 输出：返回类型约定为 `int`。
# - 为什么这样写：把独立步骤封装为清晰逻辑边界，便于复用、测试和定位验收失败。
def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.project_root).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    password = os.environ.get(args.password_env)
    # 条件分支：检查 `not password` 后选择对应处理路径。
    # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
    # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
    if not password:
        # 失败门禁：抛出 `RuntimeError(f'环境变量未设置：{args.password_env}')`，立即终止当前不可信路径。
        # - 为什么这样写：验收或合同不满足时必须失败保守，不能静默生成正式结果。
        raise RuntimeError(
            f"环境变量未设置：{args.password_env}"
        )

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

    adapter = DolphinDBDataSourceAdapter(
        DolphinDBConnectionSettings(
            host=args.host,
            port=args.port,
            username=args.username,
            password=password,
        ),
        source_id="dolphindb_primary",
    )
    bridge = DolphinDBProviderPluginBridge(
        adapter=adapter,
        config=config,
    )

    issues: list[str] = []
    warnings: list[str] = []

    bridge.open_session(config.authentication_reference)
    # 异常隔离：执行可能受文件、网络、数据库或外部环境影响的步骤。
    # - 处理：成功时继续主流程，失败时按原有异常分支记录或转换错误。
    # - 为什么这样写：保留真实失败原因，同时避免资源或中间状态失控。
    try:
        health = bridge.health_check()
        discovery = bridge.discover()
        warnings.extend(discovery.warnings)
        # 条件分支：检查 `discovery.errors` 后选择对应处理路径。
        # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
        # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
        if discovery.errors:
            issues.extend(discovery.errors)

        request = ProviderQueryRequest(
            request_id=(
                "task-020c-real-read:"
                + datetime.now(timezone.utc).isoformat()
            ),
            provider_id=config.provider_id,
            capability="EOD_MARKET_DATA",
            operation="READ_RAW_TABLE",
            usage="CURRENT_SNAPSHOT_RESEARCH",
            parameters={
                "database_uri": args.database_uri,
                "source_object_name": args.table_name,
            },
            maximum_rows=args.limit,
        )
        query_result = bridge.query_batch(request)
        # 条件分支：检查 `not query_result.records` 后选择对应处理路径。
        # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
        # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
        if not query_result.records:
            issues.append("REAL_READ_RETURNED_NO_RECORDS")

        local_target = matrix.provider("local_dolphindb")
        overlay_targets = tuple(
            replace(
                target,
                lifecycle=ProviderLifecycle.REAL_ACCEPTED,
                discovery_status=(
                    ProviderDiscoveryStatus.DISCOVERY_COMPLETE
                ),
            )
            if target.provider_id == "local_dolphindb"
            else target
            for target in matrix.provider_targets
        )
        matrix_overlay = ProviderCapabilityMatrix(
            task_id=matrix.task_id,
            matrix_version=matrix.matrix_version,
            matrix_status=matrix.matrix_status,
            provider_neutral=matrix.provider_neutral,
            automatic_activation_allowed=(
                matrix.automatic_activation_allowed
            ),
            secret_storage_allowed=matrix.secret_storage_allowed,
            core_system_may_import_vendor_sdk=(
                matrix.core_system_may_import_vendor_sdk
            ),
            upper_layers_may_depend_on_vendor_fields=(
                matrix.upper_layers_may_depend_on_vendor_fields
            ),
            required_adapter_contracts=(
                matrix.required_adapter_contracts
            ),
            capability_catalog=matrix.capability_catalog,
            provider_targets=overlay_targets,
            routing_rules=matrix.routing_rules,
        )

        overlay_entries = tuple(
            replace(
                entry,
                plugin_id=config.plugin_id,
                registration_status=PluginRegistrationStatus.AVAILABLE,
                entrypoint=config.entrypoint,
                enabled_for_routing=True,
                discovery_result_ref=discovery.discovery_id,
                authentication_reference_ref=(
                    config.authentication_reference.locator
                ),
                notes=(
                    "TASK_020C验收内存覆盖；"
                    "不修改真实注册表。"
                ),
            )
            if entry.provider_id == "local_dolphindb"
            else entry
            for entry in registry.entries
        )
        registry_overlay = ProviderPluginRegistry(
            task_id=registry.task_id,
            registry_version=registry.registry_version,
            registry_status=registry.registry_status,
            automatic_activation_allowed=(
                registry.automatic_activation_allowed
            ),
            entries=overlay_entries,
            hard_rules=registry.hard_rules,
        )
        candidates = build_provider_route_candidates(
            matrix=matrix_overlay,
            registry=registry_overlay,
            protocol=protocol,
            discovery_results={
                "local_dolphindb": discovery,
            },
            request=ProviderRouteRequest(
                capability="EOD_MARKET_DATA",
                usage="CURRENT_SNAPSHOT_RESEARCH",
            ),
        )
        local_candidates = [
            item
            for item in candidates
            if item.provider_id == "local_dolphindb"
        ]
        # 条件分支：检查 `len(local_candidates) != 1` 后选择对应处理路径。
        # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
        # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
        if len(local_candidates) != 1:
            issues.append("LOCAL_ROUTE_CANDIDATE_COUNT_INVALID")
            route_candidate = None
        else:
            route_candidate = local_candidates[0]
            warnings.extend(route_candidate.warnings)
            # 条件分支：检查 `route_candidate.decision is not RouteDecision.ELIGIBLE` 后选择对应处理路径。
            # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
            # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
            if route_candidate.decision is not RouteDecision.ELIGIBLE:
                issues.extend(route_candidate.reasons)

        report = {
            "task_id": "TASK_020C",
            "mode": "REAL_READONLY_DOLPHINDB_PLUGIN_BRIDGE_ACCEPTANCE",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "overall_status": (
                "PASSED_WITH_WARNINGS"
                if not issues
                else "FAILED"
            ),
            "provider_id": config.provider_id,
            "plugin_id": config.plugin_id,
            "bridge_version": config.bridge_version,
            "reuse_strategy": config.reuse_strategy,
            "legacy_adapter_class": config.legacy_adapter_class,
            "custom_query_engine_implemented": (
                config.custom_query_engine_implemented
            ),
            "custom_session_engine_implemented": (
                config.custom_session_engine_implemented
            ),
            "custom_dolphindb_protocol_implemented": (
                config.custom_dolphindb_protocol_implemented
            ),
            "runtime": object_to_dict(discovery.runtime),
            "discovery_outcome": discovery.outcome.value,
            "health_status": health.status.value,
            "health_latency_ms": health.latency_ms,
            "capabilities": {
                key: value.value
                for key, value in discovery.capabilities.items()
            },
            "query_operation": request.operation,
            "query_database_uri": args.database_uri,
            "query_table_name": args.table_name,
            "query_limit": args.limit,
            "query_result_count": len(query_result.records),
            "query_warnings": list(query_result.warnings),
            "route_decision": (
                route_candidate.decision.value
                if route_candidate is not None
                else None
            ),
            "route_score": (
                route_candidate.score
                if route_candidate is not None
                else 0.0
            ),
            "route_score_breakdown": (
                dict(route_candidate.score_breakdown)
                if route_candidate is not None
                else {}
            ),
            "route_reasons": (
                list(route_candidate.reasons)
                if route_candidate is not None
                else []
            ),
            "actual_registry_modified": False,
            "actual_capability_matrix_modified": False,
            "activation_recommended": (
                not issues
                and route_candidate is not None
                and route_candidate.decision
                is RouteDecision.ELIGIBLE
            ),
            "authentication_reference": (
                config.authentication_reference.locator
            ),
            "password_in_report": False,
            "database_connection_attempted": True,
            "database_readonly_query_mode": True,
            "database_write_operation_count": 0,
            "warnings": list(dict.fromkeys(warnings)),
            "issues": list(dict.fromkeys(issues)),
        }

        json_path = (
            output_dir
            / "task_020c_real_dolphindb_plugin_acceptance.json"
        )
        md_path = (
            output_dir
            / "task_020c_real_dolphindb_plugin_acceptance.md"
        )
        json_path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        md_path.write_text(_markdown(report), encoding="utf-8")

        print(
            json.dumps(
                {
                    "task_id": report["task_id"],
                    "overall_status": report["overall_status"],
                    "provider_id": report["provider_id"],
                    "discovery_outcome": report[
                        "discovery_outcome"
                    ],
                    "health_status": report["health_status"],
                    "query_result_count": report[
                        "query_result_count"
                    ],
                    "route_decision": report["route_decision"],
                    "route_score": report["route_score"],
                    "activation_recommended": report[
                        "activation_recommended"
                    ],
                    "actual_registry_modified": False,
                    "database_write_operation_count": 0,
                    "issues": report["issues"],
                    "json_report": str(json_path),
                    "markdown_report": str(md_path),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        # 输出结果：返回 `0 if not issues else 1` 给调用方。
        # - 为什么这样写：明确函数边界的最终状态，便于上层继续汇总或设置退出码。
        return 0 if not issues else 1
    finally:
        bridge.close_session()


# 脚本入口门禁：仅在本文件被直接运行时启动主流程。
# - 处理：作为模块导入时不自动执行，直接运行时调用main并传递退出状态。
# - 为什么这样写：区分可复用导入与命令行执行，避免测试或其他脚本导入时产生副作用。
if __name__ == "__main__":
    # 进程退出：使用 `SystemExit(main())` 把主流程状态返回给命令行调用方。
    # - 为什么这样写：明确成功或失败退出码，便于PowerShell、CI和人工验收判断运行结果。
    raise SystemExit(main())
