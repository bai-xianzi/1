"""使用已提交TASK_019C真实特征报告生成TASK_019D研究评分验收包。"""
# 本脚本核心功能：执行任务019dresearch市场状态评分验收的真实运行或验收流程。
# - 输入：命令行参数、项目配置、数据服务结果以及已有验收文件。
# - 处理：按既定任务顺序执行读取、校验、汇总和失败门禁，不改变核心金融算法。
# - 输出：终端信息、报告内容或进程退出码，供后续人工验收和自动化流程判断。
# - 为什么这样写：把运维与验收编排集中在脚本层，避免环境操作混入核心业务模块。
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from a_stock_quant.market_state_scoring import (
    ExplainableResearchMarketStateScorer,
    load_market_state_scoring_policy,
)


# 函数 `_markdown`：完成markdown相关处理。
# - 输入：report。
# - 处理：完成markdown相关处理，并按现有异常和门禁规则保留失败证据。
# - 输出：返回类型约定为 `str`。
# - 为什么这样写：把独立步骤封装为清晰逻辑边界，便于复用、测试和定位验收失败。
def _markdown(report: Mapping[str, Any]) -> str:
    lines = [
        "# TASK_019D 研究级市场状态评分验收",
        "",
        f"- 状态：**{report['overall_status']}**",
        f"- 评分政策：`{report['policy_status']}`",
        f"- 来源共同交易日：{report['source_common_trade_date']}",
        f"- 来源证据截止日：{report['source_as_of_date']}",
        f"- 日历滞后：{report['calendar_age_days']}天",
        f"- 候选状态：`{report['candidate_state']}`",
        f"- 候选状态可执行：{report['candidate_state_actionable']}",
        "",
        "## 分项得分",
        "",
        "| 维度 | 得分 | 特征数 |",
        "|---|---:|---:|",
    ]
    # 循环处理：将 `report['dimension_scores']` 中的元素逐项绑定到 `item`。
    # - 处理：每轮复用同一校验或转换逻辑，并保留现有顺序和累计结果。
    # - 为什么这样写：逐项处理便于定位单个来源、文件或数据集的异常。
    for item in report["dimension_scores"]:
        lines.append(
            f"| {item['family']} | {item['score']:.4f} | "
            f"{item['feature_count']} |"
        )
    lines.extend(
        [
            "",
            "## 综合研究分",
            "",
            f"- 方向得分：{report['directional_score']:.4f}",
            f"- 波动压力：{report['volatility_stress_score']:.4f}",
            f"- 稳定度：{report['stability_score']:.4f}",
            "",
            "## 解释边界",
            "",
            "- 所有阈值与锚点均为尚未经过历史校准的研究假设。",
            "- 来源数据已经过期，因此候选状态被强制设为"
            "`STALE_INPUT_INDETERMINATE`。",
            "- 本报告不是当前市场判断。",
            "- 不允许用于人工决策、仓位、选股或交易执行。",
            "",
        ]
    )
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
    parser.add_argument(
        "--source-report",
        default=(
            "reports/"
            "task_019c_real_market_state_feature_acceptance.json"
        ),
    )
    parser.add_argument(
        "--policy",
        default=(
            "configs/market_state/"
            "market_state_scoring_policy_v0.json"
        ),
    )
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

    source_path = Path(args.source_report)
    # 条件分支：检查 `not source_path.is_absolute()` 后选择对应处理路径。
    # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
    # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
    if not source_path.is_absolute():
        source_path = root / source_path
    policy_path = Path(args.policy)
    # 条件分支：检查 `not policy_path.is_absolute()` 后选择对应处理路径。
    # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
    # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
    if not policy_path.is_absolute():
        policy_path = root / policy_path

    source = json.loads(source_path.read_text(encoding="utf-8"))
    policy = load_market_state_scoring_policy(policy_path)
    snapshot = ExplainableResearchMarketStateScorer(
        policy
    ).score(source)
    snapshot.assert_research_usable()
    payload = snapshot.to_dict()

    issues: list[str] = []
    expected = {
        "status": "READY_WITH_WARNINGS",
        "policy_status": "RESEARCH_HYPOTHESIS_UNVALIDATED",
        "source_task_id": "TASK_019C",
        "calendar_age_days": 178,
        "stale_input": True,
        "candidate_state": "STALE_INPUT_INDETERMINATE",
        "research_score_allowed": True,
        "candidate_state_actionable": False,
        "manual_decision_allowed": False,
        "official_market_state_allowed": False,
        "trade_execution_allowed": False,
        "regime_label": None,
    }
    # 循环处理：将 `expected.items()` 中的元素逐项绑定到 `(key, value)`。
    # - 处理：每轮复用同一校验或转换逻辑，并保留现有顺序和累计结果。
    # - 为什么这样写：逐项处理便于定位单个来源、文件或数据集的异常。
    for key, value in expected.items():
        # 条件分支：检查 `payload.get(key) != value` 后选择对应处理路径。
        # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
        # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
        if payload.get(key) != value:
            issues.append(key)
    # 条件分支：检查 `len(payload.get('dimension_scores', [])) != 5` 后选择对应处理路径。
    # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
    # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
    if len(payload.get("dimension_scores", [])) != 5:
        issues.append("dimension_score_count")
    # 条件分支：检查 `len(payload.get('context_features', [])) != 2` 后选择对应处理路径。
    # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
    # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
    if len(payload.get("context_features", [])) != 2:
        issues.append("context_feature_count")
    # 条件分支：检查 `len(payload.get('quality_gate_features', [])) != 1` 后选择对应处理路径。
    # - 处理：条件成立时执行当前分支，否则继续后续分支或保持默认流程。
    # - 为什么这样写：显式门禁可阻止不满足前置条件的数据或状态继续向下传播。
    if len(payload.get("quality_gate_features", [])) != 1:
        issues.append("quality_gate_feature_count")

    report = {
        "task_id": "TASK_019D",
        "mode": "REAL_FEATURE_REPORT_RESEARCH_SCORING_ACCEPTANCE",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "overall_status": (
            "PASSED_WITH_WARNINGS" if not issues else "FAILED"
        ),
        "source_report": str(source_path),
        "source_report_task_id": source.get("task_id"),
        "source_report_status": source.get("overall_status"),
        **payload,
        "database_connection_attempted": False,
        "write_operation_count": 0,
        "issues": issues,
    }

    json_path = (
        output_dir
        / "task_019d_research_market_state_scoring_acceptance.json"
    )
    md_path = (
        output_dir
        / "task_019d_research_market_state_scoring_acceptance.md"
    )
    json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    md_path.write_text(_markdown(report), encoding="utf-8")

    print(json.dumps({
        "task_id": report["task_id"],
        "overall_status": report["overall_status"],
        "candidate_state": report["candidate_state"],
        "directional_score": report["directional_score"],
        "volatility_stress_score": (
            report["volatility_stress_score"]
        ),
        "stability_score": report["stability_score"],
        "calendar_age_days": report["calendar_age_days"],
        "dimension_score_count": len(
            report["dimension_scores"]
        ),
        "candidate_state_actionable": (
            report["candidate_state_actionable"]
        ),
        "database_connection_attempted": False,
        "write_operation_count": 0,
        "issues": report["issues"],
        "json_report": str(json_path),
        "markdown_report": str(md_path),
    }, ensure_ascii=False, indent=2))
    # 输出结果：返回 `0 if not issues else 1` 给调用方。
    # - 为什么这样写：明确函数边界的最终状态，便于上层继续汇总或设置退出码。
    return 0 if not issues else 1


# 脚本入口门禁：仅在本文件被直接运行时启动主流程。
# - 处理：作为模块导入时不自动执行，直接运行时调用main并传递退出状态。
# - 为什么这样写：区分可复用导入与命令行执行，避免测试或其他脚本导入时产生副作用。
if __name__ == "__main__":
    # 进程退出：使用 `SystemExit(main())` 把主流程状态返回给命令行调用方。
    # - 为什么这样写：明确成功或失败退出码，便于PowerShell、CI和人工验收判断运行结果。
    raise SystemExit(main())
