# 模块总览：从七类DolphinDB Raw表只读查询数据，并转换为统一Canonical快照对象。
# - 输入输出：输入为数据集、证券或分类实体、日期和行数限制；输出为标准记录、来源扩展和血缘。
# - 数据与安全：服务必须保留竞价日期精度、资金流符号和未确认字段，不能伪造时间或单位。
# - 运行边界：导入模块和阅读注释不会触发数据库写入；只有显式调用对应函数并满足门禁时才执行I/O。
# - 为什么这样写：先声明职责、单位、时点和副作用边界，读者可以在阅读实现前建立正确的金融与工程语境。
"""七类日线资金DolphinDB只读Canonical标准化服务。

本模块只读取TASK_016创建的三张Raw表，根据TASK_017B批准的映射合同
输出Canonical记录、来源扩展、质量标记和字段级血缘。

安全边界：
1. 只通过run_readonly_query执行select查询；
2. 不创建、修改、删除或回写DolphinDB对象；
3. 不读取桌面Excel和导入目录；
4. 不把文件修改时间或入库时间伪装为市场快照时间；
5. 分类节点使用generic entity_ids，不伪装成instrument_ids；
6. 同一Canonical主键存在多个Raw修订时保留最新ingested_at版本。
"""

# 依赖导入：加载`from __future__ import annotations`所提供的类型、标准库或项目内能力。
# - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
# - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
from __future__ import annotations

# 依赖导入：加载`import copy`所提供的类型、标准库或项目内能力。
# - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
# - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
import copy
# 依赖导入：加载`import hashlib`所提供的类型、标准库或项目内能力。
# - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
# - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
import hashlib
# 依赖导入：加载`import math`所提供的类型、标准库或项目内能力。
# - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
# - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
import math
# 依赖导入：加载`import re`所提供的类型、标准库或项目内能力。
# - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
# - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
import re
# 依赖导入：加载`import unicodedata`所提供的类型、标准库或项目内能力。
# - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
# - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
import unicodedata
# 依赖导入：加载`from collections import Counter, defaultdict`所提供的类型、标准库或项目内能力。
# - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
# - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
from collections import Counter, defaultdict
# 依赖导入：加载`from dataclasses import dataclass, field`所提供的类型、标准库或项目内能力。
# - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
# - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
from dataclasses import dataclass, field
# 依赖导入：加载`from functools import lru_cache`所提供的类型、标准库或项目内能力。
# - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
# - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
from functools import lru_cache
# 依赖导入：加载`from datetime import date, datetime, timezone`所提供的类型、标准库或项目内能力。
# - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
# - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
from datetime import date, datetime, timezone
# 依赖导入：加载`from pathlib import Path`所提供的类型、标准库或项目内能力。
# - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
# - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
from pathlib import Path
# 依赖导入：加载`from typing import Any, Mapping, Protocol, Sequence`所提供的类型、标准库或项目内能力。
# - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
# - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
from typing import Any, Mapping, Protocol, Sequence

# 依赖导入：加载`import yaml`所提供的类型、标准库或项目内能力。
# - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
# - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
import yaml

# 依赖导入：加载`from .data_contracts import DataContractError`所提供的类型、标准库或项目内能力。
# - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
# - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
from .data_contracts import DataContractError
# 依赖导入：加载`from .daily_funds_canonical_contract import REQUIRED_DATASETS, load_contract, validate_contract`所提供的类型、标准库或项目内能力。
# - 数据变化：导入只绑定名称，不在本行主动连接DolphinDB、读取来源文件或修改业务数据。
# - 为什么这样写：显式依赖使只读边界、可替换组件和测试注入点保持清晰。
from .daily_funds_canonical_contract import (
    REQUIRED_DATASETS,
    load_contract,
    validate_contract,
)


# 关键常量SERVICE_CONFIG_RELATIVE_PATH：集中保存`'configs/datasets/a_stock_daily_funds_standard_service.yaml'`对应的合同值、Schema集合或运行边界。
# - 来源与范围：该值来自当前项目任务、配置、真实数据画像或安全合同；未明确说明时不得外推为行业统一标准。
# - 单位与实例：数值单位由变量名、相邻校验和调用语义共同限定；字符串用于版本、字段、状态或DolphinDB对象标识。
# - 为什么这样写：集中命名固定参数可避免魔法值散落，并让升级、审计和回归测试有稳定锚点。
SERVICE_CONFIG_RELATIVE_PATH = (
    "configs/datasets/a_stock_daily_funds_standard_service.yaml"
)
# 关键常量MAPPING_CONTRACT_RELATIVE_PATH：集中保存`'configs/mappings/a_stock_daily_funds_canonical_v0.yaml'`对应的合同值、Schema集合或运行边界。
# - 来源与范围：该值来自当前项目任务、配置、真实数据画像或安全合同；未明确说明时不得外推为行业统一标准。
# - 单位与实例：数值单位由变量名、相邻校验和调用语义共同限定；字符串用于版本、字段、状态或DolphinDB对象标识。
# - 为什么这样写：集中命名固定参数可避免魔法值散落，并让升级、审计和回归测试有稳定锚点。
MAPPING_CONTRACT_RELATIVE_PATH = (
    "configs/mappings/a_stock_daily_funds_canonical_v0.yaml"
)
# 关键常量DICTIONARY_RELATIVE_PATH：集中保存`'schemas/canonical_fields.yaml'`对应的合同值、Schema集合或运行边界。
# - 来源与范围：该值来自当前项目任务、配置、真实数据画像或安全合同；未明确说明时不得外推为行业统一标准。
# - 单位与实例：数值单位由变量名、相邻校验和调用语义共同限定；字符串用于版本、字段、状态或DolphinDB对象标识。
# - 为什么这样写：集中命名固定参数可避免魔法值散落，并让升级、审计和回归测试有稳定锚点。
DICTIONARY_RELATIVE_PATH = "schemas/canonical_fields.yaml"
# 关键常量ENUM_DEFINITIONS_RELATIVE_PATH：集中保存`'schemas/enum_definitions.yaml'`对应的合同值、Schema集合或运行边界。
# - 来源与范围：该值来自当前项目任务、配置、真实数据画像或安全合同；未明确说明时不得外推为行业统一标准。
# - 单位与实例：数值单位由变量名、相邻校验和调用语义共同限定；字符串用于版本、字段、状态或DolphinDB对象标识。
# - 为什么这样写：集中命名固定参数可避免魔法值散落，并让升级、审计和回归测试有稳定锚点。
ENUM_DEFINITIONS_RELATIVE_PATH = "schemas/enum_definitions.yaml"

# 关键常量_DATABASE_URI_PATTERN：集中保存`re.compile('^dfs://[A-Za-z0-9_.-]+$')`对应的合同值、Schema集合或运行边界。
# - 来源与范围：该值来自当前项目任务、配置、真实数据画像或安全合同；未明确说明时不得外推为行业统一标准。
# - 单位与实例：数值单位由变量名、相邻校验和调用语义共同限定；字符串用于版本、字段、状态或DolphinDB对象标识。
# - 为什么这样写：集中命名固定参数可避免魔法值散落，并让升级、审计和回归测试有稳定锚点。
_DATABASE_URI_PATTERN = re.compile(r"^dfs://[A-Za-z0-9_.-]+$")
# 关键常量_IDENTIFIER_PATTERN：集中保存`re.compile('^[A-Za-z_][A-Za-z0-9_]*$')`对应的合同值、Schema集合或运行边界。
# - 来源与范围：该值来自当前项目任务、配置、真实数据画像或安全合同；未明确说明时不得外推为行业统一标准。
# - 单位与实例：数值单位由变量名、相邻校验和调用语义共同限定；字符串用于版本、字段、状态或DolphinDB对象标识。
# - 为什么这样写：集中命名固定参数可避免魔法值散落，并让升级、审计和回归测试有稳定锚点。
_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
# 关键常量_DATASET_ID_PATTERN：集中保存`re.compile('^[a-z][a-z0-9_]*$')`对应的合同值、Schema集合或运行边界。
# - 来源与范围：该值来自当前项目任务、配置、真实数据画像或安全合同；未明确说明时不得外推为行业统一标准。
# - 单位与实例：数值单位由变量名、相邻校验和调用语义共同限定；字符串用于版本、字段、状态或DolphinDB对象标识。
# - 为什么这样写：集中命名固定参数可避免魔法值散落，并让升级、审计和回归测试有稳定锚点。
_DATASET_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")
# 关键常量_INSTRUMENT_ID_PATTERN：集中保存`re.compile('^[0-9]{6}$')`对应的合同值、Schema集合或运行边界。
# - 来源与范围：该值来自当前项目任务、配置、真实数据画像或安全合同；未明确说明时不得外推为行业统一标准。
# - 单位与实例：数值单位由变量名、相邻校验和调用语义共同限定；字符串用于版本、字段、状态或DolphinDB对象标识。
# - 为什么这样写：集中命名固定参数可避免魔法值散落，并让升级、审计和回归测试有稳定锚点。
_INSTRUMENT_ID_PATTERN = re.compile(r"^[0-9]{6}$")
# 关键常量_PROVISIONAL_NODE_ID_PATTERN：集中保存`re.compile('^SOURCE_VENDOR:(INDUSTRY|CONCEPT):[A-F0-9]{20}$')`对应的合同值、Schema集合或运行边界。
# - 来源与范围：该值来自当前项目任务、配置、真实数据画像或安全合同；未明确说明时不得外推为行业统一标准。
# - 单位与实例：数值单位由变量名、相邻校验和调用语义共同限定；字符串用于版本、字段、状态或DolphinDB对象标识。
# - 为什么这样写：集中命名固定参数可避免魔法值散落，并让升级、审计和回归测试有稳定锚点。
_PROVISIONAL_NODE_ID_PATTERN = re.compile(
    r"^SOURCE_VENDOR:(INDUSTRY|CONCEPT):[A-F0-9]{20}$"
)

# 关键常量SUPPORTED_TRANSFORMS：集中保存`frozenset({'identity', 'percent_points_identity', 'multiply_100', 'divide_100', 'constant_OPENING_C…`对应的合同值、Schema集合或运行边界。
# - 来源与范围：该值来自当前项目任务、配置、真实数据画像或安全合同；未明确说明时不得外推为行业统一标准。
# - 单位与实例：数值单位由变量名、相邻校验和调用语义共同限定；字符串用于版本、字段、状态或DolphinDB对象标识。
# - 为什么这样写：集中命名固定参数可避免魔法值散落，并让升级、审计和回归测试有稳定锚点。
SUPPORTED_TRANSFORMS = frozenset(
    {
        "identity",
        "percent_points_identity",
        "multiply_100",
        "divide_100",
        "constant_OPENING_CALL",
        "constant_DATE_ONLY",
        "constant_SOURCE_VENDOR",
        "constant_VENDOR_ORDER_SIZE_BUCKET_V1",
        "normalized_enum",
        "provisional_hash_id",
        "sum_nullable",
        "unavailable",
        "unresolved_from_name_only",
        "no_safe_exact_value",
    }
)

# 关键常量COMMON_RAW_FIELDS：集中保存`frozenset({'dataset_id', 'snapshot_date', 'snapshot_month', 'snapshot_phase', 'schema_version', 'en…`对应的合同值、Schema集合或运行边界。
# - 来源与范围：该值来自当前项目任务、配置、真实数据画像或安全合同；未明确说明时不得外推为行业统一标准。
# - 单位与实例：数值单位由变量名、相邻校验和调用语义共同限定；字符串用于版本、字段、状态或DolphinDB对象标识。
# - 为什么这样写：集中命名固定参数可避免魔法值散落，并让升级、审计和回归测试有稳定锚点。
COMMON_RAW_FIELDS = frozenset(
    {
        "dataset_id",
        "snapshot_date",
        "snapshot_month",
        "snapshot_phase",
        "schema_version",
        "entity_key",
        "source_row_number",
        "source_file_name",
        "source_file_relative_path",
        "source_file_size_bytes",
        "source_file_mtime_utc",
        "source_file_sha256",
        "row_sha256",
        "ingest_batch_id",
        "ingested_at_utc",
        "quality_status",
        "raw_row_json",
    }
)
# 关键常量SECURITY_RAW_FIELDS：集中保存`COMMON_RAW_FIELDS | frozenset({'instrument_id', 'market_candidate', 'instrument_name', 'last_price'…`对应的合同值、Schema集合或运行边界。
# - 来源与范围：该值来自当前项目任务、配置、真实数据画像或安全合同；未明确说明时不得外推为行业统一标准。
# - 单位与实例：数值单位由变量名、相邻校验和调用语义共同限定；字符串用于版本、字段、状态或DolphinDB对象标识。
# - 为什么这样写：集中命名固定参数可避免魔法值散落，并让升级、审计和回归测试有稳定锚点。
SECURITY_RAW_FIELDS = COMMON_RAW_FIELDS | frozenset(
    {
        "instrument_id",
        "market_candidate",
        "instrument_name",
        "last_price",
        "pct_change",
        "price_change",
        "total_volume_lot",
        "current_volume_lot",
        "bid_price",
        "ask_price",
        "speed_pct",
        "turnover_pct",
        "amount_cny",
        "pe_dynamic",
        "industry_name",
        "high_price",
        "low_price",
        "open_price",
        "prev_close",
        "amplitude_pct",
        "volume_ratio",
        "order_imbalance_pct",
        "order_imbalance_lot",
        "avg_price",
        "inner_volume_lot",
        "outer_volume_lot",
        "inner_outer_ratio",
        "bid1_volume_lot",
        "ask1_volume_lot",
        "pb",
        "total_shares",
        "total_market_cap_cny",
        "float_shares",
        "float_market_cap_cny",
        "return_3d_pct",
        "return_6d_pct",
        "turnover_3d_pct",
        "turnover_6d_pct",
        "consecutive_up_days",
        "return_month_pct",
        "return_ytd_pct",
        "return_1m_pct",
        "return_1y_pct",
        "listing_date_raw",
        "speed_5m_pct",
        "return_20d_pct",
        "source_volume_unit",
        "canonical_volume_transform",
        "source_amount_unit",
    }
)
# 关键常量CLASSIFICATION_RAW_FIELDS：集中保存`COMMON_RAW_FIELDS | frozenset({'classification_type', 'node_name_raw', 'pct_change', 'return_3d_pct…`对应的合同值、Schema集合或运行边界。
# - 来源与范围：该值来自当前项目任务、配置、真实数据画像或安全合同；未明确说明时不得外推为行业统一标准。
# - 单位与实例：数值单位由变量名、相邻校验和调用语义共同限定；字符串用于版本、字段、状态或DolphinDB对象标识。
# - 为什么这样写：集中命名固定参数可避免魔法值散落，并让升级、审计和回归测试有稳定锚点。
CLASSIFICATION_RAW_FIELDS = COMMON_RAW_FIELDS | frozenset(
    {
        "classification_type",
        "node_name_raw",
        "pct_change",
        "return_3d_pct",
        "speed_pct",
        "leading_stock_name",
        "up_count",
        "down_count",
        "breadth_ratio",
        "breadth_status",
        "limit_up_count",
        "turnover_pct",
        "volume_ratio",
        "turnover_3d_pct",
        "return_5d_pct",
        "return_10d_pct",
        "return_20d_pct",
        "volume_lot",
        "amount_cny",
        "total_market_cap_cny",
        "float_market_cap_cny",
        "average_return_pct",
        "average_shares",
        "pe_ratio",
        "source_volume_unit",
        "canonical_volume_transform",
        "source_amount_unit",
    }
)
# 关键常量MONEY_FLOW_RAW_FIELDS：集中保存`COMMON_RAW_FIELDS | frozenset({'instrument_id', 'market_candidate', 'instrument_name', 'last_price'…`对应的合同值、Schema集合或运行边界。
# - 来源与范围：该值来自当前项目任务、配置、真实数据画像或安全合同；未明确说明时不得外推为行业统一标准。
# - 单位与实例：数值单位由变量名、相邻校验和调用语义共同限定；字符串用于版本、字段、状态或DolphinDB对象标识。
# - 为什么这样写：集中命名固定参数可避免魔法值散落，并让升级、审计和回归测试有稳定锚点。
MONEY_FLOW_RAW_FIELDS = COMMON_RAW_FIELDS | frozenset(
    {
        "instrument_id",
        "market_candidate",
        "instrument_name",
        "last_price",
        "pct_change",
        "main_net_inflow_cny",
        "auction_net_inflow_cny",
        "super_large_inflow_cny",
        "super_large_outflow_cny",
        "super_large_net_cny",
        "super_large_net_ratio_pct",
        "large_inflow_cny",
        "large_outflow_cny",
        "large_net_cny",
        "large_net_ratio_pct",
        "medium_inflow_cny",
        "medium_outflow_cny",
        "medium_net_cny",
        "medium_net_ratio_pct",
        "small_inflow_cny",
        "small_outflow_cny",
        "small_net_cny",
        "small_net_ratio_pct",
        "source_amount_unit",
        "outflow_sign_policy",
    }
)
# 关键常量RAW_FIELD_CATALOG：集中保存`{'security_snapshot': SECURITY_RAW_FIELDS, 'classification_snapshot': CLASSIFICATION_RAW_FIELDS, 'm…`对应的合同值、Schema集合或运行边界。
# - 来源与范围：该值来自当前项目任务、配置、真实数据画像或安全合同；未明确说明时不得外推为行业统一标准。
# - 单位与实例：数值单位由变量名、相邻校验和调用语义共同限定；字符串用于版本、字段、状态或DolphinDB对象标识。
# - 为什么这样写：集中命名固定参数可避免魔法值散落，并让升级、审计和回归测试有稳定锚点。
RAW_FIELD_CATALOG = {
    "security_snapshot": SECURITY_RAW_FIELDS,
    "classification_snapshot": CLASSIFICATION_RAW_FIELDS,
    "money_flow_snapshot": MONEY_FLOW_RAW_FIELDS,
}

