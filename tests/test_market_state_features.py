# 测试模块总览：验证 `test_market_state_features` 对应功能的合同、边界和历史回归行为。
# - 输入：构造样例、测试夹具、临时文件以及被测模块公开接口。
# - 处理：只执行测试和断言，不修改生产算法、金融语义或正式数据库。
# - 输出：可重复的通过/失败证据，供全量回归和任务验收使用。
# - 为什么这样写：把业务要求固化为自动测试，使后续注释迁移和重构能够证明行为未变化。
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


# 测试类 `FakeGatedResult`：集中验证 `test_market_state_features` 相关合同、边界条件和回归行为。
# - 输入：测试夹具、构造样例以及被测模块公开接口。
# - 处理：按独立场景组织断言，覆盖正常路径、失败门禁和关键边界。
# - 输出：通过或失败的单元测试结果，不产生正式业务数据。
# - 为什么这样写：把同一职责的回归场景集中管理，便于定位失败并防止后续修改破坏既有合同。
@dataclass
class FakeGatedResult:
    standard_result: StandardQueryResult
    blocks: bool = False

    # 测试函数 `__post_init__`：封装 `__post_init__` 测试辅助步骤，减少重复样例和断言准备。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def __post_init__(self) -> None:
        self.readiness_snapshot = SimpleNamespace(
            decision=SimpleNamespace(
                status=SimpleNamespace(value="WARNING"),
                warnings=("READINESS_WARNING",),
            )
        )

    # 测试函数 `assert_usable`：封装 `assert_usable` 测试辅助步骤，减少重复样例和断言准备。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def assert_usable(self) -> None:
        # 测试分支：根据 `self.blocks` 选择对应断言或样例路径。
        # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
        # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
        if self.blocks:
            raise DataContractError("fake blocked")


# 测试函数 `make_result`：封装 `make_result` 测试辅助步骤，减少重复样例和断言准备。
# - 输入：dataset_id、canonical_object、records、query_id、usage。
# - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
# - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
# - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
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
    # 测试分支：根据 `dataset_id == 'hy'` 选择对应断言或样例路径。
    # - 处理：保持原条件和分支顺序，仅解释不同测试场景的进入条件。
    # - 为什么这样写：显式覆盖条件差异，防止只验证单一路径造成回归盲区。
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


# 测试函数 `daily_record`：封装 `daily_record` 测试辅助步骤，减少重复样例和断言准备。
# - 输入：instrument_id、trade_date、pct_change、amount、turnover、high、low、close。
# - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
# - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
# - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
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


# 测试函数 `industry_record`：封装 `industry_record` 测试辅助步骤，减少重复样例和断言准备。
# - 输入：node_id、trade_date、pct_change、up_count、down_count、limit_up_count、breadth_ratio、average_return。
# - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
# - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
# - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
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


