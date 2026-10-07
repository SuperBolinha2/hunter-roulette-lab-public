"""Small, dependency-free implementation of the AntNet frame envelope.

The game client exposes this structure in its IL2CPP metadata:
uint len, ushort error, byte cmd, byte act, ushort index, ushort flags.

The length mode is configurable for testing, but the client-side AntNet
implementation stores the protobuf/body byte count in ``MessageHead.len``.
The default therefore uses the body length; the 12-byte header is not counted.
"""

from __future__ import annotations

from hero_skills import effective_hero_skill

from dataclasses import dataclass
import random
import struct
from weapon_skills import (
    weapon_skill_id, LITTLE_MANIAC_SKILL_ID,
    LUCKY_STREAK_BUFF_ID, lucky_die_result,
    LOVESONG_SKILL_ID,
    ARTEMIS_SKILL_ID,
    GRAZIER_SKILL_ID,
    GHOSTS_SKILL_ID, GHOSTS_BUFF_ID,
    TOXIN_BUFF_ID,
)


HEADER_SIZE = 12
MAX_FRAME_SIZE = 64 * 1024 * 1024

# The bundled client only contains historical season tables.  The real clock
# is already outside those ranges, so the lab deliberately presents one
# coherent, valid season on every login/request.  Keeping this in one place
# prevents the client from alternating between "get info" and "open season".
LAB_SEASON_ID = 18
LAB_LAST_SEASON_ID = 17
LAB_SEASON_CUP = 1
LAB_SEASON_MMR = 0
LAB_SERVER_TIME = 1_778_000_000
LAB_SEASON_START = 1_777_788_000
LAB_SEASON_END = 1_779_249_599

# CardCfgSteam 34 and its difficulty variants use hold_skill_id=1027. The
# bundled BuffCfgSteam rows show a turn-start tick of 2/20/200 stored coins.
PIGGYBANK_COINS_PER_TURN = {34: 2, 1034: 20, 2034: 200}
PIGGYBANK_USE_SKILL_ID = 1028
PIGGYBANK_EVENT_COIN_REASON = 21  # Coin_By_Card_Coin
CARD_EVENT_USE_REASON = 2  # Card_Reason_Use
PIGGYBANK_EVENT_UPDATE_REASON = 4  # Card_Reason_Update_Card_Money
WANTED_PARENT_BUFF_CFG_ID = 1020
WANTED_REWARD_BUFF_CFG_ID = 5002
WANTED_REWARD_R_CHIPS = 4
WANTED_COIN_REASON = 7  # Coin_By_Offer_Award
HALLUCINOGEN_CARD_CFG_ID = 2008
HALLUCINOGEN_USE_SKILL_ID = 1007
HALLUCINOGEN_SKILLS = {2008: 1007, 2025: 1023}
REAL_AMMO_CARD_CFG_ID = 2003
REAL_AMMO_CARD_SKILL_ID = 1002
FAKE_AMMO_CARD_CFG_ID = 2004
FAKE_AMMO_CARD_SKILL_ID = 1003
EJECT_AMMO_CARD_CFG_ID = 2001
EJECT_AMMO_CARD_SKILL_ID = 1000
EJECT_AMMO_SKILLS = {2001: 1000, 2026: 1024}
SPARE_MAGAZINE_CARD_CFG_ID = 2007
SPARE_MAGAZINE_SKILL_ID = 1006
WET_CIGARETTE_SKILLS = {2011: 1010, 2024: 1022, 2027: 1025}
BURST_MODE_BUFF_CFG_ID = 1015
MAINTENANCE_KIT_BUFF_CFG_ID = 1014
PVP_UPDATE_GAMER_DEAD_STATUS_EVENT = 76

# gun_cfg (not gun_cfg_steam) in the copied fight_dbconfig.ab: fields
# 1=id, 6=ammo_num and 7=reload_max_real. The client reads ammo_num to
# create exactly that many HUD bullet positions. The original server's
# per-round probability distribution is unavailable, so the lab fills each
# magazine deterministically with reload_max_real real rounds and the rest
# blank. This respects both shipped bounds without claiming original odds.
GUN_AMMO_SPECS = (
    (6, 3), (4, 2), (6, 3), (4, 2), (6, 3), (4, 2),
    (7, 3), (5, 2), (6, 3), (4, 2), (6, 3), (4, 2),
    (5, 2), (6, 3), (4, 2), (6, 3), (4, 2), (7, 3),
    (5, 2), (6, 3), (4, 2), (6, 3), (4, 2), (6, 3),
    (4, 2), (6, 3), (6, 3), (4, 2), (6, 3), (4, 2),
    (7, 3), (5, 2), (7, 3), (6, 3), (6, 3), (5, 2),
    (6, 0), (6, 0), (7, 3), (6, 3), (6, 3), (4, 2),
)


def pvp_gamer_has_ammo_space(gamer: bytes, real: int, blank: int, enhanced: int = 0) -> bool:
    """Add-round items cannot exceed the weapon's configured capacity."""
    gun = parse_bytes_field(gamer, 7) or b""
    gun_id = parse_varint_field(gun, 1) or 0
    return (0 <= gun_id < len(GUN_AMMO_SPECS)
            and real + blank + enhanced < GUN_AMMO_SPECS[gun_id][0])


def pvp_gun_ammo_counts(gun_id: int, *, randomize: bool = False) -> tuple[int, int]:
    """Fill the gun, respecting its configured maximum number of real rounds.

    The copied config does not disclose the original draw weights.  Runtime
    reloads choose uniformly among 1..max_real as an explicit lab estimate;
    deterministic callers retain max_real for reproducible protocol fixtures.
    """
    if not 0 <= gun_id < len(GUN_AMMO_SPECS):
        raise ValueError(f"gun cfg {gun_id} is not in the copied config")
    capacity, max_real = GUN_AMMO_SPECS[gun_id]
    real = random.randint(1, max_real) if randomize and max_real else max_real
    return real, capacity - real

# The skill ids below come from the copied fight_dbconfig.ab.  Keeping the
# mapping next to the packet builders prevents the local server from silently
# sending a card with a skill id that the shipped client cannot animate.
LAB_CARD_SKILLS = {
    2007: 1006, 2009: 1008, 2015: 1014, 2016: 1015, 2018: 1017,
    2020: 1019, 2021: 1020, 2022: 1021, 2024: 1022, 2025: 1023,
    2026: 1024, 2027: 1025, 2028: 1019, 2029: 10008, 2030: 10009,
    2031: 10010, 2032: 10011, 2033: 1026, 2034: 1028, 2036: 1038,
    2037: 1039,
}

# hero_cfg_steam/skill_cfg_steam in the copied fight_dbconfig.ab.  Values are
# (skill id, hero.init_skill_cd, skill.cd after use), respectively.
LAB_HERO_SKILLS = {
    0: (10000, 3, 3), 1: (10001, 3, 3), 13: (10002, 3, 3),
    14: (10005, 3, 3), 15: (10020, 3, 2), 16: (10017, 3, 3),
    17: (10022, 3, 3), 35: (10032, 3, 3), 36: (10035, 2, 2),
    38: (10038, 3, 3),
}


@dataclass(slots=True)
class MessageHead:
    length: int
    error: int
    cmd: int
    act: int
    index: int
    flags: int


def encode_varint(value: int) -> bytes:
    """Encode an unsigned protobuf varint."""
    if value < 0:
        value &= (1 << 64) - 1
    out = bytearray()
    while value > 0x7F:
        out.append((value & 0x7F) | 0x80)
        value >>= 7
    out.append(value)
    return bytes(out)


def decode_varint(data: bytes, offset: int = 0) -> tuple[int, int]:
    value = 0
    shift = 0
    while offset < len(data):
        byte = data[offset]
        offset += 1
        value |= (byte & 0x7F) << shift
        if not byte & 0x80:
            return value, offset
        shift += 7
        if shift > 63:
            raise ValueError("protobuf varint is too long")
    raise ValueError("truncated protobuf varint")


def pb_varint(field_number: int, value: int) -> bytes:
    return encode_varint((field_number << 3) | 0) + encode_varint(value)


def pb_bytes(field_number: int, value: bytes | str) -> bytes:
    if isinstance(value, str):
        value = value.encode("utf-8")
    return (
        encode_varint((field_number << 3) | 2)
        + encode_varint(len(value))
        + value
    )


def pb_message(*fields: bytes) -> bytes:
    return b"".join(fields)


def season_state(inventory: dict) -> dict[str, int]:
    """Return one internally consistent season state for the offline lab.

    A stale/missing value must never turn into season 0.  The client compares
    the season id in the profile with the id calculated from server time, so
    both are clamped to the same known bundled season here.
    """
    try:
        server_time = int(inventory.get("serverTime", LAB_SERVER_TIME))
    except (TypeError, ValueError):
        server_time = LAB_SERVER_TIME
    if not LAB_SEASON_START <= server_time <= LAB_SEASON_END:
        server_time = LAB_SERVER_TIME

    try:
        season_id = int(inventory.get("seasonId", LAB_SEASON_ID))
    except (TypeError, ValueError):
        season_id = LAB_SEASON_ID
    if season_id != LAB_SEASON_ID:
        season_id = LAB_SEASON_ID

    try:
        last_season_id = int(inventory.get("lastSeasonId", LAB_LAST_SEASON_ID))
    except (TypeError, ValueError):
        last_season_id = LAB_LAST_SEASON_ID
    if last_season_id <= 0 or last_season_id >= season_id:
        last_season_id = LAB_LAST_SEASON_ID

    try:
        cup = int(inventory.get("seasonCup", LAB_SEASON_CUP))
    except (TypeError, ValueError):
        cup = LAB_SEASON_CUP
    if cup <= 0:
        cup = LAB_SEASON_CUP

    try:
        mmr = int(inventory.get("seasonMmr", LAB_SEASON_MMR))
    except (TypeError, ValueError):
        mmr = LAB_SEASON_MMR
    if mmr < 0:
        mmr = LAB_SEASON_MMR

    return {
        "serverTime": server_time,
        "seasonId": season_id,
        "lastSeasonId": last_season_id,
        "seasonCup": cup,
        "seasonMmr": mmr,
    }


def _treasure_box_message(entry: dict) -> bytes:
    """Serialize the shipped TreasureBox slot state.

    The client treats ``status == 0`` (or a missing slot record) as locked and
    ``boxId == -1`` as an unlocked empty slot.  A 1000 speed factor represents
    the neutral 1.0 rate used by the client's timer arithmetic.
    """
    return pb_message(
        pb_varint(1, int(entry["index"])),
        pb_varint(2, int(entry.get("openBoxTimeDec", 1000))),
        pb_varint(3, int(entry.get("openBoxTimeDecTem", 0))),
        pb_varint(4, int(entry.get("boxId", -1))),
        pb_varint(5, int(entry.get("startTime", 0))),
        *(
            pb_varint(6, int(seconds))
            for seconds in entry.get("boxTimeTemDec", [])
        ),
        pb_varint(7, int(entry.get("status", 0))),
        *(
            pb_bytes(
                8,
                pb_message(
                    pb_varint(1, int(record.get("rate", 1000))),
                    pb_varint(2, int(record.get("startTime", 0))),
                    pb_varint(3, int(record.get("endTime", -1))),
                ),
            )
            for record in entry.get("timeRecord", [])
        ),
    )


def _home_income_message(entry: dict) -> bytes:
    """Serialize one shipped ``HomeIncome`` entry without changing its rate."""
    fields = [
        pb_varint(1, int(entry.get("itemId", 0))),
        pb_varint(2, int(entry.get("income", 0))),
        pb_varint(3, int(entry.get("startTime", 0))),
        pb_varint(4, int(entry.get("endTime", 0))),
    ]
    return pb_message(*fields)


def _home_message(
    level: int = 1,
    exp: int = 0,
    treasure_boxes: list[dict] | None = None,
    temporary_box_id: int = -1,
    r_coin_income: int = 0,
    box_reclaim: int = 0,
    get_income_time: int = 0,
    money_income: int = 0,
    current_income: list[dict] | None = None,
) -> bytes:
    """Build GamerHome, including slots and persisted passive-income rows."""
    day_data = pb_message(
        pb_varint(1, 0),  # reclaimMoney
        pb_varint(2, exp),  # exp
    )
    return pb_message(
        pb_varint(1, level),
        pb_varint(2, exp),
        pb_varint(3, r_coin_income),
        pb_varint(4, box_reclaim),
        *(
            pb_bytes(6, _treasure_box_message(box))
            for box in (treasure_boxes or [])
        ),
        pb_varint(7, temporary_box_id),
        pb_varint(8, get_income_time),
        pb_varint(9, money_income),
        *(
            pb_bytes(10, _home_income_message(entry))
            for entry in (current_income or [])
            if isinstance(entry, dict)
        ),
        pb_bytes(11, day_data),
    )


def _guild_info_message(tutorial_finished: bool) -> bytes:
    """Build both hall and PVP guide completion flags."""
    finished = 1 if tutorial_finished else 0
    return pb_message(
        pb_varint(6, finished),  # isFinishHallGuild
        pb_varint(7, finished),  # isFinishPvpGuild
    )


def parse_varint_field(data: bytes, wanted_field: int) -> int | None:
    """Read one protobuf varint field, ignoring all other wire types."""
    offset = 0
    while offset < len(data):
        tag, offset = decode_varint(data, offset)
        field_number = tag >> 3
        wire_type = tag & 7
        if wire_type == 0:
            value, offset = decode_varint(data, offset)
            if field_number == wanted_field:
                return value
        elif wire_type == 1:
            offset += 8
        elif wire_type == 2:
            size, offset = decode_varint(data, offset)
            offset += size
        elif wire_type == 5:
            offset += 4
        else:
            raise ValueError(f"unsupported protobuf wire type {wire_type}")
    return None


def parse_bytes_field(data: bytes, wanted_field: int) -> bytes | None:
    """Read one protobuf length-delimited field."""
    offset = 0
    while offset < len(data):
        tag, offset = decode_varint(data, offset)
        field_number = tag >> 3
        wire_type = tag & 7
        if wire_type == 0:
            _, offset = decode_varint(data, offset)
        elif wire_type == 1:
            offset += 8
        elif wire_type == 2:
            size, offset = decode_varint(data, offset)
            value = data[offset : offset + size]
            offset += size
            if field_number == wanted_field:
                return value
        elif wire_type == 5:
            offset += 4
        else:
            raise ValueError(f"unsupported protobuf wire type {wire_type}")
    return None


def parse_bytes_fields(data: bytes, wanted_field: int) -> list[bytes]:
    """Read every occurrence of one protobuf length-delimited field."""
    values: list[bytes] = []
    offset = 0
    while offset < len(data):
        tag, offset = decode_varint(data, offset)
        field_number = tag >> 3
        wire_type = tag & 7
        if wire_type == 0:
            _, offset = decode_varint(data, offset)
        elif wire_type == 1:
            offset += 8
        elif wire_type == 2:
            size, offset = decode_varint(data, offset)
            value = data[offset : offset + size]
            offset += size
            if field_number == wanted_field:
                values.append(value)
        elif wire_type == 5:
            offset += 4
        else:
            raise ValueError(f"unsupported protobuf wire type {wire_type}")
    return values


def _iter_pb_fields(data: bytes):
    """Yield ``(number, wire_type, value, raw_field)`` for a protobuf message.

    The lab only needs a tiny subset of protobuf, but rewriting a nested PVP
    snapshot by string replacement is unsafe: field 2 appears several times
    at different nesting levels.  Keeping the original raw field for fields
    we do not touch lets us update HP/ammo without dropping appearance data.
    """
    offset = 0
    while offset < len(data):
        start = offset
        tag, offset = decode_varint(data, offset)
        field_number = tag >> 3
        wire_type = tag & 7
        if wire_type == 0:
            value, offset = decode_varint(data, offset)
        elif wire_type == 1:
            value = data[offset : offset + 8]
            offset += 8
        elif wire_type == 2:
            size, offset = decode_varint(data, offset)
            value = data[offset : offset + size]
            offset += size
        elif wire_type == 5:
            value = data[offset : offset + 4]
            offset += 4
        else:
            raise ValueError(f"unsupported protobuf wire type {wire_type}")
        if offset > len(data):
            raise ValueError("truncated protobuf field")
        yield field_number, wire_type, value, data[start:offset]


def decode_header(data: bytes) -> MessageHead:
    if len(data) != HEADER_SIZE:
        raise ValueError(f"header must be {HEADER_SIZE} bytes")
    length, error, cmd, act, index, flags = struct.unpack("<IHBBHH", data)
    if length > MAX_FRAME_SIZE:
        raise ValueError(f"frame too large: {length}; header={data.hex()}")
    return MessageHead(length, error, cmd, act, index, flags)


def encode_frame(
    cmd: int,
    act: int,
    body: bytes = b"",
    *,
    error: int = 0,
    index: int = 0,
    flags: int = 0,
    length_mode: str = "body",
) -> bytes:
    if length_mode not in {"total", "body"}:
        raise ValueError("length_mode must be 'total' or 'body'")
    length = len(body) + HEADER_SIZE if length_mode == "total" else len(body)
    header = struct.pack(
        "<IHBBHH",
        length,
        error,
        cmd & 0xFF,
        act & 0xFF,
        index & 0xFFFF,
        flags & 0xFFFF,
    )
    return header + body


