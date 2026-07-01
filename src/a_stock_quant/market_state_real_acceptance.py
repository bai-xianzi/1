# 模块总览：TASK_019C真实市场状态特征验收的只读计划与报告合同。
# - 输入输出：本模块通过强类型合同、纯函数和显式服务调用交换数据，不在导入阶段执行数据库写入或交易动作。
# - 数据变化：只有显式构造、校验、查询、证据组合或报告导出才产生新对象与受控状态。
# - 时点与安全：就绪度和市场状态相关逻辑必须保留usage、as_of、available_at、血缘与阻断信息。
# - 为什么这样写：先声明模块边界，读者可以在阅读实现前理解职责、风险、数值语义和可复用方式。
"""TASK_019C真实市场状态特征验收的只读计划与报告合同。"""
# 依赖导入：执行`from __future__ import annotations`，加载下方合同、类型或标准库能力。
# - 数据变化：导入只把模块、类或函数绑定到当前命名空间，不在本行主动查询数据库或修改业务数据。
# - 为什么这样写：显式依赖使模块边界、可替换组件和测试注入点保持清晰。
from __future__ import annotations

# 依赖导入：执行`import json`，加载下方合同、类型或标准库能力。
# - 数据变化：导入只把模块、类或函数绑定到当前命名空间，不在本行主动查询数据库或修改业务数据。
# - 为什么这样写：显式依赖使模块边界、可替换组件和测试注入点保持清晰。
import json
# 依赖导入：执行`from dataclasses import asdict, dataclass`，加载下方合同、类型或标准库能力。
# - 数据变化：导入只把模块、类或函数绑定到当前命名空间，不在本行主动查询数据库或修改业务数据。
# - 为什么这样写：显式依赖使模块边界、可替换组件和测试注入点保持清晰。
from dataclasses import asdict, dataclass
# 依赖导入：执行`from datetime import date, datetime`，加载下方合同、类型或标准库能力。
# - 数据变化：导入只把模块、类或函数绑定到当前命名空间，不在本行主动查询数据库或修改业务数据。
# - 为什么这样写：显式依赖使模块边界、可替换组件和测试注入点保持清晰。
from datetime import date, datetime
# 依赖导入：执行`from pathlib import Path`，加载下方合同、类型或标准库能力。
# - 数据变化：导入只把模块、类或函数绑定到当前命名空间，不在本行主动查询数据库或修改业务数据。
# - 为什么这样写：显式依赖使模块边界、可替换组件和测试注入点保持清晰。
from pathlib import Path
# 依赖导入：执行`from typing import Any, Iterable, Mapping, Sequence`，加载下方合同、类型或标准库能力。
# - 数据变化：导入只把模块、类或函数绑定到当前命名空间，不在本行主动查询数据库或修改业务数据。
# - 为什么这样写：显式依赖使模块边界、可替换组件和测试注入点保持清晰。
from typing import Any, Iterable, Mapping, Sequence

# 依赖导入：执行`from .data_contracts import DataContractError`，加载下方合同、类型或标准库能力。
# - 数据变化：导入只把模块、类或函数绑定到当前命名空间，不在本行主动查询数据库或修改业务数据。
# - 为什么这样写：显式依赖使模块边界、可替换组件和测试注入点保持清晰。
from .data_contracts import DataContractError
# 依赖导入：执行`from .standard_data_service import ( ENTITY_SELECTOR_MODE, INSTRUMENT_SELECTOR_MODE,`，加载下方合同、类型或标准库能力。
# - 数据变化：导入只把模块、类或函数绑定到当前命名空间，不在本行主动查询数据库或修改业务数据。
# - 为什么这样写：显式依赖使模块边界、可替换组件和测试注入点保持清晰。
from .standard_data_service import (
    ENTITY_SELECTOR_MODE,
    INSTRUMENT_SELECTOR_MODE,
    StandardDataQuery,
    StandardDataUsage,
)


# 关键常量REAL_FEATURE_ACCEPTANCE_PLAN_VERSION：把`'0.1.0'`固定为本模块可追踪的合同值。
# - 来源：该值来自当前项目任务合同、配置或真实验收口径；未标注为行业标准时不得外推为通用值。
# - 数据范围：字符串常量用于版本、状态或模式标识；数值常量的单位和有效范围由相邻校验与调用语义约束。
# - 实操示例：报告和下游对象携带该值后，可以判断生产者版本并复现实验或验收过程。
# - 为什么这样写：集中命名固定参数可避免魔法值散落，并让配置升级、审计和兼容性检查有明确锚点。
REAL_FEATURE_ACCEPTANCE_PLAN_VERSION = "0.1.0"
# 关键常量REAL_FEATURE_ACCEPTANCE_MODE：把`'REAL_READONLY_MARKET_STATE_FEATURE_ACCEPTANCE'`固定为本模块可追踪的合同值。
# - 来源：该值来自当前项目任务合同、配置或真实验收口径；未标注为行业标准时不得外推为通用值。
# - 数据范围：字符串常量用于版本、状态或模式标识；数值常量的单位和有效范围由相邻校验与调用语义约束。
# - 实操示例：报告和下游对象携带该值后，可以判断生产者版本并复现实验或验收过程。
# - 为什么这样写：集中命名固定参数可避免魔法值散落，并让配置升级、审计和兼容性检查有明确锚点。
REAL_FEATURE_ACCEPTANCE_MODE = (
    "REAL_READONLY_MARKET_STATE_FEATURE_ACCEPTANCE"
)
# 关键常量REAL_FEATURE_ACCEPTANCE_UNIVERSE_SCOPE：把`'DETERMINISTIC_CAPPED_REAL_QUERY_UNIVERSE'`固定为本模块可追踪的合同值。
# - 来源：该值来自当前项目任务合同、配置或真实验收口径；未标注为行业标准时不得外推为通用值。
# - 数据范围：字符串常量用于版本、状态或模式标识；数值常量的单位和有效范围由相邻校验与调用语义约束。
# - 实操示例：报告和下游对象携带该值后，可以判断生产者版本并复现实验或验收过程。
# - 为什么这样写：集中命名固定参数可避免魔法值散落，并让配置升级、审计和兼容性检查有明确锚点。
REAL_FEATURE_ACCEPTANCE_UNIVERSE_SCOPE = (
    "DETERMINISTIC_CAPPED_REAL_QUERY_UNIVERSE"
)


# 函数_require_text：执行_require_text逻辑。
# - 参数value：类型str；进入函数后按合同参与校验、筛选、计算或路由。
# - 参数field_name：类型str；进入函数后按合同参与校验、筛选、计算或路由。
# - 输出：返回类型str；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
# - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
# - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
def _require_text(value: str, field_name: str) -> str:
    # 条件门禁：判断`not isinstance(value, str) or not value.strip()`，条件为真时进入受保护分支。
    # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
    # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
    # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
    if not isinstance(value, str) or not value.strip():
        # 错误阻断：抛出`DataContractError(f'{field_name}不能为空。')`并停止当前正常路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
        # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
        raise DataContractError(f"{field_name}不能为空。")
    # 结果返回：把`value.strip()`交给调用方并结束当前函数。
    # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return value.strip()


# 函数_require_positive_int：执行_require_positive_int逻辑。
# - 参数value：类型int；进入函数后按合同参与校验、筛选、计算或路由。
# - 参数field_name：类型str；进入函数后按合同参与校验、筛选、计算或路由。
# - 输出：返回类型int；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
# - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
# - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
def _require_positive_int(value: int, field_name: str) -> int:
    # 条件门禁：判断`not isinstance(value, int) or isinstance(value, bool) or value < 1`，条件为真时进入受保护分支。
    # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
    # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
    # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        # 错误阻断：抛出`DataContractError(f'{field_name}必须是正整数。')`并停止当前正常路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
        # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
        raise DataContractError(f"{field_name}必须是正整数。")
    # 结果返回：把`value`交给调用方并结束当前函数。
    # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return value


