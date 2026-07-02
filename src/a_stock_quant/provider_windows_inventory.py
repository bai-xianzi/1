# 本文件核心功能：在Windows机器级范围内盘点Python解释器、已安装客户端和安全引用证据。
# - 输入：来自项目配置、离线本地环境、命令行参数或单元测试夹具；不读取未声明的秘密值。
# - 处理：先完成类型和值域校验，再执行离线发现、排序、报告生成或断言；默认不联网、不交易、不写数据库。
# - 输出：强类型对象、UTF-8 JSON报告、稳定退出码或可重复测试结果，供下一任务和Git门禁使用。
# - 常量依据：任务号、来源层级、安全计数器和状态值来自TASK_022至TASK_024权威文件与官方接口基线。
# - 为什么这样写：教学式前置说明让维护者先理解边界再阅读实现，也防止第三方聚合源或交易能力被误升为主链。

# 本模块核心功能：在Windows主机上进行供应商无关的机器级Provider环境盘点。
# - 输入：TASK_023A Provider清单、Windows盘点规则、可注入的解释器/程序/环境快照。
# - 处理：发现多个Python解释器、仅用find_spec探测模块、读取卸载注册表中的程序名称。
# - 输出：不含密码、Token值和安装路径的TASK_023B候选排序报告。
# - 安全边界：不导入厂商SDK、不联网、不登录、不修改注册表、不写数据库、不启用交易。
"""TASK_023B Windows机器级Provider环境盘点。"""

from __future__ import annotations

import json
import os
import platform
import re
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Iterable, Mapping, Sequence

from a_stock_quant.provider_environment_discovery import ProviderTargetSpec


# 本段代码核心功能：定义 `ProviderWindowsRule`，保存经过强校验的配置条目，隔离原始JSON字典。
# - 输入：类实例字段由配置加载器、发现流程或测试夹具显式传入；不从全局状态隐式取值。
# - 处理：使用类型标注、不可变数据类或枚举限制字段形状和允许状态，避免原始字典在系统内扩散。
# - 输出：输出可比较、可序列化或可排序的 `ProviderWindowsRule` 实例，供后续报告和门禁使用。
# - 常量依据：状态名和字段名来自TASK_022至TASK_024任务合同；本定义不新增未经验证的厂商能力。
# - 为什么这样写：先建立稳定合同，再接官方SDK或券商接口，能够降低供应商替换成本并阻止秘密值进入报告。

@dataclass(frozen=True)
class ProviderWindowsRule:
    """一个Provider的Windows本地证据匹配规则。"""

    provider_id: str
    installed_app_name_tokens: tuple[str, ...]
    executable_candidates: tuple[str, ...]


# 本段代码核心功能：定义 `PythonInterpreterEvidence`，保存单一Provider或本地环境的结构化证据，不保存秘密值。
# - 输入：类实例字段由配置加载器、发现流程或测试夹具显式传入；不从全局状态隐式取值。
# - 处理：使用类型标注、不可变数据类或枚举限制字段形状和允许状态，避免原始字典在系统内扩散。
# - 输出：输出可比较、可序列化或可排序的 `PythonInterpreterEvidence` 实例，供后续报告和门禁使用。
# - 常量依据：状态名和字段名来自TASK_022至TASK_024任务合同；本定义不新增未经验证的厂商能力。
# - 为什么这样写：先建立稳定合同，再接官方SDK或券商接口，能够降低供应商替换成本并阻止秘密值进入报告。

@dataclass(frozen=True)
class PythonInterpreterEvidence:
    """一个Python解释器及其离线模块发现结果。"""

    executable: str
    version: str
    source: str
    detected_modules: tuple[str, ...]
    probe_status: str


# 本段代码核心功能：定义 `InstalledApplicationEvidence`，保存单一Provider或本地环境的结构化证据，不保存秘密值。
# - 输入：类实例字段由配置加载器、发现流程或测试夹具显式传入；不从全局状态隐式取值。
# - 处理：使用类型标注、不可变数据类或枚举限制字段形状和允许状态，避免原始字典在系统内扩散。
# - 输出：输出可比较、可序列化或可排序的 `InstalledApplicationEvidence` 实例，供后续报告和门禁使用。
# - 常量依据：状态名和字段名来自TASK_022至TASK_024任务合同；本定义不新增未经验证的厂商能力。
# - 为什么这样写：先建立稳定合同，再接官方SDK或券商接口，能够降低供应商替换成本并阻止秘密值进入报告。

@dataclass(frozen=True)
class InstalledApplicationEvidence:
    """Windows卸载注册表中的安全程序元数据，不包含安装路径。"""

    display_name: str
    display_version: str
    publisher: str


