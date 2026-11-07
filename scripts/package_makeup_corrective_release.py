"""Prepare a reviewable matched production release, without applying or deploying it.

Consumes the preserved application candidate and its verified real GPU return.
Generation code/weights stay identical to that accepted and exercised candidate.
"""
import ast
import base64
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile

from scripts import package_makeup_corrective_application as application
from scripts import package_expanded_nails_release as common

ROOT = Path(__file__).resolve().parents[1]
BASE = application.WORK
INPUT = BASE/'application-candidate-01'
OUTPUT = BASE/'release-candidate-03'
CPU_NAME = 'beautycore_makeup_release_20261106.bin'
RELEASE_ID = 'styles-20261106-01'
PROFILE_ID = 'makeup-corrective001-v1'
HELD = frozenset(('exp_cloud_berry_lips','exp_manga_lash','exp_icy_silver'))
TAGS = {'exp_cloud_berry_lips':['berry','soft','matte','everyday'],
        'exp_manga_lash':['lashes','pink','defined','playful'],
        'exp_icy_silver':['silver','cool','shimmer','evening']}


def literal_assignment(source, name):
    node = next(n for n in ast.parse(source).body if isinstance(n,ast.Assign)
                and any(isinstance(t,ast.Name) and t.id==name for t in n.targets))
    return ast.literal_eval(node.value)


def capability_source(raw):
    text=raw.decode()
    anchor='        if (candidate.feature != "nails" or candidate.route != "nails_renderer"'
    branch='''        if candidate.feature == "makeup":
            from app import makeup_contract
            expected_ids = {"exp_cloud_berry_lips", "exp_manga_lash", "exp_icy_silver"}
            if (candidate.route != "makeup_profile" or candidate.id not in expected_ids
                    or candidate.profile_id != "makeup-corrective001-v1"
                    or candidate.profile_sha256 != profile_digest(Path(makeup_contract.__file__))
                    or makeup_contract.ADAPTER_SHA256 != "991a1037cc892c1a62e1a731be577ed1aec2f331d9568b4586ff3829a4ee32c3"
                    or candidate.id not in makeup_contract.PROMPTS):
                raise ValueError("Makeup release differs from the reviewed execution contract")
            if candidate.enabled:
                result.append(candidate)
            continue
'''
    text=common.required_replace(text,anchor,branch+anchor)
    # Historical releases keep their actual ten Makeup IDs, not the new 13.
    anchor='    result = baseline_model_styles()'
    text=common.required_replace(text,anchor,anchor+'''
    if not release.enabled("makeup"):
        result["makeup"] = [sid for sid in result["makeup"] if not sid.startswith("exp_")]
''')
    return text.encode()


