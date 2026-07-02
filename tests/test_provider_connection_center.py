# 本文件核心功能：验证接入中心动态表单、秘密交换、状态机和UI ViewModel的安全合同。
# - 输入：临时Provider定义、模拟凭据写入器、目录JSON和用户提交样本。
# - 处理：覆盖合法提交、非法字段、秘密不回显、状态迁移、官方字段未核验阻断和Schema生成。
# - 输出：所有断言通过时证明TASK_024C可在不存储明文秘密的前提下支持未来可视化UI。
# - 常量依据：测试状态和安全边界来自PROVIDER_CONNECTION_CENTER.md与TASK_024C任务合同。
# - 为什么这样写：UI尚未选择具体框架时，先用领域测试锁定不可妥协的秘密和授权边界。

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from a_stock_quant.provider_connection_center import (
    ConnectionFieldDefinition,
    ConnectionStatus,
    FieldKind,
    PersistMode,
    ProviderConnectionDefinition,
    build_connection_center_view,
    build_dynamic_form_schema,
    load_connection_catalog,
    profile_to_safe_dict,
    submit_connection_form,
    transition_connection_status,
)


# 本段代码核心功能：提供只用于测试的凭据写入器。
# - 输入：领域函数传入的Provider、连接、字段和秘密值。
# - 处理：在内存中记录收到的调用并返回虚构引用；不写磁盘。
# - 输出：`test://...`引用字符串。
# - 常量依据：真实Windows安全后端属于TASK_024D，不应在本任务测试中伪装已经实现。
# - 为什么这样写：验证领域层确实把秘密交给端口，又不会把原文放进返回档案。
class RecordingCredentialWriter:
    """Record secret writes without persisting them."""

    # 本段代码核心功能：初始化空调用记录。
    # - 输入：无。
    # - 处理：创建列表。
    # - 输出：可供断言的calls属性。
    # - 常量依据：每个测试使用独立实例。
    # - 为什么这样写：测试之间不共享秘密样本。
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, str, str]] = []

    # 本段代码核心功能：记录一次秘密写入并返回非秘密引用。
    # - 输入：Provider、连接、字段和秘密值。
    # - 处理：追加元组，不执行系统调用。
    # - 输出：稳定测试引用。
    # - 常量依据：方法签名实现CredentialReferenceWriter协议。
    # - 为什么这样写：让测试检查秘密只到达写入端口。
    def store_secret(
        self,
        *,
        provider_id: str,
        connection_id: str,
        field_id: str,
        secret_value: str,
    ) -> str:
        self.calls.append(
            (provider_id, connection_id, field_id, secret_value)
        )
        return f"test://{provider_id}/{connection_id}/{field_id}"


# 本段代码核心功能：构建字段已由官方文档核验的测试Provider。
# - 输入：无。
# - 处理：创建公开环境字段、秘密API Key字段和布尔确认字段。
# - 输出：ProviderConnectionDefinition。
# - 常量依据：仅用于测试领域能力，不绑定任何真实券商。
# - 为什么这样写：避免在生产目录中编造真实券商字段，同时完整覆盖动态表单功能。
def make_verified_definition() -> ProviderConnectionDefinition:
    """Create a verified test-only provider definition."""

    return ProviderConnectionDefinition(
        provider_id="test_official_provider",
        display_name="Test official provider",
        provider_kind="TEST_ONLY",
        authority_tier="TIER_2_AUTHORIZED_BROKER",
        official_application_reference="test://official-guidance",
        form_definition_status="OFFICIAL_FIELDS_VERIFIED",
        supports_read_only_data=True,
        contains_execution_capability=True,
        fields=(
            ConnectionFieldDefinition(
                field_id="environment",
                label="Environment",
                kind=FieldKind.SELECT,
                required=True,
                persist_mode=PersistMode.CONFIGURATION,
                help_text="Official environment.",
                options=("test", "production"),
            ),
            ConnectionFieldDefinition(
                field_id="api_key",
                label="API key",
                kind=FieldKind.SECRET,
                required=True,
                persist_mode=PersistMode.CREDENTIAL_REFERENCE,
                help_text="Secret provided by the official portal.",
            ),
            ConnectionFieldDefinition(
                field_id="read_only_mode",
                label="Read-only mode",
                kind=FieldKind.BOOLEAN,
                required=True,
                persist_mode=PersistMode.CONFIGURATION,
                help_text="Must remain enabled.",
            ),
        ),
    )


