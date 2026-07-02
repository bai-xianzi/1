# 本文件核心功能：验证Windows凭据后端的引用、编码、写入、读取、存在检查、删除和失败关闭规则。
# - 输入：内存假WinCred API和不同合法/非法标识、引用及秘密值。
# - 处理：不访问真实Windows凭据集，逐项断言生产类通过稳定端口执行预期操作。
# - 输出：覆盖跨平台可执行的TASK_024D核心行为；Windows真实API另由本地验收脚本验证。
# - 为什么这样写：沙盒是Linux，依赖注入可先发现绝大多数逻辑和泄密错误，避免用户在Windows首次运行时承担低级调试。
from __future__ import annotations

import sys
import unittest
from pathlib import Path

# 本段代码核心功能：把仓库src目录加入导入路径，兼容项目尚未安装为wheel的当前运行方式。
# - 输入：测试文件绝对路径。
# - 处理：向上找到仓库根目录并把src字符串插入sys.path首位。
# - 输出：测试导入当前工作树中的a_stock_quant模块。
# - 为什么这样写：确保测试不会误用系统中旧版本包，也与现有源码目录测试方式兼容。
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from a_stock_quant.windows_credential_store import (  # noqa: E402
    CRED_MAX_CREDENTIAL_BLOB_SIZE,
    PAYLOAD_PREFIX,
    CredentialNotFoundError,
    CredentialStoreError,
    InvalidCredentialReferenceError,
    UnsupportedCredentialPlatformError,
    WindowsCredentialStore,
    _CtypesWinCredentialApi,
    build_credential_location,
    parse_credential_reference,
)


# 本段代码核心功能：以内存字典模拟WinCred写入、读取和删除行为。
# - 输入：规范化target_name、username和secret_blob。
# - 处理：复制bytes保存，保持与Windows目标覆盖语义一致；缺失时抛领域异常。
# - 输出：供WindowsCredentialStore单元测试注入的稳定假后端。
# - 为什么这样写：假后端不记录日志、不接触操作系统秘密存储，却能验证所有上层合同和错误路径。
class InMemoryWinCredentialApi:
    # 本段代码核心功能：初始化每个测试独享的内存记录和非秘密调用轨迹。
    # - 输入：无外部输入。
    # - 处理：创建目标记录字典及写入、读取、删除目标名列表。
    # - 输出：空白且隔离的假WinCred状态。
    # - 为什么这样写：测试不能共享秘密或调用历史，避免顺序相关和误判。
    def __init__(self) -> None:
        self.records: dict[str, tuple[str, bytes]] = {}
        self.write_calls: list[str] = []
        self.read_calls: list[str] = []
        self.delete_calls: list[str] = []

    # 本段代码核心功能：模拟创建或覆盖通用凭据。
    # - 输入：目标名、用户名标签和Blob。
    # - 处理：复制并保存到records，记录非秘密目标名调用。
    # - 输出：无返回值。
    # - 为什么这样写：复制bytes避免调用方后续修改缓冲区影响测试记录。
    def write_generic(self, *, target_name: str, username: str, secret_blob: bytes) -> None:
        self.write_calls.append(target_name)
        self.records[target_name] = (username, bytes(secret_blob))

    # 本段代码核心功能：模拟读取通用凭据。
    # - 输入：目标名。
    # - 处理：记录调用并返回保存值，不存在时抛CredentialNotFoundError。
    # - 输出：用户名标签与Blob。
    # - 为什么这样写：与生产适配器缺失语义保持一致。
    def read_generic(self, *, target_name: str) -> tuple[str, bytes]:
        self.read_calls.append(target_name)
        try:
            username, blob = self.records[target_name]
        except KeyError as exc:
            raise CredentialNotFoundError("credential is not configured") from exc
        return username, bytes(blob)

    # 本段代码核心功能：模拟删除通用凭据。
    # - 输入：目标名。
    # - 处理：记录调用并删除字典项，不存在时抛CredentialNotFoundError。
    # - 输出：无返回值。
    # - 为什么这样写：验证B2C撤销流程不会只删除引用而遗留底层秘密。
    def delete_generic(self, *, target_name: str) -> None:
        self.delete_calls.append(target_name)
        try:
            del self.records[target_name]
        except KeyError as exc:
            raise CredentialNotFoundError("credential is not configured") from exc


