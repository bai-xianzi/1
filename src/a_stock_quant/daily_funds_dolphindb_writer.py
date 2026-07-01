# 模块总览：负责七类日线行情、竞价与资金流Raw层的建表计划、幂等导入和隔离日志写入。
# - 输入输出：输入为通过预导入门禁的文件批次；输出为DolphinDB Raw表记录、批次日志和隔离记录。
# - 数据与安全：写入能力只在显式create或import调用中生效；本次注释迁移不会连接或写入数据库。
# - 运行边界：导入模块和阅读注释不会触发数据库写入；只有显式调用对应函数并满足门禁时才执行I/O。
# - 为什么这样写：先声明职责、单位、时点和副作用边界，读者可以在阅读实现前建立正确的金融与工程语境。
"""TASK_016B 七类日线资金 DolphinDB Raw 层建库与导入。

安全边界：
1. contract 模式只校验本地合同和DDL计划；
2. probe 模式只读探测 DolphinDB，不创建或修改对象；
3. create 模式只创建缺失数据库/表，不删除或覆盖已有对象；
4. import 模式重新运行 TASK_016A 预导入门禁后逐文件写入；
5. 覆盖不足的文件只写隔离日志，不进入主Raw表；
6. 主表以 dataset_id + source_file_sha256 + source_row_number
   作为TSDB幂等排序键，keepDuplicates=LAST；
7. 不把source_file_mtime伪装成available_at。
"""
# 依赖导入：加载`from __future__ import annotations`所提供的类型、标准库或项目内能力。
# - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
# - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
from __future__ import annotations

# 依赖导入：加载`import csv`所提供的类型、标准库或项目内能力。
# - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
# - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
import csv
# 依赖导入：加载`import getpass`所提供的类型、标准库或项目内能力。
# - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
# - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
import getpass
# 依赖导入：加载`import importlib`所提供的类型、标准库或项目内能力。
# - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
# - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
import importlib
# 依赖导入：加载`import json`所提供的类型、标准库或项目内能力。
# - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
# - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
import json
# 依赖导入：加载`import os`所提供的类型、标准库或项目内能力。
# - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
# - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
import os
# 依赖导入：加载`import re`所提供的类型、标准库或项目内能力。
# - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
# - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
import re
# 依赖导入：加载`from collections import Counter`所提供的类型、标准库或项目内能力。
# - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
# - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
from collections import Counter
# 依赖导入：加载`from collections.abc import Callable, Iterable, Sequence`所提供的类型、标准库或项目内能力。
# - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
# - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
from collections.abc import Callable, Iterable, Sequence
# 依赖导入：加载`from dataclasses import dataclass`所提供的类型、标准库或项目内能力。
# - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
# - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
from dataclasses import dataclass
# 依赖导入：加载`from datetime import datetime, timezone`所提供的类型、标准库或项目内能力。
# - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
# - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
from datetime import datetime, timezone
# 依赖导入：加载`from pathlib import Path`所提供的类型、标准库或项目内能力。
# - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
# - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
from pathlib import Path
# 依赖导入：加载`from typing import Any, Protocol`所提供的类型、标准库或项目内能力。
# - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
# - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
from typing import Any, Protocol

# 依赖导入：加载`import numpy as np`所提供的类型、标准库或项目内能力。
# - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
# - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
import numpy as np
# 依赖导入：加载`import pandas as pd`所提供的类型、标准库或项目内能力。
# - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
# - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
import pandas as pd

# 依赖导入：加载`from .daily_funds_ingest import DailyFundsContract, DailyFundsIngestError, DatasetSpec, _trim_trailing_delimiter_cell, deduplicate_headers,…`所提供的类型、标准库或项目内能力。
# - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
# - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
from .daily_funds_ingest import (
    DailyFundsContract,
    DailyFundsIngestError,
    DatasetSpec,
    _trim_trailing_delimiter_cell,
    deduplicate_headers,
    discover_snapshot_directories,
    file_sha256,
    header_fingerprint,
    iter_source_rows,
    load_daily_funds_contract,
    normalize_row,
    parse_snapshot_date_from_path,
    run_daily_funds_preflight,
    strip_cell,
    validate_daily_funds_contract,
)


# 关键常量DATABASE_URI：集中保存`'dfs://A_STOCK_DAILY_FUNDS_DB'`对应的合同值、Schema集合或运行边界。
# - 来源与范围：该值来自当前项目任务、配置、真实数据画像或安全合同；未明确说明时不得外推为行业统一标准。
# - 单位与实例：数值单位由变量名、相邻校验和调用语义共同限定；字符串用于版本、字段、状态或DolphinDB对象标识。
# - 为什么这样写：集中命名固定参数可避免魔法值散落，并让升级、审计和回归测试有稳定锚点。
DATABASE_URI = "dfs://A_STOCK_DAILY_FUNDS_DB"
# 关键常量PARTITION_START_MONTH：集中保存`'1990.01M'`对应的合同值、Schema集合或运行边界。
# - 来源与范围：该值来自当前项目任务、配置、真实数据画像或安全合同；未明确说明时不得外推为行业统一标准。
# - 单位与实例：数值单位由变量名、相邻校验和调用语义共同限定；字符串用于版本、字段、状态或DolphinDB对象标识。
# - 为什么这样写：集中命名固定参数可避免魔法值散落，并让升级、审计和回归测试有稳定锚点。
PARTITION_START_MONTH = "1990.01M"
# 关键常量PARTITION_END_MONTH：集中保存`'2100.12M'`对应的合同值、Schema集合或运行边界。
# - 来源与范围：该值来自当前项目任务、配置、真实数据画像或安全合同；未明确说明时不得外推为行业统一标准。
# - 单位与实例：数值单位由变量名、相邻校验和调用语义共同限定；字符串用于版本、字段、状态或DolphinDB对象标识。
# - 为什么这样写：集中命名固定参数可避免魔法值散落，并让升级、审计和回归测试有稳定锚点。
PARTITION_END_MONTH = "2100.12M"

# 关键常量TABLE_NAMES：集中保存`{'security_snapshot': 'security_market_snapshot_raw', 'classification_snapshot': 'classification_ma…`对应的合同值、Schema集合或运行边界。
# - 来源与范围：该值来自当前项目任务、配置、真实数据画像或安全合同；未明确说明时不得外推为行业统一标准。
# - 单位与实例：数值单位由变量名、相邻校验和调用语义共同限定；字符串用于版本、字段、状态或DolphinDB对象标识。
# - 为什么这样写：集中命名固定参数可避免魔法值散落，并让升级、审计和回归测试有稳定锚点。
TABLE_NAMES = {
    "security_snapshot": "security_market_snapshot_raw",
    "classification_snapshot": "classification_market_snapshot_raw",
    "money_flow_snapshot": "money_flow_snapshot_raw",
    "ingest_batch": "ingest_batch_log",
    "ingest_file": "ingest_file_log",
    "quarantine_file": "quarantine_file_log",
}

# 关键常量FAMILY_TO_TABLE：集中保存`{'security_snapshot': TABLE_NAMES['security_snapshot'], 'classification_snapshot': TABLE_NAMES['cla…`对应的合同值、Schema集合或运行边界。
# - 来源与范围：该值来自当前项目任务、配置、真实数据画像或安全合同；未明确说明时不得外推为行业统一标准。
# - 单位与实例：数值单位由变量名、相邻校验和调用语义共同限定；字符串用于版本、字段、状态或DolphinDB对象标识。
# - 为什么这样写：集中命名固定参数可避免魔法值散落，并让升级、审计和回归测试有稳定锚点。
FAMILY_TO_TABLE = {
    "security_snapshot": TABLE_NAMES["security_snapshot"],
    "classification_snapshot": TABLE_NAMES["classification_snapshot"],
    "money_flow_snapshot": TABLE_NAMES["money_flow_snapshot"],
}

# 关键常量IDENTIFIER_RE：集中保存`re.compile('^[A-Za-z_][A-Za-z0-9_]*$')`对应的合同值、Schema集合或运行边界。
# - 来源与范围：该值来自当前项目任务、配置、真实数据画像或安全合同；未明确说明时不得外推为行业统一标准。
# - 单位与实例：数值单位由变量名、相邻校验和调用语义共同限定；字符串用于版本、字段、状态或DolphinDB对象标识。
# - 为什么这样写：集中命名固定参数可避免魔法值散落，并让升级、审计和回归测试有稳定锚点。
IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
# 关键常量SYMBOL_LITERAL_RE：集中保存`re.compile('^[A-Za-z0-9_.:-]+$')`对应的合同值、Schema集合或运行边界。
# - 来源与范围：该值来自当前项目任务、配置、真实数据画像或安全合同；未明确说明时不得外推为行业统一标准。
# - 单位与实例：数值单位由变量名、相邻校验和调用语义共同限定；字符串用于版本、字段、状态或DolphinDB对象标识。
# - 为什么这样写：集中命名固定参数可避免魔法值散落，并让升级、审计和回归测试有稳定锚点。
SYMBOL_LITERAL_RE = re.compile(r"^[A-Za-z0-9_.:-]+$")


# 类DailyFundsDolphinDBError：TASK_016B 建库、写入或验收错误。
# - 结构：继承或实现RuntimeError；类体约包含0个字段或常量、0个方法。
# - 数据变化：类定义阶段不执行隐式I/O，实例只在构造或显式方法调用时改变受控状态。
# - 实操：调用方通过该类型集中传递配置、记录、服务或结果，避免跨模块使用无约束字典。
# - 为什么这样写：强类型边界能集中维护单位、时点、主键和安全不变量，并降低供应商耦合。
class DailyFundsDolphinDBError(RuntimeError):
    """TASK_016B 建库、写入或验收错误。"""


# 类SessionProtocol：DolphinDB会话所需最小接口。
# - 结构：继承或实现Protocol；类体约包含0个字段或常量、2个方法。
# - 数据变化：类定义阶段不执行隐式I/O，实例只在构造或显式方法调用时改变受控状态。
# - 实操：调用方通过该类型集中传递配置、记录、服务或结果，避免跨模块使用无约束字典。
# - 为什么这样写：强类型边界能集中维护单位、时点、主键和安全不变量，并降低供应商耦合。
class SessionProtocol(Protocol):
    """DolphinDB会话所需最小接口。"""

    # 函数connect：建立连接。
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
        """建立连接。"""

    # 函数run：执行DolphinDB脚本。
    # - 输入：script:str；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型Any；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把任务入口与流程编排步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    def run(self, script: str) -> Any:
        """执行DolphinDB脚本。"""


# 类AppenderProtocol：DolphinDB TableAppender 所需最小接口。
# - 结构：继承或实现Protocol；类体约包含0个字段或常量、1个方法。
# - 数据变化：类定义阶段不执行隐式I/O，实例只在构造或显式方法调用时改变受控状态。
# - 实操：调用方通过该类型集中传递配置、记录、服务或结果，避免跨模块使用无约束字典。
# - 为什么这样写：强类型边界能集中维护单位、时点、主键和安全不变量，并降低供应商耦合。
class AppenderProtocol(Protocol):
    """DolphinDB TableAppender 所需最小接口。"""

    # 函数append：追加DataFrame。
    # - 输入：data:pd.DataFrame；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型Any；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：该函数名称涉及写入能力，只有调用方显式进入受控模式时才可能产生数据库或文件副作用；注释迁移和验证不会调用它。
    # - 为什么这样写：把显式写入或持久化步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    def append(self, data: pd.DataFrame) -> Any:
        """追加DataFrame。"""


# 状态计算：把`Callable[[], SessionProtocol]`的结果保存到`SessionFactory`，供当前逻辑后续校验、转换、累计或返回。
# - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
# - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
SessionFactory = Callable[[], SessionProtocol]
# 状态计算：把`Callable[[str, str, SessionProtocol], AppenderProtocol]`的结果保存到`AppenderFactory`，供当前逻辑后续校验、转换、累计或返回。
# - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
# - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
AppenderFactory = Callable[
    [str, str, SessionProtocol], AppenderProtocol
]


# 类DolphinDBWriteSettings：DolphinDB写入连接参数。
# - 结构：继承或实现object；类体约包含5个字段或常量、1个方法。
# - 数据变化：类定义阶段不执行隐式I/O，实例只在构造或显式方法调用时改变受控状态。
# - 实操：调用方通过该类型集中传递配置、记录、服务或结果，避免跨模块使用无约束字典。
# - 为什么这样写：强类型边界能集中维护单位、时点、主键和安全不变量，并降低供应商耦合。
@dataclass(frozen=True, slots=True)
class DolphinDBWriteSettings:
    """DolphinDB写入连接参数。"""

    # 状态计算：把`'127.0.0.1'`的结果保存到`host`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    host: str = "127.0.0.1"
    # 状态计算：把`8848`的结果保存到`port`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    port: int = 8848
    # 状态计算：把`'admin'`的结果保存到`username`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    username: str = "admin"
    # 状态计算：把`''`的结果保存到`password`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    password: str = ""
    # 状态计算：把`DATABASE_URI`的结果保存到`database_uri`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    database_uri: str = DATABASE_URI

    # 函数__post_init__：执行__post_init__对应的业务处理。
    # - 输入：无外部业务参数；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型None；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    def __post_init__(self) -> None:
        # 条件门禁：判断`not self.host.strip()`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if not self.host.strip():
            # 错误阻断：抛出`DailyFundsDolphinDBError('host不能为空。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
            raise DailyFundsDolphinDBError("host不能为空。")
        # 条件门禁：判断`not 1 <= int(self.port) <= 65535`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if not 1 <= int(self.port) <= 65535:
            # 错误阻断：抛出`DailyFundsDolphinDBError('port必须在1到65535之间。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
            raise DailyFundsDolphinDBError(
                "port必须在1到65535之间。"
            )
        # 条件门禁：判断`not self.username.strip()`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if not self.username.strip():
            # 错误阻断：抛出`DailyFundsDolphinDBError('username不能为空。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
            raise DailyFundsDolphinDBError(
                "username不能为空。"
            )
        # 条件门禁：判断`not self.password`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if not self.password:
            # 错误阻断：抛出`DailyFundsDolphinDBError('DolphinDB密码不能为空。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
            raise DailyFundsDolphinDBError(
                "DolphinDB密码不能为空。"
            )
        # 条件门禁：判断`not re.fullmatch('dfs://[A-Za-z0-9_.-]+', self.database_uri)`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if not re.fullmatch(
            r"dfs://[A-Za-z0-9_.-]+",
            self.database_uri,
        ):
            # 错误阻断：抛出`DailyFundsDolphinDBError('database_uri必须使用dfs://数据库名格式。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
            raise DailyFundsDolphinDBError(
                "database_uri必须使用dfs://数据库名格式。"
            )


