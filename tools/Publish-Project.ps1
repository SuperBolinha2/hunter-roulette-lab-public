param([Parameter(Mandatory=$true)][string]$Message)
$ErrorActionPreference='Stop'
$repoRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
Push-Location -LiteralPath $repoRoot
try {
    git remote get-url origin | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'No origin configured. Connect the private repository first.' }
    $branch=git branch --show-current
    if (-not $branch -or $branch -eq 'main') { throw 'Create a work/topic branch first; shared main is not auto-published.' }
    & (Join-Path $PSScriptRoot 'Test-Project.ps1')
    git add -- server docs tools .github README.md CONTRIBUTING.md SECURITY.md .gitignore .gitattributes
    if ($LASTEXITCODE -ne 0) { throw 'Staging failed.' }
    git diff --cached --stat
    git diff --cached --quiet
    if ($LASTEXITCODE -eq 0) { Write-Host 'No changes to commit.'; return }
    if ($LASTEXITCODE -ne 1) { throw 'Cannot inspect staged changes.' }
    $answer=Read-Host 'Reviewed staged changes? Type PUBLICAR to commit and push this branch'
    if ($answer -cne 'PUBLICAR') { Write-Host 'Publication cancelled; staged files preserved.'; return }
    git commit -m $Message
    if ($LASTEXITCODE -ne 0) { throw 'Commit failed; nothing pushed.' }
    git push -u origin HEAD
    if ($LASTEXITCODE -ne 0) { throw 'Push failed; local commit preserved.' }
} finally { Pop-Location }
