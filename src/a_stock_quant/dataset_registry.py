# 模块总览：通用数据集注册表与标准字段映射引擎。
# - 输入输出：本模块通过强类型对象和纯函数交换数据，不在导入阶段执行隐式网络或数据库写入。
# - 数据变化：只有显式构造、校验、加载或方法调用才会产生新对象或更新受控状态。
# - 为什么这样写：先说明模块边界，读者可以在阅读实现前理解职责、风险和复用方式。
"""通用数据集注册表与标准字段映射引擎。

目标：
1. 数据源表不直接决定系统核心结构；
2. 每个来源数据集必须显式登记；
3. 每个来源字段必须被映射、待确认或明确保留；
4. 映射规则可以随新数据集持续扩展；
5. 映射执行同时输出质量提示、来源扩展和字段血缘。

本模块不负责连接 DolphinDB，也不写入数据库。
"""

# 依赖导入：加载标准库、类型工具和项目内合同，供下方数据结构与校验逻辑复用。
# - 标准库只提供解析、数学、时间、路径和类型能力；项目模块提供统一异常与上游合同。
# - 为什么这样写：集中导入让依赖边界清晰，并避免在函数内部重复加载同一模块。
from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

from .data_contracts import (
    DataContractError,
    MappingStatus,
    SourceType,
)


# 变量更新：计算并保存TransformFunction，右侧逻辑为`Callable[[list[Any], Mapping[str, Any], Mapping[str, Any], Mapping[str, Any]], Any]`。
# - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
# - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
TransformFunction = Callable[
    [
        list[Any],
        Mapping[str, Any],
        Mapping[str, Any],
        Mapping[str, Any],
    ],
    Any,
]


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


# 执行_require_unique逻辑，把输入参数转换为受合同约束的结果。
# - 参数values：类型Sequence[str]；进入函数后按合同校验或参与计算。
# - 参数field_name：类型str；进入函数后按合同校验或参与计算。
# - 输出：返回类型tuple[str, ...]；调用方按该类型继续校验、路由或序列化。
# - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
def _require_unique(
    values: Sequence[str],
    field_name: str,
) -> tuple[str, ...]:
    # 变量更新：计算并保存normalized，右侧逻辑为`tuple((_require_text(value, field_name) for value in values))`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    normalized = tuple(
        _require_text(value, field_name)
        for value in values
    )

    # 变量更新：计算并保存duplicates，右侧逻辑为`[value for value, count in Counter(normalized).items() if count > 1]`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 固定数值：本表达式包含1；来源是当前项目既有合同或算法定义，迁移注释不改变其数值。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    duplicates = [
        value
        for value, count in Counter(normalized).items()
        if count > 1
    ]

    # 条件门禁：判断`duplicates`，条件为真时进入受保护分支。
    # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
    # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
    if duplicates:
        # 错误阻断：抛出`DataContractError(f'{field_name} 存在重复值：{duplicates}')`并停止当前路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
        # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
        raise DataContractError(
            f"{field_name} 存在重复值：{duplicates}"
        )

    # 结果返回：把`normalized`交给调用方。
    # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
    # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
    return normalized


# 一个来源字段到标准字段的映射规则。
# - 字段source_fields：类型tuple[str, ...]。
# - 字段status：类型MappingStatus。
# - 字段transform_id：类型str，默认值'identity'。
# - 字段target_object：类型str | None，默认值None。
# - 字段canonical_field：类型str | None，默认值None。
# - 字段transform_params：类型dict[str, Any]，默认值field(default_factory=dict)。
# - 字段required：类型bool，默认值False。
# - 字段source_unit：类型str | None，默认值None。
# - 其余字段：另有2项，均在对象创建时统一校验。
# - 数据变化：类本身不执行隐式I/O，实例字段只在显式构造、校验或方法调用时变化。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
@dataclass(frozen=True, slots=True)
class FieldMappingRule:
    """一个来源字段到标准字段的映射规则。"""

    # 变量更新：计算并保存source_fields，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    source_fields: tuple[str, ...]
    # 变量更新：计算并保存status，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    status: MappingStatus
    # 变量更新：计算并保存transform_id，右侧逻辑为`'identity'`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    transform_id: str = "identity"
    # 变量更新：计算并保存target_object，右侧逻辑为`None`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    target_object: str | None = None
    # 变量更新：计算并保存canonical_field，右侧逻辑为`None`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    canonical_field: str | None = None
    # 变量更新：计算并保存transform_params，右侧逻辑为`field(default_factory=dict)`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    transform_params: dict[str, Any] = field(default_factory=dict)
    # 变量更新：计算并保存required，右侧逻辑为`False`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    required: bool = False
    # 变量更新：计算并保存source_unit，右侧逻辑为`None`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    source_unit: str | None = None
    # 变量更新：计算并保存canonical_unit，右侧逻辑为`None`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    canonical_unit: str | None = None
    # 变量更新：计算并保存notes，右侧逻辑为`None`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    notes: str | None = None

    # 执行__post_init__逻辑，把输入参数转换为受合同约束的结果。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态或模块常量。
    # - 输出：返回类型None；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：在不可变或数据类对象创建后立即校验字段关系，阻止不一致对象进入系统。
    def __post_init__(self) -> None:
        # 变量更新：计算并保存source_fields，右侧逻辑为`_require_unique(self.source_fields, 'source_fields')`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        source_fields = _require_unique(
            self.source_fields,
            "source_fields",
        )
        # API调用：执行`object.__setattr__(self, 'source_fields', source_fields)`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        object.__setattr__(self, "source_fields", source_fields)
        # API调用：执行`object.__setattr__(self, 'transform_id', _require_text(self.transform_id, 'transform_id'))`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        object.__setattr__(
            self,
            "transform_id",
            _require_text(self.transform_id, "transform_id"),
        )

        # 条件门禁：判断`self.status in {MappingStatus.MAPPED, MappingStatus.WARNING}`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if self.status in {
            MappingStatus.MAPPED,
            MappingStatus.WARNING,
        }:
            # 条件门禁：判断`self.target_object is None`，条件为真时进入受保护分支。
            # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
            # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
            if self.target_object is None:
                # 错误阻断：抛出`DataContractError('已映射规则必须提供 target_object。')`并停止当前路径。
                # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
                # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
                raise DataContractError(
                    "已映射规则必须提供 target_object。"
                )
            # 条件门禁：判断`self.canonical_field is None`，条件为真时进入受保护分支。
            # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
            # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
            if self.canonical_field is None:
                # 错误阻断：抛出`DataContractError('已映射规则必须提供 canonical_field。')`并停止当前路径。
                # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
                # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
                raise DataContractError(
                    "已映射规则必须提供 canonical_field。"
                )

        # 条件门禁：判断`self.target_object is not None`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if self.target_object is not None:
            # API调用：执行`object.__setattr__(self, 'target_object', _require_text(self.target_object, 'target_object'))`以触发注册、写入对象状态或其他显式副作用。
            # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
            # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
            object.__setattr__(
                self,
                "target_object",
                _require_text(
                    self.target_object,
                    "target_object",
                ),
            )

        # 条件门禁：判断`self.canonical_field is not None`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if self.canonical_field is not None:
            # API调用：执行`object.__setattr__(self, 'canonical_field', _require_text(self.canonical_field, 'canonical_field'))`以触发注册、写入对象状态或其他显式副作用。
            # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
            # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
            object.__setattr__(
                self,
                "canonical_field",
                _require_text(
                    self.canonical_field,
                    "canonical_field",
                ),
            )

    # 执行canonical_target逻辑，把输入参数转换为受合同约束的结果。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态或模块常量。
    # - 输出：返回类型str | None；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
    @property
    def canonical_target(self) -> str | None:
        # 条件门禁：判断`self.target_object is None or self.canonical_field is None`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if (
            self.target_object is None
            or self.canonical_field is None
        ):
            # 结果返回：把`None`交给调用方。
            # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
            # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
            return None

        # 结果返回：把`f'{self.target_object}.{self.canonical_field}'`交给调用方。
        # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
        # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
        return (
            f"{self.target_object}.{self.canonical_field}"
        )

    # 执行to_dict逻辑，把输入参数转换为受合同约束的结果。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态或模块常量。
    # - 输出：返回类型dict[str, Any]；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：把强类型对象转换为JSON安全字典，便于报告、审计和持久化。
    def to_dict(self) -> dict[str, Any]:
        # 变量更新：计算并保存result，右侧逻辑为`asdict(self)`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        result = asdict(self)
        # 变量更新：计算并保存result['status']，右侧逻辑为`self.status.value`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        result["status"] = self.status.value
        # 变量更新：计算并保存result['source_fields']，右侧逻辑为`list(self.source_fields)`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        result["source_fields"] = list(self.source_fields)
        # 结果返回：把`result`交给调用方。
        # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
        # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
        return result

    # 执行from_dict逻辑，把输入参数转换为受合同约束的结果。
    # - 参数value：类型Mapping[str, Any]；进入函数后按合同校验或参与计算。
    # - 输出：返回类型'FieldMappingRule'；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：从普通字典恢复强类型对象，集中处理枚举、默认值和兼容性。
    @classmethod
    def from_dict(
        cls,
        value: Mapping[str, Any],
    ) -> "FieldMappingRule":
        # 结果返回：把`cls(source_fields=tuple(value['source_fields']), status=MappingStatus(value['status']), transform...`交给调用方。
        # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
        # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
        return cls(
            source_fields=tuple(value["source_fields"]),
            status=MappingStatus(value["status"]),
            transform_id=value.get("transform_id", "identity"),
            target_object=value.get("target_object"),
            canonical_field=value.get("canonical_field"),
            transform_params=dict(
                value.get("transform_params", {})
            ),
            required=bool(value.get("required", False)),
            source_unit=value.get("source_unit"),
            canonical_unit=value.get("canonical_unit"),
            notes=value.get("notes"),
        )


