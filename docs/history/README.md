# Hunter Roulette research index

This directory is the writable research notebook for the local preservation lab.

Source boundary:

- Original, read-only evidence: `<ORIGINAL_GAME_ROOT>`
- Writable laboratory: `<LAB_ROOT>`
- Prior derived artifacts, not original game files: `<LOCAL_USER_PATH>`

Evidence labels:

- `[CONFIRMED]`: directly supported by the current client, current logs, metadata, or a reproducible test.
- `[HIGH CONFIDENCE]`: multiple independent artifacts agree, but the exact runtime transition has not yet been captured end to end.
- `[HYPOTHESIS]`: plausible and testable.
- `[UNKNOWN]`: insufficient evidence.

Start with `CONFIRMED_FACTS.md`, `PROTOCOL.md`, `STATE_MACHINE.md`,
`DEV_FILES_FINDINGS.md`, `PERSISTENCE_PLAN.md`, and `UNKNOWNS.md`. Do not copy authentication
material, personal identifiers, SDK keys, or original service IP addresses
into this notebook.
