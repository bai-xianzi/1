# TASK_018B 证据适配设计审查

状态：`PASSED_OFFLINE`

核心决策：Provider负责来源语义，证据适配器负责把已经结构化的结果翻译为统一
八维证据，DataReadinessEngine负责按用途决策。三层职责不得混合。

一次样本查询只能证明查询范围内的实体和日期，不能自动证明整个数据集的历史
覆盖与最新状态。因此`QUERY_SCOPE_COVERAGE_ONLY`和
`QUERY_SCOPE_FRESHNESS_ONLY`必须保留为WARNING，直到TASK_018C接入真实覆盖、
交易日时效和启用配置证据。
