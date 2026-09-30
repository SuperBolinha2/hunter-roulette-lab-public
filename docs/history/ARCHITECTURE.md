# Architecture

## Current model

```text
RLLauncher / SDK login
        |
        | HTTP(S): bootstrap, patch metadata, server discovery/login
        v
Unity 2022.3.62f2 IL2CPP client
        |
        | AntNet TCP + 12-byte envelope + protobuf payload
        v
Logic server (profile, lobby, inventory, matchmaking)
        |
        | NotifyGamerPvpStart supplies PVP endpoint/session
        v
PVP server (authoritative turn, ammo, HP, events, result)
        |
        v
xLua handlers -> C#/Unity scene, UI, animation, audio
```

## Findings

- `[CONFIRMED]` Unity version is `2022.3.62f2`, present in `globalgamemanagers` and every sampled UnityFS bundle header.
- `[CONFIRMED]` This is an IL2CPP build: `GameAssembly.dll` plus `Client_Data\il2cpp_data\Metadata\global-metadata.dat` are present. The metadata file is 18,262,792 bytes and the prior dump identified metadata version 31.
- `[CONFIRMED]` xLua is integrated. The IL2CPP dump contains `XLua.CSObjectWrap.*`, `DelegateBridge`, and Lua/C# bridge classes. `PC\fight\LuaBundles\lua.ab` contains the Lua layer.
- `[CONFIRMED]` There are 88 `.ab` files. Sampled headers are `UnityFS`, format marker `5.x.x`, engine `2022.3.62f2`.
- `[CONFIRMED]` The client ships `protobuf-net` generated types and Lua protobuf descriptors. Gameplay payloads are protobuf inside a custom AntNet TCP envelope.
- `[CONFIRMED]` Two TCP roles are explicit in Lua: the logic connection (`LuaAntNet`) and the battle connection (`PvpLuaAntNet`).
- `[CONFIRMED]` HTTP/JSON is used before TCP: `ConnectLoginSvc` decodes JSON containing a server address, port, and encryption key.
- `[CONFIRMED]` `UnityWebSocket.Runtime.dll` is shipped.
- `[UNKNOWN]` No current evidence shows WebSocket is used on the critical login-to-bot-match path. Presence of the assembly alone is not use.
- `[CONFIRMED]` No standalone `.pem`, `.crt`, `.cer`, `.pfx`, `.p12`, `.key`, JKS, or keystore file was found. TLS/OpenSSL/Chromium binaries embed trust and crypto support.
- `[CONFIRMED]` Voice-room calls use the platform SDK/GME layer, but voice is not required for the first local bot milestone.

## Authority boundary

`[HIGH CONFIDENCE]` The server is authoritative for core roulette resolution. The client sends intent (`shoot target idx`, behavior, card use), then waits for server notifications carrying the next round, PVP event result, player status, ammo, and end state. Client code performs presentation and local state application after those messages.

