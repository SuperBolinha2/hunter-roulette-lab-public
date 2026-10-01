# Match introduction — local validation complete

The owner confirmed a continuous opening with two characters on 2026-09-30.
286 backend tests pass. The Exit-state regression has protocol coverage;
clicking Exit after the correction was not separately confirmed by the owner.

The server triggers the native cinematic and preloads the participant panel.
The patched client waits for OnCutSceneFinish(-1), then shows that panel in
the same UI frame. Skill cinematics retain their original executor. The server
restores isStartPvp after introduction so the native Quit button can appear.

**Both backend and client changes are required.** Sync-Lab copies only server
sources. This helper does not prepare a clean Steam client. No game assets,
bundles or binaries are distributed here.

## Apply to an already compatible isolated copy

Close game and backend. The helper accepts only the pre-patch lua.ab hash:
`4A7AB2417E4E2E9299CE80C5E5F0E99B80CC8556850567D3F5DAC9D5755DB672`.
On a mismatch, coordinate with the owner; never disable this safeguard.
Already patched clients do not need to apply it again.

Only this optional helper needs UnityPy; backend tests do not. The laboratory
used version 1.25.3. Use a separate environment in the repository folder:

```powershell
python -m venv .local/intro-patcher
.local/intro-patcher/Scripts/python.exe -m pip install UnityPy==1.25.3
.local/intro-patcher/Scripts/python.exe tools/patch_match_intro_handoff.py --game-copy-root 'D:\Games\Hunter Roulette Lab'
```

The last command builds a preview and checks that all other TextAssets are
unchanged. After successful preview, install with the game still closed:

```powershell
.local/intro-patcher/Scripts/python.exe tools/patch_match_intro_handoff.py --game-copy-root 'D:\Games\Hunter Roulette Lab' --install
```

It preserves a rollback under the copied game's
`research/rollback/20260930-native-intro-handoff/lua-before-handoff.ab`.
To roll back, close game/backend and restore that backup to the same copied
client's `Game/Client_Data/StreamingAssets/AssetBundles/PC/fight/LuaBundles/lua.ab`.
Never restore into the original installation.

Restart the updated backend and compatible client. Check cinematic -> panel
-> ammo preparation -> turn, then Quit. Other modes/client revisions still
require their own validation. See [research evidence](history/PLAYER_INTRO_TEST.md).
