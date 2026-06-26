# A股量化投资辅助操作系统统一字段字典

> 本字典是多源数据统一语言、CWMS变量宇宙、研究实验治理和未来执行安全的共同标准。

- 字典修订：`0.6.0`
- 状态：`official_institutional_research_and_execution_governance`
- 领域数量：**46**
- 字段总数：**1235**
- 当前核心字段：**744**
- 近期字段：**50**
- 远期预留字段：**441**

## 一、机构化研究和执行治理

- 正式研究必须登记实验ID、假设、版本、时间切分、结果和失败原因。
- 因子、模型和策略通过统一生命周期晋级。
- 策略不得直接向券商发单。
- 自动交易必须具有交易前风控、幂等、状态机、停机、核对和回滚。

## 二、领域目录

### 1. 通用元数据（`common`）

所有标准对象可复用的来源、时间、质量和追溯字段

- 标准对象：`CommonRecord`
- 字段数量：36

| 标准字段 | 中文名 | 类型 | 单位 | 阶段 | 定义 |
|---|---|---|---|---|---|
| `record_id` | 记录唯一标识 | `STRING` |  | `core` | 平台内部唯一记录ID |
| `object_type` | 对象类型 | `STRING` |  | `core` | 该记录所属标准对象类型 |
| `data_status` | 数据状态 | `STRING` |  | `core` | VALID/MISSING/DELAYED/PARTIAL/SUSPECT/INVALID/NOT_APPLICABLE |
| `quality_flags` | 质量标记集合 | `STRING[]` |  | `core` | 可同时记录多个质量问题代码 |
| `is_active` | 是否有效 | `BOOL` |  | `core` | 当前记录是否在有效区间内 |
| `event_time` | 事件实际发生时间 | `TIMESTAMP` |  | `core` | 事件实际发生时间 |
| `observed_at` | 被观测时间 | `TIMESTAMP` |  | `core` | 被观测时间 |
| `published_at` | 正式发布时间 | `TIMESTAMP` |  | `core` | 正式发布时间 |
| `available_at` | 系统可用于决策时间 | `TIMESTAMP` |  | `core` | 历史研究与生产决策的强制可见性时间 |
| `effective_from` | 生效起始时间 | `TIMESTAMP` |  | `core` | 生效起始时间 |
| `effective_to` | 生效结束时间 | `TIMESTAMP` |  | `core` | 生效结束时间 |
| `ingested_at` | 入库时间 | `TIMESTAMP` |  | `core` | 入库时间 |
| `created_at` | 平台记录创建时间 | `TIMESTAMP` |  | `core` | 平台记录创建时间 |
| `updated_at` | 平台记录更新时间 | `TIMESTAMP` |  | `core` | 平台记录更新时间 |
| `source_system` | 来源系统 | `STRING` |  | `core` | 来源系统 |
| `source_dataset` | 来源数据集 | `STRING` |  | `core` | 来源数据集 |
| `source_table` | 来源表或文件 | `STRING` |  | `core` | 来源表或文件 |
| `source_field` | 来源字段 | `STRING` |  | `core` | 来源字段 |
| `source_record_id` | 来源记录标识 | `STRING` |  | `core` | 来源记录标识 |
| `source_uri` | 来源链接或文件位置 | `STRING` |  | `core` | 来源链接或文件位置 |
| `source_license_tag` | 来源许可标签 | `STRING` |  | `core` | 来源许可标签 |
| `source_confidence_score` | 来源可信度评分 | `DOUBLE` | 0-1 | `core` | 来源可信度评分 |
| `transform_rule` | 标准化转换规则 | `STRING` |  | `core` | 标准化转换规则 |
| `dictionary_revision` | 字段字典修订号 | `STRING` |  | `core` | 轻量字段定义修订标识，不代表复杂企业版本体系 |
| `notes` | 备注 | `STRING` |  | `core` | 备注 |
| `data_origin_code` | 数据值来源性质 | `STRING` |  | `core` | 区分真实观测、报告披露、人工输入、场景假设、专家评估、代理估计、因果推导、隐状态或合成生成 |
| `value_confidence_score` | 数值置信度 | `DOUBLE` | 0-1 | `core` | 该具体字段值的可信程度，与来源系统总体可信度分开 |
| `uncertainty_lower_numeric` | 数值不确定性下界 | `DOUBLE` |  | `core` | 同一单位下的估计或场景区间下界 |
| `uncertainty_upper_numeric` | 数值不确定性上界 | `DOUBLE` |  | `core` | 同一单位下的估计或场景区间上界 |
| `simulation_run_id` | 仿真运行ID | `STRING` |  | `future_reserved` | 关联因果市场仿真运行；真实数据可为空 |
| `scenario_id` | 仿真场景ID | `STRING` |  | `future_reserved` | 关联场景目录中的场景 |
| `causal_trace_id` | 因果追溯ID | `STRING` |  | `future_reserved` | 追溯该值由哪些变量和规则推导产生 |
| `generator_version` | 生成器版本 | `STRING` |  | `future_reserved` | 产生合成或推导值的生成器版本 |
| `rule_version` | 规则版本 | `STRING` |  | `future_reserved` | 适用的因果、交易制度或仿真规则版本 |
| `random_seed` | 随机种子 | `LONG` |  | `future_reserved` | 确保合成变量和行情路径可复现 |
| `configuration_hash` | 配置哈希 | `STRING` |  | `future_reserved` | 仿真参数、场景和规则配置的内容哈希 |

### 2. 证券主数据（`instrument`）

证券、公司和交易属性的统一身份层

- 标准对象：`Instrument`
- 字段数量：22

| 标准字段 | 中文名 | 类型 | 单位 | 阶段 | 定义 |
|---|---|---|---|---|---|
| `instrument_id` | 证券统一标识 | `STRING` |  | `core` | 建议格式600000.SH、000001.SZ |
| `symbol` | 证券本地代码 | `STRING` |  | `core` | 证券本地代码 |
| `exchange_code` | 交易所代码 | `STRING` |  | `core` | 交易所代码 |
| `market_code` | 市场代码 | `STRING` |  | `core` | 市场代码 |
| `asset_class` | 资产类别 | `STRING` |  | `core` | 资产类别 |
| `security_type` | 证券类型 | `STRING` |  | `core` | 证券类型 |
| `security_subtype` | 证券子类型 | `STRING` |  | `core` | 证券子类型 |
| `instrument_name_cn` | 证券中文名称 | `STRING` |  | `core` | 证券中文名称 |
| `instrument_name_en` | 证券英文名称 | `STRING` |  | `core` | 证券英文名称 |
| `company_id` | 上市公司统一标识 | `STRING` |  | `core` | 上市公司统一标识 |
| `currency_code` | 交易币种 | `STRING` |  | `core` | ISO 4217代码，如CNY |
| `board_code` | 板块代码 | `STRING` |  | `core` | 主板、科创板、创业板、北交所等内部枚举 |
| `listing_date` | 上市日期 | `DATE` |  | `core` | 上市日期 |
| `delisting_date` | 退市日期 | `DATE` |  | `core` | 退市日期 |
| `trading_status` | 交易状态 | `STRING` |  | `core` | 交易状态 |
| `is_st` | 是否ST | `BOOL` |  | `core` | 是否ST |
| `is_new_listing` | 是否新股阶段 | `BOOL` |  | `core` | 是否新股阶段 |
| `lot_size_shares` | 最小交易单位股数 | `LONG` | shares | `core` | 最小交易单位股数 |
| `price_tick_cny` | 最小价格变动单位 | `DECIMAL` | CNY | `core` | 最小价格变动单位 |
| `price_limit_rule_code` | 涨跌幅规则代码 | `STRING` |  | `core` | 涨跌幅规则代码 |
| `isin` | 国际证券识别码 | `STRING` |  | `future_reserved` | 国际证券识别码 |
| `global_identifier` | 其他全球标识 | `STRING` |  | `future_reserved` | 其他全球标识 |

### 3. 公司主数据（`company`）

上市公司及其法定实体信息

- 标准对象：`Company`
- 字段数量：15

| 标准字段 | 中文名 | 类型 | 单位 | 阶段 | 定义 |
|---|---|---|---|---|---|
| `company_id` | 公司统一标识 | `STRING` |  | `core` | 公司统一标识 |
| `legal_name_cn` | 公司法定中文名称 | `STRING` |  | `core` | 公司法定中文名称 |
| `short_name_cn` | 公司中文简称 | `STRING` |  | `core` | 公司中文简称 |
| `legal_name_en` | 公司英文名称 | `STRING` |  | `core` | 公司英文名称 |
| `unified_social_credit_code` | 统一社会信用代码 | `STRING` |  | `core` | 统一社会信用代码 |
| `registration_country_code` | 注册国家代码 | `STRING` |  | `core` | 注册国家代码 |
| `province_code` | 省级行政区代码 | `STRING` |  | `core` | 省级行政区代码 |
| `city_code` | 城市代码 | `STRING` |  | `core` | 城市代码 |
| `established_date` | 成立日期 | `DATE` |  | `core` | 成立日期 |
| `registered_capital_cny` | 注册资本 | `DECIMAL` | CNY | `core` | 注册资本 |
| `legal_representative_name` | 法定代表人姓名 | `STRING` |  | `core` | 法定代表人姓名 |
| `business_scope_text` | 经营范围 | `STRING` |  | `core` | 经营范围 |
| `website_url` | 公司官网 | `STRING` |  | `core` | 公司官网 |
| `employee_count` | 员工人数 | `LONG` | persons | `core` | 员工人数 |
| `company_status` | 公司存续状态 | `STRING` |  | `core` | 公司存续状态 |

### 4. 交易日历（`calendar`）

交易所日历和交易时段

- 标准对象：`TradingCalendar`
- 字段数量：15

| 标准字段 | 中文名 | 类型 | 单位 | 阶段 | 定义 |
|---|---|---|---|---|---|
| `trade_date` | 交易日期 | `DATE` |  | `core` | 交易日期 |
| `exchange_code` | 交易所代码 | `STRING` |  | `core` | 交易所代码 |
| `is_trading_day` | 是否交易日 | `BOOL` |  | `core` | 是否交易日 |
| `previous_trade_date` | 上一交易日 | `DATE` |  | `core` | 上一交易日 |
| `next_trade_date` | 下一交易日 | `DATE` |  | `core` | 下一交易日 |
| `preopen_start_at` | 盘前开始时间 | `TIME` |  | `core` | 盘前开始时间 |
| `auction_start_at` | 开盘集合竞价开始时间 | `TIME` |  | `core` | 开盘集合竞价开始时间 |
| `auction_end_at` | 开盘集合竞价结束时间 | `TIME` |  | `core` | 开盘集合竞价结束时间 |
| `continuous_am_start_at` | 上午连续竞价开始时间 | `TIME` |  | `core` | 上午连续竞价开始时间 |
| `continuous_am_end_at` | 上午连续竞价结束时间 | `TIME` |  | `core` | 上午连续竞价结束时间 |
| `continuous_pm_start_at` | 下午连续竞价开始时间 | `TIME` |  | `core` | 下午连续竞价开始时间 |
| `continuous_pm_end_at` | 下午连续竞价结束时间 | `TIME` |  | `core` | 下午连续竞价结束时间 |
| `closing_auction_start_at` | 收盘集合竞价开始时间 | `TIME` |  | `core` | 收盘集合竞价开始时间 |
| `market_close_at` | 正式收盘时间 | `TIME` |  | `core` | 正式收盘时间 |
| `special_session_note` | 特殊交易时段说明 | `STRING` |  | `core` | 特殊交易时段说明 |

### 5. 日行情（`market_daily`）

A股日频原始价格、复权价格、成交和交易状态

- 标准对象：`DailyBar`
- 字段数量：34

| 标准字段 | 中文名 | 类型 | 单位 | 阶段 | 定义 |
|---|---|---|---|---|---|
| `instrument_id` | 证券统一标识 | `STRING` |  | `core` | 证券统一标识 |
| `trade_date` | 交易日期 | `DATE` |  | `core` | 交易日期 |
| `pre_close_raw_cny` | 前收盘原始价 | `DECIMAL` | CNY | `core` | 前收盘原始价 |
| `open_raw_cny` | 开盘原始价 | `DECIMAL` | CNY | `core` | 开盘原始价 |
| `high_raw_cny` | 最高原始价 | `DECIMAL` | CNY | `core` | 最高原始价 |
| `low_raw_cny` | 最低原始价 | `DECIMAL` | CNY | `core` | 最低原始价 |
| `close_raw_cny` | 收盘原始价 | `DECIMAL` | CNY | `core` | 收盘原始价 |
| `vwap_raw_cny` | 成交量加权平均原始价 | `DECIMAL` | CNY | `core` | 成交量加权平均原始价 |
| `volume_shares` | 成交量（股） | `LONG` | shares | `core` | 成交量（股） |
| `volume_lots` | 成交量（手） | `DOUBLE` | lots | `core` | 成交量（手） |
| `amount_cny` | 成交额 | `DECIMAL` | CNY | `core` | 成交额 |
| `trade_count` | 成交笔数 | `LONG` | count | `core` | 成交笔数 |
| `change_cny` | 价格变动 | `DECIMAL` | CNY | `core` | 价格变动 |
| `pct_change_pct` | 涨跌幅 | `DOUBLE` | percent_points | `core` | 涨跌幅 |
| `amplitude_pct` | 振幅 | `DOUBLE` | percent_points | `core` | 振幅 |
| `turnover_rate_pct` | 换手率 | `DOUBLE` | percent_points | `core` | 换手率 |
| `adj_factor` | 复权因子 | `DOUBLE` |  | `core` | 必须通过公司行为样例确认方向和基准 |
| `open_fwd_adj_cny` | 前复权开盘价 | `DECIMAL` | CNY | `core` | 前复权开盘价 |
| `high_fwd_adj_cny` | 前复权最高价 | `DECIMAL` | CNY | `core` | 前复权最高价 |
| `low_fwd_adj_cny` | 前复权最低价 | `DECIMAL` | CNY | `core` | 前复权最低价 |
| `close_fwd_adj_cny` | 前复权收盘价 | `DECIMAL` | CNY | `core` | 前复权收盘价 |
| `open_bwd_adj_cny` | 后复权开盘价 | `DECIMAL` | CNY | `core` | 后复权开盘价 |
| `high_bwd_adj_cny` | 后复权最高价 | `DECIMAL` | CNY | `core` | 后复权最高价 |
| `low_bwd_adj_cny` | 后复权最低价 | `DECIMAL` | CNY | `core` | 后复权最低价 |
| `close_bwd_adj_cny` | 后复权收盘价 | `DECIMAL` | CNY | `core` | 后复权收盘价 |
| `upper_limit_price_cny` | 涨停价 | `DECIMAL` | CNY | `core` | 涨停价 |
| `lower_limit_price_cny` | 跌停价 | `DECIMAL` | CNY | `core` | 跌停价 |
| `is_suspended` | 是否停牌 | `BOOL` |  | `core` | 是否停牌 |
| `is_limit_up` | 是否收于涨停 | `BOOL` |  | `core` | 是否收于涨停 |
| `is_limit_down` | 是否收于跌停 | `BOOL` |  | `core` | 是否收于跌停 |
| `is_one_price_limit_up` | 是否一字涨停 | `BOOL` |  | `core` | 是否一字涨停 |
| `is_one_price_limit_down` | 是否一字跌停 | `BOOL` |  | `core` | 是否一字跌停 |
| `float_market_cap_cny` | 流通市值 | `DECIMAL` | CNY | `core` | 流通市值 |
| `total_market_cap_cny` | 总市值 | `DECIMAL` | CNY | `core` | 总市值 |

### 6. 实时/快照行情（`market_quote`）

当前MVP仅预留，未来实时行情或券商接口使用

- 标准对象：`MarketQuote`
- 字段数量：14

| 标准字段 | 中文名 | 类型 | 单位 | 阶段 | 定义 |
|---|---|---|---|---|---|
| `instrument_id` | 证券统一标识 | `STRING` |  | `core` | 证券统一标识 |
| `quote_time` | 行情时间 | `TIMESTAMP` |  | `core` | 行情时间 |
| `last_price_cny` | 最新价 | `DECIMAL` | CNY | `core` | 最新价 |
| `open_price_cny` | 当日开盘价 | `DECIMAL` | CNY | `core` | 当日开盘价 |
| `high_price_cny` | 当日最高价 | `DECIMAL` | CNY | `core` | 当日最高价 |
| `low_price_cny` | 当日最低价 | `DECIMAL` | CNY | `core` | 当日最低价 |
| `pre_close_price_cny` | 前收盘价 | `DECIMAL` | CNY | `core` | 前收盘价 |
| `bid_price_1_cny` | 买一价 | `DECIMAL` | CNY | `future_reserved` | 买一价 |
| `bid_volume_1_shares` | 买一量 | `LONG` | shares | `future_reserved` | 买一量 |
| `ask_price_1_cny` | 卖一价 | `DECIMAL` | CNY | `future_reserved` | 卖一价 |
| `ask_volume_1_shares` | 卖一量 | `LONG` | shares | `future_reserved` | 卖一量 |
| `cumulative_volume_shares` | 当日累计成交量 | `LONG` | shares | `core` | 当日累计成交量 |
| `cumulative_amount_cny` | 当日累计成交额 | `DECIMAL` | CNY | `core` | 当日累计成交额 |
| `quote_status` | 行情状态 | `STRING` |  | `core` | 行情状态 |

### 7. 集合竞价（`auction`）

个股、行业和概念集合竞价标准字段

- 标准对象：`AuctionSnapshot`
- 字段数量：21

| 标准字段 | 中文名 | 类型 | 单位 | 阶段 | 定义 |
|---|---|---|---|---|---|
| `instrument_id` | 证券统一标识 | `STRING` |  | `core` | 证券统一标识 |
| `trade_date` | 交易日期 | `DATE` |  | `core` | 交易日期 |
| `auction_phase` | 竞价阶段 | `STRING` |  | `core` | 竞价阶段 |
| `snapshot_time` | 竞价快照时间 | `TIMESTAMP` |  | `core` | 来源明确提供的竞价快照时间；日期级来源必须为空，禁止伪造精确时间 |
| `snapshot_time_precision` | 竞价快照时间精度 | `STRING` |  | `core` | EXACT_TIMESTAMP/SECOND/MINUTE/DATE_ONLY/UNKNOWN |
| `indicative_price_cny` | 竞价指示价格 | `DECIMAL` | CNY | `core` | 竞价指示价格 |
| `final_open_price_cny` | 最终开盘价 | `DECIMAL` | CNY | `core` | 最终开盘价 |
| `matched_volume_shares` | 匹配量 | `LONG` | shares | `core` | 匹配量 |
| `matched_amount_cny` | 匹配金额 | `DECIMAL` | CNY | `core` | 匹配金额 |
| `unmatched_buy_volume_shares` | 未匹配买量 | `LONG` | shares | `core` | 未匹配买量 |
| `unmatched_sell_volume_shares` | 未匹配卖量 | `LONG` | shares | `core` | 未匹配卖量 |
| `order_imbalance_ratio` | 买卖不平衡比例 | `DOUBLE` | ratio_0_1_signed | `core` | 买卖不平衡比例 |
| `auction_volume_ratio` | 竞价量比 | `DOUBLE` | ratio | `core` | 竞价量比 |
| `auction_turnover_rate_pct` | 竞价换手率 | `DOUBLE` | percent_points | `core` | 竞价换手率 |
| `open_gap_pct` | 相对前收盘开盘缺口 | `DOUBLE` | percent_points | `core` | 相对前收盘开盘缺口 |
| `buy_cancel_ratio` | 买单撤单比例 | `DOUBLE` | ratio_0_1 | `future_reserved` | 买单撤单比例 |
| `sell_cancel_ratio` | 卖单撤单比例 | `DOUBLE` | ratio_0_1 | `future_reserved` | 卖单撤单比例 |
| `sector_confirmation_score` | 行业竞价确认分 | `DOUBLE` | score_0_100 | `core` | 行业竞价确认分 |
| `concept_confirmation_score` | 概念竞价确认分 | `DOUBLE` | score_0_100 | `core` | 概念竞价确认分 |
| `auction_signal_label` | 竞价信号标签 | `STRING` |  | `core` | 竞价信号标签 |
| `auction_confidence_score` | 竞价信号置信度 | `DOUBLE` | 0-1 | `core` | 竞价信号置信度 |

