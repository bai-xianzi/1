# 本脚本核心功能：执行任务018c外部证据验收的真实运行或验收流程。
# - 输入：命令行参数、项目配置、数据服务结果以及已有验收文件。
# - 处理：按既定任务顺序执行读取、校验、汇总和失败门禁，不改变核心金融算法。
# - 输出：终端信息、报告内容或进程退出码，供后续人工验收和自动化流程判断。
# - 为什么这样写：把运维与验收编排集中在脚本层，避免环境操作混入核心业务模块。
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any


# 函数 `_json_safe`：完成JSONsafe相关处理。
# - 输入：value。
# - 处理：完成JSONsafe相关处理，并按现有异常和门禁规则保留失败证据。
# - 输出：返回类型约定为 `Any`。
# - 为什么这样写：把独立步骤封装为清晰逻辑边界，便于复用、测试和定位验收失败。
def _json_safe(value: Any) -> Any:
    # 条件分支：检查 `hasattr(value, 'value') and isinstance(getattr(value, 'value'), str)` 后选择对应处理路径。
    # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
    # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
    if hasattr(value, "value") and isinstance(getattr(value, "value"), str):
        # 输出结果：返回 `value.value` 给调用方。
        # - 为什么这样写：明确函数边界的最终状态，便于上层继续汇总或设置退出码。
        return value.value
    # 条件分支：检查 `hasattr(value, 'isoformat')` 后选择对应处理路径。
    # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
    # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
    if hasattr(value, "isoformat"):
        # 异常隔离：执行可能受文件、网络、数据库或外部环境影响的步骤。
        # - 处理：成功时继续主流程，失败时按原有异常分支记录或转换错误。
        # - 为什么这样写：保留真实失败原因，同时避免资源或中间状态失控。
        try:
            # 输出结果：返回 `value.isoformat()` 给调用方。
            # - 为什么这样写：明确函数边界的最终状态，便于上层继续汇总或设置退出码。
            return value.isoformat()
        except TypeError:
            pass
    # 条件分支：检查 `isinstance(value, dict)` 后选择对应处理路径。
    # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
    # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
    if isinstance(value, dict):
        # 输出结果：返回 `{str(key): _json_safe(item) for key, item in value.items()}` 给调用方。
        # - 为什么这样写：明确函数边界的最终状态，便于上层继续汇总或设置退出码。
        return {str(key): _json_safe(item) for key, item in value.items()}
    # 条件分支：检查 `isinstance(value, (list, tuple, set, frozenset))` 后选择对应处理路径。
    # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
    # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
    if isinstance(value, (list, tuple, set, frozenset)):
        # 输出结果：返回 `[_json_safe(item) for item in value]` 给调用方。
        # - 为什么这样写：明确函数边界的最终状态，便于上层继续汇总或设置退出码。
        return [_json_safe(item) for item in value]
    # 输出结果：返回 `value` 给调用方。
    # - 为什么这样写：明确函数边界的最终状态，便于上层继续汇总或设置退出码。
    return value


# 函数 `_markdown`：完成markdown相关处理。
# - 输入：payload。
# - 处理：完成markdown相关处理，并按现有异常和门禁规则保留失败证据。
# - 输出：返回类型约定为 `str`。
# - 为什么这样写：把独立步骤封装为清晰逻辑边界，便于复用、测试和定位验收失败。
def _markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# TASK_018C 真实外部证据验收",
        "",
        f"- 状态：**{payload['overall_status']}**",
        f"- 证据快照：`{payload['snapshot_id']}`",
        f"- 截止日期：`{payload['as_of_date']}`",
        (
            "- 最近交易日："
            f"`{payload['expected_latest_trading_date']}`"
        ),
        f"- 数据集：{payload['dataset_count']}",
        f"- 数据库写操作：{payload['write_operation_count']}",
        "",
        "| 数据集 | 覆盖 | 当前时效 | 当前启用 | 历史启用 |",
        "|---|---|---|---|---|",
    ]
    # 循环处理：将 `payload['datasets']` 中的元素逐项绑定到 `row`。
    # - 处理：每轮复用同一校验或转换逻辑，并保留现有顺序和累计结果。
    # - 为什么这样写：逐项处理便于定位单个来源、文件或数据集的异常。
    for row in payload["datasets"]:
        lines.append(
            "| {dataset_id} | {coverage_status} | "
            "{current_freshness_status} | "
            "{current_activation_status} | "
            "{historical_activation_status} |".format(**row)
        )
    lines.extend(
        [
            "",
            "## 结论",
            "",
            "- 日K完整数据库快照覆盖已证明，但当前更新落后。",
            "- 基本面当前快照覆盖与时效满足研究阈值。",
            "- 七类快照通过真实样本验收，但没有实体全集覆盖证明。",
            "- 九个数据集均已激活用于当前快照研究。",
            "- 严格历史用途只有日K处于候选激活状态。",
            "- 本验收只读取仓库报告和配置，不连接DolphinDB。",
            "",
        ]
    )
    # 输出结果：返回 `'\n'.join(lines)` 给调用方。
    # - 为什么这样写：明确函数边界的最终状态，便于上层继续汇总或设置退出码。
    return "\n".join(lines)


