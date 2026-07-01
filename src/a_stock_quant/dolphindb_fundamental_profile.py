# 模块总览：对基本面快照表进行真实只读画像和初步字段语义评估。
# - 输入输出：输入为基本面表与安全查询限制；输出为主键、缺失、范围、单位候选和异常清单。
# - 数据与安全：缺失财务值不能填零，经验单位不能冒充厂商正式定义。
# - 运行边界：导入模块和阅读注释不会触发数据库写入；只有显式调用对应函数并满足门禁时才执行I/O。
# - 为什么这样写：先声明职责、单位、时点和副作用边界，读者可以在阅读实现前建立正确的金融与工程语境。
"""DolphinDB基本面快照只读发现与语义画像。

本模块属于TASK_013的数据发现阶段。

它只执行只读查询，目标是确认：
1. 实际字段结构和覆盖范围；
2. (stock_code, snapshot_date)主键质量；
3. 快照、更新、报告期和导入时间的语义；
4. 股本和金额单位候选；
5. FundamentalSnapshot、OwnershipSnapshot和Instrument映射风险；
6. 严格历史回测是否需要阻断。

本模块不会读取桌面Excel目录，不会调用外部导入脚本，
也不会创建、删除或修改DolphinDB数据库和表。
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
# 依赖导入：加载`from typing import Any`所提供的类型、标准库或项目内能力。
# - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
# - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
from typing import Any

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
_IDENTIFIER_PATTERN = re.compile(
    r"^[A-Za-z_][A-Za-z0-9_]*$"
)

# 关键常量EXPECTED_FIELD_TYPES：集中保存`{'stock_code': 'SYMBOL', 'snapshot_date': 'DATE', 'update_date': 'DATE', 'total_shares': 'DOUBLE', …`对应的合同值、Schema集合或运行边界。
# - 来源与范围：该值来自当前项目任务、配置、真实数据画像或安全合同；未明确说明时不得外推为行业统一标准。
# - 单位与实例：数值单位由变量名、相邻校验和调用语义共同限定；字符串用于版本、字段、状态或DolphinDB对象标识。
# - 为什么这样写：集中命名固定参数可避免魔法值散落，并让升级、审计和回归测试有稳定锚点。
EXPECTED_FIELD_TYPES: dict[str, str] = {
    "stock_code": "SYMBOL",
    "snapshot_date": "DATE",
    "update_date": "DATE",
    "total_shares": "DOUBLE",
    "b_shares": "DOUBLE",
    "h_shares": "DOUBLE",
    "circulating_a_shares": "DOUBLE",
    "eps": "DOUBLE",
    "zpg": "DOUBLE",
    "total_assets": "DOUBLE",
    "current_assets": "DOUBLE",
    "fixed_assets": "DOUBLE",
    "intangible_assets": "DOUBLE",
    "shareholder_count": "LONG",
    "current_liabilities": "DOUBLE",
    "long_term_liabilities": "DOUBLE",
    "capital_reserve": "DOUBLE",
    "net_assets": "DOUBLE",
    "operating_revenue": "DOUBLE",
    "operating_cost": "DOUBLE",
    "accounts_receivable": "DOUBLE",
    "operating_profit": "DOUBLE",
    "investment_income": "DOUBLE",
    "operating_cash_flow": "DOUBLE",
    "total_cash_flow": "DOUBLE",
    "inventory": "DOUBLE",
    "total_profit": "DOUBLE",
    "after_tax_profit": "DOUBLE",
    "net_profit": "DOUBLE",
    "undistributed_profit": "DOUBLE",
    "adjusted_nav_per_share": "DOUBLE",
    "region_code": "INT",
    "source_industry_code": "INT",
    "report_period": "INT",
    "listing_date": "DATE",
    "sw_code": "SYMBOL",
    "source_detail_code": "SYMBOL",
    "source_industry_level2_code": "SYMBOL",
    "source_industry_level1_code": "SYMBOL",
    "source_sector": "STRING",
    "source_industry": "STRING",
    "source_subindustry": "STRING",
    "tdx_industry_code": "SYMBOL",
    "sw_subindustry_code": "SYMBOL",
    "sw_industry_code": "SYMBOL",
    "sw_sector_code": "SYMBOL",
    "sw_sector": "STRING",
    "sw_industry": "STRING",
    "sw_subindustry": "STRING",
    "market": "SYMBOL",
    "stock_name": "STRING",
    "pinyin": "STRING",
    "source_file": "STRING",
    "imported_at": "TIMESTAMP",
}

# 关键常量EXPECTED_FIELDS：集中保存`tuple(EXPECTED_FIELD_TYPES)`对应的合同值、Schema集合或运行边界。
# - 来源与范围：该值来自当前项目任务、配置、真实数据画像或安全合同；未明确说明时不得外推为行业统一标准。
# - 单位与实例：数值单位由变量名、相邻校验和调用语义共同限定；字符串用于版本、字段、状态或DolphinDB对象标识。
# - 为什么这样写：集中命名固定参数可避免魔法值散落，并让升级、审计和回归测试有稳定锚点。
EXPECTED_FIELDS = tuple(EXPECTED_FIELD_TYPES)

# 关键常量REQUIRED_FIELDS：集中保存`('stock_code', 'snapshot_date', 'update_date', 'total_shares', 'circulating_a_shares', 'eps', 'tota…`对应的合同值、Schema集合或运行边界。
# - 来源与范围：该值来自当前项目任务、配置、真实数据画像或安全合同；未明确说明时不得外推为行业统一标准。
# - 单位与实例：数值单位由变量名、相邻校验和调用语义共同限定；字符串用于版本、字段、状态或DolphinDB对象标识。
# - 为什么这样写：集中命名固定参数可避免魔法值散落，并让升级、审计和回归测试有稳定锚点。
REQUIRED_FIELDS = (
    "stock_code",
    "snapshot_date",
    "update_date",
    "total_shares",
    "circulating_a_shares",
    "eps",
    "total_assets",
    "net_assets",
    "operating_revenue",
    "operating_cost",
    "operating_profit",
    "total_profit",
    "after_tax_profit",
    "net_profit",
    "report_period",
    "listing_date",
    "market",
    "stock_name",
    "source_file",
    "imported_at",
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
    if (
        enum_value is not None
        and not isinstance(value, (str, bytes))
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


# 函数_records_from_result：执行_records_from_result对应的业务处理。
# - 输入：result:Any；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型list[dict[str, Any]]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
# - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def _records_from_result(
    result: Any,
) -> list[dict[str, Any]]:
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
        if any(
            not isinstance(item, dict)
            for item in result
        ):
            # 错误阻断：抛出`DataContractError('基本面画像结果列表中存在非字典记录。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
            raise DataContractError(
                "基本面画像结果列表中存在非字典记录。"
            )
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
        if any(
            not isinstance(item, dict)
            for item in records
        ):
            # 错误阻断：抛出`DataContractError('基本面画像结果无法转换为字典记录。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
            raise DataContractError(
                "基本面画像结果无法转换为字典记录。"
            )
        # 结果返回：把`list(records)`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return list(records)

    # 错误阻断：抛出`DataContractError('暂不支持当前基本面画像结果类型。')`并停止当前正常路径。
    # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
    # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
    raise DataContractError(
        "暂不支持当前基本面画像结果类型。"
    )


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


# 函数_is_missing：执行_is_missing对应的业务处理。
# - 输入：value:Any；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型bool；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
# - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def _is_missing(value: Any) -> bool:
    # 条件门禁：判断`value is None`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if value is None:
        # 结果返回：把`True`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return True

    # 异常边界：尝试执行可能失败的解析、查询、文件或类型转换步骤，并由后续处理保留错误证据。
    # - 数据变化：正常路径产生业务结果；异常路径不得静默伪造数据，应抛出、记录或隔离。
    # - 为什么这样写：把外部环境故障与业务合同失败分开，便于重试、回滚和准确验收。
    try:
        # 结果返回：把`bool(math.isnan(value))`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return bool(math.isnan(value))
    except (TypeError, ValueError):
        # 结果返回：把`False`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return False


# 函数_as_int：执行_as_int对应的业务处理。
# - 输入：value:Any；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型int；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
# - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def _as_int(value: Any) -> int:
    # 条件门禁：判断`_is_missing(value)`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if _is_missing(value):
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


# 函数_ratio：执行_ratio对应的业务处理。
# - 输入：numerator:int、denominator:int；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型float | None；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
# - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def _ratio(
    numerator: int,
    denominator: int,
) -> float | None:
    # 条件门禁：判断`denominator <= 0`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if denominator <= 0:
        # 结果返回：把`None`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return None

    # 结果返回：把`round(numerator / denominator, 6)`交给调用方并结束当前函数。
    # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return round(numerator / denominator, 6)


# 类FundamentalProfileReport：集中管理FundamentalProfileReport相关状态和不变量。
# - 结构：继承或实现object；类体约包含23个字段或常量、1个方法。
# - 数据变化：类定义阶段不执行隐式I/O，实例只在构造或显式方法调用时改变受控状态。
# - 实操：调用方通过该类型集中传递配置、记录、服务或结果，避免跨模块使用无约束字典。
# - 为什么这样写：强类型边界能集中维护单位、时点、主键和安全不变量，并降低供应商耦合。
@dataclass(slots=True)
class FundamentalProfileReport:
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
    # 状态计算：把`无`的结果保存到`expected_schema`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    expected_schema: dict[str, str]
    # 状态计算：把`无`的结果保存到`raw_fields`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    raw_fields: list[str]
    # 状态计算：把`无`的结果保存到`schema_comparison`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    schema_comparison: dict[str, Any]
    # 状态计算：把`无`的结果保存到`summary`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    summary: dict[str, Any]
    # 状态计算：把`无`的结果保存到`snapshot_counts`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    snapshot_counts: list[dict[str, Any]]
    # 状态计算：把`无`的结果保存到`report_period_counts`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    report_period_counts: list[dict[str, Any]]
    # 状态计算：把`无`的结果保存到`market_counts`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    market_counts: list[dict[str, Any]]
    # 状态计算：把`无`的结果保存到`source_file_counts`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    source_file_counts: list[dict[str, Any]]
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
    # 状态计算：把`无`的结果保存到`anomaly_counts`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    anomaly_counts: dict[str, Any]
    # 状态计算：把`无`的结果保存到`unit_candidate_summary`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    unit_candidate_summary: dict[str, Any]
    # 状态计算：把`无`的结果保存到`sample_rows`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    sample_rows: list[dict[str, Any]]
    # 状态计算：把`field(default_factory=list)`的结果保存到`checks`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    checks: list[dict[str, Any]] = field(
        default_factory=list
    )
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
    # 状态计算：把`True`的结果保存到`blocks_strict_historical_backtest`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    blocks_strict_historical_backtest: bool = True
    # 状态计算：把`False`的结果保存到`allows_current_snapshot_research`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    allows_current_snapshot_research: bool = False

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


# 类DolphinDBFundamentalProfiler：对基本面快照表执行只读聚合画像。
# - 结构：继承或实现object；类体约包含0个字段或常量、7个方法。
# - 数据变化：类定义阶段不执行隐式I/O，实例只在构造或显式方法调用时改变受控状态。
# - 实操：调用方通过该类型集中传递配置、记录、服务或结果，避免跨模块使用无约束字典。
# - 为什么这样写：强类型边界能集中维护单位、时点、主键和安全不变量，并降低供应商耦合。
class DolphinDBFundamentalProfiler:
    """对基本面快照表执行只读聚合画像。"""

    # 函数__init__：执行__init__对应的业务处理。
    # - 输入：adapter:DolphinDBDataSourceAdapter、database_uri:str、table_name:str；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型None；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    def __init__(
        self,
        adapter: DolphinDBDataSourceAdapter,
        database_uri: str = (
            "dfs://A_STOCK_FUNDAMENTAL_DB"
        ),
        table_name: str = (
            "stock_fundamental_snapshot"
        ),
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
    def _query_one(
        self,
        script: str,
    ) -> dict[str, Any]:
        # 结果返回：把`_first_record(self.adapter.run_readonly_query(script))`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return _first_record(
            self.adapter.run_readonly_query(script)
        )

    # 函数_query_rows：执行_query_rows对应的业务处理。
    # - 输入：script:str；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型list[dict[str, Any]]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把只读查询或来源发现步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    def _query_rows(
        self,
        script: str,
    ) -> list[dict[str, Any]]:
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

    # 函数_count_where：执行_count_where对应的业务处理。
    # - 输入：condition:str；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型int；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    def _count_where(
        self,
        condition: str,
    ) -> int:
        # 状态计算：把`re.sub('\\bnot\\s+isNull\\(([A-Za-z_][A-Za-z0-9_]*)\\)', 'not(isNull(\\1))', condition)`的结果保存到`normalized_condition`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        normalized_condition = re.sub(
            r"\bnot\s+isNull\(([A-Za-z_][A-Za-z0-9_]*)\)",
            r"not(isNull(\1))",
            condition,
        )

        # 状态计算：把`self._query_one(f'\n select count(*) as row_count\n from {self._table_ref}\n where {normalized_cond…`的结果保存到`result`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        result = self._query_one(
            f"""
            select count(*) as row_count
            from {self._table_ref}
            where {normalized_condition}
            """
        )
        # 结果返回：把`_as_int(result.get('row_count'))`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return _as_int(result.get("row_count"))

    # 函数collect：执行collect对应的业务处理。
    # - 输入：无外部业务参数；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型FundamentalProfileReport；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    def collect(self) -> FundamentalProfileReport:
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

        # 状态计算：把`sorted(set(EXPECTED_FIELDS) - available)`的结果保存到`missing_fields`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        missing_fields = sorted(
            set(EXPECTED_FIELDS) - available
        )
        # 状态计算：把`sorted(available - set(EXPECTED_FIELDS))`的结果保存到`unexpected_fields`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        unexpected_fields = sorted(
            available - set(EXPECTED_FIELDS)
        )
        # 状态计算：把`{'expected_field_count': len(EXPECTED_FIELDS), 'actual_field_count': len(raw_fields), 'missing_fiel…`的结果保存到`schema_comparison`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        schema_comparison = {
            "expected_field_count": len(EXPECTED_FIELDS),
            "actual_field_count": len(raw_fields),
            "missing_fields": missing_fields,
            "unexpected_fields": unexpected_fields,
            "field_order_matches": (
                tuple(raw_fields) == EXPECTED_FIELDS
            ),
            "declared_type_source": (
                "DolphinDB schema export supplied "
                "during TASK_013 discovery"
            ),
        }

        # 状态计算：把`self._query_one(f'\n select\n count(*) as row_count,\n nunique(stock_code, true)\n as stock_count,\…`的结果保存到`summary`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        summary = self._query_one(
            f"""
            select
                count(*) as row_count,
                nunique(stock_code, true)
                    as stock_count,
                min(snapshot_date)
                    as min_snapshot_date,
                max(snapshot_date)
                    as max_snapshot_date,
                min(update_date)
                    as min_update_date,
                max(update_date)
                    as max_update_date,
                min(listing_date)
                    as min_listing_date,
                max(listing_date)
                    as max_listing_date,
                min(imported_at)
                    as first_imported_at,
                max(imported_at)
                    as last_imported_at
            from {self._table_ref}
            """
        )

        # 状态计算：把`self._query_rows(f'\n select\n snapshot_date,\n count(*) as row_count\n from {self._table_ref}\n gr…`的结果保存到`snapshot_counts`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        snapshot_counts = self._query_rows(
            f"""
            select
                snapshot_date,
                count(*) as row_count
            from {self._table_ref}
            group by snapshot_date
            order by snapshot_date
            """
        )

        # 状态计算：把`self._query_rows(f'\n select\n report_period,\n count(*) as row_count\n from {self._table_ref}\n gr…`的结果保存到`report_period_counts`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        report_period_counts = self._query_rows(
            f"""
            select
                report_period,
                count(*) as row_count
            from {self._table_ref}
            group by report_period
            order by report_period
            """
        )

        # 状态计算：把`self._query_rows(f'\n select\n market,\n count(*) as row_count\n from {self._table_ref}\n group by …`的结果保存到`market_counts`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        market_counts = self._query_rows(
            f"""
            select
                market,
                count(*) as row_count
            from {self._table_ref}
            group by market
            order by market
            """
        )

        # 状态计算：把`self._query_rows(f'\n select\n source_file,\n count(*) as row_count,\n min(snapshot_date)\n as min_…`的结果保存到`source_file_counts`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        source_file_counts = self._query_rows(
            f"""
            select
                source_file,
                count(*) as row_count,
                min(snapshot_date)
                    as min_snapshot_date,
                max(snapshot_date)
                    as max_snapshot_date,
                min(imported_at)
                    as first_imported_at,
                max(imported_at)
                    as last_imported_at
            from {self._table_ref}
            group by source_file
            order by source_file
            """
        )

        # 状态计算：把`',\n'.join((f'sum(isNull({name})) as {name}_null_count' for name in valid_fields))`的结果保存到`null_expressions`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        null_expressions = ",\n".join(
            f"sum(isNull({name})) "
            f"as {name}_null_count"
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
                group by stock_code, snapshot_date
                having count(*) > 1
            )
            """
        )
        # 状态计算：把`_as_int(duplicate_summary.get('duplicate_group_count'))`的结果保存到`duplicate_summary['duplicate_group_count']`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        duplicate_summary[
            "duplicate_group_count"
        ] = _as_int(
            duplicate_summary.get(
                "duplicate_group_count"
            )
        )
        # 状态计算：把`_as_int(duplicate_summary.get('duplicate_extra_row_count'))`的结果保存到`duplicate_summary['duplicate_extra_row_count']`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        duplicate_summary[
            "duplicate_extra_row_count"
        ] = _as_int(
            duplicate_summary.get(
                "duplicate_extra_row_count"
            )
        )

        # 状态计算：把`self._query_rows(f'\n select top 20\n stock_code,\n snapshot_date,\n count(*) as duplicate_count\n …`的结果保存到`duplicate_samples`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        duplicate_samples = self._query_rows(
            f"""
            select top 20
                stock_code,
                snapshot_date,
                count(*) as duplicate_count
            from {self._table_ref}
            group by stock_code, snapshot_date
            having count(*) > 1
            order by duplicate_count desc
            """
        )

        # 状态计算：把`{'key_null_count': self._count_where('isNull(stock_code) or isNull(snapshot_date)'), 'update_after_…`的结果保存到`anomaly_counts`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        anomaly_counts = {
            "key_null_count": self._count_where(
                "isNull(stock_code) "
                "or isNull(snapshot_date)"
            ),
            "update_after_snapshot_count":
                self._count_where(
                    "not isNull(update_date) "
                    "and not isNull(snapshot_date) "
                    "and update_date > snapshot_date"
                ),
            "listing_after_snapshot_count":
                self._count_where(
                    "not isNull(listing_date) "
                    "and not isNull(snapshot_date) "
                    "and listing_date > snapshot_date"
                ),
            "negative_total_shares_count":
                self._count_where(
                    "not isNull(total_shares) "
                    "and total_shares < 0"
                ),
            "negative_circulating_shares_count":
                self._count_where(
                    "not isNull("
                    "circulating_a_shares) "
                    "and circulating_a_shares < 0"
                ),
            "circulating_above_total_count":
                self._count_where(
                    "not isNull(total_shares) "
                    "and not isNull("
                    "circulating_a_shares) "
                    "and circulating_a_shares "
                    "> total_shares"
                ),
            "nonpositive_total_assets_count":
                self._count_where(
                    "not isNull(total_assets) "
                    "and total_assets <= 0"
                ),
            "source_file_null_count":
                self._count_where(
                    "isNull(source_file)"
                ),
            "imported_at_null_count":
                self._count_where(
                    "isNull(imported_at)"
                ),
        }

        # 状态计算：把`self._count_where('not isNull(net_assets) and not isNull(total_shares) and total_shares > 0 and not…`的结果保存到`nav_checked_count`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        nav_checked_count = self._count_where(
            "not isNull(net_assets) "
            "and not isNull(total_shares) "
            "and total_shares > 0 "
            "and not isNull("
            "adjusted_nav_per_share)"
        )
        # 状态计算：把`self._count_where('not isNull(net_assets) and not isNull(total_shares) and total_shares > 0 and not…`的结果保存到`nav_match_thousand_cny_10k_shares`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        nav_match_thousand_cny_10k_shares = (
            self._count_where(
                "not isNull(net_assets) "
                "and not isNull(total_shares) "
                "and total_shares > 0 "
                "and not isNull("
                "adjusted_nav_per_share) "
                "and abs("
                "net_assets / "
                "(total_shares * 10.0) "
                "- adjusted_nav_per_share"
                ") <= 0.05"
            )
        )
        # 状态计算：把`self._count_where('not isNull(net_assets) and not isNull(total_shares) and total_shares > 0 and not…`的结果保存到`nav_match_10k_cny_10k_shares`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        nav_match_10k_cny_10k_shares = (
            self._count_where(
                "not isNull(net_assets) "
                "and not isNull(total_shares) "
                "and total_shares > 0 "
                "and not isNull("
                "adjusted_nav_per_share) "
                "and abs("
                "net_assets / total_shares "
                "- adjusted_nav_per_share"
                ") <= 0.05"
            )
        )
        # 状态计算：把`self._count_where('not isNull(after_tax_profit) and not isNull(net_profit)')`的结果保存到`profit_comparable_count`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        profit_comparable_count = self._count_where(
            "not isNull(after_tax_profit) "
            "and not isNull(net_profit)"
        )
        # 状态计算：把`self._count_where('not isNull(after_tax_profit) and not isNull(net_profit) and abs(after_tax_profit…`的结果保存到`profit_equal_count`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        profit_equal_count = self._count_where(
            "not isNull(after_tax_profit) "
            "and not isNull(net_profit) "
            "and abs(after_tax_profit "
            "- net_profit) <= 0.000001"
        )

        # 状态计算：把`{'nav_formula_checked_count': nav_checked_count, 'money_thousand_cny_and_shares_10k_match_count': n…`的结果保存到`unit_candidate_summary`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        unit_candidate_summary = {
            "nav_formula_checked_count":
                nav_checked_count,
            "money_thousand_cny_and_shares_10k_match_count":
                nav_match_thousand_cny_10k_shares,
            "money_10k_cny_and_shares_10k_match_count":
                nav_match_10k_cny_10k_shares,
            "money_thousand_cny_and_shares_10k_match_ratio":
                _ratio(
                    nav_match_thousand_cny_10k_shares,
                    nav_checked_count,
                ),
            "money_10k_cny_and_shares_10k_match_ratio":
                _ratio(
                    nav_match_10k_cny_10k_shares,
                    nav_checked_count,
                ),
            "after_tax_and_net_profit_comparable_count":
                profit_comparable_count,
            "after_tax_and_net_profit_equal_count":
                profit_equal_count,
            "after_tax_and_net_profit_equal_ratio":
                _ratio(
                    profit_equal_count,
                    profit_comparable_count,
                ),
            "interpretation": (
                "该结果仅用于单位和利润口径候选判断，"
                "不能替代供应商说明或人工确认。"
            ),
        }

        # 状态计算：把`self._query_rows(f'\n select top 20\n stock_code,\n stock_name,\n market,\n snapshot_date,\n update…`的结果保存到`sample_rows`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        sample_rows = self._query_rows(
            f"""
            select top 20
                stock_code,
                stock_name,
                market,
                snapshot_date,
                update_date,
                report_period,
                total_shares,
                circulating_a_shares,
                shareholder_count,
                eps,
                adjusted_nav_per_share,
                total_assets,
                net_assets,
                operating_revenue,
                operating_cost,
                operating_profit,
                total_profit,
                after_tax_profit,
                net_profit,
                source_file,
                imported_at
            from {self._table_ref}
            order by stock_code
            """
        )

        # 状态计算：把`[]`的结果保存到`checks`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        checks: list[dict[str, Any]] = []

        # 状态计算：把`sorted(set(REQUIRED_FIELDS) - available)`的结果保存到`missing_required`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        missing_required = sorted(
            set(REQUIRED_FIELDS) - available
        )
        # 显式调用：执行`checks.append({'check_name': '必需字段完整性', 'status': 'PASSED' if not missing_required else 'FAILED', 'blocking': bool(missing_required), 'deta…`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
        # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
        # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
        checks.append({
            "check_name": "必需字段完整性",
            "status": (
                "PASSED"
                if not missing_required
                else "FAILED"
            ),
            "blocking": bool(missing_required),
            "details": {
                "missing_fields": missing_required,
            },
        })

        # 显式调用：执行`checks.append({'check_name': '54列物理结构一致性', 'status': 'PASSED' if not missing_fields and (not unexpected_fields) and (len(raw_fields) == len…`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
        # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
        # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
        checks.append({
            "check_name": "54列物理结构一致性",
            "status": (
                "PASSED"
                if (
                    not missing_fields
                    and not unexpected_fields
                    and len(raw_fields)
                    == len(EXPECTED_FIELDS)
                )
                else "FAILED"
            ),
            "blocking": bool(
                missing_fields or unexpected_fields
            ),
            "details": schema_comparison,
        })

        # 状态计算：把`duplicate_summary['duplicate_extra_row_count']`的结果保存到`duplicate_count`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        duplicate_count = duplicate_summary[
            "duplicate_extra_row_count"
        ]
        # 显式调用：执行`checks.append({'check_name': '基本面快照主键重复', 'status': 'PASSED' if duplicate_count == 0 else 'FAILED', 'blocking': duplicate_count > 0, 'detai…`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
        # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
        # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
        checks.append({
            "check_name": "基本面快照主键重复",
            "status": (
                "PASSED"
                if duplicate_count == 0
                else "FAILED"
            ),
            "blocking": duplicate_count > 0,
            "details": duplicate_summary,
        })

        # 状态计算：把`anomaly_counts['key_null_count']`的结果保存到`key_null_count`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        key_null_count = anomaly_counts[
            "key_null_count"
        ]
        # 显式调用：执行`checks.append({'check_name': '基本面快照主键空值', 'status': 'PASSED' if key_null_count == 0 else 'FAILED', 'blocking': key_null_count > 0, 'details…`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
        # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
        # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
        checks.append({
            "check_name": "基本面快照主键空值",
            "status": (
                "PASSED"
                if key_null_count == 0
                else "FAILED"
            ),
            "blocking": key_null_count > 0,
            "details": {
                "key_null_count": key_null_count,
            },
        })

        # 状态计算：把`[check for check in checks if check['status'] == 'FAILED' and check['blocking']]`的结果保存到`structural_failures`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        structural_failures = [
            check
            for check in checks
            if (
                check["status"] == "FAILED"
                and check["blocking"]
            )
        ]

        # 状态计算：把`{_as_int(item.get('report_period')) for item in report_period_counts if not _is_missing(item.get('r…`的结果保存到`period_values`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        period_values = {
            _as_int(item.get("report_period"))
            for item in report_period_counts
            if not _is_missing(
                item.get("report_period")
            )
        }
        # 状态计算：把`bool(period_values) and period_values.issubset({3, 6, 9, 12})`的结果保存到`period_month_candidate`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        period_month_candidate = (
            bool(period_values)
            and period_values.issubset(
                {3, 6, 9, 12}
            )
        )

        # 状态计算：把`[{'category': 'FUNDAMENTAL_REPORT_PERIOD', 'blocking_for': 'strict_historical_backtest', 'question'…`的结果保存到`pending_confirmations`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        pending_confirmations = [
            {
                "category":
                    "FUNDAMENTAL_REPORT_PERIOD",
                "blocking_for":
                    "strict_historical_backtest",
                "question": (
                    "来源report_period是3/6/9/12月码、"
                    "季度码还是其他枚举？"
                ),
                "evidence": {
                    "observed_values":
                        sorted(period_values),
                    "period_month_candidate":
                        period_month_candidate,
                    "canonical_requirement":
                        "FundamentalSnapshot."
                        "report_period必须为DATE，"
                        "period_type必须明确。",
                },
            },
            {
                "category":
                    "FUNDAMENTAL_AVAILABLE_AT",
                "blocking_for":
                    "strict_historical_backtest",
                "question": (
                    "update_date是否等于正式公告日期，"
                    "还是供应商内部更新日期？"
                ),
                "evidence": {
                    "snapshot_date_semantics":
                        "文件观测快照日期",
                    "required_rule":
                        "available_at <= decision_time",
                },
            },
            {
                "category":
                    "FUNDAMENTAL_MONEY_UNIT",
                "blocking_for":
                    "canonical_mapping",
                "question": (
                    "资产、收入、利润和现金流字段"
                    "是否以千元人民币计量？"
                ),
                "evidence": unit_candidate_summary,
            },
            {
                "category":
                    "FUNDAMENTAL_SHARE_UNIT",
                "blocking_for":
                    "canonical_mapping",
                "question": (
                    "total_shares、b_shares、h_shares"
                    "和circulating_a_shares"
                    "是否以万股计量？"
                ),
                "evidence": {
                    "candidate_transform":
                        "multiply by 10000",
                },
            },
            {
                "category":
                    "FUNDAMENTAL_PROFIT_SCOPE",
                "blocking_for":
                    "canonical_mapping",
                "question": (
                    "after_tax_profit是否为公司整体净利润，"
                    "net_profit是否为归母净利润？"
                ),
                "evidence": unit_candidate_summary,
            },
            {
                "category":
                    "FUNDAMENTAL_EQUITY_SCOPE",
                "blocking_for":
                    "canonical_mapping",
                "question": (
                    "net_assets是所有者权益合计，"
                    "还是归母所有者权益？"
                ),
            },
            {
                "category":
                    "FUNDAMENTAL_TOTAL_CASH_FLOW",
                "blocking_for":
                    "canonical_mapping",
                "question": (
                    "total_cash_flow的准确会计含义是什么？"
                ),
            },
            {
                "category":
                    "FUNDAMENTAL_ZPG",
                "blocking_for":
                    "field_mapping",
                "question": (
                    "zpg字段的全称、单位和口径是什么？"
                ),
            },
            {
                "category":
                    "FUNDAMENTAL_COMPANY_ID",
                "blocking_for":
                    "canonical_mapping",
                "question": (
                    "FundamentalSnapshot要求company_id，"
                    "当前来源只有stock_code；"
                    "需要统一公司身份解析规则。"
                ),
            },
            {
                "category":
                    "CLASSIFICATION_HISTORY",
                "blocking_for":
                    "strict_historical_backtest",
                "question": (
                    "来源行业和申万行业字段缺少"
                    "分类版本与有效起止时间，"
                    "当前只能视为snapshot_date观察到的分类。"
                ),
            },
            {
                "category":
                    "INSTRUMENT_ID_FORMAT",
                "blocking_for":
                    "identity_governance",
                "question": (
                    "当前日K使用6位stock_code作为"
                    "instrument_id；基本面必须保持一致，"
                    "未来如升级为000001.SZ需统一迁移。"
                ),
            },
        ]

        # 条件门禁：判断`structural_failures`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if structural_failures:
            # 状态计算：把`QualityStatus.FAILED`的结果保存到`overall_status`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            overall_status = QualityStatus.FAILED
            # 状态计算：把`True`的结果保存到`blocks_downstream`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            blocks_downstream = True
            # 状态计算：把`False`的结果保存到`allows_current_snapshot_research`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            allows_current_snapshot_research = False
        else:
            # 状态计算：把`QualityStatus.PENDING_CONFIRMATION`的结果保存到`overall_status`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            overall_status = (
                QualityStatus.PENDING_CONFIRMATION
            )
            # 状态计算：把`True`的结果保存到`blocks_downstream`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            blocks_downstream = True
            # 状态计算：把`True`的结果保存到`allows_current_snapshot_research`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            allows_current_snapshot_research = True

        # 结果返回：把`FundamentalProfileReport(database_uri=self.database_uri, table_name=self.table_name, generated_at=_utc_now(), expected_…`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return FundamentalProfileReport(
            database_uri=self.database_uri,
            table_name=self.table_name,
            generated_at=_utc_now(),
            expected_schema=dict(EXPECTED_FIELD_TYPES),
            raw_fields=raw_fields,
            schema_comparison=schema_comparison,
            summary=summary,
            snapshot_counts=snapshot_counts,
            report_period_counts=
                report_period_counts,
            market_counts=market_counts,
            source_file_counts=source_file_counts,
            null_counts=null_counts,
            duplicate_summary=duplicate_summary,
            duplicate_samples=duplicate_samples,
            anomaly_counts=anomaly_counts,
            unit_candidate_summary=
                unit_candidate_summary,
            sample_rows=sample_rows,
            checks=checks,
            pending_confirmations=
                pending_confirmations,
            overall_status=overall_status,
            blocks_downstream=blocks_downstream,
            blocks_strict_historical_backtest=True,
            allows_current_snapshot_research=
                allows_current_snapshot_research,
        )


