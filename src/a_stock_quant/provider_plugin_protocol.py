# 模块总览：TASK_020B：通用Provider插件协议、发现结果和多来源路由。
# - 输入输出：本模块通过强类型对象和纯函数交换数据，不在导入阶段执行隐式网络或数据库写入。
# - 数据变化：只有显式构造、校验、加载或方法调用才会产生新对象或更新受控状态。
# - 为什么这样写：先说明模块边界，读者可以在阅读实现前理解职责、风险和复用方式。
"""TASK_020B：通用Provider插件协议、发现结果和多来源路由。"""
# 依赖导入：加载标准库、类型工具和项目内合同，供下方数据结构与校验逻辑复用。
# - 标准库只提供解析、数学、时间、路径和类型能力；项目模块提供统一异常与上游合同。
# - 为什么这样写：集中导入让依赖边界清晰，并避免在函数内部重复加载同一模块。
from __future__ import annotations

import json
import math
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping, Protocol, runtime_checkable

from .data_contracts import DataContractError
from .provider_capabilities import (
    CapabilityImplementationStatus,
    ProviderCapabilityMatrix,
    ProviderDiscoveryStatus,
    ProviderLifecycle,
)


# 变量更新：计算并保存SECRET_REFERENCE_PREFIXES，右侧逻辑为`('none://', 'env://', 'keyring://', 'secret-manager://', 'interactive://')`。
# - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
# - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
SECRET_REFERENCE_PREFIXES = (
    "none://",
    "env://",
    "keyring://",
    "secret-manager://",
    "interactive://",
)

# 变量更新：计算并保存_EXECUTION_CAPABILITIES，右侧逻辑为`{'ORDER_SUBMIT', 'ORDER_CANCEL', 'TRADE_CONFIRMATION'}`。
# - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
# - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
_EXECUTION_CAPABILITIES = {
    "ORDER_SUBMIT",
    "ORDER_CANCEL",
    "TRADE_CONFIRMATION",
}


# 定义插件注册表中的目标、桥接、发现、可用和失败状态。
# - 状态成员：枚举值或方法共同描述该合同允许的有限状态和行为。
# - 数据变化：类本身不执行隐式I/O，实例字段只在显式构造、校验或方法调用时变化。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
class PluginRegistrationStatus(str, Enum):
    # 变量更新：计算并保存REGISTERED_TARGET，右侧逻辑为`'REGISTERED_TARGET'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    REGISTERED_TARGET = "REGISTERED_TARGET"
    # 变量更新：计算并保存LEGACY_BRIDGE_REQUIRED，右侧逻辑为`'LEGACY_BRIDGE_REQUIRED'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    LEGACY_BRIDGE_REQUIRED = "LEGACY_BRIDGE_REQUIRED"
    # 变量更新：计算并保存DISCOVERY_PENDING，右侧逻辑为`'DISCOVERY_PENDING'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    DISCOVERY_PENDING = "DISCOVERY_PENDING"
    # 变量更新：计算并保存DISCOVERY_COMPLETE，右侧逻辑为`'DISCOVERY_COMPLETE'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    DISCOVERY_COMPLETE = "DISCOVERY_COMPLETE"
    # 变量更新：计算并保存AVAILABLE，右侧逻辑为`'AVAILABLE'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    AVAILABLE = "AVAILABLE"
    # 变量更新：计算并保存SUSPENDED，右侧逻辑为`'SUSPENDED'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    SUSPENDED = "SUSPENDED"
    # 变量更新：计算并保存FAILED，右侧逻辑为`'FAILED'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    FAILED = "FAILED"


# 定义一次真实能力发现的完成结果。
# - 状态成员：枚举值或方法共同描述该合同允许的有限状态和行为。
# - 数据变化：类本身不执行隐式I/O，实例字段只在显式构造、校验或方法调用时变化。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
class DiscoveryOutcome(str, Enum):
    # 变量更新：计算并保存NOT_RUN，右侧逻辑为`'NOT_RUN'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    NOT_RUN = "NOT_RUN"
    # 变量更新：计算并保存PARTIAL，右侧逻辑为`'PARTIAL'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    PARTIAL = "PARTIAL"
    # 变量更新：计算并保存COMPLETE，右侧逻辑为`'COMPLETE'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    COMPLETE = "COMPLETE"
    # 变量更新：计算并保存FAILED，右侧逻辑为`'FAILED'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    FAILED = "FAILED"


# 定义认证材料的引用方式而不是秘密本身。
# - 状态成员：枚举值或方法共同描述该合同允许的有限状态和行为。
# - 数据变化：类本身不执行隐式I/O，实例字段只在显式构造、校验或方法调用时变化。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
class AuthenticationReferenceKind(str, Enum):
    # 变量更新：计算并保存NONE，右侧逻辑为`'NONE'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    NONE = "NONE"
    # 变量更新：计算并保存ENVIRONMENT_VARIABLE，右侧逻辑为`'ENVIRONMENT_VARIABLE'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    ENVIRONMENT_VARIABLE = "ENVIRONMENT_VARIABLE"
    # 变量更新：计算并保存OS_KEYRING，右侧逻辑为`'OS_KEYRING'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    OS_KEYRING = "OS_KEYRING"
    # 变量更新：计算并保存EXTERNAL_SECRET_MANAGER，右侧逻辑为`'EXTERNAL_SECRET_MANAGER'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    EXTERNAL_SECRET_MANAGER = "EXTERNAL_SECRET_MANAGER"
    # 变量更新：计算并保存INTERACTIVE_SESSION，右侧逻辑为`'INTERACTIVE_SESSION'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    INTERACTIVE_SESSION = "INTERACTIVE_SESSION"


# 定义限频等政策来自合同、观察或官方文档的证据等级。
# - 状态成员：枚举值或方法共同描述该合同允许的有限状态和行为。
# - 数据变化：类本身不执行隐式I/O，实例字段只在显式构造、校验或方法调用时变化。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
class PolicyEvidenceStatus(str, Enum):
    # 变量更新：计算并保存UNKNOWN，右侧逻辑为`'UNKNOWN'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    UNKNOWN = "UNKNOWN"
    # 变量更新：计算并保存CONTRACT，右侧逻辑为`'CONTRACT'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    CONTRACT = "CONTRACT"
    # 变量更新：计算并保存OBSERVED，右侧逻辑为`'OBSERVED'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    OBSERVED = "OBSERVED"
    # 变量更新：计算并保存VENDOR_DOCUMENTATION，右侧逻辑为`'VENDOR_DOCUMENTATION'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    VENDOR_DOCUMENTATION = "VENDOR_DOCUMENTATION"


# 定义Provider分页协议类型。
# - 状态成员：枚举值或方法共同描述该合同允许的有限状态和行为。
# - 数据变化：类本身不执行隐式I/O，实例字段只在显式构造、校验或方法调用时变化。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
class PaginationMode(str, Enum):
    # 变量更新：计算并保存NONE，右侧逻辑为`'NONE'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    NONE = "NONE"
    # 变量更新：计算并保存PAGE_NUMBER，右侧逻辑为`'PAGE_NUMBER'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    PAGE_NUMBER = "PAGE_NUMBER"
    # 变量更新：计算并保存OFFSET_LIMIT，右侧逻辑为`'OFFSET_LIMIT'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    OFFSET_LIMIT = "OFFSET_LIMIT"
    # 变量更新：计算并保存CURSOR，右侧逻辑为`'CURSOR'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    CURSOR = "CURSOR"
    # 变量更新：计算并保存ITERATOR，右侧逻辑为`'ITERATOR'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    ITERATOR = "ITERATOR"


# 定义实时数据订阅或轮询模式。
# - 状态成员：枚举值或方法共同描述该合同允许的有限状态和行为。
# - 数据变化：类本身不执行隐式I/O，实例字段只在显式构造、校验或方法调用时变化。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
class SubscriptionMode(str, Enum):
    # 变量更新：计算并保存NONE，右侧逻辑为`'NONE'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    NONE = "NONE"
    # 变量更新：计算并保存POLLING，右侧逻辑为`'POLLING'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    POLLING = "POLLING"
    # 变量更新：计算并保存CALLBACK，右侧逻辑为`'CALLBACK'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    CALLBACK = "CALLBACK"
    # 变量更新：计算并保存STREAM，右侧逻辑为`'STREAM'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    STREAM = "STREAM"


# 定义许可证边界是否未知、待审查、允许或拒绝。
# - 状态成员：枚举值或方法共同描述该合同允许的有限状态和行为。
# - 数据变化：类本身不执行隐式I/O，实例字段只在显式构造、校验或方法调用时变化。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
class LicenseDecision(str, Enum):
    # 变量更新：计算并保存UNKNOWN，右侧逻辑为`'UNKNOWN'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    UNKNOWN = "UNKNOWN"
    # 变量更新：计算并保存REVIEW_REQUIRED，右侧逻辑为`'REVIEW_REQUIRED'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    # 变量更新：计算并保存ALLOWED，右侧逻辑为`'ALLOWED'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    ALLOWED = "ALLOWED"
    # 变量更新：计算并保存DENIED，右侧逻辑为`'DENIED'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    DENIED = "DENIED"


# 定义Provider健康状态，供路由硬门禁使用。
# - 状态成员：枚举值或方法共同描述该合同允许的有限状态和行为。
# - 数据变化：类本身不执行隐式I/O，实例字段只在显式构造、校验或方法调用时变化。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
class ProviderHealthStatus(str, Enum):
    # 变量更新：计算并保存UNKNOWN，右侧逻辑为`'UNKNOWN'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    UNKNOWN = "UNKNOWN"
    # 变量更新：计算并保存HEALTHY，右侧逻辑为`'HEALTHY'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    HEALTHY = "HEALTHY"
    # 变量更新：计算并保存DEGRADED，右侧逻辑为`'DEGRADED'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    DEGRADED = "DEGRADED"
    # 变量更新：计算并保存UNAVAILABLE，右侧逻辑为`'UNAVAILABLE'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    UNAVAILABLE = "UNAVAILABLE"


# 定义路由候选最终是否有资格参与选择。
# - 状态成员：枚举值或方法共同描述该合同允许的有限状态和行为。
# - 数据变化：类本身不执行隐式I/O，实例字段只在显式构造、校验或方法调用时变化。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
class RouteDecision(str, Enum):
    # 变量更新：计算并保存ELIGIBLE，右侧逻辑为`'ELIGIBLE'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    ELIGIBLE = "ELIGIBLE"
    # 变量更新：计算并保存INELIGIBLE，右侧逻辑为`'INELIGIBLE'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    INELIGIBLE = "INELIGIBLE"


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


# 执行_nonnegative_int逻辑，把输入参数转换为受合同约束的结果。
# - 参数value：类型Any；进入函数后按合同校验或参与计算。
# - 参数field_name：类型str；进入函数后按合同校验或参与计算。
# - 输出：返回类型int；调用方按该类型继续校验、路由或序列化。
# - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
# - 为什么这样写：允许零但拒绝负数，适合重试次数、保留天数等可以为零的计数。
def _nonnegative_int(value: Any, field_name: str) -> int:
    # 条件门禁：判断`isinstance(value, bool) or not isinstance(value, int) or value < 0`，条件为真时进入受保护分支。
    # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
    # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        # 错误阻断：抛出`DataContractError(f'{field_name}必须是非负整数。')`并停止当前路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
        # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
        raise DataContractError(f"{field_name}必须是非负整数。")
    # 结果返回：把`value`交给调用方。
    # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
    # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
    return value


# 执行_finite逻辑，把输入参数转换为受合同约束的结果。
# - 参数value：类型Any；进入函数后按合同校验或参与计算。
# - 参数field_name：类型str；进入函数后按合同校验或参与计算。
# - 输出：返回类型float；调用方按该类型继续校验、路由或序列化。
# - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
# - 为什么这样写：把数值统一转换为有限浮点数，避免NaN或无穷大破坏评分和阈值比较。
def _finite(value: Any, field_name: str) -> float:
    # 条件门禁：判断`isinstance(value, bool)`，条件为真时进入受保护分支。
    # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
    # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
    if isinstance(value, bool):
        # 错误阻断：抛出`DataContractError(f'{field_name}必须是有限数。')`并停止当前路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
        # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
        raise DataContractError(f"{field_name}必须是有限数。")
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
        # 错误阻断：抛出`DataContractError(f'{field_name}必须是有限数。')`并停止当前路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
        # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
        raise DataContractError(f"{field_name}必须是有限数。") from exc
    # 条件门禁：判断`not math.isfinite(result)`，条件为真时进入受保护分支。
    # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
    # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
    if not math.isfinite(result):
        # 错误阻断：抛出`DataContractError(f'{field_name}必须是有限数。')`并停止当前路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
        # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
        raise DataContractError(f"{field_name}必须是有限数。")
    # 结果返回：把`result`交给调用方。
    # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
    # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
    return result


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


# 执行_coerce_datetime逻辑，把输入参数转换为受合同约束的结果。
# - 参数value：类型Any；进入函数后按合同校验或参与计算。
# - 参数field_name：类型str；进入函数后按合同校验或参与计算。
# - 输出：返回类型datetime；调用方按该类型继续校验、路由或序列化。
# - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
def _coerce_datetime(value: Any, field_name: str) -> datetime:
    # 条件门禁：判断`isinstance(value, datetime)`，条件为真时进入受保护分支。
    # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
    # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
    if isinstance(value, datetime):
        # 结果返回：把`value`交给调用方。
        # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
        # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
        return value
    # 变量更新：计算并保存text，右侧逻辑为`_require_text(value, field_name)`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    text = _require_text(value, field_name)
    # 异常边界：执行可能失败的转换或外部调用，并把底层异常转换为项目可理解的合同错误。
    # - 数据变化：成功路径产生正常结果，失败路径保留原异常作为cause或记录明确错误。
    # - 为什么这样写：统一异常类型可以让上层门禁稳定处理，而不依赖第三方异常细节。
    try:
        # 结果返回：把`datetime.fromisoformat(text.replace('Z', '+00:00'))`交给调用方。
        # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
        # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    # 异常转换：捕获预期失败并保留上下文，随后转成项目统一错误或降级结果。
    # - 为什么这样写：上层不需要理解第三方异常细节，也能得到稳定错误语义。
    except ValueError as exc:
        # 错误阻断：抛出`DataContractError(f'{field_name}不是ISO时间。')`并停止当前路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
        # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
        raise DataContractError(f"{field_name}不是ISO时间。") from exc


