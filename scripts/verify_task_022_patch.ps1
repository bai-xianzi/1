# TASK_022 Windows validation entry point.
# This file intentionally uses ASCII-only text so Windows PowerShell 5.1
# cannot misread UTF-8 source text as the active ANSI code page.
[CmdletBinding()]
param(
    [string]$ProjectRoot = "D:\QuantProjects\a_stock_quant_os"
)

$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $ProjectRoot

if (-not (Test-Path -LiteralPath ".git")) {
    throw "Not a Git repository: $ProjectRoot"
}

$python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $python)) {
    $python = (Get-Command python -ErrorAction Stop).Source
}

$env:PYTHONPATH = Join-Path $ProjectRoot "src"

Write-Host "========== TASK_022 OFFLINE CONTRACT =========="
& $python "scripts\validate_task_022_provider_activation.py" --project-root $ProjectRoot
if ($LASTEXITCODE -ne 0) {
    throw "TASK_022 offline contract validation failed."
}

Write-Host "========== TASK_022 FOCUSED TESTS =========="
& $python -m unittest `
    tests.test_task_022_provider_activation `
    tests.test_provider_capabilities `
    tests.test_provider_plugin_protocol `
    tests.test_dolphindb_provider_plugin
if ($LASTEXITCODE -ne 0) {
    throw "TASK_022 focused unit tests failed."
}

Write-Host "========== FULL UNIT TEST SUITE =========="
& $python -m unittest discover -s tests -p "test_*.py"
if ($LASTEXITCODE -ne 0) {
    throw "Full unit test suite failed."
}

if (-not $env:DOLPHINDB_PASSWORD) {
    $secure = Read-Host "Enter DolphinDB password (not written to disk)" -AsSecureString
    $ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    try {
        $env:DOLPHINDB_PASSWORD = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr)
    }
    finally {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr)
    }
}

Write-Host "========== REAL READ-ONLY ROUTE ACCEPTANCE =========="
& $python `
    "scripts\run_task_022_real_registry_route_acceptance.py" `
    --project-root $ProjectRoot `
    --output-dir reports `
    --limit 5
if ($LASTEXITCODE -ne 0) {
    throw "TASK_022 real read-only registry route acceptance failed."
}

Write-Host "========== ENCODING AUDIT =========="
& $python "scripts\audit_git_encoding.py"
if ($LASTEXITCODE -ne 0) {
    throw "Encoding audit failed."
}

Write-Host "========== TEACHING COMMENT AUDIT =========="
& $python `
    "scripts\audit_teaching_comments.py" `
    --project-root $ProjectRoot `
    --output "$ProjectRoot\reports\task_022_teaching_comment_audit.json" `
    --mode enforce
if ($LASTEXITCODE -ne 0) {
    throw "Teaching comment audit failed."
}

Write-Host "========== GIT DIFF CHECK =========="
git diff --check
if ($LASTEXITCODE -ne 0) {
    throw "git diff --check failed."
}

Write-Host ""
Write-Host "TASK_022 VALIDATION PASSED" -ForegroundColor Green
Write-Host "Review git diff, then run complete_task_022.ps1 from the hotfix package."
