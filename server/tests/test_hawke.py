import asyncio
import random
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1]))
import protocol as p
import test_protocol
from test_bot_ai import gamer, battle
from bot_ai import Decision
from hero_drone import resolve_drone
from hero_skills import hawke_load_count, effective_hero_skill
from katie_guard import activate
from server import _pvp_apply_hp_damage, serve_client, read_frame

V, B, Bs = p.parse_varint_field, p.parse_bytes_field, p.parse_bytes_fields


class HawkeTests(unittest.TestCase):
    _state = test_protocol.ProtocolTests._state

    def resolve(self, *, upgraded=True, real=3, red=0, hp=None, frenzy=None, rng=None, guards=None):
        gs = [gamer(i, hp=4, frenzy=0, skill=10039 if upgraded else 10038) for i in range(3)]
        hp = [4, 4, 4] if hp is None else hp
        frenzy = [0, 0, 0] if frenzy is None else frenzy
        r, b, e = [real, 1, 1], [2, 2, 2], [red, 0, 0]
        result = resolve_drone(gs, hp, frenzy, r, b, e, actor=0, upgraded=upgraded,
            rng=rng or random.Random(3), damage=_pvp_apply_hp_damage,
            round_number=1, event_id=1, event_time=100, katie_guards=guards)
        return result, gs, hp, frenzy, r, b, e

    def test_floor_ceil_every_count_and_red_inclusion(self):
        for count in range(9):
            self.assertEqual(hawke_load_count(count, 0, upgraded=False), count // 2)
            self.assertEqual(hawke_load_count(count, 0, upgraded=True), (count + 1) // 2)
            self.assertEqual(hawke_load_count(0, count, upgraded=True), (count + 1) // 2)
        self.assertEqual(hawke_load_count(-1, 2, upgraded=True), 0)

    def test_upgrade_unlock_preserves_save(self):
        for star, sid in ((0, 10038), (5, 10039)):
            entry = dict(id=38, skillId=10038, starLevel=star)
            self.assertEqual(effective_hero_skill(entry), sid)
            self.assertEqual(entry['skillId'], 10038)

    def test_odd_magazine_consumption_hit_count_and_native_events(self):
        for upgraded, expected in ((False, 1), (True, 2)):
            result, gs, hp, fr, r, b, e = self.resolve(upgraded=upgraded)
            self.assertEqual((sum(n for _, n in result.consumed), len(result.hits), r[0]), (expected, expected, 3-expected))
            self.assertEqual(b[0], 2)
            self.assertEqual(hp[0], 4)
            self.assertEqual(sum(hp[1:]), 8-expected)
            self.assertEqual(p.pvp_gamer_skill_cd(gs[0]), 3)
            packet = result.packet
            events = Bs(packet, 4)
            self.assertEqual([V(B(ev, 1), 9) for ev in events], [9, 86] + [87]*expected)
            self.assertEqual([V(g,3) for g in Bs(packet,11)], [1,2])
            self.assertEqual(V(B(events[1],2),1), 0)
            self.assertEqual(V(Bs(B(events[1],2),12)[0],2), expected)
            self.assertAlmostEqual(result.wait, 9.2)

    def test_random_targets_not_fixed_and_no_self_hits(self):
        targets = set()
        for seed in range(30):
            result, *_ = self.resolve(rng=random.Random(seed))
            targets.update(h[0] for h in result.hits)
        self.assertEqual(targets, {1,2})

    def test_dead_opponents_excluded_and_no_overkill_retarget(self):
        rng = random.Random(1); rng.choice = lambda targets: targets[0]
        result, gs, hp, fr, *_ = self.resolve(real=4, hp=[4,1,1], rng=rng)
        self.assertEqual([h[0] for h in result.hits], [1,2])
        self.assertEqual(hp, [4,0,0])
        self.assertTrue(all(h[3] for h in result.hits))
        self.assertEqual([V(g,12) or 0 for g in gs], [0,1,1])
        result, *_ = self.resolve(real=4, hp=[4,0,4], frenzy=[0,0,0])
        self.assertTrue(all(h[0]==2 for h in result.hits))

    def test_damage_spends_hp_then_frenzy_no_shooter_gain(self):
        result, _, hp, fr, *_ = self.resolve(real=4, hp=[4,0,0], frenzy=[1,2,0])
        self.assertEqual((hp,fr), ([4,0,0],[1,0,0]))
        self.assertEqual([h[2] for h in result.hits], [-1,-1])

    def test_red_rounds_do_not_multiply_drone_damage(self):
        result, _, hp, _, r, b, e = self.resolve(real=0, red=3)
        self.assertEqual(result.consumed, ((2,2),))
        self.assertEqual((e[0],r[0],b[0]), (1,0,2))
        self.assertEqual(sum(hp[1:]), 6)

    def test_upgrade_one_real_reloads_after_native_ammo_removal(self):
        result, gs, _, _, r, b, e = self.resolve(real=1)
        self.assertEqual(result.consumed, ((1,1),))
        self.assertEqual((r[0],b[0],e[0]), (3,3,0))
        self.assertAlmostEqual(result.wait,14.2)
        self.assertIn(1, [V(B(ev,1),9) for ev in Bs(result.packet,4)])

    def test_invalid_empty_basic_one_real_dead_actor_and_no_enemy_do_not_mutate(self):
        for real, upgraded, hp in ((0,True,[4,4]),(1,False,[4,4]),(3,True,[0,4]),(3,True,[4,0])):
            gs=[gamer(0),gamer(1)]; fr=[0,0]; r=[real,1]; b=[2,2]; e=[0,0]
            before=(list(gs),list(hp),list(fr),list(r),list(b),list(e))
            with self.assertRaises(ValueError):
                resolve_drone(gs,hp,fr,r,b,e,actor=0,upgraded=upgraded,rng=random.Random(1),
                    damage=_pvp_apply_hp_damage,round_number=1,event_id=1,event_time=100)
            self.assertEqual((gs,hp,fr,r,b,e),before)

    def test_katie_blocks_first_hit_only(self):
        a=battle(); a.hp=[4,4,4];a.frenzy=[0,0,0]; a.real[1]=3
        a.gamers[1]=gamer(1,skill=10039,cd=0)
        a.gamers[0]=activate(a.gamers[0],10031,0,a.katie_guards)
        a.rng.choice=lambda _:0
        packet,_=a.resolve(1,Decision('skill',1,4,'drone'),event_id=1,event_time=100)
        self.assertEqual(a.hp,[3,4,4]);self.assertNotIn(0,a.katie_guards)
        hits=[B(ev,2) for ev in Bs(packet,4) if V(B(ev,1),9)==87]
        self.assertEqual(V(Bs(hits[0],24)[0],1),10049)
        self.assertIsNone(V(hits[0],2))

    def test_bot_respects_skill_ban_and_does_not_consume_normal_shot_buffs(self):
        a=battle();a.gamers[1]=gamer(1,skill=10039,cd=0);a.real[1]=3
        a.burst[1]=1;a.maintenance[1]=1
        a.resolve(1,Decision('skill',1,4,'drone'),event_id=1,event_time=100)
        self.assertEqual((a.burst[1],a.maintenance[1]),(1,1))
        a.gamers[1]=p.pvp_gamer_with_buffs(gamer(1,skill=10039,cd=0),add_cfg_ids=(10018,))
        self.assertIsNone(a.resolve(1,Decision('skill',1,4,'ban'),event_id=2,event_time=101))

    def test_tcp_both_levels_hp_and_consumption(self):
        async def run(star, expected, lethal=False):
            state=self._state({'selectedHero':38,'heroes':[dict(id=38,skillId=10038,starLevel=star)],
                               'heroGuns':[dict(heroId=38,gunId=0)]})
            state._accounts={};state._next_gid=1000001;state.pvp_port=0
            listener=await asyncio.start_server(lambda r,w:serve_client(r,w,state,'body','pvp'),'127.0.0.1',0)
            r,w=await asyncio.open_connection('127.0.0.1',listener.sockets[0].getsockname()[1])
            def send(act,body,index):w.write(p.encode_frame(3,act,body,index=index,length_mode='body'))
            async def receive(cmd,act,index=0):
                async with asyncio.timeout(4):
                    while True:
                        h,b,_=await read_frame(r,'body')
                        if (h.cmd,h.act,h.index)==(cmd,act,index):return h,b
            try:
                with patch('server.PVP_OPENING_SEQUENCE_DELAY',0):
                    send(1,p.pb_bytes(2,'local-pvp:1:6:38:0'),901)
                    _,login=await receive(3,1,901)
                    before=Bs(B(login,2),2)
                    self.assertEqual(p.pvp_gamer_skill_id(before[0]),10039 if star else 10038)
                    send(14,b'',902);await receive(3,14,902);await receive(255,1)
                    with (patch('server.pvp_gamer_skill_cd',return_value=0),
                          patch('hero_drone.skill_animation_barrier',return_value=0),
                          patch('server.random.choice',side_effect=lambda choices: choices[0]),
                          patch('server._pvp_apply_hp_damage',side_effect=lambda hp,fr,d:
                                _pvp_apply_hp_damage(hp,fr,4 if lethal else d))):
                        send(6,p.pb_varint(1,1)+p.pb_varint(1,2),903)
                        h,_=await receive(3,6,903);self.assertEqual(h.error,0)
                        _,b=await receive(255,2)
                    gs=Bs(B(b,2),2); events=Bs(B(b,1),4)
                    self.assertEqual(sum(V(B(ev,1),9)==87 for ev in events),expected)
                    self.assertEqual(sum(V(g,4) for g in gs[1:]),0 if lethal else 8-expected)
                    rounds={V(a,1):V(a,2) for a in Bs(B(gs[0],7),2)}
                    self.assertEqual((rounds.get(1,0),rounds.get(300,0)),(3-expected,3))
                    self.assertEqual(p.pvp_gamer_skill_cd(gs[0]),3)
                    self.assertEqual(V(gs[0],17),0)
                    send(6,p.pb_varint(1,1),904)
                    h,_=await receive(3,6,904);self.assertNotEqual(h.error,0)
                    if lethal:
                        _,ended=await receive(255,5)
                        self.assertTrue(ended)
                        self.assertEqual([V(g,12) or 0 for g in gs],[0,1,1])
            finally:
                w.close();await w.wait_closed();listener.close();await listener.wait_closed()
        for star,expected in ((0,1),(5,2)):
            with self.subTest(star=star):asyncio.run(run(star,expected))
        with self.subTest(lethal=True):asyncio.run(run(5,2,True))
