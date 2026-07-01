# 模块总览：复用优先开发政策和可审计决策合同。
# - 输入输出：本模块通过强类型对象和纯函数交换数据，不在导入阶段执行隐式网络或数据库写入。
# - 数据变化：只有显式构造、校验、加载或方法调用才会产生新对象或更新受控状态。
# - 为什么这样写：先说明模块边界，读者可以在阅读实现前理解职责、风险和复用方式。
"""复用优先开发政策和可审计决策合同。"""
# 依赖导入：加载标准库、类型工具和项目内合同，供下方数据结构与校验逻辑复用。
# - 标准库只提供解析、数学、时间、路径和类型能力；项目模块提供统一异常与上游合同。
# - 为什么这样写：集中导入让依赖边界清晰，并避免在函数内部重复加载同一模块。
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Iterable, Mapping

from .data_contracts import DataContractError


# 定义复用候选是项目已有组件、官方SDK、标准、开源库或自研。
# - 状态成员：枚举值或方法共同描述该合同允许的有限状态和行为。
# - 数据变化：类本身不执行隐式I/O，实例字段只在显式构造、校验或方法调用时变化。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
class ReuseCandidateType(str, Enum):
    # 变量更新：计算并保存EXISTING_PROJECT_COMPONENT，右侧逻辑为`'EXISTING_PROJECT_COMPONENT'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    EXISTING_PROJECT_COMPONENT = "EXISTING_PROJECT_COMPONENT"
    # 变量更新：计算并保存OFFICIAL_VENDOR_SDK，右侧逻辑为`'OFFICIAL_VENDOR_SDK'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    OFFICIAL_VENDOR_SDK = "OFFICIAL_VENDOR_SDK"
    # 变量更新：计算并保存OPEN_STANDARD_PROTOCOL，右侧逻辑为`'OPEN_STANDARD_PROTOCOL'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    OPEN_STANDARD_PROTOCOL = "OPEN_STANDARD_PROTOCOL"
    # 变量更新：计算并保存MATURE_OPEN_SOURCE_LIBRARY，右侧逻辑为`'MATURE_OPEN_SOURCE_LIBRARY'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    MATURE_OPEN_SOURCE_LIBRARY = "MATURE_OPEN_SOURCE_LIBRARY"
    # 变量更新：计算并保存REFERENCE_IMPLEMENTATION，右侧逻辑为`'REFERENCE_IMPLEMENTATION'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    REFERENCE_IMPLEMENTATION = "REFERENCE_IMPLEMENTATION"
    # 变量更新：计算并保存THIN_ADAPTER_OR_BRIDGE，右侧逻辑为`'THIN_ADAPTER_OR_BRIDGE'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    THIN_ADAPTER_OR_BRIDGE = "THIN_ADAPTER_OR_BRIDGE"
    # 变量更新：计算并保存CUSTOM_IMPLEMENTATION，右侧逻辑为`'CUSTOM_IMPLEMENTATION'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    CUSTOM_IMPLEMENTATION = "CUSTOM_IMPLEMENTATION"


# 定义复用评审最终采用、薄适配、扩展、延期、自研或拒绝。
# - 状态成员：枚举值或方法共同描述该合同允许的有限状态和行为。
# - 数据变化：类本身不执行隐式I/O，实例字段只在显式构造、校验或方法调用时变化。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
class ReuseDecisionType(str, Enum):
    # 变量更新：计算并保存REUSE_AS_IS，右侧逻辑为`'REUSE_AS_IS'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    REUSE_AS_IS = "REUSE_AS_IS"
    # 变量更新：计算并保存WRAP_WITH_THIN_ADAPTER，右侧逻辑为`'WRAP_WITH_THIN_ADAPTER'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    WRAP_WITH_THIN_ADAPTER = "WRAP_WITH_THIN_ADAPTER"
    # 变量更新：计算并保存EXTEND_EXISTING_COMPONENT，右侧逻辑为`'EXTEND_EXISTING_COMPONENT'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    EXTEND_EXISTING_COMPONENT = "EXTEND_EXISTING_COMPONENT"
    # 变量更新：计算并保存DEFER_PENDING_DISCOVERY，右侧逻辑为`'DEFER_PENDING_DISCOVERY'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    DEFER_PENDING_DISCOVERY = "DEFER_PENDING_DISCOVERY"
    # 变量更新：计算并保存CUSTOM_BUILD_APPROVED，右侧逻辑为`'CUSTOM_BUILD_APPROVED'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    CUSTOM_BUILD_APPROVED = "CUSTOM_BUILD_APPROVED"
    # 变量更新：计算并保存REJECT，右侧逻辑为`'REJECT'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    REJECT = "REJECT"


