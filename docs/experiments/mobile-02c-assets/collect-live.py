"""Extract only safe boundary events and redacted route/status evidence."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RUNS = [ROOT / 'beautycore/.tmp/capstone' / name for name in (
    '40b0b7e9-1063-4862-ae8d-74497e7d72f9',
    'bb6b8e3c-1d9c-4636-885e-68812865c269',
)]
SAFE = {'event', 'time_utc', 'request_id', 'correlation_id', 'feature', 'layer', 'state',
        'http_status', 'elapsed_seconds', 'remote_elapsed_seconds', 'style_id', 'attempt',
        'automatic_retry', 'response_body_sent', 'disconnect_observed', 'status', 'generator', 'nails_path'}
events, routes = [], []
for line in (line for run in RUNS for line in (run / 'backend.log').read_text(encoding='utf-8', errors='replace').splitlines()):
    start = line.find('{')
    if start >= 0:
        try:
            value = json.loads(line[start:])
            if isinstance(value, dict) and value.get('event'):
                events.append({k: v for k, v in value.items() if k in SAFE})
        except (ValueError, TypeError):
            pass
    match = re.search(r'"(GET|POST|PUT|PATCH) (/consultations[^ ]*) HTTP/1.1" (\d{3})', line)
    if match:
        method, route, status = match.groups()
        route = re.sub(r'[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}', '{consultation}', route)
        route = re.sub(r'/rec-[0-9a-f]+/', '/{recommendation}/', route)
        routes.append({'method': method, 'route': route, 'http_status': int(status)})
application = []
for line in (line for run in RUNS for line in (run / 'beautycore.log').read_text(encoding='utf-8', errors='replace').splitlines()):
    match = re.search(r'(GET|POST|PUT|PATCH) (/api/(?:ai|auth)/[^ ]+) (\d{3}) in ([0-9.]+)(ms|s)', line)
    if match:
        method, route, status, elapsed, unit = match.groups()
        route = re.sub(r'/rec-[0-9a-f]+/', '/{recommendation}/', route)
        application.append({'method': method, 'route': route, 'http_status': int(status), 'elapsed_seconds': round(float(elapsed) / (1000 if unit == 'ms' else 1), 3)})
report = {'source': 'two successive private launcher sessions; allowlisted status and timing only', 'server_events': events, 'consultation_routes': routes, 'application_routes': application}
(Path(__file__).parent / 'live-requests.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps({'consultation_routes': routes[-12:], 'remote_events': [e for e in events if e.get('layer') == 'remote'][-8:]}))
