# 模块总览：A股量化项目的最小数据接入契约。
# - 输入输出：本模块通过强类型对象和纯函数交换数据，不在导入阶段执行隐式网络或数据库写入。
# - 数据变化：只有显式构造、校验、加载或方法调用才会产生新对象或更新受控状态。
# - 为什么这样写：先说明模块边界，读者可以在阅读实现前理解职责、风险和复用方式。
"""A股量化项目的最小数据接入契约。

本模块只定义不同数据来源和下游模块之间交换数据时必须遵守的
标准接口、状态和数据结构。

当前版本不连接 DolphinDB，不读取真实数据，也不执行具体 ETL 逻辑。
"""

# 依赖导入：加载标准库、类型工具和项目内合同，供下方数据结构与校验逻辑复用。
# - 标准库只提供解析、数学、时间、路径和类型能力；项目模块提供统一异常与上游合同。
# - 为什么这样写：集中导入让依赖边界清晰，并避免在函数内部重复加载同一模块。
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4


# 数据来源类型。
# - 状态成员：枚举值或方法共同描述该合同允许的有限状态和行为。
# - 数据变化：类本身不执行隐式I/O，实例字段只在显式构造、校验或方法调用时变化。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
class SourceType(str, Enum):
    """数据来源类型。"""

    # 变量更新：计算并保存DOLPHINDB，右侧逻辑为`'DOLPHINDB'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    DOLPHINDB = "DOLPHINDB"
    # 变量更新：计算并保存DATABASE，右侧逻辑为`'DATABASE'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    DATABASE = "DATABASE"
    # 变量更新：计算并保存FILE，右侧逻辑为`'FILE'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    FILE = "FILE"
    # 变量更新：计算并保存API，右侧逻辑为`'API'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    API = "API"
    # 变量更新：计算并保存MANUAL，右侧逻辑为`'MANUAL'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    MANUAL = "MANUAL"
    # 变量更新：计算并保存OTHER，右侧逻辑为`'OTHER'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    OTHER = "OTHER"


# 来源字段映射到标准字段时的状态。
# - 状态成员：枚举值或方法共同描述该合同允许的有限状态和行为。
# - 数据变化：类本身不执行隐式I/O，实例字段只在显式构造、校验或方法调用时变化。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
class MappingStatus(str, Enum):
    """来源字段映射到标准字段时的状态。"""

    # 变量更新：计算并保存MAPPED，右侧逻辑为`'MAPPED'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    MAPPED = "MAPPED"
    # 变量更新：计算并保存UNMAPPED，右侧逻辑为`'UNMAPPED'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    UNMAPPED = "UNMAPPED"
    # 变量更新：计算并保存WARNING，右侧逻辑为`'WARNING'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    WARNING = "WARNING"
    # 变量更新：计算并保存FAILED，右侧逻辑为`'FAILED'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    FAILED = "FAILED"
    # 变量更新：计算并保存PENDING_CONFIRMATION，右侧逻辑为`'PENDING_CONFIRMATION'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    PENDING_CONFIRMATION = "PENDING_CONFIRMATION"


# 数据质量检查状态。
# - 状态成员：枚举值或方法共同描述该合同允许的有限状态和行为。
# - 数据变化：类本身不执行隐式I/O，实例字段只在显式构造、校验或方法调用时变化。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
class QualityStatus(str, Enum):
    """数据质量检查状态。"""

    # 变量更新：计算并保存PASSED，右侧逻辑为`'PASSED'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    PASSED = "PASSED"
    # 变量更新：计算并保存WARNING，右侧逻辑为`'WARNING'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    WARNING = "WARNING"
    # 变量更新：计算并保存FAILED，右侧逻辑为`'FAILED'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    FAILED = "FAILED"
    # 变量更新：计算并保存PENDING_CONFIRMATION，右侧逻辑为`'PENDING_CONFIRMATION'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    PENDING_CONFIRMATION = "PENDING_CONFIRMATION"


# 数据质量问题严重级别。
# - 状态成员：枚举值或方法共同描述该合同允许的有限状态和行为。
# - 数据变化：类本身不执行隐式I/O，实例字段只在显式构造、校验或方法调用时变化。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
class QualityLevel(str, Enum):
    """数据质量问题严重级别。"""

    # 变量更新：计算并保存INFO，右侧逻辑为`'INFO'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    INFO = "INFO"
    # 变量更新：计算并保存WARNING，右侧逻辑为`'WARNING'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    WARNING = "WARNING"
    # 变量更新：计算并保存ERROR，右侧逻辑为`'ERROR'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    ERROR = "ERROR"
    # 变量更新：计算并保存CRITICAL，右侧逻辑为`'CRITICAL'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    CRITICAL = "CRITICAL"