# 关键常量SOURCE_EVIDENCE_FIELDS：集中保存`('dataset_id', 'snapshot_date', 'snapshot_phase', 'schema_version', 'entity_key', 'source_row_numbe…`对应的合同值、Schema集合或运行边界。
# - 来源与范围：该值来自当前项目任务、配置、真实数据画像或安全合同；未明确说明时不得外推为行业统一标准。
# - 单位与实例：数值单位由变量名、相邻校验和调用语义共同限定；字符串用于版本、字段、状态或DolphinDB对象标识。
# - 为什么这样写：集中命名固定参数可避免魔法值散落，并让升级、审计和回归测试有稳定锚点。
SOURCE_EVIDENCE_FIELDS = (
    "dataset_id",
    "snapshot_date",
    "snapshot_phase",
    "schema_version",
    "entity_key",
    "source_row_number",
    "source_file_name",
    "source_file_relative_path",
    "source_file_size_bytes",
    "source_file_mtime_utc",
    "source_file_sha256",
    "row_sha256",
    "ingest_batch_id",
    "ingested_at_utc",
    "quality_status",
    "raw_row_json",
)

# 关键常量PRIMARY_KEY_FIELDS：集中保存`{'DailyBar': ('instrument_id', 'trade_date'), 'AuctionSnapshot': ('instrument_id', 'trade_date', 'a…`对应的合同值、Schema集合或运行边界。
# - 来源与范围：该值来自当前项目任务、配置、真实数据画像或安全合同；未明确说明时不得外推为行业统一标准。
# - 单位与实例：数值单位由变量名、相邻校验和调用语义共同限定；字符串用于版本、字段、状态或DolphinDB对象标识。
# - 为什么这样写：集中命名固定参数可避免魔法值散落，并让升级、审计和回归测试有稳定锚点。
PRIMARY_KEY_FIELDS = {
    "DailyBar": ("instrument_id", "trade_date"),
    "AuctionSnapshot": (
        "instrument_id",
        "trade_date",
        "auction_phase",
        "snapshot_time_precision",
    ),
    "ClassificationMarketSnapshot": (
        "classification_system",
        "classification_type",
        "node_id",
        "trade_date",
        "snapshot_phase",
    ),
    "MoneyFlowSnapshot": (
        "instrument_id",
        "trade_date",
        "flow_method_code",
    ),
}


# 类ReadonlyQueryAdapter：服务依赖的最小只读适配器合同。
# - 结构：继承或实现Protocol；类体约包含0个字段或常量、1个方法。
# - 数据变化：类定义阶段不执行隐式I/O，实例只在构造或显式方法调用时改变受控状态。
# - 实操：调用方通过该类型集中传递配置、记录、服务或结果，避免跨模块使用无约束字典。
# - 为什么这样写：强类型边界能集中维护单位、时点、主键和安全不变量，并降低供应商耦合。
class ReadonlyQueryAdapter(Protocol):
    """服务依赖的最小只读适配器合同。"""

    # 函数run_readonly_query：执行run_readonly_query对应的业务处理。
    # - 输入：script:str；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型Any；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把只读查询或来源发现步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    def run_readonly_query(self, script: str) -> Any:
        # 错误阻断：抛出`NotImplementedError`并停止当前正常路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
        # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
        raise NotImplementedError


# 类DailyFundsReadRequest：七类来源统一读取请求；entity_ids不限定为证券。
# - 结构：继承或实现object；类体约包含5个字段或常量、1个方法。
# - 数据变化：类定义阶段不执行隐式I/O，实例只在构造或显式方法调用时改变受控状态。
# - 实操：调用方通过该类型集中传递配置、记录、服务或结果，避免跨模块使用无约束字典。
# - 为什么这样写：强类型边界能集中维护单位、时点、主键和安全不变量，并降低供应商耦合。
@dataclass(frozen=True, slots=True)
class DailyFundsReadRequest:
    """七类来源统一读取请求；entity_ids不限定为证券。"""

    # 状态计算：把`无`的结果保存到`dataset_id`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    dataset_id: str
    # 状态计算：把`无`的结果保存到`entity_ids`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    entity_ids: tuple[str, ...]
    # 状态计算：把`无`的结果保存到`start_date`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    start_date: date
    # 状态计算：把`无`的结果保存到`end_date`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    end_date: date
    # 状态计算：把`5000`的结果保存到`limit_per_entity`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    limit_per_entity: int = 5_000

    # 函数__post_init__：执行__post_init__对应的业务处理。
    # - 输入：无外部业务参数；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型None；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    def __post_init__(self) -> None:
        # 状态计算：把`str(self.dataset_id).strip()`的结果保存到`dataset_id`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        dataset_id = str(self.dataset_id).strip()
        # 条件门禁：判断`not _DATASET_ID_PATTERN.fullmatch(dataset_id)`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if not _DATASET_ID_PATTERN.fullmatch(dataset_id):
            # 错误阻断：抛出`DataContractError('dataset_id格式不合法。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
            raise DataContractError("dataset_id格式不合法。")
        # 显式调用：执行`object.__setattr__(self, 'dataset_id', dataset_id)`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
        # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
        # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
        object.__setattr__(self, "dataset_id", dataset_id)

        # 状态计算：把`tuple((str(value).strip() for value in self.entity_ids))`的结果保存到`normalized`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        normalized = tuple(str(value).strip() for value in self.entity_ids)
        # 条件门禁：判断`not normalized or any((not value for value in normalized))`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if not normalized or any(not value for value in normalized):
            # 错误阻断：抛出`DataContractError('entity_ids至少包含一个非空实体。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
            raise DataContractError("entity_ids至少包含一个非空实体。")
        # 条件门禁：判断`len(set(normalized)) != len(normalized)`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if len(set(normalized)) != len(normalized):
            # 错误阻断：抛出`DataContractError('entity_ids不允许重复。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
            raise DataContractError("entity_ids不允许重复。")
        # 条件门禁：判断`any((len(value) > 128 for value in normalized))`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if any(len(value) > 128 for value in normalized):
            # 错误阻断：抛出`DataContractError('entity_id长度不能超过128。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
            raise DataContractError("entity_id长度不能超过128。")
        # 条件门禁：判断`any((any((ord(char) < 32 for char in value)) for value in normalized))`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if any(any(ord(char) < 32 for char in value) for value in normalized):
            # 错误阻断：抛出`DataContractError('entity_id不能包含控制字符。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
            raise DataContractError("entity_id不能包含控制字符。")
        # 显式调用：执行`object.__setattr__(self, 'entity_ids', normalized)`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
        # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
        # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
        object.__setattr__(self, "entity_ids", normalized)

        # 条件门禁：判断`not isinstance(self.start_date, date)`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if not isinstance(self.start_date, date):
            # 错误阻断：抛出`DataContractError('start_date必须是date。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
            raise DataContractError("start_date必须是date。")
        # 条件门禁：判断`not isinstance(self.end_date, date)`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if not isinstance(self.end_date, date):
            # 错误阻断：抛出`DataContractError('end_date必须是date。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
            raise DataContractError("end_date必须是date。")
        # 条件门禁：判断`self.start_date > self.end_date`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if self.start_date > self.end_date:
            # 错误阻断：抛出`DataContractError('start_date不能晚于end_date。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
            raise DataContractError("start_date不能晚于end_date。")
        # 条件门禁：判断`not isinstance(self.limit_per_entity, int) or not 1 <= self.limit_per_entity <= 5000`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if (
            not isinstance(self.limit_per_entity, int)
            or not 1 <= self.limit_per_entity <= 5_000
        ):
            # 错误阻断：抛出`DataContractError('limit_per_entity必须是1到5000之间的整数。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
            raise DataContractError(
                "limit_per_entity必须是1到5000之间的整数。"
            )


# 类DailyFundsCanonicalRecord：集中管理DailyFundsCanonicalRecord相关状态和不变量。
# - 结构：继承或实现object；类体约包含10个字段或常量、0个方法。
# - 数据变化：类定义阶段不执行隐式I/O，实例只在构造或显式方法调用时改变受控状态。
# - 实操：调用方通过该类型集中传递配置、记录、服务或结果，避免跨模块使用无约束字典。
# - 为什么这样写：强类型边界能集中维护单位、时点、主键和安全不变量，并降低供应商耦合。
@dataclass(frozen=True, slots=True)
class DailyFundsCanonicalRecord:
    # 状态计算：把`无`的结果保存到`dataset_id`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    dataset_id: str
    # 状态计算：把`无`的结果保存到`canonical_object`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    canonical_object: str
    # 状态计算：把`无`的结果保存到`primary_key`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    primary_key: dict[str, Any]
    # 状态计算：把`无`的结果保存到`values`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    values: dict[str, Any]
    # 状态计算：把`无`的结果保存到`source_record_id`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    source_record_id: str
    # 状态计算：把`field(default_factory=dict)`的结果保存到`source_extensions`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    source_extensions: dict[str, Any] = field(default_factory=dict)
    # 状态计算：把`()`的结果保存到`quality_flags`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    quality_flags: tuple[str, ...] = ()
    # 状态计算：把`()`的结果保存到`lineage`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    lineage: tuple[dict[str, Any], ...] = ()
    # 状态计算：把`None`的结果保存到`snapshot_date`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    snapshot_date: date | None = None
    # 状态计算：把`None`的结果保存到`ingested_at`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    ingested_at: datetime | None = None


# 类DailyFundsStandardBatch：集中管理DailyFundsStandardBatch相关状态和不变量。
# - 结构：继承或实现object；类体约包含9个字段或常量、0个方法。
# - 数据变化：类定义阶段不执行隐式I/O，实例只在构造或显式方法调用时改变受控状态。
# - 实操：调用方通过该类型集中传递配置、记录、服务或结果，避免跨模块使用无约束字典。
# - 为什么这样写：强类型边界能集中维护单位、时点、主键和安全不变量，并降低供应商耦合。
@dataclass(frozen=True, slots=True)
class DailyFundsStandardBatch:
    # 状态计算：把`无`的结果保存到`dataset_id`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    dataset_id: str
    # 状态计算：把`无`的结果保存到`canonical_object`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    canonical_object: str
    # 状态计算：把`无`的结果保存到`coverage_version`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    coverage_version: str
    # 状态计算：把`无`的结果保存到`mapping_version`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    mapping_version: str
    # 状态计算：把`无`的结果保存到`dictionary_revision`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    dictionary_revision: str
    # 状态计算：把`无`的结果保存到`scanned_source_row_count`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    scanned_source_row_count: int
    # 状态计算：把`无`的结果保存到`source_row_count`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    source_row_count: int
    # 状态计算：把`无`的结果保存到`records`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    records: tuple[DailyFundsCanonicalRecord, ...]
    # 状态计算：把`()`的结果保存到`warnings`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    warnings: tuple[str, ...] = ()


# 函数_load_yaml：执行_load_yaml对应的业务处理。
# - 输入：path:Path；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型dict[str, Any]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
# - 为什么这样写：把只读查询或来源发现步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def _load_yaml(path: Path) -> dict[str, Any]:
    # 状态计算：把`yaml.safe_load(path.read_text(encoding='utf-8'))`的结果保存到`payload`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    # 条件门禁：判断`not isinstance(payload, dict)`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if not isinstance(payload, dict):
        # 错误阻断：抛出`DataContractError(f'YAML根节点必须是映射：{path}')`并停止当前正常路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
        # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
        raise DataContractError(f"YAML根节点必须是映射：{path}")
    # 结果返回：把`payload`交给调用方并结束当前函数。
    # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return payload


