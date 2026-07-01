# 模块总览：厂商查询清单合同。
# - 输入输出：本模块通过强类型对象和纯函数交换数据，不在导入阶段执行隐式网络或数据库写入。
# - 数据变化：只有显式构造、校验、加载或方法调用才会产生新对象或更新受控状态。
# - 为什么这样写：先说明模块边界，读者可以在阅读实现前理解职责、风险和复用方式。
"""厂商查询清单合同。

具体厂商指标、报表ID、参数和返回路径必须放在版本化清单中，
不得散落在业务代码。Wind代码生成器或iFinD超级命令生成的
调用参数，应先转成VendorQueryManifest，再由未来适配器执行。

本模块不执行HTTP或SDK请求。
"""

# 依赖导入：加载标准库、类型工具和项目内合同，供下方数据结构与校验逻辑复用。
# - 标准库只提供解析、数学、时间、路径和类型能力；项目模块提供统一异常与上游合同。
# - 为什么这样写：集中导入让依赖边界清晰，并避免在函数内部重复加载同一模块。
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any

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


# 定义VendorOperation强类型合同，集中保存相关状态、参数和校验规则。
# - 状态成员：枚举值或方法共同描述该合同允许的有限状态和行为。
# - 数据变化：类本身不执行隐式I/O，实例字段只在显式构造、校验或方法调用时变化。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
class VendorOperation(str, Enum):
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
    # 变量更新：计算并保存BASIC_DATA，右侧逻辑为`'BASIC_DATA'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    BASIC_DATA = "BASIC_DATA"
    # 变量更新：计算并保存DATE_SEQUENCE，右侧逻辑为`'DATE_SEQUENCE'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    DATE_SEQUENCE = "DATE_SEQUENCE"
    # 变量更新：计算并保存DATA_POOL，右侧逻辑为`'DATA_POOL'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    DATA_POOL = "DATA_POOL"
    # 变量更新：计算并保存ECONOMIC_DATABASE，右侧逻辑为`'ECONOMIC_DATABASE'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    ECONOMIC_DATABASE = "ECONOMIC_DATABASE"
    # 变量更新：计算并保存REPORT_QUERY，右侧逻辑为`'REPORT_QUERY'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    REPORT_QUERY = "REPORT_QUERY"
    # 变量更新：计算并保存TRADING_CALENDAR，右侧逻辑为`'TRADING_CALENDAR'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    TRADING_CALENDAR = "TRADING_CALENDAR"
    # 变量更新：计算并保存PORTFOLIO_ANALYTICS，右侧逻辑为`'PORTFOLIO_ANALYTICS'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    PORTFOLIO_ANALYTICS = "PORTFOLIO_ANALYTICS"
    # 变量更新：计算并保存SMART_QUERY，右侧逻辑为`'SMART_QUERY'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    SMART_QUERY = "SMART_QUERY"


# 变量更新：计算并保存_SECRET_FRAGMENTS，右侧逻辑为`('password', 'passwd', 'secret', 'access_token', 'refresh_token', 'api_key', 'credential')`。
# - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
# - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
_SECRET_FRAGMENTS = (
    "password",
    "passwd",
    "secret",
    "access_token",
    "refresh_token",
    "api_key",
    "credential",
)


