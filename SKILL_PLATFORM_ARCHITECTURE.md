# SKILL_PLATFORM_ARCHITECTURE.md

# WJX 统一 Skill 平台权威设计

> 本文件定义开发型 Skill 与产品型 Skill 的共同内核、权限边界、研究资产、工作流、B2C交互和金融发布门禁。
> Skill 是 WJX 的一等公民，但不是能够绕过领域合同和风险门禁的万能智能体。
> 第三方 Skill 和工作流能力必须遵守 `REUSE_FIRST_ENGINEERING_POLICY.md`，先隔离审查和沙盒验证，再决定复用、薄适配或拒绝。

---

## 1. 核心定义

```text
Skill
= 指令与方法
+ 输入输出 Schema
+ 工作流
+ 工具和数据权限
+ 来源与证据政策
+ 确定性脚本
+ 质量门禁
+ 测试
+ UI 描述
+ 版本和审计
```

Skill 不是单段提示词、单个函数、单个因子或单个页面。

统一对象：

```text
SkillDefinition
SkillVersion
SkillDependency
SkillPermission
SkillWorkflow
SkillRun
SkillStepRun
SkillArtifact
SkillEvidenceLink
SkillReview
SkillPublication
ResearchArtifact
```

---

## 2. 两类 Skill

### 2.1 开发型 Skill

服务于项目开发：

- 需求澄清；
- 功能补全；
- 架构审查；
- 数据模型检查；
- 开源能力调研；
- 测试驱动开发；
- 系统化调试；
- 完成前验证；
- 避免重复造轮子。

开发型 Skill 只提供建议、计划、诊断、测试和验收支持，不自动批准项目架构、Git 提交、生产数据或正式因子。

### 2.2 产品型 Skill

面向 B2C 用户、研究员和投资者：

- 人物、公司、行业、政策、事件和论文蒸馏；
- 投资方法和产业链分析；
- 证据图谱与候选因果假设；
- 金融变量映射；
- 候选因子生成和验证；
- 回测、仿真和风险压力测试。

两类 Skill 共享合同、版本、运行、产物和审计基础，但权限域严格隔离。

---

## 3. 权限域

```text
DEVELOPMENT
RESEARCH
B2C_USER
FINANCIAL_EXPERIMENT
PRODUCTION_RESEARCH
ADMINISTRATION
```

不同权限域不得默认共享：

- 文件写权限；
- Git 权限；
- 数据库管理权限；
- 密钥访问；
- 网络域名；
- 任意代码执行；
- 因子发布；
- 交易能力。

开发型 Skill 通过测试不代表可进入 B2C；产品型 Skill 生成候选因子不代表可进入生产。

---

## 4. Skill 包结构

WJX 优先兼容开放、可移植的 Skill 包结构，并增加金融治理合同：

```text
skill.yaml
SKILL.md
input.schema.json
output.schema.json
ui.schema.json
workflow.yaml
tools.yaml
permissions.yaml
resource_policy.yaml
source_policy.yaml
evidence_policy.yaml
publication_policy.yaml
dependencies.yaml
validators/
scripts/
tests/
examples/
migrations/
CHANGELOG.md
```

第三方原始格式可以通过薄适配器映射到该结构，不能为了统一格式而复制并重写整个第三方项目。

---

## 5. 第三方 Skill 供应链治理

状态：

```text
DISCOVERED
→ QUARANTINED
→ REVIEWED
→ SANDBOX_APPROVED
→ PROJECT_APPROVED
→ PRODUCT_APPROVED
→ REVOKED
```

审查项目：

- 来源仓库、版本和提交哈希；
- 许可证与商业使用边界；
- 脚本、依赖和安装行为；
- 网络、文件、密钥和代码执行权限；
- 输入输出和数据外传；
- 资源占用；
- 维护状态；
- 与 WJX 权威合同的冲突。

不再使用或未获批准的 Skill 必须从默认运行目录和触发规则中移除，但保留必要的历史审计记录。

---

## 6. 人物知识与决策机制蒸馏

人物蒸馏是第一个产品型复合 Skill 样板，应拆为：

```text
身份消歧
→ 来源发现与合规检查
→ 网页、文档、视频和音频解析
→ 时间线
→ 主张和行为提取
→ 成功、失败与反例
→ 证据等级和矛盾检测
→ 决策机制假设
→ Canonical 概念与变量映射
→ 候选因子
→ 本地验证
→ 人工审查和发布
```

内部产物名称必须准确：

```text
PersonEvidenceGraph
PersonDecisionTimeline
DecisionMechanismHypothesis
CausalHypothesisGraph
CandidateFactorProposal
```

不得把时间先后、人物自述或第三方解释直接称为确定因果。

关系等级应复用 ASEI：

```text
SELF_REPORTED
OBSERVED_SEQUENCE
THIRD_PARTY_INTERPRETATION
ASSOCIATIONAL
PREDICTIVE
MECHANISM_HYPOTHESIS
QUASI_CAUSAL
LOCALLY_VALIDATED
REJECTED
```

---

## 7. 研究资产与发布通道

所有 Skill 产物先进入 `ResearchArtifact`：

```text
artifact_id
artifact_type
produced_by_skill_id
skill_version
source_refs
evidence_grade
causal_level
canonical_field_refs
applicability_conditions
failure_conditions
validation_status
review_status
created_at
available_at
content_hash
lineage_refs
```

产物级别：

```text
INSIGHT
HYPOTHESIS
CANDIDATE_FACTOR
APPROVED_FACTOR
```

Skill 默认最高只能自动产生 `HYPOTHESIS` 或 `CANDIDATE_FACTOR`。

正式因子路径：

```text
候选研究资产
→ Canonical 映射
→ 数据覆盖与 Readiness
→ Point-in-Time
→ 单因子实验
→ 样本外和 Walk-forward
→ 市场状态分层
→ 成本、滑点、容量和稳定性
→ 人工批准
→ 因子注册
→ 风险和组合系统使用
```

---

## 8. Skill 与 B2C

每个产品型 Skill 必须发布：

- 用户可读用途；
- 输入字段和默认值；
- 工作流步骤；
- 数据源和工具；
- 证据与因果政策；
- 资源限制；
- 权限范围；
- 产物类型；
- 质量门禁；
- 公式、代码、测试和版本引用；
- 哪些步骤需要人工审查。

B2C 用户可以选择、配置、运行、暂停、恢复、审查、复制和组合 Skill，但不能绕过正式字段、因子和交易发布门禁。

---

## 9. 开源复用策略

通用工作流状态、暂停恢复、重试、动态表单、图谱、代码查看、实验跟踪和媒体解析优先评估成熟方案。

任何候选框架必须先在虚拟沙盒执行最小 POC，记录：

```text
项目和版本
许可证
安装和运行结果
资源占用
直接复用部分
薄适配部分
不适用部分
替换路径
```

WJX 不自研通用工作流引擎、图谱渲染器、公式渲染器或代码编辑器，除非复用审查证明无可用方案。

---

## 10. 分阶段建设

```text
V0 权威合同、Schema 和生命周期
V1 开发型 Skill 实验室及双轨分析记录
V2 Skill 注册、版本、权限、运行和产物
V3 单文档人物蒸馏
V4 多来源人物蒸馏与证据图谱
V5 Canonical 变量映射和候选因子实验
V6 B2C Skill 中心和跨模块工作流
V7 用户模板、组合和经过治理的 Skill 生态
```

Skill 平台建设不得中断当前数据、Provider、安全凭据、市场状态和风险仓位主线；应以合同先行、纵向样板、小步验收的方式逐步接入。
