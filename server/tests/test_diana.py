"""Diana native skill, normal-shot effects and local trio protocol regression."""
import asyncio
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1]))
import protocol as p
import test_protocol
from test_bot_ai import gamer, battle
from bot_ai import Decision, candidates
from hero_skills import DIANA_SKILLS, DIANA_BUFFS, diana_hit, effective_hero_skill
from bot_presentation import skill_animation_barrier
from server import (serve_client, read_frame, _pvp_diana_after_normal_shot,
                    _pvp_expire_diana_turn, _pvp_apply_hp_damage, _pvp_is_eliminated)

V, B, Bs = p.parse_varint_field, p.parse_bytes_field, p.parse_bytes_fields


def signed(message, field):
    value = V(message, field)
    return value - (1 << 64) if value is not None and value >= 1 << 63 else value


def empowered(g, skill=10033, actor=0):
    return p.pvp_gamer_with_buffs(g, add_cfg_ids=(DIANA_BUFFS[DIANA_SKILLS.index(skill)],),
                                  source_index=actor)


class DianaTests(unittest.TestCase):
    _state = test_protocol.ProtocolTests._state

    def test_upgrade_does_not_mutate_save(self):
        for star, skill in ((0, 10032), (5, 10033)):
            entry = dict(id=35, skillId=10032, starLevel=star)
            self.assertEqual(effective_hero_skill(entry), skill)
            self.assertEqual(entry['skillId'], 10032)
        self.assertEqual(effective_hero_skill(dict(id=35, skillId=10033)), 10033)

    def test_basic_one_point_upgrade_two_points_and_one_slot_clamped(self):
        for upgraded in (False, True):
            for cap in range(6):
                for frenzy in range(cap + 1):
                    remaining, new_cap, delta, cap_delta = diana_hit(
                        frenzy, cap, upgraded=upgraded, eligible=True)
                    removed = min(frenzy, 1 + int(upgraded and cap > 0))
                    self.assertEqual(remaining, frenzy - removed)
                    self.assertEqual(new_cap, max(0, cap - int(upgraded)))
                    self.assertEqual(delta, -removed)
                    self.assertEqual(cap_delta, -int(upgraded and cap > 0))

    def test_only_damaging_enemy_normal_shots(self):
        for cfg, source, target, hp_delta, fr_delta, active in (
            (300, 0, 1, 0, 0, True), (1, 0, 0, -1, 0, True),
            (1, 0, 1, 0, 0, True), (1, 0, 1, -1, 0, False)):
            gs = [gamer(0), gamer(1)]
            if active: gs[0] = empowered(gs[0])
            fr = [1, 1]
            self.assertEqual(_pvp_diana_after_normal_shot(gs, fr, source, target,
                cfg, hp_delta, fr_delta), (0, 0))
            self.assertEqual(fr, [1, 1])
            self.assertEqual(V(gs[1], 23), 2)

    def test_live_red_and_burst_hits_each_reduce_capacity(self):
        gs = [empowered(gamer(0)), gamer(1, frenzy=2)]
        fr = [0, 2]
        for cfg, expected in ((1, (-2, -1)), (2, (0, -1))):
            self.assertEqual(_pvp_diana_after_normal_shot(gs, fr, 0, 1, cfg, -1, 0), expected)
        self.assertEqual((fr[1], V(gs[1], 23)), (0, 0))
        self.assertEqual(_pvp_diana_after_normal_shot(gs, fr, 0, 1, 1, -1, 0), (0, 0))

    def test_basic_preserves_capacity_and_upgrade_affects_empty_slot(self):
        for skill, expected_cap in ((10032, 2), (10033, 1)):
            gs = [empowered(gamer(0), skill), gamer(1)]
            fr = [0, 0]
            _pvp_diana_after_normal_shot(gs, fr, 0, 1, 1, -1, 0)
            self.assertEqual((fr[1], V(gs[1], 23)), (0, expected_cap))

    def test_bot_hits_other_bot_or_human_with_same_rules(self):
        for target in (0, 2):
            gs = [gamer(i) for i in range(3)]
            gs[1] = empowered(gs[1], actor=1)
            fr = [1, 1, 1]
            self.assertEqual(_pvp_diana_after_normal_shot(gs, fr, 1, target, 1, -1, 0), (-1, -1))
            self.assertEqual((fr[target], V(gs[target], 23)), (0, 1))
            self.assertEqual(fr[1], 1)

    def test_reported_two_full_skulls_become_one_empty_slot_with_native_deltas(self):
        gs = [empowered(gamer(0)), gamer(1, hp=4, frenzy=2)]
        fr = [0, 2]
        hp, fr[1], hd, fd = _pvp_apply_hp_damage(4, fr[1], 1)
        extra, cap_delta = _pvp_diana_after_normal_shot(gs, fr, 0, 1, 1, hd, fd)
        self.assertEqual((hp, fr[1], V(gs[1], 23)), (3, 0, 1))
        packet = p.pvp_shoot_event_result_body(gs[0], gs[1], 0, 1,
            target_hp_delta=hd, target_virtual_hp_delta=fd + extra,
            target_virtual_hp_cap_delta=cap_delta)
        outline = B(Bs(packet, 4)[0], 2)
        self.assertEqual((signed(outline, 2), signed(outline, 14), signed(outline, 19)), (-1, -2, -1))

    def test_effect_applied_before_elimination(self):
        gs = [empowered(gamer(0)), gamer(1, hp=0, frenzy=2)]
        hp, fr, hd, fd = _pvp_apply_hp_damage(0, 2, 1)
        frenzy = [0, fr]
        extra, _ = _pvp_diana_after_normal_shot(gs, frenzy, 0, 1, 1, hd, fd)
        self.assertEqual((hd, fd + extra), (0, -2))
        self.assertTrue(_pvp_is_eliminated(hp, frenzy[1]))

    def test_cap_snapshot_preserves_every_other_field(self):
        g = empowered(gamer(1))
        updated = p.pvp_gamer_with_frenzy_cap(g, 0)
        self.assertEqual(V(updated, 23), 0)
        self.assertEqual([raw for n, _, _, raw in p._iter_pb_fields(g) if n != 23],
                         [raw for n, _, _, raw in p._iter_pb_fields(updated) if n != 23])
        updated = p.pvp_gamer_with_state(updated, hp=2, virtual_hp=0,
            ammo_number=1, fake_ammo_number=2, round_number=2)
        self.assertEqual(V(updated, 23), 0)

    def test_expiry_once_keeps_other_buffs_and_capacity(self):
        g = p.pvp_gamer_with_buffs(empowered(gamer(0)), add_cfg_ids=(5002,))
        gs = [p.pvp_gamer_with_frenzy_cap(g, 1), gamer(1)]
        self.assertEqual(_pvp_expire_diana_turn(gs), [(0, (10052,))])
        self.assertEqual(_pvp_expire_diana_turn(gs), [])
        self.assertEqual([V(b, 1) for b in Bs(gs[0], 8)], [5002])
        self.assertEqual(V(gs[0], 23), 1)

    def test_packet_uses_signed_native_cap_delta_per_hit(self):
        packet = p.pvp_shoot_event_result_body(gamer(0), gamer(1), 0, 1,
            target_hp_delta=-1, target_virtual_hp_delta=-1, target_virtual_hp_cap_delta=-1,
            additional_shots=((1, -1, 0, 1, False),),
            additional_virtual_hp_deltas=(-1,), additional_virtual_hp_cap_deltas=(-1,))
        outlines = [B(e, 2) for e in Bs(packet, 4) if V(B(e, 1), 9) == 2]
        self.assertEqual(len(outlines), 2)
        for out in outlines:
            self.assertEqual((signed(out, 2), signed(out, 14), signed(out, 19)), (-1, -1, -1))

    def test_bot_native_activation_and_duplicate_or_banned_rejection(self):
        for skill, buff in zip(DIANA_SKILLS, DIANA_BUFFS):
            a = battle(); a.gamers[1] = gamer(1, skill=skill, cd=0)
            packet, wait = a.resolve(1, Decision('skill', 1, 3, 'hunt'), event_id=1, event_time=100)
            self.assertEqual(wait, 5.5)
            self.assertEqual(V(Bs(B(Bs(packet, 4)[1], 2), 25)[0], 1), buff)
            self.assertEqual(p.pvp_gamer_skill_cd(a.gamers[1]), 3)
            self.assertFalse(any(d.kind == 'skill' for d in candidates(a.observation(1))))
            self.assertIsNone(a.resolve(1, Decision('skill', 1, 3, 'repeat'), event_id=2, event_time=101))
            a.gamers[1] = p.pvp_gamer_with_buffs(gamer(1, skill=skill, cd=0), add_cfg_ids=(10018,))
            self.assertIsNone(a.resolve(1, Decision('skill', 1, 3, 'banned'), event_id=2, event_time=101))

    def test_tcp_activation_ordinary_shot_cap_and_turn_expiry_both_levels(self):
        async def run(star, expected_skill, expected_buff):
            state = self._state({'selectedHero': 35, 'heroes': [dict(id=35, skillId=10032, starLevel=star)]})
            state._accounts = {}; state._next_gid = 1000001; state.pvp_port = 0
            listener = await asyncio.start_server(lambda r, w: serve_client(r, w, state, 'body', 'pvp'), '127.0.0.1', 0)
            r, w = await asyncio.open_connection('127.0.0.1', listener.sockets[0].getsockname()[1])
            def send(act, body, index): w.write(p.encode_frame(3, act, body, index=index, length_mode='body'))
            async def receive(cmd, act, index=0):
                async with asyncio.timeout(4):
                    while True:
                        h, b, _ = await read_frame(r, 'body')
                        if (h.cmd, h.act, h.index) == (cmd, act, index): return h, b
            try:
                with patch('server.PVP_OPENING_SEQUENCE_DELAY', 0):
                    send(1, p.pb_bytes(2, 'local-pvp:1:6:35:0'), 901)
                    _, b = await receive(3, 1, 901)
                    self.assertEqual(p.pvp_gamer_skill_id(Bs(B(b, 2), 2)[0]), expected_skill)
                    send(14, b'', 902); await receive(3, 14, 902); await receive(255, 1)
                    with patch('server.pvp_gamer_skill_cd', return_value=0):
                        send(6, p.pb_varint(1, 1), 903)
                        h, _ = await receive(3, 6, 903); self.assertNotEqual(h.error, 0)
                        with patch('server.skill_animation_barrier', return_value=0):
                            send(6, p.pb_varint(1, 0), 904)
                            h, _ = await receive(3, 6, 904); self.assertEqual(h.error, 0)
                            _, b = await receive(255, 2)
                    g = Bs(B(b, 2), 2)[0]
                    self.assertIn(expected_buff, [V(b, 1) for b in Bs(g, 8)])
                    self.assertEqual(p.pvp_gamer_skill_cd(g), 3)
                    send(6, p.pb_varint(1, 0), 905)
                    h, _ = await receive(3, 6, 905); self.assertNotEqual(h.error, 0)
                    with (patch('server._draw_loaded_ammo', return_value=300),
                          patch('server.PREPARE_SIGNAL_DELAY', 0.001),
                          patch('server.PLAYER_CONTINUE_SHOT_SETTLE', 0.002)):
                        send(3, p.pb_varint(1, 0), 907)
                        h, _ = await receive(3, 3, 907); self.assertEqual(h.error, 0)
                        _, blank = await receive(255, 2)
                        blank_g = Bs(B(blank, 2), 2)[0]
                        self.assertIn(expected_buff, [V(buff, 1) for buff in Bs(blank_g, 8)])
                        self.assertEqual(V(blank_g, 23), 2)
                        with self.assertRaises(asyncio.TimeoutError):
                            await asyncio.wait_for(read_frame(r, 'body'), timeout=0.02)
                    with patch('server._draw_loaded_ammo', return_value=1):
                        send(3, p.pb_varint(1, 1), 906)
                        h, _ = await receive(3, 3, 906); self.assertEqual(h.error, 0)
                        _, b = await receive(255, 2)
                    result = B(b, 1)
                    out = B(Bs(result, 4)[0], 2)
                    self.assertEqual(signed(out, 2), -1)
                    self.assertEqual(signed(out, 19), -1 if star == 5 else None)
                    snapshot = Bs(B(b, 2), 2)
                    self.assertEqual(V(snapshot[1], 23), 1 if star == 5 else 2)
                    # Transition notification must clear the source buff before another actor acts.
                    _, expiry = await receive(255, 2)
                    removed = [V(buff, 1) for e in Bs(B(expiry, 1), 4) for buff in Bs(B(e, 2), 24)]
                    self.assertIn(expected_buff, removed)
                    self.assertNotIn(expected_buff, [V(buff, 1) for buff in Bs(Bs(B(expiry, 2), 2)[0], 8)])
            finally:
                w.close(); await w.wait_closed(); listener.close(); await listener.wait_closed()
        for star, skill, buff in ((0, 10032, 10051), (5, 10033, 10052)):
            with self.subTest(star=star): asyncio.run(run(star, skill, buff))