# 待人工确认事项的处理状态。
# - 状态成员：枚举值或方法共同描述该合同允许的有限状态和行为。
# - 数据变化：类本身不执行隐式I/O，实例字段只在显式构造、校验或方法调用时变化。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
class ConfirmationStatus(str, Enum):
    """待人工确认事项的处理状态。"""

    # 变量更新：计算并保存OPEN，右侧逻辑为`'OPEN'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    OPEN = "OPEN"
    # 变量更新：计算并保存RESOLVED，右侧逻辑为`'RESOLVED'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    RESOLVED = "RESOLVED"
    # 变量更新：计算并保存REJECTED，右侧逻辑为`'REJECTED'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    REJECTED = "REJECTED"


# 待确认事项对下游流程的阻断程度。
# - 状态成员：枚举值或方法共同描述该合同允许的有限状态和行为。
# - 数据变化：类本身不执行隐式I/O，实例字段只在显式构造、校验或方法调用时变化。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
class BlockingLevel(str, Enum):
    """待确认事项对下游流程的阻断程度。"""

    # 变量更新：计算并保存NONE，右侧逻辑为`'NONE'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    NONE = "NONE"
    # 变量更新：计算并保存WARNING，右侧逻辑为`'WARNING'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    WARNING = "WARNING"
    # 变量更新：计算并保存BLOCKING，右侧逻辑为`'BLOCKING'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    BLOCKING = "BLOCKING"


# 数据契约违反约定时抛出的基础异常。
# - 状态成员：枚举值或方法共同描述该合同允许的有限状态和行为。
# - 数据变化：类本身不执行隐式I/O，实例字段只在显式构造、校验或方法调用时变化。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
class DataContractError(ValueError):
    """数据契约违反约定时抛出的基础异常。"""


# 生成字符串形式的唯一标识。
# - 输入：本逻辑不接收外部业务参数，只读取对象状态或模块常量。
# - 输出：返回类型str；调用方按该类型继续校验、路由或序列化。
# - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
# - 为什么这样写：使用UUID4生成低碰撞批次标识，使多来源并发读取仍可追踪。
def _new_id() -> str:
    """生成字符串形式的唯一标识。"""

    # 结果返回：把`str(uuid4())`交给调用方。
    # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
    # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
    return str(uuid4())


# 生成带 UTC 时区的当前时间。
# - 输入：本逻辑不接收外部业务参数，只读取对象状态或模块常量。
# - 输出：返回类型datetime；调用方按该类型继续校验、路由或序列化。
# - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
# - 为什么这样写：统一使用带时区UTC时间，避免本地时区和夏令时造成时点歧义。
def _utc_now() -> datetime:
    """生成带 UTC 时区的当前时间。"""

    # 结果返回：把`datetime.now(timezone.utc)`交给调用方。
    # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
    # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
    return datetime.now(timezone.utc)


# 检查必填字符串是否为空。
# - 参数value：类型str；进入函数后按合同校验或参与计算。
# - 参数field_name：类型str；进入函数后按合同校验或参与计算。
# - 输出：返回类型None；调用方按该类型继续校验、路由或序列化。
# - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
# - 为什么这样写：在对象创建入口阻断空标识，避免后续错误只能在更深层才暴露。
def _require_non_empty(value: str, field_name: str) -> None:
    """检查必填字符串是否为空。"""

    # 条件门禁：判断`not isinstance(value, str) or not value.strip()`，条件为真时进入受保护分支。
    # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
    # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
    if not isinstance(value, str) or not value.strip():
        # 错误阻断：抛出`DataContractError(f'{field_name} 不能为空。')`并停止当前路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
        # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
        raise DataContractError(f"{field_name} 不能为空。")


