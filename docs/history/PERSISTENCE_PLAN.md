# Persistence and ownership reconstruction

This document tracks the server-side state that must survive reconnects and
server restarts. It is deliberately separate from battle synchronization.

Evidence labels follow `README.md`.

## Confirmed present behavior

- `[CONFIRMED]` `inventory.json` is loaded once when the local server starts.
- `[CONFIRMED]` saves are atomic at the file level: the server writes
  `inventory.json.tmp` and then replaces `inventory.json`.
- `[CONFIRMED]` every implemented inventory transaction calls that save
  routine after the in-memory mutation; the earlier three-only limitation was
  from the pre-inventory foundation build.
- `[CONFIRMED]` shop refresh (`22/2`) received three empty responses in the
  latest trace. The shipped schema expects shop records, purchase limits,
  unlocked items, and random items.
- `[CONFIRMED]` the current profile intentionally has no temporary home box or
  home key; it does have explicit exploration-pack/cell state and item stacks.
- `[CONFIRMED]` `23/1` accepts any positive fashion id without checking that
  the item is owned or compatible with the selected hero/gun.
- `[CONFIRMED]` the login serializer sends `GamerHome` but omits its repeated
  `boxes` field (field 6) and `temporaryBoxId` (field 7).
- `[CONFIRMED]` shipped Lua treats a missing `TreasureBox` entry, or one with
  `status = 0`, as a locked slot. It treats `status = 1` as unlocked and
  `boxId = -1` as an unlocked but empty slot. This directly explains the
  visible `Bloqueado`/zero supply-box state.

Therefore the observed symptom is not evidence of an intermittent disk-write
failure. Most affected commands do not yet have a state mutation or a real
response to save.

## Command/state matrix

| Feature | Client command | Current result | Required persistence |
|---|---:|---|---|
| Select prepared hero | `10/2` | saved | keep and validate against owned heroes |
| Equip fashion | `23/1` | saved incompletely | ownership, target/type compatibility, equipped slot |
| Refresh fashion data | `23/2` | empty | serialize owned/equipped fashion state |
| Carry hero gun | `24/1` | saved | keep and validate compatibility |
| Gun armory info/operation | `25/1`, `25/2` | empty | armory level/progress/unlocks |
| Get all shops | `22/2` | empty | shop records, unlocks, limits, random slots |
| Buy market item | `22/1` | not implemented | currency cost, acquired item, purchase limit |
| Home treasure boxes | `13/1`-`13/5` | implemented | slots, locks, timers, temporary box, costs, awards |
| Explore boxes | `32/1`-`32/6` | implemented | owned/opened cells and awarded items |
| Cards/items/rewards | several | partial | decoded balances, ownership and known transactions |

The report that a selected character item does not appear has two distinct
candidate paths that must not be conflated:

- `[CONFIRMED]` the latest trace contains character/card selection `12/2`, but
  the local server returns an empty response and does not persist `readyCard`.
- `[CONFIRMED]` fashion refresh `23/2` is also unimplemented. Fashion equip
  `23/1` does save and sends the correct `253/18` refresh notification, and all
  66 fashions currently exposed by the lab exist in `fashion_cfg_steam`.
- `[CONFIRMED]` the three presently equipped fashion records match their
  shipped target ids and types. A specific failed selection must therefore be
  classified from its command (`12/2` versus `23/1`) in a fresh trace before
  changing the wrong subsystem.

## Canonical state to reconstruct

The lab will keep one canonical state document, versioned for migrations:

- currencies and stackable items;
- owned heroes, guns, fashions and cards;
- selected hero, hero-to-gun loadout, equipped fashions and gun armory;
- shop rotations, unlocked entries and per-item purchase limits;
- home treasure-box slots, lock/open timers and pending awards;
- explore-box state and pending awards;
- a monotonically increasing state revision and schema version.

The shipped `TreasureBox` wire layout is also confirmed:

| Field | Meaning |
|---:|---|
| 1 | slot index (1-3) |
| 2 | permanent opening-speed factor |
| 3 | temporary opening-speed factor |
| 4 | configured box id; `-1` means empty |
| 5 | opening start time |
| 6 | repeated temporary time reductions |
| 7 | slot status; 0 locked, 1 unlocked |
| 8 | repeated timed speed records |

The Steam bundle contains 23 shop definitions, 482 shop-item definitions, 25
supply-box definitions, and 49 supply-box award rows. These are sufficient to
reconstruct real ids, prices, timers, and weighted awards without fabricating
them. What remains unknown is the historical account's exact slot unlock and
owned-box state; no preserved log containing those values has been found.

Every mutating command must follow the same transaction boundary:

1. Decode and validate the request against shipped configuration tables.
2. Apply the complete state change in memory.
3. Save the new state atomically.
4. Return the exact command response.
5. Send the corresponding refresh notification, when the shipped client
   contract requires one.

On login and reconnect, the server must serialize the same canonical state;
otherwise a successful save can still appear to have been lost in the UI.

## Evidence-first implementation order

1. Decode remaining Steam variants of `item_shop_main`, `item_shop_base`,
   `fashion_cfg`, `gun_cfg`, and referenced item tables from
   `fight_dbconfig.ab`.
2. Recover any still-unknown request/response fields from shipped protobuf
   annotations and Lua call sites.
3. Add schema versioning plus a rollback copy of the current lab inventory.
4. Implement shop refresh (`22/2`) before expanding purchase (`22/1`), so the
   client can display authoritative unlock and quantity data.
5. Resolve the internal weighted package tables for `701067`/`701068` and the
   old `701024..701047` character packages. The historical chain is now
   implemented from the decoded Steam rows; newer `701077+` selector variants
   remain explicitly unsupported until their server-side rule is observed.
6. Tighten armory validation and ensure login, refresh and battle appearance
   consume the same equipped state.

## Acceptance tests

- Buy three boxes, restart the server, reconnect, and observe the same count.
- Unlock a supply-crate entry, restart, and observe it unlocked with its count.
- Equip a compatible character item, reconnect and enter battle; lobby and
  battle must render the same item.
- Reject an unowned or incompatible fashion without modifying the state file.
- Reject a malformed purchase without deducting currency or granting an item.
- Interrupt a save before replace and verify that the previous JSON remains
  readable.
- Confirm that login snapshot, explicit refresh response, and push notification
  expose the same state revision.

No item id, price, unlock rule, loot table, or timer will be invented. Unknown
fields remain unknown until supported by the shipped configuration or an
observed client request.
