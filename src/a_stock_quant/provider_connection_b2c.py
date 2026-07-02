# 本文件核心功能：把已有Provider接入领域合同、Windows凭据后端和未来只读测试器组合成可供B2C页面调用的应用服务与本地HTTP接口。
# - 输入：官方Provider定义、用户通过本地页面提交的表单、无秘密连接档案、Windows凭据引用和可选只读测试器。
# - 处理：生成安全卡片与动态表单、事务式保存秘密、原子保存无秘密档案、执行显式状态迁移、限制本地HTTP请求并阻断CSRF。
# - 输出：JSON可序列化的Provider卡片、表单、无秘密档案、测试结果和撤销结果；任何普通响应都不包含API Key、Token或密码原文。
# - 常量依据：TASK_024C领域合同、TASK_024D Windows Credential Manager后端、JSON Schema 2020-12和B2C双视图权威架构。
# - 为什么这样写：页面、后端和安全存储必须通过同一应用层组合，避免UI直接写配置、直接读秘密或绕过连接状态机。
"""B2C application service and local WSGI API for provider connections."""

from __future__ import annotations

import json
import os
import secrets
import tempfile
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Mapping, Protocol, Sequence
from urllib.parse import unquote

from a_stock_quant.provider_connection_center import (
    ConnectionStatus,
    ProviderConnectionDefinition,
    ProviderConnectionProfile,
    build_connection_center_view,
    build_dynamic_form_schema,
    submit_connection_form,
    transition_connection_status,
)
from a_stock_quant.provider_connection_page import render_provider_connection_page
from a_stock_quant.windows_credential_store import (
    CredentialNotFoundError,
    WindowsCredentialStore,
    build_credential_location,
    parse_credential_reference,
)

# 本段代码核心功能：保存连接档案文件的版本、请求大小和本地HTTP安全常量。
# - 输入：无运行时输入，值来自当前MVP文件结构和本地单用户页面边界。
# - 处理：作为仓储、请求解析和安全响应头的统一事实源。
# - 输出：后续函数使用稳定常量，不在各路由散落魔法数字。
# - 常量依据：64KiB足以容纳连接表单且能阻断异常大请求；同源CSRF令牌使用256位随机值。
# - 为什么这样写：集中常量便于审计和后续升级，不把资源限制隐藏在实现细节里。
PROFILE_STORE_SCHEMA_VERSION = 1
MAX_REQUEST_BYTES = 64 * 1024
CSRF_HEADER = "HTTP_X_WJX_CSRF_TOKEN"
JSON_CONTENT_TYPE = "application/json; charset=utf-8"
HTML_CONTENT_TYPE = "text/html; charset=utf-8"
LOOPBACK_ADDRESSES = frozenset({"127.0.0.1", "::1", "localhost"})


# 本段代码核心功能：定义连接档案仓储的最小端口。
# - 输入：ProviderConnectionProfile对象或provider_id。
# - 处理：由JSON文件实现或测试假实现负责读取、保存和删除。
# - 输出：无秘密档案集合，不承担任何秘密存储职责。
# - 为什么这样写：应用服务依赖接口而不是固定文件路径，便于后续切换SQLite或统一配置服务而不改页面和领域逻辑。
class ProviderConnectionProfileRepository(Protocol):
    """Persistence port for secret-free provider profiles."""

    # 本段代码核心功能：定义读取全部无秘密Provider档案的仓储端口。
    # - 输入：无，具体实现从本机受控存储读取档案。
    # - 处理：按provider_id建立索引，禁止返回任何秘密原文。
    # - 输出：provider_id到ProviderConnectionProfile的映射。
    # - 为什么这样写：页面和应用服务只依赖统一读取合同，后续替换JSON或SQLite时无需修改业务逻辑。
    def load_all(self) -> dict[str, ProviderConnectionProfile]:
        """Return all profiles keyed by provider_id."""

    # 本段代码核心功能：定义创建或替换一个无秘密Provider档案的仓储端口。
    # - 输入：ProviderConnectionProfile。
    # - 处理：由具体仓储实现持久化。
    # - 输出：成功无返回值。
    # - 为什么这样写：应用服务只依赖端口，不绑定JSON文件。
    def save(self, profile: ProviderConnectionProfile) -> None:
        """Create or replace one profile."""

    # 本段代码核心功能：定义按Provider标识删除档案的仓储端口。
    # - 输入：provider_id。
    # - 处理：由具体仓储实现幂等删除。
    # - 输出：成功无返回值。
    # - 为什么这样写：停用动作需要同时治理凭据和无秘密档案。
    def delete(self, provider_id: str) -> None:
        """Delete one profile if it exists."""


# 本段代码核心功能：定义TASK_024F及后续Provider薄适配器必须实现的只读连接测试端口。
# - 输入：无秘密连接档案和按引用解析秘密的受控函数。
# - 处理：实现方只执行最小只读探针，不启用下单、撤单、资金划转或交易会话。
# - 输出：结构化ReadOnlyConnectionTestResult，不返回秘密、账户完整信息或原始SDK对象。
# - 为什么这样写：TASK_024E先完成统一页面和状态机，具体券商连接逻辑通过薄适配器延后接入，避免把UI绑定到某一家SDK。
class ProviderReadOnlyConnectionTester(Protocol):
    """Port implemented by one authorized provider read-only tester."""

    # 本段代码核心功能：定义正式Provider薄适配器执行一次只读连接探针的端口。
    # - 输入：无秘密连接档案和按安全引用解析秘密的受控函数。
    # - 处理：实现方只能验证登录、授权或行情读取，不得发起交易动作。
    # - 输出：不含秘密和完整账户信息的ReadOnlyConnectionTestResult。
    # - 为什么这样写：统一测试端口让B2C页面不绑定具体SDK，同时把交易能力保持在阻断状态。
    def run(
        self,
        *,
        profile: ProviderConnectionProfile,
        resolve_secret: Callable[[str], str],
    ) -> "ReadOnlyConnectionTestResult":
        """Run one non-trading connection probe."""


