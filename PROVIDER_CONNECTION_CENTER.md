# PROVIDER_CONNECTION_CENTER.md

# 官方数据源与券商接入中心权威设计

> 本文件是项目面向最终用户配置官方交易所数据服务、券商SDK和商业数据接口的权威产品与安全合同。
> 任何UI、后端API、凭据存储、Provider插件和连接测试都必须服从本文件。
> 本接入中心是 `B2C_INTERACTION_AND_WHITEBOX_ARCHITECTURE.md` 的第一个纵向样板。其卡片、动态表单、状态机、预览、只读测试、安全ViewModel、解释和审计模式必须抽象为通用能力，供标准字典、因子实验、市场仿真和Skill中心复用。

## 一、产品定位

用户不应编辑Python、PowerShell或普通JSON来完成数据源接入。系统应提供可视化“数据源与券商接入中心”：

```text
选择官方Provider
→ 查看官方申请与授权要求
→ 在官方渠道取得SDK、证书或凭据
→ 回到系统动态表单填写或选择本地文件
→ 秘密立即写入操作系统安全存储
→ 项目只保存凭据引用
→ 运行最小只读连接测试
→ 字段、时间和市场语义审查
→ Readiness通过后用于研究
```

TASK_024B的机器级SDK盘点器保留为后台辅助能力，不再作为最终用户唯一入口。

## 二、来源与接入优先级

```text
语义与验收基准：
交易所、监管和结算机构官方资料
> 已授权券商官方接口
> 已授权商业数据厂商官方SDK
> 第三方聚合补充
> 未验证爬取（禁止）
```

```text
个人项目的实际接入通道：
用户已合法授权的券商官方SDK
> 合法可用的交易所官方文件或数据服务
> 用户已授权的商业数据SDK
> 第三方来源仅作补充研究
```

## 三、UI组成

接入中心至少包含：

1. Provider卡片：显示官方性质、环境状态、授权状态、只读能力和交易阻断；
2. 官方申请指引：指向经过核验的官方入口或本地官方文档；
3. 动态表单：字段只能来自对应Provider官方接口文档；
4. 本地SDK发现：复用TASK_023B和TASK_024B后台能力；
5. 凭据安全保存：UI不长期持有明文，后端只返回凭据引用；
6. 最小只读连接测试：只查询服务状态、权限和极小样例；
7. 语义审查：字段、单位、时区、交易日、市场状态和Point-in-Time；
8. 停用与删除：用户可撤销连接并删除安全存储中的凭据。

## 四、动态表单规则

动态表单采用JSON Schema 2020-12。项目扩展属性只用于控件和安全行为：

- `x-field-kind`：text、secret、file、directory、select或boolean；
- `x-persist-mode`：configuration、credential_reference或never；
- `writeOnly: true`：秘密字段；
- `x-sensitive: true`：禁止回显、日志和报告；
- `x-read-only-first: true`：首次连接只允许只读；
- `x-execution-activation: BLOCKED`：交易能力始终单独激活。

具体券商字段未从官方文档核验前，UI只能展示“需要官方字段规范”，不得显示猜测的万能API Key表单。

## 五、凭据安全边界

禁止：

- 将API Key、Secret、Token、密码或证书口令写入普通JSON、`.env`、数据库配置表或Git；
- 在日志、异常、报告和UI读取接口中回显完整秘密；
- 以“加掩码字符串”代替安全存储；
- 把凭据保存在前端LocalStorage、浏览器缓存或可导出的状态文件；
- 用本机发现结果推断用户已经获得授权。

允许保存：

```json
{
  "provider_id": "example_broker",
  "connection_id": "default_connection",
  "credential_references": {
    "api_key": "os-keyring://wjx/example_broker/default_connection/api_key"
  }
}
```

TASK_024C只定义`CredentialReferenceWriter`端口；TASK_024D优先评估Windows Credential Locker、DPAPI或成熟Python `keyring`薄适配，不自行发明密码库。

## 六、连接状态机

```text
NOT_CONFIGURED
→ OFFICIAL_APPLICATION_REQUIRED / OFFICIAL_FIELD_SPEC_REQUIRED / SDK_NOT_FOUND
→ CREDENTIALS_SAVED
→ READ_ONLY_TEST_PENDING
→ READ_ONLY_VERIFIED
→ SEMANTIC_REVIEW_REQUIRED
→ READY_FOR_RESEARCH
```

异常状态：

- `CONNECTION_TEST_FAILED`；
- `CREDENTIAL_EXPIRED`；
- `BLOCKED_FOR_TRADING`。

普通数据源配置流程不得产生“交易已激活”状态。

## 七、连接测试边界

允许：

- 检查SDK或客户端是否存在；
- 检查凭据引用是否完整；
- 建立只读会话；
- 查询服务状态和权限列表；
- 获取极小规模行情样例；
- 验证字段和时间语义；
- 立即断开连接。

禁止：

- 创建交易会话；
- 查询非必要账户资产；
- 发送或撤销委托；
- 修改账户配置；
- 批量下载；
- 高频调用接口。

## 八、官方来源接入说明

### official-exchange-access

交易所、监管和结算机构首先作为语义与验收基准。个人是否能够使用其直连或商业数据服务，必须依据官方资格、授权和接口文件单独确认。

### galaxy

银河星耀数智和TFast仅在用户取得官方授权材料后映射具体动态表单；行情和交易域必须隔离。

### xtp

XTP Quote/Level2和Trader能力必须分域。接入中心只允许先配置和验证只读行情域。

### iquant

iQuant字段、客户端版本和授权方式必须以用户当前客户端内置官方资料为准，不能仅依据历史公开手册猜测。

### gf

投易通的具体字段和SDK交付形式必须以用户官方授权包为准。

## 九、任务位置

```text
TASK_024B 后台SDK与授权证据盘点：完成，成为接入中心辅助能力
TASK_024C 接入中心领域模型与UI合同：完成
>>> TASK_024D Windows凭据引用安全后端：下一任务
TASK_024E 接入中心可视化页面与后端接口
TASK_024F 首个已授权券商只读连接测试
TASK_024G 首个券商薄适配器、Canonical映射与Readiness验收
```

<!-- TASK_024D_WINDOWS_CREDENTIAL_STORE_START -->
## TASK_024D Windows正式凭据后端

TASK_024C的`CredentialReferenceWriter`由`WindowsCredentialStore`正式实现。秘密字段通过同一次`submit_connection_form`调用写入当前Windows用户Credential Manager，连接档案只保存`windows-credential://WJX/provider/<provider>/<connection>/<field>`引用。

B2C只允许显示后端、引用和“已配置/未配置”；替换秘密覆盖同一目标，删除动作必须同时删除操作系统凭据。真实SDK连接只能在受控运行时按引用解析秘密，不得把原文返回页面、日志、报告、数据库或Git。详细合同见`WINDOWS_CREDENTIAL_STORE.md`。
<!-- TASK_024D_WINDOWS_CREDENTIAL_STORE_END -->