# 执行_find_secret_paths逻辑，把输入参数转换为受合同约束的结果。
# - 参数value：类型Any；进入函数后按合同校验或参与计算。
# - 参数path：类型str，默认值'$'；进入函数后按合同校验或参与计算。
# - 输出：返回类型list[str]；调用方按该类型继续校验、路由或序列化。
# - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
def _find_secret_paths(
    value: Any,
    path: str = "$",
) -> list[str]:
    # 变量更新：计算并保存findings，右侧逻辑为`[]`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    findings: list[str] = []
    # 条件门禁：判断`isinstance(value, dict)`，条件为真时进入受保护分支。
    # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
    # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
    if isinstance(value, dict):
        # 迭代处理：依次读取`value.items()`中的元素，并绑定到`(key, item)`。
        # - 维度变化：每轮处理一个元素，可能向列表、字典或累计值中增加一项。
        # - 为什么这样写：显式逐项校验可以精确指出哪个字段或Provider不符合合同。
        for key, item in value.items():
            # 变量更新：计算并保存key_text，右侧逻辑为`str(key).lower()`。
            # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
            # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
            key_text = str(key).lower()
            # 变量更新：计算并保存child_path，右侧逻辑为`f'{path}.{key}'`。
            # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
            # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
            child_path = f"{path}.{key}"
            # 条件门禁：判断`any((fragment in key_text for fragment in _SECRET_FRAGMENTS))`，条件为真时进入受保护分支。
            # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
            # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
            if any(
                fragment in key_text
                for fragment in _SECRET_FRAGMENTS
            ):
                # API调用：执行`findings.append(child_path)`以触发注册、写入对象状态或其他显式副作用。
                # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
                # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
                findings.append(child_path)
            # API调用：执行`findings.extend(_find_secret_paths(item, child_path))`以触发注册、写入对象状态或其他显式副作用。
            # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
            # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
            findings.extend(
                _find_secret_paths(item, child_path)
            )
    # 备用分支：当前面的条件不满足时执行此路径。
    # - 为什么这样写：显式覆盖互斥状态，避免未处理输入静默落空。
    # 条件门禁：判断`isinstance(value, (list, tuple))`，条件为真时进入受保护分支。
    # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
    # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
    elif isinstance(value, (list, tuple)):
        # 迭代处理：依次读取`enumerate(value)`中的元素，并绑定到`(index, item)`。
        # - 维度变化：每轮处理一个元素，可能向列表、字典或累计值中增加一项。
        # - 为什么这样写：显式逐项校验可以精确指出哪个字段或Provider不符合合同。
        for index, item in enumerate(value):
            # API调用：执行`findings.extend(_find_secret_paths(item, f'{path}[{index}]'))`以触发注册、写入对象状态或其他显式副作用。
            # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
            # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
            findings.extend(
                _find_secret_paths(
                    item,
                    f"{path}[{index}]",
                )
            )
    # 结果返回：把`findings`交给调用方。
    # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
    # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
    return findings


