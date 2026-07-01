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


class TestMarketStateScoring(unittest.TestCase):
    def setUp(self):
        self.policy = load_market_state_scoring_policy(POLICY_PATH)
        self.scorer = ExplainableResearchMarketStateScorer(
            self.policy
        )

    def test_policy_loads(self):
        self.assertEqual(self.policy.task_id, "TASK_019D")
        self.assertEqual(
            self.policy.policy_status,
            "RESEARCH_HYPOTHESIS_UNVALIDATED",
        )

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

    def test_real_report_is_stale_indeterminate(self):
        result = self.scorer.score(report())
        self.assertEqual(
            result.candidate_state,
            ResearchMarketStateCandidate
            .STALE_INPUT_INDETERMINATE,
        )
        self.assertTrue(result.stale_input)
        self.assertEqual(result.calendar_age_days, 178)

    def test_real_report_has_five_dimensions(self):
        result = self.scorer.score(report())
        self.assertEqual(len(result.dimension_scores), 5)

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

    def test_bullish_candidate(self):
        values = dict(REAL_VALUES)
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

    def test_bearish_candidate(self):
        values = dict(REAL_VALUES)
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

    def test_missing_feature_blocks(self):
        data = report()
        data["features"] = data["features"][:-1]
        result = self.scorer.score(data)
        self.assertEqual(
            result.status,
            ResearchMarketStateScoreStatus.BLOCKED,
        )
        self.assertFalse(result.research_score_allowed)

    def test_duplicate_feature_blocks(self):
        data = report()
        data["features"].append(dict(data["features"][0]))
        result = self.scorer.score(data)
        self.assertTrue(result.blocks_downstream)

    def test_amount_coverage_gate_blocks(self):
        values = dict(REAL_VALUES)
        values["amount_field_coverage_ratio"] = 0.80
        result = self.scorer.score(report(values))
        self.assertTrue(result.blocks_downstream)
        self.assertIn(
            "QUALITY_GATE_FAILED:amount_field_coverage_ratio",
            result.blocking_reasons,
        )

    def test_source_issues_block(self):
        data = report()
        data["issues"] = ["bad"]
        self.assertTrue(self.scorer.score(data).blocks_downstream)

    def test_source_official_state_permission_blocks(self):
        data = report()
        data["official_market_state_allowed"] = True
        self.assertTrue(self.scorer.score(data).blocks_downstream)

    def test_context_features_do_not_have_scores(self):
        result = self.scorer.score(report())
        self.assertEqual(len(result.context_features), 2)
        self.assertTrue(
            all(
                item.normalised_score is None
                for item in result.context_features
            )
        )

    def test_result_is_never_actionable(self):
        result = self.scorer.score(report())
        self.assertFalse(result.candidate_state_actionable)
        self.assertFalse(result.manual_decision_allowed)
        self.assertFalse(result.official_market_state_allowed)
        self.assertFalse(result.trade_execution_allowed)
        self.assertIsNone(result.regime_label)

    def test_to_dict_is_json_safe(self):
        encoded = json.dumps(
            self.scorer.score(report()).to_dict(),
            ensure_ascii=False,
        )
        self.assertIn("STALE_INPUT_INDETERMINATE", encoded)

    def test_assert_research_usable_rejects_blocked(self):
        result = self.scorer.score({"task_id": "wrong"})
        with self.assertRaises(DataContractError):
            result.assert_research_usable()

    def test_policy_rejects_official_activation(self):
        raw = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
        raw["official_market_state_allowed"] = True
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "bad.json"
            path.write_text(
                json.dumps(raw, ensure_ascii=False),
                encoding="utf-8",
            )
            with self.assertRaises(DataContractError):
                load_market_state_scoring_policy(path)


if __name__ == "__main__":
    unittest.main()
