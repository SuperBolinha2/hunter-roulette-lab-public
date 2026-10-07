"""Explicit offline GM grant for the isolated copy; creates a private backup.

Never run while its game/server are active. Saves/assets are never committed.
"""
import argparse
import copy
import json
import shutil
import sys
import tempfile
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'server'))
from player_profile import ensure, grant_gm

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--game-copy-root', type=Path, required=True)
    parser.add_argument('--account', default='local')
    parser.add_argument('--display-name')
    parser.add_argument('--move-grant-from', help='Remove mistaken grant from an unused default-selection placeholder')
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    root = args.game_copy_root.resolve()
    if root.name != 'Hunter Roulette - Copia':
        raise SystemExit('Only the isolated Hunter Roulette - Copia is permitted')
    path = root / 'research/private-server/inventory.json'
    value = json.loads(path.read_text(encoding='utf-8'))
    original = copy.deepcopy(value)
    key = args.account.strip().casefold()
    if not key: raise SystemExit('Account key cannot be empty')
    profile = ensure(value, key, 'Local Hunter' if key == 'local' else args.account)
    grant_gm(profile)
    if args.display_name:
        profile['name'] = args.display_name
    if args.move_grant_from:
        source_key = args.move_grant_from.strip().casefold()
        if source_key == key: raise SystemExit('Source and destination must differ')
        source = value['profileLab']['accounts'].get(source_key)
        if source and source.get('gmAllAccessories'):
            if (source.get('icon'),source.get('frame')) != (1,1001):
                raise SystemExit('Source has a non-default selection; refusing to revoke its grant')
            source['owned'] = [1,1001]
            source['gmAllAccessories'] = False
    print('Grant: 51 avatars + 66 frames, permanent, one explicit local account.')
    if not args.execute:
        print('Preview only; pass --execute with the local server stopped.')
        return
    if value == original:
        print('Already granted; no write required.')
        return
    backup = path.parent / 'backups' / ('inventory-before-gm-accessories-' + datetime.now().strftime('%Y%m%d-%H%M%S-%f') + '.json')
    backup.parent.mkdir(exist_ok=True)
    shutil.copy2(path, backup)
    with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',dir=path.parent,delete=False,suffix='.tmp') as f:
        json.dump(value,f,ensure_ascii=False,indent=2)
        temp = Path(f.name)
    try:
        temp.replace(path)
    finally:
        temp.unlink(missing_ok=True)
    print('Private backup:', backup)

if __name__ == '__main__': main()
