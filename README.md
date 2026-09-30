# Hunter Roulette preservation lab

Private collaboration workspace for the independently written local backend,
regression tests and research notes. **Not a game distribution or a turnkey
installer.** Each developer supplies a compatible, legally obtained client.
The original game installation must remain untouched.

## Comece aqui / Start here

- [Guia em português](docs/COLLABORATION_PT.md)
- [Current status and remaining work](docs/CURRENT_STATUS.md)
- [Contribution workflow](CONTRIBUTING.md)
- [Security and exclusions](SECURITY.md)
- Historical findings: `docs/history/` (mostly Brazilian Portuguese).

Python 3.14 is the locally tested runtime; Python 3.11+ is required for
`asyncio.timeout`, but other versions are not fully validated. The backend and
test suite use only the standard library. No Unity assets are needed for tests.

```powershell
python -m unittest discover -s server/tests -q
.\tools\Test-Project.ps1
.\tools\Start-Server.ps1 -GameCopyRoot 'D:\Games\Hunter Roulette Lab'
```

Start-Server launches only the backend, not the game or any client patch.
The compatible laboratory client has historical modifications not yet supplied
as an audited portable installer. A clean Steam client is not guaranteed to
connect/play with this backend. See CURRENT_STATUS before reporting setup errors.

## Share changes, not private state

Clone this repository, work in your own branch, commit/push, then propose a
pull request. Tests run in GitHub Actions after remote setup. Update with
`tools/Update-Project.ps1` (fast-forward only; refuses a dirty working tree).
GitHub Desktop can perform the same operations without command-line Git.

`tools/Sync-Lab.ps1` bridges this source repository with a compatible isolated
game copy. Export copies approved source/notes from the lab; Apply installs
only server modules/tests, with a recoverable backup and the game closed.
It never copies saves, credentials, binaries or Unity assets. Preview is default;
pass `-Execute` after checking the proposed changes.

No repository has been uploaded until a remote URL is configured and a push
succeeds. Saving locally is not the same as publishing or updating teammates.
Do not enable unattended pull/apply on a running server or game.

No license to redistribute the game's proprietary content is granted. A public
source license for our code has not been selected; keep access private until
the project owner decides licensing and membership.
