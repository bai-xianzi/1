# 本文件核心功能：定义“官方数据源与券商接入中心”的领域对象、动态表单合同、凭据引用边界和连接状态机。
# - 输入：Provider官方接入定义、用户提交的表单值、后台环境发现结果和不含秘密值的现有连接档案。
# - 处理：校验字段、把秘密值立即交给凭据写入器、仅保留凭据引用，并生成可供未来UI直接渲染的安全ViewModel。
# - 输出：Provider卡片、JSON Schema动态表单、连接档案和状态迁移结果；任何输出都不包含API Key、Secret、Token或密码原文。
# - 常量依据：来源权威顺序来自TASK_024A，SDK证据来自TASK_024B；表单结构采用JSON Schema 2020-12，秘密存储由后续Windows安全后端实现。
# - 为什么这样写：用户应该通过可视化界面接入官方券商和交易所数据，但UI不能把密钥写进普通JSON、日志、Git或数据库配置表。
"""Provider connection-center domain and UI contract."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Mapping, Protocol, Sequence


# 本段代码核心功能：保存当前动态表单使用的JSON Schema版本标识。
# - 输入：无运行时输入，值来自JSON Schema官方2020-12元模式URI。
# - 处理：作为生成表单Schema的固定常量，不在运行中修改。
# - 输出：每份动态表单的`$schema`字段。
# - 常量依据：JSON Schema 2020-12是当前稳定公开规范，适合跨前端框架复用。
# - 为什么这样写：采用行业标准可以让未来桌面UI、Web UI和测试工具共享同一份字段合同，避免自造私有表单协议。
JSON_SCHEMA_DIALECT = "https://json-schema.org/draft/2020-12/schema"


# 本段代码核心功能：限定接入中心允许出现的字段控件类型。
# - 输入：Provider官方文档映射产生的字段类型字符串。
# - 处理：使用枚举拒绝未审核的任意控件类型。
# - 输出：供字段定义、Schema生成和UI渲染共同使用的稳定值。
# - 常量依据：个人版接入向导只需要文本、秘密、文件、目录、选择和布尔确认六类基础控件。
# - 为什么这样写：先保持控件集合小而稳定，后续新增证书、多因素认证等能力时再经权威文档审查扩展。
class FieldKind(str, Enum):
    """Supported connection-form field kinds."""

    TEXT = "text"
    SECRET = "secret"
    FILE = "file"
    DIRECTORY = "directory"
    SELECT = "select"
    BOOLEAN = "boolean"


# 本段代码核心功能：限定字段提交后允许采用的持久化策略。
# - 输入：字段定义中的持久化模式字符串。
# - 处理：将普通配置、凭据引用和完全不持久化三种情况显式分开。
# - 输出：表单提交函数据此决定保存公开值、保存引用或丢弃值。
# - 常量依据：秘密原文不得进入项目配置；临时验证码等一次性值不得持久化。
# - 为什么这样写：把安全规则写进类型系统，比依靠UI开发者记住“哪些字段不能保存”更可靠。
class PersistMode(str, Enum):
    """Persistence policy for one submitted field."""

    CONFIGURATION = "configuration"
    CREDENTIAL_REFERENCE = "credential_reference"
    NEVER = "never"


# 本段代码核心功能：定义接入中心向用户展示的连接状态机。
# - 输入：环境发现、凭据保存、只读测试、语义审查和授权有效期等事件。
# - 处理：只允许通过后文的显式迁移表改变状态。
# - 输出：Provider卡片和连接档案中的稳定状态代码。
# - 常量依据：普通连接测试不得自动进入交易激活；研究可用与交易可用必须分离。
# - 为什么这样写：单一“成功/失败”无法解释缺SDK、缺授权、密钥过期、语义待审查等不同问题。
class ConnectionStatus(str, Enum):
    """User-facing provider connection states."""

    NOT_CONFIGURED = "NOT_CONFIGURED"
    OFFICIAL_APPLICATION_REQUIRED = "OFFICIAL_APPLICATION_REQUIRED"
    OFFICIAL_FIELD_SPEC_REQUIRED = "OFFICIAL_FIELD_SPEC_REQUIRED"
    SDK_NOT_FOUND = "SDK_NOT_FOUND"
    CREDENTIALS_SAVED = "CREDENTIALS_SAVED"
    READ_ONLY_TEST_PENDING = "READ_ONLY_TEST_PENDING"
    READ_ONLY_VERIFIED = "READ_ONLY_VERIFIED"
    SEMANTIC_REVIEW_REQUIRED = "SEMANTIC_REVIEW_REQUIRED"
    READY_FOR_RESEARCH = "READY_FOR_RESEARCH"
    CONNECTION_TEST_FAILED = "CONNECTION_TEST_FAILED"
    CREDENTIAL_EXPIRED = "CREDENTIAL_EXPIRED"
    BLOCKED_FOR_TRADING = "BLOCKED_FOR_TRADING"


# 本段代码核心功能：定义单个动态表单字段的官方映射结果。
# - 输入：Provider官方接口文档或用户正式授权材料中确认的字段要求。
# - 处理：把显示、验证、是否秘密及持久化方式集中到不可变对象。
# - 输出：供JSON Schema生成器和提交校验器共同使用的字段合同。
# - 常量依据：没有官方字段依据时不得为具体券商猜测API Key、账户号、服务器地址等字段。
# - 为什么这样写：同一字段合同同时驱动前端和后端，可避免UI允许提交而后端拒绝，或后端秘密字段被UI当普通文本保存。
@dataclass(frozen=True)
class ConnectionFieldDefinition:
    """One official connection-form field definition."""

    field_id: str
    label: str
    kind: FieldKind
    required: bool
    persist_mode: PersistMode
    help_text: str
    placeholder: str = ""
    options: tuple[str, ...] = ()
    validation_pattern: str = ""


# 本段代码核心功能：定义一个Provider在接入中心中的完整展示和表单合同。
# - 输入：官方来源目录、券商官方文档映射和TASK_024B环境发现能力。
# - 处理：保存权威等级、申请指引引用、表单审核状态、字段和只读/交易能力边界。
# - 输出：Provider卡片、动态表单及后续连接测试的统一定义。
# - 常量依据：交易所/监管/结算官方资料是语义基准，用户已授权券商SDK是优先实际通道。
# - 为什么这样写：把“产品存在”“申请权限”“填写凭据”“只读验证”拆开，避免用户看到产品卡片就被误导为已经可连接。
@dataclass(frozen=True)
class ProviderConnectionDefinition:
    """Connection-center definition for one official provider."""

    provider_id: str
    display_name: str
    provider_kind: str
    authority_tier: str
    official_application_reference: str
    form_definition_status: str
    supports_read_only_data: bool
    contains_execution_capability: bool
    fields: tuple[ConnectionFieldDefinition, ...]


# 本段代码核心功能：定义安全保存后的Provider连接档案。
# - 输入：非秘密配置、字段级凭据引用、授权确认和连接状态。
# - 处理：使用不可变映射副本保存，不接收秘密原文。
# - 输出：可写入本地配置或传给UI的安全档案。
# - 常量依据：项目配置只允许保存凭据引用；秘密值由操作系统安全存储后端托管。
# - 为什么这样写：连接档案可能进入日志、报告或Git差异，因此从数据模型层面彻底排除秘密原文。
@dataclass(frozen=True)
class ProviderConnectionProfile:
    """Secret-free stored connection profile."""

    provider_id: str
    connection_id: str
    status: ConnectionStatus
    public_configuration: Mapping[str, object]
    credential_references: Mapping[str, str]
    official_authorization_confirmed: bool
    read_only_entitlement_confirmed: bool
    execution_domain_isolated: bool


# 本段代码核心功能：定义凭据写入器协议，隔离领域层与Windows安全存储实现。
# - 输入：Provider、连接、字段标识和本次UI请求中的秘密值。
# - 处理：由实现方立即写入操作系统密钥库并返回不可逆向得到原文的引用。
# - 输出：非秘密凭据引用字符串。
# - 常量依据：TASK_024C只定义边界，TASK_024D再选择并实现Windows Credential Locker、DPAPI或成熟keyring后端。
# - 为什么这样写：领域模型不绑定某个Windows API或第三方库，便于测试、替换和未来跨平台迁移。
class CredentialReferenceWriter(Protocol):
    """Port used to exchange a secret value for a safe reference."""

    # 本段代码核心功能：定义 `store_secret`，完成 `store_secret` 对应的单一业务步骤并返回明确结果。
    # - 输入：参数为 `self、provider_id、connection_id、field_id、secret_value`；路径和外部文本按UTF-8处理，安全开关必须由显式配置提供。
    # - 处理：只执行函数名对应的单一职责；缺字段、非法状态或越界值立即失败，不做静默猜测。
    # - 输出：返回类型为 `str`；测试函数通过断言表达通过或失败，不产生生产副作用。
    # - 常量依据：任务号、状态枚举、零网络/零交易计数和候选优先级来自TASK_022至TASK_024权威合同。
    # - 为什么这样写：显式输入输出和失败模式便于教学排查，也让官方交易所或券商SDK通过薄适配器接入。

    def store_secret(
        self,
        *,
        provider_id: str,
        connection_id: str,
        field_id: str,
        secret_value: str,
    ) -> str:
        """Store one secret and return its non-secret reference."""


# 本段代码核心功能：定义合法字段标识格式，防止路径、命令片段或任意文本成为配置键。
# - 输入：Provider、连接和字段标识字符串。
# - 处理：要求以小写字母开头，只允许小写字母、数字和下划线。
# - 输出：供目录加载和表单提交校验复用的正则对象。
# - 常量依据：标识只承担内部键名职责，不需要空格、斜杠、冒号或命令字符。
# - 为什么这样写：限制标识可以降低路径穿越、日志混淆和前后端键名漂移风险。
IDENTIFIER_PATTERN = re.compile(r"^[a-z][a-z0-9_]{1,63}$")


# 本段代码核心功能：保存连接状态允许的显式迁移关系。
# - 输入：当前状态和下一状态。
# - 处理：查询不可变状态集合，不执行网络或存储副作用。
# - 输出：`transition_connection_status`据此返回新状态或抛出错误。
# - 常量依据：交易阻断可以从任何研究阶段显式进入，但不能通过普通只读测试解除。
# - 为什么这样写：集中维护迁移关系可以让UI按钮、后端API和测试共享同一状态机。
ALLOWED_STATUS_TRANSITIONS: Mapping[ConnectionStatus, frozenset[ConnectionStatus]] = {
    ConnectionStatus.NOT_CONFIGURED: frozenset(
        {
            ConnectionStatus.OFFICIAL_APPLICATION_REQUIRED,
            ConnectionStatus.OFFICIAL_FIELD_SPEC_REQUIRED,
            ConnectionStatus.SDK_NOT_FOUND,
            ConnectionStatus.CREDENTIALS_SAVED,
        }
    ),
    ConnectionStatus.OFFICIAL_APPLICATION_REQUIRED: frozenset(
        {ConnectionStatus.CREDENTIALS_SAVED, ConnectionStatus.SDK_NOT_FOUND}
    ),
    ConnectionStatus.OFFICIAL_FIELD_SPEC_REQUIRED: frozenset(
        {ConnectionStatus.NOT_CONFIGURED}
    ),
    ConnectionStatus.SDK_NOT_FOUND: frozenset(
        {ConnectionStatus.NOT_CONFIGURED, ConnectionStatus.CREDENTIALS_SAVED}
    ),
    ConnectionStatus.CREDENTIALS_SAVED: frozenset(
        {
            ConnectionStatus.READ_ONLY_TEST_PENDING,
            ConnectionStatus.CREDENTIAL_EXPIRED,
            ConnectionStatus.NOT_CONFIGURED,
        }
    ),
    ConnectionStatus.READ_ONLY_TEST_PENDING: frozenset(
        {
            ConnectionStatus.READ_ONLY_VERIFIED,
            ConnectionStatus.CONNECTION_TEST_FAILED,
            ConnectionStatus.CREDENTIAL_EXPIRED,
        }
    ),
    ConnectionStatus.CONNECTION_TEST_FAILED: frozenset(
        {
            ConnectionStatus.READ_ONLY_TEST_PENDING,
            ConnectionStatus.CREDENTIALS_SAVED,
            ConnectionStatus.CREDENTIAL_EXPIRED,
        }
    ),
    ConnectionStatus.READ_ONLY_VERIFIED: frozenset(
        {
            ConnectionStatus.SEMANTIC_REVIEW_REQUIRED,
            ConnectionStatus.CREDENTIAL_EXPIRED,
            ConnectionStatus.BLOCKED_FOR_TRADING,
        }
    ),
    ConnectionStatus.SEMANTIC_REVIEW_REQUIRED: frozenset(
        {
            ConnectionStatus.READY_FOR_RESEARCH,
            ConnectionStatus.CONNECTION_TEST_FAILED,
            ConnectionStatus.CREDENTIAL_EXPIRED,
            ConnectionStatus.BLOCKED_FOR_TRADING,
        }
    ),
    ConnectionStatus.READY_FOR_RESEARCH: frozenset(
        {
            ConnectionStatus.CREDENTIAL_EXPIRED,
            ConnectionStatus.CONNECTION_TEST_FAILED,
            ConnectionStatus.BLOCKED_FOR_TRADING,
        }
    ),
    ConnectionStatus.CREDENTIAL_EXPIRED: frozenset(
        {ConnectionStatus.CREDENTIALS_SAVED, ConnectionStatus.NOT_CONFIGURED}
    ),
    ConnectionStatus.BLOCKED_FOR_TRADING: frozenset(
        {
            ConnectionStatus.READY_FOR_RESEARCH,
            ConnectionStatus.CREDENTIAL_EXPIRED,
        }
    ),
}


# 本段代码核心功能：把JSON数组字段转换为已校验、去重且保持顺序的字符串元组。
# - 输入：原始JSON值和用于错误提示的字段名。
# - 处理：要求为字符串列表，去除空白并按首次出现顺序去重。
# - 输出：不可变字符串元组。
# - 常量依据：选项顺序会直接影响UI显示，不能依赖集合的无序特性。
# - 为什么这样写：严格加载可在启动时暴露目录错误，避免错误配置拖到用户提交时才出现。
def _string_tuple(value: object, field_name: str) -> tuple[str, ...]:
    """Validate an ordered list of non-empty strings."""

    # 本段代码核心功能：阻断非列表配置。
    # - 输入：原始JSON字段值。
    # - 处理：使用类型检查拒绝字符串被逐字符解释等宽松行为。
    # - 输出：非法时抛出ValueError。
    # - 常量依据：目录格式要求所有选项显式写成JSON数组。
    # - 为什么这样写：早失败比静默修复更适合权威配置。
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a list")

    normalized: list[str] = []
    seen: set[str] = set()

    # 本段代码核心功能：逐项验证、清理并去重选项。
    # - 输入：配置数组中的每个候选值。
    # - 处理：拒绝空值和非字符串，保留第一次出现位置。
    # - 输出：更新normalized和seen。
    # - 常量依据：UI选项必须有稳定标签且不能重复。
    # - 为什么这样写：保持来源顺序便于与官方文档逐项对照。
    for item in value:
        # 本段代码核心功能：拒绝非法选项。
        # - 输入：当前数组元素。
        # - 处理：检查字符串类型和去空白后的非空性。
        # - 输出：非法时抛出ValueError。
        # - 常量依据：空选项无法被用户理解或提交。
        # - 为什么这样写：不允许目录靠前端猜测显示值。
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"{field_name} must contain non-empty strings")
        text = item.strip()

        # 本段代码核心功能：只保留首次出现的选项。
        # - 输入：规范化文本和已见集合。
        # - 处理：不存在时追加并记录。
        # - 输出：稳定去重后的列表。
        # - 常量依据：重复选项没有额外业务意义。
        # - 为什么这样写：避免UI显示重复环境或模式选项。
        if text not in seen:
            seen.add(text)
            normalized.append(text)

    return tuple(normalized)


# 本段代码核心功能：加载接入中心Provider目录并转换为领域定义。
# - 输入：UTF-8 JSON目录路径。
# - 处理：校验Provider和字段标识、控件类型、持久化策略及秘密字段约束。
# - 输出：按目录顺序返回ProviderConnectionDefinition元组。
# - 常量依据：具体Provider字段只有在官方文档映射完成后才允许进入目录。
# - 为什么这样写：目录加载时一次性拒绝“秘密字段保存为普通配置”等高风险错误。
def load_connection_catalog(path: Path) -> tuple[ProviderConnectionDefinition, ...]:
    """Load and validate the provider connection-center catalog."""

    raw = json.loads(path.read_text(encoding="utf-8-sig"))
    providers = raw.get("providers")

    # 本段代码核心功能：确认目录顶层包含Provider数组。
    # - 输入：解析后的`providers`值。
    # - 处理：执行严格类型检查。
    # - 输出：非法时抛出ValueError。
    # - 常量依据：目录只接受显式Provider列表。
    # - 为什么这样写：避免空对象被误认为有效目录。
    if not isinstance(providers, list):
        raise ValueError("providers must be a list")

    definitions: list[ProviderConnectionDefinition] = []
    seen_provider_ids: set[str] = set()

    # 本段代码核心功能：逐个Provider构建安全定义。
    # - 输入：目录中的Provider对象列表。
    # - 处理：验证标识唯一性并加载字段定义。
    # - 输出：追加到definitions。
    # - 常量依据：每个Provider必须拥有唯一稳定标识。
    # - 为什么这样写：逐项错误能精确指出是哪家官方接口配置有问题。
    for provider in providers:
        # 本段代码核心功能：拒绝非对象Provider条目。
        # - 输入：当前Provider条目。
        # - 处理：执行字典类型检查。
        # - 输出：非法时抛出ValueError。
        # - 常量依据：Provider需要多个具名字段。
        # - 为什么这样写：不允许列表或字符串被隐式转换。
        if not isinstance(provider, dict):
            raise ValueError("each provider must be an object")

        provider_id = str(provider.get("provider_id", "")).strip()

        # 本段代码核心功能：验证Provider标识格式和唯一性。
        # - 输入：规范化provider_id和已见集合。
        # - 处理：正则校验并检查重复。
        # - 输出：非法时抛出ValueError。
        # - 常量依据：内部标识格式由IDENTIFIER_PATTERN统一规定。
        # - 为什么这样写：稳定标识是凭据引用、路由和UI状态关联的基础。
        if not IDENTIFIER_PATTERN.fullmatch(provider_id):
            raise ValueError(f"invalid provider_id: {provider_id!r}")
        # 本段代码核心功能：根据条件 `provider_id in seen_provider_ids` 选择安全分支。
        # - 输入：条件表达式和此前已经规范化的局部变量。
        # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
        # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
        # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

        if provider_id in seen_provider_ids:
            raise ValueError(f"duplicate provider_id: {provider_id}")
        seen_provider_ids.add(provider_id)

        fields_raw = provider.get("fields", [])

        # 本段代码核心功能：确认字段定义是数组。
        # - 输入：当前Provider的fields值。
        # - 处理：执行严格类型检查。
        # - 输出：非法时抛出ValueError。
        # - 常量依据：无字段Provider必须使用空数组表示待官方文档映射。
        # - 为什么这样写：显式空数组比缺省任意对象更容易审计。
        if not isinstance(fields_raw, list):
            raise ValueError(f"{provider_id}.fields must be a list")

        fields: list[ConnectionFieldDefinition] = []
        seen_field_ids: set[str] = set()

        # 本段代码核心功能：逐个加载Provider字段定义。
        # - 输入：字段JSON对象。
        # - 处理：验证标识、类型、持久化模式、选项和安全约束。
        # - 输出：追加不可变字段对象。
        # - 常量依据：字段必须来自官方文档映射，不允许运行时自由新增。
        # - 为什么这样写：后端白名单校验必须与UI展示使用相同字段集合。
        for field in fields_raw:
            # 本段代码核心功能：拒绝非对象字段。
            # - 输入：当前字段条目。
            # - 处理：字典类型检查。
            # - 输出：非法时抛出ValueError。
            # - 常量依据：字段合同需要具名属性。
            # - 为什么这样写：禁止模糊位置参数配置。
            if not isinstance(field, dict):
                raise ValueError(f"{provider_id}.fields entries must be objects")

            field_id = str(field.get("field_id", "")).strip()

            # 本段代码核心功能：验证字段标识和唯一性。
            # - 输入：field_id及已见集合。
            # - 处理：正则校验并检查重复。
            # - 输出：非法时抛出ValueError。
            # - 常量依据：字段标识将参与凭据引用键生成。
            # - 为什么这样写：阻断路径或命令字符进入秘密存储键。
            if not IDENTIFIER_PATTERN.fullmatch(field_id):
                raise ValueError(f"invalid field_id: {provider_id}.{field_id}")
            # 本段代码核心功能：根据条件 `field_id in seen_field_ids` 选择安全分支。
            # - 输入：条件表达式和此前已经规范化的局部变量。
            # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
            # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
            # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
            # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

            if field_id in seen_field_ids:
                raise ValueError(f"duplicate field_id: {provider_id}.{field_id}")
            seen_field_ids.add(field_id)

            kind = FieldKind(str(field.get("kind", "")))
            persist_mode = PersistMode(str(field.get("persist_mode", "")))

            # 本段代码核心功能：强制秘密控件只能保存凭据引用或完全不持久化。
            # - 输入：字段kind和persist_mode。
            # - 处理：拒绝SECRET与CONFIGURATION组合。
            # - 输出：非法时抛出ValueError。
            # - 常量依据：秘密原文不得进入普通项目配置。
            # - 为什么这样写：从目录加载阶段防止前端错误配置造成泄密。
            if kind is FieldKind.SECRET and persist_mode is PersistMode.CONFIGURATION:
                raise ValueError(
                    f"secret field cannot use configuration persistence: "
                    f"{provider_id}.{field_id}"
                )

            options = _string_tuple(field.get("options", []), "options")

            # 本段代码核心功能：要求选择控件提供至少一个选项。
            # - 输入：字段kind和已规范化options。
            # - 处理：检查SELECT字段是否为空。
            # - 输出：非法时抛出ValueError。
            # - 常量依据：空选择框无法提交合法值。
            # - 为什么这样写：避免UI和后端对可选值范围产生分歧。
            if kind is FieldKind.SELECT and not options:
                raise ValueError(f"select field requires options: {provider_id}.{field_id}")

            fields.append(
                ConnectionFieldDefinition(
                    field_id=field_id,
                    label=str(field.get("label", field_id)).strip(),
                    kind=kind,
                    required=bool(field.get("required", False)),
                    persist_mode=persist_mode,
                    help_text=str(field.get("help_text", "")).strip(),
                    placeholder=str(field.get("placeholder", "")).strip(),
                    options=options,
                    validation_pattern=str(
                        field.get("validation_pattern", "")
                    ).strip(),
                )
            )

        definitions.append(
            ProviderConnectionDefinition(
                provider_id=provider_id,
                display_name=str(provider.get("display_name", provider_id)).strip(),
                provider_kind=str(provider.get("provider_kind", "UNKNOWN")).strip(),
                authority_tier=str(provider.get("authority_tier", "UNREVIEWED")).strip(),
                official_application_reference=str(
                    provider.get("official_application_reference", "")
                ).strip(),
                form_definition_status=str(
                    provider.get("form_definition_status", "OFFICIAL_FIELD_SPEC_REQUIRED")
                ).strip(),
                supports_read_only_data=bool(
                    provider.get("supports_read_only_data", False)
                ),
                contains_execution_capability=bool(
                    provider.get("contains_execution_capability", False)
                ),
                fields=tuple(fields),
            )
        )

    return tuple(definitions)


# 本段代码核心功能：将Provider字段合同转换成前端可直接消费的JSON Schema和UI扩展属性。
# - 输入：单个ProviderConnectionDefinition。
# - 处理：按字段类型生成标准JSON Schema，并添加`x-*`安全与控件提示；秘密字段标为writeOnly。
# - 输出：不含任何用户值的表单Schema字典。
# - 常量依据：JSON Schema负责结构校验，`x-field-kind`和`x-persist-mode`负责项目特有UI行为。
# - 为什么这样写：标准字段与少量扩展兼顾复用性和安全需求，未来更换前端框架无需重写Provider定义。
def build_dynamic_form_schema(
    definition: ProviderConnectionDefinition,
) -> dict[str, object]:
    """Build a secret-free JSON Schema for one provider form."""

    properties: dict[str, object] = {}
    required: list[str] = []

    # 本段代码核心功能：逐字段生成JSON Schema属性。
    # - 输入：Provider的字段定义元组。
    # - 处理：映射基础类型、枚举、正则、writeOnly和UI扩展属性。
    # - 输出：更新properties和required。
    # - 常量依据：字段定义是前后端共享的唯一事实源。
    # - 为什么这样写：统一生成避免手写前端表单与后端合同长期漂移。
    for field in definition.fields:
        property_schema: dict[str, object] = {
            "title": field.label,
            "description": field.help_text,
            "x-field-kind": field.kind.value,
            "x-persist-mode": field.persist_mode.value,
        }

        # 本段代码核心功能：将布尔控件映射为JSON布尔类型，其余输入映射为字符串。
        # - 输入：field.kind。
        # - 处理：根据控件语义选择标准JSON类型。
        # - 输出：设置property_schema的type。
        # - 常量依据：文件和目录在浏览器/桌面UI层仍以受控路径字符串提交。
        # - 为什么这样写：保持后端合同简单，同时允许UI使用专用选择器。
        if field.kind is FieldKind.BOOLEAN:
            property_schema["type"] = "boolean"
        else:
            property_schema["type"] = "string"

        # 本段代码核心功能：为秘密字段添加只写标记并禁止返回默认值。
        # - 输入：field.kind。
        # - 处理：设置writeOnly和x-sensitive，不写default或example。
        # - 输出：秘密字段Schema扩展属性。
        # - 常量依据：UI可接收秘密，但任何读取接口都不得回显原文。
        # - 为什么这样写：让前端生成密码控件，并提醒API文档工具不应在响应中展示该字段。
        if field.kind is FieldKind.SECRET:
            property_schema["writeOnly"] = True
            property_schema["x-sensitive"] = True

        # 本段代码核心功能：为选择控件写入官方允许值枚举。
        # - 输入：field.options。
        # - 处理：转换为普通列表供JSON序列化。
        # - 输出：property_schema.enum。
        # - 常量依据：选项来自Provider官方文档映射。
        # - 为什么这样写：前后端使用同一枚举可以阻断随意环境或协议值。
        if field.options:
            property_schema["enum"] = list(field.options)

        # 本段代码核心功能：为具有官方格式约束的字符串写入正则。
        # - 输入：field.validation_pattern。
        # - 处理：非空时设置JSON Schema pattern。
        # - 输出：property_schema.pattern。
        # - 常量依据：只有官方资料确认的格式才允许写入。
        # - 为什么这样写：未确认格式时保持空白，避免凭经验过度限制真实凭据。
        if field.validation_pattern:
            property_schema["pattern"] = field.validation_pattern

        # 本段代码核心功能：为UI添加不含秘密值的占位提示。
        # - 输入：field.placeholder。
        # - 处理：非空时写入扩展属性。
        # - 输出：property_schema.x-placeholder。
        # - 常量依据：placeholder只用于指导，不作为提交默认值。
        # - 为什么这样写：秘密输入不能通过默认值或示例泄露真实格式细节。
        if field.placeholder:
            property_schema["x-placeholder"] = field.placeholder

        properties[field.field_id] = property_schema

        # 本段代码核心功能：把必填字段加入Schema required列表。
        # - 输入：field.required。
        # - 处理：为True时追加field_id。
        # - 输出：更新required。
        # - 常量依据：必填性来自官方连接要求。
        # - 为什么这样写：由后端统一生成必填列表，避免UI漏标。
        if field.required:
            required.append(field.field_id)

    schema: dict[str, object] = {
        "$schema": JSON_SCHEMA_DIALECT,
        "$id": f"wjx://provider-connections/{definition.provider_id}/form/v1",
        "title": f"{definition.display_name} connection form",
        "type": "object",
        "additionalProperties": False,
        "properties": properties,
        "required": required,
        "x-provider-id": definition.provider_id,
        "x-form-definition-status": definition.form_definition_status,
        "x-read-only-first": True,
        "x-execution-activation": "BLOCKED",
    }
    return schema


# 本段代码核心功能：校验用户提交并把秘密值即时交换成安全凭据引用。
# - 输入：Provider定义、连接ID、UI提交字典、授权确认和CredentialReferenceWriter实现。
# - 处理：白名单校验字段；秘密字段只传给writer并立即丢弃；普通配置按策略保存；生成无秘密连接档案。
# - 输出：ProviderConnectionProfile；对象内仅含公开配置和凭据引用。
# - 常量依据：TASK_024C不实现持久化后端，但领域层必须保证秘密不会出现在返回值。
# - 为什么这样写：把“接收秘密”和“保存档案”置于同一受控事务边界，避免先写临时JSON再异步转存造成泄密窗口。
def submit_connection_form(
    definition: ProviderConnectionDefinition,
    *,
    connection_id: str,
    submitted_values: Mapping[str, object],
    official_authorization_confirmed: bool,
    read_only_entitlement_confirmed: bool,
    execution_domain_isolated: bool,
    credential_writer: CredentialReferenceWriter,
) -> ProviderConnectionProfile:
    """Validate a form submission and return a secret-free profile."""

    # 本段代码核心功能：验证连接标识。
    # - 输入：connection_id。
    # - 处理：去空白后使用统一正则校验。
    # - 输出：非法时抛出ValueError。
    # - 常量依据：连接标识会参与凭据存储键。
    # - 为什么这样写：禁止路径和命令字符进入系统密钥库资源名。
    normalized_connection_id = connection_id.strip()
    # 本段代码核心功能：根据条件 `not IDENTIFIER_PATTERN.fullmatch(normalized_connection_id)` 选择安全分支。
    # - 输入：条件表达式和此前已经规范化的局部变量。
    # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
    # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
    # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

    if not IDENTIFIER_PATTERN.fullmatch(normalized_connection_id):
        raise ValueError("invalid connection_id")

    field_map = {field.field_id: field for field in definition.fields}
    unknown_fields = sorted(set(submitted_values) - set(field_map))

    # 本段代码核心功能：拒绝目录之外的任意提交字段。
    # - 输入：提交键集合与官方字段白名单差集。
    # - 处理：稳定排序后形成错误。
    # - 输出：存在未知字段时抛出ValueError。
    # - 常量依据：UI请求不能临时发明账号、Host或交易参数字段。
    # - 为什么这样写：后端白名单是防止前端篡改和秘密旁路存储的最后边界。
    if unknown_fields:
        raise ValueError(f"unknown fields: {', '.join(unknown_fields)}")

    public_configuration: dict[str, object] = {}
    credential_references: dict[str, str] = {}

    # 本段代码核心功能：逐字段执行必填、类型、枚举、格式和持久化策略校验。
    # - 输入：官方字段定义和submitted_values。
    # - 处理：秘密值直接交writer，公开值按策略保存，NEVER字段使用后丢弃。
    # - 输出：更新public_configuration和credential_references。
    # - 常量依据：所有字段处理都由Provider目录驱动。
    # - 为什么这样写：集中循环保证新增官方字段自动获得同一安全规则。
    for field in definition.fields:
        present = field.field_id in submitted_values
        value = submitted_values.get(field.field_id)

        # 本段代码核心功能：阻断缺失的必填字段。
        # - 输入：field.required和present。
        # - 处理：必填且未提交时抛出错误。
        # - 输出：ValueError。
        # - 常量依据：必填规则来自官方字段映射。
        # - 为什么这样写：不允许把缺字段问题延迟到真实券商连接阶段。
        if field.required and not present:
            raise ValueError(f"missing required field: {field.field_id}")

        # 本段代码核心功能：跳过未提交的可选字段。
        # - 输入：present布尔值。
        # - 处理：未提交时继续下一字段。
        # - 输出：不修改任何结果。
        # - 常量依据：可选字段不应自动生成默认秘密或配置值。
        # - 为什么这样写：显式提交比隐式默认更安全。
        if not present:
            continue

        # 本段代码核心功能：校验布尔字段类型。
        # - 输入：布尔控件定义和提交值。
        # - 处理：拒绝字符串`true`等宽松转换。
        # - 输出：非法时抛出ValueError。
        # - 常量依据：授权确认必须是明确布尔值。
        # - 为什么这样写：宽松转换容易把任意非空字符串误判为已确认。
        if field.kind is FieldKind.BOOLEAN:
            # 本段代码核心功能：根据条件 `not isinstance(value, bool)` 选择安全分支。
            # - 输入：条件表达式和此前已经规范化的局部变量。
            # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
            # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
            # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
            # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

            if not isinstance(value, bool):
                raise ValueError(f"{field.field_id} must be a boolean")
        else:
            # 本段代码核心功能：校验非布尔字段为非空字符串。
            # - 输入：文本、秘密、文件、目录或选择值。
            # - 处理：检查类型并去除首尾空白。
            # - 输出：规范化字符串或ValueError。
            # - 常量依据：连接字段不接受任意对象和空字符串。
            # - 为什么这样写：防止复杂对象进入日志、配置或秘密写入器。
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field.field_id} must be a non-empty string")
            value = value.strip()

        # 本段代码核心功能：检查选择值是否在官方枚举内。
        # - 输入：field.options和规范化value。
        # - 处理：存在选项时执行成员检查。
        # - 输出：非法时抛出ValueError。
        # - 常量依据：环境和协议模式不能由用户任意拼写。
        # - 为什么这样写：避免连接测试收到未审核模式。
        if field.options and value not in field.options:
            raise ValueError(f"invalid option for {field.field_id}")

        # 本段代码核心功能：检查官方确认的字符串格式。
        # - 输入：validation_pattern和规范化value。
        # - 处理：使用完整正则匹配。
        # - 输出：非法时抛出ValueError。
        # - 常量依据：只有目录中存在模式时才检查。
        # - 为什么这样写：完整匹配可阻止额外未预期字符。
        if field.validation_pattern and not re.fullmatch(
            field.validation_pattern,
            str(value),
        ):
            raise ValueError(f"invalid format for {field.field_id}")

        # 本段代码核心功能：将秘密值交给凭据后端并只保存引用。
        # - 输入：CREDENTIAL_REFERENCE字段和当前秘密字符串。
        # - 处理：调用writer.store_secret，不把原文写入返回对象。
        # - 输出：credential_references[field_id]。
        # - 常量依据：秘密字段必须在请求内直接交换成操作系统安全引用。
        # - 为什么这样写：消除普通配置、临时文件和日志中的秘密副本。
        if field.persist_mode is PersistMode.CREDENTIAL_REFERENCE:
            reference = credential_writer.store_secret(
                provider_id=definition.provider_id,
                connection_id=normalized_connection_id,
                field_id=field.field_id,
                secret_value=str(value),
            )
            # 本段代码核心功能：根据条件 `not isinstance(reference, str) or not reference.strip()` 选择安全分支。
            # - 输入：条件表达式和此前已经规范化的局部变量。
            # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
            # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
            # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
            # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

            if not isinstance(reference, str) or not reference.strip():
                raise ValueError(
                    f"credential writer returned no reference for {field.field_id}"
                )
            credential_references[field.field_id] = reference.strip()

        # 本段代码核心功能：仅保存明确标记为普通配置的值。
        # - 输入：CONFIGURATION字段和值。
        # - 处理：写入public_configuration。
        # - 输出：公开配置映射更新。
        # - 常量依据：SECRET字段在目录加载阶段已经被禁止使用该模式。
        # - 为什么这样写：配置白名单防止临时验证码或秘密被意外持久化。
        elif field.persist_mode is PersistMode.CONFIGURATION:
            public_configuration[field.field_id] = value

        # 本段代码核心功能：明确丢弃NEVER持久化字段。
        # - 输入：NEVER字段和值。
        # - 处理：不执行保存动作。
        # - 输出：结果对象中不存在该字段。
        # - 常量依据：一次性验证码或确认文本只能在当前调用中使用。
        # - 为什么这样写：显式分支比隐式落空更便于安全审计。
        else:
            pass

    # 本段代码核心功能：根据授权和交易隔离确认决定初始档案状态。
    # - 输入：三项显式用户确认。
    # - 处理：任一条件未满足时停留在申请/授权阶段；全部满足时标记凭据已保存。
    # - 输出：ConnectionStatus。
    # - 常量依据：只读接入不能仅凭密钥存在就视为获授权。
    # - 为什么这样写：把法律授权、技术权限和交易隔离同时纳入准入。
    if not (
        official_authorization_confirmed
        and read_only_entitlement_confirmed
        and execution_domain_isolated
    ):
        status = ConnectionStatus.OFFICIAL_APPLICATION_REQUIRED
    else:
        status = ConnectionStatus.CREDENTIALS_SAVED

    return ProviderConnectionProfile(
        provider_id=definition.provider_id,
        connection_id=normalized_connection_id,
        status=status,
        public_configuration=dict(public_configuration),
        credential_references=dict(credential_references),
        official_authorization_confirmed=official_authorization_confirmed,
        read_only_entitlement_confirmed=read_only_entitlement_confirmed,
        execution_domain_isolated=execution_domain_isolated,
    )


# 本段代码核心功能：执行连接状态的显式合法迁移。
# - 输入：当前状态和期望目标状态。
# - 处理：查询ALLOWED_STATUS_TRANSITIONS；相同状态视为幂等成功。
# - 输出：合法时返回目标状态，非法时抛出ValueError。
# - 常量依据：只读验证和交易阻断使用不同状态通道。
# - 为什么这样写：所有调用方共享同一迁移规则，避免UI按钮绕过后端门禁。
def transition_connection_status(
    current: ConnectionStatus,
    target: ConnectionStatus,
) -> ConnectionStatus:
    """Validate and apply one connection-state transition."""

    # 本段代码核心功能：允许重复提交同一目标状态。
    # - 输入：current和target。
    # - 处理：相等时直接返回。
    # - 输出：原状态。
    # - 常量依据：UI网络重试和幂等命令可能重复发送状态更新。
    # - 为什么这样写：幂等处理可避免正常重试被误判为非法迁移。
    if current is target:
        return current

    allowed = ALLOWED_STATUS_TRANSITIONS.get(current, frozenset())

    # 本段代码核心功能：阻断不在显式迁移表中的状态变化。
    # - 输入：target和allowed集合。
    # - 处理：成员检查。
    # - 输出：非法时抛出ValueError。
    # - 常量依据：普通流程不能从未配置直接跳到研究就绪或交易可用。
    # - 为什么这样写：保证每个安全和语义门禁都留下可审计状态。
    if target not in allowed:
        raise ValueError(f"illegal connection transition: {current} -> {target}")

    return target


# 本段代码核心功能：生成接入中心首页所需的Provider卡片安全ViewModel。
# - 输入：Provider定义、可选连接档案及可选TASK_024B环境证据状态。
# - 处理：按Provider合并状态、可执行动作、表单可用性和交易阻断提示。
# - 输出：JSON可序列化卡片列表，不包含秘密值或秘密字段当前内容。
# - 常量依据：24B环境盘点是后台提示，不再作为用户唯一交互入口。
# - 为什么这样写：UI通过稳定ViewModel展示“申请—配置—测试—语义审查”完整流程，无需直接读取内部配置文件。
def build_connection_center_view(
    definitions: Sequence[ProviderConnectionDefinition],
    *,
    profiles: Mapping[str, ProviderConnectionProfile] | None = None,
    environment_status: Mapping[str, str] | None = None,
) -> list[dict[str, object]]:
    """Build secret-free provider cards for the future UI."""

    profile_map = profiles or {}
    environment_map = environment_status or {}
    cards: list[dict[str, object]] = []

    # 本段代码核心功能：逐Provider生成独立卡片。
    # - 输入：稳定顺序的Provider定义。
    # - 处理：合并档案、环境状态和表单状态，计算允许的UI动作。
    # - 输出：向cards追加安全字典。
    # - 常量依据：目录顺序体现官方来源和接入优先级。
    # - 为什么这样写：每张卡片独立可测试，也便于未来分页和搜索。
    for definition in definitions:
        profile = profile_map.get(definition.provider_id)

        # 本段代码核心功能：在无连接档案时选择准确的初始状态。
        # - 输入：form_definition_status和official_application_reference。
        # - 处理：字段未审核时优先显示字段规范待确认，否则显示未配置或需申请。
        # - 输出：ConnectionStatus。
        # - 常量依据：不得为具体券商猜测凭据字段。
        # - 为什么这样写：用户应先看到缺什么官方材料，而不是一个无法工作的通用密钥框。
        if profile is None:
            # 本段代码核心功能：根据条件 `definition.form_definition_status != 'OFFICIAL_FIELDS_VERIFIED'` 选择安全分支。
            # - 输入：条件表达式和此前已经规范化的局部变量。
            # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
            # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
            # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
            # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

            if definition.form_definition_status != "OFFICIAL_FIELDS_VERIFIED":
                status = ConnectionStatus.OFFICIAL_FIELD_SPEC_REQUIRED
            # 本段代码核心功能：根据条件 `definition.official_application_reference` 选择安全分支。
            # - 输入：条件表达式和此前已经规范化的局部变量。
            # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
            # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
            # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
            # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

            elif definition.official_application_reference:
                status = ConnectionStatus.OFFICIAL_APPLICATION_REQUIRED
            else:
                status = ConnectionStatus.NOT_CONFIGURED
        else:
            status = profile.status

        actions: list[str] = ["VIEW_OFFICIAL_APPLICATION_GUIDANCE"]

        # 本段代码核心功能：只有官方字段已核验时开放配置动作。
        # - 输入：form_definition_status。
        # - 处理：精确比较审核状态。
        # - 输出：可能追加OPEN_CONNECTION_FORM。
        # - 常量依据：未核验字段时不能让用户猜测输入。
        # - 为什么这样写：表单开放本身就是一项来源权威门禁。
        if definition.form_definition_status == "OFFICIAL_FIELDS_VERIFIED":
            actions.append("OPEN_CONNECTION_FORM")

        # 本段代码核心功能：只有凭据已保存或测试失败时开放只读重试。
        # - 输入：当前status。
        # - 处理：检查状态集合。
        # - 输出：可能追加RUN_READ_ONLY_CONNECTION_TEST。
        # - 常量依据：连接测试不得在没有安全凭据引用时运行。
        # - 为什么这样写：避免UI按钮触发空连接或要求明文重新提交。
        if status in {
            ConnectionStatus.CREDENTIALS_SAVED,
            ConnectionStatus.CONNECTION_TEST_FAILED,
        }:
            actions.append("RUN_READ_ONLY_CONNECTION_TEST")

        # 本段代码核心功能：允许已配置连接被停用或删除引用。
        # - 输入：profile是否存在。
        # - 处理：存在时追加停用动作。
        # - 输出：可能追加DISABLE_CONNECTION。
        # - 常量依据：用户必须能够撤销接入而不编辑文件。
        # - 为什么这样写：可撤销性是凭据和第三方接入的基本安全要求。
        if profile is not None:
            actions.append("DISABLE_CONNECTION")

        cards.append(
            {
                "provider_id": definition.provider_id,
                "display_name": definition.display_name,
                "provider_kind": definition.provider_kind,
                "authority_tier": definition.authority_tier,
                "status": status.value,
                "environment_status": environment_map.get(
                    definition.provider_id,
                    "NOT_SCANNED",
                ),
                "official_application_reference": (
                    definition.official_application_reference
                ),
                "form_definition_status": definition.form_definition_status,
                "supports_read_only_data": definition.supports_read_only_data,
                "execution_activation": "BLOCKED",
                "contains_execution_capability": (
                    definition.contains_execution_capability
                ),
                "available_actions": actions,
                "form_schema": build_dynamic_form_schema(definition),
            }
        )

    return cards


# 本段代码核心功能：把安全连接档案转换成稳定JSON字典。
# - 输入：ProviderConnectionProfile。
# - 处理：使用dataclasses.asdict并把枚举转为字符串；执行秘密键名防御检查。
# - 输出：可持久化或传给UI的字典。
# - 常量依据：档案只允许公开配置和凭据引用。
# - 为什么这样写：集中序列化可以阻止调用方直接把任意对象或秘密写入报告。
def profile_to_safe_dict(profile: ProviderConnectionProfile) -> dict[str, object]:
    """Serialize a connection profile without secret material."""

    payload = asdict(profile)
    payload["status"] = profile.status.value

    # 本段代码核心功能：在序列化出口阻断公开配置中出现常见秘密原文字段名。
    # - 输入：档案顶层键和public_configuration键。
    # - 处理：允许credential_references使用真实字段标识，但拒绝秘密键出现在普通配置或顶层。
    # - 输出：发现危险键时抛出ValueError。
    # - 常量依据：凭据引用映射必须知道它对应api_key等字段；被禁止的是秘密原文进入公开配置。
    # - 为什么这样写：既保留可定位的字段级引用，又防止未来扩展把秘密值误放到普通配置。
    forbidden_keys = {
        "password",
        "api_key",
        "api_secret",
        "token",
        "secret_value",
    }
    top_level_keys = {str(key).lower() for key in payload}
    public_keys = {
        str(key).lower()
        for key in profile.public_configuration
    }

    # 本段代码核心功能：拒绝秘密键出现在顶层或公开配置区域。
    # - 输入：forbidden_keys、top_level_keys和public_keys。
    # - 处理：计算集合交集。
    # - 输出：存在交集时抛出ValueError。
    # - 常量依据：credential_references区域不参与该交集，因为其值是安全引用而非原文。
    # - 为什么这样写：防止误报合法引用，同时保持公开配置的严格防泄露门禁。
    if forbidden_keys & (top_level_keys | public_keys):
        raise ValueError("connection profile contains a forbidden secret field")

    return payload
