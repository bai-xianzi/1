# 模块总览：TASK_020A：供应商能力矩阵与单机资源档案合同。
# - 输入输出：本模块通过强类型对象和纯函数交换数据，不在导入阶段执行隐式网络或数据库写入。
# - 数据变化：只有显式构造、校验、加载或方法调用才会产生新对象或更新受控状态。
# - 为什么这样写：先说明模块边界，读者可以在阅读实现前理解职责、风险和复用方式。
"""TASK_020A：供应商能力矩阵与单机资源档案合同。"""
# 依赖导入：加载标准库、类型工具和项目内合同，供下方数据结构与校验逻辑复用。
# - 标准库只提供解析、数学、时间、路径和类型能力；项目模块提供统一异常与上游合同。
# - 为什么这样写：集中导入让依赖边界清晰，并避免在函数内部重复加载同一模块。
from __future__ import annotations

import json
import math
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

from .data_contracts import DataContractError


# 定义Provider从登记到真实验收、激活和暂停的生命周期。
# - 状态成员：枚举值或方法共同描述该合同允许的有限状态和行为。
# - 数据变化：类本身不执行隐式I/O，实例字段只在显式构造、校验或方法调用时变化。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
class ProviderLifecycle(str, Enum):
    # 变量更新：计算并保存IMPLEMENTED_FOUNDATION，右侧逻辑为`'IMPLEMENTED_FOUNDATION'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    IMPLEMENTED_FOUNDATION = "IMPLEMENTED_FOUNDATION"
    # 变量更新：计算并保存REGISTERED_TARGET，右侧逻辑为`'REGISTERED_TARGET'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    REGISTERED_TARGET = "REGISTERED_TARGET"
    # 变量更新：计算并保存DISCOVERY_COMPLETE，右侧逻辑为`'DISCOVERY_COMPLETE'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    DISCOVERY_COMPLETE = "DISCOVERY_COMPLETE"
    # 变量更新：计算并保存ADAPTER_IMPLEMENTED，右侧逻辑为`'ADAPTER_IMPLEMENTED'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    ADAPTER_IMPLEMENTED = "ADAPTER_IMPLEMENTED"
    # 变量更新：计算并保存REAL_ACCEPTED，右侧逻辑为`'REAL_ACCEPTED'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    REAL_ACCEPTED = "REAL_ACCEPTED"
    # 变量更新：计算并保存ACTIVATED，右侧逻辑为`'ACTIVATED'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    ACTIVATED = "ACTIVATED"
    # 变量更新：计算并保存SUSPENDED，右侧逻辑为`'SUSPENDED'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    SUSPENDED = "SUSPENDED"


# 定义Provider能力发现的证据完成度。
# - 状态成员：枚举值或方法共同描述该合同允许的有限状态和行为。
# - 数据变化：类本身不执行隐式I/O，实例字段只在显式构造、校验或方法调用时变化。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
class ProviderDiscoveryStatus(str, Enum):
    # 变量更新：计算并保存VERIFIED_IN_PROJECT，右侧逻辑为`'VERIFIED_IN_PROJECT'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    VERIFIED_IN_PROJECT = "VERIFIED_IN_PROJECT"
    # 变量更新：计算并保存DISCOVERY_REQUIRED，右侧逻辑为`'DISCOVERY_REQUIRED'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    DISCOVERY_REQUIRED = "DISCOVERY_REQUIRED"
    # 变量更新：计算并保存DISCOVERY_PARTIAL，右侧逻辑为`'DISCOVERY_PARTIAL'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    DISCOVERY_PARTIAL = "DISCOVERY_PARTIAL"
    # 变量更新：计算并保存DISCOVERY_COMPLETE，右侧逻辑为`'DISCOVERY_COMPLETE'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    DISCOVERY_COMPLETE = "DISCOVERY_COMPLETE"


# 定义单项能力是实现、验证、未验证声明或不可用。
# - 状态成员：枚举值或方法共同描述该合同允许的有限状态和行为。
# - 数据变化：类本身不执行隐式I/O，实例字段只在显式构造、校验或方法调用时变化。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
class CapabilityImplementationStatus(str, Enum):
    # 变量更新：计算并保存IMPLEMENTED，右侧逻辑为`'IMPLEMENTED'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    IMPLEMENTED = "IMPLEMENTED"
    # 变量更新：计算并保存VERIFIED，右侧逻辑为`'VERIFIED'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    VERIFIED = "VERIFIED"
    # 变量更新：计算并保存DECLARED_UNVERIFIED，右侧逻辑为`'DECLARED_UNVERIFIED'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    DECLARED_UNVERIFIED = "DECLARED_UNVERIFIED"
    # 变量更新：计算并保存NOT_AVAILABLE，右侧逻辑为`'NOT_AVAILABLE'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    NOT_AVAILABLE = "NOT_AVAILABLE"


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