# 执行_looks_like_secret逻辑，把输入参数转换为受合同约束的结果。
# - 参数value：类型str；进入函数后按合同校验或参与计算。
# - 输出：返回类型bool；调用方按该类型继续校验、路由或序列化。
# - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
def _looks_like_secret(value: str) -> bool:
    # 变量更新：计算并保存text，右侧逻辑为`value.strip()`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    text = value.strip()
    # 条件门禁：判断`not text`，条件为真时进入受保护分支。
    # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
    # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
    if not text:
        # 结果返回：把`False`交给调用方。
        # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
        # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
        return False
    # 条件门禁：判断`re.fullmatch('[A-Za-z0-9_\\-]{32,}', text)`，条件为真时进入受保护分支。
    # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
    # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
    if re.fullmatch(r"[A-Za-z0-9_\-]{32,}", text):
        # 结果返回：把`True`交给调用方。
        # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
        # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
        return True
    # 变量更新：计算并保存lowered，右侧逻辑为`text.lower()`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    lowered = text.lower()
    # 变量更新：计算并保存forbidden_fragments，右侧逻辑为`('password=', 'passwd=', 'token=', 'secret=', 'api_key=', 'apikey=', 'private_key=')`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    forbidden_fragments = (
        "password=",
        "passwd=",
        "token=",
        "secret=",
        "api_key=",
        "apikey=",
        "private_key=",
    )
    # 结果返回：把`any((fragment in lowered for fragment in forbidden_fragments))`交给调用方。
    # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
    # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
    return any(fragment in lowered for fragment in forbidden_fragments)


# 定义AuthenticationReference强类型合同，集中保存相关状态、参数和校验规则。
# - 字段reference_id：类型str。
# - 字段kind：类型AuthenticationReferenceKind。
# - 字段locator：类型str。
# - 字段scopes：类型tuple[str, ...]，默认值()。
# - 字段interactive_login_required：类型bool，默认值False。
# - 数据变化：类本身不执行隐式I/O，实例字段只在显式构造、校验或方法调用时变化。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
@dataclass(frozen=True, slots=True)
class AuthenticationReference:
    # 变量更新：计算并保存reference_id，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    reference_id: str
    # 变量更新：计算并保存kind，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    kind: AuthenticationReferenceKind
    # 变量更新：计算并保存locator，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    locator: str
    # 变量更新：计算并保存scopes，右侧逻辑为`()`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    scopes: tuple[str, ...] = ()
    # 变量更新：计算并保存interactive_login_required，右侧逻辑为`False`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    interactive_login_required: bool = False

    # 执行__post_init__逻辑，把输入参数转换为受合同约束的结果。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态或模块常量。
    # - 输出：返回类型None；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：在不可变或数据类对象创建后立即校验字段关系，阻止不一致对象进入系统。
    def __post_init__(self) -> None:
        # API调用：执行`object.__setattr__(self, 'reference_id', _require_text(self.reference_id, 'reference_id'))`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        object.__setattr__(
            self,
            "reference_id",
            _require_text(self.reference_id, "reference_id"),
        )
        # 变量更新：计算并保存kind，右侧逻辑为`self.kind`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        kind = self.kind
        # 条件门禁：判断`isinstance(kind, str)`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if isinstance(kind, str):
            # 变量更新：计算并保存kind，右侧逻辑为`AuthenticationReferenceKind(kind)`。
            # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
            # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
            kind = AuthenticationReferenceKind(kind)
        # API调用：执行`object.__setattr__(self, 'kind', kind)`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        object.__setattr__(self, "kind", kind)
        # 变量更新：计算并保存locator，右侧逻辑为`_require_text(self.locator, 'locator')`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        locator = _require_text(self.locator, "locator")
        # 条件门禁：判断`not locator.startswith(SECRET_REFERENCE_PREFIXES)`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if not locator.startswith(SECRET_REFERENCE_PREFIXES):
            # 错误阻断：抛出`DataContractError('认证locator必须是受支持的引用URI。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError("认证locator必须是受支持的引用URI。")
        # 条件门禁：判断`_looks_like_secret(locator)`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if _looks_like_secret(locator):
            # 错误阻断：抛出`DataContractError('认证引用疑似包含秘密材料。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError("认证引用疑似包含秘密材料。")
        # 变量更新：计算并保存expected_prefix，右侧逻辑为`{AuthenticationReferenceKind.NONE: 'none://', AuthenticationReferenceKind.ENVIRONMENT_V...`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        expected_prefix = {
            AuthenticationReferenceKind.NONE: "none://",
            AuthenticationReferenceKind.ENVIRONMENT_VARIABLE: "env://",
            AuthenticationReferenceKind.OS_KEYRING: "keyring://",
            AuthenticationReferenceKind.EXTERNAL_SECRET_MANAGER: (
                "secret-manager://"
            ),
            AuthenticationReferenceKind.INTERACTIVE_SESSION: (
                "interactive://"
            ),
        }[kind]
        # 条件门禁：判断`not locator.startswith(expected_prefix)`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if not locator.startswith(expected_prefix):
            # 错误阻断：抛出`DataContractError('认证类型与locator前缀不一致。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError("认证类型与locator前缀不一致。")
        # API调用：执行`object.__setattr__(self, 'locator', locator)`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        object.__setattr__(self, "locator", locator)
        # API调用：执行`object.__setattr__(self, 'scopes', _unique_texts(self.scopes, 'scopes'))`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        object.__setattr__(
            self,
            "scopes",
            _unique_texts(self.scopes, "scopes"),
        )


# 定义SdkRuntimeDescriptor强类型合同，集中保存相关状态、参数和校验规则。
# - 字段provider_id：类型str。
# - 字段runtime_id：类型str。
# - 字段operating_systems：类型tuple[str, ...]。
# - 字段python_versions：类型tuple[str, ...]。
# - 字段architecture：类型str。
# - 字段client_name：类型str | None。
# - 字段client_version：类型str | None。
# - 字段sdk_name：类型str | None。
# - 其余字段：另有4项，均在对象创建时统一校验。
# - 数据变化：类本身不执行隐式I/O，实例字段只在显式构造、校验或方法调用时变化。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
@dataclass(frozen=True, slots=True)
class SdkRuntimeDescriptor:
    # 变量更新：计算并保存provider_id，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    provider_id: str
    # 变量更新：计算并保存runtime_id，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    runtime_id: str
    # 变量更新：计算并保存operating_systems，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    operating_systems: tuple[str, ...]
    # 变量更新：计算并保存python_versions，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    python_versions: tuple[str, ...]
    # 变量更新：计算并保存architecture，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    architecture: str
    # 变量更新：计算并保存client_name，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    client_name: str | None
    # 变量更新：计算并保存client_version，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    client_version: str | None
    # 变量更新：计算并保存sdk_name，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    sdk_name: str | None
    # 变量更新：计算并保存sdk_version，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    sdk_version: str | None
    # 变量更新：计算并保存installed，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    installed: bool
    # 变量更新：计算并保存installation_probe，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    installation_probe: str
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
        # 迭代处理：依次读取`('provider_id', 'runtime_id', 'architecture', 'installation_probe', 'notes')`中的元素，并绑定到`field_name`。
        # - 维度变化：每轮处理一个元素，可能向列表、字典或累计值中增加一项。
        # - 为什么这样写：显式逐项校验可以精确指出哪个字段或Provider不符合合同。
        for field_name in (
            "provider_id",
            "runtime_id",
            "architecture",
            "installation_probe",
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
        # API调用：执行`object.__setattr__(self, 'operating_systems', _unique_texts(self.operating_systems, 'operating_sy...`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        object.__setattr__(
            self,
            "operating_systems",
            _unique_texts(
                self.operating_systems,
                "operating_systems",
                allow_empty=False,
            ),
        )
        # API调用：执行`object.__setattr__(self, 'python_versions', _unique_texts(self.python_versions, 'python_versions'))`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        object.__setattr__(
            self,
            "python_versions",
            _unique_texts(self.python_versions, "python_versions"),
        )
        # 迭代处理：依次读取`('client_name', 'client_version', 'sdk_name', 'sdk_version')`中的元素，并绑定到`field_name`。
        # - 维度变化：每轮处理一个元素，可能向列表、字典或累计值中增加一项。
        # - 为什么这样写：显式逐项校验可以精确指出哪个字段或Provider不符合合同。
        for field_name in (
            "client_name",
            "client_version",
            "sdk_name",
            "sdk_version",
        ):
            # API调用：执行`object.__setattr__(self, field_name, _optional_text(getattr(self, field_name), field_name))`以触发注册、写入对象状态或其他显式副作用。
            # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
            # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
            object.__setattr__(
                self,
                field_name,
                _optional_text(getattr(self, field_name), field_name),
            )
        # 条件门禁：判断`self.installed and (not (self.client_name or self.sdk_name))`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if self.installed and not (self.client_name or self.sdk_name):
            # 错误阻断：抛出`DataContractError('已安装运行时必须声明client_name或sdk_name。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError(
                "已安装运行时必须声明client_name或sdk_name。"
            )


# 定义RateLimitPolicy强类型合同，集中保存相关状态、参数和校验规则。
# - 字段requests_per_period：类型int | None。
# - 字段period_seconds：类型int | None。
# - 字段burst_size：类型int | None。
# - 字段maximum_concurrency：类型int。
# - 字段evidence_status：类型PolicyEvidenceStatus。
# - 字段evidence_refs：类型tuple[str, ...]。
# - 数据变化：类本身不执行隐式I/O，实例字段只在显式构造、校验或方法调用时变化。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
@dataclass(frozen=True, slots=True)
class RateLimitPolicy:
    # 变量更新：计算并保存requests_per_period，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    requests_per_period: int | None
    # 变量更新：计算并保存period_seconds，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    period_seconds: int | None
    # 变量更新：计算并保存burst_size，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    burst_size: int | None
    # 变量更新：计算并保存maximum_concurrency，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    maximum_concurrency: int
    # 变量更新：计算并保存evidence_status，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    evidence_status: PolicyEvidenceStatus
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
        # 条件门禁：判断`self.requests_per_period is not None`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if self.requests_per_period is not None:
            # API调用：执行`_positive_int(self.requests_per_period, 'requests_per_period')`以触发注册、写入对象状态或其他显式副作用。
            # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
            # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
            _positive_int(
                self.requests_per_period,
                "requests_per_period",
            )
        # 条件门禁：判断`self.period_seconds is not None`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if self.period_seconds is not None:
            # API调用：执行`_positive_int(self.period_seconds, 'period_seconds')`以触发注册、写入对象状态或其他显式副作用。
            # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
            # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
            _positive_int(self.period_seconds, "period_seconds")
        # 条件门禁：判断`(self.requests_per_period is None) != (self.period_seconds is None)`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if (self.requests_per_period is None) != (
            self.period_seconds is None
        ):
            # 错误阻断：抛出`DataContractError('requests_per_period和period_seconds必须同时存在。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError(
                "requests_per_period和period_seconds必须同时存在。"
            )
        # 条件门禁：判断`self.burst_size is not None`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if self.burst_size is not None:
            # API调用：执行`_positive_int(self.burst_size, 'burst_size')`以触发注册、写入对象状态或其他显式副作用。
            # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
            # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
            _positive_int(self.burst_size, "burst_size")
        # API调用：执行`_positive_int(self.maximum_concurrency, 'maximum_concurrency')`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        _positive_int(self.maximum_concurrency, "maximum_concurrency")
        # 变量更新：计算并保存status，右侧逻辑为`self.evidence_status`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        status = self.evidence_status
        # 条件门禁：判断`isinstance(status, str)`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if isinstance(status, str):
            # 变量更新：计算并保存status，右侧逻辑为`PolicyEvidenceStatus(status)`。
            # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
            # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
            status = PolicyEvidenceStatus(status)
        # API调用：执行`object.__setattr__(self, 'evidence_status', status)`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        object.__setattr__(self, "evidence_status", status)
        # 变量更新：计算并保存refs，右侧逻辑为`_unique_texts(self.evidence_refs, 'evidence_refs')`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        refs = _unique_texts(self.evidence_refs, "evidence_refs")
        # 条件门禁：判断`status is not PolicyEvidenceStatus.UNKNOWN and (not refs)`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if status is not PolicyEvidenceStatus.UNKNOWN and not refs:
            # 错误阻断：抛出`DataContractError('非UNKNOWN限频政策必须有证据引用。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError("非UNKNOWN限频政策必须有证据引用。")
        # API调用：执行`object.__setattr__(self, 'evidence_refs', refs)`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        object.__setattr__(self, "evidence_refs", refs)


