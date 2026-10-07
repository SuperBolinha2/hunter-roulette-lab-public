"""Local Hunter Roulette preservation/private-server prototype.

This is deliberately a local development server. It does not contact the
original service, Steam authentication, or any third-party endpoint.
"""

from __future__ import annotations

from hero_skills import effective_hero_skill, bear_conversion, rabbit_power, battle_hero_skill, shelby_trade, SHELBY_SKILLS, annie_convert, DIANA_SKILLS, DIANA_BUFFS, diana_hit, VERA_SKILLS, vera_round, HAWKE_SKILLS, hawke_load_count
from protocol import pvp_gamer_with_frenzy_cap
from hero_shop import monkey_candidates, monkey_convert_shop
from fair_duel import resolve_fair_duel
from hero_drone import resolve_drone
from clans import request as clan_request, snapshot as clan_snapshot, database as clan_database, ClanError
from player_profile import (ensure as ensure_profile, equip as equip_profile,
    accessory_body, accessory_notify, detail_body as profile_detail_body, ProfileError,
    rename as rename_profile, projected as projected_profile)
import copy
from katie_guard import (KATIE_SKILLS, KATIE_BUFFS, activate as activate_katie,
    intercept as intercept_katie, expire as expire_katie, expiry_packet as katie_expiry_packet)

import argparse
import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import hashlib
import json
import logging
import math
from pathlib import Path
import random
import threading
import time
from urllib.parse import parse_qs, urlsplit

from bot_ai import (
    DIFFICULTIES, ITEM_BUFF_CFG, choose_action,
    tranquilizer_frenzy_reduction,
)
from bot_presentation import ACTION_DECISION_PAUSE, skill_animation_barrier
from bot_actions import BattleActions, TurnRestrictions, has_buff
from weapon_skills import apply_reload_trait, weapon_skill_id, prioritize_shot_ammo, normal_shot_count, carnivore_reward, self_shot_reward_multiplier

from protocol import (
    HEADER_SIZE,
    MAX_FRAME_SIZE,
    decode_header,
    chat_login_body,
    chat_server_body,
    encode_frame,
    fashion_update_body,
    explore_box_info_body,
    explore_box_notify_body,
    explore_box_open_all_body,
    explore_box_open_body,
    explore_box_award_all_body,
    explore_box_award_body,
    hero_card_ready_body,
    hero_card_unlock_body,
    hero_gun_update_body,
    bag_get_pack_body,
    bag_update_body,
    bag_sell_body,
    bag_use_body,
    home_income_body,
    home_open_box_body,
    home_sell_box_body,
    home_start_box_body,
    home_update_body,
    login_data_body,
    local_bot_start_body,
    market_purchase_body,
    parse_bytes_field,
    parse_bytes_fields,
    parse_varint_field,
    pb_bytes,
    pb_message,
    pb_varint,
    HALLUCINOGEN_CARD_CFG_ID,
    HALLUCINOGEN_SKILLS,
    REAL_AMMO_CARD_CFG_ID,
    FAKE_AMMO_CARD_CFG_ID,
    EJECT_AMMO_CARD_CFG_ID,
    EJECT_AMMO_SKILLS,
    SPARE_MAGAZINE_CARD_CFG_ID,
    BURST_MODE_BUFF_CFG_ID,
    MAINTENANCE_KIT_BUFF_CFG_ID,
    WANTED_PARENT_BUFF_CFG_ID,
    WANTED_REWARD_BUFF_CFG_ID,
    WANTED_REWARD_R_CHIPS,
    WET_CIGARETTE_SKILLS,
    LAB_CARD_SKILLS,
    LAB_HERO_SKILLS,
    pvp_gun_ammo_counts,
    PIGGYBANK_COINS_PER_TURN,
    pvp_card_slot_with_arg,
    pvp_empty_card_slot_body,
    pvp_fd_body,
    pvp_bet_simple_body,
    pvp_behavior_notification_body,
    pvp_end_body,
    pvp_event_notification_body,
    pvp_gamer_dead_body,
    pvp_gamer_info_body,
    pvp_gamer_load_body,
    pvp_initial_ammo_body,
    pvp_gamer_with_state,
    pvp_gamer_with_skill_cd,
    pvp_gamer_skill_cd,
    pvp_gamer_skill_id,
    pvp_gamer_enhanced_count,
    pvp_gamer_after_weapon_reload,
    pvp_ghosts_after_shot,
    pvp_consume_toxin_heal, pvp_event_with_toxin_removed,
    pvp_consume_lucky_die,
    pvp_event_with_consumed_lucky,
    pvp_gamer_with_coin_and_card,
    pvp_gamer_with_buffs,
    pvp_gamer_with_buff_countdown,
    pvp_info_body,
    pvp_info_with_end,
    pvp_info_with_gamers,
    pvp_info_with_shop,
    pvp_info_with_state,
    pvp_login_snapshot,
    pvp_buy_card_event_result_body,
    pvp_hallucinogen_buy_and_use_event_result_body,
    pvp_add_ammo_card_event_result_body, pvp_gamer_has_ammo_space,
    pvp_spare_magazine_event_result_body,
    pvp_eject_ammo_card_event_result_body,
    pvp_wet_cigarette_event_result_body,
    pvp_refresh_shop_event_result_body,
    pvp_shop_card,
    pvp_card_slot_body,
    pvp_piggybank_round_start_event_result_body,
    pvp_piggybank_use_event_result_body,
    pvp_hallucinogen_use_event_result_body,
    pvp_generic_card_event_result_body,
    pvp_wanted_expiry_event_result_body,
    pvp_buff_countdown_event_result_body,
    pvp_passive_buff_removal_event_result_body,
    pvp_hero_skill_event_result_body,
    _c_ammo_message,
    pvp_observer_count_body,
    pvp_next_round_body,
    pvp_shoot_event_result_body,
    pvp_collect_self_shot_event_result_body,
    pvp_surrender_body,
    pvp_skip_tv_body,
    response_body,
    server_time_body,
    season_get_info_body,
    season_open_body,
    season_state,
)


LOG = logging.getLogger("hunter-roulette.local")
TRACE = logging.getLogger("hunter-roulette.trace")

# Timing reconstructed from the bundled Lua/config.  Pvp_Prepare is emitted
# while the shot is still finishing; the active turn follows after animation.
PREPARE_SIGNAL_DELAY = 0.1
PLAYER_SELF_SHOT_SETTLE = 5.0
PLAYER_CONTINUE_SHOT_SETTLE = 2.5
PLAYER_OTHER_SHOT_SETTLE = 4.0
BOT_THINK_DELAY = 3.0
BOT_SHOT_SETTLE = 5.0
BOT_SPECTATOR_THINK_DELAY = 1.5
BOT_SPECTATOR_SHOT_SETTLE = 3.0
BOT_RAISE_GUN_DELAY = 0.5
BOT_SELECT_TARGET_DELAY = 0.8
BOT_ACTION_DECISION_DELAY = ACTION_DECISION_PAUSE
# The bundled RouletteBattleWindow.OnGameStart_New sequence starts table ammo
# at t=0, shows the ammo UI at t=1, reloads at t=4, starts playerInit at t=6,
# and closes the intro at t=11. Hold the first active-turn notification until
# that opening sequence finishes; do not invent replacement client timings.
PVP_OPENING_SEQUENCE_DELAY = 11.0

# Mode-1 TV_kaichang Slate timeline lengths, inspected from the copied bundle.
# Base and difficulty variants reference the same opening prefabs.
PVP_OPENING_HERO_SECONDS = {
    0: 8.0, 1: 6.8666668, 13: 7.3, 14: 8.0, 15: 7.6333337,
    16: 7.6000004, 17: 6.4, 35: 8.0, 36: 8.0, 38: 8.0,
}


def pvp_opening_cinema_delay(gamer: bytes) -> float:
    hero = parse_bytes_field(gamer, 9) or b''
    hero_id = parse_varint_field(hero, 1) or 0
    seconds = PVP_OPENING_HERO_SECONDS.get(hero_id, 8.0)
    # Cover the native return-to-table with the participant panel, rather
    # than adding idle time after the cutscene. Scale with the test clock.
    return max(0.0, seconds - 0.1) * PVP_OPENING_SEQUENCE_DELAY / 11.0

# The client-side ``TreasureBoxOpenAllWindow`` lays out up to twelve cells
# (three rows of four) and computes the animation length as ``len(cells) * 5``.
# Do not impose a smaller state-transition limit: a partial 32/5 resolution
# leaves the client with an incomplete queue and it never sends 32/6.
# The full 11-cell response is protocol-correct and must remain intact: the
# client owns the complete five-shot animation queue.  Performance mitigation
# belongs in the client animation, not by hiding cells from the response.

# ExploreBoxExtractSteam maps the four quality buttons to these regular
# level-zero boxes.  The same ids are the bases used by ExploreBoxCfgSteam;
# a box at level N is simply base+N (levels 0..10).
EXPLORE_BOX_BASE_BY_QUALITY = {1: 1, 2: 12, 3: 23, 4: 34}

# card_cfg.price (field 13) in the copied fight_dbconfig.ab. Only cards with
# implemented effects enter this laboratory shop; the client can display more.
PVP_LAB_SHOP_SPECS = (
    (2001, 100),  # Ejector
    (2003, 200),  # Real Bullet +1
    (2004, 100),  # Blank Bullet +1
    (2008, 200),  # Hallucinogen
    (2011, 200),  # Wet Cigarettes
    # These variants use the same already-verified packet contracts as the
    # base cards above.  They are safe to expose in the lab shop even though
    # their original weighting/availability has not been reconstructed.
    (2024, 200),  # Wet Cigarettes (self-target variant)
    (2025, 200),  # Hallucinogen (opponent-target variant)
    (2026, 100),  # Ejector (variant)
    (2027, 200),  # Wet Cigarettes (self-target variant)
    # Cards below use the generic PvpEventResult envelope.  Their cfg/skill
    # ids and prices come directly from the copied fight_dbconfig.ab; the
    # local effect semantics are deterministic and are documented in the
    # implementation matrix until a live packet for each card is captured.
    (2007, 300), (2009, 200), (2015, 300), (2016, 300), (2018, 400),
    (2020, 200), (2021, 200), (2022, 300), (2028, 200), (2029, 300),
    (2030, 200), (2031, 200), (2032, 600), (2036, 200),
    (2037, 200),
)

# Bucket remains a usable reward/pre-match prop, but is not sold by the shop.
PVP_LAB_REWARD_SPECS = PVP_LAB_SHOP_SPECS + ((2033, 200),)


def _random_shop_specs(
    previous_cards: list[bytes] | tuple[bytes, ...] = (),
) -> tuple[tuple[int, int], ...]:
    """Uniform, no-duplicate lab offers; original server weights are unknown."""
    selected = tuple(random.sample(PVP_LAB_SHOP_SPECS, 4))
    previous_cfg = tuple(parse_varint_field(card, 2) or 0
                         for card in previous_cards)
    if tuple(cfg for cfg, _ in selected) == previous_cfg:
        unused = next(
            (spec for spec in PVP_LAB_SHOP_SPECS
             if spec[0] not in previous_cfg),
            None,
        )
        selected = selected[1:] + (unused or selected[0],)
    return selected


def _replenish_sold_shop_cards(
    cards: list[bytes] | tuple[bytes, ...],
    next_card_id: int,
    turn: int,
) -> tuple[tuple[bytes, ...], int]:
    """Replace each sold offer at a turn change, retaining unsold stock."""
    if not any((parse_varint_field(card, 5) or 0) == 2 for card in cards):
        return tuple(cards), next_card_id
    prices = dict(PVP_LAB_SHOP_SPECS)
    occupied = {
        parse_varint_field(card, 2) or 0
        for card in cards if (parse_varint_field(card, 5) or 0) != 2
    }
    just_sold = {
        parse_varint_field(card, 2) or 0
        for card in cards if (parse_varint_field(card, 5) or 0) == 2
    }
    result: list[bytes] = []
    for card in cards:
        if (parse_varint_field(card, 5) or 0) != 2:
            result.append(card)
            continue
        available = [spec for spec in PVP_LAB_SHOP_SPECS
                     if spec[0] not in occupied and spec[0] not in just_sold]
        if not available:
            available = [spec for spec in PVP_LAB_SHOP_SPECS
                         if spec[0] not in occupied]
        if not available:
            result.append(card)
            continue
        replacement = random.choice(available)[0]
        result.append(pvp_shop_card(
            next_card_id, replacement, prices[replacement], turn=turn,
        ))
        occupied.add(replacement)
        next_card_id += 1
    return tuple(result), next_card_id

# ExploreBoxUpCfgSteam, decoded from fight_dbconfig.ab.  Each tuple is
# (final_quality, ammo_num, weight).  ``ammo_num`` is the number of
# Up_Qua_Ammo (event 2) entries in the five-shot animation.
EXPLORE_BOX_QUALITY_UPGRADE = {
    1: ((1, 0, 635), (2, 1, 300), (3, 2, 40), (4, 3, 25)),
    2: ((2, 0, 300), (3, 1, 40), (4, 2, 25)),
    3: ((3, 0, 40), (4, 1, 25)),
    4: ((4, 0, 100),),
}

# ItemBaseSteam.use_result_value for the two shop products is 1 (blue pack)
# and 12 (purple pack).  The item-shop rows also expose the actual Steam
# currency and prices; keeping them here makes purchases observable in both
# the bag and the exploration-box screen.
EXPLORE_BOX_SHOP = {
    14500000: {"award_id": 701264, "pack_id": 1, "currency_id": 102000, "unit_price": 35_000},
    14500001: {"award_id": 701264, "pack_id": 1, "currency_id": 102000, "unit_price": 50_000},
    14500002: {"award_id": 701265, "pack_id": 12, "currency_id": 102000, "unit_price": 100_000},
}

# ExploreBoxCfgSteam.box_award is 701219+box_id for the regular ids 1..44.
# The quality-1 extract table also lists these type-2 aliases, all of which
# resolve to the same blue award in the shipped config.
EXPLORE_BOX_REWARD_BY_CHEST = {
    **{box_id: 701_219 + box_id for box_id in range(1, 45)},
    **{box_id: 701220 for box_id in (57, 58, 61, 62, 63, 64, 65, 66)},
}
EXPLORE_BOX_SPECIAL_QUALITY_LEVEL = {
    box_id: (1, 0) for box_id in (57, 58, 61, 62, 63, 64, 65, 66)
}


def frame_record(
    service: str,
    direction: str,
    frame: bytes,
    length_mode: str,
    phase: str,
    state: dict[str, int],
) -> dict[str, object]:
    """Return one lossless, machine-readable local packet trace record."""
    if len(frame) < HEADER_SIZE:
        raise ValueError("frame shorter than AntNet header")
    head = decode_header(frame[:HEADER_SIZE])
    body = frame[HEADER_SIZE:]
    expected_body = head.length - HEADER_SIZE if length_mode == "total" else head.length
    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
        "service": service,
        "direction": direction,
        "phase": phase,
        "length_mode": length_mode,
        "header": {
            "len": head.length,
            "error": head.error,
            "cmd": head.cmd,
            "act": head.act,
            "index": head.index,
            "flags": head.flags,
        },
        "body_bytes": len(body),
        "length_consistent": expected_body == len(body),
        "raw_hex": frame.hex(),
        "state": state,
    }


def trace_frame(
    service: str,
    direction: str,
    frame: bytes,
    length_mode: str,
    phase: str,
    state: dict[str, int],
) -> None:
    TRACE.info(
        json.dumps(
            frame_record(service, direction, frame, length_mode, phase, state),
            separators=(",", ":"),
            sort_keys=True,
        )
    )

# Verified against fight_dbconfig.ab. The battle protocol carries both the
# gameplay id and the rendered model id; they are not interchangeable.
HERO_BASE_FASHION = {
    0: 101, 1: 201, 13: 301, 14: 401, 15: 501,
    16: 601, 17: 701, 35: 801, 36: 901, 38: 1001,
}
GUN_BASE_FASHION = {
    # Exact gun_cfg_steam.base_fash_id mapping.  The ids 11 and 21 are
    # shipped base fashions for the alternate gun families; they are not
    # interchangeable with the 10101/10201 families.
    0: 10101, 1: 10201, 2: 10101, 3: 10201, 4: 10101, 5: 10201,
    6: 10301, 7: 10401, 8: 11, 9: 21, 10: 10101, 11: 10201,
    12: 10501, 13: 10601, 14: 10701, 15: 10101, 16: 10201,
    17: 10301, 18: 10401, 19: 10101, 20: 10201, 21: 11, 22: 21,
    23: 11, 24: 21, 25: 11, 26: 11, 27: 21, 28: 11, 29: 10201,
    30: 10301, 31: 10401, 32: 10301, 33: 10101, 34: 10801,
    35: 10901, 36: 11, 37: 21, 38: 11001, 39: 11, 40: 21,
    41: 20101,
}
FASHION_MODEL = {
    # Legacy/alternate base rows present in FashionCfgSteam and referenced by
    # gun_cfg_steam.  Without these, a valid equipped gun silently fell back
    # to the default model in PVP.
    11: 15, 21: 16, 31: 15,
    101: 1, 102: 8, 103: 16, 104: 21, 105: 36,
    201: 2, 202: 9, 203: 22,
    301: 3, 302: 10, 303: 19,
    401: 4, 402: 11, 403: 23, 404: 32,
    501: 5, 502: 12, 503: 24, 504: 37, 505: 38,
    601: 6, 602: 13, 603: 17, 604: 20, 605: 39,
    701: 7, 702: 14, 703: 18, 704: 25,
    801: 26, 802: 27, 803: 28,
    901: 29, 902: 31, 903: 30,
    1001: 33, 1002: 34, 1003: 35,
    10101: 1, 10102: 8, 10103: 24,
    10201: 2, 10202: 9,
    10301: 3, 10302: 10,
    10401: 4, 10402: 11, 10403: 21,
    10501: 5, 10502: 12, 10503: 25,
    10601: 6, 10602: 13, 10603: 26,
    10701: 7, 10702: 14,
    10801: 17, 10802: 18,
    10901: 19, 10902: 20,
    11001: 22, 11002: 23,
    20101: 27,
}

# The client-side CardCfgSteam table marks these as the three cards granted to
# a new account.  They are valid for every owned hero even when the hero's
# persisted unlockCard list is empty.
DEFAULT_UNLOCK_CARDS = {1, 3, 4}

# CardCfgSteam -> ItemBaseSteam mapping reconstructed from the shipped config.
# These are the real one-use unlock tokens consumed by GamerCardUnlockC2S
# (typ=2), not the card_cfg ids used by GamerCardReadyC2S.
CARD_UNLOCK_ITEM = {
    1: 201000,
    3: 201001,
    4: 201002,
    8: 201004,
    9: 201005,
    11: 201006,
    19: 201007,
    22: 201008,
    29: 201009,
    30: 201010,
    31: 201011,
    21: 201012,
    33: 201013,
    34: 201014,
}

# CardCfgSteam.hall_price for the same card ids.  Values are exact config
# ItemConfig(id, number) pairs; cards absent from this table are not silently
# assigned a made-up price.
CARD_CURRENCY_COST = {
    8: (102000, 18_000),
    9: (102000, 18_000),
    11: (102000, 18_000),
    19: (101000, 36_000),
    21: (102000, 12_000),
    22: (102000, 14_000),
    29: (102000, 14_000),
    30: (102000, 18_000),
    31: (102000, 24_000),
    33: (103000, 100),
    34: (103000, 100),
}

# The same rows expose these unlock conditions in the card library.  Keep
# them as gates when the request uses either payment method; this prevents an
# item token from bypassing a real hero/home progression rule.
CARD_UNLOCK_REQUIREMENTS = {
    8: (2, 20), 9: (4, 30), 11: (2, 30), 19: (2, 30),
    21: (4, 55), 22: (4, 65), 29: (2, 20), 30: (4, 55),
    31: (4, 75), 33: (2, 30), 34: (2, 30),
}

# ItemBaseSteam use_result_value points the two purple bag boxes at
# TreasureBoxCfgSteam ids 20 and 21.  The corresponding treasure rows both
# require the configured key item 10001000 (24 units per box).  Their first
# deterministic award is taken from TreasureBoxAwardCfgSteam; this is kept
# separate from the exploration-box ids 701265/10001004 handled below.
TREASURE_BOX_USE = {
    701176: {"treasureId": 20, "awardId": 701067},
    701177: {"treasureId": 21, "awardId": 701068},
}
TREASURE_BOX_KEY_ID = 10001000
TREASURE_BOX_KEY_COUNT = {20: 24, 21: 24}

# The first-stage home-box awards are themselves hidden ``OPEN_BOX_TYPE``
# items.  Their ``use_result_value`` points to these Steam drop tables.  The
# rows below are decoded from ``drop_something_steam.bytes``; a tuple is
# ``(item id, quantity, weight)``.  Keeping the table data here makes the
# server's random step auditable instead of silently turning every package
# into a guessed reward.
_HOME_DROP_COIN_VALUES = {
    16: (240, 480, 720, 960),
    17: (300, 600, 900, 1200),
    18: (360, 720, 1080, 1440),
    19: (420, 840, 1260, 1680),
    20: (480, 960, 1440, 1920),
    21: (540, 1080, 1620, 2160),
    22: (1050, 2100, 3150, 4200),
    23: (1300, 2600, 3910, 5210),
    24: (1550, 3110, 4660, 6220),
    25: (1810, 3610, 5420, 7220),
    26: (2060, 4120, 6170, 8230),
    27: (2310, 4620, 6930, 9240),
    28: (2700, 5400, 8100, 10800),
    29: (3170, 6340, 9500, 12670),
    30: (3640, 7270, 10910, 14540),
    31: (4100, 8210, 12310, 16420),
    32: (4570, 9140, 13720, 18290),
    33: (5040, 10080, 15120, 20160),
    34: (5250, 10500, 15750, 21000),
    35: (6000, 12000, 18000, 24000),
    36: (6750, 13500, 20250, 27000),
    37: (7500, 15000, 22500, 30000),
    38: (8250, 16500, 24750, 33000),
    39: (9000, 18000, 27000, 36000),
}
_HOME_DROP_PACKAGE = {drop_id: 701024 + (drop_id - 16) for drop_id in range(16, 40)}
CONTENT_PACKAGE_TO_DROP = {
    701048 + offset: 16 + offset for offset in range(24)
}
CONTENT_PACKAGE_TO_DROP.update({701072: 49, 701073: 45, 701074: 46, 701075: 47, 701076: 48})
# ExploreBoxCfgSteam.box_award items are direct-use items (use_result_type
# 20).  Their use_result_value points at these four shipped drop tables.
CONTENT_PACKAGE_TO_DROP.update({
    701220: 116,
    701231: 127,
    701242: 138,
    701253: 149,
})
_HOME_DROP_TABLES: dict[int, tuple[tuple[int, int, int], ...]] = {
    drop_id: (
        ((package_id, 1, 10_000),)
        + tuple((101000, amount, 2_500) for amount in coin_values)
    )
    for drop_id, package_id in _HOME_DROP_PACKAGE.items()
    for coin_values in (_HOME_DROP_COIN_VALUES[drop_id],)
}
_HOME_DROP_TABLES.update(
    {
        45: ((108000, 3, 10_000), (108001, 3, 10_000), (108002, 1, 10_000), (101000, 1688, 10_000)),
        46: ((108000, 4, 10_000), (108001, 1, 10_000), (108002, 1, 10_000), (101000, 2954, 10_000)),
        47: ((108000, 2, 10_000), (108001, 2, 10_000), (108002, 2, 10_000), (101000, 899, 10_000)),
        48: ((108000, 1, 10_000), (108001, 4, 10_000), (108002, 1, 10_000), (101000, 2721, 10_000)),
        49: ((701073, 1, 2_500), (701074, 1, 2_500), (701075, 1, 2_500), (701076, 1, 2_500), (108001, 10, 10_000)),
        # Exploration box awards from ExploreBoxCfgSteam.  These rows are
        # intentionally kept as shipped: the purple/orange/red regular
        # awards are fixed coin drops, while the blue award is a character
        # package.  No extra reward chance is invented here.
        116: ((701039, 1, 10_000),),
        127: ((101000, 5_040, 2_500),),
        138: ((101000, 12_000, 2_500),),
        149: ((101000, 22_500, 2_500),),
    }
)

# ``701024..701047`` are the old home-chain random-character packages.  The
# first two values are the inclusive character-count range in ItemBaseSteam;
# the third value is zero for this historical chain.  For that chain the
# shipped Steam HeroBadgeRandomCfg table exposes the non-zero ``random``
# weights for seven level-0 heroes.  The newer 701077+ variants use a
# different selector field and remain intentionally unsupported until their
# server-side rule is observed.
RANDOM_CHARACTER_RANGES = {
    # The special level-25 home row awards 701000.  The preceding 701001..
    # 701023 rows are retained as compatible historical items as well; all
    # carry the same third value (zero) and therefore use this selector.
    701000: (1, 3), 701001: (2, 3), 701002: (2, 4), 701003: (2, 5),
    701004: (3, 5), 701005: (3, 6), 701006: (7, 13), 701007: (9, 16),
    701008: (10, 19), 701009: (12, 22), 701010: (14, 25), 701011: (15, 29),
    701012: (21, 39), 701013: (25, 46), 701014: (28, 53), 701015: (32, 59),
    701016: (36, 66), 701017: (39, 73), 701018: (56, 84), 701019: (64, 96),
    701020: (72, 108), 701021: (80, 120), 701022: (88, 132), 701023: (96, 144),
    701024: (0, 1), 701025: (1, 1), 701026: (1, 2), 701027: (1, 2),
    701028: (1, 2), 701029: (1, 3), 701030: (3, 6), 701031: (4, 8),
    701032: (5, 9), 701033: (6, 11), 701034: (7, 12), 701035: (7, 14),
    701036: (10, 19), 701037: (12, 13), 701038: (14, 26), 701039: (16, 29),
    701040: (18, 33), 701041: (19, 36), 701042: (28, 42), 701043: (32, 48),
    701044: (36, 54), 701045: (40, 60), 701046: (44, 66), 701047: (48, 72),
}
HERO_BADGE_LEVEL0 = {
    0: 601000, 1: 601100, 13: 601200, 14: 601300,
    15: 601400, 16: 601500, 17: 601600,
}
_HOME_CHARACTER_WEIGHTS = (
    (0, 500), (1, 4_000), (13, 4_000), (14, 500),
    (15, 500), (16, 250), (17, 250),
)

# TreasureBoxCfgSteam rows 1-24 form four six-box tiers.  The values below
# are decoded directly from the bundle (sell reward, instant-open value and
# opening-key cost).  TreasureBoxAwardCfgSteam maps each row to the matching
# 701048..701071 random-package item; package resolution remains a separate
# bag operation.
_HOME_BOX_SELL = (
    2_000, 2_500, 3_500, 4_000, 4_500, 5_000,
    10_500, 13_500, 16_500, 19_500, 22_000, 25_000,
    32_000, 36_500, 44_500, 50_500, 57_500, 64_000,
    74_000, 86_000, 98_000, 110_500, 123_500, 136_500,
)
_HOME_BOX_TIER = (
    (1, 3_600, 3_500, 1),
    (2, 18_000, 17_000, 5),
    (3, 43_200, 45_600, 12),
    (4, 86_400, 100_000, 24),
)
HOME_TREASURE_BOX_CONFIG: dict[int, dict[str, int]] = {}
for _box_id in range(1, 25):
    _tier_index = (_box_id - 1) // 6
    _tier_level, _open_time, _box_value, _key_count = _HOME_BOX_TIER[_tier_index]
    HOME_TREASURE_BOX_CONFIG[_box_id] = {
        "level": _tier_level,
        "type": 1,
        "openTime": _open_time,
        "sellId": 101000,
        "sellCount": _HOME_BOX_SELL[_box_id - 1],
        "valueId": 101000,
        "valueCount": _box_value,
        "keyId": TREASURE_BOX_KEY_ID,
        "keyCount": _key_count,
        "awardId": 701047 + _box_id,
    }
HOME_TREASURE_BOX_CONFIG[25] = {
    "level": 3,
    "type": 2,
    "openTime": 21_600,
    "sellId": 101000,
    "sellCount": 21_600,
    "valueId": 101000,
    "valueCount": 21_600,
    "keyId": TREASURE_BOX_KEY_ID,
    "keyCount": 6,
    # Award row 25 targets package item 701000, unlike rows 1-24.
    "awardId": 701000,
}
del _box_id, _tier_index, _tier_level, _open_time, _box_value, _key_count


def pvp_appearance(inventory: dict, hero_id: int, gun_id: int) -> tuple[int, int, int, int]:
    hero_fashion = HERO_BASE_FASHION.get(hero_id, 101)
    gun_fashion = GUN_BASE_FASHION.get(gun_id, 10101)
    for equipped in inventory.get("equippedSkins", []):
        target = int(equipped.get("targetId", -1))
        fashion_type = int(equipped.get("type", 0))
        if fashion_type == 1 and target == hero_id:
            hero_fashion = int(equipped.get("fashionId", hero_fashion))
        elif fashion_type == 2 and target == gun_id:
            gun_fashion = int(equipped.get("fashionId", gun_fashion))
    hero_default = HERO_BASE_FASHION.get(hero_id, 101)
    gun_default = GUN_BASE_FASHION.get(gun_id, 10101)
    hero_model = FASHION_MODEL.get(hero_fashion, FASHION_MODEL[hero_default])
    gun_model = FASHION_MODEL.get(gun_fashion, FASHION_MODEL[gun_default])
    return hero_model, hero_fashion, gun_model, gun_fashion


@dataclass
class LocalAccount:
    name: str
    gid: int
    session: str
    created_at: int = field(default_factory=lambda: int(time.time()))


class GameState:
    bot_difficulty: str = "scripted"
    bot_seed: int | None = None
    def __init__(self, pvp_port: int, inventory_path: Path, pkg_version_path: Path) -> None:
        self._lock = threading.Lock()
        self._accounts: dict[str, LocalAccount] = {}
        self._next_gid = 1000001
        self.pvp_port = pvp_port
        # Tests keep reproducible snapshots; the launched local server uses
        # randomized full-capacity reloads within the copied gun cfg bounds.
        self.randomize_magazines = False
        # Legacy policy is restricted to deterministic packet regression tests.
        self.bot_difficulty = "scripted"
        self.bot_seed: int | None = None
        self.inventory_path = inventory_path
        self.inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
        self.pkg_version_path = pkg_version_path
        # The bundled season is historical, but the client uses server time
        # for cooldowns.  A fixed heartbeat timestamp repeatedly rewinds its
        # clock and can permanently suppress a box-award request.
        self._clock_epoch = season_state(self.inventory)["serverTime"]
        self._clock_monotonic = time.monotonic()
        if not self.pkg_version_path.is_file():
            raise FileNotFoundError(f"PkgVersion not found: {self.pkg_version_path}")

    def server_time(self) -> int:
        """Advance the local season clock without using the real 2026 date."""
        return self._clock_epoch + max(
            0, int(time.monotonic() - self._clock_monotonic)
        )

    def timed_inventory(self, server_time: int | None = None) -> dict:
        """Give protocol builders one coherent clock without saving it."""
        return {
            **self.inventory,
            "serverTime": self.server_time() if server_time is None else server_time,
        }

    def account_for(self, name: str) -> LocalAccount:
        clean_name = (name or "local").strip()[:32] or "local"
        with self._lock:
            account = self._accounts.get(clean_name.casefold())
            if account is None:
                gid = self._next_gid
                self._next_gid += 1
                digest = hashlib.sha256(clean_name.casefold().encode()).hexdigest()[:16]
                account = LocalAccount(clean_name, gid, f"local-session-{digest}")
                self._accounts[clean_name.casefold()] = account
            return account

    def account_for_gid(self, gid: int) -> LocalAccount:
        with self._lock:
            for account in self._accounts.values():
                if account.gid == gid:
                    return account
        return self.account_for("local")

    def currency(self, item_id: int, default: int = 9_999_999) -> int:
        for item in self.inventory.get("items", []):
            if int(item.get("id", -1)) == item_id:
                return int(item.get("number", default))
        return default

    def clan_ids(self, account):
        # Stable member keys are account names, never recycled transient gids.
        names = {account.name.casefold()}
        for team in clan_database(self.inventory)['teams'].values():
            names.update(m['account'] for m in team['members'])
        return {name: self.account_for(name).gid for name in names}

    def profile_for(self, account):
        with self._lock:
            before = copy.deepcopy(self.inventory)
            try:
                value = ensure_profile(self.inventory, account.name.casefold(),
                    'Local Hunter' if account.name.casefold() == 'local' else account.name)
                if self.inventory != before:
                    self._save_inventory_locked()
                return projected_profile(copy.deepcopy(value), self.server_time())
            except (ProfileError, OSError):
                self.inventory = before
                raise

    def equip_accessory(self, account, accessory_id):
        with self._lock:
            before = copy.deepcopy(self.inventory)
            try:
                value = ensure_profile(self.inventory, account.name.casefold(),
                    'Local Hunter' if account.name.casefold() == 'local' else account.name)
                equip_profile(value, accessory_id)
                # Keep the Clan member's public avatar/name consistent too.
                for team in self.inventory.get('clanLab', {}).get('teams', {}).values():
                    for member in team['members']:
                        if member['key'] == account.name.casefold():
                            member['icon'] = value['icon']
                            member['display'] = value['name']
                if self.inventory != before:
                    self._save_inventory_locked()
                return copy.deepcopy(value)
            except (ProfileError, OSError):
                self.inventory = before
                raise

    def rename_player(self, account, raw):
        with self._lock:
            before = copy.deepcopy(self.inventory)
            try:
                clan_database(self.inventory)  # Validate before committing a cross-profile/clan change.
                ensure_profile(self.inventory, account.name.casefold(),
                    'Local Hunter' if account.name.casefold() == 'local' else account.name)
                result, value = rename_profile(self.inventory, account.name.casefold(), raw, self.server_time())
                self._save_inventory_locked()
                return result, copy.deepcopy(value)
            except (ProfileError, ClanError, OSError):
                self.inventory = before
                raise

    def clan_login(self, account):
        ids = self.clan_ids(account)
        with self._lock:
            return clan_snapshot(self.inventory, account.name.casefold(), ids)

    def handle_clan(self, account, act, body):
        ids = self.clan_ids(account)
        now = self.server_time()
        with self._lock:
            before = copy.deepcopy(self.inventory)
            try:
                result, notifications, changed = clan_request(self.inventory, account.name.casefold(),
                    account.gid, ids, act, body, now,
                    self.inventory.get('profileLab',{}).get('accounts',{}).get(account.name.casefold(),{}).get(
                        'name','Local Hunter' if account.name == 'local' else account.name))
                if changed:
                    self._save_inventory_locked()
                return result, notifications
            except (ClanError, OSError):
                self.inventory = before
                raise

    def _find_item_locked(self, item_id: int) -> dict | None:
        return next(
            (
                item
                for item in self.inventory.setdefault("items", [])
                if int(item.get("id", -1)) == item_id
            ),
            None,
        )

    def _item_number_locked(self, item_id: int) -> int:
        item = self._find_item_locked(item_id)
        return int(item.get("number", 0)) if item is not None else 0

    def _set_item_locked(self, item_id: int, number: int) -> int:
        """Set an ItemGood quantity, removing zero entries like the client."""
        number = max(0, int(number))
        item = self._find_item_locked(item_id)
        if number == 0:
            if item is not None:
                self.inventory["items"].remove(item)
            return 0
        if item is None:
            self.inventory.setdefault("items", []).append(
                {"id": int(item_id), "number": number}
            )
        else:
            item["number"] = number
        return number

    def _adjust_item_locked(self, item_id: int, delta: int) -> int:
        return self._set_item_locked(
            item_id,
            self._item_number_locked(item_id) + int(delta),
        )

    def _save_inventory_locked(self) -> None:
        temporary = self.inventory_path.with_suffix(self.inventory_path.suffix + ".tmp")
        temporary.write_text(
            json.dumps(self.inventory, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        temporary.replace(self.inventory_path)

    def select_hero(self, hero_id: int) -> bool:
        valid_ids = {int(hero["id"]) for hero in self.inventory.get("heroes", [])}
        if hero_id not in valid_ids:
            return False
        with self._lock:
            self.inventory["selectedHero"] = hero_id
            self._save_inventory_locked()
        return True

    def equip_fashion(self, target_id: int, fashion_id: int, fashion_type: int) -> bool:
        if fashion_id <= 0 or target_id < 0 or fashion_type not in {1, 2}:
            return False
        with self._lock:
            valid_heroes = {
                int(hero.get("id", -1)) for hero in self.inventory.get("heroes", [])
            }
            valid_guns = {
                int(gun.get("id", -1)) for gun in self.inventory.get("guns", [])
            }
            owned_fashions = {
                int(fashion.get("id", -1))
                for fashion in self.inventory.get("skins", [])
            }
            # FashionType is an enum (1=hero, 2=gun).  The shipped config uses
            # three/four digit ids for hero skins, five digit ids for gun skins,
            # plus the legacy gun base rows 11/21.  Rejecting a type mismatch
            # avoids persisting a selection the Lua window can never render.
            fashion_is_gun = fashion_id >= 10_000 or fashion_id in {11, 21}
            if fashion_id not in owned_fashions:
                return False
            if fashion_type == 1 and (target_id not in valid_heroes or fashion_is_gun):
                return False
            if fashion_type == 2 and (target_id not in valid_guns or not fashion_is_gun):
                return False
            equipped = self.inventory.setdefault("equippedSkins", [])
            equipped[:] = [
                item
                for item in equipped
                if not (
                    int(item.get("targetId", -1)) == target_id
                    and int(item.get("type", 1)) == fashion_type
                )
            ]
            equipped.append(
                {"targetId": target_id, "fashionId": fashion_id, "type": fashion_type}
            )
            self._save_inventory_locked()
        return True

    def carry_gun(self, hero_id: int, gun_id: int) -> bool:
        valid_heroes = {int(hero["id"]) for hero in self.inventory.get("heroes", [])}
        valid_guns = {int(gun["id"]) for gun in self.inventory.get("guns", [])}
        if hero_id not in valid_heroes or gun_id not in valid_guns:
            return False
        with self._lock:
            hero_guns = self.inventory.setdefault("heroGuns", [])
            for entry in hero_guns:
                if int(entry.get("heroId", -1)) == hero_id:
                    entry["gunId"] = gun_id
                    break
            else:
                hero_guns.append({"heroId": hero_id, "gunId": gun_id})
            self._save_inventory_locked()
        return True

    def equip_card(self, hero_id: int, card_id: int) -> dict | None:
        if card_id <= 0:
            return None
        with self._lock:
            hero = next(
                (
                    entry
                    for entry in self.inventory.get("heroes", [])
                    if int(entry.get("id", -1)) == hero_id
                ),
                None,
            )
            if hero is None:
                return None
            unlocked = hero.setdefault("unlockCards", [])
            # GamerCardReadyC2S only equips a card that the client already
            # considers unlocked.  The old prototype silently unlocked any
            # positive id here, which made a failed/locked selection appear
            # equipped until the next login.  Default cards are granted by
            # CardCfgSteam even if the per-hero list is omitted.
            if card_id not in unlocked and card_id not in DEFAULT_UNLOCK_CARDS:
                return None
            hero["readyCard"] = card_id
            self._save_inventory_locked()
            return dict(hero)

    def unlock_card(
        self, hero_id: int, card_id: int, unlock_type: int
    ) -> tuple[dict, list[dict]] | None:
        """Unlock a configured card using its real item token or currency.

        The wire request uses typ=1 for currency and typ=2 for the dedicated
        unlock token.  Both response paths return absolute ItemData quantities
        plus the complete updated hero, matching GamerCardUnlockS2C.
        """
        if card_id <= 0 or unlock_type not in {1, 2}:
            return None
        with self._lock:
            hero = next(
                (
                    entry
                    for entry in self.inventory.get("heroes", [])
                    if int(entry.get("id", -1)) == hero_id
                ),
                None,
            )
            if hero is None:
                return None
            unlocked = hero.setdefault("unlockCards", [])
            if card_id in unlocked or card_id in DEFAULT_UNLOCK_CARDS:
                return None

            required_star, required_home = CARD_UNLOCK_REQUIREMENTS.get(
                card_id, (0, 0)
            )
            if int(hero.get("starLevel", 0)) < required_star:
                return None
            if int(self.inventory.get("homeLevel", 0)) < required_home:
                return None

            if unlock_type == 2:
                cost_id = CARD_UNLOCK_ITEM.get(card_id)
                cost_count = 1
            else:
                configured_cost = CARD_CURRENCY_COST.get(card_id)
                if configured_cost is None:
                    return None
                cost_id, cost_count = configured_cost

            if self._item_number_locked(cost_id) < cost_count:
                return None
            cost_number = self._adjust_item_locked(cost_id, -cost_count)
            unlocked.append(card_id)
            unlocked.sort()
            self._save_inventory_locked()
            return dict(hero), [{"id": cost_id, "number": cost_number}]

    @staticmethod
    def _weighted_drop(
        entries: tuple[tuple[int, int, int], ...],
    ) -> tuple[int, int] | None:
        """Choose one decoded drop row using its integer probability weight."""
        total = sum(max(0, int(row[2])) for row in entries)
        if total <= 0:
            return None
        roll = random.randrange(total)
        cursor = 0
        for item_id, quantity, weight in entries:
            cursor += max(0, int(weight))
            if roll < cursor:
                return int(item_id), int(quantity)
        return None

    def _find_badge_locked(self, badge_id: int) -> dict | None:
        return next(
            (
                badge
                for badge in self.inventory.setdefault("badges", [])
                if int(badge.get("id", -1)) == int(badge_id)
            ),
            None,
        )

    def _badge_number_locked(self, badge_id: int) -> int:
        badge = self._find_badge_locked(badge_id)
        if badge is not None:
            return int(badge.get("number", 0))
        # A few older lab snapshots stored badge ItemData in the ordinary
        # item list.  Read that shape as a compatibility fallback; the setter
        # below migrates it to the dedicated login ``badge`` repeated field.
        item = self._find_item_locked(badge_id)
        return int(item.get("number", 0)) if item is not None else 0

    def _set_badge_locked(self, badge_id: int, number: int) -> int:
        number = max(0, int(number))
        badges = self.inventory.setdefault("badges", [])
        badge = self._find_badge_locked(badge_id)
        if number == 0:
            if badge is not None:
                badges.remove(badge)
        elif badge is None:
            badges.append({"id": int(badge_id), "number": number})
        else:
            badge["number"] = number
        # Never leave a badge duplicated as a normal ItemGood: GamerBag.Init
        # handles the two protobuf collections through different code paths.
        item = self._find_item_locked(badge_id)
        if item is not None:
            self.inventory.setdefault("items", []).remove(item)
        return number

    def _adjust_badge_locked(self, badge_id: int, delta: int) -> int:
        return self._set_badge_locked(
            badge_id,
            self._badge_number_locked(badge_id) + int(delta),
        )

    def use_box_content_package(self, item_id: int, count: int) -> dict | None:
        """Resolve one of the decoded hidden home/drop packages.

        The returned ``cost`` and ``award`` quantities are absolute, matching
        ``GamerUseGoodsS2C``.  One package is consumed per request unit and
        each package performs one weighted draw from its shipped drop table.
        """
        drop_id = CONTENT_PACKAGE_TO_DROP.get(int(item_id))
        if drop_id is None:
            return None
        count = max(1, min(int(count), 9999))
        with self._lock:
            before = self._item_number_locked(item_id)
            if before < count:
                return None
            deltas: dict[int, int] = {}
            table = _HOME_DROP_TABLES.get(drop_id)
            if not table:
                return None
            for _ in range(count):
                picked = self._weighted_drop(table)
                if picked is None:
                    return None
                reward_id, quantity = picked
                if quantity > 0:
                    deltas[reward_id] = deltas.get(reward_id, 0) + quantity
            source_after = self._set_item_locked(item_id, before - count)
            awards = []
            for reward_id, delta in sorted(deltas.items()):
                awards.append(
                    {
                        "id": reward_id,
                        "number": self._adjust_item_locked(reward_id, delta),
                        "chgNumber": delta,
                    }
                )
            self._save_inventory_locked()
        return {
            "cost": [{"id": int(item_id), "number": source_after}],
            "award": awards,
        }

    def use_random_character_package(self, item_id: int, count: int) -> dict | None:
        """Open the historical 701024..701047 character-count packages.

        These rows are the old home-chain variants (third ItemBase value is
        zero).  Their Steam random table has one non-zero ``random`` selector
        for seven level-0 hero badges.  The newer 701077+ packages use a
        separate selector field and are deliberately left for a later,
        evidence-backed pass.
        """
        bounds = RANDOM_CHARACTER_RANGES.get(int(item_id))
        if bounds is None:
            return None
        count = max(1, min(int(count), 9999))
        with self._lock:
            before = self._item_number_locked(item_id)
            if before < count:
                return None
            badge_deltas: dict[int, int] = {}
            selector = tuple((HERO_BADGE_LEVEL0[hero_id], 1, weight) for hero_id, weight in _HOME_CHARACTER_WEIGHTS)
            for _ in range(count):
                character_count = random.randint(int(bounds[0]), int(bounds[1]))
                for _ in range(max(0, character_count)):
                    picked = self._weighted_drop(selector)
                    if picked is None:
                        return None
                    badge_id, _ = picked
                    badge_deltas[badge_id] = badge_deltas.get(badge_id, 0) + 1
            source_after = self._set_item_locked(item_id, before - count)
            awards = []
            for badge_id, delta in sorted(badge_deltas.items()):
                awards.append(
                    {
                        "id": badge_id,
                        "number": self._adjust_badge_locked(badge_id, delta),
                        "chgNumber": delta,
                        "specialShow": True,
                    }
                )
            self._save_inventory_locked()
        return {
            "cost": [{"id": int(item_id), "number": source_after}],
            "award": awards,
        }

    def use_treasure_box(self, item_id: int, count: int) -> dict | None:
        """Open configured purple bag boxes and return absolute bag changes.

        The client sends GamerUseGoodsC2S for these items.  A transaction
        consumes the box itself plus its configured opening key, then emits
        GamerUseGoodsS2C cost ItemData and the absolute award quantity.  No
        weighted result is fabricated: only the first award row decoded from
        the shipped Steam treasure tables is used for each supported box.
        """
        config = TREASURE_BOX_USE.get(int(item_id))
        if config is None:
            return None
        count = max(1, min(int(count), 9999))
        treasure_id = int(config["treasureId"])
        award_id = int(config["awardId"])
        key_count = TREASURE_BOX_KEY_COUNT[treasure_id] * count
        with self._lock:
            box_before = self._item_number_locked(item_id)
            key_before = self._item_number_locked(TREASURE_BOX_KEY_ID)
            if box_before < count or key_before < key_count:
                return None
            box_after = self._set_item_locked(item_id, box_before - count)
            key_after = self._set_item_locked(
                TREASURE_BOX_KEY_ID, key_before - key_count
            )
            award_after = self._adjust_item_locked(award_id, count)
            self._save_inventory_locked()
        return {
            "cost": [
                {"id": int(item_id), "number": box_after},
                {"id": TREASURE_BOX_KEY_ID, "number": key_after},
            ],
            "award": [
                {"id": award_id, "number": award_after, "chgNumber": count}
            ],
        }

    @staticmethod
    def _home_remaining_seconds(
        box: dict, config: dict[str, int], now: int | None = None
    ) -> int:
        """Calculate the remaining timer using the client's box fields.

        ``openTime`` is the shipped duration in seconds.  ``openBoxTimeDec``
        and ``openBoxTimeDecTem`` are per-mille speed values, while
        ``boxTimeTemDec`` contains already-earned second reductions.  The
        optional time records are applied only for rates above the neutral
        1000 value; a neutral record must not make a box finish twice as fast.
        """
        if now is None:
            now = int(time.time())
        start = int(box.get("startTime", 0))
        if start <= 0:
            return int(config["openTime"])
        speed = max(1, int(box.get("openBoxTimeDec", 1000)))
        speed += max(0, int(box.get("openBoxTimeDecTem", 0)))
        total = float(config["openTime"]) * 1000.0 / speed
        elapsed = max(0, int(now) - start)
        elapsed += sum(max(0, int(value)) for value in box.get("boxTimeTemDec", []))
        for record in box.get("timeRecord", []):
            rate = max(1000, int(record.get("rate", 1000)))
            record_start = int(record.get("startTime", 0))
            if record_start <= 0:
                continue
            record_end = int(record.get("endTime", -1))
            if record_end <= 0:
                record_end = int(now)
            record_elapsed = max(0, record_end - record_start)
            elapsed += int(record_elapsed * (rate - 1000) / 1000)
        return max(0, int(math.ceil(total - elapsed)))

    def _home_slot_locked(self, index: int) -> dict | None:
        if index < 1 or index > 3:
            return None
        return next(
            (
                entry
                for entry in self.inventory.setdefault("treasureBoxes", [])
                if int(entry.get("index", 0)) == index
            ),
            None,
        )

    def start_home_box(
        self,
        index: int,
        way_to_save: int = 0,
        open_cost_item: int = 0,
        open_cost_num: int = 0,
    ) -> dict | None:
        """Move the temporary home box into one of the three real slots."""
        index = int(index)
        way_to_save = int(way_to_save)
        open_cost_item = int(open_cost_item)
        open_cost_num = max(0, int(open_cost_num))
        with self._lock:
            slot = self._home_slot_locked(index)
            temporary_id = int(self.inventory.get("temporaryBoxId", -1))
            config = HOME_TREASURE_BOX_CONFIG.get(temporary_id)
            if slot is None or int(slot.get("status", 0)) == 0 or config is None:
                return None
            current_id = int(slot.get("boxId", -1))
            # The client defines wayToSave=2 as discard-old and =3 as
            # open-old.  We do not yet have the separate award/notification
            # contract for =3, so never replace a running box through that
            # path; accepting it would silently lose a persisted reward.
            if current_id >= 0 and way_to_save != 2:
                return None
            if open_cost_num:
                if open_cost_item <= 0 or self._item_number_locked(open_cost_item) < open_cost_num:
                    return None
                cost_number = self._adjust_item_locked(open_cost_item, -open_cost_num)
                cost = [{"id": open_cost_item, "number": cost_number}]
            else:
                cost = []
            slot.clear()
            slot.update(
                {
                    "index": index,
                    "openBoxTimeDec": 1000,
                    "openBoxTimeDecTem": 0,
                    "boxId": temporary_id,
                    "startTime": int(time.time()),
                    "boxTimeTemDec": [],
                    "status": 1,
                    "timeRecord": [],
                }
            )
            self.inventory["temporaryBoxId"] = -1
            self._save_inventory_locked()
            return {"boxes": [dict(entry) for entry in self.inventory.get("treasureBoxes", [])], "cost": cost}

    def open_home_box(
        self, index: int, open_type: int, gid: int = 0
    ) -> dict | None:
        """Open a finished home slot or pay to open it immediately.

        OpenType is the shipped enum: 1=direct, 2=currency, 3=key/item.
        ``index == 0`` selects the temporary box used by the separate
        temporary-open command.
        """
        index = int(index)
        open_type = int(open_type)
        with self._lock:
            if index == 0:
                box_id = int(self.inventory.get("temporaryBoxId", -1))
                box = None
            else:
                box = self._home_slot_locked(index)
                box_id = int(box.get("boxId", -1)) if box is not None else -1
            config = HOME_TREASURE_BOX_CONFIG.get(box_id)
            if config is None:
                return None
            # A temporary box has not entered a timed slot yet.  The client
            # still offers the immediate money/key paths, whose cost is the
            # full configured open cost; only a slot can be opened directly
            # after its timer reaches zero.
            remaining = int(config["openTime"]) if index == 0 else self._home_remaining_seconds(box, config)
            cost: list[dict] = []
            if open_type == 1:
                if index == 0 or remaining > 0:
                    return None
            elif open_type in {2, 3}:
                if open_type == 2:
                    cost_id = int(config["valueId"])
                    full_cost = int(config["valueCount"])
                else:
                    cost_id = int(config["keyId"])
                    full_cost = int(config["keyCount"])
                cost_count = int(math.ceil(remaining * full_cost / config["openTime"])) if remaining else 0
                if cost_count:
                    if self._item_number_locked(cost_id) < cost_count:
                        return None
                    cost_number = self._adjust_item_locked(cost_id, -cost_count)
                    cost = [{"id": cost_id, "number": cost_number}]
            else:
                return None

            award_id = int(config["awardId"])
            award_number = self._adjust_item_locked(award_id, 1)
            if index == 0:
                self.inventory["temporaryBoxId"] = -1
            else:
                box.clear()
                box.update(
                    {
                        "index": index,
                        "openBoxTimeDec": 1000,
                        "openBoxTimeDecTem": 0,
                        "boxId": -1,
                        "startTime": 0,
                        "boxTimeTemDec": [],
                        "status": 1,
                        "timeRecord": [],
                    }
                )
            self._save_inventory_locked()
            return {
                "gid": int(gid),
                "box": dict(box) if box is not None else None,
                "cost": cost,
                "award": [{"id": award_id, "number": award_number, "chgNumber": 1}],
            }

    def sell_temporary_home_box(self) -> list[dict] | None:
        """Sell the unopened temporary box for its configured reward."""
        with self._lock:
            box_id = int(self.inventory.get("temporaryBoxId", -1))
            config = HOME_TREASURE_BOX_CONFIG.get(box_id)
            if config is None:
                return None
            reward_id = int(config["sellId"])
            reward_number = self._adjust_item_locked(reward_id, int(config["sellCount"]))
            self.inventory["temporaryBoxId"] = -1
            self._save_inventory_locked()
            return [
                {
                    "id": reward_id,
                    "number": reward_number,
                    "chgNumber": int(config["sellCount"]),
                }
            ]

    def collect_home_income(self) -> list[dict]:
        """Collect explicitly persisted passive-income entries, if present.

        The client stores ``income`` as a per-minute rate multiplied by 1000
        and only turns the two home currencies into rewards: Fight Coin
        (101000) and RCoin (102000).  Entries are consumed in order, with the
        configured maximum duration applied independently per currency.  The
        protocol only carries the resulting ItemData, so unknown income rows
        remain untouched instead of being guessed into rewards.
        """
        with self._lock:
            entries = self.inventory.get("currentIncome", [])
            if not isinstance(entries, list):
                return []
            now = int(time.time())
            last_claim = int(self.inventory.get("getIncomeTime", 0) or 0)
            interval = max(0, int(self.inventory.get("homeIncomeInterTime", 0) or 0))
            if interval and last_claim and now - last_claim < interval:
                return []
            allowed_items = {101000, 102000}
            awards: dict[int, int] = {}
            remaining_by_item: dict[int, int] = {}
            for entry in entries:
                if not isinstance(entry, dict):
                    continue
                try:
                    item_id = int(entry.get("itemId", 0))
                    rate = int(entry.get("income", 0))
                    start = int(entry.get("startTime", self.inventory.get("getIncomeTime", now)))
                except (TypeError, ValueError):
                    continue
                if item_id not in allowed_items or rate <= 0:
                    continue
                end = int(entry.get("endTime", -1))
                elapsed = max(0, (min(now, end) if end > 0 else now) - start)
                try:
                    configured_cap = int(
                        entry.get(
                            "maxDuration",
                            self.inventory.get("homeIncomeMaxDuration", 86_400),
                        )
                    )
                except (TypeError, ValueError):
                    configured_cap = 86_400
                configured_cap = max(0, configured_cap)
                remaining = remaining_by_item.setdefault(item_id, configured_cap)
                elapsed = min(elapsed, remaining)
                remaining_by_item[item_id] = max(0, remaining - elapsed)
                # Lua: floor(durationSec * income / 1000 / 60).
                amount = (elapsed * rate) // 60_000
                if amount > 0:
                    awards[item_id] = awards.get(item_id, 0) + amount
            if not awards:
                return []
            result = [
                {
                    "id": item_id,
                    "number": self._adjust_item_locked(item_id, amount),
                    "chgNumber": amount,
                }
                for item_id, amount in sorted(awards.items())
            ]
            self.inventory["getIncomeTime"] = now
            for entry in entries:
                if isinstance(entry, dict):
                    entry["startTime"] = now
            self._save_inventory_locked()
            return result

    def buy_supply_boxes(self, shop_item_id: int, count: int) -> dict | None:
        """Buy one of the shipped Steam exploration-box products.

        14500000 and 14500001 were previously logged as unsupported, so the
        client showed a successful shop click without receiving a box.  The
        three rows are real products: the first two grant blue pack item
        701264 (pack id 1), while 14500002 grants purple pack item 701265
        (pack id 12).  ``GamerBuyInMarketS2C`` needs both the absolute bag
        quantity and the absolute currency quantity.
        """
        config = EXPLORE_BOX_SHOP.get(int(shop_item_id))
        if config is None:
            return None
        count = max(1, min(int(count), 9999))
        with self._lock:
            cost_id = int(config["currency_id"])
            total_cost = int(config["unit_price"]) * count
            if self._item_number_locked(cost_id) < total_cost:
                return None
            cost_number = self._adjust_item_locked(cost_id, -total_cost)
            award_id = int(config["award_id"])
            award_number = self._adjust_item_locked(award_id, count)
            pack = self.inventory.setdefault("exploreBoxPack", [])
            for item in pack:
                if int(item.get("id", -1)) == int(config["pack_id"]):
                    item["number"] = int(item.get("number", 0)) + count
                    total = int(item["number"])
                    break
            else:
                pack.append({"id": int(config["pack_id"]), "number": count})
                total = count
            self._save_inventory_locked()
        return {
            "cost": [{"id": cost_id, "number": cost_number}],
            "award": [{"id": award_id, "number": award_number, "chgNumber": count}],
            "packId": int(config["pack_id"]),
            "packNumber": total,
        }

    def extract_supply_box(self, quality: int) -> bool:
        # ExploreBoxExtractSteam maps the selected quality to a level-zero
        # box.  Keep this deterministic regular row for the offline server;
        # the resulting quality-upgrade chance is resolved at open time from
        # ExploreBoxUpCfgSteam.
        box_id = EXPLORE_BOX_BASE_BY_QUALITY.get(int(quality))
        if box_id is None:
            return False
        with self._lock:
            pack = self.inventory.setdefault("exploreBoxPack", [])
            item = next(
                (
                    entry
                    for entry in pack
                    if int(entry.get("id", -1)) == box_id
                    and int(entry.get("number", 0)) > 0
                ),
                None,
            )
            if item is None:
                return False
            cells = self.inventory.setdefault("exploreCells", [])
            # The client keeps completed cells in the 11-cell grid with
            # ``chest == 0``.  They are reusable storage locations; only a
            # cell that still contains an active chest occupies its slot.
            active_ids = {
                int(cell.get("id", 0))
                for cell in cells
                if int(cell.get("chest", 0)) > 0
            }
            cell_id = next((value for value in range(1, 12) if value not in active_ids), None)
            if cell_id is None:
                return False
            item["number"] = int(item["number"]) - 1
            recycled = next(
                (cell for cell in cells if int(cell.get("id", 0)) == cell_id),
                None,
            )
            if recycled is None:
                cells.append({"id": cell_id, "chest": box_id})
            else:
                recycled.clear()
                recycled.update({"id": cell_id, "chest": box_id})
            self._save_inventory_locked()
        return True

    @staticmethod
    def _explore_box_quality_level(chest_id: int) -> tuple[int, int] | None:
        """Return (quality, level) for a supported ExploreBoxCfgSteam id."""
        for quality, base_id in EXPLORE_BOX_BASE_BY_QUALITY.items():
            level = int(chest_id) - base_id
            if 0 <= level <= 10:
                return quality, level
        return EXPLORE_BOX_SPECIAL_QUALITY_LEVEL.get(int(chest_id))

    @staticmethod
    def _pick_explore_box_quality(start_quality: int) -> tuple[int, int]:
        """Pick (final_quality, number_of_quality_upgrade_shots)."""
        rows = EXPLORE_BOX_QUALITY_UPGRADE.get(int(start_quality))
        if not rows:
            return int(start_quality), 0
        total_weight = sum(weight for _, _, weight in rows)
        draw = random.randint(1, total_weight)
        cursor = 0
        for final_quality, ammo_num, weight in rows:
            cursor += weight
            if draw <= cursor:
                return final_quality, ammo_num
        final_quality, ammo_num, _ = rows[-1]
        return final_quality, ammo_num

    def open_supply_box(
        self,
        cell_id: int | None = None,
        *,
        max_cells: int | None = None,
        replay_pending: bool = False,
    ) -> list[dict]:
        """Resolve a box into the official five-shot opening sequence.

        The Cell event enum defines 1 as no upgrade and 2 as a quality
        upgrade.  Final quality is selected with the exact weighted rows from
        ExploreBoxUpCfgSteam; the event list contains the matching number of
        quality-upgrade shots so the client animation and final chest agree.

        ``replay_pending`` is a recovery path for a client that disconnected
        after receiving ``OpenAll`` but before sending ``GetAwardAll``.  It
        replays the pending cells without charging ammo a second time.
        """
        with self._lock:
            cells = self.inventory.setdefault("exploreCells", [])
            pending = [
                cell
                for cell in cells
                if int(cell.get("chest", 0)) > 0
                and cell.get("event")
                and self._explore_box_quality_level(int(cell.get("chest", 0)))
                is not None
                and int(cell.get("chest", 0)) in EXPLORE_BOX_REWARD_BY_CHEST
                and (cell_id is None or int(cell.get("id", 0)) == cell_id)
            ]
            unopened = [
                cell
                for cell in cells
                if int(cell.get("chest", 0)) > 0
                and not cell.get("event")
                and self._explore_box_quality_level(int(cell.get("chest", 0)))
                is not None
                and (cell_id is None or int(cell.get("id", 0)) == cell_id)
            ]
            # A replay request may contain both a previously opened queue and
            # new unopened cells.  Return both in one authoritative response
            # so the client animates and then claims the complete grid once.
            selected = pending + unopened if replay_pending else unopened
            if max_cells is not None:
                selected = selected[: max(0, int(max_cells))]
            charge_cells = [cell for cell in selected if not cell.get("event")]
            cost_count = 5 * len(charge_cells)
            ammo_before = self._item_number_locked(106000)
            if selected and ammo_before < cost_count:
                return []
            cost_number = self._set_item_locked(106000, ammo_before - cost_count)
            for cell in charge_cells:
                old_chest = int(cell.get("chest", 0))
                cfg = self._explore_box_quality_level(old_chest)
                if cfg is None:
                    continue
                start_quality, level = cfg
                final_quality, upgrade_shots = self._pick_explore_box_quality(
                    start_quality
                )
                events = [2] * upgrade_shots + [1] * (5 - upgrade_shots)
                random.shuffle(events)
                cell["oldChest"] = old_chest
                cell["event"] = events
                cell["chest"] = EXPLORE_BOX_BASE_BY_QUALITY[final_quality] + level
            if charge_cells:
                self._save_inventory_locked()
            result = [dict(cell) for cell in selected]
            for cell in result:
                cell["cost"] = [{"id": 106000, "number": cost_number}]
            return result

    def collect_supply_box(
        self,
        cell_id: int | None = None,
        *,
        max_cells: int | None = None,
    ) -> list[dict]:
        """Finish the client-side opening and persist the resulting reward.

        The shipped client sends this as cmd 32/3 (single) or 32/6 (all)
        after the five opening events.  A cell is collectible only while its
        event list is present; this prevents duplicate claims on retries.
        """
        with self._lock:
            selected = [
                cell
                for cell in self.inventory.setdefault("exploreCells", [])
                if int(cell.get("chest", 0)) > 0
                and cell.get("event")
                and (cell_id is None or int(cell.get("id", 0)) == cell_id)
            ]
            if max_cells is not None:
                selected = selected[: max(0, int(max_cells))]
            if not selected:
                return []

            reward_counts: dict[int, int] = {}
            for cell in selected:
                reward_id = EXPLORE_BOX_REWARD_BY_CHEST.get(
                    int(cell.get("chest", 0))
                )
                if reward_id is None:
                    return []
                reward_counts[reward_id] = reward_counts.get(reward_id, 0) + 1

            reward_numbers = {
                reward_id: self._item_number_locked(reward_id) + count
                for reward_id, count in reward_counts.items()
            }
            for reward_id, reward_number in reward_numbers.items():
                self._set_item_locked(reward_id, reward_number)

            completed: list[dict] = []
            for cell in selected:
                completed_id = int(cell.get("id", 0))
                reward_id = EXPLORE_BOX_REWARD_BY_CHEST[int(cell.get("chest", 0))]
                cell.clear()
                cell.update({"id": completed_id, "chest": 0})
                completed.append(
                    {
                        **dict(cell),
                        "rewardId": reward_id,
                        "rewardNumber": reward_numbers[reward_id],
                        "rewardDelta": 1,
                    }
                )
            self._save_inventory_locked()
            return completed


def json_response(handler: BaseHTTPRequestHandler, payload: dict, status: int = 200) -> None:
    data = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(data)))
    handler.end_headers()
    handler.wfile.write(data)


class ApiHandler(BaseHTTPRequestHandler):
    state: GameState

    def log_message(self, format: str, *args: object) -> None:
        # Never log query parameters: they may contain sessions or account data.
        LOG.info("HTTP %s %s", self.command, urlsplit(self.path).path)

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler API
        parsed = urlsplit(self.path)
        path = parsed.path.rstrip("/") or "/"
        query = parse_qs(parsed.query, keep_blank_values=True)

        if path == "/health":
            json_response(self, {"ok": True, "server": "hunter-roulette-local", "version": 63,
                                 "bot_difficulty": self.state.bot_difficulty})
            return

        if path.lower().endswith("/pkgversion.json"):
            payload = json.loads(self.state.pkg_version_path.read_text(encoding="utf-8-sig"))
            json_response(self, payload)
            return

        if path in {"/register", "/login"}:
            name = query.get("name", ["local"])[0]
            account = self.state.account_for(name)
            json_response(
                self,
                {
                    "error": 0,
                    "session": account.session,
                    "uid": f"local-{account.gid}",
                    "iswhite": 1,
                    "payUrl": "",
                    "skip": 0,
                    "roles": [
                        {
                            "id": account.gid,
                            "server": 1,
                            "name": account.name,
                            "status": 1,
                        }
                    ],
                },
            )
            return

        if path == "/sdkareas":
            json_response(
                self,
                {
                    "error": 0,
                    "areas": [
                        {
                            "id": 1,
                            "name": '{"Portuguese":"Local Lab","English":"Local Lab"}',
                            "start": 0,
                            "state": 4,
                        }
                    ],
                    "sysfuncflags": {},
                },
            )
            return

        if path == "/newrole":
            name = query.get("name", ["Local Hunter"])[0]
            account = self.state.account_for(name)
            json_response(
                self,
                {
                    "error": 0,
                    "role": {"id": account.gid, "server": 1, "name": account.name, "sex": 1},
                },
            )
            return

        if path == "/userole":
            account = self.state.account_for("local")
            json_response(
                self,
                {
                    "error": 0,
                    "server": {
                        "ip": "127.0.0.1",
                        "port": 38001,
                        "enpkey": "",
                        "session": account.session,
                    },
                    "role": {"id": account.gid, "server": 1, "name": account.name},
                },
            )
            return

        if path == "/notice":
            json_response(self, {"error": 0, "notices": []})
            return

        if path == "/randname":
            json_response(self, {"error": 0, "name": "Local Hunter", "index": 1})
            return

        json_response(self, {"error": 404, "message": "local endpoint not implemented"}, 404)


async def read_frame(
    reader: asyncio.StreamReader, length_mode: str
) -> tuple[object, bytes, bytes]:
    header_bytes = await reader.readexactly(HEADER_SIZE)
    head = decode_header(header_bytes)
    if length_mode == "total":
        body_len = head.length - HEADER_SIZE
    else:
        body_len = head.length
    if body_len < 0 or body_len > MAX_FRAME_SIZE:
        raise ValueError(f"invalid body length {body_len}")
    body = await reader.readexactly(body_len)
    return head, body, header_bytes + body


def _reload_weapon_ammo(
    gun_id: int, enhanced: list[int], actor: int, *, randomize: bool = False,
) -> tuple[int, int]:
    """Draw a fresh magazine, then apply the weapon's post-reload conversion."""
    real, blank = pvp_gun_ammo_counts(gun_id, randomize=randomize)
    magazine = apply_reload_trait(gun_id, real, blank)
    enhanced[actor] = magazine.enhanced
    if magazine.enhanced:
        LOG.info("PVP weapon trait Screwdriver gun=%d actor=%d real=%d blank=%d enhanced=%d",
                 gun_id, actor, magazine.real, magazine.blank, magazine.enhanced)
    elif weapon_skill_id(gun_id) == 3:
        LOG.info('PVP weapon trait Little Maniac gun=%d actor=%d next_die_bonus=2', gun_id, actor)
    elif weapon_skill_id(gun_id) == 10034:
        LOG.info('PVP weapon trait Artemis gun=%d actor=%d real=%d->%d blank=%d->%d',
                 gun_id, actor, real, magazine.real, blank, magazine.blank)
    return magazine.real, magazine.blank


def _resolve_hallucinogen_self_shot(
    gamers: list[bytes],
    hit_points: list[int],
    virtual_hit_points: list[int],
    real_ammo: list[int],
    fake_ammo: list[int],
    self_shots: list[int],
    target_index: int,
    *,
    round_number: int,
    event_id: int,
    event_time: int,
    randomize_magazines: bool = False,
    enhanced_ammo: list[int] | None = None,
) -> tuple[bytes, int, bool, bytes] | None:
    """Apply the target's forced shot and return normal-shot subevents.

    The bundled client routes a shoot-skill card through ``UseCard`` and then
    ``StartShootOnce``. It animates and reconciles ammo/HP from the card
    result's embedded Enum_Shoot/Enum_Finally_Source events.
    """
    if target_index < 0 or target_index >= len(gamers):
        return None
    if enhanced_ammo is None:
        enhanced_ammo = [pvp_gamer_enhanced_count(g) for g in gamers]
    ammo_total = real_ammo[target_index] + fake_ammo[target_index] + enhanced_ammo[target_index]
    if _pvp_is_eliminated(
        hit_points[target_index], virtual_hit_points[target_index]
    ) or ammo_total <= 0:
        return None

    target_roll = random.randrange(ammo_total)
    ammo_cfg_id = (300 if target_roll < fake_ammo[target_index] else
                   1 if target_roll < fake_ammo[target_index] + real_ammo[target_index] else 2)
    target_gun = parse_bytes_field(gamers[target_index], 7) or b''
    ammo_cfg_id = prioritize_shot_ammo(parse_varint_field(target_gun, 1) or 0,
                                     ammo_cfg_id, enhanced_ammo[target_index])
    hp_delta = 0
    virtual_hp_delta = 0
    if ammo_cfg_id == 300:
        fake_ammo[target_index] -= 1
    else:
        if ammo_cfg_id == 2:
            enhanced_ammo[target_index] -= 1
        else:
            real_ammo[target_index] -= 1
        (
            hit_points[target_index],
            virtual_hit_points[target_index],
            hp_delta,
            virtual_hp_delta,
        ) = _pvp_apply_hp_damage(
            hit_points[target_index], virtual_hit_points[target_index], 2 if ammo_cfg_id == 2 else 1
        )
        self_shots[target_index] += 1

    gamers[target_index], ghosts_added = pvp_ghosts_after_shot(gamers[target_index], ammo_cfg_id)
    real_ammo[target_index] += ghosts_added
    target_dead = _pvp_is_eliminated(
        hit_points[target_index], virtual_hit_points[target_index]
    )
    match_ended = sum(
        not _pvp_is_eliminated(hp, frenzy)
        for hp, frenzy in zip(hit_points, virtual_hit_points)
    ) <= 1
    shot_real_after = real_ammo[target_index]
    shot_fake_after = fake_ammo[target_index]
    shot_enhanced_after = enhanced_ammo[target_index]
    reload_ammo_after = None
    if not target_dead and not match_ended and real_ammo[target_index] + enhanced_ammo[target_index] <= 0:
        target_gun = parse_bytes_field(gamers[target_index], 7) or b""
        reload_ammo_after = _reload_weapon_ammo(
            parse_varint_field(target_gun, 1) or 0,
            enhanced_ammo, target_index,
            randomize=randomize_magazines,
        )
        real_ammo[target_index], fake_ammo[target_index] = reload_ammo_after
        LOG.info(
            "PVP hallucinogen auto-reload target=%d real=%d fake=%d",
            target_index, *reload_ammo_after,
        )
    updated_target = pvp_gamer_with_state(
        gamers[target_index],
        weapon_reloaded=reload_ammo_after is not None,
        hp=hit_points[target_index],
        ammo_number=real_ammo[target_index],
        fake_ammo_number=fake_ammo[target_index],
        enhanced_ammo_number=enhanced_ammo[target_index],
        round_number=round_number,
        is_dead=target_dead,
        virtual_hp=virtual_hit_points[target_index],
    )
    gamers[target_index] = updated_target
    shot_result = pvp_shoot_event_result_body(
        updated_target,
        updated_target,
        target_index,
        target_index,
        ammo_cfg_id=ammo_cfg_id,
        target_hp_delta=hp_delta,
        target_virtual_hp_delta=virtual_hp_delta,
        source_ammo_after=shot_real_after,
        source_fake_ammo_after=shot_fake_after,
        source_enhanced_ammo_after=shot_enhanced_after,
        ghosts_added_real_after_shots=(ghosts_added,),
        target_dead=target_dead,
        is_end_pvp=match_ended,
        shoot_self_num=self_shots[target_index],
        event_id=event_id,
        event_time=event_time,
        source_event_status=1 if target_dead else 0,
        target_event_status=5 if target_dead else 0,
        reload_ammo_after=reload_ammo_after,
    )
    return updated_target, ammo_cfg_id, match_ended, shot_result


def _pvp_venom_after_shots(gamers: list[bytes], source: int, target: int,
                          shots: list[tuple], frenzy: list[int], restrictions: TurnRestrictions) -> bool:
    gun = parse_bytes_field(gamers[source],7) or b''
    if weapon_skill_id(parse_varint_field(gun,1) or 0) != 10037:
        return False
    if not any(s[0] in (1,2) and (s[1] < 0 or (i < len(frenzy) and frenzy[i] < 0))
               for i,s in enumerate(shots)):
        return False
    gamers[target] = pvp_gamer_with_buffs(gamers[target],add_cfg_ids=(10066,),source_index=source)
    restrictions.apply(target,10066)
    LOG.info('PVP Toxin applied shooter=%d target=%d expires_at_target_start=%d',
             source,target,restrictions.deadlines[target,10066])
    return True


def _pvp_carnivore_reward(gamer: bytes, source: int, target: int,
                          shots: list[tuple], frenzy_deltas: list[int]) -> tuple[bytes, int]:
    gun = parse_bytes_field(gamer, 7) or b''
    reward = carnivore_reward(parse_varint_field(gun, 1) or 0, source, target, shots, frenzy_deltas)
    if reward:
        coin = parse_varint_field(gamer, 5) or 0
        gamer = pvp_gamer_with_coin_and_card(gamer, coin=coin + reward)
        LOG.info('PVP Carnivore reward actor=%d target=%d reward=%d coin=%d->%d',
                 source, target, reward, coin, coin + reward)
    return gamer, reward


def _draw_ejected_ammo(real_count: int, fake_count: int) -> int | None:
    """Draw one existing round proportionally from the target's magazine."""
    total = real_count + fake_count
    if total <= 0:
        return None
    return 300 if random.randrange(total) < fake_count else 1


def _draw_loaded_ammo(real: int, blank: int, enhanced: int, *, gun_id: int = -1) -> int | None:
    if enhanced <= 0:
        return _draw_ejected_ammo(real, blank)
    if real + blank + enhanced <= 0:
        return None
    roll = random.randrange(real + blank + enhanced)
    drawn = 300 if roll < blank else 1 if roll < blank + real else 2
    return prioritize_shot_ammo(gun_id, drawn, enhanced)


# Difficulty 3 amounts in the bundled ammo_reward_cfg (real, blank -> coin).
# The trio shop submode 6 uses that difficulty index. Consecutive-shot bonus
# comes from ammo_continue_shoot_self_cfg: 100 per prior blank self-shot.
_SELF_SHOT_REWARD_TRIO = {
    (5, 1): 1300, (4, 1): 1000, (3, 1): 800, (2, 1): 600,
    (1, 1): 400, (4, 2): 600, (3, 2): 500, (2, 2): 400,
    (1, 2): 200, (3, 3): 400, (2, 3): 300, (1, 3): 100,
    (2, 4): 200, (1, 4): 100, (1, 5): 100, (6, 1): 1700,
    (5, 2): 700, (4, 3): 500, (3, 4): 300, (2, 5): 100,
    (1, 6): 100,
}


def _pvp_roll_lucky_die(gamer: bytes, raw_roll: int) -> tuple[bytes, int, int]:
    updated, roll, consumed = pvp_consume_lucky_die(gamer, raw_roll)
    if consumed:
        LOG.info('PVP Lucky Streak consumed actor=%d raw=%d bonus=2 final=%d',
                 parse_varint_field(gamer, 3) or 0, raw_roll, roll)
    # Preserve the raw die for LuckEvent.randLuck/addLuck presentation.
    return updated, roll, raw_roll if consumed else 0


def _trio_self_shot_reward(real_count: int, fake_count: int, prior_blanks: int, *, gun_id: int = -1) -> int:
    reward = _SELF_SHOT_REWARD_TRIO.get((real_count, fake_count), 0) + min(
        max(0, prior_blanks), 10
    ) * 100
    return reward * self_shot_reward_multiplier(gun_id, real_count, fake_count)


def _pvp_shot_damage(
    ammo_cfg_id: int,
    *,
    enhanced_ammo_bonus: int = 0,
    maintenance_kit_active: bool = False,
    shooter_index: int,
    target_index: int,
) -> int:
    """Resolve damage without converting the Maintenance Kit into ammo.

    Arms Voucher's cfg 2 round remains its own enhanced projectile. The
    Maintenance Kit adds one damage to a normal cfg 1 shot, including a
    self-shot; it never synthesizes a cfg 2 round or upgrades blank ammo.
    """
    if ammo_cfg_id == 2:
        # Stack count is ammunition, not an extra damage multiplier.
        return 2
    if ammo_cfg_id == 1:
        return 1 + int(maintenance_kit_active)
    return 0


def _pvp_burst_shot_state(
    burst_stacks: int,
    shooter_index: int,
    target_index: int,
) -> tuple[bool, bool]:
    """Return (consume_buff, fire_second_shot) for the next firing action.

    Burst Mode expires on the shooter's next shot, even if they target
    themselves. A self-shot stays a single shot; only a shot at another fighter
    becomes a two-shot burst.
    """
    pending = int(burst_stacks) > 0
    return pending, pending and int(shooter_index) != int(target_index)


def _pvp_bot_timing(*, player_eliminated: bool) -> tuple[float, float]:
    """Return (turn-settle, total-think) delays for the bot phase.

    Once the local fighter is out, bots still finish the match for spectators,
    but their no-human think/turn pauses are shortened. Three seconds remain
    after each bot result so the visible shot/death animation can complete.
    """
    if player_eliminated:
        return BOT_SPECTATOR_SHOT_SETTLE, BOT_SPECTATOR_THINK_DELAY
    return BOT_SHOT_SETTLE, BOT_THINK_DELAY


def _pvp_apply_hp_damage(hp: int, virtual_hp: int, damage: int) -> tuple[int, int, int, int]:
    """Spend normal HP first, then Frenzy/virtual HP for any overflow.

    The bundled client only treats a fighter as defeated after *both* pools
    reach zero.  Its hit animation also accepts separate HP and virtual-HP
    deltas, so keep those deltas explicit for packet construction.
    """
    remaining = max(0, int(damage))
    hp_lost = min(max(0, int(hp)), remaining)
    remaining -= hp_lost
    virtual_hp_lost = min(max(0, int(virtual_hp)), remaining)
    return (
        max(0, int(hp) - hp_lost),
        max(0, int(virtual_hp) - virtual_hp_lost),
        -hp_lost,
        -virtual_hp_lost,
    )


def _pvp_is_eliminated(hp: int, virtual_hp: int) -> bool:
    """Frenzy is a second survivability pool, not a display-only meter."""
    return int(hp) <= 0 and int(virtual_hp) <= 0


def _pvp_wet_cigarette_heal(hp: int, virtual_hp: int, die_roll: int) -> int:
    """A successful wet-cigarette roll heals only while at least 1 HP remains.

    The player-reported original behavior is that the cigarette is useless at
    zero HP because the heart row disappears, even if Frenzy keeps the fighter
    alive. Rolls 4-6 heal one heart up to the four-heart cap.
    """
    if not 1 <= int(die_roll) <= 6:
        raise ValueError("wet-cigarette die roll must be between 1 and 6")
    if int(hp) <= 0 or _pvp_is_eliminated(hp, virtual_hp) or int(hp) >= 4:
        return 0
    return int(int(die_roll) >= 4)


def _pvp_virtual_hp_cap(gamer: bytes, default: int = 2) -> int:
    """Read the Frenzy cap advertised by the bundled client snapshot."""
    value = parse_varint_field(gamer, 23)
    return max(0, int(default if value is None else value))


def _pvp_diana_after_normal_shot(gamers, frenzy, source, target, cfg, hp_delta, frenzy_delta):
    """Native trigger 29, only called by ordinary shot executors, before death."""
    active = next((buff for buff in reversed(DIANA_BUFFS) if has_buff(gamers[source], buff)), None)
    eligible = active is not None and source != target and cfg in (1, 2) and hp_delta + frenzy_delta < 0
    remaining, cap, delta, cap_delta = diana_hit(frenzy[target],
        _pvp_virtual_hp_cap(gamers[target]), upgraded=active == DIANA_BUFFS[1], eligible=eligible)
    frenzy[target] = remaining
    if cap_delta:
        gamers[target] = pvp_gamer_with_frenzy_cap(gamers[target], cap)
    if delta or cap_delta:
        LOG.info("PVP Diana hit actor=%d target=%d frenzy_delta=%d cap_delta=%d cap=%d",
                 source, target, delta, cap_delta, cap)
    return delta, cap_delta


def _pvp_expire_diana_turn(gamers):
    """Called once on actor transition, never on a self-blank continuation."""
    expired = []
    for index, gamer in enumerate(gamers):
        buffs = tuple(buff for buff in DIANA_BUFFS if has_buff(gamer, buff))
        if buffs:
            gamers[index] = pvp_gamer_with_buffs(gamer, del_cfg_ids=buffs)
            expired.append((index, buffs))
    return expired


def _pvp_frenzy_after_shot(
    current: int,
    cap: int,
    ammo_cfg_id: int,
    damage_dealt: int,
    shooter_index: int,
    target_index: int,
) -> tuple[int, int]:
    """Apply the observed Frenzy rule for shots at another fighter.

    A blank fired at an opponent drains one point. A real shot that actually
    deals damage grants one point, up to the advertised cap. Self-shots are
    handled by the separate self-shot/combo rules and never change Frenzy.
    """
    cap = max(0, int(cap))
    current = min(cap, max(0, int(current)))
    updated = current
    if shooter_index != target_index:
        if ammo_cfg_id == 300:
            updated = max(0, current - 1)
        elif ammo_cfg_id in (1, 2) and int(damage_dealt) > 0:
            updated = min(cap, current + 1)
    return updated, updated - current


@dataclass(frozen=True)
class RpgShotResult:
    ammo_cfg_id: int
    consumed_ammo: tuple[tuple[int, int], ...]
    damage: int
    target_hp_delta: int
    target_virtual_hp_delta: int
    shooter_virtual_hp_delta: int
    target_dead: bool
    reload_ammo_after: tuple[int, int] | None
    ghosts_added_real: int = 0
    blocked_katie_buff: int | None = None


def _pvp_resolve_rocket_shot(
    gamers: list[bytes],
    hit_points: list[int],
    virtual_hit_points: list[int],
    real_ammo: list[int],
    fake_ammo: list[int],
    enhanced_ammo: list[int],
    source_index: int,
    target_index: int,
    *,
    round_number: int,
    randomize_magazines: bool = False,
    katie_guards: dict | None = None,
) -> RpgShotResult | None:
    """Resolve cfg2032 from the shipped Rpg buff contract.

    The launcher first draws one random round from the source magazine. A
    blank consumes one blank and deals no damage; a live round consumes every
    remaining live round and deals one damage per consumed live slot. The
    enhanced cfg2 round is live as well, but remains a single live slot for
    Rocket damage. If no live round remains, perform the lab's normal
    weapon-specific auto-reload while at least two fighters remain alive.
    """
    if (
        source_index == target_index
        or not 0 <= source_index < len(gamers)
        or not 0 <= target_index < len(gamers)
        or _pvp_is_eliminated(
            hit_points[source_index], virtual_hit_points[source_index]
        )
        or _pvp_is_eliminated(
            hit_points[target_index], virtual_hit_points[target_index]
        )
    ):
        return None

    live_before = max(0, real_ammo[source_index]) + max(
        0, enhanced_ammo[source_index]
    )
    blank_before = max(0, fake_ammo[source_index])
    ammo_cfg_id = _draw_ejected_ammo(live_before, blank_before)
    if ammo_cfg_id is None:
        return None

    blocked_katie = intercept_katie(gamers,katie_guards,source_index,target_index,ammo_cfg_id) if katie_guards is not None else None

    consumed: list[tuple[int, int]] = []
    damage = 0
    target_hp_delta = 0
    target_virtual_hp_delta = 0
    if ammo_cfg_id == 300:
        fake_ammo[source_index] -= 1
        consumed.append((300, 1))
    else:
        ordinary_live = max(0, real_ammo[source_index])
        enhanced_live = max(0, enhanced_ammo[source_index])
        if ordinary_live:
            consumed.append((1, ordinary_live))
        if enhanced_live:
            consumed.append((2, enhanced_live))
        real_ammo[source_index] = 0
        enhanced_ammo[source_index] = 0
        damage = ordinary_live + enhanced_live
        if blocked_katie:
            damage = 0
        (
            hit_points[target_index],
            virtual_hit_points[target_index],
            target_hp_delta,
            target_virtual_hp_delta,
        ) = _pvp_apply_hp_damage(
            hit_points[target_index], virtual_hit_points[target_index], damage
        )

    gamers[source_index], ghosts_added = pvp_ghosts_after_shot(gamers[source_index], ammo_cfg_id)
    real_ammo[source_index] += ghosts_added
    dealt = max(0, -target_hp_delta - target_virtual_hp_delta)
    updated_frenzy, shooter_virtual_hp_delta = _pvp_frenzy_after_shot(
        virtual_hit_points[source_index],
        _pvp_virtual_hp_cap(gamers[source_index]),
        ammo_cfg_id,
        dealt,
        source_index,
        target_index,
    )
    virtual_hit_points[source_index] = updated_frenzy

    target_dead = _pvp_is_eliminated(
        hit_points[target_index], virtual_hit_points[target_index]
    )
    reload_ammo_after = None
    if real_ammo[source_index] + enhanced_ammo[source_index] <= 0:
        survivors = sum(
            not _pvp_is_eliminated(hp, frenzy)
            for hp, frenzy in zip(hit_points, virtual_hit_points)
        )
        if survivors > 1 and not _pvp_is_eliminated(
            hit_points[source_index], virtual_hit_points[source_index]
        ):
            gun = parse_bytes_field(gamers[source_index], 7) or b""
            reload_ammo_after = _reload_weapon_ammo(
                parse_varint_field(gun, 1) or 0,
                enhanced_ammo, source_index,
                randomize=randomize_magazines,
            )
            real_ammo[source_index], fake_ammo[source_index] = reload_ammo_after

    gamers[source_index] = pvp_gamer_with_state(
        gamers[source_index],
        weapon_reloaded=reload_ammo_after is not None,
        hp=hit_points[source_index],
        ammo_number=real_ammo[source_index],
        fake_ammo_number=fake_ammo[source_index],
        enhanced_ammo_number=enhanced_ammo[source_index],
        round_number=round_number,
        is_dead=_pvp_is_eliminated(
            hit_points[source_index], virtual_hit_points[source_index]
        ),
        virtual_hp=virtual_hit_points[source_index],
    )
    gamers[target_index] = pvp_gamer_with_state(
        gamers[target_index],
        hp=hit_points[target_index],
        ammo_number=real_ammo[target_index],
        fake_ammo_number=fake_ammo[target_index],
        enhanced_ammo_number=enhanced_ammo[target_index],
        round_number=round_number,
        is_dead=target_dead,
        virtual_hp=virtual_hit_points[target_index],
    )
    return RpgShotResult(
        ammo_cfg_id=ammo_cfg_id,
        consumed_ammo=tuple(consumed),
        damage=damage,
        target_hp_delta=target_hp_delta,
        target_virtual_hp_delta=target_virtual_hp_delta,
        shooter_virtual_hp_delta=shooter_virtual_hp_delta,
        target_dead=target_dead,
        reload_ammo_after=reload_ammo_after,
        ghosts_added_real=ghosts_added,
        blocked_katie_buff=blocked_katie,
    )


def _maintenance_kit_expires_after_shot(
    active: bool,
    shooter_index: int,
    target_index: int,
    shots: list[tuple[int, int, int, int, bool]],
) -> bool:
    """Expire the one-turn Kit after a real shot or an opponent-target action.

    A blank self-shot can retain the player's turn, so it may retain the buff.
    """
    return bool(
        active
        and (
            target_index != shooter_index
            or any(shot[0] in (1, 2) for shot in shots)
        )
    )


def _pvp_apply_wanted(
    gamers: list[bytes],
    target_index: int,
    rewards: list[int],
    expiry_turns: list[int],
    turn_clock: int,
    *,
    source_index: int = 0,
) -> int:
    """Give this mark one full rotation from the time it is applied."""
    duration = max(1, sum(
        not _pvp_is_eliminated(
            parse_varint_field(gamer, 4) or 0,
            parse_varint_field(gamer, 17) or 0,
        )
        for gamer in gamers
    ))
    rewards[target_index] = WANTED_REWARD_R_CHIPS
    expiry_turns[target_index] = turn_clock + duration
    cfg_ids = (WANTED_PARENT_BUFF_CFG_ID, WANTED_REWARD_BUFF_CFG_ID)
    gamers[target_index] = pvp_gamer_with_buff_countdown(
        pvp_gamer_with_buffs(
            gamers[target_index], add_cfg_ids=cfg_ids, source_index=source_index,
        ),
        cfg_ids, duration, duration_turns=duration,
    )
    return duration


def _pvp_tick_wanted(
    gamers: list[bytes],
    rewards: list[int],
    expiry_turns: list[int],
    turn_clock: int,
) -> list[tuple[int, int, int]]:
    """Settle every independent mark at an actual change of active character.

    Returns (target, turns remaining, expiry payout). Repeated shots, item uses,
    animations and reloads within one turn do not advance this clock.
    """
    changes = []
    cfg_ids = (WANTED_PARENT_BUFF_CFG_ID, WANTED_REWARD_BUFF_CFG_ID)
    for target_index, reward in enumerate(rewards[:len(gamers)]):
        if reward <= 0:
            continue
        gamer = gamers[target_index]
        survived = not _pvp_is_eliminated(
            parse_varint_field(gamer, 4) or 0,
            parse_varint_field(gamer, 17) or 0,
        )
        remaining = max(0, expiry_turns[target_index] - turn_clock)
        if remaining > 0 and survived:
            gamers[target_index] = pvp_gamer_with_buff_countdown(
                gamer, cfg_ids, remaining,
            )
            changes.append((target_index, remaining, 0))
            continue
        payout = reward if survived else 0
        if payout:
            gamer = pvp_gamer_with_coin_and_card(
                gamer, coin=(parse_varint_field(gamer, 5) or 0) + payout,
            )
        gamers[target_index] = pvp_gamer_with_buffs(gamer, del_cfg_ids=cfg_ids)
        rewards[target_index] = 0
        expiry_turns[target_index] = 0
        changes.append((target_index, 0, payout))
    return changes


async def serve_client(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
    state: GameState,
    length_mode: str,
    service: str,
    *,
    show_player_coin: bool = True,
) -> None:
    peer = writer.get_extra_info("peername")
    LOG.info("%s connected: %s", service, peer[0] if peer else "unknown")
    account = state.account_for("local")
    current_pvp_info = b""
    # The shot handler prepares the bot's entire turn up front.  Poll replies
    # must instead reflect the last PVP snapshot actually sent to the client.
    published_pvp_info = b""
    current_pvp_player = b""
    current_pvp_bot = b""
    current_pvp_extra_bot = b""
    current_pvp_round = 1
    current_pvp_player_hp = 4
    current_pvp_bot_hp = 4
    current_pvp_extra_bot_hp = 4
    # The bundled name board has six bullet positions. Four real and two blank
    # rounds keep the match finishable while preserving actual roulette shots.
    current_pvp_player_ammo = 0
    current_pvp_bot_ammo = 0
    current_pvp_player_fake_ammo = 0
    current_pvp_bot_fake_ammo = 0
    current_pvp_extra_bot_ammo = 0
    current_pvp_extra_bot_fake_ammo = 0
    current_pvp_turn = 0
    current_pvp_turn_number = 1
    current_pvp_event_id = 0
    current_pvp_shop_refreshes = 0
    current_pvp_shop_next_id = 5
    current_pvp_player_self_shots = 0
    current_pvp_bot_self_shots = 0
    current_pvp_extra_bot_self_shots = 0
    current_pvp_self_blank_streak = 0
    current_pvp_self_shoot_pool = 0
    current_pvp_player_virtual_hp = 0
    current_pvp_bot_virtual_hp = 0
    current_pvp_extra_bot_virtual_hp = 0
    current_pvp_eliminated_order: list[int] = []
    # Arms Voucher cfg-2 rounds and the Maintenance Kit damage buff are
    # separate states: only the Voucher creates a special projectile.
    current_pvp_damage_bonus = [0, 0, 0]
    current_pvp_maintenance_bonus = [0, 0, 0]
    current_pvp_burst_mode = [0, 0, 0]
    current_pvp_bucket_guard = [False, False, False]
    current_pvp_katie_guards = {}
    current_pvp_wanted_reward = [0, 0, 0]
    current_pvp_wanted_expire_turn = [0, 0, 0]
    current_pvp_wanted_turn_clock = 0
    current_pvp_restrictions = TurnRestrictions()
    bot_rng = random.Random(state.bot_seed)
    current_pvp_ready_at = 0.0
    delayed_tasks: set[asyncio.Task[None]] = set()

    def publish_pvp_frame(frame: bytes) -> None:
        """Advance the queryable room state when its notification is emitted."""
        nonlocal published_pvp_info
        head = decode_header(frame[:HEADER_SIZE])
        info_field = {
            (255, 1): 3,   # next round
            (255, 2): 2,   # shot result
            (255, 5): 1,   # match end
            (255, 15): 1,  # gamer death
        }.get((head.cmd, head.act))
        if info_field is not None:
            info = parse_bytes_field(frame[HEADER_SIZE:], info_field)
            if info:
                published_pvp_info = info

    def current_pvp_virtual_hp_at(gamer_index: int) -> int:
        return (
            current_pvp_player_virtual_hp,
            current_pvp_bot_virtual_hp,
            current_pvp_extra_bot_virtual_hp,
        )[gamer_index]

    def state_snapshot() -> dict[str, int]:
        visible_gamers = parse_bytes_fields(published_pvp_info, 2)
        return {
            "round": current_pvp_round,
            "turn": current_pvp_turn,
            "turn_number": current_pvp_turn_number,
            "event_id": current_pvp_event_id,
            "player_hp": current_pvp_player_hp,
            "bot_hp": current_pvp_bot_hp,
            "extra_bot_hp": current_pvp_extra_bot_hp,
            "player_ammo": current_pvp_player_ammo,
            "bot_ammo": current_pvp_bot_ammo,
            "player_fake_ammo": current_pvp_player_fake_ammo,
            "bot_fake_ammo": current_pvp_bot_fake_ammo,
            "extra_bot_ammo": current_pvp_extra_bot_ammo,
            "extra_bot_fake_ammo": current_pvp_extra_bot_fake_ammo,
            # Keep planned and published values separate in the wire trace;
            # delayed bot events make the former intentionally run ahead.
            "published_round": parse_varint_field(published_pvp_info, 4) or 0,
            "published_current_index": parse_varint_field(published_pvp_info, 10) or 0,
            "published_player_hp": (
                parse_varint_field(visible_gamers[0], 4) or 0
                if len(visible_gamers) > 0 else 0
            ),
            "published_bot_hp": (
                parse_varint_field(visible_gamers[1], 4) or 0
                if len(visible_gamers) > 1 else 0
            ),
            "published_extra_bot_hp": (
                parse_varint_field(visible_gamers[2], 4) or 0
                if len(visible_gamers) > 2 else 0
            ),
            "published_gamer_count": len(visible_gamers),
            "published_shop_count": len(parse_bytes_fields(published_pvp_info, 7)),
            "published_player_coin": (
                parse_varint_field(visible_gamers[0], 5) or 0
                if visible_gamers else 0
            ),
            "published_player_card_cfg": (
                parse_varint_field(
                    parse_bytes_field(visible_gamers[0], 18) or b"", 2
                ) or 0
                if visible_gamers else 0
            ),
        }

    async def send_delayed_frames(frames: list[tuple[float, bytes]]) -> None:
        """Push animation-ordered frames without blocking request handling."""
        try:
            for delay, frame in frames:
                await asyncio.sleep(delay)
                writer.write(frame)
                publish_pvp_frame(frame)
                trace_frame(
                    service,
                    "S->C",
                    frame,
                    length_mode,
                    f"delayed:{delay:.3f}s",
                    state_snapshot(),
                )
                await writer.drain()
        except asyncio.CancelledError:
            raise
        except (ConnectionError, RuntimeError):
            LOG.info("%s delayed frame sequence ended with the connection", service)

    def recover_empty_player_magazine(*, increment_turn: bool = True) -> bytes:
        """Keep the local lab playable when its magazine reaches 0/0.

        The original mode's reserve/reload packet is not present in the
        reconstructed traces. Leaving the turn active with no ammunition
        deadlocks the copied client, so the lab publishes a fresh turn
        snapshot with a full magazine within this gun's configured bounds.
        This is deliberately logged as a lab fallback, not claimed as the
        original economy rule.
        """
        nonlocal current_pvp_player, current_pvp_info
        nonlocal current_pvp_player_ammo, current_pvp_player_fake_ammo
        nonlocal current_pvp_turn_number, current_pvp_event_id
        player_gun = parse_bytes_field(current_pvp_player, 7) or b""
        current_pvp_player_ammo, current_pvp_player_fake_ammo = (
            _reload_weapon_ammo(
                parse_varint_field(player_gun, 1) or 0,
                current_pvp_damage_bonus, 0,
                randomize=state.randomize_magazines,
            )
        )
        if increment_turn:
            current_pvp_turn_number += 1
        current_pvp_event_id += 1
        current_pvp_player = pvp_gamer_with_state(
            current_pvp_player,
            weapon_reloaded=True,
            hp=current_pvp_player_hp,
            ammo_number=current_pvp_player_ammo,
            fake_ammo_number=current_pvp_player_fake_ammo,
            enhanced_ammo_number=current_pvp_damage_bonus[0],
            round_number=current_pvp_round,
            is_dead=_pvp_is_eliminated(
                current_pvp_player_hp, current_pvp_player_virtual_hp
            ),
            virtual_hp=current_pvp_player_virtual_hp,
        )
        current_pvp_info = pvp_info_with_state(
            current_pvp_info,
            current_pvp_player,
            current_pvp_bot,
            round_number=current_pvp_round,
            turn_number=current_pvp_turn_number,
            current_index=0,
            additional_gamers=(current_pvp_extra_bot,)
            if current_pvp_extra_bot else (),
        )
        LOG.warning(
            "PVP lab empty-magazine recovery: auto-reloaded player to "
            "real=%d fake=%d turn=%d",
            current_pvp_player_ammo,
            current_pvp_player_fake_ammo,
            current_pvp_turn_number,
        )
        return pvp_next_round_body(
            current_pvp_player,
            current_pvp_info,
            round_number=current_pvp_round,
            server_time=server_time,
        )

    try:
        while True:
            head, body, incoming_frame = await read_frame(reader, length_mode)
            trace_frame(
                service,
                "C->S",
                incoming_frame,
                length_mode,
                "request",
                state_snapshot(),
            )
            LOG.info(
                "%s request cmd=%d act=%d index=%d body=%d",
                service,
                head.cmd,
                head.act,
                head.index,
                len(body),
            )
            gid = parse_varint_field(body, 1) or account.gid
            account = state.account_for_gid(gid)
            server_time = state.server_time()
            timed_inventory = state.timed_inventory(server_time)
            out_body = b""
            response_error = 0
            post_frames: list[bytes] = []
            delayed_frames: list[tuple[float, bytes]] = []

            if service == "logic":
                if (head.cmd, head.act) in {(1, 1), (1, 2)}:
                    try:
                        login_profile = state.profile_for(account)
                    except (ProfileError, OSError):
                        response_error = 400
                        login_profile = None
                    prepare_hero = int(
                        state.inventory.get(
                            "selectedHero",
                            state.inventory.get("heroes", [{}])[0].get("id", 0),
                        )
                    )
                    out_body = response_body(
                        head.cmd,
                        head.act,
                        account.gid,
                        account.session,
                        state.pvp_port,
                        prepare_hero,
                        int(state.inventory.get("homeLevel", 1)),
                        state.currency(101000),
                        state.currency(103000),
                        state.currency(102000),
                        state.currency(103500),
                        profile=login_profile,
                    )
                elif (head.cmd, head.act) == (2, 3):
                    try:
                        clan_team, gamer_clan_team = state.clan_login(account)
                        login_profile = state.profile_for(account)
                        out_body = login_data_body(account.gid, account.session, timed_inventory,
                            clan_team=clan_team, gamer_clan_team=gamer_clan_team,
                            profile=login_profile, accessories=accessory_body(login_profile, 24))
                    except (ClanError, ProfileError) as exc:
                        response_error = exc.code
                    except OSError:
                        response_error = 400
                elif (head.cmd, head.act) == (2, 2):
                    try:
                        out_body, renamed_profile = state.rename_player(account, parse_bytes_field(body, 2) or b'')
                        post_frames.append(encode_frame(253,28,
                            pb_bytes(1,pb_varint(1,renamed_profile['renameFree'])),length_mode=length_mode))
                        clan_team,_ = state.clan_login(account)
                        if clan_team is not None:
                            post_frames.append(encode_frame(253,70,pb_bytes(1,clan_team),length_mode=length_mode))
                        LOG.info('PROFILE rename completed gid=%d',account.gid)
                    except (ProfileError,ClanError) as exc:
                        response_error = exc.code
                    except OSError:
                        response_error = 400
                elif head.cmd == 2 and head.act in {6, 12}:
                    response_error = 757  # Rename/showcase/country await their dedicated implementation.
                elif (head.cmd, head.act) == (2, 5):
                    try:
                        selected_profile = state.equip_accessory(account, parse_varint_field(body, 2) or 0)
                        out_body = pb_varint(1, account.gid)
                        post_frames.append(encode_frame(253, 29, accessory_notify(selected_profile), length_mode=length_mode))
                        LOG.info('PROFILE accessory equipped gid=%d id=%d', account.gid, parse_varint_field(body, 2) or 0)
                    except ProfileError as exc:
                        response_error = exc.code
                    except OSError:
                        response_error = 400
                elif (head.cmd, head.act) == (2, 9):
                    target_gid = parse_varint_field(body, 2) or account.gid
                    target_account = next((a for a in state._accounts.values() if a.gid == target_gid), None)
                    if target_account is None:
                        response_error = 544
                    elif target_account.gid != account.gid:
                        response_error = 757  # Other-player loadout isolation is a later stage.
                    else:
                        try:
                            selected_profile = state.profile_for(target_account)
                            _, target_clan = state.clan_login(target_account)
                            # Until independent showcase editing is implemented, project actual equipped models.
                            hero = int(state.inventory.get('selectedHero', 0))
                            gun = next((int(g['gunId']) for g in state.inventory.get('heroGuns', [])
                                        if int(g['heroId']) == hero), 0)
                            _, hero_skin, _, gun_skin = pvp_appearance(state.inventory, hero, gun)
                            out_body = profile_detail_body(target_gid, selected_profile, state.inventory,
                                hero=hero, gun=gun, hero_skin=hero_skin, gun_skin=gun_skin, clan=target_clan)
                        except (ProfileError, ClanError) as exc:
                            response_error = exc.code
                        except OSError:
                            response_error = 400
                elif head.cmd == 47:
                    try:
                        out_body, clan_notifications = state.handle_clan(account, head.act, body)
                        for clan_act, clan_body in clan_notifications:
                            post_frames.append(encode_frame(253, clan_act, clan_body, length_mode=length_mode))
                        LOG.info('CLAN request act=%d gid=%d completed', head.act, account.gid)
                    except ClanError as exc:
                        response_error = exc.code
                        LOG.warning('CLAN request act=%d gid=%d rejected code=%d', head.act, account.gid, exc.code)
                    except OSError:
                        response_error = 400
                        LOG.error('CLAN persistence failed; in-memory transaction rolled back')
                elif (head.cmd, head.act) == (2, 4):
                    # GetPVPServerAreaListS2C: repeated ServerAreaInfo field 2.
                    area = b"\x0a\x0f127.0.0.1:" + str(state.pvp_port).encode("ascii") + b"\x10\x01"
                    out_body = b"\x12" + bytes([len(area)]) + area
                elif (head.cmd, head.act) == (6, 1):
                    # GamerReqPvpC2S: gid=1, mode=2, heroId=4, subMode=7,
                    # cardId=8. Older lab builds discarded these fields and
                    # consequently routed every menu item to NewGuide_Single.
                    mode = parse_varint_field(body, 2) or 1
                    hero_id = parse_varint_field(body, 4) or int(
                        state.inventory.get("selectedHero", 0)
                    )
                    sub_mode = parse_varint_field(body, 7) or 0
                    card_id = parse_varint_field(body, 8) or 0
                    LOG.info(
                        "local match requested mode=%d subMode=%d hero=%d card=%d",
                        mode, sub_mode, hero_id, card_id,
                    )
                    out_body = b"\x08" + _varint(account.gid)
                    post_frames.append(
                        encode_frame(
                            253,
                            3,
                            local_bot_start_body(
                                state.pvp_port, mode, sub_mode, hero_id, card_id
                            ),
                            error=0,
                            index=0,
                            length_mode=length_mode,
                        )
                    )
                elif (head.cmd, head.act) == (18, 1):
                    out_body = season_open_body(timed_inventory)
                elif (head.cmd, head.act) == (18, 2):
                    out_body = season_get_info_body(timed_inventory)
                elif (head.cmd, head.act) == (10, 2):
                    # GamerHeroSetPreS2C. Field 1 in this request is heroId, not gid.
                    hero_id = parse_varint_field(body, 1) or 0
                    if state.select_hero(hero_id):
                        out_body = b"\x08" + _varint(hero_id)
                        LOG.info("hero equipped id=%d", hero_id)
                elif (head.cmd, head.act) == (23, 1):
                    # Persist locally selected hero/gun fashion and notify the
                    # client so the equipment window refreshes immediately.
                    fashion_type = parse_varint_field(body, 2) or 1
                    fashion_id = parse_varint_field(body, 3) or 0
                    target_id = parse_varint_field(body, 4) or 0
                    if state.equip_fashion(target_id, fashion_id, fashion_type):
                        out_body = b"\x08" + _varint(account.gid)
                        post_frames.append(
                            encode_frame(
                                253,
                                18,
                                fashion_update_body(state.inventory),
                                error=0,
                                index=0,
                                length_mode=length_mode,
                            )
                        )
                        LOG.info(
                            "fashion equipped type=%d target=%d fashion=%d",
                            fashion_type,
                            target_id,
                            fashion_id,
                        )
                    else:
                        response_error = 400
                        LOG.warning(
                            "fashion equip rejected type=%d target=%d fashion=%d",
                            fashion_type,
                            target_id,
                            fashion_id,
                        )
                elif (head.cmd, head.act) == (23, 2):
                    # GamerFashionInfoS2C has the same two repeated fields as
                    # NotifyGamerFashion: owned fashions and worn fashions.
                    # Returning the canonical persisted lists prevents the
                    # equipment page from replacing its login state with an
                    # empty refresh response.
                    out_body = fashion_update_body(state.inventory)
                elif (head.cmd, head.act) == (8, 1):
                    # GamerGetPackS2C is the explicit bag refresh request.
                    # Login already includes the same ItemGood list, but the
                    # bag window asks for it again after entering the screen.
                    out_body = bag_get_pack_body(state.inventory)
                    LOG.info("bag data returned items=%d", len(state.inventory.get("items", [])))
                elif (head.cmd, head.act) == (8, 2):
                    item_id = parse_varint_field(body, 2) or 0
                    count = max(1, parse_varint_field(body, 3) or 1)
                    if item_id in TREASURE_BOX_USE:
                        opened = state.use_treasure_box(item_id, count)
                        if opened is None:
                            response_error = 394
                            LOG.warning(
                                "treasure box use rejected item=%d count=%d key=%d",
                                item_id,
                                count,
                                TREASURE_BOX_KEY_ID,
                            )
                        else:
                            out_body = bag_use_body(
                                opened["cost"], opened["award"]
                            )
                            LOG.info(
                                "treasure box opened item=%d count=%d award=%d",
                                item_id,
                                count,
                                opened["award"][0]["id"],
                            )
                    elif item_id in CONTENT_PACKAGE_TO_DROP:
                        opened = state.use_box_content_package(item_id, count)
                        if opened is None:
                            response_error = 394
                            LOG.warning(
                                "content package use rejected item=%d count=%d",
                                item_id,
                                count,
                            )
                        else:
                            out_body = bag_use_body(
                                opened["cost"], opened["award"]
                            )
                            LOG.info(
                                "content package opened item=%d count=%d drop=%d awards=%d",
                                item_id,
                                count,
                                CONTENT_PACKAGE_TO_DROP[item_id],
                                len(opened["award"]),
                            )
                    elif item_id in RANDOM_CHARACTER_RANGES:
                        opened = state.use_random_character_package(item_id, count)
                        if opened is None:
                            response_error = 394
                            LOG.warning(
                                "random character package use rejected item=%d count=%d",
                                item_id,
                                count,
                            )
                        else:
                            out_body = bag_use_body(
                                opened["cost"], opened["award"]
                            )
                            LOG.info(
                                "random character package opened item=%d count=%d awards=%d",
                                item_id,
                                count,
                                len(opened["award"]),
                            )
                    # Steam exploration-box cards are explicitly mapped in
                    # item_base Steam (use_result_type 1129/1128).  They
                    # convert into the exploration pack; no reward is
                    # fabricated here.  701264 is the blue pack (id 1),
                    # 701265 and the legacy 10001004 are purple (id 12).
                    elif item_id in {701264, 701265, 10001004}:
                        with state._lock:
                            owned = state._item_number_locked(item_id)
                            if owned < count:
                                response_error = 394
                                LOG.warning("bag use rejected item=%d count=%d", item_id, count)
                            else:
                                state._set_item_locked(item_id, owned - count)
                                pack = state.inventory.setdefault("exploreBoxPack", [])
                                pack_id = 1 if item_id == 701264 else 12
                                pack_item = next(
                                    (entry for entry in pack if int(entry.get("id", -1)) == pack_id),
                                    None,
                                )
                                if pack_item is None:
                                    pack_item = {"id": pack_id, "number": 0}
                                    pack.append(pack_item)
                                pack_item["number"] = int(pack_item.get("number", 0)) + count
                                state._save_inventory_locked()
                                out_body = bag_use_body(
                                    [{"id": item_id, "number": owned - count}],
                                    [],
                                )
                                LOG.info(
                                    "bag item used item=%d count=%d packId=%d packNumber=%d",
                                    item_id,
                                    count,
                                    pack_id,
                                    pack_item["number"],
                                )
                    else:
                        response_error = 396
                        LOG.warning("unsupported bag use item=%d count=%d", item_id, count)
                elif (head.cmd, head.act) == (8, 3):
                    item_id = parse_varint_field(body, 2) or 0
                    count = max(1, parse_varint_field(body, 3) or 1)
                    # Prices are taken from item_base_steam.item_sell.  The
                    # card-like preview items live in the card list, so only
                    # actual ItemGood entries are sellable in this phase.
                    unit_prices = {
                        **{item: 2_000 for item in range(201004, 201013)},
                        **{201013: 10_000, 201014: 10_000},
                        **{203000: 10_000, 203001: 10_000, 203002: 10_000},
                    }
                    unit_price = unit_prices.get(item_id)
                    with state._lock:
                        owned = state._item_number_locked(item_id)
                        if unit_price is None or owned < count:
                            response_error = 407 if unit_price is None else 394
                            LOG.warning("bag sell rejected item=%d count=%d", item_id, count)
                        else:
                            sold_number = state._set_item_locked(item_id, owned - count)
                            coin_number = state._adjust_item_locked(102000, unit_price * count)
                            state._save_inventory_locked()
                            out_body = bag_sell_body(
                                [{"id": item_id, "number": sold_number}],
                                [{"id": 102000, "number": coin_number}],
                            )
                            LOG.info("bag item sold item=%d count=%d", item_id, count)
                elif (head.cmd, head.act) == (8, 6):
                    # No recent-item history is persisted by the lab yet.  An
                    # empty response is the protobuf-defined valid result and
                    # keeps the recent tab from hanging.
                    out_body = b""
                elif (head.cmd, head.act) == (8, 7):
                    response_error = 400
                    LOG.warning("bag compose is not implemented yet item=%d", parse_varint_field(body, 2) or 0)
                elif (head.cmd, head.act) == (24, 1):
                    # GamerHeroCarryGunC2S: gid=1, heroId=2, gunId=3.
                    hero_id = parse_varint_field(body, 2) or 0
                    gun_id = parse_varint_field(body, 3) or 0
                    if state.carry_gun(hero_id, gun_id):
                        out_body = b"\x08" + _varint(account.gid)
                        post_frames.append(
                            encode_frame(
                                253,
                                21,
                                hero_gun_update_body(state.inventory),
                                error=0,
                                index=0,
                                length_mode=length_mode,
                            )
                        )
                        LOG.info("hero gun equipped hero=%d gun=%d", hero_id, gun_id)
                    else:
                        response_error = 400
                        LOG.warning("hero gun equip rejected hero=%d gun=%d", hero_id, gun_id)
                elif (head.cmd, head.act) == (22, 1):
                    shop_id = parse_varint_field(body, 2) or 0
                    shop_item_id = parse_varint_field(body, 3) or 0
                    count = parse_varint_field(body, 4) or 1
                    if shop_id == 10000004 and shop_item_id in EXPLORE_BOX_SHOP:
                        purchase = state.buy_supply_boxes(shop_item_id, count)
                        if purchase is not None:
                            out_body = market_purchase_body(
                                shop_item_id,
                                count,
                                purchase["award"][0]["id"],
                                purchase["award"][0]["number"],
                                cost=purchase["cost"],
                            )
                            LOG.info(
                                "supply boxes purchased shopItem=%d count=%d packId=%d packTotal=%d",
                                shop_item_id,
                                count,
                                purchase["packId"],
                                purchase["packNumber"],
                            )
                        else:
                            response_error = 475
                            LOG.warning("supply-box purchase rejected count=%d", count)
                    else:
                        LOG.warning(
                            "unsupported market purchase shop=%d item=%d count=%d",
                            shop_id,
                            shop_item_id,
                            count,
                        )
                elif (head.cmd, head.act) == (12, 1):
                    # GamerCardUnlockC2S.typ is 1=currency, 2=unlock token.
                    # Unlike equip, this path has a fully decoded cost table,
                    # so it can safely mutate the persistent inventory.
                    card_id = parse_varint_field(body, 1) or 0
                    hero_id = parse_varint_field(body, 2) or 0
                    unlock_type = parse_varint_field(body, 3) or 0
                    unlocked = state.unlock_card(hero_id, card_id, unlock_type)
                    if unlocked is not None:
                        hero, cost = unlocked
                        out_body = hero_card_unlock_body(hero, cost)
                        LOG.info(
                            "character card unlocked card=%d hero=%d type=%d",
                            card_id,
                            hero_id,
                            unlock_type,
                        )
                    else:
                        response_error = 524
                        LOG.warning(
                            "character card unlock rejected card=%d hero=%d type=%d",
                            card_id,
                            hero_id,
                            unlock_type,
                        )
                elif (head.cmd, head.act) == (12, 2):
                    card_id = parse_varint_field(body, 1) or 0
                    hero_id = parse_varint_field(body, 2) or 0
                    hero = state.equip_card(hero_id, card_id)
                    if hero is not None:
                        out_body = hero_card_ready_body(hero)
                        LOG.info("character card equipped card=%d hero=%d", card_id, hero_id)
                    else:
                        response_error = 524
                        LOG.warning("invalid character card card=%d hero=%d", card_id, hero_id)
                elif (head.cmd, head.act) == (32, 1):
                    out_body = explore_box_info_body(timed_inventory)
                    LOG.info("explore supply-box data returned")
                elif (head.cmd, head.act) == (32, 4):
                    quality = parse_varint_field(body, 2) or 0
                    if state.extract_supply_box(quality):
                        post_frames.append(
                            encode_frame(
                                253,
                                46,
                                explore_box_notify_body(timed_inventory),
                                error=0,
                                index=0,
                                length_mode=length_mode,
                            )
                        )
                        LOG.info(
                            "supply box extracted quality=%d boxId=%d",
                            quality,
                            EXPLORE_BOX_BASE_BY_QUALITY[quality],
                        )
                    else:
                        response_error = 597
                        LOG.warning("supply box extraction rejected quality=%d", quality)
                elif (head.cmd, head.act) == (32, 2):
                    cell_id = parse_varint_field(body, 1) or 0
                    # Replaying a persisted event is safe and recovers a
                    # single box when the client lost the first open reply.
                    cells = state.open_supply_box(cell_id, replay_pending=True)
                    if cells:
                        out_body = explore_box_open_body(cells[0], cells[0].get("cost", []))
                        LOG.info(
                            "supply box opened cell=%d oldBoxId=%d boxId=%d events=%s",
                            cell_id,
                            cells[0].get("oldChest", 0),
                            cells[0]["chest"],
                            cells[0].get("event", []),
                        )
                    else:
                        response_error = 378
                        LOG.warning("supply box open rejected cell=%d", cell_id)
                elif (head.cmd, head.act) == (32, 3):
                    cell_id = parse_varint_field(body, 1) or 0
                    cells = state.collect_supply_box(cell_id)
                    if cells:
                        out_body = explore_box_award_body(cells[0])
                        LOG.info("supply box reward claimed cell=%d", cell_id)
                    else:
                        response_error = 400
                        LOG.warning("supply box reward rejected cell=%d", cell_id)
                elif (head.cmd, head.act) == (32, 5):
                    with state._lock:
                        pending_before = sum(
                            int(cell.get("chest", 0)) > 0
                            and bool(cell.get("event"))
                            for cell in state.inventory.setdefault("exploreCells", [])
                        )
                        unopened_before = sum(
                            int(cell.get("chest", 0)) > 0
                            and not cell.get("event")
                            for cell in state.inventory.setdefault("exploreCells", [])
                        )
                    cells = state.open_supply_box(
                        replay_pending=True,
                    )
                    if cells:
                        out_body = explore_box_open_all_body(
                            state.inventory, cells, cells[0].get("cost", [])
                        )
                        LOG.info(
                            "all supply boxes opened count=%d pendingBefore=%d unopenedBefore=%d",
                            len(cells),
                            pending_before,
                            unopened_before,
                        )
                    else:
                        response_error = 378
                        LOG.warning("supply box open-all rejected")
                elif (head.cmd, head.act) == (32, 6):
                    # The preceding 32/5 response contains the complete
                    # active grid.  Claim every pending cell in one response.
                    cells = state.collect_supply_box()
                    if cells:
                        out_body = explore_box_award_all_body(cells)
                        LOG.info("all supply box rewards claimed count=%d", len(cells))
                    else:
                        response_error = 400
                        LOG.warning("supply box reward all rejected")
                elif (head.cmd, head.act) == (13, 1):
                    slot_index = parse_varint_field(body, 1) or 0
                    way_to_save = parse_varint_field(body, 2) or 0
                    open_cost_item = parse_varint_field(body, 3) or 0
                    open_cost_num = parse_varint_field(body, 4) or 0
                    started = state.start_home_box(
                        slot_index,
                        way_to_save,
                        open_cost_item,
                        open_cost_num,
                    )
                    if started is None:
                        response_error = 400
                        LOG.warning(
                            "home box start rejected slot=%d way=%d temp=%d costItem=%d costCount=%d",
                            slot_index,
                            way_to_save,
                            int(state.inventory.get("temporaryBoxId", -1)),
                            open_cost_item,
                            open_cost_num,
                        )
                    else:
                        out_body = home_start_box_body(started["boxes"])
                        if started["cost"]:
                            post_frames.append(
                                encode_frame(
                                    253,
                                    6,
                                    bag_update_body(started["cost"]),
                                    error=0,
                                    index=0,
                                    length_mode=length_mode,
                                )
                            )
                        post_frames.append(
                            encode_frame(
                                253,
                                10,
                                home_update_body(state.inventory),
                                error=0,
                                index=0,
                                length_mode=length_mode,
                            )
                        )
                        started_slot = next(
                            (entry for entry in started["boxes"] if int(entry.get("index", 0)) == slot_index),
                            {},
                        )
                        LOG.info("home box started slot=%d boxId=%d", slot_index, int(started_slot.get("boxId", -1)))
                elif (head.cmd, head.act) == (13, 2):
                    slot_index = parse_varint_field(body, 1) or 0
                    open_type = parse_varint_field(body, 2) or 1
                    opened = state.open_home_box(slot_index, open_type, account.gid)
                    if opened is None:
                        response_error = 400
                        LOG.warning(
                            "home box open rejected slot=%d type=%d",
                            slot_index,
                            open_type,
                        )
                    else:
                        out_body = home_open_box_body(
                            account.gid,
                            opened["box"],
                            opened["cost"],
                            opened["award"],
                        )
                        post_frames.append(
                            encode_frame(
                                253,
                                10,
                                home_update_body(state.inventory),
                                error=0,
                                index=0,
                                length_mode=length_mode,
                            )
                        )
                        LOG.info("home box opened slot=%d type=%d award=%d", slot_index, open_type, opened["award"][0]["id"])
                elif (head.cmd, head.act) == (13, 3):
                    sold = state.sell_temporary_home_box()
                    if sold is None:
                        response_error = 400
                        LOG.warning("temporary home box sell rejected")
                    else:
                        out_body = home_sell_box_body(sold)
                        post_frames.append(
                            encode_frame(
                                253,
                                6,
                                bag_update_body(sold),
                                error=0,
                                index=0,
                                length_mode=length_mode,
                            )
                        )
                        post_frames.append(
                            encode_frame(
                                253,
                                10,
                                home_update_body(state.inventory),
                                error=0,
                                index=0,
                                length_mode=length_mode,
                            )
                        )
                        LOG.info("temporary home box sold award=%d", sold[0]["id"])
                elif (head.cmd, head.act) == (13, 4):
                    income = state.collect_home_income()
                    out_body = home_income_body(income)
                    if income:
                        post_frames.append(
                            encode_frame(
                                253,
                                6,
                                bag_update_body(income),
                                error=0,
                                index=0,
                                length_mode=length_mode,
                            )
                        )
                    LOG.info("home income collected entries=%d", len(income))
                elif (head.cmd, head.act) == (13, 5):
                    # The temporary-open request carries index=0 and the same
                    # OpenType enum as the slot request.  Older builds put the
                    # type in field 1, so accept that wire variant too.
                    open_type = parse_varint_field(body, 2) or parse_varint_field(body, 1) or 1
                    opened = state.open_home_box(0, open_type, account.gid)
                    if opened is None:
                        response_error = 400
                        LOG.warning("temporary home box open rejected type=%d", open_type)
                    else:
                        out_body = home_open_box_body(
                            account.gid,
                            None,
                            opened["cost"],
                            opened["award"],
                        )
                        post_frames.append(
                            encode_frame(
                                253,
                                6,
                                bag_update_body(opened["award"]),
                                error=0,
                                index=0,
                                length_mode=length_mode,
                            )
                        )
                        post_frames.append(
                            encode_frame(
                                253,
                                10,
                                home_update_body(state.inventory),
                                error=0,
                                index=0,
                                length_mode=length_mode,
                            )
                        )
                        LOG.info("temporary home box opened type=%d award=%d", open_type, opened["award"][0]["id"])
                elif (head.cmd, head.act) == (17, 12):
                    # GamerGetChatServerS2C: the lab reuses the local TCP endpoint.
                    out_body = chat_server_body(state.pvp_port)
                elif (head.cmd, head.act) == (2, 1):
                    # NetHeart parses this response as ServerTime. Returning
                    # an empty body would reset the client clock to zero and
                    # restart the season open/get loop after a match.
                    out_body = server_time_body(timed_inventory)
            else:
                if (head.cmd, head.act) == (17, 10):
                    # GamerChatLoginS2C on the shared local TCP endpoint.
                    out_body = chat_login_body(account.gid)
                elif (head.cmd, head.act) == (17, 11):
                    # GamerChatHeartS2C keeps the chat socket alive.
                    out_body = chat_login_body(account.gid)
                elif head.cmd == 17:
                    # Local chat acknowledgements for non-critical lobby chat actions.
                    out_body = chat_login_body(account.gid)
                elif (head.cmd, head.act) == (3, 20):
                    out_body = pvp_fd_body(account.gid, state.pvp_port)
                elif (head.cmd, head.act) == (3, 1):
                    raw_session = parse_bytes_field(body, 2) or b""
                    session = raw_session.decode("utf-8", errors="replace")
                    parts = session.split(":")
                    requested_mode = 1
                    requested_sub_mode = 4
                    hero_id = int(state.inventory.get("selectedHero", 0))
                    carried_card_cfg_id = 0
                    if len(parts) == 5 and parts[0] == "local-pvp":
                        try:
                            requested_mode = int(parts[1])
                            requested_sub_mode = int(parts[2])
                            hero_id = int(parts[3]) or hero_id
                            carried_card_cfg_id = max(0, int(parts[4]))
                        except ValueError:
                            LOG.warning("invalid local PVP session marker")
                    gun_id = 3
                    for hero_gun in state.inventory.get("heroGuns", []):
                        if int(hero_gun.get("heroId", -1)) == hero_id:
                            gun_id = int(hero_gun.get("gunId", gun_id))
                            break
                    hero_model_id, hero_fashion_id, gun_model_id, gun_fashion_id = (
                        pvp_appearance(state.inventory, hero_id, gun_id)
                    )
                    (
                        out_body,
                        current_pvp_info,
                        current_pvp_player,
                        current_pvp_bot,
                    ) = pvp_login_snapshot(
                        account.gid,
                        account.name,
                        session,
                        requested_mode,
                        requested_sub_mode,
                        hero_id,
                        hero_model_id,
                        hero_fashion_id,
                        gun_id,
                        gun_model_id,
                        gun_fashion_id,
                        carried_card_cfg_id,
                        show_player_coin=show_player_coin,
                        randomize_ammo=state.randomize_magazines,
                        player_skill_id=battle_hero_skill(effective_hero_skill(next(
                            (h for h in state.inventory.get("heroes", []) if int(h.get("id", -1)) == hero_id),
                            {"id": hero_id, "skillId": LAB_HERO_SKILLS.get(hero_id, (0,0,0))[0]},
                        )), shop_trio=requested_mode == 1 and requested_sub_mode == 6),
                    )
                    if requested_mode == 1 and requested_sub_mode == 6:
                        starting_offers = tuple(
                            pvp_shop_card(card_id, cfg_id, price)
                            for card_id, (cfg_id, price) in enumerate(
                                _random_shop_specs(), start=1
                            )
                        )
                        current_pvp_info = pvp_info_with_shop(
                            current_pvp_info, starting_offers, 300,
                        )
                        out_body = pb_message(
                            pb_varint(1, account.gid),
                            pb_bytes(2, current_pvp_info),
                            pb_varint(3, 0),
                        )
                        LOG.info(
                            "PVP initial shop cfg=%s",
                            [parse_varint_field(card, 2) or 0
                             for card in starting_offers],
                        )
                    published_pvp_info = current_pvp_info
                    room_gamers = parse_bytes_fields(current_pvp_info, 2)
                    current_pvp_extra_bot = room_gamers[2] if len(room_gamers) > 2 else b""
                    current_pvp_round = 1
                    current_pvp_player_hp = parse_varint_field(
                        current_pvp_player, 4
                    ) or 0
                    current_pvp_bot_hp = parse_varint_field(
                        current_pvp_bot, 4
                    ) or 0
                    current_pvp_extra_bot_hp = parse_varint_field(
                        current_pvp_extra_bot, 4
                    ) or 0 if current_pvp_extra_bot else 0
                    current_pvp_player_virtual_hp = (
                        parse_varint_field(current_pvp_player, 17) or 0
                    )
                    current_pvp_bot_virtual_hp = (
                        parse_varint_field(current_pvp_bot, 17) or 0
                    )
                    current_pvp_extra_bot_virtual_hp = (
                        parse_varint_field(current_pvp_extra_bot, 17) or 0
                    ) if current_pvp_extra_bot else 0
                    def gamer_initial_ammo(gamer: bytes) -> tuple[int, int]:
                        gun = parse_bytes_field(gamer, 7) or b""
                        stacks = {
                            parse_varint_field(ammo, 1): parse_varint_field(ammo, 2)
                            for ammo in parse_bytes_fields(gun, 2)
                        }
                        return stacks.get(1, 0), stacks.get(300, 0)

                    (current_pvp_player_ammo,
                     current_pvp_player_fake_ammo) = gamer_initial_ammo(
                        current_pvp_player
                    )
                    (current_pvp_bot_ammo,
                     current_pvp_bot_fake_ammo) = gamer_initial_ammo(
                        current_pvp_bot
                    )
                    if current_pvp_extra_bot:
                        (current_pvp_extra_bot_ammo,
                         current_pvp_extra_bot_fake_ammo) = gamer_initial_ammo(
                            current_pvp_extra_bot
                        )
                    current_pvp_turn = 0
                    current_pvp_turn_number = 1
                    current_pvp_event_id = 0
                    current_pvp_shop_refreshes = 0
                    current_pvp_shop_next_id = 5
                    current_pvp_player_self_shots = 0
                    current_pvp_bot_self_shots = 0
                    current_pvp_extra_bot_self_shots = 0
                    current_pvp_self_blank_streak = 0
                    current_pvp_self_shoot_pool = 0
                    current_pvp_eliminated_order = []
                    current_pvp_damage_bonus = [pvp_gamer_enhanced_count(g) for g in
                        (current_pvp_player, current_pvp_bot, current_pvp_extra_bot)]
                    current_pvp_maintenance_bonus = [0, 0, 0]
                    current_pvp_burst_mode = [0, 0, 0]
                    current_pvp_bucket_guard = [False, False, False]
                    current_pvp_katie_guards = {}
                    current_pvp_wanted_reward = [0, 0, 0]
                    current_pvp_wanted_expire_turn = [0, 0, 0]
                    current_pvp_wanted_turn_clock = 0
                    current_pvp_restrictions = TurnRestrictions()
                    current_pvp_ready_at = 0.0
                    LOG.info(
                        "PVP room login requestedMode=%d requestedSubMode=%d "
                        "localMode=1 localSubMode=%d hero=%d heroModel=%d "
                        "heroFashion=%d gun=%d gunModel=%d gunFashion=%d carriedCard=%d",
                        requested_mode,
                        requested_sub_mode,
                        requested_sub_mode if requested_mode == 1 else 4,
                        hero_id,
                        hero_model_id,
                        hero_fashion_id,
                        gun_id,
                        gun_model_id,
                        gun_fashion_id,
                        carried_card_cfg_id,
                    )
                    if current_pvp_extra_bot:
                        LOG.info(
                            "PVP configured trio snapshot gamers=%d shopCards=%d "
                            "shopRefresh=%d startingCoin=%d",
                            len(room_gamers),
                            len(parse_bytes_fields(current_pvp_info, 7)),
                            parse_varint_field(current_pvp_info, 41) or 0,
                            parse_varint_field(current_pvp_player, 5) or 0,
                        )
                elif (head.cmd, head.act) == (3, 14):
                    if current_pvp_info:
                        # The opening turn grants the first skill point only
                        # when the player actually enters the arena.
                        current_pvp_player = pvp_gamer_with_skill_cd(
                            current_pvp_player,
                            max(0, pvp_gamer_skill_cd(current_pvp_player) - 1),
                        )
                        current_pvp_info = pvp_info_with_state(
                            current_pvp_info,
                            current_pvp_player,
                            current_pvp_bot,
                            round_number=current_pvp_round,
                            turn_number=current_pvp_turn_number,
                            current_index=0,
                        )
                        published_pvp_info = current_pvp_info
                        # Native participant introduction (255/16, status 15).
                        # Keep the playable snapshot separate: presentation must
                        # finish before 255/7 starts the existing ammo choreography.
                        intro_delay = PVP_OPENING_SEQUENCE_DELAY * (4.0 / 11.0)
                        cinema_delay = pvp_opening_cinema_delay(current_pvp_player)
                        intro_info = pvp_info_with_state(
                            current_pvp_info, current_pvp_player, current_pvp_bot,
                            round_number=current_pvp_round,
                            turn_number=current_pvp_turn_number, current_index=0,
                            status=15,
                            additional_gamers=((current_pvp_extra_bot,)
                                               if current_pvp_extra_bot else ()),
                        )
                        out_body = pvp_gamer_load_body(
                            account.gid,
                            pvp_info_with_state(
                                intro_info, current_pvp_player, current_pvp_bot,
                                round_number=current_pvp_round,
                                turn_number=current_pvp_turn_number,
                                current_index=0, status=18,
                                additional_gamers=((current_pvp_extra_bot,)
                                                   if current_pvp_extra_bot else ()),
                            ),
                            current_time=server_time,
                        )
                        # The bundled client uses NotifyPvpGamerAmmo (255/7)
                        # to seed gameInitInfo and build the opening ammo HUD;
                        # then NotifyGamerPvpNextRound (255/1) enables turns.
                        post_frames.append(encode_frame(
                            255, 11, pb_message(pb_varint(2, 18), pb_varint(3, 0)),
                            error=0, index=0, length_mode=length_mode,
                        ))
                        post_frames.append(encode_frame(
                            255, 18, pb_bytes(1, 'local-opening'),
                            error=0, index=0, length_mode=length_mode,
                        ))
                        # Patched client queues this panel until the native
                        # OnCutSceneFinish(-1) callback, in the same UI frame.
                        post_frames.append(encode_frame(
                            255, 16, pb_bytes(1, intro_info),
                            error=0, index=0, length_mode=length_mode,
                        ))
                        delayed_frames.append((cinema_delay, encode_frame(
                            255, 11, pb_message(pb_varint(2, 15), pb_varint(3, 0)),
                            error=0, index=0, length_mode=length_mode,
                        )))
                        # UpdateGameState hides Quit while isStartPvp=false.
                        # Explicitly leave the intro before starting ammo; a
                        # snapshot alone does not refresh that button's state.
                        delayed_frames.append((intro_delay, encode_frame(
                            255, 11, pb_message(pb_varint(2, 2), pb_varint(3, 1)),
                            error=0, index=0, length_mode=length_mode,
                        )))
                        delayed_frames.append((0.0,
                            encode_frame(
                                255,
                                7,
                                pvp_initial_ammo_body(current_pvp_info),
                                error=0,
                                index=0,
                                length_mode=length_mode,
                            )
                        ))
                        delayed_frames.append(
                            (
                                PVP_OPENING_SEQUENCE_DELAY,
                                encode_frame(
                                    255,
                                    1,
                                    pvp_next_round_body(
                                        current_pvp_player,
                                        current_pvp_info,
                                        round_number=current_pvp_round,
                                        server_time=server_time
                                        + int(round(cinema_delay + intro_delay + PVP_OPENING_SEQUENCE_DELAY)),
                                    ),
                                    error=0,
                                    index=0,
                                    length_mode=length_mode,
                                ),
                            )
                        )
                        current_pvp_turn = 0
                        current_pvp_ready_at = (
                            time.monotonic() + cinema_delay + intro_delay + PVP_OPENING_SEQUENCE_DELAY
                        )
                        LOG.info(
                            "PVP players loaded snapshot=%d bytes; native cinema then participants then ammo; initial turn after %.1fs",
                            len(current_pvp_info),
                            cinema_delay + intro_delay + PVP_OPENING_SEQUENCE_DELAY,
                        )
                    else:
                        LOG.warning("PVP gamer-load arrived before room login")
                        out_body = b"\x08" + _varint(account.gid)
                elif (head.cmd, head.act) == (3, 3) and current_pvp_extra_bot:
                    # Mode 1/submode 6 is a three-participant free-for-all
                    # snapshot. Resolve the local shot, then let each living
                    # bot take an animated turn before returning control. Bot
                    # targeting is an explicit local heuristic: bots prioritize
                    # the human while alive, then fight the remaining bot.
                    target_index = parse_varint_field(body, 1)
                    out_body = b"\x08" + _varint(account.gid)
                    empty_magazine_recovered = (
                        target_index in (0, 1, 2)
                        and current_pvp_player
                        and current_pvp_bot
                        and current_pvp_extra_bot
                        and current_pvp_info
                        and current_pvp_turn == 0
                        and time.monotonic() >= current_pvp_ready_at
                        and not _pvp_is_eliminated(
                            current_pvp_player_hp, current_pvp_player_virtual_hp
                        )
                        and current_pvp_player_ammo + current_pvp_player_fake_ammo + current_pvp_damage_bonus[0] <= 0
                    )
                    if empty_magazine_recovered:
                        reload_info = recover_empty_player_magazine()
                        post_frames.append(encode_frame(
                            255,
                            1,
                            reload_info,
                            error=0,
                            index=0,
                            length_mode=length_mode,
                        ))
                    if (
                        target_index in (0, 1, 2)
                        and current_pvp_player
                        and current_pvp_bot
                        and current_pvp_extra_bot
                        and current_pvp_info
                        and current_pvp_turn == 0
                        and time.monotonic() >= current_pvp_ready_at
                        and not _pvp_is_eliminated(
                            current_pvp_player_hp, current_pvp_player_virtual_hp
                        )
                        and current_pvp_player_ammo + current_pvp_player_fake_ammo + current_pvp_damage_bonus[0] > 0
                        and not empty_magazine_recovered
                    ):
                        gamers = [
                            current_pvp_player,
                            current_pvp_bot,
                            current_pvp_extra_bot,
                        ]
                        hit_points = [
                            current_pvp_player_hp,
                            current_pvp_bot_hp,
                            current_pvp_extra_bot_hp,
                        ]
                        virtual_hit_points = [
                            current_pvp_player_virtual_hp,
                            current_pvp_bot_virtual_hp,
                            current_pvp_extra_bot_virtual_hp,
                        ]
                        real_ammo = [
                            current_pvp_player_ammo,
                            current_pvp_bot_ammo,
                            current_pvp_extra_bot_ammo,
                        ]
                        fake_ammo = [
                            current_pvp_player_fake_ammo,
                            current_pvp_bot_fake_ammo,
                            current_pvp_extra_bot_fake_ammo,
                        ]
                        self_shots = [
                            current_pvp_player_self_shots,
                            current_pvp_bot_self_shots,
                            current_pvp_extra_bot_self_shots,
                        ]
                        event_time = server_time
                        real_before_shot = real_ammo[0] + current_pvp_damage_bonus[0]
                        fake_before_shot = fake_ammo[0]
                        if _pvp_is_eliminated(
                            hit_points[target_index], virtual_hit_points[target_index]
                        ):
                            LOG.warning(
                                "PVP trio shot ignored: target %d already eliminated",
                                target_index,
                            )
                        else:
                            # Burst Mode is two actual consecutive shots, not
                            # a +1 damage modifier.  Draw/decrement each round
                            # separately so the client can reconcile two
                            # Enum_Shoot events and the HUD loses two rounds.
                            burst_pending, burst_active = _pvp_burst_shot_state(
                                current_pvp_burst_mode[0], 0, target_index
                            )
                            if burst_pending:
                                current_pvp_burst_mode[0] = 0
                                LOG.info(
                                    "PVP Burst Mode consumed shooter=0 target=%d double_shot=%s",
                                    target_index, burst_active,
                                )
                            maintenance_active_for_shot = bool(
                                current_pvp_maintenance_bonus[0]
                            )
                            player_shots: list[tuple[int, int, int, int, bool]] = []
                            player_virtual_hp_deltas: list[int] = []
                            player_virtual_hp_cap_deltas: list[int] = []
                            player_source_virtual_hp_deltas: list[int] = []
                            player_ghosts_added: list[int] = []
                            player_source_dead_after_shots: list[bool] = []
                            player_katie_consumed = []
                            shot_damage = 0
                            shot_count = normal_shot_count(
                                parse_varint_field(parse_bytes_field(gamers[0], 7) or b'', 1) or 0,
                                real_ammo[0], fake_ammo[0], current_pvp_damage_bonus[0],0,target_index,burst_active)
                            for shot_number in range(shot_count):
                                shot_cfg = _draw_loaded_ammo(
                                    real_ammo[0], fake_ammo[0], current_pvp_damage_bonus[0],
                                    gun_id=parse_varint_field(parse_bytes_field(gamers[0], 7) or b'', 1) or 0,
                                )
                                if shot_cfg is None:
                                    break
                                blocked_katie = intercept_katie(gamers,current_pvp_katie_guards,0,target_index,shot_cfg)
                                if blocked_katie:
                                    player_katie_consumed.append(blocked_katie)
                                    LOG.info("PVP Katie intercept shooter=0 target=%d cfg=%d",target_index,shot_cfg)
                                if shot_cfg == 300:
                                    fake_ammo[0] -= 1
                                    shot_damage = 0
                                else:
                                    if shot_cfg == 1:
                                        real_ammo[0] -= 1
                                    shot_damage = _pvp_shot_damage(
                                        shot_cfg,
                                        enhanced_ammo_bonus=current_pvp_damage_bonus[0],
                                        maintenance_kit_active=maintenance_active_for_shot,
                                        shooter_index=0,
                                        target_index=target_index,
                                    )
                                    if shot_cfg == 2:
                                        current_pvp_damage_bonus[0] -= 1
                                    if blocked_katie:
                                        shot_damage = 0
                                    elif current_pvp_bucket_guard[target_index]:
                                        shot_damage = 0
                                        current_pvp_bucket_guard[target_index] = False
                                    (
                                        hit_points[target_index],
                                        virtual_hit_points[target_index],
                                        target_hp_delta,
                                        target_virtual_hp_delta,
                                    ) = _pvp_apply_hp_damage(
                                        hit_points[target_index],
                                        virtual_hit_points[target_index],
                                        shot_damage,
                                    )
                                    if target_index == 0:
                                        self_shots[0] += 1
                                if shot_cfg == 300:
                                    target_hp_delta = 0
                                    target_virtual_hp_delta = 0
                                diana_delta, diana_cap_delta = _pvp_diana_after_normal_shot(
                                    gamers, virtual_hit_points, 0, target_index, shot_cfg,
                                    target_hp_delta, target_virtual_hp_delta)
                                target_virtual_hp_delta += diana_delta
                                player_virtual_hp_cap_deltas.append(diana_cap_delta)
                                if target_index == 0:
                                    source_virtual_hp_delta = 0
                                else:
                                    (
                                        current_pvp_player_virtual_hp,
                                        source_virtual_hp_delta,
                                    ) = _pvp_frenzy_after_shot(
                                        current_pvp_player_virtual_hp,
                                        _pvp_virtual_hp_cap(gamers[0]),
                                        shot_cfg,
                                        max(
                                            0,
                                            -target_hp_delta - target_virtual_hp_delta,
                                        ),
                                        0,
                                        target_index,
                                    )
                                    virtual_hit_points[0] = current_pvp_player_virtual_hp
                                gamers[0], added_real = pvp_ghosts_after_shot(gamers[0], shot_cfg)
                                real_ammo[0] += added_real
                                player_ghosts_added.append(added_real)
                                player_shots.append((
                                    shot_cfg,
                                    target_hp_delta,
                                    real_ammo[0],
                                    fake_ammo[0],
                                    _pvp_is_eliminated(
                                        hit_points[target_index],
                                        virtual_hit_points[target_index],
                                    ),
                                ))
                                player_virtual_hp_deltas.append(target_virtual_hp_delta)
                                player_source_virtual_hp_deltas.append(
                                    source_virtual_hp_delta
                                )
                                player_source_dead_after_shots.append(
                                    _pvp_is_eliminated(
                                        hit_points[0], virtual_hit_points[0]
                                    )
                                )
                                if _pvp_is_eliminated(
                                    hit_points[target_index],
                                    virtual_hit_points[target_index],
                                ) or player_source_dead_after_shots[-1]:
                                    break
                            if target_index == 0:
                                current_pvp_player_virtual_hp = virtual_hit_points[0]
                            maintenance_expired = _maintenance_kit_expires_after_shot(
                                maintenance_active_for_shot,
                                0,
                                target_index,
                                player_shots,
                            )
                            if maintenance_expired:
                                current_pvp_maintenance_bonus[0] = 0
                            if not player_shots:
                                LOG.warning("PVP trio shot had no drawable round")
                                continue
                            gamers[0], weapon_reward = _pvp_carnivore_reward(
                                gamers[0],0,target_index,player_shots,player_virtual_hp_deltas)
                            toxin_applied = _pvp_venom_after_shots(gamers,0,target_index,
                                player_shots,player_virtual_hp_deltas,current_pvp_restrictions)
                            wanted_reward_on_shot = (
                                current_pvp_wanted_reward[target_index]
                                if any(
                                    shot[1] < 0
                                    or player_virtual_hp_deltas[index] < 0
                                    for index, shot in enumerate(player_shots)
                                )
                                else 0
                            )
                            if wanted_reward_on_shot:
                                player_coin = (
                                    parse_varint_field(gamers[0], 5) or 0
                                )
                                gamers[0] = pvp_gamer_with_coin_and_card(
                                    gamers[0],
                                    coin=player_coin + wanted_reward_on_shot,
                                )
                                gamers[target_index] = pvp_gamer_with_buffs(
                                    gamers[target_index],
                                    del_cfg_ids=(
                                        WANTED_PARENT_BUFF_CFG_ID,
                                        WANTED_REWARD_BUFF_CFG_ID,
                                    ),
                                )
                                current_pvp_wanted_reward[target_index] = 0
                                current_pvp_wanted_expire_turn[target_index] = 0
                                LOG.info(
                                    "PVP Wanted claimed shooter=0 target=%d reward=%d",
                                    target_index,
                                    wanted_reward_on_shot,
                                )
                            player_ammo_cfg = player_shots[0][0]
                            self_blank_continues = (
                                target_index == 0
                                and all(shot[0] == 300 for shot in player_shots)
                                and not _pvp_is_eliminated(
                                    hit_points[0], virtual_hit_points[0]
                                )
                            )
                            if self_blank_continues:
                                current_pvp_self_shoot_pool += _trio_self_shot_reward(
                                    real_before_shot, fake_before_shot,
                                    current_pvp_self_blank_streak,
                                    gun_id=parse_varint_field(parse_bytes_field(gamers[0],7) or b'',1) or 0,
                                )
                                current_pvp_self_blank_streak += 1
                                next_self_coin = _trio_self_shot_reward(
                                    real_ammo[0] + current_pvp_damage_bonus[0], fake_ammo[0],
                                    current_pvp_self_blank_streak,
                                    gun_id=parse_varint_field(parse_bytes_field(gamers[0],7) or b'',1) or 0,
                                )
                                continue_bonus = min(
                                    current_pvp_self_blank_streak, 10
                                ) * 100
                            else:
                                current_pvp_self_blank_streak = 0
                                current_pvp_self_shoot_pool = 0
                                next_self_coin = 0
                                continue_bonus = 0
                            continue_state = (
                                current_pvp_self_blank_streak,
                                current_pvp_self_shoot_pool,
                                next_self_coin,
                                int(self_blank_continues),
                                continue_bonus,
                            )
                            player_reload_ammo = None
                            if (
                                real_ammo[0] + current_pvp_damage_bonus[0] <= 0
                                and not _pvp_is_eliminated(
                                    hit_points[0], virtual_hit_points[0]
                                )
                                and sum(
                                    not _pvp_is_eliminated(hp, vhp)
                                    for hp, vhp in zip(hit_points, virtual_hit_points)
                                ) > 1
                            ):
                                player_gun = parse_bytes_field(gamers[0], 7) or b""
                                real_ammo[0], fake_ammo[0] = _reload_weapon_ammo(
                                    parse_varint_field(player_gun, 1) or 0,
                                    current_pvp_damage_bonus, 0,
                                    randomize=state.randomize_magazines,
                                )
                                player_reload_ammo = (real_ammo[0], fake_ammo[0])
                                LOG.info(
                                    "PVP trio player reload with no real rounds real=%d fake=%d",
                                    *player_reload_ammo,
                                )
                            gamers[0] = pvp_gamer_with_state(
                                gamers[0], hp=hit_points[0],
                                weapon_reloaded=player_reload_ammo is not None,
                                ammo_number=real_ammo[0],
                                fake_ammo_number=fake_ammo[0],
                                enhanced_ammo_number=current_pvp_damage_bonus[0],
                                round_number=current_pvp_round,
                                virtual_hp=current_pvp_player_virtual_hp,
                                continue_shoot=continue_state,
                            )
                            if (
                                _pvp_is_eliminated(
                                    hit_points[target_index],
                                    virtual_hit_points[target_index],
                                )
                                and target_index not in current_pvp_eliminated_order
                            ):
                                current_pvp_eliminated_order.append(target_index)

                            current_pvp_event_id += 1
                            if not self_blank_continues:
                                current_pvp_turn_number += 1
                            current_pvp_turn = -1
                            current_pvp_round = max(1, current_pvp_round)
                            timeline_elapsed = 0.0
                            bot_preparations = [0, 0, 0]
                            bot_self_streaks = [0, 0, 0]
                            bot_self_pots = [0, 0, 0]
                            bot_pending_start_delay = 0.0

                            def queue_trio_frame(
                                delay: float, cmd: int, act: int, frame_body: bytes
                            ) -> None:
                                nonlocal timeline_elapsed
                                delay = max(0.0, float(delay))
                                delayed_frames.append(
                                    (
                                        delay,
                                        encode_frame(
                                            cmd,
                                            act,
                                            frame_body,
                                            error=0,
                                            index=0,
                                            length_mode=length_mode,
                                        ),
                                    )
                                )
                                timeline_elapsed += delay

                            def trio_snapshot(
                                round_number: int,
                                current_index: int,
                                status: int = 2,
                            ) -> bytes:
                                nonlocal current_pvp_info
                                nonlocal current_pvp_player, current_pvp_bot
                                nonlocal current_pvp_extra_bot
                                nonlocal current_pvp_player_hp, current_pvp_bot_hp
                                nonlocal current_pvp_extra_bot_hp
                                nonlocal current_pvp_player_ammo, current_pvp_bot_ammo
                                nonlocal current_pvp_extra_bot_ammo
                                nonlocal current_pvp_player_fake_ammo
                                nonlocal current_pvp_bot_fake_ammo
                                nonlocal current_pvp_extra_bot_fake_ammo
                                nonlocal current_pvp_player_self_shots
                                nonlocal current_pvp_bot_self_shots
                                nonlocal current_pvp_extra_bot_self_shots
                                nonlocal current_pvp_player_virtual_hp
                                nonlocal current_pvp_bot_virtual_hp
                                nonlocal current_pvp_extra_bot_virtual_hp
                                for gamer_index in range(3):
                                    gamers[gamer_index] = pvp_gamer_with_state(
                                        gamers[gamer_index],
                                        hp=hit_points[gamer_index],
                                        ammo_number=real_ammo[gamer_index],
                                        fake_ammo_number=fake_ammo[gamer_index],
                                        enhanced_ammo_number=(
                                            current_pvp_damage_bonus[gamer_index]
                                        ),
                                        round_number=round_number,
                                        is_dead=_pvp_is_eliminated(
                                            hit_points[gamer_index],
                                            virtual_hit_points[gamer_index],
                                        ),
                                        virtual_hp=virtual_hit_points[gamer_index],
                                        burst_mode_active=bool(
                                            current_pvp_burst_mode[gamer_index]
                                        ),
                                        maintenance_kit_active=bool(
                                            current_pvp_maintenance_bonus[gamer_index]
                                        ),
                                    )
                                current_pvp_player, current_pvp_bot, current_pvp_extra_bot = gamers
                                (
                                    current_pvp_player_hp,
                                    current_pvp_bot_hp,
                                    current_pvp_extra_bot_hp,
                                ) = hit_points
                                (
                                    current_pvp_player_ammo,
                                    current_pvp_bot_ammo,
                                    current_pvp_extra_bot_ammo,
                                ) = real_ammo
                                (
                                    current_pvp_player_fake_ammo,
                                    current_pvp_bot_fake_ammo,
                                    current_pvp_extra_bot_fake_ammo,
                                ) = fake_ammo
                                (
                                    current_pvp_player_self_shots,
                                    current_pvp_bot_self_shots,
                                    current_pvp_extra_bot_self_shots,
                                ) = self_shots
                                (
                                    current_pvp_player_virtual_hp,
                                    current_pvp_bot_virtual_hp,
                                    current_pvp_extra_bot_virtual_hp,
                                ) = virtual_hit_points
                                current_pvp_info = pvp_info_with_state(
                                    current_pvp_info,
                                    gamers[0],
                                    gamers[1],
                                    round_number=round_number,
                                    turn_number=current_pvp_turn_number,
                                    current_index=current_index,
                                    status=status,
                                    additional_gamers=(gamers[2],),
                                )
                                return current_pvp_info

                            def queue_actor_start(
                                actor_index: int,
                                round_number: int,
                                prepare_delay: float,
                                active_delay: float,
                            ) -> None:
                                nonlocal current_pvp_info, current_pvp_shop_next_id
                                nonlocal current_pvp_event_id
                                nonlocal current_pvp_wanted_turn_clock
                                # One tick for the next active character, not
                                # for each bullet, item, reload or animation.
                                current_pvp_wanted_turn_clock += 1
                                bot_preparations[actor_index] = 0
                                for expired_actor, expired_buffs in _pvp_expire_diana_turn(gamers):
                                    current_pvp_event_id += 1
                                    queue_trio_frame(0, 255, 2,
                                        pvp_event_notification_body(
                                            pvp_passive_buff_removal_event_result_body(
                                                gamers[expired_actor], target_index=expired_actor,
                                                cfg_ids=expired_buffs, event_id=current_pvp_event_id,
                                                event_time=server_time + int(round(timeline_elapsed))),
                                            trio_snapshot(round_number, actor_index),
                                            server_time=server_time + int(round(timeline_elapsed))))
                                expired_bans = current_pvp_restrictions.start(actor_index)
                                if expired_bans:
                                    gamers[actor_index] = pvp_gamer_with_buffs(
                                        gamers[actor_index], del_cfg_ids=expired_bans,
                                    )
                                    current_pvp_event_id += 1
                                    queue_trio_frame(0, 255, 2,
                                        pvp_event_notification_body(
                                            pvp_passive_buff_removal_event_result_body(
                                                gamers[actor_index], target_index=actor_index,
                                                cfg_ids=expired_bans,
                                                event_id=current_pvp_event_id,
                                                event_time=server_time + int(round(timeline_elapsed)),
                                            ), trio_snapshot(round_number, actor_index),
                                            server_time=server_time + int(round(timeline_elapsed)),
                                        ))
                                if not _pvp_is_eliminated(
                                    hit_points[actor_index],
                                    virtual_hit_points[actor_index],
                                ):
                                    old_cd = pvp_gamer_skill_cd(gamers[actor_index])
                                    if old_cd > 0:
                                        gamers[actor_index] = pvp_gamer_with_skill_cd(
                                            gamers[actor_index], old_cd - 1,
                                        )
                                        LOG.info(
                                            "PVP hero skill charge actor=%d skill=%d cd=%d->%d",
                                            actor_index,
                                            pvp_gamer_skill_id(gamers[actor_index]),
                                            old_cd, old_cd - 1,
                                        )
                                if (
                                    actor_index > 0
                                    and not _pvp_is_eliminated(
                                        hit_points[actor_index],
                                        virtual_hit_points[actor_index],
                                    )
                                    and real_ammo[actor_index] <= 0
                                    and current_pvp_damage_bonus[actor_index] <= 0
                                ):
                                    actor_gun = parse_bytes_field(
                                        gamers[actor_index], 7
                                    ) or b""
                                    (real_ammo[actor_index],
                                     fake_ammo[actor_index]) = _reload_weapon_ammo(
                                        parse_varint_field(actor_gun, 1) or 0,
                                        current_pvp_damage_bonus, actor_index,
                                        randomize=state.randomize_magazines,
                                    )
                                    gamers[actor_index] = pvp_gamer_with_state(
                                        gamers[actor_index],
                                        weapon_reloaded=True,
                                        hp=hit_points[actor_index],
                                        ammo_number=real_ammo[actor_index],
                                        fake_ammo_number=fake_ammo[actor_index],
                                        enhanced_ammo_number=current_pvp_damage_bonus[actor_index],
                                        round_number=round_number,
                                    )
                                    LOG.info(
                                        "PVP trio auto-reload bot %d real=%d fake=%d",
                                        actor_index,
                                        real_ammo[actor_index],
                                        fake_ammo[actor_index],
                                    )
                                previous_cards = tuple(
                                    parse_bytes_fields(current_pvp_info, 7)
                                )
                                refreshed_cards, next_id = _replenish_sold_shop_cards(
                                    previous_cards,
                                    current_pvp_shop_next_id,
                                    current_pvp_turn_number,
                                )
                                if refreshed_cards != previous_cards:
                                    current_pvp_shop_next_id = next_id
                                    current_pvp_info = pvp_info_with_shop(
                                        current_pvp_info,
                                        refreshed_cards,
                                        parse_varint_field(current_pvp_info, 41) or 0,
                                    )
                                    LOG.info(
                                        "PVP shop replenished at actor=%d turn=%d stock=%s",
                                        actor_index,
                                        current_pvp_turn_number,
                                        [parse_varint_field(card, 2) or 0
                                         for card in refreshed_cards],
                                    )
                                katie_expired = expire_katie(gamers,current_pvp_katie_guards,actor_index)
                                if katie_expired:
                                    buff, reward = katie_expired
                                    current_pvp_event_id += 1
                                    katie_time = server_time + int(round(timeline_elapsed + prepare_delay))
                                    queue_trio_frame(prepare_delay,255,2,pvp_event_notification_body(
                                        katie_expiry_packet(gamers[actor_index],actor_index,buff,reward,current_pvp_event_id,katie_time),
                                        trio_snapshot(round_number,actor_index,status=2),server_time=katie_time))
                                    LOG.info("PVP Katie expired actor=%d reward=%d",actor_index,reward)
                                    prepare_delay = 0.0
                                wanted_changes = _pvp_tick_wanted(
                                    gamers, current_pvp_wanted_reward,
                                    current_pvp_wanted_expire_turn,
                                    current_pvp_wanted_turn_clock,
                                )
                                for wanted_index, remaining, payout in wanted_changes:
                                    current_pvp_event_id += 1
                                    wanted_time = server_time + int(
                                        round(timeline_elapsed + prepare_delay)
                                    )
                                    event_info = trio_snapshot(
                                        round_number, actor_index, status=2
                                    )
                                    if remaining > 0:
                                        wanted_event = pvp_buff_countdown_event_result_body(
                                            gamers[wanted_index],
                                            target_index=wanted_index,
                                            event_id=current_pvp_event_id,
                                            event_time=wanted_time,
                                        )
                                        LOG.info(
                                            "PVP Wanted countdown target=%d active_actor=%d "
                                            "turn_clock=%d remaining=%d round=%d",
                                            wanted_index, actor_index,
                                            current_pvp_wanted_turn_clock,
                                            remaining, round_number,
                                        )
                                    else:
                                        wanted_event = pvp_wanted_expiry_event_result_body(
                                            gamers[wanted_index],
                                            target_index=wanted_index,
                                            reward=payout,
                                            event_id=current_pvp_event_id,
                                            event_time=wanted_time,
                                        )
                                        LOG.info(
                                            "PVP Wanted expired target=%d active_actor=%d "
                                            "reward=%d turn_clock=%d round=%d",
                                            wanted_index, actor_index, payout,
                                            current_pvp_wanted_turn_clock, round_number,
                                        )
                                    queue_trio_frame(
                                        prepare_delay,
                                        255,
                                        2,
                                        pvp_event_notification_body(
                                            wanted_event,
                                            event_info,
                                            server_time=wanted_time,
                                        ),
                                    )
                                    prepare_delay = 0.0
                                prepare_time = server_time + int(
                                    round(timeline_elapsed + prepare_delay)
                                )
                                prepare_info = trio_snapshot(
                                    round_number, actor_index, status=3
                                )
                                queue_trio_frame(
                                    prepare_delay,
                                    255,
                                    1,
                                    pvp_next_round_body(
                                        gamers[actor_index],
                                        prepare_info,
                                        round_number=round_number,
                                        server_time=prepare_time,
                                    ),
                                )
                                active_time = server_time + int(
                                    round(timeline_elapsed + active_delay)
                                )
                                active_info = trio_snapshot(
                                    round_number, actor_index, status=2
                                )
                                queue_trio_frame(
                                    active_delay,
                                    255,
                                    1,
                                    pvp_next_round_body(
                                        gamers[actor_index],
                                        active_info,
                                        round_number=round_number,
                                        server_time=active_time,
                                    ),
                                )

                            def queue_player_round_start(
                                round_number: int,
                                settle_delay: float,
                            ) -> None:
                                nonlocal current_pvp_round, current_pvp_turn
                                nonlocal current_pvp_ready_at, current_pvp_event_id
                                nonlocal current_pvp_player
                                current_pvp_round = round_number
                                if real_ammo[0] + current_pvp_damage_bonus[0] <= 0:
                                    player_gun = parse_bytes_field(gamers[0], 7) or b""
                                    real_ammo[0], fake_ammo[0] = _reload_weapon_ammo(
                                        parse_varint_field(player_gun, 1) or 0,
                                        current_pvp_damage_bonus, 0,
                                        randomize=state.randomize_magazines,
                                    )
                                    gamers[0] = pvp_gamer_with_state(
                                        gamers[0],
                                        weapon_reloaded=True,
                                        hp=hit_points[0],
                                        ammo_number=real_ammo[0],
                                        fake_ammo_number=fake_ammo[0],
                                        enhanced_ammo_number=current_pvp_damage_bonus[0],
                                        round_number=round_number,
                                    )
                                    current_pvp_player = gamers[0]
                                    LOG.info(
                                        "PVP trio auto-reload player gun on turn start real=%d fake=%d",
                                        real_ammo[0], fake_ammo[0],
                                    )
                                carried_slot = (
                                    parse_bytes_field(current_pvp_player, 18) or b""
                                )
                                carried_cfg_id = (
                                    parse_varint_field(carried_slot, 2) or 0
                                )
                                carried_rate = PIGGYBANK_COINS_PER_TURN.get(
                                    carried_cfg_id, 0
                                )
                                if carried_rate > 0:
                                    stored_coins = max(
                                        0, parse_varint_field(carried_slot, 7) or 0
                                    )
                                    carried_slot = pvp_card_slot_with_arg(
                                        carried_slot, stored_coins + carried_rate
                                    )
                                    current_pvp_player = pvp_gamer_with_coin_and_card(
                                        current_pvp_player,
                                        coin=parse_varint_field(
                                            current_pvp_player, 5
                                        ) or 0,
                                        card_slot=carried_slot,
                                    )
                                    gamers[0] = current_pvp_player
                                queue_actor_start(
                                    0,
                                    current_pvp_round,
                                    min(PREPARE_SIGNAL_DELAY, max(0.0, settle_delay)),
                                    max(0.0, settle_delay - PREPARE_SIGNAL_DELAY),
                                )
                                if carried_rate > 0:
                                    current_pvp_event_id += 1
                                    piggybank_event = pvp_piggybank_round_start_event_result_body(
                                        current_pvp_player,
                                        carried_slot,
                                        event_id=current_pvp_event_id,
                                        event_time=server_time
                                        + int(round(timeline_elapsed)),
                                    )
                                    queue_trio_frame(
                                        0.0,
                                        255,
                                        2,
                                        pvp_event_notification_body(
                                            piggybank_event,
                                            current_pvp_info,
                                            server_time=server_time
                                            + int(round(timeline_elapsed)),
                                        ),
                                    )
                                current_pvp_turn = 0
                                current_pvp_ready_at = (
                                    time.monotonic() + timeline_elapsed
                                )

                            alive_after_player = [
                                idx for idx, (hp, vhp) in enumerate(
                                    zip(hit_points, virtual_hit_points)
                                ) if not _pvp_is_eliminated(hp, vhp)
                            ]
                            match_ended = len(alive_after_player) <= 1
                            first_bot = next(
                                (
                                    idx
                                    for idx in (1, 2)
                                    if not _pvp_is_eliminated(
                                        hit_points[idx], virtual_hit_points[idx]
                                    )
                                ),
                                None,
                            )
                            player_died_on_shot = _pvp_is_eliminated(
                                hit_points[0], virtual_hit_points[0]
                            )
                            event_info = trio_snapshot(
                                current_pvp_round,
                                0 if self_blank_continues else (
                                    first_bot if first_bot is not None else 0
                                ),
                                status=4 if match_ended else 2,
                            )
                            source_status = 0
                            target_status = 0
                            target_eliminated = _pvp_is_eliminated(
                                hit_points[target_index],
                                virtual_hit_points[target_index],
                            )
                            if target_eliminated:
                                if target_index == 0:
                                    source_status, target_status = 1, 5
                                else:
                                    source_status, target_status = 2, 4
                            first_shot_cfg, first_shot_delta, first_real_after, first_fake_after, first_dead = player_shots[0]
                            player_event = pvp_shoot_event_result_body(
                                gamers[0],
                                gamers[target_index],
                                0,
                                target_index,
                                ammo_cfg_id=first_shot_cfg,
                                target_hp_delta=first_shot_delta,
                                target_virtual_hp_delta=player_virtual_hp_deltas[0],
                                target_virtual_hp_cap_delta=player_virtual_hp_cap_deltas[0],
                                additional_virtual_hp_cap_deltas=tuple(player_virtual_hp_cap_deltas[1:]),
                                additional_virtual_hp_deltas=tuple(
                                    player_virtual_hp_deltas[1:]
                                ),
                                source_virtual_hp_delta=(
                                    player_source_virtual_hp_deltas[0]
                                ),
                                additional_source_virtual_hp_deltas=tuple(
                                    player_source_virtual_hp_deltas[1:]
                                ),
                                source_dead_after_shots=tuple(
                                    player_source_dead_after_shots
                                ),
                                source_ammo_after=first_real_after,
                                source_fake_ammo_after=first_fake_after,
                                target_dead=first_dead,
                                is_end_pvp=match_ended,
                                shoot_self_num=self_shots[0],
                                event_id=current_pvp_event_id,
                                is_next_round=not match_ended,
                                event_time=event_time,
                                source_event_status=source_status,
                                target_event_status=target_status,
                                additional_shots=tuple(player_shots[1:]),
                                ghosts_added_real_after_shots=tuple(player_ghosts_added),
                                weapon_extra_shot_active=shot_count > (2 if burst_active else 1),
                                toxin_applied=toxin_applied,
                                del_buff_cfg=(
                                    BURST_MODE_BUFF_CFG_ID if burst_pending else None
                                ),
                                del_buff_cfgs=(
                                    (MAINTENANCE_KIT_BUFF_CFG_ID,)
                                    if maintenance_expired else ()
                                ),
                                source_coin_delta=(
                                    weapon_reward + (wanted_reward_on_shot if target_index != 0 else 0)
                                ),
                                target_coin_delta=(
                                    wanted_reward_on_shot if target_index == 0 else 0
                                ),
                                coin_reason=7 if wanted_reward_on_shot else 8,
                                target_del_buff_cfgs=(
                                    (
                                        WANTED_PARENT_BUFF_CFG_ID,
                                        WANTED_REWARD_BUFF_CFG_ID,
                                    )
                                    if wanted_reward_on_shot else ()
                                ) + tuple(player_katie_consumed),
                                reload_ammo_after=player_reload_ammo,
                                continue_shoot=(
                                    next_self_coin, current_pvp_self_shoot_pool,
                                    int(self_blank_continues), continue_bonus,
                                ),
                            )
                            post_frames.append(
                                encode_frame(
                                    255,
                                    2,
                                    pvp_event_notification_body(
                                        player_event,
                                        event_info,
                                        server_time=event_time,
                                    ),
                                    error=0,
                                    index=0,
                                    length_mode=length_mode,
                                )
                            )

                            if match_ended:
                                winner = alive_after_player[0]
                                ranks = {winner: 1}
                                for death_order, eliminated in enumerate(
                                    current_pvp_eliminated_order
                                ):
                                    ranks[eliminated] = max(2, 3 - death_order)
                                for gamer_index in range(3):
                                    gamers[gamer_index] = pvp_gamer_with_state(
                                        gamers[gamer_index],
                                        hp=hit_points[gamer_index],
                                        ammo_number=real_ammo[gamer_index],
                                        fake_ammo_number=fake_ammo[gamer_index],
                                        enhanced_ammo_number=current_pvp_damage_bonus[gamer_index],
                                        round_number=current_pvp_round,
                                        is_dead=_pvp_is_eliminated(
                                            hit_points[gamer_index],
                                            virtual_hit_points[gamer_index],
                                        ),
                                        virtual_hp=virtual_hit_points[gamer_index],
                                        rank=ranks.get(gamer_index, 2),
                                    )
                                current_pvp_player, current_pvp_bot, current_pvp_extra_bot = gamers
                                current_pvp_info = pvp_info_with_end(
                                    pvp_info_with_state(
                                        current_pvp_info,
                                        gamers[0],
                                        gamers[1],
                                        round_number=current_pvp_round,
                                        turn_number=current_pvp_turn_number,
                                        current_index=winner,
                                        status=4,
                                        additional_gamers=(gamers[2],),
                                    ),
                                    end_time=event_time,
                                )
                                end_delay = 0.2 if player_died_on_shot else 2.5
                                if player_died_on_shot:
                                    queue_trio_frame(
                                        0.2,
                                        255,
                                        15,
                                        pvp_gamer_dead_body(event_info),
                                    )
                                queue_trio_frame(
                                    end_delay,
                                    255,
                                    5,
                                    pvp_end_body(current_pvp_info),
                                )
                                current_pvp_turn = -1
                                LOG.info(
                                    "PVP trio ended on local shot target=%d ammoCfg=%d "
                                    "eventStatus=%d/%d winner=%d ranks=%s",
                                    target_index,
                                    player_ammo_cfg,
                                    source_status,
                                    target_status,
                                    winner,
                                    ranks,
                                )
                            elif self_blank_continues:
                                # A blank self-shot keeps the same turn.  Do
                                # not run bots, award a new turn, or tick the
                                # piggy bank; return control after the shot
                                # animation.  If it was the last cartridge,
                                # publish a full magazine automatically.
                                settle = max(
                                    0.0,
                                    PLAYER_CONTINUE_SHOT_SETTLE - timeline_elapsed,
                                )
                                if real_ammo[0] + fake_ammo[0] <= 0:
                                    reload_info = recover_empty_player_magazine(
                                        increment_turn=False
                                    )
                                    gamers[0] = current_pvp_player
                                    real_ammo[0] = current_pvp_player_ammo
                                    fake_ammo[0] = current_pvp_player_fake_ammo
                                    queue_trio_frame(settle, 255, 1, reload_info)
                                else:
                                    # Keep the same player's self-aim/continue
                                    # UI alive. Pvp_Prepare/PvpIng are operator
                                    # transitions; the client resets aim when
                                    # they arrive, so do not replay them for a
                                    # blank self-shot. event_info already
                                    # publishes this player as active (status 2).
                                    current_pvp_info = event_info
                                    current_pvp_ready_at = (
                                        time.monotonic() + timeline_elapsed + settle
                                    )
                                current_pvp_turn = 0
                                if real_ammo[0] + fake_ammo[0] <= 0:
                                    current_pvp_ready_at = (
                                        time.monotonic() + timeline_elapsed
                                    )
                                LOG.info(
                                    "PVP trio blank self-shot continues same operator without round reset; ammo=%d/%d",
                                    real_ammo[0], fake_ammo[0],
                                )
                            else:
                                if player_died_on_shot:
                                    queue_trio_frame(
                                        0.2,
                                        255,
                                        15,
                                        pvp_gamer_dead_body(event_info),
                                    )
                                player_animation_delay = (
                                    PLAYER_SELF_SHOT_SETTLE
                                    if target_index == 0
                                    else PLAYER_OTHER_SHOT_SETTLE
                                )
                                first_prepare_delay = min(
                                    PREPARE_SIGNAL_DELAY,
                                    max(0.0, player_animation_delay - timeline_elapsed),
                                )
                                first_active_delay = max(
                                    0.0,
                                    player_animation_delay
                                    - timeline_elapsed
                                    - first_prepare_delay,
                                )
                                if first_bot is None and not _pvp_is_eliminated(
                                    hit_points[0], virtual_hit_points[0]
                                ):
                                    LOG.warning(
                                        "PVP trio has no bot with ammunition; returning to player"
                                    )
                                    queue_player_round_start(
                                        current_pvp_round + 1,
                                        max(
                                            0.0,
                                            player_animation_delay - timeline_elapsed,
                                        ),
                                    )
                                elif first_bot is None:
                                    LOG.error(
                                        "PVP trio stalemate: local player dead and bots have no ammunition"
                                    )
                                    current_pvp_turn = -1
                                else:
                                    queue_actor_start(
                                        first_bot,
                                        current_pvp_round,
                                        first_prepare_delay,
                                        first_active_delay,
                                    )
                                    bot_queue = [
                                        idx
                                        for idx in (1, 2)
                                        if idx > first_bot and not _pvp_is_eliminated(
                                            hit_points[idx], virtual_hit_points[idx]
                                        )
                                    ]
                                    actor_index = first_bot
                                    player_death_notified = player_died_on_shot
                                    bot_settle_delay, bot_think_budget = _pvp_bot_timing(
                                        player_eliminated=player_death_notified
                                    )
                                    def finish_bot_match(settlement: float = 0.0) -> None:
                                        nonlocal current_pvp_info, current_pvp_turn
                                        nonlocal current_pvp_player, current_pvp_bot, current_pvp_extra_bot
                                        survivors = [i for i in range(3) if not _pvp_is_eliminated(hit_points[i], virtual_hit_points[i])]
                                        winner = survivors[0]
                                        ranks = {winner: 1}
                                        for death_order, eliminated in enumerate(
                                            current_pvp_eliminated_order
                                        ):
                                            ranks[eliminated] = max(
                                                2, 3 - death_order
                                            )
                                        for gamer_index in range(3):
                                            gamers[gamer_index] = pvp_gamer_with_state(
                                                gamers[gamer_index],
                                                hp=hit_points[gamer_index],
                                                ammo_number=real_ammo[gamer_index],
                                                fake_ammo_number=fake_ammo[gamer_index],
                                                enhanced_ammo_number=current_pvp_damage_bonus[gamer_index],
                                                round_number=current_pvp_round,
                                                is_dead=_pvp_is_eliminated(
                                                    hit_points[gamer_index],
                                                    virtual_hit_points[gamer_index],
                                                ),
                                                virtual_hp=virtual_hit_points[gamer_index],
                                                rank=ranks.get(gamer_index, 2),
                                            )
                                        current_pvp_player, current_pvp_bot, current_pvp_extra_bot = gamers
                                        current_pvp_info = pvp_info_with_end(
                                            pvp_info_with_state(
                                                current_pvp_info,
                                                gamers[0],
                                                gamers[1],
                                                round_number=current_pvp_round,
                                                turn_number=current_pvp_turn_number,
                                                current_index=winner,
                                                status=4,
                                                additional_gamers=(gamers[2],),
                                            ),
                                            end_time=server_time
                                            + int(round(timeline_elapsed)),
                                        )
                                        queue_trio_frame(
                                            settlement + (0.2 if player_death_notified else 2.5),
                                            255,
                                            5,
                                            pvp_end_body(current_pvp_info),
                                        )
                                        current_pvp_turn = -1
                                        LOG.info(
                                            "PVP trio ended winner=%d ranks=%s round=%d",
                                            winner,
                                            ranks,
                                            current_pvp_round,
                                        )
                                        return

                                    match_ended = False
                                    while actor_index is not None and not match_ended:
                                        bot_blank_continues = False
                                        bot_settle_delay, bot_think_budget = _pvp_bot_timing(
                                            player_eliminated=player_death_notified
                                        )
                                        if _pvp_is_eliminated(
                                            hit_points[actor_index],
                                            virtual_hit_points[actor_index],
                                        ):
                                            actor_index = next(
                                                (
                                                    idx for idx in bot_queue
                                                    if not _pvp_is_eliminated(
                                                        hit_points[idx],
                                                        virtual_hit_points[idx],
                                                    )
                                                ),
                                                None,
                                            )
                                            bot_queue = [
                                                idx for idx in bot_queue
                                                if not _pvp_is_eliminated(
                                                    hit_points[idx], virtual_hit_points[idx]
                                                )
                                            ]
                                            continue
                                        if real_ammo[actor_index] + fake_ammo[actor_index] + current_pvp_damage_bonus[actor_index] <= 0:
                                            LOG.warning(
                                                "PVP trio bot %d has no ammo; skipping its action",
                                                actor_index,
                                            )
                                            ready_queue = [
                                                idx
                                                for idx in bot_queue
                                                if not _pvp_is_eliminated(
                                                    hit_points[idx], virtual_hit_points[idx]
                                                )
                                            ]
                                            if ready_queue:
                                                next_actor = ready_queue[0]
                                                bot_queue = ready_queue[1:]
                                                queue_actor_start(
                                                    next_actor,
                                                    current_pvp_round,
                                                    PREPARE_SIGNAL_DELAY,
                                                    max(
                                                        0.0,
                                                        bot_settle_delay
                                                        - PREPARE_SIGNAL_DELAY,
                                                    ),
                                                )
                                                actor_index = next_actor
                                                continue
                                            if not _pvp_is_eliminated(
                                                hit_points[0], virtual_hit_points[0]
                                            ):
                                                queue_player_round_start(
                                                    current_pvp_round + 1,
                                                    bot_settle_delay,
                                                )
                                                break
                                            ready_bots = [
                                                idx
                                                for idx in (1, 2)
                                                if not _pvp_is_eliminated(
                                                    hit_points[idx], virtual_hit_points[idx]
                                                )
                                            ]
                                            if ready_bots:
                                                current_pvp_round += 1
                                                next_actor = ready_bots[0]
                                                bot_queue = ready_bots[1:]
                                                queue_actor_start(
                                                    next_actor,
                                                    current_pvp_round,
                                                    PREPARE_SIGNAL_DELAY,
                                                    max(
                                                        0.0,
                                                        bot_settle_delay
                                                        - PREPARE_SIGNAL_DELAY,
                                                    ),
                                                )
                                                actor_index = next_actor
                                                continue
                                            LOG.error(
                                                "PVP trio stalemate: remaining bots have no ammunition"
                                            )
                                            break
                                        else:
                                            selected_action = None
                                            action_delay = bot_pending_start_delay
                                            bot_pending_start_delay = 0.0
                                            if state.bot_difficulty != "scripted":
                                                actions = BattleActions(
                                                    gamers, hit_points, virtual_hit_points,
                                                    real_ammo, fake_ammo, self_shots,
                                                    current_pvp_damage_bonus, current_pvp_maintenance_bonus,
                                                    current_pvp_burst_mode, current_pvp_bucket_guard,
                                                    list(parse_bytes_fields(current_pvp_info, 7)),
                                                    current_pvp_round, current_pvp_shop_next_id,
                                                    current_pvp_restrictions, bot_rng,
                                                    reload=lambda gun_id: pvp_gun_ammo_counts(
                                                        gun_id, randomize=state.randomize_magazines),
                                                    draw=_draw_ejected_ammo, damage=_pvp_apply_hp_damage,
                                                    forced_shot=_resolve_hallucinogen_self_shot,
                                                    apply_wanted=lambda target, source: _pvp_apply_wanted(
                                                        gamers, target, current_pvp_wanted_reward,
                                                        current_pvp_wanted_expire_turn,
                                                        current_pvp_wanted_turn_clock, source_index=source),
                                                    randomize_magazines=state.randomize_magazines,
                                                    katie_guards=current_pvp_katie_guards,
                                                )
                                                limit = DIFFICULTIES[state.bot_difficulty].max_preparations
                                                pending = max(action_delay, 1.0)
                                                while bot_preparations[actor_index] < limit:
                                                    selected_action = choose_action(
                                                        actions.observation(actor_index, bot_preparations[actor_index], bot_self_streaks[actor_index]),
                                                        bot_rng, state.bot_difficulty)
                                                    if selected_action is None or selected_action.kind == "shoot":
                                                        break
                                                    # Wait only before executing the next action; native HUD
                                                    # effects remain in this action's normal event packet.
                                                    pending += BOT_ACTION_DECISION_DELAY
                                                    current_pvp_event_id += 1
                                                    action_time = server_time + int(round(timeline_elapsed + pending))
                                                    resolved = actions.resolve(
                                                        actor_index, selected_action,
                                                        event_id=current_pvp_event_id, event_time=action_time,
                                                        difficulty=state.bot_difficulty,
                                                        preparations=bot_preparations[actor_index])
                                                    if resolved is None:
                                                        LOG.warning("BOT stale action rejected actor=%d kind=%s", actor_index, selected_action.kind)
                                                        break
                                                    packet, settlement = resolved
                                                    current_pvp_shop_next_id = actions.next_card_id
                                                    bot_preparations[actor_index] += 1
                                                    current_pvp_info = pvp_info_with_shop(
                                                        trio_snapshot(current_pvp_round, actor_index),
                                                        actions.shop, parse_varint_field(current_pvp_info, 41) or 0)
                                                    queue_trio_frame(pending, 255, 2,
                                                        pvp_event_notification_body(packet, current_pvp_info, server_time=action_time))
                                                    LOG.info("BOT decision actor=%d difficulty=%s kind=%s target=%d cfg=%d score=%.3f reason=%s",
                                                        actor_index, state.bot_difficulty, selected_action.kind,
                                                        selected_action.target, selected_action.offer.cfg if selected_action.offer else 0,
                                                        selected_action.score, selected_action.reason)
                                                    LOG.info("BOT animation barrier actor=%d next_action_wait=%.2fs (native HUD callbacks unchanged)", actor_index, settlement)
                                                    pending = settlement
                                                    for idx in range(3):
                                                        if _pvp_is_eliminated(hit_points[idx], virtual_hit_points[idx]) and idx not in current_pvp_eliminated_order:
                                                            current_pvp_eliminated_order.append(idx)
                                                    if not player_death_notified and _pvp_is_eliminated(hit_points[0], virtual_hit_points[0]):
                                                        player_death_notified = True
                                                        queue_trio_frame(0.2, 255, 15, pvp_gamer_dead_body(current_pvp_info))
                                                        pending = max(0, pending - .2)
                                                    survivors = [i for i in range(3) if not _pvp_is_eliminated(hit_points[i], virtual_hit_points[i])]
                                                    match_ended = len(survivors) <= 1
                                                    if match_ended or _pvp_is_eliminated(hit_points[actor_index], virtual_hit_points[actor_index]):
                                                        break
                                                action_delay = pending if bot_preparations[actor_index] else action_delay
                                                if match_ended:
                                                    finish_bot_match(action_delay)
                                                    break
                                                if _pvp_is_eliminated(hit_points[actor_index], virtual_hit_points[actor_index]):
                                                    bot_pending_start_delay = action_delay
                                                    continue
                                                selected_action = choose_action(
                                                    actions.observation(actor_index, limit, bot_self_streaks[actor_index]),
                                                    bot_rng, state.bot_difficulty)
                                            bot_target = selected_action.target if selected_action is not None else (
                                                0
                                                if not _pvp_is_eliminated(
                                                    hit_points[0], virtual_hit_points[0]
                                                )
                                                else next(
                                                    idx
                                                    for idx in (1, 2)
                                                    if idx != actor_index
                                                    and not _pvp_is_eliminated(
                                                        hit_points[idx],
                                                        virtual_hit_points[idx],
                                                    )
                                                )
                                            )
                                            if selected_action is not None:
                                                LOG.info("BOT decision actor=%d difficulty=%s kind=shoot target=%d score=%.3f reason=%s",
                                                    actor_index, state.bot_difficulty, bot_target,
                                                    selected_action.score, selected_action.reason)
                                            if bot_target != actor_index and bot_self_pots[actor_index]:
                                                payout = bot_self_pots[actor_index]
                                                coin = parse_varint_field(gamers[actor_index], 5) or 0
                                                gamers[actor_index] = pvp_gamer_with_coin_and_card(
                                                    gamers[actor_index], coin=coin + payout)
                                                bot_self_pots[actor_index] = 0
                                                bot_self_streaks[actor_index] = 0
                                                current_pvp_event_id += 1
                                                queue_trio_frame(action_delay, 255, 2,
                                                    pvp_event_notification_body(
                                                        pvp_collect_self_shot_event_result_body(
                                                            gamers[actor_index], payout,
                                                            event_id=current_pvp_event_id,
                                                            event_time=server_time + int(round(timeline_elapsed + action_delay)),
                                                            passive=True),
                                                        trio_snapshot(current_pvp_round, actor_index)))
                                                action_delay = 1.0
                                            queue_trio_frame(
                                                action_delay + BOT_RAISE_GUN_DELAY,
                                                255,
                                                4,
                                                pvp_behavior_notification_body(
                                                    actor_index, 1, bot_target
                                                ),
                                            )
                                            queue_trio_frame(
                                                BOT_SELECT_TARGET_DELAY,
                                                255,
                                                4,
                                                pvp_behavior_notification_body(
                                                    actor_index, 4, bot_target
                                                ),
                                            )
                                            think_delay = max(
                                                0.0,
                                                bot_think_budget
                                                - BOT_RAISE_GUN_DELAY
                                                - BOT_SELECT_TARGET_DELAY,
                                            )
                                            burst_pending, burst_active = _pvp_burst_shot_state(
                                                current_pvp_burst_mode[actor_index],
                                                actor_index,
                                                bot_target,
                                            )
                                            if burst_pending:
                                                current_pvp_burst_mode[actor_index] = 0
                                                LOG.info(
                                                    "PVP Burst Mode consumed shooter=%d target=%d double_shot=%s",
                                                    actor_index, bot_target, burst_active,
                                                )
                                            maintenance_active_for_shot = bool(
                                                current_pvp_maintenance_bonus[actor_index]
                                            )
                                            bot_shots: list[tuple[int, int, int, int, bool]] = []
                                            bot_bucket_consumed = False
                                            bot_katie_consumed = []
                                            bot_virtual_hp_deltas: list[int] = []
                                            bot_virtual_hp_cap_deltas: list[int] = []
                                            bot_source_virtual_hp_deltas: list[int] = []
                                            bot_ghosts_added: list[int] = []
                                            bot_source_dead_after_shots: list[bool] = []
                                            shot_damage = 0
                                            shot_count = normal_shot_count(
                                                parse_varint_field(parse_bytes_field(gamers[actor_index], 7) or b'', 1) or 0,
                                                real_ammo[actor_index], fake_ammo[actor_index],
                                                current_pvp_damage_bonus[actor_index],actor_index,bot_target,burst_active)
                                            for shot_number in range(shot_count):
                                                bot_ammo_cfg = _draw_loaded_ammo(
                                                    real_ammo[actor_index], fake_ammo[actor_index], current_pvp_damage_bonus[actor_index],
                                                    gun_id=parse_varint_field(parse_bytes_field(gamers[actor_index], 7) or b'', 1) or 0,
                                                )
                                                if bot_ammo_cfg is None:
                                                    break
                                                blocked_katie = intercept_katie(gamers,current_pvp_katie_guards,actor_index,bot_target,bot_ammo_cfg)
                                                if blocked_katie:
                                                    bot_katie_consumed.append(blocked_katie)
                                                    LOG.info("PVP Katie intercept shooter=%d target=%d cfg=%d",actor_index,bot_target,bot_ammo_cfg)
                                                if bot_ammo_cfg == 300:
                                                    fake_ammo[actor_index] -= 1
                                                    shot_damage = 0
                                                    target_hp_delta = 0
                                                    target_virtual_hp_delta = 0
                                                else:
                                                    if bot_ammo_cfg == 1:
                                                        real_ammo[actor_index] -= 1
                                                    shot_damage = _pvp_shot_damage(
                                                        bot_ammo_cfg,
                                                        enhanced_ammo_bonus=current_pvp_damage_bonus[actor_index],
                                                        maintenance_kit_active=maintenance_active_for_shot,
                                                        shooter_index=actor_index,
                                                        target_index=bot_target,
                                                    )
                                                    if bot_ammo_cfg == 2:
                                                        current_pvp_damage_bonus[actor_index] -= 1
                                                    if blocked_katie:
                                                        shot_damage = 0
                                                    elif current_pvp_bucket_guard[bot_target]:
                                                        shot_damage = 0
                                                        current_pvp_bucket_guard[bot_target] = False
                                                        bot_bucket_consumed = True
                                                    (
                                                        hit_points[bot_target],
                                                        virtual_hit_points[bot_target],
                                                        target_hp_delta,
                                                        target_virtual_hp_delta,
                                                    ) = _pvp_apply_hp_damage(
                                                        hit_points[bot_target],
                                                        virtual_hit_points[bot_target],
                                                        shot_damage,
                                                    )
                                                diana_delta, diana_cap_delta = _pvp_diana_after_normal_shot(
                                                    gamers, virtual_hit_points, actor_index, bot_target,
                                                    bot_ammo_cfg, target_hp_delta, target_virtual_hp_delta)
                                                target_virtual_hp_delta += diana_delta
                                                bot_virtual_hp_cap_deltas.append(diana_cap_delta)
                                                (
                                                    virtual_hit_points[actor_index],
                                                    source_virtual_hp_delta,
                                                ) = _pvp_frenzy_after_shot(
                                                    virtual_hit_points[actor_index],
                                                    _pvp_virtual_hp_cap(
                                                        gamers[actor_index]
                                                    ),
                                                    bot_ammo_cfg,
                                                    max(
                                                        0,
                                                        -target_hp_delta
                                                        - target_virtual_hp_delta,
                                                    ),
                                                    actor_index,
                                                    bot_target,
                                                )
                                                gamers[actor_index], added_real = pvp_ghosts_after_shot(
                                                    gamers[actor_index], bot_ammo_cfg)
                                                real_ammo[actor_index] += added_real
                                                bot_ghosts_added.append(added_real)
                                                bot_shots.append((
                                                    bot_ammo_cfg,
                                                    target_hp_delta,
                                                    real_ammo[actor_index],
                                                    fake_ammo[actor_index],
                                                    _pvp_is_eliminated(
                                                        hit_points[bot_target],
                                                        virtual_hit_points[bot_target],
                                                    ),
                                                ))
                                                bot_virtual_hp_deltas.append(
                                                    target_virtual_hp_delta
                                                )
                                                bot_source_virtual_hp_deltas.append(
                                                    source_virtual_hp_delta
                                                )
                                                bot_source_dead_after_shots.append(
                                                    _pvp_is_eliminated(
                                                        hit_points[actor_index],
                                                        virtual_hit_points[actor_index],
                                                    )
                                                )
                                                if _pvp_is_eliminated(
                                                    hit_points[bot_target],
                                                    virtual_hit_points[bot_target],
                                                ) or bot_source_dead_after_shots[-1]:
                                                    break
                                            maintenance_expired = _maintenance_kit_expires_after_shot(
                                                maintenance_active_for_shot,
                                                actor_index,
                                                bot_target,
                                                bot_shots,
                                            )
                                            if maintenance_expired:
                                                current_pvp_maintenance_bonus[actor_index] = 0
                                            if not bot_shots:
                                                LOG.warning("PVP trio bot %d had no drawable round", actor_index)
                                                break
                                            gamers[actor_index], weapon_reward = _pvp_carnivore_reward(
                                                gamers[actor_index],actor_index,bot_target,bot_shots,bot_virtual_hp_deltas)
                                            toxin_applied = _pvp_venom_after_shots(gamers,actor_index,bot_target,
                                                bot_shots,bot_virtual_hp_deltas,current_pvp_restrictions)
                                            if bot_bucket_consumed:
                                                gamers[bot_target] = pvp_gamer_with_buffs(
                                                    gamers[bot_target], del_cfg_ids=(ITEM_BUFF_CFG[2033],),
                                                )
                                            wanted_reward_on_shot = (
                                                current_pvp_wanted_reward[bot_target]
                                                if any(
                                                    shot[1] < 0
                                                    or bot_virtual_hp_deltas[index] < 0
                                                    for index, shot in enumerate(bot_shots)
                                                )
                                                else 0
                                            )
                                            if wanted_reward_on_shot:
                                                bot_coin = (
                                                    parse_varint_field(
                                                        gamers[actor_index], 5
                                                    ) or 0
                                                )
                                                gamers[actor_index] = (
                                                    pvp_gamer_with_coin_and_card(
                                                        gamers[actor_index],
                                                        coin=bot_coin + wanted_reward_on_shot,
                                                    )
                                                )
                                                gamers[bot_target] = pvp_gamer_with_buffs(
                                                    gamers[bot_target],
                                                    del_cfg_ids=(
                                                        WANTED_PARENT_BUFF_CFG_ID,
                                                        WANTED_REWARD_BUFF_CFG_ID,
                                                    ),
                                                )
                                                current_pvp_wanted_reward[bot_target] = 0
                                                current_pvp_wanted_expire_turn[
                                                    bot_target
                                                ] = 0
                                                LOG.info(
                                                    "PVP Wanted claimed shooter=%d target=%d reward=%d",
                                                    actor_index,
                                                    bot_target,
                                                    wanted_reward_on_shot,
                                                )
                                            bot_ammo_cfg = bot_shots[0][0]
                                            bot_blank_continues = (
                                                bot_target == actor_index and bot_ammo_cfg == 300
                                                and not _pvp_is_eliminated(hit_points[actor_index], virtual_hit_points[actor_index]))
                                            bot_self_reward = 0
                                            bot_self_coin_delta = 0
                                            if bot_blank_continues:
                                                bot_self_reward = _trio_self_shot_reward(
                                                    real_ammo[actor_index] + current_pvp_damage_bonus[actor_index], fake_ammo[actor_index] + 1,
                                                    bot_self_streaks[actor_index],
                                                    gun_id=parse_varint_field(parse_bytes_field(gamers[actor_index],7) or b'',1) or 0)
                                                bot_self_streaks[actor_index] += 1
                                                bot_self_pots[actor_index] += bot_self_reward
                                            elif bot_target == actor_index:
                                                self_shots[actor_index] += 1
                                                bot_self_coin_delta = bot_self_pots[actor_index] // 2
                                                bot_self_pots[actor_index] = 0
                                                bot_self_streaks[actor_index] = 0
                                                if bot_self_coin_delta:
                                                    coin = parse_varint_field(gamers[actor_index], 5) or 0
                                                    gamers[actor_index] = pvp_gamer_with_coin_and_card(
                                                        gamers[actor_index], coin=coin + bot_self_coin_delta)
                                            if (
                                                _pvp_is_eliminated(
                                                    hit_points[bot_target],
                                                    virtual_hit_points[bot_target],
                                                )
                                                and bot_target not in current_pvp_eliminated_order
                                            ):
                                                current_pvp_eliminated_order.append(bot_target)
                                            current_pvp_event_id += 1
                                            if not bot_blank_continues:
                                                current_pvp_turn_number += 1
                                            survivors = [
                                                idx for idx, (hp, vhp) in enumerate(
                                                    zip(hit_points, virtual_hit_points)
                                                ) if not _pvp_is_eliminated(hp, vhp)
                                            ]
                                            match_ended = len(survivors) <= 1
                                            bot_reload_ammo = None
                                            if (
                                                not match_ended
                                                and real_ammo[actor_index] <= 0
                                                and current_pvp_damage_bonus[actor_index] <= 0
                                                and not _pvp_is_eliminated(hit_points[actor_index], virtual_hit_points[actor_index])
                                            ):
                                                bot_gun = parse_bytes_field(
                                                    gamers[actor_index], 7
                                                ) or b""
                                                real_ammo[actor_index], fake_ammo[actor_index] = (
                                                    _reload_weapon_ammo(
                                                        parse_varint_field(bot_gun, 1) or 0,
                                                        current_pvp_damage_bonus, actor_index,
                                                        randomize=state.randomize_magazines,
                                                    )
                                                )
                                                bot_reload_ammo = (
                                                    real_ammo[actor_index],
                                                    fake_ammo[actor_index],
                                                )
                                                gamers[actor_index] = pvp_gamer_after_weapon_reload(gamers[actor_index])
                                                LOG.info(
                                                    "PVP trio bot %d reload after last real shot real=%d fake=%d",
                                                    actor_index, *bot_reload_ammo,
                                                )
                                            live_queued_bots = [
                                                idx
                                                for idx in bot_queue
                                                if not _pvp_is_eliminated(
                                                    hit_points[idx], virtual_hit_points[idx]
                                                )
                                            ]
                                            next_actor = (
                                                live_queued_bots[0]
                                                if live_queued_bots
                                                else (
                                                    0 if not _pvp_is_eliminated(
                                                        hit_points[0], virtual_hit_points[0]
                                                    ) else None
                                                )
                                            )
                                            starts_new_round = False
                                            if bot_blank_continues:
                                                next_actor = actor_index
                                            if next_actor is None and not match_ended:
                                                # The human has been eliminated; keep the
                                                # two bots playing until one remains.
                                                live_bots = [
                                                    idx
                                                    for idx in (1, 2)
                                                    if not _pvp_is_eliminated(
                                                        hit_points[idx], virtual_hit_points[idx]
                                                    )
                                                ]
                                                if live_bots:
                                                    current_pvp_round += 1
                                                    starts_new_round = True
                                                    next_actor = live_bots[0]
                                                    live_queued_bots = live_bots[1:]
                                            next_index = (
                                                survivors[0]
                                                if match_ended
                                                else (next_actor if next_actor is not None else actor_index)
                                            )
                                            current_pvp_info = trio_snapshot(
                                                current_pvp_round
                                                - int(starts_new_round),
                                                next_index,
                                                status=4 if match_ended else 2,
                                            )
                                            bot_event_time = server_time + int(
                                                round(timeline_elapsed + think_delay)
                                            )
                                            first_bot_cfg, first_bot_delta, first_bot_real_after, first_bot_fake_after, first_bot_dead = bot_shots[0]
                                            bot_event = pvp_shoot_event_result_body(
                                                gamers[actor_index],
                                                gamers[bot_target],
                                                actor_index,
                                                bot_target,
                                                ammo_cfg_id=first_bot_cfg,
                                                target_hp_delta=first_bot_delta,
                                                target_virtual_hp_delta=bot_virtual_hp_deltas[0],
                                                target_virtual_hp_cap_delta=bot_virtual_hp_cap_deltas[0],
                                                additional_virtual_hp_cap_deltas=tuple(bot_virtual_hp_cap_deltas[1:]),
                                                additional_virtual_hp_deltas=tuple(
                                                    bot_virtual_hp_deltas[1:]
                                                ),
                                                source_virtual_hp_delta=(
                                                    bot_source_virtual_hp_deltas[0]
                                                ),
                                                additional_source_virtual_hp_deltas=tuple(
                                                    bot_source_virtual_hp_deltas[1:]
                                                ),
                                                source_dead_after_shots=tuple(
                                                    bot_source_dead_after_shots
                                                ),
                                                source_ammo_after=first_bot_real_after,
                                                source_fake_ammo_after=first_bot_fake_after,
                                                target_dead=first_bot_dead,
                                                is_end_pvp=match_ended,
                                                shoot_self_num=self_shots[actor_index],
                                                event_id=current_pvp_event_id,
                                                is_next_round=not match_ended and not bot_blank_continues,
                                                event_time=bot_event_time,
                                                source_event_status=(
                                                    (1 if bot_target == actor_index else 2) if _pvp_is_eliminated(
                                                        hit_points[bot_target],
                                                        virtual_hit_points[bot_target],
                                                    ) else 0
                                                ),
                                                target_event_status=(
                                                    (5 if bot_target == actor_index else 4) if _pvp_is_eliminated(
                                                        hit_points[bot_target],
                                                        virtual_hit_points[bot_target],
                                                    ) else 0
                                                ),
                                                additional_shots=tuple(bot_shots[1:]),
                                                ghosts_added_real_after_shots=tuple(bot_ghosts_added),
                                                weapon_extra_shot_active=shot_count > (2 if burst_active else 1),
                                                toxin_applied=toxin_applied,
                                                reload_ammo_after=bot_reload_ammo,
                                                continue_shoot=(
                                                    _trio_self_shot_reward(real_ammo[actor_index] + current_pvp_damage_bonus[actor_index], fake_ammo[actor_index], bot_self_streaks[actor_index],
                                                        gun_id=parse_varint_field(parse_bytes_field(gamers[actor_index],7) or b'',1) or 0),
                                                    bot_self_pots[actor_index], int(bot_blank_continues),
                                                    min(10, bot_self_streaks[actor_index]) * 100,
                                                ) if bot_target == actor_index else None,
                                                del_buff_cfg=(
                                                    BURST_MODE_BUFF_CFG_ID
                                                    if burst_pending else None
                                                ),
                                                del_buff_cfgs=(
                                                    (MAINTENANCE_KIT_BUFF_CFG_ID,)
                                                    if maintenance_expired else ()
                                                ),
                                                source_coin_delta=wanted_reward_on_shot + bot_self_coin_delta + weapon_reward,
                                                coin_reason=7,
                                                target_del_buff_cfgs=(
                                                    (
                                                        WANTED_PARENT_BUFF_CFG_ID,
                                                        WANTED_REWARD_BUFF_CFG_ID,
                                                    )
                                                    if wanted_reward_on_shot else ()
                                                ) + ((ITEM_BUFF_CFG[2033],) if bot_bucket_consumed else ()) + tuple(bot_katie_consumed),
                                            )
                                            queue_trio_frame(
                                                think_delay,
                                                255,
                                                2,
                                                pvp_event_notification_body(
                                                    bot_event,
                                                    current_pvp_info,
                                                    server_time=bot_event_time,
                                                ),
                                            )
                                            player_died_now = (
                                                not player_death_notified
                                                and _pvp_is_eliminated(
                                                    hit_points[0], virtual_hit_points[0]
                                                )
                                            )
                                            if player_died_now:
                                                player_death_notified = True
                                                bot_settle_delay, bot_think_budget = _pvp_bot_timing(
                                                    player_eliminated=True
                                                )
                                                queue_trio_frame(
                                                    0.2,
                                                    255,
                                                    15,
                                                    pvp_gamer_dead_body(current_pvp_info),
                                                )

                                        if match_ended:
                                            finish_bot_match()
                                            break

                                        if next_actor == 0:
                                            queue_player_round_start(
                                                current_pvp_round + 1,
                                                bot_settle_delay,
                                            )
                                            LOG.info(
                                                "PVP trio round=%d returns to player; alive=%s",
                                                current_pvp_round,
                                                [
                                                    idx for idx, (hp, vhp) in enumerate(
                                                        zip(hit_points, virtual_hit_points)
                                                    ) if not _pvp_is_eliminated(hp, vhp)
                                                ],
                                            )
                                            break

                                        if next_actor is not None:
                                            if next_actor == actor_index and bot_blank_continues:
                                                bot_pending_start_delay = bot_settle_delay
                                                continue
                                            bot_queue = [
                                                idx
                                                for idx in live_queued_bots
                                                if idx != next_actor
                                            ]
                                            if starts_new_round:
                                                bot_prepare_delay = min(
                                                    PREPARE_SIGNAL_DELAY,
                                                    max(
                                                        0.0,
                                                        bot_settle_delay
                                                        - (0.2 if player_died_now else 0.0),
                                                    ),
                                                )
                                                bot_active_delay = max(
                                                    0.0,
                                                    bot_settle_delay
                                                    - (0.2 if player_died_now else 0.0)
                                                    - bot_prepare_delay,
                                                )
                                            else:
                                                bot_prepare_delay = max(
                                                    0.0,
                                                    PREPARE_SIGNAL_DELAY
                                                    - (0.2 if player_died_now else 0.0),
                                                )
                                                bot_active_delay = max(
                                                    0.0,
                                                    bot_settle_delay
                                                    - (0.2 if player_died_now else 0.0)
                                                    - bot_prepare_delay,
                                                )
                                            queue_actor_start(
                                                next_actor,
                                                current_pvp_round,
                                                bot_prepare_delay,
                                                bot_active_delay,
                                            )
                                            actor_index = next_actor
                                            continue
                                        actor_index = None

                                    if current_pvp_turn == -1:
                                        current_pvp_ready_at = (
                                            time.monotonic() + timeline_elapsed
                                        )
                                    LOG.info(
                                        "PVP trio local shot target=%d ammoCfg=%d playerAmmo=%d/%d "
                                        "playerHP=%d botHP=%d extraBotHP=%d round=%d "
                                        "eventStatus=%d/%d queuedFrames=%d",
                                        target_index,
                                        player_ammo_cfg,
                                        real_ammo[0],
                                        fake_ammo[0],
                                        current_pvp_player_hp,
                                        current_pvp_bot_hp,
                                        current_pvp_extra_bot_hp,
                                        current_pvp_round,
                                        source_status,
                                        target_status,
                                        len(delayed_frames),
                                    )
                    else:
                        LOG.warning(
                            "PVP trio shoot ignored: invalid target=%r, room not ready, "
                            "turn pending, player dead, or ammo empty",
                            target_index,
                        )
                elif (head.cmd, head.act) == (3, 3):
                    # GamerPvpShootC2S.idx is the selected player's server
                    # index: 0 is the local player (shoot self), 1 is the bot.
                    # The old prototype forced every value to 1, which made a
                    # self-shot animate and damage the opponent.
                    target_index = parse_varint_field(body, 1)
                    empty_magazine_recovered = (
                        target_index in (0, 1)
                        and current_pvp_player
                        and current_pvp_bot
                        and current_pvp_info
                        and current_pvp_turn == 0
                        and time.monotonic() >= current_pvp_ready_at
                        and not _pvp_is_eliminated(
                            current_pvp_player_hp, current_pvp_player_virtual_hp
                        )
                        and not _pvp_is_eliminated(
                            current_pvp_bot_hp, current_pvp_bot_virtual_hp
                        )
                        and current_pvp_player_ammo + current_pvp_player_fake_ammo + current_pvp_damage_bonus[0] <= 0
                    )
                    if empty_magazine_recovered:
                        reload_info = recover_empty_player_magazine()
                        post_frames.append(encode_frame(
                            255,
                            1,
                            reload_info,
                            error=0,
                            index=0,
                            length_mode=length_mode,
                        ))
                    if (
                        target_index in (0, 1)
                        and current_pvp_player
                        and current_pvp_bot
                        and current_pvp_info
                        and current_pvp_turn == 0
                        and time.monotonic() >= current_pvp_ready_at
                        and not _pvp_is_eliminated(
                            current_pvp_player_hp, current_pvp_player_virtual_hp
                        )
                        and not _pvp_is_eliminated(
                            current_pvp_bot_hp, current_pvp_bot_virtual_hp
                        )
                        and current_pvp_player_ammo + current_pvp_player_fake_ammo + current_pvp_damage_bonus[0] > 0
                        and not empty_magazine_recovered
                    ):
                        out_body = b"\x08" + _varint(account.gid)
                        old_bot_hp = current_pvp_bot_hp
                        old_player_hp = current_pvp_player_hp
                        old_player_ammo = current_pvp_player_ammo
                        old_player_fake_ammo = current_pvp_player_fake_ammo
                        burst_pending, burst_active = _pvp_burst_shot_state(
                            current_pvp_burst_mode[0], 0, target_index
                        )
                        if burst_pending:
                            current_pvp_burst_mode[0] = 0
                            LOG.info(
                                "PVP Burst Mode consumed shooter=0 target=%d double_shot=%s",
                                target_index, burst_active,
                            )
                        maintenance_active_for_shot = bool(
                            current_pvp_maintenance_bonus[0]
                        )
                        player_shots: list[tuple[int, int, int, int, bool]] = []
                        player_virtual_hp_deltas: list[int] = []
                        player_source_virtual_hp_deltas: list[int] = []
                        player_ghosts_added: list[int] = []
                        player_source_dead_after_shots: list[bool] = []
                        shot_damage = 0
                        shot_count = normal_shot_count(
                            parse_varint_field(parse_bytes_field(current_pvp_player, 7) or b'', 1) or 0,
                            current_pvp_player_ammo,current_pvp_player_fake_ammo,
                            current_pvp_damage_bonus[0],0,target_index,burst_active)
                        for shot_number in range(shot_count):
                            player_ammo_cfg = _draw_loaded_ammo(
                                current_pvp_player_ammo, current_pvp_player_fake_ammo, current_pvp_damage_bonus[0],
                                gun_id=parse_varint_field(parse_bytes_field(current_pvp_player, 7) or b'', 1) or 0,
                            )
                            if player_ammo_cfg is None:
                                break
                            player_hit = player_ammo_cfg in (1, 2)
                            if player_ammo_cfg == 1:
                                current_pvp_player_ammo -= 1
                            elif player_ammo_cfg == 300:
                                current_pvp_player_fake_ammo -= 1
                            if player_hit:
                                shot_damage = _pvp_shot_damage(
                                    player_ammo_cfg,
                                    enhanced_ammo_bonus=current_pvp_damage_bonus[0],
                                    maintenance_kit_active=maintenance_active_for_shot,
                                    shooter_index=0,
                                    target_index=target_index,
                                )
                                if player_ammo_cfg == 2:
                                    current_pvp_damage_bonus[0] -= 1
                                guard_index = target_index
                                if current_pvp_bucket_guard[guard_index]:
                                    shot_damage = 0
                                    current_pvp_bucket_guard[guard_index] = False
                                if target_index == 0:
                                    (
                                        current_pvp_player_hp,
                                        current_pvp_player_virtual_hp,
                                        target_hp_delta,
                                        target_virtual_hp_delta,
                                    ) = _pvp_apply_hp_damage(
                                        current_pvp_player_hp,
                                        current_pvp_player_virtual_hp,
                                        shot_damage,
                                    )
                                    current_pvp_player_self_shots += 1
                                else:
                                    (
                                        current_pvp_bot_hp,
                                        current_pvp_bot_virtual_hp,
                                        target_hp_delta,
                                        target_virtual_hp_delta,
                                    ) = _pvp_apply_hp_damage(
                                        current_pvp_bot_hp,
                                        current_pvp_bot_virtual_hp,
                                        shot_damage,
                                    )
                            else:
                                shot_damage = 0
                                target_hp_delta = 0
                                target_virtual_hp_delta = 0
                            if target_index == 0:
                                source_virtual_hp_delta = 0
                            else:
                                (
                                    current_pvp_player_virtual_hp,
                                    source_virtual_hp_delta,
                                ) = _pvp_frenzy_after_shot(
                                    current_pvp_player_virtual_hp,
                                    _pvp_virtual_hp_cap(current_pvp_player),
                                    player_ammo_cfg,
                                    max(
                                        0,
                                        -target_hp_delta - target_virtual_hp_delta,
                                    ),
                                    0,
                                    target_index,
                                )
                            target_hp_after = (
                                current_pvp_player_hp if target_index == 0
                                else current_pvp_bot_hp
                            )
                            target_virtual_hp_after = (
                                current_pvp_player_virtual_hp if target_index == 0
                                else current_pvp_bot_virtual_hp
                            )
                            current_pvp_player, added_real = pvp_ghosts_after_shot(
                                current_pvp_player, player_ammo_cfg)
                            current_pvp_player_ammo += added_real
                            player_ghosts_added.append(added_real)
                            player_shots.append((
                                player_ammo_cfg,
                                target_hp_delta,
                                current_pvp_player_ammo,
                                current_pvp_player_fake_ammo,
                                _pvp_is_eliminated(
                                    target_hp_after, target_virtual_hp_after
                                ),
                            ))
                            player_virtual_hp_deltas.append(target_virtual_hp_delta)
                            player_source_virtual_hp_deltas.append(
                                source_virtual_hp_delta
                            )
                            player_source_dead_after_shots.append(
                                _pvp_is_eliminated(
                                    current_pvp_player_hp,
                                    current_pvp_player_virtual_hp,
                                )
                            )
                            if _pvp_is_eliminated(
                                target_hp_after, target_virtual_hp_after
                            ) or player_source_dead_after_shots[-1]:
                                break
                        maintenance_expired = _maintenance_kit_expires_after_shot(
                            maintenance_active_for_shot,
                            0,
                            target_index,
                            player_shots,
                        )
                        if maintenance_expired:
                            current_pvp_maintenance_bonus[0] = 0
                        if not player_shots:
                            LOG.warning("PVP local shot had no drawable round")
                            continue
                        current_pvp_player, weapon_reward = _pvp_carnivore_reward(
                            current_pvp_player,0,target_index,player_shots,player_virtual_hp_deltas)
                        player_ammo_cfg = player_shots[0][0]
                        self_blank_continues = (
                            target_index == 0
                            and all(shot[0] == 300 for shot in player_shots)
                            and not _pvp_is_eliminated(
                                current_pvp_player_hp, current_pvp_player_virtual_hp
                            )
                        )
                        # The no-shop lab duel has no match-currency award,
                        # but it still needs the continuous-shot UI state.
                        if self_blank_continues:
                            current_pvp_self_blank_streak += 1
                        else:
                            current_pvp_self_blank_streak = 0
                            current_pvp_self_shoot_pool = 0

                        player_died = _pvp_is_eliminated(
                            current_pvp_player_hp, current_pvp_player_virtual_hp
                        )
                        bot_died = _pvp_is_eliminated(
                            current_pvp_bot_hp, current_pvp_bot_virtual_hp
                        )
                        match_ended = player_died or bot_died
                        player_reload_ammo = None
                        if (
                            not match_ended
                            and current_pvp_player_ammo + current_pvp_damage_bonus[0] <= 0
                        ):
                            player_gun = parse_bytes_field(current_pvp_player, 7) or b""
                            current_pvp_player_ammo, current_pvp_player_fake_ammo = (
                                _reload_weapon_ammo(
                                    parse_varint_field(player_gun, 1) or 0,
                                    current_pvp_damage_bonus, 0,
                                    randomize=state.randomize_magazines,
                                )
                            )
                            player_reload_ammo = (
                                current_pvp_player_ammo,
                                current_pvp_player_fake_ammo,
                            )
                            LOG.info(
                                "PVP duel player reload after last real shot real=%d fake=%d",
                                *player_reload_ammo,
                            )
                        current_pvp_event_id += 1
                        if not self_blank_continues:
                            current_pvp_turn_number += 1
                        event_time = server_time
                        current_pvp_turn = -1 if match_ended else (
                            0 if self_blank_continues else 1
                        )
                        current_pvp_player = pvp_gamer_with_state(
                            current_pvp_player,
                            weapon_reloaded=player_reload_ammo is not None,
                            hp=current_pvp_player_hp,
                            ammo_number=current_pvp_player_ammo,
                            fake_ammo_number=current_pvp_player_fake_ammo,
                            enhanced_ammo_number=(
                                current_pvp_damage_bonus[0]
                            ),
                            round_number=current_pvp_round,
                            is_dead=player_died,
                            burst_mode_active=bool(current_pvp_burst_mode[0]),
                            maintenance_kit_active=bool(
                                current_pvp_maintenance_bonus[0]
                            ),
                            virtual_hp=current_pvp_player_virtual_hp,
                            continue_shoot=(
                                current_pvp_self_blank_streak,
                                current_pvp_self_shoot_pool,
                                1 if self_blank_continues else 0,
                                int(self_blank_continues), 0,
                            ),
                        )
                        current_pvp_bot = pvp_gamer_with_state(
                            current_pvp_bot,
                            hp=current_pvp_bot_hp,
                            ammo_number=current_pvp_bot_ammo,
                            fake_ammo_number=current_pvp_bot_fake_ammo,
                            enhanced_ammo_number=(
                                current_pvp_damage_bonus[1]
                            ),
                            round_number=current_pvp_round,
                            is_dead=bot_died,
                            virtual_hp=current_pvp_bot_virtual_hp,
                            burst_mode_active=bool(current_pvp_burst_mode[1]),
                            maintenance_kit_active=bool(
                                current_pvp_maintenance_bonus[1]
                            ),
                        )
                        info_after_player = pvp_info_with_state(
                            current_pvp_info,
                            current_pvp_player,
                            current_pvp_bot,
                            round_number=current_pvp_round,
                            turn_number=current_pvp_turn_number,
                            current_index=(
                                0 if match_ended or self_blank_continues else 1
                            ),
                        )
                        event_target = (
                            current_pvp_player
                            if target_index == 0
                            else current_pvp_bot
                        )
                        source_event_status = 0
                        target_event_status = 0
                        if player_died:
                            source_event_status = 1  # shooter died shooting self
                            target_event_status = 5  # killed by self
                        elif bot_died:
                            source_event_status = 2  # shooter killed another
                            target_event_status = 4  # killed by another
                        first_shot_cfg, first_shot_delta, first_real_after, first_fake_after, first_dead = player_shots[0]
                        player_event = pvp_shoot_event_result_body(
                            current_pvp_player,
                            event_target,
                            0,
                            target_index,
                            ammo_cfg_id=first_shot_cfg,
                            target_hp_delta=first_shot_delta,
                            target_virtual_hp_delta=player_virtual_hp_deltas[0],
                            additional_virtual_hp_deltas=tuple(
                                player_virtual_hp_deltas[1:]
                            ),
                            source_virtual_hp_delta=(
                                player_source_virtual_hp_deltas[0]
                            ),
                            additional_source_virtual_hp_deltas=tuple(
                                player_source_virtual_hp_deltas[1:]
                            ),
                            source_dead_after_shots=tuple(
                                player_source_dead_after_shots
                            ),
                            source_ammo_after=first_real_after,
                            source_fake_ammo_after=first_fake_after,
                            target_dead=first_dead,
                            is_end_pvp=match_ended,
                            shoot_self_num=current_pvp_player_self_shots,
                            event_id=current_pvp_event_id,
                            is_next_round=not match_ended,
                            event_time=event_time,
                            source_event_status=source_event_status,
                            target_event_status=target_event_status,
                            additional_shots=tuple(player_shots[1:]),
                            ghosts_added_real_after_shots=tuple(player_ghosts_added),
                            weapon_extra_shot_active=shot_count > (2 if burst_active else 1),
                            source_coin_delta=weapon_reward, coin_reason=8,
                            del_buff_cfg=(
                                BURST_MODE_BUFF_CFG_ID if burst_pending else None
                            ),
                            del_buff_cfgs=(
                                (MAINTENANCE_KIT_BUFF_CFG_ID,)
                                if maintenance_expired else ()
                            ),
                            reload_ammo_after=player_reload_ammo,
                            continue_shoot=(
                                1 if self_blank_continues else 0,
                                current_pvp_self_shoot_pool,
                                int(self_blank_continues), 0,
                            ),
                        )
                        post_frames.append(
                            encode_frame(
                                255,
                                2,
                                pvp_event_notification_body(
                                    player_event,
                                    info_after_player,
                                    server_time=event_time,
                                ),
                                error=0,
                                index=0,
                                length_mode=length_mode,
                            )
                        )
                        if match_ended:
                            # Do not schedule a bot turn after either target
                            # dies. The end packet follows the shot animation.
                            current_pvp_player = pvp_gamer_with_state(
                                current_pvp_player,
                                hp=current_pvp_player_hp,
                                ammo_number=current_pvp_player_ammo,
                                fake_ammo_number=current_pvp_player_fake_ammo,
                                enhanced_ammo_number=current_pvp_damage_bonus[0],
                                round_number=current_pvp_round,
                                is_dead=player_died,
                                rank=2 if player_died else 1,
                            )
                            current_pvp_bot = pvp_gamer_with_state(
                                current_pvp_bot,
                                hp=current_pvp_bot_hp,
                                ammo_number=current_pvp_bot_ammo,
                                fake_ammo_number=current_pvp_bot_fake_ammo,
                                enhanced_ammo_number=current_pvp_damage_bonus[1],
                                round_number=current_pvp_round,
                                is_dead=bot_died,
                                rank=2 if bot_died else 1,
                            )
                            current_pvp_info = pvp_info_with_end(
                                pvp_info_with_state(
                                    info_after_player,
                                    current_pvp_player,
                                    current_pvp_bot,
                                    round_number=current_pvp_round,
                                    turn_number=current_pvp_turn_number,
                                    current_index=0,
                                    status=4,
                                ),
                                end_time=event_time,
                            )
                            delayed_frames.append(
                                (
                                    2.5,
                                    encode_frame(
                                        255,
                                        5,
                                        pvp_end_body(current_pvp_info),
                                        error=0,
                                        index=0,
                                        length_mode=length_mode,
                                    ),
                                )
                            )
                            current_pvp_turn = -1
                            LOG.info(
                                "PVP match ended on local shot: target=%d winner=%s",
                                target_index,
                                "bot" if player_died else "local player",
                            )
                        elif self_blank_continues:
                            settle = PLAYER_CONTINUE_SHOT_SETTLE
                            if current_pvp_player_ammo + current_pvp_player_fake_ammo + current_pvp_damage_bonus[0] <= 0:
                                reload_info = recover_empty_player_magazine(
                                    increment_turn=False
                                )
                                delayed_frames.append((
                                    settle,
                                    encode_frame(
                                        255, 1, reload_info,
                                        error=0, index=0,
                                        length_mode=length_mode,
                                    ),
                                ))
                            else:
                                # A blank self-shot leaves this same player active.
                                # Do not send Pvp_Prepare/PvpIng here: the bundled
                                # client treats either as a new operator transition,
                                # resets aim to Default, and returns to Fire instead
                                # of preserving the Shoot/Cancel continuation UI.
                                current_pvp_info = pvp_info_with_state(
                                    info_after_player,
                                    current_pvp_player,
                                    current_pvp_bot,
                                    round_number=current_pvp_round,
                                    turn_number=current_pvp_turn_number,
                                    current_index=0,
                                    status=2,
                                )
                            current_pvp_turn = 0
                            current_pvp_ready_at = time.monotonic() + settle
                            LOG.info(
                                "PVP blank self-shot continues same operator without round reset; ammo=%d/%d",
                                current_pvp_player_ammo,
                                current_pvp_player_fake_ammo,
                            )
                        else:
                            # The bundled client has a two-phase transition.
                            # Pvp_Prepare is queued while Finally_Source is
                            # pending, then PvpIng activates the next operator
                            # after OnShootOver has completed.
                            player_animation_delay = (
                                PLAYER_SELF_SHOT_SETTLE
                                if target_index == 0
                                else PLAYER_OTHER_SHOT_SETTLE
                            )
                            bot_prepare_time = event_time + 1
                            bot_active_time = event_time + 2
                            if current_pvp_bot_ammo + current_pvp_damage_bonus[1] <= 0:
                                bot_gun = parse_bytes_field(current_pvp_bot, 7) or b""
                                (current_pvp_bot_ammo,
                                 current_pvp_bot_fake_ammo) = _reload_weapon_ammo(
                                    parse_varint_field(bot_gun, 1) or 0,
                                    current_pvp_damage_bonus, 1,
                                    randomize=state.randomize_magazines,
                                )
                                current_pvp_bot = pvp_gamer_with_state(
                                    current_pvp_bot,
                                    weapon_reloaded=True,
                                    hp=current_pvp_bot_hp,
                                    ammo_number=current_pvp_bot_ammo,
                                    fake_ammo_number=current_pvp_bot_fake_ammo,
                                    enhanced_ammo_number=current_pvp_damage_bonus[1],
                                    round_number=current_pvp_round,
                                )
                                LOG.info(
                                    "PVP auto-reload bot before its turn real=%d fake=%d",
                                    current_pvp_bot_ammo,
                                    current_pvp_bot_fake_ammo,
                                )
                            current_pvp_bot = pvp_gamer_with_skill_cd(
                                current_pvp_bot,
                                max(0, pvp_gamer_skill_cd(current_pvp_bot) - 1),
                            )
                            info_prepare_bot = pvp_info_with_state(
                                info_after_player,
                                current_pvp_player,
                                current_pvp_bot,
                                round_number=current_pvp_round,
                                turn_number=current_pvp_turn_number,
                                current_index=1,
                                status=3,
                            )
                            info_active_bot = pvp_info_with_state(
                                info_prepare_bot,
                                current_pvp_player,
                                current_pvp_bot,
                                round_number=current_pvp_round,
                                turn_number=current_pvp_turn_number,
                                current_index=1,
                                status=2,
                            )
                            delayed_frames.extend(
                                [
                                    (
                                        PREPARE_SIGNAL_DELAY,
                                        encode_frame(
                                            255,
                                            1,
                                            pvp_next_round_body(
                                                current_pvp_bot,
                                                info_prepare_bot,
                                                round_number=current_pvp_round,
                                                server_time=bot_prepare_time,
                                            ),
                                            error=0,
                                            index=0,
                                            length_mode=length_mode,
                                        ),
                                    ),
                                    (
                                        player_animation_delay
                                        - PREPARE_SIGNAL_DELAY,
                                        encode_frame(
                                            255,
                                            1,
                                            pvp_next_round_body(
                                                current_pvp_bot,
                                                info_active_bot,
                                                round_number=current_pvp_round,
                                                server_time=bot_active_time,
                                            ),
                                            error=0,
                                            index=0,
                                            length_mode=length_mode,
                                        ),
                                    ),
                                ]
                            )

                            # The bot targets the local player and draws from
                            # its own gun-specific magazine. Burst is
                            # represented by two real shot subevents.
                            burst_pending, burst_active = _pvp_burst_shot_state(
                                current_pvp_burst_mode[1], 1, 0
                            )
                            if burst_pending:
                                current_pvp_burst_mode[1] = 0
                                LOG.info(
                                    "PVP Burst Mode consumed shooter=1 target=0 double_shot=%s",
                                    burst_active,
                                )
                            maintenance_active_for_shot = bool(
                                current_pvp_maintenance_bonus[1]
                            )
                            bot_shots: list[tuple[int, int, int, int, bool]] = []
                            bot_virtual_hp_deltas: list[int] = []
                            bot_source_virtual_hp_deltas: list[int] = []
                            bot_ghosts_added: list[int] = []
                            bot_source_dead_after_shots: list[bool] = []
                            shot_damage = 0
                            shot_count = normal_shot_count(
                                parse_varint_field(parse_bytes_field(current_pvp_bot, 7) or b'', 1) or 0,
                                current_pvp_bot_ammo,current_pvp_bot_fake_ammo,
                                current_pvp_damage_bonus[1],1,0,burst_active)
                            for shot_number in range(shot_count):
                                bot_ammo_cfg = _draw_loaded_ammo(
                                    current_pvp_bot_ammo, current_pvp_bot_fake_ammo, current_pvp_damage_bonus[1],
                                    gun_id=parse_varint_field(parse_bytes_field(current_pvp_bot, 7) or b'', 1) or 0,
                                )
                                if bot_ammo_cfg is None:
                                    break
                                bot_hit = bot_ammo_cfg in (1, 2)
                                if bot_ammo_cfg == 1:
                                    current_pvp_bot_ammo -= 1
                                elif bot_ammo_cfg == 300:
                                    current_pvp_bot_fake_ammo -= 1
                                if bot_hit:
                                    shot_damage = _pvp_shot_damage(
                                        bot_ammo_cfg,
                                        enhanced_ammo_bonus=current_pvp_damage_bonus[1],
                                        maintenance_kit_active=maintenance_active_for_shot,
                                        shooter_index=1,
                                        target_index=0,
                                    )
                                    if bot_ammo_cfg == 2:
                                        current_pvp_damage_bonus[1] -= 1
                                    if current_pvp_bucket_guard[0]:
                                        shot_damage = 0
                                        current_pvp_bucket_guard[0] = False
                                    (
                                        current_pvp_player_hp,
                                        current_pvp_player_virtual_hp,
                                        target_hp_delta,
                                        target_virtual_hp_delta,
                                    ) = _pvp_apply_hp_damage(
                                        current_pvp_player_hp,
                                        current_pvp_player_virtual_hp,
                                        shot_damage,
                                    )
                                else:
                                    shot_damage = 0
                                    target_hp_delta = 0
                                    target_virtual_hp_delta = 0
                                (
                                    current_pvp_bot_virtual_hp,
                                    source_virtual_hp_delta,
                                ) = _pvp_frenzy_after_shot(
                                    current_pvp_bot_virtual_hp,
                                    _pvp_virtual_hp_cap(current_pvp_bot),
                                    bot_ammo_cfg,
                                    max(
                                        0,
                                        -target_hp_delta - target_virtual_hp_delta,
                                    ),
                                    1,
                                    0,
                                )
                                current_pvp_bot, added_real = pvp_ghosts_after_shot(
                                    current_pvp_bot, bot_ammo_cfg)
                                current_pvp_bot_ammo += added_real
                                bot_ghosts_added.append(added_real)
                                bot_shots.append((
                                    bot_ammo_cfg,
                                    target_hp_delta,
                                    current_pvp_bot_ammo,
                                    current_pvp_bot_fake_ammo,
                                    _pvp_is_eliminated(
                                        current_pvp_player_hp,
                                        current_pvp_player_virtual_hp,
                                    ),
                                ))
                                bot_virtual_hp_deltas.append(target_virtual_hp_delta)
                                bot_source_virtual_hp_deltas.append(
                                    source_virtual_hp_delta
                                )
                                bot_source_dead_after_shots.append(
                                    _pvp_is_eliminated(
                                        current_pvp_bot_hp,
                                        current_pvp_bot_virtual_hp,
                                    )
                                )
                                if _pvp_is_eliminated(
                                    current_pvp_player_hp,
                                    current_pvp_player_virtual_hp,
                                ) or bot_source_dead_after_shots[-1]:
                                    break
                            maintenance_expired = _maintenance_kit_expires_after_shot(
                                maintenance_active_for_shot,
                                1,
                                0,
                                bot_shots,
                            )
                            if maintenance_expired:
                                current_pvp_maintenance_bonus[1] = 0
                            current_pvp_bot, weapon_reward = _pvp_carnivore_reward(
                                current_pvp_bot,1,0,bot_shots,bot_virtual_hp_deltas)
                            if not bot_shots:
                                LOG.warning("PVP bot had no drawable round")
                                continue
                            bot_ammo_cfg = bot_shots[0][0]
                            player_died = _pvp_is_eliminated(
                                current_pvp_player_hp, current_pvp_player_virtual_hp
                            )
                            bot_reload_ammo = None
                            if (
                                not player_died
                                and current_pvp_bot_ammo + current_pvp_damage_bonus[1] <= 0
                            ):
                                bot_gun = parse_bytes_field(current_pvp_bot, 7) or b""
                                current_pvp_bot_ammo, current_pvp_bot_fake_ammo = (
                                    _reload_weapon_ammo(
                                        parse_varint_field(bot_gun, 1) or 0,
                                        current_pvp_damage_bonus, 1,
                                        randomize=state.randomize_magazines,
                                    )
                                )
                                bot_reload_ammo = (
                                    current_pvp_bot_ammo,
                                    current_pvp_bot_fake_ammo,
                                )
                                LOG.info(
                                    "PVP duel bot reload after last real shot real=%d fake=%d",
                                    *bot_reload_ammo,
                                )
                            current_pvp_event_id += 1
                            current_pvp_turn_number += 1
                            bot_event_time = event_time + 3
                            current_pvp_bot = pvp_gamer_with_state(
                                current_pvp_bot,
                                weapon_reloaded=bot_reload_ammo is not None,
                                hp=current_pvp_bot_hp,
                                ammo_number=current_pvp_bot_ammo,
                                fake_ammo_number=current_pvp_bot_fake_ammo,
                                enhanced_ammo_number=(
                                    current_pvp_damage_bonus[1]
                                ),
                                round_number=current_pvp_round,
                                burst_mode_active=bool(current_pvp_burst_mode[1]),
                                maintenance_kit_active=bool(
                                    current_pvp_maintenance_bonus[1]
                                ),
                                is_dead=_pvp_is_eliminated(
                                    current_pvp_bot_hp, current_pvp_bot_virtual_hp
                                ),
                                virtual_hp=current_pvp_bot_virtual_hp,
                            )
                            current_pvp_player = pvp_gamer_with_state(
                                current_pvp_player,
                                hp=current_pvp_player_hp,
                                ammo_number=current_pvp_player_ammo,
                                fake_ammo_number=current_pvp_player_fake_ammo,
                                enhanced_ammo_number=(
                                    current_pvp_damage_bonus[0]
                                ),
                                round_number=current_pvp_round,
                                is_dead=player_died,
                                burst_mode_active=bool(current_pvp_burst_mode[0]),
                                maintenance_kit_active=bool(
                                    current_pvp_maintenance_bonus[0]
                                ),
                                virtual_hp=current_pvp_player_virtual_hp,
                            )
                            info_after_bot = pvp_info_with_state(
                                info_active_bot,
                                current_pvp_player,
                                current_pvp_bot,
                                round_number=current_pvp_round,
                                turn_number=current_pvp_turn_number,
                                current_index=0,
                            )
                            first_bot_cfg, first_bot_delta, first_bot_real_after, first_bot_fake_after, first_bot_dead = bot_shots[0]
                            bot_event = pvp_shoot_event_result_body(
                                current_pvp_bot,
                                current_pvp_player,
                                1,
                                0,
                                ammo_cfg_id=first_bot_cfg,
                                target_hp_delta=first_bot_delta,
                                target_virtual_hp_delta=bot_virtual_hp_deltas[0],
                                additional_virtual_hp_deltas=tuple(
                                    bot_virtual_hp_deltas[1:]
                                ),
                                source_virtual_hp_delta=(
                                    bot_source_virtual_hp_deltas[0]
                                ),
                                additional_source_virtual_hp_deltas=tuple(
                                    bot_source_virtual_hp_deltas[1:]
                                ),
                                source_dead_after_shots=tuple(
                                    bot_source_dead_after_shots
                                ),
                                source_ammo_after=first_bot_real_after,
                                source_fake_ammo_after=first_bot_fake_after,
                                target_dead=first_bot_dead,
                                is_end_pvp=player_died,
                                shoot_self_num=current_pvp_bot_self_shots,
                                event_id=current_pvp_event_id,
                                is_next_round=not player_died,
                                event_time=bot_event_time,
                                source_event_status=2 if player_died else 0,
                                target_event_status=4 if player_died else 0,
                                additional_shots=tuple(bot_shots[1:]),
                                ghosts_added_real_after_shots=tuple(bot_ghosts_added),
                                weapon_extra_shot_active=shot_count > (2 if burst_active else 1),
                                source_coin_delta=weapon_reward, coin_reason=8,
                                reload_ammo_after=bot_reload_ammo,
                                del_buff_cfg=(
                                    BURST_MODE_BUFF_CFG_ID if burst_pending else None
                                ),
                                del_buff_cfgs=(
                                    (MAINTENANCE_KIT_BUFF_CFG_ID,)
                                    if maintenance_expired else ()
                                ),
                            )
                            # The client does not infer these poses from the
                            # shot result. It expects explicit bot behavior
                            # notifications: raise gun, then choose target.
                            delayed_frames.extend(
                                [
                                    (
                                        0.5,
                                        encode_frame(
                                            255,
                                            4,
                                            pvp_behavior_notification_body(1, 1, 0),
                                            error=0,
                                            index=0,
                                            length_mode=length_mode,
                                        ),
                                    ),
                                    (
                                        0.8,
                                        encode_frame(
                                            255,
                                            4,
                                            pvp_behavior_notification_body(1, 4, 0),
                                            error=0,
                                            index=0,
                                            length_mode=length_mode,
                                        ),
                                    ),
                                    (
                                        BOT_THINK_DELAY - 1.3,
                                        encode_frame(
                                            255,
                                            2,
                                            pvp_event_notification_body(
                                                bot_event,
                                                info_after_bot,
                                                server_time=bot_event_time,
                                            ),
                                            error=0,
                                            index=0,
                                            length_mode=length_mode,
                                        ),
                                    ),
                                ]
                            )
                            if player_died:
                                current_pvp_player = pvp_gamer_with_state(
                                    current_pvp_player,
                                    hp=current_pvp_player_hp,
                                    ammo_number=current_pvp_player_ammo,
                                    fake_ammo_number=current_pvp_player_fake_ammo,
                                    enhanced_ammo_number=current_pvp_damage_bonus[0],
                                    round_number=current_pvp_round,
                                    is_dead=True,
                                    rank=2,
                                )
                                current_pvp_bot = pvp_gamer_with_state(
                                    current_pvp_bot,
                                    hp=current_pvp_bot_hp,
                                    ammo_number=current_pvp_bot_ammo,
                                    fake_ammo_number=current_pvp_bot_fake_ammo,
                                    enhanced_ammo_number=current_pvp_damage_bonus[1],
                                    round_number=current_pvp_round,
                                    is_dead=False,
                                    rank=1,
                                )
                                current_pvp_info = pvp_info_with_end(
                                    pvp_info_with_state(
                                        info_after_bot,
                                        current_pvp_player,
                                        current_pvp_bot,
                                        round_number=current_pvp_round,
                                        turn_number=current_pvp_turn_number,
                                        current_index=0,
                                        status=4,
                                    ),
                                    end_time=bot_event_time,
                                )
                                delayed_frames.extend(
                                    [
                                        (
                                            0.2,
                                            encode_frame(
                                                255,
                                                15,
                                                pvp_gamer_dead_body(current_pvp_info),
                                                error=0,
                                                index=0,
                                                length_mode=length_mode,
                                            ),
                                        ),
                                        (
                                            0.2,
                                            encode_frame(
                                                255,
                                                5,
                                                pvp_end_body(current_pvp_info),
                                                error=0,
                                                index=0,
                                                length_mode=length_mode,
                                            ),
                                        ),
                                    ]
                                )
                                current_pvp_turn = -1
                                LOG.info(
                                    "PVP match ended: local player lost; HP reached zero"
                                )
                            else:
                                current_pvp_round += 1
                                if current_pvp_player_ammo + current_pvp_damage_bonus[0] <= 0:
                                    player_gun = parse_bytes_field(current_pvp_player, 7) or b""
                                    (current_pvp_player_ammo,
                                     current_pvp_player_fake_ammo) = _reload_weapon_ammo(
                                        parse_varint_field(player_gun, 1) or 0,
                                        current_pvp_damage_bonus, 0,
                                        randomize=state.randomize_magazines,
                                    )
                                    current_pvp_player = pvp_gamer_after_weapon_reload(current_pvp_player)
                                    LOG.info(
                                        "PVP auto-reload player before next turn real=%d fake=%d",
                                        current_pvp_player_ammo,
                                        current_pvp_player_fake_ammo,
                                    )
                                current_pvp_player = pvp_gamer_with_state(
                                    current_pvp_player,
                                    hp=current_pvp_player_hp,
                                    ammo_number=current_pvp_player_ammo,
                                    fake_ammo_number=current_pvp_player_fake_ammo,
                                    enhanced_ammo_number=current_pvp_damage_bonus[0],
                                    round_number=current_pvp_round,
                                )
                                current_pvp_bot = pvp_gamer_with_state(
                                    current_pvp_bot,
                                    hp=current_pvp_bot_hp,
                                    ammo_number=current_pvp_bot_ammo,
                                    fake_ammo_number=current_pvp_bot_fake_ammo,
                                    enhanced_ammo_number=current_pvp_damage_bonus[1],
                                    round_number=current_pvp_round,
                                )
                                player_prepare_time = bot_event_time + 1
                                player_active_time = bot_event_time + 2
                                carried_slot = (
                                    parse_bytes_field(current_pvp_player, 18) or b""
                                )
                                carried_cfg_id = parse_varint_field(carried_slot, 2) or 0
                                carried_rate = PIGGYBANK_COINS_PER_TURN.get(
                                    carried_cfg_id, 0
                                )
                                piggybank_event = b""
                                if carried_rate > 0:
                                    stored_coins = max(
                                        0, parse_varint_field(carried_slot, 7) or 0
                                    )
                                    carried_slot = pvp_card_slot_with_arg(
                                        carried_slot, stored_coins + carried_rate
                                    )
                                    current_pvp_player = pvp_gamer_with_coin_and_card(
                                        current_pvp_player,
                                        coin=parse_varint_field(current_pvp_player, 5) or 0,
                                        card_slot=carried_slot,
                                    )
                                    current_pvp_event_id += 1
                                    piggybank_event = pvp_piggybank_round_start_event_result_body(
                                        current_pvp_player,
                                        carried_slot,
                                        event_id=current_pvp_event_id,
                                        event_time=player_active_time,
                                    )
                                current_pvp_player = pvp_gamer_with_skill_cd(
                                    current_pvp_player,
                                    max(0, pvp_gamer_skill_cd(current_pvp_player) - 1),
                                )
                                info_prepare_player = pvp_info_with_state(
                                    info_after_bot,
                                    current_pvp_player,
                                    current_pvp_bot,
                                    round_number=current_pvp_round,
                                    turn_number=current_pvp_turn_number,
                                    current_index=0,
                                    status=3,
                                )
                                current_pvp_info = pvp_info_with_state(
                                    info_prepare_player,
                                    current_pvp_player,
                                    current_pvp_bot,
                                    round_number=current_pvp_round,
                                    turn_number=current_pvp_turn_number,
                                    current_index=0,
                                    status=2,
                                )
                                delayed_frames.extend(
                                    [
                                        (
                                            PREPARE_SIGNAL_DELAY,
                                            encode_frame(
                                                255,
                                                1,
                                                pvp_next_round_body(
                                                    current_pvp_player,
                                                    info_prepare_player,
                                                    round_number=current_pvp_round,
                                                    server_time=player_prepare_time,
                                                ),
                                                error=0,
                                                index=0,
                                                length_mode=length_mode,
                                            ),
                                        ),
                                        (
                                            BOT_SHOT_SETTLE
                                            - PREPARE_SIGNAL_DELAY,
                                            encode_frame(
                                                255,
                                                1,
                                                pvp_next_round_body(
                                                    current_pvp_player,
                                                    current_pvp_info,
                                                    round_number=current_pvp_round,
                                                    server_time=player_active_time,
                                                ),
                                                error=0,
                                                index=0,
                                                length_mode=length_mode,
                                            ),
                                        ),
                                    ]
                                )
                                if piggybank_event:
                                    delayed_frames.append(
                                        (
                                            0.0,
                                            encode_frame(
                                                255,
                                                2,
                                                pvp_event_notification_body(
                                                    piggybank_event,
                                                    current_pvp_info,
                                                    server_time=player_active_time,
                                                ),
                                                error=0,
                                                index=0,
                                                length_mode=length_mode,
                                            ),
                                        )
                                    )
                                current_pvp_turn = 0
                                current_pvp_ready_at = time.monotonic() + sum(
                                    delay for delay, _ in delayed_frames
                                )
                        LOG.info(
                            "PVP shot target=%d playerHP=%d->%d botHP=%d->%d "
                            "playerAmmo(real/fake)=%d/%d->%d/%d event=%d; "
                            "explicit bot turn queued=%s",
                            target_index,
                            old_player_hp,
                            current_pvp_player_hp,
                            old_bot_hp,
                            current_pvp_bot_hp,
                            old_player_ammo,
                            old_player_fake_ammo,
                            current_pvp_player_ammo,
                            current_pvp_player_fake_ammo,
                            current_pvp_event_id,
                            not match_ended,
                        )
                    else:
                        LOG.warning(
                            "PVP shoot ignored: invalid target=%r, room not ready, "
                            "turn pending, or match ended",
                            target_index,
                        )
                        out_body = b"\x08" + _varint(account.gid)
                elif (head.cmd, head.act) == (3, 6):
                    # GamerPvpGamerUseHeroSkillC2S.  The bundled client sends
                    # repeated target indices in field 1; Hero.SkillCd is the
                    # authoritative remaining-turn counter.
                    requested_target = parse_varint_field(body, 1)
                    gamers = [current_pvp_player, current_pvp_bot]
                    hit_points = [current_pvp_player_hp, current_pvp_bot_hp]
                    virtual_hit_points = [
                        current_pvp_player_virtual_hp, current_pvp_bot_virtual_hp
                    ]
                    if current_pvp_extra_bot:
                        gamers.append(current_pvp_extra_bot)
                        hit_points.append(current_pvp_extra_bot_hp)
                        virtual_hit_points.append(current_pvp_extra_bot_virtual_hp)
                    skill_id = pvp_gamer_skill_id(current_pvp_player)
                    exchange_effect = parse_varint_field(body, 3)
                    exchange_trade = shelby_trade(hit_points[0], virtual_hit_points[0],
                        parse_varint_field(current_pvp_player, 5) or 0,
                        exchange_effect, skill_id) if skill_id in SHELBY_SKILLS else None
                    if (
                        current_pvp_info
                        and current_pvp_turn == 0
                        and time.monotonic() >= current_pvp_ready_at
                        and pvp_gamer_skill_cd(current_pvp_player) == 0
                        and not has_buff(current_pvp_player, ITEM_BUFF_CFG[2030])
                        and not _pvp_is_eliminated(hit_points[0], virtual_hit_points[0])
                        and skill_id in (10000, 10003, 10001, 10004, 10002, 10013, 10005, 10014, 10017, 10018, *SHELBY_SKILLS, *KATIE_SKILLS, *DIANA_SKILLS, *VERA_SKILLS, *HAWKE_SKILLS)
                        and (skill_id not in HAWKE_SKILLS or (requested_mode == 1 and requested_sub_mode == 6
                            and hawke_load_count(current_pvp_player_ammo, current_pvp_damage_bonus[0],
                                upgraded=skill_id == 10039) > 0
                            and any(hit_points[i] + virtual_hit_points[i] > 0 for i in range(1, len(gamers)))))
                        and (skill_id not in DIANA_SKILLS or (requested_target == 0
                            and requested_mode == 1 and requested_sub_mode == 6
                            and not any(has_buff(gamers[0], buff) for buff in DIANA_BUFFS)))
                        and (skill_id not in KATIE_SKILLS or (requested_target == 0 and 0 not in current_pvp_katie_guards and requested_mode == 1 and requested_sub_mode == 6))
                        and (skill_id not in SHELBY_SKILLS or (requested_target == 0 and exchange_trade is not None))
                        and requested_target is not None
                        and 0 <= requested_target < len(gamers)
                        and (skill_id not in VERA_SKILLS or (
                            requested_mode == 1 and requested_sub_mode == 6 and requested_target != 0
                            and pvp_gamer_has_ammo_space(gamers[0], current_pvp_player_ammo,
                                current_pvp_player_fake_ammo, current_pvp_damage_bonus[0])
                            and [current_pvp_player_ammo, current_pvp_bot_ammo,
                                 current_pvp_extra_bot_ammo][requested_target]
                                + current_pvp_damage_bonus[requested_target] > 0))
                        and (skill_id not in (10017, 10018) or
                            [current_pvp_player_fake_ammo, current_pvp_bot_fake_ammo, current_pvp_extra_bot_fake_ammo][requested_target] > 0)
                        and not _pvp_is_eliminated(
                            hit_points[requested_target],
                            virtual_hit_points[requested_target],
                        )
                        and (skill_id not in (10001, 10004, 10002, 10013) or requested_target == 0)
                        and (skill_id not in (10005, 10014) or requested_target != 0)
                        and (skill_id not in (10002, 10013) or (
                            requested_mode == 1 and requested_sub_mode == 6
                            and monkey_candidates(parse_bytes_fields(current_pvp_info, 7))))
                    ):
                        target_index = int(requested_target)
                        roll = random.randint(1, 6) if skill_id in (10000, 10003) else None
                        lucky_consumed = False
                        if roll is not None:
                            gamers[0], roll, lucky_consumed = _pvp_roll_lucky_die(gamers[0], roll)
                        hp_delta = 0
                        virtual_hp_delta = 0
                        toxin_used = False
                        monkey_cards = None
                        multi_actor_result = None
                        exchange_coin = 0
                        conversion_cfg = None
                        skill_add_buffs = ()
                        stolen_ammo_cfg = None
                        stolen_target_reload = False
                        if skill_id in HAWKE_SKILLS:
                            real_ammo = [current_pvp_player_ammo, current_pvp_bot_ammo, current_pvp_extra_bot_ammo][:len(gamers)]
                            fake_ammo = [current_pvp_player_fake_ammo, current_pvp_bot_fake_ammo, current_pvp_extra_bot_fake_ammo][:len(gamers)]
                            multi_actor_result = resolve_drone(gamers, hit_points, virtual_hit_points,
                                real_ammo, fake_ammo, current_pvp_damage_bonus, actor=0,
                                upgraded=skill_id == 10039, rng=random, damage=_pvp_apply_hp_damage,
                                round_number=current_pvp_round, event_id=current_pvp_event_id + 1,
                                event_time=server_time, randomize_magazines=state.randomize_magazines,
                                katie_guards=current_pvp_katie_guards)
                            current_pvp_player_ammo, current_pvp_bot_ammo, current_pvp_extra_bot_ammo = real_ammo
                            current_pvp_player_fake_ammo, current_pvp_bot_fake_ammo, current_pvp_extra_bot_fake_ammo = fake_ammo
                            current_pvp_ready_at = time.monotonic() + multi_actor_result.wait
                            LOG.info("PVP Hawke skill=%d consumed=%s hits=%s hp=%s frenzy=%s real=%s red=%s wait=%.2f",
                                skill_id, multi_actor_result.consumed, multi_actor_result.hits, hit_points,
                                virtual_hit_points, real_ammo, current_pvp_damage_bonus, multi_actor_result.wait)
                        elif skill_id in VERA_SKILLS:
                            real_ammo = [current_pvp_player_ammo, current_pvp_bot_ammo, current_pvp_extra_bot_ammo]
                            fake_ammo = [current_pvp_player_fake_ammo, current_pvp_bot_fake_ammo, current_pvp_extra_bot_fake_ammo]
                            stolen_ammo_cfg = vera_round(real_ammo[target_index], current_pvp_damage_bonus[target_index],
                                upgraded=skill_id == 10036, randrange=random.randrange)
                            rounds = current_pvp_damage_bonus if stolen_ammo_cfg == 2 else real_ammo
                            rounds[target_index] -= 1
                            rounds[0] += 1
                            if real_ammo[target_index] + current_pvp_damage_bonus[target_index] == 0:
                                gun_id = parse_varint_field(parse_bytes_field(gamers[target_index],7) or b'',1) or 0
                                real_ammo[target_index], fake_ammo[target_index] = _reload_weapon_ammo(
                                    gun_id, current_pvp_damage_bonus, target_index, randomize=state.randomize_magazines)
                                gamers[target_index] = pvp_gamer_after_weapon_reload(gamers[target_index])
                                stolen_target_reload = True
                            current_pvp_player_ammo, current_pvp_bot_ammo, current_pvp_extra_bot_ammo = real_ammo
                            current_pvp_player_fake_ammo, current_pvp_bot_fake_ammo, current_pvp_extra_bot_fake_ammo = fake_ammo
                            gamers[0] = pvp_gamer_with_state(gamers[0], hp=hit_points[0], virtual_hp=virtual_hit_points[0],
                                ammo_number=real_ammo[0], fake_ammo_number=fake_ammo[0],
                                enhanced_ammo_number=current_pvp_damage_bonus[0], round_number=current_pvp_round)
                            current_pvp_ready_at = time.monotonic() + skill_animation_barrier(skill_id) + (5.0 if stolen_target_reload else 0.0)
                            LOG.info("PVP Vera actor=0 target=%d skill=%d stolen_cfg=%d real=%s blank=%s red=%s reload=%s",
                                target_index, skill_id, stolen_ammo_cfg, real_ammo, fake_ammo,
                                current_pvp_damage_bonus, stolen_target_reload)
                        elif skill_id in DIANA_SKILLS:
                            buff = DIANA_BUFFS[DIANA_SKILLS.index(skill_id)]
                            gamers[0] = pvp_gamer_with_buffs(gamers[0], add_cfg_ids=(buff,), source_index=0)
                            skill_add_buffs = tuple(b for b in parse_bytes_fields(gamers[0],8)
                                if parse_varint_field(b,1) == buff)
                            current_pvp_ready_at = time.monotonic() + skill_animation_barrier(skill_id)
                            LOG.info("PVP Diana activated actor=0 skill=%d buff=%d", skill_id, buff)
                        elif skill_id in KATIE_SKILLS:
                            gamers[0] = activate_katie(gamers[0],skill_id,0,current_pvp_katie_guards)
                            skill_add_buffs = tuple(b for b in parse_bytes_fields(gamers[0],8) if parse_varint_field(b,1) in KATIE_BUFFS)
                            current_pvp_ready_at = time.monotonic() + 8.0
                            LOG.info("PVP Katie activated actor=0 skill=%d buff=%d",skill_id,current_pvp_katie_guards[0][0])
                        elif skill_id in (10017, 10018):
                            real_ammo = [current_pvp_player_ammo, current_pvp_bot_ammo, current_pvp_extra_bot_ammo]
                            fake_ammo = [current_pvp_player_fake_ammo, current_pvp_bot_fake_ammo, current_pvp_extra_bot_fake_ammo]
                            real_ammo[target_index], fake_ammo[target_index], current_pvp_damage_bonus[target_index], conversion_cfg = annie_convert(
                                real_ammo[target_index], fake_ammo[target_index], current_pvp_damage_bonus[target_index],
                                upgraded=skill_id == 10018, friendly=target_index == 0)
                            current_pvp_player_ammo, current_pvp_bot_ammo, current_pvp_extra_bot_ammo = real_ammo
                            current_pvp_player_fake_ammo, current_pvp_bot_fake_ammo, current_pvp_extra_bot_fake_ammo = fake_ammo
                            current_pvp_ready_at = time.monotonic() + 7.0
                            LOG.info("PVP Annie target=%d cfg=%d real=%s blank=%s red=%s", target_index, conversion_cfg, real_ammo, fake_ammo, current_pvp_damage_bonus)
                        elif skill_id in SHELBY_SKILLS:
                            hp_delta, virtual_hp_delta, exchange_coin = exchange_trade
                            if hp_delta > 0:
                                gamers[0], hp_delta, toxin_used = pvp_consume_toxin_heal(gamers[0], hp_delta)
                            hit_points[0] += hp_delta
                            virtual_hit_points[0] += virtual_hp_delta
                            gamers[0] = pvp_gamer_with_coin_and_card(gamers[0],
                                coin=(parse_varint_field(gamers[0], 5) or 0) + exchange_coin)
                            current_pvp_ready_at = time.monotonic() + 7.0
                            LOG.info("PVP Shelby effect=%s hpDelta=%d frenzyDelta=%d coinDelta=%d", exchange_effect, hp_delta, virtual_hp_delta, exchange_coin)
                        elif skill_id in (10005, 10014):
                            real_ammo = [current_pvp_player_ammo, current_pvp_bot_ammo]
                            fake_ammo = [current_pvp_player_fake_ammo, current_pvp_bot_fake_ammo]
                            if current_pvp_extra_bot:
                                real_ammo.append(current_pvp_extra_bot_ammo)
                                fake_ammo.append(current_pvp_extra_bot_fake_ammo)
                            multi_actor_result = resolve_fair_duel(gamers, hit_points, virtual_hit_points,
                                real_ammo, fake_ammo, current_pvp_damage_bonus,
                                actor=0, target=target_index, upgraded=skill_id == 10014,
                                draw=_draw_loaded_ammo, damage=_pvp_apply_hp_damage,
                                round_number=current_pvp_round, event_id=current_pvp_event_id + 1,
                                event_time=server_time, randomize_magazines=state.randomize_magazines,
                                katie_guards=current_pvp_katie_guards)
                            current_pvp_player_ammo, current_pvp_bot_ammo = real_ammo[:2]
                            current_pvp_player_fake_ammo, current_pvp_bot_fake_ammo = fake_ammo[:2]
                            if len(gamers) > 2:
                                current_pvp_extra_bot_ammo = real_ammo[2]
                                current_pvp_extra_bot_fake_ammo = fake_ammo[2]
                            current_pvp_ready_at = time.monotonic() + multi_actor_result.wait
                            LOG.info("PVP Fair Duel skill=%d target=%d shots=%s hp=%s frenzy=%s real=%s blank=%s red=%s wait=%.2f",
                                skill_id, target_index, multi_actor_result.shots, hit_points, virtual_hit_points,
                                real_ammo, fake_ammo, current_pvp_damage_bonus, multi_actor_result.wait)
                        elif skill_id in (10002, 10013):
                            monkey_cards, current_pvp_shop_next_id, converted = monkey_convert_shop(
                                parse_bytes_fields(current_pvp_info, 7),
                                upgraded=skill_id == 10013,
                                next_id=current_pvp_shop_next_id, rng=random,
                            )
                            LOG.info("PVP monkey skill=%d converted=%d freeBoxCfg=2036 ids=%s",
                                     skill_id, converted, [parse_varint_field(c, 1) for c in monkey_cards])
                        elif skill_id in (10001, 10004):
                            hp_delta, spent_frenzy = bear_conversion(
                                hit_points[0], current_pvp_player_virtual_hp,
                                upgraded=skill_id == 10004,
                            )
                            virtual_hp_delta = -spent_frenzy
                            current_pvp_player_virtual_hp -= spent_frenzy
                            virtual_hit_points[0] = current_pvp_player_virtual_hp
                            gamers[0], hp_delta, toxin_used = pvp_consume_toxin_heal(gamers[0],hp_delta)
                            hit_points[0] += hp_delta
                        elif roll is not None and roll >= 3:
                            power = rabbit_power(roll, upgraded=skill_id == 10003)
                            if target_index == 0:
                                hp_delta = min(power, 4 - hit_points[0])
                                gamers[0], hp_delta, toxin_used = pvp_consume_toxin_heal(gamers[0],hp_delta)
                                hit_points[target_index] = max(
                                    0, min(4, hit_points[target_index] + hp_delta)
                                )
                            else:
                                (
                                    hit_points[target_index],
                                    virtual_hit_points[target_index],
                                    hp_delta,
                                    virtual_hp_delta,
                                ) = _pvp_apply_hp_damage(
                                    hit_points[target_index],
                                    virtual_hit_points[target_index],
                                    power,
                                )
                        skill_reset_cd = 2 if skill_id in (*SHELBY_SKILLS, *VERA_SKILLS) else 3
                        if multi_actor_result is None:
                            gamers[0] = pvp_gamer_with_skill_cd(gamers[0], skill_reset_cd)
                        gamers[target_index] = pvp_gamer_with_state(
                            gamers[target_index],
                            hp=hit_points[target_index],
                            enhanced_ammo_number=current_pvp_damage_bonus[target_index],
                            ammo_number=(
                                current_pvp_player_ammo if target_index == 0
                                else current_pvp_bot_ammo if target_index == 1
                                else current_pvp_extra_bot_ammo
                            ),
                            fake_ammo_number=(
                                current_pvp_player_fake_ammo if target_index == 0
                                else current_pvp_bot_fake_ammo if target_index == 1
                                else current_pvp_extra_bot_fake_ammo
                            ),
                            round_number=current_pvp_round,
                            is_dead=_pvp_is_eliminated(
                                hit_points[target_index],
                                virtual_hit_points[target_index],
                            ),
                            virtual_hp=(
                                virtual_hit_points[target_index]
                            ),
                        )
                        current_pvp_player = gamers[0]
                        current_pvp_bot = gamers[1]
                        if len(gamers) > 2:
                            current_pvp_extra_bot = gamers[2]
                            current_pvp_extra_bot_hp = hit_points[2]
                            current_pvp_extra_bot_virtual_hp = virtual_hit_points[2]
                        current_pvp_player_hp, current_pvp_bot_hp = hit_points[:2]
                        (
                            current_pvp_player_virtual_hp,
                            current_pvp_bot_virtual_hp,
                        ) = virtual_hit_points[:2]
                        current_pvp_info = pvp_info_with_state(
                            current_pvp_info, current_pvp_player,
                            current_pvp_bot,
                            round_number=current_pvp_round,
                            turn_number=current_pvp_turn_number,
                            current_index=0,
                            additional_gamers=(current_pvp_extra_bot,)
                            if current_pvp_extra_bot else (),
                        )
                        current_pvp_event_id += 1
                        if monkey_cards is not None:
                            current_pvp_info = pvp_info_with_shop(current_pvp_info, monkey_cards,
                                parse_varint_field(current_pvp_info, 41) or 0)
                        event = pvp_hero_skill_event_result_body(
                            current_pvp_player, gamers[target_index],
                            skill_id=skill_id,
                            target_index=target_index,
                            skill_cd=skill_reset_cd,
                            hp_delta=hp_delta,
                            virtual_hp_delta=virtual_hp_delta,
                            luck_roll=roll,
                            shop_cards=monkey_cards,
                            exchange_effect=exchange_effect if skill_id in SHELBY_SKILLS else None,
                            exchange_coin=exchange_coin,
                            conversion_cfg=conversion_cfg,
                            skill_add_buffs=skill_add_buffs,
                            stolen_ammo_cfg=stolen_ammo_cfg,
                            stolen_target_reload=stolen_target_reload,
                            event_id=current_pvp_event_id,
                            event_time=server_time,
                        )
                        if multi_actor_result is not None:
                            event = multi_actor_result.packet
                        event = pvp_event_with_consumed_lucky(event, 0, consumed=lucky_consumed,
                            event_id=current_pvp_event_id, event_time=server_time)
                        event = pvp_event_with_toxin_removed(event,0,toxin_used,
                            event_id=current_pvp_event_id,event_time=server_time)
                        post_frames.append(encode_frame(
                            255, 2,
                            pvp_event_notification_body(
                                event, current_pvp_info, server_time=server_time,
                            ),
                            error=0, index=0, length_mode=length_mode,
                        ))
                        if multi_actor_result is not None:
                            for index in range(len(gamers)):
                                if _pvp_is_eliminated(hit_points[index], virtual_hit_points[index]) and index not in current_pvp_eliminated_order:
                                    current_pvp_eliminated_order.append(index)
                            survivors = [i for i in range(len(gamers)) if not _pvp_is_eliminated(hit_points[i], virtual_hit_points[i])]
                            if _pvp_is_eliminated(hit_points[0], virtual_hit_points[0]):
                                current_pvp_turn = -1
                                delayed_frames.append((multi_actor_result.wait, encode_frame(255, 15,
                                    pvp_gamer_dead_body(current_pvp_info), length_mode=length_mode)))
                            if len(survivors) <= 1:
                                winner = survivors[0] if survivors else 0
                                for index in range(len(gamers)):
                                    gamers[index] = pvp_gamer_with_state(gamers[index],
                                        hp=hit_points[index], virtual_hp=virtual_hit_points[index],
                                        ammo_number=real_ammo[index], fake_ammo_number=fake_ammo[index],
                                        enhanced_ammo_number=current_pvp_damage_bonus[index],
                                        round_number=current_pvp_round,
                                        is_dead=index not in survivors,
                                        rank=1 if index == winner else len(gamers) - current_pvp_eliminated_order.index(index)
                                        if index in current_pvp_eliminated_order else 2)
                                current_pvp_player, current_pvp_bot = gamers[:2]
                                if len(gamers) > 2:
                                    current_pvp_extra_bot = gamers[2]
                                current_pvp_info = pvp_info_with_end(pvp_info_with_state(
                                    current_pvp_info, gamers[0], gamers[1],
                                    round_number=current_pvp_round, turn_number=current_pvp_turn_number,
                                    current_index=winner, status=4,
                                    additional_gamers=tuple(gamers[2:])), end_time=server_time)
                                delayed_frames.append((multi_actor_result.wait + .2, encode_frame(255, 5,
                                    pvp_end_body(current_pvp_info), length_mode=length_mode)))
                                current_pvp_turn = -1
                        out_body = pb_varint(1, account.gid)
                        LOG.info(
                            "PVP hero skill=%d target=%d roll=%s hpDelta=%d virDelta=%d cd=%d",
                            skill_id, target_index, roll, hp_delta,
                            virtual_hp_delta, skill_reset_cd,
                        )
                    else:
                        response_error = 1
                        LOG.warning(
                            "PVP hero skill rejected skill=%d target=%r cd=%d",
                            skill_id, requested_target,
                            pvp_gamer_skill_cd(current_pvp_player),
                        )
                elif (head.cmd, head.act) == (3, 8):
                    # GamerPvpShootMoneyC2S: the client sends idx=1 when the
                    # player chooses Cancel/Take All on a self-shot streak.
                    out_body = b"\x08" + _varint(account.gid)
                    if (
                        current_pvp_info and current_pvp_player
                        and current_pvp_turn == 0
                        and current_pvp_self_shoot_pool > 0
                    ):
                        payout = current_pvp_self_shoot_pool
                        current_coin = parse_varint_field(
                            current_pvp_player, 5
                        ) or 0
                        current_pvp_player = pvp_gamer_with_coin_and_card(
                            current_pvp_player, coin=current_coin + payout,
                        )
                        current_pvp_player = pvp_gamer_with_state(
                            current_pvp_player,
                            hp=current_pvp_player_hp,
                            ammo_number=current_pvp_player_ammo,
                            fake_ammo_number=current_pvp_player_fake_ammo,
                            enhanced_ammo_number=current_pvp_damage_bonus[0],
                            round_number=current_pvp_round,
                            virtual_hp=current_pvp_player_virtual_hp,
                            continue_shoot=(0, 0, 0, 0, 0),
                        )
                        current_pvp_self_blank_streak = 0
                        current_pvp_self_shoot_pool = 0
                        current_pvp_info = pvp_info_with_state(
                            current_pvp_info,
                            current_pvp_player, current_pvp_bot,
                            round_number=current_pvp_round,
                            turn_number=current_pvp_turn_number,
                            current_index=0,
                            additional_gamers=(
                                (current_pvp_extra_bot,)
                                if current_pvp_extra_bot else ()
                            ),
                        )
                        current_pvp_event_id += 1
                        reward_event = pvp_collect_self_shot_event_result_body(
                            current_pvp_player, payout,
                            event_id=current_pvp_event_id,
                            event_time=server_time,
                        )
                        post_frames.append(encode_frame(
                            255, 2,
                            pvp_event_notification_body(
                                reward_event, current_pvp_info,
                                server_time=server_time,
                            ),
                            error=0, index=0, length_mode=length_mode,
                        ))
                        LOG.info(
                            "PVP self-shot reward collected amount=%d balance=%d",
                            payout, current_coin + payout,
                        )
                elif (head.cmd, head.act) == (3, 4):
                    # Echo behavior packets so client-side aim/selection state
                    # stays in sync while the local server is not authoritative
                    # for matchmaking.
                    out_body = b"\x08" + _varint(account.gid)
                    post_frames.append(
                        encode_frame(
                            255,
                            4,
                            pvp_behavior_notification_body(
                                0,
                                parse_varint_field(body, 1) or 0,
                                parse_varint_field(body, 2) or 0,
                                parse_varint_field(body, 3) or 0,
                                parse_varint_field(body, 4) or 0,
                            ),
                            error=0,
                            index=0,
                            length_mode=length_mode,
                        )
                    )
                elif (head.cmd, head.act) == (3, 5):
                    # The shipped Lua sends Typ_Buy (3) or
                    # Typ_Refresh_Card (4) through this action, then waits for
                    # a PvpEventResult notification to animate and commit UI.
                    card_id = parse_varint_field(body, 1) or 0
                    action_type = parse_varint_field(body, 4) or 0
                    out_body = b"\x08" + _varint(account.gid)
                    if (
                        current_pvp_info
                        and current_pvp_player
                        and current_pvp_turn == 0
                        and time.monotonic() >= current_pvp_ready_at
                    ):
                        current_coin = parse_varint_field(current_pvp_player, 5) or 0
                        shop_cards = parse_bytes_fields(current_pvp_info, 7)
                        slot = parse_bytes_field(current_pvp_player, 18) or b""
                        slot_id = parse_varint_field(slot, 1) or 0
                        event_time = server_time
                        if action_type in (1, 3, 4) and has_buff(current_pvp_player, ITEM_BUFF_CFG[2022]):
                            response_error = 1
                            LOG.info("PVP purchase blocked actor=0 action=%d by Purchase Ban", action_type)
                        elif action_type == 1 and current_pvp_extra_bot:
                            offer = next(
                                (
                                    card for card in shop_cards
                                    if (parse_varint_field(card, 1) or 0) == card_id
                                ),
                                None,
                            )
                            offer_cfg_id = (
                                parse_varint_field(offer, 2) or 0
                                if offer is not None else 0
                            )
                            offer_status = (
                                parse_varint_field(offer, 5) or 0
                                if offer is not None else 0
                            )
                            price = (
                                parse_varint_field(offer, 3) or 0
                                if offer is not None else 0
                            )
                            requested_target = parse_varint_field(body, 2)
                            if offer_cfg_id in (REAL_AMMO_CARD_CFG_ID, FAKE_AMMO_CARD_CFG_ID):
                                if (
                                    offer_status != 1
                                    or price <= 0
                                    or current_coin < price
                                    or requested_target not in (0, 1, 2)
                                ):
                                    response_error = 1
                                    LOG.warning(
                                        "PVP add-ammo buy/use rejected id=%d cfg=%d "
                                        "status=%d price=%d coin=%d target=%r",
                                        card_id, offer_cfg_id, offer_status, price, current_coin,
                                        requested_target,
                                    )
                                else:
                                    target_index = int(requested_target)
                                    gamers = [
                                        current_pvp_player, current_pvp_bot,
                                        current_pvp_extra_bot,
                                    ]
                                    hit_points = [
                                        current_pvp_player_hp, current_pvp_bot_hp,
                                        current_pvp_extra_bot_hp,
                                    ]
                                    real_ammo = [
                                        current_pvp_player_ammo, current_pvp_bot_ammo,
                                        current_pvp_extra_bot_ammo,
                                    ]
                                    fake_ammo = [
                                        current_pvp_player_fake_ammo,
                                        current_pvp_bot_fake_ammo,
                                        current_pvp_extra_bot_fake_ammo,
                                    ]
                                    if _pvp_is_eliminated(
                                        hit_points[target_index],
                                        current_pvp_virtual_hp_at(target_index),
                                    ):
                                        response_error = 1
                                    else:
                                        if not pvp_gamer_has_ammo_space(
                                            gamers[target_index], real_ammo[target_index],
                                            fake_ammo[target_index], current_pvp_damage_bonus[target_index],
                                        ):
                                            response_error = 1
                                            LOG.info("PVP add-ammo rejected: gun full target=%d", target_index)
                                            frame = encode_frame(head.cmd, head.act, b"", index=head.index, error=response_error, length_mode=length_mode)
                                            trace_frame(service, "S->C", frame, length_mode, "response", state_snapshot())
                                            writer.write(frame)
                                            await writer.drain()
                                            continue
                                        if offer_cfg_id == FAKE_AMMO_CARD_CFG_ID:
                                            fake_ammo[target_index] += 1
                                        else:
                                            real_ammo[target_index] += 1
                                        gamers[target_index] = pvp_gamer_with_state(
                                            gamers[target_index],
                                            hp=hit_points[target_index],
                                            ammo_number=real_ammo[target_index],
                                            fake_ammo_number=fake_ammo[target_index],
                                            enhanced_ammo_number=current_pvp_damage_bonus[target_index],
                                            round_number=current_pvp_round,
                                        )
                                        gamers[0] = pvp_gamer_with_coin_and_card(
                                            gamers[0],
                                            coin=current_coin - price,
                                            card_slot=slot if slot_id > 0 else None,
                                        )
                                        (
                                            current_pvp_player, current_pvp_bot,
                                            current_pvp_extra_bot,
                                        ) = gamers
                                        (
                                            current_pvp_player_ammo, current_pvp_bot_ammo,
                                            current_pvp_extra_bot_ammo,
                                        ) = real_ammo
                                        (
                                            current_pvp_player_fake_ammo,
                                            current_pvp_bot_fake_ammo,
                                            current_pvp_extra_bot_fake_ammo,
                                        ) = fake_ammo
                                        updated_shop = tuple(
                                            pvp_shop_card(
                                                parse_varint_field(card, 1) or 0,
                                                parse_varint_field(card, 2) or 0,
                                                parse_varint_field(card, 3) or 0,
                                                parse_varint_field(card, 4) or 1,
                                                2 if (parse_varint_field(card, 1) or 0) == card_id
                                                else (parse_varint_field(card, 5) or 1),
                                            )
                                            for card in shop_cards
                                        )
                                        current_pvp_info = pvp_info_with_shop(
                                            pvp_info_with_state(
                                                current_pvp_info,
                                                current_pvp_player,
                                                current_pvp_bot,
                                                round_number=current_pvp_round,
                                                turn_number=current_pvp_turn_number,
                                                current_index=0,
                                                additional_gamers=(current_pvp_extra_bot,),
                                            ),
                                            updated_shop,
                                            parse_varint_field(current_pvp_info, 41) or 0,
                                        )
                                        current_pvp_event_id += 1
                                        result = pvp_add_ammo_card_event_result_body(
                                            current_pvp_player,
                                            gamers[target_index],
                                            offer,
                                            target_index=target_index,
                                            real_after=real_ammo[target_index],
                                            fake_after=fake_ammo[target_index],
                                            coin_delta=-price,
                                            event_id=current_pvp_event_id,
                                            event_time=event_time,
                                        )
                                        post_frames.append(encode_frame(
                                            255, 2,
                                            pvp_event_notification_body(
                                                result, current_pvp_info,
                                                server_time=event_time,
                                            ),
                                            error=0, index=0,
                                            length_mode=length_mode,
                                        ))
                                        LOG.info(
                                            "PVP ammo bought-and-used offer=%d cfg=%d "
                                            "target=%d real=%d fake=%d coin=%d->%d",
                                            card_id, offer_cfg_id, target_index,
                                            real_ammo[target_index], fake_ammo[target_index],
                                            current_coin, current_coin - price,
                                        )
                            elif offer_cfg_id == SPARE_MAGAZINE_CARD_CFG_ID:
                                if (
                                    offer_status != 1
                                    or price <= 0
                                    or current_coin < price
                                    or requested_target not in (0, 1, 2)
                                ):
                                    response_error = 1
                                    LOG.warning(
                                        "PVP spare-magazine buy/use rejected id=%d "
                                        "status=%d price=%d coin=%d target=%r",
                                        card_id, offer_status, price, current_coin,
                                        requested_target,
                                    )
                                else:
                                    target_index = int(requested_target)
                                    gamers = [
                                        current_pvp_player, current_pvp_bot,
                                        current_pvp_extra_bot,
                                    ]
                                    hit_points = [
                                        current_pvp_player_hp,
                                        current_pvp_bot_hp,
                                        current_pvp_extra_bot_hp,
                                    ]
                                    real_ammo = [
                                        current_pvp_player_ammo,
                                        current_pvp_bot_ammo,
                                        current_pvp_extra_bot_ammo,
                                    ]
                                    fake_ammo = [
                                        current_pvp_player_fake_ammo,
                                        current_pvp_bot_fake_ammo,
                                        current_pvp_extra_bot_fake_ammo,
                                    ]
                                    if _pvp_is_eliminated(
                                        hit_points[target_index],
                                        current_pvp_virtual_hp_at(target_index),
                                    ):
                                        response_error = 1
                                    else:
                                        old_real = real_ammo[target_index]
                                        old_fake = fake_ammo[target_index]
                                        # No authoritative mode-1 ammo bank was
                                        # found. Respect this gun's shipped limits.
                                        target_gun = parse_bytes_field(
                                            gamers[target_index], 7
                                        ) or b""
                                        reload_real, reload_fake = _reload_weapon_ammo(
                                            parse_varint_field(target_gun, 1) or 0,
                                            current_pvp_damage_bonus, target_index,
                                            randomize=state.randomize_magazines,
                                        )
                                        real_ammo[target_index] = reload_real
                                        fake_ammo[target_index] = reload_fake
                                        gamers[target_index] = pvp_gamer_with_state(
                                            gamers[target_index],
                                            hp=hit_points[target_index],
                                            ammo_number=reload_real,
                                            weapon_reloaded=True,
                                            fake_ammo_number=reload_fake,
                                            enhanced_ammo_number=current_pvp_damage_bonus[target_index],
                                            round_number=current_pvp_round,
                                        )
                                        gamers[0] = pvp_gamer_with_coin_and_card(
                                            gamers[0],
                                            coin=current_coin - price,
                                            card_slot=slot if slot_id > 0 else None,
                                        )
                                        (
                                            current_pvp_player, current_pvp_bot,
                                            current_pvp_extra_bot,
                                        ) = gamers
                                        (
                                            current_pvp_player_ammo,
                                            current_pvp_bot_ammo,
                                            current_pvp_extra_bot_ammo,
                                        ) = real_ammo
                                        (
                                            current_pvp_player_fake_ammo,
                                            current_pvp_bot_fake_ammo,
                                            current_pvp_extra_bot_fake_ammo,
                                        ) = fake_ammo
                                        updated_shop = tuple(
                                            pvp_shop_card(
                                                parse_varint_field(card, 1) or 0,
                                                parse_varint_field(card, 2) or 0,
                                                parse_varint_field(card, 3) or 0,
                                                parse_varint_field(card, 4) or 1,
                                                2 if (parse_varint_field(card, 1) or 0) == card_id
                                                else (parse_varint_field(card, 5) or 1),
                                            )
                                            for card in shop_cards
                                        )
                                        current_pvp_info = pvp_info_with_shop(
                                            pvp_info_with_state(
                                                current_pvp_info,
                                                current_pvp_player,
                                                current_pvp_bot,
                                                round_number=current_pvp_round,
                                                turn_number=current_pvp_turn_number,
                                                current_index=0,
                                                additional_gamers=(current_pvp_extra_bot,),
                                            ),
                                            updated_shop,
                                            parse_varint_field(current_pvp_info, 41) or 0,
                                        )
                                        current_pvp_event_id += 1
                                        result = pvp_spare_magazine_event_result_body(
                                            current_pvp_player,
                                            gamers[target_index],
                                            offer,
                                            target_index=target_index,
                                            old_real=old_real,
                                            old_fake=old_fake,
                                            real_after=reload_real,
                                            fake_after=reload_fake,
                                            coin_delta=-price,
                                            event_id=current_pvp_event_id,
                                            event_time=event_time,
                                        )
                                        post_frames.append(encode_frame(
                                            255, 2,
                                            pvp_event_notification_body(
                                                result, current_pvp_info,
                                                server_time=event_time,
                                            ),
                                            error=0, index=0,
                                            length_mode=length_mode,
                                        ))
                                        LOG.info(
                                            "PVP spare magazine bought-and-used offer=%d "
                                            "target=%d old=%d/%d new=%d/%d coin=%d->%d",
                                            card_id, target_index, old_real, old_fake,
                                            real_ammo[target_index], fake_ammo[target_index],
                                            current_coin, current_coin - price,
                                        )
                            elif offer_cfg_id in WET_CIGARETTE_SKILLS:
                                if (
                                    offer_status != 1
                                    or price <= 0
                                    or current_coin < price
                                    or requested_target not in (None, 0)
                                    or _pvp_is_eliminated(
                                        current_pvp_player_hp,
                                        current_pvp_player_virtual_hp,
                                    )
                                ):
                                    response_error = 1
                                else:
                                    current_pvp_player, roll, lucky_consumed = _pvp_roll_lucky_die(current_pvp_player, random.randint(1, 6))
                                    heal = _pvp_wet_cigarette_heal(
                                        current_pvp_player_hp,
                                        current_pvp_player_virtual_hp,
                                        roll,
                                    )
                                    current_pvp_player, heal, toxin_used = pvp_consume_toxin_heal(current_pvp_player,heal)
                                    current_pvp_player_hp += heal
                                    current_pvp_player = pvp_gamer_with_state(
                                        current_pvp_player,
                                        hp=current_pvp_player_hp,
                                        ammo_number=current_pvp_player_ammo,
                                        fake_ammo_number=current_pvp_player_fake_ammo,
                                        enhanced_ammo_number=current_pvp_damage_bonus[0],
                                        round_number=current_pvp_round,
                                    )
                                    current_pvp_player = pvp_gamer_with_coin_and_card(
                                        current_pvp_player,
                                        coin=current_coin - price,
                                        card_slot=slot if slot_id > 0 else None,
                                    )
                                    updated_shop = tuple(
                                        pvp_shop_card(
                                            parse_varint_field(card, 1) or 0,
                                            parse_varint_field(card, 2) or 0,
                                            parse_varint_field(card, 3) or 0,
                                            parse_varint_field(card, 4) or 1,
                                            2 if (parse_varint_field(card, 1) or 0) == card_id
                                            else (parse_varint_field(card, 5) or 1),
                                        )
                                        for card in shop_cards
                                    )
                                    current_pvp_info = pvp_info_with_shop(
                                        pvp_info_with_state(
                                            current_pvp_info,
                                            current_pvp_player,
                                            current_pvp_bot,
                                            round_number=current_pvp_round,
                                            turn_number=current_pvp_turn_number,
                                            current_index=0,
                                            additional_gamers=(current_pvp_extra_bot,),
                                        ),
                                        updated_shop,
                                        parse_varint_field(current_pvp_info, 41) or 0,
                                    )
                                    current_pvp_event_id += 1
                                    result = pvp_wet_cigarette_event_result_body(
                                        current_pvp_player, offer,
                                        die_roll=roll, heal_delta=heal,
                                        coin_delta=-price,
                                        event_id=current_pvp_event_id,
                                        event_time=event_time,
                                    )
                                    result = pvp_event_with_consumed_lucky(result, 0, consumed=lucky_consumed,
                                        event_id=current_pvp_event_id, event_time=server_time)
                                    result = pvp_event_with_toxin_removed(result,0,toxin_used,
                                        event_id=current_pvp_event_id,event_time=server_time)
                                    post_frames.append(encode_frame(
                                        255, 2,
                                        pvp_event_notification_body(
                                            result, current_pvp_info,
                                            server_time=event_time,
                                        ),
                                        error=0, index=0,
                                        length_mode=length_mode,
                                    ))
                                    LOG.info(
                                        "PVP wet cigarette bought-and-used cfg=%d "
                                        "roll=%d heal=%d hp=%d coin=%d->%d",
                                        offer_cfg_id, roll, heal, current_pvp_player_hp,
                                        current_coin, current_coin - price,
                                    )
                            elif offer_cfg_id in EJECT_AMMO_SKILLS:
                                if (
                                    offer_status != 1
                                    or price <= 0
                                    or current_coin < price
                                    or requested_target not in (0, 1, 2)
                                ):
                                    response_error = 1
                                else:
                                    target_index = int(requested_target)
                                    gamers = [
                                        current_pvp_player, current_pvp_bot,
                                        current_pvp_extra_bot,
                                    ]
                                    hit_points = [
                                        current_pvp_player_hp, current_pvp_bot_hp,
                                        current_pvp_extra_bot_hp,
                                    ]
                                    real_ammo = [
                                        current_pvp_player_ammo, current_pvp_bot_ammo,
                                        current_pvp_extra_bot_ammo,
                                    ]
                                    fake_ammo = [
                                        current_pvp_player_fake_ammo,
                                        current_pvp_bot_fake_ammo,
                                        current_pvp_extra_bot_fake_ammo,
                                    ]
                                    ejected_id = (
                                        _draw_loaded_ammo(
                                            real_ammo[target_index], fake_ammo[target_index], current_pvp_damage_bonus[target_index]
                                        ) if not _pvp_is_eliminated(
                                            hit_points[target_index],
                                            current_pvp_virtual_hp_at(target_index),
                                        ) else None
                                    )
                                    if ejected_id is None:
                                        response_error = 1
                                    else:
                                        if ejected_id == 300:
                                            fake_ammo[target_index] -= 1
                                        elif ejected_id == 2:
                                            current_pvp_damage_bonus[target_index] -= 1
                                        else:
                                            real_ammo[target_index] -= 1
                                        reload_ammo_after = None
                                        if (
                                            not _pvp_is_eliminated(
                                                hit_points[target_index],
                                                current_pvp_virtual_hp_at(target_index),
                                            )
                                            and real_ammo[target_index] + current_pvp_damage_bonus[target_index] <= 0
                                        ):
                                            target_gun = parse_bytes_field(
                                                gamers[target_index], 7
                                            ) or b""
                                            reload_ammo_after = _reload_weapon_ammo(
                                                parse_varint_field(target_gun, 1) or 0,
                                                current_pvp_damage_bonus, target_index,
                                                randomize=state.randomize_magazines,
                                            )
                                            real_ammo[target_index], fake_ammo[target_index] = (
                                                reload_ammo_after
                                            )
                                            LOG.info(
                                                "PVP ejector auto-reload target=%d real=%d fake=%d",
                                                target_index, *reload_ammo_after,
                                            )
                                        gamers[target_index] = pvp_gamer_with_state(
                                            gamers[target_index],
                                            weapon_reloaded=reload_ammo_after is not None,
                                            hp=hit_points[target_index],
                                            ammo_number=real_ammo[target_index],
                                            fake_ammo_number=fake_ammo[target_index],
                                            enhanced_ammo_number=current_pvp_damage_bonus[target_index],
                                            round_number=current_pvp_round,
                                        )
                                        gamers[0] = pvp_gamer_with_coin_and_card(
                                            gamers[0],
                                            coin=current_coin - price,
                                            card_slot=slot if slot_id > 0 else None,
                                        )
                                        (
                                            current_pvp_player, current_pvp_bot,
                                            current_pvp_extra_bot,
                                        ) = gamers
                                        (
                                            current_pvp_player_ammo, current_pvp_bot_ammo,
                                            current_pvp_extra_bot_ammo,
                                        ) = real_ammo
                                        (
                                            current_pvp_player_fake_ammo,
                                            current_pvp_bot_fake_ammo,
                                            current_pvp_extra_bot_fake_ammo,
                                        ) = fake_ammo
                                        updated_shop = tuple(
                                            pvp_shop_card(
                                                parse_varint_field(card, 1) or 0,
                                                parse_varint_field(card, 2) or 0,
                                                parse_varint_field(card, 3) or 0,
                                                parse_varint_field(card, 4) or 1,
                                                2 if (parse_varint_field(card, 1) or 0) == card_id
                                                else (parse_varint_field(card, 5) or 1),
                                            )
                                            for card in shop_cards
                                        )
                                        current_pvp_info = pvp_info_with_shop(
                                            pvp_info_with_state(
                                                current_pvp_info,
                                                current_pvp_player,
                                                current_pvp_bot,
                                                round_number=current_pvp_round,
                                                turn_number=current_pvp_turn_number,
                                                current_index=0,
                                                additional_gamers=(current_pvp_extra_bot,),
                                            ),
                                            updated_shop,
                                            parse_varint_field(current_pvp_info, 41) or 0,
                                        )
                                        current_pvp_event_id += 1
                                        result = pvp_eject_ammo_card_event_result_body(
                                            current_pvp_player,
                                            gamers[target_index],
                                            offer,
                                            target_index=target_index,
                                            ejected_ammo_cfg_id=ejected_id,
                                            coin_delta=-price,
                                            event_id=current_pvp_event_id,
                                            event_time=event_time,
                                            reload_ammo_after=reload_ammo_after,
                                        )
                                        post_frames.append(encode_frame(
                                            255, 2,
                                            pvp_event_notification_body(
                                                result, current_pvp_info,
                                                server_time=event_time,
                                            ),
                                            error=0, index=0,
                                            length_mode=length_mode,
                                        ))
                                        LOG.info(
                                            "PVP ejector bought-and-used offer=%d "
                                            "target=%d ejected=%d real=%d fake=%d",
                                            card_id, target_index, ejected_id,
                                            real_ammo[target_index], fake_ammo[target_index],
                                        )
                            elif (
                                offer is not None
                                and offer_cfg_id in LAB_CARD_SKILLS
                                and offer_cfg_id not in HALLUCINOGEN_SKILLS
                                and offer_cfg_id not in WET_CIGARETTE_SKILLS
                                and offer_cfg_id not in EJECT_AMMO_SKILLS
                                and offer_cfg_id not in (REAL_AMMO_CARD_CFG_ID,
                                                         FAKE_AMMO_CARD_CFG_ID,
                                                         SPARE_MAGAZINE_CARD_CFG_ID)
                                and offer_status == 1
                                and (price > 0 or (price == 0 and offer_cfg_id == 2036))
                                and current_coin >= price
                                and current_pvp_extra_bot
                            ):
                                # Generic cards still use the official
                                # PvpEventResult/skill contract.  Their
                                # deterministic local effects make every
                                # catalog card usable while we continue
                                # collecting live traces for exact balance.
                                target_index = (
                                    int(requested_target)
                                    if requested_target in (0, 1, 2) else 0
                                )
                                gamers = [
                                    current_pvp_player, current_pvp_bot,
                                    current_pvp_extra_bot,
                                ]
                                hit_points = [
                                    current_pvp_player_hp, current_pvp_bot_hp,
                                    current_pvp_extra_bot_hp,
                                ]
                                virtual_hit_points = [
                                    current_pvp_player_virtual_hp,
                                    current_pvp_bot_virtual_hp,
                                    current_pvp_extra_bot_virtual_hp,
                                ]
                                real_ammo = [
                                    current_pvp_player_ammo, current_pvp_bot_ammo,
                                    current_pvp_extra_bot_ammo,
                                ]
                                fake_ammo = [
                                    current_pvp_player_fake_ammo,
                                    current_pvp_bot_fake_ammo,
                                    current_pvp_extra_bot_fake_ammo,
                                ]
                                if _pvp_is_eliminated(
                                    hit_points[target_index],
                                    current_pvp_virtual_hp_at(target_index),
                                ):
                                    response_error = 1
                                elif offer_cfg_id == 2032 and target_index == 0:
                                    response_error = 1
                                    LOG.info("PVP Rocket Launcher rejected self-target")
                                elif offer_cfg_id == 2032 and (
                                    current_pvp_player_ammo
                                    + current_pvp_player_fake_ammo
                                    + current_pvp_damage_bonus[0] <= 0
                                ):
                                    response_error = 1
                                    LOG.info("PVP Rocket Launcher rejected: source has no ammo")
                                elif (
                                    offer_cfg_id == 2015
                                    and current_pvp_maintenance_bonus[target_index]
                                ):
                                    # The shipped fight_error table maps 352 to
                                    # "The target already has this effect and
                                    # cannot stack." Reject before charging the
                                    # player or selling the shop offer.
                                    response_error = 352
                                    LOG.info(
                                        "PVP Maintenance Kit buy/use rejected: "
                                        "target=%d already has buff 1014",
                                        target_index,
                                    )
                                elif (
                                    offer_cfg_id == 2021
                                    and current_pvp_wanted_reward[target_index]
                                ):
                                    response_error = 352
                                    LOG.info(
                                        "PVP Wanted buy/use rejected: "
                                        "target=%d already has an active bounty",
                                        target_index,
                                    )
                                elif offer_cfg_id == 2018 and (
                                    target_index == 0
                                    or (parse_varint_field(gamers[target_index], 5) or 0) <= 0
                                ):
                                    # fight_error 380: target has no bounty.
                                    response_error = 380 if target_index else 1
                                    LOG.info(
                                        "PVP Violation Ticket rejected: target=%d coin=%d",
                                        target_index,
                                        parse_varint_field(gamers[target_index], 5) or 0,
                                    )
                                else:
                                    event_type = 0
                                    hp_delta = 0
                                    add_buff_cfg = None
                                    add_buff_cfgs = ()
                                    luck_roll = None
                                    lucky_consumed = False
                                    stolen_coin = 0
                                    new_slot = None
                                    r_ammo = None
                                    c_ammo = None
                                    is_rpg_hit = None
                                    source_u_ammo = ()
                                    source_virtual_hp_delta = 0
                                    target_virtual_hp_delta = 0
                                    target_dead = False
                                    rocket_reload_ammo_after = None
                                    rocket_ghosts_added = 0
                                    rocket_blocked_katie = None
                                    skill_cd = None
                                    if offer_cfg_id == 2009:
                                        # Arms Voucher changes one existing cfg 1
                                        # round into cfg 2 (the bundled
                                        # "enhanced bullet").  The magazine
                                        # size must stay unchanged: the next
                                        # real shot consumes cfg 2 and deals two
                                        # damage.
                                        if real_ammo[target_index] <= 0:
                                            response_error = 1
                                            LOG.warning(
                                                "PVP Arms Voucher rejected: "
                                                "target=%d has no real ammo",
                                                target_index,
                                            )
                                        else:
                                            real_before = real_ammo[target_index]
                                            real_ammo[target_index] -= 1
                                            event_type = 8
                                            current_pvp_damage_bonus[target_index] += 1
                                            r_ammo = (
                                                pb_message(
                                                    pb_varint(1, 300),
                                                    pb_varint(2, fake_ammo[target_index]),
                                                    pb_varint(3, 1),
                                                ),
                                                pb_message(
                                                    pb_varint(1, 1),
                                                    pb_varint(2, real_ammo[target_index]),
                                                    pb_varint(3, 3),
                                                ),
                                                pb_message(
                                                    pb_varint(1, 2),
                                                    pb_varint(2, current_pvp_damage_bonus[target_index]),
                                                    pb_varint(3, 4),
                                                ),
                                            )
                                            c_ammo = _c_ammo_message(
                                                1, 1, 2, 1
                                            )
                                    elif offer_cfg_id == 2032:
                                        virtual_hp = [
                                            current_pvp_player_virtual_hp,
                                            current_pvp_bot_virtual_hp,
                                            current_pvp_extra_bot_virtual_hp,
                                        ]
                                        rocket = _pvp_resolve_rocket_shot(
                                            gamers, hit_points, virtual_hp,
                                            real_ammo, fake_ammo,
                                            current_pvp_damage_bonus,
                                            0, target_index,
                                            round_number=current_pvp_round,
                                            randomize_magazines=state.randomize_magazines,
                                            katie_guards=current_pvp_katie_guards,
                                        )
                                        if rocket is None:
                                            response_error = 1
                                        else:
                                            event_type = 39  # Enum_Rpg
                                            is_rpg_hit = rocket.ammo_cfg_id != 300
                                            rocket_ghosts_added = rocket.ghosts_added_real
                                            rocket_blocked_katie = rocket.blocked_katie_buff
                                            hp_delta = rocket.target_hp_delta
                                            target_virtual_hp_delta = (
                                                rocket.target_virtual_hp_delta
                                            )
                                            target_dead = rocket.target_dead
                                            source_virtual_hp_delta = (
                                                rocket.shooter_virtual_hp_delta
                                            )
                                            source_u_ammo = tuple(
                                                pb_message(
                                                    pb_varint(1, cfg_id),
                                                    pb_varint(2, number),
                                                    pb_varint(3, 1 if cfg_id == 300 else 3 if cfg_id == 1 else 4),
                                                )
                                                for cfg_id, number in rocket.consumed_ammo
                                            )
                                            rocket_reload_ammo_after = (
                                                rocket.reload_ammo_after
                                            )
                                            (
                                                current_pvp_player_virtual_hp,
                                                current_pvp_bot_virtual_hp,
                                                current_pvp_extra_bot_virtual_hp,
                                            ) = virtual_hp
                                            LOG.info(
                                                "PVP Rocket Launcher resolved target=%d "
                                                "ammoCfg=%d consumed=%s damage=%d "
                                                "targetHp=%d targetFrenzy=%d "
                                                "shooterFrenzyDelta=%d reload=%s dead=%s",
                                                target_index, rocket.ammo_cfg_id,
                                                rocket.consumed_ammo, rocket.damage,
                                                rocket.target_hp_delta,
                                                rocket.target_virtual_hp_delta,
                                                rocket.shooter_virtual_hp_delta,
                                                rocket.reload_ammo_after,
                                                rocket.target_dead,
                                            )
                                    elif offer_cfg_id == 2029:
                                        add_buff_cfg = None
                                        reduction = tranquilizer_frenzy_reduction(
                                            hit_points[target_index],
                                            virtual_hit_points[target_index],
                                        )
                                        virtual_hit_points[target_index] -= reduction
                                        target_virtual_hp_delta = -reduction
                                        event_type = 14  # Enum_Hp_Vir
                                        LOG.info(
                                            "PVP Tranquilizer used source=shop target=%d "
                                            "hp=%d frenzy=%d->%d removed=%d",
                                            target_index,
                                            hit_points[target_index],
                                            virtual_hit_points[target_index] + reduction,
                                            virtual_hit_points[target_index],
                                            reduction,
                                        )
                                    elif offer_cfg_id == 2031:
                                        skill_cd = max(
                                            0, pvp_gamer_skill_cd(gamers[target_index]) - 1
                                        )
                                        gamers[target_index] = pvp_gamer_with_skill_cd(
                                            gamers[target_index], skill_cd,
                                        )
                                        event_type = 9  # Enum_Skill_Cd
                                    elif offer_cfg_id == 2018:
                                        # LanguagePortugal: roll a die and steal
                                        # its result x100 from the target's bounty.
                                        # Local PvpGamer.coin is the R-Coin amount
                                        # shown on that player's name board.
                                        gamers[0], luck_roll, lucky_consumed = _pvp_roll_lucky_die(gamers[0], random.randint(1, 6))
                                        target_coin = (
                                            parse_varint_field(gamers[target_index], 5) or 0
                                        )
                                        stolen_coin = min(target_coin, luck_roll * 100)
                                        gamers[target_index] = pvp_gamer_with_coin_and_card(
                                            gamers[target_index],
                                            coin=target_coin - stolen_coin,
                                        )
                                        event_type = 7  # Enum_Update_Luck
                                    elif offer_cfg_id in (2020, 2028, 2036, 2037):
                                        # Surprise boxes grant a deterministic
                                        # stored card, so the result is visible
                                        # and can be used on the following turn.
                                        reward_cfg, reward_price = random.choice(
                                            tuple(spec for spec in PVP_LAB_REWARD_SPECS
                                                  if spec[0] not in (2020, 2028, 2036, 2037))
                                        )
                                        LOG.info(
                                            "PVP Surprise Box reward source=%d reward=%d card=%d",
                                            offer_cfg_id, reward_cfg,
                                            current_pvp_shop_next_id,
                                        )
                                        new_slot = pvp_card_slot_body(
                                            pvp_shop_card(
                                                current_pvp_shop_next_id,
                                                reward_cfg, reward_price,
                                            )
                                        )
                                        current_pvp_shop_next_id += 1
                                        event_type = 0
                                    else:
                                        add_buff_cfg = (
                                            MAINTENANCE_KIT_BUFF_CFG_ID
                                            if offer_cfg_id == 2015 else
                                            BURST_MODE_BUFF_CFG_ID
                                            if offer_cfg_id == 2016 else ITEM_BUFF_CFG.get(offer_cfg_id, offer_cfg_id)
                                        )
                                        event_type = 10
                                        if offer_cfg_id == 2015:
                                            current_pvp_maintenance_bonus[target_index] = 1
                                        elif offer_cfg_id == 2016:
                                            current_pvp_burst_mode[target_index] += 1
                                        elif offer_cfg_id == 2033:
                                            current_pvp_bucket_guard[target_index] = True
                                        elif offer_cfg_id in (2022, 2030):
                                            add_buff_cfg = current_pvp_restrictions.apply_to_gamer(
                                                gamers, target_index, offer_cfg_id,
                                                source_index=0,
                                            )
                                        elif offer_cfg_id == 2021:
                                            add_buff_cfg = None
                                            add_buff_cfgs = (
                                                WANTED_PARENT_BUFF_CFG_ID,
                                                WANTED_REWARD_BUFF_CFG_ID,
                                            )
                                            wanted_duration = _pvp_apply_wanted(
                                                gamers, target_index,
                                                current_pvp_wanted_reward,
                                                current_pvp_wanted_expire_turn,
                                                current_pvp_wanted_turn_clock,
                                            )
                                            LOG.info(
                                                "PVP Wanted applied source=shop target=%d "
                                                "reward=%d round=%d turn_clock=%d "
                                                "duration=%d expires_turn_clock=%d",
                                                target_index,
                                                WANTED_REWARD_R_CHIPS,
                                                current_pvp_round,
                                                current_pvp_wanted_turn_clock,
                                                wanted_duration,
                                                current_pvp_wanted_expire_turn[
                                                    target_index
                                                ],
                                            )
                                    gamers[target_index] = pvp_gamer_with_state(
                                        gamers[target_index],
                                        hp=hit_points[target_index],
                                        ammo_number=real_ammo[target_index],
                                        fake_ammo_number=fake_ammo[target_index],
                                        enhanced_ammo_number=(
                                            current_pvp_damage_bonus[target_index]
                                        ),
                                        round_number=current_pvp_round,
                                        virtual_hp=virtual_hit_points[target_index],
                                        burst_mode_active=(
                                            bool(current_pvp_burst_mode[target_index])
                                        ),
                                        maintenance_kit_active=bool(
                                            current_pvp_maintenance_bonus[target_index]
                                        ),
                                    )
                                    current_pvp_player = pvp_gamer_with_coin_and_card(
                                        gamers[0], coin=current_coin - price + stolen_coin,
                                        card_slot=(new_slot or (slot if slot_id > 0 else None)),
                                    )
                                    gamers[0] = current_pvp_player
                                    (
                                        current_pvp_player, current_pvp_bot,
                                        current_pvp_extra_bot,
                                    ) = gamers
                                    (
                                        current_pvp_player_hp, current_pvp_bot_hp,
                                        current_pvp_extra_bot_hp,
                                    ) = hit_points
                                    (
                                        current_pvp_player_ammo, current_pvp_bot_ammo,
                                        current_pvp_extra_bot_ammo,
                                    ) = real_ammo
                                    (
                                        current_pvp_player_fake_ammo,
                                        current_pvp_bot_fake_ammo,
                                        current_pvp_extra_bot_fake_ammo,
                                    ) = fake_ammo
                                    (
                                        current_pvp_player_virtual_hp,
                                        current_pvp_bot_virtual_hp,
                                        current_pvp_extra_bot_virtual_hp,
                                    ) = virtual_hit_points
                                    updated_shop = tuple(
                                        pvp_shop_card(
                                            parse_varint_field(card, 1) or 0,
                                            parse_varint_field(card, 2) or 0,
                                            parse_varint_field(card, 3) or 0,
                                            parse_varint_field(card, 4) or 1,
                                            2 if (parse_varint_field(card, 1) or 0) == card_id
                                            else (parse_varint_field(card, 5) or 1),
                                        ) for card in shop_cards
                                    )
                                    current_pvp_event_id += 1
                                    current_pvp_info = pvp_info_with_shop(
                                        pvp_info_with_state(
                                            current_pvp_info,
                                            current_pvp_player,
                                            current_pvp_bot,
                                            round_number=current_pvp_round,
                                            turn_number=current_pvp_turn_number,
                                            current_index=0,
                                            additional_gamers=(current_pvp_extra_bot,),
                                        ),
                                        updated_shop,
                                        parse_varint_field(current_pvp_info, 41) or 0,
                                    )
                                    result = pvp_generic_card_event_result_body(
                                        current_pvp_player,
                                        gamers[target_index],
                                        offer,
                                        skill_id=LAB_CARD_SKILLS[offer_cfg_id],
                                        target_index=target_index,
                                        event_id=current_pvp_event_id,
                                        event_type=event_type,
                                        hp_delta=hp_delta,
                                        virtual_hp_delta=target_virtual_hp_delta,
                                        coin_delta=-price,
                                        clear_slot=False,
                                        new_card_slot=new_slot,
                                        r_ammo=r_ammo,
                                        c_ammo=c_ammo,
                                        skill_cd=skill_cd,
                                        add_buff_cfg=add_buff_cfg,
                                        add_buff_cfgs=add_buff_cfgs,
                                        luck_roll=luck_roll,
                                        luck_success=luck_roll is not None,
                                        stolen_coin=stolen_coin,
                                        is_rpg_hit=is_rpg_hit,
                                        source_u_ammo=source_u_ammo,
                                        source_virtual_hp_delta=source_virtual_hp_delta,
                                        target_dead=target_dead,
                                        reload_ammo_after=rocket_reload_ammo_after,
                                        ghosts_added_real=rocket_ghosts_added,
                                        target_del_buff_cfgs=(rocket_blocked_katie,) if rocket_blocked_katie else (),
                                        event_time=event_time,
                                        buy=True,
                                    )
                                    result = pvp_event_with_consumed_lucky(result, 0, consumed=lucky_consumed,
                                        event_id=current_pvp_event_id, event_time=server_time)
                                    post_frames.append(encode_frame(
                                        255, 2,
                                        pvp_event_notification_body(
                                            result, current_pvp_info,
                                            server_time=event_time,
                                        ), error=0, index=0,
                                        length_mode=length_mode,
                                    ))
                                    LOG.info(
                                        "PVP generic buy/use cfg=%d skill=%d target=%d hpDelta=%d "
                                        "targetAmmo=%d/%d enhanced=%d die=%s stolen=%d",
                                        offer_cfg_id, LAB_CARD_SKILLS[offer_cfg_id],
                                        target_index, hp_delta,
                                        real_ammo[target_index],
                                        fake_ammo[target_index],
                                        current_pvp_damage_bonus[target_index],
                                        luck_roll, stolen_coin,
                                    )
                            elif (
                                offer is None
                                or offer_cfg_id not in HALLUCINOGEN_SKILLS
                                or offer_status != 1
                                or price <= 0
                                or current_coin < price
                                or requested_target not in (0, 1, 2)
                            ):
                                response_error = 1
                                LOG.warning(
                                    "PVP buy-and-use rejected id=%d cfg=%d status=%d "
                                    "price=%d coin=%d target=%r",
                                    card_id,
                                    offer_cfg_id,
                                    offer_status,
                                    price,
                                    current_coin,
                                    requested_target,
                                )
                            else:
                                target_index = int(requested_target)
                                gamers = [
                                    current_pvp_player,
                                    current_pvp_bot,
                                    current_pvp_extra_bot,
                                ]
                                hit_points = [
                                    current_pvp_player_hp,
                                    current_pvp_bot_hp,
                                    current_pvp_extra_bot_hp,
                                ]
                                virtual_hit_points = [
                                    current_pvp_player_virtual_hp,
                                    current_pvp_bot_virtual_hp,
                                    current_pvp_extra_bot_virtual_hp,
                                ]
                                real_ammo = [
                                    current_pvp_player_ammo,
                                    current_pvp_bot_ammo,
                                    current_pvp_extra_bot_ammo,
                                ]
                                fake_ammo = [
                                    current_pvp_player_fake_ammo,
                                    current_pvp_bot_fake_ammo,
                                    current_pvp_extra_bot_fake_ammo,
                                ]
                                self_shots = [
                                    current_pvp_player_self_shots,
                                    current_pvp_bot_self_shots,
                                    current_pvp_extra_bot_self_shots,
                                ]
                                old_target = gamers[target_index]
                                resolved = _resolve_hallucinogen_self_shot(
                                    gamers,
                                    hit_points,
                                    virtual_hit_points,
                                    real_ammo,
                                    fake_ammo,
                                    self_shots,
                                    target_index,
                                    round_number=current_pvp_round,
                                    event_id=current_pvp_event_id + 1,
                                    event_time=event_time + 1,
                                    randomize_magazines=state.randomize_magazines,
                                    enhanced_ammo=current_pvp_damage_bonus,
                                )
                                if resolved is None:
                                    response_error = 1
                                    LOG.warning(
                                        "PVP buy-and-use rejected id=%d target=%d "
                                        "hp=%d ammo=%d",
                                        card_id,
                                        target_index,
                                        hit_points[target_index],
                                        real_ammo[target_index] + fake_ammo[target_index],
                                    )
                                else:
                                    updated_target, ammo_cfg_id, match_ended, shot_result = resolved
                                    current_pvp_event_id += 1
                                    current_pvp_player = pvp_gamer_with_coin_and_card(
                                        gamers[0],
                                        coin=current_coin - price,
                                        card_slot=slot if slot_id > 0 else None,
                                    )
                                    gamers[0] = current_pvp_player
                                    updated_shop = tuple(
                                        pvp_shop_card(
                                            parse_varint_field(card, 1) or 0,
                                            parse_varint_field(card, 2) or 0,
                                            parse_varint_field(card, 3) or 0,
                                            parse_varint_field(card, 4) or 1,
                                            2 if (parse_varint_field(card, 1) or 0) == card_id
                                            else (parse_varint_field(card, 5) or 1),
                                        )
                                        for card in shop_cards
                                    )
                                    (
                                        current_pvp_player,
                                        current_pvp_bot,
                                        current_pvp_extra_bot,
                                    ) = gamers
                                    (
                                        current_pvp_player_hp,
                                        current_pvp_bot_hp,
                                        current_pvp_extra_bot_hp,
                                    ) = hit_points
                                    (
                                        current_pvp_player_virtual_hp,
                                        current_pvp_bot_virtual_hp,
                                        current_pvp_extra_bot_virtual_hp,
                                    ) = virtual_hit_points
                                    (
                                        current_pvp_player_ammo,
                                        current_pvp_bot_ammo,
                                        current_pvp_extra_bot_ammo,
                                    ) = real_ammo
                                    (
                                        current_pvp_player_fake_ammo,
                                        current_pvp_bot_fake_ammo,
                                        current_pvp_extra_bot_fake_ammo,
                                    ) = fake_ammo
                                    (
                                        current_pvp_player_self_shots,
                                        current_pvp_bot_self_shots,
                                        current_pvp_extra_bot_self_shots,
                                    ) = self_shots
                                    current_pvp_info = pvp_info_with_state(
                                        current_pvp_info,
                                        current_pvp_player,
                                        current_pvp_bot,
                                        round_number=current_pvp_round,
                                        turn_number=current_pvp_turn_number,
                                        current_index=0,
                                        additional_gamers=(current_pvp_extra_bot,),
                                    )
                                    current_pvp_info = pvp_info_with_shop(
                                        current_pvp_info,
                                        updated_shop,
                                        parse_varint_field(current_pvp_info, 41) or 0,
                                    )
                                    if (
                                        _pvp_is_eliminated(
                                            hit_points[target_index],
                                            virtual_hit_points[target_index],
                                        )
                                        and target_index not in current_pvp_eliminated_order
                                    ):
                                        current_pvp_eliminated_order.append(target_index)
                                    survivors = [
                                        idx for idx, (hp, frenzy) in enumerate(
                                            zip(hit_points, virtual_hit_points)
                                        ) if not _pvp_is_eliminated(hp, frenzy)
                                    ]
                                    if match_ended:
                                        winner = survivors[0]
                                        ranks = {winner: 1}
                                        for death_order, eliminated in enumerate(
                                            current_pvp_eliminated_order
                                        ):
                                            ranks[eliminated] = max(2, 3 - death_order)
                                        for gamer_index in range(3):
                                            gamers[gamer_index] = pvp_gamer_with_state(
                                                gamers[gamer_index],
                                                hp=hit_points[gamer_index],
                                                ammo_number=real_ammo[gamer_index],
                                                fake_ammo_number=fake_ammo[gamer_index],
                                                enhanced_ammo_number=current_pvp_damage_bonus[gamer_index],
                                                round_number=current_pvp_round,
                                                is_dead=_pvp_is_eliminated(
                                                    hit_points[gamer_index],
                                                    virtual_hit_points[gamer_index],
                                                ),
                                                virtual_hp=virtual_hit_points[gamer_index],
                                                rank=ranks.get(gamer_index, 2),
                                            )
                                        (
                                            current_pvp_player,
                                            current_pvp_bot,
                                            current_pvp_extra_bot,
                                        ) = gamers
                                        current_pvp_info = pvp_info_with_end(
                                            pvp_info_with_state(
                                                current_pvp_info,
                                                gamers[0],
                                                gamers[1],
                                                round_number=current_pvp_round,
                                                turn_number=current_pvp_turn_number,
                                                current_index=winner,
                                                status=4,
                                                additional_gamers=(gamers[2],),
                                            ),
                                            end_time=event_time + 3,
                                        )
                                        current_pvp_turn = -1
                                    result = pvp_hallucinogen_buy_and_use_event_result_body(
                                        current_pvp_player,
                                        old_target,
                                        offer,
                                        coin_delta=-price,
                                        target_index=target_index,
                                        event_id=current_pvp_event_id,
                                        event_time=event_time,
                                        shot_result=shot_result,
                                    )
                                    post_frames.append(
                                        encode_frame(
                                            255,
                                            2,
                                            pvp_event_notification_body(
                                                result,
                                                current_pvp_info,
                                                server_time=event_time,
                                            ),
                                            error=0,
                                            index=0,
                                            length_mode=length_mode,
                                        )
                                    )
                                    if match_ended:
                                        delayed_frames.append(
                                            (
                                                2.5,
                                                encode_frame(
                                                    255,
                                                    5,
                                                    pvp_end_body(current_pvp_info),
                                                    error=0,
                                                    index=0,
                                                    length_mode=length_mode,
                                                ),
                                            )
                                        )
                                    LOG.info(
                                        "PVP hallucinogen bought-and-used offer=%d target=%d "
                                        "price=%d coin=%d->%d ammo=%d hp=%d->%d ended=%s",
                                        card_id,
                                        target_index,
                                        price,
                                        current_coin,
                                        current_coin - price,
                                        ammo_cfg_id,
                                        hit_points[target_index] + int(ammo_cfg_id == 1),
                                        hit_points[target_index],
                                        match_ended,
                                    )
                        elif action_type == 2:
                            slot_cfg_id = parse_varint_field(slot, 2) or 0
                            requested_target = parse_varint_field(body, 2)
                            stored_coins = max(0, parse_varint_field(slot, 7) or 0)
                            if (
                                slot_id > 0
                                and card_id == slot_id
                                and slot_cfg_id in PIGGYBANK_COINS_PER_TURN
                                and requested_target in (None, 0)
                                and stored_coins > 0
                            ):
                                current_coin = parse_varint_field(current_pvp_player, 5) or 0
                                current_pvp_player = pvp_gamer_with_coin_and_card(
                                    current_pvp_player,
                                    coin=current_coin + stored_coins,
                                    card_slot=pvp_empty_card_slot_body(),
                                )
                                additional_gamers = (
                                    (current_pvp_extra_bot,)
                                    if current_pvp_extra_bot else ()
                                )
                                current_pvp_info = pvp_info_with_state(
                                    current_pvp_info,
                                    current_pvp_player,
                                    current_pvp_bot,
                                    round_number=current_pvp_round,
                                    turn_number=current_pvp_turn_number,
                                    current_index=0,
                                    additional_gamers=additional_gamers,
                                )
                                current_pvp_event_id += 1
                                result = pvp_piggybank_use_event_result_body(
                                    current_pvp_player,
                                    slot,
                                    coin_delta=stored_coins,
                                    event_id=current_pvp_event_id,
                                    event_time=event_time,
                                )
                                post_frames.append(
                                    encode_frame(
                                        255,
                                        2,
                                        pvp_event_notification_body(
                                            result,
                                            current_pvp_info,
                                            server_time=event_time,
                                        ),
                                        error=0,
                                        index=0,
                                        length_mode=length_mode,
                                    )
                                )
                                LOG.info(
                                    "PVP piggybank collected cfg=%d card=%d amount=%d coin=%d->%d",
                                    slot_cfg_id,
                                    slot_id,
                                    stored_coins,
                                    current_coin,
                                    current_coin + stored_coins,
                                )
                            elif (
                                slot_id > 0
                                and card_id == slot_id
                                and slot_cfg_id in (REAL_AMMO_CARD_CFG_ID, FAKE_AMMO_CARD_CFG_ID)
                                and current_pvp_extra_bot
                                and requested_target in (0, 1, 2)
                            ):
                                target_index = int(requested_target)
                                gamers = [
                                    current_pvp_player, current_pvp_bot,
                                    current_pvp_extra_bot,
                                ]
                                hit_points = [
                                    current_pvp_player_hp, current_pvp_bot_hp,
                                    current_pvp_extra_bot_hp,
                                ]
                                real_ammo = [
                                    current_pvp_player_ammo, current_pvp_bot_ammo,
                                    current_pvp_extra_bot_ammo,
                                ]
                                fake_ammo = [
                                    current_pvp_player_fake_ammo,
                                    current_pvp_bot_fake_ammo,
                                    current_pvp_extra_bot_fake_ammo,
                                ]
                                virtual_hit_points = [
                                    current_pvp_player_virtual_hp,
                                    current_pvp_bot_virtual_hp,
                                    current_pvp_extra_bot_virtual_hp,
                                ]
                                if _pvp_is_eliminated(
                                    hit_points[target_index],
                                    current_pvp_virtual_hp_at(target_index),
                                ):
                                    response_error = 1
                                else:
                                    if not pvp_gamer_has_ammo_space(
                                        gamers[target_index], real_ammo[target_index],
                                        fake_ammo[target_index], current_pvp_damage_bonus[target_index],
                                    ):
                                        response_error = 1
                                        LOG.info("PVP stored add-ammo rejected: gun full target=%d", target_index)
                                        frame = encode_frame(head.cmd, head.act, b"", index=head.index, error=response_error, length_mode=length_mode)
                                        trace_frame(service, "S->C", frame, length_mode, "response", state_snapshot())
                                        writer.write(frame)
                                        await writer.drain()
                                        continue
                                    if slot_cfg_id == FAKE_AMMO_CARD_CFG_ID:
                                        fake_ammo[target_index] += 1
                                    else:
                                        real_ammo[target_index] += 1
                                    gamers[target_index] = pvp_gamer_with_state(
                                        gamers[target_index],
                                        hp=hit_points[target_index],
                                        ammo_number=real_ammo[target_index],
                                        fake_ammo_number=fake_ammo[target_index],
                                        enhanced_ammo_number=(
                                            current_pvp_damage_bonus[target_index]
                                        ),
                                        round_number=current_pvp_round,
                                        burst_mode_active=(
                                            bool(current_pvp_burst_mode[target_index])
                                        ),
                                    )
                                    gamers[0] = pvp_gamer_with_coin_and_card(
                                        gamers[0],
                                        coin=current_coin,
                                        card_slot=pvp_empty_card_slot_body(),
                                    )
                                    (
                                        current_pvp_player, current_pvp_bot,
                                        current_pvp_extra_bot,
                                    ) = gamers
                                    (
                                        current_pvp_player_ammo, current_pvp_bot_ammo,
                                        current_pvp_extra_bot_ammo,
                                    ) = real_ammo
                                    (
                                        current_pvp_player_fake_ammo,
                                        current_pvp_bot_fake_ammo,
                                        current_pvp_extra_bot_fake_ammo,
                                    ) = fake_ammo
                                    current_pvp_info = pvp_info_with_state(
                                        current_pvp_info,
                                        current_pvp_player,
                                        current_pvp_bot,
                                        round_number=current_pvp_round,
                                        turn_number=current_pvp_turn_number,
                                        current_index=0,
                                        additional_gamers=(current_pvp_extra_bot,),
                                    )
                                    current_pvp_event_id += 1
                                    result = pvp_add_ammo_card_event_result_body(
                                        current_pvp_player,
                                        gamers[target_index],
                                        slot,
                                        target_index=target_index,
                                        real_after=real_ammo[target_index],
                                        fake_after=fake_ammo[target_index],
                                        event_id=current_pvp_event_id,
                                        event_time=event_time,
                                    )
                                    post_frames.append(encode_frame(
                                        255, 2,
                                        pvp_event_notification_body(
                                            result, current_pvp_info,
                                            server_time=event_time,
                                        ),
                                        error=0, index=0,
                                        length_mode=length_mode,
                                    ))
                                    LOG.info(
                                        "PVP stored ammo used card=%d cfg=%d "
                                        "target=%d real=%d fake=%d",
                                        card_id, slot_cfg_id, target_index,
                                        real_ammo[target_index], fake_ammo[target_index],
                                    )
                            elif (
                                slot_id > 0
                                and card_id == slot_id
                                and slot_cfg_id == SPARE_MAGAZINE_CARD_CFG_ID
                                and current_pvp_extra_bot
                                and requested_target in (0, 1, 2)
                            ):
                                target_index = int(requested_target)
                                gamers = [
                                    current_pvp_player, current_pvp_bot,
                                    current_pvp_extra_bot,
                                ]
                                hit_points = [
                                    current_pvp_player_hp,
                                    current_pvp_bot_hp,
                                    current_pvp_extra_bot_hp,
                                ]
                                real_ammo = [
                                    current_pvp_player_ammo,
                                    current_pvp_bot_ammo,
                                    current_pvp_extra_bot_ammo,
                                ]
                                fake_ammo = [
                                    current_pvp_player_fake_ammo,
                                    current_pvp_bot_fake_ammo,
                                    current_pvp_extra_bot_fake_ammo,
                                ]
                                if _pvp_is_eliminated(
                                    hit_points[target_index],
                                    current_pvp_virtual_hp_at(target_index),
                                ):
                                    response_error = 1
                                else:
                                    old_real = real_ammo[target_index]
                                    old_fake = fake_ammo[target_index]
                                    target_gun = parse_bytes_field(
                                        gamers[target_index], 7
                                    ) or b""
                                    reload_real, reload_fake = _reload_weapon_ammo(
                                        parse_varint_field(target_gun, 1) or 0,
                                        current_pvp_damage_bonus, target_index,
                                        randomize=state.randomize_magazines,
                                    )
                                    real_ammo[target_index] = reload_real
                                    fake_ammo[target_index] = reload_fake
                                    gamers[target_index] = pvp_gamer_with_state(
                                        gamers[target_index],
                                        hp=hit_points[target_index],
                                        ammo_number=reload_real,
                                        weapon_reloaded=True,
                                        fake_ammo_number=reload_fake,
                                        enhanced_ammo_number=current_pvp_damage_bonus[target_index],
                                        round_number=current_pvp_round,
                                    )
                                    gamers[0] = pvp_gamer_with_coin_and_card(
                                        gamers[0],
                                        coin=current_coin,
                                        card_slot=pvp_empty_card_slot_body(),
                                    )
                                    (
                                        current_pvp_player, current_pvp_bot,
                                        current_pvp_extra_bot,
                                    ) = gamers
                                    (
                                        current_pvp_player_ammo,
                                        current_pvp_bot_ammo,
                                        current_pvp_extra_bot_ammo,
                                    ) = real_ammo
                                    (
                                        current_pvp_player_fake_ammo,
                                        current_pvp_bot_fake_ammo,
                                        current_pvp_extra_bot_fake_ammo,
                                    ) = fake_ammo
                                    current_pvp_info = pvp_info_with_state(
                                        current_pvp_info,
                                        current_pvp_player,
                                        current_pvp_bot,
                                        round_number=current_pvp_round,
                                        turn_number=current_pvp_turn_number,
                                        current_index=0,
                                        additional_gamers=(current_pvp_extra_bot,),
                                    )
                                    current_pvp_event_id += 1
                                    result = pvp_spare_magazine_event_result_body(
                                        current_pvp_player,
                                        gamers[target_index],
                                        slot,
                                        target_index=target_index,
                                        old_real=old_real,
                                        old_fake=old_fake,
                                        real_after=reload_real,
                                        fake_after=reload_fake,
                                        event_id=current_pvp_event_id,
                                        event_time=event_time,
                                    )
                                    post_frames.append(encode_frame(
                                        255, 2,
                                        pvp_event_notification_body(
                                            result, current_pvp_info,
                                            server_time=event_time,
                                        ),
                                        error=0, index=0,
                                        length_mode=length_mode,
                                    ))
                                    LOG.info(
                                        "PVP stored spare magazine used card=%d "
                                        "target=%d old=%d/%d new=%d/%d",
                                        card_id, target_index, old_real, old_fake,
                                        real_ammo[target_index], fake_ammo[target_index],
                                    )
                            elif (
                                slot_id > 0
                                and card_id == slot_id
                                and slot_cfg_id in WET_CIGARETTE_SKILLS
                                and current_pvp_extra_bot
                                and requested_target in (None, 0)
                                and not _pvp_is_eliminated(
                                    current_pvp_player_hp,
                                    current_pvp_player_virtual_hp,
                                )
                            ):
                                current_pvp_player, roll, lucky_consumed = _pvp_roll_lucky_die(current_pvp_player, random.randint(1, 6))
                                heal = _pvp_wet_cigarette_heal(
                                    current_pvp_player_hp,
                                    current_pvp_player_virtual_hp,
                                    roll,
                                )
                                current_pvp_player, heal, toxin_used = pvp_consume_toxin_heal(current_pvp_player,heal)
                                current_pvp_player_hp += heal
                                current_pvp_player = pvp_gamer_with_state(
                                    current_pvp_player,
                                    hp=current_pvp_player_hp,
                                    ammo_number=current_pvp_player_ammo,
                                    fake_ammo_number=current_pvp_player_fake_ammo,
                                    enhanced_ammo_number=current_pvp_damage_bonus[0],
                                    round_number=current_pvp_round,
                                )
                                current_pvp_player = pvp_gamer_with_coin_and_card(
                                    current_pvp_player,
                                    coin=current_coin,
                                    card_slot=pvp_empty_card_slot_body(),
                                )
                                current_pvp_info = pvp_info_with_state(
                                    current_pvp_info,
                                    current_pvp_player,
                                    current_pvp_bot,
                                    round_number=current_pvp_round,
                                    turn_number=current_pvp_turn_number,
                                    current_index=0,
                                    additional_gamers=(current_pvp_extra_bot,),
                                )
                                current_pvp_event_id += 1
                                result = pvp_wet_cigarette_event_result_body(
                                    current_pvp_player, slot,
                                    die_roll=roll, heal_delta=heal,
                                    event_id=current_pvp_event_id,
                                    event_time=event_time,
                                )
                                result = pvp_event_with_consumed_lucky(result, 0, consumed=lucky_consumed,
                                    event_id=current_pvp_event_id, event_time=server_time)
                                result = pvp_event_with_toxin_removed(result,0,toxin_used,
                                    event_id=current_pvp_event_id,event_time=server_time)
                                post_frames.append(encode_frame(
                                    255, 2,
                                    pvp_event_notification_body(
                                        result, current_pvp_info,
                                        server_time=event_time,
                                    ),
                                    error=0, index=0,
                                    length_mode=length_mode,
                                ))
                                LOG.info(
                                    "PVP stored wet cigarette used cfg=%d "
                                    "roll=%d heal=%d hp=%d",
                                    slot_cfg_id, roll, heal, current_pvp_player_hp,
                                )
                            elif (
                                slot_id > 0
                                and card_id == slot_id
                                and slot_cfg_id in EJECT_AMMO_SKILLS
                                and current_pvp_extra_bot
                                and requested_target in (0, 1, 2)
                            ):
                                target_index = int(requested_target)
                                gamers = [
                                    current_pvp_player, current_pvp_bot,
                                    current_pvp_extra_bot,
                                ]
                                hit_points = [
                                    current_pvp_player_hp, current_pvp_bot_hp,
                                    current_pvp_extra_bot_hp,
                                ]
                                real_ammo = [
                                    current_pvp_player_ammo, current_pvp_bot_ammo,
                                    current_pvp_extra_bot_ammo,
                                ]
                                fake_ammo = [
                                    current_pvp_player_fake_ammo,
                                    current_pvp_bot_fake_ammo,
                                    current_pvp_extra_bot_fake_ammo,
                                ]
                                ejected_id = (
                                    _draw_loaded_ammo(
                                        real_ammo[target_index], fake_ammo[target_index], current_pvp_damage_bonus[target_index]
                                    ) if not _pvp_is_eliminated(
                                        hit_points[target_index],
                                        current_pvp_virtual_hp_at(target_index),
                                    ) else None
                                )
                                if ejected_id is None:
                                    response_error = 1
                                else:
                                    if ejected_id == 300:
                                        fake_ammo[target_index] -= 1
                                    elif ejected_id == 2:
                                        current_pvp_damage_bonus[target_index] -= 1
                                    else:
                                        real_ammo[target_index] -= 1
                                    reload_ammo_after = None
                                    if (
                                        not _pvp_is_eliminated(
                                            hit_points[target_index],
                                            current_pvp_virtual_hp_at(target_index),
                                        )
                                        and real_ammo[target_index] + current_pvp_damage_bonus[target_index] <= 0
                                    ):
                                        target_gun = parse_bytes_field(
                                            gamers[target_index], 7
                                        ) or b""
                                        reload_ammo_after = _reload_weapon_ammo(
                                            parse_varint_field(target_gun, 1) or 0,
                                            current_pvp_damage_bonus, target_index,
                                            randomize=state.randomize_magazines,
                                        )
                                        real_ammo[target_index], fake_ammo[target_index] = (
                                            reload_ammo_after
                                        )
                                        LOG.info(
                                            "PVP ejector auto-reload target=%d real=%d fake=%d",
                                            target_index, *reload_ammo_after,
                                        )
                                    gamers[target_index] = pvp_gamer_with_state(
                                        gamers[target_index],
                                        weapon_reloaded=reload_ammo_after is not None,
                                        hp=hit_points[target_index],
                                        ammo_number=real_ammo[target_index],
                                        fake_ammo_number=fake_ammo[target_index],
                                        enhanced_ammo_number=current_pvp_damage_bonus[target_index],
                                        round_number=current_pvp_round,
                                    )
                                    gamers[0] = pvp_gamer_with_coin_and_card(
                                        gamers[0],
                                        coin=current_coin,
                                        card_slot=pvp_empty_card_slot_body(),
                                    )
                                    (
                                        current_pvp_player, current_pvp_bot,
                                        current_pvp_extra_bot,
                                    ) = gamers
                                    (
                                        current_pvp_player_ammo, current_pvp_bot_ammo,
                                        current_pvp_extra_bot_ammo,
                                    ) = real_ammo
                                    (
                                        current_pvp_player_fake_ammo,
                                        current_pvp_bot_fake_ammo,
                                        current_pvp_extra_bot_fake_ammo,
                                    ) = fake_ammo
                                    current_pvp_info = pvp_info_with_state(
                                        current_pvp_info,
                                        current_pvp_player,
                                        current_pvp_bot,
                                        round_number=current_pvp_round,
                                        turn_number=current_pvp_turn_number,
                                        current_index=0,
                                        additional_gamers=(current_pvp_extra_bot,),
                                    )
                                    current_pvp_event_id += 1
                                    result = pvp_eject_ammo_card_event_result_body(
                                        current_pvp_player,
                                        gamers[target_index],
                                        slot,
                                        target_index=target_index,
                                        ejected_ammo_cfg_id=ejected_id,
                                        event_id=current_pvp_event_id,
                                        event_time=event_time,
                                        reload_ammo_after=reload_ammo_after,
                                    )
                                    post_frames.append(encode_frame(
                                        255, 2,
                                        pvp_event_notification_body(
                                            result, current_pvp_info,
                                            server_time=event_time,
                                        ),
                                        error=0, index=0,
                                        length_mode=length_mode,
                                    ))
                                    LOG.info(
                                        "PVP stored ejector used card=%d target=%d "
                                        "ejected=%d real=%d fake=%d",
                                        card_id, target_index, ejected_id,
                                        real_ammo[target_index], fake_ammo[target_index],
                                    )
                            elif (
                                slot_id > 0
                                and card_id == slot_id
                                and slot_cfg_id in HALLUCINOGEN_SKILLS
                                and current_pvp_extra_bot
                                and requested_target in (0, 1, 2)
                            ):
                                target_index = int(requested_target)
                                gamers = [
                                    current_pvp_player,
                                    current_pvp_bot,
                                    current_pvp_extra_bot,
                                ]
                                hit_points = [
                                    current_pvp_player_hp,
                                    current_pvp_bot_hp,
                                    current_pvp_extra_bot_hp,
                                ]
                                virtual_hit_points = [
                                    current_pvp_player_virtual_hp,
                                    current_pvp_bot_virtual_hp,
                                    current_pvp_extra_bot_virtual_hp,
                                ]
                                real_ammo = [
                                    current_pvp_player_ammo,
                                    current_pvp_bot_ammo,
                                    current_pvp_extra_bot_ammo,
                                ]
                                fake_ammo = [
                                    current_pvp_player_fake_ammo,
                                    current_pvp_bot_fake_ammo,
                                    current_pvp_extra_bot_fake_ammo,
                                ]
                                self_shots = [
                                    current_pvp_player_self_shots,
                                    current_pvp_bot_self_shots,
                                    current_pvp_extra_bot_self_shots,
                                ]
                                old_target = gamers[target_index]
                                current_pvp_event_id += 1
                                resolved = _resolve_hallucinogen_self_shot(
                                    gamers,
                                    hit_points,
                                    virtual_hit_points,
                                    real_ammo,
                                    fake_ammo,
                                    self_shots,
                                    target_index,
                                    round_number=current_pvp_round,
                                    event_id=current_pvp_event_id,
                                    event_time=event_time + 1,
                                    randomize_magazines=state.randomize_magazines,
                                    enhanced_ammo=current_pvp_damage_bonus,
                                )
                                if resolved is None:
                                    response_error = 1
                                    LOG.warning(
                                        "PVP hallucinogen use rejected id=%d target=%d hp=%d ammo=%d",
                                        card_id,
                                        target_index,
                                        parse_varint_field(old_target, 4) or 0,
                                        real_ammo[target_index] + fake_ammo[target_index],
                                    )
                                else:
                                    updated_target, ammo_cfg_id, match_ended, shot_result = resolved
                                    current_pvp_player = pvp_gamer_with_coin_and_card(
                                        gamers[0],
                                        coin=current_coin,
                                        card_slot=pvp_empty_card_slot_body(),
                                    )
                                    gamers[0] = current_pvp_player
                                    (
                                        current_pvp_player,
                                        current_pvp_bot,
                                        current_pvp_extra_bot,
                                    ) = gamers
                                    (
                                        current_pvp_player_hp,
                                        current_pvp_bot_hp,
                                        current_pvp_extra_bot_hp,
                                    ) = hit_points
                                    (
                                        current_pvp_player_virtual_hp,
                                        current_pvp_bot_virtual_hp,
                                        current_pvp_extra_bot_virtual_hp,
                                    ) = virtual_hit_points
                                    (
                                        current_pvp_player_ammo,
                                        current_pvp_bot_ammo,
                                        current_pvp_extra_bot_ammo,
                                    ) = real_ammo
                                    (
                                        current_pvp_player_fake_ammo,
                                        current_pvp_bot_fake_ammo,
                                        current_pvp_extra_bot_fake_ammo,
                                    ) = fake_ammo
                                    (
                                        current_pvp_player_self_shots,
                                        current_pvp_bot_self_shots,
                                        current_pvp_extra_bot_self_shots,
                                    ) = self_shots
                                    if (
                                        _pvp_is_eliminated(
                                            hit_points[target_index],
                                            virtual_hit_points[target_index],
                                        )
                                        and target_index not in current_pvp_eliminated_order
                                    ):
                                        current_pvp_eliminated_order.append(target_index)
                                    current_pvp_info = pvp_info_with_state(
                                        current_pvp_info,
                                        current_pvp_player,
                                        current_pvp_bot,
                                        round_number=current_pvp_round,
                                        turn_number=current_pvp_turn_number,
                                        current_index=0,
                                        additional_gamers=(current_pvp_extra_bot,),
                                    )
                                    survivors = [
                                        idx for idx, (hp, frenzy) in enumerate(
                                            zip(hit_points, virtual_hit_points)
                                        ) if not _pvp_is_eliminated(hp, frenzy)
                                    ]
                                    if match_ended:
                                        winner = survivors[0]
                                        ranks = {winner: 1}
                                        for death_order, eliminated in enumerate(
                                            current_pvp_eliminated_order
                                        ):
                                            ranks[eliminated] = max(2, 3 - death_order)
                                        for gamer_index in range(3):
                                            gamers[gamer_index] = pvp_gamer_with_state(
                                                gamers[gamer_index],
                                                hp=hit_points[gamer_index],
                                                ammo_number=real_ammo[gamer_index],
                                                fake_ammo_number=fake_ammo[gamer_index],
                                                enhanced_ammo_number=current_pvp_damage_bonus[gamer_index],
                                                round_number=current_pvp_round,
                                                is_dead=_pvp_is_eliminated(
                                                    hit_points[gamer_index],
                                                    virtual_hit_points[gamer_index],
                                                ),
                                                virtual_hp=virtual_hit_points[gamer_index],
                                                rank=ranks.get(gamer_index, 2),
                                            )
                                        (
                                            current_pvp_player,
                                            current_pvp_bot,
                                            current_pvp_extra_bot,
                                        ) = gamers
                                        current_pvp_info = pvp_info_with_end(
                                            pvp_info_with_state(
                                                current_pvp_info,
                                                gamers[0],
                                                gamers[1],
                                                round_number=current_pvp_round,
                                                turn_number=current_pvp_turn_number,
                                                current_index=winner,
                                                status=4,
                                                additional_gamers=(gamers[2],),
                                            ),
                                            end_time=event_time + 3,
                                        )
                                        current_pvp_turn = -1
                                    use_result = pvp_hallucinogen_use_event_result_body(
                                        current_pvp_player,
                                        updated_target,
                                        slot,
                                        target_index=target_index,
                                        event_id=current_pvp_event_id,
                                        event_time=event_time,
                                        shot_result=shot_result,
                                    )
                                    post_frames.append(
                                        encode_frame(
                                            255,
                                            2,
                                            pvp_event_notification_body(
                                                use_result,
                                                current_pvp_info,
                                                server_time=event_time,
                                            ),
                                            error=0,
                                            index=0,
                                            length_mode=length_mode,
                                        )
                                    )
                                    if match_ended:
                                        delayed_frames.append(
                                            (
                                                2.5,
                                                encode_frame(
                                                    255,
                                                    5,
                                                    pvp_end_body(current_pvp_info),
                                                    error=0,
                                                    index=0,
                                                    length_mode=length_mode,
                                                ),
                                            )
                                        )
                                    LOG.info(
                                        "PVP hallucinogen used card=%d target=%d ammo=%d hp=%d->%d remainingAmmo=%d/%d ended=%s",
                                        card_id,
                                        target_index,
                                        ammo_cfg_id,
                                        parse_varint_field(old_target, 4) or 0,
                                        hit_points[target_index],
                                        real_ammo[target_index],
                                        fake_ammo[target_index],
                                        match_ended,
                                    )
                            elif (
                                slot_id > 0
                                and card_id == slot_id
                                and slot_cfg_id in LAB_CARD_SKILLS
                                and slot_cfg_id not in HALLUCINOGEN_SKILLS
                                and slot_cfg_id not in WET_CIGARETTE_SKILLS
                                and slot_cfg_id not in EJECT_AMMO_SKILLS
                                and slot_cfg_id not in (REAL_AMMO_CARD_CFG_ID,
                                                         FAKE_AMMO_CARD_CFG_ID,
                                                         SPARE_MAGAZINE_CARD_CFG_ID)
                                and current_pvp_extra_bot
                            ):
                                target_index = (
                                    int(requested_target)
                                    if requested_target in (0, 1, 2) else 0
                                )
                                gamers = [
                                    current_pvp_player, current_pvp_bot,
                                    current_pvp_extra_bot,
                                ]
                                hit_points = [
                                    current_pvp_player_hp, current_pvp_bot_hp,
                                    current_pvp_extra_bot_hp,
                                ]
                                virtual_hit_points = [
                                    current_pvp_player_virtual_hp,
                                    current_pvp_bot_virtual_hp,
                                    current_pvp_extra_bot_virtual_hp,
                                ]
                                real_ammo = [
                                    current_pvp_player_ammo, current_pvp_bot_ammo,
                                    current_pvp_extra_bot_ammo,
                                ]
                                fake_ammo = [
                                    current_pvp_player_fake_ammo,
                                    current_pvp_bot_fake_ammo,
                                    current_pvp_extra_bot_fake_ammo,
                                ]
                                if _pvp_is_eliminated(
                                    hit_points[target_index],
                                    current_pvp_virtual_hp_at(target_index),
                                ):
                                    response_error = 1
                                elif slot_cfg_id == 2032 and target_index == 0:
                                    response_error = 1
                                    LOG.info("PVP stored Rocket Launcher rejected self-target")
                                elif slot_cfg_id == 2032 and (
                                    current_pvp_player_ammo
                                    + current_pvp_player_fake_ammo
                                    + current_pvp_damage_bonus[0] <= 0
                                ):
                                    response_error = 1
                                    LOG.info("PVP stored Rocket Launcher rejected: source has no ammo")
                                elif (
                                    slot_cfg_id == 2015
                                    and current_pvp_maintenance_bonus[target_index]
                                ):
                                    # Keep the stored card when the target
                                    # already has the non-stackable effect.
                                    response_error = 352
                                    LOG.info(
                                        "PVP stored Maintenance Kit rejected: "
                                        "target=%d already has buff 1014",
                                        target_index,
                                    )
                                elif (
                                    slot_cfg_id == 2021
                                    and current_pvp_wanted_reward[target_index]
                                ):
                                    response_error = 352
                                    LOG.info(
                                        "PVP stored Wanted rejected: "
                                        "target=%d already has an active bounty",
                                        target_index,
                                    )
                                elif slot_cfg_id == 2018 and (
                                    target_index == 0
                                    or (parse_varint_field(gamers[target_index], 5) or 0) <= 0
                                ):
                                    response_error = 380 if target_index else 1
                                    LOG.info(
                                        "PVP stored Violation Ticket rejected: "
                                        "target=%d coin=%d",
                                        target_index,
                                        parse_varint_field(gamers[target_index], 5) or 0,
                                    )
                                else:
                                    event_type = 10
                                    hp_delta = 0
                                    luck_roll = None
                                    lucky_consumed = False
                                    stolen_coin = 0
                                    add_buff_cfg = (
                                        MAINTENANCE_KIT_BUFF_CFG_ID
                                        if slot_cfg_id == 2015 else
                                        BURST_MODE_BUFF_CFG_ID
                                        if slot_cfg_id == 2016 else ITEM_BUFF_CFG.get(slot_cfg_id, slot_cfg_id)
                                    )
                                    add_buff_cfgs = ()
                                    r_ammo = None
                                    c_ammo = None
                                    is_rpg_hit = None
                                    source_u_ammo = ()
                                    source_virtual_hp_delta = 0
                                    target_virtual_hp_delta = 0
                                    target_dead = False
                                    rocket_reload_ammo_after = None
                                    rocket_ghosts_added = 0
                                    rocket_blocked_katie = None
                                    new_slot = None
                                    skill_cd = None
                                    if slot_cfg_id == 2009:
                                        add_buff_cfg = None
                                        if real_ammo[target_index] <= 0:
                                            response_error = 1
                                            LOG.warning(
                                                "PVP stored Arms Voucher rejected: "
                                                "target=%d has no real ammo",
                                                target_index,
                                            )
                                        else:
                                            real_before = real_ammo[target_index]
                                            real_ammo[target_index] -= 1
                                            event_type = 8
                                            current_pvp_damage_bonus[target_index] += 1
                                            r_ammo = (
                                                pb_message(
                                                    pb_varint(1, 300),
                                                    pb_varint(2, fake_ammo[target_index]),
                                                    pb_varint(3, 1),
                                                ),
                                                pb_message(
                                                    pb_varint(1, 1),
                                                    pb_varint(2, real_ammo[target_index]),
                                                    pb_varint(3, 3),
                                                ),
                                                pb_message(
                                                    pb_varint(1, 2),
                                                    pb_varint(2, current_pvp_damage_bonus[target_index]),
                                                    pb_varint(3, 4),
                                                ),
                                            )
                                            c_ammo = _c_ammo_message(
                                                1, 1, 2, 1
                                            )
                                    elif slot_cfg_id == 2032:
                                        add_buff_cfg = None
                                        virtual_hp = [
                                            current_pvp_player_virtual_hp,
                                            current_pvp_bot_virtual_hp,
                                            current_pvp_extra_bot_virtual_hp,
                                        ]
                                        rocket = _pvp_resolve_rocket_shot(
                                            gamers, hit_points, virtual_hp,
                                            real_ammo, fake_ammo,
                                            current_pvp_damage_bonus,
                                            0, target_index,
                                            round_number=current_pvp_round,
                                            randomize_magazines=state.randomize_magazines,
                                            katie_guards=current_pvp_katie_guards,
                                        )
                                        if rocket is None:
                                            response_error = 1
                                        else:
                                            event_type = 39  # Enum_Rpg
                                            is_rpg_hit = rocket.ammo_cfg_id != 300
                                            rocket_ghosts_added = rocket.ghosts_added_real
                                            rocket_blocked_katie = rocket.blocked_katie_buff
                                            hp_delta = rocket.target_hp_delta
                                            target_virtual_hp_delta = (
                                                rocket.target_virtual_hp_delta
                                            )
                                            target_dead = rocket.target_dead
                                            source_virtual_hp_delta = (
                                                rocket.shooter_virtual_hp_delta
                                            )
                                            source_u_ammo = tuple(
                                                pb_message(
                                                    pb_varint(1, cfg_id),
                                                    pb_varint(2, number),
                                                    pb_varint(3, 1 if cfg_id == 300 else 3 if cfg_id == 1 else 4),
                                                )
                                                for cfg_id, number in rocket.consumed_ammo
                                            )
                                            rocket_reload_ammo_after = (
                                                rocket.reload_ammo_after
                                            )
                                            (
                                                current_pvp_player_virtual_hp,
                                                current_pvp_bot_virtual_hp,
                                                current_pvp_extra_bot_virtual_hp,
                                            ) = virtual_hp
                                            LOG.info(
                                                "PVP stored Rocket Launcher resolved target=%d "
                                                "ammoCfg=%d consumed=%s damage=%d "
                                                "targetHp=%d targetFrenzy=%d "
                                                "shooterFrenzyDelta=%d reload=%s dead=%s",
                                                target_index, rocket.ammo_cfg_id,
                                                rocket.consumed_ammo, rocket.damage,
                                                rocket.target_hp_delta,
                                                rocket.target_virtual_hp_delta,
                                                rocket.shooter_virtual_hp_delta,
                                                rocket.reload_ammo_after,
                                                rocket.target_dead,
                                            )
                                    elif slot_cfg_id == 2029:
                                        add_buff_cfg = None
                                        reduction = tranquilizer_frenzy_reduction(
                                            hit_points[target_index],
                                            virtual_hit_points[target_index],
                                        )
                                        virtual_hit_points[target_index] -= reduction
                                        target_virtual_hp_delta = -reduction
                                        event_type = 14  # Enum_Hp_Vir
                                        LOG.info(
                                            "PVP Tranquilizer used source=stored target=%d "
                                            "hp=%d frenzy=%d->%d removed=%d",
                                            target_index,
                                            hit_points[target_index],
                                            virtual_hit_points[target_index] + reduction,
                                            virtual_hit_points[target_index],
                                            reduction,
                                        )
                                    elif slot_cfg_id == 2031:
                                        add_buff_cfg = None
                                        event_type = 9  # Enum_Skill_Cd
                                        skill_cd = max(
                                            0, pvp_gamer_skill_cd(gamers[target_index]) - 1
                                        )
                                        gamers[target_index] = pvp_gamer_with_skill_cd(
                                            gamers[target_index], skill_cd,
                                        )
                                    elif slot_cfg_id == 2018:
                                        add_buff_cfg = None
                                        gamers[0], luck_roll, lucky_consumed = _pvp_roll_lucky_die(gamers[0], random.randint(1, 6))
                                        target_coin = (
                                            parse_varint_field(gamers[target_index], 5) or 0
                                        )
                                        stolen_coin = min(target_coin, luck_roll * 100)
                                        gamers[target_index] = pvp_gamer_with_coin_and_card(
                                            gamers[target_index],
                                            coin=target_coin - stolen_coin,
                                        )
                                        event_type = 7
                                    elif slot_cfg_id in (2020, 2028, 2036, 2037):
                                        add_buff_cfg = None
                                        reward_cfg, reward_price = random.choice(
                                            tuple(spec for spec in PVP_LAB_REWARD_SPECS
                                                  if spec[0] not in (2020, 2028, 2036, 2037))
                                        )
                                        LOG.info(
                                            "PVP stored Surprise Box reward source=%d reward=%d card=%d",
                                            slot_cfg_id, reward_cfg,
                                            current_pvp_shop_next_id,
                                        )
                                        new_slot = pvp_card_slot_body(
                                            pvp_shop_card(
                                                current_pvp_shop_next_id,
                                                reward_cfg, reward_price,
                                            )
                                        )
                                        current_pvp_shop_next_id += 1
                                    else:
                                        new_slot = None
                                        if slot_cfg_id == 2015:
                                            current_pvp_maintenance_bonus[target_index] = 1
                                        elif slot_cfg_id == 2016:
                                            current_pvp_burst_mode[target_index] += 1
                                        elif slot_cfg_id == 2033:
                                            current_pvp_bucket_guard[target_index] = True
                                        elif slot_cfg_id in (2022, 2030):
                                            add_buff_cfg = current_pvp_restrictions.apply_to_gamer(
                                                gamers, target_index, slot_cfg_id,
                                                source_index=0,
                                            )
                                        elif slot_cfg_id == 2021:
                                            add_buff_cfg = None
                                            add_buff_cfgs = (
                                                WANTED_PARENT_BUFF_CFG_ID,
                                                WANTED_REWARD_BUFF_CFG_ID,
                                            )
                                            wanted_duration = _pvp_apply_wanted(
                                                gamers, target_index,
                                                current_pvp_wanted_reward,
                                                current_pvp_wanted_expire_turn,
                                                current_pvp_wanted_turn_clock,
                                            )
                                            LOG.info(
                                                "PVP Wanted applied source=stored target=%d "
                                                "reward=%d round=%d turn_clock=%d "
                                                "duration=%d expires_turn_clock=%d",
                                                target_index,
                                                WANTED_REWARD_R_CHIPS,
                                                current_pvp_round,
                                                current_pvp_wanted_turn_clock,
                                                wanted_duration,
                                                current_pvp_wanted_expire_turn[
                                                    target_index
                                                ],
                                            )
                                    gamers[target_index] = pvp_gamer_with_state(
                                        gamers[target_index],
                                        hp=hit_points[target_index],
                                        ammo_number=real_ammo[target_index],
                                        fake_ammo_number=fake_ammo[target_index],
                                        enhanced_ammo_number=(
                                            current_pvp_damage_bonus[target_index]
                                        ),
                                        round_number=current_pvp_round,
                                        virtual_hp=virtual_hit_points[target_index],
                                        burst_mode_active=bool(
                                            current_pvp_burst_mode[target_index]
                                        ),
                                        maintenance_kit_active=bool(
                                            current_pvp_maintenance_bonus[target_index]
                                        ),
                                    )
                                    current_pvp_player = pvp_gamer_with_coin_and_card(
                                        gamers[0], coin=current_coin + stolen_coin,
                                        card_slot=new_slot or pvp_empty_card_slot_body(),
                                    )
                                    gamers[0] = current_pvp_player
                                    (
                                        current_pvp_player, current_pvp_bot,
                                        current_pvp_extra_bot,
                                    ) = gamers
                                    (
                                        current_pvp_player_hp, current_pvp_bot_hp,
                                        current_pvp_extra_bot_hp,
                                    ) = hit_points
                                    (
                                        current_pvp_player_ammo, current_pvp_bot_ammo,
                                        current_pvp_extra_bot_ammo,
                                    ) = real_ammo
                                    (
                                        current_pvp_player_fake_ammo,
                                        current_pvp_bot_fake_ammo,
                                        current_pvp_extra_bot_fake_ammo,
                                    ) = fake_ammo
                                    (
                                        current_pvp_player_virtual_hp,
                                        current_pvp_bot_virtual_hp,
                                        current_pvp_extra_bot_virtual_hp,
                                    ) = virtual_hit_points
                                    current_pvp_info = pvp_info_with_state(
                                        current_pvp_info,
                                        current_pvp_player,
                                        current_pvp_bot,
                                        round_number=current_pvp_round,
                                        turn_number=current_pvp_turn_number,
                                        current_index=0,
                                        additional_gamers=(current_pvp_extra_bot,),
                                    )
                                    current_pvp_event_id += 1
                                    result = pvp_generic_card_event_result_body(
                                        current_pvp_player,
                                        gamers[target_index],
                                        slot,
                                        skill_id=LAB_CARD_SKILLS[slot_cfg_id],
                                        target_index=target_index,
                                        event_id=current_pvp_event_id,
                                        event_type=event_type,
                                        hp_delta=hp_delta,
                                        virtual_hp_delta=target_virtual_hp_delta,
                                        clear_slot=True,
                                        new_card_slot=new_slot,
                                        r_ammo=r_ammo,
                                        c_ammo=c_ammo,
                                        skill_cd=skill_cd,
                                        add_buff_cfg=add_buff_cfg,
                                        add_buff_cfgs=add_buff_cfgs,
                                        luck_roll=luck_roll,
                                        luck_success=luck_roll is not None,
                                        stolen_coin=stolen_coin,
                                        is_rpg_hit=is_rpg_hit,
                                        source_u_ammo=source_u_ammo,
                                        source_virtual_hp_delta=source_virtual_hp_delta,
                                        target_dead=target_dead,
                                        reload_ammo_after=rocket_reload_ammo_after,
                                        ghosts_added_real=rocket_ghosts_added,
                                        target_del_buff_cfgs=(rocket_blocked_katie,) if rocket_blocked_katie else (),
                                        event_time=event_time,
                                    )
                                    result = pvp_event_with_consumed_lucky(result, 0, consumed=lucky_consumed,
                                        event_id=current_pvp_event_id, event_time=server_time)
                                    post_frames.append(encode_frame(
                                        255, 2,
                                        pvp_event_notification_body(
                                            result, current_pvp_info,
                                            server_time=event_time,
                                        ), error=0, index=0,
                                        length_mode=length_mode,
                                    ))
                                    LOG.info(
                                        "PVP stored generic use cfg=%d skill=%d target=%d hpDelta=%d "
                                        "targetAmmo=%d/%d enhanced=%d die=%s stolen=%d",
                                        slot_cfg_id, LAB_CARD_SKILLS[slot_cfg_id],
                                        target_index, hp_delta,
                                        real_ammo[target_index],
                                        fake_ammo[target_index],
                                        current_pvp_damage_bonus[target_index],
                                        luck_roll, stolen_coin,
                                    )
                            else:
                                response_error = 1
                                if slot_cfg_id in PIGGYBANK_COINS_PER_TURN:
                                    LOG.warning(
                                        "PVP piggybank use rejected id=%d slot=%d cfg=%d "
                                        "amount=%d target=%r",
                                        card_id,
                                        slot_id,
                                        slot_cfg_id,
                                        stored_coins,
                                        requested_target,
                                    )
                                else:
                                    LOG.warning(
                                        "PVP unsupported card use rejected id=%d slot=%d "
                                        "cfg=%d target=%r",
                                        card_id,
                                        slot_id,
                                        slot_cfg_id,
                                        requested_target,
                                    )
                        elif current_pvp_extra_bot and action_type == 3:
                            old_slot_cfg_id = parse_varint_field(slot, 2) or 0
                            can_replace_slot = slot_id == 0 or (
                                slot_id > 0
                                and old_slot_cfg_id not in PIGGYBANK_COINS_PER_TURN
                            )
                            offer = next(
                                (
                                    card for card in shop_cards
                                    if (parse_varint_field(card, 1) or 0) == card_id
                                ),
                                None,
                            )
                            offer_status = (
                                parse_varint_field(offer, 5) or 0
                                if offer is not None else 0
                            )
                            price = (
                                parse_varint_field(offer, 3) or 0
                                if offer is not None else 0
                            )
                            if (
                                offer is not None
                                and offer_status == 1
                                and price > 0
                                and current_coin >= price
                                and can_replace_slot
                            ):
                                current_pvp_event_id += 1
                                current_pvp_player = pvp_gamer_with_coin_and_card(
                                    current_pvp_player,
                                    coin=current_coin - price,
                                    card_slot=pvp_card_slot_body(offer),
                                )
                                updated_shop = tuple(
                                    pvp_shop_card(
                                        parse_varint_field(card, 1) or 0,
                                        parse_varint_field(card, 2) or 0,
                                        parse_varint_field(card, 3) or 0,
                                        parse_varint_field(card, 4) or 1,
                                        2 if (parse_varint_field(card, 1) or 0) == card_id else 1,
                                    )
                                    for card in shop_cards
                                )
                                current_pvp_info = pvp_info_with_state(
                                    current_pvp_info,
                                    current_pvp_player,
                                    current_pvp_bot,
                                    round_number=current_pvp_round,
                                    turn_number=current_pvp_turn_number,
                                    current_index=0,
                                    additional_gamers=(current_pvp_extra_bot,),
                                )
                                current_pvp_info = pvp_info_with_shop(
                                    current_pvp_info,
                                    updated_shop,
                                    parse_varint_field(current_pvp_info, 41) or 0,
                                )
                                result = pvp_buy_card_event_result_body(
                                    current_pvp_player,
                                    offer,
                                    coin_delta=-price,
                                    event_id=current_pvp_event_id,
                                    event_time=event_time,
                                )
                                post_frames.append(
                                    encode_frame(
                                        255,
                                        2,
                                        pvp_event_notification_body(
                                            result,
                                            current_pvp_info,
                                            server_time=event_time,
                                        ),
                                        error=0,
                                        index=0,
                                        length_mode=length_mode,
                                    )
                                )
                                LOG.info(
                                    "PVP stored card id=%d cfg=%d price=%d coin=%d->%d replacedSlot=%d/%d",
                                    card_id,
                                    parse_varint_field(offer, 2) or 0,
                                    price,
                                    current_coin,
                                    current_coin - price,
                                    slot_id,
                                    old_slot_cfg_id,
                                )
                            else:
                                response_error = 1
                                LOG.warning(
                                    "PVP stored-card request rejected id=%d status=%d "
                                    "price=%d coin=%d slot=%d",
                                    card_id,
                                    offer_status,
                                    price,
                                    current_coin,
                                    slot_id,
                                )
                        elif current_pvp_extra_bot and action_type == 4 and card_id == 10_000:
                            refresh_price = parse_varint_field(current_pvp_info, 41) or 0
                            if refresh_price > 0 and current_coin >= refresh_price:
                                specs = _random_shop_specs(shop_cards)
                                refreshed_cards = tuple(
                                    pvp_shop_card(
                                        current_pvp_shop_next_id + offset,
                                        *specs[offset],
                                    )
                                    for offset in range(4)
                                )
                                current_pvp_shop_next_id += len(refreshed_cards)
                                current_pvp_shop_refreshes += 1
                                current_pvp_player = pvp_gamer_with_coin_and_card(
                                    current_pvp_player,
                                    coin=current_coin - refresh_price,
                                    card_slot=slot if slot_id > 0 else None,
                                )
                                current_pvp_info = pvp_info_with_state(
                                    current_pvp_info,
                                    current_pvp_player,
                                    current_pvp_bot,
                                    round_number=current_pvp_round,
                                    turn_number=current_pvp_turn_number,
                                    current_index=0,
                                    additional_gamers=(current_pvp_extra_bot,),
                                )
                                current_pvp_info = pvp_info_with_shop(
                                    current_pvp_info,
                                    refreshed_cards,
                                    refresh_price,
                                )
                                current_pvp_event_id += 1
                                result = pvp_refresh_shop_event_result_body(
                                    current_pvp_player,
                                    refreshed_cards,
                                    coin_delta=-refresh_price,
                                    event_id=current_pvp_event_id,
                                    event_time=event_time,
                                )
                                post_frames.append(
                                    encode_frame(
                                        255,
                                        2,
                                        pvp_event_notification_body(
                                            result,
                                            current_pvp_info,
                                            server_time=event_time,
                                        ),
                                        error=0,
                                        index=0,
                                        length_mode=length_mode,
                                    )
                                )
                                LOG.info(
                                    "PVP shop refreshed generation=%d price=%d coin=%d->%d "
                                    "offers=%d cfg=%s ids=%s",
                                    current_pvp_shop_refreshes,
                                    refresh_price,
                                    current_coin,
                                    current_coin - refresh_price,
                                    len(refreshed_cards),
                                    [parse_varint_field(card, 2) or 0
                                     for card in refreshed_cards],
                                    [parse_varint_field(card, 1) or 0
                                     for card in refreshed_cards],
                                )
                            else:
                                response_error = 1
                                LOG.warning(
                                    "PVP shop refresh rejected price=%d coin=%d",
                                    refresh_price,
                                    current_coin,
                                )
                        else:
                            response_error = 1
                            LOG.warning(
                                "PVP card action not yet reconstructed type=%d id=%d",
                                action_type,
                                card_id,
                            )
                    else:
                        response_error = 1
                        LOG.warning(
                            "PVP card action rejected: no active player turn or "
                            "match state unavailable type=%d id=%d",
                            action_type,
                            card_id,
                        )
                elif (head.cmd, head.act) == (3, 11):
                    out_body = pvp_info_body(
                        published_pvp_info,
                        current_time=server_time,
                    )
                elif (head.cmd, head.act) == (3, 19):
                    # The client requests a single gamer snapshot after an
                    # action.  An empty ack leaves its post-shot refresh
                    # pending and is the source of the recurring 3/19 timeout.
                    requested_index = parse_varint_field(body, 2) or 0
                    visible_gamers = parse_bytes_fields(published_pvp_info, 2)
                    gamer = (
                        visible_gamers[requested_index]
                        if 0 <= requested_index < len(visible_gamers)
                        else b""
                    )
                    out_body = pvp_gamer_info_body(
                        account.gid,
                        gamer,
                        current_time=server_time,
                    )
                elif (head.cmd, head.act) == (3, 21):
                    out_body = pvp_skip_tv_body(account.gid)
                elif (head.cmd, head.act) == (3, 13):
                    # Surrender is also used by the client when leaving the
                    # battle scene.  An empty ack makes the Lua callback call
                    # SetPvpInfo(nil), which produces the observed
                    # pvp_mode_cfg id:nil error.
                    out_body = pvp_surrender_body(account.gid, published_pvp_info)
                elif (head.cmd, head.act) == (3, 29):
                    out_body = pvp_observer_count_body(account.gid)
                elif (head.cmd, head.act) == (3, 33):
                    out_body = pvp_bet_simple_body(account.gid)
                elif (head.cmd, head.act) == (3, 10):
                    out_body = b"\x08" + _varint(account.gid)
                elif (head.cmd, head.act) == (3, 2):
                    out_body = b"\x08" + _varint(account.gid)

            response_frame = encode_frame(
                head.cmd,
                head.act,
                out_body,
                error=response_error,
                index=head.index,
                length_mode=length_mode,
            )
            trace_frame(
                service,
                "S->C",
                response_frame,
                length_mode,
                "response",
                state_snapshot(),
            )
            writer.write(response_frame)
            await writer.drain()
            for frame in post_frames:
                writer.write(frame)
                publish_pvp_frame(frame)
                trace_frame(
                    service,
                    "S->C",
                    frame,
                    length_mode,
                    "post",
                    state_snapshot(),
                )
            if post_frames:
                await writer.drain()
            if delayed_frames:
                task = asyncio.create_task(send_delayed_frames(delayed_frames))
                delayed_tasks.add(task)
                task.add_done_callback(delayed_tasks.discard)
    except (asyncio.IncompleteReadError, ConnectionError):
        pass
    except Exception:
        LOG.exception("%s protocol error from %s", service, peer)
    finally:
        for task in delayed_tasks:
            task.cancel()
        if delayed_tasks:
            await asyncio.gather(*delayed_tasks, return_exceptions=True)
        writer.close()
        try:
            await writer.wait_closed()
        except (ConnectionError, OSError):
            pass  # Windows can report a peer reset again during close.
        LOG.info("%s disconnected: %s", service, peer[0] if peer else "unknown")


def _varint(value: int) -> bytes:
    out = bytearray()
    while value > 0x7F:
        out.append((value & 0x7F) | 0x80)
        value >>= 7
    out.append(value)
    return bytes(out)


def run_http(host: str, port: int, state: GameState) -> None:
    handler = type("BoundApiHandler", (ApiHandler,), {"state": state})
    server = ThreadingHTTPServer((host, port), handler)
    LOG.info("HTTP API listening on %s:%d", host, port)
    try:
        server.serve_forever()
    finally:
        server.server_close()


async def async_main(args: argparse.Namespace) -> None:
    trace_path = Path(args.trace_file).resolve()
    trace_path.parent.mkdir(parents=True, exist_ok=True)
    TRACE.handlers.clear()
    trace_handler = logging.FileHandler(trace_path, mode="w", encoding="utf-8")
    trace_handler.setFormatter(logging.Formatter("%(message)s"))
    TRACE.addHandler(trace_handler)
    TRACE.setLevel(logging.INFO)
    TRACE.propagate = False
    TRACE.info(
        json.dumps(
            {
                "event": "trace-start",
                "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
                "length_mode": args.length_mode,
                "scope": "localhost-only; may contain local client identifiers",
            },
            separators=(",", ":"),
            sort_keys=True,
        )
    )
    state = GameState(
        args.pvp_port,
        Path(args.inventory).resolve(),
        Path(args.pkg_version).resolve(),
    )
    state.randomize_magazines = True
    state.bot_difficulty = args.bot_difficulty
    state.bot_seed = args.bot_seed
    LOG.info("Bot policy difficulty=%s seed=%r", state.bot_difficulty, state.bot_seed)
    http_thread = threading.Thread(
        target=run_http,
        args=(args.host, args.http_port, state),
        daemon=True,
        name="hunter-http",
    )
    http_thread.start()

    logic = await asyncio.start_server(
        lambda r, w: serve_client(
            r, w, state, args.length_mode, "logic",
            show_player_coin=not args.diagnostic_hide_player_coin,
        ),
        args.host,
        args.logic_port,
    )
    pvp = await asyncio.start_server(
        lambda r, w: serve_client(
            r, w, state, args.length_mode, "pvp",
            show_player_coin=not args.diagnostic_hide_player_coin,
        ),
        args.host,
        args.pvp_port,
    )
    LOG.info("Logic TCP listening on %s:%d", args.host, args.logic_port)
    LOG.info("PVP TCP listening on %s:%d", args.host, args.pvp_port)
    LOG.info("No original endpoints, Steam tokens, or external services are contacted")
    async with logic, pvp:
        await asyncio.gather(logic.serve_forever(), pvp.serve_forever())


def main() -> None:
    parser = argparse.ArgumentParser(description="Hunter Roulette local private-server prototype")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--http-port", type=int, default=38000)
    parser.add_argument("--logic-port", type=int, default=38001)
    parser.add_argument("--pvp-port", type=int, default=38002)
    parser.add_argument("--length-mode", choices=("total", "body"), default="body")
    parser.add_argument("--inventory", default="inventory.json")
    parser.add_argument(
        "--pkg-version",
        default="../../Game/Client_Data/StreamingAssets/PkgVersion.json",
    )
    parser.add_argument("--trace-file", default="packet-trace.jsonl")
    parser.add_argument("--bot-difficulty", choices=("scripted", "easy", "medium", "hard"), default="medium")
    parser.add_argument("--bot-seed", type=int, default=None,
                        help="seed bot choices/dice for diagnostics; not bullets")
    parser.add_argument(
        "--diagnostic-hide-player-coin",
        action="store_true",
        help="omit only PvpInfo.isShowPlayerCoin for a local visual A/B test",
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    try:
        asyncio.run(async_main(args))
    except KeyboardInterrupt:
        LOG.info("Stopped")


if __name__ == "__main__":
    main()