# 定义许可证、安全、维护和兼容评审状态。
# - 状态成员：枚举值或方法共同描述该合同允许的有限状态和行为。
# - 数据变化：类本身不执行隐式I/O，实例字段只在显式构造、校验或方法调用时变化。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
class ReviewStatus(str, Enum):
    # 变量更新：计算并保存NOT_REVIEWED，右侧逻辑为`'NOT_REVIEWED'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    NOT_REVIEWED = "NOT_REVIEWED"
    # 变量更新：计算并保存PASSED，右侧逻辑为`'PASSED'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    PASSED = "PASSED"
    # 变量更新：计算并保存PASSED_WITH_WARNINGS，右侧逻辑为`'PASSED_WITH_WARNINGS'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    PASSED_WITH_WARNINGS = "PASSED_WITH_WARNINGS"
    # 变量更新：计算并保存BLOCKED，右侧逻辑为`'BLOCKED'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    BLOCKED = "BLOCKED"


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


# 执行_optional_text逻辑，把输入参数转换为受合同约束的结果。
# - 参数value：类型Any；进入函数后按合同校验或参与计算。
# - 参数field_name：类型str；进入函数后按合同校验或参与计算。
# - 输出：返回类型str | None；调用方按该类型继续校验、路由或序列化。
# - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
# - 为什么这样写：把可选文本的空值与有效文本分开处理，减少每个数据类重复编写校验分支。
def _optional_text(value: Any, field_name: str) -> str | None:
    # 条件门禁：判断`value is None`，条件为真时进入受保护分支。
    # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
    # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
    if value is None:
        # 结果返回：把`None`交给调用方。
        # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
        # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
        return None
    # 结果返回：把`_require_text(value, field_name)`交给调用方。
    # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
    # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
    return _require_text(value, field_name)


# 执行_unique_texts逻辑，把输入参数转换为受合同约束的结果。
# - 参数values：类型Iterable[Any]；进入函数后按合同校验或参与计算。
# - 参数field_name：类型str；进入函数后按合同校验或参与计算。
# - 关键字参数allow_empty：类型bool，默认值True；用于控制本次调用行为。
# - 输出：返回类型tuple[str, ...]；调用方按该类型继续校验、路由或序列化。
# - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
# - 为什么这样写：把列表标准化为不可变且无重复的元组，保证配置比较和序列化结果稳定。
def _unique_texts(
    values: Iterable[Any],
    field_name: str,
    *,
    allow_empty: bool = True,
) -> tuple[str, ...]:
    # 变量更新：计算并保存result，右侧逻辑为`tuple((_require_text(value, field_name) for value in values))`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    result = tuple(_require_text(value, field_name) for value in values)
    # 条件门禁：判断`not allow_empty and (not result)`，条件为真时进入受保护分支。
    # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
    # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
    if not allow_empty and not result:
        # 错误阻断：抛出`DataContractError(f'{field_name}不能为空。')`并停止当前路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
        # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
        raise DataContractError(f"{field_name}不能为空。")
    # 条件门禁：判断`len(result) != len(set(result))`，条件为真时进入受保护分支。
    # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
    # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
    if len(result) != len(set(result)):
        # 错误阻断：抛出`DataContractError(f'{field_name}不允许重复。')`并停止当前路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
        # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
        raise DataContractError(f"{field_name}不允许重复。")
    # 结果返回：把`result`交给调用方。
    # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
    # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
    return result


