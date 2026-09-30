import asyncio
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1]))
import protocol
import test_protocol
from test_bot_ai import battle, gamer
from bot_ai import Decision
from hero_skills import effective_hero_skill, rabbit_power
from bot_presentation import skill_animation_barrier
from protocol import (parse_varint_field as V, parse_bytes_field as B,
    parse_bytes_fields as Bs, pb_bytes, pb_varint, encode_frame,
    pvp_gamer_with_state, pvp_gamer_with_buffs, pvp_gamer_skill_id,
    pvp_gamer_skill_cd, _hero_message)
from weapon_skills import LUCKY_STREAK_BUFF_ID
from server import serve_client, read_frame


class RabbitUpgradeTests(unittest.TestCase):
    _state = test_protocol.ProtocolTests._state

    def test_unlock_routes_and_inventory_preserved(self):
        for stars, purchased, stored, expected in (
            (4, False, 10000, 10000), (5, False, 10000, 10003),
            (0, True, 10000, 10003), (0, False, 10003, 10003)):
            entry = dict(id=0, starLevel=stars, skillId=stored,
                         skillUpgradeUnlocked=purchased)
            original = dict(entry)
            self.assertEqual(effective_hero_skill(entry), expected)
            self.assertEqual(V(_hero_message(entry), 4), expected)
            self.assertEqual(entry, original)

    def test_all_die_results_base_and_upgrade(self):
        for upgraded in (False, True):
            self.assertEqual([rabbit_power(r, upgraded=upgraded) for r in range(1, 7)],
                             [0, 0, 1, 1, 1, 2 if upgraded else 1])
        self.assertEqual(skill_animation_barrier(10003), skill_animation_barrier(10000))

    def test_bot_all_rolls_self_and_enemy(self):
        for sid in (10000, 10003):
            for target in (1, 2):
                for roll in range(1, 7):
                    with self.subTest(sid=sid, target=target, roll=roll):
                        actions = battle()
                        actions.gamers[1] = gamer(1, skill=sid, cd=0)
                        with patch.object(actions.rng, 'randint', return_value=roll):
                            packet, delay = actions.resolve(1, Decision('skill', target, 4, 'test'),
                                                            event_id=1, event_time=100)
                        power = rabbit_power(roll, upgraded=sid == 10003)
                        self.assertEqual(actions.hp[target], 2 + power if target == 1 else 2 - power)
                        self.assertEqual(actions.frenzy[target], 1)
                        self.assertEqual(V(packet, 2), sid)
                        self.assertEqual(pvp_gamer_skill_cd(actions.gamers[1]), 3)
                        self.assertGreater(delay, 6)

    def test_heal_cap_and_toxin(self):
        for hp, poisoned, expected in ((3, False, 4), (2, True, 3), (3, True, 3)):
            actions = battle()
            actions.hp[1] = hp
            actions.gamers[1] = gamer(1, skill=10003, cd=0)
            if poisoned:
                actions.gamers[1] = pvp_gamer_with_buffs(actions.gamers[1], add_cfg_ids=(10066,))
            with patch.object(actions.rng, 'randint', return_value=6):
                actions.resolve(1, Decision('skill', 1, 4, 'test'), event_id=1, event_time=100)
            self.assertEqual(actions.hp[1], expected)

    def test_lucky_modifier_applies_before_upgrade(self):
        actions = battle()
        actions.gamers[1] = pvp_gamer_with_buffs(gamer(1, skill=10003, cd=0), add_cfg_ids=(LUCKY_STREAK_BUFF_ID,))
        with patch.object(actions.rng, 'randint', return_value=4):
            actions.resolve(1, Decision('skill', 2, 4, 'test'), event_id=1, event_time=100)
        self.assertEqual(actions.hp[2], 0)

    def test_live_login_rolls_and_cooldown_rejection(self):
        async def exchange(roll, target):
            state = self._state({'selectedHero': 0,
                'heroes': [dict(id=0, starLevel=5, skillId=10000)],
                'heroGuns': [dict(heroId=0, gunId=0)]})
            state._accounts = {}; state._next_gid = 1000001; state.pvp_port = 0
            original = protocol._local_pvp_gamer
            def prepared(*args, **kwargs):
                g = original(*args, **kwargs)
                return pvp_gamer_with_state(g, hp=2, ammo_number=2,
                    fake_ammo_number=2, virtual_hp=1, round_number=1)
            listener = await asyncio.start_server(
                lambda r, w: serve_client(r, w, state, 'body', 'pvp'), '127.0.0.1', 0)
            reader, writer = await asyncio.open_connection('127.0.0.1', listener.sockets[0].getsockname()[1])
            async def receive(cmd, act, index=0):
                async with asyncio.timeout(4):
                    while True:
                        head, body, _ = await read_frame(reader, 'body')
                        if (head.cmd, head.act, head.index) == (cmd, act, index):
                            return head, body
            def request(act, body, index):
                writer.write(encode_frame(3, act, body, index=index, length_mode='body'))
            try:
                with patch('protocol._local_pvp_gamer', side_effect=prepared), \
                     patch('server.PVP_OPENING_SEQUENCE_DELAY', 0), \
                     patch('server.random.randint', return_value=roll):
                    request(1, pb_bytes(2, 'local-pvp:1:6:0:0'), 801)
                    _, login = await receive(3, 1, 801)
                    self.assertEqual(pvp_gamer_skill_id(Bs(B(login, 2), 2)[0]), 10003)
                    request(14, b'', 802); await receive(3, 14, 802); await receive(255, 1)
                    with patch('server.pvp_gamer_skill_cd', return_value=0):
                        request(6, pb_varint(1, target), 803)
                        head, _ = await receive(3, 6, 803)
                        self.assertEqual(head.error, 0)
                        _, notification = await receive(255, 2)
                    event = B(notification, 1)
                    self.assertEqual(V(event, 2), 10003)
                    fighters = Bs(B(notification, 2), 2)
                    power = rabbit_power(roll, upgraded=True)
                    self.assertEqual(V(fighters[target], 4), 2 + power if target == 0 else 2 - power)
                    self.assertEqual(pvp_gamer_skill_cd(fighters[0]), 3)
                    request(6, pb_varint(1, target), 804)
                    head, _ = await receive(3, 6, 804)
                    self.assertNotEqual(head.error, 0)
            finally:
                writer.close(); await writer.wait_closed()
                listener.close(); await listener.wait_closed()
        for roll in range(1, 7):
            for target in (0, 1):
                with self.subTest(roll=roll, target=target):
                    asyncio.run(exchange(roll, target))
