# TASK_001_REPOSITORY_BOOTSTRAP.md

## 1. 项目阶段

```text
CURRENT：通用数据接入骨架 + 数据入库与质量验收
```

## 2. 任务目的

完成正式代码仓库的权威上下文初始化，使后续Codex任务基于同一套项目记忆、总体架构、字段字典和阶段边界执行。

本任务只做仓库检查和权威文件一致性验收，不编写业务代码。

## 3. 必读文件

开始前完整阅读：

- `AGENTS.md`
- `PROJECT_CONTEXT.md`
- `PROJECT_MEMORY.md`
- `SYSTEM_ARCHITECTURE.md`
- `PROJECT_STATUS.md`
- `DEVELOPMENT_GUIDANCE.md`
- `CODEX_EXECUTION_POLICY.md`
- `README_PROJECT_MEMORY.md`
- `schemas/canonical_fields.yaml`
- `schemas/enum_definitions.yaml`
- `schemas/FIELD_CHANGE_PROCESS.md`

## 4. 允许修改范围

只允许：

- 修正权威Markdown文件中的明显路径错误、版本号错误或互相矛盾的当前阶段描述；
- 新增一份仓库上下文检查报告：
  - `reports/repository_bootstrap_check.md`

如`reports/`不存在，可以创建该目录。

## 5. 禁止修改范围

禁止：

- 修改或连接DolphinDB；
- 创建数据适配器；
- 创建因子、模型、回测或前端代码；
- 修改`schemas/canonical_fields.yaml`中的字段定义；
- 修改总体架构和开发顺序；
- 安装依赖；
- 大规模整理或重写权威文档；
- 删除任何现有代码或用户文件。

## 6. 执行步骤

1. 运行`git status`，记录仓库当前状态。
2. 检查必需权威文件是否存在。
3. 搜索以下过期或冲突表达：
   - `当前只处于第0步`
   - `当前处于第0步`
   - 把TradingView工作台列为数据验收后的立即优先项
   - 把自动交易或完整CWMS列为当前任务
4. 检查`PROJECT_STATUS.md`的当前阶段是否与`AGENTS.md`、`PROJECT_CONTEXT.md`一致。
5. 检查权威文件引用的关键schema文件是否存在。
6. 不改变金融语义的前提下，修复明确的文档矛盾。
7. 生成`reports/repository_bootstrap_check.md`。

## 7. 检查报告必须包含

- 检查日期；
- Git状态摘要；
- 必需文件清单及是否存在；
- 当前阶段解析结果；
- 发现的冲突；
- 实际修改的文件；
- 未解决问题；
- 是否发现数据库或代码风险；
- 下一步建议。

## 8. 验收标准

- 所有必需权威文件存在；
- 当前阶段统一为：
  `通用数据接入骨架 + 数据入库与质量验收`
- 不再保留“当前第0步”的有效指令；
- `CURRENT / NEXT / FUTURE / RESERVED`边界无冲突；
- 没有修改数据库和业务代码；
- 检查报告真实记录执行结果；
- 运行过至少以下验证命令：

```bash
git status
python -c "import yaml; yaml.safe_load(open('schemas/canonical_fields.yaml', encoding='utf-8')); yaml.safe_load(open('schemas/enum_definitions.yaml', encoding='utf-8')); print('YAML_OK')"
```

## 9. 完成汇报格式

请按以下格式汇报：

1. 新增和修改文件；
2. 每个文件职责；
3. 运行的命令；
4. 实际验证结果；
5. 发现的冲突；
6. 未解决问题；
7. 是否修改数据库；
8. 是否修改业务代码；
9. 如何撤销本次修改。
