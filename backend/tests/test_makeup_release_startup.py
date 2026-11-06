"""Execute the actual deployment notebook gate against the actual release catalogs."""
import ast
from copy import deepcopy
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize('fault', [None, 'missing_makeup', 'missing_hair', 'missing_nail', 'wrong_digest'])
def test_deployment_gate_covers_all_enabled_features(fault):
    book=json.loads((ROOT/'notebooks/render_kaggle_makeup_corrective_demo.ipynb').read_text(encoding='utf-8'))
    preparation=ast.parse(''.join(book['cells'][1]['source']))
    expected=ast.literal_eval(next(n.value for n in preparation.body if isinstance(n,ast.Assign)
        and any(isinstance(t,ast.Name) and t.id=='STYLE_RELEASE_EXPECTED' for t in n.targets)))
    startup=ast.parse(''.join(book['cells'][2]['source']))
    main=next(n for n in startup.body if isinstance(n,ast.FunctionDef) and n.name=='main')
    guard=next(n for n in main.body if isinstance(n,ast.If) and any(isinstance(c,ast.Constant)
        and isinstance(c.value,str) and 'Loaded facade does not match' in c.value for c in ast.walk(n)))
    release=json.loads((ROOT/'beautycore/lib/ai/style-release.json').read_text())
    capability={'release_id':release['release_id'],'manifest_sha256':release['manifest_sha256'],
        'model_styles':deepcopy(max(release['baseline_model_catalogs'],key=lambda x:len(x['hairstyle']))),
        'renderer_styles':list(release['renderer_styles'])}
    if fault=='missing_makeup': capability['model_styles']['makeup'].remove('exp_manga_lash')
    if fault=='missing_hair': capability['model_styles']['hairstyle'].remove('exp_wolf_cut')
    if fault=='missing_nail': capability['renderer_styles'].remove('exp_pink_aura')
    if fault=='wrong_digest': capability['manifest_sha256']='0'*64
    code=compile(ast.Module(body=[guard],type_ignores=[]),'actual-notebook-readiness-gate','exec')
    if fault:
        with pytest.raises(RuntimeError,match='Loaded facade'):
            exec(code,{'capabilities':capability,'expected_release':expected})
    else:
        exec(code,{'capabilities':capability,'expected_release':expected})
