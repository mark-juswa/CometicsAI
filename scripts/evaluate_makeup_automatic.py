"""Artist independent CPU Makeup correction and frozen catalog comparisons.

No training, deployment, GPU calls, target acceptance or package installation.
"""
import argparse
import ast
import base64
from hashlib import sha256
import html
import json
from pathlib import Path
import shutil
import sys
import time

import cv2
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.makeup_source_layers import catalog, automatic_support, apply_counterfactual, pixel_hash
from scripts.makeup_local_features import LocalCosmeticFeatures, REVISION, CHECKPOINT_SHA256

PROVIDER = ROOT / "artifacts/makeup-local-transfer-20261104"
STRUCTURE = ROOT / "artifacts/makeup-render-20261030/stable-makeup-pilot"
ALGORITHM_FILES = ["scripts/makeup_source_layers.py", "scripts/makeup_local_features.py",
                   "scripts/makeup_materials.py",
                   "scripts/evaluate_makeup_automatic.py", "scripts/makeup_surface_application.py",
                   "scripts/makeup_alignment_pilot.py", "scripts/makeup_selected_cosmetics.py",
                   "scripts/makeup_source_faithful_retouch.py", "scripts/makeup_source_render.py"]


def owned(value):
    path = (ROOT / value).resolve()
    if not path.is_relative_to(ROOT):
        raise ValueError("Path escapes project")
    return path


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def rgb(path):
    return np.asarray(Image.open(path).convert("RGB")).copy()


def freeze(output):
    output = owned(output)
    if output.exists():
        raise ValueError("Preserve prior evidence. New directory required")
    alignment = read(ROOT / "data/makeup/MAKEUP-ALIGN-001/plan.json")
    controls = read(STRUCTURE / "controls-receipt.json")
    sources = []
    for row in controls["subjects"]:
        sid = row["id"]
        labels = next(value for value in alignment["maps"] if value["id"] == sid)
        landmarks = ROOT / "artifacts/makeup-render-20261030/alignment-01" / (sid + "-landmarks.json")
        if digest(owned(row["source"])) != row["sha256"] or digest(owned(labels["labels"])) != labels["sha256"]:
            raise ValueError("Original portrait or cached parser map changed")
        sources.append({"id": sid, "source": row["source"], "sha256": row["sha256"],
                        "labels": labels["labels"], "labels_sha256": labels["sha256"],
                        "points478": landmarks.relative_to(ROOT).as_posix(), "points478_sha256": digest(landmarks),
                        "points68": row["landmarks"][0], "source_photo": row["source_photo"],
                        "source_dataset_license": row["source_dataset_license"],
                        "usage": "Reused development portrait, not untouched acceptance"})
    guides = []
    old = ROOT / "artifacts/style-expansion-20261025/release-review-01/results"
    for style in catalog():
        paths = sorted(old.glob("[0-9][0-9]-054109-" + style["id"] + ".png"))
        if style["id"] == "exp_manga_lash":
            paths = [ROOT / "artifacts/makeup-expansion-20261031/review-01/results/02-054109-exp_manga_lash.png"]
        if not paths or not paths[0].is_file():
            raise ValueError("Missing existing guide for " + style["id"])
        path = paths[0]
        guides.append({**style, "reference": path.relative_to(ROOT).as_posix(), "sha256": digest(path),
                       "role": "Existing AI generated style guide, not ground truth or a training target"})
    plan = {"schema": "makeup-automatic-correction-v1", "date": "2026-11-04",
            "production_enabled": False, "training": False, "artist_required": False,
            "sources": sources, "guides": guides, "case_count": len(sources) * len(guides),
            "provider": {"source_revision": REVISION, "checkpoint_sha256": CHECKPOINT_SHA256,
                         "license_record": "Author repository CC BY-NC-SA4.0; no deployment rights conclusion"},
            "parser": read(ROOT / "data/makeup/MAKEUP-RENDER-001/plan.json")["parser"],
            "controls_receipt_sha256": digest(STRUCTURE / "controls-receipt.json"),
            "algorithm_sha256": {name: digest(owned(name)) for name in ALGORITHM_FILES}}
    output.mkdir(parents=True)
    save(output / "plan.json", plan)
    for name in ALGORITHM_FILES:
        shutil.copyfile(owned(name), output / Path(name).name)
    return plan


