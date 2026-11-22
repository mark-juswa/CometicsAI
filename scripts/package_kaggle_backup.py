"""Extend the accepted serving notebook using the verified current Runpod CPU package."""
import argparse
import ast
import base64
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import shutil
from zipfile import ZIP_STORED, ZipFile

from scripts import package_runpod as serving

ROOT = Path(__file__).resolve().parents[1]
NAME = 'beautycore_kaggle_backup_20261113.ipynb'


def replace_once(source, old, new):
    if source.count(old) != 1:
        raise ValueError('Reviewed startup anchor changed: ' + old[:70])
    return source.replace(old, new, 1)


def build(output, package):
    output, package = Path(output).resolve(), Path(package).resolve()
    if output.exists() or output.with_suffix('.zip').exists():
        raise ValueError('Choose a new output; existing backups are preserved')
    context = package / 'build-context'
    manifest = json.loads((context / 'build-manifest.json').read_text())
    if manifest.get('schema') != 'beautycore-runpod-build-v1' or manifest.get('photo_validation') != 'local-subject-v1':
        raise ValueError('Use the verified photo-check serving package')
    for name, expected in manifest['files'].items():
        path = (context / name).resolve()
        if not path.is_relative_to(context) or serving.digest(path) != expected:
            raise ValueError('Serving package integrity differs')
    for name, expected in zip(serving.NAMES, serving.DIGESTS):
        if serving.digest(package / 'inputs' / name) != expected:
            raise ValueError('Private input differs')
    payload = {}
    inventory = manifest['cpu_updates']
    required = {'backend/app/main.py', 'backend/app/photo_suitability.py',
                'backend/app/consultation/api.py', 'backend/app/consultation/gemini.py',
                'backend/app/consultation/recommend.py', 'data/vision/blaze_face_short_range.tflite'}
    if set(inventory) != required:
        raise ValueError('Incomplete CPU update set')
    for name, expected in inventory.items():
        raw = (context / 'cpu-updates' / name).read_bytes()
        if sha256(raw).hexdigest() != expected:
            raise ValueError('CPU payload differs')
        if name.endswith('.py') and raw != (ROOT / name).read_bytes():
            raise ValueError('Rebuild the serving package from current source first')
        payload[name] = base64.b64encode(raw).decode('ascii')
    original = ROOT / 'notebooks/render_kaggle_makeup_corrective_demo.ipynb'
    raw = original.read_bytes()
    if sha256(raw).hexdigest() != serving.NOTEBOOK_SHA:
        raise ValueError('Reviewed notebook differs')
    book = deepcopy(json.loads(raw))
    prep = ''.join(book['cells'][1]['source'])
    installer = (ROOT / 'scripts/kaggle_backup_update.py').read_text()
    prep += '\n' + installer + '\nCPU_UPDATE_INVENTORY = ' + repr(inventory)
    prep += '\nCPU_UPDATE_PAYLOAD = ' + repr(payload)
    prep += '\ninstall_cpu_update(CLIENT_WORK, CPU_UPDATE_PAYLOAD, CPU_UPDATE_INVENTORY)\n'
    prep += "print('Current local photo checks and preference ranking staged. No GPU started.')\n"
    runner = ''.join(book['cells'][2]['source'])
    runner = replace_once(runner,
        "BEAUTYCORE_PUBLIC_URL = 'https://beautycore-demo.onrender.com'",
        "BEAUTYCORE_PUBLIC_URL = ''  # Validation first; connect in the final cell after acceptance.")
    runner = replace_once(runner, "if not ctypes.util.find_library(\"portaudio\"):",
        "if any(not ctypes.util.find_library(lib) for lib in ('portaudio', 'EGL', 'GLESv2')):")
    runner = replace_once(runner, '["apt-get", "install", "-y", "libportaudio2"]',
        '["apt-get", "install", "-y", "libportaudio2", "libegl1", "libgles2"]')
    anchor = '    gpu_code = f"""from pathlib import Path'
    detector_probe = '''    command([str(api_python), "-c", "from PIL import Image; from app.photo_suitability import check_subject; assert not check_subject(Image.new('RGB',(512,512),'white'), 'makeup')"],
            CPU_ROOT, cpu_env, "face-detector-load")
'''
    runner = replace_once(runner, anchor, detector_probe + anchor)
    runner = replace_once(runner,
        'record = {"status": "READY_FOR_REHEARSAL", "url": match[0], "api_pid": api.pid,',
        'record = {"status": "READY_FOR_REHEARSAL", "session_id": session_id, "started_at": started_at, "url": match[0], "api_pid": api.pid,')
    # Reuse the current release's complete readiness validator, including all IDs.
    tree = ast.parse((ROOT / 'deploy/runpod/runtime.py').read_text())
    validator = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'check_readiness')
    runner = ast.unparse(validator) + '\nBACKUP_CATALOG = ' + repr(manifest['catalog']) + '\n' + runner
    runner = replace_once(runner, '    capabilities = readiness.get("style_capabilities", {})',
        '    check_readiness(readiness, STYLE_RELEASE_EXPECTED, BACKUP_CATALOG)\n    capabilities = readiness.get("style_capabilities", {})')
    runner += "\nprint('KAGGLE_BACKUP_READY_FOR_VALIDATION: 18 Hair, 13 Makeup, 8 Nails; website not connected.')\n"
    controls = (ROOT / 'scripts/kaggle_backup_controls.py').read_text()
    controls += "\nbackup_validate(CLIENT_WORK)\n"
    connect = """# Run only after reviewing the validation and real generation outputs.
# Stop the other provider first and allow its normal registration lease to expire.
VISUAL_ACCEPTANCE_CONFIRMED = False  # Change to True only after reviewing this session's outputs.
backup_connect(CLIENT_WORK, 'https://beautycore-demo.onrender.com', visual_accepted=VISUAL_ACCEPTANCE_CONFIRMED)
"""
    intro = '''# BeautyCore current Kaggle backup, 13 November 2026

18 Hair, 13 Makeup and 8 Nails, including expanded styles and the accepted corrective Makeup adapter. Includes local subject checks and preference based consultation. Photos stay out of Gemini. Camera and training methodology remain on the Render website.

Use a copy of the previously successful Kaggle notebook with its ORIGINAL reviewed environment (Python 3.12.13, Torch 2.10.0+cu128, CUDA 12.8, Tesla T4), Internet enabled, and the two unchanged private binary inputs. A new notebook's Original environment may already be incompatible. Cell 1 refuses a mismatch; never remove its guards. Enable AI_BACKEND_API_KEY, AI_REMOTE_API_KEY and GEMINI_API_KEY privately in Kaggle Secrets.

Run setup, startup and validation in order. Startup does not register with Render. Real generation acceptance is still required. Run the final connection cell only after acceptance and stopping the other provider. See START-HERE.md. This notebook does not make Kaggle an always running service.
'''
    cells = [('markdown', intro), ('code', prep), ('code', runner),
             ('code', controls), ('markdown', '## Explicit website connection\nDo not Run All. Run this last cell manually only after validation and visual acceptance.\n'),
             ('code', connect)]
    book['cells'] = []
    for index, (kind, source) in enumerate(cells):
        cell = {'cell_type':kind, 'id':f'backup-current-{index}', 'metadata':{}, 'source':source.splitlines(keepends=True)}
        if kind == 'code':
            compile(source, f'backup-cell-{index}', 'exec')
            cell.update(execution_count=None, outputs=[])
        book['cells'].append(cell)
    output.mkdir(parents=True)
    (output / NAME).write_text(json.dumps(book, indent=1) + '\n', encoding='utf-8')
    shutil.copyfile(ROOT / 'docs/guides/kaggle-current-backup.md', output / 'START-HERE.md')
    shutil.copyfile(ROOT / 'scripts/makeup_corrective_application_probe.py', output / 'makeup_corrective_application_probe.py')
    for name in serving.NAMES:
        shutil.copyfile(package / 'inputs' / name, output / name)
    report = {'schema':'beautycore-kaggle-backup-v1', 'release_id':manifest['release_id'],
        'catalog':manifest['catalog'], 'cpu_updates':inventory, 'original_notebook_sha256':serving.NOTEBOOK_SHA,
        'validation_status':'LOCAL_PREPARATION_ONLY', 'real_kaggle_validated':False, 'production_registered':False,
        'files':{p.name:serving.digest(p) for p in output.iterdir() if p.is_file()}}
    (output / 'backup-manifest.json').write_text(json.dumps(report, indent=2) + '\n')
    with ZipFile(output.with_suffix('.zip'), 'x', compression=ZIP_STORED) as archive:
        for path in sorted(output.iterdir()):
            archive.write(path, path.name)
    with ZipFile(output.with_suffix('.zip')) as archive:
        if archive.testzip():
            raise ValueError('Backup ZIP integrity failed')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--serving-package', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(build(args.output, args.serving_package), indent=2))
