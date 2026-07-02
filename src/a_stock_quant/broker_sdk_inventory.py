# 本文件核心功能：在不导入、不登录、不联网的前提下，盘点用户明确提供的官方券商SDK与开发文档证据。
# - 输入：官方券商规则、专用证据目录、TASK_023B安全报告和用户填写的非秘密授权确认文件。
# - 处理：只读取JSON文本和文件名元数据，按官方来源、授权、只读行情权限及交易域隔离四道门禁评分。
# - 输出：UTF-8 JSON盘点报告、候选排序、阻断原因和下一任务状态；不输出绝对路径或秘密值。
# - 常量依据：来源优先级来自TASK_024A，教学注释门禁来自TASK_024A1，券商能力只采用官方资料已核验范围。
# - 为什么这样写：先确认用户真正拥有且获准使用的官方SDK，再做薄适配，避免第三方优先、无授权开发和交易能力误激活。
"""TASK_024B authorized broker SDK read-only inventory."""

from __future__ import annotations

import json
import os
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Mapping, Sequence


# 本段代码核心功能：定义秘密字段名称的拒绝模式，防止授权确认文件夹带账号、密码、Token、IP或端口。
# - 输入：固定的字段名正则表达式，不从用户文件动态扩展。
# - 处理：使用大小写不敏感匹配识别高风险键名。
# - 输出：供JSON安全校验函数复用的编译后正则对象。
# - 常量依据：TASK_024B只允许非秘密授权事实，连接参数和账户信息必须留在券商官方客户端或未来秘密管理层。
# - 为什么这样写：在读取授权文件时先阻断秘密字段，比依赖使用者自觉删除敏感信息更可靠。
SECRET_KEY_PATTERN = re.compile(
    r"(password|passwd|token|secret|api[_-]?key|account|user[_-]?id|"
    r"login|credential|host|ip|port)",
    re.IGNORECASE,
)


# 本段代码核心功能：定义允许进入证据扫描的文件扩展名上限，限制扫描器只关注SDK包和开发文档。
# - 输入：固定扩展名集合。
# - 处理：全部转换为小写并保持不可变。
# - 输出：供文件名匹配函数过滤无关文件。
# - 常量依据：常见官方交付形态包括ZIP、Wheel、动态库、安装包、PDF、Word、CHM和纯文本说明。
# - 为什么这样写：限定扩展名能够减少误命中和隐私暴露，也避免扫描器把普通个人文件纳入报告。
DEFAULT_ALLOWED_EXTENSIONS = (
    ".zip",
    ".whl",
    ".tar.gz",
    ".tgz",
    ".7z",
    ".rar",
    ".pyd",
    ".dll",
    ".so",
    ".exe",
    ".msi",
    ".pdf",
    ".doc",
    ".docx",
    ".chm",
    ".md",
    ".txt",
)


# 本段代码核心功能：定义 `BrokerSdkRule`，保存单一券商官方SDK的证据匹配与安全策略。
# - 输入：由UTF-8规则配置加载器显式传入的字段。
# - 处理：使用不可变数据类隔离原始JSON，避免运行中修改候选规则。
# - 输出：可比较、可排序且可序列化的券商规则对象。
# - 常量依据：候选券商、官方域名和能力边界来自TASK_024A官方目录，不代表用户已经获得授权。
# - 为什么这样写：把产品存在、文件匹配和实际授权拆开，防止仅凭文件名就把券商Provider误判为可接入。
@dataclass(frozen=True)
class BrokerSdkRule:
    """Official broker SDK evidence rule."""

    provider_id: str
    display_name: str
    catalog_source_id: str
    strategy_rank: int
    official_domains: tuple[str, ...]
    artifact_name_tokens: tuple[str, ...]
    allowed_extensions: tuple[str, ...]
    read_only_capability_markers: tuple[str, ...]
    execution_capability_markers: tuple[str, ...]
    verified_runtime_notes: tuple[str, ...]
    official_evidence_status: str


# 本段代码核心功能：定义 `AuthorizationEvidence`，保存用户对授权与只读权限的非秘密确认。
# - 输入：用户本地JSON中的布尔值和版本标签；不接受账号、密码、Token、服务器地址或端口。
# - 处理：把缺省值保持为False或空字符串，避免把未知状态当作已确认。
# - 输出：供候选门禁使用的不可变授权证据对象。
# - 常量依据：TASK_024B要求官方包、用户授权、只读行情权限和交易域隔离四项同时成立。
# - 为什么这样写：授权事实必须由用户显式确认，程序不能根据已安装客户端或文件名自行推断。
@dataclass(frozen=True)
class AuthorizationEvidence:
    """Non-secret user confirmation for one broker product."""

    provider_id: str
    official_package_confirmed: bool
    user_authorization_confirmed: bool
    read_only_quote_entitlement_confirmed: bool
    execution_domain_present: bool
    execution_domain_isolated_confirmed: bool
    sdk_version: str
    client_version: str
    documentation_version: str


# 本段代码核心功能：定义 `ArtifactEvidence`，保存专用证据目录中命中的安全文件名元数据。
# - 输入：规则匹配后的根目录标签、文件基名和TASK_023B安全报告中的模块或客户端名称。
# - 处理：只保存命中项，不保存绝对路径、未命中文件或文件内容。
# - 输出：单一Provider的本地证据集合。
# - 常量依据：本任务禁止整盘扫描和秘密值记录，路径仅用调用方提供的匿名标签表示。
# - 为什么这样写：保留足够的可审计证据，同时避免把用户目录结构和无关软件清单写入报告。
@dataclass(frozen=True)
class ArtifactEvidence:
    """Sanitized local evidence for one provider."""

    provider_id: str
    matched_artifact_names: tuple[str, ...]
    matched_root_labels: tuple[str, ...]
    detected_module_names: tuple[str, ...]
    matched_installed_application_names: tuple[str, ...]


