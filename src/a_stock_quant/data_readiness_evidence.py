# 模块总览：StandardDataService查询结果到统一数据就绪度证据的适配层。
# - 输入输出：本模块通过强类型合同、纯函数和显式服务调用交换数据，不在导入阶段执行数据库写入或交易动作。
# - 数据变化：只有显式构造、校验、查询、证据组合或报告导出才产生新对象与受控状态。
# - 时点与安全：就绪度和市场状态相关逻辑必须保留usage、as_of、available_at、血缘与阻断信息。
# - 为什么这样写：先声明模块边界，读者可以在阅读实现前理解职责、风险、数值语义和可复用方式。
"""StandardDataService查询结果到统一数据就绪度证据的适配层。

本模块只消费统一查询合同、Provider描述和显式补充上下文，生成八维证据与
DatasetReadinessDecision。它不连接数据库，不访问Raw表，也不替代Provider的
来源专属语义判断。
"""

# 依赖导入：执行`from __future__ import annotations`，加载下方合同、类型或标准库能力。
# - 数据变化：导入只把模块、类或函数绑定到当前命名空间，不在本行主动查询数据库或修改业务数据。
# - 为什么这样写：显式依赖使模块边界、可替换组件和测试注入点保持清晰。
from __future__ import annotations

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
# 依赖导入：执行`import json`，加载下方合同、类型或标准库能力。
# - 数据变化：导入只把模块、类或函数绑定到当前命名空间，不在本行主动查询数据库或修改业务数据。
# - 为什么这样写：显式依赖使模块边界、可替换组件和测试注入点保持清晰。
import json
# 依赖导入：执行`from pathlib import Path`，加载下方合同、类型或标准库能力。
# - 数据变化：导入只把模块、类或函数绑定到当前命名空间，不在本行主动查询数据库或修改业务数据。
# - 为什么这样写：显式依赖使模块边界、可替换组件和测试注入点保持清晰。
from pathlib import Path
# 依赖导入：执行`from typing import Any, Iterable, Mapping`，加载下方合同、类型或标准库能力。
# - 数据变化：导入只把模块、类或函数绑定到当前命名空间，不在本行主动查询数据库或修改业务数据。
# - 为什么这样写：显式依赖使模块边界、可替换组件和测试注入点保持清晰。
from typing import Any, Iterable, Mapping

# 依赖导入：执行`from .data_contracts import DataContractError, QualityStatus`，加载下方合同、类型或标准库能力。
# - 数据变化：导入只把模块、类或函数绑定到当前命名空间，不在本行主动查询数据库或修改业务数据。
# - 为什么这样写：显式依赖使模块边界、可替换组件和测试注入点保持清晰。
from .data_contracts import DataContractError, QualityStatus
# 依赖导入：执行`from .data_readiness import ( DataReadinessEngine, DataReadinessRequest,`，加载下方合同、类型或标准库能力。
# - 数据变化：导入只把模块、类或函数绑定到当前命名空间，不在本行主动查询数据库或修改业务数据。
# - 为什么这样写：显式依赖使模块边界、可替换组件和测试注入点保持清晰。
from .data_readiness import (
    DataReadinessEngine,
    DataReadinessRequest,
    DatasetReadinessDecision,
    EvidenceStatus,
    ReadinessDimension,
    ReadinessEvidence,
)
# 依赖导入：执行`from .standard_data_service import ( ProviderDescriptor, StandardDataQuery,`，加载下方合同、类型或标准库能力。
# - 数据变化：导入只把模块、类或函数绑定到当前命名空间，不在本行主动查询数据库或修改业务数据。
# - 为什么这样写：显式依赖使模块边界、可替换组件和测试注入点保持清晰。
from .standard_data_service import (
    ProviderDescriptor,
    StandardDataQuery,
    StandardDataRecord,
    StandardDataUsage,
    StandardQueryResult,
)

# 关键常量EVIDENCE_ADAPTER_VERSION：把`'0.1.0'`固定为本模块可追踪的合同值。
# - 来源：该值来自当前项目任务合同、配置或真实验收口径；未标注为行业标准时不得外推为通用值。
# - 数据范围：字符串常量用于版本、状态或模式标识；数值常量的单位和有效范围由相邻校验与调用语义约束。
# - 实操示例：报告和下游对象携带该值后，可以判断生产者版本并复现实验或验收过程。
# - 为什么这样写：集中命名固定参数可避免魔法值散落，并让配置升级、审计和兼容性检查有明确锚点。
EVIDENCE_ADAPTER_VERSION = "0.1.0"


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
    # 条件门禁：判断`isinstance(value, Mapping)`，条件为真时进入受保护分支。
    # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
    # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
    # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
    if isinstance(value, Mapping):
        # 结果返回：把`{str(k): _json_safe(v) for k, v in value.items()}`交给调用方并结束当前函数。
        # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return {str(k): _json_safe(v) for k, v in value.items()}
    # 条件门禁：判断`isinstance(value, (tuple, list, set, frozenset))`，条件为真时进入受保护分支。
    # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
    # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
    # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
    if isinstance(value, (tuple, list, set, frozenset)):
        # 结果返回：把`[_json_safe(item) for item in value]`交给调用方并结束当前函数。
        # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return [_json_safe(item) for item in value]
    # 结果返回：把`value`交给调用方并结束当前函数。
    # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return value


# 类EvidenceRuleConfig：证据适配器的可维护规则。
# - 继承边界：基类为object；类体包含约9个字段或常量、1个方法。
# - 数据变化：类定义本身不执行隐式I/O，实例只在构造、校验或显式方法调用时产生受控状态。
# - 实操示例：调用方先构造该类型，再由方法完成校验、证据组合、路由或结果导出。
# - 为什么这样写：强类型边界能把相关不变量集中管理，减少字典键拼写、状态漂移和跨模块耦合。
@dataclass(frozen=True, slots=True)
class EvidenceRuleConfig:
    """证据适配器的可维护规则。"""

    # 字段或变量rules_version：声明类型str，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    rules_version: str
    # 字段或变量entity_key_candidates：声明类型tuple[str, ...]，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    entity_key_candidates: tuple[str, ...]
    # 字段或变量date_field_candidates：声明类型tuple[str, ...]，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    date_field_candidates: tuple[str, ...]
    # 字段或变量temporal_warning_markers：声明类型tuple[str, ...]，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    temporal_warning_markers: tuple[str, ...]
    # 字段或变量default_minimum_coverage_ratio：声明类型float，初始逻辑为`1.0`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    default_minimum_coverage_ratio: float = 1.0
    # 字段或变量default_max_freshness_lag_days：声明类型int，初始逻辑为`0`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    default_max_freshness_lag_days: int = 0
    # 字段或变量coverage_scope_requires_external_evidence：声明类型bool，初始逻辑为`True`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    coverage_scope_requires_external_evidence: bool = True
    # 字段或变量freshness_scope_requires_external_evidence：声明类型bool，初始逻辑为`True`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    freshness_scope_requires_external_evidence: bool = True
    # 字段或变量activation_requires_external_verification：声明类型bool，初始逻辑为`True`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    activation_requires_external_verification: bool = True

    # 函数__post_init__：执行__post_init__逻辑。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态、模块常量或封装依赖。
    # - 输出：返回类型None；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
    # - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
    # - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
    def __post_init__(self) -> None:
        # API或函数调用：执行`object.__setattr__`，完整调用片段为`object.__setattr__(self, 'rules_version', _require_text(self.rules_version, 'rules_version'))`。
        # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
        # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
        # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
        object.__setattr__(self, 'rules_version', _require_text(self.rules_version, 'rules_version'))
        # 迭代处理：依次从`('entity_key_candidates', 'date_field_candidates', 'temporal_warning_markers')`读取元素，并绑定到`field_name`。
        # - 维度变化：每轮处理一个记录、字段、证据或配置项，可能向列表、字典或累计统计增加一项。
        # - 为什么这样写：显式逐项处理便于保留顺序、定位坏数据，并对每个实体执行同一合同。
        for field_name in ('entity_key_candidates','date_field_candidates','temporal_warning_markers'):
            # 变量更新：计算并保存values，右侧逻辑为`tuple((_require_text(v, field_name) for v in getattr(self, field_name)))`。
            # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
            # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
            values = tuple(_require_text(v, field_name) for v in getattr(self, field_name))
            # 条件门禁：判断`not values or len(values) != len(set(values))`，条件为真时进入受保护分支。
            # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
            # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
            # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
            if not values or len(values) != len(set(values)):
                # 错误阻断：抛出`DataContractError(f'{field_name}不能为空或重复。')`并停止当前正常路径。
                # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
                # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
                raise DataContractError(f'{field_name}不能为空或重复。')
            # API或函数调用：执行`object.__setattr__`，完整调用片段为`object.__setattr__(self, field_name, values)`。
            # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
            # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
            # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
            object.__setattr__(self, field_name, values)
        # 条件门禁：判断`not 0 < self.default_minimum_coverage_ratio <= 1`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if not 0 < self.default_minimum_coverage_ratio <= 1:
            # 错误阻断：抛出`DataContractError('default_minimum_coverage_ratio必须在(0,1]。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
            raise DataContractError('default_minimum_coverage_ratio必须在(0,1]。')
        # 条件门禁：判断`self.default_max_freshness_lag_days < 0`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if self.default_max_freshness_lag_days < 0:
            # 错误阻断：抛出`DataContractError('default_max_freshness_lag_days不能为负。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
            raise DataContractError('default_max_freshness_lag_days不能为负。')


