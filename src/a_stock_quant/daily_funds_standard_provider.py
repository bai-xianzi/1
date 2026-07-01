# 模块总览：把七类日线资金与竞价标准化服务接入来源无关的StandardDataService。
# - 输入输出：输入为标准查询请求；输出为Canonical记录、质量标记、血缘和Provider元数据。
# - 数据与安全：Provider层只做查询适配与投影，不重新定义来源语义或绕过Readiness门禁。
# - 运行边界：导入模块和阅读注释不会触发数据库写入；只有显式调用对应函数并满足门禁时才执行I/O。
# - 为什么这样写：先声明职责、单位、时点和副作用边界，读者可以在阅读实现前建立正确的金融与工程语境。
"""七类日线资金 StandardDataService Provider。

把 TASK_017C 的只读 Canonical 服务注册到统一标准数据入口。
分类节点使用 entity_ids，证券型来源使用 instrument_ids。
"""

# 依赖导入：加载`from __future__ import annotations`所提供的类型、标准库或项目内能力。
# - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
# - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
from __future__ import annotations

# 依赖导入：加载`from collections import Counter`所提供的类型、标准库或项目内能力。
# - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
# - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
from collections import Counter
# 依赖导入：加载`from pathlib import Path`所提供的类型、标准库或项目内能力。
# - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
# - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
from pathlib import Path
# 依赖导入：加载`from typing import Any`所提供的类型、标准库或项目内能力。
# - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
# - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
from typing import Any

# 依赖导入：加载`import yaml`所提供的类型、标准库或项目内能力。
# - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
# - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
import yaml

# 依赖导入：加载`from .data_contracts import DataContractError, QualityStatus`所提供的类型、标准库或项目内能力。
# - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
# - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
from .data_contracts import DataContractError, QualityStatus
# 依赖导入：加载`from .daily_funds_canonical_contract import REQUIRED_DATASETS`所提供的类型、标准库或项目内能力。
# - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
# - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
from .daily_funds_canonical_contract import REQUIRED_DATASETS
# 依赖导入：加载`from .dolphindb_daily_funds_service import DailyFundsReadRequest, DolphinDBDailyFundsCanonicalService`所提供的类型、标准库或项目内能力。
# - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
# - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
from .dolphindb_daily_funds_service import (
    DailyFundsReadRequest,
    DolphinDBDailyFundsCanonicalService,
)
# 依赖导入：加载`from .standard_data_service import ENTITY_SELECTOR_MODE, INSTRUMENT_SELECTOR_MODE, ProviderDescriptor, StandardDataQuery, StandardDataRecor…`所提供的类型、标准库或项目内能力。
# - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
# - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
from .standard_data_service import (
    ENTITY_SELECTOR_MODE,
    INSTRUMENT_SELECTOR_MODE,
    ProviderDescriptor,
    StandardDataQuery,
    StandardDataRecord,
    StandardDataService,
    StandardDataUsage,
    StandardDatasetProvider,
    StandardQueryMetadata,
    StandardQueryResult,
)


# 关键常量PROVIDER_REGISTRY_RELATIVE_PATH：集中保存`'configs/datasets/a_stock_daily_funds_standard_providers.yaml'`对应的合同值、Schema集合或运行边界。
# - 来源与范围：该值来自当前项目任务、配置、真实数据画像或安全合同；未明确说明时不得外推为行业统一标准。
# - 单位与实例：数值单位由变量名、相邻校验和调用语义共同限定；字符串用于版本、字段、状态或DolphinDB对象标识。
# - 为什么这样写：集中命名固定参数可避免魔法值散落，并让升级、审计和回归测试有稳定锚点。
PROVIDER_REGISTRY_RELATIVE_PATH = (
    "configs/datasets/a_stock_daily_funds_standard_providers.yaml"
)

# 关键常量_HISTORICAL_BLOCKED_USAGES：集中保存`frozenset({StandardDataUsage.STRICT_HISTORICAL_BACKTEST, StandardDataUsage.HISTORICAL_MODEL_TRAININ…`对应的合同值、Schema集合或运行边界。
# - 来源与范围：该值来自当前项目任务、配置、真实数据画像或安全合同；未明确说明时不得外推为行业统一标准。
# - 单位与实例：数值单位由变量名、相邻校验和调用语义共同限定；字符串用于版本、字段、状态或DolphinDB对象标识。
# - 为什么这样写：集中命名固定参数可避免魔法值散落，并让升级、审计和回归测试有稳定锚点。
_HISTORICAL_BLOCKED_USAGES = frozenset(
    {
        StandardDataUsage.STRICT_HISTORICAL_BACKTEST,
        StandardDataUsage.HISTORICAL_MODEL_TRAINING,
    }
)


