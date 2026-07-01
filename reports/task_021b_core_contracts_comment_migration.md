# TASK_021B 核心合同与Provider边界教学式注释迁移

## 结果

```text
目标文件：10
原始代码行：5562
迁移后总行：12772
新增教学式注释行：7210
业务逻辑变化：false
AST语义变化：false
Git提交允许：false
GitHub推送允许：false
```

## 本批文件

- `src/a_stock_quant/__init__.py`
- `src/a_stock_quant/data_contracts.py`
- `src/a_stock_quant/source_governance.py`
- `src/a_stock_quant/dataset_registry.py`
- `src/a_stock_quant/field_dictionary_governance.py`
- `src/a_stock_quant/vendor_query_manifest.py`
- `src/a_stock_quant/provider_capabilities.py`
- `src/a_stock_quant/provider_plugin_protocol.py`
- `src/a_stock_quant/reuse_first_policy.py`
- `src/a_stock_quant/dolphindb_provider_plugin.py`

## 审计器修正

修正了带装饰器类的前置注释定位：`@dataclass`等装饰器属于类定义的一部分，审计窗口必须从第一个装饰器之前开始。该修正只消除误报，不降低任何注释要求。

## 安全说明

- 所有目标文件迁移前后AST摘要完全一致；
- 没有修改常量、条件、返回值、Provider状态或DolphinDB行为；
- 仍处于全仓库迁移阶段，不允许提交或推送。