# 执行_nonnegative_number逻辑，把输入参数转换为受合同约束的结果。
# - 参数value：类型Any；进入函数后按合同校验或参与计算。
# - 参数field_name：类型str；进入函数后按合同校验或参与计算。
# - 输出：返回类型float；调用方按该类型继续校验、路由或序列化。
# - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
# - 为什么这样写：把输入统一转换为有限浮点数并拒绝负值，避免NaN和无穷大污染资源计算。
def _nonnegative_number(value: Any, field_name: str) -> float:
    # 条件门禁：判断`isinstance(value, bool)`，条件为真时进入受保护分支。
    # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
    # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
    if isinstance(value, bool):
        # 错误阻断：抛出`DataContractError(f'{field_name}必须是非负有限数。')`并停止当前路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
        # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
        raise DataContractError(f"{field_name}必须是非负有限数。")
    # 异常边界：执行可能失败的转换或外部调用，并把底层异常转换为项目可理解的合同错误。
    # - 数据变化：成功路径产生正常结果，失败路径保留原异常作为cause或记录明确错误。
    # - 为什么这样写：统一异常类型可以让上层门禁稳定处理，而不依赖第三方异常细节。
    try:
        # 变量更新：计算并保存result，右侧逻辑为`float(value)`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        result = float(value)
    # 异常转换：捕获预期失败并保留上下文，随后转成项目统一错误或降级结果。
    # - 为什么这样写：上层不需要理解第三方异常细节，也能得到稳定错误语义。
    except (TypeError, ValueError) as exc:
        # 错误阻断：抛出`DataContractError(f'{field_name}必须是非负有限数。')`并停止当前路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
        # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
        raise DataContractError(
            f"{field_name}必须是非负有限数。"
        ) from exc
    # 条件门禁：判断`not math.isfinite(result) or result < 0`，条件为真时进入受保护分支。
    # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
    # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
    if not math.isfinite(result) or result < 0:
        # 错误阻断：抛出`DataContractError(f'{field_name}必须是非负有限数。')`并停止当前路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
        # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
        raise DataContractError(f"{field_name}必须是非负有限数。")
    # 结果返回：把`result`交给调用方。
    # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
    # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
    return result


# 定义ProviderTarget强类型合同，集中保存相关状态、参数和校验规则。
# - 字段provider_id：类型str。
# - 字段display_name：类型str。
# - 字段provider_kind：类型str。
# - 字段lifecycle：类型ProviderLifecycle。
# - 字段integration_mode：类型str。
# - 字段authentication_mode：类型str。
# - 字段discovery_status：类型ProviderDiscoveryStatus。
# - 字段capabilities：类型Mapping[str, CapabilityImplementationStatus]。
# - 其余字段：另有3项，均在对象创建时统一校验。
# - 数据变化：类本身不执行隐式I/O，实例字段只在显式构造、校验或方法调用时变化。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
@dataclass(frozen=True, slots=True)
class ProviderTarget:
    # 变量更新：计算并保存provider_id，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    provider_id: str
    # 变量更新：计算并保存display_name，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    display_name: str
    # 变量更新：计算并保存provider_kind，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    provider_kind: str
    # 变量更新：计算并保存lifecycle，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    lifecycle: ProviderLifecycle
    # 变量更新：计算并保存integration_mode，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    integration_mode: str
    # 变量更新：计算并保存authentication_mode，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    authentication_mode: str
    # 变量更新：计算并保存discovery_status，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    discovery_status: ProviderDiscoveryStatus
    # 变量更新：计算并保存capabilities，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    capabilities: Mapping[str, CapabilityImplementationStatus]
    # 变量更新：计算并保存license_review_required，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    license_review_required: bool
    # 变量更新：计算并保存execution_capability，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    execution_capability: bool
    # 变量更新：计算并保存notes，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    notes: str

    # 执行__post_init__逻辑，把输入参数转换为受合同约束的结果。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态或模块常量。
    # - 输出：返回类型None；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：在不可变或数据类对象创建后立即校验字段关系，阻止不一致对象进入系统。
    def __post_init__(self) -> None:
        # 迭代处理：依次读取`('provider_id', 'display_name', 'provider_kind', 'integration_mode', 'authent...`中的元素，并绑定到`field_name`。
        # - 维度变化：每轮处理一个元素，可能向列表、字典或累计值中增加一项。
        # - 为什么这样写：显式逐项校验可以精确指出哪个字段或Provider不符合合同。
        for field_name in (
            "provider_id",
            "display_name",
            "provider_kind",
            "integration_mode",
            "authentication_mode",
            "notes",
        ):
            # API调用：执行`object.__setattr__(self, field_name, _require_text(getattr(self, field_name), field_name))`以触发注册、写入对象状态或其他显式副作用。
            # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
            # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
            object.__setattr__(
                self,
                field_name,
                _require_text(getattr(self, field_name), field_name),
            )
        # 变量更新：计算并保存lifecycle，右侧逻辑为`self.lifecycle`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        lifecycle = self.lifecycle
        # 条件门禁：判断`isinstance(lifecycle, str)`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if isinstance(lifecycle, str):
            # 变量更新：计算并保存lifecycle，右侧逻辑为`ProviderLifecycle(lifecycle)`。
            # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
            # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
            lifecycle = ProviderLifecycle(lifecycle)
        # API调用：执行`object.__setattr__(self, 'lifecycle', lifecycle)`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        object.__setattr__(self, "lifecycle", lifecycle)
        # 变量更新：计算并保存discovery，右侧逻辑为`self.discovery_status`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        discovery = self.discovery_status
        # 条件门禁：判断`isinstance(discovery, str)`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if isinstance(discovery, str):
            # 变量更新：计算并保存discovery，右侧逻辑为`ProviderDiscoveryStatus(discovery)`。
            # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
            # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
            discovery = ProviderDiscoveryStatus(discovery)
        # API调用：执行`object.__setattr__(self, 'discovery_status', discovery)`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        object.__setattr__(self, "discovery_status", discovery)
        # 变量更新：计算并保存capabilities，右侧逻辑为`{_require_text(key, 'capability'): value if isinstance(value, CapabilityImplementationS...`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        capabilities = {
            _require_text(key, "capability"): (
                value
                if isinstance(value, CapabilityImplementationStatus)
                else CapabilityImplementationStatus(value)
            )
            for key, value in self.capabilities.items()
        }
        # API调用：执行`object.__setattr__(self, 'capabilities', capabilities)`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        object.__setattr__(self, "capabilities", capabilities)
        # 条件门禁：判断`discovery is ProviderDiscoveryStatus.DISCOVERY_REQUIRED and capabilities`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if (
            discovery is ProviderDiscoveryStatus.DISCOVERY_REQUIRED
            and capabilities
        ):
            # 错误阻断：抛出`DataContractError('待发现Provider不得预填具体能力。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError(
                "待发现Provider不得预填具体能力。"
            )
        # 条件门禁：判断`lifecycle is ProviderLifecycle.ACTIVATED and discovery is not ProviderDiscoveryStatus.DISCOVERY_C...`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if (
            lifecycle is ProviderLifecycle.ACTIVATED
            and discovery
            is not ProviderDiscoveryStatus.DISCOVERY_COMPLETE
        ):
            # 错误阻断：抛出`DataContractError('未完成能力发现的Provider不得激活。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError(
                "未完成能力发现的Provider不得激活。"
            )


