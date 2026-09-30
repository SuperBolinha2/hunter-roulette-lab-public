param([Parameter(Mandatory=$true)][string]$GameCopyRoot,[string]$Python='python',
    [ValidateSet('easy','medium','hard','scripted')][string]$BotDifficulty='medium')
$ErrorActionPreference='Stop'
$repoRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$labRoot=[IO.Path]::GetFullPath($GameCopyRoot)
if ((Split-Path $labRoot -Leaf) -eq 'Hunter Roulette') { throw 'Use an isolated game copy, not the original.' }
$pkg=Join-Path $labRoot 'Game\Client_Data\StreamingAssets\PkgVersion.json'
if (-not (Test-Path -LiteralPath $pkg -PathType Leaf)) { throw 'Missing compatible copied client PkgVersion.json.' }
if (Get-NetTCPConnection -State Listen -LocalPort 38000,38001,38002 -ErrorAction SilentlyContinue) { throw 'Local ports occupied; no unrelated process will be stopped.' }
$runRoot=Join-Path $repoRoot 'runtime'
$null=New-Item -ItemType Directory -Force -Path $runRoot
$inventory=Join-Path $runRoot 'inventory.json'
if (-not (Test-Path -LiteralPath $inventory)) { Copy-Item -LiteralPath (Join-Path $repoRoot 'server\inventory.example.json') -Destination $inventory }
$trace=Join-Path $runRoot ('packet-trace-'+(Get-Date -Format yyyyMMdd-HHmmss)+'.jsonl')
Push-Location -LiteralPath (Join-Path $repoRoot 'server')
try {
    & $Python .\server.py --host 127.0.0.1 --pkg-version $pkg --inventory $inventory --trace-file $trace --bot-difficulty $BotDifficulty
    if ($LASTEXITCODE -ne 0) { throw 'Server failed.' }
} finally { Pop-Location }