# 函数_is_missing：执行_is_missing对应的业务处理。
# - 输入：value:Any；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型bool；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
# - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def _is_missing(value: Any) -> bool:
    # 条件门禁：判断`value is None`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if value is None:
        # 结果返回：把`True`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return True
    # 条件门禁：判断`isinstance(value, str)`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if isinstance(value, str):
        # 结果返回：把`not value.strip()`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return not value.strip()
    # 异常边界：尝试执行可能失败的解析、查询、文件或类型转换步骤，并由后续处理保留错误证据。
    # - 数据变化：正常路径产生业务结果；异常路径不得静默伪造数据，应抛出、记录或隔离。
    # - 为什么这样写：把外部环境故障与业务合同失败分开，便于重试、回滚和准确验收。
    try:
        # 状态计算：把`value != value`的结果保存到`unequal`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        unequal = value != value
        # 条件门禁：判断`isinstance(unequal, bool) and unequal`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if isinstance(unequal, bool) and unequal:
            # 结果返回：把`True`交给调用方并结束当前函数。
            # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
            # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
            return True
    except Exception:
        # 控制流：保留显式空分支，使循环或占位分支按既定合同继续。
        # - 数据变化：本语句不直接改变业务记录，只调整当前执行路径。
        # - 为什么这样写：显式控制流比隐式嵌套更容易检查边界和异常处理。
        pass
    # 异常边界：尝试执行可能失败的解析、查询、文件或类型转换步骤，并由后续处理保留错误证据。
    # - 数据变化：正常路径产生业务结果；异常路径不得静默伪造数据，应抛出、记录或隔离。
    # - 为什么这样写：把外部环境故障与业务合同失败分开，便于重试、回滚和准确验收。
    try:
        # 结果返回：把`bool(math.isnan(value))`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return bool(math.isnan(value))
    except (TypeError, ValueError):
        # 结果返回：把`False`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return False


# 函数_python_scalar：执行_python_scalar对应的业务处理。
# - 输入：value:Any；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型Any；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
# - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def _python_scalar(value: Any) -> Any:
    # 条件门禁：判断`_is_missing(value)`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if _is_missing(value):
        # 结果返回：把`None`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return None
    # 状态计算：把`getattr(value, 'item', None)`的结果保存到`item`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    item = getattr(value, "item", None)
    # 条件门禁：判断`callable(item)`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if callable(item):
        # 异常边界：尝试执行可能失败的解析、查询、文件或类型转换步骤，并由后续处理保留错误证据。
        # - 数据变化：正常路径产生业务结果；异常路径不得静默伪造数据，应抛出、记录或隔离。
        # - 为什么这样写：把外部环境故障与业务合同失败分开，便于重试、回滚和准确验收。
        try:
            # 结果返回：把`item()`交给调用方并结束当前函数。
            # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
            # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
            return item()
        except (TypeError, ValueError):
            # 控制流：保留显式空分支，使循环或占位分支按既定合同继续。
            # - 数据变化：本语句不直接改变业务记录，只调整当前执行路径。
            # - 为什么这样写：显式控制流比隐式嵌套更容易检查边界和异常处理。
            pass
    # 结果返回：把`value`交给调用方并结束当前函数。
    # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return value


# 函数_clean_text：执行_clean_text对应的业务处理。
# - 输入：value:Any；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型str | None；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
# - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def _clean_text(value: Any) -> str | None:
    # 条件门禁：判断`_is_missing(value)`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if _is_missing(value):
        # 结果返回：把`None`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return None
    # 状态计算：把`str(_python_scalar(value)).strip()`的结果保存到`text`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    text = str(_python_scalar(value)).strip()
    # 结果返回：把`text or None`交给调用方并结束当前函数。
    # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return text or None


# 函数_as_float：执行_as_float对应的业务处理。
# - 输入：value:Any；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型float | None；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
# - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def _as_float(value: Any) -> float | None:
    # 条件门禁：判断`_is_missing(value)`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if _is_missing(value):
        # 结果返回：把`None`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return None
    # 异常边界：尝试执行可能失败的解析、查询、文件或类型转换步骤，并由后续处理保留错误证据。
    # - 数据变化：正常路径产生业务结果；异常路径不得静默伪造数据，应抛出、记录或隔离。
    # - 为什么这样写：把外部环境故障与业务合同失败分开，便于重试、回滚和准确验收。
    try:
        # 状态计算：把`float(value)`的结果保存到`number`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        # 结果返回：把`None`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return None
    # 结果返回：把`number if math.isfinite(number) else None`交给调用方并结束当前函数。
    # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return number if math.isfinite(number) else None


# 函数_as_integral：执行_as_integral对应的业务处理。
# - 输入：value:Any；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型int | None；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
# - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def _as_integral(value: Any) -> int | None:
    # 状态计算：把`_as_float(value)`的结果保存到`number`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    number = _as_float(value)
    # 条件门禁：判断`number is None`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if number is None:
        # 结果返回：把`None`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return None
    # 状态计算：把`round(number)`的结果保存到`rounded`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    rounded = round(number)
    # 条件门禁：判断`abs(number - rounded) > 1e-09`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if abs(number - rounded) > 1e-9:
        # 结果返回：把`None`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return None
    # 结果返回：把`int(rounded)`交给调用方并结束当前函数。
    # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return int(rounded)


# 函数_as_date：执行_as_date对应的业务处理。
# - 输入：value:Any；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型date | None；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
# - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def _as_date(value: Any) -> date | None:
    # 条件门禁：判断`_is_missing(value)`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if _is_missing(value):
        # 结果返回：把`None`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return None
    # 条件门禁：判断`isinstance(value, datetime)`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if isinstance(value, datetime):
        # 结果返回：把`value.date()`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return value.date()
    # 条件门禁：判断`isinstance(value, date)`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if isinstance(value, date):
        # 结果返回：把`value`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return value
    # 状态计算：把`getattr(value, 'to_pydatetime', None)`的结果保存到`to_pydatetime`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    to_pydatetime = getattr(value, "to_pydatetime", None)
    # 条件门禁：判断`callable(to_pydatetime)`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if callable(to_pydatetime):
        # 状态计算：把`to_pydatetime()`的结果保存到`converted`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        converted = to_pydatetime()
        # 条件门禁：判断`isinstance(converted, datetime)`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if isinstance(converted, datetime):
            # 结果返回：把`converted.date()`交给调用方并结束当前函数。
            # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
            # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
            return converted.date()
        # 条件门禁：判断`isinstance(converted, date)`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if isinstance(converted, date):
            # 结果返回：把`converted`交给调用方并结束当前函数。
            # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
            # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
            return converted
    # 状态计算：把`str(value).strip().replace('.', '-')`的结果保存到`text`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    text = str(value).strip().replace(".", "-")
    # 异常边界：尝试执行可能失败的解析、查询、文件或类型转换步骤，并由后续处理保留错误证据。
    # - 数据变化：正常路径产生业务结果；异常路径不得静默伪造数据，应抛出、记录或隔离。
    # - 为什么这样写：把外部环境故障与业务合同失败分开，便于重试、回滚和准确验收。
    try:
        # 结果返回：把`date.fromisoformat(text[:10])`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return date.fromisoformat(text[:10])
    except ValueError:
        # 结果返回：把`None`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return None


# 函数_as_datetime：执行_as_datetime对应的业务处理。
# - 输入：value:Any；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型datetime | None；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
# - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def _as_datetime(value: Any) -> datetime | None:
    # 条件门禁：判断`_is_missing(value)`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if _is_missing(value):
        # 结果返回：把`None`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return None
    # 条件门禁：判断`isinstance(value, datetime)`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if isinstance(value, datetime):
        # 结果返回：把`value`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return value
    # 状态计算：把`getattr(value, 'to_pydatetime', None)`的结果保存到`to_pydatetime`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    to_pydatetime = getattr(value, "to_pydatetime", None)
    # 条件门禁：判断`callable(to_pydatetime)`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if callable(to_pydatetime):
        # 状态计算：把`to_pydatetime()`的结果保存到`converted`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        converted = to_pydatetime()
        # 条件门禁：判断`isinstance(converted, datetime)`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if isinstance(converted, datetime):
            # 结果返回：把`converted`交给调用方并结束当前函数。
            # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
            # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
            return converted
    # 状态计算：把`str(value).strip().replace('Z', '+00:00')`的结果保存到`text`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    text = str(value).strip().replace("Z", "+00:00")
    # 异常边界：尝试执行可能失败的解析、查询、文件或类型转换步骤，并由后续处理保留错误证据。
    # - 数据变化：正常路径产生业务结果；异常路径不得静默伪造数据，应抛出、记录或隔离。
    # - 为什么这样写：把外部环境故障与业务合同失败分开，便于重试、回滚和准确验收。
    try:
        # 结果返回：把`datetime.fromisoformat(text)`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return datetime.fromisoformat(text)
    except ValueError:
        # 结果返回：把`None`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return None


# 函数normalise_query_records：把DolphinDB常见返回值转换为字典行。
# - 输入：result:Any；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型list[dict[str, Any]]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
# - 为什么这样写：把只读查询或来源发现步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def normalise_query_records(result: Any) -> list[dict[str, Any]]:
    """把DolphinDB常见返回值转换为字典行。"""
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
        # 条件门禁：判断`any((not isinstance(item, dict) for item in result))`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if any(not isinstance(item, dict) for item in result):
            # 错误阻断：抛出`DataContractError('DolphinDB列表结果包含非字典行。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
            raise DataContractError("DolphinDB列表结果包含非字典行。")
        # 结果返回：把`[dict(item) for item in result]`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return [dict(item) for item in result]
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
            # 状态计算：把`to_dict(orient='records')`的结果保存到`rows`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            rows = to_dict(orient="records")
        except TypeError:
            # 状态计算：把`to_dict('records')`的结果保存到`rows`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            rows = to_dict("records")
        # 条件门禁：判断`any((not isinstance(item, dict) for item in rows))`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if any(not isinstance(item, dict) for item in rows):
            # 错误阻断：抛出`DataContractError('DolphinDB表格结果无法转换为字典行。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
            raise DataContractError("DolphinDB表格结果无法转换为字典行。")
        # 结果返回：把`[dict(item) for item in rows]`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return [dict(item) for item in rows]
    # 错误阻断：抛出`DataContractError('不支持当前DolphinDB查询返回值类型。')`并停止当前正常路径。
    # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
    # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
    raise DataContractError("不支持当前DolphinDB查询返回值类型。")


# 函数provisional_node_id：执行provisional_node_id对应的业务处理。
# - 输入：classification_type:Any、node_name:Any；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型str | None；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
# - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def provisional_node_id(
    classification_type: Any,
    node_name: Any,
) -> str | None:
    # 状态计算：把`_clean_text(classification_type)`的结果保存到`type_text`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    type_text = _clean_text(classification_type)
    # 状态计算：把`_clean_text(node_name)`的结果保存到`name_text`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    name_text = _clean_text(node_name)
    # 条件门禁：判断`type_text is None or name_text is None`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if type_text is None or name_text is None:
        # 结果返回：把`None`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return None
    # 状态计算：把`type_text.upper()`的结果保存到`normalized_type`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    normalized_type = type_text.upper()
    # 状态计算：把`unicodedata.normalize('NFKC', name_text).strip()`的结果保存到`normalized_name`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    normalized_name = unicodedata.normalize("NFKC", name_text).strip()
    # 状态计算：把`hashlib.sha256(f'{normalized_type}|{normalized_name}'.encode('utf-8')).hexdigest()[:20].upper()`的结果保存到`digest`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    digest = hashlib.sha256(
        f"{normalized_type}|{normalized_name}".encode("utf-8")
    ).hexdigest()[:20].upper()
    # 结果返回：把`f'SOURCE_VENDOR:{normalized_type}:{digest}'`交给调用方并结束当前函数。
    # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return f"SOURCE_VENDOR:{normalized_type}:{digest}"


# 函数_dictionary_objects：执行_dictionary_objects对应的业务处理。
# - 输入：dictionary:Mapping[str, Any]；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型dict[str, dict[str, dict[str, Any]]]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
# - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def _dictionary_objects(
    dictionary: Mapping[str, Any],
) -> dict[str, dict[str, dict[str, Any]]]:
    # 状态计算：把`{}`的结果保存到`objects`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    objects: dict[str, dict[str, dict[str, Any]]] = {}
    # 循环处理：逐项遍历`dictionary.get('domains', [])`，把当前元素绑定到`domain`。
    # - 数据变化：每轮只处理一个来源记录、字段、文件或证据项，并显式累计到局部集合或输出对象。
    # - 为什么这样写：逐项处理便于保留行级血缘、隔离单项异常，并控制16GB单机上的峰值内存。
    for domain in dictionary.get("domains", []):
        # 条件门禁：判断`not isinstance(domain, dict)`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if not isinstance(domain, dict):
            # 控制流：跳过本轮剩余步骤，使循环或占位分支按既定合同继续。
            # - 数据变化：本语句不直接改变业务记录，只调整当前执行路径。
            # - 为什么这样写：显式控制流比隐式嵌套更容易检查边界和异常处理。
            continue
        # 状态计算：把`_clean_text(domain.get('canonical_object'))`的结果保存到`object_name`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        object_name = _clean_text(domain.get("canonical_object"))
        # 条件门禁：判断`object_name is None`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if object_name is None:
            # 控制流：跳过本轮剩余步骤，使循环或占位分支按既定合同继续。
            # - 数据变化：本语句不直接改变业务记录，只调整当前执行路径。
            # - 为什么这样写：显式控制流比隐式嵌套更容易检查边界和异常处理。
            continue
        # 状态计算：把`objects.setdefault(object_name, {})`的结果保存到`catalog`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        catalog = objects.setdefault(object_name, {})
        # 循环处理：逐项遍历`domain.get('fields', [])`，把当前元素绑定到`item`。
        # - 数据变化：每轮只处理一个来源记录、字段、文件或证据项，并显式累计到局部集合或输出对象。
        # - 为什么这样写：逐项处理便于保留行级血缘、隔离单项异常，并控制16GB单机上的峰值内存。
        for item in domain.get("fields", []):
            # 条件门禁：判断`not isinstance(item, dict)`，条件成立时进入对应的数据、安全或异常处理分支。
            # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
            # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
            if not isinstance(item, dict):
                # 控制流：跳过本轮剩余步骤，使循环或占位分支按既定合同继续。
                # - 数据变化：本语句不直接改变业务记录，只调整当前执行路径。
                # - 为什么这样写：显式控制流比隐式嵌套更容易检查边界和异常处理。
                continue
            # 状态计算：把`_clean_text(item.get('canonical_name'))`的结果保存到`field_name`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            field_name = _clean_text(item.get("canonical_name"))
            # 条件门禁：判断`field_name`，条件成立时进入对应的数据、安全或异常处理分支。
            # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
            # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
            if field_name:
                # 状态计算：把`dict(item)`的结果保存到`catalog[field_name]`，供当前逻辑后续校验、转换、累计或返回。
                # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
                # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
                catalog[field_name] = dict(item)
    # 结果返回：把`objects`交给调用方并结束当前函数。
    # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return objects


