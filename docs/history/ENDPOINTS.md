# Endpoints and redirection

## Confirmed host roles

| Host | Observed role | Source | Confidence |
|---|---|---|---|
| `gcp-roulette.piliupd.com` | launcher client resources and server-list base | launcher `PatcherConfig.json` | CONFIRMED |
| `gcpnew-roulette.piliupd.com` | game hotfix metadata and notice | game logs and `PkgVersion.json` | CONFIRMED |
| `dsnkrnlkttaao.cloudfront.net` | packaged game-server/bootstrap address | `PkgVersion.json` and logs | CONFIRMED |
| `<private IPv4>:9005` | packaged async log/upload target | `PkgVersion.json` and logs | CONFIRMED, address redacted |

Other SDK, voice, analytics, translation, certificate, and generic library URLs exist. They are not yet proven necessary for the minimal offline path and should not be contacted by the lab.

## Transport

- `[CONFIRMED]` HTTPS is used for patch/bootstrap metadata.
- `[CONFIRMED]` HTTP is supported for ancillary API/upload operations.
- `[CONFIRMED]` Gameplay uses raw TCP through AntNet.
- `[UNKNOWN]` UDP may be used by voice/acceleration SDKs, but is not required for M0-M9.
- `[UNKNOWN]` WebSocket is shipped but not proven in the core path.

## Local redirection plan

Preferred order:

1. Patch only the writable copy's URL/configuration inputs.
2. Return local JSON that advertises `127.0.0.1` for logic and PVP.
3. Keep all lab listeners bound to `127.0.0.1`.
4. Avoid system-wide hosts/DNS changes unless a hardcoded hostname cannot be redirected inside the lab copy.

Prior lab ports were HTTP `38000`, logic TCP `38001`, and PVP TCP `38002`. These are local choices, not recovered official ports.

