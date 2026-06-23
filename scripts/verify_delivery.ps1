param(
    [string]$Remote = "origin",
    [string]$Branch = "main",
    [switch]$Fetch
)

$ErrorActionPreference = "Stop"

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