# 关键常量COMMON_COLUMNS：集中保存`(('dataset_id', 'SYMBOL'), ('snapshot_date', 'DATE'), ('snapshot_month', 'MONTH'), ('snapshot_phase…`对应的合同值、Schema集合或运行边界。
# - 来源与范围：该值来自当前项目任务、配置、真实数据画像或安全合同；未明确说明时不得外推为行业统一标准。
# - 单位与实例：数值单位由变量名、相邻校验和调用语义共同限定；字符串用于版本、字段、状态或DolphinDB对象标识。
# - 为什么这样写：集中命名固定参数可避免魔法值散落，并让升级、审计和回归测试有稳定锚点。
COMMON_COLUMNS = (
    ("dataset_id", "SYMBOL"),
    ("snapshot_date", "DATE"),
    ("snapshot_month", "MONTH"),
    ("snapshot_phase", "SYMBOL"),
    ("schema_version", "SYMBOL"),
    ("entity_key", "STRING"),
    ("source_row_number", "INT"),
    ("source_file_name", "STRING"),
    ("source_file_relative_path", "STRING"),
    ("source_file_size_bytes", "LONG"),
    ("source_file_mtime_utc", "TIMESTAMP"),
    ("source_file_sha256", "SYMBOL"),
    ("row_sha256", "STRING"),
    ("ingest_batch_id", "SYMBOL"),
    ("ingested_at_utc", "TIMESTAMP"),
    ("quality_status", "SYMBOL"),
    ("raw_row_json", "STRING"),
)

# 关键常量SECURITY_COLUMNS：集中保存`COMMON_COLUMNS + (('instrument_id', 'SYMBOL'), ('market_candidate', 'SYMBOL'), ('instrument_name', …`对应的合同值、Schema集合或运行边界。
# - 来源与范围：该值来自当前项目任务、配置、真实数据画像或安全合同；未明确说明时不得外推为行业统一标准。
# - 单位与实例：数值单位由变量名、相邻校验和调用语义共同限定；字符串用于版本、字段、状态或DolphinDB对象标识。
# - 为什么这样写：集中命名固定参数可避免魔法值散落，并让升级、审计和回归测试有稳定锚点。
SECURITY_COLUMNS = COMMON_COLUMNS + (
    ("instrument_id", "SYMBOL"),
    ("market_candidate", "SYMBOL"),
    ("instrument_name", "STRING"),
    ("last_price", "DOUBLE"),
    ("pct_change", "DOUBLE"),
    ("price_change", "DOUBLE"),
    ("total_volume_lot", "DOUBLE"),
    ("current_volume_lot", "DOUBLE"),
    ("bid_price", "DOUBLE"),
    ("ask_price", "DOUBLE"),
    ("speed_pct", "DOUBLE"),
    ("turnover_pct", "DOUBLE"),
    ("amount_cny", "DOUBLE"),
    ("pe_dynamic", "DOUBLE"),
    ("industry_name", "STRING"),
    ("high_price", "DOUBLE"),
    ("low_price", "DOUBLE"),
    ("open_price", "DOUBLE"),
    ("prev_close", "DOUBLE"),
    ("amplitude_pct", "DOUBLE"),
    ("volume_ratio", "DOUBLE"),
    ("order_imbalance_pct", "DOUBLE"),
    ("order_imbalance_lot", "DOUBLE"),
    ("avg_price", "DOUBLE"),
    ("inner_volume_lot", "DOUBLE"),
    ("outer_volume_lot", "DOUBLE"),
    ("inner_outer_ratio", "DOUBLE"),
    ("bid1_volume_lot", "DOUBLE"),
    ("ask1_volume_lot", "DOUBLE"),
    ("pb", "DOUBLE"),
    ("total_shares", "DOUBLE"),
    ("total_market_cap_cny", "DOUBLE"),
    ("float_shares", "DOUBLE"),
    ("float_market_cap_cny", "DOUBLE"),
    ("return_3d_pct", "DOUBLE"),
    ("return_6d_pct", "DOUBLE"),
    ("turnover_3d_pct", "DOUBLE"),
    ("turnover_6d_pct", "DOUBLE"),
    ("consecutive_up_days", "INT"),
    ("return_month_pct", "DOUBLE"),
    ("return_ytd_pct", "DOUBLE"),
    ("return_1m_pct", "DOUBLE"),
    ("return_1y_pct", "DOUBLE"),
    ("listing_date_raw", "STRING"),
    ("speed_5m_pct", "DOUBLE"),
    ("return_20d_pct", "DOUBLE"),
    ("source_volume_unit", "SYMBOL"),
    ("canonical_volume_transform", "SYMBOL"),
    ("source_amount_unit", "SYMBOL"),
)

# 关键常量CLASSIFICATION_COLUMNS：集中保存`COMMON_COLUMNS + (('classification_type', 'SYMBOL'), ('node_name_raw', 'STRING'), ('pct_change', 'D…`对应的合同值、Schema集合或运行边界。
# - 来源与范围：该值来自当前项目任务、配置、真实数据画像或安全合同；未明确说明时不得外推为行业统一标准。
# - 单位与实例：数值单位由变量名、相邻校验和调用语义共同限定；字符串用于版本、字段、状态或DolphinDB对象标识。
# - 为什么这样写：集中命名固定参数可避免魔法值散落，并让升级、审计和回归测试有稳定锚点。
CLASSIFICATION_COLUMNS = COMMON_COLUMNS + (
    ("classification_type", "SYMBOL"),
    ("node_name_raw", "STRING"),
    ("pct_change", "DOUBLE"),
    ("return_3d_pct", "DOUBLE"),
    ("speed_pct", "DOUBLE"),
    ("leading_stock_name", "STRING"),
    ("up_count", "INT"),
    ("down_count", "INT"),
    ("breadth_ratio", "DOUBLE"),
    ("breadth_status", "SYMBOL"),
    ("limit_up_count", "INT"),
    ("turnover_pct", "DOUBLE"),
    ("volume_ratio", "DOUBLE"),
    ("turnover_3d_pct", "DOUBLE"),
    ("return_5d_pct", "DOUBLE"),
    ("return_10d_pct", "DOUBLE"),
    ("return_20d_pct", "DOUBLE"),
    ("volume_lot", "DOUBLE"),
    ("amount_cny", "DOUBLE"),
    ("total_market_cap_cny", "DOUBLE"),
    ("float_market_cap_cny", "DOUBLE"),
    ("average_return_pct", "DOUBLE"),
    ("average_shares", "DOUBLE"),
    ("pe_ratio", "DOUBLE"),
    ("source_volume_unit", "SYMBOL"),
    ("canonical_volume_transform", "SYMBOL"),
    ("source_amount_unit", "SYMBOL"),
)

# 关键常量MONEY_FLOW_COLUMNS：集中保存`COMMON_COLUMNS + (('instrument_id', 'SYMBOL'), ('market_candidate', 'SYMBOL'), ('instrument_name', …`对应的合同值、Schema集合或运行边界。
# - 来源与范围：该值来自当前项目任务、配置、真实数据画像或安全合同；未明确说明时不得外推为行业统一标准。
# - 单位与实例：数值单位由变量名、相邻校验和调用语义共同限定；字符串用于版本、字段、状态或DolphinDB对象标识。
# - 为什么这样写：集中命名固定参数可避免魔法值散落，并让升级、审计和回归测试有稳定锚点。
MONEY_FLOW_COLUMNS = COMMON_COLUMNS + (
    ("instrument_id", "SYMBOL"),
    ("market_candidate", "SYMBOL"),
    ("instrument_name", "STRING"),
    ("last_price", "DOUBLE"),
    ("pct_change", "DOUBLE"),
    ("main_net_inflow_cny", "DOUBLE"),
    ("auction_net_inflow_cny", "DOUBLE"),
    ("super_large_inflow_cny", "DOUBLE"),
    ("super_large_outflow_cny", "DOUBLE"),
    ("super_large_net_cny", "DOUBLE"),
    ("super_large_net_ratio_pct", "DOUBLE"),
    ("large_inflow_cny", "DOUBLE"),
    ("large_outflow_cny", "DOUBLE"),
    ("large_net_cny", "DOUBLE"),
    ("large_net_ratio_pct", "DOUBLE"),
    ("medium_inflow_cny", "DOUBLE"),
    ("medium_outflow_cny", "DOUBLE"),
    ("medium_net_cny", "DOUBLE"),
    ("medium_net_ratio_pct", "DOUBLE"),
    ("small_inflow_cny", "DOUBLE"),
    ("small_outflow_cny", "DOUBLE"),
    ("small_net_cny", "DOUBLE"),
    ("small_net_ratio_pct", "DOUBLE"),
    ("source_amount_unit", "SYMBOL"),
    ("outflow_sign_policy", "SYMBOL"),
)

# 关键常量INGEST_BATCH_COLUMNS：集中保存`(('ingest_batch_id', 'SYMBOL'), ('batch_month', 'MONTH'), ('logged_at', 'TIMESTAMP'), ('status', 'S…`对应的合同值、Schema集合或运行边界。
# - 来源与范围：该值来自当前项目任务、配置、真实数据画像或安全合同；未明确说明时不得外推为行业统一标准。
# - 单位与实例：数值单位由变量名、相邻校验和调用语义共同限定；字符串用于版本、字段、状态或DolphinDB对象标识。
# - 为什么这样写：集中命名固定参数可避免魔法值散落，并让升级、审计和回归测试有稳定锚点。
INGEST_BATCH_COLUMNS = (
    ("ingest_batch_id", "SYMBOL"),
    ("batch_month", "MONTH"),
    ("logged_at", "TIMESTAMP"),
    ("status", "SYMBOL"),
    ("scan_root", "STRING"),
    ("contract_version", "STRING"),
    ("preflight_status", "SYMBOL"),
    ("source_file_count", "INT"),
    ("ready_file_count", "INT"),
    ("quarantined_file_count", "INT"),
    ("blocked_file_count", "INT"),
    ("planned_row_count", "LONG"),
    ("inserted_row_count", "LONG"),
    ("skipped_row_count", "LONG"),
    ("failed_file_count", "INT"),
    ("message", "STRING"),
)

# 关键常量INGEST_FILE_COLUMNS：集中保存`(('ingest_batch_id', 'SYMBOL'), ('snapshot_date', 'DATE'), ('snapshot_month', 'MONTH'), ('logged_at…`对应的合同值、Schema集合或运行边界。
# - 来源与范围：该值来自当前项目任务、配置、真实数据画像或安全合同；未明确说明时不得外推为行业统一标准。
# - 单位与实例：数值单位由变量名、相邻校验和调用语义共同限定；字符串用于版本、字段、状态或DolphinDB对象标识。
# - 为什么这样写：集中命名固定参数可避免魔法值散落，并让升级、审计和回归测试有稳定锚点。
INGEST_FILE_COLUMNS = (
    ("ingest_batch_id", "SYMBOL"),
    ("snapshot_date", "DATE"),
    ("snapshot_month", "MONTH"),
    ("logged_at", "TIMESTAMP"),
    ("dataset_id", "SYMBOL"),
    ("family", "SYMBOL"),
    ("source_file_name", "STRING"),
    ("source_file_sha256", "SYMBOL"),
    ("schema_version", "SYMBOL"),
    ("row_count", "LONG"),
    ("existing_row_count_before", "LONG"),
    ("inserted_row_count", "LONG"),
    ("final_row_count", "LONG"),
    ("status", "SYMBOL"),
    ("message", "STRING"),
)

# 关键常量QUARANTINE_FILE_COLUMNS：集中保存`(('ingest_batch_id', 'SYMBOL'), ('snapshot_date', 'DATE'), ('snapshot_month', 'MONTH'), ('logged_at…`对应的合同值、Schema集合或运行边界。
# - 来源与范围：该值来自当前项目任务、配置、真实数据画像或安全合同；未明确说明时不得外推为行业统一标准。
# - 单位与实例：数值单位由变量名、相邻校验和调用语义共同限定；字符串用于版本、字段、状态或DolphinDB对象标识。
# - 为什么这样写：集中命名固定参数可避免魔法值散落，并让升级、审计和回归测试有稳定锚点。
QUARANTINE_FILE_COLUMNS = (
    ("ingest_batch_id", "SYMBOL"),
    ("snapshot_date", "DATE"),
    ("snapshot_month", "MONTH"),
    ("logged_at", "TIMESTAMP"),
    ("dataset_id", "SYMBOL"),
    ("source_file_name", "STRING"),
    ("source_file_sha256", "SYMBOL"),
    ("row_count", "LONG"),
    ("reason_code", "SYMBOL"),
    ("reason_detail", "STRING"),
    ("reference_dataset_id", "SYMBOL"),
    ("coverage_ratio", "DOUBLE"),
    ("minimum_ratio", "DOUBLE"),
)

# 关键常量TABLE_SCHEMAS：集中保存`{TABLE_NAMES['security_snapshot']: SECURITY_COLUMNS, TABLE_NAMES['classification_snapshot']: CLASSI…`对应的合同值、Schema集合或运行边界。
# - 来源与范围：该值来自当前项目任务、配置、真实数据画像或安全合同；未明确说明时不得外推为行业统一标准。
# - 单位与实例：数值单位由变量名、相邻校验和调用语义共同限定；字符串用于版本、字段、状态或DolphinDB对象标识。
# - 为什么这样写：集中命名固定参数可避免魔法值散落，并让升级、审计和回归测试有稳定锚点。
TABLE_SCHEMAS = {
    TABLE_NAMES["security_snapshot"]: SECURITY_COLUMNS,
    TABLE_NAMES["classification_snapshot"]: CLASSIFICATION_COLUMNS,
    TABLE_NAMES["money_flow_snapshot"]: MONEY_FLOW_COLUMNS,
    TABLE_NAMES["ingest_batch"]: INGEST_BATCH_COLUMNS,
    TABLE_NAMES["ingest_file"]: INGEST_FILE_COLUMNS,
    TABLE_NAMES["quarantine_file"]: QUARANTINE_FILE_COLUMNS,
}

