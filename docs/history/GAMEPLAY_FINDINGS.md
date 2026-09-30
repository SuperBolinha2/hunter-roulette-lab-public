# Gameplay findings and local fixes

This document records observed behavior and the compatibility rules implemented
in the isolated local server. The original Steam installation is kept untouched.

## Burst Mode consumed by a self-shot

- The 2026-09-27 session log shows Burst Mode cfg 2016 / skill 1015 applied to
  the local player (`target=0`, server log line at 01:23:08). The next observed
  self-shot was a blank round and the server correctly continued the player's
  turn. The bug was in Burst bookkeeping: the shot path only considered Burst
  active when the target was someone else, so a self-shot neither fired a
  second bullet (correct) nor consumed the buff / HUD icon (incorrect).
- v29 makes these independent decisions in all four PVP firing paths: consume
  any pending Burst buff on the shooter's next firing action, but create the
  second shot only when targeting another fighter. A blank self-shot can still
  continue the turn under the separate self-shot rule; subsequent actions no
  longer inherit the expired Burst effect.
- The server log now records `PVP Burst Mode consumed shooter=... target=...
  double_shot=...`. Unit and trio TCP regression tests verify that a self-shot
  emits one bullet and removes buff cfg 1015, while an opponent target remains
  eligible for a two-shot sequence. In the player's retest, the log recorded
  self-target consumption at 01:40:34 (`double_shot=False`) and a bot-target
  shot at 01:41:54 (`double_shot=True`); the player marked the result correct.

## Fake-ammo elimination animation

- The bundled Lua marks a player dead separately from playing their death
  animation. The `Enum_Gamer_Dead` event updates the dead/grayscale state.
- `Enum_Update_Gamer_Dead_Status` is event type `76`; the client handles it by
  playing `PlayerAnimEnum.KillByOther` for that fighter.
- Firing fake ammo at an opponent removes one Frenzy point from the **shooter**,
  not the target. If that is the shooter's last Frenzy point while HP is already
  zero, the shooter is eliminated.
- v26 incorrectly attached type 76 to the target when a target died. v27 now
  attaches it to the shooter and stops a Burst Mode sequence on that lethal
  shot. Regression coverage verifies the event index and a local three-player
  TCP exchange. The copied client's type-76 handler now calls both
  `PlayPlayerAnimator` and `PlayChairAnimator` with `KillByOther`; the original
  Steam installation is not patched. A pre-patch Lua bundle backup is kept at
  `research/private-server/rollback/2026-09-26-pre-death-chair-animation/`.
  The resulting chair-lock/shock sequence still needs visual confirmation.
- The same type-76 handler had no camera call, so the local death animation
  could play while the view remained in first person. The first camera patch
  also passed raw **clip** names to `SinglePlayCameraAnim`, which expects an
  **Animator state**. Both shipped camera controllers have a `CameraSelfDie`
  state: the main controller binds it to `CameraSelfDie_PushRotation`, and the
  child controller binds it to `CameraSelfDie_Position` (both 4 seconds).
  The copied client now calls `SinglePlayCameraAnim("CameraSelfDie")` once for
  the local player's type-76 event. The old 4-second reset was removed; it
  could restore first person during a terminal death. Bundle round-trip
  verification passed. In the latest playtest the player reported that the
  camera is better, but still missing elements. **Not finalized; leave this as
  a future improvement.** The exact remaining camera/framing details still
  need to be identified in a later test.
  The previous and corrected bundle versions are backed up under
  `research/private-server/rollback/2026-09-26-pre-frenzy-death-camera/` and
  `research/private-server/rollback/2026-09-26-pre-camera-state-fix/`.
- The player remembers the chair/electric-shock death interrupting the blank
  firing animation. The local protocol currently emits the blank-shot event
  followed by a separate type-76 death-status event; whether the visible
  interruption matches the original needs observation.
- The camera/death sequence remains open work: verify third-person framing,
  chair/shock timing, and whether the shock interrupts the blank-shot animation
  as remembered. Do not mark the camera fix complete based only on the current
  improvement report.

## Wet cigarette at zero HP

- Player testing/recollection establishes that the original cigarette cannot
  restore HP once the heart row has disappeared at 0 HP, even while Frenzy
  keeps the fighter alive.
- Local rule: rolls `4-6` may restore one heart only when current HP is above
  zero and below the four-heart cap. At 0 HP, healing is always `0`.