# 定义RetryPolicy强类型合同，集中保存相关状态、参数和校验规则。
# - 字段maximum_attempts：类型int。
# - 字段backoff_seconds：类型tuple[int, ...]。
# - 字段retryable_error_codes：类型tuple[str, ...]。
# - 数据变化：类本身不执行隐式I/O，实例字段只在显式构造、校验或方法调用时变化。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
@dataclass(frozen=True, slots=True)
class RetryPolicy:
    # 变量更新：计算并保存maximum_attempts，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    maximum_attempts: int
    # 变量更新：计算并保存backoff_seconds，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    backoff_seconds: tuple[int, ...]
    # 变量更新：计算并保存retryable_error_codes，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    retryable_error_codes: tuple[str, ...]

    # 执行__post_init__逻辑，把输入参数转换为受合同约束的结果。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态或模块常量。
    # - 输出：返回类型None；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：在不可变或数据类对象创建后立即校验字段关系，阻止不一致对象进入系统。
    def __post_init__(self) -> None:
        # API调用：执行`_positive_int(self.maximum_attempts, 'maximum_attempts')`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        _positive_int(self.maximum_attempts, "maximum_attempts")
        # 条件门禁：判断`len(self.backoff_seconds) != max(0, self.maximum_attempts - 1)`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if len(self.backoff_seconds) != max(
            0,
            self.maximum_attempts - 1,
        ):
            # 错误阻断：抛出`DataContractError('退避次数必须等于最大尝试次数减一。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError("退避次数必须等于最大尝试次数减一。")
        # 迭代处理：依次读取`self.backoff_seconds`中的元素，并绑定到`value`。
        # - 维度变化：每轮处理一个元素，可能向列表、字典或累计值中增加一项。
        # - 为什么这样写：显式逐项校验可以精确指出哪个字段或Provider不符合合同。
        for value in self.backoff_seconds:
            # API调用：执行`_nonnegative_int(value, 'backoff_seconds')`以触发注册、写入对象状态或其他显式副作用。
            # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
            # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
            _nonnegative_int(value, "backoff_seconds")
        # API调用：执行`object.__setattr__(self, 'retryable_error_codes', _unique_texts(self.retryable_error_codes, 'retr...`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        object.__setattr__(
            self,
            "retryable_error_codes",
            _unique_texts(
                self.retryable_error_codes,
                "retryable_error_codes",
            ),
        )


# 定义BatchPolicy强类型合同，集中保存相关状态、参数和校验规则。
# - 字段recommended_entities_per_request：类型int。
# - 字段maximum_entities_per_request：类型int。
# - 字段recommended_rows_per_batch：类型int。
# - 字段maximum_rows_per_batch：类型int。
# - 字段supports_date_range：类型bool。
# - 字段supports_parallel_requests：类型bool。
# - 数据变化：类本身不执行隐式I/O，实例字段只在显式构造、校验或方法调用时变化。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
@dataclass(frozen=True, slots=True)
class BatchPolicy:
    # 变量更新：计算并保存recommended_entities_per_request，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    recommended_entities_per_request: int
    # 变量更新：计算并保存maximum_entities_per_request，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    maximum_entities_per_request: int
    # 变量更新：计算并保存recommended_rows_per_batch，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    recommended_rows_per_batch: int
    # 变量更新：计算并保存maximum_rows_per_batch，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    maximum_rows_per_batch: int
    # 变量更新：计算并保存supports_date_range，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    supports_date_range: bool
    # 变量更新：计算并保存supports_parallel_requests，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    supports_parallel_requests: bool

    # 执行__post_init__逻辑，把输入参数转换为受合同约束的结果。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态或模块常量。
    # - 输出：返回类型None；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：在不可变或数据类对象创建后立即校验字段关系，阻止不一致对象进入系统。
    def __post_init__(self) -> None:
        # 迭代处理：依次读取`('recommended_entities_per_request', 'maximum_entities_per_request', 'recomme...`中的元素，并绑定到`field_name`。
        # - 维度变化：每轮处理一个元素，可能向列表、字典或累计值中增加一项。
        # - 为什么这样写：显式逐项校验可以精确指出哪个字段或Provider不符合合同。
        for field_name in (
            "recommended_entities_per_request",
            "maximum_entities_per_request",
            "recommended_rows_per_batch",
            "maximum_rows_per_batch",
        ):
            # API调用：执行`_positive_int(getattr(self, field_name), field_name)`以触发注册、写入对象状态或其他显式副作用。
            # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
            # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
            _positive_int(getattr(self, field_name), field_name)
        # 条件门禁：判断`self.recommended_entities_per_request > self.maximum_entities_per_request`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if (
            self.recommended_entities_per_request
            > self.maximum_entities_per_request
        ):
            # 错误阻断：抛出`DataContractError('推荐实体数不能超过最大实体数。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError("推荐实体数不能超过最大实体数。")
        # 条件门禁：判断`self.recommended_rows_per_batch > self.maximum_rows_per_batch`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if (
            self.recommended_rows_per_batch
            > self.maximum_rows_per_batch
        ):
            # 错误阻断：抛出`DataContractError('推荐批次不能超过最大批次。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError("推荐批次不能超过最大批次。")


# 定义PaginationPolicy强类型合同，集中保存相关状态、参数和校验规则。
# - 字段mode：类型PaginationMode。
# - 字段default_page_size：类型int | None。
# - 字段maximum_page_size：类型int | None。
# - 字段maximum_pages：类型int | None。
# - 字段cursor_field：类型str | None。
# - 数据变化：类本身不执行隐式I/O，实例字段只在显式构造、校验或方法调用时变化。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
@dataclass(frozen=True, slots=True)
class PaginationPolicy:
    # 变量更新：计算并保存mode，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    mode: PaginationMode
    # 变量更新：计算并保存default_page_size，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    default_page_size: int | None
    # 变量更新：计算并保存maximum_page_size，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    maximum_page_size: int | None
    # 变量更新：计算并保存maximum_pages，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    maximum_pages: int | None
    # 变量更新：计算并保存cursor_field，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    cursor_field: str | None

    # 执行__post_init__逻辑，把输入参数转换为受合同约束的结果。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态或模块常量。
    # - 输出：返回类型None；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：在不可变或数据类对象创建后立即校验字段关系，阻止不一致对象进入系统。
    def __post_init__(self) -> None:
        # 变量更新：计算并保存mode，右侧逻辑为`self.mode`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        mode = self.mode
        # 条件门禁：判断`isinstance(mode, str)`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if isinstance(mode, str):
            # 变量更新：计算并保存mode，右侧逻辑为`PaginationMode(mode)`。
            # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
            # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
            mode = PaginationMode(mode)
        # API调用：执行`object.__setattr__(self, 'mode', mode)`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        object.__setattr__(self, "mode", mode)
        # 迭代处理：依次读取`('default_page_size', 'maximum_page_size', 'maximum_pages')`中的元素，并绑定到`field_name`。
        # - 维度变化：每轮处理一个元素，可能向列表、字典或累计值中增加一项。
        # - 为什么这样写：显式逐项校验可以精确指出哪个字段或Provider不符合合同。
        for field_name in (
            "default_page_size",
            "maximum_page_size",
            "maximum_pages",
        ):
            # 变量更新：计算并保存value，右侧逻辑为`getattr(self, field_name)`。
            # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
            # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
            value = getattr(self, field_name)
            # 条件门禁：判断`value is not None`，条件为真时进入受保护分支。
            # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
            # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
            if value is not None:
                # API调用：执行`_positive_int(value, field_name)`以触发注册、写入对象状态或其他显式副作用。
                # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
                # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
                _positive_int(value, field_name)
        # 条件门禁：判断`self.default_page_size is not None and self.maximum_page_size is not None and (self.default_page_...`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if (
            self.default_page_size is not None
            and self.maximum_page_size is not None
            and self.default_page_size > self.maximum_page_size
        ):
            # 错误阻断：抛出`DataContractError('默认分页大小不能超过最大分页大小。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError("默认分页大小不能超过最大分页大小。")
        # 变量更新：计算并保存cursor_field，右侧逻辑为`_optional_text(self.cursor_field, 'cursor_field')`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        cursor_field = _optional_text(self.cursor_field, "cursor_field")
        # API调用：执行`object.__setattr__(self, 'cursor_field', cursor_field)`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        object.__setattr__(self, "cursor_field", cursor_field)
        # 条件门禁：判断`mode is PaginationMode.CURSOR and cursor_field is None`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if mode is PaginationMode.CURSOR and cursor_field is None:
            # 错误阻断：抛出`DataContractError('CURSOR分页必须声明cursor_field。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError("CURSOR分页必须声明cursor_field。")
        # 条件门禁：判断`mode is PaginationMode.NONE and any((value is not None for value in (self.default_page_size, self...`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if mode is PaginationMode.NONE and any(
            value is not None
            for value in (
                self.default_page_size,
                self.maximum_page_size,
                self.maximum_pages,
                self.cursor_field,
            )
        ):
            # 错误阻断：抛出`DataContractError('NONE分页不得携带分页参数。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError("NONE分页不得携带分页参数。")


# 定义SubscriptionPolicy强类型合同，集中保存相关状态、参数和校验规则。
# - 字段mode：类型SubscriptionMode。
# - 字段maximum_symbols：类型int | None。
# - 字段heartbeat_seconds：类型int | None。
# - 字段reconnect_supported：类型bool。
# - 字段replay_supported：类型bool。
# - 数据变化：类本身不执行隐式I/O，实例字段只在显式构造、校验或方法调用时变化。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
@dataclass(frozen=True, slots=True)
class SubscriptionPolicy:
    # 变量更新：计算并保存mode，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    mode: SubscriptionMode
    # 变量更新：计算并保存maximum_symbols，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    maximum_symbols: int | None
    # 变量更新：计算并保存heartbeat_seconds，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    heartbeat_seconds: int | None
    # 变量更新：计算并保存reconnect_supported，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    reconnect_supported: bool
    # 变量更新：计算并保存replay_supported，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    replay_supported: bool

    # 执行__post_init__逻辑，把输入参数转换为受合同约束的结果。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态或模块常量。
    # - 输出：返回类型None；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：在不可变或数据类对象创建后立即校验字段关系，阻止不一致对象进入系统。
    def __post_init__(self) -> None:
        # 变量更新：计算并保存mode，右侧逻辑为`self.mode`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        mode = self.mode
        # 条件门禁：判断`isinstance(mode, str)`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if isinstance(mode, str):
            # 变量更新：计算并保存mode，右侧逻辑为`SubscriptionMode(mode)`。
            # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
            # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
            mode = SubscriptionMode(mode)
        # API调用：执行`object.__setattr__(self, 'mode', mode)`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        object.__setattr__(self, "mode", mode)
        # 条件门禁：判断`self.maximum_symbols is not None`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if self.maximum_symbols is not None:
            # API调用：执行`_positive_int(self.maximum_symbols, 'maximum_symbols')`以触发注册、写入对象状态或其他显式副作用。
            # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
            # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
            _positive_int(self.maximum_symbols, "maximum_symbols")
        # 条件门禁：判断`self.heartbeat_seconds is not None`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if self.heartbeat_seconds is not None:
            # API调用：执行`_positive_int(self.heartbeat_seconds, 'heartbeat_seconds')`以触发注册、写入对象状态或其他显式副作用。
            # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
            # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
            _positive_int(self.heartbeat_seconds, "heartbeat_seconds")
        # 条件门禁：判断`mode is SubscriptionMode.NONE and any((self.maximum_symbols is not None, self.heartbeat_seconds i...`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if mode is SubscriptionMode.NONE and any(
            (
                self.maximum_symbols is not None,
                self.heartbeat_seconds is not None,
                self.reconnect_supported,
                self.replay_supported,
            )
        ):
            # 错误阻断：抛出`DataContractError('NONE订阅不得声明订阅参数。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError("NONE订阅不得声明订阅参数。")


# 定义LicenseBoundary强类型合同，集中保存相关状态、参数和校验规则。
# - 字段decision：类型LicenseDecision。
# - 字段permitted_usages：类型tuple[str, ...]。
# - 字段cache_allowed：类型bool。
# - 字段persistent_storage_allowed：类型bool。
# - 字段redistribution_allowed：类型bool。
# - 字段maximum_retention_days：类型int | None。
# - 字段evidence_refs：类型tuple[str, ...]。
# - 数据变化：类本身不执行隐式I/O，实例字段只在显式构造、校验或方法调用时变化。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
@dataclass(frozen=True, slots=True)
class LicenseBoundary:
    # 变量更新：计算并保存decision，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    decision: LicenseDecision
    # 变量更新：计算并保存permitted_usages，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    permitted_usages: tuple[str, ...]
    # 变量更新：计算并保存cache_allowed，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    cache_allowed: bool
    # 变量更新：计算并保存persistent_storage_allowed，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    persistent_storage_allowed: bool
    # 变量更新：计算并保存redistribution_allowed，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    redistribution_allowed: bool
    # 变量更新：计算并保存maximum_retention_days，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    maximum_retention_days: int | None
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
        # 变量更新：计算并保存decision，右侧逻辑为`self.decision`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        decision = self.decision
        # 条件门禁：判断`isinstance(decision, str)`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if isinstance(decision, str):
            # 变量更新：计算并保存decision，右侧逻辑为`LicenseDecision(decision)`。
            # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
            # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
            decision = LicenseDecision(decision)
        # API调用：执行`object.__setattr__(self, 'decision', decision)`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        object.__setattr__(self, "decision", decision)
        # 变量更新：计算并保存usages，右侧逻辑为`_unique_texts(self.permitted_usages, 'permitted_usages')`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        usages = _unique_texts(
            self.permitted_usages,
            "permitted_usages",
        )
        # 变量更新：计算并保存refs，右侧逻辑为`_unique_texts(self.evidence_refs, 'evidence_refs')`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        refs = _unique_texts(self.evidence_refs, "evidence_refs")
        # API调用：执行`object.__setattr__(self, 'permitted_usages', usages)`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        object.__setattr__(self, "permitted_usages", usages)
        # API调用：执行`object.__setattr__(self, 'evidence_refs', refs)`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        object.__setattr__(self, "evidence_refs", refs)
        # 条件门禁：判断`self.maximum_retention_days is not None`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if self.maximum_retention_days is not None:
            # API调用：执行`_nonnegative_int(self.maximum_retention_days, 'maximum_retention_days')`以触发注册、写入对象状态或其他显式副作用。
            # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
            # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
            _nonnegative_int(
                self.maximum_retention_days,
                "maximum_retention_days",
            )
        # 条件门禁：判断`decision is LicenseDecision.ALLOWED`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if decision is LicenseDecision.ALLOWED:
            # 条件门禁：判断`not usages or not refs`，条件为真时进入受保护分支。
            # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
            # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
            if not usages or not refs:
                # 错误阻断：抛出`DataContractError('ALLOWED许可证必须声明用途和证据。')`并停止当前路径。
                # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
                # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
                raise DataContractError(
                    "ALLOWED许可证必须声明用途和证据。"
                )
        # 条件门禁：判断`decision is not LicenseDecision.ALLOWED and any((self.cache_allowed, self.persistent_storage_allo...`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if decision is not LicenseDecision.ALLOWED and any(
            (
                self.cache_allowed,
                self.persistent_storage_allowed,
                self.redistribution_allowed,
            )
        ):
            # 错误阻断：抛出`DataContractError('未放行许可证不得允许缓存、持久化或再分发。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError(
                "未放行许可证不得允许缓存、持久化或再分发。"
            )


