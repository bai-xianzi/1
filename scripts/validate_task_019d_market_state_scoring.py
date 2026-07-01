from __future__ import annotations

import argparse
import json
from pathlib import Path

from a_stock_quant.market_state_scoring import (
    ExplainableResearchMarketStateScorer,
    load_market_state_scoring_policy,
)


REAL_VALUES = {
    "daily_positive_return_ratio": 0.36666666666666664,
    "daily_mean_return_pct": 0.2704935333333333,
    "daily_median_return_pct": -0.1504085,
    "industry_advance_ratio": 0.44833782569631625,
    "industry_breadth_ratio_median": 0.72,
    "industry_limit_up_share_of_up": 0.018036072144288578,
    "market_amount_total_cny": 9604044032.0,
    "turnover_rate_median_pct": 1.264,
    "amount_field_coverage_ratio": 1.0,
    "cross_section_return_std_pct": 2.129311390850005,
    "intraday_range_median_pct": 2.0558627177735325,
    "absolute_return_median_pct": 0.749521,
    "positive_industry_ratio": 0.43333333333333335,
    "industry_return_std_pct": 0.6667367463166319,
    "positive_average_return_ratio": 0.9666666666666667,
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    args = parser.parse_args()
    root = Path(args.project_root).resolve()

    policy = load_market_state_scoring_policy(
        root
        / "configs"
        / "market_state"
        / "market_state_scoring_policy_v0.json"
    )
    scorer = ExplainableResearchMarketStateScorer(policy)
    report = {
        "task_id": "TASK_019C",
        "overall_status": "PASSED_WITH_WARNINGS",
        "as_of_date": "2026-06-27",
        "common_trade_date": "2025-12-31",
        "research_feature_build_allowed": True,
        "manual_decision_allowed": False,
        "official_market_state_allowed": False,
        "regime_label": None,
        "issues": [],
        "warnings": ["OFFLINE_REAL_REPORT_WARNING"],
        "features": [
            {"feature_id": key, "value": value}
            for key, value in REAL_VALUES.items()
        ],
    }
    snapshot = scorer.score(report)
    snapshot.assert_research_usable()

    require(len(policy.feature_rules) == 15, "规则数量异常")
    require(len(snapshot.dimension_scores) == 5, "维度数量异常")
    require(snapshot.calendar_age_days == 178, "日历滞后异常")
    require(snapshot.stale_input, "真实验收样本应标记为过期")
    require(
        snapshot.candidate_state.value
        == "STALE_INPUT_INDETERMINATE",
        "过期输入候选状态异常",
    )
    require(
        abs(snapshot.directional_score - 42.015411202512865)
        < 1e-9,
        "方向得分异常",
    )
    require(
        abs(
            snapshot.volatility_stress_score
            - 37.65486361912881
        )
        < 1e-9,
        "波动压力得分异常",
    )
    require(not snapshot.candidate_state_actionable, "候选状态不可执行")
    require(not snapshot.manual_decision_allowed, "不得启用人工决策")
    require(
        not snapshot.official_market_state_allowed,
        "不得启用正式状态",
    )
    require(
        not snapshot.trade_execution_allowed,
        "不得启用交易执行",
    )

    output = {
        "task_id": policy.task_id,
        "overall_status": "PASSED",
        "policy_version": policy.policy_version,
        "policy_status": policy.policy_status,
        "required_feature_count": policy.required_feature_count,
        "scored_feature_count": policy.scored_feature_count,
        "context_feature_count": policy.context_feature_count,
        "quality_gate_feature_count": (
            policy.quality_gate_feature_count
        ),
        "dimension_score_count": len(snapshot.dimension_scores),
        "directional_score": snapshot.directional_score,
        "volatility_stress_score": (
            snapshot.volatility_stress_score
        ),
        "stability_score": snapshot.stability_score,
        "calendar_age_days": snapshot.calendar_age_days,
        "stale_input": snapshot.stale_input,
        "candidate_state": snapshot.candidate_state.value,
        "candidate_state_actionable": (
            snapshot.candidate_state_actionable
        ),
        "manual_decision_allowed": (
            snapshot.manual_decision_allowed
        ),
        "official_market_state_allowed": (
            snapshot.official_market_state_allowed
        ),
        "trade_execution_allowed": (
            snapshot.trade_execution_allowed
        ),
        "database_connection_attempted": False,
        "write_operation_count": 0,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