# 一个来源数据集的注册信息和映射合同。
# - 字段dataset_id：类型str。
# - 字段source_type：类型SourceType。
# - 字段source_locator：类型dict[str, Any]。
# - 字段dataset_mode：类型str。
# - 字段coverage_version：类型str。
# - 字段schema_version：类型str。
# - 字段mapping_version：类型str。
# - 字段dictionary_revision：类型str。
# - 其余字段：另有9项，均在对象创建时统一校验。
# - 数据变化：类本身不执行隐式I/O，实例字段只在显式构造、校验或方法调用时变化。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
@dataclass(frozen=True, slots=True)
class DatasetRegistration:
    """一个来源数据集的注册信息和映射合同。"""

    # 变量更新：计算并保存dataset_id，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    dataset_id: str
    # 变量更新：计算并保存source_type，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    source_type: SourceType
    # 变量更新：计算并保存source_locator，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    source_locator: dict[str, Any]
    # 变量更新：计算并保存dataset_mode，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    dataset_mode: str
    # 变量更新：计算并保存coverage_version，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    coverage_version: str
    # 变量更新：计算并保存schema_version，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    schema_version: str
    # 变量更新：计算并保存mapping_version，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    mapping_version: str
    # 变量更新：计算并保存dictionary_revision，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    dictionary_revision: str
    # 变量更新：计算并保存date_field，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    date_field: str | None
    # 变量更新：计算并保存entity_field，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    entity_field: str | None
    # 变量更新：计算并保存primary_key_fields，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    primary_key_fields: tuple[str, ...]
    # 变量更新：计算并保存source_fields，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    source_fields: tuple[str, ...]
    # 变量更新：计算并保存canonical_objects，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    canonical_objects: tuple[str, ...]
    # 变量更新：计算并保存field_mappings，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    field_mappings: tuple[FieldMappingRule, ...]
    # 变量更新：计算并保存enabled，右侧逻辑为`True`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    enabled: bool = True
    # 变量更新：计算并保存tags，右侧逻辑为`()`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    tags: tuple[str, ...] = ()
    # 变量更新：计算并保存description，右侧逻辑为`None`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    description: str | None = None

    # 执行__post_init__逻辑，把输入参数转换为受合同约束的结果。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态或模块常量。
    # - 输出：返回类型None；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：在不可变或数据类对象创建后立即校验字段关系，阻止不一致对象进入系统。
    def __post_init__(self) -> None:
        # API调用：执行`object.__setattr__(self, 'dataset_id', _require_text(self.dataset_id, 'dataset_id'))`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        object.__setattr__(
            self,
            "dataset_id",
            _require_text(self.dataset_id, "dataset_id"),
        )
        # API调用：执行`object.__setattr__(self, 'dataset_mode', _require_text(self.dataset_mode, 'dataset_mode'))`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        object.__setattr__(
            self,
            "dataset_mode",
            _require_text(
                self.dataset_mode,
                "dataset_mode",
            ),
        )
        # API调用：执行`object.__setattr__(self, 'coverage_version', _require_text(self.coverage_version, 'coverage_versi...`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        object.__setattr__(
            self,
            "coverage_version",
            _require_text(
                self.coverage_version,
                "coverage_version",
            ),
        )
        # API调用：执行`object.__setattr__(self, 'schema_version', _require_text(self.schema_version, 'schema_version'))`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        object.__setattr__(
            self,
            "schema_version",
            _require_text(
                self.schema_version,
                "schema_version",
            ),
        )
        # API调用：执行`object.__setattr__(self, 'mapping_version', _require_text(self.mapping_version, 'mapping_version'))`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        object.__setattr__(
            self,
            "mapping_version",
            _require_text(
                self.mapping_version,
                "mapping_version",
            ),
        )
        # API调用：执行`object.__setattr__(self, 'dictionary_revision', _require_text(self.dictionary_revision, 'dictiona...`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        object.__setattr__(
            self,
            "dictionary_revision",
            _require_text(
                self.dictionary_revision,
                "dictionary_revision",
            ),
        )

        # 变量更新：计算并保存source_fields，右侧逻辑为`_require_unique(self.source_fields, 'source_fields')`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        source_fields = _require_unique(
            self.source_fields,
            "source_fields",
        )
        # 变量更新：计算并保存primary_keys，右侧逻辑为`_require_unique(self.primary_key_fields, 'primary_key_fields')`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        primary_keys = _require_unique(
            self.primary_key_fields,
            "primary_key_fields",
        )
        # 变量更新：计算并保存canonical_objects，右侧逻辑为`_require_unique(self.canonical_objects, 'canonical_objects')`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        canonical_objects = _require_unique(
            self.canonical_objects,
            "canonical_objects",
        )
        # 变量更新：计算并保存tags，右侧逻辑为`_require_unique(self.tags, 'tags')`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        tags = _require_unique(self.tags, "tags")

        # API调用：执行`object.__setattr__(self, 'source_fields', source_fields)`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        object.__setattr__(self, "source_fields", source_fields)
        # API调用：执行`object.__setattr__(self, 'primary_key_fields', primary_keys)`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        object.__setattr__(
            self,
            "primary_key_fields",
            primary_keys,
        )
        # API调用：执行`object.__setattr__(self, 'canonical_objects', canonical_objects)`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        object.__setattr__(
            self,
            "canonical_objects",
            canonical_objects,
        )
        # API调用：执行`object.__setattr__(self, 'tags', tags)`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        object.__setattr__(self, "tags", tags)

        # 变量更新：计算并保存unknown_keys，右侧逻辑为`sorted(set(primary_keys) - set(source_fields))`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        unknown_keys = sorted(
            set(primary_keys) - set(source_fields)
        )
        # 条件门禁：判断`unknown_keys`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if unknown_keys:
            # 错误阻断：抛出`DataContractError(f'主键字段未出现在 source_fields 中：{unknown_keys}')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError(
                "主键字段未出现在 source_fields 中："
                f"{unknown_keys}"
            )

        # 变量更新：计算并保存mapping_sources，右侧逻辑为`{source_field for rule in self.field_mappings for source_field in rule.source_fields}`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        mapping_sources = {
            source_field
            for rule in self.field_mappings
            for source_field in rule.source_fields
        }
        # 变量更新：计算并保存unknown_mapping_sources，右侧逻辑为`sorted(mapping_sources - set(source_fields))`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        unknown_mapping_sources = sorted(
            mapping_sources - set(source_fields)
        )
        # 条件门禁：判断`unknown_mapping_sources`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if unknown_mapping_sources:
            # 错误阻断：抛出`DataContractError(f'映射规则引用了未知来源字段：{unknown_mapping_sources}')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError(
                "映射规则引用了未知来源字段："
                f"{unknown_mapping_sources}"
            )

        # 变量更新：计算并保存undeclared_objects，右侧逻辑为`sorted({rule.target_object for rule in self.field_mappings if rule.target_object is not...`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        undeclared_objects = sorted(
            {
                rule.target_object
                for rule in self.field_mappings
                if rule.target_object is not None
            }
            - set(canonical_objects)
        )
        # 条件门禁：判断`undeclared_objects`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if undeclared_objects:
            # 错误阻断：抛出`DataContractError(f'映射规则使用了未声明的标准对象：{undeclared_objects}')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError(
                "映射规则使用了未声明的标准对象："
                f"{undeclared_objects}"
            )

    # 统计全部来源字段是否被明确处理。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态或模块常量。
    # - 输出：返回类型dict[str, Any]；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
    def mapping_coverage(self) -> dict[str, Any]:
        """统计全部来源字段是否被明确处理。"""

        # 变量更新：计算并保存rules_by_source，右侧逻辑为`{field_name: [] for field_name in self.source_fields}`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        rules_by_source: dict[
            str,
            list[FieldMappingRule],
        ] = {
            field_name: []
            for field_name in self.source_fields
        }

        # 迭代处理：依次读取`self.field_mappings`中的元素，并绑定到`rule`。
        # - 维度变化：每轮处理一个元素，可能向列表、字典或累计值中增加一项。
        # - 为什么这样写：显式逐项校验可以精确指出哪个字段或Provider不符合合同。
        for rule in self.field_mappings:
            # 迭代处理：依次读取`rule.source_fields`中的元素，并绑定到`field_name`。
            # - 维度变化：每轮处理一个元素，可能向列表、字典或累计值中增加一项。
            # - 为什么这样写：显式逐项校验可以精确指出哪个字段或Provider不符合合同。
            for field_name in rule.source_fields:
                # API调用：执行`rules_by_source[field_name].append(rule)`以触发注册、写入对象状态或其他显式副作用。
                # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
                # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
                rules_by_source[field_name].append(rule)

        # 变量更新：计算并保存unaccounted_fields，右侧逻辑为`sorted((field_name for field_name, rules in rules_by_source.items() if not rules))`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        unaccounted_fields = sorted(
            field_name
            for field_name, rules in rules_by_source.items()
            if not rules
        )
        # 变量更新：计算并保存mapped_fields，右侧逻辑为`sorted((field_name for field_name, rules in rules_by_source.items() if any((rule.status...`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        mapped_fields = sorted(
            field_name
            for field_name, rules in rules_by_source.items()
            if any(
                rule.status in {
                    MappingStatus.MAPPED,
                    MappingStatus.WARNING,
                }
                and rule.canonical_target is not None
                for rule in rules
            )
        )
        # 变量更新：计算并保存pending_fields，右侧逻辑为`sorted((field_name for field_name, rules in rules_by_source.items() if rules and field_...`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        pending_fields = sorted(
            field_name
            for field_name, rules in rules_by_source.items()
            if rules
            and field_name not in mapped_fields
            and any(
                rule.status
                is MappingStatus.PENDING_CONFIRMATION
                for rule in rules
            )
        )
        # 变量更新：计算并保存unmapped_fields，右侧逻辑为`sorted((field_name for field_name, rules in rules_by_source.items() if rules and field_...`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        unmapped_fields = sorted(
            field_name
            for field_name, rules in rules_by_source.items()
            if rules
            and field_name not in mapped_fields
            and field_name not in pending_fields
        )

        # 结果返回：把`{'source_field_count': len(self.source_fields), 'mapped_source_field_count': len(mapped_fields), ...`交给调用方。
        # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
        # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
        return {
            "source_field_count": len(self.source_fields),
            "mapped_source_field_count": len(mapped_fields),
            "pending_source_field_count": len(pending_fields),
            "unmapped_source_field_count": len(unmapped_fields),
            "unaccounted_source_field_count": len(
                unaccounted_fields
            ),
            "mapped_fields": mapped_fields,
            "pending_fields": pending_fields,
            "unmapped_fields": unmapped_fields,
            "unaccounted_fields": unaccounted_fields,
            "all_source_fields_accounted":
                not unaccounted_fields,
            "canonical_target_count": len(
                {
                    rule.canonical_target
                    for rule in self.field_mappings
                    if rule.canonical_target is not None
                }
            ),
        }

    # 执行to_dict逻辑，把输入参数转换为受合同约束的结果。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态或模块常量。
    # - 输出：返回类型dict[str, Any]；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：把强类型对象转换为JSON安全字典，便于报告、审计和持久化。
    def to_dict(self) -> dict[str, Any]:
        # 结果返回：把`{'dataset_id': self.dataset_id, 'source_type': self.source_type.value, 'source_locator': dict(sel...`交给调用方。
        # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
        # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
        return {
            "dataset_id": self.dataset_id,
            "source_type": self.source_type.value,
            "source_locator": dict(self.source_locator),
            "dataset_mode": self.dataset_mode,
            "coverage_version": self.coverage_version,
            "schema_version": self.schema_version,
            "mapping_version": self.mapping_version,
            "dictionary_revision": self.dictionary_revision,
            "date_field": self.date_field,
            "entity_field": self.entity_field,
            "primary_key_fields": list(
                self.primary_key_fields
            ),
            "source_fields": list(self.source_fields),
            "canonical_objects": list(
                self.canonical_objects
            ),
            "field_mappings": [
                rule.to_dict()
                for rule in self.field_mappings
            ],
            "enabled": self.enabled,
            "tags": list(self.tags),
            "description": self.description,
        }

    # 执行from_dict逻辑，把输入参数转换为受合同约束的结果。
    # - 参数value：类型Mapping[str, Any]；进入函数后按合同校验或参与计算。
    # - 输出：返回类型'DatasetRegistration'；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：从普通字典恢复强类型对象，集中处理枚举、默认值和兼容性。
    @classmethod
    def from_dict(
        cls,
        value: Mapping[str, Any],
    ) -> "DatasetRegistration":
        # 结果返回：把`cls(dataset_id=value['dataset_id'], source_type=SourceType(value['source_type']), source_locator=...`交给调用方。
        # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
        # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
        return cls(
            dataset_id=value["dataset_id"],
            source_type=SourceType(value["source_type"]),
            source_locator=dict(value["source_locator"]),
            dataset_mode=value["dataset_mode"],
            coverage_version=value["coverage_version"],
            schema_version=value["schema_version"],
            mapping_version=value["mapping_version"],
            dictionary_revision=value["dictionary_revision"],
            date_field=value.get("date_field"),
            entity_field=value.get("entity_field"),
            primary_key_fields=tuple(
                value.get("primary_key_fields", [])
            ),
            source_fields=tuple(value["source_fields"]),
            canonical_objects=tuple(
                value.get("canonical_objects", [])
            ),
            field_mappings=tuple(
                FieldMappingRule.from_dict(item)
                for item in value.get(
                    "field_mappings",
                    [],
                )
            ),
            enabled=bool(value.get("enabled", True)),
            tags=tuple(value.get("tags", [])),
            description=value.get("description"),
        )