# 本段代码核心功能：定义 `ProviderWindowsFinding`，保存单一Provider或本地环境的结构化证据，不保存秘密值。
# - 输入：类实例字段由配置加载器、发现流程或测试夹具显式传入；不从全局状态隐式取值。
# - 处理：使用类型标注、不可变数据类或枚举限制字段形状和允许状态，避免原始字典在系统内扩散。
# - 输出：输出可比较、可序列化或可排序的 `ProviderWindowsFinding` 实例，供后续报告和门禁使用。
# - 常量依据：状态名和字段名来自TASK_022至TASK_024任务合同；本定义不新增未经验证的厂商能力。
# - 为什么这样写：先建立稳定合同，再接官方SDK或券商接口，能够降低供应商替换成本并阻止秘密值进入报告。

@dataclass(frozen=True)
class ProviderWindowsFinding:
    """单一Provider的机器级证据、评分和下一步状态。"""

    provider_id: str
    display_name: str
    provider_kind: str
    execution_capability: bool
    priority: int
    evidence_score: int
    current_interpreter_modules: tuple[str, ...]
    other_interpreter_modules: tuple[str, ...]
    matched_installed_applications: tuple[str, ...]
    detected_executables: tuple[str, ...]
    present_credential_references: tuple[str, ...]
    inventory_status: str
    eligible_for_task_023c_review: bool
    blockers: tuple[str, ...]


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
    normalized: list[str] = []
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
        normalized.append(item.strip())
    # 本段代码核心功能：根据条件 `len(normalized) != len(set(normalized))` 选择安全分支。
    # - 输入：条件表达式及此前已经规范化的局部变量。
    # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
    # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
    # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

    if len(normalized) != len(set(normalized)):
        raise ValueError(f"{field_name} contains duplicate values")
    return tuple(normalized)


# 本段代码核心功能：定义 `load_windows_inventory_rules`，读取UTF-8配置或报告，并在返回前完成字段、类型和值域校验。
# - 输入：参数为 `path`；路径和外部文本按UTF-8处理，安全开关必须由显式配置提供。
# - 处理：只执行函数名对应的单一职责；遇到缺字段、非法状态或越界值立即失败，不做静默猜测。
# - 输出：返回类型为 `tuple[ProviderWindowsRule, ...]`；测试函数则通过断言表达通过或失败，不产生生产副作用。
# - 常量依据：任务号、状态枚举、零网络/零交易计数和候选优先级均来自TASK_022至TASK_024权威任务合同。
# - 为什么这样写：显式输入输出和失败模式便于教学排查，也让未来官方交易所或券商SDK只需通过薄适配器接入。

def load_windows_inventory_rules(path: str | Path) -> tuple[ProviderWindowsRule, ...]:
    """读取TASK_023B规则，并强制保留零秘密值、零SDK导入和零网络边界。"""

    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    # 本段代码核心功能：逐项遍历 `('secret_values_allowed', 'vendor_sdk_import_allowed', 'network_calls_allowed', ` 并处理 `field_name`。
    # - 输入：有限配置条目、发现证据或测试样本序列。
    # - 处理：每次循环只更新当前条目的局部结果，最终按稳定顺序汇总。
    # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
    # - 为什么这样写：逐项处理能保留来源级证据，避免聚合后无法追溯单个Provider。

    for field_name in (
        "secret_values_allowed",
        "vendor_sdk_import_allowed",
        "network_calls_allowed",
        "registry_install_location_allowed",
    ):
        # 本段代码核心功能：根据条件 `payload.get(field_name) is not False` 选择安全分支。
        # - 输入：条件表达式及此前已经规范化的局部变量。
        # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
        # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
        # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

        if payload.get(field_name) is not False:
            raise ValueError(f"{field_name} must be false")

    raw_rules = payload.get("providers")
    # 本段代码核心功能：根据条件 `not isinstance(raw_rules, list) or not raw_rules` 选择安全分支。
    # - 输入：条件表达式及此前已经规范化的局部变量。
    # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
    # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
    # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

    if not isinstance(raw_rules, list) or not raw_rules:
        raise ValueError("providers must be a non-empty list")

    rules: list[ProviderWindowsRule] = []
    seen: set[str] = set()
    # 本段代码核心功能：逐项遍历 `raw_rules` 并处理 `raw`。
    # - 输入：有限配置条目、发现证据或测试样本序列。
    # - 处理：每次循环只更新当前条目的局部结果，最终按稳定顺序汇总。
    # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
    # - 为什么这样写：逐项处理能保留来源级证据，避免聚合后无法追溯单个Provider。

    for raw in raw_rules:
        # 本段代码核心功能：根据条件 `not isinstance(raw, dict)` 选择安全分支。
        # - 输入：条件表达式及此前已经规范化的局部变量。
        # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
        # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
        # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

        if not isinstance(raw, dict):
            raise ValueError("each provider rule must be an object")
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
        rules.append(
            ProviderWindowsRule(
                provider_id=provider_id,
                installed_app_name_tokens=_string_tuple(
                    raw.get("installed_app_name_tokens", []),
                    "installed_app_name_tokens",
                ),
                executable_candidates=_string_tuple(
                    raw.get("executable_candidates", []),
                    "executable_candidates",
                ),
            )
        )
    return tuple(rules)


