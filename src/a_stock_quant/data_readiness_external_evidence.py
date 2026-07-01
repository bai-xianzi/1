# 模块总览：真实报告、交易日时效和启用配置到统一就绪度证据的覆盖层。
# - 输入输出：本模块通过强类型合同、纯函数和显式服务调用交换数据，不在导入阶段执行数据库写入或交易动作。
# - 数据变化：只有显式构造、校验、查询、证据组合或报告导出才产生新对象与受控状态。
# - 时点与安全：就绪度和市场状态相关逻辑必须保留usage、as_of、available_at、血缘与阻断信息。
# - 为什么这样写：先声明模块边界，读者可以在阅读实现前理解职责、风险、数值语义和可复用方式。
"""真实报告、交易日时效和启用配置到统一就绪度证据的覆盖层。

TASK_018B 已经能够从 StandardQueryResult 生成八维证据，但其中覆盖、
数据集级时效和生产启用状态需要独立证据。本模块只读取仓库内已提交的
JSON 报告和启用配置，将 COVERAGE、FRESHNESS、ACTIVATION 三个维度
替换为可审计的真实外部证据。

本模块不连接 DolphinDB，不读取 Raw 表，不执行数据库写入。
"""

# 依赖导入：执行`from __future__ import annotations`，加载下方合同、类型或标准库能力。
# - 数据变化：导入只把模块、类或函数绑定到当前命名空间，不在本行主动查询数据库或修改业务数据。
# - 为什么这样写：显式依赖使模块边界、可替换组件和测试注入点保持清晰。
from __future__ import annotations

# 依赖导入：执行`from dataclasses import dataclass`，加载下方合同、类型或标准库能力。
# - 数据变化：导入只把模块、类或函数绑定到当前命名空间，不在本行主动查询数据库或修改业务数据。
# - 为什么这样写：显式依赖使模块边界、可替换组件和测试注入点保持清晰。
from dataclasses import dataclass
# 依赖导入：执行`from datetime import date, timedelta`，加载下方合同、类型或标准库能力。
# - 数据变化：导入只把模块、类或函数绑定到当前命名空间，不在本行主动查询数据库或修改业务数据。
# - 为什么这样写：显式依赖使模块边界、可替换组件和测试注入点保持清晰。
from datetime import date, timedelta
# 依赖导入：执行`from enum import Enum`，加载下方合同、类型或标准库能力。
# - 数据变化：导入只把模块、类或函数绑定到当前命名空间，不在本行主动查询数据库或修改业务数据。
# - 为什么这样写：显式依赖使模块边界、可替换组件和测试注入点保持清晰。
from enum import Enum
# 依赖导入：执行`import json`，加载下方合同、类型或标准库能力。
# - 数据变化：导入只把模块、类或函数绑定到当前命名空间，不在本行主动查询数据库或修改业务数据。
# - 为什么这样写：显式依赖使模块边界、可替换组件和测试注入点保持清晰。
import json
# 依赖导入：执行`from pathlib import Path`，加载下方合同、类型或标准库能力。
# - 数据变化：导入只把模块、类或函数绑定到当前命名空间，不在本行主动查询数据库或修改业务数据。
# - 为什么这样写：显式依赖使模块边界、可替换组件和测试注入点保持清晰。
from pathlib import Path
# 依赖导入：执行`import re`，加载下方合同、类型或标准库能力。
# - 数据变化：导入只把模块、类或函数绑定到当前命名空间，不在本行主动查询数据库或修改业务数据。
# - 为什么这样写：显式依赖使模块边界、可替换组件和测试注入点保持清晰。
import re
# 依赖导入：执行`from typing import Any, Iterable, Mapping`，加载下方合同、类型或标准库能力。
# - 数据变化：导入只把模块、类或函数绑定到当前命名空间，不在本行主动查询数据库或修改业务数据。
# - 为什么这样写：显式依赖使模块边界、可替换组件和测试注入点保持清晰。
from typing import Any, Iterable, Mapping

# 依赖导入：执行`from .data_contracts import DataContractError`，加载下方合同、类型或标准库能力。
# - 数据变化：导入只把模块、类或函数绑定到当前命名空间，不在本行主动查询数据库或修改业务数据。
# - 为什么这样写：显式依赖使模块边界、可替换组件和测试注入点保持清晰。
from .data_contracts import DataContractError
# 依赖导入：执行`from .data_readiness import ( EvidenceStatus, ReadinessDimension,`，加载下方合同、类型或标准库能力。
# - 数据变化：导入只把模块、类或函数绑定到当前命名空间，不在本行主动查询数据库或修改业务数据。
# - 为什么这样写：显式依赖使模块边界、可替换组件和测试注入点保持清晰。
from .data_readiness import (
    EvidenceStatus,
    ReadinessDimension,
    ReadinessEvidence,
)
# 依赖导入：执行`from .data_readiness_evidence import ( EvidenceBuildContext, StandardQueryEvidenceBuilder,`，加载下方合同、类型或标准库能力。
# - 数据变化：导入只把模块、类或函数绑定到当前命名空间，不在本行主动查询数据库或修改业务数据。
# - 为什么这样写：显式依赖使模块边界、可替换组件和测试注入点保持清晰。
from .data_readiness_evidence import (
    EvidenceBuildContext,
    StandardQueryEvidenceBuilder,
)
# 依赖导入：执行`from .standard_data_service import ( ProviderDescriptor, StandardDataUsage,`，加载下方合同、类型或标准库能力。
# - 数据变化：导入只把模块、类或函数绑定到当前命名空间，不在本行主动查询数据库或修改业务数据。
# - 为什么这样写：显式依赖使模块边界、可替换组件和测试注入点保持清晰。
from .standard_data_service import (
    ProviderDescriptor,
    StandardDataUsage,
    StandardQueryResult,
)

# 关键常量EXTERNAL_EVIDENCE_VERSION：把`'0.1.0'`固定为本模块可追踪的合同值。
# - 来源：该值来自当前项目任务合同、配置或真实验收口径；未标注为行业标准时不得外推为通用值。
# - 数据范围：字符串常量用于版本、状态或模式标识；数值常量的单位和有效范围由相邻校验与调用语义约束。
# - 实操示例：报告和下游对象携带该值后，可以判断生产者版本并复现实验或验收过程。
# - 为什么这样写：集中命名固定参数可避免魔法值散落，并让配置升级、审计和兼容性检查有明确锚点。
EXTERNAL_EVIDENCE_VERSION = "0.1.0"


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


# 函数_parse_date：执行_parse_date逻辑。
# - 参数value：类型Any；进入函数后按合同参与校验、筛选、计算或路由。
# - 参数field_name：类型str；进入函数后按合同参与校验、筛选、计算或路由。
# - 输出：返回类型date；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
# - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
# - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
def _parse_date(value: Any, field_name: str) -> date:
    # 条件门禁：判断`isinstance(value, date)`，条件为真时进入受保护分支。
    # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
    # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
    # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
    if isinstance(value, date):
        # 结果返回：把`value`交给调用方并结束当前函数。
        # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return value
    # 条件门禁：判断`not isinstance(value, str) or not value.strip()`，条件为真时进入受保护分支。
    # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
    # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
    # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
    if not isinstance(value, str) or not value.strip():
        # 错误阻断：抛出`DataContractError(f'{field_name}不是有效日期。')`并停止当前正常路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
        # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
        raise DataContractError(f"{field_name}不是有效日期。")
    # 异常边界：执行可能失败的解析、转换、文件读取或外部调用，并在后续分支转换为项目统一错误。
    # - 数据变化：成功路径产生正常结果；失败路径保留原异常作为cause、降级为缺失值或记录明确问题。
    # - 为什么这样写：上层只需处理稳定的DataContractError或受控结果，不依赖第三方异常实现细节。
    try:
        # 结果返回：把`date.fromisoformat(value.strip()[:10])`交给调用方并结束当前函数。
        # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return date.fromisoformat(value.strip()[:10])
    # 异常转换：捕获ValueError，保存上下文并执行统一错误、回退或忽略策略。
    # - 数据变化：异常路径不返回未校验的半成品；必要时把失败原因写入issues、warnings或异常链。
    # - 为什么这样写：明确捕获范围可避免吞掉程序错误，同时让调用方获得稳定且可审计的失败语义。
    except ValueError as exc:
        # 错误阻断：抛出`DataContractError(f'{field_name}不是ISO日期：{value}')`并停止当前正常路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
        # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
        raise DataContractError(
            f"{field_name}不是ISO日期：{value}"
        ) from exc


# 函数_load_json：执行_load_json逻辑。
# - 参数path：类型Path；进入函数后按合同参与校验、筛选、计算或路由。
# - 输出：返回类型dict[str, Any]；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
# - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
# - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
def _load_json(path: Path) -> dict[str, Any]:
    # 异常边界：执行可能失败的解析、转换、文件读取或外部调用，并在后续分支转换为项目统一错误。
    # - 数据变化：成功路径产生正常结果；失败路径保留原异常作为cause、降级为缺失值或记录明确问题。
    # - 为什么这样写：上层只需处理稳定的DataContractError或受控结果，不依赖第三方异常实现细节。
    try:
        # 变量更新：计算并保存payload，右侧逻辑为`json.loads(path.read_text(encoding='utf-8'))`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        payload = json.loads(path.read_text(encoding="utf-8"))
    # 异常转换：捕获(OSError, json.JSONDecodeError)，保存上下文并执行统一错误、回退或忽略策略。
    # - 数据变化：异常路径不返回未校验的半成品；必要时把失败原因写入issues、warnings或异常链。
    # - 为什么这样写：明确捕获范围可避免吞掉程序错误，同时让调用方获得稳定且可审计的失败语义。
    except (OSError, json.JSONDecodeError) as exc:
        # 错误阻断：抛出`DataContractError(f'无法加载JSON：{path}')`并停止当前正常路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
        # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
        raise DataContractError(f"无法加载JSON：{path}") from exc
    # 条件门禁：判断`not isinstance(payload, dict)`，条件为真时进入受保护分支。
    # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
    # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
    # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
    if not isinstance(payload, dict):
        # 错误阻断：抛出`DataContractError(f'JSON根节点必须是对象：{path}')`并停止当前正常路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
        # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
        raise DataContractError(f"JSON根节点必须是对象：{path}")
    # 结果返回：把`payload`交给调用方并结束当前函数。
    # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return payload


