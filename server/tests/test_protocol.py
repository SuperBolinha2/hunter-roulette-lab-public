import asyncio
import sys
import json
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1]))

from protocol import (  # noqa: E402
    HEADER_SIZE,
    BURST_MODE_BUFF_CFG_ID,
    MAINTENANCE_KIT_BUFF_CFG_ID,
    WANTED_PARENT_BUFF_CFG_ID,
    WANTED_REWARD_BUFF_CFG_ID,
    WANTED_REWARD_R_CHIPS,
    PVP_UPDATE_GAMER_DEAD_STATUS_EVENT,
    LAB_HERO_SKILLS,
    decode_header,
    decode_varint,
    encode_frame,
    encode_varint,
    fashion_update_body,
    explore_box_info_body,
    explore_box_notify_body,
    explore_box_award_all_body,
    explore_box_award_body,
    explore_box_open_all_body,
    explore_box_open_body,
    hero_card_ready_body,
    hero_card_unlock_body,
    hero_gun_update_body,
    local_bot_start_body,
    login_data_body,
    parse_bytes_field,
    parse_bytes_fields,
    parse_varint_field,
    pvp_gun_ammo_counts,
    pb_bytes,
    pb_message,
    pb_varint,
    response_body,
    pvp_login_body,
    pvp_login_snapshot,
    pvp_login_snapshot,
    pvp_bet_simple_body,
    pvp_gamer_load_body,
    pvp_initial_ammo_body,
    pvp_observer_count_body,
    pvp_surrender_body,
    pvp_next_round_body,
    pvp_shoot_event_result_body,
    pvp_event_notification_body,
    pvp_buy_card_event_result_body,
    pvp_generic_card_event_result_body,
    pvp_wanted_expiry_event_result_body,
    pvp_buff_countdown_event_result_body,
    pvp_hero_skill_event_result_body,
    pvp_refresh_shop_event_result_body,
    pvp_gamer_with_coin_and_card,
    pvp_gamer_with_buffs,
    pvp_info_with_shop,
    pvp_shop_card,
    pvp_card_slot_body,
    pvp_carried_card_slot_body,
    pvp_empty_card_slot_body,
    pvp_info_with_state,
    pvp_piggybank_use_event_result_body,
    pvp_hallucinogen_use_event_result_body,
    pvp_spare_magazine_event_result_body,
    pvp_wet_cigarette_event_result_body,
    pvp_gamer_with_event_status,
    pvp_gamer_with_state,
    pvp_gamer_with_skill_cd,
    pvp_gamer_skill_cd,
    pvp_gamer_skill_id,
    _ammo_message,
    market_purchase_body,
    bag_get_pack_body,
    bag_sell_body,
    bag_use_body,
    home_income_body,
    home_open_box_body,
    home_sell_box_body,
    home_start_box_body,
    season_get_info_body,
    season_open_body,
    season_state,
    server_time_body,
    _ammo_sort_id,
)
from server import (  # noqa: E402
    GameState, _random_shop_specs, _replenish_sold_shop_cards,
    _maintenance_kit_expires_after_shot, _pvp_apply_hp_damage,
    _pvp_bot_timing, _pvp_frenzy_after_shot, _pvp_is_eliminated,
    _pvp_shot_damage, _pvp_burst_shot_state,
    _pvp_wet_cigarette_heal,
    _pvp_apply_wanted, _pvp_tick_wanted,
    _resolve_hallucinogen_self_shot,
    _pvp_resolve_rocket_shot,
    frame_record, read_frame, serve_client,
)


