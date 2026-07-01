# 模块总览：TASK_020C：现有DolphinDB Adapter的通用Provider插件薄桥接。
# - 输入输出：本模块通过强类型对象和纯函数交换数据，不在导入阶段执行隐式网络或数据库写入。
# - 数据变化：只有显式构造、校验、加载或方法调用才会产生新对象或更新受控状态。
# - 为什么这样写：先说明模块边界，读者可以在阅读实现前理解职责、风险和复用方式。
"""TASK_020C：现有DolphinDB Adapter的通用Provider插件薄桥接。

本模块只负责协议编排，不重新实现：
- DolphinDB连接；
- 只读脚本安全检查；
- 原始表读取；
- DolphinDB返回值标准化。

上述行为全部委托给DolphinDBDataSourceAdapter。
"""
# 依赖导入：加载标准库、类型工具和项目内合同，供下方数据结构与校验逻辑复用。
# - 标准库只提供解析、数学、时间、路径和类型能力；项目模块提供统一异常与上游合同。
# - 为什么这样写：集中导入让依赖边界清晰，并避免在函数内部重复加载同一模块。
from __future__ import annotations

import importlib.metadata
import importlib.util
import json
import os
import platform
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterator, Mapping

from .data_contracts import DataContractError
from .dolphindb_adapter import DolphinDBDataSourceAdapter
from .provider_capabilities import CapabilityImplementationStatus
from .provider_plugin_protocol import (
    AuthenticationReference,
    AuthenticationReferenceKind,
    BatchPolicy,
    DiscoveryOutcome,
    LicenseBoundary,
    LicenseDecision,
    PaginationMode,
    PaginationPolicy,
    PluginRegistrationStatus,
    PolicyEvidenceStatus,
    ProviderDiscoveryResult,
    ProviderHealthSnapshot,
    ProviderHealthStatus,
    ProviderQueryBatch,
    ProviderQueryRequest,
    ProviderRegistryEntry,
    ProviderSubscriptionRequest,
    RateLimitPolicy,
    RetryPolicy,
    SdkRuntimeDescriptor,
    SubscriptionMode,
    SubscriptionPolicy,
)


# 变量更新：计算并保存RuntimeProbe，右侧逻辑为`Callable[[], Mapping[str, Any]]`。
# - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
# - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
RuntimeProbe = Callable[[], Mapping[str, Any]]


# 执行_require_text逻辑，把输入参数转换为受合同约束的结果。
# - 参数value：类型Any；进入函数后按合同校验或参与计算。
# - 参数field_name：类型str；进入函数后按合同校验或参与计算。
# - 输出：返回类型str；调用方按该类型继续校验、路由或序列化。
# - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
# - 为什么这样写：统一拒绝空字符串，避免无效标识进入后续注册、路由或持久化流程。
def _require_text(value: Any, field_name: str) -> str:
    # 条件门禁：判断`not isinstance(value, str) or not value.strip()`，条件为真时进入受保护分支。
    # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
    # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
    if not isinstance(value, str) or not value.strip():
        # 错误阻断：抛出`DataContractError(f'{field_name}不能为空。')`并停止当前路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
        # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
        raise DataContractError(f"{field_name}不能为空。")
    # 结果返回：把`value.strip()`交给调用方。
    # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
    # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
    return value.strip()


# 执行_positive_int逻辑，把输入参数转换为受合同约束的结果。
# - 参数value：类型Any；进入函数后按合同校验或参与计算。
# - 参数field_name：类型str；进入函数后按合同校验或参与计算。
# - 输出：返回类型int；调用方按该类型继续校验、路由或序列化。
# - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
# - 为什么这样写：把布尔值排除在整数之外并限制为正数，防止批次、并发或页数出现零和负值。
def _positive_int(value: Any, field_name: str) -> int:
    # 条件门禁：判断`isinstance(value, bool) or not isinstance(value, int) or value < 1`，条件为真时进入受保护分支。
    # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
    # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        # 错误阻断：抛出`DataContractError(f'{field_name}必须是正整数。')`并停止当前路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
        # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
        raise DataContractError(f"{field_name}必须是正整数。")
    # 结果返回：把`value`交给调用方。
    # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
    # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
    return value


# 执行_normalise_records_with_legacy_adapter逻辑，把输入参数转换为受合同约束的结果。
# - 参数adapter：类型DolphinDBDataSourceAdapter；进入函数后按合同校验或参与计算。
# - 参数result：类型Any；进入函数后按合同校验或参与计算。
# - 输出：返回类型tuple[list[str], list[dict[str, Any]]]；调用方按该类型继续校验、路由或序列化。
# - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
def _normalise_records_with_legacy_adapter(
    adapter: DolphinDBDataSourceAdapter,
    result: Any,
) -> tuple[list[str], list[dict[str, Any]]]:
    # 变量更新：计算并保存normaliser，右侧逻辑为`getattr(adapter, '_normalise_records', None)`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    normaliser = getattr(adapter, "_normalise_records", None)
    # 条件门禁：判断`not callable(normaliser)`，条件为真时进入受保护分支。
    # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
    # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
    if not callable(normaliser):
        # 错误阻断：抛出`DataContractError('现有DolphinDB Adapter缺少结果标准化能力。')`并停止当前路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
        # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
        raise DataContractError(
            "现有DolphinDB Adapter缺少结果标准化能力。"
        )
    # 变量更新：计算并保存(fields, records)，右侧逻辑为`normaliser(result)`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    fields, records = normaliser(result)
    # 结果返回：把`(list(fields), [dict(item) for item in records])`交给调用方。
    # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
    # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
    return list(fields), [dict(item) for item in records]


