# 测试模块总览：验证 `test_data_readiness` 对应功能的合同、边界和历史回归行为。
# - 输入：构造样例、测试夹具、临时文件以及被测模块公开接口。
# - 处理：只执行测试和断言，不修改生产算法、金融语义或正式数据库。
# - 输出：可重复的通过/失败证据，供全量回归和任务验收使用。
# - 为什么这样写：把业务要求固化为自动测试，使后续注释迁移和重构能够证明行为未变化。
from __future__ import annotations

from datetime import date, datetime, timezone
import json
from pathlib import Path
import tempfile
import unittest

from a_stock_quant.data_contracts import DataContractError
from a_stock_quant.data_readiness import (
    DataReadinessEngine,
    DataReadinessRequest,
    EvidenceStatus,
    ReadinessDimension,
    ReadinessEvidence,
    ReadinessStatus,
    load_data_readiness_policy,
)
from a_stock_quant.standard_data_service import StandardDataUsage


PROJECT_ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = (
    PROJECT_ROOT
    / "configs"
    / "quality"
    / "data_readiness_policy_v0.json"
)


# 测试函数 `make_evidence`：封装 `make_evidence` 测试辅助步骤，减少重复样例和断言准备。
# - 输入：overrides。
# - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
# - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
# - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
def make_evidence(
    *,
    overrides: dict[
        ReadinessDimension,
        EvidenceStatus,
    ] | None = None,
) -> tuple[ReadinessEvidence, ...]:
    overrides = overrides or {}
    return tuple(
        ReadinessEvidence(
            dimension=dimension,
            status=overrides.get(
                dimension,
                EvidenceStatus.PASSED,
            ),
            code=(
                "CHECK_PASSED"
                if overrides.get(
                    dimension,
                    EvidenceStatus.PASSED,
                )
                is EvidenceStatus.PASSED
                else "CHECK_NOT_PASSED"
            ),
            message=f"{dimension.value} evidence",
            metrics={"count": 1},
            evidence_refs=(f"report:{dimension.value}",),
        )
        for dimension in ReadinessDimension
    )


