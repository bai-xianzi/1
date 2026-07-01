# 模块总览：来源中立的数据源治理合同。
# - 输入输出：本模块通过强类型对象和纯函数交换数据，不在导入阶段执行隐式网络或数据库写入。
# - 数据变化：只有显式构造、校验、加载或方法调用才会产生新对象或更新受控状态。
# - 为什么这样写：先说明模块边界，读者可以在阅读实现前理解职责、风险和复用方式。
"""来源中立的数据源治理合同。

本模块只定义长期稳定的数据源、能力、绑定和路由合同。
它不直接连接 Wind、iFinD、券商、DolphinDB 或文件系统，
也不保存任何账号、密码、Token 或本机路径。

设计目标：
1. 下游继续只依赖逻辑 dataset_id 和 StandardDataService；
2. 新来源通过 SourceDescriptor 和 DatasetSourceBinding 接入；
3. 主来源、备用来源、实时来源、归档来源和对账来源显式区分；
4. 来源能力显式声明，避免在业务代码中写 vendor if/else；
5. 尚未开通的 Wind、iFinD 和券商接口可以先完成离线合同和测试。
"""

# 依赖导入：加载标准库、类型工具和项目内合同，供下方数据结构与校验逻辑复用。
# - 标准库只提供解析、数学、时间、路径和类型能力；项目模块提供统一异常与上游合同。
# - 为什么这样写：集中导入让依赖边界清晰，并避免在函数内部重复加载同一模块。
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any, Iterable

from .data_contracts import DataContractError


# 执行_require_text逻辑，把输入参数转换为受合同约束的结果。
# - 参数value：类型str；进入函数后按合同校验或参与计算。
# - 参数field_name：类型str；进入函数后按合同校验或参与计算。
# - 输出：返回类型str；调用方按该类型继续校验、路由或序列化。
# - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
# - 为什么这样写：统一拒绝空字符串，避免无效标识进入后续注册、路由或持久化流程。
def _require_text(value: str, field_name: str) -> str:
    # 条件门禁：判断`not isinstance(value, str) or not value.strip()`，条件为真时进入受保护分支。
    # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
    # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
    if not isinstance(value, str) or not value.strip():
        # 错误阻断：抛出`DataContractError(f'{field_name} 不能为空。')`并停止当前路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
        # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
        raise DataContractError(f"{field_name} 不能为空。")
    # 结果返回：把`value.strip()`交给调用方。
    # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
    # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
    return value.strip()


# 执行_unique_enum_tuple逻辑，把输入参数转换为受合同约束的结果。
# - 参数values：类型Iterable[Enum]；进入函数后按合同校验或参与计算。
# - 参数enum_type：类型type[Enum]；进入函数后按合同校验或参与计算。
# - 参数field_name：类型str；进入函数后按合同校验或参与计算。
# - 输出：返回类型tuple[Enum, ...]；调用方按该类型继续校验、路由或序列化。
# - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
def _unique_enum_tuple(
    values: Iterable[Enum],
    enum_type: type[Enum],
    field_name: str,
) -> tuple[Enum, ...]:
    # 变量更新：计算并保存resolved，右侧逻辑为`[]`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    resolved: list[Enum] = []
    # 迭代处理：依次读取`values`中的元素，并绑定到`value`。
    # - 维度变化：每轮处理一个元素，可能向列表、字典或累计值中增加一项。
    # - 为什么这样写：显式逐项校验可以精确指出哪个字段或Provider不符合合同。
    for value in values:
        # 条件门禁：判断`isinstance(value, str)`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if isinstance(value, str):
            # 异常边界：执行可能失败的转换或外部调用，并把底层异常转换为项目可理解的合同错误。
            # - 数据变化：成功路径产生正常结果，失败路径保留原异常作为cause或记录明确错误。
            # - 为什么这样写：统一异常类型可以让上层门禁稳定处理，而不依赖第三方异常细节。
            try:
                # 变量更新：计算并保存value，右侧逻辑为`enum_type(value)`。
                # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
                # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
                value = enum_type(value)
            # 异常转换：捕获预期失败并保留上下文，随后转成项目统一错误或降级结果。
            # - 为什么这样写：上层不需要理解第三方异常细节，也能得到稳定错误语义。
            except ValueError as exc:
                # 错误阻断：抛出`DataContractError(f'{field_name} 包含不支持的值：{value}')`并停止当前路径。
                # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
                # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
                raise DataContractError(
                    f"{field_name} 包含不支持的值：{value}"
                ) from exc
        # 条件门禁：判断`not isinstance(value, enum_type)`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if not isinstance(value, enum_type):
            # 错误阻断：抛出`DataContractError(f'{field_name} 必须由 {enum_type.__name__} 组成。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError(
                f"{field_name} 必须由 {enum_type.__name__} 组成。"
            )
        # API调用：执行`resolved.append(value)`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        resolved.append(value)

    # 条件门禁：判断`len(set(resolved)) != len(resolved)`，条件为真时进入受保护分支。
    # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
    # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
    if len(set(resolved)) != len(resolved):
        # 错误阻断：抛出`DataContractError(f'{field_name} 不允许重复。')`并停止当前路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
        # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
        raise DataContractError(f"{field_name} 不允许重复。")
    # 结果返回：把`tuple(resolved)`交给调用方。
    # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
    # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
    return tuple(resolved)


# 执行_json_safe逻辑，把输入参数转换为受合同约束的结果。
# - 参数value：类型Any；进入函数后按合同校验或参与计算。
# - 输出：返回类型Any；调用方按该类型继续校验、路由或序列化。
# - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
def _json_safe(value: Any) -> Any:
    # 条件门禁：判断`isinstance(value, Enum)`，条件为真时进入受保护分支。
    # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
    # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
    if isinstance(value, Enum):
        # 结果返回：把`value.value`交给调用方。
        # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
        # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
        return value.value
    # 条件门禁：判断`isinstance(value, (date, datetime))`，条件为真时进入受保护分支。
    # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
    # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
    if isinstance(value, (date, datetime)):
        # 结果返回：把`value.isoformat()`交给调用方。
        # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
        # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
        return value.isoformat()
    # 条件门禁：判断`isinstance(value, dict)`，条件为真时进入受保护分支。
    # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
    # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
    if isinstance(value, dict):
        # 结果返回：把`{str(key): _json_safe(item) for key, item in value.items()}`交给调用方。
        # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
        # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
        return {
            str(key): _json_safe(item)
            for key, item in value.items()
        }
    # 条件门禁：判断`isinstance(value, (list, tuple, set, frozenset))`，条件为真时进入受保护分支。
    # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
    # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
    if isinstance(value, (list, tuple, set, frozenset)):
        # 结果返回：把`[_json_safe(item) for item in value]`交给调用方。
        # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
        # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
        return [_json_safe(item) for item in value]
    # 结果返回：把`value`交给调用方。
    # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
    # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
    return value