# 函数render_markdown：执行render_markdown对应的业务处理。
# - 输入：report:FundamentalProfileReport；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型str；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
# - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def render_markdown(
    report: FundamentalProfileReport,
) -> str:
    # 状态计算：把`report.to_dict()`的结果保存到`value`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    value = report.to_dict()
    # 状态计算：把`value['summary']`的结果保存到`summary`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    summary = value["summary"]
    # 状态计算：把`value['duplicate_summary']`的结果保存到`duplicate_summary`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    duplicate_summary = value[
        "duplicate_summary"
    ]
    # 状态计算：把`value['anomaly_counts']`的结果保存到`anomalies`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    anomalies = value["anomaly_counts"]
    # 状态计算：把`value['unit_candidate_summary']`的结果保存到`unit_candidates`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    unit_candidates = value[
        "unit_candidate_summary"
    ]

    # 状态计算：把`['# TASK_013 基本面快照画像检查', '', f'- 数据库：`{report.database_uri}`', f'- 表：`{report.table_name}`', f"- 生成…`的结果保存到`lines`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    lines = [
        "# TASK_013 基本面快照画像检查",
        "",
        f"- 数据库：`{report.database_uri}`",
        f"- 表：`{report.table_name}`",
        f"- 生成时间：`{value['generated_at']}`",
        (
            "- 状态："
            f"`{value['overall_status']}`"
        ),
        (
            "- 阻断严格历史回测："
            f"`{value['blocks_strict_historical_backtest']}`"
        ),
        (
            "- 允许当前快照研究："
            f"`{value['allows_current_snapshot_research']}`"
        ),
        "",
        "## 结构与覆盖",
        "",
        (
            f"- 实际字段数："
            f"{value['schema_comparison']['actual_field_count']}"
        ),
        (
            f"- 总行数："
            f"{summary.get('row_count')}"
        ),
        (
            f"- 股票数："
            f"{summary.get('stock_count')}"
        ),
        (
            "- 快照范围："
            f"{summary.get('min_snapshot_date')} "
            f"至 {summary.get('max_snapshot_date')}"
        ),
        (
            "- 重复额外行数："
            f"{duplicate_summary.get('duplicate_extra_row_count')}"
        ),
        "",
        "## 关键异常",
        "",
    ]

    # 循环处理：逐项遍历`anomalies.items()`，把当前元素绑定到`(name, count)`。
    # - 数据变化：每轮只处理一个来源记录、字段、文件或证据项，并显式累计到局部集合或输出对象。
    # - 为什么这样写：逐项处理便于保留行级血缘、隔离单项异常，并控制16GB单机上的峰值内存。
    for name, count in anomalies.items():
        # 显式调用：执行`lines.append(f'- `{name}`：{count}')`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
        # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
        # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
        lines.append(f"- `{name}`：{count}")

    # 显式调用：执行`lines.extend(['', '## 单位候选', '', f"- 千元人民币 + 万股公式匹配率：{unit_candidates.get('money_thousand_cny_and_shares_10k_match_ratio')}", f"- 万元人民币 + 万…`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
    # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
    # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
    lines.extend([
        "",
        "## 单位候选",
        "",
        (
            "- 千元人民币 + 万股公式匹配率："
            f"{unit_candidates.get('money_thousand_cny_and_shares_10k_match_ratio')}"
        ),
        (
            "- 万元人民币 + 万股公式匹配率："
            f"{unit_candidates.get('money_10k_cny_and_shares_10k_match_ratio')}"
        ),
        "",
        "## 待确认事项",
        "",
    ])

    # 循环处理：逐项遍历`value['pending_confirmations']`，把当前元素绑定到`item`。
    # - 数据变化：每轮只处理一个来源记录、字段、文件或证据项，并显式累计到局部集合或输出对象。
    # - 为什么这样写：逐项处理便于保留行级血缘、隔离单项异常，并控制16GB单机上的峰值内存。
    for item in value["pending_confirmations"]:
        # 显式调用：执行`lines.append(f"- **{item['category']}**：{item['question']}")`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
        # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
        # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
        lines.append(
            f"- **{item['category']}**："
            f"{item['question']}"
        )

    # 显式调用：执行`lines.extend(['', '## 结论', '', '该数据集可以继续完成标准映射和Provider开发，但在公告日期、报告期、单位和利润口径确认前，不得用于严格历史点时回测。', ''])`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
    # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
    # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
    lines.extend([
        "",
        "## 结论",
        "",
        (
            "该数据集可以继续完成标准映射和Provider开发，"
            "但在公告日期、报告期、单位和利润口径确认前，"
            "不得用于严格历史点时回测。"
        ),
        "",
    ])

    # 结果返回：把`'\n'.join(lines)`交给调用方并结束当前函数。
    # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return "\n".join(lines)


