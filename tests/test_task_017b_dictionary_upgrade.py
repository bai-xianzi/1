# 测试模块总览：验证 `test_task_017b_dictionary_upgrade` 对应功能的合同、边界和历史回归行为。
# - 输入：构造样例、测试夹具、临时文件以及被测模块公开接口。
# - 处理：只执行测试和断言，不修改生产算法、金融语义或正式数据库。
# - 输出：可重复的通过/失败证据，供全量回归和任务验收使用。
# - 为什么这样写：把业务要求固化为自动测试，使后续注释迁移和重构能够证明行为未变化。
from __future__ import annotations

import unittest
from collections import Counter
from pathlib import Path

import yaml

from a_stock_quant.daily_funds_canonical_contract import validate_contract
from a_stock_quant.field_dictionary_governance import (
    field_index,
    load_yaml,
    validate_dictionary_governance,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


# 测试类 `Task017BDictionaryUpgradeTests`：集中验证 `test_task_017b_dictionary_upgrade` 相关合同、边界条件和回归行为。
# - 输入：测试夹具、构造样例以及被测模块公开接口。
# - 处理：按独立场景组织断言，覆盖正常路径、失败门禁和关键边界。
# - 输出：通过或失败的单元测试结果，不产生正式业务数据。
# - 为什么这样写：把同一职责的回归场景集中管理，便于定位失败并防止后续修改破坏既有合同。
class Task017BDictionaryUpgradeTests(unittest.TestCase):
    # 测试函数 `setUp`：准备本组测试共享的对象、样例和环境状态。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def setUp(self) -> None:
        self.canonical = load_yaml(
            PROJECT_ROOT / "schemas" / "canonical_fields.yaml"
        )
        self.index = field_index(self.canonical)

    # 测试函数 `test_revision_and_counts`：验证 `revision、and、counts` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_revision_and_counts(self) -> None:
        lifecycle = Counter(
            field["lifecycle_stage"]
            for domain in self.canonical["domains"]
            for field in domain["fields"]
        )
        self.assertEqual(str(self.canonical["dictionary_revision"]), "0.6.0")
        self.assertEqual(len(self.canonical["domains"]), 46)
        self.assertEqual(sum(lifecycle.values()), 1235)
        self.assertEqual(lifecycle["core"], 744)

    # 测试函数 `test_auction_date_only_time_governance`：验证 `auction、date、only、time、governance` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_auction_date_only_time_governance(self) -> None:
        snapshot_time = self.index[("auction", "snapshot_time")]
        precision = self.index[("auction", "snapshot_time_precision")]
        self.assertTrue(snapshot_time["nullable"])
        self.assertEqual(snapshot_time["time_semantics"], "observation_time")
        self.assertFalse(precision["nullable"])
        self.assertEqual(precision["enum_ref"], "snapshot_time_precision")

    # 测试函数 `test_classification_market_object_exists`：验证 `classification、market、object、exists` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_classification_market_object_exists(self) -> None:
        domain = next(
            item for item in self.canonical["domains"]
            if item["canonical_object"] == "ClassificationMarketSnapshot"
        )
        fields = {item["canonical_name"] for item in domain["fields"]}
        self.assertIn("snapshot_phase", fields)
        self.assertIn("breadth_status", fields)
        self.assertIn("leading_instrument_id", fields)
        self.assertNotIn("average_shares", fields)

    # 测试函数 `test_required_enums_exist`：验证 `required、enums、exist` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_required_enums_exist(self) -> None:
        enums = yaml.safe_load(
            (PROJECT_ROOT / "schemas" / "enum_definitions.yaml").read_text(
                encoding="utf-8"
            )
        )
        self.assertIn("DATE_ONLY", enums["snapshot_time_precision"])
        self.assertIn("OPENING_AUCTION", enums["snapshot_phase"])
        self.assertIn("RATIO_MISMATCH_WARNING", enums["breadth_status"])

    # 测试函数 `test_field_governance_passes`：验证 `field、governance、passes` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_field_governance_passes(self) -> None:
        result = validate_dictionary_governance(PROJECT_ROOT)
        self.assertEqual(result["overall_status"], "PASSED")
        self.assertEqual(result["issues"], [])

    # 测试函数 `test_all_seven_mappings_are_unblocked`：验证 `all、seven、mappings、are、unblocked` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_all_seven_mappings_are_unblocked(self) -> None:
        result = validate_contract(
            PROJECT_ROOT / "configs" / "mappings" / "a_stock_daily_funds_canonical_v0.yaml",
            PROJECT_ROOT / "schemas" / "canonical_fields.yaml",
        )
        self.assertEqual(result["overall_status"], "PASSED_WITH_WARNINGS")
        self.assertEqual(result["ready_with_warning_count"], 7)
        self.assertEqual(result["blocked_count"], 0)


if __name__ == "__main__":
    unittest.main()
