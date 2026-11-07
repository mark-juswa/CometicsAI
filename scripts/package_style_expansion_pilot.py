"""Build a PRIVATE offline pilot notebook; embeds a historical hand/mask, no weights or secrets."""
import argparse
import base64
from hashlib import sha256
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = (
    "scripts/inference_performance.py", "scripts/unified_gate3_server.py",
    "scripts/style_expansion_pilot.py", "scripts/style_expansion_nails.py",
    "scripts/style_expansion_bootstrap.py", "backend/app/nails/geometry.py",
    "data/style-expansion/STYLE-EXP-001/pilot.json",
)
FIXTURE_ROOT = ROOT / "data/nails/work/manual-mask-ceiling-20260927"
ASSETS = {
    "hand.png": (FIXTURE_ROOT / "0000045_original.png",
                 "c483244132e74ffc6e492271e742c17dce4ce694050abab78c43bc306dd4fd98"),
    "mask.png": (FIXTURE_ROOT / "0000045_manual_mask.png",
                 "91580d510e48b4e09dbb5bea464a3a4bc58cbd7ee06226b9de4b4b8947ceb936"),
}
BUNDLE = "capstone_train002_20260928_v1.bin"
BUNDLE_SHA = "f0d1fed52e00b6c5a1da2cade3731237675cdebbfc0b2cde3b2dbda99a4019ac"


def preparation_cell(files, assets):
    code = """# Isolated STYLE-EXP-001. Keep this notebook private: it embeds an evaluation hand.
from pathlib import Path, PurePosixPath
from hashlib import sha256
from zipfile import ZipFile
import base64, json, socket, sys, uuid

FILES = __FILES__
ASSETS = __ASSETS__
BUNDLE = __BUNDLE__
BUNDLE_SHA = __SHA__


def safe_path(root, name):
    p = PurePosixPath(name)
    if not name or p.is_absolute() or ':' in name or chr(92) in name or '..' in p.parts:
        raise ValueError('Unsafe pilot path')
    target = (root / name).resolve()
    if not target.is_relative_to(root.resolve()):
        raise ValueError('Pilot path escapes workspace')
    return target


def extract_gpu(source, target, expected):
    if target.exists():
        raise ValueError('Fresh extraction folder required')
    with source.open('rb') as stream:
        digest = sha256()
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    if digest.hexdigest() != expected:
        raise ValueError('GPU bundle differs from the reviewed original')
    with ZipFile(source) as archive:
        manifest = json.loads(archive.read('gate3_bundle.json'))
        names = archive.namelist()
        if len(names) != len(set(names)) or set(names) != set(manifest['files']) | {'gate3_bundle.json'}:
            raise ValueError('GPU bundle inventory differs')
        if archive.testzip() is not None:
            raise ValueError('GPU bundle CRC differs')
        for name in names:
            destination = safe_path(target, name)
            raw = archive.read(name)
            if name != 'gate3_bundle.json' and sha256(raw).hexdigest() != manifest['files'][name]:
                raise ValueError('GPU member differs: ' + name)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(raw)


def prepare(inputs=Path('/kaggle/input'), working=Path('/kaggle/working')):
    if sys.platform != 'linux':
        raise RuntimeError('Run the GPU notebook inside a separate Kaggle session')
    for port in (8765, 8800):
        with socket.socket() as connection:
            connection.settimeout(1)
            if connection.connect_ex(('127.0.0.1', port)) == 0:
                raise RuntimeError('An AI service is running; do not use this session')
    matches = sorted(inputs.rglob(BUNDLE))
    print('GPU bundle matches:', len(matches), flush=True)
    if len(matches) != 1:
        for match in matches:
            print(match, flush=True)
        raise ValueError('Attach exactly ONE input containing ' + BUNDLE + '; visibility does not matter')
    work = working / ('beautycore-styles-' + uuid.uuid4().hex[:12])
    extract_gpu(matches[0], work / 'gpu-src', BUNDLE_SHA)
    for name, item in FILES.items():
        raw = base64.b64decode(item['data'], validate=True)
        if sha256(raw).hexdigest() != item['sha256']:
            raise ValueError('Experimental source differs')
        target = safe_path(work / 'overlay', name)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    for name, item in ASSETS.items():
        raw = base64.b64decode(item['data'], validate=True)
        if sha256(raw).hexdigest() != item['sha256']:
            raise ValueError('Reviewed hand/mask differs')
        target = safe_path(work / 'fixtures', name)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    (work / 'candidate.json').write_text(json.dumps(
        {name: {'sha256': item['sha256']} for name, item in FILES.items()}, indent=2))
    # Only this NEW script is copied before original preflight. No original member is replaced.
    target = work / 'gpu-src/scripts/style_expansion_bootstrap.py'
    target.write_bytes((work / 'overlay/scripts/style_expansion_bootstrap.py').read_bytes())
    print('STYLE_PILOT_WORKSPACE:', work, flush=True)
    print('Prepared only. Run the next cell once for 15 diffusion outputs plus 3 renderer looks.', flush=True)
    return work


STYLE_WORK = prepare()
"""
    return code.replace("__FILES__", repr(files)).replace("__ASSETS__", repr(assets)).replace(
        "__BUNDLE__", repr(BUNDLE)).replace("__SHA__", repr(BUNDLE_SHA))



