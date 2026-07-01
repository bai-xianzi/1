# TASK_020B 通用Provider插件协议与多来源路由

## 目标

在TASK_020A能力矩阵之上建立所有未来供应商必须遵守的插件协议。

## 协议对象

```text
ProviderPlugin
ProviderRegistryEntry
ProviderDiscoveryResult
SdkRuntimeDescriptor
AuthenticationReference
RateLimitPolicy
RetryPolicy
BatchPolicy
PaginationPolicy
SubscriptionPolicy
LicenseBoundary
ProviderHealthSnapshot
ProviderRouteRequest
ProviderRouteCandidate
```

## 插件方法

```text
describe
discover
health_check
open_session
close_session
query_batch
iter_pages
subscribe
unsubscribe
```

## 安全边界

- 核心系统和上层研究模块不得直接导入厂商SDK；
- 认证信息只能保存`env://`、`keyring://`等引用；
- 未完成能力发现、许可证审查和真实验收的插件不得路由；
- 数据读取和交易执行必须分开激活；
- TASK_020B不安装、导入或调用商业SDK；
- TASK_020B不访问网络和DolphinDB；
- 种子注册表没有任何已启用路由。

## 单机边界

插件运行策略继承TASK_020A资源档案：

```text
Provider并发不超过2
无人工覆盖最大批次100000行
大文件任务必须磁盘预检
```

## 下一步

TASK_020C把现有DolphinDB Adapter包装成第一个通用Provider插件桥，并完成离线合同与真实只读回归验收。
