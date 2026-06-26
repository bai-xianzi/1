# TASK_017 七类日线资金标准接入关闭记录

## 关闭条件

- Canonical映射合同通过；
- 字段字典升级到0.6.0；
- ClassificationMarketSnapshot已建立；
- AuctionSnapshot日期级时间精度已治理；
- 三张Raw表只读Canonical服务通过真实验收；
- 七个StandardDataService Provider完成注册；
- 七类统一真实查询全部返回结果；
- 证券与分类节点选择器边界正确；
- 严格历史用途全部由时点门禁阻断；
- 数据库写操作为0；
- 验收报告和PROJECT_STATUS已更新。

## 结论

TASK_017允许关闭，但状态保留`PASSED_WITH_WARNINGS`。
后续模块不得绕过StandardDataService和用途级门禁直接读取Raw表。