def response_body(
    cmd: int,
    act: int,
    gid: int,
    session: str,
    pvp_port: int,
    prepare_hero: int = 0,
    home_level: int = 1,
    money: int = 9_999_999,
    diamond: int = 9_999_999,
    rcoin: int = 9_999_999,
    hunter_coin: int = 9_999_999,
    profile: dict | None = None,
) -> bytes:
    """Build a conservative GamerLoginS2C response.

    The nested Gamer fields are the fields consumed immediately by the Lua
    login path. Missing optional/repeated fields intentionally remain absent.
    """
    gamer = pb_message(
        pb_varint(1, gid),
        pb_bytes(2, (profile or {}).get('name', 'Local Hunter')),
        pb_varint(3, 1),
        pb_varint(4, 1),
        pb_varint(5, (profile or {}).get('icon', 1)),
        pb_varint(6, (profile or {}).get('frame', 0)),
        pb_varint(11, 1),
        pb_varint(12, 1),
        pb_varint(13, 1),
        pb_varint(14, pvp_port),
        pb_bytes(15, "127.0.0.1"),
        pb_bytes(16, session),
        pb_bytes(18, f"local-{gid}"),
        pb_bytes(19, "local"),
        pb_bytes(33, _item_config_message(101000, money)),
        pb_bytes(34, _item_config_message(103000, diamond)),
        pb_bytes(35, _item_config_message(102000, rcoin)),
        pb_varint(40, prepare_hero),
        pb_varint(41, prepare_hero),
        pb_bytes(42, _item_config_message(103500, hunter_coin)),
        pb_varint(48, (profile or {}).get('country', 0)),
    )
    return pb_message(pb_bytes(1, gamer), pb_bytes(2, _home_message(home_level)))


def _hero_message(entry: dict) -> bytes:
    faction = int(entry.get("faction", 0))
    return pb_message(
        pb_varint(1, int(entry["id"])),
        pb_varint(2, int(entry.get("starLevel", 5))),
        pb_varint(3, 1),
        pb_varint(4, effective_hero_skill(entry)),
        pb_varint(5, 1),
        pb_varint(6, int(entry.get("trophy", 0))),
        pb_varint(7, int(entry.get("fightLevel", 1))),
        pb_varint(8, int(entry.get("fightExp", 0))),
        pb_varint(9, int(entry.get("faction", 0))),
        pb_varint(10, 1),
        *(pb_varint(11, int(card_id)) for card_id in entry.get("unlockCards", [])),
        *((pb_varint(12, int(entry["readyCard"])),) if entry.get("readyCard") else ()),
        *((pb_varint(13, faction),) if faction else ()),
    )


def hero_card_ready_body(entry: dict) -> bytes:
    """GamerCardReadyS2C with the complete, persisted GamerHero record."""
    return pb_message(pb_bytes(1, _hero_message(entry)))


def hero_card_unlock_body(entry: dict, cost: list[dict] | None = None) -> bytes:
    """GamerCardUnlockS2C with the updated hero and absolute costs.

    The client feeds ``cost`` directly into ``GamerBag.UpdateItems``.  Sending
    the post-transaction absolute quantities is therefore required for both
    the hero card page and the bag counter to stay in sync.
    """
    return pb_message(
        pb_bytes(1, _hero_message(entry)),
        *(pb_bytes(2, _item_data_message(item)) for item in (cost or [])),
    )


def market_purchase_body(
    shop_item_id: int,
    purchase_count: int,
    award_item_id: int,
    award_count: int,
    cost: list[dict] | None = None,
) -> bytes:
    """GamerBuyInMarketS2C for the shipped Steam supply-box product.

    ``cost`` is a list of absolute ItemData records.  The client feeds this
    list straight into ``GamerBag.UpdateItems``; omitting it makes a purchase
    look successful while leaving the currency unchanged.
    """
    limit_item = pb_message(
        pb_varint(1, shop_item_id),
        pb_varint(2, purchase_count),
    )
    award_item = _item_message({"id": award_item_id, "number": award_count})
    award = pb_message(pb_bytes(1, award_item))
    return pb_message(
        *(pb_bytes(1, _item_data_message(item)) for item in (cost or [])),
        pb_bytes(2, limit_item),
        pb_bytes(3, award),
    )


def _explore_box_state(inventory: dict) -> tuple[bytes, list[bytes]]:
    stored = {
        int(cell.get("id", 0)): cell for cell in inventory.get("exploreCells", [])
    }
    cells = [
        _open_explore_cell(stored[cell_id])
        if cell_id in stored
        else pb_message(pb_varint(1, cell_id))
        for cell_id in range(1, 12)
    ]
    info = pb_message(
        *(pb_bytes(1, cell) for cell in cells),
        pb_varint(2, int(inventory.get("serverTime", LAB_SERVER_TIME))),
        pb_varint(3, int(inventory.get("exploreLevel", 1))),
        pb_varint(4, int(inventory.get("exploreLevel", 1))),
        pb_varint(5, 60),
    )
    pack = [
        _item_config_message(int(item["id"]), int(item.get("number", 0)))
        for item in inventory.get("exploreBoxPack", [])
        if int(item.get("number", 0)) > 0
    ]
    return info, pack


def explore_box_info_body(inventory: dict) -> bytes:
    """GamerExploreBoxCellS2C for the current Steam exploration-box screen."""
    info, pack = _explore_box_state(inventory)
    return pb_message(
        pb_bytes(1, info),
        *(pb_bytes(3, item) for item in pack),
    )


def explore_box_notify_body(inventory: dict) -> bytes:
    """NotifyUpdateGamerExploreBox after moving a box out of storage."""
    info, pack = _explore_box_state(inventory)
    return pb_message(pb_bytes(1, info), *(pb_bytes(2, item) for item in pack))


def _open_explore_cell(cell: dict) -> bytes:
    """Encode one Cell after the server resolves its five opening shots."""
    fields = [pb_varint(1, int(cell["id"]))]
    fields.append(pb_varint(2, int(cell.get("chest", 12))))
    if cell.get("isAdv"):
        fields.append(pb_varint(3, 1))
    for event in cell.get("event", []):
        fields.append(pb_varint(4, int(event)))
    if cell.get("oldChest"):
        fields.append(pb_varint(5, int(cell["oldChest"])))
    return pb_message(*fields)


def explore_box_open_body(
    cell: dict,
    cost: list[dict] | None = None,
) -> bytes:
    """GamerExploreBoxOpenS2C for one selected cell."""
    if cost is None:
        cost = cell.get("cost", [])
    return pb_message(
        pb_bytes(1, _open_explore_cell(cell)),
        *(pb_bytes(2, _item_data_message(item)) for item in cost),
    )


def explore_box_open_all_body(
    inventory: dict,
    cells: list[dict] | None = None,
    cost: list[dict] | None = None,
) -> bytes:
    """GamerExploreBoxOpenAllS2C for cells opened by this request.

    ``cells`` is supplied by the state transition so a second open-all does
    not replay already-running boxes.  The inventory fallback keeps this
    helper convenient for the standalone protocol tests.
    """
    source = cells if cells is not None else inventory.get("exploreCells", [])
    if cost is None and source:
        cost = source[0].get("cost", [])
    return pb_message(
        *(
            pb_bytes(1, _open_explore_cell(cell))
            for cell in source
            if int(cell.get("chest", 0)) > 0
        ),
        *(pb_bytes(2, _item_data_message(item)) for item in (cost or [])),
    )


def _item_message(entry: dict) -> bytes:
    """Serialize ItemGood, whose number is a full bag quantity."""
    return pb_message(
        pb_varint(1, int(entry["id"])),
        pb_varint(2, int(entry.get("number", 1))),
    )


def _badge_message(entry: dict) -> bytes:
    """Serialize one ``Badge`` from GamerLoginGetDataS2C.badge."""
    return pb_message(
        pb_varint(1, int(entry["id"])),
        pb_varint(2, int(entry.get("number", 0))),
    )


def _item_data_message(entry: dict) -> bytes:
    """Serialize ItemData used by costs, rewards and bag notifications."""
    fields = [
        pb_varint(1, int(entry["id"])),
        pb_varint(2, int(entry.get("number", 0))),
    ]
    if entry.get("chgNumber") is not None:
        fields.append(pb_varint(3, int(entry["chgNumber"])))
    if entry.get("token") is not None:
        fields.append(pb_varint(4, int(entry["token"])))
    return pb_message(*fields)


def bag_get_pack_body(inventory: dict) -> bytes:
    """GamerGetPackS2C with the persisted ItemGood list."""
    return pb_message(
        *(
            pb_bytes(1, _item_message(item))
            for item in inventory.get("items", [])
            if int(item.get("number", 0)) > 0
        )
    )


def bag_update_body(items: list[dict] | None = None) -> bytes:
    """NotifyUpdatePack with absolute ItemData quantities."""
    return pb_message(
        *(pb_bytes(1, _item_data_message(item)) for item in (items or []))
    )


def bag_use_body(
    cost: list[dict],
    award: list[dict] | None = None,
) -> bytes:
    """GamerUseGoodsS2C with absolute post-transaction quantities."""
    reward = _item_to_get_show_change(award or [])
    return pb_message(
        *(pb_bytes(1, _item_data_message(item)) for item in cost),
        pb_bytes(3, reward),
    )


def bag_sell_body(
    sold: list[dict],
    award: list[dict] | None = None,
) -> bytes:
    """GamerSellGoodsS2C with absolute sold-item and reward quantities."""
    reward = _item_to_get_show_change(award or [])
    return pb_message(
        *(pb_bytes(1, _item_data_message(item)) for item in sold),
        pb_bytes(2, reward),
    )


def home_update_body(inventory: dict) -> bytes:
    """NotifyGamerHomeUpdate carrying the complete current home state."""
    return pb_message(
        pb_bytes(
            1,
            _home_message(
                int(inventory.get("homeLevel", 1)),
                int(inventory.get("homeExp", 0)),
                inventory.get("treasureBoxes", []),
                int(inventory.get("temporaryBoxId", -1)),
                int(inventory.get("rCoinIncome", 0)),
                int(inventory.get("boxReclaim", 0)),
                int(inventory.get("getIncomeTime", 0)),
                int(inventory.get("moneyIncome", 0)),
                inventory.get("currentIncome", []),
            ),
        )
    )


def home_start_box_body(boxes: list[dict]) -> bytes:
    """GamerStartBoxS2C with the authoritative slot list."""
    return pb_message(*(pb_bytes(2, _treasure_box_message(box)) for box in boxes))


def home_open_box_body(
    gid: int,
    box: dict | None,
    cost: list[dict] | None = None,
    award: list[dict] | None = None,
) -> bytes:
    """GamerOpenBoxS2C for a slot or the temporary home box."""
    fields = [pb_varint(1, int(gid))]
    fields.extend(pb_bytes(2, _item_data_message(item)) for item in (cost or []))
    if box is not None:
        fields.append(pb_bytes(3, _treasure_box_message(box)))
    fields.append(pb_bytes(4, _item_to_get_show_change(award or [])))
    return pb_message(*fields)


def home_sell_box_body(award: list[dict] | None = None) -> bytes:
    """GamerShellBoxS2C with the absolute sold-box reward."""
    return pb_message(pb_bytes(1, _item_to_get_show_change(award or [])))


def home_income_body(award: list[dict] | None = None) -> bytes:
    """GamerGetIncomeS2C with the absolute collected income."""
    return pb_message(pb_bytes(1, _item_to_get_show_change(award or [])))


def _item_config_message(item_id: int, number: int) -> bytes:
    return pb_message(pb_varint(1, item_id), pb_varint(2, number))


def _item_to_get_show_change(
    item_id: int | list[dict],
    number: int | None = None,
) -> bytes:
    """Serialize the common reward wrapper used by box award responses.

    ``ItemToGetShowChange.get`` is the authoritative post-transaction bag
    quantity.  The Steam client does not use that field to decide whether to
    open its reward window, though: ``GlobalFunc.IsAwardNotEmptyToShow`` only
    checks ``show``/``change``/``specialShow``.  Keep the absolute quantity in
    ``get`` and mirror each positive reward in ``show`` with ``chgNumber`` as
    the display delta.  Callers may provide ``chgNumber`` (or the internal
    ``delta`` alias) when the award is a repeated/stacked item; legacy callers
    without it safely fall back to the returned number.
    """
    if isinstance(item_id, list):
        entries = item_id
    else:
        entries = [{"id": item_id, "number": 0 if number is None else number}]
    get_fields: list[bytes] = []
    show_fields: list[bytes] = []
    special_fields: list[bytes] = []
    for item in entries:
        absolute = int(item.get("number", 0))
        if absolute < 0:
            continue
        # Do not leak the display-only delta into the authoritative ``get``
        # record.  ``token`` is retained because it is part of ItemData.
        get_entry = {
            "id": int(item["id"]),
            "number": absolute,
        }
        if item.get("token") is not None:
            get_entry["token"] = int(item["token"])
        get_fields.append(pb_bytes(1, _item_data_message(get_entry)))

        raw_delta = item.get("chgNumber", item.get("delta", absolute))
        delta = int(raw_delta)
        if delta > 0:
            show_entry = dict(get_entry)
            show_entry["chgNumber"] = delta
            show_fields.append(pb_bytes(2, _item_data_message(show_entry)))
        if item.get("specialShow") or item.get("special_show"):
            # NewItem has only the item id.  The client uses it to route hero
            # badges/skins/guns to the special reward presentation.
            special_fields.append(
                pb_bytes(4, pb_message(pb_varint(1, int(item["id"]))))
            )
    return pb_message(*(get_fields + show_fields + special_fields))


def explore_box_award_body(
    cell: dict,
    item_id: int | None = None,
    item_number: int | None = None,
) -> bytes:
    """GamerExploreBoxGetAwardS2C for one collected cell.

    The reward is taken from the state transition, not from the visual
    preview table.  Regular ExploreBoxCfgSteam cells use the box_award item
    for their final quality/level (for example 701231 for purple level 0).
    """
    reward = _item_to_get_show_change(
        [
            {
                "id": int(cell.get("rewardId", item_id if item_id is not None else 701231)),
                "number": int(
                    cell.get("rewardNumber", item_number if item_number is not None else 1)
                ),
                "chgNumber": int(cell.get("rewardDelta", 1)),
            }
        ]
    )
    return pb_message(
        pb_bytes(1, _open_explore_cell(cell)),
        pb_bytes(2, reward),
    )


def explore_box_award_all_body(
    cells: list[dict],
    item_id: int | None = None,
    item_number: int | None = None,
) -> bytes:
    """GamerExploreBoxGetAwardAllS2C for all collected cells."""
    reward_entries: dict[int, int] = {}
    for cell in cells:
        reward_id = int(cell.get("rewardId", item_id if item_id is not None else 701231))
        reward_number = int(
            cell.get("rewardNumber", item_number if item_number is not None else 1)
        )
        reward_entries[reward_id] = max(reward_entries.get(reward_id, 0), reward_number)
    reward = _item_to_get_show_change(
        [
            {
                "id": reward_id,
                "number": number,
                "chgNumber": sum(
                    int(cell.get("rewardDelta", 1))
                    for cell in cells
                    if int(cell.get("rewardId", item_id if item_id is not None else 701231))
                    == reward_id
                ),
            }
            for reward_id, number in reward_entries.items()
        ]
    )
    return pb_message(
        *(pb_bytes(1, _open_explore_cell(cell)) for cell in cells),
        pb_bytes(2, reward),
    )


def _season_message(season_id: int, last_season_id: int) -> bytes:
    return pb_message(
        pb_varint(1, season_id),
        pb_varint(2, last_season_id),
    )


def _season_info_message(season_id: int, cup: int, mmr: int = 0) -> bytes:
    return pb_message(
        pb_varint(1, season_id),
        pb_varint(2, mmr),
        pb_varint(3, cup),
        pb_varint(4, mmr),
        pb_varint(5, cup),
    )


def server_time_body(inventory: dict) -> bytes:
    """Build the direct ServerTime response used by the main heartbeat."""
    state = season_state(inventory)
    return pb_message(
        pb_varint(1, state["serverTime"]),
        pb_varint(7, 0),
    )


def season_get_info_body(inventory: dict) -> bytes:
    state = season_state(inventory)
    season_id = state["seasonId"]
    last_season_id = state["lastSeasonId"]
    cup = state["seasonCup"]
    mmr = state["seasonMmr"]
    return pb_message(
        pb_bytes(1, _season_message(season_id, last_season_id)),
        pb_bytes(2, _season_info_message(season_id, cup, mmr)),
    )


def season_open_body(inventory: dict) -> bytes:
    state = season_state(inventory)
    season_id = state["seasonId"]
    last_season_id = state["lastSeasonId"]
    cup = state["seasonCup"]
    mmr = state["seasonMmr"]
    return pb_message(
        pb_bytes(2, _season_message(season_id, last_season_id)),
        pb_bytes(3, _season_info_message(season_id, cup, mmr)),
        pb_bytes(4, _season_info_message(last_season_id, cup, mmr)),
    )


def _fashion_message(entry: dict) -> bytes:
    return pb_message(
        pb_varint(1, int(entry["id"])),
        # Permanent ownership is represented by duration=-1.  Omitting this
        # field makes the client parse duration as zero (expired), which in
        # turn makes the equip button look inconsistent until the next login.
        pb_varint(2, int(entry.get("sTime", 0))),
        pb_varint(3, int(entry.get("duration", -1))),
        pb_varint(4, int(entry.get("gTime", 0))),
        pb_varint(5, 1 if entry.get("isRead", True) else 0),
    )


def _fashion_wear_message(entry: dict) -> bytes:
    return pb_message(
        pb_varint(1, int(entry["targetId"])),
        pb_varint(2, int(entry["fashionId"])),
        pb_varint(3, int(entry.get("type", 1))),
    )


def equipped_fashions(inventory: dict) -> list[dict]:
    """Return the persisted wear list, including safe defaults for old files."""
    equipped_skins = inventory.get("equippedSkins")
    if equipped_skins is not None:
        return equipped_skins
    return [
        {
            "targetId": hero["id"],
            "fashionId": hero["baseFashionId"],
            "type": 1,
        }
        for hero in inventory.get("heroes", [])
        if hero.get("baseFashionId") is not None
    ]


def fashion_update_body(inventory: dict) -> bytes:
    """Build NotifyGamerFashion so an equip is visible without relogging."""
    return pb_message(
        *(
            pb_bytes(1, _fashion_message(fashion))
            for fashion in inventory.get("skins", [])
        ),
        *(
            pb_bytes(2, _fashion_wear_message(fashion))
            for fashion in equipped_fashions(inventory)
        ),
    )


def hero_gun_update_body(inventory: dict) -> bytes:
    """Build NotifyGamerHeroGun for an immediate weapon-selection refresh."""
    return pb_message(
        *(
            pb_bytes(1, _hero_gun_message(hero_gun))
            for hero_gun in inventory.get("heroGuns", [])
        )
    )


