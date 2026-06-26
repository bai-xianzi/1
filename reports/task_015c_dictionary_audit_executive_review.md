# TASK_015C 标准词典机构级审计执行结论

## 一、最终判断

当前标准词典无需推倒重建，具备继续作为项目统一语义底座的条件。

审计结果：

- 字典修订：`0.5`
- 状态：`official_institutional_research_and_execution_governance`
- Domain：45
- 字段出现次数：1201
- 唯一标准字段名：1011
- 枚举：71
- ERROR：0
- WARNING：11
- INFO：300

结论状态：**APPROVED_FOR_GOVERNANCE_HARDENING**

这表示逻辑架构合格，但在冻结新的DolphinDB日线资金物理表前，
需要完成一次非破坏性的治理加固。

## 二、机构能力覆盖

自动矩阵给出10项COVERED_CANDIDATE、1项PARTIAL_REVIEW_REQUIRED。

`cross_asset_macro` 的PARTIAL是自动关键词规则的低估，不是真实缺口。
字典中已有 `cross_asset_market` Domain，其描述明确包含股票指数、加密货币、
期货、商品、外汇、债券和房地产；另有宏观政策Domain。
因此人工复核后，11项机构能力域均有逻辑结构覆盖。

这不代表当前真实数据已经齐备，也不代表所有功能已经实现。

## 三、11个WARNING分类

### A. 可安全修复的元数据一致性：9项

- announcement_date
- created_at
- effective_from
- effective_to
- event_time
- published_at
- trade_date
- latitude
- longitude

这些问题只涉及 `time_semantics` 或 `unit` 缺失。
修复时不改字段名、不改数据类型、不改定义、不改下游合同。

### B. 真实语义命名冲突：1项

`trade_count` 同时表示：

- DailyBar：市场成交笔数，LONG；
- BacktestPerformance：策略交易笔数，INT。

两者不是同一金融概念。不能简单把INT改成LONG，也不能忽略。
应当保留DailyBar的 `trade_count`，并为回测字段提出新的明确名称，
例如 `executed_trade_count`，经引用检查和迁移方案后再变更。

### C. 有意的数值存储差异：1项

`value_numeric` 在宏观/实体经济使用DECIMAL，在仿真/场景使用DOUBLE。

这种差异具有合理性：

- 披露和观测指标可能要求十进制定点精度；
- 仿真计算通常需要浮点运算。

不建议机械统一。应新增“共享字段允许的上下文类型例外”治理规则，
或给字段分配稳定 `semantic_id`，明确它们是否属于同一语义族。

## 四、300个INFO的正确解释

### 1. 202个ENUM_BINDING_REVIEW

不能全部视为枚举缺失。以下类型必须区分：

- CLOSED_ENUM：有限且版本化的枚举；
- CONTROLLED_CODESET：交易所、国家、币种等受控代码集；
- OPEN_CODE：metric_code、node_code等可扩展代码；
- IDENTIFIER：统一社会信用代码、证券代码等标识符；
- FREE_TEXT：自由文本。

当前审计器只根据字段后缀识别，因此包含明显误报。
下一版治理应增加 `value_domain_kind` 和可选 `value_domain_ref`，
不能为所有 `_code` 字段硬绑枚举。

### 2. 98个TIME_SEMANTICS_REVIEW

这些字段需要按含义分类：

- event_time
- observation_time
- publication_time
- availability_time
- effective_interval
- trade_date
- report_period
- system_time

只对语义明确的字段自动补齐；其余进入人工复核队列。

## 五、5.04%映射覆盖率不是缺陷

当前只有日K和基本面两个Dataset配置，候选映射51个唯一字段。
标准词典包含未来来源、因果、场景、研究、组合和执行字段，
因此当前映射覆盖率低是开发阶段的自然结果。

禁止为了提高覆盖率而删除标准字段，或创建没有真实来源的伪映射。

## 六、下一步任务

执行 `TASK_015C-1：词典治理加固`：

1. 修复9项低风险time_semantics/unit一致性；
2. 增加字段值域分类合同；
3. 增加跨Domain共享字段合同与允许例外；
4. 对trade_count提出非破坏性迁移方案；
5. 改进字典Lint，消除后缀启发式误报；
6. 增加Golden Case和破坏性变更检查；
7. 将字典修订从0.5升级到0.5.1，而不是0.6；
8. 审计通过后再冻结日线资金DolphinDB Raw表。

## 七、硬性原则

- 不缩小标准词典；
- 不一次物理化1201个字段；
- 不批量硬绑枚举；
- 不静默改变已使用字段含义；
- 不把来源字段直接加入Canonical；
- 不因当前数据少而降低长期标准；
- 新物理表只实现当前来源实际提供并已验收的字段。