# 定义ProviderCapabilityMatrix强类型合同，集中保存相关状态、参数和校验规则。
# - 字段task_id：类型str。
# - 字段matrix_version：类型str。
# - 字段matrix_status：类型str。
# - 字段provider_neutral：类型bool。
# - 字段automatic_activation_allowed：类型bool。
# - 字段secret_storage_allowed：类型bool。
# - 字段core_system_may_import_vendor_sdk：类型bool。
# - 字段upper_layers_may_depend_on_vendor_fields：类型bool。
# - 其余字段：另有4项，均在对象创建时统一校验。
# - 数据变化：类本身不执行隐式I/O，实例字段只在显式构造、校验或方法调用时变化。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
@dataclass(frozen=True, slots=True)
class ProviderCapabilityMatrix:
    # 变量更新：计算并保存task_id，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    task_id: str
    # 变量更新：计算并保存matrix_version，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    matrix_version: str
    # 变量更新：计算并保存matrix_status，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    matrix_status: str
    # 变量更新：计算并保存provider_neutral，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    provider_neutral: bool
    # 变量更新：计算并保存automatic_activation_allowed，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    automatic_activation_allowed: bool
    # 变量更新：计算并保存secret_storage_allowed，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    secret_storage_allowed: bool
    # 变量更新：计算并保存core_system_may_import_vendor_sdk，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    core_system_may_import_vendor_sdk: bool
    # 变量更新：计算并保存upper_layers_may_depend_on_vendor_fields，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    upper_layers_may_depend_on_vendor_fields: bool
    # 变量更新：计算并保存required_adapter_contracts，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    required_adapter_contracts: tuple[str, ...]
    # 变量更新：计算并保存capability_catalog，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    capability_catalog: tuple[str, ...]
    # 变量更新：计算并保存provider_targets，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    provider_targets: tuple[ProviderTarget, ...]
    # 变量更新：计算并保存routing_rules，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    routing_rules: tuple[str, ...]

    # 执行__post_init__逻辑，把输入参数转换为受合同约束的结果。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态或模块常量。
    # - 输出：返回类型None；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：在不可变或数据类对象创建后立即校验字段关系，阻止不一致对象进入系统。
    def __post_init__(self) -> None:
        # 迭代处理：依次读取`('task_id', 'matrix_version', 'matrix_status')`中的元素，并绑定到`field_name`。
        # - 维度变化：每轮处理一个元素，可能向列表、字典或累计值中增加一项。
        # - 为什么这样写：显式逐项校验可以精确指出哪个字段或Provider不符合合同。
        for field_name in ("task_id", "matrix_version", "matrix_status"):
            # API调用：执行`object.__setattr__(self, field_name, _require_text(getattr(self, field_name), field_name))`以触发注册、写入对象状态或其他显式副作用。
            # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
            # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
            object.__setattr__(
                self,
                field_name,
                _require_text(getattr(self, field_name), field_name),
            )
        # 条件门禁：判断`self.task_id != 'TASK_020A'`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if self.task_id != "TASK_020A":
            # 错误阻断：抛出`DataContractError('能力矩阵task_id异常。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError("能力矩阵task_id异常。")
        # 条件门禁：判断`not self.provider_neutral`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if not self.provider_neutral:
            # 错误阻断：抛出`DataContractError('能力矩阵必须保持供应商中立。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError("能力矩阵必须保持供应商中立。")
        # 条件门禁：判断`any((self.automatic_activation_allowed, self.secret_storage_allowed, self.core_system_may_import_...`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if any(
            (
                self.automatic_activation_allowed,
                self.secret_storage_allowed,
                self.core_system_may_import_vendor_sdk,
                self.upper_layers_may_depend_on_vendor_fields,
            )
        ):
            # 错误阻断：抛出`DataContractError('供应商隔离硬约束被破坏。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError("供应商隔离硬约束被破坏。")
        # 迭代处理：依次读取`('required_adapter_contracts', 'capability_catalog', 'routing_rules')`中的元素，并绑定到`field_name`。
        # - 维度变化：每轮处理一个元素，可能向列表、字典或累计值中增加一项。
        # - 为什么这样写：显式逐项校验可以精确指出哪个字段或Provider不符合合同。
        for field_name in (
            "required_adapter_contracts",
            "capability_catalog",
            "routing_rules",
        ):
            # 变量更新：计算并保存values，右侧逻辑为`tuple((_require_text(value, field_name) for value in getattr(self, field_name)))`。
            # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
            # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
            values = tuple(
                _require_text(value, field_name)
                for value in getattr(self, field_name)
            )
            # 条件门禁：判断`not values or len(values) != len(set(values))`，条件为真时进入受保护分支。
            # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
            # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
            if not values or len(values) != len(set(values)):
                # 错误阻断：抛出`DataContractError(f'{field_name}必须非空且唯一。')`并停止当前路径。
                # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
                # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
                raise DataContractError(
                    f"{field_name}必须非空且唯一。"
                )
            # API调用：执行`object.__setattr__(self, field_name, values)`以触发注册、写入对象状态或其他显式副作用。
            # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
            # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
            object.__setattr__(self, field_name, values)
        # 变量更新：计算并保存ids，右侧逻辑为`[item.provider_id for item in self.provider_targets]`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        ids = [item.provider_id for item in self.provider_targets]
        # 条件门禁：判断`not ids or len(ids) != len(set(ids))`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if not ids or len(ids) != len(set(ids)):
            # 错误阻断：抛出`DataContractError('provider_targets必须非空且provider_id唯一。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError(
                "provider_targets必须非空且provider_id唯一。"
            )
        # 变量更新：计算并保存required_targets，右侧逻辑为`{'local_dolphindb', 'wind', 'ifind', 'galaxy_xingyao'}`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        required_targets = {
            "local_dolphindb",
            "wind",
            "ifind",
            "galaxy_xingyao",
        }
        # 条件门禁：判断`not required_targets.issubset(ids)`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if not required_targets.issubset(ids):
            # 错误阻断：抛出`DataContractError('缺少强制供应商目标。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError("缺少强制供应商目标。")
        # 变量更新：计算并保存catalog，右侧逻辑为`set(self.capability_catalog)`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        catalog = set(self.capability_catalog)
        # 迭代处理：依次读取`self.provider_targets`中的元素，并绑定到`target`。
        # - 维度变化：每轮处理一个元素，可能向列表、字典或累计值中增加一项。
        # - 为什么这样写：显式逐项校验可以精确指出哪个字段或Provider不符合合同。
        for target in self.provider_targets:
            # 变量更新：计算并保存unknown，右侧逻辑为`set(target.capabilities) - catalog`。
            # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
            # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
            unknown = set(target.capabilities) - catalog
            # 条件门禁：判断`unknown`，条件为真时进入受保护分支。
            # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
            # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
            if unknown:
                # 错误阻断：抛出`DataContractError(f'{target.provider_id}包含未登记能力：{sorted(unknown)}')`并停止当前路径。
                # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
                # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
                raise DataContractError(
                    f"{target.provider_id}包含未登记能力：{sorted(unknown)}"
                )

    # 执行provider逻辑，把输入参数转换为受合同约束的结果。
    # - 参数provider_id：类型str；进入函数后按合同校验或参与计算。
    # - 输出：返回类型ProviderTarget；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
    def provider(self, provider_id: str) -> ProviderTarget:
        # 变量更新：计算并保存key，右侧逻辑为`_require_text(provider_id, 'provider_id')`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        key = _require_text(provider_id, "provider_id")
        # 迭代处理：依次读取`self.provider_targets`中的元素，并绑定到`target`。
        # - 维度变化：每轮处理一个元素，可能向列表、字典或累计值中增加一项。
        # - 为什么这样写：显式逐项校验可以精确指出哪个字段或Provider不符合合同。
        for target in self.provider_targets:
            # 条件门禁：判断`target.provider_id == key`，条件为真时进入受保护分支。
            # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
            # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
            if target.provider_id == key:
                # 结果返回：把`target`交给调用方。
                # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
                # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
                return target
        # 错误阻断：抛出`DataContractError(f'未登记Provider：{key}')`并停止当前路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
        # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
        raise DataContractError(f"未登记Provider：{key}")

    # 执行eligible_providers逻辑，把输入参数转换为受合同约束的结果。
    # - 参数capability：类型str；进入函数后按合同校验或参与计算。
    # - 输出：返回类型tuple[ProviderTarget, ...]；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
    def eligible_providers(
        self,
        capability: str,
    ) -> tuple[ProviderTarget, ...]:
        # 变量更新：计算并保存key，右侧逻辑为`_require_text(capability, 'capability')`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        key = _require_text(capability, "capability")
        # 条件门禁：判断`key not in self.capability_catalog`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if key not in self.capability_catalog:
            # 错误阻断：抛出`DataContractError(f'未登记标准能力：{key}')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError(f"未登记标准能力：{key}")
        # 变量更新：计算并保存allowed_lifecycle，右侧逻辑为`{ProviderLifecycle.REAL_ACCEPTED, ProviderLifecycle.ACTIVATED}`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        allowed_lifecycle = {
            ProviderLifecycle.REAL_ACCEPTED,
            ProviderLifecycle.ACTIVATED,
        }
        # 变量更新：计算并保存allowed_status，右侧逻辑为`{CapabilityImplementationStatus.IMPLEMENTED, CapabilityImplementationStatus.VERIFIED}`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        allowed_status = {
            CapabilityImplementationStatus.IMPLEMENTED,
            CapabilityImplementationStatus.VERIFIED,
        }
        # 结果返回：把`tuple((target for target in self.provider_targets if target.lifecycle in allowed_lifecycle and ta...`交给调用方。
        # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
        # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
        return tuple(
            target
            for target in self.provider_targets
            if target.lifecycle in allowed_lifecycle
            and target.discovery_status
            in {
                ProviderDiscoveryStatus.VERIFIED_IN_PROJECT,
                ProviderDiscoveryStatus.DISCOVERY_COMPLETE,
            }
            and target.capabilities.get(key) in allowed_status
        )


