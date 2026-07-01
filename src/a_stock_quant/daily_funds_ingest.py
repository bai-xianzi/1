# 模块总览：在进入DolphinDB前完成七类来源文件的发现、结构识别、字段清洗、覆盖检查和预导入门禁。
# - 输入输出：输入为本地来源目录和Schema合同；输出为标准化待写批次、异常清单和隔离决策。
# - 数据与安全：预处理必须保留来源文件、行号、哈希和原始符号，避免不可追溯的数据修正。
# - 运行边界：导入模块和阅读注释不会触发数据库写入；只有显式调用对应函数并满足门禁时才执行I/O。
# - 为什么这样写：先声明职责、单位、时点和副作用边界，读者可以在阅读实现前建立正确的金融与工程语境。
"""TASK_016A 七类日线资金入库前解析与质量门禁。

本模块只处理本地源文件并生成写入计划，不连接或修改 DolphinDB。

支持的数据集：
- hq / kphq：个股行情与集合竞价；
- hy / gn / kphy / kpgn：行业、概念收盘及集合竞价；
- zj：个股资金流。

源文件扩展名是 .xls，但实际格式是 GB18030 编码的制表符文本。
"""
# 依赖导入：加载`from __future__ import annotations`所提供的类型、标准库或项目内能力。
# - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
# - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
from __future__ import annotations

# 依赖导入：加载`import csv`所提供的类型、标准库或项目内能力。
# - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
# - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
import csv
# 依赖导入：加载`import hashlib`所提供的类型、标准库或项目内能力。
# - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
# - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
import hashlib
# 依赖导入：加载`import json`所提供的类型、标准库或项目内能力。
# - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
# - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
import json
# 依赖导入：加载`import math`所提供的类型、标准库或项目内能力。
# - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
# - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
import math
# 依赖导入：加载`import re`所提供的类型、标准库或项目内能力。
# - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
# - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
import re
# 依赖导入：加载`from collections import Counter`所提供的类型、标准库或项目内能力。
# - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
# - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
from collections import Counter
# 依赖导入：加载`from dataclasses import dataclass`所提供的类型、标准库或项目内能力。
# - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
# - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
from dataclasses import dataclass
# 依赖导入：加载`from datetime import date, datetime, timezone`所提供的类型、标准库或项目内能力。
# - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
# - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
from datetime import date, datetime, timezone
# 依赖导入：加载`from pathlib import Path`所提供的类型、标准库或项目内能力。
# - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
# - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
from pathlib import Path
# 依赖导入：加载`from typing import Any, Iterable, Iterator`所提供的类型、标准库或项目内能力。
# - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
# - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
from typing import Any, Iterable, Iterator

# 依赖导入：加载`import yaml`所提供的类型、标准库或项目内能力。
# - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
# - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
import yaml


# 关键常量DATE_DIR_PATTERN：集中保存`re.compile('^\\d{8}$')`对应的合同值、Schema集合或运行边界。
# - 来源与范围：该值来自当前项目任务、配置、真实数据画像或安全合同；未明确说明时不得外推为行业统一标准。
# - 单位与实例：数值单位由变量名、相邻校验和调用语义共同限定；字符串用于版本、字段、状态或DolphinDB对象标识。
# - 为什么这样写：集中命名固定参数可避免魔法值散落，并让升级、审计和回归测试有稳定锚点。
DATE_DIR_PATTERN = re.compile(r"^\d{8}$")
# 关键常量INSTRUMENT_CODE_PATTERN：集中保存`re.compile('(?<!\\d)(\\d{6})(?!\\d)')`对应的合同值、Schema集合或运行边界。
# - 来源与范围：该值来自当前项目任务、配置、真实数据画像或安全合同；未明确说明时不得外推为行业统一标准。
# - 单位与实例：数值单位由变量名、相邻校验和调用语义共同限定；字符串用于版本、字段、状态或DolphinDB对象标识。
# - 为什么这样写：集中命名固定参数可避免魔法值散落，并让升级、审计和回归测试有稳定锚点。
INSTRUMENT_CODE_PATTERN = re.compile(r"(?<!\d)(\d{6})(?!\d)")
# 关键常量MISSING_DEFAULTS：集中保存`{'', '—', '--', 'N/A', 'NA', 'null', 'NULL'}`对应的合同值、Schema集合或运行边界。
# - 来源与范围：该值来自当前项目任务、配置、真实数据画像或安全合同；未明确说明时不得外推为行业统一标准。
# - 单位与实例：数值单位由变量名、相邻校验和调用语义共同限定；字符串用于版本、字段、状态或DolphinDB对象标识。
# - 为什么这样写：集中命名固定参数可避免魔法值散落，并让升级、审计和回归测试有稳定锚点。
MISSING_DEFAULTS = {"", "—", "--", "N/A", "NA", "null", "NULL"}
# 关键常量MAGNITUDE_MULTIPLIERS：集中保存`(('万亿', 1000000000000.0), ('亿', 100000000.0), ('万', 10000.0), ('千', 1000.0))`对应的合同值、Schema集合或运行边界。
# - 来源与范围：该值来自当前项目任务、配置、真实数据画像或安全合同；未明确说明时不得外推为行业统一标准。
# - 单位与实例：数值单位由变量名、相邻校验和调用语义共同限定；字符串用于版本、字段、状态或DolphinDB对象标识。
# - 为什么这样写：集中命名固定参数可避免魔法值散落，并让升级、审计和回归测试有稳定锚点。
MAGNITUDE_MULTIPLIERS = (
    ("万亿", 1_000_000_000_000.0),
    ("亿", 100_000_000.0),
    ("万", 10_000.0),
    ("千", 1_000.0),
)
# 关键常量BLOCKING_PARSE_CODES：集中保存`{'UNKNOWN_SCHEMA', 'MALFORMED_ROW', 'DUPLICATE_ENTITY_KEY', 'ROW_NORMALIZATION_FAILED'}`对应的合同值、Schema集合或运行边界。
# - 来源与范围：该值来自当前项目任务、配置、真实数据画像或安全合同；未明确说明时不得外推为行业统一标准。
# - 单位与实例：数值单位由变量名、相邻校验和调用语义共同限定；字符串用于版本、字段、状态或DolphinDB对象标识。
# - 为什么这样写：集中命名固定参数可避免魔法值散落，并让升级、审计和回归测试有稳定锚点。
BLOCKING_PARSE_CODES = {
    "UNKNOWN_SCHEMA",
    "MALFORMED_ROW",
    "DUPLICATE_ENTITY_KEY",
    "ROW_NORMALIZATION_FAILED",
}


# 类DailyFundsIngestError：日线资金解析或合同错误。
# - 结构：继承或实现ValueError；类体约包含0个字段或常量、0个方法。
# - 数据变化：类定义阶段不执行隐式I/O，实例只在构造或显式方法调用时改变受控状态。
# - 实操：调用方通过该类型集中传递配置、记录、服务或结果，避免跨模块使用无约束字典。
# - 为什么这样写：强类型边界能集中维护单位、时点、主键和安全不变量，并降低供应商耦合。
class DailyFundsIngestError(ValueError):
    """日线资金解析或合同错误。"""


# 类KnownSchema：一个已知来源表头版本。
# - 结构：继承或实现object；类体约包含4个字段或常量、0个方法。
# - 数据变化：类定义阶段不执行隐式I/O，实例只在构造或显式方法调用时改变受控状态。
# - 实操：调用方通过该类型集中传递配置、记录、服务或结果，避免跨模块使用无约束字典。
# - 为什么这样写：强类型边界能集中维护单位、时点、主键和安全不变量，并降低供应商耦合。
@dataclass(frozen=True, slots=True)
class KnownSchema:
    """一个已知来源表头版本。"""

    # 状态计算：把`无`的结果保存到`dataset_id`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    dataset_id: str
    # 状态计算：把`无`的结果保存到`schema_version`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    schema_version: str
    # 状态计算：把`无`的结果保存到`exact_header_sha256`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    exact_header_sha256: str
    # 状态计算：把`无`的结果保存到`headers`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    headers: tuple[str, ...]


# 类DatasetSpec：一个逻辑数据集的来源合同。
# - 结构：继承或实现object；类体约包含7个字段或常量、0个方法。
# - 数据变化：类定义阶段不执行隐式I/O，实例只在构造或显式方法调用时改变受控状态。
# - 实操：调用方通过该类型集中传递配置、记录、服务或结果，避免跨模块使用无约束字典。
# - 为什么这样写：强类型边界能集中维护单位、时点、主键和安全不变量，并降低供应商耦合。
@dataclass(frozen=True, slots=True)
class DatasetSpec:
    """一个逻辑数据集的来源合同。"""

    # 状态计算：把`无`的结果保存到`dataset_id`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    dataset_id: str
    # 状态计算：把`无`的结果保存到`file_name`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    file_name: str
    # 状态计算：把`无`的结果保存到`family`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    family: str
    # 状态计算：把`无`的结果保存到`snapshot_phase`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    snapshot_phase: str
    # 状态计算：把`无`的结果保存到`classification_type`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    classification_type: str | None
    # 状态计算：把`无`的结果保存到`entity_key`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    entity_key: str
    # 状态计算：把`无`的结果保存到`schemas`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    schemas: tuple[KnownSchema, ...]


# 类DailyFundsContract：完整的七类日线资金来源合同。
# - 结构：继承或实现object；类体约包含8个字段或常量、1个方法。
# - 数据变化：类定义阶段不执行隐式I/O，实例只在构造或显式方法调用时改变受控状态。
# - 实操：调用方通过该类型集中传递配置、记录、服务或结果，避免跨模块使用无约束字典。
# - 为什么这样写：强类型边界能集中维护单位、时点、主键和安全不变量，并降低供应商耦合。
@dataclass(frozen=True, slots=True)
class DailyFundsContract:
    """完整的七类日线资金来源合同。"""

    # 状态计算：把`无`的结果保存到`contract_version`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    contract_version: str
    # 状态计算：把`无`的结果保存到`source_encoding`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    source_encoding: str
    # 状态计算：把`无`的结果保存到`source_delimiter`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    source_delimiter: str
    # 状态计算：把`无`的结果保存到`missing_tokens`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    missing_tokens: frozenset[str]
    # 状态计算：把`无`的结果保存到`database_plan`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    database_plan: dict[str, Any]
    # 状态计算：把`无`的结果保存到`coverage_gates`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    coverage_gates: dict[str, dict[str, Any]]
    # 状态计算：把`无`的结果保存到`semantic_aliases`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    semantic_aliases: dict[str, str]
    # 状态计算：把`无`的结果保存到`datasets`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    datasets: dict[str, DatasetSpec]

    # 函数schema_index：按 dataset_id 和表头哈希建立索引。
    # - 输入：无外部业务参数；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型dict[tuple[str, str], KnownSchema]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    def schema_index(self) -> dict[tuple[str, str], KnownSchema]:
        """按 dataset_id 和表头哈希建立索引。"""
        # 状态计算：把`{}`的结果保存到`result`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        result: dict[tuple[str, str], KnownSchema] = {}
        # 循环处理：逐项遍历`self.datasets.values()`，把当前元素绑定到`dataset`。
        # - 数据变化：每轮只处理一个来源记录、字段、文件或证据项，并显式累计到局部集合或输出对象。
        # - 为什么这样写：逐项处理便于保留行级血缘、隔离单项异常，并控制16GB单机上的峰值内存。
        for dataset in self.datasets.values():
            # 循环处理：逐项遍历`dataset.schemas`，把当前元素绑定到`schema`。
            # - 数据变化：每轮只处理一个来源记录、字段、文件或证据项，并显式累计到局部集合或输出对象。
            # - 为什么这样写：逐项处理便于保留行级血缘、隔离单项异常，并控制16GB单机上的峰值内存。
            for schema in dataset.schemas:
                # 状态计算：把`(dataset.dataset_id, schema.exact_header_sha256)`的结果保存到`key`，供当前逻辑后续校验、转换、累计或返回。
                # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
                # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
                key = (dataset.dataset_id, schema.exact_header_sha256)
                # 条件门禁：判断`key in result`，条件成立时进入对应的数据、安全或异常处理分支。
                # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
                # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
                if key in result:
                    # 错误阻断：抛出`DailyFundsIngestError(f'Schema重复：{key}')`并停止当前正常路径。
                    # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
                    # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
                    raise DailyFundsIngestError(f"Schema重复：{key}")
                # 状态计算：把`schema`的结果保存到`result[key]`，供当前逻辑后续校验、转换、累计或返回。
                # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
                # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
                result[key] = schema
        # 结果返回：把`result`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return result


# 类ParsedSourceFile：单个文件的解析结果摘要。
# - 结构：继承或实现object；类体约包含17个字段或常量、1个方法。
# - 数据变化：类定义阶段不执行隐式I/O，实例只在构造或显式方法调用时改变受控状态。
# - 实操：调用方通过该类型集中传递配置、记录、服务或结果，避免跨模块使用无约束字典。
# - 为什么这样写：强类型边界能集中维护单位、时点、主键和安全不变量，并降低供应商耦合。
@dataclass(frozen=True, slots=True)
class ParsedSourceFile:
    """单个文件的解析结果摘要。"""

    # 状态计算：把`无`的结果保存到`dataset_id`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    dataset_id: str
    # 状态计算：把`无`的结果保存到`snapshot_date`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    snapshot_date: date
    # 状态计算：把`无`的结果保存到`file_path`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    file_path: Path
    # 状态计算：把`无`的结果保存到`file_size_bytes`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    file_size_bytes: int
    # 状态计算：把`无`的结果保存到`source_file_sha256`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    source_file_sha256: str
    # 状态计算：把`无`的结果保存到`schema_version`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    schema_version: str | None
    # 状态计算：把`无`的结果保存到`exact_header_sha256`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    exact_header_sha256: str
    # 状态计算：把`无`的结果保存到`row_count`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    row_count: int
    # 状态计算：把`无`的结果保存到`unique_key_count`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    unique_key_count: int
    # 状态计算：把`无`的结果保存到`duplicate_key_count`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    duplicate_key_count: int
    # 状态计算：把`无`的结果保存到`malformed_row_count`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    malformed_row_count: int
    # 状态计算：把`无`的结果保存到`missing_cell_count`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    missing_cell_count: int
    # 状态计算：把`无`的结果保存到`normalization_error_count`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    normalization_error_count: int
    # 状态计算：把`无`的结果保存到`entity_keys`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    entity_keys: frozenset[str]
    # 状态计算：把`无`的结果保存到`normalized_samples`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    normalized_samples: tuple[dict[str, Any], ...]
    # 状态计算：把`无`的结果保存到`anomaly_codes`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    anomaly_codes: tuple[str, ...]
    # 状态计算：把`无`的结果保存到`anomaly_details`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    anomaly_details: tuple[str, ...]

    # 函数has_blocking_parse_error：是否存在阻断该文件写入的解析问题。
    # - 输入：无外部业务参数；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型bool；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    @property
    def has_blocking_parse_error(self) -> bool:
        """是否存在阻断该文件写入的解析问题。"""
        # 结果返回：把`any((code in BLOCKING_PARSE_CODES for code in self.anomaly_codes))`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return any(code in BLOCKING_PARSE_CODES for code in self.anomaly_codes)


