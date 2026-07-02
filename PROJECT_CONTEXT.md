# PROJECT_CONTEXT.md

# WJX 项目接续上下文

## 一、项目定位

WJX 是面向个人长期使用并逐步扩展到 B2C 的 A 股统计证据研究、因果仿真与金融决策操作系统。项目以 Skill 为可组合能力单元，以 Canonical、Readiness、Point-in-Time、ASEI、CWMS、因子实验、风险和组合为内部可信底座。

## 二、双视图设计

```text
用户端操作视图
选择 / 配置 / 预览 / 运行 / 观察 / 解释 / 审批 / 复制 / 回滚
                         ⇅
B2CActionContract / Schema / Skill / ExplanationTrace
                         ⇅
系统内部执行视图
Provider / Canonical / ASEI / CWMS / 因子 / 回测 / 风险 / 组合
```

B2C 不是后期附加前端。每个模块从现在开始必须同时设计后台领域合同和用户交互合同。

## 三、核心权威文件

- `PROJECT_MEMORY.md`：长期目标与硬原则；
- `SYSTEM_ARCHITECTURE.md`：双视图总体结构和模块边界；
- `B2C_INTERACTION_AND_WHITEBOX_ARCHITECTURE.md`：全系统用户控制平面和白箱解释；
- `SKILL_PLATFORM_ARCHITECTURE.md`：开发型与产品型 Skill 平台；
- `DEVELOPMENT_GUIDANCE.md`：开发和验收方法；
- `PROJECT_STATUS.md`：当前任务与下一步；
- `REUSE_FIRST_ENGINEERING_POLICY.md`：复用优先和自研批准；
- `schemas/`：机器可读合同。

## 四、仓库和环境

```text
GitHub权威远程仓库：https://github.com/bai-xianzi/1
正式分支：main
用户本地项目：D:\QuantProjects\a_stock_quant_os
默认下载位置：D:\Users\Administrator
```

每个小任务先在虚拟沙盒基于最新 `main` 运行带前置教学注释的代码和测试，再在用户Windows、PowerShell、DolphinDB或官方SDK环境复验。任务以独立Git提交、推送GitHub `main`、远程一致和本地健康工作区为终点。

## 五、当前接续规则

新对话先读取 `PROJECT_STATUS.md` 判断当前小任务，不得用本文件中的长期背景覆盖最新状态。所有新功能先经过开源和官方方案调查，再决定直接复用、薄适配或最小自研。
