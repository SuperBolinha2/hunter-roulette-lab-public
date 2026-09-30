"""Implemented hero upgrades; never enable an ID without its executor."""
BEAR_BASE = 10001
BEAR_UPGRADE = 10004
RABBIT_BASE = 10000
RABBIT_UPGRADE = 10003
MONKEY_BASE = 10002
MONKEY_UPGRADE = 10013
ARTHUR_BASE = 10005
ARTHUR_UPGRADE = 10014
SHELBY_SKILLS = (10020, 10021, 10024, 10025, 10026, 10027)


def effective_hero_skill(entry: dict) -> int:
    skill = int(entry.get('skillId', 0))
    hero = int(entry.get('id', -1))
    pairs = {0: (RABBIT_BASE, RABBIT_UPGRADE), 1: (BEAR_BASE, BEAR_UPGRADE),
             13: (MONKEY_BASE, MONKEY_UPGRADE), 14: (ARTHUR_BASE, ARTHUR_UPGRADE),
             15: (10020, 10021), 16: (10017, 10018), 17: (10022, 10023)}
    if hero in pairs:
        base, upgrade = pairs[hero]
        unlocked = (int(entry.get('starLevel', 0)) >= 5
                    or bool(entry.get('skillUpgradeUnlocked')) or skill == upgrade)
        return upgrade if unlocked else base
    return skill


def battle_hero_skill(skill: int, *, shop_trio: bool) -> int:
    # Native difficulty3 economic variants. Lobby/save retain the base ID.
    return {10020: 10026, 10021: 10027, 10023: 10031}.get(skill, skill) if shop_trio else skill


def annie_convert(real: int, blank: int, red: int, *, upgraded: bool, friendly: bool):
    """Replace exactly one blank, never add a slot or change weapon capacity."""
    if min(real, blank, red) < 0 or blank == 0:
        return None
    cfg = 2 if upgraded and friendly else 1
    return real + (cfg == 1), blank - 1, red + (cfg == 2), cfg


def shelby_trade(hp: int, frenzy: int, coin: int, effect: int, skill: int):
    """Validated (HP delta, Frenzy delta, coin delta), or None. Self trade."""
    if skill not in SHELBY_SKILLS or hp + frenzy <= 0:
        return None
    scale = 100 if skill in (10026, 10027) else 10 if skill in (10024, 10025) else 1
    if effect == 1 and hp + frenzy > 1:
        return (-1, 0, 5 * scale) if hp > 0 else (0, -1, 5 * scale)
    if effect == 2 and coin >= 3 * scale and hp < 4:
        if hp > 0 or skill in (10021, 10025, 10027):
            return 1, 0, -3 * scale
    return None


def rabbit_power(roll: int, *, upgraded: bool) -> int:
    """Use the final die result, including native Lucky Streak modifiers."""
    if roll < 3:
        return 0
    return 2 if upgraded and roll == 6 else 1


def bear_conversion(hp: int, frenzy: int, *, upgraded: bool, hp_cap: int = 4) -> tuple[int, int]:
    """Return attempted healing and spent Frenzy, before healing suppression.

    Poison suppresses regeneration, not the cost of the conversion. Only
    Frenzy exceeding available HP space is preserved by the upgraded skill.
    """
    frenzy = max(0, frenzy)
    heal = min(frenzy, max(0, hp_cap - hp))
    return heal, heal if upgraded else frenzy
