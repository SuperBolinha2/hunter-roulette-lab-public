"""Persistent localhost Clan foundation, not a public authenticated service.

Recovered command47 schemas/rules. Rewards and membership workflows explicitly
remain unavailable rather than returning empty success or granting fake awards.
"""
import unicodedata
from protocol import pb_message as M, pb_varint as V, pb_bytes as B
from protocol import parse_varint_field as getv, parse_bytes_field as getb

CREATE_COST = 500_000
EDIT_COST = 50_000
MIN_BASE_LEVEL = 7
MAX_MEMBERS = 6
DEFAULT_ICONS = (1, 2, 3, 4, 5, 8, 9)


class ClanError(ValueError):
    def __init__(self, code): self.code = code


def key(name): return name.strip().casefold()


def database(inventory):
    data = inventory.get('clanLab', {'version': 1, 'nextId': 10001, 'teams': {}, 'cooldowns': {}})
    if not isinstance(data, dict) or data.get('version') != 1 or not isinstance(data.get('teams'), dict):
        raise ClanError(754)  # Preserve an incompatible store instead of silently replacing it.
    return data


def own_team(inventory, account_key):
    return next((t for t in database(inventory)['teams'].values()
                 if any(m['key'] == account_key for m in t['members'])), None)


def text(raw, limit, required=False):
    try: value = unicodedata.normalize('NFKC', raw.decode('utf-8')).strip()
    except UnicodeDecodeError: raise ClanError(531)
    if (required and not value) or len(value) > limit or any(
        c in '<>' or unicodedata.category(c).startswith('C') for c in value):
        raise ClanError(531)
    return value


def member_body(member, team, ids, caller):
    return M(V(1, ids[member['key']]), V(2, int(member['key'] == team['owner'])),
             V(3, 0), V(4, 0), V(5, 0), V(6, member['level']), B(7, member['display']),
             V(8, member['joined']), V(9, 0), V(10, 0),
             V(11, int(member['key'] == caller)), V(12, member['icon']), V(15, 0), V(17, 0))


def team_body(team, ids, caller):
    cycle = M(V(1, team['created']), V(2, team['created'] + 604800),
              V(3, 0), V(4, 0), *(B(5, M(V(1, ids[m['key']]), V(2, 0), V(3, 1))) for m in team['members']))
    return M(V(1, team['id']), *(B(3, member_body(m, team, ids, caller)) for m in team['members']),
             B(4, team['name']), B(5, team['description']), V(6, team['icon']),
             B(7, M(V(1, int(team['quickJoin'])))), V(8, team['created']),
             *(B(9, M(V(1, i), V(2, 0), V(3, 0))) for i in DEFAULT_ICONS),
             B(11, cycle), V(13, 0), V(14, 0), V(17, team['lastEdit']))


def gamer_body(team):
    return M(V(1, team['id'] if team else 0), V(2, 0),
             B(3, M(V(1, 0), V(2, 0), V(3, 1), V(8, 0))),
             B(4, team['name'] if team else ''), V(5, team['icon'] if team else 0))


def list_body(team, ids):
    captain = next(m for m in team['members'] if m['key'] == team['owner'])
    return M(V(1, team['id']), V(2, team['icon']), V(3, ids[captain['key']]),
             B(4, captain['display']), B(5, M(V(1, int(team['quickJoin'])))),
             B(6, team['description']), B(7, team['name']), V(8, len(team['members'])))


def snapshot(inventory, caller, ids):
    team = own_team(inventory, caller)
    return (team_body(team, ids, caller) if team else None, gamer_body(team))


def request(inventory, caller, gid, ids, act, body, now, display):
    """Return body, notifications and mutation flag. Caller identity comes from session."""
    db = database(inventory)
    own = own_team(inventory, caller)
    notifications = []
    changed = False
    tid = getv(body, 2) or (own['id'] if own else 0)
    selected = db['teams'].get(str(tid))
    if act == 1:
        # Native list tid is pagination cursor, not a membership mutation.
        cursor = getv(body, 2) or 0
        teams = sorted(db['teams'].values(), key=lambda t: t['id'])
        page = [t for t in teams if t['id'] > cursor][:100]
        return M(V(1, gid), *(B(2, list_body(t, ids)) for t in page)), [], False
    if act == 7:
        return B(1, 'Local Hunters'), [], False
    if act in (2, 5, 6, 8):
        if selected is None: raise ClanError(369)
        if act == 2: return M(V(1, gid), B(2, list_body(selected, ids))), [], False
        if act == 5:
            return V(1, gid), [(70, B(1, team_body(selected, ids, caller)))], False
        if act == 6: return B(1, team_body(selected, ids, caller)), [], False
        return M(*(B(1, member_body(m, selected, ids, caller)) for m in selected['members'])), [], False
    if act == 17: raise ClanError(772)  # No earned reward cycle exists in this foundation.
    if act not in (4, 14, 15): raise ClanError(757)
    if int(inventory.get('homeLevel', 1)) < MIN_BASE_LEVEL: raise ClanError(784)
    if act == 4:
        if own: raise ClanError(789)
        if db.get('cooldowns', {}).get(caller, 0) > now: raise ClanError(767)
    else:
        if not own: raise ClanError(763)
        if own['owner'] != caller: raise ClanError(759)
    if act == 14:
        setting = getb(body, 2)
        if setting is None: raise ClanError(757)
        own['quickJoin'] = bool(getv(setting, 1))
        result = V(1, gid)
        team = own
    else:
        if act == 15 and own['lastEdit'] and now < own['lastEdit'] + 86400: raise ClanError(785)
        name = text(getb(body, 3) or b'', 16, True)
        description = text(getb(body, 4) or b'', 30)
        icon = getv(body, 2) or 1
        if icon not in DEFAULT_ICONS: raise ClanError(764)
        if any(t['name'].casefold() == name.casefold() and t is not own for t in db['teams'].values()):
            raise ClanError(750)
        coin = next((i for i in inventory.get('items', []) if int(i.get('id', 0)) == 102000), None)
        cost = CREATE_COST if act == 4 else EDIT_COST
        if coin is None or int(coin.get('number', 0)) < cost: raise ClanError(423)
        if act == 4:
            team = {'id': db['nextId'], 'owner': caller, 'created': now, 'lastEdit': 0,
                    'quickJoin': bool(getv(body, 5)), 'members': [
                        {'key': caller, 'account': caller, 'display': display,
                         'level': int(inventory.get('homeLevel', 1)), 'icon': int(inventory.get('avatarId', 1)), 'joined': now}]}
            db['nextId'] += 1
            db['teams'][str(team['id'])] = team
        else:
            team = own
            team['lastEdit'] = now
        team.update(name=name, description=description, icon=icon)
        coin['number'] = int(coin['number']) - cost
        result = M(B(1, team_body(team, ids, caller)), B(2, M(V(1, 102000), V(2, coin['number']))))
    inventory['clanLab'] = db
    changed = True
    notifications.extend(((74, B(1, gamer_body(team))), (70, B(1, team_body(team, ids, caller)))))
    return result, notifications, changed
