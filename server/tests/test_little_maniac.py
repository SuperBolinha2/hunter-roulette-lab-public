import asyncio
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1]))
from weapon_skills import LITTLE_MANIAC_GUN_IDS, weapon_skill_id, lucky_die_result
from protocol import (
    _local_pvp_gamer, pvp_gamer_after_weapon_reload, pvp_consume_lucky_die,
    pvp_gamer_with_state, pvp_event_with_consumed_lucky,
    pvp_wet_cigarette_event_result_body, pvp_spare_magazine_event_result_body,
    pvp_shoot_event_result_body, pvp_eject_ammo_card_event_result_body,
    pvp_generic_card_event_result_body,
    pvp_shop_card, pvp_login_snapshot, encode_frame, pb_bytes, pb_varint,
    parse_bytes_field as B, parse_bytes_fields as Bs, parse_varint_field as V,
)
from server import read_frame, serve_client, _resolve_hallucinogen_self_shot


def little(index=0, gun=0, reloaded=True):
    g = _local_pvp_gamer(100+index,'trait-test',0,1,101,gun,1,10101,index,bool(index))
    return pvp_gamer_after_weapon_reload(g) if reloaded else g


def lucky(gamer):
    return [b for b in Bs(gamer,8) if V(b,1)==600]


def dice(packet):
    return [B(B(e,2) or b'',22) for e in Bs(packet,4) if B(B(e,2) or b'',22)]