def recovery_cell():
    """Same-session, scratch-only recovery; source changes have their own receipt."""
    raw = (ROOT / "scripts/style_expansion_bootstrap.py").read_bytes()
    code = """# Paste into a NEW cell in the SAME failed pilot notebook. Do not rerun old cells.
from pathlib import Path
from hashlib import sha256
from zipfile import ZipFile, ZIP_DEFLATED
import base64, json, subprocess, sys, uuid

SOURCE = __SOURCE__
EXPECTED = __EXPECTED__
if 'STYLE_WORK' not in globals():
    raise RuntimeError('The old pilot workspace is unavailable. Use the corrected v2 notebook in a new session.')
work = Path(STYLE_WORK).resolve()
if work.parent != Path('/kaggle/working') or not work.name.startswith('beautycore-styles-'):
    raise RuntimeError('This is not an owned STYLE-EXP-001 Kaggle workspace.')
failure_log = work / 'setup-evidence/base_download.log'
if not failure_log.is_file() or 'Less than 30 GiB scratch available for pinned Base, no model download started' not in failure_log.read_text():
    raise RuntimeError('This recovery is only for the confirmed scratch-space failure.')
if (work / 'results').exists():
    raise RuntimeError('Results already exist. Preserve them; do not regenerate over completed work.')
raw = base64.b64decode(SOURCE, validate=True)
if sha256(raw).hexdigest() != EXPECTED:
    raise RuntimeError('Recovery source integrity failed.')
run_id = uuid.uuid4().hex[:10]
runner = work / 'gpu-src/scripts' / ('style_expansion_scratch_resume_' + run_id + '.py')
with runner.open('xb') as stream:
    stream.write(raw)
receipt = work / ('recovery-source-' + run_id + '.json')
receipt.write_text(json.dumps({'bootstrap_sha256': EXPECTED, 'source_filename': runner.name,
                               'reason': 'scratch cache selection; preserve original model guards'}, indent=2))
result_zip = work / ('beautycore-style-expansion-recovery-results-' + run_id + '.zip')
try:
    subprocess.run([sys.executable, str(runner), '--resume-after-scratch-failure'],
                   cwd=work / 'gpu-src', check=True)
finally:
    with ZipFile(result_zip, 'x', ZIP_DEFLATED) as archive:
        for folder in ('results', 'setup-evidence'):
            for path in sorted((work / folder).rglob('*')):
                if path.is_file():
                    archive.write(path, path.relative_to(work).as_posix())
        archive.write(work / 'candidate.json', 'candidate.json')
        archive.write(receipt, receipt.name)
    print('DOWNLOAD_RECOVERY_RESULTS:', result_zip, flush=True)
print('Recovery finished. Review the images; public styles remain unchanged.', flush=True)
"""
    return code.replace("__SOURCE__", repr(base64.b64encode(raw).decode())).replace(
        "__EXPECTED__", repr(sha256(raw).hexdigest()))

