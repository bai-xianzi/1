# TASK_018A 统一数据就绪度合同与用途级政策

## 目标

建立来源无关、可审计、默认安全失败的数据就绪度合同。

本阶段只建立离线合同和政策引擎，不连接DolphinDB，不修改数据库，
不执行真实数据查询，也不开发市场状态、因子、策略或自动交易。

## 覆盖范围

统一覆盖九个已接入数据集：

- `a_stock_daily_k`
- `a_stock_fundamental_snapshot`
- `hq`
- `hy`
- `gn`
- `kphq`
- `kphy`
- `kpgn`
- `zj`

## 统一维度

- `CONTRACT`
- `QUERY_EXECUTION`
- `COVERAGE`
- `FRESHNESS`
- `LINEAGE`
- `TEMPORAL_SAFETY`
- `SEMANTIC_CONFIDENCE`
- `ACTIVATION`

## 统一状态

证据状态：

```text
PASSED
WARNING
FAILED
UNKNOWN
```

最终决策：

```text
PASSED
WARNING
BLOCKED
```

`FAILED`和`UNKNOWN`是否阻断，取决于具体用途和维度。
缺失必需证据会自动生成`EVIDENCE_MISSING`并按政策处理。

## 用途级原则

### 当前快照研究

允许部分时效、时点、语义或激活不确定性以`WARNING`形式存在；
合同、查询、覆盖和血缘缺失必须阻断。

### 人工辅助决策

时效、时点安全、语义和激活必须具有足够证据；
相关`WARNING`或`UNKNOWN`按安全失败阻断。

### 严格历史回测与历史模型训练

覆盖、时点、语义和激活均采用更严格政策；
不得把当前快照、日期级时间或未经证明的历史可见性用于历史点时用途。

## 架构边界

下游不得绕过：

```text
StandardDataService
→ DataReadinessEngine
→ 市场状态与风险仓位
```

下游不得直接读取Raw表或数据集专属服务。

## 后续任务

TASK_018B将把`StandardQueryResult`、Provider描述、覆盖报告和数据集配置
适配为上述八类证据，并建立九个数据集的统一就绪度快照生成器。
