# TASK_019B 可解释市场状态研究特征

## 目标

在TASK_019A统一输入门禁之后，生成第一版可解释、可追溯的市场状态研究特征。

## 输出对象

```text
MarketStateFeatureSnapshot
```

该对象只允许研究使用，不包含市场状态标签、仓位或交易信号。

## 五类必需特征

```text
TREND
BREADTH
LIQUIDITY
VOLATILITY
SECTOR_DIFFUSION
```

共登记15个基础特征。

## 日期对齐

必需数据集采用：

```text
LATEST_COMMON_TRADE_DATE
```

日K与行业快照没有共同交易日时，不允许把不同日期的数据拼成同一状态快照。

## 可解释性

每个特征必须携带：

- 特征ID和特征族；
- 数值和单位；
- 明确公式；
- 解释文本；
- 来源数据集；
- 来源查询ID；
- 来源记录数；
- 有效和缺失观测数；
- 警告。

## 禁止事项

TASK_019B不允许：

- 输出牛市、熊市或震荡市标签；
- 输出仓位；
- 输出选股或买卖信号；
- 解除输入层WARNING；
- 把查询证券集合成交额称为全市场成交额；
- 绕过ReadinessGatedStandardDataService；
- 修改DolphinDB。
