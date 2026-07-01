# 模块总览：统一标准数据服务接口与标准查询结果合同。
# - 输入输出：本模块通过强类型合同、纯函数和显式服务调用交换数据，不在导入阶段执行数据库写入或交易动作。
# - 数据变化：只有显式构造、校验、查询、证据组合或报告导出才产生新对象与受控状态。
# - 时点与安全：就绪度和市场状态相关逻辑必须保留usage、as_of、available_at、血缘与阻断信息。
# - 为什么这样写：先声明模块边界，读者可以在阅读实现前理解职责、风险、数值语义和可复用方式。
"""统一标准数据服务接口与标准查询结果合同。

本模块位于数据集专属标准化服务和下游业务模块之间。

目标：
1. 下游不直接调用 DolphinDB 或任何来源专属查询接口；
2. 所有数据集通过统一 Provider 接入；
3. 查询请求显式携带数据集、标准对象、实体选择器、日期和时点边界；
4. 查询结果统一携带覆盖版本、映射版本、字典版本、质量和血缘；
5. 日K只是第一个 Provider，后续基本面和七类快照复用同一合同。

本模块不负责写入数据库，也不负责因子、策略和回测。
"""

# 依赖导入：执行`from __future__ import annotations`，加载下方合同、类型或标准库能力。
# - 数据变化：导入只把模块、类或函数绑定到当前命名空间，不在本行主动查询数据库或修改业务数据。
# - 为什么这样写：显式依赖使模块边界、可替换组件和测试注入点保持清晰。
from __future__ import annotations

# 依赖导入：执行`from abc import ABC, abstractmethod`，加载下方合同、类型或标准库能力。
# - 数据变化：导入只把模块、类或函数绑定到当前命名空间，不在本行主动查询数据库或修改业务数据。
# - 为什么这样写：显式依赖使模块边界、可替换组件和测试注入点保持清晰。
from abc import ABC, abstractmethod
# 依赖导入：执行`from dataclasses import asdict, dataclass, field`，加载下方合同、类型或标准库能力。
# - 数据变化：导入只把模块、类或函数绑定到当前命名空间，不在本行主动查询数据库或修改业务数据。
# - 为什么这样写：显式依赖使模块边界、可替换组件和测试注入点保持清晰。
from dataclasses import asdict, dataclass, field
# 依赖导入：执行`from datetime import date, datetime, timezone`，加载下方合同、类型或标准库能力。
# - 数据变化：导入只把模块、类或函数绑定到当前命名空间，不在本行主动查询数据库或修改业务数据。
# - 为什么这样写：显式依赖使模块边界、可替换组件和测试注入点保持清晰。
from datetime import date, datetime, timezone
# 依赖导入：执行`from enum import Enum`，加载下方合同、类型或标准库能力。
# - 数据变化：导入只把模块、类或函数绑定到当前命名空间，不在本行主动查询数据库或修改业务数据。
# - 为什么这样写：显式依赖使模块边界、可替换组件和测试注入点保持清晰。
from enum import Enum
# 依赖导入：执行`from typing import Any, Iterable`，加载下方合同、类型或标准库能力。
# - 数据变化：导入只把模块、类或函数绑定到当前命名空间，不在本行主动查询数据库或修改业务数据。
# - 为什么这样写：显式依赖使模块边界、可替换组件和测试注入点保持清晰。
from typing import Any, Iterable
# 依赖导入：执行`from uuid import uuid4`，加载下方合同、类型或标准库能力。
# - 数据变化：导入只把模块、类或函数绑定到当前命名空间，不在本行主动查询数据库或修改业务数据。
# - 为什么这样写：显式依赖使模块边界、可替换组件和测试注入点保持清晰。
from uuid import uuid4

# 依赖导入：执行`from .data_contracts import ( DataContractError, QualityStatus,`，加载下方合同、类型或标准库能力。
# - 数据变化：导入只把模块、类或函数绑定到当前命名空间，不在本行主动查询数据库或修改业务数据。
# - 为什么这样写：显式依赖使模块边界、可替换组件和测试注入点保持清晰。
from .data_contracts import (
    DataContractError,
    QualityStatus,
)


