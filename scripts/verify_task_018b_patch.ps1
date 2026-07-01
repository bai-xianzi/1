# 脚本总览：`scripts/verify_task_018b_patch.ps1` 负责执行项目验证、交付或运维流程。
# - 输入：命令参数、项目路径、环境变量和前序任务产物。
# - 处理：保持原PowerShell命令和顺序，仅补充教学式说明。
# - 输出：控制台结果、报告文件、退出码或显式异常。
# - 为什么这样写：明确脚本边界和失败门禁，降低误执行及文件覆盖风险。
$ErrorActionPreference = "Stop"

Set-Location (Resolve-Path (Join-Path $PSScriptRoot ".."))
$python = "D:\computer\python\python.exe"
if (-not (Test-Path -LiteralPath $python)) { $python = "python" }
$env:PYTHONPATH = (Resolve-Path ".\src").Path
& $python ".\scripts\validate_task_018b_data_readiness_evidence.py" --project-root (Get-Location).Path
if ($LASTEXITCODE -ne 0) { throw "TASK_018B合同验证失败。" }
& $python -m unittest tests.test_data_readiness_evidence -v
if ($LASTEXITCODE -ne 0) { throw "TASK_018B专项测试失败。" }
Write-Host "TASK_018B verification PASSED."