# 本段代码核心功能：定义 `BrokerSdkFinding`，汇总单一券商候选的证据、评分、状态和阻断原因。
# - 输入：BrokerSdkRule、ArtifactEvidence和AuthorizationEvidence的评估结果。
# - 处理：所有状态由纯函数生成，报告层不再重新推断授权或能力。
# - 输出：可序列化的候选盘点结果。
# - 常量依据：READY状态必须满足四道门禁；任何交易能力都不能因此获得激活权限。
# - 为什么这样写：集中保存判定依据便于人工复核，也让下一薄适配任务只接受明确READY候选。
@dataclass(frozen=True)
class BrokerSdkFinding:
    """Evaluated broker SDK candidate."""

    provider_id: str
    display_name: str
    catalog_source_id: str
    strategy_rank: int
    evidence_score: int
    official_evidence_status: str
    matched_artifact_names: tuple[str, ...]
    matched_root_labels: tuple[str, ...]
    detected_module_names: tuple[str, ...]
    matched_installed_application_names: tuple[str, ...]
    official_package_confirmed: bool
    user_authorization_confirmed: bool
    read_only_quote_entitlement_confirmed: bool
    execution_domain_present: bool
    execution_domain_isolated_confirmed: bool
    sdk_version: str
    client_version: str
    documentation_version: str
    candidate_status: str
    eligible_for_read_only_adapter_task: bool
    blockers: tuple[str, ...]


# 本段代码核心功能：定义 `_string_tuple`，校验JSON中的字符串数组并统一去空白、去重复。
# - 输入：原始对象和字段名。
# - 处理：要求列表内每项为非空字符串，按首次出现顺序去重。
# - 输出：不可变字符串元组。
# - 常量依据：配置字段需要稳定排序和可重复报告，空字符串不能成为文件匹配规则。
# - 为什么这样写：强校验能在扫描前暴露配置错误，避免宽松规则误命中用户文件。
def _string_tuple(value: object, field_name: str) -> tuple[str, ...]:
    """Validate and normalize a JSON string list."""

    # 本段代码核心功能：根据条件 `not isinstance(value, list)` 选择安全分支。
    # - 输入：条件表达式和此前已经规范化的局部变量。
    # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
    # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
    # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a list")
    normalized: list[str] = []
    seen: set[str] = set()
    # 本段代码核心功能：逐项遍历有限配置条目、发现证据或测试样本。
    # - 输入：可迭代的配置、证据或样本序列。
    # - 处理：每轮只更新当前条目局部结果，最终按稳定顺序汇总。
    # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
    # - 为什么这样写：逐项处理保留来源级证据，避免聚合后无法追溯单个Provider。

    for item in value:
        # 本段代码核心功能：根据条件 `not isinstance(item, str) or not item.strip()` 选择安全分支。
        # - 输入：条件表达式和此前已经规范化的局部变量。
        # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
        # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
        # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"{field_name} must contain non-empty strings")
        text = item.strip()
        # 本段代码核心功能：根据条件 `text not in seen` 选择安全分支。
        # - 输入：条件表达式和此前已经规范化的局部变量。
        # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
        # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
        # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

        if text not in seen:
            seen.add(text)
            normalized.append(text)
    return tuple(normalized)


# 本段代码核心功能：定义 `_safe_text`，校验授权证据中的可公开版本标签。
# - 输入：原始值、字段名和最大长度。
# - 处理：只允许短字符串，拒绝换行、控制字符和疑似秘密字段表达式。
# - 输出：清理后的字符串；空值返回空字符串。
# - 常量依据：版本号和文档版本不需要包含连接参数，默认最大长度128字符。
# - 为什么这样写：限制自由文本可以降低用户误把账号或服务器信息写入报告的概率。
def _safe_text(value: object, field_name: str, maximum_length: int = 128) -> str:
    """Validate a short non-secret metadata string."""

    # 本段代码核心功能：根据条件 `value is None` 选择安全分支。
    # - 输入：条件表达式和此前已经规范化的局部变量。
    # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
    # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
    # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

    if value is None:
        return ""
    # 本段代码核心功能：根据条件 `not isinstance(value, str)` 选择安全分支。
    # - 输入：条件表达式和此前已经规范化的局部变量。
    # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
    # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
    # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    text = value.strip()
    # 本段代码核心功能：根据条件 `len(text) > maximum_length` 选择安全分支。
    # - 输入：条件表达式和此前已经规范化的局部变量。
    # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
    # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
    # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

    if len(text) > maximum_length:
        raise ValueError(f"{field_name} is too long")
    # 本段代码核心功能：根据条件 `any((ord(character) < 32 for character in text))` 选择安全分支。
    # - 输入：条件表达式和此前已经规范化的局部变量。
    # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
    # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
    # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

    if any(ord(character) < 32 for character in text):
        raise ValueError(f"{field_name} contains control characters")
    # 本段代码核心功能：根据条件 `SECRET_KEY_PATTERN.search(field_name)` 选择安全分支。
    # - 输入：条件表达式和此前已经规范化的局部变量。
    # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
    # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
    # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

    if SECRET_KEY_PATTERN.search(field_name):
        raise ValueError(f"secret-like field is forbidden: {field_name}")
    return text


