# TASK_025A 全系统 B2C 双视图与 Skill 平台权威架构验收报告

## 1. 验收结论

```text
状态：PASSED_IN_SANDBOX
任务类型：权威架构、开发指导与机器合同重构
数据库写操作：0
现有业务算法修改：0
当前业务任务顺序改变：否
```

## 2. 核心成果

- 总体架构从V10升级为V11双视图；
- 新增全系统B2C用户控制平面和白箱解释权威文件；
- 新增开发型与产品型Skill共同内核权威文件；
- 每个模块以后必须同时提供后台领域合同和B2C交互合同；
- 用户可以追溯证据、变量、公式、权重、得分贡献、代码、前置教学注释、测试和版本；
- 人物蒸馏进入ResearchArtifact和候选因子通道，不能自动发布正式因子；
- 标准字典缺失字段通过FieldProposal进入治理；
- 仿真变量区分外生控制、初始状态、内生状态、观察、输出和测试覆盖；
- 接入中心成为全系统动态表单、状态机、预览、安全和审计的首个纵向样板；
- 权威文件改为工具无关的虚拟沙盒、本地真实验收和GitHub任务交接规则。

## 3. 机器合同

新增六个JSON Schema 2020-12合同：

```text
b2c_module_manifest.schema.json
b2c_action_contract.schema.json
explanation_trace.schema.json
field_proposal.schema.json
skill_definition.schema.json
research_artifact.schema.json
```

## 4. 沙盒验证

执行命令：

```text
python scripts/validate_task_025a_dual_view_authority.py
python -m unittest tests/test_task_025a_dual_view_authority.py -v
python -m compileall scripts tests
```

结果：

```text
TASK_025A_VALIDATION_PASSED
validated_files=16
validated_schemas=6
Ran 4 tests
OK
compileall=PASSED
```

## 5. 沙盒限制

当前虚拟沙盒没有PowerShell运行时，也不能使用用户GitHub凭据。因此：

- PowerShell脚本完成静态结构检查，但最终执行需在用户Windows本地；
- 完整仓库全量测试需在用户本地最新仓库执行；
- Git提交、GitHub推送和远程哈希一致性由应用脚本在用户本地完成；
- 本任务不连接DolphinDB，不读取商业SDK，不写数据库。

## 6. 当前主线保持

本任务只增加横向权威设计。当前业务实施顺序仍为：

```text
TASK_024D Windows凭据引用安全后端
→ TASK_024E 接入中心页面与后端接口
→ TASK_024F 首个已授权券商只读连接测试
```

后续实现必须遵守本任务新增的双视图、B2C白箱和Skill平台合同。

## 7. 补充交付门禁

```text
git diff --check（模拟基线仓库）：PASSED
PowerShell应用脚本静态结构检查：PASSED
PowerShell复验脚本静态结构检查：PASSED
PowerShell真实执行：待用户Windows本地
```
