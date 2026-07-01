# 模块总览：分层验证日K复权相关来源字段、代数关系和可确认语义。
# - 输入输出：输入为真实日K样本和字段关系；输出为公式层、统计层、业务语义层的独立证据。
# - 数据与安全：代数公式成立不等于已确认前复权或后复权，未知方向必须继续保留警告。
# - 运行边界：导入模块和阅读注释不会触发数据库写入；只有显式调用对应函数并满足门禁时才执行I/O。
# - 为什么这样写：先声明职责、单位、时点和副作用边界，读者可以在阅读实现前建立正确的金融与工程语境。
"""DolphinDB日K复权字段分层只读核验。

本模块不再尝试用一个全表公式解释所有记录，而是按以下维度分层：

1. deduct_value 是否为零；
2. 公司行为字段是否存在非零值；
3. adj_factor 是否发生变化；
4. 公司行为日与普通交易日。

全部查询只读，不修改 DolphinDB。
"""

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
# 依赖导入：加载`import time`所提供的类型、标准库或项目内能力。
# - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
# - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
import time
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
# 依赖导入：加载`from .dolphindb_daily_profile import _first_record, _records_from_result`所提供的类型、标准库或项目内能力。
# - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
# - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
from .dolphindb_daily_profile import (
    _first_record,
    _records_from_result,
)
# 依赖导入：加载`from .dolphindb_probe import resolve_password`所提供的类型、标准库或项目内能力。
# - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
# - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
from .dolphindb_probe import resolve_password


# 关键常量_STOCK_CODE_PATTERN：集中保存`re.compile('^[0-9A-Za-z._-]+$')`对应的合同值、Schema集合或运行边界。
# - 来源与范围：该值来自当前项目任务、配置、真实数据画像或安全合同；未明确说明时不得外推为行业统一标准。
# - 单位与实例：数值单位由变量名、相邻校验和调用语义共同限定；字符串用于版本、字段、状态或DolphinDB对象标识。
# - 为什么这样写：集中命名固定参数可避免魔法值散落，并让升级、审计和回归测试有稳定锚点。
_STOCK_CODE_PATTERN = re.compile(r"^[0-9A-Za-z._-]+$")
# 关键常量_EPSILON：集中保存`1e-06`对应的合同值、Schema集合或运行边界。
# - 来源与范围：该值来自当前项目任务、配置、真实数据画像或安全合同；未明确说明时不得外推为行业统一标准。
# - 单位与实例：数值单位由变量名、相邻校验和调用语义共同限定；字符串用于版本、字段、状态或DolphinDB对象标识。
# - 为什么这样写：集中命名固定参数可避免魔法值散落，并让升级、审计和回归测试有稳定锚点。
_EPSILON = 0.000001
# 关键常量_PRICE_TOLERANCE：集中保存`0.01`对应的合同值、Schema集合或运行边界。
# - 来源与范围：该值来自当前项目任务、配置、真实数据画像或安全合同；未明确说明时不得外推为行业统一标准。
# - 单位与实例：数值单位由变量名、相邻校验和调用语义共同限定；字符串用于版本、字段、状态或DolphinDB对象标识。
# - 为什么这样写：集中命名固定参数可避免魔法值散落，并让升级、审计和回归测试有稳定锚点。
_PRICE_TOLERANCE = 0.01

# 关键常量_FORMULA_FIELDS：集中保存`{'adj_price_equals_close_multiply_factor': 'close * adj_factor', 'adj_price_equals_close_divide_fac…`对应的合同值、Schema集合或运行边界。
# - 来源与范围：该值来自当前项目任务、配置、真实数据画像或安全合同；未明确说明时不得外推为行业统一标准。
# - 单位与实例：数值单位由变量名、相邻校验和调用语义共同限定；字符串用于版本、字段、状态或DolphinDB对象标识。
# - 为什么这样写：集中命名固定参数可避免魔法值散落，并让升级、审计和回归测试有稳定锚点。
_FORMULA_FIELDS = {
    "adj_price_equals_close_multiply_factor": (
        "close * adj_factor"
    ),
    "adj_price_equals_close_divide_factor": (
        "close / adj_factor"
    ),
    "adj_price_equals_close_multiply_factor_plus_deduct": (
        "close * adj_factor + deduct_value"
    ),
    "adj_price_equals_close_plus_deduct_multiply_factor": (
        "(close + deduct_value) * adj_factor"
    ),
    "adj_price_equals_close_multiply_factor_minus_deduct": (
        "close * adj_factor - deduct_value"
    ),
    "adj_price_equals_close_minus_deduct_multiply_factor": (
        "(close - deduct_value) * adj_factor"
    ),
}


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


# 函数_json_safe：把数据类、日期、枚举和非有限浮点数转成标准JSON值。
# - 输入：value:Any；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型Any；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
# - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def _json_safe(value: Any) -> Any:
    """把数据类、日期、枚举和非有限浮点数转成标准JSON值。"""

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
        return {
            str(key): _json_safe(item)
            for key, item in value.items()
        }

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
    if enum_value is not None and not isinstance(
        value,
        (str, bytes),
    ):
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


# 类AdjustmentLayerReport：复权字段分层核验报告。
# - 结构：继承或实现object；类体约包含13个字段或常量、1个方法。
# - 数据变化：类定义阶段不执行隐式I/O，实例只在构造或显式方法调用时改变受控状态。
# - 实操：调用方通过该类型集中传递配置、记录、服务或结果，避免跨模块使用无约束字典。
# - 为什么这样写：强类型边界能集中维护单位、时点、主键和安全不变量，并降低供应商耦合。
@dataclass(slots=True)
class AdjustmentLayerReport:
    """复权字段分层核验报告。"""

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
    # 状态计算：把`无`的结果保存到`latest_trade_date`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    latest_trade_date: Any
    # 状态计算：把`无`的结果保存到`calendar_lag_days`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    calendar_lag_days: int | None
    # 状态计算：把`无`的结果保存到`global_layers`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    global_layers: dict[str, Any]
    # 状态计算：把`无`的结果保存到`formula_layers`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    formula_layers: list[dict[str, Any]]
    # 状态计算：把`无`的结果保存到`factor_change_summary`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    factor_change_summary: dict[str, Any]
    # 状态计算：把`无`的结果保存到`factor_change_samples`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    factor_change_samples: list[dict[str, Any]]
    # 状态计算：把`field(default_factory=list)`的结果保存到`conclusions`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    conclusions: list[dict[str, Any]] = field(default_factory=list)
    # 状态计算：把`field(default_factory=list)`的结果保存到`pending_confirmations`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    pending_confirmations: list[dict[str, Any]] = field(
        default_factory=list
    )
    # 状态计算：把`QualityStatus.PENDING_CONFIRMATION`的结果保存到`overall_status`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    overall_status: QualityStatus = (
        QualityStatus.PENDING_CONFIRMATION
    )
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


