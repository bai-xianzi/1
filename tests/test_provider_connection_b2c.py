# 本文件核心功能：验证TASK_024E数据接口接入中心的无秘密持久化、事务回滚、状态机、页面和本地HTTP安全边界。
# - 输入：内存WinCred假实现、临时档案文件、测试Provider定义和WSGI请求。
# - 处理：覆盖保存、失败恢复、只读测试、撤销、CSRF、本机限制和页面秘密防泄露。
# - 输出：任何秘密落盘、动作误开放、状态漂移或HTTP安全回退都会形成明确测试失败。
# - 常量依据：TASK_024C领域合同、TASK_024D安全存储、TASK_024E双视图和只读优先要求。
# - 为什么这样写：Linux沙盒不能调用真实Windows DLL，但通过官方后端端口注入仍能验证完整应用逻辑；真实WinCred由TASK_024D和用户Windows验收覆盖。
"""Tests for the provider connection-center B2C application."""

from __future__ import annotations

import io
import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from a_stock_quant.provider_connection_b2c import (
    JsonProviderConnectionProfileRepository,
    ProviderConnectionApplicationError,
    ProviderConnectionCenterService,
    ProviderConnectionCenterWSGIApp,
    ReadOnlyConnectionTestResult,
)
from a_stock_quant.provider_connection_center import (
    ConnectionFieldDefinition,
    ConnectionStatus,
    FieldKind,
    PersistMode,
    ProviderConnectionDefinition,
)
from a_stock_quant.windows_credential_store import (
    CredentialNotFoundError,
    CredentialStoreError,
    WindowsCredentialStore,
)


# 本段代码核心功能：模拟WinCred通用凭据API并支持指定删除次数故障注入。
# - 输入：规范化target_name、用户名标签和应用Blob。
# - 处理：在内存字典中写、读、删；delete_fail_at命中时抛系统错误。
# - 输出：供WindowsCredentialStore执行真实编码、引用和恢复逻辑。
# - 为什么这样写：测试不伪造上层安全存储行为，只替换Windows DLL端口，因此能覆盖TASK_024D到TASK_024E的组合路径。
class FakeWinCredentialApi:
    # 本段代码核心功能：初始化可注入删除故障的内存WinCred假实现。
    # - 输入：可选delete_fail_at，表示第几次删除时模拟系统失败。
    # - 处理：建立空凭据字典和调用计数，不接触真实Windows凭据。
    # - 输出：供WindowsCredentialStore组合测试使用的可控假API。
    # - 为什么这样写：故障注入必须可重复，才能验证多秘密撤销失败后的恢复逻辑。
    def __init__(self, *, delete_fail_at: int | None = None) -> None:
        self.records: dict[str, tuple[str, bytes]] = {}
        self.delete_fail_at = delete_fail_at
        self.delete_calls = 0

    # 本段代码核心功能：创建或覆盖一个内存通用凭据。
    # - 输入：目标名、用户名和秘密Blob。
    # - 处理：复制bytes并覆盖同名记录。
    # - 输出：无返回值。
    # - 为什么这样写：模拟CredWriteW覆盖语义，不保留调用方可变bytes引用。
    def write_generic(self, *, target_name: str, username: str, secret_blob: bytes) -> None:
        self.records[target_name] = (username, bytes(secret_blob))

    # 本段代码核心功能：读取一个内存通用凭据。
    # - 输入：目标名。
    # - 处理：不存在时映射为CredentialNotFoundError。
    # - 输出：用户名和秘密Blob副本。
    # - 为什么这样写：保持与WindowsCredentialStore期望的底层端口一致。
    def read_generic(self, *, target_name: str) -> tuple[str, bytes]:
        if target_name not in self.records:
            raise CredentialNotFoundError("not found")
        username, blob = self.records[target_name]
        return username, bytes(blob)

    # 本段代码核心功能：删除一个内存通用凭据并可注入一次系统失败。
    # - 输入：目标名。
    # - 处理：累计调用次数，命中故障点时抛CredentialStoreError；不存在时抛CredentialNotFoundError。
    # - 输出：成功时移除记录。
    # - 为什么这样写：用于证明多凭据撤销失败后能够恢复此前已删除秘密。
    def delete_generic(self, *, target_name: str) -> None:
        self.delete_calls += 1
        if self.delete_fail_at == self.delete_calls:
            raise CredentialStoreError("injected delete failure")
        if target_name not in self.records:
            raise CredentialNotFoundError("not found")
        del self.records[target_name]