def _gun_message(entry: dict) -> bytes:
    return pb_message(pb_varint(1, int(entry["id"])), pb_varint(2, 0))


def _hero_gun_message(entry: dict) -> bytes:
    return pb_message(
        pb_varint(1, int(entry["heroId"])),
        pb_varint(2, int(entry["gunId"])),
    )


def _card_message(entry: dict) -> bytes:
    return pb_message(
        pb_varint(1, int(entry["id"])),
        pb_varint(2, int(entry.get("number", 3))),
        pb_varint(3, int(entry.get("status", 0))),
    )


def login_data_body(gid: int, session: str, inventory: dict, *, clan_team: bytes | None = None,
                    gamer_clan_team: bytes | None = None, profile: dict | None = None,
                    accessories: bytes = b'') -> bytes:
    """Build the smallest GamerLoginGetDataS2C accepted by the client path."""
    season = season_state(inventory)
    server_time = pb_varint(1, season["serverTime"])
    time_record = pb_message(pb_varint(7, 1),
        pb_varint(13, (profile or {}).get('lastRename', 0)),
        pb_varint(14, (profile or {}).get('lastCountry', 0)))
    home_level = int(inventory.get("homeLevel", 1))
    home_exp = int(inventory.get("homeExp", 0))
    tutorial_finished = bool(inventory.get("tutorialFinished", True))
    heroes = inventory.get("heroes", [])
    guns = inventory.get("guns", [])
    hero_guns = inventory.get("heroGuns", [])
    return pb_message(
        pb_bytes(1, server_time),
        *((pb_bytes(32, clan_team),) if clan_team is not None else ()),
        *((pb_bytes(33, gamer_clan_team),) if gamer_clan_team is not None else ()),
        pb_bytes(2, time_record),
        accessories,
        pb_bytes(22, pb_varint(1, (profile or {}).get('renameFree', 0))),
        pb_varint(4, int(inventory.get("pvpCoin", 1000))),
        *(pb_bytes(5, _item_message(item)) for item in inventory.get("items", [])),
        *(pb_bytes(7, _badge_message(badge)) for badge in inventory.get("badges", [])),
        *(pb_bytes(6, _hero_message(hero)) for hero in heroes),
        *(pb_bytes(9, _card_message(card)) for card in inventory.get("cards", [])),
        pb_bytes(10, _guild_info_message(tutorial_finished)),
        pb_bytes(
            11,
            _home_message(
                home_level,
                home_exp,
                inventory.get("treasureBoxes", []),
                int(inventory.get("temporaryBoxId", -1)),
                int(inventory.get("rCoinIncome", 0)),
                int(inventory.get("boxReclaim", 0)),
                int(inventory.get("getIncomeTime", 0)),
                int(inventory.get("moneyIncome", 0)),
                inventory.get("currentIncome", []),
            ),
        ),
        pb_bytes(
            13,
            _season_message(
                season["seasonId"],
                season["lastSeasonId"],
            ),
        ),
        *(pb_bytes(16, _fashion_message(fashion)) for fashion in inventory.get("skins", [])),
        *(
            pb_bytes(17, _fashion_wear_message(fashion))
            for fashion in equipped_fashions(inventory)
        ),
        *(pb_bytes(19, _gun_message(gun)) for gun in guns),
        *(pb_bytes(20, _hero_gun_message(hero_gun)) for hero_gun in hero_guns),
    )


def chat_server_body(chat_port: int) -> bytes:
    """Advertise the local chat endpoint returned by GamerGetChatServerS2C."""
    return pb_message(
        pb_varint(1, 1),
        pb_bytes(2, "local-chat"),
        pb_bytes(3, "127.0.0.1"),
        pb_varint(4, chat_port),
    )


def chat_login_body(gid: int) -> bytes:
    """Minimal GamerChatLoginS2C/GamerChatHeartS2C acknowledgement."""
    return pb_varint(1, gid)


def local_bot_start_body(
    pvp_port: int,
    mode: int = 1,
    sub_mode: int = 0,
    hero_id: int = 0,
    card_id: int = 0,
) -> bytes:
    """Notify marker that preserves the requested local mode and loadout."""
    marker = f"local-pvp:{mode}:{sub_mode}:{hero_id}:{card_id}"
    info = pb_message(
        # The original client expects three colon-delimited components.
        # ConnectPvpSvc reads indexes 2/3 as host/port; this is deliberately
        # not a URI because the splitter does not strip leading slashes.
        pb_bytes(1, f"tcp:127.0.0.1:{pvp_port}"),
        pb_bytes(2, marker),
        pb_varint(3, 0),
    )
    return pb_bytes(1, info)


def pvp_fd_body(gid: int, pvp_port: int) -> bytes:
    return pb_message(
        pb_varint(1, gid),
        pb_bytes(2, f"local-fd-{gid}"),
        pb_varint(3, 0),
        pb_bytes(5, b""),
    )


def _local_pvp_gamer(
    gid: int,
    name: str,
    hero_id: int,
    hero_model_id: int,
    hero_fashion_id: int,
    gun_id: int,
    gun_model_id: int,
    gun_fashion_id: int,
    index: int,
    robot: bool,
    fake_ammo_count: int | None = None,
    real_ammo_count: int | None = None,
    coin: int = 0,
    card_slot: bytes | None = None,
    randomize_ammo: bool = False,
    active_skill_id: int | None = None,
) -> bytes:
    if fake_ammo_count is None or real_ammo_count is None:
        configured_real, configured_fake = pvp_gun_ammo_counts(
            gun_id, randomize=randomize_ammo
        )
        if real_ammo_count is None:
            real_ammo_count = configured_real
        if fake_ammo_count is None:
            fake_ammo_count = configured_fake
    base_hero = pb_message(
        pb_varint(1, hero_id),
        pb_varint(4, 1),
        pb_varint(5, hero_fashion_id),
    )
    base_gun = pb_message(
        pb_varint(1, gun_id),
        pb_varint(2, gun_fashion_id),
    )
    base = pb_message(
        pb_varint(1, gid),
        pb_bytes(2, name),
        pb_varint(3, 1),
        pb_varint(4, 50),
        pb_bytes(8, f"local-player-{gid}"),
        pb_varint(9, int(robot)),
        pb_varint(11, index),
        pb_bytes(22, base_hero),
        pb_varint(23, hero_id),
        pb_bytes(29, base_gun),
        pb_varint(31, hero_id + 1),
        pb_varint(33, 1001),
        # BasePvpGamer.campIdx is the team identifier used by the result UI.
        # Player and bot must not both fall back to protobuf's zero default.
        pb_varint(34, index),
    )
    # Verified against the bundled ammo_cfg: cfg 1 is real ammo and cfg 300
    # is the blank/fake round.  The order is significant for the roulette UI,
    # so keep the stacks in their official sort order (blank, then real).
    fake_ammo = pb_message(
        pb_varint(1, 300), pb_varint(2, max(0, fake_ammo_count)), pb_varint(3, 1)
    )
    real_ammo = pb_message(
        pb_varint(1, 1), pb_varint(2, max(0, real_ammo_count)), pb_varint(3, 3)
    )
    # Opening load is not an in-match reload: traits activate only later.
    gun = pb_message(
        pb_varint(1, gun_id),
        pb_bytes(2, fake_ammo),
        pb_bytes(2, real_ammo),
        pb_varint(3, gun_model_id),
        pb_varint(4, weapon_skill_id(gun_id)),
    )
    hero_skill_id, hero_skill_cd, _ = LAB_HERO_SKILLS.get(hero_id, (0, 0, 0))
    if active_skill_id is not None:
        hero_skill_id = active_skill_id
    hero = pb_message(
        pb_varint(1, hero_id),
        pb_varint(2, hero_skill_id),
        pb_varint(3, hero_skill_cd),
        pb_varint(4, hero_model_id),
    )
    fields = [
        pb_bytes(1, f"local-fd-{gid}"),
        pb_bytes(2, base),
        pb_varint(3, index),
        pb_varint(4, 4),
        pb_varint(5, max(0, coin)),
        pb_varint(6, 1),
        pb_bytes(7, gun),
        pb_bytes(9, hero),
        pb_varint(10, 2),
        pb_varint(11, 4),
        pb_varint(16, 4),
        # Frenzy/virtual HP has two visible slots in this mode and starts empty.
        pb_varint(17, 0),
        pb_varint(23, 2),
        # PvpGamerState: 0=normal. 1=grave mound, which prevents item targeting.
        pb_varint(27, 0),
    ]
    if card_slot is not None:
        fields.append(pb_bytes(18, card_slot))
    return pb_message(*fields)


def pvp_shop_card(
    card_id: int,
    cfg_id: int,
    price: int,
    turn: int = 1,
    status: int = 1,
) -> bytes:
    """Encode a visible shop offer using the shipped Pvp ``Card`` layout."""
    return pb_message(
        pb_varint(1, card_id),
        pb_varint(2, cfg_id),
        pb_varint(3, price),
        pb_varint(4, turn),
        pb_varint(5, status),  # PvpCartStatus: 1=in stock, 2=sold
        pb_varint(9, price),  # OriginalPrice
    )


def _pvp_card_with_status(card: bytes, status: int) -> bytes:
    """Replace Card.status while preserving the other configured card fields."""
    fields: list[bytes] = []
    found = False
    for number, wire_type, value, raw in _iter_pb_fields(card):
        if number == 5 and wire_type == 0:
            fields.append(pb_varint(5, status))
            found = True
        else:
            fields.append(raw)
    if not found:
        fields.append(pb_varint(5, status))
    return pb_message(*fields)


def pvp_card_slot_body(
    card: bytes,
    *,
    arg_one: int | None = -1,
    can_see: bool | None = None,
) -> bytes:
    """Encode a card slot, hiding the optional argument display by default.

    The client nameboard displays ``Card.arg_one`` whenever it is nonnegative.
    Ordinary cards have no numeric counter, so encode -1 rather than leaving
    the optional protobuf field absent (which the client reads as zero).
    Pass a nonnegative value for cards whose UI intentionally displays a
    value, such as the accumulated coins on a Piggybank.
    """
    card_id = parse_varint_field(card, 1) or 0
    cfg_id = parse_varint_field(card, 2) or 0
    fields = [pb_varint(1, card_id), pb_varint(2, cfg_id)]
    if can_see is not None:
        fields.append(pb_varint(6, int(can_see)))
    if arg_one is not None:
        fields.append(pb_varint(7, arg_one))
    return pb_message(*fields)


def pvp_carried_card_slot_body(card_cfg_id: int) -> bytes:
    """Build the initial piggybank slot from its selected cfg ID.

    The PVP snapshot is built for the first playable turn, whose hold-skill
    trigger has fired once. Other outside-carried card effects are not
    reconstructed here, so do not fabricate a slot for an unsupported card.
    """
    card_cfg_id = max(0, int(card_cfg_id))
    if card_cfg_id not in PIGGYBANK_COINS_PER_TURN:
        return b""
    stored_coins = PIGGYBANK_COINS_PER_TURN[card_cfg_id]
    return pb_message(
        pb_varint(1, card_cfg_id),
        pb_varint(2, card_cfg_id),
        pb_varint(6, 1),
        pb_varint(7, stored_coins),
    )


def pvp_card_slot_with_arg(card_slot: bytes, arg_one: int) -> bytes:
    """Replace Card.arg_one while preserving all other slot fields."""
    fields: list[bytes] = []
    found_arg = False
    for number, wire_type, value, raw in _iter_pb_fields(card_slot):
        if number == 7 and wire_type == 0:
            fields.append(pb_varint(7, arg_one))
            found_arg = True
        else:
            fields.append(raw)
    if not found_arg:
        fields.append(pb_varint(7, arg_one))
    return pb_message(*fields)


def pvp_empty_card_slot_body() -> bytes:
    """Encode an empty slot so the client clears its icon and scene prop."""
    return pb_message(
        pb_varint(1, 0),
        pb_varint(2, 0),
        pb_varint(6, 1),
        pb_varint(7, -1),
    )


def pvp_gamer_with_coin_and_card(
    gamer: bytes, *, coin: int, card_slot: bytes | None = None
) -> bytes:
    """Update a participant's match currency and stored-card slot."""
    fields: list[bytes] = []
    found_coin = False
    found_card = False
    for number, wire_type, value, raw in _iter_pb_fields(gamer):
        if number == 5 and wire_type == 0:
            fields.append(pb_varint(5, max(0, coin)))
            found_coin = True
        elif number == 18 and wire_type == 2 and card_slot is not None:
            fields.append(pb_bytes(18, card_slot))
            found_card = True
        else:
            fields.append(raw)
    if not found_coin:
        fields.append(pb_varint(5, max(0, coin)))
    if not found_card and card_slot is not None:
        fields.append(pb_bytes(18, card_slot))
    return pb_message(*fields)


def pvp_gamer_with_buffs(
    gamer: bytes,
    *,
    add_cfg_ids: tuple[int, ...] = (),
    del_cfg_ids: tuple[int, ...] = (),
    source_index: int = 0,
) -> bytes:
    """Add/remove configured PVP buffs while preserving every other gamer field."""
    add_ids = tuple(dict.fromkeys(int(cfg_id) for cfg_id in add_cfg_ids))
    del_ids = set(int(cfg_id) for cfg_id in del_cfg_ids)
    add_ids = tuple(cfg_id for cfg_id in add_ids if cfg_id not in del_ids)
    fields: list[bytes] = []
    present: set[int] = set()
    for number, wire_type, value, raw in _iter_pb_fields(gamer):
        if number == 8 and wire_type == 2:
            cfg_id = parse_varint_field(value, 1) or 0
            if cfg_id in del_ids:
                continue
            if cfg_id in add_ids:
                if cfg_id not in present:
                    fields.append(pb_bytes(8, value))
                    present.add(cfg_id)
                continue
            fields.append(raw)
            present.add(cfg_id)
        else:
            fields.append(raw)
    for cfg_id in add_ids:
        if cfg_id not in present:
            fields.append(pb_bytes(
                8,
                _pvp_buff(cfg_id, source_index=source_index),
            ))
    return pb_message(*fields)


def pvp_gamer_with_buff_countdown(
    gamer: bytes,
    cfg_ids: tuple[int, ...],
    turns_left: int,
    *,
    duration_turns: int | None = None,
) -> bytes:
    """Update elapsed/remaining turns without changing buff identity or source."""
    if turns_left <= 0:
        raise ValueError("expired buffs must be removed, not counted down")
    selected = set(cfg_ids)
    fields: list[bytes] = []
    for number, wire_type, value, raw in _iter_pb_fields(gamer):
        if (number == 8 and wire_type == 2
                and parse_varint_field(value, 1) in selected):
            duration = (duration_turns if duration_turns is not None
                        else parse_varint_field(value, 5) or turns_left)
            if duration < turns_left:
                raise ValueError("remaining turns exceed the buff duration")
            buff = pb_message(
                *(buff_raw for n, w, v, buff_raw in _iter_pb_fields(value)
                  if n not in (4, 5, 7)),
                pb_varint(4, duration - turns_left),
                pb_varint(5, duration),
                pb_varint(7, turns_left),
            )
            fields.append(pb_bytes(8, buff))
        else:
            fields.append(raw)
    return pb_message(*fields)


def pvp_info_with_shop(
    pvp_info: bytes, cards: tuple[bytes, ...] | list[bytes], refresh_coin: int
) -> bytes:
    """Replace the public shop stock and its refresh price in PvpInfo."""
    fields: list[bytes] = []
    found_cards = False
    found_price = False
    for number, wire_type, value, raw in _iter_pb_fields(pvp_info):
        if number == 7 and wire_type == 2:
            if not found_cards:
                fields.extend(pb_bytes(7, card) for card in cards)
                found_cards = True
        elif number == 41 and wire_type == 0:
            fields.append(pb_varint(41, max(0, refresh_coin)))
            found_price = True
        else:
            fields.append(raw)
    if not found_cards:
        fields.extend(pb_bytes(7, card) for card in cards)
    if not found_price:
        fields.append(pb_varint(41, max(0, refresh_coin)))
    return pb_message(*fields)


def pvp_gamer_after_weapon_reload(gamer: bytes) -> bytes:
    gun = parse_bytes_field(gamer, 7) or b''
    if weapon_skill_id(parse_varint_field(gun, 1) or 0) == GHOSTS_SKILL_ID:
        return pvp_gamer_with_buffs(gamer, del_cfg_ids=(GHOSTS_BUFF_ID,))
    if weapon_skill_id(parse_varint_field(gun, 1) or 0) == LOVESONG_SKILL_ID:
        return pvp_gamer_with_skill_cd(gamer, pvp_gamer_skill_cd(gamer) - 1)
    if weapon_skill_id(parse_varint_field(gun, 1) or 0) != LITTLE_MANIAC_SKILL_ID:
        return gamer
    return pvp_gamer_with_buffs(gamer, add_cfg_ids=(LUCKY_STREAK_BUFF_ID,),
                                source_index=parse_varint_field(gamer, 3) or 0)


def pvp_ghosts_after_shot(gamer: bytes, ammo_cfg_id: int) -> tuple[bytes, int]:
    """Native buff args hold this owner's partial count; reload clears it."""
    gun = parse_bytes_field(gamer, 7) or b''
    if weapon_skill_id(parse_varint_field(gun, 1) or 0) != GHOSTS_SKILL_ID or ammo_cfg_id != 300:
        return gamer, 0
    counter = next((parse_varint_field(b, 2) or 0 for b in parse_bytes_fields(gamer, 8)
                    if parse_varint_field(b, 1) == GHOSTS_BUFF_ID), 0)
    gamer = pvp_gamer_with_buffs(gamer, del_cfg_ids=(GHOSTS_BUFF_ID,))
    if counter:
        return gamer, 1
    buff = pb_message(_pvp_buff(GHOSTS_BUFF_ID, turns=-1,
        source_index=parse_varint_field(gamer, 3) or 0), pb_varint(2, 1))
    return pb_message(gamer, pb_bytes(8, buff)), 0