# 函数_json_path：执行_json_path逻辑。
# - 参数payload：类型Mapping[str, Any]；进入函数后按合同参与校验、筛选、计算或路由。
# - 参数path：类型str；进入函数后按合同参与校验、筛选、计算或路由。
# - 输出：返回类型Any；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
# - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
# - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
def _json_path(
    payload: Mapping[str, Any],
    path: str,
) -> Any:
    # 字段或变量current：声明类型Any，初始逻辑为`payload`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    current: Any = payload
    # 迭代处理：依次从`_require_text(path, 'json_path').split('.')`读取元素，并绑定到`part`。
    # - 维度变化：每轮处理一个记录、字段、证据或配置项，可能向列表、字典或累计统计增加一项。
    # - 为什么这样写：显式逐项处理便于保留顺序、定位坏数据，并对每个实体执行同一合同。
    for part in _require_text(path, "json_path").split("."):
        # 条件门禁：判断`not isinstance(current, Mapping) or part not in current`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if not isinstance(current, Mapping) or part not in current:
            # 错误阻断：抛出`DataContractError(f'报告缺少JSON路径：{path}')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
            raise DataContractError(
                f"报告缺少JSON路径：{path}"
            )
        # 变量更新：计算并保存current，右侧逻辑为`current[part]`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        current = current[part]
    # 结果返回：把`current`交给调用方并结束当前函数。
    # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return current


# 类ReportKind：封装ReportKind相关状态、字段与行为。
# - 继承边界：基类为str, Enum；类体包含约3个字段或常量、0个方法。
# - 数据变化：类定义本身不执行隐式I/O，实例只在构造、校验或显式方法调用时产生受控状态。
# - 实操示例：调用方先构造该类型，再由方法完成校验、证据组合、路由或结果导出。
# - 为什么这样写：强类型边界能把相关不变量集中管理，减少字典键拼写、状态漂移和跨模块耦合。
class ReportKind(str, Enum):
    # 关键常量DAILY_K_COVERAGE：把`'DAILY_K_COVERAGE'`固定为本模块可追踪的合同值。
    # - 来源：该值来自当前项目任务合同、配置或真实验收口径；未标注为行业标准时不得外推为通用值。
    # - 数据范围：字符串常量用于版本、状态或模式标识；数值常量的单位和有效范围由相邻校验与调用语义约束。
    # - 实操示例：报告和下游对象携带该值后，可以判断生产者版本并复现实验或验收过程。
    # - 为什么这样写：集中命名固定参数可避免魔法值散落，并让配置升级、审计和兼容性检查有明确锚点。
    DAILY_K_COVERAGE = "DAILY_K_COVERAGE"
    # 关键常量FUNDAMENTAL_PROFILE：把`'FUNDAMENTAL_PROFILE'`固定为本模块可追踪的合同值。
    # - 来源：该值来自当前项目任务合同、配置或真实验收口径；未标注为行业标准时不得外推为通用值。
    # - 数据范围：字符串常量用于版本、状态或模式标识；数值常量的单位和有效范围由相邻校验与调用语义约束。
    # - 实操示例：报告和下游对象携带该值后，可以判断生产者版本并复现实验或验收过程。
    # - 为什么这样写：集中命名固定参数可避免魔法值散落，并让配置升级、审计和兼容性检查有明确锚点。
    FUNDAMENTAL_PROFILE = "FUNDAMENTAL_PROFILE"
    # 关键常量DAILY_FUNDS_ACCEPTANCE：把`'DAILY_FUNDS_ACCEPTANCE'`固定为本模块可追踪的合同值。
    # - 来源：该值来自当前项目任务合同、配置或真实验收口径；未标注为行业标准时不得外推为通用值。
    # - 数据范围：字符串常量用于版本、状态或模式标识；数值常量的单位和有效范围由相邻校验与调用语义约束。
    # - 实操示例：报告和下游对象携带该值后，可以判断生产者版本并复现实验或验收过程。
    # - 为什么这样写：集中命名固定参数可避免魔法值散落，并让配置升级、审计和兼容性检查有明确锚点。
    DAILY_FUNDS_ACCEPTANCE = "DAILY_FUNDS_ACCEPTANCE"


# 类TradingCalendar：A股交易日日历；周末关闭，节假日由权威配置给出。
# - 继承边界：基类为object；类体包含约5个字段或常量、4个方法。
# - 数据变化：类定义本身不执行隐式I/O，实例只在构造、校验或显式方法调用时产生受控状态。
# - 实操示例：调用方先构造该类型，再由方法完成校验、证据组合、路由或结果导出。
# - 为什么这样写：强类型边界能把相关不变量集中管理，减少字典键拼写、状态漂移和跨模块耦合。
@dataclass(frozen=True, slots=True)
class TradingCalendar:
    """A股交易日日历；周末关闭，节假日由权威配置给出。"""

    # 字段或变量calendar_id：声明类型str，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    calendar_id: str
    # 字段或变量year：声明类型int，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    year: int
    # 字段或变量closed_dates：声明类型frozenset[date]，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    closed_dates: frozenset[date]
    # 字段或变量source_title：声明类型str，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    source_title: str
    # 字段或变量source_url：声明类型str，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    source_url: str

    # 函数__post_init__：执行__post_init__逻辑。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态、模块常量或封装依赖。
    # - 输出：返回类型None；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
    # - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
    # - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
    def __post_init__(self) -> None:
        # API或函数调用：执行`object.__setattr__`，完整调用片段为`object.__setattr__(self, 'calendar_id', _require_text(self.calendar_id, 'calendar_id'))`。
        # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
        # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
        # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
        object.__setattr__(
            self,
            "calendar_id",
            _require_text(self.calendar_id, "calendar_id"),
        )
        # API或函数调用：执行`object.__setattr__`，完整调用片段为`object.__setattr__(self, 'source_title', _require_text(self.source_title, 'source_title'))`。
        # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
        # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
        # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
        object.__setattr__(
            self,
            "source_title",
            _require_text(self.source_title, "source_title"),
        )
        # API或函数调用：执行`object.__setattr__`，完整调用片段为`object.__setattr__(self, 'source_url', _require_text(self.source_url, 'source_url'))`。
        # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
        # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
        # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
        object.__setattr__(
            self,
            "source_url",
            _require_text(self.source_url, "source_url"),
        )
        # 条件门禁：判断`not isinstance(self.year, int) or self.year < 1990`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if not isinstance(self.year, int) or self.year < 1990:
            # 错误阻断：抛出`DataContractError('year无效。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
            raise DataContractError("year无效。")
        # 迭代处理：依次从`self.closed_dates`读取元素，并绑定到`value`。
        # - 维度变化：每轮处理一个记录、字段、证据或配置项，可能向列表、字典或累计统计增加一项。
        # - 为什么这样写：显式逐项处理便于保留顺序、定位坏数据，并对每个实体执行同一合同。
        for value in self.closed_dates:
            # 条件门禁：判断`not isinstance(value, date)`，条件为真时进入受保护分支。
            # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
            # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
            # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
            if not isinstance(value, date):
                # 错误阻断：抛出`DataContractError('closed_dates必须全部为date。')`并停止当前正常路径。
                # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
                # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
                raise DataContractError(
                    "closed_dates必须全部为date。"
                )
            # 条件门禁：判断`value.year != self.year`，条件为真时进入受保护分支。
            # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
            # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
            # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
            if value.year != self.year:
                # 错误阻断：抛出`DataContractError('closed_dates只能包含配置年度日期。')`并停止当前正常路径。
                # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
                # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
                raise DataContractError(
                    "closed_dates只能包含配置年度日期。"
                )

    # 函数is_trading_day：执行is_trading_day逻辑。
    # - 参数value：类型date；进入函数后按合同参与校验、筛选、计算或路由。
    # - 输出：返回类型bool；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
    # - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
    # - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
    def is_trading_day(self, value: date) -> bool:
        # 条件门禁：判断`value.year != self.year`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if value.year != self.year:
            # 错误阻断：抛出`DataContractError(f'日期超出交易日历年度：{value}')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
            raise DataContractError(
                f"日期超出交易日历年度：{value}"
            )
        # 结果返回：把`value.weekday() < 5 and value not in self.closed_dates`交给调用方并结束当前函数。
        # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return (
            value.weekday() < 5
            and value not in self.closed_dates
        )

    # 函数latest_trading_day：执行latest_trading_day逻辑。
    # - 参数as_of_date：类型date；进入函数后按合同参与校验、筛选、计算或路由。
    # - 输出：返回类型date；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
    # - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
    # - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
    def latest_trading_day(self, as_of_date: date) -> date:
        # 条件门禁：判断`as_of_date.year != self.year`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if as_of_date.year != self.year:
            # 错误阻断：抛出`DataContractError('as_of_date超出交易日历年度。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
            raise DataContractError(
                "as_of_date超出交易日历年度。"
            )
        # 变量更新：计算并保存candidate，右侧逻辑为`as_of_date`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        candidate = as_of_date
        # 迭代处理：依次从`range(370)`读取元素，并绑定到`_`。
        # - 维度变化：每轮处理一个记录、字段、证据或配置项，可能向列表、字典或累计统计增加一项。
        # - 为什么这样写：显式逐项处理便于保留顺序、定位坏数据，并对每个实体执行同一合同。
        for _ in range(370):
            # 条件门禁：判断`self.is_trading_day(candidate)`，条件为真时进入受保护分支。
            # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
            # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
            # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
            if self.is_trading_day(candidate):
                # 结果返回：把`candidate`交给调用方并结束当前函数。
                # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
                # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
                return candidate
            # 累计更新：对candidate执行`AugAssign`对应的原地运算，增量来自`timedelta(days=1)`。
            # - 数据变化：目标值在当前作用域内按运算符增加、减少或组合，维度通常保持不变但数值会累计。
            # - 为什么这样写：原地累计清楚表达计数、评分或集合聚合过程，并避免创建不必要的中间对象。
            candidate -= timedelta(days=1)
        # 错误阻断：抛出`DataContractError('无法解析最近交易日。')`并停止当前正常路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
        # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
        raise DataContractError("无法解析最近交易日。")

    # 函数trading_sessions_after：执行trading_sessions_after逻辑。
    # - 参数start_exclusive：类型date；进入函数后按合同参与校验、筛选、计算或路由。
    # - 参数end_inclusive：类型date；进入函数后按合同参与校验、筛选、计算或路由。
    # - 输出：返回类型int；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
    # - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
    # - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
    def trading_sessions_after(
        self,
        start_exclusive: date,
        end_inclusive: date,
    ) -> int:
        # 条件门禁：判断`end_inclusive.year != self.year`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if end_inclusive.year != self.year:
            # 错误阻断：抛出`DataContractError('交易日时效结束日期必须位于配置年度。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
            raise DataContractError(
                "交易日时效结束日期必须位于配置年度。"
            )
        # 条件门禁：判断`end_inclusive <= start_exclusive`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if end_inclusive <= start_exclusive:
            # 结果返回：把`0`交给调用方并结束当前函数。
            # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
            # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
            return 0
        # 条件门禁：判断`start_exclusive.year == self.year`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if start_exclusive.year == self.year:
            # 变量更新：计算并保存cursor，右侧逻辑为`start_exclusive + timedelta(days=1)`。
            # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
            # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
            cursor = start_exclusive + timedelta(days=1)
        # 条件门禁：判断`start_exclusive == date(self.year - 1, 12, 31)`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        elif start_exclusive == date(self.year - 1, 12, 31):
            # 允许从上一年最后一天跨入当前年度。这样可处理
            # daily-funds-raw@2025-11-20..2025-12-31
            # 到2026证据截止日的交易日滞后，而不伪造2025节假日。
            # 变量更新：计算并保存cursor，右侧逻辑为`date(self.year, 1, 1)`。
            # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
            # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
            cursor = date(self.year, 1, 1)
        else:
            # 错误阻断：抛出`DataContractError('跨年度时效仅支持以上一年12月31日为起点。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
            raise DataContractError(
                "跨年度时效仅支持以上一年12月31日为起点。"
            )
        # 变量更新：计算并保存count，右侧逻辑为`0`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        count = 0
        # 循环门禁：只要`cursor <= end_inclusive`为真就继续执行当前批次。
        # - 数据变化：循环体必须通过计数器、剩余集合或状态更新逐步接近终止条件。
        # - 为什么这样写：适合处理未知轮数的分页、重试或收敛过程，同时由显式条件防止无限循环。
        while cursor <= end_inclusive:
            # 条件门禁：判断`self.is_trading_day(cursor)`，条件为真时进入受保护分支。
            # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
            # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
            # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
            if self.is_trading_day(cursor):
                # 累计更新：对count执行`AugAssign`对应的原地运算，增量来自`1`。
                # - 数据变化：目标值在当前作用域内按运算符增加、减少或组合，维度通常保持不变但数值会累计。
                # - 为什么这样写：原地累计清楚表达计数、评分或集合聚合过程，并避免创建不必要的中间对象。
                count += 1
            # 累计更新：对cursor执行`AugAssign`对应的原地运算，增量来自`timedelta(days=1)`。
            # - 数据变化：目标值在当前作用域内按运算符增加、减少或组合，维度通常保持不变但数值会累计。
            # - 为什么这样写：原地累计清楚表达计数、评分或集合聚合过程，并避免创建不必要的中间对象。
            cursor += timedelta(days=1)
        # 结果返回：把`count`交给调用方并结束当前函数。
        # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return count


