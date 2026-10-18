"""Private application rehearsal setup. Owns one loopback worker, no tunnel."""
from hashlib import sha256
from importlib import metadata
import ctypes.util
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT.parent
CPU=WORK/'cpu-src'
sys.path.insert(0,str(ROOT))
from scripts import unified_gate3_bootstrap as original


def clean_environment(source):
    env={**source,'PYTHONUNBUFFERED':'1','MPLBACKEND':'Agg','PYTHONNOUSERSITE':'1'}
    for key in ('PYTHONPATH','PYTHONSTARTUP','PYTHONUSERBASE','LD_PRELOAD','AI_INFERENCE_PROFILE','AI_PROMPT_CACHE','HAIRCAPSTONE_STYLE_REGISTRY_PATH','AI_HAIR_ADAPTER_DIRS','AI_MODEL_DIR'):
        env.pop(key,None)
    return env


def command(args,cwd,env,stage,stream=False):
    print('REHEARSAL SETUP',stage,'started',flush=True)
    log=WORK/'setup-evidence'/(stage+'.log')
    with log.open('w',encoding='utf-8') as target:
        if stream:
            process=subprocess.Popen(args,cwd=cwd,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
            for line in process.stdout:
                target.write(line);target.flush()
                if line.startswith('REHEARSAL'):print(line.rstrip(),flush=True)
            process.wait()
        else:
            process=subprocess.Popen(args,cwd=cwd,env=env,stdout=target,stderr=subprocess.STDOUT)
            while process.poll() is None:
                try:process.wait(timeout=30)
                except subprocess.TimeoutExpired:print('REHEARSAL SETUP',stage,'running; log bytes',log.stat().st_size,flush=True)
    if process.returncode:raise RuntimeError(stage+' failed; inspect setup-evidence/'+stage+'.log')
    print('REHEARSAL SETUP',stage,'finished',flush=True)



def wait_for_worker(worker):
    start=time.monotonic();last=start
    while True:
        health=original.health('http://127.0.0.1:8765')
        if original.ready(health):return
        if worker.poll() is not None:raise RuntimeError('Owned worker exited; inspect worker.log')
        if health is not None and health.get('status')=='unready':raise RuntimeError('Owned worker initialization failed; inspect worker.log')
        if time.monotonic()-start>900:raise RuntimeError('Owned worker load exceeded15minutes')
        if time.monotonic()-last>30:
            print('REHEARSAL SETUP model loading',round(time.monotonic()-start),'seconds',flush=True)
            last=time.monotonic()
        time.sleep(2)


def stop_owned_worker(worker):
    if worker is not None and worker.poll() is None:
        worker.terminate()
        try:worker.wait(timeout=15)
        except subprocess.TimeoutExpired:worker.kill();worker.wait(timeout=5)


def bootstrap():
    if sys.platform!='linux':raise RuntimeError('Run in a private Kaggle T4 session')
    with socket.socket() as probe:
        if probe.connect_ex(('127.0.0.1',8765))==0:raise RuntimeError('A worker already owns port8765; do not replace a running service')
    import re
    ram=int(re.search(r'MemTotal:\s+(\d+)',Path('/proc/meminfo').read_text())[1])*1024
    if ram<30*1024**3:raise RuntimeError('Combined CPU/GPU rehearsal requires at least30GiB host RAM')
    output=WORK/'setup-evidence';output.mkdir(exist_ok=False)
    _,review=original.verify_bundle()
    env=clean_environment(os.environ)
    env.update(CUDA_VISIBLE_DEVICES='0',HF_HOME='/tmp/beautycore-speed-hf')
    check=subprocess.run([sys.executable,'-c',"import json,platform,torch;print(json.dumps({'python':platform.python_version(),'torch':torch.__version__,'cuda':torch.version.cuda,'gpu':torch.cuda.get_device_name(0) if torch.cuda.is_available() else None}))"],cwd=ROOT,env=env,capture_output=True,text=True,check=True)
    host=json.loads(check.stdout.strip().splitlines()[-1]);(output/'host.json').write_text(json.dumps(host,indent=2)+'\n')
    expected=review['environment']
    if any(host[k]!=expected[k] for k in ('python','torch','cuda','gpu')):raise RuntimeError('Host differs from reviewed GPU runtime; inspect host.json')
    constraints=[f"torch=={expected['torch']}"]
    for name in ('torchvision','torchaudio'):
        try:constraints.append(name+'=='+metadata.version(name))
        except metadata.PackageNotFoundError:pass
    constraint=output/'torch-constraints.txt';constraint.write_text('\n'.join(constraints)+'\n')
    try:metadata.version('torchao')
    except metadata.PackageNotFoundError:pass
    else:command([sys.executable,'-m','pip','uninstall','-y','torchao'],ROOT,env,'optional-torchao')
    command([sys.executable,'-m','pip','install','--constraint',str(constraint),'-r',str(ROOT/'scripts/unified_gate3_requirements.txt')],ROOT,env,'gpu-dependencies')
    command([sys.executable,str(ROOT/'scripts/unified_gate2.py'),'--environment-only'],ROOT,env,'gpu-environment')
    observed=json.loads((output/'gpu-environment.log').read_text().strip().splitlines()[-1])
    if any(observed.get(k)!=expected.get(k) for k in ('python','packages','diffusers_commit','torch','cuda','gpu')):raise RuntimeError('Resolved GPU environment differs')
    command([sys.executable,str(ROOT/'scripts/unified_gate2.py'),'--verify-only'],ROOT,env,'gpu-artifacts')
    cache=Path(env['HF_HOME'])/'hub';cache.mkdir(parents=True,exist_ok=True)
    command([sys.executable,str(ROOT/'scripts/unified_gate1_bootstrap.py'),'--download-only','--output',str(output/'model.json'),'--cache',str(cache)],ROOT,env,'base-model-cache')
    model=json.loads((output/'model.json').read_text())
    if model['model_index_sha256']!=review['base_model_index_sha256']:raise RuntimeError('Pinned Base model index differs')
    overlay=json.loads((WORK/'candidate.json').read_text())
    for name,item in overlay.items():
        raw=(WORK/'overlay'/name).read_bytes()
        if sha256(raw).hexdigest()!=item['sha256']:raise RuntimeError('Source overlay changed')
        target=original.gate.safe_path(ROOT,name);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
    cpuenv=clean_environment(env)
    cpuenv.update(CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1')
    if not ctypes.util.find_library('portaudio'):
        command(['apt-get','update'],CPU,cpuenv,'portaudio-index')
        command(['apt-get','install','-y','libportaudio2'],CPU,cpuenv,'portaudio')
    for name in ('backend-env','segment-env'):
        command([sys.executable,'-m','venv','--without-pip',str(WORK/name)],CPU,cpuenv,name+'-create')
        command([sys.executable,'-m','pip','--python',str(WORK/name),'install','pip==25.3'],CPU,cpuenv,name+'-pip')
    api=WORK/'backend-env/bin/python';segment=WORK/'segment-env/bin/python'
    command([str(api),'-m','pip','install','-r','backend/requirements-nails.txt','--constraint','backend/requirements-demo-constraints.txt'],CPU,cpuenv,'cpu-api-install')
    command([str(segment),'-m','pip','install','torch==2.10.0','torchvision==0.25.0','--index-url','https://download.pytorch.org/whl/cpu'],CPU,cpuenv,'cpu-torch')
    command([str(segment),'-m','pip','install','-r','backend/requirements-nails-segmenter.txt'],CPU,cpuenv,'cpu-segment-install')
    for label,python in (('api',api),('segment',segment)):
        command([str(python),'-m','pip','check'],CPU,cpuenv,label+'-pip-check')
    gpu_key=secrets.token_hex(32)
    from scripts.capstone_train002_bootstrap import worker_environment
    gpuenv=worker_environment({**env,'AI_MODEL_DIR':model['snapshot'],'AI_REMOTE_API_KEY':gpu_key})
    cpuenv.update(AI_GPU_LOOPBACK='1',AI_REMOTE_URL='http://127.0.0.1:8765',AI_REMOTE_API_KEY=gpu_key,AI_BACKEND_API_KEY=secrets.token_hex(32),
        GENERATION_ENGINE='remote_flux',MAKEUP_GENERATION_ENGINE='remote_makeup',NAILS_PREVIEW_MODE='hybrid',NAILS_INFERENCE_STEPS='8',
        NAILS_SEGMENT_PYTHON=str(segment),NAILS_SEGMENT_CHECKPOINT=str(CPU/'data/nails/checkpoints/mnemic/nails_seg_s_yolov8_v1.pt'),
        NAILS_HAND_LANDMARKER_PATH=str(CPU/'data/nails/checkpoints/mediapipe/hand_landmarker.task'),
        HAIRCAPSTONE_STYLE_REGISTRY_PATH=str(CPU/'backend/app/style_registry_train002_smoke.json'),CONSULTATION_PROVIDER='deterministic',FRONTEND_ORIGINS='')
    cpuenv['PYTHONPATH']=str(CPU/'backend')
    # Copy only the test driver, never overwrite CPU application code.
    driver=CPU/'scripts/application_rehearsal.py';driver.write_bytes((ROOT/'scripts/application_rehearsal.py').read_bytes())
    command([str(api),'-c',"from app.main import nails_pipeline; nails_pipeline(); print('Hand localizer and configured pipeline loaded')"],CPU,cpuenv,'cpu-landmark-load')
    checkpoint=cpuenv['NAILS_SEGMENT_CHECKPOINT']
    command([str(segment),'-c',"import torch,torchvision; from ultralytics import YOLO; assert '+cpu' in torch.__version__; assert torchvision.extension._has_ops(); YOLO("+repr(checkpoint)+")"],CPU,cpuenv,'cpu-segment-load')
    worker=None
    try:
        with (output/'worker.log').open('w',encoding='utf-8') as log:
            worker=subprocess.Popen([sys.executable,'-m','uvicorn','scripts.application_rehearsal_worker:factory','--factory','--host','127.0.0.1','--port','8765','--workers','1'],cwd=ROOT,env=gpuenv,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        wait_for_worker(worker)
        print('REHEARSAL PLAN: 20 application results, 30 model calls (five per model hand). One pair per case. No public endpoint.',flush=True)
        command([str(api),str(driver),'--output',str(WORK/'results')],CPU,cpuenv,'application',stream=True)
    finally:
        stop_owned_worker(worker)
        print('REHEARSAL owned worker stopped; demo service untouched.',flush=True)


if __name__=='__main__':bootstrap()
