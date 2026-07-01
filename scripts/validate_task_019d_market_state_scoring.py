# 本脚本核心功能：验证任务019d市场状态评分的合同、配置和结果。
# - 输入：命令行参数、项目配置、数据服务结果以及已有验收文件。
# - 处理：按既定任务顺序执行读取、校验、汇总和失败门禁，不改变核心金融算法。
# - 输出：终端信息、报告内容或进程退出码，供后续人工验收和自动化流程判断。
# - 为什么这样写：把运维与验收编排集中在脚本层，避免环境操作混入核心业务模块。
from __future__ import annotations

import argparse
import json
from pathlib import Path

from a_stock_quant.market_state_scoring import (
    ExplainableResearchMarketStateScorer,
    load_market_state_scoring_policy,
)


# 配置常量：集中定义 `REAL_VALUES`，供后续流程复用。
# - 当前值或构造表达式：`{'daily_positive_return_ratio': 0.36666666666666664, 'daily_mean_return_pct': 0.2704935...`。
# - 为什么这样写：把固定规则集中在模块顶部，便于审计来源并避免多处硬编码产生偏差。
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