def prepare(output):
    output = owned(output)
    plan = freeze(output)
    # All preprocessing uses already present CPU assets in the existing env.
    import torch
    from transformers import SegformerForSemanticSegmentation, SegformerImageProcessor
    torch.set_num_threads(4)
    parser_dir = owned(plan["parser"]["directory"])
    for name, checksum in plan["parser"]["files"].items():
        if digest(parser_dir / name) != checksum:
            raise ValueError("Cached parser changed")
    processor = SegformerImageProcessor.from_pretrained(str(parser_dir), local_files_only=True)
    parser = SegformerForSemanticSegmentation.from_pretrained(str(parser_dir), local_files_only=True, use_safetensors=True).eval()
    sys.path[:0] = [str(STRUCTURE / "runtime" / name) for name in ("spiga", "facelib")]
    from facelib import FaceDetector
    from spiga.inference.config import ModelConfig
    from spiga.inference.framework import SPIGAFramework
    config = ModelConfig("300wpublic", load_model_url=False)
    config.model_weights_path = str(STRUCTURE / "assets")
    spiga = SPIGAFramework(config)
    detector = FaceDetector(device=torch.device("cpu"), verbose=False)
    tree = ast.parse((STRUCTURE / "vendor/stable/spiga_draw.py").read_text(encoding="utf-8"))
    functions = [value for value in tree.body if isinstance(value, ast.FunctionDef)
                 and value.name in {"parse_landmarks", "bbox_from_landmarks"}]
    if len(functions) != 2:
        raise ValueError("Cached original SPIGA helper changed")
    scope = {"np": np}
    exec(compile(ast.Module(body=functions, type_ignores=[]), "cached-spiga-helpers", "exec"), scope)
    records = []
    try:
        for guide in plan["guides"]:
            image = rgb(owned(guide["reference"]))
            if digest(owned(guide["reference"])) != guide["sha256"]:
                raise ValueError("Guide changed")
            with torch.inference_mode():
                logits = parser(**processor(images=Image.fromarray(image), return_tensors="pt")).logits
                labels = torch.nn.functional.interpolate(logits, size=(512, 512), mode="bilinear", align_corners=False).argmax(1)[0].byte().numpy()
                bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
                boxes, _, _ = detector.detect_faces(bgr)
                if len(boxes) != 1:
                    raise ValueError("Guide needs exactly one detected face")
                box = boxes[0].tolist()
                first = spiga.inference(bgr, [[box[0], box[1], box[2] - box[0], box[3] - box[1]]])
                landmarks = np.asarray(spiga.inference(bgr, scope["bbox_from_landmarks"](np.asarray(first["landmarks"])))['landmarks'], np.float32)[0]
            name = guide["id"]
            Image.fromarray(labels).save(output / (name + "-labels.png"))
            np.save(output / (name + "-68.npy"), landmarks, allow_pickle=False)
            records.append({"style_id": name, "labels": name + "-labels.png", "labels_sha256": digest(output / (name + "-labels.png")),
                            "points68": name + "-68.npy", "points68_sha256": digest(output / (name + "-68.npy"))})
            print("PREPARED", len(records), "/", len(plan["guides"]), name, flush=True)
    finally:
        save(output / "prepared.json", {"plan_sha256": digest(output / "plan.json"), "guides": records,
                                         "complete": len(records) == len(plan["guides"])})


