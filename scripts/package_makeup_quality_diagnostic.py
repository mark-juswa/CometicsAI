"""Package a fresh PRIVATE Makeup diagnostic. Portraits remain in ignored artifacts."""
import argparse
import base64
from hashlib import sha256
import json
from pathlib import Path

from scripts.package_style_expansion_pilot import preparation_cell

ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = ROOT / "data/makeup/MAKEUP-QA-001/plan.json"
FILES = ("scripts/style_expansion_bootstrap.py", "scripts/makeup_quality_bootstrap.py",
         "scripts/makeup_quality_diagnostic.py", "data/makeup/MAKEUP-QA-001/plan.json")
DATASET = ROOT / ".tmp/data_m001/paired_selection/final_v1"


def source_payloads(plan, dataset=DATASET):
    pairs = json.loads((dataset / "manifests/pairs.json").read_text(encoding="utf-8"))
    assets = {}
    for subject in plan["subjects"]:
        candidates = [r for r in pairs if r["identity_id"] == subject["id"] and r["split"] == "validation"]
        if not candidates:
            raise ValueError("Diagnostic input is not a recorded validation source")
        row = candidates[0]
        raw = (dataset / row["reference"]).read_bytes()
        if sha256(raw).hexdigest() != subject["sha256"] or row["source_sha256"] != subject["sha256"]:
            raise ValueError("Diagnostic source differs from original paired manifest")
        assets[subject["filename"]] = {"data": base64.b64encode(raw).decode(), "sha256": subject["sha256"]}
    return assets


def make_preparation(files, assets):
    code = preparation_cell(files, assets)
    code = code.replace("# Isolated STYLE-EXP-001. Keep this notebook private: it embeds an evaluation hand.",
                        "# Private MAKEUP-QA-001. Contains two reused evaluation portraits.")
    code = code.replace("beautycore-styles-", "beautycore-makeup-quality-")
    code = code.replace("STYLE_PILOT_WORKSPACE:", "MAKEUP_QA_WORKSPACE:")
    code = code.replace("Run the next cell once for 15 diffusion outputs plus 3 renderer looks.",
                        "Run the next cell once for 12 matched Makeup outputs.")
    code = code.replace("STYLE_WORK = prepare()", "MAKEUP_WORK = prepare()")
    code += """
driver = MAKEUP_WORK / 'gpu-src/scripts/makeup_quality_bootstrap.py'
with driver.open('xb') as stream:
    stream.write((MAKEUP_WORK / 'overlay/scripts/makeup_quality_bootstrap.py').read_bytes())
"""
    return code


EXECUTION_CELL = """# Private diagnostic only. No API Secrets, server, tunnel or Render changes.
from zipfile import ZipFile, ZIP_DEFLATED
import subprocess

result_zip = MAKEUP_WORK / 'beautycore-makeup-quality-results.zip'
if result_zip.exists():
    raise RuntimeError('Diagnostic already attempted here. Preserve results before preparing a new workspace.')
try:
    subprocess.run([sys.executable, str(MAKEUP_WORK / 'gpu-src/scripts/makeup_quality_bootstrap.py')],
                   cwd=MAKEUP_WORK / 'gpu-src', check=True)
finally:
    with ZipFile(result_zip, 'x', ZIP_DEFLATED) as archive:
        for folder in ('results', 'setup-evidence'):
            for path in sorted((MAKEUP_WORK / folder).rglob('*')):
                if path.is_file():
                    archive.write(path, path.relative_to(MAKEUP_WORK).as_posix())
        archive.write(MAKEUP_WORK / 'candidate.json', 'candidate.json')
    print('DOWNLOAD_MAKEUP_RESULTS:', result_zip, flush=True)
print('Diagnostic finished. Review natural complexion AND useful makeup before selecting a setting.', flush=True)
"""



