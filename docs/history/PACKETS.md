# Packet payload notes

This file records protobuf field-level facts. It does not reproduce personal session material.

## Login

- `GamerLoginC2S`: field 1 `id`, 2 `channel`, 3 `version`, 4 `session`, 5 `simulator`, 6 `deviceId`, 7 `aiTyp`, followed by OS/device fields.
- `GamerLoginS2C`: field 1 `main` (`Gamer`), field 2 `home`.
- `GamerLoginGetDataS2C`: time, inventory, heroes, cards, guild/guide state, home, season, fashions, guns, and other optional profile systems.

## PVP bootstrap

- `GamerPvpGetFdC2S`: includes gamer id and PVP session.
- `GamerPvpLoginC2S`: includes gamer id, PVP session, and device id.
- `GamerPvpLoginS2C`: returns the battle/player snapshot consumed before scene setup.
- `GamerPvpGamerLoadC2S`: sent only after local scene information finishes loading.
- `GamerPvpGamerLoadS2C`: supplies the fresh `PvpInfo` used immediately before the loaded event is dispatched.

## Turn and action

- `NotifyGamerPvpNextRound`: current gamer, round number, `PvpInfo`, server time, reconnect marker, and standby timing.
- `GamerPvpBehaviorC2S`: behavior/action plus target/card/interact arguments.
- `GamerPvpShootC2S`: field `idx` is the selected target server index.
- In the two-player local room, index `0` is the local player and index `1` is the bot. A self-shot must therefore keep `source.Idx == target.Idx == 0`; rewriting `0` to `1` selects the opponent animation and scene object.
- `NotifyGamerPvpEvent`: resolved event plus updated `PvpInfo`, time, and AI-stop state.
- `PvpEventOutline.hp` is applied as a delta by Lua, not treated as an absolute HP value.
- Ammo changes include selected/current ammo and a post-event ammo list; cfg `1` is real, cfg `300` is blank.
- `PvpEventResult.ammos` (field 7) carries self-shot ammo cfg ids; `shootSelfNum` is field 9; target index is field 10; unique event id is field 13; turn-change marker is field 14; match-end marker is field 16.
- `PvpEventOutline.uTime` is field 28; `isPlayHitAnim` is field 49; `eventGamerStatus` is field 63; `targetDead` is field 68; `gamerHurtTyp` is field 73.
- `eventGamerStatus` is not `gamerStatus`: field 18 is a final-event player-status value. `RouletteGameModule.GetPlayerState` reads the outer `PvpEventResult.source` / `targets` entries, which are `PvpGamer` snapshots; their `eventGamerStatus` is field 26. Field 63 is the separate `PvpEventOutline.eventGamerStatus` and does not populate that lookup.
- `PvpEventOutline.cAmmo` (field 11) is annotated as an ammo-type change. Ordinary shot consumption is performed by `ShootAmmo` from field 10 and reconciled by the full `rAmmo` list in field 5.
- A normal shot result contains both `Enum_Shoot` (type 2) and `Enum_Finally_Source` (type 3). The latter carries `gamerStatus` and is applied by the client from `OnFire`.
- `PvpInfo.round`, `turn`, `status`, and current gamer `idx` are fields 4, 8, 9, and 10. They must be updated in snapshots delivered with turn changes.

## Bot-related payloads

- `NotifyRobotPvp`: match info, repeated robot gamers, start info, PVP server id.
- `NotifyPvpStartRobot`: `start` and `useTime`.
- `BasePvpGamerRobotInfo`: `robotHeroPoolId`.

## Raw captures

`[UNKNOWN]` No preserved raw official-server packet capture has been located. Localhost traces are evidence of client expectations and emulator behavior, not proof that the emulated payload exactly matches the unavailable official server. The v12 integration trace confirms its own two-event shot, prepare/active transitions, and consistent round values.