# 关键常量STANDARD_QUERY_CONTRACT_VERSION：把`'0.2.0'`固定为本模块可追踪的合同值。
# - 来源：该值来自当前项目任务合同、配置或真实验收口径；未标注为行业标准时不得外推为通用值。
# - 数据范围：字符串常量用于版本、状态或模式标识；数值常量的单位和有效范围由相邻校验与调用语义约束。
# - 实操示例：报告和下游对象携带该值后，可以判断生产者版本并复现实验或验收过程。
# - 为什么这样写：集中命名固定参数可避免魔法值散落，并让配置升级、审计和兼容性检查有明确锚点。
STANDARD_QUERY_CONTRACT_VERSION = "0.2.0"
# 关键常量INSTRUMENT_SELECTOR_MODE：把`'INSTRUMENT_ID'`固定为本模块可追踪的合同值。
# - 来源：该值来自当前项目任务合同、配置或真实验收口径；未标注为行业标准时不得外推为通用值。
# - 数据范围：字符串常量用于版本、状态或模式标识；数值常量的单位和有效范围由相邻校验与调用语义约束。
# - 实操示例：报告和下游对象携带该值后，可以判断生产者版本并复现实验或验收过程。
# - 为什么这样写：集中命名固定参数可避免魔法值散落，并让配置升级、审计和兼容性检查有明确锚点。
INSTRUMENT_SELECTOR_MODE = "INSTRUMENT_ID"
# 关键常量ENTITY_SELECTOR_MODE：把`'ENTITY_ID'`固定为本模块可追踪的合同值。
# - 来源：该值来自当前项目任务合同、配置或真实验收口径；未标注为行业标准时不得外推为通用值。
# - 数据范围：字符串常量用于版本、状态或模式标识；数值常量的单位和有效范围由相邻校验与调用语义约束。
# - 实操示例：报告和下游对象携带该值后，可以判断生产者版本并复现实验或验收过程。
# - 为什么这样写：集中命名固定参数可避免魔法值散落，并让配置升级、审计和兼容性检查有明确锚点。
ENTITY_SELECTOR_MODE = "ENTITY_ID"
# 变量更新：计算并保存_ALLOWED_SELECTOR_MODES，右侧逻辑为`frozenset({INSTRUMENT_SELECTOR_MODE, ENTITY_SELECTOR_MODE})`。
# - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
# - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
_ALLOWED_SELECTOR_MODES = frozenset(
    {INSTRUMENT_SELECTOR_MODE, ENTITY_SELECTOR_MODE}
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
        # 错误阻断：抛出`DataContractError(f'{field_name} 不能为空。')`并停止当前正常路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
        # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
        raise DataContractError(f"{field_name} 不能为空。")

    # 结果返回：把`value.strip()`交给调用方并结束当前函数。
    # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return value.strip()


# 函数_normalise_unique_texts：执行_normalise_unique_texts逻辑。
# - 参数values：类型Iterable[str]；进入函数后按合同参与校验、筛选、计算或路由。
# - 参数field_name：类型str；进入函数后按合同参与校验、筛选、计算或路由。
# - 关键字参数allow_empty：类型bool，默认值False；只允许显式命名传入，降低参数错位风险。
# - 输出：返回类型tuple[str, ...]；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
# - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
# - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
def _normalise_unique_texts(
    values: Iterable[str],
    field_name: str,
    *,
    allow_empty: bool = False,
) -> tuple[str, ...]:
    # 变量更新：计算并保存normalised，右侧逻辑为`tuple((_require_text(value, field_name) for value in values))`。
    # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
    # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
    normalised = tuple(
        _require_text(value, field_name)
        for value in values
    )

    # 条件门禁：判断`not allow_empty and (not normalised)`，条件为真时进入受保护分支。
    # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
    # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
    # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
    if not allow_empty and not normalised:
        # 错误阻断：抛出`DataContractError(f'{field_name} 至少包含一个值。')`并停止当前正常路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
        # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
        raise DataContractError(
            f"{field_name} 至少包含一个值。"
        )

    # 条件门禁：判断`len(set(normalised)) != len(normalised)`，条件为真时进入受保护分支。
    # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
    # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
    # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
    if len(set(normalised)) != len(normalised):
        # 错误阻断：抛出`DataContractError(f'{field_name} 不允许重复。')`并停止当前正常路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
        # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
        raise DataContractError(
            f"{field_name} 不允许重复。"
        )

    # 结果返回：把`normalised`交给调用方并结束当前函数。
    # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return normalised


# 函数_json_safe：执行_json_safe逻辑。
# - 参数value：类型Any；进入函数后按合同参与校验、筛选、计算或路由。
# - 输出：返回类型Any；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
# - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
# - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
def _json_safe(value: Any) -> Any:
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

    # 条件门禁：判断`isinstance(value, dict)`，条件为真时进入受保护分支。
    # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
    # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
    # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
    if isinstance(value, dict):
        # 结果返回：把`{str(key): _json_safe(item) for key, item in value.items()}`交给调用方并结束当前函数。
        # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return {
            str(key): _json_safe(item)
            for key, item in value.items()
        }

    # 条件门禁：判断`isinstance(value, (list, tuple, set, frozenset))`，条件为真时进入受保护分支。
    # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
    # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
    # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
    if isinstance(value, (list, tuple, set, frozenset)):
        # 结果返回：把`[_json_safe(item) for item in value]`交给调用方并结束当前函数。
        # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return [_json_safe(item) for item in value]

    # 结果返回：把`value`交给调用方并结束当前函数。
    # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return value


# 类StandardDataUsage：标准数据的用途级时点门禁枚举。
# - 继承边界：基类为str, Enum；类体包含约4个字段或常量、0个方法。
# - 数据变化：类定义本身不执行隐式I/O，实例只在构造、校验或显式方法调用时产生受控状态。
# - 实操示例：调用方先构造该类型，再由方法完成校验、证据组合、路由或结果导出。
# - 为什么这样写：强类型边界能把相关不变量集中管理，减少字典键拼写、状态漂移和跨模块耦合。
class StandardDataUsage(str, Enum):
    """标准数据的用途级时点门禁枚举。"""

    # 关键常量CURRENT_SNAPSHOT_RESEARCH：把`'CURRENT_SNAPSHOT_RESEARCH'`固定为本模块可追踪的合同值。
    # - 来源：该值来自当前项目任务合同、配置或真实验收口径；未标注为行业标准时不得外推为通用值。
    # - 数据范围：字符串常量用于版本、状态或模式标识；数值常量的单位和有效范围由相邻校验与调用语义约束。
    # - 实操示例：报告和下游对象携带该值后，可以判断生产者版本并复现实验或验收过程。
    # - 为什么这样写：集中命名固定参数可避免魔法值散落，并让配置升级、审计和兼容性检查有明确锚点。
    CURRENT_SNAPSHOT_RESEARCH = (
        "CURRENT_SNAPSHOT_RESEARCH"
    )
    # 关键常量MANUAL_DECISION_SUPPORT：把`'MANUAL_DECISION_SUPPORT'`固定为本模块可追踪的合同值。
    # - 来源：该值来自当前项目任务合同、配置或真实验收口径；未标注为行业标准时不得外推为通用值。
    # - 数据范围：字符串常量用于版本、状态或模式标识；数值常量的单位和有效范围由相邻校验与调用语义约束。
    # - 实操示例：报告和下游对象携带该值后，可以判断生产者版本并复现实验或验收过程。
    # - 为什么这样写：集中命名固定参数可避免魔法值散落，并让配置升级、审计和兼容性检查有明确锚点。
    MANUAL_DECISION_SUPPORT = (
        "MANUAL_DECISION_SUPPORT"
    )
    # 关键常量STRICT_HISTORICAL_BACKTEST：把`'STRICT_HISTORICAL_BACKTEST'`固定为本模块可追踪的合同值。
    # - 来源：该值来自当前项目任务合同、配置或真实验收口径；未标注为行业标准时不得外推为通用值。
    # - 数据范围：字符串常量用于版本、状态或模式标识；数值常量的单位和有效范围由相邻校验与调用语义约束。
    # - 实操示例：报告和下游对象携带该值后，可以判断生产者版本并复现实验或验收过程。
    # - 为什么这样写：集中命名固定参数可避免魔法值散落，并让配置升级、审计和兼容性检查有明确锚点。
    STRICT_HISTORICAL_BACKTEST = (
        "STRICT_HISTORICAL_BACKTEST"
    )
    # 关键常量HISTORICAL_MODEL_TRAINING：把`'HISTORICAL_MODEL_TRAINING'`固定为本模块可追踪的合同值。
    # - 来源：该值来自当前项目任务合同、配置或真实验收口径；未标注为行业标准时不得外推为通用值。
    # - 数据范围：字符串常量用于版本、状态或模式标识；数值常量的单位和有效范围由相邻校验与调用语义约束。
    # - 实操示例：报告和下游对象携带该值后，可以判断生产者版本并复现实验或验收过程。
    # - 为什么这样写：集中命名固定参数可避免魔法值散落，并让配置升级、审计和兼容性检查有明确锚点。
    HISTORICAL_MODEL_TRAINING = (
        "HISTORICAL_MODEL_TRAINING"
    )


