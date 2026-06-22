# TASK_005_DOLPHINDB_DAILY_K_PROFILE.md

## 任务目标

对 `dfs://A_STOCK_DAILY_K_DB/stock_daily_k` 执行只读画像和第一轮质量验收。

## 新增能力

- 全表总行数、股票数量、日期范围；
- 所有安全字段的空值数；
- `stock_code + trade_date` 重复情况；
- OHLC逻辑异常；
- `price_change` 与前收盘差额的一致性；
- `pct_change` 常规公式与反向公式诊断；
- `amount / volume` 数量级画像；
- `adj_factor`、`adj_price` 覆盖情况；
- 结构化检查和待确认事项；
- JSON报告输出。

## 安全边界

- 只允许单条 `select` 或 `exec` 查询；
- 拒绝分号、注释、写入及结构变更关键字；
- 不写入、不删除、不修改DolphinDB；
- 不自动修复异常；
- 不猜测复权和单位；
- 不把真实密码写入代码或Git。

## 文件

- `src/a_stock_quant/dolphindb_adapter.py`
- `src/a_stock_quant/dolphindb_daily_profile.py`
- `tests/test_dolphindb_daily_profile.py`
- `tasks/TASK_005_DOLPHINDB_DAILY_K_PROFILE.md`

## 自动测试

```powershell
python -m compileall src tests
python -m unittest discover -s tests -v
```

预期：40个测试全部通过。

## 真实运行

```powershell
$env:PYTHONPATH="src"

python -m a_stock_quant.dolphindb_daily_profile `
  --database-uri "dfs://A_STOCK_DAILY_K_DB" `
  --table "stock_daily_k" `
  --output "reports/task_005_daily_k_profile.json"
```

程序会安全提示输入DolphinDB密码。整个过程只读。
