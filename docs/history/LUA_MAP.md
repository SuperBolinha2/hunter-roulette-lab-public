# Lua and xLua map

## Source

- Original bundle: `Game\Client_Data\StreamingAssets\AssetBundles\PC\fight\LuaBundles\lua.ab`
- Prior extracted tree: `<LOCAL_USER_PATH>`
- Extracted file count: 840.

The extracted scripts are readable Lua stored with a `.bytes` suffix. They remain derived artifacts; the original bundle is the canonical source.

## High-value files

| File | Role |
|---|---|
| `net\lua%define.bytes` | complete main/sub-command constants |
| `net\lua%luaantnet.bytes` | HTTP discovery, logic TCP, logic login, encryption setup, reconnect |
| `net\lua%pvpluaantnet.bytes` | PVP TCP, fd, login, reconnect, send/callback dispatch |
| `net\lua%netheart.bytes` | logic heartbeat |
| `net\lua%pvpnetheart.bytes` | PVP heartbeat every ~5 seconds |
| `data\lua%gamer.bytes` | login/profile response handling |
| `umodel\roulettegame\lua%roulettegamemodule.bytes` | battle notifications and state application |
| `umodel\roulettegame\lua%roulettegameplayernameboard.bytes` | player HUD, stored-card icon and optional `arg_one` text |
| `umodel\roulettegame\lua%roulettegameplayer.bytes` | player state, card-slot updates and battle effects |
| `uclass\roulettegamewindow\lua%roulettebattlewindow.bytes` | input-to-request path, including shoot `3/3` |
| `config\lua%ammo_cfg.bytes` | ammo cfg and ordering |
| `config\lua%robot_hero_pool_cfg.bytes` | robot hero-pool configuration |
| `config\lua%pve_level_cfg.bytes` | PVE level definitions |
| `00other\system\common\pb\*.bytes` | Lua protobuf descriptors |

## Key observations