# 定义ProviderHealthSnapshot强类型合同，集中保存相关状态、参数和校验规则。
# - 字段status：类型ProviderHealthStatus。
# - 字段checked_at：类型datetime。
# - 字段latency_ms：类型float | None。
# - 字段message：类型str。
# - 字段evidence_refs：类型tuple[str, ...]。
# - 数据变化：类本身不执行隐式I/O，实例字段只在显式构造、校验或方法调用时变化。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
@dataclass(frozen=True, slots=True)
class ProviderHealthSnapshot:
    # 变量更新：计算并保存status，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    status: ProviderHealthStatus
    # 变量更新：计算并保存checked_at，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    checked_at: datetime
    # 变量更新：计算并保存latency_ms，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    latency_ms: float | None
    # 变量更新：计算并保存message，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    message: str
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
        # 变量更新：计算并保存status，右侧逻辑为`self.status`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        status = self.status
        # 条件门禁：判断`isinstance(status, str)`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if isinstance(status, str):
            # 变量更新：计算并保存status，右侧逻辑为`ProviderHealthStatus(status)`。
            # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
            # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
            status = ProviderHealthStatus(status)
        # API调用：执行`object.__setattr__(self, 'status', status)`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        object.__setattr__(self, "status", status)
        # API调用：执行`object.__setattr__(self, 'checked_at', _coerce_datetime(self.checked_at, 'checked_at'))`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        object.__setattr__(
            self,
            "checked_at",
            _coerce_datetime(self.checked_at, "checked_at"),
        )
        # 条件门禁：判断`self.latency_ms is not None`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if self.latency_ms is not None:
            # 变量更新：计算并保存latency，右侧逻辑为`_finite(self.latency_ms, 'latency_ms')`。
            # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
            # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
            latency = _finite(self.latency_ms, "latency_ms")
            # 条件门禁：判断`latency < 0`，条件为真时进入受保护分支。
            # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
            # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
            if latency < 0:
                # 错误阻断：抛出`DataContractError('latency_ms不能为负。')`并停止当前路径。
                # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
                # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
                raise DataContractError("latency_ms不能为负。")
            # API调用：执行`object.__setattr__(self, 'latency_ms', latency)`以触发注册、写入对象状态或其他显式副作用。
            # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
            # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
            object.__setattr__(self, "latency_ms", latency)
        # API调用：执行`object.__setattr__(self, 'message', _require_text(self.message, 'message'))`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        object.__setattr__(
            self,
            "message",
            _require_text(self.message, "message"),
        )
        # API调用：执行`object.__setattr__(self, 'evidence_refs', _unique_texts(self.evidence_refs, 'evidence_refs'))`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        object.__setattr__(
            self,
            "evidence_refs",
            _unique_texts(self.evidence_refs, "evidence_refs"),
        )


# 定义ProviderDiscoveryResult强类型合同，集中保存相关状态、参数和校验规则。
# - 字段discovery_id：类型str。
# - 字段provider_id：类型str。
# - 字段plugin_id：类型str。
# - 字段outcome：类型DiscoveryOutcome。
# - 字段discovered_at：类型datetime。
# - 字段runtime：类型SdkRuntimeDescriptor。
# - 字段authentication_reference：类型AuthenticationReference。
# - 字段capabilities：类型Mapping[str, CapabilityImplementationStatus]。
# - 其余字段：另有9项，均在对象创建时统一校验。
# - 数据变化：类本身不执行隐式I/O，实例字段只在显式构造、校验或方法调用时变化。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
@dataclass(frozen=True, slots=True)
class ProviderDiscoveryResult:
    # 变量更新：计算并保存discovery_id，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    discovery_id: str
    # 变量更新：计算并保存provider_id，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    provider_id: str
    # 变量更新：计算并保存plugin_id，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    plugin_id: str
    # 变量更新：计算并保存outcome，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    outcome: DiscoveryOutcome
    # 变量更新：计算并保存discovered_at，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    discovered_at: datetime
    # 变量更新：计算并保存runtime，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    runtime: SdkRuntimeDescriptor
    # 变量更新：计算并保存authentication_reference，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    authentication_reference: AuthenticationReference
    # 变量更新：计算并保存capabilities，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    capabilities: Mapping[str, CapabilityImplementationStatus]
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
    # 变量更新：计算并保存health，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    health: ProviderHealthSnapshot
    # 变量更新：计算并保存warnings，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    warnings: tuple[str, ...]
    # 变量更新：计算并保存errors，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    errors: tuple[str, ...]

    # 执行__post_init__逻辑，把输入参数转换为受合同约束的结果。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态或模块常量。
    # - 输出：返回类型None；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：在不可变或数据类对象创建后立即校验字段关系，阻止不一致对象进入系统。
    def __post_init__(self) -> None:
        # 迭代处理：依次读取`('discovery_id', 'provider_id', 'plugin_id')`中的元素，并绑定到`field_name`。
        # - 维度变化：每轮处理一个元素，可能向列表、字典或累计值中增加一项。
        # - 为什么这样写：显式逐项校验可以精确指出哪个字段或Provider不符合合同。
        for field_name in ("discovery_id", "provider_id", "plugin_id"):
            # API调用：执行`object.__setattr__(self, field_name, _require_text(getattr(self, field_name), field_name))`以触发注册、写入对象状态或其他显式副作用。
            # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
            # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
            object.__setattr__(
                self,
                field_name,
                _require_text(getattr(self, field_name), field_name),
            )
        # 变量更新：计算并保存outcome，右侧逻辑为`self.outcome`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        outcome = self.outcome
        # 条件门禁：判断`isinstance(outcome, str)`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if isinstance(outcome, str):
            # 变量更新：计算并保存outcome，右侧逻辑为`DiscoveryOutcome(outcome)`。
            # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
            # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
            outcome = DiscoveryOutcome(outcome)
        # API调用：执行`object.__setattr__(self, 'outcome', outcome)`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        object.__setattr__(self, "outcome", outcome)
        # API调用：执行`object.__setattr__(self, 'discovered_at', _coerce_datetime(self.discovered_at, 'discovered_at'))`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        object.__setattr__(
            self,
            "discovered_at",
            _coerce_datetime(self.discovered_at, "discovered_at"),
        )
        # 条件门禁：判断`self.runtime.provider_id != self.provider_id`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if self.runtime.provider_id != self.provider_id:
            # 错误阻断：抛出`DataContractError('运行时provider_id不一致。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError("运行时provider_id不一致。")
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
        # API调用：执行`object.__setattr__(self, 'warnings', _unique_texts(self.warnings, 'warnings'))`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        object.__setattr__(
            self,
            "warnings",
            _unique_texts(self.warnings, "warnings"),
        )
        # API调用：执行`object.__setattr__(self, 'errors', _unique_texts(self.errors, 'errors'))`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        object.__setattr__(
            self,
            "errors",
            _unique_texts(self.errors, "errors"),
        )
        # 条件门禁：判断`outcome is DiscoveryOutcome.COMPLETE`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if outcome is DiscoveryOutcome.COMPLETE:
            # 条件门禁：判断`not self.runtime.installed`，条件为真时进入受保护分支。
            # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
            # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
            if not self.runtime.installed:
                # 错误阻断：抛出`DataContractError('完整发现必须确认运行时已安装。')`并停止当前路径。
                # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
                # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
                raise DataContractError("完整发现必须确认运行时已安装。")
            # 条件门禁：判断`not capabilities`，条件为真时进入受保护分支。
            # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
            # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
            if not capabilities:
                # 错误阻断：抛出`DataContractError('完整发现必须包含能力结果。')`并停止当前路径。
                # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
                # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
                raise DataContractError("完整发现必须包含能力结果。")
            # 条件门禁：判断`self.errors`，条件为真时进入受保护分支。
            # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
            # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
            if self.errors:
                # 错误阻断：抛出`DataContractError('完整发现不得包含errors。')`并停止当前路径。
                # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
                # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
                raise DataContractError("完整发现不得包含errors。")
        # 条件门禁：判断`outcome is DiscoveryOutcome.FAILED and (not self.errors)`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if outcome is DiscoveryOutcome.FAILED and not self.errors:
            # 错误阻断：抛出`DataContractError('失败发现必须记录errors。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError("失败发现必须记录errors。")


# 定义ProviderRegistryEntry强类型合同，集中保存相关状态、参数和校验规则。
# - 字段provider_id：类型str。
# - 字段plugin_id：类型str。
# - 字段registration_status：类型PluginRegistrationStatus。
# - 字段entrypoint：类型str | None。
# - 字段priority：类型int。
# - 字段enabled_for_routing：类型bool。
# - 字段discovery_result_ref：类型str | None。
# - 字段authentication_reference_ref：类型str | None。
# - 其余字段：另有1项，均在对象创建时统一校验。
# - 数据变化：类本身不执行隐式I/O，实例字段只在显式构造、校验或方法调用时变化。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
@dataclass(frozen=True, slots=True)
class ProviderRegistryEntry:
    # 变量更新：计算并保存provider_id，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    provider_id: str
    # 变量更新：计算并保存plugin_id，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    plugin_id: str
    # 变量更新：计算并保存registration_status，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    registration_status: PluginRegistrationStatus
    # 变量更新：计算并保存entrypoint，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    entrypoint: str | None
    # 变量更新：计算并保存priority，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    priority: int
    # 变量更新：计算并保存enabled_for_routing，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    enabled_for_routing: bool
    # 变量更新：计算并保存discovery_result_ref，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    discovery_result_ref: str | None
    # 变量更新：计算并保存authentication_reference_ref，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    authentication_reference_ref: str | None
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
        # 迭代处理：依次读取`('provider_id', 'plugin_id', 'notes')`中的元素，并绑定到`field_name`。
        # - 维度变化：每轮处理一个元素，可能向列表、字典或累计值中增加一项。
        # - 为什么这样写：显式逐项校验可以精确指出哪个字段或Provider不符合合同。
        for field_name in ("provider_id", "plugin_id", "notes"):
            # API调用：执行`object.__setattr__(self, field_name, _require_text(getattr(self, field_name), field_name))`以触发注册、写入对象状态或其他显式副作用。
            # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
            # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
            object.__setattr__(
                self,
                field_name,
                _require_text(getattr(self, field_name), field_name),
            )
        # 变量更新：计算并保存status，右侧逻辑为`self.registration_status`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        status = self.registration_status
        # 条件门禁：判断`isinstance(status, str)`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if isinstance(status, str):
            # 变量更新：计算并保存status，右侧逻辑为`PluginRegistrationStatus(status)`。
            # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
            # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
            status = PluginRegistrationStatus(status)
        # API调用：执行`object.__setattr__(self, 'registration_status', status)`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        object.__setattr__(self, "registration_status", status)
        # API调用：执行`object.__setattr__(self, 'entrypoint', _optional_text(self.entrypoint, 'entrypoint'))`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        object.__setattr__(
            self,
            "entrypoint",
            _optional_text(self.entrypoint, "entrypoint"),
        )
        # API调用：执行`_nonnegative_int(self.priority, 'priority')`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        _nonnegative_int(self.priority, "priority")
        # API调用：执行`object.__setattr__(self, 'discovery_result_ref', _optional_text(self.discovery_result_ref, 'disco...`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        object.__setattr__(
            self,
            "discovery_result_ref",
            _optional_text(
                self.discovery_result_ref,
                "discovery_result_ref",
            ),
        )
        # 变量更新：计算并保存auth_ref，右侧逻辑为`_optional_text(self.authentication_reference_ref, 'authentication_reference_ref')`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        auth_ref = _optional_text(
            self.authentication_reference_ref,
            "authentication_reference_ref",
        )
        # 条件门禁：判断`auth_ref is not None`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if auth_ref is not None:
            # 条件门禁：判断`not auth_ref.startswith(SECRET_REFERENCE_PREFIXES)`，条件为真时进入受保护分支。
            # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
            # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
            if not auth_ref.startswith(SECRET_REFERENCE_PREFIXES):
                # 错误阻断：抛出`DataContractError('注册表认证引用必须使用受支持的URI。')`并停止当前路径。
                # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
                # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
                raise DataContractError(
                    "注册表认证引用必须使用受支持的URI。"
                )
            # 条件门禁：判断`_looks_like_secret(auth_ref)`，条件为真时进入受保护分支。
            # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
            # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
            if _looks_like_secret(auth_ref):
                # 错误阻断：抛出`DataContractError('注册表认证引用疑似包含秘密材料。')`并停止当前路径。
                # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
                # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
                raise DataContractError("注册表认证引用疑似包含秘密材料。")
        # API调用：执行`object.__setattr__(self, 'authentication_reference_ref', auth_ref)`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        object.__setattr__(
            self,
            "authentication_reference_ref",
            auth_ref,
        )
        # 条件门禁：判断`self.enabled_for_routing`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if self.enabled_for_routing:
            # 条件门禁：判断`status not in {PluginRegistrationStatus.DISCOVERY_COMPLETE, PluginRegistrationStatus.AVAILABLE}`，条件为真时进入受保护分支。
            # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
            # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
            if status not in {
                PluginRegistrationStatus.DISCOVERY_COMPLETE,
                PluginRegistrationStatus.AVAILABLE,
            }:
                # 错误阻断：抛出`DataContractError('未完成发现的插件不得启用路由。')`并停止当前路径。
                # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
                # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
                raise DataContractError(
                    "未完成发现的插件不得启用路由。"
                )
            # 条件门禁：判断`self.entrypoint is None or self.discovery_result_ref is None`，条件为真时进入受保护分支。
            # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
            # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
            if self.entrypoint is None or self.discovery_result_ref is None:
                # 错误阻断：抛出`DataContractError('启用路由必须具有entrypoint和发现结果引用。')`并停止当前路径。
                # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
                # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
                raise DataContractError(
                    "启用路由必须具有entrypoint和发现结果引用。"
                )


