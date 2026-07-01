# TASK_021B 核心合同与Provider边界教学式注释迁移

## 目标

为数据合同、来源治理、数据集注册、字段字典、Vendor清单、Provider能力、插件协议、复用政策和DolphinDB插件桥补齐教学式前置注释。

## 硬约束

```text
只增加或修正注释
AST语义必须完全一致
完整测试必须通过
全仓库迁移尚未完成
禁止git commit
禁止git push
```

## 本批完成标准

- 十个目标源文件通过批次注释审计；
- 装饰器类审计误报已修正；
- 原有业务测试全部通过；
- 生成AST语义一致性报告；
- 保持TASK_021A提交阻断状态。

## 下一批

TASK_021C处理Readiness、StandardDataService和Market State模块。
