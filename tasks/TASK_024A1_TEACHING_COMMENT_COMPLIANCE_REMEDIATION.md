# TASK_024A1：TASK_022至TASK_024教学式前置注释合规整改

## 任务目标

本任务修复TASK_022、TASK_023A/B/C和TASK_024A人工代码未在沙盒阶段完整写入教学式前置注释的问题。整改只允许增加或完善注释、注释审计、回归测试和权威流程说明，不改变Provider选择、数据语义、Readiness、数据库或交易能力。

## 强制工作流

```text
需求与复用调查
→ 代码和教学式前置注释同步设计
→ 注释合规审计
→ 语法检查
→ 专项测试
→ 历史任务回归
→ 全项目测试
→ 编码检查与git diff --check
→ 用户确认
→ 独立Git提交并推送GitHub main
```

禁止先生成无注释代码、测试通过后再补注释。进入沙盒第一次语法检查之前，人工代码就必须达到`CODE_COMMENTING_STANDARD.md`的最低结构要求。

## 整改范围

- TASK_022 DolphinDB Provider激活相关Python与PowerShell人工代码；
- TASK_023A/B/C Provider环境发现、Windows盘点和候选选择代码；
- TASK_024A 官方交易所与券商来源权威代码；
- 对应入口脚本、单元测试和长期注释回归门禁；
- `CODE_COMMENTING_STANDARD.md`与`DEVELOPMENT_GUIDANCE.md`中的沙盒前置要求。

## 安全边界

```text
业务算法变化：0
Provider激活变化：0
供应商SDK导入：0
网络调用：0
数据库写操作：0
交易能力激活：0
秘密值读取：0
```

## 完成标准

- 目标类、函数、主要分支、循环、异常和资源上下文前均有完整教学块；
- 官方全仓库教学注释审计通过；
- TASK_022至TASK_024专项与回归测试通过；
- 全项目单元测试通过；
- `git diff --check`通过；
- 独立提交推送到GitHub `main`，本地工作区恢复干净。