# 从数据来源读取后、尚未修改语义的原始数据批次。
# - 字段source_id：类型str。
# - 字段source_type：类型SourceType。
# - 字段source_object_name：类型str。
# - 字段raw_fields：类型list[str]。
# - 字段records：类型list[dict[str, Any]]。
# - 字段source_location：类型str | None，默认值None。
# - 字段data_version：类型str | None，默认值None。
# - 字段data_start：类型datetime | None，默认值None。
# - 其余字段：另有5项，均在对象创建时统一校验。
# - 数据变化：类本身不执行隐式I/O，实例字段只在显式构造、校验或方法调用时变化。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
@dataclass(slots=True)
class RawDataBatch:
    """从数据来源读取后、尚未修改语义的原始数据批次。"""

    # 变量更新：计算并保存source_id，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    source_id: str
    # 变量更新：计算并保存source_type，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    source_type: SourceType
    # 变量更新：计算并保存source_object_name，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    source_object_name: str
    # 变量更新：计算并保存raw_fields，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    raw_fields: list[str]
    # 变量更新：计算并保存records，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    records: list[dict[str, Any]]
    # 变量更新：计算并保存source_location，右侧逻辑为`None`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    source_location: str | None = None
    # 变量更新：计算并保存data_version，右侧逻辑为`None`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    data_version: str | None = None
    # 变量更新：计算并保存data_start，右侧逻辑为`None`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    data_start: datetime | None = None
    # 变量更新：计算并保存data_end，右侧逻辑为`None`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    data_end: datetime | None = None
    # 变量更新：计算并保存notes，右侧逻辑为`None`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    notes: str | None = None
    # 变量更新：计算并保存batch_id，右侧逻辑为`field(default_factory=_new_id)`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    batch_id: str = field(default_factory=_new_id)
    # 变量更新：计算并保存read_at，右侧逻辑为`field(default_factory=_utc_now)`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    read_at: datetime = field(default_factory=_utc_now)
    # 变量更新：计算并保存row_count，右侧逻辑为`field(init=False)`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    row_count: int = field(init=False)

    # 创建对象后执行最小一致性检查。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态或模块常量。
    # - 输出：返回类型None；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：在不可变或数据类对象创建后立即校验字段关系，阻止不一致对象进入系统。
    def __post_init__(self) -> None:
        """创建对象后执行最小一致性检查。"""

        # API调用：执行`_require_non_empty(self.source_id, 'source_id')`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        _require_non_empty(self.source_id, "source_id")
        # API调用：执行`_require_non_empty(self.source_object_name, 'source_object_name')`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        _require_non_empty(self.source_object_name, "source_object_name")
        # API调用：执行`_require_non_empty(self.batch_id, 'batch_id')`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        _require_non_empty(self.batch_id, "batch_id")

        # 条件门禁：判断`not isinstance(self.source_type, SourceType)`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if not isinstance(self.source_type, SourceType):
            # 错误阻断：抛出`DataContractError('source_type 必须是 SourceType。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError("source_type 必须是 SourceType。")

        # 条件门禁：判断`any((not isinstance(name, str) or not name.strip() for name in self.raw_fields))`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if any(not isinstance(name, str) or not name.strip() for name in self.raw_fields):
            # 错误阻断：抛出`DataContractError('raw_fields 中的每个字段名都必须是非空字符串。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError("raw_fields 中的每个字段名都必须是非空字符串。")

        # 条件门禁：判断`len(self.raw_fields) != len(set(self.raw_fields))`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if len(self.raw_fields) != len(set(self.raw_fields)):
            # 错误阻断：抛出`DataContractError('raw_fields 不能包含重复字段名。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError("raw_fields 不能包含重复字段名。")

        # 条件门禁：判断`any((not isinstance(record, dict) for record in self.records))`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if any(not isinstance(record, dict) for record in self.records):
            # 错误阻断：抛出`DataContractError('records 中的每一行都必须是字典。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError("records 中的每一行都必须是字典。")

        # 条件门禁：判断`self.data_start and self.data_end and (self.data_start > self.data_end)`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if self.data_start and self.data_end and self.data_start > self.data_end:
            # 错误阻断：抛出`DataContractError('data_start 不能晚于 data_end。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError("data_start 不能晚于 data_end。")

        # 变量更新：计算并保存self.row_count，右侧逻辑为`len(self.records)`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        self.row_count = len(self.records)


