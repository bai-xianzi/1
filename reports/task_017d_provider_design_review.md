# TASK_017D 统一入口设计审查

## 决策

统一查询合同保留`instrument_ids`以兼容现有日K和基本面Provider，并新增
`entity_ids`承载行业、概念等非证券实体。两者互斥，Provider通过
`selector_mode`声明所需选择器。

## Provider清单

| 来源 | 选择器 | Canonical对象 |
|---|---|---|
| hq | INSTRUMENT_ID | DailyBar |
| kphq | INSTRUMENT_ID | AuctionSnapshot |
| hy | ENTITY_ID | ClassificationMarketSnapshot |
| gn | ENTITY_ID | ClassificationMarketSnapshot |
| kphy | ENTITY_ID | ClassificationMarketSnapshot |
| kpgn | ENTITY_ID | ClassificationMarketSnapshot |
| zj | INSTRUMENT_ID | MoneyFlowSnapshot |

## 风险控制

当前七类来源没有精确`available_at`。因此统一Provider不会向严格历史回测或
历史模型训练放行，也不会对同日人工决策声称可证明可见。
