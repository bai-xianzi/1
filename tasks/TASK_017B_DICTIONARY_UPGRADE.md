# TASK_017B 字段字典升级：分类市场快照与时间精度治理

## 目标

批准并实施TASK_017A识别出的两个非破坏性字典变更：

1. 新增`ClassificationMarketSnapshot`，把行业、概念等聚合行情与
   `ClassificationMembership`成员关系分离；
2. 允许`AuctionSnapshot.snapshot_time`在日期级来源中为空，并新增
   非空`snapshot_time_precision`，禁止伪造09:25等精确时刻。

## 字典结果

- 修订：0.6.0；
- 领域：46；
- 字段出现次数：1,235；
- 核心字段：744；
- 近期字段：50；
- 远期预留字段：441。

## 来源合同结果

七类来源全部进入`READY_WITH_WARNING`：

- hq：补充与对账DailyBar；
- kphq：日期级AuctionSnapshot；
- hy/gn/kphy/kpgn：ClassificationMarketSnapshot；
- zj：MoneyFlowSnapshot。

## 安全边界

- 本任务不连接DolphinDB；
- 不修改Raw表；
- 不开发Provider；
- `average_shares`因来源单位未确认继续保留为source extension；
- 领涨股只有名称时不得虚构统一证券ID；
- 临时节点哈希不得冒充跨供应商统一ID。
