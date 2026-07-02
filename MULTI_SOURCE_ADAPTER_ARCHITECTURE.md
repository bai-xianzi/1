# 全供应商多源适配架构

## 1. 永久目标

本项目的目标不是完成某一家供应商的接口，而是建设供应商无关、可持续扩展的：

```text
Universal Multi-Source Adapter Framework
```

目标来源包括但不限于：

- Wind；
- 同花顺iFinD；
- 东方财富Choice；
- 银河证券星耀数智；
- QMT、PTrade及其他券商SDK；
- 交易所、监管机构、结算机构和政府官方来源；
- 各券商官方SDK与数据接口；
- Tushare Pro、AKShare等第三方补充来源；
- DolphinDB、本地文件、外接硬盘和未来存储系统。

这些名称只是当前已知目标，不构成封闭名单。

## 2. 稳定边界

```text
Vendor SDK / API / File / Database
        ↓
Source Adapter
        ↓
Capability Discovery
        ↓
RawDataBatch + Source Extensions
        ↓
Canonical Mapping + Semantic Adapter
        ↓
Readiness Evidence
        ↓
StandardDataService
        ↓
研究、风险、组合、回测、报告
```

下游只依赖Canonical对象、标准能力和用途合同。

## 3. 适配器角色

必须按能力分离：

```text
MarketDataAdapter
FundamentalDataAdapter
CorporateActionAdapter
NewsEvidenceAdapter
ResearchContentAdapter
PortfolioAnalyticsAdapter
AccountQueryAdapter
PositionQueryAdapter
BrokerExecutionAdapter
```

同一家供应商可以实现多个角色，但不得把角色合成一个无边界的巨型接口。

数据读取权限不等于交易权限。交易SDK必须通过独立风控、订单状态机、幂等和账实核对后才能激活。

## 4. 能力发现

供应商名称不能代表实际能力。

每个真实接入任务必须发现并记录：

- SDK和客户端版本；
- 操作系统和Python兼容性；
- 实际授权模块；
- 可用数据范围；
- 历史和实时能力；
- 查询频率和单次上限；
- 分页、游标和批量模式；
- 登录、会话和断线恢复；
- 时间戳与available_at；
- 字段、单位、复权和公司行为；
- 许可证、缓存和再分发边界；
- 错误码和限频行为。

未发现的能力保持`DISCOVERY_REQUIRED`，不得凭产品宣传或记忆填写。

## 5. 标准能力与供应商扩展

统一系统必须同时保留：

```text
Canonical标准字段
+
Provider Capability
+
source_extensions
+
完整血缘
```

不能为了统一而丢弃供应商独有能力，也不能让供应商独有字段污染标准对象。

## 6. 多来源路由

同一数据对象可以存在多个来源：

```text
主来源
备用来源
对账来源
紧急降级来源
```

路由依据包括：

- 能力匹配；
- 数据用途；
- 时效；
- 覆盖；
- 语义可信度；
- 许可证；
- 成本；
- 健康状态；
- 用户实际授权。

禁止在因子、模型、策略和报告中写死供应商名称。

## 6.1 来源权威不是接入便利性

Provider路由必须同时记录两个互不替代的维度：

```text
semantic_authority_rank
access_channel_rank
```

- 上交所、深交所、北交所、港交所和中国结算在语义权威上最高；
- 对个人项目而言，已授权券商SDK通常在实际接入便利性上最高；
- 商业数据厂商必须有用户授权；
- 第三方聚合源即使安装方便，也不能因此获得更高权威；
- 未验证抓取接口不能参与正式路由。

数据冲突时，不能只按“哪个接口返回成功”决定，而必须结合来源权威、时间语义、许可证、字段定义和对账证据。

## 7. 当前单机实现方式

当前环境采用模块化单体，不建设微服务平台。

```text
Windows
Intel i7-10750H
16GB内存
GTX 1650 Ti 4GB
本地DolphinDB
```

默认实现：

- Provider并发不超过2；
- CPU并行任务不超过2；
- 数据库并行查询不超过2；
- 2万至5万行批次；
- 每批次检查点；
- 实际磁盘预检；
- 缓存和临时目录配额；
- 大于5GB的下载必须人工确认；
- 不自动导入35GB分钟线；
- GPU不用于适配器层。

这些是保守初值，后续通过基准测试调整。

## 8. 新Provider接入流程

```text
登记Provider目标
→ 获取真实SDK和授权环境
→ 能力发现
→ 认证与许可证评审
→ Raw适配
→ Canonical映射
→ 质量、血缘与时点门禁
→ 合同测试
→ 真实只读验收
→ 注册为候选来源
→ 人工激活
```

新增Provider不得要求重写上层研究代码。

## 9. 当前边界与开发位置

```text
TASK_020A：全供应商能力矩阵和单机资源合同已完成
TASK_020B：通用Provider插件协议和复用治理已完成
TASK_020C：DolphinDB薄Bridge真实验收已完成
TASK_022：local_dolphindb正式激活和真实路由回归已完成
TASK_023A：供应商无关离线发现合同已完成
TASK_023B：Windows机器级环境盘点与候选排序已完成
TASK_023C：原AKShare优先结论已经纠正
TASK_024A：官方交易所与券商接口基线、来源权威门禁已完成
TASK_024B：盘点工具与四道准入门禁已实现，当前位置等待Windows真实证据
```

TASK_024A已经纠正原AKShare优先结论。交易所、监管和结算机构官方资料负责定义语义与验收基准；用户已经获得授权的券商官方SDK是个人项目优先实际接入通道；Wind、iFinD等商业官方SDK位于其后。AKShare、Tushare等第三方聚合源只能用于补充研究、发现线索和交叉核验，不能注册为主事实源。

当前不做：

- 自动安装Wind、iFinD或券商SDK；
- 登录或调用任何商业、券商接口；
- 写入任何账号、密码、Token或密钥；
- 启用新的正式Provider路由；
- 启用自动交易；
- 下载大规模分钟线；
- 启动实时Level-2；
- 建设微服务或分布式系统。

<!-- TASK_024A1_COMMENT_GATE_START -->

## Provider开发的教学式注释前置门禁

任何Provider、Bridge、环境发现器、来源治理器、验证脚本和测试必须在第一次沙盒语法检查前写好教学式前置注释。注释审计失败时，任务仍停留在质量门禁，不得进入下一Provider接入或Git提交。

<!-- TASK_024A1_COMMENT_GATE_END -->

## 10. TASK_024B已授权券商SDK盘点合同

TASK_024B只接受三类输入：

1. 用户明确放入专用证据目录的官方SDK包或开发文档文件名；
2. TASK_023B已经脱敏的模块和已安装客户端命中结果；
3. 用户填写的非秘密授权、只读权限和交易域隔离布尔确认。

```text
官方包证据
+ 用户授权
+ 只读行情权限
+ 交易域隔离
→ 允许创建TASK_024C薄适配任务
```

任何一项缺失都保持阻断。评分用于排序，不能替代准入门禁。报告不得保存绝对路径、未命中文件、完整软件清单、账号、密码、Token、连接地址或端口。
