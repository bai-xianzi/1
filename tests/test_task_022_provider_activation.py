# 本文件核心功能：实现 `test_task_022_provider_activation.py` 在TASK_022至TASK_024范围内的单一任务职责。
# - 输入：来自项目配置、离线本地环境、命令行参数或单元测试夹具，不读取未声明秘密值。
# - 处理：先完成类型和值域校验，再执行离线发现、排序、报告生成或断言；默认不联网、不交易、不写数据库。
# - 输出：强类型对象、UTF-8报告、稳定退出码或可重复测试结果，供下一任务和Git门禁使用。
# - 常量依据：任务号、来源层级、安全计数器和状态值来自TASK_022至TASK_024权威文件与官方接口基线。
# - 为什么这样写：维护者先理解边界再阅读实现，可防止第三方聚合源或交易能力被误升为主链。

"""TASK_022 正式配置回归测试。"""
from __future__ import annotations

import json
import unittest
from pathlib import Path

from a_stock_quant.provider_capabilities import ProviderLifecycle, load_provider_capability_matrix
from a_stock_quant.provider_plugin_protocol import PluginRegistrationStatus, load_provider_plugin_registry

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "configs/providers/provider_plugin_registry_v0.json"
MATRIX = ROOT / "configs/providers/provider_capability_matrix_v0.json"


# TASK_022 Provider 激活测试类：集中验证正式配置、强类型合同和路由激活状态。
# - 输入：项目中的 Provider 插件注册表、能力矩阵及其标准加载函数。
# - 输出：四组相互独立的回归断言，覆盖合同身份、唯一启用路由和激活生命周期。
# - 为什么这样写：把配置层与对象层同时纳入测试，防止后续修改只更新 JSON 而破坏运行时合同。
# 本段代码核心功能：定义 `Task022ProviderActivationTest`，封装 `test_task_022_provider_activation.py` 所需的稳定数据结构。
# - 输入：实例字段由配置加载器、发现流程或测试夹具显式传入，不从全局状态隐式取值。
# - 处理：使用类型标注、不可变数据类或枚举限制字段形状和允许状态，避免原始字典扩散。
# - 输出：输出可比较、可序列化或可排序的 `Task022ProviderActivationTest` 实例，供报告和门禁使用。
# - 常量依据：状态名和字段名来自TASK_022至TASK_024任务合同，本定义不新增未经验证的厂商能力。
# - 为什么这样写：先建立稳定合同再接官方SDK，能够降低供应商替换成本并阻止秘密值进入报告。

