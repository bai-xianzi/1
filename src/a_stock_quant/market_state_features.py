# 模块总览：TASK_019B：可解释市场状态研究特征。
# - 输入输出：本模块通过强类型合同、纯函数和显式服务调用交换数据，不在导入阶段执行数据库写入或交易动作。
# - 数据变化：只有显式构造、校验、查询、证据组合或报告导出才产生新对象与受控状态。
# - 时点与安全：就绪度和市场状态相关逻辑必须保留usage、as_of、available_at、血缘与阻断信息。
# - 为什么这样写：先声明模块边界，读者可以在阅读实现前理解职责、风险、数值语义和可复用方式。
"""TASK_019B：可解释市场状态研究特征。

本模块只生成可追溯的研究特征快照，不计算市场状态标签，
不生成仓位或交易建议。
"""
# 依赖导入：执行`from __future__ import annotations`，加载下方合同、类型或标准库能力。
# - 数据变化：导入只把模块、类或函数绑定到当前命名空间，不在本行主动查询数据库或修改业务数据。
# - 为什么这样写：显式依赖使模块边界、可替换组件和测试注入点保持清晰。
from __future__ import annotations

# 依赖导入：执行`import json`，加载下方合同、类型或标准库能力。
# - 数据变化：导入只把模块、类或函数绑定到当前命名空间，不在本行主动查询数据库或修改业务数据。
# - 为什么这样写：显式依赖使模块边界、可替换组件和测试注入点保持清晰。
import json
# 依赖导入：执行`import math`，加载下方合同、类型或标准库能力。
# - 数据变化：导入只把模块、类或函数绑定到当前命名空间，不在本行主动查询数据库或修改业务数据。
# - 为什么这样写：显式依赖使模块边界、可替换组件和测试注入点保持清晰。
import math
# 依赖导入：执行`import statistics`，加载下方合同、类型或标准库能力。
# - 数据变化：导入只把模块、类或函数绑定到当前命名空间，不在本行主动查询数据库或修改业务数据。
# - 为什么这样写：显式依赖使模块边界、可替换组件和测试注入点保持清晰。
import statistics
# 依赖导入：执行`from dataclasses import asdict, dataclass`，加载下方合同、类型或标准库能力。
# - 数据变化：导入只把模块、类或函数绑定到当前命名空间，不在本行主动查询数据库或修改业务数据。
# - 为什么这样写：显式依赖使模块边界、可替换组件和测试注入点保持清晰。
from dataclasses import asdict, dataclass
# 依赖导入：执行`from datetime import date, datetime`，加载下方合同、类型或标准库能力。
# - 数据变化：导入只把模块、类或函数绑定到当前命名空间，不在本行主动查询数据库或修改业务数据。
# - 为什么这样写：显式依赖使模块边界、可替换组件和测试注入点保持清晰。
from datetime import date, datetime
# 依赖导入：执行`from enum import Enum`，加载下方合同、类型或标准库能力。
# - 数据变化：导入只把模块、类或函数绑定到当前命名空间，不在本行主动查询数据库或修改业务数据。
# - 为什么这样写：显式依赖使模块边界、可替换组件和测试注入点保持清晰。
from enum import Enum
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
# 依赖导入：执行`from .market_state_inputs import ( MarketStateFeatureFamily, MarketStateInputContractEngine,`，加载下方合同、类型或标准库能力。
# - 数据变化：导入只把模块、类或函数绑定到当前命名空间，不在本行主动查询数据库或修改业务数据。
# - 为什么这样写：显式依赖使模块边界、可替换组件和测试注入点保持清晰。
from .market_state_inputs import (
    MarketStateFeatureFamily,
    MarketStateInputContractEngine,
    MarketStateInputStatus,
)
# 依赖导入：执行`from .standard_data_service import StandardDataUsage`，加载下方合同、类型或标准库能力。
# - 数据变化：导入只把模块、类或函数绑定到当前命名空间，不在本行主动查询数据库或修改业务数据。
# - 为什么这样写：显式依赖使模块边界、可替换组件和测试注入点保持清晰。
from .standard_data_service import StandardDataUsage


# 关键常量MARKET_STATE_FEATURE_SPEC_VERSION：把`'0.1.0'`固定为本模块可追踪的合同值。
# - 来源：该值来自当前项目任务合同、配置或真实验收口径；未标注为行业标准时不得外推为通用值。
# - 数据范围：字符串常量用于版本、状态或模式标识；数值常量的单位和有效范围由相邻校验与调用语义约束。
# - 实操示例：报告和下游对象携带该值后，可以判断生产者版本并复现实验或验收过程。
# - 为什么这样写：集中命名固定参数可避免魔法值散落，并让配置升级、审计和兼容性检查有明确锚点。
MARKET_STATE_FEATURE_SPEC_VERSION = "0.1.0"


# 类MarketStateFeatureStatus：封装MarketStateFeatureStatus相关状态、字段与行为。
# - 继承边界：基类为str, Enum；类体包含约3个字段或常量、0个方法。
# - 数据变化：类定义本身不执行隐式I/O，实例只在构造、校验或显式方法调用时产生受控状态。
# - 实操示例：调用方先构造该类型，再由方法完成校验、证据组合、路由或结果导出。
# - 为什么这样写：强类型边界能把相关不变量集中管理，减少字典键拼写、状态漂移和跨模块耦合。
class MarketStateFeatureStatus(str, Enum):
    # 关键常量READY：把`'READY'`固定为本模块可追踪的合同值。
    # - 来源：该值来自当前项目任务合同、配置或真实验收口径；未标注为行业标准时不得外推为通用值。
    # - 数据范围：字符串常量用于版本、状态或模式标识；数值常量的单位和有效范围由相邻校验与调用语义约束。
    # - 实操示例：报告和下游对象携带该值后，可以判断生产者版本并复现实验或验收过程。
    # - 为什么这样写：集中命名固定参数可避免魔法值散落，并让配置升级、审计和兼容性检查有明确锚点。
    READY = "READY"
    # 关键常量READY_WITH_WARNINGS：把`'READY_WITH_WARNINGS'`固定为本模块可追踪的合同值。
    # - 来源：该值来自当前项目任务合同、配置或真实验收口径；未标注为行业标准时不得外推为通用值。
    # - 数据范围：字符串常量用于版本、状态或模式标识；数值常量的单位和有效范围由相邻校验与调用语义约束。
    # - 实操示例：报告和下游对象携带该值后，可以判断生产者版本并复现实验或验收过程。
    # - 为什么这样写：集中命名固定参数可避免魔法值散落，并让配置升级、审计和兼容性检查有明确锚点。
    READY_WITH_WARNINGS = "READY_WITH_WARNINGS"
    # 关键常量BLOCKED：把`'BLOCKED'`固定为本模块可追踪的合同值。
    # - 来源：该值来自当前项目任务合同、配置或真实验收口径；未标注为行业标准时不得外推为通用值。
    # - 数据范围：字符串常量用于版本、状态或模式标识；数值常量的单位和有效范围由相邻校验与调用语义约束。
    # - 实操示例：报告和下游对象携带该值后，可以判断生产者版本并复现实验或验收过程。
    # - 为什么这样写：集中命名固定参数可避免魔法值散落，并让配置升级、审计和兼容性检查有明确锚点。
    BLOCKED = "BLOCKED"


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


# 函数_normalise_texts：执行_normalise_texts逻辑。
# - 参数values：类型Iterable[str]；进入函数后按合同参与校验、筛选、计算或路由。
# - 参数field_name：类型str；进入函数后按合同参与校验、筛选、计算或路由。
# - 关键字参数allow_empty：类型bool，默认值False；只允许显式命名传入，降低参数错位风险。
# - 输出：返回类型tuple[str, ...]；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
# - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
# - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
def _normalise_texts(
    values: Iterable[str],
    field_name: str,
    *,
    allow_empty: bool = False,
) -> tuple[str, ...]:
    # 变量更新：计算并保存result，右侧逻辑为`tuple((_require_text(value, field_name) for value in values))`。
    # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
    # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
    result = tuple(_require_text(value, field_name) for value in values)
    # 条件门禁：判断`not allow_empty and (not result)`，条件为真时进入受保护分支。
    # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
    # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
    # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
    if not allow_empty and not result:
        # 错误阻断：抛出`DataContractError(f'{field_name}不能为空。')`并停止当前正常路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
        # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
        raise DataContractError(f"{field_name}不能为空。")
    # 条件门禁：判断`len(result) != len(set(result))`，条件为真时进入受保护分支。
    # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
    # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
    # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
    if len(result) != len(set(result)):
        # 错误阻断：抛出`DataContractError(f'{field_name}不允许重复。')`并停止当前正常路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
        # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
        raise DataContractError(f"{field_name}不允许重复。")
    # 结果返回：把`result`交给调用方并结束当前函数。
    # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return result


