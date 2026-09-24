"""Manifest-driven planning and reviewed paired-edit finalization for DATA-002+.

This does not generate images. DATA-001's frozen scripts and artifacts stay intact.
"""

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import string

from PIL import Image, ImageDraw, ImageOps


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_manifest(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if (data.get("schema_version") != 1 or not data.get("dataset_id")
            or not data.get("source_revision") or not data.get("base_model_id")
            or not data.get("base_model_revision")):
        raise ValueError("Dataset manifest header is incomplete")
    styles, samples = data.get("styles"), data.get("samples")
    if not isinstance(styles, dict) or len(styles) < 2 or not isinstance(samples, list) or not samples:
        raise ValueError("Dataset manifest requires styles and selected samples")
    if any(not isinstance(record, dict) or not record.get("training_label") or not record.get("prompt_phrase")
           for record in styles.values()):
        raise ValueError("Each style needs a training label and prompt phrase")
    seen, source_members, identity_groups = set(), set(), set()
    for sample in samples:
        source, target = sample.get("source_style"), sample.get("target_style")
        key = sample.get("sample_id")
        member = sample.get("source_member")
        if (not isinstance(key, str) or not key or key in seen or not key.replace("_", "").replace("-", "").isalnum()
                or source not in styles or target not in styles
                or source == target or sample.get("split") not in {"train", "val"}
                or not isinstance(member, str) or not member or member in source_members
                or Path(member).is_absolute() or ".." in Path(member).parts):
            raise ValueError(f"Invalid or duplicate selection: {key}")
        seen.add(key)
        source_members.add(member)
        if data["dataset_id"] == "DATA-002":
            identity = sample.get("identity_group_id")
            digest = sample.get("source_sha256")
            if (sample.get("status") != "selected" or identity != key or identity in identity_groups
                    or not isinstance(digest, str) or len(digest) != 64
                    or any(ch not in string.hexdigits for ch in digest)
                    or not sample.get("source_path") or not sample.get("source_filename")):
                raise ValueError(f"DATA-002 sample provenance is incomplete: {key}")
            identity_groups.add(identity)
    return data


def instruction(styles: dict, style_id: str) -> str:
    return (f"Change the person's hairstyle to {styles[style_id]['prompt_phrase']} while preserving "
            "their identity, facial features, expression, pose, clothing, lighting, framing, and background.")


def distribution(manifest: dict) -> dict[str, int]:
    counts = Counter()
    for sample in manifest["samples"]:
        for style in (sample["source_style"], sample["target_style"]):
            counts[f"{sample['split']}/{style}"] += 1
    return dict(sorted(counts.items()))


def assert_balanced(manifest: dict) -> None:
    counts = distribution(manifest)
    for split in ("train", "val"):
        values = [counts.get(f"{split}/{style}", 0) for style in manifest["styles"]]
        if min(values) == 0 or max(values) - min(values) > 1:
            raise ValueError(f"Unbalanced or missing target class in {split}: {values}")


def plan(manifest: dict, require_balanced: bool = True) -> dict:
    if require_balanced:
        assert_balanced(manifest)
    samples = manifest["samples"]
    return {"dataset_id": manifest["dataset_id"], "source_revision": manifest["source_revision"],
            "identity_counts": dict(sorted(Counter(sample["split"] for sample in samples).items())),
            "pair_counts": {split: 2 * sum(sample["split"] == split for sample in samples)
                            for split in ("train", "val")},
            "target_distribution": distribution(manifest),
            "generation_jobs": [{"sample_id": sample["sample_id"], "source_member": sample["source_member"],
                "source_style": sample["source_style"], "target_style": sample["target_style"],
                "split": sample["split"], "prompt": instruction(manifest["styles"], sample["target_style"]),
                "seed": manifest.get("generation", {}).get("seed", 1977), "attempt": 1}
                for sample in samples]}


def checked_image(path: Path) -> None:
    if not path.is_file() or path.stat().st_size == 0:
        raise ValueError(f"Missing or empty image: {path}")
    with Image.open(path) as image:
        image.verify()
    with Image.open(path) as image:
        if image.mode != "RGB" or image.size != (512, 512):
            raise ValueError(f"Expected 512x512 RGB image: {path}")


def audit_generations(manifest: dict, generation_dir: Path, manifest_digest: str) -> dict:
    """Check each first attempt independently; never infer visual quality."""
    marker = generation_dir.parent / "manifest.sha256"
    if not marker.is_file() or marker.read_text(encoding="utf-8").strip() != manifest_digest:
        raise ValueError(f"Generation directory does not match frozen manifest: {marker}")
    expected_ids = {sample["sample_id"] for sample in manifest["samples"]}
    actual_dirs = {path.name for path in generation_dir.iterdir() if path.is_dir()} if generation_dir.is_dir() else set()
    issues, valid_ids, image_hashes = [], [], defaultdict(list)
    for sample in manifest["samples"]:
        key = sample["sample_id"]
        folder = generation_dir / key
        original, generated, sidecar = folder / "original.png", folder / "generated.png", folder / "generated.json"
        missing = [path.name for path in (original, generated, sidecar) if not path.is_file()]
        if missing:
            issues.append({"sample_id": key, "kind": "missing", "reason": ", ".join(missing)})
            continue
        try:
            if sidecar.stat().st_size == 0:
                raise ValueError("empty generated.json")
            metadata = json.loads(sidecar.read_text(encoding="utf-8"))
            expected = {
                "sample_id": key, "identity_group_id": sample["identity_group_id"],
                "source_path": sample["source_path"], "source_member": sample["source_member"],
                "source_member_sha256": sample["source_sha256"],
                "source_style": sample["source_style"], "target_style": sample["target_style"],
                "split": sample["split"], "attempt": 1,
                "method": manifest["generation"]["method"],
                "prompt": instruction(manifest["styles"], sample["target_style"]),
                "seed": manifest["generation"]["seed"],
                "steps": manifest["generation"]["steps"],
                "guidance": manifest["generation"]["guidance"],
                "width": manifest["generation"]["width"],
                "height": manifest["generation"]["height"],
                "source_revision": manifest["source_revision"],
                "base_model_id": manifest["base_model_id"],
                "base_model_revision": manifest["base_model_revision"],
            }
            differing = [name for name, value in expected.items() if metadata.get(name) != value]
            if differing:
                raise ValueError(f"metadata mismatch: {', '.join(differing)}")
            for role, path in (("original", original), ("generated", generated)):
                checked_image(path)
                digest = sha256(path)
                if metadata.get(f"{role}_sha256") != digest:
                    raise ValueError(f"{role} SHA-256 mismatch")
                image_hashes[digest].append({"sample_id": key, "role": role, "split": sample["split"]})
            if not isinstance(metadata.get("runtime_seconds"), (int, float)) or metadata["runtime_seconds"] <= 0:
                raise ValueError("missing or invalid generation runtime")
            if not metadata.get("generated_utc"):
                raise ValueError("missing generation timestamp")
            valid_ids.append(key)
        except (OSError, ValueError, TypeError, KeyError) as error:
            issues.append({"sample_id": key, "kind": "invalid", "reason": str(error)})
    duplicates = [entries for entries in image_hashes.values() if len(entries) > 1]
    duplicated_ids = {entry["sample_id"] for group in duplicates for entry in group}
    for key in sorted(duplicated_ids):
        issues.append({"sample_id": key, "kind": "duplicate", "reason": "exact image hash appears more than once"})
    valid_ids = [key for key in valid_ids if key not in duplicated_ids]
    valid_set = set(valid_ids)
    valid_manifest = {**manifest, "samples": [s for s in manifest["samples"] if s["sample_id"] in valid_set]}
    actual_distribution = distribution(valid_manifest)
    planned_distribution = distribution(manifest)
    severe = [name for name, expected in planned_distribution.items()
              if actual_distribution.get(name, 0) * 2 < expected]
    train_hashes = {digest for digest, entries in image_hashes.items()
                    if any(entry["split"] == "train" for entry in entries)}
    val_hashes = {digest for digest, entries in image_hashes.items()
                  if any(entry["split"] == "val" for entry in entries)}
    return {
        "dataset_id": manifest["dataset_id"], "manifest_sha256": manifest_digest,
        "review_mode": "automated_unreviewed", "visual_qa": "NOT PERFORMED",
        "expected_generation_jobs": len(manifest["samples"]),
        "actual_generated_png_count": len(list(generation_dir.glob("*/generated.png"))),
        "actual_metadata_json_count": len(list(generation_dir.glob("*/generated.json"))),
        "actual_original_png_count": len(list(generation_dir.glob("*/original.png"))),
        "valid_generation_count": len(valid_ids), "valid_sample_ids": valid_ids,
        "issues": issues, "unexpected_sample_directories": sorted(actual_dirs - expected_ids),
        "duplicate_sha256_groups": duplicates, "exact_hash_split_leakage": bool(train_hashes & val_hashes),
        "actual_identity_counts": dict(sorted(Counter(s["split"] for s in valid_manifest["samples"]).items())),
        "actual_pair_counts": {split: 2 * sum(s["split"] == split for s in valid_manifest["samples"])
                               for split in ("train", "val")},
        "planned_target_distribution": planned_distribution,
        "actual_target_distribution": actual_distribution,
        "severely_underrepresented": severe,
    }


def contact_sheets(rows: list[tuple[Path, Path, str]], folder: Path, stem: str) -> list[str]:
    folder.mkdir(parents=True, exist_ok=True)
    paths = []
    for start in range(0, len(rows), 30):
        page = rows[start:start + 30]
        path = folder / f"{stem}_{start // 30 + 1:03d}.jpg"
        contact_sheet_page(page, path)
        paths.append(str(path.name))
    return paths


def contact_sheet_page(rows: list[tuple[Path, Path, str]], path: Path) -> None:
    width = 512
    sheet = Image.new("RGB", (width, len(rows) * 280), "white")
    draw = ImageDraw.Draw(sheet)
    for index, (reference, target, label) in enumerate(rows):
        for column, source in enumerate((reference, target)):
            with Image.open(source) as image:
                sheet.paste(ImageOps.contain(image, (250, 250)), (column * 256, index * 280))
        draw.text((4, index * 280 + 253), label, fill="black")
    path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(path, quality=90)


def finalize(manifest: dict, generation_dir: Path, reviews_path: Path | None, output: Path,
             review_mode: str = "human_reviewed", manifest_digest: str | None = None) -> dict:
    if review_mode == "automated_unreviewed":
        if manifest["dataset_id"] != "DATA-002" or not manifest_digest:
            raise ValueError("Automated acceptance requires DATA-002 and the approved manifest SHA-256")
        audit = audit_generations(manifest, generation_dir, manifest_digest)
        if audit["unexpected_sample_directories"] or audit["exact_hash_split_leakage"]:
            raise ValueError("Unexpected generation folders or exact-hash split leakage; inspect audit first")
        if audit["severely_underrepresented"] or not audit["valid_sample_ids"]:
            raise ValueError(f"Too few valid examples for automatic finalization: {audit['severely_underrepresented']}")
        valid_set = set(audit["valid_sample_ids"])
        samples = [sample for sample in manifest["samples"] if sample["sample_id"] in valid_set]
        reviews = {sample["sample_id"]: {"status": "TECHNICAL_ACCEPT", "attempt": 1,
                                           "review_mode": review_mode,
                                           "notes": "Passed automated structural checks; visual quality not reviewed"}
                   for sample in samples}
        plan_summary = plan({**manifest, "samples": samples}, require_balanced=False)
    elif review_mode == "human_reviewed":
        if reviews_path is None:
            raise ValueError("Human-reviewed finalization requires --reviews")
        plan_summary = plan(manifest)
        reviews = json.loads(reviews_path.read_text(encoding="utf-8"))
        samples = manifest["samples"]
        audit = None
        if set(reviews) != {sample["sample_id"] for sample in samples}:
            raise ValueError("Review identities do not exactly match selection manifest")
    else:
        raise ValueError(f"Unsupported review mode: {review_mode}")
    if output.exists() and any(output.iterdir()):
        raise ValueError(f"Refusing to replace a nonempty dataset: {output}")
    inputs, hashes = [], defaultdict(set)
    for sample in samples:
        key = sample["sample_id"]
        review = reviews[key]
        required_status = "TECHNICAL_ACCEPT" if review_mode == "automated_unreviewed" else "ACCEPT"
        if (not isinstance(review, dict) or review.get("status") != required_status
                or review.get("attempt") not in (1, 2) or not str(review.get("notes", "")).strip()):
            raise ValueError(f"Explicit ACCEPT and review notes required for {key}")
        folder = generation_dir / key
        suffix = "_r2" if review["attempt"] == 2 else ""
        original, generated = folder / "original.png", folder / f"generated{suffix}.png"
        metadata = json.loads((folder / f"generated{suffix}.json").read_text(encoding="utf-8"))
        expected = {"sample_id": key, "source_member": sample["source_member"],
                    "source_style": sample["source_style"], "target_style": sample["target_style"],
                    "split": sample["split"], "attempt": review["attempt"],
                    "source_revision": manifest["source_revision"],
                    "base_model_id": manifest["base_model_id"],
                    "base_model_revision": manifest["base_model_revision"],
                    "prompt": instruction(manifest["styles"], sample["target_style"]),
                    "width": 512, "height": 512}
        if manifest["dataset_id"] == "DATA-002":
            expected.update({"source_member_sha256": sample["source_sha256"],
                             "seed": manifest["generation"]["seed"] + review["attempt"] - 1,
                             "steps": manifest["generation"]["steps"],
                             "guidance": manifest["generation"]["guidance"],
                             "method": manifest["generation"]["method"]})
        if any(metadata.get(k) != v for k, v in expected.items()):
            raise ValueError(f"Generation metadata differs from selection for {key}")
        if metadata.get("original_sha256") != sha256(original) or metadata.get("generated_sha256") != sha256(generated):
            raise ValueError(f"Image hash differs from generation metadata for {key}")
        for role, image in (("original", original), ("generated", generated)):
            checked_image(image)
            hashes[sha256(image)].add((key, role))
        inputs.append((sample, review, metadata, original, generated))
    duplicates = [sorted(keys) for keys in hashes.values() if len(keys) > 1]
    if duplicates:
        raise ValueError(f"Exact image duplicate across identities: {duplicates}")

    rows, identity_sheet, pair_sheet = [], [], []
    for sample, review, metadata, original, generated in inputs:
        key, split = sample["sample_id"], sample["split"]
        identity_sheet.append((original, generated, f"{key} | {split} | {sample['target_style']}"))
        metadata_out = output / "manifests" / "generation" / f"{key}.json"
        metadata_out.parent.mkdir(parents=True, exist_ok=True)
        metadata_out.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
        for direction, reference, target, requested in (
                ("to_alternate", original, generated, sample["target_style"]),
                ("to_original", generated, original, sample["source_style"])):
            stem = f"{key}_{direction}"
            ref_path = output / split / "reference" / f"{stem}.png"
            target_path = output / split / "target" / f"{stem}.png"
            ref_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(reference, ref_path)
            shutil.copyfile(target, target_path)
            caption = instruction(manifest["styles"], requested)
            target_path.with_suffix(".txt").write_text(caption + "\n", encoding="utf-8")
            rows.append({"sample_id": key, "split": split, "source_style": sample["source_style"],
                         "requested_style": requested, "direction": direction, "review": review,
                         "source_member": sample["source_member"],
                         "generation_metadata": str(metadata_out.relative_to(output)),
                         "reference": str(ref_path.relative_to(output)),
                         "target": str(target_path.relative_to(output)), "caption": caption})
            pair_sheet.append((ref_path, target_path, f"{stem} | {split} | {requested}"))
    for split in ("train", "val"):
        count = plan_summary["pair_counts"][split]
        references = list((output / split / "reference").glob("*.png"))
        targets = list((output / split / "target").glob("*.png"))
        captions = list((output / split / "target").glob("*.txt"))
        if not len(references) == len(targets) == len(captions) == count:
            raise ValueError(f"Unexpected {split} file counts")
        if {p.stem for p in references} != {p.stem for p in targets} or {p.stem for p in targets} != {p.stem for p in captions}:
            raise ValueError(f"Reference, target and caption names differ in {split}")
    actual = Counter(f"{row['split']}/{row['requested_style']}" for row in rows)
    if dict(sorted(actual.items())) != plan_summary["target_distribution"]:
        raise ValueError("Target class distribution differs from manifest plan")
    train_ids = {row["sample_id"] for row in rows if row["split"] == "train"}
    val_ids = {row["sample_id"] for row in rows if row["split"] == "val"}
    if train_ids & val_ids:
        raise ValueError("Identity leakage across splits")
    (output / "manifests" / "pairs.json").write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
    (output / "manifests" / "selection.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (output / "manifests" / "reviews.json").write_text(json.dumps(reviews, indent=2) + "\n", encoding="utf-8")
    if audit is not None:
        audit_path = output / "reports" / "generation_audit.json"
        audit_path.parent.mkdir(parents=True, exist_ok=True)
        audit_path.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    identity_pages = contact_sheets(identity_sheet, output / "contact_sheets", "identity_generation")
    pair_pages = contact_sheets(pair_sheet, output / "contact_sheets", "directional_pairs")
    report = {"dataset_id": manifest["dataset_id"], "created_utc": datetime.now(timezone.utc).isoformat(),
              "source_manifest_sha256": manifest_digest, "review_mode": review_mode,
              "identity_counts": plan_summary["identity_counts"], "pair_counts": plan_summary["pair_counts"],
              "target_distribution": dict(sorted(actual.items())), "duplicate_identity_hashes": [],
              "split_leakage": False,
              "explicit_accepts": len(reviews) if review_mode == "human_reviewed" else 0,
              "automated_accepts": len(reviews) if review_mode == "automated_unreviewed" else 0,
              "excluded_generations": audit["issues"] if audit is not None else [],
              "contact_sheets": identity_pages + pair_pages,
              "visual_qa": ("NOT PERFORMED; automated structural acceptance only" if audit is not None
                            else "Explicit human decisions recorded; contact sheets require review")}
    report_path = output / "reports" / "qa.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("plan", "audit", "finalize"))
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--generation-dir", type=Path)
    parser.add_argument("--reviews", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--review-mode", choices=("human_reviewed", "automated_unreviewed"),
                        default="human_reviewed")
    parser.add_argument("--approved-manifest-sha256")
    args = parser.parse_args()
    manifest = load_manifest(args.manifest)
    if args.mode == "plan":
        print(json.dumps(plan(manifest), indent=2))
    elif args.mode == "audit":
        if not args.generation_dir or not args.approved_manifest_sha256:
            parser.error("audit requires --generation-dir and --approved-manifest-sha256")
        if sha256(args.manifest) != args.approved_manifest_sha256:
            raise ValueError("Frozen manifest hash differs from approved SHA-256")
        audit = audit_generations(manifest, args.generation_dir, args.approved_manifest_sha256)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(audit, indent=2))
    else:
        if not args.generation_dir or not args.output:
            parser.error("finalize requires --generation-dir and --output")
        if args.review_mode == "automated_unreviewed" and (
                not args.approved_manifest_sha256 or sha256(args.manifest) != args.approved_manifest_sha256):
            raise ValueError("Automated finalization requires the approved frozen manifest SHA-256")
        print(json.dumps(finalize(manifest, args.generation_dir, args.reviews, args.output,
                                  args.review_mode, args.approved_manifest_sha256), indent=2))


if __name__ == "__main__":
    main()