# 定义DolphinDBProviderPluginBridgeConfig强类型合同，集中保存相关状态、参数和校验规则。
# - 字段task_id：类型str。
# - 字段bridge_version：类型str。
# - 字段bridge_status：类型str。
# - 字段provider_id：类型str。
# - 字段plugin_id：类型str。
# - 字段entrypoint：类型str。
# - 字段legacy_adapter_class：类型str。
# - 字段reuse_strategy：类型str。
# - 其余字段：另有19项，均在对象创建时统一校验。
# - 数据变化：类本身不执行隐式I/O，实例字段只在显式构造、校验或方法调用时变化。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
@dataclass(frozen=True, slots=True)
class DolphinDBProviderPluginBridgeConfig:
    # 变量更新：计算并保存task_id，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    task_id: str
    # 变量更新：计算并保存bridge_version，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    bridge_version: str
    # 变量更新：计算并保存bridge_status，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    bridge_status: str
    # 变量更新：计算并保存provider_id，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    provider_id: str
    # 变量更新：计算并保存plugin_id，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    plugin_id: str
    # 变量更新：计算并保存entrypoint，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    entrypoint: str
    # 变量更新：计算并保存legacy_adapter_class，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    legacy_adapter_class: str
    # 变量更新：计算并保存reuse_strategy，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    reuse_strategy: str
    # 变量更新：计算并保存custom_query_engine_implemented，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    custom_query_engine_implemented: bool
    # 变量更新：计算并保存custom_session_engine_implemented，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    custom_session_engine_implemented: bool
    # 变量更新：计算并保存custom_dolphindb_protocol_implemented，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    custom_dolphindb_protocol_implemented: bool
    # 变量更新：计算并保存authentication_reference，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    authentication_reference: AuthenticationReference
    # 变量更新：计算并保存operating_systems，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    operating_systems: tuple[str, ...]
    # 变量更新：计算并保存architecture，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    architecture: str
    # 变量更新：计算并保存sdk_name，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    sdk_name: str
    # 变量更新：计算并保存installation_probe，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    installation_probe: str
    # 变量更新：计算并保存capabilities，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    capabilities: Mapping[
        str,
        CapabilityImplementationStatus,
    ]
    # 变量更新：计算并保存permitted_usages，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    permitted_usages: tuple[str, ...]
    # 变量更新：计算并保存rate_limit_policy，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    rate_limit_policy: RateLimitPolicy
    # 变量更新：计算并保存retry_policy，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    retry_policy: RetryPolicy
    # 变量更新：计算并保存batch_policy，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    batch_policy: BatchPolicy
    # 变量更新：计算并保存pagination_policy，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    pagination_policy: PaginationPolicy
    # 变量更新：计算并保存subscription_policy，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    subscription_policy: SubscriptionPolicy
    # 变量更新：计算并保存license_boundary，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    license_boundary: LicenseBoundary
    # 变量更新：计算并保存supported_operations，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    supported_operations: tuple[str, ...]
    # 变量更新：计算并保存activation_policy，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    activation_policy: Mapping[str, bool]
    # 变量更新：计算并保存hard_rules，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    hard_rules: tuple[str, ...]

    # 执行__post_init__逻辑，把输入参数转换为受合同约束的结果。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态或模块常量。
    # - 输出：返回类型None；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：在不可变或数据类对象创建后立即校验字段关系，阻止不一致对象进入系统。
    def __post_init__(self) -> None:
        # 迭代处理：依次读取`('task_id', 'bridge_version', 'bridge_status', 'provider_id', 'plugin_id', 'e...`中的元素，并绑定到`field_name`。
        # - 维度变化：每轮处理一个元素，可能向列表、字典或累计值中增加一项。
        # - 为什么这样写：显式逐项校验可以精确指出哪个字段或Provider不符合合同。
        for field_name in (
            "task_id",
            "bridge_version",
            "bridge_status",
            "provider_id",
            "plugin_id",
            "entrypoint",
            "legacy_adapter_class",
            "reuse_strategy",
            "architecture",
            "sdk_name",
            "installation_probe",
        ):
            # API调用：执行`object.__setattr__(self, field_name, _require_text(getattr(self, field_name), field_name))`以触发注册、写入对象状态或其他显式副作用。
            # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
            # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
            object.__setattr__(
                self,
                field_name,
                _require_text(getattr(self, field_name), field_name),
            )
        # 条件门禁：判断`self.task_id != 'TASK_020C'`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if self.task_id != "TASK_020C":
            # 错误阻断：抛出`DataContractError('桥接配置task_id异常。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError("桥接配置task_id异常。")
        # 条件门禁：判断`self.provider_id != 'local_dolphindb'`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if self.provider_id != "local_dolphindb":
            # 错误阻断：抛出`DataContractError('桥接配置provider_id异常。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError("桥接配置provider_id异常。")
        # 条件门禁：判断`self.reuse_strategy != 'WRAP_WITH_THIN_ADAPTER'`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if self.reuse_strategy != "WRAP_WITH_THIN_ADAPTER":
            # 错误阻断：抛出`DataContractError('DolphinDB必须使用薄桥接复用策略。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError("DolphinDB必须使用薄桥接复用策略。")
        # 条件门禁：判断`any((self.custom_query_engine_implemented, self.custom_session_engine_implemented, self.custom_do...`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if any(
            (
                self.custom_query_engine_implemented,
                self.custom_session_engine_implemented,
                self.custom_dolphindb_protocol_implemented,
            )
        ):
            # 错误阻断：抛出`DataContractError('桥接层不得重写DolphinDB核心能力。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError("桥接层不得重写DolphinDB核心能力。")
        # 条件门禁：判断`self.authentication_reference.kind is not AuthenticationReferenceKind.ENVIRONMENT_VARIABLE`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if (
            self.authentication_reference.kind
            is not AuthenticationReferenceKind.ENVIRONMENT_VARIABLE
        ):
            # 错误阻断：抛出`DataContractError('DolphinDB密码必须使用环境变量引用。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError("DolphinDB密码必须使用环境变量引用。")
        # 条件门禁：判断`not self.authentication_reference.locator.startswith('env://')`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if not self.authentication_reference.locator.startswith("env://"):
            # 错误阻断：抛出`DataContractError('DolphinDB认证引用必须使用env://。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError("DolphinDB认证引用必须使用env://。")
        # 变量更新：计算并保存operating_systems，右侧逻辑为`tuple((_require_text(value, 'operating_systems') for value in self.operating_systems))`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        operating_systems = tuple(
            _require_text(value, "operating_systems")
            for value in self.operating_systems
        )
        # 条件门禁：判断`not operating_systems`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if not operating_systems:
            # 错误阻断：抛出`DataContractError('operating_systems不能为空。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError("operating_systems不能为空。")
        # API调用：执行`object.__setattr__(self, 'operating_systems', operating_systems)`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        object.__setattr__(
            self,
            "operating_systems",
            operating_systems,
        )
        # 变量更新：计算并保存capabilities，右侧逻辑为`{_require_text(key, 'capability'): value if isinstance(value, CapabilityImplementationS...`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        capabilities = {
            _require_text(key, "capability"): (
                value
                if isinstance(value, CapabilityImplementationStatus)
                else CapabilityImplementationStatus(str(value))
            )
            for key, value in self.capabilities.items()
        }
        # 条件门禁：判断`'EOD_MARKET_DATA' not in capabilities`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if "EOD_MARKET_DATA" not in capabilities:
            # 错误阻断：抛出`DataContractError('桥接配置必须包含EOD_MARKET_DATA。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError("桥接配置必须包含EOD_MARKET_DATA。")
        # API调用：执行`object.__setattr__(self, 'capabilities', capabilities)`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        object.__setattr__(self, "capabilities", capabilities)
        # 变量更新：计算并保存usages，右侧逻辑为`tuple((_require_text(value, 'permitted_usages') for value in self.permitted_usages))`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        usages = tuple(
            _require_text(value, "permitted_usages")
            for value in self.permitted_usages
        )
        # 条件门禁：判断`not usages or len(usages) != len(set(usages))`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if not usages or len(usages) != len(set(usages)):
            # 错误阻断：抛出`DataContractError('permitted_usages必须非空且唯一。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError("permitted_usages必须非空且唯一。")
        # API调用：执行`object.__setattr__(self, 'permitted_usages', usages)`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        object.__setattr__(self, "permitted_usages", usages)
        # 变量更新：计算并保存operations，右侧逻辑为`tuple((_require_text(value, 'supported_operations') for value in self.supported_operati...`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        operations = tuple(
            _require_text(value, "supported_operations")
            for value in self.supported_operations
        )
        # 变量更新：计算并保存expected_operations，右侧逻辑为`{'READ_RAW_TABLE', 'RUN_READONLY_QUERY'}`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        expected_operations = {
            "READ_RAW_TABLE",
            "RUN_READONLY_QUERY",
        }
        # 条件门禁：判断`set(operations) != expected_operations`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if set(operations) != expected_operations:
            # 错误阻断：抛出`DataContractError('桥接支持操作集合异常。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError("桥接支持操作集合异常。")
        # API调用：执行`object.__setattr__(self, 'supported_operations', operations)`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        object.__setattr__(self, "supported_operations", operations)
        # 条件门禁：判断`self.pagination_policy.mode is not PaginationMode.NONE`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if self.pagination_policy.mode is not PaginationMode.NONE:
            # 错误阻断：抛出`DataContractError('当前薄桥接不得虚构分页能力。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError("当前薄桥接不得虚构分页能力。")
        # 条件门禁：判断`self.subscription_policy.mode is not SubscriptionMode.NONE`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if self.subscription_policy.mode is not SubscriptionMode.NONE:
            # 错误阻断：抛出`DataContractError('当前薄桥接不得虚构订阅能力。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError("当前薄桥接不得虚构订阅能力。")
        # 条件门禁：判断`self.batch_policy.maximum_rows_per_batch > 100000`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if self.batch_policy.maximum_rows_per_batch > 100000:
            # 错误阻断：抛出`DataContractError('桥接批次超过现有Adapter上限。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError("桥接批次超过现有Adapter上限。")
        # 变量更新：计算并保存required_activation_keys，右侧逻辑为`{'modify_registry_during_acceptance', 'modify_capability_matrix_during_acceptance', 'au...`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        required_activation_keys = {
            "modify_registry_during_acceptance",
            "modify_capability_matrix_during_acceptance",
            "automatic_activation_allowed",
            "activation_requires_verified_report",
        }
        # 条件门禁：判断`set(self.activation_policy) != required_activation_keys`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if set(self.activation_policy) != required_activation_keys:
            # 错误阻断：抛出`DataContractError('activation_policy字段异常。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError("activation_policy字段异常。")
        # 条件门禁：判断`any((self.activation_policy['modify_registry_during_acceptance'], self.activation_policy['modify_...`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if any(
            (
                self.activation_policy[
                    "modify_registry_during_acceptance"
                ],
                self.activation_policy[
                    "modify_capability_matrix_during_acceptance"
                ],
                self.activation_policy[
                    "automatic_activation_allowed"
                ],
            )
        ):
            # 错误阻断：抛出`DataContractError('真实验收不得自动修改或激活路由。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError("真实验收不得自动修改或激活路由。")
        # 条件门禁：判断`not self.activation_policy['activation_requires_verified_report']`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if not self.activation_policy[
            "activation_requires_verified_report"
        ]:
            # 错误阻断：抛出`DataContractError('激活必须要求验收报告。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError("激活必须要求验收报告。")


