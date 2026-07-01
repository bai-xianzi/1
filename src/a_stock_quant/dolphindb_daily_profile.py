# 模块总览：对DolphinDB日K表执行真实只读画像，统计结构、范围、缺失和基础行情关系。
# - 输入输出：输入为数据库表和安全样本边界；输出为可复现的数据画像与异常证据。
# - 数据与安全：画像阶段只观察来源事实，不在数据库中修复、覆盖或删除记录。
# - 运行边界：导入模块和阅读注释不会触发数据库写入；只有显式调用对应函数并满足门禁时才执行I/O。
# - 为什么这样写：先声明职责、单位、时点和副作用边界，读者可以在阅读实现前建立正确的金融与工程语境。
"""DolphinDB日K数据只读画像与质量验收。"""

# 依赖导入：加载`from __future__ import annotations`所提供的类型、标准库或项目内能力。
# - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
# - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
from __future__ import annotations

# 依赖导入：加载`import argparse`所提供的类型、标准库或项目内能力。
# - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
# - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
import argparse
# 依赖导入：加载`import json`所提供的类型、标准库或项目内能力。
# - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
# - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
import json
# 依赖导入：加载`import math`所提供的类型、标准库或项目内能力。
# - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
# - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
import math
# 依赖导入：加载`import re`所提供的类型、标准库或项目内能力。
# - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
# - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
import re
# 依赖导入：加载`from dataclasses import asdict, dataclass, field, is_dataclass`所提供的类型、标准库或项目内能力。
# - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
# - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
from dataclasses import asdict, dataclass, field, is_dataclass
# 依赖导入：加载`from datetime import date, datetime, timezone`所提供的类型、标准库或项目内能力。
# - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
# - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
from datetime import date, datetime, timezone
# 依赖导入：加载`from pathlib import Path`所提供的类型、标准库或项目内能力。
# - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
# - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
from pathlib import Path
# 依赖导入：加载`from typing import Any, Sequence`所提供的类型、标准库或项目内能力。
# - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
# - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
from typing import Any, Sequence

# 依赖导入：加载`from .data_contracts import DataContractError, QualityStatus`所提供的类型、标准库或项目内能力。
# - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
# - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
from .data_contracts import DataContractError, QualityStatus
# 依赖导入：加载`from .dolphindb_adapter import DolphinDBConnectionSettings, DolphinDBDataSourceAdapter`所提供的类型、标准库或项目内能力。
# - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
# - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
from .dolphindb_adapter import (
    DolphinDBConnectionSettings,
    DolphinDBDataSourceAdapter,
)
# 依赖导入：加载`from .dolphindb_probe import resolve_password`所提供的类型、标准库或项目内能力。
# - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
# - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
from .dolphindb_probe import resolve_password


# 关键常量_IDENTIFIER_PATTERN：集中保存`re.compile('^[A-Za-z_][A-Za-z0-9_]*$')`对应的合同值、Schema集合或运行边界。
# - 来源与范围：该值来自当前项目任务、配置、真实数据画像或安全合同；未明确说明时不得外推为行业统一标准。
# - 单位与实例：数值单位由变量名、相邻校验和调用语义共同限定；字符串用于版本、字段、状态或DolphinDB对象标识。
# - 为什么这样写：集中命名固定参数可避免魔法值散落，并让升级、审计和回归测试有稳定锚点。
_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

# 关键常量REQUIRED_FIELDS：集中保存`('stock_code', 'trade_date', 'open', 'high', 'low', 'close', 'amount', 'volume')`对应的合同值、Schema集合或运行边界。
# - 来源与范围：该值来自当前项目任务、配置、真实数据画像或安全合同；未明确说明时不得外推为行业统一标准。
# - 单位与实例：数值单位由变量名、相邻校验和调用语义共同限定；字符串用于版本、字段、状态或DolphinDB对象标识。
# - 为什么这样写：集中命名固定参数可避免魔法值散落，并让升级、审计和回归测试有稳定锚点。
REQUIRED_FIELDS = (
    "stock_code",
    "trade_date",
    "open",
    "high",
    "low",
    "close",
    "amount",
    "volume",
)


# 函数_utc_now：执行_utc_now对应的业务处理。
# - 输入：无外部业务参数；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型datetime；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
# - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def _utc_now() -> datetime:
    # 结果返回：把`datetime.now(timezone.utc)`交给调用方并结束当前函数。
    # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return datetime.now(timezone.utc)


# 函数_json_safe：将日期、枚举、NaN和数据类转换为标准JSON值。
# - 输入：value:Any；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型Any；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
# - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def _json_safe(value: Any) -> Any:
    """将日期、枚举、NaN和数据类转换为标准JSON值。"""

    # 条件门禁：判断`is_dataclass(value)`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if is_dataclass(value):
        # 结果返回：把`_json_safe(asdict(value))`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return _json_safe(asdict(value))

    # 条件门禁：判断`isinstance(value, dict)`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if isinstance(value, dict):
        # 结果返回：把`{str(key): _json_safe(item) for key, item in value.items()}`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return {str(key): _json_safe(item) for key, item in value.items()}

    # 条件门禁：判断`isinstance(value, (list, tuple))`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if isinstance(value, (list, tuple)):
        # 结果返回：把`[_json_safe(item) for item in value]`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return [_json_safe(item) for item in value]

    # 条件门禁：判断`isinstance(value, (datetime, date))`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if isinstance(value, (datetime, date)):
        # 结果返回：把`value.isoformat()`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return value.isoformat()

    # 状态计算：把`getattr(value, 'value', None)`的结果保存到`enum_value`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    enum_value = getattr(value, "value", None)
    # 条件门禁：判断`enum_value is not None and (not isinstance(value, (str, bytes)))`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if enum_value is not None and not isinstance(value, (str, bytes)):
        # 结果返回：把`_json_safe(enum_value)`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return _json_safe(enum_value)

    # 条件门禁：判断`isinstance(value, float) and (math.isnan(value) or math.isinf(value))`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if isinstance(value, float) and (
        math.isnan(value) or math.isinf(value)
    ):
        # 结果返回：把`None`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return None

    # 状态计算：把`getattr(value, 'item', None)`的结果保存到`item_method`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    item_method = getattr(value, "item", None)
    # 条件门禁：判断`callable(item_method)`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if callable(item_method):
        # 异常边界：尝试执行可能失败的解析、查询、文件或类型转换步骤，并由后续处理保留错误证据。
        # - 数据变化：正常路径产生业务结果；异常路径不得静默伪造数据，应抛出、记录或隔离。
        # - 为什么这样写：把外部环境故障与业务合同失败分开，便于重试、回滚和准确验收。
        try:
            # 结果返回：把`_json_safe(item_method())`交给调用方并结束当前函数。
            # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
            # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
            return _json_safe(item_method())
        except (TypeError, ValueError):
            # 控制流：保留显式空分支，使循环或占位分支按既定合同继续。
            # - 数据变化：本语句不直接改变业务记录，只调整当前执行路径。
            # - 为什么这样写：显式控制流比隐式嵌套更容易检查边界和异常处理。
            pass

    # 结果返回：把`value`交给调用方并结束当前函数。
    # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return value