# 用于校验标准对象和 canonical 字段名称。
# - 状态成员：枚举值或方法共同描述该合同允许的有限状态和行为。
# - 数据变化：类本身不执行隐式I/O，实例字段只在显式构造、校验或方法调用时变化。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
class CanonicalFieldCatalog:
    """用于校验标准对象和 canonical 字段名称。"""

    # 执行__init__逻辑，把输入参数转换为受合同约束的结果。
    # - 参数fields_by_object：类型Mapping[str, Iterable[str]]；进入函数后按合同校验或参与计算。
    # - 输出：返回类型None；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
    def __init__(
        self,
        fields_by_object: Mapping[
            str,
            Iterable[str],
        ],
    ) -> None:
        # 变量更新：计算并保存self._fields，右侧逻辑为`{_require_text(object_name, 'canonical_object'): frozenset((_require_text(field_name, '...`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        self._fields = {
            _require_text(object_name, "canonical_object"):
                frozenset(
                    _require_text(field_name, "canonical_field")
                    for field_name in field_names
                )
            for object_name, field_names
            in fields_by_object.items()
        }

    # 执行contains逻辑，把输入参数转换为受合同约束的结果。
    # - 参数object_name：类型str；进入函数后按合同校验或参与计算。
    # - 参数field_name：类型str；进入函数后按合同校验或参与计算。
    # - 输出：返回类型bool；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
    def contains(
        self,
        object_name: str,
        field_name: str,
    ) -> bool:
        # 结果返回：把`field_name in self._fields.get(object_name, frozenset())`交给调用方。
        # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
        # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
        return field_name in self._fields.get(
            object_name,
            frozenset(),
        )

    # 执行validate_registration逻辑，把输入参数转换为受合同约束的结果。
    # - 参数registration：类型DatasetRegistration；进入函数后按合同校验或参与计算。
    # - 输出：返回类型list[str]；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
    def validate_registration(
        self,
        registration: DatasetRegistration,
    ) -> list[str]:
        # 变量更新：计算并保存errors，右侧逻辑为`[]`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        errors: list[str] = []

        # 迭代处理：依次读取`registration.field_mappings`中的元素，并绑定到`rule`。
        # - 维度变化：每轮处理一个元素，可能向列表、字典或累计值中增加一项。
        # - 为什么这样写：显式逐项校验可以精确指出哪个字段或Provider不符合合同。
        for rule in registration.field_mappings:
            # 条件门禁：判断`rule.canonical_target is None`，条件为真时进入受保护分支。
            # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
            # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
            if rule.canonical_target is None:
                continue

            # 内部断言：验证`rule.target_object is not None`在开发与测试阶段必须成立。
            # - 为什么这样写：断言用于发现程序员错误，不用于替代面向用户的数据合同异常。
            assert rule.target_object is not None
            # 内部断言：验证`rule.canonical_field is not None`在开发与测试阶段必须成立。
            # - 为什么这样写：断言用于发现程序员错误，不用于替代面向用户的数据合同异常。
            assert rule.canonical_field is not None

            # 条件门禁：判断`not self.contains(rule.target_object, rule.canonical_field)`，条件为真时进入受保护分支。
            # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
            # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
            if not self.contains(
                rule.target_object,
                rule.canonical_field,
            ):
                # API调用：执行`errors.append(f'标准字段不存在：{rule.canonical_target}')`以触发注册、写入对象状态或其他显式副作用。
                # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
                # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
                errors.append(
                    "标准字段不存在："
                    f"{rule.canonical_target}"
                )

        # 结果返回：把`errors`交给调用方。
        # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
        # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
        return errors

    # 执行assert_valid逻辑，把输入参数转换为受合同约束的结果。
    # - 参数registration：类型DatasetRegistration；进入函数后按合同校验或参与计算。
    # - 输出：返回类型None；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
    def assert_valid(
        self,
        registration: DatasetRegistration,
    ) -> None:
        # 变量更新：计算并保存errors，右侧逻辑为`self.validate_registration(registration)`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        errors = self.validate_registration(registration)

        # 条件门禁：判断`errors`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if errors:
            # 错误阻断：抛出`DataContractError('标准字段目录校验失败：' + '; '.join(errors))`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError(
                "标准字段目录校验失败："
                + "; ".join(errors)
            )


