"""Offline boundary-color Makeup blending feasibility; no serving integration."""
import argparse
import base64
from hashlib import sha256
import html
import json
from pathlib import Path
import time

import cv2
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
CONFIG = {"face_labels": [1, 2, 3, 4, 5, 6, 7, 10, 11, 12], "close_kernel": 9,
          "minimum_overlap": 0.80, "minimum_face_pixels": 5000, "clone_mode": "NORMAL_CLONE", "boundary_padding_pixels": 4}


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def owned(name):
    path = (ROOT / name).resolve()
    if not path.is_relative_to(ROOT):
        raise ValueError("Input path escapes project")
    return path


def face_region(labels):
    if labels.shape != (512, 512) or not np.issubdtype(labels.dtype, np.integer) or labels.min() < 0 or labels.max() > 18:
        raise ValueError("Expected 512-square parser labels 0..18")
    binary = np.isin(labels, CONFIG["face_labels"]).astype(np.uint8)
    count, components, stats, _ = cv2.connectedComponentsWithStats(binary, 8)
    if count < 2:
        raise ValueError("No face region")
    binary = (components == 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])).astype(np.uint8)
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    filled = np.zeros_like(binary)
    cv2.drawContours(filled, contours, -1, 1, cv2.FILLED)
    filled = cv2.morphologyEx(filled, cv2.MORPH_CLOSE,
                            cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)))
    if int(filled.sum()) < CONFIG["minimum_face_pixels"]:
        raise ValueError("Insufficient face region")
    return filled.astype(bool)


