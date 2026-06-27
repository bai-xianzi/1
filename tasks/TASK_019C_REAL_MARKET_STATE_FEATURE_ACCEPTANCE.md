# TASK_019C 真实DolphinDB市场状态特征验收

## 目标

使用真实DolphinDB、统一Provider、八维就绪度门禁和TASK_019A/B合同，完成日K与行业快照共同交易日上的15项可解释特征验收。

## 真实调用链

```text
DolphinDB只读查询
→ StandardDataService
→ ReadinessGatedStandardDataService
→ MarketStateInputContractEngine
→ ExplainableMarketStateFeatureCalculator
→ MarketStateFeatureSnapshot
```

## 日期策略

```text
LATEST_COMMON_TRADE_DATE
```

先从`hy`来源扫描最近日期，再逐日验证日K是否存在相同交易日。不得把不同日期的数据拼成同一特征快照。

## 验收集合

```text
DETERMINISTIC_CAPPED_REAL_QUERY_UNIVERSE
```

- 日K最多30个证券；
- 行业快照最多30个实体；
- 按来源实体ID升序选择；
- 仅用于真实端到端计算验收；
- 不声明全市场全集覆盖。

## 验收要求

- 两个Provider真实查询均可用；
- 两个查询均通过用途级统一门禁；
- 输入合同状态为`READY`或`READY_WITH_WARNINGS`；
- 特征快照状态为`READY`或`READY_WITH_WARNINGS`；
- 生成15项特征和5个必需特征族；
- 保留2个来源查询ID；
- 保留Provider、就绪度和特征WARNING；
- 数据库只读；
- 数据库写操作为0；
- 不生成市场状态标签、仓位或交易信号。

## 本任务不做

- 不声明当前市场是牛市、熊市或震荡市；
- 不设定牛熊阈值；
- 不提供人工交易建议；
- 不训练模型；
- 不修改DolphinDB。