# 函数_coerce_date：执行_coerce_date逻辑。
# - 参数value：类型Any；进入函数后按合同参与校验、筛选、计算或路由。
# - 输出：返回类型date；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
# - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
# - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
def _coerce_date(value: Any) -> date:
    # 条件门禁：判断`isinstance(value, datetime)`，条件为真时进入受保护分支。
    # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
    # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
    # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
    if isinstance(value, datetime):
        # 结果返回：把`value.date()`交给调用方并结束当前函数。
        # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return value.date()
    # 条件门禁：判断`isinstance(value, date)`，条件为真时进入受保护分支。
    # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
    # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
    # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
    if isinstance(value, date):
        # 结果返回：把`value`交给调用方并结束当前函数。
        # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return value
    # 变量更新：计算并保存converted，右侧逻辑为`getattr(value, 'to_pydatetime', lambda: None)()`。
    # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
    # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
    converted = getattr(value, "to_pydatetime", lambda: None)()
    # 条件门禁：判断`isinstance(converted, datetime)`，条件为真时进入受保护分支。
    # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
    # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
    # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
    if isinstance(converted, datetime):
        # 结果返回：把`converted.date()`交给调用方并结束当前函数。
        # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return converted.date()
    # 条件门禁：判断`isinstance(converted, date)`，条件为真时进入受保护分支。
    # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
    # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
    # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
    if isinstance(converted, date):
        # 结果返回：把`converted`交给调用方并结束当前函数。
        # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return converted
    # 变量更新：计算并保存text，右侧逻辑为`str(value).strip().replace('.', '-')`。
    # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
    # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
    text = str(value).strip().replace(".", "-")
    # 异常边界：执行可能失败的解析、转换、文件读取或外部调用，并在后续分支转换为项目统一错误。
    # - 数据变化：成功路径产生正常结果；失败路径保留原异常作为cause、降级为缺失值或记录明确问题。
    # - 为什么这样写：上层只需处理稳定的DataContractError或受控结果，不依赖第三方异常实现细节。
    try:
        # 结果返回：把`date.fromisoformat(text[:10])`交给调用方并结束当前函数。
        # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return date.fromisoformat(text[:10])
    # 异常转换：捕获ValueError，保存上下文并执行统一错误、回退或忽略策略。
    # - 数据变化：异常路径不返回未校验的半成品；必要时把失败原因写入issues、warnings或异常链。
    # - 为什么这样写：明确捕获范围可避免吞掉程序错误，同时让调用方获得稳定且可审计的失败语义。
    except ValueError as exc:
        # 错误阻断：抛出`DataContractError(f'无法解析日期：{value!r}')`并停止当前正常路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
        # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
        raise DataContractError(f"无法解析日期：{value!r}") from exc


# 函数_ddb_date_literal：执行_ddb_date_literal逻辑。
# - 参数value：类型date；进入函数后按合同参与校验、筛选、计算或路由。
# - 输出：返回类型str；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
# - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
# - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
def _ddb_date_literal(value: date) -> str:
    # 条件门禁：判断`not isinstance(value, date)`，条件为真时进入受保护分支。
    # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
    # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
    # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
    if not isinstance(value, date):
        # 错误阻断：抛出`DataContractError('DolphinDB日期必须是date。')`并停止当前正常路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
        # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
        raise DataContractError("DolphinDB日期必须是date。")
    # 结果返回：把`value.strftime('%Y.%m.%d')`交给调用方并结束当前函数。
    # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return value.strftime("%Y.%m.%d")


# 函数_safe_identifier：执行_safe_identifier逻辑。
# - 参数value：类型str；进入函数后按合同参与校验、筛选、计算或路由。
# - 参数field_name：类型str；进入函数后按合同参与校验、筛选、计算或路由。
# - 输出：返回类型str；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
# - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
# - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
def _safe_identifier(value: str, field_name: str) -> str:
    # 变量更新：计算并保存text，右侧逻辑为`_require_text(value, field_name)`。
    # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
    # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
    text = _require_text(value, field_name)
    # 条件门禁：判断`not all((char.isalnum() or char == '_' for char in text))`，条件为真时进入受保护分支。
    # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
    # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
    # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
    if not all(char.isalnum() or char == "_" for char in text):
        # 错误阻断：抛出`DataContractError(f'{field_name}不是安全标识符。')`并停止当前正常路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
        # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
        raise DataContractError(f"{field_name}不是安全标识符。")
    # 结果返回：把`text`交给调用方并结束当前函数。
    # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return text


# 函数_safe_database_uri：执行_safe_database_uri逻辑。
# - 参数value：类型str；进入函数后按合同参与校验、筛选、计算或路由。
# - 输出：返回类型str；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
# - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
# - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
def _safe_database_uri(value: str) -> str:
    # 变量更新：计算并保存text，右侧逻辑为`_require_text(value, 'database_uri')`。
    # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
    # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
    text = _require_text(value, "database_uri")
    # 条件门禁：判断`'"' in text or '\n' in text or '\r' in text`，条件为真时进入受保护分支。
    # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
    # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
    # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
    if '"' in text or "\n" in text or "\r" in text:
        # 错误阻断：抛出`DataContractError('database_uri包含不安全字符。')`并停止当前正常路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
        # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
        raise DataContractError("database_uri包含不安全字符。")
    # 结果返回：把`text`交给调用方并结束当前函数。
    # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return text


# 函数_safe_filter：执行_safe_filter逻辑。
# - 参数value：类型str | None；进入函数后按合同参与校验、筛选、计算或路由。
# - 输出：返回类型str | None；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
# - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
# - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
def _safe_filter(value: str | None) -> str | None:
    # 条件门禁：判断`value is None`，条件为真时进入受保护分支。
    # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
    # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
    # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
    if value is None:
        # 结果返回：把`None`交给调用方并结束当前函数。
        # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return None
    # 变量更新：计算并保存text，右侧逻辑为`_require_text(value, 'dataset_filter')`。
    # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
    # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
    text = _require_text(value, "dataset_filter")
    # 变量更新：计算并保存forbidden，右侧逻辑为`(';', '\n', '\r', 'drop ', 'delete ', 'update ', 'insert ')`。
    # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
    # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
    forbidden = (";", "\n", "\r", "drop ", "delete ", "update ", "insert ")
    # 变量更新：计算并保存lowered，右侧逻辑为`text.lower()`。
    # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
    # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
    lowered = text.lower()
    # 条件门禁：判断`any((token in lowered for token in forbidden))`，条件为真时进入受保护分支。
    # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
    # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
    # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
    if any(token in lowered for token in forbidden):
        # 错误阻断：抛出`DataContractError('dataset_filter包含不安全内容。')`并停止当前正常路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
        # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
        raise DataContractError("dataset_filter包含不安全内容。")
    # 结果返回：把`text`交给调用方并结束当前函数。
    # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return text


