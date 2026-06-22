# 通用事件—实体—关系—影响领域模型

## 1. 为什么不能只用一个0/1字段

布尔值适合表达“是否发生”，不适合表达：

- 影响对象；
- 损失比例；
- 停运时长；
- 恢复时间；
- 替代能力；
- 不同主体的不同后果。

因此：

```text
事件是否发生：BOOL
事件是什么：event_type_code
影响谁：target_entity_id
影响哪方面：impact_type_code / impact_metric_code
影响多大：impact_value_numeric / 区间
持续多久：开始、结束、停运和恢复时间
为何传播：实体关系、暴露关系和因果规则
```

## 2. 六个核心对象

### WorldEntity

国家、地区、行业、公司、工厂、仓库、港口、航线、商品和市场。

### EntityRelation

拥有、运营、位于、依赖、供应、客户、支柱产业、GDP占比、出口占比等稳定关系。

### WorldEvent

战争、制裁、空袭、火灾、洪水、地震、停工、港口关闭、政策变化和价格冲击。

### EventImpact

事件对某实体的动态后果。一个事件对同一实体可以有多条影响指标。

### EntityExposure

主体对地区、供应链、商品、基础设施和政策的敏感度或脆弱性。

### CausalRule

将影响继续传播到企业经营、参与者行为、资本迁移和市场行情的已审核规则。

## 3. 例子

### 仓库被空袭

```text
WorldEvent:
  type = AIR_STRIKE
  active = true

EventImpact:
  target = WAREHOUSE_001
  type = INVENTORY_LOSS
  metric = INVENTORY_LOSS_PCT
  value = 40
  downtime = 30天
  recovery = 90天
```

### 某国支柱产业受损

```text
EntityRelation:
  国家A --PILLAR_INDUSTRY_OF--> 石油行业
  GDP占比 = 30%
  出口占比 = 70%

WorldEvent:
  type = WAR

EventImpact:
  target = 石油行业
  metric = CAPACITY_LOSS_PCT
  value = 25%
```

## 4. 字段新增判断

新需求优先扩展事件类型、实体类型、关系类型、影响类型、影响度量或因果规则。只有通用模型不能表达的稳定金融概念，才新增标准字段。


## 5. 产品界面与底层模型的分离

用户界面可以保持简单：

```text
战争：开/关
仓库受损：开/关
受损程度：滑块
预计恢复：天数
```

但底层必须转成结构化对象：

```text
WorldEvent
+ WorldEntity
+ EventImpact
+ EntityRelation / EntityExposure
```

简单界面不等于简单数据模型。这样既方便用户操作，也能保证因果传播、版本管理和未来扩展。

