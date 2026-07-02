# TASK_024E：数据接口接入中心页面与后端接口

## 这个功能是干什么的

让用户在本机页面中选择 Wind、iFinD、券商SDK等数据源，填写官方连接字段、安全保存密钥、查看状态并发起只读测试，而不再手工修改配置文件。

## 本任务范围

- 本地B2C Provider卡片页面；
- JSON Schema动态表单；
- Windows Credential Manager与无秘密档案的事务式组合；
- 本机回环限制、CSRF、请求大小、no-store和安全响应头；
- Provider只读测试器端口和状态机；
- 停用时凭据与档案的可恢复删除；
- 纯标准库本地启动器。

## 不在本任务范围

- 不调用真实Wind、iFinD或券商SDK；
- 不发送网络请求；
- 不开通下单、撤单、资金或交易权限；
- 不把某一家Provider字段写死在页面中；
- 不引入新的Web框架。

## 下一任务

TASK_024F选择用户已经正式授权的首个Provider，实现一个最小只读连接测试器，并通过本任务的`ProviderReadOnlyConnectionTester`端口注册。

## Git提交

```text
feat: add provider connection center b2c app
```