# 定义ChunkPolicy强类型合同，集中保存相关状态、参数和校验规则。
# - 字段max_codes_per_request：类型int | None，默认值None。
# - 字段max_days_per_request：类型int | None，默认值None。
# - 字段max_rows_hint：类型int | None，默认值None。
# - 字段split_strategy：类型str，默认值'NONE'。
# - 数据变化：类本身不执行隐式I/O，实例字段只在显式构造、校验或方法调用时变化。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
@dataclass(frozen=True, slots=True)
class ChunkPolicy:
    # 变量更新：计算并保存max_codes_per_request，右侧逻辑为`None`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    max_codes_per_request: int | None = None
    # 变量更新：计算并保存max_days_per_request，右侧逻辑为`None`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    max_days_per_request: int | None = None
    # 变量更新：计算并保存max_rows_hint，右侧逻辑为`None`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    max_rows_hint: int | None = None
    # 变量更新：计算并保存split_strategy，右侧逻辑为`'NONE'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    split_strategy: str = "NONE"

    # 执行__post_init__逻辑，把输入参数转换为受合同约束的结果。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态或模块常量。
    # - 输出：返回类型None；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：在不可变或数据类对象创建后立即校验字段关系，阻止不一致对象进入系统。
    def __post_init__(self) -> None:
        # 迭代处理：依次读取`('max_codes_per_request', 'max_days_per_request', 'max_rows_hint')`中的元素，并绑定到`field_name`。
        # - 维度变化：每轮处理一个元素，可能向列表、字典或累计值中增加一项。
        # - 为什么这样写：显式逐项校验可以精确指出哪个字段或Provider不符合合同。
        for field_name in (
            "max_codes_per_request",
            "max_days_per_request",
            "max_rows_hint",
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
                # 错误阻断：抛出`DataContractError(f'{field_name}必须是正整数或None。')`并停止当前路径。
                # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
                # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
                raise DataContractError(
                    f"{field_name}必须是正整数或None。"
                )


# 定义VendorQueryManifest强类型合同，集中保存相关状态、参数和校验规则。
# - 字段manifest_id：类型str。
# - 字段source_id：类型str。
# - 字段dataset_id：类型str。
# - 字段canonical_object：类型str。
# - 字段operation：类型VendorOperation。
# - 字段request_template：类型dict[str, Any]。
# - 字段field_mapping：类型dict[str, str]。
# - 字段response_data_path：类型str。
# - 其余字段：另有7项，均在对象创建时统一校验。
# - 数据变化：类本身不执行隐式I/O，实例字段只在显式构造、校验或方法调用时变化。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
@dataclass(frozen=True, slots=True)
class VendorQueryManifest:
    # 变量更新：计算并保存manifest_id，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    manifest_id: str
    # 变量更新：计算并保存source_id，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    source_id: str
    # 变量更新：计算并保存dataset_id，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    dataset_id: str
    # 变量更新：计算并保存canonical_object，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    canonical_object: str
    # 变量更新：计算并保存operation，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    operation: VendorOperation
    # 变量更新：计算并保存request_template，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    request_template: dict[str, Any]
    # 变量更新：计算并保存field_mapping，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    field_mapping: dict[str, str]
    # 变量更新：计算并保存response_data_path，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    response_data_path: str
    # 变量更新：计算并保存mapping_version，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    mapping_version: str
    # 变量更新：计算并保存source_schema_version，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    source_schema_version: str
    # 变量更新：计算并保存generated_by，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    generated_by: str
    # 变量更新：计算并保存enabled，右侧逻辑为`False`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    enabled: bool = False
    # 变量更新：计算并保存chunk_policy，右侧逻辑为`field(default_factory=ChunkPolicy)`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    chunk_policy: ChunkPolicy = field(
        default_factory=ChunkPolicy
    )
    # 变量更新：计算并保存timeout_seconds，右侧逻辑为`60`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 固定数值：本表达式包含60；来源是当前项目既有合同或算法定义，迁移注释不改变其数值。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    timeout_seconds: int = 60
    # 变量更新：计算并保存notes，右侧逻辑为`()`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    notes: tuple[str, ...] = ()

    # 执行__post_init__逻辑，把输入参数转换为受合同约束的结果。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态或模块常量。
    # - 输出：返回类型None；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：在不可变或数据类对象创建后立即校验字段关系，阻止不一致对象进入系统。
    def __post_init__(self) -> None:
        # 迭代处理：依次读取`('manifest_id', 'source_id', 'dataset_id', 'canonical_object', 'response_data...`中的元素，并绑定到`field_name`。
        # - 维度变化：每轮处理一个元素，可能向列表、字典或累计值中增加一项。
        # - 为什么这样写：显式逐项校验可以精确指出哪个字段或Provider不符合合同。
        for field_name in (
            "manifest_id",
            "source_id",
            "dataset_id",
            "canonical_object",
            "response_data_path",
            "mapping_version",
            "source_schema_version",
            "generated_by",
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

        # 变量更新：计算并保存operation，右侧逻辑为`self.operation`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        operation = self.operation
        # 条件门禁：判断`isinstance(operation, str)`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if isinstance(operation, str):
            # 异常边界：执行可能失败的转换或外部调用，并把底层异常转换为项目可理解的合同错误。
            # - 数据变化：成功路径产生正常结果，失败路径保留原异常作为cause或记录明确错误。
            # - 为什么这样写：统一异常类型可以让上层门禁稳定处理，而不依赖第三方异常细节。
            try:
                # 变量更新：计算并保存operation，右侧逻辑为`VendorOperation(operation)`。
                # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
                # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
                operation = VendorOperation(operation)
            # 异常转换：捕获预期失败并保留上下文，随后转成项目统一错误或降级结果。
            # - 为什么这样写：上层不需要理解第三方异常细节，也能得到稳定错误语义。
            except ValueError as exc:
                # 错误阻断：抛出`DataContractError('operation不是受支持的厂商操作。')`并停止当前路径。
                # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
                # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
                raise DataContractError(
                    "operation不是受支持的厂商操作。"
                ) from exc
        # API调用：执行`object.__setattr__(self, 'operation', operation)`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        object.__setattr__(
            self,
            "operation",
            operation,
        )

        # 条件门禁：判断`not isinstance(self.timeout_seconds, int) or self.timeout_seconds <= 0`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if (
            not isinstance(self.timeout_seconds, int)
            or self.timeout_seconds <= 0
        ):
            # 错误阻断：抛出`DataContractError('timeout_seconds必须是正整数。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError(
                "timeout_seconds必须是正整数。"
            )

        # 变量更新：计算并保存secret_paths，右侧逻辑为`_find_secret_paths(self.request_template)`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        secret_paths = _find_secret_paths(
            self.request_template
        )
        # 条件门禁：判断`secret_paths`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if secret_paths:
            # 错误阻断：抛出`DataContractError('request_template不得包含凭据字段：' + ', '.join(secret_paths))`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError(
                "request_template不得包含凭据字段："
                + ", ".join(secret_paths)
            )

        # 条件门禁：判断`not self.field_mapping`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if not self.field_mapping:
            # 错误阻断：抛出`DataContractError('field_mapping不能为空。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError(
                "field_mapping不能为空。"
            )

        # 条件门禁：判断`len(set(self.field_mapping)) != len(self.field_mapping)`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if len(set(self.field_mapping)) != len(
            self.field_mapping
        ):
            # 错误阻断：抛出`DataContractError('field_mapping来源字段不允许重复。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError(
                "field_mapping来源字段不允许重复。"
            )

    # 执行to_dict逻辑，把输入参数转换为受合同约束的结果。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态或模块常量。
    # - 输出：返回类型dict[str, Any]；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：把强类型对象转换为JSON安全字典，便于报告、审计和持久化。
    def to_dict(self) -> dict[str, Any]:
        # 变量更新：计算并保存payload，右侧逻辑为`asdict(self)`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        payload = asdict(self)
        # 变量更新：计算并保存payload['operation']，右侧逻辑为`self.operation.value`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        payload["operation"] = self.operation.value
        # 结果返回：把`payload`交给调用方。
        # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
        # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
        return payload

    # 执行from_dict逻辑，把输入参数转换为受合同约束的结果。
    # - 参数payload：类型dict[str, Any]；进入函数后按合同校验或参与计算。
    # - 输出：返回类型'VendorQueryManifest'；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：从普通字典恢复强类型对象，集中处理枚举、默认值和兼容性。
    @classmethod
    def from_dict(
        cls,
        payload: dict[str, Any],
    ) -> "VendorQueryManifest":
        # 结果返回：把`cls(manifest_id=payload['manifest_id'], source_id=payload['source_id'], dataset_id=payload['datas...`交给调用方。
        # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
        # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
        return cls(
            manifest_id=payload["manifest_id"],
            source_id=payload["source_id"],
            dataset_id=payload["dataset_id"],
            canonical_object=payload[
                "canonical_object"
            ],
            operation=VendorOperation(
                payload["operation"]
            ),
            request_template=dict(
                payload.get("request_template", {})
            ),
            field_mapping=dict(
                payload.get("field_mapping", {})
            ),
            response_data_path=payload[
                "response_data_path"
            ],
            mapping_version=payload[
                "mapping_version"
            ],
            source_schema_version=payload[
                "source_schema_version"
            ],
            generated_by=payload["generated_by"],
            enabled=bool(
                payload.get("enabled", False)
            ),
            chunk_policy=ChunkPolicy(
                **payload.get("chunk_policy", {})
            ),
            timeout_seconds=int(
                payload.get("timeout_seconds", 60)
            ),
            notes=tuple(payload.get("notes", [])),
        )


