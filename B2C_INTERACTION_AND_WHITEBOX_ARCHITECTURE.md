# B2C_INTERACTION_AND_WHITEBOX_ARCHITECTURE.md

# WJX 全系统 B2C 用户控制平面与白箱解释权威设计

> 本文件是 WJX 面向最终用户的交互、配置、预览、执行、解释、版本、审计和回滚能力的最高权威设计文件。
> 所有业务模块、API、Schema、Skill、页面和报告都必须同时服从本文件与 `SYSTEM_ARCHITECTURE.md`。
> 核心原则：**B2C 不是最后补上的前端，而是从用户操作界面反向约束内部操作系统设计的横向控制平面。**
> 工程优先级：**能借鉴务必借鉴，能复用优先复用，能薄适配不重写；只有成熟方案确实无法满足时才最小范围自研。**

---

## 1. 产品定位

WJX 最终不是只向用户返回一个分数、一张报告或一段模型结论。用户必须能够通过鼠标、表单、图谱、公式、代码查看器和任务进度中心控制完整研究与决策过程，并沿结果反向追溯到数据、证据、变量、公式、参数、代码、测试和版本。

全系统用户链路：

```text
用户选择模块或 Skill
→ 配置数据、变量、时间、权限和资源
→ 系统验证输入
→ 预览影响范围
→ Dry Run 或模拟执行
→ 用户确认
→ 正式运行
→ 观察步骤和中间产物
→ 查看结果与解释链
→ 查看公式、参数、代码和测试
→ 保存配置版本
→ 比较、复制、回滚或提交审核
```

所有重要用户操作必须形成不可歧义的配置快照、运行快照、数据快照、代码版本、公式版本、产物引用和审计记录。

---

## 2. 双视图总体结构

WJX 的任何功能都必须同时存在两张互相映射的结构图。

### 2.1 用户端操作视图

```text
B2C 用户工作台
├─ 数据源与券商接入中心
├─ 标准字典与字段治理中心
├─ Skill 中心与工作流编辑器
├─ 人物、公司、行业、政策和事件研究中心
├─ 研究资产与证据图谱中心
├─ 因子实验室与评分解释器
├─ 市场仿真与场景编辑器
├─ 回测、风险、仓位和组合中心
├─ T 日计划与 T+1 竞价确认
├─ 代码、公式、测试和版本查看器
└─ 任务、审批、审计、复制和回滚中心
```

### 2.2 系统内部执行视图

```text
B2C Action Contract
→ 输入 Schema 与 UI Schema
→ 权限、许可证、资源和安全校验
→ 预览 / Dry Run
→ Skill 或领域工作流编排
→ Provider / Canonical / ASEI / CWMS / 因子 / 回测 / 风险执行
→ Readiness、Point-in-Time、证据和发布门禁
→ ExplanationTrace 白箱解释链
→ ResearchArtifact / RunArtifact
→ 审批、版本、审计和回滚
```

### 2.3 两张图的连接原则

用户端的每一个按钮、字段、图谱节点和菜单动作，都必须映射到一个明确的内部合同；内部每一个可配置模块，也必须说明未来通过什么用户交互暴露。

禁止：

- 页面直接修改数据库、正式字段字典、生产因子或交易权限；
- 后台功能没有输入输出 Schema、预览、解释和审计合同；
- UI 展示的公式、代码或得分与实际运行版本不一致；
- 为了快速开发而让用户长期编辑 Python、PowerShell 或普通 JSON；
- 把“以后做前端”当作当前不需要设计交互合同的理由。

---

## 3. 全模块统一 B2C 合同

每个业务模块必须发布 `B2CModuleManifest`，至少说明：

```text
module_id
module_name
module_version
description
available_actions
input_schema_refs
output_schema_refs
ui_schema_refs
permission_policy
preview_policy
execution_policy
approval_policy
explanation_schema_ref
code_references
test_references
audit_policy
rollback_policy
```

每个用户动作必须发布 `B2CActionContract`，至少说明：

```text
action_id
action_name
module_id
required_inputs
optional_inputs
default_values
allowed_ranges
preview_supported
dry_run_supported
human_approval_required
execution_target
output_artifacts
failure_behavior
rollback_supported
explanation_level
```

