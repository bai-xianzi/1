# TASK_019A 市场状态输入合同与用途边界

## 目标

在计算任何牛熊、震荡或风险状态之前，建立唯一、可审计、用途受限的市场状态输入合同。

## 输入边界

```text
ReadinessGatedStandardDataService
→ ReadinessGatedQueryResult
→ MarketStateInputContractEngine
→ MarketStateInputAssessment
```

不得直接使用Raw表、StandardDataService裸结果或未通过八维门禁的数据。

## 第一版必需输入

- `a_stock_daily_k → DailyBar`
- `hy → ClassificationMarketSnapshot`

两者共同覆盖：

- 趋势；
- 市场宽度；
- 流动性；
- 波动率；
- 行业扩散。

其他七个数据集只作为补充、可选或背景输入。

## 用途限制

TASK_019A只允许：

```text
CURRENT_SNAPSHOT_RESEARCH
RESEARCH_ONLY
```

明确禁止：

- 人工辅助决策放行；
- 正式市场状态发布；
- 交易信号；
- 自动下单；
- 复杂机器学习模型。

## 安全失败

以下任一情况必须阻断：

- 必需数据集缺失；
- 必需数据集返回空结果；
- Provider门禁阻断；
- 八维就绪度门禁阻断；
- 输入用途不是当前快照研究；
- 必需特征族未覆盖；
- 输入不是统一门禁组合结果。