# 函数_mapping_source_fields：执行_mapping_source_fields对应的业务处理。
# - 输入：mapping:Mapping[str, Any]；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型tuple[str, ...]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
# - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def _mapping_source_fields(mapping: Mapping[str, Any]) -> tuple[str, ...]:
    # 状态计算：把`mapping.get('source')`的结果保存到`source`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    source = mapping.get("source")
    # 条件门禁：判断`source is None`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if source is None:
        # 结果返回：把`()`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return ()
    # 条件门禁：判断`isinstance(source, list)`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if isinstance(source, list):
        # 结果返回：把`tuple((str(item) for item in source))`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return tuple(str(item) for item in source)
    # 结果返回：把`(str(source),)`交给调用方并结束当前函数。
    # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return (str(source),)


# 函数validate_daily_funds_service_contract：执行validate_daily_funds_service_contract对应的业务处理。
# - 输入：project_root:str | Path；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型dict[str, Any]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
# - 为什么这样写：把合同、数据质量或安全门禁校验步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
def validate_daily_funds_service_contract(
    project_root: str | Path,
) -> dict[str, Any]:
    # 状态计算：把`str(Path(project_root).resolve())`的结果保存到`root`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    root = str(Path(project_root).resolve())
    # 结果返回：把`copy.deepcopy(_validate_daily_funds_service_contract_cached(root))`交给调用方并结束当前函数。
    # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return copy.deepcopy(_validate_daily_funds_service_contract_cached(root))


# 函数_validate_daily_funds_service_contract_cached：执行_validate_daily_funds_service_contract_cached对应的业务处理。
# - 输入：project_root:str；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型dict[str, Any]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
# - 为什么这样写：把合同、数据质量或安全门禁校验步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
@lru_cache(maxsize=16)
def _validate_daily_funds_service_contract_cached(
    project_root: str,
) -> dict[str, Any]:
    # 状态计算：把`Path(project_root)`的结果保存到`root`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    root = Path(project_root)
    # 状态计算：把`_load_yaml(root / SERVICE_CONFIG_RELATIVE_PATH)`的结果保存到`config`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    config = _load_yaml(root / SERVICE_CONFIG_RELATIVE_PATH)
    # 状态计算：把`root / str(config.get('mapping_contract_path', ''))`的结果保存到`mapping_path`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    mapping_path = root / str(config.get("mapping_contract_path", ""))
    # 状态计算：把`root / str(config.get('dictionary_path', ''))`的结果保存到`dictionary_path`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    dictionary_path = root / str(config.get("dictionary_path", ""))
    # 状态计算：把`root / str(config.get('enum_definitions_path', ''))`的结果保存到`enum_path`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    enum_path = root / str(config.get("enum_definitions_path", ""))
    # 状态计算：把`validate_contract(mapping_path, dictionary_path)`的结果保存到`mapping_validation`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    mapping_validation = validate_contract(mapping_path, dictionary_path)
    # 状态计算：把`load_contract(mapping_path)`的结果保存到`mapping_contract`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    mapping_contract = load_contract(mapping_path)
    # 状态计算：把`_load_yaml(dictionary_path)`的结果保存到`dictionary`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    dictionary = _load_yaml(dictionary_path)
    # 状态计算：把`_load_yaml(enum_path)`的结果保存到`enum_definitions`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    enum_definitions = _load_yaml(enum_path)
    # 状态计算：把`_dictionary_objects(dictionary)`的结果保存到`objects`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    objects = _dictionary_objects(dictionary)
    # 状态计算：把`[]`的结果保存到`issues`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    issues: list[dict[str, Any]] = []

    # 条件门禁：判断`mapping_validation['overall_status'] != 'PASSED_WITH_WARNINGS'`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if mapping_validation["overall_status"] != "PASSED_WITH_WARNINGS":
        # 显式调用：执行`issues.append({'severity': 'ERROR', 'code': 'MAPPING_CONTRACT_NOT_APPROVED', 'detail': mapping_validation})`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
        # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
        # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
        issues.append(
            {
                "severity": "ERROR",
                "code": "MAPPING_CONTRACT_NOT_APPROVED",
                "detail": mapping_validation,
            }
        )
    # 条件门禁：判断`config.get('mapping_version') != mapping_contract.contract_version`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if config.get("mapping_version") != mapping_contract.contract_version:
        # 显式调用：执行`issues.append({'severity': 'ERROR', 'code': 'MAPPING_VERSION_MISMATCH'})`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
        # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
        # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
        issues.append(
            {
                "severity": "ERROR",
                "code": "MAPPING_VERSION_MISMATCH",
            }
        )
    # 条件门禁：判断`str(config.get('dictionary_revision')) != str(dictionary.get('dictionary_revision'))`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if str(config.get("dictionary_revision")) != str(
        dictionary.get("dictionary_revision")
    ):
        # 显式调用：执行`issues.append({'severity': 'ERROR', 'code': 'DICTIONARY_REVISION_MISMATCH'})`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
        # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
        # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
        issues.append(
            {
                "severity": "ERROR",
                "code": "DICTIONARY_REVISION_MISMATCH",
            }
        )
    # 状态计算：把`str(config.get('database_uri', ''))`的结果保存到`database_uri`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    database_uri = str(config.get("database_uri", ""))
    # 条件门禁：判断`not _DATABASE_URI_PATTERN.fullmatch(database_uri)`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if not _DATABASE_URI_PATTERN.fullmatch(database_uri):
        # 显式调用：执行`issues.append({'severity': 'ERROR', 'code': 'DATABASE_URI_INVALID'})`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
        # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
        # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
        issues.append(
            {
                "severity": "ERROR",
                "code": "DATABASE_URI_INVALID",
            }
        )

    # 状态计算：把`config.get('coverage', {})`的结果保存到`coverage`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    coverage = config.get("coverage", {})
    # 状态计算：把`_as_date(coverage.get('start_date'))`的结果保存到`coverage_start`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    coverage_start = _as_date(coverage.get("start_date"))
    # 状态计算：把`_as_date(coverage.get('end_date'))`的结果保存到`coverage_end`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    coverage_end = _as_date(coverage.get("end_date"))
    # 条件门禁：判断`coverage_start is None or coverage_end is None or coverage_start > coverage_end`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if (
        coverage_start is None
        or coverage_end is None
        or coverage_start > coverage_end
    ):
        # 显式调用：执行`issues.append({'severity': 'ERROR', 'code': 'COVERAGE_RANGE_INVALID'})`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
        # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
        # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
        issues.append(
            {
                "severity": "ERROR",
                "code": "COVERAGE_RANGE_INVALID",
            }
        )

    # 状态计算：把`config.get('dataset_profiles', {})`的结果保存到`profiles`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    profiles = config.get("dataset_profiles", {})
    # 条件门禁：判断`set(profiles) != set(REQUIRED_DATASETS)`，条件成立时进入对应的数据、安全或异常处理分支。
    # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
    # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
    if set(profiles) != set(REQUIRED_DATASETS):
        # 显式调用：执行`issues.append({'severity': 'ERROR', 'code': 'DATASET_PROFILE_SET_MISMATCH'})`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
        # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
        # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
        issues.append(
            {
                "severity": "ERROR",
                "code": "DATASET_PROFILE_SET_MISMATCH",
            }
        )

    # 状态计算：把`set()`的结果保存到`used_transforms`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    used_transforms: set[str] = set()
    # 循环处理：逐项遍历`mapping_contract.datasets.items()`，把当前元素绑定到`(dataset_id, dataset)`。
    # - 数据变化：每轮只处理一个来源记录、字段、文件或证据项，并显式累计到局部集合或输出对象。
    # - 为什么这样写：逐项处理便于保留行级血缘、隔离单项异常，并控制16GB单机上的峰值内存。
    for dataset_id, dataset in mapping_contract.datasets.items():
        # 状态计算：把`profiles.get(dataset_id, {})`的结果保存到`profile`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        profile = profiles.get(dataset_id, {})
        # 状态计算：把`str(dataset.get('family', ''))`的结果保存到`family`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        family = str(dataset.get("family", ""))
        # 状态计算：把`str(dataset.get('canonical_object', ''))`的结果保存到`canonical_object`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        canonical_object = str(dataset.get("canonical_object", ""))
        # 状态计算：把`str(dataset.get('source_table', ''))`的结果保存到`source_table`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        source_table = str(dataset.get("source_table", ""))
        # 条件门禁：判断`profile.get('family') != family`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if profile.get("family") != family:
            # 显式调用：执行`issues.append({'severity': 'ERROR', 'code': 'PROFILE_FAMILY_MISMATCH', 'dataset_id': dataset_id})`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
            # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
            # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
            issues.append(
                {
                    "severity": "ERROR",
                    "code": "PROFILE_FAMILY_MISMATCH",
                    "dataset_id": dataset_id,
                }
            )
        # 条件门禁：判断`profile.get('canonical_object') != canonical_object`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if profile.get("canonical_object") != canonical_object:
            # 显式调用：执行`issues.append({'severity': 'ERROR', 'code': 'PROFILE_OBJECT_MISMATCH', 'dataset_id': dataset_id})`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
            # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
            # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
            issues.append(
                {
                    "severity": "ERROR",
                    "code": "PROFILE_OBJECT_MISMATCH",
                    "dataset_id": dataset_id,
                }
            )
        # 条件门禁：判断`profile.get('source_table') != source_table`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if profile.get("source_table") != source_table:
            # 显式调用：执行`issues.append({'severity': 'ERROR', 'code': 'PROFILE_TABLE_MISMATCH', 'dataset_id': dataset_id})`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
            # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
            # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
            issues.append(
                {
                    "severity": "ERROR",
                    "code": "PROFILE_TABLE_MISMATCH",
                    "dataset_id": dataset_id,
                }
            )
        # 条件门禁：判断`not _IDENTIFIER_PATTERN.fullmatch(source_table)`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if not _IDENTIFIER_PATTERN.fullmatch(source_table):
            # 显式调用：执行`issues.append({'severity': 'ERROR', 'code': 'SOURCE_TABLE_INVALID', 'dataset_id': dataset_id})`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
            # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
            # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
            issues.append(
                {
                    "severity": "ERROR",
                    "code": "SOURCE_TABLE_INVALID",
                    "dataset_id": dataset_id,
                }
            )
        # 状态计算：把`RAW_FIELD_CATALOG.get(family, frozenset())`的结果保存到`raw_fields`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        raw_fields = RAW_FIELD_CATALOG.get(family, frozenset())
        # 循环处理：逐项遍历`dataset.get('mappings', [])`，把当前元素绑定到`mapping`。
        # - 数据变化：每轮只处理一个来源记录、字段、文件或证据项，并显式累计到局部集合或输出对象。
        # - 为什么这样写：逐项处理便于保留行级血缘、隔离单项异常，并控制16GB单机上的峰值内存。
        for mapping in dataset.get("mappings", []):
            # 状态计算：把`str(mapping.get('transform', ''))`的结果保存到`transform`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            transform = str(mapping.get("transform", ""))
            # 显式调用：执行`used_transforms.add(transform)`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
            # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
            # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
            used_transforms.add(transform)
            # 条件门禁：判断`transform not in SUPPORTED_TRANSFORMS`，条件成立时进入对应的数据、安全或异常处理分支。
            # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
            # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
            if transform not in SUPPORTED_TRANSFORMS:
                # 显式调用：执行`issues.append({'severity': 'ERROR', 'code': 'UNSUPPORTED_TRANSFORM', 'dataset_id': dataset_id, 'transform': transform})`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
                # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
                # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
                issues.append(
                    {
                        "severity": "ERROR",
                        "code": "UNSUPPORTED_TRANSFORM",
                        "dataset_id": dataset_id,
                        "transform": transform,
                    }
                )
            # 循环处理：逐项遍历`_mapping_source_fields(mapping)`，把当前元素绑定到`source_field`。
            # - 数据变化：每轮只处理一个来源记录、字段、文件或证据项，并显式累计到局部集合或输出对象。
            # - 为什么这样写：逐项处理便于保留行级血缘、隔离单项异常，并控制16GB单机上的峰值内存。
            for source_field in _mapping_source_fields(mapping):
                # 条件门禁：判断`source_field not in raw_fields`，条件成立时进入对应的数据、安全或异常处理分支。
                # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
                # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
                if source_field not in raw_fields:
                    # 显式调用：执行`issues.append({'severity': 'ERROR', 'code': 'MAPPING_SOURCE_FIELD_NOT_IN_RAW_SCHEMA', 'dataset_id': dataset_id, 'source_field': source_fiel…`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
                    # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
                    # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
                    issues.append(
                        {
                            "severity": "ERROR",
                            "code": "MAPPING_SOURCE_FIELD_NOT_IN_RAW_SCHEMA",
                            "dataset_id": dataset_id,
                            "source_field": source_field,
                        }
                    )
        # 循环处理：逐项遍历`dataset.get('source_extensions', [])`，把当前元素绑定到`field_name`。
        # - 数据变化：每轮只处理一个来源记录、字段、文件或证据项，并显式累计到局部集合或输出对象。
        # - 为什么这样写：逐项处理便于保留行级血缘、隔离单项异常，并控制16GB单机上的峰值内存。
        for field_name in dataset.get("source_extensions", []):
            # 条件门禁：判断`field_name not in raw_fields`，条件成立时进入对应的数据、安全或异常处理分支。
            # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
            # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
            if field_name not in raw_fields:
                # 显式调用：执行`issues.append({'severity': 'ERROR', 'code': 'SOURCE_EXTENSION_NOT_IN_RAW_SCHEMA', 'dataset_id': dataset_id, 'source_field': field_name})`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
                # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
                # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
                issues.append(
                    {
                        "severity": "ERROR",
                        "code": "SOURCE_EXTENSION_NOT_IN_RAW_SCHEMA",
                        "dataset_id": dataset_id,
                        "source_field": field_name,
                    }
                )
        # 条件门禁：判断`canonical_object not in objects`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if canonical_object not in objects:
            # 显式调用：执行`issues.append({'severity': 'ERROR', 'code': 'CANONICAL_OBJECT_MISSING', 'dataset_id': dataset_id})`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
            # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
            # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
            issues.append(
                {
                    "severity": "ERROR",
                    "code": "CANONICAL_OBJECT_MISSING",
                    "dataset_id": dataset_id,
                }
            )
        else:
            # 循环处理：逐项遍历`dataset.get('mappings', [])`，把当前元素绑定到`mapping`。
            # - 数据变化：每轮只处理一个来源记录、字段、文件或证据项，并显式累计到局部集合或输出对象。
            # - 为什么这样写：逐项处理便于保留行级血缘、隔离单项异常，并控制16GB单机上的峰值内存。
            for mapping in dataset.get("mappings", []):
                # 状态计算：把`str(mapping.get('target', ''))`的结果保存到`target`，供当前逻辑后续校验、转换、累计或返回。
                # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
                # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
                target = str(mapping.get("target", ""))
                # 条件门禁：判断`target not in objects[canonical_object]`，条件成立时进入对应的数据、安全或异常处理分支。
                # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
                # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
                if target not in objects[canonical_object]:
                    # 显式调用：执行`issues.append({'severity': 'ERROR', 'code': 'TARGET_FIELD_MISSING', 'dataset_id': dataset_id, 'target': target})`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
                    # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
                    # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
                    issues.append(
                        {
                            "severity": "ERROR",
                            "code": "TARGET_FIELD_MISSING",
                            "dataset_id": dataset_id,
                            "target": target,
                        }
                    )
                # 状态计算：把`objects[canonical_object].get(target, {})`的结果保存到`field_def`，供当前逻辑后续校验、转换、累计或返回。
                # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
                # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
                field_def = objects[canonical_object].get(target, {})
                # 状态计算：把`field_def.get('enum_ref')`的结果保存到`enum_ref`，供当前逻辑后续校验、转换、累计或返回。
                # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
                # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
                enum_ref = field_def.get("enum_ref")
                # 条件门禁：判断`enum_ref and enum_ref not in enum_definitions`，条件成立时进入对应的数据、安全或异常处理分支。
                # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
                # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
                if enum_ref and enum_ref not in enum_definitions:
                    # 显式调用：执行`issues.append({'severity': 'ERROR', 'code': 'ENUM_REFERENCE_MISSING', 'dataset_id': dataset_id, 'target': target, 'enum_ref': enum_ref})`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
                    # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
                    # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
                    issues.append(
                        {
                            "severity": "ERROR",
                            "code": "ENUM_REFERENCE_MISSING",
                            "dataset_id": dataset_id,
                            "target": target,
                            "enum_ref": enum_ref,
                        }
                    )

    # 状态计算：把`config.get('query_policy', {})`的结果保存到`query_policy`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    query_policy = config.get("query_policy", {})
    # 循环处理：逐项遍历`(('max_entity_ids', 1, 1000), ('max_limit_per_entity', 1, 5000), ('max_raw_rows_per_request', 1, 10…`，把当前元素绑定到`(name, minimum, maximum)`。
    # - 数据变化：每轮只处理一个来源记录、字段、文件或证据项，并显式累计到局部集合或输出对象。
    # - 为什么这样写：逐项处理便于保留行级血缘、隔离单项异常，并控制16GB单机上的峰值内存。
    for name, minimum, maximum in (
        ("max_entity_ids", 1, 1000),
        ("max_limit_per_entity", 1, 5000),
        ("max_raw_rows_per_request", 1, 1_000_000),
    ):
        # 状态计算：把`query_policy.get(name)`的结果保存到`value`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        value = query_policy.get(name)
        # 条件门禁：判断`not isinstance(value, int) or not minimum <= value <= maximum`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if not isinstance(value, int) or not minimum <= value <= maximum:
            # 显式调用：执行`issues.append({'severity': 'ERROR', 'code': 'QUERY_POLICY_INVALID', 'field': name})`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
            # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
            # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
            issues.append(
                {
                    "severity": "ERROR",
                    "code": "QUERY_POLICY_INVALID",
                    "field": name,
                }
            )

    # 状态计算：把`[item for item in issues if item['severity'] == 'ERROR']`的结果保存到`errors`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    errors = [item for item in issues if item["severity"] == "ERROR"]
    # 结果返回：把`{'task_id': 'TASK_017C', 'service_id': config.get('service_id'), 'service_version': str(config.get('service_version')),…`交给调用方并结束当前函数。
    # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return {
        "task_id": "TASK_017C",
        "service_id": config.get("service_id"),
        "service_version": str(config.get("service_version")),
        "coverage_version": coverage.get("coverage_version"),
        "coverage_start": str(coverage_start),
        "coverage_end": str(coverage_end),
        "dataset_count": len(profiles),
        "raw_table_count": len(
            {item.get("source_table") for item in profiles.values()}
        ),
        "canonical_object_count": len(
            {item.get("canonical_object") for item in profiles.values()}
        ),
        "supported_transform_count": len(used_transforms),
        "known_quarantine_count": len(config.get("known_quarantines", [])),
        "overall_status": (
            "PASSED_WITH_WARNINGS" if not errors else "FAILED"
        ),
        "issues": issues,
    }