# 类ActivationEntry：封装ActivationEntry相关状态、字段与行为。
# - 继承边界：基类为object；类体包含约6个字段或常量、1个方法。
# - 数据变化：类定义本身不执行隐式I/O，实例只在构造、校验或显式方法调用时产生受控状态。
# - 实操示例：调用方先构造该类型，再由方法完成校验、证据组合、路由或结果导出。
# - 为什么这样写：强类型边界能把相关不变量集中管理，减少字典键拼写、状态漂移和跨模块耦合。
@dataclass(frozen=True, slots=True)
class ActivationEntry:
    # 字段或变量dataset_id：声明类型str，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    dataset_id: str
    # 字段或变量enabled：声明类型bool，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    enabled: bool
    # 字段或变量activation_state：声明类型str，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    activation_state: str
    # 字段或变量allowed_usages：声明类型frozenset[StandardDataUsage]，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    allowed_usages: frozenset[StandardDataUsage]
    # 字段或变量effective_from：声明类型date，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    effective_from: date
    # 字段或变量evidence_note：声明类型str，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    evidence_note: str

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
        # API或函数调用：执行`object.__setattr__`，完整调用片段为`object.__setattr__(self, 'activation_state', _require_text(self.activation_state, 'activation_state…`。
        # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
        # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
        # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
        object.__setattr__(
            self,
            "activation_state",
            _require_text(
                self.activation_state,
                "activation_state",
            ),
        )
        # API或函数调用：执行`object.__setattr__`，完整调用片段为`object.__setattr__(self, 'evidence_note', _require_text(self.evidence_note, 'evidence_note'))`。
        # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
        # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
        # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
        object.__setattr__(
            self,
            "evidence_note",
            _require_text(
                self.evidence_note,
                "evidence_note",
            ),
        )
        # 字段或变量usages：声明类型set[StandardDataUsage]，初始逻辑为`set()`。
        # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
        # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
        usages: set[StandardDataUsage] = set()
        # 迭代处理：依次从`self.allowed_usages`读取元素，并绑定到`value`。
        # - 维度变化：每轮处理一个记录、字段、证据或配置项，可能向列表、字典或累计统计增加一项。
        # - 为什么这样写：显式逐项处理便于保留顺序、定位坏数据，并对每个实体执行同一合同。
        for value in self.allowed_usages:
            # 异常边界：执行可能失败的解析、转换、文件读取或外部调用，并在后续分支转换为项目统一错误。
            # - 数据变化：成功路径产生正常结果；失败路径保留原异常作为cause、降级为缺失值或记录明确问题。
            # - 为什么这样写：上层只需处理稳定的DataContractError或受控结果，不依赖第三方异常实现细节。
            try:
                # 变量更新：计算并保存usage，右侧逻辑为`value if isinstance(value, StandardDataUsage) else StandardDataUsage(value)`。
                # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
                # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
                usage = (
                    value
                    if isinstance(value, StandardDataUsage)
                    else StandardDataUsage(value)
                )
            # 异常转换：捕获ValueError，保存上下文并执行统一错误、回退或忽略策略。
            # - 数据变化：异常路径不返回未校验的半成品；必要时把失败原因写入issues、warnings或异常链。
            # - 为什么这样写：明确捕获范围可避免吞掉程序错误，同时让调用方获得稳定且可审计的失败语义。
            except ValueError as exc:
                # 错误阻断：抛出`DataContractError(f'不支持的allowed_usage：{value}')`并停止当前正常路径。
                # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
                # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
                raise DataContractError(
                    f"不支持的allowed_usage：{value}"
                ) from exc
            # API或函数调用：执行`usages.add`，完整调用片段为`usages.add(usage)`。
            # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
            # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
            # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
            usages.add(usage)
        # API或函数调用：执行`object.__setattr__`，完整调用片段为`object.__setattr__(self, 'allowed_usages', frozenset(usages))`。
        # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
        # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
        # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
        object.__setattr__(
            self,
            "allowed_usages",
            frozenset(usages),
        )