# 类StandardDataQuery：来源无关的标准数据查询请求。
# - 继承边界：基类为object；类体包含约14个字段或常量、4个方法。
# - 数据变化：类定义本身不执行隐式I/O，实例只在构造、校验或显式方法调用时产生受控状态。
# - 实操示例：调用方先构造该类型，再由方法完成校验、证据组合、路由或结果导出。
# - 为什么这样写：强类型边界能把相关不变量集中管理，减少字典键拼写、状态漂移和跨模块耦合。
@dataclass(frozen=True, slots=True)
class StandardDataQuery:
    """来源无关的标准数据查询请求。

    as_of_date 是最小的时点安全门禁：
    查询结束日期不得晚于该日期。后续基本面 Provider 仍需基于
    公告日期或 available_at 执行更严格的可见性过滤。
    """

    # 字段或变量dataset_id：声明类型str，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    dataset_id: str
    # 字段或变量canonical_object：声明类型str，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    canonical_object: str
    # 字段或变量instrument_ids：声明类型tuple[str, ...]，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    instrument_ids: tuple[str, ...]
    # 字段或变量start_date：声明类型date，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    start_date: date
    # 字段或变量end_date：声明类型date，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    end_date: date
    # 字段或变量fields：声明类型tuple[str, ...]，初始逻辑为`()`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    fields: tuple[str, ...] = ()
    # 字段或变量entity_ids：声明类型tuple[str, ...]，初始逻辑为`()`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    entity_ids: tuple[str, ...] = ()
    # 字段或变量as_of_date：声明类型date | None，初始逻辑为`None`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    as_of_date: date | None = None
    # 字段或变量usage：声明类型StandardDataUsage，初始逻辑为`StandardDataUsage.CURRENT_SNAPSHOT_RESEARCH`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    usage: StandardDataUsage = (
        StandardDataUsage.CURRENT_SNAPSHOT_RESEARCH
    )
    # 字段或变量decision_time：声明类型datetime | None，初始逻辑为`None`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    decision_time: datetime | None = None
    # 字段或变量limit_per_instrument：声明类型int，初始逻辑为`5000`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    limit_per_instrument: int = 5_000
    # 字段或变量include_source_extensions：声明类型bool，初始逻辑为`False`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    include_source_extensions: bool = False
    # 字段或变量include_quality_flags：声明类型bool，初始逻辑为`True`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    include_quality_flags: bool = True
    # 字段或变量include_lineage：声明类型bool，初始逻辑为`True`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    include_lineage: bool = True

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
        # API或函数调用：执行`object.__setattr__`，完整调用片段为`object.__setattr__(self, 'instrument_ids', _normalise_unique_texts(self.instrument_ids, 'instrument…`。
        # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
        # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
        # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
        object.__setattr__(
            self,
            "instrument_ids",
            _normalise_unique_texts(
                self.instrument_ids,
                "instrument_ids",
                allow_empty=True,
            ),
        )
        # API或函数调用：执行`object.__setattr__`，完整调用片段为`object.__setattr__(self, 'entity_ids', _normalise_unique_texts(self.entity_ids, 'entity_ids', allow…`。
        # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
        # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
        # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
        object.__setattr__(
            self,
            "entity_ids",
            _normalise_unique_texts(
                self.entity_ids,
                "entity_ids",
                allow_empty=True,
            ),
        )

        # 条件门禁：判断`bool(self.instrument_ids) == bool(self.entity_ids)`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if bool(self.instrument_ids) == bool(self.entity_ids):
            # 错误阻断：抛出`DataContractError('instrument_ids 与 entity_ids 必须且只能提供一种。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
            raise DataContractError(
                "instrument_ids 与 entity_ids 必须且只能提供一种。"
            )

        # API或函数调用：执行`object.__setattr__`，完整调用片段为`object.__setattr__(self, 'fields', _normalise_unique_texts(self.fields, 'fields', allow_empty=True))`。
        # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
        # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
        # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
        object.__setattr__(
            self,
            "fields",
            _normalise_unique_texts(
                self.fields,
                "fields",
                allow_empty=True,
            ),
        )

        # 条件门禁：判断`not isinstance(self.start_date, date)`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if not isinstance(self.start_date, date):
            # 错误阻断：抛出`DataContractError('start_date 必须是 date。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
            raise DataContractError(
                "start_date 必须是 date。"
            )

        # 条件门禁：判断`not isinstance(self.end_date, date)`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if not isinstance(self.end_date, date):
            # 错误阻断：抛出`DataContractError('end_date 必须是 date。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
            raise DataContractError(
                "end_date 必须是 date。"
            )

        # 条件门禁：判断`self.start_date > self.end_date`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if self.start_date > self.end_date:
            # 错误阻断：抛出`DataContractError('start_date 不能晚于 end_date。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
            raise DataContractError(
                "start_date 不能晚于 end_date。"
            )

        # 变量更新：计算并保存resolved_as_of，右侧逻辑为`self.as_of_date or self.end_date`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        resolved_as_of = self.as_of_date or self.end_date

        # 条件门禁：判断`not isinstance(resolved_as_of, date)`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if not isinstance(resolved_as_of, date):
            # 错误阻断：抛出`DataContractError('as_of_date 必须是 date。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
            raise DataContractError(
                "as_of_date 必须是 date。"
            )

        # 条件门禁：判断`self.end_date > resolved_as_of`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if self.end_date > resolved_as_of:
            # 错误阻断：抛出`DataContractError('end_date 不能晚于 as_of_date，否则会形成未来数据查询。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
            raise DataContractError(
                "end_date 不能晚于 as_of_date，"
                "否则会形成未来数据查询。"
            )

        # API或函数调用：执行`object.__setattr__`，完整调用片段为`object.__setattr__(self, 'as_of_date', resolved_as_of)`。
        # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
        # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
        # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
        object.__setattr__(
            self,
            "as_of_date",
            resolved_as_of,
        )

        # 变量更新：计算并保存resolved_usage，右侧逻辑为`self.usage`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        resolved_usage = self.usage
        # 条件门禁：判断`isinstance(resolved_usage, str)`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if isinstance(resolved_usage, str):
            # 异常边界：执行可能失败的解析、转换、文件读取或外部调用，并在后续分支转换为项目统一错误。
            # - 数据变化：成功路径产生正常结果；失败路径保留原异常作为cause、降级为缺失值或记录明确问题。
            # - 为什么这样写：上层只需处理稳定的DataContractError或受控结果，不依赖第三方异常实现细节。
            try:
                # 变量更新：计算并保存resolved_usage，右侧逻辑为`StandardDataUsage(resolved_usage)`。
                # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
                # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
                resolved_usage = StandardDataUsage(
                    resolved_usage
                )
            # 异常转换：捕获ValueError，保存上下文并执行统一错误、回退或忽略策略。
            # - 数据变化：异常路径不返回未校验的半成品；必要时把失败原因写入issues、warnings或异常链。
            # - 为什么这样写：明确捕获范围可避免吞掉程序错误，同时让调用方获得稳定且可审计的失败语义。
            except ValueError as exc:
                # 错误阻断：抛出`DataContractError('usage 不是受支持的数据用途。')`并停止当前正常路径。
                # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
                # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
                raise DataContractError(
                    "usage 不是受支持的数据用途。"
                ) from exc

        # 条件门禁：判断`not isinstance(resolved_usage, StandardDataUsage)`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if not isinstance(
            resolved_usage,
            StandardDataUsage,
        ):
            # 错误阻断：抛出`DataContractError('usage 必须是 StandardDataUsage。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
            raise DataContractError(
                "usage 必须是 StandardDataUsage。"
            )

        # API或函数调用：执行`object.__setattr__`，完整调用片段为`object.__setattr__(self, 'usage', resolved_usage)`。
        # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
        # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
        # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
        object.__setattr__(
            self,
            "usage",
            resolved_usage,
        )

        # 条件门禁：判断`resolved_usage is StandardDataUsage.MANUAL_DECISION_SUPPORT and self.decision_time is None`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if (
            resolved_usage
            is StandardDataUsage.MANUAL_DECISION_SUPPORT
            and self.decision_time is None
        ):
            # 错误阻断：抛出`DataContractError('MANUAL_DECISION_SUPPORT必须提供decision_time。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
            raise DataContractError(
                "MANUAL_DECISION_SUPPORT必须提供decision_time。"
            )

        # 条件门禁：判断`self.decision_time is not None`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if self.decision_time is not None:
            # 条件门禁：判断`not isinstance(self.decision_time, datetime)`，条件为真时进入受保护分支。
            # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
            # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
            # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
            if not isinstance(self.decision_time, datetime):
                # 错误阻断：抛出`DataContractError('decision_time 必须是 datetime。')`并停止当前正常路径。
                # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
                # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
                raise DataContractError(
                    "decision_time 必须是 datetime。"
                )

            # 条件门禁：判断`self.decision_time.tzinfo is None or self.decision_time.utcoffset() is None`，条件为真时进入受保护分支。
            # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
            # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
            # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
            if (
                self.decision_time.tzinfo is None
                or self.decision_time.utcoffset() is None
            ):
                # 错误阻断：抛出`DataContractError('decision_time 必须携带时区。')`并停止当前正常路径。
                # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
                # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
                raise DataContractError(
                    "decision_time 必须携带时区。"
                )

            # 条件门禁：判断`self.decision_time.date() < resolved_as_of`，条件为真时进入受保护分支。
            # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
            # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
            # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
            if self.decision_time.date() < resolved_as_of:
                # 错误阻断：抛出`DataContractError('decision_time 的日期不能早于 as_of_date。')`并停止当前正常路径。
                # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
                # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
                raise DataContractError(
                    "decision_time 的日期不能早于 as_of_date。"
                )

        # 条件门禁：判断`not isinstance(self.limit_per_instrument, int) or not 1 <= self.limit_per_instrument <= 5000`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if (
            not isinstance(self.limit_per_instrument, int)
            or not 1 <= self.limit_per_instrument <= 5_000
        ):
            # 错误阻断：抛出`DataContractError('limit_per_instrument 必须是1到5000之间的整数。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
            raise DataContractError(
                "limit_per_instrument 必须是1到5000之间的整数。"
            )

    # 函数selector_mode：执行selector_mode逻辑。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态、模块常量或封装依赖。
    # - 输出：返回类型str；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
    # - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
    # - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
    @property
    def selector_mode(self) -> str:
        # 结果返回：把`INSTRUMENT_SELECTOR_MODE if self.instrument_ids else ENTITY_SELECTOR_MODE`交给调用方并结束当前函数。
        # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return (
            INSTRUMENT_SELECTOR_MODE
            if self.instrument_ids
            else ENTITY_SELECTOR_MODE
        )

    # 函数selector_ids：执行selector_ids逻辑。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态、模块常量或封装依赖。
    # - 输出：返回类型tuple[str, ...]；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
    # - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
    # - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
    @property
    def selector_ids(self) -> tuple[str, ...]:
        # 结果返回：把`self.instrument_ids or self.entity_ids`交给调用方并结束当前函数。
        # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return self.instrument_ids or self.entity_ids

    # 函数to_dict：执行to_dict逻辑。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态、模块常量或封装依赖。
    # - 输出：返回类型dict[str, Any]；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
    # - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
    # - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
    def to_dict(self) -> dict[str, Any]:
        # 结果返回：把`_json_safe(asdict(self))`交给调用方并结束当前函数。
        # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return _json_safe(asdict(self))


