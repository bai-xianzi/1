$ErrorActionPreference = "Stop"

Set-Location (Resolve-Path (Join-Path $PSScriptRoot ".."))

$python = "D:\computer\python\python.exe"
if (-not (Test-Path -LiteralPath $python)) {
    $python = "python"
}

$env:PYTHONPATH = (Resolve-Path ".\src").Path

& $python `
  ".\scripts\validate_task_018d_readiness_gate.py" `
  --project-root (Get-Location).Path

if ($LASTEXITCODE -ne 0) {
    throw "TASK_018D离线合同验证失败。"
}

& $python `
  -m unittest `
  tests.test_readiness_gated_data_service `
  -v

if ($LASTEXITCODE -ne 0) {
    throw "TASK_018D专项测试失败。"
}

Write-Host "TASK_018D offline verification PASSED."
