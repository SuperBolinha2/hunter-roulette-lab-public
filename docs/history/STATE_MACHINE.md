# Client state machine

## Evidence-backed path

```text
BOOT
  -> HOTFIX_VERSION_CHECK
  -> SDK_LOGIN
  -> HTTP_SERVER_DISCOVERY
  -> LOGIC_TCP_CONNECT
  -> LOGIC_LOGIN (1/1)
  -> PLAYER_DATA (2/3 and related requests)
  -> HALL / LOBBY
  -> MATCH OR LOCAL-BOT START REQUEST
  -> START_PVP NOTIFY (253/3)
  -> PVP_TCP_CONNECT
  -> GET_PVP_FD (3/20)
  -> PVP_LOGIN (3/1)
  -> BATTLE_SCENE_LOAD
  -> GAMER_LOAD (3/14)
  -> INITIAL_AMMO (255/7)
  -> NEXT_ROUND (255/1)
  -> PLAYER/BOT BEHAVIOR (3/4 and 255/4)
  -> SHOOT REQUEST (3/3)
  -> RESOLVED EVENT: SHOOT + FINALLY_SOURCE (255/2)
  -> PREPARE BOT (255/1, status 3)
  -> ACTIVE BOT (255/1, status 2)
  -> BOT RESOLVED EVENT: SHOOT + FINALLY_SOURCE (255/2)
  -> PREPARE PLAYER (255/1, status 3)
  -> ACTIVE PLAYER (255/1, status 2), repeated
  -> PVP_END (255/5)
  -> RESULT/EVALUATION (logic notify 253/5)
  -> HALL
```

Confidence:

- Bootstrap through PVP login: `[CONFIRMED]` by Lua code and historical logs.
- `GamerLoad` as a distinct gate before active controls: `[CONFIRMED]` by `OnAllInfoLoadFinish`.
- Initial ammo and next-round notifications as required gameplay gates: `[CONFIRMED at wire/client-behavior level]`; after the prior emulator pushed the initial turn, the client sent two separate behavior/shoot sequences.
- One player action followed by a bot response and another player turn: `[CONFIRMED wire, v8 ordering rejected visually]`; v8 omitted the explicit bot `255/1` before the bot event. v9 models both operator transitions explicitly.
- Full end-to-end sequence through result: `[CONFIRMED wire only, gameplay fidelity rejected]`; v8 reached `255/5` and returned to lobby, but wrong targets and animations mean this is not a playable milestone.

## Concrete current bottleneck

Server v12 passes static and localhost integration validation for the exact
shot/turn packet order above. The first unverified transition is visual: the
ammo counter must decrement during `OnFire`, the bot must finish its shot, and
the player's controls must unlock on the following active-turn notification.
