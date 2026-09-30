import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).parents[1]))
from weapon_skills import apply_reload_trait, weapon_skill_id
from protocol import (
    _local_pvp_gamer, pvp_gamer_with_state, pvp_gun_ammo_counts,
    pvp_spare_magazine_event_result_body, pvp_eject_ammo_card_event_result_body,
    pvp_shoot_event_result_body, pvp_generic_card_event_result_body, pvp_shop_card,
    parse_bytes_field as B, parse_bytes_fields as Bs, parse_varint_field as V,
)
from server import _reload_weapon_ammo, _resolve_hallucinogen_self_shot

def owner(index=0):
    return _local_pvp_gamer(100+index,'test',0,1,101,34,1,10101,index,bool(index))

def counts(message,field):
    return {V(a,1):V(a,2) for a in Bs(message,field)}

class ArtemisTests(unittest.TestCase):
    def test_opening_has_definition_without_conversion(self):
        self.assertEqual(weapon_skill_id(34),10034)
        for index in (0,1,2):
            g=owner(index)
            self.assertEqual(V(B(g,7),4),10034)
            live,blank=pvp_gun_ammo_counts(34)
            self.assertEqual(counts(B(g,7),2),{1:live,300:blank})

    def test_conversion_preserves_capacity_and_has_no_enhanced_round(self):
        for live in range(7):
            m=apply_reload_trait(34,live,6-live)
            self.assertEqual((m.real,m.blank,m.enhanced),
                (live+1,5-live,0) if live<6 else (6,0,0))

    def test_reload_replaces_previous_magazine_not_accumulates(self):
        enhanced=[4]
        for _ in range(3):
            self.assertEqual(_reload_weapon_ammo(34,enhanced,0),(4,2))
            self.assertEqual(enhanced,[0])
        with patch('protocol.random.randint',return_value=1):
            self.assertEqual(_reload_weapon_ammo(34,enhanced,0,randomize=True),(2,4))

    def test_plain_state_update_does_not_convert(self):
        g=pvp_gamer_with_state(owner(),hp=4,ammo_number=2,fake_ammo_number=4,round_number=2)
        self.assertEqual(counts(B(g,7),2),{1:2,300:4})

    def test_all_reload_packets_publish_converted_magazine_and_banner(self):
        g=pvp_gamer_with_state(owner(1),hp=4,ammo_number=4,
            fake_ammo_number=2,round_number=1,weapon_reloaded=True)
        actor=owner()
        packets=(
            pvp_spare_magazine_event_result_body(actor,g,pvp_shop_card(1,2007,200),target_index=1,
                old_real=1,old_fake=3,real_after=4,fake_after=2,event_id=1),
            pvp_eject_ammo_card_event_result_body(actor,g,pvp_shop_card(2,2001,100),target_index=1,
                ejected_ammo_cfg_id=1,reload_ammo_after=(4,2),event_id=2),
            pvp_shoot_event_result_body(g,actor,1,0,ammo_cfg_id=1,
                source_ammo_after=0,source_fake_ammo_after=3,reload_ammo_after=(4,2)),
            pvp_generic_card_event_result_body(g,actor,pvp_shop_card(3,2032,200),
                skill_id=1031,target_index=0,event_id=3,reload_ammo_after=(4,2)),
        )
        for packet in packets:
            reload=next(B(e,2) for e in Bs(packet,4) if V(B(e,2),8)==1)
            self.assertEqual(V(reload,1),1)
            self.assertIsNone(V(reload,50))
            self.assertEqual(V(reload,9),1)
            self.assertEqual(counts(reload,5),{1:3,300:3})
            change=next(B(e,2) for e in Bs(packet,4) if V(B(e,2),9)==12)
            self.assertEqual(V(change,1),1)
            self.assertIsNone(V(change,8)) # Never play a second reload.
            self.assertEqual(V(change,50),1)
            self.assertEqual(counts(change,5),{1:4,300:2})
            pair=B(change,11)
            self.assertEqual((V(B(pair,1),1),V(B(pair,1),2)),(300,1))
            self.assertEqual((V(B(pair,2),1),V(B(pair,2),2)),(1,1))
            self.assertGreaterEqual(V(change,28),V(reload,28))

    def test_hallucinogen_consuming_last_real_reloads_with_conversion(self):
        gamers=[owner(),owner(1)]
        hp=[4,4];live=[1,3];blank=[3,3];enhanced=[0,0]
        with patch('server.random.randrange',return_value=3):
            result=_resolve_hallucinogen_self_shot(gamers,hp,[0,0],live,blank,[0,0],0,
                round_number=1,event_id=1,event_time=100,enhanced_ammo=enhanced)
        self.assertEqual(result[1],1)
        self.assertEqual((live[0],blank[0]),(4,2))
        self.assertEqual(counts(B(gamers[0],7),2),{1:4,300:2})

if __name__=='__main__': unittest.main()