class Task022ProviderActivationTest(unittest.TestCase):
    # 合同身份测试：确认 TASK_022 激活不改写 TASK_020A 与 TASK_020B 的强类型来源身份。
    # - 输入：直接读取两个正式 JSON 配置中的 task_id。
    # - 输出：注册表保持 TASK_020B，能力矩阵保持 TASK_020A。
    # - 为什么这样写：task_id 表示合同来源而不是最近修改任务，错误改写会被加载器拒绝。
    # 本段代码核心功能：定义 `test_contract_identity_task_ids_are_preserved`，构造可重复场景并断言对应业务合同和安全边界不会回退。
    # - 输入：参数为 `self`；路径和外部文本按UTF-8处理，安全开关必须由显式配置提供。
    # - 处理：只执行函数名对应的单一职责；缺字段、非法状态或越界值立即失败，不做静默猜测。
    # - 输出：返回类型为 `None`；测试函数通过断言表达通过或失败，不产生生产副作用。
    # - 常量依据：任务号、状态枚举、零网络/零交易计数和候选优先级来自TASK_022至TASK_024权威合同。
    # - 为什么这样写：显式输入输出和失败模式便于教学排查，也让官方交易所或券商SDK通过薄适配器接入。

    def test_contract_identity_task_ids_are_preserved(self) -> None:
        registry_raw = json.loads(REGISTRY.read_text(encoding="utf-8-sig"))
        matrix_raw = json.loads(MATRIX.read_text(encoding="utf-8-sig"))
        self.assertEqual(registry_raw["task_id"], "TASK_020B")
        self.assertEqual(matrix_raw["task_id"], "TASK_020A")

    # 唯一路由测试：确认正式配置只允许本地 DolphinDB 参与数据路由。
    # - 输入：插件注册表 entries 与 automatic_activation_allowed 总开关。
    # - 输出：enabled_for_routing 列表仅包含 local_dolphindb，自动激活仍关闭。
    # - 为什么这样写：TASK_022 只激活一个已验收 Provider，不能顺带放开其他商业或未验收来源。
    # 本段代码核心功能：定义 `test_only_local_dolphindb_is_enabled`，构造可重复场景并断言对应业务合同和安全边界不会回退。
    # - 输入：参数为 `self`；路径和外部文本按UTF-8处理，安全开关必须由显式配置提供。
    # - 处理：只执行函数名对应的单一职责；缺字段、非法状态或越界值立即失败，不做静默猜测。
    # - 输出：返回类型为 `None`；测试函数通过断言表达通过或失败，不产生生产副作用。
    # - 常量依据：任务号、状态枚举、零网络/零交易计数和候选优先级来自TASK_022至TASK_024权威合同。
    # - 为什么这样写：显式输入输出和失败模式便于教学排查，也让官方交易所或券商SDK通过薄适配器接入。

    def test_only_local_dolphindb_is_enabled(self) -> None:
        raw = json.loads(REGISTRY.read_text(encoding="utf-8-sig"))
        enabled = [x["provider_id"] for x in raw["entries"] if x["enabled_for_routing"]]
        self.assertEqual(enabled, ["local_dolphindb"])
        self.assertFalse(raw["automatic_activation_allowed"])

    # 注册表对象测试：使用正式加载器验证 DolphinDB 插件已经进入可用路由状态。
    # - 输入：provider_plugin_registry_v0.json 的强类型加载结果。
    # - 输出：状态为 AVAILABLE、路由启用、插件入口和发现报告引用均存在。
    # - 为什么这样写：直接检查运行时对象可以发现 JSON 字段拼写正确但合同映射错误的问题。
    # 本段代码核心功能：定义 `test_registry_loads_as_available`，构造可重复场景并断言对应业务合同和安全边界不会回退。
    # - 输入：参数为 `self`；路径和外部文本按UTF-8处理，安全开关必须由显式配置提供。
    # - 处理：只执行函数名对应的单一职责；缺字段、非法状态或越界值立即失败，不做静默猜测。
    # - 输出：返回类型为 `None`；测试函数通过断言表达通过或失败，不产生生产副作用。
    # - 常量依据：任务号、状态枚举、零网络/零交易计数和候选优先级来自TASK_022至TASK_024权威合同。
    # - 为什么这样写：显式输入输出和失败模式便于教学排查，也让官方交易所或券商SDK通过薄适配器接入。

    def test_registry_loads_as_available(self) -> None:
        registry = load_provider_plugin_registry(REGISTRY)
        entry = next(x for x in registry.entries if x.provider_id == "local_dolphindb")
        self.assertIs(entry.registration_status, PluginRegistrationStatus.AVAILABLE)
        self.assertTrue(entry.enabled_for_routing)
        self.assertEqual(entry.plugin_id, "builtin.local_dolphindb.plugin_bridge")
        self.assertTrue(entry.discovery_result_ref)

    # 能力矩阵对象测试：确认本地 DolphinDB 已激活日线数据能力但没有交易执行能力。
    # - 输入：provider_capability_matrix_v0.json 的强类型加载结果及 EOD 路由筛选。
    # - 输出：生命周期为 ACTIVATED，execution_capability 为 False，且能进入 EOD 候选列表。
    # - 为什么这样写：数据路由激活与交易权限必须保持分离，防止只读 Provider 被错误提升为执行通道。
    # 本段代码核心功能：定义 `test_matrix_loads_as_activated`，构造可重复场景并断言对应业务合同和安全边界不会回退。
    # - 输入：参数为 `self`；路径和外部文本按UTF-8处理，安全开关必须由显式配置提供。
    # - 处理：只执行函数名对应的单一职责；缺字段、非法状态或越界值立即失败，不做静默猜测。
    # - 输出：返回类型为 `None`；测试函数通过断言表达通过或失败，不产生生产副作用。
    # - 常量依据：任务号、状态枚举、零网络/零交易计数和候选优先级来自TASK_022至TASK_024权威合同。
    # - 为什么这样写：显式输入输出和失败模式便于教学排查，也让官方交易所或券商SDK通过薄适配器接入。

    def test_matrix_loads_as_activated(self) -> None:
        matrix = load_provider_capability_matrix(MATRIX)
        target = matrix.provider("local_dolphindb")
        self.assertIs(target.lifecycle, ProviderLifecycle.ACTIVATED)
        self.assertFalse(target.execution_capability)
        eligible = matrix.eligible_providers("EOD_MARKET_DATA")
        self.assertIn("local_dolphindb", [x.provider_id for x in eligible])


# 本段代码核心功能：根据条件 `__name__ == '__main__'` 选择安全分支。
# - 输入：条件表达式和此前已经规范化的局部变量。
# - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
# - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
# - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
# - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

if __name__ == "__main__":
    unittest.main()
