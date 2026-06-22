# TASK_010：日K标准映射插件与批量标准化读取服务

## 一、任务目标

使用 TASK_009 的通用数据集注册表和映射引擎，完成第一条真实的
DolphinDB → 操作系统标准对象读取链路。

## 二、新增与修改文件

1. `src/a_stock_quant/dolphindb_daily_k_service.py`
   - 日K专用只读查询；
   - 前收盘上下文；
   - 批量标准化；
   - 质量标记；
   - 覆盖边界门禁。

2. `tests/test_dolphindb_daily_k_service.py`
   - 标准对象映射测试；
   - 多证券读取测试；
   - 日期边界测试；
   - 来源扩展和血缘测试。

3. `configs/datasets/a_stock_daily_k.json`
   - mapping_version 升级为 `0.2.0`；
   - 增加前收盘、标准涨跌幅、成交手数、VWAP和市值映射；
   - 来源反向 `pct_change` 继续保留在来源扩展。

4. `tasks/TASK_010_DAILY_K_STANDARDIZED_SERVICE.md`
   - 任务说明、运行方式、验收和回退方法。

## 三、标准输出

每条来源日K记录输出：

- `DailyBar`
- `OwnershipSnapshot`
- `source_extensions`
- `quality_flags`
- `lineage`

当前不会生成 `CorporateAction`，因为公司行为字段单位仍未最终确认。

## 四、主要标准化规则

- `volume_shares = volume`
- `volume_lots = volume / 100`
- `vwap_raw_cny = amount / volume`
- `pre_close_raw_cny = 上一交易日 close`
- `pct_change_pct = (close / prev_close - 1) × 100`
- `float_shares = 来源 float_shares × 10000`
- `total_shares = 来源 total_shares × 10000`
- `float_market_cap_cny = close × float_shares × 10000`
- `total_market_cap_cny = close × total_shares × 10000`

来源 `pct_change` 不覆盖标准涨跌幅，继续作为来源扩展保留。

## 五、安全边界

- 所有 DolphinDB 查询只读；
- 单次最多100只证券；
- 每只证券最多5000行；
- 查询结束日期不得超过注册配置的覆盖截止日期；
- 不修改 DolphinDB 原始字段；
- 未确认字段不会静默丢弃。

## 六、自动测试

```powershell
python -m compileall src tests
python -m unittest discover -s tests -v
```

预期：93个测试全部通过。

## 七、当前任务不包含

- 不开发正式因子；
- 不开发图表；
- 不开发股票池；
- 不批量写入标准数据库；
- 不确认前复权/后复权方向；
- 不把来源技术指标直接认定为平台技术指标。

## 八、下一任务

`TASK_011：真实 DolphinDB 日K标准化抽样验收与字段覆盖报告`