# 函数_coerce_date：执行_coerce_date逻辑。
# - 参数value：类型Any；进入函数后按合同参与校验、筛选、计算或路由。
# - 输出：返回类型date | None；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
# - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
# - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
def _coerce_date(value: Any) -> date | None:
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
    # 条件门禁：判断`isinstance(value, str) and value.strip()`，条件为真时进入受保护分支。
    # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
    # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
    # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
    if isinstance(value, str) and value.strip():
        # 变量更新：计算并保存text，右侧逻辑为`value.strip()`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        text = value.strip()
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
        except ValueError:
            # 结果返回：把`None`交给调用方并结束当前函数。
            # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
            # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
            return None
    # 结果返回：把`None`交给调用方并结束当前函数。
    # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return None


# 函数_to_float：执行_to_float逻辑。
# - 参数value：类型Any；进入函数后按合同参与校验、筛选、计算或路由。
# - 输出：返回类型float | None；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
# - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
# - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
def _to_float(value: Any) -> float | None:
    # 条件门禁：判断`value is None or isinstance(value, bool)`，条件为真时进入受保护分支。
    # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
    # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
    # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
    if value is None or isinstance(value, bool):
        # 结果返回：把`None`交给调用方并结束当前函数。
        # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return None
    # 异常边界：执行可能失败的解析、转换、文件读取或外部调用，并在后续分支转换为项目统一错误。
    # - 数据变化：成功路径产生正常结果；失败路径保留原异常作为cause、降级为缺失值或记录明确问题。
    # - 为什么这样写：上层只需处理稳定的DataContractError或受控结果，不依赖第三方异常实现细节。
    try:
        # 变量更新：计算并保存result，右侧逻辑为`float(value)`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        result = float(value)
    # 异常转换：捕获(TypeError, ValueError)，保存上下文并执行统一错误、回退或忽略策略。
    # - 数据变化：异常路径不返回未校验的半成品；必要时把失败原因写入issues、warnings或异常链。
    # - 为什么这样写：明确捕获范围可避免吞掉程序错误，同时让调用方获得稳定且可审计的失败语义。
    except (TypeError, ValueError):
        # 结果返回：把`None`交给调用方并结束当前函数。
        # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return None
    # 条件门禁：判断`not math.isfinite(result)`，条件为真时进入受保护分支。
    # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
    # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
    # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
    if not math.isfinite(result):
        # 结果返回：把`None`交给调用方并结束当前函数。
        # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return None
    # 结果返回：把`result`交给调用方并结束当前函数。
    # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return result


# 函数_record_trade_date：执行_record_trade_date逻辑。
# - 参数record：类型Any；进入函数后按合同参与校验、筛选、计算或路由。
# - 输出：返回类型date | None；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
# - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
# - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
def _record_trade_date(record: Any) -> date | None:
    # 变量更新：计算并保存values，右侧逻辑为`getattr(record, 'values', {})`。
    # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
    # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
    values = getattr(record, "values", {})
    # 变量更新：计算并保存primary_key，右侧逻辑为`getattr(record, 'primary_key', {})`。
    # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
    # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
    primary_key = getattr(record, "primary_key", {})
    # 结果返回：把`_coerce_date(values.get('trade_date', primary_key.get('trade_date')))`交给调用方并结束当前函数。
    # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return _coerce_date(
        values.get("trade_date", primary_key.get("trade_date"))
    )


# 函数_records_on_date：执行_records_on_date逻辑。
# - 参数records：类型Sequence[Any]；进入函数后按合同参与校验、筛选、计算或路由。
# - 参数target：类型date；进入函数后按合同参与校验、筛选、计算或路由。
# - 输出：返回类型tuple[Any, ...]；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
# - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
# - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
def _records_on_date(records: Sequence[Any], target: date) -> tuple[Any, ...]:
    # 结果返回：把`tuple((record for record in records if _record_trade_date(record) == target))`交给调用方并结束当前函数。
    # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return tuple(
        record
        for record in records
        if _record_trade_date(record) == target
    )


# 函数_numeric_values：执行_numeric_values逻辑。
# - 参数records：类型Sequence[Any]；进入函数后按合同参与校验、筛选、计算或路由。
# - 参数field_name：类型str；进入函数后按合同参与校验、筛选、计算或路由。
# - 输出：返回类型list[float]；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
# - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
# - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
def _numeric_values(records: Sequence[Any], field_name: str) -> list[float]:
    # 字段或变量result：声明类型list[float]，初始逻辑为`[]`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    result: list[float] = []
    # 迭代处理：依次从`records`读取元素，并绑定到`record`。
    # - 维度变化：每轮处理一个记录、字段、证据或配置项，可能向列表、字典或累计统计增加一项。
    # - 为什么这样写：显式逐项处理便于保留顺序、定位坏数据，并对每个实体执行同一合同。
    for record in records:
        # 变量更新：计算并保存value，右侧逻辑为`_to_float(getattr(record, 'values', {}).get(field_name))`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        value = _to_float(getattr(record, "values", {}).get(field_name))
        # 条件门禁：判断`value is not None`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if value is not None:
            # API或函数调用：执行`result.append`，完整调用片段为`result.append(value)`。
            # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
            # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
            # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
            result.append(value)
    # 结果返回：把`result`交给调用方并结束当前函数。
    # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return result


# 类MarketStateFeatureDefinition：封装MarketStateFeatureDefinition相关状态、字段与行为。
# - 继承边界：基类为object；类体包含约8个字段或常量、1个方法。
# - 数据变化：类定义本身不执行隐式I/O，实例只在构造、校验或显式方法调用时产生受控状态。
# - 实操示例：调用方先构造该类型，再由方法完成校验、证据组合、路由或结果导出。
# - 为什么这样写：强类型边界能把相关不变量集中管理，减少字典键拼写、状态漂移和跨模块耦合。
@dataclass(frozen=True, slots=True)
class MarketStateFeatureDefinition:
    # 字段或变量feature_id：声明类型str，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    feature_id: str
    # 字段或变量family：声明类型MarketStateFeatureFamily，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    family: MarketStateFeatureFamily
    # 字段或变量unit：声明类型str，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    unit: str
    # 字段或变量source_dataset_ids：声明类型tuple[str, ...]，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    source_dataset_ids: tuple[str, ...]
    # 字段或变量required_fields：声明类型tuple[str, ...]，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    required_fields: tuple[str, ...]
    # 字段或变量minimum_observation_count：声明类型int，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    minimum_observation_count: int
    # 字段或变量formula：声明类型str，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    formula: str
    # 字段或变量interpretation：声明类型str，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    interpretation: str

    # 函数__post_init__：执行__post_init__逻辑。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态、模块常量或封装依赖。
    # - 输出：返回类型None；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
    # - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
    # - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
    def __post_init__(self) -> None:
        # 迭代处理：依次从`('feature_id', 'unit', 'formula', 'interpretation')`读取元素，并绑定到`field_name`。
        # - 维度变化：每轮处理一个记录、字段、证据或配置项，可能向列表、字典或累计统计增加一项。
        # - 为什么这样写：显式逐项处理便于保留顺序、定位坏数据，并对每个实体执行同一合同。
        for field_name in (
            "feature_id",
            "unit",
            "formula",
            "interpretation",
        ):
            # API或函数调用：执行`object.__setattr__`，完整调用片段为`object.__setattr__(self, field_name, _require_text(getattr(self, field_name), field_name))`。
            # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
            # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
            # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
            object.__setattr__(
                self,
                field_name,
                _require_text(getattr(self, field_name), field_name),
            )
        # 变量更新：计算并保存family，右侧逻辑为`self.family`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        family = self.family
        # 条件门禁：判断`isinstance(family, str)`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if isinstance(family, str):
            # 变量更新：计算并保存family，右侧逻辑为`MarketStateFeatureFamily(family)`。
            # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
            # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
            family = MarketStateFeatureFamily(family)
        # API或函数调用：执行`object.__setattr__`，完整调用片段为`object.__setattr__(self, 'family', family)`。
        # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
        # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
        # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
        object.__setattr__(self, "family", family)
        # API或函数调用：执行`object.__setattr__`，完整调用片段为`object.__setattr__(self, 'source_dataset_ids', _normalise_texts(self.source_dataset_ids, 'source_da…`。
        # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
        # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
        # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
        object.__setattr__(
            self,
            "source_dataset_ids",
            _normalise_texts(
                self.source_dataset_ids,
                "source_dataset_ids",
            ),
        )
        # API或函数调用：执行`object.__setattr__`，完整调用片段为`object.__setattr__(self, 'required_fields', _normalise_texts(self.required_fields, 'required_fields…`。
        # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
        # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
        # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
        object.__setattr__(
            self,
            "required_fields",
            _normalise_texts(
                self.required_fields,
                "required_fields",
            ),
        )
        # 条件门禁：判断`not isinstance(self.minimum_observation_count, int) or self.minimum_observation_count < 1`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if (
            not isinstance(self.minimum_observation_count, int)
            or self.minimum_observation_count < 1
        ):
            # 错误阻断：抛出`DataContractError('minimum_observation_count必须是正整数。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
            raise DataContractError(
                "minimum_observation_count必须是正整数。"
            )