# 类DatasetEvidenceConfig：封装DatasetEvidenceConfig相关状态、字段与行为。
# - 继承边界：基类为object；类体包含约6个字段或常量、1个方法。
# - 数据变化：类定义本身不执行隐式I/O，实例只在构造、校验或显式方法调用时产生受控状态。
# - 实操示例：调用方先构造该类型，再由方法完成校验、证据组合、路由或结果导出。
# - 为什么这样写：强类型边界能把相关不变量集中管理，减少字典键拼写、状态漂移和跨模块耦合。
@dataclass(frozen=True, slots=True)
class DatasetEvidenceConfig:
    # 字段或变量dataset_id：声明类型str，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    dataset_id: str
    # 字段或变量report_kind：声明类型ReportKind，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    report_kind: ReportKind
    # 字段或变量report_paths：声明类型tuple[str, ...]，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    report_paths: tuple[str, ...]
    # 字段或变量coverage_scope：声明类型str，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    coverage_scope: str
    # 字段或变量max_current_lag_sessions：声明类型int，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    max_current_lag_sessions: int
    # 字段或变量max_manual_lag_sessions：声明类型int，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    max_manual_lag_sessions: int

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
        # 变量更新：计算并保存kind，右侧逻辑为`self.report_kind`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        kind = self.report_kind
        # 条件门禁：判断`isinstance(kind, str)`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if isinstance(kind, str):
            # 异常边界：执行可能失败的解析、转换、文件读取或外部调用，并在后续分支转换为项目统一错误。
            # - 数据变化：成功路径产生正常结果；失败路径保留原异常作为cause、降级为缺失值或记录明确问题。
            # - 为什么这样写：上层只需处理稳定的DataContractError或受控结果，不依赖第三方异常实现细节。
            try:
                # 变量更新：计算并保存kind，右侧逻辑为`ReportKind(kind)`。
                # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
                # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
                kind = ReportKind(kind)
            # 异常转换：捕获ValueError，保存上下文并执行统一错误、回退或忽略策略。
            # - 数据变化：异常路径不返回未校验的半成品；必要时把失败原因写入issues、warnings或异常链。
            # - 为什么这样写：明确捕获范围可避免吞掉程序错误，同时让调用方获得稳定且可审计的失败语义。
            except ValueError as exc:
                # 错误阻断：抛出`DataContractError(f'不支持的report_kind：{kind}')`并停止当前正常路径。
                # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
                # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
                raise DataContractError(
                    f"不支持的report_kind：{kind}"
                ) from exc
        # API或函数调用：执行`object.__setattr__`，完整调用片段为`object.__setattr__(self, 'report_kind', kind)`。
        # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
        # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
        # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
        object.__setattr__(self, "report_kind", kind)
        # 变量更新：计算并保存paths，右侧逻辑为`tuple((_require_text(item, 'report_paths') for item in self.report_paths))`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        paths = tuple(
            _require_text(item, "report_paths")
            for item in self.report_paths
        )
        # 条件门禁：判断`not paths or len(paths) != len(set(paths))`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if not paths or len(paths) != len(set(paths)):
            # 错误阻断：抛出`DataContractError('report_paths不能为空或重复。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
            raise DataContractError(
                "report_paths不能为空或重复。"
            )
        # API或函数调用：执行`object.__setattr__`，完整调用片段为`object.__setattr__(self, 'report_paths', paths)`。
        # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
        # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
        # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
        object.__setattr__(self, "report_paths", paths)
        # API或函数调用：执行`object.__setattr__`，完整调用片段为`object.__setattr__(self, 'coverage_scope', _require_text(self.coverage_scope, 'coverage_scope'))`。
        # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
        # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
        # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
        object.__setattr__(
            self,
            "coverage_scope",
            _require_text(
                self.coverage_scope,
                "coverage_scope",
            ),
        )
        # 条件门禁：判断`self.max_current_lag_sessions < 0`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if self.max_current_lag_sessions < 0:
            # 错误阻断：抛出`DataContractError('max_current_lag_sessions不能为负。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
            raise DataContractError(
                "max_current_lag_sessions不能为负。"
            )
        # 条件门禁：判断`self.max_manual_lag_sessions < 0`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if self.max_manual_lag_sessions < 0:
            # 错误阻断：抛出`DataContractError('max_manual_lag_sessions不能为负。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
            raise DataContractError(
                "max_manual_lag_sessions不能为负。"
            )


# 类ExternalEvidenceConfig：封装ExternalEvidenceConfig相关状态、字段与行为。
# - 继承边界：基类为object；类体包含约6个字段或常量、2个方法。
# - 数据变化：类定义本身不执行隐式I/O，实例只在构造、校验或显式方法调用时产生受控状态。
# - 实操示例：调用方先构造该类型，再由方法完成校验、证据组合、路由或结果导出。
# - 为什么这样写：强类型边界能把相关不变量集中管理，减少字典键拼写、状态漂移和跨模块耦合。
@dataclass(frozen=True, slots=True)
class ExternalEvidenceConfig:
    # 字段或变量contract_version：声明类型str，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    contract_version: str
    # 字段或变量snapshot_id：声明类型str，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    snapshot_id: str
    # 字段或变量as_of_date：声明类型date，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    as_of_date: date
    # 字段或变量calendar_path：声明类型str，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    calendar_path: str
    # 字段或变量activation_path：声明类型str，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    activation_path: str
    # 字段或变量datasets：声明类型tuple[DatasetEvidenceConfig, ...]，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    datasets: tuple[DatasetEvidenceConfig, ...]

    # 函数__post_init__：执行__post_init__逻辑。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态、模块常量或封装依赖。
    # - 输出：返回类型None；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
    # - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
    # - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
    def __post_init__(self) -> None:
        # API或函数调用：执行`object.__setattr__`，完整调用片段为`object.__setattr__(self, 'contract_version', _require_text(self.contract_version, 'contract_version…`。
        # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
        # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
        # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
        object.__setattr__(
            self,
            "contract_version",
            _require_text(
                self.contract_version,
                "contract_version",
            ),
        )
        # 条件门禁：判断`self.contract_version != EXTERNAL_EVIDENCE_VERSION`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if self.contract_version != EXTERNAL_EVIDENCE_VERSION:
            # 错误阻断：抛出`DataContractError('外部证据合同版本不兼容。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
            raise DataContractError(
                "外部证据合同版本不兼容。"
            )
        # API或函数调用：执行`object.__setattr__`，完整调用片段为`object.__setattr__(self, 'snapshot_id', _require_text(self.snapshot_id, 'snapshot_id'))`。
        # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
        # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
        # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
        object.__setattr__(
            self,
            "snapshot_id",
            _require_text(self.snapshot_id, "snapshot_id"),
        )
        # API或函数调用：执行`object.__setattr__`，完整调用片段为`object.__setattr__(self, 'calendar_path', _require_text(self.calendar_path, 'calendar_path'))`。
        # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
        # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
        # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
        object.__setattr__(
            self,
            "calendar_path",
            _require_text(self.calendar_path, "calendar_path"),
        )
        # API或函数调用：执行`object.__setattr__`，完整调用片段为`object.__setattr__(self, 'activation_path', _require_text(self.activation_path, 'activation_path'))`。
        # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
        # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
        # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
        object.__setattr__(
            self,
            "activation_path",
            _require_text(
                self.activation_path,
                "activation_path",
            ),
        )
        # 变量更新：计算并保存ids，右侧逻辑为`[item.dataset_id for item in self.datasets]`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        ids = [item.dataset_id for item in self.datasets]
        # 条件门禁：判断`not ids or len(ids) != len(set(ids))`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if not ids or len(ids) != len(set(ids)):
            # 错误阻断：抛出`DataContractError('datasets不能为空或dataset_id重复。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
            raise DataContractError(
                "datasets不能为空或dataset_id重复。"
            )

    # 函数dataset：执行dataset逻辑。
    # - 参数dataset_id：类型str；进入函数后按合同参与校验、筛选、计算或路由。
    # - 输出：返回类型DatasetEvidenceConfig；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
    # - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
    # - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
    def dataset(
        self,
        dataset_id: str,
    ) -> DatasetEvidenceConfig:
        # 变量更新：计算并保存key，右侧逻辑为`_require_text(dataset_id, 'dataset_id')`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        key = _require_text(dataset_id, "dataset_id")
        # 迭代处理：依次从`self.datasets`读取元素，并绑定到`item`。
        # - 维度变化：每轮处理一个记录、字段、证据或配置项，可能向列表、字典或累计统计增加一项。
        # - 为什么这样写：显式逐项处理便于保留顺序、定位坏数据，并对每个实体执行同一合同。
        for item in self.datasets:
            # 条件门禁：判断`item.dataset_id == key`，条件为真时进入受保护分支。
            # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
            # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
            # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
            if item.dataset_id == key:
                # 结果返回：把`item`交给调用方并结束当前函数。
                # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
                # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
                return item
        # 错误阻断：抛出`DataContractError(f'外部证据配置未登记数据集：{key}')`并停止当前正常路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
        # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
        raise DataContractError(
            f"外部证据配置未登记数据集：{key}"
        )


# 函数load_trading_calendar：执行load_trading_calendar逻辑。
# - 参数path：类型str | Path；进入函数后按合同参与校验、筛选、计算或路由。
# - 输出：返回类型TradingCalendar；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
# - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
# - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
def load_trading_calendar(path: str | Path) -> TradingCalendar:
    # 变量更新：计算并保存calendar_path，右侧逻辑为`Path(path)`。
    # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
    # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
    calendar_path = Path(path)
    # 变量更新：计算并保存raw，右侧逻辑为`_load_json(calendar_path)`。
    # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
    # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
    raw = _load_json(calendar_path)
    # 变量更新：计算并保存year，右侧逻辑为`int(raw['year'])`。
    # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
    # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
    year = int(raw["year"])
    # 字段或变量closed_dates：声明类型set[date]，初始逻辑为`set()`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    closed_dates: set[date] = set()
    # 迭代处理：依次从`raw['closed_periods']`读取元素，并绑定到`period`。
    # - 维度变化：每轮处理一个记录、字段、证据或配置项，可能向列表、字典或累计统计增加一项。
    # - 为什么这样写：显式逐项处理便于保留顺序、定位坏数据，并对每个实体执行同一合同。
    for period in raw["closed_periods"]:
        # 变量更新：计算并保存start，右侧逻辑为`_parse_date(period['start'], 'closed_period.start')`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        start = _parse_date(period["start"], "closed_period.start")
        # 变量更新：计算并保存end，右侧逻辑为`_parse_date(period['end'], 'closed_period.end')`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        end = _parse_date(period["end"], "closed_period.end")
        # 条件门禁：判断`start > end`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if start > end:
            # 错误阻断：抛出`DataContractError('交易所休市区间起止日期无效。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
            raise DataContractError(
                "交易所休市区间起止日期无效。"
            )
        # 变量更新：计算并保存cursor，右侧逻辑为`start`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        cursor = start
        # 循环门禁：只要`cursor <= end`为真就继续执行当前批次。
        # - 数据变化：循环体必须通过计数器、剩余集合或状态更新逐步接近终止条件。
        # - 为什么这样写：适合处理未知轮数的分页、重试或收敛过程，同时由显式条件防止无限循环。
        while cursor <= end:
            # API或函数调用：执行`closed_dates.add`，完整调用片段为`closed_dates.add(cursor)`。
            # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
            # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
            # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
            closed_dates.add(cursor)
            # 累计更新：对cursor执行`AugAssign`对应的原地运算，增量来自`timedelta(days=1)`。
            # - 数据变化：目标值在当前作用域内按运算符增加、减少或组合，维度通常保持不变但数值会累计。
            # - 为什么这样写：原地累计清楚表达计数、评分或集合聚合过程，并避免创建不必要的中间对象。
            cursor += timedelta(days=1)
    # 结果返回：把`TradingCalendar(calendar_id=str(raw['calendar_id']), year=year, closed_dates=frozenset(closed_dates…`交给调用方并结束当前函数。
    # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return TradingCalendar(
        calendar_id=str(raw["calendar_id"]),
        year=year,
        closed_dates=frozenset(closed_dates),
        source_title=str(raw["source"]["title"]),
        source_url=str(raw["source"]["url"]),
    )


