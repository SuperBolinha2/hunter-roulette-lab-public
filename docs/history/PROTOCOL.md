# Protocol map

## Envelope

| Offset | Size | Field | Status |
|---:|---:|---|---|
| `00` | 4 | `len` (`uint32`) | `[CONFIRMED: metadata]` |
| `04` | 2 | `error` (`uint16`) | `[CONFIRMED: metadata]` |
| `06` | 1 | `cmd` (`uint8`) | `[CONFIRMED: metadata]` |
| `07` | 1 | `act` (`uint8`) | `[CONFIRMED: metadata]` |
| `08` | 2 | `index` (`uint16`) | `[CONFIRMED: metadata]` |
| `10` | 2 | `flags` (`uint16`) | `[CONFIRMED: metadata]` |

`[HIGH CONFIDENCE]` The wire encoding is little-endian and `len` counts the protobuf body, not the 12-byte header. This is implemented by the prior local emulator and was sufficient for local TCP exchanges, but a new packet capture should make it fully current-session reproducible.

Flag bits from `MessageHead.Flags`: encrypt `1`, compress `2`, continue `4`, need-ack `8`, ack `16`, resend `32`, server `64`.

## Core command table

| Direction | Main ID | Sub ID | Name | Payload | Trigger | Confidence |
|---|---:|---:|---|---|---|---|
| C->S | 1 | 1 | Login by session | `GamerLoginC2S` | logic TCP established | CONFIRMED |
| C->S | 2 | 1 | Main heartbeat | server-time request | active logic session | CONFIRMED |
| C->S | 2 | 3 | Get login data | `GamerLoginGetDataC2S` | after base login | CONFIRMED |
| S->C | 253 | 3 | Start PVP | `NotifyGamerPvpStart` | match ready | CONFIRMED |
| C->S | 3 | 20 | Get PVP fd | `GamerPvpGetFdC2S` | PVP TCP connected | CONFIRMED |
| C->S | 3 | 1 | PVP login | `GamerPvpLoginC2S` | fd obtained | CONFIRMED |
| C->S | 3 | 2 | PVP heartbeat | `GamerPvpHeartC2S` | immediately, then ~5 s | CONFIRMED |
| C->S | 3 | 14 | Gamer loaded | `GamerPvpGamerLoadC2S` | battle scene/assets ready | CONFIRMED |
| S->C | 255 | 7 | Initial ammo | `NotifyPvpGamerAmmo` | battle initialization | CONFIRMED |
| S->C | 255 | 1 | Next round | `NotifyGamerPvpNextRound` | activate/advance turn | CONFIRMED |
| C->S | 3 | 4 | Gamer behavior | `GamerPvpBehaviorC2S` | raise/drop gun, choose target/card/item | CONFIRMED |
| S->C | 255 | 4 | Gamer behavior | `NotifyGamerPvpBehavior` | authoritative presentation | CONFIRMED |
| C->S | 3 | 3 | Shoot | `GamerPvpShootC2S { idx }` | click shoot | CONFIRMED |
| S->C | 255 | 2 | PVP event | `NotifyGamerPvpEvent` | resolved shot/card/round event | CONFIRMED |
| S->C | 255 | 3 | Gamer status | `NotifyGamerPvpStatus` | HP/status update | CONFIRMED |
| S->C | 255 | 5 | PVP end | `NotifyPvpEnd` | match finished | CONFIRMED |
| S->C | 253 | 5 | PVP evaluation | `NotifyGamerPvpEval` | post-match result on logic link | CONFIRMED |

## Serialization and protection

- `[CONFIRMED]` Bodies are protobuf, generated in C# and Lua.
- `[CONFIRMED]` Logic-server discovery is JSON over HTTP(S).
- `[CONFIRMED]` A server-provided `enpkey` is sent to `EncryptUtil`; login/reconnect commands are explicitly excluded from outbound encryption.
- `[HIGH CONFIDENCE]` A local server can disable payload encryption by returning no effective key and keeping flag `1` clear.
- `[UNKNOWN]` Exact cipher mode, IV derivation, compression threshold, and whether PVP uses the same key policy still require disassembly or capture.

