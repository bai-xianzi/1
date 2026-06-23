$ErrorActionPreference = "Stop"

$root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $root
$env:PYTHONPATH = (Resolve-Path ".\src").Path

Write-Host "=== TASK_014 configuration gate ==="
$config = Get-Content `
    ".\configs\datasets\a_stock_fundamental_snapshot.json" `
    -Raw `
    -Encoding UTF8 | ConvertFrom-Json

if ($config.enabled -ne $false) {
    throw "Fundamental dataset must remain disabled before acceptance."
}
if ($config.mapping_version -ne "0.2.0-rc2") {
    throw "Unexpected fundamental mapping version."
}
if ($config.dictionary_revision -ne "0.5") {
    throw "Unexpected canonical dictionary revision."
}

Write-Host "=== TASK_014 external-path guard ==="
$externalMatches = git grep -n `
    -e "D:\\Users\\Administrator\\Desktop" `
    -- "src" "configs" 2>$null
if ($LASTEXITCODE -notin @(0, 1)) {
    throw "git grep failed"
}
if ($externalMatches) {
    $externalMatches | Write-Host
    throw "src/configs contain an external desktop dependency."
}

Write-Host "=== TASK_014 compile ==="
python -m compileall src tests scripts
if ($LASTEXITCODE -ne 0) {
    throw "compileall failed"
}

Write-Host "=== TASK_014 full tests ==="
python -m unittest discover -s tests -v
if ($LASTEXITCODE -ne 0) {
    throw "unit tests failed"
}

Write-Host "=== TASK_014 candidate UTF-8 scan ==="
@'
from pathlib import Path

roots = [
    Path("src"),
    Path("tests"),
    Path("scripts"),
    Path("tasks"),
    Path("configs"),
    Path("reports"),
]
extensions = {
    ".py", ".ps1", ".md", ".json", ".yaml", ".yml",
}
failures = []
for root in roots:
    if not root.exists():
        continue
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in extensions:
            continue
        try:
            raw = path.read_bytes()
            if raw.startswith(b"\xef\xbb\xbf"):
                failures.append(f"BOM: {path}")
            raw.decode("utf-8")
        except UnicodeError as exc:
            failures.append(f"NON_UTF8: {path}: {exc}")
if failures:
    raise SystemExit("\n".join(failures))
print("Candidate UTF-8 scan: PASSED")
'@ | python -
if ($LASTEXITCODE -ne 0) {
    throw "candidate UTF-8 scan failed"
}

Write-Host "=== Existing tracked-file encoding audit ==="
python ".\scripts\audit_git_encoding.py"
if ($LASTEXITCODE -ne 0) {
    throw "encoding audit failed"
}

Write-Host "TASK_014 authority-aligned candidate verification passed."