# 定义ProviderPluginRegistry强类型合同，集中保存相关状态、参数和校验规则。
# - 字段task_id：类型str。
# - 字段registry_version：类型str。
# - 字段registry_status：类型str。
# - 字段automatic_activation_allowed：类型bool。
# - 字段entries：类型tuple[ProviderRegistryEntry, ...]。
# - 字段hard_rules：类型tuple[str, ...]。
# - 数据变化：类本身不执行隐式I/O，实例字段只在显式构造、校验或方法调用时变化。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
@dataclass(frozen=True, slots=True)
class ProviderPluginRegistry:
    # 变量更新：计算并保存task_id，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    task_id: str
    # 变量更新：计算并保存registry_version，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    registry_version: str
    # 变量更新：计算并保存registry_status，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    registry_status: str
    # 变量更新：计算并保存automatic_activation_allowed，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    automatic_activation_allowed: bool
    # 变量更新：计算并保存entries，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    entries: tuple[ProviderRegistryEntry, ...]
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
        # 迭代处理：依次读取`('task_id', 'registry_version', 'registry_status')`中的元素，并绑定到`field_name`。
        # - 维度变化：每轮处理一个元素，可能向列表、字典或累计值中增加一项。
        # - 为什么这样写：显式逐项校验可以精确指出哪个字段或Provider不符合合同。
        for field_name in (
            "task_id",
            "registry_version",
            "registry_status",
        ):
            # API调用：执行`object.__setattr__(self, field_name, _require_text(getattr(self, field_name), field_name))`以触发注册、写入对象状态或其他显式副作用。
            # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
            # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
            object.__setattr__(
                self,
                field_name,
                _require_text(getattr(self, field_name), field_name),
            )
        # 条件门禁：判断`self.task_id != 'TASK_020B'`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if self.task_id != "TASK_020B":
            # 错误阻断：抛出`DataContractError('注册表task_id异常。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError("注册表task_id异常。")
        # 条件门禁：判断`self.automatic_activation_allowed`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if self.automatic_activation_allowed:
            # 错误阻断：抛出`DataContractError('注册表不得自动激活插件。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError("注册表不得自动激活插件。")
        # 变量更新：计算并保存provider_ids，右侧逻辑为`[entry.provider_id for entry in self.entries]`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        provider_ids = [entry.provider_id for entry in self.entries]
        # 变量更新：计算并保存plugin_ids，右侧逻辑为`[entry.plugin_id for entry in self.entries]`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        plugin_ids = [entry.plugin_id for entry in self.entries]
        # 条件门禁：判断`not provider_ids or len(provider_ids) != len(set(provider_ids))`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if not provider_ids or len(provider_ids) != len(set(provider_ids)):
            # 错误阻断：抛出`DataContractError('provider_id必须非空且唯一。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError("provider_id必须非空且唯一。")
        # 条件门禁：判断`len(plugin_ids) != len(set(plugin_ids))`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if len(plugin_ids) != len(set(plugin_ids)):
            # 错误阻断：抛出`DataContractError('plugin_id必须唯一。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError("plugin_id必须唯一。")
        # API调用：执行`object.__setattr__(self, 'hard_rules', _unique_texts(self.hard_rules, 'hard_rules', allow_empty=F...`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        object.__setattr__(
            self,
            "hard_rules",
            _unique_texts(
                self.hard_rules,
                "hard_rules",
                allow_empty=False,
            ),
        )

    # 执行entry逻辑，把输入参数转换为受合同约束的结果。
    # - 参数provider_id：类型str；进入函数后按合同校验或参与计算。
    # - 输出：返回类型ProviderRegistryEntry；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
    def entry(self, provider_id: str) -> ProviderRegistryEntry:
        # 变量更新：计算并保存key，右侧逻辑为`_require_text(provider_id, 'provider_id')`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        key = _require_text(provider_id, "provider_id")
        # 迭代处理：依次读取`self.entries`中的元素，并绑定到`entry`。
        # - 维度变化：每轮处理一个元素，可能向列表、字典或累计值中增加一项。
        # - 为什么这样写：显式逐项校验可以精确指出哪个字段或Provider不符合合同。
        for entry in self.entries:
            # 条件门禁：判断`entry.provider_id == key`，条件为真时进入受保护分支。
            # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
            # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
            if entry.provider_id == key:
                # 结果返回：把`entry`交给调用方。
                # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
                # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
                return entry
        # 错误阻断：抛出`DataContractError(f'注册表未登记Provider：{key}')`并停止当前路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
        # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
        raise DataContractError(f"注册表未登记Provider：{key}")


# 定义ProviderQueryRequest强类型合同，集中保存相关状态、参数和校验规则。
# - 字段request_id：类型str。
# - 字段provider_id：类型str。
# - 字段capability：类型str。
# - 字段operation：类型str。
# - 字段usage：类型str。
# - 字段parameters：类型Mapping[str, Any]。
# - 字段maximum_rows：类型int。
# - 数据变化：类本身不执行隐式I/O，实例字段只在显式构造、校验或方法调用时变化。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
@dataclass(frozen=True, slots=True)
class ProviderQueryRequest:
    # 变量更新：计算并保存request_id，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    request_id: str
    # 变量更新：计算并保存provider_id，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    provider_id: str
    # 变量更新：计算并保存capability，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    capability: str
    # 变量更新：计算并保存operation，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    operation: str
    # 变量更新：计算并保存usage，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    usage: str
    # 变量更新：计算并保存parameters，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    parameters: Mapping[str, Any]
    # 变量更新：计算并保存maximum_rows，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    maximum_rows: int

    # 执行__post_init__逻辑，把输入参数转换为受合同约束的结果。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态或模块常量。
    # - 输出：返回类型None；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：在不可变或数据类对象创建后立即校验字段关系，阻止不一致对象进入系统。
    def __post_init__(self) -> None:
        # 迭代处理：依次读取`('request_id', 'provider_id', 'capability', 'operation', 'usage')`中的元素，并绑定到`field_name`。
        # - 维度变化：每轮处理一个元素，可能向列表、字典或累计值中增加一项。
        # - 为什么这样写：显式逐项校验可以精确指出哪个字段或Provider不符合合同。
        for field_name in (
            "request_id",
            "provider_id",
            "capability",
            "operation",
            "usage",
        ):
            # API调用：执行`object.__setattr__(self, field_name, _require_text(getattr(self, field_name), field_name))`以触发注册、写入对象状态或其他显式副作用。
            # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
            # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
            object.__setattr__(
                self,
                field_name,
                _require_text(getattr(self, field_name), field_name),
            )
        # API调用：执行`_positive_int(self.maximum_rows, 'maximum_rows')`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        _positive_int(self.maximum_rows, "maximum_rows")
        # 条件门禁：判断`not isinstance(self.parameters, Mapping)`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if not isinstance(self.parameters, Mapping):
            # 错误阻断：抛出`DataContractError('parameters必须是映射。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError("parameters必须是映射。")


# 定义ProviderQueryBatch强类型合同，集中保存相关状态、参数和校验规则。
# - 字段request_id：类型str。
# - 字段provider_id：类型str。
# - 字段capability：类型str。
# - 字段records：类型tuple[Mapping[str, Any], ...]。
# - 字段next_cursor：类型str | None。
# - 字段source_request_id：类型str。
# - 字段warnings：类型tuple[str, ...]。
# - 数据变化：类本身不执行隐式I/O，实例字段只在显式构造、校验或方法调用时变化。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
@dataclass(frozen=True, slots=True)
class ProviderQueryBatch:
    # 变量更新：计算并保存request_id，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    request_id: str
    # 变量更新：计算并保存provider_id，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    provider_id: str
    # 变量更新：计算并保存capability，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    capability: str
    # 变量更新：计算并保存records，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    records: tuple[Mapping[str, Any], ...]
    # 变量更新：计算并保存next_cursor，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    next_cursor: str | None
    # 变量更新：计算并保存source_request_id，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    source_request_id: str
    # 变量更新：计算并保存warnings，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    warnings: tuple[str, ...]

    # 执行__post_init__逻辑，把输入参数转换为受合同约束的结果。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态或模块常量。
    # - 输出：返回类型None；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：在不可变或数据类对象创建后立即校验字段关系，阻止不一致对象进入系统。
    def __post_init__(self) -> None:
        # 迭代处理：依次读取`('request_id', 'provider_id', 'capability', 'source_request_id')`中的元素，并绑定到`field_name`。
        # - 维度变化：每轮处理一个元素，可能向列表、字典或累计值中增加一项。
        # - 为什么这样写：显式逐项校验可以精确指出哪个字段或Provider不符合合同。
        for field_name in (
            "request_id",
            "provider_id",
            "capability",
            "source_request_id",
        ):
            # API调用：执行`object.__setattr__(self, field_name, _require_text(getattr(self, field_name), field_name))`以触发注册、写入对象状态或其他显式副作用。
            # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
            # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
            object.__setattr__(
                self,
                field_name,
                _require_text(getattr(self, field_name), field_name),
            )
        # 条件门禁：判断`any((not isinstance(item, Mapping) for item in self.records))`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if any(not isinstance(item, Mapping) for item in self.records):
            # 错误阻断：抛出`DataContractError('records必须由映射组成。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError("records必须由映射组成。")
        # API调用：执行`object.__setattr__(self, 'next_cursor', _optional_text(self.next_cursor, 'next_cursor'))`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        object.__setattr__(
            self,
            "next_cursor",
            _optional_text(self.next_cursor, "next_cursor"),
        )
        # API调用：执行`object.__setattr__(self, 'warnings', _unique_texts(self.warnings, 'warnings'))`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        object.__setattr__(
            self,
            "warnings",
            _unique_texts(self.warnings, "warnings"),
        )


# 定义ProviderSubscriptionRequest强类型合同，集中保存相关状态、参数和校验规则。
# - 字段subscription_id：类型str。
# - 字段provider_id：类型str。
# - 字段capability：类型str。
# - 字段symbols：类型tuple[str, ...]。
# - 字段fields：类型tuple[str, ...]。
# - 数据变化：类本身不执行隐式I/O，实例字段只在显式构造、校验或方法调用时变化。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
@dataclass(frozen=True, slots=True)
class ProviderSubscriptionRequest:
    # 变量更新：计算并保存subscription_id，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    subscription_id: str
    # 变量更新：计算并保存provider_id，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    provider_id: str
    # 变量更新：计算并保存capability，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    capability: str
    # 变量更新：计算并保存symbols，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    symbols: tuple[str, ...]
    # 变量更新：计算并保存fields，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    fields: tuple[str, ...]

    # 执行__post_init__逻辑，把输入参数转换为受合同约束的结果。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态或模块常量。
    # - 输出：返回类型None；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：在不可变或数据类对象创建后立即校验字段关系，阻止不一致对象进入系统。
    def __post_init__(self) -> None:
        # 迭代处理：依次读取`('subscription_id', 'provider_id', 'capability')`中的元素，并绑定到`field_name`。
        # - 维度变化：每轮处理一个元素，可能向列表、字典或累计值中增加一项。
        # - 为什么这样写：显式逐项校验可以精确指出哪个字段或Provider不符合合同。
        for field_name in (
            "subscription_id",
            "provider_id",
            "capability",
        ):
            # API调用：执行`object.__setattr__(self, field_name, _require_text(getattr(self, field_name), field_name))`以触发注册、写入对象状态或其他显式副作用。
            # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
            # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
            object.__setattr__(
                self,
                field_name,
                _require_text(getattr(self, field_name), field_name),
            )
        # API调用：执行`object.__setattr__(self, 'symbols', _unique_texts(self.symbols, 'symbols', allow_empty=False))`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        object.__setattr__(
            self,
            "symbols",
            _unique_texts(
                self.symbols,
                "symbols",
                allow_empty=False,
            ),
        )
        # API调用：执行`object.__setattr__(self, 'fields', _unique_texts(self.fields, 'fields', allow_empty=False))`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        object.__setattr__(
            self,
            "fields",
            _unique_texts(
                self.fields,
                "fields",
                allow_empty=False,
            ),
        )


