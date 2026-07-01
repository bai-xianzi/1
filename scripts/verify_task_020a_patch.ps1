# 脚本总览：`scripts/verify_task_020a_patch.ps1` 负责执行项目验证、交付或运维流程。
# - 输入：命令参数、项目路径、环境变量和前序任务产物。
# - 处理：保持原PowerShell命令和顺序，仅补充教学式说明。
# - 输出：控制台结果、报告文件、退出码或显式异常。
# - 为什么这样写：明确脚本边界和失败门禁，降低误执行及文件覆盖风险。
param(
    [string]$ProjectRoot = "D:\QuantProjects\a_stock_quant_os",
    [string]$Python = "D:\computer\python\python.exe"
)

$ErrorActionPreference = "Stop"
Set-Location $ProjectRoot
$env:PYTHONPATH = (Resolve-Path ".\src").Path

& $Python `
  ".\scripts\validate_task_020a_universal_adapter_contract.py" `
  --project-root $ProjectRoot
if ($LASTEXITCODE -ne 0) {
    throw "TASK_020A合同验证失败。"
}

& $Python -m unittest tests.test_provider_capabilities -v
if ($LASTEXITCODE -ne 0) {
    throw "TASK_020A专项测试失败。"
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
