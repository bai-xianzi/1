# TASK_023：外部Provider环境发现与首个接入候选选择

> **TASK_024A纠正说明：** 本任务原先把AKShare列为首个只读试点候选。该结论已被官方交易所语义基准与券商优先原则替代。当前有效入口见 `TASK_024_OFFICIAL_EXCHANGE_AND_BROKER_INTERFACE_BASELINE.md`。

## 1. 背景

TASK_022 已经正式激活本地 DolphinDB Provider，并证明真实注册表、能力矩阵、插件协议和只读路由可以闭环。项目下一步不能直接为某一家商业供应商编写专用接口，而应先建立供应商无关的环境发现和候选选择门禁。

## 2. 当前架构位置

```text
P0 复用优先与自研批准门禁
→ 1. 多源金融与现实数据接入层
   → 通用Provider协议：已完成
   → 本地DolphinDB真实Provider：TASK_022已激活
   → 外部Provider环境发现：TASK_023A（已完成）
   → Windows机器级环境盘点：TASK_023B（已完成）
   → 首个外部Provider选择：TASK_023C（已完成）
   → 官方交易所与券商接口基线：TASK_024A（已完成）
   → 用户已授权券商SDK包与只读行情盘点：TASK_024B（当前位置）
→ 2. DolphinDB数据底座与数据验收层
→ 3. 时间、公司行为与可见性处理层
→ 4. Canonical标准数据与Readiness门禁
```

TASK_023 位于第1层和第2层的交界：它决定下一项真实外部来源接入任务选择谁，但不改变DolphinDB现有事实源，也不绕过Canonical和Readiness。

## 3. 分阶段

### TASK_023A：供应商无关的离线环境发现合同（已完成）

- 建立外部Provider发现清单；
- 只检查模块入口和凭据引用名称是否存在；
- 不导入供应商SDK；
- 不登录、不联网、不读取秘密值；
- 排除交易执行Provider自动推荐；
- 生成候选顺序，但不激活任何Provider。

### TASK_023B：用户Windows真实环境盘点（已完成）

- 在用户本地项目虚拟环境中运行发现脚本；
- 生成真实环境报告；
- 核对已安装客户端、Python版本和许可证资料；
- 不把密码、Token或账户写入报告或Git。

### TASK_023C：首个外部Provider选择与接入任务书（已完成）

- 使用TASK_023B报告和供应商无关选择政策形成确定性决策；
- 排除交易执行Provider自动选择；
- 本地客户端或模块只作为存在性证据，不等于许可证和授权；
- 原AKShare优先选择已经被TASK_024A纠正；
- 形成TASK_024A运行前审查任务书；
- 不安装、不导入、不联网、不激活任何外部Provider。

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


## 7. TASK_023B允许修改

- `configs/providers/provider_windows_inventory_rules_v0.json`
- `src/a_stock_quant/provider_windows_inventory.py`
- `scripts/run_task_023b_windows_provider_inventory.py`
- `tests/test_provider_windows_inventory.py`
- `reports/task_023b_reuse_assessment.md`
- `reports/task_023b_sandbox_validation.json`
- 本任务文件、`SYSTEM_ARCHITECTURE.md`、`MULTI_SOURCE_ADAPTER_ARCHITECTURE.md`、`PROJECT_STATUS.md`

## 8. TASK_023B设计约束

- 复用Python标准库的`importlib.util.find_spec`、`subprocess`、`winreg`和Windows卸载注册表，不自行实现包管理器或客户端管理器；
- 只发现当前解释器、PATH、虚拟环境和`py -0p`明确列出的Python，不进行全盘扫描；
- 注册表只读取程序名称、版本和发布者，不读取或记录安装路径；
- 环境变量只记录配置中的引用名称是否存在，不记录值；
- 供应商SDK仅做模块入口探测，绝不执行`import`；
- 本地真实报告保存在修改包的`local_validation`目录，不自动进入Git。

## 9. TASK_023B验收标准

- 能发现多个Python解释器并分别探测模块入口；
- 能读取Windows已安装程序安全元数据并匹配Provider提示；
- 当前解释器、其他解释器、客户端和凭据引用证据分层记录；
- 交易执行Provider不进入TASK_023C自动候选；
- 报告不含秘密值、安装路径或账户信息；
- SDK导入、网络调用、注册表写入和数据库写入均为0；
- 专项测试、全量离线测试、JSON解析和`git diff --check`通过；
- 架构图明确标出TASK_023B当前位置；
- 创建独立Git提交并推送GitHub `main`。

## 10. TASK_023C允许修改

- `configs/providers/provider_selection_policy_v0.json`
- `configs/providers/provider_selection_approvals_v0.example.json`
- `src/a_stock_quant/provider_selection.py`
- `scripts/run_task_023c_provider_selection.py`
- `tests/test_provider_selection.py`
- `tasks/TASK_024_AKSHARE_READ_ONLY_PROVIDER_PILOT.md`
- `reports/task_023c_reuse_assessment.md`
- `reports/task_023c_sandbox_validation.json`
- 本任务文件、`SYSTEM_ARCHITECTURE.md`、`MULTI_SOURCE_ADAPTER_ARCHITECTURE.md`、`PROJECT_STATUS.md`

## 11. TASK_023C选择结论（经TASK_024A纠正）

```text
语义基准：official_exchange_sources
优先实际接入：用户已授权的券商官方SDK
AKShare/Tushare：SUPPLEMENTAL_ONLY
激活状态：NOT_ACTIVATED
下一任务：TASK_024A官方交易所与券商接口基线
```

此前AKShare优先结论已作废。官方交易所、监管与结算机构负责定义市场语义；券商官方SDK在用户授权后作为个人项目首选运行通道；商业数据厂商必须有有效许可证；第三方聚合源不能成为主事实源。

## 12. TASK_023C验收标准

- 能安全读取TASK_023B报告并拒绝非零安全计数；
- 交易执行Provider不会被选择；
- 本机商业客户端存在不被误判为使用授权；
- 无本地官方运行时证据时，选择官方交易所资料作为语义基准，并把实际接入通道保持为待授权；
- 输出明确标记`NOT_ACTIVATED`；
- SDK导入、网络调用、数据库写入、注册表写入和秘密值记录均为0；
- 生成TASK_024A官方交易所与券商接口基线任务书；
- 专项测试、TASK_023A/023B回归、全量离线测试和`git diff --check`通过；
- 创建独立Git提交并推送GitHub `main`。