class ProtocolTests(unittest.TestCase):
    def test_opening_panel_covers_character_specific_camera_return(self) -> None:
        from server import pvp_opening_cinema_delay
        with patch('server.PVP_OPENING_SEQUENCE_DELAY', 11.0):
            for hero, duration in ((17, 6.4), (1, 6.8666668), (0, 8.0)):
                gamer = pb_bytes(9, pb_varint(1, hero))
                self.assertAlmostEqual(pvp_opening_cinema_delay(gamer), duration - 0.1)
        with patch('server.PVP_OPENING_SEQUENCE_DELAY', 0):
            self.assertEqual(pvp_opening_cinema_delay(pb_bytes(9, pb_varint(1, 17))), 0)

    def test_rocket_launcher_draws_one_round_and_live_hit_consumes_all_live(self) -> None:
        gamers = [
            pvp_gamer_with_state(
                pb_message(
                    pb_varint(3, index), pb_varint(23, 2),
                    pb_bytes(7, pb_message(pb_varint(1, 0))),
                ),
                hp=4, ammo_number=3, fake_ammo_number=2,
                enhanced_ammo_number=0, round_number=1, virtual_hp=1,
            )
            for index in range(3)
        ]
        hp = [4, 4, 4]
        frenzy = [1, 1, 1]
        real = [3, 3, 3]
        fake = [2, 2, 2]
        enhanced = [0, 0, 0]

        with patch("server._draw_ejected_ammo", return_value=300):
            blank = _pvp_resolve_rocket_shot(
                gamers, hp, frenzy, real, fake, enhanced, 0, 1,
                round_number=1,
            )
        self.assertIsNotNone(blank)
        self.assertEqual(blank.ammo_cfg_id, 300)
        self.assertEqual(blank.consumed_ammo, ((300, 1),))
        self.assertEqual(blank.damage, 0)
        self.assertEqual((real[0], fake[0]), (3, 1))
        self.assertEqual((hp[1], frenzy[1]), (4, 1))
        self.assertEqual(blank.shooter_virtual_hp_delta, -1)

        hp = [4, 4, 4]
        frenzy = [1, 1, 1]
        real = [3, 3, 3]
        fake = [2, 2, 2]
        enhanced = [0, 0, 0]
        with patch("server._draw_ejected_ammo", return_value=1), patch(
            "server.pvp_gun_ammo_counts", return_value=(4, 2)
        ):
            live = _pvp_resolve_rocket_shot(
                gamers, hp, frenzy, real, fake, enhanced, 0, 1,
                round_number=1,
            )
        self.assertIsNotNone(live)
        self.assertEqual(live.consumed_ammo, ((1, 3),))
        self.assertEqual(live.damage, 3)
        self.assertEqual((hp[1], frenzy[1]), (1, 1))
        self.assertEqual((real[0], fake[0]), (4, 2))
        self.assertEqual(live.reload_ammo_after, (4, 2))
        self.assertEqual(live.shooter_virtual_hp_delta, 1)

    def test_rocket_launcher_event_consumes_source_ammo_and_queues_reload(self) -> None:
        player = pb_message(pb_varint(3, 0))
        bot = pb_message(pb_varint(3, 1))
        card = pvp_shop_card(5, 2032, 600)
        result = pvp_generic_card_event_result_body(
            player,
            bot,
            card,
            skill_id=10011,
            target_index=1,
            event_id=61,
            event_type=39,
            hp_delta=-3,
            virtual_hp_delta=-1,
            is_rpg_hit=True,
            source_u_ammo=(_ammo_message(1, 3, 3),),
            source_virtual_hp_delta=1,
            target_dead=True,
            reload_ammo_after=(4, 2),
            coin_delta=-600,
            buy=True,
        )
        events = parse_bytes_fields(result, 4)
        rpg_event = events[-2]
        source = parse_bytes_field(rpg_event, 1) or b""
        target = parse_bytes_field(rpg_event, 2) or b""
        self.assertEqual(parse_varint_field(source, 9), 39)
        self.assertEqual(parse_varint_field(source, 43), 1)
        self.assertEqual(
            [(parse_varint_field(ammo, 1), parse_varint_field(ammo, 2))
             for ammo in parse_bytes_fields(source, 12)],
            [(1, 3)],
        )
        self.assertEqual(parse_varint_field(source, 14), 1)
        self.assertEqual(parse_varint_field(target, 2), (1 << 64) - 3)
        self.assertEqual(parse_varint_field(target, 14), (1 << 64) - 1)
        self.assertEqual(parse_varint_field(target, 68), 1)

        reload_event = events[-1]
        reload_target = parse_bytes_field(reload_event, 2) or b""
        self.assertEqual(parse_varint_field(reload_target, 9), 1)
        self.assertEqual(parse_varint_field(reload_target, 8), 1)
        self.assertEqual(
            [(parse_varint_field(ammo, 1), parse_varint_field(ammo, 2))
             for ammo in parse_bytes_fields(reload_target, 5)],
            [(300, 2), (1, 4)],
        )

    def test_wanted_individual_deadlines_and_countdown_protocol(self) -> None:
        gamers = [pb_message(
            pb_varint(4, 4), pb_varint(5, 10_000), pb_varint(17, 2),
            pb_varint(99, 777),
        ) for _ in range(3)]
        gamers[1] = pvp_gamer_with_buffs(
            gamers[1], add_cfg_ids=(1014,), source_index=2,
        )
        rewards, expiry = [0, 0, 0], [0, 0, 0]
        self.assertEqual(_pvp_apply_wanted(gamers, 1, rewards, expiry, 0), 3)
        self.assertEqual(expiry, [0, 3, 0])
        # Nothing during this same turn consumes the budget: only a new clock
        # value from the next active character reduces the remaining turns.
        self.assertEqual(_pvp_tick_wanted(gamers, rewards, expiry, 0), [(1, 3, 0)])
        self.assertEqual(_pvp_tick_wanted(gamers, rewards, expiry, 1), [(1, 2, 0)])
        countdown = pvp_buff_countdown_event_result_body(
            gamers[1], target_index=1, event_id=20,
        )
        # Passive branch: do not clear selection/rotate players during a shot.
        self.assertEqual(parse_varint_field(countdown, 1), 17)
        event = parse_bytes_fields(countdown, 4)[0]
        outline = parse_bytes_field(event, 2) or b""
        self.assertEqual(parse_varint_field(outline, 9), 25)
        buffs = parse_bytes_fields(outline, 3)
        self.assertEqual([parse_varint_field(b, 1) for b in buffs], [1020, 5002])
        self.assertEqual([parse_varint_field(b, 7) for b in buffs], [2, 2])
        self.assertEqual([parse_varint_field(b, 4) for b in buffs], [1, 1])
        self.assertEqual([parse_varint_field(b, 5) for b in buffs], [3, 3])
        self.assertEqual(parse_bytes_fields(outline, 24), [])
        self.assertEqual(parse_bytes_fields(outline, 25), [])
        # A mark from another source applied one turn later has a later deadline.
        self.assertEqual(
            _pvp_apply_wanted(gamers, 0, rewards, expiry, 1, source_index=1), 3,
        )
        self.assertEqual(expiry, [4, 3, 0])
        self.assertEqual(_pvp_tick_wanted(gamers, rewards, expiry, 2),
                         [(0, 2, 0), (1, 1, 0)])
        self.assertEqual(_pvp_tick_wanted(gamers, rewards, expiry, 3),
                         [(0, 1, 0), (1, 0, 4)])
        self.assertEqual(parse_varint_field(gamers[1], 5), 10_004)
        self.assertEqual(parse_varint_field(gamers[0], 5), 10_000)
        self.assertEqual(
            [parse_varint_field(b, 1) for b in parse_bytes_fields(gamers[1], 8)],
            [1014],
        )
        self.assertEqual(parse_varint_field(gamers[1], 99), 777)
        self.assertEqual(_pvp_tick_wanted(gamers, rewards, expiry, 4), [(0, 0, 4)])
        self.assertEqual(parse_varint_field(gamers[0], 5), 10_004)
        self.assertEqual(_pvp_tick_wanted(gamers, rewards, expiry, 5), [])

    def test_wanted_duration_is_fixed_at_application_for_living_participants(self) -> None:
        for count in (2, 3, 4, 6, 8):
            with self.subTest(participants=count):
                gamers = [pb_message(pb_varint(4, 4)) for _ in range(count)]
                # A defeated seat does not get an active turn in the rotation.
                gamers.append(pb_message(pb_varint(4, 0), pb_varint(17, 0)))
                rewards, expiry = [0] * len(gamers), [0] * len(gamers)
                self.assertEqual(_pvp_apply_wanted(gamers, 0, rewards, expiry, 7), count)
                self.assertEqual(expiry[0], 7 + count)

    def test_burst_mode_is_consumed_by_self_shot_without_double_shot(self) -> None:
        self.assertEqual(_pvp_burst_shot_state(1, 0, 0), (True, False))
        self.assertEqual(_pvp_burst_shot_state(1, 0, 1), (True, True))
        self.assertEqual(_pvp_burst_shot_state(0, 0, 1), (False, False))

    def test_frenzy_changes_only_for_fake_miss_or_real_damage_on_opponent(self) -> None:
        self.assertEqual(
            _pvp_frenzy_after_shot(1, 2, 300, 0, 0, 1), (0, -1)
        )
        self.assertEqual(
            _pvp_frenzy_after_shot(0, 2, 1, 1, 0, 1), (1, 1)
        )
        self.assertEqual(
            _pvp_frenzy_after_shot(1, 2, 1, 0, 0, 1), (1, 0)
        )
        self.assertEqual(
            _pvp_frenzy_after_shot(0, 2, 300, 0, 0, 0), (0, 0)
        )
        self.assertEqual(
            _pvp_frenzy_after_shot(2, 2, 1, 1, 0, 1), (2, 0)
        )

    def test_spectator_bot_phase_keeps_every_shot_but_shortens_idle_timing(self) -> None:
        self.assertEqual(
            _pvp_bot_timing(player_eliminated=False), (5.0, 3.0)
        )
        self.assertEqual(
            _pvp_bot_timing(player_eliminated=True), (3.0, 1.5)
        )

    def test_shot_event_can_update_shooters_frenzy_separately_from_target(self) -> None:
        _, _, player, bot = pvp_login_snapshot(
            1000001, "Local", "local-pvp:1:6:0:0", 1, 6,
            0, 1, 101, 0, 1, 10101, 0,
        )
        result = pvp_shoot_event_result_body(
            bot, player, 1, 0,
            ammo_cfg_id=300,
            target_hp_delta=0,
            source_virtual_hp_delta=-1,
        )
        event = parse_bytes_field(result, 4) or b""
        source = parse_bytes_field(event, 1) or b""
        target = parse_bytes_field(event, 2) or b""
        self.assertEqual(parse_varint_field(source, 14), (1 << 64) - 1)
        self.assertIsNone(parse_varint_field(target, 14))
        self.assertIsNone(parse_varint_field(target, 2))

        result = pvp_shoot_event_result_body(
            bot, player, 1, 0,
            ammo_cfg_id=1,
            target_hp_delta=-1,
            source_virtual_hp_delta=1,
        )
        event = parse_bytes_field(result, 4) or b""
        source = parse_bytes_field(event, 1) or b""
        target = parse_bytes_field(event, 2) or b""
        self.assertEqual(parse_varint_field(source, 14), 1)
        self.assertEqual(parse_varint_field(target, 2), (1 << 64) - 1)

    def test_hp_damage_uses_frenzy_only_after_hp_is_empty(self) -> None:
        hp, frenzy, hp_delta, frenzy_delta = _pvp_apply_hp_damage(1, 2, 1)
        self.assertEqual((hp, frenzy, hp_delta, frenzy_delta), (0, 2, -1, 0))
        self.assertFalse(_pvp_is_eliminated(hp, frenzy))

        hp, frenzy, hp_delta, frenzy_delta = _pvp_apply_hp_damage(hp, frenzy, 1)
        self.assertEqual((hp, frenzy, hp_delta, frenzy_delta), (0, 1, 0, -1))
        self.assertFalse(_pvp_is_eliminated(hp, frenzy))

        hp, frenzy, hp_delta, frenzy_delta = _pvp_apply_hp_damage(hp, frenzy, 1)
        self.assertEqual((hp, frenzy, hp_delta, frenzy_delta), (0, 0, 0, -1))
        self.assertTrue(_pvp_is_eliminated(hp, frenzy))

    def test_shot_event_can_damage_frenzy_without_hp_loss(self) -> None:
        _, _, player, bot = pvp_login_snapshot(
            1000001, "Local", "local-pvp:1:6:0:0", 1, 6,
            0, 1, 101, 0, 1, 10101, 0,
        )
        result = pvp_shoot_event_result_body(
            bot, player, 1, 0,
            target_hp_delta=0,
            target_virtual_hp_delta=-1,
            target_dead=False,
        )
        first_event = parse_bytes_field(result, 4) or b""
        target = parse_bytes_field(first_event, 2) or b""
        self.assertEqual(parse_varint_field(target, 2), None)
        self.assertEqual(parse_varint_field(target, 14), (1 << 64) - 1)
        self.assertEqual(parse_varint_field(target, 49), 1)
        self.assertIsNone(parse_varint_field(target, 68))

    def test_hallucinogen_real_shot_spends_frenzy_before_elimination(self) -> None:
        _, _, player, bot = pvp_login_snapshot(
            1000001, "Local", "local-pvp:1:6:0:0", 1, 6,
            0, 1, 101, 0, 1, 10101, 0,
        )
        player = pvp_gamer_with_state(
            player, hp=0, ammo_number=2, fake_ammo_number=0,
            round_number=1, is_dead=False, virtual_hp=2,
        )
        gamers = [player, bot, bot]
        hit_points = [0, 4, 4]
        virtual_hit_points = [2, 0, 0]
        real_ammo = [2, 2, 2]
        fake_ammo = [0, 1, 1]
        self_shots = [0, 0, 0]

        with patch("server.random.randrange", return_value=0):
            resolved = _resolve_hallucinogen_self_shot(
                gamers, hit_points, virtual_hit_points, real_ammo,
                fake_ammo, self_shots, 0, round_number=1, event_id=1,
                event_time=1,
            )
        self.assertIsNotNone(resolved)
        _, ammo_cfg_id, match_ended, shot_result = resolved
        self.assertEqual(ammo_cfg_id, 1)
        self.assertFalse(match_ended)
        self.assertEqual((hit_points[0], virtual_hit_points[0]), (0, 1))
        self.assertFalse(_pvp_is_eliminated(hit_points[0], virtual_hit_points[0]))
        event = parse_bytes_field(shot_result, 4) or b""
        target = parse_bytes_field(event, 2) or b""
        self.assertEqual(parse_varint_field(target, 14), (1 << 64) - 1)
        self.assertIsNone(parse_varint_field(target, 68))

        with patch("server.random.randrange", return_value=0):
            resolved = _resolve_hallucinogen_self_shot(
                gamers, hit_points, virtual_hit_points, real_ammo,
                fake_ammo, self_shots, 0, round_number=1, event_id=2,
                event_time=2,
            )
        self.assertIsNotNone(resolved)
        self.assertEqual((hit_points[0], virtual_hit_points[0]), (0, 0))
        self.assertTrue(_pvp_is_eliminated(hit_points[0], virtual_hit_points[0]))
        self.assertIsNone(_resolve_hallucinogen_self_shot(
            gamers, hit_points, virtual_hit_points, real_ammo,
            fake_ammo, self_shots, 0, round_number=1, event_id=3,
            event_time=3,
        ))

    def test_hallucinogen_reloads_when_last_real_round_is_spent(self) -> None:
        _, _, player, bot = pvp_login_snapshot(
            1000001, "Local", "local-pvp:1:6:0:0", 1, 6,
            0, 1, 101, 0, 1, 10101, 0,
        )
        gamers = [player, bot, bot]
        hit_points = [4, 4, 4]
        virtual_hit_points = [0, 0, 0]
        # This reproduces the reported HUD: the bot has one live round plus
        # blanks. Hallucinogen forces the live round, leaving blanks behind.
        real_ammo = [2, 1, 2]
        fake_ammo = [1, 2, 1]
        self_shots = [0, 0, 0]

        with patch("server.random.randrange", return_value=2):
            resolved = _resolve_hallucinogen_self_shot(
                gamers, hit_points, virtual_hit_points, real_ammo,
                fake_ammo, self_shots, 1, round_number=1, event_id=8,
                event_time=100, enhanced_ammo=[0, 0, 0],
            )

        self.assertIsNotNone(resolved)
        updated_bot, ammo_cfg_id, match_ended, shot_result = resolved
        self.assertEqual(ammo_cfg_id, 1)
        self.assertFalse(match_ended)
        self.assertEqual((real_ammo[1], fake_ammo[1]), (1, 2))
        bot_gun = parse_bytes_field(updated_bot, 7) or b""
        self.assertEqual(
            {parse_varint_field(ammo, 1): parse_varint_field(ammo, 2) for ammo in parse_bytes_fields(bot_gun, 2)},
            {300: 2, 1: 1, 2: 1},
        )

        events = parse_bytes_fields(shot_result, 4)
        self.assertEqual(len(events), 3)  # shot, Enum_Reload, final source
        shot_source = parse_bytes_field(events[0], 1) or b""
        self.assertEqual(parse_varint_field(shot_source, 9), 2)
        self.assertEqual(
            [parse_varint_field(ammo, 2) for ammo in parse_bytes_fields(shot_source, 5)],
            [2, 0],
        )
        reload_target = parse_bytes_field(events[1], 2) or b""
        self.assertEqual(parse_varint_field(reload_target, 8), 1)
        self.assertEqual(parse_varint_field(reload_target, 9), 1)
        self.assertEqual(
            [parse_varint_field(ammo, 2) for ammo in parse_bytes_fields(reload_target, 5)],
            [2, 1, 1],
        )

    def test_hallucinogen_reloads_an_all_fake_magazine(self) -> None:
        _, _, player, bot = pvp_login_snapshot(
            1000001, "Local", "local-pvp:1:6:0:0", 1, 6,
            0, 1, 101, 0, 1, 10101, 0,
        )
        gamers = [player, bot, bot]
        hit_points = [4, 4, 4]
        virtual_hit_points = [0, 0, 0]
        real_ammo = [2, 0, 2]
        fake_ammo = [1, 2, 1]
        self_shots = [0, 0, 0]

        with patch("server.random.randrange", return_value=0):
            resolved = _resolve_hallucinogen_self_shot(
                gamers, hit_points, virtual_hit_points, real_ammo,
                fake_ammo, self_shots, 1, round_number=1, event_id=9,
                event_time=200, enhanced_ammo=[0, 0, 0],
            )

        self.assertIsNotNone(resolved)
        _, ammo_cfg_id, match_ended, shot_result = resolved
        self.assertEqual(ammo_cfg_id, 300)
        self.assertFalse(match_ended)
        self.assertEqual((real_ammo[1], fake_ammo[1]), (1, 2))
        events = parse_bytes_fields(shot_result, 4)
        self.assertEqual(parse_varint_field(
            parse_bytes_field(events[1], 2) or b"", 8
        ), 1)

    def test_hero_skill_identity_and_charge_round_trip(self) -> None:
        for hero_id, (skill_id, initial_cd, reset_cd) in LAB_HERO_SKILLS.items():
            _, _, player, _ = pvp_login_snapshot(
                1000001, "Local", "local-pvp:1:6:0:0", 1, 6,
                hero_id, hero_id + 1, 101, 0, 1, 10101, 0,
            )
            self.assertEqual(pvp_gamer_skill_id(player), skill_id)
            self.assertEqual(pvp_gamer_skill_cd(player), initial_cd)
            charged = pvp_gamer_with_skill_cd(player, initial_cd - 1)
            self.assertEqual(pvp_gamer_skill_cd(charged), initial_cd - 1)
            self.assertEqual(pvp_gamer_skill_id(charged), skill_id)
            self.assertIn(reset_cd, (2, 3))
            self.assertEqual(
                parse_bytes_field(charged, 7), parse_bytes_field(player, 7)
            )

    def test_rabbit_skill_event_contains_roll_hp_and_cooldown(self) -> None:
        _, _, player, bot = pvp_login_snapshot(
            1000001, "Local", "local-pvp:1:6:0:0", 1, 6,
            0, 1, 101, 0, 1, 10101, 0,
        )
        result = pvp_hero_skill_event_result_body(
            pvp_gamer_with_skill_cd(player, 3), bot,
            skill_id=10000, target_index=1, skill_cd=3,
            event_id=7, hp_delta=-1, luck_roll=4,
        )
        self.assertEqual(parse_varint_field(result, 1), 3)
        self.assertEqual(parse_varint_field(result, 2), 10000)
        self.assertEqual(parse_varint_field(result, 10), 1)
        events = parse_bytes_fields(result, 4)
        self.assertEqual(len(events), 3)
        cd = parse_bytes_field(events[0], 2) or b""
        self.assertEqual(parse_varint_field(cd, 9), 9)
        self.assertEqual(parse_varint_field(cd, 21), 3)
        luck = parse_bytes_field(events[1], 2) or b""
        self.assertEqual(parse_varint_field(luck, 9), 7)
        hp = parse_bytes_field(events[2], 2) or b""
        self.assertEqual(parse_varint_field(hp, 9), 19)
        self.assertEqual(parse_varint_field(hp, 2), -1 & ((1 << 64) - 1))

    def test_bear_skill_event_converts_frenzy_to_hp(self) -> None:
        _, _, player, _ = pvp_login_snapshot(
            1000001, "Local", "local-pvp:1:6:1:0", 1, 6,
            1, 2, 201, 1, 2, 10201, 0,
        )
        result = pvp_hero_skill_event_result_body(
            player, player, skill_id=10001, target_index=0,
            skill_cd=3, event_id=8, hp_delta=2,
            virtual_hp_delta=-2,
        )
        self.assertEqual(parse_varint_field(result, 1), 3)
        effect = parse_bytes_field(parse_bytes_fields(result, 4)[1], 2) or b""
        self.assertEqual(parse_varint_field(effect, 9), 14)
        self.assertEqual(parse_varint_field(effect, 2), 2)
        self.assertEqual(parse_varint_field(effect, 14), -2 & ((1 << 64) - 1))

    def test_gun_capacity_and_bounded_random_reload(self) -> None:
        self.assertEqual(pvp_gun_ammo_counts(0), (3, 3))
        self.assertEqual(pvp_gun_ammo_counts(1), (2, 2))
        self.assertEqual(pvp_gun_ammo_counts(6), (3, 4))
        with patch("protocol.random.randint", return_value=1) as pick:
            self.assertEqual(pvp_gun_ammo_counts(0, randomize=True), (1, 5))
            self.assertEqual(pvp_gun_ammo_counts(1, randomize=True), (1, 3))
        self.assertEqual(pick.call_args_list[0].args, (1, 3))
        self.assertEqual(pick.call_args_list[1].args, (1, 2))

    def test_last_real_shot_carries_reload_after_shoot_animation(self) -> None:
        _, _, player, bot = pvp_login_snapshot(
            1000001, "Local", "local-pvp:1:6:0:0", 1, 6,
            0, 1, 101, 0, 1, 10101, 0,
        )
        player = pvp_gamer_with_state(player, hp=4, ammo_number=2,
            fake_ammo_number=2, round_number=1, weapon_reloaded=True)
        result = pvp_shoot_event_result_body(
            player, bot, 0, 1, ammo_cfg_id=1,
            source_ammo_after=0, source_fake_ammo_after=3,
            reload_ammo_after=(2, 2), event_time=100,
        )
        events = parse_bytes_fields(result, 4)
        self.assertEqual(len(events), 4)
        shot = parse_bytes_field(events[0], 1) or b""
        self.assertEqual(parse_varint_field(shot, 9), 2)
        self.assertEqual(
            [parse_varint_field(a, 2) for a in parse_bytes_fields(shot, 5)],
            [3, 0],
        )
        reload_source = parse_bytes_field(events[1], 1) or b""
        reload_target = parse_bytes_field(events[1], 2) or b""
        self.assertEqual(parse_varint_field(reload_source, 9), 1)
        self.assertEqual(parse_varint_field(reload_target, 8), 1)
        self.assertEqual(
            [parse_varint_field(a, 2) for a in parse_bytes_fields(reload_target, 5)],
            [2, 2],
        )
        buff_target = parse_bytes_field(events[2], 2) or b""
        self.assertEqual(parse_varint_field(buff_target, 9), 10)
        self.assertEqual(parse_varint_field(buff_target, 28), parse_varint_field(reload_target, 28))
        self.assertEqual(parse_varint_field(parse_bytes_field(buff_target, 25) or b"", 1), 600)
        final = parse_bytes_field(events[3], 1) or b""
        self.assertEqual(parse_varint_field(final, 9), 3)
        self.assertGreaterEqual(parse_varint_field(final, 28) or 0, 101)

    def test_randomized_trio_login_keeps_server_magazines_within_each_gun(self) -> None:
        with patch("protocol.random.randint", return_value=1):
            _, info, _, _ = pvp_login_snapshot(
                1234, "Local Hunter", "local-pvp:1:6:0:0", 1, 6,
                0, 1, 101, 0, 1, 10101,
                randomize_ammo=True,
            )
        gamers = parse_bytes_fields(info, 2)
        self.assertEqual(len(gamers), 3)
        for gamer, expected in zip(gamers, ((1, 5), (1, 3), (1, 5))):
            gun = parse_bytes_field(gamer, 7) or b""
            stacks = {
                parse_varint_field(ammo, 1): parse_varint_field(ammo, 2)
                for ammo in parse_bytes_fields(gun, 2)
            }
            self.assertEqual((stacks[1] + stacks.get(2, 0), stacks[300]), expected)

    def test_bundled_special_ammo_sort_order(self) -> None:
        # fight_dbconfig.ab identifies the enhanced and healing rounds as
        # cfg 2/301, between blank cfg 300 and real cfg 1 in the HUD order.
        self.assertEqual(_ammo_sort_id(300), 1)
        self.assertEqual(_ammo_sort_id(301), 2)
        self.assertEqual(_ammo_sort_id(1), 3)
        self.assertEqual(_ammo_sort_id(2), 4)

    def test_enhanced_ammo_stack_can_be_added_and_removed(self) -> None:
        gamer = pb_message(
            pb_varint(4, 4),
            pb_bytes(
                7,
                pb_message(
                    pb_bytes(2, pb_message(
                        pb_varint(1, 1), pb_varint(2, 1), pb_varint(3, 3),
                    )),
                    pb_bytes(2, pb_message(
                        pb_varint(1, 300), pb_varint(2, 2), pb_varint(3, 1),
                    )),
                ),
            ),
        )
        with_enhanced = pvp_gamer_with_state(
            gamer,
            hp=4,
            ammo_number=1,
            fake_ammo_number=2,
            enhanced_ammo_number=1,
            round_number=1,
        )
        gun = parse_bytes_field(with_enhanced, 7) or b""
        stacks = parse_bytes_fields(gun, 2)
        self.assertIn(
            (2, 1),
            [(parse_varint_field(stack, 1), parse_varint_field(stack, 2))
             for stack in stacks],
        )
        without_enhanced = pvp_gamer_with_state(
            with_enhanced,
            hp=4,
            ammo_number=1,
            fake_ammo_number=2,
            enhanced_ammo_number=0,
            round_number=1,
        )
        gun = parse_bytes_field(without_enhanced, 7) or b""
        self.assertNotIn(
            2,
            [parse_varint_field(stack, 1) for stack in parse_bytes_fields(gun, 2)],
        )

    def test_burst_mode_uses_the_real_buff_cfg_in_player_snapshot(self) -> None:
        stale_card_id = pb_message(pb_varint(1, 2016))
        burst_buff = pb_message(pb_varint(1, BURST_MODE_BUFF_CFG_ID))
        other_buff = pb_message(pb_varint(1, 3001))
        gamer = pb_message(
            pb_bytes(8, stale_card_id),
            pb_bytes(8, burst_buff),
            pb_bytes(8, burst_buff),
            pb_bytes(8, other_buff),
        )

        active = pvp_gamer_with_state(
            gamer,
            hp=4,
            ammo_number=4,
            round_number=1,
            burst_mode_active=True,
        )
        active_cfgs = [
            parse_varint_field(buff, 1) for buff in parse_bytes_fields(active, 8)
        ]
        self.assertEqual(active_cfgs, [BURST_MODE_BUFF_CFG_ID, 3001])
        self.assertIsNone(parse_bytes_field(active, 19))

        inactive = pvp_gamer_with_state(
            active,
            hp=4,
            ammo_number=4,
            round_number=1,
            burst_mode_active=False,
        )
        inactive_cfgs = [
            parse_varint_field(buff, 1) for buff in parse_bytes_fields(inactive, 8)
        ]
        self.assertEqual(inactive_cfgs, [3001])

    def test_burst_mode_card_events_add_and_remove_the_buff_cfg(self) -> None:
        player = pb_message(pb_varint(1, 0))
        bot = pb_message(pb_varint(1, 1))
        card = pvp_shop_card(1, 2016, 300)
        card_result = pvp_generic_card_event_result_body(
            player,
            bot,
            card,
            skill_id=1015,
            target_index=1,
            event_id=10,
            add_buff_cfg=BURST_MODE_BUFF_CFG_ID,
        )
        card_events = parse_bytes_fields(card_result, 4)
        target_outline = parse_bytes_field(card_events[-1], 2) or b""
        added = parse_bytes_fields(target_outline, 25)
        self.assertEqual(len(added), 1)
        self.assertEqual(
            parse_varint_field(added[0], 1), BURST_MODE_BUFF_CFG_ID
        )

        shot_result = pvp_shoot_event_result_body(
            player,
            bot,
            0,
            1,
            additional_shots=((300, 0, 3, 1, False),),
            del_buff_cfg=BURST_MODE_BUFF_CFG_ID,
        )
        shot_events = parse_bytes_fields(shot_result, 4)
        self.assertEqual(len(shot_events), 3)
        self.assertEqual(parse_bytes_fields(
            parse_bytes_field(shot_events[0], 1) or b"", 24
        ), [])
        final_outline = parse_bytes_field(shot_events[-1], 1) or b""
        removed = parse_bytes_fields(final_outline, 24)
        self.assertEqual(len(removed), 1)
        self.assertEqual(
            parse_varint_field(removed[0], 1), BURST_MODE_BUFF_CFG_ID
        )

    def test_wanted_card_adds_the_hidden_parent_and_visible_reward_buff(self) -> None:
        player = pb_message(pb_varint(1, 0))
        bot = pb_message(pb_varint(1, 1))
        card = pvp_shop_card(1, 2021, 200)
        result = pvp_generic_card_event_result_body(
            player,
            bot,
            card,
            skill_id=1020,
            target_index=1,
            event_id=45,
            event_type=10,
            clear_slot=False,
            add_buff_cfgs=(
                WANTED_PARENT_BUFF_CFG_ID,
                WANTED_REWARD_BUFF_CFG_ID,
            ),
        )
        events = parse_bytes_fields(result, 4)
        target_outline = parse_bytes_field(events[-1], 2) or b""
        added = parse_bytes_fields(target_outline, 25)
        self.assertEqual(
            [parse_varint_field(buff, 1) for buff in added],
            [WANTED_PARENT_BUFF_CFG_ID, WANTED_REWARD_BUFF_CFG_ID],
        )
        self.assertEqual(
            [parse_varint_field(buff, 3) for buff in added],
            [
                1_000_000 + WANTED_PARENT_BUFF_CFG_ID,
                1_000_000 + WANTED_REWARD_BUFF_CFG_ID,
            ],
        )

    def test_wanted_shot_credits_shooter_and_removes_target_marker(self) -> None:
        player = pb_message(pb_varint(1, 0))
        bot = pb_message(pb_varint(1, 1))
        result = pvp_shoot_event_result_body(
            player,
            bot,
            0,
            1,
            ammo_cfg_id=1,
            target_hp_delta=-1,
            source_coin_delta=WANTED_REWARD_R_CHIPS,
            coin_reason=7,
            target_del_buff_cfgs=(
                WANTED_PARENT_BUFF_CFG_ID,
                WANTED_REWARD_BUFF_CFG_ID,
            ),
        )
        event = parse_bytes_field(result, 4) or b""
        source_outline = parse_bytes_field(event, 1) or b""
        target_outline = parse_bytes_field(event, 2) or b""
        coin_change = parse_bytes_field(source_outline, 4) or b""
        self.assertEqual(parse_varint_field(coin_change, 1), WANTED_REWARD_R_CHIPS)
        self.assertEqual(parse_varint_field(coin_change, 2), 7)
        removed = parse_bytes_fields(target_outline, 24)
        self.assertEqual(
            [parse_varint_field(buff, 1) for buff in removed],
            [WANTED_PARENT_BUFF_CFG_ID, WANTED_REWARD_BUFF_CFG_ID],
        )
        self.assertEqual(
            [parse_varint_field(buff, 3) for buff in removed],
            [
                1_000_000 + WANTED_PARENT_BUFF_CFG_ID,
                1_000_000 + WANTED_REWARD_BUFF_CFG_ID,
            ],
        )

    def test_wanted_expiry_credits_marked_player_and_clears_buffs(self) -> None:
        gamer = pb_message(pb_varint(1, 0))
        result = pvp_wanted_expiry_event_result_body(
            gamer,
            target_index=0,
            event_id=46,
        )
        self.assertEqual(parse_varint_field(result, 1), 17)
        events = parse_bytes_fields(result, 4)
        self.assertEqual(len(events), 1)
        coin_outline = parse_bytes_field(events[0], 2) or b""
        # ShowUIChange ignores Enum_Coin (4). Apply the payout on the very
        # same Enum_Buff_Update outline so passive handling credits it once.
        self.assertEqual(parse_varint_field(coin_outline, 9), 10)
        coin_change = parse_bytes_field(coin_outline, 4) or b""
        self.assertEqual(parse_varint_field(coin_change, 1), WANTED_REWARD_R_CHIPS)
        self.assertEqual(parse_varint_field(coin_change, 2), 7)
        buff_outline = coin_outline
        removed = parse_bytes_fields(buff_outline, 24)
        self.assertEqual(
            [parse_varint_field(buff, 1) for buff in removed],
            [WANTED_PARENT_BUFF_CFG_ID, WANTED_REWARD_BUFF_CFG_ID],
        )

    def test_wanted_buff_snapshot_helper_adds_once_and_removes_both_ids(self) -> None:
        unrelated = pb_message(pb_varint(1, 3001))
        gamer = pb_message(pb_bytes(8, unrelated))
        active = pvp_gamer_with_buffs(
            gamer,
            add_cfg_ids=(WANTED_PARENT_BUFF_CFG_ID, WANTED_REWARD_BUFF_CFG_ID),
        )
        active_wanted = {
            parse_varint_field(buff, 1): parse_varint_field(buff, 3)
            for buff in parse_bytes_fields(active, 8)
        }
        self.assertEqual(
            active_wanted[WANTED_PARENT_BUFF_CFG_ID],
            1_000_000 + WANTED_PARENT_BUFF_CFG_ID,
        )
        self.assertEqual(
            active_wanted[WANTED_REWARD_BUFF_CFG_ID],
            1_000_000 + WANTED_REWARD_BUFF_CFG_ID,
        )
        repeated = pvp_gamer_with_buffs(
            active,
            add_cfg_ids=(WANTED_PARENT_BUFF_CFG_ID, WANTED_REWARD_BUFF_CFG_ID),
        )
        self.assertEqual(
            [parse_varint_field(buff, 1) for buff in parse_bytes_fields(repeated, 8)],
            [3001, WANTED_PARENT_BUFF_CFG_ID, WANTED_REWARD_BUFF_CFG_ID],
        )
        cleared = pvp_gamer_with_buffs(
            repeated,
            del_cfg_ids=(WANTED_PARENT_BUFF_CFG_ID, WANTED_REWARD_BUFF_CFG_ID),
        )
        self.assertEqual(
            [parse_varint_field(buff, 1) for buff in parse_bytes_fields(cleared, 8)],
            [3001],
        )

    def test_maintenance_kit_buff_is_added_and_removed_in_player_snapshot(self) -> None:
        stale_card_buff = pb_message(pb_varint(1, 2015))
        maintenance_buff = pb_message(
            pb_varint(1, MAINTENANCE_KIT_BUFF_CFG_ID)
        )
        unrelated_buff = pb_message(pb_varint(1, 3001))
        gamer = pb_message(
            pb_bytes(8, stale_card_buff),
            pb_bytes(8, maintenance_buff),
            pb_bytes(8, maintenance_buff),
            pb_bytes(8, unrelated_buff),
        )

        active = pvp_gamer_with_state(
            gamer,
            hp=4,
            ammo_number=4,
            round_number=1,
            maintenance_kit_active=True,
        )
        active_cfgs = [
            parse_varint_field(buff, 1) for buff in parse_bytes_fields(active, 8)
        ]
        self.assertEqual(active_cfgs, [MAINTENANCE_KIT_BUFF_CFG_ID, 3001])

        inactive = pvp_gamer_with_state(
            active,
            hp=4,
            ammo_number=4,
            round_number=1,
            maintenance_kit_active=False,
        )
        inactive_cfgs = [
            parse_varint_field(buff, 1) for buff in parse_bytes_fields(inactive, 8)
        ]
        self.assertEqual(inactive_cfgs, [3001])

    def test_maintenance_kit_keeps_normal_shot_effect_and_damage_packet(self) -> None:
        player = pb_message(pb_varint(1, 0))
        bot = pb_message(pb_varint(1, 1))
        card = pvp_shop_card(1, 2015, 300)
        use_result = pvp_generic_card_event_result_body(
            player,
            bot,
            card,
            skill_id=1014,
            target_index=0,
            event_id=22,
            add_buff_cfg=MAINTENANCE_KIT_BUFF_CFG_ID,
        )
        use_events = parse_bytes_fields(use_result, 4)
        use_target = parse_bytes_field(use_events[-1], 2) or b""
        added = parse_bytes_fields(use_target, 25)
        self.assertEqual(
            [parse_varint_field(buff, 1) for buff in added],
            [MAINTENANCE_KIT_BUFF_CFG_ID],
        )

        shot_result = pvp_shoot_event_result_body(
            player,
            bot,
            0,
            1,
            ammo_cfg_id=1,
            target_hp_delta=-2,
            source_ammo_after=3,
            source_fake_ammo_after=2,
            del_buff_cfgs=(MAINTENANCE_KIT_BUFF_CFG_ID,),
        )
        shot_events = parse_bytes_fields(shot_result, 4)
        source_outline = parse_bytes_field(shot_events[0], 1) or b""
        target_outline = parse_bytes_field(shot_events[0], 2) or b""
        fired_round = parse_bytes_field(source_outline, 10) or b""
        self.assertEqual(parse_varint_field(fired_round, 1), 1)
        self.assertEqual(
            parse_varint_field(target_outline, 2), (1 << 64) - 2
        )
        post_shot_ammo = [
            (parse_varint_field(ammo, 1), parse_varint_field(ammo, 2))
            for ammo in parse_bytes_fields(source_outline, 5)
        ]
        self.assertIn((1, 3), post_shot_ammo)
        self.assertEqual(parse_varint_field(target_outline, 49), 1)
        self.assertEqual(parse_varint_field(target_outline, 73), 2)

        final_outline = parse_bytes_field(shot_events[-1], 1) or b""
        removed = parse_bytes_fields(final_outline, 24)
        self.assertEqual(
            [parse_varint_field(buff, 1) for buff in removed],
            [MAINTENANCE_KIT_BUFF_CFG_ID],
        )

    def test_maintenance_bonus_adds_damage_to_normal_self_and_opponent_shots(self) -> None:
        self.assertEqual(
            _pvp_shot_damage(
                1, maintenance_kit_active=True,
                shooter_index=0, target_index=1,
            ),
            2,
        )
        self.assertEqual(
            _pvp_shot_damage(
                1, maintenance_kit_active=True,
                shooter_index=0, target_index=0,
            ),
            2,
        )
        self.assertEqual(
            _pvp_shot_damage(
                300, maintenance_kit_active=True,
                shooter_index=0, target_index=1,
            ),
            0,
        )
        self.assertEqual(
            _pvp_shot_damage(
                2, enhanced_ammo_bonus=1, maintenance_kit_active=True,
                shooter_index=0, target_index=1,
            ),
            2,
        )
        self.assertTrue(_maintenance_kit_expires_after_shot(
            True, 0, 1, [(300, 0, 3, 1, False)],
        ))
        self.assertFalse(_maintenance_kit_expires_after_shot(
            True, 0, 0, [(300, 0, 3, 1, False)],
        ))
        self.assertTrue(_maintenance_kit_expires_after_shot(
            True, 0, 0, [(1, -1, 3, 1, False)],
        ))

    def test_spare_magazine_packet_has_reload_and_replacement_pairs(self) -> None:
        player = pb_message(pb_varint(1, 1))
        card = pvp_shop_card(50, 2007, 300)
        result = pvp_spare_magazine_event_result_body(
            player,
            player,
            card,
            target_index=0,
            old_real=2,
            old_fake=1,
            real_after=4,
            fake_after=2,
            event_id=77,
            coin_delta=-300,
        )
        self.assertEqual(parse_varint_field(result, 1), 7)
        self.assertEqual(parse_varint_field(result, 2), 1006)
        events = parse_bytes_fields(result, 4)
        self.assertEqual(len(events), 2)
        reload_source = parse_bytes_field(events[1], 1) or b""
        reload_target = parse_bytes_field(events[1], 2) or b""
        self.assertEqual(parse_varint_field(reload_source, 9), 12)
        self.assertEqual(parse_varint_field(reload_target, 9), 12)
        self.assertEqual(parse_varint_field(reload_target, 8), 1)
        self.assertEqual(
            [(parse_varint_field(ammo, 1), parse_varint_field(ammo, 2))
             for ammo in parse_bytes_fields(reload_target, 5)],
            [(300, 2), (1, 4)],
        )
        pairs = parse_bytes_fields(reload_target, 11)
        self.assertEqual(len(pairs), 2)
        self.assertEqual(
            [(parse_varint_field(parse_bytes_field(pair, 1) or b"", 1),
              parse_varint_field(parse_bytes_field(pair, 2) or b"", 1))
             for pair in pairs],
            [(300, 300), (1, 1)],
        )

    def test_random_shop_selection_has_four_distinct_client_cfgs(self) -> None:
        with patch("server.random.sample", return_value=[
            (2011, 200), (2004, 100), (2001, 100), (2008, 200),
        ]):
            self.assertEqual(
                _random_shop_specs(),
                ((2011, 200), (2004, 100), (2001, 100), (2008, 200)),
            )

    def test_sold_shop_slot_is_replaced_at_next_turn(self) -> None:
        original = (
            pvp_shop_card(1, 2001, 100, status=2),
            pvp_shop_card(2, 2003, 200),
            pvp_shop_card(3, 2004, 100),
            pvp_shop_card(4, 2008, 200),
        )
        # The lab pool now also contains contract-compatible item variants;
        # pin the replacement choice so this regression stays deterministic.
        with patch("server.random.choice", return_value=(2011, 200)):
            cards, next_id = _replenish_sold_shop_cards(original, 5, turn=2)
        self.assertEqual(next_id, 6)
        self.assertEqual([parse_varint_field(c, 2) for c in cards],
                         [2011, 2003, 2004, 2008])
        self.assertEqual(parse_varint_field(cards[0], 1), 5)
        self.assertEqual(parse_varint_field(cards[0], 3), 200)
        self.assertEqual(parse_varint_field(cards[0], 4), 2)
        self.assertEqual(parse_varint_field(cards[0], 5), 1)
        self.assertEqual(cards[1:], original[1:])

    def test_wet_cigarette_packet_has_luck_and_heal_delta(self) -> None:
        player = pb_message(pb_varint(1, 1))
        card = pvp_shop_card(50, 2011, 100)
        result = pvp_wet_cigarette_event_result_body(
            player, card, die_roll=4, heal_delta=1, event_id=77,
            coin_delta=-100,
        )
        self.assertEqual(parse_varint_field(result, 1), 7)
        self.assertEqual(parse_varint_field(result, 2), 1010)
        events = parse_bytes_fields(result, 4)
        self.assertEqual(len(events), 3)
        luck_source = parse_bytes_field(events[1], 1) or b""
        luck_target = parse_bytes_field(events[1], 2) or b""
        self.assertEqual(parse_varint_field(luck_source, 9), 7)
        self.assertEqual(parse_varint_field(luck_target, 9), 7)
        luck = parse_bytes_field(luck_target, 22) or b""
        self.assertEqual(parse_varint_field(luck, 1), 4)
        self.assertEqual(parse_varint_field(luck, 3), 1)
        heal_target = parse_bytes_field(events[2], 2) or b""
        self.assertEqual(parse_varint_field(heal_target, 9), 20)
        self.assertEqual(parse_varint_field(heal_target, 2), 1)

    def test_wet_cigarette_is_useless_at_zero_hp_even_with_frenzy(self) -> None:
        self.assertFalse(_pvp_is_eliminated(0, 1))
        self.assertEqual(_pvp_wet_cigarette_heal(0, 1, 5), 0)
        self.assertEqual(_pvp_wet_cigarette_heal(0, 1, 3), 0)
        self.assertEqual(_pvp_wet_cigarette_heal(0, 0, 5), 0)
        self.assertEqual(_pvp_wet_cigarette_heal(1, 1, 5), 1)
        self.assertEqual(_pvp_wet_cigarette_heal(4, 1, 6), 0)

    def test_fake_shot_that_zeros_shooters_frenzy_animates_the_shooter(self) -> None:
        _, _, player, bot = pvp_login_snapshot(
            1000001, "Local", "local-pvp:test", 1, 6,
            0, 1, 101, 0, 1, 10101, 0,
        )
        result = pvp_shoot_event_result_body(
            player, bot, 0, 1,
            ammo_cfg_id=300,
            target_hp_delta=0,
            source_virtual_hp_delta=-1,
            source_dead_after_shots=(True,),
        )
        events = parse_bytes_fields(result, 4)
        self.assertEqual(len(events), 3)  # shot, death animation, final source
        death_event = events[1]
        source = parse_bytes_field(death_event, 1) or b""
        target = parse_bytes_field(death_event, 2) or b""
        self.assertEqual(
            parse_varint_field(source, 1),
            parse_varint_field(target, 1),
        )
        self.assertEqual(parse_varint_field(source, 1), 0)
        self.assertEqual(parse_varint_field(source, 9), PVP_UPDATE_GAMER_DEAD_STATUS_EVENT)
        self.assertEqual(parse_varint_field(target, 9), PVP_UPDATE_GAMER_DEAD_STATUS_EVENT)

        target_eliminated_without_shooter_death = pvp_shoot_event_result_body(
            player, bot, 0, 1,
            ammo_cfg_id=300,
            target_hp_delta=0,
            target_dead=True,
        )
        self.assertEqual(
            len(parse_bytes_fields(target_eliminated_without_shooter_death, 4)),
            2,
        )

    def test_shot_result_puts_animation_status_on_outer_gamer_snapshots(self) -> None:
        _, _, player, bot = pvp_login_snapshot(
            1000001, "Local", "local-pvp:test", 1, 6,
            0, 1, 101, 0, 1, 10101, 0,
        )
        result = pvp_shoot_event_result_body(
            player, bot, 0, 1,
            ammo_cfg_id=1,
            target_hp_delta=-1,
            target_dead=True,
            source_event_status=2,
            target_event_status=4,
        )
        source = parse_bytes_field(result, 12) or b""
        target = parse_bytes_field(result, 11) or b""
        self.assertEqual(parse_varint_field(source, 26), 2)
        self.assertEqual(parse_varint_field(target, 26), 4)
        shot_event = parse_bytes_field(result, 4) or b""
        source_outline = parse_bytes_field(shot_event, 1) or b""
        target_outline = parse_bytes_field(shot_event, 2) or b""
        self.assertEqual(parse_varint_field(source_outline, 63), 2)
        self.assertEqual(parse_varint_field(target_outline, 63), 4)

        normal_result = pvp_shoot_event_result_body(
            pvp_gamer_with_event_status(player, 2), bot, 0, 1,
            ammo_cfg_id=300,
            target_hp_delta=0,
        )
        normal_source = parse_bytes_field(normal_result, 12) or b""
        self.assertIsNone(parse_varint_field(normal_source, 26))

    def setUp(self) -> None:
        # Integration tests should not spend the bundled client's full 11s
        # opening animation on every synthetic local match.
        self._opening_delay_patcher = patch(
            "server.PVP_OPENING_SEQUENCE_DELAY", 0.001
        )
        self._opening_delay_patcher.start()
        self.addCleanup(self._opening_delay_patcher.stop)
        # Stable synthetic matches; live matches use random.sample without
        # this patch. Separate tests override it to exercise varying stock.
        self._shop_sample_patcher = patch(
            "server.random.sample", side_effect=lambda seq, count: list(seq)[:count]
        )
        self._shop_sample_patcher.start()
        self.addCleanup(self._shop_sample_patcher.stop)

    def _state(self, inventory: dict) -> GameState:
        """Build an isolated GameState without touching the live inventory."""
        state = GameState.__new__(GameState)
        state._lock = threading.Lock()
        state.randomize_magazines = False
        state.inventory = inventory
        state._clock_epoch = season_state(inventory)["serverTime"]
        state._clock_monotonic = time.monotonic()
        handle = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        handle.close()
        state.inventory_path = Path(handle.name)
        self.addCleanup(lambda: state.inventory_path.unlink(missing_ok=True))
        return state

    def test_trace_record_preserves_header_and_raw_frame(self) -> None:
        frame = encode_frame(255, 2, b"abc", index=9, flags=64, length_mode="body")
        record = frame_record(
            "pvp",
            "S->C",
            frame,
            "body",
            "post",
            {"round": 1, "turn": 0},
        )
        self.assertEqual(record["raw_hex"], frame.hex())
        self.assertEqual(record["body_bytes"], 3)
        self.assertTrue(record["length_consistent"])
        self.assertEqual(record["header"]["cmd"], 255)
        self.assertEqual(record["header"]["act"], 2)
        self.assertEqual(record["header"]["index"], 9)
        self.assertEqual(record["header"]["flags"], 64)

    def test_varint_round_trip(self) -> None:
        for value in (0, 1, 127, 128, 16384, 2**32 - 1):
            encoded = encode_varint(value)
            decoded, offset = decode_varint(encoded)
            self.assertEqual(decoded, value)
            self.assertEqual(offset, len(encoded))


    def test_frame_header_total_length(self) -> None:
        frame = encode_frame(1, 1, b"abc", index=7, length_mode="total")
        head = decode_header(frame[:HEADER_SIZE])
        self.assertEqual(head.length, HEADER_SIZE + 3)
        self.assertEqual((head.cmd, head.act, head.index), (1, 1, 7))
        self.assertEqual(frame[HEADER_SIZE:], b"abc")


    def test_frame_header_body_length(self) -> None:
        frame = encode_frame(3, 2, b"abc", length_mode="body")
        head = decode_header(frame[:HEADER_SIZE])
        self.assertEqual(head.length, 3)


    def test_request_gid_and_login_payload(self) -> None:
        request = pb_varint(1, 1234)
        self.assertEqual(parse_varint_field(request, 1), 1234)
        response = response_body(1, 1, 1234, "local-session-test", 38002)
        self.assertTrue(response)

    def test_local_pvp_room_snapshot(self) -> None:
        session = b"local-pvp:21:41:0:0"
        request = pb_message(pb_varint(1, 1234), pb_bytes(2, session))
        self.assertEqual(parse_bytes_field(request, 2), session)
        login = pvp_login_body(
            1234, "Local Hunter", session.decode(), 21, 41,
            0, 36, 105, 0, 24, 10103,
        )
        pvp = parse_bytes_field(login, 2)
        self.assertIsNotNone(pvp)
        self.assertEqual(parse_varint_field(pvp or b"", 6), 1)
        self.assertEqual(parse_varint_field(pvp or b"", 21), 4)
        self.assertIsNone(parse_bytes_field(pvp or b"", 11))
        for gamer in parse_bytes_fields(pvp or b"", 2):
            self.assertEqual(parse_varint_field(gamer, 4), 4)
            self.assertEqual(parse_varint_field(gamer, 10), 2)
            # PvpGamerState=1 is a grave mound; items cannot select it.
            self.assertEqual(parse_varint_field(gamer, 27), 0)
        hero = parse_bytes_field(parse_bytes_fields(pvp or b"", 2)[0], 9)
        self.assertEqual(parse_varint_field(hero or b"", 1), 0)
        self.assertEqual(parse_varint_field(hero or b"", 2), 10000)
        self.assertEqual(parse_varint_field(hero or b"", 3), 3)
        self.assertEqual(parse_varint_field(hero or b"", 4), 36)
        self.assertIn(b"Local Bot", login)
        self.assertIn(
            pb_bytes(
                2,
                pb_message(
                    pb_varint(1, 300), pb_varint(2, 2), pb_varint(3, 1)
                ),
            ),
            login,
        )
        self.assertIn(
            pb_bytes(
                2,
                pb_message(
                    pb_varint(1, 1), pb_varint(2, 3), pb_varint(3, 3)
                ),
            ),
            login,
        )

        loaded = pvp_gamer_load_body(1234, pvp or b"", current_time=77)
        self.assertEqual(parse_varint_field(loaded, 1), 1234)
        self.assertEqual(parse_bytes_field(loaded, 2), pvp)
        self.assertEqual(parse_varint_field(loaded, 4), 77)

        init_ammo = pvp_initial_ammo_body(pvp or b"")
        self.assertEqual(parse_bytes_field(init_ammo, 1), pvp)
        self.assertIsNone(parse_bytes_field(init_ammo, 2))

        observers = pvp_observer_count_body(1234)
        self.assertEqual(parse_varint_field(observers, 1), 1234)
        self.assertEqual(parse_varint_field(observers, 2), 0)
        self.assertEqual(parse_varint_field(observers, 3), 0)

        betting = pvp_bet_simple_body(1234)
        self.assertEqual(parse_varint_field(betting, 1), 1234)
        self.assertEqual(parse_varint_field(betting, 2), 9_999_999)

        next_round = pvp_next_round_body(
            parse_bytes_field(pvp or b"", 2) or b"", pvp or b""
        )
        self.assertEqual(parse_varint_field(next_round, 2), 1)
        event = pvp_shoot_event_result_body(
            parse_bytes_field(pvp or b"", 2) or b"",
            parse_bytes_field(pvp or b"", 2) or b"",
            0,
            1,
        )
        self.assertEqual(parse_varint_field(event, 1), 1)
        self.assertEqual(parse_varint_field(event, 3), 0)
        self.assertEqual(parse_varint_field(event, 10), 1)
        event_wire = parse_bytes_field(event, 4) or b""
        source_outline = parse_bytes_field(event_wire, 1) or b""
        self.assertEqual(
            parse_varint_field(parse_bytes_field(source_outline, 10) or b"", 1),
            1,
        )
        self.assertEqual(
            parse_varint_field(parse_bytes_field(source_outline, 10) or b"", 3),
            3,
        )
        self.assertEqual(len(parse_bytes_fields(source_outline, 5)), 2)
        self.assertEqual(parse_bytes_fields(source_outline, 11), [])
        event_wires = parse_bytes_fields(event, 4)
        self.assertEqual(len(event_wires), 2)
        final_outline = parse_bytes_field(event_wires[1], 1) or b""
        final_target = parse_bytes_field(event_wires[1], 2) or b""
        self.assertEqual(parse_varint_field(final_outline, 1), 0)
        self.assertEqual(parse_varint_field(final_outline, 9), 3)
        self.assertEqual(parse_varint_field(final_outline, 18), 2)
        self.assertEqual(final_target, final_outline)
        notify = pvp_event_notification_body(event, pvp or b"")
        self.assertTrue(parse_bytes_field(notify, 1))
        surrender = pvp_surrender_body(1234, pvp or b"")
        self.assertEqual(parse_varint_field(surrender, 1), 1234)
        self.assertEqual(parse_bytes_field(surrender, 2), pvp)

    def test_self_shot_preserves_target_and_animation_fields(self) -> None:
        _, pvp, player, bot = pvp_login_snapshot(
            1234, "Local Hunter", "local-pvp:test", 1, 4,
            0, 36, 105, 0, 24, 10103,
        )
        event = pvp_shoot_event_result_body(
            player,
            player,
            0,
            0,
            source_ammo_after=5,
            target_dead=True,
            is_end_pvp=True,
            shoot_self_num=1,
            event_id=7,
            is_next_round=False,
            event_time=123456,
            source_event_status=1,
            target_event_status=5,
        )
        self.assertEqual(parse_varint_field(event, 3), 0)
        self.assertEqual(parse_varint_field(event, 10), 0)
        self.assertEqual(parse_varint_field(event, 7), 1)
        self.assertEqual(parse_varint_field(event, 9), 1)
        self.assertEqual(parse_varint_field(event, 13), 7)
        self.assertEqual(parse_varint_field(event, 14), 0)
        event_wire = parse_bytes_field(event, 4) or b""
        source = parse_bytes_field(event_wire, 1) or b""
        target = parse_bytes_field(event_wire, 2) or b""
        self.assertEqual(parse_varint_field(source, 1), 0)
        self.assertEqual(parse_varint_field(target, 1), 0)
        self.assertEqual(parse_varint_field(source, 28), 123456)
        self.assertEqual(parse_varint_field(target, 28), 123456)
        self.assertEqual(parse_varint_field(source, 63), 1)
        self.assertEqual(parse_varint_field(target, 63), 5)
        self.assertIsNone(parse_varint_field(source, 18))
        self.assertEqual(parse_varint_field(target, 49), 1)
        self.assertEqual(parse_varint_field(target, 73), 2)

    def test_mode1_submode6_snapshot_has_three_gamers_coin_and_shop(self) -> None:
        _, pvp, player, _ = pvp_login_snapshot(
            1234, "Local Hunter", "local-pvp:test", 1, 6,
            0, 36, 105, 0, 24, 10103,
        )
        gamers = parse_bytes_fields(pvp, 2)
        cards = parse_bytes_fields(pvp, 7)
        self.assertEqual(len(gamers), 3)
        self.assertEqual([parse_varint_field(gamer, 3) for gamer in gamers], [0, 1, 2])
        self.assertEqual([parse_varint_field(gamer, 5) for gamer in gamers], [10_000] * 3)
        self.assertEqual(parse_varint_field(player, 5), 10_000)
        self.assertEqual(
            [
                (
                    parse_varint_field(card, 1),
                    parse_varint_field(card, 2),
                    parse_varint_field(card, 3),
                    parse_varint_field(card, 5),
                    parse_varint_field(card, 9),
                )
                for card in cards
            ],
            [
                (1, 2001, 100, 1, 100),
                (2, 2003, 200, 1, 200),
                (3, 2004, 100, 1, 100),
                (4, 2008, 200, 1, 200),
            ],
        )
        self.assertEqual(parse_varint_field(pvp, 21), 6)
        self.assertEqual(parse_varint_field(pvp, 40), 1)
        self.assertEqual(parse_varint_field(pvp, 41), 300)
        self.assertEqual([parse_varint_field(pvp, n) for n in (46, 47, 48)], [1, 1, 1])

    def test_diagnostic_can_hide_coin_visual_without_changing_balance_or_card_flag(self) -> None:
        _, pvp, player, _ = pvp_login_snapshot(
            1234, "Local Hunter", "local-pvp:test", 1, 6,
            0, 36, 105, 0, 24, 10103,
            show_player_coin=False,
        )
        gamers = parse_bytes_fields(pvp, 2)
        self.assertEqual([parse_varint_field(gamer, 5) for gamer in gamers], [10_000] * 3)
        self.assertEqual(parse_varint_field(player, 5), 10_000)
        self.assertEqual(parse_varint_field(pvp, 46), 1)
        self.assertIsNone(parse_varint_field(pvp, 47))
        self.assertEqual(parse_varint_field(pvp, 48), 1)

    def test_other_submode_snapshot_remains_two_player_without_shop(self) -> None:
        _, pvp, _, _ = pvp_login_snapshot(
            1234, "Local Hunter", "local-pvp:test", 1, 4,
            0, 36, 105, 0, 24, 10103,
        )
        self.assertEqual(len(parse_bytes_fields(pvp, 2)), 2)
        self.assertEqual(parse_bytes_fields(pvp, 7), [])
        self.assertEqual(parse_varint_field(pvp, 40), 0)

    def test_equipped_piggybank_is_present_in_initial_pvp_snapshot(self) -> None:
        _, pvp, player, _ = pvp_login_snapshot(
            1234, "Local Hunter", "local-pvp:1:4:0:34", 1, 4,
            0, 36, 105, 0, 24, 10103, 34,
        )
        slot = parse_bytes_field(player, 18) or b""
        self.assertEqual(parse_varint_field(slot, 1), 34)
        self.assertEqual(parse_varint_field(slot, 2), 34)
        self.assertEqual(parse_varint_field(slot, 6), 1)
        self.assertEqual(parse_varint_field(slot, 7), 2)
        self.assertEqual([parse_varint_field(pvp, n) for n in (46, 47)], [1, 1])

        upgraded = pvp_carried_card_slot_body(1034)
        self.assertEqual(parse_varint_field(upgraded, 7), 20)
        self.assertEqual(parse_varint_field(pvp_carried_card_slot_body(2034), 7), 200)
        self.assertEqual(pvp_carried_card_slot_body(3), b"")

    def test_piggybank_use_event_animates_coin_gain_and_clears_slot(self) -> None:
        slot = pvp_carried_card_slot_body(34)
        event = pvp_piggybank_use_event_result_body(
            b"", slot, coin_delta=2, event_id=7, event_time=123456
        )
        self.assertEqual(parse_varint_field(event, 1), 8)
        self.assertEqual(parse_varint_field(event, 2), 1028)
        self.assertEqual(parse_varint_field(event, 5), 34)
        self.assertEqual(parse_varint_field(event, 6), 34)
        small_events = parse_bytes_fields(event, 4)
        self.assertEqual(len(small_events), 2)

        coin_target = parse_bytes_field(small_events[0], 2) or b""
        self.assertEqual(parse_varint_field(coin_target, 9), 50)
        coin_change = parse_bytes_field(coin_target, 4) or b""
        self.assertEqual(parse_varint_field(coin_change, 1), 2)
        self.assertEqual(parse_varint_field(coin_change, 2), 21)

        slot_target = parse_bytes_field(small_events[1], 2) or b""
        self.assertEqual(parse_varint_field(slot_target, 9), 6)
        self.assertEqual(parse_varint_field(slot_target, 48), 2)
        cleared = parse_bytes_field(slot_target, 13) or b""
        self.assertEqual(parse_varint_field(cleared, 1), 0)
        self.assertEqual(parse_varint_field(cleared, 2), 0)
        self.assertEqual(parse_varint_field(cleared, 7), (1 << 64) - 1)
        self.assertEqual(parse_varint_field(pvp_empty_card_slot_body(), 6), 1)

    def test_selected_piggybank_flows_from_match_request_into_visible_pvp_slot(self) -> None:
        state = self._state({"selectedHero": 0})
        state._accounts = {}
        state._next_gid = 1000001

        async def run_exchange() -> None:
            pvp_listener = await asyncio.start_server(
                lambda reader, writer: serve_client(
                    reader, writer, state, "body", "pvp"
                ),
                "127.0.0.1",
                0,
            )
            logic_listener = await asyncio.start_server(
                lambda reader, writer: serve_client(
                    reader, writer, state, "body", "logic"
                ),
                "127.0.0.1",
                0,
            )
            logic_writer = None
            pvp_writer = None
            try:
                state.pvp_port = pvp_listener.sockets[0].getsockname()[1]
                logic_reader, logic_writer = await asyncio.open_connection(
                    "127.0.0.1", logic_listener.sockets[0].getsockname()[1]
                )
                logic_writer.write(
                    encode_frame(
                        6,
                        1,
                        pb_varint(2, 1)
                        + pb_varint(4, 0)
                        + pb_varint(7, 4)
                        + pb_varint(8, 34),
                        index=421,
                        length_mode="body",
                    )
                )

                async with asyncio.timeout(3):
                    head, ack, _ = await read_frame(logic_reader, "body")
                self.assertEqual((head.cmd, head.act, head.index, head.error), (6, 1, 421, 0))
                async with asyncio.timeout(3):
                    head, start_notification, _ = await read_frame(logic_reader, "body")
                self.assertEqual((head.cmd, head.act), (253, 3))
                start_info = parse_bytes_field(start_notification, 1) or b""
                marker = (parse_bytes_field(start_info, 2) or b"").decode("utf-8")
                self.assertEqual(marker, "local-pvp:1:4:0:34")

                pvp_reader, pvp_writer = await asyncio.open_connection(
                    "127.0.0.1", state.pvp_port
                )
                pvp_writer.write(
                    encode_frame(
                        3,
                        1,
                        pb_bytes(2, marker),
                        index=422,
                        length_mode="body",
                    )
                )
                async with asyncio.timeout(3):
                    head, login, _ = await read_frame(pvp_reader, "body")
                self.assertEqual((head.cmd, head.act, head.index, head.error), (3, 1, 422, 0))
                pvp_info = parse_bytes_field(login, 2) or b""
                player = parse_bytes_fields(pvp_info, 2)[0]
                visible_slot = parse_bytes_field(player, 18) or b""
                self.assertEqual(parse_varint_field(visible_slot, 1), 34)
                self.assertEqual(parse_varint_field(visible_slot, 2), 34)
                self.assertEqual(parse_varint_field(visible_slot, 7), 2)

                # A match request without a selected carried card must not
                # fabricate the piggybank slot/prop.
                pvp_writer.close()
                await pvp_writer.wait_closed()
                pvp_writer = None
                logic_writer.write(
                    encode_frame(
                        6,
                        1,
                        pb_varint(2, 1)
                        + pb_varint(4, 0)
                        + pb_varint(7, 4)
                        + pb_varint(8, 0),
                        index=423,
                        length_mode="body",
                    )
                )
                async with asyncio.timeout(3):
                    head, _, _ = await read_frame(logic_reader, "body")
                self.assertEqual((head.cmd, head.act, head.index, head.error), (6, 1, 423, 0))
                async with asyncio.timeout(3):
                    head, start_notification, _ = await read_frame(logic_reader, "body")
                self.assertEqual((head.cmd, head.act), (253, 3))
                start_info = parse_bytes_field(start_notification, 1) or b""
                marker = (parse_bytes_field(start_info, 2) or b"").decode("utf-8")
                self.assertEqual(marker, "local-pvp:1:4:0:0")
                pvp_reader, pvp_writer = await asyncio.open_connection(
                    "127.0.0.1", state.pvp_port
                )
                pvp_writer.write(
                    encode_frame(
                        3,
                        1,
                        pb_bytes(2, marker),
                        index=424,
                        length_mode="body",
                    )
                )
                async with asyncio.timeout(3):
                    head, login, _ = await read_frame(pvp_reader, "body")
                self.assertEqual((head.cmd, head.act, head.index, head.error), (3, 1, 424, 0))
                pvp_info = parse_bytes_field(login, 2) or b""
                player = parse_bytes_fields(pvp_info, 2)[0]
                self.assertEqual(parse_bytes_field(player, 18), None)
            finally:
                if logic_writer is not None:
                    logic_writer.close()
                    await logic_writer.wait_closed()
                if pvp_writer is not None:
                    pvp_writer.close()
                    await pvp_writer.wait_closed()
                logic_listener.close()
                pvp_listener.close()
                await logic_listener.wait_closed()
                await pvp_listener.wait_closed()

        asyncio.run(run_exchange())

    def test_blank_shot_keeps_real_and_blank_stacks_distinct(self) -> None:
        event = pvp_shoot_event_result_body(
            b"", b"", 0, 1, ammo_cfg_id=300,
            source_ammo_after=4, source_fake_ammo_after=1,
        )
        event_wire = parse_bytes_field(event, 4) or b""
        source = parse_bytes_field(event_wire, 1) or b""
        self.assertEqual(
            [parse_varint_field(ammo, 1) for ammo in parse_bytes_fields(source, 5)],
            [300, 1],
        )
        self.assertEqual(
            [parse_varint_field(ammo, 2) for ammo in parse_bytes_fields(source, 5)],
            [1, 4],
        )

    def test_opponent_shot_and_pvp_turn_state(self) -> None:
        _, pvp, player, bot = pvp_login_snapshot(
            1234, "Local Hunter", "local-pvp:test", 1, 4,
            0, 36, 105, 0, 24, 10103,
        )
        event = pvp_shoot_event_result_body(
            player,
            bot,
            0,
            1,
            event_id=3,
            is_next_round=True,
            event_time=222,
        )
        self.assertEqual(parse_varint_field(event, 3), 0)
        self.assertEqual(parse_varint_field(event, 10), 1)
        self.assertIsNone(parse_varint_field(event, 7))
        self.assertEqual(parse_varint_field(event, 13), 3)
        self.assertEqual(parse_varint_field(event, 14), 1)

        updated = pvp_info_with_state(
            pvp,
            player,
            bot,
            round_number=4,
            turn_number=9,
            current_index=1,
        )
        self.assertEqual(parse_varint_field(updated, 4), 4)
        self.assertEqual(parse_varint_field(updated, 8), 9)
        self.assertEqual(parse_varint_field(updated, 9), 2)
        self.assertEqual(parse_varint_field(updated, 10), 1)

    def test_advanced_round_updates_embedded_gamers_and_ammo(self) -> None:
        _, pvp, player, bot = pvp_login_snapshot(
            1234, "Local Hunter", "local-pvp:test", 1, 4,
            0, 36, 105, 0, 24, 10103,
        )
        player = pvp_gamer_with_state(
            player, hp=3, ammo_number=5, round_number=2
        )
        bot = pvp_gamer_with_state(
            bot, hp=3, ammo_number=5, round_number=2
        )
        updated = pvp_info_with_state(
            pvp, player, bot,
            round_number=2,
            turn_number=3,
            current_index=0,
        )
        gamers = parse_bytes_fields(updated, 2)
        self.assertEqual(len(gamers), 2)
        self.assertEqual([parse_varint_field(gamer, 6) for gamer in gamers], [2, 2])
        gun = parse_bytes_field(gamers[0], 7) or b""
        real_ammo = next(
            ammo
            for ammo in parse_bytes_fields(gun, 2)
            if parse_varint_field(ammo, 1) == 1
        )
        self.assertEqual(parse_varint_field(real_ammo, 2), 5)

    def test_mode1_submode6_tcp_login_load_and_third_gamer_query(self) -> None:
        state = self._state({"selectedHero": 0})
        state._accounts = {}
        state._next_gid = 1000001
        state.pvp_port = 0

        async def run_exchange() -> None:
            listener = await asyncio.start_server(
                lambda reader, writer: serve_client(
                    reader, writer, state, "body", "pvp"
                ),
                "127.0.0.1",
                0,
            )
            writer = None
            try:
                port = listener.sockets[0].getsockname()[1]
                reader, writer = await asyncio.open_connection("127.0.0.1", port)

                async def receive(cmd: int, act: int, index: int = 0) -> bytes:
                    async with asyncio.timeout(2):
                        while True:
                            head, body, _ = await read_frame(reader, "body")
                            if (head.cmd, head.act, head.index) == (cmd, act, index):
                                return body

                def request(cmd: int, act: int, body: bytes, index: int) -> None:
                    writer.write(encode_frame(
                        cmd, act, body, index=index, length_mode="body"
                    ))

                request(3, 1, pb_bytes(2, "local-pvp:1:6:0:3"), 201)
                login = await receive(3, 1, 201)
                pvp = parse_bytes_field(login, 2) or b""
                self.assertEqual(len(parse_bytes_fields(pvp, 2)), 3)
                self.assertEqual(len(parse_bytes_fields(pvp, 7)), 4)

                with patch("server.PVP_OPENING_SEQUENCE_DELAY", 0.08):
                    request(3, 14, b"", 202)
                    loaded = await receive(3, 14, 202)
                    loaded_pvp = parse_bytes_field(loaded, 2) or b""
                    self.assertEqual(len(parse_bytes_fields(loaded_pvp, 2)), 3)
                    self.assertEqual(parse_varint_field(loaded_pvp, 9), 18)
                    cinema = await receive(255, 18)
                    self.assertEqual(parse_bytes_field(cinema, 1), b'local-opening')
                    cinema_started = time.monotonic()
                    presentation = await receive(255, 16)
                    # Preloaded panel is queued locally until native TV finish.
                    intro_pvp = parse_bytes_field(presentation, 1) or b''
                    self.assertEqual(parse_varint_field(intro_pvp, 9), 15)
                    self.assertEqual(parse_bytes_fields(intro_pvp, 2),
                                     parse_bytes_fields(loaded_pvp, 2))
                    intro_started = time.monotonic()
                    # Native state notifications leave TV/presentation and
                    # restore isStartPvp, which controls the Quit button.
                    phase = await receive(255, 11)
                    self.assertEqual(parse_varint_field(phase, 2), 15)
                    phase = await receive(255, 11)
                    self.assertEqual(parse_varint_field(phase, 2), 2)
                    self.assertEqual(parse_varint_field(phase, 3), 1)
                    init_ammo = await receive(255, 7)
                    self.assertGreaterEqual(time.monotonic() - intro_started, 0.07)
                    init_pvp = parse_bytes_field(init_ammo, 1) or b""
                    self.assertEqual(parse_varint_field(init_pvp, 9), 2)
                    init_gamers = parse_bytes_fields(init_pvp, 2)
                    self.assertEqual(len(init_gamers), 3)
                    init_gun = parse_bytes_field(init_gamers[0], 7) or b""
                    init_stacks = parse_bytes_fields(init_gun, 2)
                    self.assertEqual(
                        [
                            (parse_varint_field(ammo, 1), parse_varint_field(ammo, 2))
                            for ammo in init_stacks
                        ],
                        [(300, 2), (1, 2)],
                    )
                    self.assertIsNone(parse_bytes_field(init_ammo, 2))
                    # The optional reserve pool is still unknown; avoid inventing
                    # ammoBank data while reproducing the proven loaded-magazine path.
                    turn_wait_started = time.monotonic()
                    turn_start = await receive(255, 1)
                    self.assertGreaterEqual(
                        time.monotonic() - turn_wait_started, 0.06
                    )
                    turn_gamer = parse_bytes_field(turn_start, 1) or b""
                    self.assertEqual(parse_varint_field(turn_gamer, 3), 0)

                request(3, 19, pb_varint(2, 2), 203)
                gamer_info = await receive(3, 19, 203)
                extra_bot = parse_bytes_field(gamer_info, 2) or b""
                self.assertEqual(parse_varint_field(extra_bot, 3), 2)
                self.assertEqual(
                    parse_varint_field(parse_bytes_field(extra_bot, 2) or b"", 1),
                    9000002,
                )
            finally:
                if writer is not None:
                    writer.close()
                    await writer.wait_closed()
                listener.close()
                await listener.wait_closed()

        asyncio.run(run_exchange())

    def test_mode1_wanted_marks_target_and_pays_first_damaging_shooter(self) -> None:
        state = self._state({"selectedHero": 0})
        state._accounts = {}
        state._next_gid = 1000001
        state.pvp_port = 0

        async def run_exchange() -> None:
            listener = await asyncio.start_server(
                lambda reader, writer: serve_client(
                    reader, writer, state, "body", "pvp"
                ),
                "127.0.0.1",
                0,
            )
            writer = None
            try:
                port = listener.sockets[0].getsockname()[1]
                reader, writer = await asyncio.open_connection("127.0.0.1", port)

                async def receive(cmd: int, act: int, index: int = 0) -> tuple[object, bytes]:
                    async with asyncio.timeout(3):
                        while True:
                            head, body, _ = await read_frame(reader, "body")
                            if (head.cmd, head.act, head.index) == (cmd, act, index):
                                return head, body

                def request(cmd: int, act: int, body: bytes, index: int) -> None:
                    writer.write(encode_frame(
                        cmd, act, body, index=index, length_mode="body"
                    ))

                request(3, 1, pb_bytes(2, "local-pvp:1:6:0:0"), 451)
                await receive(3, 1, 451)
                request(3, 14, b"", 452)
                await receive(3, 14, 452)
                await receive(255, 7)
                await receive(255, 1)

                request(
                    3,
                    5,
                    pb_varint(1, 1) + pb_varint(2, 1) + pb_varint(4, 1),
                    453,
                )
                ack, _ = await receive(3, 5, 453)
                self.assertEqual(ack.error, 0)
                _, notification = await receive(255, 2)
                use_result = parse_bytes_field(notification, 1) or b""
                self.assertEqual(parse_varint_field(use_result, 2), 1020)
                use_event = parse_bytes_fields(use_result, 4)[-1]
                use_target = parse_bytes_field(use_event, 2) or b""
                added = parse_bytes_fields(use_target, 25)
                self.assertEqual(
                    [parse_varint_field(buff, 1) for buff in added],
                    [WANTED_PARENT_BUFF_CFG_ID, WANTED_REWARD_BUFF_CFG_ID],
                )
                self.assertEqual(
                    [parse_varint_field(buff, 3) for buff in added],
                    [
                        1_000_000 + WANTED_PARENT_BUFF_CFG_ID,
                        1_000_000 + WANTED_REWARD_BUFF_CFG_ID,
                    ],
                )

                request(3, 3, pb_varint(1, 1), 454)
                ack, _ = await receive(3, 3, 454)
                self.assertEqual(ack.error, 0)
                _, notification = await receive(255, 2)
                shot_result = parse_bytes_field(notification, 1) or b""
                shot_event = parse_bytes_field(shot_result, 4) or b""
                source_outline = parse_bytes_field(shot_event, 1) or b""
                target_outline = parse_bytes_field(shot_event, 2) or b""
                coin_change = parse_bytes_field(source_outline, 4) or b""
                self.assertEqual(
                    parse_varint_field(coin_change, 1), WANTED_REWARD_R_CHIPS
                )
                self.assertEqual(parse_varint_field(coin_change, 2), 7)
                self.assertEqual(
                    [
                        parse_varint_field(buff, 1)
                        for buff in parse_bytes_fields(target_outline, 24)
                    ],
                    [WANTED_PARENT_BUFF_CFG_ID, WANTED_REWARD_BUFF_CFG_ID],
                )
                self.assertEqual(
                    [
                        parse_varint_field(buff, 3)
                        for buff in parse_bytes_fields(target_outline, 24)
                    ],
                    [
                        1_000_000 + WANTED_PARENT_BUFF_CFG_ID,
                        1_000_000 + WANTED_REWARD_BUFF_CFG_ID,
                    ],
                )
                updated_pvp = parse_bytes_field(notification, 2) or b""
                updated_gamers = parse_bytes_fields(updated_pvp, 2)
                self.assertEqual(parse_varint_field(updated_gamers[0], 5), 9_804)
                self.assertEqual(
                    [
                        parse_varint_field(buff, 1)
                        for buff in parse_bytes_fields(updated_gamers[1], 8)
                    ],
                    [],
                )
            finally:
                if writer is not None:
                    writer.close()
                    await writer.wait_closed()
                listener.close()
                await listener.wait_closed()

        with (
            patch(
                "server._random_shop_specs",
                return_value=((2021, 200), (2003, 200), (2004, 100), (2011, 200)),
            ),
            patch("server._draw_loaded_ammo", return_value=1),
            patch("server.PVP_OPENING_SEQUENCE_DELAY", 0.001),
            patch("server.PREPARE_SIGNAL_DELAY", 0.0),
        ):
            asyncio.run(run_exchange())

    def test_mode1_wanted_does_not_tick_for_repeated_blank_self_shots(self) -> None:
        state = self._state({"selectedHero": 0})
        state._accounts = {}
        state._next_gid = 1000001
        state.pvp_port = 0

        async def run_exchange() -> None:
            listener = await asyncio.start_server(
                lambda reader, writer: serve_client(reader, writer, state, "body", "pvp"),
                "127.0.0.1", 0,
            )
            writer = None
            try:
                reader, writer = await asyncio.open_connection(
                    "127.0.0.1", listener.sockets[0].getsockname()[1],
                )

                async def receive(cmd: int, act: int, index: int = 0):
                    async with asyncio.timeout(3):
                        while True:
                            head, body, _ = await read_frame(reader, "body")
                            if (head.cmd, head.act, head.index) == (cmd, act, index):
                                return head, body

                def request(cmd: int, act: int, body: bytes, index: int):
                    writer.write(encode_frame(cmd, act, body, index=index, length_mode="body"))

                request(3, 1, pb_bytes(2, "local-pvp:1:6:0:0"), 481)
                await receive(3, 1, 481)
                request(3, 14, b"", 482)
                await receive(3, 14, 482)
                await receive(255, 7)
                await receive(255, 1)
                request(3, 5, pb_varint(1, 1) + pb_varint(2, 1) + pb_varint(4, 1), 483)
                ack, _ = await receive(3, 5, 483)
                self.assertEqual(ack.error, 0)
                await receive(255, 2)
                for request_index in (484, 485):
                    request(3, 3, pb_varint(1, 0), request_index)
                    ack, _ = await receive(3, 3, request_index)
                    self.assertEqual(ack.error, 0)
                    _, notification = await receive(255, 2)
                    result = parse_bytes_field(notification, 1) or b""
                    self.assertEqual(parse_varint_field(result, 1), 1)
                    info = parse_bytes_field(notification, 2) or b""
                    target = parse_bytes_fields(info, 2)[1]
                    marker = next(
                        b for b in parse_bytes_fields(target, 8)
                        if parse_varint_field(b, 1) == WANTED_REWARD_BUFF_CFG_ID
                    )
                    self.assertEqual(parse_varint_field(marker, 7), 3)
                    self.assertEqual(parse_varint_field(target, 5), 10_000)
            finally:
                if writer is not None:
                    writer.close()
                    await writer.wait_closed()
                listener.close()
                await listener.wait_closed()

        with (
            patch("server._random_shop_specs", return_value=(
                (2021, 200), (2003, 200), (2004, 100), (2011, 200),
            )),
            patch("server._draw_loaded_ammo", return_value=300),
            patch("server.PVP_OPENING_SEQUENCE_DELAY", 0.001),
            patch("server.PLAYER_CONTINUE_SHOT_SETTLE", 0.0),
        ):
            asyncio.run(run_exchange())

    def test_mode1_wanted_counts_a_full_rotation_from_each_application(self) -> None:
        state = self._state({"selectedHero": 0})
        state._accounts = {}
        state._next_gid = 1000001
        state.pvp_port = 0

        async def run_exchange() -> None:
            listener = await asyncio.start_server(
                lambda reader, writer: serve_client(
                    reader, writer, state, "body", "pvp"
                ),
                "127.0.0.1",
                0,
            )
            writer = None
            try:
                port = listener.sockets[0].getsockname()[1]
                reader, writer = await asyncio.open_connection("127.0.0.1", port)
                pending_frames: list[tuple[object, bytes]] = []

                async def next_frame() -> tuple[object, bytes, bytes]:
                    if pending_frames:
                        head, body = pending_frames.pop(0)
                        return head, body, b""
                    return await read_frame(reader, "body")

                async def receive(
                    cmd: int, act: int, index: int = 0
                ) -> tuple[object, bytes]:
                    for pending_index, (pending_head, pending_body) in enumerate(
                        pending_frames
                    ):
                        if (
                            pending_head.cmd,
                            pending_head.act,
                            pending_head.index,
                        ) == (cmd, act, index):
                            pending_frames.pop(pending_index)
                            return pending_head, pending_body
                    async with asyncio.timeout(3):
                        while True:
                            # The pending queue was searched above. Read new
                            # wire data, otherwise an unrelated intro packet is
                            # popped/requeued forever without yielding to timeout.
                            head, body, _ = await read_frame(reader, "body")
                            if (head.cmd, head.act, head.index) == (cmd, act, index):
                                return head, body
                            pending_frames.append((head, body))

                def request(cmd: int, act: int, body: bytes, index: int) -> None:
                    writer.write(encode_frame(
                        cmd, act, body, index=index, length_mode="body"
                    ))

                request(3, 1, pb_bytes(2, "local-pvp:1:6:0:0"), 461)
                await receive(3, 1, 461)
                request(3, 14, b"", 462)
                await receive(3, 14, 462)
                await receive(255, 7)
                await receive(255, 1)

                # Reproduce the player's two marks in the same turn. Neither
                # should expire on Bot 1's first turn; both get 3 actor changes.
                request(
                    3,
                    5,
                    pb_varint(1, 1) + pb_varint(2, 1) + pb_varint(4, 1),
                    463,
                )
                ack, _ = await receive(3, 5, 463)
                self.assertEqual(ack.error, 0)
                _, use_notification = await receive(255, 2)
                use_result = parse_bytes_field(use_notification, 1) or b""
                self.assertEqual(parse_varint_field(use_result, 2), 1020)
                applied_outline = parse_bytes_field(
                    parse_bytes_fields(use_result, 4)[-1], 2,
                ) or b""
                self.assertEqual(
                    [parse_varint_field(b, 7)
                     for b in parse_bytes_fields(applied_outline, 25)],
                    [3, 3],
                )
                request(
                    3, 5,
                    pb_varint(1, 2) + pb_varint(2, 0) + pb_varint(4, 1),
                    464,
                )
                ack, _ = await receive(3, 5, 464)
                self.assertEqual(ack.error, 0)
                await receive(255, 2)

                with (
                    patch("server._draw_loaded_ammo", side_effect=[1, 300, 300]),
                    patch("server.PREPARE_SIGNAL_DELAY", 0.001),
                    patch("server.PLAYER_OTHER_SHOT_SETTLE", 0.006),
                    patch("server.BOT_SHOT_SETTLE", 0.006),
                    patch("server.BOT_THINK_DELAY", 0.005),
                    patch("server.BOT_RAISE_GUN_DELAY", 0.001),
                    patch("server.BOT_SELECT_TARGET_DELAY", 0.001),
                ):
                    request(3, 3, pb_varint(1, 2), 465)
                    ack, _ = await receive(3, 3, 465)
                    self.assertEqual(ack.error, 0)

                    event_types: list[int] = []
                    shoot_sources: list[int] = []
                    shoot_targets: list[int] = []
                    expiries: dict[int, bytes] = {}
                    countdowns: list[tuple[int, int, int]] = []
                    async with asyncio.timeout(4):
                        while len(shoot_sources) < 3 or len(expiries) < 2:
                            head, notification, _ = await next_frame()
                            if (head.cmd, head.act) != (255, 2):
                                continue
                            result = parse_bytes_field(notification, 1) or b""
                            event_type = parse_varint_field(result, 1) or 0
                            event_types.append(event_type)
                            if event_type == 1:
                                shoot_sources.append(
                                    parse_varint_field(result, 3) or 0
                                )
                                shoot_targets.append(
                                    parse_varint_field(result, 10) or 0
                                )
                            elif event_type == 17:
                                for small_event in parse_bytes_fields(result, 4):
                                    outline = parse_bytes_field(small_event, 2) or b""
                                    target = parse_varint_field(outline, 1) or 0
                                    typ = parse_varint_field(outline, 9)
                                    if typ == 25:
                                        buff = parse_bytes_fields(outline, 3)[-1]
                                        countdowns.append((
                                            len(shoot_sources), target,
                                            parse_varint_field(buff, 7) or 0,
                                        ))
                                    elif typ == 10:
                                        self.assertEqual(len(shoot_sources), 3)
                                        expiries[target] = notification

                self.assertEqual(shoot_sources, [0, 1, 2])
                self.assertEqual(shoot_targets, [2, 0, 0])
                self.assertEqual(event_types, [1, 17, 17, 1, 17, 17, 1, 17, 17])
                self.assertEqual(countdowns, [(1, 0, 2), (1, 1, 2),
                                              (2, 0, 1), (2, 1, 1)])
                self.assertEqual(set(expiries), {0, 1})
                expiry_notification = expiries[1]
                expiry_result = parse_bytes_field(expiry_notification, 1) or b""
                expiry_events = parse_bytes_fields(expiry_result, 4)
                self.assertEqual(len(expiry_events), 1)
                coin_outline = parse_bytes_field(expiry_events[0], 2) or b""
                self.assertEqual(parse_varint_field(coin_outline, 9), 10)
                coin_change = parse_bytes_field(coin_outline, 4) or b""
                self.assertEqual(
                    parse_varint_field(coin_change, 1), WANTED_REWARD_R_CHIPS
                )
                self.assertEqual(parse_varint_field(coin_change, 2), 7)
                marker_outline = coin_outline
                self.assertEqual(
                    [
                        parse_varint_field(buff, 1)
                        for buff in parse_bytes_fields(marker_outline, 24)
                    ],
                    [WANTED_PARENT_BUFF_CFG_ID, WANTED_REWARD_BUFF_CFG_ID],
                )
                updated_pvp = parse_bytes_field(expiry_notification, 2) or b""
                updated_gamers = parse_bytes_fields(updated_pvp, 2)
                self.assertEqual(len(updated_gamers), 3)
                self.assertEqual(parse_varint_field(updated_gamers[0], 5), 9_604)
                self.assertEqual(parse_varint_field(updated_gamers[1], 5), 10_004)
                self.assertNotIn(
                    WANTED_REWARD_BUFF_CFG_ID,
                    [
                        parse_varint_field(buff, 1)
                        for buff in parse_bytes_fields(updated_gamers[1], 8)
                    ],
                )
            finally:
                if writer is not None:
                    writer.close()
                    await writer.wait_closed()
                listener.close()
                await listener.wait_closed()

        with (
            patch(
                "server._random_shop_specs",
                return_value=((2021, 200), (2021, 200), (2004, 100), (2011, 200)),
            ),
            patch("server.PVP_OPENING_SEQUENCE_DELAY", 0.001),
        ):
            asyncio.run(run_exchange())

    def test_piggybank_local_match_collects_coins_and_removes_icon_slot(self) -> None:
        state = self._state({"selectedHero": 0})
        state._accounts = {}
        state._next_gid = 1000001
        state.pvp_port = 0

        async def run_exchange() -> None:
            listener = await asyncio.start_server(
                lambda reader, writer: serve_client(
                    reader, writer, state, "body", "pvp"
                ),
                "127.0.0.1",
                0,
            )
            writer = None
            try:
                port = listener.sockets[0].getsockname()[1]
                reader, writer = await asyncio.open_connection("127.0.0.1", port)

                async def receive(cmd: int, act: int, index: int = 0) -> tuple[object, bytes]:
                    async with asyncio.timeout(3):
                        while True:
                            head, body, _ = await read_frame(reader, "body")
                            if (head.cmd, head.act, head.index) == (cmd, act, index):
                                return head, body

                def request(cmd: int, act: int, body: bytes, index: int) -> None:
                    writer.write(encode_frame(
                        cmd, act, body, index=index, length_mode="body"
                    ))

                request(3, 1, pb_bytes(2, "local-pvp:1:4:0:34"), 401)
                _, login = await receive(3, 1, 401)
                pvp = parse_bytes_field(login, 2) or b""
                player = parse_bytes_fields(pvp, 2)[0]
                initial_slot = parse_bytes_field(player, 18) or b""
                self.assertEqual(parse_varint_field(initial_slot, 2), 34)
                self.assertEqual(parse_varint_field(initial_slot, 7), 2)

                request(3, 14, b"", 402)
                await receive(3, 14, 402)
                _, opening_turn = await receive(255, 1)
                self.assertEqual(
                    pvp_gamer_skill_cd(parse_bytes_field(opening_turn, 1) or b""),
                    2,
                )

                # Typ_Use is allowed in the ordinary two-player local room;
                # it is not gated on the separate trio/shop mode.
                request(
                    3,
                    5,
                    pb_varint(1, 34) + pb_varint(2, 0) + pb_varint(4, 2),
                    403,
                )
                ack, _ = await receive(3, 5, 403)
                self.assertEqual(ack.error, 0)
                _, notification = await receive(255, 2)
                result = parse_bytes_field(notification, 1) or b""
                self.assertEqual(parse_varint_field(result, 1), 8)
                self.assertEqual(parse_varint_field(result, 2), 1028)
                self.assertEqual(parse_varint_field(result, 5), 34)
                self.assertEqual(parse_varint_field(result, 6), 34)
                use_events = parse_bytes_fields(result, 4)
                self.assertEqual(len(use_events), 2)
                coin_target = parse_bytes_field(use_events[0], 2) or b""
                coin_change = parse_bytes_field(coin_target, 4) or b""
                self.assertEqual(parse_varint_field(coin_target, 9), 50)
                self.assertEqual(parse_varint_field(coin_change, 1), 2)
                self.assertEqual(parse_varint_field(coin_change, 2), 21)
                clear_target = parse_bytes_field(use_events[1], 2) or b""
                self.assertEqual(parse_varint_field(clear_target, 9), 6)
                self.assertEqual(parse_varint_field(clear_target, 48), 2)

                updated_pvp = parse_bytes_field(notification, 2) or b""
                updated_player = parse_bytes_fields(updated_pvp, 2)[0]
                self.assertEqual(parse_varint_field(updated_player, 5), 2)
                final_slot = parse_bytes_field(updated_player, 18) or b""
                self.assertEqual(parse_varint_field(final_slot, 1), 0)
                self.assertEqual(parse_varint_field(final_slot, 2), 0)
            finally:
                if writer is not None:
                    writer.close()
                    await writer.wait_closed()
                listener.close()
                await listener.wait_closed()

        asyncio.run(run_exchange())

    def test_piggybank_accumulates_again_when_next_round_starts(self) -> None:
        state = self._state({"selectedHero": 0})
        state._accounts = {}
        state._next_gid = 1000001
        state.pvp_port = 0

        async def run_exchange() -> None:
            listener = await asyncio.start_server(
                lambda reader, writer: serve_client(
                    reader, writer, state, "body", "pvp"
                ),
                "127.0.0.1",
                0,
            )
            writer = None
            try:
                port = listener.sockets[0].getsockname()[1]
                reader, writer = await asyncio.open_connection("127.0.0.1", port)

                async def receive(cmd: int, act: int, index: int = 0) -> tuple[object, bytes]:
                    async with asyncio.timeout(6):
                        while True:
                            head, body, _ = await read_frame(reader, "body")
                            if (head.cmd, head.act, head.index) == (cmd, act, index):
                                return head, body

                def request(cmd: int, act: int, body: bytes, index: int) -> None:
                    writer.write(encode_frame(
                        cmd, act, body, index=index, length_mode="body"
                    ))

                request(3, 1, pb_bytes(2, "local-pvp:1:4:0:34"), 411)
                await receive(3, 1, 411)
                request(3, 14, b"", 412)
                await receive(3, 14, 412)
                await receive(255, 1)

                with (
                    patch("server.random.randrange", side_effect=[0, 2] + [2] * 12),
                    patch("server.PREPARE_SIGNAL_DELAY", 0.001),
                    patch("server.PLAYER_SELF_SHOT_SETTLE", 0.002),
                    patch("server.PLAYER_CONTINUE_SHOT_SETTLE", 0.002),
                    patch("server.BOT_THINK_DELAY", 1.3),
                    patch("server.BOT_SHOT_SETTLE", 0.002),
                ):
                    request(3, 3, pb_varint(1, 0), 413)
                    await receive(3, 3, 413)
                    # The shot result itself keeps the owner active; no new
                    # operator packet should reset aim or tick the piggy bank.
                    _, blank_shot = await receive(255, 2)
                    blank_result = parse_bytes_field(blank_shot, 1) or b""
                    blank_event = parse_bytes_field(blank_result, 4) or b""
                    blank_source = parse_bytes_field(blank_event, 1) or b""
                    self.assertEqual(
                        parse_varint_field(
                            parse_bytes_field(blank_source, 10) or b"", 1
                        ),
                        300,
                    )
                    blank_pvp = parse_bytes_field(blank_shot, 2) or b""
                    blank_player = parse_bytes_fields(blank_pvp, 2)[0]
                    self.assertEqual(
                        parse_varint_field(
                            parse_bytes_field(blank_player, 18) or b"", 7
                        ),
                        2,
                    )
                    continuation = parse_bytes_field(blank_player, 19) or b""
                    self.assertEqual(parse_varint_field(continuation, 4), 1)
                    with self.assertRaises(asyncio.TimeoutError):
                        await asyncio.wait_for(
                            read_frame(reader, "body"), timeout=0.02
                        )
                    await asyncio.sleep(0.01)
                    request(3, 3, pb_varint(1, 0), 415)
                    await receive(3, 3, 415)
                    round_start = None
                    async with asyncio.timeout(6):
                        while round_start is None:
                            head, body, _ = await read_frame(reader, "body")
                            if (head.cmd, head.act) != (255, 2):
                                continue
                            result = parse_bytes_field(body, 1) or b""
                            if parse_varint_field(result, 1) == 12:
                                round_start = (result, body)

                self.assertIsNotNone(round_start)
                result, notification = round_start
                self.assertEqual(parse_varint_field(result, 1), 12)
                small_event = parse_bytes_field(result, 4) or b""
                target = parse_bytes_field(small_event, 2) or b""
                self.assertEqual(parse_varint_field(target, 9), 51)
                self.assertEqual(parse_varint_field(target, 48), 4)
                updated_pvp = parse_bytes_field(notification, 2) or b""
                updated_player = parse_bytes_fields(updated_pvp, 2)[0]
                updated_slot = parse_bytes_field(updated_player, 18) or b""
                self.assertEqual(parse_varint_field(updated_slot, 7), 4)

                request(
                    3,
                    5,
                    pb_varint(1, 34) + pb_varint(2, 0) + pb_varint(4, 2),
                    414,
                )
                use_ack, _ = await receive(3, 5, 414)
                self.assertEqual(use_ack.error, 0)
                use_notification = None
                async with asyncio.timeout(3):
                    while use_notification is None:
                        head, body, _ = await read_frame(reader, "body")
                        if (head.cmd, head.act) != (255, 2):
                            continue
                        result = parse_bytes_field(body, 1) or b""
                        if parse_varint_field(result, 1) == 8:
                            use_notification = (result, body)
                use_result, use_body = use_notification
                use_events = parse_bytes_fields(use_result, 4)
                coin_target = parse_bytes_field(use_events[0], 2) or b""
                coin_change = parse_bytes_field(coin_target, 4) or b""
                self.assertEqual(parse_varint_field(coin_change, 1), 4)
                used_pvp = parse_bytes_field(use_body, 2) or b""
                used_player = parse_bytes_fields(used_pvp, 2)[0]
                self.assertEqual(parse_varint_field(used_player, 5), 4)
                used_slot = parse_bytes_field(used_player, 18) or b""
                self.assertEqual(parse_varint_field(used_slot, 2), 0)
            finally:
                if writer is not None:
                    writer.close()
                    await writer.wait_closed()
                listener.close()
                await listener.wait_closed()

        asyncio.run(run_exchange())

    def test_last_blank_self_shot_reloads_in_the_shoot_event(self) -> None:
        state = self._state({"selectedHero": 0})
        state._accounts = {}
        state._next_gid = 1000001
        state.pvp_port = 0

        async def run_exchange() -> None:
            listener = await asyncio.start_server(
                lambda reader, writer: serve_client(
                    reader, writer, state, "body", "pvp"
                ),
                "127.0.0.1", 0,
            )
            writer = None
            try:
                reader, writer = await asyncio.open_connection(
                    "127.0.0.1", listener.sockets[0].getsockname()[1]
                )
                async def receive(cmd: int, act: int, index: int = 0) -> bytes:
                    async with asyncio.timeout(3):
                        while True:
                            head, body, _ = await read_frame(reader, "body")
                            if (head.cmd, head.act, head.index) == (cmd, act, index):
                                return body

                writer.write(encode_frame(
                    3, 1, pb_bytes(2, "local-pvp:1:4:0:0"),
                    index=501, length_mode="body",
                ))
                await receive(3, 1, 501)
                writer.write(encode_frame(3, 14, b"", index=502, length_mode="body"))
                await receive(3, 14, 502)
                await receive(255, 1)
                with (
                    patch("server.random.randrange", return_value=0),
                    patch("server.PREPARE_SIGNAL_DELAY", 0.001),
                    patch("server.PLAYER_CONTINUE_SHOT_SETTLE", 0.002),
                ):
                    writer.write(encode_frame(
                        3, 3, pb_varint(1, 0), index=503, length_mode="body"
                    ))
                    await receive(3, 3, 503)
                    shot = await receive(255, 2)
                    result = parse_bytes_field(shot, 1) or b""
                    self.assertEqual(parse_varint_field(result, 1), 1)
                    shot_pvp = parse_bytes_field(shot, 2) or b""
                    shot_player = parse_bytes_fields(shot_pvp, 2)[0]
                    shot_gun = parse_bytes_field(shot_player, 7) or b""
                    self.assertEqual(
                        [parse_varint_field(ammo, 2)
                         for ammo in parse_bytes_fields(shot_gun, 2)],
                        [1, 0],
                    )
                    shot_events = parse_bytes_fields(result, 4)
                    reload_target = parse_bytes_field(shot_events[1], 2) or b""
                    self.assertEqual(parse_varint_field(reload_target, 8), 1)
                    with self.assertRaises(asyncio.TimeoutError):
                        await asyncio.wait_for(
                            read_frame(reader, "body"), timeout=0.02
                        )
            finally:
                if writer is not None:
                    writer.close()
                    await writer.wait_closed()
                listener.close()
                await listener.wait_closed()

        with (
            patch("protocol.pvp_gun_ammo_counts", return_value=(0, 1)),
            patch("server.pvp_gun_ammo_counts", return_value=(0, 1)),
        ):
            asyncio.run(run_exchange())

    def test_mode1_trio_burst_self_shot_consumes_buff_and_remains_single(self) -> None:
        state = self._state({"selectedHero": 0})
        state._accounts = {}
        state._next_gid = 1000001
        state.pvp_port = 0

        async def run_exchange() -> None:
            listener = await asyncio.start_server(
                lambda reader, writer: serve_client(
                    reader, writer, state, "body", "pvp"
                ),
                "127.0.0.1", 0,
            )
            writer = None
            try:
                reader, writer = await asyncio.open_connection(
                    "127.0.0.1", listener.sockets[0].getsockname()[1]
                )

                async def receive(
                    cmd: int, act: int, index: int = 0,
                ) -> tuple[object, bytes]:
                    async with asyncio.timeout(4):
                        while True:
                            head, body, _ = await read_frame(reader, "body")
                            if (head.cmd, head.act, head.index) == (cmd, act, index):
                                return head, body

                def request(cmd: int, act: int, body: bytes, index: int) -> None:
                    writer.write(encode_frame(
                        cmd, act, body, index=index, length_mode="body"
                    ))

                request(3, 1, pb_bytes(2, "local-pvp:1:6:0:0"), 531)
                await receive(3, 1, 531)
                request(3, 14, b"", 532)
                await receive(3, 14, 532)
                await receive(255, 1)

                # Put Burst Mode in offer 1, buy it into the carried slot, then
                # activate it on the player (target index 0).
                request(3, 5, pb_varint(1, 1) + pb_varint(4, 3), 533)
                ack, _ = await receive(3, 5, 533)
                self.assertEqual(ack.error, 0)
                await receive(255, 2)
                request(
                    3, 5,
                    pb_varint(1, 1) + pb_varint(2, 0) + pb_varint(4, 2),
                    534,
                )
                ack, _ = await receive(3, 5, 534)
                self.assertEqual(ack.error, 0)
                _, use_notification = await receive(255, 2)
                use_result = parse_bytes_field(use_notification, 1) or b""
                self.assertEqual(parse_varint_field(use_result, 1), 8)
                self.assertEqual(parse_varint_field(use_result, 5), 2016)
                used_info = parse_bytes_field(use_notification, 2) or b""
                used_player = parse_bytes_fields(used_info, 2)[0]
                self.assertIn(
                    BURST_MODE_BUFF_CFG_ID,
                    [parse_varint_field(buff, 1)
                     for buff in parse_bytes_fields(used_player, 8)],
                )

                # Pin a blank self-shot: it remains one shot and keeps the
                # player's turn, but must clear the Burst buff/eye icon.
                with patch("server.random.randrange", return_value=0):
                    request(3, 3, pb_varint(1, 0), 535)
                    await receive(3, 3, 535)
                    _, self_shot = await receive(255, 2)
                    self_result = parse_bytes_field(self_shot, 1) or b""
                    self_events = parse_bytes_fields(self_result, 4)
                    self.assertEqual(len(self_events), 2)  # one bullet + final
                    final_outline = parse_bytes_field(self_events[-1], 1) or b""
                    removed = parse_bytes_fields(final_outline, 24)
                    self.assertEqual(
                        [parse_varint_field(buff, 1) for buff in removed],
                        [BURST_MODE_BUFF_CFG_ID],
                    )
                    self_info = parse_bytes_field(self_shot, 2) or b""
                    self_player = parse_bytes_fields(self_info, 2)[0]
                    self.assertNotIn(
                        BURST_MODE_BUFF_CFG_ID,
                        [parse_varint_field(buff, 1)
                         for buff in parse_bytes_fields(self_player, 8)],
                    )

            finally:
                if writer is not None:
                    writer.close()
                    await writer.wait_closed()
                listener.close()
                await listener.wait_closed()

        with (
            patch(
                "server._random_shop_specs",
                return_value=((2016, 300), (2003, 200), (2004, 100), (2008, 200)),
            ),
            patch("protocol.pvp_gun_ammo_counts", return_value=(2, 2)),
            patch("server.pvp_gun_ammo_counts", return_value=(2, 2)),
        ):
            asyncio.run(run_exchange())

    def test_mode1_trio_blank_self_shot_keeps_turn_without_frenzy_or_bot_action(self) -> None:
        state = self._state({"selectedHero": 0})
        state._accounts = {}
        state._next_gid = 1000001
        state.pvp_port = 0

        async def run_exchange() -> None:
            listener = await asyncio.start_server(
                lambda reader, writer: serve_client(
                    reader, writer, state, "body", "pvp"
                ),
                "127.0.0.1", 0,
            )
            writer = None
            try:
                reader, writer = await asyncio.open_connection(
                    "127.0.0.1", listener.sockets[0].getsockname()[1]
                )
                async def receive(cmd: int, act: int, index: int = 0) -> bytes:
                    async with asyncio.timeout(3):
                        while True:
                            head, body, _ = await read_frame(reader, "body")
                            if (head.cmd, head.act, head.index) == (cmd, act, index):
                                return body

                writer.write(encode_frame(
                    3, 1, pb_bytes(2, "local-pvp:1:6:0:0"),
                    index=521, length_mode="body",
                ))
                login = await receive(3, 1, 521)
                initial_info = parse_bytes_field(login, 2) or b""
                initial_player = parse_bytes_fields(initial_info, 2)[0]
                self.assertEqual(parse_varint_field(initial_player, 17), 0)
                self.assertEqual(parse_varint_field(initial_player, 23), 2)
                writer.write(encode_frame(3, 14, b"", index=522, length_mode="body"))
                await receive(3, 14, 522)
                await receive(255, 1)
                with (
                    patch("server.random.randrange", return_value=0),
                    patch("server.PREPARE_SIGNAL_DELAY", 0.001),
                    patch("server.PLAYER_CONTINUE_SHOT_SETTLE", 0.002),
                ):
                    for index, expected_fake in ((523, 1), (524, 0)):
                        writer.write(encode_frame(
                            3, 3, pb_varint(1, 0),
                            index=index, length_mode="body",
                        ))
                        await receive(3, 3, index)
                        shot = await receive(255, 2)
                        result = parse_bytes_field(shot, 1) or b""
                        self.assertEqual(parse_varint_field(result, 1), 1)
                        shot_event = parse_bytes_field(result, 4) or b""
                        source = parse_bytes_field(shot_event, 1) or b""
                        self.assertEqual(
                            parse_varint_field(
                                parse_bytes_field(source, 10) or b"", 1
                            ),
                            300,
                        )
                        shot_info = parse_bytes_field(shot, 2) or b""
                        gamers = parse_bytes_fields(shot_info, 2)
                        self.assertEqual(parse_varint_field(gamers[0], 4), 4)
                        self.assertEqual(
                            parse_varint_field(gamers[0], 17),
                            0,
                        )
                        continuing = parse_bytes_field(gamers[0], 19) or b""
                        self.assertEqual(parse_varint_field(continuing, 4), 1)
                        self.assertEqual(
                            parse_varint_field(continuing, 2),
                            400 if index == 523 else 1100,
                        )
                        # The first event is the cartridge; the last event
                        # carries the UI continuation fields.
                        final = parse_bytes_fields(result, 4)[-1]
                        final_source = parse_bytes_field(final, 1) or b""
                        self.assertEqual(parse_varint_field(final_source, 53), 1)
                        gun = parse_bytes_field(gamers[0], 7) or b""
                        self.assertEqual(
                            parse_varint_field(parse_bytes_fields(gun, 2)[0], 2),
                            expected_fake,
                        )
                        # A continuing blank self-shot must not look like a new
                        # operator/round to the client: that notification resets
                        # aim and prematurely returns the HUD to Fire. Real ammo
                        # remains, so auto-reload is not due in either iteration.
                        with self.assertRaises(asyncio.TimeoutError):
                            await asyncio.wait_for(
                                read_frame(reader, "body"), timeout=0.02
                            )
                    writer.write(encode_frame(
                        3, 8, pb_varint(1, 1),
                        index=525, length_mode="body",
                    ))
                    await receive(3, 8, 525)
                    collected = await receive(255, 2)
                    collected_result = parse_bytes_field(collected, 1) or b""
                    self.assertEqual(parse_varint_field(collected_result, 1), 9)
                    bounty_event = parse_bytes_fields(collected_result, 4)[0]
                    source_outline = parse_bytes_field(bounty_event, 1) or b""
                    target_outline = parse_bytes_field(bounty_event, 2) or b""
                    self.assertEqual(
                        parse_varint_field(source_outline, 1),
                        parse_varint_field(target_outline, 1),
                    )
                    # The shipped client skips the source outline when both
                    # indexes match, so the wallet delta must be on target.
                    self.assertEqual(parse_bytes_fields(source_outline, 4), [])
                    coin_delta = parse_bytes_fields(target_outline, 4)
                    self.assertEqual(len(coin_delta), 1)
                    self.assertEqual(parse_varint_field(coin_delta[0], 1), 1100)
                    self.assertEqual(parse_varint_field(coin_delta[0], 2), 2)
                    self.assertEqual(parse_varint_field(target_outline, 16), 0)
                    self.assertEqual(parse_varint_field(target_outline, 53), 0)
                    collected_info = parse_bytes_field(collected, 2) or b""
                    collected_player = parse_bytes_fields(collected_info, 2)[0]
                    self.assertEqual(parse_varint_field(collected_player, 5), 11100)
                    self.assertEqual(
                        parse_varint_field(
                            parse_bytes_field(collected_player, 19) or b"", 2
                        ), 0,
                    )
            finally:
                if writer is not None:
                    writer.close()
                    await writer.wait_closed()
                listener.close()
                await listener.wait_closed()

        asyncio.run(run_exchange())

    def test_mode1_trio_last_blank_auto_reloads_and_accepts_next_shot(self) -> None:
        state = self._state({"selectedHero": 0})
        state._accounts = {}
        state._next_gid = 1000001
        state.pvp_port = 0

        async def run_exchange() -> None:
            listener = await asyncio.start_server(
                lambda reader, writer: serve_client(
                    reader, writer, state, "body", "pvp"
                ),
                "127.0.0.1", 0,
            )
            writer = None
            try:
                reader, writer = await asyncio.open_connection(
                    "127.0.0.1", listener.sockets[0].getsockname()[1]
                )

                async def receive(cmd: int, act: int, index: int = 0) -> bytes:
                    async with asyncio.timeout(3):
                        while True:
                            head, body, _ = await read_frame(reader, "body")
                            if (head.cmd, head.act, head.index) == (cmd, act, index):
                                return body

                writer.write(encode_frame(
                    3, 1, pb_bytes(2, "local-pvp:1:6:0:0"),
                    index=531, length_mode="body",
                ))
                await receive(3, 1, 531)
                writer.write(encode_frame(3, 14, b"", index=532, length_mode="body"))
                await receive(3, 14, 532)
                await receive(255, 1)
                with (
                    patch("server.random.randrange", return_value=0),
                    patch("server.PREPARE_SIGNAL_DELAY", 0.001),
                    patch("server.PLAYER_CONTINUE_SHOT_SETTLE", 0.002),
                ):
                    writer.write(encode_frame(
                        3, 3, pb_varint(1, 0), index=533, length_mode="body"
                    ))
                    await receive(3, 3, 533)
                    shot = await receive(255, 2)
                    shot_result = parse_bytes_field(shot, 1) or b""
                    shot_info = parse_bytes_field(shot, 2) or b""
                    shot_player = parse_bytes_fields(shot_info, 2)[0]
                    shot_gun = parse_bytes_field(shot_player, 7) or b""
                    self.assertEqual(
                        [parse_varint_field(ammo, 2)
                         for ammo in parse_bytes_fields(shot_gun, 2)],
                        [2, 2],
                    )
                    await asyncio.sleep(0.01)
                    writer.write(encode_frame(
                        3, 3, pb_varint(1, 0), index=534, length_mode="body"
                    ))
                    await receive(3, 3, 534)
                    next_shot = await receive(255, 2)
                    next_result = parse_bytes_field(next_shot, 1) or b""
                    next_event = parse_bytes_fields(next_result, 4)[0]
                    next_source = parse_bytes_field(next_event, 1) or b""
                    self.assertEqual(
                        parse_varint_field(
                            parse_bytes_field(next_source, 10) or b"", 1
                        ),
                        300,
                    )
            finally:
                if writer is not None:
                    writer.close()
                    await writer.wait_closed()
                listener.close()
                await listener.wait_closed()

        with (
            patch("protocol.pvp_gun_ammo_counts", return_value=(0, 1)),
            patch("server.pvp_gun_ammo_counts", return_value=(2, 2)),
        ):
            asyncio.run(run_exchange())

    def test_mode1_trio_last_real_reloads_with_blanks_remaining(self) -> None:
        state = self._state({"selectedHero": 0})
        state._accounts = {}
        state._next_gid = 1000001
        state.pvp_port = 0

        async def run_exchange() -> None:
            listener = await asyncio.start_server(
                lambda reader, writer: serve_client(
                    reader, writer, state, "body", "pvp"
                ),
                "127.0.0.1", 0,
            )
            writer = None
            try:
                reader, writer = await asyncio.open_connection(
                    "127.0.0.1", listener.sockets[0].getsockname()[1]
                )

                async def receive(cmd: int, act: int, index: int = 0) -> bytes:
                    async with asyncio.timeout(3):
                        while True:
                            head, body, _ = await read_frame(reader, "body")
                            if (head.cmd, head.act, head.index) == (cmd, act, index):
                                return body

                writer.write(encode_frame(
                    3, 1, pb_bytes(2, "local-pvp:1:6:0:0"),
                    index=541, length_mode="body",
                ))
                await receive(3, 1, 541)
                writer.write(encode_frame(3, 14, b"", index=542, length_mode="body"))
                await receive(3, 14, 542)
                await receive(255, 1)
                with patch("server.random.randrange", return_value=3):
                    writer.write(encode_frame(
                        3, 3, pb_varint(1, 0), index=543, length_mode="body"
                    ))
                    await receive(3, 3, 543)
                    shot = await receive(255, 2)
                shot_result = parse_bytes_field(shot, 1) or b""
                events = parse_bytes_fields(shot_result, 4)
                self.assertEqual(len(events), 3)
                first_source = parse_bytes_field(events[0], 1) or b""
                self.assertEqual(
                    [parse_varint_field(a, 2)
                     for a in parse_bytes_fields(first_source, 5)],
                    [3, 0],
                )
                reload_target = parse_bytes_field(events[1], 2) or b""
                self.assertEqual(parse_varint_field(reload_target, 9), 1)
                self.assertEqual(
                    [parse_varint_field(a, 2)
                     for a in parse_bytes_fields(reload_target, 5)],
                    [2, 2],
                )
                shot_info = parse_bytes_field(shot, 2) or b""
                shot_player = parse_bytes_fields(shot_info, 2)[0]
                gun = parse_bytes_field(shot_player, 7) or b""
                self.assertEqual(
                    [parse_varint_field(a, 2)
                     for a in parse_bytes_fields(gun, 2)],
                    [2, 2],
                )
            finally:
                if writer is not None:
                    writer.close()
                    await writer.wait_closed()
                listener.close()
                await listener.wait_closed()

        with (
            patch("protocol.pvp_gun_ammo_counts", return_value=(1, 3)),
            patch("server.pvp_gun_ammo_counts", return_value=(2, 2)),
        ):
            asyncio.run(run_exchange())

    def test_mode1_trio_turns_include_both_bots_and_return_piggybank_to_player(self) -> None:
        state = self._state({"selectedHero": 0})
        state._accounts = {}
        state._next_gid = 1000001
        state.pvp_port = 0

        async def run_exchange() -> None:
            listener = await asyncio.start_server(
                lambda reader, writer: serve_client(
                    reader, writer, state, "body", "pvp"
                ),
                "127.0.0.1",
                0,
            )
            writer = None
            try:
                port = listener.sockets[0].getsockname()[1]
                reader, writer = await asyncio.open_connection("127.0.0.1", port)

                async def receive(cmd: int, act: int, index: int = 0) -> tuple[object, bytes]:
                    async with asyncio.timeout(3):
                        while True:
                            head, body, _ = await read_frame(reader, "body")
                            if (head.cmd, head.act, head.index) == (cmd, act, index):
                                return head, body

                def request(cmd: int, act: int, body: bytes, index: int) -> None:
                    writer.write(
                        encode_frame(
                            cmd, act, body, index=index, length_mode="body"
                        )
                    )

                request(3, 1, pb_bytes(2, "local-pvp:1:6:0:34"), 431)
                _, login = await receive(3, 1, 431)
                pvp = parse_bytes_field(login, 2) or b""
                initial_gamers = parse_bytes_fields(pvp, 2)
                self.assertEqual(len(initial_gamers), 3)
                self.assertEqual(
                    parse_varint_field(
                        parse_bytes_field(initial_gamers[0], 18) or b"", 7
                    ),
                    2,
                )
                request(3, 14, b"", 432)
                await receive(3, 14, 432)
                await receive(255, 1)

                request(
                    3, 5,
                    pb_varint(1, 10_000) + pb_varint(2, -1) + pb_varint(4, 4),
                    434,
                )
                ack, _ = await receive(3, 5, 434)
                self.assertEqual(ack.error, 0)
                _, notification = await receive(255, 2)
                shop_info = parse_bytes_field(notification, 2) or b""
                wet_offer = next(
                    card for card in parse_bytes_fields(shop_info, 7)
                    if parse_varint_field(card, 2) == 2011
                )
                wet_id = parse_varint_field(wet_offer, 1) or 0
                with patch("server.random.randint", return_value=2):
                    request(
                        3, 5,
                        pb_varint(1, wet_id) + pb_varint(2, 0)
                        + pb_varint(4, 1),
                        435,
                    )
                    ack, _ = await receive(3, 5, 435)
                    self.assertEqual(ack.error, 0)
                    _, notification = await receive(255, 2)
                sold_info = parse_bytes_field(notification, 2) or b""
                self.assertIn(
                    2,
                    [parse_varint_field(card, 5)
                     for card in parse_bytes_fields(sold_info, 7)],
                )

                with (
                    patch("server.random.randrange", side_effect=(2, 0, 0)),
                    patch("server.PREPARE_SIGNAL_DELAY", 0.001),
                    patch("server.PLAYER_OTHER_SHOT_SETTLE", 0.006),
                    patch("server.BOT_SHOT_SETTLE", 0.006),
                    patch("server.BOT_THINK_DELAY", 0.005),
                    patch("server.BOT_RAISE_GUN_DELAY", 0.001),
                    patch("server.BOT_SELECT_TARGET_DELAY", 0.001),
                ):
                    request(3, 3, pb_varint(1, 2), 433)
                    await receive(3, 3, 433)
                    shoot_sources: list[int] = []
                    shoot_targets: list[int] = []
                    behavior_order: list[tuple[int, int]] = []
                    turn_order: list[tuple[int, int, int]] = []
                    turn_skill_cd: list[int] = []
                    first_bot_shop: list[bytes] | None = None
                    round_start: tuple[bytes, bytes] | None = None
                    async with asyncio.timeout(3):
                        while round_start is None:
                            head, body, _ = await read_frame(reader, "body")
                            if (head.cmd, head.act) == (255, 1):
                                gamer = parse_bytes_field(body, 1) or b""
                                info = parse_bytes_field(body, 3) or b""
                                turn_order.append(
                                    (
                                        parse_varint_field(gamer, 3) or 0,
                                        parse_varint_field(info, 4) or 0,
                                        parse_varint_field(info, 10) or 0,
                                    )
                                )
                                turn_skill_cd.append(pvp_gamer_skill_cd(gamer))
                                if first_bot_shop is None:
                                    first_bot_shop = parse_bytes_fields(info, 7)
                            elif (head.cmd, head.act) == (255, 4):
                                behavior_order.append(
                                    (
                                        parse_varint_field(body, 1) or 0,
                                        parse_varint_field(body, 2) or 0,
                                    )
                                )
                            elif (head.cmd, head.act) == (255, 2):
                                result = parse_bytes_field(body, 1) or b""
                                event_type = parse_varint_field(result, 1) or 0
                                if event_type == 1:
                                    shoot_sources.append(
                                        parse_varint_field(result, 3) or 0
                                    )
                                    shoot_targets.append(
                                        parse_varint_field(result, 10) or 0
                                    )
                                elif event_type == 12:
                                    round_start = (result, body)

                self.assertEqual(shoot_sources, [0, 1, 2])
                self.assertEqual(shoot_targets, [2, 0, 0])
                self.assertEqual(
                    behavior_order,
                    [(1, 1), (1, 4), (2, 1), (2, 4)],
                )
                self.assertEqual(
                    [actor for actor, _, _ in turn_order],
                    [1, 1, 2, 2, 0, 0],
                )
                self.assertEqual(turn_skill_cd, [2, 2, 2, 2, 1, 1])
                self.assertIsNotNone(first_bot_shop)
                # The lab pool now contains every reconstructed card, so a
                # sold slot is replaced by any previously absent cfg rather
                # than a hard-coded five-card rotation.
                first_cfgs = [parse_varint_field(card, 2) for card in first_bot_shop]
                self.assertEqual(first_cfgs[:3], [2003, 2004, 2008])
                self.assertNotIn(first_cfgs[3], first_cfgs[:3])
                self.assertTrue(all(
                    parse_varint_field(card, 5) == 1
                    for card in first_bot_shop
                ))
                self.assertEqual(
                    [round_number for _, round_number, _ in turn_order],
                    [1, 1, 1, 1, 2, 2],
                )
                result, notification = round_start
                self.assertEqual(parse_varint_field(result, 1), 12)
                updated_pvp = parse_bytes_field(notification, 2) or b""
                updated_gamers = parse_bytes_fields(updated_pvp, 2)
                self.assertEqual(len(updated_gamers), 3)
                self.assertEqual(
                    [parse_varint_field(gamer, 4) for gamer in updated_gamers],
                    [4, 4, 3],
                )
                updated_slot = parse_bytes_field(updated_gamers[0], 18) or b""
                self.assertEqual(parse_varint_field(updated_slot, 7), 4)
                self.assertEqual(parse_varint_field(updated_pvp, 4), 2)
                self.assertEqual(parse_varint_field(updated_pvp, 10), 0)
            finally:
                if writer is not None:
                    writer.close()
                    await writer.wait_closed()
                listener.close()
                await listener.wait_closed()

        asyncio.run(run_exchange())

    def test_mode1_trio_finishes_bot_elimination_after_local_player_dies(self) -> None:
        state = self._state({"selectedHero": 0})
        state._accounts = {}
        state._next_gid = 1000001
        state.pvp_port = 0

        async def run_exchange() -> None:
            listener = await asyncio.start_server(
                lambda reader, writer: serve_client(
                    reader, writer, state, "body", "pvp"
                ),
                "127.0.0.1",
                0,
            )
            writer = None
            # Keep the elimination test independent of the active gun's
            # capacity: it needs four live self-shots before the bots finish.
            server_ammo_patch = patch("server.pvp_gun_ammo_counts", return_value=(4, 2))
            protocol_ammo_patch = patch("protocol.pvp_gun_ammo_counts", return_value=(4, 2))
            server_ammo_patch.start()
            protocol_ammo_patch.start()
            try:
                port = listener.sockets[0].getsockname()[1]
                reader, writer = await asyncio.open_connection("127.0.0.1", port)

                async def receive(cmd: int, act: int, index: int = 0) -> tuple[object, bytes]:
                    async with asyncio.timeout(3):
                        while True:
                            head, body, _ = await read_frame(reader, "body")
                            if (head.cmd, head.act, head.index) == (cmd, act, index):
                                return head, body

                def request(cmd: int, act: int, body: bytes, index: int) -> None:
                    writer.write(
                        encode_frame(
                            cmd, act, body, index=index, length_mode="body"
                        )
                    )

                request(3, 1, pb_bytes(2, "local-pvp:1:6:0:0"), 441)
                await receive(3, 1, 441)
                request(3, 14, b"", 442)
                await receive(3, 14, 442)
                await receive(255, 1)

                random_values = [2, 0, 0, 2, 0, 0, 2] + [0] * 12
                with (
                    patch("server.random.randrange", side_effect=random_values),
                    patch("server.PREPARE_SIGNAL_DELAY", 0.0),
                    patch("server.PLAYER_SELF_SHOT_SETTLE", 0.0),
                    patch("server.BOT_SHOT_SETTLE", 0.0),
                    patch("server.BOT_THINK_DELAY", 0.0),
                    patch("server.BOT_SPECTATOR_SHOT_SETTLE", 0.0),
                    patch("server.BOT_SPECTATOR_THINK_DELAY", 0.0),
                    patch("server.BOT_RAISE_GUN_DELAY", 0.0),
                    patch("server.BOT_SELECT_TARGET_DELAY", 0.0),
                ):
                    for shot_number in (1, 2):
                        request(3, 3, pb_varint(1, 0), 442 + shot_number)
                        await receive(3, 3, 442 + shot_number)
                        expected_round = shot_number + 1
                        while True:
                            head, body = await receive_any(reader)
                            if (head.cmd, head.act) != (255, 1):
                                continue
                            info = parse_bytes_field(body, 3) or b""
                            if (
                                (parse_varint_field(info, 10) or 0) == 0
                                and (parse_varint_field(info, 4) or 0) == expected_round
                            ):
                                break

                    request(3, 3, pb_varint(1, 0), 445)
                    await receive(3, 3, 445)
                    player_died = False
                    end_info = b""
                    async with asyncio.timeout(3):
                        while not end_info:
                            head, body, _ = await read_frame(reader, "body")
                            if (head.cmd, head.act) == (255, 15):
                                player_died = True
                            elif (head.cmd, head.act) == (255, 5):
                                end_info = parse_bytes_field(body, 1) or b""

                self.assertTrue(player_died)
                self.assertTrue(end_info)
                self.assertEqual(parse_varint_field(end_info, 9), 4)
                self.assertEqual(parse_varint_field(end_info, 25), 1)
                final_gamers = parse_bytes_fields(end_info, 2)
                self.assertEqual(len(final_gamers), 3)
                self.assertEqual(
                    [parse_varint_field(gamer, 14) for gamer in final_gamers],
                    [3, 2, 1],
                )
                self.assertEqual(parse_varint_field(final_gamers[0], 12), 1)
                self.assertEqual(parse_varint_field(final_gamers[1], 12), 1)
                self.assertNotEqual(parse_varint_field(final_gamers[2], 12), 1)
            finally:
                protocol_ammo_patch.stop()
                server_ammo_patch.stop()
                if writer is not None:
                    writer.close()
                    await writer.wait_closed()
                listener.close()
                await listener.wait_closed()

        async def receive_any(
            reader: asyncio.StreamReader,
        ) -> tuple[object, bytes]:
            async with asyncio.timeout(3):
                head, body, _ = await read_frame(reader, "body")
                return head, body

        asyncio.run(run_exchange())

    def test_mode1_trio_hp_zero_player_survives_while_frenzy_remains(self) -> None:
        state = self._state({"selectedHero": 0})
        state._accounts = {}
        state._next_gid = 1000001
        state.pvp_port = 0

        def login_with_player_on_last_hp(*args, **kwargs):
            login, info, player, bot = pvp_login_snapshot(*args, **kwargs)
            player = pvp_gamer_with_state(
                player,
                hp=1,
                ammo_number=4,
                fake_ammo_number=2,
                round_number=1,
                is_dead=False,
                virtual_hp=2,
            )
            room_gamers = parse_bytes_fields(info, 2)
            info = pvp_info_with_state(
                info,
                player,
                bot,
                round_number=1,
                turn_number=1,
                current_index=0,
                additional_gamers=(room_gamers[2],),
            )
            gid = parse_varint_field(login, 1) or 0
            login = pb_message(pb_varint(1, gid), pb_bytes(2, info), pb_varint(3, 0))
            return login, info, player, bot

        async def run_exchange() -> None:
            listener = await asyncio.start_server(
                lambda reader, writer: serve_client(
                    reader, writer, state, "body", "pvp"
                ),
                "127.0.0.1",
                0,
            )
            writer = None
            try:
                reader, writer = await asyncio.open_connection(
                    "127.0.0.1", listener.sockets[0].getsockname()[1]
                )

                async def receive(cmd: int, act: int, index: int = 0) -> bytes:
                    async with asyncio.timeout(4):
                        while True:
                            head, body, _ = await read_frame(reader, "body")
                            if (head.cmd, head.act, head.index) == (cmd, act, index):
                                return body

                async def receive_shot_from(source_index: int) -> bytes:
                    seen = []
                    try:
                        async with asyncio.timeout(4):
                            while True:
                                head, body, _ = await read_frame(reader, "body")
                                result = parse_bytes_field(body, 1) or b""
                                note = (head.cmd, head.act,
                                        parse_varint_field(result, 1),
                                        parse_varint_field(result, 3))
                                if (head.cmd, head.act) == (255, 1):
                                    info = parse_bytes_field(body, 3) or b""
                                    note += (parse_varint_field(info, 10), tuple(
                                        (
                                            parse_varint_field(gamer, 4),
                                            parse_varint_field(gamer, 17),
                                            tuple(
                                                (parse_varint_field(ammo, 1),
                                                 parse_varint_field(ammo, 2))
                                                for ammo in parse_bytes_fields(
                                                    parse_bytes_field(gamer, 7) or b"", 2
                                                )
                                            ),
                                        ) for gamer in parse_bytes_fields(info, 2)
                                    ))
                                seen.append(note)
                                if (
                                    (head.cmd, head.act) == (255, 2)
                                    and parse_varint_field(result, 1) == 1
                                    and parse_varint_field(result, 3) == source_index
                                ):
                                    return body
                    except TimeoutError as exc:
                        raise AssertionError(f"missing shot from {source_index}; received={seen}") from exc

                writer.write(encode_frame(
                    3, 1, pb_bytes(2, "local-pvp:1:6:0:0"),
                    index=811, length_mode="body",
                ))
                await receive(3, 1, 811)
                writer.write(encode_frame(3, 14, b"", index=812, length_mode="body"))
                await receive(3, 14, 812)
                await receive(255, 1)

                writer.write(encode_frame(
                    3, 3, pb_varint(1, 0), index=813, length_mode="body"
                ))
                await receive(3, 3, 813)
                player_shot = await receive_shot_from(0)
                player_shot_info = parse_bytes_field(player_shot, 2) or b""
                player_after_shot = parse_bytes_fields(player_shot_info, 2)[0]
                self.assertEqual(parse_varint_field(player_after_shot, 4), 0)
                self.assertEqual(parse_varint_field(player_after_shot, 17), 2)
                self.assertNotEqual(parse_varint_field(player_after_shot, 12), 1)
                shot_result = parse_bytes_field(player_shot, 1) or b""
                self.assertIsNone(parse_varint_field(shot_result, 16))
            finally:
                if writer is not None:
                    writer.close()
                    await writer.wait_closed()
                listener.close()
                await listener.wait_closed()

        deterministic_draw_count = [0]

        def deterministic_ammo_roll(stop: int) -> int:
            # The player's first self-shot must be real for this regression.
            # Thereafter, choose a valid blank index whenever one is present,
            # so bots cannot enter an all-real Frenzy stalemate.
            result = stop - 1 if deterministic_draw_count[0] == 0 else 0
            deterministic_draw_count[0] += 1
            return result

        with (
            patch("server.pvp_login_snapshot", side_effect=login_with_player_on_last_hp),
            patch("server.random.randrange", side_effect=deterministic_ammo_roll),
            patch("server.PVP_OPENING_SEQUENCE_DELAY", 0.001),
            patch("server.PREPARE_SIGNAL_DELAY", 0.0),
            patch("server.BOT_RAISE_GUN_DELAY", 0.0),
            patch("server.BOT_SELECT_TARGET_DELAY", 0.0),
            patch("server.BOT_THINK_DELAY", 0.0),
            patch("server.BOT_SHOT_SETTLE", 0.0),
        ):
            asyncio.run(run_exchange())

    def test_mode1_trio_fake_shot_that_zeros_player_frenzy_marks_source_dead(self) -> None:
        state = self._state({"selectedHero": 0})
        state._accounts = {}
        state._next_gid = 1000001
        state.pvp_port = 0

        def login_with_player_on_last_frenzy(*args, **kwargs):
            login, info, player, bot = pvp_login_snapshot(*args, **kwargs)
            player = pvp_gamer_with_state(
                player,
                hp=0,
                ammo_number=4,
                fake_ammo_number=2,
                round_number=1,
                is_dead=False,
                virtual_hp=1,
            )
            room_gamers = parse_bytes_fields(info, 2)
            bot = pvp_gamer_with_state(
                bot,
                hp=1,
                ammo_number=4,
                fake_ammo_number=2,
                round_number=1,
                is_dead=False,
                virtual_hp=0,
            )
            extra_bot = pvp_gamer_with_state(
                room_gamers[2],
                hp=1,
                ammo_number=4,
                fake_ammo_number=2,
                round_number=1,
                is_dead=False,
                virtual_hp=0,
            )
            info = pvp_info_with_state(
                info,
                player,
                bot,
                round_number=1,
                turn_number=1,
                current_index=0,
                additional_gamers=(extra_bot,),
            )
            gid = parse_varint_field(login, 1) or 0
            login = pb_message(pb_varint(1, gid), pb_bytes(2, info), pb_varint(3, 0))
            return login, info, player, bot

        async def run_exchange() -> None:
            listener = await asyncio.start_server(
                lambda reader, writer: serve_client(
                    reader, writer, state, "body", "pvp"
                ),
                "127.0.0.1",
                0,
            )
            writer = None
            try:
                reader, writer = await asyncio.open_connection(
                    "127.0.0.1", listener.sockets[0].getsockname()[1]
                )

                async def receive(cmd: int, act: int, index: int = 0) -> bytes:
                    async with asyncio.timeout(3):
                        while True:
                            head, body, _ = await read_frame(reader, "body")
                            if (head.cmd, head.act, head.index) == (cmd, act, index):
                                return body

                writer.write(encode_frame(
                    3, 1, pb_bytes(2, "local-pvp:1:6:0:0"),
                    index=901, length_mode="body",
                ))
                await receive(3, 1, 901)
                writer.write(encode_frame(3, 14, b"", index=902, length_mode="body"))
                await receive(3, 14, 902)
                await receive(255, 1)

                writer.write(encode_frame(
                    3, 3, pb_varint(1, 1), index=903, length_mode="body"
                ))
                await receive(3, 3, 903)
                shot_body = b""
                async with asyncio.timeout(3):
                    while not shot_body:
                        head, body, _ = await read_frame(reader, "body")
                        if (head.cmd, head.act) == (255, 2):
                            result = parse_bytes_field(body, 1) or b""
                            if (
                                parse_varint_field(result, 1) == 1
                                and parse_varint_field(result, 3) == 0
                            ):
                                shot_body = body

                result = parse_bytes_field(shot_body, 1) or b""
                shot_events = parse_bytes_fields(result, 4)
                death_event = next(
                    event for event in shot_events
                    if parse_varint_field(
                        parse_bytes_field(event, 2) or b"", 9
                    ) == PVP_UPDATE_GAMER_DEAD_STATUS_EVENT
                )
                death_target = parse_bytes_field(death_event, 2) or b""
                self.assertEqual(parse_varint_field(death_target, 1), 0)
                info = parse_bytes_field(shot_body, 2) or b""
                dead_player = parse_bytes_fields(info, 2)[0]
                self.assertEqual(parse_varint_field(dead_player, 12), 1)
            finally:
                if writer is not None:
                    writer.close()
                    await writer.wait_closed()
                listener.close()
                await listener.wait_closed()

        draw_count = [0]

        def fake_player_shot_then_live_bot_draws(real: int, fake: int) -> int:
            draw_count[0] += 1
            return 300 if draw_count[0] == 1 else 1

        with (
            patch("server.pvp_login_snapshot", side_effect=login_with_player_on_last_frenzy),
            patch(
                "server._draw_ejected_ammo",
                side_effect=fake_player_shot_then_live_bot_draws,
            ),
            patch("server.PVP_OPENING_SEQUENCE_DELAY", 0.001),
            patch("server.PREPARE_SIGNAL_DELAY", 0.0),
            patch("server.PLAYER_OTHER_SHOT_SETTLE", 0.0),
        ):
            asyncio.run(run_exchange())

    def test_mode1_submode6_tcp_store_card_and_refresh_shop_events(self) -> None:
        state = self._state({"selectedHero": 0})
        state._accounts = {}
        state._next_gid = 1000001
        state.pvp_port = 0

        async def run_exchange() -> None:
            listener = await asyncio.start_server(
                lambda reader, writer: serve_client(
                    reader, writer, state, "body", "pvp"
                ),
                "127.0.0.1",
                0,
            )
            writer = None
            try:
                port = listener.sockets[0].getsockname()[1]
                reader, writer = await asyncio.open_connection("127.0.0.1", port)

                async def receive(cmd: int, act: int, index: int = 0) -> tuple[object, bytes]:
                    async with asyncio.timeout(3):
                        while True:
                            head, body, _ = await read_frame(reader, "body")
                            if (head.cmd, head.act, head.index) == (cmd, act, index):
                                return head, body

                def request(cmd: int, act: int, body: bytes, index: int) -> None:
                    writer.write(encode_frame(
                        cmd, act, body, index=index, length_mode="body"
                    ))

                request(3, 1, pb_bytes(2, "local-pvp:1:6:0:0"), 301)
                await receive(3, 1, 301)
                request(3, 14, b"", 302)
                await receive(3, 14, 302)
                await receive(255, 1)

                # Typ_Buy stores the selected offer. The server sends the
                # action ack first, then the coin and card-slot event.
                request(3, 5, pb_varint(1, 1) + pb_varint(4, 3), 303)
                ack, _ = await receive(3, 5, 303)
                self.assertEqual(ack.error, 0)
                _, notification = await receive(255, 2)
                result = parse_bytes_field(notification, 1) or b""
                self.assertEqual(parse_varint_field(result, 1), 2)
                self.assertEqual(parse_varint_field(result, 6), 1)
                self.assertEqual(parse_varint_field(parse_bytes_field(result, 15) or b"", 2), 2001)
                buy_events = parse_bytes_fields(result, 4)
                self.assertEqual(len(buy_events), 2)
                coin_target = parse_bytes_field(buy_events[0], 2) or b""
                coin_change = parse_bytes_field(coin_target, 4) or b""
                encoded_delta = parse_varint_field(coin_change, 1)
                self.assertEqual(encoded_delta, (-100) & ((1 << 64) - 1))
                self.assertEqual(parse_varint_field(coin_change, 2), 5)
                slot_target = parse_bytes_field(buy_events[1], 2) or b""
                self.assertEqual(parse_varint_field(slot_target, 9), 6)
                slot_card = parse_bytes_field(slot_target, 13) or b""
                self.assertEqual(parse_varint_field(slot_card, 1), 1)
                self.assertEqual(parse_varint_field(slot_card, 2), 2001)
                self.assertEqual(
                    parse_varint_field(slot_card, 7),
                    (-1) & ((1 << 64) - 1),
                )
                self.assertEqual(parse_varint_field(slot_target, 48), 1)
                bought_pvp = parse_bytes_field(notification, 2) or b""
                bought_player = parse_bytes_fields(bought_pvp, 2)[0]
                self.assertEqual(parse_varint_field(bought_player, 5), 9_900)
                bought_slot = parse_bytes_field(bought_player, 18) or b""
                self.assertEqual(parse_varint_field(bought_slot, 2), 2001)
                self.assertEqual(
                    parse_varint_field(bought_slot, 7),
                    (-1) & ((1 << 64) - 1),
                )
                self.assertEqual(
                    [parse_varint_field(card, 5) for card in parse_bytes_fields(bought_pvp, 7)],
                    [2, 1, 1, 1],
                )

                # A second store purchase replaces a normal stored card; it
                # must not surface the generic server/database error.
                request(3, 5, pb_varint(1, 4) + pb_varint(4, 3), 305)
                ack, _ = await receive(3, 5, 305)
                self.assertEqual(ack.error, 0)
                _, notification = await receive(255, 2)
                result = parse_bytes_field(notification, 1) or b""
                self.assertEqual(parse_varint_field(result, 1), 2)
                self.assertEqual(parse_varint_field(result, 6), 4)
                self.assertEqual(
                    parse_varint_field(parse_bytes_field(result, 15) or b"", 2),
                    2008,
                )
                replaced_pvp = parse_bytes_field(notification, 2) or b""
                replaced_player = parse_bytes_fields(replaced_pvp, 2)[0]
                self.assertEqual(parse_varint_field(replaced_player, 5), 9_700)
                replaced_slot = parse_bytes_field(replaced_player, 18) or b""
                self.assertEqual(parse_varint_field(replaced_slot, 1), 4)
                self.assertEqual(parse_varint_field(replaced_slot, 2), 2008)
                self.assertEqual(
                    parse_varint_field(replaced_slot, 7),
                    (-1) & ((1 << 64) - 1),
                )

                # The refresh packet uses its own event type, emits the new
                # stock on Enum_Gamer_Refresh_Shop, and subtracts the shipped
                # round-one refresh cost without clearing the replaced card.
                request(
                    3,
                    5,
                    pb_varint(1, 10_000) + pb_varint(2, -1) + pb_varint(4, 4),
                    304,
                )
                ack, _ = await receive(3, 5, 304)
                self.assertEqual(ack.error, 0)
                _, notification = await receive(255, 2)
                result = parse_bytes_field(notification, 1) or b""
                self.assertEqual(parse_varint_field(result, 1), 11)
                refresh_events = parse_bytes_fields(result, 4)
                self.assertEqual(len(refresh_events), 2)
                coin_target = parse_bytes_field(refresh_events[0], 2) or b""
                self.assertEqual(parse_varint_field(coin_target, 9), 10)
                coin_change = parse_bytes_field(coin_target, 4) or b""
                self.assertEqual(
                    parse_varint_field(coin_change, 1),
                    (-300) & ((1 << 64) - 1),
                )
                stock_target = parse_bytes_field(refresh_events[1], 2) or b""
                self.assertEqual(parse_varint_field(stock_target, 9), 83)
                refreshed = parse_bytes_fields(stock_target, 42)
                self.assertEqual(len(refreshed), 4)
                self.assertEqual(parse_bytes_fields(stock_target, 32), [])
                self.assertNotEqual(
                    [parse_varint_field(card, 2) for card in refreshed],
                    [2001, 2003, 2004, 2008],
                )
                final_pvp = parse_bytes_field(notification, 2) or b""
                final_player = parse_bytes_fields(final_pvp, 2)[0]
                self.assertEqual(parse_varint_field(final_player, 5), 9_400)
                self.assertEqual(
                    parse_varint_field(parse_bytes_field(final_player, 18) or b"", 2),
                    2008,
                )
                self.assertEqual(len(parse_bytes_fields(final_pvp, 2)), 3)

                # A client that has consumed the refresh event can buy one of
                # its newly advertised IDs and replace the stored item without
                # receiving the generic database error.
                request(3, 5, pb_varint(1, 8) + pb_varint(4, 3), 305)
                ack, _ = await receive(3, 5, 305)
                self.assertEqual(ack.error, 0)
                _, notification = await receive(255, 2)
                result = parse_bytes_field(notification, 1) or b""
                self.assertEqual(parse_varint_field(result, 1), 2)
                self.assertEqual(parse_varint_field(result, 6), 8)
                self.assertEqual(
                    parse_varint_field(parse_bytes_field(result, 15) or b"", 2),
                    2011,
                )
                final_pvp = parse_bytes_field(notification, 2) or b""
                final_player = parse_bytes_fields(final_pvp, 2)[0]
                self.assertEqual(parse_varint_field(final_player, 5), 9_200)
                self.assertEqual(
                    parse_varint_field(parse_bytes_field(final_player, 18) or b"", 2),
                    2011,
                )

                # A stored lucky card must send the die result through the
                # client's Enum_Update_Luck path, then clear the saved slot.
                with patch("server.random.randint", return_value=5):
                    request(
                        3, 5,
                        pb_varint(1, 8) + pb_varint(2, 0) + pb_varint(4, 2),
                        306,
                    )
                    ack, _ = await receive(3, 5, 306)
                    self.assertEqual(ack.error, 0)
                    _, notification = await receive(255, 2)
                result = parse_bytes_field(notification, 1) or b""
                self.assertEqual(parse_varint_field(result, 1), 8)
                self.assertEqual(parse_varint_field(result, 2), 1010)
                luck_events = parse_bytes_fields(result, 4)
                self.assertEqual(len(luck_events), 2)  # full HP: no heal
                luck_target = parse_bytes_field(luck_events[1], 2) or b""
                self.assertEqual(parse_varint_field(luck_target, 9), 7)
                luck = parse_bytes_field(luck_target, 22) or b""
                self.assertEqual(parse_varint_field(luck, 1), 5)
                self.assertEqual(parse_varint_field(luck, 3), 1)
                used_pvp = parse_bytes_field(notification, 2) or b""
                used_player = parse_bytes_fields(used_pvp, 2)[0]
                self.assertEqual(
                    parse_varint_field(parse_bytes_field(used_player, 18) or b"", 1),
                    0,
                )

                with patch(
                    "server.random.sample",
                    side_effect=lambda seq, count: list(seq)[1:5],
                ):
                    request(
                        3, 5,
                        pb_varint(1, 10_000) + pb_varint(2, -1) + pb_varint(4, 4),
                        307,
                    )
                    ack, _ = await receive(3, 5, 307)
                    self.assertEqual(ack.error, 0)
                    _, notification = await receive(255, 2)
                refreshed_pvp = parse_bytes_field(notification, 2) or b""
                wet_offer = next(
                    card for card in parse_bytes_fields(refreshed_pvp, 7)
                    if parse_varint_field(card, 2) == 2011
                )
                wet_card_id = parse_varint_field(wet_offer, 1) or 0
                with patch("server.random.randint", return_value=2):
                    request(
                        3, 5,
                        pb_varint(1, wet_card_id)
                        + pb_varint(2, 0)
                        + pb_varint(4, 1),
                        308,
                    )
                    ack, _ = await receive(3, 5, 308)
                    self.assertEqual(ack.error, 0)
                    _, notification = await receive(255, 2)
                result = parse_bytes_field(notification, 1) or b""
                self.assertEqual(parse_varint_field(result, 1), 7)
                luck_target = parse_bytes_field(
                    parse_bytes_fields(result, 4)[1], 2
                ) or b""
                luck = parse_bytes_field(luck_target, 22) or b""
                self.assertEqual(parse_varint_field(luck, 1), 2)
                self.assertEqual(parse_varint_field(luck, 3), 0)
            finally:
                if writer is not None:
                    writer.close()
                    await writer.wait_closed()
                listener.close()
                await listener.wait_closed()

        asyncio.run(run_exchange())

    def test_mode1_hallucinogen_use_consumes_slot_and_forces_enemy_self_shot(self) -> None:
        state = self._state({"selectedHero": 0})
        state._accounts = {}
        state._next_gid = 1000001
        state.pvp_port = 0

        async def run_exchange() -> None:
            listener = await asyncio.start_server(
                lambda reader, writer: serve_client(
                    reader, writer, state, "body", "pvp"
                ),
                "127.0.0.1",
                0,
            )
            writer = None
            try:
                reader, writer = await asyncio.open_connection(
                    "127.0.0.1", listener.sockets[0].getsockname()[1]
                )

                async def receive(cmd: int, act: int, index: int = 0) -> tuple[object, bytes]:
                    async with asyncio.timeout(4):
                        while True:
                            head, body, _ = await read_frame(reader, "body")
                            if (head.cmd, head.act, head.index) == (cmd, act, index):
                                return head, body

                def request(cmd: int, act: int, body: bytes, index: int) -> None:
                    writer.write(
                        encode_frame(
                            cmd, act, body, index=index, length_mode="body"
                        )
                    )

                request(3, 1, pb_bytes(2, "local-pvp:1:6:0:0"), 351)
                await receive(3, 1, 351)
                request(3, 14, b"", 352)
                await receive(3, 14, 352)
                await receive(255, 1)

                # Offer 4 is the shipped Hallucinogen cfg 2008.
                request(3, 5, pb_varint(1, 4) + pb_varint(4, 3), 353)
                ack, _ = await receive(3, 5, 353)
                self.assertEqual(ack.error, 0)
                await receive(255, 2)

                # Type_Use consumes card instance 4 and targets the living
                # enemy at index 1. Pin roll 2 to the real bullet branch.
                with patch("server.random.randrange", return_value=2):
                    request(
                        3,
                        5,
                        pb_varint(1, 4) + pb_varint(2, 1) + pb_varint(4, 2),
                        354,
                    )
                    ack, _ = await receive(3, 5, 354)
                    self.assertEqual(ack.error, 0)
                    _, use_notification = await receive(255, 2)

                use_result = parse_bytes_field(use_notification, 1) or b""
                self.assertEqual(parse_varint_field(use_result, 1), 8)
                self.assertEqual(parse_varint_field(use_result, 2), 1007)
                self.assertEqual(parse_varint_field(use_result, 5), 2008)
                self.assertEqual(parse_varint_field(use_result, 6), 4)
                self.assertEqual(parse_varint_field(use_result, 10), 1)
                used_card = parse_bytes_field(use_result, 15) or b""
                self.assertEqual(
                    parse_varint_field(used_card, 7),
                    (-1) & ((1 << 64) - 1),
                )
                use_events = parse_bytes_fields(use_result, 4)
                self.assertEqual(len(use_events), 3)
                clear_target = parse_bytes_field(use_events[0], 2) or b""
                clear_source = parse_bytes_field(use_events[0], 1) or b""
                self.assertEqual(parse_varint_field(clear_source, 9), 6)
                self.assertEqual(parse_varint_field(clear_target, 9), 6)
                self.assertEqual(parse_varint_field(clear_target, 48), 2)
                shoot_target = parse_bytes_field(use_events[1], 2) or b""
                self.assertEqual(parse_varint_field(shoot_target, 1), 1)
                self.assertEqual(
                    parse_varint_field(shoot_target, 2),
                    (-1) & ((1 << 64) - 1),
                )
                self.assertEqual(parse_varint_field(shoot_target, 9), 2)
                final_target = parse_bytes_field(use_events[2], 2) or b""
                self.assertEqual(parse_varint_field(final_target, 9), 3)
                self.assertEqual(parse_varint_field(use_result, 7), 1)
                use_info = parse_bytes_field(use_notification, 2) or b""
                use_gamers = parse_bytes_fields(use_info, 2)
                use_player = use_gamers[0]
                self.assertEqual(parse_varint_field(use_player, 5), 9_800)
                self.assertEqual(
                    parse_varint_field(parse_bytes_field(use_player, 18) or b"", 2),
                    0,
                )
                self.assertEqual(parse_varint_field(use_gamers[1], 4), 3)
                bot_gun = parse_bytes_field(use_gamers[1], 7) or b""
                bot_ammo = parse_bytes_fields(bot_gun, 2)
                self.assertEqual(
                    [parse_varint_field(ammo, 1) for ammo in bot_ammo],
                    [300, 1],
                )
                self.assertEqual(
                    [parse_varint_field(ammo, 2) for ammo in bot_ammo],
                    [2, 1],
                )
                self.assertEqual(parse_varint_field(use_info, 10), 0)
            finally:
                if writer is not None:
                    writer.close()
                    await writer.wait_closed()
                listener.close()
                await listener.wait_closed()

        asyncio.run(run_exchange())

    def test_mode1_hallucinogen_shop_buy_use_is_one_authoritative_event(self) -> None:
        state = self._state({"selectedHero": 0})
        state._accounts = {}
        state._next_gid = 1000001
        state.pvp_port = 0

        async def run_exchange() -> None:
            listener = await asyncio.start_server(
                lambda reader, writer: serve_client(
                    reader, writer, state, "body", "pvp"
                ),
                "127.0.0.1",
                0,
            )
            writer = None
            try:
                reader, writer = await asyncio.open_connection(
                    "127.0.0.1", listener.sockets[0].getsockname()[1]
                )

                async def receive(
                    cmd: int, act: int, index: int = 0
                ) -> tuple[object, bytes]:
                    async with asyncio.timeout(4):
                        while True:
                            head, body, _ = await read_frame(reader, "body")
                            if (head.cmd, head.act, head.index) == (cmd, act, index):
                                return head, body

                def request(cmd: int, act: int, body: bytes, index: int) -> None:
                    writer.write(
                        encode_frame(
                            cmd, act, body, index=index, length_mode="body"
                        )
                    )

                request(3, 1, pb_bytes(2, "local-pvp:1:6:0:0"), 361)
                await receive(3, 1, 361)
                request(3, 14, b"", 362)
                await receive(3, 14, 362)
                await receive(255, 1)

                # Typ_Buy_And_Use (1): offer 4 is cfg 2008. This path must
                # debit the shop price but must not put the one-shot card in
                # the stored-card slot.
                request(
                    3,
                    5,
                    pb_varint(1, 4)
                    + pb_varint(2, 1)
                    + pb_varint(4, 1),
                    363,
                )
                with patch("server.random.randrange", return_value=2):
                    ack, _ = await receive(3, 5, 363)
                    self.assertEqual(ack.error, 0)
                    _, notification = await receive(255, 2)

                result = parse_bytes_field(notification, 1) or b""
                self.assertEqual(parse_varint_field(result, 1), 7)
                self.assertEqual(parse_varint_field(result, 5), 2008)
                self.assertEqual(parse_varint_field(result, 6), 4)
                self.assertEqual(parse_varint_field(result, 7), 1)
                events = parse_bytes_fields(result, 4)
                self.assertEqual(len(events), 3)
                coin_target = parse_bytes_field(events[0], 2) or b""
                coin_source = parse_bytes_field(events[0], 1) or b""
                self.assertEqual(parse_varint_field(coin_source, 9), 4)
                self.assertEqual(parse_varint_field(coin_target, 9), 4)
                coin_change = parse_bytes_field(coin_target, 4) or b""
                self.assertEqual(
                    parse_varint_field(coin_change, 1),
                    (-200) & ((1 << 64) - 1),
                )
                self.assertEqual(parse_varint_field(coin_change, 2), 5)
                self.assertEqual(
                    parse_varint_field(
                        parse_bytes_field(events[1], 2) or b"", 9
                    ),
                    2,
                )
                self.assertEqual(
                    parse_varint_field(
                        parse_bytes_field(events[2], 2) or b"", 9
                    ),
                    3,
                )

                pvp_info = parse_bytes_field(notification, 2) or b""
                gamers = parse_bytes_fields(pvp_info, 2)
                player_slot = parse_bytes_field(gamers[0], 18)
                self.assertTrue(
                    player_slot is None or parse_varint_field(player_slot, 1) == 0
                )
                self.assertEqual(parse_varint_field(gamers[0], 5), 9_800)
                self.assertEqual(parse_varint_field(gamers[1], 4), 3)
                bot_gun = parse_bytes_field(gamers[1], 7) or b""
                bot_ammo = parse_bytes_fields(bot_gun, 2)
                self.assertEqual(
                    [parse_varint_field(ammo, 2) for ammo in bot_ammo],
                    [2, 1],
                )
                offers = parse_bytes_fields(pvp_info, 7)
                self.assertEqual(parse_varint_field(offers[3], 5), 2)

                # No second top-level Type_Shoot should follow the card
                # notification; the shot is already embedded above.
                with self.assertRaises(TimeoutError):
                    async with asyncio.timeout(0.2):
                        await read_frame(reader, "body")
            finally:
                if writer is not None:
                    writer.close()
                    await writer.wait_closed()
                listener.close()
                await listener.wait_closed()

        asyncio.run(run_exchange())

    def test_mode1_maintenance_kit_uses_buff_and_normal_ammo_in_live_flow(self) -> None:
        state = self._state({"selectedHero": 0})
        state._accounts = {}
        state._next_gid = 1000001
        state.pvp_port = 0

        async def run_exchange() -> None:
            listener = await asyncio.start_server(
                lambda reader, writer: serve_client(
                    reader, writer, state, "body", "pvp"
                ),
                "127.0.0.1",
                0,
            )
            writer = None
            try:
                reader, writer = await asyncio.open_connection(
                    "127.0.0.1", listener.sockets[0].getsockname()[1]
                )

                async def receive(
                    cmd: int, act: int, index: int = 0
                ) -> tuple[object, bytes]:
                    async with asyncio.timeout(5):
                        while True:
                            head, body, _ = await read_frame(reader, "body")
                            if (head.cmd, head.act, head.index) == (cmd, act, index):
                                return head, body

                def request(cmd: int, act: int, body: bytes, index: int) -> None:
                    writer.write(encode_frame(
                        cmd, act, body, index=index, length_mode="body"
                    ))

                with patch(
                    "server._random_shop_specs",
                    return_value=((2001, 100), (2003, 200), (2004, 100), (2015, 300)),
                ):
                    request(3, 1, pb_bytes(2, "local-pvp:1:6:0:0"), 371)
                    await receive(3, 1, 371)
                    request(3, 14, b"", 372)
                    await receive(3, 14, 372)
                    await receive(255, 1)

                # Buy-and-use the fourth offer (Maintenance Kit), self-targeting
                # the buff. This checks the complete live handler, not only the
                # packet builder.
                request(
                    3,
                    5,
                    pb_varint(1, 4) + pb_varint(2, 0) + pb_varint(4, 1),
                    373,
                )
                ack, _ = await receive(3, 5, 373)
                self.assertEqual(ack.error, 0)
                _, use_notification = await receive(255, 2)
                use_result = parse_bytes_field(use_notification, 1) or b""
                self.assertEqual(parse_varint_field(use_result, 1), 7)
                self.assertEqual(parse_varint_field(use_result, 2), 1014)
                self.assertEqual(parse_varint_field(use_result, 5), 2015)
                use_events = parse_bytes_fields(use_result, 4)
                use_target = parse_bytes_field(use_events[-1], 2) or b""
                added = parse_bytes_fields(use_target, 25)
                self.assertEqual(
                    [parse_varint_field(buff, 1) for buff in added],
                    [MAINTENANCE_KIT_BUFF_CFG_ID],
                )
                use_pvp = parse_bytes_field(use_notification, 2) or b""
                player_before_shot = parse_bytes_fields(use_pvp, 2)[0]
                self.assertEqual(
                    [
                        parse_varint_field(buff, 1)
                        for buff in parse_bytes_fields(player_before_shot, 8)
                    ],
                    [MAINTENANCE_KIT_BUFF_CFG_ID],
                )

                # Refresh a second Kit into the shop while the first effect
                # is active. A second buy-and-use must return the shipped
                # non-stackable-effect error without selling it or charging
                # coins. A saved copy must likewise remain in the slot when
                # its use is rejected.
                with patch(
                    "server._random_shop_specs",
                    return_value=((2001, 100), (2003, 200), (2004, 100), (2015, 300)),
                ):
                    request(
                        3, 5,
                        pb_varint(1, 10_000) + pb_varint(2, -1) + pb_varint(4, 4),
                        375,
                    )
                    ack, _ = await receive(3, 5, 375)
                    self.assertEqual(ack.error, 0)
                    _, refresh_notification = await receive(255, 2)
                refresh_pvp = parse_bytes_field(refresh_notification, 2) or b""
                second_kit = next(
                    card for card in parse_bytes_fields(refresh_pvp, 7)
                    if parse_varint_field(card, 2) == 2015
                )
                second_kit_id = parse_varint_field(second_kit, 1) or 0
                self.assertEqual(
                    parse_varint_field(parse_bytes_fields(refresh_pvp, 2)[0], 5),
                    9_400,
                )
                request(
                    3, 5,
                    pb_varint(1, second_kit_id)
                    + pb_varint(2, 0)
                    + pb_varint(4, 1),
                    376,
                )
                rejected, _ = await receive(3, 5, 376)
                self.assertEqual(rejected.error, 352)

                request(
                    3, 5,
                    pb_varint(1, second_kit_id) + pb_varint(4, 3),
                    377,
                )
                stored_ack, _ = await receive(3, 5, 377)
                self.assertEqual(stored_ack.error, 0)
                _, stored_notification = await receive(255, 2)
                stored_pvp = parse_bytes_field(stored_notification, 2) or b""
                stored_player = parse_bytes_fields(stored_pvp, 2)[0]
                self.assertEqual(parse_varint_field(stored_player, 5), 9_100)
                self.assertEqual(
                    parse_varint_field(
                        parse_bytes_field(stored_player, 18) or b"", 1
                    ),
                    second_kit_id,
                )
                request(
                    3, 5,
                    pb_varint(1, second_kit_id)
                    + pb_varint(2, 0)
                    + pb_varint(4, 2),
                    378,
                )
                rejected, _ = await receive(3, 5, 378)
                self.assertEqual(rejected.error, 352)

                with (
                    patch("server.random.randrange", return_value=2),
                    patch("server.PREPARE_SIGNAL_DELAY", 0.0),
                    patch("server.PLAYER_OTHER_SHOT_SETTLE", 0.0),
                    patch("server.BOT_THINK_DELAY", 60.0),
                ):
                    request(3, 3, pb_varint(1, 1), 374)
                    ack, _ = await receive(3, 3, 374)
                    self.assertEqual(ack.error, 0)
                    shot_notification = None
                    async with asyncio.timeout(5):
                        while shot_notification is None:
                            head, body, _ = await read_frame(reader, "body")
                            if (head.cmd, head.act) != (255, 2):
                                continue
                            result = parse_bytes_field(body, 1) or b""
                            if parse_varint_field(result, 1) == 1:
                                shot_notification = (result, body)

                shot_result, shot_body = shot_notification
                shot_events = parse_bytes_fields(shot_result, 4)
                source_outline = parse_bytes_field(shot_events[0], 1) or b""
                target_outline = parse_bytes_field(shot_events[0], 2) or b""
                self.assertEqual(
                    parse_varint_field(
                        parse_bytes_field(source_outline, 10) or b"", 1
                    ),
                    1,
                )
                self.assertEqual(
                    parse_varint_field(target_outline, 2),
                    (-2) & ((1 << 64) - 1),
                )
                self.assertEqual(parse_varint_field(target_outline, 49), 1)
                self.assertEqual(parse_varint_field(target_outline, 73), 2)
                final_outline = parse_bytes_field(shot_events[-1], 1) or b""
                removed = parse_bytes_fields(final_outline, 24)
                self.assertEqual(
                    [parse_varint_field(buff, 1) for buff in removed],
                    [MAINTENANCE_KIT_BUFF_CFG_ID],
                )

                shot_pvp = parse_bytes_field(shot_body, 2) or b""
                shot_gamers = parse_bytes_fields(shot_pvp, 2)
                player_after_shot = shot_gamers[0]
                real_rounds = [
                    (parse_varint_field(ammo, 1), parse_varint_field(ammo, 2))
                    for ammo in parse_bytes_fields(
                        parse_bytes_field(player_after_shot, 7) or b"", 2
                    )
                ]
                self.assertIn((1, 1), real_rounds)
                self.assertNotIn(2, [cfg_id for cfg_id, _ in real_rounds])
                self.assertNotIn(
                    MAINTENANCE_KIT_BUFF_CFG_ID,
                    [
                        parse_varint_field(buff, 1)
                        for buff in parse_bytes_fields(player_after_shot, 8)
                    ],
                )
            finally:
                if writer is not None:
                    writer.close()
                    await writer.wait_closed()
                listener.close()
                await listener.wait_closed()

        asyncio.run(run_exchange())

    def test_mode1_surprise_box_awards_usable_temporary_card_in_live_flow(self) -> None:
        state = self._state({"selectedHero": 0})
        state._accounts = {}
        state._next_gid = 1000001
        state.pvp_port = 0

        async def run_exchange() -> None:
            listener = await asyncio.start_server(
                lambda reader, writer: serve_client(
                    reader, writer, state, "body", "pvp"
                ),
                "127.0.0.1", 0,
            )
            writer = None
            try:
                reader, writer = await asyncio.open_connection(
                    "127.0.0.1", listener.sockets[0].getsockname()[1]
                )

                async def receive(cmd: int, act: int, index: int = 0):
                    async with asyncio.timeout(5):
                        while True:
                            head, body, _ = await read_frame(reader, "body")
                            if (head.cmd, head.act, head.index) == (cmd, act, index):
                                return head, body

                def request(cmd: int, act: int, body: bytes, index: int) -> None:
                    writer.write(encode_frame(
                        cmd, act, body, index=index, length_mode="body"
                    ))

                with patch(
                    "server._random_shop_specs",
                    return_value=((2001, 100), (2003, 200),
                                  (2004, 100), (2020, 200)),
                ):
                    request(3, 1, pb_bytes(2, "local-pvp:1:6:0:0"), 391)
                    await receive(3, 1, 391)
                    request(3, 14, b"", 392)
                    await receive(3, 14, 392)
                    await receive(255, 1)

                with patch("server.random.choice", return_value=(2003, 200)):
                    request(
                        3, 5,
                        pb_varint(1, 4) + pb_varint(2, 0) + pb_varint(4, 1),
                        393,
                    )
                    ack, _ = await receive(3, 5, 393)
                    self.assertEqual(ack.error, 0)
                    _, notification = await receive(255, 2)
                result = parse_bytes_field(notification, 1) or b""
                self.assertEqual(parse_varint_field(result, 2), 1019)
                events = parse_bytes_fields(result, 4)
                self.assertEqual(
                    parse_varint_field(parse_bytes_field(events[1], 2) or b"", 9),
                    6,
                )
                pvp = parse_bytes_field(notification, 2) or b""
                player = parse_bytes_fields(pvp, 2)[0]
                self.assertEqual(parse_varint_field(player, 5), 9_800)
                slot = parse_bytes_field(player, 18) or b""
                reward_id = parse_varint_field(slot, 1) or 0
                self.assertGreater(reward_id, 4)
                self.assertEqual(parse_varint_field(slot, 2), 2003)

                request(
                    3, 5,
                    pb_varint(1, reward_id) + pb_varint(2, 0) + pb_varint(4, 2),
                    394,
                )
                ack, _ = await receive(3, 5, 394)
                self.assertEqual(ack.error, 0)
                _, used = await receive(255, 2)
                used_result = parse_bytes_field(used, 1) or b""
                self.assertEqual(parse_varint_field(used_result, 2), 1002)
                used_pvp = parse_bytes_field(used, 2) or b""
                used_player = parse_bytes_fields(used_pvp, 2)[0]
                self.assertEqual(parse_varint_field(used_player, 5), 9_800)
                self.assertEqual(
                    parse_varint_field(parse_bytes_field(used_player, 18) or b"", 1),
                    0,
                )
                gun = parse_bytes_field(used_player, 7) or b""
                self.assertIn(
                    (1, 3),
                    [(parse_varint_field(ammo, 1), parse_varint_field(ammo, 2))
                     for ammo in parse_bytes_fields(gun, 2)],
                )
            finally:
                if writer is not None:
                    writer.close()
                    await writer.wait_closed()
                listener.close()
                await listener.wait_closed()

        with patch("protocol.pvp_gun_ammo_counts", return_value=(2, 1)):
            asyncio.run(run_exchange())

    def test_mode1_violation_ticket_rolls_and_transfers_coins_in_live_flow(self) -> None:
        state = self._state({"selectedHero": 0})
        state._accounts = {}
        state._next_gid = 1000001
        state.pvp_port = 0

        async def run_exchange() -> None:
            listener = await asyncio.start_server(
                lambda reader, writer: serve_client(
                    reader, writer, state, "body", "pvp"
                ),
                "127.0.0.1", 0,
            )
            writer = None
            try:
                reader, writer = await asyncio.open_connection(
                    "127.0.0.1", listener.sockets[0].getsockname()[1]
                )

                async def receive(cmd: int, act: int, index: int = 0):
                    async with asyncio.timeout(5):
                        while True:
                            head, body, _ = await read_frame(reader, "body")
                            if (head.cmd, head.act, head.index) == (cmd, act, index):
                                return head, body

                def request(cmd: int, act: int, body: bytes, index: int) -> None:
                    writer.write(encode_frame(
                        cmd, act, body, index=index, length_mode="body"
                    ))

                specs = ((2001, 100), (2003, 200), (2004, 100), (2018, 400))
                with patch("server._random_shop_specs", return_value=specs):
                    request(3, 1, pb_bytes(2, "local-pvp:1:6:0:0"), 381)
                    await receive(3, 1, 381)
                    request(3, 14, b"", 382)
                    await receive(3, 14, 382)
                    await receive(255, 1)

                with patch("server.random.randint", return_value=4):
                    request(
                        3, 5,
                        pb_varint(1, 4) + pb_varint(2, 1) + pb_varint(4, 1),
                        383,
                    )
                    ack, _ = await receive(3, 5, 383)
                    self.assertEqual(ack.error, 0)
                    _, notification = await receive(255, 2)
                result = parse_bytes_field(notification, 1) or b""
                self.assertEqual(parse_varint_field(result, 2), 1017)
                events = parse_bytes_fields(result, 4)
                self.assertEqual(
                    [parse_varint_field(parse_bytes_field(e, 1) or b"", 9)
                     for e in events],
                    [4, 7],
                )
                luck = parse_bytes_field(
                    parse_bytes_field(events[1], 2) or b"", 22
                ) or b""
                self.assertEqual(parse_varint_field(luck, 1), 4)
                self.assertEqual(parse_varint_field(luck, 3), 1)
                lost = parse_bytes_field(
                    parse_bytes_field(events[1], 2) or b"", 4
                ) or b""
                gained = parse_bytes_field(
                    parse_bytes_field(events[1], 1) or b"", 4
                ) or b""
                self.assertEqual(parse_varint_field(lost, 1), (-400) & ((1 << 64) - 1))
                self.assertEqual(parse_varint_field(gained, 1), 400)
                self.assertEqual(parse_varint_field(lost, 2), 1)
                self.assertEqual(parse_varint_field(gained, 2), 1)
                pvp = parse_bytes_field(notification, 2) or b""
                gamers = parse_bytes_fields(pvp, 2)
                self.assertEqual(parse_varint_field(gamers[0], 5), 10_000)
                self.assertEqual(parse_varint_field(gamers[1], 5), 9_600)

                # The same card bought into storage must run the identical
                # dice/coin sequence without charging a second use price.
                with patch("server._random_shop_specs", return_value=specs):
                    request(
                        3, 5,
                        pb_varint(1, 10_000) + pb_varint(2, -1) + pb_varint(4, 4),
                        384,
                    )
                    ack, _ = await receive(3, 5, 384)
                    self.assertEqual(ack.error, 0)
                    _, refresh = await receive(255, 2)
                refreshed_pvp = parse_bytes_field(refresh, 2) or b""
                ticket = next(
                    c for c in parse_bytes_fields(refreshed_pvp, 7)
                    if parse_varint_field(c, 2) == 2018
                )
                ticket_id = parse_varint_field(ticket, 1) or 0
                request(3, 5, pb_varint(1, ticket_id) + pb_varint(4, 3), 385)
                ack, _ = await receive(3, 5, 385)
                self.assertEqual(ack.error, 0)
                await receive(255, 2)
                with patch("server.random.randint", return_value=5):
                    request(
                        3, 5,
                        pb_varint(1, ticket_id)
                        + pb_varint(2, 1)
                        + pb_varint(4, 2),
                        386,
                    )
                    ack, _ = await receive(3, 5, 386)
                    self.assertEqual(ack.error, 0)
                    _, stored_use = await receive(255, 2)
                stored_result = parse_bytes_field(stored_use, 1) or b""
                self.assertEqual(parse_varint_field(stored_result, 2), 1017)
                stored_events = parse_bytes_fields(stored_result, 4)
                self.assertEqual(
                    [parse_varint_field(parse_bytes_field(e, 1) or b"", 9)
                     for e in stored_events],
                    [6, 7],
                )
                stored_pvp = parse_bytes_field(stored_use, 2) or b""
                gamers = parse_bytes_fields(stored_pvp, 2)
                self.assertEqual(parse_varint_field(gamers[0], 5), 9_800)
                self.assertEqual(parse_varint_field(gamers[1], 5), 9_100)
                self.assertEqual(
                    parse_varint_field(parse_bytes_field(gamers[0], 18) or b"", 1),
                    0,
                )
            finally:
                if writer is not None:
                    writer.close()
                    await writer.wait_closed()
                listener.close()
                await listener.wait_closed()

        asyncio.run(run_exchange())

    def test_mode1_hallucinogen_can_target_owner_without_losing_shot_state(self) -> None:
        state = self._state({"selectedHero": 0})
        state._accounts = {}
        state._next_gid = 1000001
        state.pvp_port = 0

        async def run_exchange() -> None:
            listener = await asyncio.start_server(
                lambda reader, writer: serve_client(reader, writer, state, "body", "pvp"),
                "127.0.0.1", 0,
            )
            writer = None
            try:
                reader, writer = await asyncio.open_connection(
                    "127.0.0.1", listener.sockets[0].getsockname()[1]
                )

                async def receive(cmd: int, act: int, index: int = 0) -> tuple[object, bytes]:
                    async with asyncio.timeout(4):
                        while True:
                            head, body, _ = await read_frame(reader, "body")
                            if (head.cmd, head.act, head.index) == (cmd, act, index):
                                return head, body

                writer.write(encode_frame(
                    3, 1, pb_bytes(2, "local-pvp:1:6:0:0"),
                    index=371, length_mode="body",
                ))
                await receive(3, 1, 371)
                writer.write(encode_frame(3, 14, b"", index=372, length_mode="body"))
                await receive(3, 14, 372)
                await receive(255, 1)

                # The client explicitly serializes target 0 for the owner.
                with patch("server.random.randrange", return_value=3):
                    writer.write(encode_frame(
                        3, 5,
                        pb_varint(1, 4) + pb_varint(2, 0) + pb_varint(4, 1),
                        index=373, length_mode="body",
                    ))
                    ack, _ = await receive(3, 5, 373)
                    self.assertEqual(ack.error, 0)
                    _, notification = await receive(255, 2)

                result = parse_bytes_field(notification, 1) or b""
                self.assertEqual(parse_varint_field(result, 10), 0)
                events = parse_bytes_fields(result, 4)
                self.assertEqual(
                    parse_varint_field(parse_bytes_field(events[0], 1) or b"", 9), 4
                )
                self.assertEqual(
                    parse_varint_field(parse_bytes_field(events[1], 1) or b"", 1), 0
                )
                pvp_info = parse_bytes_field(notification, 2) or b""
                gamers = parse_bytes_fields(pvp_info, 2)
                self.assertEqual(parse_varint_field(gamers[0], 4), 3)
                self.assertEqual(parse_varint_field(gamers[0], 5), 9_800)
                self.assertEqual(parse_varint_field(gamers[1], 4), 4)
                gun = parse_bytes_field(gamers[0], 7) or b""
                self.assertEqual(
                    [parse_varint_field(ammo, 2) for ammo in parse_bytes_fields(gun, 2)],
                    [2, 1],
                )
            finally:
                if writer is not None:
                    writer.close()
                    await writer.wait_closed()
                listener.close()
                await listener.wait_closed()

        asyncio.run(run_exchange())

    def test_mode1_round_cards_add_real_or_fake_from_shop_and_slot(self) -> None:
        state = self._state({"selectedHero": 0})
        state._accounts = {}
        state._next_gid = 1000001
        state.pvp_port = 0

        async def run_exchange() -> None:
            listener = await asyncio.start_server(
                lambda reader, writer: serve_client(reader, writer, state, "body", "pvp"),
                "127.0.0.1", 0,
            )
            try:
                for card_id, cfg_id, skill_id, ammo_id, price, counts in (
                    (2, 2003, 1002, 1, 200, [1, 3]),
                    (3, 2004, 1003, 300, 100, [2, 2]),
                ):
                    for route in ("immediate", "stored"):
                        await check_route(
                            listener, route, card_id, cfg_id, skill_id,
                            ammo_id, price, counts,
                        )
            finally:
                listener.close()
                await listener.wait_closed()

        async def check_route(
            listener: object, route: str, card_id: int, cfg_id: int, skill_id: int,
            ammo_id: int, price: int, counts: list[int],
        ) -> None:
                    reader, writer = await asyncio.open_connection(
                        "127.0.0.1", listener.sockets[0].getsockname()[1]
                    )
                    try:
                        async def receive(cmd: int, act: int, index: int = 0) -> tuple[object, bytes]:
                            async with asyncio.timeout(4):
                                while True:
                                    head, body, _ = await read_frame(reader, "body")
                                    if (head.cmd, head.act, head.index) == (cmd, act, index):
                                        return head, body

                        def request(cmd: int, act: int, body: bytes, index: int) -> None:
                            writer.write(encode_frame(
                                cmd, act, body, index=index, length_mode="body"
                            ))

                        request(3, 1, pb_bytes(2, "local-pvp:1:6:0:0"), 381)
                        await receive(3, 1, 381)
                        request(3, 14, b"", 382)
                        await receive(3, 14, 382)
                        await receive(255, 1)

                        if route == "stored":
                            request(3, 5, pb_varint(1, card_id) + pb_varint(4, 3), 383)
                            ack, _ = await receive(3, 5, 383)
                            self.assertEqual(ack.error, 0)
                            await receive(255, 2)

                        target_index = 0 if route == "immediate" else 1
                        # Neither opening magazine has activated its reload trait.
                        expected_counts = counts
                        action_type = 1 if route == "immediate" else 2
                        request(
                            3, 5,
                            pb_varint(1, card_id)
                            + pb_varint(2, target_index)
                            + pb_varint(4, action_type),
                            384,
                        )
                        ack, _ = await receive(3, 5, 384)
                        self.assertEqual(ack.error, 0)
                        _, notification = await receive(255, 2)

                        result = parse_bytes_field(notification, 1) or b""
                        self.assertEqual(
                            parse_varint_field(result, 1),
                            7 if route == "immediate" else 8,
                        )
                        self.assertEqual(parse_varint_field(result, 2), skill_id)
                        self.assertEqual(parse_varint_field(result, 5), cfg_id)
                        self.assertEqual(parse_varint_field(result, 10), target_index)
                        events = parse_bytes_fields(result, 4)
                        self.assertEqual(len(events), 2)
                        first_source = parse_bytes_field(events[0], 1) or b""
                        self.assertEqual(
                            parse_varint_field(first_source, 9),
                            4 if route == "immediate" else 6,
                        )
                        ammo_source = parse_bytes_field(events[1], 1) or b""
                        ammo_target = parse_bytes_field(events[1], 2) or b""
                        self.assertEqual(parse_varint_field(ammo_source, 9), 21)
                        self.assertEqual(parse_varint_field(ammo_target, 9), 21)
                        self.assertEqual(parse_varint_field(ammo_target, 1), target_index)
                        self.assertEqual(
                            parse_varint_field(
                                parse_bytes_field(ammo_target, 10) or b"", 1
                            ), ammo_id,
                        )
                        self.assertEqual(
                            [parse_varint_field(ammo, 2)
                             for ammo in parse_bytes_fields(ammo_target, 5)],
                            expected_counts,
                        )
                        pvp_info = parse_bytes_field(notification, 2) or b""
                        gamers = parse_bytes_fields(pvp_info, 2)
                        self.assertEqual(parse_varint_field(gamers[0], 5), 10_000 - price)
                        gun = parse_bytes_field(gamers[target_index], 7) or b""
                        self.assertEqual(
                            [parse_varint_field(ammo, 2)
                             for ammo in parse_bytes_fields(gun, 2)],
                            expected_counts,
                        )
                        if route == "stored":
                            slot = parse_bytes_field(gamers[0], 18) or b""
                            self.assertEqual(parse_varint_field(slot, 1), 0)
                    finally:
                        writer.close()
                        await writer.wait_closed()
        # Underfilled fixture leaves one legal slot for the add-round card.
        with patch("protocol.pvp_gun_ammo_counts", return_value=(2, 1)):
            asyncio.run(run_exchange())

    def test_mode1_ejector_removes_random_round_from_shop_and_slot(self) -> None:
        state = self._state({"selectedHero": 0})
        state._accounts = {}
        state._next_gid = 1000001
        state.pvp_port = 0

        async def run_exchange() -> None:
            listener = await asyncio.start_server(
                lambda reader, writer: serve_client(reader, writer, state, "body", "pvp"),
                "127.0.0.1", 0,
            )
            try:
                for route, target_index, roll, ejected_id, counts in (
                    ("immediate", 0, 0, 300, [1, 2]),
                    ("stored", 1, 2, 1, [2, 1]),
                ):
                    reader, writer = await asyncio.open_connection(
                        "127.0.0.1", listener.sockets[0].getsockname()[1]
                    )
                    try:
                        async def receive(
                            cmd: int, act: int, index: int = 0,
                        ) -> tuple[object, bytes]:
                            async with asyncio.timeout(4):
                                while True:
                                    head, body, _ = await read_frame(reader, "body")
                                    if (head.cmd, head.act, head.index) == (cmd, act, index):
                                        return head, body

                        def request(cmd: int, act: int, body: bytes, index: int) -> None:
                            writer.write(encode_frame(
                                cmd, act, body, index=index, length_mode="body"
                            ))

                        request(3, 1, pb_bytes(2, "local-pvp:1:6:0:0"), 391)
                        await receive(3, 1, 391)
                        request(3, 14, b"", 392)
                        await receive(3, 14, 392)
                        await receive(255, 1)

                        if route == "stored":
                            request(3, 5, pb_varint(1, 1) + pb_varint(4, 3), 393)
                            ack, _ = await receive(3, 5, 393)
                            self.assertEqual(ack.error, 0)
                            await receive(255, 2)

                        with patch("server.random.randrange", return_value=roll):
                            request(
                                3, 5,
                                pb_varint(1, 1)
                                + pb_varint(2, target_index)
                                + pb_varint(4, 1 if route == "immediate" else 2),
                                394,
                            )
                            ack, _ = await receive(3, 5, 394)
                            self.assertEqual(ack.error, 0)
                            _, notification = await receive(255, 2)

                        result = parse_bytes_field(notification, 1) or b""
                        self.assertEqual(
                            parse_varint_field(result, 1),
                            7 if route == "immediate" else 8,
                        )
                        self.assertEqual(parse_varint_field(result, 2), 1000)
                        self.assertEqual(parse_varint_field(result, 5), 2001)
                        self.assertEqual(parse_varint_field(result, 10), target_index)
                        events = parse_bytes_fields(result, 4)
                        self.assertEqual(len(events), 2)
                        first_source = parse_bytes_field(events[0], 1) or b""
                        self.assertEqual(
                            parse_varint_field(first_source, 9),
                            4 if route == "immediate" else 6,
                        )
                        pop_source = parse_bytes_field(events[1], 1) or b""
                        pop_target = parse_bytes_field(events[1], 2) or b""
                        self.assertEqual(parse_varint_field(pop_source, 1), target_index)
                        self.assertEqual(parse_varint_field(pop_source, 9), 13)
                        self.assertEqual(parse_varint_field(pop_target, 1), target_index)
                        self.assertEqual(parse_varint_field(pop_target, 9), 13)
                        popped = parse_bytes_field(pop_target, 12) or b""
                        self.assertEqual(parse_varint_field(popped, 1), ejected_id)
                        self.assertEqual(parse_varint_field(popped, 2), 1)

                        pvp_info = parse_bytes_field(notification, 2) or b""
                        gamers = parse_bytes_fields(pvp_info, 2)
                        self.assertEqual(parse_varint_field(gamers[0], 5), 9_900)
                        gun = parse_bytes_field(gamers[target_index], 7) or b""
                        self.assertEqual(
                            [parse_varint_field(ammo, 2)
                             for ammo in parse_bytes_fields(gun, 2)],
                            counts,
                        )
                        if route == "stored":
                            slot = parse_bytes_field(gamers[0], 18) or b""
                            self.assertEqual(parse_varint_field(slot, 1), 0)
                    finally:
                        writer.close()
                        await writer.wait_closed()
            finally:
                listener.close()
                await listener.wait_closed()

        asyncio.run(run_exchange())

    def test_mode1_ejector_reloads_when_last_real_round_is_removed(self) -> None:
        state = self._state({"selectedHero": 0})
        state._accounts = {}
        state._next_gid = 1000001
        state.pvp_port = 0

        async def run_exchange() -> None:
            listener = await asyncio.start_server(
                lambda reader, writer: serve_client(
                    reader, writer, state, "body", "pvp"
                ),
                "127.0.0.1",
                0,
            )
            try:
                for route, target_index in (("immediate", 0), ("stored", 1)):
                    reader, writer = await asyncio.open_connection(
                        "127.0.0.1", listener.sockets[0].getsockname()[1]
                    )
                    try:
                        async def receive(
                            cmd: int, act: int, index: int = 0,
                        ) -> tuple[object, bytes]:
                            async with asyncio.timeout(4):
                                while True:
                                    head, body, _ = await read_frame(reader, "body")
                                    if (head.cmd, head.act, head.index) == (
                                        cmd, act, index
                                    ):
                                        return head, body

                        def request(cmd: int, act: int, body: bytes, index: int) -> None:
                            writer.write(encode_frame(
                                cmd, act, body, index=index, length_mode="body"
                            ))

                        # Force one real round and no blanks so this use of the
                        # Ejector reproduces the exact empty-magazine edge case.
                        with (
                            patch("protocol.pvp_gun_ammo_counts", return_value=(1, 0)),
                            patch("server.pvp_gun_ammo_counts", return_value=(1, 0)),
                        ):
                            request(3, 1, pb_bytes(2, "local-pvp:1:6:0:0"), 411)
                            await receive(3, 1, 411)
                            request(3, 14, b"", 412)
                            await receive(3, 14, 412)
                            await receive(255, 1)

                            if route == "stored":
                                request(3, 5, pb_varint(1, 1) + pb_varint(4, 3), 413)
                                ack, _ = await receive(3, 5, 413)
                                self.assertEqual(ack.error, 0)
                                await receive(255, 2)

                            use_body = (
                                pb_varint(1, 1)
                                + pb_varint(2, target_index)
                                + pb_varint(4, 1 if route == "immediate" else 2)
                            )
                            request(3, 5, use_body, 414)
                            ack, _ = await receive(3, 5, 414)
                            self.assertEqual(ack.error, 0)
                            _, notification = await receive(255, 2)

                        result = parse_bytes_field(notification, 1) or b""
                        events = parse_bytes_fields(result, 4)
                        self.assertEqual(len(events), 3)
                        pop_target = parse_bytes_field(events[1], 2) or b""
                        self.assertEqual(parse_varint_field(pop_target, 9), 13)
                        reload_source = parse_bytes_field(events[2], 1) or b""
                        reload_target = parse_bytes_field(events[2], 2) or b""
                        self.assertEqual(parse_varint_field(reload_source, 9), 1)
                        self.assertEqual(parse_varint_field(reload_target, 9), 1)
                        self.assertEqual(parse_varint_field(reload_target, 8), 1)
                        self.assertEqual(
                            [parse_varint_field(ammo, 2)
                             for ammo in parse_bytes_fields(reload_target, 5)],
                            [0, 1] if target_index == 0 else [0, 0, 1],
                        )
                        pvp_info = parse_bytes_field(notification, 2) or b""
                        gamers = parse_bytes_fields(pvp_info, 2)
                        gun = parse_bytes_field(gamers[target_index], 7) or b""
                        self.assertEqual(
                            {
                                parse_varint_field(ammo, 1):
                                parse_varint_field(ammo, 2)
                                for ammo in parse_bytes_fields(gun, 2)
                            },
                            {1: 1, 300: 0} if target_index == 0 else {1: 0, 300: 0, 2: 1},
                        )

                        if route == "stored":
                            # The card is consumed; its reload still belongs
                            # to the chosen target, not the item's owner.
                            slot = parse_bytes_field(gamers[0], 18) or b""
                            self.assertEqual(parse_varint_field(slot, 1), 0)
                    finally:
                        writer.close()
                        await writer.wait_closed()
            finally:
                listener.close()
                await listener.wait_closed()

        asyncio.run(run_exchange())

    def test_pvp_queries_do_not_see_unemitted_bot_shot(self) -> None:
        """A mid-animation poll must see the player shot, not the planned bot shot."""
        state = self._state({"selectedHero": 0})
        state._accounts = {}
        state._next_gid = 1000001
        state.pvp_port = 0

        async def run_exchange() -> None:
            listener = await asyncio.start_server(
                lambda reader, writer: serve_client(
                    reader, writer, state, "body", "pvp"
                ),
                "127.0.0.1",
                0,
            )
            writer = None
            try:
                port = listener.sockets[0].getsockname()[1]
                reader, writer = await asyncio.open_connection("127.0.0.1", port)

                async def receive(cmd: int, act: int, index: int = 0) -> bytes:
                    async with asyncio.timeout(2):
                        while True:
                            head, body, _ = await read_frame(reader, "body")
                            if (head.cmd, head.act, head.index) == (cmd, act, index):
                                return body

                def request(cmd: int, act: int, body: bytes, index: int) -> None:
                    writer.write(encode_frame(
                        cmd, act, body, index=index, length_mode="body"
                    ))

                request(3, 1, pb_bytes(2, "local-pvp:1:4:0:0"), 101)
                await receive(3, 1, 101)
                request(3, 14, b"", 102)
                await receive(3, 14, 102)
                await receive(255, 1)

                # Both selected rounds are real. The server plans a bot hit
                # immediately, but its notification is delayed by the timer.
                request(3, 3, pb_varint(1, 1), 103)
                await receive(3, 3, 103)
                await receive(255, 2)

                request(3, 11, b"", 104)
                room_reply = await receive(3, 11, 104)
                visible_room = parse_bytes_field(room_reply, 1) or b""
                visible_gamers = parse_bytes_fields(visible_room, 2)
                self.assertEqual(
                    [parse_varint_field(gamer, 4) for gamer in visible_gamers],
                    [4, 3],
                )
                self.assertEqual(parse_varint_field(visible_room, 10), 1)

                request(3, 19, pb_varint(2, 0), 105)
                gamer_reply = await receive(3, 19, 105)
                visible_player = parse_bytes_field(gamer_reply, 2) or b""
                self.assertEqual(parse_varint_field(visible_player, 4), 4)
            finally:
                if writer is not None:
                    writer.close()
                    await writer.wait_closed()
                listener.close()
                await listener.wait_closed()

        with patch("server.random.randrange", return_value=5), patch(
            "server.PLAYER_OTHER_SHOT_SETTLE", 60.0
        ):
            asyncio.run(run_exchange())

    def test_season_state_is_clamped_to_one_valid_bundled_season(self) -> None:
        state = season_state(
            {"serverTime": 0, "seasonId": 0, "lastSeasonId": 0, "seasonCup": 0}
        )
        self.assertEqual(
            state,
            {
                "serverTime": 1_778_000_000,
                "seasonId": 18,
                "lastSeasonId": 17,
                "seasonCup": 1,
                "seasonMmr": 0,
            },
        )
        season = pb_bytes(1, pb_message(pb_varint(1, 18), pb_varint(2, 17)))
        self.assertIn(season, season_get_info_body({}))
        marker = local_bot_start_body(38002, 7, 701, 24, 9)
        self.assertIn(b"tcp:127.0.0.1:38002", marker)
        self.assertIn(b"local-pvp:7:701:24:9", marker)
        self.assertEqual(server_time_body({}), b"\x08\x80\xc1\xe8\xcf\x06\x38\x00")

    def test_local_server_clock_advances_heartbeat_and_box_cooldown(self) -> None:
        state = self._state({"serverTime": 1_778_000_000})
        state._clock_monotonic = 100.0

        with patch("server.time.monotonic", return_value=100.0):
            initial = state.timed_inventory()
        with patch("server.time.monotonic", return_value=106.0):
            later = state.timed_inventory()

        self.assertEqual(
            parse_varint_field(server_time_body(initial), 1), 1_778_000_000
        )
        self.assertEqual(
            parse_varint_field(server_time_body(later), 1), 1_778_000_006
        )
        initial_box = parse_bytes_field(explore_box_info_body(initial), 1) or b""
        later_box = parse_bytes_field(explore_box_info_body(later), 1) or b""
        self.assertEqual(parse_varint_field(initial_box, 2), 1_778_000_000)
        self.assertEqual(parse_varint_field(later_box, 2), 1_778_000_006)
        self.assertEqual(state.inventory["serverTime"], 1_778_000_000)

    def test_logic_heartbeat_and_box_info_publish_advancing_time(self) -> None:
        state = self._state({"serverTime": 1_778_000_000})
        state._accounts = {}
        state._next_gid = 1000001
        state.pvp_port = 0

        async def exchange() -> None:
            listener = await asyncio.start_server(
                lambda reader, writer: serve_client(
                    reader, writer, state, "body", "logic"
                ),
                "127.0.0.1",
                0,
            )
            writer = None
            try:
                port = listener.sockets[0].getsockname()[1]
                reader, writer = await asyncio.open_connection("127.0.0.1", port)
                for index, expected in ((1, 1_778_000_000), (2, 1_778_000_006)):
                    writer.write(encode_frame(2, 1, b"", index=index))
                    async with asyncio.timeout(2):
                        head, body, _ = await read_frame(reader, "body")
                    self.assertEqual((head.cmd, head.act, head.index), (2, 1, index))
                    self.assertEqual(parse_varint_field(body, 1), expected)

                writer.write(encode_frame(32, 1, b"", index=3))
                async with asyncio.timeout(2):
                    head, body, _ = await read_frame(reader, "body")
                self.assertEqual((head.cmd, head.act, head.index), (32, 1, 3))
                info = parse_bytes_field(body, 1) or b""
                self.assertEqual(parse_varint_field(info, 2), 1_778_000_010)
            finally:
                if writer is not None:
                    writer.close()
                    await writer.wait_closed()
                listener.close()
                await listener.wait_closed()

        with patch.object(
            state, "server_time", side_effect=(1_778_000_000, 1_778_000_006, 1_778_000_010)
        ):
            asyncio.run(exchange())

    def test_login_and_open_season_use_the_same_state(self) -> None:
        inventory = {
            "serverTime": 0,
            "seasonId": 999,
            "lastSeasonId": 999,
            "seasonCup": 0,
        }
        login = login_data_body(1234, "local-session-test", inventory)
        season = season_open_body(inventory)
        server_time = pb_bytes(1, pb_varint(1, 1_778_000_000))
        current_season = pb_bytes(
            13, pb_message(pb_varint(1, 18), pb_varint(2, 17))
        )
        self.assertIn(server_time, login)
        self.assertIn(current_season, login)
        self.assertIn(
            pb_bytes(2, pb_message(pb_varint(1, 18), pb_varint(2, 17))),
            season,
        )

    def test_login_home_contains_unlocked_empty_supply_box_slots(self) -> None:
        inventory = {
            "homeLevel": 50,
            "homeExp": 0,
            "treasureBoxes": [
                {
                    "index": index,
                    "openBoxTimeDec": 1000,
                    "boxId": -1,
                    "status": 1,
                }
                for index in (1, 2, 3)
            ],
            "temporaryBoxId": -1,
        }
        login = login_data_body(1234, "local-session-test", inventory)
        home = parse_bytes_field(login, 11) or b""
        slots = parse_bytes_fields(home, 6)
        self.assertEqual(len(slots), 3)
        self.assertEqual(
            [parse_varint_field(slot, 1) for slot in slots],
            [1, 2, 3],
        )
        self.assertTrue(
            all(parse_varint_field(slot, 2) == 1000 for slot in slots)
        )
        self.assertTrue(
            all(parse_varint_field(slot, 7) == 1 for slot in slots)
        )
        # Protobuf int32 -1 is emitted as its canonical ten-byte varint.
        self.assertTrue(
            all(parse_varint_field(slot, 4) == 2**64 - 1 for slot in slots)
        )
        self.assertEqual(parse_varint_field(home, 7), 2**64 - 1)

    def test_login_home_contains_persisted_income_rows(self) -> None:
        login = login_data_body(
            1234,
            "local-session-test",
            {
                "currentIncome": [
                    {
                        "itemId": 101000,
                        "income": 60_000,
                        "startTime": 100,
                        "endTime": -1,
                    }
                ]
            },
        )
        home = parse_bytes_field(login, 11) or b""
        rows = parse_bytes_fields(home, 10)
        self.assertEqual(len(rows), 1)
        self.assertEqual(parse_varint_field(rows[0], 1), 101000)
        self.assertEqual(parse_varint_field(rows[0], 2), 60_000)
        self.assertEqual(parse_varint_field(rows[0], 3), 100)
        self.assertEqual(parse_varint_field(rows[0], 4), 2**64 - 1)

    def test_equipment_update_contains_permanent_skin_and_wear_list(self) -> None:
        inventory = {
            "skins": [{"id": 105}],
            "equippedSkins": [{"targetId": 0, "fashionId": 105, "type": 1}],
            "heroGuns": [{"heroId": 0, "gunId": 3}],
        }
        fashion = fashion_update_body(inventory)
        self.assertIn(
            pb_bytes(
                1,
                pb_message(
                    pb_varint(1, 105),
                    pb_varint(2, 0),
                    pb_varint(3, -1),
                    pb_varint(4, 0),
                    pb_varint(5, 1),
                ),
            ),
            fashion,
        )
        self.assertIn(
            pb_bytes(2, pb_message(pb_varint(1, 0), pb_varint(2, 105), pb_varint(3, 1))),
            fashion,
        )
        self.assertIn(
            pb_bytes(1, pb_message(pb_varint(1, 0), pb_varint(2, 3))),
            hero_gun_update_body(inventory),
        )

    def test_card_equip_returns_complete_hero_instead_of_empty_record(self) -> None:
        body = hero_card_ready_body(
            {
                "id": 0,
                "starLevel": 5,
                "fightLevel": 10,
                "skillId": 10000,
                "faction": 20003,
                "unlockCards": [3],
                "readyCard": 3,
            }
        )
        hero = parse_bytes_field(body, 1) or b""
        self.assertEqual(parse_varint_field(hero, 1), 0)
        self.assertEqual(parse_varint_field(hero, 4), 10003)  # five-star Rabbit upgrade
        self.assertEqual(parse_varint_field(hero, 12), 3)

    def test_card_equip_does_not_unlock_a_locked_card(self) -> None:
        state = self._state(
            {
                "homeLevel": 50,
                "heroes": [{"id": 0, "starLevel": 5, "unlockCards": [1, 3, 4]}],
            }
        )
        self.assertIsNone(state.equip_card(0, 8))
        self.assertEqual(state.inventory["heroes"][0]["unlockCards"], [1, 3, 4])
        equipped = state.equip_card(0, 3)
        self.assertIsNotNone(equipped)
        self.assertEqual(equipped["readyCard"], 3)

    def test_card_unlock_consumes_token_and_returns_absolute_cost(self) -> None:
        state = self._state(
            {
                "homeLevel": 50,
                "heroes": [{"id": 0, "starLevel": 5, "unlockCards": [1, 3, 4]}],
                "items": [{"id": 201004, "number": 3}],
            }
        )
        unlocked = state.unlock_card(0, 8, 2)
        self.assertIsNotNone(unlocked)
        hero, cost = unlocked or ({}, [])
        self.assertEqual(hero["unlockCards"], [1, 3, 4, 8])
        self.assertEqual(cost, [{"id": 201004, "number": 2}])
        self.assertEqual(json.loads(state.inventory_path.read_text())["items"][0]["number"], 2)

        body = hero_card_unlock_body(hero, cost)
        returned_cost = parse_bytes_field(body, 2) or b""
        self.assertEqual(parse_varint_field(returned_cost, 1), 201004)
        self.assertEqual(parse_varint_field(returned_cost, 2), 2)

    def test_treasure_box_use_consumes_box_and_key_and_awards_item(self) -> None:
        state = self._state(
            {
                "items": [
                    {"id": 701177, "number": 2},
                    {"id": 10001000, "number": 48},
                ]
            }
        )
        opened = state.use_treasure_box(701177, 2)
        self.assertIsNotNone(opened)
        result = opened or {}
        self.assertEqual(
            result["cost"],
            [
                {"id": 701177, "number": 0},
                {"id": 10001000, "number": 0},
            ],
        )
        self.assertEqual(
            result["award"], [{"id": 701068, "number": 2, "chgNumber": 2}]
        )
        self.assertEqual(
            json.loads(state.inventory_path.read_text())["items"],
            [{"id": 701068, "number": 2}],
        )

        body = bag_use_body(result["cost"], result["award"])
        cost_items = parse_bytes_fields(body, 1)
        self.assertEqual(
            [(parse_varint_field(item, 1), parse_varint_field(item, 2)) for item in cost_items],
            [(701177, 0), (10001000, 0)],
        )
        reward = parse_bytes_field(parse_bytes_field(body, 3) or b"", 1) or b""
        self.assertEqual(parse_varint_field(reward, 1), 701068)
        self.assertEqual(parse_varint_field(reward, 2), 2)
        shown = parse_bytes_field(parse_bytes_field(body, 3) or b"", 2) or b""
        self.assertEqual(parse_varint_field(shown, 1), 701068)
        self.assertEqual(parse_varint_field(shown, 2), 2)
        self.assertEqual(parse_varint_field(shown, 3), 2)

    def test_treasure_box_use_rejects_missing_box_or_key(self) -> None:
        state = self._state(
            {
                "items": [
                    {"id": 701176, "number": 1},
                    {"id": 10001000, "number": 23},
                ]
            }
        )
        self.assertIsNone(state.use_treasure_box(701176, 1))
        self.assertEqual(state.inventory["items"][0]["number"], 1)
        self.assertEqual(state.inventory["items"][1]["number"], 23)
        self.assertIsNone(state.use_treasure_box(701176, 2))

    def test_home_content_package_resolves_decoded_drop_rows(self) -> None:
        state = self._state(
            {
                "items": [{"id": 701067, "number": 2}],
            }
        )
        # 701067 -> drop 35.  The first half of that table is the configured
        # random-character package; the first coin row begins at roll 10000.
        with patch("server.random.randrange", return_value=10000):
            opened = state.use_box_content_package(701067, 1)
        self.assertIsNotNone(opened)
        result = opened or {}
        self.assertEqual(result["cost"], [{"id": 701067, "number": 1}])
        self.assertEqual(
            result["award"], [{"id": 101000, "number": 6000, "chgNumber": 6000}]
        )
        self.assertEqual(
            json.loads(state.inventory_path.read_text())["items"],
            [{"id": 701067, "number": 1}, {"id": 101000, "number": 6000}],
        )

    def test_explore_box_award_items_use_their_embedded_drop_rows(self) -> None:
        state = self._state({"items": [{"id": 701220, "number": 1}]})
        opened = state.use_box_content_package(701220, 1)
        self.assertEqual(
            opened,
            {
                "cost": [{"id": 701220, "number": 0}],
                "award": [{"id": 701039, "number": 1, "chgNumber": 1}],
            },
        )
        self.assertEqual(
            json.loads(state.inventory_path.read_text())["items"],
            [{"id": 701039, "number": 1}],
        )

    def test_random_character_package_persists_badge_and_special_reward(self) -> None:
        state = self._state(
            {
                "items": [{"id": 701043, "number": 1}],
                "badges": [],
            }
        )
        # 701043 is the exact 32..48 range.  Force the minimum-independent
        # count to 32 and select the first configured hero weight each time.
        with patch("server.random.randint", return_value=32), patch(
            "server.random.randrange", return_value=0
        ):
            opened = state.use_random_character_package(701043, 1)
        self.assertIsNotNone(opened)
        result = opened or {}
        self.assertEqual(result["cost"], [{"id": 701043, "number": 0}])
        self.assertEqual(
            result["award"],
            [{"id": 601000, "number": 32, "chgNumber": 32, "specialShow": True}],
        )
        self.assertEqual(state.inventory["badges"], [{"id": 601000, "number": 32}])
        body = bag_use_body(result["cost"], result["award"])
        wrapper = parse_bytes_field(body, 3) or b""
        shown = parse_bytes_field(wrapper, 2) or b""
        self.assertEqual(parse_varint_field(shown, 1), 601000)
        self.assertEqual(parse_varint_field(shown, 3), 32)
        special = parse_bytes_field(wrapper, 4) or b""
        self.assertEqual(parse_varint_field(special, 1), 601000)

    def test_login_serializes_persisted_badges_separately(self) -> None:
        login = login_data_body(
            1234,
            "local-session-test",
            {"badges": [{"id": 601000, "number": 32}]},
        )
        badges = parse_bytes_fields(login, 7)
        self.assertEqual(len(badges), 1)
        self.assertEqual(parse_varint_field(badges[0], 1), 601000)
        self.assertEqual(parse_varint_field(badges[0], 2), 32)

    def test_home_box_start_timer_open_and_persist_award(self) -> None:
        state = self._state(
            {
                "homeLevel": 50,
                "temporaryBoxId": 1,
                "treasureBoxes": [
                    {"index": 1, "status": 1, "boxId": -1},
                    {"index": 2, "status": 1, "boxId": -1},
                    {"index": 3, "status": 1, "boxId": -1},
                ],
                "items": [{"id": 101000, "number": 1000}],
            }
        )
        started = state.start_home_box(2)
        self.assertIsNotNone(started)
        self.assertEqual(state.inventory["temporaryBoxId"], -1)
        self.assertEqual(state.inventory["treasureBoxes"][1]["boxId"], 1)
        state.inventory["treasureBoxes"][1]["startTime"] = int(time.time()) - 3_601
        opened = state.open_home_box(2, 1, 123)
        self.assertIsNotNone(opened)
        result = opened or {}
        self.assertEqual(
            result["award"], [{"id": 701048, "number": 1, "chgNumber": 1}]
        )
        self.assertEqual(result["box"]["boxId"], -1)
        self.assertEqual(state.inventory["treasureBoxes"][1]["boxId"], -1)
        self.assertEqual(state.inventory["items"][-1], {"id": 701048, "number": 1})

        start_body = home_start_box_body(started["boxes"])
        self.assertEqual(len(parse_bytes_fields(start_body, 2)), 3)
        open_body = home_open_box_body(123, result["box"], result["cost"], result["award"])
        self.assertEqual(parse_varint_field(open_body, 1), 123)
        award_wrapper = parse_bytes_field(open_body, 4) or b""
        award_item = parse_bytes_field(award_wrapper, 1) or b""
        self.assertEqual(parse_varint_field(award_item, 1), 701048)

    def test_home_box_replace_does_not_silently_discard_for_open_old_mode(self) -> None:
        state = self._state(
            {
                "temporaryBoxId": 2,
                "treasureBoxes": [
                    {"index": 1, "status": 1, "boxId": 1, "startTime": 123},
                    {"index": 2, "status": 1, "boxId": -1},
                    {"index": 3, "status": 1, "boxId": -1},
                ],
            }
        )
        self.assertIsNone(state.start_home_box(1, way_to_save=3))
        self.assertEqual(state.inventory["temporaryBoxId"], 2)
        self.assertEqual(state.inventory["treasureBoxes"][0]["boxId"], 1)

    def test_home_temporary_open_consumes_key_and_sell_is_persistent(self) -> None:
        state = self._state(
            {
                "temporaryBoxId": 20,
                "items": [{"id": 10001000, "number": 24}],
            }
        )
        opened = state.open_home_box(0, 3, 456)
        self.assertIsNotNone(opened)
        result = opened or {}
        self.assertEqual(result["cost"], [{"id": 10001000, "number": 0}])
        self.assertEqual(
            result["award"], [{"id": 701067, "number": 1, "chgNumber": 1}]
        )
        self.assertEqual(state.inventory["temporaryBoxId"], -1)

        state.inventory["temporaryBoxId"] = 25
        sold = state.sell_temporary_home_box()
        self.assertEqual(
            sold,
            [{"id": 101000, "number": 21600, "chgNumber": 21600}],
        )
        self.assertEqual(state.inventory["temporaryBoxId"], -1)
        sell_body = home_sell_box_body(sold)
        self.assertTrue(parse_bytes_field(sell_body, 1))

    def test_home_income_uses_only_explicit_persisted_entries(self) -> None:
        now = int(time.time())
        state = self._state(
            {
                "currentIncome": [
                    {
                        "itemId": 101000,
                        "income": 60_000,
                        "startTime": now - 120,
                        "endTime": now,
                    },
                    # The client ignores non-currency passive-income rows.
                    {"itemId": 701265, "income": 60_000, "startTime": now - 120}
                ],
                "items": [{"id": 101000, "number": 5}],
            }
        )
        income = state.collect_home_income()
        self.assertEqual(income, [{"id": 101000, "number": 125, "chgNumber": 120}])
        income_body = home_income_body(income)
        self.assertTrue(parse_bytes_field(income_body, 1))

    def test_supply_box_purchase_and_modern_pack_response(self) -> None:
        purchase = market_purchase_body(
            14500002,
            99,
            701265,
            99,
            cost=[{"id": 102000, "number": 9_899_999}],
        )
        cost = parse_bytes_field(purchase, 1) or b""
        self.assertEqual(parse_varint_field(cost, 1), 102000)
        self.assertEqual(parse_varint_field(cost, 2), 9_899_999)
        limit_item = parse_bytes_field(purchase, 2) or b""
        award = parse_bytes_field(purchase, 3) or b""
        award_item = parse_bytes_field(award, 1) or b""
        self.assertEqual(parse_varint_field(limit_item, 1), 14500002)
        self.assertEqual(parse_varint_field(limit_item, 2), 99)
        self.assertEqual(parse_varint_field(award_item, 1), 701265)
        self.assertEqual(parse_varint_field(award_item, 2), 99)

        inventory = {
            "exploreLevel": 1,
            "exploreBoxPack": [{"id": 12, "number": 98}],
            "exploreCells": [{"id": 1, "chest": 12}],
        }
        info_body = explore_box_info_body(inventory)
        info = parse_bytes_field(info_body, 1) or b""
        self.assertEqual(len(parse_bytes_fields(info, 1)), 11)
        first_cell = parse_bytes_field(info, 1) or b""
        self.assertEqual(parse_varint_field(first_cell, 1), 1)
        self.assertEqual(parse_varint_field(first_cell, 2), 12)
        pack = parse_bytes_field(info_body, 3) or b""
        self.assertEqual(parse_varint_field(pack, 1), 12)
        self.assertEqual(parse_varint_field(pack, 2), 98)

        notify = explore_box_notify_body(inventory)
        self.assertTrue(parse_bytes_field(notify, 1))
        self.assertEqual(parse_varint_field(parse_bytes_field(notify, 2) or b"", 2), 98)
        persisted = explore_box_info_body(
            {
                "exploreCells": [
                    {"id": 2, "chest": 13, "oldChest": 12, "event": [1, 1, 1, 1, 3]}
                ]
            }
        )
        persisted_info = parse_bytes_field(persisted, 1) or b""
        persisted_cell = next(
            cell for cell in parse_bytes_fields(persisted_info, 1)
            if parse_varint_field(cell, 1) == 2
        )
        self.assertEqual(parse_varint_field(persisted_cell, 5), 12)
        self.assertEqual(parse_varint_field(persisted_cell, 4), 1)
        opened = {
            "id": 1,
            "oldChest": 12,
            "chest": 13,
            "event": [1, 1, 1, 1, 3],
            "cost": [{"id": 106000, "number": 9_995}],
        }
        opened_body = explore_box_open_body(opened)
        opened_cell = parse_bytes_field(opened_body, 1) or b""
        self.assertEqual(parse_varint_field(opened_cell, 5), 12)
        self.assertEqual(parse_varint_field(opened_cell, 2), 13)
        self.assertEqual(parse_varint_field(parse_bytes_field(opened_body, 2) or b"", 1), 106000)
        self.assertEqual(parse_varint_field(parse_bytes_field(opened_body, 2) or b"", 2), 9_995)
        self.assertEqual(parse_bytes_field(explore_box_open_all_body({"exploreCells": [opened]}), 1), opened_cell)

        awarded = {"id": 1, "chest": 0, "rewardId": 701177, "rewardNumber": 1}
        award_body = explore_box_award_body(awarded)
        award_cell = parse_bytes_field(award_body, 1) or b""
        reward_wrapper = parse_bytes_field(award_body, 2) or b""
        reward = parse_bytes_field(reward_wrapper, 1) or b""
        self.assertEqual(parse_varint_field(award_cell, 1), 1)
        self.assertEqual(parse_varint_field(award_cell, 2), 0)
        self.assertEqual(parse_varint_field(reward, 1), 701177)
        self.assertEqual(parse_varint_field(reward, 2), 1)

        all_award = explore_box_award_all_body(
            [
                {"id": 1, "chest": 0, "rewardId": 701177, "rewardNumber": 1},
                {"id": 2, "chest": 0, "rewardId": 701177, "rewardNumber": 2},
            ]
        )
        self.assertEqual(len(parse_bytes_fields(all_award, 1)), 2)
        all_wrapper = parse_bytes_field(all_award, 2) or b""
        self.assertEqual(parse_varint_field(parse_bytes_field(all_wrapper, 1) or b"", 2), 2)

    def test_supply_box_shop_rows_award_their_real_pack_ids_and_prices(self) -> None:
        state = self._state({"items": [{"id": 102000, "number": 300_000}]})

        blue_single = state.buy_supply_boxes(14500000, 1)
        self.assertEqual(blue_single["cost"], [{"id": 102000, "number": 265_000}])
        self.assertEqual(
            blue_single["award"],
            [{"id": 701264, "number": 1, "chgNumber": 1}],
        )
        self.assertEqual(blue_single["packId"], 1)

        blue_discounted = state.buy_supply_boxes(14500001, 1)
        self.assertEqual(blue_discounted["cost"], [{"id": 102000, "number": 215_000}])
        self.assertEqual(blue_discounted["award"][0]["number"], 2)
        self.assertEqual(blue_discounted["packNumber"], 2)

        purple = state.buy_supply_boxes(14500002, 1)
        self.assertEqual(purple["cost"], [{"id": 102000, "number": 115_000}])
        self.assertEqual(purple["award"], [{"id": 701265, "number": 1, "chgNumber": 1}])
        self.assertEqual(
            state.inventory["exploreBoxPack"],
            [{"id": 1, "number": 2}, {"id": 12, "number": 1}],
        )

    def test_supply_box_quality_upgrade_uses_shipped_weights_and_events(self) -> None:
        no_upgrade = self._state(
            {
                "items": [{"id": 106000, "number": 5}],
                "exploreCells": [{"id": 1, "chest": 12}],
            }
        )
        with patch("server.random.randint", return_value=300), patch(
            "server.random.shuffle", lambda values: None
        ):
            opened = no_upgrade.open_supply_box(1)
        self.assertEqual(opened[0]["event"], [1, 1, 1, 1, 1])
        self.assertEqual(opened[0]["chest"], 12)

        upgraded = self._state(
            {
                "items": [{"id": 106000, "number": 5}],
                "exploreCells": [{"id": 1, "chest": 12}],
            }
        )
        with patch("server.random.randint", return_value=301), patch(
            "server.random.shuffle", lambda values: None
        ):
            opened = upgraded.open_supply_box(1)
        self.assertEqual(opened[0]["event"], [2, 1, 1, 1, 1])
        self.assertEqual(opened[0]["chest"], 23)

    def test_supply_box_single_open_replays_pending_event(self) -> None:
        state = self._state(
            {
                "items": [{"id": 106000, "number": 10}],
                "exploreCells": [
                    {"id": 1, "chest": 23, "oldChest": 12, "event": [2, 1, 1, 1, 1]}
                ],
            }
        )
        replayed = state.open_supply_box(1, replay_pending=True)
        self.assertEqual(replayed[0]["chest"], 23)
        self.assertEqual(state.inventory["items"], [{"id": 106000, "number": 10}])
        claimed = state.collect_supply_box(1)
        self.assertEqual(claimed[0]["rewardId"], 701242)
        self.assertEqual(state.inventory["items"][1], {"id": 701242, "number": 1})

    def test_supply_box_extraction_reuses_completed_cell(self) -> None:
        state = self._state(
            {
                "exploreBoxPack": [{"id": 12, "number": 1}],
                "exploreCells": [
                    {"id": 1, "chest": 0},
                    *({"id": index, "chest": 12} for index in range(2, 12)),
                ],
            }
        )
        self.assertTrue(state.extract_supply_box(2))
        self.assertEqual(state.inventory["exploreBoxPack"], [{"id": 12, "number": 0}])
        self.assertEqual(
            next(cell for cell in state.inventory["exploreCells"] if cell["id"] == 1),
            {"id": 1, "chest": 12},
        )

    def test_supply_box_extraction_accepts_all_four_quality_packs(self) -> None:
        state = self._state(
            {
                "exploreBoxPack": [
                    {"id": 1, "number": 1},
                    {"id": 23, "number": 1},
                    {"id": 34, "number": 1},
                ],
                "exploreCells": [],
            }
        )
        self.assertTrue(state.extract_supply_box(1))
        self.assertTrue(state.extract_supply_box(3))
        self.assertTrue(state.extract_supply_box(4))
        self.assertEqual(
            [(cell["id"], cell["chest"]) for cell in state.inventory["exploreCells"]],
            [(1, 1), (2, 23), (3, 34)],
        )

    def test_supply_box_open_all_is_batched_for_client_queue(self) -> None:
        state = self._state(
            {
                "items": [{"id": 106000, "number": 100}],
                "exploreCells": [
                    *({"id": index, "chest": 12} for index in range(1, 12)),
                ],
            }
        )

        with patch("server.random.randint", return_value=1):
            opened = state.open_supply_box(max_cells=6)

        self.assertEqual([cell["id"] for cell in opened], [1, 2, 3, 4, 5, 6])
        self.assertEqual(
            state.inventory["items"], [{"id": 106000, "number": 70}]
        )
        self.assertEqual(
            [
                cell["id"]
                for cell in state.inventory["exploreCells"]
                if cell.get("event")
            ],
            [1, 2, 3, 4, 5, 6],
        )
        self.assertEqual(
            [
                cell["id"]
                for cell in state.inventory["exploreCells"]
                if not cell.get("event")
            ],
            [7, 8, 9, 10, 11],
        )

        claimed = state.collect_supply_box()
        self.assertEqual([cell["id"] for cell in claimed], [1, 2, 3, 4, 5, 6])
        with patch("server.random.randint", return_value=1):
            next_batch = state.open_supply_box(max_cells=6)
        self.assertEqual([cell["id"] for cell in next_batch], [7, 8, 9, 10, 11])
        self.assertEqual(
            state.inventory["items"],
            [{"id": 106000, "number": 45}, {"id": 701231, "number": 6}],
        )

    def test_supply_box_open_all_resolves_and_claims_full_eleven_cell_grid(self) -> None:
        state = self._state(
            {
                "items": [{"id": 106000, "number": 100}],
                "exploreCells": [
                    *({"id": index, "chest": 12} for index in range(1, 12)),
                ],
            }
        )

        with patch("server.random.randint", return_value=1):
            opened = state.open_supply_box(replay_pending=True)

        self.assertEqual([cell["id"] for cell in opened], list(range(1, 12)))
        self.assertEqual(
            state.inventory["items"], [{"id": 106000, "number": 45}]
        )
        self.assertTrue(all(len(cell["event"]) == 5 for cell in opened))

        claimed = state.collect_supply_box()
        self.assertEqual([cell["id"] for cell in claimed], list(range(1, 12)))
        self.assertEqual(
            state.inventory["items"],
            [{"id": 106000, "number": 45}, {"id": 701231, "number": 11}],
        )

    def test_supply_box_open_all_replay_and_quality_upgrade_roundtrip(self) -> None:
        state = self._state(
            {
                "items": [{"id": 106000, "number": 200}],
                "exploreBoxPack": [{"id": 1, "number": 11}],
                "exploreCells": [
                    *({"id": index, "chest": 1} for index in range(1, 12)),
                ],
            }
        )

        with patch("server.random.randint", return_value=1), patch(
            "server.random.shuffle", lambda values: None
        ):
            opened = state.open_supply_box(replay_pending=True)

        self.assertEqual(len(parse_bytes_fields(
            explore_box_open_all_body(state.inventory, opened, opened[0]["cost"]),
            1,
        )), 11)
        self.assertEqual(state.inventory["items"], [{"id": 106000, "number": 145}])

        # A lost 32/5 response is replay-safe: it returns all 11 cells and
        # does not charge the five-shot cost a second time.
        replay = state.open_supply_box(replay_pending=True)
        self.assertEqual([cell["id"] for cell in replay], list(range(1, 12)))
        self.assertEqual(state.inventory["items"], [{"id": 106000, "number": 145}])

        claimed = state.collect_supply_box()
        self.assertEqual(len(claimed), 11)
        self.assertTrue(all(cell["rewardId"] == 701220 for cell in claimed))

        # Recycle the slots and force the maximum configured q1 -> q4 draw.
        state.inventory["exploreBoxPack"] = [{"id": 1, "number": 11}]
        self.assertTrue(all(state.extract_supply_box(1) for _ in range(11)))
        state.inventory["items"] = [{"id": 106000, "number": 55}]
        with patch("server.random.randint", return_value=1000), patch(
            "server.random.shuffle", lambda values: None
        ):
            upgraded = state.open_supply_box(replay_pending=True)
        self.assertEqual(len(upgraded), 11)
        self.assertTrue(all(cell["chest"] == 34 for cell in upgraded))
        self.assertTrue(all(cell["event"] == [2, 2, 2, 1, 1] for cell in upgraded))
        upgraded_claim = state.collect_supply_box()
        self.assertEqual(len(upgraded_claim), 11)
        self.assertTrue(all(cell["rewardId"] == 701253 for cell in upgraded_claim))

    def test_supply_box_open_all_replays_pending_and_opens_remaining_cells_together(self) -> None:
        state = self._state(
            {
                "items": [{"id": 106000, "number": 50}],
                "exploreCells": [
                    *(
                        {
                            "id": index,
                            "chest": 12,
                            "oldChest": 12,
                            "event": [1, 1, 1, 1, 1],
                        }
                        for index in range(1, 7)
                    ),
                    *({"id": index, "chest": 12} for index in range(7, 12)),
                ],
            }
        )

        with patch("server.random.randint", return_value=1):
            opened = state.open_supply_box(replay_pending=True)

        self.assertEqual([cell["id"] for cell in opened], list(range(1, 12)))
        self.assertEqual(
            state.inventory["items"], [{"id": 106000, "number": 25}]
        )
        self.assertEqual(
            [cell["id"] for cell in state.inventory["exploreCells"] if cell.get("event")],
            list(range(1, 12)),
        )

    def test_supply_box_open_all_replays_pending_without_recharging(self) -> None:
        state = self._state(
            {
                "items": [{"id": 106000, "number": 70}],
                "exploreCells": [
                    *(
                        {
                            "id": index,
                            "chest": 13,
                            "oldChest": 12,
                            "event": [1, 1, 1, 1, 3],
                        }
                        for index in range(1, 12)
                    ),
                ],
            }
        )

        replayed = state.open_supply_box(max_cells=6, replay_pending=True)

        self.assertEqual([cell["id"] for cell in replayed], [1, 2, 3, 4, 5, 6])
        self.assertEqual(state.inventory["items"], [{"id": 106000, "number": 70}])
        claimed = state.collect_supply_box(max_cells=6)
        self.assertEqual([cell["id"] for cell in claimed], [1, 2, 3, 4, 5, 6])
        self.assertEqual(
            [
                cell["id"]
                for cell in state.inventory["exploreCells"]
                if cell.get("event")
            ],
            [7, 8, 9, 10, 11],
        )

    def test_bag_messages_use_itemdata_absolute_quantities(self) -> None:
        inventory = {"items": [{"id": 102000, "number": 9_000}, {"id": 701177, "number": 2}]}
        bag = bag_get_pack_body(inventory)
        goods = parse_bytes_fields(bag, 1)
        self.assertEqual([parse_varint_field(item, 1) for item in goods], [102000, 701177])
        self.assertEqual([parse_varint_field(item, 2) for item in goods], [9_000, 2])

        use = bag_use_body(
            [{"id": 701177, "number": 1}],
            [{"id": 101000, "number": 25_000}],
        )
        self.assertEqual(parse_varint_field(parse_bytes_field(use, 1) or b"", 2), 1)
        award = parse_bytes_field(use, 3) or b""
        self.assertEqual(parse_varint_field(parse_bytes_field(award, 1) or b"", 1), 101000)
        self.assertEqual(parse_varint_field(parse_bytes_field(award, 1) or b"", 2), 25_000)

        sell = bag_sell_body(
            [{"id": 201004, "number": 0}],
            [{"id": 102000, "number": 11_000}],
        )
        self.assertEqual(parse_varint_field(parse_bytes_field(sell, 1) or b"", 2), 0)
        self.assertEqual(
            parse_varint_field(parse_bytes_field(parse_bytes_field(sell, 2) or b"", 1) or b"", 2),
            11_000,
        )

    def test_match_players_use_distinct_teams_and_gun_specific_magazines(self) -> None:
        _, _, player, bot = pvp_login_snapshot(
            1234, "Local Hunter", "local-pvp:test", 1, 4,
            0, 36, 105, 0, 24, 10103,
        )
        player_base = parse_bytes_field(player, 2) or b""
        bot_base = parse_bytes_field(bot, 2) or b""
        self.assertEqual(parse_varint_field(player_base, 34), 0)
        self.assertEqual(parse_varint_field(bot_base, 34), 1)
        # Opening load preserves capacity but does not activate reload traits.
        for gamer, expected in ((player, {300: 3, 1: 3}), (bot, {300: 2, 1: 2})):
            gun = parse_bytes_field(gamer, 7) or b""
            counts = {
                parse_varint_field(ammo, 1): parse_varint_field(ammo, 2)
                for ammo in parse_bytes_fields(gun, 2)
            }
            self.assertEqual(counts, expected)


    def test_mode1_tranquilizer_shop_and_stored_use_reduce_half_current_hp(self) -> None:
        original_login_snapshot = pvp_login_snapshot

        async def run_exchange(stored: bool) -> None:
            state = self._state({"selectedHero": 0})
            state._accounts = {}
            state._next_gid = 1000001
            state.pvp_port = 0

            def login_with_frenzy_targets(*args, **kwargs):
                login, info, _, _ = original_login_snapshot(*args, **kwargs)
                gamers = parse_bytes_fields(info, 2)
                player, bot, extra_bot = gamers
                bot = pvp_gamer_with_state(
                    bot, hp=3, virtual_hp=2, ammo_number=4,
                    fake_ammo_number=2, round_number=1,
                )
                extra_bot = pvp_gamer_with_state(
                    extra_bot, hp=4, virtual_hp=2, ammo_number=4,
                    fake_ammo_number=2, round_number=1,
                )
                if stored:
                    card_slot = pvp_card_slot_body(pvp_shop_card(91, 2029, 300))
                    player = pvp_gamer_with_coin_and_card(
                        player, coin=10_000, card_slot=card_slot,
                    )
                info = pvp_info_with_state(
                    info, player, bot, round_number=1, turn_number=1,
                    current_index=0, additional_gamers=(extra_bot,),
                )
                login = pb_message(
                    pb_varint(1, parse_varint_field(login, 1) or 0),
                    pb_bytes(2, info), pb_varint(3, 0),
                )
                return login, info, player, bot

            listener = await asyncio.start_server(
                lambda reader, writer: serve_client(
                    reader, writer, state, "body", "pvp",
                ),
                "127.0.0.1", 0,
            )
            writer = None
            try:
                reader, writer = await asyncio.open_connection(
                    "127.0.0.1", listener.sockets[0].getsockname()[1],
                )

                async def receive(cmd: int, act: int, index: int = 0):
                    async with asyncio.timeout(4):
                        while True:
                            head, body, _ = await read_frame(reader, "body")
                            if (head.cmd, head.act, head.index) == (cmd, act, index):
                                return head, body

                def request(cmd: int, act: int, body: bytes, index: int) -> None:
                    writer.write(encode_frame(
                        cmd, act, body, index=index, length_mode="body",
                    ))

                with (
                    patch("server.pvp_login_snapshot", side_effect=login_with_frenzy_targets),
                    patch("server._random_shop_specs", return_value=(
                        (2001, 100), (2003, 200), (2004, 100), (2029, 300),
                    )),
                ):
                    request(3, 1, pb_bytes(2, "local-pvp:1:6:0:0"), 591)
                    await receive(3, 1, 591)
                    request(3, 14, b"", 592)
                    await receive(3, 14, 592)
                    await receive(255, 1)

                    if stored:
                        action = pb_varint(1, 91) + pb_varint(2, 1) + pb_varint(4, 2)
                    else:
                        action = pb_varint(1, 4) + pb_varint(2, 1) + pb_varint(4, 1)
                    request(3, 5, action, 593)
                    ack, _ = await receive(3, 5, 593)
                    self.assertEqual(ack.error, 0)
                    _, notification = await receive(255, 2)

                result = parse_bytes_field(notification, 1) or b""
                self.assertEqual(parse_varint_field(result, 5), 2029)
                self.assertEqual(parse_varint_field(result, 2), 10008)
                effect = next(
                    event for event in parse_bytes_fields(result, 4)
                    if parse_varint_field(
                        parse_bytes_field(event, 2) or b"", 9,
                    ) == 14
                )
                target = parse_bytes_field(effect, 2) or b""
                self.assertEqual(parse_varint_field(target, 1), 1)
                self.assertEqual(
                    parse_varint_field(target, 14), (-2) & ((1 << 64) - 1),
                )
                info = parse_bytes_field(notification, 2) or b""
                gamers = parse_bytes_fields(info, 2)
                self.assertEqual(parse_varint_field(gamers[1], 4), 3)
                self.assertEqual(parse_varint_field(gamers[1], 17), 0)
                self.assertEqual(
                    parse_varint_field(gamers[0], 5), 10_000 if stored else 9_700,
                )
                if stored:
                    slot = parse_bytes_field(gamers[0], 18) or b""
                    self.assertEqual(parse_varint_field(slot, 2) or 0, 0)
            finally:
                if writer is not None:
                    writer.close()
                    await writer.wait_closed()
                listener.close()
                await listener.wait_closed()

        for stored in (False, True):
            with self.subTest(stored=stored):
                asyncio.run(run_exchange(stored))

    def test_rocket_launcher_live_flow_covers_buy_use_and_stored_use(self) -> None:
        state = self._state({"selectedHero": 0})
        state._accounts = {}
        state._next_gid = 1000001
        state.pvp_port = 0

        async def run_exchange() -> None:
            listener = await asyncio.start_server(
                lambda reader, writer: serve_client(
                    reader, writer, state, "body", "pvp"
                ),
                "127.0.0.1",
                0,
            )
            writer = None
            try:
                reader, writer = await asyncio.open_connection(
                    "127.0.0.1", listener.sockets[0].getsockname()[1]
                )

                async def receive(cmd: int, act: int, index: int = 0):
                    async with asyncio.timeout(4):
                        while True:
                            head, body, _ = await read_frame(reader, "body")
                            if (head.cmd, head.act, head.index) == (cmd, act, index):
                                return head, body

                def request(cmd: int, act: int, body: bytes, index: int) -> None:
                    writer.write(encode_frame(
                        cmd, act, body, index=index, length_mode="body"
                    ))

                with patch(
                    "server._random_shop_specs",
                    return_value=((2001, 100), (2011, 200), (2032, 600), (2032, 600)),
                ):
                    request(3, 1, pb_bytes(2, "local-pvp:1:6:0:0"), 481)
                    await receive(3, 1, 481)
                    request(3, 14, b"", 482)
                    await receive(3, 14, 482)
                    _, opening_turn = await receive(255, 1)

                opening_info = parse_bytes_field(opening_turn, 3) or b""
                opening_gamers = parse_bytes_fields(opening_info, 2)
                player_before = opening_gamers[0]
                target_before = opening_gamers[1]
                player_gun = parse_bytes_field(player_before, 7) or b""
                player_ammo = {
                    parse_varint_field(ammo, 1): parse_varint_field(ammo, 2)
                    for ammo in parse_bytes_fields(player_gun, 2)
                }
                real_before = player_ammo.get(1, 0)
                self.assertGreater(real_before, 0)
                target_hp_before = parse_varint_field(target_before, 4) or 0
                target_frenzy_before = parse_varint_field(target_before, 17) or 0

                # Buy-and-use offer 4: the true outcome consumes every cfg-1
                # round and reloads only after the Rocket event animation.
                with patch("server._draw_ejected_ammo", return_value=1):
                    request(
                        3, 5,
                        pb_varint(1, 4) + pb_varint(2, 1) + pb_varint(4, 1),
                        483,
                    )
                    ack, _ = await receive(3, 5, 483)
                    self.assertEqual(ack.error, 0)
                    _, notification = await receive(255, 2)
                result = parse_bytes_field(notification, 1) or b""
                events = parse_bytes_fields(result, 4)
                rpg_event = events[-2]
                source = parse_bytes_field(rpg_event, 1) or b""
                target = parse_bytes_field(rpg_event, 2) or b""
                self.assertEqual(parse_varint_field(source, 9), 39)
                self.assertEqual(parse_varint_field(source, 43), 1)
                self.assertEqual(
                    [(parse_varint_field(ammo, 1), parse_varint_field(ammo, 2))
                     for ammo in parse_bytes_fields(source, 12)],
                    [(1, real_before)],
                )
                target_damage = min(target_hp_before, real_before)
                frenzy_damage = min(
                    target_frenzy_before, max(0, real_before - target_hp_before)
                )
                self.assertEqual(parse_varint_field(target, 2), (-target_damage) & ((1 << 64) - 1))
                self.assertEqual(
                    parse_varint_field(target, 14) or 0,
                    (-frenzy_damage) & ((1 << 64) - 1),
                )
                reload_target = parse_bytes_field(events[-1], 2) or b""
                self.assertEqual(parse_varint_field(reload_target, 9), 1)
                self.assertEqual(parse_varint_field(reload_target, 8), 1)

                resolved_info = parse_bytes_field(notification, 2) or b""
                resolved_gamers = parse_bytes_fields(resolved_info, 2)
                reloaded_player = resolved_gamers[0]
                reloaded_gun = parse_bytes_field(reloaded_player, 7) or b""
                reloaded = {
                    parse_varint_field(ammo, 1): parse_varint_field(ammo, 2)
                    for ammo in parse_bytes_fields(reloaded_gun, 2)
                }
                self.assertGreater(reloaded.get(1, 0), 0)
                self.assertEqual(
                    parse_varint_field(resolved_gamers[1], 4),
                    max(0, target_hp_before - target_damage),
                )

                # Store offer 3, then use it on Bot 2. A blank outcome consumes
                # exactly one fake round and leaves live rounds and HP alone.
                request(3, 5, pb_varint(1, 3) + pb_varint(4, 3), 484)
                ack, _ = await receive(3, 5, 484)
                self.assertEqual(ack.error, 0)
                await receive(255, 2)
                with patch("server._draw_ejected_ammo", return_value=300):
                    request(
                        3, 5,
                        pb_varint(1, 3) + pb_varint(2, 2) + pb_varint(4, 2),
                        485,
                    )
                    ack, _ = await receive(3, 5, 485)
                    self.assertEqual(ack.error, 0)
                    _, stored_notification = await receive(255, 2)
                stored_result = parse_bytes_field(stored_notification, 1) or b""
                stored_events = parse_bytes_fields(stored_result, 4)
                stored_rpg = stored_events[-1]
                stored_source = parse_bytes_field(stored_rpg, 1) or b""
                stored_target = parse_bytes_field(stored_rpg, 2) or b""
                self.assertEqual(parse_varint_field(stored_result, 1), 8)
                self.assertEqual(parse_varint_field(stored_source, 43), 0)
                self.assertEqual(
                    [(parse_varint_field(ammo, 1), parse_varint_field(ammo, 2))
                     for ammo in parse_bytes_fields(stored_source, 12)],
                    [(300, 1)],
                )
                self.assertFalse(parse_varint_field(stored_target, 2))
                stored_info = parse_bytes_field(stored_notification, 2) or b""
                stored_gamers = parse_bytes_fields(stored_info, 2)
                remaining_slot = parse_bytes_field(stored_gamers[0], 18) or b""
                self.assertEqual(parse_varint_field(remaining_slot, 2) or 0, 0)
            finally:
                if writer is not None:
                    writer.close()
                    await writer.wait_closed()
                listener.close()
                await listener.wait_closed()

        asyncio.run(run_exchange())


if __name__ == "__main__":
    unittest.main()
