# TASK_021 全项目教学式代码注释恢复

## 目标

为项目全部人工编写代码补充与逻辑一一对应的教学式前置注释，同时保持业务逻辑、金融语义、数据门禁、查询行为和评分公式不变。

## 最终保留资产

```text
CODE_COMMENTING_STANDARD.md
configs/engineering/code_comment_policy_v0.json
src/a_stock_quant/code_comment_policy.py
scripts/audit_teaching_comments.py
tests/test_code_comment_policy.py
tasks/TASK_021_CODE_COMMENT_RESTORATION.md
reports/task_021_code_comment_restoration_closure.md
```

## 已收敛内容

A至H阶段任务书、阶段验证脚本、阶段迁移测试、临时日志和阶段报告已由统一任务书、统一政策测试、统一审计器和最终关闭报告替代。

## 长期门禁

1. 新增或修改的人工代码必须满足教学式前置注释标准。
2. docstring不能替代逻辑代码前的单行教学式说明。
3. 提交前必须运行统一注释审计、专项测试、完整测试、编码审计和`git diff --check`。
4. 注释迁移完成只解除临时迁移阻断，不解除用户确认和项目其他门禁。
5. 阶段施工记录仍可通过Git历史追溯，不再占用主工作区。

## 状态

```text
TASK_STATUS = COMPLETE
COMMENT_MIGRATION_STATUS = COMPLETE
BUSINESS_LOGIC_CHANGED = false
DATABASE_WRITE_REQUIRED = false
```
