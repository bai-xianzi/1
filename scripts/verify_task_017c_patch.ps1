$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

$python = "D:\computer\python\python.exe"
if (-not (Test-Path $python)) {
    $python = "python"
}

$env:PYTHONPATH = (Resolve-Path ".\src").Path

& $python `
  ".\scripts\validate_task_017c_daily_funds_service.py" `
  --project-root $projectRoot

if ($LASTEXITCODE -ne 0) {
    throw "TASK_017C service contract validation failed."
}

& $python `
  -m unittest `
  tests.test_dolphindb_daily_funds_service `
  -v

if ($LASTEXITCODE -ne 0) {
    throw "TASK_017C dedicated tests failed."
}

Write-Host "TASK_017C patch verification PASSED."
