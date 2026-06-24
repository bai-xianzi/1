# 厂商API与来源中立适配合同

## 稳定边界

下游只使用：

```text
dataset_id
canonical_object
StandardDataQuery
StandardQueryResult
```

下游不得出现：

```text
WindPy
THS_iFinD
quantapi URL
DolphinDB物理表名
供应商指标名
```

## 分层

```text
厂商认证
→ 厂商传输客户端
→ VendorQueryManifest
→ RawDataBatch
→ DatasetRegistration
→ CanonicalMappingEngine
→ 语义和时点校验
→ StandardDataService Provider
```

## 查询清单

查询清单必须包含：

- 来源ID；
- 逻辑数据集ID；
- 厂商操作类型；
- 请求模板；
- 来源字段到Canonical字段映射；
- 返回数据路径；
- 分块策略；
- 映射版本；
- 来源模式版本；
- 生成工具和生成日期；
- 是否启用。

凭据只能通过CredentialReference引用环境变量。

## 厂商指标治理

厂商指标和报表ID不是Canonical字段。

```text
厂商指标变化
→ 更新查询清单和映射版本
→ 重新真实验收
→ 下游保持不变
```

## 券商接口边界

市场数据：

```text
行情、历史数据、实时快照、交易日历
```

交易执行：

```text
账户、资金、持仓、订单、撤单、成交
```

两者必须使用不同合同。当前包只实现市场数据来源治理。