# 类EvidenceBuildContext：Provider查询结果以外的显式证据上下文。
# - 继承边界：基类为object；类体包含约20个字段或常量、1个方法。
# - 数据变化：类定义本身不执行隐式I/O，实例只在构造、校验或显式方法调用时产生受控状态。
# - 实操示例：调用方先构造该类型，再由方法完成校验、证据组合、路由或结果导出。
# - 为什么这样写：强类型边界能把相关不变量集中管理，减少字典键拼写、状态漂移和跨模块耦合。
@dataclass(frozen=True, slots=True)
class EvidenceBuildContext:
    """Provider查询结果以外的显式证据上下文。"""

    # 字段或变量expected_entity_count：声明类型int | None，初始逻辑为`None`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    expected_entity_count: int | None = None
    # 字段或变量observed_entity_count：声明类型int | None，初始逻辑为`None`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    observed_entity_count: int | None = None
    # 字段或变量minimum_coverage_ratio：声明类型float | None，初始逻辑为`None`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    minimum_coverage_ratio: float | None = None
    # 字段或变量coverage_scope_proven：声明类型bool，初始逻辑为`False`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    coverage_scope_proven: bool = False
    # 字段或变量expected_through_date：声明类型date | None，初始逻辑为`None`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    expected_through_date: date | None = None
    # 字段或变量latest_available_date：声明类型date | None，初始逻辑为`None`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    latest_available_date: date | None = None
    # 字段或变量max_freshness_lag_days：声明类型int | None，初始逻辑为`None`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    max_freshness_lag_days: int | None = None
    # 字段或变量freshness_scope_proven：声明类型bool，初始逻辑为`False`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    freshness_scope_proven: bool = False
    # 字段或变量stale_is_failure：声明类型bool，初始逻辑为`False`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    stale_is_failure: bool = False
    # 字段或变量temporal_status：声明类型EvidenceStatus | None，初始逻辑为`None`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    temporal_status: EvidenceStatus | None = None
    # 字段或变量temporal_code：声明类型str | None，初始逻辑为`None`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    temporal_code: str | None = None
    # 字段或变量temporal_message：声明类型str | None，初始逻辑为`None`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    temporal_message: str | None = None
    # 字段或变量semantic_status：声明类型EvidenceStatus | None，初始逻辑为`None`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    semantic_status: EvidenceStatus | None = None
    # 字段或变量semantic_code：声明类型str | None，初始逻辑为`None`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    semantic_code: str | None = None
    # 字段或变量semantic_message：声明类型str | None，初始逻辑为`None`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    semantic_message: str | None = None
    # 字段或变量activation_status：声明类型EvidenceStatus | None，初始逻辑为`None`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    activation_status: EvidenceStatus | None = None
    # 字段或变量activation_code：声明类型str | None，初始逻辑为`None`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    activation_code: str | None = None
    # 字段或变量activation_message：声明类型str | None，初始逻辑为`None`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    activation_message: str | None = None
    # 字段或变量activation_verified：声明类型bool，初始逻辑为`False`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    activation_verified: bool = False
    # 字段或变量evidence_refs：声明类型tuple[str, ...]，初始逻辑为`()`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    evidence_refs: tuple[str, ...] = ()

    # 函数__post_init__：执行__post_init__逻辑。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态、模块常量或封装依赖。
    # - 输出：返回类型None；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
    # - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
    # - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
    def __post_init__(self) -> None:
        # 迭代处理：依次从`('expected_entity_count', 'observed_entity_count', 'max_freshness_lag_days')`读取元素，并绑定到`name`。
        # - 维度变化：每轮处理一个记录、字段、证据或配置项，可能向列表、字典或累计统计增加一项。
        # - 为什么这样写：显式逐项处理便于保留顺序、定位坏数据，并对每个实体执行同一合同。
        for name in ('expected_entity_count','observed_entity_count','max_freshness_lag_days'):
            # 变量更新：计算并保存value，右侧逻辑为`getattr(self, name)`。
            # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
            # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
            value = getattr(self, name)
            # 条件门禁：判断`value is not None and value < 0`，条件为真时进入受保护分支。
            # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
            # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
            # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
            if value is not None and value < 0:
                # 错误阻断：抛出`DataContractError(f'{name}不能为负。')`并停止当前正常路径。
                # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
                # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
                raise DataContractError(f'{name}不能为负。')
        # 条件门禁：判断`self.minimum_coverage_ratio is not None and (not 0 < self.minimum_coverage_ratio <= 1)`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if self.minimum_coverage_ratio is not None and not 0 < self.minimum_coverage_ratio <= 1:
            # 错误阻断：抛出`DataContractError('minimum_coverage_ratio必须在(0,1]。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
            raise DataContractError('minimum_coverage_ratio必须在(0,1]。')
        # 条件门禁：判断`self.latest_available_date and self.expected_through_date`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if self.latest_available_date and self.expected_through_date:
            # 条件门禁：判断`not isinstance(self.latest_available_date, date) or not isinstance(self.expected_through_date, date)`，条件为真时进入受保护分支。
            # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
            # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
            # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
            if not isinstance(self.latest_available_date, date) or not isinstance(self.expected_through_date, date):
                # 错误阻断：抛出`DataContractError('新鲜度日期必须是date。')`并停止当前正常路径。
                # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
                # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
                raise DataContractError('新鲜度日期必须是date。')
        # 变量更新：计算并保存refs，右侧逻辑为`tuple((_require_text(v, 'evidence_refs') for v in self.evidence_refs))`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        refs = tuple(_require_text(v, 'evidence_refs') for v in self.evidence_refs)
        # 条件门禁：判断`len(refs) != len(set(refs))`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if len(refs) != len(set(refs)):
            # 错误阻断：抛出`DataContractError('evidence_refs不允许重复。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
            raise DataContractError('evidence_refs不允许重复。')
        # API或函数调用：执行`object.__setattr__`，完整调用片段为`object.__setattr__(self, 'evidence_refs', refs)`。
        # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
        # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
        # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
        object.__setattr__(self, 'evidence_refs', refs)


# 类DatasetReadinessSnapshot：一次标准查询对应的可审计就绪度快照。
# - 继承边界：基类为object；类体包含约10个字段或常量、3个方法。
# - 数据变化：类定义本身不执行隐式I/O，实例只在构造、校验或显式方法调用时产生受控状态。
# - 实操示例：调用方先构造该类型，再由方法完成校验、证据组合、路由或结果导出。
# - 为什么这样写：强类型边界能把相关不变量集中管理，减少字典键拼写、状态漂移和跨模块耦合。
@dataclass(frozen=True, slots=True)
class DatasetReadinessSnapshot:
    """一次标准查询对应的可审计就绪度快照。"""

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
    # 字段或变量query_id：声明类型str，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    query_id: str
    # 字段或变量usage：声明类型StandardDataUsage，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    usage: StandardDataUsage
    # 字段或变量adapter_version：声明类型str，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    adapter_version: str
    # 字段或变量rules_version：声明类型str，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    rules_version: str
    # 字段或变量evidence：声明类型tuple[ReadinessEvidence, ...]，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    evidence: tuple[ReadinessEvidence, ...]
    # 字段或变量decision：声明类型DatasetReadinessDecision，初始逻辑为`仅类型声明`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    decision: DatasetReadinessDecision
    # 字段或变量generated_at：声明类型datetime，初始逻辑为`field(default_factory=lambda: datetime.now(timezone.utc))`。
    # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
    # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # 函数__post_init__：执行__post_init__逻辑。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态、模块常量或封装依赖。
    # - 输出：返回类型None；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
    # - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
    # - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
    def __post_init__(self) -> None:
        # 迭代处理：依次从`('dataset_id', 'canonical_object', 'provider_id', 'query_id', 'adapter_version', 'rules_version')`读取元素，并绑定到`name`。
        # - 维度变化：每轮处理一个记录、字段、证据或配置项，可能向列表、字典或累计统计增加一项。
        # - 为什么这样写：显式逐项处理便于保留顺序、定位坏数据，并对每个实体执行同一合同。
        for name in ('dataset_id','canonical_object','provider_id','query_id','adapter_version','rules_version'):
            # API或函数调用：执行`object.__setattr__`，完整调用片段为`object.__setattr__(self, name, _require_text(getattr(self, name), name))`。
            # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
            # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
            # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
            object.__setattr__(self, name, _require_text(getattr(self, name), name))
        # 条件门禁：判断`self.decision.dataset_id != self.dataset_id`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if self.decision.dataset_id != self.dataset_id:
            # 错误阻断：抛出`DataContractError('快照与决策dataset_id不一致。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
            raise DataContractError('快照与决策dataset_id不一致。')
        # 条件门禁：判断`self.decision.usage is not self.usage`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if self.decision.usage is not self.usage:
            # 错误阻断：抛出`DataContractError('快照与决策usage不一致。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
            raise DataContractError('快照与决策usage不一致。')
        # 变量更新：计算并保存dimensions，右侧逻辑为`{item.dimension for item in self.evidence}`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        dimensions = {item.dimension for item in self.evidence}
        # 条件门禁：判断`dimensions != set(ReadinessDimension)`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if dimensions != set(ReadinessDimension):
            # 错误阻断：抛出`DataContractError('快照必须完整包含八个就绪度维度。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
            raise DataContractError('快照必须完整包含八个就绪度维度。')

    # 函数assert_usable：执行assert_usable逻辑。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态、模块常量或封装依赖。
    # - 输出：返回类型None；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
    # - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
    # - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
    def assert_usable(self) -> None:
        # API或函数调用：执行`self.decision.assert_usable`，完整调用片段为`self.decision.assert_usable()`。
        # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
        # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
        # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
        self.decision.assert_usable()

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


