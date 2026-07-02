# 本文件核心功能：验证TASK_023A环境发现合同、安全计数器和候选排序。
# - 输入：来自项目配置、离线本地环境、命令行参数或单元测试夹具；不读取未声明的秘密值。
# - 处理：先完成类型和值域校验，再执行离线发现、排序、报告生成或断言；默认不联网、不交易、不写数据库。
# - 输出：强类型对象、UTF-8 JSON报告、稳定退出码或可重复测试结果，供下一任务和Git门禁使用。
# - 常量依据：任务号、来源层级、安全计数器和状态值来自TASK_022至TASK_024权威文件与官方接口基线。
# - 为什么这样写：教学式前置说明让维护者先理解边界再阅读实现，也防止第三方聚合源或交易能力被误升为主链。

# 本测试文件核心功能：验证TASK_023A环境发现合同、安全边界和候选排序。
"""TASK_023A Provider环境发现测试。"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from a_stock_quant.provider_environment_discovery import (
    ProviderTargetSpec,
    build_provider_environment_report,
    discover_provider_environment,
    load_provider_discovery_manifest,
    rank_next_discovery_candidates,
)


# 本段代码核心功能：定义 `ProviderEnvironmentDiscoveryTests`，组织验证TASK_023A环境发现合同、安全计数器和候选排序的独立测试场景。
# - 输入：类实例字段由配置加载器、发现流程或测试夹具显式传入；不从全局状态隐式取值。
# - 处理：使用类型标注、不可变数据类或枚举限制字段形状和允许状态，避免原始字典在系统内扩散。
# - 输出：输出可比较、可序列化或可排序的 `ProviderEnvironmentDiscoveryTests` 实例，供后续报告和门禁使用。
# - 常量依据：状态名和字段名来自TASK_022至TASK_024任务合同；本定义不新增未经验证的厂商能力。
# - 为什么这样写：先建立稳定合同，再接官方SDK或券商接口，能够降低供应商替换成本并阻止秘密值进入报告。

class ProviderEnvironmentDiscoveryTests(unittest.TestCase):
    # 本段代码核心功能：定义 `_target`，提供局部纯函数辅助，统一规范化、查找或匹配规则。
    # - 输入：参数为 `self、provider_id、modules、credentials、execution、priority`；路径和外部文本按UTF-8处理，安全开关必须由显式配置提供。
    # - 处理：只执行函数名对应的单一职责；遇到缺字段、非法状态或越界值立即失败，不做静默猜测。
    # - 输出：返回类型为 `ProviderTargetSpec`；测试函数则通过断言表达通过或失败，不产生生产副作用。
    # - 常量依据：任务号、状态枚举、零网络/零交易计数和候选优先级均来自TASK_022至TASK_024权威任务合同。
    # - 为什么这样写：显式输入输出和失败模式便于教学排查，也让未来官方交易所或券商SDK只需通过薄适配器接入。

    def _target(
        self,
        provider_id: str,
        *,
        modules: tuple[str, ...] = (),
        credentials: tuple[str, ...] = (),
        execution: bool = False,
        priority: int = 30,
    ) -> ProviderTargetSpec:
        return ProviderTargetSpec(
            provider_id=provider_id,
            display_name=provider_id,
            provider_kind="TEST",
            execution_capability=execution,
            priority=priority,
            python_module_candidates=modules,
            credential_reference_names=credentials,
            discovery_method="TEST",
            evidence_level="TEST",
            license_review_required=True,
        )

    # 本段代码核心功能：定义 `test_manifest_rejects_secret_and_network_permissions`，构造单一可重复场景，断言对应业务合同和安全边界不会回退。
    # - 输入：参数为 `self`；路径和外部文本按UTF-8处理，安全开关必须由显式配置提供。
    # - 处理：只执行函数名对应的单一职责；遇到缺字段、非法状态或越界值立即失败，不做静默猜测。
    # - 输出：返回类型为 `None`；测试函数则通过断言表达通过或失败，不产生生产副作用。
    # - 常量依据：任务号、状态枚举、零网络/零交易计数和候选优先级均来自TASK_022至TASK_024权威任务合同。
    # - 为什么这样写：显式输入输出和失败模式便于教学排查，也让未来官方交易所或券商SDK只需通过薄适配器接入。

    def test_manifest_rejects_secret_and_network_permissions(self) -> None:
        # 本段代码核心功能：在受控上下文中打开临时资源并保证离开代码块时自动释放。
        # - 输入：临时目录、文件句柄或补丁上下文。
        # - 处理：上下文管理器负责建立和清理资源，业务代码只处理块内对象。
        # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
        # - 为什么这样写：自动清理可以防止测试污染、文件句柄泄漏和跨任务状态残留。

        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "manifest.json"
            path.write_text(
                json.dumps(
                    {
                        "secret_values_allowed": True,
                        "vendor_sdk_import_allowed": False,
                        "network_calls_allowed": False,
                        "targets": [{}],
                    }
                ),
                encoding="utf-8",
            )
            # 本段代码核心功能：在受控上下文中打开临时资源并保证离开代码块时自动释放。
            # - 输入：临时目录、文件句柄或补丁上下文。
            # - 处理：上下文管理器负责建立和清理资源，业务代码只处理块内对象。
            # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
            # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
            # - 为什么这样写：自动清理可以防止测试污染、文件句柄泄漏和跨任务状态残留。

            with self.assertRaisesRegex(ValueError, "secret_values_allowed"):
                load_provider_discovery_manifest(path)

    # 本段代码核心功能：定义 `test_discovery_uses_find_spec_without_importing_vendor_sdk`，构造单一可重复场景，断言对应业务合同和安全边界不会回退。
    # - 输入：参数为 `self`；路径和外部文本按UTF-8处理，安全开关必须由显式配置提供。
    # - 处理：只执行函数名对应的单一职责；遇到缺字段、非法状态或越界值立即失败，不做静默猜测。
    # - 输出：返回类型为 `None`；测试函数则通过断言表达通过或失败，不产生生产副作用。
    # - 常量依据：任务号、状态枚举、零网络/零交易计数和候选优先级均来自TASK_022至TASK_024权威任务合同。
    # - 为什么这样写：显式输入输出和失败模式便于教学排查，也让未来官方交易所或券商SDK只需通过薄适配器接入。

    def test_discovery_uses_find_spec_without_importing_vendor_sdk(self) -> None:
        calls: list[str] = []

        # 本段代码核心功能：定义 `fake_find_spec`，完成fake_find_spec对应的单一业务步骤并返回明确结果。
        # - 输入：参数为 `name`；路径和外部文本按UTF-8处理，安全开关必须由显式配置提供。
        # - 处理：只执行函数名对应的单一职责；遇到缺字段、非法状态或越界值立即失败，不做静默猜测。
        # - 输出：返回类型为 `object | None`；测试函数则通过断言表达通过或失败，不产生生产副作用。
        # - 常量依据：任务号、状态枚举、零网络/零交易计数和候选优先级均来自TASK_022至TASK_024权威任务合同。
        # - 为什么这样写：显式输入输出和失败模式便于教学排查，也让未来官方交易所或券商SDK只需通过薄适配器接入。

        def fake_find_spec(name: str) -> object | None:
            calls.append(name)
            return object() if name == "installed_sdk" else None

        findings = discover_provider_environment(
            (self._target("vendor", modules=("installed_sdk", "missing_sdk")),),
            environ={},
            find_spec=fake_find_spec,
        )
        self.assertEqual(calls, ["installed_sdk", "missing_sdk"])
        self.assertEqual(findings[0].runtime_status, "RUNTIME_PRESENT")
        self.assertEqual(findings[0].detected_python_modules, ("installed_sdk",))

    # 本段代码核心功能：定义 `test_credential_values_never_enter_report`，构造单一可重复场景，断言对应业务合同和安全边界不会回退。
    # - 输入：参数为 `self`；路径和外部文本按UTF-8处理，安全开关必须由显式配置提供。
    # - 处理：只执行函数名对应的单一职责；遇到缺字段、非法状态或越界值立即失败，不做静默猜测。
    # - 输出：返回类型为 `None`；测试函数则通过断言表达通过或失败，不产生生产副作用。
    # - 常量依据：任务号、状态枚举、零网络/零交易计数和候选优先级均来自TASK_022至TASK_024权威任务合同。
    # - 为什么这样写：显式输入输出和失败模式便于教学排查，也让未来官方交易所或券商SDK只需通过薄适配器接入。

    def test_credential_values_never_enter_report(self) -> None:
        secret_value = "must-not-appear"
        findings = discover_provider_environment(
            (self._target("vendor", modules=("sdk",), credentials=("TOKEN_NAME",)),),
            environ={"TOKEN_NAME": secret_value},
            find_spec=lambda _: object(),
        )
        report_text = json.dumps(build_provider_environment_report(findings), ensure_ascii=False)
        self.assertIn("TOKEN_NAME", report_text)
        self.assertNotIn(secret_value, report_text)
        self.assertEqual(findings[0].present_credential_references, ("TOKEN_NAME",))

    # 本段代码核心功能：定义 `test_execution_provider_is_never_recommended_automatically`，构造单一可重复场景，断言对应业务合同和安全边界不会回退。
    # - 输入：参数为 `self`；路径和外部文本按UTF-8处理，安全开关必须由显式配置提供。
    # - 处理：只执行函数名对应的单一职责；遇到缺字段、非法状态或越界值立即失败，不做静默猜测。
    # - 输出：返回类型为 `None`；测试函数则通过断言表达通过或失败，不产生生产副作用。
    # - 常量依据：任务号、状态枚举、零网络/零交易计数和候选优先级均来自TASK_022至TASK_024权威任务合同。
    # - 为什么这样写：显式输入输出和失败模式便于教学排查，也让未来官方交易所或券商SDK只需通过薄适配器接入。

    def test_execution_provider_is_never_recommended_automatically(self) -> None:
        findings = discover_provider_environment(
            (
                self._target("data_provider", modules=("sdk",), priority=20),
                self._target("broker", modules=("sdk",), execution=True, priority=10),
            ),
            environ={},
            find_spec=lambda _: object(),
        )
        self.assertEqual(rank_next_discovery_candidates(findings), ("data_provider",))

    # 本段代码核心功能：定义 `test_candidate_ranking_is_deterministic`，构造单一可重复场景，断言对应业务合同和安全边界不会回退。
    # - 输入：参数为 `self`；路径和外部文本按UTF-8处理，安全开关必须由显式配置提供。
    # - 处理：只执行函数名对应的单一职责；遇到缺字段、非法状态或越界值立即失败，不做静默猜测。
    # - 输出：返回类型为 `None`；测试函数则通过断言表达通过或失败，不产生生产副作用。
    # - 常量依据：任务号、状态枚举、零网络/零交易计数和候选优先级均来自TASK_022至TASK_024权威任务合同。
    # - 为什么这样写：显式输入输出和失败模式便于教学排查，也让未来官方交易所或券商SDK只需通过薄适配器接入。

    def test_candidate_ranking_is_deterministic(self) -> None:
        findings = discover_provider_environment(
            (
                self._target("z_provider", modules=("sdk",), priority=30),
                self._target("a_provider", modules=("sdk",), priority=30),
                self._target("first_provider", modules=("sdk",), priority=10),
            ),
            environ={},
            find_spec=lambda _: object(),
        )
        self.assertEqual(
            rank_next_discovery_candidates(findings),
            ("first_provider", "a_provider", "z_provider"),
        )

    # 本段代码核心功能：定义 `test_manual_review_target_remains_blocked`，构造单一可重复场景，断言对应业务合同和安全边界不会回退。
    # - 输入：参数为 `self`；路径和外部文本按UTF-8处理，安全开关必须由显式配置提供。
    # - 处理：只执行函数名对应的单一职责；遇到缺字段、非法状态或越界值立即失败，不做静默猜测。
    # - 输出：返回类型为 `None`；测试函数则通过断言表达通过或失败，不产生生产副作用。
    # - 常量依据：任务号、状态枚举、零网络/零交易计数和候选优先级均来自TASK_022至TASK_024权威任务合同。
    # - 为什么这样写：显式输入输出和失败模式便于教学排查，也让未来官方交易所或券商SDK只需通过薄适配器接入。

    def test_manual_review_target_remains_blocked(self) -> None:
        findings = discover_provider_environment(
            (self._target("manual_provider"),),
            environ={},
            find_spec=lambda _: None,
        )
        self.assertEqual(findings[0].runtime_status, "MANUAL_REVIEW_REQUIRED")
        self.assertFalse(findings[0].eligible_for_next_discovery)
        self.assertIn("NO_VERIFIED_PYTHON_MODULE_HINT", findings[0].blockers)


# 本段代码核心功能：根据条件 `__name__ == '__main__'` 选择安全分支。
# - 输入：条件表达式及此前已经规范化的局部变量。
# - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
# - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
# - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
# - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

if __name__ == "__main__":
    unittest.main()