- `[CONFIRMED]` `SendPvpShootC2S` sends only the selected target index and locks input until the server callback returns.
- `[CONFIRMED]` `RouletteGameModule.StartGame` registers authoritative server notifications before gameplay.
- `[CONFIRMED]` `OnAllInfoLoadFinish` sends `3/14` and only then marks player information loaded.
- `[CONFIRMED]` PVP notification `255/7` is `NotifyPvpGamerAmmo`. Its Lua handler stores `gameInitInfo` and dispatches the battle window's `OnGameStart`; that window reads `gameInitInfo.pvpInfo.gamers` and calls `SetAmmo` for each loaded magazine. It is a distinct initialization gate, not interchangeable with the next-turn packet `255/1`.
- `[CONFIRMED]` `255/4` is the client behavior-notification path (`NotifyGamerPvpBehavior`). The Lua maps action 1 to `PortGun` (raise weapon), action 4 to `Chose` (aim at `tIdx`), and action 2 to `DropGun`. The local bot scheduler already queues raise/aim before its shot result; source proves intended animation routing, but only a live client can confirm those poses actually play.
- `[CONFIRMED]` A normal `Type_Shoot` event is queued by `StartShootOnce`; the scene animation's `OnFire` first calls `ShootAmmo(source.ammo.cfgId)` and then applies the event source/target outlines. The source outline's `rAmmo` is the complete post-shot magazine list and is sorted by each configured ammo `sortId`. `ammoBank` is a separate optional reserve pool; its actual mode-1 starting contents are not reconstructed.
- `[CONFIRMED]` `ammo_cfg` describes ammo cfg/type/order, and `PvpModeCfg` has no initial magazine counts. The local `2` blank + `4` real setup is an emulator choice, not a client-configured original rule. The old live trace only proves that this payload was sent in that test build.
- `[CONFIRMED]` `RouletteGamePlayer:UpdatePlayerInfo` discards an outline only when its `uTime` is older than the player's last applied update. For a shot, `OnFire` first decrements/animates the chosen cfg locally; the source outline then supplies authoritative full `rAmmo`. The captured old live shot has matching cfg, `rAmmo`, HP, and `PvpInfo`, with event times in order, so its wire values do not explain a persistent ammo mismatch.
- `[CONFIRMED]` `ammoBank` is PvpEventOutline field 23. On `Enum_Shoot`, `UpdatePlayerInfo` calls `OpAmmoBankData(data.ammoBank)`, which replaces `CurAmmoBank` and refreshes the reserve-ammo UI. The current emulator omits that field because its actual initial reserve is unknown; an absent repeated field parses as empty, so reserve UI is not yet faithfully modeled. This is distinct from the main magazine `rAmmo` display.
- `[CONFIRMED]` `RouletteGamePlayer:UpdatePlayerInfo` applies `rAmmo` via `SetAmmo` and passes `ammoBank` to `OpAmmoBankData` on `Enum_Shoot`. The HUD nameboard animates removals through `SetAmmos(popIndex)` and then refreshes the full stack list. These are the client-side points to compare against the reported momentary HUD reversal; a packet trace and screen result are still needed to decide whether its cause is ordering or values.
- `[CONFIRMED]` Lua updates scene/UI/animation from parsed PVP notifications.
- `[CONFIRMED]` Client `Card.arg_one` is the optional accumulated-coin argument, not a generic item quantity. `RouletteGamePlayerNameBoard:SetCardSlot` shows `_text_card_arg` when `arg_one >= 0`, and hides it when negative. Omitting this optional protobuf scalar makes the client read its default `0`, which displays a spurious zero on ordinary stored cards. Encode `arg_one=-1` for cards without a number; send a nonnegative value only when the card's mechanic uses it (for example, the Piggybank balance). The empty slot already uses `-1`.
- `[CONFIRMED]` The general card/prop-selection list also explicitly hides `_Txt_ItemCount`; ordinary cards do not have an inventory-count label in that view. Do not model a quantity merely because `Card.arg_one` exists.
- `[CONFIRMED]` Shop selection distinguishes `Typ_Buy_And_Use=1`, `Typ_Use=2` for a card already in the slot, and `Typ_Buy=3` to store the selected offer. These requests have separate effects and must not be conflated in the server handler.
- `[CONFIRMED]` Card targeting uses one shared UI path: `OnClickCardSlot`/`OnShopItemClick -> ShowCurSelectCardInfo -> IsCanUseItem -> OnUseBtnClick -> ShowCurSelectBtn`. `ShowCurSelectBtn` reads each card's skill `target_typ`/`target_num`, activates the common `_Btn_PlayerSelectN` controls, then enables `_obj_PlayerSelect`; card effects are dispatched separately by `ClientAnimExpression.UseCard` according to `skill_typ` (for example, Shoot, ChangeAmmo, and PopAmmo). A UI repair here should be generic; effect/event-result support remains item-specific.
- `[TRACE, NOT YET VERIFIED]` In `private-server/packet-trace-20260923-201910.jsonl`, the observed `3/4` behavior requests alternated selecting shop item ID 4 and canceling with `-1`; none reached a `3/5` use request. The associated published state had `player_card_cfg=0`, so that capture does not prove a stored-slot-use attempt.
- `[EXPERIMENT, PENDING VISUAL TEST]` Lab Lua bundle patch v3 hides `_obj_UseCard` while `IsCanUseItem` has entered the shared target-selection path, for both shop and stored items. It is installed only in `Hunter Roulette - Copia`; the new client session has not yet reached PVP, so arrows/click routing are not visually confirmed. Rollback and v1/v2/v3 bundles are under `research\private-server\rollback\2026-09-23-pre-item-target-ui`.
- `[CONFIRMED]` Coin display and carried-card display are separate client paths. `RouletteGamePlayer:SetCoin` calls `scene:UpdatePlayerCoin`; that method gates display through `IsShowPlayerCoin()` and then calls the native `SceneController:UpdatePlayerCoin`. A carried item instead travels through `SetCardSlot -> NameBoard:SetCardSlot -> scene:PlayerCardShow`. Thus a coin prop is not evidence of an equipped Piggybank. The native C# method bodies are unavailable in the IL2CPP stub dump, so the exact 3D asset/rendering remains unverified.
- `[CONFIRMED]` The current local `OnGameStart_New` Lua cadence is table ammo at t=0, ammo HUD at +1 s, `SetAmmo(..., true)`/reload at +4 s, `playerInit` at +6 s, and opening completion at +11 s. Server v15 delays the first `255/1` until +11 s, preventing the active turn from overlapping that opening. This server gate does not change the client's +4 s reload timer; the user still reports that reload begins somewhat early. Do not change it without a measured target interval or a reference capture.
- `[CONFIRMED]` Exact `step = -1` battle logic was not found; only guide-end sentinels currently match.

## Reproducible local source extracts

- `tools\extract_battle_lua.py` reads the copied install's `lua.ab` with UnityPy and extracts 15 selected TextAssets to `private-server\lua-extract\battle-contract`. It refuses changed-file overwrites; source bundles remain untouched.