# 本段代码核心功能：提供失败可控的内存档案仓储。
# - 输入：ProviderConnectionProfile和fail_on_save开关。
# - 处理：正常时复制保存，故障时在秘密写入之后抛异常。
# - 输出：供事务回滚测试使用。
# - 为什么这样写：必须验证“凭据已经写入但无秘密档案保存失败”的最危险边界。
class MemoryProfileRepository:
    # 本段代码核心功能：初始化支持保存和删除故障注入的内存档案仓储。
    # - 输入：fail_on_save和fail_on_delete两个测试开关。
    # - 处理：建立空档案字典并保存故障配置。
    # - 输出：供事务回滚和撤销恢复测试使用的仓储对象。
    # - 为什么这样写：分别控制两类持久化故障，才能证明秘密和无秘密档案不会出现半完成状态。
    def __init__(self, *, fail_on_save: bool = False, fail_on_delete: bool = False) -> None:
        self.items = {}
        self.fail_on_save = fail_on_save
        self.fail_on_delete = fail_on_delete

    # 本段代码核心功能：返回当前内存档案副本。
    # - 输入：无。
    # - 处理：复制items。
    # - 输出：按provider_id索引的字典。
    # - 为什么这样写：防止测试调用方直接修改仓储内部状态。
    def load_all(self):
        return dict(self.items)

    # 本段代码核心功能：保存档案或按故障开关抛出异常。
    # - 输入：profile。
    # - 处理：检查fail_on_save后覆盖记录。
    # - 输出：成功无返回值。
    # - 为什么这样写：用于验证秘密写入后的档案保存失败回滚。
    def save(self, profile) -> None:
        if self.fail_on_save:
            raise OSError("injected profile save failure")
        self.items[profile.provider_id] = profile

    # 本段代码核心功能：删除档案或按故障开关抛出异常。
    # - 输入：provider_id。
    # - 处理：检查fail_on_delete后幂等删除。
    # - 输出：成功无返回值。
    # - 为什么这样写：为撤销失败恢复场景提供可控仓储。
    def delete(self, provider_id: str) -> None:
        if self.fail_on_delete:
            raise OSError("injected profile delete failure")
        self.items.pop(provider_id, None)


# 本段代码核心功能：返回固定成功或失败结果的只读测试器。
# - 输入：预设success和运行时profile、resolve_secret函数。
# - 处理：解析api_key以证明测试器只能通过受控引用读取秘密，随后返回无秘密结果。
# - 输出：ReadOnlyConnectionTestResult。
# - 为什么这样写：验证SDK测试端口得到实际秘密但页面响应不包含秘密原文。
class FixedTester:
    # 本段代码核心功能：初始化返回固定成功或失败结果的只读连接测试器。
    # - 输入：success布尔值。
    # - 处理：保存预设结果并清空已观察秘密。
    # - 输出：可用于验证成功和失败状态迁移的测试器对象。
    # - 为什么这样写：测试结果可控后，专项测试才能只关注应用服务的秘密解析和状态机行为。
    def __init__(self, success: bool) -> None:
        self.success = success
        self.observed_secret = None

    # 本段代码核心功能：执行一次固定结果的只读测试并证明秘密只能通过引用解析。
    # - 输入：无秘密档案和受控resolve_secret函数。
    # - 处理：解析api_key引用并保存观察值，然后返回预设结果。
    # - 输出：不含秘密的ReadOnlyConnectionTestResult。
    # - 为什么这样写：既验证测试器可以使用秘密，又验证页面响应和结果对象不会回传秘密原文。
    def run(self, *, profile, resolve_secret):
        self.observed_secret = resolve_secret(profile.credential_references["api_key"])
        return ReadOnlyConnectionTestResult(
            success=self.success,
            summary="read-only probe passed" if self.success else "read-only probe failed",
            observations=("SDK session remained read-only",),
        )