# 执行load_dolphindb_provider_plugin_bridge_config逻辑，把输入参数转换为受合同约束的结果。
# - 参数path：类型str | Path；进入函数后按合同校验或参与计算。
# - 输出：返回类型DolphinDBProviderPluginBridgeConfig；调用方按该类型继续校验、路由或序列化。
# - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
def load_dolphindb_provider_plugin_bridge_config(
    path: str | Path,
) -> DolphinDBProviderPluginBridgeConfig:
    # 变量更新：计算并保存raw，右侧逻辑为`json.loads(Path(path).read_text(encoding='utf-8'))`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    # 条件门禁：判断`not isinstance(raw, dict)`，条件为真时进入受保护分支。
    # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
    # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
    if not isinstance(raw, dict):
        # 错误阻断：抛出`DataContractError('DolphinDB桥接配置根节点必须是对象。')`并停止当前路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
        # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
        raise DataContractError("DolphinDB桥接配置根节点必须是对象。")
    # 变量更新：计算并保存auth，右侧逻辑为`raw['authentication_reference']`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    auth = raw["authentication_reference"]
    # 变量更新：计算并保存runtime，右侧逻辑为`raw['runtime']`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    runtime = raw["runtime"]
    # 变量更新：计算并保存rate，右侧逻辑为`raw['rate_limit_policy']`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    rate = raw["rate_limit_policy"]
    # 变量更新：计算并保存retry，右侧逻辑为`raw['retry_policy']`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    retry = raw["retry_policy"]
    # 变量更新：计算并保存batch，右侧逻辑为`raw['batch_policy']`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    batch = raw["batch_policy"]
    # 变量更新：计算并保存pagination，右侧逻辑为`raw['pagination_policy']`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    pagination = raw["pagination_policy"]
    # 变量更新：计算并保存subscription，右侧逻辑为`raw['subscription_policy']`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    subscription = raw["subscription_policy"]
    # 变量更新：计算并保存license_raw，右侧逻辑为`raw['license_boundary']`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    license_raw = raw["license_boundary"]
    # 结果返回：把`DolphinDBProviderPluginBridgeConfig(task_id=str(raw['task_id']), bridge_version=str(raw['bridge_v...`交给调用方。
    # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
    # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
    return DolphinDBProviderPluginBridgeConfig(
        task_id=str(raw["task_id"]),
        bridge_version=str(raw["bridge_version"]),
        bridge_status=str(raw["bridge_status"]),
        provider_id=str(raw["provider_id"]),
        plugin_id=str(raw["plugin_id"]),
        entrypoint=str(raw["entrypoint"]),
        legacy_adapter_class=str(raw["legacy_adapter_class"]),
        reuse_strategy=str(raw["reuse_strategy"]),
        custom_query_engine_implemented=bool(
            raw["custom_query_engine_implemented"]
        ),
        custom_session_engine_implemented=bool(
            raw["custom_session_engine_implemented"]
        ),
        custom_dolphindb_protocol_implemented=bool(
            raw["custom_dolphindb_protocol_implemented"]
        ),
        authentication_reference=AuthenticationReference(
            reference_id=str(auth["reference_id"]),
            kind=AuthenticationReferenceKind(str(auth["kind"])),
            locator=str(auth["locator"]),
            scopes=tuple(str(value) for value in auth["scopes"]),
        ),
        operating_systems=tuple(
            str(value) for value in runtime["operating_systems"]
        ),
        architecture=str(runtime["architecture"]),
        sdk_name=str(runtime["sdk_name"]),
        installation_probe=str(runtime["installation_probe"]),
        capabilities={
            str(key): CapabilityImplementationStatus(str(value))
            for key, value in raw["capabilities"].items()
        },
        permitted_usages=tuple(
            str(value) for value in raw["permitted_usages"]
        ),
        rate_limit_policy=RateLimitPolicy(
            requests_per_period=rate["requests_per_period"],
            period_seconds=rate["period_seconds"],
            burst_size=rate["burst_size"],
            maximum_concurrency=int(rate["maximum_concurrency"]),
            evidence_status=PolicyEvidenceStatus(
                str(rate["evidence_status"])
            ),
            evidence_refs=tuple(
                str(value) for value in rate["evidence_refs"]
            ),
        ),
        retry_policy=RetryPolicy(
            maximum_attempts=int(retry["maximum_attempts"]),
            backoff_seconds=tuple(
                int(value) for value in retry["backoff_seconds"]
            ),
            retryable_error_codes=tuple(
                str(value)
                for value in retry["retryable_error_codes"]
            ),
        ),
        batch_policy=BatchPolicy(
            recommended_entities_per_request=int(
                batch["recommended_entities_per_request"]
            ),
            maximum_entities_per_request=int(
                batch["maximum_entities_per_request"]
            ),
            recommended_rows_per_batch=int(
                batch["recommended_rows_per_batch"]
            ),
            maximum_rows_per_batch=int(
                batch["maximum_rows_per_batch"]
            ),
            supports_date_range=bool(batch["supports_date_range"]),
            supports_parallel_requests=bool(
                batch["supports_parallel_requests"]
            ),
        ),
        pagination_policy=PaginationPolicy(
            mode=PaginationMode(str(pagination["mode"])),
            default_page_size=pagination["default_page_size"],
            maximum_page_size=pagination["maximum_page_size"],
            maximum_pages=pagination["maximum_pages"],
            cursor_field=pagination["cursor_field"],
        ),
        subscription_policy=SubscriptionPolicy(
            mode=SubscriptionMode(str(subscription["mode"])),
            maximum_symbols=subscription["maximum_symbols"],
            heartbeat_seconds=subscription["heartbeat_seconds"],
            reconnect_supported=bool(
                subscription["reconnect_supported"]
            ),
            replay_supported=bool(subscription["replay_supported"]),
        ),
        license_boundary=LicenseBoundary(
            decision=LicenseDecision(str(license_raw["decision"])),
            permitted_usages=tuple(
                str(value)
                for value in license_raw["permitted_usages"]
            ),
            cache_allowed=bool(license_raw["cache_allowed"]),
            persistent_storage_allowed=bool(
                license_raw["persistent_storage_allowed"]
            ),
            redistribution_allowed=bool(
                license_raw["redistribution_allowed"]
            ),
            maximum_retention_days=license_raw[
                "maximum_retention_days"
            ],
            evidence_refs=tuple(
                str(value)
                for value in license_raw["evidence_refs"]
            ),
        ),
        supported_operations=tuple(
            str(value) for value in raw["supported_operations"]
        ),
        activation_policy={
            str(key): bool(value)
            for key, value in raw["activation_policy"].items()
        },
        hard_rules=tuple(str(value) for value in raw["hard_rules"]),
    )


