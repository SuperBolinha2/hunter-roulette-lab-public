import asyncio
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).parents[1]))
import test_protocol
import protocol
from test_bot_ai import gamer,battle
from bot_ai import Decision
from katie_guard import activate,intercept,expire,expiry_packet
from hero_skills import effective_hero_skill,battle_hero_skill
from protocol import parse_varint_field as V,parse_bytes_field as B,parse_bytes_fields as Bs
from server import serve_client,read_frame


class KatieTests(unittest.TestCase):
    _state=test_protocol.ProtocolTests._state

    def test_unlock_and_scaled_reward(self):
        entry=dict(id=17,skillId=10022,starLevel=5)
        self.assertEqual(battle_hero_skill(effective_hero_skill(entry),shop_trio=True),10031)
        self.assertEqual(entry['skillId'],10022)
        for skill,reward in ((10022,0),(10023,2),(10030,20),(10031,200)):
            gs=[gamer(0)]; guards={}; gs[0]=activate(gs[0],skill,0,guards)
            buff,paid=expire(gs,guards,0)
            self.assertEqual((paid,V(gs[0],5)),(reward,10000+reward))
            self.assertNotIn(buff,[V(b,1) for b in Bs(gs[0],8)])
            self.assertIsNone(expire(gs,guards,0))

    def test_interception_once_no_reward_and_own_shot_bypasses(self):
        gs=[gamer(0),gamer(1)]; guards={}; gs[0]=activate(gs[0],10031,0,guards)
        self.assertIsNone(intercept(gs,guards,0,0,1))
        self.assertEqual(intercept(gs,guards,1,0,1),10049)
        self.assertIsNone(intercept(gs,guards,1,0,1))
        self.assertIsNone(expire(gs,guards,0))
        self.assertEqual(V(gs[0],5),10000)

    def test_blanks_preserve_pet_until_owner_turn(self):
        gs=[gamer(0),gamer(1)]; guards={}; gs[0]=activate(gs[0],10031,0,guards)
        for _ in range(3):
            self.assertIsNone(intercept(gs,guards,1,0,300))
            self.assertIn(0,guards)
            self.assertIn(10049,[V(b,1) for b in Bs(gs[0],8)])
        self.assertEqual(expire(gs,guards,0),(10049,200))
        self.assertNotIn(0,guards)

    def test_blank_then_red_consumes_without_expiry_reward(self):
        gs=[gamer(0),gamer(1)]; guards={}; gs[0]=activate(gs[0],10031,0,guards)
        self.assertIsNone(intercept(gs,guards,1,0,300))
        self.assertEqual(intercept(gs,guards,1,0,2),10049)
        self.assertIsNone(expire(gs,guards,0))
        self.assertEqual(V(gs[0],5),10000)

    def test_individual_expiry_and_dead_no_reward(self):
        gs=[gamer(0),gamer(1)]; guards={}
        for i in range(2): gs[i]=activate(gs[i],10031,i,guards)
        expire(gs,guards,0); self.assertIn(1,guards)
        gs[1]=protocol.pvp_gamer_with_state(gs[1],hp=0,virtual_hp=0,ammo_number=1,fake_ammo_number=1,round_number=1)
        self.assertEqual(expire(gs,guards,1),(10049,0))

    def test_bot_activation_native_packet(self):
        a=battle(); a.gamers[1]=gamer(1,skill=10031,cd=0)
        packet,wait=a.resolve(1,Decision('skill',1,3,'shield'),event_id=1,event_time=100)
        self.assertEqual(a.katie_guards[1],(10049,200))
        self.assertEqual(V(B(Bs(packet,4)[1],2),9),10)
        self.assertEqual(V(Bs(B(Bs(packet,4)[1],2),25)[0],1),10049)
        self.assertEqual(wait,8)

    def test_expiry_passive_native_removal(self):
        packet=expiry_packet(gamer(0),0,10049,200,1,100)
        out=B(Bs(packet,4)[0],2)
        self.assertEqual(V(packet,1),17)
        self.assertEqual(V(B(out,4),2),20)
        self.assertEqual(V(Bs(out,24)[0],1),10049)
        self.assertEqual(V(Bs(out,24)[0],8),2)

    def test_interception_packet_native_pet_destroy_state(self):
        for cfg in (10029,10031,10047,10049):
            packet=protocol.pvp_shoot_event_result_body(gamer(1),gamer(2),1,2,
                source_ammo_after=1,source_fake_ammo_after=1,target_hp_delta=0,
                target_del_buff_cfgs=(cfg,))
            outline=B(Bs(packet,4)[0],2)
            buff=Bs(outline,24)[0]
            self.assertEqual((V(buff,1),V(buff,6),V(buff,8)),(cfg,2,3))

    def test_tcp_activation_and_duplicate_rejection(self):
        async def run():
            state=self._state({'selectedHero':17,'heroes':[dict(id=17,skillId=10022,starLevel=5)]})
            state._accounts={};state._next_gid=1000001;state.pvp_port=0
            listener=await asyncio.start_server(lambda r,w:serve_client(r,w,state,'body','pvp'),'127.0.0.1',0)
            r,w=await asyncio.open_connection('127.0.0.1',listener.sockets[0].getsockname()[1])
            def send(act,body,index):w.write(protocol.encode_frame(3,act,body,index=index,length_mode='body'))
            async def receive(cmd,act,index=0):
                async with asyncio.timeout(4):
                    while True:
                        h,b,_=await read_frame(r,'body')
                        if (h.cmd,h.act,h.index)==(cmd,act,index):return h,b
            try:
                with patch('server.PVP_OPENING_SEQUENCE_DELAY',0):
                    send(1,protocol.pb_bytes(2,'local-pvp:1:6:17:0'),901)
                    _,b=await receive(3,1,901)
                    self.assertEqual(protocol.pvp_gamer_skill_id(Bs(B(b,2),2)[0]),10031)
                    send(14,b'',902);await receive(3,14,902);await receive(255,1)
                    with patch('server.pvp_gamer_skill_cd',return_value=0):
                        send(6,protocol.pb_varint(1,0),903)
                        h,_=await receive(3,6,903);self.assertEqual(h.error,0)
                        _,b=await receive(255,2)
                    g=Bs(B(b,2),2)[0]
                    self.assertIn(10049,[V(b,1) for b in Bs(g,8)])
                    self.assertEqual(protocol.pvp_gamer_skill_cd(g),3)
                    send(6,protocol.pb_varint(1,0),904)
                    h,_=await receive(3,6,904);self.assertNotEqual(h.error,0)
            finally:
                w.close();await w.wait_closed();listener.close();await listener.wait_closed()
        asyncio.run(run())

    def test_bot_rocket_blocked_and_pet_destroyed(self):
        a=battle(cfg=2032); a.gamers[0]=activate(a.gamers[0],10031,0,a.katie_guards)
        a.real[1]=3; a.blank[1]=0; a.enhanced[1]=1
        offer=next(o for o in a.observation(1).offers if o.cfg==2032)
        packet,_=a.resolve(1,Decision('item',0,3,'rocket',offer),event_id=1,event_time=100)
        self.assertEqual((a.hp[0],a.frenzy[0]),(2,1))
        self.assertNotIn(0,a.katie_guards)
        removals=[B(e,2) for e in Bs(packet,4) if V(B(e,2),9)==10 and Bs(B(e,2),24)]
        self.assertEqual(V(Bs(removals[0],24)[0],8),3)
        self.assertIsNone(expire(a.gamers,a.katie_guards,0))
        self.assertEqual(V(a.gamers[0],5),10000)

    def test_human_rocket_resolver_real_and_blank(self):
        from server import _pvp_resolve_rocket_shot
        for cfg in (1,300):
            gs=[gamer(0),gamer(1)];guards={};gs[1]=activate(gs[1],10031,1,guards)
            hp=[2,2];fr=[1,1];real=[3,1];blank=[1,2];red=[1,0]
            with patch('server._draw_ejected_ammo',return_value=cfg):
                result=_pvp_resolve_rocket_shot(gs,hp,fr,real,blank,red,0,1,
                    round_number=1,katie_guards=guards)
            self.assertEqual((hp[1],fr[1]),(2,1))
            if cfg==1:
                self.assertEqual(result.blocked_katie_buff,10049)
                self.assertEqual(result.consumed_ammo,((1,3),(2,1)))
                self.assertIsNotNone(result.reload_ammo_after)
                self.assertNotIn(1,guards)
            else:
                self.assertIsNone(result.blocked_katie_buff)
                self.assertEqual(result.consumed_ammo,((300,1),))
                self.assertIn(1,guards)

    def test_grazier_duel_red_blocked_in_both_directions(self):
        from fair_duel import resolve_fair_duel
        from server import _pvp_apply_hp_damage
        for shooter in (0,1):
            gs=[gamer(0),gamer(1)]; guards={}; victim=1-shooter
            gs[shooter]=protocol.pb_message(
                *(raw for n,w,v,raw in protocol._iter_pb_fields(gs[shooter]) if n!=7),
                protocol.pb_bytes(7,protocol.pb_varint(1,7)))
            gs[victim]=activate(gs[victim],10031,victim,guards)
            hp=[2,2];fr=[1,1];real=[1,1];blank=[2,2];red=[0,1] if shooter==1 else [0,0]
            draws=iter((300,1) if shooter==1 else (1,))
            result=resolve_fair_duel(gs,hp,fr,real,blank,red,actor=0,target=1,
                upgraded=True,draw=lambda r,b,e:next(draws),damage=_pvp_apply_hp_damage,
                round_number=1,event_id=1,event_time=100,katie_guards=guards)
            self.assertEqual(result.shots[-1],(shooter,victim,2))
            self.assertEqual((hp,fr),([2,2],[1,1]))
            self.assertNotIn(victim,guards)
            shot=[e for e in Bs(result.packet,4) if V(B(e,1),9)==2][-1]
            removed=Bs(B(shot,2),24)[0]
            self.assertEqual((V(removed,1),V(removed,8)),(10049,3))
            self.assertIsNone(expire(gs,guards,victim))
