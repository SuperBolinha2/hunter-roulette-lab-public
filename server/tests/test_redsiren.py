import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]))
from weapon_skills import normal_shot_count, weapon_skill_id
from protocol import (_local_pvp_gamer,pvp_shoot_event_result_body,
    parse_bytes_field as B,parse_bytes_fields as Bs,parse_varint_field as V)

class RedSirenTests(unittest.TestCase):
    def test_native_definition(self):
        g=_local_pvp_gamer(100,'test',0,1,101,13,1,10101,0,False)
        self.assertEqual(V(B(g,7),4),10019)
        self.assertEqual(weapon_skill_id(13),10019)

    def test_only_live_enemy_attack_adds_one(self):
        self.assertEqual(normal_shot_count(13,3,0,0,0,1),2)
        self.assertEqual(normal_shot_count(13,0,0,2,0,1),2)
        self.assertEqual(normal_shot_count(13,0,0,0,0,1),1)

    def test_any_blank_prevents_extra(self):
        for blank in range(1,7):
            self.assertEqual(normal_shot_count(13,2,blank,1,0,1),1)

    def test_self_and_other_weapons_do_not_trigger(self):
        self.assertEqual(normal_shot_count(13,3,0,0,0,0),1)
        self.assertEqual(normal_shot_count(13,3,0,0,0,0,True),1)
        for gun in (0,1,7,14,34,38):
            self.assertEqual(normal_shot_count(gun,3,0,0,0,1),1)

    def test_burst_additive_not_recursive(self):
        self.assertEqual(normal_shot_count(13,4,0,0,0,1,True),3)
        self.assertEqual(normal_shot_count(13,4,1,0,0,1,True),2)

    def test_two_native_shots_have_separate_damage_ammo_and_banner(self):
        g=_local_pvp_gamer(100,'test',0,1,101,13,1,10101,0,False)
        target=_local_pvp_gamer(101,'test',0,1,101,21,1,10101,1,True)
        result=pvp_shoot_event_result_body(g,target,0,1,ammo_cfg_id=1,
            target_hp_delta=-1,source_ammo_after=2,source_fake_ammo_after=0,
            additional_shots=((1,-1,1,0,False),),weapon_extra_shot_active=True)
        events=Bs(result,4)
        self.assertEqual([V(B(e,1),9) for e in events],[2,2,3])
        self.assertEqual(V(B(events[0],1),50),1)
        self.assertIsNone(V(B(events[1],1),50))
        self.assertEqual([V(B(e,2),2) for e in events[:2]],[(1<<64)-1]*2)
        self.assertEqual([{V(a,1):V(a,2) for a in Bs(B(e,1),5)}[1]
            for e in events[:2]],[2,1])

if __name__=='__main__':unittest.main()