# 本段代码核心功能：保存一次只读连接测试的用户可见、安全结果。
# - 输入：测试器给出的成功标志、摘要、观察项、警告和可选能力代码。
# - 处理：使用不可变对象保存，不接受秘密值、完整账户号或SDK会话对象。
# - 输出：可写入HTTP响应和验收报告的白箱测试结果。
# - 常量依据：时间统一使用UTC ISO-8601，能力代码由后续Provider协议治理。
# - 为什么这样写：连接“成功/失败”之外还需要解释测试了什么、警告是什么，同时必须限制输出边界。
@dataclass(frozen=True)
class ReadOnlyConnectionTestResult:
    """Secret-free outcome of one provider read-only probe."""

    success: bool
    summary: str
    observations: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    capability_codes: tuple[str, ...] = ()
    tested_at: str = ""

    # 本段代码核心功能：为未显式提供时间的测试结果补充UTC时间。
    # - 输入：当前不可变结果对象。
    # - 处理：已有tested_at时原样返回，否则创建带时区的ISO-8601时间。
    # - 输出：始终含tested_at的结果对象。
    # - 为什么这样写：测试器可以在可重复测试中固定时间，生产路径又能自动记录实际执行时点。
    def with_timestamp(self) -> "ReadOnlyConnectionTestResult":
        if self.tested_at:
            return self
        return replace(
            self,
            tested_at=datetime.now(timezone.utc).isoformat(),
        )


# 本段代码核心功能：定义应用层可安全映射到HTTP状态码的业务异常。
# - 输入：稳定错误代码、用户可读消息和HTTP状态。
# - 处理：保存不含秘密的有限信息，不拼接submitted_values或底层SDK异常全文。
# - 输出：WSGI适配器返回一致JSON错误结构。
# - 为什么这样写：普通ValueError、文件错误和SDK错误不能直接回显给页面，否则可能泄露路径、秘密或内部实现。
class ProviderConnectionApplicationError(RuntimeError):
    """Safe application error suitable for a B2C response."""

    # 本段代码核心功能：初始化一个可安全返回B2C页面的应用层错误。
    # - 输入：稳定错误代码、用户可读消息和HTTP状态码。
    # - 处理：只保存经过审查的安全信息，不保留秘密值或底层异常全文。
    # - 输出：供WSGI层映射为统一JSON错误的异常对象。
    # - 为什么这样写：浏览器不能直接看到文件路径、SDK内部状态或可能含秘密的原始异常。
    def __init__(self, code: str, message: str, *, http_status: int = 400) -> None:
        super().__init__(message)
        self.code = code
        self.safe_message = message
        self.http_status = http_status


# 本段代码核心功能：计算无秘密连接档案的默认本地保存路径。
# - 输入：可选环境变量LOCALAPPDATA和用户主目录。
# - 处理：Windows优先使用当前用户LocalAppData；其他平台仅用于测试时回退到用户目录。
# - 输出：`.../WJX/provider_connection_profiles.json`路径。
# - 为什么这样写：运行配置不应写进Git仓库，且档案虽然无秘密仍属于用户本机状态。
def default_profile_store_path() -> Path:
    local_app_data = os.environ.get("LOCALAPPDATA", "").strip()
    base = Path(local_app_data) if local_app_data else Path.home() / ".wjx"
    return base / "WJX" / "provider_connection_profiles.json"


# 本段代码核心功能：把ProviderConnectionProfile转换成可持久化但绝不含秘密原文的普通字典。
# - 输入：领域层已经生成的无秘密档案。
# - 处理：显式列出允许字段，把枚举转换为稳定字符串，并复制映射避免共享可变对象。
# - 输出：JSON可序列化字典。
# - 为什么这样写：显式白名单比asdict后直接落盘更安全，未来领域对象增加字段时不会自动把未审查内容写入文件。
def _profile_to_payload(profile: ProviderConnectionProfile) -> dict[str, object]:
    return {
        "provider_id": profile.provider_id,
        "connection_id": profile.connection_id,
        "status": profile.status.value,
        "public_configuration": dict(profile.public_configuration),
        "credential_references": dict(profile.credential_references),
        "official_authorization_confirmed": profile.official_authorization_confirmed,
        "read_only_entitlement_confirmed": profile.read_only_entitlement_confirmed,
        "execution_domain_isolated": profile.execution_domain_isolated,
    }


