# PROJECT_STATUS.md

# A股量化投资辅助操作系统——当前状态

更新日期：2026-06-23

## 当前阶段

```text
阶段：通用数据接入骨架搭建 + 数据入库与质量验收
已完成：TASK_012 统一数据服务接口与标准查询结果合同
当前任务：TASK_013 基本面快照发现、时点语义画像与注册草案
```

当前目标仍然不是选股模型、复杂因子库、前端或自动交易，
而是建立可被所有下游模块复用的数据标准化、查询、质量和时点基础设施。

## 已完成任务

- TASK_001：仓库初始化与项目治理基础；
- TASK_002：Raw、Canonical、质量、待确认和血缘数据合同；
- TASK_003：DolphinDB通用只读适配器；
- TASK_004：真实DolphinDB只读探测；
- TASK_005：日K字段画像与基础质量检查；
- TASK_006：日K字段单位和语义验证；
- TASK_007：复权公式分层验证；
- TASK_008：快照覆盖边界与更新链路；
- TASK_009：数据集注册表与标准字段映射引擎；
- TASK_010：日K标准映射插件与批量标准化读取服务；
- TASK_011：真实DolphinDB日K标准化抽样验收；
- TASK_012：统一数据服务接口与标准查询结果合同。

## 架构校正结论

- 量化操作系统代码不依赖桌面Excel目录、外部导入工具或外部`config.py`；
- Excel导入脚本属于独立数据端，不是量化操作系统运行依赖；
- DolphinDB库名和表名通过数据集注册配置进入系统；
- 通用标准数据服务核心与日K专属Provider分离；
- 本机路径、密码和购买的原始数据不得提交Git；
- 后续新增基本面和七类数据时，只新增数据集注册、语义适配器和Provider，
  不修改因子、策略、回测等下游模块。

## 已确认的日K结论

- 数据库：`dfs://A_STOCK_DAILY_K_DB`
- 表：`stock_daily_k`
- 数据模式：`SNAPSHOT`
- 覆盖版本：`a_stock_daily_k@2026-05-29`
- 主键 `(stock_code, trade_date)` 无重复；
- OHLC核心逻辑检查通过；
- `volume` 按股解释；
- `amount` 按人民币元解释；
- `float_shares`、`total_shares` 按万股转换为股；
- 标准涨跌幅由收盘价和前收盘价重新计算；
- 来源 `pct_change` 的反向符号作为信息保留；
- 复权关系为 `adj_price = close * adj_factor + deduct_value`；
- 前复权/后复权方向和基准仍不命名；
- TASK_011真实标准化验收状态为 `PASSED`，不阻断下游。

## 当前基本面数据身份

当前已从数据端配置和成功日志确认：

- 数据集候选：`a_stock_fundamental_snapshot`
- 数据库：`dfs://A_STOCK_FUNDAMENTAL_DB`
- 表：`stock_fundamental_snapshot`
- 快照日期：`2026-06-19`
- 来源文件：`2026-06-19更新简化个股基本面数据.xlsx`
- 来源Excel字段：51列
- DolphinDB目标字段：54列
- 导入日志记录：5541行、5541只股票
- 主键候选：`(stock_code, snapshot_date)`

导入成功日志不等于数据库最终验收。TASK_013仍需真实查询确认表结构、行数、
重复、缺失、日期语义、单位、覆盖和时点可见性。

## 当前开发任务

TASK_013完成：

```text
基本面DolphinDB真实表
→ 完整字段结构
→ 主键与覆盖范围
→ 日期和时点语义
→ 缺失、重复和异常画像
→ FundamentalSnapshot映射草案
→ DatasetRegistration
→ 待确认事项和验收报告
```

基本面严格历史回测必须满足：

```text
available_at <= decision_time
```

`snapshot_date`、`update_date`和`report_period`不得未经验证直接当作公告时间。

## 下一数据关口

TASK_013之后继续完成基本面标准Provider与真实验收，再依次接入：

- `hq`
- `hy`
- `gn`
- `kphq`
- `kphy`
- `kpgn`
- `zj`

七类数据批量接入前，再建设独立数据端的通用压缩Excel摄取框架、
集中本机路径配置、统一导入日志和断点续传机制。

## 数据门禁后的顺序

```text
市场状态MVP
→ 风险仓位MVP
→ 第一批基础因子
→ 规则/线性/LightGBM基线
→ 真实A股回测
→ 每日选股和仓位报告
```

## CWMS长期定位

CWMS因果世界—市场仿真引擎属于已确认的长期研究底座。

- 真实数据与合成行情使用相同标准字段和标准对象；
- 世界事件通过通用实体、关系、事件和影响表达；
- 牛熊状态、行业结构和资本迁移应由因果机制驱动；
- 随机性用于参数、时滞和具体行情路径；
- 当前只维护字段、场景、规则和架构契约；
- 当前不开发完整CWMS运行引擎。

## Git与GitHub交付闭环

每个任务只有同时满足下列条件才算完成：

```text
代码和文档已进入正式仓库
全量测试通过
PROJECT_STATUS.md已更新
Git提交说明准确
本地工作区干净
已推送GitHub
HEAD与远程main一致
```