# 所有具体厂商插件必须满足的结构化协议。
# - 状态成员：枚举值或方法共同描述该合同允许的有限状态和行为。
# - 数据变化：类本身不执行隐式I/O，实例字段只在显式构造、校验或方法调用时变化。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
@runtime_checkable
class ProviderPlugin(Protocol):
    """所有具体厂商插件必须满足的结构化协议。"""

    # 执行describe逻辑，把输入参数转换为受合同约束的结果。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态或模块常量。
    # - 输出：返回类型ProviderRegistryEntry；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：返回静态插件身份但保持路由禁用，防止描述阶段自动激活。
    def describe(self) -> ProviderRegistryEntry:
        ...

    # 执行discover逻辑，把输入参数转换为受合同约束的结果。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态或模块常量。
    # - 输出：返回类型ProviderDiscoveryResult；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：把运行时、健康、许可证和能力证据合并成单一发现结果，避免把计划能力误当成真实能力。
    def discover(self) -> ProviderDiscoveryResult:
        ...

    # 执行health_check逻辑，把输入参数转换为受合同约束的结果。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态或模块常量。
    # - 输出：返回类型ProviderHealthSnapshot；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：把底层健康结果翻译为Provider统一状态，便于路由层使用同一判定标准。
    def health_check(self) -> ProviderHealthSnapshot:
        ...

    # 执行open_session逻辑，把输入参数转换为受合同约束的结果。
    # - 参数authentication_reference：类型AuthenticationReference；进入函数后按合同校验或参与计算。
    # - 输出：返回类型None；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：只校验认证引用和环境变量存在性，不把密码写入配置或对象。
    def open_session(
        self,
        authentication_reference: AuthenticationReference,
    ) -> None:
        ...

    # 执行close_session逻辑，把输入参数转换为受合同约束的结果。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态或模块常量。
    # - 输出：返回类型None；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：显式释放可释放的底层会话并更新插件状态，防止关闭后继续查询。
    def close_session(self) -> None:
        ...

    # 执行query_batch逻辑，把输入参数转换为受合同约束的结果。
    # - 参数request：类型ProviderQueryRequest；进入函数后按合同校验或参与计算。
    # - 输出：返回类型ProviderQueryBatch；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：把通用请求委托给现有适配器并转换为统一批次，复用已有安全和查询逻辑。
    def query_batch(
        self,
        request: ProviderQueryRequest,
    ) -> ProviderQueryBatch:
        ...

    # 执行iter_pages逻辑，把输入参数转换为受合同约束的结果。
    # - 参数request：类型ProviderQueryRequest；进入函数后按合同校验或参与计算。
    # - 输出：返回类型Iterator[ProviderQueryBatch]；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
    def iter_pages(
        self,
        request: ProviderQueryRequest,
    ) -> Iterator[ProviderQueryBatch]:
        ...

    # 执行subscribe逻辑，把输入参数转换为受合同约束的结果。
    # - 参数request：类型ProviderSubscriptionRequest；进入函数后按合同校验或参与计算。
    # - 输出：返回类型str；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
    def subscribe(
        self,
        request: ProviderSubscriptionRequest,
    ) -> str:
        ...

    # 执行unsubscribe逻辑，把输入参数转换为受合同约束的结果。
    # - 参数subscription_id：类型str；进入函数后按合同校验或参与计算。
    # - 输出：返回类型None；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
    def unsubscribe(self, subscription_id: str) -> None:
        ...


# 定义ProviderRouteRequest强类型合同，集中保存相关状态、参数和校验规则。
# - 字段capability：类型str。
# - 字段usage：类型str。
# - 字段requires_realtime：类型bool，默认值False。
# - 字段requires_execution：类型bool，默认值False。
# - 数据变化：类本身不执行隐式I/O，实例字段只在显式构造、校验或方法调用时变化。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
@dataclass(frozen=True, slots=True)
class ProviderRouteRequest:
    # 变量更新：计算并保存capability，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    capability: str
    # 变量更新：计算并保存usage，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    usage: str
    # 变量更新：计算并保存requires_realtime，右侧逻辑为`False`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    requires_realtime: bool = False
    # 变量更新：计算并保存requires_execution，右侧逻辑为`False`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    requires_execution: bool = False

    # 执行__post_init__逻辑，把输入参数转换为受合同约束的结果。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态或模块常量。
    # - 输出：返回类型None；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：在不可变或数据类对象创建后立即校验字段关系，阻止不一致对象进入系统。
    def __post_init__(self) -> None:
        # API调用：执行`object.__setattr__(self, 'capability', _require_text(self.capability, 'capability'))`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        object.__setattr__(
            self,
            "capability",
            _require_text(self.capability, "capability"),
        )
        # API调用：执行`object.__setattr__(self, 'usage', _require_text(self.usage, 'usage'))`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        object.__setattr__(
            self,
            "usage",
            _require_text(self.usage, "usage"),
        )


# 定义ProviderRouteCandidate强类型合同，集中保存相关状态、参数和校验规则。
# - 字段provider_id：类型str。
# - 字段plugin_id：类型str。
# - 字段decision：类型RouteDecision。
# - 字段score：类型float。
# - 字段score_breakdown：类型Mapping[str, float]。
# - 字段reasons：类型tuple[str, ...]。
# - 字段warnings：类型tuple[str, ...]。
# - 数据变化：类本身不执行隐式I/O，实例字段只在显式构造、校验或方法调用时变化。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
@dataclass(frozen=True, slots=True)
class ProviderRouteCandidate:
    # 变量更新：计算并保存provider_id，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    provider_id: str
    # 变量更新：计算并保存plugin_id，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    plugin_id: str
    # 变量更新：计算并保存decision，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    decision: RouteDecision
    # 变量更新：计算并保存score，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    score: float
    # 变量更新：计算并保存score_breakdown，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    score_breakdown: Mapping[str, float]
    # 变量更新：计算并保存reasons，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    reasons: tuple[str, ...]
    # 变量更新：计算并保存warnings，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    warnings: tuple[str, ...]

    # 执行__post_init__逻辑，把输入参数转换为受合同约束的结果。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态或模块常量。
    # - 输出：返回类型None；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：在不可变或数据类对象创建后立即校验字段关系，阻止不一致对象进入系统。
    def __post_init__(self) -> None:
        # 迭代处理：依次读取`('provider_id', 'plugin_id')`中的元素，并绑定到`field_name`。
        # - 维度变化：每轮处理一个元素，可能向列表、字典或累计值中增加一项。
        # - 为什么这样写：显式逐项校验可以精确指出哪个字段或Provider不符合合同。
        for field_name in ("provider_id", "plugin_id"):
            # API调用：执行`object.__setattr__(self, field_name, _require_text(getattr(self, field_name), field_name))`以触发注册、写入对象状态或其他显式副作用。
            # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
            # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
            object.__setattr__(
                self,
                field_name,
                _require_text(getattr(self, field_name), field_name),
            )
        # 变量更新：计算并保存decision，右侧逻辑为`self.decision`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        decision = self.decision
        # 条件门禁：判断`isinstance(decision, str)`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if isinstance(decision, str):
            # 变量更新：计算并保存decision，右侧逻辑为`RouteDecision(decision)`。
            # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
            # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
            decision = RouteDecision(decision)
        # API调用：执行`object.__setattr__(self, 'decision', decision)`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        object.__setattr__(self, "decision", decision)
        # 变量更新：计算并保存score，右侧逻辑为`_finite(self.score, 'score')`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        score = _finite(self.score, "score")
        # 条件门禁：判断`score < 0 or score > 100`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if score < 0 or score > 100:
            # 错误阻断：抛出`DataContractError('路由得分必须位于0到100。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError("路由得分必须位于0到100。")
        # API调用：执行`object.__setattr__(self, 'score', score)`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        object.__setattr__(self, "score", score)
        # 变量更新：计算并保存breakdown，右侧逻辑为`{_require_text(key, 'score_breakdown_key'): _finite(value, 'score_breakdown_value') for...`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        breakdown = {
            _require_text(key, "score_breakdown_key"): _finite(
                value,
                "score_breakdown_value",
            )
            for key, value in self.score_breakdown.items()
        }
        # 条件门禁：判断`any((value < 0 for value in breakdown.values()))`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if any(value < 0 for value in breakdown.values()):
            # 错误阻断：抛出`DataContractError('评分分解不得为负。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError("评分分解不得为负。")
        # API调用：执行`object.__setattr__(self, 'score_breakdown', breakdown)`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        object.__setattr__(self, "score_breakdown", breakdown)
        # API调用：执行`object.__setattr__(self, 'reasons', _unique_texts(self.reasons, 'reasons'))`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        object.__setattr__(
            self,
            "reasons",
            _unique_texts(self.reasons, "reasons"),
        )
        # API调用：执行`object.__setattr__(self, 'warnings', _unique_texts(self.warnings, 'warnings'))`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        object.__setattr__(
            self,
            "warnings",
            _unique_texts(self.warnings, "warnings"),
        )
        # 条件门禁：判断`decision is RouteDecision.ELIGIBLE and self.reasons`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if decision is RouteDecision.ELIGIBLE and self.reasons:
            # 错误阻断：抛出`DataContractError('合格候选不得包含阻断原因。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError("合格候选不得包含阻断原因。")
        # 条件门禁：判断`decision is RouteDecision.INELIGIBLE and (not self.reasons)`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if decision is RouteDecision.INELIGIBLE and not self.reasons:
            # 错误阻断：抛出`DataContractError('不合格候选必须说明原因。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError("不合格候选必须说明原因。")


# 定义ProviderPluginProtocolConfig强类型合同，集中保存相关状态、参数和校验规则。
# - 字段task_id：类型str。
# - 字段protocol_version：类型str。
# - 字段protocol_status：类型str。
# - 字段provider_neutral：类型bool。
# - 字段vendor_sdk_import_boundary：类型str。
# - 字段automatic_plugin_activation_allowed：类型bool。
# - 字段secret_material_allowed：类型bool。
# - 字段network_probe_during_validation_allowed：类型bool。
# - 其余字段：另有11项，均在对象创建时统一校验。
# - 数据变化：类本身不执行隐式I/O，实例字段只在显式构造、校验或方法调用时变化。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
@dataclass(frozen=True, slots=True)
class ProviderPluginProtocolConfig:
    # 变量更新：计算并保存task_id，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    task_id: str
    # 变量更新：计算并保存protocol_version，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    protocol_version: str
    # 变量更新：计算并保存protocol_status，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    protocol_status: str
    # 变量更新：计算并保存provider_neutral，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    provider_neutral: bool
    # 变量更新：计算并保存vendor_sdk_import_boundary，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    vendor_sdk_import_boundary: str
    # 变量更新：计算并保存automatic_plugin_activation_allowed，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    automatic_plugin_activation_allowed: bool
    # 变量更新：计算并保存secret_material_allowed，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    secret_material_allowed: bool
    # 变量更新：计算并保存network_probe_during_validation_allowed，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    network_probe_during_validation_allowed: bool
    # 变量更新：计算并保存database_probe_during_validation_allowed，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    database_probe_during_validation_allowed: bool
    # 变量更新：计算并保存required_plugin_methods，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    required_plugin_methods: tuple[str, ...]
    # 变量更新：计算并保存required_discovery_sections，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    required_discovery_sections: tuple[str, ...]
    # 变量更新：计算并保存authentication_reference_prefixes，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    authentication_reference_prefixes: tuple[str, ...]
    # 变量更新：计算并保存registration_statuses_eligible_for_routing，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    registration_statuses_eligible_for_routing: tuple[
        PluginRegistrationStatus,
        ...,
    ]
    # 变量更新：计算并保存discovery_outcomes_eligible_for_routing，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    discovery_outcomes_eligible_for_routing: tuple[
        DiscoveryOutcome,
        ...,
    ]
    # 变量更新：计算并保存health_statuses_eligible_for_routing，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    health_statuses_eligible_for_routing: tuple[
        ProviderHealthStatus,
        ...,
    ]
    # 变量更新：计算并保存capability_statuses_eligible_for_routing，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    capability_statuses_eligible_for_routing: tuple[
        CapabilityImplementationStatus,
        ...,
    ]
    # 变量更新：计算并保存license_decisions_eligible_for_routing，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    license_decisions_eligible_for_routing: tuple[
        LicenseDecision,
        ...,
    ]
    # 变量更新：计算并保存route_score_weights，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    route_score_weights: Mapping[str, float]
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
        # 迭代处理：依次读取`('task_id', 'protocol_version', 'protocol_status', 'vendor_sdk_import_boundary')`中的元素，并绑定到`field_name`。
        # - 维度变化：每轮处理一个元素，可能向列表、字典或累计值中增加一项。
        # - 为什么这样写：显式逐项校验可以精确指出哪个字段或Provider不符合合同。
        for field_name in (
            "task_id",
            "protocol_version",
            "protocol_status",
            "vendor_sdk_import_boundary",
        ):
            # API调用：执行`object.__setattr__(self, field_name, _require_text(getattr(self, field_name), field_name))`以触发注册、写入对象状态或其他显式副作用。
            # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
            # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
            object.__setattr__(
                self,
                field_name,
                _require_text(getattr(self, field_name), field_name),
            )
        # 条件门禁：判断`self.task_id != 'TASK_020B'`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if self.task_id != "TASK_020B":
            # 错误阻断：抛出`DataContractError('协议task_id异常。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError("协议task_id异常。")
        # 条件门禁：判断`not self.provider_neutral`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if not self.provider_neutral:
            # 错误阻断：抛出`DataContractError('协议必须保持供应商中立。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError("协议必须保持供应商中立。")
        # 条件门禁：判断`any((self.automatic_plugin_activation_allowed, self.secret_material_allowed, self.network_probe_d...`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if any(
            (
                self.automatic_plugin_activation_allowed,
                self.secret_material_allowed,
                self.network_probe_during_validation_allowed,
                self.database_probe_during_validation_allowed,
            )
        ):
            # 错误阻断：抛出`DataContractError('TASK_020B安全边界被破坏。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError("TASK_020B安全边界被破坏。")
        # 迭代处理：依次读取`('required_plugin_methods', 'required_discovery_sections', 'authentication_re...`中的元素，并绑定到`field_name`。
        # - 维度变化：每轮处理一个元素，可能向列表、字典或累计值中增加一项。
        # - 为什么这样写：显式逐项校验可以精确指出哪个字段或Provider不符合合同。
        for field_name in (
            "required_plugin_methods",
            "required_discovery_sections",
            "authentication_reference_prefixes",
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
        # 条件门禁：判断`set(self.authentication_reference_prefixes) != set(SECRET_REFERENCE_PREFIXES)`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if set(self.authentication_reference_prefixes) != set(
            SECRET_REFERENCE_PREFIXES
        ):
            # 错误阻断：抛出`DataContractError('认证引用前缀合同异常。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError("认证引用前缀合同异常。")
        # 变量更新：计算并保存weights，右侧逻辑为`{_require_text(key, 'route_score_weight'): _finite(value, 'route_score_weight') for key...`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        weights = {
            _require_text(key, "route_score_weight"): _finite(
                value,
                "route_score_weight",
            )
            for key, value in self.route_score_weights.items()
        }
        # 条件门禁：判断`set(weights) != {'capability', 'discovery', 'health', 'license', 'priority', 'exact_usage'}`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if set(weights) != {
            "capability",
            "discovery",
            "health",
            "license",
            "priority",
            "exact_usage",
        }:
            # 错误阻断：抛出`DataContractError('路由权重维度异常。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError("路由权重维度异常。")
        # 条件门禁：判断`not math.isclose(sum(weights.values()), 100.0, abs_tol=1e-09)`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if not math.isclose(sum(weights.values()), 100.0, abs_tol=1e-9):
            # 错误阻断：抛出`DataContractError('路由权重之和必须为100。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError("路由权重之和必须为100。")
        # API调用：执行`object.__setattr__(self, 'route_score_weights', weights)`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        object.__setattr__(self, "route_score_weights", weights)


