"""Allowlist and credential-pattern guardrail; never print secret contents."""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULES = json.loads((ROOT / 'tools/Modules.json').read_text(encoding='utf-8'))
ROOT_FILES = {'.gitignore','.gitattributes','README.md','CONTRIBUTING.md','SECURITY.md'}
secret = re.compile(r'(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{30,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)')


def allowed(path):
    p = Path(path)
    name = p.name
    if any(part in {'.local','runtime','backups','__pycache__','rollback','Game','RLLaunch','lua-extract','config-extract'} for part in p.parts):
        return False
    if path in ROOT_FILES or path == '.github/workflows/test.yml':
        return True
    if path == 'server/inventory.example.json' or path in {'server/'+m for m in MODULES}:
        return True
    if path.startswith('server/tests/') and name.startswith('test_') and p.suffix == '.py':
        return True
    if path.startswith('docs/') and p.suffix == '.md':
        return True
    return path == 'tools/hooks/pre-push' or (path.startswith('tools/') and p.suffix in {'.py','.ps1','.json'})


def audit(paths):
    errors=[]
    for rel in paths:
        if not allowed(rel):
            errors.append(f'Excluded file: {rel}')
            continue
        p=ROOT / rel
        if p.is_symlink() or p.resolve().parent != p.parent.resolve():
            errors.append(f'Symlink refused: {rel}')
            continue
        if not p.is_file():
            continue  # A staged deletion is not a leaked file.
        try:
            body=p.read_text(encoding='utf-8-sig')
        except UnicodeError:
            errors.append(f'Non-text file: {rel}')
            continue
        if secret.search(body):
            errors.append(f'Possible credential detected: {rel}')
    return errors


if __name__ == '__main__':
    if (ROOT/'.git').exists():
        result=subprocess.run(['git','ls-files','-z','--cached','--others','--exclude-standard'],cwd=ROOT,capture_output=True,check=True)
        paths=sorted(set(result.stdout.decode('utf-8').rstrip('\0').split('\0')))
    else:
        paths=[p.relative_to(ROOT).as_posix() for p in ROOT.rglob('*') if p.is_file()
               and not any(part in {'.local','runtime','backups','__pycache__','.git'} for part in p.relative_to(ROOT).parts)]
    errors=audit([p for p in paths if p])
    if (ROOT/'.git').exists():
        staged=subprocess.run(['git','diff','--cached','--no-ext-diff','--unified=0'],cwd=ROOT,capture_output=True,check=True)
        if secret.search(staged.stdout.decode('utf-8','replace')):
            errors.append('Possible credential in staged patch; contents withheld.')
    for error in errors: print(error,file=sys.stderr)
    print(f'Sharing audit: {len(paths)} candidate files, {len(errors)} problems.')
    sys.exit(bool(errors))