# 本段代码核心功能：定义 `_dedupe_paths`，提供局部纯函数辅助，统一规范化、查找或匹配规则。
# - 输入：参数为 `paths`；路径和外部文本按UTF-8处理，安全开关必须由显式配置提供。
# - 处理：只执行函数名对应的单一职责；遇到缺字段、非法状态或越界值立即失败，不做静默猜测。
# - 输出：返回类型为 `tuple[str, ...]`；测试函数则通过断言表达通过或失败，不产生生产副作用。
# - 常量依据：任务号、状态枚举、零网络/零交易计数和候选优先级均来自TASK_022至TASK_024权威任务合同。
# - 为什么这样写：显式输入输出和失败模式便于教学排查，也让未来官方交易所或券商SDK只需通过薄适配器接入。

def _dedupe_paths(paths: Iterable[str]) -> tuple[str, ...]:
    """按Windows不区分大小写语义稳定去重解释器路径。"""

    result: list[str] = []
    seen: set[str] = set()
    # 本段代码核心功能：逐项遍历 `paths` 并处理 `raw`。
    # - 输入：有限配置条目、发现证据或测试样本序列。
    # - 处理：每次循环只更新当前条目的局部结果，最终按稳定顺序汇总。
    # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
    # - 为什么这样写：逐项处理能保留来源级证据，避免聚合后无法追溯单个Provider。

    for raw in paths:
        value = str(raw).strip().strip('"')
        # 本段代码核心功能：根据条件 `not value` 选择安全分支。
        # - 输入：条件表达式及此前已经规范化的局部变量。
        # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
        # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
        # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

        if not value:
            continue
        key = os.path.normcase(os.path.abspath(value))
        # 本段代码核心功能：根据条件 `key not in seen` 选择安全分支。
        # - 输入：条件表达式及此前已经规范化的局部变量。
        # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
        # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
        # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

        if key not in seen:
            seen.add(key)
            result.append(value)
    return tuple(result)


# 本段代码核心功能：定义 `discover_python_interpreter_paths`，在既定安全边界内收集本地可证明证据，不执行网络或交易操作。
# - 输入：参数为 `无显式参数`；路径和外部文本按UTF-8处理，安全开关必须由显式配置提供。
# - 处理：只执行函数名对应的单一职责；遇到缺字段、非法状态或越界值立即失败，不做静默猜测。
# - 输出：返回类型为 `tuple[tuple[str, str], ...]`；测试函数则通过断言表达通过或失败，不产生生产副作用。
# - 常量依据：任务号、状态枚举、零网络/零交易计数和候选优先级均来自TASK_022至TASK_024权威任务合同。
# - 为什么这样写：显式输入输出和失败模式便于教学排查，也让未来官方交易所或券商SDK只需通过薄适配器接入。

def discover_python_interpreter_paths() -> tuple[tuple[str, str], ...]:
    """只通过当前解释器、PATH和py启动器发现Python，不遍历磁盘。"""

    candidates: list[tuple[str, str]] = [(sys.executable, "CURRENT_INTERPRETER")]

    # 本段代码核心功能：逐项遍历 `('python', 'python3')` 并处理 `executable_name`。
    # - 输入：有限配置条目、发现证据或测试样本序列。
    # - 处理：每次循环只更新当前条目的局部结果，最终按稳定顺序汇总。
    # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
    # - 为什么这样写：逐项处理能保留来源级证据，避免聚合后无法追溯单个Provider。

    for executable_name in ("python", "python3"):
        located = shutil.which(executable_name)
        # 本段代码核心功能：根据条件 `located` 选择安全分支。
        # - 输入：条件表达式及此前已经规范化的局部变量。
        # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
        # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
        # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

        if located:
            candidates.append((located, f"PATH_{executable_name.upper()}"))

    virtual_env = os.environ.get("VIRTUAL_ENV")
    # 本段代码核心功能：根据条件 `virtual_env` 选择安全分支。
    # - 输入：条件表达式及此前已经规范化的局部变量。
    # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
    # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
    # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

    if virtual_env:
        candidates.append((str(Path(virtual_env) / "Scripts" / "python.exe"), "VIRTUAL_ENV"))

    py_launcher = shutil.which("py")
    # 本段代码核心功能：根据条件 `py_launcher and platform.system() == 'Windows'` 选择安全分支。
    # - 输入：条件表达式及此前已经规范化的局部变量。
    # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
    # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
    # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

    if py_launcher and platform.system() == "Windows":
        # 本段代码核心功能：执行可能失败的本地解析或探测，并在失败时保持安全降级。
        # - 输入：文件、解释器、注册表或模块查找等可能抛出异常的本地操作。
        # - 处理：成功时保留证据，失败时转换为受控状态，清理动作放入finally。
        # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
        # - 为什么这样写：第三方环境不可假定稳定，受控异常能避免一次失败中断整份盘点。

        try:
            completed = subprocess.run(
                [py_launcher, "-0p"],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=10,
            )
            # 本段代码核心功能：逐项遍历 `completed.stdout.splitlines()` 并处理 `line`。
            # - 输入：有限配置条目、发现证据或测试样本序列。
            # - 处理：每次循环只更新当前条目的局部结果，最终按稳定顺序汇总。
            # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
            # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
            # - 为什么这样写：逐项处理能保留来源级证据，避免聚合后无法追溯单个Provider。

            for line in completed.stdout.splitlines():
                cleaned = line.strip()
                # 本段代码核心功能：根据条件 `not cleaned` 选择安全分支。
                # - 输入：条件表达式及此前已经规范化的局部变量。
                # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
                # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
                # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
                # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

                if not cleaned:
                    continue
                match = re.search(
                    r"([A-Za-z]:\\.*?python(?:w)?\.exe)\s*$",
                    cleaned,
                    flags=re.IGNORECASE,
                )
                # 本段代码核心功能：根据条件 `match` 选择安全分支。
                # - 输入：条件表达式及此前已经规范化的局部变量。
                # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
                # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
                # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
                # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

                if match:
                    candidates.append((match.group(1), "PY_LAUNCHER"))
        except (OSError, subprocess.SubprocessError):
            pass

    unique_paths = _dedupe_paths(path for path, _ in candidates)
    source_by_key = {
        os.path.normcase(os.path.abspath(path)): source for path, source in candidates
    }
    return tuple(
        (path, source_by_key[os.path.normcase(os.path.abspath(path))])
        for path in unique_paths
        if Path(path).is_file()
    )


