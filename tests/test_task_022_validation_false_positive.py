"""TASK_022 离线校验器回归测试。"""
from __future__ import annotations

import unittest

from scripts.validate_task_022_provider_activation import contains_string_literal


# 校验误报回归测试类：区分教学式注释文本与可执行代码中的真实字符串字面量。
# - 输入：分别只在注释中出现、以及在运行时代码中出现的历史警告名称。
# - 输出：注释场景返回 False，运行时字符串场景返回 True。
# - 为什么这样写：修复全文搜索误报时仍要保留对真实运行时警告的阻断能力。
class Task022ValidationFalsePositiveTest(unittest.TestCase):
    # 测试注释隔离：历史警告名称只出现在注释时，不应被识别为运行时字符串。
    # - 输入：包含目标文本的 Python 注释。
    # - 输出：contains_string_literal 返回 False。
    # - 为什么这样写：防止教学式注释再次触发全文搜索式误报。
    def test_comment_text_is_not_runtime_literal(self) -> None:
        source = "# REGISTRY_ACTIVATION_REQUIRES_SEPARATE_TASK\nvalue = 1\n"
        self.assertFalse(
            contains_string_literal(source, "REGISTRY_ACTIVATION_REQUIRES_SEPARATE_TASK")
        )

    # 测试真实字面量：目标文本仍处于可执行字符串常量时必须被识别。
    # - 输入：包含目标字符串字面量的 Python 列表。
    # - 输出：contains_string_literal 返回 True。
    # - 为什么这样写：修复误报的同时不能放松对真实运行时警告的阻断。
    def test_runtime_string_literal_is_detected(self) -> None:
        source = 'warnings = ["REGISTRY_ACTIVATION_REQUIRES_SEPARATE_TASK"]\n'
        self.assertTrue(
            contains_string_literal(source, "REGISTRY_ACTIVATION_REQUIRES_SEPARATE_TASK")
        )


if __name__ == "__main__":
    unittest.main()