# 类RealFeatureDatasetPlan：封装RealFeatureDatasetPlan相关状态、字段与行为。
# - 继承边界：基类为object；类体包含约6个字段或常量、1个方法。
# - 数据变化：类定义本身不执行隐式I/O，实例只在构造、校验或显式方法调用时产生受控状态。
# - 实操示例：调用方先构造该类型，再由方法完成校验、证据组合、路由或结果导出。
# - 为什么这样写：强类型边界能把相关不变量集中管理，减少字典键拼写、状态漂移和跨模块耦合。
@dataclass(frozen=True, slots=True)
class RealFeatureDatasetPlan:
    # 字段或变量dataset_id：声明类型str，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    dataset_id: str
    # 字段或变量canonical_object：声明类型str，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    canonical_object: str
    # 字段或变量selector_mode：声明类型str，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    selector_mode: str
    # 字段或变量selector_limit：声明类型int，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    selector_limit: int
    # 字段或变量minimum_result_count：声明类型int，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    minimum_result_count: int
    # 字段或变量limit_per_selector：声明类型int，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    limit_per_selector: int

    # 函数__post_init__：执行__post_init__逻辑。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态、模块常量或封装依赖。
    # - 输出：返回类型None；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
    # - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
    # - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
    def __post_init__(self) -> None:
        # API或函数调用：执行`object.__setattr__`，完整调用片段为`object.__setattr__(self, 'dataset_id', _require_text(self.dataset_id, 'dataset_id'))`。
        # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
        # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
        # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
        object.__setattr__(
            self,
            "dataset_id",
            _require_text(self.dataset_id, "dataset_id"),
        )
        # API或函数调用：执行`object.__setattr__`，完整调用片段为`object.__setattr__(self, 'canonical_object', _require_text(self.canonical_object, 'canonical_object…`。
        # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
        # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
        # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
        object.__setattr__(
            self,
            "canonical_object",
            _require_text(
                self.canonical_object,
                "canonical_object",
            ),
        )
        # 变量更新：计算并保存mode，右侧逻辑为`_require_text(self.selector_mode, 'selector_mode').upper()`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        mode = _require_text(
            self.selector_mode,
            "selector_mode",
        ).upper()
        # 条件门禁：判断`mode not in {INSTRUMENT_SELECTOR_MODE, ENTITY_SELECTOR_MODE}`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if mode not in {
            INSTRUMENT_SELECTOR_MODE,
            ENTITY_SELECTOR_MODE,
        }:
            # 错误阻断：抛出`DataContractError('selector_mode不受支持。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
            raise DataContractError("selector_mode不受支持。")
        # API或函数调用：执行`object.__setattr__`，完整调用片段为`object.__setattr__(self, 'selector_mode', mode)`。
        # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
        # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
        # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
        object.__setattr__(self, "selector_mode", mode)
        # API或函数调用：执行`object.__setattr__`，完整调用片段为`object.__setattr__(self, 'selector_limit', _require_positive_int(self.selector_limit, 'selector_lim…`。
        # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
        # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
        # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
        object.__setattr__(
            self,
            "selector_limit",
            _require_positive_int(
                self.selector_limit,
                "selector_limit",
            ),
        )
        # API或函数调用：执行`object.__setattr__`，完整调用片段为`object.__setattr__(self, 'minimum_result_count', _require_positive_int(self.minimum_result_count, '…`。
        # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
        # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
        # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
        object.__setattr__(
            self,
            "minimum_result_count",
            _require_positive_int(
                self.minimum_result_count,
                "minimum_result_count",
            ),
        )
        # API或函数调用：执行`object.__setattr__`，完整调用片段为`object.__setattr__(self, 'limit_per_selector', _require_positive_int(self.limit_per_selector, 'limi…`。
        # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
        # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
        # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
        object.__setattr__(
            self,
            "limit_per_selector",
            _require_positive_int(
                self.limit_per_selector,
                "limit_per_selector",
            ),
        )
        # 条件门禁：判断`self.limit_per_selector > 5000`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if self.limit_per_selector > 5_000:
            # 错误阻断：抛出`DataContractError('limit_per_selector不能超过5000。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
            raise DataContractError(
                "limit_per_selector不能超过5000。"
            )


