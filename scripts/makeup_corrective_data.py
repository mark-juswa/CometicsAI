"""Style labeled corrective data on the established source split and quality gate.

Target creation, target admission and GPU training remain separate operations.
"""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
DATASET_ID = "DATA-M001-CORRECTIVE-001"
SCHEMA = "DATA-M001-corrective-final-v1"
SOURCE_ARCHIVE_SHA256 = "c15fd40199b4d46050dc864eaed647b0ad41921507c2f99cb1cfec2b46922c6a"
STYLE_IDS = {"natural_makeup", "no_makeup_makeup", "soft_glam", "smoky_glam", "dewy_peach", "rosy_pink",
    "bronze_golden_glam", "matte_nude", "classic_red_lip", "bold_evening_glam",
    "exp_cloud_berry_lips", "exp_manga_lash", "exp_icy_silver"}
CATALOG = ROOT / "data/makeup" / DATASET_ID / "catalog.json"
SOURCE_DATASET = ROOT / ".tmp/data_m001/paired_selection/final_v1"


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def owned(root, name):
    root = Path(root).resolve()
    if not isinstance(name, str) or "\\" in name or ":" in name:
        raise ValueError("Invalid corrective relative path")
    path = (root / name).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError("Missing or escaped corrective file")
    return path


def validate_catalog(catalog):
    styles = catalog.get("styles", [])
    if (catalog.get("schema") != "makeup-corrective-catalog-v1" or len(styles) != 13
            or {s["id"] for s in styles} != STYLE_IDS or len({s["caption"] for s in styles}) != 13
            or catalog.get("production_enabled") is not False):
        raise ValueError("Expected the frozen complete13stylecorrectivecatalog")
    for style in styles:
        if (set(style["components"]) != {"eyes", "lips", "blush", "complexion_finish", "brows", "contour_highlight"}
                or style["name"] not in style["caption"] or not catalog.get("preservation_instruction")
                or catalog["preservation_instruction"] not in style["caption"]
                or not all(isinstance(s, str) and s.strip() for s in style["components"].values())):
            raise ValueError("Style supervision lacks a complete cosmetic description")
    return {s["id"]: s for s in styles}


