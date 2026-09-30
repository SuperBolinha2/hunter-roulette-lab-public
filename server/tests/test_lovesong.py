import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1]))
from protocol import (
    _local_pvp_gamer, pvp_gamer_after_weapon_reload, pvp_gamer_with_skill_cd,
    pvp_gamer_skill_cd, pvp_gamer_with_state, pvp_spare_magazine_event_result_body,
    pvp_eject_ammo_card_event_result_body, pvp_shoot_event_result_body,
    pvp_generic_card_event_result_body, pvp_shop_card,
    parse_bytes_field as B, parse_bytes_fields as Bs, parse_varint_field as V,
)
from weapon_skills import weapon_skill_id

def owner(index=0, gun=14):
    return pvp_gamer_with_skill_cd(_local_pvp_gamer(100+index,'test',0,1,101,
        gun,1,10101,index,bool(index)),3)

class LoveSongTests(unittest.TestCase):
    def test_opening_defines_trait_without_charge(self):
        g=owner()
        self.assertEqual(weapon_skill_id(14),10016)
        self.assertEqual(V(B(g,7),4),10016)
        self.assertEqual(pvp_gamer_skill_cd(g),3)

    def test_each_reload_gives_one_charge_and_caps_at_ready(self):
        g=owner()
        for expected in (2,1,0,0):
            g=pvp_gamer_after_weapon_reload(g)
            self.assertEqual(pvp_gamer_skill_cd(g),expected)

    def test_plain_state_updates_do_not_grant_charge(self):
        g=pvp_gamer_with_state(owner(),hp=4,ammo_number=2,
            fake_ammo_number=2,round_number=2)
        self.assertEqual(pvp_gamer_skill_cd(g),3)
        g=pvp_gamer_with_state(g,hp=4,ammo_number=2,
            fake_ammo_number=2,round_number=2,weapon_reloaded=True)
        self.assertEqual(pvp_gamer_skill_cd(g),2)

    def test_other_weapons_do_not_grant_charge(self):
        for gun in (0,1,2,21):
            self.assertEqual(pvp_gamer_skill_cd(pvp_gamer_after_weapon_reload(owner(gun=gun))),3)

    def test_reload_paths_publish_native_cd_update_on_correct_owner(self):
        g=pvp_gamer_after_weapon_reload(owner(index=1))
        actor=owner()
        packets=(
            pvp_spare_magazine_event_result_body(actor,g,pvp_shop_card(1,2007,200),target_index=1,
                old_real=1,old_fake=2,real_after=2,fake_after=2,event_id=1,event_time=100),
            pvp_eject_ammo_card_event_result_body(actor,g,pvp_shop_card(2,2001,100),target_index=1,
                ejected_ammo_cfg_id=1,reload_ammo_after=(2,2),event_id=2,event_time=100),
            pvp_shoot_event_result_body(g,actor,1,0,ammo_cfg_id=1,
                source_ammo_after=0,source_fake_ammo_after=2,reload_ammo_after=(2,2),event_time=100),
            pvp_generic_card_event_result_body(g,actor,pvp_shop_card(3,2032,200),
                skill_id=1031,target_index=0,event_id=3,event_time=100,reload_ammo_after=(2,2)),
        )
        for packet in packets:
            events=Bs(packet,4)
            reload=next(B(e,2) for e in events if V(B(e,2),8)==1)
            updates=[e for e in events if V(B(e,2),9)==9]
            self.assertEqual(len(updates),1)
            update=updates[0]
            self.assertEqual(V(B(update,1),1),1)
            self.assertEqual(V(B(update,2),1),1)
            self.assertEqual(V(B(update,2),21),2)
            self.assertEqual(V(B(update,2),28),V(reload,28))
            self.assertEqual(V(reload,50),1)

if __name__=='__main__': unittest.main()
