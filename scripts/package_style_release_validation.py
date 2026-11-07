"""Package fresh private validation with four documented reused portraits, no weights/keys."""
import argparse
import base64
from hashlib import sha256
import json
from pathlib import Path
from scripts.package_style_expansion_pilot import preparation_cell
from scripts.package_makeup_quality_diagnostic import source_payloads
ROOT = Path(__file__).resolve().parents[1]
FILES = ("scripts/style_expansion_bootstrap.py", "scripts/makeup_quality_diagnostic.py",
         "scripts/style_release_bootstrap.py", "scripts/style_release_validation.py",
         "data/style-expansion/STYLE-VAL-001/plan.json")

EXECUTION = """# Run once in this fresh private notebook. No API Secrets or Render connection.
from zipfile import ZipFile, ZIP_DEFLATED
import subprocess
result_zip = VALIDATION_WORK / 'beautycore-release-validation-results.zip'
if result_zip.exists():
    raise RuntimeError('Already attempted. Download existing results rather than rerunning.')
try:
    subprocess.run([sys.executable, str(VALIDATION_WORK / 'gpu-src/scripts/style_release_bootstrap.py')],
                   cwd=VALIDATION_WORK / 'gpu-src', check=True)
finally:
    with ZipFile(result_zip, 'x', ZIP_DEFLATED) as archive:
        for folder in ('results', 'setup-evidence'):
            for path in sorted((VALIDATION_WORK / folder).rglob('*')):
                if path.is_file():
                    archive.write(path, path.relative_to(VALIDATION_WORK).as_posix())
        archive.write(VALIDATION_WORK / 'candidate.json', 'candidate.json')
        for name in FILES:
            archive.write(VALIDATION_WORK / 'overlay' / name, 'experiment-sources/' + name)
    print('DOWNLOAD_RELEASE_VALIDATION_RESULTS:', result_zip, flush=True)
print('Finished. Return ZIP for review. No styles or production settings enabled.', flush=True)
"""


def payloads():
    from scripts.style_release_validation import cases
    plan = json.loads((ROOT / FILES[-1]).read_text(encoding="utf-8"))
    if len(cases(plan)) != 29:
        raise ValueError("Expected29calls")
    assets = source_payloads({"subjects": plan["makeup_subjects"]})
    manifest = json.loads((ROOT / "docs/data/DATA-002-manifest.json").read_text(encoding="utf-8"))
    for row in plan["hair_subjects"]:
        frozen = next(r for r in manifest["samples"] if r["sample_id"] == row["id"])
        if frozen["split"] != "val" or frozen["source_sha256"] != row["sha256"]:
            raise ValueError("Hair source not the selected historical validation input")
        raw = (ROOT / "artifacts/style-expansion-20261025/release-validation-inputs" / row["filename"]).read_bytes()
        if sha256(raw).hexdigest() != row["sha256"]:
            raise ValueError("Hair input bytes differ")
        assets[row["filename"]] = {"data": base64.b64encode(raw).decode(), "sha256": row["sha256"]}
    files = {}
    for name in FILES:
        raw = (ROOT / name).read_bytes()
        files[name] = {"data": base64.b64encode(raw).decode(), "sha256": sha256(raw).hexdigest()}
    return files, assets


def build(output):
    output = Path(output)
    if output.exists():
        raise ValueError("Refuse to overwrite a prepared notebook")
    files, assets = payloads()
    prep = preparation_cell(files, assets)
    prep = prep.replace("# Isolated STYLE-EXP-001. Keep this notebook private: it embeds an evaluation hand.",
                        "# Private STYLE-VAL-001. Four reused research portraits; do not publish.")
    prep = prep.replace("beautycore-styles-", "beautycore-release-validation-")
    prep = prep.replace("STYLE_PILOT_WORKSPACE:", "RELEASE_VALIDATION_WORKSPACE:")
    prep = prep.replace("Run the next cell once for 15 diffusion outputs plus 3 renderer looks.",
                        "Run the next cell once for29portrait calls. No Nail GPU calls in this notebook.")
    prep = prep.replace("STYLE_WORK = prepare()", "VALIDATION_WORK = prepare()")
    prep += """
driver = VALIDATION_WORK / 'gpu-src/scripts/style_release_bootstrap.py'
with driver.open('xb') as stream:
    stream.write((VALIDATION_WORK / 'overlay/scripts/style_release_bootstrap.py').read_bytes())
"""
    for name, code in (("preparation", prep), ("execution", EXECUTION)):
        compile(code, name, "exec")
    book = {"nbformat": 4, "nbformat_minor": 5,
            "metadata": {"kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"}},
            "cells": [{"cell_type": "markdown", "metadata": {}, "source": [
                "# BeautyCore private release validation — STYLE-VAL-001\n",
                "Import into a NEW PRIVATE Kaggle notebook. Select the reviewed GPU T4 image; enable Internet. "
                "Attach exactly ONE input containing capstone_train002_20260928_v1.bin. No CPU bundle, API Secrets or website registration.\n",
                "29calls:10existing Makeup presets x2reused people at selected guidance2.5, "
                "2new Makeup prompts x2people at2.5, Curtain/Comma on2historical Hair validation inputs at4.0, "
                "then one makeup restoration image. Same full adapters,20steps,seed1977,512square. One foundation.\n",
                "Four original Natural/Red Lip outputs must match earlier selected2.5pixels. "
                "The final Makeup control must match its initial pixels after switching adapters. "
                "Mismatch stops and preserves partial evidence.\n",
                "At prior roughly64seconds/call, generation is about31minutes; setup/model download are extra. "
                "No new training, automatic quality approval, enabled style IDs, production prompt changes or Render deployment.\n",
                "Contains4reused research portraits with recorded source metadata. Do not publish notebook/results. "
                "These are development cases, not untouched final evaluation. Photo rights limitations are recorded in the plan.\n",
                "Automatic Nail masks/renderers are checked separately on the existing local CPU runtime; "
                "this notebook does not install CPU Nail models or alter the working demo.\n",
                "Run cell1once, then cell2once. Download the ZIP printed after DOWNLOAD_RELEASE_VALIDATION_RESULTS, "
                "including on failure, and return it for review.\n"]},
                {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": prep.splitlines(keepends=True)},
                {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": EXECUTION.splitlines(keepends=True)}]}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(book, indent=2) + "\n", encoding="utf-8")
    return {"notebook": str(output), "sha256": sha256(output.read_bytes()).hexdigest(),
            "source_hashes": {k: v["sha256"] for k, v in files.items()},
            "portrait_hashes": {k: v["sha256"] for k, v in assets.items()}, "expected_calls": 29,
            "includes_private_portraits": True, "includes_weights": False, "includes_keys": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    print(json.dumps(build(parser.parse_args().output), indent=2))

