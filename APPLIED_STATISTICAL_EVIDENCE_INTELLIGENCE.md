# 全网应用统计证据发现、因果知识与特征治理

英文暂定：`Applied Statistical Evidence Intelligence (ASEI)`

## 1. 定位

本能力用于从全网持续发现、结构化和治理基于统计分析形成的公开知识。

来源不限于正式论文，也不限于心理学。只要公开材料包含可识别的样本、变量、比较、统计结果、效应方向、预测关系或因果识别设计，就可以进入“统计证据候选库”。

长期覆盖范围包括但不限于：

- 同行评审论文、预印本、工作论文、会议论文和学位论文；
- 学术期刊文章、学者刊物、研究通讯、方法说明和数据附录；
- 政府统计公报、监管报告、央行和国际组织报告；
- 大学、研究机构、智库、行业协会和非营利组织报告；
- 调查、民调、抽样研究、实验、自然实验和准实验；
- 企业、数据厂商和咨询机构发布的统计白皮书；
- 数据新闻、杂志研究文章和带有可核验方法的公开统计分析；
- 复现研究、反驳、评论、勘误、撤稿和方法学批评；
- 公开数据集、代码、问卷、量表、测量说明和版本记录。

“可被发现”不等于“可直接启用”。所有来源先作为候选证据，经过方法识别、质量评分、冲突分析、人工审核和本项目验证后，才能进入字段字典、特征、规则、模型或CWMS。

## 2. 最重要的认识边界

统计结果具有研究价值，但统计结果不自动等于因果律。

系统必须区分：

```text
DESCRIPTIVE              描述性统计
ASSOCIATIONAL            正相关、负相关或条件关联
PREDICTIVE               样本外预测关系
QUASI_CAUSAL             准实验或自然实验支持的因果候选
CAUSAL_EXPERIMENTAL      随机实验支持的因果结论
MECHANISTIC_CONSTRAINT   数学、物理、会计或制度硬约束
```

任何来源若只报告相关性，系统只能登记为关联规则或特征假设，不得自动升级为因果规则。

系统还必须区分：

```text
统计显著
效应大小
经济意义
可迁移性
可复现性
可执行性
```

`p_value < 0.05`不能代替效应量、置信区间、样本外验证和现实可用性。

## 3. 统一证据主链

```text
全网来源发现
→ 来源身份、版本、许可和发布时间确认
→ 文档、表格、图形、数据和代码解析
→ 统计主张与变量提取
→ 研究设计和因果识别等级判定
→ 效应量、不确定性、样本和适用范围提取
→ 标准字段和标准实体映射
→ 支持证据、反证、复现、勘误和撤稿关系
→ 候选字段、候选特征、候选关联规则或候选因果规则
→ 人工审核
→ 本项目数据复核、样本外检验和稳定性检验
→ APPROVED / ACTIVE 或 REJECTED / RETIRED
```

这条链是项目的长期知识来源之一，但不能绕过现有数据质量、实验登记、风险门禁和生产晋级流程。

## 4. 需要稳定的知识对象

### 4.1 EvidenceSourceDocument

记录来源本身：

- `source_document_id`
- `source_kind`
- `title`
- `authors_or_organization`
- `publisher`
- `publication_date`
- `url`
- `doi_or_stable_identifier`
- `language_code`
- `jurisdiction`
- `license_code`
- `version_id`
- `retrieved_at`
- `available_at`
- `retraction_status`
- `superseded_by_document_id`
- `content_hash`

### 4.2 StatisticalClaim

记录来源中的一条可核验统计主张：

- `statistical_claim_id`
- `source_document_id`
- `claim_text`
- `claim_type_code`
- `cause_or_predictor_field_ref`
- `outcome_field_ref`
- `relation_direction_code`
- `causal_identification_level`
- `effect_size_type`
- `effect_size_value`
- `confidence_interval_lower`
- `confidence_interval_upper`
- `p_value`
- `sample_size`
- `population_scope`
- `time_scope`
- `geographic_scope`
- `platform_scope`
- `language_scope`
- `study_design_code`
- `measurement_method`
- `model_specification`
- `adjustment_variables`
- `limitations_text`
- `evidence_grade`
- `review_status`

### 4.3 EvidenceRelationship

连接支持、反证和版本关系：

- `relationship_id`
- `from_claim_id`
- `to_claim_id`
- `relationship_type_code`
- `SUPPORTS`
- `CONTRADICTS`
- `REPLICATES`
- `FAILS_TO_REPLICATE`
- `CRITIQUES_METHOD`
- `CORRECTS`
- `RETRACTS`
- `SUPERSEDES`
- `relationship_strength`
- `assessment_basis`

### 4.4 FeatureHypothesis

把统计主张转换为项目候选特征：

- `feature_hypothesis_id`
- `statistical_claim_ids`
- `canonical_input_field_refs`
- `canonical_output_field_ref`
- `transformation_spec`
- `expected_direction`
- `expected_lag`
- `applicability_conditions`
- `failure_conditions`
- `local_validation_status`
- `feature_version`
- `activation_status`

### 4.5 ActorProfileSnapshot与ContentCredibilityAssessment

涉及用户、作者、专家、机构或评论来源时，必须使用稳定匿名ID和时点快照：

```text
content_id
→ author_or_actor_id_hash
→ actor_profile_snapshot_id
→ statistical_claim_ids
→ feature_hypothesis_ids
→ content_credibility_assessment_id
```

不能把“某类人在某项研究中呈现某种统计倾向”永久写成某个具体人的人格事实。

用户画像必须：

- 基于可观测行为；
- 指明统计窗口；
- 指明样本量；
- 指明平台和语言环境；
- 指明特征提取器版本；
- 只使用评价发生前已经可见的数据；
- 保存置信度和不确定性；
- 允许失效、衰减和重新估计；
- 不使用真实身份，优先使用不可逆匿名标识；
- 不以单一特征决定评论真假、交易建议或人员价值判断。

