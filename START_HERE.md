# START_HERE.md

<!-- TASK_024C_PROVIDER_CONNECTION_CENTER_START_HERE_START -->

涉及券商、交易所、商业数据SDK、API Key、证书或连接UI时，开始编码前必须阅读`PROVIDER_CONNECTION_CENTER.md`，并确认具体字段已有官方文档依据、秘密只保存为操作系统凭据引用、交易激活保持阻断。

<!-- TASK_024C_PROVIDER_CONNECTION_CENTER_START_HERE_END -->


## 这一步只做什么

这是项目正式启动的第一个动作：

> 把最新权威记忆、字段字典、复用优先政策和工程规则放入正式Git仓库，并替换旧的`AGENTS.md`和`PROJECT_CONTEXT.md`。

这一步不编写业务代码，不连接DolphinDB，不修改数据库。

## 操作方法

1. 在电脑上创建或打开项目正式Git仓库。
2. 将本启动包全部解压到仓库根目录。
3. 如果仓库已有同名文件，先备份或查看Git差异，再使用本版本更新。
4. 在VSCode终端运行：

```bash
git status
```

5. 确认以下文件存在：

```text
AGENTS.md
PROJECT_CONTEXT.md
PROJECT_MEMORY.md
SYSTEM_ARCHITECTURE.md
PROJECT_STATUS.md
DEVELOPMENT_GUIDANCE.md
REUSE_FIRST_ENGINEERING_POLICY.md
CODEX_EXECUTION_POLICY.md
schemas/canonical_fields.yaml
schemas/enum_definitions.yaml
```

6. 将`tasks/TASK_001_REPOSITORY_BOOTSTRAP.md`交给Codex执行。

## 本步骤验收标准

- 仓库不再出现“当前仍处于第0步”的错误描述；
- `CURRENT / NEXT / FUTURE / RESERVED`边界清晰；
- 开发执行者能够找到全部权威文件，并在编码前读取复用优先政策；
- 没有修改DolphinDB；
- 没有创建业务代码；
- Git差异只包含项目上下文和权威文件。