# 函数load_activation_registry：执行load_activation_registry逻辑。
# - 参数path：类型str | Path；进入函数后按合同参与校验、筛选、计算或路由。
# - 输出：返回类型dict[str, ActivationEntry]；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
# - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
# - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
def load_activation_registry(
    path: str | Path,
) -> dict[str, ActivationEntry]:
    # 变量更新：计算并保存registry_path，右侧逻辑为`Path(path)`。
    # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
    # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
    registry_path = Path(path)
    # 变量更新：计算并保存raw，右侧逻辑为`_load_json(registry_path)`。
    # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
    # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
    raw = _load_json(registry_path)
    # 字段或变量entries：声明类型dict[str, ActivationEntry]，初始逻辑为`{}`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    entries: dict[str, ActivationEntry] = {}
    # 迭代处理：依次从`raw['datasets']`读取元素，并绑定到`item`。
    # - 维度变化：每轮处理一个记录、字段、证据或配置项，可能向列表、字典或累计统计增加一项。
    # - 为什么这样写：显式逐项处理便于保留顺序、定位坏数据，并对每个实体执行同一合同。
    for item in raw["datasets"]:
        # 变量更新：计算并保存entry，右侧逻辑为`ActivationEntry(dataset_id=str(item['dataset_id']), enabled=bool(item['enabled']), activation_state…`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        entry = ActivationEntry(
            dataset_id=str(item["dataset_id"]),
            enabled=bool(item["enabled"]),
            activation_state=str(item["activation_state"]),
            allowed_usages=frozenset(
                StandardDataUsage(value)
                for value in item["allowed_usages"]
            ),
            effective_from=_parse_date(
                item["effective_from"],
                "effective_from",
            ),
            evidence_note=str(item["evidence_note"]),
        )
        # 条件门禁：判断`entry.dataset_id in entries`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if entry.dataset_id in entries:
            # 错误阻断：抛出`DataContractError(f'启用配置dataset_id重复：{entry.dataset_id}')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
            raise DataContractError(
                f"启用配置dataset_id重复：{entry.dataset_id}"
            )
        # 变量更新：计算并保存entries[entry.dataset_id]，右侧逻辑为`entry`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        entries[entry.dataset_id] = entry
    # 结果返回：把`entries`交给调用方并结束当前函数。
    # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return entries


# 函数load_external_evidence_config：执行load_external_evidence_config逻辑。
# - 参数path：类型str | Path；进入函数后按合同参与校验、筛选、计算或路由。
# - 输出：返回类型ExternalEvidenceConfig；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
# - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
# - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
def load_external_evidence_config(
    path: str | Path,
) -> ExternalEvidenceConfig:
    # 变量更新：计算并保存config_path，右侧逻辑为`Path(path)`。
    # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
    # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
    config_path = Path(path)
    # 变量更新：计算并保存raw，右侧逻辑为`_load_json(config_path)`。
    # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
    # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
    raw = _load_json(config_path)
    # 变量更新：计算并保存datasets，右侧逻辑为`tuple((DatasetEvidenceConfig(dataset_id=str(item['dataset_id']), report_kind=ReportKind(item['repor…`。
    # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
    # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
    datasets = tuple(
        DatasetEvidenceConfig(
            dataset_id=str(item["dataset_id"]),
            report_kind=ReportKind(item["report_kind"]),
            report_paths=tuple(item["report_paths"]),
            coverage_scope=str(item["coverage_scope"]),
            max_current_lag_sessions=int(
                item["max_current_lag_sessions"]
            ),
            max_manual_lag_sessions=int(
                item["max_manual_lag_sessions"]
            ),
        )
        for item in raw["datasets"]
    )
    # 结果返回：把`ExternalEvidenceConfig(contract_version=str(raw['contract_version']), snapshot_id=str(raw['snapshot…`交给调用方并结束当前函数。
    # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return ExternalEvidenceConfig(
        contract_version=str(raw["contract_version"]),
        snapshot_id=str(raw["snapshot_id"]),
        as_of_date=_parse_date(
            raw["as_of_date"],
            "as_of_date",
        ),
        calendar_path=str(raw["calendar_path"]),
        activation_path=str(raw["activation_path"]),
        datasets=datasets,
    )


