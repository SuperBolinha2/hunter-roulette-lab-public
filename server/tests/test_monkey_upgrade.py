import asyncio
import random
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1]))
import test_protocol
from hero_skills import effective_hero_skill
from hero_shop import monkey_convert_shop, monkey_candidates
from protocol import (parse_varint_field as V, parse_bytes_field as B,
    parse_bytes_fields as Bs, pvp_shop_card, pb_bytes, pb_varint, pb_message,
    encode_frame, pvp_gamer_skill_id, pvp_gamer_skill_cd)
from test_bot_ai import battle, gamer
from bot_ai import Decision, ITEM_BUFF_CFG
from bot_presentation import skill_animation_barrier
from protocol import pvp_gamer_with_buffs
from server import serve_client, read_frame


def stock():
    return tuple(pvp_shop_card(i + 1, cfg, 200) for i, cfg in enumerate((2001, 2003, 2004, 2008)))


class MonkeyUpgradeTests(unittest.TestCase):
    _state = test_protocol.ProtocolTests._state

    def test_unlock(self):
        for stars, purchased, expected in ((4, False, 10002), (5, False, 10013), (0, True, 10013)):
            entry = dict(id=13, skillId=10002, starLevel=stars, skillUpgradeUnlocked=purchased)
            original = dict(entry)
            self.assertEqual(effective_hero_skill(entry), expected)
            self.assertEqual(entry, original)

    def test_base_two_upgrade_three_random_without_reordering(self):
        original = stock()
        outcomes = set()
        for upgraded in (False, True):
            for seed in range(15):
                cards, next_id, count = monkey_convert_shop(original, upgraded=upgraded,
                                                            next_id=50, rng=random.Random(seed))
                self.assertEqual(count, 3 if upgraded else 2)
                changed = tuple(i for i, card in enumerate(cards) if card != original[i])
                outcomes.add(changed)
                for i in changed:
                    self.assertEqual((V(cards[i], 2), V(cards[i], 3), V(cards[i], 5)), (2036, 0, 1))
                    self.assertGreaterEqual(V(cards[i], 1), 50)
                self.assertEqual(next_id, 50 + count)
                self.assertEqual(len({V(c, 1) for c in cards}), 4)
        self.assertGreater(len(outcomes), 2)

    def test_sold_free_and_empty_slots(self):
        sold = pvp_shop_card(9, 2001, 200, status=2)
        free = pvp_shop_card(10, 2036, 0)
        for source in ((), (sold, free), (sold, free, pvp_shop_card(11, 2004, 100))):
            cards, next_id, count = monkey_convert_shop(source, upgraded=True, next_id=1, rng=random.Random(1))
            self.assertEqual(count, len(monkey_candidates(source)))
            if source:
                self.assertEqual(cards[:2], source[:2])
                self.assertGreater(next_id, 11 if count else 10)

    def test_bot_event_native_shop_and_cooldown(self):
        for sid, count in ((10002, 2), (10013, 3)):
            actions = battle(); actions.shop[:] = stock()
            actions.gamers[1] = gamer(1, cd=0, skill=sid)
            old_hp, old_frenzy = list(actions.hp), list(actions.frenzy)
            packet, wait = actions.resolve(1, Decision('skill', 1, 4, 'test'), event_id=5, event_time=100)
            self.assertEqual(sum(V(c, 2) == 2036 for c in actions.shop), count)
            self.assertEqual(pvp_gamer_skill_cd(actions.gamers[1]), 3)
            self.assertEqual((actions.hp, actions.frenzy), (old_hp, old_frenzy))
            events = Bs(packet, 4)
            shop = next(B(e, 2) for e in events if V(B(e, 2), 9) == 38)
            self.assertEqual(Bs(shop, 42), actions.shop)
            self.assertEqual(wait, skill_animation_barrier(sid))

    def test_bot_skill_ban_and_no_eligible_offers(self):
        for blocked in (False, True):
            actions = battle(); actions.shop[:] = stock() if blocked else []
            actions.gamers[1] = gamer(1, cd=0, skill=10013)
            if blocked:
                actions.gamers[1] = pvp_gamer_with_buffs(actions.gamers[1], add_cfg_ids=(ITEM_BUFF_CFG[2030],))
            self.assertIsNone(actions.resolve(1, Decision('skill', 1, 4, 'test'), event_id=5, event_time=100))

    def test_tcp_skill_and_free_box_purchase(self):
        async def exchange(stars, count):
            state = self._state({'selectedHero': 13,
                'heroes': [dict(id=13, starLevel=stars, skillId=10002)],
                'heroGuns': [dict(heroId=13, gunId=0)]})
            state._accounts = {}; state._next_gid = 1000001; state.pvp_port = 0
            listener = await asyncio.start_server(lambda r, w: serve_client(r, w, state, 'body', 'pvp'), '127.0.0.1', 0)
            reader, writer = await asyncio.open_connection('127.0.0.1', listener.sockets[0].getsockname()[1])
            async def receive(cmd, act, index=0):
                async with asyncio.timeout(4):
                    while True:
                        head, body, _ = await read_frame(reader, 'body')
                        if (head.cmd, head.act, head.index) == (cmd, act, index): return head, body
            def request(act, body, index):
                writer.write(encode_frame(3, act, body, index=index, length_mode='body'))
            try:
                with patch('server.PVP_OPENING_SEQUENCE_DELAY', 0):
                    request(1, pb_bytes(2, 'local-pvp:1:6:13:0'), 901)
                    _, login = await receive(3, 1, 901)
                    self.assertEqual(pvp_gamer_skill_id(Bs(B(login, 2), 2)[0]), 10013 if stars == 5 else 10002)
                    request(14, b'', 902); await receive(3, 14, 902); await receive(255, 1)
                    with patch('server.pvp_gamer_skill_cd', return_value=0):
                        request(6, pb_varint(1, 0), 903)
                        head, _ = await receive(3, 6, 903); self.assertEqual(head.error, 0)
                        _, notification = await receive(255, 2)
                    info = B(notification, 2)
                    boxes = [c for c in Bs(info, 7) if V(c, 2) == 2036 and V(c, 3) == 0]
                    self.assertEqual(len(boxes), count)
                    player = Bs(info, 2)[0]; coin = V(player, 5)
                    self.assertEqual(pvp_gamer_skill_cd(player), 3)
                    request(6, pb_varint(1, 0), 904)
                    head, _ = await receive(3, 6, 904); self.assertNotEqual(head.error, 0)
                    request(5, pb_message(pb_varint(1, V(boxes[0], 1)), pb_varint(2, 0), pb_varint(4, 1)), 905)
                    head, _ = await receive(3, 5, 905); self.assertEqual(head.error, 0)
                    _, opened = await receive(255, 2)
                    self.assertEqual(V(Bs(B(opened, 2), 2)[0], 5), coin)
                    consumed = next(c for c in Bs(B(opened, 2), 7) if V(c, 1) == V(boxes[0], 1))
                    self.assertEqual(V(consumed, 5), 2)
            finally:
                writer.close(); await writer.wait_closed(); listener.close(); await listener.wait_closed()
        for stars, count in ((4, 2), (5, 3)):
            with self.subTest(stars=stars): asyncio.run(exchange(stars, count))
