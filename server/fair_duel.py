"""Arthur's skill shots, not normal fire: alternate until a live round.

No normal-shot rewards, Frenzy gain/loss, Burst or Maintenance consumption.
The client's Cowboy callbacks consume all shots from one native skill packet.
"""
from dataclasses import dataclass
from protocol import (parse_varint_field as V, parse_bytes_field as B,
    parse_bytes_fields as Bs, pb_message, pb_varint, pb_bytes,
    pvp_gamer_with_state, pvp_gamer_with_skill_cd, pvp_gamer_after_weapon_reload,
    pvp_gun_ammo_counts, pvp_shoot_event_result_body, _pvp_event_outline,
    _reload_ammo_messages, _append_reload_weapon_buff_event,
    pvp_hero_skill_event_result_body)
from weapon_skills import apply_reload_trait, prioritize_shot_ammo
from katie_guard import intercept as intercept_katie


@dataclass
class DuelResult:
    packet: bytes
    shots: tuple[tuple[int, int, int], ...]
    wait: float


def resolve_fair_duel(gamers, hp, frenzy, real, blank, enhanced, *, actor,
                      target, upgraded, draw, damage, round_number, event_id,
                      event_time, randomize_magazines=False, katie_guards=None):
    if actor == target or hp[actor] + frenzy[actor] <= 0 or hp[target] + frenzy[target] <= 0:
        raise ValueError('duel requires two surviving opponents')
    skill_id = 10014 if upgraded else 10005
    gamers[actor] = pvp_gamer_with_skill_cd(gamers[actor], 3)
    events = Bs(pvp_hero_skill_event_result_body(gamers[actor], gamers[target],
        skill_id=skill_id, target_index=target, skill_cd=3, event_id=event_id,
        event_time=event_time), 4)

    def sync(index):
        gamers[index] = pvp_gamer_with_state(gamers[index], hp=hp[index],
            virtual_hp=frenzy[index], ammo_number=real[index],
            fake_ammo_number=blank[index], enhanced_ammo_number=enhanced[index],
            round_number=round_number, is_dead=hp[index] + frenzy[index] <= 0)

    def small(source, destination):
        events.append(pb_message(pb_bytes(1, source), pb_bytes(2, destination),
                                 pb_varint(3, event_id), pb_varint(4, len(events) + 1)))

    def reload(index):
        reload_time = event_time + len(events) + 1
        gun_id = V(B(gamers[index], 7) or b'', 1) or 0
        r, b = pvp_gun_ammo_counts(gun_id, randomize=randomize_magazines)
        magazine = apply_reload_trait(gun_id, r, b)
        real[index], blank[index], enhanced[index] = magazine.real, magazine.blank, magazine.enhanced
        gamers[index] = pvp_gamer_after_weapon_reload(gamers[index]); sync(index)
        small(_pvp_event_outline(index, event_type=1, event_time=reload_time),
              _pvp_event_outline(index, event_type=1, is_reload=True,
                  r_ammo=_reload_ammo_messages(gamers[index], real[index], blank[index]),
                  event_time=reload_time))
        _append_reload_weapon_buff_event(events, gamers[index], event_id=event_id, event_time=reload_time)

    # Native Enum_Fix_Ammo_Befor_Duel permits the skill's extra round even
    # when the ordinary magazine is full. It is not an add-round shop item.
    added = 2 if upgraded else 1
    (enhanced if upgraded else real)[actor] += 1
    sync(actor)
    small(_pvp_event_outline(actor, event_type=52, event_time=event_time),
          _pvp_event_outline(actor, added, include_ammo=True, event_type=52,
              ammo_after=real[actor], fake_ammo_after=blank[actor],
              enhanced_ammo_after=enhanced[actor], event_time=event_time))
    shots = []
    shooter, victim = actor, target
    # Each blank shrinks a magazine. Arthur's added live round guarantees
    # termination; opponent reloads only if completely empty before its shot.
    while True:
        if real[shooter] + blank[shooter] + enhanced[shooter] == 0:
            reload(shooter)
        cfg = draw(real[shooter], blank[shooter], enhanced[shooter])
        gun_id = V(B(gamers[shooter], 7) or b'', 1) or 0
        cfg = prioritize_shot_ammo(gun_id, cfg, enhanced[shooter])
        pool = blank if cfg == 300 else real if cfg == 1 else enhanced if cfg == 2 else None
        if pool is None or pool[shooter] <= 0:
            raise ValueError('invalid duel draw')
        pool[shooter] -= 1
        hp_delta = frenzy_delta = 0
        blocked_katie = intercept_katie(gamers,katie_guards,shooter,victim,cfg) if katie_guards is not None else None
        if cfg != 300 and not blocked_katie:
            hp[victim], frenzy[victim], hp_delta, frenzy_delta = damage(
                hp[victim], frenzy[victim], 2 if cfg == 2 else 1)
        sync(shooter); sync(victim)
        shot = pvp_shoot_event_result_body(gamers[shooter], gamers[victim], shooter, victim,
            ammo_cfg_id=cfg, target_hp_delta=hp_delta, target_virtual_hp_delta=frenzy_delta,
            source_ammo_after=real[shooter], source_fake_ammo_after=blank[shooter],
            source_enhanced_ammo_after=enhanced[shooter],
            target_del_buff_cfgs=(blocked_katie,) if blocked_katie else (),
            target_dead=hp[victim] + frenzy[victim] <= 0,
            target_event_status=5 if hp[victim] + frenzy[victim] <= 0 else 0,
            event_id=event_id, event_time=event_time + len(events) + 1)
        events.append(Bs(shot, 4)[0])  # Native Enum_Shoot, no normal-fire final event.
        shots.append((shooter, victim, cfg))
        if cfg != 300:
            break
        shooter, victim = victim, shooter
    for index in (actor, target):
        if hp[index] + frenzy[index] > 0 and real[index] + enhanced[index] == 0:
            reload(index)
    packet = pb_message(pb_varint(1, 3), pb_varint(2, skill_id), pb_varint(3, actor),
        *(pb_bytes(4, e) for e in events), pb_varint(10, target),
        pb_bytes(11, gamers[target]), pb_bytes(12, gamers[actor]), pb_varint(13, event_id))
    # Presentation estimate: native opening plus alternating shot/reload time.
    wait = 5.0 + len(shots) * 2.5 + sum(V(B(e, 1), 9) == 1 for e in events) * 3.0
    return DuelResult(packet, tuple(shots), wait)
