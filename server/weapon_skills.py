"""Server-side weapon traits, introduced one verified family at a time.

No Unity dependency: these rules can be tested without launching the client.
Gun IDs come from the copied gun_cfg, not from the selected hero or skin.
"""
from dataclasses import dataclass

SCREWDRIVER_GUN_IDS = frozenset((1, 5, 9, 16, 20, 29))
SCREWDRIVER_SKILL_ID = 2
LITTLE_MANIAC_GUN_IDS = frozenset((0, 8, 10, 15, 19, 33))
LITTLE_MANIAC_SKILL_ID = 3
LUCKY_STREAK_BUFF_ID = 600
LOVESONG_GUN_IDS = frozenset((14,))
LOVESONG_SKILL_ID = 10016
ARTEMIS_GUN_IDS = frozenset((34,))
ARTEMIS_SKILL_ID = 10034
GRAZIER_GUN_IDS = frozenset((7, 18, 31))
GRAZIER_SKILL_ID = 10007
GHOSTS_SKILL_ID = 10040
GHOSTS_BUFF_ID = 10070
REDSIREN_SKILL_ID = 10019
CARNIVORE_SKILL_ID = 10015
LADY_J_GUN_IDS = frozenset((6,17,30,32))
LADY_J_SKILL_ID = 10006
VENOM_SKILL_ID = 10037
TOXIN_BUFF_ID = 10066


def weapon_skill_id(gun_id: int) -> int:
    if gun_id in SCREWDRIVER_GUN_IDS:
        return SCREWDRIVER_SKILL_ID
    if gun_id in LOVESONG_GUN_IDS:
        return LOVESONG_SKILL_ID
    if gun_id in ARTEMIS_GUN_IDS:
        return ARTEMIS_SKILL_ID
    if gun_id in GRAZIER_GUN_IDS:
        return GRAZIER_SKILL_ID
    if gun_id == 38:
        return GHOSTS_SKILL_ID
    if gun_id == 13:
        return REDSIREN_SKILL_ID
    if gun_id == 12:
        return CARNIVORE_SKILL_ID
    if gun_id in LADY_J_GUN_IDS:
        return LADY_J_SKILL_ID
    if gun_id == 35:
        return VENOM_SKILL_ID
    return LITTLE_MANIAC_SKILL_ID if gun_id in LITTLE_MANIAC_GUN_IDS else 0


def lucky_die_result(raw_roll: int, active: bool) -> int:
    if not 1 <= raw_roll <= 6:
        raise ValueError('Die result must be between 1 and 6')
    return min(6, raw_roll + 2) if active else raw_roll


def prioritize_shot_ammo(gun_id: int, drawn: int | None, enhanced: int) -> int | None:
    """Grazier changes which live round fires, never the blank/live odds."""
    if weapon_skill_id(gun_id) == GRAZIER_SKILL_ID and enhanced > 0 and drawn == 1:
        return 2
    return drawn


def normal_shot_count(gun_id: int, real: int, blank: int, enhanced: int,
                      source: int, target: int, burst: bool = False) -> int:
    """RedSiren adds one normal enemy shot, without recursing on that shot."""
    if source == target:
        return 1
    red = weapon_skill_id(gun_id) == REDSIREN_SKILL_ID and blank == 0 and real + enhanced > 0
    return 1 + int(burst) + int(red)


def carnivore_reward(gun_id: int, source: int, target: int,
                     shots: list[tuple], frenzy_deltas: list[int]) -> int:
    if weapon_skill_id(gun_id) != CARNIVORE_SKILL_ID or source == target:
        return 0
    return 2 * sum(shot[0] in (1, 2) and (shot[1] < 0 or
        (i < len(frenzy_deltas) and frenzy_deltas[i] < 0))
        for i, shot in enumerate(shots))


def self_shot_reward_multiplier(gun_id: int, real: int, blank: int) -> int:
    return 2 if weapon_skill_id(gun_id) == LADY_J_SKILL_ID and real >= blank else 1


@dataclass(frozen=True)
class ReloadMagazine:
    real: int
    blank: int
    enhanced: int = 0


def apply_reload_trait(gun_id: int, real: int, blank: int) -> ReloadMagazine:
    """Screwdriver upgrades one ordinary live round; capacity is conserved.

    Rounds of the same cfg are represented as a stack, so choosing randomly
    between ordinary rounds produces the same observable stack conversion.
    A fresh magazine replaces previous enhanced ammunition, not accumulates it.
    """
    if real < 0 or blank < 0:
        raise ValueError('Reload counts cannot be negative')
    if weapon_skill_id(gun_id) == ARTEMIS_SKILL_ID and blank:
        return ReloadMagazine(real + 1, blank - 1)
    if weapon_skill_id(gun_id) == SCREWDRIVER_SKILL_ID and real:
        return ReloadMagazine(real - 1, blank, 1)
    return ReloadMagazine(real, blank)