# 一个来源字段映射到标准字段后的结果。
# - 字段source_field：类型str。
# - 字段canonical_field_ref：类型str | None。
# - 字段status：类型MappingStatus。
# - 字段source_data_type：类型str | None，默认值None。
# - 字段target_data_type：类型str | None，默认值None。
# - 字段source_unit：类型str | None，默认值None。
# - 字段target_unit：类型str | None，默认值None。
# - 字段transform_rule：类型str | None，默认值None。
# - 其余字段：另有2项，均在对象创建时统一校验。
# - 数据变化：类本身不执行隐式I/O，实例字段只在显式构造、校验或方法调用时变化。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
@dataclass(slots=True)
class FieldMappingResult:
    """一个来源字段映射到标准字段后的结果。"""

    # 变量更新：计算并保存source_field，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    source_field: str
    # 变量更新：计算并保存canonical_field_ref，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    canonical_field_ref: str | None
    # 变量更新：计算并保存status，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    status: MappingStatus
    # 变量更新：计算并保存source_data_type，右侧逻辑为`None`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    source_data_type: str | None = None
    # 变量更新：计算并保存target_data_type，右侧逻辑为`None`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    target_data_type: str | None = None
    # 变量更新：计算并保存source_unit，右侧逻辑为`None`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    source_unit: str | None = None
    # 变量更新：计算并保存target_unit，右侧逻辑为`None`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    target_unit: str | None = None
    # 变量更新：计算并保存transform_rule，右侧逻辑为`None`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    transform_rule: str | None = None
    # 变量更新：计算并保存requires_confirmation，右侧逻辑为`False`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    requires_confirmation: bool = False
    # 变量更新：计算并保存message，右侧逻辑为`None`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    message: str | None = None

    # 检查字段映射结果是否符合最小约定。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态或模块常量。
    # - 输出：返回类型None；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：在不可变或数据类对象创建后立即校验字段关系，阻止不一致对象进入系统。
    def __post_init__(self) -> None:
        """检查字段映射结果是否符合最小约定。"""

        # API调用：执行`_require_non_empty(self.source_field, 'source_field')`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        _require_non_empty(self.source_field, "source_field")

        # 条件门禁：判断`not isinstance(self.status, MappingStatus)`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if not isinstance(self.status, MappingStatus):
            # 错误阻断：抛出`DataContractError('status 必须是 MappingStatus。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError("status 必须是 MappingStatus。")

        # 条件门禁：判断`self.status is MappingStatus.MAPPED and (not self.canonical_field_ref)`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if self.status is MappingStatus.MAPPED and not self.canonical_field_ref:
            # 错误阻断：抛出`DataContractError('状态为 MAPPED 时，canonical_field_ref 不能为空。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError(
                "状态为 MAPPED 时，canonical_field_ref 不能为空。"
            )

        # 条件门禁：判断`self.canonical_field_ref is not None`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if self.canonical_field_ref is not None:
            # 变量更新：计算并保存field_ref，右侧逻辑为`self.canonical_field_ref.strip()`。
            # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
            # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
            field_ref = self.canonical_field_ref.strip()
            # 条件门禁：判断`not field_ref`，条件为真时进入受保护分支。
            # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
            # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
            if not field_ref:
                # 错误阻断：抛出`DataContractError('canonical_field_ref 不能是空字符串。')`并停止当前路径。
                # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
                # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
                raise DataContractError("canonical_field_ref 不能是空字符串。")
            # 条件门禁：判断`'.' not in field_ref`，条件为真时进入受保护分支。
            # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
            # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
            if "." not in field_ref:
                # 错误阻断：抛出`DataContractError('canonical_field_ref 必须使用 domain.field 格式。')`并停止当前路径。
                # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
                # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
                raise DataContractError(
                    "canonical_field_ref 必须使用 domain.field 格式。"
                )

        # 条件门禁：判断`self.status is MappingStatus.PENDING_CONFIRMATION and (not self.requires_confirmation)`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if (
            self.status is MappingStatus.PENDING_CONFIRMATION
            and not self.requires_confirmation
        ):
            # 错误阻断：抛出`DataContractError('状态为 PENDING_CONFIRMATION 时，requires_confirmation 必须为 True。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError(
                "状态为 PENDING_CONFIRMATION 时，requires_confirmation 必须为 True。"
            )


