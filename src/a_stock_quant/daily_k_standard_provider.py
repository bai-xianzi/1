# 模块总览：把DolphinDB日K标准化服务接入统一StandardDataService。
# - 输入输出：输入为标准日K查询；输出为DailyBar或OwnershipSnapshot记录及质量、血缘元数据。
# - 数据与安全：日K来源异常必须保留为质量标记，不能在Provider层静默修正。
# - 运行边界：导入模块和阅读注释不会触发数据库写入；只有显式调用对应函数并满足门禁时才执行I/O。
# - 为什么这样写：先声明职责、单位、时点和副作用边界，读者可以在阅读实现前建立正确的金融与工程语境。
"""日K标准数据Provider。

本模块属于日K数据集插件层，不属于通用标准数据服务核心。

职责：
1. 把DolphinDBDailyKStandardizedService接入StandardDataService；
2. 传播日K覆盖、映射、字典、质量和血缘信息；
3. 保持通用核心不依赖DolphinDB和日K专属规则。
"""

# 依赖导入：加载`from __future__ import annotations`所提供的类型、标准库或项目内能力。
# - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
# - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
from __future__ import annotations

# 依赖导入：加载`from collections import Counter`所提供的类型、标准库或项目内能力。
# - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
# - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
from collections import Counter
# 依赖导入：加载`from typing import Any, Mapping`所提供的类型、标准库或项目内能力。
# - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
# - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
from typing import Any, Mapping

# 依赖导入：加载`from .data_contracts import DataContractError, MappingStatus, QualityStatus`所提供的类型、标准库或项目内能力。
# - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
# - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
from .data_contracts import (
    DataContractError,
    MappingStatus,
    QualityStatus,
)
# 依赖导入：加载`from .dolphindb_daily_k_service import DailyKReadRequest, DolphinDBDailyKStandardizedService`所提供的类型、标准库或项目内能力。
# - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
# - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
from .dolphindb_daily_k_service import (
    DailyKReadRequest,
    DolphinDBDailyKStandardizedService,
)
# 依赖导入：加载`from .standard_data_service import ProviderDescriptor, StandardDataQuery, StandardDataRecord, StandardDatasetProvider, StandardQueryMetadat…`所提供的类型、标准库或项目内能力。
# - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
# - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
from .standard_data_service import (
    ProviderDescriptor,
    StandardDataQuery,
    StandardDataRecord,
    StandardDatasetProvider,
    StandardQueryMetadata,
    StandardQueryResult,
)


# 关键常量_BLOCKING_DAILY_K_FLAGS：集中保存`frozenset({'SOURCE_PRICE_CHANGE_MISMATCH', 'SOURCE_PCT_CHANGE_SEMANTIC_MISMATCH', 'SOURCE_ADJ_FORMU…`对应的合同值、Schema集合或运行边界。
# - 来源与范围：该值来自当前项目任务、配置、真实数据画像或安全合同；未明确说明时不得外推为行业统一标准。
# - 单位与实例：数值单位由变量名、相邻校验和调用语义共同限定；字符串用于版本、字段、状态或DolphinDB对象标识。
# - 为什么这样写：集中命名固定参数可避免魔法值散落，并让升级、审计和回归测试有稳定锚点。
_BLOCKING_DAILY_K_FLAGS = frozenset(
    {
        "SOURCE_PRICE_CHANGE_MISMATCH",
        "SOURCE_PCT_CHANGE_SEMANTIC_MISMATCH",
        "SOURCE_ADJ_FORMULA_MISMATCH",
    }
)


