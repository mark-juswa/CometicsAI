"""Offline rehearsal checks. Real gateway/consultation; synthetic GPU/vision."""
import asyncio
import base64
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
from zipfile import ZipFile
import httpx
import numpy as np
from PIL import Image
import pytest
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.testclient import TestClient
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from scripts import application_rehearsal as run
from scripts.application_rehearsal_worker import create_app
from scripts.application_rehearsal_bootstrap import clean_environment
from scripts import package_application_rehearsal as package
KEY='rehearsal-test-only-not-a-real-secret-123456'


def test_mode_control_requires_key_valid_input_ready_idle_owner(monkeypatch):
    monkeypatch.setenv('AI_REMOTE_API_KEY',KEY)
    owner=SimpleNamespace(owner=asyncio.Lock(),synchronize=lambda:None,audit=[{}])
    runtime=SimpleNamespace(ready=True,owner=owner)
    client=TestClient(create_app(SimpleNamespace(app=FastAPI(),runtime=runtime)))
    headers={'X-API-Key':KEY}
    assert client.post('/rehearsal/mode',json={'mode':'candidate'}).status_code==401
    for body in ({'mode':'unknown'},{'mode':'candidate','extra':1}):
        assert client.post('/rehearsal/mode',headers=headers,json=body).status_code==422
    assert client.post('/rehearsal/mode',headers=headers,json={'mode':'candidate'}).status_code==200
    assert owner.performance.cache_enabled and not owner.performance.phase_timing and not owner.audit
    asyncio.run(owner.owner.acquire())
    assert client.post('/rehearsal/mode',headers=headers,json={'mode':'baseline'}).status_code==409
    owner.owner.release()
    assert client.post('/rehearsal/mode',headers=headers,json={'mode':'baseline'}).status_code==200
    assert not owner.performance.cache_enabled
    runtime.ready=False
    assert client.post('/rehearsal/mode',headers=headers,json={'mode':'baseline'}).status_code==503


def test_environment_and_pair_analysis_reject_stale_injection_duplicate_or_missing_pairs():
    env=clean_environment({'PYTHONPATH':'unrelated','MPLBACKEND':'inline','AI_PROMPT_CACHE':'1','AI_MODEL_DIR':'previous','KEEP':'yes'})
    assert env['MPLBACKEND']=='Agg' and env['PYTHONNOUSERSITE']=='1' and env['KEEP']=='yes'
    assert not set(env)&{'PYTHONPATH','AI_PROMPT_CACHE','AI_MODEL_DIR'}
    a={'case':'red','mode':'baseline','wall_seconds':10,'rgb_sha256':'same','mask_pixels_sha256':'mask','png_sha256':'png'}
    b={**a,'mode':'candidate','wall_seconds':12}
    assert run.compare_records([a,b])[0]['observed_saving_percent']<0
    for rows in ([a],[a,a,b]):
        with pytest.raises(RuntimeError):run.compare_records(rows)
    assert not run.compare_records([a,{**b,'rgb_sha256':'different'}])[0]['pixels_equal']
    assert not run.compare_records([a,{**b,'mask_pixels_sha256':'different'}])[0]['mask_pixels_equal']


def hand_fixture():
    photo=Image.new('RGB',(80,80),'white');fingers={}
    for i in range(5):
        pixels=np.zeros((80,80),dtype=np.uint8);pixels[10:20,5+i*14:12+i*14]=255
        fingers[str(i)]=Image.fromarray(pixels)
    return photo,Image.fromarray(np.maximum.reduce([np.asarray(v) for v in fingers.values()])),fingers


def test_preservation_rejects_missing_finger_or_outside_changes():
    photo,mask,fingers=hand_fixture()
    pixels=np.asarray(photo).copy();pixels[np.asarray(mask)>0]=[255,0,0];result=Image.fromarray(pixels)
    assert run.preservation(photo,result,mask,fingers)['changed_outside_mask_pixels']==0
    with pytest.raises(RuntimeError):run.preservation(photo,photo,mask,fingers)
    result.putpixel((0,0),(0,0,0))
    with pytest.raises(RuntimeError):run.preservation(photo,result,mask,fingers)


