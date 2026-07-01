# TASK_021A 全项目教学式注释迁移盘点

## 快照基线

- 快照SHA256：`693a1c573f7675781ff1814b846a4da67c4723647fd5f719376cd41f93de5ebc`
- 快照文件条目：283
- Git基线：`e04032a (HEAD -> main, public/main, public/HEAD, origin/main, origin/HEAD) feat: add reusable dolphindb provider plugin bridge`

## 代码规模

- 人工代码文件：123
- Python文件：102
- PowerShell文件：21
- 代码总行数：42861
- 非空代码行：38383
- 现有单行注释：24
- Python函数：1392
- Python类：272
- Python docstring：264

当前绝大多数文件依赖docstring或完全没有教学式`#`前置注释，因此不能通过用户要求的全项目规则。

## 迁移批次

- `BATCH_01_CORE_CONTRACTS_AND_PROVIDER_BOUNDARIES`：10个文件
- `BATCH_02_READINESS_STANDARD_SERVICE_AND_MARKET_STATE`：9个文件
- `BATCH_03_DOLPHINDB_DATA_SERVICES_AND_INGEST`：17个文件
- `BATCH_05_PYTHON_OPERATIONAL_SCRIPTS`：31个文件
- `BATCH_06_TEST_SUITE`：35个文件
- `BATCH_07_POWERSHELL_VERIFICATION_SCRIPTS`：21个文件

## 提交门禁

在全部批次完成、全量测试通过、注释审计通过，并到达用户确认点之前：

```text
GITHUB_COMMIT_BLOCKED = true
GITHUB_PUSH_BLOCKED = true
USER_CONFIRMATION_REQUIRED = true
```

## 批次原则

每一批只改注释和必要的注释审计元数据，不改变业务行为。每批完成后运行专项测试、完整测试、编码审计和Git空白检查。

