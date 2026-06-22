# TASK_003_DOLPHINDB_READONLY_ADAPTER.md

## 当前阶段

通用数据接入骨架 + 数据入库与质量验收。

## 任务目标

实现第一个真实来源适配器骨架：DolphinDB只读适配器。

## 本任务只做

- 连接参数校验；
- 延迟建立DolphinDB会话；
- 健康检查；
- 从指定DFS表读取有限行原始数据；
- 转换为`RawDataBatch`；
- 使用假会话完成单元测试。

## 明确不做

- 不创建、删除或修改数据库和表；
- 不执行写入；
- 不推断复权方式；
- 不推断成交量和成交额单位；
- 不推断日期语义；
- 不开始因子、模型和回测；
- 不在代码中硬编码真实密码。

## 计划文件

- `src/a_stock_quant/dolphindb_adapter.py`
- `tests/test_dolphindb_adapter.py`
- `tasks/TASK_003_DOLPHINDB_READONLY_ADAPTER.md`

## 验收命令

```powershell
python -m compileall src tests
python -m unittest discover -s tests -v
```

## 验收结果要求

- 现有19个数据契约测试继续通过；
- 新增6个DolphinDB适配器测试通过；
- 合计25个测试通过；
- 未连接或修改真实数据库。