# 一次数据质量检查的结构化结果。
# - 字段check_name：类型str。
# - 字段level：类型QualityLevel。
# - 字段status：类型QualityStatus。
# - 字段checked_row_count：类型int。
# - 字段failed_row_count：类型int。
# - 字段blocking：类型bool。
# - 字段sample_failures：类型list[dict[str, Any]]，默认值field(default_factory=list)。
# - 字段description：类型str | None，默认值None。
# - 其余字段：另有3项，均在对象创建时统一校验。
# - 数据变化：类本身不执行隐式I/O，实例字段只在显式构造、校验或方法调用时变化。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
@dataclass(slots=True)
class DataQualityResult:
    """一次数据质量检查的结构化结果。"""

    # 变量更新：计算并保存check_name，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    check_name: str
    # 变量更新：计算并保存level，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    level: QualityLevel
    # 变量更新：计算并保存status，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    status: QualityStatus
    # 变量更新：计算并保存checked_row_count，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    checked_row_count: int
    # 变量更新：计算并保存failed_row_count，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    failed_row_count: int
    # 变量更新：计算并保存blocking，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    blocking: bool
    # 变量更新：计算并保存sample_failures，右侧逻辑为`field(default_factory=list)`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    sample_failures: list[dict[str, Any]] = field(default_factory=list)
    # 变量更新：计算并保存description，右侧逻辑为`None`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    description: str | None = None
    # 变量更新：计算并保存check_id，右侧逻辑为`field(default_factory=_new_id)`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    check_id: str = field(default_factory=_new_id)
    # 变量更新：计算并保存checked_at，右侧逻辑为`field(default_factory=_utc_now)`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    checked_at: datetime = field(default_factory=_utc_now)
    # 变量更新：计算并保存failure_rate，右侧逻辑为`field(init=False)`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    failure_rate: float = field(init=False)

    # 检查行数、状态和唯一标识是否符合约定。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态或模块常量。
    # - 输出：返回类型None；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：在不可变或数据类对象创建后立即校验字段关系，阻止不一致对象进入系统。
    def __post_init__(self) -> None:
        """检查行数、状态和唯一标识是否符合约定。"""

        # API调用：执行`_require_non_empty(self.check_name, 'check_name')`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        _require_non_empty(self.check_name, "check_name")
        # API调用：执行`_require_non_empty(self.check_id, 'check_id')`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        _require_non_empty(self.check_id, "check_id")

        # 条件门禁：判断`not isinstance(self.level, QualityLevel)`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if not isinstance(self.level, QualityLevel):
            # 错误阻断：抛出`DataContractError('level 必须是 QualityLevel。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError("level 必须是 QualityLevel。")
        # 条件门禁：判断`not isinstance(self.status, QualityStatus)`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if not isinstance(self.status, QualityStatus):
            # 错误阻断：抛出`DataContractError('status 必须是 QualityStatus。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError("status 必须是 QualityStatus。")
        # 条件门禁：判断`self.checked_row_count < 0`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if self.checked_row_count < 0:
            # 错误阻断：抛出`DataContractError('checked_row_count 不能小于 0。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError("checked_row_count 不能小于 0。")
        # 条件门禁：判断`self.failed_row_count < 0`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if self.failed_row_count < 0:
            # 错误阻断：抛出`DataContractError('failed_row_count 不能小于 0。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError("failed_row_count 不能小于 0。")
        # 条件门禁：判断`self.failed_row_count > self.checked_row_count`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if self.failed_row_count > self.checked_row_count:
            # 错误阻断：抛出`DataContractError('failed_row_count 不能大于 checked_row_count。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError(
                "failed_row_count 不能大于 checked_row_count。"
            )
        # 条件门禁：判断`self.status is QualityStatus.PASSED and self.failed_row_count > 0`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if self.status is QualityStatus.PASSED and self.failed_row_count > 0:
            # 错误阻断：抛出`DataContractError('状态为 PASSED 时，failed_row_count 必须为 0。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError(
                "状态为 PASSED 时，failed_row_count 必须为 0。"
            )
        # 条件门禁：判断`any((not isinstance(item, dict) for item in self.sample_failures))`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if any(not isinstance(item, dict) for item in self.sample_failures):
            # 错误阻断：抛出`DataContractError('sample_failures 中的每一项都必须是字典。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError("sample_failures 中的每一项都必须是字典。")

        # 变量更新：计算并保存self.failure_rate，右侧逻辑为`0.0 if self.checked_row_count == 0 else self.failed_row_count / self.checked_row_count`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 固定数值：本表达式包含0.0, 0；来源是当前项目既有合同或算法定义，迁移注释不改变其数值。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        self.failure_rate = (
            0.0
            if self.checked_row_count == 0
            else self.failed_row_count / self.checked_row_count
        )

    # 返回本次质量结果是否阻止下游继续运行。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态或模块常量。
    # - 输出：返回类型bool；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
    @property
    def blocks_downstream(self) -> bool:
        """返回本次质量结果是否阻止下游继续运行。"""

        # 结果返回：把`self.blocking`交给调用方。
        # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
        # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
        return self.blocking


