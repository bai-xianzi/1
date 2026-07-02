# TASK_023：外部Provider环境发现与首个接入候选选择

## 1. 背景

TASK_022 已经正式激活本地 DolphinDB Provider，并证明真实注册表、能力矩阵、插件协议和只读路由可以闭环。项目下一步不能直接为某一家商业供应商编写专用接口，而应先建立供应商无关的环境发现和候选选择门禁。

## 2. 当前架构位置

```text
P0 复用优先与自研批准门禁
→ 1. 多源金融与现实数据接入层
   → 通用Provider协议：已完成
   → 本地DolphinDB真实Provider：TASK_022已激活
   → 外部Provider环境发现：TASK_023（当前位置）
→ 2. DolphinDB数据底座与数据验收层
→ 3. 时间、公司行为与可见性处理层
→ 4. Canonical标准数据与Readiness门禁
```

TASK_023 位于第1层和第2层的交界：它决定下一项真实外部来源接入任务选择谁，但不改变DolphinDB现有事实源，也不绕过Canonical和Readiness。

## 3. 分阶段

### TASK_023A：供应商无关的离线环境发现合同

- 建立外部Provider发现清单；
- 只检查模块入口和凭据引用名称是否存在；
- 不导入供应商SDK；
- 不登录、不联网、不读取秘密值；
- 排除交易执行Provider自动推荐；
- 生成候选顺序，但不激活任何Provider。

### TASK_023B：用户Windows真实环境盘点

- 在用户本地项目虚拟环境中运行发现脚本；
- 生成真实环境报告；
- 核对已安装客户端、Python版本和许可证资料；
- 不把密码、Token或账户写入报告或Git。

### TASK_023C：首个外部Provider选择与接入任务书

- 根据真实运行时、用户授权、许可证、覆盖、成本和维护性选择首个Provider；
- 优先复用官方SDK或成熟开源组件；
- 明确薄适配范围；
- 未通过审查时不得开始专用插件编码。

## 4. TASK_023A允许修改

- `configs/providers/provider_discovery_targets_v0.json`
- `src/a_stock_quant/provider_environment_discovery.py`
- `scripts/run_task_023_provider_environment_discovery.py`
- `tests/test_provider_environment_discovery.py`
- `tasks/TASK_023_EXTERNAL_PROVIDER_DISCOVERY_AND_SELECTION.md`
- `reports/task_023a_reuse_assessment.md`
- `reports/task_023a_sandbox_validation.json`
- `SYSTEM_ARCHITECTURE.md`
- `MULTI_SOURCE_ADAPTER_ARCHITECTURE.md`
- `PROJECT_STATUS.md`

## 5. 禁止修改

- TASK_022已经验收的注册表和能力矩阵；
- DolphinDB数据库、表和数据；
- Canonical字段；
- StandardDataService和Readiness门禁；
- 任何商业SDK安装状态；
- 账号、密码、Token、密钥和券商账户；
- 交易执行能力和自动交易状态。

## 6. TASK_023A验收标准

- 清单只包含可核实的模块候选；
- 未核实供应商保持人工审查；
- 扫描器不导入供应商SDK；
- 网络调用为0；
- 数据库写操作为0；
- 秘密值记录为0；
- 交易执行Provider不会被自动推荐；
- 测试、语法检查和JSON解析通过；
- 架构图明确标出TASK_023当前位置；
- 创建独立Git提交并推送GitHub `main`。
