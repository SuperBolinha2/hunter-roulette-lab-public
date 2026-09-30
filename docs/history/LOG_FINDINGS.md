# Historical log findings

## Inventory

- Eleven Unity/game logs: 2026-03-13 through 2026-05-04.
- Launcher logs: `RLGame.log` plus three backups, `RLBrowser.log` plus two backups.
- Three QAV/GME voice SDK logs.
- The largest game log is `outLog_26_03_14_03_30_16_1773459016.txt` at 360,412 bytes and contains the richest gameplay evidence.

## Confirmed timeline evidence

- Every sampled session performs hotfix/version loading before SDK login and TCP activity.
- March builds request code/resource line `716.702`; later April/May logs show `716.706`.
- Historical sessions reached real battle scenes: the largest log contains repeated card callbacks, multiple `RouletteGameSceneController:OnShootOver(Int32)` stacks, voice-room setup/exit, scene teardown, and return to the role/hall scene.
- TCP connection attempts are visible through `AntNet.TcpObject_New:Connect` stacks.
- Server-returned errors preserve command pairs. Examples:
  - `cmd 3 / act 4`, error 638: interactive item cooldown.
  - `cmd 3 / act 5`, error 639: target already has the effect.
  - `cmd 5 / act 5`, error 627: room player rank difference too large.
  - `cmd 5 / act 7`, error 583: only the host may operate.
- These errors corroborate the Lua command table and prove that error responses retain the original request's cmd/act.

## Privacy boundary

The logs also contain live or historical tokens, user IDs, device IDs, friend lists, IP addresses, chat/translation text, and SDK secrets. Findings must be recorded structurally; raw lines containing those fields must not be copied.

## What the logs do not provide

- No raw official TCP hex dump was found.
- No complete decoded official protobuf exchange was found.
- Exact official IP/port values are intentionally excluded and are unnecessary for localhost preservation.

## Prior localhost run: 2026-09-13 13:40

The preserved emulator log supplies stronger local evidence than the earlier summary:

- Local HTTP bootstrap, logic login, profile requests, and local match creation completed.
- PVP connected; the client sent `3/20`, `3/1`, heartbeat `3/2`, then scene-ready `3/14`.
- At 13:40:28 the emulator returned the player snapshot and pushed the initial turn.
- The client sent behavior packets and a first `3/3` at 13:40:32. The emulator recorded bot HP `4 -> 3`, player ammo `6 -> 5`, and scheduled the bot event after 1.8 seconds.
- The client then requested post-action state (`3/19`) and ancillary PVP state (`3/29`, `3/33`).
- A second behavior/shot sequence arrived at 13:40:40. The emulator recorded bot HP `3 -> 2`, player HP `3 -> 2`, and player ammo `5 -> 4`.
- Heartbeats/queries continued until both TCP sessions disconnected at 13:40:53.

This confirms two client-originated shots at the transport/state-machine level. It does **not** confirm what was rendered, whether every animation/state update was correct, or whether `255/5` and the results screen work.

The matching client log stops at 13:40:26 with `NullReferenceException` in `BackGroundCtrl.OnDestroy`. Because the server received gameplay traffic for another 27 seconds, treat that exception as a logging/runtime anomaly to isolate, not as proof that battle entry failed.
