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
