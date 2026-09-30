import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]))
from weapon_skills import LADY_J_GUN_IDS,self_shot_reward_multiplier,weapon_skill_id
from server import _trio_self_shot_reward
from protocol import (_local_pvp_gamer,pvp_shoot_event_result_body,
    parse_bytes_field as B,parse_bytes_fields as Bs,parse_varint_field as V)

class LadyJTests(unittest.TestCase):
    def test_families_and_opening_definition(self):
        for gun in LADY_J_GUN_IDS:
            g=_local_pvp_gamer(100,'test',0,1,101,gun,1,10101,0,False)
            self.assertEqual(weapon_skill_id(gun),10006)
            self.assertEqual(V(B(g,7),4),10006)
            self.assertEqual(V(g,5),0)

    def test_condition_before_shot_includes_equality(self):
        self.assertEqual(self_shot_reward_multiplier(6,3,3),2)
        self.assertEqual(self_shot_reward_multiplier(6,3,4),1)
        self.assertEqual(self_shot_reward_multiplier(6,4,3),2)

    def test_actual_base_and_combo_rewards_doubled(self):
        self.assertEqual(_trio_self_shot_reward(3,3,0,gun_id=6),800)
        self.assertEqual(_trio_self_shot_reward(3,3,1,gun_id=6),1000)
        self.assertEqual(_trio_self_shot_reward(3,4,0,gun_id=6),300)

    def test_other_weapons_unchanged(self):
        for gun in (0,1,7,12,13,14,34,38):
            self.assertEqual(_trio_self_shot_reward(3,3,1,gun_id=gun),500)

    def test_banner_only_qualifying_blank_self_shot(self):
        g=_local_pvp_gamer(100,'test',0,1,101,6,1,10101,0,False)
        for target,cfg,blank,expected in ((0,300,2,True),(0,300,3,False),(1,300,2,False),(0,1,2,False)):
            packet=pvp_shoot_event_result_body(g,g,0,target,ammo_cfg_id=cfg,
                source_ammo_after=3,source_fake_ammo_after=blank)
            self.assertEqual(bool(V(B(Bs(packet,4)[0],1),50)),expected)

if __name__=='__main__':unittest.main()