# 关键常量TABLE_DEFINITIONS：集中保存`{TABLE_NAMES['security_snapshot']: {'partition_column': 'snapshot_month', 'sort_columns': ('dataset…`对应的合同值、Schema集合或运行边界。
# - 来源与范围：该值来自当前项目任务、配置、真实数据画像或安全合同；未明确说明时不得外推为行业统一标准。
# - 单位与实例：数值单位由变量名、相邻校验和调用语义共同限定；字符串用于版本、字段、状态或DolphinDB对象标识。
# - 为什么这样写：集中命名固定参数可避免魔法值散落，并让升级、审计和回归测试有稳定锚点。
TABLE_DEFINITIONS = {
    TABLE_NAMES["security_snapshot"]: {
        "partition_column": "snapshot_month",
        "sort_columns": (
            "dataset_id",
            "source_file_sha256",
            "source_row_number",
        ),
        "keep_duplicates": "LAST",
    },
    TABLE_NAMES["classification_snapshot"]: {
        "partition_column": "snapshot_month",
        "sort_columns": (
            "dataset_id",
            "source_file_sha256",
            "source_row_number",
        ),
        "keep_duplicates": "LAST",
    },
    TABLE_NAMES["money_flow_snapshot"]: {
        "partition_column": "snapshot_month",
        "sort_columns": (
            "dataset_id",
            "source_file_sha256",
            "source_row_number",
        ),
        "keep_duplicates": "LAST",
    },
    TABLE_NAMES["ingest_batch"]: {
        "partition_column": "batch_month",
        "sort_columns": ("ingest_batch_id", "logged_at"),
        "keep_duplicates": "ALL",
    },
    TABLE_NAMES["ingest_file"]: {
        "partition_column": "snapshot_month",
        "sort_columns": (
            "ingest_batch_id",
            "source_file_sha256",
            "logged_at",
        ),
        "keep_duplicates": "ALL",
    },
    TABLE_NAMES["quarantine_file"]: {
        "partition_column": "snapshot_month",
        "sort_columns": (
            "ingest_batch_id",
            "source_file_sha256",
            "logged_at",
        ),
        "keep_duplicates": "ALL",
    },
}


# 函数_validate_identifier：执行_validate_identifier对应的业务处理。
# - 输入：value:str；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型str；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
# - 为什么这样写：把合同、数据质量或安全门禁校验步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def _validate_identifier(value: str) -> str:
    # 条件门禁：判断`not IDENTIFIER_RE.fullmatch(value)`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if not IDENTIFIER_RE.fullmatch(value):
        # 错误阻断：抛出`DailyFundsDolphinDBError(f'非法DolphinDB标识符：{value!r}')`并停止当前正常路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
        # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
        raise DailyFundsDolphinDBError(
            f"非法DolphinDB标识符：{value!r}"
        )
    # 结果返回：把`value`交给调用方并结束当前函数。
    # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return value


# 函数_symbol_literal：执行_symbol_literal对应的业务处理。
# - 输入：value:str；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型str；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
# - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def _symbol_literal(value: str) -> str:
    # 条件门禁：判断`not SYMBOL_LITERAL_RE.fullmatch(value)`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if not SYMBOL_LITERAL_RE.fullmatch(value):
        # 错误阻断：抛出`DailyFundsDolphinDBError(f'不能安全构造SYMBOL字面量：{value!r}')`并停止当前正常路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
        # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
        raise DailyFundsDolphinDBError(
            f"不能安全构造SYMBOL字面量：{value!r}"
        )
    # 结果返回：把`f'`{value}'`交给调用方并结束当前函数。
    # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return f"`{value}"


# 函数_schema_table_expression：执行_schema_table_expression对应的业务处理。
# - 输入：columns:Sequence[tuple[str, str]]；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型str；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
# - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def _schema_table_expression(
    columns: Sequence[tuple[str, str]],
) -> str:
    # 状态计算：把`','.join((f'`{_validate_identifier(name)}' for name, _ in columns))`的结果保存到`names`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    names = ",".join(
        f"`{_validate_identifier(name)}" for name, _ in columns
    )
    # 状态计算：把`','.join((data_type for _, data_type in columns))`的结果保存到`types`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    types = ",".join(data_type for _, data_type in columns)
    # 结果返回：把`f'table(1:0, [{names}], [{types}])'`交给调用方并结束当前函数。
    # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return f"table(1:0, [{names}], [{types}])"


# 函数build_create_database_script：生成幂等、非破坏性的DolphinDB建库建表脚本。
# - 输入：database_uri:str；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型str；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：该函数名称涉及写入能力，只有调用方显式进入受控模式时才可能产生数据库或文件副作用；注释迁移和验证不会调用它。
# - 为什么这样写：把显式写入或持久化步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def build_create_database_script(
    database_uri: str = DATABASE_URI,
) -> str:
    """生成幂等、非破坏性的DolphinDB建库建表脚本。"""
    # 条件门禁：判断`not re.fullmatch('dfs://[A-Za-z0-9_.-]+', database_uri)`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if not re.fullmatch(
        r"dfs://[A-Za-z0-9_.-]+",
        database_uri,
    ):
        # 错误阻断：抛出`DailyFundsDolphinDBError('database_uri格式非法。')`并停止当前正常路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
        # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
        raise DailyFundsDolphinDBError(
            "database_uri格式非法。"
        )

    # 状态计算：把`[f'dbPath = "{database_uri}"', 'if(!existsDatabase(dbPath)){', f' db = database(dbPath, VALUE, {PAR…`的结果保存到`lines`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    lines = [
        f'dbPath = "{database_uri}"',
        "if(!existsDatabase(dbPath)){",
        (
            "    db = database("
            f"dbPath, VALUE, "
            f"{PARTITION_START_MONTH}..{PARTITION_END_MONTH}, "
            ', "TSDB")'
        ),
        "}else{",
        "    db = database(dbPath)",
        "}",
    ]

    # 循环处理：逐项遍历`enumerate(TABLE_SCHEMAS.items(), start=1)`，把当前元素绑定到`(index, (table_name, columns))`。
    # - 数据变化：每轮只处理一个来源记录、字段、文件或证据项，并显式累计到局部集合或输出对象。
    # - 为什么这样写：逐项处理便于保留行级血缘、隔离单项异常，并控制16GB单机上的峰值内存。
    for index, (table_name, columns) in enumerate(
        TABLE_SCHEMAS.items(),
        start=1,
    ):
        # 状态计算：把`TABLE_DEFINITIONS[table_name]`的结果保存到`definition`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        definition = TABLE_DEFINITIONS[table_name]
        # 状态计算：把`f'schema_{index}'`的结果保存到`schema_var`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        schema_var = f"schema_{index}"
        # 状态计算：把`definition['partition_column']`的结果保存到`partition_column`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        partition_column = definition["partition_column"]
        # 状态计算：把`','.join((f'`{_validate_identifier(item)}' for item in definition['sort_columns']))`的结果保存到`sort_columns`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        sort_columns = ",".join(
            f"`{_validate_identifier(item)}"
            for item in definition["sort_columns"]
        )
        # 状态计算：把`definition['keep_duplicates']`的结果保存到`keep_duplicates`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        keep_duplicates = definition["keep_duplicates"]
        # 显式调用：执行`lines.extend([f'if(!existsTable(dbPath, `{table_name})){{', f' {schema_var} = {_schema_table_expression(columns)}', f' db.createPartitioned…`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
        # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
        # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
        lines.extend(
            [
                f"if(!existsTable(dbPath, `{table_name})){{",
                (
                    f"    {schema_var} = "
                    f"{_schema_table_expression(columns)}"
                ),
                (
                    "    db.createPartitionedTable("
                    f"{schema_var}, `{table_name}, "
                    f"`{partition_column}, , "
                    f"[{sort_columns}], {keep_duplicates})"
                ),
                "}",
            ]
        )

    # 显式调用：执行`lines.append('tableNames = ' + '[' + ','.join((f'`{name}' for name in TABLE_SCHEMAS)) + ']')`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
    # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
    # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
    lines.append(
        "tableNames = "
        + "[" + ",".join(
            f"`{name}" for name in TABLE_SCHEMAS
        ) + "]"
    )
    # 显式调用：执行`lines.append('tableExists = each(existsTable{dbPath}, tableNames)')`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
    # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
    # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
    lines.append(
        "tableExists = each(existsTable{dbPath}, tableNames)"
    )
    # 显式调用：执行`lines.append('table(tableNames as table_name, tableExists as table_exists)')`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
    # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
    # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
    lines.append(
        "table(tableNames as table_name, "
        "tableExists as table_exists)"
    )
    # 结果返回：把`'\n'.join(lines)`交给调用方并结束当前函数。
    # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return "\n".join(lines)


# 函数validate_local_contract：不连接DolphinDB，验证来源合同与物理Schema计划。
# - 输入：contract_path:Path；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型dict[str, Any]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
# - 为什么这样写：把合同、数据质量或安全门禁校验步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def validate_local_contract(
    contract_path: Path,
) -> dict[str, Any]:
    """不连接DolphinDB，验证来源合同与物理Schema计划。"""
    # 状态计算：把`load_daily_funds_contract(contract_path)`的结果保存到`contract`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    contract = load_daily_funds_contract(contract_path)
    # 状态计算：把`validate_daily_funds_contract(contract)`的结果保存到`contract_result`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    contract_result = validate_daily_funds_contract(contract)

    # 状态计算：把`list(contract_result.get('issues', []))`的结果保存到`issues`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    issues = list(contract_result.get("issues", []))
    # 状态计算：把`dict(contract.database_plan.get('physical_tables', {}))`的结果保存到`planned_tables`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    planned_tables = dict(
        contract.database_plan.get(
            "physical_tables",
            {},
        )
    )
    # 循环处理：逐项遍历`TABLE_NAMES.items()`，把当前元素绑定到`(plan_key, expected_table)`。
    # - 数据变化：每轮只处理一个来源记录、字段、文件或证据项，并显式累计到局部集合或输出对象。
    # - 为什么这样写：逐项处理便于保留行级血缘、隔离单项异常，并控制16GB单机上的峰值内存。
    for plan_key, expected_table in TABLE_NAMES.items():
        # 状态计算：把`planned_tables.get(plan_key)`的结果保存到`actual`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        actual = planned_tables.get(plan_key)
        # 条件门禁：判断`actual != expected_table`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if actual != expected_table:
            # 显式调用：执行`issues.append({'severity': 'ERROR', 'code': 'PHYSICAL_TABLE_PLAN_MISMATCH', 'plan_key': plan_key, 'expected': expected_table, 'actual': act…`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
            # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
            # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
            issues.append(
                {
                    "severity": "ERROR",
                    "code": "PHYSICAL_TABLE_PLAN_MISMATCH",
                    "plan_key": plan_key,
                    "expected": expected_table,
                    "actual": actual,
                }
            )

    # 循环处理：逐项遍历`TABLE_SCHEMAS.items()`，把当前元素绑定到`(table_name, columns)`。
    # - 数据变化：每轮只处理一个来源记录、字段、文件或证据项，并显式累计到局部集合或输出对象。
    # - 为什么这样写：逐项处理便于保留行级血缘、隔离单项异常，并控制16GB单机上的峰值内存。
    for table_name, columns in TABLE_SCHEMAS.items():
        # 状态计算：把`[name for name, _ in columns]`的结果保存到`names`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        names = [name for name, _ in columns]
        # 条件门禁：判断`len(names) != len(set(names))`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if len(names) != len(set(names)):
            # 显式调用：执行`issues.append({'severity': 'ERROR', 'code': 'DUPLICATE_PHYSICAL_COLUMN', 'table_name': table_name})`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
            # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
            # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
            issues.append(
                {
                    "severity": "ERROR",
                    "code": "DUPLICATE_PHYSICAL_COLUMN",
                    "table_name": table_name,
                }
            )
        # 状态计算：把`TABLE_DEFINITIONS[table_name]`的结果保存到`definition`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        definition = TABLE_DEFINITIONS[table_name]
        # 条件门禁：判断`definition['partition_column'] not in names`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if definition["partition_column"] not in names:
            # 显式调用：执行`issues.append({'severity': 'ERROR', 'code': 'PARTITION_COLUMN_MISSING', 'table_name': table_name})`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
            # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
            # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
            issues.append(
                {
                    "severity": "ERROR",
                    "code": "PARTITION_COLUMN_MISSING",
                    "table_name": table_name,
                }
            )
        # 条件门禁：判断`any((item not in names for item in definition['sort_columns']))`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if any(
            item not in names
            for item in definition["sort_columns"]
        ):
            # 显式调用：执行`issues.append({'severity': 'ERROR', 'code': 'SORT_COLUMN_MISSING', 'table_name': table_name})`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
            # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
            # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
            issues.append(
                {
                    "severity": "ERROR",
                    "code": "SORT_COLUMN_MISSING",
                    "table_name": table_name,
                }
            )

    # 状态计算：把`build_create_database_script(str(contract.database_plan.get('database_uri', DATABASE_URI)))`的结果保存到`ddl`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    ddl = build_create_database_script(
        str(
            contract.database_plan.get(
                "database_uri",
                DATABASE_URI,
            )
        )
    )
    # 结果返回：把`{'task_id': 'TASK_016B', 'mode': 'CONTRACT', 'contract_version': contract.contract_version, 'dataset_count': len(contra…`交给调用方并结束当前函数。
    # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return {
        "task_id": "TASK_016B",
        "mode": "CONTRACT",
        "contract_version": contract.contract_version,
        "dataset_count": len(contract.datasets),
        "physical_table_count": len(TABLE_SCHEMAS),
        "main_raw_table_count": len(FAMILY_TO_TABLE),
        "database_uri": contract.database_plan.get(
            "database_uri"
        ),
        "partition_domain": (
            f"{PARTITION_START_MONTH}.."
            f"{PARTITION_END_MONTH}"
        ),
        "overall_status": (
            "PASSED"
            if not any(
                item.get("severity") == "ERROR"
                for item in issues
            )
            else "FAILED"
        ),
        "issues": issues,
        "ddl_sha256": hashlib_sha256_text(ddl),
    }


# 函数hashlib_sha256_text：执行hashlib_sha256_text对应的业务处理。
# - 输入：value:str；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型str；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
# - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def hashlib_sha256_text(value: str) -> str:
    # 依赖导入：加载`import hashlib`所提供的类型、标准库或项目内能力。
    # - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
    # - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
    import hashlib

    # 结果返回：把`hashlib.sha256(value.encode('utf-8')).hexdigest()`交给调用方并结束当前函数。
    # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


# 函数_default_session_factory：执行_default_session_factory对应的业务处理。
# - 输入：无外部业务参数；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型SessionProtocol；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
# - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def _default_session_factory() -> SessionProtocol:
    # 异常边界：尝试执行可能失败的解析、查询、文件或类型转换步骤，并由后续处理保留错误证据。
    # - 数据变化：正常路径产生业务结果；异常路径不得静默伪造数据，应抛出、记录或隔离。
    # - 为什么这样写：把外部环境故障与业务合同失败分开，便于重试、回滚和准确验收。
    try:
        # 状态计算：把`importlib.import_module('dolphindb')`的结果保存到`ddb`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        ddb = importlib.import_module("dolphindb")
    except ImportError as exc:
        # 错误阻断：抛出`DailyFundsDolphinDBError('未安装dolphindb Python客户端。')`并停止当前正常路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
        # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
        raise DailyFundsDolphinDBError(
            "未安装dolphindb Python客户端。"
        ) from exc
    # 状态计算：把`getattr(ddb, 'Session', None)`的结果保存到`session_class`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    session_class = getattr(ddb, "Session", None)
    # 条件门禁：判断`session_class is not None`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if session_class is not None:
        # 结果返回：把`session_class()`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return session_class()
    # 状态计算：把`getattr(ddb, 'session', None)`的结果保存到`legacy_factory`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    legacy_factory = getattr(ddb, "session", None)
    # 条件门禁：判断`legacy_factory is None`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if legacy_factory is None:
        # 错误阻断：抛出`DailyFundsDolphinDBError('dolphindb包没有Session/session入口。')`并停止当前正常路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
        # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
        raise DailyFundsDolphinDBError(
            "dolphindb包没有Session/session入口。"
        )
    # 结果返回：把`legacy_factory()`交给调用方并结束当前函数。
    # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return legacy_factory()


