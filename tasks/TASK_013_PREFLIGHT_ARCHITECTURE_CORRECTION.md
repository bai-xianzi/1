# TASK_013 前置校正：标准数据核心解耦与本机路径隔离

## 目标

在正式开发基本面Provider之前，校正两个长期扩展风险：

1. 通用`standard_data_service.py`不得直接依赖DolphinDB日K服务；
2. 本机路径、密码和购买的Excel压缩数据不得进入Git。

## 变更

- 通用查询合同和Provider接口保留在：
  `src/a_stock_quant/standard_data_service.py`
- 日K专属Provider移动到：
  `src/a_stock_quant/daily_k_standard_provider.py`
- 增加`.gitignore`保护本机配置、凭据和原始购买数据；
- 更新`PROJECT_STATUS.md`，将TASK_012标记为完成并启动TASK_013；
- 现有查询合同、行为和测试数量保持兼容。

## 不变内容

- 不修改日K数据库、表和映射配置；
- 不修改`DolphinDBDailyKStandardizedService`的金融语义；
- 不开发Excel导入器；
- 不开发基本面因子、模型或回测；
- 不改变现有标准字段。

## 验证

```powershell
python -m compileall src tests
python -m unittest discover -s tests -v
python scripts/audit_git_encoding.py
```

本校正通过后，继续执行TASK_013基本面真实表画像。