- Unit regression coverage includes 0 HP with remaining Frenzy and a valid
  healing roll. The local item action may still resolve/consume as before; the
  key compatibility rule is that it cannot restore a heart from 0 HP.

## Maintenance Kit self-shot damage and spectator pacing

- The user observed that a real self-shot after activating the +1 damage
  upgrade took only one HP. Normal cfg-1 shots now receive the Maintenance
  Kit's extra damage even when the target is the shooter; blank ammo remains
  zero-damage and Arms Voucher cfg-2 remains separate.
- The prior match trace recorded 102 queued frames between local-player
  elimination and `PVP_END` (about 2m44s), because the two surviving bots
  completed their match at the normal 5s turn-settle / 3s think cadence. After
  the local player is eliminated, bot-vs-bot timing now uses 3s settle and 1.5s
  total think time, preserving each action while shortening idle waits. The
  final result no longer adds a separate 2.5s spectator-only pause; the client
  still controls the final animation/result timer.
- Static tests cover +1 self-shot damage, shooter-side fake-ammo elimination,
  and spectator timing. Manual confirmation remains necessary for the two-HP
  HUD change, chair/shock animation, and perceived time to the Loser screen.

## Hallucinogen self-target and automatic reload

- The 2026-09-27 trace identified the exact item as cfg 2025 / skill 1023,
  offer 40. It forced Bot 1 to fire its last real round (real ammo 1→0, HP
  4→3), left fake rounds in the HUD, and omitted any reload event. This was a
  server-side event omission, not a bullet-type substitution.
- `_resolve_hallucinogen_self_shot` now saves the immediate post-shot counts,
  reloads the selected survivor if real ammo reaches zero, and appends the
  existing `Enum_Reload` event after `Enum_Shoot`. The PVP snapshot carries the
  reloaded magazine. This applies to both cfg 2008 and 2025 and to either shop
  or stored-item use. It does not reload after an elimination or match end.
- Normal PVP shot handlers now also reload when no real rounds remain,
  regardless of whether the last consumed round was real or fake. A false
  self-shot still retains the player's turn; the immediate reload is embedded
  in that shot result so no extra operator-transition event resets aim.
- In the original copied config, skill 1023 has `target_typ=2`, so the client
  correctly hid the local player's arrow under its shipped rules. The local
  Lua patch deliberately adds the living main player as a selectable target
  for skill 1023 only; all other opponent-only items retain their old rule.
  The prompt text still says “enemy.” This is a lab override, not evidence that
  the original online mode allowed self-targeting for this variant.
- Validation: the full 99-test protocol suite passes, including the forced
  shot/reload event ordering, all-fake magazine reload, and next-shot readiness.
  The Lua asset round-tripped through UnityPy, the exact expected source hash
  was checked, and an exact pre-patch copy was backed up before installing into
  `Hunter Roulette - Copia`. The player then reported the Hallucinogen and
  reload behavior functional. The server log records cfg 2008 targeting the
  local player and cfg 2025 targeting Bot 1; after cfg 2025 forced a real shot,
  the server logged a reload to 1 real + 3 fake and the outgoing PVP snapshot
  retained those counts.
- Remaining visual issue: the player says the reload behavior works but the
  weapon's reload animation still looks somewhat wrong. Track this as a
  not-finalized weapon-animation item for the future weapon stage, alongside
  per-weapon magazine capacity/composition. Do not reopen the Hallucinogen
  functional status based on that animation-only discrepancy.
- The number/type mix on each replacement magazine still uses the lab's
  estimated per-weapon table; do not treat it as recovered original RNG.

## Wanted (cfg 2021 / skill 1020) — bounty lifecycle

- The copied `fight_languagedb.ab` English description says Wanted marks one
  player for one round: the first player to deal gunshot damage to that target
  gains 4 R-Chips; otherwise the marked player gains 4 R-Chips.
- The copied `fight_dbconfig.ab` links card 2021 to skill 1020. Buff 1020 is a
  hidden one-round control buff and links to visible buff 5002; buff 5002 uses
  `UI_Fight_bufficon_reward` and `Offer_Reward` logic 18 with amount 4. The
  protocol's `Coin_By_Offer_Award` reason is 7.
- The old local path only accumulated an unused 300-chip counter and sent the
  card cfgId as a buff, so it neither displayed nor paid the real bounty.
  The current lab server now adds buffs 1020+5002, pays +4 to the first
  damaging gunshot attacker and removes both buffs, or pays +4 to the living
  marked player when that application's turn budget expires if unclaimed.
  Shop and stored-card use share the corrected effect; duplicate marking is
  rejected while the bounty is live.