# 需要人工确认的数据语义或来源问题。
# - 字段category：类型str。
# - 字段source_object：类型str。
# - 字段issue_description：类型str。
# - 字段field_or_object_name：类型str | None，默认值None。
# - 字段possible_options：类型list[str]，默认值field(default_factory=list)。
# - 字段status：类型ConfirmationStatus，默认值ConfirmationStatus.OPEN。
# - 字段blocking_level：类型BlockingLevel，默认值BlockingLevel.WARNING。
# - 字段resolution_text：类型str | None，默认值None。
# - 其余字段：另有3项，均在对象创建时统一校验。
# - 数据变化：类本身不执行隐式I/O，实例字段只在显式构造、校验或方法调用时变化。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
@dataclass(slots=True)
class PendingConfirmation:
    """需要人工确认的数据语义或来源问题。"""

    # 变量更新：计算并保存category，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    category: str
    # 变量更新：计算并保存source_object，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    source_object: str
    # 变量更新：计算并保存issue_description，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    issue_description: str
    # 变量更新：计算并保存field_or_object_name，右侧逻辑为`None`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    field_or_object_name: str | None = None
    # 变量更新：计算并保存possible_options，右侧逻辑为`field(default_factory=list)`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    possible_options: list[str] = field(default_factory=list)
    # 变量更新：计算并保存status，右侧逻辑为`ConfirmationStatus.OPEN`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    status: ConfirmationStatus = ConfirmationStatus.OPEN
    # 变量更新：计算并保存blocking_level，右侧逻辑为`BlockingLevel.WARNING`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    blocking_level: BlockingLevel = BlockingLevel.WARNING
    # 变量更新：计算并保存resolution_text，右侧逻辑为`None`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    resolution_text: str | None = None
    # 变量更新：计算并保存resolved_at，右侧逻辑为`None`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    resolved_at: datetime | None = None
    # 变量更新：计算并保存confirmation_id，右侧逻辑为`field(default_factory=_new_id)`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    confirmation_id: str = field(default_factory=_new_id)
    # 变量更新：计算并保存created_at，右侧逻辑为`field(default_factory=_utc_now)`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    created_at: datetime = field(default_factory=_utc_now)

    # 检查待确认事项的基本完整性。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态或模块常量。
    # - 输出：返回类型None；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：在不可变或数据类对象创建后立即校验字段关系，阻止不一致对象进入系统。
    def __post_init__(self) -> None:
        """检查待确认事项的基本完整性。"""

        # API调用：执行`_require_non_empty(self.category, 'category')`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        _require_non_empty(self.category, "category")
        # API调用：执行`_require_non_empty(self.source_object, 'source_object')`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        _require_non_empty(self.source_object, "source_object")
        # API调用：执行`_require_non_empty(self.issue_description, 'issue_description')`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        _require_non_empty(self.issue_description, "issue_description")
        # API调用：执行`_require_non_empty(self.confirmation_id, 'confirmation_id')`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        _require_non_empty(self.confirmation_id, "confirmation_id")

        # 条件门禁：判断`not isinstance(self.status, ConfirmationStatus)`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if not isinstance(self.status, ConfirmationStatus):
            # 错误阻断：抛出`DataContractError('status 必须是 ConfirmationStatus。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError("status 必须是 ConfirmationStatus。")
        # 条件门禁：判断`not isinstance(self.blocking_level, BlockingLevel)`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if not isinstance(self.blocking_level, BlockingLevel):
            # 错误阻断：抛出`DataContractError('blocking_level 必须是 BlockingLevel。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError("blocking_level 必须是 BlockingLevel。")
        # 条件门禁：判断`any((not isinstance(option, str) or not option.strip() for option in self.possible_options))`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if any(not isinstance(option, str) or not option.strip() for option in self.possible_options):
            # 错误阻断：抛出`DataContractError('possible_options 中的每个选项都必须是非空字符串。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError(
                "possible_options 中的每个选项都必须是非空字符串。"
            )
        # 条件门禁：判断`self.status is ConfirmationStatus.RESOLVED`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if self.status is ConfirmationStatus.RESOLVED:
            # 条件门禁：判断`self.resolved_at is None`，条件为真时进入受保护分支。
            # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
            # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
            if self.resolved_at is None:
                # 错误阻断：抛出`DataContractError('状态为 RESOLVED 时，resolved_at 不能为空。')`并停止当前路径。
                # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
                # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
                raise DataContractError(
                    "状态为 RESOLVED 时，resolved_at 不能为空。"
                )
            # 条件门禁：判断`not self.resolution_text or not self.resolution_text.strip()`，条件为真时进入受保护分支。
            # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
            # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
            if not self.resolution_text or not self.resolution_text.strip():
                # 错误阻断：抛出`DataContractError('状态为 RESOLVED 时，resolution_text 不能为空。')`并停止当前路径。
                # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
                # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
                raise DataContractError(
                    "状态为 RESOLVED 时，resolution_text 不能为空。"
                )

    # 判断当前事项是否仍阻断下游流程。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态或模块常量。
    # - 输出：返回类型bool；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
    @property
    def blocks_downstream(self) -> bool:
        """判断当前事项是否仍阻断下游流程。"""

        # 结果返回：把`self.status is ConfirmationStatus.OPEN and self.blocking_level is BlockingLevel.BLOCKING`交给调用方。
        # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
        # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
        return (
            self.status is ConfirmationStatus.OPEN
            and self.blocking_level is BlockingLevel.BLOCKING
        )


