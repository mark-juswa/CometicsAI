"""Build one PRIVATE notebook with source and an approved full-hand fixture.

Generated notebook goes under ignored artifacts/, never into the public source tree.
No weights, keys or client photos are embedded. Existing notebooks/bundles stay intact.
"""
import base64
from hashlib import sha256
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
FILES=('scripts/inference_performance.py','scripts/unified_gate3_server.py',
       'scripts/application_rehearsal_worker.py','scripts/application_rehearsal.py','scripts/application_rehearsal_bootstrap.py')
BUNDLES=(('capstone_train002_20260928_v1.bin','f0d1fed52e00b6c5a1da2cade3731237675cdebbfc0b2cde3b2dbda99a4019ac','gpu-src','gate3_bundle.json'),
         ('render_kaggle_cpu_20261009.bin','f391050851519e9cc1080830b615a6cc457b6dd1e21fde156522bb959fad9ede','cpu-src','demo_bundle.json'))
HAND=ROOT/'data/nails/work/manual-mask-ceiling-20260927/0000045_original.png'
HAND_SHA='c483244132e74ffc6e492271e742c17dce4ce694050abab78c43bc306dd4fd98'


def make_cell(files,hand):
    source="""# Private CPU/GPU rehearsal; no Secrets, public tunnel, registration or Render changes.
from pathlib import Path
from hashlib import sha256
from zipfile import ZipFile, ZIP_DEFLATED
import base64, json, subprocess, sys, uuid
FILES = __FILES__
HAND = __HAND__
BUNDLES = __BUNDLES__
work=Path('/kaggle/working')/('beautycore-app-check-'+uuid.uuid4().hex[:10])
work.mkdir(parents=True,exist_ok=False)
for filename,expected,folder,manifest_name in BUNDLES:
    matches=list(Path('/kaggle/input').rglob(filename))
    assert len(matches)==1, 'Attach exactly one private input containing '+filename
    raw=matches[0].read_bytes()
    assert sha256(raw).hexdigest()==expected, 'Private bundle hash differs: '+filename
    root=work/folder;root.mkdir()
    with ZipFile(matches[0]) as archive:
        manifest=json.loads(archive.read(manifest_name))
        names=archive.namelist()
        assert len(names)==len(set(names)) and set(names)==set(manifest['files'])|{manifest_name}
        assert archive.testzip() is None
        for name in names:
            target=(root/name).resolve()
            assert ':' not in name and chr(92) not in name and target.is_relative_to(root.resolve())
            data=archive.read(name)
            if name!=manifest_name:assert sha256(data).hexdigest()==manifest['files'][name]
            target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
for name,item in FILES.items():
    data=base64.b64decode(item['data'],validate=True)
    assert sha256(data).hexdigest()==item['sha256']
    target=(work/'overlay'/name).resolve()
    assert target.is_relative_to((work/'overlay').resolve())
    target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
data=base64.b64decode(HAND['data'],validate=True)
assert sha256(data).hexdigest()==HAND['sha256']
(work/'fixtures').mkdir();(work/'fixtures/hand.png').write_bytes(data)
(work/'candidate.json').write_text(json.dumps({name:{'sha256':item['sha256']} for name,item in FILES.items()},indent=2))
bootstrap=work/'gpu-src/scripts/application_rehearsal_bootstrap.py'
bootstrap.parent.mkdir(parents=True,exist_ok=True)
bootstrap.write_bytes((work/'overlay/scripts/application_rehearsal_bootstrap.py').read_bytes())
print('REHEARSAL_WORKSPACE:',work,flush=True)
print('20 application results / 30 model calls. Full hands cost five calls each. Allow tens of minutes; progress streams here.',flush=True)
result=work/'beautycore-application-results.zip'
try:
    subprocess.run([sys.executable,str(bootstrap)],cwd=work/'gpu-src',check=True)
finally:
    # Preserve partial evidence on failure too. Never package environments/weights/keys.
    with ZipFile(result,'x',ZIP_DEFLATED) as archive:
        for folder in ('results','setup-evidence'):
            for file in sorted((work/folder).glob('*')):
                if file.is_file():archive.write(file,folder+'/'+file.name)
        archive.write(work/'candidate.json','candidate.json')
    print('DOWNLOAD_REHEARSAL_RESULTS:',result,flush=True)
print('Done. Keep this notebook/results private; working website and demo notebook were not changed.',flush=True)
"""
    return source.replace('__FILES__',repr(files)).replace('__HAND__',repr(hand)).replace('__BUNDLES__',repr(BUNDLES))


def build(output=None):
    output=Path(output or ROOT/'artifacts/application-rehearsal-20261018/beautycore_application_rehearsal.ipynb')
    if output.exists():raise ValueError('Refuse to overwrite a generated private rehearsal notebook')
    raw=HAND.read_bytes()
    if sha256(raw).hexdigest()!=HAND_SHA:raise ValueError('Reviewed original hand differs')
    files={name:{'data':base64.b64encode((ROOT/name).read_bytes()).decode('ascii'),'sha256':sha256((ROOT/name).read_bytes()).hexdigest()} for name in FILES}
    cell=make_cell(files,{'data':base64.b64encode(raw).decode('ascii'),'sha256':HAND_SHA})
    compile(cell,'private-application-cell','exec')
    book={'nbformat':4,'nbformat_minor':5,'metadata':{'kernelspec':{'name':'python3','display_name':'Python 3','language':'python'}},'cells':[
      {'cell_type':'markdown','metadata':{},'source':['# BeautyCore private full-hand and consultation rehearsal\n',
        'Use a separate private notebook, T4 GPU, Internet and both existing private GPU/CPU datasets. No API Secrets. Do not replace the demo notebook.\n',
        'This is 20 application results with 30 model calls, not 20 single-crop images: each model hand generates five nails. Allow tens of minutes. Fine-grained progress appears below.\n',
        'Exercises actual CPU API/gateway, segmentation, refinement, loopback model and compositing. Consultation uses the existing deterministic recommendation provider for reproducibility; no Gemini, Next.js/browser or Render acceptance is claimed.\n',
        'Includes one previously reviewed 11K Hands original for private evaluation, not a customer photo. Keep private. The owned GPU worker stops after the run; this is not a demo server.\n']},
      {'cell_type':'code','execution_count':None,'outputs':[],'metadata':{},'source':cell.splitlines(keepends=True)}]}
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(book,indent=2)+'\n',encoding='utf-8')
    return {'notebook':str(output),'sha256':sha256(output.read_bytes()).hexdigest(),'bytes':output.stat().st_size,'source_hashes':{name:item['sha256'] for name,item in files.items()},'hand_sha256':HAND_SHA}


if __name__=='__main__':print(json.dumps(build(),indent=2))
