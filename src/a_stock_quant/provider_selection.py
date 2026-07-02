# 本文件核心功能：依据来源权威、授权证据和安全门禁选择下一阶段Provider候选。
# - 输入：来自项目配置、离线本地环境、命令行参数或单元测试夹具；不读取未声明的秘密值。
# - 处理：先完成类型和值域校验，再执行离线发现、排序、报告生成或断言；默认不联网、不交易、不写数据库。
# - 输出：强类型对象、UTF-8 JSON报告、稳定退出码或可重复测试结果，供下一任务和Git门禁使用。
# - 常量依据：任务号、来源层级、安全计数器和状态值来自TASK_022至TASK_024权威文件与官方接口基线。
# - 为什么这样写：教学式前置说明让维护者先理解边界再阅读实现，也防止第三方聚合源或交易能力被误升为主链。

# 本模块核心功能：把TASK_023B机器级证据转换为官方来源优先的接入规划决策。
# - 语义基准：交易所、监管和结算机构官方资料。
# - 接入通道：用户已授权的券商官方SDK优先。
# - 第三方聚合：只允许补充研究和交叉核验，不能成为首个主Provider。
# - 输出仅为规划决策；不安装、不导入、不联网、不激活任何Provider。
"""TASK_023C外部Provider选择与官方来源优先规划决策。"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Mapping


_ZERO_SAFETY_FIELDS = (
    "vendor_sdk_imports",
    "network_calls",
    "database_write_operations",
    "registry_write_operations",
    "secret_values_recorded",
    "installation_paths_recorded",
)


# 本段代码核心功能：定义 `ProviderSelectionProfile`，保存经过强校验的配置条目，隔离原始JSON字典。
# - 输入：类实例字段由配置加载器、发现流程或测试夹具显式传入；不从全局状态隐式取值。
# - 处理：使用类型标注、不可变数据类或枚举限制字段形状和允许状态，避免原始字典在系统内扩散。
# - 输出：输出可比较、可序列化或可排序的 `ProviderSelectionProfile` 实例，供后续报告和门禁使用。
# - 常量依据：状态名和字段名来自TASK_022至TASK_024任务合同；本定义不新增未经验证的厂商能力。
# - 为什么这样写：先建立稳定合同，再接官方SDK或券商接口，能够降低供应商替换成本并阻止秘密值进入报告。

@dataclass(frozen=True)
class ProviderSelectionProfile:
    """一个Provider的来源角色、授权边界和规划用途。"""

    provider_id: str
    strategy_rank: int
    pilot_eligible: bool
    local_evidence_required: bool
    manual_authorization_required: bool
    credential_required: bool
    code_license_status: str
    intended_use_scope: str
    reuse_path: str
    planned_capabilities: tuple[str, ...]
    required_gates_before_runtime: tuple[str, ...]
    known_risks: tuple[str, ...]
    source_role: str = "UNCLASSIFIED"
    primary_source_eligible: bool = False
    supplemental_only: bool = False


# 本段代码核心功能：定义 `ProviderSelectionPolicy`，保存来源、激活和安全门禁的不可变政策配置。
# - 输入：类实例字段由配置加载器、发现流程或测试夹具显式传入；不从全局状态隐式取值。
# - 处理：使用类型标注、不可变数据类或枚举限制字段形状和允许状态，避免原始字典在系统内扩散。
# - 输出：输出可比较、可序列化或可排序的 `ProviderSelectionPolicy` 实例，供后续报告和门禁使用。
# - 常量依据：状态名和字段名来自TASK_022至TASK_024任务合同；本定义不新增未经验证的厂商能力。
# - 为什么这样写：先建立稳定合同，再接官方SDK或券商接口，能够降低供应商替换成本并阻止秘密值进入报告。

@dataclass(frozen=True)
class ProviderSelectionPolicy:
    """TASK_023C选择政策；运行、秘密和交易权限必须保持关闭。"""

    default_provider_when_no_local_evidence: str
    profiles: tuple[ProviderSelectionProfile, ...]


# 本段代码核心功能：定义 `ProviderSelectionDecision`，保存Provider选择结果、阻断原因和下一任务状态。
# - 输入：类实例字段由配置加载器、发现流程或测试夹具显式传入；不从全局状态隐式取值。
# - 处理：使用类型标注、不可变数据类或枚举限制字段形状和允许状态，避免原始字典在系统内扩散。
# - 输出：输出可比较、可序列化或可排序的 `ProviderSelectionDecision` 实例，供后续报告和门禁使用。
# - 常量依据：状态名和字段名来自TASK_022至TASK_024任务合同；本定义不新增未经验证的厂商能力。
# - 为什么这样写：先建立稳定合同，再接官方SDK或券商接口，能够降低供应商替换成本并阻止秘密值进入报告。

@dataclass(frozen=True)
class ProviderSelectionDecision:
    """外部Provider规划级决策，不代表运行时激活。"""

    selected_provider_id: str
    decision_status: str
    selection_basis: str
    evidence_score: int
    strategy_rank: int
    source_role: str
    intended_use_scope: str
    reuse_path: str
    planned_capabilities: tuple[str, ...]
    required_gates_before_runtime: tuple[str, ...]
    known_risks: tuple[str, ...]
    activation_status: str
    next_task_id: str


# 本段代码核心功能：定义 `_string_tuple`，提供局部纯函数辅助，统一规范化、查找或匹配规则。
# - 输入：参数为 `value、field_name`；路径和外部文本按UTF-8处理，安全开关必须由显式配置提供。
# - 处理：只执行函数名对应的单一职责；遇到缺字段、非法状态或越界值立即失败，不做静默猜测。
# - 输出：返回类型为 `tuple[str, ...]`；测试函数则通过断言表达通过或失败，不产生生产副作用。
# - 常量依据：任务号、状态枚举、零网络/零交易计数和候选优先级均来自TASK_022至TASK_024权威任务合同。
# - 为什么这样写：显式输入输出和失败模式便于教学排查，也让未来官方交易所或券商SDK只需通过薄适配器接入。

def _string_tuple(value: object, field_name: str) -> tuple[str, ...]:
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
    # 本段代码核心功能：根据条件 `len(result) != len(set(result))` 选择安全分支。
    # - 输入：条件表达式及此前已经规范化的局部变量。
    # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
    # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
    # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

    if len(result) != len(set(result)):
        raise ValueError(f"{field_name} contains duplicate values")
    return tuple(result)


# 本段代码核心功能：定义 `load_provider_selection_policy`，读取UTF-8配置或报告，并在返回前完成字段、类型和值域校验。
# - 输入：参数为 `path`；路径和外部文本按UTF-8处理，安全开关必须由显式配置提供。
# - 处理：只执行函数名对应的单一职责；遇到缺字段、非法状态或越界值立即失败，不做静默猜测。
# - 输出：返回类型为 `ProviderSelectionPolicy`；测试函数则通过断言表达通过或失败，不产生生产副作用。
# - 常量依据：任务号、状态枚举、零网络/零交易计数和候选优先级均来自TASK_022至TASK_024权威任务合同。
# - 为什么这样写：显式输入输出和失败模式便于教学排查，也让未来官方交易所或券商SDK只需通过薄适配器接入。

def load_provider_selection_policy(path: str | Path) -> ProviderSelectionPolicy:
    """读取选择政策，并拒绝安装、联网、SDK导入、秘密值或交易权限。"""

    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    # 本段代码核心功能：根据条件 `payload.get('task_id') != 'TASK_023C'` 选择安全分支。
    # - 输入：条件表达式及此前已经规范化的局部变量。
    # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
    # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
    # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

    if payload.get("task_id") != "TASK_023C":
        raise ValueError("task_id must be TASK_023C")
    # 本段代码核心功能：逐项遍历 `('activation_allowed', 'network_calls_allowed', 'vendor_sdk_import_allowed', 'se` 并处理 `field_name`。
    # - 输入：有限配置条目、发现证据或测试样本序列。
    # - 处理：每次循环只更新当前条目的局部结果，最终按稳定顺序汇总。
    # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
    # - 为什么这样写：逐项处理能保留来源级证据，避免聚合后无法追溯单个Provider。

    for field_name in (
        "activation_allowed",
        "network_calls_allowed",
        "vendor_sdk_import_allowed",
        "secret_values_allowed",
        "execution_provider_selection_allowed",
    ):
        # 本段代码核心功能：根据条件 `payload.get(field_name) is not False` 选择安全分支。
        # - 输入：条件表达式及此前已经规范化的局部变量。
        # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
        # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
        # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

        if payload.get(field_name) is not False:
            raise ValueError(f"{field_name} must be false")

    default_provider = payload.get("default_provider_when_no_local_evidence")
    # 本段代码核心功能：根据条件 `not isinstance(default_provider, str) or not default_provider.strip()` 选择安全分支。
    # - 输入：条件表达式及此前已经规范化的局部变量。
    # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
    # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
    # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

    if not isinstance(default_provider, str) or not default_provider.strip():
        raise ValueError("default_provider_when_no_local_evidence must be a non-empty string")

    raw_profiles = payload.get("candidate_profiles")
    # 本段代码核心功能：根据条件 `not isinstance(raw_profiles, list) or not raw_profiles` 选择安全分支。
    # - 输入：条件表达式及此前已经规范化的局部变量。
    # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
    # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
    # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

    if not isinstance(raw_profiles, list) or not raw_profiles:
        raise ValueError("candidate_profiles must be a non-empty list")

    profiles: list[ProviderSelectionProfile] = []
    seen: set[str] = set()
    # 本段代码核心功能：逐项遍历 `raw_profiles` 并处理 `raw`。
    # - 输入：有限配置条目、发现证据或测试样本序列。
    # - 处理：每次循环只更新当前条目的局部结果，最终按稳定顺序汇总。
    # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
    # - 为什么这样写：逐项处理能保留来源级证据，避免聚合后无法追溯单个Provider。

    for raw in raw_profiles:
        # 本段代码核心功能：根据条件 `not isinstance(raw, dict)` 选择安全分支。
        # - 输入：条件表达式及此前已经规范化的局部变量。
        # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
        # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
        # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

        if not isinstance(raw, dict):
            raise ValueError("each candidate profile must be an object")
        provider_id = raw.get("provider_id")
        # 本段代码核心功能：根据条件 `not isinstance(provider_id, str) or not provider_id.strip()` 选择安全分支。
        # - 输入：条件表达式及此前已经规范化的局部变量。
        # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
        # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
        # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

        if not isinstance(provider_id, str) or not provider_id.strip():
            raise ValueError("provider_id must be a non-empty string")
        provider_id = provider_id.strip()
        # 本段代码核心功能：根据条件 `provider_id in seen` 选择安全分支。
        # - 输入：条件表达式及此前已经规范化的局部变量。
        # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
        # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
        # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

        if provider_id in seen:
            raise ValueError(f"duplicate provider_id: {provider_id}")
        seen.add(provider_id)
        strategy_rank = raw.get("strategy_rank")
        # 本段代码核心功能：根据条件 `not isinstance(strategy_rank, int) or strategy_rank < 0` 选择安全分支。
        # - 输入：条件表达式及此前已经规范化的局部变量。
        # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
        # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
        # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

        if not isinstance(strategy_rank, int) or strategy_rank < 0:
            raise ValueError(f"invalid strategy_rank: {provider_id}")
        profile = ProviderSelectionProfile(
            provider_id=provider_id,
            strategy_rank=strategy_rank,
            pilot_eligible=bool(raw.get("pilot_eligible", False)),
            local_evidence_required=bool(raw.get("local_evidence_required", False)),
            manual_authorization_required=bool(raw.get("manual_authorization_required", False)),
            credential_required=bool(raw.get("credential_required", False)),
            code_license_status=str(raw.get("code_license_status", "")).strip(),
            intended_use_scope=str(raw.get("intended_use_scope", "")).strip(),
            reuse_path=str(raw.get("reuse_path", "")).strip(),
            planned_capabilities=_string_tuple(raw.get("planned_capabilities", []), "planned_capabilities"),
            required_gates_before_runtime=_string_tuple(
                raw.get("required_gates_before_runtime", []),
                "required_gates_before_runtime",
            ),
            known_risks=_string_tuple(raw.get("known_risks", []), "known_risks"),
            source_role=str(raw.get("source_role", "UNCLASSIFIED")).strip(),
            primary_source_eligible=bool(raw.get("primary_source_eligible", False)),
            supplemental_only=bool(raw.get("supplemental_only", False)),
        )
        # 本段代码核心功能：根据条件 `profile.supplemental_only and profile.primary_source_eligible` 选择安全分支。
        # - 输入：条件表达式及此前已经规范化的局部变量。
        # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
        # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
        # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

        if profile.supplemental_only and profile.primary_source_eligible:
            raise ValueError(f"supplemental provider cannot be primary: {provider_id}")
        profiles.append(profile)

    # 本段代码核心功能：根据条件 `default_provider.strip() not in seen` 选择安全分支。
    # - 输入：条件表达式及此前已经规范化的局部变量。
    # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
    # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
    # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

    if default_provider.strip() not in seen:
        raise ValueError("default provider is not present in candidate_profiles")
    return ProviderSelectionPolicy(default_provider.strip(), tuple(profiles))


# 本段代码核心功能：定义 `load_task_023b_inventory_report`，读取UTF-8配置或报告，并在返回前完成字段、类型和值域校验。
# - 输入：参数为 `path`；路径和外部文本按UTF-8处理，安全开关必须由显式配置提供。
# - 处理：只执行函数名对应的单一职责；遇到缺字段、非法状态或越界值立即失败，不做静默猜测。
# - 输出：返回类型为 `dict[str, object]`；测试函数则通过断言表达通过或失败，不产生生产副作用。
# - 常量依据：任务号、状态枚举、零网络/零交易计数和候选优先级均来自TASK_022至TASK_024权威任务合同。
# - 为什么这样写：显式输入输出和失败模式便于教学排查，也让未来官方交易所或券商SDK只需通过薄适配器接入。

def load_task_023b_inventory_report(path: str | Path) -> dict[str, object]:
    """读取并验证TASK_023B报告的安全边界。"""

    report = json.loads(Path(path).read_text(encoding="utf-8"))
    # 本段代码核心功能：根据条件 `report.get('task_id') != 'TASK_023B'` 选择安全分支。
    # - 输入：条件表达式及此前已经规范化的局部变量。
    # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
    # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
    # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

    if report.get("task_id") != "TASK_023B":
        raise ValueError("inventory report task_id must be TASK_023B")
    # 本段代码核心功能：逐项遍历 `_ZERO_SAFETY_FIELDS` 并处理 `field_name`。
    # - 输入：有限配置条目、发现证据或测试样本序列。
    # - 处理：每次循环只更新当前条目的局部结果，最终按稳定顺序汇总。
    # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
    # - 为什么这样写：逐项处理能保留来源级证据，避免聚合后无法追溯单个Provider。

    for field_name in _ZERO_SAFETY_FIELDS:
        # 本段代码核心功能：根据条件 `int(report.get(field_name, -1)) != 0` 选择安全分支。
        # - 输入：条件表达式及此前已经规范化的局部变量。
        # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
        # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
        # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

        if int(report.get(field_name, -1)) != 0:
            raise ValueError(f"unsafe inventory report field: {field_name}")
    # 本段代码核心功能：根据条件 `bool(report.get('activation_performed'))` 选择安全分支。
    # - 输入：条件表达式及此前已经规范化的局部变量。
    # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
    # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
    # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

    if bool(report.get("activation_performed")):
        raise ValueError("inventory report must not activate a Provider")
    findings = report.get("findings")
    # 本段代码核心功能：根据条件 `not isinstance(findings, list)` 选择安全分支。
    # - 输入：条件表达式及此前已经规范化的局部变量。
    # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
    # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
    # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

    if not isinstance(findings, list):
        raise ValueError("inventory report findings must be a list")
    return report


# 本段代码核心功能：定义 `_finding_by_provider`，提供局部纯函数辅助，统一规范化、查找或匹配规则。
# - 输入：参数为 `report`；路径和外部文本按UTF-8处理，安全开关必须由显式配置提供。
# - 处理：只执行函数名对应的单一职责；遇到缺字段、非法状态或越界值立即失败，不做静默猜测。
# - 输出：返回类型为 `dict[str, Mapping[str, object]]`；测试函数则通过断言表达通过或失败，不产生生产副作用。
# - 常量依据：任务号、状态枚举、零网络/零交易计数和候选优先级均来自TASK_022至TASK_024权威任务合同。
# - 为什么这样写：显式输入输出和失败模式便于教学排查，也让未来官方交易所或券商SDK只需通过薄适配器接入。

def _finding_by_provider(report: Mapping[str, object]) -> dict[str, Mapping[str, object]]:
    findings = report.get("findings", [])
    result: dict[str, Mapping[str, object]] = {}
    # 本段代码核心功能：逐项遍历 `findings if isinstance(findings, list) else []` 并处理 `raw`。
    # - 输入：有限配置条目、发现证据或测试样本序列。
    # - 处理：每次循环只更新当前条目的局部结果，最终按稳定顺序汇总。
    # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
    # - 为什么这样写：逐项处理能保留来源级证据，避免聚合后无法追溯单个Provider。

    for raw in findings if isinstance(findings, list) else []:
        # 本段代码核心功能：根据条件 `not isinstance(raw, dict)` 选择安全分支。
        # - 输入：条件表达式及此前已经规范化的局部变量。
        # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
        # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
        # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

        if not isinstance(raw, dict):
            continue
        provider_id = raw.get("provider_id")
        # 本段代码核心功能：根据条件 `isinstance(provider_id, str) and provider_id` 选择安全分支。
        # - 输入：条件表达式及此前已经规范化的局部变量。
        # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
        # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
        # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

        if isinstance(provider_id, str) and provider_id:
            result[provider_id] = raw
    return result


# 本段代码核心功能：定义 `_primary_candidates`，提供局部纯函数辅助，统一规范化、查找或匹配规则。
# - 输入：参数为 `profiles`；路径和外部文本按UTF-8处理，安全开关必须由显式配置提供。
# - 处理：只执行函数名对应的单一职责；遇到缺字段、非法状态或越界值立即失败，不做静默猜测。
# - 输出：返回类型为 `tuple[ProviderSelectionProfile, ...]`；测试函数则通过断言表达通过或失败，不产生生产副作用。
# - 常量依据：任务号、状态枚举、零网络/零交易计数和候选优先级均来自TASK_022至TASK_024权威任务合同。
# - 为什么这样写：显式输入输出和失败模式便于教学排查，也让未来官方交易所或券商SDK只需通过薄适配器接入。

def _primary_candidates(
    profiles: Iterable[ProviderSelectionProfile],
) -> tuple[ProviderSelectionProfile, ...]:
    return tuple(
        profile
        for profile in profiles
        if profile.pilot_eligible
        and profile.primary_source_eligible
        and not profile.supplemental_only
        and profile.intended_use_scope != "SEPARATE_EXECUTION_DOMAIN"
    )


# 本段代码核心功能：定义 `select_first_external_provider`，按照来源权威和授权门禁选择候选，同时保持Provider未激活。
# - 输入：参数为 `policy、inventory_report`；路径和外部文本按UTF-8处理，安全开关必须由显式配置提供。
# - 处理：只执行函数名对应的单一职责；遇到缺字段、非法状态或越界值立即失败，不做静默猜测。
# - 输出：返回类型为 `ProviderSelectionDecision`；测试函数则通过断言表达通过或失败，不产生生产副作用。
# - 常量依据：任务号、状态枚举、零网络/零交易计数和候选优先级均来自TASK_022至TASK_024权威任务合同。
# - 为什么这样写：显式输入输出和失败模式便于教学排查，也让未来官方交易所或券商SDK只需通过薄适配器接入。

def select_first_external_provider(
    policy: ProviderSelectionPolicy,
    inventory_report: Mapping[str, object],
) -> ProviderSelectionDecision:
    """选择官方来源基线或已授权券商评审对象，不会激活任何运行时。"""

    findings = _finding_by_provider(inventory_report)
    profiles = _primary_candidates(policy.profiles)
    # 本段代码核心功能：根据条件 `not profiles` 选择安全分支。
    # - 输入：条件表达式及此前已经规范化的局部变量。
    # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
    # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
    # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

    if not profiles:
        raise ValueError("no primary-source-eligible non-execution profile exists")

    local_candidates: list[tuple[ProviderSelectionProfile, int]] = []
    # 本段代码核心功能：逐项遍历 `profiles` 并处理 `profile`。
    # - 输入：有限配置条目、发现证据或测试样本序列。
    # - 处理：每次循环只更新当前条目的局部结果，最终按稳定顺序汇总。
    # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
    # - 为什么这样写：逐项处理能保留来源级证据，避免聚合后无法追溯单个Provider。

    for profile in profiles:
        finding = findings.get(profile.provider_id, {})
        evidence_score = int(finding.get("evidence_score", 0) or 0)
        eligible_by_inventory = bool(finding.get("eligible_for_task_023c_review", False))
        # 本段代码核心功能：根据条件 `evidence_score > 0 and eligible_by_inventory` 选择安全分支。
        # - 输入：条件表达式及此前已经规范化的局部变量。
        # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
        # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
        # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

        if evidence_score > 0 and eligible_by_inventory:
            local_candidates.append((profile, evidence_score))

    broker_candidates = [
        item
        for item in local_candidates
        if item[0].source_role == "AUTHORIZED_BROKER_OFFICIAL_ACCESS"
    ]
    # 本段代码核心功能：根据条件 `broker_candidates` 选择安全分支。
    # - 输入：条件表达式及此前已经规范化的局部变量。
    # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
    # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
    # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

    if broker_candidates:
        broker_candidates.sort(
            key=lambda item: (item[0].strategy_rank, -item[1], item[0].provider_id)
        )
        selected, evidence_score = broker_candidates[0]
        basis = "LOCAL_OFFICIAL_BROKER_EVIDENCE_PENDING_AUTHORIZATION"
        decision_status = "SELECTED_FOR_OFFICIAL_BROKER_AUTHORIZATION_REVIEW"
    else:
        profile_by_id = {profile.provider_id: profile for profile in profiles}
        selected = profile_by_id.get(policy.default_provider_when_no_local_evidence)
        # 本段代码核心功能：根据条件 `selected is None` 选择安全分支。
        # - 输入：条件表达式及此前已经规范化的局部变量。
        # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
        # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
        # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

        if selected is None:
            raise ValueError("default provider is not primary-source eligible")
        evidence_score = int(findings.get(selected.provider_id, {}).get("evidence_score", 0) or 0)
        basis = "OFFICIAL_MARKET_INFRASTRUCTURE_SEMANTIC_BASELINE"
        decision_status = "OFFICIAL_BASELINE_SELECTED_ACCESS_CHANNEL_PENDING"

    gates = list(selected.required_gates_before_runtime)
    # 本段代码核心功能：根据条件 `selected.local_evidence_required and evidence_score <= 0` 选择安全分支。
    # - 输入：条件表达式及此前已经规范化的局部变量。
    # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
    # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
    # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

    if selected.local_evidence_required and evidence_score <= 0:
        gates.insert(0, "LOCAL_OFFICIAL_PACKAGE_OR_CLIENT_EVIDENCE_REQUIRED")
    # 本段代码核心功能：根据条件 `selected.manual_authorization_required` 选择安全分支。
    # - 输入：条件表达式及此前已经规范化的局部变量。
    # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
    # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
    # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

    if selected.manual_authorization_required:
        gates.insert(0, "MANUAL_AUTHORIZATION_APPROVAL_REQUIRED")
    # 本段代码核心功能：根据条件 `selected.credential_required` 选择安全分支。
    # - 输入：条件表达式及此前已经规范化的局部变量。
    # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
    # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
    # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

    if selected.credential_required:
        gates.insert(0, "CREDENTIAL_REFERENCE_REQUIRED_SECRET_VALUE_FORBIDDEN_IN_REPORT")

    return ProviderSelectionDecision(
        selected_provider_id=selected.provider_id,
        decision_status=decision_status,
        selection_basis=basis,
        evidence_score=evidence_score,
        strategy_rank=selected.strategy_rank,
        source_role=selected.source_role,
        intended_use_scope=selected.intended_use_scope,
        reuse_path=selected.reuse_path,
        planned_capabilities=selected.planned_capabilities,
        required_gates_before_runtime=tuple(dict.fromkeys(gates)),
        known_risks=selected.known_risks,
        activation_status="NOT_ACTIVATED",
        next_task_id="TASK_024A",
    )


# 本段代码核心功能：定义 `build_provider_selection_report`，组合已经验证的中间证据，生成后续任务可消费的结构化结果。
# - 输入：参数为 `decision、inventory_report`；路径和外部文本按UTF-8处理，安全开关必须由显式配置提供。
# - 处理：只执行函数名对应的单一职责；遇到缺字段、非法状态或越界值立即失败，不做静默猜测。
# - 输出：返回类型为 `dict[str, object]`；测试函数则通过断言表达通过或失败，不产生生产副作用。
# - 常量依据：任务号、状态枚举、零网络/零交易计数和候选优先级均来自TASK_022至TASK_024权威任务合同。
# - 为什么这样写：显式输入输出和失败模式便于教学排查，也让未来官方交易所或券商SDK只需通过薄适配器接入。

def build_provider_selection_report(
    decision: ProviderSelectionDecision,
    inventory_report: Mapping[str, object],
) -> dict[str, object]:
    """生成不含秘密值和机器路径的TASK_023C决策报告。"""

    return {
        "task_id": "TASK_023C",
        "mode": "OFFLINE_OFFICIAL_SOURCE_FIRST_PROVIDER_SELECTION",
        "overall_status": "PASSED_WITH_WARNINGS",
        "inventory_selection_status": inventory_report.get("selection_status", "UNKNOWN"),
        "inventory_provider_count": int(inventory_report.get("provider_count", 0) or 0),
        "decision": asdict(decision),
        "third_party_primary_source_forbidden": True,
        "vendor_sdk_imports": 0,
        "network_calls": 0,
        "database_write_operations": 0,
        "registry_write_operations": 0,
        "secret_values_recorded": 0,
        "installation_paths_recorded": 0,
        "provider_activation_operations": 0,
    }


# 本段代码核心功能：定义 `write_provider_selection_report`，把内存中的结构化结果以UTF-8和稳定换行写入目标文件。
# - 输入：参数为 `report、path`；路径和外部文本按UTF-8处理，安全开关必须由显式配置提供。
# - 处理：只执行函数名对应的单一职责；遇到缺字段、非法状态或越界值立即失败，不做静默猜测。
# - 输出：返回类型为 `Path`；测试函数则通过断言表达通过或失败，不产生生产副作用。
# - 常量依据：任务号、状态枚举、零网络/零交易计数和候选优先级均来自TASK_022至TASK_024权威任务合同。
# - 为什么这样写：显式输入输出和失败模式便于教学排查，也让未来官方交易所或券商SDK只需通过薄适配器接入。

def write_provider_selection_report(
    report: Mapping[str, object], path: str | Path
) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return output_path