# 完成字段映射后的标准化数据批次。
# - 字段raw_batch_id：类型str。
# - 字段domain_code：类型str。
# - 字段canonical_object_name：类型str。
# - 字段field_dictionary_version：类型str。
# - 字段mapping_version：类型str。
# - 字段records：类型list[dict[str, Any]]。
# - 字段quality_status：类型QualityStatus，默认值QualityStatus.PENDING_CONFIRMATION。
# - 字段pending_confirmations：类型list[PendingConfirmation]，默认值field(default_factory=list)。
# - 其余字段：另有4项，均在对象创建时统一校验。
# - 数据变化：类本身不执行隐式I/O，实例字段只在显式构造、校验或方法调用时变化。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
@dataclass(slots=True)
class CanonicalDataBatch:
    """完成字段映射后的标准化数据批次。"""

    # 变量更新：计算并保存raw_batch_id，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    raw_batch_id: str
    # 变量更新：计算并保存domain_code，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    domain_code: str
    # 变量更新：计算并保存canonical_object_name，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    canonical_object_name: str
    # 变量更新：计算并保存field_dictionary_version，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    field_dictionary_version: str
    # 变量更新：计算并保存mapping_version，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    mapping_version: str
    # 变量更新：计算并保存records，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    records: list[dict[str, Any]]
    # 变量更新：计算并保存quality_status，右侧逻辑为`QualityStatus.PENDING_CONFIRMATION`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    quality_status: QualityStatus = QualityStatus.PENDING_CONFIRMATION
    # 变量更新：计算并保存pending_confirmations，右侧逻辑为`field(default_factory=list)`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    pending_confirmations: list[PendingConfirmation] = field(default_factory=list)
    # 变量更新：计算并保存notes，右侧逻辑为`None`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    notes: str | None = None
    # 变量更新：计算并保存batch_id，右侧逻辑为`field(default_factory=_new_id)`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    batch_id: str = field(default_factory=_new_id)
    # 变量更新：计算并保存transformed_at，右侧逻辑为`field(default_factory=_utc_now)`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    transformed_at: datetime = field(default_factory=_utc_now)
    # 变量更新：计算并保存row_count，右侧逻辑为`field(init=False)`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    row_count: int = field(init=False)

    # 检查标准化批次的基本完整性。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态或模块常量。
    # - 输出：返回类型None；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：在不可变或数据类对象创建后立即校验字段关系，阻止不一致对象进入系统。
    def __post_init__(self) -> None:
        """检查标准化批次的基本完整性。"""

        # API调用：执行`_require_non_empty(self.raw_batch_id, 'raw_batch_id')`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        _require_non_empty(self.raw_batch_id, "raw_batch_id")
        # API调用：执行`_require_non_empty(self.domain_code, 'domain_code')`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        _require_non_empty(self.domain_code, "domain_code")
        # API调用：执行`_require_non_empty(self.canonical_object_name, 'canonical_object_name')`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        _require_non_empty(self.canonical_object_name, "canonical_object_name")
        # API调用：执行`_require_non_empty(self.field_dictionary_version, 'field_dictionary_version')`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        _require_non_empty(self.field_dictionary_version, "field_dictionary_version")
        # API调用：执行`_require_non_empty(self.mapping_version, 'mapping_version')`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        _require_non_empty(self.mapping_version, "mapping_version")
        # API调用：执行`_require_non_empty(self.batch_id, 'batch_id')`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        _require_non_empty(self.batch_id, "batch_id")

        # 条件门禁：判断`not isinstance(self.quality_status, QualityStatus)`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if not isinstance(self.quality_status, QualityStatus):
            # 错误阻断：抛出`DataContractError('quality_status 必须是 QualityStatus。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError("quality_status 必须是 QualityStatus。")
        # 条件门禁：判断`any((not isinstance(record, dict) for record in self.records))`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if any(not isinstance(record, dict) for record in self.records):
            # 错误阻断：抛出`DataContractError('records 中的每一行都必须是字典。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError("records 中的每一行都必须是字典。")
        # 条件门禁：判断`any((not isinstance(item, PendingConfirmation) for item in self.pending_confirmations))`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if any(
            not isinstance(item, PendingConfirmation)
            for item in self.pending_confirmations
        ):
            # 错误阻断：抛出`DataContractError('pending_confirmations 中的每一项都必须是 PendingConfirmation。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError(
                "pending_confirmations 中的每一项都必须是 PendingConfirmation。"
            )

        # 变量更新：计算并保存self.row_count，右侧逻辑为`len(self.records)`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        self.row_count = len(self.records)

    # 判断该标准化批次是否应阻止下游使用。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态或模块常量。
    # - 输出：返回类型bool；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
    @property
    def blocks_downstream(self) -> bool:
        """判断该标准化批次是否应阻止下游使用。"""

        # 条件门禁：判断`self.quality_status in {QualityStatus.FAILED, QualityStatus.PENDING_CONFIRMATION}`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if self.quality_status in {
            QualityStatus.FAILED,
            QualityStatus.PENDING_CONFIRMATION,
        }:
            # 结果返回：把`True`交给调用方。
            # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
            # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
            return True
        # 结果返回：把`any((item.blocks_downstream for item in self.pending_confirmations))`交给调用方。
        # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
        # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
        return any(item.blocks_downstream for item in self.pending_confirmations)


