"""Verify the web saved-look catalog against backend public styles; no AI imports."""
import ast
import json
from pathlib import Path
root = Path(__file__).resolve().parents[1]
registry = json.loads((root / 'backend/app/style_registry.json').read_text(encoding='utf-8'))
expected = {'hairstyle': {item['style_id']: item['display_name'] for item in registry['styles'] if item['support_status'] != 'disabled' and registry['adapters'][item['adapter_id']]['status'] == 'enabled'}}
for feature, source, constructor in [('makeup', 'backend/app/makeup_styles.py', 'MakeupStyle'), ('nails', 'backend/app/nails/styles.py', 'NailStyle')]:
    tree = ast.parse((root / source).read_text(encoding='utf-8'))
    expected[feature] = {ast.literal_eval(node.args[0]): ast.literal_eval(node.args[1]) for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == constructor}
actual = json.loads((root / 'beautycore/lib/business/style-catalog.json').read_text(encoding='utf-8'))
if actual != expected:
    raise SystemExit('Saved-look public catalog differs from the backend. Review and synchronize public IDs/names only.')
print('Saved-look public style IDs and names match all three backend catalogs.')