EXECUTION_CELL = """# Run only after preparation succeeded. No API Secrets or website registration.
from zipfile import ZipFile, ZIP_DEFLATED
import subprocess

result_zip = STYLE_WORK / 'beautycore-style-expansion-results.zip'
if result_zip.exists():
    raise RuntimeError('Pilot already ran here. Preserve/download results before a new separate run.')
try:
    subprocess.run([sys.executable, str(STYLE_WORK / 'gpu-src/scripts/style_expansion_bootstrap.py')],
                   cwd=STYLE_WORK / 'gpu-src', check=True)
finally:
    # Preserve partial evidence if setup/inference fails; never include weights, environments or credentials.
    with ZipFile(result_zip, 'x', ZIP_DEFLATED) as archive:
        for folder in ('results', 'setup-evidence'):
            for path in sorted((STYLE_WORK / folder).rglob('*')):
                if path.is_file():
                    archive.write(path, path.relative_to(STYLE_WORK).as_posix())
        archive.write(STYLE_WORK / 'candidate.json', 'candidate.json')
    print('DOWNLOAD_RESULTS:', result_zip, flush=True)
print('Pilot finished. Outputs need visual review; public styles have not changed.', flush=True)
"""


def build(output):
    output = Path(output)
    if output.exists():
        raise ValueError("Refusing to overwrite an earlier private pilot notebook")
    payload = {}
    for name in FILES:
        raw = (ROOT / name).read_bytes()
        payload[name] = {"data": base64.b64encode(raw).decode(), "sha256": sha256(raw).hexdigest()}
    assets = {}
    for name, (path, digest) in ASSETS.items():
        raw = path.read_bytes()
        if sha256(raw).hexdigest() != digest:
            raise ValueError("Historical reviewed fixture differs: " + name)
        assets[name] = {"data": base64.b64encode(raw).decode(), "sha256": digest}
    cells = [preparation_cell(payload, assets), EXECUTION_CELL]
    for code in cells:
        compile(code, "style-expansion-cell", "exec")
    book = {"nbformat": 4, "nbformat_minor": 5,
            "metadata": {"kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"}},
            "cells": [{"cell_type": "markdown", "metadata": {}, "source": [
                "# BeautyCore private style expansion pilot\\n".replace("\\n", "\n"),
                "Use a NEW private Kaggle notebook based on the reviewed T4 environment. Attach one input containing "
                + BUNDLE + ". No CPU bundle, Secrets, tunnel or Render edits. Keep the demo notebook intact.\n",
                "This is a pilot, not training: 3 new Hair prompts across 2 existing adapters, 2 Makeup prompts, "
                "5 old-style controls, 2 restoration checks = 15 diffusion outputs, plus 3 experimental renderer looks. "
                "One reused input per feature; no new generalization claim. Progress prints per case.\n",
                "Strict original bundle, adapter and environment checks remain. A host mismatch stops. "
                "Do not bypass pins. Setup includes a model download and may take substantial time; no fixed completion-time guarantee.\n",
                "The embedded full-hand fixture/manual mask are reused research validation assets. Keep the notebook and "
                "results private. The renderer test bypasses segmentation and does not prove live upload quality.\n",
                "After the run, download beautycore-style-expansion-results.zip from the printed working folder. "
                "Return the ZIP for visual review; no new styles are activated automatically.\n"]}] +
            [{"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [],
              "source": code.splitlines(keepends=True)} for code in cells]}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(book, indent=2) + "\n", encoding="utf-8")
    return {"notebook": str(output), "sha256": sha256(output.read_bytes()).hexdigest(),
            "includes_weights": False, "includes_secrets": False, "includes_private_fixture": True,
            "source_hashes": {name: item["sha256"] for name, item in payload.items()}}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT /
                        "artifacts/style-expansion-20261025/beautycore_style_expansion_pilot.ipynb")
    print(json.dumps(build(parser.parse_args().output), indent=2))