# 类RealFeatureAcceptancePlan：封装RealFeatureAcceptancePlan相关状态、字段与行为。
# - 继承边界：基类为object；类体包含约18个字段或常量、2个方法。
# - 数据变化：类定义本身不执行隐式I/O，实例只在构造、校验或显式方法调用时产生受控状态。
# - 实操示例：调用方先构造该类型，再由方法完成校验、证据组合、路由或结果导出。
# - 为什么这样写：强类型边界能把相关不变量集中管理，减少字典键拼写、状态漂移和跨模块耦合。
@dataclass(frozen=True, slots=True)
class RealFeatureAcceptancePlan:
    # 字段或变量contract_version：声明类型str，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    contract_version: str
    # 字段或变量task_id：声明类型str，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    task_id: str
    # 字段或变量mode：声明类型str，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    mode: str
    # 字段或变量as_of_date：声明类型date，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    as_of_date: date
    # 字段或变量external_evidence_config：声明类型str，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    external_evidence_config: str
    # 字段或变量readiness_policy：声明类型str，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    readiness_policy: str
    # 字段或变量evidence_rules：声明类型str，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    evidence_rules: str
    # 字段或变量market_state_input_contract：声明类型str，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    market_state_input_contract: str
    # 字段或变量market_state_feature_spec：声明类型str，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    market_state_feature_spec: str
    # 字段或变量required_datasets：声明类型tuple[RealFeatureDatasetPlan, ...]，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    required_datasets: tuple[RealFeatureDatasetPlan, ...]
    # 字段或变量candidate_dataset_id：声明类型str，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    candidate_dataset_id: str
    # 字段或变量candidate_date_row_scan_limit：声明类型int，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    candidate_date_row_scan_limit: int
    # 字段或变量maximum_candidate_dates_to_check：声明类型int，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    maximum_candidate_dates_to_check: int
    # 字段或变量common_date_policy：声明类型str，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    common_date_policy: str
    # 字段或变量universe_scope：声明类型str，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    universe_scope: str
    # 字段或变量selector_order：声明类型str，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    selector_order: str
    # 字段或变量claim_full_market_coverage：声明类型bool，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    claim_full_market_coverage: bool
    # 字段或变量acceptance_invariants：声明类型Mapping[str, Any]，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    acceptance_invariants: Mapping[str, Any]

    # 函数__post_init__：执行__post_init__逻辑。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态、模块常量或封装依赖。
    # - 输出：返回类型None；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
    # - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
    # - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
    def __post_init__(self) -> None:
        # 迭代处理：依次从`('contract_version', 'task_id', 'mode', 'external_evidence_config', 'readiness_policy', 'evidence_r…`读取元素，并绑定到`field_name`。
        # - 维度变化：每轮处理一个记录、字段、证据或配置项，可能向列表、字典或累计统计增加一项。
        # - 为什么这样写：显式逐项处理便于保留顺序、定位坏数据，并对每个实体执行同一合同。
        for field_name in (
            "contract_version",
            "task_id",
            "mode",
            "external_evidence_config",
            "readiness_policy",
            "evidence_rules",
            "market_state_input_contract",
            "market_state_feature_spec",
            "candidate_dataset_id",
            "common_date_policy",
            "universe_scope",
            "selector_order",
        ):
            # API或函数调用：执行`object.__setattr__`，完整调用片段为`object.__setattr__(self, field_name, _require_text(getattr(self, field_name), field_name))`。
            # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
            # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
            # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
            object.__setattr__(
                self,
                field_name,
                _require_text(
                    getattr(self, field_name),
                    field_name,
                ),
            )
        # 条件门禁：判断`self.contract_version != REAL_FEATURE_ACCEPTANCE_PLAN_VERSION`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if self.contract_version != REAL_FEATURE_ACCEPTANCE_PLAN_VERSION:
            # 错误阻断：抛出`DataContractError('TASK_019C验收计划版本不兼容。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
            raise DataContractError("TASK_019C验收计划版本不兼容。")
        # 条件门禁：判断`self.task_id != 'TASK_019C'`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if self.task_id != "TASK_019C":
            # 错误阻断：抛出`DataContractError('TASK_019C验收计划task_id异常。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
            raise DataContractError("TASK_019C验收计划task_id异常。")
        # 条件门禁：判断`self.mode != REAL_FEATURE_ACCEPTANCE_MODE`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if self.mode != REAL_FEATURE_ACCEPTANCE_MODE:
            # 错误阻断：抛出`DataContractError('TASK_019C验收模式异常。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
            raise DataContractError("TASK_019C验收模式异常。")
        # 条件门禁：判断`not isinstance(self.as_of_date, date)`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if not isinstance(self.as_of_date, date):
            # 错误阻断：抛出`DataContractError('as_of_date必须是date。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
            raise DataContractError("as_of_date必须是date。")
        # 条件门禁：判断`len(self.required_datasets) != 2`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if len(self.required_datasets) != 2:
            # 错误阻断：抛出`DataContractError('TASK_019C必须且只能登记两个必需数据集。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
            raise DataContractError("TASK_019C必须且只能登记两个必需数据集。")
        # 变量更新：计算并保存ids，右侧逻辑为`{item.dataset_id for item in self.required_datasets}`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        ids = {item.dataset_id for item in self.required_datasets}
        # 条件门禁：判断`ids != {'a_stock_daily_k', 'hy'}`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if ids != {"a_stock_daily_k", "hy"}:
            # 错误阻断：抛出`DataContractError('TASK_019C必需数据集必须是日K和行业快照。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
            raise DataContractError("TASK_019C必需数据集必须是日K和行业快照。")
        # 条件门禁：判断`self.candidate_dataset_id != 'hy'`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if self.candidate_dataset_id != "hy":
            # 错误阻断：抛出`DataContractError('共同日期候选必须来自hy。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
            raise DataContractError("共同日期候选必须来自hy。")
        # API或函数调用：执行`object.__setattr__`，完整调用片段为`object.__setattr__(self, 'candidate_date_row_scan_limit', _require_positive_int(self.candidate_date…`。
        # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
        # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
        # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
        object.__setattr__(
            self,
            "candidate_date_row_scan_limit",
            _require_positive_int(
                self.candidate_date_row_scan_limit,
                "candidate_date_row_scan_limit",
            ),
        )
        # API或函数调用：执行`object.__setattr__`，完整调用片段为`object.__setattr__(self, 'maximum_candidate_dates_to_check', _require_positive_int(self.maximum_can…`。
        # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
        # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
        # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
        object.__setattr__(
            self,
            "maximum_candidate_dates_to_check",
            _require_positive_int(
                self.maximum_candidate_dates_to_check,
                "maximum_candidate_dates_to_check",
            ),
        )
        # 条件门禁：判断`self.common_date_policy != 'LATEST_COMMON_TRADE_DATE'`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if self.common_date_policy != "LATEST_COMMON_TRADE_DATE":
            # 错误阻断：抛出`DataContractError('共同日期政策异常。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
            raise DataContractError("共同日期政策异常。")
        # 条件门禁：判断`self.universe_scope != REAL_FEATURE_ACCEPTANCE_UNIVERSE_SCOPE`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if self.universe_scope != REAL_FEATURE_ACCEPTANCE_UNIVERSE_SCOPE:
            # 错误阻断：抛出`DataContractError('验收证券集合范围异常。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
            raise DataContractError("验收证券集合范围异常。")
        # 条件门禁：判断`self.selector_order != 'SOURCE_ENTITY_ID_ASC'`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if self.selector_order != "SOURCE_ENTITY_ID_ASC":
            # 错误阻断：抛出`DataContractError('选择器排序政策异常。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
            raise DataContractError("选择器排序政策异常。")
        # 条件门禁：判断`self.claim_full_market_coverage`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if self.claim_full_market_coverage:
            # 错误阻断：抛出`DataContractError('TASK_019C验收集合不得声明全市场覆盖。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
            raise DataContractError(
                "TASK_019C验收集合不得声明全市场覆盖。"
            )
        # 条件门禁：判断`not isinstance(self.acceptance_invariants, Mapping)`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if not isinstance(self.acceptance_invariants, Mapping):
            # 错误阻断：抛出`DataContractError('acceptance_invariants必须是对象。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
            raise DataContractError("acceptance_invariants必须是对象。")

    # 函数dataset：执行dataset逻辑。
    # - 参数dataset_id：类型str；进入函数后按合同参与校验、筛选、计算或路由。
    # - 输出：返回类型RealFeatureDatasetPlan；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
    # - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
    # - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
    def dataset(self, dataset_id: str) -> RealFeatureDatasetPlan:
        # 变量更新：计算并保存key，右侧逻辑为`_require_text(dataset_id, 'dataset_id')`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        key = _require_text(dataset_id, "dataset_id")
        # 迭代处理：依次从`self.required_datasets`读取元素，并绑定到`item`。
        # - 维度变化：每轮处理一个记录、字段、证据或配置项，可能向列表、字典或累计统计增加一项。
        # - 为什么这样写：显式逐项处理便于保留顺序、定位坏数据，并对每个实体执行同一合同。
        for item in self.required_datasets:
            # 条件门禁：判断`item.dataset_id == key`，条件为真时进入受保护分支。
            # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
            # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
            # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
            if item.dataset_id == key:
                # 结果返回：把`item`交给调用方并结束当前函数。
                # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
                # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
                return item
        # 错误阻断：抛出`DataContractError(f'验收计划未登记数据集：{key}')`并停止当前正常路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
        # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
        raise DataContractError(f"验收计划未登记数据集：{key}")


# 类ReadonlySourceDescriptor：封装ReadonlySourceDescriptor相关状态、字段与行为。
# - 继承边界：基类为object；类体包含约6个字段或常量、2个方法。
# - 数据变化：类定义本身不执行隐式I/O，实例只在构造、校验或显式方法调用时产生受控状态。
# - 实操示例：调用方先构造该类型，再由方法完成校验、证据组合、路由或结果导出。
# - 为什么这样写：强类型边界能把相关不变量集中管理，减少字典键拼写、状态漂移和跨模块耦合。
@dataclass(frozen=True, slots=True)
class ReadonlySourceDescriptor:
    # 字段或变量dataset_id：声明类型str，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    dataset_id: str
    # 字段或变量database_uri：声明类型str，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    database_uri: str
    # 字段或变量table_name：声明类型str，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    table_name: str
    # 字段或变量entity_field：声明类型str，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    entity_field: str
    # 字段或变量date_field：声明类型str，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    date_field: str
    # 字段或变量dataset_filter：声明类型str | None，初始逻辑为`None`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    dataset_filter: str | None = None

    # 函数__post_init__：执行__post_init__逻辑。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态、模块常量或封装依赖。
    # - 输出：返回类型None；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
    # - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
    # - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
    def __post_init__(self) -> None:
        # API或函数调用：执行`object.__setattr__`，完整调用片段为`object.__setattr__(self, 'dataset_id', _require_text(self.dataset_id, 'dataset_id'))`。
        # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
        # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
        # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
        object.__setattr__(
            self,
            "dataset_id",
            _require_text(self.dataset_id, "dataset_id"),
        )
        # API或函数调用：执行`object.__setattr__`，完整调用片段为`object.__setattr__(self, 'database_uri', _safe_database_uri(self.database_uri))`。
        # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
        # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
        # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
        object.__setattr__(
            self,
            "database_uri",
            _safe_database_uri(self.database_uri),
        )
        # API或函数调用：执行`object.__setattr__`，完整调用片段为`object.__setattr__(self, 'table_name', _safe_identifier(self.table_name, 'table_name'))`。
        # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
        # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
        # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
        object.__setattr__(
            self,
            "table_name",
            _safe_identifier(self.table_name, "table_name"),
        )
        # API或函数调用：执行`object.__setattr__`，完整调用片段为`object.__setattr__(self, 'entity_field', _safe_identifier(self.entity_field, 'entity_field'))`。
        # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
        # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
        # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
        object.__setattr__(
            self,
            "entity_field",
            _safe_identifier(self.entity_field, "entity_field"),
        )
        # API或函数调用：执行`object.__setattr__`，完整调用片段为`object.__setattr__(self, 'date_field', _safe_identifier(self.date_field, 'date_field'))`。
        # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
        # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
        # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
        object.__setattr__(
            self,
            "date_field",
            _safe_identifier(self.date_field, "date_field"),
        )
        # API或函数调用：执行`object.__setattr__`，完整调用片段为`object.__setattr__(self, 'dataset_filter', _safe_filter(self.dataset_filter))`。
        # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
        # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
        # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
        object.__setattr__(
            self,
            "dataset_filter",
            _safe_filter(self.dataset_filter),
        )

    # 函数table_ref：执行table_ref逻辑。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态、模块常量或封装依赖。
    # - 输出：返回类型str；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
    # - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
    # - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
    @property
    def table_ref(self) -> str:
        # 结果返回：把`f'loadTable("{self.database_uri}", `{self.table_name})'`交给调用方并结束当前函数。
        # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return (
            f'loadTable("{self.database_uri}", '
            f'`{self.table_name})'
        )


