# 测试模块总览：验证 `test_field_dictionary_governance` 对应功能的合同、边界和历史回归行为。
# - 输入：构造样例、测试夹具、临时文件以及被测模块公开接口。
# - 处理：只执行测试和断言，不修改生产算法、金融语义或正式数据库。
# - 输出：可重复的通过/失败证据，供全量回归和任务验收使用。
# - 为什么这样写：把业务要求固化为自动测试，使后续注释迁移和重构能够证明行为未变化。
from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from a_stock_quant.field_dictionary_governance import (  # noqa: E402
    EXPECTED_DICTIONARY_REVISION,
    EXPECTED_VALUE_DOMAIN_KINDS,
    field_index,
    load_yaml,
    validate_dictionary_governance,
)


# 测试类 `TestFieldDictionaryGovernance`：集中验证 `test_field_dictionary_governance` 相关合同、边界条件和回归行为。
# - 输入：测试夹具、构造样例以及被测模块公开接口。
# - 处理：按独立场景组织断言，覆盖正常路径、失败门禁和关键边界。
# - 输出：通过或失败的单元测试结果，不产生正式业务数据。
# - 为什么这样写：把同一职责的回归场景集中管理，便于定位失败并防止后续修改破坏既有合同。
class TestFieldDictionaryGovernance(unittest.TestCase):
    # 测试函数 `setUp`：准备本组测试共享的对象、样例和环境状态。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def setUp(self) -> None:
        self.canonical = load_yaml(
            PROJECT_ROOT / "schemas" / "canonical_fields.yaml"
        )
        self.contract = load_yaml(
            PROJECT_ROOT / "schemas" / "field_governance_contract.yaml"
        )
        self.index = field_index(self.canonical)

    # 测试函数 `test_dictionary_revision_is_hardened`：验证 `dictionary、revision、is、hardened` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_dictionary_revision_is_hardened(self) -> None:
        self.assertEqual(
            str(self.canonical["dictionary_revision"]),
            EXPECTED_DICTIONARY_REVISION,
        )
        self.assertEqual(
            str(self.contract["dictionary_revision"]),
            EXPECTED_DICTIONARY_REVISION,
        )

    # 测试函数 `test_value_domain_kinds_are_explicit`：验证 `value、domain、kinds、are、explicit` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_value_domain_kinds_are_explicit(self) -> None:
        self.assertEqual(
            set(self.contract["value_domain_kinds"]),
            EXPECTED_VALUE_DOMAIN_KINDS,
        )

    # 测试函数 `test_required_metadata_matches_contract`：验证 `required、metadata、matches、contract` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_required_metadata_matches_contract(self) -> None:
        # 参数化循环：逐项使用 `self.contract['required_metadata']` 验证同一合同。
        # - 处理：每轮保留原样例、顺序和断言，便于定位具体失败项。
        # - 为什么这样写：用一致规则覆盖多组输入，减少复制测试并提高边界覆盖率。
        for requirement in self.contract["required_metadata"]:
            key = (
                requirement["domain_code"],
                requirement["canonical_name"],
            )
            self.assertIn(key, self.index)
            self.assertEqual(
                self.index[key].get(requirement["key"]),
                requirement["value"],
            )

    # 测试函数 `test_semantic_collisions_are_governed`：验证 `semantic、collisions、are、governed` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_semantic_collisions_are_governed(self) -> None:
        report = validate_dictionary_governance(PROJECT_ROOT)
        self.assertEqual(report["overall_status"], "PASSED")
        self.assertEqual(report["issues"], [])

    # 测试函数 `test_trade_count_is_not_silently_renamed`：验证 `trade、count、is、not、silently、renamed` 场景是否满足既定预期。
    # - 输入：测试对象状态、固定样例或当前测试夹具。
    # - 处理：调用被测接口并比较实际结果、异常或状态与预期合同。
    # - 输出：通过断言表达成功；不符合预期时由测试框架记录失败证据。
    # - 为什么这样写：把一个行为要求固定为可重复执行的回归测试，避免注释迁移或后续重构静默改变业务语义。
    def test_trade_count_is_not_silently_renamed(self) -> None:
        self.assertIn(("backtest", "trade_count"), self.index)
        self.assertNotIn(("backtest", "executed_trade_count"), self.index)


if __name__ == "__main__":
    unittest.main()
