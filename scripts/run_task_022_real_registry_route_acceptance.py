# 本脚本核心功能：使用真实 Provider 配置完成 TASK_022 的只读验收，并把结果写入结构化报告。
# - 输入：项目根目录、DolphinDB 连接参数、目标数据库表和最多 5 行的读取上限。
# - 输出：JSON、Markdown 验收报告，以及用于 Git 闭环前判断的进程退出码。
# - 为什么这样写：正式激活必须证明真实配置可以完成健康检查、发现、读取和路由，不能继续依赖内存覆盖。
"""使用真实 Provider 配置执行 TASK_022 只读验收。"""
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

from a_stock_quant.dolphindb_adapter import DolphinDBConnectionSettings, DolphinDBDataSourceAdapter
from a_stock_quant.dolphindb_provider_plugin import DolphinDBProviderPluginBridge, load_dolphindb_provider_plugin_bridge_config
from a_stock_quant.provider_capabilities import load_provider_capability_matrix
from a_stock_quant.provider_plugin_protocol import (
    ProviderHealthStatus,
    ProviderQueryRequest,
    ProviderRouteRequest,
    RouteDecision,
    build_provider_route_candidates,
    load_provider_plugin_protocol_config,
    load_provider_plugin_registry,
    object_to_dict,
)

TASK_SECTION_START = "<!-- TASK_022_STATUS_START -->"
TASK_SECTION_END = "<!-- TASK_022_STATUS_END -->"


# 状态文件更新：只替换 TASK_022 的受控状态区块，不重写其他历史进度。
# - 输入：PROJECT_STATUS.md 路径、状态值和下一操作说明。
# - 输出：UTF-8、LF 换行的项目状态文件。
# - 为什么这样写：真实验收通过后应立刻留下权威状态，但必须避免破坏其他任务记录。
def update_task_status(path: Path, *, status: str, current_action: str) -> None:
    text = path.read_text(encoding="utf-8-sig")
    block = f"""{TASK_SECTION_START}

## TASK_022：DolphinDB Provider 正式激活与真实注册表路由回归

- 状态：`{status}`
- 当前操作：{current_action}
- 验收报告：`reports/task_022_real_dolphindb_provider_activation.json`
- 安全边界：只读；数据库写操作为 0；未启用交易能力。

{TASK_SECTION_END}"""
    if TASK_SECTION_START not in text or TASK_SECTION_END not in text:
        raise RuntimeError("PROJECT_STATUS.md 缺少 TASK_022 受控状态区块。")
    before = text.split(TASK_SECTION_START, 1)[0].rstrip()
    after = text.split(TASK_SECTION_END, 1)[1].lstrip()
    updated = before + "\n\n" + block + ("\n\n" + after if after else "\n")
    path.write_text(updated, encoding="utf-8", newline="\n")


