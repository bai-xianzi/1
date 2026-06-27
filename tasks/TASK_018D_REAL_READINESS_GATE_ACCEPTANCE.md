# TASK_018D 九个数据集真实端到端统一就绪度门禁验收

## 目标

把下列链路组合成下游唯一准入入口：

```text
StandardDataService
→ StandardQueryResult
→ 八维ReadinessEvidence
→ DataReadinessEngine
→ ReadinessGatedQueryResult
```

TASK_018D必须使用真实DolphinDB只读查询，对九个已接入数据集和四种用途执行端到端门禁验收。

## 数据集

- `a_stock_daily_k`
- `a_stock_fundamental_snapshot`
- `hq`
- `hy`
- `gn`
- `kphq`
- `kphy`
- `kpgn`
- `zj`

## 用途

- `CURRENT_SNAPSHOT_RESEARCH`
- `MANUAL_DECISION_SUPPORT`
- `STRICT_HISTORICAL_BACKTEST`
- `HISTORICAL_MODEL_TRAINING`

共执行：

```text
9个数据集 × 4种用途 = 36次真实门禁评估
```

## 验收原则

### 当前快照研究

九个数据集必须都能经过统一门禁返回可用结果。

允许最终决策为`WARNING`，但不允许被阻断；所有WARNING必须保留证据代码和来源引用。

### 人工辅助决策

当前九个数据集均未获得人工决策用途激活，因此必须全部阻断。

### 严格历史用途

基本面和七类快照必须因启用、覆盖、时点或语义证据而阻断。

日K已登记为历史候选，但是否最终通过，以真实查询产生的八维证据为准，不得硬编码放行。

## 安全边界

- 只允许调用标准Provider；
- 禁止市场状态、因子和交易模块直接读取Raw表；
- 验收脚本只执行DolphinDB只读查询；
- 不创建、修改或删除数据库、表和记录；
- `assert_usable()`必须同时通过Provider门禁和八维就绪度门禁；
- 任一门禁阻断时，不得由下游手工绕过。

## 交付

- `ReadinessGatedStandardDataService`
- `ReadinessGatedQueryResult`
- 九数据集真实验收计划
- 真实验收脚本
- 离线合同验证
- 专项单元测试
- JSON与Markdown验收报告

## TASK_018关闭条件

TASK_018D真实验收包核验通过后，才更新`PROJECT_STATUS.md`、生成TASK_018关闭报告、提交并建立`task-018`标签。