# 函数load_evidence_rule_config：执行load_evidence_rule_config逻辑。
# - 参数path：类型str | Path；进入函数后按合同参与校验、筛选、计算或路由。
# - 输出：返回类型EvidenceRuleConfig；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
# - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
# - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
def load_evidence_rule_config(path: str | Path) -> EvidenceRuleConfig:
    # 变量更新：计算并保存rule_path，右侧逻辑为`Path(path)`。
    # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
    # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
    rule_path = Path(path)
    # 异常边界：执行可能失败的解析、转换、文件读取或外部调用，并在后续分支转换为项目统一错误。
    # - 数据变化：成功路径产生正常结果；失败路径保留原异常作为cause、降级为缺失值或记录明确问题。
    # - 为什么这样写：上层只需处理稳定的DataContractError或受控结果，不依赖第三方异常实现细节。
    try:
        # 变量更新：计算并保存raw，右侧逻辑为`json.loads(rule_path.read_text(encoding='utf-8'))`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        raw = json.loads(rule_path.read_text(encoding='utf-8'))
    # 异常转换：捕获(OSError, json.JSONDecodeError)，保存上下文并执行统一错误、回退或忽略策略。
    # - 数据变化：异常路径不返回未校验的半成品；必要时把失败原因写入issues、warnings或异常链。
    # - 为什么这样写：明确捕获范围可避免吞掉程序错误，同时让调用方获得稳定且可审计的失败语义。
    except (OSError, json.JSONDecodeError) as exc:
        # 错误阻断：抛出`DataContractError(f'无法加载证据规则：{rule_path}')`并停止当前正常路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
        # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
        raise DataContractError(f'无法加载证据规则：{rule_path}') from exc
    # 条件门禁：判断`not isinstance(raw, dict)`，条件为真时进入受保护分支。
    # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
    # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
    # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
    if not isinstance(raw, dict):
        # 错误阻断：抛出`DataContractError('证据规则根节点必须是对象。')`并停止当前正常路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
        # - 为什么这样写：发现合同破坏、时点风险或不安全输入时立即失败，比静默修正更可靠。
        raise DataContractError('证据规则根节点必须是对象。')
    # 结果返回：把`EvidenceRuleConfig(rules_version=str(raw['rules_version']), entity_key_candidates=tuple(raw['entity…`交给调用方并结束当前函数。
    # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return EvidenceRuleConfig(
        rules_version=str(raw['rules_version']),
        entity_key_candidates=tuple(raw['entity_key_candidates']),
        date_field_candidates=tuple(raw['date_field_candidates']),
        temporal_warning_markers=tuple(raw['temporal_warning_markers']),
        default_minimum_coverage_ratio=float(raw.get('default_minimum_coverage_ratio', 1.0)),
        default_max_freshness_lag_days=int(raw.get('default_max_freshness_lag_days', 0)),
        coverage_scope_requires_external_evidence=bool(raw.get('coverage_scope_requires_external_evidence', True)),
        freshness_scope_requires_external_evidence=bool(raw.get('freshness_scope_requires_external_evidence', True)),
        activation_requires_external_verification=bool(raw.get('activation_requires_external_verification', True)),
    )


