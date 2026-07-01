# Provider插件协议

## 稳定接口

```text
Provider Capability Matrix
        ↓
Provider Plugin Registry
        ↓
Provider Discovery Result
        ↓
Explainable Route Candidate
        ↓
Canonical / StandardDataService
```

能力矩阵登记“项目希望接入什么”，插件注册表登记“当前有什么插件入口”，发现结果登记“真实环境实际具有什么能力”。

三个对象不得合并，否则容易把计划能力、宣传能力和真实授权能力混淆。

## 认证边界

认证对象只允许引用：

```text
none://
env://
keyring://
secret-manager://
interactive://
```

代码、配置、报告和Git历史不得出现密码、Token、API密钥、私钥或券商账户凭据。

## 发现结果

完整发现必须证明：

- SDK或客户端确实安装；
- Provider与插件身份一致；
- 能力状态已经验证；
- 限频和重试政策有证据；
- 批量和分页语义明确；
- 实时订阅模式明确；
- 许可证允许指定用途；
- 健康状态可用；
- 无未解决错误。

## 多来源路由

路由评分只在硬门禁通过后使用。硬门禁包括：

- 注册表显式启用；
- 插件入口存在；
- 能力发现完成；
- Provider生命周期已通过真实验收；
- 能力已实现或验证；
- 许可证允许本次用途；
- 健康状态可用；
- 实时与交易请求满足专属能力。

任何硬门禁失败时，得分归零，并返回可解释阻断原因。

## 当前种子注册表

Wind、iFinD、银河证券星耀数智、Choice、QMT、PTrade、Tushare Pro、AkShare等均已登记，但尚未实现插件，也没有任何路由被启用。

本地DolphinDB和本地文件已有旧接口基础，状态为：

```text
LEGACY_BRIDGE_REQUIRED
```

## 下一阶段

TASK_020C优先桥接本地DolphinDB，因为它已具备真实数据、Provider和就绪度验收，可在不增加商业授权成本的情况下验证整个插件协议。