# 类DolphinDBAdjustmentLayerProfiler：按字段状态和公司行为分层核验复权关系。
# - 结构：继承或实现object；类体约包含0个字段或常量、25个方法。
# - 数据变化：类定义阶段不执行隐式I/O，实例只在构造或显式方法调用时改变受控状态。
# - 实操：调用方通过该类型集中传递配置、记录、服务或结果，避免跨模块使用无约束字典。
# - 为什么这样写：强类型边界能集中维护单位、时点、主键和安全不变量，并降低供应商耦合。
class DolphinDBAdjustmentLayerProfiler:
    """按字段状态和公司行为分层核验复权关系。"""

    # 函数__init__：执行__init__对应的业务处理。
    # - 输入：adapter:DolphinDBDataSourceAdapter、database_uri:str、table_name:str、factor_chunk_size:int；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型None；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    def __init__(
        self,
        adapter: DolphinDBDataSourceAdapter,
        database_uri: str = "dfs://A_STOCK_DAILY_K_DB",
        table_name: str = "stock_daily_k",
        factor_chunk_size: int = 100,
    ) -> None:
        # 显式调用：执行`adapter._validate_database_uri(database_uri)`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
        # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
        # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
        adapter._validate_database_uri(database_uri)
        # 显式调用：执行`adapter._validate_table_name(table_name)`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
        # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
        # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
        adapter._validate_table_name(table_name)

        # 条件门禁：判断`not isinstance(factor_chunk_size, int) or not 1 <= factor_chunk_size <= 500`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if (
            not isinstance(factor_chunk_size, int)
            or not 1 <= factor_chunk_size <= 500
        ):
            # 错误阻断：抛出`DataContractError('factor_chunk_size 必须是 1 到 500 之间的整数。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
            raise DataContractError(
                "factor_chunk_size 必须是 1 到 500 之间的整数。"
            )

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
        # 状态计算：把`factor_chunk_size`的结果保存到`self.factor_chunk_size`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        self.factor_chunk_size = factor_chunk_size
        # 状态计算：把`None`的结果保存到`self._stock_codes_cache`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        self._stock_codes_cache: list[str] | None = None
        # 状态计算：把`2`的结果保存到`self.transient_retry_count`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        self.transient_retry_count = 2

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

    # 函数_run_readonly_with_retry：对偶发文件打开失败执行有限次只读重试。
    # - 输入：script:str；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型Any；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    def _run_readonly_with_retry(self, script: str) -> Any:
        """对偶发文件打开失败执行有限次只读重试。"""

        # 状态计算：把`self.transient_retry_count + 1`的结果保存到`attempts`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        attempts = self.transient_retry_count + 1

        # 循环处理：逐项遍历`range(attempts)`，把当前元素绑定到`attempt`。
        # - 数据变化：每轮只处理一个来源记录、字段、文件或证据项，并显式累计到局部集合或输出对象。
        # - 为什么这样写：逐项处理便于保留行级血缘、隔离单项异常，并控制16GB单机上的峰值内存。
        for attempt in range(attempts):
            # 异常边界：尝试执行可能失败的解析、查询、文件或类型转换步骤，并由后续处理保留错误证据。
            # - 数据变化：正常路径产生业务结果；异常路径不得静默伪造数据，应抛出、记录或隔离。
            # - 为什么这样写：把外部环境故障与业务合同失败分开，便于重试、回滚和准确验收。
            try:
                # 结果返回：把`self.adapter.run_readonly_query(script)`交给调用方并结束当前函数。
                # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
                # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
                return self.adapter.run_readonly_query(script)
            except DataContractError as exc:
                # 状态计算：把`str(exc)`的结果保存到`message`，供当前逻辑后续校验、转换、累计或返回。
                # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
                # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
                message = str(exc)

                # 条件门禁：判断`"Can't open file" not in message or attempt >= attempts - 1`，条件成立时进入对应的数据、安全或异常处理分支。
                # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
                # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
                if (
                    "Can't open file" not in message
                    or attempt >= attempts - 1
                ):
                    # 错误阻断：抛出`无`并停止当前正常路径。
                    # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
                    # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
                    raise

                # 显式调用：执行`time.sleep(0.5 * (attempt + 1))`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
                # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
                # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
                time.sleep(0.5 * (attempt + 1))

        # 错误阻断：抛出`DataContractError('只读查询重试流程异常结束。')`并停止当前正常路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
        # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
        raise DataContractError("只读查询重试流程异常结束。")

    # 函数_query_one：执行_query_one对应的业务处理。
    # - 输入：script:str；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型dict[str, Any]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把只读查询或来源发现步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    def _query_one(self, script: str) -> dict[str, Any]:
        # 结果返回：把`_first_record(self._run_readonly_with_retry(script))`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return _first_record(
            self._run_readonly_with_retry(script)
        )

    # 函数_query_rows：执行_query_rows对应的业务处理。
    # - 输入：script:str；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型list[dict[str, Any]]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把只读查询或来源发现步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    def _query_rows(self, script: str) -> list[dict[str, Any]]:
        # 结果返回：把`_records_from_result(self._run_readonly_with_retry(script))`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return _records_from_result(
            self._run_readonly_with_retry(script)
        )

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

    # 函数_coverage：执行_coverage对应的业务处理。
    # - 输入：matched:Any、comparable:Any；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型float | None；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    @staticmethod
    def _coverage(
        matched: Any,
        comparable: Any,
    ) -> float | None:
        # 状态计算：把`DolphinDBAdjustmentLayerProfiler._as_int(comparable)`的结果保存到`comparable_count`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        comparable_count = (
            DolphinDBAdjustmentLayerProfiler._as_int(comparable)
        )

        # 条件门禁：判断`comparable_count <= 0`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if comparable_count <= 0:
            # 结果返回：把`None`交给调用方并结束当前函数。
            # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
            # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
            return None

        # 结果返回：把`DolphinDBAdjustmentLayerProfiler._as_int(matched) / comparable_count`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return (
            DolphinDBAdjustmentLayerProfiler._as_int(matched)
            / comparable_count
        )

    # 函数_calendar_lag_days：执行_calendar_lag_days对应的业务处理。
    # - 输入：value:Any；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型int | None；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    @staticmethod
    def _calendar_lag_days(value: Any) -> int | None:
        # 条件门禁：判断`value is None`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if value is None:
            # 结果返回：把`None`交给调用方并结束当前函数。
            # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
            # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
            return None

        # 条件门禁：判断`isinstance(value, datetime)`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if isinstance(value, datetime):
            # 状态计算：把`value.date()`的结果保存到`latest_date`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            latest_date = value.date()
        # 条件门禁：判断`isinstance(value, date)`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        elif isinstance(value, date):
            # 状态计算：把`value`的结果保存到`latest_date`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            latest_date = value
        else:
            # 状态计算：把`str(value).strip()`的结果保存到`text`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            text = str(value).strip()

            # 异常边界：尝试执行可能失败的解析、查询、文件或类型转换步骤，并由后续处理保留错误证据。
            # - 数据变化：正常路径产生业务结果；异常路径不得静默伪造数据，应抛出、记录或隔离。
            # - 为什么这样写：把外部环境故障与业务合同失败分开，便于重试、回滚和准确验收。
            try:
                # 状态计算：把`datetime.fromisoformat(text).date()`的结果保存到`latest_date`，供当前逻辑后续校验、转换、累计或返回。
                # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
                # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
                latest_date = datetime.fromisoformat(text).date()
            except ValueError:
                # 异常边界：尝试执行可能失败的解析、查询、文件或类型转换步骤，并由后续处理保留错误证据。
                # - 数据变化：正常路径产生业务结果；异常路径不得静默伪造数据，应抛出、记录或隔离。
                # - 为什么这样写：把外部环境故障与业务合同失败分开，便于重试、回滚和准确验收。
                try:
                    # 状态计算：把`date.fromisoformat(text[:10])`的结果保存到`latest_date`，供当前逻辑后续校验、转换、累计或返回。
                    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
                    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
                    latest_date = date.fromisoformat(text[:10])
                except ValueError:
                    # 结果返回：把`None`交给调用方并结束当前函数。
                    # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
                    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
                    return None

        # 结果返回：把`(datetime.now(timezone.utc).date() - latest_date).days`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return (
            datetime.now(timezone.utc).date() - latest_date
        ).days

    # 函数_quote_stock_code：执行_quote_stock_code对应的业务处理。
    # - 输入：stock_code:str；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型str；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    @staticmethod
    def _quote_stock_code(stock_code: str) -> str:
        # 条件门禁：判断`not _STOCK_CODE_PATTERN.fullmatch(stock_code)`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if not _STOCK_CODE_PATTERN.fullmatch(stock_code):
            # 错误阻断：抛出`DataContractError(f'发现不安全的股票代码：{stock_code!r}')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
            raise DataContractError(
                f"发现不安全的股票代码：{stock_code!r}"
            )

        # 结果返回：把`f'"{stock_code}"'`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return f'"{stock_code}"'

    # 函数_chunked：执行_chunked对应的业务处理。
    # - 输入：values:list[str]、size:int；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型list[list[str]]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    @staticmethod
    def _chunked(
        values: list[str],
        size: int,
    ) -> list[list[str]]:
        # 结果返回：把`[values[index:index + size] for index in range(0, len(values), size)]`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return [
            values[index:index + size]
            for index in range(0, len(values), size)
        ]

    # 函数_action_expression：公司行为字段任一非零时返回真。
    # - 输入：无外部业务参数；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型str；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    @staticmethod
    def _action_expression() -> str:
        """公司行为字段任一非零时返回真。"""

        # 结果返回：把`f'abs(nullFill(dividend, 0)) > {_EPSILON} or abs(nullFill(bonus_share, 0)) > {_EPSILON} or abs(nullFill(convert_share, …`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return (
            f"abs(nullFill(dividend, 0)) > {_EPSILON} "
            f"or abs(nullFill(bonus_share, 0)) > {_EPSILON} "
            f"or abs(nullFill(convert_share, 0)) > {_EPSILON} "
            f"or abs(nullFill(allot_share, 0)) > {_EPSILON} "
            f"or abs(nullFill(allot_price, 0)) > {_EPSILON}"
        )

    # 函数_load_stock_codes：执行_load_stock_codes对应的业务处理。
    # - 输入：无外部业务参数；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型list[str]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把只读查询或来源发现步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    def _load_stock_codes(self) -> list[str]:
        # 条件门禁：判断`self._stock_codes_cache is not None`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if self._stock_codes_cache is not None:
            # 结果返回：把`list(self._stock_codes_cache)`交给调用方并结束当前函数。
            # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
            # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
            return list(self._stock_codes_cache)

        # 状态计算：把`self._query_rows(f'\n select distinct stock_code\n from {self._table_ref}\n order by stock_code\n ')`的结果保存到`rows`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        rows = self._query_rows(
            f"""
            select distinct stock_code
            from {self._table_ref}
            order by stock_code
            """
        )

        # 状态计算：把`[]`的结果保存到`result`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        result: list[str] = []

        # 循环处理：逐项遍历`rows`，把当前元素绑定到`row`。
        # - 数据变化：每轮只处理一个来源记录、字段、文件或证据项，并显式累计到局部集合或输出对象。
        # - 为什么这样写：逐项处理便于保留行级血缘、隔离单项异常，并控制16GB单机上的峰值内存。
        for row in rows:
            # 状态计算：把`row.get('stock_code')`的结果保存到`value`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            value = row.get("stock_code")

            # 条件门禁：判断`value is None`，条件成立时进入对应的数据、安全或异常处理分支。
            # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
            # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
            if value is None:
                # 控制流：跳过本轮剩余步骤，使循环或占位分支按既定合同继续。
                # - 数据变化：本语句不直接改变业务记录，只调整当前执行路径。
                # - 为什么这样写：显式控制流比隐式嵌套更容易检查边界和异常处理。
                continue

            # 状态计算：把`str(value).strip()`的结果保存到`code`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            code = str(value).strip()

            # 条件门禁：判断`not code`，条件成立时进入对应的数据、安全或异常处理分支。
            # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
            # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
            if not code:
                # 控制流：跳过本轮剩余步骤，使循环或占位分支按既定合同继续。
                # - 数据变化：本语句不直接改变业务记录，只调整当前执行路径。
                # - 为什么这样写：显式控制流比隐式嵌套更容易检查边界和异常处理。
                continue

            # 显式调用：执行`self._quote_stock_code(code)`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
            # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
            # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
            self._quote_stock_code(code)
            # 显式调用：执行`result.append(code)`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
            # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
            # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
            result.append(code)

        # 状态计算：把`result`的结果保存到`self._stock_codes_cache`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        self._stock_codes_cache = result
        # 结果返回：把`list(result)`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return list(result)

    # 函数_layer_specs：执行_layer_specs对应的业务处理。
    # - 输入：无外部业务参数；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型list[tuple[str, bool, bool]]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    @staticmethod
    def _layer_specs() -> list[
        tuple[str, bool, bool]
    ]:
        # 结果返回：把`[('deduct_zero_action_zero', False, False), ('deduct_zero_action_nonzero', False, True), ('deduct_nonzero_action_zero',…`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return [
            ("deduct_zero_action_zero", False, False),
            ("deduct_zero_action_nonzero", False, True),
            ("deduct_nonzero_action_zero", True, False),
            ("deduct_nonzero_action_nonzero", True, True),
        ]

    # 函数_layer_condition：执行_layer_condition对应的业务处理。
    # - 输入：deduct_nonzero:bool、action_nonzero:bool；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型str；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    def _layer_condition(
        self,
        *,
        deduct_nonzero: bool,
        action_nonzero: bool,
    ) -> str:
        # 状态计算：把`f'abs(deduct_value) > {_EPSILON}' if deduct_nonzero else f'abs(deduct_value) <= {_EPSILON}'`的结果保存到`deduct_condition`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        deduct_condition = (
            f"abs(deduct_value) > {_EPSILON}"
            if deduct_nonzero
            else f"abs(deduct_value) <= {_EPSILON}"
        )
        # 状态计算：把`self._action_expression()`的结果保存到`action_expression`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        action_expression = self._action_expression()
        # 状态计算：把`f'({action_expression})' if action_nonzero else f'not ({action_expression})'`的结果保存到`action_condition`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        action_condition = (
            f"({action_expression})"
            if action_nonzero
            else f"not ({action_expression})"
        )
        # 结果返回：把`f'({deduct_condition}) and ({action_condition})'`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return (
            f"({deduct_condition}) and ({action_condition})"
        )

    # 函数_empty_global_layers：执行_empty_global_layers对应的业务处理。
    # - 输入：无外部业务参数；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型dict[str, Any]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    @staticmethod
    def _empty_global_layers() -> dict[str, Any]:
        # 结果返回：把`{'stock_code_count': 0, 'chunk_count': 0, 'row_count': 0, 'adj_factor_equal_one_count': 0, 'deduct_zero_count': 0, 'ded…`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return {
            "stock_code_count": 0,
            "chunk_count": 0,
            "row_count": 0,
            "adj_factor_equal_one_count": 0,
            "deduct_zero_count": 0,
            "deduct_nonzero_count": 0,
            "adj_price_equal_close_count": 0,
            "corporate_action_nonzero_count": 0,
        }

    # 函数_empty_formula_layer：执行_empty_formula_layer对应的业务处理。
    # - 输入：layer_name:str、deduct_nonzero:bool、action_nonzero:bool；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型dict[str, Any]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    @staticmethod
    def _empty_formula_layer(
        *,
        layer_name: str,
        deduct_nonzero: bool,
        action_nonzero: bool,
    ) -> dict[str, Any]:
        # 状态计算：把`{'layer_name': layer_name, 'deduct_nonzero': deduct_nonzero, 'action_nonzero': action_nonzero, 'sto…`的结果保存到`result`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        result: dict[str, Any] = {
            "layer_name": layer_name,
            "deduct_nonzero": deduct_nonzero,
            "action_nonzero": action_nonzero,
            "stock_code_count": 0,
            "chunk_count": 0,
            "comparable_row_count": 0,
        }

        # 循环处理：逐项遍历`_FORMULA_FIELDS`，把当前元素绑定到`name`。
        # - 数据变化：每轮只处理一个来源记录、字段、文件或证据项，并显式累计到局部集合或输出对象。
        # - 为什么这样写：逐项处理便于保留行级血缘、隔离单项异常，并控制16GB单机上的峰值内存。
        for name in _FORMULA_FIELDS:
            # 状态计算：把`0`的结果保存到`result[f'{name}_match_count']`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            result[f"{name}_match_count"] = 0

        # 结果返回：把`result`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return result

    # 函数_collect_layer_statistics_chunked：按股票代码分批完成全局与公式分层统计。
    # - 输入：无外部业务参数；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型tuple[dict[str, Any], list[dict[str, Any]]]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    def _collect_layer_statistics_chunked(
        self,
    ) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        """按股票代码分批完成全局与公式分层统计。"""

        # 状态计算：把`self._load_stock_codes()`的结果保存到`stock_codes`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        stock_codes = self._load_stock_codes()
        # 状态计算：把`self._chunked(stock_codes, self.factor_chunk_size)`的结果保存到`chunks`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        chunks = self._chunked(
            stock_codes,
            self.factor_chunk_size,
        )
        # 状态计算：把`self._action_expression()`的结果保存到`action`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        action = self._action_expression()

        # 状态计算：把`self._empty_global_layers()`的结果保存到`global_total`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        global_total = self._empty_global_layers()
        # 状态计算：把`len(stock_codes)`的结果保存到`global_total['stock_code_count']`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        global_total["stock_code_count"] = len(stock_codes)
        # 状态计算：把`len(chunks)`的结果保存到`global_total['chunk_count']`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        global_total["chunk_count"] = len(chunks)

        # 状态计算：把`{layer_name: self._empty_formula_layer(layer_name=layer_name, deduct_nonzero=deduct_nonzero, action…`的结果保存到`formula_totals`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        formula_totals = {
            layer_name: self._empty_formula_layer(
                layer_name=layer_name,
                deduct_nonzero=deduct_nonzero,
                action_nonzero=action_nonzero,
            )
            for (
                layer_name,
                deduct_nonzero,
                action_nonzero,
            ) in self._layer_specs()
        }

        # 循环处理：逐项遍历`formula_totals.values()`，把当前元素绑定到`total`。
        # - 数据变化：每轮只处理一个来源记录、字段、文件或证据项，并显式累计到局部集合或输出对象。
        # - 为什么这样写：逐项处理便于保留行级血缘、隔离单项异常，并控制16GB单机上的峰值内存。
        for total in formula_totals.values():
            # 状态计算：把`len(stock_codes)`的结果保存到`total['stock_code_count']`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            total["stock_code_count"] = len(stock_codes)
            # 状态计算：把`len(chunks)`的结果保存到`total['chunk_count']`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            total["chunk_count"] = len(chunks)

        # 循环处理：逐项遍历`chunks`，把当前元素绑定到`chunk`。
        # - 数据变化：每轮只处理一个来源记录、字段、文件或证据项，并显式累计到局部集合或输出对象。
        # - 为什么这样写：逐项处理便于保留行级血缘、隔离单项异常，并控制16GB单机上的峰值内存。
        for chunk in chunks:
            # 状态计算：把`', '.join((self._quote_stock_code(code) for code in chunk))`的结果保存到`literals`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            literals = ", ".join(
                self._quote_stock_code(code)
                for code in chunk
            )
            # 状态计算：把`['count(*) as row_count', f'sum(iif(abs(adj_factor - 1) <= {_EPSILON}, 1, 0)) as adj_factor_equal_o…`的结果保存到`fields`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            fields: list[str] = [
                "count(*) as row_count",
                (
                    "sum(iif("
                    f"abs(adj_factor - 1) <= {_EPSILON}, "
                    "1, 0)) as adj_factor_equal_one_count"
                ),
                (
                    "sum(iif("
                    f"abs(deduct_value) <= {_EPSILON}, "
                    "1, 0)) as deduct_zero_count"
                ),
                (
                    "sum(iif("
                    f"abs(deduct_value) > {_EPSILON}, "
                    "1, 0)) as deduct_nonzero_count"
                ),
                (
                    "sum(iif("
                    f"abs(adj_price - close) <= {_PRICE_TOLERANCE}, "
                    "1, 0)) as adj_price_equal_close_count"
                ),
                (
                    f"sum(iif({action}, 1, 0)) "
                    "as corporate_action_nonzero_count"
                ),
            ]

            # 循环处理：逐项遍历`self._layer_specs()`，把当前元素绑定到`(layer_name, deduct_nonzero, action_nonzero)`。
            # - 数据变化：每轮只处理一个来源记录、字段、文件或证据项，并显式累计到局部集合或输出对象。
            # - 为什么这样写：逐项处理便于保留行级血缘、隔离单项异常，并控制16GB单机上的峰值内存。
            for (
                layer_name,
                deduct_nonzero,
                action_nonzero,
            ) in self._layer_specs():
                # 状态计算：把`self._layer_condition(deduct_nonzero=deduct_nonzero, action_nonzero=action_nonzero)`的结果保存到`condition`，供当前逻辑后续校验、转换、累计或返回。
                # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
                # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
                condition = self._layer_condition(
                    deduct_nonzero=deduct_nonzero,
                    action_nonzero=action_nonzero,
                )
                # 显式调用：执行`fields.append(f'sum(iif(({condition}) and close != 0 and adj_factor != 0 and adj_price != 0, 1, 0)) as {layer_name}_comparable_row_count')`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
                # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
                # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
                fields.append(
                    "sum(iif("
                    f"({condition}) "
                    "and close != 0 "
                    "and adj_factor != 0 "
                    "and adj_price != 0, "
                    "1, 0)) "
                    f"as {layer_name}_comparable_row_count"
                )

                # 循环处理：逐项遍历`_FORMULA_FIELDS.items()`，把当前元素绑定到`(name, formula)`。
                # - 数据变化：每轮只处理一个来源记录、字段、文件或证据项，并显式累计到局部集合或输出对象。
                # - 为什么这样写：逐项处理便于保留行级血缘、隔离单项异常，并控制16GB单机上的峰值内存。
                for name, formula in _FORMULA_FIELDS.items():
                    # 显式调用：执行`fields.append(f'sum(iif(({condition}) and close != 0 and adj_factor != 0 and adj_price != 0 and abs(adj_price - ({formula})) <= {_PRICE_TOL…`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
                    # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
                    # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
                    fields.append(
                        "sum(iif("
                        f"({condition}) "
                        "and close != 0 "
                        "and adj_factor != 0 "
                        "and adj_price != 0 "
                        f"and abs(adj_price - ({formula})) "
                        f"<= {_PRICE_TOLERANCE}, "
                        "1, 0)) "
                        f"as {layer_name}_{name}_match_count"
                    )

            # 状态计算：把`self._query_one('select\n ' + ',\n '.join(fields) + f'\n from {self._table_ref}\n where stock_code …`的结果保存到`result`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            result = self._query_one(
                "select\n    "
                + ",\n    ".join(fields)
                + f"""
                from {self._table_ref}
                where stock_code in [{literals}]
                """
            )

            # 循环处理：逐项遍历`global_total`，把当前元素绑定到`key`。
            # - 数据变化：每轮只处理一个来源记录、字段、文件或证据项，并显式累计到局部集合或输出对象。
            # - 为什么这样写：逐项处理便于保留行级血缘、隔离单项异常，并控制16GB单机上的峰值内存。
            for key in global_total:
                # 条件门禁：判断`key in {'stock_code_count', 'chunk_count'}`，条件成立时进入对应的数据、安全或异常处理分支。
                # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
                # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
                if key in {"stock_code_count", "chunk_count"}:
                    # 控制流：跳过本轮剩余步骤，使循环或占位分支按既定合同继续。
                    # - 数据变化：本语句不直接改变业务记录，只调整当前执行路径。
                    # - 为什么这样写：显式控制流比隐式嵌套更容易检查边界和异常处理。
                    continue

                # 状态计算：把`self._as_int(global_total.get(key)) + self._as_int(result.get(key))`的结果保存到`global_total[key]`，供当前逻辑后续校验、转换、累计或返回。
                # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
                # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
                global_total[key] = (
                    self._as_int(global_total.get(key))
                    + self._as_int(result.get(key))
                )

            # 循环处理：逐项遍历`self._layer_specs()`，把当前元素绑定到`(layer_name, _, _)`。
            # - 数据变化：每轮只处理一个来源记录、字段、文件或证据项，并显式累计到局部集合或输出对象。
            # - 为什么这样写：逐项处理便于保留行级血缘、隔离单项异常，并控制16GB单机上的峰值内存。
            for (
                layer_name,
                _,
                _,
            ) in self._layer_specs():
                # 状态计算：把`formula_totals[layer_name]`的结果保存到`total`，供当前逻辑后续校验、转换、累计或返回。
                # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
                # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
                total = formula_totals[layer_name]
                # 状态计算：把`f'{layer_name}_comparable_row_count'`的结果保存到`comparable_key`，供当前逻辑后续校验、转换、累计或返回。
                # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
                # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
                comparable_key = (
                    f"{layer_name}_comparable_row_count"
                )
                # 状态计算：把`self._as_int(total.get('comparable_row_count')) + self._as_int(result.get(comparable_key))`的结果保存到`total['comparable_row_count']`，供当前逻辑后续校验、转换、累计或返回。
                # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
                # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
                total["comparable_row_count"] = (
                    self._as_int(
                        total.get("comparable_row_count")
                    )
                    + self._as_int(
                        result.get(comparable_key)
                    )
                )

                # 循环处理：逐项遍历`_FORMULA_FIELDS`，把当前元素绑定到`name`。
                # - 数据变化：每轮只处理一个来源记录、字段、文件或证据项，并显式累计到局部集合或输出对象。
                # - 为什么这样写：逐项处理便于保留行级血缘、隔离单项异常，并控制16GB单机上的峰值内存。
                for name in _FORMULA_FIELDS:
                    # 状态计算：把`f'{layer_name}_{name}_match_count'`的结果保存到`source_key`，供当前逻辑后续校验、转换、累计或返回。
                    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
                    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
                    source_key = (
                        f"{layer_name}_{name}_match_count"
                    )
                    # 状态计算：把`f'{name}_match_count'`的结果保存到`target_key`，供当前逻辑后续校验、转换、累计或返回。
                    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
                    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
                    target_key = f"{name}_match_count"
                    # 状态计算：把`self._as_int(total.get(target_key)) + self._as_int(result.get(source_key))`的结果保存到`total[target_key]`，供当前逻辑后续校验、转换、累计或返回。
                    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
                    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
                    total[target_key] = (
                        self._as_int(total.get(target_key))
                        + self._as_int(
                            result.get(source_key)
                        )
                    )

        # 状态计算：把`[]`的结果保存到`formula_layers`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        formula_layers: list[dict[str, Any]] = []

        # 循环处理：逐项遍历`self._layer_specs()`，把当前元素绑定到`(layer_name, _, _)`。
        # - 数据变化：每轮只处理一个来源记录、字段、文件或证据项，并显式累计到局部集合或输出对象。
        # - 为什么这样写：逐项处理便于保留行级血缘、隔离单项异常，并控制16GB单机上的峰值内存。
        for (
            layer_name,
            _,
            _,
        ) in self._layer_specs():
            # 状态计算：把`formula_totals[layer_name]`的结果保存到`total`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            total = formula_totals[layer_name]
            # 状态计算：把`total.get('comparable_row_count')`的结果保存到`comparable`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            comparable = total.get("comparable_row_count")
            # 状态计算：把`{name: self._coverage(total.get(f'{name}_match_count'), comparable) for name in _FORMULA_FIELDS}`的结果保存到`coverages`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            coverages = {
                name: self._coverage(
                    total.get(f"{name}_match_count"),
                    comparable,
                )
                for name in _FORMULA_FIELDS
            }
            # 状态计算：把`coverages`的结果保存到`total['candidate_coverages']`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            total["candidate_coverages"] = coverages
            # 状态计算：把`self._best_candidate(coverages)`的结果保存到`(total['best_candidate'], total['best_coverage'])`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            (
                total["best_candidate"],
                total["best_coverage"],
            ) = self._best_candidate(coverages)
            # 显式调用：执行`formula_layers.append(total)`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
            # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
            # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
            formula_layers.append(total)

        # 结果返回：把`(global_total, formula_layers)`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return global_total, formula_layers

    # 函数_collect_global_layers：执行_collect_global_layers对应的业务处理。
    # - 输入：无外部业务参数；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型dict[str, Any]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    def _collect_global_layers(self) -> dict[str, Any]:
        # 状态计算：把`self._action_expression()`的结果保存到`action`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        action = self._action_expression()

        # 结果返回：把`self._query_one(f'\n select\n count(*) as row_count,\n sum(\n iif(\n abs(adj_factor - 1) <= {_EPSILON},\n 1,\n 0\n )\n …`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return self._query_one(
            f"""
            select
                count(*) as row_count,
                sum(
                    iif(
                        abs(adj_factor - 1) <= {_EPSILON},
                        1,
                        0
                    )
                ) as adj_factor_equal_one_count,
                sum(
                    iif(
                        abs(deduct_value) <= {_EPSILON},
                        1,
                        0
                    )
                ) as deduct_zero_count,
                sum(
                    iif(
                        abs(deduct_value) > {_EPSILON},
                        1,
                        0
                    )
                ) as deduct_nonzero_count,
                sum(
                    iif(
                        abs(adj_price - close)
                            <= {_PRICE_TOLERANCE},
                        1,
                        0
                    )
                ) as adj_price_equal_close_count,
                sum(
                    iif({action}, 1, 0)
                ) as corporate_action_nonzero_count
            from {self._table_ref}
            """
        )

    # 函数_collect_formula_layer：执行_collect_formula_layer对应的业务处理。
    # - 输入：layer_name:str、deduct_nonzero:bool、action_nonzero:bool；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型dict[str, Any]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    def _collect_formula_layer(
        self,
        *,
        layer_name: str,
        deduct_nonzero: bool,
        action_nonzero: bool,
    ) -> dict[str, Any]:
        # 状态计算：把`f'abs(deduct_value) > {_EPSILON}' if deduct_nonzero else f'abs(deduct_value) <= {_EPSILON}'`的结果保存到`deduct_condition`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        deduct_condition = (
            f"abs(deduct_value) > {_EPSILON}"
            if deduct_nonzero
            else f"abs(deduct_value) <= {_EPSILON}"
        )
        # 状态计算：把`self._action_expression()`的结果保存到`action_expression`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        action_expression = self._action_expression()
        # 状态计算：把`f'({action_expression})' if action_nonzero else f'not ({action_expression})'`的结果保存到`action_condition`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        action_condition = (
            f"({action_expression})"
            if action_nonzero
            else f"not ({action_expression})"
        )

        # 状态计算：把`',\n'.join((f'sum(iif(abs(adj_price - ({formula})) <= {_PRICE_TOLERANCE}, 1, 0)) as {name}_match_co…`的结果保存到`match_expressions`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        match_expressions = ",\n".join(
            (
                "sum(iif("
                f"abs(adj_price - ({formula})) "
                f"<= {_PRICE_TOLERANCE}, 1, 0)) "
                f"as {name}_match_count"
            )
            for name, formula in _FORMULA_FIELDS.items()
        )

        # 状态计算：把`self._query_one(f'\n select\n count(*) as comparable_row_count,\n {match_expressions}\n from {self.…`的结果保存到`result`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        result = self._query_one(
            f"""
            select
                count(*) as comparable_row_count,
                {match_expressions}
            from {self._table_ref}
            where
                close != 0
                and adj_factor != 0
                and adj_price != 0
                and {deduct_condition}
                and {action_condition}
            """
        )
        # 状态计算：把`layer_name`的结果保存到`result['layer_name']`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        result["layer_name"] = layer_name
        # 状态计算：把`deduct_nonzero`的结果保存到`result['deduct_nonzero']`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        result["deduct_nonzero"] = deduct_nonzero
        # 状态计算：把`action_nonzero`的结果保存到`result['action_nonzero']`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        result["action_nonzero"] = action_nonzero

        # 状态计算：把`result.get('comparable_row_count')`的结果保存到`comparable`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        comparable = result.get("comparable_row_count")
        # 状态计算：把`{}`的结果保存到`coverages`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        coverages: dict[str, float | None] = {}

        # 循环处理：逐项遍历`_FORMULA_FIELDS`，把当前元素绑定到`name`。
        # - 数据变化：每轮只处理一个来源记录、字段、文件或证据项，并显式累计到局部集合或输出对象。
        # - 为什么这样写：逐项处理便于保留行级血缘、隔离单项异常，并控制16GB单机上的峰值内存。
        for name in _FORMULA_FIELDS:
            # 状态计算：把`self._coverage(result.get(f'{name}_match_count'), comparable)`的结果保存到`coverages[name]`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            coverages[name] = self._coverage(
                result.get(f"{name}_match_count"),
                comparable,
            )

        # 状态计算：把`coverages`的结果保存到`result['candidate_coverages']`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        result["candidate_coverages"] = coverages
        # 状态计算：把`self._best_candidate(coverages)`的结果保存到`(best_name, best_coverage)`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        best_name, best_coverage = self._best_candidate(coverages)
        # 状态计算：把`best_name`的结果保存到`result['best_candidate']`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        result["best_candidate"] = best_name
        # 状态计算：把`best_coverage`的结果保存到`result['best_coverage']`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        result["best_coverage"] = best_coverage
        # 结果返回：把`result`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return result

    # 函数_best_candidate：执行_best_candidate对应的业务处理。
    # - 输入：coverages:dict[str, Any]；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型tuple[str | None, float | None]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    @staticmethod
    def _best_candidate(
        coverages: dict[str, Any],
    ) -> tuple[str | None, float | None]:
        # 状态计算：把`{name: float(value) for name, value in coverages.items() if isinstance(value, (int, float)) and mat…`的结果保存到`valid`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        valid = {
            name: float(value)
            for name, value in coverages.items()
            if isinstance(value, (int, float))
            and math.isfinite(float(value))
        }

        # 条件门禁：判断`not valid`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if not valid:
            # 结果返回：把`(None, None)`交给调用方并结束当前函数。
            # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
            # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
            return None, None

        # 状态计算：把`max(valid, key=valid.get)`的结果保存到`best_name`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        best_name = max(valid, key=valid.get)
        # 结果返回：把`(best_name, valid[best_name])`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return best_name, valid[best_name]

    # 函数_empty_factor_change_summary：执行_empty_factor_change_summary对应的业务处理。
    # - 输入：无外部业务参数；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型dict[str, Any]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    @staticmethod
    def _empty_factor_change_summary() -> dict[str, Any]:
        # 结果返回：把`{'stock_code_count': 0, 'chunk_count': 0, 'factor_change_count': 0, 'factor_change_deduct_nonzero_count': 0, 'factor_ch…`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return {
            "stock_code_count": 0,
            "chunk_count": 0,
            "factor_change_count": 0,
            "factor_change_deduct_nonzero_count": 0,
            "factor_change_action_nonzero_count": 0,
            "factor_change_adj_price_equal_close_count": 0,
        }

    # 函数_merge_factor_change_summary：执行_merge_factor_change_summary对应的业务处理。
    # - 输入：total:dict[str, Any]、part:dict[str, Any]；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型None；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    def _merge_factor_change_summary(
        self,
        total: dict[str, Any],
        part: dict[str, Any],
    ) -> None:
        # 循环处理：逐项遍历`total`，把当前元素绑定到`key`。
        # - 数据变化：每轮只处理一个来源记录、字段、文件或证据项，并显式累计到局部集合或输出对象。
        # - 为什么这样写：逐项处理便于保留行级血缘、隔离单项异常，并控制16GB单机上的峰值内存。
        for key in total:
            # 条件门禁：判断`key in {'stock_code_count', 'chunk_count'}`，条件成立时进入对应的数据、安全或异常处理分支。
            # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
            # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
            if key in {"stock_code_count", "chunk_count"}:
                # 控制流：跳过本轮剩余步骤，使循环或占位分支按既定合同继续。
                # - 数据变化：本语句不直接改变业务记录，只调整当前执行路径。
                # - 为什么这样写：显式控制流比隐式嵌套更容易检查边界和异常处理。
                continue

            # 状态计算：把`self._as_int(total.get(key)) + self._as_int(part.get(key))`的结果保存到`total[key]`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            total[key] = (
                self._as_int(total.get(key))
                + self._as_int(part.get(key))
            )

    # 函数_collect_factor_changes：执行_collect_factor_changes对应的业务处理。
    # - 输入：无外部业务参数；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型tuple[dict[str, Any], list[dict[str, Any]]]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    def _collect_factor_changes(
        self,
    ) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        # 状态计算：把`self._load_stock_codes()`的结果保存到`stock_codes`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        stock_codes = self._load_stock_codes()
        # 状态计算：把`self._chunked(stock_codes, self.factor_chunk_size)`的结果保存到`chunks`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        chunks = self._chunked(
            stock_codes,
            self.factor_chunk_size,
        )
        # 状态计算：把`self._empty_factor_change_summary()`的结果保存到`total`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        total = self._empty_factor_change_summary()
        # 状态计算：把`len(stock_codes)`的结果保存到`total['stock_code_count']`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        total["stock_code_count"] = len(stock_codes)
        # 状态计算：把`len(chunks)`的结果保存到`total['chunk_count']`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        total["chunk_count"] = len(chunks)
        # 状态计算：把`self._action_expression()`的结果保存到`action`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        action = self._action_expression()
        # 状态计算：把`[]`的结果保存到`samples`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        samples: list[dict[str, Any]] = []

        # 循环处理：逐项遍历`chunks`，把当前元素绑定到`chunk`。
        # - 数据变化：每轮只处理一个来源记录、字段、文件或证据项，并显式累计到局部集合或输出对象。
        # - 为什么这样写：逐项处理便于保留行级血缘、隔离单项异常，并控制16GB单机上的峰值内存。
        for chunk in chunks:
            # 状态计算：把`', '.join((self._quote_stock_code(code) for code in chunk))`的结果保存到`literals`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            literals = ", ".join(
                self._quote_stock_code(code)
                for code in chunk
            )
            # 状态计算：把`f'\n select\n stock_code,\n trade_date,\n close,\n adj_price,\n adj_factor,\n deduct_value,\n divid…`的结果保存到`context_query`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            context_query = f"""
                select
                    stock_code,
                    trade_date,
                    close,
                    adj_price,
                    adj_factor,
                    deduct_value,
                    dividend,
                    bonus_share,
                    convert_share,
                    allot_share,
                    allot_price,
                    move(adj_factor, 1) as prev_adj_factor,
                    move(close, 1) as prev_close,
                    move(adj_price, 1) as prev_adj_price
                from {self._table_ref}
                where stock_code in [{literals}]
                context by stock_code
                csort trade_date
            """

            # 状态计算：把`self._query_one(f'\n select\n count(*) as factor_change_count,\n sum(\n iif(\n abs(deduct_value) > …`的结果保存到`part`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            part = self._query_one(
                f"""
                select
                    count(*) as factor_change_count,
                    sum(
                        iif(
                            abs(deduct_value) > {_EPSILON},
                            1,
                            0
                        )
                    ) as factor_change_deduct_nonzero_count,
                    sum(
                        iif({action}, 1, 0)
                    ) as factor_change_action_nonzero_count,
                    sum(
                        iif(
                            abs(adj_price - close)
                                <= {_PRICE_TOLERANCE},
                            1,
                            0
                        )
                    ) as factor_change_adj_price_equal_close_count
                from ({context_query})
                where
                    abs(adj_factor - prev_adj_factor)
                        > {_EPSILON}
                """
            )
            # 显式调用：执行`self._merge_factor_change_summary(total, part)`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
            # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
            # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
            self._merge_factor_change_summary(total, part)

            # 显式调用：执行`samples.extend(self._query_rows(f'\n select top 3\n stock_code,\n trade_date,\n prev_close,\n close,\n prev_adj_price,\n adj_price,\n prev_…`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
            # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
            # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
            samples.extend(
                self._query_rows(
                    f"""
                    select top 3
                        stock_code,
                        trade_date,
                        prev_close,
                        close,
                        prev_adj_price,
                        adj_price,
                        prev_adj_factor,
                        adj_factor,
                        deduct_value,
                        dividend,
                        bonus_share,
                        convert_share,
                        allot_share,
                        allot_price
                    from ({context_query})
                    where
                        abs(adj_factor - prev_adj_factor)
                            > {_EPSILON}
                    order by trade_date desc
                    """
                )
            )

        # 状态计算：把`{}`的结果保存到`unique_samples`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        unique_samples: dict[
            tuple[str, str],
            dict[str, Any],
        ] = {}

        # 循环处理：逐项遍历`samples`，把当前元素绑定到`row`。
        # - 数据变化：每轮只处理一个来源记录、字段、文件或证据项，并显式累计到局部集合或输出对象。
        # - 为什么这样写：逐项处理便于保留行级血缘、隔离单项异常，并控制16GB单机上的峰值内存。
        for row in samples:
            # 状态计算：把`(str(row.get('stock_code') or ''), str(row.get('trade_date') or ''))`的结果保存到`key`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            key = (
                str(row.get("stock_code") or ""),
                str(row.get("trade_date") or ""),
            )
            # 状态计算：把`row`的结果保存到`unique_samples[key]`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            unique_samples[key] = row

        # 状态计算：把`list(unique_samples.values())`的结果保存到`ordered`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        ordered = list(unique_samples.values())
        # 显式调用：执行`ordered.sort(key=lambda row: str(row.get('trade_date') or ''), reverse=True)`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
        # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
        # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
        ordered.sort(
            key=lambda row: str(row.get("trade_date") or ""),
            reverse=True,
        )
        # 结果返回：把`(total, ordered[:50])`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return total, ordered[:50]

    # 函数_evaluate：执行_evaluate对应的业务处理。
    # - 输入：formula_layers:list[dict[str, Any]]、factor_change_summary:dict[str, Any]、calendar_lag_days:int | None；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型tuple[list[dict[str, Any]], list[dict[str, Any]]]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    def _evaluate(
        self,
        *,
        formula_layers: list[dict[str, Any]],
        factor_change_summary: dict[str, Any],
        calendar_lag_days: int | None,
    ) -> tuple[
        list[dict[str, Any]],
        list[dict[str, Any]],
    ]:
        # 状态计算：把`[]`的结果保存到`conclusions`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        conclusions: list[dict[str, Any]] = []
        # 状态计算：把`[]`的结果保存到`pending`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        pending: list[dict[str, Any]] = []

        # 状态计算：把`[layer for layer in formula_layers if self._as_int(layer.get('comparable_row_count')) > 0]`的结果保存到`nonempty_layers`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        nonempty_layers = [
            layer
            for layer in formula_layers
            if self._as_int(
                layer.get("comparable_row_count")
            ) > 0
        ]

        # 循环处理：逐项遍历`nonempty_layers`，把当前元素绑定到`layer`。
        # - 数据变化：每轮只处理一个来源记录、字段、文件或证据项，并显式累计到局部集合或输出对象。
        # - 为什么这样写：逐项处理便于保留行级血缘、隔离单项异常，并控制16GB单机上的峰值内存。
        for layer in nonempty_layers:
            # 状态计算：把`layer.get('best_coverage')`的结果保存到`coverage`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            coverage = layer.get("best_coverage")
            # 状态计算：把`isinstance(coverage, (int, float)) and float(coverage) >= 0.99`的结果保存到`confirmed`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            confirmed = (
                isinstance(coverage, (int, float))
                and float(coverage) >= 0.99
            )
            # 显式调用：执行`conclusions.append({'topic': 'ADJUSTMENT_LAYER_FORMULA', 'layer_name': layer.get('layer_name'), 'candidate': layer.get('best_candidate'), '…`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
            # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
            # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
            conclusions.append(
                {
                    "topic": "ADJUSTMENT_LAYER_FORMULA",
                    "layer_name": layer.get("layer_name"),
                    "candidate": layer.get("best_candidate"),
                    "coverage": coverage,
                    "confirmed": confirmed,
                }
            )

            # 条件门禁：判断`not confirmed`，条件成立时进入对应的数据、安全或异常处理分支。
            # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
            # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
            if not confirmed:
                # 显式调用：执行`pending.append({'category': 'ADJUSTMENT_LAYER_FORMULA', 'layer_name': layer.get('layer_name'), 'blocking': True, 'description': '该分层没有候选公式达…`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
                # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
                # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
                pending.append(
                    {
                        "category": "ADJUSTMENT_LAYER_FORMULA",
                        "layer_name": layer.get("layer_name"),
                        "blocking": True,
                        "description": (
                            "该分层没有候选公式达到99%覆盖率。"
                        ),
                    }
                )

        # 状态计算：把`self._as_int(factor_change_summary.get('factor_change_count'))`的结果保存到`factor_change_count`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        factor_change_count = self._as_int(
            factor_change_summary.get("factor_change_count")
        )
        # 状态计算：把`self._as_int(factor_change_summary.get('factor_change_action_nonzero_count'))`的结果保存到`action_count`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        action_count = self._as_int(
            factor_change_summary.get(
                "factor_change_action_nonzero_count"
            )
        )
        # 状态计算：把`self._as_int(factor_change_summary.get('factor_change_deduct_nonzero_count'))`的结果保存到`deduct_count`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        deduct_count = self._as_int(
            factor_change_summary.get(
                "factor_change_deduct_nonzero_count"
            )
        )

        # 显式调用：执行`conclusions.append({'topic': 'FACTOR_CHANGE_ASSOCIATION', 'factor_change_count': factor_change_count, 'action_nonzero_coverage': self._cove…`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
        # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
        # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
        conclusions.append(
            {
                "topic": "FACTOR_CHANGE_ASSOCIATION",
                "factor_change_count": factor_change_count,
                "action_nonzero_coverage": self._coverage(
                    action_count,
                    factor_change_count,
                ),
                "deduct_nonzero_coverage": self._coverage(
                    deduct_count,
                    factor_change_count,
                ),
                "confirmed": factor_change_count > 0,
            }
        )

        # 条件门禁：判断`factor_change_count == 0`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if factor_change_count == 0:
            # 显式调用：执行`pending.append({'category': 'FACTOR_CHANGE_ASSOCIATION', 'blocking': True, 'description': '没有取得复权因子变化记录。'})`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
            # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
            # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
            pending.append(
                {
                    "category": "FACTOR_CHANGE_ASSOCIATION",
                    "blocking": True,
                    "description": "没有取得复权因子变化记录。",
                }
            )

        # 状态计算：把`calendar_lag_days is not None and calendar_lag_days <= 7`的结果保存到`freshness_confirmed`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        freshness_confirmed = (
            calendar_lag_days is not None
            and calendar_lag_days <= 7
        )
        # 显式调用：执行`conclusions.append({'topic': 'DATA_FRESHNESS', 'calendar_lag_days': calendar_lag_days, 'confirmed': freshness_confirmed})`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
        # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
        # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
        conclusions.append(
            {
                "topic": "DATA_FRESHNESS",
                "calendar_lag_days": calendar_lag_days,
                "confirmed": freshness_confirmed,
            }
        )

        # 条件门禁：判断`not freshness_confirmed`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if not freshness_confirmed:
            # 显式调用：执行`pending.append({'category': 'DATA_FRESHNESS', 'blocking': True, 'description': '最新交易日期距运行日期超过7个日历日，需要检查更新链路。'})`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
            # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
            # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
            pending.append(
                {
                    "category": "DATA_FRESHNESS",
                    "blocking": True,
                    "description": (
                        "最新交易日期距运行日期超过7个日历日，"
                        "需要检查更新链路。"
                    ),
                }
            )

        # 结果返回：把`(conclusions, pending)`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return conclusions, pending

    # 函数collect：执行collect对应的业务处理。
    # - 输入：无外部业务参数；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型AdjustmentLayerReport；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    def collect(self) -> AdjustmentLayerReport:
        # 状态计算：把`self._query_one(f'\n select max(trade_date) as max_trade_date\n from {self._table_ref}\n ')`的结果保存到`latest`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        latest = self._query_one(
            f"""
            select max(trade_date) as max_trade_date
            from {self._table_ref}
            """
        )
        # 状态计算：把`latest.get('max_trade_date')`的结果保存到`latest_trade_date`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        latest_trade_date = latest.get("max_trade_date")
        # 状态计算：把`self._calendar_lag_days(latest_trade_date)`的结果保存到`lag_days`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        lag_days = self._calendar_lag_days(latest_trade_date)
        # 状态计算：把`self._collect_layer_statistics_chunked()`的结果保存到`(global_layers, formula_layers)`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        (
            global_layers,
            formula_layers,
        ) = self._collect_layer_statistics_chunked()
        # 状态计算：把`self._collect_factor_changes()`的结果保存到`(factor_change_summary, factor_change_samples)`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        (
            factor_change_summary,
            factor_change_samples,
        ) = self._collect_factor_changes()
        # 状态计算：把`self._evaluate(formula_layers=formula_layers, factor_change_summary=factor_change_summary, calendar…`的结果保存到`(conclusions, pending)`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        conclusions, pending = self._evaluate(
            formula_layers=formula_layers,
            factor_change_summary=factor_change_summary,
            calendar_lag_days=lag_days,
        )

        # 结果返回：把`AdjustmentLayerReport(database_uri=self.database_uri, table_name=self.table_name, generated_at=_utc_now(), latest_trade…`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return AdjustmentLayerReport(
            database_uri=self.database_uri,
            table_name=self.table_name,
            generated_at=_utc_now(),
            latest_trade_date=latest_trade_date,
            calendar_lag_days=lag_days,
            global_layers=global_layers,
            formula_layers=formula_layers,
            factor_change_summary=factor_change_summary,
            factor_change_samples=factor_change_samples,
            conclusions=conclusions,
            pending_confirmations=pending,
            overall_status=(
                QualityStatus.PENDING_CONFIRMATION
                if pending
                else QualityStatus.PASSED
            ),
            blocks_downstream=bool(pending),
        )


# 函数build_parser：执行build_parser对应的业务处理。
# - 输入：无外部业务参数；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型argparse.ArgumentParser；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
# - 为什么这样写：把对象构造、字段映射或标准化转换步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def build_parser() -> argparse.ArgumentParser:
    # 状态计算：把`argparse.ArgumentParser(description='DolphinDB日K复权字段分层只读核验。')`的结果保存到`parser`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    parser = argparse.ArgumentParser(
        description="DolphinDB日K复权字段分层只读核验。"
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
    # 显式调用：执行`parser.add_argument('--factor-chunk-size', type=int, default=100)`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
    # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
    # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
    parser.add_argument(
        "--factor-chunk-size",
        type=int,
        default=100,
    )
    # 显式调用：执行`parser.add_argument('--output', default='reports/task_007_adjustment_layers.json')`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
    # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
    # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
    parser.add_argument(
        "--output",
        default=(
            "reports/task_007_adjustment_layers.json"
        ),
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

        # 状态计算：把`DolphinDBAdjustmentLayerProfiler(adapter=adapter, database_uri=args.database_uri, table_name=args.t…`的结果保存到`report`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        report = DolphinDBAdjustmentLayerProfiler(
            adapter=adapter,
            database_uri=args.database_uri,
            table_name=args.table,
            factor_chunk_size=args.factor_chunk_size,
        ).collect()
    except DataContractError as exc:
        # 显式调用：执行`print(f'复权分层核验失败：{exc}')`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
        # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
        # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
        print(f"复权分层核验失败：{exc}")
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

    # 显式调用：执行`print('=== 日K复权字段分层核验完成 ===')`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
    # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
    # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
    print("=== 日K复权字段分层核验完成 ===")
    # 显式调用：执行`print(f'来源：{report.database_uri}/{report.table_name}')`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
    # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
    # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
    print(f"来源：{report.database_uri}/{report.table_name}")
    # 显式调用：执行`print(f'最新日期：{report.latest_trade_date}')`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
    # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
    # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
    print(f"最新日期：{report.latest_trade_date}")
    # 显式调用：执行`print(f'日历滞后天数：{report.calendar_lag_days}')`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
    # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
    # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
    print(f"日历滞后天数：{report.calendar_lag_days}")

    # 显式调用：执行`print(f"复权分层核验批次数：{report.global_layers.get('chunk_count')}")`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
    # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
    # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
    print(
        "复权分层核验批次数："
        f"{report.global_layers.get('chunk_count')}"
    )

    # 循环处理：逐项遍历`report.formula_layers`，把当前元素绑定到`layer`。
    # - 数据变化：每轮只处理一个来源记录、字段、文件或证据项，并显式累计到局部集合或输出对象。
    # - 为什么这样写：逐项处理便于保留行级血缘、隔离单项异常，并控制16GB单机上的峰值内存。
    for layer in report.formula_layers:
        # 显式调用：执行`print(f"{layer.get('layer_name')}：行数={layer.get('comparable_row_count')} 最佳公式={layer.get('best_candidate')} 覆盖率={layer.get('best_coverage')…`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
        # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
        # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
        print(
            f"{layer.get('layer_name')}："
            f"行数={layer.get('comparable_row_count')} "
            f"最佳公式={layer.get('best_candidate')} "
            f"覆盖率={layer.get('best_coverage')}"
        )

    # 显式调用：执行`print(f"复权因子变化记录数：{report.factor_change_summary.get('factor_change_count')}")`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
    # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
    # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
    print(
        "复权因子变化记录数："
        f"{report.factor_change_summary.get('factor_change_count')}"
    )
    # 显式调用：执行`print(f"复权因子变化核验批次数：{report.factor_change_summary.get('chunk_count')}")`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
    # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
    # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
    print(
        "复权因子变化核验批次数："
        f"{report.factor_change_summary.get('chunk_count')}"
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