# 函数_load_service_assets：执行_load_service_assets对应的业务处理。
# - 输入：project_root:str；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
# - 输出：返回类型tuple[Any, ...]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
# - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
# - 为什么这样写：把只读查询或来源发现步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
@lru_cache(maxsize=16)
def _load_service_assets(project_root: str) -> tuple[Any, ...]:
    # 状态计算：把`Path(project_root)`的结果保存到`root`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    root = Path(project_root)
    # 状态计算：把`_load_yaml(root / SERVICE_CONFIG_RELATIVE_PATH)`的结果保存到`config`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    config = _load_yaml(root / SERVICE_CONFIG_RELATIVE_PATH)
    # 状态计算：把`root / str(config['mapping_contract_path'])`的结果保存到`mapping_path`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    mapping_path = root / str(config["mapping_contract_path"])
    # 状态计算：把`root / str(config['dictionary_path'])`的结果保存到`dictionary_path`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    dictionary_path = root / str(config["dictionary_path"])
    # 状态计算：把`root / str(config['enum_definitions_path'])`的结果保存到`enum_path`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    enum_path = root / str(config["enum_definitions_path"])
    # 状态计算：把`load_contract(mapping_path)`的结果保存到`mapping_contract`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    mapping_contract = load_contract(mapping_path)
    # 状态计算：把`_load_yaml(dictionary_path)`的结果保存到`dictionary`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    dictionary = _load_yaml(dictionary_path)
    # 状态计算：把`_load_yaml(enum_path)`的结果保存到`enum_definitions`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    enum_definitions = _load_yaml(enum_path)
    # 状态计算：把`_dictionary_objects(dictionary)`的结果保存到`object_fields`，供当前逻辑后续校验、转换、累计或返回。
    # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
    # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
    object_fields = _dictionary_objects(dictionary)
    # 结果返回：把`(config, mapping_path, dictionary_path, enum_path, mapping_contract, dictionary, enum_definitions, object_fields)`交给调用方并结束当前函数。
    # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
    # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
    return (
        config,
        mapping_path,
        dictionary_path,
        enum_path,
        mapping_contract,
        dictionary,
        enum_definitions,
        object_fields,
    )


