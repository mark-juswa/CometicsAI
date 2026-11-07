"""Offline MAKEUP-TONE-001: bounded generated-skin tone correction, never serving."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import shutil
import time

import cv2
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
CONFIG = {
    "minimum_lightness_gap": 2.0,
    "maximum_lightness_reduction": 16.0,
    "maximum_chroma_vector": 8.0,
    "inward_feather_pixels": 12.0,
    "protected_feature_margin_pixels": 2,
}


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def read_rgb(path):
    with Image.open(path) as im:
        return np.array(im.convert("RGB"))


def lab(rgb):
    return cv2.cvtColor(rgb.astype(np.float32) / 255.0, cv2.COLOR_RGB2LAB)


def validate_arrays(rgb, labels):
    if (rgb.dtype != np.uint8 or rgb.ndim != 3 or rgb.shape[2] != 3
            or labels.shape != rgb.shape[:2] or not np.issubdtype(labels.dtype, np.integer)
            or labels.min() < 0 or labels.max() > 18):
        raise ValueError("Expected uint8 RGB and matching integer parser labels 0..18")


def neutral_region(rgb, labels, box):
    validate_arrays(rgb, labels)
    h, w = labels.shape
    if len(box) != 4 or any(type(v) is not int for v in box):
        raise ValueError("Neutral box must contain four integer coordinates")
    x0, y0, x1, y1 = box
    if not (0 <= x0 < x1 <= w and 0 <= y0 < y1 <= h):
        raise ValueError("Neutral box out of bounds")
    region = np.zeros((h, w), bool)
    region[y0:y1, x0:x1] = True
    distance = cv2.distanceTransform((labels == 1).astype(np.uint8), cv2.DIST_L2, 5)
    region &= distance > 3
    values = lab(rgb)
    if region.sum() < 200:
        raise ValueError("Insufficient neutral forehead skin")
    low, high = np.quantile(values[:, :, 0][region], (0.15, 0.85))
    region &= (values[:, :, 0] >= low) & (values[:, :, 0] <= high)
    if region.sum() < 200:
        raise ValueError("Insufficient neutral skin after highlight/shadow exclusion")
    return region, np.median(values[region], axis=0)


def edit_mask(labels, config):
    if config != CONFIG:
        raise ValueError("Unreviewed correction configuration")
    skin = np.isin(labels, (1, 2))
    if skin.sum() < 1000:
        raise ValueError("Insufficient parsed facial skin")
    feature = np.isin(labels, (3, 4, 5, 6, 7, 10, 11, 12)).astype(np.uint8)
    margin = config["protected_feature_margin_pixels"]
    protected = cv2.dilate(feature, cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE, (margin * 2 + 1, margin * 2 + 1))) > 0
    # Only semantic features are hard-protected; rectangular orbital exclusion
    # created pale boxes in v1. Smoothly fade tone correction near real features.
    for group in ((4, 6), (5, 7)):
        if np.isin(labels, group).sum() < 20:
            raise ValueError("Missing eye/brow group")
    allowed = skin & ~protected
    face_distance = cv2.distanceTransform(skin.astype(np.uint8), cv2.DIST_L2, 5)
    feature_distance = cv2.distanceTransform((~protected).astype(np.uint8), cv2.DIST_L2, 5)
    face_weight = np.clip((face_distance - 0.5) / config["inward_feather_pixels"], 0, 1)
    transition = np.clip(feature_distance / 20.0, 0, 1)
    feature_weight = transition * transition * (3 - 2 * transition)
    alpha = face_weight * feature_weight
    alpha[~allowed] = 0
    return alpha.astype(np.float32), protected


def correct(source, raw, source_labels, raw_labels, box, config=None):
    config = CONFIG if config is None else config
    validate_arrays(source, source_labels)
    validate_arrays(raw, raw_labels)
    if source.shape != raw.shape or config != CONFIG:
        raise ValueError("Image sizes or fixed correction configuration differ")
    source_region, source_center = neutral_region(source, source_labels, box)
    raw_region, raw_center = neutral_region(raw, raw_labels, box)
    alpha, protected = edit_mask(raw_labels, config)
    measured = source_center - raw_center
    white_cast = float(raw_center[0] - source_center[0])
    applied = np.zeros(3, np.float32)
    result = raw.copy()
    started = time.perf_counter()
    if white_cast > config["minimum_lightness_gap"]:
        applied[0] = max(float(measured[0]), -config["maximum_lightness_reduction"])
        chroma = measured[1:].copy()
        norm = float(np.linalg.norm(chroma))
        if norm > config["maximum_chroma_vector"]:
            chroma *= config["maximum_chroma_vector"] / norm
        applied[1:] = chroma
        adjusted = lab(raw) + alpha[:, :, None] * applied
        converted = cv2.cvtColor(adjusted, cv2.COLOR_LAB2RGB)
        edited = np.rint(np.clip(converted, 0, 1) * 255).astype(np.uint8)
        result[alpha > 0] = edited[alpha > 0]
    # Deliberately restore untouched RGB exactly; avoid whole-frame Lab roundtrip.
    changed = np.any(result != raw, axis=2)
    if np.any(changed & (alpha == 0)) or np.any(changed & protected):
        raise RuntimeError("Protected pixels changed")
    corrected_center = np.median(lab(result)[raw_region], axis=0)
    return result, {
        "alpha": alpha, "protected": protected,
        "source_neutral": source_region, "raw_neutral": raw_region,
    }, {
        "status": "APPLIED" if white_cast > config["minimum_lightness_gap"] else "NO_EXCESS_LIGHTNESS",
        "source_neutral_lab": source_center.tolist(),
        "raw_neutral_lab": raw_center.tolist(),
        "corrected_neutral_lab": corrected_center.tolist(),
        "estimated_lightness_gap_before": white_cast,
        "estimated_lightness_gap_after": float(corrected_center[0] - source_center[0]),
        "applied_lab_offset": applied.tolist(),
        "changed_pixels": int(changed.sum()),
        "outside_mask_changed_pixels": int((changed & (alpha == 0)).sum()),
        "protected_changed_pixels": int((changed & protected).sum()),
        "source_neutral_pixels": int(source_region.sum()),
        "raw_neutral_pixels": int(raw_region.sum()),
        "transform_seconds_excluding_regions_and_file_io": time.perf_counter() - started,
        "metric_limit": "Patch statistics are fitted diagnostics, not an independent quality score.",
    }


def save_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def resolve_owned(relative):
    path = (ROOT / relative).resolve()
    if not path.is_relative_to(ROOT):
        raise ValueError("Input path escapes project")
    return path


def load_plan(path):
    plan = json.loads(Path(path).read_text(encoding="utf-8"))
    if (plan.get("experiment") != "MAKEUP-TONE-001" or plan.get("production_enabled") is not False
            or plan.get("training") is not False or plan.get("correction") != CONFIG
            or len(plan["cases"]) != 6 or len(plan["subjects"]) != 2
            or len({r["id"] for r in plan["cases"]}) != 6):
        raise ValueError("Frozen offline six-case scope differs")
    for row in plan["subjects"]:
        if digest(resolve_owned(row["source"])) != row["source_sha256"]:
            raise ValueError("Source hash differs")
    for row in plan["cases"]:
        if digest(resolve_owned(row["raw"])) != row["raw_sha256"]:
            raise ValueError("Raw result hash differs")
    if digest(resolve_owned(plan["source_report"])) != plan["source_report_sha256"]:
        raise ValueError("Raw report hash differs")
    return plan


def mask_overlay(rgb, alpha, neutral):
    out = rgb.copy().astype(np.float32)
    weight = (alpha * 0.35)[:, :, None]
    out = out * (1-weight) + np.array([50, 150, 245]) * weight
    out[neutral] = out[neutral] * 0.4 + np.array([0, 240, 80]) * 0.6
    return np.rint(out).clip(0, 255).astype(np.uint8)


def prepare(plan_path, output):
    plan = load_plan(plan_path)
    output = Path(output)
    if output.exists():
        raise ValueError("New evidence directory required")
    parser_dir = resolve_owned(plan["parser"]["directory"])
    for name, expected in plan["parser"]["files"].items():
        if Path(name).name != name or digest(parser_dir/name) != expected:
            raise ValueError("Cached parser configuration/weights differ")
    output.mkdir(parents=True)
    shutil.copyfile(plan_path, output/"plan.json")
    import torch
    from transformers import SegformerImageProcessor, SegformerForSemanticSegmentation
    torch.set_num_threads(4)
    processor = SegformerImageProcessor.from_pretrained(str(parser_dir), local_files_only=True)
    model = SegformerForSemanticSegmentation.from_pretrained(
        str(parser_dir), local_files_only=True, use_safetensors=True).eval()
    records = []
    items = [dict(r, key="source-"+r["id"], path=r["source"]) for r in plan["subjects"]]
    by_id = {r["id"]:r for r in plan["subjects"]}
    items += [dict(r, key=r["id"], path=r["raw"],
                   neutral_box=by_id[r["subject_id"]]["neutral_box"]) for r in plan["cases"]]
    sheet = Image.new("RGB", (2048, 1090), "white")
    draw = ImageDraw.Draw(sheet)
    for index, item in enumerate(items):
        rgb = read_rgb(resolve_owned(item["path"]))
        if rgb.shape != (512, 512, 3):
            raise ValueError("Expected unchanged 512-square artifact")
        with torch.inference_mode():
            inputs = processor(images=Image.fromarray(rgb), return_tensors="pt")
            logits = model(**inputs).logits
            labels = torch.nn.functional.interpolate(logits, size=(512,512),
                mode="bilinear", align_corners=False).argmax(1)[0].byte().numpy()
        neutral, _ = neutral_region(rgb, labels, item["neutral_box"])
        alpha, _ = edit_mask(labels, plan["correction"])
        name = item["key"]+"-labels.png"
        Image.fromarray(labels).save(output/name)
        overlay = mask_overlay(rgb, alpha, neutral)
        Image.fromarray(overlay).save(output/(item["key"]+"-regions.png"))
        x,y=index%4*512,index//4*545
        sheet.paste(Image.fromarray(overlay), (x,y+25))
        draw.text((x+4,y+5),item["key"],fill="black")
        records.append({"key":item["key"],"labels":name,"labels_sha256":digest(output/name)})
        print("REGIONS", index+1, "/",len(items), item["key"],flush=True)
    sheet.save(output/"region-review.png")
    save_json(output/"prepared.json", {
        "plan_sha256":digest(plan_path),"labels":records,
        "mask_review":"PENDING_QUALITATIVE_INSPECTION",
        "production_enabled":False,
    })


def apply(plan_path, output):
    plan = load_plan(plan_path)
    output = Path(output)
    prepared = json.loads((output/"prepared.json").read_text())
    if (output/"report.json").exists():
        raise ValueError("Do not overwrite completed comparison")
    if digest(plan_path) != prepared["plan_sha256"] or digest(output/"plan.json") != prepared["plan_sha256"]:
        raise ValueError("Prepared plan differs")
    labels = {}
    for row in prepared["labels"]:
        path=(output/row["labels"]).resolve()
        if not path.is_relative_to(output.resolve()) or digest(path) != row["labels_sha256"]:
            raise ValueError("Prepared labels differ")
        labels[row["key"]] = np.asarray(Image.open(path)).copy()
    by_id = {r["id"]:r for r in plan["subjects"]}
    sheets = {sid:Image.new("RGB",(1536,1640),"white") for sid in by_id}
    records = []
    for row in plan["cases"]:
        sid=row["subject_id"]
        source=read_rgb(resolve_owned(by_id[sid]["source"]))
        raw=read_rgb(resolve_owned(row["raw"]))
        result, masks, metrics=correct(source, raw, labels["source-"+sid], labels[row["id"]],
                                       by_id[sid]["neutral_box"], plan["correction"])
        image_path=output/(row["id"]+"-corrected.png")
        Image.fromarray(result).save(image_path)
        Image.fromarray(np.rint(masks["alpha"]*255).astype(np.uint8)).save(output/(row["id"]+"-alpha.png"))
        strip=Image.new("RGB",(1536,550),"white");draw=ImageDraw.Draw(strip)
        for column,(title,rgb) in enumerate((("ORIGINAL",source),("CURRENT RAW",raw),("TONE TEST - NOT DEPLOYED",result))):
            strip.paste(Image.fromarray(rgb),(column*512,30))
            draw.text((column*512+7,8),title+" | "+row["style_id"],fill="black")
        strip_path=output/(row["id"]+"-comparison.png");strip.save(strip_path)
        order=sum(r["subject_id"]==sid for r in records)
        sheets[sid].paste(strip,(0,order*545))
        records.append({**row,"output":image_path.name,"sha256":digest(image_path),
                        "comparison":strip_path.name,"metrics":metrics,
                        "human_verdict":"PENDING"})
        print(row["id"],metrics["status"],"patch L gap",
              round(metrics["estimated_lightness_gap_before"],2),"->",
              round(metrics["estimated_lightness_gap_after"],2),flush=True)
    for sid,sheet in sheets.items():sheet.save(output/(sid+"-comparison.png"))
    save_json(output/"report.json", {
        "experiment":plan["experiment"],"plan_sha256":digest(plan_path),
        "production_enabled":False,"training":False,"gpu_generation_calls":0,
        "cached_parser":plan["parser"],"method":"bounded_lab_offset_on_generated_skin",
        "cases":records,"status":"COMPLETE_REQUIRES_VISUAL_REVIEW",
        "limitations":plan["notes"],
    })
    return records


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--stage",choices=("prepare","apply"),required=True)
    args=parser.parse_args()
    (prepare if args.stage=="prepare" else apply)(args.plan,args.output)