# 本段代码核心功能：定义 `_assert_no_secret_keys`，递归检查JSON对象是否包含被禁止的秘密字段名。
# - 输入：任意JSON解析结果和当前字段路径。
# - 处理：遍历字典键和值及列表元素，命中SECRET_KEY_PATTERN立即失败。
# - 输出：安全时无返回值；发现高风险字段时抛出ValueError。
# - 常量依据：授权证据只允许布尔事实和版本标签，账户与连接信息不属于本任务合同。
# - 为什么这样写：递归检查能够阻断秘密字段藏在嵌套对象或数组中的绕过方式。
def _assert_no_secret_keys(value: object, path: str = "root") -> None:
    """Reject secret-like JSON keys at any nesting level."""

    # 本段代码核心功能：根据条件 `isinstance(value, dict)` 选择安全分支。
    # - 输入：条件表达式和此前已经规范化的局部变量。
    # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
    # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
    # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

    if isinstance(value, dict):
        # 本段代码核心功能：逐项遍历有限配置条目、发现证据或测试样本。
        # - 输入：可迭代的配置、证据或样本序列。
        # - 处理：每轮只更新当前条目局部结果，最终按稳定顺序汇总。
        # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
        # - 为什么这样写：逐项处理保留来源级证据，避免聚合后无法追溯单个Provider。

        for key, nested_value in value.items():
            # 本段代码核心功能：根据条件 `not isinstance(key, str)` 选择安全分支。
            # - 输入：条件表达式和此前已经规范化的局部变量。
            # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
            # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
            # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
            # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

            if not isinstance(key, str):
                raise ValueError(f"non-string JSON key at {path}")
            # 本段代码核心功能：根据条件 `SECRET_KEY_PATTERN.search(key)` 选择安全分支。
            # - 输入：条件表达式和此前已经规范化的局部变量。
            # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
            # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
            # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
            # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

            if SECRET_KEY_PATTERN.search(key):
                raise ValueError(f"secret-like field is forbidden: {path}.{key}")
            _assert_no_secret_keys(nested_value, f"{path}.{key}")
    # 本段代码核心功能：根据条件 `isinstance(value, list)` 选择安全分支。
    # - 输入：条件表达式和此前已经规范化的局部变量。
    # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
    # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
    # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

    elif isinstance(value, list):
        # 本段代码核心功能：逐项遍历有限配置条目、发现证据或测试样本。
        # - 输入：可迭代的配置、证据或样本序列。
        # - 处理：每轮只更新当前条目局部结果，最终按稳定顺序汇总。
        # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
        # - 为什么这样写：逐项处理保留来源级证据，避免聚合后无法追溯单个Provider。

        for index, nested_value in enumerate(value):
            _assert_no_secret_keys(nested_value, f"{path}[{index}]")


# 本段代码核心功能：定义 `load_broker_sdk_rules`，读取并强制执行TASK_024B安全开关。
# - 输入：UTF-8规则配置路径。
# - 处理：校验零网络、零SDK导入、零登录、零交易、零秘密值、禁止整盘扫描和禁止记录绝对路径。
# - 输出：按strategy_rank和provider_id稳定排序的BrokerSdkRule元组。
# - 常量依据：安全开关来自TASK_024B任务书，候选内容来自TASK_024A官方接口目录。
# - 为什么这样写：扫描器只有在配置显式保持只读时才启动，防止后续配置修改悄悄扩大权限。
def load_broker_sdk_rules(path: str | Path) -> tuple[BrokerSdkRule, ...]:
    """Load validated broker SDK inventory rules."""

    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    required_false_flags = (
        "network_calls_allowed",
        "vendor_sdk_import_allowed",
        "broker_login_allowed",
        "trade_session_initialization_allowed",
        "order_submission_allowed",
        "secret_values_allowed",
        "whole_drive_scan_allowed",
        "file_content_read_allowed",
        "absolute_paths_recorded",
    )
    # 本段代码核心功能：逐项遍历有限配置条目、发现证据或测试样本。
    # - 输入：可迭代的配置、证据或样本序列。
    # - 处理：每轮只更新当前条目局部结果，最终按稳定顺序汇总。
    # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
    # - 为什么这样写：逐项处理保留来源级证据，避免聚合后无法追溯单个Provider。

    for field_name in required_false_flags:
        # 本段代码核心功能：根据条件 `payload.get(field_name) is not False` 选择安全分支。
        # - 输入：条件表达式和此前已经规范化的局部变量。
        # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
        # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
        # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

        if payload.get(field_name) is not False:
            raise ValueError(f"{field_name} must be false")

    raw_providers = payload.get("providers")
    # 本段代码核心功能：根据条件 `not isinstance(raw_providers, list) or not raw_providers` 选择安全分支。
    # - 输入：条件表达式和此前已经规范化的局部变量。
    # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
    # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
    # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

    if not isinstance(raw_providers, list) or not raw_providers:
        raise ValueError("providers must be a non-empty list")

    rules: list[BrokerSdkRule] = []
    seen: set[str] = set()
    # 本段代码核心功能：逐项遍历有限配置条目、发现证据或测试样本。
    # - 输入：可迭代的配置、证据或样本序列。
    # - 处理：每轮只更新当前条目局部结果，最终按稳定顺序汇总。
    # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
    # - 为什么这样写：逐项处理保留来源级证据，避免聚合后无法追溯单个Provider。

    for raw in raw_providers:
        # 本段代码核心功能：根据条件 `not isinstance(raw, dict)` 选择安全分支。
        # - 输入：条件表达式和此前已经规范化的局部变量。
        # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
        # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
        # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

        if not isinstance(raw, dict):
            raise ValueError("each provider rule must be an object")
        provider_id = _safe_text(raw.get("provider_id"), "provider_id")
        # 本段代码核心功能：根据条件 `not provider_id` 选择安全分支。
        # - 输入：条件表达式和此前已经规范化的局部变量。
        # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
        # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
        # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

        if not provider_id:
            raise ValueError("provider_id must not be empty")
        # 本段代码核心功能：根据条件 `provider_id in seen` 选择安全分支。
        # - 输入：条件表达式和此前已经规范化的局部变量。
        # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
        # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
        # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

        if provider_id in seen:
            raise ValueError(f"duplicate provider_id: {provider_id}")
        seen.add(provider_id)
        strategy_rank = raw.get("strategy_rank")
        # 本段代码核心功能：根据条件 `not isinstance(strategy_rank, int) or strategy_rank < 0` 选择安全分支。
        # - 输入：条件表达式和此前已经规范化的局部变量。
        # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
        # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
        # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

        if not isinstance(strategy_rank, int) or strategy_rank < 0:
            raise ValueError(f"invalid strategy_rank for {provider_id}")

        allowed_extensions = tuple(
            extension.lower()
            for extension in _string_tuple(
                raw.get("allowed_extensions", list(DEFAULT_ALLOWED_EXTENSIONS)),
                f"{provider_id}.allowed_extensions",
            )
        )
        rules.append(
            BrokerSdkRule(
                provider_id=provider_id,
                display_name=_safe_text(raw.get("display_name"), "display_name"),
                catalog_source_id=_safe_text(
                    raw.get("catalog_source_id"), "catalog_source_id"
                ),
                strategy_rank=strategy_rank,
                official_domains=_string_tuple(
                    raw.get("official_domains", []),
                    f"{provider_id}.official_domains",
                ),
                artifact_name_tokens=_string_tuple(
                    raw.get("artifact_name_tokens", []),
                    f"{provider_id}.artifact_name_tokens",
                ),
                allowed_extensions=allowed_extensions,
                read_only_capability_markers=_string_tuple(
                    raw.get("read_only_capability_markers", []),
                    f"{provider_id}.read_only_capability_markers",
                ),
                execution_capability_markers=_string_tuple(
                    raw.get("execution_capability_markers", []),
                    f"{provider_id}.execution_capability_markers",
                ),
                verified_runtime_notes=_string_tuple(
                    raw.get("verified_runtime_notes", []),
                    f"{provider_id}.verified_runtime_notes",
                ),
                official_evidence_status=_safe_text(
                    raw.get("official_evidence_status"),
                    "official_evidence_status",
                ),
            )
        )
    return tuple(sorted(rules, key=lambda item: (item.strategy_rank, item.provider_id)))