# 函数write_reports：执行write_reports对应的业务处理。
# - 输入：report:FundamentalProfileReport、json_path:str | Path、markdown_path:str | Path；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型None；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：该函数名称涉及写入能力，只有调用方显式进入受控模式时才可能产生数据库或文件副作用；注释迁移和验证不会调用它。
# - 为什么这样写：把显式写入或持久化步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def write_reports(
    report: FundamentalProfileReport,
    json_path: str | Path,
    markdown_path: str | Path,
) -> None:
    # 状态计算：把`Path(json_path)`的结果保存到`json_file`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    json_file = Path(json_path)
    # 状态计算：把`Path(markdown_path)`的结果保存到`markdown_file`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    markdown_file = Path(markdown_path)

    # 显式调用：执行`json_file.parent.mkdir(parents=True, exist_ok=True)`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
    # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
    # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
    json_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    # 显式调用：执行`markdown_file.parent.mkdir(parents=True, exist_ok=True)`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
    # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
    # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
    markdown_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # 显式调用：执行`json_file.write_text(json.dumps(report.to_dict(), ensure_ascii=False, indent=2), encoding='utf-8')`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
    # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
    # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
    json_file.write_text(
        json.dumps(
            report.to_dict(),
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    # 显式调用：执行`markdown_file.write_text(render_markdown(report), encoding='utf-8')`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
    # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
    # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
    markdown_file.write_text(
        render_markdown(report),
        encoding="utf-8",
    )


# 函数build_parser：执行build_parser对应的业务处理。
# - 输入：无外部业务参数；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型argparse.ArgumentParser；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
# - 为什么这样写：把对象构造、字段映射或标准化转换步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def build_parser() -> argparse.ArgumentParser:
    # 状态计算：把`argparse.ArgumentParser(description='对DolphinDB基本面快照表执行只读画像。')`的结果保存到`parser`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    parser = argparse.ArgumentParser(
        description=(
            "对DolphinDB基本面快照表执行只读画像。"
        )
    )
    # 显式调用：执行`parser.add_argument('--host', default='127.0.0.1')`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
    # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
    # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
    parser.add_argument(
        "--host",
        default="127.0.0.1",
    )
    # 显式调用：执行`parser.add_argument('--port', type=int, default=8848)`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
    # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
    # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
    parser.add_argument(
        "--port",
        type=int,
        default=8848,
    )
    # 显式调用：执行`parser.add_argument('--username', default='admin')`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
    # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
    # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
    parser.add_argument(
        "--username",
        default="admin",
    )
    # 显式调用：执行`parser.add_argument('--database-uri', default='dfs://A_STOCK_FUNDAMENTAL_DB')`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
    # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
    # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
    parser.add_argument(
        "--database-uri",
        default="dfs://A_STOCK_FUNDAMENTAL_DB",
    )
    # 显式调用：执行`parser.add_argument('--table-name', default='stock_fundamental_snapshot')`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
    # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
    # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
    parser.add_argument(
        "--table-name",
        default="stock_fundamental_snapshot",
    )
    # 显式调用：执行`parser.add_argument('--output', default='reports/task_013_fundamental_profile.json')`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
    # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
    # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
    parser.add_argument(
        "--output",
        default=(
            "reports/"
            "task_013_fundamental_profile.json"
        ),
    )
    # 显式调用：执行`parser.add_argument('--markdown-output', default='reports/task_013_fundamental_profile_final_check.md')`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
    # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
    # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
    parser.add_argument(
        "--markdown-output",
        default=(
            "reports/"
            "task_013_fundamental_profile_final_check.md"
        ),
    )
    # 结果返回：把`parser`交给调用方并结束当前函数。
    # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return parser


# 函数main：执行main对应的业务处理。
# - 输入：无外部业务参数；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型int；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
# - 为什么这样写：把任务入口与流程编排步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def main() -> int:
    # 状态计算：把`build_parser().parse_args()`的结果保存到`args`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    args = build_parser().parse_args()
    # 状态计算：把`resolve_password()`的结果保存到`password`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    password = resolve_password()

    # 状态计算：把`DolphinDBConnectionSettings(host=args.host, port=args.port, username=args.username, password=passwo…`的结果保存到`settings`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    settings = DolphinDBConnectionSettings(
        host=args.host,
        port=args.port,
        username=args.username,
        password=password,
    )
    # 状态计算：把`DolphinDBDataSourceAdapter(settings=settings, source_id='dolphindb_fundamental')`的结果保存到`adapter`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    adapter = DolphinDBDataSourceAdapter(
        settings=settings,
        source_id="dolphindb_fundamental",
    )

    # 状态计算：把`adapter.health_check()`的结果保存到`health`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    health = adapter.health_check()
    # 条件门禁：判断`health.status is not QualityStatus.PASSED`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if health.status is not QualityStatus.PASSED:
        # 显式调用：执行`print(f'DolphinDB健康检查失败：{health.description}')`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
        # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
        # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
        print(
            "DolphinDB健康检查失败："
            f"{health.description}"
        )
        # 结果返回：把`1`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return 1

    # 状态计算：把`DolphinDBFundamentalProfiler(adapter=adapter, database_uri=args.database_uri, table_name=args.table…`的结果保存到`report`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    report = DolphinDBFundamentalProfiler(
        adapter=adapter,
        database_uri=args.database_uri,
        table_name=args.table_name,
    ).collect()

    # 显式调用：执行`write_reports(report, args.output, args.markdown_output)`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
    # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
    # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
    write_reports(
        report,
        args.output,
        args.markdown_output,
    )

    # 显式调用：执行`print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
    # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
    # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
    print(
        json.dumps(
            report.to_dict(),
            ensure_ascii=False,
            indent=2,
        )
    )
    # 显式调用：执行`print(f'\n画像报告已写入：{args.output}')`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
    # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
    # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
    print(
        "\n画像报告已写入："
        f"{args.output}"
    )
    # 显式调用：执行`print(f'检查摘要已写入：{args.markdown_output}')`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
    # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
    # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
    print(
        "检查摘要已写入："
        f"{args.markdown_output}"
    )
    # 结果返回：把`0 if report.overall_status is not QualityStatus.FAILED else 2`交给调用方并结束当前函数。
    # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return (
        0
        if report.overall_status
        is not QualityStatus.FAILED
        else 2
    )


# 条件门禁：判断`__name__ == '__main__'`，条件成立时进入对应的数据、安全或异常处理分支。
# - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
# - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
if __name__ == "__main__":
    # 错误阻断：抛出`SystemExit(main())`并停止当前正常路径。
    # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
    # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
    raise SystemExit(main())
