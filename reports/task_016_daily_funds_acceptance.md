# TASK_016 七类日线资金接入验收

- 状态：**PASSED**
- 数据库：`dfs://A_STOCK_DAILY_FUNDS_DB`
- 来源文件：185
- 正常文件：184
- 隔离文件：1
- 阻断文件：0
- 首次实际写入：461,966
- 幂等重跑新增：0
- 幂等跳过：461,966
- 失败文件：0
- 隔离泄漏：0

## 主Raw表

| 表 | 行数 |
|---|---:|
| `security_market_snapshot_raw` | 278,786 |
| `classification_market_snapshot_raw` | 24,648 |
| `money_flow_snapshot_raw` | 158,532 |

## 隔离结论

2025-12-23的`kphq`来源文件共288行，因为全市场覆盖率不足，
只进入隔离日志，没有进入主Raw表。

## 下一任务

`TASK_017`：七类快照Canonical标准化服务与
StandardDataService Provider。