def initialize(workspace, source_dataset=SOURCE_DATASET, catalog_path=CATALOG, *, extra_training_sources=()):
    from PIL import Image
    workspace, source_dataset = Path(workspace), Path(source_dataset)
    if workspace.exists():
        raise ValueError("Preserve existing corrective workspace")
    catalog = read(catalog_path)
    styles = validate_catalog(catalog)
    old = read(source_dataset / "manifests/pairs.json")
    selection = read(source_dataset / "manifests/selection.json")
    if selection["source_archive_sha256"] != SOURCE_ARCHIVE_SHA256:
        raise ValueError("Source archive provenance differs")
    if (len(selection["train_ids"]) != 10 or len(selection["validation_ids"]) != 2
            or set(selection["train_ids"]) & set(selection["validation_ids"])):
        raise ValueError("Original identity split is not intact")
    workspace.mkdir(parents=True)
    shutil.copyfile(catalog_path, workspace / "catalog.json")
    sources = []
    for split in ("train", "validation"):
        for identity in selection[split + "_ids"]:
            row = next(r for r in old if r["identity_id"] == identity and r["split"] == split)
            source = owned(source_dataset, row["reference"])
            if digest(source) != row["source_sha256"]:
                raise ValueError("Original source image differs")
            with Image.open(source) as image:
                if image.size != (512, 512) or image.mode != "RGB":
                    raise ValueError("Original source is not RGB512")
                rgb_sha = sha256(image.tobytes()).hexdigest()
            target = workspace / "origins" / (identity + ".jpg")
            target.parent.mkdir(exist_ok=True)
            shutil.copyfile(source, target)
            sources.append({"identity_id": identity, "split": split, "path": target.relative_to(workspace).as_posix(),
                "sha256": row["source_sha256"], "rgb_sha256": rgb_sha, "source_photo": row["source_photo"],
                "source_dataset_license": selection["source_dataset_license"]})
    historical_selection = json.loads(json.dumps(selection))
    for extra in extra_training_sources:
        identity = extra["identity_id"]
        if (identity in {s["identity_id"] for s in sources} or extra.get("split") != "train"
                or extra.get("source_archive_sha256") != SOURCE_ARCHIVE_SHA256
                or extra.get("ffhq_metadata_md5") != selection["ffhq_metadata_md5"]):
            raise ValueError("Additional source is duplicate, split leaking or not from the pinned archive/metadata")
        path = owned(ROOT, extra["path"])
        if digest(path) != extra["sha256"]:
            raise ValueError("Additional original hash differs")
        with Image.open(path) as image:
            if image.size != (512, 512) or image.mode != "RGB" or image.format != "JPEG":
                raise ValueError("Additional source must be an original RGB512JPEG")
            rgb_sha = sha256(image.tobytes()).hexdigest()
        target = workspace / "origins" / (identity + ".jpg")
        shutil.copyfile(path, target)
        sources.append({"identity_id": identity, "split": "train", "path": target.relative_to(workspace).as_posix(),
            "sha256": extra["sha256"], "rgb_sha256": rgb_sha, "source_photo": extra["source_photo"],
            "source_dataset_license": extra["source_dataset_license"], "added_training_source": True,
            "source_archive_member": extra["source_archive_member"], "ffhq_metadata_md5": extra["ffhq_metadata_md5"]})
        selection["train_ids"].append(identity)
    if extra_training_sources:
        selection["schema"] = "makeup-corrective-source-assignment-v1"
        selection["dataset_id"] = DATASET_ID
        selection["review_rule"] = "Source identity assignment only; new synthetic targets require separate corrective quality admission."
    # Balanced finite plan, not a count of accepted targets. Keep useful existing
    # training-identity proofs eligible without concentrating every style on them.
    preferred = {"soft_glam": "006553", "bold_evening_glam": "035149", "exp_icy_silver": "006553",
                 "matte_nude": "006553", "dewy_peach": "035149", "classic_red_lip": "035149",
                 "no_makeup_makeup": "035149", "exp_manga_lash": "006553"}
    plan = []
    for i, style_id in enumerate(styles):
        train_ids = [selection["train_ids"][(i + offset) % 10] for offset in (0, 3, 5, 8)]
        if style_id in preferred and preferred[style_id] not in train_ids:
            train_ids[0] = preferred[style_id]
        if extra_training_sources:
            replace = next(j for j in reversed(range(4)) if train_ids[j] != preferred.get(style_id))
            train_ids[replace] = extra_training_sources[i % len(extra_training_sources)]["identity_id"]
        for split, ids in (("train", train_ids), ("validation", selection["validation_ids"])):
            for identity in ids:
                plan.append({"pair_id": identity + "-" + style_id, "identity_id": identity,
                             "split": split, "style_id": style_id})
    frozen = {"schema": "makeup-corrective-selection-v1", "dataset_id": DATASET_ID,
        "source_archive_sha256": SOURCE_ARCHIVE_SHA256, "source_selection": selection,
        "historical_source_selection": historical_selection,
        "catalog_sha256": digest(workspace / "catalog.json"), "sources": sources, "planned_pairs": plan,
        "planned_counts": {split: sum(r["split"] == split for r in plan) for split in ("train", "validation")},
        "production_enabled": False, "training_started": False}
    write(workspace / "manifests/selection.json", frozen)
    write(workspace / "manifests/pairs.json", [])
    write(workspace / "reports/historical-caption-audit.json", {"source_manifest_sha256": digest(source_dataset / "manifests/pairs.json"),
        "pairs": len(old), "unique_captions": len({r["caption"] for r in old}),
        "caption_counts": dict(Counter(r["caption"] for r in old)), "style_id_rows": sum("style_id" in r for r in old),
        "interpretation": "A supervision gap, not a measurement of Base-versus-adapter causality."})
    write(workspace / "reports/qa.json", {"schema": SCHEMA, "status": "DRAFT", "dataset_id": DATASET_ID,
        "train_pairs": 0, "validation_pairs": 0, "review_mode": "explicit_human_review"})
    return frozen


