# Non-destructive isolated fixture test. Fixtures remain recoverable in .local.
$ErrorActionPreference='Stop'
$repoRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$fixtureRoot=Join-Path $repoRoot ('.local/sync-test-'+[guid]::NewGuid().ToString('N'))
$fixtureRepo=Join-Path $fixtureRoot 'repo'
$fixtureLab=Join-Path $fixtureRoot 'LabFixture'
foreach ($dir in @('repo/tools','lab-placeholder','LabFixture/research/private-server/tests')) {
    $null=New-Item -ItemType Directory -Force -Path (Join-Path $fixtureRoot $dir)
}
foreach ($name in @('Sync-Lab.ps1','Modules.json')) {
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot $name) -Destination (Join-Path $fixtureRepo 'tools')
}
$modules=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'Modules.json') -Raw|ConvertFrom-Json
foreach ($m in $modules) {
    Copy-Item -LiteralPath (Join-Path $repoRoot "server/$m") -Destination (Join-Path $fixtureLab 'research/private-server')
}
Copy-Item -LiteralPath (Join-Path $repoRoot 'docs/history/GAMEPLAY_FINDINGS.md') -Destination (Join-Path $fixtureLab 'research/private-server/GAMEPLAY_FINDINGS.md')
$sync=Join-Path $fixtureRepo 'tools/Sync-Lab.ps1'
& $sync -Direction Export -GameCopyRoot $fixtureLab -Execute
$repoFile=Join-Path $fixtureRepo 'server/hero_shop.py'
$labFile=Join-Path $fixtureLab 'research/private-server/hero_shop.py'
if ((Get-FileHash -LiteralPath $repoFile).Hash -ne (Get-FileHash -LiteralPath $labFile).Hash) { throw 'Initial export mismatch.' }
# Synthetic fixture only: deliberately edit both sides and assert no overwrite.
$original=[IO.File]::ReadAllText($repoFile)
[IO.File]::WriteAllText($repoFile,$original+"`n# fixture repo edit`n",[Text.UTF8Encoding]::new($false))
[IO.File]::WriteAllText($labFile,$original+"`n# fixture lab edit`n",[Text.UTF8Encoding]::new($false))
$conflictBlocked=$false
try { & $sync -Direction Export -GameCopyRoot $fixtureLab -Execute }
catch { if ($_.Exception.Message -like 'Both sides changed*') { $conflictBlocked=$true } else { throw } }
if (-not $conflictBlocked) { throw 'Conflicting changes were not blocked.' }
if ([IO.File]::ReadAllText($repoFile) -notmatch 'fixture repo edit') { throw 'Repository edit was overwritten.' }
# Reset the synthetic repo fixture to the baseline; a lab-only edit must export.
[IO.File]::WriteAllText($repoFile,$original,[Text.UTF8Encoding]::new($false))
& $sync -Direction Export -GameCopyRoot $fixtureLab -Execute
if ([IO.File]::ReadAllText($repoFile) -notmatch 'fixture lab edit') { throw 'Lab edit was not exported.' }
if (-not (Get-ChildItem -LiteralPath (Join-Path $fixtureRepo 'backups') -Recurse -File)) { throw 'Recoverable backup was not created.' }
$originalBlocked=$false
try { & $sync -Direction Export -GameCopyRoot (Join-Path $fixtureRoot 'Hunter Roulette') -Execute }
catch { if ($_.Exception.Message -like 'Original game is forbidden*') { $originalBlocked=$true } else { throw } }
if (-not $originalBlocked) { throw 'Original installation safety boundary failed.' }
Write-Host 'Sync fixture tests passed: initial export, conflict refusal, lab-only update, backup, original-path rejection.'
Write-Host "Recoverable test fixture (ignored): $fixtureRoot"
