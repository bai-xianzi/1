# 本文件核心功能：把Provider接入中心提交的秘密值写入Windows Credential Manager，并只向项目配置返回安全引用。
# - 输入：provider_id、connection_id、field_id和仅存在于本次请求内存中的secret_value。
# - 处理：校验标识和大小，把秘密编码成带版本前缀的应用数据，通过微软WinCred官方API写入当前用户凭据集；读取和删除同样只接受安全引用。
# - 输出：`windows-credential://WJX/provider/...`形式的非秘密引用，以及供运行时使用的按需解析、存在检查和删除能力。
# - 常量依据：CredentialBlob上限2560字节、CRED_TYPE_GENERIC和CRED_PERSIST_LOCAL_MACHINE来自微软WinCred官方合同。
# - 为什么这样写：复用Windows官方凭据存储而不自研加密算法，同时用薄适配器满足TASK_024C的CredentialReferenceWriter协议。
"""Windows Credential Manager backend for secret-free provider profiles."""

from __future__ import annotations

import ctypes
import platform
import re
from ctypes import wintypes
from dataclasses import dataclass
from typing import Protocol
from urllib.parse import urlsplit

# 本段代码核心功能：声明Windows Credential Manager官方常量和WJX引用格式常量。
# - 输入：无运行时输入，数值来自微软wincred.h合同。
# - 处理：作为写入、读取、删除、大小校验和引用解析的统一事实源。
# - 输出：后续函数使用稳定常量而不散落魔法数字。
# - 常量依据：CRED_TYPE_GENERIC=1、CRED_PERSIST_LOCAL_MACHINE=2、最大Blob为5*512字节。
# - 为什么这样写：集中记录官方常量便于审计，也避免未来实现者误用域密码凭据或企业漫游持久化。
CRED_TYPE_GENERIC = 1
CRED_PERSIST_LOCAL_MACHINE = 2
CRED_MAX_CREDENTIAL_BLOB_SIZE = 5 * 512
ERROR_NOT_FOUND = 1168
REFERENCE_SCHEME = "windows-credential"
REFERENCE_AUTHORITY = "WJX"
TARGET_PREFIX = "WJX/provider"
PAYLOAD_PREFIX = b"WJX1\x00"
IDENTIFIER_PATTERN = re.compile(r"^[a-z][a-z0-9_]{1,63}$")


# 本段代码核心功能：定义Windows凭据后端统一异常基类。
# - 输入：只接受不含秘密原文的操作说明和系统错误码。
# - 处理：由具体异常区分平台不支持、引用非法、凭据不存在和Win32调用失败。
# - 输出：调用方可以安全记录异常类型和错误码，而不会把secret_value写入日志。
# - 为什么这样写：秘密管理失败必须显式失败关闭，但异常信息本身也不能成为泄密旁路。
class CredentialStoreError(RuntimeError):
    """Base error for WJX credential-store operations."""


# 本段代码核心功能：表示当前操作系统无法使用Windows Credential Manager。
# - 输入：当前平台名称。
# - 处理：默认后端初始化时检测，不尝试静默退回明文文件或自制加密。
# - 输出：清晰的失败关闭异常。
# - 为什么这样写：跨平台测试可以注入假后端，但生产秘密绝不能因为平台不支持而降级到普通配置。
class UnsupportedCredentialPlatformError(CredentialStoreError):
    """Raised when the Windows-only backend is requested elsewhere."""


# 本段代码核心功能：表示凭据引用格式不合法或不属于WJX命名空间。
# - 输入：外部配置或UI提交的引用字符串。
# - 处理：在任何Win32调用之前检查scheme、authority、路径段和标识格式。
# - 输出：安全的ValueError子类，不包含秘密原文。
# - 为什么这样写：引用可能来自配置、数据库或用户输入，必须防止任意Windows目标名被借此读取或删除。
class InvalidCredentialReferenceError(ValueError):
    """Raised when a credential reference is malformed or out of scope."""


# 本段代码核心功能：表示目标引用尚未在当前用户Windows凭据集中配置。
# - 输入：安全引用或目标名。
# - 处理：把Win32 ERROR_NOT_FOUND映射成稳定领域异常。
# - 输出：UI可据此显示“未配置”而不误报系统故障。
# - 为什么这样写：凭据缺失是可预期状态，与权限失败、平台错误或其他Win32错误必须区分。
class CredentialNotFoundError(CredentialStoreError):
    """Raised when the requested credential does not exist."""