def previous_path(subject, style):
    latest = ROOT / "artifacts/makeup-reference-20261101/run-05"
    name = subject + "-" + style
    if style in {"natural_makeup", "classic_red_lip"}:
        name = "g4-" + name
    path = latest / (name + "-corrected.png")
    if path.is_file():
        return path, "Previous rejected transfer"
    base = ROOT / "artifacts/style-expansion-20261025/release-review-01/results"
    paths = sorted(base.glob("[0-9][0-9]-" + subject + "-" + style + ".png"))
    if paths:
        return paths[0], "Previous generated result"
    if style == "exp_manga_lash" and subject in {"054109", "056266"}:
        path = ROOT / "artifacts/makeup-expansion-20261031/review-01/results" / (("02-" if subject == "054109" else "03-") + subject + "-exp_manga_lash.png")
        return path, "Previous generated result"
    return None, "No matched previous result available"


def generate(output):
    output = owned(output)
    plan, prepared = read(output / "plan.json"), read(output / "prepared.json")
    if (output / "report.json").exists() or (output / "results").exists():
        raise ValueError("Preserve prior generation evidence")
    if not prepared["complete"] or prepared["plan_sha256"] != digest(output / "plan.json"):
        raise ValueError("Incomplete or changed preparation")
    for path, checksum in plan["algorithm_sha256"].items():
        if digest(owned(path)) != checksum:
            raise ValueError("Frozen algorithm changed: " + path)
    records = {row["style_id"]: row for row in prepared["guides"]}
    result_dir = output / "results"
    result_dir.mkdir()
    provider = LocalCosmeticFeatures(PROVIDER)
    report = {"schema": plan["schema"], "production_enabled": False, "artist_required": False,
              "new_diffusion_calls": 0, "training": False, "device": "cpu", "cases": [], "controls": []}
    try:
        for source in plan["sources"]:
            sid = source["id"]
            for path, checksum in ((source["source"], source["sha256"]), (source["labels"], source["labels_sha256"]),
                                   (source["points478"], source["points478_sha256"])):
                if digest(owned(path)) != checksum:
                    raise ValueError("Frozen source changed")
            original = rgb(owned(source["source"]))
            labels = np.array(Image.open(owned(source["labels"])))
            points = read(owned(source["points478"]))["points"]
            coarse = np.asarray(source["points68"], np.float32)
            fields = automatic_support(labels, points, coarse)
            coverage = np.maximum(fields["eye"], fields["cheek"])
            # Actual identical-reference neural control, not just a zero mask.
            baseline, identical, meta = provider.counterfactual(original, labels, coarse, original, labels, coarse, coverage)
            control, _, _ = apply_counterfactual(original, original, labels, labels, points, baseline, identical, fields, "natural_makeup")
            if not np.array_equal(control, original):
                raise ValueError("Identical reference changed source pixels")
            report["controls"].append({"subject_id": sid, "identical_reference_source_exact": True,
                                        "decoder_max_difference": float(np.max(np.abs(baseline - identical)))})
            for guide in plan["guides"]:
                name = guide["id"]
                record = records[name]
                for path, checksum in ((record["labels"], record["labels_sha256"]), (record["points68"], record["points68_sha256"])):
                    if digest(output / path) != checksum:
                        raise ValueError("Prepared guide map changed")
                if digest(owned(guide["reference"])) != guide["sha256"]:
                    raise ValueError("Frozen guide changed")
                reference = rgb(owned(guide["reference"]))
                ref_labels = np.array(Image.open(output / record["labels"]))
                ref_points = np.load(output / record["points68"], allow_pickle=False)
                started = time.perf_counter()
                baseline, edited, provider_meta = provider.counterfactual(original, labels, coarse, reference, ref_labels, ref_points, coverage)
                corrected, masks, metrics = apply_counterfactual(original, reference, labels, ref_labels, points, baseline, edited, fields, name)
                case_id = sid + "-" + name
                np.savez_compressed(result_dir / (case_id + "-fields.npz"), baseline=baseline, edited=edited, **masks)
                Image.fromarray(corrected).save(result_dir / (case_id + ".png"))
                previous, previous_title = previous_path(sid, name)
                images = [original, reference, rgb(previous) if previous else np.full_like(original, 238), corrected]
                titles = ["Original", "Existing style guide (AI output)", previous_title, "Automatic source anchored correction"]
                sheet = Image.new("RGB", (2048, 544), "white")
                draw = ImageDraw.Draw(sheet)
                for index, (title, array) in enumerate(zip(titles, images)):
                    draw.text((index * 512 + 5, 8), title, fill="black")
                    sheet.paste(Image.fromarray(array), (index * 512, 32))
                sheet.save(result_dir / (case_id + "-comparison.png"))
                report["cases"].append({"id": case_id, "subject_id": sid, "style_id": name,
                                        "output": "results/" + case_id + ".png", "rgb_sha256": pixel_hash(corrected),
                                        "png_sha256": digest(result_dir / (case_id + ".png")),
                                        "previous": previous.relative_to(ROOT).as_posix() if previous else None,
                                        "previous_title": previous_title, "source_photo": source["source_photo"],
                                        "source_dataset_license": source["source_dataset_license"],
                                        "provider": provider_meta, **metrics, "seconds": time.perf_counter() - started,
                                        "visual_review": "PENDING", "eligible_for_training": False})
                print("CORRECTED", len(report["cases"]), "/", plan["case_count"], case_id, flush=True)
        # A second forward after the entire catalog must reproduce the first.
        source, guide = plan["sources"][0], plan["guides"][0]
        original, reference = rgb(owned(source["source"])), rgb(owned(guide["reference"]))
        labels = np.array(Image.open(owned(source["labels"])))
        points = read(owned(source["points478"]))["points"]
        coarse = np.asarray(source["points68"], np.float32)
        fields = automatic_support(labels, points, coarse)
        record = records[guide["id"]]
        ref_labels = np.array(Image.open(output / record["labels"]))
        ref_points = np.load(output / record["points68"], allow_pickle=False)
        a, b, _ = provider.counterfactual(original, labels, coarse, reference, ref_labels, ref_points, np.maximum(fields["eye"], fields["cheek"]))
        repeated, _, _ = apply_counterfactual(original, reference, labels, ref_labels, points, a, b, fields, guide["id"])
        report["catalog_cache_independent"] = pixel_hash(repeated) == report["cases"][0]["rgb_sha256"]
        if not report["catalog_cache_independent"]:
            raise ValueError("Style order mutated source feature cache")
        report["status"] = "DONE_GENERATION_VISUAL_REVIEW_REQUIRED"
    finally:
        save(output / "report.json", report)
    gallery(output)