# 定义VendorManifestRegistry强类型合同，集中保存相关状态、参数和校验规则。
# - 状态成员：枚举值或方法共同描述该合同允许的有限状态和行为。
# - 数据变化：类本身不执行隐式I/O，实例字段只在显式构造、校验或方法调用时变化。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
class VendorManifestRegistry:
    # 执行__init__逻辑，把输入参数转换为受合同约束的结果。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态或模块常量。
    # - 输出：返回类型None；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
    def __init__(self) -> None:
        # 变量更新：计算并保存self._items，右侧逻辑为`{}`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        self._items: dict[
            str, VendorQueryManifest
        ] = {}

    # 执行register逻辑，把输入参数转换为受合同约束的结果。
    # - 参数manifest：类型VendorQueryManifest；进入函数后按合同校验或参与计算。
    # - 输出：返回类型None；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
    def register(
        self,
        manifest: VendorQueryManifest,
    ) -> None:
        # 条件门禁：判断`manifest.manifest_id in self._items`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if manifest.manifest_id in self._items:
            # 错误阻断：抛出`DataContractError(f'manifest已注册：{manifest.manifest_id}')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError(
                f"manifest已注册：{manifest.manifest_id}"
            )
        # 变量更新：计算并保存self._items[manifest.manifest_id]，右侧逻辑为`manifest`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        self._items[manifest.manifest_id] = manifest

    # 执行get逻辑，把输入参数转换为受合同约束的结果。
    # - 参数manifest_id：类型str；进入函数后按合同校验或参与计算。
    # - 输出：返回类型VendorQueryManifest；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
    def get(
        self,
        manifest_id: str,
    ) -> VendorQueryManifest:
        # 异常边界：执行可能失败的转换或外部调用，并把底层异常转换为项目可理解的合同错误。
        # - 数据变化：成功路径产生正常结果，失败路径保留原异常作为cause或记录明确错误。
        # - 为什么这样写：统一异常类型可以让上层门禁稳定处理，而不依赖第三方异常细节。
        try:
            # 结果返回：把`self._items[manifest_id]`交给调用方。
            # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
            # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
            return self._items[manifest_id]
        # 异常转换：捕获预期失败并保留上下文，随后转成项目统一错误或降级结果。
        # - 为什么这样写：上层不需要理解第三方异常细节，也能得到稳定错误语义。
        except KeyError as exc:
            # 错误阻断：抛出`DataContractError(f'未知manifest：{manifest_id}')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError(
                f"未知manifest：{manifest_id}"
            ) from exc

    # 执行list_for_dataset逻辑，把输入参数转换为受合同约束的结果。
    # - 参数dataset_id：类型str；进入函数后按合同校验或参与计算。
    # - 关键字参数include_disabled：类型bool，默认值False；用于控制本次调用行为。
    # - 输出：返回类型tuple[VendorQueryManifest, ...]；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
    def list_for_dataset(
        self,
        dataset_id: str,
        *,
        include_disabled: bool = False,
    ) -> tuple[VendorQueryManifest, ...]:
        # 变量更新：计算并保存items，右侧逻辑为`[item for item in self._items.values() if item.dataset_id == dataset_id and (include_di...`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        items = [
            item
            for item in self._items.values()
            if item.dataset_id == dataset_id
            and (
                include_disabled or item.enabled
            )
        ]
        # API调用：执行`items.sort(key=lambda item: (item.source_id, item.operation.value, item.manifest_id))`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        items.sort(
            key=lambda item: (
                item.source_id,
                item.operation.value,
                item.manifest_id,
            )
        )
        # 结果返回：把`tuple(items)`交给调用方。
        # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
        # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
        return tuple(items)
