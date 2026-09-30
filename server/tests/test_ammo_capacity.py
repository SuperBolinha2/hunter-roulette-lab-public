"""Add-round items use weapon capacity, including enhanced ammunition."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))
from protocol import GUN_AMMO_SPECS, pb_message, pb_bytes, pb_varint, pvp_gamer_has_ammo_space
from bot_ai import Fighter, ItemRule, _item_score
from test_bot_ai import battle


class AmmoCapacityTests(unittest.TestCase):
    def test_all_weapons_and_enhanced_rounds(self):
        for gun_id, (capacity, _) in enumerate(GUN_AMMO_SPECS):
            gamer = pb_message(pb_bytes(7, pb_varint(1, gun_id)))
            with self.subTest(gun=gun_id):
                self.assertFalse(pvp_gamer_has_ammo_space(gamer, 1, capacity - 1))
                self.assertFalse(pvp_gamer_has_ammo_space(gamer, 0, capacity - 1, 1))
                self.assertFalse(pvp_gamer_has_ammo_space(gamer, 1, capacity))
                self.assertTrue(pvp_gamer_has_ammo_space(gamer, 1, capacity - 2))

    def test_bot_uses_target_capacity_not_eight(self):
        actor = Fighter(1, 2, 1, 1, 3, capacity=4)
        target = Fighter(2, 2, 1, 1, 5, capacity=6)
        self.assertIsNone(_item_score(ItemRule('real', '', 'real'), actor, actor))
        self.assertIsNone(_item_score(ItemRule('blank', '', 'blank'), actor, target))

    def test_bot_full_target_is_not_a_candidate(self):
        from bot_ai import candidates
        actions = battle(cfg=2004)
        actions.real[:] = [1, 1, 1]
        actions.blank[:] = [5, 5, 5]
        before = (list(actions.gamers), list(actions.shop))
        self.assertFalse(any(d.kind == 'item' for d in candidates(actions.observation(1))))
        self.assertEqual(before, (actions.gamers, actions.shop))