# 函数load_daily_funds_contract：读取并验证 YAML 来源合同。
# - 输入：path:Path；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型DailyFundsContract；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
# - 为什么这样写：把只读查询或来源发现步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def load_daily_funds_contract(path: Path) -> DailyFundsContract:
    """读取并验证 YAML 来源合同。"""
    # 状态计算：把`yaml.safe_load(path.read_text(encoding='utf-8'))`的结果保存到`payload`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    # 条件门禁：判断`not isinstance(payload, dict)`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if not isinstance(payload, dict):
        # 错误阻断：抛出`DailyFundsIngestError('来源合同根节点必须是字典。')`并停止当前正常路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
        # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
        raise DailyFundsIngestError("来源合同根节点必须是字典。")

    # 状态计算：把`payload.get('source_format')`的结果保存到`source_format`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    source_format = payload.get("source_format")
    # 状态计算：把`payload.get('datasets')`的结果保存到`datasets_payload`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    datasets_payload = payload.get("datasets")
    # 条件门禁：判断`not isinstance(source_format, dict)`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if not isinstance(source_format, dict):
        # 错误阻断：抛出`DailyFundsIngestError('source_format 缺失或类型错误。')`并停止当前正常路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
        # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
        raise DailyFundsIngestError("source_format 缺失或类型错误。")
    # 条件门禁：判断`not isinstance(datasets_payload, dict)`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if not isinstance(datasets_payload, dict):
        # 错误阻断：抛出`DailyFundsIngestError('datasets 缺失或类型错误。')`并停止当前正常路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
        # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
        raise DailyFundsIngestError("datasets 缺失或类型错误。")

    # 状态计算：把`{}`的结果保存到`datasets`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    datasets: dict[str, DatasetSpec] = {}
    # 循环处理：逐项遍历`datasets_payload.items()`，把当前元素绑定到`(dataset_id, raw_spec)`。
    # - 数据变化：每轮只处理一个来源记录、字段、文件或证据项，并显式累计到局部集合或输出对象。
    # - 为什么这样写：逐项处理便于保留行级血缘、隔离单项异常，并控制16GB单机上的峰值内存。
    for dataset_id, raw_spec in datasets_payload.items():
        # 条件门禁：判断`not isinstance(raw_spec, dict)`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if not isinstance(raw_spec, dict):
            # 错误阻断：抛出`DailyFundsIngestError(f'数据集配置必须是字典：{dataset_id}')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
            raise DailyFundsIngestError(
                f"数据集配置必须是字典：{dataset_id}"
            )

        # 状态计算：把`raw_spec.get('schemas')`的结果保存到`schemas_payload`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        schemas_payload = raw_spec.get("schemas")
        # 条件门禁：判断`not isinstance(schemas_payload, list) or not schemas_payload`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if not isinstance(schemas_payload, list) or not schemas_payload:
            # 错误阻断：抛出`DailyFundsIngestError(f'数据集必须至少有一个已知Schema：{dataset_id}')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
            raise DailyFundsIngestError(
                f"数据集必须至少有一个已知Schema：{dataset_id}"
            )

        # 状态计算：把`[]`的结果保存到`schemas`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        schemas: list[KnownSchema] = []
        # 循环处理：逐项遍历`schemas_payload`，把当前元素绑定到`schema_payload`。
        # - 数据变化：每轮只处理一个来源记录、字段、文件或证据项，并显式累计到局部集合或输出对象。
        # - 为什么这样写：逐项处理便于保留行级血缘、隔离单项异常，并控制16GB单机上的峰值内存。
        for schema_payload in schemas_payload:
            # 条件门禁：判断`not isinstance(schema_payload, dict)`，条件成立时进入对应的数据、安全或异常处理分支。
            # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
            # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
            if not isinstance(schema_payload, dict):
                # 错误阻断：抛出`DailyFundsIngestError(f'Schema配置必须是字典：{dataset_id}')`并停止当前正常路径。
                # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
                # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
                raise DailyFundsIngestError(
                    f"Schema配置必须是字典：{dataset_id}"
                )
            # 状态计算：把`schema_payload.get('headers')`的结果保存到`headers`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            headers = schema_payload.get("headers")
            # 条件门禁：判断`not isinstance(headers, list) or not all((isinstance(item, str) for item in headers))`，条件成立时进入对应的数据、安全或异常处理分支。
            # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
            # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
            if not isinstance(headers, list) or not all(
                isinstance(item, str) for item in headers
            ):
                # 错误阻断：抛出`DailyFundsIngestError(f'Schema headers 非法：{dataset_id}')`并停止当前正常路径。
                # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
                # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
                raise DailyFundsIngestError(
                    f"Schema headers 非法：{dataset_id}"
                )
            # 状态计算：把`str(schema_payload.get('exact_header_sha256', ''))`的结果保存到`expected_hash`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            expected_hash = str(
                schema_payload.get("exact_header_sha256", "")
            )
            # 状态计算：把`header_fingerprint(headers)`的结果保存到`actual_hash`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            actual_hash = header_fingerprint(headers)
            # 条件门禁：判断`expected_hash != actual_hash`，条件成立时进入对应的数据、安全或异常处理分支。
            # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
            # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
            if expected_hash != actual_hash:
                # 错误阻断：抛出`DailyFundsIngestError(f"Schema表头哈希不一致：{dataset_id}/{schema_payload.get('schema_version')}")`并停止当前正常路径。
                # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
                # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
                raise DailyFundsIngestError(
                    f"Schema表头哈希不一致："
                    f"{dataset_id}/"
                    f"{schema_payload.get('schema_version')}"
                )
            # 显式调用：执行`schemas.append(KnownSchema(dataset_id=str(dataset_id), schema_version=str(schema_payload.get('schema_version', '')), exact_header_sha256=ex…`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
            # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
            # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
            schemas.append(
                KnownSchema(
                    dataset_id=str(dataset_id),
                    schema_version=str(
                        schema_payload.get("schema_version", "")
                    ),
                    exact_header_sha256=expected_hash,
                    headers=tuple(headers),
                )
            )

        # 状态计算：把`DatasetSpec(dataset_id=str(dataset_id), file_name=str(raw_spec.get('file_name', '')), family=str(ra…`的结果保存到`dataset_spec`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        dataset_spec = DatasetSpec(
            dataset_id=str(dataset_id),
            file_name=str(raw_spec.get("file_name", "")),
            family=str(raw_spec.get("family", "")),
            snapshot_phase=str(
                raw_spec.get("snapshot_phase", "")
            ),
            classification_type=(
                None
                if raw_spec.get("classification_type") is None
                else str(raw_spec.get("classification_type"))
            ),
            entity_key=str(raw_spec.get("entity_key", "")),
            schemas=tuple(schemas),
        )
        # 条件门禁：判断`not dataset_spec.file_name`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if not dataset_spec.file_name:
            # 错误阻断：抛出`DailyFundsIngestError(f'file_name 不能为空：{dataset_id}')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
            raise DailyFundsIngestError(
                f"file_name 不能为空：{dataset_id}"
            )
        # 条件门禁：判断`dataset_spec.family not in {'security_snapshot', 'classification_snapshot', 'money_flow_snapshot'}`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if dataset_spec.family not in {
            "security_snapshot",
            "classification_snapshot",
            "money_flow_snapshot",
        }:
            # 错误阻断：抛出`DailyFundsIngestError(f'family 非法：{dataset_id}/{dataset_spec.family}')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
            raise DailyFundsIngestError(
                f"family 非法：{dataset_id}/{dataset_spec.family}"
            )
        # 状态计算：把`dataset_spec`的结果保存到`datasets[dataset_spec.dataset_id]`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        datasets[dataset_spec.dataset_id] = dataset_spec

    # 状态计算：把`{'hq', 'hy', 'gn', 'kphq', 'kphy', 'kpgn', 'zj'}`的结果保存到`required_dataset_ids`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    required_dataset_ids = {
        "hq",
        "hy",
        "gn",
        "kphq",
        "kphy",
        "kpgn",
        "zj",
    }
    # 条件门禁：判断`set(datasets) != required_dataset_ids`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if set(datasets) != required_dataset_ids:
        # 错误阻断：抛出`DailyFundsIngestError(f'七类数据集必须完整登记。 expected={sorted(required_dataset_ids)} actual={sorted(datasets)}')`并停止当前正常路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
        # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
        raise DailyFundsIngestError(
            "七类数据集必须完整登记。"
            f" expected={sorted(required_dataset_ids)}"
            f" actual={sorted(datasets)}"
        )

    # 状态计算：把`DailyFundsContract(contract_version=str(payload.get('contract_version', '')), source_encoding=str(s…`的结果保存到`contract`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    contract = DailyFundsContract(
        contract_version=str(payload.get("contract_version", "")),
        source_encoding=str(source_format.get("encoding", "")),
        source_delimiter=str(source_format.get("delimiter", "")),
        missing_tokens=frozenset(
            str(item)
            for item in source_format.get(
                "missing_tokens", MISSING_DEFAULTS
            )
        ),
        database_plan=dict(payload.get("database_plan", {})),
        coverage_gates=dict(payload.get("coverage_gates", {})),
        semantic_aliases={
            str(key): str(value)
            for key, value in dict(
                payload.get("semantic_aliases", {})
            ).items()
        },
        datasets=datasets,
    )
    # 显式调用：执行`contract.schema_index()`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
    # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
    # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
    contract.schema_index()
    # 结果返回：把`contract`交给调用方并结束当前函数。
    # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return contract


# 函数validate_daily_funds_contract：返回来源合同的机器校验结果。
# - 输入：contract:DailyFundsContract；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型dict[str, Any]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
# - 为什么这样写：把合同、数据质量或安全门禁校验步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def validate_daily_funds_contract(
    contract: DailyFundsContract,
) -> dict[str, Any]:
    """返回来源合同的机器校验结果。"""
    # 状态计算：把`sum((len(dataset.schemas) for dataset in contract.datasets.values()))`的结果保存到`schema_count`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    schema_count = sum(
        len(dataset.schemas)
        for dataset in contract.datasets.values()
    )
    # 状态计算：把`[schema.exact_header_sha256 for dataset in contract.datasets.values() for schema in dataset.schemas]`的结果保存到`hashes`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    hashes = [
        schema.exact_header_sha256
        for dataset in contract.datasets.values()
        for schema in dataset.schemas
    ]
    # 状态计算：把`[]`的结果保存到`issues`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    issues: list[dict[str, Any]] = []
    # 条件门禁：判断`len(hashes) != len(set(((schema.dataset_id, schema.exact_header_sha256) for dataset in contract.datasets.values() for schema in d…`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if len(hashes) != len(set((schema.dataset_id, schema.exact_header_sha256)
                              for dataset in contract.datasets.values()
                              for schema in dataset.schemas)):
        # 显式调用：执行`issues.append({'severity': 'ERROR', 'code': 'DUPLICATE_SCHEMA_KEY', 'message': 'dataset_id + header hash 必须唯一。'})`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
        # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
        # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
        issues.append(
            {
                "severity": "ERROR",
                "code": "DUPLICATE_SCHEMA_KEY",
                "message": "dataset_id + header hash 必须唯一。",
            }
        )

    # 循环处理：逐项遍历`contract.coverage_gates.items()`，把当前元素绑定到`(child, gate)`。
    # - 数据变化：每轮只处理一个来源记录、字段、文件或证据项，并显式累计到局部集合或输出对象。
    # - 为什么这样写：逐项处理便于保留行级血缘、隔离单项异常，并控制16GB单机上的峰值内存。
    for child, gate in contract.coverage_gates.items():
        # 状态计算：把`str(gate.get('reference_dataset_id', ''))`的结果保存到`reference`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        reference = str(gate.get("reference_dataset_id", ""))
        # 状态计算：把`gate.get('minimum_intersection_ratio')`的结果保存到`threshold`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        threshold = gate.get("minimum_intersection_ratio")
        # 条件门禁：判断`child not in contract.datasets`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if child not in contract.datasets:
            # 显式调用：执行`issues.append({'severity': 'ERROR', 'code': 'UNKNOWN_COVERAGE_CHILD', 'message': child})`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
            # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
            # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
            issues.append(
                {
                    "severity": "ERROR",
                    "code": "UNKNOWN_COVERAGE_CHILD",
                    "message": child,
                }
            )
        # 条件门禁：判断`reference not in contract.datasets`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if reference not in contract.datasets:
            # 显式调用：执行`issues.append({'severity': 'ERROR', 'code': 'UNKNOWN_COVERAGE_REFERENCE', 'message': reference})`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
            # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
            # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
            issues.append(
                {
                    "severity": "ERROR",
                    "code": "UNKNOWN_COVERAGE_REFERENCE",
                    "message": reference,
                }
            )
        # 条件门禁：判断`not isinstance(threshold, (int, float)) or not 0 < float(threshold) <= 1`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if not isinstance(threshold, (int, float)) or not 0 < float(
            threshold
        ) <= 1:
            # 显式调用：执行`issues.append({'severity': 'ERROR', 'code': 'INVALID_COVERAGE_THRESHOLD', 'message': child})`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
            # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
            # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
            issues.append(
                {
                    "severity": "ERROR",
                    "code": "INVALID_COVERAGE_THRESHOLD",
                    "message": child,
                }
            )

    # 状态计算：把`contract.database_plan.get('physical_tables', {})`的结果保存到`physical_tables`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    physical_tables = contract.database_plan.get(
        "physical_tables", {}
    )
    # 条件门禁：判断`not isinstance(physical_tables, dict)`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if not isinstance(physical_tables, dict):
        # 显式调用：执行`issues.append({'severity': 'ERROR', 'code': 'PHYSICAL_TABLE_PLAN_MISSING', 'message': 'physical_tables 必须是字典。'})`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
        # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
        # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
        issues.append(
            {
                "severity": "ERROR",
                "code": "PHYSICAL_TABLE_PLAN_MISSING",
                "message": "physical_tables 必须是字典。",
            }
        )

    # 结果返回：把`{'task_id': 'TASK_016A', 'contract_version': contract.contract_version, 'dataset_count': len(contract.datasets), 'schem…`交给调用方并结束当前函数。
    # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return {
        "task_id": "TASK_016A",
        "contract_version": contract.contract_version,
        "dataset_count": len(contract.datasets),
        "schema_count": schema_count,
        "coverage_gate_count": len(contract.coverage_gates),
        "overall_status": (
            "PASSED"
            if not any(
                item["severity"] == "ERROR" for item in issues
            )
            else "FAILED"
        ),
        "issues": issues,
    }