def pvp_consume_toxin_heal(gamer: bytes, heal: int) -> tuple[bytes, int, bool]:
    active = heal > 0 and any(parse_varint_field(b,1) == TOXIN_BUFF_ID
                             for b in parse_bytes_fields(gamer,8))
    if active:
        gamer = pvp_gamer_with_buffs(gamer, del_cfg_ids=(TOXIN_BUFF_ID,))
        heal = max(0, heal - 1)
    return gamer, heal, active


def pvp_event_with_toxin_removed(result: bytes, target: int, consumed: bool, *,
                                 event_id: int, event_time: int) -> bytes:
    if not consumed:
        return result
    outline = _pvp_event_outline(target,event_type=10,event_time=event_time,
                                 del_buffs=(_pvp_buff(TOXIN_BUFF_ID, exist_type=3),))
    event = pb_message(pb_bytes(1,outline),pb_bytes(2,outline),
                       pb_varint(3,event_id),pb_varint(4,0))
    fields=[]; inserted=False
    for n,_,_,raw in _iter_pb_fields(result):
        if n == 4 and not inserted:
            fields.append(pb_bytes(4,event)); inserted=True
        fields.append(raw)
    if not inserted: fields.append(pb_bytes(4,event))
    return pb_message(*fields)


def pvp_consume_lucky_die(gamer: bytes, raw_roll: int) -> tuple[bytes, int, bool]:
    active = any(parse_varint_field(b, 1) == LUCKY_STREAK_BUFF_ID
                 for b in parse_bytes_fields(gamer, 8))
    roll = lucky_die_result(raw_roll, active)
    if active:
        gamer = pvp_gamer_with_buffs(gamer, del_cfg_ids=(LUCKY_STREAK_BUFF_ID,))
    return gamer, roll, active


def _reload_weapon_buffs(gamer: bytes) -> tuple[bytes, ...]:
    gun = parse_bytes_field(gamer, 7) or b''
    if weapon_skill_id(parse_varint_field(gun, 1) or 0) != LITTLE_MANIAC_SKILL_ID:
        return ()
    return tuple(b for b in parse_bytes_fields(gamer, 8)
                 if parse_varint_field(b, 1) == LUCKY_STREAK_BUFF_ID)


def _append_reload_weapon_buff_event(events: list[bytes], gamer: bytes, *,
                                     event_id: int, event_time: int) -> None:
    """Reload outlines don't enter the client's UpdateBuffs branch (typ 10).

    Emit that native event separately, with the same timestamp as reload so
    its deferred callback isn't rejected as older than this HUD update.
    Source and target are the weapon owner: no target/camera redirection.
    """
    buffs = _reload_weapon_buffs(gamer)
    gun = parse_bytes_field(gamer, 7) or b''
    if weapon_skill_id(parse_varint_field(gun, 1) or 0) == ARTEMIS_SKILL_ID:
        # Native flow: show the unconverted reload first, then delayed typ12
        # with CAmmo so the client animates the blank -> live substitution.
        reload_event = events[-1]
        outline = parse_bytes_field(reload_event, 2) or b''
        ammo = {parse_varint_field(a, 1): parse_varint_field(a, 2) or 0
                for a in parse_bytes_fields(outline, 5)}
        real, blank = ammo.get(1, 0), ammo.get(300, 0)
        if real <= 0:
            return
        owner = parse_varint_field(gamer, 3) or 0
        base = (_ammo_message(300, blank + 1, 1), _ammo_message(1, real - 1, 3))
        def opening_outline(raw: bytes, target: bool) -> bytes:
            fields = [r for n, _, _, r in _iter_pb_fields(raw)
                      if n not in (5, 9, 11, 50)]
            fields.append(pb_varint(9, 1))
            if target:
                fields.extend(pb_bytes(5, a) for a in base)
            return pb_message(*fields)
        events[-1] = pb_message(
            *(pb_bytes(n, opening_outline(value, n == 2)) if n in (1, 2) and wire == 2 else raw
              for n, wire, value, raw in _iter_pb_fields(reload_event)))
        source = _pvp_event_outline(owner, event_type=12, event_time=event_time + 1)
        target = _pvp_event_outline(owner, event_type=12, event_time=event_time + 1,
            r_ammo=(_ammo_message(300, blank, 1), _ammo_message(1, real, 3)),
            c_ammo=_c_ammo_message(300, 1, 1, 1), is_gun_buff=True)
        events.append(pb_message(pb_bytes(1, source), pb_bytes(2, target),
            pb_varint(3, event_id), pb_varint(4, len(events) + 1)))
        return
    lovesong = weapon_skill_id(parse_varint_field(gun, 1) or 0) == LOVESONG_SKILL_ID
    if not buffs and not lovesong:
        return
    owner = parse_varint_field(gamer, 3) or 0
    event_type = 9 if lovesong else 10
    source = _pvp_event_outline(owner, event_type=event_type, event_time=event_time)
    target = _pvp_event_outline(owner, event_type=event_type, event_time=event_time,
                                add_buffs=buffs,
                                skill_cd=pvp_gamer_skill_cd(gamer) if lovesong else None)
    events.append(pb_message(pb_bytes(1, source), pb_bytes(2, target),
                             pb_varint(3, event_id), pb_varint(4, len(events) + 1)))


def pvp_event_with_consumed_lucky(result: bytes, actor: int, *,
                                  consumed: int, event_id: int, event_time: int) -> bytes:
    """consumed is the unmodified die (1..6), or zero when no buff was used."""
    if not consumed:
        return result
    lucky_die_result(consumed, True)
    outline = _pvp_event_outline(actor, event_type=10, event_time=event_time,
                                del_buffs=(_pvp_buff(LUCKY_STREAK_BUFF_ID),))
    removal = pb_message(pb_bytes(1, outline), pb_bytes(2, outline),
                         pb_varint(3, event_id), pb_varint(4, 0))
    fields = []
    inserted = False
    for number, wire, value, raw in _iter_pb_fields(result):
        if number == 4 and not inserted:
            fields.append(pb_bytes(4, removal))
            inserted = True
        if number == 4 and wire == 2:
            event_fields = []
            for part, part_wire, part_value, part_raw in _iter_pb_fields(value):
                if part in (1, 2) and part_wire == 2:
                    outline_fields = []
                    for key, key_wire, luck, outline_raw in _iter_pb_fields(part_value):
                        if key == 22 and key_wire == 2:
                            luck_fields = [r for k, _, _, r in _iter_pb_fields(luck) if k not in (1, 2)]
                            luck_fields.extend((pb_varint(1, consumed), pb_varint(2, 2)))
                            luck_fields.append(pb_bytes(4, _pvp_buff(LUCKY_STREAK_BUFF_ID,
                                                                    source_index=actor)))
                            outline_raw = pb_bytes(22, pb_message(*luck_fields))
                        outline_fields.append(outline_raw)
                    part_raw = pb_bytes(part, pb_message(*outline_fields))
                event_fields.append(part_raw)
            raw = pb_bytes(4, pb_message(*event_fields))
        fields.append(raw)
    if not inserted:
        fields.append(pb_bytes(4, removal))
    return pb_message(*fields)


def pvp_login_snapshot(
    gid: int,
    player_name: str,
    session: str,
    requested_mode: int,
    requested_sub_mode: int,
    hero_id: int,
    hero_model_id: int,
    hero_fashion_id: int,
    gun_id: int,
    gun_model_id: int,
    gun_fashion_id: int,
    carried_card_cfg_id: int = 0,
    show_player_coin: bool = True,
    randomize_ammo: bool = False,
    player_skill_id: int | None = None,
) -> tuple[bytes, bytes, bytes, bytes]:
    """Build the initial authoritative room snapshot for the requested mode.

    Mode 1/submode 6 is reconstructed from bundled client config: three
    combatants, 10,000 starting coins, and four deterministic configured cards.
    Other submodes retain the two-player lab room.
    """
    mode = 1
    sub_mode = requested_sub_mode if requested_mode == 1 and requested_sub_mode > 0 else 4
    has_trio_shop = requested_mode == 1 and sub_mode == 6
    starting_coin = 10_000 if has_trio_shop else 0
    carried_card_slot = pvp_carried_card_slot_body(carried_card_cfg_id)
    player = _local_pvp_gamer(
        gid,
        player_name,
        hero_id,
        hero_model_id,
        hero_fashion_id,
        gun_id,
        gun_model_id,
        gun_fashion_id,
        0,
        False,
        coin=starting_coin,
        card_slot=carried_card_slot or None,
        randomize_ammo=randomize_ammo,
        active_skill_id=player_skill_id,
    )
    bot_hero = 1 if hero_id != 1 else 0
    bot_hero_model = 2 if bot_hero == 1 else 1
    bot_hero_fashion = 201 if bot_hero == 1 else 101
    bot_gun = 1 if bot_hero == 1 else 0
    bot = _local_pvp_gamer(
        9000001,
        "Local Bot",
        bot_hero,
        bot_hero_model,
        bot_hero_fashion,
        bot_gun,
        2 if bot_gun == 1 else 1,
        10201 if bot_gun == 1 else 10101,
        1,
        True,
        coin=starting_coin,
        randomize_ammo=randomize_ammo,
    )
    extra_bot = b""
    if has_trio_shop:
        # These hero/fashion rows are present in the shipped Steam tables.
        # Choose an identity distinct from the local player and first bot.
        candidates = (
            (0, 1, 101),
            (1, 2, 201),
            (13, 3, 301),
            (14, 4, 401),
            (15, 5, 501),
        )
        used_heroes = {hero_id, bot_hero}
        extra_hero, extra_model, extra_fashion = next(
            row for row in candidates if row[0] not in used_heroes
        )
        extra_gun = 1 if extra_hero == 1 else 0
        extra_bot = _local_pvp_gamer(
            9000002,
            "Local Bot 2",
            extra_hero,
            extra_model,
            extra_fashion,
            extra_gun,
            2 if extra_gun == 1 else 1,
            10201 if extra_gun == 1 else 10101,
            2,
            True,
            coin=starting_coin,
            randomize_ammo=randomize_ammo,
        )
    shop_cards = (
        pvp_shop_card(1, 2001, 100),  # ejector
        pvp_shop_card(2, 2003, 200),  # real round
        pvp_shop_card(3, 2004, 100),  # blank round
        pvp_shop_card(4, 2008, 200),  # hallucination
    ) if has_trio_shop else ()
    bet_info = pb_message(pb_varint(1, 0), pb_varint(8, 0), pb_varint(9, 0))
    pvp_fields = [
        pb_bytes(1, session),
        pb_bytes(2, player),
        pb_bytes(2, bot),
        pb_varint(3, 0),
        pb_varint(4, 1),
        pb_varint(5, 1),
        pb_varint(6, mode),
        pb_varint(8, 1),
        pb_varint(9, 2),
        pb_varint(10, 0),
        pb_varint(12, 0),
        pb_varint(16, 0),
        pb_bytes(17, bet_info),
        pb_varint(21, sub_mode),
        pb_varint(22, 0),
        pb_varint(24, 1),
        pb_varint(25, 0),
        pb_varint(27, 0),
        pb_varint(28, 0),
        pb_varint(29, 0),
        pb_varint(30, 2),
        pb_varint(40, int(has_trio_shop)),
        pb_varint(41, 300 if has_trio_shop else 0),
    ]
    if extra_bot:
        pvp_fields.append(pb_bytes(2, extra_bot))
    pvp_fields.extend(pb_bytes(7, card) for card in shop_cards)
    if has_trio_shop or carried_card_slot:
        pvp_fields.append(pb_varint(46, 1))  # isShowCardSlot
        if show_player_coin:
            pvp_fields.append(pb_varint(47, 1))  # isShowPlayerCoin
    if has_trio_shop:
        pvp_fields.append(pb_varint(44, 1))  # isHasShootAward
        pvp_fields.append(pb_varint(48, 1))  # isShowPvpCoin
    pvp = pb_message(*pvp_fields)
    login = pb_message(pb_varint(1, gid), pb_bytes(2, pvp), pb_varint(3, 0))
    return login, pvp, player, bot


def pvp_login_body(
    gid: int,
    player_name: str,
    session: str,
    requested_mode: int,
    requested_sub_mode: int,
    hero_id: int,
    hero_model_id: int,
    hero_fashion_id: int,
    gun_id: int,
    gun_model_id: int,
    gun_fashion_id: int,
    carried_card_cfg_id: int = 0,
) -> bytes:
    """Compatibility wrapper returning only the room-login response."""
    return pvp_login_snapshot(
        gid,
        player_name,
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
    )[0]


def pvp_gamer_load_body(gid: int, pvp_info: bytes, current_time: int = 0) -> bytes:
    """GamerPvpGamerLoadS2C sent after every battle asset finishes loading.

    This is not a plain acknowledgement: the client replaces its current
    ``RouletteGameModule.pvpInfo`` with field 2 from this response.  Omitting
    it therefore leaves a fully loaded scene with no players or game mode.
    """
    return pb_message(
        pb_varint(1, gid),
        pb_bytes(2, pvp_info),
        pb_varint(4, current_time),
    )


def pvp_initial_ammo_body(pvp_info: bytes) -> bytes:
    """Notify the client that the room's initial loaded magazines are ready.

    ``NotifyPvpGamerAmmo.pvpInfo`` is consumed by the bundled client's
    ``OnGameStart`` path to populate each player's ammo display.  The optional
    reserve ``ammoBank`` is deliberately omitted until its mode-specific
    contents are reconstructed from evidence.
    """
    return pb_message(pb_bytes(1, pvp_info))


def _ammo_message(cfg_id: int, number: int, sort_id: int) -> bytes:
    return pb_message(
        pb_varint(1, cfg_id),
        pb_varint(2, max(0, number)),
        pb_varint(3, sort_id),
    )


def _c_ammo_message(
    source_cfg_id: int,
    source_number: int,
    target_cfg_id: int,
    target_number: int,
) -> bytes:
    """Encode one CAmmo replacement pair used by reload/change events."""
    return pb_message(
        pb_bytes(1, _ammo_message(
            source_cfg_id, source_number, _ammo_sort_id(source_cfg_id)
        )),
        pb_bytes(2, _ammo_message(
            target_cfg_id, target_number, _ammo_sort_id(target_cfg_id)
        )),
    )


def _ammo_sort_id(cfg_id: int) -> int:
    """Return the sort id used by the bundled ammo config."""
    if cfg_id == 1:  # 实弹 / real round
        return 3
    if cfg_id == 2:  # 强化弹 / enhanced round (Arms Voucher)
        return 4
    if cfg_id == 300:  # 虚弹 / blank round
        return 1
    if cfg_id == 301:  # 治疗弹 / healing round
        return 2
    return 1


def pvp_gamer_enhanced_count(gamer: bytes) -> int:
    return sum(parse_varint_field(a, 2) or 0
               for a in parse_bytes_fields(parse_bytes_field(gamer, 7) or b'', 2)
               if parse_varint_field(a, 1) == 2)


def _reload_ammo_messages(gamer: bytes, real: int, blank: int) -> tuple[bytes, ...]:
    enhanced = pvp_gamer_enhanced_count(gamer)
    return (_ammo_message(300, blank, 1), _ammo_message(1, real, 3),
            *((_ammo_message(2, enhanced, 4),) if enhanced else ()))


def _weapon_trait_activated(gamer: bytes) -> bool:
    gun = parse_bytes_field(gamer, 7) or b''
    skill = weapon_skill_id(parse_varint_field(gun, 1) or 0)
    return skill in (LOVESONG_SKILL_ID, ARTEMIS_SKILL_ID) or (skill == 2 and pvp_gamer_enhanced_count(gamer) > 0) or (
        skill == LITTLE_MANIAC_SKILL_ID and bool(_reload_weapon_buffs(gamer)))


def _gun_with_ammo(gun: bytes, ammo_cfg_id: int, ammo_number: int) -> bytes:
    """Update the first matching ammo stack while preserving gun metadata."""
    fields: list[bytes] = []
    replaced = False
    for number, wire_type, value, raw in _iter_pb_fields(gun):
        if number == 2 and wire_type == 2:
            cfg_id = parse_varint_field(value, 1) or ammo_cfg_id
            if cfg_id == ammo_cfg_id and not replaced:
                if cfg_id == 2 and ammo_number <= 0:
                    # The enhanced round is a temporary stack.  Once its
                    # shot is consumed, omit the zero-count stack so the HUD
                    # does not resurrect the Arms Voucher icon on the next
                    # room snapshot.
                    replaced = True
                    continue
                fields.append(
                    pb_bytes(
                        2,
                        _ammo_message(
                            cfg_id, ammo_number, _ammo_sort_id(cfg_id)
                        ),
                    )
                )
                replaced = True
                continue
        fields.append(raw)
    if not replaced and not (ammo_cfg_id == 2 and ammo_number <= 0):
        fields.insert(
            1,
            pb_bytes(
                2,
                _ammo_message(
                    ammo_cfg_id, ammo_number, _ammo_sort_id(ammo_cfg_id)
                ),
            ),
        )
    return pb_message(*fields)


def pvp_gamer_with_skill_cd(gamer: bytes, skill_cd: int) -> bytes:
    """Replace Hero.SkillCd while preserving the hero identity and outfit."""
    gamer_fields: list[bytes] = []
    for number, wire_type, value, raw in _iter_pb_fields(gamer):
        if number == 9 and wire_type == 2:
            hero_fields = [
                field_raw for field_number, _, _, field_raw in _iter_pb_fields(value)
                if field_number != 3
            ]
            hero_fields.append(pb_varint(3, max(0, int(skill_cd))))
            gamer_fields.append(pb_bytes(9, pb_message(*hero_fields)))
        else:
            gamer_fields.append(raw)
    return pb_message(*gamer_fields)