### 8. 资金流（`money_flow`）

资金流来源差异大，必须保留flow_method_code和来源口径

- 标准对象：`MoneyFlowSnapshot`
- 字段数量：17

| 标准字段 | 中文名 | 类型 | 单位 | 阶段 | 定义 |
|---|---|---|---|---|---|
| `instrument_id` | 证券统一标识 | `STRING` |  | `core` | 证券统一标识 |
| `trade_date` | 交易日期 | `DATE` |  | `core` | 交易日期 |
| `inflow_total_cny` | 总流入额 | `DECIMAL` | CNY | `core` | 总流入额 |
| `outflow_total_cny` | 总流出额 | `DECIMAL` | CNY | `core` | 总流出额 |
| `net_inflow_total_cny` | 总净流入额 | `DECIMAL` | CNY | `core` | 总净流入额 |
| `net_inflow_main_cny` | 主力净流入额 | `DECIMAL` | CNY | `core` | 主力净流入额 |
| `net_inflow_super_large_cny` | 超大单净流入额 | `DECIMAL` | CNY | `core` | 超大单净流入额 |
| `net_inflow_large_cny` | 大单净流入额 | `DECIMAL` | CNY | `core` | 大单净流入额 |
| `net_inflow_medium_cny` | 中单净流入额 | `DECIMAL` | CNY | `core` | 中单净流入额 |
| `net_inflow_small_cny` | 小单净流入额 | `DECIMAL` | CNY | `core` | 小单净流入额 |
| `active_buy_amount_cny` | 主动买入额 | `DECIMAL` | CNY | `core` | 主动买入额 |
| `active_sell_amount_cny` | 主动卖出额 | `DECIMAL` | CNY | `core` | 主动卖出额 |
| `active_buy_ratio` | 主动买入比例 | `DOUBLE` | ratio_0_1 | `core` | 主动买入比例 |
| `main_flow_ratio` | 主力净流入占成交额比例 | `DOUBLE` | ratio | `core` | 主力净流入占成交额比例 |
| `flow_persistence_days` | 资金流持续天数 | `INT` | days | `core` | 资金流持续天数 |
| `northbound_net_inflow_cny` | 北向资金净流入 | `DECIMAL` | CNY | `future_reserved` | 北向资金净流入 |
| `flow_method_code` | 资金流口径代码 | `STRING` |  | `core` | 资金流口径代码 |

### 9. 公司行为（`corporate_action`）

分红送转配股、股本变化与复权依据

- 标准对象：`CorporateAction`
- 字段数量：24

| 标准字段 | 中文名 | 类型 | 单位 | 阶段 | 定义 |
|---|---|---|---|---|---|
| `corporate_action_id` | 公司行为ID | `STRING` |  | `core` | 公司行为ID |
| `instrument_id` | 证券统一标识 | `STRING` |  | `core` | 证券统一标识 |
| `action_type` | 公司行为类型 | `STRING` |  | `core` | 公司行为类型 |
| `announcement_date` | 公告日期 | `DATE` |  | `core` | 公告日期 |
| `record_date` | 股权登记日 | `DATE` |  | `core` | 股权登记日 |
| `ex_date` | 除权除息日 | `DATE` |  | `core` | 除权除息日 |
| `payment_date` | 派息日 | `DATE` |  | `core` | 派息日 |
| `listing_date_new_shares` | 新增股份上市日 | `DATE` |  | `core` | 新增股份上市日 |
| `cash_dividend_per_share_cny` | 每股现金分红 | `DECIMAL` | CNY/share | `core` | 每股现金分红 |
| `bonus_share_ratio` | 送股比例 | `DOUBLE` | shares_per_share | `core` | 送股比例 |
| `capital_reserve_transfer_ratio` | 转增比例 | `DOUBLE` | shares_per_share | `core` | 转增比例 |
| `rights_issue_ratio` | 配股比例 | `DOUBLE` | shares_per_share | `core` | 配股比例 |
| `rights_issue_price_cny` | 配股价格 | `DECIMAL` | CNY | `core` | 配股价格 |
| `split_ratio` | 拆股比例 | `DOUBLE` |  | `core` | 拆股比例 |
| `merge_ratio` | 合股比例 | `DOUBLE` |  | `core` | 合股比例 |
| `repurchase_shares` | 回购股数 | `LONG` | shares | `core` | 回购股数 |
| `repurchase_amount_cny` | 回购金额 | `DECIMAL` | CNY | `core` | 回购金额 |
| `pre_action_total_shares` | 行为前总股本 | `LONG` | shares | `core` | 行为前总股本 |
| `post_action_total_shares` | 行为后总股本 | `LONG` | shares | `core` | 行为后总股本 |
| `pre_action_float_shares` | 行为前流通股本 | `LONG` | shares | `core` | 行为前流通股本 |
| `post_action_float_shares` | 行为后流通股本 | `LONG` | shares | `core` | 行为后流通股本 |
| `adj_factor_before` | 行为前复权因子 | `DOUBLE` |  | `core` | 行为前复权因子 |
| `adj_factor_after` | 行为后复权因子 | `DOUBLE` |  | `core` | 行为后复权因子 |
| `action_status` | 公司行为状态 | `STRING` |  | `core` | 公司行为状态 |

### 10. 基本面与财务（`fundamental`）

核心指标采用标准字段，长尾指标使用metric_code扩展，不建立无限宽表

- 标准对象：`FundamentalSnapshot`
- 字段数量：54

| 标准字段 | 中文名 | 类型 | 单位 | 阶段 | 定义 |
|---|---|---|---|---|---|
| `instrument_id` | 证券统一标识 | `STRING` |  | `core` | 证券统一标识 |
| `company_id` | 公司统一标识 | `STRING` |  | `core` | 公司统一标识 |
| `report_period` | 报告期 | `DATE` |  | `core` | 报告期 |
| `period_type` | 报告期类型 | `STRING` |  | `core` | 报告期类型 |
| `fiscal_year` | 财年 | `INT` |  | `core` | 财年 |
| `fiscal_quarter` | 财季 | `INT` |  | `core` | 财季 |
| `announcement_date` | 公告日期 | `DATE` |  | `core` | 公告日期 |
| `statement_type` | 报表类型 | `STRING` |  | `core` | 报表类型 |
| `consolidation_scope` | 合并口径 | `STRING` |  | `core` | 合并口径 |
| `accounting_standard_code` | 会计准则代码 | `STRING` |  | `core` | 会计准则代码 |
| `currency_code` | 报表币种 | `STRING` |  | `core` | 报表币种 |
| `revenue_cny` | 营业收入 | `DECIMAL` | CNY | `core` | 营业收入 |
| `operating_cost_cny` | 营业成本 | `DECIMAL` | CNY | `core` | 营业成本 |
| `gross_profit_cny` | 毛利润 | `DECIMAL` | CNY | `core` | 毛利润 |
| `operating_profit_cny` | 营业利润 | `DECIMAL` | CNY | `core` | 营业利润 |
| `total_profit_cny` | 利润总额 | `DECIMAL` | CNY | `core` | 利润总额 |
| `net_profit_cny` | 净利润 | `DECIMAL` | CNY | `core` | 净利润 |
| `net_profit_parent_cny` | 归母净利润 | `DECIMAL` | CNY | `core` | 归母净利润 |
| `net_profit_excl_nonrecurring_cny` | 扣非归母净利润 | `DECIMAL` | CNY | `core` | 扣非归母净利润 |
| `total_assets_cny` | 总资产 | `DECIMAL` | CNY | `core` | 总资产 |
| `total_liabilities_cny` | 总负债 | `DECIMAL` | CNY | `core` | 总负债 |
| `total_equity_cny` | 所有者权益 | `DECIMAL` | CNY | `core` | 所有者权益 |
| `equity_parent_cny` | 归母所有者权益 | `DECIMAL` | CNY | `core` | 归母所有者权益 |
| `cash_and_equivalents_cny` | 货币资金及现金等价物 | `DECIMAL` | CNY | `core` | 货币资金及现金等价物 |
| `inventory_cny` | 存货 | `DECIMAL` | CNY | `core` | 存货 |
| `accounts_receivable_cny` | 应收账款 | `DECIMAL` | CNY | `core` | 应收账款 |
| `operating_cash_flow_cny` | 经营活动现金流净额 | `DECIMAL` | CNY | `core` | 经营活动现金流净额 |
| `investing_cash_flow_cny` | 投资活动现金流净额 | `DECIMAL` | CNY | `core` | 投资活动现金流净额 |
| `financing_cash_flow_cny` | 筹资活动现金流净额 | `DECIMAL` | CNY | `core` | 筹资活动现金流净额 |
| `basic_eps_cny` | 基本每股收益 | `DOUBLE` | CNY/share | `core` | 基本每股收益 |
| `diluted_eps_cny` | 稀释每股收益 | `DOUBLE` | CNY/share | `core` | 稀释每股收益 |
| `book_value_per_share_cny` | 每股净资产 | `DOUBLE` | CNY/share | `core` | 每股净资产 |
| `roe_pct` | 净资产收益率 | `DOUBLE` | percent_points | `core` | 净资产收益率 |
| `roa_pct` | 总资产收益率 | `DOUBLE` | percent_points | `core` | 总资产收益率 |
| `gross_margin_pct` | 毛利率 | `DOUBLE` | percent_points | `core` | 毛利率 |
| `net_margin_pct` | 净利率 | `DOUBLE` | percent_points | `core` | 净利率 |
| `debt_to_asset_pct` | 资产负债率 | `DOUBLE` | percent_points | `core` | 资产负债率 |
| `current_ratio` | 流动比率 | `DOUBLE` | ratio | `core` | 流动比率 |
| `quick_ratio` | 速动比率 | `DOUBLE` | ratio | `core` | 速动比率 |
| `inventory_turnover` | 存货周转率 | `DOUBLE` | times | `core` | 存货周转率 |
| `receivable_turnover` | 应收账款周转率 | `DOUBLE` | times | `core` | 应收账款周转率 |
| `revenue_yoy_pct` | 营业收入同比增速 | `DOUBLE` | percent_points | `core` | 营业收入同比增速 |
| `net_profit_yoy_pct` | 净利润同比增速 | `DOUBLE` | percent_points | `core` | 净利润同比增速 |
| `net_profit_parent_yoy_pct` | 归母净利润同比增速 | `DOUBLE` | percent_points | `core` | 归母净利润同比增速 |
| `operating_cash_flow_yoy_pct` | 经营现金流同比增速 | `DOUBLE` | percent_points | `core` | 经营现金流同比增速 |
| `pe_ttm` | 市盈率TTM | `DOUBLE` | times | `core` | 市盈率TTM |
| `pb_mrq` | 市净率MRQ | `DOUBLE` | times | `core` | 市净率MRQ |
| `ps_ttm` | 市销率TTM | `DOUBLE` | times | `core` | 市销率TTM |
| `dividend_yield_pct` | 股息率 | `DOUBLE` | percent_points | `core` | 股息率 |
| `metric_code` | 扩展财务指标代码 | `STRING` |  | `near_term` | 用于容纳未固化为宽表字段的财务指标 |
| `metric_value_numeric` | 扩展指标数值 | `DECIMAL` |  | `near_term` | 扩展指标数值 |
| `metric_value_text` | 扩展指标文本值 | `STRING` |  | `near_term` | 扩展指标文本值 |
| `metric_unit` | 扩展指标单位 | `STRING` |  | `near_term` | 扩展指标单位 |
| `metric_basis_code` | 扩展指标口径 | `STRING` |  | `near_term` | 如TTM/MRQ/单季/累计/合并/母公司 |

### 11. 股本与股东（`ownership`）

股本、持有人结构和质押等信息

- 标准对象：`OwnershipSnapshot`
- 字段数量：14

| 标准字段 | 中文名 | 类型 | 单位 | 阶段 | 定义 |
|---|---|---|---|---|---|
| `instrument_id` | 证券统一标识 | `STRING` |  | `core` | 证券统一标识 |
| `as_of_date` | 统计日期 | `DATE` |  | `core` | 统计日期 |
| `total_shares` | 总股本 | `LONG` | shares | `core` | 总股本 |
| `float_shares` | 流通股本 | `LONG` | shares | `core` | 流通股本 |
| `free_float_shares` | 自由流通股本 | `LONG` | shares | `core` | 自由流通股本 |
| `restricted_shares` | 限售股本 | `LONG` | shares | `core` | 限售股本 |
| `shareholder_count` | 股东户数 | `LONG` | count | `core` | 股东户数 |
| `top10_holding_pct` | 前十大股东持股比例 | `DOUBLE` | percent_points | `core` | 前十大股东持股比例 |
| `institutional_holding_pct` | 机构持股比例 | `DOUBLE` | percent_points | `core` | 机构持股比例 |
| `fund_holding_pct` | 基金持股比例 | `DOUBLE` | percent_points | `core` | 基金持股比例 |
| `northbound_holding_pct` | 北向持股比例 | `DOUBLE` | percent_points | `future_reserved` | 北向持股比例 |
| `pledged_share_pct` | 质押股份比例 | `DOUBLE` | percent_points | `core` | 质押股份比例 |
| `insider_holding_pct` | 董监高持股比例 | `DOUBLE` | percent_points | `core` | 董监高持股比例 |
| `shareholder_concentration_score` | 股权集中度评分 | `DOUBLE` | score_0_100 | `core` | 股权集中度评分 |

### 12. 行业概念指数分类（`classification`）

多套行业、概念和指数体系并存，必须带体系与历史有效区间

- 标准对象：`ClassificationMembership`
- 字段数量：15

| 标准字段 | 中文名 | 类型 | 单位 | 阶段 | 定义 |
|---|---|---|---|---|---|
| `classification_system` | 分类体系 | `STRING` |  | `core` | 如申万、中信、证监会、Wind、自定义概念 |
| `classification_version` | 分类体系版本 | `STRING` |  | `core` | 分类体系版本 |
| `classification_type` | 分类类型 | `STRING` |  | `core` | INDUSTRY/CONCEPT/INDEX/THEME/REGION |
| `node_id` | 分类节点ID | `STRING` |  | `core` | 分类节点ID |
| `node_code` | 分类节点代码 | `STRING` |  | `core` | 分类节点代码 |
| `node_name_cn` | 分类节点中文名 | `STRING` |  | `core` | 分类节点中文名 |
| `node_name_en` | 分类节点英文名 | `STRING` |  | `core` | 分类节点英文名 |
| `node_level` | 分类层级 | `INT` |  | `core` | 分类层级 |
| `parent_node_id` | 父节点ID | `STRING` |  | `core` | 父节点ID |
| `instrument_id` | 成员证券标识 | `STRING` |  | `core` | 成员证券标识 |
| `membership_weight_pct` | 成员权重 | `DOUBLE` | percent_points | `core` | 成员权重 |
| `membership_rank` | 成员排序 | `INT` |  | `core` | 成员排序 |
| `effective_from` | 成员生效时间 | `TIMESTAMP` |  | `core` | 成员生效时间 |
| `effective_to` | 成员失效时间 | `TIMESTAMP` |  | `core` | 成员失效时间 |
| `membership_reason` | 纳入原因 | `STRING` |  | `core` | 纳入原因 |

### 13. 宏观与政策（`macro_policy`）

宏观指标和政策事件的统一时间与影响字段

- 标准对象：`MacroPolicyRecord`
- 字段数量：25

| 标准字段 | 中文名 | 类型 | 单位 | 阶段 | 定义 |
|---|---|---|---|---|---|
| `series_id` | 宏观序列ID | `STRING` |  | `core` | 宏观序列ID |
| `indicator_code` | 指标代码 | `STRING` |  | `core` | 指标代码 |
| `indicator_name_cn` | 指标中文名 | `STRING` |  | `core` | 指标中文名 |
| `region_code` | 地区代码 | `STRING` |  | `core` | 地区代码 |
| `frequency_code` | 频率代码 | `STRING` |  | `core` | 频率代码 |
| `period_start_date` | 统计期开始 | `DATE` |  | `core` | 统计期开始 |
| `period_end_date` | 统计期结束 | `DATE` |  | `core` | 统计期结束 |
| `release_date` | 发布日期 | `DATE` |  | `core` | 发布日期 |
| `value_numeric` | 指标值 | `DECIMAL` |  | `core` | 指标值 |
| `unit_code` | 单位代码 | `STRING` |  | `core` | 单位代码 |
| `is_revised` | 是否修订 | `BOOL` |  | `core` | 是否修订 |
| `previous_value_numeric` | 前次公布值 | `DECIMAL` |  | `core` | 前次公布值 |
| `consensus_value_numeric` | 市场预期值 | `DECIMAL` |  | `future_reserved` | 市场预期值 |
| `surprise_value_numeric` | 超预期值 | `DECIMAL` |  | `future_reserved` | 超预期值 |
| `policy_event_id` | 政策事件ID | `STRING` |  | `core` | 政策事件ID |
| `policy_type` | 政策类型 | `STRING` |  | `core` | 政策类型 |
| `policy_issuer_id` | 发布机构ID | `STRING` |  | `core` | 发布机构ID |
| `policy_title` | 政策标题 | `STRING` |  | `core` | 政策标题 |
| `policy_direction` | 政策方向 | `STRING` |  | `core` | 政策方向 |
| `policy_strength_score` | 政策力度评分 | `DOUBLE` | score_0_100 | `core` | 政策力度评分 |
| `policy_target_text` | 政策目标 | `STRING` |  | `core` | 政策目标 |
| `beneficiary_sector_ids` | 受益行业ID集合 | `STRING[]` |  | `core` | 受益行业ID集合 |
| `adverse_sector_ids` | 不利行业ID集合 | `STRING[]` |  | `core` | 不利行业ID集合 |
| `policy_effective_date` | 政策生效日期 | `DATE` |  | `core` | 政策生效日期 |
| `policy_expiry_date` | 政策失效日期 | `DATE` |  | `core` | 政策失效日期 |

### 14. 跨资产与全球市场状态（`cross_asset_market`）

股票指数、加密货币、期货、商品、外汇、债券和房地产等跨市场观测与场景冲击变量

- 标准对象：`CrossAssetMarketSnapshot`
- 字段数量：23

