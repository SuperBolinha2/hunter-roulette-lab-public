"""Hawke's native drone skill, separate from ordinary fire and its bonuses."""
from dataclasses import dataclass
from hero_skills import hawke_load_count
from bot_presentation import skill_animation_barrier
from protocol import (parse_varint_field as V, parse_bytes_field as B,
    parse_bytes_fields as Bs, pb_message, pb_varint, pb_bytes, _ammo_message,
    _ammo_sort_id, _pvp_event_outline, _pvp_buff, pvp_gamer_with_state,
    pvp_gamer_with_skill_cd, pvp_gamer_after_weapon_reload, pvp_gun_ammo_counts,
    _weapon_trait_activated, _reload_weapon_buffs, _append_reload_weapon_buff_event)
from weapon_skills import apply_reload_trait
from katie_guard import intercept as intercept_katie


@dataclass
class DroneResult:
    packet: bytes
    wait: float
    consumed: tuple[tuple[int, int], ...]
    hits: tuple[tuple[int, int, int, bool], ...]


def resolve_drone(gamers, hp, frenzy, real, blank, enhanced, *, actor, upgraded,
                  rng, damage, round_number, event_id, event_time,
                  randomize_magazines=False, katie_guards=None):
    count = hawke_load_count(real[actor], enhanced[actor], upgraded=upgraded)
    targets = [i for i in range(len(gamers)) if i != actor and hp[i] + frenzy[i] > 0]
    if count <= 0 or hp[actor] + frenzy[actor] <= 0 or not targets:
        raise ValueError('drone requires loaded rounds and surviving enemies')
    consumed = {1: 0, 2: 0}
    for _ in range(count):
        cfg = 1 if rng.randrange(real[actor] + enhanced[actor]) < real[actor] else 2
        (real if cfg == 1 else enhanced)[actor] -= 1
        consumed[cfg] += 1
    gamers[actor] = pvp_gamer_with_skill_cd(gamers[actor], 3)

    def sync(index):
        gamers[index] = pvp_gamer_with_state(gamers[index], hp=hp[index],
            virtual_hp=frenzy[index], ammo_number=real[index], fake_ammo_number=blank[index],
            enhanced_ammo_number=enhanced[index], round_number=round_number,
            is_dead=hp[index] + frenzy[index] <= 0)

    for index in range(len(gamers)): sync(index)
    events = []
    def small(source, target):
        events.append(pb_message(pb_bytes(1, source), pb_bytes(2, target),
                                 pb_varint(3, event_id), pb_varint(4, len(events)+1)))

    small(_pvp_event_outline(actor, event_type=9, event_time=event_time),
          _pvp_event_outline(actor, event_type=9, skill_cd=3, event_time=event_time))
    small(_pvp_event_outline(actor, event_type=86, event_time=event_time),
          _pvp_event_outline(actor, event_type=86, event_time=event_time,
              u_ammo=tuple(_ammo_message(cfg, number, _ammo_sort_id(cfg))
                           for cfg, number in consumed.items() if number)))
    hits = []
    for _ in range(count):
        surviving = [i for i in targets if hp[i] + frenzy[i] > 0]
        if not surviving: break
        target = rng.choice(surviving)
        blocked = (intercept_katie(gamers, katie_guards, actor, target, 1)
                   if katie_guards is not None else None)
        hd = fd = 0
        if not blocked:
            # Drone hits are one damage each, not normal red-ammo shots.
            hp[target], frenzy[target], hd, fd = damage(hp[target], frenzy[target], 1)
        dead = hp[target] + frenzy[target] <= 0
        hits.append((target, hd, fd, dead))
        small(_pvp_event_outline(actor, event_type=87, event_time=event_time),
              _pvp_event_outline(target, event_type=87, hp_delta=hd, virtual_hp_delta=fd,
                  target_dead=dead, event_time=event_time,
                  del_buffs=(_pvp_buff(blocked, source_index=target, exist_type=3),) if blocked else ()))
        sync(target)
    reloaded = real[actor] + enhanced[actor] == 0
    if reloaded:
        gun = V(B(gamers[actor], 7) or b'', 1) or 0
        r, b = pvp_gun_ammo_counts(gun, randomize=randomize_magazines)
        m = apply_reload_trait(gun, r, b)
        real[actor], blank[actor], enhanced[actor] = m.real, m.blank, m.enhanced
        gamers[actor] = pvp_gamer_after_weapon_reload(gamers[actor]); sync(actor)
        small(_pvp_event_outline(actor, event_type=1, event_time=event_time),
              _pvp_event_outline(actor, event_type=1, is_reload=True, event_time=event_time,
                  r_ammo=Bs(B(gamers[actor], 7) or b'', 2),
                  is_gun_buff=_weapon_trait_activated(gamers[actor]), add_buffs=_reload_weapon_buffs(gamers[actor])))
        _append_reload_weapon_buff_event(events, gamers[actor], event_id=event_id, event_time=event_time)
    packet = pb_message(pb_varint(1, 3), pb_varint(2, 10039 if upgraded else 10038),
        pb_varint(3, actor), *(pb_bytes(4, e) for e in events),
        *(pb_varint(10, i) for i in targets), *(pb_bytes(11, gamers[i]) for i in targets),
        pb_bytes(12, gamers[actor]), pb_varint(13, event_id))
    # Native hit-effects add a 0.5s stage after the 4s skill presentation.
    return DroneResult(packet, skill_animation_barrier(10039 if upgraded else 10038)
                       + .5 + (5.0 if reloaded else 0.0),
                       tuple((cfg, n) for cfg, n in consumed.items() if n), tuple(hits))
