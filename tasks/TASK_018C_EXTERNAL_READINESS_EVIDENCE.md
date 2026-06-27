# TASK_018C 真实覆盖、交易日时效与启用证据

## 目标

把TASK_018B中的三类占位证据替换为真实、可审计的仓库证据：

```text
QUERY_SCOPE_COVERAGE_ONLY
QUERY_SCOPE_FRESHNESS_ONLY
PROVIDER_REGISTERED_ACTIVATION_UNVERIFIED
```

替换来源：

- 已提交的数据覆盖和真实验收报告；
- 上海证券交易所2026年休市安排；
- 独立的数据集用途启用注册表。

本阶段不连接DolphinDB，不执行数据库写入，不修改StandardDataService。

## 覆盖的数据集

```text
a_stock_daily_k
a_stock_fundamental_snapshot
hq
hy
gn
kphq
kphy
kpgn
zj
```

## 覆盖证据

### 日K

使用`reports/task_008_dataset_coverage.json`证明：

- 16,548,275行；
- 5,523个证券；
- 数据库最大日期与声明截止日一致；
- 当前完整数据库快照覆盖状态为PASSED。

### 基本面

使用`reports/task_013_fundamental_profile.json`证明：

- 5,541行；
- 5,541个证券；
- 当前快照主键无重复；
- 当前快照研究允许；
- 严格历史用途仍被语义和时点问题阻断。

### 七类快照

使用TASK_017C和TASK_017D真实验收报告证明：

- 七类来源均返回真实Canonical记录；
- 七个Provider均通过统一入口查询；
- 日期范围和真实抽样已验收；
- 尚未证明完整实体全集，因此覆盖维度保留WARNING。

## 交易日时效

使用上海证券交易所官方2026年休市安排。

以2026-06-27为证据截止日：

```text
最近交易日 = 2026-06-26
```

当前研究时效结果：

```text
日K：落后19个交易日 → WARNING
基本面：落后5个交易日，阈值10 → PASSED
七类快照：明显超过1个交易日阈值 → WARNING
```

固定历史区间不以“当前是否最新”作为阻断条件；
严格历史准入继续由覆盖、时点、语义和启用状态决定。

## 用途启用

- 九个数据集均启用`CURRENT_SNAPSHOT_RESEARCH`；
- 只有日K启用严格历史候选用途；
- 基本面和七类快照未启用严格历史回测与历史模型训练；
- 所有数据集暂未启用`MANUAL_DECISION_SUPPORT`。

## 后续

TASK_018D将把真实StandardDataService查询结果与本阶段外部证据覆盖层组合，
生成九个数据集的完整八维就绪度快照，并执行只读真实验收。
