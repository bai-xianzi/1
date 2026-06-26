# TASK_016B 七类日线资金 DolphinDB Raw 层

## 目标

把TASK_016A门禁通过的七类日线资金写入：

- `dfs://A_STOCK_DAILY_FUNDS_DB`
- `security_market_snapshot_raw`
- `classification_market_snapshot_raw`
- `money_flow_snapshot_raw`
- `ingest_batch_log`
- `ingest_file_log`
- `quarantine_file_log`

## 分区与幂等

- 引擎：TSDB；
- 分区列：`snapshot_month` / `batch_month`；
- 分区域：1990.01M至2100.12M；
- 主Raw表排序列：
  `dataset_id, source_file_sha256, source_row_number`；
- `keepDuplicates=LAST`；
- 同一源文件重跑不会重复累计；
- 新哈希的修订文件仍可保留为新的Raw版本。

## 四种运行模式

1. `contract`：本地合同和DDL计划检查，不连接DolphinDB；
2. `probe`：只读检查连接、版本和目标对象是否存在；
3. `create`：仅创建缺失对象，不删除或覆盖；
4. `import`：重跑TASK_016A门禁后逐文件写入和验收。

## 安全门禁

- 预导入状态必须是READY或READY_WITH_QUARANTINE；
- 默认计划写入行必须仍为461,966；
- 未知Schema、畸形行、重复键、标准化错误阻断；
- 文件哈希在预导入后变化时阻断；
- 每个文件写入后按哈希回查行数；
- 隔离文件哈希在主Raw表中必须为0行；
- 部分已有目标表时拒绝自动建表；
- 已有表结构不一致时拒绝写入；
- 不调用dropDatabase或dropTable。

## 当前阶段

先运行`probe`。确认服务器和目标数据库状态后，
再分别执行`create`和`import`。