# 函数_records_from_result：把常见DolphinDB表格返回值转换为记录列表。
# - 输入：result:Any；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型list[dict[str, Any]]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
# - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def _records_from_result(result: Any) -> list[dict[str, Any]]:
    """把常见DolphinDB表格返回值转换为记录列表。"""

    # 条件门禁：判断`result is None`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if result is None:
        # 结果返回：把`[]`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return []

    # 条件门禁：判断`isinstance(result, list)`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if isinstance(result, list):
        # 条件门禁：判断`any((not isinstance(item, dict) for item in result))`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if any(not isinstance(item, dict) for item in result):
            # 错误阻断：抛出`DataContractError('画像结果列表中存在非字典记录。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
            raise DataContractError("画像结果列表中存在非字典记录。")
        # 结果返回：把`list(result)`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return list(result)

    # 条件门禁：判断`isinstance(result, dict)`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if isinstance(result, dict):
        # 结果返回：把`[dict(result)]`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return [dict(result)]

    # 状态计算：把`getattr(result, 'to_dict', None)`的结果保存到`to_dict`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    to_dict = getattr(result, "to_dict", None)
    # 条件门禁：判断`callable(to_dict)`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if callable(to_dict):
        # 异常边界：尝试执行可能失败的解析、查询、文件或类型转换步骤，并由后续处理保留错误证据。
        # - 数据变化：正常路径产生业务结果；异常路径不得静默伪造数据，应抛出、记录或隔离。
        # - 为什么这样写：把外部环境故障与业务合同失败分开，便于重试、回滚和准确验收。
        try:
            # 状态计算：把`to_dict(orient='records')`的结果保存到`records`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            records = to_dict(orient="records")
        except TypeError:
            # 状态计算：把`to_dict('records')`的结果保存到`records`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            records = to_dict("records")

        # 条件门禁：判断`any((not isinstance(item, dict) for item in records))`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if any(not isinstance(item, dict) for item in records):
            # 错误阻断：抛出`DataContractError('画像结果无法转换为字典记录。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
            raise DataContractError("画像结果无法转换为字典记录。")
        # 结果返回：把`list(records)`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return list(records)

    # 错误阻断：抛出`DataContractError('暂不支持当前画像结果类型。')`并停止当前正常路径。
    # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
    # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
    raise DataContractError("暂不支持当前画像结果类型。")


# 函数_first_record：执行_first_record对应的业务处理。
# - 输入：result:Any；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型dict[str, Any]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
# - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def _first_record(result: Any) -> dict[str, Any]:
    # 状态计算：把`_records_from_result(result)`的结果保存到`records`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    records = _records_from_result(result)
    # 结果返回：把`records[0] if records else {}`交给调用方并结束当前函数。
    # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return records[0] if records else {}


# 类DailyKProfileReport：日K表只读画像报告。
# - 结构：继承或实现object；类体约包含17个字段或常量、1个方法。
# - 数据变化：类定义阶段不执行隐式I/O，实例只在构造或显式方法调用时改变受控状态。
# - 实操：调用方通过该类型集中传递配置、记录、服务或结果，避免跨模块使用无约束字典。
# - 为什么这样写：强类型边界能集中维护单位、时点、主键和安全不变量，并降低供应商耦合。
@dataclass(slots=True)
class DailyKProfileReport:
    """日K表只读画像报告。"""

    # 状态计算：把`无`的结果保存到`database_uri`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    database_uri: str
    # 状态计算：把`无`的结果保存到`table_name`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    table_name: str
    # 状态计算：把`无`的结果保存到`generated_at`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    generated_at: datetime
    # 状态计算：把`无`的结果保存到`raw_fields`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    raw_fields: list[str]
    # 状态计算：把`无`的结果保存到`summary`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    summary: dict[str, Any]
    # 状态计算：把`无`的结果保存到`null_counts`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    null_counts: dict[str, Any]
    # 状态计算：把`无`的结果保存到`duplicate_summary`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    duplicate_summary: dict[str, Any]
    # 状态计算：把`无`的结果保存到`duplicate_samples`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    duplicate_samples: list[dict[str, Any]]
    # 状态计算：把`无`的结果保存到`ohlc_summary`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    ohlc_summary: dict[str, Any]
    # 状态计算：把`无`的结果保存到`change_formula_summary`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    change_formula_summary: dict[str, Any]
    # 状态计算：把`无`的结果保存到`change_formula_samples`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    change_formula_samples: list[dict[str, Any]]
    # 状态计算：把`无`的结果保存到`amount_volume_summary`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    amount_volume_summary: dict[str, Any]
    # 状态计算：把`无`的结果保存到`adjustment_summary`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    adjustment_summary: dict[str, Any]
    # 状态计算：把`field(default_factory=list)`的结果保存到`checks`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    checks: list[dict[str, Any]] = field(default_factory=list)
    # 状态计算：把`field(default_factory=list)`的结果保存到`pending_confirmations`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    pending_confirmations: list[dict[str, Any]] = field(default_factory=list)
    # 状态计算：把`QualityStatus.PENDING_CONFIRMATION`的结果保存到`overall_status`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    overall_status: QualityStatus = QualityStatus.PENDING_CONFIRMATION
    # 状态计算：把`True`的结果保存到`blocks_downstream`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    blocks_downstream: bool = True

    # 函数to_dict：执行to_dict对应的业务处理。
    # - 输入：无外部业务参数；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型dict[str, Any]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把结果序列化或视图转换步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    def to_dict(self) -> dict[str, Any]:
        # 结果返回：把`_json_safe(self)`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return _json_safe(self)