# 定义ReuseCandidateAssessment强类型合同，集中保存相关状态、参数和校验规则。
# - 字段candidate_id：类型str。
# - 字段candidate_type：类型ReuseCandidateType。
# - 字段name：类型str。
# - 字段source_ref：类型str。
# - 字段version：类型str | None。
# - 字段license_id：类型str | None。
# - 字段license_status：类型ReviewStatus。
# - 字段security_status：类型ReviewStatus。
# - 其余字段：另有7项，均在对象创建时统一校验。
# - 数据变化：类本身不执行隐式I/O，实例字段只在显式构造、校验或方法调用时变化。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
@dataclass(frozen=True, slots=True)
class ReuseCandidateAssessment:
    # 变量更新：计算并保存candidate_id，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    candidate_id: str
    # 变量更新：计算并保存candidate_type，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    candidate_type: ReuseCandidateType
    # 变量更新：计算并保存name，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    name: str
    # 变量更新：计算并保存source_ref，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    source_ref: str
    # 变量更新：计算并保存version，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    version: str | None
    # 变量更新：计算并保存license_id，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    license_id: str | None
    # 变量更新：计算并保存license_status，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    license_status: ReviewStatus
    # 变量更新：计算并保存security_status，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    security_status: ReviewStatus
    # 变量更新：计算并保存maintenance_status，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    maintenance_status: ReviewStatus
    # 变量更新：计算并保存compatibility_status，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    compatibility_status: ReviewStatus
    # 变量更新：计算并保存semantic_gap_status，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    semantic_gap_status: ReviewStatus
    # 变量更新：计算并保存supported_requirements，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    supported_requirements: tuple[str, ...]
    # 变量更新：计算并保存gaps，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    gaps: tuple[str, ...]
    # 变量更新：计算并保存warnings，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    warnings: tuple[str, ...]
    # 变量更新：计算并保存evidence_refs，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    evidence_refs: tuple[str, ...]

    # 执行__post_init__逻辑，把输入参数转换为受合同约束的结果。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态或模块常量。
    # - 输出：返回类型None；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：在不可变或数据类对象创建后立即校验字段关系，阻止不一致对象进入系统。
    def __post_init__(self) -> None:
        # 迭代处理：依次读取`('candidate_id', 'name', 'source_ref')`中的元素，并绑定到`field_name`。
        # - 维度变化：每轮处理一个元素，可能向列表、字典或累计值中增加一项。
        # - 为什么这样写：显式逐项校验可以精确指出哪个字段或Provider不符合合同。
        for field_name in (
            "candidate_id",
            "name",
            "source_ref",
        ):
            # API调用：执行`object.__setattr__(self, field_name, _require_text(getattr(self, field_name), field_name))`以触发注册、写入对象状态或其他显式副作用。
            # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
            # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
            object.__setattr__(
                self,
                field_name,
                _require_text(getattr(self, field_name), field_name),
            )
        # 变量更新：计算并保存candidate_type，右侧逻辑为`self.candidate_type`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        candidate_type = self.candidate_type
        # 条件门禁：判断`isinstance(candidate_type, str)`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if isinstance(candidate_type, str):
            # 变量更新：计算并保存candidate_type，右侧逻辑为`ReuseCandidateType(candidate_type)`。
            # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
            # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
            candidate_type = ReuseCandidateType(candidate_type)
        # API调用：执行`object.__setattr__(self, 'candidate_type', candidate_type)`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        object.__setattr__(self, "candidate_type", candidate_type)
        # 迭代处理：依次读取`('version', 'license_id')`中的元素，并绑定到`field_name`。
        # - 维度变化：每轮处理一个元素，可能向列表、字典或累计值中增加一项。
        # - 为什么这样写：显式逐项校验可以精确指出哪个字段或Provider不符合合同。
        for field_name in ("version", "license_id"):
            # API调用：执行`object.__setattr__(self, field_name, _optional_text(getattr(self, field_name), field_name))`以触发注册、写入对象状态或其他显式副作用。
            # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
            # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
            object.__setattr__(
                self,
                field_name,
                _optional_text(getattr(self, field_name), field_name),
            )
        # 迭代处理：依次读取`('license_status', 'security_status', 'maintenance_status', 'compatibility_st...`中的元素，并绑定到`field_name`。
        # - 维度变化：每轮处理一个元素，可能向列表、字典或累计值中增加一项。
        # - 为什么这样写：显式逐项校验可以精确指出哪个字段或Provider不符合合同。
        for field_name in (
            "license_status",
            "security_status",
            "maintenance_status",
            "compatibility_status",
            "semantic_gap_status",
        ):
            # 变量更新：计算并保存value，右侧逻辑为`getattr(self, field_name)`。
            # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
            # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
            value = getattr(self, field_name)
            # 条件门禁：判断`isinstance(value, str)`，条件为真时进入受保护分支。
            # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
            # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
            if isinstance(value, str):
                # 变量更新：计算并保存value，右侧逻辑为`ReviewStatus(value)`。
                # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
                # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
                value = ReviewStatus(value)
            # API调用：执行`object.__setattr__(self, field_name, value)`以触发注册、写入对象状态或其他显式副作用。
            # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
            # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
            object.__setattr__(self, field_name, value)
        # 迭代处理：依次读取`('supported_requirements', 'gaps', 'warnings', 'evidence_refs')`中的元素，并绑定到`field_name`。
        # - 维度变化：每轮处理一个元素，可能向列表、字典或累计值中增加一项。
        # - 为什么这样写：显式逐项校验可以精确指出哪个字段或Provider不符合合同。
        for field_name in (
            "supported_requirements",
            "gaps",
            "warnings",
            "evidence_refs",
        ):
            # API调用：执行`object.__setattr__(self, field_name, _unique_texts(getattr(self, field_name), field_name))`以触发注册、写入对象状态或其他显式副作用。
            # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
            # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
            object.__setattr__(
                self,
                field_name,
                _unique_texts(
                    getattr(self, field_name),
                    field_name,
                ),
            )
        # 条件门禁：判断`self.license_status in {ReviewStatus.PASSED, ReviewStatus.PASSED_WITH_WARNINGS} and self.license_...`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if self.license_status in {
            ReviewStatus.PASSED,
            ReviewStatus.PASSED_WITH_WARNINGS,
        } and self.license_id is None:
            # 错误阻断：抛出`DataContractError('许可证通过时必须记录license_id。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError(
                "许可证通过时必须记录license_id。"
            )
        # 条件门禁：判断`self.candidate_type is not ReuseCandidateType.CUSTOM_IMPLEMENTATION`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if self.candidate_type is not ReuseCandidateType.CUSTOM_IMPLEMENTATION:
            # 条件门禁：判断`not self.evidence_refs`，条件为真时进入受保护分支。
            # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
            # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
            if not self.evidence_refs:
                # 错误阻断：抛出`DataContractError('复用候选必须包含证据引用。')`并停止当前路径。
                # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
                # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
                raise DataContractError(
                    "复用候选必须包含证据引用。"
                )

    # 执行blocked逻辑，把输入参数转换为受合同约束的结果。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态或模块常量。
    # - 输出：返回类型bool；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
    @property
    def blocked(self) -> bool:
        # 结果返回：把`any((status is ReviewStatus.BLOCKED for status in (self.license_status, self.security_status, sel...`交给调用方。
        # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
        # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
        return any(
            status is ReviewStatus.BLOCKED
            for status in (
                self.license_status,
                self.security_status,
                self.maintenance_status,
                self.compatibility_status,
                self.semantic_gap_status,
            )
        )

    # 执行reusable逻辑，把输入参数转换为受合同约束的结果。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态或模块常量。
    # - 输出：返回类型bool；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
    @property
    def reusable(self) -> bool:
        # 变量更新：计算并保存accepted，右侧逻辑为`{ReviewStatus.PASSED, ReviewStatus.PASSED_WITH_WARNINGS}`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        accepted = {
            ReviewStatus.PASSED,
            ReviewStatus.PASSED_WITH_WARNINGS,
        }
        # 结果返回：把`not self.blocked and self.license_status in accepted and (self.security_status in accepted) and (...`交给调用方。
        # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
        # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
        return (
            not self.blocked
            and self.license_status in accepted
            and self.security_status in accepted
            and self.maintenance_status in accepted
            and self.compatibility_status in accepted
            and self.semantic_gap_status in accepted
        )