# 定义SourceProtocol强类型合同，集中保存相关状态、参数和校验规则。
# - 状态成员：枚举值或方法共同描述该合同允许的有限状态和行为。
# - 数据变化：类本身不执行隐式I/O，实例字段只在显式构造、校验或方法调用时变化。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
class SourceProtocol(str, Enum):
    # 变量更新：计算并保存DATABASE，右侧逻辑为`'DATABASE'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    DATABASE = "DATABASE"
    # 变量更新：计算并保存FILE，右侧逻辑为`'FILE'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    FILE = "FILE"
    # 变量更新：计算并保存SDK，右侧逻辑为`'SDK'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    SDK = "SDK"
    # 变量更新：计算并保存HTTP，右侧逻辑为`'HTTP'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    HTTP = "HTTP"
    # 变量更新：计算并保存STREAM，右侧逻辑为`'STREAM'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    STREAM = "STREAM"
    # 变量更新：计算并保存BROKER，右侧逻辑为`'BROKER'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    BROKER = "BROKER"


# 定义SourceRole强类型合同，集中保存相关状态、参数和校验规则。
# - 状态成员：枚举值或方法共同描述该合同允许的有限状态和行为。
# - 数据变化：类本身不执行隐式I/O，实例字段只在显式构造、校验或方法调用时变化。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
class SourceRole(str, Enum):
    # 变量更新：计算并保存PRIMARY，右侧逻辑为`'PRIMARY'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    PRIMARY = "PRIMARY"
    # 变量更新：计算并保存FALLBACK，右侧逻辑为`'FALLBACK'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    FALLBACK = "FALLBACK"
    # 变量更新：计算并保存RECONCILIATION，右侧逻辑为`'RECONCILIATION'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    RECONCILIATION = "RECONCILIATION"
    # 变量更新：计算并保存REALTIME，右侧逻辑为`'REALTIME'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    REALTIME = "REALTIME"
    # 变量更新：计算并保存ARCHIVE，右侧逻辑为`'ARCHIVE'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    ARCHIVE = "ARCHIVE"


# 定义SourceCapability强类型合同，集中保存相关状态、参数和校验规则。
# - 状态成员：枚举值或方法共同描述该合同允许的有限状态和行为。
# - 数据变化：类本身不执行隐式I/O，实例字段只在显式构造、校验或方法调用时变化。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
class SourceCapability(str, Enum):
    # 变量更新：计算并保存TIME_SERIES，右侧逻辑为`'TIME_SERIES'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    TIME_SERIES = "TIME_SERIES"
    # 变量更新：计算并保存CROSS_SECTION，右侧逻辑为`'CROSS_SECTION'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    CROSS_SECTION = "CROSS_SECTION"
    # 变量更新：计算并保存HISTORICAL_QUOTES，右侧逻辑为`'HISTORICAL_QUOTES'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    HISTORICAL_QUOTES = "HISTORICAL_QUOTES"
    # 变量更新：计算并保存REALTIME_QUOTES，右侧逻辑为`'REALTIME_QUOTES'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    REALTIME_QUOTES = "REALTIME_QUOTES"
    # 变量更新：计算并保存HIGH_FREQUENCY，右侧逻辑为`'HIGH_FREQUENCY'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    HIGH_FREQUENCY = "HIGH_FREQUENCY"
    # 变量更新：计算并保存SNAPSHOT，右侧逻辑为`'SNAPSHOT'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    SNAPSHOT = "SNAPSHOT"
    # 变量更新：计算并保存FUNDAMENTAL，右侧逻辑为`'FUNDAMENTAL'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    FUNDAMENTAL = "FUNDAMENTAL"
    # 变量更新：计算并保存CLASSIFICATION，右侧逻辑为`'CLASSIFICATION'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    CLASSIFICATION = "CLASSIFICATION"
    # 变量更新：计算并保存MONEY_FLOW，右侧逻辑为`'MONEY_FLOW'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    MONEY_FLOW = "MONEY_FLOW"
    # 变量更新：计算并保存MACRO，右侧逻辑为`'MACRO'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    MACRO = "MACRO"
    # 变量更新：计算并保存REPORTS，右侧逻辑为`'REPORTS'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    REPORTS = "REPORTS"
    # 变量更新：计算并保存NEWS_EVENTS，右侧逻辑为`'NEWS_EVENTS'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    NEWS_EVENTS = "NEWS_EVENTS"
    # 变量更新：计算并保存TRADING_CALENDAR，右侧逻辑为`'TRADING_CALENDAR'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    TRADING_CALENDAR = "TRADING_CALENDAR"
    # 变量更新：计算并保存PORTFOLIO_ANALYTICS，右侧逻辑为`'PORTFOLIO_ANALYTICS'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    PORTFOLIO_ANALYTICS = "PORTFOLIO_ANALYTICS"
    # 变量更新：计算并保存INCREMENTAL_SYNC，右侧逻辑为`'INCREMENTAL_SYNC'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    INCREMENTAL_SYNC = "INCREMENTAL_SYNC"
    # 变量更新：计算并保存POINT_IN_TIME，右侧逻辑为`'POINT_IN_TIME'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    POINT_IN_TIME = "POINT_IN_TIME"
    # 变量更新：计算并保存ORDERS，右侧逻辑为`'ORDERS'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    ORDERS = "ORDERS"
    # 变量更新：计算并保存POSITIONS，右侧逻辑为`'POSITIONS'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    POSITIONS = "POSITIONS"
    # 变量更新：计算并保存ACCOUNT，右侧逻辑为`'ACCOUNT'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    ACCOUNT = "ACCOUNT"


# 定义SourceOperationalStatus强类型合同，集中保存相关状态、参数和校验规则。
# - 状态成员：枚举值或方法共同描述该合同允许的有限状态和行为。
# - 数据变化：类本身不执行隐式I/O，实例字段只在显式构造、校验或方法调用时变化。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
class SourceOperationalStatus(str, Enum):
    # 变量更新：计算并保存DISABLED，右侧逻辑为`'DISABLED'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    DISABLED = "DISABLED"
    # 变量更新：计算并保存CONFIGURED，右侧逻辑为`'CONFIGURED'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    CONFIGURED = "CONFIGURED"
    # 变量更新：计算并保存AVAILABLE，右侧逻辑为`'AVAILABLE'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    AVAILABLE = "AVAILABLE"
    # 变量更新：计算并保存DEGRADED，右侧逻辑为`'DEGRADED'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    DEGRADED = "DEGRADED"
    # 变量更新：计算并保存UNAVAILABLE，右侧逻辑为`'UNAVAILABLE'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    UNAVAILABLE = "UNAVAILABLE"