def register_target(workspace, prepared_dir, raw_path, generation):
    from PIL import Image
    try:
        from makeup_target_quality import quality_review_template
    except ImportError:
        from scripts.makeup_target_quality import quality_review_template
    workspace, prepared_dir, raw_path = Path(workspace), Path(prepared_dir), Path(raw_path)
    selection = read(workspace / "manifests/selection.json")
    styles = validate_catalog(read(workspace / "catalog.json"))
    report = read(prepared_dir / "report.json")
    identity, style_id = report["source_id"], report["style_id"]
    source = next(s for s in selection["sources"] if s["identity_id"] == identity)
    pair_id = identity + "-" + style_id
    if pair_id not in {p["pair_id"] for p in selection["planned_pairs"]}:
        raise ValueError("Target is outside the frozen identity/style plan")
    if (generation.get("tool") != "built-in image_gen" or generation.get("source_id") != identity
            or generation.get("style_id") != style_id or generation.get("training_accepted") is not False
            or generation.get("production_enabled") is not False
            or generation.get("prompt_record") not in ("EXACT", "SUMMARY ONLY")
            or not generation.get("prompt") or not generation.get("model_id")):
        raise ValueError("Truthful external target generation provenance required")
    target = prepared_dir / "prepared.png"
    if (digest(target) != report["prepared_sha256"] or digest(raw_path) != report["raw_sha256"]
            or report["source_sha256"] != source["sha256"] or report["training_accepted"] is not False
            or report["not_our_makeup_model_output"] is not True):
        raise ValueError("Teacher preparation/input binding differs")
    rows = read(workspace / "manifests/pairs.json")
    if pair_id in {r["pair_id"] for r in rows}:
        raise ValueError("Preserve the previous registered target and review")
    split = source["split"]
    reference = workspace / split / "reference" / (pair_id + ".png")
    result = workspace / split / "target" / (pair_id + ".png")
    reference.parent.mkdir(parents=True, exist_ok=True)
    result.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(owned(workspace, source["path"])) as original:
        original.convert("RGB").save(reference)
    shutil.copyfile(target, result)
    caption = styles[style_id]["caption"]
    caption_path = result.with_suffix(".txt")
    caption_path.write_text(caption + "\n", encoding="utf-8")
    provenance = workspace / "provenance" / pair_id
    provenance.mkdir(parents=True)
    shutil.copyfile(raw_path, provenance / "teacher-raw.png")
    shutil.copyfile(prepared_dir / "report.json", provenance / "preparation.json")
    shutil.copyfile(prepared_dir / "alpha.png", provenance / "alpha.png")
    write(provenance / "generation.json", generation)
    row = {"pair_id": pair_id, "identity_id": identity, "split": split, "style_id": style_id,
        "reference": reference.relative_to(workspace).as_posix(), "target": result.relative_to(workspace).as_posix(),
        "source_sha256": digest(reference), "target_sha256": digest(result),
        "source_original_sha256": source["sha256"], "source_original_path": source["path"],
        "source_rgb_sha256": source["rgb_sha256"], "source_photo": source["source_photo"],
        "source_dataset_license": source["source_dataset_license"], "caption": caption,
        "caption_path": caption_path.relative_to(workspace).as_posix(), "target_variant_position": None,
        "target_variant_is_style_class": False, "target_origin": "external_editor_source_fitted",
        "target_is_archived_ffhq_variant": False,
        "provenance_files": {p.relative_to(workspace).as_posix(): digest(p) for p in provenance.iterdir()},
        "preparation_code_sha256": report.get("preparation_code_sha256"),
        "preparation_record": "Recorded recipe hash" if report.get("preparation_code_sha256") else "Historical proof, recipe hash not recorded"}
    rows.append(row)
    template = quality_review_template(rows)
    review_path = workspace / "reports/target_quality.json"
    if review_path.exists():
        prior = {r["pair_id"]: r for r in read(review_path)["pairs"]}
        template["pairs"] = [prior.get(r["pair_id"], r) for r in template["pairs"]]
    write(workspace / "manifests/pairs.json", rows)
    write(review_path, template)
    write(workspace / "reports/qa.json", {"schema": SCHEMA, "status": "DRAFT", "dataset_id": DATASET_ID,
        "train_pairs": sum(r["split"] == "train" for r in rows),
        "validation_pairs": sum(r["split"] == "validation" for r in rows), "review_mode": "explicit_human_review"})
    return row


