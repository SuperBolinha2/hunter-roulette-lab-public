# Confirmed facts

1. `[CONFIRMED]` Original installation is read-only evidence; the sibling `Hunter Roulette - Copia` is the writable lab.
2. `[CONFIRMED]` Both trees contained 1300 files and 3,519,042,360 bytes at baseline. All relative paths/sizes and critical hashes listed in `BASELINE.md` matched.
3. `[CONFIRMED]` Unity `2022.3.62f2`, Windows x64 IL2CPP, `GameAssembly.dll`, `UnityPlayer.dll`, and `global-metadata.dat` are present.
4. `[CONFIRMED]` The original has eleven game logs dated 2026-03-13 through 2026-05-04 and launcher/QAV logs.
5. `[CONFIRMED]` At least one historical game log records a real gameplay session: repeated `OnShootOver`, card events, scene exits/entries, and server-returned error codes appear in `outLog_26_03_14_03_30_16_1773459016.txt`.
6. `[CONFIRMED]` Hotfix/bootstrap uses `gcpnew-roulette.piliupd.com`; the launcher configuration uses `gcp-roulette.piliupd.com`; the packaged game-server address is a CloudFront hostname. Query strings and credentials are deliberately not copied here.
7. `[CONFIRMED]` AntNet message fields are `uint len`, `ushort error`, `byte cmd`, `byte act`, `ushort index`, `ushort flags`.
8. `[CONFIRMED]` AntNet defines flags for encryption, compression, continuation, acknowledgements, resend, and server direction.
9. `[CONFIRMED]` `GAME_CMD_PVP_ING = 3`; act `3` is shoot, act `4` is behavior, act `14` is scene-load completion, act `20` gets the PVP fd.
10. `[CONFIRMED]` `GAME_CMD_PVP_NOTIFY = 255`; act `1` is next round, act `2` is PVP event, act `3` is gamer status, act `4` is gamer behavior, act `5` is PVP end, act `7` is initial ammo, act `21` is start/recover AI.
11. `[CONFIRMED]` The clue `(255,3) Client -> Server` is inconsistent with the shipped command table. In this build, `255/3` is a server-to-client gamer-status notification. The shoot request is `3/3`; its authoritative result is normally `255/2`.
12. `[CONFIRMED]` The client sends `GamerPvpShootC2S.idx` and does not locally decide hit, HP loss, ammo result, death, or victory.
13. `[CONFIRMED]` After scene loading it sends `GamerPvpGamerLoadC2S` (`3/14`) and parses a separate `GamerPvpGamerLoadS2C` before marking all player info loaded.
14. `[CONFIRMED]` PVP heartbeat is `3/2`, sent immediately and then at approximately five-second intervals while the battle connection is active.
15. `[CONFIRMED]` Lua registers separate handlers for next round, PVP event, gamer behavior/status, PVP end, ammo initialization, and other presentation events.
16. `[CONFIRMED]` Bot-related protobufs/enums exist: `NotifyRobotPvp`, `NotifyPvpStartRobot`, `BasePvpGamerRobotInfo`, `PvpRobotBehavior`, and `PvpRobotStatus`.
17. `[CONFIRMED]` Bot behavior enum values include heart, shoot, skill, card, PVP login/TCP, next round, PVP event, PVP end, and error.
18. `[CONFIRMED]` `step = -1` has not been tied to the battle protocol. The only exact current Lua hits found were guide end sentinels in `novice_guild_step_cfg`.
19. `[CONFIRMED]` Bundled ammo configuration identifies cfg `1` as real ammo, cfg `2` as the enhanced two-damage round, cfg `300` as blank ammo, and cfg `301` as healing ammo; the prior local tests corrected an earlier inversion.
20. `[CONFIRMED: latest local trace]` When the player magazine reached real=0 and fake=0, repeated `3/3` shot requests received only acknowledgements while the turn stayed active. The copied client therefore froze because the emulator had no empty-magazine transition.
21. `[CONFIRMED]` A prior localhost emulator has eight passing static/unit protocol tests.
22. `[CONFIRMED: wire evidence]` In the 2026-09-13 localhost run, the client completed PVP login, sent `3/14`, received the initial-turn push, sent behavior packets and then two distinct `3/3` shoot requests. The emulator advanced player/bot HP and ammo after each request.
23. `[HIGH CONFIDENCE: inferred from client behavior]` The client accepted enough of the first `255/2 -> delayed bot 255/2 -> 255/1` sequence to enable and send a second shot 8.679 seconds later. The emulator code emits those frames in that order, but outgoing frames were not hex-logged and the screen was not recorded.
24. `[CONFIRMED]` The client log for that run ended at a `NullReferenceException` in `BackGroundCtrl.OnDestroy` during scene cleanup at 13:40:26. The TCP session nevertheless continued until 13:40:53 and carried both later shoot requests, so this exception alone is not the first-action transport blocker.
25. `[UNKNOWN]` A visually verified complete shot-to-win match, `255/5` end transition, and logic-side evaluation have not yet been demonstrated.