# 定义ConflictStatus强类型合同，集中保存相关状态、参数和校验规则。
# - 状态成员：枚举值或方法共同描述该合同允许的有限状态和行为。
# - 数据变化：类本身不执行隐式I/O，实例字段只在显式构造、校验或方法调用时变化。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
class ConflictStatus(str, Enum):
    # 变量更新：计算并保存MATCHED，右侧逻辑为`'MATCHED'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    MATCHED = "MATCHED"
    # 变量更新：计算并保存WITHIN_TOLERANCE，右侧逻辑为`'WITHIN_TOLERANCE'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    WITHIN_TOLERANCE = "WITHIN_TOLERANCE"
    # 变量更新：计算并保存CONFLICT，右侧逻辑为`'CONFLICT'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    CONFLICT = "CONFLICT"
    # 变量更新：计算并保存PENDING_REVIEW，右侧逻辑为`'PENDING_REVIEW'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    PENDING_REVIEW = "PENDING_REVIEW"
    # 变量更新：计算并保存RESOLVED，右侧逻辑为`'RESOLVED'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    RESOLVED = "RESOLVED"


# 定义CredentialReference强类型合同，集中保存相关状态、参数和校验规则。
# - 字段reference_id：类型str。
# - 字段environment_variable：类型str。
# - 字段required：类型bool，默认值True。
# - 字段description：类型str，默认值''。
# - 数据变化：类本身不执行隐式I/O，实例字段只在显式构造、校验或方法调用时变化。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
@dataclass(frozen=True, slots=True)
class CredentialReference:
    # 变量更新：计算并保存reference_id，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    reference_id: str
    # 变量更新：计算并保存environment_variable，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    environment_variable: str
    # 变量更新：计算并保存required，右侧逻辑为`True`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    required: bool = True
    # 变量更新：计算并保存description，右侧逻辑为`''`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    description: str = ""

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
        # API调用：执行`object.__setattr__(self, 'environment_variable', _require_text(self.environment_variable, 'enviro...`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        object.__setattr__(
            self,
            "environment_variable",
            _require_text(
                self.environment_variable,
                "environment_variable",
            ),
        )

    # 执行to_dict逻辑，把输入参数转换为受合同约束的结果。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态或模块常量。
    # - 输出：返回类型dict[str, Any]；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：把强类型对象转换为JSON安全字典，便于报告、审计和持久化。
    def to_dict(self) -> dict[str, Any]:
        # 结果返回：把`_json_safe(asdict(self))`交给调用方。
        # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
        # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
        return _json_safe(asdict(self))


# 定义RateLimitPolicy强类型合同，集中保存相关状态、参数和校验规则。
# - 字段request_max_rows_hint：类型int | None，默认值None。
# - 字段quota_unit：类型str | None，默认值None。
# - 字段quota_limit_hint：类型int | None，默认值None。
# - 字段quota_window_seconds：类型int | None，默认值None。
# - 字段account_specific：类型bool，默认值True。
# - 字段hard_enforcement_enabled：类型bool，默认值False。
# - 数据变化：类本身不执行隐式I/O，实例字段只在显式构造、校验或方法调用时变化。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
@dataclass(frozen=True, slots=True)
class RateLimitPolicy:
    # 变量更新：计算并保存request_max_rows_hint，右侧逻辑为`None`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    request_max_rows_hint: int | None = None
    # 变量更新：计算并保存quota_unit，右侧逻辑为`None`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    quota_unit: str | None = None
    # 变量更新：计算并保存quota_limit_hint，右侧逻辑为`None`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    quota_limit_hint: int | None = None
    # 变量更新：计算并保存quota_window_seconds，右侧逻辑为`None`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    quota_window_seconds: int | None = None
    # 变量更新：计算并保存account_specific，右侧逻辑为`True`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    account_specific: bool = True
    # 变量更新：计算并保存hard_enforcement_enabled，右侧逻辑为`False`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    hard_enforcement_enabled: bool = False

    # 执行__post_init__逻辑，把输入参数转换为受合同约束的结果。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态或模块常量。
    # - 输出：返回类型None；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：在不可变或数据类对象创建后立即校验字段关系，阻止不一致对象进入系统。
    def __post_init__(self) -> None:
        # 迭代处理：依次读取`('request_max_rows_hint', 'quota_limit_hint', 'quota_window_seconds')`中的元素，并绑定到`field_name`。
        # - 维度变化：每轮处理一个元素，可能向列表、字典或累计值中增加一项。
        # - 为什么这样写：显式逐项校验可以精确指出哪个字段或Provider不符合合同。
        for field_name in (
            "request_max_rows_hint",
            "quota_limit_hint",
            "quota_window_seconds",
        ):
            # 变量更新：计算并保存value，右侧逻辑为`getattr(self, field_name)`。
            # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
            # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
            value = getattr(self, field_name)
            # 条件门禁：判断`value is not None and (not isinstance(value, int) or value <= 0)`，条件为真时进入受保护分支。
            # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
            # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
            if value is not None and (
                not isinstance(value, int) or value <= 0
            ):
                # 错误阻断：抛出`DataContractError(f'{field_name} 必须是正整数或None。')`并停止当前路径。
                # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
                # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
                raise DataContractError(
                    f"{field_name} 必须是正整数或None。"
                )

        # 条件门禁：判断`self.hard_enforcement_enabled and self.quota_limit_hint is None`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if (
            self.hard_enforcement_enabled
            and self.quota_limit_hint is None
        ):
            # 错误阻断：抛出`DataContractError('启用硬配额时必须提供quota_limit_hint。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError(
                "启用硬配额时必须提供quota_limit_hint。"
            )

    # 执行to_dict逻辑，把输入参数转换为受合同约束的结果。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态或模块常量。
    # - 输出：返回类型dict[str, Any]；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：把强类型对象转换为JSON安全字典，便于报告、审计和持久化。
    def to_dict(self) -> dict[str, Any]:
        # 结果返回：把`_json_safe(asdict(self))`交给调用方。
        # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
        # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
        return _json_safe(asdict(self))