# 本段代码核心功能：构造一个包含公开地址和两个秘密字段的官方Provider定义。
# - 输入：无。
# - 处理：使用TASK_024C真实数据类和枚举定义动态表单。
# - 输出：可用于保存、回滚和多凭据删除测试的ProviderConnectionDefinition。
# - 为什么这样写：两个秘密字段可以验证跨字段事务，而公开字段可以验证档案白名单持久化。
def make_definition() -> ProviderConnectionDefinition:
    return ProviderConnectionDefinition(
        provider_id="demo_provider",
        display_name="Demo Official Provider",
        provider_kind="MARKET_DATA",
        authority_tier="OFFICIAL_SDK",
        official_application_reference="official://demo/application",
        form_definition_status="OFFICIAL_FIELDS_VERIFIED",
        supports_read_only_data=True,
        contains_execution_capability=True,
        fields=(
            ConnectionFieldDefinition(
                field_id="endpoint",
                label="Endpoint",
                kind=FieldKind.TEXT,
                required=True,
                persist_mode=PersistMode.CONFIGURATION,
                help_text="Official read-only endpoint.",
            ),
            ConnectionFieldDefinition(
                field_id="api_key",
                label="API Key",
                kind=FieldKind.SECRET,
                required=True,
                persist_mode=PersistMode.CREDENTIAL_REFERENCE,
                help_text="Stored in Windows Credential Manager.",
            ),
            ConnectionFieldDefinition(
                field_id="api_secret",
                label="API Secret",
                kind=FieldKind.SECRET,
                required=True,
                persist_mode=PersistMode.CREDENTIAL_REFERENCE,
                help_text="Stored in Windows Credential Manager.",
            ),
        ),
    )


# 本段代码核心功能：构造标准安全提交参数。
# - 输入：可选秘密文本。
# - 处理：生成公开endpoint、两个秘密和三项明确授权确认。
# - 输出：可直接展开传给service.submit_connection的字典。
# - 为什么这样写：所有测试共享同一合法基线，只在目标边界修改一个条件。
def make_submission(secret: str = "TOP-SECRET-024E") -> dict[str, object]:
    return {
        "provider_id": "demo_provider",
        "connection_id": "demo_default",
        "values": {
            "endpoint": "https://official.example/read-only",
            "api_key": secret,
            "api_secret": "SECOND-SECRET-024E",
        },
        "official_authorization_confirmed": True,
        "read_only_entitlement_confirmed": True,
        "execution_domain_isolated": True,
    }