# 函数strip_cell：统一去除来源单元格两端空白和BOM。
# - 输入：value:Any；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型str；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
# - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def strip_cell(value: Any) -> str:
    """统一去除来源单元格两端空白和BOM。"""
    # 条件门禁：判断`value is None`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if value is None:
        # 结果返回：把`''`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return ""
    # 结果返回：把`str(value).replace('\ufeff', '').strip()`交给调用方并结束当前函数。
    # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return str(value).replace("\ufeff", "").strip()


# 函数header_fingerprint：生成与 TASK_015B 一致的精确表头哈希。
# - 输入：headers:Iterable[str]；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型str；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
# - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def header_fingerprint(headers: Iterable[str]) -> str:
    """生成与 TASK_015B 一致的精确表头哈希。"""
    # 状态计算：把`[strip_cell(item) for item in headers]`的结果保存到`normalized`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    normalized = [strip_cell(item) for item in headers]
    # 状态计算：把`'\x1f'.join(normalized).encode('utf-8')`的结果保存到`payload`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    payload = "\x1f".join(normalized).encode("utf-8")
    # 结果返回：把`hashlib.sha256(payload).hexdigest()`交给调用方并结束当前函数。
    # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return hashlib.sha256(payload).hexdigest()


# 函数deduplicate_headers：保留重复表头，并为后续重复项增加 __2、__3 后缀。
# - 输入：headers:Iterable[str]；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型list[str]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
# - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def deduplicate_headers(headers: Iterable[str]) -> list[str]:
    """保留重复表头，并为后续重复项增加 __2、__3 后缀。"""
    # 状态计算：把`[]`的结果保存到`result`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    result: list[str] = []
    # 状态计算：把`Counter()`的结果保存到`counts`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    counts: Counter[str] = Counter()
    # 循环处理：逐项遍历`headers`，把当前元素绑定到`raw_name`。
    # - 数据变化：每轮只处理一个来源记录、字段、文件或证据项，并显式累计到局部集合或输出对象。
    # - 为什么这样写：逐项处理便于保留行级血缘、隔离单项异常，并控制16GB单机上的峰值内存。
    for raw_name in headers:
        # 状态计算：把`strip_cell(raw_name)`的结果保存到`name`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        name = strip_cell(raw_name)
        # 状态计算：把`1`的结果保存到`counts[name]`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        counts[name] += 1
        # 状态计算：把`'' if counts[name] == 1 else f'__{counts[name]}'`的结果保存到`suffix`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        suffix = "" if counts[name] == 1 else f"__{counts[name]}"
        # 显式调用：执行`result.append(f'{name}{suffix}')`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
        # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
        # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
        result.append(f"{name}{suffix}")
    # 结果返回：把`result`交给调用方并结束当前函数。
    # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return result


# 函数file_sha256：流式计算文件SHA256。
# - 输入：path:Path、chunk_size:int；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型str；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
# - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def file_sha256(path: Path, chunk_size: int = 1024 * 1024) -> str:
    """流式计算文件SHA256。"""
    # 状态计算：把`hashlib.sha256()`的结果保存到`digest`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    digest = hashlib.sha256()
    # 资源上下文：在`path.open('rb')`管理的生命周期内执行后续代码。
    # - 数据变化：上下文负责成对获取和释放文件、会话或临时资源，异常时仍执行清理。
    # - 为什么这样写：显式资源边界可避免连接、文件句柄或临时状态泄漏。
    with path.open("rb") as handle:
        # 条件循环：在`True`保持成立期间重复执行受控步骤。
        # - 数据变化：每轮必须推进索引、分页、重试或状态，否则可能形成无限循环。
        # - 为什么这样写：适合处理分页和有限重试，同时把终止条件保留为可审计的安全边界。
        while True:
            # 状态计算：把`handle.read(chunk_size)`的结果保存到`chunk`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            chunk = handle.read(chunk_size)
            # 条件门禁：判断`not chunk`，条件成立时进入对应的数据、安全或异常处理分支。
            # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
            # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
            if not chunk:
                # 控制流：结束当前循环，使循环或占位分支按既定合同继续。
                # - 数据变化：本语句不直接改变业务记录，只调整当前执行路径。
                # - 为什么这样写：显式控制流比隐式嵌套更容易检查边界和异常处理。
                break
            # 显式调用：执行`digest.update(chunk)`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
            # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
            # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
            digest.update(chunk)
    # 结果返回：把`digest.hexdigest()`交给调用方并结束当前函数。
    # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return digest.hexdigest()


# 函数stable_json：生成稳定、可哈希的JSON。
# - 输入：value:Any；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型str；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
# - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def stable_json(value: Any) -> str:
    """生成稳定、可哈希的JSON。"""
    # 结果返回：把`json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), default=str)`交给调用方并结束当前函数。
    # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )


# 函数parse_snapshot_date_from_path：从父目录 YYYYMMDD 推导快照日期。
# - 输入：path:Path；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型date；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
# - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def parse_snapshot_date_from_path(path: Path) -> date:
    """从父目录 YYYYMMDD 推导快照日期。"""
    # 状态计算：把`path.parent.name`的结果保存到`directory_name`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    directory_name = path.parent.name
    # 条件门禁：判断`not DATE_DIR_PATTERN.fullmatch(directory_name)`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if not DATE_DIR_PATTERN.fullmatch(directory_name):
        # 错误阻断：抛出`DailyFundsIngestError(f'快照目录不是YYYYMMDD：{path.parent}')`并停止当前正常路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
        # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
        raise DailyFundsIngestError(
            f"快照目录不是YYYYMMDD：{path.parent}"
        )
    # 结果返回：把`datetime.strptime(directory_name, '%Y%m%d').date()`交给调用方并结束当前函数。
    # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return datetime.strptime(directory_name, "%Y%m%d").date()


# 函数is_missing：判断来源值是否为缺失标记。
# - 输入：value:Any、missing_tokens:frozenset[str] | set[str]；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型bool；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
# - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def is_missing(
    value: Any,
    missing_tokens: frozenset[str] | set[str] = MISSING_DEFAULTS,
) -> bool:
    """判断来源值是否为缺失标记。"""
    # 结果返回：把`strip_cell(value) in missing_tokens`交给调用方并结束当前函数。
    # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return strip_cell(value) in missing_tokens


# 函数parse_source_number：解析中文数量级数值，保持原有正负号。
# - 输入：value:Any、missing_tokens:frozenset[str] | set[str]；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型float | None；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
# - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def parse_source_number(
    value: Any,
    missing_tokens: frozenset[str] | set[str] = MISSING_DEFAULTS,
) -> float | None:
    """解析中文数量级数值，保持原有正负号。

    示例：
    - 30.3万 -> 303000
    - 6.06亿 -> 606000000
    - 3.97万亿 -> 3970000000000
    - -35.0亿 -> -3500000000
    - — -> None
    """
    # 状态计算：把`strip_cell(value)`的结果保存到`text`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    text = strip_cell(value)
    # 条件门禁：判断`text in missing_tokens`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if text in missing_tokens:
        # 结果返回：把`None`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return None

    # 状态计算：把`text.replace(',', '').replace('％', '%').replace('−', '-').replace('－', '-').replace('＋', '+').repla…`的结果保存到`normalized`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    normalized = (
        text.replace(",", "")
        .replace("％", "%")
        .replace("−", "-")
        .replace("－", "-")
        .replace("＋", "+")
        .replace(" ", "")
    )
    # 条件门禁：判断`normalized.endswith('%')`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if normalized.endswith("%"):
        # 状态计算：把`normalized[:-1]`的结果保存到`normalized`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        normalized = normalized[:-1]

    # 状态计算：把`1.0`的结果保存到`multiplier`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    multiplier = 1.0
    # 循环处理：逐项遍历`MAGNITUDE_MULTIPLIERS`，把当前元素绑定到`(suffix, candidate)`。
    # - 数据变化：每轮只处理一个来源记录、字段、文件或证据项，并显式累计到局部集合或输出对象。
    # - 为什么这样写：逐项处理便于保留行级血缘、隔离单项异常，并控制16GB单机上的峰值内存。
    for suffix, candidate in MAGNITUDE_MULTIPLIERS:
        # 条件门禁：判断`normalized.endswith(suffix)`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if normalized.endswith(suffix):
            # 状态计算：把`candidate`的结果保存到`multiplier`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            multiplier = candidate
            # 状态计算：把`normalized[:-len(suffix)]`的结果保存到`normalized`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            normalized = normalized[: -len(suffix)]
            # 控制流：结束当前循环，使循环或占位分支按既定合同继续。
            # - 数据变化：本语句不直接改变业务记录，只调整当前执行路径。
            # - 为什么这样写：显式控制流比隐式嵌套更容易检查边界和异常处理。
            break

    # 条件门禁：判断`normalized in {'', '+', '-'}`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if normalized in {"", "+", "-"}:
        # 结果返回：把`None`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return None

    # 异常边界：尝试执行可能失败的解析、查询、文件或类型转换步骤，并由后续处理保留错误证据。
    # - 数据变化：正常路径产生业务结果；异常路径不得静默伪造数据，应抛出、记录或隔离。
    # - 为什么这样写：把外部环境故障与业务合同失败分开，便于重试、回滚和准确验收。
    try:
        # 状态计算：把`float(normalized) * multiplier`的结果保存到`result`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        result = float(normalized) * multiplier
    except ValueError as exc:
        # 错误阻断：抛出`DailyFundsIngestError(f'无法解析数值：{text!r}')`并停止当前正常路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
        # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
        raise DailyFundsIngestError(
            f"无法解析数值：{text!r}"
        ) from exc

    # 条件门禁：判断`not math.isfinite(result)`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if not math.isfinite(result):
        # 错误阻断：抛出`DailyFundsIngestError(f'数值不是有限数：{text!r}')`并停止当前正常路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
        # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
        raise DailyFundsIngestError(
            f"数值不是有限数：{text!r}"
        )
    # 结果返回：把`result`交给调用方并结束当前函数。
    # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return result


# 函数parse_source_int：解析整数或带中文数量级的整数。
# - 输入：value:Any、missing_tokens:frozenset[str] | set[str]；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型int | None；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
# - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def parse_source_int(
    value: Any,
    missing_tokens: frozenset[str] | set[str] = MISSING_DEFAULTS,
) -> int | None:
    """解析整数或带中文数量级的整数。"""
    # 状态计算：把`parse_source_number(value, missing_tokens)`的结果保存到`parsed`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    parsed = parse_source_number(value, missing_tokens)
    # 条件门禁：判断`parsed is None`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if parsed is None:
        # 结果返回：把`None`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return None
    # 状态计算：把`round(parsed)`的结果保存到`rounded`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    rounded = round(parsed)
    # 条件门禁：判断`abs(parsed - rounded) > 1e-09`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if abs(parsed - rounded) > 1e-9:
        # 错误阻断：抛出`DailyFundsIngestError(f'来源值不是整数：{value!r}')`并停止当前正常路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
        # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
        raise DailyFundsIngestError(
            f"来源值不是整数：{value!r}"
        )
    # 结果返回：把`int(rounded)`交给调用方并结束当前函数。
    # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return int(rounded)


# 函数normalize_instrument_code：把 = "000001"、="000001" 等来源值标准化为6位代码。
# - 输入：value:Any；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型str；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
# - 为什么这样写：把对象构造、字段映射或标准化转换步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def normalize_instrument_code(value: Any) -> str:
    """把 = "000001"、="000001" 等来源值标准化为6位代码。"""
    # 状态计算：把`strip_cell(value)`的结果保存到`text`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    text = strip_cell(value)
    # 状态计算：把`INSTRUMENT_CODE_PATTERN.search(text)`的结果保存到`match`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    match = INSTRUMENT_CODE_PATTERN.search(text)
    # 条件门禁：判断`match is None`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if match is None:
        # 错误阻断：抛出`DailyFundsIngestError(f'无法识别6位证券代码：{text!r}')`并停止当前正常路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
        # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
        raise DailyFundsIngestError(
            f"无法识别6位证券代码：{text!r}"
        )
    # 结果返回：把`match.group(1)`交给调用方并结束当前函数。
    # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return match.group(1)