# 定义SourceDescriptor强类型合同，集中保存相关状态、参数和校验规则。
# - 字段source_id：类型str。
# - 字段vendor_name：类型str。
# - 字段protocol：类型SourceProtocol。
# - 字段capabilities：类型tuple[SourceCapability, ...]。
# - 字段enabled：类型bool，默认值False。
# - 字段operational_status：类型SourceOperationalStatus，默认值SourceOperationalStatus.DISABLED。
# - 字段credential_references：类型tuple[CredentialReference, ...]，默认值()。
# - 字段rate_limit_policy：类型RateLimitPolicy | None，默认值None。
# - 其余字段：另有3项，均在对象创建时统一校验。
# - 数据变化：类本身不执行隐式I/O，实例字段只在显式构造、校验或方法调用时变化。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
@dataclass(frozen=True, slots=True)
class SourceDescriptor:
    # 变量更新：计算并保存source_id，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    source_id: str
    # 变量更新：计算并保存vendor_name，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    vendor_name: str
    # 变量更新：计算并保存protocol，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    protocol: SourceProtocol
    # 变量更新：计算并保存capabilities，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    capabilities: tuple[SourceCapability, ...]
    # 变量更新：计算并保存enabled，右侧逻辑为`False`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    enabled: bool = False
    # 变量更新：计算并保存operational_status，右侧逻辑为`SourceOperationalStatus.DISABLED`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    operational_status: SourceOperationalStatus = (
        SourceOperationalStatus.DISABLED
    )
    # 变量更新：计算并保存credential_references，右侧逻辑为`()`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    credential_references: tuple[
        CredentialReference, ...
    ] = ()
    # 变量更新：计算并保存rate_limit_policy，右侧逻辑为`None`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    rate_limit_policy: RateLimitPolicy | None = None
    # 变量更新：计算并保存timezone，右侧逻辑为`'Asia/Shanghai'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    timezone: str = "Asia/Shanghai"
    # 变量更新：计算并保存documentation_status，右侧逻辑为`''`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    documentation_status: str = ""
    # 变量更新：计算并保存metadata，右侧逻辑为`field(default_factory=dict)`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    metadata: dict[str, Any] = field(default_factory=dict)

    # 执行__post_init__逻辑，把输入参数转换为受合同约束的结果。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态或模块常量。
    # - 输出：返回类型None；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：在不可变或数据类对象创建后立即校验字段关系，阻止不一致对象进入系统。
    def __post_init__(self) -> None:
        # API调用：执行`object.__setattr__(self, 'source_id', _require_text(self.source_id, 'source_id'))`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        object.__setattr__(
            self,
            "source_id",
            _require_text(self.source_id, "source_id"),
        )
        # API调用：执行`object.__setattr__(self, 'vendor_name', _require_text(self.vendor_name, 'vendor_name'))`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        object.__setattr__(
            self,
            "vendor_name",
            _require_text(self.vendor_name, "vendor_name"),
        )
        # 变量更新：计算并保存protocol，右侧逻辑为`self.protocol`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        protocol = self.protocol
        # 条件门禁：判断`isinstance(protocol, str)`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if isinstance(protocol, str):
            # 异常边界：执行可能失败的转换或外部调用，并把底层异常转换为项目可理解的合同错误。
            # - 数据变化：成功路径产生正常结果，失败路径保留原异常作为cause或记录明确错误。
            # - 为什么这样写：统一异常类型可以让上层门禁稳定处理，而不依赖第三方异常细节。
            try:
                # 变量更新：计算并保存protocol，右侧逻辑为`SourceProtocol(protocol)`。
                # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
                # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
                protocol = SourceProtocol(protocol)
            # 异常转换：捕获预期失败并保留上下文，随后转成项目统一错误或降级结果。
            # - 为什么这样写：上层不需要理解第三方异常细节，也能得到稳定错误语义。
            except ValueError as exc:
                # 错误阻断：抛出`DataContractError('protocol不是受支持的来源协议。')`并停止当前路径。
                # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
                # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
                raise DataContractError(
                    "protocol不是受支持的来源协议。"
                ) from exc
        # API调用：执行`object.__setattr__(self, 'protocol', protocol)`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        object.__setattr__(self, "protocol", protocol)

        # API调用：执行`object.__setattr__(self, 'capabilities', _unique_enum_tuple(self.capabilities, SourceCapability, ...`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        object.__setattr__(
            self,
            "capabilities",
            _unique_enum_tuple(
                self.capabilities,
                SourceCapability,
                "capabilities",
            ),
        )

        # 变量更新：计算并保存status，右侧逻辑为`self.operational_status`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        status = self.operational_status
        # 条件门禁：判断`isinstance(status, str)`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if isinstance(status, str):
            # 异常边界：执行可能失败的转换或外部调用，并把底层异常转换为项目可理解的合同错误。
            # - 数据变化：成功路径产生正常结果，失败路径保留原异常作为cause或记录明确错误。
            # - 为什么这样写：统一异常类型可以让上层门禁稳定处理，而不依赖第三方异常细节。
            try:
                # 变量更新：计算并保存status，右侧逻辑为`SourceOperationalStatus(status)`。
                # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
                # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
                status = SourceOperationalStatus(status)
            # 异常转换：捕获预期失败并保留上下文，随后转成项目统一错误或降级结果。
            # - 为什么这样写：上层不需要理解第三方异常细节，也能得到稳定错误语义。
            except ValueError as exc:
                # 错误阻断：抛出`DataContractError('operational_status不是受支持的状态。')`并停止当前路径。
                # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
                # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
                raise DataContractError(
                    "operational_status不是受支持的状态。"
                ) from exc

        # 条件门禁：判断`not self.enabled and status is not SourceOperationalStatus.DISABLED`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if not self.enabled and status is not (
            SourceOperationalStatus.DISABLED
        ):
            # 错误阻断：抛出`DataContractError('未启用来源的operational_status必须为DISABLED。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError(
                "未启用来源的operational_status必须为DISABLED。"
            )

        # API调用：执行`object.__setattr__(self, 'operational_status', status)`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        object.__setattr__(
            self,
            "operational_status",
            status,
        )

        # 变量更新：计算并保存credential_ids，右侧逻辑为`[item.reference_id for item in self.credential_references]`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        credential_ids = [
            item.reference_id
            for item in self.credential_references
        ]
        # 条件门禁：判断`len(set(credential_ids)) != len(credential_ids)`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if len(set(credential_ids)) != len(credential_ids):
            # 错误阻断：抛出`DataContractError('credential_references不允许重复reference_id。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError(
                "credential_references不允许重复reference_id。"
            )

        # API调用：执行`object.__setattr__(self, 'timezone', _require_text(self.timezone, 'timezone'))`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        object.__setattr__(
            self,
            "timezone",
            _require_text(self.timezone, "timezone"),
        )

    # 执行supports逻辑，把输入参数转换为受合同约束的结果。
    # - 参数required_capabilities：类型Iterable[SourceCapability]；进入函数后按合同校验或参与计算。
    # - 输出：返回类型bool；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
    def supports(
        self,
        required_capabilities: Iterable[
            SourceCapability
        ],
    ) -> bool:
        # 变量更新：计算并保存required，右侧逻辑为`set(_unique_enum_tuple(required_capabilities, SourceCapability, 'required_capabilities'))`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        required = set(
            _unique_enum_tuple(
                required_capabilities,
                SourceCapability,
                "required_capabilities",
            )
        )
        # 结果返回：把`required.issubset(set(self.capabilities))`交给调用方。
        # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
        # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
        return required.issubset(set(self.capabilities))

    # 执行to_dict逻辑，把输入参数转换为受合同约束的结果。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态或模块常量。
    # - 输出：返回类型dict[str, Any]；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：把强类型对象转换为JSON安全字典，便于报告、审计和持久化。
    def to_dict(self) -> dict[str, Any]:
        # 结果返回：把`_json_safe(asdict(self))`交给调用方。
        # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
        # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
        return _json_safe(asdict(self))

    # 执行from_dict逻辑，把输入参数转换为受合同约束的结果。
    # - 参数payload：类型dict[str, Any]；进入函数后按合同校验或参与计算。
    # - 输出：返回类型'SourceDescriptor'；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：从普通字典恢复强类型对象，集中处理枚举、默认值和兼容性。
    @classmethod
    def from_dict(
        cls,
        payload: dict[str, Any],
    ) -> "SourceDescriptor":
        # 变量更新：计算并保存credentials，右侧逻辑为`tuple((CredentialReference(**item) for item in payload.get('credential_references', [])))`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        credentials = tuple(
            CredentialReference(**item)
            for item in payload.get(
                "credential_references",
                [],
            )
        )
        # 变量更新：计算并保存rate_payload，右侧逻辑为`payload.get('rate_limit_policy')`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        rate_payload = payload.get("rate_limit_policy")
        # 变量更新：计算并保存rate_policy，右侧逻辑为`RateLimitPolicy(**rate_payload) if rate_payload else None`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        rate_policy = (
            RateLimitPolicy(**rate_payload)
            if rate_payload
            else None
        )
        # 结果返回：把`cls(source_id=payload['source_id'], vendor_name=payload['vendor_name'], protocol=SourceProtocol(p...`交给调用方。
        # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
        # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
        return cls(
            source_id=payload["source_id"],
            vendor_name=payload["vendor_name"],
            protocol=SourceProtocol(payload["protocol"]),
            capabilities=tuple(
                SourceCapability(item)
                for item in payload.get(
                    "capabilities",
                    [],
                )
            ),
            enabled=bool(payload.get("enabled", False)),
            operational_status=SourceOperationalStatus(
                payload.get(
                    "operational_status",
                    "DISABLED",
                )
            ),
            credential_references=credentials,
            rate_limit_policy=rate_policy,
            timezone=payload.get(
                "timezone",
                "Asia/Shanghai",
            ),
            documentation_status=payload.get(
                "documentation_status",
                "",
            ),
            metadata=dict(payload.get("metadata", {})),
        )


