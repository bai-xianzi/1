$ErrorActionPreference = "Stop"

Set-Location (Resolve-Path (Join-Path $PSScriptRoot ".."))

$python = "D:\computer\python\python.exe"
if (-not (Test-Path -LiteralPath $python)) {
    $python = "python"
}

$env:PYTHONPATH = (Resolve-Path ".\src").Path

$validatorArgs = @(
    ".\scripts\validate_task_018c_external_evidence.py",
    "--project-root",
    (Get-Location).Path
)
& $python @validatorArgs
if ($LASTEXITCODE -ne 0) {
    throw "TASK_018C外部证据验证失败。"
}

$testArgs = @(
    "-m",
    "unittest",
    "tests.test_data_readiness_external_evidence",
    "-v"
)
& $python @testArgs
if ($LASTEXITCODE -ne 0) {
    throw "TASK_018C专项测试失败。"
}

Write-Host "TASK_018C verification PASSED."
