$ErrorActionPreference='Stop'
$repoRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
Push-Location -LiteralPath $repoRoot
try {
    git config --local core.hooksPath tools/hooks
    if ($LASTEXITCODE -ne 0) { throw 'Cannot install repository-local hook.' }
    Write-Host 'Local pre-push sharing audit enabled; no global Git setting changed.'
} finally { Pop-Location }
