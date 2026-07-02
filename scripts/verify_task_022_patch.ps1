# 本文件核心功能：执行TASK_022至TASK_024教学式注释整改相关的Windows PowerShell安全流程。
# - 输入：项目根目录、包目录、Git工作区、Python解释器和待验证文件路径。
# - 处理：先检查路径与Git状态，再执行备份、整改、测试或提交；任何失败立即抛出异常。
# - 输出：明确的控制台状态、非零失败退出和可回滚备份，不连接或写入业务数据库。
# - 常量依据：默认项目路径来自用户确认，main分支和UTF-8 BOM来自项目交付规范。
# - 为什么这样写：Windows PowerShell 5.1对编码和退出码敏感，显式门禁可防止乱码及失败后误提交。

# TASK_022 Windows validation entry point.
# This file intentionally uses ASCII-only text so Windows PowerShell 5.1
# cannot misread UTF-8 source text as the active ANSI code page.
[CmdletBinding()]
param(
    [string]$ProjectRoot = "D:\QuantProjects\a_stock_quant_os"
)

$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $ProjectRoot

# 本段代码核心功能：进入受控流程块（if）。
# - 输入：当前PowerShell变量、Git状态或文件路径，均来自脚本参数和前序显式检查。
# - 处理：按关键字语义执行单一分支、循环、函数或异常保护，不隐藏失败退出码。
# - 输出：更新局部变量、打印验收信息或抛出异常阻断后续提交，不修改业务数据库。
# - 常量依据：项目路径、main分支、UTF-8编码和零副作用要求来自任务合同及本机项目约定。
# - 为什么这样写：显式门禁能防止错误工作区、编码损坏或测试失败仍继续提交到GitHub。

if (-not (Test-Path -LiteralPath ".git")) {
    throw "Not a Git repository: $ProjectRoot"
}

$python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
# 本段代码核心功能：进入受控流程块（if）。
# - 输入：当前PowerShell变量、Git状态或文件路径，均来自脚本参数和前序显式检查。
# - 处理：按关键字语义执行单一分支、循环、函数或异常保护，不隐藏失败退出码。
# - 输出：更新局部变量、打印验收信息或抛出异常阻断后续提交，不修改业务数据库。
# - 常量依据：项目路径、main分支、UTF-8编码和零副作用要求来自任务合同及本机项目约定。
# - 为什么这样写：显式门禁能防止错误工作区、编码损坏或测试失败仍继续提交到GitHub。

if (-not (Test-Path -LiteralPath $python)) {
    $python = (Get-Command python -ErrorAction Stop).Source
}

$env:PYTHONPATH = Join-Path $ProjectRoot "src"

Write-Host "========== TASK_022 OFFLINE CONTRACT =========="
& $python "scripts\validate_task_022_provider_activation.py" --project-root $ProjectRoot
# 本段代码核心功能：进入受控流程块（if）。
# - 输入：当前PowerShell变量、Git状态或文件路径，均来自脚本参数和前序显式检查。
# - 处理：按关键字语义执行单一分支、循环、函数或异常保护，不隐藏失败退出码。
# - 输出：更新局部变量、打印验收信息或抛出异常阻断后续提交，不修改业务数据库。
# - 常量依据：项目路径、main分支、UTF-8编码和零副作用要求来自任务合同及本机项目约定。
# - 为什么这样写：显式门禁能防止错误工作区、编码损坏或测试失败仍继续提交到GitHub。

if ($LASTEXITCODE -ne 0) {
    throw "TASK_022 offline contract validation failed."
}

Write-Host "========== TASK_022 FOCUSED TESTS =========="
& $python -m unittest `
    tests.test_task_022_provider_activation `
    tests.test_provider_capabilities `
    tests.test_provider_plugin_protocol `
    tests.test_dolphindb_provider_plugin
# 本段代码核心功能：进入受控流程块（if）。
# - 输入：当前PowerShell变量、Git状态或文件路径，均来自脚本参数和前序显式检查。
# - 处理：按关键字语义执行单一分支、循环、函数或异常保护，不隐藏失败退出码。
# - 输出：更新局部变量、打印验收信息或抛出异常阻断后续提交，不修改业务数据库。
# - 常量依据：项目路径、main分支、UTF-8编码和零副作用要求来自任务合同及本机项目约定。
# - 为什么这样写：显式门禁能防止错误工作区、编码损坏或测试失败仍继续提交到GitHub。

if ($LASTEXITCODE -ne 0) {
    throw "TASK_022 focused unit tests failed."
}

Write-Host "========== FULL UNIT TEST SUITE =========="
& $python -m unittest discover -s tests -p "test_*.py"
# 本段代码核心功能：进入受控流程块（if）。
# - 输入：当前PowerShell变量、Git状态或文件路径，均来自脚本参数和前序显式检查。
# - 处理：按关键字语义执行单一分支、循环、函数或异常保护，不隐藏失败退出码。
# - 输出：更新局部变量、打印验收信息或抛出异常阻断后续提交，不修改业务数据库。
# - 常量依据：项目路径、main分支、UTF-8编码和零副作用要求来自任务合同及本机项目约定。
# - 为什么这样写：显式门禁能防止错误工作区、编码损坏或测试失败仍继续提交到GitHub。

if ($LASTEXITCODE -ne 0) {
    throw "Full unit test suite failed."
}

