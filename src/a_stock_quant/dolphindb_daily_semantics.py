# 模块总览：验证日K字段的单位、方向、日期和跨字段业务关系。
# - 输入输出：输入为真实日K样本；输出为每项语义假设的证据、置信状态和待确认问题。
# - 数据与安全：经验关系必须与厂商文档确认分开，证据不足时保留来源值和警告。
# - 运行边界：导入模块和阅读注释不会触发数据库写入；只有显式调用对应函数并满足门禁时才执行I/O。
# - 为什么这样写：先声明职责、单位、时点和副作用边界，读者可以在阅读实现前建立正确的金融与工程语境。
"""DolphinDB日K字段语义只读核验。

本模块核验：
1. turnover_rate、volume、float_shares 的候选单位关系；
2. amount 与 volume、价格字段的候选尺度关系；
3. adj_price 与 close、adj_factor 的候选公式；
4. price_change 与 pct_change 的820条例外记录；
5. 数据最新日期的日历滞后。

所有查询均为只读聚合或有限样例查询。
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


# 函数_json_safe：执行_json_safe对应的业务处理。
# - 输入：value:Any；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型Any；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
# - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def _json_safe(value: Any) -> Any:
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


# 类DailyKSemanticReport：日K字段语义核验报告。
# - 结构：继承或实现object；类体约包含14个字段或常量、1个方法。
# - 数据变化：类定义阶段不执行隐式I/O，实例只在构造或显式方法调用时改变受控状态。
# - 实操：调用方通过该类型集中传递配置、记录、服务或结果，避免跨模块使用无约束字典。
# - 为什么这样写：强类型边界能集中维护单位、时点、主键和安全不变量，并降低供应商耦合。
@dataclass(slots=True)
class DailyKSemanticReport:
    """日K字段语义核验报告。"""

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
    # 状态计算：把`无`的结果保存到`turnover_unit_analysis`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    turnover_unit_analysis: dict[str, Any]
    # 状态计算：把`无`的结果保存到`amount_volume_analysis`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    amount_volume_analysis: dict[str, Any]
    # 状态计算：把`无`的结果保存到`adjustment_relation_analysis`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    adjustment_relation_analysis: dict[str, Any]
    # 状态计算：把`无`的结果保存到`price_change_anomaly_summary`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    price_change_anomaly_summary: dict[str, Any]
    # 状态计算：把`无`的结果保存到`price_change_anomaly_samples`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    price_change_anomaly_samples: list[dict[str, Any]]
    # 状态计算：把`field(default_factory=list)`的结果保存到`conclusions`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    conclusions: list[dict[str, Any]] = field(default_factory=list)
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


# 类DolphinDBDailyKSemanticProfiler：日K字段候选语义关系的只读核验器。
# - 结构：继承或实现object；类体约包含0个字段或常量、16个方法。
# - 数据变化：类定义阶段不执行隐式I/O，实例只在构造或显式方法调用时改变受控状态。
# - 实操：调用方通过该类型集中传递配置、记录、服务或结果，避免跨模块使用无约束字典。
# - 为什么这样写：强类型边界能集中维护单位、时点、主键和安全不变量，并降低供应商耦合。
class DolphinDBDailyKSemanticProfiler:
    """日K字段候选语义关系的只读核验器。"""

    # 函数__init__：执行__init__对应的业务处理。
    # - 输入：adapter:DolphinDBDataSourceAdapter、database_uri:str、table_name:str、anomaly_chunk_size:int；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型None；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    def __init__(
        self,
        adapter: DolphinDBDataSourceAdapter,
        database_uri: str = "dfs://A_STOCK_DAILY_K_DB",
        table_name: str = "stock_daily_k",
        anomaly_chunk_size: int = 100,
    ) -> None:
        # 显式调用：执行`adapter._validate_database_uri(database_uri)`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
        # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
        # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
        adapter._validate_database_uri(database_uri)
        # 显式调用：执行`adapter._validate_table_name(table_name)`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
        # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
        # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
        adapter._validate_table_name(table_name)

        # 条件门禁：判断`not isinstance(anomaly_chunk_size, int) or not 1 <= anomaly_chunk_size <= 500`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if (
            not isinstance(anomaly_chunk_size, int)
            or not 1 <= anomaly_chunk_size <= 500
        ):
            # 错误阻断：抛出`DataContractError('anomaly_chunk_size 必须是 1 到 500 之间的整数。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
            raise DataContractError(
                "anomaly_chunk_size 必须是 1 到 500 之间的整数。"
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
        # 状态计算：把`anomaly_chunk_size`的结果保存到`self.anomaly_chunk_size`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        self.anomaly_chunk_size = anomaly_chunk_size

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
        # 状态计算：把`DolphinDBDailyKSemanticProfiler._as_int(comparable)`的结果保存到`comparable_count`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        comparable_count = DolphinDBDailyKSemanticProfiler._as_int(
            comparable
        )

        # 条件门禁：判断`comparable_count <= 0`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if comparable_count <= 0:
            # 结果返回：把`None`交给调用方并结束当前函数。
            # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
            # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
            return None

        # 结果返回：把`DolphinDBDailyKSemanticProfiler._as_int(matched) / comparable_count`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return (
            DolphinDBDailyKSemanticProfiler._as_int(matched)
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
        return (datetime.now(timezone.utc).date() - latest_date).days

    # 函数_quote_stock_code：生成安全的DolphinDB字符串字面量。
    # - 输入：stock_code:str；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型str；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    @staticmethod
    def _quote_stock_code(stock_code: str) -> str:
        """生成安全的DolphinDB字符串字面量。"""

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

    # 函数_chunked：把股票代码拆成固定大小的小批次。
    # - 输入：values:list[str]、size:int；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型list[list[str]]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    @staticmethod
    def _chunked(
        values: list[str],
        size: int,
    ) -> list[list[str]]:
        """把股票代码拆成固定大小的小批次。"""

        # 结果返回：把`[values[index:index + size] for index in range(0, len(values), size)]`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return [
            values[index:index + size]
            for index in range(0, len(values), size)
        ]

    # 函数_load_stock_codes：只读取股票代码列表，不加载日K全表。
    # - 输入：无外部业务参数；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型list[str]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把只读查询或来源发现步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    def _load_stock_codes(self) -> list[str]:
        """只读取股票代码列表，不加载日K全表。"""

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

        # 状态计算：把`[]`的结果保存到`stock_codes`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        stock_codes: list[str] = []

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
            # 显式调用：执行`stock_codes.append(code)`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
            # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
            # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
            stock_codes.append(code)

        # 结果返回：把`stock_codes`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return stock_codes

    # 函数_empty_anomaly_summary：生成分批异常统计的初始累计值。
    # - 输入：无外部业务参数；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型dict[str, Any]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    @staticmethod
    def _empty_anomaly_summary() -> dict[str, Any]:
        """生成分批异常统计的初始累计值。"""

        # 结果返回：把`{'stock_code_count': 0, 'chunk_count': 0, 'total_context_row_count': 0, 'comparable_row_count': 0, 'anomaly_row_count':…`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return {
            "stock_code_count": 0,
            "chunk_count": 0,
            "total_context_row_count": 0,
            "comparable_row_count": 0,
            "anomaly_row_count": 0,
            "anomaly_adj_factor_changed_count": 0,
            "anomaly_dividend_present_count": 0,
            "anomaly_dividend_nonzero_count": 0,
            "anomaly_bonus_share_present_count": 0,
            "anomaly_bonus_share_nonzero_count": 0,
            "anomaly_convert_share_present_count": 0,
            "anomaly_convert_share_nonzero_count": 0,
            "anomaly_allot_share_present_count": 0,
            "anomaly_allot_share_nonzero_count": 0,
            "anomaly_allot_price_present_count": 0,
            "anomaly_allot_price_nonzero_count": 0,
            "pct_change_negated_formula_exception_count": 0,
        }

    # 函数_merge_anomaly_summary：把一个股票批次的统计合并到总计。
    # - 输入：total:dict[str, Any]、part:dict[str, Any]；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型None；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    def _merge_anomaly_summary(
        self,
        total: dict[str, Any],
        part: dict[str, Any],
    ) -> None:
        """把一个股票批次的统计合并到总计。"""

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

    # 函数_collect_anomalies_chunked：按股票代码分批核验异常，避免全表宽查询导致内存溢出。
    # - 输入：无外部业务参数；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型tuple[dict[str, Any], list[dict[str, Any]]]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    def _collect_anomalies_chunked(
        self,
    ) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        """按股票代码分批核验异常，避免全表宽查询导致内存溢出。"""

        # 状态计算：把`self._load_stock_codes()`的结果保存到`stock_codes`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        stock_codes = self._load_stock_codes()
        # 状态计算：把`self._chunked(stock_codes, self.anomaly_chunk_size)`的结果保存到`chunks`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        chunks = self._chunked(
            stock_codes,
            self.anomaly_chunk_size,
        )
        # 状态计算：把`self._empty_anomaly_summary()`的结果保存到`total`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        total = self._empty_anomaly_summary()
        # 状态计算：把`len(stock_codes)`的结果保存到`total['stock_code_count']`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        total["stock_code_count"] = len(stock_codes)
        # 状态计算：把`len(chunks)`的结果保存到`total['chunk_count']`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        total["chunk_count"] = len(chunks)

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

            # 状态计算：把`f'\n select\n stock_code,\n trade_date,\n close,\n price_change,\n pct_change,\n adj_factor,\n divi…`的结果保存到`context_query`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            context_query = f"""
                select
                    stock_code,
                    trade_date,
                    close,
                    price_change,
                    pct_change,
                    adj_factor,
                    dividend,
                    bonus_share,
                    convert_share,
                    allot_share,
                    allot_price,
                    move(close, 1) as prev_close,
                    move(adj_factor, 1) as prev_adj_factor
                from {self._table_ref}
                where stock_code in [{literals}]
                context by stock_code
                csort trade_date
            """

            # 状态计算：把`self._query_one(f'\n select\n count(*) as total_context_row_count,\n count(*) as comparable_row_cou…`的结果保存到`part`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            part = self._query_one(
                f"""
                select
                    count(*) as total_context_row_count,
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
                    ) as anomaly_row_count,
                    sum(
                        iif(
                            abs(
                                price_change
                                - (close - prev_close)
                            ) > 0.0001
                            and not isNull(prev_adj_factor)
                            and not isNull(adj_factor)
                            and abs(
                                adj_factor - prev_adj_factor
                            ) > 0.000001,
                            1,
                            0
                        )
                    ) as anomaly_adj_factor_changed_count,
                    sum(
                        iif(
                            abs(
                                price_change
                                - (close - prev_close)
                            ) > 0.0001
                            and not isNull(dividend),
                            1,
                            0
                        )
                    ) as anomaly_dividend_present_count,
                    sum(
                        iif(
                            abs(
                                price_change
                                - (close - prev_close)
                            ) > 0.0001
                            and not isNull(dividend)
                            and abs(dividend) > 0.000001,
                            1,
                            0
                        )
                    ) as anomaly_dividend_nonzero_count,
                    sum(
                        iif(
                            abs(
                                price_change
                                - (close - prev_close)
                            ) > 0.0001
                            and not isNull(bonus_share),
                            1,
                            0
                        )
                    ) as anomaly_bonus_share_present_count,
                    sum(
                        iif(
                            abs(
                                price_change
                                - (close - prev_close)
                            ) > 0.0001
                            and not isNull(bonus_share)
                            and abs(bonus_share) > 0.000001,
                            1,
                            0
                        )
                    ) as anomaly_bonus_share_nonzero_count,
                    sum(
                        iif(
                            abs(
                                price_change
                                - (close - prev_close)
                            ) > 0.0001
                            and not isNull(convert_share),
                            1,
                            0
                        )
                    ) as anomaly_convert_share_present_count,
                    sum(
                        iif(
                            abs(
                                price_change
                                - (close - prev_close)
                            ) > 0.0001
                            and not isNull(convert_share)
                            and abs(convert_share) > 0.000001,
                            1,
                            0
                        )
                    ) as anomaly_convert_share_nonzero_count,
                    sum(
                        iif(
                            abs(
                                price_change
                                - (close - prev_close)
                            ) > 0.0001
                            and not isNull(allot_share),
                            1,
                            0
                        )
                    ) as anomaly_allot_share_present_count,
                    sum(
                        iif(
                            abs(
                                price_change
                                - (close - prev_close)
                            ) > 0.0001
                            and not isNull(allot_share)
                            and abs(allot_share) > 0.000001,
                            1,
                            0
                        )
                    ) as anomaly_allot_share_nonzero_count,
                    sum(
                        iif(
                            abs(
                                price_change
                                - (close - prev_close)
                            ) > 0.0001
                            and not isNull(allot_price),
                            1,
                            0
                        )
                    ) as anomaly_allot_price_present_count,
                    sum(
                        iif(
                            abs(
                                price_change
                                - (close - prev_close)
                            ) > 0.0001
                            and not isNull(allot_price)
                            and abs(allot_price) > 0.000001,
                            1,
                            0
                        )
                    ) as anomaly_allot_price_nonzero_count,
                    sum(
                        iif(
                            abs(
                                price_change
                                - (close - prev_close)
                            ) > 0.0001
                            and prev_close != 0
                            and not isNull(pct_change)
                            and abs(
                                pct_change
                                - round(
                                    (prev_close - close)
                                    / prev_close
                                    * 100,
                                    2
                                )
                            ) > 0.000001,
                            1,
                            0
                        )
                    ) as pct_change_negated_formula_exception_count
                from ({context_query})
                where
                    not isNull(prev_close)
                    and not isNull(close)
                    and not isNull(price_change)
                """
            )
            # 显式调用：执行`self._merge_anomaly_summary(total, part)`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
            # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
            # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
            self._merge_anomaly_summary(total, part)

            # 状态计算：把`self._query_rows(f'\n select top 5\n stock_code,\n trade_date,\n prev_close,\n close,\n price_chang…`的结果保存到`part_samples`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            part_samples = self._query_rows(
                f"""
                select top 5
                    stock_code,
                    trade_date,
                    prev_close,
                    close,
                    price_change,
                    close - prev_close
                        as expected_price_change,
                    abs(
                        price_change
                        - (close - prev_close)
                    ) as price_change_error,
                    pct_change,
                    round(
                        (prev_close - close)
                        / prev_close
                        * 100,
                        2
                    ) as expected_negated_pct_change,
                    prev_adj_factor,
                    adj_factor,
                    dividend,
                    bonus_share,
                    convert_share,
                    allot_share,
                    allot_price
                from ({context_query})
                where
                    not isNull(prev_close)
                    and not isNull(close)
                    and not isNull(price_change)
                    and abs(
                        price_change
                        - (close - prev_close)
                    ) > 0.0001
                order by
                    price_change_error desc,
                    trade_date desc
                """
            )
            # 显式调用：执行`samples.extend(part_samples)`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
            # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
            # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
            samples.extend(part_samples)

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
            # 状态计算：把`unique_samples.get(key)`的结果保存到`existing`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            existing = unique_samples.get(key)
            # 状态计算：把`float(row.get('price_change_error') or 0)`的结果保存到`current_error`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            current_error = float(
                row.get("price_change_error") or 0
            )
            # 状态计算：把`float(existing.get('price_change_error') or 0) if existing is not None else -1.0`的结果保存到`existing_error`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            existing_error = float(
                existing.get("price_change_error") or 0
            ) if existing is not None else -1.0

            # 条件门禁：判断`existing is None or current_error > existing_error`，条件成立时进入对应的数据、安全或异常处理分支。
            # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
            # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
            if existing is None or current_error > existing_error:
                # 状态计算：把`row`的结果保存到`unique_samples[key]`，供当前逻辑后续校验、转换、累计或返回。
                # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
                # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
                unique_samples[key] = row

        # 状态计算：把`list(unique_samples.values())`的结果保存到`ordered_samples`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        ordered_samples = list(unique_samples.values())
        # 显式调用：执行`ordered_samples.sort(key=lambda row: (float(row.get('price_change_error') or 0), str(row.get('trade_date') or '')), reverse=True)`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
        # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
        # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
        ordered_samples.sort(
            key=lambda row: (
                float(row.get("price_change_error") or 0),
                str(row.get("trade_date") or ""),
            ),
            reverse=True,
        )

        # 结果返回：把`(total, ordered_samples[:50])`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return total, ordered_samples[:50]

    # 函数collect：执行字段语义候选关系核验。
    # - 输入：无外部业务参数；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型DailyKSemanticReport；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    def collect(self) -> DailyKSemanticReport:
        """执行字段语义候选关系核验。"""

        # 状态计算：把`self._query_one(f'\n select\n max(trade_date) as max_trade_date\n from {self._table_ref}\n ')`的结果保存到`latest`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        latest = self._query_one(
            f"""
            select
                max(trade_date) as max_trade_date
            from {self._table_ref}
            """
        )
        # 状态计算：把`latest.get('max_trade_date')`的结果保存到`latest_trade_date`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        latest_trade_date = latest.get("max_trade_date")

        # 状态计算：把`self._query_one(f'\n select\n count(*) as comparable_row_count,\n sum(\n iif(\n abs(\n turnover_rat…`的结果保存到`turnover`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        turnover = self._query_one(
            f"""
            select
                count(*) as comparable_row_count,
                sum(
                    iif(
                        abs(
                            turnover_rate
                            - round(
                                volume
                                / float_shares
                                / 100.0,
                                3
                            )
                        ) <= 0.000001,
                        1,
                        0
                    )
                ) as volume_share_float_10k_percent_match_count,
                sum(
                    iif(
                        abs(
                            turnover_rate
                            - round(
                                volume
                                / float_shares,
                                3
                            )
                        ) <= 0.000001,
                        1,
                        0
                    )
                ) as volume_lot_float_10k_percent_match_count,
                sum(
                    iif(
                        abs(
                            turnover_rate
                            - round(
                                volume
                                / float_shares
                                * 100.0,
                                3
                            )
                        ) <= 0.000001,
                        1,
                        0
                    )
                ) as same_unit_percent_match_count
            from {self._table_ref}
            where
                not isNull(turnover_rate)
                and not isNull(volume)
                and not isNull(float_shares)
                and float_shares > 0
            """
        )
        # 状态计算：把`turnover.get('comparable_row_count')`的结果保存到`turnover_comparable`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        turnover_comparable = turnover.get("comparable_row_count")
        # 状态计算：把`{'volume_share_float_10k_turnover_percent': self._coverage(turnover.get('volume_share_float_10k_per…`的结果保存到`turnover['candidate_coverages']`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        turnover["candidate_coverages"] = {
            "volume_share_float_10k_turnover_percent": self._coverage(
                turnover.get(
                    "volume_share_float_10k_percent_match_count"
                ),
                turnover_comparable,
            ),
            "volume_lot_float_10k_turnover_percent": self._coverage(
                turnover.get(
                    "volume_lot_float_10k_percent_match_count"
                ),
                turnover_comparable,
            ),
            "same_unit_turnover_percent": self._coverage(
                turnover.get("same_unit_percent_match_count"),
                turnover_comparable,
            ),
        }

        # 状态计算：把`self._query_one(f'\n select\n count(*) as comparable_row_count,\n sum(\n iif(\n abs(\n amount / vol…`的结果保存到`amount_volume`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        amount_volume = self._query_one(
            f"""
            select
                count(*) as comparable_row_count,
                sum(
                    iif(
                        abs(
                            amount / volume / close - 1
                        ) <= 0.30,
                        1,
                        0
                    )
                ) as scale_1_1_close_match_count,
                sum(
                    iif(
                        abs(
                            amount
                            / (volume * 100.0)
                            / close
                            - 1
                        ) <= 0.30,
                        1,
                        0
                    )
                ) as scale_1_100_close_match_count,
                sum(
                    iif(
                        abs(
                            amount
                            * 100.0
                            / volume
                            / close
                            - 1
                        ) <= 0.30,
                        1,
                        0
                    )
                ) as scale_100_1_close_match_count,
                sum(
                    iif(
                        abs(
                            amount
                            * 10000.0
                            / volume
                            / close
                            - 1
                        ) <= 0.30,
                        1,
                        0
                    )
                ) as scale_10000_1_close_match_count,
                sum(
                    iif(
                        abs(
                            amount
                            * 100.0
                            / volume
                            / adj_price
                            - 1
                        ) <= 0.30,
                        1,
                        0
                    )
                ) as scale_100_1_adj_price_match_count
            from {self._table_ref}
            where
                not isNull(amount)
                and not isNull(volume)
                and not isNull(close)
                and not isNull(adj_price)
                and amount > 0
                and volume > 0
                and close > 0
                and adj_price > 0
            """
        )
        # 状态计算：把`amount_volume.get('comparable_row_count')`的结果保存到`amount_comparable`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        amount_comparable = amount_volume.get("comparable_row_count")
        # 状态计算：把`{'amount_scale_1_volume_scale_1_close': self._coverage(amount_volume.get('scale_1_1_close_match_cou…`的结果保存到`amount_volume['candidate_coverages']`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        amount_volume["candidate_coverages"] = {
            "amount_scale_1_volume_scale_1_close": self._coverage(
                amount_volume.get("scale_1_1_close_match_count"),
                amount_comparable,
            ),
            "amount_scale_1_volume_scale_100_close": self._coverage(
                amount_volume.get("scale_1_100_close_match_count"),
                amount_comparable,
            ),
            "amount_scale_100_volume_scale_1_close": self._coverage(
                amount_volume.get("scale_100_1_close_match_count"),
                amount_comparable,
            ),
            "amount_scale_10000_volume_scale_1_close": self._coverage(
                amount_volume.get("scale_10000_1_close_match_count"),
                amount_comparable,
            ),
            "amount_scale_100_volume_scale_1_adj_price": self._coverage(
                amount_volume.get(
                    "scale_100_1_adj_price_match_count"
                ),
                amount_comparable,
            ),
        }

        # 状态计算：把`self._query_one(f'\n select\n count(*) as comparable_row_count,\n sum(\n iif(\n abs(\n adj_price\n …`的结果保存到`adjustment`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        adjustment = self._query_one(
            f"""
            select
                count(*) as comparable_row_count,
                sum(
                    iif(
                        abs(
                            adj_price
                            / (close * adj_factor)
                            - 1
                        ) <= 0.000001,
                        1,
                        0
                    )
                ) as close_multiply_factor_match_count,
                sum(
                    iif(
                        abs(
                            adj_price
                            / (close / adj_factor)
                            - 1
                        ) <= 0.000001,
                        1,
                        0
                    )
                ) as close_divide_factor_match_count,
                sum(
                    iif(
                        abs(
                            adj_price
                            / (
                                close * adj_factor
                                - deduct_value
                            )
                            - 1
                        ) <= 0.000001,
                        1,
                        0
                    )
                ) as close_multiply_factor_minus_deduct_match_count,
                sum(
                    iif(
                        abs(
                            adj_price
                            / (
                                (close - deduct_value)
                                * adj_factor
                            )
                            - 1
                        ) <= 0.000001,
                        1,
                        0
                    )
                ) as close_minus_deduct_multiply_factor_match_count,
                sum(
                    iif(
                        abs(
                            adj_price
                            / (
                                close * adj_factor
                                + deduct_value
                            )
                            - 1
                        ) <= 0.000001,
                        1,
                        0
                    )
                ) as close_multiply_factor_plus_deduct_match_count,
                sum(
                    iif(
                        abs(
                            adj_price
                            / (
                                (close + deduct_value)
                                * adj_factor
                            )
                            - 1
                        ) <= 0.000001,
                        1,
                        0
                    )
                ) as close_plus_deduct_multiply_factor_match_count,
                sum(
                    iif(
                        not isNull(deduct_value)
                        and abs(deduct_value) > 0.000001,
                        1,
                        0
                    )
                ) as deduct_value_nonzero_count
            from {self._table_ref}
            where
                not isNull(close)
                and not isNull(adj_factor)
                and not isNull(adj_price)
                and not isNull(deduct_value)
                and close != 0
                and adj_factor != 0
                and adj_price != 0
                and close * adj_factor != deduct_value
                and close != deduct_value
            """
        )
        # 状态计算：把`adjustment.get('comparable_row_count')`的结果保存到`adjustment_comparable`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        adjustment_comparable = adjustment.get("comparable_row_count")
        # 状态计算：把`{'adj_price_equals_close_multiply_adj_factor': self._coverage(adjustment.get('close_multiply_factor…`的结果保存到`adjustment['candidate_coverages']`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        adjustment["candidate_coverages"] = {
            "adj_price_equals_close_multiply_adj_factor": self._coverage(
                adjustment.get(
                    "close_multiply_factor_match_count"
                ),
                adjustment_comparable,
            ),
            "adj_price_equals_close_divide_adj_factor": self._coverage(
                adjustment.get(
                    "close_divide_factor_match_count"
                ),
                adjustment_comparable,
            ),
            "adj_price_equals_close_multiply_factor_minus_deduct": self._coverage(
                adjustment.get(
                    "close_multiply_factor_minus_deduct_match_count"
                ),
                adjustment_comparable,
            ),
            "adj_price_equals_close_minus_deduct_multiply_factor": self._coverage(
                adjustment.get(
                    "close_minus_deduct_multiply_factor_match_count"
                ),
                adjustment_comparable,
            ),
            "adj_price_equals_close_multiply_factor_plus_deduct": self._coverage(
                adjustment.get(
                    "close_multiply_factor_plus_deduct_match_count"
                ),
                adjustment_comparable,
            ),
            "adj_price_equals_close_plus_deduct_multiply_factor": self._coverage(
                adjustment.get(
                    "close_plus_deduct_multiply_factor_match_count"
                ),
                adjustment_comparable,
            ),
        }

        # 状态计算：把`self._collect_anomalies_chunked()`的结果保存到`(anomaly_summary, anomaly_samples)`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        (
            anomaly_summary,
            anomaly_samples,
        ) = self._collect_anomalies_chunked()

        # 状态计算：把`self._evaluate(turnover=turnover, amount_volume=amount_volume, adjustment=adjustment, anomaly_summa…`的结果保存到`(conclusions, pending)`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        conclusions, pending = self._evaluate(
            turnover=turnover,
            amount_volume=amount_volume,
            adjustment=adjustment,
            anomaly_summary=anomaly_summary,
        )

        # 结果返回：把`DailyKSemanticReport(database_uri=self.database_uri, table_name=self.table_name, generated_at=_utc_now(), latest_trade_…`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return DailyKSemanticReport(
            database_uri=self.database_uri,
            table_name=self.table_name,
            generated_at=_utc_now(),
            latest_trade_date=latest_trade_date,
            calendar_lag_days=self._calendar_lag_days(
                latest_trade_date
            ),
            turnover_unit_analysis=turnover,
            amount_volume_analysis=amount_volume,
            adjustment_relation_analysis=adjustment,
            price_change_anomaly_summary=anomaly_summary,
            price_change_anomaly_samples=anomaly_samples,
            conclusions=conclusions,
            pending_confirmations=pending,
            overall_status=(
                QualityStatus.PENDING_CONFIRMATION
                if pending
                else QualityStatus.PASSED
            ),
            blocks_downstream=bool(pending),
        )

    # 函数_best_candidate：执行_best_candidate对应的业务处理。
    # - 输入：coverages:dict[str, Any]；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型tuple[str | None, float | None]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    @staticmethod
    def _best_candidate(
        coverages: dict[str, Any],
    ) -> tuple[str | None, float | None]:
        # 状态计算：把`{key: value for key, value in coverages.items() if isinstance(value, (int, float)) and (not (isinst…`的结果保存到`valid`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        valid = {
            key: value
            for key, value in coverages.items()
            if isinstance(value, (int, float))
            and not (
                isinstance(value, float)
                and math.isnan(value)
            )
        }

        # 条件门禁：判断`not valid`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if not valid:
            # 结果返回：把`(None, None)`交给调用方并结束当前函数。
            # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
            # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
            return None, None

        # 状态计算：把`max(valid, key=valid.get)`的结果保存到`name`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        name = max(valid, key=valid.get)
        # 结果返回：把`(name, float(valid[name]))`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return name, float(valid[name])

    # 函数_evaluate：执行_evaluate对应的业务处理。
    # - 输入：turnover:dict[str, Any]、amount_volume:dict[str, Any]、adjustment:dict[str, Any]、anomaly_summary:dict[str, Any]；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型tuple[list[dict[str, Any]], list[dict[str, Any]]]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    def _evaluate(
        self,
        *,
        turnover: dict[str, Any],
        amount_volume: dict[str, Any],
        adjustment: dict[str, Any],
        anomaly_summary: dict[str, Any],
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

        # 状态计算：把`self._best_candidate(turnover.get('candidate_coverages', {}))`的结果保存到`(turnover_name, turnover_coverage)`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        turnover_name, turnover_coverage = self._best_candidate(
            turnover.get("candidate_coverages", {})
        )
        # 状态计算：把`turnover_coverage is not None and turnover_coverage >= 0.99`的结果保存到`turnover_confirmed`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        turnover_confirmed = (
            turnover_coverage is not None
            and turnover_coverage >= 0.99
        )
        # 显式调用：执行`conclusions.append({'topic': 'TURNOVER_AND_SHARE_UNIT', 'candidate': turnover_name, 'coverage': turnover_coverage, 'confirmed': turnover_co…`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
        # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
        # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
        conclusions.append(
            {
                "topic": "TURNOVER_AND_SHARE_UNIT",
                "candidate": turnover_name,
                "coverage": turnover_coverage,
                "confirmed": turnover_confirmed,
            }
        )

        # 条件门禁：判断`not turnover_confirmed`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if not turnover_confirmed:
            # 显式调用：执行`pending.append({'category': 'TURNOVER_AND_SHARE_UNIT', 'blocking': True, 'description': '换手率、成交量和流通股本的候选关系未达到99%覆盖率。'})`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
            # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
            # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
            pending.append(
                {
                    "category": "TURNOVER_AND_SHARE_UNIT",
                    "blocking": True,
                    "description": (
                        "换手率、成交量和流通股本的候选关系"
                        "未达到99%覆盖率。"
                    ),
                }
            )

        # 状态计算：把`self._best_candidate(amount_volume.get('candidate_coverages', {}))`的结果保存到`(amount_name, amount_coverage)`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        amount_name, amount_coverage = self._best_candidate(
            amount_volume.get("candidate_coverages", {})
        )
        # 状态计算：把`amount_coverage is not None and amount_coverage >= 0.95`的结果保存到`amount_confirmed`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        amount_confirmed = (
            amount_coverage is not None
            and amount_coverage >= 0.95
        )
        # 显式调用：执行`conclusions.append({'topic': 'AMOUNT_VOLUME_SCALE', 'candidate': amount_name, 'coverage': amount_coverage, 'confirmed': amount_confirmed})`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
        # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
        # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
        conclusions.append(
            {
                "topic": "AMOUNT_VOLUME_SCALE",
                "candidate": amount_name,
                "coverage": amount_coverage,
                "confirmed": amount_confirmed,
            }
        )

        # 条件门禁：判断`not amount_confirmed`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if not amount_confirmed:
            # 显式调用：执行`pending.append({'category': 'AMOUNT_VOLUME_SCALE', 'blocking': True, 'description': '成交额、成交量和价格的候选尺度关系未达到95%覆盖率。'})`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
            # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
            # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
            pending.append(
                {
                    "category": "AMOUNT_VOLUME_SCALE",
                    "blocking": True,
                    "description": (
                        "成交额、成交量和价格的候选尺度关系"
                        "未达到95%覆盖率。"
                    ),
                }
            )

        # 状态计算：把`self._best_candidate(adjustment.get('candidate_coverages', {}))`的结果保存到`(adjustment_name, adjustment_coverage)`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        adjustment_name, adjustment_coverage = self._best_candidate(
            adjustment.get("candidate_coverages", {})
        )
        # 状态计算：把`adjustment_coverage is not None and adjustment_coverage >= 0.999`的结果保存到`adjustment_confirmed`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        adjustment_confirmed = (
            adjustment_coverage is not None
            and adjustment_coverage >= 0.999
        )
        # 显式调用：执行`conclusions.append({'topic': 'ADJUSTMENT_FORMULA', 'candidate': adjustment_name, 'coverage': adjustment_coverage, 'confirmed': adjustment_c…`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
        # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
        # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
        conclusions.append(
            {
                "topic": "ADJUSTMENT_FORMULA",
                "candidate": adjustment_name,
                "coverage": adjustment_coverage,
                "confirmed": adjustment_confirmed,
            }
        )

        # 条件门禁：判断`not adjustment_confirmed`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if not adjustment_confirmed:
            # 显式调用：执行`pending.append({'category': 'ADJUSTMENT_FORMULA', 'blocking': True, 'description': 'adj_price与close、adj_factor的候选公式未达到99.9%覆盖率。'})`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
            # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
            # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
            pending.append(
                {
                    "category": "ADJUSTMENT_FORMULA",
                    "blocking": True,
                    "description": (
                        "adj_price与close、adj_factor的候选公式"
                        "未达到99.9%覆盖率。"
                    ),
                }
            )

        # 状态计算：把`self._as_int(anomaly_summary.get('anomaly_row_count'))`的结果保存到`anomaly_count`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        anomaly_count = self._as_int(
            anomaly_summary.get("anomaly_row_count")
        )
        # 状态计算：把`self._as_int(anomaly_summary.get('pct_change_negated_formula_exception_count'))`的结果保存到`pct_exception_count`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        pct_exception_count = self._as_int(
            anomaly_summary.get(
                "pct_change_negated_formula_exception_count"
            )
        )
        # 显式调用：执行`conclusions.append({'topic': 'PRICE_CHANGE_EXCEPTION', 'anomaly_row_count': anomaly_count, 'pct_change_exception_count': pct_exception_coun…`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
        # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
        # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
        conclusions.append(
            {
                "topic": "PRICE_CHANGE_EXCEPTION",
                "anomaly_row_count": anomaly_count,
                "pct_change_exception_count": pct_exception_count,
                "confirmed": anomaly_count == pct_exception_count,
            }
        )

        # 条件门禁：判断`anomaly_count > 0`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if anomaly_count > 0:
            # 显式调用：执行`pending.append({'category': 'PRICE_CHANGE_EXCEPTION', 'blocking': True, 'description': f'仍有{anomaly_count}条price_change例外记录需要分类核验。'})`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
            # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
            # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
            pending.append(
                {
                    "category": "PRICE_CHANGE_EXCEPTION",
                    "blocking": True,
                    "description": (
                        f"仍有{anomaly_count}条price_change例外记录"
                        "需要分类核验。"
                    ),
                }
            )

        # 结果返回：把`(conclusions, pending)`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return conclusions, pending


# 函数build_parser：执行build_parser对应的业务处理。
# - 输入：无外部业务参数；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型argparse.ArgumentParser；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
# - 为什么这样写：把对象构造、字段映射或标准化转换步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def build_parser() -> argparse.ArgumentParser:
    # 状态计算：把`argparse.ArgumentParser(description='DolphinDB日K字段语义只读核验。')`的结果保存到`parser`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    parser = argparse.ArgumentParser(
        description="DolphinDB日K字段语义只读核验。"
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
    # 显式调用：执行`parser.add_argument('--anomaly-chunk-size', type=int, default=100, help='异常核验每批股票数量，默认100，范围1到500。')`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
    # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
    # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
    parser.add_argument(
        "--anomaly-chunk-size",
        type=int,
        default=100,
        help="异常核验每批股票数量，默认100，范围1到500。",
    )
    # 显式调用：执行`parser.add_argument('--output', default='reports/task_006_daily_k_semantics.json')`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
    # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
    # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
    parser.add_argument(
        "--output",
        default="reports/task_006_daily_k_semantics.json",
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

        # 状态计算：把`DolphinDBDailyKSemanticProfiler(adapter=adapter, database_uri=args.database_uri, table_name=args.ta…`的结果保存到`report`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        report = DolphinDBDailyKSemanticProfiler(
            adapter=adapter,
            database_uri=args.database_uri,
            table_name=args.table,
            anomaly_chunk_size=args.anomaly_chunk_size,
        ).collect()
    except DataContractError as exc:
        # 显式调用：执行`print(f'语义核验失败：{exc}')`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
        # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
        # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
        print(f"语义核验失败：{exc}")
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

    # 显式调用：执行`print('=== 日K字段语义只读核验完成 ===')`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
    # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
    # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
    print("=== 日K字段语义只读核验完成 ===")
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

    # 循环处理：逐项遍历`report.conclusions`，把当前元素绑定到`conclusion`。
    # - 数据变化：每轮只处理一个来源记录、字段、文件或证据项，并显式累计到局部集合或输出对象。
    # - 为什么这样写：逐项处理便于保留行级血缘、隔离单项异常，并控制16GB单机上的峰值内存。
    for conclusion in report.conclusions:
        # 显式调用：执行`print(f"{conclusion.get('topic')}：{conclusion.get('candidate', '')} 覆盖率={conclusion.get('coverage', '')} 确认={conclusion.get('confirmed')}")`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
        # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
        # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
        print(
            f"{conclusion.get('topic')}："
            f"{conclusion.get('candidate', '')} "
            f"覆盖率={conclusion.get('coverage', '')} "
            f"确认={conclusion.get('confirmed')}"
        )

    # 显式调用：执行`print(f"price_change例外数：{report.price_change_anomaly_summary.get('anomaly_row_count')}")`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
    # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
    # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
    print(
        "price_change例外数："
        f"{report.price_change_anomaly_summary.get('anomaly_row_count')}"
    )
    # 显式调用：执行`print(f"异常核验批次数：{report.price_change_anomaly_summary.get('chunk_count')}")`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
    # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
    # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
    print(
        "异常核验批次数："
        f"{report.price_change_anomaly_summary.get('chunk_count')}"
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
