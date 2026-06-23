# TASK_013 基本面结构与样例初步评估

## 已读取内容

- DolphinDB结构导出：54列
- 真实样例：10行
- 数据库：`dfs://A_STOCK_FUNDAMENTAL_DB`
- 表：`stock_fundamental_snapshot`
- 样例快照日期：`2026-06-19`
- 样例报告期代码：`3`

## 初步候选

- `total_shares`等股本字段大概率按万股，需要候选转换`×10000`；
- 资产、收入、利润和现金流字段大概率按千元人民币，需要候选转换`×1000`；
- `eps`和`adjusted_nav_per_share`大概率是元/股；
- `after_tax_profit`可能是整体净利润；
- `net_profit`可能是归母净利润。

上述均需要全表画像和人工确认，当前不得作为最终口径。

## 发现的结构问题

1. 来源`report_period`是INT，而标准字段要求DATE；
2. `update_date`尚不能直接命名为`announcement_date`；
3. 来源缺少`company_id`；
4. 行业分类字段是一对多层级结构，普通单对象映射不足；
5. `zpg`在10条样例中全部为空，语义未知；
6. `total_cash_flow`、`net_assets`等字段口径仍需确认。

## 当前门禁

- 当前快照研究：候选允许；
- 严格历史点时回测：阻断；
- 基本面正式Provider：尚未开发；
- 注册配置：保持`enabled=false`。

## 下一步

将TASK_013文件放入正式仓库，运行真实DolphinDB画像，
再根据报告固化单位、报告期、公告时间和利润口径。