# 本段代码核心功能：保存从安全引用解析出的三个受控标识和Windows目标名。
# - 输入：经过格式校验的provider、connection和field标识。
# - 处理：使用不可变dataclass防止解析后被调用方修改。
# - 输出：供读取、删除、存在检查和UI安全状态共用。
# - 为什么这样写：引用解析只做一次，后续所有操作使用同一规范化结果，避免路径和目标名漂移。
@dataclass(frozen=True)
class CredentialLocation:
    """Validated location of one WJX provider secret."""

    provider_id: str
    connection_id: str
    field_id: str
    target_name: str
    reference: str


# 本段代码核心功能：定义可替换的底层WinCred API端口。
# - 输入：规范化目标名、非秘密用户名标签和应用定义的字节Blob。
# - 处理：生产实现调用Advapi32，单元测试实现只在内存中模拟行为。
# - 输出：写入、读取和删除的稳定Python合同。
# - 为什么这样写：Linux沙盒无法调用Windows DLL，通过依赖注入仍可完整验证引用、编码、大小、错误和集成逻辑。
class WinCredentialApi(Protocol):
    """Minimal port over the WinCred API used by this module."""

    # 本段代码核心功能：定义创建或覆盖一个通用Windows凭据的底层端口。
    # - 输入：规范化目标名、非秘密用户名标签和应用Blob。
    # - 处理：由生产或测试实现完成实际保存。
    # - 输出：成功无返回值，失败由实现抛领域异常。
    # - 为什么这样写：领域类只依赖最小端口，不直接依赖ctypes DLL对象。
    def write_generic(self, *, target_name: str, username: str, secret_blob: bytes) -> None:
        """Create or replace one generic credential."""

    # 本段代码核心功能：定义按目标名读取通用Windows凭据的底层端口。
    # - 输入：规范化WJX目标名。
    # - 处理：由实现复制用户名标签和Blob。
    # - 输出：`(username, secret_blob)`或CredentialNotFoundError。
    # - 为什么这样写：读取端口只返回运行时需要的最小数据，不暴露凭据枚举能力。
    def read_generic(self, *, target_name: str) -> tuple[str, bytes]:
        """Return the username label and application-defined secret blob."""

    # 本段代码核心功能：定义删除一个通用Windows凭据的底层端口。
    # - 输入：规范化WJX目标名。
    # - 处理：由实现调用官方删除能力。
    # - 输出：成功无返回值，不存在或失败抛稳定异常。
    # - 为什么这样写：B2C撤销必须删除底层秘密，而不只是移除配置引用。
    def delete_generic(self, *, target_name: str) -> None:
        """Delete one generic credential."""


# 本段代码核心功能：定义CredReadW和CredWriteW共用的FILETIME布局。
# - 输入：由Windows API填充，不接受业务输入。
# - 处理：严格按Win32两个DWORD布局声明。
# - 输出：嵌入CREDENTIALW结构，写入时为零，读取时仅作结构占位。
# - 常量依据：Windows SDK FILETIME结构定义。
# - 为什么这样写：ctypes结构布局必须与官方ABI一致，否则可能读取错误内存。
class _FILETIME(ctypes.Structure):
    _fields_ = [
        ("dwLowDateTime", wintypes.DWORD),
        ("dwHighDateTime", wintypes.DWORD),
    ]


# 本段代码核心功能：定义WinCred Unicode凭据结构的ctypes布局。
# - 输入：写入时由本模块构造，读取时由CredReadW返回。
# - 处理：字段顺序和类型严格对应CREDENTIALW。
# - 输出：可传递给CredWriteW或从CredReadW指针读取。
# - 常量依据：微软wincred.h中的CREDENTIALW结构。
# - 为什么这样写：明确使用Unicode W版本可避免Windows本地代码页造成目标名和用户名损坏。
class _CREDENTIALW(ctypes.Structure):
    _fields_ = [
        ("Flags", wintypes.DWORD),
        ("Type", wintypes.DWORD),
        ("TargetName", wintypes.LPWSTR),
        ("Comment", wintypes.LPWSTR),
        ("LastWritten", _FILETIME),
        ("CredentialBlobSize", wintypes.DWORD),
        ("CredentialBlob", ctypes.POINTER(ctypes.c_ubyte)),
        ("Persist", wintypes.DWORD),
        ("AttributeCount", wintypes.DWORD),
        ("Attributes", ctypes.c_void_p),
        ("TargetAlias", wintypes.LPWSTR),
        ("UserName", wintypes.LPWSTR),
    ]