- Automated protocol/TCP regression tests cover the visible marker, claim
  payout, and marker removal. The three-player TCP test marks both the player
  and Bot 1 during one turn, shoots Bot 2 and lets the bots fire blanks. Both
  marks count 3→2→1 and expire at the third actual turn transition, not when
  Bot 1 first acts. Both recipients gain +4 exactly once. Another TCP test
  confirms repeated blank self-shots leave the counter at 3. This is
  server/protocol verification, not visual-client confirmation.
- In the player's test on 2026-09-27, Wanted was applied to both the player and
  Bot 1. The log recorded the player's real hit claiming Bot 1's bounty and the
  bot's return shot claiming the player's bounty, each for +4. The player later
  confirmed the shot correctly removes Wanted; the remaining question was
  duration when no real damaging shot lands. That earlier trace had no unclaimed
  expiry because both marks were claimed.
- The client source explains the visual failure: `RouletteGamePlayer:AddBuff`
  rejects a buff when another has the same `Buff.id`, and `RemoveBuff` searches
  by that same `id`. `_pvp_buff` had assigned `id=1` to every cfg, so Wanted's
  hidden control buff 1020 and visible marker 5002 collided (as could other
  local buffs). The builder now assigns a stable synthetic id `1,000,000 +
  cfgId` unless an explicit instance id is supplied. Add and remove events use
  the same ids. Regression tests assert distinct add/remove ids and retain the
  TCP claim path. The player confirmed claim removal; expiry/countdown still
  require the current manual retest.
- Future economy work, not part of the Wanted bug: scale shop prices and the
  4-R-Chip bounty consistently for the 10x/100x/1000x modes. Current local
  three-player test mode remains 1x.
- The 2026-09-28 retest rejected expiry on the marked actor's imminent turn:
  Bot 1's mark expired on its first action after application, too early. The
  player proposed a countdown measured in actual active-character changes,
  with one full rotation as the budget, starting at application.
- Current local rule: each application stores its own deadline as application
  turn clock + number of living participants at that time. All marks count
  down on a new active character. Same-turn applications have equal deadlines;
  later applications have later deadlines. Self-shot continuations, card use,
  animations, and reloads do not spend turns. Defeated seats are skipped and
  existing budgets are not shortened after another participant is eliminated.
- Recovered client mechanism: `Enum_Gamer_Buff_Calc` is 25 and its repeated
  `PvpEventOutline.buffs` field is 3. `RouletteGamePlayer:UpdateBuffsInfo` updates
  existing ids and uses `showNum` to switch the table effect when configured.
  Buff effect 5002 uses base effect 107 with change enabled. The original
  `effect_cfg_buff` maps 107/count 1→136, 2→137, 3→138, 4→139. The server sends
  countdown events rather than removing/re-adding a buff; ids/source are kept.
  `Buff.turn` stores elapsed turns, `ContinueTurn` the original budget, and
  `showNum` the remaining turns. The original server's deadline algorithm is
  unavailable; the local duration implements the player's proposed rule.
- Application logs include source, target, duration, current clock and deadline;
  each actual turn boundary logs the active actor and each remaining countdown
  or expiry/payout. Compilation and 110 tests pass, including independent
  deadlines and once-only payouts. The player subsequently accepted the duration.
- Wanted aim regression (2026-09-28): the current copied Lua bundle confirms
  `SetGamerPvpEvent(Type_System=11)` overwrites `gamerPvpEvent`, clears the
  animation queue and calls `ClearCurSelectInfo`/`PlayerLookForward`. Countdown
  and expiry packets could therefore interrupt a correctly selected shot.
  Both now use `Type_Behavior=17`, whose early UI-only branch preserves those
  states. No changes to target indices, damage or individual duration.
- `ShowUIChange` skips standalone `Enum_Coin=4`. The expiry payout now travels
  on the same `Enum_Buff_Update=10` outline as removal: `UpdatePlayerInfo`
  unconditionally applies `coin` before the enum-specific buff update. This
  keeps the passive reward visible without replaying a shot/card animation.
  All 110 tests pass; the TCP checks passive countdown/expiry, full duration,
  both removals and once-only +4 balances. Aim animation requires manual retest.
- Energy Pump (cfg 2031 / skill 10010) was subsequently confirmed by the player
  as working. The log records use on the player and a bot and a skill-charge
  update without HP or ammo changes; it is closed in the manual item list.