# 类StandardDataRecord：一个标准对象记录。
# - 继承边界：基类为object；类体包含约7个字段或常量、2个方法。
# - 数据变化：类定义本身不执行隐式I/O，实例只在构造、校验或显式方法调用时产生受控状态。
# - 实操示例：调用方先构造该类型，再由方法完成校验、证据组合、路由或结果导出。
# - 为什么这样写：强类型边界能把相关不变量集中管理，减少字典键拼写、状态漂移和跨模块耦合。
@dataclass(frozen=True, slots=True)
class StandardDataRecord:
    """一个标准对象记录。"""

    # 字段或变量canonical_object：声明类型str，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    canonical_object: str
    # 字段或变量primary_key：声明类型dict[str, Any]，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    primary_key: dict[str, Any]
    # 字段或变量values：声明类型dict[str, Any]，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    values: dict[str, Any]
    # 字段或变量source_record_id：声明类型str | None，初始逻辑为`None`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    source_record_id: str | None = None
    # 字段或变量source_extensions：声明类型dict[str, Any]，初始逻辑为`field(default_factory=dict)`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    source_extensions: dict[str, Any] = field(
        default_factory=dict
    )
    # 字段或变量quality_flags：声明类型tuple[str, ...]，初始逻辑为`()`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    quality_flags: tuple[str, ...] = ()
    # 字段或变量lineage：声明类型tuple[dict[str, Any], ...]，初始逻辑为`()`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    lineage: tuple[dict[str, Any], ...] = ()

    # 函数__post_init__：执行__post_init__逻辑。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态、模块常量或封装依赖。
    # - 输出：返回类型None；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
    # - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
    # - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
    def __post_init__(self) -> None:
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

        # 条件门禁：判断`not self.primary_key`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if not self.primary_key:
            # 错误阻断：抛出`DataContractError('标准记录必须包含 primary_key。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
            raise DataContractError(
                "标准记录必须包含 primary_key。"
            )

        # 条件门禁：判断`not isinstance(self.values, dict)`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if not isinstance(self.values, dict):
            # 错误阻断：抛出`DataContractError('values 必须是字典。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
            raise DataContractError(
                "values 必须是字典。"
            )

        # 条件门禁：判断`self.source_record_id is not None`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if self.source_record_id is not None:
            # API或函数调用：执行`object.__setattr__`，完整调用片段为`object.__setattr__(self, 'source_record_id', _require_text(self.source_record_id, 'source_record_id…`。
            # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
            # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
            # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
            object.__setattr__(
                self,
                "source_record_id",
                _require_text(
                    self.source_record_id,
                    "source_record_id",
                ),
            )

        # API或函数调用：执行`object.__setattr__`，完整调用片段为`object.__setattr__(self, 'quality_flags', _normalise_unique_texts(self.quality_flags, 'quality_flag…`。
        # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
        # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
        # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
        object.__setattr__(
            self,
            "quality_flags",
            _normalise_unique_texts(
                self.quality_flags,
                "quality_flags",
                allow_empty=True,
            ),
        )

    # 函数to_dict：执行to_dict逻辑。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态、模块常量或封装依赖。
    # - 输出：返回类型dict[str, Any]；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
    # - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
    # - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
    def to_dict(self) -> dict[str, Any]:
        # 结果返回：把`_json_safe(asdict(self))`交给调用方并结束当前函数。
        # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return _json_safe(asdict(self))