# 函数_default_appender_factory：执行_default_appender_factory对应的业务处理。
# - 输入：database_uri:str、table_name:str、session:SessionProtocol；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型AppenderProtocol；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
# - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def _default_appender_factory(
    database_uri: str,
    table_name: str,
    session: SessionProtocol,
) -> AppenderProtocol:
    # 异常边界：尝试执行可能失败的解析、查询、文件或类型转换步骤，并由后续处理保留错误证据。
    # - 数据变化：正常路径产生业务结果；异常路径不得静默伪造数据，应抛出、记录或隔离。
    # - 为什么这样写：把外部环境故障与业务合同失败分开，便于重试、回滚和准确验收。
    try:
        # 状态计算：把`importlib.import_module('dolphindb')`的结果保存到`ddb`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        ddb = importlib.import_module("dolphindb")
    except ImportError as exc:
        # 错误阻断：抛出`DailyFundsDolphinDBError('未安装dolphindb Python客户端。')`并停止当前正常路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
        # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
        raise DailyFundsDolphinDBError(
            "未安装dolphindb Python客户端。"
        ) from exc

    # 状态计算：把`getattr(ddb, 'TableAppender', None)`的结果保存到`appender_class`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    appender_class = getattr(ddb, "TableAppender", None)
    # 条件门禁：判断`appender_class is None`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if appender_class is None:
        # 状态计算：把`getattr(ddb, 'tableAppender', None)`的结果保存到`appender_class`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        appender_class = getattr(ddb, "tableAppender", None)
    # 条件门禁：判断`appender_class is None`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if appender_class is None:
        # 错误阻断：抛出`DailyFundsDolphinDBError('dolphindb包不支持TableAppender/tableAppender。')`并停止当前正常路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
        # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
        raise DailyFundsDolphinDBError(
            "dolphindb包不支持TableAppender/tableAppender。"
        )
    # 结果返回：把`appender_class(dbPath=database_uri, tableName=table_name, ddbSession=session, action='fitColumnType')`交给调用方并结束当前函数。
    # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return appender_class(
        dbPath=database_uri,
        tableName=table_name,
        ddbSession=session,
        action="fitColumnType",
    )


# 函数connect_session：执行connect_session对应的业务处理。
# - 输入：settings:DolphinDBWriteSettings、session_factory:SessionFactory；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型SessionProtocol；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
# - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def connect_session(
    settings: DolphinDBWriteSettings,
    session_factory: SessionFactory = _default_session_factory,
) -> SessionProtocol:
    # 状态计算：把`session_factory()`的结果保存到`session`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    session = session_factory()
    # 异常边界：尝试执行可能失败的解析、查询、文件或类型转换步骤，并由后续处理保留错误证据。
    # - 数据变化：正常路径产生业务结果；异常路径不得静默伪造数据，应抛出、记录或隔离。
    # - 为什么这样写：把外部环境故障与业务合同失败分开，便于重试、回滚和准确验收。
    try:
        # 显式调用：执行`session.connect(settings.host, int(settings.port), settings.username, settings.password)`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
        # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
        # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
        session.connect(
            settings.host,
            int(settings.port),
            settings.username,
            settings.password,
        )
    except Exception as exc:
        # 错误阻断：抛出`DailyFundsDolphinDBError(f'DolphinDB连接失败：{exc}')`并停止当前正常路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
        # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
        raise DailyFundsDolphinDBError(
            f"DolphinDB连接失败：{exc}"
        ) from exc
    # 异常边界：尝试执行可能失败的解析、查询、文件或类型转换步骤，并由后续处理保留错误证据。
    # - 数据变化：正常路径产生业务结果；异常路径不得静默伪造数据，应抛出、记录或隔离。
    # - 为什么这样写：把外部环境故障与业务合同失败分开，便于重试、回滚和准确验收。
    try:
        # 状态计算：把`session.run('1 + 1')`的结果保存到`result`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        result = session.run("1 + 1")
    except Exception as exc:
        # 错误阻断：抛出`DailyFundsDolphinDBError(f'DolphinDB健康检查失败：{exc}')`并停止当前正常路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
        # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
        raise DailyFundsDolphinDBError(
            f"DolphinDB健康检查失败：{exc}"
        ) from exc
    # 条件门禁：判断`int(result) != 2`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if int(result) != 2:
        # 错误阻断：抛出`DailyFundsDolphinDBError(f'DolphinDB健康检查返回异常：{result!r}')`并停止当前正常路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
        # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
        raise DailyFundsDolphinDBError(
            f"DolphinDB健康检查返回异常：{result!r}"
        )
    # 结果返回：把`session`交给调用方并结束当前函数。
    # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return session


# 函数_to_bool：执行_to_bool对应的业务处理。
# - 输入：value:Any；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型bool；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
# - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def _to_bool(value: Any) -> bool:
    # 条件门禁：判断`isinstance(value, (bool, np.bool_))`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if isinstance(value, (bool, np.bool_)):
        # 结果返回：把`bool(value)`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return bool(value)
    # 条件门禁：判断`isinstance(value, (int, np.integer))`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if isinstance(value, (int, np.integer)):
        # 结果返回：把`bool(int(value))`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return bool(int(value))
    # 结果返回：把`str(value).strip().lower() in {'true', '1', 'yes'}`交给调用方并结束当前函数。
    # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return str(value).strip().lower() in {
        "true",
        "1",
        "yes",
    }


# 函数_default_runtime_info：执行_default_runtime_info对应的业务处理。
# - 输入：无外部业务参数；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型dict[str, Any]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
# - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def _default_runtime_info() -> dict[str, Any]:
    # 异常边界：尝试执行可能失败的解析、查询、文件或类型转换步骤，并由后续处理保留错误证据。
    # - 数据变化：正常路径产生业务结果；异常路径不得静默伪造数据，应抛出、记录或隔离。
    # - 为什么这样写：把外部环境故障与业务合同失败分开，便于重试、回滚和准确验收。
    try:
        # 状态计算：把`importlib.import_module('dolphindb')`的结果保存到`ddb`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        ddb = importlib.import_module("dolphindb")
        # 结果返回：把`{'python_client_version': str(getattr(ddb, '__version__', 'UNKNOWN')), 'table_appender_available': bool(getattr(ddb, 'T…`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return {
            "python_client_version": str(
                getattr(ddb, "__version__", "UNKNOWN")
            ),
            "table_appender_available": bool(
                getattr(ddb, "TableAppender", None)
                or getattr(ddb, "tableAppender", None)
            ),
        }
    except ImportError:
        # 结果返回：把`{'python_client_version': 'NOT_INSTALLED', 'table_appender_available': False}`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return {
            "python_client_version": "NOT_INSTALLED",
            "table_appender_available": False,
        }


# 函数probe_dolphindb_environment：只读探测服务器和目标数据库状态。
# - 输入：settings:DolphinDBWriteSettings、session_factory:SessionFactory、runtime_info_provider:Callable[[], dict[str, Any]]；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型dict[str, Any]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
# - 为什么这样写：把只读查询或来源发现步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def probe_dolphindb_environment(
    settings: DolphinDBWriteSettings,
    *,
    session_factory: SessionFactory = _default_session_factory,
    runtime_info_provider: Callable[
        [], dict[str, Any]
    ] = _default_runtime_info,
) -> dict[str, Any]:
    """只读探测服务器和目标数据库状态。"""
    # 状态计算：把`connect_session(settings, session_factory)`的结果保存到`session`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    session = connect_session(settings, session_factory)
    # 异常边界：尝试执行可能失败的解析、查询、文件或类型转换步骤，并由后续处理保留错误证据。
    # - 数据变化：正常路径产生业务结果；异常路径不得静默伪造数据，应抛出、记录或隔离。
    # - 为什么这样写：把外部环境故障与业务合同失败分开，便于重试、回滚和准确验收。
    try:
        # 状态计算：把`session.run('version()')`的结果保存到`server_version`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        server_version = session.run("version()")
    except Exception as exc:
        # 状态计算：把`f'UNAVAILABLE:{type(exc).__name__}:{exc}'`的结果保存到`server_version`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        server_version = f"UNAVAILABLE:{type(exc).__name__}:{exc}"

    # 状态计算：把`_to_bool(session.run(f'existsDatabase("{settings.database_uri}")'))`的结果保存到`database_exists`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    database_exists = _to_bool(
        session.run(
            f'existsDatabase("{settings.database_uri}")'
        )
    )
    # 状态计算：把`{}`的结果保存到`table_status`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    table_status: dict[str, bool] = {}
    # 循环处理：逐项遍历`TABLE_SCHEMAS`，把当前元素绑定到`table_name`。
    # - 数据变化：每轮只处理一个来源记录、字段、文件或证据项，并显式累计到局部集合或输出对象。
    # - 为什么这样写：逐项处理便于保留行级血缘、隔离单项异常，并控制16GB单机上的峰值内存。
    for table_name in TABLE_SCHEMAS:
        # 状态计算：把`_to_bool(session.run(f'existsTable("{settings.database_uri}", `{table_name})'))`的结果保存到`table_status[table_name]`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        table_status[table_name] = _to_bool(
            session.run(
                f'existsTable("{settings.database_uri}", '
                f"`{table_name})"
            )
        )

    # 状态计算：把`runtime_info_provider()`的结果保存到`runtime_info`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    runtime_info = runtime_info_provider()
    # 状态计算：把`runtime_info.get('python_client_version', 'UNKNOWN')`的结果保存到`client_version`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    client_version = runtime_info.get(
        "python_client_version",
        "UNKNOWN",
    )
    # 状态计算：把`bool(runtime_info.get('table_appender_available', False))`的结果保存到`appender_available`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    appender_available = bool(
        runtime_info.get(
            "table_appender_available",
            False,
        )
    )

    # 条件门禁：判断`not database_exists`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if not database_exists:
        # 状态计算：把`'READY_TO_CREATE'`的结果保存到`readiness`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        readiness = "READY_TO_CREATE"
    # 条件门禁：判断`all(table_status.values())`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    elif all(table_status.values()):
        # 状态计算：把`'READY_TO_VALIDATE_EXISTING_SCHEMA'`的结果保存到`readiness`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        readiness = "READY_TO_VALIDATE_EXISTING_SCHEMA"
    # 条件门禁：判断`any(table_status.values())`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    elif any(table_status.values()):
        # 状态计算：把`'REVIEW_PARTIAL_EXISTING_SCHEMA'`的结果保存到`readiness`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        readiness = "REVIEW_PARTIAL_EXISTING_SCHEMA"
    else:
        # 状态计算：把`'READY_TO_CREATE_TABLES_IN_EXISTING_DB'`的结果保存到`readiness`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        readiness = "READY_TO_CREATE_TABLES_IN_EXISTING_DB"

    # 结果返回：把`{'task_id': 'TASK_016B', 'mode': 'PROBE', 'generated_at': datetime.now(timezone.utc).isoformat(), 'host': settings.host…`交给调用方并结束当前函数。
    # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return {
        "task_id": "TASK_016B",
        "mode": "PROBE",
        "generated_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "host": settings.host,
        "port": settings.port,
        "username": settings.username,
        "database_uri": settings.database_uri,
        "server_version": str(server_version),
        "python_client_version": str(client_version),
        "pandas_version": pd.__version__,
        "numpy_version": np.__version__,
        "table_appender_available": appender_available,
        "database_exists": database_exists,
        "target_table_status": table_status,
        "readiness": readiness,
        "overall_status": (
            "PASSED"
            if appender_available
            and readiness
            != "REVIEW_PARTIAL_EXISTING_SCHEMA"
            else "REVIEW_REQUIRED"
        ),
        "safety": [
            "本次PROBE只执行健康检查、版本查询和exists检查。",
            "未创建、删除或修改数据库和表。",
            "未读取或写入本地日线资金源文件。",
        ],
    }


# 函数_normalize_coldefs：执行_normalize_coldefs对应的业务处理。
# - 输入：result:Any；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型list[dict[str, str]]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
# - 为什么这样写：把对象构造、字段映射或标准化转换步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def _normalize_coldefs(result: Any) -> list[dict[str, str]]:
    # 条件门禁：判断`result is None`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if result is None:
        # 结果返回：把`[]`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return []
    # 条件门禁：判断`isinstance(result, list)`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if isinstance(result, list):
        # 状态计算：把`result`的结果保存到`rows`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        rows = result
    else:
        # 状态计算：把`getattr(result, 'to_dict', None)`的结果保存到`to_dict`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        to_dict = getattr(result, "to_dict", None)
        # 条件门禁：判断`not callable(to_dict)`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if not callable(to_dict):
            # 错误阻断：抛出`DailyFundsDolphinDBError('无法解析DolphinDB schema.colDefs返回值。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
            raise DailyFundsDolphinDBError(
                "无法解析DolphinDB schema.colDefs返回值。"
            )
        # 异常边界：尝试执行可能失败的解析、查询、文件或类型转换步骤，并由后续处理保留错误证据。
        # - 数据变化：正常路径产生业务结果；异常路径不得静默伪造数据，应抛出、记录或隔离。
        # - 为什么这样写：把外部环境故障与业务合同失败分开，便于重试、回滚和准确验收。
        try:
            # 状态计算：把`to_dict(orient='records')`的结果保存到`rows`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            rows = to_dict(orient="records")
        except TypeError:
            # 状态计算：把`to_dict('records')`的结果保存到`rows`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            rows = to_dict("records")
    # 状态计算：把`[]`的结果保存到`normalized`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    normalized: list[dict[str, str]] = []
    # 循环处理：逐项遍历`rows`，把当前元素绑定到`row`。
    # - 数据变化：每轮只处理一个来源记录、字段、文件或证据项，并显式累计到局部集合或输出对象。
    # - 为什么这样写：逐项处理便于保留行级血缘、隔离单项异常，并控制16GB单机上的峰值内存。
    for row in rows:
        # 条件门禁：判断`not isinstance(row, dict)`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if not isinstance(row, dict):
            # 错误阻断：抛出`DailyFundsDolphinDBError('schema.colDefs包含非字典行。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
            raise DailyFundsDolphinDBError(
                "schema.colDefs包含非字典行。"
            )
        # 显式调用：执行`normalized.append({'name': str(row.get('name', '')), 'typeString': str(row.get('typeString', row.get('type', ''))).upper()})`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
        # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
        # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
        normalized.append(
            {
                "name": str(row.get("name", "")),
                "typeString": str(
                    row.get(
                        "typeString",
                        row.get("type", ""),
                    )
                ).upper(),
            }
        )
    # 结果返回：把`normalized`交给调用方并结束当前函数。
    # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return normalized


