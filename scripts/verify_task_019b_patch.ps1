param(
    [string]$ProjectRoot = "D:\QuantProjects\a_stock_quant_os",
    [string]$Python = "D:\computer\python\python.exe"
)

$ErrorActionPreference = "Stop"
Set-Location $ProjectRoot
$env:PYTHONPATH = (Resolve-Path ".\src").Path

& $Python `
  ".\scripts\validate_task_019b_market_state_features.py" `
  --project-root $ProjectRoot
if ($LASTEXITCODE -ne 0) {
    throw "TASK_019B合同验证失败。"
}

& $Python -m unittest tests.test_market_state_features -v
if ($LASTEXITCODE -ne 0) {
    throw "TASK_019B专项测试失败。"
}

& $Python -m unittest discover -s tests -p "test_*.py" -v
if ($LASTEXITCODE -ne 0) {
    throw "完整测试失败。"
}

$auditScript = @(
    ".\scripts\audit_git_encoding.py",
    ".\scripts\audit_text_encoding.py"
) | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1

if ($null -eq $auditScript) {
    throw "没有找到编码审计脚本。"
}

& $Python $auditScript
if ($LASTEXITCODE -ne 0) {
    throw "编码审计失败。"
}

git diff --check
if ($LASTEXITCODE -ne 0) {
    throw "Git空白检查失败。"
}

git status --short
