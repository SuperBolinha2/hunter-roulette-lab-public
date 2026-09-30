"""Musical Barrier lifetime independent of Bucket; local self-target trio."""
from protocol import (pvp_gamer_with_buffs, pvp_gamer_with_coin_and_card,
    parse_varint_field as V, parse_bytes_fields as Bs, pb_message, pb_varint,
    pb_bytes, _pvp_event_outline, _pvp_buff)

KATIE_SKILLS = (10022, 10023, 10030, 10031)
KATIE_BUFFS = (10029, 10031, 10047, 10049)


def activate(gamer, skill, actor, guards):
    if actor in guards:
        raise ValueError('barrier already active')
    buff, reward = {10022:(10029,0),10023:(10031,2),10030:(10047,20),10031:(10049,200)}[skill]
    gamer = pvp_gamer_with_buffs(gamer, del_cfg_ids=KATIE_BUFFS)
    gamer = pvp_gamer_with_buffs(gamer, add_cfg_ids=(buff,), source_index=actor)
    guards[actor] = (buff, reward)
    return gamer


def intercept(gamers, guards, shooter, target, ammo_cfg):
    """Blank shots leave the pet intact; an enemy live impact consumes it."""
    if ammo_cfg == 300 or shooter == target or target not in guards:
        return None
    buff, _ = guards.pop(target)
    gamers[target] = pvp_gamer_with_buffs(gamers[target], del_cfg_ids=(buff,))
    return buff


def expire(gamers, guards, actor):
    """At owner's next turn; no payout after interception or defeat."""
    if actor not in guards:
        return None
    buff, reward = guards.pop(actor)
    gamer = pvp_gamer_with_buffs(gamers[actor], del_cfg_ids=(buff,))
    if (V(gamer,4) or 0) + (V(gamer,17) or 0) <= 0:
        reward = 0
    gamers[actor] = pvp_gamer_with_coin_and_card(gamer, coin=(V(gamer,5) or 0)+reward)
    return buff, reward


def expiry_packet(gamer, actor, buff, reward, event_id, event_time):
    outline = _pvp_event_outline(actor, event_type=10,
        del_buffs=(_pvp_buff(buff, source_index=actor, exist_type=2),),
        coin_delta=reward if reward else None, coin_reason=20, event_time=event_time)
    small=pb_message(pb_bytes(1,_pvp_event_outline(actor,event_type=10,event_time=event_time)),
        pb_bytes(2,outline),pb_varint(3,event_id),pb_varint(4,1))
    return pb_message(pb_varint(1,17),pb_varint(3,actor),pb_bytes(4,small),
        pb_bytes(11,gamer),pb_bytes(12,gamer),pb_varint(13,event_id))
