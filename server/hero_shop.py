"""Monkey shop conversion shared by human and bot executors.

Native buff logic67 uses card36, count2/3, price0. Trio's corresponding
card_diffict entry is2036. Only available offers can be converted; retain
sold slots and unselected offers. Fresh IDs invalidate stale purchase requests.
"""
from protocol import parse_varint_field as V, pvp_shop_card

MONKEY_BOX_CFG = 2036


def monkey_candidates(cards):
    return [i for i, card in enumerate(cards)
            if V(card, 5) == 1 and not (V(card, 2) == MONKEY_BOX_CFG and V(card, 3) == 0)]


def monkey_convert_shop(cards, *, upgraded, next_id, rng):
    cards = list(cards)
    eligible = monkey_candidates(cards)
    selected = rng.sample(eligible, min(3 if upgraded else 2, len(eligible)))
    next_id = max(next_id, max((V(card, 1) or 0 for card in cards), default=0) + 1)
    for index in selected:
        cards[index] = pvp_shop_card(next_id, MONKEY_BOX_CFG, 0, V(cards[index], 4) or 1)
        next_id += 1
    return tuple(cards), next_id, len(selected)