# 测试类 `TestMarketStateFeatures`：集中验证 `test_market_state_features` 相关合同、边界条件和回归行为。
# - 输入：测试夹具、构造样例以及被测模块公开接口。
# - 处理：按独立场景组织断言，覆盖正常路径、失败门禁和关键边界。
# - 输出：通过或失败的单元测试结果，不产生正式业务数据。
# - 为什么这样写：把同一职责的回归场景集中管理，便于定位失败并防止后续修改破坏既有合同。
class TestMarketStateFeatures(unittest.TestCase):
    # 测试函数 `setUp`：准备本组测试共享的对象、样例和环境状态。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
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

    # 测试函数 `_results`：封装 `_results` 测试辅助步骤，减少重复样例和断言准备。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
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

    # 测试函数 `test_spec_loads`：验证 `spec、loads` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_spec_loads(self):
        self.assertEqual(self.spec.task_id, "TASK_019B")
        self.assertEqual(self.spec.spec_version, "0.1.0")

    # 测试函数 `test_spec_has_fifteen_features`：验证 `spec、has、fifteen、features` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_spec_has_fifteen_features(self):
        self.assertEqual(len(self.spec.feature_definitions), 15)

    # 测试函数 `test_snapshot_is_research_only`：验证 `snapshot、is、research、only` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_snapshot_is_research_only(self):
        snapshot = self.calculator.calculate(self._results())
        self.assertFalse(snapshot.manual_decision_allowed)
        self.assertFalse(snapshot.official_market_state_allowed)
        self.assertIsNone(snapshot.regime_label)

    # 测试函数 `test_latest_common_date_is_used`：验证 `latest、common、date、is、used` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
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

    # 测试函数 `test_all_required_features_are_generated`：验证 `all、required、features、are、generated` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_all_required_features_are_generated(self):
        snapshot = self.calculator.calculate(self._results())
        self.assertEqual(len(snapshot.features), 15)
        self.assertEqual(snapshot.missing_required_features, ())

    # 测试函数 `test_warning_input_produces_ready_with_warnings`：验证 `warning、input、produces、ready、with、warnings` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_warning_input_produces_ready_with_warnings(self):
        snapshot = self.calculator.calculate(self._results())
        self.assertEqual(
            snapshot.status,
            MarketStateFeatureStatus.READY_WITH_WARNINGS,
        )
        self.assertTrue(snapshot.research_feature_build_allowed)

    # 测试函数 `test_daily_positive_ratio`：验证 `daily、positive、ratio` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_daily_positive_ratio(self):
        value = self.calculator.calculate(
            self._results()
        ).feature("daily_positive_return_ratio").value
        self.assertAlmostEqual(value, 2 / 3)

    # 测试函数 `test_daily_mean_and_median`：验证 `daily、mean、and、median` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
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

    # 测试函数 `test_liquidity_features`：验证 `liquidity、features` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
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

    # 测试函数 `test_volatility_features`：验证 `volatility、features` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
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

    # 测试函数 `test_breadth_features`：验证 `breadth、features` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
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

    # 测试函数 `test_sector_diffusion_features`：验证 `sector、diffusion、features` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
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

    # 测试函数 `test_feature_provenance_is_preserved`：验证 `feature、provenance、is、preserved` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
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

    # 测试函数 `test_no_common_date_blocks`：验证 `no、common、date、blocks` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
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

    # 测试函数 `test_insufficient_daily_observations_blocks`：验证 `insufficient、daily、observations、blocks` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
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

    # 测试函数 `test_blocked_input_gate_blocks_features`：验证 `blocked、input、gate、blocks、features` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_blocked_input_gate_blocks_features(self):
        results = self._results()
        results["hy"].blocks = True
        snapshot = self.calculator.calculate(results)
        self.assertEqual(
            snapshot.status,
            MarketStateFeatureStatus.BLOCKED,
        )
        self.assertEqual(snapshot.features, ())

    # 测试函数 `test_wrong_usage_blocks_at_input_contract`：验证 `wrong、usage、blocks、at、input、contract` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
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

    # 测试函数 `test_to_dict_is_json_safe`：验证 `to、dict、is、json、safe` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_to_dict_is_json_safe(self):
        payload = self.calculator.calculate(
            self._results()
        ).to_dict()
        encoded = json.dumps(payload, ensure_ascii=False)
        self.assertIn("2025-12-31", encoded)

    # 测试函数 `test_assert_research_usable_rejects_blocked`：验证 `assert、research、usable、rejects、blocked` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_assert_research_usable_rejects_blocked(self):
        snapshot = self.calculator.calculate({})
        # 测试上下文：通过 `self.assertRaises(DataContractError)` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
        with self.assertRaises(DataContractError):
            snapshot.assert_research_usable()

    # 测试函数 `test_spec_rejects_regime_labels`：验证 `spec、rejects、regime、labels` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_spec_rejects_regime_labels(self):
        raw = json.loads(
            FEATURE_SPEC_PATH.read_text(encoding="utf-8")
        )
        raw["regime_label_allowed"] = True
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
                load_market_state_feature_spec(path)


if __name__ == "__main__":
    unittest.main()