# 本段代码核心功能：定义 `load_authorization_evidence`，读取用户填写的非秘密授权确认。
# - 输入：可选UTF-8 JSON路径和允许的provider_id集合。
# - 处理：文件不存在时返回空映射；存在时递归拒绝秘密字段并强校验布尔值与版本标签。
# - 输出：provider_id到AuthorizationEvidence的映射。
# - 常量依据：未知、缺失或未填写的授权状态一律按False处理，不进行乐观推断。
# - 为什么这样写：允许任务在没有SDK时安全运行，同时要求真正的候选必须由用户明确确认。
def load_authorization_evidence(
    path: str | Path | None,
    allowed_provider_ids: Iterable[str],
) -> dict[str, AuthorizationEvidence]:
    """Load a local non-secret authorization confirmation file."""

    # 本段代码核心功能：根据条件 `path is None` 选择安全分支。
    # - 输入：条件表达式和此前已经规范化的局部变量。
    # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
    # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
    # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

    if path is None:
        return {}
    evidence_path = Path(path)
    # 本段代码核心功能：根据条件 `not evidence_path.is_file()` 选择安全分支。
    # - 输入：条件表达式和此前已经规范化的局部变量。
    # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
    # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
    # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

    if not evidence_path.is_file():
        return {}

    payload = json.loads(evidence_path.read_text(encoding="utf-8-sig"))
    _assert_no_secret_keys(payload)
    raw_entries = payload.get("providers") if isinstance(payload, dict) else None
    # 本段代码核心功能：根据条件 `not isinstance(raw_entries, list)` 选择安全分支。
    # - 输入：条件表达式和此前已经规范化的局部变量。
    # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
    # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
    # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

    if not isinstance(raw_entries, list):
        raise ValueError("authorization providers must be a list")

    allowed = set(allowed_provider_ids)
    result: dict[str, AuthorizationEvidence] = {}
    boolean_fields = (
        "official_package_confirmed",
        "user_authorization_confirmed",
        "read_only_quote_entitlement_confirmed",
        "execution_domain_present",
        "execution_domain_isolated_confirmed",
    )
    # 本段代码核心功能：逐项遍历有限配置条目、发现证据或测试样本。
    # - 输入：可迭代的配置、证据或样本序列。
    # - 处理：每轮只更新当前条目局部结果，最终按稳定顺序汇总。
    # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
    # - 为什么这样写：逐项处理保留来源级证据，避免聚合后无法追溯单个Provider。

    for raw in raw_entries:
        # 本段代码核心功能：根据条件 `not isinstance(raw, dict)` 选择安全分支。
        # - 输入：条件表达式和此前已经规范化的局部变量。
        # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
        # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
        # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

        if not isinstance(raw, dict):
            raise ValueError("authorization entry must be an object")
        provider_id = _safe_text(raw.get("provider_id"), "provider_id")
        # 本段代码核心功能：根据条件 `provider_id not in allowed` 选择安全分支。
        # - 输入：条件表达式和此前已经规范化的局部变量。
        # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
        # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
        # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

        if provider_id not in allowed:
            raise ValueError(f"unknown provider_id in authorization file: {provider_id}")
        # 本段代码核心功能：根据条件 `provider_id in result` 选择安全分支。
        # - 输入：条件表达式和此前已经规范化的局部变量。
        # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
        # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
        # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

        if provider_id in result:
            raise ValueError(f"duplicate authorization provider_id: {provider_id}")
        # 本段代码核心功能：逐项遍历有限配置条目、发现证据或测试样本。
        # - 输入：可迭代的配置、证据或样本序列。
        # - 处理：每轮只更新当前条目局部结果，最终按稳定顺序汇总。
        # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
        # - 为什么这样写：逐项处理保留来源级证据，避免聚合后无法追溯单个Provider。

        for field_name in boolean_fields:
            # 本段代码核心功能：根据条件 `not isinstance(raw.get(field_name, False), bool)` 选择安全分支。
            # - 输入：条件表达式和此前已经规范化的局部变量。
            # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
            # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
            # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
            # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

            if not isinstance(raw.get(field_name, False), bool):
                raise ValueError(f"{provider_id}.{field_name} must be boolean")
        result[provider_id] = AuthorizationEvidence(
            provider_id=provider_id,
            official_package_confirmed=raw.get(
                "official_package_confirmed", False
            ),
            user_authorization_confirmed=raw.get(
                "user_authorization_confirmed", False
            ),
            read_only_quote_entitlement_confirmed=raw.get(
                "read_only_quote_entitlement_confirmed", False
            ),
            execution_domain_present=raw.get(
                "execution_domain_present", False
            ),
            execution_domain_isolated_confirmed=raw.get(
                "execution_domain_isolated_confirmed", False
            ),
            sdk_version=_safe_text(raw.get("sdk_version"), "sdk_version"),
            client_version=_safe_text(
                raw.get("client_version"), "client_version"
            ),
            documentation_version=_safe_text(
                raw.get("documentation_version"),
                "documentation_version",
            ),
        )
    return result