| 标准字段 | 中文名 | 类型 | 单位 | 阶段 | 定义 |
|---|---|---|---|---|---|
| `cross_asset_snapshot_id` | 跨资产快照ID | `STRING` |  | `future_reserved` | 跨资产快照ID |
| `observation_time` | 观测时间 | `TIMESTAMP` |  | `future_reserved` | 观测时间 |
| `asset_class_code` | 资产类别代码 | `STRING` |  | `future_reserved` | 资产类别代码 |
| `market_code` | 市场代码 | `STRING` |  | `future_reserved` | 市场代码 |
| `instrument_id` | 基准工具或指数ID | `STRING` |  | `future_reserved` | 基准工具或指数ID |
| `country_code` | 国家代码 | `STRING` |  | `future_reserved` | 国家代码 |
| `currency_code` | 计价货币 | `STRING` |  | `future_reserved` | 计价货币 |
| `price_level` | 价格或指数点位 | `DOUBLE` |  | `future_reserved` | 价格或指数点位 |
| `return_1d_pct` | 1日涨跌幅 | `DOUBLE` | percent_points | `future_reserved` | 1日涨跌幅 |
| `return_5d_pct` | 5日涨跌幅 | `DOUBLE` | percent_points | `future_reserved` | 5日涨跌幅 |
| `return_20d_pct` | 20日涨跌幅 | `DOUBLE` | percent_points | `future_reserved` | 20日涨跌幅 |
| `volatility_20d_pct` | 20日波动率 | `DOUBLE` | percent_points | `future_reserved` | 20日波动率 |
| `drawdown_pct` | 当前回撤 | `DOUBLE` | percent_points | `future_reserved` | 当前回撤 |
| `liquidity_score` | 流动性评分 | `DOUBLE` | score_0_100 | `future_reserved` | 流动性评分 |
| `open_interest_value` | 未平仓量 | `DOUBLE` |  | `future_reserved` | 未平仓量 |
| `basis_pct` | 期现基差 | `DOUBLE` | percent_points | `future_reserved` | 期现基差 |
| `funding_rate_pct` | 资金费率 | `DOUBLE` | percent_points | `future_reserved` | 资金费率 |
| `market_regime_code` | 跨资产市场状态 | `STRING` |  | `future_reserved` | 跨资产市场状态 |
| `shock_direction_code` | 场景冲击方向 | `STRING` |  | `future_reserved` | 场景冲击方向 |
| `shock_magnitude_pct` | 场景冲击幅度 | `DOUBLE` | percent_points | `future_reserved` | 场景冲击幅度 |
| `data_origin_code` | 数据来源性质 | `STRING` |  | `future_reserved` | 数据来源性质 |
| `value_confidence_score` | 数值置信度 | `DOUBLE` | 0-1 | `future_reserved` | 数值置信度 |
| `crude_oil_price_usd_bbl` | 原油价格 | `DOUBLE` | USD_per_barrel | `future_reserved` | 国际原油或指定原油基准的美元每桶价格 |

### 15. 文档新闻公告（`document_news`）

公告、新闻、研报、政策和网页内容的统一文档头

- 标准对象：`Document`
- 字段数量：24

| 标准字段 | 中文名 | 类型 | 单位 | 阶段 | 定义 |
|---|---|---|---|---|---|
| `document_id` | 文档ID | `STRING` |  | `core` | 文档ID |
| `document_type` | 文档类型 | `STRING` |  | `core` | 文档类型 |
| `title` | 标题 | `STRING` |  | `core` | 标题 |
| `subtitle` | 副标题 | `STRING` |  | `core` | 副标题 |
| `content_text` | 正文 | `STRING` |  | `core` | 正文 |
| `summary_text` | 摘要 | `STRING` |  | `core` | 摘要 |
| `language_code` | 语言代码 | `STRING` |  | `core` | 语言代码 |
| `publisher_id` | 发布者ID | `STRING` |  | `core` | 发布者ID |
| `publisher_name` | 发布者名称 | `STRING` |  | `core` | 发布者名称 |
| `author_ids` | 作者ID集合 | `STRING[]` |  | `core` | 作者ID集合 |
| `published_at` | 发布时间 | `TIMESTAMP` |  | `core` | 发布时间 |
| `collected_at` | 采集时间 | `TIMESTAMP` |  | `core` | 采集时间 |
| `source_url` | 原文链接 | `STRING` |  | `core` | 原文链接 |
| `document_hash` | 文档哈希 | `STRING` |  | `core` | 文档哈希 |
| `duplicate_cluster_id` | 重复内容簇ID | `STRING` |  | `core` | 重复内容簇ID |
| `entity_mentions` | 实体提及集合 | `STRING[]` |  | `core` | 实体提及集合 |
| `topic_tags` | 主题标签 | `STRING[]` |  | `core` | 主题标签 |
| `event_type_codes` | 事件类型集合 | `STRING[]` |  | `core` | 事件类型集合 |
| `is_official_source` | 是否官方来源 | `BOOL` |  | `core` | 是否官方来源 |
| `is_paywalled` | 是否付费墙 | `BOOL` |  | `core` | 是否付费墙 |
| `credibility_score` | 可信度评分 | `DOUBLE` | 0-1 | `core` | 可信度评分 |
| `novelty_score` | 新颖度评分 | `DOUBLE` | 0-1 | `core` | 新颖度评分 |
| `source_reach_score` | 来源传播力评分 | `DOUBLE` | 0-1 | `core` | 来源传播力评分 |
| `correction_status` | 更正状态 | `STRING` |  | `core` | 更正状态 |

### 16. 社交帖子（`social_post`）

社交平台帖子、论坛主题和社区内容

- 标准对象：`SocialPost`
- 字段数量：24

| 标准字段 | 中文名 | 类型 | 单位 | 阶段 | 定义 |
|---|---|---|---|---|---|
| `post_id` | 帖子ID | `STRING` |  | `core` | 帖子ID |
| `platform_code` | 平台代码 | `STRING` |  | `core` | 平台代码 |
| `channel_id` | 频道或社区ID | `STRING` |  | `core` | 频道或社区ID |
| `thread_id` | 讨论线程ID | `STRING` |  | `core` | 讨论线程ID |
| `author_id_hash` | 作者匿名标识 | `STRING` |  | `core` | 作者匿名标识 |
| `author_type` | 作者类型 | `STRING` |  | `core` | 作者类型 |
| `author_follower_count` | 作者粉丝数 | `LONG` | count | `core` | 作者粉丝数 |
| `author_reputation_score` | 作者信誉分 | `DOUBLE` | score_0_100 | `core` | 作者信誉分 |
| `content_text` | 帖子正文 | `STRING` |  | `core` | 帖子正文 |
| `language_code` | 语言代码 | `STRING` |  | `core` | 语言代码 |
| `published_at` | 发布时间 | `TIMESTAMP` |  | `core` | 发布时间 |
| `collected_at` | 采集时间 | `TIMESTAMP` |  | `core` | 采集时间 |
| `view_count` | 浏览量 | `LONG` | count | `core` | 浏览量 |
| `like_count` | 点赞数 | `LONG` | count | `core` | 点赞数 |
| `share_count` | 转发数 | `LONG` | count | `core` | 转发数 |
| `reply_count` | 回复数 | `LONG` | count | `core` | 回复数 |
| `favorite_count` | 收藏数 | `LONG` | count | `core` | 收藏数 |
| `hashtag_list` | 话题标签 | `STRING[]` |  | `core` | 话题标签 |
| `entity_mentions` | 实体提及集合 | `STRING[]` |  | `core` | 实体提及集合 |
| `geo_region_code` | 地理区域代码 | `STRING` |  | `core` | 地理区域代码 |
| `is_edited` | 是否编辑过 | `BOOL` |  | `core` | 是否编辑过 |
| `is_deleted` | 是否删除 | `BOOL` |  | `core` | 是否删除 |
| `deletion_reason_code` | 删除原因代码 | `STRING` |  | `core` | 删除原因代码 |
| `media_type_codes` | 媒体类型集合 | `STRING[]` |  | `core` | 媒体类型集合 |

### 17. 评论区与内容治理（`comment_moderation`）

评论区维护、垃圾内容、机器人、操纵话术、申诉和人工审核

- 标准对象：`CommentModeration`
- 字段数量：38

| 标准字段 | 中文名 | 类型 | 单位 | 阶段 | 定义 |
|---|---|---|---|---|---|
| `comment_id` | 评论ID | `STRING` |  | `core` | 评论ID |
| `post_id` | 所属帖子ID | `STRING` |  | `core` | 所属帖子ID |
| `thread_id` | 讨论线程ID | `STRING` |  | `core` | 讨论线程ID |
| `parent_comment_id` | 父评论ID | `STRING` |  | `core` | 父评论ID |
| `root_comment_id` | 根评论ID | `STRING` |  | `core` | 根评论ID |
| `platform_code` | 平台代码 | `STRING` |  | `core` | 平台代码 |
| `author_id_hash` | 作者匿名标识 | `STRING` |  | `core` | 作者匿名标识 |
| `author_type` | 作者类型 | `STRING` |  | `core` | 作者类型 |
| `content_text` | 评论正文 | `STRING` |  | `core` | 评论正文 |
| `language_code` | 语言代码 | `STRING` |  | `core` | 语言代码 |
| `published_at` | 发布时间 | `TIMESTAMP` |  | `core` | 发布时间 |
| `collected_at` | 采集时间 | `TIMESTAMP` |  | `core` | 采集时间 |
| `like_count` | 点赞数 | `LONG` | count | `core` | 点赞数 |
| `reply_count` | 回复数 | `LONG` | count | `core` | 回复数 |
| `is_pinned` | 是否置顶 | `BOOL` |  | `core` | 是否置顶 |
| `is_deleted` | 是否删除 | `BOOL` |  | `core` | 是否删除 |
| `is_hidden` | 是否隐藏 | `BOOL` |  | `core` | 是否隐藏 |
| `moderation_status` | 审核状态 | `STRING` |  | `core` | 审核状态 |
| `moderation_action` | 审核动作 | `STRING` |  | `core` | 审核动作 |
| `moderation_reason_codes` | 审核原因集合 | `STRING[]` |  | `core` | 审核原因集合 |
| `moderator_type` | 审核者类型 | `STRING` |  | `core` | 审核者类型 |
| `moderated_at` | 审核时间 | `TIMESTAMP` |  | `core` | 审核时间 |
| `appeal_status` | 申诉状态 | `STRING` |  | `core` | 申诉状态 |
| `appeal_result` | 申诉结果 | `STRING` |  | `core` | 申诉结果 |
| `spam_score` | 垃圾信息评分 | `DOUBLE` | 0-1 | `core` | 垃圾信息评分 |
| `bot_probability` | 机器人概率 | `DOUBLE` | 0-1 | `core` | 机器人概率 |
| `toxicity_score` | 有害性评分 | `DOUBLE` | 0-1 | `core` | 有害性评分 |
| `insult_score` | 侮辱性评分 | `DOUBLE` | 0-1 | `core` | 侮辱性评分 |
| `hate_score` | 仇恨性评分 | `DOUBLE` | 0-1 | `core` | 仇恨性评分 |
| `threat_score` | 威胁性评分 | `DOUBLE` | 0-1 | `core` | 威胁性评分 |
| `rumor_probability` | 谣言概率 | `DOUBLE` | 0-1 | `core` | 谣言概率 |
| `market_manipulation_probability` | 市场操纵话术概率 | `DOUBLE` | 0-1 | `core` | 市场操纵话术概率 |
| `pump_dump_probability` | 拉抬出货话术概率 | `DOUBLE` | 0-1 | `core` | 拉抬出货话术概率 |
| `investment_solicitation_flag` | 是否涉嫌投资招揽 | `BOOL` |  | `core` | 是否涉嫌投资招揽 |
| `personal_data_risk_flag` | 是否含个人敏感信息 | `BOOL` |  | `core` | 是否含个人敏感信息 |
| `duplicate_cluster_id` | 重复评论簇ID | `STRING` |  | `core` | 重复评论簇ID |
| `coordinated_behavior_cluster_id` | 协同行为簇ID | `STRING` |  | `core` | 协同行为簇ID |
| `user_reputation_score` | 用户信誉分 | `DOUBLE` | score_0_100 | `core` | 用户信誉分 |

### 18. 舆情与叙事（`sentiment`）

情绪、立场、热度、叙事阶段和市场影响

- 标准对象：`SentimentNarrative`
- 字段数量：28

| 标准字段 | 中文名 | 类型 | 单位 | 阶段 | 定义 |
|---|---|---|---|---|---|
| `analysis_id` | 舆情分析ID | `STRING` |  | `core` | 舆情分析ID |
| `target_entity_id` | 目标实体ID | `STRING` |  | `core` | 目标实体ID |
| `source_content_id` | 来源内容ID | `STRING` |  | `core` | 来源内容ID |
| `sentiment_score` | 情绪极性分 | `DOUBLE` | -1_to_1 | `core` | 情绪极性分 |
| `sentiment_label` | 情绪标签 | `STRING` |  | `core` | 情绪标签 |
| `stance_label` | 立场标签 | `STRING` |  | `core` | 立场标签 |
| `emotion_fear_score` | 恐惧情绪分 | `DOUBLE` | 0-1 | `core` | 恐惧情绪分 |
| `emotion_greed_score` | 贪婪情绪分 | `DOUBLE` | 0-1 | `core` | 贪婪情绪分 |
| `emotion_anger_score` | 愤怒情绪分 | `DOUBLE` | 0-1 | `core` | 愤怒情绪分 |
| `emotion_optimism_score` | 乐观情绪分 | `DOUBLE` | 0-1 | `core` | 乐观情绪分 |
| `emotion_pessimism_score` | 悲观情绪分 | `DOUBLE` | 0-1 | `core` | 悲观情绪分 |
| `uncertainty_score` | 不确定性评分 | `DOUBLE` | 0-1 | `core` | 不确定性评分 |
| `attention_score` | 关注度评分 | `DOUBLE` | 0-100 | `core` | 关注度评分 |
| `heat_score` | 热度评分 | `DOUBLE` | 0-100 | `core` | 热度评分 |
| `virality_score` | 传播性评分 | `DOUBLE` | 0-100 | `core` | 传播性评分 |
| `controversy_score` | 争议度评分 | `DOUBLE` | 0-100 | `core` | 争议度评分 |
| `credibility_score` | 可信度评分 | `DOUBLE` | 0-1 | `core` | 可信度评分 |
| `rumor_probability` | 谣言概率 | `DOUBLE` | 0-1 | `core` | 谣言概率 |
| `manipulation_probability` | 操纵概率 | `DOUBLE` | 0-1 | `core` | 操纵概率 |
| `narrative_id` | 叙事ID | `STRING` |  | `core` | 叙事ID |
| `narrative_name` | 叙事名称 | `STRING` |  | `core` | 叙事名称 |
| `narrative_stage` | 叙事阶段 | `STRING` |  | `core` | 叙事阶段 |
| `narrative_momentum_score` | 叙事动量 | `DOUBLE` | score | `core` | 叙事动量 |
| `narrative_decay_score` | 叙事衰减 | `DOUBLE` | score | `core` | 叙事衰减 |
| `impact_direction` | 预期影响方向 | `STRING` |  | `core` | 预期影响方向 |
| `impact_horizon_code` | 影响期限 | `STRING` |  | `core` | 影响期限 |
| `impact_magnitude_score` | 影响强度 | `DOUBLE` | score_0_100 | `core` | 影响强度 |
| `analysis_confidence_score` | 分析置信度 | `DOUBLE` | 0-1 | `core` | 分析置信度 |

### 19. 专家观点（`expert_opinion`）

专家逻辑必须有条件、期限、正反证据和事后评价

- 标准对象：`ExpertOpinion`
- 字段数量：30

| 标准字段 | 中文名 | 类型 | 单位 | 阶段 | 定义 |
|---|---|---|---|---|---|
| `opinion_id` | 专家观点ID | `STRING` |  | `core` | 专家观点ID |
| `expert_id` | 专家ID | `STRING` |  | `core` | 专家ID |
| `source_document_id` | 来源文档ID | `STRING` |  | `core` | 来源文档ID |
| `claim_text` | 核心判断 | `STRING` |  | `core` | 核心判断 |
| `premise_text` | 前提依据 | `STRING` |  | `core` | 前提依据 |
| `condition_text` | 成立条件 | `STRING` |  | `core` | 成立条件 |
| `causal_chain_text` | 因果链 | `STRING` |  | `core` | 因果链 |
| `target_entity_ids` | 目标实体集合 | `STRING[]` |  | `core` | 目标实体集合 |
| `prediction_direction` | 预测方向 | `STRING` |  | `core` | 预测方向 |
| `prediction_horizon_code` | 预测周期 | `STRING` |  | `core` | 预测周期 |
| `prediction_probability` | 预测概率 | `DOUBLE` | 0-1 | `core` | 预测概率 |
| `expert_confidence_score` | 专家自述置信度 | `DOUBLE` | 0-1 | `core` | 专家自述置信度 |
| `evidence_ids` | 支持证据集合 | `STRING[]` |  | `core` | 支持证据集合 |
| `counterevidence_ids` | 反向证据集合 | `STRING[]` |  | `core` | 反向证据集合 |
| `invalidation_condition_text` | 失效条件 | `STRING` |  | `core` | 失效条件 |
| `prediction_start_date` | 预测起始日期 | `DATE` |  | `core` | 预测起始日期 |
| `prediction_end_date` | 预测结束日期 | `DATE` |  | `core` | 预测结束日期 |
| `evaluation_date` | 评价日期 | `DATE` |  | `core` | 评价日期 |
| `evaluation_result` | 评价结果 | `STRING` |  | `core` | 评价结果 |
| `realized_return_pct` | 实际收益 | `DOUBLE` | percent_points | `core` | 实际收益 |
| `hit_flag` | 是否命中 | `BOOL` |  | `core` | 是否命中 |
| `bias_tags` | 偏差标签 | `STRING[]` |  | `core` | 偏差标签 |
| `review_status` | 人工审核状态 | `STRING` |  | `core` | 人工审核状态 |
| `expert_domain_codes` | 专家擅长领域代码集合 | `STRING[]` |  | `future_reserved` | 战争、能源、宏观、产业、市场微观结构等专家能力领域 |
| `expert_reliability_score` | 专家综合可靠度 | `DOUBLE` | 0-1 | `future_reserved` | 结合样本数、领域匹配、方向、幅度和时点表现形成 |
| `historical_direction_accuracy` | 历史方向准确率 | `DOUBLE` | 0-1 | `future_reserved` | 在对应领域预测方向正确的比例 |
| `historical_magnitude_error` | 历史幅度误差 | `DOUBLE` |  | `future_reserved` | 预测影响幅度与实际结果的标准化误差 |
| `historical_timing_error_days` | 历史时点误差 | `DOUBLE` | days | `future_reserved` | 预测发生时间与实际发生时间的平均误差 |
| `expert_evaluation_sample_count` | 专家评估样本数 | `INT` | count | `future_reserved` | 用于计算专家可靠度的有效样本数量 |
| `regime_reliability_json` | 不同市场状态可靠度 | `JSON` |  | `future_reserved` | 专家在牛市、熊市、危机等状态下的分项可靠度 |

### 20. 地缘政治、战争与冲突（`geopolitical_conflict`）

战争、制裁、封锁、和谈、基础设施和资本市场影响；事实与推断必须分离

- 标准对象：`GeopoliticalConflictEvent`
- 字段数量：63