# 本段代码核心功能：验证接入中心应用、仓储、测试器和HTTP安全的完整行为。
# - 输入：每个测试独立临时目录、假WinCred和标准Provider定义。
# - 处理：setUp创建隔离对象，tearDown由TemporaryDirectory自动清理。
# - 输出：14项独立回归门禁。
# - 为什么这样写：测试之间不得共享秘密、档案或状态，防止顺序依赖掩盖事务错误。
class ProviderConnectionB2CTests(unittest.TestCase):
    # 本段代码核心功能：为每项测试创建隔离服务和安全存储。
    # - 输入：unittest生命周期。
    # - 处理：创建临时目录、假API、WindowsCredentialStore、JSON仓储和定义。
    # - 输出：self.service等测试对象。
    # - 为什么这样写：每项测试从NOT_CONFIGURED开始，结果可重复。
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.api = FakeWinCredentialApi()
        self.store = WindowsCredentialStore(api=self.api)
        self.repository = JsonProviderConnectionProfileRepository(
            Path(self.temporary.name) / "profiles.json"
        )
        self.definition = make_definition()
        self.service = ProviderConnectionCenterService(
            definitions=(self.definition,),
            profile_repository=self.repository,
            credential_store=self.store,
        )

    # 本段代码核心功能：确认生成器形式定义不会在初始化时被消费丢失。
    # - 输入：只产生一个定义的generator。
    # - 处理：初始化服务并获取卡片。
    # - 输出：卡片仍包含demo_provider。
    # - 为什么这样写：应用端口声明Sequence但防御生成器更稳健，避免首次遍历后页面为空。
    def test_definition_generator_is_materialized_once(self) -> None:
        service = ProviderConnectionCenterService(
            definitions=(item for item in (self.definition,)),
            profile_repository=self.repository,
            credential_store=self.store,
        )
        self.assertEqual("demo_provider", service.list_cards()[0]["provider_id"])

    # 本段代码核心功能：确认首页动作来自领域available_actions且未注册测试器时测试按钮被明确阻断。
    # - 输入：未配置档案和空testers注册表。
    # - 处理：调用list_cards。
    # - 输出：配置可用、测试不可用并说明等待TASK_024F。
    # - 为什么这样写：防止字段名写错导致配置按钮永久禁用，也防止页面展示没有后端实现的测试动作。
    def test_card_action_availability_uses_domain_available_actions(self) -> None:
        card = self.service.list_cards()[0]
        self.assertTrue(card["action_availability"]["OPEN_CONNECTION_FORM"]["available"])
        self.assertFalse(card["action_availability"]["RUN_READ_ONLY_CONNECTION_TEST"]["available"])
        self.assertIn("TASK_024F", card["action_availability"]["RUN_READ_ONLY_CONNECTION_TEST"]["reason"])

    # 本段代码核心功能：确认合法提交把秘密写入WinCred而档案文件只保存引用。
    # - 输入：含独特秘密标记的标准提交。
    # - 处理：调用submit_connection并读取JSON文件和安全profile。
    # - 输出：文件不含秘密，状态为CREDENTIALS_SAVED，页面只显示configured。
    # - 为什么这样写：这是TASK_024E最核心的B2C安全边界。
    def test_submit_saves_only_secret_references(self) -> None:
        secret = "UNIQUE-SECRET-MUST-NOT-LEAK"
        result = self.service.submit_connection(**make_submission(secret))
        persisted = self.repository.path.read_text(encoding="utf-8")
        self.assertNotIn(secret, persisted)
        self.assertNotIn("SECOND-SECRET-024E", persisted)
        self.assertIn("windows-credential://", persisted)
        self.assertEqual(ConnectionStatus.CREDENTIALS_SAVED.value, result["profile"]["status"])
        self.assertTrue(result["profile"]["credential_status"]["api_key"]["configured"])
        self.assertIsNone(result["profile"]["credential_status"]["api_key"]["secret_value"])

    # 本段代码核心功能：确认档案保存失败后新写入的多项秘密全部回滚。
    # - 输入：fail_on_save内存仓储和合法提交。
    # - 处理：秘密先写入假WinCred，仓储再失败，服务捕获并回滚。
    # - 输出：安全业务错误且假WinCred为空。
    # - 为什么这样写：避免用户看到“保存失败”但Windows保险箱残留半套凭据。
    def test_profile_save_failure_rolls_back_new_secrets(self) -> None:
        repository = MemoryProfileRepository(fail_on_save=True)
        service = ProviderConnectionCenterService(
            definitions=(self.definition,),
            profile_repository=repository,
            credential_store=self.store,
        )
        with self.assertRaises(ProviderConnectionApplicationError) as captured:
            service.submit_connection(**make_submission())
        self.assertEqual("CONNECTION_SAVE_FAILED", captured.exception.code)
        self.assertEqual({}, self.api.records)

    # 本段代码核心功能：确认更新失败会恢复旧秘密而不是仅删除新值。
    # - 输入：先成功保存OLD，再让仓储失败并提交NEW。
    # - 处理：事务写入器记录旧值，失败后按引用恢复。
    # - 输出：两个秘密仍为旧值。
    # - 为什么这样写：更新失败不能破坏此前可用的连接。
    def test_update_failure_restores_previous_secrets(self) -> None:
        memory = MemoryProfileRepository()
        service = ProviderConnectionCenterService(
            definitions=(self.definition,),
            profile_repository=memory,
            credential_store=self.store,
        )
        service.submit_connection(**make_submission("OLD-KEY"))
        profile = memory.items["demo_provider"]
        memory.fail_on_save = True
        with self.assertRaises(ProviderConnectionApplicationError):
            service.submit_connection(**make_submission("NEW-KEY"))
        self.assertEqual("OLD-KEY", self.store.resolve_secret(profile.credential_references["api_key"]))
        self.assertEqual("SECOND-SECRET-024E", self.store.resolve_secret(profile.credential_references["api_secret"]))

    # 本段代码核心功能：确认JSON仓储严格拒绝未知字段和错误版本。
    # - 输入：人工构造的非法档案文件。
    # - 处理：调用load_all。
    # - 输出：ValueError失败关闭。
    # - 为什么这样写：本地配置被旧版本或人工修改后不能宽松猜测并传给SDK。
    def test_repository_rejects_unknown_profile_fields(self) -> None:
        self.repository.path.parent.mkdir(parents=True, exist_ok=True)
        self.repository.path.write_text(
            json.dumps({"schema_version": 1, "profiles": [{"unexpected": "value"}]}),
            encoding="utf-8",
        )
        with self.assertRaises(ValueError):
            self.repository.load_all()

    # 本段代码核心功能：确认没有具体测试器时只读测试被后端阻断。
    # - 输入：已保存连接和空testers。
    # - 处理：调用run_read_only_test。
    # - 输出：READ_ONLY_TESTER_NOT_AVAILABLE冲突错误。
    # - 为什么这样写：TASK_024E不能假装已经连接Wind、iFinD或券商SDK。
    def test_read_only_test_requires_registered_tester(self) -> None:
        self.service.submit_connection(**make_submission())
        with self.assertRaises(ProviderConnectionApplicationError) as captured:
            self.service.run_read_only_test("demo_provider")
        self.assertEqual("READ_ONLY_TESTER_NOT_AVAILABLE", captured.exception.code)

    # 本段代码核心功能：确认成功只读探针通过受控引用读取秘密并迁移到READ_ONLY_VERIFIED。
    # - 输入：成功FixedTester和已保存连接。
    # - 处理：执行测试并持久化最终状态。
    # - 输出：测试器看到秘密，响应不含秘密且交易仍BLOCKED。
    # - 为什么这样写：验证未来TASK_024F接入点，同时保持B2C白箱与秘密隔离。
    def test_successful_read_only_test_updates_state_without_leak(self) -> None:
        tester = FixedTester(True)
        service = ProviderConnectionCenterService(
            definitions=(self.definition,),
            profile_repository=self.repository,
            credential_store=self.store,
            testers={"demo_provider": tester},
        )
        service.submit_connection(**make_submission("RUNTIME-ONLY-SECRET"))
        result = service.run_read_only_test("demo_provider")
        self.assertEqual("RUNTIME-ONLY-SECRET", tester.observed_secret)
        self.assertEqual(ConnectionStatus.READ_ONLY_VERIFIED.value, result["profile"]["status"])
        self.assertEqual("BLOCKED", result["execution_activation"])
        self.assertNotIn("RUNTIME-ONLY-SECRET", json.dumps(result, ensure_ascii=False))

    # 本段代码核心功能：确认失败探针迁移到CONNECTION_TEST_FAILED并可再次测试。
    # - 输入：失败FixedTester。
    # - 处理：保存连接、执行测试、检查卡片动作。
    # - 输出：失败状态和可重试动作。
    # - 为什么这样写：网络或授权失败是可恢复状态，不能永久锁死连接。
    def test_failed_read_only_test_is_retryable(self) -> None:
        tester = FixedTester(False)
        service = ProviderConnectionCenterService(
            definitions=(self.definition,),
            profile_repository=self.repository,
            credential_store=self.store,
            testers={"demo_provider": tester},
        )
        service.submit_connection(**make_submission())
        result = service.run_read_only_test("demo_provider")
        self.assertEqual(ConnectionStatus.CONNECTION_TEST_FAILED.value, result["profile"]["status"])
        self.assertTrue(service.list_cards()[0]["action_availability"]["RUN_READ_ONLY_CONNECTION_TEST"]["available"])

    # 本段代码核心功能：确认正常停用同时删除两项秘密和档案。
    # - 输入：已保存连接。
    # - 处理：调用disable_connection。
    # - 输出：假WinCred和档案均为空。
    # - 为什么这样写：停用不能只隐藏页面记录而把密钥遗留在Windows保险箱。
    def test_disable_deletes_credentials_and_profile(self) -> None:
        self.service.submit_connection(**make_submission())
        self.service.disable_connection("demo_provider")
        self.assertEqual({}, self.api.records)
        self.assertEqual({}, self.repository.load_all())

    # 本段代码核心功能：确认第二项凭据删除失败时恢复第一项并保留档案。
    # - 输入：delete_fail_at=2的假WinCred和内存仓储。
    # - 处理：保存两项秘密后执行停用。
    # - 输出：抛安全错误、档案存在、两个秘密仍可读取。
    # - 为什么这样写：多项撤销必须尽可能保持原子性，不能产生“配置存在但第一把钥匙丢失”的半状态。
    def test_disable_failure_restores_previously_deleted_secret(self) -> None:
        api = FakeWinCredentialApi(delete_fail_at=2)
        store = WindowsCredentialStore(api=api)
        repository = MemoryProfileRepository()
        service = ProviderConnectionCenterService(
            definitions=(self.definition,),
            profile_repository=repository,
            credential_store=store,
        )
        service.submit_connection(**make_submission("RESTORE-ME"))
        profile = repository.items["demo_provider"]
        with self.assertRaises(ProviderConnectionApplicationError) as captured:
            service.disable_connection("demo_provider")
        self.assertEqual("CREDENTIAL_DELETE_FAILED", captured.exception.code)
        self.assertIn("demo_provider", repository.items)
        self.assertEqual("RESTORE-ME", store.resolve_secret(profile.credential_references["api_key"]))
        self.assertEqual("SECOND-SECRET-024E", store.resolve_secret(profile.credential_references["api_secret"]))

    # 本段代码核心功能：确认非本机来源不能访问页面和API。
    # - 输入：REMOTE_ADDR为局域网地址的WSGI请求。
    # - 处理：直接调用应用并捕获状态与JSON。
    # - 输出：403 LOCAL_ONLY。
    # - 为什么这样写：密钥输入页不能因为误配置监听地址而对局域网开放。
    def test_wsgi_rejects_non_loopback_client(self) -> None:
        app = ProviderConnectionCenterWSGIApp(self.service, csrf_token="fixed-token")
        status, _headers, payload = self._call_wsgi(app, method="GET", path="/api/health", remote="192.168.1.8")
        self.assertEqual("403 Forbidden", status)
        self.assertEqual("LOCAL_ONLY", payload["error"]["code"])

    # 本段代码核心功能：确认所有变更请求必须携带页面CSRF令牌。
    # - 输入：不含X-WJX-CSRF-Token的POST。
    # - 处理：调用保存路由。
    # - 输出：403 CSRF_REJECTED且秘密未写入。
    # - 为什么这样写：本地HTTP服务仍可能被浏览器中的恶意网页跨站触发。
    def test_wsgi_rejects_mutation_without_csrf(self) -> None:
        app = ProviderConnectionCenterWSGIApp(self.service, csrf_token="fixed-token")
        body = json.dumps({"connection_id": "demo_default", "values": {}}).encode("utf-8")
        status, _headers, payload = self._call_wsgi(app, method="POST", path="/api/provider-connections/demo_provider", body=body)
        self.assertEqual("403 Forbidden", status)
        self.assertEqual("CSRF_REJECTED", payload["error"]["code"])
        self.assertEqual({}, self.api.records)

    # 本段代码核心功能：确认首页包含功能解释和秘密防泄露承诺，但不包含浏览器持久化调用。
    # - 输入：GET /provider-connections。
    # - 处理：读取HTML文本。
    # - 输出：页面说明存在，localStorage和sessionStorage不存在。
    # - 为什么这样写：用户应理解页面用途，秘密又不能为了便利留在浏览器持久状态。
    def test_page_is_explanatory_and_does_not_use_browser_storage(self) -> None:
        app = ProviderConnectionCenterWSGIApp(self.service, csrf_token="fixed-token")
        status, _headers, body = self._call_wsgi(app, method="GET", path="/provider-connections", decode_json=False)
        html = body.decode("utf-8")
        self.assertEqual("200 OK", status)
        self.assertIn("这个页面是干什么的", html)
        self.assertIn("Windows安全凭据", html)
        self.assertNotIn("localStorage.", html)
        self.assertNotIn("sessionStorage.", html)

    # 本段代码核心功能：执行一个最小WSGI请求并返回状态、响应头和解码结果。
    # - 输入：应用、方法、路径、来源、请求体和是否解析JSON。
    # - 处理：构造标准environ，捕获start_response，拼接bytes。
    # - 输出：状态字符串、头字典和JSON对象或原始bytes。
    # - 为什么这样写：不启动真实端口即可稳定验证本机、CSRF和页面响应。
    def _call_wsgi(self, app, *, method: str, path: str, remote: str = "127.0.0.1", body: bytes = b"", decode_json: bool = True):
        captured = {}

        # 本段代码核心功能：捕获WSGI应用通过start_response返回的状态和响应头。
        # - 输入：HTTP状态字符串和头部键值序列。
        # - 处理：转换头部为字典并写入当前测试局部容器。
        # - 输出：供_call_wsgi返回并由测试断言的状态与响应头。
        # - 为什么这样写：不启动真实网络端口也能完整检查WSGI状态、安全头和响应内容。
        def start_response(status, headers):
            captured["status"] = status
            captured["headers"] = dict(headers)

        environ = {
            "REQUEST_METHOD": method,
            "PATH_INFO": path,
            "REMOTE_ADDR": remote,
            "CONTENT_TYPE": "application/json",
            "CONTENT_LENGTH": str(len(body)),
            "wsgi.input": io.BytesIO(body),
        }
        response = b"".join(app(environ, start_response))
        payload = json.loads(response.decode("utf-8")) if decode_json else response
        return captured["status"], captured["headers"], payload


# 本段代码核心功能：支持专项测试文件直接运行并返回标准unittest退出码。
# - 输入：Python直接执行标志。
# - 处理：调用unittest.main。
# - 输出：终端显示测试数量和结果。
# - 为什么这样写：既支持全量discover，也方便TASK_024E应用器执行单文件快速门禁。
if __name__ == "__main__":
    unittest.main()
