\
$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

$python = "D:\computer\python\python.exe"
if (-not (Test-Path $python)) {
    $python = "python"
}

$env:PYTHONPATH = (Resolve-Path ".\src").Path

& $python `
  ".\scripts\validate_task_017d_standard_provider_registry.py" `
  --project-root $projectRoot

if ($LASTEXITCODE -ne 0) {
    throw "TASK_017D provider registry validation failed."
}

& $python `
  -m unittest `
  tests.test_daily_funds_standard_provider `
  -v

if ($LASTEXITCODE -ne 0) {
    throw "TASK_017D unit tests failed."
}

Write-Host "TASK_017D patch verification PASSED."