# 类DolphinDBDailyFundsCanonicalService：三张Raw表到四类Canonical对象的只读标准化服务。
# - 结构：继承或实现object；类体约包含0个字段或常量、28个方法。
# - 数据变化：类定义阶段不执行隐式I/O，实例只在构造或显式方法调用时改变受控状态。
# - 实操：调用方通过该类型集中传递配置、记录、服务或结果，避免跨模块使用无约束字典。
# - 为什么这样写：强类型边界能集中维护单位、时点、主键和安全不变量，并降低供应商耦合。
class DolphinDBDailyFundsCanonicalService:
    """三张Raw表到四类Canonical对象的只读标准化服务。"""

    # 函数__init__：执行__init__对应的业务处理。
    # - 输入：adapter:ReadonlyQueryAdapter、project_root:str | Path；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型None；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    def __init__(
        self,
        adapter: ReadonlyQueryAdapter,
        *,
        project_root: str | Path,
    ) -> None:
        # 状态计算：把`Path(project_root).resolve()`的结果保存到`self.project_root`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        self.project_root = Path(project_root).resolve()
        # 状态计算：把`validate_daily_funds_service_contract(self.project_root)`的结果保存到`validation`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        validation = validate_daily_funds_service_contract(self.project_root)
        # 条件门禁：判断`validation['overall_status'] != 'PASSED_WITH_WARNINGS'`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if validation["overall_status"] != "PASSED_WITH_WARNINGS":
            # 错误阻断：抛出`DataContractError(f"TASK_017C服务合同无效：{validation['issues']}")`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
            raise DataContractError(
                f"TASK_017C服务合同无效：{validation['issues']}"
            )
        # 状态计算：把`adapter`的结果保存到`self.adapter`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        self.adapter = adapter
        # 状态计算：把`_load_service_assets(str(self.project_root))`的结果保存到`(self.config, self.mapping_path, self.dictionary_…`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        (
            self.config,
            self.mapping_path,
            self.dictionary_path,
            self.enum_path,
            self.mapping_contract,
            self.dictionary,
            self.enum_definitions,
            self.object_fields,
        ) = _load_service_assets(str(self.project_root))
        # 状态计算：把`str(self.config['database_uri'])`的结果保存到`self.database_uri`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        self.database_uri = str(self.config["database_uri"])
        # 状态计算：把`self.config['coverage']`的结果保存到`coverage`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        coverage = self.config["coverage"]
        # 状态计算：把`str(coverage['coverage_version'])`的结果保存到`self.coverage_version`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        self.coverage_version = str(coverage["coverage_version"])
        # 状态计算：把`_as_date(coverage['start_date'])`的结果保存到`self.coverage_start`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        self.coverage_start = _as_date(coverage["start_date"])
        # 状态计算：把`_as_date(coverage['end_date'])`的结果保存到`self.coverage_end`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        self.coverage_end = _as_date(coverage["end_date"])
        # 内部断言：要求`self.coverage_start is not None`成立，用于暴露开发期不变量破坏。
        # - 数据变化：断言通过时不改变业务数据，失败时中断当前测试或内部流程。
        # - 为什么这样写：把不可接受的内部状态显式化，避免错误结果继续进入报告。
        assert self.coverage_start is not None
        # 内部断言：要求`self.coverage_end is not None`成立，用于暴露开发期不变量破坏。
        # - 数据变化：断言通过时不改变业务数据，失败时中断当前测试或内部流程。
        # - 为什么这样写：把不可接受的内部状态显式化，避免错误结果继续进入报告。
        assert self.coverage_end is not None
        # 状态计算：把`dict(self.config['query_policy'])`的结果保存到`self.query_policy`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        self.query_policy = dict(self.config["query_policy"])
        # 状态计算：把`dict(self.config['dataset_profiles'])`的结果保存到`self.profiles`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        self.profiles = dict(self.config["dataset_profiles"])
        # 状态计算：把`tuple((dict(item) for item in self.config.get('known_quarantines', [])))`的结果保存到`self.known_quarantines`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        self.known_quarantines = tuple(
            dict(item) for item in self.config.get("known_quarantines", [])
        )

    # 函数service_id：执行service_id对应的业务处理。
    # - 输入：无外部业务参数；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型str；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    @property
    def service_id(self) -> str:
        # 结果返回：把`str(self.config['service_id'])`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return str(self.config["service_id"])

    # 函数service_version：执行service_version对应的业务处理。
    # - 输入：无外部业务参数；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型str；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    @property
    def service_version(self) -> str:
        # 结果返回：把`str(self.config['service_version'])`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return str(self.config["service_version"])

    # 函数mapping_version：执行mapping_version对应的业务处理。
    # - 输入：无外部业务参数；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型str；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    @property
    def mapping_version(self) -> str:
        # 结果返回：把`self.mapping_contract.contract_version`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return self.mapping_contract.contract_version

    # 函数dictionary_revision：执行dictionary_revision对应的业务处理。
    # - 输入：无外部业务参数；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型str；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    @property
    def dictionary_revision(self) -> str:
        # 结果返回：把`str(self.dictionary['dictionary_revision'])`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return str(self.dictionary["dictionary_revision"])

    # 函数dataset_profile：执行dataset_profile对应的业务处理。
    # - 输入：dataset_id:str；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型dict[str, Any]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把只读查询或来源发现步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    def dataset_profile(self, dataset_id: str) -> dict[str, Any]:
        # 异常边界：尝试执行可能失败的解析、查询、文件或类型转换步骤，并由后续处理保留错误证据。
        # - 数据变化：正常路径产生业务结果；异常路径不得静默伪造数据，应抛出、记录或隔离。
        # - 为什么这样写：把外部环境故障与业务合同失败分开，便于重试、回滚和准确验收。
        try:
            # 结果返回：把`dict(self.profiles[dataset_id])`交给调用方并结束当前函数。
            # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
            # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
            return dict(self.profiles[dataset_id])
        except KeyError as exc:
            # 错误阻断：抛出`DataContractError(f'不支持七类来源：{dataset_id}')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
            raise DataContractError(f"不支持七类来源：{dataset_id}") from exc

    # 函数available_fields：执行available_fields对应的业务处理。
    # - 输入：dataset_id:str；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型tuple[str, ...]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    def available_fields(self, dataset_id: str) -> tuple[str, ...]:
        # 状态计算：把`self.mapping_contract.datasets.get(dataset_id)`的结果保存到`dataset`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        dataset = self.mapping_contract.datasets.get(dataset_id)
        # 条件门禁：判断`dataset is None`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if dataset is None:
            # 错误阻断：抛出`DataContractError(f'不支持七类来源：{dataset_id}')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
            raise DataContractError(f"不支持七类来源：{dataset_id}")
        # 结果返回：把`tuple((str(item['target']) for item in dataset['mappings']))`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return tuple(str(item["target"]) for item in dataset["mappings"])

    # 函数_date_literal：执行_date_literal对应的业务处理。
    # - 输入：value:date；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型str；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    @staticmethod
    def _date_literal(value: date) -> str:
        # 结果返回：把`value.strftime('%Y.%m.%d')`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return value.strftime("%Y.%m.%d")

    # 函数_symbol_vector：执行_symbol_vector对应的业务处理。
    # - 输入：values:Sequence[str]；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型str；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    @staticmethod
    def _symbol_vector(values: Sequence[str]) -> str:
        # 结果返回：把`'symbol([' + ','.join((f'"{value}"' for value in values)) + '])'`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return "symbol([" + ",".join(f'"{value}"' for value in values) + "])"

    # 函数_symbol_literal：执行_symbol_literal对应的业务处理。
    # - 输入：value:str；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型str；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    @staticmethod
    def _symbol_literal(value: str) -> str:
        # 条件门禁：判断`not _DATASET_ID_PATTERN.fullmatch(value)`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if not _DATASET_ID_PATTERN.fullmatch(value):
            # 错误阻断：抛出`DataContractError('不安全的dataset_id。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
            raise DataContractError("不安全的dataset_id。")
        # 结果返回：把`f'`{value}'`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return f"`{value}"

    # 函数_validate_request：执行_validate_request对应的业务处理。
    # - 输入：request:DailyFundsReadRequest；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型None；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把合同、数据质量或安全门禁校验步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    def _validate_request(self, request: DailyFundsReadRequest) -> None:
        # 状态计算：把`self.dataset_profile(request.dataset_id)`的结果保存到`profile`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        profile = self.dataset_profile(request.dataset_id)
        # 条件门禁：判断`len(request.entity_ids) > int(self.query_policy['max_entity_ids'])`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if len(request.entity_ids) > int(self.query_policy["max_entity_ids"]):
            # 错误阻断：抛出`DataContractError('一次查询实体数超过服务上限。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
            raise DataContractError("一次查询实体数超过服务上限。")
        # 条件门禁：判断`request.limit_per_entity > int(self.query_policy['max_limit_per_entity'])`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if request.limit_per_entity > int(
            self.query_policy["max_limit_per_entity"]
        ):
            # 错误阻断：抛出`DataContractError('limit_per_entity超过服务上限。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
            raise DataContractError("limit_per_entity超过服务上限。")
        # 条件门禁：判断`request.start_date < self.coverage_start`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if request.start_date < self.coverage_start:
            # 错误阻断：抛出`DataContractError(f'请求开始日期早于七类Raw覆盖起点：{request.start_date} < {self.coverage_start}')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
            raise DataContractError(
                "请求开始日期早于七类Raw覆盖起点："
                f"{request.start_date} < {self.coverage_start}"
            )
        # 条件门禁：判断`request.end_date > self.coverage_end`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if request.end_date > self.coverage_end:
            # 错误阻断：抛出`DataContractError(f'请求结束日期晚于七类Raw覆盖终点：{request.end_date} > {self.coverage_end}')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
            raise DataContractError(
                "请求结束日期晚于七类Raw覆盖终点："
                f"{request.end_date} > {self.coverage_end}"
            )
        # 条件门禁：判断`profile['selector_mode'] == 'INSTRUMENT_ID'`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if profile["selector_mode"] == "INSTRUMENT_ID":
            # 状态计算：把`[value for value in request.entity_ids if not _INSTRUMENT_ID_PATTERN.fullmatch(value)]`的结果保存到`invalid`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            invalid = [
                value
                for value in request.entity_ids
                if not _INSTRUMENT_ID_PATTERN.fullmatch(value)
            ]
            # 条件门禁：判断`invalid`，条件成立时进入对应的数据、安全或异常处理分支。
            # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
            # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
            if invalid:
                # 错误阻断：抛出`DataContractError(f'证券型来源只接受6位代码：{invalid}')`并停止当前正常路径。
                # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
                # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
                raise DataContractError(
                    f"证券型来源只接受6位代码：{invalid}"
                )

    # 函数_selected_raw_fields：执行_selected_raw_fields对应的业务处理。
    # - 输入：dataset_id:str；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型tuple[str, ...]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    def _selected_raw_fields(self, dataset_id: str) -> tuple[str, ...]:
        # 状态计算：把`self.mapping_contract.datasets[dataset_id]`的结果保存到`dataset`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        dataset = self.mapping_contract.datasets[dataset_id]
        # 状态计算：把`set(SOURCE_EVIDENCE_FIELDS)`的结果保存到`fields`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        fields: set[str] = set(SOURCE_EVIDENCE_FIELDS)
        # 状态计算：把`self.profiles[dataset_id]`的结果保存到`profile`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        profile = self.profiles[dataset_id]
        # 显式调用：执行`fields.add(str(profile['raw_entity_field']))`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
        # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
        # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
        fields.add(str(profile["raw_entity_field"]))
        # 循环处理：逐项遍历`dataset['mappings']`，把当前元素绑定到`mapping`。
        # - 数据变化：每轮只处理一个来源记录、字段、文件或证据项，并显式累计到局部集合或输出对象。
        # - 为什么这样写：逐项处理便于保留行级血缘、隔离单项异常，并控制16GB单机上的峰值内存。
        for mapping in dataset["mappings"]:
            # 显式调用：执行`fields.update(_mapping_source_fields(mapping))`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
            # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
            # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
            fields.update(_mapping_source_fields(mapping))
        # 显式调用：执行`fields.update((str(item) for item in dataset.get('source_extensions', [])))`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
        # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
        # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
        fields.update(str(item) for item in dataset.get("source_extensions", []))
        # 状态计算：把`RAW_FIELD_CATALOG[str(dataset['family'])]`的结果保存到`raw_catalog`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        raw_catalog = RAW_FIELD_CATALOG[str(dataset["family"])]
        # 状态计算：把`sorted(fields - raw_catalog)`的结果保存到`unknown`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        unknown = sorted(fields - raw_catalog)
        # 条件门禁：判断`unknown`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if unknown:
            # 错误阻断：抛出`DataContractError(f'服务请求了Raw表不存在的字段：{dataset_id} {unknown}')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
            raise DataContractError(
                f"服务请求了Raw表不存在的字段：{dataset_id} {unknown}"
            )
        # 结果返回：把`tuple(sorted(fields))`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return tuple(sorted(fields))

    # 函数_build_query：执行_build_query对应的业务处理。
    # - 输入：request:DailyFundsReadRequest；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型str；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把只读查询或来源发现步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    def _build_query(self, request: DailyFundsReadRequest) -> str:
        # 状态计算：把`self.profiles[request.dataset_id]`的结果保存到`profile`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        profile = self.profiles[request.dataset_id]
        # 状态计算：把`str(profile['source_table'])`的结果保存到`table_name`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        table_name = str(profile["source_table"])
        # 条件门禁：判断`not _IDENTIFIER_PATTERN.fullmatch(table_name)`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if not _IDENTIFIER_PATTERN.fullmatch(table_name):
            # 错误阻断：抛出`DataContractError('source_table格式不合法。')`并停止当前正常路径。
            # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
            # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
            raise DataContractError("source_table格式不合法。")
        # 状态计算：把`', '.join(self._selected_raw_fields(request.dataset_id))`的结果保存到`fields`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        fields = ", ".join(self._selected_raw_fields(request.dataset_id))
        # 状态计算：把`[f'dataset_id={self._symbol_literal(request.dataset_id)}', f'snapshot_date>={self._date_literal(req…`的结果保存到`where_parts`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        where_parts = [
            f"dataset_id={self._symbol_literal(request.dataset_id)}",
            f"snapshot_date>={self._date_literal(request.start_date)}",
            f"snapshot_date<={self._date_literal(request.end_date)}",
        ]
        # 条件门禁：判断`profile['selector_mode'] == 'INSTRUMENT_ID'`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if profile["selector_mode"] == "INSTRUMENT_ID":
            # 显式调用：执行`where_parts.append('instrument_id in ' + self._symbol_vector(request.entity_ids))`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
            # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
            # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
            where_parts.append(
                "instrument_id in "
                + self._symbol_vector(request.entity_ids)
            )
        # 状态计算：把`int(self.query_policy['max_raw_rows_per_request'])`的结果保存到`max_rows`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        max_rows = int(self.query_policy["max_raw_rows_per_request"])
        # 结果返回：把`f'select top {max_rows} {fields} from loadTable("{self.database_uri}", `{table_name}) where ' + ' and '.join(where_part…`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return (
            f"select top {max_rows} {fields} "
            f'from loadTable("{self.database_uri}", `{table_name}) '
            "where "
            + " and ".join(where_parts)
            + " order by snapshot_date, source_row_number"
        )

    # 函数_raw_entity_identity：执行_raw_entity_identity对应的业务处理。
    # - 输入：dataset_id:str、row:Mapping[str, Any]；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型tuple[str | None, str | None]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    def _raw_entity_identity(
        self,
        dataset_id: str,
        row: Mapping[str, Any],
    ) -> tuple[str | None, str | None]:
        # 状态计算：把`self.profiles[dataset_id]`的结果保存到`profile`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        profile = self.profiles[dataset_id]
        # 条件门禁：判断`profile['selector_mode'] == 'INSTRUMENT_ID'`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if profile["selector_mode"] == "INSTRUMENT_ID":
            # 状态计算：把`_clean_text(row.get('instrument_id'))`的结果保存到`instrument_id`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            instrument_id = _clean_text(row.get("instrument_id"))
            # 结果返回：把`(instrument_id, instrument_id)`交给调用方并结束当前函数。
            # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
            # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
            return instrument_id, instrument_id
        # 状态计算：把`_clean_text(row.get('node_name_raw'))`的结果保存到`node_name`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        node_name = _clean_text(row.get("node_name_raw"))
        # 状态计算：把`provisional_node_id(row.get('classification_type'), node_name)`的结果保存到`node_id`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        node_id = provisional_node_id(
            row.get("classification_type"),
            node_name,
        )
        # 结果返回：把`(node_name, node_id)`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return node_name, node_id

    # 函数_filter_entity_rows：执行_filter_entity_rows对应的业务处理。
    # - 输入：request:DailyFundsReadRequest、rows:Sequence[dict[str, Any]]；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型tuple[list[dict[str, Any]], set[str]]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    def _filter_entity_rows(
        self,
        request: DailyFundsReadRequest,
        rows: Sequence[dict[str, Any]],
    ) -> tuple[list[dict[str, Any]], set[str]]:
        # 状态计算：把`set(request.entity_ids)`的结果保存到`requested`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        requested = set(request.entity_ids)
        # 状态计算：把`[]`的结果保存到`selected`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        selected: list[dict[str, Any]] = []
        # 状态计算：把`set()`的结果保存到`matched`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        matched: set[str] = set()
        # 循环处理：逐项遍历`rows`，把当前元素绑定到`row`。
        # - 数据变化：每轮只处理一个来源记录、字段、文件或证据项，并显式累计到局部集合或输出对象。
        # - 为什么这样写：逐项处理便于保留行级血缘、隔离单项异常，并控制16GB单机上的峰值内存。
        for row in rows:
            # 状态计算：把`self._raw_entity_identity(request.dataset_id, row)`的结果保存到`(name_or_id, provisional_id)`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            name_or_id, provisional_id = self._raw_entity_identity(
                request.dataset_id,
                row,
            )
            # 状态计算：把`{value for value in (name_or_id, provisional_id) if value}`的结果保存到`candidates`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            candidates = {value for value in (name_or_id, provisional_id) if value}
            # 状态计算：把`requested & candidates`的结果保存到`intersection`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            intersection = requested & candidates
            # 条件门禁：判断`not intersection`，条件成立时进入对应的数据、安全或异常处理分支。
            # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
            # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
            if not intersection:
                # 控制流：跳过本轮剩余步骤，使循环或占位分支按既定合同继续。
                # - 数据变化：本语句不直接改变业务记录，只调整当前执行路径。
                # - 为什么这样写：显式控制流比隐式嵌套更容易检查边界和异常处理。
                continue
            # 显式调用：执行`matched.update(intersection)`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
            # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
            # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
            matched.update(intersection)
            # 显式调用：执行`selected.append(row)`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
            # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
            # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
            selected.append(row)
        # 结果返回：把`(selected, matched)`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return selected, matched

    # 函数_apply_transform：执行_apply_transform对应的业务处理。
    # - 输入：transform:str、source_fields:tuple[str, ...]、row:Mapping[str, Any]、target_field:str；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型Any；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把对象构造、字段映射或标准化转换步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    def _apply_transform(
        self,
        *,
        transform: str,
        source_fields: tuple[str, ...],
        row: Mapping[str, Any],
        target_field: str,
    ) -> Any:
        # 状态计算：把`[row.get(field_name) for field_name in source_fields]`的结果保存到`values`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        values = [row.get(field_name) for field_name in source_fields]
        # 条件门禁：判断`transform in {'identity', 'percent_points_identity'}`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if transform in {"identity", "percent_points_identity"}:
            # 结果返回：把`values[0] if values else None`交给调用方并结束当前函数。
            # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
            # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
            return values[0] if values else None
        # 条件门禁：判断`transform == 'multiply_100'`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if transform == "multiply_100":
            # 状态计算：把`_as_float(values[0] if values else None)`的结果保存到`number`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            number = _as_float(values[0] if values else None)
            # 结果返回：把`None if number is None else number * 100.0`交给调用方并结束当前函数。
            # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
            # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
            return None if number is None else number * 100.0
        # 条件门禁：判断`transform == 'divide_100'`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if transform == "divide_100":
            # 状态计算：把`_as_float(values[0] if values else None)`的结果保存到`number`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            number = _as_float(values[0] if values else None)
            # 结果返回：把`None if number is None else number / 100.0`交给调用方并结束当前函数。
            # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
            # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
            return None if number is None else number / 100.0
        # 条件门禁：判断`transform == 'normalized_enum'`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if transform == "normalized_enum":
            # 状态计算：把`_clean_text(values[0] if values else None)`的结果保存到`text`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            text = _clean_text(values[0] if values else None)
            # 结果返回：把`None if text is None else text.upper()`交给调用方并结束当前函数。
            # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
            # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
            return None if text is None else text.upper()
        # 条件门禁：判断`transform == 'provisional_hash_id'`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if transform == "provisional_hash_id":
            # 结果返回：把`provisional_node_id(row.get('classification_type'), values[0] if values else None)`交给调用方并结束当前函数。
            # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
            # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
            return provisional_node_id(
                row.get("classification_type"),
                values[0] if values else None,
            )
        # 条件门禁：判断`transform == 'sum_nullable'`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if transform == "sum_nullable":
            # 状态计算：把`[_as_float(value) for value in values]`的结果保存到`numbers`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            numbers = [_as_float(value) for value in values]
            # 状态计算：把`[value for value in numbers if value is not None]`的结果保存到`present`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            present = [value for value in numbers if value is not None]
            # 结果返回：把`None if not present else sum(present)`交给调用方并结束当前函数。
            # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
            # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
            return None if not present else sum(present)
        # 条件门禁：判断`transform.startswith('constant_')`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if transform.startswith("constant_"):
            # 结果返回：把`transform[len('constant_'):]`交给调用方并结束当前函数。
            # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
            # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
            return transform[len("constant_") :]
        # 条件门禁：判断`transform in {'unavailable', 'unresolved_from_name_only', 'no_safe_exact_value'}`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if transform in {
            "unavailable",
            "unresolved_from_name_only",
            "no_safe_exact_value",
        }:
            # 结果返回：把`None`交给调用方并结束当前函数。
            # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
            # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
            return None
        # 错误阻断：抛出`DataContractError(f'未实现的Canonical转换：{target_field}/{transform}')`并停止当前正常路径。
        # - 数据变化：不产生正常返回值，调用方必须捕获异常或让当前任务失败。
        # - 为什么这样写：合同、时点、数据质量或安全边界被破坏时立即失败，比静默修正更可靠。
        raise DataContractError(
            f"未实现的Canonical转换：{target_field}/{transform}"
        )

    # 函数_coerce_value：执行_coerce_value对应的业务处理。
    # - 输入：value:Any、field_definition:Mapping[str, Any]；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型Any；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    def _coerce_value(
        self,
        value: Any,
        field_definition: Mapping[str, Any],
    ) -> Any:
        # 条件门禁：判断`_is_missing(value)`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if _is_missing(value):
            # 结果返回：把`None`交给调用方并结束当前函数。
            # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
            # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
            return None
        # 状态计算：把`str(field_definition.get('data_type', ''))`的结果保存到`data_type`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        data_type = str(field_definition.get("data_type", ""))
        # 条件门禁：判断`data_type == 'DATE'`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if data_type == "DATE":
            # 结果返回：把`_as_date(value)`交给调用方并结束当前函数。
            # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
            # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
            return _as_date(value)
        # 条件门禁：判断`data_type == 'TIMESTAMP'`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if data_type == "TIMESTAMP":
            # 结果返回：把`_as_datetime(value)`交给调用方并结束当前函数。
            # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
            # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
            return _as_datetime(value)
        # 条件门禁：判断`data_type in {'INT', 'LONG'}`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if data_type in {"INT", "LONG"}:
            # 结果返回：把`_as_integral(value)`交给调用方并结束当前函数。
            # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
            # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
            return _as_integral(value)
        # 条件门禁：判断`data_type in {'DOUBLE', 'DECIMAL'}`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if data_type in {"DOUBLE", "DECIMAL"}:
            # 结果返回：把`_as_float(value)`交给调用方并结束当前函数。
            # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
            # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
            return _as_float(value)
        # 条件门禁：判断`data_type == 'BOOL'`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if data_type == "BOOL":
            # 条件门禁：判断`isinstance(value, bool)`，条件成立时进入对应的数据、安全或异常处理分支。
            # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
            # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
            if isinstance(value, bool):
                # 结果返回：把`value`交给调用方并结束当前函数。
                # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
                # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
                return value
            # 状态计算：把`str(value).strip().lower()`的结果保存到`text`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            text = str(value).strip().lower()
            # 条件门禁：判断`text in {'true', '1', 'yes'}`，条件成立时进入对应的数据、安全或异常处理分支。
            # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
            # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
            if text in {"true", "1", "yes"}:
                # 结果返回：把`True`交给调用方并结束当前函数。
                # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
                # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
                return True
            # 条件门禁：判断`text in {'false', '0', 'no'}`，条件成立时进入对应的数据、安全或异常处理分支。
            # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
            # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
            if text in {"false", "0", "no"}:
                # 结果返回：把`False`交给调用方并结束当前函数。
                # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
                # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
                return False
            # 结果返回：把`None`交给调用方并结束当前函数。
            # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
            # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
            return None
        # 条件门禁：判断`data_type == 'STRING'`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if data_type == "STRING":
            # 结果返回：把`_clean_text(value)`交给调用方并结束当前函数。
            # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
            # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
            return _clean_text(value)
        # 结果返回：把`_python_scalar(value)`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return _python_scalar(value)

    # 函数_source_record_id：执行_source_record_id对应的业务处理。
    # - 输入：dataset_id:str、row:Mapping[str, Any]；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型str；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    def _source_record_id(
        self,
        dataset_id: str,
        row: Mapping[str, Any],
    ) -> str:
        # 状态计算：把`_clean_text(row.get('source_file_sha256')) or 'NOHASH'`的结果保存到`source_hash`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        source_hash = _clean_text(row.get("source_file_sha256")) or "NOHASH"
        # 状态计算：把`_as_integral(row.get('source_row_number'))`的结果保存到`row_number`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        row_number = _as_integral(row.get("source_row_number"))
        # 结果返回：把`f'{dataset_id}:{source_hash}:{row_number or 0}'`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return f"{dataset_id}:{source_hash}:{row_number or 0}"

    # 函数_lineage：执行_lineage对应的业务处理。
    # - 输入：dataset_id:str、source_record_id:str、canonical_object:str、mapping:Mapping[str, Any]；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型dict[str, Any]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    def _lineage(
        self,
        *,
        dataset_id: str,
        source_record_id: str,
        canonical_object: str,
        mapping: Mapping[str, Any],
    ) -> dict[str, Any]:
        # 结果返回：把`{'dataset_id': dataset_id, 'source_table': self.profiles[dataset_id]['source_table'], 'source_record_id': source_record…`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return {
            "dataset_id": dataset_id,
            "source_table": self.profiles[dataset_id]["source_table"],
            "source_record_id": source_record_id,
            "target_object": canonical_object,
            "canonical_field": str(mapping["target"]),
            "source_fields": list(_mapping_source_fields(mapping)),
            "transform_id": str(mapping["transform"]),
            "semantic_status": str(mapping["status"]),
            "mapping_version": self.mapping_version,
            "dictionary_revision": self.dictionary_revision,
        }

    # 函数_source_extensions：执行_source_extensions对应的业务处理。
    # - 输入：dataset_id:str、row:Mapping[str, Any]；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型dict[str, Any]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    def _source_extensions(
        self,
        dataset_id: str,
        row: Mapping[str, Any],
    ) -> dict[str, Any]:
        # 状态计算：把`self.mapping_contract.datasets[dataset_id]`的结果保存到`dataset`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        dataset = self.mapping_contract.datasets[dataset_id]
        # 状态计算：把`tuple(dict.fromkeys([*SOURCE_EVIDENCE_FIELDS, *dataset.get('source_extensions', [])]))`的结果保存到`fields`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        fields = tuple(
            dict.fromkeys(
                [
                    *SOURCE_EVIDENCE_FIELDS,
                    *dataset.get("source_extensions", []),
                ]
            )
        )
        # 结果返回：把`{field_name: _python_scalar(row.get(field_name)) for field_name in fields}`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return {
            field_name: _python_scalar(row.get(field_name))
            for field_name in fields
        }

    # 函数_build_record：执行_build_record对应的业务处理。
    # - 输入：dataset_id:str、row:Mapping[str, Any]；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型tuple[DailyFundsCanonicalRecord | None, tuple[str, ...]]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把对象构造、字段映射或标准化转换步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    def _build_record(
        self,
        dataset_id: str,
        row: Mapping[str, Any],
    ) -> tuple[DailyFundsCanonicalRecord | None, tuple[str, ...]]:
        # 状态计算：把`self.mapping_contract.datasets[dataset_id]`的结果保存到`dataset`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        dataset = self.mapping_contract.datasets[dataset_id]
        # 状态计算：把`str(dataset['canonical_object'])`的结果保存到`canonical_object`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        canonical_object = str(dataset["canonical_object"])
        # 状态计算：把`self.object_fields[canonical_object]`的结果保存到`field_catalog`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        field_catalog = self.object_fields[canonical_object]
        # 状态计算：把`self._source_record_id(dataset_id, row)`的结果保存到`source_record_id`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        source_record_id = self._source_record_id(dataset_id, row)
        # 状态计算：把`{}`的结果保存到`values`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        values: dict[str, Any] = {}
        # 状态计算：把`list(dataset.get('quality_flags', []))`的结果保存到`quality_flags`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        quality_flags = list(dataset.get("quality_flags", []))
        # 状态计算：把`[]`的结果保存到`lineage`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        lineage: list[dict[str, Any]] = []

        # 循环处理：逐项遍历`dataset['mappings']`，把当前元素绑定到`mapping`。
        # - 数据变化：每轮只处理一个来源记录、字段、文件或证据项，并显式累计到局部集合或输出对象。
        # - 为什么这样写：逐项处理便于保留行级血缘、隔离单项异常，并控制16GB单机上的峰值内存。
        for mapping in dataset["mappings"]:
            # 状态计算：把`str(mapping['target'])`的结果保存到`target`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            target = str(mapping["target"])
            # 状态计算：把`_mapping_source_fields(mapping)`的结果保存到`source_fields`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            source_fields = _mapping_source_fields(mapping)
            # 状态计算：把`self._apply_transform(transform=str(mapping['transform']), source_fields=source_fields, row=row, ta…`的结果保存到`transformed`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            transformed = self._apply_transform(
                transform=str(mapping["transform"]),
                source_fields=source_fields,
                row=row,
                target_field=target,
            )
            # 状态计算：把`self._coerce_value(transformed, field_catalog[target])`的结果保存到`coerced`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            coerced = self._coerce_value(transformed, field_catalog[target])
            # 状态计算：把`field_catalog[target].get('enum_ref')`的结果保存到`enum_ref`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            enum_ref = field_catalog[target].get("enum_ref")
            # 条件门禁：判断`coerced is not None and enum_ref and (coerced not in self.enum_definitions[enum_ref])`，条件成立时进入对应的数据、安全或异常处理分支。
            # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
            # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
            if (
                coerced is not None
                and enum_ref
                and coerced not in self.enum_definitions[enum_ref]
            ):
                # 显式调用：执行`quality_flags.append(f'CANONICAL_ENUM_INVALID_{target.upper()}')`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
                # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
                # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
                quality_flags.append(
                    f"CANONICAL_ENUM_INVALID_{target.upper()}"
                )
                # 状态计算：把`None`的结果保存到`coerced`，供当前逻辑后续校验、转换、累计或返回。
                # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
                # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
                coerced = None
            # 条件门禁：判断`transformed is not None and coerced is None and (str(field_catalog[target].get('data_type')) in {'INT', 'LONG'})`，条件成立时进入对应的数据、安全或异常处理分支。
            # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
            # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
            if (
                transformed is not None
                and coerced is None
                and str(field_catalog[target].get("data_type"))
                in {"INT", "LONG"}
            ):
                # 显式调用：执行`quality_flags.append(f'NON_INTEGRAL_CANONICAL_{target.upper()}')`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
                # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
                # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
                quality_flags.append(
                    f"NON_INTEGRAL_CANONICAL_{target.upper()}"
                )
            # 状态计算：把`coerced`的结果保存到`values[target]`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            values[target] = coerced
            # 条件门禁：判断`mapping.get('status') == 'MAPPED_WITH_WARNING'`，条件成立时进入对应的数据、安全或异常处理分支。
            # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
            # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
            if mapping.get("status") == "MAPPED_WITH_WARNING":
                # 显式调用：执行`quality_flags.append(f'MAPPING_WARNING_{target.upper()}')`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
                # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
                # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
                quality_flags.append(f"MAPPING_WARNING_{target.upper()}")
            # 显式调用：执行`lineage.append(self._lineage(dataset_id=dataset_id, source_record_id=source_record_id, canonical_object=canonical_object, mapping=mapping))`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
            # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
            # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
            lineage.append(
                self._lineage(
                    dataset_id=dataset_id,
                    source_record_id=source_record_id,
                    canonical_object=canonical_object,
                    mapping=mapping,
                )
            )

        # 状态计算：把`_clean_text(row.get('quality_status'))`的结果保存到`source_quality`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        source_quality = _clean_text(row.get("quality_status"))
        # 条件门禁：判断`source_quality and source_quality != 'PASSED'`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if source_quality and source_quality != "PASSED":
            # 显式调用：执行`quality_flags.append(f'SOURCE_QUALITY_{source_quality.upper()}')`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
            # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
            # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
            quality_flags.append(f"SOURCE_QUALITY_{source_quality.upper()}")

        # 状态计算：把`PRIMARY_KEY_FIELDS[canonical_object]`的结果保存到`primary_fields`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        primary_fields = PRIMARY_KEY_FIELDS[canonical_object]
        # 状态计算：把`{field_name: values.get(field_name) for field_name in primary_fields}`的结果保存到`primary_key`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        primary_key = {field_name: values.get(field_name) for field_name in primary_fields}
        # 状态计算：把`[field_name for field_name, value in primary_key.items() if value is None]`的结果保存到`missing_primary`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        missing_primary = [
            field_name
            for field_name, value in primary_key.items()
            if value is None
        ]
        # 条件门禁：判断`missing_primary`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if missing_primary:
            # 结果返回：把`(None, tuple((f'RECORD_SKIPPED_PRIMARY_KEY_MISSING_{field_name.upper()}' for field_name in missing_primary)))`交给调用方并结束当前函数。
            # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
            # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
            return None, tuple(
                f"RECORD_SKIPPED_PRIMARY_KEY_MISSING_{field_name.upper()}"
                for field_name in missing_primary
            )

        # 状态计算：把`_as_date(row.get('snapshot_date'))`的结果保存到`snapshot_date`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        snapshot_date = _as_date(row.get("snapshot_date"))
        # 结果返回：把`(DailyFundsCanonicalRecord(dataset_id=dataset_id, canonical_object=canonical_object, primary_key=primary_key, values=va…`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return (
            DailyFundsCanonicalRecord(
                dataset_id=dataset_id,
                canonical_object=canonical_object,
                primary_key=primary_key,
                values=values,
                source_record_id=source_record_id,
                source_extensions=self._source_extensions(dataset_id, row),
                quality_flags=tuple(dict.fromkeys(quality_flags)),
                lineage=tuple(lineage),
                snapshot_date=snapshot_date,
                ingested_at=_as_datetime(row.get("ingested_at_utc")),
            ),
            (),
        )

    # 函数_revision_key：执行_revision_key对应的业务处理。
    # - 输入：record:DailyFundsCanonicalRecord；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型tuple[str, str]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    @staticmethod
    def _revision_key(record: DailyFundsCanonicalRecord) -> tuple[str, str]:
        # 状态计算：把`record.ingested_at`的结果保存到`value`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        value = record.ingested_at
        # 条件门禁：判断`value is None`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if value is None:
            # 状态计算：把`''`的结果保存到`timestamp`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            timestamp = ""
        # 条件门禁：判断`value.tzinfo is None`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        elif value.tzinfo is None:
            # 状态计算：把`value.isoformat(timespec='microseconds')`的结果保存到`timestamp`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            timestamp = value.isoformat(timespec="microseconds")
        else:
            # 状态计算：把`value.astimezone(timezone.utc).replace(tzinfo=None).isoformat(timespec='microseconds')`的结果保存到`timestamp`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            timestamp = (
                value.astimezone(timezone.utc)
                .replace(tzinfo=None)
                .isoformat(timespec="microseconds")
            )
        # 结果返回：把`(timestamp, record.source_record_id)`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return timestamp, record.source_record_id

    # 函数_primary_key_tuple：执行_primary_key_tuple对应的业务处理。
    # - 输入：record:DailyFundsCanonicalRecord；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型tuple[tuple[str, str], ...]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    @staticmethod
    def _primary_key_tuple(
        record: DailyFundsCanonicalRecord,
    ) -> tuple[tuple[str, str], ...]:
        # 结果返回：把`tuple(((key, str(value)) for key, value in record.primary_key.items()))`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return tuple(
            (key, str(value))
            for key, value in record.primary_key.items()
        )

    # 函数_deduplicate_revisions：执行_deduplicate_revisions对应的业务处理。
    # - 输入：records:Sequence[DailyFundsCanonicalRecord]；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型tuple[list[DailyFundsCanonicalRecord], int]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    def _deduplicate_revisions(
        self,
        records: Sequence[DailyFundsCanonicalRecord],
    ) -> tuple[list[DailyFundsCanonicalRecord], int]:
        # 状态计算：把`{}`的结果保存到`selected`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        selected: dict[
            tuple[tuple[str, str], ...],
            DailyFundsCanonicalRecord,
        ] = {}
        # 状态计算：把`0`的结果保存到`collapsed`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        collapsed = 0
        # 循环处理：逐项遍历`records`，把当前元素绑定到`record`。
        # - 数据变化：每轮只处理一个来源记录、字段、文件或证据项，并显式累计到局部集合或输出对象。
        # - 为什么这样写：逐项处理便于保留行级血缘、隔离单项异常，并控制16GB单机上的峰值内存。
        for record in records:
            # 状态计算：把`self._primary_key_tuple(record)`的结果保存到`key`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            key = self._primary_key_tuple(record)
            # 状态计算：把`selected.get(key)`的结果保存到`existing`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            existing = selected.get(key)
            # 条件门禁：判断`existing is None`，条件成立时进入对应的数据、安全或异常处理分支。
            # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
            # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
            if existing is None:
                # 状态计算：把`record`的结果保存到`selected[key]`，供当前逻辑后续校验、转换、累计或返回。
                # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
                # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
                selected[key] = record
                # 控制流：跳过本轮剩余步骤，使循环或占位分支按既定合同继续。
                # - 数据变化：本语句不直接改变业务记录，只调整当前执行路径。
                # - 为什么这样写：显式控制流比隐式嵌套更容易检查边界和异常处理。
                continue
            # 状态计算：把`1`的结果保存到`collapsed`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            collapsed += 1
            # 条件门禁：判断`self._revision_key(record) >= self._revision_key(existing)`，条件成立时进入对应的数据、安全或异常处理分支。
            # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
            # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
            if self._revision_key(record) >= self._revision_key(existing):
                # 状态计算：把`record`的结果保存到`selected[key]`，供当前逻辑后续校验、转换、累计或返回。
                # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
                # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
                selected[key] = record
        # 结果返回：把`(list(selected.values()), collapsed)`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return list(selected.values()), collapsed

    # 函数_canonical_entity_key：执行_canonical_entity_key对应的业务处理。
    # - 输入：record:DailyFundsCanonicalRecord；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型str；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    @staticmethod
    def _canonical_entity_key(record: DailyFundsCanonicalRecord) -> str:
        # 条件门禁：判断`'instrument_id' in record.primary_key`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if "instrument_id" in record.primary_key:
            # 结果返回：把`str(record.primary_key['instrument_id'])`交给调用方并结束当前函数。
            # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
            # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
            return str(record.primary_key["instrument_id"])
        # 结果返回：把`str(record.primary_key.get('node_id', ''))`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return str(record.primary_key.get("node_id", ""))

    # 函数_limit_records：执行_limit_records对应的业务处理。
    # - 输入：records:Sequence[DailyFundsCanonicalRecord]、limit_per_entity:int；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型list[DailyFundsCanonicalRecord]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    def _limit_records(
        self,
        records: Sequence[DailyFundsCanonicalRecord],
        limit_per_entity: int,
    ) -> list[DailyFundsCanonicalRecord]:
        # 状态计算：把`defaultdict(int)`的结果保存到`counts`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        counts: defaultdict[str, int] = defaultdict(int)
        # 状态计算：把`[]`的结果保存到`selected`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        selected: list[DailyFundsCanonicalRecord] = []
        # 状态计算：把`sorted(records, key=lambda record: (self._canonical_entity_key(record), str(record.snapshot_date or…`的结果保存到`ordered`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        ordered = sorted(
            records,
            key=lambda record: (
                self._canonical_entity_key(record),
                str(record.snapshot_date or ""),
                str(record.primary_key),
            ),
        )
        # 循环处理：逐项遍历`ordered`，把当前元素绑定到`record`。
        # - 数据变化：每轮只处理一个来源记录、字段、文件或证据项，并显式累计到局部集合或输出对象。
        # - 为什么这样写：逐项处理便于保留行级血缘、隔离单项异常，并控制16GB单机上的峰值内存。
        for record in ordered:
            # 状态计算：把`self._canonical_entity_key(record)`的结果保存到`entity_key`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            entity_key = self._canonical_entity_key(record)
            # 条件门禁：判断`counts[entity_key] >= limit_per_entity`，条件成立时进入对应的数据、安全或异常处理分支。
            # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
            # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
            if counts[entity_key] >= limit_per_entity:
                # 控制流：跳过本轮剩余步骤，使循环或占位分支按既定合同继续。
                # - 数据变化：本语句不直接改变业务记录，只调整当前执行路径。
                # - 为什么这样写：显式控制流比隐式嵌套更容易检查边界和异常处理。
                continue
            # 状态计算：把`1`的结果保存到`counts[entity_key]`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            counts[entity_key] += 1
            # 显式调用：执行`selected.append(record)`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
            # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
            # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
            selected.append(record)
        # 结果返回：把`selected`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return selected

    # 函数_known_quarantine_warnings：执行_known_quarantine_warnings对应的业务处理。
    # - 输入：request:DailyFundsReadRequest；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型list[str]；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把封装单一业务职责的可测试步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    def _known_quarantine_warnings(
        self,
        request: DailyFundsReadRequest,
    ) -> list[str]:
        # 状态计算：把`[]`的结果保存到`warnings`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        warnings: list[str] = []
        # 循环处理：逐项遍历`self.known_quarantines`，把当前元素绑定到`item`。
        # - 数据变化：每轮只处理一个来源记录、字段、文件或证据项，并显式累计到局部集合或输出对象。
        # - 为什么这样写：逐项处理便于保留行级血缘、隔离单项异常，并控制16GB单机上的峰值内存。
        for item in self.known_quarantines:
            # 状态计算：把`_as_date(item.get('snapshot_date'))`的结果保存到`quarantine_date`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            quarantine_date = _as_date(item.get("snapshot_date"))
            # 条件门禁：判断`item.get('dataset_id') == request.dataset_id and quarantine_date is not None and (request.start_date <= quarantine_date <= reques…`，条件成立时进入对应的数据、安全或异常处理分支。
            # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
            # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
            if (
                item.get("dataset_id") == request.dataset_id
                and quarantine_date is not None
                and request.start_date <= quarantine_date <= request.end_date
            ):
                # 显式调用：执行`warnings.append(f"KNOWN_QUARANTINED_SOURCE_DATE:{request.dataset_id}:{quarantine_date}:{item.get('reason_code')}")`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
                # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
                # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
                warnings.append(
                    "KNOWN_QUARANTINED_SOURCE_DATE:"
                    f"{request.dataset_id}:{quarantine_date}:"
                    f"{item.get('reason_code')}"
                )
        # 结果返回：把`warnings`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return warnings

    # 函数read：执行read对应的业务处理。
    # - 输入：request:DailyFundsReadRequest；参数进入函数后按当前模块合同参与校验、查询、转换或报告生成。
    # - 输出：返回类型DailyFundsStandardBatch；调用方据此继续构造标准对象、质量证据、血缘或验收结果。
    # - 数据与安全：状态只通过显式返回值、受控对象或明确依赖调用传递，不在定义阶段执行数据库操作。
    # - 为什么这样写：把只读查询或来源发现步骤封装为独立函数，便于单元测试、失败定位和未来替换数据Provider。
    def read(
        self,
        request: DailyFundsReadRequest,
    ) -> DailyFundsStandardBatch:
        # 显式调用：执行`self._validate_request(request)`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
        # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
        # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
        self._validate_request(request)
        # 状态计算：把`normalise_query_records(self.adapter.run_readonly_query(self._build_query(request)))`的结果保存到`raw_rows`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        raw_rows = normalise_query_records(
            self.adapter.run_readonly_query(self._build_query(request))
        )
        # 状态计算：把`self._filter_entity_rows(request, raw_rows)`的结果保存到`(selected_rows, matched_selectors)`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        selected_rows, matched_selectors = self._filter_entity_rows(
            request,
            raw_rows,
        )
        # 状态计算：把`[]`的结果保存到`records`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        records: list[DailyFundsCanonicalRecord] = []
        # 状态计算：把`self._known_quarantine_warnings(request)`的结果保存到`warnings`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        warnings = self._known_quarantine_warnings(request)
        # 状态计算：把`Counter()`的结果保存到`skipped_flags`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        skipped_flags: Counter[str] = Counter()

        # 循环处理：逐项遍历`selected_rows`，把当前元素绑定到`row`。
        # - 数据变化：每轮只处理一个来源记录、字段、文件或证据项，并显式累计到局部集合或输出对象。
        # - 为什么这样写：逐项处理便于保留行级血缘、隔离单项异常，并控制16GB单机上的峰值内存。
        for row in selected_rows:
            # 条件门禁：判断`_clean_text(row.get('dataset_id')) != request.dataset_id`，条件成立时进入对应的数据、安全或异常处理分支。
            # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
            # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
            if _clean_text(row.get("dataset_id")) != request.dataset_id:
                # 状态计算：把`1`的结果保存到`skipped_flags['RECORD_SKIPPED_DATASET_MISMATCH']`，供当前逻辑后续校验、转换、累计或返回。
                # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
                # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
                skipped_flags["RECORD_SKIPPED_DATASET_MISMATCH"] += 1
                # 控制流：跳过本轮剩余步骤，使循环或占位分支按既定合同继续。
                # - 数据变化：本语句不直接改变业务记录，只调整当前执行路径。
                # - 为什么这样写：显式控制流比隐式嵌套更容易检查边界和异常处理。
                continue
            # 状态计算：把`self._build_record(request.dataset_id, row)`的结果保存到`(record, skip_reasons)`，供当前逻辑后续校验、转换、累计或返回。
            # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
            # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
            record, skip_reasons = self._build_record(request.dataset_id, row)
            # 条件门禁：判断`record is None`，条件成立时进入对应的数据、安全或异常处理分支。
            # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
            # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
            if record is None:
                # 显式调用：执行`skipped_flags.update(skip_reasons)`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
                # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
                # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
                skipped_flags.update(skip_reasons)
                # 控制流：跳过本轮剩余步骤，使循环或占位分支按既定合同继续。
                # - 数据变化：本语句不直接改变业务记录，只调整当前执行路径。
                # - 为什么这样写：显式控制流比隐式嵌套更容易检查边界和异常处理。
                continue
            # 显式调用：执行`records.append(record)`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
            # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
            # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
            records.append(record)

        # 状态计算：把`self._deduplicate_revisions(records)`的结果保存到`(deduplicated, collapsed)`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        deduplicated, collapsed = self._deduplicate_revisions(records)
        # 状态计算：把`self._limit_records(deduplicated, request.limit_per_entity)`的结果保存到`limited`，供当前逻辑后续校验、转换、累计或返回。
        # - 数据变化：赋值只更新当前作用域中的显式变量；具体类型、形状、单位和空值语义由右侧表达式及上游合同决定。
        # - 为什么这样写：为中间结果命名可以保留数据流和异常定位点，避免把多步金融语义压缩成不可审计表达式。
        limited = self._limit_records(deduplicated, request.limit_per_entity)
        # 循环处理：逐项遍历`request.entity_ids`，把当前元素绑定到`selector`。
        # - 数据变化：每轮只处理一个来源记录、字段、文件或证据项，并显式累计到局部集合或输出对象。
        # - 为什么这样写：逐项处理便于保留行级血缘、隔离单项异常，并控制16GB单机上的峰值内存。
        for selector in request.entity_ids:
            # 条件门禁：判断`selector not in matched_selectors`，条件成立时进入对应的数据、安全或异常处理分支。
            # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
            # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
            if selector not in matched_selectors:
                # 显式调用：执行`warnings.append(f'NO_DATA_FOR_ENTITY:{selector}')`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
                # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
                # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
                warnings.append(f"NO_DATA_FOR_ENTITY:{selector}")
        # 条件门禁：判断`collapsed`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if collapsed:
            # 显式调用：执行`warnings.append(f'COLLAPSED_RAW_REVISIONS:{collapsed}')`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
            # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
            # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
            warnings.append(f"COLLAPSED_RAW_REVISIONS:{collapsed}")
        # 条件门禁：判断`len(raw_rows) >= int(self.query_policy['max_raw_rows_per_request'])`，条件成立时进入对应的数据、安全或异常处理分支。
        # - 数据变化：条件本身只产生布尔结果；分支体内的显式赋值、返回、异常或I/O才会改变状态。
        # - 为什么这样写：尽早分流缺失、越界、过期或不安全状态，防止错误数据继续传播到下游。
        if len(raw_rows) >= int(self.query_policy["max_raw_rows_per_request"]):
            # 显式调用：执行`warnings.append('QUERY_REACHED_RAW_ROW_CAP')`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
            # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
            # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
            warnings.append("QUERY_REACHED_RAW_ROW_CAP")
        # 循环处理：逐项遍历`sorted(skipped_flags.items())`，把当前元素绑定到`(flag, count)`。
        # - 数据变化：每轮只处理一个来源记录、字段、文件或证据项，并显式累计到局部集合或输出对象。
        # - 为什么这样写：逐项处理便于保留行级血缘、隔离单项异常，并控制16GB单机上的峰值内存。
        for flag, count in sorted(skipped_flags.items()):
            # 显式调用：执行`warnings.append(f'{flag}:{count}')`以触发当前步骤所需的校验、累计、日志、查询或受控写入。
            # - 数据变化：副作用只来自被调用API的公开合同；数据库或文件变化必须由调用名称、模式和上游门禁明确授权。
            # - 为什么这样写：把副作用保留为独立语句，便于测试替换、错误定位和安全审计。
            warnings.append(f"{flag}:{count}")

        # 结果返回：把`DailyFundsStandardBatch(dataset_id=request.dataset_id, canonical_object=str(self.mapping_contract.datasets[request.data…`交给调用方并结束当前函数。
        # - 数据变化：返回值可能包含标准对象、证据、报告或状态；局部变量随调用结束释放。
        # - 为什么这样写：显式返回点让调用方明确获得的数据类型、状态和控制流终点。
        return DailyFundsStandardBatch(
            dataset_id=request.dataset_id,
            canonical_object=str(
                self.mapping_contract.datasets[request.dataset_id][
                    "canonical_object"
                ]
            ),
            coverage_version=self.coverage_version,
            mapping_version=self.mapping_version,
            dictionary_revision=self.dictionary_revision,
            scanned_source_row_count=len(raw_rows),
            source_row_count=len(selected_rows),
            records=tuple(limited),
            warnings=tuple(dict.fromkeys(warnings)),
        )
