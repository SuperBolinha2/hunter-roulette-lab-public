import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]))
from protocol import (_local_pvp_gamer,pvp_consume_toxin_heal,pvp_event_with_toxin_removed,
    pvp_shoot_event_result_body,pvp_gamer_with_buffs,parse_bytes_field as B,
    parse_bytes_fields as Bs,parse_varint_field as V)
from server import _pvp_venom_after_shots
from bot_actions import TurnRestrictions

def gamer(index=0,gun=35):
    return _local_pvp_gamer(100+index,'test',0,1,101,gun,1,10101,index,bool(index))

def toxin(g):return [b for b in Bs(g,8) if V(b,1)==10066]

class VenomTests(unittest.TestCase):
    def test_opening_has_skill_but_not_poison(self):
        self.assertEqual(V(B(gamer(),7),4),10037)
        self.assertEqual(toxin(gamer()),[])

    def test_hit_applies_single_buff_on_target(self):
        gs=[gamer(),gamer(1,21)];timer=TurnRestrictions()
        for _ in range(2):
            self.assertTrue(_pvp_venom_after_shots(gs,0,1,[(1,-1,1,2,False)],[0],timer))
        self.assertEqual(len(toxin(gs[1])),1)
        self.assertEqual(toxin(gs[0]),[])

    def test_false_and_blocked_hit_do_not_apply(self):
        for cfg,delta in ((300,0),(1,0)):
            gs=[gamer(),gamer(1,21)]
            self.assertFalse(_pvp_venom_after_shots(gs,0,1,[(cfg,delta,1,2,False)],[0],TurnRestrictions()))

    def test_next_positive_heal_reduced_and_following_heal_normal(self):
        for heal,expected in ((1,0),(2,1),(3,2)):
            g=pvp_gamer_with_buffs(gamer(),add_cfg_ids=(10066,))
            g,recovered,used=pvp_consume_toxin_heal(g,heal)
            self.assertEqual((recovered,used),(expected,True))
            self.assertEqual(toxin(g),[])
            self.assertEqual(pvp_consume_toxin_heal(g,1)[1:],(1,False))

    def test_failed_or_zero_heal_does_not_consume(self):
        g=pvp_gamer_with_buffs(gamer(),add_cfg_ids=(10066,))
        updated,heal,used=pvp_consume_toxin_heal(g,0)
        self.assertEqual((updated,heal,used),(g,0,False))

    def test_individual_duration_survives_next_target_turn(self):
        timer=TurnRestrictions();timer.apply(1,10066)
        self.assertEqual(timer.start(0),())
        self.assertEqual(timer.start(1),())
        self.assertEqual(timer.start(2),())
        self.assertEqual(timer.start(0),())
        self.assertEqual(timer.start(1),(10066,))

    def test_reapplication_refreshes_duration(self):
        timer=TurnRestrictions();timer.apply(1,10066);timer.start(1)
        timer.apply(1,10066)
        self.assertEqual(timer.start(1),())
        self.assertEqual(timer.start(1),(10066,))

    def test_shot_add_and_heal_remove_native_hud_events(self):
        result=pvp_shoot_event_result_body(gamer(),gamer(1),0,1,
            ammo_cfg_id=1,target_hp_delta=-1,toxin_applied=True)
        target=B(Bs(result,4)[0],2)
        self.assertEqual(V(B(target,25),1),10066)
        result=pvp_event_with_toxin_removed(result,1,True,event_id=1,event_time=100)
        removal=B(Bs(result,4)[0],2)
        self.assertEqual((V(removal,1),V(removal,9)),(1,10))
        self.assertEqual(V(B(removal,24),1),10066)
        self.assertEqual(V(B(removal,24),8),3)  # End effect on healing consumption.

    def test_expiry_has_native_end_effect_reason(self):
        from protocol import pvp_passive_buff_removal_event_result_body
        result = pvp_passive_buff_removal_event_result_body(
            gamer(), target_index=0, cfg_ids=(10066,), event_id=2)
        removal = B(Bs(result,4)[0],2)
        self.assertEqual(V(B(removal,24),8),2)

if __name__=='__main__':unittest.main()