# 类MarketStateFeatureSpec：封装MarketStateFeatureSpec相关状态、字段与行为。
# - 继承边界：基类为object；类体包含约14个字段或常量、2个方法。
# - 数据变化：类定义本身不执行隐式I/O，实例只在构造、校验或显式方法调用时产生受控状态。
# - 实操示例：调用方先构造该类型，再由方法完成校验、证据组合、路由或结果导出。
# - 为什么这样写：强类型边界能把相关不变量集中管理，减少字典键拼写、状态漂移和跨模块耦合。
@dataclass(frozen=True, slots=True)
class MarketStateFeatureSpec:
    # 字段或变量task_id：声明类型str，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    task_id: str
    # 字段或变量spec_version：声明类型str，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    spec_version: str
    # 字段或变量input_contract_version：声明类型str，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    input_contract_version: str
    # 字段或变量output_object：声明类型str，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    output_object: str
    # 字段或变量output_scope：声明类型str，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    output_scope: str
    # 字段或变量allowed_usage：声明类型StandardDataUsage，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    allowed_usage: StandardDataUsage
    # 字段或变量manual_decision_allowed：声明类型bool，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    manual_decision_allowed: bool
    # 字段或变量official_market_state_allowed：声明类型bool，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    official_market_state_allowed: bool
    # 字段或变量regime_label_allowed：声明类型bool，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    regime_label_allowed: bool
    # 字段或变量date_alignment_policy：声明类型str，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    date_alignment_policy: str
    # 字段或变量required_source_datasets：声明类型tuple[str, ...]，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    required_source_datasets: tuple[str, ...]
    # 字段或变量required_feature_families：声明类型tuple[MarketStateFeatureFamily, ...]，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    required_feature_families: tuple[MarketStateFeatureFamily, ...]
    # 字段或变量feature_definitions：声明类型tuple[MarketStateFeatureDefinition, ...]，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    feature_definitions: tuple[MarketStateFeatureDefinition, ...]
    # 字段或变量hard_rules：声明类型tuple[str, ...]，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    hard_rules: tuple[str, ...]

    # 函数__post_init__：执行__post_init__逻辑。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态、模块常量或封装依赖。
    # - 输出：返回类型None；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
    # - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
    # - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
    def __post_init__(self) -> None:
        # 迭代处理：依次从`('task_id', 'spec_version', 'input_contract_version', 'output_object', 'output_scope', 'date_alignm…`读取元素，并绑定到`field_name`。
        # - 维度变化：每轮处理一个记录、字段、证据或配置项，可能向列表、字典或累计统计增加一项。
        # - 为什么这样写：显式逐项处理便于保留顺序、定位坏数据，并对每个实体执行同一合同。
        for field_name in (
            "task_id",
            "spec_version",
            "input_contract_version",
            "output_object",
            "output_scope",
            "date_alignment_policy",
        ):
            # API或函数调用：执行`object.__setattr__`，完整调用片段为`object.__setattr__(self, field_name, _require_text(getattr(self, field_name), field_name))`。
            # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
            # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
            # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
            object.__setattr__(
                self,
                field_name,
                _require_text(getattr(self, field_name), field_name),
            )
        # 变量更新：计算并保存usage，右侧逻辑为`self.allowed_usage`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        usage = self.allowed_usage
        # 条件门禁：判断`isinstance(usage, str)`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if isinstance(usage, str):
            # 变量更新：计算并保存usage，右侧逻辑为`StandardDataUsage(usage)`。
            # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
            # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
            usage = StandardDataUsage(usage)
        # 条件门禁：判断`usage is not StandardDataUsage.CURRENT_SNAPSHOT_RESEARCH`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if usage is not StandardDataUsage.CURRENT_SNAPSHOT_RESEARCH:
            # 错误阻断：抛出`DataContractError('TASK_019B只允许CURRENT_SNAPSHOT_RESEARCH。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
            raise DataContractError(
                "TASK_019B只允许CURRENT_SNAPSHOT_RESEARCH。"
            )
        # API或函数调用：执行`object.__setattr__`，完整调用片段为`object.__setattr__(self, 'allowed_usage', usage)`。
        # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
        # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
        # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
        object.__setattr__(self, "allowed_usage", usage)
        # 条件门禁：判断`self.manual_decision_allowed or self.official_market_state_allowed or self.regime_label_allowed`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if (
            self.manual_decision_allowed
            or self.official_market_state_allowed
            or self.regime_label_allowed
        ):
            # 错误阻断：抛出`DataContractError('TASK_019B不得启用决策、正式状态或状态标签。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
            raise DataContractError(
                "TASK_019B不得启用决策、正式状态或状态标签。"
            )
        # 条件门禁：判断`self.date_alignment_policy != 'LATEST_COMMON_TRADE_DATE'`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if self.date_alignment_policy != "LATEST_COMMON_TRADE_DATE":
            # 错误阻断：抛出`DataContractError('不支持的日期对齐政策。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
            raise DataContractError("不支持的日期对齐政策。")
        # API或函数调用：执行`object.__setattr__`，完整调用片段为`object.__setattr__(self, 'required_source_datasets', _normalise_texts(self.required_source_datasets…`。
        # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
        # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
        # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
        object.__setattr__(
            self,
            "required_source_datasets",
            _normalise_texts(
                self.required_source_datasets,
                "required_source_datasets",
            ),
        )
        # 变量更新：计算并保存families，右侧逻辑为`tuple((item if isinstance(item, MarketStateFeatureFamily) else MarketStateFeatureFamily(item) for i…`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        families = tuple(
            item if isinstance(item, MarketStateFeatureFamily)
            else MarketStateFeatureFamily(item)
            for item in self.required_feature_families
        )
        # 条件门禁：判断`not families or len(families) != len(set(families))`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if not families or len(families) != len(set(families)):
            # 错误阻断：抛出`DataContractError('required_feature_families必须非空且唯一。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
            raise DataContractError(
                "required_feature_families必须非空且唯一。"
            )
        # API或函数调用：执行`object.__setattr__`，完整调用片段为`object.__setattr__(self, 'required_feature_families', families)`。
        # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
        # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
        # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
        object.__setattr__(self, "required_feature_families", families)
        # 条件门禁：判断`not self.feature_definitions`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if not self.feature_definitions:
            # 错误阻断：抛出`DataContractError('feature_definitions不能为空。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
            raise DataContractError("feature_definitions不能为空。")
        # 变量更新：计算并保存feature_ids，右侧逻辑为`[item.feature_id for item in self.feature_definitions]`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        feature_ids = [item.feature_id for item in self.feature_definitions]
        # 条件门禁：判断`len(feature_ids) != len(set(feature_ids))`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if len(feature_ids) != len(set(feature_ids)):
            # 错误阻断：抛出`DataContractError('feature_id不允许重复。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
            raise DataContractError("feature_id不允许重复。")
        # 变量更新：计算并保存covered，右侧逻辑为`{item.family for item in self.feature_definitions}`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        covered = {item.family for item in self.feature_definitions}
        # 条件门禁：判断`not set(families).issubset(covered)`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if not set(families).issubset(covered):
            # 错误阻断：抛出`DataContractError('必需特征族未被定义覆盖。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
            raise DataContractError("必需特征族未被定义覆盖。")
        # API或函数调用：执行`object.__setattr__`，完整调用片段为`object.__setattr__(self, 'hard_rules', _normalise_texts(self.hard_rules, 'hard_rules'))`。
        # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
        # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
        # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
        object.__setattr__(
            self,
            "hard_rules",
            _normalise_texts(self.hard_rules, "hard_rules"),
        )

    # 函数definition：执行definition逻辑。
    # - 参数feature_id：类型str；进入函数后按合同参与校验、筛选、计算或路由。
    # - 输出：返回类型MarketStateFeatureDefinition；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
    # - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
    # - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
    def definition(self, feature_id: str) -> MarketStateFeatureDefinition:
        # 变量更新：计算并保存key，右侧逻辑为`_require_text(feature_id, 'feature_id')`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        key = _require_text(feature_id, "feature_id")
        # 迭代处理：依次从`self.feature_definitions`读取元素，并绑定到`item`。
        # - 维度变化：每轮处理一个记录、字段、证据或配置项，可能向列表、字典或累计统计增加一项。
        # - 为什么这样写：显式逐项处理便于保留顺序、定位坏数据，并对每个实体执行同一合同。
        for item in self.feature_definitions:
            # 条件门禁：判断`item.feature_id == key`，条件为真时进入受保护分支。
            # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
            # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
            # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
            if item.feature_id == key:
                # 结果返回：把`item`交给调用方并结束当前函数。
                # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
                # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
                return item
        # 错误阻断：抛出`DataContractError(f'未登记市场状态特征：{key}')`并停止当前正常路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
        # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
        raise DataContractError(f"未登记市场状态特征：{key}")


