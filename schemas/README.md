# schemas 目录说明

本目录是项目机器可读金融语义和仿真知识资产的权威位置。

- `canonical_fields.yaml`：统一字段和领域对象；
- `enum_definitions.yaml`：统一枚举；
- `field_governance_contract.yaml`：值域分类、时间语义、跨领域同名字段和迁移治理合同；
- `simulation_variables.yaml`：变量激活、可控权限和传播方式；
- `causal_rules.yaml`：因果规则与硬逻辑；
- `scenario_catalog.yaml`：标准场景模板；
- `scenario_interventions.yaml`：用户场景干预合同；
- `entity_exposure_schema.yaml`：企业、行业与现实世界暴露模板；
- `FIELD_CHANGE_PROCESS.md`：字段和规则变更流程；
- `FIELD_DICTIONARY_MASTER.md`：人类可读完整字典。

用户举例不能直接转成字段。新增内容应优先使用通用实体、关系、事件、影响、暴露和因果规则表达。
