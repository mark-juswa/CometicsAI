"""Verified CPU update installer for the separate Kaggle backup notebook."""
import base64
from hashlib import sha256
import json
from pathlib import Path


def install_cpu_update(work, payload, inventory):
    work = Path(work).resolve()
    root = (work / 'cpu-src').resolve()
    receipt = work / 'photo-check-update.json'
    if receipt.exists():
        raise RuntimeError('CPU update already installed; use a fresh setup')
    if set(payload) != set(inventory):
        raise ValueError('CPU update inventory differs')
    prepared = []
    for name, expected in inventory.items():
        target = (root / name).resolve()
        if not target.is_relative_to(root) or ':' in name or '\\' in name:
            raise ValueError('Unsafe CPU update path')
        raw = base64.b64decode(payload[name], validate=True)
        if sha256(raw).hexdigest() != expected:
            raise ValueError('CPU update hash differs')
        if name.endswith('.py'):
            compile(raw, name, 'exec')
        prepared.append((target, raw))
    # Validate the entire inventory before changing any staged application file.
    for target, raw in prepared:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    receipt.write_text(json.dumps({'schema': 'beautycore-photo-check-update-v1',
        'files': inventory, 'model_weights_changed': False}, indent=2))