| 标准字段 | 中文名 | 类型 | 单位 | 阶段 | 定义 |
|---|---|---|---|---|---|
| `conflict_id` | 冲突ID | `STRING` |  | `core` | 冲突ID |
| `conflict_event_id` | 冲突事件ID | `STRING` |  | `core` | 冲突事件ID |
| `conflict_name` | 冲突名称 | `STRING` |  | `core` | 冲突名称 |
| `conflict_type` | 冲突类型 | `STRING` |  | `core` | 冲突类型 |
| `conflict_status` | 冲突状态 | `STRING` |  | `core` | 冲突状态 |
| `conflict_phase` | 冲突阶段 | `STRING` |  | `core` | 冲突阶段 |
| `event_type` | 事件类型 | `STRING` |  | `core` | 事件类型 |
| `actor_primary_id` | 主要行动方ID | `STRING` |  | `core` | 主要行动方ID |
| `actor_secondary_id` | 次要行动方ID | `STRING` |  | `core` | 次要行动方ID |
| `initiator_actor_id` | 发起方ID | `STRING` |  | `core` | 发起方ID |
| `target_actor_id` | 目标方ID | `STRING` |  | `core` | 目标方ID |
| `actor_role_codes` | 参与方角色集合 | `STRING[]` |  | `core` | 参与方角色集合 |
| `country_codes` | 涉及国家代码 | `STRING[]` |  | `core` | 涉及国家代码 |
| `region_codes` | 涉及地区代码 | `STRING[]` |  | `core` | 涉及地区代码 |
| `location_name` | 地点名称 | `STRING` |  | `core` | 地点名称 |
| `latitude` | 纬度 | `DOUBLE` | degrees | `core` | 纬度 |
| `longitude` | 经度 | `DOUBLE` | degrees | `core` | 经度 |
| `event_time` | 事件时间 | `TIMESTAMP` |  | `core` | 事件时间 |
| `reported_at` | 首次报道时间 | `TIMESTAMP` |  | `core` | 首次报道时间 |
| `confirmed_at` | 确认时间 | `TIMESTAMP` |  | `core` | 确认时间 |
| `confirmation_status` | 确认状态 | `STRING` |  | `core` | 确认状态 |
| `source_count` | 独立来源数量 | `INT` | count | `core` | 独立来源数量 |
| `confidence_score` | 事件可信度 | `DOUBLE` | 0-1 | `core` | 事件可信度 |
| `severity_level` | 严重程度 | `STRING` |  | `core` | 严重程度 |
| `escalation_level` | 升级程度 | `STRING` |  | `core` | 升级程度 |
| `conflict_intensity_score` | 冲突强度 | `DOUBLE` | score_0_100 | `core` | 冲突强度 |
| `surprise_score` | 突发性评分 | `DOUBLE` | score_0_100 | `core` | 突发性评分 |
| `attack_method_code` | 行动方式代码 | `STRING` |  | `core` | 地面、空袭、导弹、无人机、海上、网络等 |
| `weapon_system_codes` | 武器系统类型集合 | `STRING[]` |  | `core` | 武器系统类型集合 |
| `mobilization_level` | 动员等级 | `STRING` |  | `core` | 动员等级 |
| `troop_movement_flag` | 是否发生兵力调动 | `BOOL` |  | `core` | 是否发生兵力调动 |
| `border_closure_flag` | 是否关闭边境 | `BOOL` |  | `core` | 是否关闭边境 |
| `blockade_flag` | 是否封锁 | `BOOL` |  | `core` | 是否封锁 |
| `ceasefire_status` | 停火状态 | `STRING` |  | `core` | 停火状态 |
| `peace_talk_status` | 和谈状态 | `STRING` |  | `core` | 和谈状态 |
| `sanction_event_flag` | 是否制裁事件 | `BOOL` |  | `core` | 是否制裁事件 |
| `embargo_flag` | 是否禁运 | `BOOL` |  | `core` | 是否禁运 |
| `export_control_flag` | 是否出口管制 | `BOOL` |  | `core` | 是否出口管制 |
| `territorial_control_change_score` | 领土控制变化评分 | `DOUBLE` | score | `core` | 领土控制变化评分 |
| `civilian_casualty_count` | 平民伤亡人数 | `LONG` | persons | `core` | 平民伤亡人数 |
| `military_casualty_count` | 军事人员伤亡人数 | `LONG` | persons | `core` | 军事人员伤亡人数 |
| `displaced_person_count` | 流离失所人数 | `LONG` | persons | `core` | 流离失所人数 |
| `casualty_data_confidence_score` | 伤亡数据可信度 | `DOUBLE` | 0-1 | `core` | 伤亡数据可信度 |
| `infrastructure_type_codes` | 受影响基础设施类型 | `STRING[]` |  | `core` | 受影响基础设施类型 |
| `energy_facility_affected_flag` | 能源设施是否受影响 | `BOOL` |  | `core` | 能源设施是否受影响 |
| `port_affected_flag` | 港口是否受影响 | `BOOL` |  | `core` | 港口是否受影响 |
| `shipping_lane_affected_flag` | 航道是否受影响 | `BOOL` |  | `core` | 航道是否受影响 |
| `financial_infrastructure_affected_flag` | 金融基础设施是否受影响 | `BOOL` |  | `core` | 金融基础设施是否受影响 |
| `telecom_infrastructure_affected_flag` | 通信基础设施是否受影响 | `BOOL` |  | `core` | 通信基础设施是否受影响 |
| `supply_chain_disruption_score` | 供应链中断评分 | `DOUBLE` | score_0_100 | `core` | 供应链中断评分 |
| `shipping_risk_score` | 航运风险评分 | `DOUBLE` | score_0_100 | `core` | 航运风险评分 |
| `energy_supply_risk_score` | 能源供应风险评分 | `DOUBLE` | score_0_100 | `core` | 能源供应风险评分 |
| `commodity_impact_score` | 大宗商品影响评分 | `DOUBLE` | score_0_100 | `core` | 大宗商品影响评分 |
| `trade_route_impact_score` | 贸易路线影响评分 | `DOUBLE` | score_0_100 | `core` | 贸易路线影响评分 |
| `insurance_risk_score` | 保险风险评分 | `DOUBLE` | score_0_100 | `core` | 保险风险评分 |
| `affected_sector_ids` | 受影响行业集合 | `STRING[]` |  | `core` | 受影响行业集合 |
| `affected_asset_ids` | 受影响资产集合 | `STRING[]` |  | `core` | 受影响资产集合 |
| `market_impact_direction` | 市场影响方向 | `STRING` |  | `core` | 市场影响方向 |
| `market_impact_horizon_code` | 市场影响期限 | `STRING` |  | `core` | 市场影响期限 |
| `market_impact_magnitude_score` | 市场影响强度 | `DOUBLE` | score_0_100 | `core` | 市场影响强度 |
| `market_volatility_impact_score` | 波动率影响评分 | `DOUBLE` | score_0_100 | `core` | 波动率影响评分 |
| `scenario_id` | 所属情景ID | `STRING` |  | `core` | 所属情景ID |
| `scenario_probability` | 情景概率 | `DOUBLE` | 0-1 | `core` | 情景概率 |

### 21. 实体经济与另类数据（`real_economy`）

生产、消费、物流、房地产、就业和供应链等长期扩展数据

- 标准对象：`AlternativeEconomicMetric`
- 字段数量：24

| 标准字段 | 中文名 | 类型 | 单位 | 阶段 | 定义 |
|---|---|---|---|---|---|
| `alternative_metric_id` | 实体经济指标ID | `STRING` |  | `core` | 实体经济指标ID |
| `metric_category` | 指标类别 | `STRING` |  | `core` | 指标类别 |
| `metric_code` | 指标代码 | `STRING` |  | `core` | 指标代码 |
| `metric_name_cn` | 指标中文名 | `STRING` |  | `core` | 指标中文名 |
| `region_code` | 地区代码 | `STRING` |  | `core` | 地区代码 |
| `industry_id` | 行业ID | `STRING` |  | `core` | 行业ID |
| `company_id` | 公司ID | `STRING` |  | `core` | 公司ID |
| `period_start_date` | 统计期开始 | `DATE` |  | `core` | 统计期开始 |
| `period_end_date` | 统计期结束 | `DATE` |  | `core` | 统计期结束 |
| `value_numeric` | 指标值 | `DECIMAL` |  | `core` | 指标值 |
| `unit_code` | 单位代码 | `STRING` |  | `core` | 单位代码 |
| `electricity_consumption_value` | 用电量 | `DECIMAL` |  | `future_reserved` | 用电量 |
| `freight_volume_value` | 货运量 | `DECIMAL` |  | `future_reserved` | 货运量 |
| `port_throughput_value` | 港口吞吐量 | `DECIMAL` |  | `future_reserved` | 港口吞吐量 |
| `logistics_index_value` | 物流指数 | `DOUBLE` |  | `future_reserved` | 物流指数 |
| `job_posting_count` | 招聘岗位数 | `LONG` |  | `future_reserved` | 招聘岗位数 |
| `store_footfall_count` | 门店客流量 | `LONG` |  | `future_reserved` | 门店客流量 |
| `housing_transaction_area` | 房地产成交面积 | `DOUBLE` |  | `future_reserved` | 房地产成交面积 |
| `consumer_spending_value_cny` | 消费支出 | `DECIMAL` | CNY | `future_reserved` | 消费支出 |
| `satellite_activity_score` | 遥感活动评分 | `DOUBLE` | score | `future_reserved` | 遥感活动评分 |
| `petroleum_input_cost_index` | 石油投入成本指数 | `DOUBLE` |  | `future_reserved` | 企业或行业石油类原料和燃料投入成本水平 |
| `real_estate_price_index` | 房地产价格指数 | `DOUBLE` |  | `future_reserved` | 指定地区房地产价格水平或场景指数 |
| `mortgage_rate_pct` | 住房按揭利率 | `DOUBLE` | percent_points | `future_reserved` | 住房按揭利率 |
| `household_disposable_income` | 居民可支配收入 | `DOUBLE` | CNY | `future_reserved` | 指定地区和期间居民可支配收入 |

### 22. 参与者行为与资本配置（`participant_behavior`）

居民、散户、机构、游资和外资的行为与资产配置状态

- 标准对象：`ParticipantBehaviorSnapshot`
- 字段数量：29

| 标准字段 | 中文名 | 类型 | 单位 | 阶段 | 定义 |
|---|---|---|---|---|---|
| `behavior_snapshot_id` | 行为快照ID | `STRING` |  | `core` | 行为快照ID |
| `as_of_date` | 观察日期 | `DATE` |  | `core` | 观察日期 |
| `participant_type` | 参与者类型 | `STRING` |  | `core` | 参与者类型 |
| `region_code` | 地区代码 | `STRING` |  | `core` | 地区代码 |
| `asset_class` | 资产类别 | `STRING` |  | `core` | 资产类别 |
| `gross_inflow_cny` | 总流入 | `DECIMAL` | CNY | `core` | 总流入 |
| `gross_outflow_cny` | 总流出 | `DECIMAL` | CNY | `core` | 总流出 |
| `net_flow_cny` | 净流入 | `DECIMAL` | CNY | `core` | 净流入 |
| `estimated_cash_balance_cny` | 估算可配置现金 | `DECIMAL` | CNY | `core` | 估算可配置现金 |
| `risk_appetite_score` | 风险偏好评分 | `DOUBLE` | score_0_100 | `core` | 风险偏好评分 |
| `leverage_score` | 杠杆程度评分 | `DOUBLE` | score_0_100 | `core` | 杠杆程度评分 |
| `fear_score` | 恐惧评分 | `DOUBLE` | score_0_100 | `core` | 恐惧评分 |
| `greed_score` | 贪婪评分 | `DOUBLE` | score_0_100 | `core` | 贪婪评分 |
| `herding_score` | 从众评分 | `DOUBLE` | score_0_100 | `core` | 从众评分 |
| `marginal_buyer_score` | 边际买方强度 | `DOUBLE` | score_0_100 | `core` | 边际买方强度 |
| `allocation_preference_code` | 资产配置偏好 | `STRING` |  | `core` | 资产配置偏好 |
| `switch_to_equity_probability` | 转向股票概率 | `DOUBLE` | 0-1 | `core` | 转向股票概率 |
| `switch_to_property_probability` | 转向房地产概率 | `DOUBLE` | 0-1 | `core` | 转向房地产概率 |
| `switch_to_deposit_probability` | 转向存款概率 | `DOUBLE` | 0-1 | `core` | 转向存款概率 |
| `switch_to_bond_probability` | 转向债券概率 | `DOUBLE` | 0-1 | `core` | 转向债券概率 |
| `switch_to_gold_probability` | 转向黄金概率 | `DOUBLE` | 0-1 | `core` | 转向黄金概率 |
| `capital_flight_probability` | 资金外移概率 | `DOUBLE` | 0-1 | `core` | 资金外移概率 |
| `behavior_confidence_score` | 行为估计置信度 | `DOUBLE` | 0-1 | `core` | 行为估计置信度 |
| `switch_to_fund_probability` | 转向基金概率 | `DOUBLE` | 0-1 | `future_reserved` | 该参与者提高基金配置的概率 |
| `switch_to_wealth_management_probability` | 转向理财概率 | `DOUBLE` | 0-1 | `future_reserved` | 该参与者提高银行或资管理财配置的概率 |
| `switch_to_commodity_probability` | 转向商品概率 | `DOUBLE` | 0-1 | `future_reserved` | 该参与者提高商品或商品基金配置的概率 |
| `switch_to_foreign_asset_probability` | 转向海外资产概率 | `DOUBLE` | 0-1 | `future_reserved` | 该参与者提高海外资产配置的概率 |
| `switch_to_real_economy_probability` | 转向实体投资概率 | `DOUBLE` | 0-1 | `future_reserved` | 该参与者提高实体经营或产业投资配置的概率 |
| `capital_absorption_score` | 资金吸纳强度评分 | `DOUBLE` | score_0_100 | `future_reserved` | 某资产类别从其他资产吸收资金的强度 |

### 23. 市场状态（`market_state`）

牛震熊、宽度、流动性、赚钱效应和系统性风险

- 标准对象：`MarketState`
- 字段数量：31

| 标准字段 | 中文名 | 类型 | 单位 | 阶段 | 定义 |
|---|---|---|---|---|---|
| `market_state_id` | 市场状态ID | `STRING` |  | `core` | 市场状态ID |
| `trade_date` | 交易日期 | `DATE` |  | `core` | 交易日期 |
| `market_scope_code` | 市场范围代码 | `STRING` |  | `core` | 市场范围代码 |
| `bull_probability` | 牛市概率 | `DOUBLE` | 0-1 | `core` | 牛市概率 |
| `sideways_probability` | 震荡概率 | `DOUBLE` | 0-1 | `core` | 震荡概率 |
| `bear_probability` | 熊市概率 | `DOUBLE` | 0-1 | `core` | 熊市概率 |
| `regime_label` | 市场状态标签 | `STRING` |  | `core` | 市场状态标签 |
| `trend_score` | 趋势评分 | `DOUBLE` | score_0_100 | `core` | 趋势评分 |
| `breadth_score` | 市场宽度评分 | `DOUBLE` | score_0_100 | `core` | 市场宽度评分 |
| `liquidity_score` | 流动性评分 | `DOUBLE` | score_0_100 | `core` | 流动性评分 |
| `profit_effect_score` | 赚钱效应评分 | `DOUBLE` | score_0_100 | `core` | 赚钱效应评分 |
| `volatility_score` | 波动风险评分 | `DOUBLE` | score_0_100 | `core` | 波动风险评分 |
| `drawdown_score` | 回撤风险评分 | `DOUBLE` | score_0_100 | `core` | 回撤风险评分 |
| `limit_up_count` | 涨停家数 | `INT` | count | `core` | 涨停家数 |
| `limit_down_count` | 跌停家数 | `INT` | count | `core` | 跌停家数 |
| `advance_count` | 上涨家数 | `INT` | count | `core` | 上涨家数 |
| `decline_count` | 下跌家数 | `INT` | count | `core` | 下跌家数 |
| `new_high_count` | 创新高家数 | `INT` | count | `core` | 创新高家数 |
| `new_low_count` | 创新低家数 | `INT` | count | `core` | 创新低家数 |
| `sector_diffusion_score` | 行业扩散评分 | `DOUBLE` | score_0_100 | `core` | 行业扩散评分 |
| `crowding_score` | 拥挤度评分 | `DOUBLE` | score_0_100 | `core` | 拥挤度评分 |
| `systemic_risk_score` | 系统性风险评分 | `DOUBLE` | score_0_100 | `core` | 系统性风险评分 |
| `state_confidence_score` | 状态判断置信度 | `DOUBLE` | 0-1 | `core` | 状态判断置信度 |
| `state_reason_codes` | 状态原因代码 | `STRING[]` |  | `core` | 状态原因代码 |
| `state_explanation_text` | 状态解释 | `STRING` |  | `core` | 状态解释 |
| `crisis_probability` | 危机状态概率 | `DOUBLE` | 0-1 | `future_reserved` | 极端风险或流动性危机状态概率 |
| `liquidity_regime_code` | 流动性状态代码 | `STRING` |  | `future_reserved` | 宽松、正常、收紧、枯竭等流动性状态 |
| `capital_flow_regime_code` | 资本流动状态代码 | `STRING` |  | `future_reserved` | 净流入、平衡、净流出、避险外移等 |
| `structural_market_flag` | 是否结构性行情 | `BOOL` |  | `future_reserved` | 指数与行业个股明显分化的结构性市场 |
| `dominant_sector_ids` | 主导行业集合 | `STRING[]` |  | `future_reserved` | 当前市场或仿真场景中主导收益和资金的行业 |
| `causal_driver_ids` | 主要因果驱动集合 | `STRING[]` |  | `future_reserved` | 导致当前市场状态的关键变量、事件和规则 |

### 24. 风险、仓位与策略门控（`risk_position`）

上游风险对模型和个股信号拥有否决权

- 标准对象：`RiskPositionDecision`
- 字段数量：15

| 标准字段 | 中文名 | 类型 | 单位 | 阶段 | 定义 |
|---|---|---|---|---|---|
| `risk_decision_id` | 风险决策ID | `STRING` |  | `core` | 风险决策ID |
| `decision_time` | 决策时间 | `TIMESTAMP` |  | `core` | 决策时间 |
| `risk_state` | 风险状态 | `STRING` |  | `core` | 风险状态 |
| `risk_level` | 风险等级 | `STRING` |  | `core` | 风险等级 |
| `recommended_total_position_pct` | 建议总仓位 | `DOUBLE` | percent_points | `core` | 建议总仓位 |
| `minimum_cash_pct` | 最低现金比例 | `DOUBLE` | percent_points | `core` | 最低现金比例 |
| `max_single_stock_weight_pct` | 单股最大权重 | `DOUBLE` | percent_points | `core` | 单股最大权重 |
| `max_sector_weight_pct` | 行业最大权重 | `DOUBLE` | percent_points | `core` | 行业最大权重 |
| `max_daily_turnover_pct` | 单日最大换手率 | `DOUBLE` | percent_points | `core` | 单日最大换手率 |
| `allow_new_positions` | 是否允许新开仓 | `BOOL` |  | `core` | 是否允许新开仓 |
| `allow_leverage` | 是否允许杠杆 | `BOOL` |  | `core` | 是否允许杠杆 |
| `allowed_strategy_codes` | 允许策略集合 | `STRING[]` |  | `core` | 允许策略集合 |
| `blocked_strategy_codes` | 禁止策略集合 | `STRING[]` |  | `core` | 禁止策略集合 |
| `halted_reason_codes` | 停止原因集合 | `STRING[]` |  | `core` | 停止原因集合 |
| `risk_explanation_text` | 风险解释 | `STRING` |  | `core` | 风险解释 |

### 25. 因子、标签与模型（`factor_model`）

基础因子、标签、模型预测和可解释性

- 标准对象：`FeaturePrediction`
- 字段数量：29

| 标准字段 | 中文名 | 类型 | 单位 | 阶段 | 定义 |
|---|---|---|---|---|---|
| `feature_id` | 特征ID | `STRING` |  | `core` | 特征ID |
| `feature_name` | 特征名称 | `STRING` |  | `core` | 特征名称 |
| `feature_family` | 特征家族 | `STRING` |  | `core` | 特征家族 |
| `instrument_id` | 证券统一标识 | `STRING` |  | `core` | 证券统一标识 |
| `trade_date` | 交易日期 | `DATE` |  | `core` | 交易日期 |
| `feature_value` | 特征值 | `DOUBLE` |  | `core` | 特征值 |
| `window_length` | 计算窗口 | `INT` | periods | `core` | 计算窗口 |
| `lag_periods` | 滞后期数 | `INT` | periods | `core` | 滞后期数 |
| `normalization_code` | 标准化方式 | `STRING` |  | `core` | 标准化方式 |
| `neutralization_code` | 中性化方式 | `STRING` |  | `core` | 中性化方式 |
| `winsorization_code` | 去极值方式 | `STRING` |  | `core` | 去极值方式 |
| `feature_formula` | 特征公式 | `STRING` |  | `core` | 特征公式 |
| `label_id` | 标签ID | `STRING` |  | `core` | 标签ID |
| `label_name` | 标签名称 | `STRING` |  | `core` | 标签名称 |
| `label_horizon_days` | 标签期限 | `INT` | trading_days | `core` | 标签期限 |
| `label_value` | 标签值 | `DOUBLE` |  | `core` | 标签值 |
| `model_id` | 模型ID | `STRING` |  | `core` | 模型ID |
| `model_name` | 模型名称 | `STRING` |  | `core` | 模型名称 |
| `model_type` | 模型类型 | `STRING` |  | `core` | 模型类型 |
| `prediction_time` | 预测时间 | `TIMESTAMP` |  | `core` | 预测时间 |
| `prediction_score` | 预测分数 | `DOUBLE` |  | `core` | 预测分数 |
| `prediction_probability` | 预测概率 | `DOUBLE` | 0-1 | `core` | 预测概率 |
| `prediction_rank` | 横截面排名 | `INT` |  | `core` | 横截面排名 |
| `prediction_confidence_score` | 预测置信度 | `DOUBLE` | 0-1 | `core` | 预测置信度 |
| `feature_contributions` | 特征贡献 | `MAP<STRING,DOUBLE>` |  | `core` | 特征贡献 |
| `model_explanation_text` | 模型解释 | `STRING` |  | `core` | 模型解释 |
| `experiment_id` | 关联研究实验ID | `STRING` |  | `near_term` | 关联research_experiment实验 |
| `model_version` | 模型版本 | `STRING` |  | `near_term` | 模型代码、特征和参数版本 |
| `feature_set_version` | 特征集合版本 | `STRING` |  | `near_term` | 本次预测使用的特征集合版本 |

