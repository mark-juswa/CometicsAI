"""Build a private Hair-only notebook from existing documented research photos."""
import argparse
import base64
from hashlib import sha256
import json
from pathlib import Path
from zipfile import ZipFile

from scripts.package_style_expansion_pilot import preparation_cell, BUNDLE, BUNDLE_SHA
from scripts.hair_expansion_validation import cases

ROOT = Path(__file__).resolve().parents[1]
FILES = ("scripts/style_expansion_bootstrap.py", "scripts/makeup_quality_diagnostic.py",
         "scripts/hair_expansion_bootstrap.py", "scripts/hair_expansion_validation.py",
         "data/style-expansion/HAIR-EXP-002/plan.json")
EXECUTION = """# Isolated private test. No API Secrets, tunnel, website registration or training.
import os, signal, subprocess, sys
from zipfile import ZipFile, ZIP_DEFLATED
result_zip = HAIR_WORK / 'beautycore-hair-expansion-results.zip'
marker = HAIR_WORK / 'hair-attempted'
if marker.exists() or result_zip.exists():
    raise RuntimeError('Already attempted. Download results; do not rerun over this experiment.')
marker.write_text('HAIR-EXP-002\\n', encoding='utf-8')
process = None
try:
    process = subprocess.Popen([sys.executable, str(HAIR_WORK / 'gpu-src/scripts/hair_expansion_bootstrap.py')],
                               cwd=HAIR_WORK / 'gpu-src', start_new_session=True)
    try:
        status = process.wait(timeout=7200)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGTERM)
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
        raise RuntimeError('Two-hour safety limit reached. Preserve logs and return the results ZIP.')
    if status:
        raise subprocess.CalledProcessError(status, process.args)
finally:
    if process is not None and process.poll() is None:
        os.killpg(process.pid, signal.SIGTERM)
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
    with ZipFile(result_zip, 'x', ZIP_DEFLATED) as archive:
        for folder in ('results', 'setup-evidence', 'fixtures'):
            for path in sorted((HAIR_WORK / folder).rglob('*')):
                if path.is_file():
                    archive.write(path, path.relative_to(HAIR_WORK).as_posix())
        archive.write(HAIR_WORK / 'candidate.json', 'candidate.json')
        archive.write(marker, marker.name)
        for name in FILES:
            archive.write(HAIR_WORK / 'overlay' / name, 'experiment-sources/' + name)
    print('DOWNLOAD_HAIR_RESULTS:', result_zip, flush=True)
print('Finished. Download and return the ZIP for visual review; no public styles changed.')
"""


def payloads():
    plan = json.loads((ROOT / FILES[-1]).read_text(encoding="utf-8"))
    if len(cases(plan)) != 21:
        raise ValueError("Expected exactly21 Hair calls")
    frozen_bundle = ROOT / "artifacts" / BUNDLE
    if sha256(frozen_bundle.read_bytes()).hexdigest() != BUNDLE_SHA:
        raise ValueError("Original GPU archive differs")
    registry_name = "backend/app/style_registry_train002_smoke.json"
    with ZipFile(frozen_bundle) as gpu:
        registry_raw = gpu.read(registry_name)
    if (sha256(registry_raw).hexdigest() != plan["registry_sha256"]
            or json.loads(registry_raw) != json.loads((ROOT / registry_name).read_text(encoding="utf-8"))):
        raise ValueError("Hair plan registry differs from the original GPU artifact")
    source = ROOT / "data/source" / plan["source_archive_filename"]
    if sha256(source.read_bytes()).hexdigest() != plan["source_archive_sha256"]:
        raise ValueError("Historical source archive differs")
    manifest = json.loads((ROOT / "docs/data/DATA-002-manifest.json").read_text(encoding="utf-8"))
    assets = {}
    with ZipFile(source) as archive:
        for subject in plan["subjects"]:
            original = next(row for row in manifest["samples"] if row["sample_id"] == subject["id"])
            if (original["split"] != "val" or original["source_sha256"] != subject["sha256"]
                    or original["source_member"] != subject["source_member"]):
                raise ValueError("Selected historical source metadata differs")
            raw = archive.read(subject["source_member"])
            if sha256(raw).hexdigest() != subject["sha256"]:
                raise ValueError("Historical source bytes differ")
            assets[subject["filename"]] = {"data": base64.b64encode(raw).decode(), "sha256": subject["sha256"]}
    files = {}
    for name in FILES:
        raw = (ROOT / name).read_bytes()
        if name.endswith(".py"):
            compile(raw, name, "exec")
        files[name] = {"data": base64.b64encode(raw).decode(), "sha256": sha256(raw).hexdigest()}
    return files, assets


