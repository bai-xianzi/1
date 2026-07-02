# TASK_024D：Windows 凭据引用安全后端

## 任务目标

实现 TASK_024C `CredentialReferenceWriter` 的 Windows 正式后端，使用户在 B2C 接入中心输入的 API Key、Secret、Token 或密码立即进入 Windows Credential Manager，项目只保存安全引用。

## 复用结论

优先复用微软官方 WinCred API，通过 Python `ctypes` 建立薄适配器；不实现自制密码算法，不引入明文文件后端，不要求额外第三方运行依赖。

## 交付范围

- `src/a_stock_quant/windows_credential_store.py`；
- `tests/test_windows_credential_store.py`；
- Windows 真实验收脚本；
- 安全引用 JSON Schema；
- 权威合同、任务、报告和项目状态同步。

## 禁止范围

- 不读取、修改或提交用户真实券商秘密；
- 不连接任何券商或商业 SDK；
- 不访问网络；
- 不写 DolphinDB；
- 不激活交易能力；
- 不把秘密写入日志、报告、配置、数据库或 Git。

## 验收标准

```text
跨平台单元测试通过
全仓库测试通过
Python编译通过
教学式注释审计通过
Windows真实写入/读取/删除探针通过
报告无秘密材料
数据库写入0
网络请求0
交易动作0
独立Git提交并推送main
```

## 建议提交

```text
feat: add Windows credential reference backend
```
