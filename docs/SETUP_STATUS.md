# Collaboration setup — 2026-09-30

Private repository: https://github.com/SuperBolinha2/hunter-roulette-lab
Initial source published; Git credential login completed through the owner's
browser, no passwords/tokens stored in this project. Original game and GM
inventory were not touched. No collaborators invited yet.

Included:10 backend modules,21 test files,33 sanitized historical notes,
synthetic inventory and safe development tools.285 backend tests passed
both in the export and a fresh clone downloaded from GitHub. The cloud
workflow also passed. Sync fixture checks confirm conflict refusal, backup,
source export and original-installation rejection. Apply remains opt-in and
requires game/backend closed; it was not applied to the real lab during setup.

Protection API for main returned403. GitHub-enforced PR/review/check rules
are therefore NOT enabled. Private visibility was retained; no account plan
was changed. Use topic branches and reviews by convention until supported
branch rules can be configured. Local Publish script refuses main and asks
for explicit confirmation; owner can still use Git directly.

Local pre-push audit enabled for the owner's clone. Collaborators should run
`tools/Install-Hooks.ps1` once. Hooks are not automatically installed by clone
and can be bypassed; they do not replace access control/review/CI.

Local export watcher is available but was NOT started or added to Windows
startup. No unattended cloud push/pull, background updater or game overwrite
was enabled. Publication/update is explicit, preserving in-progress work.
