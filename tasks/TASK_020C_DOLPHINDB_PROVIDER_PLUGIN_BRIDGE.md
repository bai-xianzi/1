# TASK_020C DolphinDB通用Provider插件薄桥接

## 目标

把现有`DolphinDBDataSourceAdapter`包装为TASK_020B通用Provider插件，但不重写其核心能力。

## 复用内容

```text
DolphinDBDataSourceAdapter
├─ 延迟建立会话
├─ 健康检查
├─ read_raw
├─ run_readonly_query
├─ 只读脚本安全检查
└─ 返回值标准化
```

TASK_020C只增加：

```text
ProviderPlugin描述
SDK运行时发现
认证引用检查
能力发现结果
批次请求编排
不支持订阅的显式合同
路由候选验收覆盖
```

## 安全边界

- 密码只通过`env://DOLPHINDB_PASSWORD`引用；
- 不把密码写入配置、日志或验收报告；
- 真实验收只读取最多5行默认样本；
- 不执行写入；
- 不修改真实能力矩阵和插件注册表；
- 验收通过后再单独执行激活任务。

## 真实验收

默认读取：

```text
dfs://A_STOCK_DAILY_K_DB
stock_daily_k
limit = 5
```

如本地真实库表名不同，可以通过命令行参数覆盖。

## 下一步

TASK_020D核验真实验收报告，然后把本地DolphinDB从`LEGACY_BRIDGE_REQUIRED`升级为已验收插件，并执行实际注册表路由回归。

<!-- TASK_020C_REAL_ACCEPTANCE -->

## 真实验收结果

```text
状态：PASSED_WITH_WARNINGS
数据库：dfs://A_STOCK_DAILY_K_DB
表：stock_daily_k
真实读取：5行
健康状态：HEALTHY
能力发现：COMPLETE
路由决策：ELIGIBLE
路由得分：99.0
数据库写操作：0
issues：[]
```

真实注册表和能力矩阵尚未修改，正式激活由TASK_020D执行。