# 执行default_dolphindb_runtime_probe逻辑，把输入参数转换为受合同约束的结果。
# - 输入：本逻辑不接收外部业务参数，只读取对象状态或模块常量。
# - 输出：返回类型Mapping[str, Any]；调用方按该类型继续校验、路由或序列化。
# - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
def default_dolphindb_runtime_probe() -> Mapping[str, Any]:
    # 变量更新：计算并保存spec，右侧逻辑为`importlib.util.find_spec('dolphindb')`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    spec = importlib.util.find_spec("dolphindb")
    # 变量更新：计算并保存installed，右侧逻辑为`spec is not None`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    installed = spec is not None
    # 变量更新：计算并保存version，右侧逻辑为`None`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    version = None
    # 条件门禁：判断`installed`，条件为真时进入受保护分支。
    # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
    # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
    if installed:
        # 异常边界：执行可能失败的转换或外部调用，并把底层异常转换为项目可理解的合同错误。
        # - 数据变化：成功路径产生正常结果，失败路径保留原异常作为cause或记录明确错误。
        # - 为什么这样写：统一异常类型可以让上层门禁稳定处理，而不依赖第三方异常细节。
        try:
            # 变量更新：计算并保存version，右侧逻辑为`importlib.metadata.version('dolphindb')`。
            # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
            # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
            version = importlib.metadata.version("dolphindb")
        # 异常转换：捕获预期失败并保留上下文，随后转成项目统一错误或降级结果。
        # - 为什么这样写：上层不需要理解第三方异常细节，也能得到稳定错误语义。
        except importlib.metadata.PackageNotFoundError:
            # 变量更新：计算并保存version，右侧逻辑为`'unknown'`。
            # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
            # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
            version = "unknown"
    # 结果返回：把`{'installed': installed, 'sdk_version': version, 'python_version': f'{sys.version_info.major}.{sy...`交给调用方。
    # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
    # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
    return {
        "installed": installed,
        "sdk_version": version,
        "python_version": (
            f"{sys.version_info.major}.{sys.version_info.minor}"
        ),
        "operating_system": platform.system() or "Unknown",
        "architecture": platform.machine() or "unknown",
        "probe": "importlib.util.find_spec + importlib.metadata.version",
    }