# 函数_load_registry：执行_load_registry对应的业务处理。
# - 输入：project_root:Path；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型dict[str, Any]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
# - 为什么这样写：把只读查询或来源发现步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def _load_registry(project_root: Path) -> dict[str, Any]:
    # 状态计算：把`project_root / PROVIDER_REGISTRY_RELATIVE_PATH`的结果保存到`path`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    path = project_root / PROVIDER_REGISTRY_RELATIVE_PATH
    # 状态计算：把`yaml.safe_load(path.read_text(encoding='utf-8'))`的结果保存到`payload`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    # 条件门禁：判断`not isinstance(payload, dict)`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if not isinstance(payload, dict):
        # 错误阻断：抛出`DataContractError('Provider注册配置根节点必须是映射。')`并停止当前正常路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
        # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
        raise DataContractError("Provider注册配置根节点必须是映射。")
    # 结果返回：把`payload`交给调用方并结束当前函数。
    # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return payload


# 类DailyFundsStandardDataProvider：把单个七类来源接入统一 StandardDataService。
# - 结构：继承或实现StandardDatasetProvider；类体约包含0个字段或常量、8个方法。
# - 数据变化：类定义阶段不执行隐式I/O，实例只在构造或显式方法调用时改变受控状态。
# - 实操：调用方通过该类型集中传递配置、记录、服务或结果，避免跨模块使用无约束字典。
# - 为什么这样写：强类型边界能集中维护单位、时点、主键和安全不变量，并降低供应商耦合。
class DailyFundsStandardDataProvider(StandardDatasetProvider):
    """把单个七类来源接入统一 StandardDataService。"""

    # 函数__init__：执行__init__对应的业务处理。
    # - 输入：service:DolphinDBDailyFundsCanonicalService、dataset_id:str、project_root:str | Path；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型None；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    def __init__(
        self,
        service: DolphinDBDailyFundsCanonicalService,
        dataset_id: str,
        *,
        project_root: str | Path,
    ) -> None:
        # 条件门禁：判断`dataset_id not in REQUIRED_DATASETS`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if dataset_id not in REQUIRED_DATASETS:
            # 错误阻断：抛出`DataContractError(f'不支持七类来源：{dataset_id}')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
            raise DataContractError(f"不支持七类来源：{dataset_id}")
        # 状态计算：把`service`的结果保存到`self.service`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        self.service = service
        # 状态计算：把`dataset_id`的结果保存到`self.dataset_id`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        self.dataset_id = dataset_id
        # 状态计算：把`Path(project_root).resolve()`的结果保存到`self.project_root`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        self.project_root = Path(project_root).resolve()
        # 状态计算：把`_load_registry(self.project_root)`的结果保存到`self.registry`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        self.registry = _load_registry(self.project_root)
        # 异常边界：尝试执行可能失败的解析、查询、文件或类型转换步骤，并由后续处理保留错误证据。
        # - 数据变化：正常路径产生业务结果；异常路径不得静默伪造数据，应抛出、记录或隔离。
        # - 为什么这样写：把外部环境故障与业务合同失败分开，便于重试、回滚和准确验收。
        try:
            # 状态计算：把`dict(self.registry['providers'][dataset_id])`的结果保存到`self.registration`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            self.registration = dict(
                self.registry["providers"][dataset_id]
            )
        except KeyError as exc:
            # 错误阻断：抛出`DataContractError(f'Provider注册表缺少来源：{dataset_id}')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
            raise DataContractError(
                f"Provider注册表缺少来源：{dataset_id}"
            ) from exc
        # 状态计算：把`service.dataset_profile(dataset_id)`的结果保存到`self.profile`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        self.profile = service.dataset_profile(dataset_id)
        # 状态计算：把`str(self.registration['canonical_object'])`的结果保存到`self.canonical_object`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        self.canonical_object = str(
            self.registration["canonical_object"]
        )
        # 状态计算：把`str(self.profile['canonical_object'])`的结果保存到`profile_object`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        profile_object = str(self.profile["canonical_object"])
        # 条件门禁：判断`self.canonical_object != profile_object`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if self.canonical_object != profile_object:
            # 错误阻断：抛出`DataContractError(f'Provider对象与Canonical服务不一致：{dataset_id}/{self.canonical_object}/{profile_object}')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
            raise DataContractError(
                "Provider对象与Canonical服务不一致："
                f"{dataset_id}/{self.canonical_object}/{profile_object}"
            )

    # 函数descriptor：执行descriptor对应的业务处理。
    # - 输入：无外部业务参数；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型ProviderDescriptor；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    @property
    def descriptor(self) -> ProviderDescriptor:
        # 结果返回：把`ProviderDescriptor(provider_id=str(self.registration['provider_id']), dataset_id=self.dataset_id, supported_objects=(se…`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return ProviderDescriptor(
            provider_id=str(self.registration["provider_id"]),
            dataset_id=self.dataset_id,
            supported_objects=(self.canonical_object,),
            coverage_version=self.service.coverage_version,
            mapping_version=self.service.mapping_version,
            dictionary_revision=self.service.dictionary_revision,
            selector_mode=str(self.registration["selector_mode"]),
        )

    # 函数available_fields：执行available_fields对应的业务处理。
    # - 输入：无外部业务参数；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型tuple[str, ...]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    def available_fields(self) -> tuple[str, ...]:
        # 结果返回：把`self.service.available_fields(self.dataset_id)`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return self.service.available_fields(self.dataset_id)

    # 函数_selected_fields：执行_selected_fields对应的业务处理。
    # - 输入：request:StandardDataQuery；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型tuple[str, ...]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    def _selected_fields(
        self,
        request: StandardDataQuery,
    ) -> tuple[str, ...]:
        # 状态计算：把`self.available_fields()`的结果保存到`available`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        available = self.available_fields()
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
        unknown = sorted(set(request.fields) - set(available))
        # 条件门禁：判断`unknown`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if unknown:
            # 错误阻断：抛出`DataContractError(f'请求了未登记的七类Canonical字段：{unknown}')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
            raise DataContractError(
                "请求了未登记的七类Canonical字段："
                f"{unknown}"
            )
        # 结果返回：把`request.fields`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return request.fields

    # 函数_selector_ids：执行_selector_ids对应的业务处理。
    # - 输入：request:StandardDataQuery；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型tuple[str, ...]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    def _selector_ids(
        self,
        request: StandardDataQuery,
    ) -> tuple[str, ...]:
        # 状态计算：把`self.descriptor.selector_mode`的结果保存到`mode`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        mode = self.descriptor.selector_mode
        # 条件门禁：判断`mode == INSTRUMENT_SELECTOR_MODE`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if mode == INSTRUMENT_SELECTOR_MODE:
            # 结果返回：把`request.instrument_ids`交给调用方并结束当前函数。
            # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
            # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
            return request.instrument_ids
        # 条件门禁：判断`mode == ENTITY_SELECTOR_MODE`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if mode == ENTITY_SELECTOR_MODE:
            # 结果返回：把`request.entity_ids`交给调用方并结束当前函数。
            # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
            # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
            return request.entity_ids
        # 错误阻断：抛出`DataContractError(f'未知Provider选择器：{mode}')`并停止当前正常路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
        # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
        raise DataContractError(f"未知Provider选择器：{mode}")

    # 函数_project_lineage：执行_project_lineage对应的业务处理。
    # - 输入：lineage:tuple[dict[str, Any], ...]、request:StandardDataQuery；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型tuple[dict[str, Any], ...]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    @staticmethod
    def _project_lineage(
        lineage: tuple[dict[str, Any], ...],
        request: StandardDataQuery,
    ) -> tuple[dict[str, Any], ...]:
        # 条件门禁：判断`not request.include_lineage`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if not request.include_lineage:
            # 结果返回：把`()`交给调用方并结束当前函数。
            # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
            # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
            return ()
        # 条件门禁：判断`not request.fields`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if not request.fields:
            # 结果返回：把`tuple(lineage)`交给调用方并结束当前函数。
            # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
            # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
            return tuple(lineage)
        # 结果返回：把`tuple((item for item in lineage if item.get('canonical_field') in request.fields))`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return tuple(
            item
            for item in lineage
            if item.get("canonical_field") in request.fields
        )

    # 函数_usage_gate：执行_usage_gate对应的业务处理。
    # - 输入：request:StandardDataQuery；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型tuple[bool, tuple[str, ...]]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    @staticmethod
    def _usage_gate(
        request: StandardDataQuery,
    ) -> tuple[bool, tuple[str, ...]]:
        # 状态计算：把`['DAILY_FUNDS_EXACT_AVAILABLE_AT_UNPROVEN']`的结果保存到`warnings`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        warnings: list[str] = [
            "DAILY_FUNDS_EXACT_AVAILABLE_AT_UNPROVEN"
        ]
        # 状态计算：把`False`的结果保存到`blocks`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        blocks = False
        # 条件门禁：判断`request.usage in _HISTORICAL_BLOCKED_USAGES`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if request.usage in _HISTORICAL_BLOCKED_USAGES:
            # 状态计算：把`True`的结果保存到`blocks`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            blocks = True
            # 显式调用：执行`warnings.append('DAILY_FUNDS_STRICT_HISTORICAL_USAGE_BLOCKED')`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
            # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
            # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
            warnings.append(
                "DAILY_FUNDS_STRICT_HISTORICAL_USAGE_BLOCKED"
            )
        # 条件门禁：判断`request.usage is StandardDataUsage.MANUAL_DECISION_SUPPORT and request.decision_time is not None and (request.decision_time.date(…`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        elif (
            request.usage
            is StandardDataUsage.MANUAL_DECISION_SUPPORT
            and request.decision_time is not None
            and request.decision_time.date() <= request.end_date
        ):
            # 状态计算：把`True`的结果保存到`blocks`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            blocks = True
            # 显式调用：执行`warnings.append('DAILY_FUNDS_SAME_DAY_DECISION_TIME_UNPROVEN')`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
            # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
            # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
            warnings.append(
                "DAILY_FUNDS_SAME_DAY_DECISION_TIME_UNPROVEN"
            )
        # 结果返回：把`(blocks, tuple(warnings))`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return blocks, tuple(warnings)

    # 函数query：执行query对应的业务处理。
    # - 输入：request:StandardDataQuery；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型StandardQueryResult；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把只读查询或来源发现步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    def query(
        self,
        request: StandardDataQuery,
    ) -> StandardQueryResult:
        # 条件门禁：判断`request.dataset_id != self.dataset_id`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if request.dataset_id != self.dataset_id:
            # 错误阻断：抛出`DataContractError('查询数据集与七类Provider不一致。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
            raise DataContractError(
                "查询数据集与七类Provider不一致。"
            )
        # 条件门禁：判断`request.canonical_object != self.canonical_object`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if request.canonical_object != self.canonical_object:
            # 错误阻断：抛出`DataContractError('查询Canonical对象与七类Provider不一致。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
            raise DataContractError(
                "查询Canonical对象与七类Provider不一致。"
            )

        # 状态计算：把`self._selected_fields(request)`的结果保存到`selected_fields`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        selected_fields = self._selected_fields(request)
        # 状态计算：把`self._selector_ids(request)`的结果保存到`selectors`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        selectors = self._selector_ids(request)
        # 状态计算：把`self.service.read(DailyFundsReadRequest(dataset_id=self.dataset_id, entity_ids=selectors, start_dat…`的结果保存到`batch`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        batch = self.service.read(
            DailyFundsReadRequest(
                dataset_id=self.dataset_id,
                entity_ids=selectors,
                start_date=request.start_date,
                end_date=request.end_date,
                limit_per_entity=request.limit_per_instrument,
            )
        )

        # 状态计算：把`[]`的结果保存到`records`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        records: list[StandardDataRecord] = []
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
            # 状态计算：把`{field_name: source_record.values.get(field_name) for field_name in selected_fields}`的结果保存到`projected_values`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            projected_values = {
                field_name: source_record.values.get(field_name)
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
            # 状态计算：把`self._project_lineage(source_record.lineage, request)`的结果保存到`lineage`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            lineage = self._project_lineage(
                source_record.lineage,
                request,
            )
            # 状态计算：把`len(lineage)`的结果保存到`lineage_item_count`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            lineage_item_count += len(lineage)
            # 显式调用：执行`records.append(StandardDataRecord(canonical_object=source_record.canonical_object, primary_key=dict(source_record.primary_key), values=proj…`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
            # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
            # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
            records.append(
                StandardDataRecord(
                    canonical_object=source_record.canonical_object,
                    primary_key=dict(source_record.primary_key),
                    values=projected_values,
                    source_record_id=source_record.source_record_id,
                    source_extensions=(
                        dict(source_record.source_extensions)
                        if request.include_source_extensions
                        else {}
                    ),
                    quality_flags=quality_flags,
                    lineage=lineage,
                )
            )

        # 状态计算：把`self._usage_gate(request)`的结果保存到`(usage_blocks, usage_warnings)`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        usage_blocks, usage_warnings = self._usage_gate(request)
        # 状态计算：把`tuple(dict.fromkeys([*batch.warnings, *usage_warnings]))`的结果保存到`warnings`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        warnings = tuple(
            dict.fromkeys([*batch.warnings, *usage_warnings])
        )
        # 条件门禁：判断`usage_blocks`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if usage_blocks:
            # 状态计算：把`QualityStatus.FAILED`的结果保存到`status`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            status = QualityStatus.FAILED
            # 状态计算：把`True`的结果保存到`blocks_downstream`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            blocks_downstream = True
        # 条件门禁：判断`warnings or quality_counts`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        elif warnings or quality_counts:
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

        # 状态计算：把`StandardQueryMetadata(dataset_id=batch.dataset_id, canonical_object=batch.canonical_object, provide…`的结果保存到`metadata`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        metadata = StandardQueryMetadata(
            dataset_id=batch.dataset_id,
            canonical_object=batch.canonical_object,
            provider_id=self.descriptor.provider_id,
            coverage_version=batch.coverage_version,
            mapping_version=batch.mapping_version,
            dictionary_revision=batch.dictionary_revision,
            source_row_count=batch.source_row_count,
            result_count=len(records),
            status=status,
            blocks_downstream=blocks_downstream,
            warnings=warnings,
            quality_flag_counts=dict(sorted(quality_counts.items())),
            lineage_item_count=lineage_item_count,
        )
        # 结果返回：把`StandardQueryResult(query=request, metadata=metadata, records=tuple(records))`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return StandardQueryResult(
            query=request,
            metadata=metadata,
            records=tuple(records),
        )


