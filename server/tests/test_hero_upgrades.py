import asyncio
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1]))
from hero_skills import effective_hero_skill, bear_conversion
from protocol import (pb_message, pb_varint, pb_bytes, _hero_message,
    parse_varint_field as V, parse_bytes_field as B, parse_bytes_fields as Bs,
    pvp_gamer_with_state, pvp_gamer_with_buffs, encode_frame, pvp_gamer_skill_id)
from test_bot_ai import battle, gamer
from bot_ai import Decision
import test_protocol
from server import serve_client, read_frame
import protocol


class HeroUpgradeTests(unittest.TestCase):
    _state = test_protocol.ProtocolTests._state

    def test_unlock_either_route_without_mutating_inventory(self):
        for stars, purchased, skill in ((0, False,10001),(4,False,10001),
                                       (5,False,10004),(0,True,10004)):
            entry = dict(id=1, starLevel=stars, skillId=10001, skillUpgradeUnlocked=purchased)
            original = dict(entry)
            self.assertEqual(effective_hero_skill(entry),skill)
            self.assertEqual(V(_hero_message(entry),4),skill)
            self.assertEqual(entry,original)
        self.assertEqual(effective_hero_skill(dict(id=0,starLevel=5,skillId=10000)),10003)

    def test_conversion_boundaries(self):
        for hp,frenzy,healed,spent in ((3,2,1,1),(0,2,2,2),(4,2,0,0),(2,0,0,0),(1,5,3,3)):
            self.assertEqual(bear_conversion(hp,frenzy,upgraded=True),(healed,spent))
            self.assertEqual(bear_conversion(hp,frenzy,upgraded=False),(healed,frenzy))

    def test_bot_executor_and_toxin(self):
        for poisoned in (False,True):
            actions=battle();actions.hp[1]=3;actions.frenzy[1]=2
            actions.gamers[1]=gamer(1,skill=10004,cd=0)
            if poisoned:
                actions.gamers[1]=pvp_gamer_with_buffs(actions.gamers[1],add_cfg_ids=(10066,))
            packet,wait=actions.resolve(1,Decision('skill',1,4,'test'),event_id=1,event_time=100)
            self.assertEqual((actions.hp[1],actions.frenzy[1]),(3 if poisoned else 4,1))
            self.assertEqual(V(packet,2),10004)
            self.assertGreater(wait,4)

    def test_live_login_and_skill_preserves_excess(self):
        state=self._state({'selectedHero':1,'heroes':[dict(id=1,starLevel=5,skillId=10001)],
                           'heroGuns':[dict(heroId=1,gunId=1)]})
        state._accounts={};state._next_gid=1000001;state.pvp_port=0
        original=protocol._local_pvp_gamer
        def prepared(*args,**kwargs):
            g=original(*args,**kwargs)
            if V(g,3)==0:
                g=pvp_gamer_with_state(g,hp=3,ammo_number=2,fake_ammo_number=2,
                                       virtual_hp=2,round_number=1)
            return g
        async def exchange():
            listener=await asyncio.start_server(lambda r,w:serve_client(r,w,state,'body','pvp'),'127.0.0.1',0)
            reader,writer=await asyncio.open_connection('127.0.0.1',listener.sockets[0].getsockname()[1])
            async def receive(cmd,act,index=0):
                async with asyncio.timeout(4):
                    while True:
                        head,body,_=await read_frame(reader,'body')
                        if (head.cmd,head.act,head.index)==(cmd,act,index):return head,body
            def request(act,body,index):writer.write(encode_frame(3,act,body,index=index,length_mode='body'))
            try:
                request(1,pb_bytes(2,'local-pvp:1:6:1:0'),701)
                _,login=await receive(3,1,701)
                self.assertEqual(pvp_gamer_skill_id(Bs(B(login,2),2)[0]),10004)
                request(14,b'',702);await receive(3,14,702);await receive(255,1)
                request(6,pb_varint(1,0),703)
                head,_=await receive(3,6,703);self.assertEqual(head.error,0)
                _,notification=await receive(255,2)
                self.assertEqual(V(B(notification,1),2),10004)
                player=Bs(B(notification,2),2)[0]
                self.assertEqual((V(player,4),V(player,17)),(4,1))
            finally:
                writer.close();await writer.wait_closed();listener.close();await listener.wait_closed()
        with patch('protocol._local_pvp_gamer',side_effect=prepared), \
             patch('server.pvp_gamer_skill_cd',return_value=0), \
             patch('server.PVP_OPENING_SEQUENCE_DELAY',0):
            asyncio.run(exchange())
