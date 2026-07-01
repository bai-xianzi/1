# TASK_019D 研究级可解释市场状态评分

## 目标

把TASK_019C真实生成的15项研究特征转换为五个分项得分和一个不可执行的研究候选状态。

## 输出

```text
ResearchMarketStateScoreSnapshot
```

包含：

- 趋势得分；
- 市场宽度得分；
- 流动性得分；
- 波动压力得分；
- 行业扩散得分；
- 方向综合得分；
- 稳定度；
- 研究候选状态；
- 每个特征的原值、标准化分和权重；
- 输入警告和阻断原因。

## 候选状态

```text
BULLISH_CANDIDATE
BALANCED_CANDIDATE
BEARISH_CANDIDATE
VOLATILE_TRANSITION_CANDIDATE
STALE_INPUT_INDETERMINATE
```

这些不是正式牛熊标签。

## 安全规则

- 所有锚点和阈值都标记为`RESEARCH_HYPOTHESIS_UNVALIDATED`；
- 15项特征缺失任何一项都阻断；
- 成交额字段覆盖率低于95%时阻断；
- 输入超过10个日历日时强制输出`STALE_INPUT_INDETERMINATE`；
- 过期输入仍可用于检查公式和分项得分，但不能形成当前市场判断；
- 绝对成交额与行业收益离散度只作上下文；
- 不启用人工决策、正式状态或交易执行。

## TASK_019C真实样本

TASK_019C共同交易日为2025-12-31，证据截止日为2026-06-27，日历滞后178天。因此TASK_019D真实验收必须输出：

```text
STALE_INPUT_INDETERMINATE
```

而不能输出当前牛市、熊市或震荡市结论。