# 类StandardQueryMetadata：标准查询结果的版本、质量和血缘摘要。
# - 继承边界：基类为object；类体包含约15个字段或常量、2个方法。
# - 数据变化：类定义本身不执行隐式I/O，实例只在构造、校验或显式方法调用时产生受控状态。
# - 实操示例：调用方先构造该类型，再由方法完成校验、证据组合、路由或结果导出。
# - 为什么这样写：强类型边界能把相关不变量集中管理，减少字典键拼写、状态漂移和跨模块耦合。
@dataclass(frozen=True, slots=True)
class StandardQueryMetadata:
    """标准查询结果的版本、质量和血缘摘要。"""

    # 字段或变量dataset_id：声明类型str，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    dataset_id: str
    # 字段或变量canonical_object：声明类型str，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    canonical_object: str
    # 字段或变量provider_id：声明类型str，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    provider_id: str
    # 字段或变量coverage_version：声明类型str，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    coverage_version: str
    # 字段或变量mapping_version：声明类型str，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    mapping_version: str
    # 字段或变量dictionary_revision：声明类型str，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    dictionary_revision: str
    # 字段或变量source_row_count：声明类型int，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    source_row_count: int
    # 字段或变量result_count：声明类型int，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    result_count: int
    # 字段或变量status：声明类型QualityStatus，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    status: QualityStatus
    # 字段或变量blocks_downstream：声明类型bool，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    blocks_downstream: bool
    # 字段或变量warnings：声明类型tuple[str, ...]，初始逻辑为`()`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    warnings: tuple[str, ...] = ()
    # 字段或变量quality_flag_counts：声明类型dict[str, int]，初始逻辑为`field(default_factory=dict)`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    quality_flag_counts: dict[str, int] = field(
        default_factory=dict
    )
    # 字段或变量lineage_item_count：声明类型int，初始逻辑为`0`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    lineage_item_count: int = 0
    # 字段或变量query_id：声明类型str，初始逻辑为`field(default_factory=lambda: str(uuid4()))`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    query_id: str = field(
        default_factory=lambda: str(uuid4())
    )
    # 字段或变量generated_at：声明类型datetime，初始逻辑为`field(default_factory=lambda: datetime.now(timezone.utc))`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    generated_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    # 函数__post_init__：执行__post_init__逻辑。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态、模块常量或封装依赖。
    # - 输出：返回类型None；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
    # - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
    # - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
    def __post_init__(self) -> None:
        # 迭代处理：依次从`('dataset_id', 'canonical_object', 'provider_id', 'coverage_version', 'mapping_version', 'dictionar…`读取元素，并绑定到`field_name`。
        # - 维度变化：每轮处理一个记录、字段、证据或配置项，可能向列表、字典或累计统计增加一项。
        # - 为什么这样写：显式逐项处理便于保留顺序、定位坏数据，并对每个实体执行同一合同。
        for field_name in (
            "dataset_id",
            "canonical_object",
            "provider_id",
            "coverage_version",
            "mapping_version",
            "dictionary_revision",
            "query_id",
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

        # 条件门禁：判断`self.source_row_count < 0`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if self.source_row_count < 0:
            # 错误阻断：抛出`DataContractError('source_row_count 不能为负数。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
            raise DataContractError(
                "source_row_count 不能为负数。"
            )

        # 条件门禁：判断`self.result_count < 0`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if self.result_count < 0:
            # 错误阻断：抛出`DataContractError('result_count 不能为负数。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
            raise DataContractError(
                "result_count 不能为负数。"
            )

        # 条件门禁：判断`self.lineage_item_count < 0`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if self.lineage_item_count < 0:
            # 错误阻断：抛出`DataContractError('lineage_item_count 不能为负数。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
            raise DataContractError(
                "lineage_item_count 不能为负数。"
            )

        # 条件门禁：判断`self.status is QualityStatus.PASSED and self.blocks_downstream`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if (
            self.status is QualityStatus.PASSED
            and self.blocks_downstream
        ):
            # 错误阻断：抛出`DataContractError('PASSED 查询不能阻断下游。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
            raise DataContractError(
                "PASSED 查询不能阻断下游。"
            )

        # API或函数调用：执行`object.__setattr__`，完整调用片段为`object.__setattr__(self, 'warnings', tuple((_require_text(item, 'warnings') for item in self.warnin…`。
        # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
        # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
        # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
        object.__setattr__(
            self,
            "warnings",
            tuple(
                _require_text(item, "warnings")
                for item in self.warnings
            ),
        )

    # 函数to_dict：执行to_dict逻辑。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态、模块常量或封装依赖。
    # - 输出：返回类型dict[str, Any]；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
    # - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
    # - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
    def to_dict(self) -> dict[str, Any]:
        # 结果返回：把`_json_safe(asdict(self))`交给调用方并结束当前函数。
        # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return _json_safe(asdict(self))