# 函数inspect_existing_table_schema：执行inspect_existing_table_schema对应的业务处理。
# - 输入：session:SessionProtocol、database_uri:str、table_name:str；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型list[dict[str, str]]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
# - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def inspect_existing_table_schema(
    session: SessionProtocol,
    database_uri: str,
    table_name: str,
) -> list[dict[str, str]]:
    # 显式调用：执行`_validate_identifier(table_name)`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
    # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
    # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
    _validate_identifier(table_name)
    # 状态计算：把`f'schema(loadTable("{database_uri}", `{table_name})).colDefs'`的结果保存到`script`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    script = (
        f'schema(loadTable("{database_uri}", '
        f"`{table_name})).colDefs"
    )
    # 结果返回：把`_normalize_coldefs(session.run(script))`交给调用方并结束当前函数。
    # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return _normalize_coldefs(session.run(script))


# 函数validate_remote_table_schemas：校验所有目标表字段名和类型。
# - 输入：session:SessionProtocol、database_uri:str；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型dict[str, Any]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
# - 为什么这样写：把合同、数据质量或安全门禁校验步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def validate_remote_table_schemas(
    session: SessionProtocol,
    database_uri: str,
) -> dict[str, Any]:
    """校验所有目标表字段名和类型。"""
    # 状态计算：把`[]`的结果保存到`issues`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    issues: list[dict[str, Any]] = []
    # 状态计算：把`{}`的结果保存到`tables`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    tables: dict[str, Any] = {}
    # 循环处理：逐项遍历`TABLE_SCHEMAS.items()`，把当前元素绑定到`(table_name, expected_columns)`。
    # - 数据变化：每轮只处理一个来源记录、字段、文件或证据项，并显式累计到局部集合或输出对象。
    # - 为什么这样写：逐项处理便于保留行级血缘、隔离单项异常，并控制16GB单机上的峰值内存。
    for table_name, expected_columns in TABLE_SCHEMAS.items():
        # 状态计算：把`_to_bool(session.run(f'existsTable("{database_uri}", `{table_name})'))`的结果保存到`exists`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        exists = _to_bool(
            session.run(
                f'existsTable("{database_uri}", `{table_name})'
            )
        )
        # 条件门禁：判断`not exists`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if not exists:
            # 显式调用：执行`issues.append({'severity': 'ERROR', 'code': 'TABLE_MISSING', 'table_name': table_name})`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
            # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
            # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
            issues.append(
                {
                    "severity": "ERROR",
                    "code": "TABLE_MISSING",
                    "table_name": table_name,
                }
            )
            # 状态计算：把`{'exists': False, 'column_count': 0}`的结果保存到`tables[table_name]`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            tables[table_name] = {
                "exists": False,
                "column_count": 0,
            }
            # 控制流：跳过本轮剩余步骤，使循环或占位分支按既定合同继续。
            # - 数据变化：本语句不直接改变业务记录，只调整当前执行路径。
            # - 为什么这样写：显式控制流比隐式嵌套更容易检查边界和异常处理。
            continue

        # 状态计算：把`inspect_existing_table_schema(session, database_uri, table_name)`的结果保存到`actual`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        actual = inspect_existing_table_schema(
            session,
            database_uri,
            table_name,
        )
        # 状态计算：把`[{'name': name, 'typeString': data_type} for name, data_type in expected_columns]`的结果保存到`expected`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        expected = [
            {"name": name, "typeString": data_type}
            for name, data_type in expected_columns
        ]
        # 状态计算：把`{'exists': True, 'column_count': len(actual), 'actual_columns': actual}`的结果保存到`tables[table_name]`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        tables[table_name] = {
            "exists": True,
            "column_count": len(actual),
            "actual_columns": actual,
        }
        # 条件门禁：判断`actual != expected`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if actual != expected:
            # 显式调用：执行`issues.append({'severity': 'ERROR', 'code': 'TABLE_SCHEMA_MISMATCH', 'table_name': table_name, 'expected': expected, 'actual': actual})`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
            # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
            # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
            issues.append(
                {
                    "severity": "ERROR",
                    "code": "TABLE_SCHEMA_MISMATCH",
                    "table_name": table_name,
                    "expected": expected,
                    "actual": actual,
                }
            )

    # 结果返回：把`{'database_uri': database_uri, 'table_count': len(TABLE_SCHEMAS), 'overall_status': 'PASSED' if not issues else 'FAILED…`交给调用方并结束当前函数。
    # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return {
        "database_uri": database_uri,
        "table_count": len(TABLE_SCHEMAS),
        "overall_status": (
            "PASSED"
            if not issues
            else "FAILED"
        ),
        "issues": issues,
        "tables": tables,
    }


# 函数create_database_and_tables：创建缺失对象，不删除、不覆盖已有对象。
# - 输入：settings:DolphinDBWriteSettings、session_factory:SessionFactory；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型dict[str, Any]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：该函数名称涉及写入能力，只有调用方显式进入受控模式时才可能产生数据库或文件副作用；注释迁移和验证不会调用它。
# - 为什么这样写：把显式写入或持久化步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def create_database_and_tables(
    settings: DolphinDBWriteSettings,
    *,
    session_factory: SessionFactory = _default_session_factory,
) -> dict[str, Any]:
    """创建缺失对象，不删除、不覆盖已有对象。"""
    # 状态计算：把`connect_session(settings, session_factory)`的结果保存到`session`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    session = connect_session(settings, session_factory)

    # 状态计算：把`probe_dolphindb_environment(settings, session_factory=lambda: _ConnectedSessionProxy(session))`的结果保存到`before`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    before = probe_dolphindb_environment(
        settings,
        session_factory=lambda: _ConnectedSessionProxy(session),
    )
    # 条件门禁：判断`before['readiness'] == 'REVIEW_PARTIAL_EXISTING_SCHEMA'`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if before["readiness"] == "REVIEW_PARTIAL_EXISTING_SCHEMA":
        # 错误阻断：抛出`DailyFundsDolphinDBError('目标数据库中只有部分目标表。为避免覆盖未知结构，本次拒绝自动创建。')`并停止当前正常路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
        # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
        raise DailyFundsDolphinDBError(
            "目标数据库中只有部分目标表。"
            "为避免覆盖未知结构，本次拒绝自动创建。"
        )

    # 状态计算：把`build_create_database_script(settings.database_uri)`的结果保存到`ddl`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    ddl = build_create_database_script(
        settings.database_uri
    )
    # 异常边界：尝试执行可能失败的解析、查询、文件或类型转换步骤，并由后续处理保留错误证据。
    # - 数据变化：正常路径产生业务结果；异常路径不得静默伪造数据，应抛出、记录或隔离。
    # - 为什么这样写：把外部环境故障与业务合同失败分开，便于重试、回滚和准确验收。
    try:
        # 状态计算：把`session.run(ddl)`的结果保存到`ddl_result`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        ddl_result = session.run(ddl)
    except Exception as exc:
        # 错误阻断：抛出`DailyFundsDolphinDBError(f'DolphinDB建库建表失败：{exc}')`并停止当前正常路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
        # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
        raise DailyFundsDolphinDBError(
            f"DolphinDB建库建表失败：{exc}"
        ) from exc

    # 状态计算：把`validate_remote_table_schemas(session, settings.database_uri)`的结果保存到`schema_validation`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    schema_validation = validate_remote_table_schemas(
        session,
        settings.database_uri,
    )
    # 条件门禁：判断`schema_validation['overall_status'] != 'PASSED'`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if schema_validation["overall_status"] != "PASSED":
        # 错误阻断：抛出`DailyFundsDolphinDBError(f"建库建表后Schema验证失败：{schema_validation['issues']}")`并停止当前正常路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
        # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
        raise DailyFundsDolphinDBError(
            "建库建表后Schema验证失败："
            f"{schema_validation['issues']}"
        )

    # 结果返回：把`{'task_id': 'TASK_016B', 'mode': 'CREATE', 'generated_at': datetime.now(timezone.utc).isoformat(), 'database_uri': sett…`交给调用方并结束当前函数。
    # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return {
        "task_id": "TASK_016B",
        "mode": "CREATE",
        "generated_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "database_uri": settings.database_uri,
        "before": before,
        "ddl_result": _json_safe(ddl_result),
        "schema_validation": schema_validation,
        "overall_status": "PASSED",
        "safety": [
            "只创建不存在的数据库或表。",
            "未调用dropDatabase或dropTable。",
            "已有部分目标表时拒绝自动继续。",
            "创建后逐表验证字段名和类型。",
        ],
    }


# 类_ConnectedSessionProxy：让probe复用已连接会话而不重复连接。
# - 结构：继承或实现object；类体约包含0个字段或常量、3个方法。
# - 数据变化：类定义阶段不执行隐式I/O，实例只在构造或显式方法调用时改变受控状态。
# - 实操：调用方通过该类型集中传递配置、记录、服务或结果，避免跨模块使用无约束字典。
# - 为什么这样写：强类型边界能集中维护单位、时点、主键和安全不变量，并降低供应商耦合。
class _ConnectedSessionProxy:
    """让probe复用已连接会话而不重复连接。"""

    # 函数__init__：执行__init__对应的业务处理。
    # - 输入：session:SessionProtocol；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型None；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    def __init__(self, session: SessionProtocol) -> None:
        # 状态计算：把`session`的结果保存到`self._session`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        self._session = session

    # 函数connect：执行connect对应的业务处理。
    # - 输入：host:str、port:int、user_id:str、password:str；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型bool；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    def connect(
        self,
        host: str,
        port: int,
        user_id: str,
        password: str,
    ) -> bool:
        # 结果返回：把`True`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return True

    # 函数run：执行run对应的业务处理。
    # - 输入：script:str；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型Any；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把任务入口与流程编排步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    def run(self, script: str) -> Any:
        # 结果返回：把`self._session.run(script)`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return self._session.run(script)


# 函数load_normalized_file_rows：再次严格解析一个READY文件并返回全部标准化Raw行。
# - 输入：file_path:Path、dataset:DatasetSpec、contract:DailyFundsContract、ingest_batch_id:str、ingested_at:datetime；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型list[dict[str, Any]]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
# - 为什么这样写：把只读查询或来源发现步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def load_normalized_file_rows(
    *,
    file_path: Path,
    dataset: DatasetSpec,
    contract: DailyFundsContract,
    ingest_batch_id: str,
    ingested_at: datetime,
) -> list[dict[str, Any]]:
    """再次严格解析一个READY文件并返回全部标准化Raw行。"""
    # 状态计算：把`parse_snapshot_date_from_path(file_path)`的结果保存到`snapshot_date`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    snapshot_date = parse_snapshot_date_from_path(file_path)
    # 状态计算：把`file_sha256(file_path)`的结果保存到`source_hash`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    source_hash = file_sha256(file_path)
    # 状态计算：把`contract.schema_index()`的结果保存到`schema_index`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    schema_index = contract.schema_index()

    # 状态计算：把`iter_source_rows(file_path, encoding=contract.source_encoding, delimiter=contract.source_delimiter)`的结果保存到`iterator`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    iterator = iter_source_rows(
        file_path,
        encoding=contract.source_encoding,
        delimiter=contract.source_delimiter,
    )
    # 异常边界：尝试执行可能失败的解析、查询、文件或类型转换步骤，并由后续处理保留错误证据。
    # - 数据变化：正常路径产生业务结果；异常路径不得静默伪造数据，应抛出、记录或隔离。
    # - 为什么这样写：把外部环境故障与业务合同失败分开，便于重试、回滚和准确验收。
    try:
        # 状态计算：把`next(iterator)`的结果保存到`(_, header_cells)`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        _, header_cells = next(iterator)
    except StopIteration as exc:
        # 错误阻断：抛出`DailyFundsDolphinDBError(f'空文件：{file_path}')`并停止当前正常路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
        # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
        raise DailyFundsDolphinDBError(
            f"空文件：{file_path}"
        ) from exc

    # 状态计算：把`_trim_trailing_delimiter_cell(header_cells)`的结果保存到`header_cells`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    header_cells = _trim_trailing_delimiter_cell(
        header_cells
    )
    # 状态计算：把`header_fingerprint(header_cells)`的结果保存到`exact_hash`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    exact_hash = header_fingerprint(header_cells)
    # 状态计算：把`schema_index.get((dataset.dataset_id, exact_hash))`的结果保存到`known_schema`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    known_schema = schema_index.get(
        (dataset.dataset_id, exact_hash)
    )
    # 条件门禁：判断`known_schema is None`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if known_schema is None:
        # 错误阻断：抛出`DailyFundsDolphinDBError(f'未知Schema：{dataset.dataset_id}/{exact_hash}')`并停止当前正常路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
        # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
        raise DailyFundsDolphinDBError(
            f"未知Schema：{dataset.dataset_id}/{exact_hash}"
        )

    # 状态计算：把`list(known_schema.headers)`的结果保存到`expected_header`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    expected_header = list(known_schema.headers)
    # 状态计算：把`deduplicate_headers(expected_header)`的结果保存到`deduplicated_header`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    deduplicated_header = deduplicate_headers(
        expected_header
    )
    # 状态计算：把`len(expected_header)`的结果保存到`expected_length`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    expected_length = len(expected_header)
    # 状态计算：把`[]`的结果保存到`rows`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    rows: list[dict[str, Any]] = []

    # 循环处理：逐项遍历`iterator`，把当前元素绑定到`(physical_line_number, raw_cells)`。
    # - 数据变化：每轮只处理一个来源记录、字段、文件或证据项，并显式累计到局部集合或输出对象。
    # - 为什么这样写：逐项处理便于保留行级血缘、隔离单项异常，并控制16GB单机上的峰值内存。
    for physical_line_number, raw_cells in iterator:
        # 状态计算：把`_trim_trailing_delimiter_cell(raw_cells, expected_length=expected_length)`的结果保存到`cells`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        cells = _trim_trailing_delimiter_cell(
            raw_cells,
            expected_length=expected_length,
        )
        # 条件门禁：判断`not cells or all((strip_cell(item) == '' for item in cells))`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if not cells or all(
            strip_cell(item) == "" for item in cells
        ):
            # 控制流：跳过本轮剩余步骤，使循环或占位分支按既定合同继续。
            # - 数据变化：本语句不直接改变业务记录，只调整当前执行路径。
            # - 为什么这样写：显式控制流比隐式嵌套更容易检查边界和异常处理。
            continue
        # 条件门禁：判断`len(cells) != expected_length`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if len(cells) != expected_length:
            # 错误阻断：抛出`DailyFundsDolphinDBError(f'再次解析发现畸形行：{file_path}, line={physical_line_number}, expected={expected_length}, actual={len(…`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
            raise DailyFundsDolphinDBError(
                "再次解析发现畸形行："
                f"{file_path}, line={physical_line_number}, "
                f"expected={expected_length}, actual={len(cells)}"
            )
        # 状态计算：把`{deduplicated_header[index]: strip_cell(value) for index, value in enumerate(cells)}`的结果保存到`raw_row`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        raw_row = {
            deduplicated_header[index]: strip_cell(value)
            for index, value in enumerate(cells)
        }
        # 异常边界：尝试执行可能失败的解析、查询、文件或类型转换步骤，并由后续处理保留错误证据。
        # - 数据变化：正常路径产生业务结果；异常路径不得静默伪造数据，应抛出、记录或隔离。
        # - 为什么这样写：把外部环境故障与业务合同失败分开，便于重试、回滚和准确验收。
        try:
            # 状态计算：把`normalize_row(raw_row, dataset=dataset, snapshot_date=snapshot_date, source_file=file_path, source_…`的结果保存到`normalized`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            normalized = normalize_row(
                raw_row,
                dataset=dataset,
                snapshot_date=snapshot_date,
                source_file=file_path,
                source_file_hash=source_hash,
                schema_version=known_schema.schema_version,
                source_row_number=physical_line_number - 1,
                ingest_batch_id=ingest_batch_id,
                ingested_at=ingested_at,
                missing_tokens=contract.missing_tokens,
            )
        except Exception as exc:
            # 错误阻断：抛出`DailyFundsDolphinDBError(f'再次解析标准化失败：{file_path}, line={physical_line_number}, {type(exc).__name__}: {exc}')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
            raise DailyFundsDolphinDBError(
                "再次解析标准化失败："
                f"{file_path}, line={physical_line_number}, "
                f"{type(exc).__name__}: {exc}"
            ) from exc
        # 显式调用：执行`rows.append(normalized)`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
        # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
        # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
        rows.append(normalized)

    # 结果返回：把`rows`交给调用方并结束当前函数。
    # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return rows