# 定义ReuseDecisionRecord强类型合同，集中保存相关状态、参数和校验规则。
# - 字段decision_id：类型str。
# - 字段problem_statement：类型str。
# - 字段requirements：类型tuple[str, ...]。
# - 字段candidates：类型tuple[ReuseCandidateAssessment, ...]。
# - 字段decision：类型ReuseDecisionType。
# - 字段selected_candidate_id：类型str | None。
# - 字段rationale：类型str。
# - 字段custom_build_evidence：类型Mapping[str, str]。
# - 其余字段：另有4项，均在对象创建时统一校验。
# - 数据变化：类本身不执行隐式I/O，实例字段只在显式构造、校验或方法调用时变化。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
@dataclass(frozen=True, slots=True)
class ReuseDecisionRecord:
    # 变量更新：计算并保存decision_id，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    decision_id: str
    # 变量更新：计算并保存problem_statement，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    problem_statement: str
    # 变量更新：计算并保存requirements，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    requirements: tuple[str, ...]
    # 变量更新：计算并保存candidates，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    candidates: tuple[ReuseCandidateAssessment, ...]
    # 变量更新：计算并保存decision，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    decision: ReuseDecisionType
    # 变量更新：计算并保存selected_candidate_id，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    selected_candidate_id: str | None
    # 变量更新：计算并保存rationale，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    rationale: str
    # 变量更新：计算并保存custom_build_evidence，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    custom_build_evidence: Mapping[str, str]
    # 变量更新：计算并保存maintenance_owner，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    maintenance_owner: str | None
    # 变量更新：计算并保存test_plan_ref，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    test_plan_ref: str | None
    # 变量更新：计算并保存migration_path，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    migration_path: str | None
    # 变量更新：计算并保存evidence_refs，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    evidence_refs: tuple[str, ...]

    # 执行__post_init__逻辑，把输入参数转换为受合同约束的结果。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态或模块常量。
    # - 输出：返回类型None；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：在不可变或数据类对象创建后立即校验字段关系，阻止不一致对象进入系统。
    def __post_init__(self) -> None:
        # 迭代处理：依次读取`('decision_id', 'problem_statement', 'rationale')`中的元素，并绑定到`field_name`。
        # - 维度变化：每轮处理一个元素，可能向列表、字典或累计值中增加一项。
        # - 为什么这样写：显式逐项校验可以精确指出哪个字段或Provider不符合合同。
        for field_name in (
            "decision_id",
            "problem_statement",
            "rationale",
        ):
            # API调用：执行`object.__setattr__(self, field_name, _require_text(getattr(self, field_name), field_name))`以触发注册、写入对象状态或其他显式副作用。
            # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
            # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
            object.__setattr__(
                self,
                field_name,
                _require_text(getattr(self, field_name), field_name),
            )
        # API调用：执行`object.__setattr__(self, 'requirements', _unique_texts(self.requirements, 'requirements', allow_e...`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        object.__setattr__(
            self,
            "requirements",
            _unique_texts(
                self.requirements,
                "requirements",
                allow_empty=False,
            ),
        )
        # 条件门禁：判断`not self.candidates`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if not self.candidates:
            # 错误阻断：抛出`DataContractError('至少需要一个候选方案。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError("至少需要一个候选方案。")
        # 变量更新：计算并保存candidate_ids，右侧逻辑为`[item.candidate_id for item in self.candidates]`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        candidate_ids = [item.candidate_id for item in self.candidates]
        # 条件门禁：判断`len(candidate_ids) != len(set(candidate_ids))`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if len(candidate_ids) != len(set(candidate_ids)):
            # 错误阻断：抛出`DataContractError('candidate_id不允许重复。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError("candidate_id不允许重复。")
        # 变量更新：计算并保存decision，右侧逻辑为`self.decision`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        decision = self.decision
        # 条件门禁：判断`isinstance(decision, str)`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if isinstance(decision, str):
            # 变量更新：计算并保存decision，右侧逻辑为`ReuseDecisionType(decision)`。
            # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
            # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
            decision = ReuseDecisionType(decision)
        # API调用：执行`object.__setattr__(self, 'decision', decision)`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        object.__setattr__(self, "decision", decision)
        # 变量更新：计算并保存selected，右侧逻辑为`_optional_text(self.selected_candidate_id, 'selected_candidate_id')`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        selected = _optional_text(
            self.selected_candidate_id,
            "selected_candidate_id",
        )
        # API调用：执行`object.__setattr__(self, 'selected_candidate_id', selected)`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        object.__setattr__(self, "selected_candidate_id", selected)
        # API调用：执行`object.__setattr__(self, 'maintenance_owner', _optional_text(self.maintenance_owner, 'maintenance...`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        object.__setattr__(
            self,
            "maintenance_owner",
            _optional_text(self.maintenance_owner, "maintenance_owner"),
        )
        # API调用：执行`object.__setattr__(self, 'test_plan_ref', _optional_text(self.test_plan_ref, 'test_plan_ref'))`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        object.__setattr__(
            self,
            "test_plan_ref",
            _optional_text(self.test_plan_ref, "test_plan_ref"),
        )
        # API调用：执行`object.__setattr__(self, 'migration_path', _optional_text(self.migration_path, 'migration_path'))`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        object.__setattr__(
            self,
            "migration_path",
            _optional_text(self.migration_path, "migration_path"),
        )
        # API调用：执行`object.__setattr__(self, 'evidence_refs', _unique_texts(self.evidence_refs, 'evidence_refs', allo...`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        object.__setattr__(
            self,
            "evidence_refs",
            _unique_texts(
                self.evidence_refs,
                "evidence_refs",
                allow_empty=False,
            ),
        )
        # 变量更新：计算并保存custom_evidence，右侧逻辑为`{_require_text(key, 'custom_build_evidence_key'): _require_text(value, 'custom_build_ev...`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        custom_evidence = {
            _require_text(key, "custom_build_evidence_key"): _require_text(
                value,
                "custom_build_evidence_value",
            )
            for key, value in self.custom_build_evidence.items()
        }
        # API调用：执行`object.__setattr__(self, 'custom_build_evidence', custom_evidence)`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        object.__setattr__(
            self,
            "custom_build_evidence",
            custom_evidence,
        )

        # 变量更新：计算并保存selected_candidate，右侧逻辑为`None`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        selected_candidate = None
        # 条件门禁：判断`selected is not None`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if selected is not None:
            # 迭代处理：依次读取`self.candidates`中的元素，并绑定到`item`。
            # - 维度变化：每轮处理一个元素，可能向列表、字典或累计值中增加一项。
            # - 为什么这样写：显式逐项校验可以精确指出哪个字段或Provider不符合合同。
            for item in self.candidates:
                # 条件门禁：判断`item.candidate_id == selected`，条件为真时进入受保护分支。
                # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
                # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
                if item.candidate_id == selected:
                    # 变量更新：计算并保存selected_candidate，右侧逻辑为`item`。
                    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
                    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
                    selected_candidate = item
                    break
            # 条件门禁：判断`selected_candidate is None`，条件为真时进入受保护分支。
            # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
            # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
            if selected_candidate is None:
                # 错误阻断：抛出`DataContractError('selected_candidate_id不存在。')`并停止当前路径。
                # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
                # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
                raise DataContractError("selected_candidate_id不存在。")

        # 变量更新：计算并保存selection_decisions，右侧逻辑为`{ReuseDecisionType.REUSE_AS_IS, ReuseDecisionType.WRAP_WITH_THIN_ADAPTER, ReuseDecision...`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        selection_decisions = {
            ReuseDecisionType.REUSE_AS_IS,
            ReuseDecisionType.WRAP_WITH_THIN_ADAPTER,
            ReuseDecisionType.EXTEND_EXISTING_COMPONENT,
            ReuseDecisionType.CUSTOM_BUILD_APPROVED,
        }
        # 条件门禁：判断`decision in selection_decisions and selected_candidate is None`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if decision in selection_decisions and selected_candidate is None:
            # 错误阻断：抛出`DataContractError('该决策必须选择候选方案。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError("该决策必须选择候选方案。")

        # 条件门禁：判断`decision in {ReuseDecisionType.REUSE_AS_IS, ReuseDecisionType.WRAP_WITH_THIN_ADAPTER, ReuseDecisi...`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if decision in {
            ReuseDecisionType.REUSE_AS_IS,
            ReuseDecisionType.WRAP_WITH_THIN_ADAPTER,
            ReuseDecisionType.EXTEND_EXISTING_COMPONENT,
        }:
            # 条件门禁：判断`selected_candidate is None or not selected_candidate.reusable`，条件为真时进入受保护分支。
            # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
            # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
            if selected_candidate is None or not selected_candidate.reusable:
                # 错误阻断：抛出`DataContractError('选中的复用候选未通过评审。')`并停止当前路径。
                # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
                # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
                raise DataContractError("选中的复用候选未通过评审。")
            # 条件门禁：判断`selected_candidate.candidate_type is ReuseCandidateType.CUSTOM_IMPLEMENTATION`，条件为真时进入受保护分支。
            # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
            # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
            if (
                selected_candidate.candidate_type
                is ReuseCandidateType.CUSTOM_IMPLEMENTATION
            ):
                # 错误阻断：抛出`DataContractError('复用决策不能选择自研候选。')`并停止当前路径。
                # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
                # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
                raise DataContractError("复用决策不能选择自研候选。")

        # 条件门禁：判断`decision is ReuseDecisionType.CUSTOM_BUILD_APPROVED`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if decision is ReuseDecisionType.CUSTOM_BUILD_APPROVED:
            # 条件门禁：判断`selected_candidate is None or selected_candidate.candidate_type is not ReuseCandidateType.CUSTOM_...`，条件为真时进入受保护分支。
            # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
            # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
            if (
                selected_candidate is None
                or selected_candidate.candidate_type
                is not ReuseCandidateType.CUSTOM_IMPLEMENTATION
            ):
                # 错误阻断：抛出`DataContractError('自研批准必须选择CUSTOM_IMPLEMENTATION。')`并停止当前路径。
                # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
                # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
                raise DataContractError(
                    "自研批准必须选择CUSTOM_IMPLEMENTATION。"
                )
            # 变量更新：计算并保存required_keys，右侧逻辑为`{'documented_functional_gap', 'documented_candidate_comparison', 'documented_license_or...`。
            # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
            # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
            required_keys = {
                "documented_functional_gap",
                "documented_candidate_comparison",
                "documented_license_or_security_blocker",
                "documented_maintenance_owner",
                "documented_test_plan",
                "documented_migration_or_replacement_path",
            }
            # 条件门禁：判断`set(custom_evidence) != required_keys`，条件为真时进入受保护分支。
            # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
            # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
            if set(custom_evidence) != required_keys:
                # 错误阻断：抛出`DataContractError('自研证据集合不完整。')`并停止当前路径。
                # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
                # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
                raise DataContractError("自研证据集合不完整。")
            # 条件门禁：判断`not all((self.maintenance_owner, self.test_plan_ref, self.migration_path))`，条件为真时进入受保护分支。
            # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
            # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
            if not all(
                (
                    self.maintenance_owner,
                    self.test_plan_ref,
                    self.migration_path,
                )
            ):
                # 错误阻断：抛出`DataContractError('自研批准必须记录维护、测试和迁移信息。')`并停止当前路径。
                # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
                # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
                raise DataContractError(
                    "自研批准必须记录维护、测试和迁移信息。"
                )

    # 执行to_dict逻辑，把输入参数转换为受合同约束的结果。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态或模块常量。
    # - 输出：返回类型dict[str, Any]；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：把强类型对象转换为JSON安全字典，便于报告、审计和持久化。
    def to_dict(self) -> dict[str, Any]:
        # 执行convert逻辑，把输入参数转换为受合同约束的结果。
        # - 参数value：类型Any；进入函数后按合同校验或参与计算。
        # - 输出：返回类型Any；调用方按该类型继续校验、路由或序列化。
        # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
        # - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
        def convert(value: Any) -> Any:
            # 条件门禁：判断`isinstance(value, Enum)`，条件为真时进入受保护分支。
            # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
            # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
            if isinstance(value, Enum):
                # 结果返回：把`value.value`交给调用方。
                # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
                # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
                return value.value
            # 条件门禁：判断`isinstance(value, tuple)`，条件为真时进入受保护分支。
            # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
            # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
            if isinstance(value, tuple):
                # 结果返回：把`[convert(item) for item in value]`交给调用方。
                # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
                # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
                return [convert(item) for item in value]
            # 条件门禁：判断`isinstance(value, list)`，条件为真时进入受保护分支。
            # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
            # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
            if isinstance(value, list):
                # 结果返回：把`[convert(item) for item in value]`交给调用方。
                # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
                # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
                return [convert(item) for item in value]
            # 条件门禁：判断`isinstance(value, Mapping)`，条件为真时进入受保护分支。
            # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
            # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
            if isinstance(value, Mapping):
                # 结果返回：把`{str(key): convert(item) for key, item in value.items()}`交给调用方。
                # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
                # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
                return {
                    str(key): convert(item)
                    for key, item in value.items()
                }
            # 结果返回：把`value`交给调用方。
            # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
            # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
            return value
        # 结果返回：把`convert(asdict(self))`交给调用方。
        # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
        # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
        return convert(asdict(self))