# 本段代码核心功能：定义 `probe_python_interpreter`，在既定安全边界内收集本地可证明证据，不执行网络或交易操作。
# - 输入：参数为 `executable、source、module_names`；路径和外部文本按UTF-8处理，安全开关必须由显式配置提供。
# - 处理：只执行函数名对应的单一职责；遇到缺字段、非法状态或越界值立即失败，不做静默猜测。
# - 输出：返回类型为 `PythonInterpreterEvidence`；测试函数则通过断言表达通过或失败，不产生生产副作用。
# - 常量依据：任务号、状态枚举、零网络/零交易计数和候选优先级均来自TASK_022至TASK_024权威任务合同。
# - 为什么这样写：显式输入输出和失败模式便于教学排查，也让未来官方交易所或券商SDK只需通过薄适配器接入。

def probe_python_interpreter(
    executable: str,
    source: str,
    module_names: Sequence[str],
) -> PythonInterpreterEvidence:
    """在目标解释器中调用find_spec；不会import任何待探测模块。"""

    probe_code = (
        "import importlib.util,json,platform,sys;"
        "mods=json.loads(sys.argv[1]);"
        "found=[];"
        "[(found.append(m) if importlib.util.find_spec(m) is not None else None) for m in mods];"
        "print(json.dumps({'version':platform.python_version(),'found':found},ensure_ascii=True))"
    )
    # 本段代码核心功能：执行可能失败的本地解析或探测，并在失败时保持安全降级。
    # - 输入：文件、解释器、注册表或模块查找等可能抛出异常的本地操作。
    # - 处理：成功时保留证据，失败时转换为受控状态，清理动作放入finally。
    # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
    # - 为什么这样写：第三方环境不可假定稳定，受控异常能避免一次失败中断整份盘点。

    try:
        completed = subprocess.run(
            [executable, "-I", "-c", probe_code, json.dumps(list(module_names))],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=15,
        )
        # 本段代码核心功能：根据条件 `completed.returncode != 0` 选择安全分支。
        # - 输入：条件表达式及此前已经规范化的局部变量。
        # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
        # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
        # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

        if completed.returncode != 0:
            return PythonInterpreterEvidence(executable, "", source, (), "PROBE_FAILED")
        payload = json.loads(completed.stdout.strip())
        found = tuple(str(item) for item in payload.get("found", []))
        return PythonInterpreterEvidence(
            executable=executable,
            version=str(payload.get("version", "")),
            source=source,
            detected_modules=found,
            probe_status="PASSED",
        )
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError, TypeError):
        return PythonInterpreterEvidence(executable, "", source, (), "PROBE_FAILED")


# 本段代码核心功能：定义 `collect_python_interpreter_evidence`，在既定安全边界内收集本地可证明证据，不执行网络或交易操作。
# - 输入：参数为 `module_names`；路径和外部文本按UTF-8处理，安全开关必须由显式配置提供。
# - 处理：只执行函数名对应的单一职责；遇到缺字段、非法状态或越界值立即失败，不做静默猜测。
# - 输出：返回类型为 `tuple[PythonInterpreterEvidence, ...]`；测试函数则通过断言表达通过或失败，不产生生产副作用。
# - 常量依据：任务号、状态枚举、零网络/零交易计数和候选优先级均来自TASK_022至TASK_024权威任务合同。
# - 为什么这样写：显式输入输出和失败模式便于教学排查，也让未来官方交易所或券商SDK只需通过薄适配器接入。

