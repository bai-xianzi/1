# 本文件核心功能：建立交易所、结算机构、券商与第三方来源的权威分层和接入门禁。
# - 输入：来自项目配置、离线本地环境、命令行参数或单元测试夹具；不读取未声明的秘密值。
# - 处理：先完成类型和值域校验，再执行离线发现、排序、报告生成或断言；默认不联网、不交易、不写数据库。
# - 输出：强类型对象、UTF-8 JSON报告、稳定退出码或可重复测试结果，供下一任务和Git门禁使用。
# - 常量依据：任务号、来源层级、安全计数器和状态值来自TASK_022至TASK_024权威文件与官方接口基线。
# - 为什么这样写：教学式前置说明让维护者先理解边界再阅读实现，也防止第三方聚合源或交易能力被误升为主链。

# 本模块核心功能：把官方交易所、结算机构、券商、商业SDK和第三方聚合源放入统一权威等级。
# - 语义权威：交易所、监管与结算基础设施优先。
# - 实际接入：用户已授权的券商官方SDK优先。
# - 第三方聚合：只能补充研究和交叉核验，不能成为Canonical事实源。
# - 未验证爬取：禁止进入核心数据链路。
"""TASK_024A官方交易所与券商优先的数据来源权威门禁。"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Mapping, Sequence


_ZERO_OPERATION_FIELDS = (
    "vendor_sdk_imports",
    "network_calls",
    "database_write_operations",
    "registry_write_operations",
    "secret_values_recorded",
    "provider_activation_operations",
    "execution_activation_operations",
)


# 本段代码核心功能：定义 `AuthorityTier`，定义来源权威层级的有限枚举，禁止任意字符串绕过门禁。
# - 输入：类实例字段由配置加载器、发现流程或测试夹具显式传入；不从全局状态隐式取值。
# - 处理：使用类型标注、不可变数据类或枚举限制字段形状和允许状态，避免原始字典在系统内扩散。
# - 输出：输出可比较、可序列化或可排序的 `AuthorityTier` 实例，供后续报告和门禁使用。
# - 常量依据：状态名和字段名来自TASK_022至TASK_024任务合同；本定义不新增未经验证的厂商能力。
# - 为什么这样写：先建立稳定合同，再接官方SDK或券商接口，能够降低供应商替换成本并阻止秘密值进入报告。

@dataclass(frozen=True)
class AuthorityTier:
    """来源等级及其语义权威、接入便利性和允许用途。"""

    tier_id: str
    semantic_authority_rank: int
    access_channel_rank: int
    primary_source_eligible: bool
    allowed_roles: tuple[str, ...]
    required_domain_classes: tuple[str, ...]


# 本段代码核心功能：定义 `SourceAuthorityPolicy`，保存来源、激活和安全门禁的不可变政策配置。
# - 输入：类实例字段由配置加载器、发现流程或测试夹具显式传入；不从全局状态隐式取值。
# - 处理：使用类型标注、不可变数据类或枚举限制字段形状和允许状态，避免原始字典在系统内扩散。
# - 输出：输出可比较、可序列化或可排序的 `SourceAuthorityPolicy` 实例，供后续报告和门禁使用。
# - 常量依据：状态名和字段名来自TASK_022至TASK_024任务合同；本定义不新增未经验证的厂商能力。
# - 为什么这样写：先建立稳定合同，再接官方SDK或券商接口，能够降低供应商替换成本并阻止秘密值进入报告。

@dataclass(frozen=True)
class SourceAuthorityPolicy:
    """TASK_024A的离线来源权威政策。"""

    semantic_authority_order: tuple[str, ...]
    practical_access_order: tuple[str, ...]
    rules: Mapping[str, bool]
    tiers: tuple[AuthorityTier, ...]


# 本段代码核心功能：定义 `OfficialInterfaceEntry`，保存经过强校验的配置条目，隔离原始JSON字典。
# - 输入：类实例字段由配置加载器、发现流程或测试夹具显式传入；不从全局状态隐式取值。
# - 处理：使用类型标注、不可变数据类或枚举限制字段形状和允许状态，避免原始字典在系统内扩散。
# - 输出：输出可比较、可序列化或可排序的 `OfficialInterfaceEntry` 实例，供后续报告和门禁使用。
# - 常量依据：状态名和字段名来自TASK_022至TASK_024任务合同；本定义不新增未经验证的厂商能力。
# - 为什么这样写：先建立稳定合同，再接官方SDK或券商接口，能够降低供应商替换成本并阻止秘密值进入报告。

@dataclass(frozen=True)
class OfficialInterfaceEntry:
    """一条经过来源分级的官方接口或补充来源目录记录。"""

    source_id: str
    display_name: str
    tier_id: str
    domain_class: str
    official_domains: tuple[str, ...]
    evidence_status: str
    interface_families: tuple[str, ...]
    semantic_baseline: bool
    direct_personal_access_expected: bool
    authorization_or_membership_required: bool
    execution_capability: bool
    read_only_scope_allowed_for_review: bool
    notes: str


# 本段代码核心功能：定义 `_string_tuple`，提供局部纯函数辅助，统一规范化、查找或匹配规则。
# - 输入：参数为 `value、field_name、allow_empty`；路径和外部文本按UTF-8处理，安全开关必须由显式配置提供。
# - 处理：只执行函数名对应的单一职责；遇到缺字段、非法状态或越界值立即失败，不做静默猜测。
# - 输出：返回类型为 `tuple[str, ...]`；测试函数则通过断言表达通过或失败，不产生生产副作用。
# - 常量依据：任务号、状态枚举、零网络/零交易计数和候选优先级均来自TASK_022至TASK_024权威任务合同。
# - 为什么这样写：显式输入输出和失败模式便于教学排查，也让未来官方交易所或券商SDK只需通过薄适配器接入。

def _string_tuple(value: object, field_name: str, *, allow_empty: bool = False) -> tuple[str, ...]:
    # 本段代码核心功能：根据条件 `not isinstance(value, list)` 选择安全分支。
    # - 输入：条件表达式及此前已经规范化的局部变量。
    # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
    # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
    # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a list")
    result: list[str] = []
    # 本段代码核心功能：逐项遍历 `value` 并处理 `item`。
    # - 输入：有限配置条目、发现证据或测试样本序列。
    # - 处理：每次循环只更新当前条目的局部结果，最终按稳定顺序汇总。
    # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
    # - 为什么这样写：逐项处理能保留来源级证据，避免聚合后无法追溯单个Provider。

    for item in value:
        # 本段代码核心功能：根据条件 `not isinstance(item, str) or not item.strip()` 选择安全分支。
        # - 输入：条件表达式及此前已经规范化的局部变量。
        # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
        # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
        # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"{field_name} must contain non-empty strings")
        result.append(item.strip())
    # 本段代码核心功能：根据条件 `not allow_empty and (not result)` 选择安全分支。
    # - 输入：条件表达式及此前已经规范化的局部变量。
    # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
    # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
    # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

    if not allow_empty and not result:
        raise ValueError(f"{field_name} must not be empty")
    # 本段代码核心功能：根据条件 `len(result) != len(set(result))` 选择安全分支。
    # - 输入：条件表达式及此前已经规范化的局部变量。
    # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
    # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
    # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

    if len(result) != len(set(result)):
        raise ValueError(f"{field_name} contains duplicates")
    return tuple(result)


# 本段代码核心功能：定义 `load_source_authority_policy`，读取UTF-8配置或报告，并在返回前完成字段、类型和值域校验。
# - 输入：参数为 `path`；路径和外部文本按UTF-8处理，安全开关必须由显式配置提供。
# - 处理：只执行函数名对应的单一职责；遇到缺字段、非法状态或越界值立即失败，不做静默猜测。
# - 输出：返回类型为 `SourceAuthorityPolicy`；测试函数则通过断言表达通过或失败，不产生生产副作用。
# - 常量依据：任务号、状态枚举、零网络/零交易计数和候选优先级均来自TASK_022至TASK_024权威任务合同。
# - 为什么这样写：显式输入输出和失败模式便于教学排查，也让未来官方交易所或券商SDK只需通过薄适配器接入。

def load_source_authority_policy(path: str | Path) -> SourceAuthorityPolicy:
    """读取政策，并拒绝任何运行、联网、秘密值或交易激活权限。"""

    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    # 本段代码核心功能：根据条件 `payload.get('task_id') != 'TASK_024A'` 选择安全分支。
    # - 输入：条件表达式及此前已经规范化的局部变量。
    # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
    # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
    # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

    if payload.get("task_id") != "TASK_024A":
        raise ValueError("task_id must be TASK_024A")
    # 本段代码核心功能：逐项遍历 `('network_calls_allowed', 'vendor_sdk_import_allowed', 'provider_activation_allo` 并处理 `field_name`。
    # - 输入：有限配置条目、发现证据或测试样本序列。
    # - 处理：每次循环只更新当前条目的局部结果，最终按稳定顺序汇总。
    # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
    # - 为什么这样写：逐项处理能保留来源级证据，避免聚合后无法追溯单个Provider。

    for field_name in (
        "network_calls_allowed",
        "vendor_sdk_import_allowed",
        "provider_activation_allowed",
        "secret_values_allowed",
        "execution_activation_allowed",
    ):
        # 本段代码核心功能：根据条件 `payload.get(field_name) is not False` 选择安全分支。
        # - 输入：条件表达式及此前已经规范化的局部变量。
        # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
        # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
        # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

        if payload.get(field_name) is not False:
            raise ValueError(f"{field_name} must be false")

    semantic_order = _string_tuple(
        payload.get("semantic_authority_order"), "semantic_authority_order"
    )
    access_order = _string_tuple(
        payload.get("practical_access_order"), "practical_access_order"
    )
    rules = payload.get("rules")
    # 本段代码核心功能：根据条件 `not isinstance(rules, dict) or not rules` 选择安全分支。
    # - 输入：条件表达式及此前已经规范化的局部变量。
    # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
    # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
    # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

    if not isinstance(rules, dict) or not rules:
        raise ValueError("rules must be a non-empty object")
    # 本段代码核心功能：根据条件 `any((value is not True for value in rules.values()))` 选择安全分支。
    # - 输入：条件表达式及此前已经规范化的局部变量。
    # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
    # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
    # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

    if any(value is not True for value in rules.values()):
        raise ValueError("all source-authority rules must be true")

    raw_tiers = payload.get("tiers")
    # 本段代码核心功能：根据条件 `not isinstance(raw_tiers, list) or not raw_tiers` 选择安全分支。
    # - 输入：条件表达式及此前已经规范化的局部变量。
    # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
    # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
    # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

    if not isinstance(raw_tiers, list) or not raw_tiers:
        raise ValueError("tiers must be a non-empty list")
    tiers: list[AuthorityTier] = []
    seen: set[str] = set()
    # 本段代码核心功能：逐项遍历 `raw_tiers` 并处理 `raw`。
    # - 输入：有限配置条目、发现证据或测试样本序列。
    # - 处理：每次循环只更新当前条目的局部结果，最终按稳定顺序汇总。
    # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
    # - 为什么这样写：逐项处理能保留来源级证据，避免聚合后无法追溯单个Provider。

    for raw in raw_tiers:
        # 本段代码核心功能：根据条件 `not isinstance(raw, dict)` 选择安全分支。
        # - 输入：条件表达式及此前已经规范化的局部变量。
        # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
        # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
        # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

        if not isinstance(raw, dict):
            raise ValueError("each tier must be an object")
        tier_id = str(raw.get("tier_id", "")).strip()
        # 本段代码核心功能：根据条件 `not tier_id or tier_id in seen` 选择安全分支。
        # - 输入：条件表达式及此前已经规范化的局部变量。
        # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
        # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
        # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

        if not tier_id or tier_id in seen:
            raise ValueError(f"invalid or duplicate tier_id: {tier_id}")
        seen.add(tier_id)
        semantic_rank = raw.get("semantic_authority_rank")
        access_rank = raw.get("access_channel_rank")
        # 本段代码核心功能：根据条件 `not isinstance(semantic_rank, int) or semantic_rank < 0` 选择安全分支。
        # - 输入：条件表达式及此前已经规范化的局部变量。
        # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
        # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
        # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

        if not isinstance(semantic_rank, int) or semantic_rank < 0:
            raise ValueError(f"invalid semantic_authority_rank: {tier_id}")
        # 本段代码核心功能：根据条件 `not isinstance(access_rank, int) or access_rank < 0` 选择安全分支。
        # - 输入：条件表达式及此前已经规范化的局部变量。
        # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
        # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
        # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

        if not isinstance(access_rank, int) or access_rank < 0:
            raise ValueError(f"invalid access_channel_rank: {tier_id}")
        tiers.append(
            AuthorityTier(
                tier_id=tier_id,
                semantic_authority_rank=semantic_rank,
                access_channel_rank=access_rank,
                primary_source_eligible=bool(raw.get("primary_source_eligible")),
                allowed_roles=_string_tuple(
                    raw.get("allowed_roles", []), "allowed_roles", allow_empty=True
                ),
                required_domain_classes=_string_tuple(
                    raw.get("required_domain_classes"), "required_domain_classes"
                ),
            )
        )

    # 本段代码核心功能：根据条件 `set(semantic_order) != seen` 选择安全分支。
    # - 输入：条件表达式及此前已经规范化的局部变量。
    # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
    # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
    # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

    if set(semantic_order) != seen:
        raise ValueError("semantic_authority_order must contain every tier exactly once")
    # 本段代码核心功能：根据条件 `set(access_order) != seen - {'T4_UNVERIFIED_SCRAPE_BLOCKED'}` 选择安全分支。
    # - 输入：条件表达式及此前已经规范化的局部变量。
    # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
    # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
    # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

    if set(access_order) != seen - {"T4_UNVERIFIED_SCRAPE_BLOCKED"}:
        raise ValueError("practical_access_order must contain every non-blocked tier")
    return SourceAuthorityPolicy(semantic_order, access_order, dict(rules), tuple(tiers))


# 本段代码核心功能：定义 `load_official_interface_catalog`，读取UTF-8配置或报告，并在返回前完成字段、类型和值域校验。
# - 输入：参数为 `path`；路径和外部文本按UTF-8处理，安全开关必须由显式配置提供。
# - 处理：只执行函数名对应的单一职责；遇到缺字段、非法状态或越界值立即失败，不做静默猜测。
# - 输出：返回类型为 `tuple[OfficialInterfaceEntry, ...]`；测试函数则通过断言表达通过或失败，不产生生产副作用。
# - 常量依据：任务号、状态枚举、零网络/零交易计数和候选优先级均来自TASK_022至TASK_024权威任务合同。
# - 为什么这样写：显式输入输出和失败模式便于教学排查，也让未来官方交易所或券商SDK只需通过薄适配器接入。

def load_official_interface_catalog(path: str | Path) -> tuple[OfficialInterfaceEntry, ...]:
    """读取官方接口目录；目录本身只来自人工核验后的静态配置。"""

    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    # 本段代码核心功能：根据条件 `payload.get('task_id') != 'TASK_024A'` 选择安全分支。
    # - 输入：条件表达式及此前已经规范化的局部变量。
    # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
    # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
    # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

    if payload.get("task_id") != "TASK_024A":
        raise ValueError("catalog task_id must be TASK_024A")
    raw_entries = payload.get("entries")
    # 本段代码核心功能：根据条件 `not isinstance(raw_entries, list) or not raw_entries` 选择安全分支。
    # - 输入：条件表达式及此前已经规范化的局部变量。
    # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
    # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
    # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

    if not isinstance(raw_entries, list) or not raw_entries:
        raise ValueError("entries must be a non-empty list")

    entries: list[OfficialInterfaceEntry] = []
    seen: set[str] = set()
    # 本段代码核心功能：逐项遍历 `raw_entries` 并处理 `raw`。
    # - 输入：有限配置条目、发现证据或测试样本序列。
    # - 处理：每次循环只更新当前条目的局部结果，最终按稳定顺序汇总。
    # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
    # - 为什么这样写：逐项处理能保留来源级证据，避免聚合后无法追溯单个Provider。

    for raw in raw_entries:
        # 本段代码核心功能：根据条件 `not isinstance(raw, dict)` 选择安全分支。
        # - 输入：条件表达式及此前已经规范化的局部变量。
        # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
        # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
        # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

        if not isinstance(raw, dict):
            raise ValueError("each catalog entry must be an object")
        source_id = str(raw.get("source_id", "")).strip()
        # 本段代码核心功能：根据条件 `not source_id or source_id in seen` 选择安全分支。
        # - 输入：条件表达式及此前已经规范化的局部变量。
        # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
        # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
        # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

        if not source_id or source_id in seen:
            raise ValueError(f"invalid or duplicate source_id: {source_id}")
        seen.add(source_id)
        entries.append(
            OfficialInterfaceEntry(
                source_id=source_id,
                display_name=str(raw.get("display_name", "")).strip(),
                tier_id=str(raw.get("tier_id", "")).strip(),
                domain_class=str(raw.get("domain_class", "")).strip(),
                official_domains=_string_tuple(
                    raw.get("official_domains"), "official_domains"
                ),
                evidence_status=str(raw.get("evidence_status", "")).strip(),
                interface_families=_string_tuple(
                    raw.get("interface_families"), "interface_families"
                ),
                semantic_baseline=bool(raw.get("semantic_baseline")),
                direct_personal_access_expected=bool(
                    raw.get("direct_personal_access_expected")
                ),
                authorization_or_membership_required=bool(
                    raw.get("authorization_or_membership_required")
                ),
                execution_capability=bool(raw.get("execution_capability")),
                read_only_scope_allowed_for_review=bool(
                    raw.get("read_only_scope_allowed_for_review")
                ),
                notes=str(raw.get("notes", "")).strip(),
            )
        )
    return tuple(entries)


# 本段代码核心功能：定义 `validate_source_authority_contract`，执行跨配置一致性检查，并把不安全组合转化为明确异常。
# - 输入：参数为 `policy、entries`；路径和外部文本按UTF-8处理，安全开关必须由显式配置提供。
# - 处理：只执行函数名对应的单一职责；遇到缺字段、非法状态或越界值立即失败，不做静默猜测。
# - 输出：返回类型为 `tuple[str, ...]`；测试函数则通过断言表达通过或失败，不产生生产副作用。
# - 常量依据：任务号、状态枚举、零网络/零交易计数和候选优先级均来自TASK_022至TASK_024权威任务合同。
# - 为什么这样写：显式输入输出和失败模式便于教学排查，也让未来官方交易所或券商SDK只需通过薄适配器接入。

def validate_source_authority_contract(
    policy: SourceAuthorityPolicy,
    entries: Sequence[OfficialInterfaceEntry],
) -> tuple[str, ...]:
    """验证大局观门禁：官方基准、券商优先、聚合源降级和爬虫阻断。"""

    tier_by_id = {tier.tier_id: tier for tier in policy.tiers}
    errors: list[str] = []
    required_sources = {"sse", "szse", "bse", "hkex_omdc", "chinaclear"}
    present_sources = {entry.source_id for entry in entries}
    missing = sorted(required_sources - present_sources)
    # 本段代码核心功能：根据条件 `missing` 选择安全分支。
    # - 输入：条件表达式及此前已经规范化的局部变量。
    # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
    # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
    # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

    if missing:
        errors.append("missing official market infrastructure: " + ",".join(missing))

    # 本段代码核心功能：逐项遍历 `entries` 并处理 `entry`。
    # - 输入：有限配置条目、发现证据或测试样本序列。
    # - 处理：每次循环只更新当前条目的局部结果，最终按稳定顺序汇总。
    # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
    # - 为什么这样写：逐项处理能保留来源级证据，避免聚合后无法追溯单个Provider。

    for entry in entries:
        tier = tier_by_id.get(entry.tier_id)
        # 本段代码核心功能：根据条件 `tier is None` 选择安全分支。
        # - 输入：条件表达式及此前已经规范化的局部变量。
        # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
        # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
        # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

        if tier is None:
            errors.append(f"unknown tier: {entry.source_id}:{entry.tier_id}")
            continue
        # 本段代码核心功能：根据条件 `entry.domain_class not in tier.required_domain_classes` 选择安全分支。
        # - 输入：条件表达式及此前已经规范化的局部变量。
        # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
        # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
        # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

        if entry.domain_class not in tier.required_domain_classes:
            errors.append(f"domain class does not match tier: {entry.source_id}")
        # 本段代码核心功能：根据条件 `not entry.display_name or not entry.evidence_status or (not entry.notes)` 选择安全分支。
        # - 输入：条件表达式及此前已经规范化的局部变量。
        # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
        # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
        # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

        if not entry.display_name or not entry.evidence_status or not entry.notes:
            errors.append(f"incomplete catalog entry: {entry.source_id}")

        # 本段代码核心功能：根据条件 `entry.tier_id == 'T0_OFFICIAL_MARKET_INFRASTRUCTURE'` 选择安全分支。
        # - 输入：条件表达式及此前已经规范化的局部变量。
        # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
        # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
        # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

        if entry.tier_id == "T0_OFFICIAL_MARKET_INFRASTRUCTURE":
            # 本段代码核心功能：根据条件 `not entry.semantic_baseline` 选择安全分支。
            # - 输入：条件表达式及此前已经规范化的局部变量。
            # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
            # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
            # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
            # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

            if not entry.semantic_baseline:
                errors.append(f"official infrastructure must be semantic baseline: {entry.source_id}")
            # 本段代码核心功能：根据条件 `not tier.primary_source_eligible` 选择安全分支。
            # - 输入：条件表达式及此前已经规范化的局部变量。
            # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
            # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
            # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
            # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

            if not tier.primary_source_eligible:
                errors.append("T0 must be primary-source eligible")

        # 本段代码核心功能：根据条件 `entry.tier_id == 'T1_AUTHORIZED_BROKER_OFFICIAL'` 选择安全分支。
        # - 输入：条件表达式及此前已经规范化的局部变量。
        # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
        # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
        # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

        if entry.tier_id == "T1_AUTHORIZED_BROKER_OFFICIAL":
            # 本段代码核心功能：根据条件 `not entry.authorization_or_membership_required` 选择安全分支。
            # - 输入：条件表达式及此前已经规范化的局部变量。
            # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
            # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
            # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
            # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

            if not entry.authorization_or_membership_required:
                errors.append(f"broker channel must require authorization: {entry.source_id}")
            # 本段代码核心功能：根据条件 `entry.execution_capability and (not entry.read_only_scope_allowed_for_review)` 选择安全分支。
            # - 输入：条件表达式及此前已经规范化的局部变量。
            # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
            # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
            # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
            # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

            if entry.execution_capability and not entry.read_only_scope_allowed_for_review:
                errors.append(f"broker must expose a separately reviewable read-only scope: {entry.source_id}")

        # 本段代码核心功能：根据条件 `entry.tier_id == 'T3_THIRD_PARTY_AGGREGATOR_SUPPLEMENTAL'` 选择安全分支。
        # - 输入：条件表达式及此前已经规范化的局部变量。
        # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
        # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
        # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

        if entry.tier_id == "T3_THIRD_PARTY_AGGREGATOR_SUPPLEMENTAL":
            # 本段代码核心功能：根据条件 `entry.semantic_baseline or tier.primary_source_eligible` 选择安全分支。
            # - 输入：条件表达式及此前已经规范化的局部变量。
            # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
            # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
            # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
            # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

            if entry.semantic_baseline or tier.primary_source_eligible:
                errors.append(f"third-party aggregator cannot be primary: {entry.source_id}")
            # 本段代码核心功能：根据条件 `entry.read_only_scope_allowed_for_review` 选择安全分支。
            # - 输入：条件表达式及此前已经规范化的局部变量。
            # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
            # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
            # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
            # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

            if entry.read_only_scope_allowed_for_review:
                errors.append(f"third-party aggregator cannot be first pilot: {entry.source_id}")

        # 本段代码核心功能：根据条件 `entry.tier_id == 'T4_UNVERIFIED_SCRAPE_BLOCKED'` 选择安全分支。
        # - 输入：条件表达式及此前已经规范化的局部变量。
        # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
        # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
        # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

        if entry.tier_id == "T4_UNVERIFIED_SCRAPE_BLOCKED":
            errors.append(f"blocked scrape endpoint must not enter the catalog: {entry.source_id}")

    # 本段代码核心功能：根据条件 `policy.semantic_authority_order[0] != 'T0_OFFICIAL_MARKET_INFRASTRUCTURE'` 选择安全分支。
    # - 输入：条件表达式及此前已经规范化的局部变量。
    # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
    # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
    # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

    if policy.semantic_authority_order[0] != "T0_OFFICIAL_MARKET_INFRASTRUCTURE":
        errors.append("official market infrastructure must be first semantic authority")
    # 本段代码核心功能：根据条件 `policy.practical_access_order[0] != 'T1_AUTHORIZED_BROKER_OFFICIAL'` 选择安全分支。
    # - 输入：条件表达式及此前已经规范化的局部变量。
    # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
    # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
    # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

    if policy.practical_access_order[0] != "T1_AUTHORIZED_BROKER_OFFICIAL":
        errors.append("authorized broker must be first practical access channel")
    return tuple(errors)


# 本段代码核心功能：定义 `rank_semantic_baselines`，依据显式优先级和稳定次级键排序候选，保证结果可重复。
# - 输入：参数为 `policy、entries`；路径和外部文本按UTF-8处理，安全开关必须由显式配置提供。
# - 处理：只执行函数名对应的单一职责；遇到缺字段、非法状态或越界值立即失败，不做静默猜测。
# - 输出：返回类型为 `tuple[OfficialInterfaceEntry, ...]`；测试函数则通过断言表达通过或失败，不产生生产副作用。
# - 常量依据：任务号、状态枚举、零网络/零交易计数和候选优先级均来自TASK_022至TASK_024权威任务合同。
# - 为什么这样写：显式输入输出和失败模式便于教学排查，也让未来官方交易所或券商SDK只需通过薄适配器接入。

def rank_semantic_baselines(
    policy: SourceAuthorityPolicy,
    entries: Sequence[OfficialInterfaceEntry],
) -> tuple[OfficialInterfaceEntry, ...]:
    """按语义权威排列可作为基准的来源。"""

    tier_by_id = {tier.tier_id: tier for tier in policy.tiers}
    return tuple(
        sorted(
            (entry for entry in entries if entry.semantic_baseline),
            key=lambda item: (
                tier_by_id[item.tier_id].semantic_authority_rank,
                item.source_id,
            ),
        )
    )


# 本段代码核心功能：定义 `rank_practical_access_candidates`，依据显式优先级和稳定次级键排序候选，保证结果可重复。
# - 输入：参数为 `policy、entries`；路径和外部文本按UTF-8处理，安全开关必须由显式配置提供。
# - 处理：只执行函数名对应的单一职责；遇到缺字段、非法状态或越界值立即失败，不做静默猜测。
# - 输出：返回类型为 `tuple[OfficialInterfaceEntry, ...]`；测试函数则通过断言表达通过或失败，不产生生产副作用。
# - 常量依据：任务号、状态枚举、零网络/零交易计数和候选优先级均来自TASK_022至TASK_024权威任务合同。
# - 为什么这样写：显式输入输出和失败模式便于教学排查，也让未来官方交易所或券商SDK只需通过薄适配器接入。

def rank_practical_access_candidates(
    policy: SourceAuthorityPolicy,
    entries: Sequence[OfficialInterfaceEntry],
) -> tuple[OfficialInterfaceEntry, ...]:
    """按个人项目可落地性排列官方接入渠道，不代表已经获得授权。"""

    tier_by_id = {tier.tier_id: tier for tier in policy.tiers}
    candidates = [
        entry
        for entry in entries
        if tier_by_id[entry.tier_id].primary_source_eligible
        and entry.direct_personal_access_expected
        and entry.read_only_scope_allowed_for_review
    ]
    return tuple(
        sorted(
            candidates,
            key=lambda item: (
                tier_by_id[item.tier_id].access_channel_rank,
                item.source_id,
            ),
        )
    )


# 本段代码核心功能：定义 `build_source_authority_report`，组合已经验证的中间证据，生成后续任务可消费的结构化结果。
# - 输入：参数为 `policy、entries`；路径和外部文本按UTF-8处理，安全开关必须由显式配置提供。
# - 处理：只执行函数名对应的单一职责；遇到缺字段、非法状态或越界值立即失败，不做静默猜测。
# - 输出：返回类型为 `dict[str, object]`；测试函数则通过断言表达通过或失败，不产生生产副作用。
# - 常量依据：任务号、状态枚举、零网络/零交易计数和候选优先级均来自TASK_022至TASK_024权威任务合同。
# - 为什么这样写：显式输入输出和失败模式便于教学排查，也让未来官方交易所或券商SDK只需通过薄适配器接入。

def build_source_authority_report(
    policy: SourceAuthorityPolicy,
    entries: Sequence[OfficialInterfaceEntry],
) -> dict[str, object]:
    """生成TASK_024A离线报告，不访问任何网站、SDK、账户或数据库。"""

    errors = validate_source_authority_contract(policy, entries)
    semantic = rank_semantic_baselines(policy, entries)
    access = rank_practical_access_candidates(policy, entries)
    return {
        "task_id": "TASK_024A",
        "mode": "OFFLINE_OFFICIAL_INTERFACE_BASELINE",
        "overall_status": "PASSED" if not errors else "BLOCKED",
        "policy_status": "OFFICIAL_EXCHANGE_AND_BROKER_FIRST",
        "semantic_baseline_source_ids": [entry.source_id for entry in semantic],
        "practical_access_candidate_ids": [entry.source_id for entry in access],
        "third_party_primary_source_forbidden": True,
        "unverified_scraping_core_pipeline_forbidden": True,
        "execution_activation_allowed": False,
        "validation_errors": list(errors),
        "catalog_entry_count": len(entries),
        "next_task_id": "TASK_024B",
        "next_task": "USER_AUTHORIZED_BROKER_SDK_PACKAGE_AND_READ_ONLY_CAPABILITY_INVENTORY",
        **{field: 0 for field in _ZERO_OPERATION_FIELDS},
    }


# 本段代码核心功能：定义 `write_source_authority_report`，把内存中的结构化结果以UTF-8和稳定换行写入目标文件。
# - 输入：参数为 `report、path`；路径和外部文本按UTF-8处理，安全开关必须由显式配置提供。
# - 处理：只执行函数名对应的单一职责；遇到缺字段、非法状态或越界值立即失败，不做静默猜测。
# - 输出：返回类型为 `Path`；测试函数则通过断言表达通过或失败，不产生生产副作用。
# - 常量依据：任务号、状态枚举、零网络/零交易计数和候选优先级均来自TASK_022至TASK_024权威任务合同。
# - 为什么这样写：显式输入输出和失败模式便于教学排查，也让未来官方交易所或券商SDK只需通过薄适配器接入。

def write_source_authority_report(report: Mapping[str, object], path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return output_path


# 本段代码核心功能：定义 `catalog_as_dicts`，完成catalog_as_dicts对应的单一业务步骤并返回明确结果。
# - 输入：参数为 `entries`；路径和外部文本按UTF-8处理，安全开关必须由显式配置提供。
# - 处理：只执行函数名对应的单一职责；遇到缺字段、非法状态或越界值立即失败，不做静默猜测。
# - 输出：返回类型为 `list[dict[str, object]]`；测试函数则通过断言表达通过或失败，不产生生产副作用。
# - 常量依据：任务号、状态枚举、零网络/零交易计数和候选优先级均来自TASK_022至TASK_024权威任务合同。
# - 为什么这样写：显式输入输出和失败模式便于教学排查，也让未来官方交易所或券商SDK只需通过薄适配器接入。

def catalog_as_dicts(entries: Sequence[OfficialInterfaceEntry]) -> list[dict[str, object]]:
    """便于调试和报告的稳定序列化，不执行任何外部操作。"""

    return [asdict(entry) for entry in entries]
