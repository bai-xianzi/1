# TASK_012：统一数据服务接口与标准查询结果合同

## 一、任务依据

TASK_011 已完成真实 DolphinDB 日K标准化抽样验收，
正式下一任务为：

```text
TASK_012：统一数据服务接口与标准查询结果合同
```

本任务继续服务于当前主线：

```text
通用数据接入 → 标准化 → 数据质量与血缘 → 统一数据服务
```

不提前开发因子、策略、回测、前端或完整 CWMS。

## 二、任务目标

在数据集专属服务与下游业务模块之间建立统一、来源无关的数据合同：

```text
下游模块
    ↓ StandardDataQuery
StandardDataService
    ↓
StandardDatasetProvider
    ↓
日K、基本面、行情、竞价、资金流等专属标准化服务
    ↓
StandardQueryResult
```

日K是第一个 Provider，后续数据集不得重新设计另一套下游接口。

## 三、新增文件

- `src/a_stock_quant/standard_data_service.py`
- `tests/test_standard_data_service.py`
- `tasks/TASK_012_STANDARD_DATA_SERVICE.md`
- `scripts/verify_delivery.ps1`

同时更新：

- `PROJECT_STATUS.md`

## 四、统一查询请求

`StandardDataQuery` 显式声明：

- `dataset_id`
- `canonical_object`
- `instrument_ids`
- `start_date`
- `end_date`
- `fields`
- `as_of_date`
- 每只证券最大记录数
- 是否返回来源扩展、质量标记和字段血缘

最小时间安全门禁：

```text
end_date <= as_of_date
```

这不是完整的基本面公告可见性规则。后续基本面 Provider
仍必须使用公告日期或 `available_at` 执行更严格的时点过滤。

## 五、统一查询结果

`StandardQueryResult` 包含：

- 原始标准查询请求；
- 标准对象记录；
- 统一主键；
- 覆盖版本；
- 映射版本；
- 字典版本；
- Provider身份；
- 质量状态；
- 下游阻断标识；
- 质量标记汇总；
- 字段血缘条目数；
- 警告信息。

## 六、日K Provider

`DailyKStandardDataProvider` 将 TASK_010 的
`DolphinDBDailyKStandardizedService` 接入统一服务。

当前支持：

- `DailyBar`
- `OwnershipSnapshot`

支持：

- 标准字段投影；
- 来源扩展按需返回；
- 质量标记按需返回；
- 血缘按标准对象和字段过滤；
- 阻断质量标记传播；
- 覆盖、映射和字典版本传播。

## 七、禁止事项

本任务不得：

- 让下游直接编写 DolphinDB SQL；
- 把来源字段暴露为标准查询字段；
- 新增正式因子；
- 开发市场状态、风险仓位或回测；
- 开发完整基本面可见性逻辑；
- 开发完整 CWMS 生成器。

## 八、自动测试

```powershell
python -m compileall src tests
python -m unittest discover -s tests -v
```

按当前仓库实际测试状态：原有103个测试，本任务新增18个测试。

预期：

```text
Ran 121 tests

OK
```

## 九、任务交付闭环

每个后续任务必须完成：

1. 文件放入正式仓库；
2. 全量测试通过；
3. 更新 `PROJECT_STATUS.md`；
4. 检查 Git 暂存内容；
5. 使用准确任务说明提交；
6. 推送 GitHub；
7. 验证 `HEAD` 与远程分支一致；
8. 完成后再进入下一任务。

## 十、下一关口

TASK_012 完成后，继续：

```text
基本面和七类快照数据注册、语义适配与真实验收
```

数据门禁全部通过后，才开始市场状态与风险仓位 MVP。