def gallery(output):
    output = owned(output)
    plan, report = read(output / "plan.json"), read(output / "report.json")
    sources = {row["id"]: row for row in plan["sources"]}
    guides = {row["id"]: row for row in plan["guides"]}
    material_review = report.get("schema") == "automatic-material-review-v1"
    cards = []
    for case in report["cases"]:
        source, guide = sources[case["subject_id"]], guides[case["style_id"]]
        paths = [owned(source["source"]), owned(guide["reference"]), owned(case["previous"]) if case["previous"] else None, output / case["output"]]
        titles = ["Original", "Makeup guide (existing AI output)", case["previous_title"],
                  "Source material correction, EXPERIMENTAL" if material_review else "Automatic correction, EXPERIMENTAL"]
        figures = []
        for title, path in zip(titles, paths):
            if path:
                mime = "image/jpeg" if path.suffix.lower() in {".jpg", ".jpeg"} else "image/png"
                data = "data:" + mime + ";base64," + base64.b64encode(path.read_bytes()).decode()
                figures.append('<figure><figcaption>' + html.escape(title) + '</figcaption><button type="button" aria-label="Enlarge ' + html.escape(title) + '" onclick="openImage(this)"><img width="512" height="512" alt="' + html.escape(title) + '" src="' + data + '"></button></figure>')
            else:
                figures.append('<figure><figcaption>No matched previous result available</figcaption><p>Not generated or substituted.</p></figure>')
        cards.append('<section data-person="' + case["subject_id"] + '" data-style="' + case["style_id"] + '"><h2>' + html.escape(guide["name"] + ' / ' + case["subject_id"]) + '</h2><div class="grid">' + ''.join(figures) + '</div><p>Source: ' + html.escape(source["source_photo"]["author"]) + ', ' + html.escape(source["source_photo"]["license"]) + '. Reused development portrait. ' + html.escape(case["visual_review"]) + '</p></section>')
    select = '<label>Person <select id="person" onchange="filterCases()"><option value="all">All four</option>' + ''.join('<option>' + sid + '</option>' for sid in sources) + '</select></label> <label>Style <select id="style" onchange="filterCases()"><option value="all">All thirteen</option>' + ''.join('<option value="' + row["id"] + '">' + html.escape(row["name"]) + '</option>' for row in plan["guides"]) + '</select></label>'
    page = '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Automatic Makeup correction</title><style>body{font:16px system-ui;background:#f5f3f0;margin:24px;color:#252525}.grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px}figure{margin:0}figcaption{min-height:3em}button{padding:0;border:0;background:none;cursor:zoom-in}img{max-width:100%;height:auto}section{margin:36px 0}dialog{max-width:95vw;max-height:95vh}dialog img{width:512px}select{font:inherit;max-width:90vw}[hidden]{display:none!important}@media(max-width:700px){body{margin:12px}.grid{grid-template-columns:repeat(2,minmax(0,1fr))}}</style><h1>Automatic source anchored Makeup</h1><p>Four existing development portraits, all thirteen catalog styles. No artist required, no new diffusion, no model training or production change. Guides are imperfect prior AI outputs. These candidates require visual review; technical preservation alone is insufficient. Missing baselines are labeled.</p>' + select + ''.join(cards) + '<dialog id="viewer"><button type="button" onclick="document.getElementById(\'viewer\').close()">Close native image</button><p id="caption"></p><img id="native" alt="Enlarged comparison"></dialog><script>let prior;function openImage(b){prior=b;document.getElementById("native").src=b.querySelector("img").src;document.getElementById("caption").textContent=b.closest("figure").querySelector("figcaption").textContent;document.getElementById("viewer").showModal()}document.getElementById("viewer").addEventListener("close",()=>{if(prior)prior.focus()});function filterCases(){let p=document.getElementById("person").value,s=document.getElementById("style").value;document.querySelectorAll("section").forEach(e=>e.hidden=(p!=="all"&&p!==e.dataset.person)||(s!=="all"&&s!==e.dataset.style))}</script></html>'
    if material_review:
        styles = len({case["style_id"] for case in report["cases"]})
        note = (str(len(report["cases"])) + " comparisons, " + str(styles) + " catalog styles on four reused development portraits. "
                "Previous panels are actual November 4 automatic results. Existing user photo supplies observed lash/reflective detail only; "
                "its author/license is unknown and no training use is approved. Original source canvas, local lip confidence and style materials. "
                "Eye opening cores are protected; one pixel lid rim may be occluded by mascara. No source smoothing, new diffusion, training or production change. "
                "Appearance remains EXPERIMENTAL; source preservation alone is insufficient.")
        start = page.index("<p>Four existing development portraits")
        end = page.index("</p>", start) + 4
        page = page[:start] + "<p>" + html.escape(note) + "</p>" + page[end:]
    (output / "review-self-contained.html").write_text(page, encoding="utf-8")


