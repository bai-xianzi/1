# 本文件核心功能：验证TASK_024A官方来源权威分层、爬取阻断和只读边界。
# - 输入：来自项目配置、离线本地环境、命令行参数或单元测试夹具；不读取未声明的秘密值。
# - 处理：先完成类型和值域校验，再执行离线发现、排序、报告生成或断言；默认不联网、不交易、不写数据库。
# - 输出：强类型对象、UTF-8 JSON报告、稳定退出码或可重复测试结果，供下一任务和Git门禁使用。
# - 常量依据：任务号、来源层级、安全计数器和状态值来自TASK_022至TASK_024权威文件与官方接口基线。
# - 为什么这样写：教学式前置说明让维护者先理解边界再阅读实现，也防止第三方聚合源或交易能力被误升为主链。

# 本测试文件核心功能：验证官方交易所语义基准、券商优先接入、聚合源降级和爬虫阻断。
"""TASK_024A来源权威门禁测试。"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from a_stock_quant.source_authority import (
    AuthorityTier,
    OfficialInterfaceEntry,
    SourceAuthorityPolicy,
    build_source_authority_report,
    load_official_interface_catalog,
    load_source_authority_policy,
    rank_practical_access_candidates,
    rank_semantic_baselines,
    validate_source_authority_contract,
    write_source_authority_report,
)


ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "configs/providers/source_authority_policy_v1.json"
CATALOG_PATH = ROOT / "configs/providers/official_interface_catalog_v1.json"


# 本段代码核心功能：定义 `SourceAuthorityTests`，组织验证TASK_024A官方来源权威分层、爬取阻断和只读边界的独立测试场景。
# - 输入：类实例字段由配置加载器、发现流程或测试夹具显式传入；不从全局状态隐式取值。
# - 处理：使用类型标注、不可变数据类或枚举限制字段形状和允许状态，避免原始字典在系统内扩散。
# - 输出：输出可比较、可序列化或可排序的 `SourceAuthorityTests` 实例，供后续报告和门禁使用。
# - 常量依据：状态名和字段名来自TASK_022至TASK_024任务合同；本定义不新增未经验证的厂商能力。
# - 为什么这样写：先建立稳定合同，再接官方SDK或券商接口，能够降低供应商替换成本并阻止秘密值进入报告。

class SourceAuthorityTests(unittest.TestCase):
    # 本段代码核心功能：定义 `setUp`，为每个测试方法加载独立且可重复使用的配置夹具。
    # - 输入：参数为 `self`；路径和外部文本按UTF-8处理，安全开关必须由显式配置提供。
    # - 处理：只执行函数名对应的单一职责；遇到缺字段、非法状态或越界值立即失败，不做静默猜测。
    # - 输出：返回类型为 `None`；测试函数则通过断言表达通过或失败，不产生生产副作用。
    # - 常量依据：任务号、状态枚举、零网络/零交易计数和候选优先级均来自TASK_022至TASK_024权威任务合同。
    # - 为什么这样写：显式输入输出和失败模式便于教学排查，也让未来官方交易所或券商SDK只需通过薄适配器接入。

    def setUp(self) -> None:
        self.policy = load_source_authority_policy(POLICY_PATH)
        self.entries = load_official_interface_catalog(CATALOG_PATH)

    # 本段代码核心功能：定义 `test_official_market_infrastructure_is_first_semantic_authority`，构造单一可重复场景，断言对应业务合同和安全边界不会回退。
    # - 输入：参数为 `self`；路径和外部文本按UTF-8处理，安全开关必须由显式配置提供。
    # - 处理：只执行函数名对应的单一职责；遇到缺字段、非法状态或越界值立即失败，不做静默猜测。
    # - 输出：返回类型为 `None`；测试函数则通过断言表达通过或失败，不产生生产副作用。
    # - 常量依据：任务号、状态枚举、零网络/零交易计数和候选优先级均来自TASK_022至TASK_024权威任务合同。
    # - 为什么这样写：显式输入输出和失败模式便于教学排查，也让未来官方交易所或券商SDK只需通过薄适配器接入。

    def test_official_market_infrastructure_is_first_semantic_authority(self) -> None:
        self.assertEqual(
            self.policy.semantic_authority_order[0],
            "T0_OFFICIAL_MARKET_INFRASTRUCTURE",
        )
        ranked = rank_semantic_baselines(self.policy, self.entries)
        self.assertTrue(ranked)
        self.assertTrue(all(entry.semantic_baseline for entry in ranked))
        self.assertEqual(
            {entry.source_id for entry in ranked},
            {"sse", "szse", "bse", "hkex_omdc", "chinaclear"},
        )

    # 本段代码核心功能：定义 `test_authorized_broker_is_first_practical_access_channel`，构造单一可重复场景，断言对应业务合同和安全边界不会回退。
    # - 输入：参数为 `self`；路径和外部文本按UTF-8处理，安全开关必须由显式配置提供。
    # - 处理：只执行函数名对应的单一职责；遇到缺字段、非法状态或越界值立即失败，不做静默猜测。
    # - 输出：返回类型为 `None`；测试函数则通过断言表达通过或失败，不产生生产副作用。
    # - 常量依据：任务号、状态枚举、零网络/零交易计数和候选优先级均来自TASK_022至TASK_024权威任务合同。
    # - 为什么这样写：显式输入输出和失败模式便于教学排查，也让未来官方交易所或券商SDK只需通过薄适配器接入。

    def test_authorized_broker_is_first_practical_access_channel(self) -> None:
        self.assertEqual(
            self.policy.practical_access_order[0],
            "T1_AUTHORIZED_BROKER_OFFICIAL",
        )
        ranked = rank_practical_access_candidates(self.policy, self.entries)
        self.assertTrue(ranked)
        first_tier_ids = {entry.tier_id for entry in ranked[:4]}
        self.assertEqual(first_tier_ids, {"T1_AUTHORIZED_BROKER_OFFICIAL"})

    # 本段代码核心功能：定义 `test_catalog_contains_verified_exchange_and_clearing_baseline`，构造单一可重复场景，断言对应业务合同和安全边界不会回退。
    # - 输入：参数为 `self`；路径和外部文本按UTF-8处理，安全开关必须由显式配置提供。
    # - 处理：只执行函数名对应的单一职责；遇到缺字段、非法状态或越界值立即失败，不做静默猜测。
    # - 输出：返回类型为 `None`；测试函数则通过断言表达通过或失败，不产生生产副作用。
    # - 常量依据：任务号、状态枚举、零网络/零交易计数和候选优先级均来自TASK_022至TASK_024权威任务合同。
    # - 为什么这样写：显式输入输出和失败模式便于教学排查，也让未来官方交易所或券商SDK只需通过薄适配器接入。

    def test_catalog_contains_verified_exchange_and_clearing_baseline(self) -> None:
        source_ids = {entry.source_id for entry in self.entries}
        # 本段代码核心功能：逐项遍历 `('sse', 'szse', 'bse', 'hkex_omdc', 'chinaclear')` 并处理 `source_id`。
        # - 输入：有限配置条目、发现证据或测试样本序列。
        # - 处理：每次循环只更新当前条目的局部结果，最终按稳定顺序汇总。
        # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
        # - 为什么这样写：逐项处理能保留来源级证据，避免聚合后无法追溯单个Provider。

        for source_id in ("sse", "szse", "bse", "hkex_omdc", "chinaclear"):
            self.assertIn(source_id, source_ids)

    # 本段代码核心功能：定义 `test_catalog_contains_official_broker_candidates`，构造单一可重复场景，断言对应业务合同和安全边界不会回退。
    # - 输入：参数为 `self`；路径和外部文本按UTF-8处理，安全开关必须由显式配置提供。
    # - 处理：只执行函数名对应的单一职责；遇到缺字段、非法状态或越界值立即失败，不做静默猜测。
    # - 输出：返回类型为 `None`；测试函数则通过断言表达通过或失败，不产生生产副作用。
    # - 常量依据：任务号、状态枚举、零网络/零交易计数和候选优先级均来自TASK_022至TASK_024权威任务合同。
    # - 为什么这样写：显式输入输出和失败模式便于教学排查，也让未来官方交易所或券商SDK只需通过薄适配器接入。

    def test_catalog_contains_official_broker_candidates(self) -> None:
        source_ids = {entry.source_id for entry in self.entries}
        # 本段代码核心功能：逐项遍历 `('galaxy_xingyao_tfast', 'zhongtai_xtp', 'guosen_iquant', 'gf_touyitong')` 并处理 `source_id`。
        # - 输入：有限配置条目、发现证据或测试样本序列。
        # - 处理：每次循环只更新当前条目的局部结果，最终按稳定顺序汇总。
        # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
        # - 为什么这样写：逐项处理能保留来源级证据，避免聚合后无法追溯单个Provider。

        for source_id in (
            "galaxy_xingyao_tfast",
            "zhongtai_xtp",
            "guosen_iquant",
            "gf_touyitong",
        ):
            self.assertIn(source_id, source_ids)

    # 本段代码核心功能：定义 `test_third_party_aggregators_are_never_primary`，构造单一可重复场景，断言对应业务合同和安全边界不会回退。
    # - 输入：参数为 `self`；路径和外部文本按UTF-8处理，安全开关必须由显式配置提供。
    # - 处理：只执行函数名对应的单一职责；遇到缺字段、非法状态或越界值立即失败，不做静默猜测。
    # - 输出：返回类型为 `None`；测试函数则通过断言表达通过或失败，不产生生产副作用。
    # - 常量依据：任务号、状态枚举、零网络/零交易计数和候选优先级均来自TASK_022至TASK_024权威任务合同。
    # - 为什么这样写：显式输入输出和失败模式便于教学排查，也让未来官方交易所或券商SDK只需通过薄适配器接入。

    def test_third_party_aggregators_are_never_primary(self) -> None:
        third_party = [
            entry
            for entry in self.entries
            if entry.tier_id == "T3_THIRD_PARTY_AGGREGATOR_SUPPLEMENTAL"
        ]
        self.assertEqual({entry.source_id for entry in third_party}, {"akshare", "tushare_pro"})
        self.assertTrue(all(not entry.semantic_baseline for entry in third_party))
        self.assertTrue(all(not entry.read_only_scope_allowed_for_review for entry in third_party))
        ranked_ids = {
            entry.source_id
            for entry in rank_practical_access_candidates(self.policy, self.entries)
        }
        self.assertNotIn("akshare", ranked_ids)
        self.assertNotIn("tushare_pro", ranked_ids)

    # 本段代码核心功能：定义 `test_unverified_scraping_is_blocked_by_policy`，构造单一可重复场景，断言对应业务合同和安全边界不会回退。
    # - 输入：参数为 `self`；路径和外部文本按UTF-8处理，安全开关必须由显式配置提供。
    # - 处理：只执行函数名对应的单一职责；遇到缺字段、非法状态或越界值立即失败，不做静默猜测。
    # - 输出：返回类型为 `None`；测试函数则通过断言表达通过或失败，不产生生产副作用。
    # - 常量依据：任务号、状态枚举、零网络/零交易计数和候选优先级均来自TASK_022至TASK_024权威任务合同。
    # - 为什么这样写：显式输入输出和失败模式便于教学排查，也让未来官方交易所或券商SDK只需通过薄适配器接入。

    def test_unverified_scraping_is_blocked_by_policy(self) -> None:
        blocked_tier = next(
            tier
            for tier in self.policy.tiers
            if tier.tier_id == "T4_UNVERIFIED_SCRAPE_BLOCKED"
        )
        self.assertFalse(blocked_tier.primary_source_eligible)
        self.assertEqual(blocked_tier.allowed_roles, ())
        self.assertTrue(
            self.policy.rules["unverified_scraping_core_pipeline_forbidden"]
        )

    # 本段代码核心功能：定义 `test_trading_capable_brokers_remain_read_only_review_only`，构造单一可重复场景，断言对应业务合同和安全边界不会回退。
    # - 输入：参数为 `self`；路径和外部文本按UTF-8处理，安全开关必须由显式配置提供。
    # - 处理：只执行函数名对应的单一职责；遇到缺字段、非法状态或越界值立即失败，不做静默猜测。
    # - 输出：返回类型为 `None`；测试函数则通过断言表达通过或失败，不产生生产副作用。
    # - 常量依据：任务号、状态枚举、零网络/零交易计数和候选优先级均来自TASK_022至TASK_024权威任务合同。
    # - 为什么这样写：显式输入输出和失败模式便于教学排查，也让未来官方交易所或券商SDK只需通过薄适配器接入。

    def test_trading_capable_brokers_remain_read_only_review_only(self) -> None:
        brokers = [
            entry
            for entry in self.entries
            if entry.tier_id == "T1_AUTHORIZED_BROKER_OFFICIAL"
        ]
        self.assertTrue(any(entry.execution_capability for entry in brokers))
        self.assertTrue(
            all(entry.read_only_scope_allowed_for_review for entry in brokers)
        )
        report = build_source_authority_report(self.policy, self.entries)
        self.assertFalse(report["execution_activation_allowed"])
        self.assertEqual(report["execution_activation_operations"], 0)

    # 本段代码核心功能：定义 `test_contract_validation_passes_for_shipped_catalog`，构造单一可重复场景，断言对应业务合同和安全边界不会回退。
    # - 输入：参数为 `self`；路径和外部文本按UTF-8处理，安全开关必须由显式配置提供。
    # - 处理：只执行函数名对应的单一职责；遇到缺字段、非法状态或越界值立即失败，不做静默猜测。
    # - 输出：返回类型为 `None`；测试函数则通过断言表达通过或失败，不产生生产副作用。
    # - 常量依据：任务号、状态枚举、零网络/零交易计数和候选优先级均来自TASK_022至TASK_024权威任务合同。
    # - 为什么这样写：显式输入输出和失败模式便于教学排查，也让未来官方交易所或券商SDK只需通过薄适配器接入。

    def test_contract_validation_passes_for_shipped_catalog(self) -> None:
        self.assertEqual(validate_source_authority_contract(self.policy, self.entries), ())

    # 本段代码核心功能：定义 `test_contract_rejects_aggregator_promoted_to_primary`，构造单一可重复场景，断言对应业务合同和安全边界不会回退。
    # - 输入：参数为 `self`；路径和外部文本按UTF-8处理，安全开关必须由显式配置提供。
    # - 处理：只执行函数名对应的单一职责；遇到缺字段、非法状态或越界值立即失败，不做静默猜测。
    # - 输出：返回类型为 `None`；测试函数则通过断言表达通过或失败，不产生生产副作用。
    # - 常量依据：任务号、状态枚举、零网络/零交易计数和候选优先级均来自TASK_022至TASK_024权威任务合同。
    # - 为什么这样写：显式输入输出和失败模式便于教学排查，也让未来官方交易所或券商SDK只需通过薄适配器接入。

    def test_contract_rejects_aggregator_promoted_to_primary(self) -> None:
        bad_entry = OfficialInterfaceEntry(
            source_id="bad_aggregator",
            display_name="Bad Aggregator",
            tier_id="T3_THIRD_PARTY_AGGREGATOR_SUPPLEMENTAL",
            domain_class="THIRD_PARTY_PROJECT",
            official_domains=("example.invalid",),
            evidence_status="UNVERIFIED",
            interface_families=("SCRAPE",),
            semantic_baseline=True,
            direct_personal_access_expected=True,
            authorization_or_membership_required=False,
            execution_capability=False,
            read_only_scope_allowed_for_review=True,
            notes="invalid test record",
        )
        errors = validate_source_authority_contract(
            self.policy, (*self.entries, bad_entry)
        )
        self.assertTrue(any("third-party aggregator cannot be primary" in item for item in errors))

    # 本段代码核心功能：定义 `test_policy_rejects_network_permission`，构造单一可重复场景，断言对应业务合同和安全边界不会回退。
    # - 输入：参数为 `self`；路径和外部文本按UTF-8处理，安全开关必须由显式配置提供。
    # - 处理：只执行函数名对应的单一职责；遇到缺字段、非法状态或越界值立即失败，不做静默猜测。
    # - 输出：返回类型为 `None`；测试函数则通过断言表达通过或失败，不产生生产副作用。
    # - 常量依据：任务号、状态枚举、零网络/零交易计数和候选优先级均来自TASK_022至TASK_024权威任务合同。
    # - 为什么这样写：显式输入输出和失败模式便于教学排查，也让未来官方交易所或券商SDK只需通过薄适配器接入。

    def test_policy_rejects_network_permission(self) -> None:
        payload = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
        payload["network_calls_allowed"] = True
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

            with self.assertRaisesRegex(ValueError, "network_calls_allowed"):
                load_source_authority_policy(path)

    # 本段代码核心功能：定义 `test_report_has_zero_external_operations_and_utf8_round_trip`，构造单一可重复场景，断言对应业务合同和安全边界不会回退。
    # - 输入：参数为 `self`；路径和外部文本按UTF-8处理，安全开关必须由显式配置提供。
    # - 处理：只执行函数名对应的单一职责；遇到缺字段、非法状态或越界值立即失败，不做静默猜测。
    # - 输出：返回类型为 `None`；测试函数则通过断言表达通过或失败，不产生生产副作用。
    # - 常量依据：任务号、状态枚举、零网络/零交易计数和候选优先级均来自TASK_022至TASK_024权威任务合同。
    # - 为什么这样写：显式输入输出和失败模式便于教学排查，也让未来官方交易所或券商SDK只需通过薄适配器接入。

    def test_report_has_zero_external_operations_and_utf8_round_trip(self) -> None:
        report = build_source_authority_report(self.policy, self.entries)
        self.assertEqual(report["overall_status"], "PASSED")
        self.assertEqual(report["next_task_id"], "TASK_024B")
        # 本段代码核心功能：逐项遍历 `('vendor_sdk_imports', 'network_calls', 'database_write_operations', 'registry_w` 并处理 `field_name`。
        # - 输入：有限配置条目、发现证据或测试样本序列。
        # - 处理：每次循环只更新当前条目的局部结果，最终按稳定顺序汇总。
        # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
        # - 为什么这样写：逐项处理能保留来源级证据，避免聚合后无法追溯单个Provider。

        for field_name in (
            "vendor_sdk_imports",
            "network_calls",
            "database_write_operations",
            "registry_write_operations",
            "secret_values_recorded",
            "provider_activation_operations",
            "execution_activation_operations",
        ):
            self.assertEqual(report[field_name], 0)
        report["note"] = "官方交易所为语义基准，授权券商为优先接入通道"
        # 本段代码核心功能：在受控上下文中打开临时资源并保证离开代码块时自动释放。
        # - 输入：临时目录、文件句柄或补丁上下文。
        # - 处理：上下文管理器负责建立和清理资源，业务代码只处理块内对象。
        # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
        # - 为什么这样写：自动清理可以防止测试污染、文件句柄泄漏和跨任务状态残留。

        with tempfile.TemporaryDirectory() as temp_dir:
            path = write_source_authority_report(
                report, Path(temp_dir) / "report.json"
            )
            loaded = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(
            loaded["note"],
            "官方交易所为语义基准，授权券商为优先接入通道",
        )


# 本段代码核心功能：根据条件 `__name__ == '__main__'` 选择安全分支。
# - 输入：条件表达式及此前已经规范化的局部变量。
# - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
# - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
# - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
# - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

if __name__ == "__main__":
    unittest.main()
