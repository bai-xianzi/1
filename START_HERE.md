# START_HERE.md

# 新对话和新任务启动入口

## 1. 先读取权威文件

```text
PROJECT_STATUS.md
PROJECT_MEMORY.md
SYSTEM_ARCHITECTURE.md
B2C_INTERACTION_AND_WHITEBOX_ARCHITECTURE.md
SKILL_PLATFORM_ARCHITECTURE.md
DEVELOPMENT_GUIDANCE.md
REUSE_FIRST_ENGINEERING_POLICY.md
CODE_COMMENTING_STANDARD.md
```

## 2. 重建工作状态

```text
GitHub权威仓库：https://github.com/bai-xianzi/1
分支：main
用户本地项目：D:\QuantProjects\a_stock_quant_os
默认下载位置：D:\Users\Administrator
```

从GitHub最新 `main` 建立沙盒工作副本。改动少时提供精确PowerShell修改代码；改动多时提供可解压修改包。所有新增或修改代码必须先完成前置教学注释，再在沙盒运行。

## 3. 新功能设计顺序

```text
调查项目已有能力、官方方案和成熟开源
→ 决定复用、薄适配或最小自研
→ 同时设计后台领域合同与B2C交互合同
→ 定义Schema、Skill关系、ExplanationTrace和治理门禁
→ 编码和测试
→ 本地真实验收
→ Git提交并推送GitHub main
```

## 4. 双结构图要求

每个功能必须说明：

- 用户在界面看什么、填什么、选什么、如何预览、执行、解释和回滚；
- 内部调用哪些Provider、Canonical、ASEI、CWMS、因子、回测、风险或组合模块；
- 两侧通过什么Action Contract、Schema、Skill和解释链连接。

## 5. 完成标准

仅修改本地、仅生成ZIP或仅创建未推送commit均不算完成。阶段终点是测试通过、权威文件同步、提交准确、推送GitHub `main`、HEAD与远程一致且工作区健康。
