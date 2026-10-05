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
from hero_skills import vera_round, effective_hero_skill
from server import serve_client, read_frame

V, B, Bs = p.parse_varint_field, p.parse_bytes_field, p.parse_bytes_fields


class VeraTests(unittest.TestCase):
    _state = test_protocol.ProtocolTests._state

    def test_basic_weights_by_round_upgrade_prioritizes_red(self):
        self.assertEqual([vera_round(2, 1, upgraded=False, randrange=lambda _: i)
                          for i in range(3)], [1, 1, 2])
        self.assertEqual(vera_round(2, 1, upgraded=True, randrange=lambda _: 0), 2)
        self.assertEqual(vera_round(2, 0, upgraded=True, randrange=lambda _: 0), 1)
        self.assertIsNone(vera_round(0, 0, upgraded=True, randrange=lambda _: 0))

    def test_upgrade_selection_preserves_save(self):
        for star, expected in ((0, 10035), (5, 10036)):
            entry = dict(id=36, skillId=10035, starLevel=star)
            self.assertEqual(effective_hero_skill(entry), expected)
            self.assertEqual(entry['skillId'], 10035)

    def action(self, skill=10036, target_real=2, target_red=1):
        a = battle(); a.gamers[1] = gamer(1, skill=skill, cd=0)
        a.real[1], a.blank[1] = 1, 1
        a.real[0], a.enhanced[0] = target_real, target_red
        return a

    def test_bot_transfers_one_and_keeps_red_type_with_two_native_callbacks(self):
        for skill in (10035, 10036):
            a = self.action(skill)
            if skill == 10035: a.rng.randrange = lambda _: 2
            before = (sum(a.real), sum(a.enhanced), sum(a.blank))
            packet, wait = a.resolve(1, Decision('skill', 0, 3, 'steal'), event_id=1, event_time=100)
            self.assertEqual((sum(a.real), sum(a.enhanced), sum(a.blank)), before)
            self.assertEqual((a.real[0], a.enhanced[0], a.enhanced[1]), (2, 0, 1))
            self.assertEqual(p.pvp_gamer_skill_cd(a.gamers[1]), 2)
            self.assertEqual(wait, 5)
            pop, add = Bs(packet, 4)[1:3]
            self.assertEqual((V(B(pop, 1), 1), V(B(pop, 2), 1), V(B(pop, 1), 9)), (0, 0, 13))
            self.assertEqual(V(Bs(B(pop, 2), 12)[0], 1), 2)
            self.assertEqual((V(B(add, 1), 1), V(B(add, 2), 1), V(B(add, 1), 9)), (1, 1, 77))
            self.assertEqual(V(B(B(add, 2), 10), 1), 2)

    def test_last_live_round_reloads_victim_after_pop_and_add(self):
        a = self.action(target_real=1, target_red=0)
        packet, wait = a.resolve(1, Decision('skill', 0, 3, 'steal'), event_id=1, event_time=100)
        self.assertEqual((a.real[1], a.real[0], a.blank[0]), (2, 2, 2))
        self.assertEqual(wait, 10)
        self.assertEqual([V(B(e, 1), 9) for e in Bs(packet, 4)][:4], [9, 13, 77, 1])
        self.assertEqual(V(B(Bs(packet, 4)[3], 2), 8), 1)

    def test_self_full_empty_banned_and_dead_are_rejected_without_mutation(self):
        for case in ('self', 'full', 'empty', 'banned', 'dead'):
            a = self.action(); target = 0
            if case == 'self': target = 1
            if case == 'full': a.real[1], a.blank[1] = 2, 4
            if case == 'empty': a.real[0], a.enhanced[0] = 0, 0
            if case == 'banned': a.gamers[1] = p.pvp_gamer_with_buffs(a.gamers[1], add_cfg_ids=(10018,))
            if case == 'dead': a.hp[0], a.frenzy[0] = 0, 0
            before = (list(a.real), list(a.blank), list(a.enhanced), list(a.gamers))
            self.assertIsNone(a.resolve(1, Decision('skill', target, 3, 'invalid'), event_id=1, event_time=100))
            self.assertEqual((a.real, a.blank, a.enhanced, a.gamers), before)

    def test_tcp_both_levels_transfer_and_reset_two_charges(self):
        async def run(star):
            state = self._state({'selectedHero': 36, 'heroes': [dict(id=36, skillId=10035, starLevel=star)],
                                 'heroGuns': [dict(heroId=36, gunId=0)]})
            state._accounts = {}; state._next_gid = 1000001; state.pvp_port = 0
            listener = await asyncio.start_server(lambda r,w: serve_client(r,w,state,'body','pvp'), '127.0.0.1', 0)
            r,w = await asyncio.open_connection('127.0.0.1', listener.sockets[0].getsockname()[1])
            def send(act, body, index): w.write(p.encode_frame(3, act, body, index=index, length_mode='body'))
            async def receive(cmd, act, index=0):
                async with asyncio.timeout(4):
                    while True:
                        h,b,_ = await read_frame(r,'body')
                        if (h.cmd,h.act,h.index) == (cmd,act,index): return h,b
            try:
                # Synthetic magazines leave space; actual game starts with a full gun.
                with patch('server.PVP_OPENING_SEQUENCE_DELAY',0), patch('protocol.pvp_gun_ammo_counts',return_value=(2,2)):
                    send(1,p.pb_bytes(2,'local-pvp:1:6:36:0'),901)
                    _,login = await receive(3,1,901)
                    before = Bs(B(login,2),2)
                    self.assertEqual(p.pvp_gamer_skill_id(before[0]),10036 if star==5 else 10035)
                    self.assertEqual(p.pvp_gamer_skill_cd(before[0]),2)
                    send(14,b'',902); await receive(3,14,902); await receive(255,1)
                    with patch('server.pvp_gamer_skill_cd',return_value=0), patch('server.skill_animation_barrier',return_value=0):
                        send(6,p.pb_varint(1,0),903)
                        h,_ = await receive(3,6,903); self.assertNotEqual(h.error,0)
                        send(6,p.pb_varint(1,1),904)
                        h,_ = await receive(3,6,904); self.assertEqual(h.error,0)
                        _,b = await receive(255,2)
                    after = Bs(B(b,2),2)
                    def rounds(g): return {V(a,1):V(a,2) for a in Bs(B(g,7),2)}
                    self.assertEqual(rounds(after[0]).get(1,0),rounds(before[0]).get(1,0)+1)
                    self.assertEqual(rounds(after[1]).get(1,0),rounds(before[1]).get(1,0)-1)
                    self.assertEqual(p.pvp_gamer_skill_cd(after[0]),2)
                    self.assertEqual([V(B(e,1),9) for e in Bs(B(b,1),4)][:3],[9,13,77])
                    send(6,p.pb_varint(1,1),905)
                    h,_ = await receive(3,6,905); self.assertNotEqual(h.error,0)
            finally:
                w.close(); await w.wait_closed(); listener.close(); await listener.wait_closed()
        for star in (0,5):
            with self.subTest(star=star): asyncio.run(run(star))