class LittleManiacTests(unittest.TestCase):
    def test_verified_family_ids_have_native_trait_and_one_buff(self):
        for gun in LITTLE_MANIAC_GUN_IDS:
            g=little(gun=gun)
            self.assertEqual(weapon_skill_id(gun),3)
            self.assertEqual(V(B(g,7),4),3)
            self.assertEqual(len(lucky(g)),1)

    def test_tutorial_ids_do_not_receive_lucky(self):
        for gun in (2,3,4,11,21,22):
            self.assertEqual(lucky(little(gun=gun)),[])

    def test_initial_magazine_capacity_does_not_change(self):
        _,_,g,_=pvp_login_snapshot(100,'trait-test','local-pvp:1:6:0:0',1,6,0,1,101,0,1,10101)
        self.assertEqual(sum(V(a,2) for a in Bs(B(g,7),2)),6)
        self.assertEqual(lucky(g), [])

    def test_opening_load_has_no_lucky_for_any_family_member(self):
        for gun in LITTLE_MANIAC_GUN_IDS:
            for index in (0, 1, 2):
                self.assertEqual(lucky(little(index=index, gun=gun, reloaded=False)), [])

    def test_every_roll_is_boosted_and_capped_at_six(self):
        for raw,expected in zip(range(1,7),(3,4,5,6,6,6)):
            self.assertEqual(lucky_die_result(raw,True),expected)
            self.assertEqual(lucky_die_result(raw,False),raw)

    def test_invalid_die_does_not_consume_buff(self):
        g=little()
        with self.assertRaises(ValueError): pvp_consume_lucky_die(g,0)
        self.assertEqual(len(lucky(g)),1)

    def test_only_next_die_receives_bonus(self):
        g,roll,used=pvp_consume_lucky_die(little(),1)
        self.assertTrue(used)
        self.assertEqual(roll,3)
        self.assertEqual(lucky(g),[])
        _,roll,used=pvp_consume_lucky_die(g,1)
        self.assertFalse(used)
        self.assertEqual(roll,1)

    def test_reload_replaces_one_buff_without_stacking(self):
        g=little()
        for _ in range(4): g=pvp_gamer_after_weapon_reload(g)
        self.assertEqual(len(lucky(g)),1)
        self.assertEqual(V(lucky(g)[0],4),(-1)&((1<<64)-1))

    def test_item_add_and_turn_snapshot_do_not_restore_consumed_buff(self):
        g,_,_=pvp_consume_lucky_die(little(),2)
        g=pvp_gamer_with_state(g,hp=4,ammo_number=3,fake_ammo_number=4,round_number=8)
        self.assertEqual(lucky(g),[])
        g=pvp_gamer_with_state(g,hp=4,ammo_number=2,fake_ammo_number=4,round_number=8,weapon_reloaded=True)
        self.assertEqual(len(lucky(g)),1)

    def test_consuming_actor_buff_does_not_touch_other_players(self):
        actor,target=little(),little(index=1)
        actor,_,_=pvp_consume_lucky_die(actor,4)
        self.assertEqual(lucky(actor),[])
        self.assertEqual(len(lucky(target)),1)

    def test_native_dice_packet_has_raw_roll_bonus_and_buff_icon(self):
        for raw in range(1,7):
            g,roll,_=pvp_consume_lucky_die(little(),raw)
            packet=pvp_wet_cigarette_event_result_body(g,pvp_shop_card(1,2011,200),
                die_roll=roll,heal_delta=0,event_id=1)
            packet=pvp_event_with_consumed_lucky(packet,0,consumed=raw,event_id=1,event_time=1)
            die=dice(packet)[0]
            self.assertEqual((V(die,1),V(die,2)),(raw,2))
            self.assertEqual(V(Bs(die,4)[0],1),600)
            self.assertEqual(V(die,3),int(roll>=4))
            removal=B(Bs(packet,4)[0],2)
            self.assertEqual(V(Bs(removal,24)[0],1),600)

    def test_reload_event_publishes_lucky_and_weapon_banner(self):
        g=little()
        packet=pvp_spare_magazine_event_result_body(g,g,pvp_shop_card(1,2007,200),
            target_index=0,old_real=1,old_fake=3,real_after=2,fake_after=4,event_id=1)
        reload=next(B(e,2) for e in Bs(packet,4) if V(B(e,2) or b'',8))
        self.assertEqual(V(reload,50),1)
        self.assertEqual(V(Bs(reload,25)[0],1),600)

    def test_every_reload_path_has_client_consumed_buff_update(self):
        g=little(index=1)
        packets=(
            pvp_spare_magazine_event_result_body(little(),g,pvp_shop_card(1,2007,200),target_index=1,
                old_real=1,old_fake=3,real_after=2,fake_after=4,event_id=1,event_time=100),
            pvp_eject_ammo_card_event_result_body(little(),g,pvp_shop_card(1,2001,100),target_index=1,
                ejected_ammo_cfg_id=1,event_id=1,event_time=100,reload_ammo_after=(2,4)),
            pvp_shoot_event_result_body(g,little(),1,0,event_id=1,event_time=100,reload_ammo_after=(2,4)),
            pvp_generic_card_event_result_body(g,little(),pvp_shop_card(1,2032,600),skill_id=1031,
                target_index=0,event_id=1,event_time=100,event_type=39,reload_ammo_after=(2,4)),
        )
        for packet in packets:
            events=Bs(packet,4)
            reload=next(B(e,2) for e in events if V(B(e,2) or b'',8))
            # Native Lua only calls UpdateBuffs for typ 10/2, not reload 1/12.
            updates=[e for e in events if V(B(e,2) or b'',9)==10 and Bs(B(e,2),25)]
            self.assertEqual(len(updates),1)
            update=B(updates[0],2)
            self.assertEqual(V(update,1),1)
            self.assertEqual(V(B(updates[0],1),1),1)
            self.assertEqual(V(update,28),V(reload,28))
            self.assertEqual(V(Bs(update,25)[0],1),600)

    def test_second_spare_magazine_emits_update_after_buff_was_consumed(self):
        g=little()
        for time in (100,200):
            g,_,_=pvp_consume_lucky_die(g,2)
            self.assertEqual(lucky(g),[])
            g=pvp_gamer_after_weapon_reload(g)
            packet=pvp_spare_magazine_event_result_body(g,g,pvp_shop_card(1,2007,200),
                target_index=0,old_real=1,old_fake=3,real_after=2,fake_after=4,event_id=time,event_time=time)
            target=B(Bs(packet,4)[-1],2)
            self.assertEqual(V(target,9),10)
            self.assertEqual(V(Bs(target,25)[0],1),600)
            self.assertEqual(V(target,28),time)

    def test_hallucinogen_last_live_reload_restores_lucky_not_on_plain_shot(self):
        gs=[little(),little(index=1,gun=21)]
        gs[0],_,_=pvp_consume_lucky_die(gs[0],1)
        hp=[4,4]; real=[1,2]; blank=[2,2]
        with patch('server.random.randrange',return_value=2):
            result=_resolve_hallucinogen_self_shot(gs,hp,[0,0],real,blank,[0,0],0,
                round_number=1,event_id=1,event_time=1,enhanced_ammo=[0,0])
        self.assertEqual(len(lucky(gs[0])),1)
        reload=B(Bs(result[3],4)[1],2)
        self.assertEqual(V(Bs(reload,25)[0],1),600)

    def test_bot_cigarette_uses_its_own_next_die_bonus(self):
        import test_bot_ai as fixtures
        from bot_ai import candidates
        for stored in (False,True):
            state=fixtures.battle(2011,stored=stored)
            state.gamers[1]=pvp_gamer_after_weapon_reload(state.gamers[1])
            action=next(d for d in candidates(state.observation(1),'hard')
                        if d.offer is not None and d.target==1)
            with patch.object(state.rng,'randint',return_value=2):
                packet,_=state.resolve(1,action,event_id=1,event_time=1,difficulty='hard')
            self.assertEqual(state.hp[1],3)
            self.assertEqual(lucky(state.gamers[1]),[])
            self.assertEqual((V(dice(packet)[0],1),V(dice(packet)[0],2)),(2,2))

    def test_live_server_direct_and_stored_dice_consumption_reload_and_skill(self):
        import test_protocol as fixtures
        state=fixtures.ProtocolTests._state(self,{'selectedHero':0,'heroGuns':[{'heroId':0,'gunId':0}]})
        state._accounts={}; state._next_gid=1000001; state.pvp_port=0

        async def exchange(stored):
            listener=await asyncio.start_server(lambda r,w:serve_client(r,w,state,'body','pvp'),'127.0.0.1',0)
            writer=None
            try:
                reader,writer=await asyncio.open_connection('127.0.0.1',listener.sockets[0].getsockname()[1])
                async def receive(cmd,act,index=0):
                    async with asyncio.timeout(4):
                        while True:
                            h,b,_=await read_frame(reader,'body')
                            if (h.cmd,h.act,h.index)==(cmd,act,index):return h,b
                def request(act,body,index):
                    writer.write(encode_frame(3,act,body,index=index,length_mode='body'))
                async def use(card,target,index):
                    if stored:
                        request(5,pb_varint(1,card)+pb_varint(4,3),index+100)
                        h,_=await receive(3,5,index+100);self.assertEqual(h.error,0)
                        await receive(255,2)
                    request(5,pb_varint(1,card)+pb_varint(2,target)+pb_varint(4,2 if stored else 1),index)
                    h,_=await receive(3,5,index);self.assertEqual(h.error,0)
                    _,b=await receive(255,2)
                    return B(b,1),Bs(B(b,2),2)
                request(1,pb_bytes(2,'local-pvp:1:6:0:0'),801)
                _,b=await receive(3,1,801)
                self.assertEqual(lucky(Bs(B(b,2),2)[0]),[])
                request(14,b'',802);await receive(3,14,802);await receive(255,1)
                _, gs = await use(5,0,808) # First actual reload activates trait.
                self.assertEqual(len(lucky(gs[0])),1)
                with patch('server.random.randrange',return_value=5):
                    _,gs=await use(1,0,803) # Forced live shot is not a die.
                self.assertEqual(V(gs[0],4),3)
                self.assertEqual(len(lucky(gs[0])),1)
                with patch('server.random.randint',return_value=2):
                    packet,gs=await use(2,0,804) # 2+2 succeeds and heals.
                self.assertEqual(V(gs[0],4),4)
                self.assertEqual(lucky(gs[0]),[])
                self.assertEqual((V(dice(packet)[0],1),V(dice(packet)[0],2)),(2,2))
                with patch('server.random.randint',return_value=1):
                    packet,gs=await use(3,1,805) # No second bonus.
                self.assertEqual((V(dice(packet)[0],1),V(dice(packet)[0],2)),(1,0))
                self.assertEqual(V(gs[1],5),9900)
                packet,gs=await use(4,0,806)
                update=B(Bs(packet,4)[-1],2)
                self.assertEqual(V(update,9),10)
                self.assertEqual(V(Bs(update,25)[0],1),600)
                self.assertEqual(len(lucky(gs[0])),1)
                with patch('server.pvp_gamer_skill_cd',return_value=0),patch('server.random.randint',return_value=1):
                    request(6,pb_varint(1,1),807)
                    h,_=await receive(3,6,807);self.assertEqual(h.error,0)
                    _,b=await receive(255,2)
                packet=B(b,1);gs=Bs(B(b,2),2)
                self.assertEqual((V(dice(packet)[0],1),V(dice(packet)[0],2)),(1,2))
                self.assertEqual(V(gs[1],4),3) # Rabbit succeeds on adjusted 3.
                self.assertEqual(lucky(gs[0]),[])
            finally:
                if writer is not None:writer.close();await writer.wait_closed()
                listener.close();await listener.wait_closed()

        with patch('server.PVP_OPENING_SEQUENCE_DELAY',0.001),patch('server._random_shop_specs',return_value=((2008,200),(2011,200),(2018,400),(2007,200),(2007,200))):
            for stored in (False,True):
                with self.subTest(stored=stored):asyncio.run(exchange(stored))


if __name__=='__main__':unittest.main()
