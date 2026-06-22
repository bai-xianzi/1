# TASK_009：通用 DolphinDB 数据集注册表与标准字段映射引擎

## 一、任务目标

建立可持续扩展的数据接入核心，使未来新增基本面、行业、概念、
资金流、竞价和其他 DolphinDB 表时，只需要新增注册配置和必要的
转换插件，不需要重写整个系统。

## 二、核心原则

- DolphinDB 表结构不能直接成为系统核心结构；
- 系统核心只使用统一字段字典中的 canonical 字段；
- 每个来源字段必须处于以下状态之一：
  - `MAPPED`
  - `WARNING`
  - `PENDING_CONFIRMATION`
  - `UNMAPPED`
- 未确认字段保留在来源扩展中，不允许静默丢弃；
- 一个来源数据集可以输出多个标准对象；
- 每次映射必须保留转换规则、映射版本和字段字典修订号。

## 三、新增文件

- `src/a_stock_quant/dataset_registry.py`
- `tests/test_dataset_registry.py`
- `configs/datasets/a_stock_daily_k.json`
- `tasks/TASK_009_DATASET_REGISTRY_AND_MAPPING_ENGINE.md`

## 四、本任务提供的能力

1. `DatasetRegistration`
   - 数据集ID
   - 来源位置
   - 覆盖版本
   - 来源字段
   - 主键
   - 标准对象
   - 字段映射合同

2. `DatasetRegistry`
   - 注册、覆盖、查找和筛选数据集
   - 从JSON目录批量加载注册配置

3. `CanonicalFieldCatalog`
   - 校验标准对象及 canonical 字段名称

4. `TransformRegistry`
   - 可插拔转换函数
   - 单位转换
   - 价格变动和涨跌幅计算

5. `CanonicalMappingEngine`
   - 将一个来源记录输出为一个或多个标准对象片段
   - 保留未映射来源字段
   - 输出字段级数据血缘

## 五、初始日K注册配置

`a_stock_daily_k.json` 对当前48个来源字段全部进行了显式登记。

已确认字段进入：

- `DailyBar`
- `OwnershipSnapshot`

尚未确认的技术指标、专有信号、公司行为单位和复权方向继续保留为
`PENDING_CONFIRMATION`，不会被静默丢弃。

## 六、自动测试

```powershell
python -m compileall src tests
python -m unittest discover -s tests -v
```

预期：82个测试全部通过。

## 七、下一任务

`TASK_010：日K标准映射插件与批量标准化读取服务`

它将使用本任务的通用引擎，真正把 DolphinDB 日K行转换为
`DailyBar` 和 `OwnershipSnapshot` 标准对象。