# 本段代码核心功能：定义 `_file_name_matches`，判断单个文件名是否属于某券商规则的SDK或文档证据。
# - 输入：文件基名和BrokerSdkRule。
# - 处理：先检查允许扩展名，再要求至少一个官方产品标记出现在小写文件名中。
# - 输出：匹配返回True，否则False。
# - 常量依据：规则中的标记来自官方产品名称或官方仓库文件命名，不使用模糊供应商猜测。
# - 为什么这样写：扩展名与产品标记同时满足可以降低普通文件被误识别为官方SDK的风险。
def _file_name_matches(file_name: str, rule: BrokerSdkRule) -> bool:
    """Return whether a basename is safe evidence for one rule."""

    lower_name = file_name.lower()
    extension_match = any(
        lower_name.endswith(extension) for extension in rule.allowed_extensions
    )
    # 本段代码核心功能：根据条件 `not extension_match` 选择安全分支。
    # - 输入：条件表达式和此前已经规范化的局部变量。
    # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
    # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
    # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

    if not extension_match:
        return False
    return any(token.lower() in lower_name for token in rule.artifact_name_tokens)


# 本段代码核心功能：定义 `scan_evidence_roots`，在调用方明确指定的专用目录内盘点文件名证据。
# - 输入：券商规则、标签到目录的映射、最大目录深度和最大文件数。
# - 处理：不跟随符号链接、不读取文件内容、不扫描盘符根目录，命中后只保存文件基名和匿名根标签。
# - 输出：provider_id到ArtifactEvidence的初始映射及实际扫描文件数。
# - 常量依据：默认深度4、文件上限5000是单机安全阈值；whole-drive扫描由规则硬门禁禁止。
# - 为什么这样写：专用证据目录足以确认用户持有的官方包，又不会把整台电脑的文件结构暴露给报告。
def scan_evidence_roots(
    rules: Sequence[BrokerSdkRule],
    roots: Mapping[str, str | Path],
    *,
    maximum_depth: int = 4,
    maximum_files: int = 5000,
) -> tuple[dict[str, ArtifactEvidence], int]:
    """Scan only explicitly supplied intake roots using filename metadata."""

    # 本段代码核心功能：根据条件 `maximum_depth < 0 or maximum_depth > 12` 选择安全分支。
    # - 输入：条件表达式和此前已经规范化的局部变量。
    # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
    # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
    # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

    if maximum_depth < 0 or maximum_depth > 12:
        raise ValueError("maximum_depth must be between 0 and 12")
    # 本段代码核心功能：根据条件 `maximum_files < 1 or maximum_files > 100000` 选择安全分支。
    # - 输入：条件表达式和此前已经规范化的局部变量。
    # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
    # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
    # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

    if maximum_files < 1 or maximum_files > 100_000:
        raise ValueError("maximum_files must be between 1 and 100000")

    artifacts: dict[str, set[str]] = {rule.provider_id: set() for rule in rules}
    root_labels: dict[str, set[str]] = {rule.provider_id: set() for rule in rules}
    scanned_file_count = 0

    # 本段代码核心功能：逐项遍历有限配置条目、发现证据或测试样本。
    # - 输入：可迭代的配置、证据或样本序列。
    # - 处理：每轮只更新当前条目局部结果，最终按稳定顺序汇总。
    # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
    # - 为什么这样写：逐项处理保留来源级证据，避免聚合后无法追溯单个Provider。

    for raw_label, raw_root in roots.items():
        label = _safe_text(raw_label, "root_label", maximum_length=64)
        # 本段代码核心功能：根据条件 `not label` 选择安全分支。
        # - 输入：条件表达式和此前已经规范化的局部变量。
        # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
        # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
        # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

        if not label:
            raise ValueError("root label must not be empty")
        root = Path(raw_root).expanduser().resolve()
        # 本段代码核心功能：根据条件 `not root.is_dir()` 选择安全分支。
        # - 输入：条件表达式和此前已经规范化的局部变量。
        # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
        # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
        # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

        if not root.is_dir():
            continue
        # 本段代码核心功能：根据条件 `root.parent == root` 选择安全分支。
        # - 输入：条件表达式和此前已经规范化的局部变量。
        # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
        # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
        # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

        if root.parent == root:
            raise ValueError("drive or filesystem root scanning is forbidden")

        # 本段代码核心功能：逐项遍历有限配置条目、发现证据或测试样本。
        # - 输入：可迭代的配置、证据或样本序列。
        # - 处理：每轮只更新当前条目局部结果，最终按稳定顺序汇总。
        # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
        # - 为什么这样写：逐项处理保留来源级证据，避免聚合后无法追溯单个Provider。

        for current_root, directory_names, file_names in os.walk(
            root,
            topdown=True,
            followlinks=False,
        ):
            current_path = Path(current_root)
            relative_parts = current_path.relative_to(root).parts
            # 本段代码核心功能：根据条件 `len(relative_parts) >= maximum_depth` 选择安全分支。
            # - 输入：条件表达式和此前已经规范化的局部变量。
            # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
            # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
            # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
            # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

            if len(relative_parts) >= maximum_depth:
                directory_names[:] = []
            directory_names[:] = sorted(
                name
                for name in directory_names
                if not (current_path / name).is_symlink()
            )
            # 本段代码核心功能：逐项遍历有限配置条目、发现证据或测试样本。
            # - 输入：可迭代的配置、证据或样本序列。
            # - 处理：每轮只更新当前条目局部结果，最终按稳定顺序汇总。
            # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
            # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
            # - 为什么这样写：逐项处理保留来源级证据，避免聚合后无法追溯单个Provider。

            for file_name in sorted(file_names):
                scanned_file_count += 1
                # 本段代码核心功能：根据条件 `scanned_file_count > maximum_files` 选择安全分支。
                # - 输入：条件表达式和此前已经规范化的局部变量。
                # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
                # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
                # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
                # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

                if scanned_file_count > maximum_files:
                    raise RuntimeError("evidence scan file limit exceeded")
                # 本段代码核心功能：逐项遍历有限配置条目、发现证据或测试样本。
                # - 输入：可迭代的配置、证据或样本序列。
                # - 处理：每轮只更新当前条目局部结果，最终按稳定顺序汇总。
                # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
                # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
                # - 为什么这样写：逐项处理保留来源级证据，避免聚合后无法追溯单个Provider。

                for rule in rules:
                    # 本段代码核心功能：根据条件 `_file_name_matches(file_name, rule)` 选择安全分支。
                    # - 输入：条件表达式和此前已经规范化的局部变量。
                    # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
                    # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
                    # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
                    # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

                    if _file_name_matches(file_name, rule):
                        artifacts[rule.provider_id].add(file_name)
                        root_labels[rule.provider_id].add(label)

    result = {
        rule.provider_id: ArtifactEvidence(
            provider_id=rule.provider_id,
            matched_artifact_names=tuple(sorted(artifacts[rule.provider_id])),
            matched_root_labels=tuple(sorted(root_labels[rule.provider_id])),
            detected_module_names=(),
            matched_installed_application_names=(),
        )
        for rule in rules
    }
    return result, scanned_file_count