# 类StandardQueryEvidenceBuilder：把统一查询结果确定性地映射为八维证据。
# - 继承边界：基类为object；类体包含约0个字段或常量、16个方法。
# - 数据变化：类定义本身不执行隐式I/O，实例只在构造、校验或显式方法调用时产生受控状态。
# - 实操示例：调用方先构造该类型，再由方法完成校验、证据组合、路由或结果导出。
# - 为什么这样写：强类型边界能把相关不变量集中管理，减少字典键拼写、状态漂移和跨模块耦合。
class StandardQueryEvidenceBuilder:
    """把统一查询结果确定性地映射为八维证据。"""

    # 函数__init__：执行__init__逻辑。
    # - 参数rules：类型EvidenceRuleConfig；进入函数后按合同参与校验、筛选、计算或路由。
    # - 输出：返回类型None；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
    # - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
    # - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
    def __init__(self, rules: EvidenceRuleConfig) -> None:
        # 变量更新：计算并保存self.rules，右侧逻辑为`rules`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        self.rules = rules

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
        # 变量更新：计算并保存ctx，右侧逻辑为`context or EvidenceBuildContext()`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        ctx = context or EvidenceBuildContext()
        # 结果返回：把`(self._contract(result, descriptor, ctx), self._query_execution(result, ctx), self._coverage(result…`交给调用方并结束当前函数。
        # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return (
            self._contract(result, descriptor, ctx),
            self._query_execution(result, ctx),
            self._coverage(result, ctx),
            self._freshness(result, ctx),
            self._lineage(result, ctx),
            self._temporal(result, ctx),
            self._semantic(result, ctx),
            self._activation(result, descriptor, ctx),
        )

    # 函数_refs：执行_refs逻辑。
    # - 参数result：类型StandardQueryResult；进入函数后按合同参与校验、筛选、计算或路由。
    # - 参数ctx：类型EvidenceBuildContext；进入函数后按合同参与校验、筛选、计算或路由。
    # - 可变位置参数extra：类型str；按调用顺序收集为tuple。
    # - 输出：返回类型tuple[str, ...]；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
    # - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
    # - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
    def _refs(self, result: StandardQueryResult, ctx: EvidenceBuildContext, *extra: str) -> tuple[str, ...]:
        # 变量更新：计算并保存refs，右侧逻辑为`[f'query:{result.metadata.query_id}', f'provider:{result.metadata.provider_id}', *ctx.evidence_refs…`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        refs = [f'query:{result.metadata.query_id}', f'provider:{result.metadata.provider_id}', *ctx.evidence_refs, *extra]
        # 结果返回：把`tuple(dict.fromkeys(refs))`交给调用方并结束当前函数。
        # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return tuple(dict.fromkeys(refs))

    # 函数_contract：执行_contract逻辑。
    # - 参数result：类型StandardQueryResult；进入函数后按合同参与校验、筛选、计算或路由。
    # - 参数descriptor：类型ProviderDescriptor；进入函数后按合同参与校验、筛选、计算或路由。
    # - 参数ctx：类型EvidenceBuildContext；进入函数后按合同参与校验、筛选、计算或路由。
    # - 输出：返回类型ReadinessEvidence；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
    # - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
    # - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
    def _contract(self, result: StandardQueryResult, descriptor: ProviderDescriptor, ctx: EvidenceBuildContext) -> ReadinessEvidence:
        # 字段或变量failures：声明类型list[str]，初始逻辑为`[]`。
        # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
        # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
        failures: list[str] = []
        # 变量更新：计算并保存pairs，右侧逻辑为`(('dataset_id', result.metadata.dataset_id, descriptor.dataset_id), ('provider_id', result.metadata…`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        pairs = (
            ('dataset_id', result.metadata.dataset_id, descriptor.dataset_id),
            ('provider_id', result.metadata.provider_id, descriptor.provider_id),
            ('coverage_version', result.metadata.coverage_version, descriptor.coverage_version),
            ('mapping_version', result.metadata.mapping_version, descriptor.mapping_version),
            ('dictionary_revision', result.metadata.dictionary_revision, descriptor.dictionary_revision),
        )
        # 迭代处理：依次从`pairs`读取元素，并绑定到`name, actual, expected`。
        # - 维度变化：每轮处理一个记录、字段、证据或配置项，可能向列表、字典或累计统计增加一项。
        # - 为什么这样写：显式逐项处理便于保留顺序、定位坏数据，并对每个实体执行同一合同。
        for name, actual, expected in pairs:
            # 条件门禁：判断`actual != expected`，条件为真时进入受保护分支。
            # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
            # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
            # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
            if actual != expected:
                # API或函数调用：执行`failures.append`，完整调用片段为`failures.append(f'{name}:{actual}!={expected}')`。
                # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
                # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
                # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
                failures.append(f'{name}:{actual}!={expected}')
        # 条件门禁：判断`result.query.canonical_object not in descriptor.supported_objects`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if result.query.canonical_object not in descriptor.supported_objects:
            # API或函数调用：执行`failures.append`，完整调用片段为`failures.append('canonical_object_not_supported')`。
            # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
            # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
            # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
            failures.append('canonical_object_not_supported')
        # 条件门禁：判断`result.query.selector_mode != descriptor.selector_mode`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if result.query.selector_mode != descriptor.selector_mode:
            # API或函数调用：执行`failures.append`，完整调用片段为`failures.append('selector_mode_mismatch')`。
            # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
            # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
            # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
            failures.append('selector_mode_mismatch')
        # 变量更新：计算并保存status，右侧逻辑为`EvidenceStatus.FAILED if failures else EvidenceStatus.PASSED`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        status = EvidenceStatus.FAILED if failures else EvidenceStatus.PASSED
        # 结果返回：把`ReadinessEvidence(dimension=ReadinessDimension.CONTRACT, status=status, code='CONTRACT_MISMATCH' if…`交给调用方并结束当前函数。
        # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return ReadinessEvidence(
            dimension=ReadinessDimension.CONTRACT,
            status=status,
            code='CONTRACT_MISMATCH' if failures else 'CONTRACT_MATCHED',
            message='统一查询合同与Provider描述不一致。' if failures else '统一查询合同、版本和Provider描述一致。',
            metrics={'failures': failures, 'supported_objects': list(descriptor.supported_objects), 'selector_mode': descriptor.selector_mode},
            evidence_refs=self._refs(result, ctx, f'coverage:{descriptor.coverage_version}', f'mapping:{descriptor.mapping_version}', f'dictionary:{descriptor.dictionary_revision}'),
        )

    # 函数_query_execution：执行_query_execution逻辑。
    # - 参数result：类型StandardQueryResult；进入函数后按合同参与校验、筛选、计算或路由。
    # - 参数ctx：类型EvidenceBuildContext；进入函数后按合同参与校验、筛选、计算或路由。
    # - 输出：返回类型ReadinessEvidence；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
    # - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
    # - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
    def _query_execution(self, result: StandardQueryResult, ctx: EvidenceBuildContext) -> ReadinessEvidence:
        # 变量更新：计算并保存quality，右侧逻辑为`result.metadata.status`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        quality = result.metadata.status
        # 条件门禁：判断`result.metadata.blocks_downstream or quality is QualityStatus.FAILED`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if result.metadata.blocks_downstream or quality is QualityStatus.FAILED:
            # 变量更新：计算并保存status, code，右侧逻辑为`(EvidenceStatus.FAILED, 'QUERY_BLOCKED')`。
            # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
            # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
            status, code = EvidenceStatus.FAILED, 'QUERY_BLOCKED'
        # 条件门禁：判断`quality in {QualityStatus.WARNING, QualityStatus.PENDING_CONFIRMATION}`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        elif quality in {QualityStatus.WARNING, QualityStatus.PENDING_CONFIRMATION}:
            # 变量更新：计算并保存status, code，右侧逻辑为`(EvidenceStatus.WARNING, 'QUERY_COMPLETED_WITH_WARNINGS')`。
            # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
            # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
            status, code = EvidenceStatus.WARNING, 'QUERY_COMPLETED_WITH_WARNINGS'
        else:
            # 变量更新：计算并保存status, code，右侧逻辑为`(EvidenceStatus.PASSED, 'QUERY_COMPLETED')`。
            # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
            # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
            status, code = EvidenceStatus.PASSED, 'QUERY_COMPLETED'
        # 结果返回：把`ReadinessEvidence(dimension=ReadinessDimension.QUERY_EXECUTION, status=status, code=code, message='…`交给调用方并结束当前函数。
        # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return ReadinessEvidence(
            dimension=ReadinessDimension.QUERY_EXECUTION,
            status=status,
            code=code,
            message='标准查询已完成并生成结构化结果。' if status is not EvidenceStatus.FAILED else '标准查询结果被Provider质量门禁阻断。',
            metrics={'quality_status': quality.value, 'blocks_downstream': result.metadata.blocks_downstream, 'source_row_count': result.metadata.source_row_count, 'result_count': result.metadata.result_count},
            evidence_refs=self._refs(result, ctx),
        )

    # 函数_entity_values：执行_entity_values逻辑。
    # - 参数records：类型Iterable[StandardDataRecord]；进入函数后按合同参与校验、筛选、计算或路由。
    # - 输出：返回类型set[str]；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
    # - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
    # - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
    def _entity_values(self, records: Iterable[StandardDataRecord]) -> set[str]:
        # 字段或变量values：声明类型set[str]，初始逻辑为`set()`。
        # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
        # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
        values: set[str] = set()
        # 迭代处理：依次从`records`读取元素，并绑定到`record`。
        # - 维度变化：每轮处理一个记录、字段、证据或配置项，可能向列表、字典或累计统计增加一项。
        # - 为什么这样写：显式逐项处理便于保留顺序、定位坏数据，并对每个实体执行同一合同。
        for record in records:
            # 变量更新：计算并保存combined，右侧逻辑为`{**record.values, **record.primary_key}`。
            # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
            # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
            combined = {**record.values, **record.primary_key}
            # 迭代处理：依次从`self.rules.entity_key_candidates`读取元素，并绑定到`key`。
            # - 维度变化：每轮处理一个记录、字段、证据或配置项，可能向列表、字典或累计统计增加一项。
            # - 为什么这样写：显式逐项处理便于保留顺序、定位坏数据，并对每个实体执行同一合同。
            for key in self.rules.entity_key_candidates:
                # 变量更新：计算并保存value，右侧逻辑为`combined.get(key)`。
                # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
                # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
                value = combined.get(key)
                # 条件门禁：判断`value is not None and str(value).strip()`，条件为真时进入受保护分支。
                # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
                # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
                # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
                if value is not None and str(value).strip():
                    # API或函数调用：执行`values.add`，完整调用片段为`values.add(str(value).strip())`。
                    # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
                    # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
                    # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
                    values.add(str(value).strip())
                    # 循环提前结束：当前条件已满足，不再处理剩余元素。
                    # - 数据变化：保留已累计结果，并把控制流移动到循环之后。
                    # - 为什么这样写：在找到唯一结果或达到安全上限后停止，可减少不必要计算。
                    break
        # 结果返回：把`values`交给调用方并结束当前函数。
        # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return values

    # 函数_coverage：执行_coverage逻辑。
    # - 参数result：类型StandardQueryResult；进入函数后按合同参与校验、筛选、计算或路由。
    # - 参数ctx：类型EvidenceBuildContext；进入函数后按合同参与校验、筛选、计算或路由。
    # - 输出：返回类型ReadinessEvidence；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
    # - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
    # - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
    def _coverage(self, result: StandardQueryResult, ctx: EvidenceBuildContext) -> ReadinessEvidence:
        # 变量更新：计算并保存expected，右侧逻辑为`ctx.expected_entity_count`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        expected = ctx.expected_entity_count
        # 条件门禁：判断`expected is None`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if expected is None:
            # 变量更新：计算并保存expected，右侧逻辑为`len(result.query.selector_ids)`。
            # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
            # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
            expected = len(result.query.selector_ids)
        # 变量更新：计算并保存observed，右侧逻辑为`ctx.observed_entity_count`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        observed = ctx.observed_entity_count
        # 条件门禁：判断`observed is None`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if observed is None:
            # 变量更新：计算并保存observed，右侧逻辑为`len(self._entity_values(result.records))`。
            # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
            # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
            observed = len(self._entity_values(result.records))
        # 变量更新：计算并保存ratio，右侧逻辑为`0.0 if expected == 0 else min(observed / expected, 1.0)`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        ratio = 0.0 if expected == 0 else min(observed / expected, 1.0)
        # 变量更新：计算并保存threshold，右侧逻辑为`ctx.minimum_coverage_ratio or self.rules.default_minimum_coverage_ratio`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        threshold = ctx.minimum_coverage_ratio or self.rules.default_minimum_coverage_ratio
        # 变量更新：计算并保存metrics，右侧逻辑为`{'expected_entity_count': expected, 'observed_entity_count': observed, 'coverage_ratio': ratio, 'mi…`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        metrics = {'expected_entity_count': expected, 'observed_entity_count': observed, 'coverage_ratio': ratio, 'minimum_coverage_ratio': threshold, 'scope_proven': ctx.coverage_scope_proven, 'result_count': result.metadata.result_count}
        # 条件门禁：判断`result.metadata.result_count == 0 or observed == 0`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if result.metadata.result_count == 0 or observed == 0:
            # 变量更新：计算并保存status, code, message，右侧逻辑为`(EvidenceStatus.FAILED, 'COVERAGE_EMPTY', '查询范围没有返回可用标准记录。')`。
            # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
            # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
            status, code, message = EvidenceStatus.FAILED, 'COVERAGE_EMPTY', '查询范围没有返回可用标准记录。'
        # 条件门禁：判断`ratio < threshold`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        elif ratio < threshold:
            # 变量更新：计算并保存status, code, message，右侧逻辑为`(EvidenceStatus.WARNING, 'COVERAGE_BELOW_THRESHOLD', '查询实体覆盖低于阈值。')`。
            # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
            # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
            status, code, message = EvidenceStatus.WARNING, 'COVERAGE_BELOW_THRESHOLD', '查询实体覆盖低于阈值。'
        # 条件门禁：判断`ctx.coverage_scope_proven or not self.rules.coverage_scope_requires_external_evidence`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        elif ctx.coverage_scope_proven or not self.rules.coverage_scope_requires_external_evidence:
            # 变量更新：计算并保存status, code, message，右侧逻辑为`(EvidenceStatus.PASSED, 'COVERAGE_PROVEN', '外部覆盖证据和查询结果满足阈值。')`。
            # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
            # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
            status, code, message = EvidenceStatus.PASSED, 'COVERAGE_PROVEN', '外部覆盖证据和查询结果满足阈值。'
        else:
            # 变量更新：计算并保存status, code, message，右侧逻辑为`(EvidenceStatus.WARNING, 'QUERY_SCOPE_COVERAGE_ONLY', '当前只能证明本次查询实体覆盖，尚不能证明数据集级完整覆盖。')`。
            # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
            # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
            status, code, message = EvidenceStatus.WARNING, 'QUERY_SCOPE_COVERAGE_ONLY', '当前只能证明本次查询实体覆盖，尚不能证明数据集级完整覆盖。'
        # 结果返回：把`ReadinessEvidence(ReadinessDimension.COVERAGE, status, code, message, metrics, self._refs(result, c…`交给调用方并结束当前函数。
        # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return ReadinessEvidence(ReadinessDimension.COVERAGE, status, code, message, metrics, self._refs(result, ctx))

    # 函数_as_date：执行_as_date逻辑。
    # - 参数value：类型Any；进入函数后按合同参与校验、筛选、计算或路由。
    # - 输出：返回类型date | None；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
    # - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
    # - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
    @staticmethod
    def _as_date(value: Any) -> date | None:
        # 条件门禁：判断`isinstance(value, datetime)`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        # 结果返回：把`value.date()`交给调用方并结束当前函数。
        # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        if isinstance(value, datetime): return value.date()
        # 条件门禁：判断`isinstance(value, date)`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        # 结果返回：把`value`交给调用方并结束当前函数。
        # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        if isinstance(value, date): return value
        # 条件门禁：判断`isinstance(value, str)`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if isinstance(value, str):
            # 异常边界：执行可能失败的解析、转换、文件读取或外部调用，并在后续分支转换为项目统一错误。
            # - 数据变化：成功路径产生正常结果；失败路径保留原异常作为cause、降级为缺失值或记录明确问题。
            # - 为什么这样写：上层只需处理稳定的DataContractError或受控结果，不依赖第三方异常实现细节。
            # 结果返回：把`date.fromisoformat(value[:10])`交给调用方并结束当前函数。
            # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
            # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
            try: return date.fromisoformat(value[:10])
            # 异常转换：捕获ValueError，保存上下文并执行统一错误、回退或忽略策略。
            # - 数据变化：异常路径不返回未校验的半成品；必要时把失败原因写入issues、warnings或异常链。
            # - 为什么这样写：明确捕获范围可避免吞掉程序错误，同时让调用方获得稳定且可审计的失败语义。
            # 结果返回：把`None`交给调用方并结束当前函数。
            # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
            # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
            except ValueError: return None
        # 结果返回：把`None`交给调用方并结束当前函数。
        # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return None

    # 函数_latest_record_date：执行_latest_record_date逻辑。
    # - 参数records：类型Iterable[StandardDataRecord]；进入函数后按合同参与校验、筛选、计算或路由。
    # - 输出：返回类型date | None；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
    # - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
    # - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
    def _latest_record_date(self, records: Iterable[StandardDataRecord]) -> date | None:
        # 字段或变量dates：声明类型list[date]，初始逻辑为`[]`。
        # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
        # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
        dates: list[date] = []
        # 迭代处理：依次从`records`读取元素，并绑定到`record`。
        # - 维度变化：每轮处理一个记录、字段、证据或配置项，可能向列表、字典或累计统计增加一项。
        # - 为什么这样写：显式逐项处理便于保留顺序、定位坏数据，并对每个实体执行同一合同。
        for record in records:
            # 变量更新：计算并保存combined，右侧逻辑为`{**record.values, **record.primary_key}`。
            # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
            # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
            combined = {**record.values, **record.primary_key}
            # 迭代处理：依次从`self.rules.date_field_candidates`读取元素，并绑定到`key`。
            # - 维度变化：每轮处理一个记录、字段、证据或配置项，可能向列表、字典或累计统计增加一项。
            # - 为什么这样写：显式逐项处理便于保留顺序、定位坏数据，并对每个实体执行同一合同。
            for key in self.rules.date_field_candidates:
                # 变量更新：计算并保存parsed，右侧逻辑为`self._as_date(combined.get(key))`。
                # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
                # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
                parsed = self._as_date(combined.get(key))
                # 条件门禁：判断`parsed is not None`，条件为真时进入受保护分支。
                # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
                # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
                # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
                if parsed is not None:
                    # API或函数调用：执行`dates.append`，完整调用片段为`dates.append(parsed)`。
                    # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
                    # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
                    # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
                    dates.append(parsed)
        # 结果返回：把`max(dates) if dates else None`交给调用方并结束当前函数。
        # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return max(dates) if dates else None

    # 函数_freshness：执行_freshness逻辑。
    # - 参数result：类型StandardQueryResult；进入函数后按合同参与校验、筛选、计算或路由。
    # - 参数ctx：类型EvidenceBuildContext；进入函数后按合同参与校验、筛选、计算或路由。
    # - 输出：返回类型ReadinessEvidence；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
    # - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
    # - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
    def _freshness(self, result: StandardQueryResult, ctx: EvidenceBuildContext) -> ReadinessEvidence:
        # 变量更新：计算并保存latest，右侧逻辑为`ctx.latest_available_date or self._latest_record_date(result.records)`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        latest = ctx.latest_available_date or self._latest_record_date(result.records)
        # 变量更新：计算并保存expected，右侧逻辑为`ctx.expected_through_date or result.query.end_date`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        expected = ctx.expected_through_date or result.query.end_date
        # 变量更新：计算并保存limit，右侧逻辑为`ctx.max_freshness_lag_days`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        limit = ctx.max_freshness_lag_days
        # 条件门禁：判断`limit is None`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        # 变量更新：计算并保存limit，右侧逻辑为`self.rules.default_max_freshness_lag_days`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        if limit is None: limit = self.rules.default_max_freshness_lag_days
        # 字段或变量metrics：声明类型dict[str, Any]，初始逻辑为`{'latest_available_date': latest, 'expected_through_date': expected, 'max_freshness_lag_days': limi…`。
        # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
        # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
        metrics: dict[str, Any] = {'latest_available_date': latest, 'expected_through_date': expected, 'max_freshness_lag_days': limit, 'scope_proven': ctx.freshness_scope_proven}
        # 条件门禁：判断`latest is None`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if latest is None:
            # 变量更新：计算并保存status, code, message，右侧逻辑为`(EvidenceStatus.UNKNOWN, 'FRESHNESS_DATE_MISSING', '无法从结果或补充上下文确认最新可用日期。')`。
            # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
            # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
            status, code, message = EvidenceStatus.UNKNOWN, 'FRESHNESS_DATE_MISSING', '无法从结果或补充上下文确认最新可用日期。'
        # 条件门禁：判断`latest > expected`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        elif latest > expected:
            # 变量更新：计算并保存status, code, message，右侧逻辑为`(EvidenceStatus.WARNING, 'FUTURE_DATED_OBSERVATION', '最新观测日期晚于期望截止日期，需要检查时点边界。')`。
            # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
            # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
            status, code, message = EvidenceStatus.WARNING, 'FUTURE_DATED_OBSERVATION', '最新观测日期晚于期望截止日期，需要检查时点边界。'
            # 变量更新：计算并保存metrics['lag_days']，右侧逻辑为`(expected - latest).days`。
            # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
            # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
            metrics['lag_days'] = (expected - latest).days
        else:
            # 变量更新：计算并保存lag，右侧逻辑为`(expected - latest).days`。
            # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
            # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
            lag = (expected - latest).days
            # 变量更新：计算并保存metrics['lag_days']，右侧逻辑为`lag`。
            # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
            # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
            metrics['lag_days'] = lag
            # 条件门禁：判断`lag > limit`，条件为真时进入受保护分支。
            # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
            # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
            # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
            if lag > limit:
                # 变量更新：计算并保存status，右侧逻辑为`EvidenceStatus.FAILED if ctx.stale_is_failure else EvidenceStatus.WARNING`。
                # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
                # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
                status = EvidenceStatus.FAILED if ctx.stale_is_failure else EvidenceStatus.WARNING
                # 变量更新：计算并保存code, message，右侧逻辑为`('FRESHNESS_STALE', '最新观测日期落后于允许阈值。')`。
                # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
                # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
                code, message = 'FRESHNESS_STALE', '最新观测日期落后于允许阈值。'
            # 条件门禁：判断`ctx.freshness_scope_proven or not self.rules.freshness_scope_requires_external_evidence`，条件为真时进入受保护分支。
            # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
            # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
            # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
            elif ctx.freshness_scope_proven or not self.rules.freshness_scope_requires_external_evidence:
                # 变量更新：计算并保存status, code, message，右侧逻辑为`(EvidenceStatus.PASSED, 'FRESHNESS_PROVEN', '外部时效证据证明数据达到期望截止日期。')`。
                # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
                # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
                status, code, message = EvidenceStatus.PASSED, 'FRESHNESS_PROVEN', '外部时效证据证明数据达到期望截止日期。'
            else:
                # 变量更新：计算并保存status, code, message，右侧逻辑为`(EvidenceStatus.WARNING, 'QUERY_SCOPE_FRESHNESS_ONLY', '当前只能证明本次结果日期，尚不能证明数据集级最新状态。')`。
                # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
                # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
                status, code, message = EvidenceStatus.WARNING, 'QUERY_SCOPE_FRESHNESS_ONLY', '当前只能证明本次结果日期，尚不能证明数据集级最新状态。'
        # 结果返回：把`ReadinessEvidence(ReadinessDimension.FRESHNESS, status, code, message, metrics, self._refs(result, …`交给调用方并结束当前函数。
        # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return ReadinessEvidence(ReadinessDimension.FRESHNESS, status, code, message, metrics, self._refs(result, ctx))

    # 函数_lineage：执行_lineage逻辑。
    # - 参数result：类型StandardQueryResult；进入函数后按合同参与校验、筛选、计算或路由。
    # - 参数ctx：类型EvidenceBuildContext；进入函数后按合同参与校验、筛选、计算或路由。
    # - 输出：返回类型ReadinessEvidence；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
    # - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
    # - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
    def _lineage(self, result: StandardQueryResult, ctx: EvidenceBuildContext) -> ReadinessEvidence:
        # 变量更新：计算并保存total，右侧逻辑为`len(result.records)`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        total = len(result.records)
        # 变量更新：计算并保存source_ids，右侧逻辑为`sum((bool(r.source_record_id) for r in result.records))`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        source_ids = sum(bool(r.source_record_id) for r in result.records)
        # 变量更新：计算并保存records_with_lineage，右侧逻辑为`sum((bool(r.lineage) for r in result.records))`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        records_with_lineage = sum(bool(r.lineage) for r in result.records)
        # 变量更新：计算并保存calculated_items，右侧逻辑为`sum((len(r.lineage) for r in result.records))`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        calculated_items = sum(len(r.lineage) for r in result.records)
        # 变量更新：计算并保存metrics，右侧逻辑为`{'record_count': total, 'source_record_id_count': source_ids, 'records_with_lineage': records_with_…`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        metrics = {'record_count': total, 'source_record_id_count': source_ids, 'records_with_lineage': records_with_lineage, 'metadata_lineage_item_count': result.metadata.lineage_item_count, 'calculated_lineage_item_count': calculated_items}
        # 条件门禁：判断`total == 0 or source_ids == 0 or calculated_items == 0`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if total == 0 or source_ids == 0 or calculated_items == 0:
            # 变量更新：计算并保存status, code, message，右侧逻辑为`(EvidenceStatus.FAILED, 'LINEAGE_MISSING', '结果缺少来源记录标识或字段血缘。')`。
            # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
            # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
            status, code, message = EvidenceStatus.FAILED, 'LINEAGE_MISSING', '结果缺少来源记录标识或字段血缘。'
        # 条件门禁：判断`source_ids < total or records_with_lineage < total or calculated_items != result.metadata.lineage_i…`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        elif source_ids < total or records_with_lineage < total or calculated_items != result.metadata.lineage_item_count:
            # 变量更新：计算并保存status, code, message，右侧逻辑为`(EvidenceStatus.WARNING, 'LINEAGE_PARTIAL', '部分记录血缘缺失或元数据计数不一致。')`。
            # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
            # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
            status, code, message = EvidenceStatus.WARNING, 'LINEAGE_PARTIAL', '部分记录血缘缺失或元数据计数不一致。'
        else:
            # 变量更新：计算并保存status, code, message，右侧逻辑为`(EvidenceStatus.PASSED, 'LINEAGE_COMPLETE', '所有标准记录均包含来源标识和字段血缘。')`。
            # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
            # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
            status, code, message = EvidenceStatus.PASSED, 'LINEAGE_COMPLETE', '所有标准记录均包含来源标识和字段血缘。'
        # 结果返回：把`ReadinessEvidence(ReadinessDimension.LINEAGE, status, code, message, metrics, self._refs(result, ct…`交给调用方并结束当前函数。
        # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return ReadinessEvidence(ReadinessDimension.LINEAGE, status, code, message, metrics, self._refs(result, ctx, *(f'source:{r.source_record_id}' for r in result.records if r.source_record_id)))

    # 函数_temporal_markers：执行_temporal_markers逻辑。
    # - 参数result：类型StandardQueryResult；进入函数后按合同参与校验、筛选、计算或路由。
    # - 输出：返回类型list[str]；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
    # - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
    # - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
    def _temporal_markers(self, result: StandardQueryResult) -> list[str]:
        # 变量更新：计算并保存texts，右侧逻辑为`list(result.metadata.warnings)`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        texts = list(result.metadata.warnings)
        # 迭代处理：依次从`result.records`读取元素，并绑定到`record`。
        # - 维度变化：每轮处理一个记录、字段、证据或配置项，可能向列表、字典或累计统计增加一项。
        # - 为什么这样写：显式逐项处理便于保留顺序、定位坏数据，并对每个实体执行同一合同。
        # API或函数调用：执行`texts.extend`，完整调用片段为`texts.extend(record.quality_flags)`。
        # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
        # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
        # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
        for record in result.records: texts.extend(record.quality_flags)
        # 字段或变量markers：声明类型list[str]，初始逻辑为`[]`。
        # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
        # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
        markers: list[str] = []
        # 迭代处理：依次从`texts`读取元素，并绑定到`text`。
        # - 维度变化：每轮处理一个记录、字段、证据或配置项，可能向列表、字典或累计统计增加一项。
        # - 为什么这样写：显式逐项处理便于保留顺序、定位坏数据，并对每个实体执行同一合同。
        for text in texts:
            # 变量更新：计算并保存upper，右侧逻辑为`text.upper()`。
            # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
            # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
            upper = text.upper()
            # 条件门禁：判断`any((marker in upper for marker in self.rules.temporal_warning_markers))`，条件为真时进入受保护分支。
            # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
            # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
            # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
            if any(marker in upper for marker in self.rules.temporal_warning_markers):
                # API或函数调用：执行`markers.append`，完整调用片段为`markers.append(text)`。
                # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
                # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
                # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
                markers.append(text)
        # 结果返回：把`list(dict.fromkeys(markers))`交给调用方并结束当前函数。
        # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return list(dict.fromkeys(markers))

    # 函数_explicit：执行_explicit逻辑。
    # - 参数dimension：类型ReadinessDimension；进入函数后按合同参与校验、筛选、计算或路由。
    # - 参数status：类型EvidenceStatus | None；进入函数后按合同参与校验、筛选、计算或路由。
    # - 参数code：类型str | None；进入函数后按合同参与校验、筛选、计算或路由。
    # - 参数message：类型str | None；进入函数后按合同参与校验、筛选、计算或路由。
    # - 参数result：类型StandardQueryResult；进入函数后按合同参与校验、筛选、计算或路由。
    # - 参数ctx：类型EvidenceBuildContext；进入函数后按合同参与校验、筛选、计算或路由。
    # - 输出：返回类型ReadinessEvidence | None；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
    # - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
    # - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
    def _explicit(self, dimension: ReadinessDimension, status: EvidenceStatus | None, code: str | None, message: str | None, result: StandardQueryResult, ctx: EvidenceBuildContext) -> ReadinessEvidence | None:
        # 条件门禁：判断`status is None`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        # 结果返回：把`None`交给调用方并结束当前函数。
        # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        if status is None: return None
        # 结果返回：把`ReadinessEvidence(dimension, status, code or f'{dimension.value}_EXPLICIT', message or '使用显式补充证据。',…`交给调用方并结束当前函数。
        # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return ReadinessEvidence(dimension, status, code or f'{dimension.value}_EXPLICIT', message or '使用显式补充证据。', {}, self._refs(result, ctx))

    # 函数_temporal：执行_temporal逻辑。
    # - 参数result：类型StandardQueryResult；进入函数后按合同参与校验、筛选、计算或路由。
    # - 参数ctx：类型EvidenceBuildContext；进入函数后按合同参与校验、筛选、计算或路由。
    # - 输出：返回类型ReadinessEvidence；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
    # - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
    # - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
    def _temporal(self, result: StandardQueryResult, ctx: EvidenceBuildContext) -> ReadinessEvidence:
        # 变量更新：计算并保存explicit，右侧逻辑为`self._explicit(ReadinessDimension.TEMPORAL_SAFETY, ctx.temporal_status, ctx.temporal_code, ctx.temp…`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        explicit = self._explicit(ReadinessDimension.TEMPORAL_SAFETY, ctx.temporal_status, ctx.temporal_code, ctx.temporal_message, result, ctx)
        # 条件门禁：判断`explicit`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        # 结果返回：把`explicit`交给调用方并结束当前函数。
        # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        if explicit: return explicit
        # 变量更新：计算并保存markers，右侧逻辑为`self._temporal_markers(result)`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        markers = self._temporal_markers(result)
        # 变量更新：计算并保存metrics，右侧逻辑为`{'as_of_date': result.query.as_of_date, 'decision_time': result.query.decision_time, 'temporal_mark…`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        metrics = {'as_of_date': result.query.as_of_date, 'decision_time': result.query.decision_time, 'temporal_markers': markers}
        # 条件门禁：判断`result.metadata.blocks_downstream`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if result.metadata.blocks_downstream:
            # 变量更新：计算并保存status, code, message，右侧逻辑为`(EvidenceStatus.FAILED, 'PROVIDER_TEMPORAL_GATE_BLOCKED', 'Provider已阻断当前用途或时点。')`。
            # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
            # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
            status, code, message = EvidenceStatus.FAILED, 'PROVIDER_TEMPORAL_GATE_BLOCKED', 'Provider已阻断当前用途或时点。'
        # 条件门禁：判断`markers`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        elif markers:
            # 变量更新：计算并保存status, code, message，右侧逻辑为`(EvidenceStatus.WARNING, 'TEMPORAL_WARNING_PRESENT', '结果包含无法证明精确可见时间的警告。')`。
            # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
            # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
            status, code, message = EvidenceStatus.WARNING, 'TEMPORAL_WARNING_PRESENT', '结果包含无法证明精确可见时间的警告。'
        # 条件门禁：判断`result.query.as_of_date is not None`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        elif result.query.as_of_date is not None:
            # 变量更新：计算并保存status, code, message，右侧逻辑为`(EvidenceStatus.PASSED, 'AS_OF_BOUNDARY_ENFORCED', '查询显式携带并通过as_of_date边界。')`。
            # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
            # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
            status, code, message = EvidenceStatus.PASSED, 'AS_OF_BOUNDARY_ENFORCED', '查询显式携带并通过as_of_date边界。'
        else:
            # 变量更新：计算并保存status, code, message，右侧逻辑为`(EvidenceStatus.UNKNOWN, 'TEMPORAL_EVIDENCE_MISSING', '查询未提供足够的时点安全证据。')`。
            # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
            # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
            status, code, message = EvidenceStatus.UNKNOWN, 'TEMPORAL_EVIDENCE_MISSING', '查询未提供足够的时点安全证据。'
        # 结果返回：把`ReadinessEvidence(ReadinessDimension.TEMPORAL_SAFETY, status, code, message, metrics, self._refs(re…`交给调用方并结束当前函数。
        # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return ReadinessEvidence(ReadinessDimension.TEMPORAL_SAFETY, status, code, message, metrics, self._refs(result, ctx))

    # 函数_semantic：执行_semantic逻辑。
    # - 参数result：类型StandardQueryResult；进入函数后按合同参与校验、筛选、计算或路由。
    # - 参数ctx：类型EvidenceBuildContext；进入函数后按合同参与校验、筛选、计算或路由。
    # - 输出：返回类型ReadinessEvidence；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
    # - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
    # - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
    def _semantic(self, result: StandardQueryResult, ctx: EvidenceBuildContext) -> ReadinessEvidence:
        # 变量更新：计算并保存explicit，右侧逻辑为`self._explicit(ReadinessDimension.SEMANTIC_CONFIDENCE, ctx.semantic_status, ctx.semantic_code, ctx.…`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        explicit = self._explicit(ReadinessDimension.SEMANTIC_CONFIDENCE, ctx.semantic_status, ctx.semantic_code, ctx.semantic_message, result, ctx)
        # 条件门禁：判断`explicit`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        # 结果返回：把`explicit`交给调用方并结束当前函数。
        # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        if explicit: return explicit
        # 字段或变量flags：声明类型list[str]，初始逻辑为`[]`。
        # - 数据变化：类型注解不改变运行值；存在默认表达式时才在构造或执行阶段生成初始值。
        # - 为什么这样写：显式类型帮助IDE、测试和审计器理解数据形状，并降低不同Provider之间的隐式类型转换。
        flags: list[str] = []
        # 迭代处理：依次从`result.records`读取元素，并绑定到`record`。
        # - 维度变化：每轮处理一个记录、字段、证据或配置项，可能向列表、字典或累计统计增加一项。
        # - 为什么这样写：显式逐项处理便于保留顺序、定位坏数据，并对每个实体执行同一合同。
        # API或函数调用：执行`flags.extend`，完整调用片段为`flags.extend(record.quality_flags)`。
        # - 参数逻辑：位置参数按声明顺序绑定，关键字参数按名称绑定；返回值若未赋值，通常依赖显式副作用或校验异常。
        # - 数据变化：可能更新受控对象、写入报告文件、注册Provider或执行纯校验；具体边界由被调用合同限定。
        # - 为什么这样写：直接调用已有稳定接口符合复用优先原则，并把复杂细节隔离在单一实现中。
        for record in result.records: flags.extend(record.quality_flags)
        # 变量更新：计算并保存flags，右侧逻辑为`list(dict.fromkeys(flags))`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        flags = list(dict.fromkeys(flags))
        # 变量更新：计算并保存warnings，右侧逻辑为`list(result.metadata.warnings)`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        warnings = list(result.metadata.warnings)
        # 变量更新：计算并保存metrics，右侧逻辑为`{'quality_flags': flags, 'warnings': warnings, 'quality_status': result.metadata.status.value}`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        metrics = {'quality_flags': flags, 'warnings': warnings, 'quality_status': result.metadata.status.value}
        # 条件门禁：判断`result.metadata.status is QualityStatus.FAILED`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if result.metadata.status is QualityStatus.FAILED:
            # 变量更新：计算并保存status, code, message，右侧逻辑为`(EvidenceStatus.FAILED, 'SEMANTIC_PROVIDER_FAILED', 'Provider报告语义或质量失败。')`。
            # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
            # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
            status, code, message = EvidenceStatus.FAILED, 'SEMANTIC_PROVIDER_FAILED', 'Provider报告语义或质量失败。'
        # 条件门禁：判断`flags or warnings or result.metadata.status in {QualityStatus.WARNING, QualityStatus.PENDING_CONFIR…`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        elif flags or warnings or result.metadata.status in {QualityStatus.WARNING, QualityStatus.PENDING_CONFIRMATION}:
            # 变量更新：计算并保存status, code, message，右侧逻辑为`(EvidenceStatus.WARNING, 'SEMANTIC_WARNINGS_PRESENT', '标准结果仍包含来源语义或质量警告。')`。
            # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
            # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
            status, code, message = EvidenceStatus.WARNING, 'SEMANTIC_WARNINGS_PRESENT', '标准结果仍包含来源语义或质量警告。'
        else:
            # 变量更新：计算并保存status, code, message，右侧逻辑为`(EvidenceStatus.PASSED, 'SEMANTIC_CHECKS_PASSED', 'Provider未报告语义警告。')`。
            # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
            # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
            status, code, message = EvidenceStatus.PASSED, 'SEMANTIC_CHECKS_PASSED', 'Provider未报告语义警告。'
        # 结果返回：把`ReadinessEvidence(ReadinessDimension.SEMANTIC_CONFIDENCE, status, code, message, metrics, self._ref…`交给调用方并结束当前函数。
        # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return ReadinessEvidence(ReadinessDimension.SEMANTIC_CONFIDENCE, status, code, message, metrics, self._refs(result, ctx))

    # 函数_activation：执行_activation逻辑。
    # - 参数result：类型StandardQueryResult；进入函数后按合同参与校验、筛选、计算或路由。
    # - 参数descriptor：类型ProviderDescriptor；进入函数后按合同参与校验、筛选、计算或路由。
    # - 参数ctx：类型EvidenceBuildContext；进入函数后按合同参与校验、筛选、计算或路由。
    # - 输出：返回类型ReadinessEvidence；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
    # - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
    # - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
    def _activation(self, result: StandardQueryResult, descriptor: ProviderDescriptor, ctx: EvidenceBuildContext) -> ReadinessEvidence:
        # 变量更新：计算并保存explicit，右侧逻辑为`self._explicit(ReadinessDimension.ACTIVATION, ctx.activation_status, ctx.activation_code, ctx.activ…`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        explicit = self._explicit(ReadinessDimension.ACTIVATION, ctx.activation_status, ctx.activation_code, ctx.activation_message, result, ctx)
        # 条件门禁：判断`explicit`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        # 结果返回：把`explicit`交给调用方并结束当前函数。
        # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        if explicit: return explicit
        # 变量更新：计算并保存matched，右侧逻辑为`descriptor.provider_id == result.metadata.provider_id and descriptor.dataset_id == result.metadata.…`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        matched = descriptor.provider_id == result.metadata.provider_id and descriptor.dataset_id == result.metadata.dataset_id
        # 变量更新：计算并保存metrics，右侧逻辑为`{'provider_registered': matched, 'activation_verified': ctx.activation_verified}`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        metrics = {'provider_registered': matched, 'activation_verified': ctx.activation_verified}
        # 条件门禁：判断`not matched`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        if not matched:
            # 变量更新：计算并保存status, code, message，右侧逻辑为`(EvidenceStatus.FAILED, 'PROVIDER_REGISTRATION_MISMATCH', '查询结果与Provider登记不一致。')`。
            # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
            # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
            status, code, message = EvidenceStatus.FAILED, 'PROVIDER_REGISTRATION_MISMATCH', '查询结果与Provider登记不一致。'
        # 条件门禁：判断`ctx.activation_verified or not self.rules.activation_requires_external_verification`，条件为真时进入受保护分支。
        # - 数据变化：条件表达式本身只产生布尔结果；只有分支体内的显式赋值、返回或异常会改变状态与控制流。
        # - 数值范围：涉及阈值、比例或日期时，边界由表达式中的比较符和相邻合同共同限定。
        # - 为什么这样写：把不合法、过期或不安全状态尽早分流，避免错误证据继续传播到下游研究或交易层。
        elif ctx.activation_verified or not self.rules.activation_requires_external_verification:
            # 变量更新：计算并保存status, code, message，右侧逻辑为`(EvidenceStatus.PASSED, 'DATASET_ACTIVATION_VERIFIED', '数据集和Provider启用状态已由外部配置确认。')`。
            # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
            # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
            status, code, message = EvidenceStatus.PASSED, 'DATASET_ACTIVATION_VERIFIED', '数据集和Provider启用状态已由外部配置确认。'
        else:
            # 变量更新：计算并保存status, code, message，右侧逻辑为`(EvidenceStatus.WARNING, 'PROVIDER_REGISTERED_ACTIVATION_UNVERIFIED', 'Provider已登记且可查询，但尚未由独立启用配置证明…`。
            # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
            # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
            status, code, message = EvidenceStatus.WARNING, 'PROVIDER_REGISTERED_ACTIVATION_UNVERIFIED', 'Provider已登记且可查询，但尚未由独立启用配置证明生产激活状态。'
        # 结果返回：把`ReadinessEvidence(ReadinessDimension.ACTIVATION, status, code, message, metrics, self._refs(result,…`交给调用方并结束当前函数。
        # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return ReadinessEvidence(ReadinessDimension.ACTIVATION, status, code, message, metrics, self._refs(result, ctx))


