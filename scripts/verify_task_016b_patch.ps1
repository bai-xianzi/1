# 脚本总览：`scripts/verify_task_016b_patch.ps1` 负责执行项目验证、交付或运维流程。
# - 输入：命令参数、项目路径、环境变量和前序任务产物。
# - 处理：保持原PowerShell命令和顺序，仅补充教学式说明。
# - 输出：控制台结果、报告文件、退出码或显式异常。
# - 为什么这样写：明确脚本边界和失败门禁，降低误执行及文件覆盖风险。
$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

$python = "D:\computer\python\python.exe"
if (-not (Test-Path $python)) {
    $python = "python"
}

$env:PYTHONPATH = (Resolve-Path ".\src").Path

& $python `
  ".\scripts\run_task_016b_daily_funds_import.py" `
  --mode contract `
  --project-root $projectRoot `
  --output-dir `
  "D:\Users\Administrator\task_016b_contract_check"

if ($LASTEXITCODE -ne 0) {
    throw "TASK_016B contract validation failed."
}

& $python `
  -m unittest `
  tests.test_daily_funds_dolphindb_writer `
  -v

if ($LASTEXITCODE -ne 0) {
    throw "TASK_016B unit tests failed."
}

Write-Host "TASK_016B patch verification PASSED."
