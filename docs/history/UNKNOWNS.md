# Unknowns and next questions

## Immediate blockers

1. `[UNKNOWN]` What the prior two-shot localhost sequence rendered on screen; no synchronized visual capture exists.
2. `[UNKNOWN]` Exact first missing/invalid packet or field after the second shot and before a completed `255/5`/result transition.
3. `[UNKNOWN]` Exact minimum `NotifyGamerPvpEvent` field set accepted for a real and blank shot in every target/self combination.
4. `[UNKNOWN]` Exact ordering/timing among event, status, next-round, death, PVP-end, and logic evaluation notifications.
5. `[UNKNOWN]` Whether `255/21 NotifyPvpStartRobot` is required for the original bot presentation or only for recovering a server-side robot worker.

## Protocol details

- Exact encryption cipher/mode, IV, padding, and key activation behavior.
- Compression algorithm/threshold behind flag `2`.
- Ack/retry behavior needed under localhost packet loss (probably unnecessary initially).
- Official packet length semantics should be confirmed by a capture even though the prior emulator strongly supports body length.

## Assets and modes

- Which shipped modes still have all required local assets.
- Which mode is the simplest bot-capable path with the smallest server state.
- Whether `Clash_PVE`, classic solo/bot, tutorial, or another mode minimizes required profile systems.

## Logs

- Correlate exact historical scene windows with QAV/launcher timestamps.
- Build a safe redacted event extractor rather than manually reading raw sensitive lines.
- Determine why the client log stopped at `BackGroundCtrl.OnDestroy` while TCP gameplay traffic continued for roughly 27 seconds.