def pvp_gamer_with_event_status(gamer: bytes, event_status: int) -> bytes:
    """Set the transient animation status on a PvpGamer snapshot.

    ``RouletteGameModule.GetPlayerState`` reads ``source``/``targets`` from
    the outer PvpEventResult, whose entries are PvpGamer messages.  That
    message's eventGamerStatus is field 26 (distinct from field 63 on an
    individual PvpEventOutline).
    """
    fields: list[bytes] = []
    found = False
    for number, _wire_type, _value, raw in _iter_pb_fields(gamer):
        if number == 26:
            if not found and event_status:
                fields.append(pb_varint(26, int(event_status)))
            found = True
        else:
            fields.append(raw)
    if event_status and not found:
        fields.append(pb_varint(26, int(event_status)))
    return pb_message(*fields)


def pvp_gamer_skill_cd(gamer: bytes) -> int:
    hero = parse_bytes_field(gamer, 9) or b""
    return parse_varint_field(hero, 3) or 0


def pvp_gamer_skill_id(gamer: bytes) -> int:
    hero = parse_bytes_field(gamer, 9) or b""
    return parse_varint_field(hero, 2) or 0


def pvp_gamer_with_frenzy_cap(gamer: bytes, cap: int) -> bytes:
    """Replace only the absolute capacity; do not rewrite ammo or other state."""
    return pb_message(*(raw for number, _, _, raw in _iter_pb_fields(gamer)
                        if number != 23), pb_varint(23, max(0, cap)))


def pvp_gamer_with_state(
    gamer: bytes,
    *,
    hp: int,
    ammo_number: int,
    fake_ammo_number: int | None = None,
    enhanced_ammo_number: int | None = None,
    round_number: int,
    is_dead: bool = False,
    weapon_reloaded: bool = False,
    rank: int | None = None,
    status: int | None = None,
    burst_mode_active: bool | None = None,
    maintenance_kit_active: bool | None = None,
    burst_source_index: int = 0,
    virtual_hp: int | None = None,
    virtual_hp_cap: int | None = None,
    continue_shoot: tuple[int, int, int, int, int] | None = None,
) -> bytes:
    """Return a PvpGamer snapshot with authoritative HP/round/ammo values."""
    fields: list[bytes] = []
    found_hp = False
    found_round = False
    found_dead = False
    found_rank = False
    found_status = False
    replaced_extra: set[int] = set()
    managed_buff_states = {
        BURST_MODE_BUFF_CFG_ID: burst_mode_active,
        MAINTENANCE_KIT_BUFF_CFG_ID: maintenance_kit_active,
    }
    managed_buff_added: set[int] = set()
    for number, wire_type, value, raw in _iter_pb_fields(gamer):
        if number in (17, 19, 23) and {
            17: virtual_hp, 19: continue_shoot, 23: virtual_hp_cap,
        }[number] is not None:
            if number not in replaced_extra:
                if number == 19:
                    shot_num, coin, next_coin, state, bonus = continue_shoot
                    fields.append(pb_bytes(19, pb_message(
                        pb_varint(1, shot_num), pb_varint(2, coin),
                        pb_varint(3, next_coin), pb_varint(4, state),
                        pb_varint(5, bonus),
                    )))
                else:
                    fields.append(pb_varint(number, max(0, int(
                        virtual_hp if number == 17 else virtual_hp_cap
                    ))))
                replaced_extra.add(number)
            continue
        if wire_type == 0 and number == 4:
            fields.append(pb_varint(4, max(0, hp)))
            found_hp = True
        elif wire_type == 0 and number == 6:
            fields.append(pb_varint(6, round_number))
            found_round = True
        elif wire_type == 0 and number == 12:
            fields.append(pb_varint(12, int(is_dead)))
            found_dead = True
        elif wire_type == 0 and number == 14 and rank is not None:
            fields.append(pb_varint(14, rank))
            found_rank = True
        elif wire_type == 0 and number == 10 and status is not None:
            fields.append(pb_varint(10, status))
            found_status = True
        elif wire_type == 2 and number == 8 and (
            burst_mode_active is not None or maintenance_kit_active is not None
        ):
            buff_cfg_id = parse_varint_field(value, 1)
            if buff_cfg_id in (2015, 2016):
                # Remove a stale card cfg accidentally emitted by older code.
                continue
            active = managed_buff_states.get(buff_cfg_id)
            if active is not None:
                if buff_cfg_id in (BURST_MODE_BUFF_CFG_ID, MAINTENANCE_KIT_BUFF_CFG_ID):
                    if buff_cfg_id not in managed_buff_added and active:
                        fields.append(pb_bytes(
                            8,
                            _pvp_buff(
                                buff_cfg_id,
                                source_index=burst_source_index,
                            ),
                        ))
                        managed_buff_added.add(buff_cfg_id)
            else:
                fields.append(raw)
        elif wire_type == 2 and number == 7:
            updated_gun = _gun_with_ammo(value, 1, ammo_number)
            if fake_ammo_number is not None:
                updated_gun = _gun_with_ammo(updated_gun, 300, fake_ammo_number)
            if enhanced_ammo_number is not None:
                updated_gun = _gun_with_ammo(
                    updated_gun, 2, enhanced_ammo_number
                )
            fields.append(pb_bytes(7, updated_gun))
        else:
            fields.append(raw)
    if not found_hp:
        fields.append(pb_varint(4, max(0, hp)))
    if not found_round:
        fields.append(pb_varint(6, round_number))
    if is_dead and not found_dead:
        fields.append(pb_varint(12, 1))
    if rank is not None and not found_rank:
        fields.append(pb_varint(14, rank))
    if status is not None and not found_status:
        fields.append(pb_varint(10, status))
    for number, value in ((17, virtual_hp), (23, virtual_hp_cap)):
        if value is not None and number not in replaced_extra:
            fields.append(pb_varint(number, max(0, int(value))))
    if continue_shoot is not None and 19 not in replaced_extra:
        shot_num, coin, next_coin, state, bonus = continue_shoot
        fields.append(pb_bytes(19, pb_message(
            pb_varint(1, shot_num), pb_varint(2, coin),
            pb_varint(3, next_coin), pb_varint(4, state),
            pb_varint(5, bonus),
        )))
    for buff_cfg_id, active in managed_buff_states.items():
        if active and buff_cfg_id not in managed_buff_added:
            fields.append(pb_bytes(
                8,
                _pvp_buff(buff_cfg_id, source_index=burst_source_index),
            ))
    result = pb_message(*fields)
    return pvp_gamer_after_weapon_reload(result) if weapon_reloaded else result


def pvp_info_with_gamers(pvp_info: bytes, player: bytes, bot: bytes) -> bytes:
    """Replace the two room gamers without disturbing the rest of PvpInfo."""
    fields: list[bytes] = []
    gamer_index = 0
    for number, wire_type, value, raw in _iter_pb_fields(pvp_info):
        if number == 2 and wire_type == 2 and gamer_index < 2:
            fields.append(pb_bytes(2, player if gamer_index == 0 else bot))
            gamer_index += 1
        else:
            fields.append(raw)
    while gamer_index < 2:
        fields.append(pb_bytes(2, player if gamer_index == 0 else bot))
        gamer_index += 1
    return pb_message(*fields)


def pvp_info_with_state(
    pvp_info: bytes,
    player: bytes,
    bot: bytes,
    *,
    round_number: int,
    turn_number: int,
    current_index: int,
    status: int = 2,
    additional_gamers: tuple[bytes, ...] = (),
) -> bytes:
    """Update the authoritative room state used by the battle UI.

    The client reads the round, turn owner and current player directly from
    ``PvpInfo`` after every event.  Updating only the embedded gamers leaves
    the scene rendered but makes its aim/fire animation state lag behind the
    server.
    """
    replacements = {
        4: max(1, round_number),
        8: max(1, turn_number),
        9: status,
        10: current_index,
    }
    found: set[int] = set()
    fields: list[bytes] = []
    gamers = (player, bot, *additional_gamers)
    gamer_index = 0
    for number, wire_type, value, raw in _iter_pb_fields(pvp_info):
        if number == 2 and wire_type == 2 and gamer_index < len(gamers):
            fields.append(pb_bytes(2, gamers[gamer_index]))
            gamer_index += 1
        elif wire_type == 0 and number in replacements:
            fields.append(pb_varint(number, replacements[number]))
            found.add(number)
        else:
            fields.append(raw)
    while gamer_index < len(gamers):
        fields.append(pb_bytes(2, gamers[gamer_index]))
        gamer_index += 1
    for number in (4, 8, 9, 10):
        if number not in found:
            fields.append(pb_varint(number, replacements[number]))
    return pb_message(*fields)


def pvp_info_with_end(pvp_info: bytes, *, end_time: int = LAB_SERVER_TIME) -> bytes:
    """Mark a room as finished so the client leaves the active-round loop."""
    fields: list[bytes] = []
    found_status = False
    found_end_time = False
    found_close_time = False
    found_is_end = False
    for number, wire_type, value, raw in _iter_pb_fields(pvp_info):
        if wire_type == 0 and number == 9:
            fields.append(pb_varint(9, 4))  # PvpStatus.PvpEnd
            found_status = True
        elif wire_type == 0 and number == 14:
            fields.append(pb_varint(14, end_time))
            found_end_time = True
        elif wire_type == 0 and number == 15:
            fields.append(pb_varint(15, end_time))
            found_close_time = True
        elif wire_type == 0 and number == 25:
            fields.append(pb_varint(25, 1))  # PvpInfo.isEndPvp
            found_is_end = True
        else:
            fields.append(raw)
    if not found_status:
        fields.append(pb_varint(9, 4))
    if not found_end_time:
        fields.append(pb_varint(14, end_time))
    if not found_close_time:
        fields.append(pb_varint(15, end_time))
    if not found_is_end:
        fields.append(pb_varint(25, 1))
    return pb_message(*fields)


def pvp_next_round_body(
    gamer: bytes,
    pvp_info: bytes,
    round_number: int = 1,
    server_time: int = LAB_SERVER_TIME,
    standby_time: int = 0,
    fast_login: bool = False,
) -> bytes:
    """Notify the client which player owns the current turn.

    The official Lua path replaces its turn state only after receiving this
    notification.  A room snapshot alone is enough to render the arena but
    is not enough to enable the shoot controls.
    """
    return pb_message(
        pb_bytes(1, gamer),
        pb_varint(2, round_number),
        pb_bytes(3, pvp_info),
        pb_varint(4, server_time),
        pb_varint(5, int(fast_login)),
        pb_varint(6, server_time),
        pb_varint(7, standby_time),
    )


def pvp_event_notification_body(
    event_result: bytes,
    pvp_info: bytes,
    server_time: int = LAB_SERVER_TIME,
    stop_ai: bool = False,
) -> bytes:
    """Wrap a PvpEventResult in the official 255/2 notification payload."""
    return pb_message(
        pb_bytes(1, event_result),
        pb_bytes(2, pvp_info),
        pb_varint(3, server_time),
        pb_varint(4, int(stop_ai)),
    )


def _pvp_card_small_event(
    *,
    player_index: int,
    event_id: int,
    sub_event_id: int,
    event_time: int,
    event_type: int,
    coin_delta: int | None = None,
    coin_reason: int = 5,
    card_slot: bytes | None = None,
    card_reason: int | None = None,
    cards: tuple[bytes, ...] | list[bytes] = (),
    add_buffs: tuple[bytes, ...] | list[bytes] = (),
    del_buffs: tuple[bytes, ...] | list[bytes] = (),
    buffs: tuple[bytes, ...] | list[bytes] = (),
) -> bytes:
    """Build one PvpEvent using the client-declared PvpEventOutline fields."""
    # The shoot-skill animation iterates every small event and reads
    # event.source.typ, even for card/coin events. Omitting it raises a Lua
    # exception in ClientAnimExpression.AddOtherEvent and aborts the card use.
    source = pb_message(pb_varint(1, player_index), pb_varint(9, event_type))
    target_fields = [
        pb_varint(1, player_index),
        pb_varint(9, event_type),
        pb_varint(28, event_time),
    ]
    if coin_delta is not None:
        # ChangeCoin.coin is an increment (not an absolute balance); the Lua
        # client adds it to PvpGamer.coin. Purchases use reason 5; piggybank
        # withdrawals use reason 21 (Coin_By_Card_Coin).
        change = pb_message(pb_varint(1, coin_delta), pb_varint(2, coin_reason))
        target_fields.append(pb_bytes(4, change))
    if card_slot is not None:
        target_fields.append(pb_bytes(13, card_slot))
    if card_reason is not None:
        target_fields.append(pb_varint(48, card_reason))
    target_fields.extend(pb_bytes(25, buff) for buff in add_buffs)
    target_fields.extend(pb_bytes(24, buff) for buff in del_buffs)
    target_fields.extend(pb_bytes(3, buff) for buff in buffs)
    # PvpEventOutline.cards is field 42 in the shipped client schema. Field
    # 32 is a different field, so using it silently leaves the client's shop
    # list stale after a refresh.
    target_fields.extend(pb_bytes(42, card) for card in cards)
    target = pb_message(*target_fields)
    return pb_message(
        pb_bytes(1, source),
        pb_bytes(2, target),
        pb_varint(3, event_id),
        pb_varint(4, sub_event_id),
    )


def _pvp_buff(cfg_id: int, *, buff_id: int | None = None, turns: int = 1,
              source_index: int = 0, show_num: int = 1, exist_type: int | None = None) -> bytes:
    """Minimal Buff message accepted by the bundled name-board code.

    The original buff tables are present in the Unity bundle, but many of the
    local-only cards do not have a captured live event to recover their
    instance id from.  Use a stable, per-cfg lab id when one is not supplied:
    the client deduplicates and removes buffs by ``Buff.id``, not ``cfgId``.
    Reusing one id for different cfgIds hides or removes the wrong buff.
    """
    if cfg_id == LUCKY_STREAK_BUFF_ID:
        turns = -1  # Until the next die, not until a turn boundary.
    if buff_id is None:
        buff_id = 1_000_000 + int(cfg_id)
    return pb_message(
        pb_varint(1, cfg_id),
        pb_varint(3, buff_id),
        pb_varint(4, turns),
        pb_varint(5, turns),
        pb_varint(6, source_index),
        pb_varint(7, show_num),
        *((pb_varint(8, exist_type),) if exist_type is not None else ()),
    )


def pvp_generic_card_event_result_body(
    player: bytes,
    target: bytes,
    card: bytes,
    *,
    skill_id: int,
    target_index: int,
    event_id: int,
    event_type: int = 0,
    hp_delta: int = 0,
    virtual_hp_delta: int = 0,
    coin_delta: int | None = None,
    clear_slot: bool = True,
    new_card_slot: bytes | None = None,
    r_ammo: tuple[bytes, ...] | list[bytes] | None = None,
    c_ammo: bytes | None = None,
    u_ammo: tuple[bytes, ...] | list[bytes] = (),
    add_buff_cfg: int | None = None,
    del_buff_cfg: int | None = None,
    skill_cd: int | None = None,
    luck_roll: int | None = None,
    luck_success: bool = False,
    stolen_coin: int = 0,
    is_rpg_hit: bool | None = None,
    source_u_ammo: tuple[bytes, ...] | list[bytes] = (),
    ghosts_added_real: int = 0,
    source_virtual_hp_delta: int = 0,
    target_dead: bool = False,
    reload_ammo_after: tuple[int, int] | None = None,
    event_time: int = LAB_SERVER_TIME,
    buy: bool = False,
    add_buff_cfgs: tuple[int, ...] = (),
    target_del_buff_cfgs: tuple[int, ...] = (),
) -> bytes:
    """Build the common Buy/Use card envelope for reconstructed cards.

    Normal cards, Lucky cards, ammo replacement and RPG cards all share the
    same PvpEventResult envelope.  The small-event outline carries the
    authoritative UI delta, so the server can add a new card without making
    the client guess from an inventory-only acknowledgement.
    """
    actor_index = parse_varint_field(player, 3) or 0
    cfg_id = parse_varint_field(card, 2) or 0
    card_id = parse_varint_field(card, 1) or 0
    events: list[bytes] = []
    if coin_delta is not None:
        events.append(_pvp_card_small_event(
            player_index=actor_index, event_id=event_id, sub_event_id=1,
            event_time=event_time, event_type=4, coin_delta=coin_delta,
        ))
        if new_card_slot is not None:
            events.append(_pvp_card_small_event(
                player_index=actor_index, event_id=event_id, sub_event_id=2,
                event_time=event_time, event_type=6,
                card_slot=new_card_slot, card_reason=1,
            ))
    elif clear_slot:
        events.append(_pvp_card_small_event(
            player_index=actor_index, event_id=event_id, sub_event_id=1,
            event_time=event_time, event_type=6,
            card_slot=new_card_slot or pvp_empty_card_slot_body(),
            card_reason=CARD_EVENT_USE_REASON if new_card_slot is None else 1,
        ))
    target_type = event_type or 0
    target_kwargs: dict[str, object] = {
        "event_type": target_type,
        "event_time": event_time,
    }
    if hp_delta:
        target_kwargs["hp_delta"] = hp_delta
    if virtual_hp_delta:
        target_kwargs["virtual_hp_delta"] = virtual_hp_delta
    if target_dead:
        target_kwargs["target_dead"] = True
    if r_ammo is not None:
        target_kwargs["r_ammo"] = r_ammo
    if c_ammo is not None:
        target_kwargs["c_ammo"] = c_ammo
    if u_ammo:
        target_kwargs["u_ammo"] = u_ammo
    requested_add_buff_cfgs = tuple(dict.fromkeys(
        ((add_buff_cfg,) if add_buff_cfg is not None else ())
        + tuple(add_buff_cfgs)
    ))
    if requested_add_buff_cfgs:
        target_buffs = {
            parse_varint_field(buff, 1): buff
            for buff in parse_bytes_fields(target, 8)
        }
        target_kwargs["add_buffs"] = tuple(
            target_buffs.get(cfg_id, _pvp_buff(cfg_id))
            for cfg_id in requested_add_buff_cfgs
        )
    if del_buff_cfg is not None:
        target_kwargs["del_buffs"] = (_pvp_buff(del_buff_cfg),)
    if skill_cd is not None:
        target_kwargs["skill_cd"] = skill_cd
    if luck_roll is not None:
        target_kwargs["luck"] = pb_message(
            pb_varint(1, luck_roll), pb_varint(2, 0),
            pb_varint(3, int(luck_success)), pb_varint(5, 0),
        )
    if stolen_coin:
        if target_index == actor_index or luck_roll is None or stolen_coin < 0:
            raise ValueError("coin theft requires a rolled die and another target")
        # UseNormalCard ignores standalone Enum_Coin events. The Lucky event
        # itself is queued and applied after the die UI, so put both transfer
        # deltas in its source/target outlines.
        target_kwargs["coin_delta"] = -stolen_coin
        target_kwargs["coin_reason"] = 1  # Coin_By_Steal
    if is_rpg_hit is not None:
        target_kwargs["is_rpg_hit"] = is_rpg_hit
    # A target event is always emitted, even for a cosmetic/marker card.  The
    # client queues it in OtherEvent and then calls ShowUIChange_Small.
    source_outline = _pvp_event_outline(
        actor_index, event_type=target_type, event_time=event_time,
        is_rpg_hit=is_rpg_hit,
        u_ammo=source_u_ammo,
        virtual_hp_delta=source_virtual_hp_delta,
        coin_delta=stolen_coin if stolen_coin else None,
        coin_reason=1,
    )
    target_outline = _pvp_event_outline(target_index, **target_kwargs)
    events.append(pb_message(
        pb_bytes(1, source_outline), pb_bytes(2, target_outline),
        pb_varint(3, event_id), pb_varint(4, len(events) + 1),
    ))
    if target_del_buff_cfgs:
        # Enum_Rpg does not call UpdateBuffs: use a native buff-update event.
        removed = tuple(_pvp_buff(cfg,source_index=target_index,exist_type=3)
            for cfg in target_del_buff_cfgs)
        events.append(pb_message(
            pb_bytes(1,_pvp_event_outline(target_index,event_type=10,event_time=event_time)),
            pb_bytes(2,_pvp_event_outline(target_index,event_type=10,del_buffs=removed,event_time=event_time)),
            pb_varint(3,event_id),pb_varint(4,len(events)+1)))
    if ghosts_added_real:
        ammo = parse_bytes_fields(parse_bytes_field(player, 7) or b'', 2)
        addition = _pvp_event_outline(actor_index, 1, ghosts_added_real,
            event_type=21, include_ammo=True, r_ammo=ammo,
            is_gun_buff=True, event_time=event_time)
        events.append(pb_message(pb_bytes(1, addition), pb_bytes(2, addition),
            pb_varint(3, event_id), pb_varint(4, len(events) + 1)))
    if reload_ammo_after is not None:
        reload_real, reload_fake = reload_ammo_after
        reload_outline_source = _pvp_event_outline(
            actor_index, event_type=1, event_time=event_time + 1,
        )
        reload_outline_target = _pvp_event_outline(
            actor_index,
            event_type=1,  # Enum_Reload
            is_reload=True,
            r_ammo=_reload_ammo_messages(player, reload_real, reload_fake),
            is_gun_buff=_weapon_trait_activated(player),
            add_buffs=_reload_weapon_buffs(player),
            event_time=event_time + 1,
        )
        events.append(pb_message(
            pb_bytes(1, reload_outline_source),
            pb_bytes(2, reload_outline_target),
            pb_varint(3, event_id), pb_varint(4, len(events) + 1),
        ))
    if reload_ammo_after is not None:
        _append_reload_weapon_buff_event(events, player, event_id=event_id, event_time=event_time + 1)
    fields = [
        pb_varint(1, 7 if buy else 8),
        pb_varint(2, skill_id), pb_varint(3, actor_index),
        *(pb_bytes(4, event) for event in events),
        pb_varint(5, cfg_id), pb_varint(6, card_id),
        pb_varint(10, target_index), pb_bytes(11, target),
        pb_bytes(12, player), pb_varint(13, event_id), pb_bytes(15, card),
    ]
    return pb_message(*fields)