def reapply(previous, output):
    """Review a material correction against frozen fields, without another model call."""
    previous, output = owned(previous), owned(output)
    if output.exists():
        raise ValueError("Preserve earlier material results")
    prior_plan, prior_report = read(previous / "plan.json"), read(previous / "report.json")
    if len(prior_report["cases"]) != prior_plan["case_count"]:
        raise ValueError("Complete frozen field matrix required")
    frozen_fields = {row["id"]: digest(previous / "results" / (row["id"] + "-fields.npz"))
                     for row in prior_report["cases"]}
    for row in prior_report["cases"]:
        if digest(previous / row["output"]) != row["png_sha256"]:
            raise ValueError("Prior material output changed")
    output.mkdir(parents=True)
    plan = {**prior_plan, "upstream_plan_sha256": digest(previous / "plan.json"),
            "upstream_report_sha256": digest(previous / "report.json"),
            "upstream_directory": previous.relative_to(ROOT).as_posix(),
            "upstream_fields_sha256": frozen_fields,
            "algorithm_sha256": {name: digest(owned(name)) for name in ALGORITHM_FILES}}
    save(output / "plan.json", plan)
    for name in ALGORITHM_FILES:
        shutil.copyfile(owned(name), output / Path(name).name)
    sources = {row["id"]: row for row in plan["sources"]}
    guides = {row["id"]: row for row in plan["guides"]}
    prepared = {row["style_id"]: row for row in read(previous / "prepared.json")["guides"]}
    result_dir = output / "results"
    result_dir.mkdir()
    report = {"schema": plan["schema"], "production_enabled": False, "artist_required": False,
              "training": False, "new_model_calls": 0, "new_diffusion_calls": 0,
              "reused_saved_neural_fields": True, "cases": [], "controls": prior_report["controls"],
              "catalog_cache_independent": prior_report["catalog_cache_independent"]}
    try:
        for old_case in prior_report["cases"]:
            source, guide = sources[old_case["subject_id"]], guides[old_case["style_id"]]
            for name, checksum in ((source["source"], source["sha256"]), (source["labels"], source["labels_sha256"]),
                                   (source["points478"], source["points478_sha256"]), (guide["reference"], guide["sha256"])):
                if digest(owned(name)) != checksum:
                    raise ValueError("Frozen correction input changed")
            original, reference = rgb(owned(source["source"])), rgb(owned(guide["reference"]))
            labels = np.array(Image.open(owned(source["labels"])))
            ref_record = prepared[guide["id"]]
            if digest(previous / ref_record["labels"]) != ref_record["labels_sha256"]:
                raise ValueError("Frozen reference parsing changed")
            ref_labels = np.array(Image.open(previous / ref_record["labels"]))
            points = read(owned(source["points478"]))["points"]
            file = previous / "results" / (old_case["id"] + "-fields.npz")
            if digest(file) != frozen_fields[old_case["id"]]:
                raise ValueError("Frozen learned fields changed")
            with np.load(file, allow_pickle=False) as saved:
                fields = {name: saved[name].copy() for name in ("eye", "cheek")}
                corrected, masks, metrics = apply_counterfactual(original, reference, labels, ref_labels, points,
                                                                saved["baseline"], saved["edited"], fields, guide["id"])
            path = result_dir / (old_case["id"] + ".png")
            Image.fromarray(corrected).save(path)
            prior_image = rgb(owned(old_case["previous"])) if old_case["previous"] else np.full_like(original, 238)
            images = [original, reference, prior_image, corrected]
            sheet = Image.new("RGB", (2048, 544), "white")
            draw = ImageDraw.Draw(sheet)
            for index, (title, array) in enumerate(zip(["Original", "Existing style guide (AI output)", old_case["previous_title"], "Automatic source anchored correction"], images)):
                draw.text((index * 512 + 5, 8), title, fill="black")
                sheet.paste(Image.fromarray(array), (index * 512, 32))
            sheet.save(result_dir / (old_case["id"] + "-comparison.png"))
            record = {**old_case, **metrics, "output": path.relative_to(output).as_posix(),
                      "rgb_sha256": pixel_hash(corrected), "png_sha256": digest(path),
                      "reused_neural_field_sha256": frozen_fields[old_case["id"]], "visual_review": "PENDING",
                      "eligible_for_training": False}
            report["cases"].append(record)
            print("MATERIAL_CORRECTED", len(report["cases"]), "/", plan["case_count"], old_case["id"], flush=True)
        report["status"] = "DONE_MATERIAL_CORRECTION_VISUAL_REVIEW_REQUIRED"
    finally:
        save(output / "report.json", report)
    gallery(output)


