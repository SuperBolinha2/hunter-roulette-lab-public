import asyncio
import sys
import tempfile
import threading
import time
from pathlib import Path
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1]))
from weapon_skills import apply_reload_trait, weapon_skill_id, SCREWDRIVER_GUN_IDS
from bot_ai import Fighter
from protocol import (
    _local_pvp_gamer, pvp_gamer_with_state, pvp_gamer_enhanced_count,
    pvp_spare_magazine_event_result_body, pvp_shoot_event_result_body,
    pvp_eject_ammo_card_event_result_body, pvp_shop_card,
    parse_bytes_field, parse_bytes_fields, parse_varint_field,
    encode_frame, pb_bytes, pb_varint, season_state,
)
from server import (
    _reload_weapon_ammo, _draw_loaded_ammo, _resolve_hallucinogen_self_shot,
    GameState, read_frame, serve_client,
)


def gamer(gun=1, index=0, reloaded=True):
    g = _local_pvp_gamer(123 + index, 'weapon-test', 1, 2, 201,
                            gun, 2, 10201, index, bool(index),
                            real_ammo_count=2, fake_ammo_count=2)
    magazine = apply_reload_trait(gun, 2, 2)
    return pvp_gamer_with_state(g, hp=4, ammo_number=magazine.real,
        fake_ammo_number=magazine.blank, enhanced_ammo_number=magazine.enhanced,
        round_number=1, weapon_reloaded=True) if reloaded else g


def counts(message, field):
    return {parse_varint_field(a, 1): parse_varint_field(a, 2)
            for a in parse_bytes_fields(message, field)}