def blend(source, raw, source_labels, raw_labels):
    for image in (source, raw):
        if image.dtype != np.uint8 or image.shape != (512, 512, 3):
            raise ValueError("Expected uint8 512-square RGB")
    original_face, generated_face = face_region(source_labels), face_region(raw_labels)
    union = original_face | generated_face
    mask = original_face & generated_face
    overlap = float(mask.sum() / union.sum())
    if overlap < CONFIG["minimum_overlap"] or int(mask.sum()) < CONFIG["minimum_face_pixels"]:
        raise ValueError("Source/generated face regions do not sufficiently overlap")
    # All facial features stay inside one region. Separate protected islands were
    # the source of pale feature-adjacent transitions in the rejected Lab method.
    # Cosmetic RGB is not promised unchanged: gradient-domain blending may alter it.
    mask_u8 = mask.astype(np.uint8) * 255
    x, y, w, h = cv2.boundingRect(mask_u8)
    started = time.perf_counter()
    if np.array_equal(source, raw):
        result = source.copy()
    else:
        padding = CONFIG["boundary_padding_pixels"]
        original = cv2.copyMakeBorder(source, padding, padding, padding, padding, cv2.BORDER_REFLECT_101)
        generated = cv2.copyMakeBorder(raw, padding, padding, padding, padding, cv2.BORDER_REFLECT_101)
        padded_mask = cv2.copyMakeBorder(mask_u8, padding, padding, padding, padding, cv2.BORDER_CONSTANT, value=0)
        combined = cv2.cvtColor(cv2.seamlessClone(
            cv2.cvtColor(generated, cv2.COLOR_RGB2BGR),
            cv2.cvtColor(original, cv2.COLOR_RGB2BGR), padded_mask,
            (x + w // 2 + padding, y + h // 2 + padding), cv2.NORMAL_CLONE), cv2.COLOR_BGR2RGB)
        result = combined[padding:-padding, padding:-padding].copy()
        result[~mask] = source[~mask]
    return result, mask, {"face_overlap_iou": overlap, "blend_pixels": int(mask.sum()),
                         "cpu_blend_seconds": time.perf_counter() - started,
                         "outside_face_changed_from_original": int(np.any(result[~mask] != source[~mask], axis=1).sum()),
                         "cosmetic_pixels_hard_protected": False}


def patch_diagnostic(source, raw, result, source_labels, raw_labels, box):
    x0, y0, x1, y1 = box
    region = np.zeros((512, 512), bool)
    region[y0:y1, x0:x1] = True
    region &= (source_labels == 1) & (raw_labels == 1)
    if region.sum() < 200:
        return {"status": "INSUFFICIENT_COMMON_SKIN"}
    centers = {}
    for name, rgb in (("source", source), ("raw", raw), ("blend", result)):
        values = cv2.cvtColor(rgb.astype(np.float32) / 255, cv2.COLOR_RGB2LAB)
        centers[name] = np.median(values[region], axis=0).tolist()
    return {"status": "DIAGNOSTIC_ONLY", "median_lab": centers, "pixels": int(region.sum()),
            "note": "Existing development forehead box; not used to fit blend, not a calibrated skin or appearance score."}


def load_plan(path):
    plan = json.loads(Path(path).read_text(encoding="utf-8"))
    if (plan.get("experiment") != "MAKEUP-BLEND-001"
            or plan.get("schema") != "beautycore-makeup-boundary-blend-v1"
            or plan.get("production_enabled") is not False or plan.get("training") is not False
            or plan.get("new_diffusion_calls") != 0 or plan.get("configuration") != CONFIG
            or len(plan.get("sources", [])) != 2 or len(plan.get("cases", [])) != 6):
        raise ValueError("One-method offline scope differs")
    for row in plan["sources"]:
        for name, key in (("source", "source_sha256"), ("source_labels", "source_labels_sha256")):
            if digest(owned(row[name])) != row[key]:
                raise ValueError("Frozen source/label differs")
    for row in plan["cases"]:
        for name, key in (("raw", "raw_sha256"), ("raw_labels", "raw_labels_sha256")):
            if digest(owned(row[name])) != row[key]:
                raise ValueError("Frozen result/label differs")
    return plan


def rgb(path):
    with Image.open(path) as image:
        return np.asarray(image.convert("RGB")).copy()


def gallery(output, rows):
    figures = []
    for row in rows:
        figures.append("<h2>" + html.escape(row["id"]) + "</h2><div class=grid>")
        for label, key in (("Original", "source_output"), ("AI output: white cast", "raw_output"), ("Boundary blend: EXPERIMENTAL", "output")):
            raw = (output / row[key]).read_bytes()
            figures.append("<figure><figcaption>" + label + "</figcaption><button onclick='show(this)'><img alt='" +
                           html.escape(label, quote=True) + "' src='data:image/png;base64," +
                           base64.b64encode(raw).decode() + "'></button></figure>")
        figures.append("</div>")
    page = """<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>Makeup boundary blend — NOT DEPLOYED</title><style>body{font:16px system-ui;margin:24px auto;padding:0 16px;max-width:1500px;background:#f5f5f8}
.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}figure{margin:0;min-width:0}img{max-width:100%;display:block}
button{border:0;padding:0;background:none;cursor:zoom-in}dialog{max-width:95vw;max-height:95vh}dialog img{max-height:85vh;object-fit:contain}
@media(max-width:700px){.grid{grid-template-columns:1fr}}</style><h1>Makeup boundary blend — NOT DEPLOYED</h1>
<p>One fixed method on six saved images. Review skin tone, makeup visibility, face details and forehead/jaw/eye/mouth transitions.
Outside the blend, the original photo is restored. Generated face geometry/texture is not repaired. No success is inferred from numeric diagnostics.</p>""" + "".join(figures) + """
<dialog id=viewer><button onclick="this.parentElement.close()">Close</button><img alt="Original-size result"></dialog>
<script>function show(b){const d=document.getElementById('viewer');d.querySelector('img').src=b.querySelector('img').src;d.showModal();}</script>"""
    (output / "review-self-contained.html").write_bytes(page.encode())


def run(plan_path, output):
    plan = load_plan(plan_path)
    output = Path(output)
    if output.exists():
        raise ValueError("Preserve existing evidence; new output required")
    output.mkdir(parents=True)
    (output / "plan.json").write_bytes(Path(plan_path).read_bytes())
    report = {"experiment": "MAKEUP-BLEND-001", "production_enabled": False, "new_diffusion_calls": 0,
              "status": "IN_PROGRESS", "opencv": cv2.__version__, "plan_sha256": digest(plan_path), "cases": []}
    sources = {row["id"]: row for row in plan["sources"]}
    def save():
        (output / "report.json").write_bytes((json.dumps(report, indent=2) + "\n").encode())
    try:
        for row in plan["cases"]:
            subject = sources[row["subject_id"]]
            source, raw = rgb(owned(subject["source"])), rgb(owned(row["raw"]))
            source_labels = np.asarray(Image.open(owned(subject["source_labels"]))).copy()
            raw_labels = np.asarray(Image.open(owned(row["raw_labels"]))).copy()
            result, mask, metrics = blend(source, raw, source_labels, raw_labels)
            names = {"source_output": row["id"]+"-source.png", "raw_output": row["id"]+"-raw.png",
                     "output": row["id"]+"-blend.png"}
            for key, image in (("source_output", source), ("raw_output", raw), ("output", result)):
                Image.fromarray(image).save(output / names[key])
            Image.fromarray(mask.astype(np.uint8)*255).save(output / (row["id"]+"-mask.png"))
            sheet = Image.new("RGB", (1536, 542), "white")
            draw = ImageDraw.Draw(sheet)
            for i, (label, array) in enumerate((("Original", source), ("AI output - white cast", raw), ("Boundary blend - EXPERIMENTAL", result))):
                draw.text((i*512+8, 8), label, fill="black")
                sheet.paste(Image.fromarray(array), (i*512, 30))
            sheet.save(output / (row["id"]+"-comparison.png"))
            report["cases"].append({**row, **names, **metrics, "output_sha256": digest(output/names["output"]),
                                    "rgb_sha256": sha256(result.tobytes()).hexdigest(),
                                    "visual_verdict": "NEEDS_REVIEW",
                                    "forehead_diagnostic": patch_diagnostic(source, raw, result, source_labels, raw_labels, subject["neutral_box"])})
            save()
        report["status"] = "COMPLETE_REQUIRES_VISUAL_REVIEW"
    except BaseException as exc:
        report.update(status="FAILED", error_type=type(exc).__name__, error=str(exc))
        raise
    finally:
        save()
        gallery(output, report["cases"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, default=ROOT/"data/makeup/MAKEUP-BLEND-001/plan.json")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args.plan, args.output)