# 本段代码核心功能：通过ctypes对微软Advapi32 WinCred函数建立最薄生产适配层。
# - 输入：Windows当前用户会话、目标名、用户名标签和秘密Blob。
# - 处理：调用CredWriteW、CredReadW、CredDeleteW和CredFree；错误只返回操作名与Win32错误码。
# - 输出：实现WinCredentialApi协议，不保存额外明文副本。
# - 为什么这样写：直接复用Windows官方Credential Manager，无新增第三方运行依赖，也不实现任何自制密码算法。
class _CtypesWinCredentialApi:
    """Thin ctypes adapter over the official Windows Credential Manager API."""

    # 本段代码核心功能：加载Advapi32并声明四个WinCred函数签名。
    # - 输入：当前操作系统平台。
    # - 处理：非Windows立即失败；Windows使用use_last_error保证错误码来自同一线程的最近调用。
    # - 输出：初始化可用的DLL函数对象。
    # - 为什么这样写：生产后端只能在Windows显式启用，禁止静默降级到文件或环境变量。
    def __init__(self) -> None:
        if platform.system() != "Windows":
            raise UnsupportedCredentialPlatformError(
                "Windows Credential Manager backend requires Windows"
            )
        win_dll = getattr(ctypes, "WinDLL", None)
        if win_dll is None:
            raise UnsupportedCredentialPlatformError(
                "ctypes.WinDLL is unavailable on this Python runtime"
            )
        self._advapi32 = win_dll("Advapi32.dll", use_last_error=True)
        self._advapi32.CredWriteW.argtypes = [ctypes.POINTER(_CREDENTIALW), wintypes.DWORD]
        self._advapi32.CredWriteW.restype = wintypes.BOOL
        self._advapi32.CredReadW.argtypes = [
            wintypes.LPCWSTR,
            wintypes.DWORD,
            wintypes.DWORD,
            ctypes.POINTER(ctypes.POINTER(_CREDENTIALW)),
        ]
        self._advapi32.CredReadW.restype = wintypes.BOOL
        self._advapi32.CredDeleteW.argtypes = [
            wintypes.LPCWSTR,
            wintypes.DWORD,
            wintypes.DWORD,
        ]
        self._advapi32.CredDeleteW.restype = wintypes.BOOL
        self._advapi32.CredFree.argtypes = [ctypes.c_void_p]
        self._advapi32.CredFree.restype = None

    # 本段代码核心功能：把应用定义字节Blob写为当前用户的通用、本机持久凭据。
    # - 输入：已校验目标名、非秘密用户名标签和不超过2560字节的Blob。
    # - 处理：构造CREDENTIALW并调用CredWriteW，允许同目标覆盖更新。
    # - 输出：成功无返回值，失败抛出不含秘密的CredentialStoreError。
    # - 为什么这样写：CRED_TYPE_GENERIC不会被Windows认证包自动消费，适合Provider API Key和Token等应用秘密。
    def write_generic(self, *, target_name: str, username: str, secret_blob: bytes) -> None:
        blob_buffer = (ctypes.c_ubyte * len(secret_blob)).from_buffer_copy(secret_blob)
        credential = _CREDENTIALW()
        credential.Flags = 0
        credential.Type = CRED_TYPE_GENERIC
        credential.TargetName = target_name
        credential.Comment = "WJX provider secret"
        credential.CredentialBlobSize = len(secret_blob)
        credential.CredentialBlob = ctypes.cast(
            blob_buffer,
            ctypes.POINTER(ctypes.c_ubyte),
        )
        credential.Persist = CRED_PERSIST_LOCAL_MACHINE
        credential.AttributeCount = 0
        credential.Attributes = None
        credential.TargetAlias = None
        credential.UserName = username
        if not self._advapi32.CredWriteW(ctypes.byref(credential), 0):
            self._raise_last_error("CredWriteW")

    # 本段代码核心功能：从当前用户凭据集中读取一个通用凭据并复制出应用Blob。
    # - 输入：已校验的WJX目标名。
    # - 处理：调用CredReadW，复制用户名和Blob，并在finally中调用CredFree释放Windows分配的内存。
    # - 输出：`(username, secret_blob)`；不存在时抛CredentialNotFoundError。
    # - 为什么这样写：先复制再释放保证没有悬空指针，显式CredFree遵守官方内存所有权合同。
    def read_generic(self, *, target_name: str) -> tuple[str, bytes]:
        pointer = ctypes.POINTER(_CREDENTIALW)()
        if not self._advapi32.CredReadW(
            target_name,
            CRED_TYPE_GENERIC,
            0,
            ctypes.byref(pointer),
        ):
            error_code = ctypes.get_last_error()
            if error_code == ERROR_NOT_FOUND:
                raise CredentialNotFoundError("credential is not configured")
            self._raise_last_error("CredReadW", error_code=error_code)
        try:
            credential = pointer.contents
            username = credential.UserName or ""
            secret_blob = ctypes.string_at(
                credential.CredentialBlob,
                credential.CredentialBlobSize,
            )
            return username, secret_blob
        finally:
            self._advapi32.CredFree(ctypes.cast(pointer, ctypes.c_void_p))

    # 本段代码核心功能：删除当前用户凭据集中指定的通用凭据。
    # - 输入：已校验WJX目标名。
    # - 处理：调用CredDeleteW并映射ERROR_NOT_FOUND。
    # - 输出：成功无返回值，不存在或系统失败时抛稳定异常。
    # - 为什么这样写：B2C用户必须能够撤销和删除凭据，删除失败不能被静默忽略。
    def delete_generic(self, *, target_name: str) -> None:
        if not self._advapi32.CredDeleteW(target_name, CRED_TYPE_GENERIC, 0):
            error_code = ctypes.get_last_error()
            if error_code == ERROR_NOT_FOUND:
                raise CredentialNotFoundError("credential is not configured")
            self._raise_last_error("CredDeleteW", error_code=error_code)

    # 本段代码核心功能：把Win32最近错误转换为不含秘密材料的领域异常。
    # - 输入：固定操作名和可选错误码。
    # - 处理：未提供时读取ctypes线程本地last-error，只拼接操作名和数字码。
    # - 输出：抛出CredentialStoreError。
    # - 为什么这样写：错误诊断需要错误码，但不得把目标Blob、secret_value或请求对象格式化进异常。
    def _raise_last_error(self, operation: str, *, error_code: int | None = None) -> None:
        code = ctypes.get_last_error() if error_code is None else error_code
        raise CredentialStoreError(f"{operation} failed with Win32 error {code}")


