#

> 当前正式版本：V8。V7及以前版本只作为历史参考。
 README_PROJECT_MEMORY.md

本目录保存 `wjx--` 项目的总体项目级记忆。

## 权威文件

- `PROJECT_MEMORY.md`：长期不变的项目理解、原则和总体方向；
- `SYSTEM_ARCHITECTURE.md`：系统总体结构图和模块边界，属于长期记忆核心；
- `PROJECT_STATUS.md`：当前阶段、未决问题和下一步；
- `README_PROJECT_MEMORY.md`：使用规则；
- `DEVELOPMENT_GUIDANCE.md`：开发大局观、通用数据架构和渐进式实施规则；
- `REUSE_FIRST_ENGINEERING_POLICY.md`：最高优先级的复用、借鉴、第三方评估和自研批准门禁；
- `CODEX_EXECUTION_POLICY.md`：Codex上下文隔离、任务包和验收规则；
- `CAUSAL_MARKET_SIMULATION_ENGINE.md`：CWMS专项设计；
- `schemas/`：字段、仿真变量、用户干预、因果规则、场景和企业暴露的机器契约；
- `MEMORY_REVIEW_REPORT_V5.md`：本轮逻辑复核和改动说明。

## 强制同步规则

以后项目出现重要新结论时：

1. 长期方向变化：更新 `PROJECT_MEMORY.md`；
2. 模块、流程或层级变化：更新 `SYSTEM_ARCHITECTURE.md`；
3. 当前进度变化：更新 `PROJECT_STATUS.md`；
4. 标杆研究结论变化：同步更新 `SYSTEM_ARCHITECTURE.md` 和对应的 `benchmarks/` 资料；
5. 数据源与适配器变化：检查字段字典、映射、血缘和总体结构；
6. 新功能、重大重构或第三方组件变化：先更新或引用 `REUSE_FIRST_ENGINEERING_POLICY.md` 的复用决策记录；
7. Codex任务规则变化：更新 `CODEX_EXECUTION_POLICY.md`；
8. 各文件存在冲突时，必须先统一再继续开发。

新开的所有对话都属于同一个 `wjx--` 项目，应共同使用这套项目级记忆。


## 渐进式开发约束

后续任何重大开发或项目记忆更新，都必须同时检查：

- 是否已经调查项目已有、官方和开源成熟方案；
- 是否优先采用复用、组合或薄适配而不是从零重写；
- 自研部分是否已经缩小到必要范围；
- 是否保留已有可运行功能；
- 是否影响统一字段字典；
- 是否影响总体结构图；
- 是否提供未来扩展余地；
- 是否能通过新增或替换而不是整体重写完成；
- 是否需要兼容、映射或迁移方案。


- `EVENT_ENTITY_IMPACT_DOMAIN_MODEL.md`：通用事件、实体、关系和影响的正式领域模型。

## V7恢复并确认的机器可读知识资产

- `schemas/enum_definitions.yaml`
- `schemas/simulation_variables.yaml`
- `schemas/causal_rules.yaml`
- `schemas/scenario_catalog.yaml`
- `schemas/entity_exposure_schema.yaml`
- `schemas/scenario_interventions.yaml`
- `schemas/FIELD_CHANGE_PROCESS.md`

- `INSTITUTIONAL_RESEARCH_AND_EXECUTION_GOVERNANCE.md`：机构化研究生产线、实验生命周期、券商级执行安全、账实核对和回滚原则。
