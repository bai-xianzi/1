from __future__ import annotations

import json
import tempfile
import unittest
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

from a_stock_quant.data_contracts import DataContractError
from a_stock_quant.market_state_inputs import (
    MarketStateFeatureFamily,
    MarketStateInputContractEngine,
    MarketStateInputStatus,
    load_market_state_input_contract,
)
from a_stock_quant.standard_data_service import StandardDataUsage


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = (
    ROOT
    / "configs"
    / "market_state"
    / "market_state_input_contract_v0.json"
)


@dataclass
class FakeGatedResult:
    dataset_id: str
    canonical_object: str
    provider_id: str
    query_id: str
    result_count: int = 1
    readiness_status: str = "WARNING"
    blocks: bool = False
    usage: StandardDataUsage = StandardDataUsage.CURRENT_SNAPSHOT_RESEARCH

    def __post_init__(self) -> None:
        self.standard_result = SimpleNamespace(
            query=SimpleNamespace(
                dataset_id=self.dataset_id,
                canonical_object=self.canonical_object,
                usage=self.usage,
            ),
            metadata=SimpleNamespace(
                provider_id=self.provider_id,
                query_id=self.query_id,
                result_count=self.result_count,
                warnings=("SOURCE_WARNING",),
            ),
        )
        self.readiness_snapshot = SimpleNamespace(
            decision=SimpleNamespace(
                status=SimpleNamespace(value=self.readiness_status),
                warnings=("SEMANTIC_CONFIDENCE:WARNING",),
            )
        )

    def assert_usable(self) -> None:
        if self.blocks:
            raise DataContractError("fake blocked")


class TestMarketStateInputs(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = load_market_state_input_contract(CONTRACT_PATH)
        self.engine = MarketStateInputContractEngine(self.contract)

    def _required_results(self):
        return {
            "a_stock_daily_k": FakeGatedResult(
                "a_stock_daily_k",
                "DailyBar",
                "daily",
                "q1",
            ),
            "hy": FakeGatedResult(
                "hy",
                "ClassificationMarketSnapshot",
                "hy",
                "q2",
            ),
        }

    def test_contract_loads(self):
        self.assertEqual(self.contract.contract_version, "0.1.0")
        self.assertEqual(self.contract.task_id, "TASK_019A")

    def test_only_current_snapshot_research_is_allowed(self):
        self.assertIs(
            self.contract.allowed_usage,
            StandardDataUsage.CURRENT_SNAPSHOT_RESEARCH,
        )

    def test_all_nine_datasets_are_registered(self):
        self.assertEqual(len(self.contract.dataset_requirements), 9)

    def test_daily_k_and_industry_are_required(self):
        required = {
            item.dataset_id
            for item in self.contract.dataset_requirements
            if item.required
        }
        self.assertEqual(required, {"a_stock_daily_k", "hy"})

    def test_research_only_boundaries_are_closed(self):
        self.assertFalse(self.contract.manual_decision_allowed)
        self.assertFalse(self.contract.official_market_state_allowed)

    def test_required_results_are_ready_with_warnings(self):
        result = self.engine.evaluate(self._required_results())
        self.assertEqual(
            result.status,
            MarketStateInputStatus.READY_WITH_WARNINGS,
        )
        self.assertTrue(result.research_feature_build_allowed)
        self.assertFalse(result.manual_decision_allowed)
        self.assertFalse(result.official_market_state_allowed)

    def test_missing_daily_k_blocks(self):
        results = self._required_results()
        del results["a_stock_daily_k"]
        result = self.engine.evaluate(results)
        self.assertEqual(result.status, MarketStateInputStatus.BLOCKED)
        self.assertIn(
            "a_stock_daily_k",
            result.missing_required_datasets,
        )

    def test_blocked_required_dataset_blocks(self):
        results = self._required_results()
        results["hy"].blocks = True
        result = self.engine.evaluate(results)
        self.assertEqual(result.status, MarketStateInputStatus.BLOCKED)
        self.assertIn("hy", result.blocked_datasets)

    def test_wrong_usage_blocks(self):
        results = self._required_results()
        results["a_stock_daily_k"].usage = (
            StandardDataUsage.MANUAL_DECISION_SUPPORT
        )
        results["a_stock_daily_k"].__post_init__()
        result = self.engine.evaluate(results)
        self.assertEqual(result.status, MarketStateInputStatus.BLOCKED)

    def test_empty_required_result_blocks(self):
        results = self._required_results()
        results["hy"].result_count = 0
        results["hy"].__post_init__()
        result = self.engine.evaluate(results)
        self.assertEqual(result.status, MarketStateInputStatus.BLOCKED)

    def test_plain_standard_result_shape_is_rejected(self):
        results = self._required_results()
        results["hy"] = SimpleNamespace()
        result = self.engine.evaluate(results)
        self.assertEqual(result.status, MarketStateInputStatus.BLOCKED)

    def test_required_feature_families_are_covered(self):
        result = self.engine.evaluate(self._required_results())
        self.assertEqual(result.missing_feature_families, ())
        expected = {
            MarketStateFeatureFamily.TREND,
            MarketStateFeatureFamily.BREADTH,
            MarketStateFeatureFamily.LIQUIDITY,
            MarketStateFeatureFamily.VOLATILITY,
            MarketStateFeatureFamily.SECTOR_DIFFUSION,
        }
        covered = {
            family
            for summary in result.dataset_summaries
            for family in summary.feature_families
        }
        self.assertTrue(expected.issubset(covered))

    def test_assert_research_usable_rejects_blocked(self):
        result = self.engine.evaluate({})
        with self.assertRaises(DataContractError):
            result.assert_research_usable()

    def test_hq_is_not_required_primary(self):
        requirement = self.contract.requirement("hq")
        self.assertFalse(requirement.required)
        self.assertEqual(requirement.role.value, "SUPPLEMENTAL")

    def test_config_rejects_official_market_state_activation(self):
        raw = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        raw["official_market_state_allowed"] = True
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "bad.json"
            path.write_text(
                json.dumps(raw, ensure_ascii=False),
                encoding="utf-8",
            )
            with self.assertRaises(DataContractError):
                load_market_state_input_contract(path)


if __name__ == "__main__":
    unittest.main()