### 26. 策略与股票池（`strategy_universe`）

市场状态先决定策略许可，再生成可交易股票池

- 标准对象：`StrategyUniverse`
- 字段数量：15

| 标准字段 | 中文名 | 类型 | 单位 | 阶段 | 定义 |
|---|---|---|---|---|---|
| `strategy_id` | 策略ID | `STRING` |  | `core` | 策略ID |
| `strategy_name` | 策略名称 | `STRING` |  | `core` | 策略名称 |
| `strategy_type` | 策略类型 | `STRING` |  | `core` | 策略类型 |
| `strategy_status` | 策略状态 | `STRING` |  | `core` | 策略状态 |
| `eligible_market_state_codes` | 适用市场状态集合 | `STRING[]` |  | `core` | 适用市场状态集合 |
| `required_feature_ids` | 依赖特征集合 | `STRING[]` |  | `core` | 依赖特征集合 |
| `holding_period_days` | 预期持有期 | `INT` | trading_days | `core` | 预期持有期 |
| `rebalance_frequency_code` | 调仓频率 | `STRING` |  | `core` | 调仓频率 |
| `universe_id` | 股票池ID | `STRING` |  | `core` | 股票池ID |
| `universe_name` | 股票池名称 | `STRING` |  | `core` | 股票池名称 |
| `instrument_id` | 成员证券标识 | `STRING` |  | `core` | 成员证券标识 |
| `inclusion_flag` | 是否纳入 | `BOOL` |  | `core` | 是否纳入 |
| `inclusion_reason_codes` | 纳入原因集合 | `STRING[]` |  | `core` | 纳入原因集合 |
| `exclusion_reason_codes` | 排除原因集合 | `STRING[]` |  | `core` | 排除原因集合 |
| `universe_effective_date` | 股票池生效日期 | `DATE` |  | `core` | 股票池生效日期 |

### 27. 目标组合与交易决策（`portfolio_decision`）

最终目标权重、交易数量、解释和人工复核

- 标准对象：`TradeDecision`
- 字段数量：25

| 标准字段 | 中文名 | 类型 | 单位 | 阶段 | 定义 |
|---|---|---|---|---|---|
| `portfolio_id` | 组合ID | `STRING` |  | `core` | 组合ID |
| `decision_id` | 决策ID | `STRING` |  | `core` | 决策ID |
| `decision_time` | 决策时间 | `TIMESTAMP` |  | `core` | 决策时间 |
| `instrument_id` | 证券统一标识 | `STRING` |  | `core` | 证券统一标识 |
| `action_code` | 建议动作 | `STRING` |  | `core` | 建议动作 |
| `current_weight_pct` | 当前权重 | `DOUBLE` | percent_points | `core` | 当前权重 |
| `target_weight_pct` | 目标权重 | `DOUBLE` | percent_points | `core` | 目标权重 |
| `weight_change_pct` | 权重变化 | `DOUBLE` | percent_points | `core` | 权重变化 |
| `current_quantity_shares` | 当前持股数 | `LONG` | shares | `core` | 当前持股数 |
| `target_quantity_shares` | 目标持股数 | `LONG` | shares | `core` | 目标持股数 |
| `recommended_trade_quantity_shares` | 建议交易股数 | `LONG` | shares | `core` | 建议交易股数 |
| `reference_price_cny` | 参考价格 | `DECIMAL` | CNY | `core` | 参考价格 |
| `estimated_trade_amount_cny` | 预计交易金额 | `DECIMAL` | CNY | `core` | 预计交易金额 |
| `model_score` | 模型分数 | `DOUBLE` |  | `core` | 模型分数 |
| `composite_score` | 综合分数 | `DOUBLE` |  | `core` | 综合分数 |
| `risk_level` | 风险等级 | `STRING` |  | `core` | 风险等级 |
| `market_state_label` | 市场状态标签 | `STRING` |  | `core` | 市场状态标签 |
| `confidence_score` | 决策置信度 | `DOUBLE` | 0-1 | `core` | 决策置信度 |
| `valid_until` | 决策有效截止时间 | `TIMESTAMP` |  | `core` | 决策有效截止时间 |
| `reason_codes` | 决策原因集合 | `STRING[]` |  | `core` | 决策原因集合 |
| `reason_text` | 决策原因说明 | `STRING` |  | `core` | 决策原因说明 |
| `risk_warning_text` | 风险提示 | `STRING` |  | `core` | 风险提示 |
| `human_override_flag` | 是否人工修改 | `BOOL` |  | `core` | 是否人工修改 |
| `human_override_action` | 人工修改动作 | `STRING` |  | `core` | 人工修改动作 |
| `human_override_reason` | 人工修改原因 | `STRING` |  | `core` | 人工修改原因 |

### 28. 回测与绩效（`backtest`）

真实A股成交约束、成本、容量和绩效指标

- 标准对象：`BacktestPerformance`
- 字段数量：36

| 标准字段 | 中文名 | 类型 | 单位 | 阶段 | 定义 |
|---|---|---|---|---|---|
| `backtest_run_id` | 回测运行ID | `STRING` |  | `core` | 回测运行ID |
| `trade_date` | 交易日期 | `DATE` |  | `core` | 交易日期 |
| `portfolio_nav` | 组合净值 | `DOUBLE` |  | `core` | 组合净值 |
| `portfolio_return_pct` | 组合收益率 | `DOUBLE` | percent_points | `core` | 组合收益率 |
| `benchmark_nav` | 基准净值 | `DOUBLE` |  | `core` | 基准净值 |
| `benchmark_return_pct` | 基准收益率 | `DOUBLE` | percent_points | `core` | 基准收益率 |
| `excess_return_pct` | 超额收益率 | `DOUBLE` | percent_points | `core` | 超额收益率 |
| `drawdown_pct` | 回撤 | `DOUBLE` | percent_points | `core` | 回撤 |
| `gross_exposure_pct` | 总暴露 | `DOUBLE` | percent_points | `core` | 总暴露 |
| `net_exposure_pct` | 净暴露 | `DOUBLE` | percent_points | `core` | 净暴露 |
| `cash_weight_pct` | 现金权重 | `DOUBLE` | percent_points | `core` | 现金权重 |
| `turnover_pct` | 换手率 | `DOUBLE` | percent_points | `core` | 换手率 |
| `commission_cost_cny` | 佣金成本 | `DECIMAL` | CNY | `core` | 佣金成本 |
| `stamp_duty_cost_cny` | 印花税成本 | `DECIMAL` | CNY | `core` | 印花税成本 |
| `transfer_fee_cost_cny` | 过户费成本 | `DECIMAL` | CNY | `core` | 过户费成本 |
| `slippage_cost_cny` | 滑点成本 | `DECIMAL` | CNY | `core` | 滑点成本 |
| `market_impact_cost_cny` | 市场冲击成本 | `DECIMAL` | CNY | `core` | 市场冲击成本 |
| `trade_count` | 交易笔数 | `INT` | count | `core` | 交易笔数 |
| `unfilled_order_count` | 未成交订单数 | `INT` | count | `core` | 未成交订单数 |
| `capacity_estimate_cny` | 策略容量估计 | `DECIMAL` | CNY | `core` | 策略容量估计 |
| `annualized_return_pct` | 年化收益率 | `DOUBLE` | percent_points | `core` | 年化收益率 |
| `annualized_volatility_pct` | 年化波动率 | `DOUBLE` | percent_points | `core` | 年化波动率 |
| `sharpe_ratio` | 夏普比率 | `DOUBLE` |  | `core` | 夏普比率 |
| `sortino_ratio` | 索提诺比率 | `DOUBLE` |  | `core` | 索提诺比率 |
| `max_drawdown_pct` | 最大回撤 | `DOUBLE` | percent_points | `core` | 最大回撤 |
| `win_rate_pct` | 胜率 | `DOUBLE` | percent_points | `core` | 胜率 |
| `profit_loss_ratio` | 盈亏比 | `DOUBLE` |  | `core` | 盈亏比 |
| `simulation_run_id` | 仿真运行ID | `STRING` |  | `future_reserved` | 使用合成行情时关联仿真运行 |
| `scenario_id` | 场景ID | `STRING` |  | `future_reserved` | 使用合成行情或压力测试时关联场景 |
| `monte_carlo_path_id` | 蒙特卡洛路径ID | `STRING` |  | `future_reserved` | 同一场景下某条具体随机行情路径 |
| `stress_test_flag` | 是否压力测试 | `BOOL` |  | `future_reserved` | 该回测是否属于极端或指定因果场景压力测试 |
| `market_data_origin_code` | 回测行情数据来源性质 | `STRING` |  | `future_reserved` | 真实历史、重采样、合成、混合等 |
| `experiment_id` | 关联研究实验ID | `STRING` |  | `near_term` | 关联研究实验和晋级评审 |
| `walk_forward_fold_id` | 滚动验证折ID | `STRING` |  | `near_term` | Walk-forward中的具体窗口 |
| `cost_model_version` | 交易成本模型版本 | `STRING` |  | `near_term` | 费用、滑点和冲击成本模型版本 |
| `capacity_warning_flag` | 容量预警标记 | `BOOL` |  | `near_term` | 策略规模超过流动性或容量约束 |

### 29. 订单、成交、持仓与账户（`execution`）

当前人工执行可记录，未来用于QMT/PTrade/vn.py

- 标准对象：`OrderTradePosition`
- 字段数量：40

| 标准字段 | 中文名 | 类型 | 单位 | 阶段 | 定义 |
|---|---|---|---|---|---|
| `account_id` | 账户ID | `STRING` |  | `core` | 账户ID |
| `broker_code` | 券商代码 | `STRING` |  | `core` | 券商代码 |
| `order_id` | 平台订单ID | `STRING` |  | `core` | 平台订单ID |
| `broker_order_id` | 券商订单ID | `STRING` |  | `core` | 券商订单ID |
| `client_order_id` | 客户端订单ID | `STRING` |  | `core` | 客户端订单ID |
| `instrument_id` | 证券统一标识 | `STRING` |  | `core` | 证券统一标识 |
| `side_code` | 买卖方向 | `STRING` |  | `core` | 买卖方向 |
| `order_type` | 订单类型 | `STRING` |  | `core` | 订单类型 |
| `order_price_cny` | 委托价格 | `DECIMAL` | CNY | `core` | 委托价格 |
| `order_quantity_shares` | 委托数量 | `LONG` | shares | `core` | 委托数量 |
| `filled_quantity_shares` | 成交数量 | `LONG` | shares | `core` | 成交数量 |
| `remaining_quantity_shares` | 剩余数量 | `LONG` | shares | `core` | 剩余数量 |
| `average_fill_price_cny` | 平均成交价 | `DECIMAL` | CNY | `core` | 平均成交价 |
| `order_status` | 订单状态 | `STRING` |  | `core` | 订单状态 |
| `submitted_at` | 提交时间 | `TIMESTAMP` |  | `core` | 提交时间 |
| `accepted_at` | 受理时间 | `TIMESTAMP` |  | `core` | 受理时间 |
| `last_update_at` | 最后更新时间 | `TIMESTAMP` |  | `core` | 最后更新时间 |
| `cancelled_at` | 撤单时间 | `TIMESTAMP` |  | `core` | 撤单时间 |
| `reject_reason_code` | 拒单原因代码 | `STRING` |  | `core` | 拒单原因代码 |
| `commission_cny` | 佣金 | `DECIMAL` | CNY | `core` | 佣金 |
| `stamp_duty_cny` | 印花税 | `DECIMAL` | CNY | `core` | 印花税 |
| `transfer_fee_cny` | 过户费 | `DECIMAL` | CNY | `core` | 过户费 |
| `slippage_cny` | 滑点金额 | `DECIMAL` | CNY | `core` | 滑点金额 |
| `position_quantity_shares` | 持仓数量 | `LONG` | shares | `core` | 持仓数量 |
| `available_quantity_shares` | 可卖数量 | `LONG` | shares | `core` | 可卖数量 |
| `position_cost_cny` | 持仓成本 | `DECIMAL` | CNY | `core` | 持仓成本 |
| `market_value_cny` | 持仓市值 | `DECIMAL` | CNY | `core` | 持仓市值 |
| `unrealized_pnl_cny` | 浮动盈亏 | `DECIMAL` | CNY | `core` | 浮动盈亏 |
| `realized_pnl_cny` | 已实现盈亏 | `DECIMAL` | CNY | `core` | 已实现盈亏 |
| `cash_balance_cny` | 现金余额 | `DECIMAL` | CNY | `core` | 现金余额 |
| `available_cash_cny` | 可用资金 | `DECIMAL` | CNY | `core` | 可用资金 |
| `strategy_id` | 策略ID | `STRING` |  | `future_reserved` | 订单来源策略 |
| `decision_id` | 决策ID | `STRING` |  | `future_reserved` | 订单来源的组合或人工决策 |
| `environment_code` | 运行环境 | `STRING` |  | `future_reserved` | 研究、回测、模拟盘或实盘 |
| `idempotency_key` | 幂等键 | `STRING` |  | `future_reserved` | 防止网络重试导致重复下单 |
| `pretrade_risk_decision_id` | 交易前风控决策ID | `STRING` |  | `future_reserved` | 独立交易前风控记录 |
| `pretrade_risk_passed` | 交易前风控是否通过 | `BOOL` |  | `future_reserved` | 通过后才可发往券商 |
| `kill_switch_level_code` | 停机级别 | `STRING` |  | `future_reserved` | 暂停开仓、只卖出、撤单、停策略、停账户或全部停止 |
| `manual_intervention_flag` | 是否人工干预 | `BOOL` |  | `future_reserved` | 订单状态是否经过人工处理 |
| `last_reconciled_at` | 最后核对时间 | `TIMESTAMP` |  | `future_reserved` | 最后一次与券商账实核对时间 |

### 30. 任务运行与数据质量（`system_quality`）

个人项目轻量日志、质量门禁和运行状态

- 标准对象：`TaskQualityRecord`
- 字段数量：29

| 标准字段 | 中文名 | 类型 | 单位 | 阶段 | 定义 |
|---|---|---|---|---|---|
| `task_run_id` | 任务运行ID | `STRING` |  | `core` | 任务运行ID |
| `task_name` | 任务名称 | `STRING` |  | `core` | 任务名称 |
| `run_date` | 运行日期 | `DATE` |  | `core` | 运行日期 |
| `started_at` | 开始时间 | `TIMESTAMP` |  | `core` | 开始时间 |
| `ended_at` | 结束时间 | `TIMESTAMP` |  | `core` | 结束时间 |
| `run_status` | 运行状态 | `STRING` |  | `core` | 运行状态 |
| `error_code` | 错误代码 | `STRING` |  | `core` | 错误代码 |
| `error_message` | 错误信息 | `STRING` |  | `core` | 错误信息 |
| `warning_messages` | 警告集合 | `STRING[]` |  | `core` | 警告集合 |
| `input_row_count` | 输入行数 | `LONG` | count | `core` | 输入行数 |
| `output_row_count` | 输出行数 | `LONG` | count | `core` | 输出行数 |
| `coverage_ratio` | 覆盖率 | `DOUBLE` | 0-1 | `core` | 覆盖率 |
| `duplicate_ratio` | 重复率 | `DOUBLE` | 0-1 | `core` | 重复率 |
| `null_ratio` | 空值率 | `DOUBLE` | 0-1 | `core` | 空值率 |
| `invalid_ratio` | 无效率 | `DOUBLE` | 0-1 | `core` | 无效率 |
| `stale_data_flag` | 是否使用过期数据 | `BOOL` |  | `core` | 是否使用过期数据 |
| `latest_source_time` | 最新来源时间 | `TIMESTAMP` |  | `core` | 最新来源时间 |
| `quality_gate_passed` | 质量门禁是否通过 | `BOOL` |  | `core` | 质量门禁是否通过 |
| `quality_gate_failure_codes` | 质量门禁失败代码 | `STRING[]` |  | `core` | 质量门禁失败代码 |
| `memory_peak_mb` | 峰值内存 | `DOUBLE` | MB | `core` | 峰值内存 |
| `elapsed_seconds` | 运行耗时 | `DOUBLE` | seconds | `core` | 运行耗时 |
| `environment_code` | 运行环境 | `STRING` |  | `near_term` | 研究、回测、模拟盘或实盘 |
| `deployment_version` | 部署版本 | `STRING` |  | `future_reserved` | 当前运行程序版本 |
| `code_commit_hash` | 代码提交哈希 | `STRING` |  | `near_term` | 当前任务对应的Git提交 |
| `configuration_hash` | 配置哈希 | `STRING` |  | `near_term` | 运行配置内容哈希 |
| `release_status_code` | 发布状态 | `STRING` |  | `future_reserved` | 草稿、测试、批准、部署、回滚或退役 |
| `rollback_target_version` | 回滚目标版本 | `STRING` |  | `future_reserved` | 异常时可恢复的稳定版本 |
| `backup_status_code` | 备份状态 | `STRING` |  | `future_reserved` | 数据和配置备份状态 |
| `recovery_test_status_code` | 恢复演练状态 | `STRING` |  | `future_reserved` | 故障恢复是否经过演练 |

### 31. 图表与研究标注（`visualization`）

TradingView式工作台中的人工标注、事件和交易证据

- 标准对象：`ChartAnnotation`
- 字段数量：10

| 标准字段 | 中文名 | 类型 | 单位 | 阶段 | 定义 |
|---|---|---|---|---|---|
| `annotation_id` | 标注ID | `STRING` |  | `core` | 标注ID |
| `chart_id` | 图表ID | `STRING` |  | `core` | 图表ID |
| `instrument_id` | 证券统一标识 | `STRING` |  | `core` | 证券统一标识 |
| `annotation_time` | 标注时间 | `TIMESTAMP` |  | `core` | 标注时间 |
| `annotation_type` | 标注类型 | `STRING` |  | `core` | 标注类型 |
| `annotation_text` | 标注文本 | `STRING` |  | `core` | 标注文本 |
| `created_by_type` | 创建者类型 | `STRING` |  | `core` | 创建者类型 |
| `visibility_code` | 可见性 | `STRING` |  | `core` | 可见性 |
| `linked_event_ids` | 关联事件ID集合 | `STRING[]` |  | `core` | 关联事件ID集合 |
| `linked_decision_ids` | 关联决策ID集合 | `STRING[]` |  | `core` | 关联决策ID集合 |

### 32. 仿真变量定义（`simulation_variable`）

定义标准字段如何作为真实、人工、估计、推导或合成变量进入因果市场仿真

- 标准对象：`SimulationVariableDefinition`
- 字段数量：33

