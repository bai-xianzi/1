# TASK_004 DolphinDB真实只读探测验收报告

## 验收结论

TASK_004 已通过真实环境验收。

- DolphinDB连接状态：PASSED
- 脚本执行能力：正常
- 数据库：`dfs://A_STOCK_DAILY_K_DB`
- 数据表：`stock_daily_k`
- 查询方式：只读 `select top 5`
- 实际读取行数：5
- 原始字段数：48
- 写入、删库、改表：未执行

## 本次抽样信息

抽样记录来自股票代码 `600601`，样例日期包括：

- 1990-12-19
- 1990-12-20
- 1990-12-21

主要字段包括：

- 标识与日期：`stock_code`、`trade_date`
- OHLC：`open`、`high`、`low`、`close`
- 量额：`amount`、`volume`
- 技术指标：均线、MACD、KDJ、RSI、BIAS、BOLL
- 股本：`float_shares`、`total_shares`
- 复权与公司行为：`adj_factor`、`adj_price`、`dividend`、送转配字段

## 已确认事项

1. Python只读适配器能够连接本机DolphinDB。
2. `A_STOCK_DAILY_K_DB/stock_daily_k` 可以被成功读取。
3. 返回结果可以转换为 `RawDataBatch`。
4. 字段名和原始记录能够被完整输出。
5. 当前读取流程没有修改真实数据库。

## 需要继续核验的问题

以下内容不能依据本次5行样例直接下结论：

1. `open/high/low/close` 的复权口径。
2. `adj_price` 的确切定义。
3. `volume` 的单位是股、手或其他口径。
4. `amount` 的单位是元、千元、万元或其他口径。
5. `turnover_rate` 使用百分数还是小数比例。
6. `float_shares` 和 `total_shares` 的单位。
7. `trade_date` 的完整时间语义。
8. `pct_change` 的计算方向和公式。

## 已发现的重点核验信号

样例中价格上涨，但 `pct_change` 为负数：

- 1990-12-19 收盘价：185.3
- 1990-12-20 收盘价：194.6
- `price_change`：正数约9.3
- `pct_change`：-5.02

这可能表示：

- 涨跌幅符号方向与常规定义不同；
- 字段计算公式不同；
- 数据源存在历史口径问题；
- 或该字段并非通常含义的涨跌幅。

在完成全表抽样和公式复核前，不应直接修正或重算。

## 下一任务建议

进入 TASK_005：DolphinDB日K数据只读画像与质量验收。

建议至少统计：

- 总行数
- 股票数量
- 最早和最晚交易日期
- 主键重复情况
- 各字段空值率
- OHLC逻辑异常
- `price_change` 与前收盘价的一致性
- `pct_change` 公式方向
- `amount/volume` 与价格之间的数量级关系
- 复权字段覆盖情况
- 每只股票日期是否递增及是否存在重复日期

TASK_005 仍只读，不修改DolphinDB。
