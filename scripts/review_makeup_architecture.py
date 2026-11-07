"""Offline architecture receipt and retained component comparison, no new model calls."""
import argparse
import base64
from hashlib import sha256
import html
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.makeup_source_layers import catalog, render_layers, pixel_hash, VERSION
from scripts.makeup_surface_application import lip_coverage, palette
from scripts.makeup_target_quality import policy, validate_dataset_quality


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def owned(path):
    result = (ROOT / path).resolve()
    if not result.is_relative_to(ROOT):
        raise ValueError("Evidence path escapes project")
    return result


def run(output):
    output = owned(output)
    if output.exists():
        raise ValueError("Preserve prior evidence, choose a new output directory")
    plan = json.loads(owned("data/makeup/MAKEUP-SURFACE-001/plan.json").read_text())
    retained = owned("artifacts/makeup-surface-20261102/lip-final/report.json")
    report = json.loads(retained.read_text())
    expected = {row["id"]: row for row in report["cases"]}
    sources = {row["id"]: row for row in plan["sources"]}
    # Verify all frozen evidence BEFORE allocating the output folder.
    inputs = {}
    for row in plan["sources"]:
        for field in ("source", "source_labels"):
            inputs[row[field]] = row[field + "_sha256"]
    for row in plan["cases"]:
        for field in ("raw", "raw_labels"):
            inputs[row[field]] = row[field + "_sha256"]
        name = row["source_landmarks"]
        inputs["artifacts/makeup-cosmetic-layers-20261101/" + name] = plan["landmark_sha256"][name]
        inputs["artifacts/makeup-surface-20261102/lip-final/" + expected[row["id"]]["output"]] = expected[row["id"]]["png_sha256"]
    previous_audit = json.loads(owned("artifacts/makeup-realism-audit-20261102/audit.json").read_text())
    previous_hashes = {key.replace("\\", "/"): value for key, value in previous_audit["unchanged_sha256"].items()}
    for row in plan["cases"]:
        previous = "artifacts/makeup-reference-20261101/run-05/" + row["id"] + "-corrected.png"
        inputs[previous] = previous_hashes[previous]
    for name, checksum in inputs.items():
        if digest(owned(name)) != checksum:
            raise ValueError("Frozen input or prior output changed: " + name)
    output.mkdir(parents=True)
    result = {"date": "2026-11-04", "implementation": VERSION,
              "source_fitted_artist_assets_available": False,
              "new_model_calls": 0, "new_training_calls": 0, "production_changed": False,
              "appearance": "EXPERIMENTAL_COMPONENT_ONLY", "full_makeup_solved": False,
              "inputs_sha256": inputs, "cases": [], "catalog": []}
    sections = []
    for case in plan["cases"]:
        sid, case_id = case["subject_id"], case["id"]
        source = sources[sid]
        original = np.array(Image.open(owned(source["source"])).convert("RGB"))
        reference = np.array(Image.open(owned(case["raw"])).convert("RGB"))
        labels = np.array(Image.open(owned(source["source_labels"])))
        ref_labels = np.array(Image.open(owned(case["raw_labels"])))
        points = json.loads(owned("artifacts/makeup-cosmetic-layers-20261101/" + case["source_landmarks"]).read_text())["points"]
        alpha, _, agreement = lip_coverage(labels, points)
        doc = {"schema": "makeup-source-layers-v1", "production_enabled": False,
               "source_rgb_sha256": pixel_hash(original), "labels_sha256": pixel_hash(labels),
               "style_id": case["style_id"], "scope": "component",
               "artist_review": {"decision": "PENDING"},
               "material_provenance": "Existing generated guide palette, for exact regression only. NOT artist/salon authored.",
               "coverage_provenance": "Retained parser/landmark development estimate. NOT artist reviewed.",
               "layers": [{"id": "lip-pigment", "kind": "lip", "alpha_path": case_id + "-alpha.npy", "alpha_sha256": pixel_hash(alpha),
                           "palette_lab": palette(reference, ref_labels).tolist()}]}
        corrected, metrics = render_layers(original, labels, doc, {"lip-pigment": alpha}, development_only=True)
        if pixel_hash(corrected) != expected[case_id]["rgb_sha256"]:
            raise ValueError("Retained lip component changed")
        previous = np.array(Image.open(owned("artifacts/makeup-reference-20261101/run-05/" + case_id + "-corrected.png")))
        titles = ["Original", "Existing AI guide (defective face)", "Previous transfer (REJECTED)", "Retained lip ONLY (not full look)"]
        images = [original, reference, previous, corrected]
        sheet = Image.new("RGB", (2048, 544), "white")
        draw = ImageDraw.Draw(sheet)
        figures = []
        for index, (title, array) in enumerate(zip(titles, images)):
            draw.text((index * 512 + 5, 8), title, fill="black")
            sheet.paste(Image.fromarray(array), (index * 512, 32))
            path = output / (case_id + "-" + str(index) + ".png")
            Image.fromarray(array).save(path)
            data = base64.b64encode(path.read_bytes()).decode()
            figures.append('<figure><figcaption>' + html.escape(title) + '</figcaption><a href="data:image/png;base64,' + data + '" download="' + path.name + '"><img width="512" height="512" alt="' + html.escape(title) + '" src="data:image/png;base64,' + data + '"></a></figure>')
        sheet.save(output / (case_id + "-comparison.png"))
        (output / (case_id + "-layers.json")).write_text(json.dumps(doc, indent=2) + "\n")
        np.save(output / (case_id + "-alpha.npy"), alpha, allow_pickle=False)
        result["cases"].append({"id": case_id, "subject_id": sid, "style_id": case["style_id"],
                                "rgb_sha256": pixel_hash(corrected), "retained_rgb_exact": True,
                                "lip_contour_agreement": agreement, "source_photo": source["source_photo"],
                                "source_dataset_license": source["source_dataset_license"], **metrics})
        credit = source["source_photo"]
        sections.append('<section><h2>' + html.escape(case_id) + '</h2><div class="grid">' + ''.join(figures) + '</div><p>Source: ' + html.escape(credit["author"]) + ', ' + html.escape(credit["license"]) + '. Development person already reused. Lip only is incomplete for this style.</p></section>')
    for style in catalog():
        result["catalog"].append({**style, "source_fitted_artist_assets": "NOT STARTED",
                                  "full_look_quality": "NEEDS VERIFICATION",
                                  "retained_lip_component_cases": sum(row["style_id"] == style["id"] for row in result["cases"])})
    rules = policy()
    dataset = owned(".tmp/data_m001/paired_selection/final_v1")
    try:
        validate_dataset_quality(dataset)
    except ValueError as error:
        result["historical_corrective_training_admission"] = {"allowed": False, "reason": str(error)}
    else:
        raise RuntimeError("Historical uncorrected dataset unexpectedly admitted")
    result["rejected_target_count"] = len(rules["rejected_target_sha256"])
    result["new_usable_corrective_pairs"] = 0
    result["implementation_sha256"] = {name: digest(owned(name)) for name in [
        "scripts/makeup_source_layers.py", "scripts/makeup_target_quality.py",
        "scripts/review_makeup_architecture.py", "scripts/data_m001_paired.py",
        "scripts/data_m001_package_training.py", "notebooks/train_m001_kaggle.py"]}
    (output / "review.json").write_text(json.dumps(result, indent=2) + "\n")
    inventory = ''.join('<li>' + html.escape(row["name"]) + ' (' + ('serving' if row["serving"] else 'held') + '), full look quality NEEDS VERIFICATION</li>' for row in result["catalog"])
    page = '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Makeup architecture review</title><style>body{font:16px system-ui;margin:24px;background:#f5f4f2;color:#202020}section{margin:40px 0}.grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}figure{margin:0}img{width:100%;height:auto}figcaption{min-height:3em;font-weight:600}a{color:inherit}p{max-width:1000px}@media(max-width:700px){body{margin:12px}.grid{grid-template-columns:repeat(2,minmax(0,1fr))}}</style><h1>Makeup architecture and component review</h1><p>Full Makeup remains unresolved. These six outputs exactly reproduce the previously preferred lip component through the reusable source material operator. They are not new full looks, artist assets, untouched acceptance subjects or approved training targets. Existing generated guides contain pale reconstructed faces. Click an image to download native 512 pixel evidence.</p>' + ''.join(sections) + '<h2>Complete catalog</h2><ul>' + inventory + '</ul><p>60 historical targets refused for corrective reuse. Zero new usable corrective training pairs. No new model calls or production changes.</p></html>'
    (output / "review-self-contained.html").write_text(page, encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="artifacts/makeup-architecture-20261104/review")
    args = parser.parse_args()
    result = run(args.output)
    print(json.dumps({"cases": len(result["cases"]), "catalog": len(result["catalog"]),
                      "full_makeup_solved": False, "new_usable_corrective_pairs": 0}))
