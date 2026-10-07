# Match introduction — native client compatibility

The local owner confirmed cinematic to participant-panel handoff on2026-09-30.
The backend preloads the panel, but a compatible client callback is also needed.
Backend sources alone do not prepare an unmodified Steam client.

This public repository intentionally excludes the optional native-client patch
helper and all bundles/binaries/extracted Lua. The helper remains in the private
archive for separate distribution review. No game assets are provided here.
Do not disable compatibility/hash safeguards or overwrite the original client.

Use a legitimately obtained compatible isolated copy; otherwise backend tests
can run without visual gameplay. A clean-client installer remains future work.
See historical research in [PLAYER_INTRO_TEST.md](history/PLAYER_INTRO_TEST.md).
