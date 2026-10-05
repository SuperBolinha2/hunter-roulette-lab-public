"""Animation barriers, not HUD delays or gameplay skill cooldowns.

The client applies effects through its own animation callbacks. A following
action must not replace those callbacks. Cutscene and skillShowTime below are
native asset/config values; recovery/card margins need manual visual tuning.
"""

ACTION_DECISION_PAUSE = 0.6
ANIMATION_RECOVERY_MARGIN = 1.0
NATIVE_SKILL_SHOW_TIME = {10000: 6.0, 10003: 6.0, 10001: 4.75, 10004: 4.75,
                          10032: 4.5, 10033: 4.5,
                          10035: 4.0, 10036: 4.0,
                          10002: 3.0, 10013: 3.0, 10017: 6.0, 10018: 6.0,
                          **{s:3.0 for s in (10022,10023,10030,10031)},
                          **{s: 6.0 for s in (10020, 10021, 10024, 10025, 10026, 10027)}}
# fight_cutsceneprefab.ab, Slate.Cutscene._length at playbackSpeed=1.
# OnCutSceneFinish at 3.3 (rabbit) / 3.9 (bear) starts the separate skill
# UI timer. Sum these stages instead of maxing them or waiting only for UI.
NATIVE_SKILL_CUTSCENE_TIME = {10000: 3.4, 10003: 3.4, 10001: 4.0, 10004: 4.0,
                              10032: 0.0, 10033: 0.0,
                              10035: 0.0, 10036: 0.0,
                              10002: 4.0, 10013: 4.0, 10017: 0.0, 10018: 0.0,
                              **{s:4.0 for s in (10022,10023,10030,10031)},
                              **{s: 0.0 for s in (10020, 10021, 10024, 10025, 10026, 10027)}}
# normal_const_parameter_steam_int: card_target_show_time=2,
# card_target_show_time_expression=1. Purchase/slot animation precedes both.
CARD_TARGET_SHOW_TIME = 2.0
CARD_OPENING_MARGIN = 2.0


def skill_animation_barrier(skill_id: int) -> float:
    return NATIVE_SKILL_CUTSCENE_TIME[skill_id] + NATIVE_SKILL_SHOW_TIME[skill_id] + ANIMATION_RECOVERY_MARGIN


def card_animation_barrier(effect: str, *, stored: bool, resolver_wait: float) -> float:
    # Keep longer resolver-specific waits for shooting/reload/dice. Stored
    # cards skip coin throwing, but retain their native slot/target animation.
    opening = 1.0 if stored else CARD_OPENING_MARGIN
    effect_wait = {"energy": 1.0, "purchase_ban": 2.0, "skill_ban": 2.0,
                   "heal": 3.0, "steal": 4.0}.get(effect, 1.0)
    return max(resolver_wait, opening + CARD_TARGET_SHOW_TIME + effect_wait + ANIMATION_RECOVERY_MARGIN)