| 标准字段 | 中文名 | 类型 | 单位 | 阶段 | 定义 |
|---|---|---|---|---|---|
| `simulation_variable_id` | 仿真变量定义ID | `STRING` |  | `future_reserved` | 仿真变量定义唯一标识 |
| `canonical_field_name` | 对应标准字段名 | `STRING` |  | `future_reserved` | 必须存在于canonical_fields.yaml |
| `simulation_enabled` | 是否允许参与仿真 | `BOOL` |  | `future_reserved` | 该标准字段是否可作为仿真输入、中间状态或输出 |
| `variable_role_code` | 变量角色代码 | `STRING` |  | `future_reserved` | 结构、外生状态、内生状态、中间变量或输出变量 |
| `allowed_input_mode_codes` | 允许输入模式集合 | `STRING[]` |  | `future_reserved` | 真实、人工、场景、代理、专家、推导、隐状态或合成 |
| `default_input_mode_code` | 默认输入模式 | `STRING` |  | `future_reserved` | 没有真实数据时采用的默认激活方式 |
| `valid_min_numeric` | 合法最小数值 | `DOUBLE` |  | `future_reserved` | 仿真变量允许的最小数值 |
| `valid_max_numeric` | 合法最大数值 | `DOUBLE` |  | `future_reserved` | 仿真变量允许的最大数值 |
| `default_value_numeric` | 默认数值 | `DOUBLE` |  | `future_reserved` | 未指定场景且允许默认值时使用 |
| `default_value_text` | 默认文本值 | `STRING` |  | `future_reserved` | 枚举或文本变量默认值 |
| `distribution_code` | 默认分布代码 | `STRING` |  | `future_reserved` | 常数、均匀、三角、正态、经验、状态依赖等 |
| `distribution_parameters_json` | 分布参数 | `JSON` |  | `future_reserved` | 分布、状态转移或采样参数 |
| `manual_override_allowed` | 是否允许人工覆盖 | `BOOL` |  | `future_reserved` | 场景编辑器能否人工设定该变量 |
| `scenario_override_allowed` | 是否允许场景覆盖 | `BOOL` |  | `future_reserved` | 标准场景能否覆盖默认生成方式 |
| `proxy_variable_names` | 代理变量集合 | `STRING[]` |  | `future_reserved` | 真实数据缺失时可用于估计的标准变量 |
| `parent_variable_names` | 直接父变量集合 | `STRING[]` |  | `future_reserved` | 主要用于推导该变量的上游变量 |
| `derivation_rule_ids` | 推导规则集合 | `STRING[]` |  | `future_reserved` | 用于生成该内生变量的因果规则 |
| `output_rule_ids` | 下游规则集合 | `STRING[]` |  | `future_reserved` | 该变量变化后可能触发的因果规则 |
| `update_frequency_code` | 更新频率代码 | `STRING` |  | `future_reserved` | 事件、逐笔、分钟、日、月、季度或场景级 |
| `persistence_score` | 状态持续性评分 | `DOUBLE` | 0-1 | `future_reserved` | 变量冲击跨期保持的程度 |
| `mean_reversion_score` | 均值回归评分 | `DOUBLE` | 0-1 | `future_reserved` | 变量回归长期状态的倾向 |
| `uncertainty_level_code` | 不确定性等级 | `STRING` |  | `future_reserved` | 低、中、高、极高 |
| `missing_input_policy_code` | 缺失输入处理策略 | `STRING` |  | `future_reserved` | 停止、人工、代理、估计、采样或保持前值 |
| `required_for_regime_flag` | 市场状态推导是否必需 | `BOOL` |  | `future_reserved` | 是否为牛熊和流动性状态计算的必要变量 |
| `required_for_micro_path_flag` | 微观路径生成是否必需 | `BOOL` |  | `future_reserved` | 是否为K线、分时或逐笔路径生成的必要变量 |
| `calibration_status_code` | 校准状态 | `STRING` |  | `future_reserved` | 未设计、待校准、已校准、需复核 |
| `canonical_field_ref` | 限定标准字段引用 | `STRING` |  | `future_reserved` | 优先采用domain_code.canonical_name，解决跨领域同名字段歧义 |
| `scenario_addressable` | 是否可被场景系统寻址 | `BOOL` |  | `future_reserved` | 是否可在用户场景控制平面中检索和引用 |
| `control_permission_code` | 用户控制权限代码 | `STRING` |  | `future_reserved` | 直接控制、条件覆盖、测试覆盖、只读或输出 |
| `default_propagation_mode_code` | 默认传播模式 | `STRING` |  | `future_reserved` | 自动传播、选择性传播、固定不传播或仅测试 |
| `override_requires_reason` | 覆盖是否必须填写理由 | `BOOL` |  | `future_reserved` | 覆盖内生或输出变量时必须保存人工理由 |
| `default_conflict_policy_code` | 默认冲突策略 | `STRING` |  | `future_reserved` | 发生硬逻辑或多干预冲突时的默认处理 |
| `user_control_help_text` | 用户控制说明 | `STRING` |  | `future_reserved` | 面向场景编辑器解释可控方式、风险和下游影响 |

### 33. 仿真变量状态值（`simulation_value`）

记录某次场景和时点中真实、人工、估计、推导或随机生成的变量值

- 标准对象：`SimulationVariableValue`
- 字段数量：24

| 标准字段 | 中文名 | 类型 | 单位 | 阶段 | 定义 |
|---|---|---|---|---|---|
| `simulation_value_id` | 仿真变量值ID | `STRING` |  | `future_reserved` | 仿真变量具体值唯一标识 |
| `simulation_run_id` | 仿真运行ID | `STRING` |  | `future_reserved` | 所属仿真运行 |
| `scenario_id` | 场景ID | `STRING` |  | `future_reserved` | 所属世界场景 |
| `canonical_field_name` | 标准字段名 | `STRING` |  | `future_reserved` | 被赋值的标准变量 |
| `simulation_time` | 仿真时间 | `TIMESTAMP` |  | `future_reserved` | 该变量值在仿真世界中的时点 |
| `entity_id` | 作用实体ID | `STRING` |  | `future_reserved` | 公司、行业、资产、参与者或基础设施 |
| `instrument_id` | 作用证券ID | `STRING` |  | `future_reserved` | 证券级变量作用对象 |
| `industry_id` | 作用行业ID | `STRING` |  | `future_reserved` | 行业级变量作用对象 |
| `country_code` | 作用国家代码 | `STRING` |  | `future_reserved` | 国家级变量作用范围 |
| `region_code` | 作用地区代码 | `STRING` |  | `future_reserved` | 地区级变量作用范围 |
| `value_numeric` | 仿真数值 | `DOUBLE` |  | `future_reserved` | 数值变量的具体值 |
| `value_text` | 仿真文本或枚举值 | `STRING` |  | `future_reserved` | 文本或枚举变量具体值 |
| `value_bool` | 仿真布尔值 | `BOOL` |  | `future_reserved` | 布尔变量具体值 |
| `unit_code` | 单位代码 | `STRING` |  | `future_reserved` | 该数值采用的统一单位 |
| `value_origin_code` | 数值来源性质 | `STRING` |  | `future_reserved` | 真实、人工、场景、专家、代理、推导、隐状态或合成 |
| `input_mode_code` | 本次输入模式 | `STRING` |  | `future_reserved` | 本次仿真实际使用的变量激活方式 |
| `value_confidence_score` | 数值置信度 | `DOUBLE` | 0-1 | `future_reserved` | 该次变量值可信程度 |
| `uncertainty_lower_numeric` | 不确定性下界 | `DOUBLE` |  | `future_reserved` | 仿真区间下界 |
| `uncertainty_upper_numeric` | 不确定性上界 | `DOUBLE` |  | `future_reserved` | 仿真区间上界 |
| `parent_simulation_value_ids` | 父变量值集合 | `STRING[]` |  | `future_reserved` | 直接导致该值的上游变量值 |
| `causal_trace_id` | 因果追溯ID | `STRING` |  | `future_reserved` | 关联完整因果传播路径 |
| `manual_override_flag` | 是否人工覆盖 | `BOOL` |  | `future_reserved` | 本次值是否由人工强制设定 |
| `sampled_flag` | 是否随机采样 | `BOOL` |  | `future_reserved` | 本次值是否从允许分布采样 |
| `random_seed` | 随机种子 | `LONG` |  | `future_reserved` | 该变量采样使用的随机种子 |

### 34. 因果规则与硬逻辑（`causal_rule`）

记录物理、会计、制度、经济传导和专家逻辑，约束变量如何有因有果地传播

- 标准对象：`CausalRuleDefinition`
- 字段数量：39

| 标准字段 | 中文名 | 类型 | 单位 | 阶段 | 定义 |
|---|---|---|---|---|---|
| `causal_rule_id` | 因果规则ID | `STRING` |  | `future_reserved` | 因果规则唯一标识 |
| `causal_rule_name_cn` | 因果规则中文名 | `STRING` |  | `future_reserved` | 规则可读名称 |
| `cause_variable_names` | 原因变量集合 | `STRING[]` |  | `future_reserved` | 触发规则的上游标准变量 |
| `effect_variable_names` | 结果变量集合 | `STRING[]` |  | `future_reserved` | 规则产生影响的下游标准变量 |
| `causal_relation_type_code` | 因果关系类型 | `STRING` |  | `future_reserved` | 硬恒等、硬约束、硬方向、条件因果、概率因果或经验相关 |
| `effect_direction_code` | 影响方向代码 | `STRING` |  | `future_reserved` | 正向、负向、双向、非单调或由条件决定 |
| `effect_function_code` | 影响函数代码 | `STRING` |  | `future_reserved` | 线性、分段、阈值、弹性、逻辑函数、自定义等 |
| `effect_function_parameters_json` | 影响函数参数 | `JSON` |  | `future_reserved` | 系数、阈值、弹性或状态依赖参数 |
| `lag_min_days` | 最短传导滞后 | `DOUBLE` | days | `future_reserved` | 原因到结果开始显现的最短时间 |
| `lag_max_days` | 最长传导滞后 | `DOUBLE` | days | `future_reserved` | 原因到结果开始显现的最长时间 |
| `effect_duration_days` | 影响持续时间 | `DOUBLE` | days | `future_reserved` | 影响大致持续时间 |
| `decay_function_code` | 影响衰减函数 | `STRING` |  | `future_reserved` | 无衰减、线性、指数、分段或自定义 |
| `applicable_condition_expression` | 适用条件表达式 | `STRING` |  | `future_reserved` | 规则成立必须满足的条件 |
| `invalidation_condition_expression` | 失效条件表达式 | `STRING` |  | `future_reserved` | 规则不再适用或方向改变的条件 |
| `strength_min` | 影响强度下界 | `DOUBLE` |  | `future_reserved` | 规则强度参数下界 |
| `strength_mode` | 影响强度众数 | `DOUBLE` |  | `future_reserved` | 最可能影响强度 |
| `strength_max` | 影响强度上界 | `DOUBLE` |  | `future_reserved` | 规则强度参数上界 |
| `causal_confidence_score` | 因果规则置信度 | `DOUBLE` | 0-1 | `future_reserved` | 综合证据、统计和专家评价后的可信程度 |
| `evidence_level_code` | 证据等级 | `STRING` |  | `future_reserved` | 定义、制度、物理、会计、研究、统计、专家或假设 |
| `evidence_ids` | 支持证据集合 | `STRING[]` |  | `future_reserved` | 支持该规则的文档、数据或案例 |
| `counterevidence_ids` | 反证集合 | `STRING[]` |  | `future_reserved` | 削弱或推翻该规则的证据 |
| `expert_logic_ids` | 专家逻辑集合 | `STRING[]` |  | `future_reserved` | 提供或支持该规则的专家观点 |
| `historical_hit_rate` | 历史命中率 | `DOUBLE` | 0-1 | `future_reserved` | 在适用样本中方向或状态命中的比例 |
| `historical_sample_count` | 历史有效样本数 | `INT` | count | `future_reserved` | 用于校准规则的样本数量 |
| `applicable_regime_codes` | 适用市场状态集合 | `STRING[]` |  | `future_reserved` | 规则在何种市场状态下适用 |
| `applicable_entity_type_codes` | 适用实体类型集合 | `STRING[]` |  | `future_reserved` | 国家、行业、公司、参与者或资产 |
| `rule_version` | 规则版本 | `STRING` |  | `future_reserved` | 规则定义和参数版本 |
| `effective_from` | 规则生效时间 | `TIMESTAMP` |  | `future_reserved` | 该版本规则生效起点 |
| `effective_to` | 规则失效时间 | `TIMESTAMP` |  | `future_reserved` | 该版本规则结束时间 |
| `review_status_code` | 规则审核状态 | `STRING` |  | `future_reserved` | 草稿、待审核、启用、暂停、废弃 |
| `cause_field_refs` | 限定原因字段引用集合 | `STRING[]` |  | `future_reserved` | 优先使用domain_code.canonical_name |
| `effect_field_refs` | 限定结果字段引用集合 | `STRING[]` |  | `future_reserved` | 优先使用domain_code.canonical_name |
| `proposed_by_type_code` | 规则提出者类型 | `STRING` |  | `future_reserved` | 项目负责人、专家、大语言模型、数据挖掘或官方规则 |
| `proposed_by_id` | 规则提出者ID | `STRING` |  | `future_reserved` | 专家、模型、用户或资料来源标识 |
| `llm_generated_flag` | 是否由大语言模型提出 | `BOOL` |  | `future_reserved` | 大语言模型提出的规则必须人工审核 |
| `human_review_required_flag` | 是否必须人工审核 | `BOOL` |  | `future_reserved` | 进入APPROVED或ACTIVE前是否强制人工核验 |
| `approved_by_user_id` | 批准人ID | `STRING` |  | `future_reserved` | 人工批准规则的用户或审核者 |
| `approved_at` | 批准时间 | `TIMESTAMP` |  | `future_reserved` | 规则获得人工批准的时间 |
| `approval_notes` | 批准说明 | `STRING` |  | `future_reserved` | 证据、反例、适用范围和限制说明 |

### 35. 因果仿真场景（`simulation_scenario`）

定义一次世界、经济、行为和资本冲击场景及其假设变量

- 标准对象：`SimulationScenario`
- 字段数量：28

| 标准字段 | 中文名 | 类型 | 单位 | 阶段 | 定义 |
|---|---|---|---|---|---|
| `scenario_id` | 场景ID | `STRING` |  | `future_reserved` | 仿真场景唯一标识 |
| `scenario_name_cn` | 场景中文名 | `STRING` |  | `future_reserved` | 场景可读名称 |
| `scenario_type_code` | 场景类型 | `STRING` |  | `future_reserved` | 基准、牛市、熊市、战争、能源、房地产、政策、流动性等 |
| `scenario_status_code` | 场景状态 | `STRING` |  | `future_reserved` | 草稿、已审核、可运行、冻结、废弃 |
| `scenario_description` | 场景说明 | `STRING` |  | `future_reserved` | 现实或假设世界发生了什么 |
| `scenario_start_time` | 场景开始时间 | `TIMESTAMP` |  | `future_reserved` | 冲击开始时点 |
| `scenario_end_time` | 场景结束时间 | `TIMESTAMP` |  | `future_reserved` | 场景预设结束时点 |
| `target_market_scope_code` | 目标市场范围 | `STRING` |  | `future_reserved` | 全市场、国家、行业、概念或证券集合 |
| `target_entity_ids` | 目标实体集合 | `STRING[]` |  | `future_reserved` | 受到直接或重点影响的对象 |
| `base_regime_code` | 初始市场状态 | `STRING` |  | `future_reserved` | 冲击发生前的牛熊、流动性和风险状态 |
| `shock_variable_names` | 冲击变量集合 | `STRING[]` |  | `future_reserved` | 人工或模板设定的上游变量 |
| `shock_simulation_value_ids` | 冲击变量值集合 | `STRING[]` |  | `future_reserved` | 场景中具体冲击值 |
| `scenario_probability` | 场景发生概率 | `DOUBLE` | 0-1 | `future_reserved` | 场景用于预测或组合情景分析时的主观或模型概率 |
| `scenario_weight` | 场景权重 | `DOUBLE` | 0-1 | `future_reserved` | 多场景汇总时权重 |
| `manual_input_flag` | 是否含人工输入 | `BOOL` |  | `future_reserved` | 场景是否包含人工设定变量 |
| `scenario_template_id` | 场景模板ID | `STRING` |  | `future_reserved` | 战争、油价、房地产等模板来源 |
| `parent_scenario_id` | 父场景ID | `STRING` |  | `future_reserved` | 由某基础场景派生 |
| `causal_rule_set_id` | 因果规则集ID | `STRING` |  | `future_reserved` | 本场景采用的规则集合 |
| `market_rule_set_id` | 市场制度规则集ID | `STRING` |  | `future_reserved` | A股或其他市场交易规则版本 |
| `generator_version` | 生成器版本 | `STRING` |  | `future_reserved` | 执行该场景的引擎版本 |
| `random_seed` | 随机种子 | `LONG` |  | `future_reserved` | 具体路径可复现种子 |
| `configuration_hash` | 配置哈希 | `STRING` |  | `future_reserved` | 场景、规则和生成参数哈希 |
| `created_by_type` | 创建者类型 | `STRING` |  | `future_reserved` | 人工、系统、专家或模板 |
| `review_notes` | 审核备注 | `STRING` |  | `future_reserved` | 场景合理性和适用范围说明 |
| `scenario_run_mode_code` | 场景运行模式 | `STRING` |  | `future_reserved` | 因果场景、直接市场扰动、混合或模块测试 |
| `intervention_ids` | 用户干预集合 | `STRING[]` |  | `future_reserved` | 本场景包含的正式干预合同 |
| `causal_consistency_required_flag` | 是否要求因果一致 | `BOOL` |  | `future_reserved` | 是否禁止违反硬逻辑和市场制度 |
| `allow_forced_override_flag` | 是否允许强制覆盖 | `BOOL` |  | `future_reserved` | 是否允许为软件异常测试覆盖内生或输出变量 |

### 36. 企业行业与现实世界暴露（`entity_exposure`）

描述主体对地区、商品、供应链、基础设施、政策等对象的数量化脆弱性或受益敏感度。它不是事件结果；事件结果由event_impact表示，稳定结构关系由entity_relation表示。

- 标准对象：`EntityExposure`
- 字段数量：25

