# TASK_018D 九个数据集真实端到端就绪度门禁验收

- 状态：**PASSED_WITH_WARNINGS**
- Provider：9
- 数据集：9
- 用途：4
- 真实门禁评估：36
- 当前研究可用：9
- 人工决策阻断：9
- 严格历史回测阻断：9
- 历史模型训练阻断：9
- 数据库写操作：0

| 数据集 | 用途 | Provider状态 | 就绪度决策 | 阻断 | 记录数 |
|---|---|---|---|---:|---:|
| a_stock_daily_k | CURRENT_SNAPSHOT_RESEARCH | PASSED | WARNING | False | 1 |
| a_stock_daily_k | MANUAL_DECISION_SUPPORT | PASSED | BLOCKED | True | 1 |
| a_stock_daily_k | STRICT_HISTORICAL_BACKTEST | PASSED | BLOCKED | True | 1 |
| a_stock_daily_k | HISTORICAL_MODEL_TRAINING | PASSED | BLOCKED | True | 1 |
| a_stock_fundamental_snapshot | CURRENT_SNAPSHOT_RESEARCH | WARNING | WARNING | False | 1 |
| a_stock_fundamental_snapshot | MANUAL_DECISION_SUPPORT | WARNING | BLOCKED | True | 1 |
| a_stock_fundamental_snapshot | STRICT_HISTORICAL_BACKTEST | FAILED | BLOCKED | True | 1 |
| a_stock_fundamental_snapshot | HISTORICAL_MODEL_TRAINING | FAILED | BLOCKED | True | 1 |
| hq | CURRENT_SNAPSHOT_RESEARCH | WARNING | WARNING | False | 1 |
| hq | MANUAL_DECISION_SUPPORT | WARNING | BLOCKED | True | 1 |
| hq | STRICT_HISTORICAL_BACKTEST | FAILED | BLOCKED | True | 1 |
| hq | HISTORICAL_MODEL_TRAINING | FAILED | BLOCKED | True | 1 |
| hy | CURRENT_SNAPSHOT_RESEARCH | WARNING | WARNING | False | 1 |
| hy | MANUAL_DECISION_SUPPORT | WARNING | BLOCKED | True | 1 |
| hy | STRICT_HISTORICAL_BACKTEST | FAILED | BLOCKED | True | 1 |
| hy | HISTORICAL_MODEL_TRAINING | FAILED | BLOCKED | True | 1 |
| gn | CURRENT_SNAPSHOT_RESEARCH | WARNING | WARNING | False | 1 |
| gn | MANUAL_DECISION_SUPPORT | WARNING | BLOCKED | True | 1 |
| gn | STRICT_HISTORICAL_BACKTEST | FAILED | BLOCKED | True | 1 |
| gn | HISTORICAL_MODEL_TRAINING | FAILED | BLOCKED | True | 1 |
| kphq | CURRENT_SNAPSHOT_RESEARCH | WARNING | WARNING | False | 1 |
| kphq | MANUAL_DECISION_SUPPORT | WARNING | BLOCKED | True | 1 |
| kphq | STRICT_HISTORICAL_BACKTEST | FAILED | BLOCKED | True | 1 |
| kphq | HISTORICAL_MODEL_TRAINING | FAILED | BLOCKED | True | 1 |
| kphy | CURRENT_SNAPSHOT_RESEARCH | WARNING | WARNING | False | 1 |
| kphy | MANUAL_DECISION_SUPPORT | WARNING | BLOCKED | True | 1 |
| kphy | STRICT_HISTORICAL_BACKTEST | FAILED | BLOCKED | True | 1 |
| kphy | HISTORICAL_MODEL_TRAINING | FAILED | BLOCKED | True | 1 |
| kpgn | CURRENT_SNAPSHOT_RESEARCH | WARNING | WARNING | False | 1 |
| kpgn | MANUAL_DECISION_SUPPORT | WARNING | BLOCKED | True | 1 |
| kpgn | STRICT_HISTORICAL_BACKTEST | FAILED | BLOCKED | True | 1 |
| kpgn | HISTORICAL_MODEL_TRAINING | FAILED | BLOCKED | True | 1 |
| zj | CURRENT_SNAPSHOT_RESEARCH | WARNING | WARNING | False | 1 |
| zj | MANUAL_DECISION_SUPPORT | WARNING | BLOCKED | True | 1 |
| zj | STRICT_HISTORICAL_BACKTEST | FAILED | BLOCKED | True | 1 |
| zj | HISTORICAL_MODEL_TRAINING | FAILED | BLOCKED | True | 1 |

## 解释

- 当前快照研究必须通过统一门禁，但允许保留WARNING。
- 人工辅助决策当前全部阻断，因为尚未激活。
- 基本面和七类快照的严格历史用途由启用、覆盖、时点或语义证据阻断。
- 日K是否通过严格历史用途，以真实八维证据结果为准。
- 本验收仅执行只读查询，不修改DolphinDB。