# 记录原始批次到标准批次之间的转换血缘。
# - 字段source_batch_id：类型str。
# - 字段target_batch_id：类型str。
# - 字段source_location：类型str。
# - 字段target_object：类型str。
# - 字段mapping_version：类型str。
# - 字段transformation_version：类型str。
# - 字段code_version：类型str | None，默认值None。
# - 字段configuration_version：类型str | None，默认值None。
# - 其余字段：另有3项，均在对象创建时统一校验。
# - 数据变化：类本身不执行隐式I/O，实例字段只在显式构造、校验或方法调用时变化。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
@dataclass(slots=True)
class DataLineageRecord:
    """记录原始批次到标准批次之间的转换血缘。"""

    # 变量更新：计算并保存source_batch_id，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    source_batch_id: str
    # 变量更新：计算并保存target_batch_id，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    target_batch_id: str
    # 变量更新：计算并保存source_location，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    source_location: str
    # 变量更新：计算并保存target_object，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    target_object: str
    # 变量更新：计算并保存mapping_version，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    mapping_version: str
    # 变量更新：计算并保存transformation_version，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    transformation_version: str
    # 变量更新：计算并保存code_version，右侧逻辑为`None`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    code_version: str | None = None
    # 变量更新：计算并保存configuration_version，右侧逻辑为`None`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    configuration_version: str | None = None
    # 变量更新：计算并保存description，右侧逻辑为`None`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    description: str | None = None
    # 变量更新：计算并保存lineage_id，右侧逻辑为`field(default_factory=_new_id)`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    lineage_id: str = field(default_factory=_new_id)
    # 变量更新：计算并保存transformed_at，右侧逻辑为`field(default_factory=_utc_now)`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    transformed_at: datetime = field(default_factory=_utc_now)

    # 检查血缘记录的关键标识和版本是否完整。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态或模块常量。
    # - 输出：返回类型None；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：在不可变或数据类对象创建后立即校验字段关系，阻止不一致对象进入系统。
    def __post_init__(self) -> None:
        """检查血缘记录的关键标识和版本是否完整。"""

        # 变量更新：计算并保存required_values，右侧逻辑为`{'source_batch_id': self.source_batch_id, 'target_batch_id': self.target_batch_id, 'sou...`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        required_values = {
            "source_batch_id": self.source_batch_id,
            "target_batch_id": self.target_batch_id,
            "source_location": self.source_location,
            "target_object": self.target_object,
            "mapping_version": self.mapping_version,
            "transformation_version": self.transformation_version,
            "lineage_id": self.lineage_id,
        }
        # 迭代处理：依次读取`required_values.items()`中的元素，并绑定到`(field_name, value)`。
        # - 维度变化：每轮处理一个元素，可能向列表、字典或累计值中增加一项。
        # - 为什么这样写：显式逐项校验可以精确指出哪个字段或Provider不符合合同。
        for field_name, value in required_values.items():
            # API调用：执行`_require_non_empty(value, field_name)`以触发注册、写入对象状态或其他显式副作用。
            # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
            # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
            _require_non_empty(value, field_name)

        # 条件门禁：判断`self.source_batch_id == self.target_batch_id`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if self.source_batch_id == self.target_batch_id:
            # 错误阻断：抛出`DataContractError('source_batch_id 和 target_batch_id 不能相同。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError(
                "source_batch_id 和 target_batch_id 不能相同。"
            )


# 所有数据来源适配器必须遵守的最小接口。
# - 状态成员：枚举值或方法共同描述该合同允许的有限状态和行为。
# - 数据变化：类本身不执行隐式I/O，实例字段只在显式构造、校验或方法调用时变化。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
class DataSourceAdapter(ABC):
    """所有数据来源适配器必须遵守的最小接口。"""

    # 保存数据来源的唯一标识和来源类型。
    # - 参数source_id：类型str；进入函数后按合同校验或参与计算。
    # - 参数source_type：类型SourceType；进入函数后按合同校验或参与计算。
    # - 输出：返回类型None；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
    def __init__(self, source_id: str, source_type: SourceType) -> None:
        """保存数据来源的唯一标识和来源类型。"""

        # API调用：执行`_require_non_empty(source_id, 'source_id')`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        _require_non_empty(source_id, "source_id")
        # 条件门禁：判断`not isinstance(source_type, SourceType)`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if not isinstance(source_type, SourceType):
            # 错误阻断：抛出`DataContractError('source_type 必须是 SourceType。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError("source_type 必须是 SourceType。")
        # 变量更新：计算并保存self.source_id，右侧逻辑为`source_id`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        self.source_id = source_id
        # 变量更新：计算并保存self.source_type，右侧逻辑为`source_type`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        self.source_type = source_type

    # 从来源读取一批原始数据。
    # - 参数source_object_name：类型str；进入函数后按合同校验或参与计算。
    # - 可变关键字参数kwargs：接收额外命名配置。
    # - 输出：返回类型RawDataBatch；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
    @abstractmethod
    def read_raw(
        self,
        source_object_name: str,
        **kwargs: Any,
    ) -> RawDataBatch:
        """从来源读取一批原始数据。"""

        # 错误阻断：抛出`NotImplementedError`并停止当前路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
        # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
        raise NotImplementedError

    # 检查当前数据来源是否可用。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态或模块常量。
    # - 输出：返回类型DataQualityResult；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：把底层健康结果翻译为Provider统一状态，便于路由层使用同一判定标准。
    @abstractmethod
    def health_check(self) -> DataQualityResult:
        """检查当前数据来源是否可用。"""

        # 错误阻断：抛出`NotImplementedError`并停止当前路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
        # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
        raise NotImplementedError
