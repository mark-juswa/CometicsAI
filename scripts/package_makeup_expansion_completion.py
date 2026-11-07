"""Package the missing Manga Lash test with verified retained Makeup images."""
import argparse
import base64
from hashlib import sha256
import json
from pathlib import Path
from PIL import Image

from scripts.package_style_expansion_pilot import preparation_cell
from scripts.package_makeup_quality_diagnostic import source_payloads
from scripts.package_hair_expansion_validation import EXECUTION as HAIR_EXECUTION
from scripts.makeup_expansion_completion import cases

ROOT = Path(__file__).resolve().parents[1]
FILES = ("scripts/style_expansion_bootstrap.py", "scripts/makeup_quality_diagnostic.py",
         "scripts/makeup_expansion_bootstrap.py", "scripts/makeup_expansion_completion.py",
         "data/style-expansion/MAKEUP-EXP-002/plan.json")
EXECUTION = (HAIR_EXECUTION.replace("HAIR_WORK", "MAKEUP_EXPANSION_WORK")
             .replace("hair_expansion_bootstrap.py", "makeup_expansion_bootstrap.py")
             .replace("beautycore-hair-expansion-results.zip", "beautycore-makeup-expansion-results.zip")
             .replace("hair-attempted", "makeup-expansion-attempted")
             .replace("HAIR-EXP-002", "MAKEUP-EXP-002")
             .replace("DOWNLOAD_HAIR_RESULTS", "DOWNLOAD_MAKEUP_EXPANSION_RESULTS"))


def payloads():
    plan = json.loads((ROOT / FILES[-1]).read_text(encoding="utf-8"))
    if len(cases(plan)) != 3:
        raise ValueError("Expected exactly three new Makeup calls")
    assets = source_payloads(plan)
    folder = ROOT / "artifacts/style-expansion-20261025/release-review-01/results"
    raw = (folder / "report.json").read_bytes()
    if sha256(raw).hexdigest() != plan["reference_report_sha256"]:
        raise ValueError("Previously verified Makeup report differs")
    assets[plan["reference_report_filename"]] = {"data": base64.b64encode(raw).decode(), "sha256": sha256(raw).hexdigest()}
    for ref in plan["retained_outputs"]:
        path = folder / ref["original_output"]
        raw = path.read_bytes()
        if sha256(raw).hexdigest() != ref["png_sha256"]:
            raise ValueError("Retained Makeup image file differs")
        with Image.open(path) as im:
            if sha256(im.convert("RGB").tobytes()).hexdigest() != ref["rgb_sha256"]:
                raise ValueError("Retained Makeup image pixels differ")
        assets[ref["filename"]] = {"data": base64.b64encode(raw).decode(), "sha256": ref["png_sha256"]}
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
        raise ValueError("Do not overwrite a prepared Makeup notebook")
    files, assets = payloads()
    prep = preparation_cell(files, assets)
    for before, after in {
        "# Isolated STYLE-EXP-001. Keep this notebook private: it embeds an evaluation hand.":
          "# Private MAKEUP-EXP-002. Reused research portraits and saved outputs; do not publish.",
        "beautycore-styles-": "beautycore-makeup-expansion-",
        "STYLE_PILOT_WORKSPACE:": "MAKEUP_EXPANSION_WORKSPACE:",
        "Run the next cell once for 15 diffusion outputs plus 3 renderer looks.":
          "Run Cell 2 once: one saved-pixel control, then two new Manga Lash images.",
        "STYLE_WORK = prepare()": "MAKEUP_EXPANSION_WORK = prepare()",
    }.items():
        if before not in prep:
            raise ValueError("Preparation template anchor changed")
        prep = prep.replace(before, after)
    prep += """
driver = MAKEUP_EXPANSION_WORK / 'gpu-src/scripts/makeup_expansion_bootstrap.py'
with driver.open('xb') as file:
    file.write((MAKEUP_EXPANSION_WORK / 'overlay/scripts/makeup_expansion_bootstrap.py').read_bytes())
"""
    intro = """# BeautyCore private Makeup expansion completion — MAKEUP-EXP-002

This tests only the missing Manga Lash style. It is not a white-cast fix and does not deploy Makeup.
Use a separate private copy of the tested pinned Kaggle image, select T4 and enable Internet.
Attach exactly ONE input containing capstone_train002_20260928_v1.bin. No CPU bundle or API Secrets.

Three new images: one Soft Glam control that must match saved pixels, then two Manga Lash candidates.
Six previously verified Soft Glam/Berry/Icy Silver outputs are embedded and reused without regeneration.
Same existing MAKEUP-001 adapter at full1.0,20steps,seed1977,512square, experimental guidance2.5.
The original deployed contract remains4.0. No new model/training/photographs or parameter sweep.
Prior roughly64seconds per image suggests about3minutes15seconds inference, with setup/download additional.

Contains two reused research photos and their source author/license metadata, plus saved generated images.
Keep the notebook/results private. These are development sources, not untouched final evaluation.

Run Cell1 once, then Cell2 once. If the Soft Glam control differs, the test stops before Manga.
Download beautycore-makeup-expansion-results.zip after DOWNLOAD_MAKEUP_EXPANSION_RESULTS, including on failure.
Return the ZIP for review of lashes, skin tone/texture and facial geometry. Then stop this test session.
"""
    cells = []
    for i, (kind, text) in enumerate((("markdown", intro), ("code", prep), ("code", EXECUTION))):
        cell = {"cell_type": kind, "id": "makeup-expansion-" + str(i), "metadata": {},
                "source": text.splitlines(keepends=True)}
        if kind == "code":
            compile(text, cell["id"], "exec")
            cell.update(execution_count=None, outputs=[])
        cells.append(cell)
    book = {"nbformat": 4, "nbformat_minor": 5,
            "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}}, "cells": cells}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((json.dumps(book, indent=1) + "\n").encode())
    return {"date": "2026-10-31", "status": "PREPARED_GPU_NOT_RUN", "experiment": "MAKEUP-EXP-002",
            "notebook": str(path), "sha256": sha256(path.read_bytes()).hexdigest(), "bytes": path.stat().st_size,
            "new_inference_calls": 3, "retained_outputs": 6,
            "source_sha256": {k: v["sha256"] for k, v in files.items()},
            "fixture_sha256": {k: v["sha256"] for k, v in assets.items()},
            "white_cast_fix_claimed": False, "production_changed": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    result = build(parser.parse_args().output)
    (ROOT / "docs/experiments/makeup-expansion-completion-20261031.json").write_bytes(
        (json.dumps(result, indent=2) + "\n").encode())
    print(json.dumps({k: v for k, v in result.items() if k not in ("source_sha256", "fixture_sha256")}, indent=2))