# 测试类 `DataReadinessContractTests`：集中验证 `test_data_readiness` 相关合同、边界条件和回归行为。
# - 输入：测试夹具、构造样例以及被测模块公开接口。
# - 处理：按独立场景组织断言，覆盖正常路径、失败门禁和关键边界。
# - 输出：通过或失败的单元测试结果，不产生正式业务数据。
# - 为什么这样写：把同一职责的回归场景集中管理，便于定位失败并防止后续修改破坏既有合同。
class DataReadinessContractTests(unittest.TestCase):
    # 测试函数 `setUp`：准备本组测试共享的对象、样例和环境状态。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def setUp(self) -> None:
        self.policy = load_data_readiness_policy(
            POLICY_PATH
        )
        self.engine = DataReadinessEngine(self.policy)

    # 测试函数 `request`：封装 `request` 测试辅助步骤，减少重复样例和断言准备。
    # - 输入：usage、evidence。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def request(
        self,
        *,
        usage: StandardDataUsage = (
            StandardDataUsage.CURRENT_SNAPSHOT_RESEARCH
        ),
        evidence: tuple[ReadinessEvidence, ...] | None = None,
    ) -> DataReadinessRequest:
        return DataReadinessRequest(
            dataset_id="a_stock_daily_k",
            usage=usage,
            evidence=evidence or make_evidence(),
            as_of_date=date(2026, 6, 27),
            decision_time=(
                datetime(
                    2026,
                    6,
                    27,
                    15,
                    30,
                    tzinfo=timezone.utc,
                )
                if usage
                is StandardDataUsage.MANUAL_DECISION_SUPPORT
                else None
            ),
        )

    # 测试函数 `test_policy_loads_all_nine_datasets`：验证 `policy、loads、all、nine、datasets` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_policy_loads_all_nine_datasets(self) -> None:
        self.assertEqual(
            len(self.policy.dataset_catalog),
            9,
        )
        self.assertEqual(
            {
                item.dataset_id
                for item in self.policy.dataset_catalog
            },
            {
                "a_stock_daily_k",
                "a_stock_fundamental_snapshot",
                "hq",
                "hy",
                "gn",
                "kphq",
                "kphy",
                "kpgn",
                "zj",
            },
        )

    # 测试函数 `test_policy_covers_all_usages`：验证 `policy、covers、all、usages` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_policy_covers_all_usages(self) -> None:
        self.assertEqual(
            set(self.policy.usage_policies),
            set(StandardDataUsage),
        )

    # 测试函数 `test_all_passed_is_passed`：验证 `all、passed、is、passed` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_all_passed_is_passed(self) -> None:
        result = self.engine.evaluate(self.request())
        self.assertEqual(
            result.status,
            ReadinessStatus.PASSED,
        )
        self.assertFalse(result.blocks_downstream)
        result.assert_usable()

    # 测试函数 `test_current_research_freshness_warning_is_usable`：验证 `current、research、freshness、warning、is、usable` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_current_research_freshness_warning_is_usable(self) -> None:
        result = self.engine.evaluate(
            self.request(
                evidence=make_evidence(
                    overrides={
                        ReadinessDimension.FRESHNESS:
                        EvidenceStatus.WARNING,
                    }
                )
            )
        )
        self.assertEqual(
            result.status,
            ReadinessStatus.WARNING,
        )
        self.assertFalse(result.blocks_downstream)
        result.assert_usable()

    # 测试函数 `test_current_research_temporal_unknown_is_warning`：验证 `current、research、temporal、unknown、is、warning` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_current_research_temporal_unknown_is_warning(self) -> None:
        result = self.engine.evaluate(
            self.request(
                evidence=make_evidence(
                    overrides={
                        ReadinessDimension.TEMPORAL_SAFETY:
                        EvidenceStatus.UNKNOWN,
                    }
                )
            )
        )
        self.assertEqual(
            result.status,
            ReadinessStatus.WARNING,
        )
        self.assertFalse(result.blocks_downstream)

    # 测试函数 `test_missing_lineage_evidence_blocks`：验证 `missing、lineage、evidence、blocks` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_missing_lineage_evidence_blocks(self) -> None:
        evidence = tuple(
            item
            for item in make_evidence()
            if item.dimension
            is not ReadinessDimension.LINEAGE
        )
        result = self.engine.evaluate(
            self.request(evidence=evidence)
        )
        self.assertEqual(
            result.status,
            ReadinessStatus.BLOCKED,
        )
        self.assertTrue(result.blocks_downstream)
        self.assertIn(
            "LINEAGE:EVIDENCE_MISSING",
            result.blocking_reasons,
        )

    # 测试函数 `test_manual_temporal_warning_blocks`：验证 `manual、temporal、warning、blocks` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_manual_temporal_warning_blocks(self) -> None:
        result = self.engine.evaluate(
            self.request(
                usage=(
                    StandardDataUsage.MANUAL_DECISION_SUPPORT
                ),
                evidence=make_evidence(
                    overrides={
                        ReadinessDimension.TEMPORAL_SAFETY:
                        EvidenceStatus.WARNING,
                    }
                ),
            )
        )
        self.assertEqual(
            result.status,
            ReadinessStatus.BLOCKED,
        )

    # 测试函数 `test_manual_freshness_warning_blocks`：验证 `manual、freshness、warning、blocks` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_manual_freshness_warning_blocks(self) -> None:
        result = self.engine.evaluate(
            self.request(
                usage=(
                    StandardDataUsage.MANUAL_DECISION_SUPPORT
                ),
                evidence=make_evidence(
                    overrides={
                        ReadinessDimension.FRESHNESS:
                        EvidenceStatus.WARNING,
                    }
                ),
            )
        )
        self.assertEqual(
            result.status,
            ReadinessStatus.BLOCKED,
        )

    # 测试函数 `test_historical_temporal_warning_blocks`：验证 `historical、temporal、warning、blocks` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_historical_temporal_warning_blocks(self) -> None:
        result = self.engine.evaluate(
            self.request(
                usage=(
                    StandardDataUsage.STRICT_HISTORICAL_BACKTEST
                ),
                evidence=make_evidence(
                    overrides={
                        ReadinessDimension.TEMPORAL_SAFETY:
                        EvidenceStatus.WARNING,
                    }
                ),
            )
        )
        self.assertEqual(
            result.status,
            ReadinessStatus.BLOCKED,
        )

    # 测试函数 `test_historical_semantic_warning_blocks`：验证 `historical、semantic、warning、blocks` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_historical_semantic_warning_blocks(self) -> None:
        result = self.engine.evaluate(
            self.request(
                usage=(
                    StandardDataUsage.HISTORICAL_MODEL_TRAINING
                ),
                evidence=make_evidence(
                    overrides={
                        ReadinessDimension.SEMANTIC_CONFIDENCE:
                        EvidenceStatus.WARNING,
                    }
                ),
            )
        )
        self.assertEqual(
            result.status,
            ReadinessStatus.BLOCKED,
        )

    # 测试函数 `test_failed_query_blocks_all_usages`：验证 `failed、query、blocks、all、usages` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_failed_query_blocks_all_usages(self) -> None:
        # 参数化循环：逐项使用 `StandardDataUsage` 验证同一合同。
        # - 处理：每轮保留原样例、顺序和断言，便于定位具体失败项。
        # - 为什么这样写：用一致规则覆盖多组输入，减少复制测试并提高边界覆盖率。
        for usage in StandardDataUsage:
            # 测试上下文：通过 `self.subTest(usage=usage.value)` 管理异常断言、临时资源或子测试范围。
            # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
            # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
            with self.subTest(usage=usage.value):
                result = self.engine.evaluate(
                    self.request(
                        usage=usage,
                        evidence=make_evidence(
                            overrides={
                                ReadinessDimension.QUERY_EXECUTION:
                                EvidenceStatus.FAILED,
                            }
                        ),
                    )
                )
                self.assertEqual(
                    result.status,
                    ReadinessStatus.BLOCKED,
                )

    # 测试函数 `test_duplicate_dimension_is_rejected`：验证 `duplicate、dimension、is、rejected` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_duplicate_dimension_is_rejected(self) -> None:
        item = make_evidence()[0]
        # 测试上下文：通过 `self.assertRaises(DataContractError)` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
        with self.assertRaises(DataContractError):
            DataReadinessRequest(
                dataset_id="a_stock_daily_k",
                usage=(
                    StandardDataUsage.CURRENT_SNAPSHOT_RESEARCH
                ),
                evidence=(item, item),
            )

    # 测试函数 `test_manual_usage_requires_decision_time`：验证 `manual、usage、requires、decision、time` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_manual_usage_requires_decision_time(self) -> None:
        # 测试上下文：通过 `self.assertRaises(DataContractError)` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
        with self.assertRaises(DataContractError):
            DataReadinessRequest(
                dataset_id="a_stock_daily_k",
                usage=(
                    StandardDataUsage.MANUAL_DECISION_SUPPORT
                ),
                evidence=make_evidence(),
            )

    # 测试函数 `test_unknown_dataset_is_rejected`：验证 `unknown、dataset、is、rejected` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_unknown_dataset_is_rejected(self) -> None:
        request = DataReadinessRequest(
            dataset_id="unknown_dataset",
            usage=(
                StandardDataUsage.CURRENT_SNAPSHOT_RESEARCH
            ),
            evidence=make_evidence(),
        )
        # 测试上下文：通过 `self.assertRaises(DataContractError)` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
        with self.assertRaises(DataContractError):
            self.engine.evaluate(request)

    # 测试函数 `test_blocked_assert_usable_raises`：验证 `blocked、assert、usable、raises` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_blocked_assert_usable_raises(self) -> None:
        result = self.engine.evaluate(
            self.request(
                evidence=make_evidence(
                    overrides={
                        ReadinessDimension.COVERAGE:
                        EvidenceStatus.FAILED,
                    }
                )
            )
        )
        # 测试上下文：通过 `self.assertRaises(DataContractError)` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
        with self.assertRaises(DataContractError):
            result.assert_usable()

    # 测试函数 `test_to_dict_is_json_serialisable`：验证 `to、dict、is、json、serialisable` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_to_dict_is_json_serialisable(self) -> None:
        result = self.engine.evaluate(self.request())
        serialised = result.to_dict()
        json.dumps(serialised, ensure_ascii=False)
        self.assertEqual(
            serialised["usage"],
            "CURRENT_SNAPSHOT_RESEARCH",
        )
        self.assertEqual(
            serialised["status"],
            "PASSED",
        )
        self.assertEqual(
            serialised["as_of_date"],
            "2026-06-27",
        )

    # 测试函数 `test_policy_rejects_incomplete_dimension_list`：验证 `policy、rejects、incomplete、dimension、list` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_policy_rejects_incomplete_dimension_list(self) -> None:
        raw = json.loads(
            POLICY_PATH.read_text(encoding="utf-8")
        )
        raw["dimensions"] = raw["dimensions"][:-1]
        # 测试上下文：通过 `tempfile.TemporaryDirectory()` 管理异常断言、临时资源或子测试范围。
        # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
        # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "invalid.json"
            path.write_text(
                json.dumps(raw, ensure_ascii=False),
                encoding="utf-8",
            )
            # 测试上下文：通过 `self.assertRaises(DataContractError)` 管理异常断言、临时资源或子测试范围。
            # - 处理：上下文结束时自动完成异常匹配、资源释放或子场景归档。
            # - 为什么这样写：确保失败也能执行清理，并让异常类型和发生边界可被精确验证。
            with self.assertRaises(DataContractError):
                load_data_readiness_policy(path)


if __name__ == "__main__":
    unittest.main()