# 函数prepare_dataframe：按目标DolphinDB类型准备DataFrame。
# - 输入：rows:Sequence[dict[str, Any]]、columns:Sequence[tuple[str, str]]；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型pd.DataFrame；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
# - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def prepare_dataframe(
    rows: Sequence[dict[str, Any]],
    columns: Sequence[tuple[str, str]],
) -> pd.DataFrame:
    """按目标DolphinDB类型准备DataFrame。"""
    # 状态计算：把`[name for name, _ in columns]`的结果保存到`names`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    names = [name for name, _ in columns]
    # 状态计算：把`pd.DataFrame([{name: row.get(name) for name in names} for row in rows], columns=names)`的结果保存到`frame`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    frame = pd.DataFrame(
        [{name: row.get(name) for name in names} for row in rows],
        columns=names,
    )
    # 循环处理：逐项遍历`columns`，把当前元素绑定到`(name, data_type)`。
    # - 数据变化：每轮只处理一个来源记录、字段、文件或证据项，并显式累计到局部集合或输出对象。
    # - 为什么这样写：逐项处理便于保留行级血缘、隔离单项异常，并控制16GB单机上的峰值内存。
    for name, data_type in columns:
        # 条件门禁：判断`data_type == 'DATE'`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if data_type == "DATE":
            # 状态计算：把`pd.to_datetime(frame[name], errors='raise').values.astype('datetime64[D]')`的结果保存到`frame[name]`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            frame[name] = pd.to_datetime(
                frame[name],
                errors="raise",
            ).values.astype("datetime64[D]")
        # 条件门禁：判断`data_type == 'MONTH'`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        elif data_type == "MONTH":
            # 状态计算：把`pd.to_datetime(frame[name], errors='raise').values.astype('datetime64[M]')`的结果保存到`frame[name]`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            frame[name] = pd.to_datetime(
                frame[name],
                errors="raise",
            ).values.astype("datetime64[M]")
        # 条件门禁：判断`data_type == 'TIMESTAMP'`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        elif data_type == "TIMESTAMP":
            # 状态计算：把`pd.to_datetime(frame[name], errors='raise', utc=True)`的结果保存到`parsed`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            parsed = pd.to_datetime(
                frame[name],
                errors="raise",
                utc=True,
            )
            # 状态计算：把`parsed.dt.tz_convert(None).astype('datetime64[ns]')`的结果保存到`frame[name]`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            frame[name] = parsed.dt.tz_convert(
                None
            ).astype("datetime64[ns]")
        # 条件门禁：判断`data_type == 'INT'`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        elif data_type == "INT":
            # 状态计算：把`pd.to_numeric(frame[name], errors='coerce').astype('Int32')`的结果保存到`frame[name]`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            frame[name] = pd.to_numeric(
                frame[name],
                errors="coerce",
            ).astype("Int32")
        # 条件门禁：判断`data_type == 'LONG'`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        elif data_type == "LONG":
            # 状态计算：把`pd.to_numeric(frame[name], errors='coerce').astype('Int64')`的结果保存到`frame[name]`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            frame[name] = pd.to_numeric(
                frame[name],
                errors="coerce",
            ).astype("Int64")
        # 条件门禁：判断`data_type == 'DOUBLE'`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        elif data_type == "DOUBLE":
            # 状态计算：把`pd.to_numeric(frame[name], errors='coerce').astype('float64')`的结果保存到`frame[name]`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            frame[name] = pd.to_numeric(
                frame[name],
                errors="coerce",
            ).astype("float64")
        # 条件门禁：判断`data_type in {'STRING', 'SYMBOL'}`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        elif data_type in {"STRING", "SYMBOL"}:
            # 状态计算：把`frame[name].where(frame[name].notna(), None)`的结果保存到`frame[name]`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            frame[name] = frame[name].where(
                frame[name].notna(),
                None,
            )
    # 结果返回：把`frame`交给调用方并结束当前函数。
    # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return frame


# 函数decide_file_write_action：根据已存在行数决定幂等动作。
# - 输入：existing_count:int、expected_count:int；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型str；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：该函数名称涉及写入能力，只有调用方显式进入受控模式时才可能产生数据库或文件副作用；注释迁移和验证不会调用它。
# - 为什么这样写：把显式写入或持久化步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def decide_file_write_action(
    existing_count: int,
    expected_count: int,
) -> str:
    """根据已存在行数决定幂等动作。"""
    # 条件门禁：判断`existing_count < 0 or expected_count < 0`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if existing_count < 0 or expected_count < 0:
        # 错误阻断：抛出`DailyFundsDolphinDBError('行数不能为负数。')`并停止当前正常路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
        # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
        raise DailyFundsDolphinDBError(
            "行数不能为负数。"
        )
    # 条件门禁：判断`existing_count == expected_count`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if existing_count == expected_count:
        # 结果返回：把`'SKIP_IDEMPOTENT'`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return "SKIP_IDEMPOTENT"
    # 条件门禁：判断`existing_count == 0`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if existing_count == 0:
        # 结果返回：把`'WRITE_NEW'`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return "WRITE_NEW"
    # 结果返回：把`'RECOVER_PARTIAL'`交给调用方并结束当前函数。
    # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return "RECOVER_PARTIAL"


# 函数_count_file_rows：执行_count_file_rows对应的业务处理。
# - 输入：session:SessionProtocol、database_uri:str、table_name:str、dataset_id:str、source_file_sha256:str；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型int；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
# - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def _count_file_rows(
    session: SessionProtocol,
    database_uri: str,
    table_name: str,
    dataset_id: str,
    source_file_sha256: str,
) -> int:
    # 状态计算：把`f'exec count(*) from loadTable("{database_uri}", `{table_name}) where dataset_id={_symbol_literal(d…`的结果保存到`script`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    script = (
        "exec count(*) from "
        f'loadTable("{database_uri}", `{table_name}) '
        f"where dataset_id={_symbol_literal(dataset_id)} "
        f"and source_file_sha256="
        f"{_symbol_literal(source_file_sha256)}"
    )
    # 状态计算：把`session.run(script)`的结果保存到`result`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    result = session.run(script)
    # 结果返回：把`int(result)`交给调用方并结束当前函数。
    # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return int(result)


# 函数_count_table_rows：执行_count_table_rows对应的业务处理。
# - 输入：session:SessionProtocol、database_uri:str、table_name:str；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型int；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
# - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def _count_table_rows(
    session: SessionProtocol,
    database_uri: str,
    table_name: str,
) -> int:
    # 状态计算：把`session.run(f'exec count(*) from loadTable("{database_uri}", `{table_name})')`的结果保存到`result`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    result = session.run(
        "exec count(*) from "
        f'loadTable("{database_uri}", `{table_name})'
    )
    # 结果返回：把`int(result)`交给调用方并结束当前函数。
    # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return int(result)


# 函数_append_rows：执行_append_rows对应的业务处理。
# - 输入：database_uri:str、table_name:str、session:SessionProtocol、rows:Sequence[dict[str, Any]]、appender_factory:AppenderFactory；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型int；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：该函数名称涉及写入能力，只有调用方显式进入受控模式时才可能产生数据库或文件副作用；注释迁移和验证不会调用它。
# - 为什么这样写：把显式写入或持久化步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def _append_rows(
    *,
    database_uri: str,
    table_name: str,
    session: SessionProtocol,
    rows: Sequence[dict[str, Any]],
    appender_factory: AppenderFactory,
) -> int:
    # 条件门禁：判断`not rows`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if not rows:
        # 结果返回：把`0`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return 0
    # 状态计算：把`prepare_dataframe(rows, TABLE_SCHEMAS[table_name])`的结果保存到`frame`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    frame = prepare_dataframe(
        rows,
        TABLE_SCHEMAS[table_name],
    )
    # 状态计算：把`appender_factory(database_uri, table_name, session)`的结果保存到`appender`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    appender = appender_factory(
        database_uri,
        table_name,
        session,
    )
    # 状态计算：把`appender.append(frame)`的结果保存到`result`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    result = appender.append(frame)
    # 条件门禁：判断`isinstance(result, (int, np.integer))`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if isinstance(result, (int, np.integer)):
        # 结果返回：把`int(result)`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return int(result)
    # 结果返回：把`len(frame)`交给调用方并结束当前函数。
    # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return len(frame)


# 函数_read_csv：执行_read_csv对应的业务处理。
# - 输入：path:Path；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型list[dict[str, str]]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
# - 为什么这样写：把只读查询或来源发现步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def _read_csv(path: Path) -> list[dict[str, str]]:
    # 资源上下文：在`path.open('r', encoding='utf-8-sig', newline='')`管理的生命周期内执行后续代码。
    # - 数据变化：上下文负责成对获取和释放文件、会话或临时资源，异常时仍执行清理。
    # - 为什么这样写：显式资源边界可避免连接、文件句柄或临时状态泄漏。
    with path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as handle:
        # 结果返回：把`list(csv.DictReader(handle))`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return list(csv.DictReader(handle))


# 函数_write_json：执行_write_json对应的业务处理。
# - 输入：path:Path、payload:Any；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型None；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：该函数名称涉及写入能力，只有调用方显式进入受控模式时才可能产生数据库或文件副作用；注释迁移和验证不会调用它。
# - 为什么这样写：把显式写入或持久化步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def _write_json(path: Path, payload: Any) -> None:
    # 显式调用：执行`path.write_text(json.dumps(_json_safe(payload), ensure_ascii=False, indent=2), encoding='utf-8')`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
    # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
    # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
    path.write_text(
        json.dumps(
            _json_safe(payload),
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


# 函数_json_safe：执行_json_safe对应的业务处理。
# - 输入：value:Any；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型Any；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
# - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def _json_safe(value: Any) -> Any:
    # 条件门禁：判断`isinstance(value, dict)`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if isinstance(value, dict):
        # 结果返回：把`{str(key): _json_safe(item) for key, item in value.items()}`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return {
            str(key): _json_safe(item)
            for key, item in value.items()
        }
    # 条件门禁：判断`isinstance(value, (list, tuple, set))`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if isinstance(value, (list, tuple, set)):
        # 结果返回：把`[_json_safe(item) for item in value]`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return [_json_safe(item) for item in value]
    # 条件门禁：判断`isinstance(value, (datetime, Path))`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if isinstance(value, (datetime, Path)):
        # 结果返回：把`str(value)`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return str(value)
    # 条件门禁：判断`isinstance(value, (np.integer,))`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if isinstance(value, (np.integer,)):
        # 结果返回：把`int(value)`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return int(value)
    # 条件门禁：判断`isinstance(value, (np.floating,))`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if isinstance(value, (np.floating,)):
        # 结果返回：把`float(value)`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return float(value)
    # 条件门禁：判断`isinstance(value, pd.DataFrame)`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if isinstance(value, pd.DataFrame):
        # 结果返回：把`value.to_dict(orient='records')`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return value.to_dict(orient="records")
    # 结果返回：把`value`交给调用方并结束当前函数。
    # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return value


# 函数_batch_log_row：执行_batch_log_row对应的业务处理。
# - 输入：batch_id:str、now:datetime、status:str、root:Path、contract_version:str、preflight:dict[str, Any]、inserted_row_count:int、skipped_row_count:int等；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型dict[str, Any]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
# - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def _batch_log_row(
    *,
    batch_id: str,
    now: datetime,
    status: str,
    root: Path,
    contract_version: str,
    preflight: dict[str, Any],
    inserted_row_count: int,
    skipped_row_count: int,
    failed_file_count: int,
    message: str,
) -> dict[str, Any]:
    # 结果返回：把`{'ingest_batch_id': batch_id, 'batch_month': now.strftime('%Y-%m'), 'logged_at': now.isoformat(), 'status': status, 'sc…`交给调用方并结束当前函数。
    # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return {
        "ingest_batch_id": batch_id,
        "batch_month": now.strftime("%Y-%m"),
        "logged_at": now.isoformat(),
        "status": status,
        "scan_root": str(root),
        "contract_version": contract_version,
        "preflight_status": str(
            preflight.get("overall_status", "")
        ),
        "source_file_count": int(
            preflight.get("profiled_file_count", 0)
        ),
        "ready_file_count": int(
            preflight.get("ready_file_count", 0)
        ),
        "quarantined_file_count": int(
            preflight.get("quarantined_file_count", 0)
        ),
        "blocked_file_count": int(
            preflight.get("blocked_file_count", 0)
        ),
        "planned_row_count": int(
            preflight.get("planned_insert_row_count", 0)
        ),
        "inserted_row_count": inserted_row_count,
        "skipped_row_count": skipped_row_count,
        "failed_file_count": failed_file_count,
        "message": message,
    }