# 可持续扩展的数据集注册中心。
# - 状态成员：枚举值或方法共同描述该合同允许的有限状态和行为。
# - 数据变化：类本身不执行隐式I/O，实例字段只在显式构造、校验或方法调用时变化。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
class DatasetRegistry:
    """可持续扩展的数据集注册中心。"""

    # 执行__init__逻辑，把输入参数转换为受合同约束的结果。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态或模块常量。
    # - 输出：返回类型None；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
    def __init__(self) -> None:
        # 变量更新：计算并保存self._registrations，右侧逻辑为`{}`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        self._registrations: dict[
            str,
            DatasetRegistration,
        ] = {}

    # 执行register逻辑，把输入参数转换为受合同约束的结果。
    # - 参数registration：类型DatasetRegistration；进入函数后按合同校验或参与计算。
    # - 关键字参数replace：类型bool，默认值False；用于控制本次调用行为。
    # - 输出：返回类型None；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
    def register(
        self,
        registration: DatasetRegistration,
        *,
        replace: bool = False,
    ) -> None:
        # 条件门禁：判断`registration.dataset_id in self._registrations and (not replace)`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if (
            registration.dataset_id
            in self._registrations
            and not replace
        ):
            # 错误阻断：抛出`DataContractError(f'数据集已注册：{registration.dataset_id}')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError(
                "数据集已注册："
                f"{registration.dataset_id}"
            )

        # 变量更新：计算并保存self._registrations[registration.dataset_id]，右侧逻辑为`registration`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        self._registrations[
            registration.dataset_id
        ] = registration

    # 执行get逻辑，把输入参数转换为受合同约束的结果。
    # - 参数dataset_id：类型str；进入函数后按合同校验或参与计算。
    # - 输出：返回类型DatasetRegistration；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
    def get(
        self,
        dataset_id: str,
    ) -> DatasetRegistration:
        # 变量更新：计算并保存key，右侧逻辑为`_require_text(dataset_id, 'dataset_id')`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        key = _require_text(dataset_id, "dataset_id")

        # 异常边界：执行可能失败的转换或外部调用，并把底层异常转换为项目可理解的合同错误。
        # - 数据变化：成功路径产生正常结果，失败路径保留原异常作为cause或记录明确错误。
        # - 为什么这样写：统一异常类型可以让上层门禁稳定处理，而不依赖第三方异常细节。
        try:
            # 结果返回：把`self._registrations[key]`交给调用方。
            # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
            # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
            return self._registrations[key]
        # 异常转换：捕获预期失败并保留上下文，随后转成项目统一错误或降级结果。
        # - 为什么这样写：上层不需要理解第三方异常细节，也能得到稳定错误语义。
        except KeyError as exc:
            # 错误阻断：抛出`DataContractError(f'数据集未注册：{key}')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError(
                f"数据集未注册：{key}"
            ) from exc

    # 执行list逻辑，把输入参数转换为受合同约束的结果。
    # - 关键字参数enabled_only：类型bool，默认值False；用于控制本次调用行为。
    # - 关键字参数source_type：类型SourceType | None，默认值None；用于控制本次调用行为。
    # - 关键字参数canonical_object：类型str | None，默认值None；用于控制本次调用行为。
    # - 输出：返回类型list[DatasetRegistration]；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
    def list(
        self,
        *,
        enabled_only: bool = False,
        source_type: SourceType | None = None,
        canonical_object: str | None = None,
    ) -> list[DatasetRegistration]:
        # 变量更新：计算并保存result，右侧逻辑为`list(self._registrations.values())`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        result = list(self._registrations.values())

        # 条件门禁：判断`enabled_only`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if enabled_only:
            # 变量更新：计算并保存result，右侧逻辑为`[item for item in result if item.enabled]`。
            # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
            # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
            result = [
                item
                for item in result
                if item.enabled
            ]

        # 条件门禁：判断`source_type is not None`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if source_type is not None:
            # 变量更新：计算并保存result，右侧逻辑为`[item for item in result if item.source_type is source_type]`。
            # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
            # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
            result = [
                item
                for item in result
                if item.source_type is source_type
            ]

        # 条件门禁：判断`canonical_object is not None`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if canonical_object is not None:
            # 变量更新：计算并保存result，右侧逻辑为`[item for item in result if canonical_object in item.canonical_objects]`。
            # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
            # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
            result = [
                item
                for item in result
                if canonical_object
                in item.canonical_objects
            ]

        # 结果返回：把`sorted(result, key=lambda item: item.dataset_id)`交给调用方。
        # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
        # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
        return sorted(
            result,
            key=lambda item: item.dataset_id,
        )

    # 执行load_json逻辑，把输入参数转换为受合同约束的结果。
    # - 参数path：类型str | Path；进入函数后按合同校验或参与计算。
    # - 关键字参数replace：类型bool，默认值False；用于控制本次调用行为。
    # - 输出：返回类型DatasetRegistration；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
    def load_json(
        self,
        path: str | Path,
        *,
        replace: bool = False,
    ) -> DatasetRegistration:
        # 变量更新：计算并保存file_path，右侧逻辑为`Path(path)`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        file_path = Path(path)
        # 变量更新：计算并保存value，右侧逻辑为`json.loads(file_path.read_text(encoding='utf-8'))`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        value = json.loads(
            file_path.read_text(encoding="utf-8")
        )
        # 变量更新：计算并保存registration，右侧逻辑为`DatasetRegistration.from_dict(value)`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        registration = DatasetRegistration.from_dict(value)
        # API调用：执行`self.register(registration, replace=replace)`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        self.register(registration, replace=replace)
        # 结果返回：把`registration`交给调用方。
        # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
        # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
        return registration

    # 执行load_directory逻辑，把输入参数转换为受合同约束的结果。
    # - 参数directory：类型str | Path；进入函数后按合同校验或参与计算。
    # - 关键字参数replace：类型bool，默认值False；用于控制本次调用行为。
    # - 输出：返回类型list[DatasetRegistration]；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
    def load_directory(
        self,
        directory: str | Path,
        *,
        replace: bool = False,
    ) -> list[DatasetRegistration]:
        # 变量更新：计算并保存root，右侧逻辑为`Path(directory)`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        root = Path(directory)

        # 条件门禁：判断`not root.exists()`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if not root.exists():
            # 错误阻断：抛出`DataContractError(f'注册目录不存在：{root}')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError(
                f"注册目录不存在：{root}"
            )

        # 变量更新：计算并保存loaded，右侧逻辑为`[self.load_json(path, replace=replace) for path in sorted(root.glob('*.json'))]`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        loaded = [
            self.load_json(path, replace=replace)
            for path in sorted(root.glob("*.json"))
        ]
        # 结果返回：把`loaded`交给调用方。
        # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
        # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
        return loaded

    # 执行to_dict逻辑，把输入参数转换为受合同约束的结果。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态或模块常量。
    # - 输出：返回类型dict[str, Any]；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：把强类型对象转换为JSON安全字典，便于报告、审计和持久化。
    def to_dict(self) -> dict[str, Any]:
        # 结果返回：把`{'datasets': [item.to_dict() for item in self.list()]}`交给调用方。
        # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
        # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
        return {
            "datasets": [
                item.to_dict()
                for item in self.list()
            ]
        }


