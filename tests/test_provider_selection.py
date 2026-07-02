# 本文件核心功能：验证TASK_023C及TASK_024A修正后的来源优先级和选择门禁。
# - 输入：来自项目配置、离线本地环境、命令行参数或单元测试夹具；不读取未声明的秘密值。
# - 处理：先完成类型和值域校验，再执行离线发现、排序、报告生成或断言；默认不联网、不交易、不写数据库。
# - 输出：强类型对象、UTF-8 JSON报告、稳定退出码或可重复测试结果，供下一任务和Git门禁使用。
# - 常量依据：任务号、来源层级、安全计数器和状态值来自TASK_022至TASK_024权威文件与官方接口基线。
# - 为什么这样写：教学式前置说明让维护者先理解边界再阅读实现，也防止第三方聚合源或交易能力被误升为主链。

# 本测试文件核心功能：验证TASK_023C已纠正为官方交易所基准、券商优先、聚合源不作为主源。
"""TASK_023C Provider选择回归测试。"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from a_stock_quant.provider_selection import (
    ProviderSelectionPolicy,
    ProviderSelectionProfile,
    build_provider_selection_report,
    load_provider_selection_policy,
    load_task_023b_inventory_report,
    select_first_external_provider,
    write_provider_selection_report,
)


# 本段代码核心功能：定义 `ProviderSelectionTests`，组织验证TASK_023C及TASK_024A修正后的来源优先级和选择门禁的独立测试场景。
# - 输入：类实例字段由配置加载器、发现流程或测试夹具显式传入；不从全局状态隐式取值。
# - 处理：使用类型标注、不可变数据类或枚举限制字段形状和允许状态，避免原始字典在系统内扩散。
# - 输出：输出可比较、可序列化或可排序的 `ProviderSelectionTests` 实例，供后续报告和门禁使用。
# - 常量依据：状态名和字段名来自TASK_022至TASK_024任务合同；本定义不新增未经验证的厂商能力。
# - 为什么这样写：先建立稳定合同，再接官方SDK或券商接口，能够降低供应商替换成本并阻止秘密值进入报告。

class ProviderSelectionTests(unittest.TestCase):
    # 本段代码核心功能：定义 `_profile`，提供局部纯函数辅助，统一规范化、查找或匹配规则。
    # - 输入：参数为 `self、provider_id、rank、eligible、local_required、manual_auth、credential、scope、role、primary、supplemental`；路径和外部文本按UTF-8处理，安全开关必须由显式配置提供。
    # - 处理：只执行函数名对应的单一职责；遇到缺字段、非法状态或越界值立即失败，不做静默猜测。
    # - 输出：返回类型为 `ProviderSelectionProfile`；测试函数则通过断言表达通过或失败，不产生生产副作用。
    # - 常量依据：任务号、状态枚举、零网络/零交易计数和候选优先级均来自TASK_022至TASK_024权威任务合同。
    # - 为什么这样写：显式输入输出和失败模式便于教学排查，也让未来官方交易所或券商SDK只需通过薄适配器接入。

    def _profile(
        self,
        provider_id: str,
        *,
        rank: int,
        eligible: bool = True,
        local_required: bool = False,
        manual_auth: bool = False,
        credential: bool = False,
        scope: str = "SEMANTIC_BASELINE_AND_RECONCILIATION",
        role: str = "OFFICIAL_MARKET_INFRASTRUCTURE_BASELINE",
        primary: bool = True,
        supplemental: bool = False,
    ) -> ProviderSelectionProfile:
        return ProviderSelectionProfile(
            provider_id=provider_id,
            strategy_rank=rank,
            pilot_eligible=eligible,
            local_evidence_required=local_required,
            manual_authorization_required=manual_auth,
            credential_required=credential,
            code_license_status="VERIFIED",
            intended_use_scope=scope,
            reuse_path="THIN_ADAPTER",
            planned_capabilities=("CAPABILITY",),
            required_gates_before_runtime=("GATE",),
            known_risks=("RISK",),
            source_role=role,
            primary_source_eligible=primary,
            supplemental_only=supplemental,
        )

    # 本段代码核心功能：定义 `_inventory`，提供局部纯函数辅助，统一规范化、查找或匹配规则。
    # - 输入：参数为 `self、findings`；路径和外部文本按UTF-8处理，安全开关必须由显式配置提供。
    # - 处理：只执行函数名对应的单一职责；遇到缺字段、非法状态或越界值立即失败，不做静默猜测。
    # - 输出：返回类型为 `dict[str, object]`；测试函数则通过断言表达通过或失败，不产生生产副作用。
    # - 常量依据：任务号、状态枚举、零网络/零交易计数和候选优先级均来自TASK_022至TASK_024权威任务合同。
    # - 为什么这样写：显式输入输出和失败模式便于教学排查，也让未来官方交易所或券商SDK只需通过薄适配器接入。

    def _inventory(self, findings: list[dict[str, object]]) -> dict[str, object]:
        return {
            "task_id": "TASK_023B",
            "selection_status": "CANDIDATES_REQUIRE_MANUAL_REVIEW" if findings else "NO_LOCAL_PROVIDER_EVIDENCE",
            "provider_count": 9,
            "findings": findings,
            "vendor_sdk_imports": 0,
            "network_calls": 0,
            "database_write_operations": 0,
            "registry_write_operations": 0,
            "secret_values_recorded": 0,
            "installation_paths_recorded": 0,
            "activation_performed": False,
        }

    # 本段代码核心功能：定义 `test_policy_rejects_network_or_activation_permission`，构造单一可重复场景，断言对应业务合同和安全边界不会回退。
    # - 输入：参数为 `self`；路径和外部文本按UTF-8处理，安全开关必须由显式配置提供。
    # - 处理：只执行函数名对应的单一职责；遇到缺字段、非法状态或越界值立即失败，不做静默猜测。
    # - 输出：返回类型为 `None`；测试函数则通过断言表达通过或失败，不产生生产副作用。
    # - 常量依据：任务号、状态枚举、零网络/零交易计数和候选优先级均来自TASK_022至TASK_024权威任务合同。
    # - 为什么这样写：显式输入输出和失败模式便于教学排查，也让未来官方交易所或券商SDK只需通过薄适配器接入。

    def test_policy_rejects_network_or_activation_permission(self) -> None:
        # 本段代码核心功能：在受控上下文中打开临时资源并保证离开代码块时自动释放。
        # - 输入：临时目录、文件句柄或补丁上下文。
        # - 处理：上下文管理器负责建立和清理资源，业务代码只处理块内对象。
        # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
        # - 为什么这样写：自动清理可以防止测试污染、文件句柄泄漏和跨任务状态残留。

        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "policy.json"
            path.write_text(
                json.dumps(
                    {
                        "task_id": "TASK_023C",
                        "default_provider_when_no_local_evidence": "official_exchange_sources",
                        "activation_allowed": False,
                        "network_calls_allowed": True,
                        "vendor_sdk_import_allowed": False,
                        "secret_values_allowed": False,
                        "execution_provider_selection_allowed": False,
                        "candidate_profiles": [],
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
                load_provider_selection_policy(path)

    # 本段代码核心功能：定义 `test_inventory_rejects_nonzero_safety_counter`，构造单一可重复场景，断言对应业务合同和安全边界不会回退。
    # - 输入：参数为 `self`；路径和外部文本按UTF-8处理，安全开关必须由显式配置提供。
    # - 处理：只执行函数名对应的单一职责；遇到缺字段、非法状态或越界值立即失败，不做静默猜测。
    # - 输出：返回类型为 `None`；测试函数则通过断言表达通过或失败，不产生生产副作用。
    # - 常量依据：任务号、状态枚举、零网络/零交易计数和候选优先级均来自TASK_022至TASK_024权威任务合同。
    # - 为什么这样写：显式输入输出和失败模式便于教学排查，也让未来官方交易所或券商SDK只需通过薄适配器接入。

    def test_inventory_rejects_nonzero_safety_counter(self) -> None:
        report = self._inventory([])
        report["network_calls"] = 1
        # 本段代码核心功能：在受控上下文中打开临时资源并保证离开代码块时自动释放。
        # - 输入：临时目录、文件句柄或补丁上下文。
        # - 处理：上下文管理器负责建立和清理资源，业务代码只处理块内对象。
        # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
        # - 为什么这样写：自动清理可以防止测试污染、文件句柄泄漏和跨任务状态残留。

        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "inventory.json"
            path.write_text(json.dumps(report), encoding="utf-8")
            # 本段代码核心功能：在受控上下文中打开临时资源并保证离开代码块时自动释放。
            # - 输入：临时目录、文件句柄或补丁上下文。
            # - 处理：上下文管理器负责建立和清理资源，业务代码只处理块内对象。
            # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
            # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
            # - 为什么这样写：自动清理可以防止测试污染、文件句柄泄漏和跨任务状态残留。

            with self.assertRaisesRegex(ValueError, "network_calls"):
                load_task_023b_inventory_report(path)

    # 本段代码核心功能：定义 `test_no_local_evidence_selects_official_exchange_baseline`，构造单一可重复场景，断言对应业务合同和安全边界不会回退。
    # - 输入：参数为 `self`；路径和外部文本按UTF-8处理，安全开关必须由显式配置提供。
    # - 处理：只执行函数名对应的单一职责；遇到缺字段、非法状态或越界值立即失败，不做静默猜测。
    # - 输出：返回类型为 `None`；测试函数则通过断言表达通过或失败，不产生生产副作用。
    # - 常量依据：任务号、状态枚举、零网络/零交易计数和候选优先级均来自TASK_022至TASK_024权威任务合同。
    # - 为什么这样写：显式输入输出和失败模式便于教学排查，也让未来官方交易所或券商SDK只需通过薄适配器接入。

    def test_no_local_evidence_selects_official_exchange_baseline(self) -> None:
        policy = ProviderSelectionPolicy(
            "official_exchange_sources",
            (
                self._profile("official_exchange_sources", rank=0),
                self._profile(
                    "akshare",
                    rank=80,
                    eligible=False,
                    primary=False,
                    supplemental=True,
                    role="THIRD_PARTY_AGGREGATOR_SUPPLEMENTAL",
                ),
            ),
        )
        decision = select_first_external_provider(policy, self._inventory([]))
        self.assertEqual(decision.selected_provider_id, "official_exchange_sources")
        self.assertEqual(
            decision.decision_status,
            "OFFICIAL_BASELINE_SELECTED_ACCESS_CHANNEL_PENDING",
        )
        self.assertEqual(
            decision.selection_basis,
            "OFFICIAL_MARKET_INFRASTRUCTURE_SEMANTIC_BASELINE",
        )

    # 本段代码核心功能：定义 `test_local_official_broker_evidence_is_preferred_for_access_review`，构造单一可重复场景，断言对应业务合同和安全边界不会回退。
    # - 输入：参数为 `self`；路径和外部文本按UTF-8处理，安全开关必须由显式配置提供。
    # - 处理：只执行函数名对应的单一职责；遇到缺字段、非法状态或越界值立即失败，不做静默猜测。
    # - 输出：返回类型为 `None`；测试函数则通过断言表达通过或失败，不产生生产副作用。
    # - 常量依据：任务号、状态枚举、零网络/零交易计数和候选优先级均来自TASK_022至TASK_024权威任务合同。
    # - 为什么这样写：显式输入输出和失败模式便于教学排查，也让未来官方交易所或券商SDK只需通过薄适配器接入。

    def test_local_official_broker_evidence_is_preferred_for_access_review(self) -> None:
        policy = ProviderSelectionPolicy(
            "official_exchange_sources",
            (
                self._profile("official_exchange_sources", rank=0),
                self._profile(
                    "galaxy_xingyao",
                    rank=10,
                    local_required=True,
                    manual_auth=True,
                    role="AUTHORIZED_BROKER_OFFICIAL_ACCESS",
                    scope="AUTHORIZED_READ_ONLY_MARKET_AND_REFERENCE_DATA",
                ),
            ),
        )
        inventory = self._inventory(
            [
                {
                    "provider_id": "galaxy_xingyao",
                    "evidence_score": 140,
                    "eligible_for_task_023c_review": True,
                }
            ]
        )
        decision = select_first_external_provider(policy, inventory)
        self.assertEqual(decision.selected_provider_id, "galaxy_xingyao")
        self.assertEqual(
            decision.decision_status,
            "SELECTED_FOR_OFFICIAL_BROKER_AUTHORIZATION_REVIEW",
        )
        self.assertEqual(decision.activation_status, "NOT_ACTIVATED")
        self.assertIn(
            "MANUAL_AUTHORIZATION_APPROVAL_REQUIRED",
            decision.required_gates_before_runtime,
        )

    # 本段代码核心功能：定义 `test_akshare_local_evidence_cannot_make_it_primary`，构造单一可重复场景，断言对应业务合同和安全边界不会回退。
    # - 输入：参数为 `self`；路径和外部文本按UTF-8处理，安全开关必须由显式配置提供。
    # - 处理：只执行函数名对应的单一职责；遇到缺字段、非法状态或越界值立即失败，不做静默猜测。
    # - 输出：返回类型为 `None`；测试函数则通过断言表达通过或失败，不产生生产副作用。
    # - 常量依据：任务号、状态枚举、零网络/零交易计数和候选优先级均来自TASK_022至TASK_024权威任务合同。
    # - 为什么这样写：显式输入输出和失败模式便于教学排查，也让未来官方交易所或券商SDK只需通过薄适配器接入。

    def test_akshare_local_evidence_cannot_make_it_primary(self) -> None:
        policy = ProviderSelectionPolicy(
            "official_exchange_sources",
            (
                self._profile("official_exchange_sources", rank=0),
                self._profile(
                    "akshare",
                    rank=1,
                    eligible=False,
                    primary=False,
                    supplemental=True,
                    role="THIRD_PARTY_AGGREGATOR_SUPPLEMENTAL",
                ),
            ),
        )
        inventory = self._inventory(
            [
                {
                    "provider_id": "akshare",
                    "evidence_score": 200,
                    "eligible_for_task_023c_review": True,
                }
            ]
        )
        decision = select_first_external_provider(policy, inventory)
        self.assertEqual(decision.selected_provider_id, "official_exchange_sources")

    # 本段代码核心功能：定义 `test_supplemental_profile_cannot_be_primary_in_policy`，构造单一可重复场景，断言对应业务合同和安全边界不会回退。
    # - 输入：参数为 `self`；路径和外部文本按UTF-8处理，安全开关必须由显式配置提供。
    # - 处理：只执行函数名对应的单一职责；遇到缺字段、非法状态或越界值立即失败，不做静默猜测。
    # - 输出：返回类型为 `None`；测试函数则通过断言表达通过或失败，不产生生产副作用。
    # - 常量依据：任务号、状态枚举、零网络/零交易计数和候选优先级均来自TASK_022至TASK_024权威任务合同。
    # - 为什么这样写：显式输入输出和失败模式便于教学排查，也让未来官方交易所或券商SDK只需通过薄适配器接入。

    def test_supplemental_profile_cannot_be_primary_in_policy(self) -> None:
        payload = {
            "task_id": "TASK_023C",
            "default_provider_when_no_local_evidence": "akshare",
            "activation_allowed": False,
            "network_calls_allowed": False,
            "vendor_sdk_import_allowed": False,
            "secret_values_allowed": False,
            "execution_provider_selection_allowed": False,
            "candidate_profiles": [
                {
                    "provider_id": "akshare",
                    "strategy_rank": 1,
                    "pilot_eligible": True,
                    "primary_source_eligible": True,
                    "supplemental_only": True,
                    "source_role": "THIRD_PARTY_AGGREGATOR_SUPPLEMENTAL",
                    "planned_capabilities": [],
                    "required_gates_before_runtime": [],
                    "known_risks": []
                }
            ],
        }
        # 本段代码核心功能：在受控上下文中打开临时资源并保证离开代码块时自动释放。
        # - 输入：临时目录、文件句柄或补丁上下文。
        # - 处理：上下文管理器负责建立和清理资源，业务代码只处理块内对象。
        # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
        # - 为什么这样写：自动清理可以防止测试污染、文件句柄泄漏和跨任务状态残留。

        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "policy.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            # 本段代码核心功能：在受控上下文中打开临时资源并保证离开代码块时自动释放。
            # - 输入：临时目录、文件句柄或补丁上下文。
            # - 处理：上下文管理器负责建立和清理资源，业务代码只处理块内对象。
            # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
            # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
            # - 为什么这样写：自动清理可以防止测试污染、文件句柄泄漏和跨任务状态残留。

            with self.assertRaisesRegex(ValueError, "supplemental provider cannot be primary"):
                load_provider_selection_policy(path)

    # 本段代码核心功能：定义 `test_execution_domain_is_excluded`，构造单一可重复场景，断言对应业务合同和安全边界不会回退。
    # - 输入：参数为 `self`；路径和外部文本按UTF-8处理，安全开关必须由显式配置提供。
    # - 处理：只执行函数名对应的单一职责；遇到缺字段、非法状态或越界值立即失败，不做静默猜测。
    # - 输出：返回类型为 `None`；测试函数则通过断言表达通过或失败，不产生生产副作用。
    # - 常量依据：任务号、状态枚举、零网络/零交易计数和候选优先级均来自TASK_022至TASK_024权威任务合同。
    # - 为什么这样写：显式输入输出和失败模式便于教学排查，也让未来官方交易所或券商SDK只需通过薄适配器接入。

    def test_execution_domain_is_excluded(self) -> None:
        policy = ProviderSelectionPolicy(
            "official_exchange_sources",
            (
                self._profile("official_exchange_sources", rank=0),
                self._profile(
                    "qmt",
                    rank=1,
                    eligible=True,
                    primary=False,
                    scope="SEPARATE_EXECUTION_DOMAIN",
                    role="BROKER_EXECUTION_DOMAIN",
                ),
            ),
        )
        inventory = self._inventory(
            [
                {
                    "provider_id": "qmt",
                    "evidence_score": 200,
                    "eligible_for_task_023c_review": True,
                }
            ]
        )
        decision = select_first_external_provider(policy, inventory)
        self.assertEqual(decision.selected_provider_id, "official_exchange_sources")
        self.assertEqual(decision.activation_status, "NOT_ACTIVATED")

    # 本段代码核心功能：定义 `test_report_has_zero_runtime_operations`，构造单一可重复场景，断言对应业务合同和安全边界不会回退。
    # - 输入：参数为 `self`；路径和外部文本按UTF-8处理，安全开关必须由显式配置提供。
    # - 处理：只执行函数名对应的单一职责；遇到缺字段、非法状态或越界值立即失败，不做静默猜测。
    # - 输出：返回类型为 `None`；测试函数则通过断言表达通过或失败，不产生生产副作用。
    # - 常量依据：任务号、状态枚举、零网络/零交易计数和候选优先级均来自TASK_022至TASK_024权威任务合同。
    # - 为什么这样写：显式输入输出和失败模式便于教学排查，也让未来官方交易所或券商SDK只需通过薄适配器接入。

    def test_report_has_zero_runtime_operations(self) -> None:
        policy = ProviderSelectionPolicy(
            "official_exchange_sources",
            (self._profile("official_exchange_sources", rank=0),),
        )
        inventory = self._inventory([])
        decision = select_first_external_provider(policy, inventory)
        report = build_provider_selection_report(decision, inventory)
        self.assertTrue(report["third_party_primary_source_forbidden"])
        # 本段代码核心功能：逐项遍历 `('vendor_sdk_imports', 'network_calls', 'database_write_operations', 'registry_w` 并处理 `field`。
        # - 输入：有限配置条目、发现证据或测试样本序列。
        # - 处理：每次循环只更新当前条目的局部结果，最终按稳定顺序汇总。
        # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
        # - 为什么这样写：逐项处理能保留来源级证据，避免聚合后无法追溯单个Provider。

        for field in (
            "vendor_sdk_imports",
            "network_calls",
            "database_write_operations",
            "registry_write_operations",
            "secret_values_recorded",
            "installation_paths_recorded",
            "provider_activation_operations",
        ):
            self.assertEqual(report[field], 0)

    # 本段代码核心功能：定义 `test_utf8_report_round_trip`，构造单一可重复场景，断言对应业务合同和安全边界不会回退。
    # - 输入：参数为 `self`；路径和外部文本按UTF-8处理，安全开关必须由显式配置提供。
    # - 处理：只执行函数名对应的单一职责；遇到缺字段、非法状态或越界值立即失败，不做静默猜测。
    # - 输出：返回类型为 `None`；测试函数则通过断言表达通过或失败，不产生生产副作用。
    # - 常量依据：任务号、状态枚举、零网络/零交易计数和候选优先级均来自TASK_022至TASK_024权威任务合同。
    # - 为什么这样写：显式输入输出和失败模式便于教学排查，也让未来官方交易所或券商SDK只需通过薄适配器接入。

    def test_utf8_report_round_trip(self) -> None:
        policy = ProviderSelectionPolicy(
            "official_exchange_sources",
            (self._profile("official_exchange_sources", rank=0),),
        )
        inventory = self._inventory([])
        report = build_provider_selection_report(
            select_first_external_provider(policy, inventory), inventory
        )
        report["note"] = "官方交易所为语义基准，券商官方接口为优先接入通道"
        # 本段代码核心功能：在受控上下文中打开临时资源并保证离开代码块时自动释放。
        # - 输入：临时目录、文件句柄或补丁上下文。
        # - 处理：上下文管理器负责建立和清理资源，业务代码只处理块内对象。
        # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
        # - 为什么这样写：自动清理可以防止测试污染、文件句柄泄漏和跨任务状态残留。

        with tempfile.TemporaryDirectory() as temp_dir:
            path = write_provider_selection_report(report, Path(temp_dir) / "report.json")
            loaded = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(
            loaded["note"],
            "官方交易所为语义基准，券商官方接口为优先接入通道",
        )


# 本段代码核心功能：根据条件 `__name__ == '__main__'` 选择安全分支。
# - 输入：条件表达式及此前已经规范化的局部变量。
# - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
# - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
# - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
# - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

if __name__ == "__main__":
    unittest.main()