# 本段代码核心功能：对TASK_024D公开合同和安全失败模式进行完整单元测试。
# - 输入：每个测试创建的独立内存后端和WindowsCredentialStore。
# - 处理：执行真实业务方法并断言引用、Blob、异常、存在状态和安全ViewModel。
# - 输出：任何合同回退都会形成明确unittest失败。
# - 为什么这样写：凭据后端属于高风险基础设施，边界条件必须与正常路径同等测试。
class WindowsCredentialStoreTests(unittest.TestCase):
    # 本段代码核心功能：为每个测试创建隔离的假API和被测存储对象。
    # - 输入：无外部输入。
    # - 处理：重新初始化records和调用列表。
    # - 输出：self.api和self.store。
    # - 为什么这样写：测试之间不能共享任何秘密或目标名状态。
    def setUp(self) -> None:
        self.api = InMemoryWinCredentialApi()
        self.store = WindowsCredentialStore(api=self.api)

    # 本段代码核心功能：验证三个标识生成稳定、可逆的WJX安全引用和Windows目标名。
    # - 输入：合法provider、connection和field标识。
    # - 处理：先生成再解析。
    # - 输出：所有字段、引用和目标名完全一致。
    # - 为什么这样写：连接档案必须长期保存稳定引用，不能因前后端实现不同产生漂移。
    def test_build_and_parse_reference_round_trip(self) -> None:
        location = build_credential_location(
            provider_id="broker_demo",
            connection_id="research_main",
            field_id="api_token",
        )
        self.assertEqual(
            "windows-credential://WJX/provider/broker_demo/research_main/api_token",
            location.reference,
        )
        self.assertEqual(
            "WJX/provider/broker_demo/research_main/api_token",
            location.target_name,
        )
        self.assertEqual(location, parse_credential_reference(location.reference))

    # 本段代码核心功能：验证store_secret只返回引用并按WJX1格式写入假WinCred后端。
    # - 输入：含中文和符号的秘密值。
    # - 处理：调用store_secret并查看假后端保存的目标、用户名和Blob。
    # - 输出：返回值不含秘密，Blob可被后续严格解码。
    # - 为什么这样写：连接档案和UI响应只能得到引用，秘密只能出现在安全存储调用边界。
    def test_store_secret_returns_reference_without_secret_text(self) -> None:
        secret = "令牌-Alpha-123"
        reference = self.store.store_secret(
            provider_id="broker_demo",
            connection_id="research_main",
            field_id="api_token",
            secret_value=secret,
        )
        self.assertNotIn(secret, reference)
        location = parse_credential_reference(reference)
        username, blob = self.api.records[location.target_name]
        self.assertEqual("broker_demo:research_main:api_token", username)
        self.assertTrue(blob.startswith(PAYLOAD_PREFIX))
        self.assertEqual(secret, self.store.resolve_secret(reference))

    # 本段代码核心功能：验证同一引用再次保存时执行安全覆盖更新。
    # - 输入：相同标识的旧值和新值。
    # - 处理：连续调用两次store_secret。
    # - 输出：引用不变，读取结果为新值，后端只有一个目标记录。
    # - 为什么这样写：B2C“替换密钥”不应生成孤儿凭据或要求用户编辑配置引用。
    def test_store_secret_replaces_existing_value_at_same_reference(self) -> None:
        first = self.store.store_secret(
            provider_id="broker_demo",
            connection_id="research_main",
            field_id="api_token",
            secret_value="old-value",
        )
        second = self.store.store_secret(
            provider_id="broker_demo",
            connection_id="research_main",
            field_id="api_token",
            secret_value="new-value",
        )
        self.assertEqual(first, second)
        self.assertEqual("new-value", self.store.resolve_secret(second))
        self.assertEqual(1, len(self.api.records))

    # 本段代码核心功能：验证安全状态对象不包含秘密或用户名标签。
    # - 输入：已配置引用。
    # - 处理：调用build_safe_status。
    # - 输出：只返回后端、引用、configured和显式None秘密占位。
    # - 为什么这样写：B2C页面只能显示是否配置，不能通过状态接口取得原文。
    def test_safe_status_never_returns_secret(self) -> None:
        secret = "private-token"
        reference = self.store.store_secret(
            provider_id="broker_demo",
            connection_id="research_main",
            field_id="api_token",
            secret_value=secret,
        )
        status = self.store.build_safe_status(reference)
        self.assertEqual("WINDOWS_CREDENTIAL_MANAGER", status["backend"])
        self.assertTrue(status["configured"])
        self.assertIsNone(status["secret_value"])
        self.assertNotIn(secret, repr(status))

    # 本段代码核心功能：验证未配置引用的存在检查返回False而不是系统异常。
    # - 输入：合法但尚未写入的引用。
    # - 处理：调用secret_exists。
    # - 输出：False。
    # - 为什么这样写：UI需要稳定展示“未配置”，该状态不应被当作系统故障。
    def test_secret_exists_returns_false_for_missing_reference(self) -> None:
        reference = build_credential_location(
            provider_id="broker_demo",
            connection_id="research_main",
            field_id="api_token",
        ).reference
        self.assertFalse(self.store.secret_exists(reference))

    # 本段代码核心功能：验证删除会同时改变存在状态并阻止后续读取。
    # - 输入：先保存的引用。
    # - 处理：调用delete_secret，再检查存在和resolve_secret。
    # - 输出：存在为False，读取抛CredentialNotFoundError。
    # - 为什么这样写：撤销必须真正删除操作系统秘密，而不只是隐藏前端卡片。
    def test_delete_secret_removes_underlying_record(self) -> None:
        reference = self.store.store_secret(
            provider_id="broker_demo",
            connection_id="research_main",
            field_id="api_token",
            secret_value="temporary-value",
        )
        self.store.delete_secret(reference)
        self.assertFalse(self.store.secret_exists(reference))
        with self.assertRaises(CredentialNotFoundError):
            self.store.resolve_secret(reference)

    # 本段代码核心功能：验证引用解析拒绝其他scheme、authority、查询参数和非法标识。
    # - 输入：四种越权或非规范引用。
    # - 处理：逐项调用parse_credential_reference。
    # - 输出：全部抛InvalidCredentialReferenceError。
    # - 为什么这样写：配置引用不能成为读取用户任意Credential Manager记录的通用入口。
    def test_reference_parser_rejects_out_of_scope_targets(self) -> None:
        invalid_references = (
            "file://WJX/provider/broker_demo/research_main/api_token",
            "windows-credential://OTHER/provider/broker_demo/research_main/api_token",
            "windows-credential://WJX/provider/Broker/research_main/api_token",
            "windows-credential://WJX/provider/broker_demo/research_main/api_token?x=1",
        )
        for reference in invalid_references:
            with self.subTest(reference=reference):
                with self.assertRaises(InvalidCredentialReferenceError):
                    parse_credential_reference(reference)

    # 本段代码核心功能：验证秘密为空时在底层写入前失败。
    # - 输入：空字符串。
    # - 处理：调用store_secret。
    # - 输出：ValueError且假API无写调用。
    # - 为什么这样写：不允许用空值覆盖有效密钥或产生看似已配置的无效状态。
    def test_empty_secret_is_rejected_before_write(self) -> None:
        with self.assertRaises(ValueError):
            self.store.store_secret(
                provider_id="broker_demo",
                connection_id="research_main",
                field_id="api_token",
                secret_value="",
            )
        self.assertEqual([], self.api.write_calls)

    # 本段代码核心功能：验证超过微软CredentialBlob上限的秘密在写入前失败。
    # - 输入：确保加上WJX前缀后超过2560字节的字符串。
    # - 处理：调用store_secret。
    # - 输出：ValueError且后端无记录。
    # - 为什么这样写：在Python层给出明确错误，避免依赖Win32模糊失败并防止秘密出现在系统错误文本中。
    def test_oversized_secret_is_rejected_before_write(self) -> None:
        oversized = "x" * (CRED_MAX_CREDENTIAL_BLOB_SIZE + 1)
        with self.assertRaises(ValueError):
            self.store.store_secret(
                provider_id="broker_demo",
                connection_id="research_main",
                field_id="api_token",
                secret_value=oversized,
            )
        self.assertEqual({}, self.api.records)

    # 本段代码核心功能：验证读取到未知载荷格式时失败关闭。
    # - 输入：合法目标下人工放入的非WJX Blob。
    # - 处理：调用resolve_secret。
    # - 输出：CredentialStoreError，不返回猜测文本。
    # - 为什么这样写：不能把其他应用、损坏或旧版本数据误当作有效Provider密钥。
    def test_unknown_payload_format_is_rejected(self) -> None:
        location = build_credential_location(
            provider_id="broker_demo",
            connection_id="research_main",
            field_id="api_token",
        )
        self.api.records[location.target_name] = (
            "broker_demo:research_main:api_token",
            b"not-a-wjx-payload",
        )
        with self.assertRaises(CredentialStoreError):
            self.store.resolve_secret(location.reference)

    # 本段代码核心功能：验证用户名标签与引用不一致时拒绝秘密。
    # - 输入：合法Blob但错误用户名标签。
    # - 处理：调用resolve_secret。
    # - 输出：CredentialStoreError。
    # - 为什么这样写：目标名之外再校验标签可以发现手工篡改、错误迁移和记录串线。
    def test_username_label_mismatch_is_rejected(self) -> None:
        location = build_credential_location(
            provider_id="broker_demo",
            connection_id="research_main",
            field_id="api_token",
        )
        self.api.records[location.target_name] = (
            "other:connection:field",
            PAYLOAD_PREFIX + b"value",
        )
        with self.assertRaises(CredentialStoreError):
            self.store.resolve_secret(location.reference)

    # 本段代码核心功能：验证非Windows环境默认生产后端明确失败而不降级。
    # - 输入：当前沙盒平台。
    # - 处理：仅在非Windows时初始化_CtypesWinCredentialApi。
    # - 输出：UnsupportedCredentialPlatformError。
    # - 为什么这样写：秘密安全不能因为平台不支持而退回明文文件、环境变量或内存长期保存。
    @unittest.skipIf(sys.platform.startswith("win"), "non-Windows failure path only")
    def test_default_ctypes_backend_fails_closed_off_windows(self) -> None:
        with self.assertRaises(UnsupportedCredentialPlatformError):
            _CtypesWinCredentialApi()


# 本段代码核心功能：允许用户或应用脚本直接运行本专项测试文件。
# - 输入：Python命令行入口。
# - 处理：由unittest发现并执行当前测试类。
# - 输出：标准测试数量、通过或失败及退出码。
# - 为什么这样写：既支持全量discover，也方便TASK_024D本地验收前单独运行。
if __name__ == "__main__":
    unittest.main()
