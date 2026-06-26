# TASK_017A Canonical缺口审查

## 可以继续设计的来源

| 来源 | 目标对象 | 状态 |
|---|---|---|
| hq | DailyBar | READY_WITH_WARNING |
| zj | MoneyFlowSnapshot | READY_WITH_WARNING |

`hq`只能作为补充和对账数据集，不能覆盖已有权威日K。

## 被阻断的来源

| 来源 | 原因 |
|---|---|
| kphq | AuctionSnapshot要求精确snapshot_time，但来源没有可靠时间 |
| hy | 缺少ClassificationMarketSnapshot |
| gn | 缺少ClassificationMarketSnapshot |
| kphy | 缺少ClassificationMarketSnapshot |
| kpgn | 缺少ClassificationMarketSnapshot |

## 必须禁止

- 把`source_file_mtime_utc`当成市场快照时间；
- 把`ingested_at_utc`当成市场快照时间；
- 自动填入09:25；
- 自动填入交易日午夜；
- 把分类聚合行情写成成员关系。

## 推荐顺序

1. 新增`ClassificationMarketSnapshot`字典对象；
2. 处理AuctionSnapshot日期级来源的时间精度治理；
3. 再开发只读Canonical服务；
4. 最后接入StandardDataService并做真实库验收。
