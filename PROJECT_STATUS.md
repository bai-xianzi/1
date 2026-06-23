# A股量化投资辅助操作系统——项目状态

更新日期：2026-06-23

## 一、当前阶段

```text
阶段：通用数据接入骨架搭建 + 真实数据画像与标准化验收
当前工作：完成 TASK_013 交付闭环，并启动 TASK_014
下一任务：TASK_014 基本面标准化服务、用途级时点门禁与真实抽样验收
```

当前阶段仍然不开发复杂因子库、选股模型、自动交易或前端系统。

当前最优先目标是：

```text
真实数据
→ 数据集注册
→ 字段和语义画像
→ Canonical 标准对象
→ 质量、血缘、时点门禁
→ StandardDataService
→ 市场状态与风险仓位
```

---

## 二、已完成任务

- TASK_001：仓库初始化与项目治理基础；
- TASK_002：Raw、Canonical、质量、待确认和血缘数据合同；
- TASK_003：DolphinDB 通用只读适配器；
- TASK_004：真实 DolphinDB 只读探测；
- TASK_005：日K字段画像与基础质量检查；
- TASK_006：日K字段单位和语义验证；
- TASK_007：复权公式分层验证；
- TASK_008：快照覆盖边界与更新链路；
- TASK_009：数据集注册表与标准字段映射引擎；
- TASK_010：日K标准映射插件与批量标准化读取服务；
- TASK_011：真实 DolphinDB 日K标准化抽样验收；
- TASK_012：统一标准数据服务接口与标准查询结果合同；
- TASK_013：基本面快照发现、时点语义画像与注册草案。

---

## 三、架构铁律

### 1. 数据端与量化操作系统分离

```text
数据端
压缩包 / Excel / API / 外接硬盘
→ 解压
→ 清洗
→ 导入
→ 数据库
```

```text
量化操作系统
数据库适配器
→ 数据集注册
→ 语义适配
→ Canonical 标准对象
→ StandardDataService
→ 因子、策略、回测、报告
```

量化操作系统不得依赖：

- 桌面 Excel 目录；
- 外部导入脚本路径；
- 外部 `config.py`；
- 购买数据的实际压缩包路径；
- 某台电脑的固定盘符；
- 供应商原始中文字段。

### 2. 允许变化的部分

以下变化只能影响数据端，不应影响量化操作系统：

- Excel 文件移动；
- 压缩包移动；
- 导入脚本改名、替换或删除；
- 更换硬盘、NAS 或服务器；
- DolphinDB 物理表迁移；
- 后续改用 API 或其他存储。

### 3. 稳定依赖边界

```text
导入器
→ 负责把 Excel 数据写入数据库

数据库适配器
→ 负责从数据库读取 RawDataBatch

语义适配器
→ 负责单位、公式、日期和业务口径

CanonicalMappingEngine
→ 负责来源字段到标准字段映射

StandardDataService
→ 负责向整个操作系统提供统一数据接口
```

---

## 四、日K数据现状

### 物理身份

```text
数据库：dfs://A_STOCK_DAILY_K_DB
表：stock_daily_k
```

### 覆盖

```text
记录数：16,548,275
股票数：5,523
日期范围：1990-12-19 至 2026-05-29
字段数：48
```

### 已确认结论

- 主键 `(stock_code, trade_date)` 无重复；
- OHLC 核心逻辑检查通过；
- `volume` 按股解释；
- `amount` 按人民币元解释；
- `float_shares`、`total_shares` 来源单位按万股，标准化时转换为股；
- 标准涨跌幅由 `close` 和 `pre_close` 重新计算；
- 来源 `pct_change` 的反向符号作为来源扩展保留；
- 复权关系为：

```text
adj_price = close * adj_factor + deduct_value
```

- 前复权、后复权方向和复权基准仍不做未经证据支持的命名；
- TASK_011 真实标准化抽样验收结果为 `PASSED`。

---

## 五、基本面快照现状

### 物理身份

```text
数据集：a_stock_fundamental_snapshot
数据库：dfs://A_STOCK_FUNDAMENTAL_DB
表：stock_fundamental_snapshot
```

### 数据规模

```text
数据量：5,541 行
股票数：5,541
字段数：54
快照日期：2026-06-19
主键：(stock_code, snapshot_date)
```

### 结构和质量结论

```text
54列结构一致：PASSED
主键重复：0
主键空值：0
日期异常：0
负股本：0
流通股大于总股本：0
非正总资产：0
source_file 缺失：0
imported_at 缺失：0
```

### 缺失情况

```text
13只股票：
主要财务字段为空

8只股票：
market、stock_name、pinyin 为空或空字符串

zpg：
5,541 行全部为空
```

这些记录不得删除，也不得把空值填成零。

标准化阶段应区分：

```text
没有财务数据
≠
财务数据为 0
```

### 报告期结论

`report_period` 当前确认是报告期结束月份码候选：

```text
3  → 3月报告期
9  → 9月报告期
12 → 12月报告期
```

覆盖情况：

```text
3月：5,491 行
9月：11 行
12月：26 行
空值：13 行
```

来源没有直接提供完整报告期日期。

TASK_014 中需要依据 `update_date` 与月份码推导报告期结束日，并保留：

```text
source_report_period_month
source_update_date
derived_report_period
```

推导结果必须带 `DERIVED` 或 `WARNING` 状态，不能静默覆盖来源值。

### 单位结论

#### 股本字段

以下字段来源单位按万股进行经验确认：

```text
total_shares
b_shares
h_shares
circulating_a_shares
```

Canonical 转换：

```text
来源万股 × 10000 → 标准股
```

#### 金额字段

资产、收入、成本、利润和现金流字段来源单位按千元人民币进行经验确认。

全表证据：