| 标准字段 | 中文名 | 类型 | 单位 | 阶段 | 定义 |
|---|---|---|---|---|---|
| `exposure_id` | 暴露关系ID | `STRING` |  | `future_reserved` | 暴露关系唯一标识 |
| `source_entity_id` | 暴露主体ID | `STRING` |  | `future_reserved` | 公司、行业、证券或参与者 |
| `source_entity_type_code` | 暴露主体类型 | `STRING` |  | `future_reserved` | 公司、行业、证券、组合等 |
| `target_entity_id` | 暴露对象ID | `STRING` |  | `future_reserved` | 国家、地区、商品、供应商、港口、工厂等 |
| `target_entity_type_code` | 暴露对象类型 | `STRING` |  | `future_reserved` | 地理、基础设施、供应链、商品、政策、客户或资产 |
| `exposure_type_code` | 暴露类型 | `STRING` |  | `future_reserved` | 总部、工厂、仓库、客户、供应商、能源、商品、物流、汇率、政策等 |
| `exposure_direction_code` | 暴露方向 | `STRING` |  | `future_reserved` | 正向受益、负向受损、双向或条件决定 |
| `exposure_weight` | 暴露权重 | `DOUBLE` | 0-1 | `future_reserved` | 该暴露对主体的重要程度 |
| `dependency_share_pct` | 依赖占比 | `DOUBLE` | percent_points | `future_reserved` | 收入、成本、产能、采购或销售的依赖占比 |
| `substitution_score` | 替代能力评分 | `DOUBLE` | score_0_100 | `future_reserved` | 受冲击后寻找替代来源或市场的能力 |
| `insurance_coverage_pct` | 保险覆盖比例 | `DOUBLE` | percent_points | `future_reserved` | 相关资产或损失的保险覆盖比例 |
| `inventory_buffer_days` | 库存缓冲天数 | `DOUBLE` | days | `future_reserved` | 在供应中断情况下可维持的库存时间 |
| `recovery_time_min_days` | 最短恢复时间 | `DOUBLE` | days | `future_reserved` | 受损后恢复的合理下界 |
| `recovery_time_max_days` | 最长恢复时间 | `DOUBLE` | days | `future_reserved` | 受损后恢复的合理上界 |
| `country_code` | 暴露国家代码 | `STRING` |  | `future_reserved` | 地理暴露所属国家 |
| `region_code` | 暴露地区代码 | `STRING` |  | `future_reserved` | 地理暴露所属地区 |
| `location_name` | 暴露地点名称 | `STRING` |  | `future_reserved` | 工厂、仓库、港口或市场地点 |
| `commodity_code` | 关联商品代码 | `STRING` |  | `future_reserved` | 原油、天然气、金属、农产品等 |
| `infrastructure_id` | 基础设施ID | `STRING` |  | `future_reserved` | 港口、航线、电网、通信等 |
| `supplier_id` | 供应商ID | `STRING` |  | `future_reserved` | 供应链上游主体 |
| `customer_id` | 客户ID | `STRING` |  | `future_reserved` | 主要客户主体 |
| `evidence_ids` | 暴露证据集合 | `STRING[]` |  | `future_reserved` | 年报、公告、新闻、网站或人工标注证据 |
| `exposure_confidence_score` | 暴露关系置信度 | `DOUBLE` | 0-1 | `future_reserved` | 暴露关系和权重可信程度 |
| `effective_from` | 暴露关系生效时间 | `TIMESTAMP` |  | `future_reserved` | 关系有效起点 |
| `effective_to` | 暴露关系失效时间 | `TIMESTAMP` |  | `future_reserved` | 关系有效终点 |

### 37. 因果行情生成运行（`synthetic_market`）

记录因果世界状态到市场状态、行业个股冲击及微观行情路径的生成过程

- 标准对象：`SyntheticMarketRun`
- 字段数量：24

| 标准字段 | 中文名 | 类型 | 单位 | 阶段 | 定义 |
|---|---|---|---|---|---|
| `synthetic_market_run_id` | 合成行情运行ID | `STRING` |  | `future_reserved` | 一次完整因果行情生成运行 |
| `simulation_run_id` | 仿真运行ID | `STRING` |  | `future_reserved` | 世界状态和变量传播运行ID |
| `scenario_id` | 场景ID | `STRING` |  | `future_reserved` | 本次运行使用的场景 |
| `monte_carlo_path_id` | 蒙特卡洛路径ID | `STRING` |  | `future_reserved` | 同场景下具体路径标识 |
| `generator_version` | 生成器版本 | `STRING` |  | `future_reserved` | 因果和微观行情生成器版本 |
| `causal_rule_set_id` | 因果规则集ID | `STRING` |  | `future_reserved` | 本次使用的因果规则集合 |
| `market_rule_set_id` | 市场制度规则集ID | `STRING` |  | `future_reserved` | A股或其他市场交易规则 |
| `random_seed` | 随机种子 | `LONG` |  | `future_reserved` | 确保路径可复现 |
| `configuration_hash` | 配置哈希 | `STRING` |  | `future_reserved` | 场景、变量、规则和生成参数哈希 |
| `generated_granularity_code` | 生成粒度 | `STRING` |  | `future_reserved` | 日K、分钟、分时、逐笔或订单簿 |
| `generated_start_time` | 生成行情起始时间 | `TIMESTAMP` |  | `future_reserved` | 合成行情起点 |
| `generated_end_time` | 生成行情结束时间 | `TIMESTAMP` |  | `future_reserved` | 合成行情终点 |
| `generated_instrument_count` | 生成证券数量 | `INT` | count | `future_reserved` | 本次生成的证券数量 |
| `causal_market_regime_code` | 因果推导市场状态 | `STRING` |  | `future_reserved` | 由上游因果链推导的牛熊震荡危机状态 |
| `causal_regime_confidence_score` | 市场状态置信度 | `DOUBLE` | 0-1 | `future_reserved` | 上游因果对市场大状态的置信度 |
| `path_variant_code` | 具体路径类型 | `STRING` |  | `future_reserved` | 缓慢阴跌、急跌反弹、结构性行情等 |
| `price_path_method_code` | 价格路径方法 | `STRING` |  | `future_reserved` | 状态依赖随机过程、历史块重采样或混合方法 |
| `volume_path_method_code` | 成交量路径方法 | `STRING` |  | `future_reserved` | 成交量与流动性生成方法 |
| `causal_trace_ids` | 因果追溯集合 | `STRING[]` |  | `future_reserved` | 市场状态、行业和证券路径的主要因果链 |
| `output_dataset_uri` | 输出数据集位置 | `STRING` |  | `future_reserved` | 标准字段格式的合成行情数据位置 |
| `constraint_validation_passed` | 约束校验是否通过 | `BOOL` |  | `future_reserved` | 物理、会计、制度和行情一致性是否全部通过 |
| `constraint_violation_codes` | 约束违规代码集合 | `STRING[]` |  | `future_reserved` | 发现的逻辑、交易制度或聚合一致性问题 |
| `tick_to_bar_reconciliation_passed` | 逐笔到K线汇总是否一致 | `BOOL` |  | `future_reserved` | 逐笔、分钟和日K汇总一致性 |
| `generated_at` | 生成时间 | `TIMESTAMP` |  | `future_reserved` | 系统实际生成时间 |

### 38. 合成行情通用验证（`simulation_evaluation`）

统一评估市场预测、因子挖掘、多因子选股、策略、组合、风险和整套系统在合成行情中的表现

- 标准对象：`SimulationEvaluation`
- 字段数量：27

| 标准字段 | 中文名 | 类型 | 单位 | 阶段 | 定义 |
|---|---|---|---|---|---|
| `simulation_evaluation_id` | 仿真验证ID | `STRING` |  | `future_reserved` | 一次目标模块验证记录 |
| `simulation_run_id` | 仿真运行ID | `STRING` |  | `future_reserved` | 所用因果仿真运行 |
| `synthetic_market_run_id` | 合成行情运行ID | `STRING` |  | `future_reserved` | 所用具体行情路径 |
| `scenario_id` | 场景ID | `STRING` |  | `future_reserved` | 所用场景 |
| `target_module_type_code` | 被验证模块类型 | `STRING` |  | `future_reserved` | 因子、模型、市场预测、策略、组合、风险或系统 |
| `target_module_id` | 被验证模块ID | `STRING` |  | `future_reserved` | 因子、模型或策略标识 |
| `target_module_version` | 被验证模块版本 | `STRING` |  | `future_reserved` | 目标实现版本 |
| `evaluation_status_code` | 验证状态 | `STRING` |  | `future_reserved` | 待运行、通过、警告、失败或无效 |
| `expected_regime_code` | 场景预期市场状态 | `STRING` |  | `future_reserved` | 因果引擎给出的真实状态标签 |
| `predicted_regime_code` | 模型预测市场状态 | `STRING` |  | `future_reserved` | 行情预测模型输出状态 |
| `regime_prediction_correct_flag` | 市场状态预测是否正确 | `BOOL` |  | `future_reserved` | 预测牛熊震荡危机是否命中 |
| `regime_detection_lag_days` | 市场状态识别滞后 | `DOUBLE` | days | `future_reserved` | 模型识别状态变化的滞后 |
| `factor_ic` | 合成行情因子IC | `DOUBLE` |  | `future_reserved` | 因子与未来收益的线性相关 |
| `factor_rank_ic` | 合成行情因子RankIC | `DOUBLE` |  | `future_reserved` | 因子排名与未来收益排名相关 |
| `factor_monotonicity_score` | 因子分组单调性评分 | `DOUBLE` | score_0_100 | `future_reserved` | 因子分组收益单调程度 |
| `selection_hit_rate` | 选股命中率 | `DOUBLE` | 0-1 | `future_reserved` | 因子或多因子选股命中场景受益股票比例 |
| `strategy_return_pct` | 策略收益率 | `DOUBLE` | percent_points | `future_reserved` | 该路径上的策略收益率 |
| `strategy_max_drawdown_pct` | 策略最大回撤 | `DOUBLE` | percent_points | `future_reserved` | 该路径上的最大回撤 |
| `strategy_failure_flag` | 策略是否失效 | `BOOL` |  | `future_reserved` | 是否触发预定义失效条件 |
| `tail_loss_pct` | 尾部损失 | `DOUBLE` | percent_points | `future_reserved` | 极端场景或分位数尾部损失 |
| `unfilled_order_ratio` | 未成交订单比例 | `DOUBLE` | 0-1 | `future_reserved` | 涨跌停、停牌和流动性约束下未成交比例 |
| `risk_gate_correct_flag` | 风险门控是否正确 | `BOOL` |  | `future_reserved` | 风险仓位是否在场景下做出合理限制 |
| `robustness_score` | 跨路径稳健性评分 | `DOUBLE` | score_0_100 | `future_reserved` | 同场景多路径和多状态稳定程度 |
| `failure_reason_codes` | 失败原因集合 | `STRING[]` |  | `future_reserved` | 模型、因子、策略或系统失效原因 |
| `evaluation_report_uri` | 验证报告位置 | `STRING` |  | `future_reserved` | 详细仿真验证报告位置 |
| `causal_consistency_status_code` | 因果一致性状态 | `STRING` |  | `future_reserved` | 有效、警告、已破坏或未检查 |
| `direct_market_shock_flag` | 是否直接市场冲击 | `BOOL` |  | `future_reserved` | 该验证是否包含无上游解释的市场外生注入 |

### 39. 用户场景干预合同（`scenario_intervention`）

记录用户对世界、跨资产、行业、公司、市场状态或测试输出变量施加的可审计干预

- 标准对象：`ScenarioIntervention`
- 字段数量：33

| 标准字段 | 中文名 | 类型 | 单位 | 阶段 | 定义 |
|---|---|---|---|---|---|
| `intervention_id` | 干预ID | `STRING` |  | `future_reserved` | 干预ID |
| `scenario_id` | 场景ID | `STRING` |  | `future_reserved` | 场景ID |
| `canonical_field_ref` | 限定标准字段引用 | `STRING` |  | `future_reserved` | domain_code.canonical_name |
| `canonical_field_name` | 标准字段名 | `STRING` |  | `future_reserved` | 标准字段名 |
| `target_scope_code` | 作用范围代码 | `STRING` |  | `future_reserved` | 作用范围代码 |
| `target_entity_ids` | 作用实体集合 | `STRING[]` |  | `future_reserved` | 作用实体集合 |
| `country_code` | 国家代码 | `STRING` |  | `future_reserved` | 国家代码 |
| `region_code` | 地区代码 | `STRING` |  | `future_reserved` | 地区代码 |
| `industry_id` | 行业ID | `STRING` |  | `future_reserved` | 行业ID |
| `instrument_id` | 证券ID | `STRING` |  | `future_reserved` | 证券ID |
| `intervention_mode_code` | 干预方式 | `STRING` |  | `future_reserved` | 绝对值、增量、涨跌幅、开关、路径、分布或状态冲击 |
| `value_numeric` | 干预数值 | `DOUBLE` |  | `future_reserved` | 干预数值 |
| `value_text` | 干预文本值 | `STRING` |  | `future_reserved` | 干预文本值 |
| `value_bool` | 干预布尔值 | `BOOL` |  | `future_reserved` | 干预布尔值 |
| `distribution_parameters_json` | 分布或路径参数 | `JSON` |  | `future_reserved` | 分布或路径参数 |
| `start_time` | 开始时间 | `TIMESTAMP` |  | `future_reserved` | 开始时间 |
| `end_time` | 结束时间 | `TIMESTAMP` |  | `future_reserved` | 结束时间 |
| `ramp_function_code` | 变化路径代码 | `STRING` |  | `future_reserved` | 变化路径代码 |
| `propagation_mode_code` | 传播模式 | `STRING` |  | `future_reserved` | 传播模式 |
| `priority_level` | 干预优先级 | `INT` |  | `future_reserved` | 干预优先级 |
| `conflict_policy_code` | 冲突策略 | `STRING` |  | `future_reserved` | 冲突策略 |
| `direct_market_shock_flag` | 是否直接市场冲击 | `BOOL` |  | `future_reserved` | 是否直接市场冲击 |
| `forced_override_flag` | 是否强制覆盖 | `BOOL` |  | `future_reserved` | 是否强制覆盖 |
| `override_reason` | 强制覆盖理由 | `STRING` |  | `future_reserved` | 强制覆盖理由 |
| `created_by_user_id` | 创建用户ID | `STRING` |  | `future_reserved` | 创建用户ID |
| `created_at` | 创建时间 | `TIMESTAMP` |  | `future_reserved` | 创建时间 |
| `review_status_code` | 审核状态 | `STRING` |  | `future_reserved` | 审核状态 |
| `causal_consistency_status_code` | 因果一致性状态 | `STRING` |  | `future_reserved` | 因果一致性状态 |
| `validation_messages` | 校验信息 | `STRING[]` |  | `future_reserved` | 校验信息 |
| `intervention_target_kind_code` | 干预目标种类 | `STRING` |  | `future_reserved` | 字段值、创建事件、切换事件、覆盖影响、覆盖关系或直接市场冲击 |
| `target_object_id` | 目标对象记录ID | `STRING` |  | `future_reserved` | 被修改的事件、影响、实体关系或其他标准对象ID |
| `event_template_id` | 事件模板ID | `STRING` |  | `future_reserved` | 战争、火灾、港口关闭等通用事件模板 |
| `structured_payload_json` | 结构化干预载荷 | `JSON` |  | `future_reserved` | 创建事件、影响或关系时使用的结构化参数，不以新增专用字段替代 |

### 40. 现实世界通用实体（`world_entity`）

统一表示国家、地区、行业、公司、工厂、仓库、港口、航线、能源设施、市场指数等可被事件影响或被场景操纵的对象。

- 标准对象：`WorldEntity`
- 字段数量：19

| 标准字段 | 中文名 | 类型 | 单位 | 阶段 | 定义 |
|---|---|---|---|---|---|
| `entity_id` | 通用实体ID | `STRING` |  | `future_reserved` | 跨场景和因果图稳定的实体唯一标识 |
| `entity_type_code` | 实体类型代码 | `STRING` |  | `future_reserved` | 国家、地区、行业、公司、工厂、仓库、港口、市场等 |
| `entity_name` | 实体名称 | `STRING` |  | `future_reserved` | 实体可读名称 |
| `entity_status_code` | 实体状态代码 | `STRING` |  | `future_reserved` | 正常、受限、部分运行、停运、损毁等状态 |
| `parent_entity_id` | 父实体ID | `STRING` |  | `future_reserved` | 例如仓库所属公司、地区所属国家 |
| `linked_domain_code` | 关联业务领域代码 | `STRING` |  | `future_reserved` | 关联company、classification、instrument等既有标准对象 |
| `linked_record_id` | 关联业务记录ID | `STRING` |  | `future_reserved` | 关联既有领域对象的主键 |
| `country_code` | 国家代码 | `STRING` |  | `future_reserved` | 实体所在国家 |
| `region_code` | 地区代码 | `STRING` |  | `future_reserved` | 实体所在地区 |
| `location_name` | 地点名称 | `STRING` |  | `future_reserved` | 工厂、仓库、港口或市场所在地 |
| `latitude` | 纬度 | `DOUBLE` | degrees | `future_reserved` | 实体地理纬度 |
| `longitude` | 经度 | `DOUBLE` | degrees | `future_reserved` | 实体地理经度 |
| `active_flag` | 实体是否有效 | `BOOL` |  | `future_reserved` | 实体是否处于有效生命周期 |
| `operational_status_code` | 运营状态代码 | `STRING` |  | `future_reserved` | 正常、受限、部分停产、完全停产、恢复中等 |
| `criticality_score` | 关键性评分 | `DOUBLE` | score_0_100 | `future_reserved` | 该实体对上级经济体、行业或公司的重要程度 |
| `evidence_ids` | 实体证据集合 | `STRING[]` |  | `future_reserved` | 年报、公告、官网、地图、官方资料等证据 |
| `entity_confidence_score` | 实体信息置信度 | `DOUBLE` | 0-1 | `future_reserved` | 实体身份、地点和状态的可信程度 |
| `effective_from` | 实体关系生效时间 | `TIMESTAMP` |  | `future_reserved` | 该实体记录生效起点 |
| `effective_to` | 实体关系失效时间 | `TIMESTAMP` |  | `future_reserved` | 该实体记录失效终点 |

### 41. 通用实体关系（`entity_relation`）

表达国家—行业、公司—工厂、公司—仓库、公司—供应商、企业—港口等稳定结构关系；与事件造成的动态影响分开。

- 标准对象：`EntityRelation`
- 字段数量：19

| 标准字段 | 中文名 | 类型 | 单位 | 阶段 | 定义 |
|---|---|---|---|---|---|
| `relation_id` | 实体关系ID | `STRING` |  | `future_reserved` | 实体关系唯一标识 |
| `source_entity_id` | 源实体ID | `STRING` |  | `future_reserved` | 关系起点实体 |
| `source_entity_type_code` | 源实体类型 | `STRING` |  | `future_reserved` | 源实体类型 |
| `target_entity_id` | 目标实体ID | `STRING` |  | `future_reserved` | 关系终点实体 |
| `target_entity_type_code` | 目标实体类型 | `STRING` |  | `future_reserved` | 目标实体类型 |
| `relation_type_code` | 关系类型代码 | `STRING` |  | `future_reserved` | 拥有、运营、位于、依赖、供应、客户、支柱产业等 |
| `relation_active_flag` | 关系是否有效 | `BOOL` |  | `future_reserved` | 关系当前是否生效 |
| `relation_direction_code` | 关系方向代码 | `STRING` |  | `future_reserved` | 单向、双向或无向 |
| `relation_weight` | 关系权重 | `DOUBLE` | 0-1 | `future_reserved` | 关系在传播中的基础权重 |
| `dependency_share_pct` | 依赖占比 | `DOUBLE` | percent_points | `future_reserved` | 收入、成本、产能、采购、出口或财政等依赖占比 |
| `criticality_score` | 关系关键性评分 | `DOUBLE` | score_0_100 | `future_reserved` | 该关系中断的系统重要性 |
| `substitution_score` | 替代能力评分 | `DOUBLE` | score_0_100 | `future_reserved` | 目标对象不可用时替代的难易程度 |
| `relation_metric_code` | 关系度量代码 | `STRING` |  | `future_reserved` | GDP占比、出口占比、财政占比、产能占比等 |
| `relation_metric_value` | 关系度量数值 | `DOUBLE` |  | `future_reserved` | 关系度量的具体值 |
| `relation_metric_unit_code` | 关系度量单位 | `STRING` |  | `future_reserved` | 百分比、金额、数量等统一单位 |
| `evidence_ids` | 关系证据集合 | `STRING[]` |  | `future_reserved` | 支持关系存在和权重的证据 |
| `relation_confidence_score` | 关系置信度 | `DOUBLE` | 0-1 | `future_reserved` | 关系和参数的可信程度 |
| `effective_from` | 关系生效时间 | `TIMESTAMP` |  | `future_reserved` | 关系有效起点 |
| `effective_to` | 关系失效时间 | `TIMESTAMP` |  | `future_reserved` | 关系有效终点 |

### 42. 现实世界通用事件（`world_event`）

统一表示战争、制裁、空袭、火灾、洪水、地震、停工、港口关闭、政策变化、价格冲击等事件。布尔字段只表示事件是否发生。

- 标准对象：`WorldEvent`
- 字段数量：21