# 定义DatasetSourceBinding强类型合同，集中保存相关状态、参数和校验规则。
# - 字段dataset_id：类型str。
# - 字段source_id：类型str。
# - 字段role：类型SourceRole。
# - 字段priority：类型int。
# - 字段source_locator：类型dict[str, Any]。
# - 字段mapping_version：类型str。
# - 字段source_schema_version：类型str。
# - 字段required_capabilities：类型tuple[SourceCapability, ...]，默认值()。
# - 其余字段：另有4项，均在对象创建时统一校验。
# - 数据变化：类本身不执行隐式I/O，实例字段只在显式构造、校验或方法调用时变化。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
@dataclass(frozen=True, slots=True)
class DatasetSourceBinding:
    # 变量更新：计算并保存dataset_id，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    dataset_id: str
    # 变量更新：计算并保存source_id，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    source_id: str
    # 变量更新：计算并保存role，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    role: SourceRole
    # 变量更新：计算并保存priority，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    priority: int
    # 变量更新：计算并保存source_locator，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    source_locator: dict[str, Any]
    # 变量更新：计算并保存mapping_version，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    mapping_version: str
    # 变量更新：计算并保存source_schema_version，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    source_schema_version: str
    # 变量更新：计算并保存required_capabilities，右侧逻辑为`()`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    required_capabilities: tuple[
        SourceCapability, ...
    ] = ()
    # 变量更新：计算并保存enabled，右侧逻辑为`False`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    enabled: bool = False
    # 变量更新：计算并保存effective_from，右侧逻辑为`None`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    effective_from: date | None = None
    # 变量更新：计算并保存effective_to，右侧逻辑为`None`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    effective_to: date | None = None
    # 变量更新：计算并保存notes，右侧逻辑为`''`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    notes: str = ""

    # 执行__post_init__逻辑，把输入参数转换为受合同约束的结果。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态或模块常量。
    # - 输出：返回类型None；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：在不可变或数据类对象创建后立即校验字段关系，阻止不一致对象进入系统。
    def __post_init__(self) -> None:
        # API调用：执行`object.__setattr__(self, 'dataset_id', _require_text(self.dataset_id, 'dataset_id'))`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        object.__setattr__(
            self,
            "dataset_id",
            _require_text(self.dataset_id, "dataset_id"),
        )
        # API调用：执行`object.__setattr__(self, 'source_id', _require_text(self.source_id, 'source_id'))`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        object.__setattr__(
            self,
            "source_id",
            _require_text(self.source_id, "source_id"),
        )
        # 变量更新：计算并保存role，右侧逻辑为`self.role`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        role = self.role
        # 条件门禁：判断`isinstance(role, str)`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if isinstance(role, str):
            # 异常边界：执行可能失败的转换或外部调用，并把底层异常转换为项目可理解的合同错误。
            # - 数据变化：成功路径产生正常结果，失败路径保留原异常作为cause或记录明确错误。
            # - 为什么这样写：统一异常类型可以让上层门禁稳定处理，而不依赖第三方异常细节。
            try:
                # 变量更新：计算并保存role，右侧逻辑为`SourceRole(role)`。
                # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
                # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
                role = SourceRole(role)
            # 异常转换：捕获预期失败并保留上下文，随后转成项目统一错误或降级结果。
            # - 为什么这样写：上层不需要理解第三方异常细节，也能得到稳定错误语义。
            except ValueError as exc:
                # 错误阻断：抛出`DataContractError('role不是受支持的来源角色。')`并停止当前路径。
                # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
                # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
                raise DataContractError(
                    "role不是受支持的来源角色。"
                ) from exc
        # API调用：执行`object.__setattr__(self, 'role', role)`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        object.__setattr__(self, "role", role)

        # 条件门禁：判断`not isinstance(self.priority, int) or self.priority < 1`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if not isinstance(self.priority, int) or self.priority < 1:
            # 错误阻断：抛出`DataContractError('priority必须是大于等于1的整数。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError(
                "priority必须是大于等于1的整数。"
            )

        # API调用：执行`object.__setattr__(self, 'mapping_version', _require_text(self.mapping_version, 'mapping_version'))`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        object.__setattr__(
            self,
            "mapping_version",
            _require_text(
                self.mapping_version,
                "mapping_version",
            ),
        )
        # API调用：执行`object.__setattr__(self, 'source_schema_version', _require_text(self.source_schema_version, 'sour...`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        object.__setattr__(
            self,
            "source_schema_version",
            _require_text(
                self.source_schema_version,
                "source_schema_version",
            ),
        )
        # API调用：执行`object.__setattr__(self, 'required_capabilities', _unique_enum_tuple(self.required_capabilities, ...`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        object.__setattr__(
            self,
            "required_capabilities",
            _unique_enum_tuple(
                self.required_capabilities,
                SourceCapability,
                "required_capabilities",
            ),
        )

        # 条件门禁：判断`self.effective_from is not None and self.effective_to is not None and (self.effective_from > self...`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if (
            self.effective_from is not None
            and self.effective_to is not None
            and self.effective_from > self.effective_to
        ):
            # 错误阻断：抛出`DataContractError('effective_from不能晚于effective_to。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError(
                "effective_from不能晚于effective_to。"
            )

    # 执行is_effective_on逻辑，把输入参数转换为受合同约束的结果。
    # - 参数target_date：类型date；进入函数后按合同校验或参与计算。
    # - 输出：返回类型bool；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
    def is_effective_on(self, target_date: date) -> bool:
        # 条件门禁：判断`self.effective_from and target_date < self.effective_from`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if self.effective_from and target_date < self.effective_from:
            # 结果返回：把`False`交给调用方。
            # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
            # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
            return False
        # 条件门禁：判断`self.effective_to and target_date > self.effective_to`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if self.effective_to and target_date > self.effective_to:
            # 结果返回：把`False`交给调用方。
            # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
            # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
            return False
        # 结果返回：把`True`交给调用方。
        # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
        # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
        return True

    # 执行to_dict逻辑，把输入参数转换为受合同约束的结果。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态或模块常量。
    # - 输出：返回类型dict[str, Any]；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：把强类型对象转换为JSON安全字典，便于报告、审计和持久化。
    def to_dict(self) -> dict[str, Any]:
        # 结果返回：把`_json_safe(asdict(self))`交给调用方。
        # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
        # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
        return _json_safe(asdict(self))