# 函数load_real_feature_acceptance_plan：执行load_real_feature_acceptance_plan逻辑。
# - 参数path：类型str | Path；进入函数后按合同参与校验、筛选、计算或路由。
# - 输出：返回类型RealFeatureAcceptancePlan；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
# - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
# - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
def load_real_feature_acceptance_plan(
    path: str | Path,
) -> RealFeatureAcceptancePlan:
    # 变量更新：计算并保存plan_path，右侧逻辑为`Path(path)`。
    # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
    # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
    plan_path = Path(path)
    # 异常边界：执行可能失败的解析、转换、文件读取或外部调用，并在后续分支转换为项目统一错误。
    # - 数据变化：成功路径产生正常结果；失败路径保留原异常作为cause、降级为缺失值或记录明确问题。
    # - 为什么这样写：上层只需处理稳定的DataContractError或受控结果，不依赖第三方异常实现细节。
    try:
        # 变量更新：计算并保存raw，右侧逻辑为`json.loads(plan_path.read_text(encoding='utf-8'))`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        raw = json.loads(plan_path.read_text(encoding="utf-8"))
    # 异常转换：捕获(OSError, json.JSONDecodeError)，保存上下文并执行统一错误、回退或忽略策略。
    # - 数据变化：异常路径不返回未校验的半成品；必要时把失败原因写入issues、warnings或异常链。
    # - 为什么这样写：明确捕获范围可避免吞掉程序错误，同时让调用方获得稳定且可审计的失败语义。
    except (OSError, json.JSONDecodeError) as exc:
        # 错误阻断：抛出`DataContractError(f'无法加载TASK_019C验收计划：{plan_path}')`并停止当前正常路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
        # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
        raise DataContractError(
            f"无法加载TASK_019C验收计划：{plan_path}"
        ) from exc
    # 条件门禁：判断`not isinstance(raw, dict)`，条件为真时进入受保护分支。
    # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
    # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
    # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
    if not isinstance(raw, dict):
        # 错误阻断：抛出`DataContractError('TASK_019C验收计划根节点必须是对象。')`并停止当前正常路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
        # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
        raise DataContractError("TASK_019C验收计划根节点必须是对象。")
    # 变量更新：计算并保存discovery，右侧逻辑为`raw['common_date_discovery']`。
    # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
    # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
    discovery = raw["common_date_discovery"]
    # 变量更新：计算并保存universe，右侧逻辑为`raw['universe_policy']`。
    # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
    # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
    universe = raw["universe_policy"]
    # 结果返回：把`RealFeatureAcceptancePlan(contract_version=str(raw['contract_version']), task_id=str(raw['task_id']…`交给调用方并结束当前函数。
    # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return RealFeatureAcceptancePlan(
        contract_version=str(raw["contract_version"]),
        task_id=str(raw["task_id"]),
        mode=str(raw["mode"]),
        as_of_date=_coerce_date(raw["as_of_date"]),
        external_evidence_config=str(
            raw["external_evidence_config"]
        ),
        readiness_policy=str(raw["readiness_policy"]),
        evidence_rules=str(raw["evidence_rules"]),
        market_state_input_contract=str(
            raw["market_state_input_contract"]
        ),
        market_state_feature_spec=str(
            raw["market_state_feature_spec"]
        ),
        required_datasets=tuple(
            RealFeatureDatasetPlan(
                dataset_id=str(item["dataset_id"]),
                canonical_object=str(item["canonical_object"]),
                selector_mode=str(item["selector_mode"]),
                selector_limit=int(item["selector_limit"]),
                minimum_result_count=int(
                    item["minimum_result_count"]
                ),
                limit_per_selector=int(
                    item["limit_per_selector"]
                ),
            )
            for item in raw["required_datasets"]
        ),
        candidate_dataset_id=str(
            discovery["candidate_dataset_id"]
        ),
        candidate_date_row_scan_limit=int(
            discovery["candidate_date_row_scan_limit"]
        ),
        maximum_candidate_dates_to_check=int(
            discovery["maximum_candidate_dates_to_check"]
        ),
        common_date_policy=str(discovery["policy"]),
        universe_scope=str(universe["scope"]),
        selector_order=str(universe["selector_order"]),
        claim_full_market_coverage=bool(
            universe["claim_full_market_coverage"]
        ),
        acceptance_invariants=dict(raw["acceptance_invariants"]),
    )


# 函数build_recent_date_rows_query：执行build_recent_date_rows_query逻辑。
# - 参数source：类型ReadonlySourceDescriptor；进入函数后按合同参与校验、筛选、计算或路由。
# - 参数row_limit：类型int；进入函数后按合同参与校验、筛选、计算或路由。
# - 输出：返回类型str；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
# - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
# - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
def build_recent_date_rows_query(
    source: ReadonlySourceDescriptor,
    row_limit: int,
) -> str:
    # 变量更新：计算并保存limit，右侧逻辑为`_require_positive_int(row_limit, 'row_limit')`。
    # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
    # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
    limit = _require_positive_int(row_limit, "row_limit")
    # 变量更新：计算并保存where，右侧逻辑为`f' where {source.dataset_filter}' if source.dataset_filter else ''`。
    # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
    # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
    where = (
        f" where {source.dataset_filter}"
        if source.dataset_filter
        else ""
    )
    # 结果返回：把`f'select top {limit} {source.date_field} from {source.table_ref}{where} order by {source.date_field…`交给调用方并结束当前函数。
    # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return (
        f"select top {limit} {source.date_field} "
        f"from {source.table_ref}"
        f"{where} "
        f"order by {source.date_field} desc"
    )


# 函数build_date_presence_query：执行build_date_presence_query逻辑。
# - 参数source：类型ReadonlySourceDescriptor；进入函数后按合同参与校验、筛选、计算或路由。
# - 参数target_date：类型date；进入函数后按合同参与校验、筛选、计算或路由。
# - 输出：返回类型str；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
# - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
# - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
def build_date_presence_query(
    source: ReadonlySourceDescriptor,
    target_date: date,
) -> str:
    # 变量更新：计算并保存where_parts，右侧逻辑为`[f'{source.date_field} = {_ddb_date_literal(target_date)}']`。
    # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
    # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
    where_parts = [
        f"{source.date_field} = {_ddb_date_literal(target_date)}"
    ]
    # 条件门禁：判断`source.dataset_filter`，条件为真时进入受保护分支。
    # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
    # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
    # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
    if source.dataset_filter:
        # API或函数调用：执行`where_parts.insert`，完整调用片段为`where_parts.insert(0, source.dataset_filter)`。
        # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
        # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
        # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
        where_parts.insert(0, source.dataset_filter)
    # 结果返回：把`f"select top 1 {source.date_field} from {source.table_ref} where {' and '.join(where_parts)}"`交给调用方并结束当前函数。
    # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return (
        f"select top 1 {source.date_field} "
        f"from {source.table_ref} "
        f"where {' and '.join(where_parts)}"
    )


