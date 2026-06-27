# TASK_019C 真实市场状态特征验收

- 状态：**PASSED_WITH_WARNINGS**
- 共同交易日：2025-12-31
- 输入状态：READY_WITH_WARNINGS
- 特征状态：READY_WITH_WARNINGS
- 真实特征：15
- 数据库只读：True
- 数据库写操作：0

## 查询范围

- 范围：`DETERMINISTIC_CAPPED_REAL_QUERY_UNIVERSE`
- 本验收不声明全市场全集覆盖。

| 数据集 | 选择器 | 返回记录 | Provider状态 | 就绪度 | 阻断 |
|---|---:|---:|---|---|---:|
| a_stock_daily_k | 30 | 30 | PASSED | WARNING | False |
| hy | 30 | 30 | WARNING | WARNING | False |

## 15项真实特征

| 特征 | 特征族 | 数值 | 单位 | 有效观测 | 来源记录 |
|---|---|---:|---|---:|---:|
| daily_positive_return_ratio | TREND | 0.36666667 | ratio | 30 | 30 |
| daily_mean_return_pct | TREND | 0.27049353 | percent_points | 30 | 30 |
| daily_median_return_pct | TREND | -0.1504085 | percent_points | 30 | 30 |
| industry_advance_ratio | BREADTH | 0.44833783 | ratio | 30 | 30 |
| industry_breadth_ratio_median | BREADTH | 0.72 | ratio | 29 | 30 |
| industry_limit_up_share_of_up | BREADTH | 0.018036072 | ratio | 30 | 30 |
| market_amount_total_cny | LIQUIDITY | 9.604044e+09 | CNY | 30 | 30 |
| turnover_rate_median_pct | LIQUIDITY | 1.264 | percent_points | 30 | 30 |
| amount_field_coverage_ratio | LIQUIDITY | 1 | ratio | 30 | 30 |
| cross_section_return_std_pct | VOLATILITY | 2.1293114 | percent_points | 30 | 30 |
| intraday_range_median_pct | VOLATILITY | 2.0558627 | percent_points | 30 | 30 |
| absolute_return_median_pct | VOLATILITY | 0.749521 | percent_points | 30 | 30 |
| positive_industry_ratio | SECTOR_DIFFUSION | 0.43333333 | ratio | 30 | 30 |
| industry_return_std_pct | SECTOR_DIFFUSION | 0.66673675 | percent_points | 30 | 30 |
| positive_average_return_ratio | SECTOR_DIFFUSION | 0.96666667 | ratio | 30 | 30 |

## 边界

- 仅用于研究特征验收。
- 不输出牛市、熊市或震荡市标签。
- 不输出仓位、选股或交易建议。
- 所有WARNING和来源查询ID均保留在JSON报告中。