# 定义ReuseFirstPolicy强类型合同，集中保存相关状态、参数和校验规则。
# - 字段task_id：类型str。
# - 字段policy_version：类型str。
# - 字段policy_status：类型str。
# - 字段principle：类型str。
# - 字段custom_implementation_default_allowed：类型bool。
# - 字段unknown_license_reuse_allowed：类型bool。
# - 字段copy_without_provenance_allowed：类型bool。
# - 字段vendor_sdk_reimplementation_allowed：类型bool。
# - 其余字段：另有5项，均在对象创建时统一校验。
# - 数据变化：类本身不执行隐式I/O，实例字段只在显式构造、校验或方法调用时变化。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
@dataclass(frozen=True, slots=True)
class ReuseFirstPolicy:
    # 变量更新：计算并保存task_id，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    task_id: str
    # 变量更新：计算并保存policy_version，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    policy_version: str
    # 变量更新：计算并保存policy_status，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    policy_status: str
    # 变量更新：计算并保存principle，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    principle: str
    # 变量更新：计算并保存custom_implementation_default_allowed，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    custom_implementation_default_allowed: bool
    # 变量更新：计算并保存unknown_license_reuse_allowed，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    unknown_license_reuse_allowed: bool
    # 变量更新：计算并保存copy_without_provenance_allowed，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    copy_without_provenance_allowed: bool
    # 变量更新：计算并保存vendor_sdk_reimplementation_allowed，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    vendor_sdk_reimplementation_allowed: bool
    # 变量更新：计算并保存reuse_order，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    reuse_order: tuple[str, ...]
    # 变量更新：计算并保存required_assessment_sections，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    required_assessment_sections: tuple[str, ...]
    # 变量更新：计算并保存required_custom_build_evidence，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    required_custom_build_evidence: tuple[str, ...]
    # 变量更新：计算并保存adapter_specific_rules，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    adapter_specific_rules: tuple[str, ...]
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
        # 迭代处理：依次读取`('task_id', 'policy_version', 'policy_status', 'principle')`中的元素，并绑定到`field_name`。
        # - 维度变化：每轮处理一个元素，可能向列表、字典或累计值中增加一项。
        # - 为什么这样写：显式逐项校验可以精确指出哪个字段或Provider不符合合同。
        for field_name in (
            "task_id",
            "policy_version",
            "policy_status",
            "principle",
        ):
            # API调用：执行`object.__setattr__(self, field_name, _require_text(getattr(self, field_name), field_name))`以触发注册、写入对象状态或其他显式副作用。
            # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
            # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
            object.__setattr__(
                self,
                field_name,
                _require_text(getattr(self, field_name), field_name),
            )
        # 条件门禁：判断`self.task_id != 'TASK_020B_REUSE'`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if self.task_id != "TASK_020B_REUSE":
            # 错误阻断：抛出`DataContractError('复用政策task_id异常。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError("复用政策task_id异常。")
        # 条件门禁：判断`self.principle != 'REUSE_FIRST_CUSTOM_BUILD_LAST'`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if self.principle != "REUSE_FIRST_CUSTOM_BUILD_LAST":
            # 错误阻断：抛出`DataContractError('复用政策原则异常。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError("复用政策原则异常。")
        # 条件门禁：判断`any((self.custom_implementation_default_allowed, self.unknown_license_reuse_allowed, self.copy_wi...`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if any(
            (
                self.custom_implementation_default_allowed,
                self.unknown_license_reuse_allowed,
                self.copy_without_provenance_allowed,
                self.vendor_sdk_reimplementation_allowed,
            )
        ):
            # 错误阻断：抛出`DataContractError('复用优先硬约束被破坏。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError("复用优先硬约束被破坏。")
        # 迭代处理：依次读取`('reuse_order', 'required_assessment_sections', 'required_custom_build_eviden...`中的元素，并绑定到`field_name`。
        # - 维度变化：每轮处理一个元素，可能向列表、字典或累计值中增加一项。
        # - 为什么这样写：显式逐项校验可以精确指出哪个字段或Provider不符合合同。
        for field_name in (
            "reuse_order",
            "required_assessment_sections",
            "required_custom_build_evidence",
            "adapter_specific_rules",
            "hard_rules",
        ):
            # API调用：执行`object.__setattr__(self, field_name, _unique_texts(getattr(self, field_name), field_name, allow_e...`以触发注册、写入对象状态或其他显式副作用。
            # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
            # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
            object.__setattr__(
                self,
                field_name,
                _unique_texts(
                    getattr(self, field_name),
                    field_name,
                    allow_empty=False,
                ),
            )
        # 条件门禁：判断`self.reuse_order[-1] != 'CUSTOM_IMPLEMENTATION_LAST_RESORT'`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if self.reuse_order[-1] != "CUSTOM_IMPLEMENTATION_LAST_RESORT":
            # 错误阻断：抛出`DataContractError('自研必须位于复用顺序最后。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError("自研必须位于复用顺序最后。")


