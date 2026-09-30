import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).parents[1]))
from weapon_skills import GRAZIER_GUN_IDS, weapon_skill_id, prioritize_shot_ammo
from server import _draw_loaded_ammo, _resolve_hallucinogen_self_shot
from protocol import (_local_pvp_gamer, pvp_gamer_with_state, pvp_gamer_enhanced_count,
    parse_bytes_field as B, parse_bytes_fields as Bs, parse_varint_field as V)

def gamer(gun=7):
    return _local_pvp_gamer(100,'test',0,1,101,gun,1,10101,0,False)

class GrazierTests(unittest.TestCase):
    def test_families_define_trait_without_creating_enhanced_ammo(self):
        for gun in GRAZIER_GUN_IDS:
            g=gamer(gun)
            self.assertEqual(weapon_skill_id(gun),10007)
            self.assertEqual(V(B(g,7),4),10007)
            self.assertEqual(pvp_gamer_enhanced_count(g),0)

    def test_blank_probability_is_unchanged_and_all_live_results_prioritize_red(self):
        for gun in GRAZIER_GUN_IDS:
            for roll in range(5):
                with patch('server.random.randrange',return_value=roll):
                    self.assertEqual(_draw_loaded_ammo(1,3,1,gun_id=gun),300 if roll<3 else 2)

    def test_other_guns_and_no_red_keep_original_draw(self):
        for gun in (0,1,14,34,21):
            self.assertEqual(prioritize_shot_ammo(gun,1,1),1)
        self.assertEqual(prioritize_shot_ammo(7,1,0),1)
        self.assertIsNone(prioritize_shot_ammo(7,None,1))

    def test_red_consumption_allows_ordinary_live_on_next_shot(self):
        with patch('server.random.randrange',return_value=3):
            self.assertEqual(_draw_loaded_ammo(1,3,1,gun_id=7),2)
            self.assertEqual(_draw_loaded_ammo(1,3,0,gun_id=7),1)

    def test_hallucinogen_prioritizes_red_consumes_one_deals_two_and_shows_banner(self):
        g=pvp_gamer_with_state(gamer(),hp=4,ammo_number=1,fake_ammo_number=3,
            enhanced_ammo_number=1,round_number=1)
        gamers=[g];hp=[4];real=[1];blank=[3];red=[1]
        with patch('server.random.randrange',return_value=3):
            result=_resolve_hallucinogen_self_shot(gamers,hp,[0],real,blank,[0],0,
                round_number=1,event_id=1,event_time=100,enhanced_ammo=red)
        self.assertEqual(result[1],2)
        self.assertEqual((hp[0],real[0],blank[0],red[0]),(2,1,3,0))
        source=B(Bs(result[3],4)[0],1)
        self.assertEqual(V(source,50),1)

    def test_blank_forced_shot_preserves_red(self):
        g=pvp_gamer_with_state(gamer(),hp=4,ammo_number=1,fake_ammo_number=3,
            enhanced_ammo_number=1,round_number=1)
        gamers=[g];hp=[4];real=[1];blank=[3];red=[1]
        with patch('server.random.randrange',return_value=0):
            result=_resolve_hallucinogen_self_shot(gamers,hp,[0],real,blank,[0],0,
                round_number=1,event_id=1,event_time=100,enhanced_ammo=red)
        self.assertEqual(result[1],300)
        self.assertEqual((hp[0],real[0],blank[0],red[0]),(4,1,2,1))

if __name__=='__main__':unittest.main()
