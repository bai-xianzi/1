# A股量化投资辅助操作系统——项目状态

更新日期：2026-06-27

## 一、当前阶段

```text
阶段：统一数据质量门禁完成，进入市场状态识别MVP建设
当前工作：关闭 TASK_018，并启动 TASK_019
下一任务：TASK_019 市场状态输入合同与可解释基线
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
- TASK_013：基本面快照发现、时点语义画像与注册草案；
- TASK_014：基本面标准化服务、用途级时点门禁、StandardDataService Provider 与真实抽样验收。
- TASK_015：七类快照来源治理、完整画像、字典审计与接入合同。
- TASK_016：七类日线资金预导入、DolphinDB Raw层真实导入与幂等验收。
- TASK_017：七类日线资金Canonical字典升级、只读标准化服务、七个StandardDataService Provider与真实统一入口验收。
- TASK_018：统一数据就绪度合同、八维证据适配、外部覆盖/时效/启用证据与九数据集真实用途级门禁验收。

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

当前数据集配置继续保持：

```json
"enabled": false
```

TASK_014 已完成真实验收，但验收通过不等于自动启用。
后续由统一配置激活策略决定何时启用，不能在单个任务中静默改为 `true`。

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

## 七、TASK_014 最终状态

```text
基本面只读标准化服务：PASSED
StandardDataService Provider：PASSED
金额单位转换：PASSED
股本单位转换：PASSED
报告期结束日推导：PASSED_WITH_DERIVATION_WARNING
空财务载荷处理：PASSED
Canonical 字段约束：PASSED
当前快照研究：ALLOWED_WITH_WARNING
快照后人工辅助决策：ALLOWED_WITH_WARNING
严格历史回测：BLOCKED
历史模型训练：BLOCKED
真实 DolphinDB 抽样验收：PASSED
```

真实验收覆盖：

```text
000001：正常一季报
002731：旧三季报
600015：年报
001235：身份和财务不完整
001248：有身份但无财务载荷
```

验收结论：

- 金额字段由千元人民币转换为人民币元；
- 股本字段由万股转换为股；
- 3、9、12 月报告期推导结果符合预期；
- `update_date` 不映射为公告日期；
- 空财务载荷不补零；
- Instrument 身份候选继续保留；
- 行业分类使用权威 Canonical 字段；
- 当前研究与快照后的人工辅助决策允许但带警告；
- 严格历史回测和历史模型训练继续阻断；
- 数据集配置继续保持 `enabled=false`。

TASK_014 交付文件包括：

```text
configs/datasets/a_stock_fundamental_snapshot.json
src/a_stock_quant/dolphindb_fundamental_service.py
src/a_stock_quant/fundamental_standard_provider.py
src/a_stock_quant/standard_data_service.py
tests/test_dolphindb_fundamental_service.py
tests/test_fundamental_standard_provider.py
tests/test_standard_data_service.py
scripts/run_task_014_fundamental_acceptance.py
scripts/verify_task_014_patch.ps1
tasks/TASK_014_FUNDAMENTAL_STANDARD_SERVICE.md
reports/task_014_source_excel_unit_validation.json
reports/task_014_source_excel_unit_validation.md
reports/task_014_fundamental_acceptance.json
reports/task_014_fundamental_acceptance.md
```

---

## 八、TASK_015 最终状态

```text
七类来源合同与盘点：PASSED
全量物理画像：PASSED_WITH_REVIEW_ITEMS
标准字段字典审计：PASSED_WITH_REVIEW_ITEMS
字典治理加固：PASSED
未知Schema：0
需要业务隔离的文件：1
```

七类来源：

```text
hq hy gn kphq kphy kpgn zj
```

TASK_015确认了13种来源Schema、统一缺失值和中文量级转换规则、
证券代码清洗规则、资金流负号保留规则、分类节点与证券实体边界，
并明确2025-12-23的kphq文件因覆盖率不足必须隔离。

---

## 九、TASK_016 最终状态

### DolphinDB物理身份

```text
数据库：dfs://A_STOCK_DAILY_FUNDS_DB
引擎：TSDB
分区：MONTH
```

主Raw表：

```text
security_market_snapshot_raw          278,786
classification_market_snapshot_raw     24,648
money_flow_snapshot_raw               158,532
合计                                  461,966
```

治理表：

```text
ingest_batch_log
ingest_file_log
quarantine_file_log
```

真实验收：

```text
来源文件：185
正常文件：184
隔离文件：1
阻断文件：0
首次写入：461,966
幂等重跑新增：0
幂等跳过：461,966
失败文件：0
隔离泄漏：0
```

隔离对象：

```text
日期：2025-12-23
数据集：kphq
来源行数：288
处理：只记录隔离日志，不进入主Raw表
```

TASK_016实现了非破坏建库、逐文件哈希血缘、逐文件回查验收、
TSDB幂等恢复、批次日志、文件日志和隔离日志。

---

## 十、TASK_017 最终状态

### TASK_017A：Canonical接入合同

```text
来源数据集：7
初始READY_WITH_WARNING：2
初始BLOCKED缺口：5
合同状态：PASSED_WITH_REVIEW_ITEMS
```

确认结论：

- `hq`只能作为`DailyBar`补充和对账来源；
- `kphq`不得伪造09:25；
- 行业和概念聚合行情不是成员关系；
- `zj`保留来源资金流符号；
- 来源扩展和完整血缘必须保留。

### TASK_017B：字段字典升级

```text
dictionary_revision：0.6.0
领域数量：46
字段出现次数：1,235
Canonical阻断来源：0
```

新增`ClassificationMarketSnapshot`，并为
`AuctionSnapshot`增加日期级时间精度治理。
`average_shares`因单位未确认继续留在来源扩展。

### TASK_017C：只读Canonical服务

```text
服务版本：0.1.0
映射版本：0.2.0
真实来源：7
数据库写操作：0
状态：PASSED_WITH_WARNINGS
```

真实抽样对象：

```text
hq    → DailyBar
kphq  → AuctionSnapshot
hy    → ClassificationMarketSnapshot
gn    → ClassificationMarketSnapshot
kphy  → ClassificationMarketSnapshot
kpgn  → ClassificationMarketSnapshot
zj    → MoneyFlowSnapshot
```

### TASK_017D：统一StandardDataService入口

```text
Provider：7
统一真实查询：7
INSTRUMENT_ID Provider：3
ENTITY_ID Provider：4
严格历史用途阻断：7
数据库写操作：0
状态：PASSED_WITH_WARNINGS
```

用途门禁：

```text
当前快照研究：允许，但保留WARNING
同日人工辅助决策：阻断
严格历史回测：阻断
历史模型训练：阻断
```

剩余WARNING不得静默消除：

- `hq`不是权威日K；
- `kphq`只有`DATE_ONLY`时间精度；
- 分类节点ID仍是来源名称的稳定派生ID；
- 分类领先证券ID尚未解析；
- `average_shares`来源单位未确认；
- 资金流方法仍需供应商文档；
- 缺少可靠`available_at`，不能用于严格历史点时用途。

---

## 十一、TASK_018 最终状态

任务名称：

```text
TASK_018 统一数据质量门禁与数据就绪度服务
```

### TASK_018A：统一数据就绪度合同

```text
数据集：9
数据用途：4
证据维度：8
决策状态：PASSED / WARNING / BLOCKED
缺失关键证据：安全失败
状态：PASSED_OFFLINE
```

建立了来源无关的`DataReadinessEngine`，并明确：

- Provider负责来源专属语义和质量；
- StandardDataService负责统一查询结果；
- 就绪度引擎按用途决定是否准入；
- Raw访问不得绕过统一服务；
- 缺失必需证据时不得静默放行。

### TASK_018B：统一查询结果转八维证据

```text
输入：StandardQueryResult + ProviderDescriptor + 显式上下文
输出：8项 ReadinessEvidence
状态：PASSED_OFFLINE
```

八个维度：

```text
CONTRACT
QUERY_EXECUTION
COVERAGE
FRESHNESS
LINEAGE
TEMPORAL_SAFETY
SEMANTIC_CONFIDENCE
ACTIVATION
```

一次样本查询只证明查询范围，不自动证明全数据集覆盖、最新状态或生产启用状态。

### TASK_018C：外部覆盖、交易日时效和启用证据

```text
证据截止日：2026-06-27
应有最近交易日：2026-06-26
数据集：9
覆盖PASSED：2
覆盖WARNING：7
当前研究启用PASSED：9
历史启用PASSED：1
历史启用FAILED：8
数据库连接：0
数据库写操作：0
状态：PASSED_WITH_WARNINGS
```

确认：

- 日K和基本面具备报告支持的覆盖证据；
- 七类快照仅证明日期范围和真实样本，未夸大为全实体覆盖；
- 日线时效按交易日而不是自然日计算；
- 数据存在、数据质量和用途启用彼此分离。

### TASK_018D：真实端到端统一门禁

```text
Provider：9
数据集：9
用途：4
真实评估：36
证据维度：8
当前研究可用：9
当前研究WARNING：9
人工辅助决策阻断：9
严格历史回测阻断：9
历史模型训练阻断：9
数据库模式：真实连接、只读查询
数据库写操作：0
问题数量：0
状态：PASSED_WITH_WARNINGS
```

新增统一组合入口：

```text
ReadinessGatedStandardDataService.query()
→ StandardQueryResult
→ DatasetReadinessSnapshot
→ assert_usable()
```

Provider门禁和八维就绪度门禁均不得被下游静默绕过。

### TASK_018 关闭结论

```text
统一数据准入入口：已建立
九个数据集统一评估：已完成
用途级安全失败：已证明
真实DolphinDB只读验收：已完成
市场状态模块直接读取Raw或绕过门禁：禁止
TASK_018总状态：PASSED_WITH_WARNINGS
```

保留的WARNING和BLOCKED属于真实治理结果，不得为获得“全绿”而删除：

- 日K当前时效落后，并保留来源涨跌幅符号语义警告；
- 基本面可靠公告可见时间尚未证明；
- 七类快照未证明全实体覆盖；
- 竞价数据只有日期级时间精度；
- 分类实体ID和领先证券ID仍需权威主数据；
- `average_shares`单位和资金流方法仍需供应商文档；
- 七类快照缺少可靠`available_at`。

---

## 十二、当前任务：TASK_019

任务名称：

```text
TASK_019 市场状态输入合同与可解释基线
```

目标：

- 只通过`ReadinessGatedStandardDataService`读取获准数据；
- 建立市场状态MVP的输入对象、特征定义和缺失处理合同；
- 第一版优先使用可解释的市场宽度、趋势、成交、波动和板块扩散指标；
- 输出牛市、震荡、熊市候选概率或评分及可解释原因；
- 任何数据集被门禁阻断时，不生成正式市场状态结论；
- 不在本任务中开发复杂选股模型、组合优化、自动交易或大型前端。

TASK_019第一阶段应先完成输入合同和离线基线，再决定真实运行与阈值校准。

---

## 十三、CWMS 长期定位

CWMS 因果世界—市场仿真引擎属于长期研究底座。

长期原则：

- 真实数据和合成数据使用同一套 Canonical 标准字段；
- 世界事件通过通用实体、关系、事件和影响表达；
- 牛熊状态、行业结构和资本迁移由因果机制驱动；
- 随机性只用于参数、时滞和具体行情路径；
- 当前只维护字段、场景、规则和架构合同；
- 当前不开发完整 CWMS 运行引擎。

---

## 十四、Git 与 GitHub 交付闭环

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

TASK_018关闭提交完成最终测试、双远程推送并创建、推送`task-018`标签后正式闭环；当前开发入口转入TASK_019。

<!-- TASK_019_CLOSURE_START -->

## TASK_019 市场状态研究MVP关闭记录

```text
关闭状态：CLOSED_WITH_WARNINGS
用途范围：RESEARCH_ONLY
真实特征：15项 / 5个特征族
真实共同交易日：2025-12-31
研究评分政策：RESEARCH_HYPOTHESIS_UNVALIDATED
真实评分候选：STALE_INPUT_INDETERMINATE
人工决策：BLOCKED
正式市场状态：BLOCKED
交易执行：BLOCKED
数据库写操作：0
```

TASK_019已经建立统一门禁输入、可解释特征、真实只读验收和研究评分链路。由于真实共同日期已经过期，且评分阈值未完成历史校准，TASK_019不得用于当前市场判断或实盘决策。

下一任务：

```text
TASK_020
全供应商多源适配架构与单机资源运行档案
```

TASK_020必须覆盖Wind、iFinD、银河证券星耀数智及其他数据和券商SDK的统一能力模型，同时按照当前单机硬件采用小批次、增量、断点续跑和磁盘配额优先的实现方式。

<!-- TASK_019_CLOSURE_END -->

<!-- TASK_020A_STATUS -->

## TASK_020 当前阶段

```text
TASK_019：市场状态研究MVP已关闭
CURRENT：TASK_020A 全供应商适配与单机资源合同
NEXT：TASK_020B 通用Provider插件协议与能力路由
```

当前不安装商业SDK，不接通自动交易，不下载大规模分钟线。先稳定供应商无关能力矩阵、资源档案和插件边界。

<!-- TASK_020B_REUSE_STATUS -->

## TASK_020B 工程治理补充

```text
复用原则：REUSE_FIRST_CUSTOM_BUILD_LAST
未知许可证复用：禁止
无来源复制：禁止
重写厂商SDK：禁止
默认自研：禁止
```

TASK_020C将通过薄Bridge复用现有DolphinDB Adapter，作为复用优先政策的第一个真实工程应用。