| 标准字段 | 中文名 | 类型 | 单位 | 阶段 | 定义 |
|---|---|---|---|---|---|
| `event_id` | 通用事件ID | `STRING` |  | `future_reserved` | 事件唯一标识 |
| `event_type_code` | 事件类型代码 | `STRING` |  | `future_reserved` | 战争、空袭、火灾、洪水、政策、市场冲击等 |
| `event_name` | 事件名称 | `STRING` |  | `future_reserved` | 事件可读名称 |
| `event_active_flag` | 事件是否发生或生效 | `BOOL` |  | `future_reserved` | 只作为发生与否的门控，不代表影响程度 |
| `event_status_code` | 事件状态代码 | `STRING` |  | `future_reserved` | 计划、发生中、已确认、结束、取消、否定等 |
| `parent_event_id` | 父事件ID | `STRING` |  | `future_reserved` | 复杂事件链中的上级事件 |
| `event_start_time` | 事件开始时间 | `TIMESTAMP` |  | `future_reserved` | 事件开始时点 |
| `event_end_time` | 事件结束时间 | `TIMESTAMP` |  | `future_reserved` | 事件结束或预计结束时点 |
| `country_codes` | 涉及国家代码集合 | `STRING[]` |  | `future_reserved` | 事件涉及国家 |
| `region_codes` | 涉及地区代码集合 | `STRING[]` |  | `future_reserved` | 事件涉及地区 |
| `location_name` | 事件地点 | `STRING` |  | `future_reserved` | 事件发生地点 |
| `latitude` | 事件纬度 | `DOUBLE` | degrees | `future_reserved` | 事件地理纬度 |
| `longitude` | 事件经度 | `DOUBLE` | degrees | `future_reserved` | 事件地理经度 |
| `event_severity_score` | 事件严重程度评分 | `DOUBLE` | score_0_100 | `future_reserved` | 事件自身严重程度，不等同于对任一实体的损失 |
| `event_probability` | 事件发生概率 | `DOUBLE` | 0-1 | `future_reserved` | 预测或场景事件发生概率 |
| `surprise_score` | 事件突发性评分 | `DOUBLE` | score_0_100 | `future_reserved` | 相对于市场预期的意外程度 |
| `data_origin_code` | 事件值来源性质 | `STRING` |  | `future_reserved` | 真实观测、人工设定、场景假设或合成事件 |
| `source_ids` | 事件来源集合 | `STRING[]` |  | `future_reserved` | 新闻、公告、官方资料或人工场景 |
| `evidence_ids` | 事件证据集合 | `STRING[]` |  | `future_reserved` | 支持事件真实性和参数的证据 |
| `event_confidence_score` | 事件置信度 | `DOUBLE` | 0-1 | `future_reserved` | 事件真实性和范围的可信程度 |
| `scenario_id` | 所属场景ID | `STRING` |  | `future_reserved` | 仿真事件所属场景 |

### 43. 事件对实体的通用影响（`event_impact`）

表达某事件对某实体产生的具体影响。一个事件可对一个实体产生多条不同指标的影响记录。

- 标准对象：`EventImpact`
- 字段数量：25

| 标准字段 | 中文名 | 类型 | 单位 | 阶段 | 定义 |
|---|---|---|---|---|---|
| `impact_id` | 事件影响ID | `STRING` |  | `future_reserved` | 影响记录唯一标识 |
| `event_id` | 通用事件ID | `STRING` |  | `future_reserved` | 造成该影响的事件 |
| `target_entity_id` | 受影响实体ID | `STRING` |  | `future_reserved` | 国家、行业、公司、工厂、仓库、港口等 |
| `target_entity_type_code` | 受影响实体类型 | `STRING` |  | `future_reserved` | 受影响对象类型 |
| `impact_type_code` | 影响类型代码 | `STRING` |  | `future_reserved` | 物理损坏、产能损失、库存损失、成本上升、需求变化等 |
| `impact_active_flag` | 影响是否生效 | `BOOL` |  | `future_reserved` | 影响门控开关 |
| `impact_direction_code` | 影响方向代码 | `STRING` |  | `future_reserved` | 正向、负向、双向或条件决定 |
| `impact_metric_code` | 影响度量代码 | `STRING` |  | `future_reserved` | 产能损失率、库存损失率、吞吐下降率、成本变化率等 |
| `impact_value_numeric` | 影响数值 | `DOUBLE` |  | `future_reserved` | 影响度量的具体数值 |
| `impact_value_text` | 影响文本或状态值 | `STRING` |  | `future_reserved` | 部分停运、完全停运等文本或枚举 |
| `impact_unit_code` | 影响单位代码 | `STRING` |  | `future_reserved` | 百分比、天、金额、指数点等 |
| `impact_lower_numeric` | 影响区间下界 | `DOUBLE` |  | `future_reserved` | 不确定影响的合理下界 |
| `impact_upper_numeric` | 影响区间上界 | `DOUBLE` |  | `future_reserved` | 不确定影响的合理上界 |
| `impact_severity_score` | 影响严重程度评分 | `DOUBLE` | score_0_100 | `future_reserved` | 该事件对该实体的影响强度 |
| `impact_start_time` | 影响开始时间 | `TIMESTAMP` |  | `future_reserved` | 影响开始生效时点 |
| `impact_end_time` | 影响结束时间 | `TIMESTAMP` |  | `future_reserved` | 影响结束或预计结束时点 |
| `downtime_days` | 停运时长 | `DOUBLE` | days | `future_reserved` | 受影响实体无法正常运行的时间 |
| `expected_recovery_days` | 预计恢复时长 | `DOUBLE` | days | `future_reserved` | 恢复到正常或指定水平的时间 |
| `propagation_enabled` | 是否允许因果传播 | `BOOL` |  | `future_reserved` | 该影响是否继续向下游变量传播 |
| `causal_rule_ids` | 关联因果规则集合 | `STRING[]` |  | `future_reserved` | 负责继续传播该影响的已审核规则 |
| `manual_override_flag` | 是否人工覆盖 | `BOOL` |  | `future_reserved` | 影响参数是否由用户强制覆盖 |
| `data_origin_code` | 影响值来源性质 | `STRING` |  | `future_reserved` | 观测、专家、估计、推导、场景或合成 |
| `evidence_ids` | 影响证据集合 | `STRING[]` |  | `future_reserved` | 支持影响类型和程度的证据 |
| `impact_confidence_score` | 影响置信度 | `DOUBLE` | 0-1 | `future_reserved` | 影响对象、方向和数值的可信程度 |
| `scenario_id` | 所属场景ID | `STRING` |  | `future_reserved` | 影响所属仿真场景 |

### 44. 研究实验注册与生命周期（`research_experiment`）

统一登记因子、模型、市场状态、选股、策略、组合、风险和CWMS实验；保存假设、数据与代码版本、时间切分、成本容量、结果、失败原因和晋级状态。

- 标准对象：`ResearchExperiment`
- 字段数量：38

| 标准字段 | 中文名 | 类型 | 单位 | 阶段 | 定义 |
|---|---|---|---|---|---|
| `experiment_id` | 实验ID | `STRING` |  | `near_term` | 研究实验唯一标识 |
| `experiment_name` | 实验名称 | `STRING` |  | `near_term` | 实验可读名称 |
| `research_question` | 研究问题 | `STRING` |  | `near_term` | 本次实验需要回答的明确问题 |
| `hypothesis_text` | 研究假设 | `STRING` |  | `near_term` | 实验开始前登记的可证伪假设 |
| `target_module_type_code` | 目标模块类型 | `STRING` |  | `near_term` | 因子、模型、市场状态、策略、组合、风险或执行 |
| `target_module_id` | 目标模块ID | `STRING` |  | `near_term` | 被研究对象的唯一标识 |
| `experiment_status_code` | 实验运行状态 | `STRING` |  | `near_term` | 计划、运行、完成、失败、失效或归档 |
| `promotion_stage_code` | 研究晋级阶段 | `STRING` |  | `near_term` | 想法、研究、验证、模拟盘、有限实盘、实盘、暂停或退役 |
| `approval_status_code` | 实验审批状态 | `STRING` |  | `future_reserved` | 待审、通过、拒绝或需复核 |
| `data_snapshot_id` | 数据快照ID | `STRING` |  | `near_term` | 本次实验使用的数据快照 |
| `data_version` | 数据版本 | `STRING` |  | `near_term` | 数据集或数据库版本 |
| `field_dictionary_version` | 字段字典版本 | `STRING` |  | `near_term` | 本次实验使用的字段字典版本 |
| `feature_set_version` | 特征集合版本 | `STRING` |  | `near_term` | 因子或特征集合版本 |
| `model_version` | 模型版本 | `STRING` |  | `near_term` | 模型实现和参数版本 |
| `strategy_version` | 策略版本 | `STRING` |  | `near_term` | 策略逻辑版本 |
| `code_commit_hash` | 代码提交哈希 | `STRING` |  | `near_term` | 可复现本次实验的Git提交 |
| `configuration_hash` | 配置哈希 | `STRING` |  | `near_term` | 参数和配置内容哈希 |
| `random_seed` | 随机种子 | `LONG` |  | `near_term` | 实验和模型随机种子 |
| `train_start_date` | 训练开始日期 | `DATE` |  | `near_term` | 训练集起始日期 |
| `train_end_date` | 训练结束日期 | `DATE` |  | `near_term` | 训练集结束日期 |
| `validation_start_date` | 验证开始日期 | `DATE` |  | `near_term` | 验证集起始日期 |
| `validation_end_date` | 验证结束日期 | `DATE` |  | `near_term` | 验证集结束日期 |
| `test_start_date` | 测试开始日期 | `DATE` |  | `near_term` | 样本外测试起始日期 |
| `test_end_date` | 测试结束日期 | `DATE` |  | `near_term` | 样本外测试结束日期 |
| `walk_forward_config_json` | 滚动验证配置 | `JSON` |  | `near_term` | Walk-forward切分和重训配置 |
| `benchmark_id` | 基准ID | `STRING` |  | `near_term` | 实验比较基准 |
| `cost_model_version` | 成本模型版本 | `STRING` |  | `near_term` | 手续费、滑点和市场冲击模型版本 |
| `capacity_model_version` | 容量模型版本 | `STRING` |  | `near_term` | 流动性和容量评估模型版本 |
| `primary_metric_code` | 主要评价指标 | `STRING` |  | `near_term` | 实验预先指定的主要评价指标 |
| `primary_metric_value` | 主要指标结果 | `DOUBLE` |  | `near_term` | 主要评价指标实际结果 |
| `negative_result_flag` | 是否负面结果 | `BOOL` |  | `near_term` | 实验未支持假设或成本后失效 |
| `failure_reason_codes` | 失败原因集合 | `STRING[]` |  | `near_term` | 数据、泄漏、成本、容量、稳定性或实现问题 |
| `conclusion_text` | 实验结论 | `STRING` |  | `near_term` | 结构化指标之外的实验结论 |
| `next_action_code` | 下一步动作 | `STRING` |  | `near_term` | 继续研究、修改、晋级、暂停或退役 |
| `created_at` | 实验创建时间 | `TIMESTAMP` |  | `near_term` | 实验登记时间 |
| `completed_at` | 实验完成时间 | `TIMESTAMP` |  | `near_term` | 实验结束时间 |
| `reviewed_by` | 复核人或复核主体 | `STRING` |  | `future_reserved` | 人工或系统复核主体 |
| `review_notes` | 复核备注 | `STRING` |  | `future_reserved` | 晋级或拒绝依据 |

### 45. 订单成交持仓资金账实核对（`execution_reconciliation`）

核对系统本地订单、成交、持仓、现金和费用与券商实际记录，发现差异时阻止继续自动交易或要求人工处理。

- 标准对象：`ExecutionReconciliation`
- 字段数量：28

| 标准字段 | 中文名 | 类型 | 单位 | 阶段 | 定义 |
|---|---|---|---|---|---|
| `reconciliation_run_id` | 核对运行ID | `STRING` |  | `future_reserved` | 一次账实核对运行唯一标识 |
| `account_id` | 账户ID | `STRING` |  | `future_reserved` | 被核对账户 |
| `broker_code` | 券商代码 | `STRING` |  | `future_reserved` | 券商或交易通道 |
| `trade_date` | 交易日期 | `DATE` |  | `future_reserved` | 核对所属交易日 |
| `environment_code` | 运行环境 | `STRING` |  | `future_reserved` | 研究、回测、模拟盘或实盘 |
| `reconciliation_scope_code` | 核对范围 | `STRING` |  | `future_reserved` | 订单、成交、持仓、现金、费用或全量 |
| `local_order_count` | 本地订单数量 | `INT` | count | `future_reserved` | 本地系统记录订单数 |
| `broker_order_count` | 券商订单数量 | `INT` | count | `future_reserved` | 券商侧订单数 |
| `local_fill_count` | 本地成交数量 | `INT` | count | `future_reserved` | 本地成交回报数量 |
| `broker_fill_count` | 券商成交数量 | `INT` | count | `future_reserved` | 券商侧成交数量 |
| `local_position_count` | 本地持仓证券数 | `INT` | count | `future_reserved` | 本地持仓证券数量 |
| `broker_position_count` | 券商持仓证券数 | `INT` | count | `future_reserved` | 券商侧持仓证券数量 |
| `local_cash_balance_cny` | 本地现金余额 | `DOUBLE` | CNY | `future_reserved` | 本地系统记录现金 |
| `broker_cash_balance_cny` | 券商现金余额 | `DOUBLE` | CNY | `future_reserved` | 券商实际现金 |
| `cash_difference_cny` | 现金差异 | `DOUBLE` | CNY | `future_reserved` | 本地与券商现金差异 |
| `position_difference_count` | 持仓差异数量 | `INT` | count | `future_reserved` | 存在数量或成本差异的证券数 |
| `order_difference_count` | 订单差异数量 | `INT` | count | `future_reserved` | 订单状态或数量差异数 |
| `fill_difference_count` | 成交差异数量 | `INT` | count | `future_reserved` | 成交记录差异数 |
| `fee_difference_cny` | 费用差异 | `DOUBLE` | CNY | `future_reserved` | 手续费、税费和其他费用差异 |
| `reconciliation_status_code` | 核对状态 | `STRING` |  | `future_reserved` | 待核对、完全一致、不一致、阻断或已解决 |
| `discrepancy_codes` | 差异代码集合 | `STRING[]` |  | `future_reserved` | 订单、成交、持仓、现金或费用差异 |
| `discrepancy_details_json` | 差异详情 | `JSON` |  | `future_reserved` | 逐项差异内容 |
| `blocking_flag` | 是否阻断交易 | `BOOL` |  | `future_reserved` | 发现重大差异时禁止新交易 |
| `manual_resolution_required` | 是否需要人工处理 | `BOOL` |  | `future_reserved` | 是否必须人工核查并确认 |
| `resolved_at` | 解决时间 | `TIMESTAMP` |  | `future_reserved` | 差异解决时间 |
| `resolution_text` | 解决说明 | `STRING` |  | `future_reserved` | 差异原因和处理方式 |
| `source_snapshot_id` | 券商快照ID | `STRING` |  | `future_reserved` | 用于核对的券商侧快照 |
| `created_at` | 核对创建时间 | `TIMESTAMP` |  | `future_reserved` | 核对记录生成时间 |

### 46. 分类节点市场快照（`classification_market`）

行业、概念、指数、主题或地区等分类节点在交易日和市场阶段上的聚合行情、广度、成交与估值快照；不得与ClassificationMembership成员关系混用

- 标准对象：`ClassificationMarketSnapshot`
- 字段数量：33

| 标准字段 | 中文名 | 类型 | 单位 | 阶段 | 定义 |
|---|---|---|---|---|---|
| `classification_system` | 分类体系 | `STRING` |  | `core` | 分类节点所属体系；来源暂未提供权威体系时可使用明确版本化的来源体系代码 |
| `classification_version` | 分类体系版本 | `STRING` |  | `core` | 分类体系版本；来源未提供时为空 |
| `classification_type` | 分类类型 | `STRING` |  | `core` | INDUSTRY/CONCEPT/INDEX/THEME/REGION/OTHER |
| `node_id` | 分类节点ID | `STRING` |  | `core` | 分类体系内稳定节点标识；临时哈希ID必须通过质量标记说明且不得冒充跨供应商统一ID |
| `node_code` | 分类节点代码 | `STRING` |  | `core` | 来源或主数据提供的分类节点代码 |
| `node_name_cn` | 分类节点中文名 | `STRING` |  | `core` | 分类节点中文名称 |
| `node_level` | 分类层级 | `INT` |  | `core` | 分类节点层级；来源未提供时为空 |
| `parent_node_id` | 父节点ID | `STRING` |  | `core` | 父分类节点标识；来源未提供时为空 |
| `trade_date` | 交易日期 | `DATE` |  | `core` | 聚合市场快照所属交易日 |
| `snapshot_phase` | 市场快照阶段 | `STRING` |  | `core` | CLOSE、OPENING_AUCTION等市场阶段；阶段不等于精确时间戳 |
| `pct_change_pct` | 节点涨跌幅 | `DOUBLE` | percent_points | `core` | 分类节点聚合涨跌幅 |
| `return_3d_pct` | 三日收益率 | `DOUBLE` | percent_points | `core` | 分类节点三日聚合收益率 |
| `return_5d_pct` | 五日收益率 | `DOUBLE` | percent_points | `core` | 分类节点五日聚合收益率 |
| `return_10d_pct` | 十日收益率 | `DOUBLE` | percent_points | `core` | 分类节点十日聚合收益率 |
| `return_20d_pct` | 二十日收益率 | `DOUBLE` | percent_points | `core` | 分类节点二十日聚合收益率 |
| `speed_pct` | 涨速 | `DOUBLE` | percent_points | `core` | 来源报告的分类节点涨速 |
| `leading_instrument_id` | 领涨证券统一标识 | `STRING` |  | `core` | 领涨证券统一标识；来源只提供名称且无法可靠解析时为空 |
| `leading_instrument_name_cn` | 领涨证券中文名 | `STRING` |  | `core` | 来源报告的领涨证券中文名称 |
| `up_count` | 上涨成分数量 | `INT` | count | `core` | 分类节点内上涨成分数量 |
| `down_count` | 下跌成分数量 | `INT` | count | `core` | 分类节点内下跌成分数量 |
| `limit_up_count` | 涨停成分数量 | `INT` | count | `core` | 分类节点内涨停成分数量 |
| `breadth_ratio` | 涨跌家数比 | `DOUBLE` | ratio | `core` | 上涨成分数量与下跌成分数量之比；全涨、全跌等不可用单一数值表达的状态由breadth_status记录 |
| `breadth_status` | 市场广度状态 | `STRING` |  | `core` | NORMAL/ALL_UP/ALL_DOWN/RATIO_MISMATCH_WARNING/UNKNOWN |
| `turnover_rate_pct` | 节点换手率 | `DOUBLE` | percent_points | `core` | 分类节点聚合换手率 |
| `volume_ratio` | 节点量比 | `DOUBLE` | ratio | `core` | 分类节点聚合量比 |
| `turnover_3d_pct` | 三日换手率 | `DOUBLE` | percent_points | `core` | 分类节点三日聚合换手率 |
| `volume_lots` | 节点成交量（手） | `DOUBLE` | lots | `core` | 分类节点聚合成交量（手） |
| `volume_shares` | 节点成交量（股） | `LONG` | shares | `core` | 由确认的手数口径乘以100得到的分类节点聚合成交量（股）；单位未确认时不得生成 |
| `amount_cny` | 节点成交额 | `DECIMAL` | CNY | `core` | 分类节点聚合成交额 |
| `total_market_cap_cny` | 节点总市值 | `DECIMAL` | CNY | `core` | 分类节点成分证券总市值聚合 |
| `float_market_cap_cny` | 节点流通市值 | `DECIMAL` | CNY | `core` | 分类节点成分证券流通市值聚合 |
| `average_return_pct` | 成分平均收益率 | `DOUBLE` | percent_points | `core` | 分类节点成分证券平均收益率 |
| `pe_ratio` | 节点市盈率 | `DOUBLE` | ratio | `core` | 来源报告的分类节点市盈率口径 |