# 类DailyKStandardDataProvider：把 TASK_010 日K服务接入统一标准数据服务。
# - 结构：继承或实现StandardDatasetProvider；类体约包含1个字段或常量、7个方法。
# - 数据变化：类定义阶段不执行隐式I/O，实例只在构造或显式方法调用时改变受控状态。
# - 实操：调用方通过该类型集中传递配置、记录、服务或结果，避免跨模块使用无约束字典。
# - 为什么这样写：强类型边界能集中维护单位、时点、主键和安全不变量，并降低供应商耦合。
class DailyKStandardDataProvider(StandardDatasetProvider):
    """把 TASK_010 日K服务接入统一标准数据服务。"""

    # 状态计算：把`'dolphindb_daily_k_standard_provider'`的结果保存到`provider_id`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    provider_id = "dolphindb_daily_k_standard_provider"

    # 函数__init__：执行__init__对应的业务处理。
    # - 输入：service:DolphinDBDailyKStandardizedService；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型None；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    def __init__(
        self,
        service: DolphinDBDailyKStandardizedService,
    ) -> None:
        # 状态计算：把`service`的结果保存到`self.service`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        self.service = service
        # 状态计算：把`service.registration`的结果保存到`self.registration`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        self.registration = service.registration
        # 状态计算：把`self._build_field_catalog()`的结果保存到`self._fields_by_object`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        self._fields_by_object = self._build_field_catalog()

    # 函数_build_field_catalog：执行_build_field_catalog对应的业务处理。
    # - 输入：无外部业务参数；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型dict[str, tuple[str, ...]]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把对象构造、字段映射或标准化转换步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    def _build_field_catalog(
        self,
    ) -> dict[str, tuple[str, ...]]:
        # 状态计算：把`{}`的结果保存到`fields`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        fields: dict[str, list[str]] = {}

        # 循环处理：逐项遍历`self.registration.field_mappings`，把当前元素绑定到`rule`。
        # - 数据变化：每轮只处理一个来源记录、字段、文件或证据项，并显式累计到局部集合或输出对象。
        # - 为什么这样写：逐项处理便于保留行级血缘、隔离单项异常，并控制16GB单机上的峰值内存。
        for rule in self.registration.field_mappings:
            # 条件门禁：判断`rule.status not in {MappingStatus.MAPPED, MappingStatus.WARNING}`，条件成立时进入对应的数据、安全或异常处理分支。
            # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
            # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
            if rule.status not in {
                MappingStatus.MAPPED,
                MappingStatus.WARNING,
            }:
                # 控制流：跳过本轮剩余步骤，使循环或占位分支按既定合同继续。
                # - 数据变化：本语句不直接改变业务记录，只调整当前执行路径。
                # - 为什么这样写：显式控制流比隐式嵌套更容易检查边界和异常处理。
                continue

            # 条件门禁：判断`rule.target_object is None or rule.canonical_field is None`，条件成立时进入对应的数据、安全或异常处理分支。
            # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
            # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
            if (
                rule.target_object is None
                or rule.canonical_field is None
            ):
                # 控制流：跳过本轮剩余步骤，使循环或占位分支按既定合同继续。
                # - 数据变化：本语句不直接改变业务记录，只调整当前执行路径。
                # - 为什么这样写：显式控制流比隐式嵌套更容易检查边界和异常处理。
                continue

            # 状态计算：把`fields.setdefault(rule.target_object, [])`的结果保存到`values`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            values = fields.setdefault(
                rule.target_object,
                [],
            )

            # 条件门禁：判断`rule.canonical_field not in values`，条件成立时进入对应的数据、安全或异常处理分支。
            # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
            # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
            if rule.canonical_field not in values:
                # 显式调用：执行`values.append(rule.canonical_field)`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
                # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
                # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
                values.append(rule.canonical_field)

        # 结果返回：把`{object_name: tuple(field_names) for object_name, field_names in fields.items()}`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return {
            object_name: tuple(field_names)
            for object_name, field_names in fields.items()
        }

    # 函数descriptor：执行descriptor对应的业务处理。
    # - 输入：无外部业务参数；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型ProviderDescriptor；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    @property
    def descriptor(self) -> ProviderDescriptor:
        # 结果返回：把`ProviderDescriptor(provider_id=self.provider_id, dataset_id=self.registration.dataset_id, supported_objects=tuple(sorte…`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return ProviderDescriptor(
            provider_id=self.provider_id,
            dataset_id=self.registration.dataset_id,
            supported_objects=tuple(
                sorted(self._fields_by_object)
            ),
            coverage_version=
                self.registration.coverage_version,
            mapping_version=
                self.registration.mapping_version,
            dictionary_revision=
                self.registration.dictionary_revision,
        )

    # 函数available_fields：执行available_fields对应的业务处理。
    # - 输入：canonical_object:str；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型tuple[str, ...]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    def available_fields(
        self,
        canonical_object: str,
    ) -> tuple[str, ...]:
        # 异常边界：尝试执行可能失败的解析、查询、文件或类型转换步骤，并由后续处理保留错误证据。
        # - 数据变化：正常路径产生业务结果；异常路径不得静默伪造数据，应抛出、记录或隔离。
        # - 为什么这样写：把外部环境故障与业务合同失败分开，便于重试、回滚和准确验收。
        try:
            # 结果返回：把`self._fields_by_object[canonical_object]`交给调用方并结束当前函数。
            # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
            # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
            return self._fields_by_object[
                canonical_object
            ]
        except KeyError as exc:
            # 错误阻断：抛出`DataContractError(f'日K Provider 不支持标准对象：{canonical_object}')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
            raise DataContractError(
                "日K Provider 不支持标准对象："
                f"{canonical_object}"
            ) from exc

    # 函数_validate_fields：执行_validate_fields对应的业务处理。
    # - 输入：request:StandardDataQuery；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型tuple[str, ...]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把合同、数据质量或安全门禁校验步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    def _validate_fields(
        self,
        request: StandardDataQuery,
    ) -> tuple[str, ...]:
        # 状态计算：把`self.available_fields(request.canonical_object)`的结果保存到`available`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        available = self.available_fields(
            request.canonical_object
        )

        # 条件门禁：判断`not request.fields`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if not request.fields:
            # 结果返回：把`available`交给调用方并结束当前函数。
            # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
            # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
            return available

        # 状态计算：把`sorted(set(request.fields) - set(available))`的结果保存到`unknown`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        unknown = sorted(
            set(request.fields) - set(available)
        )

        # 条件门禁：判断`unknown`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if unknown:
            # 错误阻断：抛出`DataContractError(f'请求了未登记的标准字段：{unknown}')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
            raise DataContractError(
                "请求了未登记的标准字段："
                f"{unknown}"
            )

        # 结果返回：把`request.fields`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return request.fields

    # 函数_primary_key：执行_primary_key对应的业务处理。
    # - 输入：canonical_object:str、values:Mapping[str, Any]、fallback:Mapping[str, Any]；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型dict[str, Any]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    @staticmethod
    def _primary_key(
        canonical_object: str,
        values: Mapping[str, Any],
        fallback: Mapping[str, Any],
    ) -> dict[str, Any]:
        # 条件门禁：判断`canonical_object == 'DailyBar'`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if canonical_object == "DailyBar":
            # 结果返回：把`{'instrument_id': values.get('instrument_id', fallback.get('instrument_id')), 'trade_date': values.get('trade_date', fa…`交给调用方并结束当前函数。
            # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
            # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
            return {
                "instrument_id": values.get(
                    "instrument_id",
                    fallback.get("instrument_id"),
                ),
                "trade_date": values.get(
                    "trade_date",
                    fallback.get("trade_date"),
                ),
            }

        # 条件门禁：判断`canonical_object == 'OwnershipSnapshot'`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if canonical_object == "OwnershipSnapshot":
            # 结果返回：把`{'instrument_id': values.get('instrument_id', fallback.get('instrument_id')), 'as_of_date': values.get('as_of_date', fa…`交给调用方并结束当前函数。
            # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
            # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
            return {
                "instrument_id": values.get(
                    "instrument_id",
                    fallback.get("instrument_id"),
                ),
                "as_of_date": values.get(
                    "as_of_date",
                    fallback.get("trade_date"),
                ),
            }

        # 结果返回：把`dict(fallback)`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return dict(fallback)

    # 函数query：执行query对应的业务处理。
    # - 输入：request:StandardDataQuery；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型StandardQueryResult；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把只读查询或来源发现步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    def query(
        self,
        request: StandardDataQuery,
    ) -> StandardQueryResult:
        # 条件门禁：判断`request.dataset_id != self.registration.dataset_id`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if request.dataset_id != self.registration.dataset_id:
            # 错误阻断：抛出`DataContractError('查询数据集与日K Provider 不一致。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
            raise DataContractError(
                "查询数据集与日K Provider 不一致。"
            )

        # 状态计算：把`self._validate_fields(request)`的结果保存到`selected_fields`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        selected_fields = self._validate_fields(request)

        # 状态计算：把`self.service.read(DailyKReadRequest(instrument_ids=request.instrument_ids, start_date=request.start…`的结果保存到`batch`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        batch = self.service.read(
            DailyKReadRequest(
                instrument_ids=request.instrument_ids,
                start_date=request.start_date,
                end_date=request.end_date,
                limit_per_instrument=
                    request.limit_per_instrument,
            )
        )

        # 状态计算：把`[]`的结果保存到`rows`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        rows: list[StandardDataRecord] = []
        # 状态计算：把`list(batch.warnings)`的结果保存到`warnings`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        warnings = list(batch.warnings)
        # 状态计算：把`Counter()`的结果保存到`quality_counts`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        quality_counts: Counter[str] = Counter()
        # 状态计算：把`0`的结果保存到`lineage_item_count`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        lineage_item_count = 0

        # 循环处理：逐项遍历`batch.records`，把当前元素绑定到`source_record`。
        # - 数据变化：每轮只处理一个来源记录、字段、文件或证据项，并显式累计到局部集合或输出对象。
        # - 为什么这样写：逐项处理便于保留行级血缘、隔离单项异常，并控制16GB单机上的峰值内存。
        for source_record in batch.records:
            # 状态计算：把`source_record.canonical_objects.get(request.canonical_object)`的结果保存到`canonical_values`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            canonical_values = (
                source_record.canonical_objects.get(
                    request.canonical_object
                )
            )

            # 条件门禁：判断`canonical_values is None`，条件成立时进入对应的数据、安全或异常处理分支。
            # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
            # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
            if canonical_values is None:
                # 显式调用：执行`warnings.append(f'来源记录缺少标准对象：{source_record.source_record_id} {request.canonical_object}')`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
                # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
                # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
                warnings.append(
                    "来源记录缺少标准对象："
                    f"{source_record.source_record_id} "
                    f"{request.canonical_object}"
                )
                # 控制流：跳过本轮剩余步骤，使循环或占位分支按既定合同继续。
                # - 数据变化：本语句不直接改变业务记录，只调整当前执行路径。
                # - 为什么这样写：显式控制流比隐式嵌套更容易检查边界和异常处理。
                continue

            # 状态计算：把`{field_name: canonical_values.get(field_name) for field_name in selected_fields}`的结果保存到`projected_values`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            projected_values = {
                field_name: canonical_values.get(field_name)
                for field_name in selected_fields
            }

            # 状态计算：把`tuple(source_record.quality_flags if request.include_quality_flags else ())`的结果保存到`quality_flags`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            quality_flags = tuple(
                source_record.quality_flags
                if request.include_quality_flags
                else ()
            )
            # 显式调用：执行`quality_counts.update(quality_flags)`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
            # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
            # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
            quality_counts.update(quality_flags)

            # 状态计算：把`tuple((item for item in source_record.lineage if item.get('target_object') == request.canonical_obj…`的结果保存到`lineage`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            lineage = tuple(
                item
                for item in source_record.lineage
                if (
                    item.get("target_object")
                    == request.canonical_object
                    and (
                        not request.fields
                        or item.get("canonical_field")
                        in request.fields
                    )
                )
            )
            # 条件门禁：判断`not request.include_lineage`，条件成立时进入对应的数据、安全或异常处理分支。
            # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
            # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
            if not request.include_lineage:
                # 状态计算：把`()`的结果保存到`lineage`，供当前逻辑后续校验、转换、累计或返回。
                # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
                # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
                lineage = ()

            # 状态计算：把`len(lineage)`的结果保存到`lineage_item_count`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            lineage_item_count += len(lineage)

            # 显式调用：执行`rows.append(StandardDataRecord(canonical_object=request.canonical_object, primary_key=self._primary_key(request.canonical_object, canonical…`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
            # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
            # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
            rows.append(
                StandardDataRecord(
                    canonical_object=
                        request.canonical_object,
                    primary_key=self._primary_key(
                        request.canonical_object,
                        canonical_values,
                        source_record.primary_key,
                    ),
                    values=projected_values,
                    source_record_id=
                        source_record.source_record_id,
                    source_extensions=(
                        dict(
                            source_record.source_extensions
                        )
                        if request.include_source_extensions
                        else {}
                    ),
                    quality_flags=quality_flags,
                    lineage=lineage,
                )
            )

        # 状态计算：把`sum((count for flag, count in quality_counts.items() if flag in _BLOCKING_DAILY_K_FLAGS))`的结果保存到`blocking_flag_count`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        blocking_flag_count = sum(
            count
            for flag, count in quality_counts.items()
            if flag in _BLOCKING_DAILY_K_FLAGS
        )

        # 条件门禁：判断`blocking_flag_count`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if blocking_flag_count:
            # 状态计算：把`QualityStatus.FAILED`的结果保存到`status`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            status = QualityStatus.FAILED
            # 状态计算：把`True`的结果保存到`blocks_downstream`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            blocks_downstream = True
        # 条件门禁：判断`warnings`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        elif warnings:
            # 状态计算：把`QualityStatus.WARNING`的结果保存到`status`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            status = QualityStatus.WARNING
            # 状态计算：把`False`的结果保存到`blocks_downstream`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            blocks_downstream = False
        else:
            # 状态计算：把`QualityStatus.PASSED`的结果保存到`status`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            status = QualityStatus.PASSED
            # 状态计算：把`False`的结果保存到`blocks_downstream`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            blocks_downstream = False

        # 状态计算：把`StandardQueryMetadata(dataset_id=batch.dataset_id, canonical_object=request.canonical_object, provi…`的结果保存到`metadata`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        metadata = StandardQueryMetadata(
            dataset_id=batch.dataset_id,
            canonical_object=
                request.canonical_object,
            provider_id=self.provider_id,
            coverage_version=batch.coverage_version,
            mapping_version=batch.mapping_version,
            dictionary_revision=
                batch.dictionary_revision,
            source_row_count=batch.source_row_count,
            result_count=len(rows),
            status=status,
            blocks_downstream=blocks_downstream,
            warnings=tuple(warnings),
            quality_flag_counts=dict(
                sorted(quality_counts.items())
            ),
            lineage_item_count=lineage_item_count,
        )

        # 结果返回：把`StandardQueryResult(query=request, metadata=metadata, records=tuple(rows))`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return StandardQueryResult(
            query=request,
            metadata=metadata,
            records=tuple(rows),
        )