所有配置对象必须可版本化、可复制、可比较、可导出、可审计、可回滚，并能作为 Skill 输入。

---

## 4. 白箱解释链

系统统一使用 `ExplanationTrace` 表达一次运行的解释路径。

最小链路：

```text
最终结果
→ 风险修正
→ 综合评分
→ 单项因子得分
→ 因子公式与权重
→ 标准化和缺失处理
→ Canonical 字段
→ 来源数据与时点
→ 证据、算法、代码和测试版本
```

每个解释步骤至少包含：

```text
trace_id
run_id
module_id
step_id
input_references
transformation
formula
parameter_values
intermediate_values
output_reference
code_reference
test_reference
evidence_reference
warning_codes
```

用户端不得只显示“综合评分 87”而隐藏构成过程。至少应支持展开查看单项得分、原始输入、标准化值、公式、权重、风险调整、代码版本和测试状态。

---

## 5. 算法代码、公式和教学式注释查看

用户可以通过受控只读代码查看器打开与当前算法版本对应的源代码快照。

代码查看器必须支持：

- 当前公式和用户可读公式；
- 与公式对应的实际算法文件；
- 前置教学式注释；
- Git 提交和算法版本；
- 测试文件和最近验收状态；
- 版本差异；
- 失效条件和适用范围。

代码查看器不得允许：

- 浏览无关服务器文件；
- 读取密钥、账号或系统配置；
- 修改源代码；
- 任意执行 Python、PowerShell 或 SQL；
- 绕过权限下载受限制代码。

所有可展示的人工算法代码必须遵守 `CODE_COMMENTING_STANDARD.md`。代码、注释、界面公式和实际执行结果必须来自同一版本。

---

## 6. 数据模块交互合同

数据模块至少提供：

```text
选择 Provider
→ 查看官方申请和授权要求
→ 输入或选择安全凭据
→ 测试连接
→ 发现能力
→ 预览极小样例
→ 查看 Raw 到 Canonical 映射
→ 查看覆盖、时效、血缘和 Readiness
→ 用户确认
→ 激活研究能力
```

用户可以在 UI 中输入密钥，但秘密必须在同一次后端调用中写入操作系统安全存储。前端、普通配置、日志、报告、数据库和 Git 只能保存凭据引用。

数据白箱至少展示：

- 来源字段和 Canonical 字段；
- 单位、日期、时区和可见时间转换；
- 缺失、异常和冲突处理；
- 数据覆盖与更新时间；
- 用途级 Readiness；
- 当前允许与阻断的用途。

`PROVIDER_CONNECTION_CENTER.md` 是数据接入中心的首个纵向实现样板，但其动态表单、状态机、安全 ViewModel、预览、只读测试和审计模式应复用于其他模块。

---

## 7. 标准字典与字段治理交互合同

标准字典必须提供可视化字段搜索、分类浏览、字段详情、来源映射、单位、时间语义、使用关系和变更历史。

当因子、Skill 或仿真发现标准字典缺失字段时，必须生成 `FieldProposal`，而不是在代码中静默新增字段。

字段提案流程：

```text
发现变量缺口
→ 搜索同义字段和可推导字段
→ 生成字段提案
→ 确认业务定义、单位、类型和时间语义
→ 确认候选来源与可见时间
→ 字段治理审查
→ APPROVED / MERGED / REJECTED / DATA_PENDING
→ 建立映射与 Readiness
→ 允许进入研究或实验
```

普通用户可以提出和修改草案，但不能直接覆盖正式 Canonical 合同。

---

## 8. 因子实验与评分交互合同

因子实验室必须允许用户通过公式编辑器、可视化节点编辑器、模板或 Skill 选择：

- 输入变量；
- 时间范围；
- 标准化和截断；
- 缺失值和异常值处理；
- 因子方向和权重；
- 目标变量；
- 市场状态；
- 训练、验证和测试区间；
- 成本、滑点和容量假设。

每个因子必须同时保存：

```text
机器可执行公式
用户可读公式
输入字段和单位
标准化与异常规则
权重和参数
适用市场状态
失效条件
代码文件与 Git 版本
测试与验收结果
```

因子生命周期：