# 执行load_provider_plugin_protocol_config逻辑，把输入参数转换为受合同约束的结果。
# - 参数path：类型str | Path；进入函数后按合同校验或参与计算。
# - 输出：返回类型ProviderPluginProtocolConfig；调用方按该类型继续校验、路由或序列化。
# - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
def load_provider_plugin_protocol_config(
    path: str | Path,
) -> ProviderPluginProtocolConfig:
    # 变量更新：计算并保存raw，右侧逻辑为`json.loads(Path(path).read_text(encoding='utf-8'))`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    # 条件门禁：判断`not isinstance(raw, dict)`，条件为真时进入受保护分支。
    # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
    # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
    if not isinstance(raw, dict):
        # 错误阻断：抛出`DataContractError('插件协议根节点必须是对象。')`并停止当前路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
        # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
        raise DataContractError("插件协议根节点必须是对象。")
    # 结果返回：把`ProviderPluginProtocolConfig(task_id=str(raw['task_id']), protocol_version=str(raw['protocol_vers...`交给调用方。
    # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
    # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
    return ProviderPluginProtocolConfig(
        task_id=str(raw["task_id"]),
        protocol_version=str(raw["protocol_version"]),
        protocol_status=str(raw["protocol_status"]),
        provider_neutral=bool(raw["provider_neutral"]),
        vendor_sdk_import_boundary=str(
            raw["vendor_sdk_import_boundary"]
        ),
        automatic_plugin_activation_allowed=bool(
            raw["automatic_plugin_activation_allowed"]
        ),
        secret_material_allowed=bool(raw["secret_material_allowed"]),
        network_probe_during_validation_allowed=bool(
            raw["network_probe_during_validation_allowed"]
        ),
        database_probe_during_validation_allowed=bool(
            raw["database_probe_during_validation_allowed"]
        ),
        required_plugin_methods=tuple(
            str(value) for value in raw["required_plugin_methods"]
        ),
        required_discovery_sections=tuple(
            str(value) for value in raw["required_discovery_sections"]
        ),
        authentication_reference_prefixes=tuple(
            str(value)
            for value in raw["authentication_reference_prefixes"]
        ),
        registration_statuses_eligible_for_routing=tuple(
            PluginRegistrationStatus(str(value))
            for value in raw[
                "registration_statuses_eligible_for_routing"
            ]
        ),
        discovery_outcomes_eligible_for_routing=tuple(
            DiscoveryOutcome(str(value))
            for value in raw[
                "discovery_outcomes_eligible_for_routing"
            ]
        ),
        health_statuses_eligible_for_routing=tuple(
            ProviderHealthStatus(str(value))
            for value in raw[
                "health_statuses_eligible_for_routing"
            ]
        ),
        capability_statuses_eligible_for_routing=tuple(
            CapabilityImplementationStatus(str(value))
            for value in raw[
                "capability_statuses_eligible_for_routing"
            ]
        ),
        license_decisions_eligible_for_routing=tuple(
            LicenseDecision(str(value))
            for value in raw[
                "license_decisions_eligible_for_routing"
            ]
        ),
        route_score_weights={
            str(key): float(value)
            for key, value in raw["route_score_weights"].items()
        },
        hard_rules=tuple(str(value) for value in raw["hard_rules"]),
    )


# 执行load_provider_plugin_registry逻辑，把输入参数转换为受合同约束的结果。
# - 参数path：类型str | Path；进入函数后按合同校验或参与计算。
# - 输出：返回类型ProviderPluginRegistry；调用方按该类型继续校验、路由或序列化。
# - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
def load_provider_plugin_registry(
    path: str | Path,
) -> ProviderPluginRegistry:
    # 变量更新：计算并保存raw，右侧逻辑为`json.loads(Path(path).read_text(encoding='utf-8'))`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    # 条件门禁：判断`not isinstance(raw, dict)`，条件为真时进入受保护分支。
    # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
    # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
    if not isinstance(raw, dict):
        # 错误阻断：抛出`DataContractError('插件注册表根节点必须是对象。')`并停止当前路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
        # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
        raise DataContractError("插件注册表根节点必须是对象。")
    # 变量更新：计算并保存entries，右侧逻辑为`tuple((ProviderRegistryEntry(provider_id=str(item['provider_id']), plugin_id=str(item['...`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    entries = tuple(
        ProviderRegistryEntry(
            provider_id=str(item["provider_id"]),
            plugin_id=str(item["plugin_id"]),
            registration_status=PluginRegistrationStatus(
                str(item["registration_status"])
            ),
            entrypoint=(
                str(item["entrypoint"])
                if item["entrypoint"] is not None
                else None
            ),
            priority=int(item["priority"]),
            enabled_for_routing=bool(item["enabled_for_routing"]),
            discovery_result_ref=(
                str(item["discovery_result_ref"])
                if item["discovery_result_ref"] is not None
                else None
            ),
            authentication_reference_ref=(
                str(item["authentication_reference_ref"])
                if item["authentication_reference_ref"] is not None
                else None
            ),
            notes=str(item["notes"]),
        )
        for item in raw["entries"]
    )
    # 结果返回：把`ProviderPluginRegistry(task_id=str(raw['task_id']), registry_version=str(raw['registry_version'])...`交给调用方。
    # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
    # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
    return ProviderPluginRegistry(
        task_id=str(raw["task_id"]),
        registry_version=str(raw["registry_version"]),
        registry_status=str(raw["registry_status"]),
        automatic_activation_allowed=bool(
            raw["automatic_activation_allowed"]
        ),
        entries=entries,
        hard_rules=tuple(str(value) for value in raw["hard_rules"]),
    )


