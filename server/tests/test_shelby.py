import asyncio
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1]))
import protocol
import test_protocol
from hero_skills import effective_hero_skill, battle_hero_skill, shelby_trade
from test_bot_ai import battle, gamer
from bot_ai import Decision
from protocol import parse_varint_field as V, parse_bytes_field as B, parse_bytes_fields as Bs
from server import serve_client, read_frame


class ShelbyTests(unittest.TestCase):
    _state = test_protocol.ProtocolTests._state

    def test_unlock_and_mode_do_not_mutate_save(self):
        entry = dict(id=15, skillId=10020, starLevel=5)
        self.assertEqual(effective_hero_skill(entry), 10021)
        self.assertEqual(battle_hero_skill(10021, shop_trio=True), 10027)
        self.assertEqual(entry['skillId'], 10020)
        self.assertEqual(effective_hero_skill(dict(id=15, skillId=10020, starLevel=4)), 10020)

    def test_trade_costs_and_frenzy(self):
        for skill, scale in ((10020, 1), (10024, 10), (10026, 100)):
            self.assertEqual(shelby_trade(2, 0, 1000, 1, skill), (-1, 0, 5 * scale))
            self.assertEqual(shelby_trade(0, 2, 1000, 1, skill), (0, -1, 5 * scale))
            self.assertEqual(shelby_trade(2, 0, 1000, 2, skill), (1, 0, -3 * scale))

    def test_guards(self):
        for args in ((1, 0, 1000, 1, 10027), (0, 1, 1000, 1, 10027),
                     (0, 0, 1000, 2, 10027), (4, 2, 1000, 2, 10027),
                     (2, 1, 299, 2, 10027), (2, 1, 1000, 3, 10027),
                     (0, 2, 1000, 2, 10026)):
            self.assertIsNone(shelby_trade(*args))
        self.assertEqual(shelby_trade(0, 2, 300, 2, 10027), (1, 0, -300))

    def test_bot_same_trade_and_effect_validation(self):
        a = battle(); a.gamers[1] = gamer(1, hp=2, skill=10027, cd=0)
        self.assertIsNone(a.resolve(1, Decision('skill', 1, 4, 'forged', effect=9), event_id=1, event_time=100))
        packet, wait = a.resolve(1, Decision('skill', 1, 4, 'heal', effect=2), event_id=1, event_time=100)
        self.assertEqual((a.hp[1], V(a.gamers[1], 5)), (3, 9700))
        self.assertEqual(protocol.pvp_gamer_skill_cd(a.gamers[1]), 2)
        self.assertEqual([V(B(e, 2), 9) for e in Bs(packet, 4)], [9, 48, 61])
        self.assertEqual(V(B(Bs(packet, 4)[1], 2), 47), 2)
        self.assertEqual(wait, 7)

    def test_tcp_both_effects_snapshots_and_rejection(self):
        async def run(effect):
            state = self._state({'selectedHero': 15,
                'heroes': [dict(id=15, starLevel=5, skillId=10020)]})
            state._accounts = {}; state._next_gid = 1000001; state.pvp_port = 0
            original = protocol._local_pvp_gamer
            def prepared(*args, **kwargs):
                return protocol.pvp_gamer_with_state(original(*args, **kwargs), hp=2, virtual_hp=2,
                    ammo_number=1, fake_ammo_number=2, round_number=1)
            listener = await asyncio.start_server(lambda r,w: serve_client(r,w,state,'body','pvp'), '127.0.0.1',0)
            r,w = await asyncio.open_connection('127.0.0.1', listener.sockets[0].getsockname()[1])
            def send(act, body, index):
                w.write(protocol.encode_frame(3,act,body,index=index,length_mode='body'))
            async def receive(cmd,act,index=0):
                async with asyncio.timeout(4):
                    while True:
                        h,b,_ = await read_frame(r,'body')
                        if (h.cmd,h.act,h.index)==(cmd,act,index): return h,b
            try:
                with patch('protocol._local_pvp_gamer',side_effect=prepared), patch('server.PVP_OPENING_SEQUENCE_DELAY',0):
                    send(1,protocol.pb_bytes(2,'local-pvp:1:6:15:0'),901)
                    _,b=await receive(3,1,901)
                    self.assertEqual(protocol.pvp_gamer_skill_id(Bs(B(b,2),2)[0]),10027)
                    send(14,b'',902); await receive(3,14,902); await receive(255,1)
                    with patch('server.pvp_gamer_skill_cd',return_value=0):
                        send(6,protocol.pb_varint(1,0)+protocol.pb_varint(3,9),903)
                        h,_=await receive(3,6,903); self.assertNotEqual(h.error,0)
                        send(6,protocol.pb_varint(1,0)+protocol.pb_varint(3,effect),904)
                        h,_=await receive(3,6,904); self.assertEqual(h.error,0)
                        _,b=await receive(255,2)
                    g=Bs(B(b,2),2)[0]
                    self.assertEqual(V(g,4),1 if effect==1 else 3)
                    self.assertEqual(V(g,5),10500 if effect==1 else 9700)
                    self.assertEqual(protocol.pvp_gamer_skill_cd(g),2)
                    events=Bs(B(b,1),4)
                    self.assertEqual(V(B(events[1],2),47),effect)
                    send(6,protocol.pb_varint(1,0)+protocol.pb_varint(3,effect),905)
                    h,_=await receive(3,6,905); self.assertNotEqual(h.error,0)
            finally:
                w.close(); await w.wait_closed(); listener.close(); await listener.wait_closed()
        for effect in (1,2): asyncio.run(run(effect))
