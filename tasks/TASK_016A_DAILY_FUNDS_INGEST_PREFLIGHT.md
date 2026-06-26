# TASK_016A 七类日线资金Raw摄取预导入

## 目标

在连接或修改DolphinDB之前，用正式摄取解析器对本机七类日线资金执行一次全量只读预导入。

## 来源

- hq：个股收盘行情
- hy：行业收盘行情
- gn：概念收盘行情
- kphq：个股集合竞价
- kphy：行业集合竞价
- kpgn：概念集合竞价
- zj：个股资金流

文件扩展名是 `.xls`，实际格式是GB18030编码的制表符文本。

## 物理Raw层规划

七个逻辑数据集映射到三个共享物理Raw表：

1. `security_market_snapshot_raw`
   - hq
   - kphq

2. `classification_market_snapshot_raw`
   - hy
   - gn
   - kphy
   - kpgn

3. `money_flow_snapshot_raw`
   - zj

另有：

- `ingest_batch_log`
- `ingest_file_log`
- `quarantine_file_log`

这样保留七类逻辑身份，同时避免复制三套完全相同的物理Schema。

## TASK_016A做什么

- 识别13个已知表头版本；
- 解析GB18030制表符文本；
- 从父目录推导snapshot_date；
- 标准化Excel公式样式证券代码；
- 解析万、亿、万亿；
- 保持资金流流出字段的来源负号；
- 解析行业和概念涨跌家数；
- 检查畸形行、重复实体键和未知Schema；
- 执行kphq/hq、kphy/hy、kpgn/gn、zj/hq覆盖门禁；
- 生成DolphinDB写入计划；
- 输出隔离清单和标准化样本。

## TASK_016A不做什么

- 不连接DolphinDB；
- 不创建数据库；
- 不创建表；
- 不写入任何记录；
- 不把source_file_mtime伪装成available_at；
- 不把分类名称伪造成稳定node_id；
- 不静默补齐缺失文件；
- 不导入覆盖不完整的2025-12-23 kphq。

## 门禁

- 未知Schema：BLOCKED
- 畸形行：BLOCKED
- 同文件重复实体键：BLOCKED
- 行标准化失败：BLOCKED
- 覆盖率低于95%：QUARANTINED
- 缺失文件：WARNING

## 预期全量结果

根据TASK_015B物理画像，预期：

- 日期目录：30
- 源文件：185
- 解析行：462,254
- 隔离文件：1
- 隔离行：288
- 计划写入行：461,966
- 总体状态：READY_WITH_QUARANTINE

以上只是预期，必须以TASK_016A新解析器在本机实际运行结果为准。

## 验收命令

```powershell
$env:PYTHONPATH = (Resolve-Path ".\src").Path

python ".\scripts\run_task_016a_daily_funds_preflight.py" `
  --validate-contract-only

python -m unittest tests.test_daily_funds_ingest -v

python -m unittest discover -s tests -v

python ".\scripts\audit_git_encoding.py"
```

全量预导入：

```powershell
python ".\scripts\run_task_016a_daily_funds_preflight.py" `
  --root "D:\Users\Administrator\Desktop\数据导入\日线资金\2025\2025\2025" `
  --output-dir "D:\Users\Administrator\task_016a_daily_funds_preflight"
```

## 下一任务

TASK_016B根据本次报告创建DolphinDB数据库和Raw表，并执行真实写入和验收。