# 定义SingleMachineResourceProfile强类型合同，集中保存相关状态、参数和校验规则。
# - 字段task_id：类型str。
# - 字段profile_version：类型str。
# - 字段profile_status：类型str。
# - 字段profile_id：类型str。
# - 字段operating_system：类型str。
# - 字段physical_core_count：类型int。
# - 字段logical_thread_count：类型int。
# - 字段memory_gib：类型int。
# - 其余字段：另有17项，均在对象创建时统一校验。
# - 数据变化：类本身不执行隐式I/O，实例字段只在显式构造、校验或方法调用时变化。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
@dataclass(frozen=True, slots=True)
class SingleMachineResourceProfile:
    # 变量更新：计算并保存task_id，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    task_id: str
    # 变量更新：计算并保存profile_version，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    profile_version: str
    # 变量更新：计算并保存profile_status，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    profile_status: str
    # 变量更新：计算并保存profile_id，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    profile_id: str
    # 变量更新：计算并保存operating_system，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    operating_system: str
    # 变量更新：计算并保存physical_core_count，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    physical_core_count: int
    # 变量更新：计算并保存logical_thread_count，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    logical_thread_count: int
    # 变量更新：计算并保存memory_gib，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    memory_gib: int
    # 变量更新：计算并保存gpu_memory_gib，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    gpu_memory_gib: int
    # 变量更新：计算并保存architecture_mode，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    architecture_mode: str
    # 变量更新：计算并保存max_parallel_provider_calls，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    max_parallel_provider_calls: int
    # 变量更新：计算并保存max_parallel_cpu_jobs，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    max_parallel_cpu_jobs: int
    # 变量更新：计算并保存max_parallel_database_queries，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    max_parallel_database_queries: int
    # 变量更新：计算并保存default_batch_rows，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    default_batch_rows: int
    # 变量更新：计算并保存large_batch_rows，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    large_batch_rows: int
    # 变量更新：计算并保存maximum_batch_rows_without_override，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    maximum_batch_rows_without_override: int
    # 变量更新：计算并保存maximum_in_memory_result_mib，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    maximum_in_memory_result_mib: int
    # 变量更新：计算并保存process_memory_soft_limit_mib，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    process_memory_soft_limit_mib: int
    # 变量更新：计算并保存minimum_free_space_gib，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    minimum_free_space_gib: float
    # 变量更新：计算并保存temporary_directory_quota_gib，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    temporary_directory_quota_gib: float
    # 变量更新：计算并保存cache_quota_gib，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    cache_quota_gib: float
    # 变量更新：计算并保存large_download_threshold_gib，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    large_download_threshold_gib: float
    # 变量更新：计算并保存automatic_35gb_minute_data_import_allowed，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    automatic_35gb_minute_data_import_allowed: bool
    # 变量更新：计算并保存gpu_enabled_by_default，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    gpu_enabled_by_default: bool
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
        # 迭代处理：依次读取`('task_id', 'profile_version', 'profile_status', 'profile_id', 'operating_sys...`中的元素，并绑定到`field_name`。
        # - 维度变化：每轮处理一个元素，可能向列表、字典或累计值中增加一项。
        # - 为什么这样写：显式逐项校验可以精确指出哪个字段或Provider不符合合同。
        for field_name in (
            "task_id",
            "profile_version",
            "profile_status",
            "profile_id",
            "operating_system",
            "architecture_mode",
        ):
            # API调用：执行`object.__setattr__(self, field_name, _require_text(getattr(self, field_name), field_name))`以触发注册、写入对象状态或其他显式副作用。
            # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
            # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
            object.__setattr__(
                self,
                field_name,
                _require_text(getattr(self, field_name), field_name),
            )
        # 条件门禁：判断`self.task_id != 'TASK_020A'`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if self.task_id != "TASK_020A":
            # 错误阻断：抛出`DataContractError('资源档案task_id异常。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError("资源档案task_id异常。")
        # 迭代处理：依次读取`('physical_core_count', 'logical_thread_count', 'memory_gib', 'gpu_memory_gib...`中的元素，并绑定到`field_name`。
        # - 维度变化：每轮处理一个元素，可能向列表、字典或累计值中增加一项。
        # - 为什么这样写：显式逐项校验可以精确指出哪个字段或Provider不符合合同。
        for field_name in (
            "physical_core_count",
            "logical_thread_count",
            "memory_gib",
            "gpu_memory_gib",
            "max_parallel_provider_calls",
            "max_parallel_cpu_jobs",
            "max_parallel_database_queries",
            "default_batch_rows",
            "large_batch_rows",
            "maximum_batch_rows_without_override",
            "maximum_in_memory_result_mib",
            "process_memory_soft_limit_mib",
        ):
            # API调用：执行`object.__setattr__(self, field_name, _positive_int(getattr(self, field_name), field_name))`以触发注册、写入对象状态或其他显式副作用。
            # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
            # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
            object.__setattr__(
                self,
                field_name,
                _positive_int(getattr(self, field_name), field_name),
            )
        # 条件门禁：判断`self.logical_thread_count < self.physical_core_count`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if self.logical_thread_count < self.physical_core_count:
            # 错误阻断：抛出`DataContractError('逻辑线程不能少于物理核心。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError("逻辑线程不能少于物理核心。")
        # 条件门禁：判断`self.max_parallel_provider_calls > 2`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if self.max_parallel_provider_calls > 2:
            # 错误阻断：抛出`DataContractError('当前单机Provider并发不得超过2。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError("当前单机Provider并发不得超过2。")
        # 条件门禁：判断`self.max_parallel_cpu_jobs > 2`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if self.max_parallel_cpu_jobs > 2:
            # 错误阻断：抛出`DataContractError('当前单机CPU并行任务不得超过2。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError("当前单机CPU并行任务不得超过2。")
        # 条件门禁：判断`self.max_parallel_database_queries > 2`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if self.max_parallel_database_queries > 2:
            # 错误阻断：抛出`DataContractError('当前单机数据库并发不得超过2。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError("当前单机数据库并发不得超过2。")
        # 条件门禁：判断`not self.default_batch_rows <= self.large_batch_rows <= self.maximum_batch_rows_without_override`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if not (
            self.default_batch_rows
            <= self.large_batch_rows
            <= self.maximum_batch_rows_without_override
        ):
            # 错误阻断：抛出`DataContractError('批次行数层级异常。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError("批次行数层级异常。")
        # 迭代处理：依次读取`('minimum_free_space_gib', 'temporary_directory_quota_gib', 'cache_quota_gib'...`中的元素，并绑定到`field_name`。
        # - 维度变化：每轮处理一个元素，可能向列表、字典或累计值中增加一项。
        # - 为什么这样写：显式逐项校验可以精确指出哪个字段或Provider不符合合同。
        for field_name in (
            "minimum_free_space_gib",
            "temporary_directory_quota_gib",
            "cache_quota_gib",
            "large_download_threshold_gib",
        ):
            # API调用：执行`object.__setattr__(self, field_name, _nonnegative_number(getattr(self, field_name), field_name))`以触发注册、写入对象状态或其他显式副作用。
            # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
            # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
            object.__setattr__(
                self,
                field_name,
                _nonnegative_number(
                    getattr(self, field_name),
                    field_name,
                ),
            )
        # 条件门禁：判断`self.automatic_35gb_minute_data_import_allowed`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if self.automatic_35gb_minute_data_import_allowed:
            # 错误阻断：抛出`DataContractError('不得自动导入35GB分钟线。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError("不得自动导入35GB分钟线。")
        # 条件门禁：判断`self.gpu_enabled_by_default`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if self.gpu_enabled_by_default:
            # 错误阻断：抛出`DataContractError('GPU不得默认启用。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError("GPU不得默认启用。")
        # 变量更新：计算并保存rules，右侧逻辑为`tuple((_require_text(value, 'hard_rules') for value in self.hard_rules))`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        rules = tuple(
            _require_text(value, "hard_rules")
            for value in self.hard_rules
        )
        # 条件门禁：判断`not rules or len(rules) != len(set(rules))`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if not rules or len(rules) != len(set(rules)):
            # 错误阻断：抛出`DataContractError('hard_rules必须非空且唯一。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError("hard_rules必须非空且唯一。")
        # API调用：执行`object.__setattr__(self, 'hard_rules', rules)`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        object.__setattr__(self, "hard_rules", rules)

    # 执行choose_batch_rows逻辑，把输入参数转换为受合同约束的结果。
    # - 参数requested_rows：类型int | None，默认值None；进入函数后按合同校验或参与计算。
    # - 输出：返回类型int；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
    def choose_batch_rows(
        self,
        requested_rows: int | None = None,
    ) -> int:
        # 条件门禁：判断`requested_rows is None`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if requested_rows is None:
            # 结果返回：把`self.default_batch_rows`交给调用方。
            # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
            # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
            return self.default_batch_rows
        # 变量更新：计算并保存value，右侧逻辑为`_positive_int(requested_rows, 'requested_rows')`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        value = _positive_int(requested_rows, "requested_rows")
        # 条件门禁：判断`value > self.maximum_batch_rows_without_override`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if value > self.maximum_batch_rows_without_override:
            # 错误阻断：抛出`DataContractError('请求批次超过单机无人工覆盖上限。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError(
                "请求批次超过单机无人工覆盖上限。"
            )
        # 结果返回：把`value`交给调用方。
        # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
        # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
        return value

    # 执行assert_storage_safe逻辑，把输入参数转换为受合同约束的结果。
    # - 参数free_space_gib：类型float；进入函数后按合同校验或参与计算。
    # - 参数planned_download_gib：类型float，默认值0；进入函数后按合同校验或参与计算。
    # - 输出：返回类型None；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
    def assert_storage_safe(
        self,
        free_space_gib: float,
        planned_download_gib: float = 0,
    ) -> None:
        # 变量更新：计算并保存free_value，右侧逻辑为`_nonnegative_number(free_space_gib, 'free_space_gib')`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        free_value = _nonnegative_number(
            free_space_gib,
            "free_space_gib",
        )
        # 变量更新：计算并保存planned_value，右侧逻辑为`_nonnegative_number(planned_download_gib, 'planned_download_gib')`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        planned_value = _nonnegative_number(
            planned_download_gib,
            "planned_download_gib",
        )
        # 变量更新：计算并保存remaining，右侧逻辑为`free_value - planned_value`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        remaining = free_value - planned_value
        # 条件门禁：判断`remaining < self.minimum_free_space_gib`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if remaining < self.minimum_free_space_gib:
            # 错误阻断：抛出`DataContractError('计划任务会使磁盘空间低于安全阈值。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError(
                "计划任务会使磁盘空间低于安全阈值。"
            )
        # 条件门禁：判断`planned_value > self.large_download_threshold_gib`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if planned_value > self.large_download_threshold_gib:
            # 错误阻断：抛出`DataContractError('大文件下载必须取得人工覆盖授权。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError(
                "大文件下载必须取得人工覆盖授权。"
            )


