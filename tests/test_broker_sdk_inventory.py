# 本文件核心功能：验证TASK_024B券商SDK盘点的授权门禁、证据扫描、隐私边界和候选排序。
# - 输入：临时规则、授权JSON、专用证据目录和TASK_023B安全报告夹具。
# - 处理：只调用纯函数和本地临时文件，不联网、不导入券商SDK、不登录、不交易。
# - 输出：全部断言通过时证明无证据、部分证据、完整只读授权和交易域未隔离场景均被正确处理。
# - 常量依据：测试状态和值来自TASK_024B任务合同，候选示例不代表用户真实拥有相应授权。
# - 为什么这样写：先用受控夹具证明安全逻辑，再让Windows本机报告只承担环境证据，不承担业务规则验证。
"""Tests for TASK_024B broker SDK inventory."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from a_stock_quant.broker_sdk_inventory import (
    build_inventory_report,
    evaluate_broker_candidates,
    load_authorization_evidence,
    load_broker_sdk_rules,
    merge_task_023b_evidence,
    scan_evidence_roots,
    write_inventory_report,
)


# 本段代码核心功能：定义 `BrokerSdkInventoryTests`，组织TASK_024B独立安全与行为测试。
# - 输入：每个测试创建自己的临时目录和JSON夹具。
# - 处理：通过unittest生命周期隔离文件状态，不依赖用户电脑或Git仓库外部环境。
# - 输出：七个以上测试场景的确定性通过或失败结果。
# - 常量依据：覆盖配置门禁、秘密字段、专用目录、23B复用、READY准入、交易隔离和UTF-8报告。
# - 为什么这样写：场景级测试能防止以后为了接入某券商而放松全局只读安全边界。
class BrokerSdkInventoryTests(unittest.TestCase):
    """TASK_024B unit tests."""

    # 本段代码核心功能：定义 `setUp`，为每个测试建立隔离目录和最小双券商规则。
    # - 输入：unittest自动调用，无外部参数。
    # - 处理：创建临时目录、规则配置和常用路径。
    # - 输出：在实例上保存root、rules_path和output_path。
    # - 常量依据：测试候选使用galaxy_xingyao与zhongtai_xtp，均保持执行能力不激活。
    # - 为什么这样写：统一夹具减少重复，同时每个测试仍拥有独立文件系统状态。
    def setUp(self) -> None:
        """Create isolated test fixtures."""

        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.rules_path = self.root / "rules.json"
        self.output_path = self.root / "report.json"
        self.rules_path.write_text(
            json.dumps(
                {
                    "network_calls_allowed": False,
                    "vendor_sdk_import_allowed": False,
                    "broker_login_allowed": False,
                    "trade_session_initialization_allowed": False,
                    "order_submission_allowed": False,
                    "secret_values_allowed": False,
                    "whole_drive_scan_allowed": False,
                    "file_content_read_allowed": False,
                    "absolute_paths_recorded": False,
                    "providers": [
                        {
                            "provider_id": "galaxy_xingyao",
                            "display_name": "银河证券星耀数智与TFast",
                            "catalog_source_id": "galaxy_xingyao_tfast",
                            "strategy_rank": 10,
                            "official_domains": ["chinastock.com.cn"],
                            "artifact_name_tokens": ["xingyao", "tfast", "星耀数智"],
                            "allowed_extensions": [".zip", ".pdf"],
                            "read_only_capability_markers": ["STANDARDIZED_FINANCIAL_DATA"],
                            "execution_capability_markers": ["STRATEGY_EXECUTION"],
                            "verified_runtime_notes": ["PUBLIC_SDK_PACKAGE_NOT_VERIFIED"],
                            "official_evidence_status": "OFFICIAL_PRODUCT_PAGE_VERIFIED",
                        },
                        {
                            "provider_id": "zhongtai_xtp",
                            "display_name": "中泰证券XTP",
                            "catalog_source_id": "zhongtai_xtp",
                            "strategy_rank": 20,
                            "official_domains": ["zts.com.cn", "github.com/ztsec"],
                            "artifact_name_tokens": ["xtp_api", "xtp_quote"],
                            "allowed_extensions": [".zip", ".pyd"],
                            "read_only_capability_markers": ["QUOTE_API"],
                            "execution_capability_markers": ["TRADING_API"],
                            "verified_runtime_notes": ["PYTHON_3_9_SERIES_OFFICIAL_BINARY_REFERENCE"],
                            "official_evidence_status": "OFFICIAL_REPOSITORY_VERIFIED",
                        },
                    ],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    # 本段代码核心功能：定义 `tearDown`，删除当前测试创建的全部临时文件。
    # - 输入：unittest自动调用。
    # - 处理：关闭TemporaryDirectory并递归清理目录。
    # - 输出：无持久副作用。
    # - 常量依据：测试不得污染项目目录或用户证据目录。
    # - 为什么这样写：无论测试成功或失败都清理夹具，保持重复运行稳定。
    def tearDown(self) -> None:
        """Clean temporary fixtures."""

        self.temporary_directory.cleanup()

    # 本段代码核心功能：定义 `_write_authorization`，生成单一Provider的非秘密授权夹具。
    # - 输入：provider_id和需要覆盖的布尔或版本字段。
    # - 处理：填充安全默认值并写入UTF-8 JSON。
    # - 输出：授权文件路径。
    # - 常量依据：字段集合严格对应AuthorizationEvidence，不提供密码或连接参数入口。
    # - 为什么这样写：测试辅助函数保持授权状态显式，便于逐场景只修改一个门禁。
    def _write_authorization(self, provider_id: str, **overrides: object) -> Path:
        """Write one safe authorization entry."""

        entry: dict[str, object] = {
            "provider_id": provider_id,
            "official_package_confirmed": False,
            "user_authorization_confirmed": False,
            "read_only_quote_entitlement_confirmed": False,
            "execution_domain_present": False,
            "execution_domain_isolated_confirmed": False,
            "sdk_version": "",
            "client_version": "",
            "documentation_version": "",
        }
        entry.update(overrides)
        path = self.root / "authorization.json"
        path.write_text(
            json.dumps({"providers": [entry]}, ensure_ascii=False),
            encoding="utf-8",
        )
        return path

    # 本段代码核心功能：验证任何安全开关被改为True时规则加载立即失败。
    # - 输入：把network_calls_allowed改为True的规则JSON。
    # - 处理：调用load_broker_sdk_rules并捕获ValueError。
    # - 输出：断言异常消息指向被破坏的安全字段。
    # - 常量依据：网络调用在TASK_024B中绝对禁止。
    # - 为什么这样写：防止配置文件绕过代码默认值开启外部访问。
    def test_rules_reject_unsafe_switches(self) -> None:
        """Unsafe rule switches must fail closed."""

        payload = json.loads(self.rules_path.read_text(encoding="utf-8"))
        payload["network_calls_allowed"] = True
        self.rules_path.write_text(json.dumps(payload), encoding="utf-8")
        # 本段代码核心功能：在受控上下文中使用临时资源并保证离开代码块时自动释放。
        # - 输入：临时目录、文件句柄、补丁上下文或其他上下文管理器。
        # - 处理：上下文管理器负责建立和清理资源，业务代码只处理块内对象。
        # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
        # - 为什么这样写：自动清理可防止测试污染、文件句柄泄漏和跨任务状态残留。

        with self.assertRaisesRegex(ValueError, "network_calls_allowed"):
            load_broker_sdk_rules(self.rules_path)

    # 本段代码核心功能：验证授权文件中的秘密字段即使嵌套也会被拒绝。
    # - 输入：包含token字段的授权JSON。
    # - 处理：调用load_authorization_evidence。
    # - 输出：断言抛出secret-like field错误。
    # - 常量依据：Token不属于非秘密授权事实。
    # - 为什么这样写：确保报告生成前就阻止敏感值进入内存合同。
    def test_authorization_rejects_secret_like_fields(self) -> None:
        """Secret-like fields are forbidden."""

        path = self.root / "unsafe.json"
        path.write_text(
            json.dumps(
                {
                    "providers": [
                        {
                            "provider_id": "zhongtai_xtp",
                            "token": "must-not-be-read",
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        # 本段代码核心功能：在受控上下文中使用临时资源并保证离开代码块时自动释放。
        # - 输入：临时目录、文件句柄、补丁上下文或其他上下文管理器。
        # - 处理：上下文管理器负责建立和清理资源，业务代码只处理块内对象。
        # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
        # - 为什么这样写：自动清理可防止测试污染、文件句柄泄漏和跨任务状态残留。

        with self.assertRaisesRegex(ValueError, "secret-like field"):
            load_authorization_evidence(
                path,
                {"galaxy_xingyao", "zhongtai_xtp"},
            )

    # 本段代码核心功能：验证扫描器只报告命中的SDK文件基名和匿名根标签。
    # - 输入：专用目录中的XTP ZIP、无关TXT和嵌套文件。
    # - 处理：调用scan_evidence_roots。
    # - 输出：断言仅XTP文件被记录，报告证据不含绝对路径。
    # - 常量依据：TASK_024B禁止整盘扫描和绝对路径记录。
    # - 为什么这样写：证明文件系统盘点同时满足可用性与隐私边界。
    def test_scan_records_only_matched_basenames(self) -> None:
        """The scanner records only sanitized matched names."""

        intake = self.root / "intake"
        intake.mkdir()
        (intake / "XTP_API_2.2.50.8.zip").write_bytes(b"not-read")
        (intake / "private_notes.txt").write_text("ignored", encoding="utf-8")
        rules = load_broker_sdk_rules(self.rules_path)
        evidence, scanned_count = scan_evidence_roots(
            rules,
            {"official_intake": intake},
        )
        self.assertEqual(scanned_count, 2)
        xtp = evidence["zhongtai_xtp"]
        self.assertEqual(xtp.matched_artifact_names, ("XTP_API_2.2.50.8.zip",))
        self.assertEqual(xtp.matched_root_labels, ("official_intake",))
        self.assertNotIn(str(intake), json.dumps(xtp.__dict__, ensure_ascii=False))

    # 本段代码核心功能：验证仅有本地文件证据而未确认授权时不会进入适配任务。
    # - 输入：匹配的XTP包和空授权映射。
    # - 处理：扫描并评估候选。
    # - 输出：断言状态要求人工确认且包含三项授权阻断。
    # - 常量依据：文件存在不等于用户拥有合法API权限。
    # - 为什么这样写：防止最常见的“装了客户端就算可接入”误判。
    def test_local_package_without_authorization_is_not_ready(self) -> None:
        """A package alone does not prove authorization."""

        intake = self.root / "intake"
        intake.mkdir()
        (intake / "xtp_quote_api.zip").write_bytes(b"unused")
        rules = load_broker_sdk_rules(self.rules_path)
        evidence, _ = scan_evidence_roots(rules, {"intake": intake})
        findings = evaluate_broker_candidates(rules, evidence, {})
        xtp = next(item for item in findings if item.provider_id == "zhongtai_xtp")
        self.assertFalse(xtp.eligible_for_read_only_adapter_task)
        self.assertEqual(
            xtp.candidate_status,
            "LOCAL_EVIDENCE_REQUIRES_MANUAL_CONFIRMATION",
        )
        self.assertIn("USER_AUTHORIZATION_NOT_CONFIRMED", xtp.blockers)

    # 本段代码核心功能：验证四道门禁齐全且交易域已隔离时生成READY候选。
    # - 输入：XTP官方包证据和完整非秘密授权确认。
    # - 处理：加载授权并评估候选。
    # - 输出：断言XTP为READY且推荐顺序第一。
    # - 常量依据：交易能力存在并不禁止只读试点，但必须明确隔离。
    # - 为什么这样写：证明系统可以在严格安全边界下推进真正的券商薄适配。
    def test_complete_read_only_evidence_becomes_ready(self) -> None:
        """Complete evidence enables a read-only adapter task."""

        intake = self.root / "intake"
        intake.mkdir()
        (intake / "XTP_API_20250806_2.2.50.8.zip").write_bytes(b"unused")
        rules = load_broker_sdk_rules(self.rules_path)
        evidence, _ = scan_evidence_roots(rules, {"intake": intake})
        authorization_path = self._write_authorization(
            "zhongtai_xtp",
            official_package_confirmed=True,
            user_authorization_confirmed=True,
            read_only_quote_entitlement_confirmed=True,
            execution_domain_present=True,
            execution_domain_isolated_confirmed=True,
            sdk_version="2.2.50.8",
            documentation_version="2025-08-06",
        )
        authorization = load_authorization_evidence(
            authorization_path,
            {rule.provider_id for rule in rules},
        )
        findings = evaluate_broker_candidates(rules, evidence, authorization)
        self.assertEqual(findings[0].provider_id, "zhongtai_xtp")
        self.assertTrue(findings[0].eligible_for_read_only_adapter_task)
        self.assertEqual(
            findings[0].candidate_status,
            "READY_FOR_READ_ONLY_ADAPTER_TASK",
        )

    # 本段代码核心功能：验证交易域存在但未确认隔离时即使其他证据齐全仍被阻断。
    # - 输入：完整包、授权和只读权限，但execution_domain_isolated_confirmed为False。
    # - 处理：评估候选。
    # - 输出：断言阻断原因包含EXECUTION_DOMAIN_NOT_ISOLATED。
    # - 常量依据：行情与下单能力必须分离，不能因同一SDK提供Quote就默认安全。
    # - 为什么这样写：把用户当前只需要数据的目标与未来自动交易权限严格隔离。
    def test_execution_domain_must_be_isolated(self) -> None:
        """Execution-capable SDKs require explicit isolation."""

        intake = self.root / "intake"
        intake.mkdir()
        (intake / "XTP_API.zip").write_bytes(b"unused")
        rules = load_broker_sdk_rules(self.rules_path)
        evidence, _ = scan_evidence_roots(rules, {"intake": intake})
        authorization_path = self._write_authorization(
            "zhongtai_xtp",
            official_package_confirmed=True,
            user_authorization_confirmed=True,
            read_only_quote_entitlement_confirmed=True,
            execution_domain_present=True,
            execution_domain_isolated_confirmed=False,
        )
        authorization = load_authorization_evidence(
            authorization_path,
            {rule.provider_id for rule in rules},
        )
        findings = evaluate_broker_candidates(rules, evidence, authorization)
        xtp = next(item for item in findings if item.provider_id == "zhongtai_xtp")
        self.assertFalse(xtp.eligible_for_read_only_adapter_task)
        self.assertIn("EXECUTION_DOMAIN_NOT_ISOLATED", xtp.blockers)

    # 本段代码核心功能：验证TASK_023B脱敏报告的客户端与模块证据能够被安全复用。
    # - 输入：包含galaxy_xingyao命中项的最小23B JSON。
    # - 处理：调用merge_task_023b_evidence。
    # - 输出：断言模块和客户端名称进入对应ArtifactEvidence。
    # - 常量依据：23B报告不包含安装路径和秘密值，因此可作为软证据使用。
    # - 为什么这样写：复用已有盘点结果符合大局观，也避免重复读取Windows注册表。
    def test_task_023b_evidence_is_reused_without_authorization_inference(self) -> None:
        """TASK_023B evidence is merged as soft evidence only."""

        rules = load_broker_sdk_rules(self.rules_path)
        evidence, _ = scan_evidence_roots(rules, {})
        report_path = self.root / "task23b.json"
        report_path.write_text(
            json.dumps(
                {
                    "findings": [
                        {
                            "provider_id": "galaxy_xingyao",
                            "current_interpreter_modules": ["xingyao_sdk"],
                            "other_interpreter_modules": [],
                            "matched_installed_applications": ["银河证券星耀数智"],
                        }
                    ]
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        merged = merge_task_023b_evidence(evidence, report_path)
        galaxy = merged["galaxy_xingyao"]
        self.assertEqual(galaxy.detected_module_names, ("xingyao_sdk",))
        self.assertEqual(
            galaxy.matched_installed_application_names,
            ("银河证券星耀数智",),
        )
        findings = evaluate_broker_candidates(rules, merged, {})
        galaxy_finding = next(
            item for item in findings if item.provider_id == "galaxy_xingyao"
        )
        self.assertFalse(galaxy_finding.eligible_for_read_only_adapter_task)

    # 本段代码核心功能：验证无本地证据时报告成功但保持在TASK_024B证据接收阶段。
    # - 输入：空证据和空授权结果。
    # - 处理：构建并写入报告，再按UTF-8重新解析。
    # - 输出：断言零候选、零副作用计数、正确selection_status和单一末尾换行。
    # - 常量依据：没有券商SDK不是程序错误，也不能自动降级选择AKShare或Tushare。
    # - 为什么这样写：确保真实电脑没有授权包时项目诚实停留，而不是为推进任务选择低权威来源。
    def test_no_evidence_report_is_safe_and_deterministic(self) -> None:
        """No evidence is a warning result, not a false candidate."""

        rules = load_broker_sdk_rules(self.rules_path)
        evidence, scanned_count = scan_evidence_roots(rules, {})
        findings = evaluate_broker_candidates(rules, evidence, {})
        report = build_inventory_report(
            findings,
            scanned_file_count=scanned_count,
            task_023b_report_used=False,
            authorization_file_used=False,
        )
        write_inventory_report(report, self.output_path)
        loaded = json.loads(self.output_path.read_text(encoding="utf-8"))
        self.assertEqual(
            loaded["selection_status"],
            "NO_AUTHORIZED_BROKER_SDK_EVIDENCE",
        )
        self.assertEqual(loaded["ready_candidate_count"], 0)
        self.assertEqual(loaded["vendor_sdk_imports"], 0)
        self.assertEqual(loaded["order_submissions"], 0)
        self.assertTrue(self.output_path.read_bytes().endswith(b"\n"))


# 本段代码核心功能：当测试文件被直接执行时启动unittest标准运行器。
# - 输入：系统命令行中的unittest选项。
# - 处理：调用unittest.main发现当前测试类。
# - 输出：通过时退出码0，断言失败时非零。
# - 常量依据：项目验证脚本同时支持直接文件执行和unittest discover。
# - 为什么这样写：标准入口便于沙盒专项运行并保持与全量测试一致。
if __name__ == "__main__":
    unittest.main()