# 标准化转换函数注册中心。
# - 状态成员：枚举值或方法共同描述该合同允许的有限状态和行为。
# - 数据变化：类本身不执行隐式I/O，实例字段只在显式构造、校验或方法调用时变化。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
class TransformRegistry:
    """标准化转换函数注册中心。"""

    # 执行__init__逻辑，把输入参数转换为受合同约束的结果。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态或模块常量。
    # - 输出：返回类型None；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
    def __init__(self) -> None:
        # 变量更新：计算并保存self._transforms，右侧逻辑为`{}`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        self._transforms: dict[
            str,
            TransformFunction,
        ] = {}
        # API调用：执行`self.register('identity', self._identity)`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        self.register("identity", self._identity)
        # API调用：执行`self.register('multiply', self._multiply)`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        self.register("multiply", self._multiply)
        # API调用：执行`self.register('divide', self._divide)`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        self.register("divide", self._divide)
        # API调用：执行`self.register('negate', self._negate)`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        self.register("negate", self._negate)
        # API调用：执行`self.register('price_change_from_prev_close', self._price_change_from_prev_close)`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        self.register(
            "price_change_from_prev_close",
            self._price_change_from_prev_close,
        )
        # API调用：执行`self.register('pct_change_from_prev_close', self._pct_change_from_prev_close)`以触发注册、写入对象状态或其他显式副作用。
        # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
        # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
        self.register(
            "pct_change_from_prev_close",
            self._pct_change_from_prev_close,
        )

    # 执行register逻辑，把输入参数转换为受合同约束的结果。
    # - 参数transform_id：类型str；进入函数后按合同校验或参与计算。
    # - 参数function：类型TransformFunction；进入函数后按合同校验或参与计算。
    # - 关键字参数replace：类型bool，默认值False；用于控制本次调用行为。
    # - 输出：返回类型None；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
    def register(
        self,
        transform_id: str,
        function: TransformFunction,
        *,
        replace: bool = False,
    ) -> None:
        # 变量更新：计算并保存key，右侧逻辑为`_require_text(transform_id, 'transform_id')`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        key = _require_text(
            transform_id,
            "transform_id",
        )

        # 条件门禁：判断`key in self._transforms and (not replace)`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if key in self._transforms and not replace:
            # 错误阻断：抛出`DataContractError(f'转换函数已注册：{key}')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError(
                f"转换函数已注册：{key}"
            )

        # 条件门禁：判断`not callable(function)`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if not callable(function):
            # 错误阻断：抛出`DataContractError(f'转换函数不可调用：{key}')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError(
                f"转换函数不可调用：{key}"
            )

        # 变量更新：计算并保存self._transforms[key]，右侧逻辑为`function`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        self._transforms[key] = function

    # 执行apply逻辑，把输入参数转换为受合同约束的结果。
    # - 参数transform_id：类型str；进入函数后按合同校验或参与计算。
    # - 参数values：类型list[Any]；进入函数后按合同校验或参与计算。
    # - 关键字参数params：类型Mapping[str, Any]，必须显式提供；用于控制本次调用行为。
    # - 关键字参数record：类型Mapping[str, Any]，必须显式提供；用于控制本次调用行为。
    # - 关键字参数context：类型Mapping[str, Any]，必须显式提供；用于控制本次调用行为。
    # - 输出：返回类型Any；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
    def apply(
        self,
        transform_id: str,
        values: list[Any],
        *,
        params: Mapping[str, Any],
        record: Mapping[str, Any],
        context: Mapping[str, Any],
    ) -> Any:
        # 异常边界：执行可能失败的转换或外部调用，并把底层异常转换为项目可理解的合同错误。
        # - 数据变化：成功路径产生正常结果，失败路径保留原异常作为cause或记录明确错误。
        # - 为什么这样写：统一异常类型可以让上层门禁稳定处理，而不依赖第三方异常细节。
        try:
            # 变量更新：计算并保存function，右侧逻辑为`self._transforms[transform_id]`。
            # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
            # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
            function = self._transforms[transform_id]
        # 异常转换：捕获预期失败并保留上下文，随后转成项目统一错误或降级结果。
        # - 为什么这样写：上层不需要理解第三方异常细节，也能得到稳定错误语义。
        except KeyError as exc:
            # 错误阻断：抛出`DataContractError(f'转换函数未注册：{transform_id}')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError(
                f"转换函数未注册：{transform_id}"
            ) from exc

        # 结果返回：把`function(values, params, record, context)`交给调用方。
        # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
        # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
        return function(values, params, record, context)

    # 执行_require_one逻辑，把输入参数转换为受合同约束的结果。
    # - 参数values：类型list[Any]；进入函数后按合同校验或参与计算。
    # - 输出：返回类型Any；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
    @staticmethod
    def _require_one(values: list[Any]) -> Any:
        # 条件门禁：判断`len(values) != 1`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if len(values) != 1:
            # 错误阻断：抛出`DataContractError('该转换要求恰好一个来源值。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError(
                "该转换要求恰好一个来源值。"
            )

        # 结果返回：把`values[0]`交给调用方。
        # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
        # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
        return values[0]

    # 执行_identity逻辑，把输入参数转换为受合同约束的结果。
    # - 参数values：类型list[Any]；进入函数后按合同校验或参与计算。
    # - 参数params：类型Mapping[str, Any]；进入函数后按合同校验或参与计算。
    # - 参数record：类型Mapping[str, Any]；进入函数后按合同校验或参与计算。
    # - 参数context：类型Mapping[str, Any]；进入函数后按合同校验或参与计算。
    # - 输出：返回类型Any；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
    @classmethod
    def _identity(
        cls,
        values: list[Any],
        params: Mapping[str, Any],
        record: Mapping[str, Any],
        context: Mapping[str, Any],
    ) -> Any:
        # 结果返回：把`cls._require_one(values)`交给调用方。
        # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
        # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
        return cls._require_one(values)

    # 执行_multiply逻辑，把输入参数转换为受合同约束的结果。
    # - 参数values：类型list[Any]；进入函数后按合同校验或参与计算。
    # - 参数params：类型Mapping[str, Any]；进入函数后按合同校验或参与计算。
    # - 参数record：类型Mapping[str, Any]；进入函数后按合同校验或参与计算。
    # - 参数context：类型Mapping[str, Any]；进入函数后按合同校验或参与计算。
    # - 输出：返回类型Any；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
    @classmethod
    def _multiply(
        cls,
        values: list[Any],
        params: Mapping[str, Any],
        record: Mapping[str, Any],
        context: Mapping[str, Any],
    ) -> Any:
        # 变量更新：计算并保存value，右侧逻辑为`cls._require_one(values)`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        value = cls._require_one(values)

        # 条件门禁：判断`value is None`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if value is None:
            # 结果返回：把`None`交给调用方。
            # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
            # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
            return None

        # 变量更新：计算并保存factor，右侧逻辑为`params.get('factor')`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        factor = params.get("factor")
        # 条件门禁：判断`not isinstance(factor, (int, float))`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if not isinstance(factor, (int, float)):
            # 错误阻断：抛出`DataContractError('multiply 转换缺少数值 factor。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError(
                "multiply 转换缺少数值 factor。"
            )

        # 结果返回：把`value * factor`交给调用方。
        # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
        # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
        return value * factor

    # 执行_divide逻辑，把输入参数转换为受合同约束的结果。
    # - 参数values：类型list[Any]；进入函数后按合同校验或参与计算。
    # - 参数params：类型Mapping[str, Any]；进入函数后按合同校验或参与计算。
    # - 参数record：类型Mapping[str, Any]；进入函数后按合同校验或参与计算。
    # - 参数context：类型Mapping[str, Any]；进入函数后按合同校验或参与计算。
    # - 输出：返回类型Any；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
    @classmethod
    def _divide(
        cls,
        values: list[Any],
        params: Mapping[str, Any],
        record: Mapping[str, Any],
        context: Mapping[str, Any],
    ) -> Any:
        # 变量更新：计算并保存value，右侧逻辑为`cls._require_one(values)`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        value = cls._require_one(values)

        # 条件门禁：判断`value is None`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if value is None:
            # 结果返回：把`None`交给调用方。
            # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
            # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
            return None

        # 变量更新：计算并保存divisor，右侧逻辑为`params.get('divisor')`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        divisor = params.get("divisor")
        # 条件门禁：判断`not isinstance(divisor, (int, float)) or divisor == 0`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if (
            not isinstance(divisor, (int, float))
            or divisor == 0
        ):
            # 错误阻断：抛出`DataContractError('divide 转换需要非零 divisor。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError(
                "divide 转换需要非零 divisor。"
            )

        # 结果返回：把`value / divisor`交给调用方。
        # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
        # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
        return value / divisor

    # 执行_negate逻辑，把输入参数转换为受合同约束的结果。
    # - 参数values：类型list[Any]；进入函数后按合同校验或参与计算。
    # - 参数params：类型Mapping[str, Any]；进入函数后按合同校验或参与计算。
    # - 参数record：类型Mapping[str, Any]；进入函数后按合同校验或参与计算。
    # - 参数context：类型Mapping[str, Any]；进入函数后按合同校验或参与计算。
    # - 输出：返回类型Any；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
    @classmethod
    def _negate(
        cls,
        values: list[Any],
        params: Mapping[str, Any],
        record: Mapping[str, Any],
        context: Mapping[str, Any],
    ) -> Any:
        # 变量更新：计算并保存value，右侧逻辑为`cls._require_one(values)`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        value = cls._require_one(values)
        # 结果返回：把`None if value is None else -value`交给调用方。
        # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
        # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
        return None if value is None else -value

    # 执行_price_change_from_prev_close逻辑，把输入参数转换为受合同约束的结果。
    # - 参数values：类型list[Any]；进入函数后按合同校验或参与计算。
    # - 参数params：类型Mapping[str, Any]；进入函数后按合同校验或参与计算。
    # - 参数record：类型Mapping[str, Any]；进入函数后按合同校验或参与计算。
    # - 参数context：类型Mapping[str, Any]；进入函数后按合同校验或参与计算。
    # - 输出：返回类型Any；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
    @staticmethod
    def _price_change_from_prev_close(
        values: list[Any],
        params: Mapping[str, Any],
        record: Mapping[str, Any],
        context: Mapping[str, Any],
    ) -> Any:
        # 条件门禁：判断`len(values) != 1`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if len(values) != 1:
            # 错误阻断：抛出`DataContractError('价格变动转换要求一个 close 来源值。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError(
                "价格变动转换要求一个 close 来源值。"
            )

        # 变量更新：计算并保存close，右侧逻辑为`values[0]`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 固定数值：本表达式包含0；来源是当前项目既有合同或算法定义，迁移注释不改变其数值。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        close = values[0]
        # 变量更新：计算并保存prev_close，右侧逻辑为`context.get('prev_close')`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        prev_close = context.get("prev_close")

        # 条件门禁：判断`close is None or prev_close is None`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if close is None or prev_close is None:
            # 结果返回：把`None`交给调用方。
            # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
            # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
            return None

        # 结果返回：把`close - prev_close`交给调用方。
        # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
        # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
        return close - prev_close

    # 执行_pct_change_from_prev_close逻辑，把输入参数转换为受合同约束的结果。
    # - 参数values：类型list[Any]；进入函数后按合同校验或参与计算。
    # - 参数params：类型Mapping[str, Any]；进入函数后按合同校验或参与计算。
    # - 参数record：类型Mapping[str, Any]；进入函数后按合同校验或参与计算。
    # - 参数context：类型Mapping[str, Any]；进入函数后按合同校验或参与计算。
    # - 输出：返回类型Any；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
    @staticmethod
    def _pct_change_from_prev_close(
        values: list[Any],
        params: Mapping[str, Any],
        record: Mapping[str, Any],
        context: Mapping[str, Any],
    ) -> Any:
        # 条件门禁：判断`len(values) != 1`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if len(values) != 1:
            # 错误阻断：抛出`DataContractError('涨跌幅转换要求一个 close 来源值。')`并停止当前路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
            # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
            raise DataContractError(
                "涨跌幅转换要求一个 close 来源值。"
            )

        # 变量更新：计算并保存close，右侧逻辑为`values[0]`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 固定数值：本表达式包含0；来源是当前项目既有合同或算法定义，迁移注释不改变其数值。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        close = values[0]
        # 变量更新：计算并保存prev_close，右侧逻辑为`context.get('prev_close')`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        prev_close = context.get("prev_close")

        # 条件门禁：判断`close is None or prev_close is None or prev_close == 0`，条件为真时进入受保护分支。
        # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
        # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
        if (
            close is None
            or prev_close is None
            or prev_close == 0
        ):
            # 结果返回：把`None`交给调用方。
            # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
            # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
            return None

        # 变量更新：计算并保存precision，右侧逻辑为`int(params.get('precision', 6))`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 固定数值：本表达式包含6；来源是当前项目既有合同或算法定义，迁移注释不改变其数值。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        precision = int(params.get("precision", 6))
        # 结果返回：把`round((close / prev_close - 1) * 100, precision)`交给调用方。
        # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
        # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
        return round(
            (close / prev_close - 1) * 100,
            precision,
        )