# 函数infer_market_candidate：按代码前缀给出市场候选，不作为最终身份权威。
# - 输入：instrument_id:str；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型str；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
# - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def infer_market_candidate(instrument_id: str) -> str:
    """按代码前缀给出市场候选，不作为最终身份权威。"""
    # 条件门禁：判断`instrument_id.startswith(('4', '8', '92'))`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if instrument_id.startswith(("4", "8", "92")):
        # 结果返回：把`'BJ'`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return "BJ"
    # 条件门禁：判断`instrument_id.startswith('6')`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if instrument_id.startswith("6"):
        # 结果返回：把`'SH'`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return "SH"
    # 条件门禁：判断`instrument_id.startswith(('0', '2', '3'))`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if instrument_id.startswith(("0", "2", "3")):
        # 结果返回：把`'SZ'`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return "SZ"
    # 结果返回：把`'UNKNOWN'`交给调用方并结束当前函数。
    # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return "UNKNOWN"


# 函数parse_breadth_counts：解析“涨跌家数”，例如 7/6。
# - 输入：value:Any；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型tuple[int | None, int | None]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
# - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def parse_breadth_counts(value: Any) -> tuple[int | None, int | None]:
    """解析“涨跌家数”，例如 7/6。"""
    # 状态计算：把`strip_cell(value)`的结果保存到`text`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    text = strip_cell(value)
    # 条件门禁：判断`text in MISSING_DEFAULTS`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if text in MISSING_DEFAULTS:
        # 结果返回：把`(None, None)`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return None, None
    # 状态计算：把`re.fullmatch('(\\d+)\\s*/\\s*(\\d+)', text)`的结果保存到`match`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    match = re.fullmatch(r"(\d+)\s*/\s*(\d+)", text)
    # 条件门禁：判断`match is None`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if match is None:
        # 错误阻断：抛出`DailyFundsIngestError(f'无法解析涨跌家数：{text!r}')`并停止当前正常路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
        # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
        raise DailyFundsIngestError(
            f"无法解析涨跌家数：{text!r}"
        )
    # 结果返回：把`(int(match.group(1)), int(match.group(2)))`交给调用方并结束当前函数。
    # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return int(match.group(1)), int(match.group(2))


# 函数parse_breadth_ratio：解析涨跌比，并保留全涨、全跌等状态。
# - 输入：value:Any、up_count:int | None、down_count:int | None、missing_tokens:frozenset[str] | set[str]；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型tuple[float | None, str]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
# - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def parse_breadth_ratio(
    value: Any,
    up_count: int | None,
    down_count: int | None,
    missing_tokens: frozenset[str] | set[str] = MISSING_DEFAULTS,
) -> tuple[float | None, str]:
    """解析涨跌比，并保留全涨、全跌等状态。"""
    # 状态计算：把`strip_cell(value)`的结果保存到`text`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    text = strip_cell(value)
    # 条件门禁：判断`text in missing_tokens`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if text in missing_tokens:
        # 结果返回：把`(None, 'UNKNOWN')`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return None, "UNKNOWN"
    # 条件门禁：判断`text == '全涨'`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if text == "全涨":
        # 结果返回：把`(None, 'ALL_UP')`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return None, "ALL_UP"
    # 条件门禁：判断`text == '全跌'`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if text == "全跌":
        # 结果返回：把`(None, 'ALL_DOWN')`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return None, "ALL_DOWN"
    # 状态计算：把`parse_source_number(text, missing_tokens)`的结果保存到`ratio`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    ratio = parse_source_number(text, missing_tokens)
    # 条件门禁：判断`ratio is None`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if ratio is None:
        # 结果返回：把`(None, 'UNKNOWN')`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return None, "UNKNOWN"

    # 条件门禁：判断`up_count is not None and down_count not in {None, 0} and (abs(ratio - up_count / down_count) > 0.05)`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if (
        up_count is not None
        and down_count not in {None, 0}
        and abs(ratio - up_count / down_count) > 0.05
    ):
        # 结果返回：把`(ratio, 'RATIO_MISMATCH_WARNING')`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return ratio, "RATIO_MISMATCH_WARNING"
    # 结果返回：把`(ratio, 'NORMAL')`交给调用方并结束当前函数。
    # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return ratio, "NORMAL"


# 函数first_non_missing：按优先级取得首个非缺失来源字段。
# - 输入：row:dict[str, str]、names:Iterable[str]、missing_tokens:frozenset[str] | set[str]；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型str | None；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
# - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def first_non_missing(
    row: dict[str, str],
    names: Iterable[str],
    missing_tokens: frozenset[str] | set[str],
) -> str | None:
    """按优先级取得首个非缺失来源字段。"""
    # 循环处理：逐项遍历`names`，把当前元素绑定到`name`。
    # - 数据变化：每轮只处理一个来源记录、字段、文件或证据项，并显式累计到局部集合或输出对象。
    # - 为什么这样写：逐项处理便于保留行级血缘、隔离单项异常，并控制16GB单机上的峰值内存。
    for name in names:
        # 状态计算：把`row.get(name)`的结果保存到`value`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        value = row.get(name)
        # 条件门禁：判断`value is not None and (not is_missing(value, missing_tokens))`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if value is not None and not is_missing(value, missing_tokens):
            # 结果返回：把`value`交给调用方并结束当前函数。
            # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
            # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
            return value
    # 结果返回：把`None`交给调用方并结束当前函数。
    # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return None


# 函数normalized_base_metadata：构造三类物理Raw表共享的血缘字段。
# - 输入：dataset:DatasetSpec、snapshot_date:date、source_file:Path、source_file_hash:str、schema_version:str、source_row_number:int、raw_row:dict[str, str]、entity_key:str等；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型dict[str, Any]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
# - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def normalized_base_metadata(
    *,
    dataset: DatasetSpec,
    snapshot_date: date,
    source_file: Path,
    source_file_hash: str,
    schema_version: str,
    source_row_number: int,
    raw_row: dict[str, str],
    entity_key: str,
    ingest_batch_id: str,
    ingested_at: datetime,
) -> dict[str, Any]:
    """构造三类物理Raw表共享的血缘字段。"""
    # 状态计算：把`datetime.fromtimestamp(source_file.stat().st_mtime, tz=timezone.utc)`的结果保存到`mtime`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    mtime = datetime.fromtimestamp(
        source_file.stat().st_mtime,
        tz=timezone.utc,
    )
    # 结果返回：把`{'dataset_id': dataset.dataset_id, 'snapshot_date': snapshot_date.isoformat(), 'snapshot_month': snapshot_date.strftime…`交给调用方并结束当前函数。
    # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return {
        "dataset_id": dataset.dataset_id,
        "snapshot_date": snapshot_date.isoformat(),
        "snapshot_month": snapshot_date.strftime("%Y-%m"),
        "snapshot_phase": dataset.snapshot_phase,
        "schema_version": schema_version,
        "entity_key": entity_key,
        "source_row_number": source_row_number,
        "source_file_name": source_file.name,
        "source_file_relative_path": (
            f"{source_file.parent.name}/{source_file.name}"
        ),
        "source_file_size_bytes": source_file.stat().st_size,
        "source_file_mtime_utc": mtime.isoformat(),
        "source_file_sha256": source_file_hash,
        "row_sha256": hashlib.sha256(
            stable_json(raw_row).encode("utf-8")
        ).hexdigest(),
        "ingest_batch_id": ingest_batch_id,
        "ingested_at_utc": ingested_at.astimezone(
            timezone.utc
        ).isoformat(),
        "quality_status": "PASSED",
        "raw_row_json": stable_json(raw_row),
    }


# 函数normalize_security_row：标准化 hq / kphq 到安全Raw结构。
# - 输入：row:dict[str, str]、dataset:DatasetSpec、snapshot_date:date、source_file:Path、source_file_hash:str、schema_version:str、source_row_number:int、ingest_batch_id:str等；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型dict[str, Any]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
# - 为什么这样写：把对象构造、字段映射或标准化转换步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def normalize_security_row(
    row: dict[str, str],
    *,
    dataset: DatasetSpec,
    snapshot_date: date,
    source_file: Path,
    source_file_hash: str,
    schema_version: str,
    source_row_number: int,
    ingest_batch_id: str,
    ingested_at: datetime,
    missing_tokens: frozenset[str],
) -> dict[str, Any]:
    """标准化 hq / kphq 到安全Raw结构。"""
    # 状态计算：把`normalize_instrument_code(row.get('代码'))`的结果保存到`instrument_id`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    instrument_id = normalize_instrument_code(row.get("代码"))
    # 状态计算：把`normalized_base_metadata(dataset=dataset, snapshot_date=snapshot_date, source_file=source_file, sou…`的结果保存到`base`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    base = normalized_base_metadata(
        dataset=dataset,
        snapshot_date=snapshot_date,
        source_file=source_file,
        source_file_hash=source_file_hash,
        schema_version=schema_version,
        source_row_number=source_row_number,
        raw_row=row,
        entity_key=instrument_id,
        ingest_batch_id=ingest_batch_id,
        ingested_at=ingested_at,
    )

    # 状态计算：把`lambda *names: first_non_missing(row, names, missing_tokens)`的结果保存到`value`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    value = lambda *names: first_non_missing(
        row, names, missing_tokens
    )
    # 状态计算：把`lambda *names: parse_source_number(value(*names), missing_tokens)`的结果保存到`number`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    number = lambda *names: parse_source_number(
        value(*names), missing_tokens
    )
    # 状态计算：把`lambda *names: parse_source_int(value(*names), missing_tokens)`的结果保存到`integer`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    integer = lambda *names: parse_source_int(
        value(*names), missing_tokens
    )

    # 显式调用：执行`base.update({'instrument_id': instrument_id, 'market_candidate': infer_market_candidate(instrument_id), 'instrument_name': strip_cell(row.g…`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
    # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
    # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
    base.update(
        {
            "instrument_id": instrument_id,
            "market_candidate": infer_market_candidate(
                instrument_id
            ),
            "instrument_name": strip_cell(row.get("名称")),
            "last_price": number("最新"),
            "pct_change": number("涨幅%"),
            "price_change": number("涨跌"),
            "total_volume_lot": number("总量", "总手"),
            "current_volume_lot": number("现量", "现手"),
            "bid_price": number("买入价"),
            "ask_price": number("卖出价"),
            "speed_pct": number("涨速%"),
            "turnover_pct": number("换手%"),
            "amount_cny": number("金额"),
            "pe_dynamic": number("市盈率(动)"),
            "industry_name": strip_cell(row.get("所属行业")),
            "high_price": number("最高"),
            "low_price": number("最低"),
            "open_price": number("开盘"),
            "prev_close": number("昨收"),
            "amplitude_pct": number("振幅%"),
            "volume_ratio": number("量比"),
            "order_imbalance_pct": number("委比%"),
            "order_imbalance_lot": number("委差"),
            "avg_price": number("均价"),
            "inner_volume_lot": number("内盘"),
            "outer_volume_lot": number("外盘"),
            "inner_outer_ratio": number("内外比"),
            "bid1_volume_lot": number("买一量"),
            "ask1_volume_lot": number("卖一量"),
            "pb": number("市净率"),
            "total_shares": number("总股本"),
            "total_market_cap_cny": number("总市值"),
            "float_shares": number("流通股本"),
            "float_market_cap_cny": number("流通市值"),
            "return_3d_pct": number("3日涨幅%"),
            "return_6d_pct": number("6日涨幅%"),
            "turnover_3d_pct": number("3日换手%"),
            "turnover_6d_pct": number("6日换手%"),
            "consecutive_up_days": integer(
                "连涨天数1", "连涨天数__2", "连涨天数"
            ),
            "return_month_pct": number("本月涨幅%"),
            "return_ytd_pct": number(
                "今年涨幅%1", "今年涨幅%__2", "今年涨幅%"
            ),
            "return_1m_pct": number("近一月涨幅%"),
            "return_1y_pct": number(
                "近一年涨幅%1", "近一年涨幅%__2", "近一年涨幅%"
            ),
            "listing_date_raw": strip_cell(row.get("上市日")),
            "speed_5m_pct": number("5分钟涨速%"),
            "return_20d_pct": number("20日涨幅%"),
            "source_volume_unit": "LOT_CANDIDATE",
            "canonical_volume_transform": "multiply_by_100",
            "source_amount_unit": "CNY",
        }
    )
    # 结果返回：把`base`交给调用方并结束当前函数。
    # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return base


