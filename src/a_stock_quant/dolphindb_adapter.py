# 模块总览：提供DolphinDB来源的通用只读连接、健康检查、受限查询和返回值标准化能力。
# - 输入输出：输入为数据库、表和项目内部生成的只读脚本；输出为Python可消费的行记录或健康状态。
# - 数据与安全：安全边界是拒绝写入语句和无限制读取，使上层服务可以复用同一只读适配器。
# - 运行边界：导入模块和阅读注释不会触发数据库写入；只有显式调用对应函数并满足门禁时才执行I/O。
# - 为什么这样写：先声明职责、单位、时点和副作用边界，读者可以在阅读实现前建立正确的金融与工程语境。
"""DolphinDB 只读数据源适配器。

当前版本只负责：
1. 建立只读连接；
2. 执行健康检查；
3. 按限制行数读取原始表；
4. 执行项目内部生成的安全只读查询；
5. 转换为 RawDataBatch。

本模块不会创建、删除或修改 DolphinDB 数据库和表。
"""

# 依赖导入：加载`from __future__ import annotations`所提供的类型、标准库或项目内能力。
# - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
# - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
from __future__ import annotations

# 依赖导入：加载`import re`所提供的类型、标准库或项目内能力。
# - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
# - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
import re
# 依赖导入：加载`from dataclasses import dataclass`所提供的类型、标准库或项目内能力。
# - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
# - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
from dataclasses import dataclass
# 依赖导入：加载`from typing import Any, Callable, Protocol`所提供的类型、标准库或项目内能力。
# - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
# - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
from typing import Any, Callable, Protocol

# 依赖导入：加载`from .data_contracts import DataContractError, DataQualityResult, DataSourceAdapter, QualityLevel, QualityStatus, RawDataBatch, SourceType`所提供的类型、标准库或项目内能力。
# - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
# - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
from .data_contracts import (
    DataContractError,
    DataQualityResult,
    DataSourceAdapter,
    QualityLevel,
    QualityStatus,
    RawDataBatch,
    SourceType,
)


# 类DolphinDBSessionProtocol：DolphinDB 会话需要提供的最小方法。
# - 结构：继承或实现Protocol；类体约包含0个字段或常量、2个方法。
# - 数据变化：类定义阶段不执行隐式I/O，实例只在构造或显式方法调用时改变受控状态。
# - 实操：调用方通过该类型集中传递配置、记录、服务或结果，避免跨模块使用无约束字典。
# - 为什么这样写：强类型边界能集中维护单位、时点、主键和安全不变量，并降低供应商耦合。
class DolphinDBSessionProtocol(Protocol):
    """DolphinDB 会话需要提供的最小方法。"""

    # 函数connect：连接 DolphinDB。
    # - 输入：host:str、port:int、user_id:str、password:str；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型Any；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    def connect(
        self,
        host: str,
        port: int,
        user_id: str,
        password: str,
    ) -> Any:
        """连接 DolphinDB。"""

    # 函数run：运行 DolphinDB 脚本并返回结果。
    # - 输入：script:str；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型Any；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把任务入口与流程编排步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    def run(self, script: str) -> Any:
        """运行 DolphinDB 脚本并返回结果。"""


# 状态计算：把`Callable[[], DolphinDBSessionProtocol]`的结果保存到`SessionFactory`，供当前逻辑后续校验、转换、累计或返回。
# - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
# - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
SessionFactory = Callable[[], DolphinDBSessionProtocol]


# 类DolphinDBConnectionSettings：DolphinDB 连接参数。
# - 结构：继承或实现object；类体约包含4个字段或常量、1个方法。
# - 数据变化：类定义阶段不执行隐式I/O，实例只在构造或显式方法调用时改变受控状态。
# - 实操：调用方通过该类型集中传递配置、记录、服务或结果，避免跨模块使用无约束字典。
# - 为什么这样写：强类型边界能集中维护单位、时点、主键和安全不变量，并降低供应商耦合。
@dataclass(frozen=True, slots=True)
class DolphinDBConnectionSettings:
    """DolphinDB 连接参数。"""

    # 状态计算：把`无`的结果保存到`host`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    host: str
    # 状态计算：把`无`的结果保存到`port`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    port: int
    # 状态计算：把`无`的结果保存到`username`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    username: str
    # 状态计算：把`无`的结果保存到`password`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    password: str

    # 函数__post_init__：检查连接参数。
    # - 输入：无外部业务参数；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型None；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    def __post_init__(self) -> None:
        """检查连接参数。"""

        # 条件门禁：判断`not self.host.strip()`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if not self.host.strip():
            # 错误阻断：抛出`DataContractError('host 不能为空。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
            raise DataContractError("host 不能为空。")

        # 条件门禁：判断`not isinstance(self.port, int) or not 1 <= self.port <= 65535`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if not isinstance(self.port, int) or not 1 <= self.port <= 65535:
            # 错误阻断：抛出`DataContractError('port 必须是 1 到 65535 之间的整数。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
            raise DataContractError("port 必须是 1 到 65535 之间的整数。")

        # 条件门禁：判断`not self.username.strip()`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if not self.username.strip():
            # 错误阻断：抛出`DataContractError('username 不能为空。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
            raise DataContractError("username 不能为空。")