def refine(previous, output, material_inputs, representative=False):
    """Refine frozen automatic fields using source confidence/observed detail.

    All previous panels are the actual November4 automatic results, rather
    than missing or substituted generation baselines. No neural model calls.
    """
    previous, output, material_inputs = map(owned, (previous, output, material_inputs))
    if output.exists():
        raise ValueError("Preserve previous review outputs; use a new directory")
    old_plan, old_report = read(previous / "plan.json"), read(previous / "report.json")
    raw = owned(old_plan["upstream_directory"])
    prepared = {row["style_id"]: row for row in read(raw / "prepared.json")["guides"]}
    probabilities = read(material_inputs / "lip-probabilities/report.json")
    confidence = {row["id"]: row for row in probabilities["sources"]}
    detail_dir = material_inputs / "detail-reference"
    detail = read(detail_dir / "report.json")
    def checked(path, checksum):
        path = owned(path)
        if digest(path) != checksum:
            raise ValueError("Frozen material input changed: " + str(path))
        return path
    detail_image = rgb(checked(detail["source"], detail["source_sha256"]))
    detail_labels = np.array(Image.open(checked(detail_dir / "labels.png", detail["labels_sha256"])))
    detail_points = np.load(checked(detail_dir / "points68.npy", detail["points68_sha256"]), allow_pickle=False)
    selected = {( "054109", "exp_manga_lash"), ("056266", "exp_icy_silver"),
                ("006553", "classic_red_lip"), ("035149", "bold_evening_glam"),
                ("054109", "natural_makeup"), ("006553", "bronze_golden_glam"),
                ("056266", "dewy_peach"), ("035149", "matte_nude"),
                ("054109", "exp_cloud_berry_lips")}
    cases = [row for row in old_report["cases"] if not representative or (row["subject_id"], row["style_id"]) in selected]
    if len(old_report["cases"]) != 52 or (representative and len(cases) != len(selected)):
        raise ValueError("Complete baseline matrix required")
    for case in old_report["cases"]:
        checked(previous / case["output"], case["png_sha256"])
    inputs = {"probabilities": digest(material_inputs / "lip-probabilities/report.json"),
              "detail": digest(detail_dir / "report.json"),
              "upstream_plan": digest(previous / "plan.json"), "upstream_report": digest(previous / "report.json")}
    output.mkdir(parents=True); result_dir = output / "results"; result_dir.mkdir()
    plan = {**old_plan, "date": "2026-11-05", "case_count": len(cases),
            "baseline_directory": previous.relative_to(ROOT).as_posix(),
            "material_input_directory": material_inputs.relative_to(ROOT).as_posix(),
            "field_directory": raw.relative_to(ROOT).as_posix(), "material_input_reports_sha256": inputs,
            "detail_source_provenance": detail, "lip_parser_provenance": probabilities["parser"],
            "algorithm_sha256": {name: digest(owned(name)) for name in ALGORITHM_FILES},
            "representative_only": representative}
    save(output / "plan.json", plan)
    for name in ALGORITHM_FILES:
        shutil.copyfile(owned(name), output / Path(name).name)
    sources, guides = ({row["id"]: row for row in plan[key]} for key in ("sources", "guides"))
    report = {"schema": "automatic-material-review-v1", "production_enabled": False,
              "training": False, "artist_required": False, "new_model_calls": 0,
              "preparation_cpu_parser_calls": 5, "preparation_cpu_detail_spiga_passes": 2,
              "new_diffusion_calls": 0, "reused_saved_neural_fields": True, "cases": []}
    try:
        for old_case in cases:
            started = time.perf_counter()
            source, guide = sources[old_case["subject_id"]], guides[old_case["style_id"]]
            original = rgb(checked(source["source"], source["sha256"]))
            reference = rgb(checked(guide["reference"], guide["sha256"]))
            labels = np.array(Image.open(checked(source["labels"], source["labels_sha256"])))
            points = read(checked(source["points478"], source["points478_sha256"]))["points"]
            conf, prep = confidence[source["id"]], prepared[guide["id"]]
            if conf["source_sha256"] != source["sha256"] or not conf["hard_labels_exact"]:
                raise ValueError("Lip confidence is not bound to the original source")
            context = {"lip_probability": np.load(checked(material_inputs / "lip-probabilities" / conf["file"], conf["sha256"]), allow_pickle=False),
                       "detail_image": detail_image, "detail_labels": detail_labels, "detail_points68": detail_points,
                       "reference_points68": np.load(checked(raw / prep["points68"], prep["points68_sha256"]), allow_pickle=False)}
            ref_labels = np.array(Image.open(checked(raw / prep["labels"], prep["labels_sha256"])))
            field_path = raw / "results" / (old_case["id"] + "-fields.npz")
            checked(field_path, old_plan["upstream_fields_sha256"][old_case["id"]])
            with np.load(field_path, allow_pickle=False) as saved:
                corrected, masks, metrics = apply_counterfactual(original, reference, labels, ref_labels, points,
                    saved["baseline"], saved["edited"], {name: saved[name].copy() for name in ("eye", "cheek")}, guide["id"], materials=context)
            path = result_dir / (old_case["id"] + ".png"); Image.fromarray(corrected).save(path)
            np.savez_compressed(result_dir / (old_case["id"] + "-masks.npz"), **masks)
            prior_path = previous / old_case["output"]
            before = rgb(prior_path)
            sheet = Image.new("RGB", (2048, 544), "white"); draw = ImageDraw.Draw(sheet)
            titles = ["Original", "Selected makeup guide (AI)", "Previous automatic result, Nov4", "Source material correction, EXPERIMENTAL"]
            for i, (title, value) in enumerate(zip(titles, (original, reference, before, corrected))):
                draw.text((i * 512 + 5, 8), title, fill="black"); sheet.paste(Image.fromarray(value), (i * 512, 32))
            sheet.save(result_dir / (old_case["id"] + "-comparison.png"))
            report["cases"].append({"id": old_case["id"], "subject_id": source["id"], "style_id": guide["id"],
                "output": path.relative_to(output).as_posix(), "png_sha256": digest(path), "rgb_sha256": pixel_hash(corrected),
                "previous": prior_path.relative_to(ROOT).as_posix(), "previous_title": titles[2],
                "reused_neural_field_sha256": digest(field_path), "lip_probability_sha256": conf["sha256"],
                "changed_from_previous_pixels": int(np.any(corrected != before, axis=2).sum()),
                "source_photo": source["source_photo"], "source_dataset_license": source["source_dataset_license"],
                "seconds": time.perf_counter() - started, "visual_review": "PENDING", "eligible_for_training": False, **metrics})
            print("MATERIAL_REFINED", len(report["cases"]), "/", len(cases), old_case["id"], flush=True)
        report["status"] = "DONE_MATERIAL_CORRECTION_VISUAL_REVIEW_REQUIRED"
    finally:
        save(output / "report.json", report)
    gallery(output)


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("phase", choices=["prepare", "generate", "gallery", "reapply", "refine"])
    cli.add_argument("--output", default="artifacts/makeup-local-transfer-20261104/catalog-01")
    cli.add_argument("--from-directory", default="artifacts/makeup-local-transfer-20261104/catalog-01")
    cli.add_argument("--material-inputs", default="artifacts/makeup-refinement-20261105")
    cli.add_argument("--representative", action="store_true")
    args = cli.parse_args()
    if args.phase == "refine":
        refine(args.from_directory, args.output, args.material_inputs, args.representative)
    elif args.phase == "reapply":
        reapply(args.from_directory, args.output)
    else:
        {"prepare": prepare, "generate": generate, "gallery": gallery}[args.phase](args.output)