def build(path):
    path = Path(path)
    if path.exists():
        raise ValueError("Refuse to overwrite a prepared Hair notebook")
    files, assets = payloads()
    prep = preparation_cell(files, assets)
    replacements = {
        "# Isolated STYLE-EXP-001. Keep this notebook private: it embeds an evaluation hand.":
            "# Private HAIR-EXP-002. Four historical research portraits; do not publish.",
        "beautycore-styles-": "beautycore-hair-",
        "STYLE_PILOT_WORKSPACE:": "HAIR_WORKSPACE:",
        "Run the next cell once for 15 diffusion outputs plus 3 renderer looks.":
            "Run Cell 2 once for21Hair images. No Makeup/Nails inference or live website connection.",
        "Reviewed hand/mask differs": "Historical Hair portrait differs",
        "STYLE_WORK = prepare()": "HAIR_WORK = prepare()",
    }
    for before, after in replacements.items():
        if before not in prep:
            raise ValueError("Notebook template anchor changed: " + before)
        prep = prep.replace(before, after)
    prep += """
driver = HAIR_WORK / 'gpu-src/scripts/hair_expansion_bootstrap.py'
with driver.open('xb') as file:
    file.write((HAIR_WORK / 'overlay/scripts/hair_expansion_bootstrap.py').read_bytes())
"""
    cells = []
    intro = """# BeautyCore private Hair expansion comparison — HAIR-EXP-002

Use a separate private copy of the tested pinned Kaggle GPU image. Select T4 and enable Internet.
Attach exactly ONE input containing capstone_train002_20260928_v1.bin.
No new CPU bundle, API Secrets or Render configuration is needed.

Five candidates: Butterfly Cut, Wolf Cut, Korean Two-Block, Korean Comma Hair and Textured French Bob with Wispy Bangs.
Four existing documented validation portraits are embedded: two long-haired and two with visible sides.
These are reused private development cases, not new untouched final evaluation. Original photo rights were not independently verified.
Keep the notebook and results private; source metadata/limits are preserved in the plan.

21 images:10 candidates +10 nearest-existing-style controls +1 adapter-restoration control.
One fixed prompt/adapter per style. Full existing adapters, guidance4.0,20steps,seed1977,512square.
At prior roughly64seconds per image, inference is about23minutes, plus installation/model download.
This is an estimate, not a measured duration for this batch.

Run Cell1 once, then Cell2 once. It prints each completed image and creates a downloadable ZIP, including partial evidence on failure.
Open results/review-self-contained.html after downloading/extracting for original/baseline/candidate comparisons.
No new training, auto-approval, public server, enabled Hair ID or deployment.
Return the ZIP for review before any Hair production integration.
"""
    for index, (kind, code) in enumerate((("markdown", intro), ("code", prep), ("code", EXECUTION))):
        cell = {"cell_type": kind, "id": "hair-expansion-" + str(index), "metadata": {},
                "source": code.splitlines(keepends=True)}
        if kind == "code":
            compile(code, "hair-cell-" + str(index), "exec")
            cell.update(execution_count=None, outputs=[])
        cells.append(cell)
    book = {"nbformat": 4, "nbformat_minor": 5,
            "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}},
            "cells": cells}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((json.dumps(book, indent=1) + "\n").encode())
    return {"date": "2026-10-30", "experiment": "HAIR-EXP-002", "status": "PREPARED_GPU_NOT_RUN",
            "notebook": str(path), "sha256": sha256(path.read_bytes()).hexdigest(),
            "bytes": path.stat().st_size, "expected_calls": 21,
            "source_sha256": {name: row["sha256"] for name, row in files.items()},
            "portrait_sha256": {name: row["sha256"] for name, row in assets.items()},
            "includes_private_portraits": True, "includes_weights": False, "includes_keys": False,
            "production_enabled": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    receipt = build(args.output)
    (ROOT / "docs/experiments/hair-expansion-preparation-20261030.json").write_bytes(
        (json.dumps(receipt, indent=2) + "\n").encode())
    print(json.dumps({k: v for k, v in receipt.items() if k not in ("source_sha256", "portrait_sha256")}, indent=2))
