import asyncio
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1]))
import test_protocol
import protocol
from fair_duel import resolve_fair_duel
from hero_skills import effective_hero_skill
from test_bot_ai import battle, gamer
from bot_ai import Decision
from protocol import (parse_varint_field as V, parse_bytes_field as B,
    parse_bytes_fields as Bs, pb_bytes, pb_varint, encode_frame,
    pvp_gamer_with_state, pvp_gamer_skill_cd, pvp_gamer_skill_id)
from server import _pvp_apply_hp_damage, serve_client, read_frame


class FairDuelTests(unittest.TestCase):
    _state = test_protocol.ProtocolTests._state

    def resolve(self, *, upgraded=True, draws=(2,), actor=0, target=1,
                real=None, blank=None, red=None, hp=None, frenzy=None, guns=None):
        real = list(real or [1, 1, 1]); blank = list(blank or [2, 2, 2])
        red = list(red or [0, 0, 0]); hp = list(hp or [4, 4, 4])
        frenzy = list(frenzy or [2, 2, 2])
        gamers = [gamer(i, hp=hp[i], frenzy=frenzy[i], skill=10014, cd=0) for i in range(3)]
        if guns is not None:
            for i, gun in enumerate(guns):
                gamers[i] = protocol.pb_message(
                    *(raw for n, w, v, raw in protocol._iter_pb_fields(gamers[i]) if n != 7),
                    pb_bytes(7, pb_varint(1, gun)))
        draws = iter(draws)
        result = resolve_fair_duel(gamers, hp, frenzy, real, blank, red,
            actor=actor, target=target, upgraded=upgraded,
            draw=lambda r, b, e: next(draws), damage=_pvp_apply_hp_damage,
            round_number=1, event_id=1, event_time=100)
        return result, gamers, hp, frenzy, real, blank, red

    def test_unlock_routes(self):
        for stars, purchased, expected in ((4, False, 10005), (5, False, 10014), (0, True, 10014)):
            entry = dict(id=14, skillId=10005, starLevel=stars, skillUpgradeUnlocked=purchased)
            original = dict(entry)
            self.assertEqual(effective_hero_skill(entry), expected)
            self.assertEqual(entry, original)

    def test_added_round_and_damage_basic_and_upgrade(self):
        for upgraded, cfg, dmg in ((False, 1, 1), (True, 2, 2)):
            result, gamers, hp, frenzy, real, blank, red = self.resolve(upgraded=upgraded, draws=(cfg,))
            self.assertEqual(hp, [4, 4 - dmg, 4])
            self.assertEqual(frenzy, [2, 2, 2])
            self.assertEqual(result.shots, ((0, 1, cfg),))
            add_event = next(e for e in Bs(result.packet, 4) if V(B(e, 1), 9) == 52)
            self.assertEqual(V(B(B(add_event, 2), 10), 1), cfg)
            self.assertEqual(pvp_gamer_skill_cd(gamers[0]), 3)

    def test_alternating_blanks_then_live_native_sequence(self):
        result, gamers, hp, frenzy, real, blank, red = self.resolve(draws=(300, 300, 2))
        self.assertEqual(result.shots, ((0, 1, 300), (1, 0, 300), (0, 1, 2)))
        self.assertEqual((hp, frenzy), ([4, 2, 4], [2, 2, 2]))
        self.assertEqual(blank, [1, 1, 2])
        events = Bs(result.packet, 4)
        self.assertEqual([V(B(e, 1), 9) for e in events], [9, 52, 2, 2, 2])
        self.assertEqual([V(B(e, 1), 1) for e in events[2:]], [0, 1, 0])
        self.assertEqual(V(result.packet, 1), 3)
        self.assertEqual(V(result.packet, 2), 10014)

    def test_opponent_can_win_and_added_red_remains(self):
        result, gamers, hp, frenzy, real, blank, red = self.resolve(draws=(300, 1))
        self.assertEqual(result.shots[-1], (1, 0, 1))
        self.assertEqual(hp[0], 3)
        self.assertEqual(red[0], 1)

    def test_reload_after_last_live_and_frenzy_overflow_damage(self):
        result, gamers, hp, frenzy, real, blank, red = self.resolve(
            draws=(2,), real=[0, 1, 1], hp=[4, 1, 4])
        self.assertEqual((hp[1], frenzy[1]), (0, 1))
        self.assertGreater(real[0] + red[0], 0)
        self.assertEqual(real[0] + blank[0] + red[0], 6)
        self.assertIn(1, [V(B(e, 1), 9) for e in Bs(result.packet, 4)])

    def test_elimination_only_when_both_pools_zero(self):
        result, gamers, hp, frenzy, real, blank, red = self.resolve(
            draws=(2,), hp=[4, 1, 4], frenzy=[2, 1, 2])
        self.assertEqual((hp[1], frenzy[1]), (0, 0))
        shot = next(e for e in Bs(result.packet, 4) if V(B(e, 1), 9) == 2)
        self.assertEqual(V(B(shot, 2), 68), 1)
        self.assertEqual(V(B(shot, 2), 63), 5)

    def test_no_self_duel(self):
        with self.assertRaises(ValueError): self.resolve(target=0)

    def test_grazier_exclusive_priority_and_correct_consumption(self):
        for gun in (0, 1, 7, 18, 31):
            with self.subTest(gun=gun):
                result, gamers, hp, frenzy, real, blank, red = self.resolve(
                    draws=(1,), guns=(gun, 0, 0))
                prioritized = gun in (7, 18, 31)
                self.assertEqual(result.shots[0][2], 2 if prioritized else 1)
                self.assertEqual(hp[1], 2 if prioritized else 3)
                self.assertEqual((real[0], red[0]), (1, 0) if prioritized else (0, 1))

    def test_grazier_keeps_blanks_and_falls_back_without_red(self):
        result, gamers, hp, frenzy, real, blank, red = self.resolve(
            draws=(300, 300, 1), guns=(7, 0, 0))
        self.assertEqual(result.shots, ((0, 1, 300), (1, 0, 300), (0, 1, 2)))
        self.assertEqual(blank[:2], [1, 1])
        result, gamers, hp, frenzy, real, blank, red = self.resolve(
            upgraded=False, draws=(1,), guns=(7, 0, 0))
        self.assertEqual(result.shots, ((0, 1, 1),))
        self.assertEqual(hp[1], 3)

    def test_priority_uses_current_shooter_not_duel_initiator(self):
        result, gamers, hp, frenzy, real, blank, red = self.resolve(
            draws=(300, 1), guns=(0, 7, 0), red=[0, 1, 0])
        self.assertEqual(result.shots, ((0, 1, 300), (1, 0, 2)))
        self.assertEqual(hp[0], 2)
        self.assertEqual((real[1], red[1]), (1, 0))

    def test_bot_uses_same_duel_and_preserves_item_modifiers(self):
        actions = battle(); actions.gamers[1] = gamer(1, hp=4, skill=10014, cd=0)
        actions.hp[1] = 4; actions.hp[2] = 4
        actions.maintenance[1] = 1; actions.burst[1] = 1
        with patch.object(actions.rng, 'randrange', return_value=6):
            packet, wait = actions.resolve(1, Decision('skill', 2, 4, 'test'), event_id=1, event_time=100)
        self.assertEqual(actions.hp[2], 2)
        self.assertEqual((actions.maintenance[1], actions.burst[1]), (1, 1))
        self.assertEqual(V(packet, 2), 10014)
        self.assertGreater(wait, 4)

    def test_tcp_alternation_hud_and_cd(self):
        async def exchange():
            state = self._state({'selectedHero': 14,
                'heroes': [dict(id=14, starLevel=5, skillId=10005)],
                'heroGuns': [dict(heroId=14, gunId=7)]})
            state._accounts = {}; state._next_gid = 1000001; state.pvp_port = 0
            original = protocol._local_pvp_gamer
            def prepared(*args, **kwargs):
                g = original(*args, **kwargs)
                return pvp_gamer_with_state(g, hp=4, virtual_hp=2,
                    ammo_number=1, fake_ammo_number=2, round_number=1)
            listener = await asyncio.start_server(lambda r, w: serve_client(r, w, state, 'body', 'pvp'), '127.0.0.1', 0)
            reader, writer = await asyncio.open_connection('127.0.0.1', listener.sockets[0].getsockname()[1])
            async def receive(cmd, act, index=0):
                async with asyncio.timeout(4):
                    while True:
                        head, body, _ = await read_frame(reader, 'body')
                        if (head.cmd, head.act, head.index) == (cmd, act, index): return head, body
            def request(act, body, index):
                writer.write(encode_frame(3, act, body, index=index, length_mode='body'))
            try:
                with patch('protocol._local_pvp_gamer', side_effect=prepared), \
                     patch('server.PVP_OPENING_SEQUENCE_DELAY', 0):
                    request(1, pb_bytes(2, 'local-pvp:1:6:14:0'), 911)
                    _, login = await receive(3, 1, 911)
                    self.assertEqual(pvp_gamer_skill_id(Bs(B(login, 2), 2)[0]), 10014)
                    request(14, b'', 912); await receive(3, 14, 912); await receive(255, 1)
                    with patch('server.pvp_gamer_skill_cd', return_value=0), \
                         patch('server._draw_loaded_ammo', side_effect=(300, 300, 1)):
                        request(6, pb_varint(1, 0), 913)
                        head, _ = await receive(3, 6, 913); self.assertNotEqual(head.error, 0)
                        request(6, pb_varint(1, 1), 914)
                        head, _ = await receive(3, 6, 914); self.assertEqual(head.error, 0)
                        _, notification = await receive(255, 2)
                    event, info = B(notification, 1), B(notification, 2)
                    self.assertEqual([V(B(e, 1), 1) for e in Bs(event, 4) if V(B(e, 1), 9) == 2], [0, 1, 0])
                    self.assertEqual([V(B(B(e, 1), 10) or b'', 1) for e in Bs(event, 4)
                                      if V(B(e, 1), 9) == 2], [300, 300, 2])
                    fighters = Bs(info, 2)
                    self.assertEqual([V(g, 4) for g in fighters], [4, 2, 4])
                    self.assertEqual(pvp_gamer_skill_cd(fighters[0]), 3)
                    request(6, pb_varint(1, 1), 915)
                    head, _ = await receive(3, 6, 915); self.assertNotEqual(head.error, 0)
            finally:
                writer.close(); await writer.wait_closed(); listener.close(); await listener.wait_closed()
        asyncio.run(exchange())
