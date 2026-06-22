# TASK_006_DOLPHINDB_DAILY_K_SEMANTICS.md

## 本次修订原因

全表异常核验同时执行 `context by`、`move`、多列和多个派生标志，
在约1655万行数据上导致DolphinDB服务器内存不足。

## 修订方案

- 先只读取得股票代码列表；
- 按股票代码分批执行异常核验；
- 默认每批100只股票；
- 每批只加载核验所需字段；
- 在Python端汇总各批统计；
- 每批最多取5条异常样例，最终保留误差最大的50条；
- 不创建临时表，不写入数据库。

## 文件

- `src/a_stock_quant/dolphindb_daily_semantics.py`
- `tests/test_dolphindb_daily_semantics.py`
- `tasks/TASK_006_DOLPHINDB_DAILY_K_SEMANTICS.md`

## 自动测试

```powershell
python -m compileall src tests
python -m unittest discover -s tests -v
```

## 真实运行

```powershell
$env:PYTHONPATH="src"

python -m a_stock_quant.dolphindb_daily_semantics `
  --database-uri "dfs://A_STOCK_DAILY_K_DB" `
  --table "stock_daily_k" `
  --anomaly-chunk-size 100 `
  --output "reports/task_006_daily_k_semantics.json"
```

内存仍不足时，可将批次调小：

```powershell
--anomaly-chunk-size 50
```

允许范围为1到500。批次越小，内存占用越低，但查询次数越多。

## 安全边界

- 全部查询只读；
- 不修改DolphinDB；
- 不在代码或Git中保存密码；
- 语义未完全确认前继续阻断正式因子和回测。