# 定义MappingExecutionResult强类型合同，集中保存相关状态、参数和校验规则。
# - 字段dataset_id：类型str。
# - 字段outputs：类型dict[str, dict[str, Any]]。
# - 字段source_extensions：类型dict[str, Any]。
# - 字段warnings：类型list[str]。
# - 字段lineage：类型list[dict[str, Any]]。
# - 数据变化：类本身不执行隐式I/O，实例字段只在显式构造、校验或方法调用时变化。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
@dataclass(slots=True)
class MappingExecutionResult:
    # 变量更新：计算并保存dataset_id，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    dataset_id: str
    # 变量更新：计算并保存outputs，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    outputs: dict[str, dict[str, Any]]
    # 变量更新：计算并保存source_extensions，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    source_extensions: dict[str, Any]
    # 变量更新：计算并保存warnings，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    warnings: list[str]
    # 变量更新：计算并保存lineage，右侧逻辑为`类型声明`。
    # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
    # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
    lineage: list[dict[str, Any]]

    # 执行to_dict逻辑，把输入参数转换为受合同约束的结果。
    # - 输入：本逻辑不接收外部业务参数，只读取对象状态或模块常量。
    # - 输出：返回类型dict[str, Any]；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：把强类型对象转换为JSON安全字典，便于报告、审计和持久化。
    def to_dict(self) -> dict[str, Any]:
        # 结果返回：把`asdict(self)`交给调用方。
        # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
        # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
        return asdict(self)


