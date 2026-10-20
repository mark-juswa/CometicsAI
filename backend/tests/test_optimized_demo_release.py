"""Release packaging/integrity tests; no Kaggle, model weights or credentials."""
import ast
import base64
from hashlib import sha256
import json
from pathlib import Path
from unittest.mock import patch
import pytest
from scripts.optimized_demo_overlay import FILES, install_overlay, stage_overlay, validated
ROOT=Path(__file__).resolve().parents[2]

def payload():
    return {name:{'data':base64.b64encode((ROOT/name).read_bytes()).decode(),'sha256':sha256((ROOT/name).read_bytes()).hexdigest()} for name in FILES}

def fixture(tmp_path):
    root=tmp_path/'gpu-src';(root/'scripts').mkdir(parents=True)
    original=b'# original pinned source\n'
    (root/'scripts/unified_gate3_server.py').write_bytes(original)
    manifest={'files':{'scripts/unified_gate3_server.py':sha256(original).hexdigest()}}
    (root/'gate3_bundle.json').write_text(json.dumps(manifest))
    work=tmp_path/'session';work.mkdir();out=work/'gpu-session';out.mkdir()
    staged=stage_overlay(work,payload())
    return root,staged,out

def test_release_notebook_embeds_current_source_and_preserves_original_fallback():
    book=json.loads((ROOT/'notebooks/render_kaggle_optimized_demo.ipynb').read_text())
    code=[cell for cell in book['cells'] if cell['cell_type']=='code']
    assert len(code)==3
    for cell in code:
        assert cell['execution_count'] is None and cell['outputs']==[]
        compile(''.join(cell['source']),'<notebook>','exec')
    tree=ast.parse(''.join(code[0]['source']))
    value=next(node.value for node in ast.walk(tree) if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='OPTIMIZED_SOURCES' for t in node.targets))
    embedded=validated(ast.literal_eval(value))
    for name in FILES:
        assert embedded[name].replace(b'\r\n',b'\n')==(ROOT/name).read_bytes().replace(b'\r\n',b'\n')
    main=ast.parse(''.join(code[1]['source']))
    gpu=next(node.value for node in ast.walk(main) if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='gpu_code' for t in node.targets))
    source=eval(compile(ast.Expression(gpu),'<gpu-expression>','eval'),{'WORK':Path('/kaggle/working/fixture')})
    compile(source,'<worker-startup>','exec')
    assert "original.verify_bundle()" in source and "AI_PROMPT_CACHE_SCOPE='nails'" in source
    assert source.index('original.verify_bundle()')<source.index('install_overlay')<source.index('return start')
    assert "AI_INFERENCE_PROFILE='0'" in source
    old=json.loads((ROOT/'notebooks/render_kaggle_client_demo.ipynb').read_text())
    assert 'install_overlay' not in ''.join(''.join(cell['source']) for cell in old['cells'])

def test_overlay_checks_all_sources_before_write_and_retains_original_manifest(tmp_path):
    root,staged,out=fixture(tmp_path);before=(root/'gate3_bundle.json').read_bytes()
    with patch('scripts.optimized_demo_overlay.socket.socket') as factory:
        factory.return_value.__enter__.return_value.connect_ex.return_value=1
        result=install_overlay(root,staged,out)
    assert result['policy']=='nails-only'
    assert (root/'gate3_bundle.json').read_bytes()==before
    for name in FILES:assert (root/name).read_bytes()==(ROOT/name).read_bytes()
    assert (out/'optimized-worker-release.json').is_file()
    with patch('scripts.optimized_demo_overlay.socket.socket') as factory:
        factory.return_value.__enter__.return_value.connect_ex.return_value=1
        with pytest.raises(RuntimeError,match='already installed'):install_overlay(root,staged,out)

def test_tampered_overlay_and_wrong_inventory_rejected_before_write(tmp_path):
    root,staged,out=fixture(tmp_path)
    body=json.loads(staged.read_text());body['scripts/inference_performance.py']['sha256']='0'*64;staged.write_text(json.dumps(body))
    with patch('scripts.optimized_demo_overlay.socket.socket') as factory:
        factory.return_value.__enter__.return_value.connect_ex.return_value=1
        with pytest.raises(ValueError,match='hash'):install_overlay(root,staged,out)
    assert (root/'scripts/unified_gate3_server.py').read_bytes()==b'# original pinned source\n'
    with pytest.raises(ValueError,match='inventory'):validated({'../escape':{}})

def test_running_services_and_changed_original_source_block_installation(tmp_path):
    root,staged,out=fixture(tmp_path)
    with patch('scripts.optimized_demo_overlay.socket.socket') as factory:
        factory.return_value.__enter__.return_value.connect_ex.return_value=0
        with pytest.raises(RuntimeError,match='running'):install_overlay(root,staged,out)
    (root/'scripts/unified_gate3_server.py').write_text('# unexpected')
    with patch('scripts.optimized_demo_overlay.socket.socket') as factory:
        factory.return_value.__enter__.return_value.connect_ex.return_value=1
        with pytest.raises(ValueError,match='Original worker'):install_overlay(root,staged,out)
    assert not (root/'scripts/inference_performance.py').exists()
