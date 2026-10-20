"""Stage the reviewed source overlay in a fresh extracted demo workspace only."""
import base64
from hashlib import sha256
import json
from pathlib import Path
import socket

FILES = frozenset({'scripts/inference_performance.py', 'scripts/unified_gate3_server.py'})

def validated(payload):
    if not isinstance(payload, dict) or set(payload) != FILES:
        raise ValueError('Unexpected optimization source inventory')
    result = {}
    for name, item in payload.items():
        if not isinstance(item, dict) or set(item) != {'data', 'sha256'}:
            raise ValueError('Invalid optimization source record')
        raw = base64.b64decode(item['data'], validate=True)
        if sha256(raw).hexdigest() != item['sha256']:
            raise ValueError('Optimization source hash differs: ' + name)
        compile(raw, name, 'exec')
        result[name] = raw
    return result

def stage_overlay(work, payload):
    work = Path(work)
    validated(payload)
    target = work / 'optimized-worker.json'
    with target.open('x', encoding='utf-8') as file:
        json.dump(payload, file)
    return target

def install_overlay(root, payload_file, output):
    root, output = Path(root), Path(output)
    for port in (8765, 8800):
        with socket.socket() as connection:
            connection.settimeout(1)
            if connection.connect_ex(('127.0.0.1', port)) == 0:
                raise RuntimeError('Do not replace source while an AI service is running')
    record = output / 'optimized-worker-release.json'
    if record.exists():
        raise RuntimeError('Optimization already installed; use a fresh session')
    payload = json.loads(Path(payload_file).read_text(encoding='utf-8'))
    sources = validated(payload)
    manifest_file = root / 'gate3_bundle.json'
    manifest = json.loads(manifest_file.read_text(encoding='utf-8'))
    # The original bootstrap verifies the entire bundle first. Check every replaced
    # file again here; never rewrite that pinned manifest or private archive.
    for name in FILES:
        target = root / name
        if name in manifest['files']:
            if sha256(target.read_bytes()).hexdigest() != manifest['files'][name]:
                raise ValueError('Original worker source differs before overlay')
        elif target.exists():
            raise ValueError('Unexpected preexisting optimization source')
    for name, raw in sources.items():
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    evidence = {'policy': 'nails-only', 'original_manifest_sha256': sha256(manifest_file.read_bytes()).hexdigest(),
                'source_sha256': {name: sha256(raw).hexdigest() for name, raw in sources.items()},
                'model_parameters_changed': False}
    record.write_text(json.dumps(evidence, indent=2), encoding='utf-8')
    print('OPTIMIZATION: Nails-only public-prompt reuse; Hair/Makeup use baseline inference.', flush=True)
    return evidence