# 定义ConflictRecord强类型合同，集中保存相关状态、参数和校验规则。
# - 字段dataset_id：类型str。
# - 字段canonical_object：类型str。
# - 字段primary_key：类型dict[str, Any]。
# - 字段field_name：类型str。
# - 字段observation_time：类型datetime | date。
# - 字段primary_source_id：类型str。
# - 字段comparison_source_id：类型str。
# - 字段primary_value：类型Any。
# - 其余字段：另有5项，均在对象创建时统一校验。
# - 数据变化：类本身不执行隐式I/O，实例字段只在显式构造、校验或方法调用时变化。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
@dataclass(frozen=True, slots=True)
class ConflictRecord:
    # 变量更新：计算并保存dataset_id，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    dataset_id: str
    # 变量更新：计算并保存canonical_object，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    canonical_object: str
    # 变量更新：计算并保存primary_key，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    primary_key: dict[str, Any]
    # 变量更新：计算并保存field_name，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    field_name: str
    # 变量更新：计算并保存observation_time，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    observation_time: datetime | date
    # 变量更新：计算并保存primary_source_id，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    primary_source_id: str
    # 变量更新：计算并保存comparison_source_id，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    comparison_source_id: str
    # 变量更新：计算并保存primary_value，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    primary_value: Any
    # 变量更新：计算并保存comparison_value，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    comparison_value: Any
    # 变量更新：计算并保存difference，右侧逻辑为`None`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    difference: Any = None
    # 变量更新：计算并保存tolerance，右侧逻辑为`None`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    tolerance: Any = None
    # 变量更新：计算并保存status，右侧逻辑为`ConflictStatus.PENDING_REVIEW`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    status: ConflictStatus = ConflictStatus.PENDING_REVIEW
    # 变量更新：计算并保存resolution_note，右侧逻辑为`''`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    resolution_note: str = ""

    # 执行__post_init__逻辑，把输入参数转换为受合同约束的结果。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态或模块常量。
    # - 输出：返回类型None；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：在不可变或数据类对象创建后立即校验字段关系，阻止不一致对象进入系统。
    def __post_init__(self) -> None:
        # 迭代处理：依次读取`('dataset_id', 'canonical_object', 'field_name', 'primary_source_id', 'compar...`中的元素，并绑定到`field_name`。
        # - 维度变化：每轮处理一个元素，可能向列表、字典或累计值中增加一项。
        # - 为什么这样写：显式逐项校验可以精确指出哪个字段或Provider不符合合同。
        for field_name in (
            "dataset_id",
            "canonical_object",
            "field_name",
            "primary_source_id",
            "comparison_source_id",
        ):
            # API调用：执行`object.__setattr__(self, field_name, _require_text(getattr(self, field_name), field_name))`以触发注册、写入对象状态或其他显式副作用。
            # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
            # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
            object.__setattr__(
                self,
                field_name,
                _require_text(
                    getattr(self, field_name),
                    field_name,
                ),
            )

        # 条件门禁：判断`self.primary_source_id == self.comparison_source_id`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if (
            self.primary_source_id
            == self.comparison_source_id
        ):
            # 错误阻断：抛出`DataContractError('冲突比较必须来自两个不同来源。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError(
                "冲突比较必须来自两个不同来源。"
            )

        # 变量更新：计算并保存status，右侧逻辑为`self.status`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        status = self.status
        # 条件门禁：判断`isinstance(status, str)`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if isinstance(status, str):
            # 异常边界：执行可能失败的转换或外部调用，并把底层异常转换为项目可理解的合同错误。
            # - 数据变化：成功路径产生正常结果，失败路径保留原异常作为cause或记录明确错误。
            # - 为什么这样写：统一异常类型可以让上层门禁稳定处理，而不依赖第三方异常细节。
            try:
                # 变量更新：计算并保存status，右侧逻辑为`ConflictStatus(status)`。
                # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
                # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
                status = ConflictStatus(status)
            # 异常转换：捕获预期失败并保留上下文，随后转成项目统一错误或降级结果。
            # - 为什么这样写：上层不需要理解第三方异常细节，也能得到稳定错误语义。
            except ValueError as exc:
                # 错误阻断：抛出`DataContractError('status不是受支持的冲突状态。')`并停止当前路径。
                # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
                # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
                raise DataContractError(
                    "status不是受支持的冲突状态。"
                ) from exc
        # API调用：执行`object.__setattr__(self, 'status', status)`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        object.__setattr__(self, "status", status)

    # 执行to_dict逻辑，把输入参数转换为受合同约束的结果。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态或模块常量。
    # - 输出：返回类型dict[str, Any]；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：把强类型对象转换为JSON安全字典，便于报告、审计和持久化。
    def to_dict(self) -> dict[str, Any]:
        # 结果返回：把`_json_safe(asdict(self))`交给调用方。
        # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
        # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
        return _json_safe(asdict(self))


