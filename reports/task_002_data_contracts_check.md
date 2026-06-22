# TASK_002 数据契约验收记录

## 1. 任务目标

建立最小、通用、可扩展的数据接入契约，不连接 DolphinDB，不读取真实数据，不修改任何现有数据库或表。

## 2. 本次文件

### `src/a_stock_quant/data_contracts.py`

职责：定义不同数据来源与下游模块之间交换数据时必须遵守的标准接口、状态和数据结构。

主要内容：

- `SourceType`
- `MappingStatus`
- `QualityStatus`
- `QualityLevel`
- `ConfirmationStatus`
- `BlockingLevel`
- `DataContractError`
- `RawDataBatch`
- `FieldMappingResult`
- `DataQualityResult`
- `PendingConfirmation`
- `CanonicalDataBatch`
- `DataLineageRecord`
- `DataSourceAdapter`

### `tests/test_data_contracts.py`

职责：使用 Python 标准库 `unittest` 验证数据契约的正常路径、错误路径、阻断逻辑和适配器接口。

## 3. 输入与输出

### 输入

- 原始来源标识、来源类型、原始字段和原始记录；
- 字段映射状态和标准字段引用；
- 数据质量检查结果；
- 待人工确认事项；
- 原始批次到标准批次的血缘信息。

### 输出

- 结构化原始数据批次；
- 结构化字段映射结果；
- 结构化质量检查结果；
- 结构化待确认事项；
- 结构化标准数据批次；
- 结构化数据血缘记录；
- 统一的数据来源适配器接口。

## 4. 运行命令

```powershell
python -m compileall src tests
python -m unittest discover -s tests -v
```

## 5. 验证标准

- Python 源码与测试文件可以完成编译；
- 19 个自动测试全部通过；
- 不安装第三方依赖；
- 不连接 DolphinDB；
- 不读取真实业务数据；
- 不修改任何数据库、表或字段。

## 6. 已验证结果

在 Python 3.11 环境完成验证：

- `compileall`：通过；
- `unittest`：19 个测试全部通过；
- 总耗时约 0.006 秒；
- 最终状态：`OK`。

## 7. 尚未完成内容

以下内容不属于 TASK_002，本次没有开发：

- DolphinDB 具体连接适配器；
- Excel、CSV、API 的正式读取逻辑；
- 真实字段映射配置；
- 真实数据质量规则；
- DolphinDB 数据写入或表结构修改。

## 8. 回退方法

尚未提交时：

```powershell
git restore src/a_stock_quant/data_contracts.py tests/test_data_contracts.py reports/task_002_data_contracts_check.md
```

提交后需要撤销时，应使用新的回退提交，不使用破坏性历史重写命令。