# 本段代码核心功能：从本地JSON恢复严格的ProviderConnectionProfile。
# - 输入：单个档案JSON对象。
# - 处理：执行类型、状态、映射和布尔值校验，只接受领域对象声明的字段。
# - 输出：不可变ProviderConnectionProfile；非法文件立即失败关闭。
# - 为什么这样写：本地档案可能被旧版本或人工修改，加载时不能宽松猜测并把错误配置传给SDK。
def _profile_from_payload(payload: object) -> ProviderConnectionProfile:
    if not isinstance(payload, dict):
        raise ValueError("profile entry must be an object")
    allowed = {
        "provider_id",
        "connection_id",
        "status",
        "public_configuration",
        "credential_references",
        "official_authorization_confirmed",
        "read_only_entitlement_confirmed",
        "execution_domain_isolated",
    }
    unknown = set(payload) - allowed
    if unknown:
        raise ValueError("profile entry contains unsupported fields")
    public_configuration = payload.get("public_configuration")
    credential_references = payload.get("credential_references")
    if not isinstance(public_configuration, dict):
        raise ValueError("public_configuration must be an object")
    if not isinstance(credential_references, dict):
        raise ValueError("credential_references must be an object")
    if not all(isinstance(key, str) and isinstance(value, str) for key, value in credential_references.items()):
        raise ValueError("credential_references must contain string pairs")
    boolean_fields = (
        "official_authorization_confirmed",
        "read_only_entitlement_confirmed",
        "execution_domain_isolated",
    )
    if not all(isinstance(payload.get(name), bool) for name in boolean_fields):
        raise ValueError("profile confirmation fields must be booleans")
    return ProviderConnectionProfile(
        provider_id=str(payload.get("provider_id", "")),
        connection_id=str(payload.get("connection_id", "")),
        status=ConnectionStatus(str(payload.get("status", ""))),
        public_configuration=dict(public_configuration),
        credential_references=dict(credential_references),
        official_authorization_confirmed=bool(payload["official_authorization_confirmed"]),
        read_only_entitlement_confirmed=bool(payload["read_only_entitlement_confirmed"]),
        execution_domain_isolated=bool(payload["execution_domain_isolated"]),
    )


# 本段代码核心功能：把无秘密连接档案原子保存到用户本地JSON文件。
# - 输入：目标路径和ProviderConnectionProfile。
# - 处理：严格加载、以provider_id覆盖、写临时文件、flush与fsync后os.replace原子替换。
# - 输出：崩溃时保留旧文件，成功时得到版本化档案集合。
# - 为什么这样写：页面提交不能先清空旧配置再写新配置；原子替换可以降低断电或异常导致的文件损坏风险。
class JsonProviderConnectionProfileRepository:
    """Atomic JSON repository for secret-free connection profiles."""

    # 本段代码核心功能：初始化无秘密连接档案的原子JSON仓储。
    # - 输入：可选显式文件路径；未提供时使用当前用户本机默认路径。
    # - 处理：仅保存目标路径，不在初始化阶段读写文件。
    # - 输出：后续load、save和delete共享的仓储实例。
    # - 为什么这样写：显式注入路径便于测试和迁移，默认路径又能避免把运行配置写进Git仓库。
    def __init__(self, path: Path | None = None) -> None:
        self.path = path if path is not None else default_profile_store_path()

    # 本段代码核心功能：读取全部无秘密档案并按provider_id建立索引。
    # - 输入：本地JSON文件；文件不存在视为空集合。
    # - 处理：校验schema_version、profiles数组、对象内容和provider_id唯一性。
    # - 输出：新的字典副本，不暴露内部可变状态。
    # - 为什么这样写：启动阶段一次性暴露损坏或重复档案，避免页面显示与后端操作不一致。
    def load_all(self) -> dict[str, ProviderConnectionProfile]:
        if not self.path.exists():
            return {}
        raw = json.loads(self.path.read_text(encoding="utf-8-sig"))
        if not isinstance(raw, dict):
            raise ValueError("profile store must be an object")
        if raw.get("schema_version") != PROFILE_STORE_SCHEMA_VERSION:
            raise ValueError("unsupported profile store schema_version")
        profiles_raw = raw.get("profiles")
        if not isinstance(profiles_raw, list):
            raise ValueError("profile store profiles must be a list")
        result: dict[str, ProviderConnectionProfile] = {}
        for item in profiles_raw:
            profile = _profile_from_payload(item)
            if not profile.provider_id or profile.provider_id in result:
                raise ValueError("profile store contains invalid or duplicate provider_id")
            result[profile.provider_id] = profile
        return result

    # 本段代码核心功能：创建或替换一个Provider的无秘密档案。
    # - 输入：ProviderConnectionProfile。
    # - 处理：加载旧集合、覆盖同provider_id对象并调用原子写入。
    # - 输出：磁盘上的稳定档案文件。
    # - 为什么这样写：一个Provider在个人版接入中心只保留一个活动连接，减少多账户与权限混淆。
    def save(self, profile: ProviderConnectionProfile) -> None:
        profiles = self.load_all()
        profiles[profile.provider_id] = profile
        self._write_all(profiles)

    # 本段代码核心功能：删除一个Provider的无秘密档案。
    # - 输入：provider_id。
    # - 处理：不存在时幂等返回，存在时删除并原子写入剩余集合。
    # - 输出：不再包含该Provider的档案文件。
    # - 为什么这样写：撤销动作可能因UI重试重复发送，幂等删除能避免无意义失败。
    def delete(self, provider_id: str) -> None:
        profiles = self.load_all()
        if provider_id not in profiles:
            return
        del profiles[provider_id]
        self._write_all(profiles)

    # 本段代码核心功能：把完整档案集合写入临时文件后原子替换目标文件。
    # - 输入：按provider_id索引的档案映射。
    # - 处理：稳定排序、UTF-8序列化、fsync、os.replace，并在失败时删除临时文件。
    # - 输出：版本化且无秘密的JSON文件。
    # - 为什么这样写：稳定排序便于审计，临时文件与目标位于同目录以保证os.replace原子性。
    def _write_all(self, profiles: Mapping[str, ProviderConnectionProfile]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": PROFILE_STORE_SCHEMA_VERSION,
            "profiles": [
                _profile_to_payload(profiles[provider_id])
                for provider_id in sorted(profiles)
            ],
        }
        encoded = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{self.path.name}.",
            suffix=".tmp",
            dir=str(self.path.parent),
            text=True,
        )
        temporary_path = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(encoded)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary_path, self.path)
        except Exception:
            temporary_path.unlink(missing_ok=True)
            raise