# 类StandardQueryReadinessService：组合证据适配器和DataReadinessEngine生成就绪度快照。
# - 继承边界：基类为object；类体包含约0个字段或常量、2个方法。
# - 数据变化：类定义本身不执行隐式I/O，实例只在构造、校验或显式方法调用时产生受控状态。
# - 实操示例：调用方先构造该类型，再由方法完成校验、证据组合、路由或结果导出。
# - 为什么这样写：强类型边界能把相关不变量集中管理，减少字典键拼写、状态漂移和跨模块耦合。
class StandardQueryReadinessService:
    """组合证据适配器和DataReadinessEngine生成就绪度快照。"""

    # 函数__init__：执行__init__逻辑。
    # - 参数engine：类型DataReadinessEngine；进入函数后按合同参与校验、筛选、计算或路由。
    # - 参数builder：类型StandardQueryEvidenceBuilder；进入函数后按合同参与校验、筛选、计算或路由。
    # - 输出：返回类型None；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
    # - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
    # - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
    def __init__(self, engine: DataReadinessEngine, builder: StandardQueryEvidenceBuilder) -> None:
        # 变量更新：计算并保存self.engine，右侧逻辑为`engine`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        self.engine = engine
        # 变量更新：计算并保存self.builder，右侧逻辑为`builder`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        self.builder = builder

    # 函数assess：执行assess逻辑。
    # - 参数result：类型StandardQueryResult；进入函数后按合同参与校验、筛选、计算或路由。
    # - 参数descriptor：类型ProviderDescriptor；进入函数后按合同参与校验、筛选、计算或路由。
    # - 参数context：类型EvidenceBuildContext | None，默认值None；进入函数后按合同参与校验、筛选、计算或路由。
    # - 输出：返回类型DatasetReadinessSnapshot；调用方据此继续构造证据、执行门禁、序列化或生成研究结果。
    # - 数据变化：只通过显式返回值、受控对象字段或明确依赖调用传递状态，不隐藏数据库写入或交易副作用。
    # - 为什么这样写：把该步骤封装为可测试函数，可复用同一合同并在失败时精确定位输入、证据或控制流问题。
    def assess(self, result: StandardQueryResult, descriptor: ProviderDescriptor, context: EvidenceBuildContext | None = None) -> DatasetReadinessSnapshot:
        # 变量更新：计算并保存evidence，右侧逻辑为`self.builder.build(result, descriptor, context)`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        evidence = self.builder.build(result, descriptor, context)
        # 变量更新：计算并保存request，右侧逻辑为`DataReadinessRequest(dataset_id=result.query.dataset_id, usage=result.query.usage, evidence=evidenc…`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        request = DataReadinessRequest(
            dataset_id=result.query.dataset_id,
            usage=result.query.usage,
            evidence=evidence,
            as_of_date=result.query.as_of_date,
            decision_time=result.query.decision_time,
        )
        # 变量更新：计算并保存decision，右侧逻辑为`self.engine.evaluate(request)`。
        # - 数据变化：赋值只更新当前作用域的目标变量、容器引用或对象字段；类型和数值范围由右侧表达式及后续校验决定。
        # - 为什么这样写：给中间结果命名可以避免重复计算，并让后续门禁、错误信息和审计记录引用同一事实。
        decision = self.engine.evaluate(request)
        # 结果返回：把`DatasetReadinessSnapshot(dataset_id=result.query.dataset_id, canonical_object=result.query.canonica…`交给调用方并结束当前函数。
        # - 数据变化：返回值可能是不可变合同对象、序列化字典、证据集合或布尔门禁；函数内局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return DatasetReadinessSnapshot(
            dataset_id=result.query.dataset_id,
            canonical_object=result.query.canonical_object,
            provider_id=descriptor.provider_id,
            query_id=result.metadata.query_id,
            usage=result.query.usage,
            adapter_version=EVIDENCE_ADAPTER_VERSION,
            rules_version=self.builder.rules.rules_version,
            evidence=evidence,
            decision=decision,
        )