def build(destination=OUTPUT):
    destination=Path(destination)
    receipt=json.loads((BASE/'application-return-01/technical-review.json').read_text())
    if not (receipt['all13_exactly_equal_to_human_accepted_raw'] is True
            and receipt['active_tensor_equality']=='PASS_ALL16' and receipt['foundation_load_count']==1
            and receipt['archive_sha256']=='2293af526ae2f5f9f916ac6ab3d9f258cc8e6afc3ee5bab0c9ead6a0a94ce739'):
        raise ValueError('Real application gate has not passed')
    input_report=json.loads((INPUT/'package.json').read_text())
    cpu_path=INPUT/input_report['cpu']['name']
    if common.digest(cpu_path)!=input_report['cpu']['sha256']:
        raise ValueError('Tested application candidate changed')
    book=json.loads((INPUT/'makeup_corrective001_application.ipynb').read_text())
    preparation=''.join(book['cells'][1]['source'])
    startup=''.join(book['cells'][2]['source'])
    payload=literal_assignment(preparation,'OPTIMIZED_SOURCES')
    original_payload=deepcopy(payload)
    old_evidence=literal_assignment(preparation,'STYLE_RELEASE_EXPECTED')
    with ZipFile(cpu_path) as archive:
        files={n:archive.read(n) for n in archive.namelist()}
    manifest=json.loads(files.pop('demo_bundle.json'))
    release_path='backend/app/style_release.json'
    old_release=json.loads(files[release_path])
    release=deepcopy(old_release)
    release['release_id']=RELEASE_ID
    profile_hash=sha256(files[application.CONTRACT_PATH].replace(b'\r\n',b'\n')).hexdigest()
    for row in release['candidates']:
        if row['id'] in HELD:
            row.update(profile_id=PROFILE_ID,profile_sha256=profile_hash,review_status='accepted',enabled=True,
                       tags=TAGS[row['id']],evidence=[
                           'docs/experiments/makeup-corrective-model-results-20261106.md',
                           'docs/experiments/makeup-corrective-application-results-20261106.md'])
    style_text=files['backend/app/makeup_styles.py'].decode()
    style_text=style_text.replace('# Controlled candidate catalog only, production release remains held.',
                                  '# Reviewed corrective model catalog, release candidate.')
    for row in release['candidates']:
        if row['id'] in HELD:
            before=f"MakeupStyle({row['id']!r}, {row['name']!r}, 'Corrective application validation candidate.',"
            after=f"MakeupStyle({row['id']!r}, {row['name']!r}, {row['description']!r},"
            style_text=common.required_replace(style_text,before,after)
    files['backend/app/makeup_styles.py']=style_text.encode()
    files['backend/app/style_releases/'+old_release['release_id']+'.json']=application.encoded(old_release)
    files[release_path]=application.encoded(release)
    files['backend/app/style_capabilities.py']=capability_source(files['backend/app/style_capabilities.py'])
    evidence={'release_id':RELEASE_ID,'manifest_sha256':sha256(json.dumps(release,sort_keys=True,ensure_ascii=True,
                          separators=(',',':')).encode()).hexdigest(),
              'enabled_style_ids':sorted(c['id'] for c in release['candidates'] if c['enabled'])}
    # The original tested generation/adapter/scaling code is unchanged.
    for name in (release_path,'backend/app/style_capabilities.py'):
        if name in payload:
            raw=files[name]
            payload[name]={'data':base64.b64encode(raw).decode(),'sha256':sha256(raw).hexdigest()}
        else:
            files['candidate/worker/'+name]=files[name]
    overlay=json.loads(files['candidate/worker-manifest.json'])
    overlay['files']['backend/app/style_capabilities.py']=sha256(files['backend/app/style_capabilities.py']).hexdigest()
    overlay['production_approved']=False
    files['candidate/worker-manifest.json']=application.encoded(overlay)
    manifest['worker_sources']={k:v['sha256'] for k,v in payload.items()}
    manifest['style_release']=evidence
    manifest['release_candidate_status']='PREPARED_PENDING_PROJECT_LEAD_PRODUCTION_APPROVAL'
    # Generate matching Render JSON with the existing generator in an isolated tree.
    stage=destination/'source'
    if stage.exists():
        raise ValueError('Release candidate requires a fresh destination')
    for name,raw in files.items():
        if name.startswith(('backend/app/','data/makeup/')):
            common.immutable(stage/name,raw)
    business='beautycore/lib/business/style-catalog.json'
    generated='beautycore/lib/ai/style-release.json'
    common.immutable(stage/business,(ROOT/business).read_bytes())
    (stage/generated).parent.mkdir(parents=True,exist_ok=True)
    generator=(ROOT/'scripts/generate_style_release.py').read_text()
    generator=common.required_replace(generator,'"makeup": sorted(PROMPTS),',
        '"makeup": sorted(PROMPTS) if release is not None and release.enabled("makeup") else sorted(s for s in PROMPTS if not s.startswith("exp_")),')
    common.immutable(stage/'scripts/generate_style_release.py',generator.encode())
    env={**os.environ,'PYTHONPATH':str((stage/'backend').resolve()),
         'HAIRCAPSTONE_STYLE_REGISTRY_PATH':str((stage/'backend/app/style_registry_train002_smoke.json').resolve())}
    result=subprocess.run([sys.executable,str((stage/'scripts/generate_style_release.py').resolve()),'--write'],
                          env=env,cwd=stage,check=True,capture_output=True,text=True)
    business_json=json.loads((stage/business).read_text(encoding='utf-8'))
    generated_json=json.loads((stage/generated).read_text(encoding='utf-8'))
    if {k:len(v) for k,v in business_json.items()}!={'hairstyle':18,'makeup':13,'nails':8}:
        raise ValueError('Production business catalog scope changed')
    if len(generated_json['compatible_releases'])!=3 or any(len(c['makeup'])!=10
            for r in generated_json['compatible_releases'] for c in r['baseline_model_catalogs']):
        raise ValueError('Historical fallback catalog changed')
    for name in ('docs/experiments/makeup-corrective-model-results-20261106.md',
                 'docs/experiments/makeup-corrective-application-results-20261106.md'):
        files[name]=(ROOT/name).read_bytes()
    manifest['files']={k:sha256(v).hexdigest() for k,v in files.items()}
    files['demo_bundle.json']=application.encoded(manifest)
    archive=common.archive_bytes(files)
    for before,after in [(repr(original_payload),repr(payload)),(repr(old_evidence),repr(evidence)),
                         (input_report['cpu']['name'],CPU_NAME),(input_report['cpu']['sha256'],sha256(archive).hexdigest())]:
        preparation=common.required_replace(preparation,before,after)
    stop='''    record = {"status": "CONTROLLED_APPLICATION_READY", "url": f"http://127.0.0.1:{PORT}",
              "api_pid": api.pid, "readiness": readiness, "production_registered": False}
    (WORK / "demo-session.json").write_text(json.dumps(record, indent=2))
    print("CONTROLLED APPLICATION READY. Run Cell 3. Website connection unchanged.", flush=True)
    return
'''
    startup=common.required_replace(startup,stop,'')
    # No other startup/generation change. Existing exact readiness and authenticated
    # registration checks now gate the normal production connection.
    book['cells'][0]['source']=[
        '# BeautyCore corrective Makeup release candidate\n\n'
        'Prepared for project lead production review. Do not run before approval and matching Render metadata deployment. '
        f'Private pinned T4 notebook. Attach {CPU_NAME} and unchanged {common.GPU_NAME}. '
        'Enable the existing three secrets, then run three code cells in order. '
        'This starter uses normal authenticated website registration. It contains 18 Hair, 13 Makeup and 8 Nails styles. '
        'No training or repeated catalog generation. Preserve prior inputs/notebooks for rollback.\n']
    book['cells'][1]['source']=preparation.splitlines(keepends=True)
    book['cells'][2]['source']=startup.splitlines(keepends=True)
    book['cells'][3]['source']=[
        "record = json.loads((CLIENT_WORK/'demo-session.json').read_text())\n"
        "print('Status:', record['status'])\n"
        "print('Release:', STYLE_RELEASE_EXPECTED['release_id'])\n"
        "print('Catalog: 18 Hair, 13 Makeup, 8 Nails')\n"
        "print('Keep this session running. Complete the website upload/generate/save/book rehearsal.')\n"]
    for i,cell in enumerate(book['cells']):
        if cell['cell_type']=='code':
            compile(''.join(cell['source']),f'release-cell-{i}','exec')
            cell['outputs'],cell['execution_count']=[],None
    # Reviewable publication sources. Nothing is applied to the live checkout.
    publication=[application.CONTRACT_PATH,'backend/app/makeup_styles.py','backend/app/style_capabilities.py',release_path,
                 'backend/app/style_releases/'+old_release['release_id']+'.json',application.PRESETS_PATH,
                 'scripts/makeup_inference_server.py','scripts/unified_gate3_server.py',
                 'scripts/generate_style_release.py',business,generated]
    common.immutable(stage/'scripts/makeup_inference_server.py',files['candidate/worker/scripts/makeup_inference_server.py'])
    server=base64.b64decode(payload['scripts/unified_gate3_server.py']['data'])
    from scripts.package_all_hair_nails_release import HOOK
    if not server.endswith(HOOK):
        raise ValueError('Unexpected shared worker release hook')
    common.immutable(stage/'scripts/unified_gate3_server.py',server[:-len(HOOK)])
    report={'schema':'makeup-corrective-release-candidate-v1','status':'PREPARED_PENDING_PRODUCTION_REVIEW',
            'release':evidence,'catalog_counts':{'hairstyle':18,'makeup':13,'nails':8},
            'cpu':{'name':CPU_NAME,'sha256':sha256(archive).hexdigest(),'bytes':len(archive)},
            'gpu':input_report['gpu'],'model_checkpoint_sha256':application.CHECKPOINT_SHA,
            'generation_code_identical_to_tested_application':True,
            'publication_files':{name:{'candidate_sha256':common.digest(stage/name),
                'current_sha256':common.digest(ROOT/name) if (ROOT/name).exists() else None} for name in publication},
            'production_approved':False,'published':False,'deployed':False,'generator_stdout':result.stdout.strip()}
    common.immutable(destination/CPU_NAME,archive)
    common.immutable(destination/'beautycore_makeup_release.ipynb',application.encoded(book))
    common.immutable(destination/'release.json',application.encoded(report))
    return report


if __name__=='__main__':
    result=build()
    print(json.dumps({k:result[k] for k in ('status','release','cpu','catalog_counts','published','deployed')},indent=2))