# 类ReportBackedEvidenceResolver：把已提交真实报告转换为覆盖、交易日时效和启用证据。
# - 继承边界：基类为object；类体包含约0个字段或常量、10个方法。
# - 数据变化：类定义本身不执行隐式I/O，实例只在构造、校验或显式方法调用时产生受控状态。
# - 实操示例：调用方先构造该类型，再由方法完成校验、证据组合、路由或结果导出。
# - 为什么这样写：强类型边界能把相关不变量集中管理，减少字典键拼写、状态漂移和跨模块耦合。
class ReportBackedEvidenceResolver:
    """把已提交真实报告转换为覆盖、交易日时效和启用证据。"""

    # 函数__init__：执行__init__逻辑。
    # - 关键字参数project_root：类型str | Path，无默认值；只允许显式命名传入，降低参数错位风险。
    # - 关键字参数config：类型ExternalEvidenceConfig，无默认值；只允许显式命名传入，降低参数错位风险。
    # - 关键字参数calendar：类型TradingCalendar，无默认值；只允许显式命名传入，降低参数错位风险。
    # - 关键字参数activations：类型Mapping[str, ActivationEntry]，无默认值；只允许显式命名传入，降低参数错位风险。
    # - 输出：返回类型None；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
    # - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
    # - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
    def __init__(
        self,
        *,
        project_root: str | Path,
        config: ExternalEvidenceConfig,
        calendar: TradingCalendar,
        activations: Mapping[str, ActivationEntry],
    ) -> None:
        # 变量更新：计算并保存self.project_root，右侧逻辑为`Path(project_root).resolve()`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        self.project_root = Path(project_root).resolve()
        # 变量更新：计算并保存self.config，右侧逻辑为`config`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        self.config = config
        # 变量更新：计算并保存self.calendar，右侧逻辑为`calendar`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        self.calendar = calendar
        # 变量更新：计算并保存self.activations，右侧逻辑为`dict(activations)`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        self.activations = dict(activations)
        # 变量更新：计算并保存config_ids，右侧逻辑为`{item.dataset_id for item in self.config.datasets}`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        config_ids = {
            item.dataset_id
            for item in self.config.datasets
        }
        # 条件门禁：判断`config_ids != set(self.activations)`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if config_ids != set(self.activations):
            # 错误阻断：抛出`DataContractError('外部证据配置与启用注册表数据集集合不一致。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
            raise DataContractError(
                "外部证据配置与启用注册表数据集集合不一致。"
            )
        # 字段或变量self._reports：声明类型dict[str, dict[str, Any]]，初始逻辑为`{}`。
        # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
        # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
        self._reports: dict[str, dict[str, Any]] = {}

    # 函数from_project：执行from_project逻辑。
    # - 关键字参数project_root：类型str | Path，无默认值；只允许显式命名传入，降低参数错位风险。
    # - 关键字参数config_path：类型str | Path，无默认值；只允许显式命名传入，降低参数错位风险。
    # - 输出：返回类型'ReportBackedEvidenceResolver'；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
    # - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
    # - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
    @classmethod
    def from_project(
        cls,
        *,
        project_root: str | Path,
        config_path: str | Path,
    ) -> "ReportBackedEvidenceResolver":
        # 变量更新：计算并保存root，右侧逻辑为`Path(project_root).resolve()`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        root = Path(project_root).resolve()
        # 变量更新：计算并保存config_file，右侧逻辑为`Path(config_path)`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        config_file = Path(config_path)
        # 条件门禁：判断`not config_file.is_absolute()`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if not config_file.is_absolute():
            # 变量更新：计算并保存config_file，右侧逻辑为`root / config_file`。
            # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
            # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
            config_file = root / config_file
        # 变量更新：计算并保存config，右侧逻辑为`load_external_evidence_config(config_file)`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        config = load_external_evidence_config(config_file)
        # 变量更新：计算并保存calendar，右侧逻辑为`load_trading_calendar(root / config.calendar_path)`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        calendar = load_trading_calendar(
            root / config.calendar_path
        )
        # 变量更新：计算并保存activations，右侧逻辑为`load_activation_registry(root / config.activation_path)`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        activations = load_activation_registry(
            root / config.activation_path
        )
        # 结果返回：把`cls(project_root=root, config=config, calendar=calendar, activations=activations)`交给调用方并结束当前函数。
        # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return cls(
            project_root=root,
            config=config,
            calendar=calendar,
            activations=activations,
        )

    # 函数_report：执行_report逻辑。
    # - 参数relative_path：类型str；进入函数后按合同参与校验、筛选、计算或路由。
    # - 输出：返回类型dict[str, Any]；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
    # - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
    # - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
    def _report(self, relative_path: str) -> dict[str, Any]:
        # 变量更新：计算并保存key，右侧逻辑为`_require_text(relative_path, 'report_path')`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        key = _require_text(relative_path, "report_path")
        # 条件门禁：判断`key not in self._reports`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if key not in self._reports:
            # 变量更新：计算并保存self._reports[key]，右侧逻辑为`_load_json(self.project_root / key)`。
            # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
            # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
            self._reports[key] = _load_json(
                self.project_root / key
            )
        # 结果返回：把`self._reports[key]`交给调用方并结束当前函数。
        # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return self._reports[key]

    # 函数_dataset_row：执行_dataset_row逻辑。
    # - 参数report：类型Mapping[str, Any]；进入函数后按合同参与校验、筛选、计算或路由。
    # - 参数dataset_id：类型str；进入函数后按合同参与校验、筛选、计算或路由。
    # - 输出：返回类型Mapping[str, Any]；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
    # - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
    # - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
    @staticmethod
    def _dataset_row(
        report: Mapping[str, Any],
        dataset_id: str,
    ) -> Mapping[str, Any]:
        # 变量更新：计算并保存rows，右侧逻辑为`report.get('datasets')`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        rows = report.get("datasets")
        # 条件门禁：判断`not isinstance(rows, list)`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if not isinstance(rows, list):
            # 错误阻断：抛出`DataContractError('验收报告datasets不是列表。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
            raise DataContractError(
                "验收报告datasets不是列表。"
            )
        # 变量更新：计算并保存matches，右侧逻辑为`[row for row in rows if isinstance(row, Mapping) and str(row.get('dataset_id')) == dataset_id]`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        matches = [
            row
            for row in rows
            if isinstance(row, Mapping)
            and str(row.get("dataset_id")) == dataset_id
        ]
        # 条件门禁：判断`len(matches) != 1`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if len(matches) != 1:
            # 错误阻断：抛出`DataContractError(f'验收报告中{dataset_id}应恰好出现一次。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
            raise DataContractError(
                f"验收报告中{dataset_id}应恰好出现一次。"
            )
        # 结果返回：把`matches[0]`交给调用方并结束当前函数。
        # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return matches[0]

    # 函数_refs：执行_refs逻辑。
    # - 参数dataset：类型DatasetEvidenceConfig；进入函数后按合同参与校验、筛选、计算或路由。
    # - 参数extra：类型Iterable[str]，默认值()；进入函数后按合同参与校验、筛选、计算或路由。
    # - 输出：返回类型tuple[str, ...]；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
    # - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
    # - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
    def _refs(
        self,
        dataset: DatasetEvidenceConfig,
        extra: Iterable[str] = (),
    ) -> tuple[str, ...]:
        # 变量更新：计算并保存refs，右侧逻辑为`[f'external_snapshot:{self.config.snapshot_id}', f'calendar:{self.calendar.calendar_id}', *(f'repor…`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        refs = [
            f"external_snapshot:{self.config.snapshot_id}",
            f"calendar:{self.calendar.calendar_id}",
            *(
                f"report:{path}"
                for path in dataset.report_paths
            ),
            *extra,
        ]
        # 结果返回：把`tuple(dict.fromkeys(refs))`交给调用方并结束当前函数。
        # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return tuple(dict.fromkeys(refs))

    # 函数coverage_evidence：执行coverage_evidence逻辑。
    # - 参数dataset_id：类型str；进入函数后按合同参与校验、筛选、计算或路由。
    # - 输出：返回类型ReadinessEvidence；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
    # - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
    # - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
    def coverage_evidence(
        self,
        dataset_id: str,
    ) -> ReadinessEvidence:
        # 变量更新：计算并保存dataset，右侧逻辑为`self.config.dataset(dataset_id)`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        dataset = self.config.dataset(dataset_id)

        # 条件门禁：判断`dataset.report_kind is ReportKind.DAILY_K_COVERAGE`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if dataset.report_kind is ReportKind.DAILY_K_COVERAGE:
            # 变量更新：计算并保存report，右侧逻辑为`self._report(dataset.report_paths[0])`。
            # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
            # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
            report = self._report(dataset.report_paths[0])
            # 变量更新：计算并保存summary，右侧逻辑为`report['database_summary']`。
            # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
            # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
            summary = report["database_summary"]
            # 变量更新：计算并保存evaluation，右侧逻辑为`report['coverage_evaluation']`。
            # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
            # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
            evaluation = report["coverage_evaluation"]
            # 变量更新：计算并保存passed，右侧逻辑为`report.get('overall_status') == 'PASSED' and (not bool(report.get('blocks_downstream'))) and bool(e…`。
            # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
            # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
            passed = (
                report.get("overall_status") == "PASSED"
                and not bool(report.get("blocks_downstream"))
                and bool(
                    evaluation.get(
                        "database_matches_declared_cutoff"
                    )
                )
                and int(summary.get("row_count", 0)) > 0
                and int(summary.get("entity_count", 0)) > 0
            )
            # 变量更新：计算并保存status，右侧逻辑为`EvidenceStatus.PASSED if passed else EvidenceStatus.FAILED`。
            # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
            # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
            status = (
                EvidenceStatus.PASSED
                if passed
                else EvidenceStatus.FAILED
            )
            # 变量更新：计算并保存code，右侧逻辑为`'FULL_DATABASE_SNAPSHOT_COVERAGE_PROVEN' if passed else 'DAILY_K_COVERAGE_REPORT_FAILED'`。
            # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
            # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
            code = (
                "FULL_DATABASE_SNAPSHOT_COVERAGE_PROVEN"
                if passed
                else "DAILY_K_COVERAGE_REPORT_FAILED"
            )
            # 变量更新：计算并保存message，右侧逻辑为`'日K数据库边界、实体数和声明截止日由真实覆盖报告证明。' if passed else '日K真实覆盖报告未通过。'`。
            # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
            # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
            message = (
                "日K数据库边界、实体数和声明截止日由真实覆盖报告证明。"
                if passed
                else "日K真实覆盖报告未通过。"
            )
            # 变量更新：计算并保存metrics，右侧逻辑为`{'coverage_scope': dataset.coverage_scope, 'row_count': int(summary.get('row_count', 0)), 'entity_c…`。
            # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
            # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
            metrics = {
                "coverage_scope": dataset.coverage_scope,
                "row_count": int(summary.get("row_count", 0)),
                "entity_count": int(
                    summary.get("entity_count", 0)
                ),
                "min_data_date": summary.get("min_data_date"),
                "max_data_date": summary.get("max_data_date"),
                "declared_cutoff_date": evaluation.get(
                    "declared_cutoff_date"
                ),
                "database_matches_declared_cutoff": bool(
                    evaluation.get(
                        "database_matches_declared_cutoff"
                    )
                ),
            }

        # 条件门禁：判断`dataset.report_kind is ReportKind.FUNDAMENTAL_PROFILE`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        elif (
            dataset.report_kind
            is ReportKind.FUNDAMENTAL_PROFILE
        ):
            # 变量更新：计算并保存report，右侧逻辑为`self._report(dataset.report_paths[0])`。
            # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
            # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
            report = self._report(dataset.report_paths[0])
            # 变量更新：计算并保存summary，右侧逻辑为`report['summary']`。
            # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
            # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
            summary = report["summary"]
            # 变量更新：计算并保存duplicate，右侧逻辑为`report['duplicate_summary']`。
            # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
            # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
            duplicate = report["duplicate_summary"]
            # 变量更新：计算并保存passed，右侧逻辑为`bool(report.get('allows_current_snapshot_research')) and int(summary.get('row_count', 0)) > 0 and (…`。
            # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
            # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
            passed = (
                bool(report.get("allows_current_snapshot_research"))
                and int(summary.get("row_count", 0)) > 0
                and int(summary.get("stock_count", 0)) > 0
                and int(
                    duplicate.get(
                        "duplicate_extra_row_count",
                        -1,
                    )
                )
                == 0
            )
            # 变量更新：计算并保存status，右侧逻辑为`EvidenceStatus.PASSED if passed else EvidenceStatus.FAILED`。
            # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
            # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
            status = (
                EvidenceStatus.PASSED
                if passed
                else EvidenceStatus.FAILED
            )
            # 变量更新：计算并保存code，右侧逻辑为`'CURRENT_FUNDAMENTAL_SNAPSHOT_COVERAGE_PROVEN' if passed else 'FUNDAMENTAL_COVERAGE_REPORT_FAILED'`。
            # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
            # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
            code = (
                "CURRENT_FUNDAMENTAL_SNAPSHOT_COVERAGE_PROVEN"
                if passed
                else "FUNDAMENTAL_COVERAGE_REPORT_FAILED"
            )
            # 变量更新：计算并保存message，右侧逻辑为`'基本面当前快照的股票数、行数和主键唯一性已由真实剖析报告证明。' if passed else '基本面当前快照覆盖报告未通过。'`。
            # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
            # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
            message = (
                "基本面当前快照的股票数、行数和主键唯一性已由真实剖析报告证明。"
                if passed
                else "基本面当前快照覆盖报告未通过。"
            )
            # 变量更新：计算并保存metrics，右侧逻辑为`{'coverage_scope': dataset.coverage_scope, 'row_count': int(summary.get('row_count', 0)), 'entity_c…`。
            # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
            # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
            metrics = {
                "coverage_scope": dataset.coverage_scope,
                "row_count": int(summary.get("row_count", 0)),
                "entity_count": int(
                    summary.get("stock_count", 0)
                ),
                "min_snapshot_date": summary.get(
                    "min_snapshot_date"
                ),
                "max_snapshot_date": summary.get(
                    "max_snapshot_date"
                ),
                "profile_status": report.get("overall_status"),
                "allows_current_snapshot_research": bool(
                    report.get(
                        "allows_current_snapshot_research"
                    )
                ),
                "duplicate_extra_row_count": int(
                    duplicate.get(
                        "duplicate_extra_row_count",
                        -1,
                    )
                ),
            }

        else:
            # 变量更新：计算并保存canonical_report，右侧逻辑为`self._report(dataset.report_paths[0])`。
            # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
            # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
            canonical_report = self._report(
                dataset.report_paths[0]
            )
            # 变量更新：计算并保存service_report，右侧逻辑为`self._report(dataset.report_paths[1])`。
            # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
            # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
            service_report = self._report(
                dataset.report_paths[1]
            )
            # 变量更新：计算并保存canonical_row，右侧逻辑为`self._dataset_row(canonical_report, dataset_id)`。
            # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
            # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
            canonical_row = self._dataset_row(
                canonical_report,
                dataset_id,
            )
            # 变量更新：计算并保存service_row，右侧逻辑为`self._dataset_row(service_report, dataset_id)`。
            # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
            # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
            service_row = self._dataset_row(
                service_report,
                dataset_id,
            )
            # 变量更新：计算并保存accepted，右侧逻辑为`canonical_report.get('overall_status') == 'PASSED_WITH_WARNINGS' and service_report.get('overall_st…`。
            # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
            # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
            accepted = (
                canonical_report.get("overall_status")
                == "PASSED_WITH_WARNINGS"
                and service_report.get("overall_status")
                == "PASSED_WITH_WARNINGS"
                and int(canonical_row.get("result_count", 0))
                > 0
                and int(service_row.get("result_count", 0))
                > 0
            )
            # 变量更新：计算并保存status，右侧逻辑为`EvidenceStatus.WARNING if accepted else EvidenceStatus.FAILED`。
            # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
            # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
            status = (
                EvidenceStatus.WARNING
                if accepted
                else EvidenceStatus.FAILED
            )
            # 变量更新：计算并保存code，右侧逻辑为`'DATE_RANGE_AND_REAL_SAMPLE_ACCEPTED' if accepted else 'DAILY_FUNDS_ACCEPTANCE_FAILED'`。
            # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
            # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
            code = (
                "DATE_RANGE_AND_REAL_SAMPLE_ACCEPTED"
                if accepted
                else "DAILY_FUNDS_ACCEPTANCE_FAILED"
            )
            # 变量更新：计算并保存message，右侧逻辑为`'七类快照已通过真实Canonical和统一入口抽样验收，但尚无完整实体全集覆盖证明。' if accepted else '七类快照真实验收未通过。'`。
            # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
            # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
            message = (
                "七类快照已通过真实Canonical和统一入口抽样验收，"
                "但尚无完整实体全集覆盖证明。"
                if accepted
                else "七类快照真实验收未通过。"
            )
            # 变量更新：计算并保存metrics，右侧逻辑为`{'coverage_scope': dataset.coverage_scope, 'coverage_version': canonical_report.get('coverage_versi…`。
            # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
            # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
            metrics = {
                "coverage_scope": dataset.coverage_scope,
                "coverage_version": canonical_report.get(
                    "coverage_version"
                ),
                "canonical_result_count": int(
                    canonical_row.get("result_count", 0)
                ),
                "unified_result_count": int(
                    service_row.get("result_count", 0)
                ),
                "selector_mode": service_row.get(
                    "selector_mode"
                ),
                "exhaustive_entity_coverage_proven": False,
            }

        # 结果返回：把`ReadinessEvidence(dimension=ReadinessDimension.COVERAGE, status=status, code=code, message=message,…`交给调用方并结束当前函数。
        # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return ReadinessEvidence(
            dimension=ReadinessDimension.COVERAGE,
            status=status,
            code=code,
            message=message,
            metrics=metrics,
            evidence_refs=self._refs(dataset),
        )

    # 函数_latest_available_date：执行_latest_available_date逻辑。
    # - 参数dataset：类型DatasetEvidenceConfig；进入函数后按合同参与校验、筛选、计算或路由。
    # - 输出：返回类型date；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
    # - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
    # - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
    def _latest_available_date(
        self,
        dataset: DatasetEvidenceConfig,
    ) -> date:
        # 条件门禁：判断`dataset.report_kind is ReportKind.DAILY_K_COVERAGE`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if dataset.report_kind is ReportKind.DAILY_K_COVERAGE:
            # 变量更新：计算并保存report，右侧逻辑为`self._report(dataset.report_paths[0])`。
            # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
            # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
            report = self._report(dataset.report_paths[0])
            # 结果返回：把`_parse_date(_json_path(report, 'coverage_evaluation.database_max_date'), 'daily_k.database_max_date…`交给调用方并结束当前函数。
            # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
            # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
            return _parse_date(
                _json_path(
                    report,
                    "coverage_evaluation.database_max_date",
                ),
                "daily_k.database_max_date",
            )

        # 条件门禁：判断`dataset.report_kind is ReportKind.FUNDAMENTAL_PROFILE`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if (
            dataset.report_kind
            is ReportKind.FUNDAMENTAL_PROFILE
        ):
            # 变量更新：计算并保存report，右侧逻辑为`self._report(dataset.report_paths[0])`。
            # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
            # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
            report = self._report(dataset.report_paths[0])
            # 结果返回：把`_parse_date(_json_path(report, 'summary.max_snapshot_date'), 'fundamental.max_snapshot_date')`交给调用方并结束当前函数。
            # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
            # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
            return _parse_date(
                _json_path(
                    report,
                    "summary.max_snapshot_date",
                ),
                "fundamental.max_snapshot_date",
            )

        # 变量更新：计算并保存report，右侧逻辑为`self._report(dataset.report_paths[0])`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        report = self._report(dataset.report_paths[0])
        # 变量更新：计算并保存coverage_version，右侧逻辑为`str(report['coverage_version'])`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        coverage_version = str(report["coverage_version"])
        # 变量更新：计算并保存match，右侧逻辑为`re.search('@(\\d{4}-\\d{2}-\\d{2})\\.\\.(\\d{4}-\\d{2}-\\d{2})$', coverage_version)`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        match = re.search(
            r"@(\d{4}-\d{2}-\d{2})\.\.(\d{4}-\d{2}-\d{2})$",
            coverage_version,
        )
        # 条件门禁：判断`match is None`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if match is None:
            # 错误阻断：抛出`DataContractError('无法从七类快照coverage_version解析截止日。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
            raise DataContractError(
                "无法从七类快照coverage_version解析截止日。"
            )
        # 结果返回：把`_parse_date(match.group(2), 'daily_funds.coverage_end_date')`交给调用方并结束当前函数。
        # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return _parse_date(
            match.group(2),
            "daily_funds.coverage_end_date",
        )

    # 函数freshness_evidence：执行freshness_evidence逻辑。
    # - 参数dataset_id：类型str；进入函数后按合同参与校验、筛选、计算或路由。
    # - 参数usage：类型StandardDataUsage；进入函数后按合同参与校验、筛选、计算或路由。
    # - 参数as_of_date：类型date；进入函数后按合同参与校验、筛选、计算或路由。
    # - 输出：返回类型ReadinessEvidence；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
    # - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
    # - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
    def freshness_evidence(
        self,
        dataset_id: str,
        usage: StandardDataUsage,
        as_of_date: date,
    ) -> ReadinessEvidence:
        # 变量更新：计算并保存dataset，右侧逻辑为`self.config.dataset(dataset_id)`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        dataset = self.config.dataset(dataset_id)
        # 变量更新：计算并保存latest，右侧逻辑为`self._latest_available_date(dataset)`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        latest = self._latest_available_date(dataset)
        # 变量更新：计算并保存expected，右侧逻辑为`self.calendar.latest_trading_day(as_of_date)`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        expected = self.calendar.latest_trading_day(as_of_date)

        # 变量更新：计算并保存historical，右侧逻辑为`usage in {StandardDataUsage.STRICT_HISTORICAL_BACKTEST, StandardDataUsage.HISTORICAL_MODEL_TRAINING}`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        historical = usage in {
            StandardDataUsage.STRICT_HISTORICAL_BACKTEST,
            StandardDataUsage.HISTORICAL_MODEL_TRAINING,
        }
        # 条件门禁：判断`historical`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if historical:
            # 结果返回：把`ReadinessEvidence(dimension=ReadinessDimension.FRESHNESS, status=EvidenceStatus.PASSED, code='FIXED…`交给调用方并结束当前函数。
            # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
            # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
            return ReadinessEvidence(
                dimension=ReadinessDimension.FRESHNESS,
                status=EvidenceStatus.PASSED,
                code=(
                    "FIXED_HISTORICAL_RANGE_CURRENT_FRESHNESS_"
                    "NOT_APPLICABLE"
                ),
                message=(
                    "固定历史区间的准入由覆盖、时点和语义证据决定，"
                    "不以当前数据是否最新作为阻断条件。"
                ),
                metrics={
                    "latest_available_date": latest,
                    "expected_latest_trading_date": expected,
                    "trading_session_lag": (
                        self.calendar.trading_sessions_after(
                            latest,
                            expected,
                        )
                    ),
                    "usage": usage.value,
                },
                evidence_refs=self._refs(dataset),
            )

        # 变量更新：计算并保存lag，右侧逻辑为`self.calendar.trading_sessions_after(latest, expected)`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        lag = self.calendar.trading_sessions_after(
            latest,
            expected,
        )
        # 变量更新：计算并保存threshold，右侧逻辑为`dataset.max_manual_lag_sessions if usage is StandardDataUsage.MANUAL_DECISION_SUPPORT else dataset.…`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        threshold = (
            dataset.max_manual_lag_sessions
            if usage
            is StandardDataUsage.MANUAL_DECISION_SUPPORT
            else dataset.max_current_lag_sessions
        )
        # 变量更新：计算并保存passed，右侧逻辑为`latest <= expected and lag <= threshold`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        passed = latest <= expected and lag <= threshold
        # 变量更新：计算并保存status，右侧逻辑为`EvidenceStatus.PASSED if passed else EvidenceStatus.WARNING`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        status = (
            EvidenceStatus.PASSED
            if passed
            else EvidenceStatus.WARNING
        )
        # 变量更新：计算并保存code，右侧逻辑为`'TRADING_SESSION_FRESHNESS_WITHIN_SLA' if passed else 'TRADING_SESSION_LAG_EXCEEDS_SLA'`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        code = (
            "TRADING_SESSION_FRESHNESS_WITHIN_SLA"
            if passed
            else "TRADING_SESSION_LAG_EXCEEDS_SLA"
        )
        # 变量更新：计算并保存message，右侧逻辑为`'真实报告截止日满足交易日时效阈值。' if passed else '真实报告截止日落后于用途对应的交易日时效阈值。'`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        message = (
            "真实报告截止日满足交易日时效阈值。"
            if passed
            else "真实报告截止日落后于用途对应的交易日时效阈值。"
        )
        # 结果返回：把`ReadinessEvidence(dimension=ReadinessDimension.FRESHNESS, status=status, code=code, message=message…`交给调用方并结束当前函数。
        # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return ReadinessEvidence(
            dimension=ReadinessDimension.FRESHNESS,
            status=status,
            code=code,
            message=message,
            metrics={
                "latest_available_date": latest,
                "expected_latest_trading_date": expected,
                "trading_session_lag": lag,
                "maximum_allowed_trading_session_lag": (
                    threshold
                ),
                "usage": usage.value,
                "calendar_source_title": (
                    self.calendar.source_title
                ),
            },
            evidence_refs=self._refs(dataset),
        )

    # 函数activation_evidence：执行activation_evidence逻辑。
    # - 参数dataset_id：类型str；进入函数后按合同参与校验、筛选、计算或路由。
    # - 参数usage：类型StandardDataUsage；进入函数后按合同参与校验、筛选、计算或路由。
    # - 参数as_of_date：类型date；进入函数后按合同参与校验、筛选、计算或路由。
    # - 输出：返回类型ReadinessEvidence；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
    # - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
    # - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
    def activation_evidence(
        self,
        dataset_id: str,
        usage: StandardDataUsage,
        as_of_date: date,
    ) -> ReadinessEvidence:
        # 异常边界：执行可能失败的解析、转换、文件读取或外部调用，并在后续分支转换为项目统一错误。
        # - 数据变化：成功路径产生正常结果；失败路径保留原异常作为cause、降级为缺失值或记录明确问题。
        # - 为什么这样写：上层只需处理稳定的DataContractError或受控结果，不依赖第三方异常实现细节。
        try:
            # 变量更新：计算并保存entry，右侧逻辑为`self.activations[dataset_id]`。
            # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
            # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
            entry = self.activations[dataset_id]
        # 异常转换：捕获KeyError，保存上下文并执行统一错误、回退或忽略策略。
        # - 数据变化：异常路径不返回未校验的半成品；必要时把失败原因写入issues、warnings或异常链。
        # - 为什么这样写：明确捕获范围可避免吞掉程序错误，同时让调用方获得稳定且可审计的失败语义。
        except KeyError as exc:
            # 错误阻断：抛出`DataContractError(f'启用注册表未登记数据集：{dataset_id}')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
            raise DataContractError(
                f"启用注册表未登记数据集：{dataset_id}"
            ) from exc

        # 变量更新：计算并保存effective，右侧逻辑为`entry.effective_from <= as_of_date`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        effective = entry.effective_from <= as_of_date
        # 变量更新：计算并保存allowed，右侧逻辑为`entry.enabled and effective and (usage in entry.allowed_usages)`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        allowed = (
            entry.enabled
            and effective
            and usage in entry.allowed_usages
        )
        # 变量更新：计算并保存status，右侧逻辑为`EvidenceStatus.PASSED if allowed else EvidenceStatus.FAILED`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        status = (
            EvidenceStatus.PASSED
            if allowed
            else EvidenceStatus.FAILED
        )
        # 变量更新：计算并保存code，右侧逻辑为`'DATASET_USAGE_ACTIVATION_VERIFIED' if allowed else 'DATASET_USAGE_NOT_ACTIVATED'`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        code = (
            "DATASET_USAGE_ACTIVATION_VERIFIED"
            if allowed
            else "DATASET_USAGE_NOT_ACTIVATED"
        )
        # 变量更新：计算并保存message，右侧逻辑为`'独立启用注册表确认该数据集可用于当前用途。' if allowed else '独立启用注册表未批准该数据集用于当前用途。'`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        message = (
            "独立启用注册表确认该数据集可用于当前用途。"
            if allowed
            else "独立启用注册表未批准该数据集用于当前用途。"
        )
        # 变量更新：计算并保存dataset，右侧逻辑为`self.config.dataset(dataset_id)`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        dataset = self.config.dataset(dataset_id)
        # 结果返回：把`ReadinessEvidence(dimension=ReadinessDimension.ACTIVATION, status=status, code=code, message=messag…`交给调用方并结束当前函数。
        # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return ReadinessEvidence(
            dimension=ReadinessDimension.ACTIVATION,
            status=status,
            code=code,
            message=message,
            metrics={
                "enabled": entry.enabled,
                "effective": effective,
                "activation_state": entry.activation_state,
                "allowed_usages": sorted(
                    item.value
                    for item in entry.allowed_usages
                ),
                "requested_usage": usage.value,
                "effective_from": entry.effective_from,
                "evidence_note": entry.evidence_note,
            },
            evidence_refs=self._refs(
                dataset,
                (
                    "config:"
                    + self.config.activation_path,
                ),
            ),
        )

    # 函数resolve：执行resolve逻辑。
    # - 关键字参数dataset_id：类型str，无默认值；只允许显式命名传入，降低参数错位风险。
    # - 关键字参数usage：类型StandardDataUsage，无默认值；只允许显式命名传入，降低参数错位风险。
    # - 关键字参数as_of_date：类型date | None，默认值None；只允许显式命名传入，降低参数错位风险。
    # - 输出：返回类型tuple[ReadinessEvidence, ...]；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
    # - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
    # - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
    def resolve(
        self,
        *,
        dataset_id: str,
        usage: StandardDataUsage,
        as_of_date: date | None = None,
    ) -> tuple[ReadinessEvidence, ...]:
        # 变量更新：计算并保存resolved_as_of，右侧逻辑为`as_of_date or self.config.as_of_date`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        resolved_as_of = as_of_date or self.config.as_of_date
        # 结果返回：把`(self.coverage_evidence(dataset_id), self.freshness_evidence(dataset_id, usage, resolved_as_of), se…`交给调用方并结束当前函数。
        # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return (
            self.coverage_evidence(dataset_id),
            self.freshness_evidence(
                dataset_id,
                usage,
                resolved_as_of,
            ),
            self.activation_evidence(
                dataset_id,
                usage,
                resolved_as_of,
            ),
        )