# 本段代码核心功能：在一次表单提交中为多个秘密字段提供尽可能接近事务的写入与回滚。
# - 输入：WindowsCredentialStore和每次store_secret调用。
# - 处理：写前记录旧秘密是否存在及原值，失败时恢复旧值或删除新值，成功后显式commit清空回滚材料。
# - 输出：满足CredentialReferenceWriter协议的安全引用。
# - 为什么这样写：Windows Credential Manager没有跨多个凭据的事务，应用层必须防止第二个字段失败后留下半套新凭据。
class _TransactionalCredentialWriter:
    # 本段代码核心功能：初始化一次表单提交范围内的凭据事务协调器。
    # - 输入：已经通过TASK_024D验证的WindowsCredentialStore。
    # - 处理：建立空回滚记录和未提交状态，不立即读取或写入秘密。
    # - 输出：后续多个秘密字段共享的事务式写入对象。
    # - 为什么这样写：Windows凭据管理器没有多凭据原子事务，必须在应用层记录可逆操作。
    def __init__(self, store: WindowsCredentialStore) -> None:
        self._store = store
        self._undo: list[tuple[str, str | None]] = []
        self._committed = False

    # 本段代码核心功能：保存一个秘密并记录可逆操作。
    # - 输入：Provider、连接、字段标识和秘密值。
    # - 处理：先构造引用，存在时读取旧值，再写新值并记录旧状态。
    # - 输出：标准windows-credential引用。
    # - 为什么这样写：只有在内存中短暂保存旧值才能在档案持久化失败时恢复此前可用连接。
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
        old_value: str | None = None
        if self._store.secret_exists(location.reference):
            old_value = self._store.resolve_secret(location.reference)
        reference = self._store.store_secret(
            provider_id=provider_id,
            connection_id=connection_id,
            field_id=field_id,
            secret_value=secret_value,
        )
        self._undo.append((reference, old_value))
        return reference

    # 本段代码核心功能：确认档案已经持久化并销毁回滚材料。
    # - 输入：无。
    # - 处理：标记已提交并清空旧秘密列表。
    # - 输出：后续rollback不再执行。
    # - 为什么这样写：旧秘密不应在应用服务对象中保留超过单次请求生命周期。
    def commit(self) -> None:
        self._committed = True
        self._undo.clear()

    # 本段代码核心功能：倒序恢复本次请求覆盖或新增的秘密。
    # - 输入：此前记录的引用和旧值。
    # - 处理：有旧值时重新写回，无旧值时删除新凭据；不存在删除视为幂等。
    # - 输出：恢复请求前状态，随后清空回滚材料。
    # - 为什么这样写：倒序撤销与写入顺序相反，可降低多字段依赖时的恢复风险。
    def rollback(self) -> None:
        if self._committed:
            return
        for reference, old_value in reversed(self._undo):
            location = parse_credential_reference(reference)
            if old_value is None:
                try:
                    self._store.delete_secret(reference)
                except CredentialNotFoundError:
                    pass
            else:
                self._store.store_secret(
                    provider_id=location.provider_id,
                    connection_id=location.connection_id,
                    field_id=location.field_id,
                    secret_value=old_value,
                )
        self._undo.clear()


# 本段代码核心功能：把连接档案转换成B2C可见的无秘密对象。
# - 输入：ProviderConnectionProfile和WindowsCredentialStore。
# - 处理：公开配置直接复制，凭据仅生成configured状态，不解析秘密文本。
# - 输出：可安全返回页面的profile字典。
# - 为什么这样写：页面需要知道哪些字段已配置，但绝不能获得秘密或用占位星号暗示秘密长度。
def _safe_profile_view(
    profile: ProviderConnectionProfile,
    credential_store: WindowsCredentialStore,
) -> dict[str, object]:
    credential_status = {
        field_id: credential_store.build_safe_status(reference)
        for field_id, reference in profile.credential_references.items()
    }
    return {
        "provider_id": profile.provider_id,
        "connection_id": profile.connection_id,
        "status": profile.status.value,
        "public_configuration": dict(profile.public_configuration),
        "credential_status": credential_status,
        "official_authorization_confirmed": profile.official_authorization_confirmed,
        "read_only_entitlement_confirmed": profile.read_only_entitlement_confirmed,
        "execution_domain_isolated": profile.execution_domain_isolated,
    }