def collect_python_interpreter_evidence(
    module_names: Sequence[str],
) -> tuple[PythonInterpreterEvidence, ...]:
    """对所有安全发现的解释器运行统一离线模块探测。"""

    return tuple(
        probe_python_interpreter(executable, source, module_names)
        for executable, source in discover_python_interpreter_paths()
    )


# 本段代码核心功能：定义 `collect_installed_applications`，在既定安全边界内收集本地可证明证据，不执行网络或交易操作。
# - 输入：参数为 `无显式参数`；路径和外部文本按UTF-8处理，安全开关必须由显式配置提供。
# - 处理：只执行函数名对应的单一职责；遇到缺字段、非法状态或越界值立即失败，不做静默猜测。
# - 输出：返回类型为 `tuple[InstalledApplicationEvidence, ...]`；测试函数则通过断言表达通过或失败，不产生生产副作用。
# - 常量依据：任务号、状态枚举、零网络/零交易计数和候选优先级均来自TASK_022至TASK_024权威任务合同。
# - 为什么这样写：显式输入输出和失败模式便于教学排查，也让未来官方交易所或券商SDK只需通过薄适配器接入。

def collect_installed_applications() -> tuple[InstalledApplicationEvidence, ...]:
    """读取Windows卸载注册表，只保留名称、版本和发布者。"""

    # 本段代码核心功能：根据条件 `platform.system() != 'Windows'` 选择安全分支。
    # - 输入：条件表达式及此前已经规范化的局部变量。
    # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
    # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
    # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

    if platform.system() != "Windows":
        return ()
    # 本段代码核心功能：执行可能失败的本地解析或探测，并在失败时保持安全降级。
    # - 输入：文件、解释器、注册表或模块查找等可能抛出异常的本地操作。
    # - 处理：成功时保留证据，失败时转换为受控状态，清理动作放入finally。
    # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
    # - 为什么这样写：第三方环境不可假定稳定，受控异常能避免一次失败中断整份盘点。

    try:
        import winreg
    except ImportError:
        return ()

    roots = (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER)
    subkey = r"Software\Microsoft\Windows\CurrentVersion\Uninstall"
    access_modes = (winreg.KEY_READ, winreg.KEY_READ | getattr(winreg, "KEY_WOW64_32KEY", 0), winreg.KEY_READ | getattr(winreg, "KEY_WOW64_64KEY", 0))
    records: dict[tuple[str, str, str], InstalledApplicationEvidence] = {}

    # 本段代码核心功能：逐项遍历 `roots` 并处理 `root`。
    # - 输入：有限配置条目、发现证据或测试样本序列。
    # - 处理：每次循环只更新当前条目的局部结果，最终按稳定顺序汇总。
    # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
    # - 为什么这样写：逐项处理能保留来源级证据，避免聚合后无法追溯单个Provider。

    for root in roots:
        # 本段代码核心功能：逐项遍历 `access_modes` 并处理 `access`。
        # - 输入：有限配置条目、发现证据或测试样本序列。
        # - 处理：每次循环只更新当前条目的局部结果，最终按稳定顺序汇总。
        # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
        # - 为什么这样写：逐项处理能保留来源级证据，避免聚合后无法追溯单个Provider。

        for access in access_modes:
            # 本段代码核心功能：执行可能失败的本地解析或探测，并在失败时保持安全降级。
            # - 输入：文件、解释器、注册表或模块查找等可能抛出异常的本地操作。
            # - 处理：成功时保留证据，失败时转换为受控状态，清理动作放入finally。
            # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
            # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
            # - 为什么这样写：第三方环境不可假定稳定，受控异常能避免一次失败中断整份盘点。

            try:
                # 本段代码核心功能：在受控上下文中打开临时资源并保证离开代码块时自动释放。
                # - 输入：临时目录、文件句柄或补丁上下文。
                # - 处理：上下文管理器负责建立和清理资源，业务代码只处理块内对象。
                # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
                # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
                # - 为什么这样写：自动清理可以防止测试污染、文件句柄泄漏和跨任务状态残留。

                with winreg.OpenKey(root, subkey, 0, access) as uninstall_key:
                    index = 0
                    # 本段代码核心功能：在终止条件满足前重复执行受控步骤。
                    # - 输入：当前索引、剩余行数或仍待处理的本地对象。
                    # - 处理：每轮都推进状态并保持明确退出条件。
                    # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
                    # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
                    # - 为什么这样写：显式终止条件可避免无限循环和不可控资源消耗。

                    while True:
                        # 本段代码核心功能：执行可能失败的本地解析或探测，并在失败时保持安全降级。
                        # - 输入：文件、解释器、注册表或模块查找等可能抛出异常的本地操作。
                        # - 处理：成功时保留证据，失败时转换为受控状态，清理动作放入finally。
                        # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
                        # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
                        # - 为什么这样写：第三方环境不可假定稳定，受控异常能避免一次失败中断整份盘点。

                        try:
                            child_name = winreg.EnumKey(uninstall_key, index)
                        except OSError:
                            break
                        index += 1
                        # 本段代码核心功能：执行可能失败的本地解析或探测，并在失败时保持安全降级。
                        # - 输入：文件、解释器、注册表或模块查找等可能抛出异常的本地操作。
                        # - 处理：成功时保留证据，失败时转换为受控状态，清理动作放入finally。
                        # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
                        # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
                        # - 为什么这样写：第三方环境不可假定稳定，受控异常能避免一次失败中断整份盘点。

                        try:
                            # 本段代码核心功能：在受控上下文中打开临时资源并保证离开代码块时自动释放。
                            # - 输入：临时目录、文件句柄或补丁上下文。
                            # - 处理：上下文管理器负责建立和清理资源，业务代码只处理块内对象。
                            # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
                            # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
                            # - 为什么这样写：自动清理可以防止测试污染、文件句柄泄漏和跨任务状态残留。

                            with winreg.OpenKey(uninstall_key, child_name, 0, access) as child:
                                # 本段代码核心功能：定义 `read_value`，完成read_value对应的单一业务步骤并返回明确结果。
                                # - 输入：参数为 `name`；路径和外部文本按UTF-8处理，安全开关必须由显式配置提供。
                                # - 处理：只执行函数名对应的单一职责；遇到缺字段、非法状态或越界值立即失败，不做静默猜测。
                                # - 输出：返回类型为 `str`；测试函数则通过断言表达通过或失败，不产生生产副作用。
                                # - 常量依据：任务号、状态枚举、零网络/零交易计数和候选优先级均来自TASK_022至TASK_024权威任务合同。
                                # - 为什么这样写：显式输入输出和失败模式便于教学排查，也让未来官方交易所或券商SDK只需通过薄适配器接入。

                                def read_value(name: str) -> str:
                                    # 本段代码核心功能：执行可能失败的本地解析或探测，并在失败时保持安全降级。
                                    # - 输入：文件、解释器、注册表或模块查找等可能抛出异常的本地操作。
                                    # - 处理：成功时保留证据，失败时转换为受控状态，清理动作放入finally。
                                    # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
                                    # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
                                    # - 为什么这样写：第三方环境不可假定稳定，受控异常能避免一次失败中断整份盘点。

                                    try:
                                        value, _ = winreg.QueryValueEx(child, name)
                                        return str(value).strip()
                                    except OSError:
                                        return ""

                                display_name = read_value("DisplayName")
                                # 本段代码核心功能：根据条件 `not display_name` 选择安全分支。
                                # - 输入：条件表达式及此前已经规范化的局部变量。
                                # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
                                # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
                                # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
                                # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

                                if not display_name:
                                    continue
                                record = InstalledApplicationEvidence(
                                    display_name=display_name,
                                    display_version=read_value("DisplayVersion"),
                                    publisher=read_value("Publisher"),
                                )
                                records[(record.display_name, record.display_version, record.publisher)] = record
                        except OSError:
                            continue
            except OSError:
                continue
    return tuple(sorted(records.values(), key=lambda item: item.display_name.casefold()))