# 函数normalize_classification_row：标准化 hy / gn / kphy / kpgn 到安全Raw结构。
# - 输入：row:dict[str, str]、dataset:DatasetSpec、snapshot_date:date、source_file:Path、source_file_hash:str、schema_version:str、source_row_number:int、ingest_batch_id:str等；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型dict[str, Any]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
# - 为什么这样写：把对象构造、字段映射或标准化转换步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def normalize_classification_row(
    row: dict[str, str],
    *,
    dataset: DatasetSpec,
    snapshot_date: date,
    source_file: Path,
    source_file_hash: str,
    schema_version: str,
    source_row_number: int,
    ingest_batch_id: str,
    ingested_at: datetime,
    missing_tokens: frozenset[str],
) -> dict[str, Any]:
    """标准化 hy / gn / kphy / kpgn 到安全Raw结构。"""
    # 状态计算：把`strip_cell(row.get('名称'))`的结果保存到`node_name`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    node_name = strip_cell(row.get("名称"))
    # 条件门禁：判断`not node_name`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if not node_name:
        # 错误阻断：抛出`DailyFundsIngestError('分类节点名称为空。')`并停止当前正常路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
        # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
        raise DailyFundsIngestError("分类节点名称为空。")
    # 状态计算：把`normalized_base_metadata(dataset=dataset, snapshot_date=snapshot_date, source_file=source_file, sou…`的结果保存到`base`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    base = normalized_base_metadata(
        dataset=dataset,
        snapshot_date=snapshot_date,
        source_file=source_file,
        source_file_hash=source_file_hash,
        schema_version=schema_version,
        source_row_number=source_row_number,
        raw_row=row,
        entity_key=node_name,
        ingest_batch_id=ingest_batch_id,
        ingested_at=ingested_at,
    )

    # 状态计算：把`lambda *names: first_non_missing(row, names, missing_tokens)`的结果保存到`value`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    value = lambda *names: first_non_missing(
        row, names, missing_tokens
    )
    # 状态计算：把`lambda *names: parse_source_number(value(*names), missing_tokens)`的结果保存到`number`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    number = lambda *names: parse_source_number(
        value(*names), missing_tokens
    )
    # 状态计算：把`lambda *names: parse_source_int(value(*names), missing_tokens)`的结果保存到`integer`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    integer = lambda *names: parse_source_int(
        value(*names), missing_tokens
    )
    # 状态计算：把`parse_breadth_counts(row.get('涨跌家数'))`的结果保存到`(up_count, down_count)`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    up_count, down_count = parse_breadth_counts(
        row.get("涨跌家数")
    )
    # 状态计算：把`parse_breadth_ratio(row.get('涨跌比'), up_count, down_count, missing_tokens)`的结果保存到`(breadth_ratio, breadth_status)`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    breadth_ratio, breadth_status = parse_breadth_ratio(
        row.get("涨跌比"),
        up_count,
        down_count,
        missing_tokens,
    )

    # 显式调用：执行`base.update({'classification_type': dataset.classification_type, 'node_name_raw': node_name, 'pct_change': number('涨幅%'), 'return_3d_pct': …`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
    # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
    # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
    base.update(
        {
            "classification_type": dataset.classification_type,
            "node_name_raw": node_name,
            "pct_change": number("涨幅%"),
            "return_3d_pct": number("3日涨幅%"),
            "speed_pct": number("涨速%"),
            "leading_stock_name": strip_cell(row.get("领涨股")),
            "up_count": up_count,
            "down_count": down_count,
            "breadth_ratio": breadth_ratio,
            "breadth_status": breadth_status,
            "limit_up_count": integer("涨停家数"),
            "turnover_pct": number("换手%"),
            "volume_ratio": number("量比"),
            "turnover_3d_pct": number("3日换手%"),
            "return_5d_pct": number("5日涨幅%"),
            "return_10d_pct": number("10日涨幅%"),
            "return_20d_pct": number("20日涨幅%"),
            "volume_lot": number("成交量"),
            "amount_cny": number("金额"),
            "total_market_cap_cny": number("总市值"),
            "float_market_cap_cny": number("流通市值"),
            "average_return_pct": number("平均收益"),
            "average_shares": number("平均股本"),
            "pe_ratio": number("市盈率"),
            "source_volume_unit": "LOT_CANDIDATE",
            "canonical_volume_transform": "multiply_by_100",
            "source_amount_unit": "CNY",
        }
    )
    # 结果返回：把`base`交给调用方并结束当前函数。
    # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return base


# 函数normalize_money_flow_row：标准化 zj，保留来源流出字段的原始负号。
# - 输入：row:dict[str, str]、dataset:DatasetSpec、snapshot_date:date、source_file:Path、source_file_hash:str、schema_version:str、source_row_number:int、ingest_batch_id:str等；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型dict[str, Any]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
# - 为什么这样写：把对象构造、字段映射或标准化转换步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def normalize_money_flow_row(
    row: dict[str, str],
    *,
    dataset: DatasetSpec,
    snapshot_date: date,
    source_file: Path,
    source_file_hash: str,
    schema_version: str,
    source_row_number: int,
    ingest_batch_id: str,
    ingested_at: datetime,
    missing_tokens: frozenset[str],
) -> dict[str, Any]:
    """标准化 zj，保留来源流出字段的原始负号。"""
    # 状态计算：把`normalize_instrument_code(row.get('代码'))`的结果保存到`instrument_id`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    instrument_id = normalize_instrument_code(row.get("代码"))
    # 状态计算：把`normalized_base_metadata(dataset=dataset, snapshot_date=snapshot_date, source_file=source_file, sou…`的结果保存到`base`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    base = normalized_base_metadata(
        dataset=dataset,
        snapshot_date=snapshot_date,
        source_file=source_file,
        source_file_hash=source_file_hash,
        schema_version=schema_version,
        source_row_number=source_row_number,
        raw_row=row,
        entity_key=instrument_id,
        ingest_batch_id=ingest_batch_id,
        ingested_at=ingested_at,
    )
    # 状态计算：把`lambda *names: first_non_missing(row, names, missing_tokens)`的结果保存到`value`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    value = lambda *names: first_non_missing(
        row, names, missing_tokens
    )
    # 状态计算：把`lambda *names: parse_source_number(value(*names), missing_tokens)`的结果保存到`number`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    number = lambda *names: parse_source_number(
        value(*names), missing_tokens
    )

    # 显式调用：执行`base.update({'instrument_id': instrument_id, 'market_candidate': infer_market_candidate(instrument_id), 'instrument_name': strip_cell(row.g…`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
    # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
    # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
    base.update(
        {
            "instrument_id": instrument_id,
            "market_candidate": infer_market_candidate(
                instrument_id
            ),
            "instrument_name": strip_cell(row.get("名称")),
            "last_price": number("最新"),
            "pct_change": number("涨幅%"),
            "main_net_inflow_cny": number("主力净流入"),
            "auction_net_inflow_cny": number("集合竞价"),
            "super_large_inflow_cny": number("超大单流入"),
            "super_large_outflow_cny": number("超大单流出"),
            "super_large_net_cny": number("超大单净额"),
            "super_large_net_ratio_pct": number(
                "超大单净占比%"
            ),
            "large_inflow_cny": number("大单流入"),
            "large_outflow_cny": number("大单流出"),
            "large_net_cny": number("大单净额"),
            "large_net_ratio_pct": number("大单净占比%"),
            "medium_inflow_cny": number("中单流入"),
            "medium_outflow_cny": number("中单流出"),
            "medium_net_cny": number("中单净额"),
            "medium_net_ratio_pct": number("中单净占比%"),
            "small_inflow_cny": number("小单流入"),
            "small_outflow_cny": number("小单流出"),
            "small_net_cny": number("小单净额"),
            "small_net_ratio_pct": number("小单净占比%"),
            "source_amount_unit": "CNY",
            "outflow_sign_policy": "PRESERVE_SOURCE_SIGN",
        }
    )
    # 结果返回：把`base`交给调用方并结束当前函数。
    # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return base


# 函数normalize_row：按三类物理Raw表选择标准化函数。
# - 输入：row:dict[str, str]、dataset:DatasetSpec、snapshot_date:date、source_file:Path、source_file_hash:str、schema_version:str、source_row_number:int、ingest_batch_id:str等；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型dict[str, Any]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
# - 为什么这样写：把对象构造、字段映射或标准化转换步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def normalize_row(
    row: dict[str, str],
    *,
    dataset: DatasetSpec,
    snapshot_date: date,
    source_file: Path,
    source_file_hash: str,
    schema_version: str,
    source_row_number: int,
    ingest_batch_id: str,
    ingested_at: datetime,
    missing_tokens: frozenset[str],
) -> dict[str, Any]:
    """按三类物理Raw表选择标准化函数。"""
    # 状态计算：把`{'row': row, 'dataset': dataset, 'snapshot_date': snapshot_date, 'source_file': source_file, 'sourc…`的结果保存到`kwargs`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    kwargs = {
        "row": row,
        "dataset": dataset,
        "snapshot_date": snapshot_date,
        "source_file": source_file,
        "source_file_hash": source_file_hash,
        "schema_version": schema_version,
        "source_row_number": source_row_number,
        "ingest_batch_id": ingest_batch_id,
        "ingested_at": ingested_at,
        "missing_tokens": missing_tokens,
    }
    # 条件门禁：判断`dataset.family == 'security_snapshot'`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if dataset.family == "security_snapshot":
        # 结果返回：把`normalize_security_row(**kwargs)`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return normalize_security_row(**kwargs)
    # 条件门禁：判断`dataset.family == 'classification_snapshot'`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if dataset.family == "classification_snapshot":
        # 结果返回：把`normalize_classification_row(**kwargs)`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return normalize_classification_row(**kwargs)
    # 条件门禁：判断`dataset.family == 'money_flow_snapshot'`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if dataset.family == "money_flow_snapshot":
        # 结果返回：把`normalize_money_flow_row(**kwargs)`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return normalize_money_flow_row(**kwargs)
    # 错误阻断：抛出`DailyFundsIngestError(f'不支持的family：{dataset.family}')`并停止当前正常路径。
    # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
    # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
    raise DailyFundsIngestError(
        f"不支持的family：{dataset.family}"
    )


# 函数_trim_trailing_delimiter_cell：移除来源每行末尾额外制表符产生的空单元格。
# - 输入：cells:list[str]、expected_length:int | None；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型list[str]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
# - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def _trim_trailing_delimiter_cell(
    cells: list[str],
    expected_length: int | None = None,
) -> list[str]:
    """移除来源每行末尾额外制表符产生的空单元格。"""
    # 状态计算：把`list(cells)`的结果保存到`result`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    result = list(cells)
    # 条件门禁：判断`expected_length is None`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if expected_length is None:
        # 条件循环：在`result and strip_cell(result[-1]) == ''`保持成立期间重复执行受控步骤。
        # - 数据变化：每轮必须推进索引、分页、重试或状态，否则可能形成无限循环。
        # - 为什么这样写：适合处理分页和有限重试，同时把终止条件保留为可审计的安全边界。
        while result and strip_cell(result[-1]) == "":
            # 显式调用：执行`result.pop()`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
            # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
            # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
            result.pop()
        # 结果返回：把`result`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return result

    # 条件循环：在`len(result) > expected_length and strip_cell(result[-1]) == ''`保持成立期间重复执行受控步骤。
    # - 数据变化：每轮必须推进索引、分页、重试或状态，否则可能形成无限循环。
    # - 为什么这样写：适合处理分页和有限重试，同时把终止条件保留为可审计的安全边界。
    while (
        len(result) > expected_length
        and strip_cell(result[-1]) == ""
    ):
        # 显式调用：执行`result.pop()`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
        # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
        # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
        result.pop()
    # 结果返回：把`result`交给调用方并结束当前函数。
    # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return result


# 函数iter_source_rows：逐行读取来源文件，返回物理行号和原始单元格。
# - 输入：file_path:Path、encoding:str、delimiter:str；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型Iterator[tuple[int, list[str]]]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
# - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def iter_source_rows(
    file_path: Path,
    *,
    encoding: str,
    delimiter: str,
) -> Iterator[tuple[int, list[str]]]:
    """逐行读取来源文件，返回物理行号和原始单元格。"""
    # 资源上下文：在`file_path.open('r', encoding=encoding, newline='', errors='strict')`管理的生命周期内执行后续代码。
    # - 数据变化：上下文负责成对获取和释放文件、会话或临时资源，异常时仍执行清理。
    # - 为什么这样写：显式资源边界可避免连接、文件句柄或临时状态泄漏。
    with file_path.open(
        "r",
        encoding=encoding,
        newline="",
        errors="strict",
    ) as handle:
        # 状态计算：把`csv.reader(handle, delimiter=delimiter)`的结果保存到`reader`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        reader = csv.reader(handle, delimiter=delimiter)
        # 循环处理：逐项遍历`enumerate(reader, start=1)`，把当前元素绑定到`(physical_line_number, cells)`。
        # - 数据变化：每轮只处理一个来源记录、字段、文件或证据项，并显式累计到局部集合或输出对象。
        # - 为什么这样写：逐项处理便于保留行级血缘、隔离单项异常，并控制16GB单机上的峰值内存。
        for physical_line_number, cells in enumerate(reader, start=1):
            # 显式调用：执行`(yield (physical_line_number, cells))`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
            # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
            # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
            yield physical_line_number, cells