def pvp_hero_skill_event_result_body(
    source: bytes,
    target: bytes,
    *,
    skill_id: int,
    target_index: int,
    skill_cd: int,
    event_id: int,
    hp_delta: int = 0,
    virtual_hp_delta: int = 0,
    luck_roll: int | None = None,
    shop_cards: tuple[bytes, ...] | list[bytes] | None = None,
    exchange_effect: int | None = None,
    exchange_coin: int = 0,
    conversion_cfg: int | None = None,
    skill_add_buffs: tuple[bytes, ...] = (),
    stolen_ammo_cfg: int | None = None,
    stolen_target_reload: bool = False,
    event_time: int = LAB_SERVER_TIME,
) -> bytes:
    """Hero-skill envelope with a cooldown reset and optional HP/die effect."""
    actor_index = parse_varint_field(source, 3) or 0
    cd_event = pb_message(
        pb_bytes(1, _pvp_event_outline(actor_index, event_type=9, event_time=event_time)),
        pb_bytes(2, _pvp_event_outline(
            actor_index, event_type=9, skill_cd=skill_cd, event_time=event_time,
        )),
        pb_varint(3, event_id), pb_varint(4, 1),
    )
    events = [cd_event]
    if stolen_ammo_cfg is not None:
        # Spider's callbacks buffer pop by victim and add by recipient.
        events.append(pb_message(
            pb_bytes(1, _pvp_event_outline(target_index, event_type=13, event_time=event_time)),
            pb_bytes(2, _pvp_event_outline(target_index, event_type=13,
                u_ammo=(_ammo_message(stolen_ammo_cfg, 1, _ammo_sort_id(stolen_ammo_cfg)),),
                event_time=event_time)), pb_varint(3, event_id), pb_varint(4, len(events)+1)))
        events.append(pb_message(
            pb_bytes(1, _pvp_event_outline(actor_index, event_type=77, event_time=event_time)),
            pb_bytes(2, _pvp_event_outline(actor_index, event_type=77,
                include_ammo=True, ammo_cfg_id=stolen_ammo_cfg, ammo_num=1,
                r_ammo=parse_bytes_fields(parse_bytes_field(source, 7) or b'', 2),
                event_time=event_time)), pb_varint(3, event_id), pb_varint(4, len(events)+1)))
        if stolen_target_reload:
            events.append(pb_message(
                pb_bytes(1, _pvp_event_outline(target_index, event_type=1, event_time=event_time)),
                pb_bytes(2, _pvp_event_outline(target_index, event_type=1, is_reload=True,
                    r_ammo=parse_bytes_fields(parse_bytes_field(target, 7) or b'', 2),
                    is_gun_buff=_weapon_trait_activated(target), add_buffs=_reload_weapon_buffs(target),
                    event_time=event_time)), pb_varint(3, event_id), pb_varint(4, len(events)+1)))
            _append_reload_weapon_buff_event(events, target, event_id=event_id, event_time=event_time)
    if skill_add_buffs:
        events.append(pb_message(
            pb_bytes(1, _pvp_event_outline(target_index,event_type=10,event_time=event_time)),
            pb_bytes(2, _pvp_event_outline(target_index,event_type=10,
                add_buffs=skill_add_buffs,event_time=event_time)),
            pb_varint(3,event_id),pb_varint(4,len(events)+1)))
    if conversion_cfg is not None:
        gun = parse_bytes_field(target, 7) or b''
        events.append(pb_message(
            pb_bytes(1, _pvp_event_outline(target_index, event_type=8, event_time=event_time)),
            pb_bytes(2, _pvp_event_outline(target_index, event_type=8,
                r_ammo=parse_bytes_fields(gun, 2),
                c_ammo=_c_ammo_message(300, 1, conversion_cfg, 1), event_time=event_time)),
            pb_varint(3, event_id), pb_varint(4, len(events) + 1)))
    if shop_cards is not None:
        events.append(_pvp_card_small_event(
            player_index=actor_index, event_id=event_id, sub_event_id=2,
            event_time=event_time, event_type=38, cards=shop_cards,
        ))  # Enum_Shop: native Monkey animation callback, not refresh83.
    if luck_roll is not None:
        luck = pb_message(
            pb_varint(1, luck_roll), pb_varint(2, 0),
            pb_varint(3, int(luck_roll >= 3)), pb_varint(5, 0),
        )
        events.append(pb_message(
            pb_bytes(1, _pvp_event_outline(
                actor_index, event_type=7, event_time=event_time,
            )),
            pb_bytes(2, _pvp_event_outline(
                target_index, event_type=7, luck=luck, event_time=event_time,
            )),
            pb_varint(3, event_id), pb_varint(4, len(events) + 1),
        ))
    if exchange_effect is not None:
        # Native Deer animation reads buffEffect from Enum48; HP uses Enum61.
        events.append(pb_message(
            pb_bytes(1, _pvp_event_outline(actor_index, event_type=48, event_time=event_time)),
            pb_bytes(2, pb_message(_pvp_event_outline(actor_index,
                event_type=48, coin_delta=exchange_coin,
                coin_reason=18 if exchange_effect == 1 else 19,
                event_time=event_time), pb_varint(47, exchange_effect))),
            pb_varint(3, event_id), pb_varint(4, len(events) + 1)))
        events.append(pb_message(
            pb_bytes(1, _pvp_event_outline(actor_index, event_type=61, event_time=event_time)),
            pb_bytes(2, _pvp_event_outline(target_index, event_type=61,
                hp_delta=hp_delta, virtual_hp_delta=virtual_hp_delta, event_time=event_time)),
            pb_varint(3, event_id), pb_varint(4, len(events) + 1)))
    elif hp_delta or virtual_hp_delta:
        effect_type = 14 if virtual_hp_delta else 20 if hp_delta > 0 else 19
        events.append(pb_message(
            pb_bytes(1, _pvp_event_outline(
                actor_index, event_type=effect_type, event_time=event_time,
            )),
            pb_bytes(2, _pvp_event_outline(
                target_index, event_type=effect_type,
                hp_delta=hp_delta, virtual_hp_delta=virtual_hp_delta,
                event_time=event_time,
            )),
            pb_varint(3, event_id), pb_varint(4, len(events) + 1),
        ))
    return pb_message(
        pb_varint(1, 3),  # PvpEventEnum.type_Skill
        pb_varint(2, skill_id),
        pb_varint(3, actor_index),
        *(pb_bytes(4, event) for event in events),
        pb_varint(10, target_index),
        pb_bytes(11, target),
        pb_bytes(12, source),
        pb_varint(13, event_id),
    )


def pvp_piggybank_round_start_event_result_body(
    player: bytes,
    card_slot: bytes,
    *,
    event_id: int,
    event_time: int = LAB_SERVER_TIME,
    player_index: int = 0,
) -> bytes:
    """Notify the client of the piggybank's turn-start balance increase."""
    small_event = _pvp_card_small_event(
        player_index=player_index,
        event_id=event_id,
        sub_event_id=1,
        event_time=event_time,
        event_type=51,  # Enum_Update_Card_Arg
        card_slot=card_slot,
        card_reason=PIGGYBANK_EVENT_UPDATE_REASON,
    )
    return pb_message(
        pb_varint(1, 12),  # Type_Round_Start
        pb_varint(3, player_index),
        pb_bytes(4, small_event),
        pb_bytes(11, player),
        pb_bytes(12, player),
        pb_varint(13, event_id),
    )


def pvp_piggybank_use_event_result_body(
    player: bytes,
    card_slot: bytes,
    *,
    coin_delta: int,
    event_id: int,
    event_time: int = LAB_SERVER_TIME,
    player_index: int = 0,
) -> bytes:
    """Build the use animation, withdrawal, and consumed-slot event."""
    cfg_id = parse_varint_field(card_slot, 2) or 0
    card_id = parse_varint_field(card_slot, 1) or 0
    empty_slot = pvp_empty_card_slot_body()
    events = (
        _pvp_card_small_event(
            player_index=player_index,
            event_id=event_id,
            sub_event_id=1,
            event_time=event_time,
            event_type=50,  # Enum_Get_Card_Coin
            coin_delta=coin_delta,
            coin_reason=PIGGYBANK_EVENT_COIN_REASON,
        ),
        _pvp_card_small_event(
            player_index=player_index,
            event_id=event_id,
            sub_event_id=2,
            event_time=event_time,
            event_type=6,  # Enum_Card_Slot
            card_slot=empty_slot,
            card_reason=CARD_EVENT_USE_REASON,
        ),
    )
    fields = [
        pb_varint(1, 8),  # Type_Use_Card
        pb_varint(2, PIGGYBANK_USE_SKILL_ID),
        pb_varint(3, player_index),
        *(pb_bytes(4, event) for event in events),
        pb_varint(5, cfg_id),  # itemId
        pb_varint(6, card_id),  # uniqueId
        pb_varint(10, player_index),  # tIdx
        pb_bytes(11, player),  # targets
        pb_bytes(12, player),  # source
        pb_varint(13, event_id),
        pb_bytes(15, card_slot),
    ]
    return pb_message(*fields)


def pvp_hallucinogen_use_event_result_body(
    player: bytes,
    target: bytes,
    card_slot: bytes,
    *,
    target_index: int,
    event_id: int,
    event_time: int = LAB_SERVER_TIME,
    shot_result: bytes = b"",
) -> bytes:
    """Build a stored-Hallucinogen event with its forced shot embedded.

    The client allows cfg 2008 to target any living player, including its
    owner, and forces that target to fire at themself. It dispatches through
    ``UseCard -> StartShootOnce``; therefore the normal shot subevents must be
    part of this Type_Use_Card result, not a separate top-level Type_Shoot.
    """
    actor_index = parse_varint_field(player, 3) or 0
    cfg_id = parse_varint_field(card_slot, 2) or 0
    card_id = parse_varint_field(card_slot, 1) or 0
    skill_id = HALLUCINOGEN_SKILLS.get(cfg_id)
    if skill_id is None:
        raise ValueError(f"not a Hallucinogen card: {cfg_id}")
    clear_slot_event = _pvp_card_small_event(
        player_index=actor_index,
        event_id=event_id,
        sub_event_id=1,
        event_time=event_time,
        event_type=6,  # Enum_Card_Slot
        card_slot=pvp_empty_card_slot_body(),
        card_reason=CARD_EVENT_USE_REASON,
    )
    fields = [
        pb_varint(1, 8),  # Type_Use_Card
        pb_varint(2, skill_id),
        pb_varint(3, actor_index),
        pb_bytes(4, clear_slot_event),
        *(pb_bytes(4, event) for event in parse_bytes_fields(shot_result, 4)),
        pb_varint(5, cfg_id),
        pb_varint(6, card_id),
        *(
            [pb_varint(7, ammo_cfg_id)]
            if (ammo_cfg_id := parse_varint_field(shot_result, 7)) is not None
            else []
        ),
        *(
            [pb_varint(9, shoot_self_num)]
            if (shoot_self_num := parse_varint_field(shot_result, 9)) is not None
            else []
        ),
        pb_varint(10, target_index),
        pb_bytes(11, target),
        pb_bytes(12, player),
        pb_varint(13, event_id),
        pb_bytes(15, card_slot),
    ]
    if parse_varint_field(shot_result, 16):
        fields.append(pb_varint(16, 1))  # isEndPvp
    return pb_message(*fields)


def pvp_hallucinogen_buy_and_use_event_result_body(
    player: bytes,
    target: bytes,
    shop_card: bytes,
    *,
    coin_delta: int,
    target_index: int,
    event_id: int,
    event_time: int = LAB_SERVER_TIME,
    shot_result: bytes = b"",
) -> bytes:
    """Build the immediate-buy/use event consumed by the client's card UI.

    The client first animates the Enum_Coin event, then uses ``card`` and
    ``targets`` to show the target and dispatch ``UseCard``. As for a stored
    card, the forced self-shot's normal shot subevents live inside this same
    Type_Buy_Use_Card result.
    """
    actor_index = parse_varint_field(player, 3) or 0
    cfg_id = parse_varint_field(shop_card, 2) or 0
    shop_id = parse_varint_field(shop_card, 1) or 0
    skill_id = HALLUCINOGEN_SKILLS.get(cfg_id)
    if skill_id is None:
        raise ValueError(f"not a Hallucinogen card: {cfg_id}")
    coin_event = _pvp_card_small_event(
        player_index=actor_index,
        event_id=event_id,
        sub_event_id=1,
        event_time=event_time,
        event_type=4,  # Enum_Coin
        coin_delta=coin_delta,
        coin_reason=5,  # Coin_By_Buy_Card
    )
    fields = [
        pb_varint(1, 7),  # Type_Buy_Use_Card
        pb_varint(2, skill_id),
        pb_varint(3, actor_index),
        pb_bytes(4, coin_event),
        *(pb_bytes(4, event) for event in parse_bytes_fields(shot_result, 4)),
        pb_varint(5, cfg_id),  # itemId
        pb_varint(6, shop_id),  # uniqueId
        *(
            [pb_varint(7, ammo_cfg_id)]
            if (ammo_cfg_id := parse_varint_field(shot_result, 7)) is not None
            else []
        ),
        *(
            [pb_varint(9, shoot_self_num)]
            if (shoot_self_num := parse_varint_field(shot_result, 9)) is not None
            else []
        ),
        pb_varint(10, target_index),
        pb_bytes(11, target),
        pb_bytes(12, player),
        pb_varint(13, event_id),
        pb_bytes(15, shop_card),
    ]
    if parse_varint_field(shot_result, 16):
        fields.append(pb_varint(16, 1))  # isEndPvp
    return pb_message(*fields)


def _pvp_add_ammo_small_event(
    target_index: int,
    *,
    ammo_cfg_id: int,
    real_after: int,
    fake_after: int,
    event_id: int,
    event_time: int,
    sub_event_id: int,
    source_index: int = 0,
    enhanced_after: int = 0,
) -> bytes:
    """Enum_AddFixed_Ammo: one bullet and the full post-use magazine."""
    source = _pvp_event_outline(source_index, event_type=21, event_time=event_time)
    target = _pvp_event_outline(
        target_index,
        ammo_cfg_id=ammo_cfg_id,
        ammo_num=1,
        include_ammo=True,
        ammo_after=real_after,
        fake_ammo_after=fake_after,
        enhanced_ammo_after=enhanced_after,
        event_type=21,
        event_time=event_time,
    )
    return pb_message(
        pb_bytes(1, source),
        pb_bytes(2, target),
        pb_varint(3, event_id),
        pb_varint(4, sub_event_id),
    )