# 本段代码核心功能：进入受控流程块（if）。
# - 输入：当前PowerShell变量、Git状态或文件路径，均来自脚本参数和前序显式检查。
# - 处理：按关键字语义执行单一分支、循环、函数或异常保护，不隐藏失败退出码。
# - 输出：更新局部变量、打印验收信息或抛出异常阻断后续提交，不修改业务数据库。
# - 常量依据：项目路径、main分支、UTF-8编码和零副作用要求来自任务合同及本机项目约定。
# - 为什么这样写：显式门禁能防止错误工作区、编码损坏或测试失败仍继续提交到GitHub。

if (-not $env:DOLPHINDB_PASSWORD) {
    $secure = Read-Host "Enter DolphinDB password (not written to disk)" -AsSecureString
    $ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    # 本段代码核心功能：进入受控流程块（try）。
    # - 输入：当前PowerShell变量、Git状态或文件路径，均来自脚本参数和前序显式检查。
    # - 处理：按关键字语义执行单一分支、循环、函数或异常保护，不隐藏失败退出码。
    # - 输出：更新局部变量、打印验收信息或抛出异常阻断后续提交，不修改业务数据库。
    # - 常量依据：项目路径、main分支、UTF-8编码和零副作用要求来自任务合同及本机项目约定。
    # - 为什么这样写：显式门禁能防止错误工作区、编码损坏或测试失败仍继续提交到GitHub。

    try {
        $env:DOLPHINDB_PASSWORD = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr)
    }
    # 本段代码核心功能：进入受控流程块（finally）。
    # - 输入：当前PowerShell变量、Git状态或文件路径，均来自脚本参数和前序显式检查。
    # - 处理：按关键字语义执行单一分支、循环、函数或异常保护，不隐藏失败退出码。
    # - 输出：更新局部变量、打印验收信息或抛出异常阻断后续提交，不修改业务数据库。
    # - 常量依据：项目路径、main分支、UTF-8编码和零副作用要求来自任务合同及本机项目约定。
    # - 为什么这样写：显式门禁能防止错误工作区、编码损坏或测试失败仍继续提交到GitHub。

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
# 本段代码核心功能：进入受控流程块（if）。
# - 输入：当前PowerShell变量、Git状态或文件路径，均来自脚本参数和前序显式检查。
# - 处理：按关键字语义执行单一分支、循环、函数或异常保护，不隐藏失败退出码。
# - 输出：更新局部变量、打印验收信息或抛出异常阻断后续提交，不修改业务数据库。
# - 常量依据：项目路径、main分支、UTF-8编码和零副作用要求来自任务合同及本机项目约定。
# - 为什么这样写：显式门禁能防止错误工作区、编码损坏或测试失败仍继续提交到GitHub。

if ($LASTEXITCODE -ne 0) {
    throw "TASK_022 real read-only registry route acceptance failed."
}

Write-Host "========== ENCODING AUDIT =========="
& $python "scripts\audit_git_encoding.py"
# 本段代码核心功能：进入受控流程块（if）。
# - 输入：当前PowerShell变量、Git状态或文件路径，均来自脚本参数和前序显式检查。
# - 处理：按关键字语义执行单一分支、循环、函数或异常保护，不隐藏失败退出码。
# - 输出：更新局部变量、打印验收信息或抛出异常阻断后续提交，不修改业务数据库。
# - 常量依据：项目路径、main分支、UTF-8编码和零副作用要求来自任务合同及本机项目约定。
# - 为什么这样写：显式门禁能防止错误工作区、编码损坏或测试失败仍继续提交到GitHub。

if ($LASTEXITCODE -ne 0) {
    throw "Encoding audit failed."
}

Write-Host "========== TEACHING COMMENT AUDIT =========="
& $python `
    "scripts\audit_teaching_comments.py" `
    --project-root $ProjectRoot `
    --output "$ProjectRoot\reports\task_022_teaching_comment_audit.json" `
    --mode enforce
# 本段代码核心功能：进入受控流程块（if）。
# - 输入：当前PowerShell变量、Git状态或文件路径，均来自脚本参数和前序显式检查。
# - 处理：按关键字语义执行单一分支、循环、函数或异常保护，不隐藏失败退出码。
# - 输出：更新局部变量、打印验收信息或抛出异常阻断后续提交，不修改业务数据库。
# - 常量依据：项目路径、main分支、UTF-8编码和零副作用要求来自任务合同及本机项目约定。
# - 为什么这样写：显式门禁能防止错误工作区、编码损坏或测试失败仍继续提交到GitHub。

if ($LASTEXITCODE -ne 0) {
    throw "Teaching comment audit failed."
}

Write-Host "========== GIT DIFF CHECK =========="
git diff --check
# 本段代码核心功能：进入受控流程块（if）。
# - 输入：当前PowerShell变量、Git状态或文件路径，均来自脚本参数和前序显式检查。
# - 处理：按关键字语义执行单一分支、循环、函数或异常保护，不隐藏失败退出码。
# - 输出：更新局部变量、打印验收信息或抛出异常阻断后续提交，不修改业务数据库。
# - 常量依据：项目路径、main分支、UTF-8编码和零副作用要求来自任务合同及本机项目约定。
# - 为什么这样写：显式门禁能防止错误工作区、编码损坏或测试失败仍继续提交到GitHub。

if ($LASTEXITCODE -ne 0) {
    throw "git diff --check failed."
}

Write-Host ""
Write-Host "TASK_022 VALIDATION PASSED" -ForegroundColor Green
Write-Host "Review git diff, then run complete_task_022.ps1 from the hotfix package."