# 函数_coverage_index：执行_coverage_index对应的业务处理。
# - 输入：coverage_rows:Sequence[dict[str, str]]；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型dict[tuple[str, str], dict[str, str]]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
# - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def _coverage_index(
    coverage_rows: Sequence[dict[str, str]],
) -> dict[tuple[str, str], dict[str, str]]:
    # 结果返回：把`{(row['snapshot_date'], row['dataset_id']): row for row in coverage_rows}`交给调用方并结束当前函数。
    # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return {
        (
            row["snapshot_date"],
            row["dataset_id"],
        ): row
        for row in coverage_rows
    }


# 函数run_daily_funds_import：执行真实导入；调用前必须已经创建并验证表。
# - 输入：settings:DolphinDBWriteSettings、root:Path、contract_path:Path、output_dir:Path、expected_planned_row_count:int | None、session_factory:SessionFactory、appender_factory:AppenderFactory；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型dict[str, Any]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：该函数名称涉及写入能力，只有调用方显式进入受控模式时才可能产生数据库或文件副作用；注释迁移和验证不会调用它。
# - 为什么这样写：把显式写入或持久化步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def run_daily_funds_import(
    *,
    settings: DolphinDBWriteSettings,
    root: Path,
    contract_path: Path,
    output_dir: Path,
    expected_planned_row_count: int | None = None,
    session_factory: SessionFactory = _default_session_factory,
    appender_factory: AppenderFactory = _default_appender_factory,
) -> dict[str, Any]:
    """执行真实导入；调用前必须已经创建并验证表。"""
    # 显式调用：执行`output_dir.mkdir(parents=True, exist_ok=True)`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
    # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
    # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
    output_dir.mkdir(parents=True, exist_ok=True)
    # 状态计算：把`datetime.now(timezone.utc)`的结果保存到`started_at`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    started_at = datetime.now(timezone.utc)
    # 状态计算：把`'task016b_' + started_at.strftime('%Y%m%dT%H%M%S%fZ')`的结果保存到`batch_id`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    batch_id = (
        "task016b_"
        + started_at.strftime("%Y%m%dT%H%M%S%fZ")
    )

    # 状态计算：把`output_dir / 'preflight'`的结果保存到`preflight_dir`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    preflight_dir = output_dir / "preflight"
    # 状态计算：把`run_daily_funds_preflight(root=root, contract_path=contract_path, output_dir=preflight_dir, generat…`的结果保存到`preflight`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    preflight = run_daily_funds_preflight(
        root=root,
        contract_path=contract_path,
        output_dir=preflight_dir,
        generated_at=started_at,
    )
    # 条件门禁：判断`preflight['overall_status'] not in {'READY', 'READY_WITH_QUARANTINE'}`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if preflight["overall_status"] not in {
        "READY",
        "READY_WITH_QUARANTINE",
    }:
        # 错误阻断：抛出`DailyFundsDolphinDBError(f"TASK_016A重跑未通过，拒绝写入：{preflight['overall_status']}")`并停止当前正常路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
        # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
        raise DailyFundsDolphinDBError(
            "TASK_016A重跑未通过，拒绝写入："
            f"{preflight['overall_status']}"
        )
    # 状态计算：把`int(preflight['planned_insert_row_count'])`的结果保存到`planned_count`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    planned_count = int(
        preflight["planned_insert_row_count"]
    )
    # 条件门禁：判断`expected_planned_row_count is not None and planned_count != expected_planned_row_count`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if (
        expected_planned_row_count is not None
        and planned_count != expected_planned_row_count
    ):
        # 错误阻断：抛出`DailyFundsDolphinDBError(f'计划写入行数发生变化，拒绝写入：expected={expected_planned_row_count}, actual={planned_count}')`并停止当前正常路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
        # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
        raise DailyFundsDolphinDBError(
            "计划写入行数发生变化，拒绝写入："
            f"expected={expected_planned_row_count}, "
            f"actual={planned_count}"
        )

    # 状态计算：把`load_daily_funds_contract(contract_path)`的结果保存到`contract`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    contract = load_daily_funds_contract(contract_path)
    # 状态计算：把`connect_session(settings, session_factory)`的结果保存到`session`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    session = connect_session(settings, session_factory)
    # 状态计算：把`validate_remote_table_schemas(session, settings.database_uri)`的结果保存到`remote_validation`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    remote_validation = validate_remote_table_schemas(
        session,
        settings.database_uri,
    )
    # 条件门禁：判断`remote_validation['overall_status'] != 'PASSED'`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if remote_validation["overall_status"] != "PASSED":
        # 错误阻断：抛出`DailyFundsDolphinDBError(f"远端表结构未通过验收，拒绝写入：{remote_validation['issues']}")`并停止当前正常路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
        # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
        raise DailyFundsDolphinDBError(
            "远端表结构未通过验收，拒绝写入："
            f"{remote_validation['issues']}"
        )

    # 状态计算：把`_read_csv(preflight_dir / 'task_016a_file_results.csv')`的结果保存到`file_rows`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    file_rows = _read_csv(
        preflight_dir / "task_016a_file_results.csv"
    )
    # 状态计算：把`_read_csv(preflight_dir / 'task_016a_coverage_checks.csv')`的结果保存到`coverage_rows`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    coverage_rows = _read_csv(
        preflight_dir / "task_016a_coverage_checks.csv"
    )
    # 状态计算：把`_coverage_index(coverage_rows)`的结果保存到`coverage_by_key`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    coverage_by_key = _coverage_index(coverage_rows)

    # 状态计算：把`0`的结果保存到`inserted_total`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    inserted_total = 0
    # 状态计算：把`0`的结果保存到`skipped_total`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    skipped_total = 0
    # 状态计算：把`0`的结果保存到`failed_files`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    failed_files = 0
    # 状态计算：把`[]`的结果保存到`file_reports`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    file_reports: list[dict[str, Any]] = []

    # 显式调用：执行`_append_rows(database_uri=settings.database_uri, table_name=TABLE_NAMES['ingest_batch'], session=session, rows=[_batch_log_row(batch_id=bat…`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
    # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
    # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
    _append_rows(
        database_uri=settings.database_uri,
        table_name=TABLE_NAMES["ingest_batch"],
        session=session,
        rows=[
            _batch_log_row(
                batch_id=batch_id,
                now=started_at,
                status="STARTED",
                root=root,
                contract_version=contract.contract_version,
                preflight=preflight,
                inserted_row_count=0,
                skipped_row_count=0,
                failed_file_count=0,
                message="TASK_016A门禁通过，开始逐文件导入。",
            )
        ],
        appender_factory=appender_factory,
    )

    # 异常边界：尝试执行可能失败的解析、查询、文件或类型转换步骤，并由后续处理保留错误证据。
    # - 数据变化：正常路径产生业务结果；异常路径不得静默伪造数据，应抛出、记录或隔离。
    # - 为什么这样写：把外部环境故障与业务合同失败分开，便于重试、回滚和准确验收。
    try:
        # 循环处理：逐项遍历`file_rows`，把当前元素绑定到`item`。
        # - 数据变化：每轮只处理一个来源记录、字段、文件或证据项，并显式累计到局部集合或输出对象。
        # - 为什么这样写：逐项处理便于保留行级血缘、隔离单项异常，并控制16GB单机上的峰值内存。
        for item in file_rows:
            # 状态计算：把`item['snapshot_date']`的结果保存到`snapshot_date`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            snapshot_date = item["snapshot_date"]
            # 状态计算：把`item['dataset_id']`的结果保存到`dataset_id`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            dataset_id = item["dataset_id"]
            # 状态计算：把`item['status']`的结果保存到`status`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            status = item["status"]
            # 状态计算：把`contract.datasets[dataset_id]`的结果保存到`dataset`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            dataset = contract.datasets[dataset_id]
            # 状态计算：把`root / snapshot_date / item['file_name']`的结果保存到`source_file`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            source_file = (
                root
                / snapshot_date
                / item["file_name"]
            )
            # 状态计算：把`item['source_file_sha256']`的结果保存到`source_hash`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            source_hash = item["source_file_sha256"]
            # 状态计算：把`int(item['row_count'])`的结果保存到`expected_count`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            expected_count = int(item["row_count"])
            # 状态计算：把`FAMILY_TO_TABLE[dataset.family]`的结果保存到`table_name`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            table_name = FAMILY_TO_TABLE[
                dataset.family
            ]
            # 状态计算：把`datetime.now(timezone.utc)`的结果保存到`logged_at`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            logged_at = datetime.now(timezone.utc)

            # 条件门禁：判断`status == 'QUARANTINED'`，条件成立时进入对应的数据、安全或异常处理分支。
            # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
            # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
            if status == "QUARANTINED":
                # 状态计算：把`coverage_by_key.get((snapshot_date, dataset_id), {})`的结果保存到`coverage`，供当前逻辑后续校验、转换、累计或返回。
                # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
                # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
                coverage = coverage_by_key.get(
                    (snapshot_date, dataset_id),
                    {},
                )
                # 状态计算：把`item['quarantine_reason']`的结果保存到`reason`，供当前逻辑后续校验、转换、累计或返回。
                # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
                # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
                reason = item["quarantine_reason"]
                # 状态计算：把`reason.split(':', 1)[0]`的结果保存到`reason_code`，供当前逻辑后续校验、转换、累计或返回。
                # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
                # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
                reason_code = reason.split(":", 1)[0]
                # 状态计算：把`{'ingest_batch_id': batch_id, 'snapshot_date': datetime.strptime(snapshot_date, '%Y%m%d').date().is…`的结果保存到`quarantine_row`，供当前逻辑后续校验、转换、累计或返回。
                # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
                # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
                quarantine_row = {
                    "ingest_batch_id": batch_id,
                    "snapshot_date": datetime.strptime(
                        snapshot_date,
                        "%Y%m%d",
                    ).date().isoformat(),
                    "snapshot_month": (
                        f"{snapshot_date[:4]}-"
                        f"{snapshot_date[4:6]}"
                    ),
                    "logged_at": logged_at.isoformat(),
                    "dataset_id": dataset_id,
                    "source_file_name": item["file_name"],
                    "source_file_sha256": source_hash,
                    "row_count": expected_count,
                    "reason_code": reason_code,
                    "reason_detail": reason,
                    "reference_dataset_id": coverage.get(
                        "reference_dataset_id",
                        "",
                    ),
                    "coverage_ratio": (
                        float(coverage["coverage_ratio"])
                        if coverage.get("coverage_ratio")
                        else None
                    ),
                    "minimum_ratio": (
                        float(coverage["minimum_ratio"])
                        if coverage.get("minimum_ratio")
                        else None
                    ),
                }
                # 显式调用：执行`_append_rows(database_uri=settings.database_uri, table_name=TABLE_NAMES['quarantine_file'], session=session, rows=[quarantine_row], appende…`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
                # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
                # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
                _append_rows(
                    database_uri=settings.database_uri,
                    table_name=TABLE_NAMES[
                        "quarantine_file"
                    ],
                    session=session,
                    rows=[quarantine_row],
                    appender_factory=appender_factory,
                )
                # 显式调用：执行`file_reports.append({'snapshot_date': snapshot_date, 'dataset_id': dataset_id, 'table_name': table_name, 'status': 'QUARANTINED', 'row_coun…`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
                # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
                # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
                file_reports.append(
                    {
                        "snapshot_date": snapshot_date,
                        "dataset_id": dataset_id,
                        "table_name": table_name,
                        "status": "QUARANTINED",
                        "row_count": expected_count,
                        "inserted_row_count": 0,
                        "final_row_count": 0,
                        "source_file_sha256": source_hash,
                    }
                )
                # 显式调用：执行`_append_rows(database_uri=settings.database_uri, table_name=TABLE_NAMES['ingest_file'], session=session, rows=[{'ingest_batch_id': batch_id…`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
                # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
                # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
                _append_rows(
                    database_uri=settings.database_uri,
                    table_name=TABLE_NAMES["ingest_file"],
                    session=session,
                    rows=[
                        {
                            "ingest_batch_id": batch_id,
                            "snapshot_date": datetime.strptime(
                                snapshot_date,
                                "%Y%m%d",
                            ).date().isoformat(),
                            "snapshot_month": (
                                f"{snapshot_date[:4]}-"
                                f"{snapshot_date[4:6]}"
                            ),
                            "logged_at": logged_at.isoformat(),
                            "dataset_id": dataset_id,
                            "family": dataset.family,
                            "source_file_name": item["file_name"],
                            "source_file_sha256": source_hash,
                            "schema_version": item["schema_version"],
                            "row_count": expected_count,
                            "existing_row_count_before": 0,
                            "inserted_row_count": 0,
                            "final_row_count": 0,
                            "status": "QUARANTINED",
                            "message": reason,
                        }
                    ],
                    appender_factory=appender_factory,
                )
                # 控制流：跳过本轮剩余步骤，使循环或占位分支按既定合同继续。
                # - 数据变化：本语句不直接改变业务记录，只调整当前执行路径。
                # - 为什么这样写：显式控制流比隐式嵌套更容易检查边界和异常处理。
                continue

            # 条件门禁：判断`status != 'READY'`，条件成立时进入对应的数据、安全或异常处理分支。
            # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
            # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
            if status != "READY":
                # 错误阻断：抛出`DailyFundsDolphinDBError(f'发现非READY且非QUARANTINED文件：{snapshot_date}/{dataset_id}/{status}')`并停止当前正常路径。
                # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
                # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
                raise DailyFundsDolphinDBError(
                    "发现非READY且非QUARANTINED文件："
                    f"{snapshot_date}/{dataset_id}/{status}"
                )

            # 状态计算：把`file_sha256(source_file)`的结果保存到`actual_hash`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            actual_hash = file_sha256(source_file)
            # 条件门禁：判断`actual_hash != source_hash`，条件成立时进入对应的数据、安全或异常处理分支。
            # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
            # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
            if actual_hash != source_hash:
                # 错误阻断：抛出`DailyFundsDolphinDBError(f'源文件在预导入后发生变化：{source_file}')`并停止当前正常路径。
                # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
                # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
                raise DailyFundsDolphinDBError(
                    "源文件在预导入后发生变化："
                    f"{source_file}"
                )

            # 状态计算：把`_count_file_rows(session, settings.database_uri, table_name, dataset_id, source_hash)`的结果保存到`existing_count`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            existing_count = _count_file_rows(
                session,
                settings.database_uri,
                table_name,
                dataset_id,
                source_hash,
            )
            # 状态计算：把`decide_file_write_action(existing_count, expected_count)`的结果保存到`action`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            action = decide_file_write_action(
                existing_count,
                expected_count,
            )
            # 状态计算：把`0`的结果保存到`inserted_count`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            inserted_count = 0

            # 条件门禁：判断`action == 'SKIP_IDEMPOTENT'`，条件成立时进入对应的数据、安全或异常处理分支。
            # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
            # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
            if action == "SKIP_IDEMPOTENT":
                # 状态计算：把`expected_count`的结果保存到`skipped_total`，供当前逻辑后续校验、转换、累计或返回。
                # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
                # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
                skipped_total += expected_count
            else:
                # 状态计算：把`load_normalized_file_rows(file_path=source_file, dataset=dataset, contract=contract, ingest_batch_i…`的结果保存到`normalized_rows`，供当前逻辑后续校验、转换、累计或返回。
                # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
                # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
                normalized_rows = load_normalized_file_rows(
                    file_path=source_file,
                    dataset=dataset,
                    contract=contract,
                    ingest_batch_id=batch_id,
                    ingested_at=started_at,
                )
                # 条件门禁：判断`len(normalized_rows) != expected_count`，条件成立时进入对应的数据、安全或异常处理分支。
                # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
                # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
                if len(normalized_rows) != expected_count:
                    # 错误阻断：抛出`DailyFundsDolphinDBError(f'再次解析行数不一致：{source_file}, expected={expected_count}, actual={len(normalized_rows)}')`并停止当前正常路径。
                    # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
                    # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
                    raise DailyFundsDolphinDBError(
                        "再次解析行数不一致："
                        f"{source_file}, "
                        f"expected={expected_count}, "
                        f"actual={len(normalized_rows)}"
                    )
                # 状态计算：把`_append_rows(database_uri=settings.database_uri, table_name=table_name, session=session, rows=norma…`的结果保存到`inserted_count`，供当前逻辑后续校验、转换、累计或返回。
                # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
                # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
                inserted_count = _append_rows(
                    database_uri=settings.database_uri,
                    table_name=table_name,
                    session=session,
                    rows=normalized_rows,
                    appender_factory=appender_factory,
                )
                # 状态计算：把`inserted_count`的结果保存到`inserted_total`，供当前逻辑后续校验、转换、累计或返回。
                # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
                # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
                inserted_total += inserted_count

            # 状态计算：把`_count_file_rows(session, settings.database_uri, table_name, dataset_id, source_hash)`的结果保存到`final_count`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            final_count = _count_file_rows(
                session,
                settings.database_uri,
                table_name,
                dataset_id,
                source_hash,
            )
            # 条件门禁：判断`final_count != expected_count`，条件成立时进入对应的数据、安全或异常处理分支。
            # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
            # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
            if final_count != expected_count:
                # 错误阻断：抛出`DailyFundsDolphinDBError(f'文件写入后行数验收失败：{source_file}, expected={expected_count}, actual={final_count}')`并停止当前正常路径。
                # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
                # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
                raise DailyFundsDolphinDBError(
                    "文件写入后行数验收失败："
                    f"{source_file}, "
                    f"expected={expected_count}, "
                    f"actual={final_count}"
                )

            # 状态计算：把`'SKIPPED_IDEMPOTENT' if action == 'SKIP_IDEMPOTENT' else 'RECOVERED_PARTIAL' if action == 'RECOVER_…`的结果保存到`file_status`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            file_status = (
                "SKIPPED_IDEMPOTENT"
                if action == "SKIP_IDEMPOTENT"
                else (
                    "RECOVERED_PARTIAL"
                    if action == "RECOVER_PARTIAL"
                    else "COMMITTED"
                )
            )
            # 显式调用：执行`_append_rows(database_uri=settings.database_uri, table_name=TABLE_NAMES['ingest_file'], session=session, rows=[{'ingest_batch_id': batch_id…`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
            # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
            # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
            _append_rows(
                database_uri=settings.database_uri,
                table_name=TABLE_NAMES["ingest_file"],
                session=session,
                rows=[
                    {
                        "ingest_batch_id": batch_id,
                        "snapshot_date": datetime.strptime(
                            snapshot_date,
                            "%Y%m%d",
                        ).date().isoformat(),
                        "snapshot_month": (
                            f"{snapshot_date[:4]}-"
                            f"{snapshot_date[4:6]}"
                        ),
                        "logged_at": logged_at.isoformat(),
                        "dataset_id": dataset_id,
                        "family": dataset.family,
                        "source_file_name": item["file_name"],
                        "source_file_sha256": source_hash,
                        "schema_version": item["schema_version"],
                        "row_count": expected_count,
                        "existing_row_count_before": existing_count,
                        "inserted_row_count": inserted_count,
                        "final_row_count": final_count,
                        "status": file_status,
                        "message": action,
                    }
                ],
                appender_factory=appender_factory,
            )
            # 显式调用：执行`file_reports.append({'snapshot_date': snapshot_date, 'dataset_id': dataset_id, 'table_name': table_name, 'status': file_status, 'row_count'…`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
            # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
            # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
            file_reports.append(
                {
                    "snapshot_date": snapshot_date,
                    "dataset_id": dataset_id,
                    "table_name": table_name,
                    "status": file_status,
                    "row_count": expected_count,
                    "inserted_row_count": inserted_count,
                    "final_row_count": final_count,
                    "source_file_sha256": source_hash,
                }
            )

        # 状态计算：把`{table_name: _count_table_rows(session, settings.database_uri, table_name) for table_name in FAMILY…`的结果保存到`table_counts`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        table_counts = {
            table_name: _count_table_rows(
                session,
                settings.database_uri,
                table_name,
            )
            for table_name in FAMILY_TO_TABLE.values()
        }

        # 状态计算：把`[item['source_file_sha256'] for item in file_rows if item['status'] == 'QUARANTINED']`的结果保存到`quarantined_hashes`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        quarantined_hashes = [
            item["source_file_sha256"]
            for item in file_rows
            if item["status"] == "QUARANTINED"
        ]
        # 状态计算：把`0`的结果保存到`quarantined_leak_count`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        quarantined_leak_count = 0
        # 循环处理：逐项遍历`file_rows`，把当前元素绑定到`item`。
        # - 数据变化：每轮只处理一个来源记录、字段、文件或证据项，并显式累计到局部集合或输出对象。
        # - 为什么这样写：逐项处理便于保留行级血缘、隔离单项异常，并控制16GB单机上的峰值内存。
        for item in file_rows:
            # 条件门禁：判断`item['status'] != 'QUARANTINED'`，条件成立时进入对应的数据、安全或异常处理分支。
            # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
            # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
            if item["status"] != "QUARANTINED":
                # 控制流：跳过本轮剩余步骤，使循环或占位分支按既定合同继续。
                # - 数据变化：本语句不直接改变业务记录，只调整当前执行路径。
                # - 为什么这样写：显式控制流比隐式嵌套更容易检查边界和异常处理。
                continue
            # 状态计算：把`contract.datasets[item['dataset_id']]`的结果保存到`dataset`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            dataset = contract.datasets[
                item["dataset_id"]
            ]
            # 状态计算：把`_count_file_rows(session, settings.database_uri, FAMILY_TO_TABLE[dataset.family], item['dataset_id'…`的结果保存到`quarantined_leak_count`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            quarantined_leak_count += _count_file_rows(
                session,
                settings.database_uri,
                FAMILY_TO_TABLE[dataset.family],
                item["dataset_id"],
                item["source_file_sha256"],
            )
        # 条件门禁：判断`quarantined_leak_count != 0`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if quarantined_leak_count != 0:
            # 错误阻断：抛出`DailyFundsDolphinDBError('隔离文件进入了主Raw表。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
            raise DailyFundsDolphinDBError(
                "隔离文件进入了主Raw表。"
            )

        # 状态计算：把`datetime.now(timezone.utc)`的结果保存到`completed_at`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        completed_at = datetime.now(timezone.utc)
        # 显式调用：执行`_append_rows(database_uri=settings.database_uri, table_name=TABLE_NAMES['ingest_batch'], session=session, rows=[_batch_log_row(batch_id=bat…`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
        # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
        # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
        _append_rows(
            database_uri=settings.database_uri,
            table_name=TABLE_NAMES["ingest_batch"],
            session=session,
            rows=[
                _batch_log_row(
                    batch_id=batch_id,
                    now=completed_at,
                    status="COMPLETED",
                    root=root,
                    contract_version=contract.contract_version,
                    preflight=preflight,
                    inserted_row_count=inserted_total,
                    skipped_row_count=skipped_total,
                    failed_file_count=0,
                    message="全部READY文件完成逐文件行数验收。",
                )
            ],
            appender_factory=appender_factory,
        )

        # 状态计算：把`{'task_id': 'TASK_016B', 'mode': 'IMPORT', 'ingest_batch_id': batch_id, 'started_at': started_at.is…`的结果保存到`report`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        report = {
            "task_id": "TASK_016B",
            "mode": "IMPORT",
            "ingest_batch_id": batch_id,
            "started_at": started_at.isoformat(),
            "completed_at": completed_at.isoformat(),
            "database_uri": settings.database_uri,
            "preflight": preflight,
            "inserted_row_count": inserted_total,
            "skipped_idempotent_row_count": skipped_total,
            "failed_file_count": 0,
            "file_status_counts": dict(
                Counter(
                    item["status"]
                    for item in file_reports
                )
            ),
            "main_table_row_counts": table_counts,
            "quarantined_source_hashes": quarantined_hashes,
            "quarantined_leak_count": quarantined_leak_count,
            "overall_status": "PASSED",
        }
    except Exception as exc:
        # 状态计算：把`1`的结果保存到`failed_files`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        failed_files += 1
        # 状态计算：把`datetime.now(timezone.utc)`的结果保存到`failed_at`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        failed_at = datetime.now(timezone.utc)
        # 异常边界：尝试执行可能失败的解析、查询、文件或类型转换步骤，并由后续处理保留错误证据。
        # - 数据变化：正常路径产生业务结果；异常路径不得静默伪造数据，应抛出、记录或隔离。
        # - 为什么这样写：把外部环境故障与业务合同失败分开，便于重试、回滚和准确验收。
        try:
            # 显式调用：执行`_append_rows(database_uri=settings.database_uri, table_name=TABLE_NAMES['ingest_batch'], session=session, rows=[_batch_log_row(batch_id=bat…`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
            # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
            # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
            _append_rows(
                database_uri=settings.database_uri,
                table_name=TABLE_NAMES["ingest_batch"],
                session=session,
                rows=[
                    _batch_log_row(
                        batch_id=batch_id,
                        now=failed_at,
                        status="FAILED",
                        root=root,
                        contract_version=contract.contract_version,
                        preflight=preflight,
                        inserted_row_count=inserted_total,
                        skipped_row_count=skipped_total,
                        failed_file_count=failed_files,
                        message=f"{type(exc).__name__}: {exc}",
                    )
                ],
                appender_factory=appender_factory,
            )
        except Exception:
            # 控制流：保留显式空分支，使循环或占位分支按既定合同继续。
            # - 数据变化：本语句不直接改变业务记录，只调整当前执行路径。
            # - 为什么这样写：显式控制流比隐式嵌套更容易检查边界和异常处理。
            pass
        # 错误阻断：抛出`无`并停止当前正常路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
        # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
        raise

    # 显式调用：执行`_write_json(output_dir / 'task_016b_import_summary.json', report)`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
    # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
    # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
    _write_json(
        output_dir / "task_016b_import_summary.json",
        report,
    )
    # 显式调用：执行`_write_json(output_dir / 'task_016b_file_results.json', file_reports)`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
    # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
    # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
    _write_json(
        output_dir / "task_016b_file_results.json",
        file_reports,
    )
    # 显式调用：执行`(output_dir / 'task_016b_import_summary.md').write_text(_build_import_markdown(report), encoding='utf-8')`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
    # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
    # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
    (
        output_dir / "task_016b_import_summary.md"
    ).write_text(
        _build_import_markdown(report),
        encoding="utf-8",
    )
    # 结果返回：把`report`交给调用方并结束当前函数。
    # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return report