# 执行load_provider_capability_matrix逻辑，把输入参数转换为受合同约束的结果。
# - 参数path：类型str | Path；进入函数后按合同校验或参与计算。
# - 输出：返回类型ProviderCapabilityMatrix；调用方按该类型继续校验、路由或序列化。
# - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
# - 为什么这样写：把JSON配置转换成强类型能力矩阵，加载时立即发现配置错误。
def load_provider_capability_matrix(
    path: str | Path,
) -> ProviderCapabilityMatrix:
    # 变量更新：计算并保存raw，右侧逻辑为`json.loads(Path(path).read_text(encoding='utf-8'))`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    # 条件门禁：判断`not isinstance(raw, dict)`，条件为真时进入受保护分支。
    # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
    # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
    if not isinstance(raw, dict):
        # 错误阻断：抛出`DataContractError('能力矩阵根节点必须是对象。')`并停止当前路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
        # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
        raise DataContractError("能力矩阵根节点必须是对象。")
    # 变量更新：计算并保存targets，右侧逻辑为`tuple((ProviderTarget(provider_id=str(item['provider_id']), display_name=str(item['disp...`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    targets = tuple(
        ProviderTarget(
            provider_id=str(item["provider_id"]),
            display_name=str(item["display_name"]),
            provider_kind=str(item["provider_kind"]),
            lifecycle=ProviderLifecycle(str(item["lifecycle"])),
            integration_mode=str(item["integration_mode"]),
            authentication_mode=str(item["authentication_mode"]),
            discovery_status=ProviderDiscoveryStatus(
                str(item["discovery_status"])
            ),
            capabilities={
                str(key): CapabilityImplementationStatus(str(value))
                for key, value in item["capabilities"].items()
            },
            license_review_required=bool(
                item["license_review_required"]
            ),
            execution_capability=bool(
                item["execution_capability"]
            ),
            notes=str(item["notes"]),
        )
        for item in raw["provider_targets"]
    )
    # 结果返回：把`ProviderCapabilityMatrix(task_id=str(raw['task_id']), matrix_version=str(raw['matrix_version']), ...`交给调用方。
    # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
    # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
    return ProviderCapabilityMatrix(
        task_id=str(raw["task_id"]),
        matrix_version=str(raw["matrix_version"]),
        matrix_status=str(raw["matrix_status"]),
        provider_neutral=bool(raw["provider_neutral"]),
        automatic_activation_allowed=bool(
            raw["automatic_activation_allowed"]
        ),
        secret_storage_allowed=bool(raw["secret_storage_allowed"]),
        core_system_may_import_vendor_sdk=bool(
            raw["core_system_may_import_vendor_sdk"]
        ),
        upper_layers_may_depend_on_vendor_fields=bool(
            raw["upper_layers_may_depend_on_vendor_fields"]
        ),
        required_adapter_contracts=tuple(
            str(value) for value in raw["required_adapter_contracts"]
        ),
        capability_catalog=tuple(
            str(value) for value in raw["capability_catalog"]
        ),
        provider_targets=targets,
        routing_rules=tuple(
            str(value) for value in raw["routing_rules"]
        ),
    )