# 本段代码核心功能：定义 `merge_task_023b_evidence`，把既有安全报告中的模块和客户端名称并入24B证据。
# - 输入：当前ArtifactEvidence映射、可选TASK_023B报告路径和provider别名映射。
# - 处理：只读取报告已脱敏字段，不读取注册表、安装路径或秘密值；未知provider忽略。
# - 输出：新的ArtifactEvidence映射，原映射保持不变。
# - 常量依据：TASK_023B报告合同只包含命中客户端名称、模块名称和零秘密计数。
# - 为什么这样写：复用已有机器盘点结果可以避免重复扫描，同时不把“安装存在”误当作“已授权”。
def merge_task_023b_evidence(
    evidence_by_provider: Mapping[str, ArtifactEvidence],
    task_023b_report_path: str | Path | None,
    provider_aliases: Mapping[str, str] | None = None,
) -> dict[str, ArtifactEvidence]:
    """Merge sanitized module and installed-client evidence from TASK_023B."""

    merged = dict(evidence_by_provider)
    # 本段代码核心功能：根据条件 `task_023b_report_path is None` 选择安全分支。
    # - 输入：条件表达式和此前已经规范化的局部变量。
    # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
    # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
    # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

    if task_023b_report_path is None:
        return merged
    report_path = Path(task_023b_report_path)
    # 本段代码核心功能：根据条件 `not report_path.is_file()` 选择安全分支。
    # - 输入：条件表达式和此前已经规范化的局部变量。
    # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
    # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
    # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

    if not report_path.is_file():
        return merged

    payload = json.loads(report_path.read_text(encoding="utf-8-sig"))
    aliases = dict(provider_aliases or {})
    findings = payload.get("findings") if isinstance(payload, dict) else None
    # 本段代码核心功能：根据条件 `not isinstance(findings, list)` 选择安全分支。
    # - 输入：条件表达式和此前已经规范化的局部变量。
    # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
    # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
    # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

    if not isinstance(findings, list):
        raise ValueError("TASK_023B report findings must be a list")

    # 本段代码核心功能：逐项遍历有限配置条目、发现证据或测试样本。
    # - 输入：可迭代的配置、证据或样本序列。
    # - 处理：每轮只更新当前条目局部结果，最终按稳定顺序汇总。
    # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
    # - 为什么这样写：逐项处理保留来源级证据，避免聚合后无法追溯单个Provider。

    for raw in findings:
        # 本段代码核心功能：根据条件 `not isinstance(raw, dict)` 选择安全分支。
        # - 输入：条件表达式和此前已经规范化的局部变量。
        # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
        # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
        # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

        if not isinstance(raw, dict):
            continue
        raw_provider_id = raw.get("provider_id")
        # 本段代码核心功能：根据条件 `not isinstance(raw_provider_id, str)` 选择安全分支。
        # - 输入：条件表达式和此前已经规范化的局部变量。
        # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
        # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
        # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

        if not isinstance(raw_provider_id, str):
            continue
        provider_id = aliases.get(raw_provider_id, raw_provider_id)
        existing = merged.get(provider_id)
        # 本段代码核心功能：根据条件 `existing is None` 选择安全分支。
        # - 输入：条件表达式和此前已经规范化的局部变量。
        # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
        # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
        # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

        if existing is None:
            continue
        module_names = set(existing.detected_module_names)
        installed_names = set(existing.matched_installed_application_names)
        # 本段代码核心功能：逐项遍历有限配置条目、发现证据或测试样本。
        # - 输入：可迭代的配置、证据或样本序列。
        # - 处理：每轮只更新当前条目局部结果，最终按稳定顺序汇总。
        # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
        # - 为什么这样写：逐项处理保留来源级证据，避免聚合后无法追溯单个Provider。

        for field_name in (
            "current_interpreter_modules",
            "other_interpreter_modules",
        ):
            raw_values = raw.get(field_name, [])
            # 本段代码核心功能：根据条件 `isinstance(raw_values, list)` 选择安全分支。
            # - 输入：条件表达式和此前已经规范化的局部变量。
            # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
            # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
            # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
            # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

            if isinstance(raw_values, list):
                module_names.update(
                    value.strip()
                    for value in raw_values
                    if isinstance(value, str) and value.strip()
                )
        raw_apps = raw.get("matched_installed_applications", [])
        # 本段代码核心功能：根据条件 `isinstance(raw_apps, list)` 选择安全分支。
        # - 输入：条件表达式和此前已经规范化的局部变量。
        # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
        # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
        # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

        if isinstance(raw_apps, list):
            installed_names.update(
                value.strip()
                for value in raw_apps
                if isinstance(value, str) and value.strip()
            )
        merged[provider_id] = ArtifactEvidence(
            provider_id=existing.provider_id,
            matched_artifact_names=existing.matched_artifact_names,
            matched_root_labels=existing.matched_root_labels,
            detected_module_names=tuple(sorted(module_names)),
            matched_installed_application_names=tuple(sorted(installed_names)),
        )
    return merged


