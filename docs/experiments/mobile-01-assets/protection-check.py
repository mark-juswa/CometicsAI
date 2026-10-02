"""Inspect mobile bundle boundaries without printing any private configuration values."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[3]
mobile = ROOT / 'mobile'
bundles = list((mobile / 'dist').rglob('*.js')) + list((mobile / 'dist').rglob('*.hbc'))
if len(bundles) < 2:
    raise SystemExit('Export Android and web bundles before this check.')

private_values = []
for env_path in [ROOT / 'backend/.env', ROOT / 'beautycore/.env.local']:
    if not env_path.exists():
        continue
    for line in env_path.read_text(encoding='utf-8-sig').splitlines():
        if not line.strip() or line.lstrip().startswith('#') or '=' not in line:
            continue
        key, value = line.split('=', 1)
        value = value.strip().strip('\"\'')
        if len(value) >= 16 and any(part in key.upper() for part in ['SECRET', 'KEY', 'TOKEN', 'DATABASE', 'REMOTE_URL', 'REMOTE_ROOT']):
            private_values.append((key.strip(), value))

leaks = []
for bundle in bundles:
    raw = bundle.read_bytes()
    for key, value in private_values:
        if value.encode() in raw or value.encode('utf-16-le') in raw:
            leaks.append({'bundle': str(bundle.relative_to(mobile)), 'key': key})

source = [file for folder in ['app', 'components', 'features', 'lib', 'store', 'constants']
          for file in (mobile / folder).rglob('*') if file.suffix in ['.ts', '.tsx']]
forbidden = ['AI_REMOTE_', 'KAGGLE_API', 'GEMINI_API_KEY', 'SESSION_SECRET', 'AI_CONSULTATION_HANDLE_SECRET', 'DATABASE_URL']
source_violations = [{'file': str(file.relative_to(mobile)), 'token': token}
                     for file in source for token in forbidden if token in file.read_text(encoding='utf-8')]
protected = ['backend', 'frontend', 'beautycore', 'scripts', 'notebooks', 'data', 'START.bat', 'STOP.bat']
diff = subprocess.run(['git', 'diff', '--name-only', 'e05b832', '--', *protected], cwd=ROOT, capture_output=True, text=True, check=True)
changed = diff.stdout.splitlines()
report = {'status': 'VERIFIED' if not leaks and not source_violations and not changed else 'FAILED',
          'privateValuesChecked': len(private_values), 'secretLeaks': leaks, 'sourceBoundaryViolations': source_violations,
          'protectedPathsChanged': changed, 'baseline': 'e05b832',
          'bundles': [{'path': str(file.relative_to(mobile)), 'sha256': hashlib.sha256(file.read_bytes()).hexdigest()} for file in bundles]}
(Path(__file__).parent / 'protection-results.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print(json.dumps({key: report[key] for key in ['status', 'privateValuesChecked', 'secretLeaks', 'sourceBoundaryViolations', 'protectedPathsChanged']}))
if report['status'] != 'VERIFIED':
    raise SystemExit(1)