# 函数parse_source_file：完整扫描一个来源文件并生成解析摘要。
# - 输入：file_path:Path、dataset:DatasetSpec、contract:DailyFundsContract、ingest_batch_id:str、ingested_at:datetime、sample_limit:int；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型ParsedSourceFile；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
# - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def parse_source_file(
    file_path: Path,
    *,
    dataset: DatasetSpec,
    contract: DailyFundsContract,
    ingest_batch_id: str,
    ingested_at: datetime,
    sample_limit: int = 2,
) -> ParsedSourceFile:
    """完整扫描一个来源文件并生成解析摘要。"""
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
        # 状态计算：把`next(iterator)`的结果保存到`(header_line_number, header_cells)`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        header_line_number, header_cells = next(iterator)
    except StopIteration as exc:
        # 错误阻断：抛出`DailyFundsIngestError(f'空文件：{file_path}')`并停止当前正常路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
        # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
        raise DailyFundsIngestError(
            f"空文件：{file_path}"
        ) from exc

    # 状态计算：把`_trim_trailing_delimiter_cell(header_cells)`的结果保存到`header_cells`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    header_cells = _trim_trailing_delimiter_cell(header_cells)
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

    # 状态计算：把`[]`的结果保存到`anomaly_codes`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    anomaly_codes: list[str] = []
    # 状态计算：把`[]`的结果保存到`anomaly_details`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    anomaly_details: list[str] = []
    # 条件门禁：判断`known_schema is None`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if known_schema is None:
        # 显式调用：执行`anomaly_codes.append('UNKNOWN_SCHEMA')`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
        # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
        # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
        anomaly_codes.append("UNKNOWN_SCHEMA")
        # 显式调用：执行`anomaly_details.append(f'unknown_header_sha256={exact_hash}')`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
        # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
        # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
        anomaly_details.append(
            f"unknown_header_sha256={exact_hash}"
        )
        # 状态计算：把`None`的结果保存到`schema_version`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        schema_version = None
        # 状态计算：把`[strip_cell(item) for item in header_cells]`的结果保存到`expected_header`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        expected_header = [strip_cell(item) for item in header_cells]
    else:
        # 状态计算：把`known_schema.schema_version`的结果保存到`schema_version`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        schema_version = known_schema.schema_version
        # 状态计算：把`list(known_schema.headers)`的结果保存到`expected_header`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        expected_header = list(known_schema.headers)

    # 状态计算：把`deduplicate_headers(expected_header)`的结果保存到`deduplicated_header`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    deduplicated_header = deduplicate_headers(expected_header)
    # 状态计算：把`len(expected_header)`的结果保存到`expected_length`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    expected_length = len(expected_header)
    # 状态计算：把`0`的结果保存到`row_count`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    row_count = 0
    # 状态计算：把`0`的结果保存到`malformed_row_count`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    malformed_row_count = 0
    # 状态计算：把`0`的结果保存到`missing_cell_count`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    missing_cell_count = 0
    # 状态计算：把`0`的结果保存到`normalization_error_count`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    normalization_error_count = 0
    # 状态计算：把`[]`的结果保存到`keys`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    keys: list[str] = []
    # 状态计算：把`[]`的结果保存到`samples`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    samples: list[dict[str, Any]] = []

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
        if not cells or all(strip_cell(item) == "" for item in cells):
            # 控制流：跳过本轮剩余步骤，使循环或占位分支按既定合同继续。
            # - 数据变化：本语句不直接改变业务记录，只调整当前执行路径。
            # - 为什么这样写：显式控制流比隐式嵌套更容易检查边界和异常处理。
            continue
        # 状态计算：把`1`的结果保存到`row_count`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        row_count += 1

        # 条件门禁：判断`len(cells) != expected_length`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if len(cells) != expected_length:
            # 状态计算：把`1`的结果保存到`malformed_row_count`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            malformed_row_count += 1
            # 条件门禁：判断`malformed_row_count <= 10`，条件成立时进入对应的数据、安全或异常处理分支。
            # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
            # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
            if malformed_row_count <= 10:
                # 显式调用：执行`anomaly_details.append(f'malformed_row:line={physical_line_number},expected={expected_length},actual={len(cells)}')`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
                # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
                # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
                anomaly_details.append(
                    "malformed_row:"
                    f"line={physical_line_number},"
                    f"expected={expected_length},"
                    f"actual={len(cells)}"
                )
            # 控制流：跳过本轮剩余步骤，使循环或占位分支按既定合同继续。
            # - 数据变化：本语句不直接改变业务记录，只调整当前执行路径。
            # - 为什么这样写：显式控制流比隐式嵌套更容易检查边界和异常处理。
            continue

        # 状态计算：把`{deduplicated_header[index]: strip_cell(value) for index, value in enumerate(cells)}`的结果保存到`raw_row`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        raw_row = {
            deduplicated_header[index]: strip_cell(value)
            for index, value in enumerate(cells)
        }
        # 状态计算：把`sum((is_missing(value, contract.missing_tokens) for value in raw_row.values()))`的结果保存到`missing_cell_count`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        missing_cell_count += sum(
            is_missing(value, contract.missing_tokens)
            for value in raw_row.values()
        )

        # 条件门禁：判断`known_schema is None`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if known_schema is None:
            # 控制流：跳过本轮剩余步骤，使循环或占位分支按既定合同继续。
            # - 数据变化：本语句不直接改变业务记录，只调整当前执行路径。
            # - 为什么这样写：显式控制流比隐式嵌套更容易检查边界和异常处理。
            continue

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
        except Exception as exc:  # noqa: BLE001
            # 状态计算：把`1`的结果保存到`normalization_error_count`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            normalization_error_count += 1
            # 条件门禁：判断`normalization_error_count <= 10`，条件成立时进入对应的数据、安全或异常处理分支。
            # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
            # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
            if normalization_error_count <= 10:
                # 显式调用：执行`anomaly_details.append(f'normalization_error:line={physical_line_number},type={type(exc).__name__},message={exc}')`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
                # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
                # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
                anomaly_details.append(
                    "normalization_error:"
                    f"line={physical_line_number},"
                    f"type={type(exc).__name__},"
                    f"message={exc}"
                )
            # 控制流：跳过本轮剩余步骤，使循环或占位分支按既定合同继续。
            # - 数据变化：本语句不直接改变业务记录，只调整当前执行路径。
            # - 为什么这样写：显式控制流比隐式嵌套更容易检查边界和异常处理。
            continue

        # 显式调用：执行`keys.append(str(normalized['entity_key']))`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
        # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
        # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
        keys.append(str(normalized["entity_key"]))
        # 条件门禁：判断`len(samples) < sample_limit`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if len(samples) < sample_limit:
            # 显式调用：执行`samples.append(normalized)`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
            # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
            # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
            samples.append(normalized)

    # 状态计算：把`sum((count - 1 for count in Counter(keys).values() if count > 1))`的结果保存到`duplicate_key_count`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    duplicate_key_count = sum(
        count - 1
        for count in Counter(keys).values()
        if count > 1
    )
    # 条件门禁：判断`malformed_row_count`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if malformed_row_count:
        # 显式调用：执行`anomaly_codes.append('MALFORMED_ROW')`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
        # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
        # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
        anomaly_codes.append("MALFORMED_ROW")
    # 条件门禁：判断`normalization_error_count`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if normalization_error_count:
        # 显式调用：执行`anomaly_codes.append('ROW_NORMALIZATION_FAILED')`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
        # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
        # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
        anomaly_codes.append("ROW_NORMALIZATION_FAILED")
    # 条件门禁：判断`duplicate_key_count`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if duplicate_key_count:
        # 显式调用：执行`anomaly_codes.append('DUPLICATE_ENTITY_KEY')`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
        # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
        # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
        anomaly_codes.append("DUPLICATE_ENTITY_KEY")

    # 结果返回：把`ParsedSourceFile(dataset_id=dataset.dataset_id, snapshot_date=snapshot_date, file_path=file_path, file_size_bytes=file_…`交给调用方并结束当前函数。
    # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return ParsedSourceFile(
        dataset_id=dataset.dataset_id,
        snapshot_date=snapshot_date,
        file_path=file_path,
        file_size_bytes=file_path.stat().st_size,
        source_file_sha256=source_hash,
        schema_version=schema_version,
        exact_header_sha256=exact_hash,
        row_count=row_count,
        unique_key_count=len(set(keys)),
        duplicate_key_count=duplicate_key_count,
        malformed_row_count=malformed_row_count,
        missing_cell_count=missing_cell_count,
        normalization_error_count=normalization_error_count,
        entity_keys=frozenset(keys),
        normalized_samples=tuple(samples),
        anomaly_codes=tuple(anomaly_codes),
        anomaly_details=tuple(anomaly_details),
    )


# 函数discover_snapshot_directories：发现根目录下一层的 YYYYMMDD 快照目录。
# - 输入：root:Path；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型list[Path]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
# - 为什么这样写：把只读查询或来源发现步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def discover_snapshot_directories(root: Path) -> list[Path]:
    """发现根目录下一层的 YYYYMMDD 快照目录。"""
    # 条件门禁：判断`not root.exists()`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if not root.exists():
        # 错误阻断：抛出`DailyFundsIngestError(f'数据根目录不存在：{root}')`并停止当前正常路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
        # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
        raise DailyFundsIngestError(
            f"数据根目录不存在：{root}"
        )
    # 结果返回：把`sorted((path for path in root.iterdir() if path.is_dir() and DATE_DIR_PATTERN.fullmatch(path.name)))`交给调用方并结束当前函数。
    # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return sorted(
        path
        for path in root.iterdir()
        if path.is_dir()
        and DATE_DIR_PATTERN.fullmatch(path.name)
    )


# 函数_file_result_row：执行_file_result_row对应的业务处理。
# - 输入：result:ParsedSourceFile、family:str、status:str、quarantine_reason:str；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型dict[str, Any]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
# - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def _file_result_row(
    result: ParsedSourceFile,
    *,
    family: str,
    status: str,
    quarantine_reason: str = "",
) -> dict[str, Any]:
    # 结果返回：把`{'snapshot_date': result.snapshot_date.strftime('%Y%m%d'), 'dataset_id': result.dataset_id, 'family': family, 'file_nam…`交给调用方并结束当前函数。
    # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return {
        "snapshot_date": result.snapshot_date.strftime("%Y%m%d"),
        "dataset_id": result.dataset_id,
        "family": family,
        "file_name": result.file_path.name,
        "file_size_bytes": result.file_size_bytes,
        "source_file_sha256": result.source_file_sha256,
        "schema_version": result.schema_version or "",
        "exact_header_sha256": result.exact_header_sha256,
        "row_count": result.row_count,
        "unique_key_count": result.unique_key_count,
        "duplicate_key_count": result.duplicate_key_count,
        "malformed_row_count": result.malformed_row_count,
        "missing_cell_count": result.missing_cell_count,
        "normalization_error_count": result.normalization_error_count,
        "status": status,
        "quarantine_reason": quarantine_reason,
        "anomaly_codes": "|".join(result.anomaly_codes),
        "anomaly_details": "|".join(result.anomaly_details),
    }


# 函数_write_csv：执行_write_csv对应的业务处理。
# - 输入：path:Path、rows:list[dict[str, Any]]、fieldnames:list[str]；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型None；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：该函数名称涉及写入能力，只有调用方显式进入受控模式时才可能产生数据库或文件副作用；注释迁移和验证不会调用它。
# - 为什么这样写：把显式写入或持久化步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def _write_csv(
    path: Path,
    rows: list[dict[str, Any]],
    fieldnames: list[str],
) -> None:
    # 资源上下文：在`path.open('w', encoding='utf-8-sig', newline='')`管理的生命周期内执行后续代码。
    # - 数据变化：上下文负责成对获取和释放文件、会话或临时资源，异常时仍执行清理。
    # - 为什么这样写：显式资源边界可避免连接、文件句柄或临时状态泄漏。
    with path.open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as handle:
        # 状态计算：把`csv.DictWriter(handle, fieldnames=fieldnames)`的结果保存到`writer`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        # 显式调用：执行`writer.writeheader()`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
        # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
        # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
        writer.writeheader()
        # 显式调用：执行`writer.writerows(rows)`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
        # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
        # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
        writer.writerows(rows)


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
    # 条件门禁：判断`isinstance(value, (list, tuple, set, frozenset))`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if isinstance(value, (list, tuple, set, frozenset)):
        # 结果返回：把`[_json_safe(item) for item in value]`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return [_json_safe(item) for item in value]
    # 条件门禁：判断`isinstance(value, (date, datetime))`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if isinstance(value, (date, datetime)):
        # 结果返回：把`value.isoformat()`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return value.isoformat()
    # 条件门禁：判断`isinstance(value, Path)`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if isinstance(value, Path):
        # 结果返回：把`str(value)`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return str(value)
    # 条件门禁：判断`isinstance(value, float) and (not math.isfinite(value))`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if isinstance(value, float) and not math.isfinite(value):
        # 结果返回：把`None`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return None
    # 结果返回：把`value`交给调用方并结束当前函数。
    # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return value


