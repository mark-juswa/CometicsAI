"""Package two private reference-conditioned MAKEUP-001 calls using old guards."""
import base64
from hashlib import sha256
import json
from pathlib import Path

from scripts.package_style_expansion_pilot import preparation_cell
from scripts.makeup_reference_diagnostic import validate_plan, INFERENCE

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "artifacts/makeup-complexion-release-20261105"
PLAN = ROOT / "data/makeup/MAKEUP-GUIDED-001/plan.json"
FILES = ("scripts/style_expansion_bootstrap.py", "scripts/makeup_quality_bootstrap.py",
         "scripts/makeup_quality_diagnostic.py", "scripts/makeup_reference_bootstrap.py",
         "scripts/makeup_reference_diagnostic.py", "data/makeup/MAKEUP-GUIDED-001/plan.json")


def payload(path):
    raw = Path(path).read_bytes()
    return {"data": base64.b64encode(raw).decode(), "sha256": sha256(raw).hexdigest()}


def build(output):
    output = Path(output)
    if output.exists() or PLAN.exists():
        raise ValueError("Preserve existing diagnostic plan/notebook; do not overwrite")
    original = json.loads((ROOT / "artifacts/makeup-refinement-20261105/catalog-review/plan.json").read_text())
    subjects = {s["id"]: s for s in original["sources"]}
    guide_paths = {
        "soft_glam": WORK / "teacher-proof/006553-soft-glam-v1/prepared.png",
        "bold_evening_glam": WORK / "teacher-proof/035149-bold-evening-source-protected-v2.png",
    }
    plan = {"schema": "makeup-reference-diagnostic-v1", "date": "2026-11-05",
            "production_enabled": False, "training": False, "inference": INFERENCE, "cases": []}
    assets = {}
    for source_id, style, guide_id in (("054109", "soft_glam", "006553"), ("056266", "bold_evening_glam", "035149")):
        source = subjects[source_id]
        row = {"source_id": source_id, "source_split": "validation", "source_photo": source["source_photo"],
            "style_id": style, "guide_identity_id": guide_id, "guide_source_split": "train",
            "guide_kind": "external-editor-synthetic-source-protected", "guide_tool": "built-in image_gen",
            "guide_tool_model_id": "not provided by tool", "guide_source_photo": subjects[guide_id]["source_photo"],
            "guide_review": "Direction approved on035149Bold only; not admitted as training or production asset.",
            "previous_kind": "rejected CPU whole-face-review compositor, not MAKEUP-001 baseline"}
        paths = {"source": ROOT / source["source"], "guide": guide_paths[style],
                 "previous": WORK / ("whole-face-review/results/" + source_id + "-" + style + ".png")}
        if sha256(paths["source"].read_bytes()).hexdigest() != source["sha256"]:
            raise ValueError("Original portrait differs")
        for kind, path in paths.items():
            name = source_id + "-" + style + "-" + kind + path.suffix
            assets[name] = payload(path)
            row[kind + "_filename"] = name
            row[kind + "_sha256"] = assets[name]["sha256"]
        plan["cases"].append(row)
    validate_plan(plan)
    PLAN.parent.mkdir(parents=True, exist_ok=True)
    PLAN.write_text(json.dumps(plan, indent=2) + "\n")
    files = {name: payload(ROOT / name) for name in FILES}
    prep = preparation_cell(files, assets)
    changes = {
        "# Isolated STYLE-EXP-001. Keep this notebook private: it embeds an evaluation hand.":
            "# Private MAKEUP-GUIDED-001. Contains research portraits and synthetic cosmetic guides.",
        "beautycore-styles-": "beautycore-makeup-reference-",
        "STYLE_PILOT_WORKSPACE:": "MAKEUP_REFERENCE_WORKSPACE:",
        "Run the next cell once for 15 diffusion outputs plus 3 renderer looks.": "Prepared for exactly TWO new Makeup generations.",
        "STYLE_WORK = prepare()": "MAKEUP_REFERENCE_WORK = prepare()",
    }
    for before, after in changes.items():
        if before not in prep:
            raise ValueError("Reviewed preparation template changed")
        prep = prep.replace(before, after)
    prep += "\nfor entry in ('makeup_quality_bootstrap.py', 'makeup_reference_bootstrap.py'):\n    target = MAKEUP_REFERENCE_WORK / 'gpu-src/scripts' / entry\n    with target.open('xb') as stream:\n        stream.write((MAKEUP_REFERENCE_WORK / 'overlay/scripts' / entry).read_bytes())\n"
    execute = '''# No training, API server, tunnel or Render change.
from zipfile import ZipFile, ZIP_DEFLATED
import subprocess

attempt = MAKEUP_REFERENCE_WORK / 'attempted'
with attempt.open('x') as marker:
    marker.write('Exactly two reference-conditioned generations; preserve partial results.\\n')
result_zip = MAKEUP_REFERENCE_WORK / 'beautycore-makeup-reference-results.zip'
try:
    subprocess.run([sys.executable, str(MAKEUP_REFERENCE_WORK / 'gpu-src/scripts/makeup_reference_bootstrap.py')],
                   cwd=MAKEUP_REFERENCE_WORK / 'gpu-src', check=True)
finally:
    with ZipFile(result_zip, 'x', ZIP_DEFLATED) as archive:
        for folder in ('results', 'setup-evidence', 'fixtures'):
            for path in sorted((MAKEUP_REFERENCE_WORK / folder).rglob('*')):
                if path.is_file():
                    archive.write(path, path.relative_to(MAKEUP_REFERENCE_WORK).as_posix())
        archive.write(MAKEUP_REFERENCE_WORK / 'candidate.json', 'candidate.json')
        archive.write(MAKEUP_REFERENCE_WORK / 'overlay/data/makeup/MAKEUP-GUIDED-001/plan.json', 'plan.json')
    print('DOWNLOAD_MAKEUP_REFERENCE_RESULTS:', result_zip, flush=True)
print('Finished. Review the two actual MAKEUP-001 outputs before any wider run or deployment.', flush=True)
'''
    intro = '''# Complete Makeup, bounded real model check

Use a **private copy** of the existing working pinned Kaggle notebook image, with its GPU accelerator and Internet enabled.
Import this notebook into that private copy. Keep the input containing `capstone_train002_20260928_v1.bin`.
Attach exactly one matching GPU bundle, no CPU bundle. No API secrets required. Do not run old training or service cells.

Run the two code cells once. This generates exactly **two** 512 square images with the existing MAKEUP-001 adapter at full influence,
20 steps, guidance4, seed1977: Soft Glam on054109 and Bold Evening on056266. Original model/environment/hash guards are preserved.
It does not train or publish anything. Setup and model loading are additional to inference time.

Image1 supplies identity/complexion. Image2 supplies complete cosmetic appearance from a different training identity.
These are external-editor synthetic guides, not MAKEUP-001 output and not approved training pairs.
The comparison's Previous panel is the explicitly rejected CPU compositor, not a matched model baseline.
Two reused development portraits cannot establish all13style quality. Hair, Nails and live Render settings are unchanged.

Download `beautycore-makeup-reference-results.zip` from the printed `DOWNLOAD_MAKEUP_REFERENCE_RESULTS` path, including on failure.
Keep this notebook and its research portraits/results private. Return the ZIP for visual and technical review.
'''
    book = {"cells": [
        {"cell_type": "markdown", "metadata": {}, "source": intro.splitlines(True)},
        *[{"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": code.splitlines(True)}
          for code in (prep, execute)]],
        "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}},
        "nbformat": 4, "nbformat_minor": 5}
    for cell in book["cells"]:
        if cell["cell_type"] == "code":
            compile("".join(cell["source"]), "private-notebook-cell", "exec")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(book, indent=1) + "\n")
    receipt = {"notebook": str(output.relative_to(ROOT)), "sha256": sha256(output.read_bytes()).hexdigest(),
        "bytes": output.stat().st_size, "expected_generation_calls": 2, "source_files": {k: v["sha256"] for k, v in files.items()},
        "fixture_count": len(assets), "training": False, "production_enabled": False}
    (output.parent / "package-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    build(WORK / "gpu-check/complete_makeup_gpu_check.ipynb")
