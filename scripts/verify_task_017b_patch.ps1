$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

$python = "D:\computer\python\python.exe"
if (-not (Test-Path $python)) {
    $python = "python"
}

$env:PYTHONPATH = (Resolve-Path ".\src").Path

& $python `
  ".\scripts\validate_task_017b_dictionary_upgrade.py" `
  --project-root $projectRoot

if ($LASTEXITCODE -ne 0) {
    throw "TASK_017B dictionary validation failed."
}

& $python `
  -m unittest `
  tests.test_field_dictionary_governance `
  tests.test_daily_funds_canonical_contract `
  tests.test_task_017b_dictionary_upgrade `
  -v

if ($LASTEXITCODE -ne 0) {
    throw "TASK_017B tests failed."
}

Write-Host "TASK_017B verification PASSED."
