"""Actor-indexed item/skill executor for the local trio lab.

Selection lives in bot_ai and cannot see random outcomes. This executor checks
the actual inventory/stock again, draws results, and uses native packet builders.
Shared draw/damage/forced-shot/Wanted rules are supplied by the server.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import random
from typing import Callable
from weapon_skills import apply_reload_trait
from hero_skills import bear_conversion, rabbit_power, shelby_trade, SHELBY_SKILLS, annie_convert
from hero_shop import monkey_convert_shop
from fair_duel import resolve_fair_duel
from katie_guard import activate as activate_katie, intercept as intercept_katie, KATIE_BUFFS, KATIE_SKILLS

from bot_ai import (Decision, Fighter, ITEM_RULES, ITEM_BUFF_CFG, Observation,
                    Offer, candidates, tranquilizer_frenzy_reduction)
from bot_presentation import skill_animation_barrier, card_animation_barrier
from protocol import (
    GUN_AMMO_SPECS,
    LAB_CARD_SKILLS, WANTED_PARENT_BUFF_CFG_ID, WANTED_REWARD_BUFF_CFG_ID,
    parse_bytes_field, parse_bytes_fields, parse_varint_field,
    pb_message, pb_varint, _c_ammo_message, _ammo_message,
    pvp_card_slot_body, pvp_empty_card_slot_body,
    pvp_gamer_with_coin_and_card, pvp_gamer_with_state, pvp_gamer_with_buffs,
    pvp_gamer_skill_id, pvp_gamer_skill_cd, pvp_gamer_with_skill_cd,
    pvp_shop_card, pvp_generic_card_event_result_body,
    pvp_add_ammo_card_event_result_body, pvp_spare_magazine_event_result_body,
    pvp_eject_ammo_card_event_result_body, pvp_wet_cigarette_event_result_body,
    pvp_hallucinogen_use_event_result_body,
    pvp_hallucinogen_buy_and_use_event_result_body,
    pvp_hero_skill_event_result_body,
    pvp_gamer_after_weapon_reload, pvp_consume_lucky_die,
    pvp_event_with_consumed_lucky,
    pvp_ghosts_after_shot,
    pvp_consume_toxin_heal, pvp_event_with_toxin_removed,
)


def has_buff(gamer: bytes, cfg: int) -> bool:
    return any(parse_varint_field(b, 1) == cfg for b in parse_bytes_fields(gamer, 8))


@dataclass
class TurnRestrictions:
    """A ban covers the target's next complete turn, not the caster's turn."""
    starts: list[int] = field(default_factory=lambda: [0, 0, 0])
    deadlines: dict[tuple[int, int], int] = field(default_factory=dict)

    def apply(self, target: int, cfg: int) -> None:
        if cfg not in (2022, 2030, 10066):
            raise ValueError("unknown turn restriction")
        self.deadlines[target, cfg] = self.starts[target] + 2

    def apply_to_gamer(
        self, gamers: list[bytes], target: int, cfg: int, *, source_index: int = 0,
    ) -> int:
        """Apply a timed ban and persist its native HUD buff in the gamer snapshot."""
        self.apply(target, cfg)
        buff_cfg = ITEM_BUFF_CFG[cfg]
        gamers[target] = pvp_gamer_with_buffs(
            gamers[target], add_cfg_ids=(buff_cfg,), source_index=source_index,
        )
        return buff_cfg

    def start(self, actor: int) -> tuple[int, ...]:
        self.starts[actor] += 1
        expired = tuple(cfg for (target, cfg), end in self.deadlines.items()
                        if target == actor and self.starts[actor] >= end)
        for cfg in expired:
            del self.deadlines[actor, cfg]
        return tuple(10066 if cfg == 10066 else ITEM_BUFF_CFG[cfg] for cfg in expired)


@dataclass
class BattleActions:
    gamers: list[bytes]
    hp: list[int]
    frenzy: list[int]
    real: list[int]
    blank: list[int]
    self_shots: list[int]
    enhanced: list[int]
    maintenance: list[int]
    burst: list[int]
    bucket: list[bool]
    shop: list[bytes]
    round_number: int
    next_card_id: int
    restrictions: TurnRestrictions
    rng: random.Random
    reload: Callable[[int], tuple[int, int]]
    draw: Callable[[int, int], int | None]
    damage: Callable[[int, int, int], tuple[int, int, int, int]]
    forced_shot: Callable[..., tuple | None]
    apply_wanted: Callable[[int, int], None]
    randomize_magazines: bool = False
    katie_guards: dict = field(default_factory=dict)

    def sync(self) -> None:
        for i, gamer in enumerate(self.gamers):
            self.gamers[i] = pvp_gamer_with_state(
                gamer, hp=self.hp[i], virtual_hp=self.frenzy[i],
                ammo_number=self.real[i], fake_ammo_number=self.blank[i],
                enhanced_ammo_number=self.enhanced[i],
                burst_mode_active=bool(self.burst[i]),
                maintenance_kit_active=bool(self.maintenance[i]),
                round_number=self.round_number,
                is_dead=self.hp[i] + self.frenzy[i] <= 0,
            )

    def observation(self, actor: int, preparations: int = 0, streak: int = 0) -> Observation:
        fighters = tuple(Fighter(
            i, self.hp[i], self.frenzy[i], self.real[i], self.blank[i],
            self.enhanced[i], parse_varint_field(g, 5) or 0,
            pvp_gamer_skill_id(g), pvp_gamer_skill_cd(g),
            frozenset(parse_varint_field(b, 1) or 0 for b in parse_bytes_fields(g, 8)),
            GUN_AMMO_SPECS[parse_varint_field(parse_bytes_field(g, 7) or b"", 1) or 0][0],
        ) for i, g in enumerate(self.gamers))
        offers = [Offer(parse_varint_field(c, 1) or 0,
                        parse_varint_field(c, 2) or 0,
                        parse_varint_field(c, 3) or 0)
                  for c in self.shop if parse_varint_field(c, 5) == 1]
        slot = parse_bytes_field(self.gamers[actor], 18) or b""
        if (parse_varint_field(slot, 2) or 0) in ITEM_RULES:
            offers.append(Offer(parse_varint_field(slot, 1) or 0,
                                parse_varint_field(slot, 2) or 0, 0, True))
        return Observation(actor, fighters, tuple(offers), streak, preparations)

    def resolve(self, actor: int, decision: Decision, *, event_id: int,
                event_time: int, difficulty: str = "medium",
                preparations: int = 0) -> tuple[bytes, float] | None:
        # Revalidate instead of trusting a stale plan or a forged stock id.
        legal = candidates(self.observation(actor, preparations), difficulty)
        if not any((d.kind, d.target, d.offer, d.effect) ==
                   (decision.kind, decision.target, decision.offer, decision.effect) for d in legal):
            return None
        target = decision.target
        if decision.kind == "skill":
            sid = pvp_gamer_skill_id(self.gamers[actor])
            if sid in (10005, 10014):
                def duel_draw(r, b, e):
                    n = self.rng.randrange(r + b + e)
                    return 300 if n < b else 1 if n < b + r else 2
                result = resolve_fair_duel(self.gamers, self.hp, self.frenzy,
                    self.real, self.blank, self.enhanced, actor=actor, target=target,
                    upgraded=sid == 10014, draw=duel_draw, damage=self.damage,
                    round_number=self.round_number, event_id=event_id, event_time=event_time,
                      randomize_magazines=self.randomize_magazines, katie_guards=self.katie_guards)
                return result.packet, result.wait
            roll = None
            lucky_consumed = 0
            toxin_used = False
            hp_delta = frenzy_delta = 0
            monkey_cards = None
            exchange_coin = 0
            conversion_cfg = None
            skill_add_buffs = ()
            if sid in KATIE_SKILLS:
                self.gamers[actor] = activate_katie(self.gamers[actor],sid,actor,self.katie_guards)
                skill_add_buffs = tuple(b for b in parse_bytes_fields(self.gamers[actor],8)
                    if parse_varint_field(b,1) in KATIE_BUFFS)
            elif sid in (10017, 10018):
                converted = annie_convert(self.real[target], self.blank[target], self.enhanced[target],
                    upgraded=sid == 10018, friendly=target == actor)
                if converted is None:
                    return None
                self.real[target], self.blank[target], self.enhanced[target], conversion_cfg = converted
            elif sid in SHELBY_SKILLS:
                coin = parse_varint_field(self.gamers[actor], 5) or 0
                trade = shelby_trade(self.hp[actor], self.frenzy[actor], coin, decision.effect, sid)
                if trade is None or target != actor:
                    return None
                hp_delta, frenzy_delta, exchange_coin = trade
                if hp_delta > 0:
                    self.gamers[actor], hp_delta, toxin_used = pvp_consume_toxin_heal(self.gamers[actor], hp_delta)
                self.hp[actor] += hp_delta
                self.frenzy[actor] += frenzy_delta
                self.gamers[actor] = pvp_gamer_with_coin_and_card(self.gamers[actor], coin=coin + exchange_coin)
            elif sid in (10002, 10013):
                monkey_cards, self.next_card_id, _ = monkey_convert_shop(
                    self.shop, upgraded=sid == 10013, next_id=self.next_card_id, rng=self.rng)
                self.shop[:] = monkey_cards
            elif sid in (10001, 10004):
                hp_delta, spent_frenzy = bear_conversion(self.hp[actor], self.frenzy[actor], upgraded=sid == 10004)
                self.gamers[actor], hp_delta, toxin_used = pvp_consume_toxin_heal(self.gamers[actor],hp_delta)
                frenzy_delta = -spent_frenzy
                self.hp[actor] += hp_delta
                self.frenzy[actor] -= spent_frenzy
            elif sid in (10000, 10003):
                roll = self.rng.randint(1, 6)
                raw_roll = roll
                self.gamers[actor], roll, used_lucky = pvp_consume_lucky_die(self.gamers[actor], roll)
                lucky_consumed = raw_roll if used_lucky else 0
                if roll >= 3:
                    power = rabbit_power(roll, upgraded=sid == 10003)
                    if target == actor:
                        hp_delta = min(power, max(0, 4 - self.hp[actor]))
                        self.gamers[actor], hp_delta, toxin_used = pvp_consume_toxin_heal(self.gamers[actor], hp_delta)
                        self.hp[actor] += hp_delta
                    else:
                        self.hp[target], self.frenzy[target], hp_delta, frenzy_delta = self.damage(
                            self.hp[target], self.frenzy[target], power)
            else:
                return None
            skill_cd = 2 if sid in SHELBY_SKILLS else 3
            self.gamers[actor] = pvp_gamer_with_skill_cd(self.gamers[actor], skill_cd)
            self.sync()
            packet = pvp_hero_skill_event_result_body(
                self.gamers[actor], self.gamers[target], skill_id=sid,
                target_index=target, skill_cd=skill_cd, event_id=event_id,
                hp_delta=hp_delta, virtual_hp_delta=frenzy_delta,
                luck_roll=roll, shop_cards=monkey_cards, event_time=event_time,
                exchange_effect=decision.effect if sid in SHELBY_SKILLS else None,
                exchange_coin=exchange_coin, conversion_cfg=conversion_cfg, skill_add_buffs=skill_add_buffs)
            packet = pvp_event_with_consumed_lucky(packet, actor, consumed=lucky_consumed,
                                                   event_id=event_id, event_time=event_time)
            packet = pvp_event_with_toxin_removed(packet,actor,toxin_used,
                event_id=event_id,event_time=event_time)
            return packet, skill_animation_barrier(sid)
        if decision.kind != "item" or decision.offer is None:
            return None
        offer = decision.offer
        rule = ITEM_RULES[offer.cfg]
        card = (parse_bytes_field(self.gamers[actor], 18) or b"") if offer.stored else next(
            c for c in self.shop if parse_varint_field(c, 1) == offer.id)
        coin = parse_varint_field(self.gamers[actor], 5) or 0
        cost = 0 if offer.stored else offer.price
        old_real, old_blank = self.real[target], self.blank[target]
        old_actor_frenzy = self.frenzy[actor]
        empty = pvp_empty_card_slot_body() if offer.stored else None
        self.gamers[actor] = pvp_gamer_with_coin_and_card(
            self.gamers[actor], coin=coin - cost, card_slot=empty)
        if not offer.stored:
            self.shop[:] = [pvp_shop_card(
                parse_varint_field(c, 1) or 0, parse_varint_field(c, 2) or 0,
                parse_varint_field(c, 3) or 0, parse_varint_field(c, 4) or 1,
                2 if parse_varint_field(c, 1) == offer.id else (parse_varint_field(c, 5) or 1),
            ) for c in self.shop]
        buy_coin = -cost if not offer.stored else None
        common = dict(target_index=target, event_id=event_id, event_time=event_time,
                      coin_delta=buy_coin)
        effect = rule.effect
        packet = None
        lucky_consumed = 0
        delay = 5.0
        generic: dict = {}
        if effect in ("real", "blank"):
            (self.real if effect == "real" else self.blank)[target] += 1
            self.sync()
            packet = pvp_add_ammo_card_event_result_body(
                self.gamers[actor], self.gamers[target], card,
                real_after=self.real[target], fake_after=self.blank[target], **common)
        elif effect == "reload":
            gun = parse_bytes_field(self.gamers[target], 7) or b""
            self.real[target], self.blank[target] = self.reload(parse_varint_field(gun, 1) or 0)
            magazine = apply_reload_trait(parse_varint_field(gun, 1) or 0,
                                          self.real[target], self.blank[target])
            self.real[target], self.enhanced[target] = magazine.real, magazine.enhanced
            self.gamers[target] = pvp_gamer_after_weapon_reload(self.gamers[target])
            self.sync()
            packet = pvp_spare_magazine_event_result_body(
                self.gamers[actor], self.gamers[target], card,
                old_real=old_real, old_fake=old_blank,
                real_after=self.real[target], fake_after=self.blank[target], **common)
            delay = 7.0
        elif effect == "eject":
            ammo = self.draw(self.real[target] + self.enhanced[target], self.blank[target])
            if ammo == 1 and self.enhanced[target] and self.rng.randrange(
                    self.real[target] + self.enhanced[target]) >= self.real[target]:
                ammo = 2
            if ammo is None:
                raise RuntimeError("validated ejector had no round")
            (self.blank if ammo == 300 else self.enhanced if ammo == 2 else self.real)[target] -= 1
            reload_after = None
            if self.real[target] + self.enhanced[target] <= 0:
                gun = parse_bytes_field(self.gamers[target], 7) or b""
                reload_after = self.reload(parse_varint_field(gun, 1) or 0)
                self.real[target], self.blank[target] = reload_after
                magazine = apply_reload_trait(parse_varint_field(gun, 1) or 0,
                                              self.real[target], self.blank[target])
                self.real[target], self.enhanced[target] = magazine.real, magazine.enhanced
                reload_after = self.real[target], self.blank[target]
                self.gamers[target] = pvp_gamer_after_weapon_reload(self.gamers[target])
            self.sync()
            packet = pvp_eject_ammo_card_event_result_body(
                self.gamers[actor], self.gamers[target], card,
                ejected_ammo_cfg_id=ammo, reload_ammo_after=reload_after, **common)
            delay = 7.0 if reload_after else 5.0
        elif effect == "hallucinogen":
            result = self.forced_shot(
                self.gamers, self.hp, self.frenzy, self.real, self.blank,
                self.self_shots, target, round_number=self.round_number,
                event_id=event_id, event_time=event_time,
                randomize_magazines=self.randomize_magazines,
                enhanced_ammo=self.enhanced)
            if result is None:
                raise RuntimeError("validated hallucinogen had no target")
            self.sync()
            if offer.stored:
                packet = pvp_hallucinogen_use_event_result_body(
                    self.gamers[actor], self.gamers[target], card,
                    target_index=target, event_id=event_id,
                    event_time=event_time, shot_result=result[3])
            else:
                packet = pvp_hallucinogen_buy_and_use_event_result_body(
                    self.gamers[actor], self.gamers[target], card,
                    shot_result=result[3], **common)
            delay = 8.0
        elif effect == "rocket":
            live_before = self.real[actor] + self.enhanced[actor]
            ammo_cfg_id = self.draw(live_before, self.blank[actor])
            if ammo_cfg_id is None:
                raise RuntimeError("validated Rocket Launcher had no round")
            consumed: list[bytes] = []
            hp_delta = frenzy_delta = 0
            damage = 0
            blocked_katie = intercept_katie(self.gamers,self.katie_guards,actor,target,ammo_cfg_id)
            if ammo_cfg_id == 300:
                self.blank[actor] -= 1
                consumed.append(_ammo_message(300, 1, 1))
                self.frenzy[actor] = max(0, self.frenzy[actor] - 1)
                source_frenzy_delta = self.frenzy[actor] - old_actor_frenzy
                is_hit = False
            else:
                ordinary_live = self.real[actor]
                enhanced_live = self.enhanced[actor]
                if ordinary_live:
                    consumed.append(_ammo_message(1, ordinary_live, 3))
                if enhanced_live:
                    consumed.append(_ammo_message(2, enhanced_live, 4))
                self.real[actor] = 0
                self.enhanced[actor] = 0
                damage = ordinary_live + enhanced_live
                if blocked_katie:
                    damage = 0
                self.hp[target], self.frenzy[target], hp_delta, frenzy_delta = self.damage(
                    self.hp[target], self.frenzy[target], damage)
                cap = parse_varint_field(self.gamers[actor], 23)
                cap = 2 if cap is None else max(0, cap)
                if hp_delta < 0 or frenzy_delta < 0:
                    self.frenzy[actor] = min(cap, self.frenzy[actor] + 1)
                source_frenzy_delta = self.frenzy[actor] - old_actor_frenzy
                is_hit = True

            self.gamers[actor], ghosts_added = pvp_ghosts_after_shot(self.gamers[actor], ammo_cfg_id)
            self.real[actor] += ghosts_added
            reload_after = None
            if self.real[actor] + self.enhanced[actor] <= 0:
                survivors = sum(f.hp + f.frenzy > 0 for f in self.observation(actor).fighters)
                if survivors > 1 and self.hp[actor] + self.frenzy[actor] > 0:
                    gun = parse_bytes_field(self.gamers[actor], 7) or b""
                    reload_after = self.reload(parse_varint_field(gun, 1) or 0)
                    self.real[actor], self.blank[actor] = reload_after
                    magazine = apply_reload_trait(parse_varint_field(gun, 1) or 0,
                                                  self.real[actor], self.blank[actor])
                    self.real[actor], self.enhanced[actor] = magazine.real, magazine.enhanced
                    reload_after = self.real[actor], self.blank[actor]
                    self.gamers[actor] = pvp_gamer_after_weapon_reload(self.gamers[actor])
            self.sync()
            generic = dict(
                event_type=39,
                hp_delta=hp_delta,
                virtual_hp_delta=frenzy_delta,
                is_rpg_hit=is_hit,
                source_u_ammo=tuple(consumed),
                ghosts_added_real=ghosts_added,
                source_virtual_hp_delta=source_frenzy_delta,
                target_dead=self.hp[target] + self.frenzy[target] <= 0,
                reload_ammo_after=reload_after,
                target_del_buff_cfgs=(blocked_katie,) if blocked_katie else (),
            )
            delay = 8.0
        elif effect == "heal":
            roll = self.rng.randint(1, 6)
            raw_roll = roll
            self.gamers[actor], roll, used_lucky = pvp_consume_lucky_die(self.gamers[actor], roll)
            lucky_consumed = raw_roll if used_lucky else 0
            heal = int(roll >= 4 and 0 < self.hp[target] < 4)
            self.gamers[target], heal, toxin_used = pvp_consume_toxin_heal(self.gamers[target],heal)
            self.hp[target] += heal
            self.sync()
            packet = pvp_wet_cigarette_event_result_body(
                self.gamers[actor], card, die_roll=roll, heal_delta=heal,
                event_id=event_id, event_time=event_time, coin_delta=buy_coin)
            packet = pvp_event_with_toxin_removed(packet,target,toxin_used,
                event_id=event_id,event_time=event_time)
            delay = 6.0
        elif effect == "enhance":
            self.real[target] -= 1
            self.enhanced[target] += 1
            generic = dict(event_type=8,
                           c_ammo=_c_ammo_message(1, 1, 2, 1),
                           r_ammo=(_ammo_message(300, self.blank[target], 1),
                                   _ammo_message(1, self.real[target], 3),
                                   _ammo_message(2, self.enhanced[target], 4)))
        elif effect in ("burst", "maintenance", "bucket", "wanted", "purchase_ban", "skill_ban"):
            buff = ITEM_BUFF_CFG.get(offer.cfg, offer.cfg)
            if effect == "burst":
                self.burst[target] = 1
                buff = 1015
            elif effect == "maintenance":
                self.maintenance[target] = 1
                buff = 1014
            elif effect == "bucket":
                self.bucket[target] = True
            elif effect == "wanted":
                self.apply_wanted(target, actor)
                generic = dict(event_type=10, add_buff_cfgs=(1020, 5002))
            elif effect in ("purchase_ban", "skill_ban"):
                self.restrictions.apply(target, offer.cfg)
            if effect != "wanted":
                self.gamers[target] = pvp_gamer_with_buffs(
                    self.gamers[target], add_cfg_ids=(buff,), source_index=actor)
                generic = dict(event_type=10, add_buff_cfg=buff)
        elif effect == "steal":
            roll = self.rng.randint(1, 6)
            raw_roll = roll
            self.gamers[actor], roll, used_lucky = pvp_consume_lucky_die(self.gamers[actor], roll)
            lucky_consumed = raw_roll if used_lucky else 0
            other_coin = parse_varint_field(self.gamers[target], 5) or 0
            stolen = min(other_coin, roll * 100)
            self.gamers[target] = pvp_gamer_with_coin_and_card(
                self.gamers[target], coin=other_coin - stolen)
            self.gamers[actor] = pvp_gamer_with_coin_and_card(
                self.gamers[actor], coin=coin - cost + stolen)
            generic = dict(event_type=7, luck_roll=roll, luck_success=True, stolen_coin=stolen)
            delay = 7.0
        elif effect == "energy":
            cd = max(0, pvp_gamer_skill_cd(self.gamers[target]) - 1)
            self.gamers[target] = pvp_gamer_with_skill_cd(self.gamers[target], cd)
            generic = dict(event_type=9, skill_cd=cd)
        elif effect == "tranquilizer":
            reduction = tranquilizer_frenzy_reduction(
                self.hp[target], self.frenzy[target],
            )
            self.frenzy[target] -= reduction
            generic = dict(event_type=14, virtual_hp_delta=-reduction)
        elif effect == "box":
            rewards = [c for c, r in ITEM_RULES.items() if r.enabled and r.effect != "box"]
            reward = self.rng.choice(rewards)
            new_slot = pvp_card_slot_body(pvp_shop_card(self.next_card_id, reward, 0))
            self.next_card_id += 1
            self.gamers[actor] = pvp_gamer_with_coin_and_card(
                self.gamers[actor], coin=coin - cost, card_slot=new_slot)
            generic = dict(new_card_slot=new_slot)
        else:
            raise RuntimeError(f"enabled item has no resolver: {offer.cfg}")
        if packet is None:
            self.sync()
            packet = pvp_generic_card_event_result_body(
                self.gamers[actor], self.gamers[target], card,
                skill_id=LAB_CARD_SKILLS[offer.cfg], buy=not offer.stored,
                clear_slot=offer.stored, **common, **generic)
        packet = pvp_event_with_consumed_lucky(packet, actor, consumed=lucky_consumed,
                                               event_id=event_id, event_time=event_time)
        return packet, card_animation_barrier(effect, stored=offer.stored, resolver_wait=delay)