# 函数build_selector_rows_query：执行build_selector_rows_query逻辑。
# - 参数source：类型ReadonlySourceDescriptor；进入函数后按合同参与校验、筛选、计算或路由。
# - 参数target_date：类型date；进入函数后按合同参与校验、筛选、计算或路由。
# - 参数selector_limit：类型int；进入函数后按合同参与校验、筛选、计算或路由。
# - 输出：返回类型str；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
# - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
# - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
def build_selector_rows_query(
    source: ReadonlySourceDescriptor,
    target_date: date,
    selector_limit: int,
) -> str:
    # 变量更新：计算并保存limit，右侧逻辑为`_require_positive_int(selector_limit, 'selector_limit')`。
    # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
    # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
    limit = _require_positive_int(
        selector_limit,
        "selector_limit",
    )
    # 变量更新：计算并保存where_parts，右侧逻辑为`[f'{source.date_field} = {_ddb_date_literal(target_date)}']`。
    # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
    # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
    where_parts = [
        f"{source.date_field} = {_ddb_date_literal(target_date)}"
    ]
    # 条件门禁：判断`source.dataset_filter`，条件为真时进入受保护分支。
    # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
    # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
    # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
    if source.dataset_filter:
        # API或函数调用：执行`where_parts.insert`，完整调用片段为`where_parts.insert(0, source.dataset_filter)`。
        # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
        # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
        # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
        where_parts.insert(0, source.dataset_filter)
    # 结果返回：把`f"select top {limit} {source.entity_field} from {source.table_ref} where {' and '.join(where_parts)…`交给调用方并结束当前函数。
    # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return (
        f"select top {limit} {source.entity_field} "
        f"from {source.table_ref} "
        f"where {' and '.join(where_parts)} "
        f"order by {source.entity_field}"
    )


# 函数assert_readonly_query：执行assert_readonly_query逻辑。
# - 参数script：类型str；进入函数后按合同参与校验、筛选、计算或路由。
# - 输出：返回类型None；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
# - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
# - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
def assert_readonly_query(script: str) -> None:
    # 变量更新：计算并保存text，右侧逻辑为`_require_text(script, 'script')`。
    # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
    # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
    text = _require_text(script, "script")
    # 变量更新：计算并保存lowered，右侧逻辑为`' '.join(text.lower().split())`。
    # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
    # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
    lowered = " ".join(text.lower().split())
    # 条件门禁：判断`not lowered.startswith('select ')`，条件为真时进入受保护分支。
    # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
    # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
    # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
    if not lowered.startswith("select "):
        # 错误阻断：抛出`DataContractError('TASK_019C只允许SELECT查询。')`并停止当前正常路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
        # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
        raise DataContractError("TASK_019C只允许SELECT查询。")
    # 变量更新：计算并保存forbidden，右侧逻辑为`(' insert ', ' update ', ' delete ', ' drop ', ' create ', ' alter ', ' append!', ' tableinsert', '…`。
    # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
    # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
    forbidden = (
        " insert ",
        " update ",
        " delete ",
        " drop ",
        " create ",
        " alter ",
        " append!",
        " tableinsert",
        " save",
        " write",
    )
    # 变量更新：计算并保存padded，右侧逻辑为`f' {lowered} '`。
    # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
    # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
    padded = f" {lowered} "
    # 条件门禁：判断`any((token in padded for token in forbidden))`，条件为真时进入受保护分支。
    # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
    # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
    # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
    if any(token in padded for token in forbidden):
        # 错误阻断：抛出`DataContractError('查询包含潜在写操作。')`并停止当前正常路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
        # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
        raise DataContractError("查询包含潜在写操作。")


# 函数unique_dates_from_rows：执行unique_dates_from_rows逻辑。
# - 参数rows：类型Sequence[Mapping[str, Any]]；进入函数后按合同参与校验、筛选、计算或路由。
# - 参数date_field：类型str；进入函数后按合同参与校验、筛选、计算或路由。
# - 参数maximum_count：类型int；进入函数后按合同参与校验、筛选、计算或路由。
# - 输出：返回类型tuple[date, ...]；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
# - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
# - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
def unique_dates_from_rows(
    rows: Sequence[Mapping[str, Any]],
    date_field: str,
    maximum_count: int,
) -> tuple[date, ...]:
    # 变量更新：计算并保存field，右侧逻辑为`_safe_identifier(date_field, 'date_field')`。
    # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
    # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
    field = _safe_identifier(date_field, "date_field")
    # 变量更新：计算并保存maximum，右侧逻辑为`_require_positive_int(maximum_count, 'maximum_count')`。
    # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
    # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
    maximum = _require_positive_int(
        maximum_count,
        "maximum_count",
    )
    # 字段或变量values：声明类型list[date]，初始逻辑为`[]`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    values: list[date] = []
    # 字段或变量seen：声明类型set[date]，初始逻辑为`set()`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    seen: set[date] = set()
    # 迭代处理：依次从`rows`读取元素，并绑定到`row`。
    # - 维度变化：每轮处理一个记录、字段、证据或配置项，可能向列表、字典或累计统计增加一项。
    # - 为什么这样写：显式逐项处理便于保留顺序、定位坏数据，并对每个实体执行同一合同。
    for row in rows:
        # 条件门禁：判断`field not in row or row[field] is None`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if field not in row or row[field] is None:
            # 当前元素跳过：本轮记录不满足处理条件，直接进入下一轮。
            # - 数据变化：本轮后续代码不执行，已累计的其他结果保持不变。
            # - 为什么这样写：早跳过可以降低嵌套层级，并清楚隔离无效或不适用数据。
            continue
        # 变量更新：计算并保存value，右侧逻辑为`_coerce_date(row[field])`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        value = _coerce_date(row[field])
        # 条件门禁：判断`value in seen`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if value in seen:
            # 当前元素跳过：本轮记录不满足处理条件，直接进入下一轮。
            # - 数据变化：本轮后续代码不执行，已累计的其他结果保持不变。
            # - 为什么这样写：早跳过可以降低嵌套层级，并清楚隔离无效或不适用数据。
            continue
        # API或函数调用：执行`seen.add`，完整调用片段为`seen.add(value)`。
        # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
        # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
        # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
        seen.add(value)
        # API或函数调用：执行`values.append`，完整调用片段为`values.append(value)`。
        # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
        # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
        # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
        values.append(value)
        # 条件门禁：判断`len(values) >= maximum`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if len(values) >= maximum:
            # 循环提前结束：当前条件已满足，不再处理剩余元素。
            # - 数据变化：保留已累计结果，并把控制流移动到循环之后。
            # - 为什么这样写：在找到唯一结果或达到安全上限后停止，可减少不必要计算。
            break
    # 结果返回：把`tuple(sorted(values, reverse=True))`交给调用方并结束当前函数。
    # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return tuple(sorted(values, reverse=True))


