"""使用已提交TASK_019C真实特征报告生成TASK_019D研究评分验收包。"""
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
    return "\n".join(lines)


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
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.project_root).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    source_path = Path(args.source_report)
    if not source_path.is_absolute():
        source_path = root / source_path
    policy_path = Path(args.policy)
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
    for key, value in expected.items():
        if payload.get(key) != value:
            issues.append(key)
    if len(payload.get("dimension_scores", [])) != 5:
        issues.append("dimension_score_count")
    if len(payload.get("context_features", [])) != 2:
        issues.append("context_feature_count")
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
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