# 函数build_daily_funds_standard_providers：执行build_daily_funds_standard_providers对应的业务处理。
# - 输入：service:DolphinDBDailyFundsCanonicalService、project_root:str | Path；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型tuple[DailyFundsStandardDataProvider, ...]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
# - 为什么这样写：把对象构造、字段映射或标准化转换步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def build_daily_funds_standard_providers(
    service: DolphinDBDailyFundsCanonicalService,
    *,
    project_root: str | Path,
) -> tuple[DailyFundsStandardDataProvider, ...]:
    # 结果返回：把`tuple((DailyFundsStandardDataProvider(service, dataset_id, project_root=project_root) for dataset_id in REQUIRED_DATASE…`交给调用方并结束当前函数。
    # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return tuple(
        DailyFundsStandardDataProvider(
            service,
            dataset_id,
            project_root=project_root,
        )
        for dataset_id in REQUIRED_DATASETS
    )


# 函数register_daily_funds_standard_providers：执行register_daily_funds_standard_providers对应的业务处理。
# - 输入：standard_service:StandardDataService、canonical_service:DolphinDBDailyFundsCanonicalService、project_root:str | Path、replace:bool；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型tuple[ProviderDescriptor, ...]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
# - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def register_daily_funds_standard_providers(
    standard_service: StandardDataService,
    canonical_service: DolphinDBDailyFundsCanonicalService,
    *,
    project_root: str | Path,
    replace: bool = False,
) -> tuple[ProviderDescriptor, ...]:
    # 状态计算：把`build_daily_funds_standard_providers(canonical_service, project_root=project_root)`的结果保存到`providers`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    providers = build_daily_funds_standard_providers(
        canonical_service,
        project_root=project_root,
    )
    # 循环处理：逐项遍历`providers`，把当前元素绑定到`provider`。
    # - 数据变化：每轮只处理一个来源记录、字段、文件或证据项，并显式累计到局部集合或输出对象。
    # - 为什么这样写：逐项处理便于保留行级血缘、隔离单项异常，并控制16GB单机上的峰值内存。
    for provider in providers:
        # 显式调用：执行`standard_service.register_provider(provider, replace=replace)`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
        # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
        # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
        standard_service.register_provider(
            provider,
            replace=replace,
        )
    # 结果返回：把`tuple((provider.descriptor for provider in providers))`交给调用方并结束当前函数。
    # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return tuple(provider.descriptor for provider in providers)