# 类MarketStateFeatureObservation：封装MarketStateFeatureObservation相关状态、字段与行为。
# - 继承边界：基类为object；类体包含约13个字段或常量、1个方法。
# - 数据变化：类定义本身不执行隐式I/O，实例只在构造、校验或显式方法调用时产生受控状态。
# - 实操示例：调用方先构造该类型，再由方法完成校验、证据组合、路由或结果导出。
# - 为什么这样写：强类型边界能把相关不变量集中管理，减少字典键拼写、状态漂移和跨模块耦合。
@dataclass(frozen=True, slots=True)
class MarketStateFeatureObservation:
    # 字段或变量feature_id：声明类型str，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    feature_id: str
    # 字段或变量family：声明类型MarketStateFeatureFamily，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    family: MarketStateFeatureFamily
    # 字段或变量value：声明类型float，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    value: float
    # 字段或变量unit：声明类型str，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    unit: str
    # 字段或变量as_of_date：声明类型date，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    as_of_date: date
    # 字段或变量formula：声明类型str，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    formula: str
    # 字段或变量interpretation：声明类型str，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    interpretation: str
    # 字段或变量source_dataset_ids：声明类型tuple[str, ...]，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    source_dataset_ids: tuple[str, ...]
    # 字段或变量source_query_ids：声明类型tuple[str, ...]，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    source_query_ids: tuple[str, ...]
    # 字段或变量source_record_count：声明类型int，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    source_record_count: int
    # 字段或变量valid_observation_count：声明类型int，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    valid_observation_count: int
    # 字段或变量missing_observation_count：声明类型int，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    missing_observation_count: int
    # 字段或变量warnings：声明类型tuple[str, ...]，初始逻辑为`()`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    warnings: tuple[str, ...] = ()

    # 函数__post_init__：执行__post_init__逻辑。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态、模块常量或封装依赖。
    # - 输出：返回类型None；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
    # - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
    # - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
    def __post_init__(self) -> None:
        # 迭代处理：依次从`('feature_id', 'unit', 'formula', 'interpretation')`读取元素，并绑定到`field_name`。
        # - 维度变化：每轮处理一个记录、字段、证据或配置项，可能向列表、字典或累计统计增加一项。
        # - 为什么这样写：显式逐项处理便于保留顺序、定位坏数据，并对每个实体执行同一合同。
        for field_name in (
            "feature_id",
            "unit",
            "formula",
            "interpretation",
        ):
            # API或函数调用：执行`object.__setattr__`，完整调用片段为`object.__setattr__(self, field_name, _require_text(getattr(self, field_name), field_name))`。
            # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
            # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
            # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
            object.__setattr__(
                self,
                field_name,
                _require_text(getattr(self, field_name), field_name),
            )
        # 条件门禁：判断`not isinstance(self.as_of_date, date)`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if not isinstance(self.as_of_date, date):
            # 错误阻断：抛出`DataContractError('as_of_date必须是date。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
            raise DataContractError("as_of_date必须是date。")
        # 条件门禁：判断`not math.isfinite(float(self.value))`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if not math.isfinite(float(self.value)):
            # 错误阻断：抛出`DataContractError('特征值必须是有限数。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
            raise DataContractError("特征值必须是有限数。")
        # 条件门禁：判断`self.source_record_count < 0`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if self.source_record_count < 0:
            # 错误阻断：抛出`DataContractError('source_record_count不能为负。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
            raise DataContractError("source_record_count不能为负。")
        # 条件门禁：判断`self.valid_observation_count < 0`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if self.valid_observation_count < 0:
            # 错误阻断：抛出`DataContractError('valid_observation_count不能为负。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
            raise DataContractError(
                "valid_observation_count不能为负。"
            )
        # 条件门禁：判断`self.missing_observation_count < 0`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if self.missing_observation_count < 0:
            # 错误阻断：抛出`DataContractError('missing_observation_count不能为负。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
            raise DataContractError(
                "missing_observation_count不能为负。"
            )
        # API或函数调用：执行`object.__setattr__`，完整调用片段为`object.__setattr__(self, 'source_dataset_ids', _normalise_texts(self.source_dataset_ids, 'source_da…`。
        # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
        # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
        # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
        object.__setattr__(
            self,
            "source_dataset_ids",
            _normalise_texts(
                self.source_dataset_ids,
                "source_dataset_ids",
            ),
        )
        # API或函数调用：执行`object.__setattr__`，完整调用片段为`object.__setattr__(self, 'source_query_ids', _normalise_texts(self.source_query_ids, 'source_query_…`。
        # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
        # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
        # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
        object.__setattr__(
            self,
            "source_query_ids",
            _normalise_texts(
                self.source_query_ids,
                "source_query_ids",
            ),
        )
        # API或函数调用：执行`object.__setattr__`，完整调用片段为`object.__setattr__(self, 'warnings', _normalise_texts(self.warnings, 'warnings', allow_empty=True))`。
        # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
        # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
        # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
        object.__setattr__(
            self,
            "warnings",
            _normalise_texts(
                self.warnings,
                "warnings",
                allow_empty=True,
            ),
        )


# 类MarketStateFeatureSnapshot：封装MarketStateFeatureSnapshot相关状态、字段与行为。
# - 继承边界：基类为object；类体包含约13个字段或常量、4个方法。
# - 数据变化：类定义本身不执行隐式I/O，实例只在构造、校验或显式方法调用时产生受控状态。
# - 实操示例：调用方先构造该类型，再由方法完成校验、证据组合、路由或结果导出。
# - 为什么这样写：强类型边界能把相关不变量集中管理，减少字典键拼写、状态漂移和跨模块耦合。
@dataclass(frozen=True, slots=True)
class MarketStateFeatureSnapshot:
    # 字段或变量status：声明类型MarketStateFeatureStatus，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    status: MarketStateFeatureStatus
    # 字段或变量feature_spec_version：声明类型str，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    feature_spec_version: str
    # 字段或变量input_contract_version：声明类型str，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    input_contract_version: str
    # 字段或变量usage：声明类型StandardDataUsage，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    usage: StandardDataUsage
    # 字段或变量as_of_date：声明类型date | None，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    as_of_date: date | None
    # 字段或变量input_assessment_status：声明类型str，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    input_assessment_status: str
    # 字段或变量features：声明类型tuple[MarketStateFeatureObservation, ...]，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    features: tuple[MarketStateFeatureObservation, ...]
    # 字段或变量missing_required_features：声明类型tuple[str, ...]，初始逻辑为`()`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    missing_required_features: tuple[str, ...] = ()
    # 字段或变量warnings：声明类型tuple[str, ...]，初始逻辑为`()`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    warnings: tuple[str, ...] = ()
    # 字段或变量research_feature_build_allowed：声明类型bool，初始逻辑为`False`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    research_feature_build_allowed: bool = False
    # 字段或变量manual_decision_allowed：声明类型bool，初始逻辑为`False`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    manual_decision_allowed: bool = False
    # 字段或变量official_market_state_allowed：声明类型bool，初始逻辑为`False`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    official_market_state_allowed: bool = False
    # 字段或变量regime_label：声明类型str | None，初始逻辑为`None`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    regime_label: str | None = None

    # 函数blocks_downstream：执行blocks_downstream逻辑。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态、模块常量或封装依赖。
    # - 输出：返回类型bool；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
    # - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
    # - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
    @property
    def blocks_downstream(self) -> bool:
        # 结果返回：把`self.status is MarketStateFeatureStatus.BLOCKED`交给调用方并结束当前函数。
        # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return self.status is MarketStateFeatureStatus.BLOCKED

    # 函数assert_research_usable：执行assert_research_usable逻辑。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态、模块常量或封装依赖。
    # - 输出：返回类型None；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
    # - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
    # - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
    def assert_research_usable(self) -> None:
        # 条件门禁：判断`self.blocks_downstream`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if self.blocks_downstream:
            # 错误阻断：抛出`DataContractError('市场状态特征快照被阻断：' + ', '.join(self.missing_required_features))`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
            raise DataContractError(
                "市场状态特征快照被阻断："
                + ", ".join(self.missing_required_features)
            )

    # 函数feature：执行feature逻辑。
    # - 参数feature_id：类型str；进入函数后按合同参与校验、筛选、计算或路由。
    # - 输出：返回类型MarketStateFeatureObservation；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
    # - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
    # - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
    def feature(self, feature_id: str) -> MarketStateFeatureObservation:
        # 变量更新：计算并保存key，右侧逻辑为`_require_text(feature_id, 'feature_id')`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        key = _require_text(feature_id, "feature_id")
        # 迭代处理：依次从`self.features`读取元素，并绑定到`item`。
        # - 维度变化：每轮处理一个记录、字段、证据或配置项，可能向列表、字典或累计统计增加一项。
        # - 为什么这样写：显式逐项处理便于保留顺序、定位坏数据，并对每个实体执行同一合同。
        for item in self.features:
            # 条件门禁：判断`item.feature_id == key`，条件为真时进入受保护分支。
            # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
            # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
            # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
            if item.feature_id == key:
                # 结果返回：把`item`交给调用方并结束当前函数。
                # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
                # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
                return item
        # 错误阻断：抛出`DataContractError(f'特征快照中不存在：{key}')`并停止当前正常路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
        # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
        raise DataContractError(f"特征快照中不存在：{key}")

    # 函数to_dict：执行to_dict逻辑。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态、模块常量或封装依赖。
    # - 输出：返回类型dict[str, Any]；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
    # - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
    # - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
    def to_dict(self) -> dict[str, Any]:
        # 函数convert：执行convert逻辑。
        # - 参数value：类型Any；进入函数后按合同参与校验、筛选、计算或路由。
        # - 输出：返回类型Any；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
        # - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
        # - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
        def convert(value: Any) -> Any:
            # 条件门禁：判断`isinstance(value, Enum)`，条件为真时进入受保护分支。
            # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
            # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
            # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
            if isinstance(value, Enum):
                # 结果返回：把`value.value`交给调用方并结束当前函数。
                # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
                # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
                return value.value
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
                # 结果返回：把`[convert(item) for item in value]`交给调用方并结束当前函数。
                # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
                # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
                return [convert(item) for item in value]
            # 条件门禁：判断`isinstance(value, list)`，条件为真时进入受保护分支。
            # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
            # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
            # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
            if isinstance(value, list):
                # 结果返回：把`[convert(item) for item in value]`交给调用方并结束当前函数。
                # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
                # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
                return [convert(item) for item in value]
            # 条件门禁：判断`isinstance(value, dict)`，条件为真时进入受保护分支。
            # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
            # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
            # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
            if isinstance(value, dict):
                # 结果返回：把`{str(k): convert(v) for k, v in value.items()}`交给调用方并结束当前函数。
                # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
                # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
                return {str(k): convert(v) for k, v in value.items()}
            # 结果返回：把`value`交给调用方并结束当前函数。
            # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
            # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
            return value
        # 结果返回：把`convert(asdict(self))`交给调用方并结束当前函数。
        # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return convert(asdict(self))