# 函数unique_selectors_from_rows：执行unique_selectors_from_rows逻辑。
# - 参数rows：类型Sequence[Mapping[str, Any]]；进入函数后按合同参与校验、筛选、计算或路由。
# - 参数entity_field：类型str；进入函数后按合同参与校验、筛选、计算或路由。
# - 参数maximum_count：类型int；进入函数后按合同参与校验、筛选、计算或路由。
# - 输出：返回类型tuple[str, ...]；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
# - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
# - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
def unique_selectors_from_rows(
    rows: Sequence[Mapping[str, Any]],
    entity_field: str,
    maximum_count: int,
) -> tuple[str, ...]:
    # 变量更新：计算并保存field，右侧逻辑为`_safe_identifier(entity_field, 'entity_field')`。
    # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
    # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
    field = _safe_identifier(entity_field, "entity_field")
    # 变量更新：计算并保存maximum，右侧逻辑为`_require_positive_int(maximum_count, 'maximum_count')`。
    # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
    # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
    maximum = _require_positive_int(
        maximum_count,
        "maximum_count",
    )
    # 字段或变量values：声明类型list[str]，初始逻辑为`[]`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    values: list[str] = []
    # 字段或变量seen：声明类型set[str]，初始逻辑为`set()`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    seen: set[str] = set()
    # 迭代处理：依次从`rows`读取元素，并绑定到`row`。
    # - 维度变化：每轮处理一个记录、字段、证据或配置项，可能向列表、字典或累计统计增加一项。
    # - 为什么这样写：显式逐项处理便于保留顺序、定位坏数据，并对每个实体执行同一合同。
    for row in rows:
        # 变量更新：计算并保存raw，右侧逻辑为`row.get(field)`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        raw = row.get(field)
        # 条件门禁：判断`raw is None`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if raw is None:
            # 当前元素跳过：本轮记录不满足处理条件，直接进入下一轮。
            # - 数据变化：本轮后续代码不执行，已累计的其他结果保持不变。
            # - 为什么这样写：早跳过可以降低嵌套层级，并清楚隔离无效或不适用数据。
            continue
        # 变量更新：计算并保存text，右侧逻辑为`str(raw).strip()`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        text = str(raw).strip()
        # 条件门禁：判断`not text or text in seen`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if not text or text in seen:
            # 当前元素跳过：本轮记录不满足处理条件，直接进入下一轮。
            # - 数据变化：本轮后续代码不执行，已累计的其他结果保持不变。
            # - 为什么这样写：早跳过可以降低嵌套层级，并清楚隔离无效或不适用数据。
            continue
        # API或函数调用：执行`seen.add`，完整调用片段为`seen.add(text)`。
        # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
        # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
        # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
        seen.add(text)
        # API或函数调用：执行`values.append`，完整调用片段为`values.append(text)`。
        # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
        # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
        # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
        values.append(text)
        # 条件门禁：判断`len(values) >= maximum`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if len(values) >= maximum:
            # 循环提前结束：当前条件已满足，不再处理剩余元素。
            # - 数据变化：保留已累计结果，并把控制流移动到循环之后。
            # - 为什么这样写：在找到唯一结果或达到安全上限后停止，可减少不必要计算。
            break
    # 结果返回：把`tuple(values)`交给调用方并结束当前函数。
    # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return tuple(values)


# 函数build_feature_acceptance_query：执行build_feature_acceptance_query逻辑。
# - 参数dataset_plan：类型RealFeatureDatasetPlan；进入函数后按合同参与校验、筛选、计算或路由。
# - 参数selectors：类型Sequence[str]；进入函数后按合同参与校验、筛选、计算或路由。
# - 参数common_date：类型date；进入函数后按合同参与校验、筛选、计算或路由。
# - 参数as_of_date：类型date；进入函数后按合同参与校验、筛选、计算或路由。
# - 输出：返回类型StandardDataQuery；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
# - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
# - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
def build_feature_acceptance_query(
    dataset_plan: RealFeatureDatasetPlan,
    selectors: Sequence[str],
    common_date: date,
    as_of_date: date,
) -> StandardDataQuery:
    # 变量更新：计算并保存selector_values，右侧逻辑为`tuple((_require_text(value, 'selector') for value in selectors))`。
    # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
    # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
    selector_values = tuple(
        _require_text(value, "selector")
        for value in selectors
    )
    # 条件门禁：判断`not selector_values`，条件为真时进入受保护分支。
    # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
    # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
    # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
    if not selector_values:
        # 错误阻断：抛出`DataContractError('真实验收选择器不能为空。')`并停止当前正常路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
        # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
        raise DataContractError("真实验收选择器不能为空。")
    # 条件门禁：判断`len(selector_values) > dataset_plan.selector_limit`，条件为真时进入受保护分支。
    # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
    # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
    # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
    if len(selector_values) > dataset_plan.selector_limit:
        # 错误阻断：抛出`DataContractError('选择器数量超过验收计划限制。')`并停止当前正常路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
        # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
        raise DataContractError("选择器数量超过验收计划限制。")
    # 条件门禁：判断`common_date > as_of_date`，条件为真时进入受保护分支。
    # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
    # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
    # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
    if common_date > as_of_date:
        # 错误阻断：抛出`DataContractError('共同交易日不能晚于as_of_date。')`并停止当前正常路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
        # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
        raise DataContractError("共同交易日不能晚于as_of_date。")
    # 变量更新：计算并保存instrument_ids，右侧逻辑为`selector_values if dataset_plan.selector_mode == INSTRUMENT_SELECTOR_MODE else ()`。
    # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
    # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
    instrument_ids = (
        selector_values
        if dataset_plan.selector_mode
        == INSTRUMENT_SELECTOR_MODE
        else ()
    )
    # 变量更新：计算并保存entity_ids，右侧逻辑为`selector_values if dataset_plan.selector_mode == ENTITY_SELECTOR_MODE else ()`。
    # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
    # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
    entity_ids = (
        selector_values
        if dataset_plan.selector_mode
        == ENTITY_SELECTOR_MODE
        else ()
    )
    # 结果返回：把`StandardDataQuery(dataset_id=dataset_plan.dataset_id, canonical_object=dataset_plan.canonical_objec…`交给调用方并结束当前函数。
    # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return StandardDataQuery(
        dataset_id=dataset_plan.dataset_id,
        canonical_object=dataset_plan.canonical_object,
        instrument_ids=instrument_ids,
        entity_ids=entity_ids,
        start_date=common_date,
        end_date=common_date,
        as_of_date=as_of_date,
        usage=StandardDataUsage.CURRENT_SNAPSHOT_RESEARCH,
        limit_per_instrument=dataset_plan.limit_per_selector,
        include_source_extensions=True,
        include_quality_flags=True,
        include_lineage=True,
    )


