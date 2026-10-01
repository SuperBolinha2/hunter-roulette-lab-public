# Repository instructions for coding agents

## Feature progress is tracked here

The canonical feature checklist is [docs/FEATURE_CHECKLIST.md](docs/FEATURE_CHECKLIST.md).
It records confirmed behavior, partial work and missing features by menu, hero,
weapon, item and system. Do not create a competing completion list.

For changes to game behavior, menus, progression or feature support:

1. Find and read the relevant checklist section before implementation.
   Search by feature name or stable ID; reading the entire technical catalog
   is not required for an unrelated small change.
2. Include the affected checklist IDs in the work summary / pull request.
3. Update those rows in the same change: describe what works, what was tested
   and what remains. Add a new stable ID if the behavior has no existing row.
   Preserve existing IDs and unrelated contributors' updates.
4. Keep `[ ] [TESTAR]` when implementation/automated tests pass but required
   player/runtime validation is missing. Use `[ ] [PARCIAL]` when only part works.
5. Use `[x] [CONFIRMADO]` only with recorded manual approval for that precise
   scope. An ACK, icon, recovered description or unit test does not prove
   animation, camera, audio, persistence, multiplayer or every mode.
6. Reopen a row as partial when a regression is confirmed, preserving prior
   evidence and explaining the new limitation.
7. In the handoff, report IDs updated, tests run and manual checks still needed.

Use [docs/templates/FEATURE_TEST.md](docs/templates/FEATURE_TEST.md) for a
new discovery/test record. Use [docs/FEATURE_CATALOG.md](docs/FEATURE_CATALOG.md)
when investigating native windows, modes or cfgIds; its references do not mean
those features are implemented.

For documentation, tooling or refactoring with no feature-status impact,
state that in the work summary; do not mark a gameplay feature done merely
to satisfy this workflow.

## Working boundaries

- Follow [CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md).
- Keep the original game read-only; only use the isolated compatible lab copy.
- Preserve GM progress, inventory and other people's changes unless the user
  explicitly requests otherwise.
- Never commit client assets/binaries, Lua dumps, personal packet traces,
  saves or credentials. The repository contains backend code and safe notes.
- Do not silently enable unsupported modes or assume fallback gameplay proves
  support. Existing confirmations are local three-seat tests unless stated.
- Do not restart the player's game/server unless the current task authorizes it.

## Verification

From the repository root:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\Test-Project.ps1
```

If Python is not on PATH, pass `-Python <python-executable>`. Report actual
results and limitations. For code changes, add relevant regression coverage.

## Code Review Rules

- Flag behavior changes without the relevant checklist update or an explicit
  explanation of no feature-status impact.
- Flag completion claims supported only by static/protocol tests when manual
  validation is required. The safe status is TESTAR or PARCIAL, not CONFIRMADO.