# 类DolphinDBDataSourceAdapter：DolphinDB 的最小只读适配器。
# - 结构：继承或实现DataSourceAdapter；类体约包含4个字段或常量、9个方法。
# - 数据变化：类定义阶段不执行隐式I/O，实例只在构造或显式方法调用时改变受控状态。
# - 实操：调用方通过该类型集中传递配置、记录、服务或结果，避免跨模块使用无约束字典。
# - 为什么这样写：强类型边界能集中维护单位、时点、主键和安全不变量，并降低供应商耦合。
class DolphinDBDataSourceAdapter(DataSourceAdapter):
    """DolphinDB 的最小只读适配器。"""

    # 状态计算：把`re.compile('^[A-Za-z_][A-Za-z0-9_]*$')`的结果保存到`_TABLE_NAME_PATTERN`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    _TABLE_NAME_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
    # 状态计算：把`re.compile('^dfs://[A-Za-z0-9_.-]+$')`的结果保存到`_DATABASE_URI_PATTERN`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    _DATABASE_URI_PATTERN = re.compile(r"^dfs://[A-Za-z0-9_.-]+$")
    # 状态计算：把`re.compile('^(select|exec)\\b', re.IGNORECASE)`的结果保存到`_READ_ONLY_PREFIX_PATTERN`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    _READ_ONLY_PREFIX_PATTERN = re.compile(
        r"^(select|exec)\b",
        re.IGNORECASE,
    )
    # 状态计算：把`re.compile('\\b(insert|update|delete|drop|create|alter|rename|truncate|grant|revoke)\\b|append!|ups…`的结果保存到`_FORBIDDEN_SCRIPT_PATTERN`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    _FORBIDDEN_SCRIPT_PATTERN = re.compile(
        r"\b(insert|update|delete|drop|create|alter|rename|truncate|"
        r"grant|revoke)\b|append!|upsert!|tableInsert|saveTable|"
        r"loadTextEx|dropDatabase|database\s*\(",
        re.IGNORECASE,
    )

    # 函数__init__：保存连接设置，但不在初始化时立即连接。
    # - 输入：settings:DolphinDBConnectionSettings、session_factory:SessionFactory | None、source_id:str；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型None；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    def __init__(
        self,
        settings: DolphinDBConnectionSettings,
        session_factory: SessionFactory | None = None,
        source_id: str = "dolphindb_primary",
    ) -> None:
        """保存连接设置，但不在初始化时立即连接。"""

        # 显式调用：执行`super().__init__(source_id=source_id, source_type=SourceType.DOLPHINDB)`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
        # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
        # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
        super().__init__(
            source_id=source_id,
            source_type=SourceType.DOLPHINDB,
        )
        # 状态计算：把`settings`的结果保存到`self.settings`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        self.settings = settings
        # 状态计算：把`session_factory or self._default_session_factory`的结果保存到`self._session_factory`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        self._session_factory = session_factory or self._default_session_factory
        # 状态计算：把`None`的结果保存到`self._session`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        self._session: DolphinDBSessionProtocol | None = None

    # 函数_default_session_factory：创建真实 DolphinDB 会话。
    # - 输入：无外部业务参数；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型DolphinDBSessionProtocol；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    @staticmethod
    def _default_session_factory() -> DolphinDBSessionProtocol:
        """创建真实 DolphinDB 会话。"""

        # 异常边界：尝试执行可能失败的解析、查询、文件或类型转换步骤，并由后续处理保留错误证据。
        # - 数据变化：正常路径产生业务结果；异常路径不得静默伪造数据，应抛出、记录或隔离。
        # - 为什么这样写：把外部环境故障与业务合同失败分开，便于重试、回滚和准确验收。
        try:
            # 依赖导入：加载`import dolphindb as ddb`所提供的类型、标准库或项目内能力。
            # - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
            # - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
            import dolphindb as ddb
        except ImportError as exc:
            # 错误阻断：抛出`DataContractError('未安装 dolphindb Python 客户端，无法建立真实连接。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
            raise DataContractError(
                "未安装 dolphindb Python 客户端，无法建立真实连接。"
            ) from exc

        # 结果返回：把`ddb.session()`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return ddb.session()

    # 函数_get_session：按需建立并缓存会话。
    # - 输入：无外部业务参数；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型DolphinDBSessionProtocol；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    def _get_session(self) -> DolphinDBSessionProtocol:
        """按需建立并缓存会话。"""

        # 条件门禁：判断`self._session is None`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if self._session is None:
            # 状态计算：把`self._session_factory()`的结果保存到`session`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            session = self._session_factory()

            # 异常边界：尝试执行可能失败的解析、查询、文件或类型转换步骤，并由后续处理保留错误证据。
            # - 数据变化：正常路径产生业务结果；异常路径不得静默伪造数据，应抛出、记录或隔离。
            # - 为什么这样写：把外部环境故障与业务合同失败分开，便于重试、回滚和准确验收。
            try:
                # 显式调用：执行`session.connect(self.settings.host, self.settings.port, self.settings.username, self.settings.password)`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
                # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
                # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
                session.connect(
                    self.settings.host,
                    self.settings.port,
                    self.settings.username,
                    self.settings.password,
                )
            except Exception as exc:
                # 错误阻断：抛出`DataContractError(f'DolphinDB 连接失败：{exc}')`并停止当前正常路径。
                # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
                # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
                raise DataContractError(
                    f"DolphinDB 连接失败：{exc}"
                ) from exc

            # 状态计算：把`session`的结果保存到`self._session`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            self._session = session

        # 结果返回：把`self._session`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return self._session

    # 函数_validate_database_uri：限制数据库URI格式。
    # - 输入：database_uri:str；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型None；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把合同、数据质量或安全门禁校验步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    @classmethod
    def _validate_database_uri(cls, database_uri: str) -> None:
        """限制数据库URI格式。"""

        # 条件门禁：判断`not cls._DATABASE_URI_PATTERN.fullmatch(database_uri)`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if not cls._DATABASE_URI_PATTERN.fullmatch(database_uri):
            # 错误阻断：抛出`DataContractError('database_uri 必须使用 dfs://数据库名 格式。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
            raise DataContractError(
                "database_uri 必须使用 dfs://数据库名 格式。"
            )

    # 函数_validate_table_name：限制表名只能使用字母、数字和下划线。
    # - 输入：table_name:str；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型None；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把合同、数据质量或安全门禁校验步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    @classmethod
    def _validate_table_name(cls, table_name: str) -> None:
        """限制表名只能使用字母、数字和下划线。"""

        # 条件门禁：判断`not cls._TABLE_NAME_PATTERN.fullmatch(table_name)`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if not cls._TABLE_NAME_PATTERN.fullmatch(table_name):
            # 错误阻断：抛出`DataContractError('source_object_name 不是合法的 DolphinDB 表名。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
            raise DataContractError(
                "source_object_name 不是合法的 DolphinDB 表名。"
            )

    # 函数_normalise_records：把常见 DolphinDB 返回值转换为字段列表和字典记录。
    # - 输入：result:Any；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型tuple[list[str], list[dict[str, Any]]]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    @staticmethod
    def _normalise_records(result: Any) -> tuple[list[str], list[dict[str, Any]]]:
        """把常见 DolphinDB 返回值转换为字段列表和字典记录。"""

        # 条件门禁：判断`result is None`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if result is None:
            # 结果返回：把`([], [])`交给调用方并结束当前函数。
            # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
            # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
            return [], []

        # 条件门禁：判断`isinstance(result, list)`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if isinstance(result, list):
            # 条件门禁：判断`any((not isinstance(item, dict) for item in result))`，条件成立时进入对应的数据、安全或异常处理分支。
            # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
            # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
            if any(not isinstance(item, dict) for item in result):
                # 错误阻断：抛出`DataContractError('DolphinDB 返回的列表中存在非字典记录。')`并停止当前正常路径。
                # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
                # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
                raise DataContractError(
                    "DolphinDB 返回的列表中存在非字典记录。"
                )

            # 状态计算：把`list(result[0].keys()) if result else []`的结果保存到`fields`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            fields = list(result[0].keys()) if result else []
            # 结果返回：把`(fields, result)`交给调用方并结束当前函数。
            # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
            # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
            return fields, result

        # 状态计算：把`getattr(result, 'to_dict', None)`的结果保存到`to_dict`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        to_dict = getattr(result, "to_dict", None)
        # 状态计算：把`getattr(result, 'columns', None)`的结果保存到`columns`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        columns = getattr(result, "columns", None)

        # 条件门禁：判断`callable(to_dict) and columns is not None`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if callable(to_dict) and columns is not None:
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
            if any(not isinstance(item, dict) for item in records):
                # 错误阻断：抛出`DataContractError('DolphinDB 表格结果无法转换为字典记录。')`并停止当前正常路径。
                # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
                # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
                raise DataContractError(
                    "DolphinDB 表格结果无法转换为字典记录。"
                )

            # 结果返回：把`([str(column) for column in columns], list(records))`交给调用方并结束当前函数。
            # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
            # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
            return [str(column) for column in columns], list(records)

        # 错误阻断：抛出`DataContractError('暂不支持当前 DolphinDB 返回值类型。')`并停止当前正常路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
        # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
        raise DataContractError(
            "暂不支持当前 DolphinDB 返回值类型。"
        )

    # 函数health_check：通过执行 1 + 1 检查连接和基本执行能力。
    # - 输入：无外部业务参数；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型DataQualityResult；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把合同、数据质量或安全门禁校验步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    def health_check(self) -> DataQualityResult:
        """通过执行 1 + 1 检查连接和基本执行能力。"""

        # 异常边界：尝试执行可能失败的解析、查询、文件或类型转换步骤，并由后续处理保留错误证据。
        # - 数据变化：正常路径产生业务结果；异常路径不得静默伪造数据，应抛出、记录或隔离。
        # - 为什么这样写：把外部环境故障与业务合同失败分开，便于重试、回滚和准确验收。
        try:
            # 状态计算：把`self._get_session().run('1 + 1')`的结果保存到`result`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            result = self._get_session().run("1 + 1")
            # 状态计算：把`result == 2`的结果保存到`passed`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            passed = result == 2
        except Exception as exc:
            # 结果返回：把`DataQualityResult(check_name='DolphinDB连接健康检查', level=QualityLevel.CRITICAL, status=QualityStatus.FAILED, checked_row_c…`交给调用方并结束当前函数。
            # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
            # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
            return DataQualityResult(
                check_name="DolphinDB连接健康检查",
                level=QualityLevel.CRITICAL,
                status=QualityStatus.FAILED,
                checked_row_count=1,
                failed_row_count=1,
                blocking=True,
                description=f"健康检查执行失败：{exc}",
            )

        # 结果返回：把`DataQualityResult(check_name='DolphinDB连接健康检查', level=QualityLevel.INFO if passed else QualityLevel.CRITICAL, status=Qu…`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return DataQualityResult(
            check_name="DolphinDB连接健康检查",
            level=QualityLevel.INFO if passed else QualityLevel.CRITICAL,
            status=QualityStatus.PASSED if passed else QualityStatus.FAILED,
            checked_row_count=1,
            failed_row_count=0 if passed else 1,
            blocking=not passed,
            description=(
                "DolphinDB连接和脚本执行正常。"
                if passed
                else f"健康检查返回异常结果：{result!r}"
            ),
        )

    # 函数run_readonly_query：执行经过安全检查的只读 select/exec 查询。
    # - 输入：script:str；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型Any；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把只读查询或来源发现步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    def run_readonly_query(self, script: str) -> Any:
        """执行经过安全检查的只读 select/exec 查询。"""

        # 条件门禁：判断`not isinstance(script, str) or not script.strip()`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if not isinstance(script, str) or not script.strip():
            # 错误阻断：抛出`DataContractError('只读查询脚本不能为空。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
            raise DataContractError("只读查询脚本不能为空。")

        # 状态计算：把`' '.join(script.split())`的结果保存到`normalized`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        normalized = " ".join(script.split())

        # 条件门禁：判断`';' in normalized`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if ";" in normalized:
            # 错误阻断：抛出`DataContractError('只读查询不允许包含分号。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
            raise DataContractError("只读查询不允许包含分号。")

        # 条件门禁：判断`re.search('(^|\\s)//', normalized) or '/*' in normalized`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if re.search(r"(^|\s)//", normalized) or "/*" in normalized:
            # 错误阻断：抛出`DataContractError('只读查询不允许包含注释。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
            raise DataContractError("只读查询不允许包含注释。")

        # 条件门禁：判断`not self._READ_ONLY_PREFIX_PATTERN.match(normalized)`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if not self._READ_ONLY_PREFIX_PATTERN.match(normalized):
            # 错误阻断：抛出`DataContractError('只读查询只能以 select 或 exec 开头。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
            raise DataContractError(
                "只读查询只能以 select 或 exec 开头。"
            )

        # 条件门禁：判断`self._FORBIDDEN_SCRIPT_PATTERN.search(normalized)`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if self._FORBIDDEN_SCRIPT_PATTERN.search(normalized):
            # 错误阻断：抛出`DataContractError('只读查询中包含被禁止的写入或结构变更关键字。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
            raise DataContractError(
                "只读查询中包含被禁止的写入或结构变更关键字。"
            )

        # 异常边界：尝试执行可能失败的解析、查询、文件或类型转换步骤，并由后续处理保留错误证据。
        # - 数据变化：正常路径产生业务结果；异常路径不得静默伪造数据，应抛出、记录或隔离。
        # - 为什么这样写：把外部环境故障与业务合同失败分开，便于重试、回滚和准确验收。
        try:
            # 结果返回：把`self._get_session().run(script)`交给调用方并结束当前函数。
            # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
            # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
            return self._get_session().run(script)
        except Exception as exc:
            # 错误阻断：抛出`DataContractError(f'DolphinDB只读查询失败：{exc}')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
            raise DataContractError(
                f"DolphinDB只读查询失败：{exc}"
            ) from exc

    # 函数read_raw：从指定 DFS 表读取有限行原始数据。
    # - 输入：source_object_name:str、kwargs:Any；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型RawDataBatch；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把只读查询或来源发现步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    def read_raw(
        self,
        source_object_name: str,
        **kwargs: Any,
    ) -> RawDataBatch:
        """从指定 DFS 表读取有限行原始数据。"""

        # 状态计算：把`kwargs.get('database_uri')`的结果保存到`database_uri`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        database_uri = kwargs.get("database_uri")
        # 状态计算：把`kwargs.get('limit', 100)`的结果保存到`limit`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        limit = kwargs.get("limit", 100)

        # 条件门禁：判断`not isinstance(database_uri, str)`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if not isinstance(database_uri, str):
            # 错误阻断：抛出`DataContractError('read_raw 必须提供字符串 database_uri。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
            raise DataContractError(
                "read_raw 必须提供字符串 database_uri。"
            )

        # 条件门禁：判断`not isinstance(limit, int) or not 1 <= limit <= 100000`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if not isinstance(limit, int) or not 1 <= limit <= 100_000:
            # 错误阻断：抛出`DataContractError('limit 必须是 1 到 100000 之间的整数。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
            raise DataContractError(
                "limit 必须是 1 到 100000 之间的整数。"
            )

        # 显式调用：执行`self._validate_database_uri(database_uri)`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
        # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
        # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
        self._validate_database_uri(database_uri)
        # 显式调用：执行`self._validate_table_name(source_object_name)`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
        # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
        # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
        self._validate_table_name(source_object_name)

        # 状态计算：把`f'select top {limit} * from loadTable("{database_uri}", `{source_object_name})'`的结果保存到`script`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        script = (
            f'select top {limit} * '
            f'from loadTable("{database_uri}", `{source_object_name})'
        )

        # 异常边界：尝试执行可能失败的解析、查询、文件或类型转换步骤，并由后续处理保留错误证据。
        # - 数据变化：正常路径产生业务结果；异常路径不得静默伪造数据，应抛出、记录或隔离。
        # - 为什么这样写：把外部环境故障与业务合同失败分开，便于重试、回滚和准确验收。
        try:
            # 状态计算：把`self._get_session().run(script)`的结果保存到`result`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            result = self._get_session().run(script)
        except Exception as exc:
            # 错误阻断：抛出`DataContractError(f'DolphinDB 读取失败：{exc}')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
            raise DataContractError(
                f"DolphinDB 读取失败：{exc}"
            ) from exc

        # 状态计算：把`self._normalise_records(result)`的结果保存到`(raw_fields, records)`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        raw_fields, records = self._normalise_records(result)

        # 结果返回：把`RawDataBatch(source_id=self.source_id, source_type=self.source_type, source_object_name=source_object_name, raw_fields=…`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return RawDataBatch(
            source_id=self.source_id,
            source_type=self.source_type,
            source_object_name=source_object_name,
            raw_fields=raw_fields,
            records=records,
            source_location=f"{database_uri}/{source_object_name}",
            notes=(
                f"只读抽样查询，limit={limit}；"
                "未推断复权、单位或日期语义。"
            ),
        )
