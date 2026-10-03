"""Count private-value matches without printing values, keys or source lines."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
private = []
for source in (ROOT / 'backend/.env', ROOT / 'beautycore/.env.local'):
    if not source.exists():
        continue
    for line in source.read_text(encoding='utf-8-sig').splitlines():
        if '=' not in line or line.lstrip().startswith('#'):
            continue
        key, value = line.split('=', 1)
        value = value.strip().strip('"\'')
        if len(value) >= 16 and any(word in key.upper() for word in ('SECRET', 'KEY', 'TOKEN', 'DATABASE', 'REMOTE_URL', 'REMOTE_ROOT')):
            private.append(value.encode())

files = [path for platform in ('android', 'web') for path in (ROOT / f'mobile/dist/{platform}').rglob('*') if path.is_file()]
matches = sum(any(value in path.read_bytes() for value in private) for path in files)
result = {'private_values_scanned': len(private), 'bundle_files_scanned': len(files), 'files_with_private_matches': matches}
(Path(__file__).parent / 'bundle-scan.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps(result))
assert private and files and matches == 0
