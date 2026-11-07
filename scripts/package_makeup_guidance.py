"""Build one private cached-session MAKEUP-QA-003 cell; no portraits or weights embedded."""
import argparse
import base64
from hashlib import sha256
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_FILES = ("scripts/makeup_guidance_diagnostic.py", "data/makeup/MAKEUP-QA-003/plan.json")


def cell():
    from scripts.makeup_guidance_diagnostic import validate_plan
    plan = json.loads((ROOT / SOURCE_FILES[1]).read_text())
    validate_plan(plan)
    frozen = json.loads((ROOT / "docs/experiments/makeup-quality-diagnostic-20261025.json").read_text())
    original = {name: {"sha256": value} for name, value in frozen["source_hashes"].items()}
    files = {}
    for name in SOURCE_FILES:
        raw = (ROOT / name).read_bytes()
        files[name] = {"sha256": sha256(raw).hexdigest(), "data": base64.b64encode(raw).decode()}
    code = """# ONE NEW cell in the SAME completed private Makeup diagnostic notebook.
# Keep the old cells/results unchanged. Five new forwards, no model download/install.
from pathlib import Path
from hashlib import sha256
from zipfile import ZipFile, ZIP_DEFLATED
import base64, json, subprocess, sys, uuid

QA3_FILES = __FILES__
QA3_ORIGINAL = __ORIGINAL__

def launch_makeup_guidance():
    if 'MAKEUP_WORK' not in globals():
        raise RuntimeError('The cached diagnostic session is unavailable. Do not run old cells; request a fresh adjustment notebook.')
    work = Path(MAKEUP_WORK).resolve()
    if work.parent != Path('/kaggle/working') or not work.name.startswith('beautycore-makeup-quality-'):
        raise RuntimeError('Expected the completed owned Makeup diagnostic workspace.')
    if json.loads((work / 'candidate.json').read_text()) != QA3_ORIGINAL:
        raise RuntimeError('Original source inventory differs.')
    for name, row in QA3_ORIGINAL.items():
        if sha256((work / 'gpu-src' / name).read_bytes()).hexdigest() != row['sha256']:
            raise RuntimeError('Frozen diagnostic source differs: ' + name)
    if (any(work.glob('results-guidance-*')) or
            any(work.glob('beautycore-makeup-guidance-results-*.zip'))):
        raise RuntimeError('A guidance follow-up was already attempted here. Return its ZIP instead of generating again.')
    plan_name = 'data/makeup/MAKEUP-QA-003/plan.json'
    plan = json.loads(base64.b64decode(QA3_FILES[plan_name]['data'], validate=True))
    reports = list(work.glob('results-adjustment-*/report.json'))
    matches = [p for p in reports if sha256(p.read_bytes()).hexdigest() == plan['reference_report_sha256']]
    if len(matches) != 1:
        raise RuntimeError('Expected exactly one reviewed completed adjustment report. Keep that session and its results intact.')
    reference = matches[0].parent
    if any((work / name).exists() for name in
           ('.makeup-adjustment.lock', '.makeup-quality-continuation.lock', '.makeup-guidance.lock')):
        raise RuntimeError('Another diagnostic is still running; do not start a second GPU child.')
    run_id = uuid.uuid4().hex[:10]
    written = {}
    for name, row in QA3_FILES.items():
        raw = base64.b64decode(row['data'], validate=True)
        if sha256(raw).hexdigest() != row['sha256']:
            raise RuntimeError('Guidance source integrity differs.')
        if name.endswith('.py'):
            target = work / 'gpu-src/scripts' / ('makeup_guidance_' + run_id + '.py')
        else:
            target = work / 'gpu-src/data/makeup/MAKEUP-QA-003' / ('plan-' + run_id + '.json')
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as stream:
            stream.write(raw)
        written[name] = target
    output = work / ('results-guidance-' + run_id)
    evidence = work / 'setup-evidence' / ('guidance-' + run_id)
    result_zip = work / ('beautycore-makeup-guidance-results-' + run_id + '.zip')
    receipt = work / ('guidance-sources-' + run_id + '.json')
    receipt.write_text(json.dumps({
        'experiment': 'MAKEUP-QA-003',
        'files': {name: {'sha256': row['sha256']} for name, row in QA3_FILES.items()},
        'reference_report_sha256': plan['reference_report_sha256'],
        'retained_cases': 8, 'expected_new_calls': 5,
        'new_download': False, 'new_install': False, 'production_change': False}, indent=2) + '\\n')
    print('MAKEUP_GUIDANCE WORKSPACE:', work, flush=True)
    print('8 saved controls + 1 repeated guidance3.0 control + 4 guidance2.5 candidates. Same adapter at1.0; unchanged20steps/seed/resolution.', flush=True)
    try:
        subprocess.run([sys.executable, str(written['scripts/makeup_guidance_diagnostic.py']),
                        '--bootstrap', '--output', str(output),
                        '--plan', str(written[plan_name]), '--reference', str(reference),
                        '--evidence', str(evidence)], cwd=work / 'gpu-src', check=True)
    finally:
        with ZipFile(result_zip, 'x', ZIP_DEFLATED) as archive:
            for file in sorted(output.rglob('*')):
                if file.is_file():
                    archive.write(file, 'results/' + file.relative_to(output).as_posix())
            for file in sorted((work / 'setup-evidence').rglob('*')):
                if file.is_file():
                    archive.write(file, file.relative_to(work).as_posix())
            archive.write(work / 'candidate.json', 'candidate.json')
            archive.write(receipt, receipt.name)
            for name, path in written.items():
                archive.write(path, 'experiment-sources/' + name)
        print('DOWNLOAD_MAKEUP_GUIDANCE_RESULTS:', result_zip, flush=True)
    print('Finished. Return the new ZIP for quality review. Website/models unchanged.', flush=True)

launch_makeup_guidance()
"""
    result = code.replace("__FILES__", repr(files)).replace("__ORIGINAL__", repr(original))
    compile(result, "makeup-adjustment-cell", "exec")
    return result


def build(output):
    output = Path(output)
    if output.exists():
        raise ValueError("Refusing to overwrite a prepared cell")
    code = cell()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(code, encoding="utf-8")
    return {"path": str(output), "sha256": sha256(output.read_bytes()).hexdigest(),
            "expected_new_calls": 5, "retained_cases": 8, "private_portrait_payload": False,
            "sources": {name: sha256((ROOT / name).read_bytes()).hexdigest() for name in SOURCE_FILES}}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.output), indent=2))