# 类DolphinDBDailyKProfiler：对DolphinDB日K表执行只读聚合画像。
# - 结构：继承或实现object；类体约包含0个字段或常量、8个方法。
# - 数据变化：类定义阶段不执行隐式I/O，实例只在构造或显式方法调用时改变受控状态。
# - 实操：调用方通过该类型集中传递配置、记录、服务或结果，避免跨模块使用无约束字典。
# - 为什么这样写：强类型边界能集中维护单位、时点、主键和安全不变量，并降低供应商耦合。
class DolphinDBDailyKProfiler:
    """对DolphinDB日K表执行只读聚合画像。"""

    # 函数__init__：执行__init__对应的业务处理。
    # - 输入：adapter:DolphinDBDataSourceAdapter、database_uri:str、table_name:str；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型None；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    def __init__(
        self,
        adapter: DolphinDBDataSourceAdapter,
        database_uri: str = "dfs://A_STOCK_DAILY_K_DB",
        table_name: str = "stock_daily_k",
    ) -> None:
        # 显式调用：执行`adapter._validate_database_uri(database_uri)`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
        # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
        # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
        adapter._validate_database_uri(database_uri)
        # 显式调用：执行`adapter._validate_table_name(table_name)`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
        # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
        # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
        adapter._validate_table_name(table_name)

        # 状态计算：把`adapter`的结果保存到`self.adapter`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        self.adapter = adapter
        # 状态计算：把`database_uri`的结果保存到`self.database_uri`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        self.database_uri = database_uri
        # 状态计算：把`table_name`的结果保存到`self.table_name`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        self.table_name = table_name

    # 函数_table_ref：执行_table_ref对应的业务处理。
    # - 输入：无外部业务参数；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型str；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    @property
    def _table_ref(self) -> str:
        # 结果返回：把`f'loadTable("{self.database_uri}", `{self.table_name})'`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return (
            f'loadTable("{self.database_uri}", '
            f'`{self.table_name})'
        )

    # 函数_query_one：执行_query_one对应的业务处理。
    # - 输入：script:str；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型dict[str, Any]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把只读查询或来源发现步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    def _query_one(self, script: str) -> dict[str, Any]:
        # 结果返回：把`_first_record(self.adapter.run_readonly_query(script))`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return _first_record(self.adapter.run_readonly_query(script))

    # 函数_query_rows：执行_query_rows对应的业务处理。
    # - 输入：script:str；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型list[dict[str, Any]]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把只读查询或来源发现步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    def _query_rows(self, script: str) -> list[dict[str, Any]]:
        # 结果返回：把`_records_from_result(self.adapter.run_readonly_query(script))`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return _records_from_result(
            self.adapter.run_readonly_query(script)
        )

    # 函数_discover_fields：执行_discover_fields对应的业务处理。
    # - 输入：无外部业务参数；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型list[str]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把只读查询或来源发现步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    def _discover_fields(self) -> list[str]:
        # 状态计算：把`self.adapter.read_raw(self.table_name, database_uri=self.database_uri, limit=1)`的结果保存到`batch`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        batch = self.adapter.read_raw(
            self.table_name,
            database_uri=self.database_uri,
            limit=1,
        )
        # 结果返回：把`batch.raw_fields`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return batch.raw_fields

    # 函数_as_int：执行_as_int对应的业务处理。
    # - 输入：value:Any；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型int；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    @staticmethod
    def _as_int(value: Any) -> int:
        # 条件门禁：判断`value is None`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if value is None:
            # 结果返回：把`0`交给调用方并结束当前函数。
            # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
            # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
            return 0

        # 条件门禁：判断`isinstance(value, float) and math.isnan(value)`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if isinstance(value, float) and math.isnan(value):
            # 结果返回：把`0`交给调用方并结束当前函数。
            # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
            # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
            return 0

        # 异常边界：尝试执行可能失败的解析、查询、文件或类型转换步骤，并由后续处理保留错误证据。
        # - 数据变化：正常路径产生业务结果；异常路径不得静默伪造数据，应抛出、记录或隔离。
        # - 为什么这样写：把外部环境故障与业务合同失败分开，便于重试、回滚和准确验收。
        try:
            # 结果返回：把`int(value)`交给调用方并结束当前函数。
            # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
            # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
            return int(value)
        except (TypeError, ValueError, OverflowError):
            # 结果返回：把`0`交给调用方并结束当前函数。
            # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
            # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
            return 0

    # 函数collect：执行画像并返回结构化报告。
    # - 输入：无外部业务参数；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型DailyKProfileReport；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    def collect(self) -> DailyKProfileReport:
        """执行画像并返回结构化报告。"""

        # 状态计算：把`self._discover_fields()`的结果保存到`raw_fields`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        raw_fields = self._discover_fields()
        # 状态计算：把`[name for name in raw_fields if _IDENTIFIER_PATTERN.fullmatch(name)]`的结果保存到`valid_fields`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        valid_fields = [
            name
            for name in raw_fields
            if _IDENTIFIER_PATTERN.fullmatch(name)
        ]
        # 状态计算：把`set(valid_fields)`的结果保存到`available`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        available = set(valid_fields)

        # 状态计算：把`self._query_one(f'\n select\n count(*) as row_count,\n nunique(stock_code, true) as stock_count,\n …`的结果保存到`summary`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        summary = self._query_one(
            f"""
            select
                count(*) as row_count,
                nunique(stock_code, true) as stock_count,
                min(trade_date) as min_trade_date,
                max(trade_date) as max_trade_date
            from {self._table_ref}
            """
        )

        # 状态计算：把`',\n'.join((f'sum(isNull({name})) as {name}_null_count' for name in valid_fields))`的结果保存到`null_expressions`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        null_expressions = ",\n".join(
            f"sum(isNull({name})) as {name}_null_count"
            for name in valid_fields
        )
        # 状态计算：把`self._query_one(f'\n select\n {null_expressions}\n from {self._table_ref}\n ') if null_expressions …`的结果保存到`null_counts`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        null_counts = (
            self._query_one(
                f"""
                select
                    {null_expressions}
                from {self._table_ref}
                """
            )
            if null_expressions
            else {}
        )

        # 状态计算：把`{}`的结果保存到`duplicate_summary`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        duplicate_summary: dict[str, Any] = {}
        # 状态计算：把`[]`的结果保存到`duplicate_samples`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        duplicate_samples: list[dict[str, Any]] = []

        # 条件门禁：判断`{'stock_code', 'trade_date'}.issubset(available)`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if {"stock_code", "trade_date"}.issubset(available):
            # 状态计算：把`self._query_one(f'\n select\n count(*) as duplicate_group_count,\n sum(duplicate_count - 1)\n as du…`的结果保存到`duplicate_summary`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            duplicate_summary = self._query_one(
                f"""
                select
                    count(*) as duplicate_group_count,
                    sum(duplicate_count - 1)
                        as duplicate_extra_row_count
                from (
                    select count(*) as duplicate_count
                    from {self._table_ref}
                    group by stock_code, trade_date
                    having count(*) > 1
                )
                """
            )
            # 状态计算：把`self._query_rows(f'\n select top 20\n stock_code,\n trade_date,\n count(*) as duplicate_count\n fro…`的结果保存到`duplicate_samples`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            duplicate_samples = self._query_rows(
                f"""
                select top 20
                    stock_code,
                    trade_date,
                    count(*) as duplicate_count
                from {self._table_ref}
                group by stock_code, trade_date
                having count(*) > 1
                order by duplicate_count desc
                """
            )
            # 状态计算：把`self._as_int(duplicate_summary.get('duplicate_group_count'))`的结果保存到`duplicate_summary['duplicate_group_count']`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            duplicate_summary["duplicate_group_count"] = self._as_int(
                duplicate_summary.get("duplicate_group_count")
            )
            # 状态计算：把`self._as_int(duplicate_summary.get('duplicate_extra_row_count'))`的结果保存到`duplicate_summary['duplicate_extra_row_count']`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            duplicate_summary["duplicate_extra_row_count"] = self._as_int(
                duplicate_summary.get("duplicate_extra_row_count")
            )

        # 状态计算：把`{}`的结果保存到`ohlc_summary`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        ohlc_summary: dict[str, Any] = {}
        # 条件门禁：判断`{'open', 'high', 'low', 'close'}.issubset(available)`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if {"open", "high", "low", "close"}.issubset(available):
            # 状态计算：把`self._query_one(f'\n select\n count(*) as checked_row_count,\n sum(isNull(open)) as open_null_count…`的结果保存到`ohlc_summary`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            ohlc_summary = self._query_one(
                f"""
                select
                    count(*) as checked_row_count,
                    sum(isNull(open)) as open_null_count,
                    sum(isNull(high)) as high_null_count,
                    sum(isNull(low)) as low_null_count,
                    sum(isNull(close)) as close_null_count,
                    sum(iif(open <= 0, 1, 0)) as open_nonpositive_count,
                    sum(iif(high <= 0, 1, 0)) as high_nonpositive_count,
                    sum(iif(low <= 0, 1, 0)) as low_nonpositive_count,
                    sum(iif(close <= 0, 1, 0)) as close_nonpositive_count,
                    sum(iif(high < low, 1, 0)) as high_below_low_count,
                    sum(iif(high < open, 1, 0)) as high_below_open_count,
                    sum(iif(high < close, 1, 0)) as high_below_close_count,
                    sum(iif(low > open, 1, 0)) as low_above_open_count,
                    sum(iif(low > close, 1, 0)) as low_above_close_count
                from {self._table_ref}
                """
            )

            # 状态计算：把`('open_null_count', 'high_null_count', 'low_null_count', 'close_null_count')`的结果保存到`missing_keys`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            missing_keys = (
                "open_null_count",
                "high_null_count",
                "low_null_count",
                "close_null_count",
            )
            # 状态计算：把`('open_nonpositive_count', 'high_nonpositive_count', 'low_nonpositive_count', 'close_nonpositive_co…`的结果保存到`anomaly_keys`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            anomaly_keys = (
                "open_nonpositive_count",
                "high_nonpositive_count",
                "low_nonpositive_count",
                "close_nonpositive_count",
                "high_below_low_count",
                "high_below_open_count",
                "high_below_close_count",
                "low_above_open_count",
                "low_above_close_count",
            )
            # 状态计算：把`sum((self._as_int(ohlc_summary.get(key)) for key in missing_keys))`的结果保存到`ohlc_summary['missing_ohlc_count']`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            ohlc_summary["missing_ohlc_count"] = sum(
                self._as_int(ohlc_summary.get(key))
                for key in missing_keys
            )
            # 状态计算：把`sum((self._as_int(ohlc_summary.get(key)) for key in anomaly_keys))`的结果保存到`ohlc_summary['ohlc_logic_anomaly_count']`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            ohlc_summary["ohlc_logic_anomaly_count"] = sum(
                self._as_int(ohlc_summary.get(key))
                for key in anomaly_keys
            )

        # 状态计算：把`{}`的结果保存到`change_formula_summary`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        change_formula_summary: dict[str, Any] = {}
        # 状态计算：把`[]`的结果保存到`change_formula_samples`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        change_formula_samples: list[dict[str, Any]] = []
        # 状态计算：把`{'stock_code', 'trade_date', 'close', 'price_change', 'pct_change'}`的结果保存到`formula_fields`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        formula_fields = {
            "stock_code",
            "trade_date",
            "close",
            "price_change",
            "pct_change",
        }

        # 条件门禁：判断`formula_fields.issubset(available)`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if formula_fields.issubset(available):
            # 状态计算：把`f'\n select\n stock_code,\n trade_date,\n close,\n price_change,\n pct_change,\n move(close, 1) as …`的结果保存到`context_query`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            context_query = f"""
                select
                    stock_code,
                    trade_date,
                    close,
                    price_change,
                    pct_change,
                    move(close, 1) as prev_close
                from {self._table_ref}
                context by stock_code
                csort trade_date
            """
            # 状态计算：把`self._query_one(f'\n select\n count(*) as comparable_row_count,\n sum(\n iif(\n abs(\n price_change…`的结果保存到`change_formula_summary`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            change_formula_summary = self._query_one(
                f"""
                select
                    count(*) as comparable_row_count,
                    sum(
                        iif(
                            abs(
                                price_change
                                - (close - prev_close)
                            ) > 0.0001,
                            1,
                            0
                        )
                    ) as price_change_mismatch_count,
                    sum(
                        iif(
                            abs(
                                pct_change
                                - (
                                    (close / prev_close - 1)
                                    * 100
                                )
                            ) > 0.01,
                            1,
                            0
                        )
                    ) as pct_change_standard_mismatch_count,
                    sum(
                        iif(
                            abs(
                                pct_change
                                - (
                                    (prev_close / close - 1)
                                    * 100
                                )
                            ) > 0.01,
                            1,
                            0
                        )
                    ) as pct_change_inverse_mismatch_count,
                    sum(
                        iif(
                            abs(
                                pct_change
                                - (
                                    (prev_close - close)
                                    / prev_close
                                    * 100
                                )
                            ) > 0.01,
                            1,
                            0
                        )
                    ) as pct_change_negated_standard_mismatch_count
                from ({context_query})
                where
                    not isNull(prev_close)
                    and not isNull(close)
                    and prev_close != 0
                    and close != 0
                    and not isNull(price_change)
                    and not isNull(pct_change)
                """
            )
            # 状态计算：把`self._query_rows(f'\n select top 20\n stock_code,\n trade_date,\n prev_close,\n close,\n price_chan…`的结果保存到`change_formula_samples`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            change_formula_samples = self._query_rows(
                f"""
                select top 20
                    stock_code,
                    trade_date,
                    prev_close,
                    close,
                    price_change,
                    close - prev_close
                        as expected_price_change,
                    pct_change,
                    (close / prev_close - 1) * 100
                        as expected_standard_pct_change,
                    (prev_close / close - 1) * 100
                        as expected_inverse_pct_change,
                    (prev_close - close) / prev_close * 100
                        as expected_negated_standard_pct_change
                from ({context_query})
                where
                    not isNull(prev_close)
                    and not isNull(close)
                    and prev_close != 0
                    and close != 0
                    and not isNull(price_change)
                    and not isNull(pct_change)
                    and (
                        abs(
                            price_change
                            - (close - prev_close)
                        ) > 0.0001
                        or abs(
                            pct_change
                            - (
                                (close / prev_close - 1)
                                * 100
                            )
                        ) > 0.01
                    )
                """
            )

        # 状态计算：把`{}`的结果保存到`amount_volume_summary`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        amount_volume_summary: dict[str, Any] = {}
        # 条件门禁：判断`{'amount', 'volume'}.issubset(available)`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if {"amount", "volume"}.issubset(available):
            # 状态计算：把`self._query_one(f'\n select\n count(*) as comparable_row_count,\n min(amount / volume)\n as min_amo…`的结果保存到`amount_volume_summary`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            amount_volume_summary = self._query_one(
                f"""
                select
                    count(*) as comparable_row_count,
                    min(amount / volume)
                        as min_amount_per_volume,
                    avg(amount / volume)
                        as avg_amount_per_volume,
                    max(amount / volume)
                        as max_amount_per_volume
                from {self._table_ref}
                where
                    not isNull(amount)
                    and not isNull(volume)
                    and amount > 0
                    and volume > 0
                """
            )

        # 状态计算：把`{}`的结果保存到`adjustment_summary`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        adjustment_summary: dict[str, Any] = {}
        # 条件门禁：判断`{'adj_factor', 'adj_price'}.issubset(available)`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if {"adj_factor", "adj_price"}.issubset(available):
            # 状态计算：把`self._query_one(f'\n select\n count(*) as row_count,\n sum(isNull(adj_factor))\n as adj_factor_null…`的结果保存到`adjustment_summary`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            adjustment_summary = self._query_one(
                f"""
                select
                    count(*) as row_count,
                    sum(isNull(adj_factor))
                        as adj_factor_null_count,
                    sum(
                        iif(
                            isNull(adj_factor),
                            0,
                            iif(adj_factor == 1, 1, 0)
                        )
                    ) as adj_factor_equal_one_count,
                    sum(
                        iif(
                            isNull(adj_factor),
                            0,
                            iif(adj_factor != 1, 1, 0)
                        )
                    ) as adj_factor_non_one_count,
                    sum(isNull(adj_price))
                        as adj_price_null_count,
                    sum(
                        iif(
                            isNull(adj_price),
                            0,
                            iif(
                                isNull(close),
                                0,
                                iif(
                                    abs(adj_price - close) <= 0.0001,
                                    1,
                                    0
                                )
                            )
                        )
                    ) as adj_price_equal_close_count,
                    sum(
                        iif(
                            isNull(adj_price),
                            0,
                            iif(
                                isNull(close),
                                0,
                                iif(
                                    abs(adj_price - close) > 0.0001,
                                    1,
                                    0
                                )
                            )
                        )
                    ) as adj_price_close_difference_count
                from {self._table_ref}
                """
            )

        # 状态计算：把`self._evaluate(raw_fields=raw_fields, null_counts=null_counts, duplicate_summary=duplicate_summary,…`的结果保存到`(checks, pending, overall, blocks)`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        checks, pending, overall, blocks = self._evaluate(
            raw_fields=raw_fields,
            null_counts=null_counts,
            duplicate_summary=duplicate_summary,
            ohlc_summary=ohlc_summary,
            change_formula_summary=change_formula_summary,
        )

        # 结果返回：把`DailyKProfileReport(database_uri=self.database_uri, table_name=self.table_name, generated_at=_utc_now(), raw_fields=raw…`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return DailyKProfileReport(
            database_uri=self.database_uri,
            table_name=self.table_name,
            generated_at=_utc_now(),
            raw_fields=raw_fields,
            summary=summary,
            null_counts=null_counts,
            duplicate_summary=duplicate_summary,
            duplicate_samples=duplicate_samples,
            ohlc_summary=ohlc_summary,
            change_formula_summary=change_formula_summary,
            change_formula_samples=change_formula_samples,
            amount_volume_summary=amount_volume_summary,
            adjustment_summary=adjustment_summary,
            checks=checks,
            pending_confirmations=pending,
            overall_status=overall,
            blocks_downstream=blocks,
        )

    # 函数_evaluate：把画像指标转换成质量检查和待确认事项。
    # - 输入：raw_fields:list[str]、null_counts:dict[str, Any]、duplicate_summary:dict[str, Any]、ohlc_summary:dict[str, Any]、change_formula_summary:dict[str, Any]；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型tuple[list[dict[str, Any]], list[dict[str, Any]], QualitySt…；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    def _evaluate(
        self,
        *,
        raw_fields: list[str],
        null_counts: dict[str, Any],
        duplicate_summary: dict[str, Any],
        ohlc_summary: dict[str, Any],
        change_formula_summary: dict[str, Any],
    ) -> tuple[
        list[dict[str, Any]],
        list[dict[str, Any]],
        QualityStatus,
        bool,
    ]:
        """把画像指标转换成质量检查和待确认事项。"""

        # 状态计算：把`[]`的结果保存到`checks`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        checks: list[dict[str, Any]] = []
        # 状态计算：把`[]`的结果保存到`pending`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        pending: list[dict[str, Any]] = []
        # 状态计算：把`False`的结果保存到`blocking_failure`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        blocking_failure = False
        # 状态计算：把`False`的结果保存到`has_warning`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        has_warning = False

        # 状态计算：把`sorted(set(REQUIRED_FIELDS) - set(raw_fields))`的结果保存到`missing_fields`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        missing_fields = sorted(set(REQUIRED_FIELDS) - set(raw_fields))
        # 显式调用：执行`checks.append({'check_name': '必需字段完整性', 'status': QualityStatus.PASSED.value if not missing_fields else QualityStatus.FAILED.value, 'blocki…`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
        # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
        # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
        checks.append(
            {
                "check_name": "必需字段完整性",
                "status": (
                    QualityStatus.PASSED.value
                    if not missing_fields
                    else QualityStatus.FAILED.value
                ),
                "blocking": bool(missing_fields),
                "details": {"missing_fields": missing_fields},
            }
        )
        # 状态计算：把`blocking_failure or bool(missing_fields)`的结果保存到`blocking_failure`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        blocking_failure = blocking_failure or bool(missing_fields)

        # 状态计算：把`self._as_int(null_counts.get('stock_code_null_count')) + self._as_int(null_counts.get('trade_date_n…`的结果保存到`key_null_count`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        key_null_count = (
            self._as_int(
                null_counts.get("stock_code_null_count")
            )
            + self._as_int(
                null_counts.get("trade_date_null_count")
            )
        )
        # 显式调用：执行`checks.append({'check_name': '主键字段空值', 'status': QualityStatus.PASSED.value if key_null_count == 0 else QualityStatus.FAILED.value, 'blocki…`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
        # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
        # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
        checks.append(
            {
                "check_name": "主键字段空值",
                "status": (
                    QualityStatus.PASSED.value
                    if key_null_count == 0
                    else QualityStatus.FAILED.value
                ),
                "blocking": key_null_count > 0,
                "details": {"null_count": key_null_count},
            }
        )
        # 状态计算：把`blocking_failure or key_null_count > 0`的结果保存到`blocking_failure`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        blocking_failure = blocking_failure or key_null_count > 0

        # 状态计算：把`self._as_int(duplicate_summary.get('duplicate_extra_row_count'))`的结果保存到`duplicate_extra`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        duplicate_extra = self._as_int(
            duplicate_summary.get("duplicate_extra_row_count")
        )
        # 显式调用：执行`checks.append({'check_name': '股票代码与交易日期重复', 'status': QualityStatus.PASSED.value if duplicate_extra == 0 else QualityStatus.FAILED.value, '…`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
        # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
        # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
        checks.append(
            {
                "check_name": "股票代码与交易日期重复",
                "status": (
                    QualityStatus.PASSED.value
                    if duplicate_extra == 0
                    else QualityStatus.FAILED.value
                ),
                "blocking": duplicate_extra > 0,
                "details": {
                    "duplicate_extra_row_count": duplicate_extra
                },
            }
        )
        # 状态计算：把`blocking_failure or duplicate_extra > 0`的结果保存到`blocking_failure`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        blocking_failure = blocking_failure or duplicate_extra > 0

        # 状态计算：把`self._as_int(ohlc_summary.get('ohlc_logic_anomaly_count'))`的结果保存到`ohlc_anomaly`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        ohlc_anomaly = self._as_int(
            ohlc_summary.get("ohlc_logic_anomaly_count")
        )
        # 显式调用：执行`checks.append({'check_name': 'OHLC逻辑关系', 'status': QualityStatus.PASSED.value if ohlc_anomaly == 0 else QualityStatus.WARNING.value, 'block…`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
        # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
        # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
        checks.append(
            {
                "check_name": "OHLC逻辑关系",
                "status": (
                    QualityStatus.PASSED.value
                    if ohlc_anomaly == 0
                    else QualityStatus.WARNING.value
                ),
                "blocking": False,
                "details": {
                    "ohlc_logic_anomaly_count": ohlc_anomaly
                },
            }
        )
        # 状态计算：把`has_warning or ohlc_anomaly > 0`的结果保存到`has_warning`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        has_warning = has_warning or ohlc_anomaly > 0

        # 状态计算：把`self._as_int(change_formula_summary.get('comparable_row_count'))`的结果保存到`comparable`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        comparable = self._as_int(
            change_formula_summary.get("comparable_row_count")
        )
        # 状态计算：把`self._as_int(change_formula_summary.get('pct_change_standard_mismatch_count'))`的结果保存到`standard_mismatch`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        standard_mismatch = self._as_int(
            change_formula_summary.get(
                "pct_change_standard_mismatch_count"
            )
        )
        # 状态计算：把`self._as_int(change_formula_summary.get('pct_change_inverse_mismatch_count'))`的结果保存到`inverse_mismatch`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        inverse_mismatch = self._as_int(
            change_formula_summary.get(
                "pct_change_inverse_mismatch_count"
            )
        )
        # 状态计算：把`self._as_int(change_formula_summary.get('pct_change_negated_standard_mismatch_count'))`的结果保存到`negated_standard_mismatch`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        negated_standard_mismatch = self._as_int(
            change_formula_summary.get(
                "pct_change_negated_standard_mismatch_count"
            )
        )
        # 状态计算：把`comparable == 0 or standard_mismatch > 0`的结果保存到`formula_pending`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        formula_pending = comparable == 0 or standard_mismatch > 0

        # 显式调用：执行`checks.append({'check_name': '涨跌幅公式一致性', 'status': QualityStatus.PENDING_CONFIRMATION.value if formula_pending else QualityStatus.PASSED.va…`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
        # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
        # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
        checks.append(
            {
                "check_name": "涨跌幅公式一致性",
                "status": (
                    QualityStatus.PENDING_CONFIRMATION.value
                    if formula_pending
                    else QualityStatus.PASSED.value
                ),
                "blocking": formula_pending,
                "details": {
                    "comparable_row_count": comparable,
                    "standard_mismatch_count": standard_mismatch,
                    "inverse_mismatch_count": inverse_mismatch,
                    "negated_standard_mismatch_count": (
                        negated_standard_mismatch
                    ),
                },
            }
        )

        # 条件门禁：判断`formula_pending`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if formula_pending:
            # 显式调用：执行`pending.append({'category': 'PCT_CHANGE_FORMULA', 'field': 'pct_change', 'blocking': True, 'description': '需要确认pct_change采用常规涨跌幅、反向分母公式、常规涨…`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
            # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
            # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
            pending.append(
                {
                    "category": "PCT_CHANGE_FORMULA",
                    "field": "pct_change",
                    "blocking": True,
                    "description": (
                        "需要确认pct_change采用常规涨跌幅、"
                        "反向分母公式、常规涨跌幅取反或其他公式。"
                    ),
                }
            )

        # 显式调用：执行`pending.extend([{'category': 'ADJUSTMENT_METHOD', 'field': 'open/high/low/close/adj_price', 'blocking': True, 'description': '价格复权口径尚未确认。'}…`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
        # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
        # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
        pending.extend(
            [
                {
                    "category": "ADJUSTMENT_METHOD",
                    "field": "open/high/low/close/adj_price",
                    "blocking": True,
                    "description": "价格复权口径尚未确认。",
                },
                {
                    "category": "VOLUME_UNIT",
                    "field": "volume",
                    "blocking": True,
                    "description": "成交量单位尚未确认。",
                },
                {
                    "category": "AMOUNT_UNIT",
                    "field": "amount",
                    "blocking": True,
                    "description": "成交额单位尚未确认。",
                },
                {
                    "category": "SHARE_UNIT",
                    "field": "float_shares/total_shares",
                    "blocking": True,
                    "description": "股本字段单位尚未确认。",
                },
                {
                    "category": "TRADE_DATE_SEMANTICS",
                    "field": "trade_date",
                    "blocking": False,
                    "description": "日期时区和时间语义尚未固化。",
                },
            ]
        )

        # 状态计算：把`blocking_failure or any((bool(item.get('blocking')) for item in pending))`的结果保存到`blocks`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        blocks = blocking_failure or any(
            bool(item.get("blocking")) for item in pending
        )

        # 条件门禁：判断`blocking_failure`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if blocking_failure:
            # 状态计算：把`QualityStatus.FAILED`的结果保存到`overall`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            overall = QualityStatus.FAILED
        # 条件门禁：判断`pending`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        elif pending:
            # 状态计算：把`QualityStatus.PENDING_CONFIRMATION`的结果保存到`overall`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            overall = QualityStatus.PENDING_CONFIRMATION
        # 条件门禁：判断`has_warning`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        elif has_warning:
            # 状态计算：把`QualityStatus.WARNING`的结果保存到`overall`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            overall = QualityStatus.WARNING
        else:
            # 状态计算：把`QualityStatus.PASSED`的结果保存到`overall`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            overall = QualityStatus.PASSED

        # 结果返回：把`(checks, pending, overall, blocks)`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return checks, pending, overall, blocks


# 函数build_parser：执行build_parser对应的业务处理。
# - 输入：无外部业务参数；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型argparse.ArgumentParser；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
# - 为什么这样写：把对象构造、字段映射或标准化转换步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def build_parser() -> argparse.ArgumentParser:
    # 状态计算：把`argparse.ArgumentParser(description='DolphinDB日K表只读画像与质量验收。')`的结果保存到`parser`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    parser = argparse.ArgumentParser(
        description="DolphinDB日K表只读画像与质量验收。"
    )
    # 显式调用：执行`parser.add_argument('--host', default='127.0.0.1')`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
    # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
    # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
    parser.add_argument("--host", default="127.0.0.1")
    # 显式调用：执行`parser.add_argument('--port', type=int, default=8848)`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
    # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
    # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
    parser.add_argument("--port", type=int, default=8848)
    # 显式调用：执行`parser.add_argument('--username', default='admin')`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
    # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
    # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
    parser.add_argument("--username", default="admin")
    # 显式调用：执行`parser.add_argument('--database-uri', default='dfs://A_STOCK_DAILY_K_DB')`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
    # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
    # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
    parser.add_argument(
        "--database-uri",
        default="dfs://A_STOCK_DAILY_K_DB",
    )
    # 显式调用：执行`parser.add_argument('--table', default='stock_daily_k')`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
    # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
    # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
    parser.add_argument("--table", default="stock_daily_k")
    # 显式调用：执行`parser.add_argument('--output', default='reports/task_005_daily_k_profile.json')`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
    # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
    # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
    parser.add_argument(
        "--output",
        default="reports/task_005_daily_k_profile.json",
    )
    # 结果返回：把`parser`交给调用方并结束当前函数。
    # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return parser


# 函数main：执行main对应的业务处理。
# - 输入：argv:Sequence[str] | None；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型int；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
# - 为什么这样写：把任务入口与流程编排步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def main(argv: Sequence[str] | None = None) -> int:
    # 状态计算：把`build_parser().parse_args(argv)`的结果保存到`args`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    args = build_parser().parse_args(argv)

    # 异常边界：尝试执行可能失败的解析、查询、文件或类型转换步骤，并由后续处理保留错误证据。
    # - 数据变化：正常路径产生业务结果；异常路径不得静默伪造数据，应抛出、记录或隔离。
    # - 为什么这样写：把外部环境故障与业务合同失败分开，便于重试、回滚和准确验收。
    try:
        # 状态计算：把`DolphinDBConnectionSettings(host=args.host, port=args.port, username=args.username, password=resolv…`的结果保存到`settings`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        settings = DolphinDBConnectionSettings(
            host=args.host,
            port=args.port,
            username=args.username,
            password=resolve_password(),
        )
        # 状态计算：把`DolphinDBDataSourceAdapter(settings=settings)`的结果保存到`adapter`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        adapter = DolphinDBDataSourceAdapter(settings=settings)
        # 状态计算：把`adapter.health_check()`的结果保存到`health`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        health = adapter.health_check()

        # 条件门禁：判断`health.blocks_downstream`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if health.blocks_downstream:
            # 显式调用：执行`print(f'健康检查失败：{health.description}')`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
            # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
            # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
            print(f"健康检查失败：{health.description}")
            # 结果返回：把`1`交给调用方并结束当前函数。
            # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
            # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
            return 1

        # 状态计算：把`DolphinDBDailyKProfiler(adapter=adapter, database_uri=args.database_uri, table_name=args.table).col…`的结果保存到`report`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        report = DolphinDBDailyKProfiler(
            adapter=adapter,
            database_uri=args.database_uri,
            table_name=args.table,
        ).collect()
    except DataContractError as exc:
        # 显式调用：执行`print(f'画像失败：{exc}')`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
        # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
        # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
        print(f"画像失败：{exc}")
        # 结果返回：把`2`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return 2

    # 状态计算：把`Path(args.output)`的结果保存到`output_path`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    output_path = Path(args.output)
    # 显式调用：执行`output_path.parent.mkdir(parents=True, exist_ok=True)`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
    # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
    # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
    output_path.parent.mkdir(parents=True, exist_ok=True)
    # 显式调用：执行`output_path.write_text(json.dumps(report.to_dict(), ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
    # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
    # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
    output_path.write_text(
        json.dumps(
            report.to_dict(),
            ensure_ascii=False,
            indent=2,
            allow_nan=False,
        ),
        encoding="utf-8",
    )

    # 显式调用：执行`print('=== 日K数据只读画像完成 ===')`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
    # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
    # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
    print("=== 日K数据只读画像完成 ===")
    # 显式调用：执行`print(f'来源：{report.database_uri}/{report.table_name}')`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
    # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
    # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
    print(f"来源：{report.database_uri}/{report.table_name}")
    # 显式调用：执行`print(f"总行数：{report.summary.get('row_count')}")`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
    # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
    # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
    print(f"总行数：{report.summary.get('row_count')}")
    # 显式调用：执行`print(f"股票数量：{report.summary.get('stock_count')}")`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
    # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
    # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
    print(f"股票数量：{report.summary.get('stock_count')}")
    # 显式调用：执行`print(f"最早日期：{report.summary.get('min_trade_date')}")`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
    # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
    # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
    print(f"最早日期：{report.summary.get('min_trade_date')}")
    # 显式调用：执行`print(f"最晚日期：{report.summary.get('max_trade_date')}")`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
    # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
    # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
    print(f"最晚日期：{report.summary.get('max_trade_date')}")
    # 显式调用：执行`print(f"重复额外行数：{report.duplicate_summary.get('duplicate_extra_row_count')}")`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
    # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
    # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
    print(
        "重复额外行数："
        f"{report.duplicate_summary.get('duplicate_extra_row_count')}"
    )
    # 显式调用：执行`print(f"OHLC逻辑异常计数：{report.ohlc_summary.get('ohlc_logic_anomaly_count')}")`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
    # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
    # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
    print(
        "OHLC逻辑异常计数："
        f"{report.ohlc_summary.get('ohlc_logic_anomaly_count')}"
    )
    # 显式调用：执行`print(f"涨跌幅常规公式不匹配数：{report.change_formula_summary.get('pct_change_standard_mismatch_count')}")`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
    # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
    # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
    print(
        "涨跌幅常规公式不匹配数："
        f"{report.change_formula_summary.get('pct_change_standard_mismatch_count')}"
    )
    # 显式调用：执行`print(f"涨跌幅反向分母公式不匹配数：{report.change_formula_summary.get('pct_change_inverse_mismatch_count')}")`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
    # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
    # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
    print(
        "涨跌幅反向分母公式不匹配数："
        f"{report.change_formula_summary.get('pct_change_inverse_mismatch_count')}"
    )
    # 显式调用：执行`print(f"涨跌幅常规公式取反不匹配数：{report.change_formula_summary.get('pct_change_negated_standard_mismatch_count')}")`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
    # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
    # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
    print(
        "涨跌幅常规公式取反不匹配数："
        f"{report.change_formula_summary.get('pct_change_negated_standard_mismatch_count')}"
    )
    # 显式调用：执行`print(f"复权因子等于1行数：{report.adjustment_summary.get('adj_factor_equal_one_count')}")`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
    # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
    # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
    print(
        "复权因子等于1行数："
        f"{report.adjustment_summary.get('adj_factor_equal_one_count')}"
    )
    # 显式调用：执行`print(f"复权价等于收盘价行数：{report.adjustment_summary.get('adj_price_equal_close_count')}")`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
    # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
    # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
    print(
        "复权价等于收盘价行数："
        f"{report.adjustment_summary.get('adj_price_equal_close_count')}"
    )
    # 显式调用：执行`print(f'整体状态：{report.overall_status.value}')`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
    # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
    # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
    print(f"整体状态：{report.overall_status.value}")
    # 显式调用：执行`print(f'阻断下游：{report.blocks_downstream}')`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
    # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
    # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
    print(f"阻断下游：{report.blocks_downstream}")
    # 显式调用：执行`print(f'完整报告：{output_path}')`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
    # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
    # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
    print(f"完整报告：{output_path}")
    # 结果返回：把`0`交给调用方并结束当前函数。
    # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return 0


# 条件门禁：判断`__name__ == '__main__'`，条件成立时进入对应的数据、安全或异常处理分支。
# - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
# - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
if __name__ == "__main__":
    # 错误阻断：抛出`SystemExit(main())`并停止当前正常路径。
    # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
    # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
    raise SystemExit(main())
