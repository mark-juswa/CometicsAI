"""Offline benchmark packaging/analysis checks; never loads a diffusion model."""
import ast
import base64
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from scripts.benchmark_generation_performance import summarize
from scripts.package_generation_benchmark import FILES

ROOT=Path(__file__).resolve().parents[2]
# Accepted pre-release benchmark source at984ed46; preserve its completed evidence.
ACCEPTED_SOURCE_SHA256={'scripts/inference_performance.py': '9a27f9cd9a18e222afb5fc173bc41229103ac03158484e9c91f0853e5e957174', 'scripts/unified_gate3_server.py': '98ffabc5da01dc047fc3a9a61948048abf9e455f6c75655344104e76d945c4f5', 'scripts/benchmark_generation_performance.py': 'da8cedc2e05a0d4a69ceb34c2799582bace38050f310cd4b830ea5407615a6c5', 'scripts/generation_performance_bootstrap.py': '6c58a420a265c6972424717d4ce52de7ca337c2384e682c6305e934165d607d6'}


def test_summary_reports_sample_count_repeatability_and_negative_saving_honestly():
    runs=[{'mode':mode,'wall_seconds':value,'rgb_sha256':'same'} for mode,values in [('baseline',[10.,12.,11.]),('candidate',[13.,14.,15.])] for value in values]
    result=summarize(runs)
    assert result['baseline_n']==3 and result['candidate_n']==3
    assert result['baseline_median_seconds']==11
    assert result['candidate_median_seconds']==14
    assert result['observed_median_saving_percent']<0
    assert result['candidate_matches_baseline_pixels'] and result['baseline_repeatable']
    runs[-1]['rgb_sha256']='different'
    assert not summarize(runs)['candidate_matches_baseline_pixels']
    single=summarize([runs[0],runs[3]])
    assert single['baseline_repeatable'] is None
    assert 'Single observations' in single['note']


def test_accepted_notebook_embeds_only_the_expected_reviewed_historical_source():
    book=json.loads((ROOT/'notebooks/beautycore_generation_speed_benchmark.ipynb').read_text(encoding='utf-8'))
    assert len(book['cells'])==2
    code=''.join(book['cells'][1]['source'])
    tree=ast.parse(code)
    values={node.targets[0].id:ast.literal_eval(node.value) for node in tree.body if isinstance(node,ast.Assign) and isinstance(node.targets[0],ast.Name) and node.targets[0].id in ('FILES','BUNDLE','EXPECTED')}
    assert set(values['FILES'])==set(FILES)
    for name,item in values['FILES'].items():
        raw=base64.b64decode(item['data'],validate=True)
        assert sha256(raw).hexdigest()==item['sha256']
        assert sha256(raw.replace(b'\r\n',b'\n')).hexdigest()==ACCEPTED_SOURCE_SHA256[name]
        compile(raw,name,'exec')
    assert values['BUNDLE']=='capstone_train002_20260928_v1.bin'
    assert all(not name.endswith(('.safetensors','.env','.bin','.pt')) for name in values['FILES'])


def test_cell_owns_fresh_workspaces_preserves_inputs_and_packages_only_results(tmp_path,monkeypatch):
    inputs=tmp_path/'input';inputs.mkdir()
    work=tmp_path/'working';work.mkdir()
    demo=work/'render-kaggle';demo.mkdir();(demo/'unchanged.txt').write_text('demo-stays')
    bundle=inputs/'capstone_train002_20260928_v1.bin'
    with ZipFile(bundle,'w') as z:z.writestr('scripts/original.py','# synthetic test bundle only')
    book=json.loads((ROOT/'notebooks/beautycore_generation_speed_benchmark.ipynb').read_text(encoding='utf-8'))
    code=''.join(book['cells'][1]['source'])
    code=code.replace("Path('/kaggle/input')",'Path('+repr(str(inputs))+')').replace("Path('/kaggle/working')",'Path('+repr(str(work))+')')
    code=code.replace("EXPECTED = 'f0d1fed52e00b6c5a1da2cade3731237675cdebbfc0b2cde3b2dbda99a4019ac'",'EXPECTED = '+repr(sha256(bundle.read_bytes()).hexdigest()))
    calls=[]
    def fake_child(args,cwd,check):
        assert check and Path(cwd).is_relative_to(work)
        assert args[-1].endswith('generation_performance_bootstrap.py')
        calls.append(cwd)
        results=Path(cwd).parent/'results';results.mkdir()
        (results/'report.json').write_text('{"fixture":true}')
    monkeypatch.setattr(subprocess,'run',fake_child)
    for _ in range(2):exec(compile(code,'private-benchmark-cell','exec'),{})
    assert len(calls)==2 and calls[0]!=calls[1]
    assert (demo/'unchanged.txt').read_text()=='demo-stays'
    for root in calls:
        with ZipFile(Path(root).parent/'beautycore-speed-results.zip') as z:
            assert z.namelist()==['results/report.json']
    with ZipFile(bundle) as z:assert z.namelist()==['scripts/original.py']


def test_future_worker_packages_include_its_optional_performance_dependency():
    from scripts.package_deployment01 import FILES as deployment
    from scripts.nails_latency_update import FILES as latency
    from scripts.package_unified_gate3 import NEW_FILES as unified
    for inventory in (deployment, latency, unified):
        assert 'scripts/unified_gate3_server.py' in inventory
        assert 'scripts/inference_performance.py' in inventory
