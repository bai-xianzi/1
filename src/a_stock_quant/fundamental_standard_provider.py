# 模块总览：把基本面标准化服务接入统一StandardDataService。
# - 输入输出：输入为基本面标准查询；输出为Canonical快照、质量、血缘和用途限制元数据。
# - 数据与安全：Provider必须传播公告时点与缺失值警告，不能把当前快照错误用于历史时点。
# - 运行边界：导入模块和阅读注释不会触发数据库写入；只有显式调用对应函数并满足门禁时才执行I/O。
# - 为什么这样写：先声明职责、单位、时点和副作用边界，读者可以在阅读实现前建立正确的金融与工程语境。
"""基本面标准数据Provider与用途级时点门禁。"""

# 依赖导入：加载`from __future__ import annotations`所提供的类型、标准库或项目内能力。
# - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
# - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
from __future__ import annotations

# 依赖导入：加载`from collections import Counter`所提供的类型、标准库或项目内能力。
# - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
# - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
from collections import Counter
# 依赖导入：加载`from datetime import datetime`所提供的类型、标准库或项目内能力。
# - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
# - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
from datetime import datetime
# 依赖导入：加载`from typing import Any`所提供的类型、标准库或项目内能力。
# - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
# - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
from typing import Any

# 依赖导入：加载`from .data_contracts import DataContractError, QualityStatus`所提供的类型、标准库或项目内能力。
# - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
# - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
from .data_contracts import DataContractError, QualityStatus
# 依赖导入：加载`from .dolphindb_fundamental_service import DATASET_ID, DolphinDBFundamentalStandardizedService, FundamentalCanonicalRecord, FundamentalRead…`所提供的类型、标准库或项目内能力。
# - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
# - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
from .dolphindb_fundamental_service import (
    DATASET_ID,
    DolphinDBFundamentalStandardizedService,
    FundamentalCanonicalRecord,
    FundamentalReadRequest,
)
# 依赖导入：加载`from .standard_data_service import ProviderDescriptor, StandardDataQuery, StandardDataRecord, StandardDataUsage, StandardDatasetProvider, S…`所提供的类型、标准库或项目内能力。
# - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
# - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
from .standard_data_service import (
    ProviderDescriptor,
    StandardDataQuery,
    StandardDataRecord,
    StandardDataUsage,
    StandardDatasetProvider,
    StandardQueryMetadata,
    StandardQueryResult,
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

# 该目录必须与schemas/canonical_fields.yaml revision 0.5完全一致。
# 关键常量_FIELDS_BY_OBJECT：集中保存`{'FundamentalSnapshot': ('instrument_id', 'company_id', 'report_period', 'period_type', 'fiscal_yea…`对应的合同值、Schema集合或运行边界。
# - 来源与范围：该值来自当前项目任务、配置、真实数据画像或安全合同；未明确说明时不得外推为行业统一标准。
# - 单位与实例：数值单位由变量名、相邻校验和调用语义共同限定；字符串用于版本、字段、状态或DolphinDB对象标识。
# - 为什么这样写：集中命名固定参数可避免魔法值散落，并让升级、审计和回归测试有稳定锚点。
_FIELDS_BY_OBJECT: dict[str, tuple[str, ...]] = {
    "FundamentalSnapshot": (
        "instrument_id",
        "company_id",
        "report_period",
        "period_type",
        "fiscal_year",
        "fiscal_quarter",
        "announcement_date",
        "statement_type",
        "consolidation_scope",
        "accounting_standard_code",
        "currency_code",
        "revenue_cny",
        "operating_cost_cny",
        "operating_profit_cny",
        "total_profit_cny",
        "net_profit_cny",
        "net_profit_parent_cny",
        "total_assets_cny",
        "total_equity_cny",
        "inventory_cny",
        "accounts_receivable_cny",
        "operating_cash_flow_cny",
        "basic_eps_cny",
        "book_value_per_share_cny",
    ),
    "OwnershipSnapshot": (
        "instrument_id",
        "as_of_date",
        "total_shares",
        "float_shares",
        "shareholder_count",
    ),
    "Instrument": (
        "instrument_id",
        "symbol",
        "exchange_code",
        "market_code",
        "asset_class",
        "security_type",
        "instrument_name_cn",
        "company_id",
        "currency_code",
        "listing_date",
        "trading_status",
        "is_st",
        "is_new_listing",
        "lot_size_shares",
    ),
    "ClassificationMembership": (
        "classification_system",
        "classification_version",
        "classification_type",
        "node_id",
        "node_code",
        "node_name_cn",
        "node_name_en",
        "node_level",
        "parent_node_id",
        "instrument_id",
        "membership_weight_pct",
        "membership_rank",
        "effective_from",
        "effective_to",
        "membership_reason",
    ),
}


# 类FundamentalStandardDataProvider：把基本面标准化服务接入StandardDataService。
# - 结构：继承或实现StandardDatasetProvider；类体约包含1个字段或常量、7个方法。
# - 数据变化：类定义阶段不执行隐式I/O，实例只在构造或显式方法调用时改变受控状态。
# - 实操：调用方通过该类型集中传递配置、记录、服务或结果，避免跨模块使用无约束字典。
# - 为什么这样写：强类型边界能集中维护单位、时点、主键和安全不变量，并降低供应商耦合。
class FundamentalStandardDataProvider(StandardDatasetProvider):
    """把基本面标准化服务接入StandardDataService。"""

    # 状态计算：把`'dolphindb_fundamental_standard_provider'`的结果保存到`provider_id`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    provider_id = "dolphindb_fundamental_standard_provider"

    # 函数__init__：执行__init__对应的业务处理。
    # - 输入：service:DolphinDBFundamentalStandardizedService；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型None；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    def __init__(
        self,
        service: DolphinDBFundamentalStandardizedService,
    ) -> None:
        # 状态计算：把`service`的结果保存到`self.service`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        self.service = service

    # 函数descriptor：执行descriptor对应的业务处理。
    # - 输入：无外部业务参数；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型ProviderDescriptor；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    @property
    def descriptor(self) -> ProviderDescriptor:
        # 状态计算：把`self.service.registration`的结果保存到`registration`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        registration = self.service.registration
        # 结果返回：把`ProviderDescriptor(provider_id=self.provider_id, dataset_id=registration.dataset_id, supported_objects=tuple(sorted(_FI…`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return ProviderDescriptor(
            provider_id=self.provider_id,
            dataset_id=registration.dataset_id,
            supported_objects=tuple(sorted(_FIELDS_BY_OBJECT)),
            coverage_version=registration.coverage_version,
            mapping_version=registration.mapping_version,
            dictionary_revision=registration.dictionary_revision,
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
            # 结果返回：把`_FIELDS_BY_OBJECT[canonical_object]`交给调用方并结束当前函数。
            # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
            # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
            return _FIELDS_BY_OBJECT[canonical_object]
        except KeyError as exc:
            # 错误阻断：抛出`DataContractError(f'基本面Provider不支持标准对象：{canonical_object}')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
            raise DataContractError(
                "基本面Provider不支持标准对象："
                f"{canonical_object}"
            ) from exc

    # 函数_selected_fields：执行_selected_fields对应的业务处理。
    # - 输入：request:StandardDataQuery；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型tuple[str, ...]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    def _selected_fields(
        self,
        request: StandardDataQuery,
    ) -> tuple[str, ...]:
        # 状态计算：把`self.available_fields(request.canonical_object)`的结果保存到`available`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        available = self.available_fields(request.canonical_object)
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
            # 错误阻断：抛出`DataContractError(f'请求了未登记的基本面标准字段：{unknown}')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
            raise DataContractError(
                "请求了未登记的基本面标准字段："
                f"{unknown}"
            )
        # 结果返回：把`request.fields`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return request.fields

    # 函数_record_is_visible：执行_record_is_visible对应的业务处理。
    # - 输入：record:FundamentalCanonicalRecord、request:StandardDataQuery；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型tuple[bool, str | None]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    @staticmethod
    def _record_is_visible(
        record: FundamentalCanonicalRecord,
        request: StandardDataQuery,
    ) -> tuple[bool, str | None]:
        # 内部断言：要求`request.as_of_date is not None`成立，用于暴露开发期不变量破坏。
        # - 数据变化：断言通过时不改变业务数据，失败时中断当前测试或内部流程。
        # - 为什么这样写：把不可接受的内部状态显式化，避免错误结果继续进入报告。
        assert request.as_of_date is not None

        # 条件门禁：判断`record.snapshot_date is not None and record.snapshot_date > request.as_of_date`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if (
            record.snapshot_date is not None
            and record.snapshot_date > request.as_of_date
        ):
            # 结果返回：把`(False, 'SNAPSHOT_AFTER_AS_OF')`交给调用方并结束当前函数。
            # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
            # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
            return False, "SNAPSHOT_AFTER_AS_OF"

        # imported_at是当前唯一可以证明的本地可用时间。缺失时采取安全失败。
        # 条件门禁：判断`record.imported_at is None`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if record.imported_at is None:
            # 结果返回：把`(False, 'AVAILABLE_AT_MISSING')`交给调用方并结束当前函数。
            # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
            # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
            return False, "AVAILABLE_AT_MISSING"

        # 条件门禁：判断`record.imported_at.date() > request.as_of_date`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if record.imported_at.date() > request.as_of_date:
            # 结果返回：把`(False, 'IMPORTED_AFTER_AS_OF')`交给调用方并结束当前函数。
            # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
            # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
            return False, "IMPORTED_AFTER_AS_OF"

        # 条件门禁：判断`request.decision_time is None`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if request.decision_time is None:
            # 日期级研究查询按as_of_date日终解释，并在结果中保留时区警告。
            # 结果返回：把`(True, None)`交给调用方并结束当前函数。
            # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
            # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
            return True, None

        # 状态计算：把`request.decision_time`的结果保存到`decision_time`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        decision_time = request.decision_time
        # 内部断言：要求`isinstance(decision_time, datetime)`成立，用于暴露开发期不变量破坏。
        # - 数据变化：断言通过时不改变业务数据，失败时中断当前测试或内部流程。
        # - 为什么这样写：把不可接受的内部状态显式化，避免错误结果继续进入报告。
        assert isinstance(decision_time, datetime)

        # DolphinDB中的imported_at没有明确时区。为避免伪精确，同日内不能证明
        # imported_at <= decision_time；只有决策日期严格晚于入库日期时才可见。
        # 条件门禁：判断`decision_time.date() <= record.imported_at.date()`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if decision_time.date() <= record.imported_at.date():
            # 结果返回：把`(False, 'SAME_DAY_TIMEZONE_UNPROVEN')`交给调用方并结束当前函数。
            # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
            # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
            return False, "SAME_DAY_TIMEZONE_UNPROVEN"

        # 结果返回：把`(True, None)`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return True, None

    # 函数_project_lineage：执行_project_lineage对应的业务处理。
    # - 输入：record:FundamentalCanonicalRecord、request:StandardDataQuery；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型tuple[dict[str, Any], ...]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    @staticmethod
    def _project_lineage(
        record: FundamentalCanonicalRecord,
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
        # 结果返回：把`tuple((item for item in record.lineage if not request.fields or item.get('canonical_field') in request.fields))`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return tuple(
            item
            for item in record.lineage
            if (
                not request.fields
                or item.get("canonical_field") in request.fields
            )
        )

    # 函数query：执行query对应的业务处理。
    # - 输入：request:StandardDataQuery；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型StandardQueryResult；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把只读查询或来源发现步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    def query(
        self,
        request: StandardDataQuery,
    ) -> StandardQueryResult:
        # 条件门禁：判断`request.dataset_id != DATASET_ID`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if request.dataset_id != DATASET_ID:
            # 错误阻断：抛出`DataContractError('查询数据集与基本面Provider不一致。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
            raise DataContractError(
                "查询数据集与基本面Provider不一致。"
            )

        # 状态计算：把`self._selected_fields(request)`的结果保存到`selected_fields`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        selected_fields = self._selected_fields(request)
        # 内部断言：要求`request.as_of_date is not None`成立，用于暴露开发期不变量破坏。
        # - 数据变化：断言通过时不改变业务数据，失败时中断当前测试或内部流程。
        # - 为什么这样写：把不可接受的内部状态显式化，避免错误结果继续进入报告。
        assert request.as_of_date is not None

        # 状态计算：把`request.as_of_date < self.service.coverage_date`的结果保存到`pre_coverage`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        pre_coverage = request.as_of_date < self.service.coverage_date
        # 状态计算：把`self.service.read(FundamentalReadRequest(instrument_ids=request.instrument_ids, start_date=request.…`的结果保存到`batch`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        batch = self.service.read(
            FundamentalReadRequest(
                instrument_ids=request.instrument_ids,
                start_date=request.start_date,
                end_date=request.end_date,
                limit_per_instrument=request.limit_per_instrument,
            )
        )

        # 状态计算：把`list(batch.warnings)`的结果保存到`warnings`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        warnings = list(batch.warnings)
        # 状态计算：把`Counter()`的结果保存到`quality_counts`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        quality_counts: Counter[str] = Counter()
        # 状态计算：把`Counter()`的结果保存到`visibility_counts`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        visibility_counts: Counter[str] = Counter()
        # 状态计算：把`0`的结果保存到`lineage_item_count`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        lineage_item_count = 0
        # 状态计算：把`[]`的结果保存到`result_records`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        result_records: list[StandardDataRecord] = []
        # 状态计算：把`0`的结果保存到`matching_object_count`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        matching_object_count = 0

        # 循环处理：逐项遍历`batch.records`，把当前元素绑定到`record`。
        # - 数据变化：每轮只处理一个来源记录、字段、文件或证据项，并显式累计到局部集合或输出对象。
        # - 为什么这样写：逐项处理便于保留行级血缘、隔离单项异常，并控制16GB单机上的峰值内存。
        for record in batch.records:
            # 条件门禁：判断`record.canonical_object != request.canonical_object`，条件成立时进入对应的数据、安全或异常处理分支。
            # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
            # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
            if record.canonical_object != request.canonical_object:
                # 控制流：跳过本轮剩余步骤，使循环或占位分支按既定合同继续。
                # - 数据变化：本语句不直接改变业务记录，只调整当前执行路径。
                # - 为什么这样写：显式控制流比隐式嵌套更容易检查边界和异常处理。
                continue

            # 状态计算：把`1`的结果保存到`matching_object_count`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            matching_object_count += 1
            # 状态计算：把`self._record_is_visible(record, request)`的结果保存到`(visible, reason)`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            visible, reason = self._record_is_visible(record, request)
            # 条件门禁：判断`not visible`，条件成立时进入对应的数据、安全或异常处理分支。
            # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
            # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
            if not visible:
                # 状态计算：把`1`的结果保存到`visibility_counts[reason or 'UNKNOWN']`，供当前逻辑后续校验、转换、累计或返回。
                # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
                # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
                visibility_counts[reason or "UNKNOWN"] += 1
                # 控制流：跳过本轮剩余步骤，使循环或占位分支按既定合同继续。
                # - 数据变化：本语句不直接改变业务记录，只调整当前执行路径。
                # - 为什么这样写：显式控制流比隐式嵌套更容易检查边界和异常处理。
                continue

            # 状态计算：把`{field_name: record.values.get(field_name) for field_name in selected_fields}`的结果保存到`values`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            values = {
                field_name: record.values.get(field_name)
                for field_name in selected_fields
            }
            # 状态计算：把`tuple(record.quality_flags if request.include_quality_flags else ())`的结果保存到`quality_flags`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            quality_flags = tuple(
                record.quality_flags
                if request.include_quality_flags
                else ()
            )
            # 显式调用：执行`quality_counts.update(quality_flags)`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
            # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
            # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
            quality_counts.update(quality_flags)

            # 状态计算：把`self._project_lineage(record, request)`的结果保存到`lineage`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            lineage = self._project_lineage(record, request)
            # 状态计算：把`len(lineage)`的结果保存到`lineage_item_count`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            lineage_item_count += len(lineage)

            # 显式调用：执行`result_records.append(StandardDataRecord(canonical_object=record.canonical_object, primary_key=dict(record.primary_key), values=values, sou…`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
            # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
            # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
            result_records.append(
                StandardDataRecord(
                    canonical_object=record.canonical_object,
                    primary_key=dict(record.primary_key),
                    values=values,
                    source_record_id=record.source_record_id,
                    source_extensions=(
                        dict(record.source_extensions)
                        if request.include_source_extensions
                        else {}
                    ),
                    quality_flags=quality_flags,
                    lineage=lineage,
                )
            )

        # 条件门禁：判断`pre_coverage`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if pre_coverage:
            # 显式调用：执行`warnings.append('查询时点早于当前基本面快照覆盖日2026-06-19，不得用当前快照回填历史。')`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
            # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
            # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
            warnings.append(
                "查询时点早于当前基本面快照覆盖日2026-06-19，"
                "不得用当前快照回填历史。"
            )

        # 循环处理：逐项遍历`sorted(visibility_counts.items())`，把当前元素绑定到`(reason, count)`。
        # - 数据变化：每轮只处理一个来源记录、字段、文件或证据项，并显式累计到局部集合或输出对象。
        # - 为什么这样写：逐项处理便于保留行级血缘、隔离单项异常，并控制16GB单机上的峰值内存。
        for reason, count in sorted(visibility_counts.items()):
            # 显式调用：执行`warnings.append(f'基本面时点门禁过滤{count}条记录：{reason}。')`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
            # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
            # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
            warnings.append(
                f"基本面时点门禁过滤{count}条记录：{reason}。"
            )

        # 状态计算：把`request.usage in _HISTORICAL_BLOCKED_USAGES`的结果保存到`historical_blocked`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        historical_blocked = request.usage in _HISTORICAL_BLOCKED_USAGES
        # 条件门禁：判断`historical_blocked`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if historical_blocked:
            # 显式调用：执行`warnings.append('当前基本面数据只有2026-06-19观察快照，update_date不能证明是正式公告日期；严格历史回测和历史模型训练被阻断。')`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
            # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
            # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
            warnings.append(
                "当前基本面数据只有2026-06-19观察快照，"
                "update_date不能证明是正式公告日期；"
                "严格历史回测和历史模型训练被阻断。"
            )

        # 条件门禁：判断`request.usage in {StandardDataUsage.CURRENT_SNAPSHOT_RESEARCH, StandardDataUsage.MANUAL_DECISION_SUPPORT}`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if request.usage in {
            StandardDataUsage.CURRENT_SNAPSHOT_RESEARCH,
            StandardDataUsage.MANUAL_DECISION_SUPPORT,
        }:
            # 显式调用：执行`warnings.append('当前快照只允许研究或快照之后的人工辅助决策；金额与股本单位为经验确认，利润、权益、公告日、公司身份及分类版本仍保留WARNING。')`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
            # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
            # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
            warnings.append(
                "当前快照只允许研究或快照之后的人工辅助决策；"
                "金额与股本单位为经验确认，利润、权益、公告日、"
                "公司身份及分类版本仍保留WARNING。"
            )

        # 状态计算：把`batch.source_row_count > 0 and matching_object_count == 0`的结果保存到`missing_requested_object`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        missing_requested_object = (
            batch.source_row_count > 0
            and matching_object_count == 0
        )
        # 条件门禁：判断`missing_requested_object`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if missing_requested_object:
            # 显式调用：执行`warnings.append('来源记录存在，但没有生成请求的标准对象；空财务载荷不会被补零。')`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
            # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
            # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
            warnings.append(
                "来源记录存在，但没有生成请求的标准对象；"
                "空财务载荷不会被补零。"
            )

        # 状态计算：把`matching_object_count > 0 and (not result_records) and bool(visibility_counts)`的结果保存到`all_matching_invisible`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        all_matching_invisible = (
            matching_object_count > 0
            and not result_records
            and bool(visibility_counts)
        )

        # 状态计算：把`any((pre_coverage, historical_blocked, missing_requested_object, all_matching_invisible))`的结果保存到`blocks_downstream`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        blocks_downstream = any(
            (
                pre_coverage,
                historical_blocked,
                missing_requested_object,
                all_matching_invisible,
            )
        )

        # 条件门禁：判断`blocks_downstream`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if blocks_downstream:
            # 状态计算：把`QualityStatus.FAILED`的结果保存到`status`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            status = QualityStatus.FAILED
        # 条件门禁：判断`warnings or quality_counts`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        elif warnings or quality_counts:
            # 状态计算：把`QualityStatus.WARNING`的结果保存到`status`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            status = QualityStatus.WARNING
        else:
            # 状态计算：把`QualityStatus.PASSED`的结果保存到`status`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            status = QualityStatus.PASSED

        # 状态计算：把`Counter(quality_counts)`的结果保存到`combined_quality_counts`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        combined_quality_counts = Counter(quality_counts)
        # 显式调用：执行`combined_quality_counts.update({f'VISIBILITY_{key}': value for key, value in visibility_counts.items()})`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
        # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
        # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
        combined_quality_counts.update(
            {
                f"VISIBILITY_{key}": value
                for key, value in visibility_counts.items()
            }
        )

        # 状态计算：把`StandardQueryMetadata(dataset_id=batch.dataset_id, canonical_object=request.canonical_object, provi…`的结果保存到`metadata`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        metadata = StandardQueryMetadata(
            dataset_id=batch.dataset_id,
            canonical_object=request.canonical_object,
            provider_id=self.provider_id,
            coverage_version=batch.coverage_version,
            mapping_version=batch.mapping_version,
            dictionary_revision=batch.dictionary_revision,
            source_row_count=batch.source_row_count,
            result_count=len(result_records),
            status=status,
            blocks_downstream=blocks_downstream,
            warnings=tuple(dict.fromkeys(warnings)),
            quality_flag_counts=dict(
                sorted(combined_quality_counts.items())
            ),
            lineage_item_count=lineage_item_count,
        )

        # 结果返回：把`StandardQueryResult(query=request, metadata=metadata, records=tuple(result_records))`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return StandardQueryResult(
            query=request,
            metadata=metadata,
            records=tuple(result_records),
        )
