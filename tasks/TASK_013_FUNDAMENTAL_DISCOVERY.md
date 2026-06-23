# TASK_013：基本面快照发现、时点语义画像与注册草案

## 一、任务定位

当前主线仍然是：

```text
真实数据接入
→ 语义画像
→ Canonical映射
→ 质量、血缘和时点门禁
→ StandardDataService
```

本任务验证第二类真实数据能否复用已有数据基础设施。

本任务不开发基本面因子、模型、回测或完整Excel导入框架。

## 二、已确认物理身份

```text
dataset_id: a_stock_fundamental_snapshot
database_uri: dfs://A_STOCK_FUNDAMENTAL_DB
table_name: stock_fundamental_snapshot
source_snapshot: 2026-06-19
physical_key_candidate: (stock_code, snapshot_date)
expected_columns: 54
```

导入日志记录5541行、5541只股票，但日志不是数据库最终验收结果。

## 三、交付文件

- `src/a_stock_quant/dolphindb_fundamental_profile.py`
- `tests/test_dolphindb_fundamental_profile.py`
- `configs/datasets/a_stock_fundamental_snapshot.json`
- `tasks/TASK_013_FUNDAMENTAL_DISCOVERY.md`
- `reports/task_013_preliminary_schema_assessment.json`
- `reports/task_013_preliminary_schema_assessment.md`

运行真实画像后生成：

- `reports/task_013_fundamental_profile.json`
- `reports/task_013_fundamental_profile_final_check.md`

## 四、初步语义结论

由54列结构和10条真实样例得到以下候选，而不是最终确认：

- 股本字段大概率为万股；
- 资产、收入、利润和现金流字段大概率为千元人民币；
- `report_period`是INT，样例值为3，不能直接映射到DATE；
- `update_date`可能是公告日期，也可能只是供应商更新日期；
- `after_tax_profit`和`net_profit`可能分别对应整体净利润和归母净利润；
- `net_assets`的合并/归母口径仍未知；
- `total_cash_flow`、`zpg`语义未知；
- 行业分类缺少版本和有效区间，必须使用专属分类适配器；
- `company_id`缺少来源，需要统一公司身份解析规则。

## 五、运行测试

```powershell
python -m compileall src tests
python -m unittest discover -s tests -v
python scripts/audit_git_encoding.py
```

## 六、运行真实画像

不要把密码写入命令或Git配置。先在当前PowerShell设置环境变量：

```powershell
$env:DOLPHINDB_PASSWORD = Read-Host `
  "请输入DolphinDB密码"
```

然后运行：

```powershell
python -m a_stock_quant.dolphindb_fundamental_profile
```

默认读取：

```text
dfs://A_STOCK_FUNDAMENTAL_DB
stock_fundamental_snapshot
```

## 七、通过条件

- 实际54列与声明结构一致；
- `(stock_code, snapshot_date)`无重复；
- 主键无空值；
- 快照日期覆盖明确；
- 来源文件和导入时间完整；
- 股本、金额和利润口径形成证据；
- 所有未确认问题写入报告；
- 严格历史回测在公告时间未确认前保持阻断。

## 八、下一任务

TASK_013完成后，开发：

```text
基本面标准化服务
+ Fundamental Provider
+ 点时安全门禁
+ 真实抽样验收
```

完成后再进入七类快照数据接入。
