import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]))
from weapon_skills import carnivore_reward,weapon_skill_id
from server import _pvp_carnivore_reward
from protocol import (_local_pvp_gamer,pvp_shoot_event_result_body,
    parse_bytes_field as B,parse_bytes_fields as Bs,parse_varint_field as V)

def gamer(index=0,gun=12):
    return _local_pvp_gamer(100+index,'test',0,1,101,gun,1,10101,index,bool(index),coin=10000)

class CarnivoreTests(unittest.TestCase):
    def test_definition_without_opening_reward(self):
        g=gamer()
        self.assertEqual(weapon_skill_id(12),10015)
        self.assertEqual(V(B(g,7),4),10015)
        self.assertEqual(V(g,5),10000)

    def test_reward_per_hit_not_per_damage(self):
        for cfg,damage in ((1,-1),(2,-2),(1,-3)):
            self.assertEqual(carnivore_reward(12,0,1,[(cfg,damage,1,2,False)],[0]),2)

    def test_frenzy_damage_counts_and_blocked_hit_does_not(self):
        self.assertEqual(carnivore_reward(12,0,1,[(1,0,1,2,False)],[-1]),2)
        self.assertEqual(carnivore_reward(12,0,1,[(1,0,1,2,False)],[0]),0)

    def test_self_blank_other_weapon_no_reward(self):
        self.assertEqual(carnivore_reward(12,0,0,[(1,-1,1,2,False)],[0]),0)
        self.assertEqual(carnivore_reward(12,0,1,[(300,0,1,2,False)],[0]),0)
        for gun in (0,1,7,13,14,34,38):
            self.assertEqual(carnivore_reward(gun,0,1,[(1,-1,1,2,False)],[0]),0)

    def test_chain_rewards_each_damaging_shot(self):
        shots=[(1,-1,2,0,False),(2,-2,1,0,False),(300,0,1,0,False)]
        self.assertEqual(carnivore_reward(12,0,1,shots,[0,0,0]),4)

    def test_authoritative_balance_and_owner(self):
        for index,target in ((0,1),(1,0),(2,0)):
            g,reward=_pvp_carnivore_reward(gamer(index),index,target,[(1,-1,1,2,False)],[0])
            self.assertEqual(reward,2)
            self.assertEqual(V(g,5),10002)
            self.assertEqual(V(g,3),index)

    def test_shot_packet_has_native_coin_delta_and_weapon_banner(self):
        packet=pvp_shoot_event_result_body(gamer(),gamer(1,21),0,1,
            ammo_cfg_id=1,target_hp_delta=-1,source_coin_delta=2,coin_reason=8)
        source=B(Bs(packet,4)[0],1)
        self.assertEqual(V(source,50),1)
        self.assertEqual(V(B(source,4),1),2)
        self.assertEqual(V(B(source,4),2),8)

if __name__=='__main__':unittest.main()