def pvp_add_ammo_card_event_result_body(
    player: bytes,
    target: bytes,
    card: bytes,
    *,
    target_index: int,
    real_after: int,
    fake_after: int,
    event_id: int,
    event_time: int = LAB_SERVER_TIME,
    coin_delta: int | None = None,
) -> bytes:
    """Animate one real/blank round from the shop or stored card slot."""
    actor_index = parse_varint_field(player, 3) or 0
    cfg_id = parse_varint_field(card, 2) or 0
    card_id = parse_varint_field(card, 1) or 0
    ammo_spec = {
        REAL_AMMO_CARD_CFG_ID: (REAL_AMMO_CARD_SKILL_ID, 1),
        FAKE_AMMO_CARD_CFG_ID: (FAKE_AMMO_CARD_SKILL_ID, 300),
    }.get(cfg_id)
    if ammo_spec is None:
        raise ValueError(f"not an add-ammo card: {cfg_id}")
    skill_id, ammo_cfg_id = ammo_spec
    events: list[bytes] = []
    if coin_delta is not None:
        events.append(_pvp_card_small_event(
            player_index=actor_index, event_id=event_id, sub_event_id=1,
            event_time=event_time, event_type=4, coin_delta=coin_delta,
        ))
    else:
        events.append(_pvp_card_small_event(
            player_index=actor_index, event_id=event_id, sub_event_id=1,
            event_time=event_time, event_type=6,
            card_slot=pvp_empty_card_slot_body(),
            card_reason=CARD_EVENT_USE_REASON,
        ))
    events.append(_pvp_add_ammo_small_event(
        target_index,
        ammo_cfg_id=ammo_cfg_id,
        real_after=real_after,
        fake_after=fake_after,
        event_id=event_id,
        event_time=event_time,
        sub_event_id=2,
        source_index=actor_index,
        enhanced_after=pvp_gamer_enhanced_count(target),
    ))
    return pb_message(
        pb_varint(1, 7 if coin_delta is not None else 8),
        pb_varint(2, skill_id),
        pb_varint(3, actor_index),
        *(pb_bytes(4, event) for event in events),
        pb_varint(5, cfg_id),
        pb_varint(6, card_id),
        pb_varint(10, target_index),
        pb_bytes(11, target),
        pb_bytes(12, player),
        pb_varint(13, event_id),
        pb_bytes(15, card),
    )


def pvp_spare_magazine_event_result_body(
    player: bytes,
    target: bytes,
    card: bytes,
    *,
    target_index: int,
    old_real: int,
    old_fake: int,
    real_after: int,
    fake_after: int,
    event_id: int,
    event_time: int = LAB_SERVER_TIME,
    coin_delta: int | None = None,
) -> bytes:
    """Animate cfg 2007's forced magazine replacement.

    The copied client consumes this skill through ``ChangeAmmo``.  It waits
    for ``Enum_Reload_And_Change_Ammo`` and then applies the full ``rAmmo``
    list, using each ``CAmmo`` pair to animate the old stacks being replaced.
    The lab has no reconstructed mode-1 reserve/ammo-bank table yet, so the
    caller supplies the deterministic local post-reload counts explicitly.
    """
    actor_index = parse_varint_field(player, 3) or 0
    cfg_id = parse_varint_field(card, 2) or 0
    card_id = parse_varint_field(card, 1) or 0
    if cfg_id != SPARE_MAGAZINE_CARD_CFG_ID:
        raise ValueError(f"not a Spare Magazine card: {cfg_id}")
    if min(old_real, old_fake, real_after, fake_after) < 0:
        raise ValueError("magazine counts cannot be negative")

    events: list[bytes] = []
    if coin_delta is not None:
        events.append(_pvp_card_small_event(
            player_index=actor_index, event_id=event_id, sub_event_id=1,
            event_time=event_time, event_type=4, coin_delta=coin_delta,
        ))
    else:
        events.append(_pvp_card_small_event(
            player_index=actor_index, event_id=event_id, sub_event_id=1,
            event_time=event_time, event_type=6,
            card_slot=pvp_empty_card_slot_body(),
            card_reason=CARD_EVENT_USE_REASON,
        ))

    replacement_pairs: list[bytes] = []
    if old_fake:
        replacement_pairs.append(
            _c_ammo_message(300, old_fake, 300, fake_after)
        )
    if old_real:
        replacement_pairs.append(
            _c_ammo_message(1, old_real, 1, real_after)
        )
    # CAmmo is repeated field 11.  Keep the source and target outlines on the
    # selected player: ChangeAmmo's ShowUIChange path updates that target,
    # while RouletteGamePlayer delays type 12 until the reload callback.
    source = _pvp_event_outline(
        target_index, event_type=12, event_time=event_time,
    )
    target_outline = _pvp_event_outline(
        target_index,
        event_type=12,
        is_reload=True,
        r_ammo=_reload_ammo_messages(target, real_after, fake_after),
        is_gun_buff=_weapon_trait_activated(target),
        add_buffs=_reload_weapon_buffs(target),
        event_time=event_time,
    )
    target_fields = list(_iter_pb_fields(target_outline))
    # Re-encode the target with each CAmmo pair.  Keeping this localized avoids
    # adding a second, subtly different event-outline encoder.
    target_outline = pb_message(
        *(raw for _, _, _, raw in target_fields),
        *(pb_bytes(11, pair) for pair in replacement_pairs),
    )
    events.append(pb_message(
        pb_bytes(1, source),
        pb_bytes(2, target_outline),
        pb_varint(3, event_id),
        pb_varint(4, 2),
    ))
    _append_reload_weapon_buff_event(events, target, event_id=event_id, event_time=event_time)
    return pb_message(
        pb_varint(1, 7 if coin_delta is not None else 8),
        pb_varint(2, SPARE_MAGAZINE_SKILL_ID),
        pb_varint(3, actor_index),
        *(pb_bytes(4, event) for event in events),
        pb_varint(5, cfg_id),
        pb_varint(6, card_id),
        pb_varint(10, target_index),
        pb_bytes(11, target),
        pb_bytes(12, player),
        pb_varint(13, event_id),
        pb_bytes(15, card),
    )


def pvp_eject_ammo_card_event_result_body(
    player: bytes,
    target: bytes,
    card: bytes,
    *,
    target_index: int,
    ejected_ammo_cfg_id: int,
    event_id: int,
    event_time: int = LAB_SERVER_TIME,
    coin_delta: int | None = None,
    reload_ammo_after: tuple[int, int] | None = None,
) -> bytes:
    """Animate cfg 2001 ejecting a round and any resulting automatic reload."""
    actor_index = parse_varint_field(player, 3) or 0
    cfg_id = parse_varint_field(card, 2) or 0
    card_id = parse_varint_field(card, 1) or 0
    skill_id = EJECT_AMMO_SKILLS.get(cfg_id)
    if skill_id is None:
        raise ValueError(f"not an eject-ammo card: {cfg_id}")
    events: list[bytes] = []
    if coin_delta is not None:
        events.append(_pvp_card_small_event(
            player_index=actor_index, event_id=event_id, sub_event_id=1,
            event_time=event_time, event_type=4, coin_delta=coin_delta,
        ))
    else:
        events.append(_pvp_card_small_event(
            player_index=actor_index, event_id=event_id, sub_event_id=1,
            event_time=event_time, event_type=6,
            card_slot=pvp_empty_card_slot_body(),
            card_reason=CARD_EVENT_USE_REASON,
        ))
    # PopAmmo buffers by event.source.Idx and completes on the target's
    # animation callback, so both small-event outlines must name the target.
    source = _pvp_event_outline(
        target_index, event_type=13, event_time=event_time,
    )
    target_outline = pb_message(
        pb_varint(1, target_index),
        pb_varint(9, 13),  # Enum_Pop_Ammo
        pb_bytes(12, _ammo_message(
            ejected_ammo_cfg_id, 1, _ammo_sort_id(ejected_ammo_cfg_id)
        )),
        pb_varint(28, event_time),
    )
    events.append(pb_message(
        pb_bytes(1, source),
        pb_bytes(2, target_outline),
        pb_varint(3, event_id),
        pb_varint(4, 2),
    ))
    if reload_ammo_after is not None:
        reload_real, reload_fake = reload_ammo_after
        reload_source = _pvp_event_outline(
            target_index, event_type=1, event_time=event_time + 1,
        )
        reload_target = _pvp_event_outline(
            target_index,
            event_type=1,  # Enum_Reload
            is_reload=True,
            r_ammo=_reload_ammo_messages(target, reload_real, reload_fake),
            is_gun_buff=_weapon_trait_activated(target),
            add_buffs=_reload_weapon_buffs(target),
            event_time=event_time + 1,
        )
        events.append(pb_message(
            pb_bytes(1, reload_source),
            pb_bytes(2, reload_target),
            pb_varint(3, event_id),
            pb_varint(4, 3),
        ))
    if reload_ammo_after is not None:
        _append_reload_weapon_buff_event(events, target, event_id=event_id, event_time=event_time + 1)
    return pb_message(
        pb_varint(1, 7 if coin_delta is not None else 8),
        pb_varint(2, skill_id),
        pb_varint(3, actor_index),
        *(pb_bytes(4, event) for event in events),
        pb_varint(5, cfg_id),
        pb_varint(6, card_id),
        pb_varint(10, target_index),
        pb_bytes(11, target),
        pb_bytes(12, player),
        pb_varint(13, event_id),
        pb_bytes(15, card),
    )


def pvp_wet_cigarette_event_result_body(
    player: bytes,
    card: bytes,
    *,
    die_roll: int,
    heal_delta: int,
    event_id: int,
    event_time: int = LAB_SERVER_TIME,
    coin_delta: int | None = None,
) -> bytes:
    """Client skill type Lucky: show d6, then apply a successful heal."""
    actor_index = parse_varint_field(player, 3) or 0
    cfg_id = parse_varint_field(card, 2) or 0
    card_id = parse_varint_field(card, 1) or 0
    skill_id = WET_CIGARETTE_SKILLS.get(cfg_id)
    if skill_id is None or not 1 <= die_roll <= 6 or heal_delta not in (0, 1):
        raise ValueError("invalid wet-cigarette event")
    success = die_roll >= 4
    if heal_delta and not success:
        raise ValueError("failed roll cannot heal")
    first = _pvp_card_small_event(
        player_index=actor_index, event_id=event_id, sub_event_id=1,
        event_time=event_time,
        event_type=4 if coin_delta is not None else 6,
        coin_delta=coin_delta,
        card_slot=pvp_empty_card_slot_body() if coin_delta is None else None,
        card_reason=CARD_EVENT_USE_REASON if coin_delta is None else None,
    )
    luck = pb_message(
        pb_varint(1, die_roll),
        pb_varint(2, 0),
        pb_varint(3, int(success)),
        pb_varint(5, 0),
    )
    luck_event = pb_message(
        pb_bytes(1, _pvp_event_outline(actor_index, event_type=7, event_time=event_time)),
        pb_bytes(2, pb_message(
            pb_varint(1, actor_index), pb_varint(9, 7),
            pb_bytes(22, luck), pb_varint(28, event_time),
        )),
        pb_varint(3, event_id), pb_varint(4, 2),
    )
    events = [first, luck_event]
    if heal_delta:
        events.append(pb_message(
            pb_bytes(1, _pvp_event_outline(actor_index, event_type=20, event_time=event_time)),
            pb_bytes(2, _pvp_event_outline(
                actor_index, hp_delta=heal_delta, event_type=20, event_time=event_time,
            )),
            pb_varint(3, event_id), pb_varint(4, 3),
        ))
    return pb_message(
        pb_varint(1, 7 if coin_delta is not None else 8),
        pb_varint(2, skill_id), pb_varint(3, actor_index),
        *(pb_bytes(4, event) for event in events),
        pb_varint(5, cfg_id), pb_varint(6, card_id),
        pb_varint(10, actor_index), pb_bytes(11, player), pb_bytes(12, player),
        pb_varint(13, event_id), pb_bytes(15, card),
    )


def pvp_buy_card_event_result_body(
    player: bytes,
    card: bytes,
    *,
    coin_delta: int,
    event_id: int,
    event_time: int = LAB_SERVER_TIME,
) -> bytes:
    """Build the coin + stored-slot event for a Typ_Buy request."""
    actor_index = parse_varint_field(player, 3) or 0
    card_slot = pvp_card_slot_body(card)
    events = (
        _pvp_card_small_event(
            player_index=actor_index,
            event_id=event_id,
            sub_event_id=1,
            event_time=event_time,
            event_type=4,  # Enum_Coin
            coin_delta=coin_delta,
        ),
        _pvp_card_small_event(
            player_index=actor_index,
            event_id=event_id,
            sub_event_id=2,
            event_time=event_time,
            event_type=6,  # Enum_Card_Slot
            card_slot=card_slot,
            card_reason=1,  # Card_Reason_Buy
        ),
    )
    return pb_message(
        pb_varint(1, 2),  # Type_Buy_Card
        pb_varint(3, actor_index),
        *(pb_bytes(4, event) for event in events),
        pb_varint(6, parse_varint_field(card, 1) or 0),
        pb_bytes(11, player),
        pb_bytes(12, player),
        pb_varint(13, event_id),
        pb_bytes(15, card),
    )


def pvp_refresh_shop_event_result_body(
    player: bytes,
    cards: tuple[bytes, ...] | list[bytes],
    *,
    coin_delta: int,
    event_id: int,
    event_time: int = LAB_SERVER_TIME,
) -> bytes:
    """Apply refreshed stock via the client's generic system-event path.

    Type_Gamer_Refresh_Shop (36) hides the fire control and enters the
    card-target animation. That path calls GetCardSkillType(itemId), but a
    shop-refresh request has no item cfgId; the client gets skill -1 and
    never applies Enum_Gamer_Refresh_Shop or restores fire. Type_System (11)
    instead runs ShowUIChange for both small events without hiding fire.
    """
    events = (
        _pvp_card_small_event(
            player_index=0,
            event_id=event_id,
            sub_event_id=1,
            event_time=event_time,
            event_type=10,  # Generic UI update: ShowUIChange skips Enum_Coin.
            coin_delta=coin_delta,
        ),
        _pvp_card_small_event(
            player_index=0,
            event_id=event_id,
            sub_event_id=2,
            event_time=event_time,
            event_type=83,  # Enum_Gamer_Refresh_Shop
            cards=cards,
        ),
    )
    return pb_message(
        pb_varint(1, 11),  # Type_System: no missing-card animation deadlock
        pb_varint(3, 0),
        *(pb_bytes(4, event) for event in events),
        pb_bytes(11, player),
        pb_bytes(12, player),
        pb_varint(13, event_id),
    )


def pvp_wanted_expiry_event_result_body(
    gamer: bytes,
    *,
    target_index: int,
    reward: int = WANTED_REWARD_R_CHIPS,
    event_id: int,
    event_time: int = LAB_SERVER_TIME,
) -> bytes:
    """Expire a mark without resetting an in-flight shot's selected target.

    Type_Behavior takes SetGamerPvpEvent's passive UI branch; Type_System
    clears selection, calls PlayerLookForward and overwrites gamerPvpEvent.
    ShowUIChange skips standalone Enum_Coin, so carry the payout on the buff
    removal outline instead. UpdatePlayerInfo applies its coin field before
    removing buffs, independent of the outline's enum.
    """
    event = _pvp_card_small_event(
            player_index=target_index,
            event_id=event_id,
            sub_event_id=1,
            event_time=event_time,
            event_type=10,  # Enum_Buff_Update
            coin_delta=reward if reward > 0 else None,
            coin_reason=WANTED_COIN_REASON,
            del_buffs=tuple(
                _pvp_buff(cfg_id)
                for cfg_id in (
                    WANTED_PARENT_BUFF_CFG_ID,
                    WANTED_REWARD_BUFF_CFG_ID,
                )
            ),
        )
    return pb_message(
        pb_varint(1, 17),  # Type_Behavior: passive, preserves shot/aim state
        pb_varint(3, target_index),
        pb_bytes(4, event),
        pb_bytes(11, gamer),
        pb_bytes(12, gamer),
        pb_varint(13, event_id),
    )


def pvp_buff_countdown_event_result_body(
    gamer: bytes,
    *,
    target_index: int,
    event_id: int,
    event_time: int = LAB_SERVER_TIME,
) -> bytes:
    """Use Enum_Gamer_Buff_Calc to update the Wanted HUD/table countdown.

    The shipped Lua updates existing instances by id and switches table effects
    using showNum. AddBuff would ignore an existing id or replay creation FX.
    Type_Behavior preserves the selected target and current animation queue.
    """
    buffs = tuple(
        buff for buff in parse_bytes_fields(gamer, 8)
        if parse_varint_field(buff, 1) in (
            WANTED_PARENT_BUFF_CFG_ID, WANTED_REWARD_BUFF_CFG_ID,
        )
    )
    event = _pvp_card_small_event(
        player_index=target_index,
        event_id=event_id,
        sub_event_id=1,
        event_time=event_time,
        event_type=25,  # Enum_Gamer_Buff_Calc / PvpEventOutline.buffs field 3
        buffs=buffs,
    )
    return pb_message(
        pb_varint(1, 17),  # Type_Behavior: passive, preserves shot/aim state
        pb_varint(3, target_index),
        pb_bytes(4, event),
        pb_bytes(11, gamer),
        pb_bytes(12, gamer),
        pb_varint(13, event_id),
    )


def pvp_passive_buff_removal_event_result_body(
    gamer: bytes, *, target_index: int, cfg_ids: tuple[int, ...],
    event_id: int, event_time: int = LAB_SERVER_TIME,
) -> bytes:
    """Expire actor-specific restrictions through the aim-preserving UI path."""
    event = _pvp_card_small_event(
        player_index=target_index, event_id=event_id, sub_event_id=1,
        event_time=event_time, event_type=10,
        del_buffs=tuple(_pvp_buff(cfg, exist_type=2 if cfg == TOXIN_BUFF_ID else None) for cfg in cfg_ids),
    )
    return pb_message(pb_varint(1, 17), pb_varint(3, target_index),
                      pb_bytes(4, event), pb_bytes(11, gamer),
                      pb_bytes(12, gamer), pb_varint(13, event_id))