# 类ExternalEvidenceOverlayBuilder：在TASK_018B八维证据上覆盖三项真实外部证据。
# - 继承边界：基类为StandardQueryEvidenceBuilder；类体包含约0个字段或常量、2个方法。
# - 数据变化：类定义本身不执行隐式I/O，实例只在构造、校验或显式方法调用时产生受控状态。
# - 实操示例：调用方先构造该类型，再由方法完成校验、证据组合、路由或结果导出。
# - 为什么这样写：强类型边界能把相关不变量集中管理，减少字典键拼写、状态漂移和跨模块耦合。
class ExternalEvidenceOverlayBuilder(
    StandardQueryEvidenceBuilder
):
    """在TASK_018B八维证据上覆盖三项真实外部证据。"""

    # 函数__init__：执行__init__逻辑。
    # - 关键字参数base_rules：类型Any，无默认值；只允许显式命名传入，降低参数错位风险。
    # - 关键字参数resolver：类型ReportBackedEvidenceResolver，无默认值；只允许显式命名传入，降低参数错位风险。
    # - 输出：返回类型None；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
    # - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
    # - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
    def __init__(
        self,
        *,
        base_rules: Any,
        resolver: ReportBackedEvidenceResolver,
    ) -> None:
        # API或函数调用：执行`super().__init__`，完整调用片段为`super().__init__(base_rules)`。
        # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
        # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
        # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
        super().__init__(base_rules)
        # 变量更新：计算并保存self.resolver，右侧逻辑为`resolver`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        self.resolver = resolver

    # 函数build：执行build逻辑。
    # - 参数result：类型StandardQueryResult；进入函数后按合同参与校验、筛选、计算或路由。
    # - 参数descriptor：类型ProviderDescriptor；进入函数后按合同参与校验、筛选、计算或路由。
    # - 参数context：类型EvidenceBuildContext | None，默认值None；进入函数后按合同参与校验、筛选、计算或路由。
    # - 输出：返回类型tuple[ReadinessEvidence, ...]；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
    # - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
    # - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
    def build(
        self,
        result: StandardQueryResult,
        descriptor: ProviderDescriptor,
        context: EvidenceBuildContext | None = None,
    ) -> tuple[ReadinessEvidence, ...]:
        # 变量更新：计算并保存base，右侧逻辑为`list(super().build(result, descriptor, context))`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        base = list(
            super().build(result, descriptor, context)
        )
        # 变量更新：计算并保存overrides，右侧逻辑为`{item.dimension: item for item in self.resolver.resolve(dataset_id=result.query.dataset_id, usage=r…`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        overrides = {
            item.dimension: item
            for item in self.resolver.resolve(
                dataset_id=result.query.dataset_id,
                usage=result.query.usage,
                as_of_date=result.query.as_of_date,
            )
        }
        # 变量更新：计算并保存output，右侧逻辑为`tuple((overrides.get(item.dimension, item) for item in base))`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        output = tuple(
            overrides.get(item.dimension, item)
            for item in base
        )
        # 变量更新：计算并保存dimensions，右侧逻辑为`{item.dimension for item in output}`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        dimensions = {
            item.dimension
            for item in output
        }
        # 条件门禁：判断`dimensions != set(ReadinessDimension)`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if dimensions != set(ReadinessDimension):
            # 错误阻断：抛出`DataContractError('外部证据覆盖后必须完整保留八个维度。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
            raise DataContractError(
                "外部证据覆盖后必须完整保留八个维度。"
            )
        # 结果返回：把`output`交给调用方并结束当前函数。
        # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return output