```text
IDEA
→ MAPPED
→ DATA_READY
→ EXPERIMENTAL
→ VALIDATED
→ APPROVED
→ ACTIVE
→ RETIRED
```

Skill 自动生成的结果最高只能进入 `CANDIDATE_FACTOR` 或 `EXPERIMENTAL`，不得自动成为生产因子。

---

## 9. 市场仿真交互合同

用户通过场景编辑器选择和输入变量时，每个变量必须具有明确角色：

```text
EXOGENOUS_CONTROL
INITIAL_STATE
DERIVED_STATE
OBSERVATION_ONLY
TARGET_OUTPUT
TEST_OVERRIDE
```

用户不能任意把所有因子设为外生输入。内生变量和综合因子应由因果规则推导。测试模式强制覆盖时必须标记 `CAUSAL_CONSISTENCY_BROKEN`。

仿真界面必须显示：

```text
输入变量
→ 受影响实体
→ 企业经营变量
→ 参与者行为
→ 资本迁移
→ 市场状态
→ 行业与股票结果
```

每条传播边必须可查看规则来源、公式、方向、强度、时滞、置信度、适用范围、失效条件、支持证据和反证。

发现缺失变量时必须进入字段提案流程。

---

## 10. Skill 在全系统中的交互入口

Skill 不只存在于“Skill 中心”。每个模块都可以暴露经过批准的 Skill：

```text
数据模块：Provider 接入、字段映射、质量诊断
字典模块：字段缺口、同义检查、单位和时间语义审查
证据模块：文档蒸馏、主张提取、反证发现
因子模块：变量发现、因子生成、失效诊断
仿真模块：场景构建、变量角色和因果规则审查
回测模块：前视偏差、成本、制度和结果诊断
风险模块：压力测试、仓位解释和否决原因
```

用户可以组合多个 Skill，但每一步仍必须服从领域模块的合同和门禁。

---

## 11. 用户角色与权限

建议最低角色：

```text
B2C_USER
ADVANCED_RESEARCHER
ADMINISTRATOR
DEVELOPER_MAINTAINER
```

普通用户可以运行已批准 Skill、查看白箱解释、保存个人模板；高级研究用户可以创建候选因子、字段提案和仿真场景；管理员负责审核字段、因子、Skill 和 Provider；开发维护用户管理代码、测试和版本。

查看代码不等于拥有修改和执行权限。

---

## 12. 复用优先的 B2C 实现策略

以下通用能力必须优先评估成熟官方或开源实现：

- JSON Schema 动态表单；
- 图谱和流程可视化；
- 数学公式渲染；
- 只读代码查看与差异；
- 工作流编排、暂停、恢复和人工确认；
- 任务状态、日志和重试；
- 实验跟踪和版本；
- 权限和凭据安全；
- 文档、网页、视频和音频解析。

WJX 独立开发应集中在：

- A 股 Canonical 金融语义；
- 字段治理和 Point-in-Time；
- ASEI 证据等级与反证；
- 因果假设和仿真变量角色；
- 研究资产到候选因子和生产因子的发布门禁；
- 风险、仓位、组合和评分贡献解释；
- B2C 白箱研究体验的领域整合。

---

## 13. 开发验收要求

任何新模块只有同时满足以下两类合同，才算架构设计完成：

```text
后台领域合同：
数据模型 / 业务逻辑 / API / 门禁 / 测试

B2C 交互合同：
看什么 / 填什么 / 选什么 / 如何预览 / 如何执行
/ 如何解释 / 如何查看代码 / 如何保存版本 / 如何回滚
```

当前阶段可以先实现领域合同、API、Schema 和交互合同，不要求每个模块立即完成完整页面；但禁止以“前端以后再做”为理由省略交互设计。

---

## 14. 分阶段路线

```text
V0 统一 B2CModuleManifest、B2CActionContract、ExplanationTrace
V1 数据源与券商接入中心纵向样板
V2 标准字典与字段提案中心
V3 因子实验室和白箱评分解释器
V4 市场仿真场景编辑器
V5 Skill 工作流中心和人物蒸馏纵向样板
V6 数据、字典、Skill、因子、仿真、回测、风险和报告统一工作台
```

现有业务开发顺序继续有效；本路线为所有阶段提供用户端和内部系统双视图约束。
