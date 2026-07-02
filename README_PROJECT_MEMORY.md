# README_PROJECT_MEMORY.md

# WJX 项目权威记忆使用规则

## 权威文件

1. `PROJECT_MEMORY.md`：长期目标、硬原则和稳定判断；
2. `SYSTEM_ARCHITECTURE.md`：用户端与内部系统双结构图、模块边界和依赖；
3. `B2C_INTERACTION_AND_WHITEBOX_ARCHITECTURE.md`：B2C控制平面、白箱解释、配置版本和回滚；
4. `SKILL_PLATFORM_ARCHITECTURE.md`：开发型与产品型Skill共同内核、权限和发布门禁；
5. `PROJECT_STATUS.md`：当前阶段、完成事项和下一步；
6. `DEVELOPMENT_GUIDANCE.md`：复用优先、双合同、沙盒验证和Git闭环；
7. `REUSE_FIRST_ENGINEERING_POLICY.md`：官方、开源、薄适配和最小自研批准；
8. `PROVIDER_CONNECTION_CENTER.md`：数据接入中心纵向样板；
9. `CODE_COMMENTING_STANDARD.md`：前置教学式注释和用户可见代码解释；
10. `schemas/`：字段、枚举、B2C、Skill、因子、仿真和场景机器合同。

## 冲突优先级

- 当前做到哪里：`PROJECT_STATUS.md`；
- 模块归属和双视图：`SYSTEM_ARCHITECTURE.md`；
- 用户交互与白箱：`B2C_INTERACTION_AND_WHITEBOX_ARCHITECTURE.md`；
- Skill：`SKILL_PLATFORM_ARCHITECTURE.md`；
- 字段和枚举：`schemas/`。

发现冲突必须先统一权威文件再继续开发。

## 强制同步

任何新增功能都必须检查是否同步影响：长期记忆、总体架构、B2C交互、Skill、字段字典、数据时点、白箱解释、测试和项目状态。

## 任务闭环

GitHub `main` 是权威远程仓库和任务交接区。每个小任务必须经过沙盒验证、本地适用验证、独立提交、推送和远程一致性检查。ZIP只用于修改传递和恢复，不能替代GitHub闭环。
