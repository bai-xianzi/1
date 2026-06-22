# TASK_011：真实 DolphinDB 日K标准化抽样验收与字段覆盖报告

## 一、任务目标

将 TASK_010 的标准化读取服务连接到真实 DolphinDB，在不修改数据库
的前提下，完成第一轮真实标准对象抽样验收。

## 二、新增文件

- `src/a_stock_quant/dolphindb_daily_k_acceptance.py`
- `tests/test_dolphindb_daily_k_acceptance.py`
- `tasks/TASK_011_DAILY_K_REAL_ACCEPTANCE.md`

## 三、默认抽样范围

默认抽样覆盖不同板块的证券代码：

- `000001`
- `001332`
- `300622`
- `600694`
- `688012`
- `920029`

默认日期范围：

- 起始日期：`2026-05-26`
- 结束日期：`2026-05-29`

所有默认证券均来自已确认存在真实数据的样本。

## 四、验收项目

1. 来源行数与标准化记录数一致；
2. `DailyBar` 核心字段100%覆盖；
3. `OwnershipSnapshot` 核心字段100%覆盖；
4. 所有待确认来源字段仍保留在 `source_extensions`；
5. 所有记录包含有效字段血缘；
6. 标准涨跌幅、成交手数、VWAP和市值计算内部一致；
7. 来源反向涨跌幅仅作为信息标记；
8. 来源价格变动、涨跌幅语义或复权公式异常会阻断验收。

## 五、自动测试

```powershell
python -m compileall src tests
python -m unittest discover -s tests -v
```

在 TASK_010 的93个测试基础上，新增9个测试。

预期：

```text
Ran 102 tests

OK
```

## 六、真实验收命令

```powershell
$env:PYTHONPATH="src"

python -m a_stock_quant.dolphindb_daily_k_acceptance `
  --registration "configs/datasets/a_stock_daily_k.json" `
  --instrument "000001" `
  --instrument "001332" `
  --instrument "300622" `
  --instrument "600694" `
  --instrument "688012" `
  --instrument "920029" `
  --start-date "2026-05-26" `
  --end-date "2026-05-29" `
  --limit-per-instrument 20 `
  --output "reports/task_011_daily_k_acceptance.json"
```

未设置 `DOLPHINDB_PASSWORD` 时，程序会安全提示输入密码。

## 七、通过标准

```text
整体状态：PASSED
阻断下游：False
DailyBar核心字段覆盖率：100%
OwnershipSnapshot核心字段覆盖率：100%
待确认字段保留率：100%
计算字段不一致数：0
阻断质量标记数：0
```

`SOURCE_PCT_CHANGE_SIGN_INVERTED` 是已确认的来源语义信息，不属于阻断异常。

## 八、输出报告

`reports/task_011_daily_k_acceptance.json`

报告包含：

- 请求范围；
- 标准对象字段覆盖；
- 待确认字段保留情况；
- 字段血缘覆盖；
- 计算字段一致性；
- 质量标记统计；
- 最多10条标准化样本。

## 九、下一任务

`TASK_012：统一数据服务接口与标准查询结果合同`