def validate_corrective_dataset(dataset, *, require_finalized=True):
    from PIL import Image
    try:
        from makeup_target_quality import validate_dataset_quality, validate_quality
    except ImportError:
        from scripts.makeup_target_quality import validate_dataset_quality, validate_quality
    dataset = Path(dataset)
    qa, selection = read(dataset / "reports/qa.json"), read(dataset / "manifests/selection.json")
    statuses = {"FINALIZED"} if require_finalized else {"DRAFT", "FINALIZED"}
    if qa.get("schema") != SCHEMA or qa.get("status") not in statuses or qa.get("dataset_id") != DATASET_ID:
        raise ValueError("Corrective data is not finalized")
    if selection.get("source_archive_sha256") != SOURCE_ARCHIVE_SHA256 or digest(dataset / "catalog.json") != selection["catalog_sha256"]:
        raise ValueError("Corrective source/catalog binding differs")
    styles = validate_catalog(read(dataset / "catalog.json"))
    rows = read(dataset / "manifests/pairs.json")
    expected = {p["pair_id"]: p for p in selection["planned_pairs"]}
    if len(rows) != 78 or len(expected) != 78 or {r["pair_id"] for r in rows} != set(expected):
        raise ValueError("Complete52train/26validationcorrectiveplan required")
    sources = {s["identity_id"]: s for s in selection["sources"]}
    original = selection["source_selection"]
    historical = selection.get("historical_source_selection", original)
    added = {s["identity_id"] for s in sources.values() if s.get("added_training_source") is True}
    if (len(historical["train_ids"]) != 10 or len(historical["validation_ids"]) != 2
            or original["validation_ids"] != historical["validation_ids"]
            or set(original["train_ids"]) != set(historical["train_ids"]) | added
            or set(original["train_ids"]) & set(original["validation_ids"])):
        raise ValueError("Frozen source identity split differs")
    counts = Counter()
    coverage = {}
    for row in rows:
        planned, source = expected[row["pair_id"]], sources[row["identity_id"]]
        if (any(row.get(k) != planned[k] for k in ("identity_id", "split", "style_id"))
                or row["split"] != source["split"] or row["identity_id"] not in original[row["split"] + "_ids"]
                or row["caption"] != styles[row["style_id"]]["caption"]
                or owned(dataset, row["caption_path"]).read_text(encoding="utf-8").strip() != row["caption"]
                or row.get("target_origin") != "external_editor_source_fitted"
                or row.get("target_is_archived_ffhq_variant") is not False):
            raise ValueError("Corrective style/caption/origin/split differs")
        if (digest(owned(dataset, row["source_original_path"])) != source["sha256"]
                or row["source_original_sha256"] != source["sha256"] or row["source_photo"] != source["source_photo"]):
            raise ValueError("Original photo provenance differs")
        for kind in ("reference", "target"):
            path = owned(dataset, row[kind])
            with Image.open(path) as image:
                if image.format != "PNG" or image.mode != "RGB" or image.size != (512, 512):
                    raise ValueError("Corrective training requires lossless RGB512PNG pairs")
                if kind == "reference" and sha256(image.tobytes()).hexdigest() != source["rgb_sha256"]:
                    raise ValueError("Training original pixels differ from source")
        if len(row.get("provenance_files", {})) != 4 or any(digest(owned(dataset, name)) != value for name, value in row["provenance_files"].items()):
            raise ValueError("Teacher generation/preparation evidence differs")
        counts[row["split"]] += 1
        coverage.setdefault((row["split"], row["style_id"]), set()).add(row["identity_id"])
    if counts != {"train": 52, "validation": 26} or any(len(coverage.get((split, style), set())) != count
            for split, count in (("train", 4), ("validation", 2)) for style in styles):
        raise ValueError("Corrective style/identity coverage is incomplete")
    quality = (validate_dataset_quality(dataset) if require_finalized else
               validate_quality(rows, read(dataset / "reports/target_quality.json"), dataset))
    return {"dataset_schema": SCHEMA, "dataset_id": DATASET_ID, "pair_counts": dict(counts),
        "identity_counts": {split: len({r["identity_id"] for r in rows if r["split"] == split}) for split in counts},
        "catalog_sha256": digest(dataset / "catalog.json"), "source_archive_sha256": SOURCE_ARCHIVE_SHA256,
        "pairs_sha256": digest(dataset / "manifests/pairs.json"), "qa_sha256": digest(dataset / "reports/qa.json"),
        "selection_sha256": digest(dataset / "manifests/selection.json"), "corrective_quality": quality}


def finalize(workspace, destination):
    workspace, destination = Path(workspace).resolve(), Path(destination).resolve()
    if destination.exists() or destination.is_relative_to(workspace):
        raise ValueError("Use a fresh final directory outside the candidate workspace")
    # All real pair/style/image/provenance AND human appearance admission checks
    # run before copying or writing a FINALIZED label anywhere.
    evidence = validate_corrective_dataset(workspace, require_finalized=False)
    shutil.copytree(workspace, destination)
    qa = read(destination / "reports/qa.json")
    qa.update(status="FINALIZED", train_pairs=52, validation_pairs=26,
              source_archive_sha256=SOURCE_ARCHIVE_SHA256, review_mode="explicit_human_review")
    write(destination / "reports/qa.json", qa)
    return validate_corrective_dataset(destination)


if __name__ == "__main__":
    import argparse
    cli = argparse.ArgumentParser(description=__doc__)
    sub = cli.add_subparsers(dest="operation", required=True)
    init = sub.add_parser("initialize"); init.add_argument("workspace", type=Path)
    check = sub.add_parser("validate"); check.add_argument("workspace", type=Path)
    final = sub.add_parser("finalize"); final.add_argument("workspace", type=Path); final.add_argument("destination", type=Path)
    args = cli.parse_args()
    if args.operation == "initialize":
        result = initialize(args.workspace)
    elif args.operation == "finalize":
        result = finalize(args.workspace, args.destination)
    else:
        result = validate_corrective_dataset(args.workspace)
    print(json.dumps(result, indent=2))