# 本段代码核心功能：定义 `_default_authorization`，为未填写的券商创建全部未确认的安全证据。
# - 输入：provider_id。
# - 处理：所有布尔门禁设为False，版本字段保持空字符串。
# - 输出：AuthorizationEvidence实例。
# - 常量依据：未知状态不得推断为已授权或已隔离。
# - 为什么这样写：统一默认对象可以简化评估逻辑，并确保缺少用户确认时稳定阻断。
def _default_authorization(provider_id: str) -> AuthorizationEvidence:
    """Build a conservative default authorization object."""

    return AuthorizationEvidence(
        provider_id=provider_id,
        official_package_confirmed=False,
        user_authorization_confirmed=False,
        read_only_quote_entitlement_confirmed=False,
        execution_domain_present=False,
        execution_domain_isolated_confirmed=False,
        sdk_version="",
        client_version="",
        documentation_version="",
    )


# 本段代码核心功能：定义 `evaluate_broker_candidates`，按四道门禁评估并排序券商只读候选。
# - 输入：BrokerSdkRule序列、本地ArtifactEvidence映射和AuthorizationEvidence映射。
# - 处理：计算证据分数，生成明确阻断原因；交易域存在但未隔离时禁止进入适配任务。
# - 输出：按可用性、strategy_rank、分数和provider_id稳定排序的BrokerSdkFinding元组。
# - 常量依据：READY要求官方包确认、用户授权、只读行情权限、实际本地证据和交易域隔离同时满足。
# - 为什么这样写：评分只帮助排序，真正准入仍由不可替代的布尔门禁决定，避免高分绕过安全条件。
def evaluate_broker_candidates(
    rules: Sequence[BrokerSdkRule],
    artifact_evidence: Mapping[str, ArtifactEvidence],
    authorization_evidence: Mapping[str, AuthorizationEvidence],
) -> tuple[BrokerSdkFinding, ...]:
    """Evaluate read-only broker adapter eligibility."""

    findings: list[BrokerSdkFinding] = []
    # 本段代码核心功能：逐项遍历有限配置条目、发现证据或测试样本。
    # - 输入：可迭代的配置、证据或样本序列。
    # - 处理：每轮只更新当前条目局部结果，最终按稳定顺序汇总。
    # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
    # - 为什么这样写：逐项处理保留来源级证据，避免聚合后无法追溯单个Provider。

    for rule in rules:
        artifact = artifact_evidence.get(
            rule.provider_id,
            ArtifactEvidence(rule.provider_id, (), (), (), ()),
        )
        authorization = authorization_evidence.get(
            rule.provider_id,
            _default_authorization(rule.provider_id),
        )
        local_evidence_present = bool(
            artifact.matched_artifact_names
            or artifact.detected_module_names
            or artifact.matched_installed_application_names
        )
        blockers: list[str] = []
        # 本段代码核心功能：根据条件 `not local_evidence_present` 选择安全分支。
        # - 输入：条件表达式和此前已经规范化的局部变量。
        # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
        # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
        # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

        if not local_evidence_present:
            blockers.append("NO_LOCAL_OFFICIAL_SDK_OR_CLIENT_EVIDENCE")
        # 本段代码核心功能：根据条件 `not authorization.official_package_confirmed` 选择安全分支。
        # - 输入：条件表达式和此前已经规范化的局部变量。
        # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
        # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
        # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

        if not authorization.official_package_confirmed:
            blockers.append("OFFICIAL_PACKAGE_NOT_CONFIRMED")
        # 本段代码核心功能：根据条件 `not authorization.user_authorization_confirmed` 选择安全分支。
        # - 输入：条件表达式和此前已经规范化的局部变量。
        # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
        # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
        # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

        if not authorization.user_authorization_confirmed:
            blockers.append("USER_AUTHORIZATION_NOT_CONFIRMED")
        # 本段代码核心功能：根据条件 `not authorization.read_only_quote_entitlement_confirmed` 选择安全分支。
        # - 输入：条件表达式和此前已经规范化的局部变量。
        # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
        # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
        # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

        if not authorization.read_only_quote_entitlement_confirmed:
            blockers.append("READ_ONLY_QUOTE_ENTITLEMENT_NOT_CONFIRMED")
        # 本段代码核心功能：根据条件 `authorization.execution_domain_present and (not authorization.execution_domain_isolated_confirmed)` 选择安全分支。
        # - 输入：条件表达式和此前已经规范化的局部变量。
        # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
        # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
        # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

        if (
            authorization.execution_domain_present
            and not authorization.execution_domain_isolated_confirmed
        ):
            blockers.append("EXECUTION_DOMAIN_NOT_ISOLATED")

        eligible = not blockers
        # 本段代码核心功能：根据条件 `eligible` 选择安全分支。
        # - 输入：条件表达式和此前已经规范化的局部变量。
        # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
        # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
        # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

        if eligible:
            candidate_status = "READY_FOR_READ_ONLY_ADAPTER_TASK"
        # 本段代码核心功能：根据条件 `local_evidence_present` 选择安全分支。
        # - 输入：条件表达式和此前已经规范化的局部变量。
        # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
        # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
        # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

        elif local_evidence_present:
            candidate_status = "LOCAL_EVIDENCE_REQUIRES_MANUAL_CONFIRMATION"
        else:
            candidate_status = "NO_LOCAL_EVIDENCE"

        score = 0
        score += 30 if artifact.matched_artifact_names else 0
        score += 15 if artifact.detected_module_names else 0
        score += 10 if artifact.matched_installed_application_names else 0
        score += 15 if authorization.official_package_confirmed else 0
        score += 15 if authorization.user_authorization_confirmed else 0
        score += 15 if authorization.read_only_quote_entitlement_confirmed else 0
        score += 10 if authorization.documentation_version else 0
        # 本段代码核心功能：根据条件 `authorization.execution_domain_present` 选择安全分支。
        # - 输入：条件表达式和此前已经规范化的局部变量。
        # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
        # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
        # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

        if authorization.execution_domain_present:
            score -= 10
        # 本段代码核心功能：根据条件 `authorization.execution_domain_isolated_confirmed` 选择安全分支。
        # - 输入：条件表达式和此前已经规范化的局部变量。
        # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
        # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
        # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

        if authorization.execution_domain_isolated_confirmed:
            score += 10

        findings.append(
            BrokerSdkFinding(
                provider_id=rule.provider_id,
                display_name=rule.display_name,
                catalog_source_id=rule.catalog_source_id,
                strategy_rank=rule.strategy_rank,
                evidence_score=max(score, 0),
                official_evidence_status=rule.official_evidence_status,
                matched_artifact_names=artifact.matched_artifact_names,
                matched_root_labels=artifact.matched_root_labels,
                detected_module_names=artifact.detected_module_names,
                matched_installed_application_names=(
                    artifact.matched_installed_application_names
                ),
                official_package_confirmed=(
                    authorization.official_package_confirmed
                ),
                user_authorization_confirmed=(
                    authorization.user_authorization_confirmed
                ),
                read_only_quote_entitlement_confirmed=(
                    authorization.read_only_quote_entitlement_confirmed
                ),
                execution_domain_present=authorization.execution_domain_present,
                execution_domain_isolated_confirmed=(
                    authorization.execution_domain_isolated_confirmed
                ),
                sdk_version=authorization.sdk_version,
                client_version=authorization.client_version,
                documentation_version=authorization.documentation_version,
                candidate_status=candidate_status,
                eligible_for_read_only_adapter_task=eligible,
                blockers=tuple(blockers),
            )
        )
    return tuple(
        sorted(
            findings,
            key=lambda item: (
                not item.eligible_for_read_only_adapter_task,
                item.strategy_rank,
                -item.evidence_score,
                item.provider_id,
            ),
        )
    )


