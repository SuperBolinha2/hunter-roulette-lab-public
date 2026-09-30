$ErrorActionPreference='Stop'
$repoRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
Push-Location -LiteralPath $repoRoot
try {
    if (@(git status --porcelain).Count) { throw 'Working tree has changes. Commit or resolve them first; nothing overwritten.' }
    git remote get-url origin | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'No origin configured yet.' }
    git pull --ff-only
    if ($LASTEXITCODE -ne 0) { throw 'Update requires manual resolution; no forced reset was performed.' }
    & (Join-Path $PSScriptRoot 'Test-Project.ps1')
    Write-Host 'Source updated and tested. Game copy was NOT modified; preview Sync-Lab Apply when ready.'
} finally { Pop-Location }
