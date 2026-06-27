$ErrorActionPreference = "Stop"

Set-Location (Resolve-Path (Join-Path $PSScriptRoot ".."))

$python = "D:\computer\python\python.exe"
if (-not (Test-Path -LiteralPath $python)) {
    $python = "python"
}

$env:PYTHONPATH = (Resolve-Path ".\src").Path

& $python `
  ".\scripts\validate_task_018a_data_readiness_contract.py" `
  --project-root (Get-Location).Path

if ($LASTEXITCODE -ne 0) {
    throw "TASK_018A合同验证失败。"
}

& $python `
  -m unittest `
  tests.test_data_readiness `
  -v

if ($LASTEXITCODE -ne 0) {
    throw "TASK_018A专项测试失败。"
}

Write-Host "TASK_018A verification PASSED."