# 函数_build_import_markdown：执行_build_import_markdown对应的业务处理。
# - 输入：report:dict[str, Any]；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型str；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：该函数名称涉及写入能力，只有调用方显式进入受控模式时才可能产生数据库或文件副作用；注释迁移和验证不会调用它。
# - 为什么这样写：把显式写入或持久化步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def _build_import_markdown(
    report: dict[str, Any],
) -> str:
    # 状态计算：把`'\n'.join((f'- `{name}`：{count}' for name, count in report['main_table_row_counts'].items()))`的结果保存到`table_lines`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    table_lines = "\n".join(
        f"- `{name}`：{count}"
        for name, count in report[
            "main_table_row_counts"
        ].items()
    )
    # 结果返回：把`f"# TASK_016B 七类日线资金真实导入\n\n- 状态：**{report['overall_status']}**\n- 批次：`{report['ingest_batch_id']}`\n- 数据库：`{report['da…`交给调用方并结束当前函数。
    # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return f"""# TASK_016B 七类日线资金真实导入

- 状态：**{report['overall_status']}**
- 批次：`{report['ingest_batch_id']}`
- 数据库：`{report['database_uri']}`
- 本次实际追加：{report['inserted_row_count']}
- 幂等跳过：{report['skipped_idempotent_row_count']}
- 失败文件：{report['failed_file_count']}
- 隔离泄漏行数：{report['quarantined_leak_count']}

## 主Raw表当前行数

{table_lines}

## 说明

- 本次先重新执行TASK_016A门禁；
- READY文件逐文件写入并逐文件回查行数；
- 相同源文件重复运行会按源文件哈希幂等跳过；
- 部分写入可通过TSDB keepDuplicates=LAST恢复；
- 隔离文件不进入主Raw表；
- source_file_mtime仅作为来源证据。
"""


# 函数resolve_password：执行resolve_password对应的业务处理。
# - 输入：无外部业务参数；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型str；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
# - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def resolve_password() -> str:
    # 状态计算：把`os.getenv('DOLPHINDB_PASSWORD')`的结果保存到`password`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    password = os.getenv("DOLPHINDB_PASSWORD")
    # 条件门禁：判断`password is None`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if password is None:
        # 状态计算：把`getpass.getpass('请输入 DolphinDB 密码：')`的结果保存到`password`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        password = getpass.getpass(
            "请输入 DolphinDB 密码："
        )
    # 条件门禁：判断`not password`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if not password:
        # 错误阻断：抛出`DailyFundsDolphinDBError('DolphinDB密码不能为空。')`并停止当前正常路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
        # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
        raise DailyFundsDolphinDBError(
            "DolphinDB密码不能为空。"
        )
    # 结果返回：把`password`交给调用方并结束当前函数。
    # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return password