# 类StandardQueryResult：统一标准查询结果合同。
# - 继承边界：基类为object；类体包含约3个字段或常量、3个方法。
# - 数据变化：类定义本身不执行隐式I/O，实例只在构造、校验或显式方法调用时产生受控状态。
# - 实操示例：调用方先构造该类型，再由方法完成校验、证据组合、路由或结果导出。
# - 为什么这样写：强类型边界能把相关不变量集中管理，减少字典键拼写、状态漂移和跨模块耦合。
@dataclass(frozen=True, slots=True)
class StandardQueryResult:
    """统一标准查询结果合同。"""

    # 字段或变量query：声明类型StandardDataQuery，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    query: StandardDataQuery
    # 字段或变量metadata：声明类型StandardQueryMetadata，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    metadata: StandardQueryMetadata
    # 字段或变量records：声明类型tuple[StandardDataRecord, ...]，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    records: tuple[StandardDataRecord, ...]

    # 函数__post_init__：执行__post_init__逻辑。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态、模块常量或封装依赖。
    # - 输出：返回类型None；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
    # - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
    # - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
    def __post_init__(self) -> None:
        # 条件门禁：判断`self.metadata.dataset_id != self.query.dataset_id`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if self.metadata.dataset_id != self.query.dataset_id:
            # 错误阻断：抛出`DataContractError('查询与结果的 dataset_id 不一致。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
            raise DataContractError(
                "查询与结果的 dataset_id 不一致。"
            )

        # 条件门禁：判断`self.metadata.canonical_object != self.query.canonical_object`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if (
            self.metadata.canonical_object
            != self.query.canonical_object
        ):
            # 错误阻断：抛出`DataContractError('查询与结果的 canonical_object 不一致。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
            raise DataContractError(
                "查询与结果的 canonical_object 不一致。"
            )

        # 条件门禁：判断`self.metadata.result_count != len(self.records)`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if self.metadata.result_count != len(self.records):
            # 错误阻断：抛出`DataContractError('metadata.result_count 与 records 数量不一致。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
            raise DataContractError(
                "metadata.result_count 与 records 数量不一致。"
            )

        # 变量更新：计算并保存invalid_objects，右侧逻辑为`sorted({record.canonical_object for record in self.records if record.canonical_object != self.query…`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        invalid_objects = sorted(
            {
                record.canonical_object
                for record in self.records
                if record.canonical_object
                != self.query.canonical_object
            }
        )

        # 条件门禁：判断`invalid_objects`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if invalid_objects:
            # 错误阻断：抛出`DataContractError(f'结果中存在不匹配的标准对象：{invalid_objects}')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
            raise DataContractError(
                "结果中存在不匹配的标准对象："
                f"{invalid_objects}"
            )

    # 函数assert_usable：执行assert_usable逻辑。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态、模块常量或封装依赖。
    # - 输出：返回类型None；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
    # - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
    # - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
    def assert_usable(self) -> None:
        # 条件门禁：判断`self.metadata.blocks_downstream`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if self.metadata.blocks_downstream:
            # 错误阻断：抛出`DataContractError('标准查询结果被质量门禁阻断。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
            raise DataContractError(
                "标准查询结果被质量门禁阻断。"
            )

    # 函数to_dict：执行to_dict逻辑。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态、模块常量或封装依赖。
    # - 输出：返回类型dict[str, Any]；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
    # - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
    # - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
    def to_dict(self) -> dict[str, Any]:
        # 结果返回：把`{'query': self.query.to_dict(), 'metadata': self.metadata.to_dict(), 'records': [record.to_dict() f…`交给调用方并结束当前函数。
        # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return {
            "query": self.query.to_dict(),
            "metadata": self.metadata.to_dict(),
            "records": [
                record.to_dict()
                for record in self.records
            ],
        }


