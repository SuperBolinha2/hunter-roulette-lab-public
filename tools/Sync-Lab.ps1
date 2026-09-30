param([Parameter(Mandatory=$true)][ValidateSet('Export','Apply')][string]$Direction,
    [Parameter(Mandatory=$true)][string]$GameCopyRoot,[switch]$Execute)
$ErrorActionPreference='Stop'
$repoRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$labRoot=[IO.Path]::GetFullPath($GameCopyRoot).TrimEnd('\')
if ((Split-Path $labRoot -Leaf) -eq 'Hunter Roulette') { throw 'Original game is forbidden. Use an isolated copy.' }
$labServer=Join-Path $labRoot 'research\private-server'
if (-not (Test-Path -LiteralPath (Join-Path $labServer 'server.py'))) { throw 'Expected an existing compatible isolated lab, not a clean-client installer.' }
if ($Direction -eq 'Apply') {
    $gameClient=Join-Path $labRoot 'Game\Client.exe'
    if (Get-Process -Name Client -ErrorAction SilentlyContinue | Where-Object { $_.Path -eq $gameClient }) { throw 'Close the copied game before applying source.' }
    if (Get-NetTCPConnection -State Listen -LocalPort 38000,38001,38002 -ErrorAction SilentlyContinue) { throw 'Stop the local backend before applying source.' }
}
$statePath=Join-Path $repoRoot '.local\sync-state.json'
$baseline=@{}
if (Test-Path -LiteralPath $statePath) {
    $state=Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json
    if ($state.labRoot -ne $labRoot) { throw 'Sync state belongs to another lab; use a separate clone for each lab.' }
    foreach ($p in $state.hashes.PSObject.Properties) { $baseline[$p.Name]=$p.Value }
}
$modules=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'Modules.json') -Raw | ConvertFrom-Json
$pairs=@()
foreach ($m in $modules) { $pairs+=@{repo="server/$m";lab="research/private-server/$m";doc=$false} }
$testRoot=if ($Direction -eq 'Export') { Join-Path $labServer 'tests' } else { Join-Path $repoRoot 'server\tests' }
foreach ($f in Get-ChildItem -LiteralPath $testRoot -File -Filter 'test_*.py') { $pairs+=@{repo="server/tests/$($f.Name)";lab="research/private-server/tests/$($f.Name)";doc=$false} }
if ($Direction -eq 'Export') {
    $notes=@(Get-ChildItem -LiteralPath (Join-Path $labRoot 'research') -File -Filter '*.md')
    $notes+=Get-Item -LiteralPath (Join-Path $labServer 'GAMEPLAY_FINDINGS.md')
    foreach ($n in $notes) { $pairs+=@{repo="docs/history/$($n.Name)";lab=$n.FullName.Substring($labRoot.Length+1);doc=$true} }
}
function Get-SafeBody($pair) {
    $body=[IO.File]::ReadAllText((Join-Path $labRoot $pair.lab))
    if ($pair.doc) {
        $body=$body.Replace($labRoot,'<LAB_ROOT>').Replace((Join-Path (Split-Path $labRoot -Parent) 'Hunter Roulette'),'<ORIGINAL_GAME_ROOT>')
        $body=[regex]::Replace($body,'(?i)[A-Z]:\\Users\\[^\s`"<>]+','<LOCAL_USER_PATH>')
        $body=[regex]::Replace($body,'(?i)[\w.+-]+@[\w.-]+\.[A-Z]{2,}','<REDACTED_EMAIL>')
        $body=$body.Replace('vinic','<local-user>')
    }
    return $body
}
function BodyHash([string]$body) {
    $sha=[Security.Cryptography.SHA256]::Create()
    try { return ([BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($body)))).Replace('-','') } finally { $sha.Dispose() }
}
$plan=@();$pending=@();$conflicts=@()
foreach ($pair in $pairs) {
    $repoFile=Join-Path $repoRoot $pair.repo
    $labFile=Join-Path $labRoot $pair.lab
    $labBody=if (Test-Path -LiteralPath $labFile) { Get-SafeBody $pair } else { $null }
    $repoBody=if (Test-Path -LiteralPath $repoFile) { [IO.File]::ReadAllText($repoFile) } else { $null }
    $labHash=if ($null -ne $labBody) { BodyHash $labBody } else { '' }
    $repoHash=if ($null -ne $repoBody) { BodyHash $repoBody } else { '' }
    if ($labHash -eq $repoHash) { $baseline[$pair.repo]=$repoHash;continue }
    $old=if ($baseline.ContainsKey($pair.repo)) { $baseline[$pair.repo] } else { '' }
    $sourceHash=if ($Direction -eq 'Export') { $labHash } else { $repoHash }
    $destHash=if ($Direction -eq 'Export') { $repoHash } else { $labHash }
    if (-not $sourceHash) { $conflicts+=$pair.repo+' (missing source)';continue }
    if ($destHash -and $destHash -ne $old) {
        if ($sourceHash -eq $old) { $pending+=$pair.repo;continue }
        $conflicts+=$pair.repo;continue
    }
    $plan+=@{pair=$pair;body=$(if ($Direction -eq 'Export') { $labBody } else { $repoBody });hash=$sourceHash}
}
if ($conflicts.Count) { throw ('Both sides changed or no baseline: '+($conflicts -join ', ')+'. Resolve manually; nothing copied.') }
if ($pending.Count) { Write-Host ('Opposite-direction changes preserved: '+($pending -join ', ')) }
foreach ($item in $plan) { Write-Host "$Direction $($item.pair.repo)" }
if (-not $Execute) { Write-Host "Preview: $($plan.Count) files. Add -Execute to perform the sync."; return }
$backupRoot=Join-Path $repoRoot ('backups/'+(Get-Date -Format 'yyyyMMdd-HHmmss-fff'))
foreach ($item in $plan) {
    $relative=if ($Direction -eq 'Export') { $item.pair.repo } else { $item.pair.lab }
    $dest=Join-Path $(if ($Direction -eq 'Export') { $repoRoot } else { $labRoot }) $relative
    if (Test-Path -LiteralPath $dest) {
        $backup=Join-Path $backupRoot $relative
        $null=New-Item -ItemType Directory -Force -Path (Split-Path $backup -Parent)
        Copy-Item -LiteralPath $dest -Destination $backup
    }
    $null=New-Item -ItemType Directory -Force -Path (Split-Path $dest -Parent)
    [IO.File]::WriteAllText($dest,$item.body,[Text.UTF8Encoding]::new($false))
    $baseline[$item.pair.repo]=$item.hash
}
$null=New-Item -ItemType Directory -Force -Path (Split-Path $statePath -Parent)
$stateJson=@{labRoot=$labRoot;hashes=$baseline}|ConvertTo-Json -Depth 5
[IO.File]::WriteAllText($statePath,$stateJson,[Text.UTF8Encoding]::new($false))
if ($plan.Count) { Write-Host "Synchronized $($plan.Count) approved files; saves/assets untouched. Existing files backed up under backups/." }