# 本段代码核心功能：组织TASK_024C的领域与安全回归测试。
# - 输入：unittest运行器。
# - 处理：每个方法验证一个独立合同。
# - 输出：测试结果。
# - 常量依据：类名与任务能力一一对应。
# - 为什么这样写：细分测试便于定位未来UI或凭据后端集成破坏的具体边界。
class ProviderConnectionCenterTests(unittest.TestCase):
    """TASK_024C provider connection-center tests."""

    # 本段代码核心功能：验证秘密字段在Schema中是只写且无默认值。
    # - 输入：测试Provider定义。
    # - 处理：生成动态Schema并检查关键属性。
    # - 输出：断言结果。
    # - 常量依据：秘密不得在读取接口中回显。
    # - 为什么这样写：这是未来自动生成UI时最直接的防泄露标记。
    def test_dynamic_schema_marks_secret_fields_write_only(self) -> None:
        schema = build_dynamic_form_schema(make_verified_definition())
        api_key = schema["properties"]["api_key"]
        self.assertTrue(api_key["writeOnly"])
        self.assertTrue(api_key["x-sensitive"])
        self.assertNotIn("default", api_key)
        self.assertNotIn("example", api_key)
        self.assertEqual(schema["x-execution-activation"], "BLOCKED")

    # 本段代码核心功能：验证提交后档案只保存凭据引用而不保存秘密原文。
    # - 输入：环境、秘密和只读确认样本。
    # - 处理：调用submit_connection_form并安全序列化。
    # - 输出：引用存在、秘密原文不存在的断言。
    # - 常量依据：明文秘密只允许进入CredentialReferenceWriter。
    # - 为什么这样写：直接覆盖用户在UI粘贴密钥后的核心安全路径。
    def test_submission_exchanges_secret_for_reference(self) -> None:
        writer = RecordingCredentialWriter()
        profile = submit_connection_form(
            make_verified_definition(),
            connection_id="default_connection",
            submitted_values={
                "environment": "test",
                "api_key": "super-secret-value",
                "read_only_mode": True,
            },
            official_authorization_confirmed=True,
            read_only_entitlement_confirmed=True,
            execution_domain_isolated=True,
            credential_writer=writer,
        )
        safe = profile_to_safe_dict(profile)
        serialized = json.dumps(safe, ensure_ascii=False)
        self.assertEqual(len(writer.calls), 1)
        self.assertEqual(writer.calls[0][-1], "super-secret-value")
        self.assertNotIn("super-secret-value", serialized)
        self.assertEqual(
            safe["credential_references"]["api_key"],
            "test://test_official_provider/default_connection/api_key",
        )
        self.assertEqual(safe["status"], "CREDENTIALS_SAVED")

    # 本段代码核心功能：验证未知字段被后端白名单拒绝。
    # - 输入：额外的host字段。
    # - 处理：提交表单并捕获ValueError。
    # - 输出：异常断言。
    # - 常量依据：具体连接字段必须来自官方文档映射。
    # - 为什么这样写：阻止篡改UI请求绕过目录合同。
    def test_unknown_submission_field_is_rejected(self) -> None:
        writer = RecordingCredentialWriter()
        # 本段代码核心功能：在受控上下文中使用临时资源并保证离开代码块时自动释放。
        # - 输入：临时目录、文件句柄、补丁上下文或其他上下文管理器。
        # - 处理：上下文管理器负责建立和清理资源，业务代码只处理块内对象。
        # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
        # - 为什么这样写：自动清理可防止测试污染、文件句柄泄漏和跨任务状态残留。

        with self.assertRaises(ValueError):
            submit_connection_form(
                make_verified_definition(),
                connection_id="default_connection",
                submitted_values={
                    "environment": "test",
                    "api_key": "secret",
                    "read_only_mode": True,
                    "host": "unreviewed.example",
                },
                official_authorization_confirmed=True,
                read_only_entitlement_confirmed=True,
                execution_domain_isolated=True,
                credential_writer=writer,
            )

    # 本段代码核心功能：验证目录拒绝把秘密字段保存成普通配置。
    # - 输入：临时非法目录JSON。
    # - 处理：写文件并调用load_connection_catalog。
    # - 输出：ValueError断言。
    # - 常量依据：SECRET和CONFIGURATION组合永久禁止。
    # - 为什么这样写：把高风险错误挡在项目启动阶段。
    def test_catalog_rejects_secret_configuration_persistence(self) -> None:
        catalog = {
            "providers": [
                {
                    "provider_id": "bad_provider",
                    "fields": [
                        {
                            "field_id": "api_key",
                            "kind": "secret",
                            "persist_mode": "configuration",
                        }
                    ],
                }
            ]
        }
        # 本段代码核心功能：在受控上下文中使用临时资源并保证离开代码块时自动释放。
        # - 输入：临时目录、文件句柄、补丁上下文或其他上下文管理器。
        # - 处理：上下文管理器负责建立和清理资源，业务代码只处理块内对象。
        # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
        # - 为什么这样写：自动清理可防止测试污染、文件句柄泄漏和跨任务状态残留。

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "catalog.json"
            path.write_text(json.dumps(catalog), encoding="utf-8")
            # 本段代码核心功能：在受控上下文中使用临时资源并保证离开代码块时自动释放。
            # - 输入：临时目录、文件句柄、补丁上下文或其他上下文管理器。
            # - 处理：上下文管理器负责建立和清理资源，业务代码只处理块内对象。
            # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
            # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
            # - 为什么这样写：自动清理可防止测试污染、文件句柄泄漏和跨任务状态残留。

            with self.assertRaises(ValueError):
                load_connection_catalog(path)

    # 本段代码核心功能：验证生产目录中未核验具体字段的Provider不会开放配置按钮。
    # - 输入：仓库正式Provider目录。
    # - 处理：加载并生成卡片。
    # - 输出：状态和动作断言。
    # - 常量依据：当前公开资料不足以为每家券商猜测准确凭据字段。
    # - 为什么这样写：确保“可视化”不会退化为不可靠的万能密钥框。
    def test_unverified_official_fields_keep_form_closed(self) -> None:
        path = Path(
            "configs/providers/provider_connection_center_catalog_v1.json"
        )
        definitions = load_connection_catalog(path)
        cards = build_connection_center_view(definitions)
        self.assertGreaterEqual(len(cards), 5)
        # 本段代码核心功能：逐项遍历有限配置条目、发现证据或测试样本。
        # - 输入：可迭代的配置、证据或样本序列。
        # - 处理：每轮只更新当前条目局部结果，最终按稳定顺序汇总。
        # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
        # - 为什么这样写：逐项处理保留来源级证据，避免聚合后无法追溯单个Provider。

        for card in cards:
            self.assertEqual(
                card["status"],
                "OFFICIAL_FIELD_SPEC_REQUIRED",
            )
            self.assertNotIn(
                "OPEN_CONNECTION_FORM",
                card["available_actions"],
            )
            self.assertEqual(card["execution_activation"], "BLOCKED")

    # 本段代码核心功能：验证状态机允许只读流程并拒绝跳过门禁。
    # - 输入：合法和非法状态组合。
    # - 处理：调用transition_connection_status。
    # - 输出：目标状态或ValueError断言。
    # - 常量依据：未配置不能直接进入READY_FOR_RESEARCH。
    # - 为什么这样写：防止未来UI直接改状态字段绕过连接与语义审查。
    def test_status_machine_requires_ordered_read_only_flow(self) -> None:
        self.assertEqual(
            transition_connection_status(
                ConnectionStatus.CREDENTIALS_SAVED,
                ConnectionStatus.READ_ONLY_TEST_PENDING,
            ),
            ConnectionStatus.READ_ONLY_TEST_PENDING,
        )
        # 本段代码核心功能：在受控上下文中使用临时资源并保证离开代码块时自动释放。
        # - 输入：临时目录、文件句柄、补丁上下文或其他上下文管理器。
        # - 处理：上下文管理器负责建立和清理资源，业务代码只处理块内对象。
        # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
        # - 为什么这样写：自动清理可防止测试污染、文件句柄泄漏和跨任务状态残留。

        with self.assertRaises(ValueError):
            transition_connection_status(
                ConnectionStatus.NOT_CONFIGURED,
                ConnectionStatus.READY_FOR_RESEARCH,
            )

    # 本段代码核心功能：验证未确认授权时即便秘密写入成功也不会标记为可测试。
    # - 输入：授权确认False的合法表单。
    # - 处理：提交并检查状态。
    # - 输出：OFFICIAL_APPLICATION_REQUIRED断言。
    # - 常量依据：技术凭据存在不等于获得合法权限。
    # - 为什么这样写：许可证和授权门禁不能被UI密钥框替代。
    def test_authorization_confirmation_is_independent_gate(self) -> None:
        writer = RecordingCredentialWriter()
        profile = submit_connection_form(
            make_verified_definition(),
            connection_id="default_connection",
            submitted_values={
                "environment": "test",
                "api_key": "secret",
                "read_only_mode": True,
            },
            official_authorization_confirmed=False,
            read_only_entitlement_confirmed=True,
            execution_domain_isolated=True,
            credential_writer=writer,
        )
        self.assertEqual(
            profile.status,
            ConnectionStatus.OFFICIAL_APPLICATION_REQUIRED,
        )


# 本段代码核心功能：仅在文件被直接运行时启动unittest。
# - 输入：Python模块运行上下文。
# - 处理：检查`__name__`并调用unittest.main。
# - 输出：标准测试进程结果。
# - 常量依据：测试发现器导入文件时不重复启动。
# - 为什么这样写：兼容单文件运行和全量discover。
if __name__ == "__main__":
    unittest.main()