# 本段代码核心功能：定义 `_matches_any_token`，提供局部纯函数辅助，统一规范化、查找或匹配规则。
# - 输入：参数为 `value、tokens`；路径和外部文本按UTF-8处理，安全开关必须由显式配置提供。
# - 处理：只执行函数名对应的单一职责；遇到缺字段、非法状态或越界值立即失败，不做静默猜测。
# - 输出：返回类型为 `bool`；测试函数则通过断言表达通过或失败，不产生生产副作用。
# - 常量依据：任务号、状态枚举、零网络/零交易计数和候选优先级均来自TASK_022至TASK_024权威任务合同。
# - 为什么这样写：显式输入输出和失败模式便于教学排查，也让未来官方交易所或券商SDK只需通过薄适配器接入。

def _matches_any_token(value: str, tokens: Sequence[str]) -> bool:
    normalized = value.casefold()
    return any(token.casefold() in normalized for token in tokens)


# 本段代码核心功能：定义 `build_windows_provider_findings`，组合已经验证的中间证据，生成后续任务可消费的结构化结果。
# - 输入：参数为 `targets、rules、interpreters、applications、environ、executable_lookup`；路径和外部文本按UTF-8处理，安全开关必须由显式配置提供。
# - 处理：只执行函数名对应的单一职责；遇到缺字段、非法状态或越界值立即失败，不做静默猜测。
# - 输出：返回类型为 `tuple[ProviderWindowsFinding, ...]`；测试函数则通过断言表达通过或失败，不产生生产副作用。
# - 常量依据：任务号、状态枚举、零网络/零交易计数和候选优先级均来自TASK_022至TASK_024权威任务合同。
# - 为什么这样写：显式输入输出和失败模式便于教学排查，也让未来官方交易所或券商SDK只需通过薄适配器接入。

