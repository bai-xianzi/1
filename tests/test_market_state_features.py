from __future__ import annotations

import json
import math
import tempfile
import unittest
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from types import SimpleNamespace

from a_stock_quant.data_contracts import (
    DataContractError,
    QualityStatus,
)
from a_stock_quant.market_state_features import (
    ExplainableMarketStateFeatureCalculator,
    MarketStateFeatureStatus,
    load_market_state_feature_spec,
)
from a_stock_quant.market_state_inputs import (
    MarketStateInputContractEngine,
    load_market_state_input_contract,
)
from a_stock_quant.standard_data_service import (
    StandardDataQuery,
    StandardDataRecord,
    StandardDataUsage,
    StandardQueryMetadata,
    StandardQueryResult,
)


ROOT = Path(__file__).resolve().parents[1]
INPUT_CONTRACT_PATH = (
    ROOT
    / "configs"
    / "market_state"
    / "market_state_input_contract_v0.json"
)
FEATURE_SPEC_PATH = (
    ROOT
    / "configs"
    / "market_state"
    / "market_state_feature_spec_v0.json"
)


@dataclass
class FakeGatedResult:
    standard_result: StandardQueryResult
    blocks: bool = False

    def __post_init__(self) -> None:
        self.readiness_snapshot = SimpleNamespace(
            decision=SimpleNamespace(
                status=SimpleNamespace(value="WARNING"),
                warnings=("READINESS_WARNING",),
            )
        )

    def assert_usable(self) -> None:
        if self.blocks:
            raise DataContractError("fake blocked")


def make_result(
    dataset_id: str,
    canonical_object: str,
    records: tuple[StandardDataRecord, ...],
    *,
    query_id: str,
    usage: StandardDataUsage = (
        StandardDataUsage.CURRENT_SNAPSHOT_RESEARCH
    ),
) -> FakeGatedResult:
    trade_dates = [
        record.values["trade_date"]
        for record in records
        if record.values.get("trade_date") is not None
    ]
    start = min(trade_dates)
    end = max(trade_dates)
    if dataset_id == "hy":
        query = StandardDataQuery(
            dataset_id=dataset_id,
            canonical_object=canonical_object,
            instrument_ids=(),
            entity_ids=("industry-a", "industry-b"),
            start_date=start,
            end_date=end,
            usage=usage,
        )
    else:
        query = StandardDataQuery(
            dataset_id=dataset_id,
            canonical_object=canonical_object,
            instrument_ids=("000001", "000002", "000003"),
            entity_ids=(),
            start_date=start,
            end_date=end,
            usage=usage,
        )
    metadata = StandardQueryMetadata(
        dataset_id=dataset_id,
        canonical_object=canonical_object,
        provider_id=f"{dataset_id}-provider",
        coverage_version="coverage-v1",
        mapping_version="mapping-v1",
        dictionary_revision="dictionary-v1",
        source_row_count=len(records),
        result_count=len(records),
        status=QualityStatus.WARNING,
        blocks_downstream=False,
        warnings=("SOURCE_WARNING",),
        query_id=query_id,
    )
    return FakeGatedResult(
        StandardQueryResult(
            query=query,
            metadata=metadata,
            records=records,
        )
    )


def daily_record(
    instrument_id: str,
    trade_date: date,
    pct_change: float,
    amount: float,
    turnover: float,
    high: float,
    low: float,
    close: float,
) -> StandardDataRecord:
    return StandardDataRecord(
        canonical_object="DailyBar",
        primary_key={
            "instrument_id": instrument_id,
            "trade_date": trade_date,
        },
        values={
            "instrument_id": instrument_id,
            "trade_date": trade_date,
            "pct_change_pct": pct_change,
            "amount_cny": amount,
            "turnover_rate_pct": turnover,
            "high_raw_cny": high,
            "low_raw_cny": low,
            "close_raw_cny": close,
        },
    )


def industry_record(
    node_id: str,
    trade_date: date,
    pct_change: float,
    up_count: int,
    down_count: int,
    limit_up_count: int,
    breadth_ratio: float,
    average_return: float,
) -> StandardDataRecord:
    return StandardDataRecord(
        canonical_object="ClassificationMarketSnapshot",
        primary_key={
            "node_id": node_id,
            "trade_date": trade_date,
        },
        values={
            "node_id": node_id,
            "trade_date": trade_date,
            "pct_change_pct": pct_change,
            "up_count": up_count,
            "down_count": down_count,
            "limit_up_count": limit_up_count,
            "breadth_ratio": breadth_ratio,
            "average_return_pct": average_return,
            "amount_cny": 100.0,
        },
    )