# 函数validate_real_feature_acceptance_report：执行validate_real_feature_acceptance_report逻辑。
# - 参数report：类型Mapping[str, Any]；进入函数后按合同参与校验、筛选、计算或路由。
# - 参数plan：类型RealFeatureAcceptancePlan；进入函数后按合同参与校验、筛选、计算或路由。
# - 输出：返回类型tuple[str, ...]；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
# - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
# - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
def validate_real_feature_acceptance_report(
    report: Mapping[str, Any],
    plan: RealFeatureAcceptancePlan,
) -> tuple[str, ...]:
    # 字段或变量issues：声明类型list[str]，初始逻辑为`[]`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    issues: list[str] = []
    # 变量更新：计算并保存expected，右侧逻辑为`plan.acceptance_invariants`。
    # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
    # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
    expected = plan.acceptance_invariants

    # 变量更新：计算并保存checks，右侧逻辑为`((report.get('task_id') == plan.task_id, 'task_id'), (report.get('mode') == plan.mode, 'mode'), (in…`。
    # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
    # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
    checks = (
        (report.get("task_id") == plan.task_id, "task_id"),
        (report.get("mode") == plan.mode, "mode"),
        (
            int(report.get("required_dataset_count", -1))
            == int(expected["required_dataset_count"]),
            "required_dataset_count",
        ),
        (
            int(report.get("required_feature_family_count", -1))
            == int(expected["required_feature_family_count"]),
            "required_feature_family_count",
        ),
        (
            int(report.get("feature_definition_count", -1))
            == int(expected["feature_definition_count"]),
            "feature_definition_count",
        ),
        (
            int(report.get("generated_feature_count", -1))
            == int(expected["generated_feature_count"]),
            "generated_feature_count",
        ),
        (
            int(report.get("unique_source_query_id_count", -1))
            == int(expected["unique_source_query_id_count"]),
            "unique_source_query_id_count",
        ),
        (
            bool(report.get("database_connection_attempted"))
            is bool(expected["database_connection_attempted"]),
            "database_connection_attempted",
        ),
        (
            bool(report.get("database_readonly_query_mode"))
            is bool(expected["database_readonly_query_mode"]),
            "database_readonly_query_mode",
        ),
        (
            int(report.get("write_operation_count", -1))
            == int(expected["database_write_operation_count"]),
            "write_operation_count",
        ),
        (
            bool(report.get("manual_decision_allowed"))
            is bool(expected["manual_decision_allowed"]),
            "manual_decision_allowed",
        ),
        (
            bool(report.get("official_market_state_allowed"))
            is bool(expected["official_market_state_allowed"]),
            "official_market_state_allowed",
        ),
        (
            report.get("regime_label") is expected["regime_label"],
            "regime_label",
        ),
        (
            report.get("universe_scope") == plan.universe_scope,
            "universe_scope",
        ),
        (
            report.get("claim_full_market_coverage") is False,
            "claim_full_market_coverage",
        ),
        (
            report.get("input_assessment_status")
            in {"READY", "READY_WITH_WARNINGS"},
            "input_assessment_status",
        ),
        (
            report.get("feature_snapshot_status")
            in {"READY", "READY_WITH_WARNINGS"},
            "feature_snapshot_status",
        ),
        (
            bool(report.get("research_feature_build_allowed")),
            "research_feature_build_allowed",
        ),
        (
            bool(report.get("common_trade_date")),
            "common_trade_date",
        ),
    )
    # 迭代处理：依次从`checks`读取元素，并绑定到`passed, name`。
    # - 维度变化：每轮处理一个记录、字段、证据或配置项，可能向列表、字典或累计统计增加一项。
    # - 为什么这样写：显式逐项处理便于保留顺序、定位坏数据，并对每个实体执行同一合同。
    for passed, name in checks:
        # 条件门禁：判断`not passed`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if not passed:
            # API或函数调用：执行`issues.append`，完整调用片段为`issues.append(name)`。
            # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
            # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
            # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
            issues.append(name)

    # 变量更新：计算并保存query_summaries，右侧逻辑为`report.get('query_summaries', [])`。
    # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
    # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
    query_summaries = report.get("query_summaries", [])
    # 条件门禁：判断`not isinstance(query_summaries, list)`，条件为真时进入受保护分支。
    # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
    # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
    # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
    if not isinstance(query_summaries, list):
        # API或函数调用：执行`issues.append`，完整调用片段为`issues.append('query_summaries')`。
        # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
        # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
        # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
        issues.append("query_summaries")
    else:
        # 变量更新：计算并保存by_dataset，右侧逻辑为`{str(item.get('dataset_id')): item for item in query_summaries if isinstance(item, Mapping)}`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        by_dataset = {
            str(item.get("dataset_id")): item
            for item in query_summaries
            if isinstance(item, Mapping)
        }
        # 迭代处理：依次从`plan.required_datasets`读取元素，并绑定到`dataset_plan`。
        # - 维度变化：每轮处理一个记录、字段、证据或配置项，可能向列表、字典或累计统计增加一项。
        # - 为什么这样写：显式逐项处理便于保留顺序、定位坏数据，并对每个实体执行同一合同。
        for dataset_plan in plan.required_datasets:
            # 变量更新：计算并保存summary，右侧逻辑为`by_dataset.get(dataset_plan.dataset_id)`。
            # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
            # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
            summary = by_dataset.get(dataset_plan.dataset_id)
            # 条件门禁：判断`summary is None`，条件为真时进入受保护分支。
            # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
            # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
            # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
            if summary is None:
                # API或函数调用：执行`issues.append`，完整调用片段为`issues.append(f'query_summary:{dataset_plan.dataset_id}')`。
                # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
                # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
                # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
                issues.append(
                    f"query_summary:{dataset_plan.dataset_id}"
                )
                # 当前元素跳过：本轮记录不满足处理条件，直接进入下一轮。
                # - 数据变化：本轮后续代码不执行，已累计的其他结果保持不变。
                # - 为什么这样写：早跳过可以降低嵌套层级，并清楚隔离无效或不适用数据。
                continue
            # 条件门禁：判断`int(summary.get('result_count', -1)) < dataset_plan.minimum_result_count`，条件为真时进入受保护分支。
            # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
            # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
            # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
            if int(summary.get("result_count", -1)) < (
                dataset_plan.minimum_result_count
            ):
                # API或函数调用：执行`issues.append`，完整调用片段为`issues.append(f'minimum_result_count:{dataset_plan.dataset_id}')`。
                # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
                # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
                # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
                issues.append(
                    f"minimum_result_count:{dataset_plan.dataset_id}"
                )
            # 条件门禁：判断`bool(summary.get('blocks_downstream'))`，条件为真时进入受保护分支。
            # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
            # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
            # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
            if bool(summary.get("blocks_downstream")):
                # API或函数调用：执行`issues.append`，完整调用片段为`issues.append(f'query_blocked:{dataset_plan.dataset_id}')`。
                # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
                # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
                # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
                issues.append(
                    f"query_blocked:{dataset_plan.dataset_id}"
                )

    # 变量更新：计算并保存features，右侧逻辑为`report.get('features', [])`。
    # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
    # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
    features = report.get("features", [])
    # 条件门禁：判断`not isinstance(features, list)`，条件为真时进入受保护分支。
    # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
    # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
    # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
    if not isinstance(features, list):
        # API或函数调用：执行`issues.append`，完整调用片段为`issues.append('features')`。
        # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
        # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
        # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
        issues.append("features")
    else:
        # 变量更新：计算并保存feature_ids，右侧逻辑为`[str(item.get('feature_id')) for item in features if isinstance(item, Mapping)]`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        feature_ids = [
            str(item.get("feature_id"))
            for item in features
            if isinstance(item, Mapping)
        ]
        # 条件门禁：判断`len(feature_ids) != len(set(feature_ids))`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if len(feature_ids) != len(set(feature_ids)):
            # API或函数调用：执行`issues.append`，完整调用片段为`issues.append('duplicate_feature_ids')`。
            # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
            # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
            # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
            issues.append("duplicate_feature_ids")
        # 条件门禁：判断`any((item.get('regime_label') is not None for item in features if isinstance(item, Mapping)))`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if any(
            item.get("regime_label") is not None
            for item in features
            if isinstance(item, Mapping)
        ):
            # API或函数调用：执行`issues.append`，完整调用片段为`issues.append('feature_regime_label')`。
            # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
            # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
            # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
            issues.append("feature_regime_label")

    # 结果返回：把`tuple(dict.fromkeys(issues))`交给调用方并结束当前函数。
    # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return tuple(dict.fromkeys(issues))


# 函数report_to_json_safe：执行report_to_json_safe逻辑。
# - 参数value：类型Any；进入函数后按合同参与校验、筛选、计算或路由。
# - 输出：返回类型Any；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
# - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
# - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
def report_to_json_safe(value: Any) -> Any:
    # 条件门禁：判断`isinstance(value, (date, datetime))`，条件为真时进入受保护分支。
    # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
    # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
    # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
    if isinstance(value, (date, datetime)):
        # 结果返回：把`value.isoformat()`交给调用方并结束当前函数。
        # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return value.isoformat()
    # 条件门禁：判断`isinstance(value, tuple)`，条件为真时进入受保护分支。
    # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
    # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
    # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
    if isinstance(value, tuple):
        # 结果返回：把`[report_to_json_safe(item) for item in value]`交给调用方并结束当前函数。
        # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return [report_to_json_safe(item) for item in value]
    # 条件门禁：判断`isinstance(value, list)`，条件为真时进入受保护分支。
    # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
    # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
    # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
    if isinstance(value, list):
        # 结果返回：把`[report_to_json_safe(item) for item in value]`交给调用方并结束当前函数。
        # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return [report_to_json_safe(item) for item in value]
    # 条件门禁：判断`isinstance(value, Mapping)`，条件为真时进入受保护分支。
    # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
    # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
    # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
    if isinstance(value, Mapping):
        # 结果返回：把`{str(key): report_to_json_safe(item) for key, item in value.items()}`交给调用方并结束当前函数。
        # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return {
            str(key): report_to_json_safe(item)
            for key, item in value.items()
        }
    # 结果返回：把`value`交给调用方并结束当前函数。
    # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return value
