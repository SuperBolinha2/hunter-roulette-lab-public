# Authentication

## Observed layers

1. Launcher/platform SDK obtains a user id and short-lived login token.
2. HTTP login/server discovery returns a logic-server address, port, session context, and encryption key material.
3. Logic TCP sends `GamerLoginC2S` with id, channel, version, session, device data, and `aiTyp`.
4. Match start supplies a PVP session/address.
5. PVP TCP asks for an fd (`3/20`) and then sends `GamerPvpLoginC2S` (`3/1`).

`[CONFIRMED]` Historical logs contain live tokens, IDs, device identifiers, friend data, and third-party SDK keys. They must remain local and must not be copied into reports or test fixtures.

## Minimal local-auth hypothesis

`[HIGH CONFIDENCE]` The preservation server does not need to reproduce platform authentication. It can assign a fixed local account, issue a synthetic local session, return localhost endpoints, and omit/disable encryption for the isolated path.

`[UNKNOWN]` The smallest HTTP response schema accepted by the current launcher/game boundary still needs a clean capture and one-variable-at-a-time reduction.

