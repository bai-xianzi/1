# TASK_017B 字典变更验收报告

## 已实施

### ClassificationMarketSnapshot

新增独立分类市场快照对象，覆盖分类体系、节点身份、交易日期、
快照阶段、收益、市场广度、成交、市值和估值。它与
`ClassificationMembership`的成员关系语义明确分离。

### AuctionSnapshot时间精度

- `snapshot_time`改为可空；
- 新增非空`snapshot_time_precision`；
- 日期级来源使用`DATE_ONLY`；
- 日期级记录的`snapshot_time`必须为空；
- 禁止文件修改时间、入库时间、午夜或固定09:25回填。

## 暂不提升为Canonical

`average_shares`来源单位尚未确认，继续保留在`source_extensions`，
避免把未知单位字段错误命名为“股”。

## 结论

TASK_017A的5个阻断项已通过字典0.6.0解决。七类映射均可进入后续
只读Canonical服务开发，但仍必须携带质量标记和完整血缘。
