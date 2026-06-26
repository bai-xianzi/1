# TASK_017D 七类 StandardDataService Provider 与统一入口验收

## 目标

- 扩展统一查询合同，使证券使用`instrument_ids`，分类节点使用`entity_ids`；
- 为七类来源分别注册Provider；
- 统一输出版本、质量、血缘和用途级门禁；
- 通过StandardDataService完成真实DolphinDB只读验收。

## 兼容性

既有日K和基本面调用继续使用`instrument_ids`。新字段`entity_ids`为可选，
但两种选择器必须且只能提供一种。Provider描述新增`selector_mode`，既有Provider
默认仍为`INSTRUMENT_ID`。

## 时点门禁

七类来源没有可证明的精确`available_at`：

- 当前快照研究：允许，保留WARNING；
- 同日人工决策：阻断；
- 严格历史回测：阻断；
- 历史模型训练：阻断。

## 安全边界

- 只调用TASK_017C只读服务；
- 不写入DolphinDB；
- 不伪造分类节点为证券；
- 不伪造精确可用时间。
