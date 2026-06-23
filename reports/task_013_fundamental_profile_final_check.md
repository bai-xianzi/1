# TASK_013 基本面快照画像检查

- 数据库：`dfs://A_STOCK_FUNDAMENTAL_DB`
- 表：`stock_fundamental_snapshot`
- 生成时间：`2026-06-23T12:06:10.564566+00:00`
- 状态：`QualityStatus.PENDING_CONFIRMATION`
- 阻断严格历史回测：`True`
- 允许当前快照研究：`True`

## 结构与覆盖

- 实际字段数：54
- 总行数：5541
- 股票数：5541
- 快照范围：2026-06-19T00:00:00 至 2026-06-19T00:00:00
- 重复额外行数：0

## 关键异常

- `key_null_count`：0
- `update_after_snapshot_count`：0
- `listing_after_snapshot_count`：0
- `negative_total_shares_count`：0
- `negative_circulating_shares_count`：0
- `circulating_above_total_count`：0
- `nonpositive_total_assets_count`：0
- `source_file_null_count`：0
- `imported_at_null_count`：0

## 单位候选

- 千元人民币 + 万股公式匹配率：0.880065
- 万元人民币 + 万股公式匹配率：0.000543

## 待确认事项

- **FUNDAMENTAL_REPORT_PERIOD**：来源report_period是3/6/9/12月码、季度码还是其他枚举？
- **FUNDAMENTAL_AVAILABLE_AT**：update_date是否等于正式公告日期，还是供应商内部更新日期？
- **FUNDAMENTAL_MONEY_UNIT**：资产、收入、利润和现金流字段是否以千元人民币计量？
- **FUNDAMENTAL_SHARE_UNIT**：total_shares、b_shares、h_shares和circulating_a_shares是否以万股计量？
- **FUNDAMENTAL_PROFIT_SCOPE**：after_tax_profit是否为公司整体净利润，net_profit是否为归母净利润？
- **FUNDAMENTAL_EQUITY_SCOPE**：net_assets是所有者权益合计，还是归母所有者权益？
- **FUNDAMENTAL_TOTAL_CASH_FLOW**：total_cash_flow的准确会计含义是什么？
- **FUNDAMENTAL_ZPG**：zpg字段的全称、单位和口径是什么？
- **FUNDAMENTAL_COMPANY_ID**：FundamentalSnapshot要求company_id，当前来源只有stock_code；需要统一公司身份解析规则。
- **CLASSIFICATION_HISTORY**：来源行业和申万行业字段缺少分类版本与有效起止时间，当前只能视为snapshot_date观察到的分类。
- **INSTRUMENT_ID_FORMAT**：当前日K使用6位stock_code作为instrument_id；基本面必须保持一致，未来如升级为000001.SZ需统一迁移。

## 结论

该数据集可以继续完成标准映射和Provider开发，但在公告日期、报告期、单位和利润口径确认前，不得用于严格历史点时回测。