# 把一个来源记录映射为一个或多个标准对象片段。
# - 状态成员：枚举值或方法共同描述该合同允许的有限状态和行为。
# - 数据变化：类本身不执行隐式I/O，实例字段只在显式构造、校验或方法调用时变化。
# - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
class CanonicalMappingEngine:
    """把一个来源记录映射为一个或多个标准对象片段。"""

    # 执行__init__逻辑，把输入参数转换为受合同约束的结果。
    # - 参数transforms：类型TransformRegistry | None，默认值None；进入函数后按合同校验或参与计算。
    # - 输出：返回类型None；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
    def __init__(
        self,
        transforms: TransformRegistry | None = None,
    ) -> None:
        # 变量更新：计算并保存self.transforms，右侧逻辑为`transforms or TransformRegistry()`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        self.transforms = transforms or TransformRegistry()

    # 执行map_record逻辑，把输入参数转换为受合同约束的结果。
    # - 参数registration：类型DatasetRegistration；进入函数后按合同校验或参与计算。
    # - 参数record：类型Mapping[str, Any]；进入函数后按合同校验或参与计算。
    # - 关键字参数context：类型Mapping[str, Any] | None，默认值None；用于控制本次调用行为。
    # - 输出：返回类型MappingExecutionResult；调用方按该类型继续校验、路由或序列化。
    # - 数据变化：函数只按签名和合同更新局部值、对象字段或明确返回值；不会隐藏额外副作用。
    # - 为什么这样写：把该职责封装在独立边界内，可以减少重复代码并让校验、测试和替换路径保持一致。
    def map_record(
        self,
        registration: DatasetRegistration,
        record: Mapping[str, Any],
        *,
        context: Mapping[str, Any] | None = None,
    ) -> MappingExecutionResult:
        # 变量更新：计算并保存context_values，右侧逻辑为`context or {}`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        context_values = context or {}
        # 变量更新：计算并保存outputs，右侧逻辑为`{}`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        outputs: dict[str, dict[str, Any]] = {}
        # 变量更新：计算并保存warnings，右侧逻辑为`[]`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        warnings: list[str] = []
        # 变量更新：计算并保存lineage，右侧逻辑为`[]`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        lineage: list[dict[str, Any]] = []
        # 变量更新：计算并保存mapped_source_fields，右侧逻辑为`set()`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        mapped_source_fields: set[str] = set()

        # 迭代处理：依次读取`registration.field_mappings`中的元素，并绑定到`rule`。
        # - 维度变化：每轮处理一个元素，可能向列表、字典或累计值中增加一项。
        # - 为什么这样写：显式逐项校验可以精确指出哪个字段或Provider不符合合同。
        for rule in registration.field_mappings:
            # 条件门禁：判断`rule.status not in {MappingStatus.MAPPED, MappingStatus.WARNING}`，条件为真时进入受保护分支。
            # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
            # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
            if rule.status not in {
                MappingStatus.MAPPED,
                MappingStatus.WARNING,
            }:
                continue

            # 变量更新：计算并保存missing，右侧逻辑为`[field_name for field_name in rule.source_fields if field_name not in record]`。
            # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
            # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
            missing = [
                field_name
                for field_name in rule.source_fields
                if field_name not in record
            ]

            # 条件门禁：判断`missing`，条件为真时进入受保护分支。
            # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
            # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
            if missing:
                # 变量更新：计算并保存message，右侧逻辑为`f'映射 {rule.canonical_target} 缺少来源字段：{missing}'`。
                # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
                # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
                message = (
                    f"映射 {rule.canonical_target} "
                    f"缺少来源字段：{missing}"
                )

                # 条件门禁：判断`rule.required`，条件为真时进入受保护分支。
                # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
                # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
                if rule.required:
                    # 错误阻断：抛出`DataContractError(message)`并停止当前路径。
                    # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
                    # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
                    raise DataContractError(message)

                # API调用：执行`warnings.append(message)`以触发注册、写入对象状态或其他显式副作用。
                # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
                # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
                warnings.append(message)
                continue

            # 变量更新：计算并保存values，右侧逻辑为`[record[field_name] for field_name in rule.source_fields]`。
            # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
            # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
            values = [
                record[field_name]
                for field_name in rule.source_fields
            ]
            # 变量更新：计算并保存value，右侧逻辑为`self.transforms.apply(rule.transform_id, values, params=rule.transform_params, record=r...`。
            # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
            # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
            value = self.transforms.apply(
                rule.transform_id,
                values,
                params=rule.transform_params,
                record=record,
                context=context_values,
            )

            # 内部断言：验证`rule.target_object is not None`在开发与测试阶段必须成立。
            # - 为什么这样写：断言用于发现程序员错误，不用于替代面向用户的数据合同异常。
            assert rule.target_object is not None
            # 内部断言：验证`rule.canonical_field is not None`在开发与测试阶段必须成立。
            # - 为什么这样写：断言用于发现程序员错误，不用于替代面向用户的数据合同异常。
            assert rule.canonical_field is not None

            # 变量更新：计算并保存target，右侧逻辑为`outputs.setdefault(rule.target_object, {})`。
            # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
            # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
            target = outputs.setdefault(
                rule.target_object,
                {},
            )

            # 条件门禁：判断`rule.canonical_field in target`，条件为真时进入受保护分支。
            # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
            # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
            if rule.canonical_field in target:
                # 错误阻断：抛出`DataContractError(f'同一记录重复写入标准字段：{rule.canonical_target}')`并停止当前路径。
                # - 数据变化：不产生正常返回值，调用方必须捕获或让任务失败。
                # - 为什么这样写：发现合同破坏时立即失败，比静默修正或继续运行更安全。
                raise DataContractError(
                    "同一记录重复写入标准字段："
                    f"{rule.canonical_target}"
                )

            # 变量更新：计算并保存target[rule.canonical_field]，右侧逻辑为`value`。
            # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
            # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
            target[rule.canonical_field] = value
            # API调用：执行`mapped_source_fields.update(rule.source_fields)`以触发注册、写入对象状态或其他显式副作用。
            # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
            # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
            mapped_source_fields.update(rule.source_fields)
            # API调用：执行`lineage.append({'target_object': rule.target_object, 'canonical_field': rule.canonical_field, 'so...`以触发注册、写入对象状态或其他显式副作用。
            # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
            # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
            lineage.append(
                {
                    "target_object": rule.target_object,
                    "canonical_field":
                        rule.canonical_field,
                    "source_fields":
                        list(rule.source_fields),
                    "transform_id":
                        rule.transform_id,
                    "transform_params":
                        dict(rule.transform_params),
                    "mapping_version":
                        registration.mapping_version,
                    "dictionary_revision":
                        registration.dictionary_revision,
                }
            )

            # 条件门禁：判断`rule.status is MappingStatus.WARNING`，条件为真时进入受保护分支。
            # - 数据变化：分支本身不改变值，只有分支体内的显式赋值、返回或异常会改变控制流。
            # - 为什么这样写：把无效状态尽早拒绝，避免错误数据继续传播到更深层。
            if rule.status is MappingStatus.WARNING:
                # API调用：执行`warnings.append(f'映射规则带警告：{rule.canonical_target}')`以触发注册、写入对象状态或其他显式副作用。
                # - 参数变化：实参按函数签名传入，返回值未保存表示调用目的主要是副作用或校验。
                # - 为什么这样写：把副作用单独成行便于审计，并可在测试中替换或模拟。
                warnings.append(
                    "映射规则带警告："
                    f"{rule.canonical_target}"
                )

        # 变量更新：计算并保存source_extensions，右侧逻辑为`{field_name: value for field_name, value in record.items() if field_name not in mapped_...`。
        # - 数据变化：赋值只改变当前作用域中的目标变量或对象字段，类型由注解或右侧表达式决定。
        # - 为什么这样写：先给中间结果命名，便于后续校验、错误定位和审计，不重复执行同一表达式。
        source_extensions = {
            field_name: value
            for field_name, value in record.items()
            if field_name not in mapped_source_fields
        }

        # 结果返回：把`MappingExecutionResult(dataset_id=registration.dataset_id, outputs=outputs, source_extensions=sou...`交给调用方。
        # - 数据变化：函数在此结束，返回对象保持当前已校验状态。
        # - 为什么这样写：显式返回点让调用方清楚获得的数据类型和控制流终点。
        return MappingExecutionResult(
            dataset_id=registration.dataset_id,
            outputs=outputs,
            source_extensions=source_extensions,
            warnings=warnings,
            lineage=lineage,
        )