# 本段代码核心功能：定义 `build_inventory_report`，生成稳定、可审计且不含秘密值的TASK_024B报告。
# - 输入：已排序finding、扫描文件数和输入来源是否存在的布尔事实。
# - 处理：根据READY候选和本地证据数量决定总体状态、选择状态和下一任务。
# - 输出：可直接写入JSON的字典。
# - 常量依据：没有READY候选时不得自动进入券商适配；交易、网络、SDK导入和秘密记录计数固定为零。
# - 为什么这样写：报告明确区分“工具运行成功”和“已找到可接入券商”，避免PASSED被误解为授权完成。
def build_inventory_report(
    findings: Sequence[BrokerSdkFinding],
    *,
    scanned_file_count: int,
    task_023b_report_used: bool,
    authorization_file_used: bool,
) -> dict[str, object]:
    """Build the TASK_024B JSON report."""

    ready = [
        finding
        for finding in findings
        if finding.eligible_for_read_only_adapter_task
    ]
    with_local_evidence = [
        finding
        for finding in findings
        if finding.matched_artifact_names
        or finding.detected_module_names
        or finding.matched_installed_application_names
    ]
    # 本段代码核心功能：根据条件 `ready` 选择安全分支。
    # - 输入：条件表达式和此前已经规范化的局部变量。
    # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
    # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
    # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

    if ready:
        overall_status = "PASSED_WITH_CANDIDATES"
        selection_status = "AUTHORIZED_READ_ONLY_CANDIDATES_FOUND"
        next_task = "TASK_024C_FIRST_AUTHORIZED_BROKER_READ_ONLY_ADAPTER"
    # 本段代码核心功能：根据条件 `with_local_evidence` 选择安全分支。
    # - 输入：条件表达式和此前已经规范化的局部变量。
    # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
    # - 输出：更新局部结果、阻断原因或测试断言，不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK合同，不把经验猜测写成官方规则。
    # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

    elif with_local_evidence:
        overall_status = "PASSED_WITH_WARNINGS"
        selection_status = "LOCAL_EVIDENCE_REQUIRES_MANUAL_CONFIRMATION"
        next_task = "TASK_024B_AUTHORIZATION_EVIDENCE_COMPLETION"
    else:
        overall_status = "PASSED_WITH_WARNINGS"
        selection_status = "NO_AUTHORIZED_BROKER_SDK_EVIDENCE"
        next_task = "TASK_024B_AUTHORIZED_SDK_EVIDENCE_INTAKE"

    return {
        "task_id": "TASK_024B",
        "mode": "AUTHORIZED_BROKER_SDK_READ_ONLY_INVENTORY",
        "overall_status": overall_status,
        "selection_status": selection_status,
        "next_task": next_task,
        "provider_count": len(findings),
        "ready_candidate_count": len(ready),
        "local_evidence_provider_count": len(with_local_evidence),
        "recommended_provider_ids": [item.provider_id for item in ready],
        "scanned_file_count": scanned_file_count,
        "task_023b_report_used": task_023b_report_used,
        "authorization_file_used": authorization_file_used,
        "findings": [asdict(item) for item in findings],
        "network_calls": 0,
        "vendor_sdk_imports": 0,
        "broker_logins": 0,
        "trade_session_initializations": 0,
        "order_submissions": 0,
        "database_write_operations": 0,
        "registry_write_operations": 0,
        "secret_values_recorded": 0,
        "absolute_paths_recorded": 0,
        "file_content_reads_for_sdk_artifacts": 0,
    }


# 本段代码核心功能：定义 `write_inventory_report`，以确定性UTF-8格式保存盘点结果。
# - 输入：报告映射和输出路径。
# - 处理：创建父目录，使用ensure_ascii=False、两空格缩进和单一末尾换行写入。
# - 输出：返回最终Path对象。
# - 常量依据：Windows PowerShell验证脚本将显式按UTF-8读取，避免系统ANSI编码污染中文。
# - 为什么这样写：稳定序列化便于Git外报告比较和人工审阅，也避免重复出现乱码JSON问题。
def write_inventory_report(
    report: Mapping[str, object],
    output_path: str | Path,
) -> Path:
    """Write a deterministic UTF-8 inventory report."""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return path
