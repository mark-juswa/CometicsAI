"""Reproduce reviewed dependencies/assets for a private no-server benchmark."""
from hashlib import sha256
from importlib import metadata
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts import unified_gate3_bootstrap as original


def bootstrap():
    output=ROOT.parent/'setup-evidence'
    output.mkdir(exist_ok=False)
    # Verify original members before applying the independently hashed candidate source overlay.
    _,review=original.verify_bundle()
    expected=review['environment']
    env={**os.environ,'CUDA_VISIBLE_DEVICES':'0','PYTHONUNBUFFERED':'1','HF_HOME':'/tmp/beautycore-speed-hf','MPLBACKEND':'Agg'}
    for key in ('PYTHONPATH','PYTHONSTARTUP','PYTHONUSERBASE','LD_PRELOAD','AI_INFERENCE_PROFILE','AI_PROMPT_CACHE'):
        env.pop(key,None)
    check=subprocess.run([sys.executable,'-c',"import json,platform,torch;print(json.dumps({'python':platform.python_version(),'torch':torch.__version__,'cuda':torch.version.cuda,'gpu':torch.cuda.get_device_name(0) if torch.cuda.is_available() else None}))"],cwd=ROOT,env=env,capture_output=True,text=True,check=True)
    host=json.loads(check.stdout.strip().splitlines()[-1])
    (output/'host.json').write_text(json.dumps(host,indent=2)+'\n')
    if any(host[k]!=expected[k] for k in ('python','torch','cuda','gpu')):
        raise RuntimeError('Kaggle host differs from the reviewed environment; inspect setup-evidence/host.json without changing model settings')
    constraints=[f"torch=={expected['torch']}"]
    for name in ('torchvision','torchaudio'):
        try:constraints.append(f'{name}=={metadata.version(name)}')
        except metadata.PackageNotFoundError:pass
    path=output/'torch_constraints.txt';path.write_text('\n'.join(constraints)+'\n')
    try:metadata.version('torchao')
    except metadata.PackageNotFoundError:pass
    else:original.run([sys.executable,'-m','pip','uninstall','-y','torchao'],output,'optional_torchao.log',env)
    original.run([sys.executable,'-m','pip','install','--constraint',str(path),'-r',str(ROOT/'scripts/unified_gate3_requirements.txt')],output,'dependency_install.log',env)
    original.run([sys.executable,str(ROOT/'scripts/unified_gate2.py'),'--environment-only'],output,'environment.log',env)
    observed=json.loads((output/'environment.log').read_text().strip().splitlines()[-1])
    if any(observed.get(k)!=expected.get(k) for k in ('python','packages','diffusers_commit','torch','cuda','gpu')):
        raise RuntimeError('Resolved environment differs; do not claim a matched benchmark')
    original.run([sys.executable,str(ROOT/'scripts/unified_gate2.py'),'--verify-only'],output,'artifact_preflight.log',env)
    cache=Path(env['HF_HOME'])/'hub';cache.mkdir(parents=True,exist_ok=True)
    original.run([sys.executable,str(ROOT/'scripts/unified_gate1_bootstrap.py'),'--download-only','--output',str(output/'model.json'),'--cache',str(cache)],output,'base_download.log',env)
    model=json.loads((output/'model.json').read_text())
    if model['model_index_sha256']!=review['base_model_index_sha256']:
        raise RuntimeError('Base model index differs')
    candidate=json.loads((ROOT.parent/'candidate.json').read_text())
    for name,record in candidate.items():
        raw=(ROOT.parent/'overlay'/name).read_bytes()
        if sha256(raw).hexdigest()!=record['sha256']:
            raise RuntimeError('Candidate source differs')
        target=original.gate.safe_path(ROOT,name)
        target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
    from scripts.capstone_train002_bootstrap import worker_environment
    env=worker_environment({**env,'AI_MODEL_DIR':model['snapshot'],'AI_REMOTE_API_KEY':secrets.token_hex(32)})
    # This subprocess loads one foundation directly. No uvicorn, public tunnel, registration or external API key.
    original.run([sys.executable,str(ROOT/'scripts/benchmark_generation_performance.py'),'--output',str(ROOT.parent/'results')],output,'benchmark.log',env)
    print('BENCHMARK_FINISHED: inspect results/report.json and generated images; no website configuration changed.',flush=True)


if __name__=='__main__':
    bootstrap()
