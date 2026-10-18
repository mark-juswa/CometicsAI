"""Check public names/descriptions across both approved Hair catalogs; no model imports."""
import ast
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
expected = {'hairstyle': {}}
for filename in ('style_registry.json','style_registry_train002_smoke.json'):
    registry = json.loads((ROOT/'backend/app'/filename).read_text(encoding='utf-8'))
    for item in registry['styles']:
        if item['support_status'] == 'disabled' or registry['adapters'][item['adapter_id']]['status'] != 'enabled':
            continue
        previous = expected['hairstyle'].setdefault(item['style_id'],item['display_name'])
        if previous != item['display_name']:
            raise SystemExit('Approved Hair catalogs disagree on a public style name.')
for feature,source,constructor in [('makeup','backend/app/makeup_styles.py','MakeupStyle'),('nails','backend/app/nails/styles.py','NailStyle')]:
    tree = ast.parse((ROOT/source).read_text(encoding='utf-8'))
    expected[feature] = {ast.literal_eval(n.args[0]):ast.literal_eval(n.args[1]) for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id == constructor}
actual = json.loads((ROOT/'beautycore/lib/business/style-catalog.json').read_text(encoding='utf-8'))
if set(actual) != set(expected):
    raise SystemExit('Public feature catalog differs.')
for feature,names in expected.items():
    rows=actual[feature]
    if set(rows) != set(names):
        raise SystemExit('Saved-look styles differ from the approved public registries: '+feature)
    for key,name in names.items():
        item=rows[key]
        if set(item) != {'name','description','services'} or item['name'] != name or not isinstance(item['description'],str) or not 1 <= len(item['description']) <= 240 or not isinstance(item['services'],list):
            raise SystemExit('Invalid public look metadata: '+feature+'/'+key)
print('Public look metadata matches both Hair registries, Makeup and Nails; backend model availability is unchanged.')
