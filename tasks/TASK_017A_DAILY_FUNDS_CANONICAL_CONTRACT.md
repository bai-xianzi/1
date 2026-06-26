# TASK_017A 七类日线资金Canonical接入合同与字典缺口审查

## 目标

在开发DolphinDB只读标准化服务前，先冻结七类来源到Canonical对象的
语义边界、单位变换、质量标记、来源扩展和阻断项。

## 结论

- `hq`可作为`DailyBar`补充与对账来源，但不得替代权威日K；
- `zj`可进入`MoneyFlowSnapshot`，资金流口径仍带WARNING；
- `kphq`因缺少可证明的精确快照时间，被Schema缺口阻断；
- `hy/gn/kphy/kpgn`是分类节点聚合行情，不是
  `ClassificationMembership`；
- 字典需要新增`ClassificationMarketSnapshot`；
- 不得使用文件修改时间、入库时间、午夜或常量09:25伪造竞价时间。

## 本任务不做

- 不连接DolphinDB；
- 不修改数据库；
- 不改字段字典；
- 不接入StandardDataService；
- 不开发因子、模型、回测或交易。

## 后续拆分

- TASK_017B：批准并实施字段字典变更；
- TASK_017C：三张Raw表只读标准化服务；
- TASK_017D：StandardDataService Provider与真实抽样验收。