# 本段代码核心功能：校验Provider、连接和字段标识符合接入中心的受控键名规则。
# - 输入：标识名称和值。
# - 处理：要求字符串去空白后完全匹配小写字母开头、仅含小写字母数字下划线的统一正则。
# - 输出：返回规范化标识；非法时抛ValueError。
# - 为什么这样写：这些标识会进入Windows目标名和安全引用，必须阻断路径、URI分隔符、命令和日志混淆字符。
def _normalize_identifier(name: str, value: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{name} must be a string")
    normalized = value.strip()
    if not IDENTIFIER_PATTERN.fullmatch(normalized):
        raise ValueError(f"invalid {name}")
    return normalized


# 本段代码核心功能：从三个受控标识生成稳定Windows目标名和可持久化安全引用。
# - 输入：provider_id、connection_id和field_id。
# - 处理：统一规范化后使用固定WJX命名空间拼接目标名与URI。
# - 输出：不可变CredentialLocation。
# - 为什么这样写：目标名与引用必须一一对应，配置只保存引用，运行时再受控解析到目标名。
def build_credential_location(
    *,
    provider_id: str,
    connection_id: str,
    field_id: str,
) -> CredentialLocation:
    provider = _normalize_identifier("provider_id", provider_id)
    connection = _normalize_identifier("connection_id", connection_id)
    field = _normalize_identifier("field_id", field_id)
    target_name = f"{TARGET_PREFIX}/{provider}/{connection}/{field}"
    reference = (
        f"{REFERENCE_SCHEME}://{REFERENCE_AUTHORITY}/provider/"
        f"{provider}/{connection}/{field}"
    )
    return CredentialLocation(
        provider_id=provider,
        connection_id=connection,
        field_id=field,
        target_name=target_name,
        reference=reference,
    )


# 本段代码核心功能：把持久化安全引用解析回WJX受控目标位置。
# - 输入：配置、数据库或运行请求中的reference字符串。
# - 处理：检查scheme、authority、固定provider路径、段数和每个标识；再与标准生成结果比对。
# - 输出：合法CredentialLocation；非法或非WJX引用时抛InvalidCredentialReferenceError。
# - 为什么这样写：运行时只允许访问本项目命名空间，不能把任意Credential Manager目标名作为引用注入。
def parse_credential_reference(reference: str) -> CredentialLocation:
    if not isinstance(reference, str) or not reference.strip():
        raise InvalidCredentialReferenceError("credential reference must be a non-empty string")
    parsed = urlsplit(reference.strip())
    path_parts = tuple(part for part in parsed.path.split("/") if part)
    if (
        parsed.scheme != REFERENCE_SCHEME
        or parsed.netloc.lower() != REFERENCE_AUTHORITY.lower()
        or len(path_parts) != 4
        or path_parts[0] != "provider"
        or parsed.query
        or parsed.fragment
    ):
        raise InvalidCredentialReferenceError("credential reference is outside WJX namespace")
    try:
        location = build_credential_location(
            provider_id=path_parts[1],
            connection_id=path_parts[2],
            field_id=path_parts[3],
        )
    except ValueError as exc:
        raise InvalidCredentialReferenceError("credential reference contains invalid identifiers") from exc
    if location.reference != reference.strip():
        raise InvalidCredentialReferenceError("credential reference is not canonical")
    return location


# 本段代码核心功能：把秘密文本编码成带版本前缀的可移植应用Blob并执行官方大小上限检查。
# - 输入：本次请求内存中的secret_value。
# - 处理：拒绝非字符串和空值，使用UTF-8编码并添加WJX1前缀，检查总字节数不超过2560。
# - 输出：交给WinCred API的bytes；异常不回显秘密内容。
# - 为什么这样写：CRED_TYPE_GENERIC的Blob由应用定义，版本前缀便于未来迁移，UTF-8保证跨Python版本稳定解码。
def _encode_secret(secret_value: str) -> bytes:
    if not isinstance(secret_value, str):
        raise ValueError("secret_value must be a string")
    if not secret_value:
        raise ValueError("secret_value must not be empty")
    payload = PAYLOAD_PREFIX + secret_value.encode("utf-8")
    if len(payload) > CRED_MAX_CREDENTIAL_BLOB_SIZE:
        raise ValueError(
            f"secret_value exceeds Windows Credential Manager limit of "
            f"{CRED_MAX_CREDENTIAL_BLOB_SIZE} bytes"
        )
    return payload


# 本段代码核心功能：校验并解码从WinCred读取的WJX应用Blob。
# - 输入：Windows Credential Manager返回的原始bytes。
# - 处理：要求WJX1版本前缀并按严格UTF-8解码。
# - 输出：仅返回给受控运行时调用方的秘密字符串。
# - 为什么这样写：拒绝未知格式可避免把其他应用或旧格式Blob误当作Provider秘密使用。
def _decode_secret(secret_blob: bytes) -> str:
    if not isinstance(secret_blob, bytes) or not secret_blob.startswith(PAYLOAD_PREFIX):
        raise CredentialStoreError("credential payload format is not recognized")
    try:
        return secret_blob[len(PAYLOAD_PREFIX) :].decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise CredentialStoreError("credential payload is not valid UTF-8") from exc


# 本段代码核心功能：向Provider接入中心提供Windows秘密写入、运行时读取、存在检查和撤销删除能力。
# - 输入：可选WinCredentialApi；生产默认使用官方ctypes适配器，测试注入假实现。
# - 处理：所有公开方法先构建或解析受控引用，再调用底层API；不保存secret_value实例属性。
# - 输出：安全引用、按需秘密、布尔配置状态或删除结果。
# - 为什么这样写：单一类既满足TASK_024C的store_secret协议，又为后续只读SDK连接测试提供受控解析接口。
class WindowsCredentialStore:
    """WJX provider-secret store backed by Windows Credential Manager."""

    # 本段代码核心功能：选择生产WinCred适配器或测试注入后端。
    # - 输入：可选api对象。
    # - 处理：未提供时初始化_CtypesWinCredentialApi；提供时仅保存端口对象。
    # - 输出：可用WindowsCredentialStore实例。
    # - 为什么这样写：生产路径始终使用官方Windows后端，单元测试无需Windows或真实用户凭据集。
    def __init__(self, api: WinCredentialApi | None = None) -> None:
        self._api = api if api is not None else _CtypesWinCredentialApi()

    # 本段代码核心功能：实现TASK_024C的CredentialReferenceWriter.store_secret协议。
    # - 输入：Provider、连接、字段标识和秘密原文。
    # - 处理：生成受控位置、编码Blob并写入官方凭据集，方法结束后对象不保留秘密。
    # - 输出：可安全保存到连接档案的windows-credential引用。
    # - 为什么这样写：秘密接收和安全存储位于同一调用边界，消除先写临时JSON或日志的泄密窗口。
    def store_secret(
        self,
        *,
        provider_id: str,
        connection_id: str,
        field_id: str,
        secret_value: str,
    ) -> str:
        location = build_credential_location(
            provider_id=provider_id,
            connection_id=connection_id,
            field_id=field_id,
        )
        secret_blob = _encode_secret(secret_value)
        username = f"{location.provider_id}:{location.connection_id}:{location.field_id}"
        self._api.write_generic(
            target_name=location.target_name,
            username=username,
            secret_blob=secret_blob,
        )
        return location.reference

    # 本段代码核心功能：为受控Provider运行时按引用解析秘密。
    # - 输入：连接档案中的windows-credential引用。
    # - 处理：解析命名空间，调用WinCred读取，校验用户名标签和WJX1载荷格式。
    # - 输出：秘密字符串，仅存在于调用方本次运行内存；不返回给普通UI或报告。
    # - 为什么这样写：SDK连接必须拿到实际Token，但读取能力与UI展示、配置持久化严格分离。
    def resolve_secret(self, reference: str) -> str:
        location = parse_credential_reference(reference)
        username, secret_blob = self._api.read_generic(target_name=location.target_name)
        expected_username = (
            f"{location.provider_id}:{location.connection_id}:{location.field_id}"
        )
        if username != expected_username:
            raise CredentialStoreError("credential username label does not match reference")
        return _decode_secret(secret_blob)

    # 本段代码核心功能：以不读取和不回显秘密原文的方式检查引用是否已配置。
    # - 输入：受控凭据引用。
    # - 处理：调用底层读取，仅判断成功或CredentialNotFoundError；读取结果立即丢弃。
    # - 输出：True表示当前用户凭据集中存在，False表示未配置。
    # - 为什么这样写：B2C卡片只需要“已配置/未配置”，不能为了状态显示把秘密发送到前端。
    def secret_exists(self, reference: str) -> bool:
        location = parse_credential_reference(reference)
        try:
            self._api.read_generic(target_name=location.target_name)
        except CredentialNotFoundError:
            return False
        return True

    # 本段代码核心功能：撤销并删除一个Provider秘密。
    # - 输入：受控凭据引用。
    # - 处理：解析WJX命名空间后调用CredDeleteW适配器。
    # - 输出：成功无返回值；不存在或系统错误显式抛出。
    # - 为什么这样写：用户必须能够从B2C界面删除凭据，不能只删除配置引用而把秘密遗留在操作系统中。
    def delete_secret(self, reference: str) -> None:
        location = parse_credential_reference(reference)
        self._api.delete_generic(target_name=location.target_name)

    # 本段代码核心功能：生成可直接返回B2C卡片的无秘密状态对象。
    # - 输入：受控凭据引用。
    # - 处理：只执行存在检查，不解析秘密文本。
    # - 输出：后端类型、引用和configured布尔值，不包含用户名或Blob。
    # - 为什么这样写：统一安全ViewModel防止后续页面开发者为了显示状态直接调用resolve_secret。
    def build_safe_status(self, reference: str) -> dict[str, object]:
        location = parse_credential_reference(reference)
        return {
            "backend": "WINDOWS_CREDENTIAL_MANAGER",
            "reference": location.reference,
            "configured": self.secret_exists(location.reference),
            "secret_value": None,
        }
