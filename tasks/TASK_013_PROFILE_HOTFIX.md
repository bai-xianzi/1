# TASK_013 基本面画像统计热修复

## 修复原因

首次真实画像中出现互相矛盾的统计：

- 更新日期晚于快照：5528
- 上市日期晚于快照：5528
- 负总股本：5528
- 流通股大于总股本：5528
- 税后利润等于净利润：5541

这些结果与日期范围和真实样例冲突。

## 根因

DolphinDB条件使用了：

```text
not isNull(field) and ...
```

存在逻辑优先级歧义。画像器现在会统一转换为：

```text
not(isNull(field)) and ...
```

同时，空报告期可能以NaN返回，旧逻辑会错误转换为0。
修复后空值不再进入报告期枚举。

## 操作

覆盖两个同名文件后执行：

```powershell
python -m compileall src tests

python -m unittest discover `
  -s tests `
  -p "test_dolphindb_fundamental_profile.py" `
  -v

Remove-Item `
  ".\reports\task_013_fundamental_profile.json" `
  -ErrorAction SilentlyContinue

Remove-Item `
  ".\reports\task_013_fundamental_profile_final_check.md" `
  -ErrorAction SilentlyContinue

python -m a_stock_quant.dolphindb_fundamental_profile
```

修复前生成的画像报告不得提交Git。
