"""Finalize DATA-001 only after 30 explicit visual ACCEPT reviews.

Example: python scripts/data001_finalize.py --generation-dir data/dataset_v1/kaggle \
    --reviews data/dataset_v1/reviews.json
Reviews JSON maps each source key (e.g. CrewCut_1) to
{"status":"ACCEPT","attempt":1,"notes":"Identity, hairstyle, and background checked"}.
Status REGENERATE or REJECT blocks finalization; no automated image review is claimed.
"""

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import shutil

from PIL import Image, ImageDraw, ImageOps


ROOT = Path(__file__).resolve().parents[1]
SELECTION = json.loads((ROOT / "docs/data/DATA-001-selection.json").read_text(encoding="utf-8"))
PHRASES = {"CrewCut": "a crew cut", "BobHair": "a bob hairstyle", "LayeredHair": "a layered hairstyle"}
MODEL = "black-forest-labs/FLUX.2-klein-base-4B"


def instruction(style):
    return (f"Change the person's hairstyle to {PHRASES[style]} while preserving their identity, "
            "facial features, expression, pose, clothing, lighting, framing, and background.\n")


def sheet(rows, path, size=(280, 280)):
    cols = 3
    page_height = 335
    canvas = Image.new("RGB", (cols * (size[0] * 2 + 20), ((len(rows) + cols - 1) // cols) * page_height), "white")
    draw = ImageDraw.Draw(canvas)
    for i, (source, target, label) in enumerate(rows):
        x, y = (i % cols) * (size[0] * 2 + 20), (i // cols) * page_height
        for photo, left in ((source, x), (target, x + size[0] + 10)):
            with Image.open(photo) as im:
                canvas.paste(ImageOps.contain(im.convert("RGB"), size), (left, y))
        draw.text((x, y + 285), label, fill="black")
        draw.text((x, y + 304), "REFERENCE / REAL       TARGET / GENERATED" if "original" in str(source) else "REFERENCE                 TARGET", fill="black")
    path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(path, quality=88)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--generation-dir", type=Path, required=True)
    parser.add_argument("--generation-format", choices=("v1", "v2"), default="v1")
    parser.add_argument("--reviews", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=ROOT / "data/dataset_v1/final")
    args = parser.parse_args()
    reviews = json.loads(args.reviews.read_text(encoding="utf-8"))
    entries = []
    for original_style, config in SELECTION["styles"].items():
        alternate_style = config["alternate_style"]
        for split in ("train", "val"):
            for filename in config[split]:
                key = f"{original_style}_{Path(filename).stem}"
                entry = reviews.get(key)
                if (not isinstance(entry, dict) or entry.get("status") != "ACCEPT"
                        or entry.get("attempt") not in (1, 2) or not str(entry.get("notes", "")).strip()):
                    raise RuntimeError(f"STOP: explicit ACCEPT, attempt 1/2, and review notes required for {key}; got {entry}")
                if args.generation_format == "v2":
                    folder = args.generation_dir / key
                    original = folder / "source.png"
                    suffix = "_r2" if entry["attempt"] == 2 else ""
                    generated = folder / f"result{suffix}.png"
                    metadata_path = folder / f"generation{suffix}.json"
                else:
                    original = args.generation_dir / "original" / f"{key}.png"
                    generated = args.generation_dir / "generated" / f"{key}{'_r2' if entry['attempt'] == 2 else ''}.png"
                    metadata_path = generated.with_suffix(".json")
                metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
                expected = {"sample_id": key, "source_class": original_style,
                            "requested_class": alternate_style, "source_filename": filename,
                            "split": split, "attempt": entry["attempt"], "model": MODEL,
                            "source_revision": SELECTION["source_revision"],
                            "source_archive_path": f"FaceSketches-HairStyle40/image/{original_style}/{filename}",
                            "width": 512, "height": 512}
                for field, value in expected.items():
                    if metadata.get(field) != value:
                        raise RuntimeError(f"STOP: {key} generation metadata {field}={metadata.get(field)!r}; expected {value!r}")
                if not metadata.get("model_revision") or not metadata.get("generated_utc") or not metadata.get("prompt"):
                    raise RuntimeError(f"STOP: incomplete generation provenance for {key}")
                if metadata.get("source_sha256") != hashlib.sha256(original.read_bytes()).hexdigest():
                    raise RuntimeError(f"STOP: original SHA256 differs from generation metadata for {key}")
                if metadata.get("output_sha256") != hashlib.sha256(generated.read_bytes()).hexdigest():
                    raise RuntimeError(f"STOP: generated SHA256 differs from generation metadata for {key}")
                if args.generation_format == "v2":
                    if (metadata.get("method") != "pilot_v2_masked" or metadata.get("parser_model") != "jonathandinu/face-parsing"
                            or not metadata.get("parser_revision") or metadata.get("pipeline") != "Flux2KleinInpaintPipeline"
                            or metadata.get("outside_mask_pixel_policy") != "copy exact source RGB"):
                        raise RuntimeError(f"STOP: V2 generation provenance incomplete for {key}")
                    for name, field in (("semantic_labels.png", "semantic_sha256"),
                                        ("raw_hair_mask.png", "raw_mask_sha256"),
                                        ("editable_mask.png", "final_mask_sha256")):
                        mask_path = folder / name
                        if metadata.get(field) != hashlib.sha256(mask_path.read_bytes()).hexdigest():
                            raise RuntimeError(f"STOP: V2 mask hash mismatch for {key}: {name}")
                        with Image.open(mask_path) as mask_image:
                            if mask_image.mode != "L" or mask_image.size != (512, 512):
                                raise RuntimeError(f"STOP: invalid V2 mask {mask_path}")
                    with Image.open(original) as src, Image.open(generated) as gen, Image.open(folder / "editable_mask.png") as mask:
                        src_px, gen_px, mask_px = src.convert("RGB").load(), gen.convert("RGB").load(), mask.load()
                        for y in range(512):
                            for x in range(512):
                                if mask_px[x, y] == 0 and src_px[x, y] != gen_px[x, y]:
                                    raise RuntimeError(f"STOP: V2 changed protected pixel in {key} at {(x, y)}")
                for path in (original, generated):
                    with Image.open(path) as image:
                        image.verify()
                    with Image.open(path) as image:
                        if image.mode != "RGB":
                            raise RuntimeError(f"STOP: expected RGB image, found {image.mode} in {path}")
                        rgb = image.convert("RGB")
                        if rgb.size != (512, 512):
                            raise RuntimeError(f"STOP: invalid dimensions {rgb.size} in {path}")
                entries.append((key, original_style, alternate_style, split, original, generated, entry, metadata))
    if len(entries) != 30 or len(reviews) != 30:
        raise RuntimeError("STOP: expected exactly 30 reviewed identity groups")

    groups_by_split = defaultdict(set)
    distribution = Counter()
    seen_hashes = defaultdict(set)
    for key, original_style, alternate_style, split, original, generated, _, _ in entries:
        groups_by_split[split].add(key)
        distribution[(split, original_style)] += 1
        distribution[(split, alternate_style)] += 1
        for role, path in (("original", original), ("generated", generated)):
            seen_hashes[hashlib.sha256(path.read_bytes()).hexdigest()].add((key, role, split))
    if groups_by_split["train"] & groups_by_split["val"]:
        raise RuntimeError("STOP: source identity occurs in both train and validation")
    if len(groups_by_split["train"]) != 24 or len(groups_by_split["val"]) != 6:
        raise RuntimeError("STOP: train/validation identity counts differ from 24/6")
    expected_distribution = Counter({(split, style): count
                                     for split, count in (("train", 16), ("val", 4)) for style in PHRASES})
    if distribution != expected_distribution:
        raise RuntimeError(f"STOP: target class distribution mismatch: {distribution}")
    unexpected_duplicates = [sorted(list(v)) for v in seen_hashes.values() if len(v) > 1]
    if unexpected_duplicates:
        raise RuntimeError(f"STOP: repeated original/generated SHA256 across identity groups or roles: {unexpected_duplicates}")

    # Perform all gates before copying. The final directory must be empty on entry.
    if args.output.exists() and any(args.output.iterdir()):
        raise RuntimeError(f"STOP: final output already exists; inspect it before replacing: {args.output}")
    manifest = []
    identity_rows, pair_rows = [], []
    for key, original_style, alternate_style, split, original, generated, review, metadata in entries:
        attempt = review["attempt"]
        identity_rows.append((original, generated, f"{key} / {split} / {alternate_style} / ACCEPT r{attempt}"))
        metadata_out = args.output / "manifests" / "generation" / f"{key}.json"
        metadata_out.parent.mkdir(parents=True, exist_ok=True)
        metadata_out.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
        for direction, reference, target, requested in (
            ("to_original", generated, original, original_style),
            ("to_alternate", original, generated, alternate_style),
        ):
            stem = f"{key}_{direction}"
            ref_out = args.output / split / "reference" / f"{stem}.png"
            target_out = args.output / split / "target" / f"{stem}.png"
            ref_out.parent.mkdir(parents=True, exist_ok=True)
            target_out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(reference, ref_out)
            shutil.copyfile(target, target_out)
            target_out.with_suffix(".txt").write_text(instruction(requested), encoding="utf-8")
            pair_rows.append((ref_out, target_out, f"{stem} / {split} / {requested}"))
            manifest.append({"identity_group": key, "split": split, "source_class": original_style,
                             "requested_style": requested, "direction": direction, "attempt": attempt,
                             "selected_source": metadata["source_archive_path"],
                             "selection_revision": SELECTION["source_revision"],
                             "generation_metadata": str(metadata_out.relative_to(args.output)),
                             "generation_model": metadata["model"],
                             "generation_model_revision": metadata["model_revision"],
                             "generation_prompt": metadata["prompt"],
                             "generation_seed": metadata["seed"],
                             "generation_output_sha256": metadata["output_sha256"],
                             "review": review,
                             "reference": str(ref_out.relative_to(args.output)),
                             "target": str(target_out.relative_to(args.output)),
                             "caption": instruction(requested).strip()})
    if len(manifest) != 60:
        raise RuntimeError(f"STOP: built {len(manifest)} directional pairs instead of 60")
    for split, expected in (("train", 48), ("val", 12)):
        reference = sorted((args.output / split / "reference").glob("*.png"))
        target = sorted((args.output / split / "target").glob("*.png"))
        captions = sorted((args.output / split / "target").glob("*.txt"))
        if len(reference) != expected or len(target) != expected or len(captions) != expected:
            raise RuntimeError(f"STOP: {split} file counts differ from {expected}")
        if {p.stem for p in reference} != {p.stem for p in target} or {p.stem for p in target} != {p.stem for p in captions}:
            raise RuntimeError(f"STOP: {split} reference/target/caption filenames do not align")
        if any(not caption.read_text(encoding="utf-8").strip() for caption in captions):
            raise RuntimeError(f"STOP: {split} has an empty caption")
    output_manifest = args.output / "manifests" / "pairs.json"
    output_manifest.parent.mkdir(parents=True, exist_ok=True)
    output_manifest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (args.output / "manifests" / "reviews.json").write_text(json.dumps(reviews, indent=2) + "\n", encoding="utf-8")
    (args.output / "manifests" / "selection.json").write_text(json.dumps(SELECTION, indent=2) + "\n", encoding="utf-8")
    sheet(identity_rows, args.output / "contact_sheets" / "identity_generation.jpg")
    sheet(pair_rows, args.output / "contact_sheets" / "all_pairs.jpg")
    report = {"source": SELECTION["source_repository"], "revision": SELECTION["source_revision"],
              "license_declared": SELECTION["source_license_declared"],
              "identity_groups": {k: len(v) for k, v in groups_by_split.items()},
              "directional_pairs": len(manifest),
              "target_class_distribution": {f"{k[0]}/{k[1]}": v for k, v in sorted(distribution.items())},
              "unexpected_duplicate_sha256_groups": unexpected_duplicates,
              "caption_reference_target_alignment": "PASS", "image_open_rgb_dimensions": "PASS",
              "split_leakage": "NONE", "visual_qa": "30 explicit ACCEPT decisions with notes in supplied reviews; manual sheet inspection still required"}
    (args.output / "reports").mkdir(exist_ok=True)
    (args.output / "reports" / "qa.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
