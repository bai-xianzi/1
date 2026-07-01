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
- Tushare Pro、AkShare；
- 交易所、监管机构和政府官方来源；
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

## 9. 当前边界

TASK_020A只建立架构合同、能力矩阵和资源档案。

不做：

- 安装Wind、iFinD或券商SDK；
- 写入任何账号或密钥；
- 启用自动交易；
- 下载大规模分钟线；
- 启动实时Level-2；
- 建设微服务或分布式系统。