# 函数run_daily_funds_preflight：执行全量只读预导入并写出报告。
# - 输入：root:Path、contract_path:Path、output_dir:Path、generated_at:datetime | None；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型dict[str, Any]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
# - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def run_daily_funds_preflight(
    *,
    root: Path,
    contract_path: Path,
    output_dir: Path,
    generated_at: datetime | None = None,
) -> dict[str, Any]:
    """执行全量只读预导入并写出报告。"""
    # 状态计算：把`load_daily_funds_contract(contract_path)`的结果保存到`contract`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    contract = load_daily_funds_contract(contract_path)
    # 状态计算：把`validate_daily_funds_contract(contract)`的结果保存到`contract_report`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    contract_report = validate_daily_funds_contract(contract)
    # 条件门禁：判断`contract_report['overall_status'] != 'PASSED'`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if contract_report["overall_status"] != "PASSED":
        # 错误阻断：抛出`DailyFundsIngestError(f"来源合同校验失败：{contract_report['issues']}")`并停止当前正常路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
        # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
        raise DailyFundsIngestError(
            f"来源合同校验失败：{contract_report['issues']}"
        )

    # 状态计算：把`generated_at or datetime.now(timezone.utc)`的结果保存到`generated_at`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    generated_at = generated_at or datetime.now(timezone.utc)
    # 状态计算：把`'task016a_' + generated_at.astimezone(timezone.utc).strftime('%Y%m%dT%H%M%SZ')`的结果保存到`ingest_batch_id`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    ingest_batch_id = (
        "task016a_"
        + generated_at.astimezone(timezone.utc).strftime(
            "%Y%m%dT%H%M%SZ"
        )
    )
    # 显式调用：执行`output_dir.mkdir(parents=True, exist_ok=True)`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
    # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
    # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
    output_dir.mkdir(parents=True, exist_ok=True)

    # 状态计算：把`discover_snapshot_directories(root)`的结果保存到`date_dirs`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    date_dirs = discover_snapshot_directories(root)
    # 状态计算：把`[]`的结果保存到`file_results`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    file_results: list[dict[str, Any]] = []
    # 状态计算：把`[]`的结果保存到`anomaly_rows`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    anomaly_rows: list[dict[str, Any]] = []
    # 状态计算：把`[]`的结果保存到`coverage_rows`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    coverage_rows: list[dict[str, Any]] = []
    # 状态计算：把`{dataset_id: [] for dataset_id in contract.datasets}`的结果保存到`sample_payload`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    sample_payload: dict[str, list[dict[str, Any]]] = {
        dataset_id: [] for dataset_id in contract.datasets
    }
    # 状态计算：把`Counter()`的结果保存到`schema_usage`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    schema_usage: Counter[tuple[str, str]] = Counter()
    # 状态计算：把`{}`的结果保存到`parsed_by_date`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    parsed_by_date: dict[
        str, dict[str, ParsedSourceFile]
    ] = {}
    # 状态计算：把`{dataset_id: spec.family for dataset_id, spec in contract.datasets.items()}`的结果保存到`family_by_dataset`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    family_by_dataset = {
        dataset_id: spec.family
        for dataset_id, spec in contract.datasets.items()
    }

    # 循环处理：逐项遍历`date_dirs`，把当前元素绑定到`date_dir`。
    # - 数据变化：每轮只处理一个来源记录、字段、文件或证据项，并显式累计到局部集合或输出对象。
    # - 为什么这样写：逐项处理便于保留行级血缘、隔离单项异常，并控制16GB单机上的峰值内存。
    for date_dir in date_dirs:
        # 状态计算：把`{}`的结果保存到`date_results`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        date_results: dict[str, ParsedSourceFile] = {}
        # 循环处理：逐项遍历`contract.datasets.items()`，把当前元素绑定到`(dataset_id, dataset)`。
        # - 数据变化：每轮只处理一个来源记录、字段、文件或证据项，并显式累计到局部集合或输出对象。
        # - 为什么这样写：逐项处理便于保留行级血缘、隔离单项异常，并控制16GB单机上的峰值内存。
        for dataset_id, dataset in contract.datasets.items():
            # 状态计算：把`date_dir / dataset.file_name`的结果保存到`file_path`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            file_path = date_dir / dataset.file_name
            # 条件门禁：判断`not file_path.exists()`，条件成立时进入对应的数据、安全或异常处理分支。
            # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
            # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
            if not file_path.exists():
                # 显式调用：执行`anomaly_rows.append({'severity': 'WARNING', 'snapshot_date': date_dir.name, 'dataset_id': dataset_id, 'type': 'MISSING_FILE', 'detail': dat…`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
                # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
                # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
                anomaly_rows.append(
                    {
                        "severity": "WARNING",
                        "snapshot_date": date_dir.name,
                        "dataset_id": dataset_id,
                        "type": "MISSING_FILE",
                        "detail": dataset.file_name,
                    }
                )
                # 控制流：跳过本轮剩余步骤，使循环或占位分支按既定合同继续。
                # - 数据变化：本语句不直接改变业务记录，只调整当前执行路径。
                # - 为什么这样写：显式控制流比隐式嵌套更容易检查边界和异常处理。
                continue

            # 异常边界：尝试执行可能失败的解析、查询、文件或类型转换步骤，并由后续处理保留错误证据。
            # - 数据变化：正常路径产生业务结果；异常路径不得静默伪造数据，应抛出、记录或隔离。
            # - 为什么这样写：把外部环境故障与业务合同失败分开，便于重试、回滚和准确验收。
            try:
                # 状态计算：把`parse_source_file(file_path, dataset=dataset, contract=contract, ingest_batch_id=ingest_batch_id, i…`的结果保存到`result`，供当前逻辑后续校验、转换、累计或返回。
                # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
                # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
                result = parse_source_file(
                    file_path,
                    dataset=dataset,
                    contract=contract,
                    ingest_batch_id=ingest_batch_id,
                    ingested_at=generated_at,
                )
            except Exception as exc:  # noqa: BLE001
                # 显式调用：执行`anomaly_rows.append({'severity': 'ERROR', 'snapshot_date': date_dir.name, 'dataset_id': dataset_id, 'type': 'FILE_READ_FAILED', 'detail': f…`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
                # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
                # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
                anomaly_rows.append(
                    {
                        "severity": "ERROR",
                        "snapshot_date": date_dir.name,
                        "dataset_id": dataset_id,
                        "type": "FILE_READ_FAILED",
                        "detail": (
                            f"{type(exc).__name__}: {exc}"
                        ),
                    }
                )
                # 控制流：跳过本轮剩余步骤，使循环或占位分支按既定合同继续。
                # - 数据变化：本语句不直接改变业务记录，只调整当前执行路径。
                # - 为什么这样写：显式控制流比隐式嵌套更容易检查边界和异常处理。
                continue

            # 状态计算：把`result`的结果保存到`date_results[dataset_id]`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            date_results[dataset_id] = result
            # 条件门禁：判断`result.schema_version is not None`，条件成立时进入对应的数据、安全或异常处理分支。
            # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
            # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
            if result.schema_version is not None:
                # 状态计算：把`1`的结果保存到`schema_usage[dataset_id, result.schema_version]`，供当前逻辑后续校验、转换、累计或返回。
                # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
                # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
                schema_usage[
                    (dataset_id, result.schema_version)
                ] += 1
            # 显式调用：执行`sample_payload[dataset_id].extend(list(result.normalized_samples))`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
            # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
            # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
            sample_payload[dataset_id].extend(
                list(result.normalized_samples)
            )
            # 状态计算：把`sample_payload[dataset_id][:3]`的结果保存到`sample_payload[dataset_id]`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            sample_payload[dataset_id] = sample_payload[
                dataset_id
            ][:3]

            # 状态计算：把`'BLOCKED' if result.has_blocking_parse_error else 'READY'`的结果保存到`initial_status`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            initial_status = (
                "BLOCKED"
                if result.has_blocking_parse_error
                else "READY"
            )
            # 显式调用：执行`file_results.append(_file_result_row(result, family=dataset.family, status=initial_status))`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
            # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
            # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
            file_results.append(
                _file_result_row(
                    result,
                    family=dataset.family,
                    status=initial_status,
                )
            )
            # 状态计算：把`{'UNKNOWN_SCHEMA': f'header_sha256={result.exact_header_sha256}', 'MALFORMED_ROW': f'malformed_row_…`的结果保存到`anomaly_summaries`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            anomaly_summaries = {
                "UNKNOWN_SCHEMA": (
                    f"header_sha256={result.exact_header_sha256}"
                ),
                "MALFORMED_ROW": (
                    f"malformed_row_count="
                    f"{result.malformed_row_count}"
                ),
                "DUPLICATE_ENTITY_KEY": (
                    f"duplicate_key_count="
                    f"{result.duplicate_key_count}"
                ),
                "ROW_NORMALIZATION_FAILED": (
                    f"normalization_error_count="
                    f"{result.normalization_error_count}"
                ),
            }
            # 循环处理：逐项遍历`result.anomaly_codes`，把当前元素绑定到`code`。
            # - 数据变化：每轮只处理一个来源记录、字段、文件或证据项，并显式累计到局部集合或输出对象。
            # - 为什么这样写：逐项处理便于保留行级血缘、隔离单项异常，并控制16GB单机上的峰值内存。
            for code in result.anomaly_codes:
                # 显式调用：执行`anomaly_rows.append({'severity': 'ERROR', 'snapshot_date': date_dir.name, 'dataset_id': dataset_id, 'type': code, 'detail': anomaly_summari…`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
                # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
                # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
                anomaly_rows.append(
                    {
                        "severity": "ERROR",
                        "snapshot_date": date_dir.name,
                        "dataset_id": dataset_id,
                        "type": code,
                        "detail": anomaly_summaries.get(
                            code,
                            "|".join(result.anomaly_details),
                        ),
                    }
                )
        # 状态计算：把`date_results`的结果保存到`parsed_by_date[date_dir.name]`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        parsed_by_date[date_dir.name] = date_results

    # 覆盖门禁在全部文件解析后执行。
    # 状态计算：把`{}`的结果保存到`quarantine_keys`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    quarantine_keys: dict[tuple[str, str], str] = {}
    # 循环处理：逐项遍历`parsed_by_date.items()`，把当前元素绑定到`(date_name, date_results)`。
    # - 数据变化：每轮只处理一个来源记录、字段、文件或证据项，并显式累计到局部集合或输出对象。
    # - 为什么这样写：逐项处理便于保留行级血缘、隔离单项异常，并控制16GB单机上的峰值内存。
    for date_name, date_results in parsed_by_date.items():
        # 循环处理：逐项遍历`contract.coverage_gates.items()`，把当前元素绑定到`(child_id, gate)`。
        # - 数据变化：每轮只处理一个来源记录、字段、文件或证据项，并显式累计到局部集合或输出对象。
        # - 为什么这样写：逐项处理便于保留行级血缘、隔离单项异常，并控制16GB单机上的峰值内存。
        for child_id, gate in contract.coverage_gates.items():
            # 状态计算：把`str(gate.get('reference_dataset_id'))`的结果保存到`reference_id`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            reference_id = str(
                gate.get("reference_dataset_id")
            )
            # 状态计算：把`date_results.get(child_id)`的结果保存到`child`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            child = date_results.get(child_id)
            # 状态计算：把`date_results.get(reference_id)`的结果保存到`reference`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            reference = date_results.get(reference_id)
            # 条件门禁：判断`child is None or reference is None`，条件成立时进入对应的数据、安全或异常处理分支。
            # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
            # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
            if child is None or reference is None:
                # 控制流：跳过本轮剩余步骤，使循环或占位分支按既定合同继续。
                # - 数据变化：本语句不直接改变业务记录，只调整当前执行路径。
                # - 为什么这样写：显式控制流比隐式嵌套更容易检查边界和异常处理。
                continue
            # 条件门禁：判断`child.has_blocking_parse_error or reference.has_blocking_parse_error`，条件成立时进入对应的数据、安全或异常处理分支。
            # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
            # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
            if (
                child.has_blocking_parse_error
                or reference.has_blocking_parse_error
            ):
                # 控制流：跳过本轮剩余步骤，使循环或占位分支按既定合同继续。
                # - 数据变化：本语句不直接改变业务记录，只调整当前执行路径。
                # - 为什么这样写：显式控制流比隐式嵌套更容易检查边界和异常处理。
                continue

            # 状态计算：把`child.entity_keys & reference.entity_keys`的结果保存到`intersection`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            intersection = (
                child.entity_keys & reference.entity_keys
            )
            # 状态计算：把`child.entity_keys - reference.entity_keys`的结果保存到`child_only`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            child_only = child.entity_keys - reference.entity_keys
            # 状态计算：把`reference.entity_keys - child.entity_keys`的结果保存到`reference_only`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            reference_only = (
                reference.entity_keys - child.entity_keys
            )
            # 状态计算：把`len(intersection) / len(reference.entity_keys) if reference.entity_keys else 0.0`的结果保存到`ratio`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            ratio = (
                len(intersection) / len(reference.entity_keys)
                if reference.entity_keys
                else 0.0
            )
            # 状态计算：把`float(gate.get('minimum_intersection_ratio', 0.95))`的结果保存到`threshold`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            threshold = float(
                gate.get("minimum_intersection_ratio", 0.95)
            )
            # 状态计算：把`'PASSED' if ratio >= threshold else 'FAILED'`的结果保存到`status`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            status = "PASSED" if ratio >= threshold else "FAILED"
            # 显式调用：执行`coverage_rows.append({'snapshot_date': date_name, 'dataset_id': child_id, 'reference_dataset_id': reference_id, 'intersection_count': len(i…`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
            # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
            # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
            coverage_rows.append(
                {
                    "snapshot_date": date_name,
                    "dataset_id": child_id,
                    "reference_dataset_id": reference_id,
                    "intersection_count": len(intersection),
                    "child_only_count": len(child_only),
                    "reference_only_count": len(reference_only),
                    "coverage_ratio": round(ratio, 12),
                    "minimum_ratio": threshold,
                    "status": status,
                }
            )
            # 条件门禁：判断`status == 'FAILED'`，条件成立时进入对应的数据、安全或异常处理分支。
            # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
            # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
            if status == "FAILED":
                # 状态计算：把`f'UNIVERSE_COVERAGE_INCOMPLETE:{ratio:.6f}<{threshold:.6f}'`的结果保存到`reason`，供当前逻辑后续校验、转换、累计或返回。
                # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
                # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
                reason = (
                    "UNIVERSE_COVERAGE_INCOMPLETE:"
                    f"{ratio:.6f}<{threshold:.6f}"
                )
                # 状态计算：把`reason`的结果保存到`quarantine_keys[date_name, child_id]`，供当前逻辑后续校验、转换、累计或返回。
                # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
                # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
                quarantine_keys[(date_name, child_id)] = reason
                # 显式调用：执行`anomaly_rows.append({'severity': 'ERROR', 'snapshot_date': date_name, 'dataset_id': child_id, 'type': 'UNIVERSE_COVERAGE_INCOMPLETE', 'deta…`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
                # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
                # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
                anomaly_rows.append(
                    {
                        "severity": "ERROR",
                        "snapshot_date": date_name,
                        "dataset_id": child_id,
                        "type": "UNIVERSE_COVERAGE_INCOMPLETE",
                        "detail": stable_json(
                            {
                                "reference_dataset_id": reference_id,
                                "intersection_count": len(
                                    intersection
                                ),
                                "child_only_count": len(child_only),
                                "reference_only_count": len(
                                    reference_only
                                ),
                                "coverage_ratio": ratio,
                                "minimum_ratio": threshold,
                                "action": gate.get(
                                    "failure_action",
                                    "QUARANTINE_FILE",
                                ),
                            }
                        ),
                    }
                )

    # 循环处理：逐项遍历`file_results`，把当前元素绑定到`row`。
    # - 数据变化：每轮只处理一个来源记录、字段、文件或证据项，并显式累计到局部集合或输出对象。
    # - 为什么这样写：逐项处理便于保留行级血缘、隔离单项异常，并控制16GB单机上的峰值内存。
    for row in file_results:
        # 状态计算：把`(row['snapshot_date'], row['dataset_id'])`的结果保存到`key`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        key = (row["snapshot_date"], row["dataset_id"])
        # 条件门禁：判断`key in quarantine_keys and row['status'] == 'READY'`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if key in quarantine_keys and row["status"] == "READY":
            # 状态计算：把`'QUARANTINED'`的结果保存到`row['status']`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            row["status"] = "QUARANTINED"
            # 状态计算：把`quarantine_keys[key]`的结果保存到`row['quarantine_reason']`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            row["quarantine_reason"] = quarantine_keys[key]

    # 状态计算：把`[row for row in file_results if row['status'] == 'BLOCKED']`的结果保存到`blocking_files`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    blocking_files = [
        row for row in file_results if row["status"] == "BLOCKED"
    ]
    # 状态计算：把`[row for row in file_results if row['status'] == 'QUARANTINED']`的结果保存到`quarantined_files`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    quarantined_files = [
        row
        for row in file_results
        if row["status"] == "QUARANTINED"
    ]
    # 状态计算：把`[row for row in file_results if row['status'] == 'READY']`的结果保存到`importable_files`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    importable_files = [
        row for row in file_results if row["status"] == "READY"
    ]

    # 状态计算：把`{}`的结果保存到`dataset_counts`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    dataset_counts: dict[str, dict[str, int]] = {}
    # 循环处理：逐项遍历`contract.datasets`，把当前元素绑定到`dataset_id`。
    # - 数据变化：每轮只处理一个来源记录、字段、文件或证据项，并显式累计到局部集合或输出对象。
    # - 为什么这样写：逐项处理便于保留行级血缘、隔离单项异常，并控制16GB单机上的峰值内存。
    for dataset_id in contract.datasets:
        # 状态计算：把`[row for row in file_results if row['dataset_id'] == dataset_id]`的结果保存到`rows`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        rows = [
            row
            for row in file_results
            if row["dataset_id"] == dataset_id
        ]
        # 状态计算：把`{'profiled_file_count': len(rows), 'ready_file_count': sum((row['status'] == 'READY' for row in row…`的结果保存到`dataset_counts[dataset_id]`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        dataset_counts[dataset_id] = {
            "profiled_file_count": len(rows),
            "ready_file_count": sum(
                row["status"] == "READY" for row in rows
            ),
            "quarantined_file_count": sum(
                row["status"] == "QUARANTINED" for row in rows
            ),
            "blocked_file_count": sum(
                row["status"] == "BLOCKED" for row in rows
            ),
            "parsed_row_count": sum(
                int(row["row_count"]) for row in rows
            ),
            "planned_insert_row_count": sum(
                int(row["row_count"])
                for row in rows
                if row["status"] == "READY"
            ),
        }

    # 状态计算：把`Counter()`的结果保存到`family_insert_counts`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    family_insert_counts: Counter[str] = Counter()
    # 循环处理：逐项遍历`importable_files`，把当前元素绑定到`row`。
    # - 数据变化：每轮只处理一个来源记录、字段、文件或证据项，并显式累计到局部集合或输出对象。
    # - 为什么这样写：逐项处理便于保留行级血缘、隔离单项异常，并控制16GB单机上的峰值内存。
    for row in importable_files:
        # 状态计算：把`int(row['row_count'])`的结果保存到`family_insert_counts[str(row['family'])]`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        family_insert_counts[str(row["family"])] += int(
            row["row_count"]
        )

    # 状态计算：把`sum((item['type'] == 'MISSING_FILE' for item in anomaly_rows))`的结果保存到`missing_count`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    missing_count = sum(
        item["type"] == "MISSING_FILE"
        for item in anomaly_rows
    )
    # 状态计算：把`sum((item['type'] == 'UNKNOWN_SCHEMA' for item in anomaly_rows))`的结果保存到`unknown_schema_count`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    unknown_schema_count = sum(
        item["type"] == "UNKNOWN_SCHEMA"
        for item in anomaly_rows
    )
    # 状态计算：把`sum((item['type'] in {'FILE_READ_FAILED', 'UNKNOWN_SCHEMA', 'MALFORMED_ROW', 'DUPLICATE_ENTITY_KEY'…`的结果保存到`parser_error_count`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    parser_error_count = sum(
        item["type"]
        in {
            "FILE_READ_FAILED",
            "UNKNOWN_SCHEMA",
            "MALFORMED_ROW",
            "DUPLICATE_ENTITY_KEY",
            "ROW_NORMALIZATION_FAILED",
        }
        for item in anomaly_rows
    )

    # 条件门禁：判断`blocking_files or parser_error_count`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if blocking_files or parser_error_count:
        # 状态计算：把`'BLOCKED'`的结果保存到`overall_status`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        overall_status = "BLOCKED"
    # 条件门禁：判断`quarantined_files`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    elif quarantined_files:
        # 状态计算：把`'READY_WITH_QUARANTINE'`的结果保存到`overall_status`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        overall_status = "READY_WITH_QUARANTINE"
    else:
        # 状态计算：把`'READY'`的结果保存到`overall_status`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        overall_status = "READY"

    # 状态计算：把`[{'dataset_id': dataset_id, 'schema_version': schema_version, 'file_count': file_count} for (datase…`的结果保存到`schema_usage_rows`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    schema_usage_rows = [
        {
            "dataset_id": dataset_id,
            "schema_version": schema_version,
            "file_count": file_count,
        }
        for (
            dataset_id,
            schema_version,
        ), file_count in sorted(schema_usage.items())
    ]

    # 状态计算：把`{'task_id': 'TASK_016A', 'generated_at': generated_at.isoformat(), 'ingest_batch_id': ingest_batch_…`的结果保存到`summary`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    summary = {
        "task_id": "TASK_016A",
        "generated_at": generated_at.isoformat(),
        "ingest_batch_id": ingest_batch_id,
        "scan_root": str(root),
        "contract_path": str(contract_path),
        "contract_version": contract.contract_version,
        "overall_status": overall_status,
        "snapshot_directory_count": len(date_dirs),
        "profiled_file_count": len(file_results),
        "ready_file_count": len(importable_files),
        "quarantined_file_count": len(quarantined_files),
        "blocked_file_count": len(blocking_files),
        "missing_file_warning_count": missing_count,
        "unknown_schema_count": unknown_schema_count,
        "parsed_row_count": sum(
            int(row["row_count"]) for row in file_results
        ),
        "planned_insert_row_count": sum(
            int(row["row_count"]) for row in importable_files
        ),
        "quarantined_row_count": sum(
            int(row["row_count"])
            for row in quarantined_files
        ),
        "dataset_counts": dataset_counts,
        "physical_table_write_plan": {
            contract.database_plan.get(
                "physical_tables", {}
            ).get(
                family, family
            ): count
            for family, count in sorted(
                family_insert_counts.items()
            )
        },
        "database_plan": contract.database_plan,
        "safety_decisions": [
            "TASK_016A不连接或修改DolphinDB。",
            "未知Schema、畸形行、重复实体键和标准化错误会阻断。",
            "覆盖率不足的文件进入隔离，不写入主Raw表。",
            "缺失文件只登记WARNING，不伪造记录。",
            "source_file_mtime仅保留为证据，不等同available_at。",
            "资金流流出字段保持来源负号，不再次取负。",
            "分类名称只作为source node_name_raw，不伪造稳定node_id。",
        ],
        "next_gate": (
            "TASK_016B_CREATE_TABLES_AND_IMPORT"
            if overall_status == "READY_WITH_QUARANTINE"
            else "RESOLVE_PREFLIGHT_BLOCKERS"
        ),
    }

    # 状态计算：把`['snapshot_date', 'dataset_id', 'family', 'file_name', 'file_size_bytes', 'source_file_sha256', 'sc…`的结果保存到`file_fields`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    file_fields = [
        "snapshot_date",
        "dataset_id",
        "family",
        "file_name",
        "file_size_bytes",
        "source_file_sha256",
        "schema_version",
        "exact_header_sha256",
        "row_count",
        "unique_key_count",
        "duplicate_key_count",
        "malformed_row_count",
        "missing_cell_count",
        "normalization_error_count",
        "status",
        "quarantine_reason",
        "anomaly_codes",
        "anomaly_details",
    ]
    # 状态计算：把`['severity', 'snapshot_date', 'dataset_id', 'type', 'detail']`的结果保存到`anomaly_fields`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    anomaly_fields = [
        "severity",
        "snapshot_date",
        "dataset_id",
        "type",
        "detail",
    ]
    # 状态计算：把`['snapshot_date', 'dataset_id', 'reference_dataset_id', 'intersection_count', 'child_only_count', '…`的结果保存到`coverage_fields`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    coverage_fields = [
        "snapshot_date",
        "dataset_id",
        "reference_dataset_id",
        "intersection_count",
        "child_only_count",
        "reference_only_count",
        "coverage_ratio",
        "minimum_ratio",
        "status",
    ]

    # 显式调用：执行`_write_csv(output_dir / 'task_016a_file_results.csv', file_results, file_fields)`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
    # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
    # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
    _write_csv(
        output_dir / "task_016a_file_results.csv",
        file_results,
        file_fields,
    )
    # 显式调用：执行`_write_csv(output_dir / 'task_016a_anomalies.csv', anomaly_rows, anomaly_fields)`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
    # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
    # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
    _write_csv(
        output_dir / "task_016a_anomalies.csv",
        anomaly_rows,
        anomaly_fields,
    )
    # 显式调用：执行`_write_csv(output_dir / 'task_016a_coverage_checks.csv', coverage_rows, coverage_fields)`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
    # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
    # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
    _write_csv(
        output_dir / "task_016a_coverage_checks.csv",
        coverage_rows,
        coverage_fields,
    )
    # 显式调用：执行`_write_csv(output_dir / 'task_016a_schema_usage.csv', schema_usage_rows, ['dataset_id', 'schema_version', 'file_count'])`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
    # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
    # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
    _write_csv(
        output_dir / "task_016a_schema_usage.csv",
        schema_usage_rows,
        ["dataset_id", "schema_version", "file_count"],
    )

    # 显式调用：执行`(output_dir / 'task_016a_normalized_samples.json').write_text(json.dumps(_json_safe(sample_payload), ensure_ascii=False, indent=2), encodin…`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
    # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
    # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
    (
        output_dir / "task_016a_normalized_samples.json"
    ).write_text(
        json.dumps(
            _json_safe(sample_payload),
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    # 状态计算：把`output_dir / 'task_016a_preflight_summary.json'`的结果保存到`summary_path`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    summary_path = (
        output_dir / "task_016a_preflight_summary.json"
    )
    # 显式调用：执行`summary_path.write_text(json.dumps(_json_safe(summary), ensure_ascii=False, indent=2), encoding='utf-8')`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
    # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
    # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
    summary_path.write_text(
        json.dumps(
            _json_safe(summary),
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    # 状态计算：把`_build_preflight_markdown(summary)`的结果保存到`markdown`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    markdown = _build_preflight_markdown(summary)
    # 显式调用：执行`(output_dir / 'task_016a_preflight_summary.md').write_text(markdown, encoding='utf-8')`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
    # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
    # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
    (
        output_dir / "task_016a_preflight_summary.md"
    ).write_text(markdown, encoding="utf-8")

    # 结果返回：把`summary`交给调用方并结束当前函数。
    # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return summary


# 函数_build_preflight_markdown：构建人类可读预导入报告。
# - 输入：summary:dict[str, Any]；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型str；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
# - 为什么这样写：把对象构造、字段映射或标准化转换步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def _build_preflight_markdown(
    summary: dict[str, Any],
) -> str:
    """构建人类可读预导入报告。"""
    # 状态计算：把`[]`的结果保存到`dataset_lines`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    dataset_lines = []
    # 循环处理：逐项遍历`summary['dataset_counts'].items()`，把当前元素绑定到`(dataset_id, counts)`。
    # - 数据变化：每轮只处理一个来源记录、字段、文件或证据项，并显式累计到局部集合或输出对象。
    # - 为什么这样写：逐项处理便于保留行级血缘、隔离单项异常，并控制16GB单机上的峰值内存。
    for dataset_id, counts in summary["dataset_counts"].items():
        # 显式调用：执行`dataset_lines.append('| {dataset} | {files} | {ready} | {quarantine} | {blocked} | {rows} | {planned} |'.format(dataset=dataset_id, files=c…`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
        # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
        # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
        dataset_lines.append(
            "| {dataset} | {files} | {ready} | {quarantine} | "
            "{blocked} | {rows} | {planned} |".format(
                dataset=dataset_id,
                files=counts["profiled_file_count"],
                ready=counts["ready_file_count"],
                quarantine=counts[
                    "quarantined_file_count"
                ],
                blocked=counts["blocked_file_count"],
                rows=counts["parsed_row_count"],
                planned=counts[
                    "planned_insert_row_count"
                ],
            )
        )

    # 状态计算：把`[f'| {table_name} | {row_count} |' for table_name, row_count in summary['physical_table_write_plan'…`的结果保存到`table_lines`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    table_lines = [
        f"| {table_name} | {row_count} |"
        for table_name, row_count in summary[
            "physical_table_write_plan"
        ].items()
    ]

    # 结果返回：把`f"# TASK_016A 日线资金预导入报告\n\n总体状态：**{summary['overall_status']}**\n\n## 一、扫描结果\n\n- 快照目录：{summary['snapshot_directory_cou…`交给调用方并结束当前函数。
    # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return f"""# TASK_016A 日线资金预导入报告

总体状态：**{summary['overall_status']}**

## 一、扫描结果

- 快照目录：{summary['snapshot_directory_count']}
- 已画像文件：{summary['profiled_file_count']}
- 可写入文件：{summary['ready_file_count']}
- 隔离文件：{summary['quarantined_file_count']}
- 阻断文件：{summary['blocked_file_count']}
- 缺失文件警告：{summary['missing_file_warning_count']}
- 已解析行：{summary['parsed_row_count']}
- 计划写入行：{summary['planned_insert_row_count']}
- 隔离行：{summary['quarantined_row_count']}

## 二、七类数据

| 数据集 | 文件 | Ready | Quarantine | Blocked | 解析行 | 计划写入 |
|---|---:|---:|---:|---:|---:|---:|
{chr(10).join(dataset_lines)}

## 三、物理表写入计划

| 物理表 | 计划行数 |
|---|---:|
{chr(10).join(table_lines)}

## 四、安全边界

{chr(10).join(f"- {item}" for item in summary['safety_decisions'])}

## 五、下一门禁

`{summary['next_gate']}`

TASK_016A没有连接或修改DolphinDB。
"""


# 状态计算：把`['DailyFundsContract', 'DailyFundsIngestError', 'DatasetSpec', 'KnownSchema', 'ParsedSourceFile', '…`的结果保存到`__all__`，供当前逻辑后续校验、转换、累计或返回。
# - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
# - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
__all__ = [
    "DailyFundsContract",
    "DailyFundsIngestError",
    "DatasetSpec",
    "KnownSchema",
    "ParsedSourceFile",
    "deduplicate_headers",
    "discover_snapshot_directories",
    "header_fingerprint",
    "infer_market_candidate",
    "load_daily_funds_contract",
    "normalize_instrument_code",
    "normalize_row",
    "parse_breadth_counts",
    "parse_breadth_ratio",
    "parse_snapshot_date_from_path",
    "parse_source_file",
    "parse_source_int",
    "parse_source_number",
    "run_daily_funds_preflight",
    "validate_daily_funds_contract",
]