def pvp_behavior_notification_body(
    index: int,
    action: int,
    target_index: int = 0,
    card_id: int = 0,
    interact: int = 0,
) -> bytes:
    """Echo the small behavior notification used by the battle UI."""
    return pb_message(
        pb_varint(1, index),
        pb_varint(2, action),
        pb_varint(3, target_index),
        pb_varint(4, card_id),
        pb_varint(5, interact),
    )


def _pvp_event_outline(
    index: int,
    ammo_cfg_id: int = 1,
    ammo_num: int = 1,
    hp_delta: int = 0,
    hp_cap_delta: int = 0,
    virtual_hp_delta: int = 0,
    *,
    virtual_hp_cap_delta: int = 0,
    coin_delta: int | None = None,
    coin_reason: int = 5,
    include_ammo: bool = False,
    ammo_after: int = 1,
    fake_ammo_after: int = 2,
    enhanced_ammo_after: int = 0,
    r_ammo: tuple[bytes, ...] | list[bytes] | None = None,
    c_ammo: bytes | None = None,
    event_type: int = 2,
    ghost_gun: bool = False,
    is_reload: bool = False,
    is_gun_buff: bool = False,
    gamer_status: int | None = None,
    is_play_hit_anim: bool = False,
    target_dead: bool = False,
    event_time: int = LAB_SERVER_TIME,
    event_gamer_status: int = 0,
    u_ammo: tuple[bytes, ...] | list[bytes] = (),
    skill_cd: int | None = None,
    luck: bytes | None = None,
    add_buffs: tuple[bytes, ...] | list[bytes] = (),
    del_buffs: tuple[bytes, ...] | list[bytes] = (),
    is_rpg_hit: bool | None = None,
    card_slot: bytes | None = None,
    card_reason: int | None = None,
    continue_shoot: tuple[int, int, int, int] | None = None,
) -> bytes:
    fields = [pb_varint(1, index)]
    if hp_delta:
        fields.append(pb_varint(2, hp_delta))
    if hp_cap_delta:
        fields.append(pb_varint(7, hp_cap_delta))
    if virtual_hp_delta:
        fields.append(pb_varint(14, virtual_hp_delta))
    if virtual_hp_cap_delta:
        fields.append(pb_varint(19, virtual_hp_cap_delta))
    if continue_shoot is not None:
        next_coin, coin, state, bonus = continue_shoot
        fields.extend((pb_varint(15, next_coin), pb_varint(16, coin),
                       pb_varint(53, state), pb_varint(54, bonus)))
    if coin_delta is not None:
        fields.append(pb_bytes(4, pb_message(
            pb_varint(1, coin_delta), pb_varint(2, coin_reason),
        )))
    if is_reload:
        fields.append(pb_varint(8, 1))
    if is_gun_buff:
        fields.append(pb_varint(50, 1))
    fields.append(pb_varint(9, event_type))
    if ghost_gun:
        fields.append(pb_varint(69, 1))
    if include_ammo:
        fields.append(
            pb_bytes(
                10,
                _ammo_message(
                    ammo_cfg_id, ammo_num, _ammo_sort_id(ammo_cfg_id)
                ),
            )
        )
        # The repeated rAmmo field is a full post-shot list, in sort order.
        if r_ammo is None:
            r_ammo = (
                _ammo_message(300, fake_ammo_after, _ammo_sort_id(300)),
                _ammo_message(1, ammo_after, _ammo_sort_id(1)),
                *((_ammo_message(2, enhanced_ammo_after, 4),)
                  if enhanced_ammo_after else ()),
            )
    if r_ammo is not None:
        fields.extend(pb_bytes(5, ammo) for ammo in r_ammo)
    if c_ammo is not None:
        fields.append(pb_bytes(11, c_ammo))
    fields.extend(pb_bytes(12, ammo) for ammo in u_ammo)
    if card_slot is not None:
        fields.append(pb_bytes(13, card_slot))
    if skill_cd is not None:
        fields.append(pb_varint(21, max(0, skill_cd)))
    if luck is not None:
        fields.append(pb_bytes(22, luck))
    fields.extend(pb_bytes(24, buff) for buff in del_buffs)
    fields.extend(pb_bytes(25, buff) for buff in add_buffs)
    if is_rpg_hit is not None:
        fields.append(pb_varint(43, int(is_rpg_hit)))
    if card_reason is not None:
        fields.append(pb_varint(48, card_reason))
    if gamer_status is not None:
        # PvpEventOutline.gamerStatus belongs only to the final source event.
        fields.append(pb_varint(18, gamer_status))
    fields.append(pb_varint(28, event_time))
    if is_play_hit_anim:
        fields.append(pb_varint(49, 1))
        fields.append(pb_varint(73, 2))  # Pvp_Gamer_Hurt_Typ_Normal
    if event_gamer_status:
        # ClientAnimExpression.GetPlayerState reads EventGamerStatus (field
        # 63), not the unrelated gamerStatus field 18.
        fields.append(pb_varint(63, event_gamer_status))
    if target_dead:
        fields.append(pb_varint(68, 1))
    return pb_message(*fields)


def pvp_shoot_event_result_body(
    source_gamer: bytes,
    target_gamer: bytes,
    source_index: int,
    target_index: int,
    *,
    ammo_cfg_id: int = 1,
    ammo_num: int = 1,
    target_hp_delta: int = -1,
    source_ammo_after: int = 1,
    source_fake_ammo_after: int = 2,
    source_enhanced_ammo_after: int | None = None,
    target_dead: bool = False,
    is_end_pvp: bool = False,
    shoot_self_num: int = 0,
    event_id: int = 1,
    is_next_round: bool = False,
    event_time: int = LAB_SERVER_TIME,
    source_event_status: int = 0,
    target_event_status: int = 0,
    additional_shots: tuple[tuple[int, int, int, int, bool], ...] = (),
    ghosts_added_real_after_shots: tuple[int, ...] = (),
    weapon_extra_shot_active: bool = False,
    toxin_applied: bool = False,
    del_buff_cfg: int | None = None,
    del_buff_cfgs: tuple[int, ...] = (),
    self_virtual_hp_delta: int = 0,
    target_virtual_hp_delta: int = 0,
    additional_virtual_hp_deltas: tuple[int, ...] = (),
    target_virtual_hp_cap_delta: int = 0,
    additional_virtual_hp_cap_deltas: tuple[int, ...] = (),
    source_virtual_hp_delta: int = 0,
    additional_source_virtual_hp_deltas: tuple[int, ...] = (),
    source_dead_after_shots: tuple[bool, ...] = (),
    continue_shoot: tuple[int, int, int, int] | None = None,
    reload_ammo_after: tuple[int, int] | None = None,
    source_coin_delta: int = 0,
    target_coin_delta: int = 0,
    coin_reason: int = WANTED_COIN_REASON,
    target_del_buff_cfgs: tuple[int, ...] = (),
) -> bytes:
    """Build a normal-shot result with the same delta semantics as the client.

    ``PvpEventOutline.hp`` is not an absolute HP value.  The official Lua
    handler adds it to the current player HP, so a real hit must carry -1
    (and a fake round carries 0).  The event also includes the full post-shot
    ammo list; without it the client cannot reconcile its visible magazine.
    """
    shot_specs = (
        (ammo_cfg_id, target_hp_delta, source_ammo_after,
         source_fake_ammo_after, target_dead),
        *additional_shots,
    )
    events: list[bytes] = []
    final_enhanced = (pvp_gamer_enhanced_count(source_gamer)
                      if reload_ammo_after is None else 0)
    if source_enhanced_ammo_after is not None:
        final_enhanced = source_enhanced_ammo_after
    for shot_number, (shot_cfg, shot_delta, real_after, fake_after, shot_dead) in enumerate(shot_specs):
        added_real = (ghosts_added_real_after_shots[shot_number]
                      if shot_number < len(ghosts_added_real_after_shots) else 0)
        is_last = shot_number == len(shot_specs) - 1
        shot_virtual_delta = (
            target_virtual_hp_delta if shot_number == 0
            else additional_virtual_hp_deltas[shot_number - 1]
            if shot_number - 1 < len(additional_virtual_hp_deltas)
            else 0
        )
        if shot_number == 0:
            shot_virtual_delta += self_virtual_hp_delta
        shot_source_virtual_delta = (
            source_virtual_hp_delta if shot_number == 0
            else additional_source_virtual_hp_deltas[shot_number - 1]
            if shot_number - 1 < len(additional_source_virtual_hp_deltas)
            else 0
        )
        source_died_on_shot = (
            source_dead_after_shots[shot_number]
            if shot_number < len(source_dead_after_shots)
            else False
        )
        source_outline = _pvp_event_outline(
            source_index,
            shot_cfg,
            ammo_num,
            ghost_gun=bool(added_real),
            is_gun_buff=(source_index == target_index and shot_cfg == 300
                and real_after + final_enhanced >= fake_after + 1
                and weapon_skill_id(parse_varint_field(parse_bytes_field(source_gamer,7) or b'',1) or 0) == 10006
            ) or (source_coin_delta > 0 and (shot_delta < 0 or shot_virtual_delta < 0) and source_index != target_index
                and weapon_skill_id(parse_varint_field(parse_bytes_field(source_gamer, 7) or b'', 1) or 0) == 10015
            ) or (weapon_extra_shot_active and shot_number == 0) or bool(added_real) or (shot_cfg == 2 and weapon_skill_id(
                parse_varint_field(parse_bytes_field(source_gamer, 7) or b'', 1) or 0
            ) == GRAZIER_SKILL_ID),
            hp_delta=0,
            virtual_hp_delta=shot_source_virtual_delta,
            coin_delta=(source_coin_delta if is_last and source_coin_delta else None),
            coin_reason=coin_reason,
            include_ammo=True,
            ammo_after=real_after,
            fake_ammo_after=fake_after,
            enhanced_ammo_after=final_enhanced + sum(
                int(spec[0] == 2) for spec in shot_specs[shot_number + 1:]),
            event_time=event_time + shot_number,
            event_gamer_status=source_event_status if is_last else 0,
        )
        target_outline = _pvp_event_outline(
            target_index,
            shot_cfg,
            ammo_num,
            hp_delta=shot_delta,
            virtual_hp_delta=shot_virtual_delta,
            virtual_hp_cap_delta=(target_virtual_hp_cap_delta if shot_number == 0
                else additional_virtual_hp_cap_deltas[shot_number - 1]
                if shot_number - 1 < len(additional_virtual_hp_cap_deltas) else 0),
            coin_delta=(target_coin_delta if is_last and target_coin_delta else None),
            coin_reason=coin_reason,
            is_play_hit_anim=shot_delta < 0 or shot_virtual_delta < 0,
            target_dead=shot_dead,
            event_time=event_time + shot_number,
            event_gamer_status=target_event_status if is_last else 0,
            del_buffs=(
                tuple(_pvp_buff(cfg_id, source_index=target_index, exist_type=3)
                    if cfg_id in (10029,10031,10047,10049) else _pvp_buff(cfg_id)
                    for cfg_id in target_del_buff_cfgs)
                if is_last else ()
            ),
            add_buffs=(_pvp_buff(TOXIN_BUFF_ID,source_index=source_index),)
                if toxin_applied and is_last else (),
        )
        events.append(pb_message(
            pb_bytes(1, source_outline),
            pb_bytes(2, target_outline),
            pb_varint(3, 0),
            pb_varint(4, shot_number),
        ))
        if shot_cfg == 300 and source_died_on_shot:
            # Firing a blank at an opponent removes Frenzy from the SHOOTER.
            # The ordinary blank-hit path suppresses the lethal animation, so
            # send the separate dead-status event for the source fighter.
            death_outline = _pvp_event_outline(
                source_index,
                event_type=PVP_UPDATE_GAMER_DEAD_STATUS_EVENT,
                event_time=event_time + shot_number + 1,
            )
            events.append(pb_message(
                pb_bytes(1, death_outline),
                pb_bytes(2, death_outline),
                pb_varint(3, 0),
                pb_varint(4, shot_number + 1),
            ))
    if reload_ammo_after is not None:
        reload_real, reload_fake = reload_ammo_after
        reload_source = _pvp_event_outline(
            source_index, event_type=1, event_time=event_time + len(shot_specs),
        )
        reload_target = _pvp_event_outline(
            source_index, event_type=1, is_reload=True,
            r_ammo=_reload_ammo_messages(source_gamer, reload_real, reload_fake),
            is_gun_buff=_weapon_trait_activated(source_gamer),
            add_buffs=_reload_weapon_buffs(source_gamer),
            event_time=event_time + len(shot_specs),
        )
        events.append(pb_message(
            pb_bytes(1, reload_source),
            pb_bytes(2, reload_target),
            pb_varint(3, 0),
            pb_varint(4, len(shot_specs)),
        ))
    if reload_ammo_after is not None:
        _append_reload_weapon_buff_event(events, source_gamer, event_id=event_id,
                                         event_time=event_time + len(shot_specs))
    # The bundled Lua holds Pvp_Prepare until this official final-source
    # event has been applied from OnFire.  gamerStatus=2 is PvpIng_Status.
    final_outline = _pvp_event_outline(
        source_index,
        event_type=3,  # PvpEventSmall.Enum_Finally_Source
        gamer_status=2,
        event_time=event_time + len(shot_specs) + int(reload_ammo_after is not None),
        continue_shoot=continue_shoot,
        del_buffs=tuple(
            _pvp_buff(cfg_id)
            for cfg_id in ((del_buff_cfg,) if del_buff_cfg is not None else ())
            + tuple(del_buff_cfgs)
        ),
    )
    final_event = pb_message(
        pb_bytes(1, final_outline),
        pb_bytes(2, final_outline),
        pb_varint(3, 0),
        pb_varint(4, 0),
    )
    result_fields = [
        pb_varint(1, 1),  # PvpEventEnum.Type_Shoot
        pb_varint(3, source_index),
        *(pb_bytes(4, event) for event in events),
        pb_bytes(4, final_event),
        pb_varint(9, shoot_self_num),
        pb_varint(10, target_index),
        pb_bytes(11, pvp_gamer_with_event_status(
            target_gamer, target_event_status,
        )),
        pb_bytes(12, pvp_gamer_with_event_status(
            source_gamer, source_event_status,
        )),
        pb_varint(13, event_id),
        pb_varint(14, int(is_next_round)),
    ]
    if source_index == target_index:
        # The client uses this repeated list to resolve the self-shot bullet
        # animation independently of source.ammo.
        for shot_number, (shot_cfg, *_rest) in reversed(list(enumerate(shot_specs))):
            result_fields.insert(3, pb_varint(7, shot_cfg))
    if is_end_pvp:
        result_fields.append(pb_varint(16, 1))
    return pb_message(*result_fields)


def pvp_collect_self_shot_event_result_body(
    gamer: bytes, coin_delta: int, *, event_id: int,
    event_time: int = LAB_SERVER_TIME,
    passive: bool = False,
) -> bytes:
    """PvpEventEnum.Type_GetShoot_Money with a credited coin delta.

    Source and target are the same player. The client skips the source outline
    for same-player events and applies only the target outline, so place both
    the credit and cleared bounty state on the target.
    """
    actor_index = parse_varint_field(gamer, 3) or 0
    outline = _pvp_event_outline(
        actor_index, event_type=15, event_time=event_time,
    )
    target = _pvp_event_outline(
        actor_index, event_type=15, event_time=event_time,
        coin_delta=coin_delta, coin_reason=2,
        continue_shoot=(0, 0, 0, 0),
    )
    event = pb_message(
        pb_bytes(1, outline), pb_bytes(2, target),
        pb_varint(3, 0), pb_varint(4, 0),
    )
    return pb_message(
        pb_varint(1, 17 if passive else 9), pb_varint(3, actor_index), pb_bytes(4, event),
        pb_bytes(11, gamer), pb_bytes(12, gamer),
        pb_varint(13, event_id),
    )


def pvp_info_body(pvp_info: bytes, current_time: int = LAB_SERVER_TIME) -> bytes:
    """GamerPvpGetPvpInfoS2C used by reconnect/refresh paths."""
    return pb_message(pb_bytes(1, pvp_info), pb_varint(2, current_time))


def pvp_end_body(pvp_info: bytes, *, is_fast_login: bool = False) -> bytes:
    """NotifyPvpEnd sent after the last shot has finished animating."""
    return pb_message(pb_bytes(1, pvp_info), pb_varint(2, int(is_fast_login)))


def pvp_gamer_dead_body(pvp_info: bytes) -> bytes:
    """NotifyPvpGamerDead used to finalize the local player's death path."""
    return pb_message(pb_bytes(1, pvp_info))


def pvp_gamer_info_body(
    gid: int, gamer: bytes, current_time: int = LAB_SERVER_TIME
) -> bytes:
    """GamerPvpGamerGetInfoS2C used by the post-shot refresh path."""
    return pb_message(
        pb_varint(1, gid),
        pb_bytes(2, gamer),
        pb_varint(3, current_time),
    )


def pvp_skip_tv_body(gid: int) -> bytes:
    return pb_message(pb_varint(1, gid))


def pvp_surrender_body(gid: int, pvp_info: bytes) -> bytes:
    """GamerPvpSurrenderS2C; the client expects the final room snapshot."""
    return pb_message(pb_varint(1, gid), pb_bytes(2, pvp_info))


def pvp_observer_count_body(gid: int) -> bytes:
    """GamerPvpGetObGamerNumS2C for an offline room with no spectators."""
    return pb_message(
        pb_varint(1, gid),
        pb_varint(2, 0),
        pb_varint(3, 0),
    )


def pvp_bet_simple_body(gid: int) -> bytes:
    """GamerObBetSimpleInfoS2C with a present, empty betting snapshot."""
    return pb_message(
        pb_varint(1, gid),
        pb_varint(2, 9_999_999),
        pb_varint(3, 0),
        pb_varint(4, 0),
    )