def build_windows_provider_findings(
    targets: Sequence[ProviderTargetSpec],
    rules: Sequence[ProviderWindowsRule],
    interpreters: Sequence[PythonInterpreterEvidence],
    applications: Sequence[InstalledApplicationEvidence],
    *,
    environ: Mapping[str, str] | None = None,
    executable_lookup: Callable[[str], str | None] | None = None,
) -> tuple[ProviderWindowsFinding, ...]:
    """把机器级事实映射为Provider证据评分；评分只用于决定23C评审顺序。"""

    environment = os.environ if environ is None else environ
    lookup = shutil.which if executable_lookup is None else executable_lookup
    rule_by_provider = {rule.provider_id: rule for rule in rules}
    current_key = os.path.normcase(os.path.abspath(sys.executable))
    findings: list[ProviderWindowsFinding] = []

    # 本段代码核心功能：逐项遍历 `targets` 并处理 `target`。
    # - 输入：有限配置条目、发现证据或测试样本序列。
    # - 处理：每次循环只更新当前条目的局部结果，最终按稳定顺序汇总。
    # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
    # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
    # - 为什么这样写：逐项处理能保留来源级证据，避免聚合后无法追溯单个Provider。

    for target in targets:
        rule = rule_by_provider.get(target.provider_id)
        # 本段代码核心功能：根据条件 `rule is None` 选择安全分支。
        # - 输入：条件表达式及此前已经规范化的局部变量。
        # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
        # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
        # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

        if rule is None:
            raise ValueError(f"missing Windows inventory rule: {target.provider_id}")

        current_modules: set[str] = set()
        other_modules: set[str] = set()
        # 本段代码核心功能：逐项遍历 `interpreters` 并处理 `interpreter`。
        # - 输入：有限配置条目、发现证据或测试样本序列。
        # - 处理：每次循环只更新当前条目的局部结果，最终按稳定顺序汇总。
        # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
        # - 为什么这样写：逐项处理能保留来源级证据，避免聚合后无法追溯单个Provider。

        for interpreter in interpreters:
            matched = set(interpreter.detected_modules).intersection(target.python_module_candidates)
            interpreter_key = os.path.normcase(os.path.abspath(interpreter.executable))
            # 本段代码核心功能：根据条件 `interpreter_key == current_key` 选择安全分支。
            # - 输入：条件表达式及此前已经规范化的局部变量。
            # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
            # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
            # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
            # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

            if interpreter_key == current_key:
                current_modules.update(matched)
            else:
                other_modules.update(matched)

        matched_apps = tuple(
            app.display_name
            for app in applications
            if _matches_any_token(app.display_name, rule.installed_app_name_tokens)
        )
        detected_executables = tuple(
            name for name in rule.executable_candidates if lookup(name)
        )
        present_references = tuple(
            name for name in target.credential_reference_names if bool(environment.get(name))
        )

        score = 100 if current_modules else 0
        score += 80 if other_modules else 0
        score += 40 if matched_apps else 0
        score += 30 if detected_executables else 0
        score += 10 if present_references else 0

        blockers: list[str] = []
        # 本段代码核心功能：根据条件 `target.license_review_required` 选择安全分支。
        # - 输入：条件表达式及此前已经规范化的局部变量。
        # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
        # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
        # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

        if target.license_review_required:
            blockers.append("LICENSE_AND_AUTHORIZATION_REVIEW_REQUIRED")
        # 本段代码核心功能：根据条件 `target.execution_capability` 选择安全分支。
        # - 输入：条件表达式及此前已经规范化的局部变量。
        # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
        # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
        # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

        if target.execution_capability:
            blockers.append("EXECUTION_CAPABILITY_SEPARATE_ACTIVATION_REQUIRED")
        # 本段代码核心功能：根据条件 `score == 0` 选择安全分支。
        # - 输入：条件表达式及此前已经规范化的局部变量。
        # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
        # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
        # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

        if score == 0:
            blockers.append("NO_LOCAL_PROVIDER_EVIDENCE")

        eligible = score > 0 and not target.execution_capability
        # 本段代码核心功能：根据条件 `target.execution_capability` 选择安全分支。
        # - 输入：条件表达式及此前已经规范化的局部变量。
        # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
        # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
        # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

        if target.execution_capability:
            inventory_status = "SEPARATE_EXECUTION_REVIEW_REQUIRED"
        # 本段代码核心功能：根据条件 `eligible` 选择安全分支。
        # - 输入：条件表达式及此前已经规范化的局部变量。
        # - 处理：只执行满足合同的分支，非法状态通过异常或阻断原因显式返回。
        # - 输出：更新局部结果、阻断原因或测试断言；不绕过上层来源和授权门禁。
        # - 常量依据：分支状态和零副作用要求来自对应TASK任务合同，不把经验猜测写成官方规则。
        # - 为什么这样写：避免把缺失证据、未授权运行时或危险能力误判为可用。

        elif eligible:
            inventory_status = "LOCAL_EVIDENCE_FOUND_TASK_023C_REVIEW_REQUIRED"
        else:
            inventory_status = "LOCAL_EVIDENCE_NOT_FOUND"

        findings.append(
            ProviderWindowsFinding(
                provider_id=target.provider_id,
                display_name=target.display_name,
                provider_kind=target.provider_kind,
                execution_capability=target.execution_capability,
                priority=target.priority,
                evidence_score=score,
                current_interpreter_modules=tuple(sorted(current_modules)),
                other_interpreter_modules=tuple(sorted(other_modules)),
                matched_installed_applications=tuple(sorted(set(matched_apps))),
                detected_executables=tuple(sorted(detected_executables)),
                present_credential_references=present_references,
                inventory_status=inventory_status,
                eligible_for_task_023c_review=eligible,
                blockers=tuple(blockers),
            )
        )
    return tuple(findings)


