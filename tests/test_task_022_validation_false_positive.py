# 本文件核心功能：实现 `test_task_022_validation_false_positive.py` 在TASK_022至TASK_024范围内的单一任务职责。
# - 输入：来自项目配置、离线本地环境、命令行参数或单元测试夹具，不读取未声明秘密值。
# - 处理：先完成类型和值域校验，再执行离线发现、排序、报告生成或断言；默认不联网、不交易、不写数据库。
# - 输出：强类型对象、UTF-8报告、稳定退出码或可重复测试结果，供下一任务和Git门禁使用。
# - 常量依据：任务号、来源层级、安全计数器和状态值来自TASK_022至TASK_024权威文件与官方接口基线。
# - 为什么这样写：维护者先理解边界再阅读实现，可防止第三方聚合源或交易能力被误升为主链。

"""TASK_022 离线校验器回归测试。"""
from __future__ import annotations

import unittest

from scripts.validate_task_022_provider_activation import contains_string_literal


# 校验误报回归测试类：区分教学式注释文本与可执行代码中的真实字符串字面量。
# - 输入：分别只在注释中出现、以及在运行时代码中出现的历史警告名称。
# - 输出：注释场景返回 False，运行时字符串场景返回 True。
# - 为什么这样写：修复全文搜索误报时仍要保留对真实运行时警告的阻断能力。
# 本段代码核心功能：定义 `Task022ValidationFalsePositiveTest`，封装 `test_task_022_validation_false_positive.py` 所需的稳定数据结构。
# - 输入：实例字段由配置加载器、发现流程或测试夹具显式传入，不从全局状态隐式取值。
# - 处理：使用类型标注、不可变数据类或枚举限制字段形状和允许状态，避免原始字典扩散。
# - 输出：输出可比较、可序列化或可排序的 `Task022ValidationFalsePositiveTest` 实例，供报告和门禁使用。
# - 常量依据：状态名和字段名来自TASK_022至TASK_024任务合同，本定义不新增未经验证的厂商能力。
# - 为什么这样写：先建立稳定合同再接官方SDK，能够降低供应商替换成本并阻止秘密值进入报告。

class Task022ValidationFalsePositiveTest(unittest.TestCase):
    # 测试注释隔离：历史警告名称只出现在注释时，不应被识别为运行时字符串。
    # - 输入：包含目标文本的 Python 注释。
    # - 输出：contains_string_literal 返回 False。
    # - 为什么这样写：防止教学式注释再次触发全文搜索式误报。
    # 本段代码核心功能：定义 `test_comment_text_is_not_runtime_literal`，构造可重复场景并断言对应业务合同和安全边界不会回退。
    # - 输入：参数为 `self`；路径和外部文本按UTF-8处理，安全开关必须由显式配置提供。
    # - 处理：只执行函数名对应的单一职责；缺字段、非法状态或越界值立即失败，不做静默猜测。
    # - 输出：返回类型为 `None`；测试函数通过断言表达通过或失败，不产生生产副作用。
    # - 常量依据：任务号、状态枚举、零网络/零交易计数和候选优先级来自TASK_022至TASK_024权威合同。
    # - 为什么这样写：显式输入输出和失败模式便于教学排查，也让官方交易所或券商SDK通过薄适配器接入。

    def test_comment_text_is_not_runtime_literal(self) -> None:
        source = "# REGISTRY_ACTIVATION_REQUIRES_SEPARATE_TASK\nvalue = 1\n"
        self.assertFalse(
            contains_string_literal(source, "REGISTRY_ACTIVATION_REQUIRES_SEPARATE_TASK")
        )

    # 测试真实字面量：目标文本仍处于可执行字符串常量时必须被识别。
    # - 输入：包含目标字符串字面量的 Python 列表。
    # - 输出：contains_string_literal 返回 True。
    # - 为什么这样写：修复误报的同时不能放松对真实运行时警告的阻断。
    # 本段代码核心功能：定义 `test_runtime_string_literal_is_detected`，构造可重复场景并断言对应业务合同和安全边界不会回退。
    # - 输入：参数为 `self`；路径和外部文本按UTF-8处理，安全开关必须由显式配置提供。
    # - 处理：只执行函数名对应的单一职责；缺字段、非法状态或越界值立即失败，不做静默猜测。
    # - 输出：返回类型为 `None`；测试函数通过断言表达通过或失败，不产生生产副作用。
    # - 常量依据：任务号、状态枚举、零网络/零交易计数和候选优先级来自TASK_022至TASK_024权威合同。
    # - 为什么这样写：显式输入输出和失败模式便于教学排查，也让官方交易所或券商SDK通过薄适配器接入。

    def test_runtime_string_literal_is_detected(self) -> None:
        source = 'warnings = ["REGISTRY_ACTIVATION_REQUIRES_SEPARATE_TASK"]\n'
        self.assertTrue(
            contains_string_literal(source, "REGISTRY_ACTIVATION_REQUIRES_SEPARATE_TASK")
        )


# 本段代码核心功能：根据条件 `__name__ == '__main__'` 选择安全分支。
# - 输入：条件表达式和此前已经规范化的局部变量。
# - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
# - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
# - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
# - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

if __name__ == "__main__":
    unittest.main()
