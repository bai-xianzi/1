# TASK_020C DolphinDB插件桥设计评审

## 复用决定

选择：

```text
WRAP_WITH_THIN_ADAPTER
```

不选择重新开发DolphinDB客户端。

## 原因

现有Adapter已经实现：

- 延迟连接；
- 连接异常包装；
- 健康检查；
- 表名和数据库URI安全检查；
- 只读脚本白名单与写操作黑名单；
- 有限行数读取；
- 常见返回值标准化；
- RawDataBatch构建。

重新开发这些内容会形成重复代码和两套安全边界。

## 薄桥接责任

桥接层只负责把已有行为翻译为TASK_020B对象：

```text
DataQualityResult
→ ProviderHealthSnapshot

RawDataBatch
→ ProviderQueryBatch

现有Adapter能力
→ ProviderDiscoveryResult
```

## 已知遗留限制

现有Adapter没有公开`close()`方法，桥接层只能在该方法存在时调用，否则由进程生命周期释放会话。

现有返回值标准化方法是私有方法。薄桥接暂时复用它，后续可以在不改变逻辑的情况下将其提升为公开稳定方法。

## 激活策略

TASK_020C只产生真实验收报告，不直接修改种子注册表和能力矩阵。这样可防止测试过程中自动激活数据源。

TASK_020D在报告核验后执行正式激活和路由回归。
