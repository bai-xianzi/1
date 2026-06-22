# TASK_004_DOLPHINDB_REAL_READONLY_PROBE.md

## 任务目标

在不修改DolphinDB的前提下，使用本机真实配置完成：

1. 连接健康检查；
2. `A_STOCK_DAILY_K_DB/stock_daily_k` 少量只读抽样；
3. 输出原始字段和少量样例；
4. 保留“复权、单位、日期语义尚未确认”的边界。

## 新增文件

- `src/a_stock_quant/dolphindb_probe.py`
  - 命令行入口；
  - 安全读取密码；
  - 执行健康检查；
  - 执行有限行只读抽样。

- `tests/test_dolphindb_probe.py`
  - 使用假适配器验证控制流程；
  - 不连接真实数据库。

- `tasks/TASK_004_DOLPHINDB_REAL_READONLY_PROBE.md`
  - 记录任务范围、命令和验收标准。

## 安全约束

- 不把密码写入代码、Git或任务文档；
- 不执行创建、删除、更新、追加写入；
- 只执行`1 + 1`健康检查和`select top N`查询；
- 抽样上限1000行；
- 不推断复权方式；
- 不推断成交量、成交额单位；
- 不推断日期语义。

## 自动测试

```powershell
python -m compileall src tests
python -m unittest discover -s tests -v
```

预期：32个测试全部通过。

## 真实健康检查

项目使用`src`目录布局，因此先设置临时模块路径：

```powershell
$env:PYTHONPATH="src"
python -m a_stock_quant.dolphindb_probe --health-only
```

程序会安全提示输入DolphinDB密码，终端不会显示输入内容。

## 真实少量抽样

```powershell
$env:PYTHONPATH="src"
python -m a_stock_quant.dolphindb_probe `
  --database-uri "dfs://A_STOCK_DAILY_K_DB" `
  --table "stock_daily_k" `
  --limit 5 `
  --preview-rows 3
```

主机、端口或用户名不是默认值时，追加：

```powershell
--host "实际主机" --port 实际端口 --username "实际用户名"
```

## 验收标准

- 健康检查显示`PASSED`；
- 抽样读取成功；
- 来源为`dfs://A_STOCK_DAILY_K_DB/stock_daily_k`；
- 读取行数不超过5；
- 输出原始字段；
- 不出现写入或库表变更；
- 真实结果由用户提供后再形成验收结论。
