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
