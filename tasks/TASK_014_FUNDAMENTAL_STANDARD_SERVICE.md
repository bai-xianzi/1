# TASK_014 基本面标准化服务、用途级时点门禁与真实抽样验收（权威对齐 RC2）

## 一、权威基线

本候选以仓库提交 `b024b5a`、标签 `task-013` 为工程基线，并遵守：

```text
PROJECT_MEMORY.md
SYSTEM_ARCHITECTURE.md
PROJECT_STATUS.md
DEVELOPMENT_GUIDANCE.md
schemas/canonical_fields.yaml revision 0.5
schemas/enum_definitions.yaml
```

旧 TASK_014 RC1/RC2 草案不得继续使用。本版本重新校验了所有输出字段，
不再产生字段字典中不存在的伪 Canonical 字段。

## 二、任务目标

把以下基本面快照接入统一标准数据服务：

```text
dfs://A_STOCK_FUNDAMENTAL_DB
stock_fundamental_snapshot
```

稳定链路：

```text
DolphinDB Raw
→ 数据集注册
→ 基本面语义适配
→ Canonical 候选对象
→ 用途级时点门禁
→ FundamentalStandardDataProvider
→ StandardDataService
```

操作系统不读取 Excel，不依赖桌面路径，不调用外部导入脚本，也不修改数据库。

## 三、本任务实现

1. `StandardDataQuery` 新增用途级门禁：
   - `CURRENT_SNAPSHOT_RESEARCH`
   - `MANUAL_DECISION_SUPPORT`
   - `STRICT_HISTORICAL_BACKTEST`
   - `HISTORICAL_MODEL_TRAINING`
2. 人工辅助决策必须提供带时区的 `decision_time`；
3. 读取参数和版本信息来自 `DatasetRegistration`；
4. 数据集保持 `enabled=false`，真实验收必须显式放行；
5. 金额字段按千元人民币乘 1000；
6. 股本字段按万股乘 10000，并输出整数股数；
7. 根据 `update_date + report_period月份码` 推导报告期结束日；
8. `update_date` 不映射为 `announcement_date`；
9. 空财务载荷不生成零填充财务或股本对象；
10. 输出权威字段字典中存在的：
    - `FundamentalSnapshot`
    - `OwnershipSnapshot`
    - `Instrument`
    - `ClassificationMembership`
11. 未进入宽表字典的来源指标保留在 `source_extensions`；
12. 当前快照研究和快照之后的人工决策允许但带警告；
13. 严格历史回测、历史模型训练和快照前查询继续阻断；
14. 提供五只真实证券的 DolphinDB 抽样验收脚本。

## 四、Canonical 输出边界

### FundamentalSnapshot

只输出 revision 0.5 中存在且当前有合理来源的字段，例如：

```text
instrument_id
company_id
report_period
period_type
fiscal_year
fiscal_quarter
announcement_date = null
statement_type = null
consolidation_scope = null
accounting_standard_code = null
currency_code
revenue_cny
operating_cost_cny
operating_profit_cny
total_profit_cny
net_profit_cny
net_profit_parent_cny
total_assets_cny
total_equity_cny
inventory_cny
accounts_receivable_cny
operating_cash_flow_cny
basic_eps_cny
book_value_per_share_cny
```

以下来源指标当前没有完全等价的宽表字段，不制造新字段：

```text
current_assets
fixed_assets
intangible_assets
current_liabilities
long_term_liabilities
capital_reserve
investment_income
total_cash_flow
undistributed_profit
zpg
```

它们继续保存在 `source_extensions`，以后依据正式语义进入 metric 扩展或新字典修订。

### ClassificationMembership

使用权威字段名：

```text
node_id
node_code
node_name_cn
node_level
parent_node_id
effective_from
effective_to
```

分类版本和历史区间未知，因此只表达 `snapshot_date` 当日观察到的候选分类，
并保留 `CLASSIFICATION_VERSION_UNKNOWN` 和快照区间警告。

## 五、单位与报告期

```text
来源金额：千元人民币
Canonical：来源值 × 1000 → CNY

来源股本：万股
Canonical：来源值 × 10000 → shares（LONG语义）

来源每股指标：元/股
Canonical：保持原值
```

单位证据状态为 `CONFIRMED_EMPIRICALLY`，不是供应商文档确认。

报告期推导示例：

```text
update_date=2026-04-25, report_period=3
→ 2026-03-31

update_date=2026-04-29, report_period=9
→ 2025-09-30

update_date=2026-04-29, report_period=12
→ 2025-12-31
```

该结果属于 `DERIVED/WARNING`。

## 六、时点门禁

```text
snapshot_date：快照观察日期
imported_at：当前唯一可证明的本地可用时间
update_date：供应商更新日，不等于公告日
```

规则：

```text
CURRENT_SNAPSHOT_RESEARCH
→ 快照日之后按日期级可见，WARNING，不阻断

MANUAL_DECISION_SUPPORT
→ 必须提供decision_time；由于imported_at时区未知，
  只有决策日期严格晚于入库日期时才允许

STRICT_HISTORICAL_BACKTEST
HISTORICAL_MODEL_TRAINING
→ FAILED，阻断

as_of_date < 2026-06-19
→ FAILED，禁止用当前快照回填历史
```

## 七、真实验收样本

```text
000001：正常2026年一季报
002731：2025年三季报
600015：2025年年报
001235：身份和财务不完整
001248：有身份但没有财务载荷
```

## 八、配置状态

真实验收完成前必须保持：

```json
"enabled": false
```

## 九、执行

```powershell
$env:PYTHONPATH = (Resolve-Path ".\src").Path

python -m compileall src tests scripts
python -m unittest discover -s tests -v
python ".\scripts\audit_git_encoding.py"
python ".\scripts\run_task_014_fundamental_acceptance.py"
```

生成：

```text
reports/task_014_fundamental_acceptance.json
reports/task_014_fundamental_acceptance.md
```

## 十、验收门槛

- 全量单元测试通过；
- 所有映射目标和 Provider 公布字段都存在于 canonical revision 0.5；
- 000001 金额、股本和报告期转换正确；
- 002731 报告期为 2025-09-30；
- 600015 报告期为 2025-12-31；
- 001235、001248 不生成零填充财务快照；
- Instrument 候选仍被保留；
- 分类字段名称与字典一致；
- 当前研究和快照后人工决策为 WARNING 且不阻断；
- 历史用途继续阻断；
- 真实验收 `overall_status=PASSED`。

TASK_014 真实验收通过前，不提交、不推送、不打标签，也不更新 PROJECT_STATUS 为完成。
