# TASK_024C：官方数据源与券商接入中心领域模型及UI合同

状态：IMPLEMENTED_PENDING_WINDOWS_CREDENTIAL_BACKEND

## 一、目标

把TASK_024B后台机器盘点能力纳入面向最终用户的可视化接入流程，建立Provider卡片、动态表单、凭据引用、连接状态机和安全ViewModel。

本任务不选择桌面或Web前端框架，不实现真实Windows秘密存储，不联网、不导入券商SDK、不登录和不连接交易域。

## 二、核心决策

- TASK_024B保留为后台SDK环境发现器；
- UI动态表单必须来自Provider官方文档映射；
- 未核验字段时显示`OFFICIAL_FIELD_SPEC_REQUIRED`，不展示猜测的密钥框；
- 秘密字段只允许`credential_reference`持久化；
- 领域层通过`CredentialReferenceWriter`端口交换秘密与引用；
- ViewModel、档案、报告和日志不含秘密原文；
- 普通接入流程永久阻断交易激活。

## 三、交付

- `PROVIDER_CONNECTION_CENTER.md`；
- `configs/providers/provider_connection_center_catalog_v1.json`；
- `schemas/provider_connection_profile_v1.schema.json`；
- `src/a_stock_quant/provider_connection_center.py`；
- `scripts/run_task_024c_provider_connection_center.py`；
- `tests/test_provider_connection_center.py`；
- 架构、状态、多源适配和TASK_024B定位更新；
- 项目记忆、开发指导、启动入口和权威索引幂等补丁。

## 四、下一任务

`TASK_024D_WINDOWS_CREDENTIAL_REFERENCE_BACKEND`

优先复用成熟操作系统密钥库能力，不自行设计密码学或密码库。
