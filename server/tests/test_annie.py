import asyncio
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).parents[1]))
import protocol
import test_protocol
from hero_skills import annie_convert, effective_hero_skill
from test_bot_ai import battle, gamer
from bot_ai import Decision
from protocol import parse_varint_field as V, parse_bytes_field as B, parse_bytes_fields as Bs
from server import serve_client, read_frame


class AnnieTests(unittest.TestCase):
    _state = test_protocol.ProtocolTests._state

    def test_variants_and_capacity(self):
        for upgraded, friendly, cfg in ((False, True, 1),(True,True,2),(True,False,1),(False,False,1)):
            r,b,e,c=annie_convert(1,4,1,upgraded=upgraded,friendly=friendly)
            self.assertEqual((r+b+e,b,c),(6,3,cfg))
        self.assertIsNone(annie_convert(3,0,2,upgraded=True,friendly=True))
        self.assertIsNone(annie_convert(-1,1,0,upgraded=True,friendly=True))

    def test_unlock(self):
        for stars,sid in ((4,10017),(5,10018)):
            entry=dict(id=16,skillId=10017,starLevel=stars)
            self.assertEqual(effective_hero_skill(entry),sid)
            self.assertEqual(entry['skillId'],10017)

    def test_bot_native_replacement(self):
        for skill,cfg in ((10017,1),(10018,2)):
            a=battle(); a.gamers[1]=gamer(1,skill=skill,cd=0)
            packet,wait=a.resolve(1,Decision('skill',1,3,'test'),event_id=1,event_time=100)
            self.assertEqual((a.real[1],a.blank[1],a.enhanced[1]),(2,3,0) if cfg==1 else (1,3,1))
            event=Bs(packet,4)[1]; target=B(event,2)
            self.assertEqual(V(target,9),8)
            self.assertEqual(V(B(Bs(target,11)[0],2),1),cfg)
            self.assertEqual(protocol.pvp_gamer_skill_cd(a.gamers[1]),3)
            self.assertEqual(wait,7)

    def test_tcp_self_and_enemy(self):
        async def run(target):
            state=self._state({'selectedHero':16,'heroes':[dict(id=16,skillId=10017,starLevel=5)]})
            state._accounts={}; state._next_gid=1000001; state.pvp_port=0
            listener=await asyncio.start_server(lambda r,w:serve_client(r,w,state,'body','pvp'),'127.0.0.1',0)
            r,w=await asyncio.open_connection('127.0.0.1',listener.sockets[0].getsockname()[1])
            def send(act,b,index): w.write(protocol.encode_frame(3,act,b,index=index,length_mode='body'))
            async def receive(cmd,act,index=0):
                async with asyncio.timeout(4):
                    while True:
                        h,b,_=await read_frame(r,'body')
                        if (h.cmd,h.act,h.index)==(cmd,act,index): return h,b
            try:
                with patch('server.PVP_OPENING_SEQUENCE_DELAY',0):
                    send(1,protocol.pb_bytes(2,'local-pvp:1:6:16:0'),901)
                    _,b=await receive(3,1,901); before=Bs(B(b,2),2)[target]
                    self.assertEqual(protocol.pvp_gamer_skill_id(Bs(B(b,2),2)[0]),10018)
                    send(14,b'',902); await receive(3,14,902); await receive(255,1)
                    with patch('server.pvp_gamer_skill_cd',return_value=0):
                        send(6,protocol.pb_varint(1,target),903)
                        h,_=await receive(3,6,903); self.assertEqual(h.error,0)
                        _,b=await receive(255,2)
                    event=B(b,1); after=Bs(B(b,2),2)[target]
                    def ammo(g): return {V(a,1):V(a,2) or 0 for a in Bs(B(g,7),2)}
                    old,new=ammo(before),ammo(after); cfg=2 if target==0 else 1
                    self.assertEqual(sum(old.values()),sum(new.values()))
                    self.assertEqual(new[300],old[300]-1)
                    self.assertEqual(new.get(cfg,0),old.get(cfg,0)+1)
                    outline=B(Bs(event,4)[1],2)
                    self.assertEqual(ammo(after),{V(a,1):V(a,2) or 0 for a in Bs(outline,5)})
                    self.assertEqual(V(B(Bs(outline,11)[0],2),1),cfg)
                    send(6,protocol.pb_varint(1,target),904)
                    h,_=await receive(3,6,904); self.assertNotEqual(h.error,0)
            finally:
                w.close(); await w.wait_closed(); listener.close(); await listener.wait_closed()
        for target in (0,1): asyncio.run(run(target))
