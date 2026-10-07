"""Account-keyed local profile foundation; GM grants are explicit, never global.

Derived ID/type pairs from copied player_head_pic; no client assets included.
"""
import time
import unicodedata
from protocol import pb_message, pb_varint as V, pb_bytes as B

RENAME_CD = 86400
RENAME_PRICE = 10

AVATARS = tuple(range(1, 47)) + tuple(range(501, 506))
FRAMES = tuple(range(1001, 1057)) + tuple(range(1501, 1511))
CATALOG = {**dict.fromkeys(AVATARS, 1), **dict.fromkeys(FRAMES, 2)}


class ProfileError(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(str(code))


def ensure(inventory, key, display):
    root = inventory.setdefault('profileLab', {'version': 1, 'accounts': {}})
    if not isinstance(root, dict) or root.get('version') != 1 or not isinstance(root.get('accounts'), dict):
        raise ProfileError(400)
    if key not in root['accounts']:
        root['accounts'][key] = {
            'name': display, 'icon': 1, 'frame': 1001, 'country': 0,
            'owned': [1, 1001], 'gmAllAccessories': False,
            'renameFree': 1, 'lastRename': 0, 'lastCountry': 0,
        }
    return root['accounts'][key]


def grant_gm(profile):
    """Explicit local administrator grant requested by the player."""
    profile['owned'] = sorted(set(profile.get('owned', [])) | set(CATALOG))
    profile['gmAllAccessories'] = True


def accessory_body(profile, number=1):
    return pb_message(*(B(number, pb_message(V(1, i), V(2, CATALOG[i]), V(4, 0)))
                        for i in sorted(set(profile['owned'])) if i in CATALOG))


def equip(profile, accessory_id):
    if accessory_id not in CATALOG or accessory_id not in profile['owned']:
        raise ProfileError(400)
    profile['icon' if CATALOG[accessory_id] == 1 else 'frame'] = accessory_id


def accessory_notify(profile):
    return pb_message(accessory_body(profile), V(2, profile['icon']), V(3, profile['frame']))


def projected(profile, server_now, wall_now=None):
    """Keep UI cooldown coherent across restarts of the historical lab clock."""
    result = dict(profile)
    if profile.get('lastRenameWall'):
        elapsed = max(0, int((time.time() if wall_now is None else wall_now) - profile['lastRenameWall']))
        result['lastRename'] = max(0, server_now - elapsed)
    return result


def rename(inventory, key, raw, server_now, wall_now=None):
    try:
        name = raw.decode('utf-8')
    except UnicodeDecodeError:
        raise ProfileError(283)
    if not name.strip(): raise ProfileError(531)
    if name != name.strip() or any(c in '<>' or unicodedata.category(c).startswith('C') for c in name):
        raise ProfileError(283)
    # Match GlobalFunc.getStringLength: UTF8 1/2-byte char=1, 3/4-byte char=2.
    if sum(1 if len(c.encode('utf-8')) <= 2 else 2 for c in name) > 12:
        raise ProfileError(518)
    root = inventory['profileLab']['accounts']
    profile = root[key]
    if profile['name'] == name:
        raise ProfileError(511)
    folded = unicodedata.normalize('NFKC',name).casefold()
    if any(k != key and unicodedata.normalize('NFKC',p['name']).casefold() == folded for k,p in root.items()):
        raise ProfileError(256)
    wall_now = int(time.time() if wall_now is None else wall_now)
    last = profile.get('lastRename',0)
    elapsed = (max(0, wall_now-profile['lastRenameWall']) if profile.get('lastRenameWall')
               else server_now-last)
    if last and elapsed < RENAME_CD: raise ProfileError(513)
    cost = b''
    if profile.get('renameFree',0) > 0:
        profile['renameFree'] -= 1
    else:
        item = next((i for i in inventory.get('items',[]) if int(i['id']) == 103000),None)
        if item is None or int(item.get('number',0)) < RENAME_PRICE: raise ProfileError(410)
        item['number'] = int(item['number']) - RENAME_PRICE
        cost = B(1,pb_message(V(1,103000),V(2,item['number'])))
    profile.update(name=name,lastRename=server_now,lastRenameWall=wall_now)
    for team in inventory.get('clanLab',{}).get('teams',{}).values():
        for member in team['members']:
            if member['key'] == key: member['display'] = name
    return pb_message(cost,V(2,server_now)), profile


def detail_body(gid, profile, inventory, *, hero, gun, hero_skin, gun_skin, clan=None):
    # Unknown statistics remain zero; no synthetic wins or private account data.
    collection = pb_message(*(V(3, i) for i in sorted(set(profile['owned'])) if i in AVATARS),
                            *(V(4, i) for i in sorted(set(profile['owned'])) if i in FRAMES))
    data = pb_message(V(1, gid), V(2, hero), V(3, int(inventory.get('homeLevel', 1))),
        B(4, profile['name']), V(5, profile['icon']), V(6, profile['frame']),
        V(7, 0), V(8, 0), V(9, 0), V(10, 0), V(11, 1), V(13, 0), V(14, 0),
        V(16, profile['country']), V(17, 0), V(18, gun), V(19, 0), V(20, 0),
        V(22, hero_skin), V(23, gun_skin), B(25, collection), V(26, 0), V(29, 0),
        *((B(28, clan),) if clan is not None else ()))
    return pb_message(V(1, gid), B(2, data))
