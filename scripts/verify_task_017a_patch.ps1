$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

$python = "D:\computer\python\python.exe"
if (-not (Test-Path $python)) {
    $python = "python"
}

$env:PYTHONPATH = (Resolve-Path ".\src").Path

& $python `
  ".\scripts\validate_task_017a_daily_funds_canonical_contract.py" `
  --project-root $projectRoot

if ($LASTEXITCODE -ne 0) {
    throw "TASK_017A contract validation failed."
}

& $python `
  -m unittest `
  tests.test_daily_funds_canonical_contract `
  -v

if ($LASTEXITCODE -ne 0) {
    throw "TASK_017A unit tests failed."
}

Write-Host "TASK_017A verification PASSED."
