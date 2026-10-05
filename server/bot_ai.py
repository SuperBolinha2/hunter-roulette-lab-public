"""Small, observation-only utility policy. No engine, network or ML dependency.

Hunter Roulette has private magazines, Frenzy and more than two participants:
this is not a port of Buckshot's two-seat minimax. Scores use expected outcomes
and public counts; the resolver, not the policy, draws bullets and dice.
"""
from __future__ import annotations

from dataclasses import dataclass
import random

# Item cfgId != buff cfgId. Confirmed against copied skill_cfg.buff_id and
# buff_cfg.imgName; use these same ids for HUD, legality and expiry.
ITEM_BUFF_CFG = {2015: 1014, 2016: 1015, 2022: 1021, 2030: 10018, 2033: 1026}


def tranquilizer_frenzy_reduction(hp: int, frenzy: int) -> int:
    """Reduce Frenzy by ceil(current HP / 2), clamped to the target's Frenzy."""
    current_hp = max(0, int(hp))
    current_frenzy = max(0, int(frenzy))
    return min(current_frenzy, (current_hp + 1) // 2)


@dataclass(frozen=True)
class ItemRule:
    name: str
    description: str
    effect: str
    targets: str = "any"
    enabled: bool = True


# Derived from copied card_cfg/skill_cfg, ITEM_CATALOG and manual corrections.
# Descriptions are data for explicit scoring rules, not an LLM prompt. New cfgs
# need both a rule and a resolver; unknown cards must never be bought blindly.
ITEM_RULES = {
    2001: ItemRule("Ejector", "Remove a random round from the chosen gun.", "eject"),
    2003: ItemRule("Real Bullet +1", "Add one real round to the chosen gun.", "real"),
    2004: ItemRule("Blank Bullet +1", "Add one blank round to the chosen gun.", "blank"),
    2007: ItemRule("Spare Magazine", "Replace the chosen gun's magazine and reload.", "reload"),
    2008: ItemRule("Hallucinogen", "Force the chosen surviving player to shoot themself.", "hallucinogen"),
    2009: ItemRule("Arms Voucher", "Enhance an existing real round for two damage.", "enhance"),
    2011: ItemRule("Wet Cigarettes", "Roll 4+ to heal one HP; ineffective at zero HP.", "heal"),
    2015: ItemRule("Maintenance Kit", "Next normal enemy shot deals one extra damage.", "maintenance", "self"),
    2016: ItemRule("Burst Mode", "Next enemy shot fires twice; self-shot consumes it without doubling.", "burst", "self"),
    2018: ItemRule("Violation Ticket", "Roll a die and steal the result times 100 coins.", "steal", "enemy"),
    2020: ItemRule("Surprise Box", "Receive a random prop in temporary storage.", "box", "self"),
    2021: ItemRule("Wanted", "Mark for a rotation: damaging shooter claims bounty, otherwise marked survivor collects.", "wanted"),
    2022: ItemRule("Purchase Ban", "Prevent the opponent buying during their next turn.", "purchase_ban", "enemy"),
    2024: ItemRule("Wet Cigarettes", "Roll for a one-HP heal on yourself.", "heal", "self"),
    2025: ItemRule("Hallucinogen", "Force a self-shot; self target allowed by the local manual correction.", "hallucinogen"),
    2026: ItemRule("Ejector", "Remove a random round from the chosen gun.", "eject"),
    2027: ItemRule("Wet Cigarettes", "Roll for a one-HP heal on yourself.", "heal", "self"),
    2028: ItemRule("Surprise Box", "Receive a random stored prop.", "box", "self"),
    2029: ItemRule(
        "Tranquilizer",
        "Reduce the target's Frenzy by half their current HP (rounded up).",
        "tranquilizer",
    ),
    2030: ItemRule("Permission Ban", "Prevent the opponent using a hero skill next turn.", "skill_ban", "enemy"),
    2031: ItemRule("Energy Pump", "Restore one skill charge (reduce local cooldown by one).", "energy"),
    2032: ItemRule("Rocket Launcher", "Randomly fires one round: a blank consumes one; a live hit consumes all remaining live rounds and deals damage equal to their count.", "rocket", "enemy"),
    2033: ItemRule("Bucket", "Block the first normal-shot damage this turn.", "bucket", "self"),
    2034: ItemRule("Piggy Bank", "Accumulate coins and collect the stored balance.", "piggybank", "self", False),
    2036: ItemRule("Surprise Box", "Receive a random stored prop.", "box", "self"),
    2037: ItemRule("Surprise Box", "Receive a random stored prop.", "box", "self"),
}


@dataclass(frozen=True)
class Difficulty:
    margin: float
    mistake_chance: float
    risk: float
    max_preparations: int
    max_self_shots: int


DIFFICULTIES = {
    "easy": Difficulty(.65, .20, 1.3, 1, 2),
    "medium": Difficulty(.30, .06, 2.2, 2, 3),
    "hard": Difficulty(.12, .01, 3.2, 3, 4),
}


@dataclass(frozen=True)
class Fighter:
    index: int
    hp: int
    frenzy: int
    real: int
    blank: int
    enhanced: int = 0
    coin: int = 0
    skill_id: int = 0
    skill_cd: int = 0
    buffs: frozenset[int] = frozenset()
    capacity: int = 8

    @property
    def alive(self) -> bool:
        return self.hp + self.frenzy > 0

    @property
    def live_probability(self) -> float:
        # Enhanced rounds are live, but don't guarantee a live result while
        # blanks remain. Priority conversion belongs to Grazier, not every gun.
        live = self.real + self.enhanced
        total = live + self.blank
        return live / total if total else 0.0


@dataclass(frozen=True)
class Offer:
    id: int
    cfg: int
    price: int = 0
    stored: bool = False


@dataclass(frozen=True)
class Observation:
    actor: int
    fighters: tuple[Fighter, ...]
    offers: tuple[Offer, ...] = ()
    self_shot_streak: int = 0
    preparations: int = 0


@dataclass(frozen=True)
class Decision:
    kind: str
    target: int
    score: float
    reason: str
    offer: Offer | None = None
    effect: int | None = None


def _item_score(rule: ItemRule, actor: Fighter, target: Fighter) -> float | None:
    enemy = actor.index != target.index
    p = actor.live_probability
    q = target.live_probability
    effect = rule.effect
    if effect == "heal":
        return (4 - target.hp) * 1.6 if not enemy and 0 < target.hp < 4 else None
    if effect == "enhance":
        return 1.0 + p * 3 if not enemy and target.real > 0 and not target.enhanced else None
    if effect in ("burst", "maintenance"):
        buff = 1015 if effect == "burst" else 1014
        return .9 + p * 3 if not enemy and buff not in target.buffs else None
    if effect == "bucket":
        return 1.3 + (4 - actor.hp) * .5 if not enemy and ITEM_BUFF_CFG[2033] not in target.buffs else None
    if effect == "hallucinogen":
        # Forced-shot packets currently resolve ordinary magazines only. Do not
        # consume/duplicate a boosted round until that combined path is tested.
        return .8 + q * 3 + (2 if target.hp + target.frenzy <= 1 else 0) if enemy and not target.enhanced and target.real + target.blank > 0 else None
    if effect == "real":
        return 1.3 + (1 - p) * 2 if not enemy and target.real + target.blank + target.enhanced < target.capacity else None
    if effect == "blank":
        return 1.0 + q * 1.8 if enemy and target.real + target.blank + target.enhanced < target.capacity else None
    if effect == "eject":
        return 1.0 + q if enemy and not target.enhanced and target.real + target.blank > 1 else None
    if effect == "rocket":
        live = actor.real + actor.enhanced
        total = live + actor.blank
        if not enemy or total <= 0:
            return None
        hit_chance = live / total
        kill_chance = float(live > 0 and target.hp + target.frenzy <= live)
        return .8 + hit_chance * (1.2 + min(4, live) * .75 + 1.5 * kill_chance) - (1 - hit_chance) * .35
    if effect == "reload":
        return 2.0 if not enemy and (target.real + target.blank <= 2 or p < .3) else None
    if effect == "steal":
        return 2.0 + min(target.coin, 350) / 350 if enemy and target.coin > 0 else None
    if effect == "box":
        return 1.25 if not enemy else None
    if effect == "energy":
        return 1.5 + min(2, actor.skill_cd) * .6 if not enemy and actor.skill_cd > 0 and actor.skill_id in (10000, 10003, 10001, 10004, 10002, 10013) else None
    if effect == "wanted":
        return .8 + p if enemy and 5002 not in target.buffs else None
    if effect == "purchase_ban":
        return 1.3 + min(1, target.coin / 300) if enemy and target.coin >= 100 and ITEM_BUFF_CFG[2022] not in target.buffs else None
    if effect == "skill_ban":
        return 2.4 if enemy and target.skill_id in (10000, 10003, 10001, 10004, 10002, 10013) and target.skill_cd <= 1 and ITEM_BUFF_CFG[2030] not in target.buffs else None
    if effect == "tranquilizer":
        reduction = tranquilizer_frenzy_reduction(target.hp, target.frenzy)
        return 1.5 + 1.25 * reduction if enemy and reduction > 0 else None
    return None


def candidates(obs: Observation, difficulty: str = "medium") -> tuple[Decision, ...]:
    profile = DIFFICULTIES[difficulty]
    actor = next(f for f in obs.fighters if f.index == obs.actor)
    if not actor.alive:
        return ()
    choices: list[Decision] = []
    p = actor.live_probability
    damage = (2 if actor.enhanced else 1) + int(1014 in actor.buffs)
    for target in obs.fighters:
        if not target.alive or actor.real + actor.blank + actor.enhanced <= 0:
            continue
        if target.index == actor.index:
            if obs.self_shot_streak >= profile.max_self_shots or 1015 in actor.buffs or 1014 in actor.buffs:
                continue
            threat = damage / max(1, actor.hp + actor.frenzy)
            death = float(actor.hp + actor.frenzy <= damage)
            score = (1 - p) * (2.6 + .15 * obs.self_shot_streak) - p * (profile.risk * threat + 5 * death)
            reason = "self-blank continuation/bounty versus visible death risk"
        else:
            kill = float(target.hp + target.frenzy <= damage)
            frenzy_need = int(actor.frenzy < 2)
            score = 1 + p * (2 + 3 * kill + .6 * frenzy_need) - (1 - p) * (.7 + (1.8 if actor.hp == 0 else 0))
            if 5002 in target.buffs:
                score += p * .25
            if ITEM_BUFF_CFG[2033] in target.buffs:
                score -= p * 1.5
            score += (4 - target.hp) * .05
            reason = "expected damage/elimination, Frenzy and visible target effects"
        choices.append(Decision("shoot", target.index, score, reason))
    if obs.preparations < profile.max_preparations:
        if ITEM_BUFF_CFG[2030] not in actor.buffs and actor.skill_cd == 0:
            if actor.skill_id in (10001, 10004) and actor.frenzy > 0 and actor.hp < 4:
                choices.append(Decision("skill", actor.index, 3 + min(actor.frenzy, 4 - actor.hp), "convert Frenzy to missing HP"))
            elif actor.skill_id in (10000, 10003):
                if actor.hp < 4:
                    choices.append(Decision("skill", actor.index, 2 + (4 - actor.hp) * .5, "die skill restores missing HP"))
                for target in obs.fighters:
                    if target.alive and target.index != actor.index:
                        choices.append(Decision("skill", target.index, 2.5 + int(target.hp + target.frenzy == 1), "available die skill; expected damage"))
            elif actor.skill_id in (10002, 10013) and any(
                not o.stored and not (o.cfg == 2036 and o.price == 0) for o in obs.offers):
                choices.append(Decision("skill", actor.index, 4, "convert shop offers to free Surprise Boxes"))
            elif actor.skill_id in (10005, 10014):
                for target in obs.fighters:
                    if target.alive and target.index != actor.index:
                          choices.append(Decision("skill", target.index, 2.5, "Fair Duel starts with an extra live round"))
            elif actor.skill_id in (10020, 10021, 10024, 10025, 10026, 10027):
                from hero_skills import shelby_trade
                if shelby_trade(actor.hp, actor.frenzy, actor.coin, 2, actor.skill_id):
                    choices.append(Decision("skill", actor.index, 2 + (4 - actor.hp), "buy HP", effect=2))
                if actor.hp >= 3 and actor.coin < 500 and shelby_trade(actor.hp, actor.frenzy, actor.coin, 1, actor.skill_id):
                    choices.append(Decision("skill", actor.index, 1.5, "trade spare HP for shop money", effect=1))
            elif actor.skill_id in (10017, 10018) and actor.blank > 0:
                choices.append(Decision("skill", actor.index, 2.8, "replace own blank with live/enhanced round"))
            elif actor.skill_id in (10022,10023,10030,10031) and not actor.buffs.intersection((10029,10031,10047,10049)):
                choices.append(Decision("skill",actor.index,3.0,"protect from next enemy shot"))
            elif actor.skill_id in (10032,10033) and not actor.buffs.intersection((10051,10052)):
                if actor.real + actor.enhanced > 0 and any(
                    f.alive and f.index != actor.index and f.frenzy > 0 for f in obs.fighters):
                    choices.append(Decision("skill",actor.index,3.2,"ordinary hits remove enemy Frenzy this turn"))
            elif actor.skill_id in (10035,10036) and actor.real + actor.blank + actor.enhanced < actor.capacity:
                for target in obs.fighters:
                    if target.alive and target.index != actor.index and target.real + target.enhanced > 0:
                        choices.append(Decision("skill",target.index,3.4 + .4 * bool(target.enhanced),
                                                "steal enemy live round into free magazine slot"))
        for offer in obs.offers:
            rule = ITEM_RULES.get(offer.cfg)
            if rule is None or not rule.enabled:
                continue
            if not offer.stored and (ITEM_BUFF_CFG[2022] in actor.buffs or offer.price > actor.coin):
                continue
            for target in obs.fighters:
                if not target.alive or (rule.targets == "self" and target.index != actor.index) or (rule.targets == "enemy" and target.index == actor.index):
                    continue
                score = _item_score(rule, actor, target)
                if score is None:
                    continue
                cost = 0 if offer.stored else .2 + 1.4 * offer.price / max(300, actor.coin)
                choices.append(Decision("item", target.index, score - cost,
                                        rule.description, offer))
    return tuple(choices)


def choose_action(obs: Observation, rng: random.Random, difficulty: str = "medium") -> Decision | None:
    """O(offers * fighters), bounded; difficulty never changes actual outcomes."""
    options = candidates(obs, difficulty)
    if not options:
        return None
    profile = DIFFICULTIES[difficulty]
    best = max(o.score for o in options)
    pool = [o for o in options if o.score >= best - profile.margin * max(1, abs(best))]
    if rng.random() < profile.mistake_chance:
        # Mistakes only among legal decisions, never secret knowledge or cheat HP.
        pool = list(options)
    weights = [max(.05, o.score - min(x.score for x in pool) + .25) for o in pool]
    return rng.choices(pool, weights=weights, k=1)[0]
