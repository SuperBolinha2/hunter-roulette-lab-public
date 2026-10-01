# Current status — backend v63, 2026-09-30

286 local standard-library tests passed in the laboratory before this export.
Source-copy/CI validation must also pass before publication. Local three-seat
shop gameplay is manually playable; not all modes/features are complete.

For navigation and per-feature progress, use the [game checklist](FEATURE_CHECKLIST.md).
The [technical catalog](FEATURE_CATALOG.md) inventories native references,
not supported-feature claims. Keep completion status in the checklist and link
specific evidence; do not treat a visible screen or generic ACK as a working system.

Recent validation: Arthur duel, Shelby HP/chips trades, Annie own blank-to-red
and enemy blank-to-live substitutions. Katie robot presentation corrected via
native Buff.existTyp3 on impact and2 on expiry; blanks preserve protection.
Rocket protection and Grazier/Arthur duel protection have automated coverage;
their exact recent visual interactions still need targeted manual confirmation.

Remaining work includes additional improved hero skills (Diana/Vera/Hawke),
team-mode targeting, pre-match items, exact weapon reload mixtures, some
reload/death-camera timing, Enhance Hero purchase/progression and a clean
new-player account/tutorial. Existing lab GM progress is intentionally preserved.

Historical notes preserve partial investigations and earlier versions; latest
sections supersede earlier claims. Never infer that an item/skill passing one
manual test is correct in every mode or combination.

## Portability limitations

The native match opening was confirmed with two characters in the local lab.
It requires a client-side callback patch as well as the backend changes.
See [match introduction setup and limitations](MATCH_INTRO.md).

Backend and tests are portable. A compatible modified client is needed for
visual gameplay. Client binaries/assets, original Lua dumps and historical
patch scripts are intentionally not exported. An audited clean-client patch
installer remains separate future work. Start-Server does not create it.

Example inventory is synthetic, minimal, tutorial-skipped for protocol tests;
it is not a tested natural first-time progression profile.