class TestMarketStateFeatures(unittest.TestCase):
    def setUp(self) -> None:
        contract = load_market_state_input_contract(
            INPUT_CONTRACT_PATH
        )
        spec = load_market_state_feature_spec(FEATURE_SPEC_PATH)
        self.spec = spec
        self.calculator = ExplainableMarketStateFeatureCalculator(
            MarketStateInputContractEngine(contract),
            spec,
        )
        self.trade_date = date(2025, 12, 31)

    def _results(self):
        daily = (
            daily_record(
                "000001",
                self.trade_date,
                -1.0,
                100.0,
                1.0,
                10.5,
                9.5,
                10.0,
            ),
            daily_record(
                "000002",
                self.trade_date,
                2.0,
                200.0,
                2.0,
                21.0,
                19.0,
                20.0,
            ),
            daily_record(
                "000003",
                self.trade_date,
                3.0,
                300.0,
                3.0,
                31.5,
                28.5,
                30.0,
            ),
        )
        industry = (
            industry_record(
                "industry-a",
                self.trade_date,
                1.0,
                60,
                40,
                3,
                1.5,
                0.8,
            ),
            industry_record(
                "industry-b",
                self.trade_date,
                -0.5,
                30,
                70,
                1,
                0.6,
                -0.2,
            ),
        )
        return {
            "a_stock_daily_k": make_result(
                "a_stock_daily_k",
                "DailyBar",
                daily,
                query_id="daily-q",
            ),
            "hy": make_result(
                "hy",
                "ClassificationMarketSnapshot",
                industry,
                query_id="hy-q",
            ),
        }

    def test_spec_loads(self):
        self.assertEqual(self.spec.task_id, "TASK_019B")
        self.assertEqual(self.spec.spec_version, "0.1.0")

    def test_spec_has_fifteen_features(self):
        self.assertEqual(len(self.spec.feature_definitions), 15)

    def test_snapshot_is_research_only(self):
        snapshot = self.calculator.calculate(self._results())
        self.assertFalse(snapshot.manual_decision_allowed)
        self.assertFalse(snapshot.official_market_state_allowed)
        self.assertIsNone(snapshot.regime_label)

    def test_latest_common_date_is_used(self):
        results = self._results()
        older = date(2025, 12, 30)
        existing = results[
            "a_stock_daily_k"
        ].standard_result.records
        results["a_stock_daily_k"] = make_result(
            "a_stock_daily_k",
            "DailyBar",
            existing + (
                daily_record(
                    "000001",
                    older,
                    0.1,
                    1.0,
                    1.0,
                    10,
                    9,
                    9.5,
                ),
            ),
            query_id="daily-q",
        )
        snapshot = self.calculator.calculate(results)
        self.assertEqual(snapshot.as_of_date, self.trade_date)

    def test_all_required_features_are_generated(self):
        snapshot = self.calculator.calculate(self._results())
        self.assertEqual(len(snapshot.features), 15)
        self.assertEqual(snapshot.missing_required_features, ())

    def test_warning_input_produces_ready_with_warnings(self):
        snapshot = self.calculator.calculate(self._results())
        self.assertEqual(
            snapshot.status,
            MarketStateFeatureStatus.READY_WITH_WARNINGS,
        )
        self.assertTrue(snapshot.research_feature_build_allowed)

    def test_daily_positive_ratio(self):
        value = self.calculator.calculate(
            self._results()
        ).feature("daily_positive_return_ratio").value
        self.assertAlmostEqual(value, 2 / 3)

    def test_daily_mean_and_median(self):
        snapshot = self.calculator.calculate(self._results())
        self.assertAlmostEqual(
            snapshot.feature("daily_mean_return_pct").value,
            4 / 3,
        )
        self.assertEqual(
            snapshot.feature("daily_median_return_pct").value,
            2.0,
        )

    def test_liquidity_features(self):
        snapshot = self.calculator.calculate(self._results())
        self.assertEqual(
            snapshot.feature("market_amount_total_cny").value,
            600.0,
        )
        self.assertEqual(
            snapshot.feature("turnover_rate_median_pct").value,
            2.0,
        )
        self.assertEqual(
            snapshot.feature("amount_field_coverage_ratio").value,
            1.0,
        )

    def test_volatility_features(self):
        snapshot = self.calculator.calculate(self._results())
        expected_std = math.sqrt(26 / 9)
        self.assertAlmostEqual(
            snapshot.feature(
                "cross_section_return_std_pct"
            ).value,
            expected_std,
        )
        self.assertAlmostEqual(
            snapshot.feature(
                "intraday_range_median_pct"
            ).value,
            10.0,
        )
        self.assertEqual(
            snapshot.feature(
                "absolute_return_median_pct"
            ).value,
            2.0,
        )

    def test_breadth_features(self):
        snapshot = self.calculator.calculate(self._results())
        self.assertEqual(
            snapshot.feature("industry_advance_ratio").value,
            0.45,
        )
        self.assertEqual(
            snapshot.feature(
                "industry_breadth_ratio_median"
            ).value,
            1.05,
        )
        self.assertAlmostEqual(
            snapshot.feature(
                "industry_limit_up_share_of_up"
            ).value,
            4 / 90,
        )

    def test_sector_diffusion_features(self):
        snapshot = self.calculator.calculate(self._results())
        self.assertEqual(
            snapshot.feature("positive_industry_ratio").value,
            0.5,
        )
        self.assertEqual(
            snapshot.feature("industry_return_std_pct").value,
            0.75,
        )
        self.assertEqual(
            snapshot.feature(
                "positive_average_return_ratio"
            ).value,
            0.5,
        )

    def test_feature_provenance_is_preserved(self):
        feature = self.calculator.calculate(
            self._results()
        ).feature("daily_mean_return_pct")
        self.assertEqual(
            feature.source_dataset_ids,
            ("a_stock_daily_k",),
        )
        self.assertEqual(feature.source_query_ids, ("daily-q",))
        self.assertEqual(feature.source_record_count, 3)

    def test_no_common_date_blocks(self):
        results = self._results()
        other_date = date(2025, 12, 29)
        results["hy"] = make_result(
            "hy",
            "ClassificationMarketSnapshot",
            (
                industry_record(
                    "industry-a",
                    other_date,
                    1,
                    1,
                    1,
                    0,
                    1,
                    1,
                ),
                industry_record(
                    "industry-b",
                    other_date,
                    -1,
                    1,
                    1,
                    0,
                    1,
                    -1,
                ),
            ),
            query_id="hy-q-2",
        )
        snapshot = self.calculator.calculate(results)
        self.assertEqual(
            snapshot.status,
            MarketStateFeatureStatus.BLOCKED,
        )
        self.assertIn(
            "LATEST_COMMON_TRADE_DATE",
            snapshot.missing_required_features,
        )

    def test_insufficient_daily_observations_blocks(self):
        results = self._results()
        records = results[
            "a_stock_daily_k"
        ].standard_result.records[:2]
        results["a_stock_daily_k"] = make_result(
            "a_stock_daily_k",
            "DailyBar",
            records,
            query_id="daily-short",
        )
        snapshot = self.calculator.calculate(results)
        self.assertEqual(
            snapshot.status,
            MarketStateFeatureStatus.BLOCKED,
        )
        self.assertIn(
            "daily_mean_return_pct",
            snapshot.missing_required_features,
        )

    def test_blocked_input_gate_blocks_features(self):
        results = self._results()
        results["hy"].blocks = True
        snapshot = self.calculator.calculate(results)
        self.assertEqual(
            snapshot.status,
            MarketStateFeatureStatus.BLOCKED,
        )
        self.assertEqual(snapshot.features, ())

    def test_wrong_usage_blocks_at_input_contract(self):
        results = self._results()
        results["hy"] = make_result(
            "hy",
            "ClassificationMarketSnapshot",
            results["hy"].standard_result.records,
            query_id="hy-manual",
            usage=StandardDataUsage.STRICT_HISTORICAL_BACKTEST,
        )
        snapshot = self.calculator.calculate(results)
        self.assertEqual(
            snapshot.status,
            MarketStateFeatureStatus.BLOCKED,
        )

    def test_to_dict_is_json_safe(self):
        payload = self.calculator.calculate(
            self._results()
        ).to_dict()
        encoded = json.dumps(payload, ensure_ascii=False)
        self.assertIn("2025-12-31", encoded)

    def test_assert_research_usable_rejects_blocked(self):
        snapshot = self.calculator.calculate({})
        with self.assertRaises(DataContractError):
            snapshot.assert_research_usable()

    def test_spec_rejects_regime_labels(self):
        raw = json.loads(
            FEATURE_SPEC_PATH.read_text(encoding="utf-8")
        )
        raw["regime_label_allowed"] = True
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "bad.json"
            path.write_text(
                json.dumps(raw, ensure_ascii=False),
                encoding="utf-8",
            )
            with self.assertRaises(DataContractError):
                load_market_state_feature_spec(path)


if __name__ == "__main__":
    unittest.main()
