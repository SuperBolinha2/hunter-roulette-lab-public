import asyncio
from contextlib import ExitStack
import random
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1]))
from bot_ai import (DIFFICULTIES, ITEM_RULES, ITEM_BUFF_CFG, Decision, Fighter, Observation,
                    Offer, candidates, choose_action,
                    tranquilizer_frenzy_reduction)
from bot_actions import BattleActions, TurnRestrictions, has_buff
from bot_presentation import (skill_animation_barrier, card_animation_barrier,
                              NATIVE_SKILL_SHOW_TIME, NATIVE_SKILL_CUTSCENE_TIME)
from protocol import (encode_frame, parse_bytes_field, parse_bytes_fields,
                      parse_varint_field, pb_bytes, pb_message, pb_varint,
                      pvp_gamer_with_buffs, pvp_shop_card,
                      pvp_card_slot_body, pvp_gamer_with_state)
from server import (_pvp_apply_hp_damage, _resolve_hallucinogen_self_shot,
                    read_frame, serve_client)
import test_protocol as protocol_helpers


def gamer(i, hp=2, frenzy=1, coin=10000, real=1, blank=4, cd=1, skill=10001):
    return pb_message(pb_varint(3, i), pb_varint(4, hp), pb_varint(5, coin),
        pb_bytes(7, pb_message(pb_varint(1, 0))),
        pb_bytes(9, pb_message(pb_varint(1, 0), pb_varint(2, skill), pb_varint(3, cd))),
        pb_varint(17, frenzy), pb_varint(23, 2))


