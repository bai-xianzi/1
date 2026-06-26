# TASK_017 七类日线资金标准接入验收

- 状态：**PASSED_WITH_WARNINGS**
- 数据库：`dfs://A_STOCK_DAILY_FUNDS_DB`
- 字段字典：`0.6.0`
- Canonical服务：`0.1.0`
- 映射合同：`0.2.0`
- 来源数据集：7
- Provider：7
- 统一真实查询：7
- 严格历史用途阻断：7
- 数据库写操作：0

## 对象和选择器

| 来源 | 选择器 | Canonical对象 |
|---|---|---|
| hq | INSTRUMENT_ID | DailyBar |
| kphq | INSTRUMENT_ID | AuctionSnapshot |
| zj | INSTRUMENT_ID | MoneyFlowSnapshot |
| hy | ENTITY_ID | ClassificationMarketSnapshot |
| gn | ENTITY_ID | ClassificationMarketSnapshot |
| kphy | ENTITY_ID | ClassificationMarketSnapshot |
| kpgn | ENTITY_ID | ClassificationMarketSnapshot |

## 结论

七类来源已经通过统一`StandardDataService`真实只读验收。
当前快照研究可以使用，但必须保留WARNING；同日人工辅助决策、
严格历史回测和历史模型训练继续阻断。

## 下一任务

`TASK_018`：统一数据质量门禁与数据就绪度服务。
