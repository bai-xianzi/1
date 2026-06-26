# TASK_017C 三张DolphinDB Raw表只读Canonical标准化服务

## 目标

为TASK_016建立的三张主Raw表提供统一只读语义服务：

- `security_market_snapshot_raw`；
- `classification_market_snapshot_raw`；
- `money_flow_snapshot_raw`。

输出四类Canonical对象：

- `DailyBar`；
- `AuctionSnapshot`；
- `ClassificationMarketSnapshot`；
- `MoneyFlowSnapshot`。

## 关键能力

- 七类来源使用一套合同驱动转换引擎；
- 数据库查询只允许`select`；
- 证券和分类节点使用通用`entity_ids`，不混淆身份；
- 分类节点名称生成稳定、可重现的临时`node_id`；
- 日期级竞价来源保持`snapshot_time=NULL`和`DATE_ONLY`；
- 手转换为股时要求结果可安全转换为整数；
- 资金流桶保留来源正负号并派生总净流入；
- 来源扩展、Raw证据、质量标记和字段级血缘完整保留；
- 同一Canonical主键的多个Raw修订保留最新入库版本；
- 已知隔离日期显式写入批次警告。

## 边界

本任务不修改DolphinDB，不写Canonical物理表，不接入
`StandardDataService`，不开发因子、策略、回测或交易。

## 下一任务

TASK_017D需要向后兼容地扩展统一查询合同，使分类节点可以通过
generic entity IDs查询，而不是错误复用`instrument_ids`，随后注册七个
StandardDataService Provider并完成统一入口真实验收。