def test_private_cell_preserves_demo_owns_fresh_folders_and_packages_partial_failure(tmp_path,monkeypatch):
    inputs=tmp_path/'input';inputs.mkdir();working=tmp_path/'working';working.mkdir()
    demo=working/'render-kaggle';demo.mkdir();(demo/'keep').write_text('working')
    bundles=[]
    for name,_,folder,manifest in package.BUNDLES:
        p=inputs/name;data=b'immutable fixture'
        with ZipFile(p,'w') as z:
            z.writestr('original.txt',data);z.writestr(manifest,json.dumps({'files':{'original.txt':sha256(data).hexdigest()}}))
        bundles.append((name,sha256(p.read_bytes()).hexdigest(),folder,manifest))
    payload={name:{'data':base64.b64encode((ROOT/name).read_bytes()).decode(),'sha256':sha256((ROOT/name).read_bytes()).hexdigest()} for name in package.FILES}
    hand=b'cell-only-fixture'
    code=package.make_cell(payload,{'data':base64.b64encode(hand).decode(),'sha256':sha256(hand).hexdigest()})
    code=code.replace(repr(package.BUNDLES),repr(tuple(bundles))).replace("Path('/kaggle/input')",'Path('+repr(str(inputs))+')').replace("Path('/kaggle/working')",'Path('+repr(str(working))+')')
    calls=[]
    def child(args,cwd,check):
        assert check
        work=Path(cwd).parent;calls.append(work)
        (work/'results').mkdir();(work/'results/report.json').write_text('{"fixture":true}')
        (work/'setup-evidence').mkdir();(work/'setup-evidence/host.json').write_text('{}')
        if len(calls)==2:raise subprocess.CalledProcessError(1,args)
    monkeypatch.setattr(subprocess,'run',child)
    exec(compile(code,'private-cell','exec'),{})
    with pytest.raises(subprocess.CalledProcessError):exec(compile(code,'private-cell','exec'),{})
    assert calls[0]!=calls[1] and (demo/'keep').read_text()=='working'
    for work in calls:
        with ZipFile(work/'beautycore-application-results.zip') as z:
            assert set(z.namelist())=={'results/report.json','setup-evidence/host.json','candidate.json'}


def test_full_driver_twenty_gateway_results_thirty_model_calls_and_real_consultation_state(tmp_path,monkeypatch):
    from app import main
    from app.consultation.api import build_router
    from app.consultation.store import ConsultationStore
    monkeypatch.setenv('AI_BACKEND_API_KEY',KEY);monkeypatch.setenv('AI_REMOTE_API_KEY',KEY);monkeypatch.setenv('CONSULTATION_PROVIDER','deterministic')
    cpu=tmp_path/'cpu-src';(cpu/'backend').mkdir(parents=True)
    inputs=tmp_path/'gpu-src/gate1/inputs';inputs.mkdir(parents=True)
    fixtures=tmp_path/'fixtures';fixtures.mkdir()
    photo,mask,fingers=hand_fixture()
    photo.save(fixtures/'hand.png');photo.save(inputs/'hairstyle.png');photo.save(inputs/'makeup.jpg')
    monkeypatch.setattr(run,'ROOT',cpu)
    segmenter=SimpleNamespace(segment_fingertips=lambda *a,**kw:(mask,fingers))
    monkeypatch.setattr(main,'nails_pipeline',lambda:SimpleNamespace(segmenter=segmenter))
    Client=httpx.AsyncClient;send_original=Client.send;sleep_original=asyncio.sleep
    release=asyncio.Event();audit=[];modes=[];counts=[]
    worker=FastAPI()
    @worker.post('/rehearsal/mode')
    async def mode(body:dict):
        counts.append(len(audit));audit.clear();modes.append(body['mode']);return {'ok':True}
    @worker.get('/status')
    async def status():return {'requests':audit.copy(),'foundation_load_count':1,'gpu_runtime_ready':True}
    @worker.get('/health')
    async def health():return {'foundation_load_count':1,'gpu_runtime_ready':True}
    async def send(self,request,*args,**kwargs):
        response=await send_original(self,request,*args,**kwargs)
        if response.status_code==429:release.set()
        return response
    monkeypatch.setattr(Client,'send',send)
    def client(*args,**kwargs):
        if kwargs.get('base_url')=='http://127.0.0.1:8765':kwargs['transport']=httpx.ASGITransport(app=worker)
        return Client(*args,**kwargs)
    monkeypatch.setattr(httpx,'AsyncClient',client)
    async def fast_sleep(_):await sleep_original(0)
    monkeypatch.setattr(asyncio,'sleep',fast_sleep)
    styles={'hairstyle':['bob_hair','bun','crew_cut'],'makeup':['natural_makeup'],'nails':['classic_red','french_tip','glossy_black','nude_pink','pink_ombre']}
    loaders={}
    for feature,ids in styles.items():
        async def load(ids=ids):return [main.StyleResponse(id=s,name=s,description=s,status='available') for s in ids]
        loaders[feature]=load
    async def dispatch(feature,image,style):
        await release.wait();release.clear()
        count=5 if feature=='nails' and style in ('classic_red','glossy_black') else 0 if feature=='nails' else 1
        audit.extend({'feature':feature,'style_id':style} for _ in range(count))
        result=photo.copy();metadata={}
        if feature=='nails':
            segmenter.segment_fingertips(None)
            pixels=np.asarray(result).copy();pixels[np.asarray(mask)>0]=[70+len(style),30,80];result=Image.fromarray(pixels)
            metadata={'nails_edited':5,'inference_steps':8,'inference_path':'model' if count else 'renderer'}
        output=BytesIO();result.save(output,'PNG')
        return main.GenerateResponse(status='completed',generator='synthetic-test',style=main.StyleResponse(id=style,name=style,description=style,status='available'),image=main.ImageResponse(data_url='data:image/png;base64,'+base64.b64encode(output.getvalue()).decode(),content_type='image/png',width=80,height=80),metadata=metadata)
    app=FastAPI()
    @app.post('/features/{feature}/generate')
    async def generate(feature:str,image:UploadFile=File(),style_id:str=Form()):return await dispatch(feature,image,style_id)
    app.include_router(build_router(lambda:loaders,main.validated_image,ConsultationStore(),dispatch=dispatch))
    monkeypatch.setattr(main,'app',app)
    asyncio.run(run.rehearse(tmp_path/'results'))
    report=json.loads((tmp_path/'results/report.json').read_text())
    assert report['status']=='APPLICATION_COMPARISON_COMPLETE_VISUAL_REVIEW_REQUIRED'
    assert len(report['requests'])==20 and len(report['comparisons'])==10
    assert sum(len(r['worker_requests']) for r in report['requests'])==30
    assert modes==['baseline','candidate'] and counts==[0,15] and len(audit)==15
    assert all(r['pixels_equal'] and r['mask_pixels_equal'] for r in report['comparisons'])
    assert all(report['modes'][m]['nails_consultation']['selected_completed_look'] for m in modes)


