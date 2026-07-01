# 测试模块总览：验证 `test_market_state_inputs` 对应功能的合同、边界和历史回归行为。
# - 输入：构造样例、测试夹具、临时文件以及被测模块公开接口。
# - 处理：只执行测试和断言，不修改生产算法、金融语义或正式数据库。
# - 输出：可重复的通过/失败证据，供全量回归和任务验收使用。
# - 为什么这样写：把业务要求固化为自动测试，使后续注释迁移和重构能够证明行为未变化。
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


# 测试类 `FakeGatedResult`：集中验证 `test_market_state_inputs` 相关合同、边界条件和回归行为。
# - 输入：测试夹具、构造样例以及被测模块公开接口。
# - 处理：按独立场景组织断言，覆盖正常路径、失败门禁和关键边界。
# - 输出：通过或失败的单元测试结果，不产生正式业务数据。
# - 为什么这样写：把同一职责的回归场景集中管理，便于定位失败并防止后续修改破坏既有合同。
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

    # 测试函数 `__post_init__`：封装 `__post_init__` 测试辅助步骤，减少重复样例和断言准备。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
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


# 测试类 `TestMarketStateInputs`：集中验证 `test_market_state_inputs` 相关合同、边界条件和回归行为。
# - 输入：测试夹具、构造样例以及被测模块公开接口。
# - 处理：按独立场景组织断言，覆盖正常路径、失败门禁和关键边界。
# - 输出：通过或失败的单元测试结果，不产生正式业务数据。
# - 为什么这样写：把同一职责的回归场景集中管理，便于定位失败并防止后续修改破坏既有合同。
class TestMarketStateInputs(unittest.TestCase):
    # 测试函数 `setUp`：准备本组测试共享的对象、样例和环境状态。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def setUp(self) -> None:
        self.contract = load_market_state_input_contract(CONTRACT_PATH)
        self.engine = MarketStateInputContractEngine(self.contract)

    # 测试函数 `_required_results`：封装 `_required_results` 测试辅助步骤，减少重复样例和断言准备。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
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

    # 测试函数 `test_contract_loads`：验证 `contract、loads` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_contract_loads(self):
        self.assertEqual(self.contract.contract_version, "0.1.0")
        self.assertEqual(self.contract.task_id, "TASK_019A")

    # 测试函数 `test_only_current_snapshot_research_is_allowed`：验证 `only、current、snapshot、research、is、allowed` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_only_current_snapshot_research_is_allowed(self):
        self.assertIs(
            self.contract.allowed_usage,
            StandardDataUsage.CURRENT_SNAPSHOT_RESEARCH,
        )

    # 测试函数 `test_all_nine_datasets_are_registered`：验证 `all、nine、datasets、are、registered` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_all_nine_datasets_are_registered(self):
        self.assertEqual(len(self.contract.dataset_requirements), 9)

    # 测试函数 `test_daily_k_and_industry_are_required`：验证 `daily、k、and、industry、are、required` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_daily_k_and_industry_are_required(self):
        required = {
            item.dataset_id
            for item in self.contract.dataset_requirements
            if item.required
        }
        self.assertEqual(required, {"a_stock_daily_k", "hy"})

    # 测试函数 `test_research_only_boundaries_are_closed`：验证 `research、only、boundaries、are、closed` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_research_only_boundaries_are_closed(self):
        self.assertFalse(self.contract.manual_decision_allowed)
        self.assertFalse(self.contract.official_market_state_allowed)

    # 测试函数 `test_required_results_are_ready_with_warnings`：验证 `required、results、are、ready、with、warnings` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_required_results_are_ready_with_warnings(self):
        result = self.engine.evaluate(self._required_results())
        self.assertEqual(
            result.status,
            MarketStateInputStatus.READY_WITH_WARNINGS,
        )
        self.assertTrue(result.research_feature_build_allowed)
        self.assertFalse(result.manual_decision_allowed)
        self.assertFalse(result.official_market_state_allowed)

    # 测试函数 `test_missing_daily_k_blocks`：验证 `missing、daily、k、blocks` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_missing_daily_k_blocks(self):
        results = self._required_results()
        del results["a_stock_daily_k"]
        result = self.engine.evaluate(results)
        self.assertEqual(result.status, MarketStateInputStatus.BLOCKED)
        self.assertIn(
            "a_stock_daily_k",
            result.missing_required_datasets,
        )

    # 测试函数 `test_blocked_required_dataset_blocks`：验证 `blocked、required、dataset、blocks` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_blocked_required_dataset_blocks(self):
        results = self._required_results()
        results["hy"].blocks = True
        result = self.engine.evaluate(results)
        self.assertEqual(result.status, MarketStateInputStatus.BLOCKED)
        self.assertIn("hy", result.blocked_datasets)

    # 测试函数 `test_wrong_usage_blocks`：验证 `wrong、usage、blocks` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_wrong_usage_blocks(self):
        results = self._required_results()
        results["a_stock_daily_k"].usage = (
            StandardDataUsage.MANUAL_DECISION_SUPPORT
        )
        results["a_stock_daily_k"].__post_init__()
        result = self.engine.evaluate(results)
        self.assertEqual(result.status, MarketStateInputStatus.BLOCKED)

    # 测试函数 `test_empty_required_result_blocks`：验证 `empty、required、result、blocks` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_empty_required_result_blocks(self):
        results = self._required_results()
        results["hy"].result_count = 0
        results["hy"].__post_init__()
        result = self.engine.evaluate(results)
        self.assertEqual(result.status, MarketStateInputStatus.BLOCKED)

    # 测试函数 `test_plain_standard_result_shape_is_rejected`：验证 `plain、standard、result、shape、is、rejected` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_plain_standard_result_shape_is_rejected(self):
        results = self._required_results()
        results["hy"] = SimpleNamespace()
        result = self.engine.evaluate(results)
        self.assertEqual(result.status, MarketStateInputStatus.BLOCKED)

    # 测试函数 `test_required_feature_families_are_covered`：验证 `required、feature、families、are、covered` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
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

    # 测试函数 `test_assert_research_usable_rejects_blocked`：验证 `assert、research、usable、rejects、blocked` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_assert_research_usable_rejects_blocked(self):
        result = self.engine.evaluate({})
        # 测试上下文：通过 `self.assertRaises(DataContractError)` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
        with self.assertRaises(DataContractError):
            result.assert_research_usable()

    # 测试函数 `test_hq_is_not_required_primary`：验证 `hq、is、not、required、primary` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_hq_is_not_required_primary(self):
        requirement = self.contract.requirement("hq")
        self.assertFalse(requirement.required)
        self.assertEqual(requirement.role.value, "SUPPLEMENTAL")

    # 测试函数 `test_config_rejects_official_market_state_activation`：验证 `config、rejects、official、market、state、activation` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_config_rejects_official_market_state_activation(self):
        raw = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
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
                load_market_state_input_contract(path)


if __name__ == "__main__":
    unittest.main()