## 5. 来源等级不等于是否收录

系统可以收录低等级来源，但必须降低证据权重并明确用途。

建议来源等级：

```text
A  高质量系统综述、元分析、权威统计与高可信复现
B  同行评审研究、严谨准实验或公开可复核研究
C  预印本、工作论文、研究机构报告和方法透明的行业研究
D  杂志、数据新闻、学者刊物和带统计方法的公开分析
E  专家评论、观点文章或方法信息不足的统计主张
```

等级只影响可信度、审核优先级和启用权限，不决定是否保存。

低等级来源仍可用于：

- 发现候选变量；
- 发现反例；
- 形成待验证假设；
- 扩充场景目录；
- 发现可能的交互项和条件；
- 指导本项目重新统计。

低等级来源不得单独进入生产规则。

## 6. 因果、相关与预测的启用规则

### 6.1 关联规则

适用于正相关、负相关和条件关系：

```text
ASSOCIATIONAL
```

可用于：

- 候选特征；
- 排序中的弱证据；
- 研究解释；
- CWMS概率规则候选。

不得描述为“导致”。

### 6.2 预测规则

只有经过时间外或样本外验证，才能标记：

```text
PREDICTIVE
```

可进入模型候选，但仍不等于因果。

### 6.3 因果规则

只有研究设计支持，且满足适用条件时，才允许登记为：

```text
QUASI_CAUSAL
CAUSAL_EXPERIMENTAL
MECHANISTIC_CONSTRAINT
```

因果规则必须保存：

- 识别策略；
- 处理变量和结果变量；
- 对照组或反事实构造；
- 混杂控制；
- 稳健性检查；
- 适用人群、地区、语言、平台和时期；
- 时滞和持续时间；
- 外部有效性风险；
- 反证和失效条件。

## 7. 与字段字典的关系

系统从来源中发现的新变量不能直接写入`canonical_fields.yaml`。

正式流程：

```text
统计主张
→ 检查现有字段能否表达
→ 优先复用现有通用对象、关系、事件和度量
→ 无法表达时生成字段候选
→ 字段治理审查
→ 枚举、单位、时间、来源、隐私和血缘审查
→ 字典版本升级
```

禁止为每篇文章、每个结论或每个业务例子创建专用字段。

字段应表达稳定可观测量；研究结论、权重、方向、适用条件和证据等级通常应进入规则或证据对象，而不是固化成字段名称。

## 8. 与CWMS的关系

统计证据为CWMS提供：

- 因果规则候选；
- 关联和概率规则候选；
- 参数区间；
- 反应时滞；
- 异质性和条件效应；
- 参与者行为规则；
- 事件影响和暴露权重；
- 反例和失效条件。

CWMS不得把统计关联伪装成硬因果。

规则激活优先级仍为：

```text
数学、物理和会计硬约束
> 交易制度
> 已验证因果规则
> 已验证预测规则
> 统计关联和专家候选
> 代理、默认值和采样
```

## 9. 与机构化研究生产线的关系

每一条准备进入项目的统计主张都必须经历研究生命周期：

```text
DISCOVERED
→ PARSED
→ NORMALIZED
→ PENDING_METHOD_REVIEW
→ PENDING_DOMAIN_REVIEW
→ LOCAL_REPLICATION
→ VALIDATED / DISPUTED / REJECTED
→ APPROVED
→ ACTIVE
→ MONITORED
→ RETIRED
```

必须保存失败复现、无效结论、争议和撤稿，不得只保存“有效规律”。

## 10. 自动化与人工边界

大语言模型和自动化工具可以：

- 搜索候选来源；
- 识别统计表述；
- 提取变量、效应方向和样本信息；
- 发现字段映射候选；
- 生成待审核结构化记录；
- 检索支持、反证和复现来源；
- 生成本项目复现计划。

大语言模型和自动化工具不得：

- 自动把相关性升级为因果；
- 自动批准正式字段；
- 自动启用生产规则；
- 自动用低质量来源改变交易决策；
- 忽略相反证据、勘误和撤稿；
- 将来源摘要伪装成已阅读的完整方法；
- 把统计群体规律变成对具体个人的确定性标签。

## 11. 版权、隐私与来源合规

全网发现能力必须遵守：

- 来源网站使用条款和访问频率限制；
- 版权与数据库权利；
- 公开信息和授权边界；
- 只保存允许保存的全文、片段、元数据或链接；
- 对受版权保护内容优先保存元数据、结构化主张和必要短摘录；
- 对个人数据进行匿名化、最小化和用途限制；
- 不主动收集与投资研究无关的敏感个人信息；
- 每条证据保留来源URL、获取时间、版本和内容哈希。

## 12. 个人版实施顺序

当前不建设大规模全网爬虫或自动规则生产线。

渐进顺序：

```text
V0  权威原则、对象和治理合同
V1  人工提供URL/文件后的单文档统计主张提取
V2  白名单来源检索、去重、版本和反证跟踪
V3  论文与报告库批量处理、字段候选和复现任务生成
V4  定时发现、证据图谱和自动失效监控
V5  与CWMS、因子研究、用户画像和舆情可信度联动
```

实施必须服从“逻辑可以机构级，实现必须个人级”。

## 13. 当前项目优先级

该能力是长期核心横向能力，但不改变当前MVP顺序。

当前仍优先完成：

```text
统一数据质量门禁
→ 市场状态MVP
→ 风险仓位MVP
→ 基础因子与真实A股回测
```

ASEI当前先完成权威记忆、结构归属和字段治理边界；正式实现按后续独立任务推进。
