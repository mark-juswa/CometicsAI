"""Generate a self-contained private Kaggle notebook; includes source, never weights/secrets."""
import base64
from hashlib import sha256
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
FILES=('scripts/inference_performance.py','scripts/unified_gate3_server.py',
       'scripts/benchmark_generation_performance.py','scripts/generation_performance_bootstrap.py')
BUNDLE='capstone_train002_20260928_v1.bin'
BUNDLE_SHA='f0d1fed52e00b6c5a1da2cade3731237675cdebbfc0b2cde3b2dbda99a4019ac'


def build():
    payload={name:{'data':base64.b64encode((ROOT/name).read_bytes()).decode('ascii'),
                   'sha256':sha256((ROOT/name).read_bytes()).hexdigest()} for name in FILES}
    cell="""# Private benchmark only: no public tunnel, website registration or API Secrets.
from pathlib import Path
from hashlib import sha256
from zipfile import ZipFile, ZIP_DEFLATED
import base64, json, subprocess, sys, uuid
FILES = __FILES__
BUNDLE = __BUNDLE__
EXPECTED = __SHA__
inputs = list(Path('/kaggle/input').rglob(BUNDLE))
assert len(inputs)==1, 'Attach exactly one copy of the existing private expanded GPU bundle.'
source=inputs[0]
assert sha256(source.read_bytes()).hexdigest()==EXPECTED, 'Approved bundle hash differs.'
work=Path('/kaggle/working')/('beautycore-speed-'+uuid.uuid4().hex[:10])
root=work/'gpu-src'
root.mkdir(parents=True)
with ZipFile(source) as archive:
    assert len(archive.namelist())==len(set(archive.namelist())), 'Duplicate archive member.'
    assert archive.testzip() is None, 'Private bundle CRC differs.'
    for name in archive.namelist():
        target=(root/name).resolve()
        assert ':' not in name and chr(92) not in name and target.is_relative_to(root.resolve()), 'Unsafe bundle path.'
        if name.endswith('/'):
            target.mkdir(parents=True,exist_ok=True)
            continue
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(archive.read(name))
overlay=work/'overlay'
for name,item in FILES.items():
    raw=base64.b64decode(item['data'],validate=True)
    assert sha256(raw).hexdigest()==item['sha256'], 'Benchmark source hash differs.'
    target=overlay/name
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_bytes(raw)
(work/'candidate.json').write_text(json.dumps({name:{'sha256':item['sha256']} for name,item in FILES.items()},indent=2))
# Original bundle verification runs before source overlay; each run has its own owned folder.
bootstrap=root/'scripts/generation_performance_bootstrap.py'
bootstrap.write_bytes((overlay/'scripts/generation_performance_bootstrap.py').read_bytes())
print('BENCHMARK_WORKSPACE:',work,flush=True)
print('Select GPU T4 and enable Internet. The setup keeps model/runtime pins; a host mismatch stops before inference.',flush=True)
subprocess.run([sys.executable,str(bootstrap)],cwd=root,check=True)
result=work/'beautycore-speed-results.zip'
with ZipFile(result,'x',ZIP_DEFLATED) as archive:
    for file in sorted((work/'results').glob('*')):
        if file.is_file():archive.write(file,'results/'+file.name)
print('DOWNLOAD_RESULTS:',result,flush=True)
print('Keep the notebook private. Return report.json and the comparison outputs; the working website notebook was not changed.',flush=True)
"""
    cell=cell.replace('__FILES__',repr(payload)).replace('__BUNDLE__',repr(BUNDLE)).replace('__SHA__',repr(BUNDLE_SHA))
    notebook={'nbformat':4,'nbformat_minor':5,'metadata':{'kernelspec':{'name':'python3','display_name':'Python 3','language':'python'},'language_info':{'name':'python'}},
      'cells':[{'cell_type':'markdown','metadata':{},'source':[
        '# BeautyCore private generation speed benchmark\n',
        'Run in a **new private notebook** with T4 GPU and Internet. Attach the existing private dataset containing `'+BUNDLE+'`. No Secrets, public tunnel or Render changes. Do not run inside the demo notebook.\n',
        'The setup refuses a runtime that differs from the reviewed GPU environment. It downloads the pinned Base and runs paired measurements with the same model/adapter/seed/steps/input. This uses GPU quota and can take tens of minutes.\n',
        'Nails measures an approved localized crop, not full-hand/application latency. Generated output is evidence for review; caching remains disabled in the working system.\n']},
        {'cell_type':'code','metadata':{},'execution_count':None,'outputs':[],'source':cell.splitlines(keepends=True)}]}
    target=ROOT/'notebooks/beautycore_generation_speed_benchmark.ipynb'
    target.write_text(json.dumps(notebook,indent=2)+'\n',encoding='utf-8')
    (ROOT/'notebooks/beautycore_generation_speed_benchmark_cell.py').write_text(cell,encoding='utf-8')
    compile(cell,str(target),'exec')
    return {'notebook':str(target),'source_files':len(FILES),'includes_weights':False,'includes_secrets':False}


if __name__=='__main__':
    print(json.dumps(build()))