# 本段代码核心功能：组合Provider领域合同、档案仓储、Windows凭据和只读测试器，为页面提供单一应用入口。
# - 输入：Provider定义序列、仓储、凭据后端、环境状态和测试器注册表。
# - 处理：执行查询、提交、测试和撤销四类用例，统一安全错误和状态迁移。
# - 输出：所有方法仅返回无秘密字典。
# - 为什么这样写：UI不应自行拼接领域函数，单一应用服务可确保桌面UI、Web UI和测试工具共享同一门禁。
class ProviderConnectionCenterService:
    """Application service used by the provider connection-center UI."""

    # 本段代码核心功能：初始化接入中心的统一应用服务与依赖注册表。
    # - 输入：Provider定义、无秘密档案仓储、Windows凭据后端、环境状态和可选只读测试器。
    # - 处理：校验Provider标识唯一性并构建只读映射，不在初始化时连接外部SDK。
    # - 输出：供页面查询、提交、测试和停用操作复用的服务实例。
    # - 为什么这样写：依赖集中注入可以保持UI、领域合同和具体Provider薄适配器相互解耦。
    def __init__(
        self,
        *,
        definitions: Sequence[ProviderConnectionDefinition],
        profile_repository: ProviderConnectionProfileRepository,
        credential_store: WindowsCredentialStore,
        environment_status: Mapping[str, str] | None = None,
        testers: Mapping[str, ProviderReadOnlyConnectionTester] | None = None,
    ) -> None:
        definition_tuple = tuple(definitions)
        definition_map = {definition.provider_id: definition for definition in definition_tuple}
        if len(definition_map) != len(definition_tuple):
            raise ValueError("duplicate provider definitions")
        self._definitions = definition_tuple
        self._definition_map = definition_map
        self._profiles = profile_repository
        self._credential_store = credential_store
        self._environment_status = dict(environment_status or {})
        self._testers = dict(testers or {})

    # 本段代码核心功能：生成接入中心首页Provider卡片及动作可用性。
    # - 输入：当前定义、档案、环境状态和测试器注册表。
    # - 处理：复用TASK_024C卡片构建器，再补充页面级动作是否真正有后端实现及阻断原因。
    # - 输出：无秘密卡片列表。
    # - 为什么这样写：领域层决定“理论允许动作”，应用层再说明“当前实现是否就绪”，避免页面显示可点击但后端尚未接入的测试按钮。
    def list_cards(self) -> list[dict[str, object]]:
        profiles = self._profiles.load_all()
        cards = build_connection_center_view(
            self._definitions,
            profiles=profiles,
            environment_status=self._environment_status,
        )
        for card in cards:
            provider_id = str(card["provider_id"])
            card["action_availability"] = {
                "OPEN_CONNECTION_FORM": {
                    "available": "OPEN_CONNECTION_FORM" in card.get("available_actions", []),
                    "reason": "",
                },
                "RUN_READ_ONLY_CONNECTION_TEST": {
                    "available": provider_id in self._testers
                    and "RUN_READ_ONLY_CONNECTION_TEST" in card.get("available_actions", []),
                    "reason": "" if provider_id in self._testers else "等待TASK_024F接入首个官方只读测试器",
                },
                "DISABLE_CONNECTION": {
                    "available": provider_id in profiles,
                    "reason": "",
                },
            }
        return cards

    # 本段代码核心功能：返回一个Provider的动态表单、公开旧值和凭据配置状态。
    # - 输入：provider_id。
    # - 处理：查找官方定义、生成JSON Schema，并在存在档案时生成安全profile视图。
    # - 输出：页面渲染所需对象，不回显任何秘密字段值。
    # - 为什么这样写：表单定义和提交验证都来自同一领域合同，页面只负责渲染而不重复实现字段规则。
    def get_form(self, provider_id: str) -> dict[str, object]:
        definition = self._require_definition(provider_id)
        profiles = self._profiles.load_all()
        profile = profiles.get(provider_id)
        return {
            "provider": {
                "provider_id": definition.provider_id,
                "display_name": definition.display_name,
                "provider_kind": definition.provider_kind,
                "authority_tier": definition.authority_tier,
                "official_application_reference": definition.official_application_reference,
                "form_definition_status": definition.form_definition_status,
                "supports_read_only_data": definition.supports_read_only_data,
                "execution_activation": "BLOCKED",
            },
            "schema": build_dynamic_form_schema(definition),
            "profile": (
                _safe_profile_view(profile, self._credential_store)
                if profile is not None
                else None
            ),
            "security_notice": "秘密值只写入Windows凭据管理器，页面和档案不会回显或保存原文。",
        }

    # 本段代码核心功能：接收页面表单并事务式生成Windows凭据引用与无秘密档案。
    # - 输入：provider_id、connection_id、字段值和三个授权确认布尔值。
    # - 处理：阻止更换活动connection_id；复用领域提交校验；档案保存失败时回滚秘密；成功后返回安全视图。
    # - 输出：无秘密档案和更新后的Provider卡片。
    # - 为什么这样写：秘密写入与档案持久化必须处于同一应用事务边界，不能先落临时JSON再异步转存。
    def submit_connection(
        self,
        *,
        provider_id: str,
        connection_id: str,
        values: Mapping[str, object],
        official_authorization_confirmed: bool,
        read_only_entitlement_confirmed: bool,
        execution_domain_isolated: bool,
    ) -> dict[str, object]:
        definition = self._require_definition(provider_id)
        profiles = self._profiles.load_all()
        existing = profiles.get(provider_id)
        if existing is not None and existing.connection_id != connection_id.strip():
            raise ProviderConnectionApplicationError(
                "CONNECTION_ID_CHANGE_REQUIRES_DISABLE",
                "如需更换连接标识，请先在界面停用现有连接。",
                http_status=409,
            )
        writer = _TransactionalCredentialWriter(self._credential_store)
        try:
            profile = submit_connection_form(
                definition,
                connection_id=connection_id,
                submitted_values=values,
                official_authorization_confirmed=official_authorization_confirmed,
                read_only_entitlement_confirmed=read_only_entitlement_confirmed,
                execution_domain_isolated=execution_domain_isolated,
                credential_writer=writer,
            )
            self._profiles.save(profile)
        except ProviderConnectionApplicationError:
            writer.rollback()
            raise
        except ValueError as exc:
            writer.rollback()
            raise ProviderConnectionApplicationError(
                "INVALID_CONNECTION_FORM",
                str(exc),
                http_status=400,
            ) from exc
        except Exception as exc:
            writer.rollback()
            raise ProviderConnectionApplicationError(
                "CONNECTION_SAVE_FAILED",
                "连接未保存，系统已尝试恢复提交前状态。",
                http_status=500,
            ) from exc
        writer.commit()
        return {
            "profile": _safe_profile_view(profile, self._credential_store),
            "cards": self.list_cards(),
        }

    # 本段代码核心功能：调用已注册Provider只读测试器并严格执行连接状态迁移。
    # - 输入：provider_id和当前无秘密档案。
    # - 处理：检查测试器、转为PENDING、执行探针、根据结果转为VERIFIED或FAILED并保存。
    # - 输出：安全测试结果和更新档案。
    # - 为什么这样写：测试过程和状态变化必须留下档案，且任何底层异常都不能把秘密或SDK内部对象回显给页面。
    def run_read_only_test(self, provider_id: str) -> dict[str, object]:
        self._require_definition(provider_id)
        tester = self._testers.get(provider_id)
        if tester is None:
            raise ProviderConnectionApplicationError(
                "READ_ONLY_TESTER_NOT_AVAILABLE",
                "该数据源尚未接入只读测试器，等待TASK_024F。",
                http_status=409,
            )
        profiles = self._profiles.load_all()
        profile = profiles.get(provider_id)
        if profile is None:
            raise ProviderConnectionApplicationError(
                "CONNECTION_NOT_CONFIGURED",
                "请先保存连接信息。",
                http_status=409,
            )
        try:
            pending_status = transition_connection_status(
                profile.status,
                ConnectionStatus.READ_ONLY_TEST_PENDING,
            )
        except ValueError as exc:
            raise ProviderConnectionApplicationError(
                "READ_ONLY_TEST_NOT_ALLOWED",
                "当前连接状态不允许执行只读测试。",
                http_status=409,
            ) from exc
        pending_profile = replace(profile, status=pending_status)
        self._profiles.save(pending_profile)
        try:
            result = tester.run(
                profile=pending_profile,
                resolve_secret=self._credential_store.resolve_secret,
            ).with_timestamp()
        except Exception:
            result = ReadOnlyConnectionTestResult(
                success=False,
                summary="只读连接测试发生内部错误，未启用任何交易能力。",
                warnings=("请查看本地受控日志并核对SDK、授权和网络环境。",),
            ).with_timestamp()
        target = (
            ConnectionStatus.READ_ONLY_VERIFIED
            if result.success
            else ConnectionStatus.CONNECTION_TEST_FAILED
        )
        final_status = transition_connection_status(pending_profile.status, target)
        final_profile = replace(pending_profile, status=final_status)
        self._profiles.save(final_profile)
        return {
            "test_result": asdict(result),
            "profile": _safe_profile_view(final_profile, self._credential_store),
            "execution_activation": "BLOCKED",
        }

    # 本段代码核心功能：撤销一个Provider连接并删除其全部Windows秘密与本地无秘密档案。
    # - 输入：provider_id。
    # - 处理：先逐个删除凭据；不存在视为幂等；任一系统错误则保留档案并失败关闭；全部成功后删除档案。
    # - 输出：撤销确认和更新卡片。
    # - 为什么这样写：只删档案会把秘密遗留在系统保险箱，只删秘密又会留下误导性配置，二者必须作为一个用户动作治理。
    def disable_connection(self, provider_id: str) -> dict[str, object]:
        self._require_definition(provider_id)
        profiles = self._profiles.load_all()
        profile = profiles.get(provider_id)
        if profile is None:
            return {"disabled": True, "cards": self.list_cards()}

        # 本段代码核心功能：在删除前把仍然存在的秘密短暂读取到请求内存，作为失败恢复材料。
        # - 输入：档案中的受控Windows凭据引用。
        # - 处理：不存在的引用跳过；存在时按引用读取并连同规范化位置保存到局部列表。
        # - 输出：仅在当前函数生命周期存在的恢复列表，不写日志、文件、页面或报告。
        # - 为什么这样写：Windows凭据删除没有多项事务，第二项删除失败时必须能够恢复第一项，避免档案保留但凭据残缺。
        recovery_material: list[tuple[object, str]] = []
        for reference in profile.credential_references.values():
            try:
                location = parse_credential_reference(reference)
                secret_value = self._credential_store.resolve_secret(reference)
            except CredentialNotFoundError:
                continue
            recovery_material.append((location, secret_value))

        deleted_locations: list[object] = []
        try:
            for location, _secret_value in recovery_material:
                self._credential_store.delete_secret(location.reference)
                deleted_locations.append(location)
            self._profiles.delete(provider_id)
        except Exception as exc:
            recovery_by_reference = {
                location.reference: (location, secret_value)
                for location, secret_value in recovery_material
            }
            recovery_failed = False
            for location in reversed(deleted_locations):
                original_location, secret_value = recovery_by_reference[location.reference]
                try:
                    self._credential_store.store_secret(
                        provider_id=original_location.provider_id,
                        connection_id=original_location.connection_id,
                        field_id=original_location.field_id,
                        secret_value=secret_value,
                    )
                except Exception:
                    recovery_failed = True
            message = (
                "凭据删除失败，系统恢复未完全成功；请停止继续操作并检查本地安全存储。"
                if recovery_failed
                else "凭据删除失败，系统已恢复此前删除的秘密并保留连接档案。"
            )
            raise ProviderConnectionApplicationError(
                "CREDENTIAL_DELETE_FAILED",
                message,
                http_status=500,
            ) from exc
        finally:
            recovery_material.clear()
            deleted_locations.clear()
        return {"disabled": True, "cards": self.list_cards()}

    # 本段代码核心功能：按稳定标识查找Provider定义并提供安全404错误。
    # - 输入：provider_id。
    # - 处理：从初始化时构建的定义映射读取。
    # - 输出：ProviderConnectionDefinition或ProviderConnectionApplicationError。
    # - 为什么这样写：所有用例共享同一查找逻辑，避免某些路由对未知Provider宽松处理。
    def _require_definition(self, provider_id: str) -> ProviderConnectionDefinition:
        definition = self._definition_map.get(provider_id)
        if definition is None:
            raise ProviderConnectionApplicationError(
                "PROVIDER_NOT_FOUND",
                "未找到该数据源定义。",
                http_status=404,
            )
        return definition


