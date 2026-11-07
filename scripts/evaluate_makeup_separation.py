"""Frozen offline six-case diagnostic, not a live serving entry point."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import shutil
import sys

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.makeup_cosmetic_separation import transfer, CONFIG


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def owned(path):
    resolved = (ROOT / path).resolve()
    if not resolved.is_relative_to(ROOT):
        raise ValueError("Path escapes project")
    return resolved


def run(output):
    prior = json.loads(owned("data/makeup/MAKEUP-LAYERS-001/plan-v3.json").read_text(encoding="utf-8"))
    landmarks = owned("artifacts/makeup-cosmetic-layers-20261101")
    if output.exists():
        raise ValueError("Keep existing evidence; select a new empty output path")
    if len(prior["cases"]) != 6:
        raise ValueError("Six fixed reference comparisons required")
    dependencies = [
        "scripts/makeup_cosmetic_separation.py",
        "scripts/makeup_selected_cosmetics.py",
        "scripts/makeup_source_faithful_retouch.py",
        "scripts/makeup_source_render.py",
        "scripts/makeup_alignment_pilot.py",
        "scripts/evaluate_makeup_separation.py",
    ]
    plan = {
        "experiment": "MAKEUP-SEPARATION-001",
        "configuration": CONFIG,
        "production_enabled": False,
        "automatic_promotion": False,
        "new_diffusion_calls": 0,
        "sources": prior["sources"],
        "cases": prior["cases"],
        "source_sha256": {p: digest(owned(p)) for p in dependencies},
        "landmark_sha256": {},
        "previous_failure": "artifacts/makeup-cosmetic-layers-20261101/run-03",
    }
    for row in plan["cases"]:
        for field in ("source_landmarks", "reference_landmarks"):
            name = row[field]
            plan["landmark_sha256"][name] = digest(landmarks / name)
    sources = {row["id"]: row for row in plan["sources"]}
    output.mkdir(parents=True, exist_ok=False)
    (output / "plan.json").write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    for path in dependencies:
        shutil.copyfile(owned(path), output / Path(path).name)
    report = {
        "experiment": plan["experiment"], "status": "IN_PROGRESS",
        "production_enabled": False, "new_diffusion_calls": 0, "cases": [],
    }
    try:
        for row in plan["cases"]:
            source = sources[row["subject_id"]]
            for key, hash_key in (("source", "source_sha256"), ("source_labels", "source_labels_sha256")):
                if digest(owned(source[key])) != source[hash_key]:
                    raise ValueError("Original input hash differs")
            for key, hash_key in (("raw", "raw_sha256"), ("raw_labels", "raw_labels_sha256")):
                if digest(owned(row[key])) != row[hash_key]:
                    raise ValueError("Selected reference hash differs")
            original = np.asarray(Image.open(owned(source["source"])).convert("RGB")).copy()
            reference = np.asarray(Image.open(owned(row["raw"])).convert("RGB")).copy()
            labels = np.asarray(Image.open(owned(source["source_labels"]))).copy()
            ref_labels = np.asarray(Image.open(owned(row["raw_labels"]))).copy()
            sp = json.loads((landmarks / row["source_landmarks"]).read_text(encoding="utf-8"))
            rp = json.loads((landmarks / row["reference_landmarks"]).read_text(encoding="utf-8"))
            if sp["source_sha256"] != source["source_sha256"] or rp["source_sha256"] != row["raw_sha256"]:
                raise ValueError("Landmark provenance differs")
            result, masks, metrics = transfer(
                original, reference, labels, ref_labels, sp["points"], rp["points"]
            )
            for name, image in (("original", original), ("selected-makeup", reference), ("corrected", result)):
                Image.fromarray(image).save(output / (row["id"] + "-" + name + ".png"))
            for name, matte in masks.items():
                Image.fromarray(np.rint(matte * 255).astype(np.uint8)).save(
                    output / (row["id"] + "-" + name + "-mask.png")
                )
            sheet = Image.new("RGB", (1536, 542), "white")
            draw = ImageDraw.Draw(sheet)
            for i, (title, image) in enumerate([
                ("Original person", original),
                ("Selected existing makeup", reference),
                ("Cosmetic separation test, NOT DEPLOYED", result),
            ]):
                draw.text((i * 512 + 6, 8), title, fill="black")
                sheet.paste(Image.fromarray(image), (i * 512, 30))
            sheet.save(output / (row["id"] + "-comparison.png"))
            path = row["id"] + "-corrected.png"
            report["cases"].append({
                **row, **metrics, "output": path,
                "png_sha256": digest(output / path),
                "rgb_sha256": sha256(result.tobytes()).hexdigest(),
                "visual_verdict": "NEEDS_REVIEW",
            })
            print("SEPARATION_DONE", row["id"], json.dumps(metrics), flush=True)
        report["status"] = "COMPLETE_REQUIRES_VISUAL_REVIEW"
    finally:
        (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="artifacts/makeup-separation-20261101/run-01")
    arguments = parser.parse_args()
    run(owned(arguments.output))