def continuation_cell():
    """Preserve the frozen v1 source and eight results; embed only new recovery code."""
    import ast
    old = ROOT / "artifacts/makeup-quality-20261025/beautycore_makeup_quality_diagnostic.ipynb"
    book = json.loads(old.read_text(encoding="utf-8"))
    tree = ast.parse("".join(book["cells"][1]["source"]))
    original = next(ast.literal_eval(node.value) for node in tree.body if isinstance(node, ast.Assign)
                    and isinstance(node.targets[0], ast.Name) and node.targets[0].id == "FILES")
    expected = {name: {"sha256": row["sha256"]} for name, row in original.items()}
    files = {}
    for name in ("scripts/makeup_quality_diagnostic.py", "scripts/makeup_quality_resume_bootstrap.py"):
        raw = (ROOT / name).read_bytes()
        files[name] = {"data": base64.b64encode(raw).decode(), "sha256": sha256(raw).hexdigest()}
    code = """# NEW cell in the SAME failed Makeup notebook. Keep old cells/results unchanged.
from pathlib import Path
from hashlib import sha256
from zipfile import ZipFile, ZIP_DEFLATED
import base64, json, subprocess, sys, uuid

FILES = __FILES__
ORIGINAL = __ORIGINAL__
if 'MAKEUP_WORK' not in globals():
    raise RuntimeError('Original workspace is unavailable. Use the corrected v2 notebook in a new session.')
work = Path(MAKEUP_WORK).resolve()
if work.parent != Path('/kaggle/working') or not work.name.startswith('beautycore-makeup-quality-'):
    raise RuntimeError('Not the expected owned Makeup diagnostic workspace.')
if json.loads((work / 'candidate.json').read_text()) != ORIGINAL:
    raise RuntimeError('Original source inventory differs; preserve the existing ZIP.')
for name, row in ORIGINAL.items():
    if sha256((work / 'gpu-src' / name).read_bytes()).hexdigest() != row['sha256']:
        raise RuntimeError('Original source changed: ' + name)
log = work / 'setup-evidence/diagnostic.log'
if 'Setting requires_grad=True on inference tensor outside InferenceMode is not allowed.' not in log.read_text():
    raise RuntimeError('This continuation is only for the confirmed tensor restoration error.')
for previous in work.glob('results-resume-*/report.json'):
    if json.loads(previous.read_text()).get('status') == 'DIAGNOSTIC_COMPLETE_REQUIRES_VISUAL_REVIEW':
        raise RuntimeError('A completed continuation already exists. Download it instead of generating again.')
run_id = uuid.uuid4().hex[:10]
written = {}
for name, row in FILES.items():
    raw = base64.b64decode(row['data'], validate=True)
    if sha256(raw).hexdigest() != row['sha256']:
        raise RuntimeError('Recovery source integrity differs.')
    target = work / 'gpu-src/scripts' / (Path(name).stem + '_resume_' + run_id + '.py')
    with target.open('xb') as stream:
        stream.write(raw)
    written[name] = target
output = work / ('results-resume-' + run_id)
evidence = work / 'setup-evidence' / ('continuation-' + run_id)
receipt = work / ('resume-sources-' + run_id + '.json')
receipt.write_text(json.dumps({'files': {name: {'sha256': row['sha256']} for name, row in FILES.items()},
    'original_report_sha256': sha256((work / 'results/report.json').read_bytes()).hexdigest(),
    'expected_calls': 5, 'kept_old_images': 8, 'model_download': False,
    'note': 'One continuity control and four missing reduced-adapter images.'}, indent=2))
result_zip = work / ('beautycore-makeup-quality-resumed-' + run_id + '.zip')
try:
    subprocess.run([sys.executable, str(written['scripts/makeup_quality_resume_bootstrap.py']),
                   '--runner', str(written['scripts/makeup_quality_diagnostic.py']),
                   '--output', str(output), '--evidence', str(evidence)],
                   cwd=work / 'gpu-src', check=True)
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
    print('DOWNLOAD_RESUMED_MAKEUP_RESULTS:', result_zip, flush=True)
print('Finished. Send the new ZIP for visual review; original files and deployed settings unchanged.', flush=True)
"""
    return code.replace("__FILES__", repr(files)).replace("__ORIGINAL__", repr(expected))

def build(output):
    output = Path(output)
    if output.exists():
        raise ValueError("Refusing to overwrite an existing diagnostic notebook")
    plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
    from scripts.makeup_quality_diagnostic import validate_plan
    validate_plan(plan)
    assets = source_payloads(plan)
    files = {}
    for name in FILES:
        raw = (ROOT / name).read_bytes()
        files[name] = {"data": base64.b64encode(raw).decode(), "sha256": sha256(raw).hexdigest()}
    code = make_preparation(files, assets)
    compile(code, "makeup-quality-preparation", "exec")
    compile(EXECUTION_CELL, "makeup-quality-execution", "exec")
    book = {"nbformat": 4, "nbformat_minor": 5,
            "metadata": {"kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"}},
            "cells": [
                {"cell_type": "markdown", "metadata": {}, "source": [
                    "# BeautyCore private Makeup complexion diagnostic\n",
                    "Fresh PRIVATE notebook, reviewed T4 image and Internet. Attach exactly one original GPU bundle "
                    "named capstone_train002_20260928_v1.bin. No CPU bundle or API Secrets.\n",
                    "Twelve outputs: two reused validation portraits x Natural/Classic Red Lip x foundation only, "
                    "current adapter (1.0), reduced adapter (0.5). Same prompts, seed, steps, guidance and source. "
                    "No new training, masks, recoloring or automatic production changes.\n",
                    "Strict original artifact/environment checks remain. Scratch selection checks actual free space "
                    "and keeps the original 30 GiB guard. GPU setup/model download take time. Progress prints per case.\n",
                    "This private notebook embeds existing research portraits. Do not publish it or its results. "
                    "These people are reused diagnostic development cases, not an untouched final test set.\n",
                    "Actual adapter layer scaling/tensors are verified and full influence is restored afterward. "
                    "Restoration is a state check, not an extra generated image. Reduced influence may not fix whitening.\n",
                    "Download beautycore-makeup-quality-results.zip from the printed working folder and return it for review. "
                    "Failure also produces a partial ZIP. Do not mix old style-pilot recovery cells into this notebook.\n"]},
                {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [],
                 "source": code.splitlines(keepends=True)},
                {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [],
                 "source": EXECUTION_CELL.splitlines(keepends=True)}]}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(book, indent=2) + "\n", encoding="utf-8")
    return {"notebook": str(output), "sha256": sha256(output.read_bytes()).hexdigest(),
            "source_hashes": {k: v["sha256"] for k, v in files.items()},
            "portrait_hashes": {k: v["sha256"] for k, v in assets.items()},
            "expected_outputs": 12, "includes_private_portraits": True,
            "includes_weights": False, "includes_secret_values": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT /
                        "artifacts/makeup-quality-20261025/beautycore_makeup_quality_diagnostic.ipynb")
    args = parser.parse_args()
    print(json.dumps(build(args.output), indent=2))
