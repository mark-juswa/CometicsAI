"""Reproduce the bounded lip correction. Never starts a service or a model."""
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
from scripts.makeup_surface_application import apply_lipstick, CONFIG


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def owned(relative):
    path = (ROOT / relative).resolve()
    if not path.is_relative_to(ROOT):
        raise ValueError("Path escapes project")
    return path


def run(output):
    output = owned(output)
    if output.exists():
        raise ValueError("Preserve prior evidence. Use an empty output directory.")
    previous = json.loads(owned("data/makeup/MAKEUP-REFERENCE-001/plan.json").read_text(encoding="utf-8"))
    points_folder = owned("artifacts/makeup-cosmetic-layers-20261101")
    dependencies = [
        "scripts/makeup_surface_application.py", "scripts/evaluate_makeup_surface_application.py",
        "scripts/makeup_alignment_pilot.py", "scripts/makeup_selected_cosmetics.py",
        "scripts/makeup_source_faithful_retouch.py", "scripts/makeup_source_render.py",
    ]
    plan = {
        "experiment": "MAKEUP-SURFACE-001",
        "configuration": CONFIG,
        "scope": "Lip boundary and source surface correction only. Full Makeup remains unresolved.",
        "production_enabled": False, "automatic_promotion": False,
        "sources": previous["sources"], "cases": previous["cases"],
        "landmark_sha256": previous["landmark_sha256"],
        "source_sha256": {path: digest(owned(path)) for path in dependencies},
    }
    if len(plan["cases"]) != 6:
        raise ValueError("Expected the fixed six case matrix")
    sources = {row["id"]: row for row in plan["sources"]}
    output.mkdir(parents=True)
    (output / "plan.json").write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    for name in dependencies:
        shutil.copyfile(owned(name), output / Path(name).name)
    report = {"experiment": plan["experiment"], "production_enabled": False,
              "status": "IN_PROGRESS", "full_makeup_appearance": "NOT_SOLVED",
              "cases": []}
    try:
        for case in plan["cases"]:
            source = sources[case["subject_id"]]
            for row, pairs in [
                (source, [("source", "source_sha256"), ("source_labels", "source_labels_sha256")]),
                (case, [("raw", "raw_sha256"), ("raw_labels", "raw_labels_sha256")]),
            ]:
                for path_key, hash_key in pairs:
                    if digest(owned(row[path_key])) != row[hash_key]:
                        raise ValueError("Frozen image or label map changed")
            point_path = points_folder / case["source_landmarks"]
            if digest(point_path) != plan["landmark_sha256"][case["source_landmarks"]]:
                raise ValueError("Frozen original landmarks changed")
            record = json.loads(point_path.read_text(encoding="utf-8"))
            if record["source_sha256"] != source["source_sha256"]:
                raise ValueError("Source landmark provenance mismatch")
            original = np.array(Image.open(owned(source["source"])).convert("RGB"))
            reference = np.array(Image.open(owned(case["raw"])).convert("RGB"))
            labels = np.array(Image.open(owned(source["source_labels"])))
            reference_labels = np.array(Image.open(owned(case["raw_labels"])))
            corrected, alpha, metrics = apply_lipstick(
                original, reference, labels, reference_labels, record["points"]
            )
            for name, array in (("original", original), ("reference", reference),
                                ("corrected", corrected)):
                Image.fromarray(array).save(output / (case["id"] + "-" + name + ".png"))
            Image.fromarray(np.rint(alpha * 255).astype(np.uint8)).save(
                output / (case["id"] + "-lip-mask.png")
            )
            sheet = Image.new("RGB", (1536, 542), "white")
            draw = ImageDraw.Draw(sheet)
            for index, (title, array) in enumerate([
                ("Original photograph", original),
                ("Previous AI output, color guide only", reference),
                ("Lip correction ONLY, full Makeup unresolved", corrected),
            ]):
                draw.text((index * 512 + 5, 8), title, fill="black")
                sheet.paste(Image.fromarray(array), (index * 512, 30))
            sheet.save(output / (case["id"] + "-comparison.png"))
            name = case["id"] + "-corrected.png"
            report["cases"].append({
                **case, **metrics, "output": name,
                "png_sha256": digest(output / name),
                "rgb_sha256": sha256(corrected.tobytes()).hexdigest(),
                "visual_verdict": "LIMITED_LIP_PROOF_NOT_FULL_MAKEUP_ACCEPTANCE",
            })
            print("LIP_CORRECTION", case["id"], flush=True)
        report["status"] = "COMPLETE_LIMITED_COMPONENT_PROOF"
    finally:
        (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return plan, report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="artifacts/makeup-surface-20261102/lip-final")
    args = parser.parse_args()
    run(args.output)