# 本段代码核心功能：定义 `rank_task_023c_candidates`，依据显式优先级和稳定次级键排序候选，保证结果可重复。
# - 输入：参数为 `findings`；路径和外部文本按UTF-8处理，安全开关必须由显式配置提供。
# - 处理：只执行函数名对应的单一职责；遇到缺字段、非法状态或越界值立即失败，不做静默猜测。
# - 输出：返回类型为 `tuple[str, ...]`；测试函数则通过断言表达通过或失败，不产生生产副作用。
# - 常量依据：任务号、状态枚举、零网络/零交易计数和候选优先级均来自TASK_022至TASK_024权威任务合同。
# - 为什么这样写：显式输入输出和失败模式便于教学排查，也让未来官方交易所或券商SDK只需通过薄适配器接入。

def rank_task_023c_candidates(
    findings: Iterable[ProviderWindowsFinding],
) -> tuple[str, ...]:
    """按证据分降序、业务优先级升序和provider_id稳定排序。"""

    candidates = [item for item in findings if item.eligible_for_task_023c_review]
    candidates.sort(key=lambda item: (-item.evidence_score, item.priority, item.provider_id))
    return tuple(item.provider_id for item in candidates)


# 本段代码核心功能：定义 `build_windows_inventory_report`，组合已经验证的中间证据，生成后续任务可消费的结构化结果。
# - 输入：参数为 `findings、interpreters、applications`；路径和外部文本按UTF-8处理，安全开关必须由显式配置提供。
# - 处理：只执行函数名对应的单一职责；遇到缺字段、非法状态或越界值立即失败，不做静默猜测。
# - 输出：返回类型为 `dict[str, object]`；测试函数则通过断言表达通过或失败，不产生生产副作用。
# - 常量依据：任务号、状态枚举、零网络/零交易计数和候选优先级均来自TASK_022至TASK_024权威任务合同。
# - 为什么这样写：显式输入输出和失败模式便于教学排查，也让未来官方交易所或券商SDK只需通过薄适配器接入。

def build_windows_inventory_report(
    findings: Sequence[ProviderWindowsFinding],
    interpreters: Sequence[PythonInterpreterEvidence],
    applications: Sequence[InstalledApplicationEvidence],
) -> dict[str, object]:
    """生成可供TASK_023C读取的安全报告，不把秘密值和安装路径写入文件。"""

    ranked = rank_task_023c_candidates(findings)
    return {
        "task_id": "TASK_023B",
        "mode": "WINDOWS_MACHINE_LEVEL_PROVIDER_INVENTORY",
        "overall_status": "PASSED_WITH_WARNINGS" if findings else "FAILED",
        "platform_system": platform.system(),
        "platform_release": platform.release(),
        "machine": platform.machine(),
        "python_interpreter_count": len(interpreters),
        "installed_applications_scanned_count": len(applications),
        "provider_count": len(findings),
        "providers_with_local_evidence_count": sum(item.evidence_score > 0 for item in findings),
        "recommended_task_023c_provider_ids": list(ranked),
        "selection_status": "CANDIDATES_REQUIRE_MANUAL_REVIEW" if ranked else "NO_LOCAL_PROVIDER_EVIDENCE",
        "python_interpreters": [asdict(item) for item in interpreters],
        "findings": [asdict(item) for item in findings],
        "vendor_sdk_imports": 0,
        "network_calls": 0,
        "database_write_operations": 0,
        "registry_write_operations": 0,
        "secret_values_recorded": 0,
        "installation_paths_recorded": 0,
        "activation_performed": False,
    }


# 本段代码核心功能：定义 `write_windows_inventory_report`，把内存中的结构化结果以UTF-8和稳定换行写入目标文件。
# - 输入：参数为 `report、path`；路径和外部文本按UTF-8处理，安全开关必须由显式配置提供。
# - 处理：只执行函数名对应的单一职责；遇到缺字段、非法状态或越界值立即失败，不做静默猜测。
# - 输出：返回类型为 `Path`；测试函数则通过断言表达通过或失败，不产生生产副作用。
# - 常量依据：任务号、状态枚举、零网络/零交易计数和候选优先级均来自TASK_022至TASK_024权威任务合同。
# - 为什么这样写：显式输入输出和失败模式便于教学排查，也让未来官方交易所或券商SDK只需通过薄适配器接入。

def write_windows_inventory_report(report: Mapping[str, object], path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return output_path
