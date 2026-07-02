# 本文件核心功能：验证TASK_023B机器级证据分类、隐私边界和排序规则。
# - 输入：来自项目配置、离线本地环境、命令行参数或单元测试夹具；不读取未声明的秘密值。
# - 处理：先完成类型和值域校验，再执行离线发现、排序、报告生成或断言；默认不联网、不交易、不写数据库。
# - 输出：强类型对象、UTF-8 JSON报告、稳定退出码或可重复测试结果，供下一任务和Git门禁使用。
# - 常量依据：任务号、来源层级、安全计数器和状态值来自TASK_022至TASK_024权威文件与官方接口基线。
# - 为什么这样写：教学式前置说明让维护者先理解边界再阅读实现，也防止第三方聚合源或交易能力被误升为主链。

# 本测试文件核心功能：验证TASK_023B机器级盘点、证据评分、安全边界和候选排序。
"""TASK_023B Windows Provider盘点测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

from a_stock_quant.provider_environment_discovery import ProviderTargetSpec
from a_stock_quant.provider_windows_inventory import (
    InstalledApplicationEvidence,
    ProviderWindowsRule,
    PythonInterpreterEvidence,
    build_windows_inventory_report,
    build_windows_provider_findings,
    load_windows_inventory_rules,
    rank_task_023c_candidates,
)


# 本段代码核心功能：定义 `ProviderWindowsInventoryTests`，组织验证TASK_023B机器级证据分类、隐私边界和排序规则的独立测试场景。
# - 输入：类实例字段由配置加载器、发现流程或测试夹具显式传入；不从全局状态隐式取值。
# - 处理：使用类型标注、不可变数据类或枚举限制字段形状和允许状态，避免原始字典在系统内扩散。
# - 输出：输出可比较、可序列化或可排序的 `ProviderWindowsInventoryTests` 实例，供后续报告和门禁使用。
# - 常量依据：状态名和字段名来自TASK_022至TASK_024任务合同；本定义不新增未经验证的厂商能力。
# - 为什么这样写：先建立稳定合同，再接官方SDK或券商接口，能够降低供应商替换成本并阻止秘密值进入报告。

class ProviderWindowsInventoryTests(unittest.TestCase):
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

    # 本段代码核心功能：定义 `_rule`，提供局部纯函数辅助，统一规范化、查找或匹配规则。
    # - 输入：参数为 `self、provider_id、tokens、executables`；路径和外部文本按UTF-8处理，安全开关必须由显式配置提供。
    # - 处理：只执行函数名对应的单一职责；遇到缺字段、非法状态或越界值立即失败，不做静默猜测。
    # - 输出：返回类型为 `ProviderWindowsRule`；测试函数则通过断言表达通过或失败，不产生生产副作用。
    # - 常量依据：任务号、状态枚举、零网络/零交易计数和候选优先级均来自TASK_022至TASK_024权威任务合同。
    # - 为什么这样写：显式输入输出和失败模式便于教学排查，也让未来官方交易所或券商SDK只需通过薄适配器接入。

    def _rule(
        self,
        provider_id: str,
        *,
        tokens: tuple[str, ...] = (),
        executables: tuple[str, ...] = (),
    ) -> ProviderWindowsRule:
        return ProviderWindowsRule(provider_id, tokens, executables)

    # 本段代码核心功能：定义 `test_rules_reject_secret_or_network_permissions`，构造单一可重复场景，断言对应业务合同和安全边界不会回退。
    # - 输入：参数为 `self`；路径和外部文本按UTF-8处理，安全开关必须由显式配置提供。
    # - 处理：只执行函数名对应的单一职责；遇到缺字段、非法状态或越界值立即失败，不做静默猜测。
    # - 输出：返回类型为 `None`；测试函数则通过断言表达通过或失败，不产生生产副作用。
    # - 常量依据：任务号、状态枚举、零网络/零交易计数和候选优先级均来自TASK_022至TASK_024权威任务合同。
    # - 为什么这样写：显式输入输出和失败模式便于教学排查，也让未来官方交易所或券商SDK只需通过薄适配器接入。

    def test_rules_reject_secret_or_network_permissions(self) -> None:
        # 本段代码核心功能：在受控上下文中打开临时资源并保证离开代码块时自动释放。
        # - 输入：临时目录、文件句柄或补丁上下文。
        # - 处理：上下文管理器负责建立和清理资源，业务代码只处理块内对象。
        # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
        # - 为什么这样写：自动清理可以防止测试污染、文件句柄泄漏和跨任务状态残留。

        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "rules.json"
            path.write_text(
                json.dumps(
                    {
                        "secret_values_allowed": False,
                        "vendor_sdk_import_allowed": False,
                        "network_calls_allowed": True,
                        "registry_install_location_allowed": False,
                        "providers": [],
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

            with self.assertRaisesRegex(ValueError, "network_calls_allowed"):
                load_windows_inventory_rules(path)

    # 本段代码核心功能：定义 `test_current_interpreter_module_has_highest_evidence_weight`，构造单一可重复场景，断言对应业务合同和安全边界不会回退。
    # - 输入：参数为 `self`；路径和外部文本按UTF-8处理，安全开关必须由显式配置提供。
    # - 处理：只执行函数名对应的单一职责；遇到缺字段、非法状态或越界值立即失败，不做静默猜测。
    # - 输出：返回类型为 `None`；测试函数则通过断言表达通过或失败，不产生生产副作用。
    # - 常量依据：任务号、状态枚举、零网络/零交易计数和候选优先级均来自TASK_022至TASK_024权威任务合同。
    # - 为什么这样写：显式输入输出和失败模式便于教学排查，也让未来官方交易所或券商SDK只需通过薄适配器接入。

    def test_current_interpreter_module_has_highest_evidence_weight(self) -> None:
        target = self._target("vendor", modules=("sdk",))
        interpreters = (
            PythonInterpreterEvidence(
                executable=sys.executable,
                version="3.11",
                source="CURRENT_INTERPRETER",
                detected_modules=("sdk",),
                probe_status="PASSED",
            ),
        )
        finding = build_windows_provider_findings(
            (target,),
            (self._rule("vendor"),),
            interpreters,
            (),
            environ={},
            executable_lookup=lambda _: None,
        )[0]
        self.assertEqual(finding.evidence_score, 100)
        self.assertTrue(finding.eligible_for_task_023c_review)

    # 本段代码核心功能：定义 `test_other_interpreter_and_installed_client_are_separate_evidence`，构造单一可重复场景，断言对应业务合同和安全边界不会回退。
    # - 输入：参数为 `self`；路径和外部文本按UTF-8处理，安全开关必须由显式配置提供。
    # - 处理：只执行函数名对应的单一职责；遇到缺字段、非法状态或越界值立即失败，不做静默猜测。
    # - 输出：返回类型为 `None`；测试函数则通过断言表达通过或失败，不产生生产副作用。
    # - 常量依据：任务号、状态枚举、零网络/零交易计数和候选优先级均来自TASK_022至TASK_024权威任务合同。
    # - 为什么这样写：显式输入输出和失败模式便于教学排查，也让未来官方交易所或券商SDK只需通过薄适配器接入。

    def test_other_interpreter_and_installed_client_are_separate_evidence(self) -> None:
        target = self._target("vendor", modules=("sdk",))
        interpreters = (
            PythonInterpreterEvidence(
                executable="C:/OtherPython/python.exe",
                version="3.10",
                source="PY_LAUNCHER",
                detected_modules=("sdk",),
                probe_status="PASSED",
            ),
        )
        applications = (
            InstalledApplicationEvidence("Vendor Terminal", "1.0", "Vendor"),
        )
        finding = build_windows_provider_findings(
            (target,),
            (self._rule("vendor", tokens=("Vendor Terminal",)),),
            interpreters,
            applications,
            environ={},
            executable_lookup=lambda _: None,
        )[0]
        self.assertEqual(finding.evidence_score, 120)
        self.assertEqual(finding.other_interpreter_modules, ("sdk",))
        self.assertEqual(finding.matched_installed_applications, ("Vendor Terminal",))

    # 本段代码核心功能：定义 `test_execution_provider_is_never_task_023c_auto_candidate`，构造单一可重复场景，断言对应业务合同和安全边界不会回退。
    # - 输入：参数为 `self`；路径和外部文本按UTF-8处理，安全开关必须由显式配置提供。
    # - 处理：只执行函数名对应的单一职责；遇到缺字段、非法状态或越界值立即失败，不做静默猜测。
    # - 输出：返回类型为 `None`；测试函数则通过断言表达通过或失败，不产生生产副作用。
    # - 常量依据：任务号、状态枚举、零网络/零交易计数和候选优先级均来自TASK_022至TASK_024权威任务合同。
    # - 为什么这样写：显式输入输出和失败模式便于教学排查，也让未来官方交易所或券商SDK只需通过薄适配器接入。

    def test_execution_provider_is_never_task_023c_auto_candidate(self) -> None:
        target = self._target("broker", modules=("sdk",), execution=True)
        finding = build_windows_provider_findings(
            (target,),
            (self._rule("broker"),),
            (
                PythonInterpreterEvidence(
                    sys.executable,
                    "3.11",
                    "CURRENT_INTERPRETER",
                    ("sdk",),
                    "PASSED",
                ),
            ),
            (),
            environ={},
            executable_lookup=lambda _: None,
        )[0]
        self.assertFalse(finding.eligible_for_task_023c_review)
        self.assertEqual(finding.inventory_status, "SEPARATE_EXECUTION_REVIEW_REQUIRED")

    # 本段代码核心功能：定义 `test_secret_value_and_install_path_never_enter_report`，构造单一可重复场景，断言对应业务合同和安全边界不会回退。
    # - 输入：参数为 `self`；路径和外部文本按UTF-8处理，安全开关必须由显式配置提供。
    # - 处理：只执行函数名对应的单一职责；遇到缺字段、非法状态或越界值立即失败，不做静默猜测。
    # - 输出：返回类型为 `None`；测试函数则通过断言表达通过或失败，不产生生产副作用。
    # - 常量依据：任务号、状态枚举、零网络/零交易计数和候选优先级均来自TASK_022至TASK_024权威任务合同。
    # - 为什么这样写：显式输入输出和失败模式便于教学排查，也让未来官方交易所或券商SDK只需通过薄适配器接入。

    def test_secret_value_and_install_path_never_enter_report(self) -> None:
        secret = "never-record-this-token"
        target = self._target("vendor", credentials=("TOKEN_NAME",))
        finding = build_windows_provider_findings(
            (target,),
            (self._rule("vendor", tokens=("Vendor",)),),
            (),
            (InstalledApplicationEvidence("Vendor", "1.0", "Publisher"),),
            environ={"TOKEN_NAME": secret},
            executable_lookup=lambda _: None,
        )[0]
        report = build_windows_inventory_report(
            (finding,),
            (),
            (InstalledApplicationEvidence("Vendor", "1.0", "Publisher"),),
        )
        text = json.dumps(report, ensure_ascii=False)
        self.assertIn("TOKEN_NAME", text)
        self.assertNotIn(secret, text)
        self.assertNotIn("InstallLocation", text)
        self.assertNotIn("installed_applications", report)
        self.assertEqual(report["secret_values_recorded"], 0)
        self.assertEqual(report["installation_paths_recorded"], 0)

    # 本段代码核心功能：定义 `test_candidate_ranking_prefers_evidence_then_priority`，构造单一可重复场景，断言对应业务合同和安全边界不会回退。
    # - 输入：参数为 `self`；路径和外部文本按UTF-8处理，安全开关必须由显式配置提供。
    # - 处理：只执行函数名对应的单一职责；遇到缺字段、非法状态或越界值立即失败，不做静默猜测。
    # - 输出：返回类型为 `None`；测试函数则通过断言表达通过或失败，不产生生产副作用。
    # - 常量依据：任务号、状态枚举、零网络/零交易计数和候选优先级均来自TASK_022至TASK_024权威任务合同。
    # - 为什么这样写：显式输入输出和失败模式便于教学排查，也让未来官方交易所或券商SDK只需通过薄适配器接入。

    def test_candidate_ranking_prefers_evidence_then_priority(self) -> None:
        targets = (
            self._target("low_score", modules=("sdk_low",), priority=10),
            self._target("high_score_b", modules=("sdk_b",), priority=30),
            self._target("high_score_a", modules=("sdk_a",), priority=20),
        )
        rules = tuple(self._rule(target.provider_id) for target in targets)
        findings = build_windows_provider_findings(
            targets,
            rules,
            (
                PythonInterpreterEvidence(
                    sys.executable,
                    "3.11",
                    "CURRENT_INTERPRETER",
                    ("sdk_a", "sdk_b"),
                    "PASSED",
                ),
                PythonInterpreterEvidence(
                    "C:/Other/python.exe",
                    "3.10",
                    "PY_LAUNCHER",
                    ("sdk_low",),
                    "PASSED",
                ),
            ),
            (),
            environ={},
            executable_lookup=lambda _: None,
        )
        self.assertEqual(
            rank_task_023c_candidates(findings),
            ("high_score_a", "high_score_b", "low_score"),
        )

    # 本段代码核心功能：定义 `test_missing_rule_is_rejected`，构造单一可重复场景，断言对应业务合同和安全边界不会回退。
    # - 输入：参数为 `self`；路径和外部文本按UTF-8处理，安全开关必须由显式配置提供。
    # - 处理：只执行函数名对应的单一职责；遇到缺字段、非法状态或越界值立即失败，不做静默猜测。
    # - 输出：返回类型为 `None`；测试函数则通过断言表达通过或失败，不产生生产副作用。
    # - 常量依据：任务号、状态枚举、零网络/零交易计数和候选优先级均来自TASK_022至TASK_024权威任务合同。
    # - 为什么这样写：显式输入输出和失败模式便于教学排查，也让未来官方交易所或券商SDK只需通过薄适配器接入。

    def test_missing_rule_is_rejected(self) -> None:
        # 本段代码核心功能：在受控上下文中打开临时资源并保证离开代码块时自动释放。
        # - 输入：临时目录、文件句柄或补丁上下文。
        # - 处理：上下文管理器负责建立和清理资源，业务代码只处理块内对象。
        # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
        # - 为什么这样写：自动清理可以防止测试污染、文件句柄泄漏和跨任务状态残留。

        with self.assertRaisesRegex(ValueError, "missing Windows inventory rule"):
            build_windows_provider_findings(
                (self._target("vendor"),),
                (),
                (),
                (),
                environ={},
                executable_lookup=lambda _: None,
            )


# 本段代码核心功能：根据条件 `__name__ == '__main__'` 选择安全分支。
# - 输入：条件表达式及此前已经规范化的局部变量。
# - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
# - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
# - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
# - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

if __name__ == "__main__":
    unittest.main()
