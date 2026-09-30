import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]))
from server import PVP_LAB_SHOP_SPECS, PVP_LAB_REWARD_SPECS, _random_shop_specs, _replenish_sold_shop_cards
from protocol import pvp_shop_card, parse_varint_field

class ShopExclusionsTests(unittest.TestCase):
    def test_bucket_not_sold_but_preserved_as_reward(self):
        self.assertNotIn(2033,dict(PVP_LAB_SHOP_SPECS))
        self.assertIn(2033,dict(PVP_LAB_REWARD_SPECS))
        for _ in range(40):
            self.assertNotIn(2033,dict(_random_shop_specs()))
        cards,_=_replenish_sold_shop_cards([pvp_shop_card(1,2001,100,status=2)],10,2)
        self.assertNotIn(2033,[parse_varint_field(c,2) for c in cards])