# 本段代码核心功能：提供一个仅监听本机回环地址的轻量WSGI适配器，把页面操作映射到应用服务。
# - 输入：标准WSGI environ、应用服务和随机CSRF令牌。
# - 处理：限制来源、路由、请求体、JSON类型和变更请求令牌；设置no-store与安全响应头。
# - 输出：HTML页面或统一JSON响应。
# - 为什么这样写：项目当前没有固定前端框架，先复用Python标准库建立可替换的本地纵向样板，不把领域逻辑锁进某个Web框架。
class ProviderConnectionCenterWSGIApp:
    """Local-only WSGI adapter for the provider connection center."""

    # 本段代码核心功能：初始化只允许本机访问的WSGI页面适配器。
    # - 输入：统一应用服务和可选固定CSRF令牌。
    # - 处理：保存服务；未提供令牌时生成高强度随机令牌。
    # - 输出：可由标准库WSGI服务器调用的本地应用对象。
    # - 为什么这样写：CSRF令牌必须在服务启动时集中生成，页面路由不能各自维护不一致的安全状态。
    def __init__(
        self,
        service: ProviderConnectionCenterService,
        *,
        csrf_token: str | None = None,
    ) -> None:
        self._service = service
        self.csrf_token = csrf_token or secrets.token_urlsafe(32)

    # 本段代码核心功能：处理一次WSGI请求并返回符合安全边界的页面或JSON。
    # - 输入：WSGI environ和start_response。
    # - 处理：阻断非回环来源，分派路由，映射安全业务异常并隐藏未预期异常细节。
    # - 输出：可迭代bytes响应体。
    # - 为什么这样写：集中异常映射可确保任何底层错误都不会把秘密、文件路径或SDK内部状态返回浏览器。
    def __call__(self, environ: Mapping[str, object], start_response):
        remote = str(environ.get("REMOTE_ADDR", ""))
        if remote not in LOOPBACK_ADDRESSES:
            return self._json_response(
                start_response,
                403,
                {"ok": False, "error": {"code": "LOCAL_ONLY", "message": "接入中心只允许本机访问。"}},
            )
        try:
            return self._dispatch(environ, start_response)
        except ProviderConnectionApplicationError as exc:
            return self._json_response(
                start_response,
                exc.http_status,
                {"ok": False, "error": {"code": exc.code, "message": exc.safe_message}},
            )
        except ValueError as exc:
            return self._json_response(
                start_response,
                400,
                {"ok": False, "error": {"code": "INVALID_REQUEST", "message": str(exc)}},
            )
        except Exception:
            return self._json_response(
                start_response,
                500,
                {"ok": False, "error": {"code": "INTERNAL_ERROR", "message": "请求未完成，秘密未被返回。"}},
            )

    # 本段代码核心功能：按HTTP方法和路径调用具体应用用例。
    # - 输入：标准PATH_INFO、REQUEST_METHOD和请求体。
    # - 处理：支持首页、健康检查、卡片、表单、保存、只读测试和撤销六类路由。
    # - 输出：HTML或JSON响应；未知路由返回404。
    # - 为什么这样写：路由集合保持小而明确，TASK_024F只需注册测试器，无需新增绕过应用服务的SDK路由。
    def _dispatch(self, environ: Mapping[str, object], start_response):
        method = str(environ.get("REQUEST_METHOD", "GET")).upper()
        path = unquote(str(environ.get("PATH_INFO", "/")))
        if method == "GET" and path in {"/", "/provider-connections"}:
            html = render_provider_connection_page(self.csrf_token)
            return self._response(start_response, 200, HTML_CONTENT_TYPE, html.encode("utf-8"))
        if method == "GET" and path == "/api/health":
            return self._json_response(start_response, 200, {"ok": True, "service": "provider-connection-center"})
        if method == "GET" and path == "/api/provider-connections":
            return self._json_response(start_response, 200, {"ok": True, "cards": self._service.list_cards()})
        segments = tuple(part for part in path.split("/") if part)
        if len(segments) >= 3 and segments[:2] == ("api", "provider-connections"):
            provider_id = segments[2]
            if method == "GET" and len(segments) == 4 and segments[3] == "form":
                return self._json_response(start_response, 200, {"ok": True, **self._service.get_form(provider_id)})
            if method in {"POST", "DELETE"}:
                self._require_csrf(environ)
            if method == "POST" and len(segments) == 3:
                body = self._read_json(environ)
                values = body.get("values")
                if not isinstance(values, dict):
                    raise ValueError("values must be an object")
                result = self._service.submit_connection(
                    provider_id=provider_id,
                    connection_id=str(body.get("connection_id", "")),
                    values=values,
                    official_authorization_confirmed=body.get("official_authorization_confirmed") is True,
                    read_only_entitlement_confirmed=body.get("read_only_entitlement_confirmed") is True,
                    execution_domain_isolated=body.get("execution_domain_isolated") is True,
                )
                return self._json_response(start_response, 200, {"ok": True, **result})
            if method == "POST" and len(segments) == 4 and segments[3] == "test":
                result = self._service.run_read_only_test(provider_id)
                return self._json_response(start_response, 200, {"ok": True, **result})
            if method == "DELETE" and len(segments) == 3:
                result = self._service.disable_connection(provider_id)
                return self._json_response(start_response, 200, {"ok": True, **result})
        return self._json_response(
            start_response,
            404,
            {"ok": False, "error": {"code": "ROUTE_NOT_FOUND", "message": "未找到接口。"}},
        )

    # 本段代码核心功能：校验所有变更请求携带当前页面随机CSRF令牌。
    # - 输入：X-WJX-CSRF-Token请求头。
    # - 处理：使用secrets.compare_digest进行定时安全比较。
    # - 输出：匹配时继续，不匹配时返回403业务异常。
    # - 为什么这样写：本地服务仍可能被恶意网页跨站触发，随机同源令牌可阻断无权保存或删除凭据的请求。
    def _require_csrf(self, environ: Mapping[str, object]) -> None:
        supplied = str(environ.get(CSRF_HEADER, ""))
        if not supplied or not secrets.compare_digest(supplied, self.csrf_token):
            raise ProviderConnectionApplicationError(
                "CSRF_REJECTED",
                "页面安全令牌无效，请刷新接入中心后重试。",
                http_status=403,
            )

    # 本段代码核心功能：在固定大小上限内读取并解析JSON请求体。
    # - 输入：CONTENT_LENGTH、CONTENT_TYPE和wsgi.input。
    # - 处理：要求application/json，拒绝负数、缺失、超过64KiB和非对象JSON。
    # - 输出：普通字典。
    # - 为什么这样写：秘密只应存在于受限请求内存，不能接受无限流、表单编码或任意复杂顶层结构。
    def _read_json(self, environ: Mapping[str, object]) -> dict[str, object]:
        content_type = str(environ.get("CONTENT_TYPE", "")).split(";", 1)[0].strip().lower()
        if content_type != "application/json":
            raise ProviderConnectionApplicationError(
                "JSON_REQUIRED",
                "请求必须使用application/json。",
                http_status=415,
            )
        try:
            content_length = int(str(environ.get("CONTENT_LENGTH", "0") or "0"))
        except ValueError as exc:
            raise ValueError("invalid CONTENT_LENGTH") from exc
        if content_length < 0 or content_length > MAX_REQUEST_BYTES:
            raise ProviderConnectionApplicationError(
                "REQUEST_TOO_LARGE",
                "连接表单超过允许大小。",
                http_status=413,
            )
        stream = environ.get("wsgi.input")
        if stream is None or not hasattr(stream, "read"):
            raise ValueError("missing request body")
        raw = stream.read(content_length)
        parsed = json.loads(raw.decode("utf-8"))
        if not isinstance(parsed, dict):
            raise ValueError("request body must be an object")
        return parsed

    # 本段代码核心功能：把字典序列化为UTF-8 JSON并统一返回。
    # - 输入：状态码和JSON对象。
    # - 处理：ensure_ascii=False便于中文UI，separators减少无意义体积。
    # - 输出：带安全响应头的WSGI bytes列表。
    # - 为什么这样写：统一序列化避免某个路由遗漏no-store或返回Python对象字符串。
    def _json_response(self, start_response, status: int, payload: Mapping[str, object]):
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        return self._response(start_response, status, JSON_CONTENT_TYPE, body)

    # 本段代码核心功能：生成统一状态行、安全响应头和内容长度。
    # - 输入：HTTP状态、内容类型和响应字节。
    # - 处理：映射常用状态文本，设置no-store、nosniff、frame deny和严格referrer策略。
    # - 输出：标准WSGI响应体列表。
    # - 为什么这样写：接入页面可能处理密钥输入，浏览器缓存、嵌入和类型嗅探必须显式关闭。
    def _response(self, start_response, status: int, content_type: str, body: bytes):
        status_text = {
            200: "OK",
            400: "Bad Request",
            403: "Forbidden",
            404: "Not Found",
            409: "Conflict",
            413: "Payload Too Large",
            415: "Unsupported Media Type",
            500: "Internal Server Error",
        }.get(status, "Error")
        headers = [
            ("Content-Type", content_type),
            ("Content-Length", str(len(body))),
            ("Cache-Control", "no-store, max-age=0"),
            ("Pragma", "no-cache"),
            ("X-Content-Type-Options", "nosniff"),
            ("X-Frame-Options", "DENY"),
            ("Referrer-Policy", "no-referrer"),
            ("Content-Security-Policy", "default-src 'self'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'"),
        ]
        start_response(f"{status} {status_text}", headers)
        return [body]