```text
千元人民币 + 万股公式匹配：
4,865 / 5,528 = 88.01%

万元人民币 + 万股公式匹配：
3 / 5,528 = 0.05%
```

Canonical 转换：

```text
来源千元人民币 × 1000 → 人民币元
```

该状态属于：

```text
CONFIRMED_EMPIRICALLY
```

不是：

```text
CONFIRMED_BY_VENDOR_DOCUMENTATION
```

### 利润字段结论

```text
可比较记录：5,528
after_tax_profit 与 net_profit 完全相等：1,142
相等比例：20.66%
```

因此两个字段不能合并。

当前候选：

```text
after_tax_profit
→ 税后利润 / 公司整体净利润候选

net_profit
→ 归母净利润候选
```

在供应商说明书确认前，二者都应保留原始来源值，并维持 `WARNING` 状态。

### 时点规则

基本面快照目前采用以下时间定义：

```text
snapshot_date
= 这份全市场 Excel 快照代表的观察日期
= 2026-06-19

imported_at
= 数据真正进入本地系统的时间
= 2026-06-19 19:36:51.269

update_date
= 供应商提供的数据更新日期
= 不能直接视为公告日期

report_period
= 来源报告期结束月份码
```

用途级门禁：

```text
当前快照研究：
ALLOWED_WITH_WARNING

快照之后的人工辅助决策：
ALLOWED_WITH_WARNING

严格历史点时回测：
BLOCKED

历史模型训练：
BLOCKED

用本快照回填 2026-06-19 之前：
BLOCKED
```

当前数据集配置必须保持：

```json
"enabled": false
```

直到 TASK_014 的标准 Provider 和真实抽样验收完成。

---

## 六、TASK_013 最终状态

```text
物理结构画像：PASSED
主键质量：PASSED
基础异常检查：PASSED
单位识别：PASSED_WITH_EMPIRICAL_EVIDENCE
报告期识别：PASSED_WITH_DERIVATION_WARNING
当前快照研究：ALLOWED_WITH_WARNING
严格历史回测：BLOCKED
```

TASK_013 交付文件包括：

```text
configs/datasets/a_stock_fundamental_snapshot.json
src/a_stock_quant/dolphindb_fundamental_profile.py
tests/test_dolphindb_fundamental_profile.py
tasks/TASK_013_FUNDAMENTAL_DISCOVERY.md
tasks/TASK_013_PROFILE_HOTFIX.md
reports/task_013_preliminary_schema_assessment.json
reports/task_013_preliminary_schema_assessment.md
reports/task_013_fundamental_profile.json
reports/task_013_fundamental_profile_final_check.md
```

---

## 七、当前任务：TASK_014

任务名称：

```text
TASK_014
基本面标准化服务、用途级时点门禁与真实抽样验收
```

### 主要开发内容

```text
DolphinDB 基本面只读查询
→ 财务空记录识别
→ 股本单位转换
→ 金额单位转换
→ 报告期结束日推导
→ FundamentalSnapshot
→ OwnershipSnapshot
→ Instrument 候选
→ ClassificationMembershipSnapshot
→ source_extensions
→ 字段血缘
→ 用途级时点门禁
→ StandardDataService Provider
→ 真实样本验收
```

### 真实验收样本

至少覆盖：

```text
000001
正常 3 月报告期数据

002731
9 月报告期旧数据

600015
12 月报告期数据

001235
全部财务字段为空

001248
有名称和市场，但财务字段为空
```

### TASK_014 不做的内容

- 不修改 DolphinDB 原始表；
- 不修改 Excel 导入脚本；
- 不开发通用 Excel 摄取框架；
- 不开发基本面因子；
- 不开发选股模型；
- 不进入自动交易；
- 不解除严格历史回测门禁。

---

## 八、七类数据后续接入

基本面 Provider 验收完成后，按顺序接入：

```text
hq
hy
gn
kphq
kphy
kpgn
zj
```

七类数据批量接入前，独立建设数据端：

```text
通用压缩包管理
+ 通用 Excel 读取
+ 集中本机路径配置
+ 数据集专属配置
+ 专属清洗插件
+ 统一导入日志
+ 重复检测
+ 断点续传
+ DolphinDB 写入器
```

目标不是七套完整脚本，而是：

```text
一套通用导入框架
+ 多份数据集配置
+ 少量专属插件
```

---

## 九、数据门禁后的开发顺序

```text
基本面标准 Provider
→ 七类快照标准接入
→ 统一数据质量门禁
→ 市场状态 MVP
→ 风险仓位 MVP
→ 第一批基础因子
→ 规则 / 线性 / LightGBM 基线
→ 真实 A 股回测
→ 每日选股与仓位报告
→ T+1 竞价确认
→ 人工实盘交易闭环
```

---

## 十、CWMS 长期定位

CWMS 因果世界—市场仿真引擎属于长期研究底座。

长期原则：

- 真实数据和合成数据使用同一套 Canonical 标准字段；
- 世界事件通过通用实体、关系、事件和影响表达；
- 牛熊状态、行业结构和资本迁移由因果机制驱动；
- 随机性只用于参数、时滞和具体行情路径；
- 当前只维护字段、场景、规则和架构合同；
- 当前不开发完整 CWMS 运行引擎。

---

## 十一、Git 与 GitHub 交付闭环

每个任务只有同时满足以下条件才算完成：

```text
代码和文档已进入正式仓库
全量测试通过
PROJECT_STATUS.md 已更新
Git 提交说明准确
本地工作区干净
已推送 origin/main
已推送 public/main
HEAD 与两个远程 main 一致
任务标签已建立并推送
```

当前 TASK_013 在完成本文件替换、测试、提交、双远程推送和 `task-013` 标签后正式闭环。
