"""Build a separate optimized starter; preserve original notebook and private inputs."""
import base64
from hashlib import sha256
import json
from pathlib import Path
from scripts.optimized_demo_overlay import FILES, validated

ROOT = Path(__file__).resolve().parents[1]

def build():
    payload = {name: {'data': base64.b64encode((ROOT/name).read_bytes()).decode('ascii'),
                      'sha256': sha256((ROOT/name).read_bytes()).hexdigest()} for name in sorted(FILES)}
    validated(payload)
    setup = (ROOT/'notebooks/render_kaggle_client_setup.py').read_text(encoding='utf-8')
    installer = (ROOT/'scripts/optimized_demo_overlay.py').read_text(encoding='utf-8')
    runner = (ROOT/'scripts/render_kaggle_bootstrap.py').read_text(encoding='utf-8')
    runner = runner.replace('WORK = Path("/kaggle/working/render-kaggle")', 'WORK = CLIENT_WORK')
    runner = runner.rsplit('if __name__ == "__main__":', 1)[0]
    anchor = 'original.start_server = lambda output, env: start(output, worker_environment(env))'
    replacement = """import importlib.util
spec = importlib.util.spec_from_file_location('optimized_overlay', Path({str(WORK / 'worker_overlay.py')!r}))
release_overlay = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release_overlay)
def start_optimized(output, env):
    original.verify_bundle()
    release_overlay.install_overlay(original.ROOT, Path({str(WORK / 'optimized-worker.json')!r}), output)
    return start(output, worker_environment(dict(env, AI_PROMPT_CACHE='1', AI_PROMPT_CACHE_SCOPE='nails', AI_INFERENCE_PROFILE='0')))
original.start_server = start_optimized"""
    if runner.count(anchor) != 1:
        raise ValueError('Reviewed demo worker hook changed')
    runner = runner.replace(anchor, replacement)
    registrar = (ROOT/'scripts/render_kaggle_registration.py').read_text(encoding='utf-8')
    preparation = setup + "\nCLIENT_WORK = prepare()\n" + installer + "\nOPTIMIZED_SOURCES = " + repr(payload) + "\nstage_overlay(CLIENT_WORK, OPTIMIZED_SOURCES)\n(CLIENT_WORK/'worker_overlay.py').write_text(" + repr(installer) + ", encoding='utf-8')\nprint('Optimized worker staged. Run Cell 2 once.')\n"
    prefix = "import os\nBEAUTYCORE_PUBLIC_URL = 'https://beautycore-demo.onrender.com'\nos.environ['BEAUTYCORE_PUBLIC_URL'] = BEAUTYCORE_PUBLIC_URL\n(CLIENT_WORK/'runtime_registration.py').write_text(" + repr(registrar) + ", encoding='utf-8')\n"
    cells = [('markdown', '# BeautyCore optimized scheduled demo\n\nSeparate release notebook. Keep the original starter as fallback. Use the same pinned Kaggle image, T4, Internet, both existing private datasets and the same three enabled Secrets. Run the three code cells once in order. New source is installed only after original bundle/environment/model checks. Nails-only public-prompt reuse; Hair/Makeup remain on baseline. No model quality settings are reduced. First live browser/GPU rehearsal remains required.\n'),
             ('code', preparation), ('code', prefix+runner+'\nmain()\n'),
             ('code', "record=json.loads((CLIENT_WORK/'demo-session.json').read_text())\nprint('Status:',record['status'])\nprint('Website:',BEAUTYCORE_PUBLIC_URL)\nprint('Optimization: Nails-only; Hair/Makeup baseline')\nprint('Rehearse Hair, Makeup, model Nails, renderer Nails and Consultation.')\n")]
    book = {'nbformat':4,'nbformat_minor':5,'metadata':{'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'}},'cells':[]}
    for index,(kind,source) in enumerate(cells):
        cell={'cell_type':kind,'id':'optimized-demo-'+str(index),'metadata':{},'source':source.splitlines(keepends=True)}
        if kind=='code':
            compile(source,'optimized-cell-'+str(index),'exec')
            cell.update(execution_count=None, outputs=[])
        book['cells'].append(cell)
    target=ROOT/'notebooks/render_kaggle_optimized_demo.ipynb'
    target.write_text(json.dumps(book,indent=1)+'\n',encoding='utf-8')
    return {'notebook':str(target),'sha256':sha256(target.read_bytes()).hexdigest(),'bytes':target.stat().st_size,
            'source_sha256':{name:item['sha256'] for name,item in payload.items()},'scope':'nails-only','original_inputs_changed':False}

if __name__=='__main__':print(json.dumps(build(),indent=2))