def battle(cfg=2015, stored=False):
    gamers = [gamer(i) for i in range(3)]
    card = pvp_shop_card(44, cfg, 200)
    if stored:
        from protocol import pvp_gamer_with_coin_and_card
        gamers[1] = pvp_gamer_with_coin_and_card(gamers[1], coin=10000,
                                               card_slot=pvp_card_slot_body(card))
    def wanted(target, source):
        gamers[target] = pvp_gamer_with_buffs(
            gamers[target], add_cfg_ids=(1020, 5002), source_index=source)
    return BattleActions(gamers, [2, 2, 2], [1, 1, 1], [1, 1, 1], [4, 4, 4],
        [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [False] * 3,
        [] if stored else [card], 1, 100, TurnRestrictions(), random.Random(4),
        reload=lambda _: (2, 2), draw=lambda r, f: 300 if f else 1,
        damage=_pvp_apply_hp_damage, forced_shot=_resolve_hallucinogen_self_shot,
        apply_wanted=wanted)


class BotPolicyTests(unittest.TestCase):
    def test_tranquilizer_reduces_ceil_half_current_hp_clamped_to_frenzy(self):
        cases = (
            (4, 2, 2),
            (3, 2, 2),
            (2, 2, 1),
            (1, 2, 1),
            (4, 1, 1),
            (0, 2, 0),
            (4, 0, 0),
        )
        for hp, frenzy, expected in cases:
            with self.subTest(hp=hp, frenzy=frenzy):
                self.assertEqual(
                    tranquilizer_frenzy_reduction(hp, frenzy), expected,
                )

    def test_targets_other_bot_while_human_alive(self):
        fighters = tuple(Fighter(i, 4, 1, 2, 2) for i in range(3))
        obs = Observation(1, fighters, preparations=3)
        targets = {choose_action(obs, random.Random(seed), "hard").target for seed in range(100)}
        self.assertIn(0, targets)
        self.assertIn(2, targets)

    def test_blank_heavy_magazine_can_choose_self(self):
        obs = Observation(1, tuple(Fighter(i, 4, 1, 1, 5) for i in range(3)), preparations=3)
        best = max(candidates(obs, "hard"), key=lambda c: c.score)
        self.assertEqual(best.target, 1)

    def test_dangerous_self_shot_scores_below_enemy_shot(self):
        obs = Observation(1, (Fighter(0, 4, 0, 2, 2), Fighter(1, 1, 0, 4, 1)))
        options = candidates(obs, "hard")
        self.assertLess(next(o.score for o in options if o.target == 1),
                        next(o.score for o in options if o.target == 0))

    def test_only_observations_go_to_policy(self):
        obs = Observation(1, tuple(Fighter(i, 4, 0, 2, 3) for i in range(3)))
        # Different authoritative outcomes cannot be an input: the policy has
        # no deck/order/die-roll field and is reproducible from observation/seed.
        self.assertEqual(choose_action(obs, random.Random(23)),
                         choose_action(obs, random.Random(23)))
        self.assertNotIn("deck", obs.__dataclass_fields__)
        self.assertNotIn("next_bullet", obs.__dataclass_fields__)

    def test_dead_targets_and_dead_actor_are_not_selected(self):
        obs = Observation(1, (Fighter(0, 0, 0, 3, 2), Fighter(1, 2, 0, 3, 2), Fighter(2, 2, 0, 3, 2)))
        self.assertTrue(all(d.target != 0 for d in candidates(obs)))
        self.assertEqual(candidates(Observation(0, obs.fighters)), ())

    def test_zero_hp_cannot_use_cigarette_even_with_frenzy(self):
        obs = Observation(1, (Fighter(0, 3, 0, 2, 2), Fighter(1, 0, 2, 2, 2, coin=1000)),
                          (Offer(1, 2011, 200),))
        self.assertFalse(any(d.offer for d in candidates(obs)))

    def test_ban_blocks_buy_but_allows_own_stored_item(self):
        obs = Observation(1, (Fighter(0, 4, 0, 2, 2),
                             Fighter(1, 2, 1, 2, 2, coin=1000, buffs=frozenset({1021}))),
                          (Offer(1, 2011, 200), Offer(2, 2015, 0, True)))
        items = [d for d in candidates(obs) if d.offer]
        self.assertTrue(items)
        self.assertTrue(all(d.offer.stored for d in items))

    def test_skill_ban_and_insufficient_coin_are_respected(self):
        obs = Observation(1, (Fighter(0, 4, 0, 2, 2), Fighter(1, 2, 2, 2, 2,
                          coin=99, skill_id=10001, buffs=frozenset({10018}))),
                          (Offer(1, 2015, 300),))
        self.assertTrue(all(d.kind == "shoot" for d in candidates(obs)))

    def test_unknown_and_unimplemented_cards_are_not_bought(self):
        obs = Observation(1, tuple(Fighter(i, 2, 1, 2, 2, coin=10000) for i in range(3)),
                          (Offer(1, 9999, 0), Offer(2, 2032, 600), Offer(3, 2034, 0)))
        selected = candidates(obs)
        self.assertTrue(all(d.offer is None or d.offer.cfg not in (9999, 2034)
                            for d in selected))
        self.assertTrue(any(d.offer is not None and d.offer.cfg == 2032
                            for d in selected))

    def test_difficulty_limits_preparation_and_self_shot_loops(self):
        self.assertLess(DIFFICULTIES["easy"].max_preparations, DIFFICULTIES["hard"].max_preparations)
        for difficulty, profile in DIFFICULTIES.items():
            obs = Observation(1, tuple(Fighter(i, 4, 0, 1, 5, coin=10000) for i in range(3)),
                              (Offer(1, 2015, 300),), profile.max_self_shots,
                              profile.max_preparations)
            self.assertTrue(all(d.kind == "shoot" and d.target != 1 for d in candidates(obs, difficulty)))

    def test_all_catalog_entries_have_descriptions(self):
        self.assertEqual(len(ITEM_RULES), 26)
        self.assertTrue(all(r.description and r.name for r in ITEM_RULES.values()))

    def test_enhanced_round_combination_is_not_sent_to_ordinary_item_resolver(self):
        obs = Observation(1, (Fighter(0, 3, 1, 2, 2, enhanced=1),
                              Fighter(1, 3, 1, 2, 2, coin=10000)),
                          (Offer(1, 2008, 200), Offer(2, 2001, 100)))
        self.assertTrue(all(d.offer is None for d in candidates(obs)))

    def test_bot_cannot_buy_above_its_own_balance(self):
        obs = Observation(1, tuple(Fighter(i, 2, 1, 2, 2, coin=50) for i in range(3)),
                          (Offer(1, 2011, 200), Offer(2, 2015, 300)))
        self.assertTrue(all(d.offer is None for d in candidates(obs)))


class BotActionTests(unittest.TestCase):
    def test_tranquilizer_bought_or_stored_reduces_target_frenzy_from_current_hp(self):
        for stored in (False, True):
            with self.subTest(stored=stored):
                state = battle(2029, stored=stored)
                state.hp[0] = 3
                state.frenzy[0] = 2
                state.gamers[0] = pvp_gamer_with_state(
                    state.gamers[0], hp=3, virtual_hp=2,
                    ammo_number=1, fake_ammo_number=4, round_number=1,
                )
                decision = next(
                    option for option in candidates(state.observation(1), "hard")
                    if option.offer is not None and option.target == 0
                )
                packet, _ = state.resolve(
                    1, decision, event_id=91, event_time=1000,
                    difficulty="hard",
                )
                self.assertEqual(state.frenzy[0], 0)
                self.assertEqual(parse_varint_field(state.gamers[0], 17), 0)
                target_event = next(
                    event for event in parse_bytes_fields(packet, 4)
                    if parse_varint_field(
                        parse_bytes_field(event, 2) or b"", 9,
                    ) == 14
                )
                target = parse_bytes_field(target_event, 2) or b""
                self.assertEqual(
                    parse_varint_field(target, 14), (-2) & ((1 << 64) - 1),
                )
                slot = parse_bytes_field(state.gamers[1], 18) or b""
                self.assertEqual(parse_varint_field(slot, 2) or 0, 0)

    def test_rocket_launcher_fake_and_live_outcomes_consume_expected_ammo(self):
        for stored, ammo_result in ((False, 300), (True, 1)):
            with self.subTest(stored=stored, ammo=ammo_result):
                state = battle(2032, stored=stored)
                state.real[1] = 3
                state.blank[1] = 1
                state.draw = lambda real, blank, result=ammo_result: result
                action = next(
                    d for d in candidates(state.observation(1), "hard")
                    if d.offer is not None and d.offer.cfg == 2032
                )
                result = state.resolve(1, action, event_id=91, event_time=1000,
                                       difficulty="hard")
                self.assertIsNotNone(result)
                packet, _ = result
                events = parse_bytes_fields(packet, 4)
                rpg = next(
                    event for event in events
                    if parse_varint_field(parse_bytes_field(event, 1) or b"", 9) == 39
                )
                source = parse_bytes_field(rpg, 1) or b""
                target = parse_bytes_field(rpg, 2) or b""
                used = [
                    (parse_varint_field(ammo, 1), parse_varint_field(ammo, 2))
                    for ammo in parse_bytes_fields(source, 12)
                ]
                if ammo_result == 300:
                    self.assertEqual(used, [(300, 1)])
                    self.assertEqual(parse_varint_field(source, 43), 0)
                    self.assertEqual(parse_varint_field(target, 2) or 0, 0)
                    self.assertEqual((state.real[1], state.blank[1]), (3, 0))
                else:
                    self.assertEqual(used, [(1, 3)])
                    self.assertEqual(parse_varint_field(source, 43), 1)
                    self.assertEqual(parse_varint_field(target, 2), (1 << 64) - 2)
                    self.assertEqual(parse_varint_field(target, 14), (1 << 64) - 1)
                    self.assertEqual((state.real[1], state.blank[1]), (2, 2))

    def test_every_enabled_cfg_resolves_with_the_real_actor(self):
        for cfg, rule in ITEM_RULES.items():
            if not rule.enabled:
                continue
            with self.subTest(cfg=cfg):
                state = battle(cfg)
                decisions = [d for d in candidates(state.observation(1), "hard") if d.offer]
                self.assertTrue(decisions, cfg)
                decision = max(decisions, key=lambda d: d.score)
                with patch("server.random.randrange", return_value=0):
                    result = state.resolve(1, decision, event_id=90, event_time=1000, difficulty="hard")
                self.assertIsNotNone(result)
                packet, delay = result
                self.assertEqual(parse_varint_field(packet, 3), 1)
                self.assertEqual(parse_varint_field(packet, 10), decision.target)
                self.assertEqual(parse_varint_field(packet, 5), cfg)
                self.assertGreater(delay, 0)
                self.assertEqual(parse_varint_field(state.shop[0], 5), 2)
                balance = parse_varint_field(state.gamers[1], 5)
                self.assertGreaterEqual(balance, 9800)
                self.assertLessEqual(balance, 10400)
                if cfg != 2018:
                    self.assertEqual(balance, 9800)
                    self.assertEqual(parse_varint_field(state.gamers[0], 5), 10000)

    def test_stored_item_is_consumed_without_charging_or_selling_stock(self):
        state = battle(2015, stored=True)
        action = next(d for d in candidates(state.observation(1)) if d.offer)
        packet, _ = state.resolve(1, action, event_id=10, event_time=1000)
        self.assertEqual(parse_varint_field(packet, 1), 8)
        self.assertEqual(parse_varint_field(state.gamers[1], 5), 10000)
        slot = parse_bytes_field(state.gamers[1], 18) or b""
        self.assertFalse(parse_varint_field(slot, 2))
        self.assertIsNone(state.resolve(1, action, event_id=11, event_time=1001))

    def test_stale_or_forged_action_does_not_mutate_wallet(self):
        state = battle()
        forged = Decision("item", 1, 100, "forged", Offer(999, 2015, 200))
        before = list(state.gamers)
        self.assertIsNone(state.resolve(1, forged, event_id=11, event_time=1001))
        self.assertEqual(before, state.gamers)
        self.assertEqual(parse_varint_field(state.shop[0], 5), 1)

    def test_buying_ban_is_enforced_without_charge(self):
        state = battle()
        action = next(d for d in candidates(state.observation(1)) if d.offer)
        state.restrictions.apply_to_gamer(state.gamers, 1, 2022, source_index=0)
        before = list(state.gamers)
        self.assertIsNone(state.resolve(1, action, event_id=11, event_time=1001))
        self.assertEqual(before, state.gamers)

    def test_turn_ban_buff_survives_snapshot_and_does_not_block_skill(self):
        state = battle(2022)
        from protocol import pvp_gamer_with_skill_cd
        state.gamers[1] = pvp_gamer_with_skill_cd(state.gamers[1], 0)
        buff_cfg = state.restrictions.apply_to_gamer(
            state.gamers, 1, 2022, source_index=0,
        )

        state.sync()
        self.assertEqual(buff_cfg, 1021)
        self.assertTrue(has_buff(state.gamers[1], 1021))
        options = candidates(state.observation(1))
        self.assertTrue(any(action.kind == "skill" for action in options))
        self.assertFalse(any(action.offer is not None for action in options))

        self.assertEqual(state.restrictions.start(1), ())
        self.assertTrue(has_buff(state.gamers[1], 1021))
        expired = state.restrictions.start(1)
        state.gamers[1] = pvp_gamer_with_buffs(
            state.gamers[1], del_cfg_ids=expired,
        )
        self.assertEqual(expired, (1021,))
        self.assertFalse(has_buff(state.gamers[1], 1021))

    def test_restrictions_last_the_targets_next_complete_turn_independently(self):
        restrictions = TurnRestrictions()
        restrictions.start(0)
        restrictions.apply(1, 2022)
        restrictions.apply(2, 2030)
        self.assertEqual(restrictions.start(1), ())
        self.assertEqual(restrictions.start(0), ())
        self.assertEqual(restrictions.start(2), ())
        self.assertEqual(restrictions.start(1), (1021,))
        self.assertIn((2, 2030), restrictions.deadlines)
        self.assertEqual(restrictions.start(2), (10018,))

    def test_bear_skill_converts_only_its_own_frenzy(self):
        state = battle()
        from protocol import pvp_gamer_with_skill_cd
        state.gamers[1] = pvp_gamer_with_skill_cd(state.gamers[1], 0)
        action = next(d for d in candidates(state.observation(1)) if d.kind == "skill")
        packet, _ = state.resolve(1, action, event_id=91, event_time=1000)
        self.assertEqual(state.hp, [2, 3, 2])
        self.assertEqual(state.frenzy, [1, 0, 1])
        self.assertEqual(parse_varint_field(packet, 3), 1)
        for small in parse_bytes_fields(packet, 4):
            self.assertEqual(parse_varint_field(parse_bytes_field(small, 1), 1), 1)

    def test_buff_items_emit_native_hud_ids_not_item_ids(self):
        for cfg in (2022, 2030, 2033):
            with self.subTest(cfg=cfg):
                state = battle(cfg)
                action = next(d for d in candidates(state.observation(1)) if d.offer)
                packet, _ = state.resolve(1, action, event_id=91, event_time=1000)
                expected = ITEM_BUFF_CFG[cfg]
                self.assertTrue(has_buff(state.gamers[action.target], expected))
                self.assertFalse(has_buff(state.gamers[action.target], cfg))
                added = [parse_varint_field(b, 1) for event in parse_bytes_fields(packet, 4)
                         for b in parse_bytes_fields(parse_bytes_field(event, 2) or b"", 25)]
                self.assertIn(expected, added)

    def test_bear_hp_and_frenzy_effects_are_in_skill_packet_not_deferred_to_shot(self):
        state = battle()
        from protocol import pvp_gamer_with_skill_cd
        state.gamers[1] = pvp_gamer_with_skill_cd(state.gamers[1], 0)
        action = next(d for d in candidates(state.observation(1)) if d.kind == "skill")
        packet, wait = state.resolve(1, action, event_id=91, event_time=1000)
        effect = parse_bytes_field(parse_bytes_fields(packet, 4)[-1], 2)
        self.assertEqual(parse_varint_field(effect, 2), 1)  # hp delta
        self.assertEqual(parse_varint_field(effect, 14), (1 << 64) - 1)  # Frenzy -1
        self.assertEqual(parse_varint_field(effect, 28), 1000)
        self.assertEqual(wait, skill_animation_barrier(10001))

    def test_animation_barriers_include_skill_ui_and_recovery(self):
        for sid, native in NATIVE_SKILL_SHOW_TIME.items():
            self.assertGreater(skill_animation_barrier(sid), native + NATIVE_SKILL_CUTSCENE_TIME[sid])
        self.assertEqual(skill_animation_barrier(10001), 9.75)
        self.assertGreater(card_animation_barrier("energy", stored=False, resolver_wait=5), 5)
        self.assertGreater(card_animation_barrier("heal", stored=False, resolver_wait=6), 6)

    def test_surprise_box_awards_a_resolvable_stored_item(self):
        state = battle(2020)
        action = next(d for d in candidates(state.observation(1)) if d.offer)
        state.resolve(1, action, event_id=91, event_time=1000)
        slot = parse_bytes_field(state.gamers[1], 18) or b""
        cfg = parse_varint_field(slot, 2)
        self.assertTrue(ITEM_RULES[cfg].enabled)
        self.assertNotEqual(ITEM_RULES[cfg].effect, "box")

    def test_duplicate_damage_buff_is_not_bought_again(self):
        state = battle(2015)
        state.gamers[1] = pvp_gamer_with_buffs(state.gamers[1], add_cfg_ids=(1014,))
        self.assertFalse(any(d.offer for d in candidates(state.observation(1))))

    def test_generic_box_events_have_unique_subevent_ids(self):
        state = battle(2020)
        decision = next(d for d in candidates(state.observation(1)) if d.offer)
        packet, _ = state.resolve(1, decision, event_id=91, event_time=1000)
        ids = [parse_varint_field(event, 4) for event in parse_bytes_fields(packet, 4)]
        self.assertEqual(ids, [1, 2, 3])

    def test_lucky_hero_skill_outlines_use_the_bot_index(self):
        state = battle()
        state.gamers[1] = gamer(1, cd=0, skill=10000)
        decision = next(d for d in candidates(state.observation(1)) if d.kind == "skill")
        packet, _ = state.resolve(1, decision, event_id=91, event_time=1000)
        for small in parse_bytes_fields(packet, 4):
            self.assertEqual(parse_varint_field(parse_bytes_field(small, 1), 1), 1)


class BotWireTests(unittest.TestCase):
    def test_trio_utility_bots_buy_and_use_with_own_actor(self):
        state = protocol_helpers.ProtocolTests()._state({"selectedHero": 0})
        state._accounts, state._next_gid, state.pvp_port = {}, 1000001, 0
        state.bot_difficulty, state.bot_seed = "hard", 7
        async def run():
            listener = await asyncio.start_server(
                lambda r, w: serve_client(r, w, state, "body", "pvp"), "127.0.0.1", 0)
            reader, writer = await asyncio.open_connection("127.0.0.1", listener.sockets[0].getsockname()[1])
            try:
                async def receive(cmd, act, index=0):
                    async with asyncio.timeout(5):
                        while True:
                            head, body, _ = await read_frame(reader, "body")
                            if (head.cmd, head.act, head.index) == (cmd, act, index):
                                return head, body
                writer.write(encode_frame(3, 1, pb_bytes(2, "local-pvp:1:6:0:0"), index=1, length_mode="body"))
                await receive(3, 1, 1)
                writer.write(encode_frame(3, 14, b"", index=2, length_mode="body"))
                await receive(3, 14, 2)
                await receive(255, 1)
                writer.write(encode_frame(3, 3, pb_varint(1, 1), index=3, length_mode="body"))
                ack, _ = await receive(3, 3, 3)
                self.assertEqual(ack.error, 0)
                actors, targets, items = [], [], []
                async with asyncio.timeout(5):
                    while len(actors) < 2:
                        head, body, _ = await read_frame(reader, "body")
                        if (head.cmd, head.act) != (255, 2):
                            continue
                        packet = parse_bytes_field(body, 1) or b""
                        actor = parse_varint_field(packet, 3) or 0
                        typ = parse_varint_field(packet, 1)
                        if actor in (1, 2) and typ in (7, 8):
                            items.append(packet)
                        if actor in (1, 2) and typ == 1:
                            actors.append(actor)
                            targets.append(parse_varint_field(packet, 10) or 0)
                self.assertTrue(items)
                self.assertEqual(set(actors), {1, 2})
                self.assertTrue(all(target in (0, 1, 2) for target in targets))
                self.assertTrue(all(parse_varint_field(p, 3) in (1, 2) for p in items))
            finally:
                writer.close()
                await writer.wait_closed()
                listener.close()
                await listener.wait_closed()
                await asyncio.sleep(.01)
        with ExitStack() as stack:
            stack.enter_context(patch("server._random_shop_specs", return_value=(
                (2009, 200), (2015, 300), (2016, 300), (2011, 200))))
            for timing in ("PVP_OPENING_SEQUENCE_DELAY", "PLAYER_OTHER_SHOT_SETTLE", "PLAYER_SELF_SHOT_SETTLE",
                           "BOT_THINK_DELAY", "BOT_SHOT_SETTLE", "BOT_RAISE_GUN_DELAY",
                           "BOT_SELECT_TARGET_DELAY", "BOT_ACTION_DECISION_DELAY", "PREPARE_SIGNAL_DELAY"):
                stack.enter_context(patch("server." + timing, 0.0))
            # Preserve actual packets/resolution while accelerating only animation waits.
            original = BattleActions.resolve
            def quick(*args, **kwargs):
                result = original(*args, **kwargs)
                return (result[0], 0.0) if result else None
            stack.enter_context(patch("server.BattleActions.resolve", quick))
            stack.enter_context(patch("server.random.randrange", side_effect=lambda n: n - 1))
            asyncio.run(run())


    def test_bot_blank_self_shots_continue_then_bank_its_own_bounty(self):
        state = protocol_helpers.ProtocolTests()._state({"selectedHero": 0})
        state._accounts, state._next_gid, state.pvp_port = {}, 1000001, 0
        state.bot_difficulty, state.bot_seed = "hard", 7
        async def run():
            listener = await asyncio.start_server(
                lambda r, w: serve_client(r, w, state, "body", "pvp"), "127.0.0.1", 0)
            reader, writer = await asyncio.open_connection("127.0.0.1", listener.sockets[0].getsockname()[1])
            try:
                async def receive(cmd, act, index=0):
                    async with asyncio.timeout(5):
                        while True:
                            head, body, _ = await read_frame(reader, "body")
                            if (head.cmd, head.act, head.index) == (cmd, act, index):
                                return head, body
                writer.write(encode_frame(3, 1, pb_bytes(2, "local-pvp:1:6:0:0"), index=1, length_mode="body"))
                await receive(3, 1, 1)
                writer.write(encode_frame(3, 14, b"", index=2, length_mode="body"))
                await receive(3, 14, 2)
                await receive(255, 1)
                writer.write(encode_frame(3, 3, pb_varint(1, 1), index=3, length_mode="body"))
                ack, _ = await receive(3, 3, 3)
                self.assertEqual(ack.error, 0)
                actors, targets, items = [], [], []
                async with asyncio.timeout(5):
                    while len(actors) < 4:
                        head, body, _ = await read_frame(reader, "body")
                        if (head.cmd, head.act) != (255, 2):
                            continue
                        packet = parse_bytes_field(body, 1) or b""
                        actor = parse_varint_field(packet, 3) or 0
                        typ = parse_varint_field(packet, 1)
                        if actor in (1, 2) and typ in (7, 8):
                            items.append(packet)
                        if actor in (1, 2) and typ == 1:
                            actors.append(actor)
                            targets.append(parse_varint_field(packet, 10) or 0)
                self.assertFalse(items)
                self.assertEqual(set(actors), {1, 2})
                self.assertEqual(actors, [1, 1, 1, 2])
                self.assertEqual(targets, [1, 1, 2, 0])
                last_info = parse_bytes_field(body, 2) or b""
                last_gamers = parse_bytes_fields(last_info, 2)
                self.assertGreater(parse_varint_field(last_gamers[1], 5), 10000)
                self.assertTrue(all(parse_varint_field(p, 3) in (1, 2) for p in items))
            finally:
                writer.close()
                await writer.wait_closed()
                listener.close()
                await listener.wait_closed()
                await asyncio.sleep(.01)
        with ExitStack() as stack:
            for timing in ("PVP_OPENING_SEQUENCE_DELAY", "PLAYER_OTHER_SHOT_SETTLE", "PLAYER_SELF_SHOT_SETTLE",
                           "BOT_THINK_DELAY", "BOT_SHOT_SETTLE", "BOT_RAISE_GUN_DELAY",
                           "BOT_SELECT_TARGET_DELAY", "PREPARE_SIGNAL_DELAY"):
                stack.enter_context(patch("server." + timing, 0.0))
            # Preserve actual packets/resolution while accelerating only animation waits.
            original = BattleActions.resolve
            def quick(*args, **kwargs):
                result = original(*args, **kwargs)
                return (result[0], 0.0) if result else None
            stack.enter_context(patch("server.BattleActions.resolve", quick))
            stack.enter_context(patch("server.random.randrange", return_value=0))
            def self_then_attack(obs, rng, difficulty):
                target = obs.actor if obs.actor == 1 and obs.self_shot_streak < 2 else (2 if obs.actor == 1 else 0)
                return Decision("shoot", target, 1, "scripted continuation regression")
            stack.enter_context(patch("server.choose_action", self_then_attack))
            asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