def test_generated_private_notebook_contains_exact_reviewed_scripts_no_outputs_and_no_weights(tmp_path,monkeypatch):
    photo,_,_=hand_fixture();fixture=tmp_path/'fixture.png';photo.save(fixture)
    monkeypatch.setattr(package,'HAND',fixture);monkeypatch.setattr(package,'HAND_SHA',sha256(fixture.read_bytes()).hexdigest())
    output=tmp_path/'private.ipynb';result=package.build(output)
    assert result['sha256']==sha256(output.read_bytes()).hexdigest()
    with pytest.raises(ValueError):package.build(output)
    book=json.loads(output.read_text())
    assert len(book['cells'])==2 and not book['cells'][1]['outputs']
    import ast
    code=''.join(book['cells'][1]['source']);tree=ast.parse(code)
    values={n.targets[0].id:ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id in ('FILES','HAND','BUNDLES')}
    assert set(values['FILES'])==set(package.FILES)
    for name,item in values['FILES'].items():
        raw=base64.b64decode(item['data'],validate=True)
        assert raw==(ROOT/name).read_bytes() and sha256(raw).hexdigest()==item['sha256']
        compile(raw,name,'exec')
        assert not name.endswith(('.bin','.safetensors','.pt','.env'))
    assert base64.b64decode(values['HAND']['data'])==fixture.read_bytes()
    assert values['BUNDLES']==package.BUNDLES


def test_worker_wait_fails_immediately_on_reported_unready_and_waits_only_while_loading(monkeypatch):
    from scripts import application_rehearsal_bootstrap as boot
    process=SimpleNamespace(poll=lambda:None)
    monkeypatch.setattr(boot.original,'ready',lambda health:bool(health and health.get('status')=='ready'))
    monkeypatch.setattr(boot.original,'health',lambda url:{'status':'unready'})
    with pytest.raises(RuntimeError,match='initialization failed'):boot.wait_for_worker(process)
    states=iter([None,{'status':'ready'}]);waits=[]
    monkeypatch.setattr(boot.original,'health',lambda url:next(states))
    monkeypatch.setattr(boot.time,'sleep',lambda seconds:waits.append(seconds))
    boot.wait_for_worker(process)
    assert waits==[2]
    monkeypatch.setattr(boot.original,'health',lambda url:None)
    with pytest.raises(RuntimeError,match='exited'):boot.wait_for_worker(SimpleNamespace(poll=lambda:1))


def test_cleanup_terminates_only_its_owned_live_handle_and_bounds_wait(monkeypatch):
    from scripts.application_rehearsal_bootstrap import stop_owned_worker
    calls=[]
    def wait(timeout):
        calls.append(('wait',timeout))
        if timeout==15:raise subprocess.TimeoutExpired('owned-fixture',timeout)
    owned=SimpleNamespace(poll=lambda:None,terminate=lambda:calls.append('terminate'),kill=lambda:calls.append('kill'),wait=wait)
    stop_owned_worker(None)
    stop_owned_worker(SimpleNamespace(poll=lambda:0))
    assert not calls
    stop_owned_worker(owned)
    assert calls==['terminate',('wait',15),'kill',('wait',5)]
