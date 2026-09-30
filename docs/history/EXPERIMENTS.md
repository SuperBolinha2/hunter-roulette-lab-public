# Experiments

## E-000 Baseline comparison

- Hypothesis: the writable sibling copy starts from the same critical client snapshot as the original.
- Changed: nothing in either game tree.
- Expected: equal paths/sizes and critical SHA-256 hashes.
- Observed: 1300 files and 3,519,042,360 bytes in each; no path/size differences; all listed critical hashes equal.
- Conclusion: `[CONFIRMED]` the lab copy is a valid starting point for controlled modifications.
- Next: record any lab patch as a relative-path/hash delta.

## E-001 Prior IL2CPP dump applicability

- Hypothesis: the prior dump still matches the current original/lab binaries.
- Changed: nothing.
- Expected: current `GameAssembly.dll` and `global-metadata.dat` hashes match the snapshot used previously.
- Observed: critical hashes match and all previously recovered symbol families are present.
- Conclusion: `[HIGH CONFIDENCE]` the prior dump is applicable. A fresh dump is optional, not the current bottleneck.
- Next: only rerun Il2CppDumper if a symbol/RVA mismatch appears.

## E-002 Prior protocol emulator tests

- Hypothesis: the hand-built AntNet/protobuf encoder is internally consistent.
- Changed: prior isolated lab only.
- Expected: compilation and eight protocol tests pass.
- Observed again on 2026-09-16: `Ran 8 tests ... OK`; `protocol.py` and `server.py` also passed `py_compile`.
- Conclusion: `[CONFIRMED: prior static test]` encoders satisfy their assertions. This does not prove playability.
- Next: preserve outgoing-frame hex and correlate it with a visual recording.

## E-003 Prior live action-cycle evidence

- Hypothesis: after PVP login and `3/14`, the minimum enabling sequence is `255/7` then `255/1`; a player `3/3` request can be completed by `255/2` plus a subsequent `255/1`.
- Changed: prior isolated localhost emulator only.
- Expected: the client sends one shot, consumes the resolved player/bot events and next-round push, then becomes able to shoot again.
- Observed: after `3/14` and the initial-turn push, the client sent shots at 13:40:32 and 13:40:40. Between them it issued the expected post-action state queries. The server-side state moved bot HP `4 -> 3 -> 2`, player HP `4 -> 3 -> 2`, and player ammo `6 -> 5 -> 4`.
- Conclusion: `[CONFIRMED: incoming wire]` two client shoot requests occurred; `[HIGH CONFIDENCE]` one player/bot/next-round cycle was accepted sufficiently to unlock the second request; `[UNKNOWN]` visual correctness.
- Next: repeat with timestamped outgoing raw hex and video/screenshot evidence, then continue until `255/5` and evaluation.

## E-004 Complete v8 match and result

- Hypothesis: two more valid player turns reduce bot HP to zero; the last `255/2` followed after animation delay by `255/5` transitions to a result/evaluation flow.
- Changed: added lossless localhost frame tracing and ran the writable client through a complete local match.
- Expected: final hit/death animation, PVP end, result/evaluation, and return to hall without client exception.
- Observed: 309 frames, zero frame-length errors, four `3/3` requests, final `255/2`, delayed `255/5`, and return to lobby. The shot bodies alternated `0800`, `0801`, `0800`, `0801`, proving the client really requested both self and opponent targets. Visual/user observation rejected the result: self-shots struck the opponent and animation/turn synchronization was wrong.
- Root cause: `server.py` changed every target other than `1` into `1`; it also reused event id `1`, always marked `isNextRound`, wrote death state to field 18 instead of field 63, left `PvpInfo.round/turn/idx` stale, and sent the bot event without first changing the active gamer.
- Conclusion: `[CONFIRMED wire completion, REJECTED gameplay fidelity]`. Reaching `255/5` is not sufficient evidence of a playable reconstruction.

## E-005 Target, animation, and turn contract (v9)

- Hypothesis: preserving `GamerPvpShootC2S.idx` and matching the shipped Lua/protobuf animation fields will make self/opponent shots address the correct scene object and keep operator state synchronized.
- Changed: target `0/1` is preserved; `PvpEventResult` now emits self-shot ammo/count, unique event id, real `isNextRound`, and event time; `PvpEventOutline` emits `uTime`, `eventGamerStatus` field 63, `isPlayHitAnim` field 49, and hurt type field 73; `PvpInfo` updates round, turn, status, and current index; bot and player turns each receive `255/1` before action.
- Static result: `py_compile` passed and all 11 protocol tests passed. Tests decode self-shot as source `0`, target `0`, and opponent-shot as source `0`, target `1`.
- Live result: pending the active writable-copy run.
- Conclusion: `[CONFIRMED static contract / LIVE PENDING]`.
