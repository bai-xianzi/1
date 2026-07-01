param(
    [string]$Remote = "origin",
    [string]$Branch = "main",
    [switch]$Fetch
)

$ErrorActionPreference = "Stop"

# PowerShell函数 `Invoke-Git`：封装 `scripts/verify_delivery.ps1` 中对应的可复用操作。
# - 输入：参数块、调用参数、环境变量、项目路径或上游管道对象。
# - 处理：保持原命令、参数、异常和文件操作顺序，仅补充说明。
# - 输出：返回管道对象、文件、状态、退出码或显式异常。
# - 为什么这样写：明确函数边界和破坏性操作，便于复核、测试和安全回滚。
function Invoke-Git {
    param(
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$Args
    )

    $output = & git @Args 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "git $($Args -join ' ') failed:`n$output"
    }

    return $output
}

$inside = (Invoke-Git rev-parse --is-inside-work-tree).Trim()
if ($inside -ne "true") {
    throw "The current directory is not a Git repository."
}

$repoRoot = (Invoke-Git rev-parse --show-toplevel).Trim()
Push-Location $repoRoot

try {
    if (Test-Path ".\scripts\audit_git_encoding.py") {
        Write-Host "Running UTF-8 repository audit ..."
        & python ".\scripts\audit_git_encoding.py"
        if ($LASTEXITCODE -ne 0) {
            throw "UTF-8 repository audit failed."
        }
    }
    else {
        Write-Warning "Encoding audit script is missing."
    }

    if ($Fetch) {
        Write-Host "Fetching remote references from $Remote ..."
        Invoke-Git fetch $Remote | Out-Null
    }

    $localBranch = (Invoke-Git branch --show-current).Trim()
    $head = (Invoke-Git rev-parse HEAD).Trim()
    $status = @(Invoke-Git status --porcelain)

    Write-Host "=== Delivery status check ==="
    Write-Host "Local branch : $localBranch"
    Write-Host "Local HEAD   : $head"

    if ($localBranch -ne $Branch) {
        Write-Warning "Current branch is not the expected branch: $Branch"
    }

    $dirtyLines = @(
        $status | Where-Object {
            -not [string]::IsNullOrWhiteSpace($_)
        }
    )

    if ($dirtyLines.Count -gt 0) {
        Write-Host "Working tree contains uncommitted changes:"
        $dirtyLines | ForEach-Object {
            Write-Host $_
        }
        exit 2
    }

    Write-Host "Working tree : clean"

    $remoteRef = "$Remote/$Branch"

    try {
        $remoteHead = (Invoke-Git rev-parse $remoteRef).Trim()
    }
    catch {
        Write-Warning "Cannot resolve remote branch $remoteRef. Retry with -Fetch."
        exit 3
    }

    Write-Host "Remote ref   : $remoteRef"
    Write-Host "Remote HEAD  : $remoteHead"

    $countsText = (
        Invoke-Git rev-list --left-right --count "$remoteRef...HEAD"
    ).Trim()

    $counts = $countsText -split "\s+"
    if ($counts.Count -lt 2) {
        throw "Unexpected rev-list output: $countsText"
    }

    $behind = [int]$counts[0]
    $ahead = [int]$counts[1]

    Write-Host "Local ahead  : $ahead"
    Write-Host "Local behind : $behind"

    if ($head -ne $remoteHead) {
        Write-Warning "Local HEAD and remote HEAD are not identical."
        exit 4
    }

    Write-Host "Delivery status: PASSED"
    Write-Host "Local repository and GitHub remote branch are identical."
    exit 0
}
finally {
    Pop-Location
}
