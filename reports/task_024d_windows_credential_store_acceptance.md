# TASK_024D Windows 凭据引用安全后端验收报告

## 沙盒结论

```text
状态：SANDBOX_PASSED_WINDOWS_REAL_ACCEPTANCE_REQUIRED
跨平台专项测试：12项通过
TASK_024D合同验证：通过
强制真实报告验证器（安全测试夹具）：通过
Python编译：通过
应用器备份、复制、幂等补丁和恢复：通过
接入中心提交到凭据后端的注入式端到端流程：通过
PowerShell启动器ASCII检查：通过
真实Windows Credential Manager：待用户本地应用脚本执行
数据库写操作：0
网络请求：0
交易动作：0
```

## 实现说明

- 复用微软官方 `CredWriteW`、`CredReadW`、`CredDeleteW` 和 `CredFree`；
- 使用 `CRED_TYPE_GENERIC` 和本机持久化；
- 项目只保存 `windows-credential://WJX/provider/...` 引用；
- B2C状态只显示是否配置，不返回秘密；
- 单元测试通过可注入假 WinCred API 在 Linux 沙盒验证；
- Windows 本地脚本使用一次性随机秘密完成真实写入、读取和删除；
- 应用和复验PowerShell均为纯ASCII极小启动器，复杂逻辑由UTF-8 Python执行。

## 沙盒限制

Linux沙盒不能加载Windows `Advapi32.dll`，因此不能把假后端测试冒充真实Credential Manager验收。正式应用器会在用户Windows环境中强制执行随机探针，探针失败时恢复文件且不创建Git提交。

## 正式关闭条件

只有 `reports/task_024d_windows_credential_store_real_acceptance.json` 显示全部布尔门禁通过，且全量测试、教学式注释审计、UTF-8审计、Git提交、GitHub推送和健康工作区全部完成后，TASK_024D 才算关闭。
