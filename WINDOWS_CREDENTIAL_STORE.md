# WINDOWS_CREDENTIAL_STORE.md

# WJX Windows 凭据引用安全后端权威合同

> 本文件定义 Provider、Skill、搜索、模型和其他外部服务秘密在 Windows 用户端的安全保存、引用、运行时解析、撤销和白箱状态规则。
> 核心原则：秘密值可以由用户在 B2C 界面输入，但只能在同一次后端请求的内存中短暂存在；项目配置、日志、报告、数据库、Git 和普通 UI 响应只能保存或展示安全引用。

## 1. 复用决策

本项目不自研加密算法和秘密文件格式。Windows 个人用户环境默认复用微软官方 Credential Manager：

```text
B2C秘密输入
→ TASK_024C submit_connection_form
→ WindowsCredentialStore薄适配器
→ CredWriteW / CredReadW / CredDeleteW / CredFree
→ 当前Windows用户的Credential Manager
```

实现使用 `CRED_TYPE_GENERIC` 保存应用定义秘密，使用 `CRED_PERSIST_LOCAL_MACHINE` 使同一Windows用户在本机后续登录会话可用，不启用企业漫游。

## 2. 引用格式

```text
windows-credential://WJX/provider/<provider_id>/<connection_id>/<field_id>
```

对应 Windows 目标名：

```text
WJX/provider/<provider_id>/<connection_id>/<field_id>
```

三个标识必须使用小写字母开头，只包含小写字母、数字和下划线。运行时只能解析 WJX 命名空间，不能读取或删除任意 Credential Manager 记录。

## 3. B2C 双视图

### 用户端

用户可以：

- 输入新秘密；
- 查看“已配置/未配置”；
- 替换秘密；
- 运行只读连接测试；
- 删除秘密和停用连接。

用户永远不能：

- 从页面读回秘密原文；
- 在浏览器、日志、配置或报告中看到完整秘密；
- 通过任意目标名读取系统其他凭据。

### 系统内部

```text
秘密字段writeOnly提交
→ 标识和长度校验
→ WJX1 + UTF-8应用Blob
→ CredWriteW
→ 返回windows-credential引用
→ 连接档案只保存引用
```

只读SDK运行时：

```text
连接档案引用
→ 解析WJX命名空间
→ CredReadW
→ 校验用户名标签和WJX1载荷
→ 秘密只进入本次SDK调用内存
```

## 4. 白箱与安全状态

普通 UI 状态对象只允许：

```json
{
  "backend": "WINDOWS_CREDENTIAL_MANAGER",
  "reference": "windows-credential://WJX/provider/...",
  "configured": true,
  "secret_value": null
}
```

代码查看器可以展示保存、解析、删除算法和前置教学注释，但不得展示真实秘密、CredentialBlob 或用户凭据列表。

## 5. 失败关闭

以下情况必须阻断：

- 非 Windows 环境请求默认生产后端；
- 非 WJX 引用或非法标识；
- 空秘密或超过微软 2560 字节 CredentialBlob 上限；
- Credential Manager 不可用或系统策略拒绝；
- 用户名标签与引用不一致；
- 未知或损坏的应用载荷格式；
- 删除失败。

禁止自动降级到明文 JSON、环境变量、Git 配置或自制加密文件。

## 6. 真实验收

TASK_024D 关闭前必须在用户 Windows 环境执行一次随机探针：

```text
TASK_024C表单提交
→ 写入Credential Manager
→ 连接档案无秘密
→ 按引用读取并比对
→ UI安全状态不回显
→ 删除
→ 确认不存在
```

探针不连接券商、不访问网络、不写 DolphinDB、不触发交易；报告只记录安全引用和布尔结果。
