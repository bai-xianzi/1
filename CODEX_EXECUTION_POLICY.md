# CODEX_EXECUTION_POLICY.md

# Codex开发执行规则

Codex无法继承本项目长期聊天上下文，因此每次任务必须依赖仓库中的权威文件和明确任务包。

## 必须先读取

- `PROJECT_MEMORY.md`
- `SYSTEM_ARCHITECTURE.md`
- `PROJECT_STATUS.md`
- `DEVELOPMENT_GUIDANCE.md`
- `CAUSAL_MARKET_SIMULATION_ENGINE.md`
- `schemas/simulation_variables.yaml`
- `schemas/scenario_interventions.yaml`
- `schemas/causal_rules.yaml`
- `schemas/canonical_fields.yaml`
- `schemas/enum_definitions.yaml`
- 对应来源映射文件
- 根目录`AGENTS.md`
- 根目录`PROJECT_CONTEXT.md`

## Codex允许做

- 在明确范围内编写代码；
- 建立适配器、映射、校验和测试；
- 运行脚本并生成报告；
- 修复明确错误；
- 输出待确认问题。

## Codex禁止自行做

- 改变总体架构和开发顺序；
- 删除或重建正式数据库；
- 擅自新增、删除或改名标准字段；
- 猜测复权、单位、报告期或可用时间；
- 让下游业务模块直接依赖来源字段；
- 提前扩展不在当前阶段的复杂系统；
- 无迁移方案破坏已有接口和结果；
- 根据大语言模型输出直接批准或启用因果规则；
- 将直接市场冲击描述成已经完成上游因果解释；
- 无记录地强制覆盖内生变量或最终行情输出；

## 任务包固定结构

1. 项目阶段；
2. 任务目的；
3. 必读文件；
4. 允许修改范围；
5. 禁止修改范围；
6. 输入；
7. 输出；
8. 标准字段和接口；
9. 异常与待确认处理；
10. 测试与验收；
11. 完成汇报格式。

## 完成汇报

- 新增和修改文件；
- 文件职责；
- 运行方法；
- 测试结果；
- 实际输出；
- 数据或架构问题；
- 待人工确认事项；
- 是否修改数据库；
- 是否影响已有功能；
- 是否遵循字段字典和总体结构。


## 新增场景字段的禁止事项

Codex遇到“仓库被炸”“支柱产业受损”“港口受灾”等描述时，不得自动创建同名专用字段。

必须先判断能否使用：

1. `world_entity`
2. `entity_relation`
3. `world_event`
4. `event_impact`
5. `entity_exposure`
6. `causal_rule`

只有经过项目经理确认，且通用模型无法准确表达时，才允许新增稳定标准变量。

布尔字段只能表达是否发生或是否生效，不能代替损失比例、影响强度、停运时间和恢复周期。


## 项目经理与Codex的边界

- 甲方需求由项目经理先完成领域抽象和技术决策；
- Codex不得根据用户自然语言直接新增字段、表或核心模块；
- Codex发现需求与字段字典、总体结构或通用事件模型冲突时，必须停止并报告；
- 未经项目经理任务包明确授权，不得修改标准字典、因果规则状态和总体架构。


## 研究实验与执行安全的Codex边界

Codex不得：

- 只输出收益最好的实验而删除失败实验；
- 在没有实验ID、数据版本和配置版本时生成正式研究结论；
- 让策略代码直接调用券商下单；
- 绕过交易前风控；
- 在网络超时后无幂等检查地重复发单；
- 修改实盘环境配置而不提供回滚方案；
- 在账实核对失败后继续自动交易。

涉及自动交易、订单状态、核对或停机功能时，必须先由项目经理明确接口、状态机和验收条件。


<!-- TASK_021A_COMMENT_CODEX -->

## Codex代码注释执行约束

Codex生成补丁前必须先读取`CODE_COMMENTING_STANDARD.md`和`configs/engineering/code_comment_policy_v0.json`。

所有新增和修改代码必须在对应逻辑之前提供教学式单行注释。Codex不得把docstring当作合规依据，不得绕过注释审计，也不得在用户确认前执行Git提交或推送。