# 函数load_market_state_feature_spec：执行load_market_state_feature_spec逻辑。
# - 参数path：类型str | Path；进入函数后按合同参与校验、筛选、计算或路由。
# - 输出：返回类型MarketStateFeatureSpec；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
# - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
# - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
def load_market_state_feature_spec(
    path: str | Path,
) -> MarketStateFeatureSpec:
    # 变量更新：计算并保存spec_path，右侧逻辑为`Path(path)`。
    # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
    # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
    spec_path = Path(path)
    # 异常边界：执行可能失败的解析、转换、文件读取或外部调用，并在后续分支转换为项目统一错误。
    # - 数据变化：成功路径产生正常结果；失败路径保留原异常作为cause、降级为缺失值或记录明确问题。
    # - 为什么这样写：上层只需处理稳定的DataContractError或受控结果，不依赖第三方异常实现细节。
    try:
        # 变量更新：计算并保存raw，右侧逻辑为`json.loads(spec_path.read_text(encoding='utf-8'))`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        raw = json.loads(spec_path.read_text(encoding="utf-8"))
    # 异常转换：捕获(OSError, json.JSONDecodeError)，保存上下文并执行统一错误、回退或忽略策略。
    # - 数据变化：异常路径不返回未校验的半成品；必要时把失败原因写入issues、warnings或异常链。
    # - 为什么这样写：明确捕获范围可避免吞掉程序错误，同时让调用方获得稳定且可审计的失败语义。
    except (OSError, json.JSONDecodeError) as exc:
        # 错误阻断：抛出`DataContractError(f'无法加载市场状态特征规范：{spec_path}')`并停止当前正常路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
        # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
        raise DataContractError(
            f"无法加载市场状态特征规范：{spec_path}"
        ) from exc
    # 条件门禁：判断`not isinstance(raw, dict)`，条件为真时进入受保护分支。
    # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
    # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
    # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
    if not isinstance(raw, dict):
        # 错误阻断：抛出`DataContractError('特征规范根节点必须是对象。')`并停止当前正常路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
        # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
        raise DataContractError("特征规范根节点必须是对象。")
    # 变量更新：计算并保存definitions，右侧逻辑为`tuple((MarketStateFeatureDefinition(feature_id=str(item['feature_id']), family=MarketStateFeatureFa…`。
    # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
    # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
    definitions = tuple(
        MarketStateFeatureDefinition(
            feature_id=str(item["feature_id"]),
            family=MarketStateFeatureFamily(str(item["family"])),
            unit=str(item["unit"]),
            source_dataset_ids=tuple(
                str(value) for value in item["source_dataset_ids"]
            ),
            required_fields=tuple(
                str(value) for value in item["required_fields"]
            ),
            minimum_observation_count=int(
                item["minimum_observation_count"]
            ),
            formula=str(item["formula"]),
            interpretation=str(item["interpretation"]),
        )
        for item in raw["feature_definitions"]
    )
    # 结果返回：把`MarketStateFeatureSpec(task_id=str(raw['task_id']), spec_version=str(raw['spec_version']), input_co…`交给调用方并结束当前函数。
    # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return MarketStateFeatureSpec(
        task_id=str(raw["task_id"]),
        spec_version=str(raw["spec_version"]),
        input_contract_version=str(raw["input_contract_version"]),
        output_object=str(raw["output_object"]),
        output_scope=str(raw["output_scope"]),
        allowed_usage=StandardDataUsage(str(raw["allowed_usage"])),
        manual_decision_allowed=bool(raw["manual_decision_allowed"]),
        official_market_state_allowed=bool(
            raw["official_market_state_allowed"]
        ),
        regime_label_allowed=bool(raw["regime_label_allowed"]),
        date_alignment_policy=str(raw["date_alignment_policy"]),
        required_source_datasets=tuple(
            str(value) for value in raw["required_source_datasets"]
        ),
        required_feature_families=tuple(
            MarketStateFeatureFamily(str(value))
            for value in raw["required_feature_families"]
        ),
        feature_definitions=definitions,
        hard_rules=tuple(str(value) for value in raw["hard_rules"]),
    )


