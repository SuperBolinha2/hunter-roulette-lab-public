import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).parents[1]))
from protocol import (_local_pvp_gamer, pvp_ghosts_after_shot,
    pvp_gamer_after_weapon_reload, pvp_gamer_with_state,
    pvp_shoot_event_result_body, parse_bytes_field as B,
    parse_bytes_fields as Bs, parse_varint_field as V)
from server import _resolve_hallucinogen_self_shot, _pvp_resolve_rocket_shot
from weapon_skills import weapon_skill_id

def gamer(index=0,gun=38):
    return _local_pvp_gamer(100+index,'test',0,1,101,gun,1,10101,index,bool(index))

class GhostsTests(unittest.TestCase):
    def test_opening_has_no_extra_real_or_counter(self):
        g=gamer()
        self.assertEqual(weapon_skill_id(38),10040)
        self.assertEqual(V(B(g,7),4),10040)
        self.assertEqual(Bs(g,8),[])

    def test_every_two_blanks_grants_one_real(self):
        g=gamer()
        for expected in (0,1,0,1,0,1):
            g,added=pvp_ghosts_after_shot(g,300)
            self.assertEqual(added,expected)

    def test_live_shot_does_not_reset_partial_count(self):
        g,_=pvp_ghosts_after_shot(gamer(),300)
        for cfg in (1,2):
            g,added=pvp_ghosts_after_shot(g,cfg)
            self.assertEqual(added,0)
        self.assertEqual(pvp_ghosts_after_shot(g,300)[1],1)

    def test_reload_resets_partial_count(self):
        g,_=pvp_ghosts_after_shot(gamer(),300)
        g=pvp_gamer_after_weapon_reload(g)
        g,added=pvp_ghosts_after_shot(g,300)
        self.assertEqual(added,0)
        self.assertEqual(pvp_ghosts_after_shot(g,300)[1],1)

    def test_turn_ammo_edits_ejector_do_not_count_or_clear_partial(self):
        g,_=pvp_ghosts_after_shot(gamer(),300)
        g=pvp_gamer_with_state(g,hp=4,ammo_number=2,fake_ammo_number=3,round_number=2)
        self.assertEqual(pvp_ghosts_after_shot(g,300)[1],1)

    def test_other_weapons_and_owners_are_isolated(self):
        for gun in (0,1,7,14,34):
            g=gamer(gun=gun)
            self.assertEqual(pvp_ghosts_after_shot(g,300),(g,0))
        a,_=pvp_ghosts_after_shot(gamer(),300)
        self.assertEqual(pvp_ghosts_after_shot(gamer(index=1),300)[1],0)
        self.assertEqual(pvp_ghosts_after_shot(a,300)[1],1)

    def test_second_forced_blank_adds_real_and_native_add_animation(self):
        g,_=pvp_ghosts_after_shot(gamer(),300)
        gamers=[g];hp=[4];live=[2];blank=[3];red=[0]
        with patch('server.random.randrange',return_value=0):
            result=_resolve_hallucinogen_self_shot(gamers,hp,[0],live,blank,[0],0,
                round_number=1,event_id=1,event_time=100,enhanced_ammo=red)
        self.assertEqual((result[1],live[0],blank[0],hp[0]),(300,3,2,4))
        events=Bs(result[3],4)
        shot=B(events[0],1)
        self.assertEqual({V(a,1):V(a,2) for a in Bs(shot,5)},{300:2,1:3})
        self.assertEqual(V(shot,69),1)
        self.assertEqual(V(shot,50),1)
        self.assertFalse(any(V(B(e,2),9)==21 for e in events))

    def test_double_blank_chain_add_event_between_second_shot_and_final(self):
        packet=pvp_shoot_event_result_body(gamer(),gamer(index=1),0,1,
            ammo_cfg_id=300,source_ammo_after=2,source_fake_ammo_after=3,
            additional_shots=((300,0,3,2,False),),ghosts_added_real_after_shots=(0,1))
        types=[V(B(e,1),9) for e in Bs(packet,4)]
        self.assertEqual(types,[2,2,3])
        events=Bs(packet,4)
        self.assertIsNone(V(B(events[0],1),69))
        self.assertEqual(V(B(events[1],1),69),1)

    def test_rocket_blank_counts_as_shot_and_grants_one_real(self):
        g,_=pvp_ghosts_after_shot(gamer(),300)
        gamers=[g,gamer(index=1)];hp=[4,4];frenzy=[2,0];live=[2,2];blank=[3,3];red=[0,0]
        with patch('server.random.randrange',return_value=0):
            result=_pvp_resolve_rocket_shot(gamers,hp,frenzy,live,blank,red,0,1,round_number=1)
        self.assertEqual(result.ghosts_added_real,1)
        self.assertEqual((live[0],blank[0]),(3,2))
        self.assertIsNone(result.reload_ammo_after)

if __name__=='__main__':unittest.main()