# 类ProviderDescriptor：标准数据 Provider 的公开描述。
# - 继承边界：基类为object；类体包含约7个字段或常量、2个方法。
# - 数据变化：类定义本身不执行隐式I/O，实例只在构造、校验或显式方法调用时产生受控状态。
# - 实操示例：调用方先构造该类型，再由方法完成校验、证据组合、路由或结果导出。
# - 为什么这样写：强类型边界能把相关不变量集中管理，减少字典键拼写、状态漂移和跨模块耦合。
@dataclass(frozen=True, slots=True)
class ProviderDescriptor:
    """标准数据 Provider 的公开描述。"""

    # 字段或变量provider_id：声明类型str，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    provider_id: str
    # 字段或变量dataset_id：声明类型str，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    dataset_id: str
    # 字段或变量supported_objects：声明类型tuple[str, ...]，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    supported_objects: tuple[str, ...]
    # 字段或变量coverage_version：声明类型str，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    coverage_version: str
    # 字段或变量mapping_version：声明类型str，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    mapping_version: str
    # 字段或变量dictionary_revision：声明类型str，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    dictionary_revision: str
    # 字段或变量selector_mode：声明类型str，初始逻辑为`INSTRUMENT_SELECTOR_MODE`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    selector_mode: str = INSTRUMENT_SELECTOR_MODE

    # 函数__post_init__：执行__post_init__逻辑。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态、模块常量或封装依赖。
    # - 输出：返回类型None；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
    # - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
    # - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
    def __post_init__(self) -> None:
        # 迭代处理：依次从`('provider_id', 'dataset_id', 'coverage_version', 'mapping_version', 'dictionary_revision')`读取元素，并绑定到`field_name`。
        # - 维度变化：每轮处理一个记录、字段、证据或配置项，可能向列表、字典或累计统计增加一项。
        # - 为什么这样写：显式逐项处理便于保留顺序、定位坏数据，并对每个实体执行同一合同。
        for field_name in (
            "provider_id",
            "dataset_id",
            "coverage_version",
            "mapping_version",
            "dictionary_revision",
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

        # API或函数调用：执行`object.__setattr__`，完整调用片段为`object.__setattr__(self, 'supported_objects', _normalise_unique_texts(self.supported_objects, 'supp…`。
        # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
        # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
        # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
        object.__setattr__(
            self,
            "supported_objects",
            _normalise_unique_texts(
                self.supported_objects,
                "supported_objects",
            ),
        )

        # 变量更新：计算并保存selector_mode，右侧逻辑为`_require_text(self.selector_mode, 'selector_mode').upper()`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        selector_mode = _require_text(
            self.selector_mode,
            "selector_mode",
        ).upper()
        # 条件门禁：判断`selector_mode not in _ALLOWED_SELECTOR_MODES`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if selector_mode not in _ALLOWED_SELECTOR_MODES:
            # 错误阻断：抛出`DataContractError('selector_mode 只支持 INSTRUMENT_ID 或 ENTITY_ID。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
            raise DataContractError(
                "selector_mode 只支持 INSTRUMENT_ID 或 ENTITY_ID。"
            )
        # API或函数调用：执行`object.__setattr__`，完整调用片段为`object.__setattr__(self, 'selector_mode', selector_mode)`。
        # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
        # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
        # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
        object.__setattr__(
            self,
            "selector_mode",
            selector_mode,
        )

    # 函数to_dict：执行to_dict逻辑。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态、模块常量或封装依赖。
    # - 输出：返回类型dict[str, Any]；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
    # - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
    # - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
    def to_dict(self) -> dict[str, Any]:
        # 结果返回：把`_json_safe(asdict(self))`交给调用方并结束当前函数。
        # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return _json_safe(asdict(self))


# 类StandardDatasetProvider：数据集专属标准化服务的统一 Provider 接口。
# - 继承边界：基类为ABC；类体包含约0个字段或常量、2个方法。
# - 数据变化：类定义本身不执行隐式I/O，实例只在构造、校验或显式方法调用时产生受控状态。
# - 实操示例：调用方先构造该类型，再由方法完成校验、证据组合、路由或结果导出。
# - 为什么这样写：强类型边界能把相关不变量集中管理，减少字典键拼写、状态漂移和跨模块耦合。
class StandardDatasetProvider(ABC):
    """数据集专属标准化服务的统一 Provider 接口。"""

    # 函数descriptor：执行descriptor逻辑。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态、模块常量或封装依赖。
    # - 输出：返回类型ProviderDescriptor；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
    # - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
    # - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
    @property
    @abstractmethod
    def descriptor(self) -> ProviderDescriptor:
        # 错误阻断：抛出`NotImplementedError`并停止当前正常路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
        # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
        raise NotImplementedError

    # 函数query：执行query逻辑。
    # - 参数request：类型StandardDataQuery；进入函数后按合同参与校验、筛选、计算或路由。
    # - 输出：返回类型StandardQueryResult；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
    # - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
    # - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
    @abstractmethod
    def query(
        self,
        request: StandardDataQuery,
    ) -> StandardQueryResult:
        # 错误阻断：抛出`NotImplementedError`并停止当前正常路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
        # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
        raise NotImplementedError