# 执行load_single_machine_resource_profile逻辑，把输入参数转换为受合同约束的结果。
# - 参数path：类型str | Path；进入函数后按合同校验或参与计算。
# - 输出：返回类型SingleMachineResourceProfile；调用方按该类型继续校验、路由或序列化。
# - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
# - 为什么这样写：把单机资源JSON转换为受约束对象，确保批次与磁盘门禁一致。
def load_single_machine_resource_profile(
    path: str | Path,
) -> SingleMachineResourceProfile:
    # 变量更新：计算并保存raw，右侧逻辑为`json.loads(Path(path).read_text(encoding='utf-8'))`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    # 条件门禁：判断`not isinstance(raw, dict)`，条件为真时进入受保护分支。
    # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
    # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
    if not isinstance(raw, dict):
        # 错误阻断：抛出`DataContractError('资源档案根节点必须是对象。')`并停止当前路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
        # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
        raise DataContractError("资源档案根节点必须是对象。")
    # 变量更新：计算并保存machine，右侧逻辑为`raw['machine']`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    machine = raw["machine"]
    # 变量更新：计算并保存execution，右侧逻辑为`raw['default_execution']`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    execution = raw["default_execution"]
    # 变量更新：计算并保存storage，右侧逻辑为`raw['storage_safety']`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    storage = raw["storage_safety"]
    # 变量更新：计算并保存gpu，右侧逻辑为`raw['gpu_policy']`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    gpu = raw["gpu_policy"]
    # 结果返回：把`SingleMachineResourceProfile(task_id=str(raw['task_id']), profile_version=str(raw['profile_versio...`交给调用方。
    # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
    # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
    return SingleMachineResourceProfile(
        task_id=str(raw["task_id"]),
        profile_version=str(raw["profile_version"]),
        profile_status=str(raw["profile_status"]),
        profile_id=str(raw["profile_id"]),
        operating_system=str(machine["operating_system"]),
        physical_core_count=int(machine["physical_core_count"]),
        logical_thread_count=int(machine["logical_thread_count"]),
        memory_gib=int(machine["memory_gib"]),
        gpu_memory_gib=int(machine["gpu_memory_gib"]),
        architecture_mode=str(raw["architecture_mode"]),
        max_parallel_provider_calls=int(
            execution["max_parallel_provider_calls"]
        ),
        max_parallel_cpu_jobs=int(
            execution["max_parallel_cpu_jobs"]
        ),
        max_parallel_database_queries=int(
            execution["max_parallel_database_queries"]
        ),
        default_batch_rows=int(execution["default_batch_rows"]),
        large_batch_rows=int(execution["large_batch_rows"]),
        maximum_batch_rows_without_override=int(
            execution["maximum_batch_rows_without_override"]
        ),
        maximum_in_memory_result_mib=int(
            execution["maximum_in_memory_result_mib"]
        ),
        process_memory_soft_limit_mib=int(
            execution["process_memory_soft_limit_mib"]
        ),
        minimum_free_space_gib=float(
            storage["minimum_free_space_gib"]
        ),
        temporary_directory_quota_gib=float(
            storage["temporary_directory_quota_gib"]
        ),
        cache_quota_gib=float(storage["cache_quota_gib"]),
        large_download_threshold_gib=float(
            storage["large_download_threshold_gib"]
        ),
        automatic_35gb_minute_data_import_allowed=bool(
            storage[
                "automatic_35gb_minute_data_import_allowed"
            ]
        ),
        gpu_enabled_by_default=bool(gpu["enabled_by_default"]),
        hard_rules=tuple(str(value) for value in raw["hard_rules"]),
    )
