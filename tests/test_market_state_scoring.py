# 测试模块总览：验证 `test_market_state_scoring` 对应功能的合同、边界和历史回归行为。
# - 输入：构造样例、测试夹具、临时文件以及被测模块公开接口。
# - 处理：只执行测试和断言，不修改生产算法、金融语义或正式数据库。
# - 输出：可重复的通过/失败证据，供全量回归和任务验收使用。
# - 为什么这样写：把业务要求固化为自动测试，使后续注释迁移和重构能够证明行为未变化。
from __future__ import annotations

import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from a_stock_quant.data_contracts import DataContractError
from a_stock_quant.market_state_scoring import (
    ExplainableResearchMarketStateScorer,
    ResearchMarketStateCandidate,
    ResearchMarketStateScoreStatus,
    ScoringFeatureRole,
    load_market_state_scoring_policy,
)


ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = (
    ROOT
    / "configs"
    / "market_state"
    / "market_state_scoring_policy_v0.json"
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


# 测试函数 `report`：封装 `report` 测试辅助步骤，减少重复样例和断言准备。
# - 输入：values、common_trade_date、as_of_date。
# - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
# - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
# - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
def report(
    values=None,
    *,
    common_trade_date="2025-12-31",
    as_of_date="2026-06-27",
):
    data = REAL_VALUES if values is None else values
    return {
        "task_id": "TASK_019C",
        "overall_status": "PASSED_WITH_WARNINGS",
        "as_of_date": as_of_date,
        "common_trade_date": common_trade_date,
        "research_feature_build_allowed": True,
        "manual_decision_allowed": False,
        "official_market_state_allowed": False,
        "regime_label": None,
        "issues": [],
        "warnings": ["SOURCE_WARNING"],
        "features": [
            {
                "feature_id": feature_id,
                "value": value,
            }
            for feature_id, value in data.items()
        ],
    }


# 测试类 `TestMarketStateScoring`：集中验证 `test_market_state_scoring` 相关合同、边界条件和回归行为。
# - 输入：测试夹具、构造样例以及被测模块公开接口。
# - 处理：按独立场景组织断言，覆盖正常路径、失败门禁和关键边界。
# - 输出：通过或失败的单元测试结果，不产生正式业务数据。
# - 为什么这样写：把同一职责的回归场景集中管理，便于定位失败并防止后续修改破坏既有合同。
class TestMarketStateScoring(unittest.TestCase):
    # 测试函数 `setUp`：准备本组测试共享的对象、样例和环境状态。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def setUp(self):
        self.policy = load_market_state_scoring_policy(POLICY_PATH)
        self.scorer = ExplainableResearchMarketStateScorer(
            self.policy
        )

    # 测试函数 `test_policy_loads`：验证 `policy、loads` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_policy_loads(self):
        self.assertEqual(self.policy.task_id, "TASK_019D")
        self.assertEqual(
            self.policy.policy_status,
            "RESEARCH_HYPOTHESIS_UNVALIDATED",
        )

    # 测试函数 `test_rule_role_counts`：验证 `rule、role、counts` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_rule_role_counts(self):
        roles = [rule.role for rule in self.policy.feature_rules]
        self.assertEqual(
            roles.count(ScoringFeatureRole.SCORE),
            12,
        )
        self.assertEqual(
            roles.count(ScoringFeatureRole.CONTEXT_ONLY),
            2,
        )
        self.assertEqual(
            roles.count(ScoringFeatureRole.QUALITY_GATE),
            1,
        )

    # 测试函数 `test_real_report_is_stale_indeterminate`：验证 `real、report、is、stale、indeterminate` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_real_report_is_stale_indeterminate(self):
        result = self.scorer.score(report())
        self.assertEqual(
            result.candidate_state,
            ResearchMarketStateCandidate
            .STALE_INPUT_INDETERMINATE,
        )
        self.assertTrue(result.stale_input)
        self.assertEqual(result.calendar_age_days, 178)

    # 测试函数 `test_real_report_has_five_dimensions`：验证 `real、report、has、five、dimensions` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_real_report_has_five_dimensions(self):
        result = self.scorer.score(report())
        self.assertEqual(len(result.dimension_scores), 5)

    # 测试函数 `test_real_report_scores_are_stable`：验证 `real、report、scores、are、stable` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_real_report_scores_are_stable(self):
        result = self.scorer.score(report())
        self.assertAlmostEqual(
            result.directional_score,
            42.015411202512865,
        )
        self.assertAlmostEqual(
            result.volatility_stress_score,
            37.65486361912881,
        )
        self.assertAlmostEqual(
            result.stability_score,
            62.34513638087119,
        )

    # 测试函数 `test_current_real_values_are_balanced_candidate`：验证 `current、real、values、are、balanced、candidate` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_current_real_values_are_balanced_candidate(self):
        result = self.scorer.score(
            report(
                common_trade_date="2025-12-31",
                as_of_date="2025-12-31",
            )
        )
        self.assertEqual(
            result.candidate_state,
            ResearchMarketStateCandidate.BALANCED_CANDIDATE,
        )

    # 测试函数 `test_bullish_candidate`：验证 `bullish、candidate` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_bullish_candidate(self):
        values = dict(REAL_VALUES)
        # 参数化循环：逐项使用 `('daily_positive_return_ratio', 'industry_advance_ratio', 'positive_industry_ratio', 'positive_average_r…` 验证同一合同。
        # - 处理：每轮保留原样例、顺序和断言，便于定位具体失败项。
        # - 为什么这样写：用一致规则覆盖多组输入，减少复制测试并提高边界覆盖率。
        for feature_id in (
            "daily_positive_return_ratio",
            "industry_advance_ratio",
            "positive_industry_ratio",
            "positive_average_return_ratio",
        ):
            values[feature_id] = 0.85
        values["daily_mean_return_pct"] = 2.0
        values["daily_median_return_pct"] = 1.5
        values["industry_breadth_ratio_median"] = 2.0
        values["industry_limit_up_share_of_up"] = 0.10
        values["turnover_rate_median_pct"] = 3.5
        result = self.scorer.score(
            report(
                values,
                common_trade_date="2025-12-31",
                as_of_date="2025-12-31",
            )
        )
        self.assertEqual(
            result.candidate_state,
            ResearchMarketStateCandidate.BULLISH_CANDIDATE,
        )

    # 测试函数 `test_bearish_candidate`：验证 `bearish、candidate` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_bearish_candidate(self):
        values = dict(REAL_VALUES)
        # 参数化循环：逐项使用 `('daily_positive_return_ratio', 'industry_advance_ratio', 'positive_industry_ratio', 'positive_average_r…` 验证同一合同。
        # - 处理：每轮保留原样例、顺序和断言，便于定位具体失败项。
        # - 为什么这样写：用一致规则覆盖多组输入，减少复制测试并提高边界覆盖率。
        for feature_id in (
            "daily_positive_return_ratio",
            "industry_advance_ratio",
            "positive_industry_ratio",
            "positive_average_return_ratio",
        ):
            values[feature_id] = 0.10
        values["daily_mean_return_pct"] = -2.0
        values["daily_median_return_pct"] = -1.5
        values["industry_breadth_ratio_median"] = 0.2
        values["industry_limit_up_share_of_up"] = 0.0
        values["turnover_rate_median_pct"] = 0.2
        result = self.scorer.score(
            report(
                values,
                common_trade_date="2025-12-31",
                as_of_date="2025-12-31",
            )
        )
        self.assertEqual(
            result.candidate_state,
            ResearchMarketStateCandidate.BEARISH_CANDIDATE,
        )

    # 测试函数 `test_volatile_transition_candidate`：验证 `volatile、transition、candidate` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_volatile_transition_candidate(self):
        values = dict(REAL_VALUES)
        values["daily_positive_return_ratio"] = 0.5
        values["daily_mean_return_pct"] = 0.0
        values["daily_median_return_pct"] = 0.0
        values["industry_advance_ratio"] = 0.5
        values["industry_breadth_ratio_median"] = 1.0
        values["industry_limit_up_share_of_up"] = 0.03
        values["turnover_rate_median_pct"] = 1.5
        values["positive_industry_ratio"] = 0.5
        values["positive_average_return_ratio"] = 0.5
        values["cross_section_return_std_pct"] = 4.0
        values["intraday_range_median_pct"] = 6.0
        values["absolute_return_median_pct"] = 4.0
        result = self.scorer.score(
            report(
                values,
                common_trade_date="2025-12-31",
                as_of_date="2025-12-31",
            )
        )
        self.assertEqual(
            result.candidate_state,
            ResearchMarketStateCandidate
            .VOLATILE_TRANSITION_CANDIDATE,
        )

    # 测试函数 `test_missing_feature_blocks`：验证 `missing、feature、blocks` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_missing_feature_blocks(self):
        data = report()
        data["features"] = data["features"][:-1]
        result = self.scorer.score(data)
        self.assertEqual(
            result.status,
            ResearchMarketStateScoreStatus.BLOCKED,
        )
        self.assertFalse(result.research_score_allowed)

    # 测试函数 `test_duplicate_feature_blocks`：验证 `duplicate、feature、blocks` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_duplicate_feature_blocks(self):
        data = report()
        data["features"].append(dict(data["features"][0]))
        result = self.scorer.score(data)
        self.assertTrue(result.blocks_downstream)

    # 测试函数 `test_amount_coverage_gate_blocks`：验证 `amount、coverage、gate、blocks` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_amount_coverage_gate_blocks(self):
        values = dict(REAL_VALUES)
        values["amount_field_coverage_ratio"] = 0.80
        result = self.scorer.score(report(values))
        self.assertTrue(result.blocks_downstream)
        self.assertIn(
            "QUALITY_GATE_FAILED:amount_field_coverage_ratio",
            result.blocking_reasons,
        )

    # 测试函数 `test_source_issues_block`：验证 `source、issues、block` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_source_issues_block(self):
        data = report()
        data["issues"] = ["bad"]
        self.assertTrue(self.scorer.score(data).blocks_downstream)

    # 测试函数 `test_source_official_state_permission_blocks`：验证 `source、official、state、permission、blocks` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_source_official_state_permission_blocks(self):
        data = report()
        data["official_market_state_allowed"] = True
        self.assertTrue(self.scorer.score(data).blocks_downstream)

    # 测试函数 `test_context_features_do_not_have_scores`：验证 `context、features、do、not、have、scores` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_context_features_do_not_have_scores(self):
        result = self.scorer.score(report())
        self.assertEqual(len(result.context_features), 2)
        self.assertTrue(
            all(
                item.normalised_score is None
                for item in result.context_features
            )
        )

    # 测试函数 `test_result_is_never_actionable`：验证 `result、is、never、actionable` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_result_is_never_actionable(self):
        result = self.scorer.score(report())
        self.assertFalse(result.candidate_state_actionable)
        self.assertFalse(result.manual_decision_allowed)
        self.assertFalse(result.official_market_state_allowed)
        self.assertFalse(result.trade_execution_allowed)
        self.assertIsNone(result.regime_label)

    # 测试函数 `test_to_dict_is_json_safe`：验证 `to、dict、is、json、safe` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_to_dict_is_json_safe(self):
        encoded = json.dumps(
            self.scorer.score(report()).to_dict(),
            ensure_ascii=False,
        )
        self.assertIn("STALE_INPUT_INDETERMINATE", encoded)

    # 测试函数 `test_assert_research_usable_rejects_blocked`：验证 `assert、research、usable、rejects、blocked` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_assert_research_usable_rejects_blocked(self):
        result = self.scorer.score({"task_id": "wrong"})
        # 测试上下文：通过 `self.assertRaises(DataContractError)` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
        with self.assertRaises(DataContractError):
            result.assert_research_usable()

    # 测试函数 `test_policy_rejects_official_activation`：验证 `policy、rejects、official、activation` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_policy_rejects_official_activation(self):
        raw = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
        raw["official_market_state_allowed"] = True
        # 测试上下文：通过 `tempfile.TemporaryDirectory()` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "bad.json"
            path.write_text(
                json.dumps(raw, ensure_ascii=False),
                encoding="utf-8",
            )
            # 测试上下文：通过 `self.assertRaises(DataContractError)` 管理异常断言、临时资源或子测试范围。
            # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
            # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
            with self.assertRaises(DataContractError):
                load_market_state_scoring_policy(path)


if __name__ == "__main__":
    unittest.main()
