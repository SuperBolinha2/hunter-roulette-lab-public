param([string]$Python='python')
$ErrorActionPreference='Stop'
$repoRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
Push-Location -LiteralPath $repoRoot
try {
    & $Python .\tools\audit_share.py
    if ($LASTEXITCODE -ne 0) { throw 'Sharing audit failed.' }
    & $Python -m unittest discover -s server/tests -q
    if ($LASTEXITCODE -ne 0) { throw 'Regression tests failed.' }
    & (Join-Path $PSScriptRoot 'Test-Sync.ps1')
} finally { Pop-Location }
