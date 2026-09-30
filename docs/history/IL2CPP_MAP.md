# IL2CPP map

## Canonical binaries

- `Game\GameAssembly.dll` — 65,385,936 bytes.
- `Game\Client_Data\il2cpp_data\Metadata\global-metadata.dat` — 18,262,792 bytes.

## Prior dump

Generated with Il2CppDumper 6.7.46 under:

`<LOCAL_USER_PATH>`

Artifacts: `dump.cs`, `il2cpp.h`, `script.json`, `stringliteral.json`, and dummy assemblies. Critical current hashes match the snapshot used for that dump, so the derived symbols are applicable to this baseline.

## Important types

| Type | Role |
|---|---|
| `NetDefine.GameServerConfig` | CDN/bootstrap configuration |
| `AntNet.MessageHead` | 12-byte frame header |
| `AntNet.SendData` / `RecvData` | frame body wrappers |
| `AntNet.NetObject` / `TcpObject_New` | callback routing and TCP transport |
| `AntNet.EncryptUtil` | server-keyed payload encryption and exclusions |
| `ProtoBufSerializer` | protobuf serialization bridge |
| `GamerLogin*` | logic login/profile |
| `GamerPvp*` | PVP requests/responses |
| `NotifyGamerPvp*`, `NotifyPvp*` | server notifications |
| `NotifyRobotPvp`, `PvpRobotBehavior`, `PvpRobotStatus` | robot orchestration protocol |

## Limits

`dump.cs` recovers signatures, fields, protobuf attributes, and RVAs, not original method bodies. Native disassembly or runtime tracing is needed for exact encryption/compression code and any logic not present in Lua.