# 主验收流程：加载真实配置，建立只读会话，完成健康、发现、查询和路由四层证明。
# - 参数 argv：可选命令行参数序列；为空时读取系统命令行。
# - 输出：通过返回 0，任何硬性验收条件失败返回 1。
# - 为什么这样写：统一退出码让 PowerShell 能在失败时立即阻断 Git 提交和推送。
def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--output-dir", default="reports")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8848)
    parser.add_argument("--username", default="admin")
    parser.add_argument("--password-env", default="DOLPHINDB_PASSWORD")
    parser.add_argument("--database-uri", default="dfs://A_STOCK_DAILY_K_DB")
    parser.add_argument("--table-name", default="stock_daily_k")
    parser.add_argument("--limit", type=int, default=5)
    args = parser.parse_args(argv)

    root = Path(args.project_root).resolve()
    output = root / args.output_dir
    output.mkdir(parents=True, exist_ok=True)
    password = os.environ.get(args.password_env)
    if not password:
        raise RuntimeError(f"环境变量未设置：{args.password_env}")
    if not 1 <= args.limit <= 5:
        raise RuntimeError("TASK_022 真实验收最多读取 5 行。")

    provider_config = load_dolphindb_provider_plugin_bridge_config(
        root / "configs/providers/dolphindb_provider_plugin_bridge_v0.json"
    )
    matrix = load_provider_capability_matrix(
        root / "configs/providers/provider_capability_matrix_v0.json"
    )
    registry = load_provider_plugin_registry(
        root / "configs/providers/provider_plugin_registry_v0.json"
    )
    protocol = load_provider_plugin_protocol_config(
        root / "configs/providers/provider_plugin_protocol_v0.json"
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
    bridge = DolphinDBProviderPluginBridge(adapter=adapter, config=provider_config)
    issues: list[str] = []
    bridge.open_session(provider_config.authentication_reference)
    try:
        health = bridge.health_check()
        if health.status is ProviderHealthStatus.UNAVAILABLE:
            issues.append("PROVIDER_HEALTH_UNAVAILABLE")

        discovery = bridge.discover()
        if discovery.outcome.value != "COMPLETE":
            issues.append("DISCOVERY_NOT_COMPLETE")
        if discovery.errors:
            issues.extend(discovery.errors)

        query = ProviderQueryRequest(
            request_id="task-022-real-read:" + datetime.now(timezone.utc).isoformat(),
            provider_id="local_dolphindb",
            capability="EOD_MARKET_DATA",
            operation="READ_RAW_TABLE",
            usage="CURRENT_SNAPSHOT_RESEARCH",
            parameters={
                "database_uri": args.database_uri,
                "source_object_name": args.table_name,
            },
            maximum_rows=args.limit,
        )
        result = bridge.query_batch(query)
        if not 1 <= len(result.records) <= args.limit:
            issues.append("REAL_READ_COUNT_OUT_OF_RANGE")

        candidates = build_provider_route_candidates(
            matrix=matrix,
            registry=registry,
            protocol=protocol,
            discovery_results={"local_dolphindb": discovery},
            request=ProviderRouteRequest(
                capability="EOD_MARKET_DATA",
                usage="CURRENT_SNAPSHOT_RESEARCH",
            ),
        )
        eligible_provider_ids = [
            item.provider_id
            for item in candidates
            if item.decision is RouteDecision.ELIGIBLE
        ]
        if eligible_provider_ids != ["local_dolphindb"]:
            issues.append(
                "ELIGIBLE_PROVIDER_SET_INVALID:" + ",".join(eligible_provider_ids)
            )
        local = [item for item in candidates if item.provider_id == "local_dolphindb"]
        if len(local) != 1:
            issues.append("LOCAL_ROUTE_CANDIDATE_COUNT_INVALID")
            candidate = None
        else:
            candidate = local[0]
            if candidate.decision is not RouteDecision.ELIGIBLE:
                issues.extend(candidate.reasons)
            if candidate.score <= 90.0:
                issues.append("ROUTE_SCORE_NOT_GREATER_THAN_90")

        warnings = sorted(
            set(discovery.warnings + (candidate.warnings if candidate else ()))
        )
        overall_status = (
            "FAILED"
            if issues
            else ("PASSED_WITH_WARNINGS" if warnings else "PASSED")
        )
        report = {
            "task_id": "TASK_022",
            "mode": "REAL_CONFIG_READONLY_ROUTE_REGRESSION",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "overall_status": overall_status,
            "provider_id": "local_dolphindb",
            "plugin_id": provider_config.plugin_id,
            "registry_status": registry.registry_status,
            "matrix_status": matrix.matrix_status,
            "health_status": health.status.value,
            "discovery_outcome": discovery.outcome.value,
            "query_result_count": len(result.records),
            "eligible_provider_ids": eligible_provider_ids,
            "route_decision": candidate.decision.value if candidate else None,
            "route_score": candidate.score if candidate else None,
            "warnings": warnings,
            "issues": sorted(set(issues)),
            "database_write_operations": 0,
            "registry_entry": object_to_dict(
                next(
                    item
                    for item in registry.entries
                    if item.provider_id == "local_dolphindb"
                )
            ),
        }
    finally:
        bridge.close_session()

    json_path = output / "task_022_real_dolphindb_provider_activation.json"
    md_path = output / "task_022_real_dolphindb_provider_activation.md"
    json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    md_path.write_text(
        "\n".join(
            [
                "# TASK_022 DolphinDB Provider 正式激活真实验收",
                "",
                f"- 状态：**{report['overall_status']}**",
                f"- 健康状态：`{report['health_status']}`",
                f"- 发现结果：`{report['discovery_outcome']}`",
                f"- 只读返回：{report['query_result_count']} 行",
                f"- 合格路由集合：`{report['eligible_provider_ids']}`",
                f"- 路由结果：`{report['route_decision']}`",
                f"- 路由得分：{report['route_score']}",
                "- 数据库写操作：0",
                "",
                "## 问题",
                *([f"- `{item}`" for item in report["issues"]] or ["- 无"]),
                "",
                "## 警告",
                *([f"- `{item}`" for item in report["warnings"]] or ["- 无"]),
                "",
            ]
        ),
        encoding="utf-8",
    )
    if not issues:
        update_task_status(
            root / "PROJECT_STATUS.md",
            status="REAL_ACCEPTED_PENDING_GIT_CLOSURE",
            current_action="运行完整审计并创建独立 Git 提交后推送到 GitHub main。",
        )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not issues else 1


# 脚本入口：把主流程退出码原样交给 PowerShell 验收脚本。
# - 输入：操作系统命令行参数。
# - 为什么这样写：保留非零退出码，确保真实验收失败时不会继续提交。
if __name__ == "__main__":
    raise SystemExit(main())
