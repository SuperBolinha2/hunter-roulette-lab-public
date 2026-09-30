param([Parameter(Mandatory=$true)][string]$GameCopyRoot,[int]$PollSeconds=3)
if ($PollSeconds -lt 2) { throw 'Minimum poll interval is two seconds.' }
Write-Host 'Local export only. No Git push/pull or game modifications. Ctrl+C stops.'
while ($true) {
    try { & (Join-Path $PSScriptRoot 'Sync-Lab.ps1') -Direction Export -GameCopyRoot $GameCopyRoot -Execute }
    catch { Write-Warning $_; break }
    Start-Sleep -Seconds $PollSeconds
}
