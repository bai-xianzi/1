# TASK_002_DATA_CONTRACTS.md

## 1. 当前项目阶段

```text
CURRENT：通用数据接入骨架 + 数据入库与质量验收
```

## 2. 任务目标

建立项目第一版最小数据接入契约，为后续接入DolphinDB日K、基本面数据、Excel、CSV、API和其他数据库提供统一边界。

本任务只定义通用接口、标准数据结构和测试，不连接DolphinDB，不读取正式数据，不修改数据库。

## 3. 必读文件

开始实施前必须完整阅读：

* `AGENTS.md`
* `PROJECT_CONTEXT.md`
* `PROJECT_MEMORY.md`
* `SYSTEM_ARCHITECTURE.md`
* `PROJECT_STATUS.md`
* `DEVELOPMENT_GUIDANCE.md`
* `CODEX_EXECUTION_POLICY.md`
* `schemas/canonical_fields.yaml`
* `schemas/enum_definitions.yaml`
* `schemas/FIELD_CHANGE_PROCESS.md`
* `reports/repository_bootstrap_check.md`

## 4. 本任务需要解决的问题

定义以下最小稳定边界：

1. 数据来源适配器接口；
2. 原始数据批次及其元数据；
3. 标准化数据批次；
4. 字段映射结果；
5. 数据质量检查结果；
6. 数据血缘记录；
7. 待人工确认事项；
8. 统一错误类型。

## 5. 允许新增的目录和文件

建议新增：

```text
src/
└─ a_stock_quant/
   ├─ __init__.py
   └─ data_contracts.py

tests/
└─ test_data_contracts.py

reports/
└─ task_002_data_contracts_check.md
```

本任务应尽量只创建以上文件，不扩大代码范围。

## 6. 最小对象要求

### 6.1 DataSourceAdapter

使用Python抽象基类或`Protocol`定义最小接口。

至少包括：

```python
source_id
source_type
read_raw(...)
health_check(...)
```

设计要求：

* 不绑定DolphinDB；
* 不绑定Excel；
* 不绑定某个字段名称；
* 后续不同数据来源可以独立实现；
* 当前只定义接口，不实现真实来源连接。

### 6.2 RawDataBatch

至少表达：

* 数据来源ID；
* 来源类型；
* 来源对象名称；
* 读取时间；
* 数据时间范围；
* 原始字段名称；
* 原始数据行数；
* 原始数据内容；
* 来源批次ID；
* 来源文件或数据库对象位置；
* 数据版本；
* 备注。

原始字段和原始值不得在这一层被悄悄修改。

### 6.3 CanonicalDataBatch

至少表达：

* 对应的原始批次ID；
* 标准领域代码；
* 标准对象名称；
* 标准字段版本；
* 标准化后的数据；
* 数据行数；
* 映射版本；
* 转换时间；
* 质量状态；
* 待确认事项。

### 6.4 FieldMappingResult

至少表达：

* 来源字段；
* 标准字段完整引用；
* 映射状态；
* 来源类型；
* 目标类型；
* 来源单位；
* 目标单位；
* 转换规则；
* 是否需要人工确认；
* 错误或警告信息。

不允许自动猜测复权、单位和时间语义。

### 6.5 DataQualityResult

至少表达：

* 检查ID；
* 检查名称；
* 检查级别；
* 检查状态；
* 检查总行数；
* 失败行数；
* 失败比例；
* 样例异常；
* 是否阻断下游；
* 检查时间；
* 说明。

建议状态：

```text
PASSED
WARNING
FAILED
PENDING_CONFIRMATION
```

### 6.6 DataLineageRecord

至少表达：

* 血缘记录ID；
* 来源批次ID；
* 目标批次ID；
* 来源位置；
* 目标对象；
* 映射版本；
* 转换版本；
* 代码版本；
* 配置版本；
* 转换时间；
* 转换说明。

### 6.7 PendingConfirmation

至少表达：

* 确认事项ID；
* 事项类别；
* 来源对象；
* 字段或对象名称；
* 问题说明；
* 可能选项；
* 当前状态；
* 阻断级别；
* 创建时间；
* 解决时间；
* 解决结论。

典型事项包括：

* 复权方式未知；
* 成交量单位未知；
* 成交额单位未知；
* 日期业务含义未知；
* 字段定义冲突；
* 多来源数值冲突。

## 7. 数据内容类型要求

第一版可使用：

```python
list[dict[str, Any]]
```

作为批次数据容器。

当前不要引入Pandas、Polars、PyArrow或数据库依赖。

原因：

* 先稳定接口和语义；
* 避免数据框架绑定；
* 后续可在适配器内部转换；
* 降低当前安装和运行复杂度。

## 8. 类型和实现原则

* 使用Python 3.11；
* 优先使用标准库；
* 可使用：

  * `dataclasses`
  * `typing`
  * `abc`
  * `enum`
  * `datetime`
  * `uuid`
* 不安装新依赖；
* 类型定义应清晰；
* 重要字段应有简短中文或英文注释；
* 不实现业务算法；
* 不实现数据库连接；
* 不修改字段字典；
* 不创建空的大型架构。

## 9. 测试要求

测试至少覆盖：

1. 可以创建一个原始数据批次；
2. 可以创建一个标准数据批次；
3. 可以创建字段映射结果；
4. 可以创建通过、警告、失败和待确认质量结果；
5. 可以创建血缘记录；
6. 可以创建待确认事项；
7. 批次ID和检查ID非空；
8. 阻断状态可以被明确判断；
9. 一个最小虚拟适配器能够符合`DataSourceAdapter`接口；
10. 不需要连接DolphinDB即可运行全部测试。

优先使用标准库`unittest`，不要安装`pytest`。

## 10. 禁止事项

禁止：

* 连接或修改DolphinDB；
* 猜测日K字段含义；
* 创建DolphinDB专用实现；
* 创建完整ETL系统；
* 创建因子、模型、回测或前端；
* 新增、删除或改名标准字段；
* 引入Pandas等第三方依赖；
* 建立微服务；
* 修改总体架构；
* 修改开发顺序；
* 大规模重构已有文档。

## 11. 验证命令

至少运行：

```powershell
python -m unittest discover -s tests -v
```

以及：

```powershell
python -m compileall src
```

## 12. 验收标准

任务完成必须满足：

* 通用接口不依赖DolphinDB；
* 核心数据对象可以单独实例化；
* 测试全部通过；
* 代码可以编译；
* 没有安装新依赖；
* 没有连接数据库；
* 没有修改字段字典；
* 没有创建与当前任务无关的功能；
* 生成`reports/task_002_data_contracts_check.md`；
* Git差异只包含本任务允许的文件。

## 13. 检查报告内容

`reports/task_002_data_contracts_check.md`至少记录：

* 新增文件；
* 每个文件的职责；
* 对象和接口清单；
* 运行命令；
* 测试结果；
* 是否安装依赖；
* 是否连接数据库；
* 是否修改字段字典；
* 已知限制；
* 下一步建议。

## 14. 完成汇报格式

完成后按以下顺序汇报：

1. 新增或修改的文件；
2. 每个文件的职责；
3. 核心接口和对象；
4. 运行命令；
5. 实际测试结果；
6. 已知限制；
7. 是否安装依赖；
8. 是否连接或修改数据库；
9. 是否修改字段字典；
10. 如何撤销本次修改。