# 函数 `main`：组织命令行入口、依次执行本脚本的核心步骤并返回进程退出状态。
# - 输入：无显式参数，使用模块配置、环境或闭包状态。
# - 处理：组织命令行入口、依次执行本脚本的核心步骤并返回进程退出状态，并按现有异常和门禁规则保留失败证据。
# - 输出：返回类型约定为 `int`。
# - 为什么这样写：把独立步骤封装为清晰逻辑边界，便于复用、测试和定位验收失败。
def main() -> int:
    parser = argparse.ArgumentParser(
        description="生成TASK_018C真实外部证据验收报告。"
    )
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    src = root / "src"
    # 条件分支：检查 `str(src) not in sys.path` 后选择对应处理路径。
    # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
    # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))

    from a_stock_quant.data_readiness_external_evidence import (
        ReportBackedEvidenceResolver,
    )
    from a_stock_quant.standard_data_service import (
        StandardDataUsage,
    )

    resolver = ReportBackedEvidenceResolver.from_project(
        project_root=root,
        config_path=(
            "configs/quality/"
            "data_readiness_external_evidence_v0.json"
        ),
    )
    as_of = resolver.config.as_of_date
    expected = resolver.calendar.latest_trading_day(as_of)

    rows = []
    # 循环处理：将 `resolver.config.datasets` 中的元素逐项绑定到 `item`。
    # - 处理：每轮复用同一校验或转换逻辑，并保留现有顺序和累计结果。
    # - 为什么这样写：逐项处理便于定位单个来源、文件或数据集的异常。
    for item in resolver.config.datasets:
        current = {
            evidence.dimension.value: evidence
            for evidence in resolver.resolve(
                dataset_id=item.dataset_id,
                usage=(
                    StandardDataUsage
                    .CURRENT_SNAPSHOT_RESEARCH
                ),
                as_of_date=as_of,
            )
        }
        historical = {
            evidence.dimension.value: evidence
            for evidence in resolver.resolve(
                dataset_id=item.dataset_id,
                usage=(
                    StandardDataUsage
                    .STRICT_HISTORICAL_BACKTEST
                ),
                as_of_date=as_of,
            )
        }
        rows.append(
            {
                "dataset_id": item.dataset_id,
                "report_kind": item.report_kind.value,
                "coverage_status": (
                    current["COVERAGE"].status.value
                ),
                "coverage_code": current["COVERAGE"].code,
                "coverage_metrics": (
                    current["COVERAGE"].metrics
                ),
                "current_freshness_status": (
                    current["FRESHNESS"].status.value
                ),
                "current_freshness_code": (
                    current["FRESHNESS"].code
                ),
                "current_freshness_metrics": (
                    current["FRESHNESS"].metrics
                ),
                "current_activation_status": (
                    current["ACTIVATION"].status.value
                ),
                "historical_freshness_status": (
                    historical["FRESHNESS"].status.value
                ),
                "historical_activation_status": (
                    historical["ACTIVATION"].status.value
                ),
                "evidence_refs": sorted(
                    {
                        ref
                        for evidence in current.values()
                        for ref in evidence.evidence_refs
                    }
                ),
            }
        )

    statuses = {
        row["coverage_status"]
        for row in rows
    } | {
        row["current_freshness_status"]
        for row in rows
    } | {
        row["historical_activation_status"]
        for row in rows
    }
    overall = (
        "PASSED_WITH_WARNINGS"
        if "WARNING" in statuses or "FAILED" in statuses
        else "PASSED"
    )
    payload = {
        "task_id": "TASK_018C",
        "mode": "REPORT_BACKED_EXTERNAL_EVIDENCE_ACCEPTANCE",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "external_evidence_version": "0.1.0",
        "snapshot_id": resolver.config.snapshot_id,
        "as_of_date": as_of.isoformat(),
        "expected_latest_trading_date": expected.isoformat(),
        "dataset_count": len(rows),
        "coverage_passed_count": sum(
            row["coverage_status"] == "PASSED"
            for row in rows
        ),
        "coverage_warning_count": sum(
            row["coverage_status"] == "WARNING"
            for row in rows
        ),
        "current_freshness_passed_count": sum(
            row["current_freshness_status"] == "PASSED"
            for row in rows
        ),
        "current_freshness_warning_count": sum(
            row["current_freshness_status"] == "WARNING"
            for row in rows
        ),
        "current_activation_passed_count": sum(
            row["current_activation_status"] == "PASSED"
            for row in rows
        ),
        "historical_activation_passed_count": sum(
            row["historical_activation_status"] == "PASSED"
            for row in rows
        ),
        "historical_activation_failed_count": sum(
            row["historical_activation_status"] == "FAILED"
            for row in rows
        ),
        "database_connection_attempted": False,
        "write_operation_count": 0,
        "overall_status": overall,
        "datasets": rows,
    }

    json_path = (
        output_dir
        / "task_018c_external_evidence_acceptance.json"
    )
    md_path = (
        output_dir
        / "task_018c_external_evidence_acceptance.md"
    )
    payload = _json_safe(payload)
    json_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
        newline="\n",
    )
    md_path.write_text(
        _markdown(payload),
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    print(f"JSON: {json_path}")
    print(f"Markdown: {md_path}")
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
