# TASK_015C-1 标准词典治理加固

## 目标

在日线资金DolphinDB物理表冻结前，对修订0.5执行非破坏性治理加固。

## 完成内容

1. 字典修订号升级为0.5.1；
2. 补齐已确认的时间语义和经纬度单位；
3. 新增 `field_governance_contract.yaml`；
4. 明确五类值域：封闭枚举、受控代码集、开放代码、标识符、自由文本；
5. 登记 `trade_count` 语义冲突及非破坏性迁移计划；
6. 登记 `value_numeric` 合理的上下文类型差异；
7. 新增机器校验器和单元测试；
8. 保持1201个字段及生命周期数量不变。

## 不做

- 不修改DolphinDB；
- 不导入日线资金；
- 不删除future_reserved；
- 不机械修改全部INFO候选；
- 不直接重命名已使用字段；
- 不把来源字段直接提升为Canonical。

## 验收

- `python scripts/validate_task_015c1_dictionary_governance.py`
- `python -m unittest discover -s tests -v`
- `python scripts/audit_git_encoding.py`
- `git diff --check`