# 类StandardDataService：面向所有下游模块的统一标准数据入口。
# - 继承边界：基类为object；类体包含约0个字段或常量、5个方法。
# - 数据变化：类定义本身不执行隐式I/O，实例只在构造、校验或显式方法调用时产生受控状态。
# - 实操示例：调用方先构造该类型，再由方法完成校验、证据组合、路由或结果导出。
# - 为什么这样写：强类型边界能把相关不变量集中管理，减少字典键拼写、状态漂移和跨模块耦合。
class StandardDataService:
    """面向所有下游模块的统一标准数据入口。"""

    # 函数__init__：执行__init__逻辑。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态、模块常量或封装依赖。
    # - 输出：返回类型None；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
    # - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
    # - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
    def __init__(self) -> None:
        # 字段或变量self._providers：声明类型dict[str, StandardDatasetProvider]，初始逻辑为`{}`。
        # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
        # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
        self._providers: dict[
            str,
            StandardDatasetProvider,
        ] = {}

    # 函数register_provider：执行register_provider逻辑。
    # - 参数provider：类型StandardDatasetProvider；进入函数后按合同参与校验、筛选、计算或路由。
    # - 关键字参数replace：类型bool，默认值False；只允许显式命名传入，降低参数错位风险。
    # - 输出：返回类型None；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
    # - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
    # - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
    def register_provider(
        self,
        provider: StandardDatasetProvider,
        *,
        replace: bool = False,
    ) -> None:
        # 变量更新：计算并保存descriptor，右侧逻辑为`provider.descriptor`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        descriptor = provider.descriptor
        # 变量更新：计算并保存dataset_id，右侧逻辑为`descriptor.dataset_id`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        dataset_id = descriptor.dataset_id

        # 条件门禁：判断`dataset_id in self._providers and (not replace)`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if dataset_id in self._providers and not replace:
            # 错误阻断：抛出`DataContractError(f'数据集 Provider 已注册：{dataset_id}')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
            raise DataContractError(
                f"数据集 Provider 已注册：{dataset_id}"
            )

        # 变量更新：计算并保存self._providers[dataset_id]，右侧逻辑为`provider`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        self._providers[dataset_id] = provider

    # 函数list_datasets：执行list_datasets逻辑。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态、模块常量或封装依赖。
    # - 输出：返回类型tuple[ProviderDescriptor, ...]；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
    # - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
    # - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
    def list_datasets(self) -> tuple[ProviderDescriptor, ...]:
        # 结果返回：把`tuple((self._providers[key].descriptor for key in sorted(self._providers)))`交给调用方并结束当前函数。
        # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return tuple(
            self._providers[key].descriptor
            for key in sorted(self._providers)
        )

    # 函数get_provider：执行get_provider逻辑。
    # - 参数dataset_id：类型str；进入函数后按合同参与校验、筛选、计算或路由。
    # - 输出：返回类型StandardDatasetProvider；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
    # - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
    # - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
    def get_provider(
        self,
        dataset_id: str,
    ) -> StandardDatasetProvider:
        # 变量更新：计算并保存key，右侧逻辑为`_require_text(dataset_id, 'dataset_id')`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        key = _require_text(dataset_id, "dataset_id")

        # 异常边界：执行可能失败的解析、转换、文件读取或外部调用，并在后续分支转换为项目统一错误。
        # - 数据变化：成功路径产生正常结果；失败路径保留原异常作为cause、降级为缺失值或记录明确问题。
        # - 为什么这样写：上层只需处理稳定的DataContractError或受控结果，不依赖第三方异常实现细节。
        try:
            # 结果返回：把`self._providers[key]`交给调用方并结束当前函数。
            # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
            # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
            return self._providers[key]
        # 异常转换：捕获KeyError，保存上下文并执行统一错误、回退或忽略策略。
        # - 数据变化：异常路径不返回未校验的半成品；必要时把失败原因写入issues、warnings或异常链。
        # - 为什么这样写：明确捕获范围可避免吞掉程序错误，同时让调用方获得稳定且可审计的失败语义。
        except KeyError as exc:
            # 错误阻断：抛出`DataContractError(f'未注册标准数据 Provider：{key}')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
            raise DataContractError(
                f"未注册标准数据 Provider：{key}"
            ) from exc

    # 函数query：执行query逻辑。
    # - 参数request：类型StandardDataQuery；进入函数后按合同参与校验、筛选、计算或路由。
    # - 输出：返回类型StandardQueryResult；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
    # - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
    # - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
    def query(
        self,
        request: StandardDataQuery,
    ) -> StandardQueryResult:
        # 变量更新：计算并保存provider，右侧逻辑为`self.get_provider(request.dataset_id)`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        provider = self.get_provider(request.dataset_id)
        # 变量更新：计算并保存descriptor，右侧逻辑为`provider.descriptor`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        descriptor = provider.descriptor

        # 条件门禁：判断`request.selector_mode != descriptor.selector_mode`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if request.selector_mode != descriptor.selector_mode:
            # 错误阻断：抛出`DataContractError(f'查询实体选择器与 Provider 不一致：query={request.selector_mode}, provider={descriptor.selec…`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
            raise DataContractError(
                "查询实体选择器与 Provider 不一致："
                f"query={request.selector_mode}, "
                f"provider={descriptor.selector_mode}"
            )

        # 条件门禁：判断`request.canonical_object not in descriptor.supported_objects`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if (
            request.canonical_object
            not in descriptor.supported_objects
        ):
            # 错误阻断：抛出`DataContractError(f'Provider 不支持标准对象：{request.canonical_object}')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
            raise DataContractError(
                "Provider 不支持标准对象："
                f"{request.canonical_object}"
            )

        # 变量更新：计算并保存result，右侧逻辑为`provider.query(request)`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        result = provider.query(request)

        # 条件门禁：判断`result.metadata.dataset_id != request.dataset_id`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if result.metadata.dataset_id != request.dataset_id:
            # 错误阻断：抛出`DataContractError('Provider 返回了错误的数据集。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
            raise DataContractError(
                "Provider 返回了错误的数据集。"
            )

        # 结果返回：把`result`交给调用方并结束当前函数。
        # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return result