# 定义SourceRoute强类型合同，集中保存相关状态、参数和校验规则。
# - 字段binding：类型DatasetSourceBinding。
# - 字段source：类型SourceDescriptor。
# - 数据变化：类本身不执行隐式I/O，实例字段只在显式构造、校验或方法调用时变化。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
@dataclass(frozen=True, slots=True)
class SourceRoute:
    # 变量更新：计算并保存binding，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    binding: DatasetSourceBinding
    # 变量更新：计算并保存source，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    source: SourceDescriptor

    # 执行to_dict逻辑，把输入参数转换为受合同约束的结果。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态或模块常量。
    # - 输出：返回类型dict[str, Any]；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：把强类型对象转换为JSON安全字典，便于报告、审计和持久化。
    def to_dict(self) -> dict[str, Any]:
        # 结果返回：把`{'binding': self.binding.to_dict(), 'source': self.source.to_dict()}`交给调用方。
        # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
        # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
        return {
            "binding": self.binding.to_dict(),
            "source": self.source.to_dict(),
        }


# 来源和逻辑数据集绑定注册表。
# - 状态成员：枚举值或方法共同描述该合同允许的有限状态和行为。
# - 数据变化：类本身不执行隐式I/O，实例字段只在显式构造、校验或方法调用时变化。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
class SourceCatalog:
    """来源和逻辑数据集绑定注册表。

    当前只负责静态选择顺序，不执行网络请求和自动故障转移。
    自动故障转移必须在未来引入健康检查、幂等和审计后再启用。
    """

    # 执行__init__逻辑，把输入参数转换为受合同约束的结果。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态或模块常量。
    # - 输出：返回类型None；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
    def __init__(self) -> None:
        # 变量更新：计算并保存self._sources，右侧逻辑为`{}`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        self._sources: dict[str, SourceDescriptor] = {}
        # 变量更新：计算并保存self._bindings，右侧逻辑为`[]`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        self._bindings: list[DatasetSourceBinding] = []

    # 执行register_source逻辑，把输入参数转换为受合同约束的结果。
    # - 参数source：类型SourceDescriptor；进入函数后按合同校验或参与计算。
    # - 输出：返回类型None；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
    def register_source(
        self,
        source: SourceDescriptor,
    ) -> None:
        # 条件门禁：判断`source.source_id in self._sources`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if source.source_id in self._sources:
            # 错误阻断：抛出`DataContractError(f'来源已注册：{source.source_id}')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError(
                f"来源已注册：{source.source_id}"
            )
        # 变量更新：计算并保存self._sources[source.source_id]，右侧逻辑为`source`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        self._sources[source.source_id] = source

    # 执行register_binding逻辑，把输入参数转换为受合同约束的结果。
    # - 参数binding：类型DatasetSourceBinding；进入函数后按合同校验或参与计算。
    # - 输出：返回类型None；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
    def register_binding(
        self,
        binding: DatasetSourceBinding,
    ) -> None:
        # 条件门禁：判断`binding.source_id not in self._sources`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if binding.source_id not in self._sources:
            # 错误阻断：抛出`DataContractError(f'来源未注册：{binding.source_id}')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError(
                f"来源未注册：{binding.source_id}"
            )

        # 变量更新：计算并保存duplicate，右侧逻辑为`any((item.dataset_id == binding.dataset_id and item.source_id == binding.source_id and ...`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        duplicate = any(
            item.dataset_id == binding.dataset_id
            and item.source_id == binding.source_id
            and item.role == binding.role
            for item in self._bindings
        )
        # 条件门禁：判断`duplicate`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if duplicate:
            # 错误阻断：抛出`DataContractError('同一dataset/source/role绑定不允许重复。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError(
                "同一dataset/source/role绑定不允许重复。"
            )

        # 变量更新：计算并保存source，右侧逻辑为`self._sources[binding.source_id]`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        source = self._sources[binding.source_id]
        # 条件门禁：判断`not source.supports(binding.required_capabilities)`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if not source.supports(
            binding.required_capabilities
        ):
            # 错误阻断：抛出`DataContractError('来源能力不能满足绑定要求。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError(
                "来源能力不能满足绑定要求。"
            )

        # API调用：执行`self._bindings.append(binding)`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        self._bindings.append(binding)

    # 执行get_source逻辑，把输入参数转换为受合同约束的结果。
    # - 参数source_id：类型str；进入函数后按合同校验或参与计算。
    # - 输出：返回类型SourceDescriptor；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
    def get_source(
        self,
        source_id: str,
    ) -> SourceDescriptor:
        # 异常边界：执行可能失败的转换或外部调用，并把底层异常转换为项目可理解的合同错误。
        # - 数据变化：成功路径产生正常结果，失败路径保留原异常作为cause或记录明确错误。
        # - 为什么这样写：统一异常类型可以让上层门禁稳定处理，而不依赖第三方异常细节。
        try:
            # 结果返回：把`self._sources[source_id]`交给调用方。
            # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
            # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
            return self._sources[source_id]
        # 异常转换：捕获预期失败并保留上下文，随后转成项目统一错误或降级结果。
        # - 为什么这样写：上层不需要理解第三方异常细节，也能得到稳定错误语义。
        except KeyError as exc:
            # 错误阻断：抛出`DataContractError(f'未知来源：{source_id}')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError(
                f"未知来源：{source_id}"
            ) from exc

    # 执行list_sources逻辑，把输入参数转换为受合同约束的结果。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态或模块常量。
    # - 输出：返回类型tuple[SourceDescriptor, ...]；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
    def list_sources(self) -> tuple[SourceDescriptor, ...]:
        # 结果返回：把`tuple((self._sources[key] for key in sorted(self._sources)))`交给调用方。
        # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
        # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
        return tuple(
            self._sources[key]
            for key in sorted(self._sources)
        )

    # 执行routes_for逻辑，把输入参数转换为受合同约束的结果。
    # - 参数dataset_id：类型str；进入函数后按合同校验或参与计算。
    # - 参数required_capabilities：类型Iterable[SourceCapability]，默认值()；进入函数后按合同校验或参与计算。
    # - 关键字参数roles：类型Iterable[SourceRole] | None，默认值None；用于控制本次调用行为。
    # - 关键字参数target_date：类型date | None，默认值None；用于控制本次调用行为。
    # - 关键字参数include_disabled：类型bool，默认值False；用于控制本次调用行为。
    # - 输出：返回类型tuple[SourceRoute, ...]；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
    def routes_for(
        self,
        dataset_id: str,
        required_capabilities: Iterable[
            SourceCapability
        ] = (),
        *,
        roles: Iterable[SourceRole] | None = None,
        target_date: date | None = None,
        include_disabled: bool = False,
    ) -> tuple[SourceRoute, ...]:
        # 变量更新：计算并保存dataset_id，右侧逻辑为`_require_text(dataset_id, 'dataset_id')`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        dataset_id = _require_text(
            dataset_id,
            "dataset_id",
        )
        # 变量更新：计算并保存required，右侧逻辑为`tuple(required_capabilities)`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        required = tuple(required_capabilities)
        # 变量更新：计算并保存role_filter，右侧逻辑为`set(_unique_enum_tuple(roles, SourceRole, 'roles')) if roles is not None else None`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        role_filter = (
            set(
                _unique_enum_tuple(
                    roles,
                    SourceRole,
                    "roles",
                )
            )
            if roles is not None
            else None
        )

        # 变量更新：计算并保存routes，右侧逻辑为`[]`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        routes: list[SourceRoute] = []
        # 迭代处理：依次读取`self._bindings`中的元素，并绑定到`binding`。
        # - 维度变化：每轮处理一个元素，可能向列表、字典或累计值中增加一项。
        # - 为什么这样写：显式逐项校验可以精确指出哪个字段或Provider不符合合同。
        for binding in self._bindings:
            # 条件门禁：判断`binding.dataset_id != dataset_id`，条件为真时进入受保护分支。
            # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
            # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
            if binding.dataset_id != dataset_id:
                continue
            # 条件门禁：判断`role_filter is not None and binding.role not in role_filter`，条件为真时进入受保护分支。
            # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
            # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
            if role_filter is not None and (
                binding.role not in role_filter
            ):
                continue
            # 条件门禁：判断`target_date is not None and (not binding.is_effective_on(target_date))`，条件为真时进入受保护分支。
            # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
            # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
            if target_date is not None and (
                not binding.is_effective_on(target_date)
            ):
                continue

            # 变量更新：计算并保存source，右侧逻辑为`self._sources[binding.source_id]`。
            # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
            # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
            source = self._sources[binding.source_id]
            # 条件门禁：判断`not include_disabled and (not source.enabled or not binding.enabled)`，条件为真时进入受保护分支。
            # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
            # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
            if not include_disabled and (
                not source.enabled
                or not binding.enabled
            ):
                continue
            # 条件门禁：判断`not source.supports(required)`，条件为真时进入受保护分支。
            # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
            # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
            if not source.supports(required):
                continue

            # API调用：执行`routes.append(SourceRoute(binding=binding, source=source))`以触发注册、写入对象状态或其他显式副作用。
            # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
            # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
            routes.append(
                SourceRoute(
                    binding=binding,
                    source=source,
                )
            )

        # 变量更新：计算并保存role_order，右侧逻辑为`{SourceRole.PRIMARY: 0, SourceRole.REALTIME: 1, SourceRole.FALLBACK: 2, SourceRole.RECO...`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 固定数值：本表达式包含0, 1, 2, 3, 4；来源是当前项目既有合同或算法定义，迁移注释不改变其数值。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        role_order = {
            SourceRole.PRIMARY: 0,
            SourceRole.REALTIME: 1,
            SourceRole.FALLBACK: 2,
            SourceRole.RECONCILIATION: 3,
            SourceRole.ARCHIVE: 4,
        }
        # API调用：执行`routes.sort(key=lambda route: (role_order[route.binding.role], route.binding.priority, route.sour...`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        routes.sort(
            key=lambda route: (
                role_order[route.binding.role],
                route.binding.priority,
                route.source.source_id,
            )
        )
        # 结果返回：把`tuple(routes)`交给调用方。
        # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
        # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
        return tuple(routes)

    # 执行primary_route逻辑，把输入参数转换为受合同约束的结果。
    # - 参数dataset_id：类型str；进入函数后按合同校验或参与计算。
    # - 参数required_capabilities：类型Iterable[SourceCapability]，默认值()；进入函数后按合同校验或参与计算。
    # - 关键字参数target_date：类型date | None，默认值None；用于控制本次调用行为。
    # - 输出：返回类型SourceRoute；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
    def primary_route(
        self,
        dataset_id: str,
        required_capabilities: Iterable[
            SourceCapability
        ] = (),
        *,
        target_date: date | None = None,
    ) -> SourceRoute:
        # 变量更新：计算并保存routes，右侧逻辑为`self.routes_for(dataset_id, required_capabilities, roles=(SourceRole.PRIMARY,), target_...`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        routes = self.routes_for(
            dataset_id,
            required_capabilities,
            roles=(SourceRole.PRIMARY,),
            target_date=target_date,
        )
        # 条件门禁：判断`not routes`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if not routes:
            # 错误阻断：抛出`DataContractError(f'没有可用主来源：{dataset_id}')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError(
                f"没有可用主来源：{dataset_id}"
            )
        # 结果返回：把`routes[0]`交给调用方。
        # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
        # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
        return routes[0]