# 执行build_provider_route_candidates逻辑，把输入参数转换为受合同约束的结果。
# - 关键字参数matrix：类型ProviderCapabilityMatrix，必须显式提供；用于控制本次调用行为。
# - 关键字参数registry：类型ProviderPluginRegistry，必须显式提供；用于控制本次调用行为。
# - 关键字参数protocol：类型ProviderPluginProtocolConfig，必须显式提供；用于控制本次调用行为。
# - 关键字参数discovery_results：类型Mapping[str, ProviderDiscoveryResult]，必须显式提供；用于控制本次调用行为。
# - 关键字参数request：类型ProviderRouteRequest，必须显式提供；用于控制本次调用行为。
# - 输出：返回类型tuple[ProviderRouteCandidate, ...]；调用方按该类型继续校验、路由或序列化。
# - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
# - 为什么这样写：先执行硬门禁再计算可解释评分，避免高分供应商绕过许可证或健康限制。
def build_provider_route_candidates(
    *,
    matrix: ProviderCapabilityMatrix,
    registry: ProviderPluginRegistry,
    protocol: ProviderPluginProtocolConfig,
    discovery_results: Mapping[str, ProviderDiscoveryResult],
    request: ProviderRouteRequest,
) -> tuple[ProviderRouteCandidate, ...]:
    # 条件门禁：判断`request.capability not in matrix.capability_catalog`，条件为真时进入受保护分支。
    # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
    # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
    if request.capability not in matrix.capability_catalog:
        # 错误阻断：抛出`DataContractError(f'能力矩阵未登记请求能力：{request.capability}')`并停止当前路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
        # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
        raise DataContractError(
            f"能力矩阵未登记请求能力：{request.capability}"
        )

    # 变量更新：计算并保存candidates，右侧逻辑为`[]`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    candidates: list[ProviderRouteCandidate] = []
    # 迭代处理：依次读取`registry.entries`中的元素，并绑定到`entry`。
    # - 维度变化：每轮处理一个元素，可能向列表、字典或累计值中增加一项。
    # - 为什么这样写：显式逐项校验可以精确指出哪个字段或Provider不符合合同。
    for entry in registry.entries:
        # 变量更新：计算并保存target，右侧逻辑为`matrix.provider(entry.provider_id)`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        target = matrix.provider(entry.provider_id)
        # 变量更新：计算并保存discovery，右侧逻辑为`discovery_results.get(entry.provider_id)`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        discovery = discovery_results.get(entry.provider_id)
        # 变量更新：计算并保存reasons，右侧逻辑为`[]`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        reasons: list[str] = []
        # 变量更新：计算并保存warnings，右侧逻辑为`[]`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        warnings: list[str] = []
        # 变量更新：计算并保存breakdown，右侧逻辑为`{key: 0.0 for key in protocol.route_score_weights}`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 固定数值：本表达式包含0.0；来源是当前项目既有合同或算法定义，迁移注释不改变其数值。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        breakdown = {
            key: 0.0 for key in protocol.route_score_weights
        }

        # 条件门禁：判断`not entry.enabled_for_routing`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if not entry.enabled_for_routing:
            # API调用：执行`reasons.append('REGISTRY_ROUTING_DISABLED')`以触发注册、写入对象状态或其他显式副作用。
            # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
            # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
            reasons.append("REGISTRY_ROUTING_DISABLED")
        # 条件门禁：判断`entry.registration_status not in protocol.registration_statuses_eligible_for_routing`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if entry.registration_status not in (
            protocol.registration_statuses_eligible_for_routing
        ):
            # API调用：执行`reasons.append('REGISTRATION_STATUS_NOT_ELIGIBLE')`以触发注册、写入对象状态或其他显式副作用。
            # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
            # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
            reasons.append("REGISTRATION_STATUS_NOT_ELIGIBLE")
        # 条件门禁：判断`entry.entrypoint is None`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if entry.entrypoint is None:
            # API调用：执行`reasons.append('PLUGIN_ENTRYPOINT_MISSING')`以触发注册、写入对象状态或其他显式副作用。
            # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
            # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
            reasons.append("PLUGIN_ENTRYPOINT_MISSING")
        # 条件门禁：判断`discovery is None`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if discovery is None:
            # API调用：执行`reasons.append('DISCOVERY_RESULT_MISSING')`以触发注册、写入对象状态或其他显式副作用。
            # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
            # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
            reasons.append("DISCOVERY_RESULT_MISSING")
        # 备用分支：当前面的条件不满足时执行此路径。
        # - 为什么这样写：显式覆盖互斥状态，避免未处理输入静默落空。
        else:
            # 条件门禁：判断`discovery.provider_id != entry.provider_id`，条件为真时进入受保护分支。
            # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
            # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
            if discovery.provider_id != entry.provider_id:
                # API调用：执行`reasons.append('DISCOVERY_PROVIDER_MISMATCH')`以触发注册、写入对象状态或其他显式副作用。
                # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
                # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
                reasons.append("DISCOVERY_PROVIDER_MISMATCH")
            # 条件门禁：判断`discovery.plugin_id != entry.plugin_id`，条件为真时进入受保护分支。
            # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
            # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
            if discovery.plugin_id != entry.plugin_id:
                # API调用：执行`reasons.append('DISCOVERY_PLUGIN_MISMATCH')`以触发注册、写入对象状态或其他显式副作用。
                # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
                # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
                reasons.append("DISCOVERY_PLUGIN_MISMATCH")
            # 条件门禁：判断`discovery.outcome not in protocol.discovery_outcomes_eligible_for_routing`，条件为真时进入受保护分支。
            # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
            # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
            if discovery.outcome not in (
                protocol.discovery_outcomes_eligible_for_routing
            ):
                # API调用：执行`reasons.append('DISCOVERY_OUTCOME_NOT_ELIGIBLE')`以触发注册、写入对象状态或其他显式副作用。
                # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
                # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
                reasons.append("DISCOVERY_OUTCOME_NOT_ELIGIBLE")
            # 备用分支：当前面的条件不满足时执行此路径。
            # - 为什么这样写：显式覆盖互斥状态，避免未处理输入静默落空。
            else:
                # 变量更新：计算并保存breakdown['discovery']，右侧逻辑为`protocol.route_score_weights['discovery']`。
                # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
                # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
                breakdown["discovery"] = protocol.route_score_weights[
                    "discovery"
                ]

            # 变量更新：计算并保存capability_status，右侧逻辑为`discovery.capabilities.get(request.capability)`。
            # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
            # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
            capability_status = discovery.capabilities.get(
                request.capability
            )
            # 条件门禁：判断`capability_status not in protocol.capability_statuses_eligible_for_routing`，条件为真时进入受保护分支。
            # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
            # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
            if capability_status not in (
                protocol.capability_statuses_eligible_for_routing
            ):
                # API调用：执行`reasons.append('CAPABILITY_NOT_VERIFIED')`以触发注册、写入对象状态或其他显式副作用。
                # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
                # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
                reasons.append("CAPABILITY_NOT_VERIFIED")
            # 备用分支：当前面的条件不满足时执行此路径。
            # - 为什么这样写：显式覆盖互斥状态，避免未处理输入静默落空。
            else:
                # 变量更新：计算并保存breakdown['capability']，右侧逻辑为`protocol.route_score_weights['capability']`。
                # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
                # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
                breakdown["capability"] = protocol.route_score_weights[
                    "capability"
                ]

            # 条件门禁：判断`discovery.health.status not in protocol.health_statuses_eligible_for_routing`，条件为真时进入受保护分支。
            # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
            # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
            if discovery.health.status not in (
                protocol.health_statuses_eligible_for_routing
            ):
                # API调用：执行`reasons.append('HEALTH_NOT_ELIGIBLE')`以触发注册、写入对象状态或其他显式副作用。
                # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
                # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
                reasons.append("HEALTH_NOT_ELIGIBLE")
            # 备用分支：当前面的条件不满足时执行此路径。
            # - 为什么这样写：显式覆盖互斥状态，避免未处理输入静默落空。
            # 条件门禁：判断`discovery.health.status is ProviderHealthStatus.HEALTHY`，条件为真时进入受保护分支。
            # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
            # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
            elif discovery.health.status is ProviderHealthStatus.HEALTHY:
                # 变量更新：计算并保存breakdown['health']，右侧逻辑为`protocol.route_score_weights['health']`。
                # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
                # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
                breakdown["health"] = protocol.route_score_weights[
                    "health"
                ]
            # 备用分支：当前面的条件不满足时执行此路径。
            # - 为什么这样写：显式覆盖互斥状态，避免未处理输入静默落空。
            else:
                # 变量更新：计算并保存breakdown['health']，右侧逻辑为`protocol.route_score_weights['health'] * 0.5`。
                # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
                # - 固定数值：本表达式包含0.5；来源是当前项目既有合同或算法定义，迁移注释不改变其数值。
                # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
                breakdown["health"] = (
                    protocol.route_score_weights["health"] * 0.5
                )
                # API调用：执行`warnings.append('PROVIDER_HEALTH_DEGRADED')`以触发注册、写入对象状态或其他显式副作用。
                # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
                # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
                warnings.append("PROVIDER_HEALTH_DEGRADED")

            # 变量更新：计算并保存license_boundary，右侧逻辑为`discovery.license_boundary`。
            # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
            # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
            license_boundary = discovery.license_boundary
            # 条件门禁：判断`license_boundary.decision not in protocol.license_decisions_eligible_for_routing`，条件为真时进入受保护分支。
            # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
            # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
            if license_boundary.decision not in (
                protocol.license_decisions_eligible_for_routing
            ):
                # API调用：执行`reasons.append('LICENSE_NOT_ALLOWED')`以触发注册、写入对象状态或其他显式副作用。
                # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
                # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
                reasons.append("LICENSE_NOT_ALLOWED")
            # 备用分支：当前面的条件不满足时执行此路径。
            # - 为什么这样写：显式覆盖互斥状态，避免未处理输入静默落空。
            # 条件门禁：判断`request.usage not in license_boundary.permitted_usages`，条件为真时进入受保护分支。
            # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
            # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
            elif request.usage not in license_boundary.permitted_usages:
                # API调用：执行`reasons.append('USAGE_NOT_LICENSED')`以触发注册、写入对象状态或其他显式副作用。
                # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
                # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
                reasons.append("USAGE_NOT_LICENSED")
            # 备用分支：当前面的条件不满足时执行此路径。
            # - 为什么这样写：显式覆盖互斥状态，避免未处理输入静默落空。
            else:
                # 变量更新：计算并保存breakdown['license']，右侧逻辑为`protocol.route_score_weights['license']`。
                # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
                # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
                breakdown["license"] = protocol.route_score_weights[
                    "license"
                ]
                # 变量更新：计算并保存breakdown['exact_usage']，右侧逻辑为`protocol.route_score_weights['exact_usage']`。
                # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
                # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
                breakdown["exact_usage"] = (
                    protocol.route_score_weights["exact_usage"]
                )

            # 条件门禁：判断`request.requires_realtime and discovery.subscription_policy.mode is SubscriptionMode.NONE`，条件为真时进入受保护分支。
            # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
            # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
            if (
                request.requires_realtime
                and discovery.subscription_policy.mode
                is SubscriptionMode.NONE
            ):
                # API调用：执行`reasons.append('REALTIME_SUBSCRIPTION_NOT_SUPPORTED')`以触发注册、写入对象状态或其他显式副作用。
                # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
                # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
                reasons.append("REALTIME_SUBSCRIPTION_NOT_SUPPORTED")

        # 条件门禁：判断`request.requires_execution`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if request.requires_execution:
            # 条件门禁：判断`request.capability not in _EXECUTION_CAPABILITIES`，条件为真时进入受保护分支。
            # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
            # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
            if request.capability not in _EXECUTION_CAPABILITIES:
                # API调用：执行`reasons.append('EXECUTION_REQUEST_CAPABILITY_MISMATCH')`以触发注册、写入对象状态或其他显式副作用。
                # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
                # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
                reasons.append("EXECUTION_REQUEST_CAPABILITY_MISMATCH")
            # 条件门禁：判断`not target.execution_capability`，条件为真时进入受保护分支。
            # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
            # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
            if not target.execution_capability:
                # API调用：执行`reasons.append('PROVIDER_NOT_EXECUTION_CAPABLE')`以触发注册、写入对象状态或其他显式副作用。
                # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
                # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
                reasons.append("PROVIDER_NOT_EXECUTION_CAPABLE")
        # 备用分支：当前面的条件不满足时执行此路径。
        # - 为什么这样写：显式覆盖互斥状态，避免未处理输入静默落空。
        # 条件门禁：判断`request.capability in _EXECUTION_CAPABILITIES`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        elif request.capability in _EXECUTION_CAPABILITIES:
            # API调用：执行`reasons.append('EXECUTION_CAPABILITY_REQUIRES_EXPLICIT_FLAG')`以触发注册、写入对象状态或其他显式副作用。
            # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
            # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
            reasons.append("EXECUTION_CAPABILITY_REQUIRES_EXPLICIT_FLAG")

        # 条件门禁：判断`target.lifecycle not in {ProviderLifecycle.REAL_ACCEPTED, ProviderLifecycle.ACTIVATED}`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if target.lifecycle not in {
            ProviderLifecycle.REAL_ACCEPTED,
            ProviderLifecycle.ACTIVATED,
        }:
            # API调用：执行`reasons.append('PROVIDER_LIFECYCLE_NOT_ACCEPTED')`以触发注册、写入对象状态或其他显式副作用。
            # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
            # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
            reasons.append("PROVIDER_LIFECYCLE_NOT_ACCEPTED")

        # 条件门禁：判断`target.discovery_status not in {ProviderDiscoveryStatus.VERIFIED_IN_PROJECT, ProviderDiscoverySta...`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if target.discovery_status not in {
            ProviderDiscoveryStatus.VERIFIED_IN_PROJECT,
            ProviderDiscoveryStatus.DISCOVERY_COMPLETE,
        }:
            # API调用：执行`reasons.append('MATRIX_DISCOVERY_NOT_COMPLETE')`以触发注册、写入对象状态或其他显式副作用。
            # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
            # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
            reasons.append("MATRIX_DISCOVERY_NOT_COMPLETE")

        # 变量更新：计算并保存priority_score，右侧逻辑为`protocol.route_score_weights['priority'] * (max(0.0, 100.0 - float(entry.priority)) / 1...`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 固定数值：本表达式包含100.0, 0.0, 100.0；来源是当前项目既有合同或算法定义，迁移注释不改变其数值。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        priority_score = protocol.route_score_weights["priority"] * (
            max(0.0, 100.0 - float(entry.priority)) / 100.0
        )
        # 变量更新：计算并保存breakdown['priority']，右侧逻辑为`priority_score`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        breakdown["priority"] = priority_score

        # 变量更新：计算并保存reasons，右侧逻辑为`list(dict.fromkeys(reasons))`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        reasons = list(dict.fromkeys(reasons))
        # 变量更新：计算并保存warnings，右侧逻辑为`list(dict.fromkeys(warnings))`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        warnings = list(dict.fromkeys(warnings))
        # 条件门禁：判断`reasons`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if reasons:
            # 变量更新：计算并保存decision，右侧逻辑为`RouteDecision.INELIGIBLE`。
            # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
            # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
            decision = RouteDecision.INELIGIBLE
            # 变量更新：计算并保存score，右侧逻辑为`0.0`。
            # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
            # - 固定数值：本表达式包含0.0；来源是当前项目既有合同或算法定义，迁移注释不改变其数值。
            # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
            score = 0.0
            # 变量更新：计算并保存breakdown，右侧逻辑为`{key: 0.0 for key in breakdown}`。
            # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
            # - 固定数值：本表达式包含0.0；来源是当前项目既有合同或算法定义，迁移注释不改变其数值。
            # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
            breakdown = {key: 0.0 for key in breakdown}
        # 备用分支：当前面的条件不满足时执行此路径。
        # - 为什么这样写：显式覆盖互斥状态，避免未处理输入静默落空。
        else:
            # 变量更新：计算并保存decision，右侧逻辑为`RouteDecision.ELIGIBLE`。
            # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
            # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
            decision = RouteDecision.ELIGIBLE
            # 变量更新：计算并保存score，右侧逻辑为`sum(breakdown.values())`。
            # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
            # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
            score = sum(breakdown.values())

        # API调用：执行`candidates.append(ProviderRouteCandidate(provider_id=entry.provider_id, plugin_id=entry.plugin_id...`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        candidates.append(
            ProviderRouteCandidate(
                provider_id=entry.provider_id,
                plugin_id=entry.plugin_id,
                decision=decision,
                score=score,
                score_breakdown=breakdown,
                reasons=tuple(reasons),
                warnings=tuple(warnings),
            )
        )

    # 结果返回：把`tuple(sorted(candidates, key=lambda item: (item.decision is not RouteDecision.ELIGIBLE, -item.sco...`交给调用方。
    # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
    # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
    return tuple(
        sorted(
            candidates,
            key=lambda item: (
                item.decision is not RouteDecision.ELIGIBLE,
                -item.score,
                item.provider_id,
            ),
        )
    )


# 执行dataclass_to_json_safe逻辑，把输入参数转换为受合同约束的结果。
# - 参数value：类型Any；进入函数后按合同校验或参与计算。
# - 输出：返回类型Any；调用方按该类型继续校验、路由或序列化。
# - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
def dataclass_to_json_safe(value: Any) -> Any:
    # 条件门禁：判断`isinstance(value, Enum)`，条件为真时进入受保护分支。
    # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
    # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
    if isinstance(value, Enum):
        # 结果返回：把`value.value`交给调用方。
        # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
        # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
        return value.value
    # 条件门禁：判断`isinstance(value, datetime)`，条件为真时进入受保护分支。
    # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
    # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
    if isinstance(value, datetime):
        # 结果返回：把`value.isoformat()`交给调用方。
        # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
        # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
        return value.isoformat()
    # 条件门禁：判断`isinstance(value, tuple)`，条件为真时进入受保护分支。
    # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
    # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
    if isinstance(value, tuple):
        # 结果返回：把`[dataclass_to_json_safe(item) for item in value]`交给调用方。
        # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
        # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
        return [dataclass_to_json_safe(item) for item in value]
    # 条件门禁：判断`isinstance(value, list)`，条件为真时进入受保护分支。
    # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
    # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
    if isinstance(value, list):
        # 结果返回：把`[dataclass_to_json_safe(item) for item in value]`交给调用方。
        # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
        # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
        return [dataclass_to_json_safe(item) for item in value]
    # 条件门禁：判断`isinstance(value, Mapping)`，条件为真时进入受保护分支。
    # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
    # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
    if isinstance(value, Mapping):
        # 结果返回：把`{str(key): dataclass_to_json_safe(item) for key, item in value.items()}`交给调用方。
        # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
        # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
        return {
            str(key): dataclass_to_json_safe(item)
            for key, item in value.items()
        }
    # 结果返回：把`value`交给调用方。
    # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
    # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
    return value


# 执行object_to_dict逻辑，把输入参数转换为受合同约束的结果。
# - 参数value：类型Any；进入函数后按合同校验或参与计算。
# - 输出：返回类型dict[str, Any]；调用方按该类型继续校验、路由或序列化。
# - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
def object_to_dict(value: Any) -> dict[str, Any]:
    # 条件门禁：判断`not hasattr(value, '__dataclass_fields__')`，条件为真时进入受保护分支。
    # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
    # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
    if not hasattr(value, "__dataclass_fields__"):
        # 错误阻断：抛出`DataContractError('对象不是dataclass。')`并停止当前路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
        # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
        raise DataContractError("对象不是dataclass。")
    # 结果返回：把`dataclass_to_json_safe(asdict(value))`交给调用方。
    # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
    # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
    return dataclass_to_json_safe(asdict(value))