# 执行load_reuse_first_policy逻辑，把输入参数转换为受合同约束的结果。
# - 参数path：类型str | Path；进入函数后按合同校验或参与计算。
# - 输出：返回类型ReuseFirstPolicy；调用方按该类型继续校验、路由或序列化。
# - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
def load_reuse_first_policy(path: str | Path) -> ReuseFirstPolicy:
    # 变量更新：计算并保存raw，右侧逻辑为`json.loads(Path(path).read_text(encoding='utf-8'))`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    # 条件门禁：判断`not isinstance(raw, dict)`，条件为真时进入受保护分支。
    # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
    # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
    if not isinstance(raw, dict):
        # 错误阻断：抛出`DataContractError('复用政策根节点必须是对象。')`并停止当前路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
        # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
        raise DataContractError("复用政策根节点必须是对象。")
    # 结果返回：把`ReuseFirstPolicy(task_id=str(raw['task_id']), policy_version=str(raw['policy_version']), policy_s...`交给调用方。
    # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
    # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
    return ReuseFirstPolicy(
        task_id=str(raw["task_id"]),
        policy_version=str(raw["policy_version"]),
        policy_status=str(raw["policy_status"]),
        principle=str(raw["principle"]),
        custom_implementation_default_allowed=bool(
            raw["custom_implementation_default_allowed"]
        ),
        unknown_license_reuse_allowed=bool(
            raw["unknown_license_reuse_allowed"]
        ),
        copy_without_provenance_allowed=bool(
            raw["copy_without_provenance_allowed"]
        ),
        vendor_sdk_reimplementation_allowed=bool(
            raw["vendor_sdk_reimplementation_allowed"]
        ),
        reuse_order=tuple(str(value) for value in raw["reuse_order"]),
        required_assessment_sections=tuple(
            str(value)
            for value in raw["required_assessment_sections"]
        ),
        required_custom_build_evidence=tuple(
            str(value)
            for value in raw["required_custom_build_evidence"]
        ),
        adapter_specific_rules=tuple(
            str(value) for value in raw["adapter_specific_rules"]
        ),
        hard_rules=tuple(str(value) for value in raw["hard_rules"]),
    )
