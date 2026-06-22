# TASK_007_DOLPHINDB_ADJUSTMENT_LAYERS.md

## 修订原因

Windows 可以完整读取目标 Level File，原文件与复制文件的 SHA256 一致；
`getTSDBSortKeyEntry` 也成功返回该文件中的 sort key 条目。

因此没有证据表明文件丢失或无法读取。此前错误更像是在全表宽扫描期间
出现的偶发文件打开失败或资源竞争。

## 修订方案

- 全局复权统计改为按股票代码分批；
- 四个复权公式分层在同一个批次查询中计算；
- 默认每批100只股票；
- 股票代码列表只读取一次并缓存；
- 因子变化核验继续分批；
- 对 `Can't open file` 最多执行2次短暂只读重试；
- 持续失败时立即停止并保留原始报错；
- 不修改、删除或重建DolphinDB数据。

## 自动测试

```powershell
python -m compileall src tests
python -m unittest discover -s tests -v
```

## 真实运行

```powershell
$env:PYTHONPATH="src"

python -m a_stock_quant.dolphindb_adjustment_layers `
  --database-uri "dfs://A_STOCK_DAILY_K_DB" `
  --table "stock_daily_k" `
  --factor-chunk-size 100 `
  --output "reports/task_007_adjustment_layers.json"
```

仍出现资源压力时，把 `--factor-chunk-size` 调整为50。

## 安全边界

- 全部查询只读；
- 不删除 Level File；
- 不删除分区；
- 不调用强制恢复或清理函数；
- 不把密码写入项目文件。
