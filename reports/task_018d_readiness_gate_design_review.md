# TASK_018D 统一就绪度门禁设计审查

## 审查结论

状态：`PASSED_OFFLINE_DESIGN`

## 关键改动

此前下游可能分别调用：

```text
StandardDataService.query()
DataReadinessEngine.evaluate()
```

这种分离方式存在调用方只取标准查询结果、遗漏统一门禁的风险。

TASK_018D新增组合服务：

```text
ReadinessGatedStandardDataService.query()
```

返回：

```text
ReadinessGatedQueryResult
├─ standard_result
└─ readiness_snapshot
```

其`assert_usable()`依次执行：

1. `StandardQueryResult.assert_usable()`
2. `DatasetReadinessSnapshot.assert_usable()`

因此Provider阻断和八维就绪度阻断都不能被静默忽略。

## 真实验收设计

验收脚本连接本地DolphinDB，但只执行：

- 健康检查；
- 每个数据集抽取一个真实样本实体和日期；
- 通过九个标准Provider进行查询；
- 生成八维证据；
- 执行四种用途政策；
- 输出只读验收报告。

验收脚本不直接读取数据用于下游分析，也不执行任何DDL或DML。

## 预期结果

- 当前研究：9个数据集可用，通常携带WARNING；
- 人工决策：9个数据集阻断；
- 严格历史回测：至少8个数据集阻断；
- 历史模型训练：至少8个数据集阻断；
- 日K历史用途由真实证据决定；
- 每次评估完整包含8个证据维度；
- 数据库写操作为0。

## 未解决语义不会被消除

- 日K当前数据时效落后；
- 基本面公告可见时间没有被正式证明；
- 七类快照没有全实体覆盖证明；
- 竞价只有日期级时间；
- 分类实体ID仍需权威主数据；
- 资金流方法仍需供应商文档；
- 七类快照缺少可靠`available_at`。

这些事项继续作为WARNING或BLOCKED证据存在。
