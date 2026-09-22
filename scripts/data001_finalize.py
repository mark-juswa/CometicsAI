"""Finalize DATA-001 only after 30 explicit visual ACCEPT reviews.

Example: python scripts/data001_finalize.py --generation-dir data/dataset_v1/kaggle \
    --reviews data/dataset_v1/reviews.json
Reviews JSON maps each source key (e.g. CrewCut_1) to {"status":"ACCEPT","attempt":1}.
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
PHRASES = {"CrewCut": "a crew cut", "BobHair": "a bob hairstyle", "LayeredHair": "layered hair"}


def instruction(style):
    return (f"Change the person's hairstyle to {PHRASES[style]} while preserving their identity, "
            "face, expression, pose, clothing, lighting, framing, and background.\n")


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
                if not isinstance(entry, dict) or entry.get("status") != "ACCEPT" or entry.get("attempt") not in (1, 2):
                    raise RuntimeError(f"STOP: explicit ACCEPT and attempt 1/2 required for {key}; got {entry}")
                original = args.generation_dir / "original" / f"{key}.png"
                generated = args.generation_dir / "generated" / f"{key}{'_r2' if entry['attempt'] == 2 else ''}.png"
                metadata = json.loads(generated.with_suffix(".json").read_text(encoding="utf-8"))
                assert metadata["source_class"] == original_style and metadata["requested_class"] == alternate_style
                assert metadata["source_filename"] == filename and metadata["split"] == split
                assert metadata["attempt"] == entry["attempt"]
                for path in (original, generated):
                    with Image.open(path) as image:
                        image.verify()
                    with Image.open(path) as image:
                        rgb = image.convert("RGB")
                        assert rgb.size == (512, 512), (path, rgb.size)
                entries.append((key, original_style, alternate_style, split, original, generated, entry["attempt"]))
    assert len(entries) == 30 and len(reviews) == 30, "Expected exactly 30 reviewed identity groups"

    # Perform all gates before copying. The final directory must be empty on entry.
    if args.output.exists() and any(args.output.iterdir()):
        raise RuntimeError(f"STOP: final output already exists; inspect it before replacing: {args.output}")
    manifest = []
    identity_rows, pair_rows = [], []
    seen_hashes = defaultdict(set)
    groups_by_split = defaultdict(set)
    distribution = Counter()
    for key, original_style, alternate_style, split, original, generated, attempt in entries:
        groups_by_split[split].add(key)
        identity_rows.append((original, generated, f"{key} / {split} / {alternate_style} / ACCEPT r{attempt}"))
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
            distribution[(split, requested)] += 1
            manifest.append({"identity_group": key, "split": split, "source_class": original_style,
                             "requested_style": requested, "direction": direction, "attempt": attempt,
                             "reference": str(ref_out.relative_to(args.output)),
                             "target": str(target_out.relative_to(args.output)),
                             "caption": instruction(requested).strip()})
        for role, path in (("original", original), ("generated", generated)):
            seen_hashes[hashlib.sha256(path.read_bytes()).hexdigest()].add((key, role))
    assert not (groups_by_split["train"] & groups_by_split["val"])
    assert len(groups_by_split["train"]) == 24 and len(groups_by_split["val"]) == 6
    assert len(manifest) == 60 and distribution == Counter({
        (split, style): count for split, count in (("train", 16), ("val", 4)) for style in PHRASES})
    unexpected_duplicates = [sorted(list(v)) for v in seen_hashes.values() if len(v) > 1]
    assert not unexpected_duplicates, unexpected_duplicates
    for split, expected in (("train", 48), ("val", 12)):
        reference = sorted((args.output / split / "reference").glob("*.png"))
        target = sorted((args.output / split / "target").glob("*.png"))
        captions = sorted((args.output / split / "target").glob("*.txt"))
        assert len(reference) == len(target) == len(captions) == expected
        assert {p.stem for p in reference} == {p.stem for p in target} == {p.stem for p in captions}
    output_manifest = args.output / "manifests" / "pairs.json"
    output_manifest.parent.mkdir(parents=True, exist_ok=True)
    output_manifest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    sheet(identity_rows, args.output / "contact_sheets" / "identity_generation.jpg")
    sheet(pair_rows, args.output / "contact_sheets" / "all_pairs.jpg")
    report = {"source": SELECTION["source_repository"], "revision": SELECTION["source_revision"],
              "license_declared": SELECTION["source_license_declared"],
              "identity_groups": {k: len(v) for k, v in groups_by_split.items()},
              "directional_pairs": len(manifest),
              "target_class_distribution": {f"{k[0]}/{k[1]}": v for k, v in sorted(distribution.items())},
              "unexpected_duplicate_sha256_groups": unexpected_duplicates,
              "caption_reference_target_alignment": "PASS", "image_open_rgb_dimensions": "PASS",
              "split_leakage": "NONE", "visual_qa": "30 explicit ACCEPT decisions in supplied reviews; manual sheet inspection still required"}
    (args.output / "reports").mkdir(exist_ok=True)
    (args.output / "reports" / "qa.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