# 类ExplainableMarketStateFeatureCalculator：从通过TASK_019A门禁的结果构建可解释研究特征。
# - 继承边界：基类为object；类体包含约0个字段或常量、6个方法。
# - 数据变化：类定义本身不执行隐式I/O，实例只在构造、校验或显式方法调用时产生受控状态。
# - 实操示例：调用方先构造该类型，再由方法完成校验、证据组合、路由或结果导出。
# - 为什么这样写：强类型边界能把相关不变量集中管理，减少字典键拼写、状态漂移和跨模块耦合。
class ExplainableMarketStateFeatureCalculator:
    """从通过TASK_019A门禁的结果构建可解释研究特征。"""

    # 函数__init__：执行__init__逻辑。
    # - 参数input_engine：类型MarketStateInputContractEngine；进入函数后按合同参与校验、筛选、计算或路由。
    # - 参数feature_spec：类型MarketStateFeatureSpec；进入函数后按合同参与校验、筛选、计算或路由。
    # - 输出：返回类型None；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
    # - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
    # - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
    def __init__(
        self,
        input_engine: MarketStateInputContractEngine,
        feature_spec: MarketStateFeatureSpec,
    ) -> None:
        # 条件门禁：判断`not isinstance(input_engine, MarketStateInputContractEngine)`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if not isinstance(input_engine, MarketStateInputContractEngine):
            # 错误阻断：抛出`DataContractError('input_engine必须是MarketStateInputContractEngine。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
            raise DataContractError(
                "input_engine必须是MarketStateInputContractEngine。"
            )
        # 条件门禁：判断`not isinstance(feature_spec, MarketStateFeatureSpec)`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if not isinstance(feature_spec, MarketStateFeatureSpec):
            # 错误阻断：抛出`DataContractError('feature_spec必须是MarketStateFeatureSpec。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
            raise DataContractError(
                "feature_spec必须是MarketStateFeatureSpec。"
            )
        # 条件门禁：判断`input_engine.contract.contract_version != feature_spec.input_contract_version`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if (
            input_engine.contract.contract_version
            != feature_spec.input_contract_version
        ):
            # 错误阻断：抛出`DataContractError('输入合同版本与特征规范不一致。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
            raise DataContractError(
                "输入合同版本与特征规范不一致。"
            )
        # 变量更新：计算并保存self.input_engine，右侧逻辑为`input_engine`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        self.input_engine = input_engine
        # 变量更新：计算并保存self.feature_spec，右侧逻辑为`feature_spec`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        self.feature_spec = feature_spec

    # 函数_standard_result：执行_standard_result逻辑。
    # - 参数gated_result：类型Any；进入函数后按合同参与校验、筛选、计算或路由。
    # - 输出：返回类型Any；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
    # - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
    # - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
    @staticmethod
    def _standard_result(gated_result: Any) -> Any:
        # 条件门禁：判断`not hasattr(gated_result, 'standard_result')`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if not hasattr(gated_result, "standard_result"):
            # 错误阻断：抛出`DataContractError('缺少standard_result。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
            raise DataContractError("缺少standard_result。")
        # 结果返回：把`gated_result.standard_result`交给调用方并结束当前函数。
        # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return gated_result.standard_result

    # 函数_blocked_snapshot：执行_blocked_snapshot逻辑。
    # - 参数input_status：类型str；进入函数后按合同参与校验、筛选、计算或路由。
    # - 参数warnings：类型Iterable[str]；进入函数后按合同参与校验、筛选、计算或路由。
    # - 参数missing_features：类型Iterable[str]，默认值()；进入函数后按合同参与校验、筛选、计算或路由。
    # - 输出：返回类型MarketStateFeatureSnapshot；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
    # - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
    # - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
    def _blocked_snapshot(
        self,
        input_status: str,
        warnings: Iterable[str],
        missing_features: Iterable[str] = (),
    ) -> MarketStateFeatureSnapshot:
        # 结果返回：把`MarketStateFeatureSnapshot(status=MarketStateFeatureStatus.BLOCKED, feature_spec_version=self.featu…`交给调用方并结束当前函数。
        # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return MarketStateFeatureSnapshot(
            status=MarketStateFeatureStatus.BLOCKED,
            feature_spec_version=self.feature_spec.spec_version,
            input_contract_version=(
                self.feature_spec.input_contract_version
            ),
            usage=self.feature_spec.allowed_usage,
            as_of_date=None,
            input_assessment_status=input_status,
            features=(),
            missing_required_features=tuple(
                dict.fromkeys(missing_features)
            ),
            warnings=tuple(dict.fromkeys(warnings)),
            research_feature_build_allowed=False,
            manual_decision_allowed=False,
            official_market_state_allowed=False,
            regime_label=None,
        )

    # 函数_latest_common_date：执行_latest_common_date逻辑。
    # - 参数results：类型Mapping[str, Any]；进入函数后按合同参与校验、筛选、计算或路由。
    # - 输出：返回类型date | None；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
    # - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
    # - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
    def _latest_common_date(
        self,
        results: Mapping[str, Any],
    ) -> date | None:
        # 字段或变量date_sets：声明类型list[set[date]]，初始逻辑为`[]`。
        # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
        # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
        date_sets: list[set[date]] = []
        # 迭代处理：依次从`self.feature_spec.required_source_datasets`读取元素，并绑定到`dataset_id`。
        # - 维度变化：每轮处理一个记录、字段、证据或配置项，可能向列表、字典或累计统计增加一项。
        # - 为什么这样写：显式逐项处理便于保留顺序、定位坏数据，并对每个实体执行同一合同。
        for dataset_id in self.feature_spec.required_source_datasets:
            # 变量更新：计算并保存gated，右侧逻辑为`results.get(dataset_id)`。
            # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
            # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
            gated = results.get(dataset_id)
            # 条件门禁：判断`gated is None`，条件为真时进入受保护分支。
            # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
            # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
            # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
            if gated is None:
                # 结果返回：把`None`交给调用方并结束当前函数。
                # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
                # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
                return None
            # 变量更新：计算并保存standard，右侧逻辑为`self._standard_result(gated)`。
            # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
            # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
            standard = self._standard_result(gated)
            # 变量更新：计算并保存dates，右侧逻辑为`{item for item in (_record_trade_date(record) for record in standard.records) if item is not None}`。
            # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
            # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
            dates = {
                item
                for item in (
                    _record_trade_date(record)
                    for record in standard.records
                )
                if item is not None
            }
            # 条件门禁：判断`not dates`，条件为真时进入受保护分支。
            # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
            # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
            # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
            if not dates:
                # 结果返回：把`None`交给调用方并结束当前函数。
                # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
                # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
                return None
            # API或函数调用：执行`date_sets.append`，完整调用片段为`date_sets.append(dates)`。
            # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
            # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
            # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
            date_sets.append(dates)
        # 变量更新：计算并保存common，右侧逻辑为`set.intersection(*date_sets)`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        common = set.intersection(*date_sets)
        # 结果返回：把`max(common) if common else None`交给调用方并结束当前函数。
        # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return max(common) if common else None

    # 函数_observe：执行_observe逻辑。
    # - 参数feature_id：类型str；进入函数后按合同参与校验、筛选、计算或路由。
    # - 参数value：类型float | None；进入函数后按合同参与校验、筛选、计算或路由。
    # - 关键字参数as_of_date：类型date，无默认值；只允许显式命名传入，降低参数错位风险。
    # - 关键字参数source_records：类型Sequence[Any]，无默认值；只允许显式命名传入，降低参数错位风险。
    # - 关键字参数valid_count：类型int，无默认值；只允许显式命名传入，降低参数错位风险。
    # - 关键字参数query_ids：类型tuple[str, ...]，无默认值；只允许显式命名传入，降低参数错位风险。
    # - 关键字参数warnings：类型Iterable[str]，默认值()；只允许显式命名传入，降低参数错位风险。
    # - 输出：返回类型MarketStateFeatureObservation | None；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
    # - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
    # - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
    def _observe(
        self,
        feature_id: str,
        value: float | None,
        *,
        as_of_date: date,
        source_records: Sequence[Any],
        valid_count: int,
        query_ids: tuple[str, ...],
        warnings: Iterable[str] = (),
    ) -> MarketStateFeatureObservation | None:
        # 变量更新：计算并保存definition，右侧逻辑为`self.feature_spec.definition(feature_id)`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        definition = self.feature_spec.definition(feature_id)
        # 条件门禁：判断`value is None`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if value is None:
            # 结果返回：把`None`交给调用方并结束当前函数。
            # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
            # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
            return None
        # 条件门禁：判断`valid_count < definition.minimum_observation_count`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if valid_count < definition.minimum_observation_count:
            # 结果返回：把`None`交给调用方并结束当前函数。
            # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
            # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
            return None
        # 变量更新：计算并保存source_count，右侧逻辑为`len(source_records)`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        source_count = len(source_records)
        # 结果返回：把`MarketStateFeatureObservation(feature_id=definition.feature_id, family=definition.family, value=flo…`交给调用方并结束当前函数。
        # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return MarketStateFeatureObservation(
            feature_id=definition.feature_id,
            family=definition.family,
            value=float(value),
            unit=definition.unit,
            as_of_date=as_of_date,
            formula=definition.formula,
            interpretation=definition.interpretation,
            source_dataset_ids=definition.source_dataset_ids,
            source_query_ids=query_ids,
            source_record_count=source_count,
            valid_observation_count=valid_count,
            missing_observation_count=max(
                source_count - valid_count,
                0,
            ),
            warnings=tuple(dict.fromkeys(warnings)),
        )

    # 函数calculate：执行calculate逻辑。
    # - 参数results：类型Mapping[str, Any]；进入函数后按合同参与校验、筛选、计算或路由。
    # - 输出：返回类型MarketStateFeatureSnapshot；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
    # - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
    # - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
    def calculate(
        self,
        results: Mapping[str, Any],
    ) -> MarketStateFeatureSnapshot:
        # 变量更新：计算并保存input_assessment，右侧逻辑为`self.input_engine.evaluate(results)`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        input_assessment = self.input_engine.evaluate(results)
        # 变量更新：计算并保存input_status，右侧逻辑为`input_assessment.status.value`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        input_status = input_assessment.status.value
        # 变量更新：计算并保存propagated_warnings，右侧逻辑为`list(input_assessment.warnings)`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        propagated_warnings = list(input_assessment.warnings)

        # 条件门禁：判断`input_assessment.blocks_downstream`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if input_assessment.blocks_downstream:
            # 变量更新：计算并保存missing，右侧逻辑为`[*input_assessment.missing_required_datasets, *input_assessment.blocked_datasets, *(family.value fo…`。
            # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
            # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
            missing = [
                *input_assessment.missing_required_datasets,
                *input_assessment.blocked_datasets,
                *(
                    family.value
                    for family in input_assessment.missing_feature_families
                ),
            ]
            # 结果返回：把`self._blocked_snapshot(input_status, propagated_warnings, missing)`交给调用方并结束当前函数。
            # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
            # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
            return self._blocked_snapshot(
                input_status,
                propagated_warnings,
                missing,
            )

        # 变量更新：计算并保存common_date，右侧逻辑为`self._latest_common_date(results)`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        common_date = self._latest_common_date(results)
        # 条件门禁：判断`common_date is None`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if common_date is None:
            # API或函数调用：执行`propagated_warnings.append`，完整调用片段为`propagated_warnings.append('NO_COMMON_TRADE_DATE_FOR_REQUIRED_DATASETS')`。
            # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
            # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
            # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
            propagated_warnings.append(
                "NO_COMMON_TRADE_DATE_FOR_REQUIRED_DATASETS"
            )
            # 结果返回：把`self._blocked_snapshot(input_status, propagated_warnings, ('LATEST_COMMON_TRADE_DATE',))`交给调用方并结束当前函数。
            # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
            # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
            return self._blocked_snapshot(
                input_status,
                propagated_warnings,
                ("LATEST_COMMON_TRADE_DATE",),
            )

        # 变量更新：计算并保存daily_result，右侧逻辑为`self._standard_result(results['a_stock_daily_k'])`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        daily_result = self._standard_result(
            results["a_stock_daily_k"]
        )
        # 变量更新：计算并保存industry_result，右侧逻辑为`self._standard_result(results['hy'])`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        industry_result = self._standard_result(results["hy"])
        # 变量更新：计算并保存daily_records，右侧逻辑为`_records_on_date(daily_result.records, common_date)`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        daily_records = _records_on_date(
            daily_result.records,
            common_date,
        )
        # 变量更新：计算并保存industry_records，右侧逻辑为`_records_on_date(industry_result.records, common_date)`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        industry_records = _records_on_date(
            industry_result.records,
            common_date,
        )
        # 变量更新：计算并保存daily_query_ids，右侧逻辑为`(daily_result.metadata.query_id,)`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        daily_query_ids = (daily_result.metadata.query_id,)
        # 变量更新：计算并保存industry_query_ids，右侧逻辑为`(industry_result.metadata.query_id,)`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        industry_query_ids = (industry_result.metadata.query_id,)

        # 字段或变量observations：声明类型list[MarketStateFeatureObservation]，初始逻辑为`[]`。
        # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
        # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
        observations: list[MarketStateFeatureObservation] = []

        # 变量更新：计算并保存daily_returns，右侧逻辑为`_numeric_values(daily_records, 'pct_change_pct')`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        daily_returns = _numeric_values(
            daily_records,
            "pct_change_pct",
        )
        # 变量更新：计算并保存amounts，右侧逻辑为`_numeric_values(daily_records, 'amount_cny')`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        amounts = _numeric_values(daily_records, "amount_cny")
        # 变量更新：计算并保存turnover_rates，右侧逻辑为`_numeric_values(daily_records, 'turnover_rate_pct')`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        turnover_rates = _numeric_values(
            daily_records,
            "turnover_rate_pct",
        )
        # 字段或变量intraday_ranges：声明类型list[float]，初始逻辑为`[]`。
        # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
        # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
        intraday_ranges: list[float] = []
        # 迭代处理：依次从`daily_records`读取元素，并绑定到`record`。
        # - 维度变化：每轮处理一个记录、字段、证据或配置项，可能向列表、字典或累计统计增加一项。
        # - 为什么这样写：显式逐项处理便于保留顺序、定位坏数据，并对每个实体执行同一合同。
        for record in daily_records:
            # 变量更新：计算并保存values，右侧逻辑为`record.values`。
            # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
            # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
            values = record.values
            # 变量更新：计算并保存high，右侧逻辑为`_to_float(values.get('high_raw_cny'))`。
            # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
            # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
            high = _to_float(values.get("high_raw_cny"))
            # 变量更新：计算并保存low，右侧逻辑为`_to_float(values.get('low_raw_cny'))`。
            # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
            # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
            low = _to_float(values.get("low_raw_cny"))
            # 变量更新：计算并保存close，右侧逻辑为`_to_float(values.get('close_raw_cny'))`。
            # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
            # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
            close = _to_float(values.get("close_raw_cny"))
            # 条件门禁：判断`high is not None and low is not None and (close is not None) and (close > 0) and (high >= low)`，条件为真时进入受保护分支。
            # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
            # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
            # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
            if (
                high is not None
                and low is not None
                and close is not None
                and close > 0
                and high >= low
            ):
                # API或函数调用：执行`intraday_ranges.append`，完整调用片段为`intraday_ranges.append((high - low) / close * 100.0)`。
                # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
                # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
                # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
                intraday_ranges.append(
                    (high - low) / close * 100.0
                )

        # 变量更新：计算并保存up_counts，右侧逻辑为`_numeric_values(industry_records, 'up_count')`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        up_counts = _numeric_values(industry_records, "up_count")
        # 变量更新：计算并保存down_counts，右侧逻辑为`_numeric_values(industry_records, 'down_count')`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        down_counts = _numeric_values(
            industry_records,
            "down_count",
        )
        # 变量更新：计算并保存limit_up_counts，右侧逻辑为`_numeric_values(industry_records, 'limit_up_count')`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        limit_up_counts = _numeric_values(
            industry_records,
            "limit_up_count",
        )
        # 变量更新：计算并保存breadth_ratios，右侧逻辑为`_numeric_values(industry_records, 'breadth_ratio')`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        breadth_ratios = _numeric_values(
            industry_records,
            "breadth_ratio",
        )
        # 变量更新：计算并保存industry_returns，右侧逻辑为`_numeric_values(industry_records, 'pct_change_pct')`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        industry_returns = _numeric_values(
            industry_records,
            "pct_change_pct",
        )
        # 变量更新：计算并保存average_returns，右侧逻辑为`_numeric_values(industry_records, 'average_return_pct')`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        average_returns = _numeric_values(
            industry_records,
            "average_return_pct",
        )

        # 函数add：执行add逻辑。
        # - 参数item：类型MarketStateFeatureObservation | None；进入函数后按合同参与校验、筛选、计算或路由。
        # - 输出：返回类型None；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
        # - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
        # - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
        def add(item: MarketStateFeatureObservation | None) -> None:
            # 条件门禁：判断`item is not None`，条件为真时进入受保护分支。
            # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
            # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
            # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
            if item is not None:
                # API或函数调用：执行`observations.append`，完整调用片段为`observations.append(item)`。
                # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
                # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
                # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
                observations.append(item)

        # API或函数调用：执行`add`，完整调用片段为`add(self._observe('daily_positive_return_ratio', sum((value > 0 for value in daily_returns)) / len(…`。
        # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
        # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
        # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
        add(self._observe(
            "daily_positive_return_ratio",
            (
                sum(value > 0 for value in daily_returns)
                / len(daily_returns)
                if daily_returns else None
            ),
            as_of_date=common_date,
            source_records=daily_records,
            valid_count=len(daily_returns),
            query_ids=daily_query_ids,
        ))
        # API或函数调用：执行`add`，完整调用片段为`add(self._observe('daily_mean_return_pct', statistics.fmean(daily_returns) if daily_returns else No…`。
        # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
        # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
        # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
        add(self._observe(
            "daily_mean_return_pct",
            statistics.fmean(daily_returns)
            if daily_returns else None,
            as_of_date=common_date,
            source_records=daily_records,
            valid_count=len(daily_returns),
            query_ids=daily_query_ids,
        ))
        # API或函数调用：执行`add`，完整调用片段为`add(self._observe('daily_median_return_pct', statistics.median(daily_returns) if daily_returns else…`。
        # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
        # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
        # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
        add(self._observe(
            "daily_median_return_pct",
            statistics.median(daily_returns)
            if daily_returns else None,
            as_of_date=common_date,
            source_records=daily_records,
            valid_count=len(daily_returns),
            query_ids=daily_query_ids,
        ))

        # 变量更新：计算并保存total_up，右侧逻辑为`sum(up_counts)`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        total_up = sum(up_counts)
        # 变量更新：计算并保存total_down，右侧逻辑为`sum(down_counts)`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        total_down = sum(down_counts)
        # 变量更新：计算并保存comparable_total，右侧逻辑为`total_up + total_down`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        comparable_total = total_up + total_down
        # 变量更新：计算并保存breadth_valid_count，右侧逻辑为`min(len(up_counts), len(down_counts))`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        breadth_valid_count = min(
            len(up_counts),
            len(down_counts),
        )
        # API或函数调用：执行`add`，完整调用片段为`add(self._observe('industry_advance_ratio', total_up / comparable_total if comparable_total > 0 els…`。
        # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
        # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
        # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
        add(self._observe(
            "industry_advance_ratio",
            total_up / comparable_total
            if comparable_total > 0 else None,
            as_of_date=common_date,
            source_records=industry_records,
            valid_count=breadth_valid_count,
            query_ids=industry_query_ids,
        ))
        # API或函数调用：执行`add`，完整调用片段为`add(self._observe('industry_breadth_ratio_median', statistics.median(breadth_ratios) if breadth_rat…`。
        # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
        # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
        # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
        add(self._observe(
            "industry_breadth_ratio_median",
            statistics.median(breadth_ratios)
            if breadth_ratios else None,
            as_of_date=common_date,
            source_records=industry_records,
            valid_count=len(breadth_ratios),
            query_ids=industry_query_ids,
        ))
        # 字段或变量limit_share_warnings：声明类型list[str]，初始逻辑为`[]`。
        # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
        # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
        limit_share_warnings: list[str] = []
        # 条件门禁：判断`total_up > 0`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if total_up > 0:
            # 变量更新：计算并保存limit_share，右侧逻辑为`sum(limit_up_counts) / total_up`。
            # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
            # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
            limit_share = sum(limit_up_counts) / total_up
        # 条件门禁：判断`up_counts and limit_up_counts`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        elif up_counts and limit_up_counts:
            # 变量更新：计算并保存limit_share，右侧逻辑为`0.0`。
            # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
            # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
            limit_share = 0.0
            # API或函数调用：执行`limit_share_warnings.append`，完整调用片段为`limit_share_warnings.append('ZERO_TOTAL_UP_COUNT_INTERPRETED_AS_ZERO_SHARE')`。
            # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
            # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
            # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
            limit_share_warnings.append(
                "ZERO_TOTAL_UP_COUNT_INTERPRETED_AS_ZERO_SHARE"
            )
        else:
            # 变量更新：计算并保存limit_share，右侧逻辑为`None`。
            # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
            # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
            limit_share = None
        # API或函数调用：执行`add`，完整调用片段为`add(self._observe('industry_limit_up_share_of_up', limit_share, as_of_date=common_date, source_reco…`。
        # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
        # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
        # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
        add(self._observe(
            "industry_limit_up_share_of_up",
            limit_share,
            as_of_date=common_date,
            source_records=industry_records,
            valid_count=min(len(limit_up_counts), len(up_counts)),
            query_ids=industry_query_ids,
            warnings=limit_share_warnings,
        ))

        # API或函数调用：执行`add`，完整调用片段为`add(self._observe('market_amount_total_cny', sum(amounts) if amounts else None, as_of_date=common_d…`。
        # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
        # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
        # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
        add(self._observe(
            "market_amount_total_cny",
            sum(amounts) if amounts else None,
            as_of_date=common_date,
            source_records=daily_records,
            valid_count=len(amounts),
            query_ids=daily_query_ids,
            warnings=(
                "QUERY_UNIVERSE_TOTAL_NOT_PROVEN_FULL_MARKET",
            ),
        ))
        # API或函数调用：执行`add`，完整调用片段为`add(self._observe('turnover_rate_median_pct', statistics.median(turnover_rates) if turnover_rates e…`。
        # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
        # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
        # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
        add(self._observe(
            "turnover_rate_median_pct",
            statistics.median(turnover_rates)
            if turnover_rates else None,
            as_of_date=common_date,
            source_records=daily_records,
            valid_count=len(turnover_rates),
            query_ids=daily_query_ids,
        ))
        # API或函数调用：执行`add`，完整调用片段为`add(self._observe('amount_field_coverage_ratio', len(amounts) / len(daily_records) if daily_records…`。
        # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
        # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
        # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
        add(self._observe(
            "amount_field_coverage_ratio",
            len(amounts) / len(daily_records)
            if daily_records else None,
            as_of_date=common_date,
            source_records=daily_records,
            valid_count=len(amounts),
            query_ids=daily_query_ids,
        ))

        # API或函数调用：执行`add`，完整调用片段为`add(self._observe('cross_section_return_std_pct', statistics.pstdev(daily_returns) if len(daily_ret…`。
        # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
        # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
        # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
        add(self._observe(
            "cross_section_return_std_pct",
            statistics.pstdev(daily_returns)
            if len(daily_returns) >= 2 else None,
            as_of_date=common_date,
            source_records=daily_records,
            valid_count=len(daily_returns),
            query_ids=daily_query_ids,
        ))
        # API或函数调用：执行`add`，完整调用片段为`add(self._observe('intraday_range_median_pct', statistics.median(intraday_ranges) if intraday_range…`。
        # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
        # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
        # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
        add(self._observe(
            "intraday_range_median_pct",
            statistics.median(intraday_ranges)
            if intraday_ranges else None,
            as_of_date=common_date,
            source_records=daily_records,
            valid_count=len(intraday_ranges),
            query_ids=daily_query_ids,
        ))
        # 变量更新：计算并保存absolute_returns，右侧逻辑为`[abs(value) for value in daily_returns]`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        absolute_returns = [abs(value) for value in daily_returns]
        # API或函数调用：执行`add`，完整调用片段为`add(self._observe('absolute_return_median_pct', statistics.median(absolute_returns) if absolute_ret…`。
        # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
        # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
        # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
        add(self._observe(
            "absolute_return_median_pct",
            statistics.median(absolute_returns)
            if absolute_returns else None,
            as_of_date=common_date,
            source_records=daily_records,
            valid_count=len(absolute_returns),
            query_ids=daily_query_ids,
        ))

        # API或函数调用：执行`add`，完整调用片段为`add(self._observe('positive_industry_ratio', sum((value > 0 for value in industry_returns)) / len(i…`。
        # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
        # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
        # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
        add(self._observe(
            "positive_industry_ratio",
            (
                sum(value > 0 for value in industry_returns)
                / len(industry_returns)
                if industry_returns else None
            ),
            as_of_date=common_date,
            source_records=industry_records,
            valid_count=len(industry_returns),
            query_ids=industry_query_ids,
        ))
        # API或函数调用：执行`add`，完整调用片段为`add(self._observe('industry_return_std_pct', statistics.pstdev(industry_returns) if len(industry_re…`。
        # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
        # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
        # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
        add(self._observe(
            "industry_return_std_pct",
            statistics.pstdev(industry_returns)
            if len(industry_returns) >= 2 else None,
            as_of_date=common_date,
            source_records=industry_records,
            valid_count=len(industry_returns),
            query_ids=industry_query_ids,
        ))
        # API或函数调用：执行`add`，完整调用片段为`add(self._observe('positive_average_return_ratio', sum((value > 0 for value in average_returns)) / …`。
        # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
        # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
        # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
        add(self._observe(
            "positive_average_return_ratio",
            (
                sum(value > 0 for value in average_returns)
                / len(average_returns)
                if average_returns else None
            ),
            as_of_date=common_date,
            source_records=industry_records,
            valid_count=len(average_returns),
            query_ids=industry_query_ids,
        ))

        # 变量更新：计算并保存observed_ids，右侧逻辑为`{item.feature_id for item in observations}`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        observed_ids = {item.feature_id for item in observations}
        # 变量更新：计算并保存required_ids，右侧逻辑为`{item.feature_id for item in self.feature_spec.feature_definitions if item.family in self.feature_s…`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        required_ids = {
            item.feature_id
            for item in self.feature_spec.feature_definitions
            if item.family in self.feature_spec.required_feature_families
        }
        # 变量更新：计算并保存missing，右侧逻辑为`tuple(sorted(required_ids - observed_ids))`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        missing = tuple(sorted(required_ids - observed_ids))

        # 条件门禁：判断`missing`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if missing:
            # 变量更新：计算并保存status，右侧逻辑为`MarketStateFeatureStatus.BLOCKED`。
            # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
            # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
            status = MarketStateFeatureStatus.BLOCKED
            # API或函数调用：执行`propagated_warnings.append`，完整调用片段为`propagated_warnings.append('REQUIRED_FEATURES_MISSING_OR_INSUFFICIENT')`。
            # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
            # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
            # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
            propagated_warnings.append(
                "REQUIRED_FEATURES_MISSING_OR_INSUFFICIENT"
            )
            # 变量更新：计算并保存research_allowed，右侧逻辑为`False`。
            # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
            # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
            research_allowed = False
        # 条件门禁：判断`input_assessment.status is MarketStateInputStatus.READY_WITH_WARNINGS or propagated_warnings or any…`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        elif (
            input_assessment.status
            is MarketStateInputStatus.READY_WITH_WARNINGS
            or propagated_warnings
            or any(item.warnings for item in observations)
        ):
            # 变量更新：计算并保存status，右侧逻辑为`MarketStateFeatureStatus.READY_WITH_WARNINGS`。
            # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
            # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
            status = MarketStateFeatureStatus.READY_WITH_WARNINGS
            # 变量更新：计算并保存research_allowed，右侧逻辑为`True`。
            # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
            # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
            research_allowed = True
        else:
            # 变量更新：计算并保存status，右侧逻辑为`MarketStateFeatureStatus.READY`。
            # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
            # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
            status = MarketStateFeatureStatus.READY
            # 变量更新：计算并保存research_allowed，右侧逻辑为`True`。
            # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
            # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
            research_allowed = True

        # 结果返回：把`MarketStateFeatureSnapshot(status=status, feature_spec_version=self.feature_spec.spec_version, inpu…`交给调用方并结束当前函数。
        # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return MarketStateFeatureSnapshot(
            status=status,
            feature_spec_version=self.feature_spec.spec_version,
            input_contract_version=(
                self.feature_spec.input_contract_version
            ),
            usage=self.feature_spec.allowed_usage,
            as_of_date=common_date,
            input_assessment_status=input_status,
            features=tuple(observations),
            missing_required_features=missing,
            warnings=tuple(dict.fromkeys(propagated_warnings)),
            research_feature_build_allowed=research_allowed,
            manual_decision_allowed=False,
            official_market_state_allowed=False,
            regime_label=None,
        )
