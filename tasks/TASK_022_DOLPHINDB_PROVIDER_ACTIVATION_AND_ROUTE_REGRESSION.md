# TASK_022：DolphinDB Provider 正式激活与真实注册表路由回归

## 1. 背景

TASK_020C 已经证明 `DolphinDBProviderPluginBridge` 能够复用现有 `DolphinDBDataSourceAdapter` 完成健康检查、能力发现、有限只读查询和路由候选计算。但是 TASK_020C 为了保持安全，只在内存中覆盖注册表和能力矩阵，没有修改真实配置。

TASK_022 负责关闭这一缺口：把已经真实验收的 `local_dolphindb` 插件正式写入真实 Provider 注册表和能力矩阵，并从真实配置重新执行路由回归。

## 2. 目标

1. 将 `local_dolphindb` 的注册状态升级为 `AVAILABLE`；
2. 将插件入口切换为 `DolphinDBProviderPluginBridge`；
3. 将 `enabled_for_routing` 设置为 `true`；
4. 将能力矩阵生命周期升级为 `ACTIVATED`；
5. 将已真实验证的五项能力升级为 `VERIFIED`；
6. 从真实配置加载矩阵、注册表和协议；
7. 执行健康检查、能力发现和最多 5 行只读查询；
8. 使用真实注册表计算 `EOD_MARKET_DATA` 路由候选；
9. 确认 `local_dolphindb` 为唯一 `ELIGIBLE` 候选；
10. 生成 JSON 与 Markdown 验收报告。

## 3. 允许修改

- `configs/providers/provider_plugin_registry_v0.json`
- `configs/providers/provider_capability_matrix_v0.json`
- `src/a_stock_quant/dolphindb_provider_plugin.py` 中已经完成的注册表激活警告
- `tasks/TASK_022_DOLPHINDB_PROVIDER_ACTIVATION_AND_ROUTE_REGRESSION.md`
- `scripts/run_task_022_real_registry_route_acceptance.py`
- `scripts/validate_task_022_provider_activation.py`
- `scripts/verify_task_022_patch.ps1`
- `tests/test_task_022_provider_activation.py`
- `PROJECT_STATUS.md` 的 TASK_022 状态段
- TASK_022 验收生成的报告

## 4. 禁止修改

- DolphinDB 数据库、表和数据；
- Canonical 字段；
- StandardDataService；
- Readiness 门禁；
- 外部商业 Provider 状态；
- 交易执行能力；
- 认证秘密；
- TASK_020C 已有验收报告。

## 5. 配置变化

### 注册表

`local_dolphindb`：

- `plugin_id = builtin.local_dolphindb.plugin_bridge`
- `registration_status = AVAILABLE`
- `entrypoint = a_stock_quant.dolphindb_provider_plugin:DolphinDBProviderPluginBridge`
- `enabled_for_routing = true`
- `discovery_result_ref = reports/task_022_real_dolphindb_provider_activation.json`

全局 `automatic_activation_allowed` 仍为 `false`。本任务是经过明确验收的单一 Provider 人工激活，不允许其他 Provider 自动激活。

### 能力矩阵

`local_dolphindb`：

- `lifecycle = ACTIVATED`
- `discovery_status = DISCOVERY_COMPLETE`
- `EOD_MARKET_DATA = VERIFIED`
- `FUNDAMENTAL_DATA = VERIFIED`
- `CLASSIFICATION_DATA = VERIFIED`
- `MONEY_FLOW = VERIFIED`
- `AUCTION_DATA = VERIFIED`

## 6. 验收标准

- 配置强类型加载通过；
- 只有 `local_dolphindb` 启用路由；
- 插件入口可以导入；
- DolphinDB 健康检查不为 `UNAVAILABLE`；
- 能力发现结果为 `COMPLETE`；
- 有限只读查询返回 1 至 5 行；
- 真实路由候选为 `ELIGIBLE`；
- 路由得分大于 90；
- 数据库写操作为 0；
- 专项测试和全量测试通过；
- Git 工作区只包含 TASK_022 允许范围；
- 创建独立 Git 提交并推送到 GitHub `main`；
- `HEAD == origin/main`，工作区干净。

## 7. 合同身份字段保持规则

`provider_capability_matrix_v0.json` 和 `provider_plugin_registry_v0.json` 的 `task_id` 是创建该强类型合同的身份字段，不是“最近一次修改任务号”。因此 TASK_022 激活配置时必须保持：

- 能力矩阵：`task_id = TASK_020A`
- 插件注册表：`task_id = TASK_020B`

TASK_022 的变更由任务文件、状态、版本、报告和 Git 提交记录表达，不能覆盖上游合同身份字段。
