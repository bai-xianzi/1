# 脚本总览：`scripts/verify_task_016a_patch.ps1` 负责执行项目验证、交付或运维流程。
# - 输入：命令参数、项目路径、环境变量和前序任务产物。
# - 处理：保持原PowerShell命令和顺序，仅补充教学式说明。
# - 输出：控制台结果、报告文件、退出码或显式异常。
# - 为什么这样写：明确脚本边界和失败门禁，降低误执行及文件覆盖风险。
[CmdletBinding()]
param(
    [string]$ProjectRoot = "D:\QuantProjects\a_stock_quant_os",
    [string]$PythonExe = "D:\computer\python\python.exe"
)

$ErrorActionPreference = "Stop"
Set-Location $ProjectRoot

$env:PYTHONPATH = (Resolve-Path ".\src").Path

& $PythonExe `
  ".\scripts\run_task_016a_daily_funds_preflight.py" `
  --validate-contract-only

& $PythonExe `
  -m unittest `
  tests.test_daily_funds_ingest `
  -v

& $PythonExe `
  ".\scripts\audit_git_encoding.py"

git diff --check

Write-Host "TASK_016A patch verification PASSED."
