# TASK_008：数据更新链路与最新日期核验

## 一、任务定位

本任务不把 DolphinDB 当作实时行情库，也不把“距今天多少天”作为故障。

当前日K数据是人工下载和逐步导入的快照数据，已确认截止日期为：

`2026-05-29`

本任务负责把这个事实固化为可复用的数据集覆盖边界，并为未来增量导入提供核验入口。

## 二、新增能力

1. 核验数据库最大日期是否等于人工声明截止日期；
2. 把数据集模式记录为 `SNAPSHOT`；
3. 生成稳定的覆盖版本，例如：
   `a_stock_daily_k@2026-05-29`；
4. 记录允许查询的起止日期；
5. 可选扫描源文件目录，从文件名提取最新日期；
6. 可选记录导入成功和失败日志的状态；
7. 当源文件日期晚于数据库日期时，提示存在待导入数据；
8. 日历滞后只作为信息，不阻断快照数据使用。

## 三、新增文件

- `src/a_stock_quant/dolphindb_dataset_coverage.py`
- `tests/test_dolphindb_dataset_coverage.py`
- `tasks/TASK_008_DATASET_COVERAGE_AND_UPDATE_CHAIN.md`

## 四、自动测试

```powershell
python -m compileall src tests
python -m unittest discover -s tests -v
```

预期：70个测试全部通过。

## 五、当前日K数据运行命令

```powershell
$env:PYTHONPATH="src"

python -m a_stock_quant.dolphindb_dataset_coverage `
  --dataset-id "a_stock_daily_k" `
  --database-uri "dfs://A_STOCK_DAILY_K_DB" `
  --table "stock_daily_k" `
  --date-field "trade_date" `
  --entity-field "stock_code" `
  --declared-cutoff-date "2026-05-29" `
  --output "reports/task_008_dataset_coverage.json"
```

## 六、可选源文件和日志盘点

以后准备增量导入时，可追加：

```powershell
  --source-dir "D:\你的日K源文件目录" `
  --import-log "D:\你的导入工具\logs\import_success.csv" `
  --import-log "D:\你的导入工具\logs\import_failed.csv"
```

`--source-dir` 和 `--import-log` 都可以重复使用。

## 七、验收标准

当前日K数据应得到：

- `dataset_mode = SNAPSHOT`
- `declared_cutoff_date = 2026-05-29`
- `database_max_date = 2026-05-29`
- `database_matches_declared_cutoff = true`
- `overall_status = PASSED`
- `blocks_downstream = false`

## 八、与后续通用适配器的关系

本报告以后会进入数据集注册表，作为每个 DolphinDB 数据集的：

- 覆盖边界；
- 数据版本；
- 增量导入起点；
- 查询范围门禁；
- 映射和血缘的上游元数据。

本任务不负责字段映射。完成后进入通用 DolphinDB 数据集注册与标准字段映射引擎。


## 九、兼容性修订

DolphinDB 3.00.5 将 `count(distinct stock_code)` 解析为嵌套聚合，
会返回 `Cannot nest aggregate function`。

修订后分为两个只读查询：

1. 查询总行数、最早日期、最晚日期；
2. 对 `select distinct stock_code` 的结果单独计数。

该修订不改变数据，不改变覆盖边界判定逻辑。