class ScrewdriverTests(unittest.TestCase):
    def test_all_verified_ids_upgrade_without_changing_capacity(self):
        for gun in SCREWDRIVER_GUN_IDS:
            for live in (1, 2):
                with self.subTest(gun=gun, live=live):
                    m = apply_reload_trait(gun, live, 4-live)
                    self.assertEqual((m.real, m.blank, m.enhanced), (live-1,4-live,1))
                    self.assertEqual(m.real+m.blank+m.enhanced,4)
                    self.assertEqual(weapon_skill_id(gun),2)

    def test_other_guns_and_tutorial_have_no_accidental_trait(self):
        for gun in (0,3,7,11,21,22):
            m = apply_reload_trait(gun,2,2)
            self.assertEqual((m.real,m.blank,m.enhanced),(2,2,0))

    def test_zero_live_does_not_manufacture_bullet(self):
        self.assertEqual(apply_reload_trait(1,0,4).enhanced,0)
        with self.assertRaises(ValueError): apply_reload_trait(1,-1,4)

    def test_bot_probability_counts_red_as_live_not_guaranteed(self):
        self.assertEqual(Fighter(0,4,0,1,2,enhanced=1).live_probability,0.5)
        self.assertEqual(Fighter(0,4,0,0,3,enhanced=1).live_probability,0.25)

    def test_initial_snapshot_has_trait_definition_but_no_red_bullet(self):
        gun = parse_bytes_field(gamer(reloaded=False),7)
        self.assertEqual(parse_varint_field(gun,4),2)
        self.assertEqual(counts(gun,2),{300:2,1:2})

    def test_opening_load_has_no_red_for_any_family_member(self):
        for gun in SCREWDRIVER_GUN_IDS:
            for index in (0, 1, 2):
                self.assertEqual(pvp_gamer_enhanced_count(gamer(gun,index,reloaded=False)),0)

    def test_reload_replaces_not_accumulates_previous_red_rounds(self):
        red=[4,0]
        self.assertEqual(_reload_weapon_ammo(1,red,0),(1,2))
        self.assertEqual(red,[1,0])

    def test_random_minimum_live_still_has_one_shootable_red_round(self):
        red=[0]
        with patch('protocol.random.randint',return_value=1):
            self.assertEqual(_reload_weapon_ammo(1,red,0,randomize=True),(0,3))
        self.assertEqual(red,[1])
        with patch('server.random.randrange',return_value=3):
            self.assertEqual(_draw_loaded_ammo(0,3,1),2)

    def test_draw_includes_all_types_without_seeing_future_outcome(self):
        for roll,wanted in ((0,300),(1,300),(2,1),(3,2)):
            with patch('server.random.randrange',return_value=roll):
                self.assertEqual(_draw_loaded_ammo(1,2,1),wanted)

    def test_spare_magazine_publishes_red_and_gun_activation(self):
        g=gamer()
        packet=pvp_spare_magazine_event_result_body(g,g,pvp_shop_card(5,2007,200),
            target_index=0,old_real=1,old_fake=2,real_after=1,fake_after=2,event_id=1)
        outline=parse_bytes_field(parse_bytes_fields(packet,4)[-1],2)
        self.assertEqual(counts(outline,5),{300:2,1:1,2:1})
        self.assertEqual(parse_varint_field(outline,50),1)

    def test_shoot_preserves_red_when_a_different_round_is_consumed(self):
        packet=pvp_shoot_event_result_body(gamer(),gamer(index=1),0,1,
            ammo_cfg_id=300,target_hp_delta=0,source_ammo_after=1,source_fake_ammo_after=1)
        outline=parse_bytes_field(parse_bytes_fields(packet,4)[0],1)
        self.assertEqual(counts(outline,5),{300:1,1:1,2:1})

    def test_natural_reload_red_round_appears_only_in_reload_not_shot(self):
        packet=pvp_shoot_event_result_body(gamer(),gamer(index=1),0,1,
            ammo_cfg_id=2,target_hp_delta=-2,source_ammo_after=0,
            source_fake_ammo_after=2,reload_ammo_after=(1,2))
        events=parse_bytes_fields(packet,4)
        shot=parse_bytes_field(events[0],1)
        reload=parse_bytes_field(events[1],2)
        self.assertNotIn(2,counts(shot,5))
        self.assertEqual(counts(reload,5),{300:2,1:1,2:1})
        self.assertEqual(parse_varint_field(reload,50),1)

    def test_ejector_reload_publishes_full_new_magazine(self):
        g=gamer()
        packet=pvp_eject_ammo_card_event_result_body(g,g,pvp_shop_card(2,2001,100),
            target_index=0,ejected_ammo_cfg_id=2,event_id=1,reload_ammo_after=(1,2))
        outline=parse_bytes_field(parse_bytes_fields(packet,4)[-1],2)
        self.assertEqual(counts(outline,5),{300:2,1:1,2:1})

    def test_forced_shot_does_not_reload_while_red_round_remains(self):
        gs=[gamer(),gamer(gun=0,index=1)]
        hp=[4,4]; real=[1,2]; blank=[2,2]; red=[1,0]
        with patch('server.random.randrange',return_value=2):
            result=_resolve_hallucinogen_self_shot(gs,hp,[0,0],real,blank,[0,0],0,
                round_number=1,event_id=1,event_time=1,enhanced_ammo=red)
        self.assertEqual(result[1],1)
        self.assertEqual((real[0],blank[0],red[0]),(0,2,1))
        self.assertEqual(hp[0],3)

    def test_forced_red_shot_deals_two_and_reloads_with_trait(self):
        gs=[gamer(),gamer(gun=0,index=1)]
        hp=[4,4];real=[1,2];blank=[2,2];red=[1,0]
        # Consume the ordinary live round first, then the enhanced round.
        real[0]=0
        with patch('server.random.randrange',return_value=2):
            result=_resolve_hallucinogen_self_shot(gs,hp,[0,0],real,blank,[0,0],0,
                round_number=1,event_id=1,event_time=1,enhanced_ammo=red)
        self.assertEqual(result[1],2)
        self.assertEqual(hp[0],2)
        self.assertEqual((real[0],blank[0],red[0]),(1,2,1))
        self.assertEqual(pvp_gamer_enhanced_count(gs[0]),1)

    def test_live_server_reload_item_interactions_and_normal_red_damage(self):
        """Real TCP handlers, real trait enabled, isolated temporary inventory."""
        state = GameState.__new__(GameState)
        state._lock = threading.Lock()
        state.inventory = {'selectedHero': 1, 'heroGuns': [{'heroId': 1, 'gunId': 1}]}
        state.randomize_magazines = False
        state._clock_epoch = season_state(state.inventory)['serverTime']
        state._clock_monotonic = time.monotonic()
        state._accounts = {}
        state._next_gid = 1000001
        state.pvp_port = 0
        handle = tempfile.NamedTemporaryFile(suffix='.json', delete=False)
        handle.close()
        state.inventory_path = Path(handle.name)
        self.addCleanup(lambda: state.inventory_path.unlink(missing_ok=True))

        async def exchange(stored=False):
            listener = await asyncio.start_server(
                lambda r, w: serve_client(r, w, state, 'body', 'pvp'), '127.0.0.1', 0)
            writer = None
            try:
                reader, writer = await asyncio.open_connection(
                    '127.0.0.1', listener.sockets[0].getsockname()[1])

                async def receive(cmd, act, index=0):
                    async with asyncio.timeout(4):
                        while True:
                            head, body, _ = await read_frame(reader, 'body')
                            if (head.cmd, head.act, head.index) == (cmd, act, index):
                                return head, body

                def request(act, body, index):
                    writer.write(encode_frame(3, act, body, index=index, length_mode='body'))

                async def use(card, target, index):
                    if stored:
                        request(5, pb_varint(1, card) + pb_varint(4, 3), index + 100)
                        ack, _ = await receive(3, 5, index + 100)
                        self.assertEqual(ack.error, 0)
                        await receive(255, 2)
                    request(5, pb_varint(1, card) + pb_varint(2, target) + pb_varint(4, 2 if stored else 1), index)
                    ack, _ = await receive(3, 5, index)
                    self.assertEqual(ack.error, 0)
                    _, packet = await receive(255, 2)
                    result = parse_bytes_field(packet, 1)
                    gamers = parse_bytes_fields(parse_bytes_field(packet, 2), 2)
                    return result, gamers

                request(1, pb_bytes(2, 'local-pvp:1:6:1:0'), 701)
                _, login = await receive(3, 1, 701)
                initial = parse_bytes_fields(parse_bytes_field(login, 2), 2)[0]
                self.assertEqual(counts(parse_bytes_field(initial, 7), 2), {300:2, 1:2})
                request(14, b'', 702)
                await receive(3, 14, 702)
                await receive(255, 1)

                result, gamers = await use(1, 0, 703)  # Spare Magazine
                outline = parse_bytes_field(parse_bytes_fields(result, 4)[-1], 2)
                self.assertEqual(parse_varint_field(outline, 50), 1)
                self.assertEqual(counts(outline, 5), {300:2, 1:1, 2:1})
                self.assertEqual(counts(parse_bytes_field(gamers[0], 7), 2), {300:2, 1:1, 2:1})

                result, gamers = await use(2, 0, 704)  # Voucher stacks with trait.
                self.assertEqual(counts(parse_bytes_field(gamers[0], 7), 2), {300:2, 1:0, 2:2})
                ammo_outline = parse_bytes_field(parse_bytes_fields(result, 4)[-1], 2)
                self.assertEqual(counts(ammo_outline, 5), {300:2, 1:0, 2:2})

                # Free a slot first: add-round items must not exceed capacity.
                with patch('server.random.randrange', return_value=3):
                    _, gamers = await use(4, 0, 706)  # Hallucinogen consumes ONE red.
                self.assertEqual(parse_varint_field(gamers[0], 4), 2)
                self.assertEqual(counts(parse_bytes_field(gamers[0], 7), 2), {300:2, 1:0, 2:1})

                result, gamers = await use(3, 0, 705)  # Add Real preserves red.
                ammo_outline = parse_bytes_field(parse_bytes_fields(result, 4)[-1], 2)
                self.assertEqual(counts(ammo_outline, 5), {300:2, 1:1, 2:1})
                self.assertEqual(counts(parse_bytes_field(gamers[0], 7), 2), {300:2, 1:1, 2:1})

                with patch('server._draw_loaded_ammo', return_value=2):
                    request(3, pb_varint(1, 2), 707)
                    ack, _ = await receive(3, 3, 707)
                    self.assertEqual(ack.error, 0)
                    _, packet = await receive(255, 2)
                result = parse_bytes_field(packet, 1)
                self.assertEqual(parse_varint_field(result, 1), 1)
                target = parse_bytes_field(parse_bytes_fields(result, 4)[0], 2)
                self.assertEqual(parse_varint_field(target, 2), (-2) & ((1 << 64) - 1))
                source = parse_bytes_field(result, 12)
                self.assertEqual(counts(parse_bytes_field(source, 7), 2), {300:2, 1:1})
            finally:
                if writer is not None:
                    writer.close()
                    await writer.wait_closed()
                listener.close()
                await listener.wait_closed()

        with (
            patch('server.PVP_OPENING_SEQUENCE_DELAY', 0.001),
            patch('server._random_shop_specs', return_value=((2007,200), (2009,200), (2003,200), (2008,200))),
            patch('server.PREPARE_SIGNAL_DELAY', 0.001),
            patch('server.PLAYER_OTHER_SHOT_SETTLE', 0.006),
            patch('server.BOT_THINK_DELAY', 0.005),
            patch('server.BOT_RAISE_GUN_DELAY', 0.001),
            patch('server.BOT_SELECT_TARGET_DELAY', 0.001),
        ):
            for stored in (False, True):
                with self.subTest(stored=stored):
                    asyncio.run(exchange(stored))


if __name__=='__main__': unittest.main()
