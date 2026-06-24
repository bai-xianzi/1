# TASK_015 多源接口合同与七类快照盘点

## 任务定位

本任务仍属于权威PROJECT_STATUS中的TASK_015：

```text
七类快照数据源盘点、物理结构发现与接入优先级确认
```

为保证未来可接 Wind、iFinD 和券商而不推倒重来，
本任务先增加来源中立的治理合同和厂商模板。
不改变已验收的日K、基本面和StandardDataService行为。

## 子任务

### TASK_015A：多源接入合同

- SourceDescriptor；
- SourceCapability；
- DatasetSourceBinding；
- SourceRole；
- SourceCatalog；
- ConflictRecord；
- VendorQueryManifest；
- Wind和iFinD禁用模板；
- 离线测试。

### TASK_015B：七类快照物理盘点

- hq；
- hy；
- gn；
- kphq；
- kphy；
- kpgn；
- zj。

输出每类来源文件、字段、类型、样例、覆盖、主键、单位、
时间语义、可见时间、Canonical候选和待确认事项。

## 约束

- 不保存凭据；
- 不调用尚未购买的厂商接口；
- 不修改DolphinDB原始表；
- 不启用Wind或iFinD模板；
- 不修改下游业务模块；
- 不开发因子、模型、回测或自动交易；
- 不把券商订单执行混入市场数据适配器。

## 验收

```powershell
$env:PYTHONPATH = (Resolve-Path ".\src").Path
python -m compileall src tests scripts
python -m unittest discover -s tests -v
python ".\scripts\validate_task_015_source_templates.py"
```

真实厂商接口验收必须等取得账号和权限后另立任务。