# 复用DolphinDBDataSourceAdapter的通用Provider插件桥。
# - 状态成员：枚举值或方法共同描述该合同允许的有限状态和行为。
# - 数据变化：类本身不执行隐式I/O，实例字段只在显式构造、校验或方法调用时变化。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
class DolphinDBProviderPluginBridge:
    """复用DolphinDBDataSourceAdapter的通用Provider插件桥。"""

    # 执行__init__逻辑，把输入参数转换为受合同约束的结果。
    # - 关键字参数adapter：类型DolphinDBDataSourceAdapter，必须显式提供；用于控制本次调用行为。
    # - 关键字参数config：类型DolphinDBProviderPluginBridgeConfig，必须显式提供；用于控制本次调用行为。
    # - 关键字参数runtime_probe：类型RuntimeProbe | None，默认值None；用于控制本次调用行为。
    # - 输出：返回类型None；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
    def __init__(
        self,
        *,
        adapter: DolphinDBDataSourceAdapter,
        config: DolphinDBProviderPluginBridgeConfig,
        runtime_probe: RuntimeProbe | None = None,
    ) -> None:
        # 条件门禁：判断`adapter is None`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if adapter is None:
            # 错误阻断：抛出`DataContractError('adapter不能为空。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError("adapter不能为空。")
        # 条件门禁：判断`not isinstance(config, DolphinDBProviderPluginBridgeConfig)`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if not isinstance(config, DolphinDBProviderPluginBridgeConfig):
            # 错误阻断：抛出`DataContractError('config类型异常。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError("config类型异常。")
        # 变量更新：计算并保存self._adapter，右侧逻辑为`adapter`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        self._adapter = adapter
        # 变量更新：计算并保存self.config，右侧逻辑为`config`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        self.config = config
        # 变量更新：计算并保存self._runtime_probe，右侧逻辑为`runtime_probe or default_dolphindb_runtime_probe`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        self._runtime_probe = (
            runtime_probe or default_dolphindb_runtime_probe
        )
        # 变量更新：计算并保存self._session_open，右侧逻辑为`False`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        self._session_open = False

    # 执行adapter逻辑，把输入参数转换为受合同约束的结果。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态或模块常量。
    # - 输出：返回类型DolphinDBDataSourceAdapter；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
    @property
    def adapter(self) -> DolphinDBDataSourceAdapter:
        # 结果返回：把`self._adapter`交给调用方。
        # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
        # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
        return self._adapter

    # 执行describe逻辑，把输入参数转换为受合同约束的结果。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态或模块常量。
    # - 输出：返回类型ProviderRegistryEntry；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：返回静态插件身份但保持路由禁用，防止描述阶段自动激活。
    def describe(self) -> ProviderRegistryEntry:
        # 结果返回：把`ProviderRegistryEntry(provider_id=self.config.provider_id, plugin_id=self.config.plugin_id, regis...`交给调用方。
        # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
        # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
        return ProviderRegistryEntry(
            provider_id=self.config.provider_id,
            plugin_id=self.config.plugin_id,
            registration_status=(
                PluginRegistrationStatus.DISCOVERY_PENDING
            ),
            entrypoint=self.config.entrypoint,
            priority=10,
            enabled_for_routing=False,
            discovery_result_ref=None,
            authentication_reference_ref=(
                self.config.authentication_reference.locator
            ),
            notes=(
                "薄桥接复用DolphinDBDataSourceAdapter；"
                "真实验收前不启用路由。"
            ),
        )

    # 执行health_check逻辑，把输入参数转换为受合同约束的结果。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态或模块常量。
    # - 输出：返回类型ProviderHealthSnapshot；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：把底层健康结果翻译为Provider统一状态，便于路由层使用同一判定标准。
    def health_check(self) -> ProviderHealthSnapshot:
        # 变量更新：计算并保存started，右侧逻辑为`time.perf_counter()`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        started = time.perf_counter()
        # 变量更新：计算并保存result，右侧逻辑为`self._adapter.health_check()`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        result = self._adapter.health_check()
        # 变量更新：计算并保存latency_ms，右侧逻辑为`(time.perf_counter() - started) * 1000.0`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 固定数值：本表达式包含1000.0；来源是当前项目既有合同或算法定义，迁移注释不改变其数值。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        latency_ms = (time.perf_counter() - started) * 1000.0
        # 变量更新：计算并保存status_value，右侧逻辑为`getattr(getattr(result, 'status', None), 'value', str(getattr(result, 'status', ''))).u...`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        status_value = getattr(
            getattr(result, "status", None),
            "value",
            str(getattr(result, "status", "")),
        ).upper()
        # 变量更新：计算并保存blocking，右侧逻辑为`bool(getattr(result, 'blocking', False))`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        blocking = bool(getattr(result, "blocking", False))
        # 条件门禁：判断`status_value == 'PASSED' and (not blocking)`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if status_value == "PASSED" and not blocking:
            # 变量更新：计算并保存status，右侧逻辑为`ProviderHealthStatus.HEALTHY`。
            # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
            # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
            status = ProviderHealthStatus.HEALTHY
        # 备用分支：当前面的条件不满足时执行此路径。
        # - 为什么这样写：显式覆盖互斥状态，避免未处理输入静默落空。
        # 条件门禁：判断`status_value in {'WARNING', 'WARN'} and (not blocking)`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        elif status_value in {"WARNING", "WARN"} and not blocking:
            # 变量更新：计算并保存status，右侧逻辑为`ProviderHealthStatus.DEGRADED`。
            # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
            # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
            status = ProviderHealthStatus.DEGRADED
        # 备用分支：当前面的条件不满足时执行此路径。
        # - 为什么这样写：显式覆盖互斥状态，避免未处理输入静默落空。
        else:
            # 变量更新：计算并保存status，右侧逻辑为`ProviderHealthStatus.UNAVAILABLE`。
            # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
            # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
            status = ProviderHealthStatus.UNAVAILABLE
        # 变量更新：计算并保存description，右侧逻辑为`str(getattr(result, 'description', 'DolphinDB health check')).strip() or 'DolphinDB hea...`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        description = str(
            getattr(result, "description", "DolphinDB health check")
        ).strip() or "DolphinDB health check"
        # 结果返回：把`ProviderHealthSnapshot(status=status, checked_at=datetime.now(timezone.utc), latency_ms=latency_m...`交给调用方。
        # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
        # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
        return ProviderHealthSnapshot(
            status=status,
            checked_at=datetime.now(timezone.utc),
            latency_ms=latency_ms,
            message=description,
            evidence_refs=(
                "legacy-adapter:DolphinDBDataSourceAdapter.health_check",
            ),
        )

    # 执行discover逻辑，把输入参数转换为受合同约束的结果。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态或模块常量。
    # - 输出：返回类型ProviderDiscoveryResult；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：把运行时、健康、许可证和能力证据合并成单一发现结果，避免把计划能力误当成真实能力。
    def discover(self) -> ProviderDiscoveryResult:
        # 变量更新：计算并保存runtime_raw，右侧逻辑为`dict(self._runtime_probe())`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        runtime_raw = dict(self._runtime_probe())
        # 变量更新：计算并保存installed，右侧逻辑为`bool(runtime_raw.get('installed'))`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        installed = bool(runtime_raw.get("installed"))
        # 变量更新：计算并保存health，右侧逻辑为`self.health_check()`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        health = self.health_check()
        # 变量更新：计算并保存errors，右侧逻辑为`[]`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        errors: list[str] = []
        # 变量更新：计算并保存warnings，右侧逻辑为`['LEGACY_ADAPTER_BRIDGE', 'REGISTRY_ACTIVATION_REQUIRES_SEPARATE_TASK']`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        warnings: list[str] = [
            "LEGACY_ADAPTER_BRIDGE",
            "REGISTRY_ACTIVATION_REQUIRES_SEPARATE_TASK",
        ]
        # 条件门禁：判断`not installed`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if not installed:
            # API调用：执行`errors.append('DOLPHINDB_PYTHON_CLIENT_NOT_INSTALLED')`以触发注册、写入对象状态或其他显式副作用。
            # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
            # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
            errors.append("DOLPHINDB_PYTHON_CLIENT_NOT_INSTALLED")
        # 条件门禁：判断`health.status is ProviderHealthStatus.UNAVAILABLE`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if health.status is ProviderHealthStatus.UNAVAILABLE:
            # API调用：执行`errors.append('DOLPHINDB_HEALTH_UNAVAILABLE')`以触发注册、写入对象状态或其他显式副作用。
            # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
            # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
            errors.append("DOLPHINDB_HEALTH_UNAVAILABLE")
        # 变量更新：计算并保存outcome，右侧逻辑为`DiscoveryOutcome.COMPLETE if not errors else DiscoveryOutcome.FAILED`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        outcome = (
            DiscoveryOutcome.COMPLETE
            if not errors
            else DiscoveryOutcome.FAILED
        )
        # 变量更新：计算并保存runtime，右侧逻辑为`SdkRuntimeDescriptor(provider_id=self.config.provider_id, runtime_id=f"runtime:{self.co...`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 固定数值：本表达式包含0；来源是当前项目既有合同或算法定义，迁移注释不改变其数值。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        runtime = SdkRuntimeDescriptor(
            provider_id=self.config.provider_id,
            runtime_id=(
                f"runtime:{self.config.provider_id}:"
                f"{runtime_raw.get('sdk_version') or 'unknown'}"
            ),
            operating_systems=(
                str(
                    runtime_raw.get("operating_system")
                    or self.config.operating_systems[0]
                ),
            ),
            python_versions=(
                str(
                    runtime_raw.get("python_version")
                    or f"{sys.version_info.major}."
                    f"{sys.version_info.minor}"
                ),
            ),
            architecture=str(
                runtime_raw.get("architecture")
                or self.config.architecture
            ),
            client_name="Local DolphinDB Server",
            client_version=None,
            sdk_name=self.config.sdk_name,
            sdk_version=(
                str(runtime_raw["sdk_version"])
                if runtime_raw.get("sdk_version") is not None
                else None
            ),
            installed=installed,
            installation_probe=str(
                runtime_raw.get("probe")
                or self.config.installation_probe
            ),
            notes=(
                "仅探测Python客户端并复用现有Adapter；"
                "不重新实现DolphinDB协议。"
            ),
        )
        # 结果返回：把`ProviderDiscoveryResult(discovery_id=f'discovery:{self.config.provider_id}:{datetime.now(timezone...`交给调用方。
        # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
        # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
        return ProviderDiscoveryResult(
            discovery_id=(
                f"discovery:{self.config.provider_id}:"
                f"{datetime.now(timezone.utc).isoformat()}"
            ),
            provider_id=self.config.provider_id,
            plugin_id=self.config.plugin_id,
            outcome=outcome,
            discovered_at=datetime.now(timezone.utc),
            runtime=runtime,
            authentication_reference=(
                self.config.authentication_reference
            ),
            capabilities=self.config.capabilities,
            rate_limit_policy=self.config.rate_limit_policy,
            retry_policy=self.config.retry_policy,
            batch_policy=self.config.batch_policy,
            pagination_policy=self.config.pagination_policy,
            subscription_policy=self.config.subscription_policy,
            license_boundary=self.config.license_boundary,
            health=health,
            warnings=tuple(warnings),
            errors=tuple(errors),
        )

    # 执行open_session逻辑，把输入参数转换为受合同约束的结果。
    # - 参数authentication_reference：类型AuthenticationReference；进入函数后按合同校验或参与计算。
    # - 输出：返回类型None；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：只校验认证引用和环境变量存在性，不把密码写入配置或对象。
    def open_session(
        self,
        authentication_reference: AuthenticationReference,
    ) -> None:
        # 条件门禁：判断`authentication_reference.reference_id != self.config.authentication_reference.reference_id or aut...`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if (
            authentication_reference.reference_id
            != self.config.authentication_reference.reference_id
            or authentication_reference.kind
            is not self.config.authentication_reference.kind
            or authentication_reference.locator
            != self.config.authentication_reference.locator
        ):
            # 错误阻断：抛出`DataContractError('认证引用与桥接配置不一致。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError("认证引用与桥接配置不一致。")
        # 变量更新：计算并保存env_name，右侧逻辑为`authentication_reference.locator.removeprefix('env://')`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        env_name = authentication_reference.locator.removeprefix(
            "env://"
        )
        # 条件门禁：判断`not env_name or not os.environ.get(env_name)`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if not env_name or not os.environ.get(env_name):
            # 错误阻断：抛出`DataContractError(f"环境变量未设置：{env_name or '<empty>'}")`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError(
                f"环境变量未设置：{env_name or '<empty>'}"
            )
        # 变量更新：计算并保存self._session_open，右侧逻辑为`True`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        self._session_open = True

    # 执行close_session逻辑，把输入参数转换为受合同约束的结果。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态或模块常量。
    # - 输出：返回类型None；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：显式释放可释放的底层会话并更新插件状态，防止关闭后继续查询。
    def close_session(self) -> None:
        # 变量更新：计算并保存close_method，右侧逻辑为`getattr(self._adapter, 'close', None)`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        close_method = getattr(self._adapter, "close", None)
        # 条件门禁：判断`callable(close_method)`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if callable(close_method):
            # API调用：执行`close_method()`以触发注册、写入对象状态或其他显式副作用。
            # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
            # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
            close_method()
        # 变量更新：计算并保存self._session_open，右侧逻辑为`False`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        self._session_open = False

    # 执行_assert_request逻辑，把输入参数转换为受合同约束的结果。
    # - 参数request：类型ProviderQueryRequest；进入函数后按合同校验或参与计算。
    # - 输出：返回类型None；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
    def _assert_request(self, request: ProviderQueryRequest) -> None:
        # 条件门禁：判断`not self._session_open`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if not self._session_open:
            # 错误阻断：抛出`DataContractError('Provider插件会话尚未打开。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError("Provider插件会话尚未打开。")
        # 条件门禁：判断`request.provider_id != self.config.provider_id`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if request.provider_id != self.config.provider_id:
            # 错误阻断：抛出`DataContractError('请求provider_id与插件不一致。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError("请求provider_id与插件不一致。")
        # 条件门禁：判断`request.capability not in self.config.capabilities`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if request.capability not in self.config.capabilities:
            # 错误阻断：抛出`DataContractError('请求能力未在桥接配置中登记。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError("请求能力未在桥接配置中登记。")
        # 变量更新：计算并保存capability_status，右侧逻辑为`self.config.capabilities[request.capability]`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        capability_status = self.config.capabilities[
            request.capability
        ]
        # 条件门禁：判断`capability_status not in {CapabilityImplementationStatus.IMPLEMENTED, CapabilityImplementationSta...`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if capability_status not in {
            CapabilityImplementationStatus.IMPLEMENTED,
            CapabilityImplementationStatus.VERIFIED,
        }:
            # 错误阻断：抛出`DataContractError('请求能力尚未实现或验证。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError("请求能力尚未实现或验证。")
        # 条件门禁：判断`request.usage not in self.config.permitted_usages`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if request.usage not in self.config.permitted_usages:
            # 错误阻断：抛出`DataContractError('请求用途不在本地数据许可范围。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError("请求用途不在本地数据许可范围。")
        # 条件门禁：判断`request.maximum_rows > self.config.batch_policy.maximum_rows_per_batch`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if (
            request.maximum_rows
            > self.config.batch_policy.maximum_rows_per_batch
        ):
            # 错误阻断：抛出`DataContractError('请求行数超过桥接批次上限。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError("请求行数超过桥接批次上限。")
        # 条件门禁：判断`request.operation not in self.config.supported_operations`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if request.operation not in self.config.supported_operations:
            # 错误阻断：抛出`DataContractError('桥接不支持请求操作。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError("桥接不支持请求操作。")

    # 执行query_batch逻辑，把输入参数转换为受合同约束的结果。
    # - 参数request：类型ProviderQueryRequest；进入函数后按合同校验或参与计算。
    # - 输出：返回类型ProviderQueryBatch；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：把通用请求委托给现有适配器并转换为统一批次，复用已有安全和查询逻辑。
    def query_batch(
        self,
        request: ProviderQueryRequest,
    ) -> ProviderQueryBatch:
        # API调用：执行`self._assert_request(request)`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        self._assert_request(request)
        # 变量更新：计算并保存warnings，右侧逻辑为`['LEGACY_ADAPTER_BRIDGE']`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        warnings = ["LEGACY_ADAPTER_BRIDGE"]
        # 条件门禁：判断`request.operation == 'READ_RAW_TABLE'`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if request.operation == "READ_RAW_TABLE":
            # 变量更新：计算并保存source_object_name，右侧逻辑为`_require_text(request.parameters.get('source_object_name'), 'source_object_name')`。
            # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
            # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
            source_object_name = _require_text(
                request.parameters.get("source_object_name"),
                "source_object_name",
            )
            # 变量更新：计算并保存database_uri，右侧逻辑为`_require_text(request.parameters.get('database_uri'), 'database_uri')`。
            # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
            # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
            database_uri = _require_text(
                request.parameters.get("database_uri"),
                "database_uri",
            )
            # 变量更新：计算并保存raw_batch，右侧逻辑为`self._adapter.read_raw(source_object_name, database_uri=database_uri, limit=request.max...`。
            # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
            # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
            raw_batch = self._adapter.read_raw(
                source_object_name,
                database_uri=database_uri,
                limit=request.maximum_rows,
            )
            # 变量更新：计算并保存records，右侧逻辑为`tuple((dict(item) for item in raw_batch.records))`。
            # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
            # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
            records = tuple(
                dict(item) for item in raw_batch.records
            )
            # 变量更新：计算并保存source_request_id，右侧逻辑为`f'{database_uri}/{source_object_name}'`。
            # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
            # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
            source_request_id = (
                f"{database_uri}/{source_object_name}"
            )
        # 备用分支：当前面的条件不满足时执行此路径。
        # - 为什么这样写：显式覆盖互斥状态，避免未处理输入静默落空。
        # 条件门禁：判断`request.operation == 'RUN_READONLY_QUERY'`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        elif request.operation == "RUN_READONLY_QUERY":
            # 变量更新：计算并保存script，右侧逻辑为`_require_text(request.parameters.get('script'), 'script')`。
            # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
            # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
            script = _require_text(
                request.parameters.get("script"),
                "script",
            )
            # 变量更新：计算并保存result，右侧逻辑为`self._adapter.run_readonly_query(script)`。
            # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
            # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
            result = self._adapter.run_readonly_query(script)
            # 变量更新：计算并保存(_, normalised)，右侧逻辑为`_normalise_records_with_legacy_adapter(self._adapter, result)`。
            # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
            # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
            _, normalised = _normalise_records_with_legacy_adapter(
                self._adapter,
                result,
            )
            # 条件门禁：判断`len(normalised) > request.maximum_rows`，条件为真时进入受保护分支。
            # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
            # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
            if len(normalised) > request.maximum_rows:
                # 错误阻断：抛出`DataContractError('只读查询返回行数超过请求maximum_rows；请在查询中显式限制结果。')`并停止当前路径。
                # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
                # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
                raise DataContractError(
                    "只读查询返回行数超过请求maximum_rows；"
                    "请在查询中显式限制结果。"
                )
            # 变量更新：计算并保存records，右侧逻辑为`tuple(normalised)`。
            # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
            # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
            records = tuple(normalised)
            # 变量更新：计算并保存source_request_id，右侧逻辑为`request.request_id`。
            # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
            # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
            source_request_id = request.request_id
            # API调用：执行`warnings.append('RESULT_NORMALISED_BY_LEGACY_ADAPTER')`以触发注册、写入对象状态或其他显式副作用。
            # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
            # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
            warnings.append(
                "RESULT_NORMALISED_BY_LEGACY_ADAPTER"
            )
        # 备用分支：当前面的条件不满足时执行此路径。
        # - 为什么这样写：显式覆盖互斥状态，避免未处理输入静默落空。
        else:
            # 错误阻断：抛出`DataContractError('桥接不支持请求操作。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError("桥接不支持请求操作。")

        # 结果返回：把`ProviderQueryBatch(request_id=request.request_id, provider_id=self.config.provider_id, capability...`交给调用方。
        # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
        # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
        return ProviderQueryBatch(
            request_id=request.request_id,
            provider_id=self.config.provider_id,
            capability=request.capability,
            records=records,
            next_cursor=None,
            source_request_id=source_request_id,
            warnings=tuple(warnings),
        )

    # 执行iter_pages逻辑，把输入参数转换为受合同约束的结果。
    # - 参数request：类型ProviderQueryRequest；进入函数后按合同校验或参与计算。
    # - 输出：返回类型Iterator[ProviderQueryBatch]；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
    def iter_pages(
        self,
        request: ProviderQueryRequest,
    ) -> Iterator[ProviderQueryBatch]:
        yield self.query_batch(request)

    # 执行subscribe逻辑，把输入参数转换为受合同约束的结果。
    # - 参数request：类型ProviderSubscriptionRequest；进入函数后按合同校验或参与计算。
    # - 输出：返回类型str；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
    def subscribe(
        self,
        request: ProviderSubscriptionRequest,
    ) -> str:
        # 状态清理：删除`request`引用。
        # - 为什么这样写：显式释放不再需要的引用，避免后续代码误用。
        del request
        # 错误阻断：抛出`DataContractError('当前DolphinDB薄桥接不支持实时订阅。')`并停止当前路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
        # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
        raise DataContractError(
            "当前DolphinDB薄桥接不支持实时订阅。"
        )

    # 执行unsubscribe逻辑，把输入参数转换为受合同约束的结果。
    # - 参数subscription_id：类型str；进入函数后按合同校验或参与计算。
    # - 输出：返回类型None；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
    def unsubscribe(self, subscription_id: str) -> None:
        # API调用：执行`_require_text(subscription_id, 'subscription_id')`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        _require_text(subscription_id, "subscription_id")
        # 错误阻断：抛出`DataContractError('当前DolphinDB薄桥接不支持实时订阅。')`并停止当前路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
        # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
        raise DataContractError(
            "当前DolphinDB薄桥接不支持实时订阅。"
        )
