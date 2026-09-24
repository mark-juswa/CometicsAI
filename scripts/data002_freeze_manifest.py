"""Freeze manually curated DATA-002 source identities into one generation contract.

This is local source inspection only. It neither extracts the archive nor runs FLUX.
The generated manifest, not this helper, is authoritative for later stages.
"""

import hashlib
from io import BytesIO
import json
from pathlib import Path
from zipfile import ZipFile

from PIL import Image, ImageDraw, ImageOps

from data002_source_audit import original_members
from paired_dataset import load_manifest, plan


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "data/source/FaceSketches-HairStyle40.zip"
CURATION = ROOT / "docs/data/DATA-002-curation.json"
MANIFEST = ROOT / "docs/data/DATA-002-manifest.json"
HASH_FILE = ROOT / "docs/data/DATA-002-manifest.sha256"
SHEETS = ROOT / "docs/data/DATA-002-selection-sheets"
SOURCE_REVISION = "45de974926fe64551fc2d0b80973335e20ca10e2"
BASE_REVISION = "a3b4f4849157f664bdbc776fd7453c2783562f4d"

STYLE_DEFINITIONS = {
    "Afro": ("afro", "an afro hairstyle"),
    "BowlCut": ("bowl_cut", "a bowl cut"),
    "Bun": ("bun", "a hair bun"),
    "CornRows": ("cornrows", "cornrows"),
    "DreadLocks": ("dreadlocks", "dreadlocks"),
    "HiTopFade": ("hi_top_fade", "a high-top fade"),
    "PixieCut": ("pixie_cut", "a pixie cut"),
    "PonyTail": ("ponytail", "a ponytail"),
    "SpikyHair": ("spiky_hair", "spiky hair"),
    "WaistLenHair": ("waist_length_hair", "waist-length hair"),
}

# Two edge-disjoint directed cycles: every class has two source relationships
# and two target relationships, with both modest and stronger edits.
PAIR_CYCLES = (
    ("BowlCut", "PixieCut", "Bun", "PonyTail", "WaistLenHair",
     "DreadLocks", "CornRows", "Afro", "HiTopFade", "SpikyHair"),
    ("BowlCut", "Afro", "CornRows", "DreadLocks", "WaistLenHair",
     "PonyTail", "Bun", "PixieCut", "SpikyHair", "HiTopFade"),
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def target_map() -> dict[str, list[str]]:
    targets = {name: [] for name in STYLE_DEFINITIONS}
    for cycle in PAIR_CYCLES:
        if set(cycle) != set(targets) or len(cycle) != len(targets):
            raise ValueError("Each pairing cycle must cover every selected class once")
        for index, source in enumerate(cycle):
            targets[source].append(cycle[(index + 1) % len(cycle)])
    if any(len(set(values)) != 2 for values in targets.values()):
        raise ValueError("A class has a repeated target")
    if any(sum(style in values for values in targets.values()) != 2 for style in targets):
        raise ValueError("Pairing graph is not target-balanced")
    return targets


def source_image(archive: ZipFile, member: str) -> tuple[bytes, Image.Image]:
    payload = archive.read(member)
    with Image.open(BytesIO(payload)) as image:
        image.load()
        photo = ImageOps.exif_transpose(image).convert("RGB")
    if min(photo.size) < 256:
        raise ValueError(f"Source too small: {member}: {photo.size}")
    return payload, photo


def difference_hash(photo: Image.Image) -> int:
    values = list(ImageOps.grayscale(ImageOps.fit(photo, (9, 8))).getdata())
    return sum((values[row * 9 + col] > values[row * 9 + col + 1]) << (row * 8 + col)
               for row in range(8) for col in range(8))


def build() -> tuple[dict, dict, dict[str, list[tuple[dict, Image.Image]]]]:
    curation = json.loads(CURATION.read_text(encoding="utf-8"))
    if set(curation["classes"]) != set(STYLE_DEFINITIONS):
        raise ValueError("Curated class set differs from frozen definitions")
    targets = target_map()
    styles = {style_id: {"training_label": label, "prompt_phrase": phrase}
              for label, (style_id, phrase) in STYLE_DEFINITIONS.items()}
    samples, seen_hashes, sheets, ledger, perceptual = [], {}, {}, {}, []
    archive_hash = file_sha256(ARCHIVE)
    with ZipFile(ARCHIVE) as archive:
        inventory = original_members(archive)
        for label, (style_id, _) in STYLE_DEFINITIONS.items():
            record = curation["classes"][label]
            chosen = record["train"] + record["val"]
            reserve = record["reserve"]
            if (len(record["train"]) < 8 or len(record["val"]) < 2
                    or len(set(chosen + reserve)) != len(chosen + reserve)):
                raise ValueError(f"Selection count or duplicate file error: {label}")
            available = {Path(path).name: path for path in inventory[label]}
            if not set(chosen + reserve) <= set(available):
                raise ValueError(f"Missing selected/reserve source file: {label}")
            ledger[label] = {"selected_train": len(record["train"]),
                             "selected_val": len(record["val"]), "reserve": len(reserve),
                             "rejected": len(available) - len(chosen) - len(reserve),
                             "reserve_files": reserve,
                             "rejected_files": sorted(set(available) - set(chosen) - set(reserve)),
                             "rejection_notes": record["rejection_notes"]}
            sheets[label] = []
            for split, filenames in (("train", record["train"]), ("val", record["val"])):
                for index, filename in enumerate(filenames):
                    member = available[filename]
                    payload, photo = source_image(archive, member)
                    source_hash = sha256_bytes(payload)
                    if source_hash in seen_hashes:
                        raise ValueError(f"Exact duplicate source file: {member} and {seen_hashes[source_hash]}")
                    seen_hashes[source_hash] = member
                    target_label = targets[label][index % 2]
                    sample_id = f"d2_{style_id}_{filename.replace('.', '').lower()}"
                    sample = {"sample_id": sample_id, "identity_group_id": sample_id,
                              "source_style": style_id,
                              "target_style": STYLE_DEFINITIONS[target_label][0],
                              "split": split, "status": "selected",
                              "source_filename": filename,
                              "source_path": f"data/source/FaceSketches-HairStyle40.zip!{member}",
                              "source_member": member, "source_sha256": source_hash,
                              "source_width": photo.width, "source_height": photo.height}
                    samples.append(sample)
                    sheets[label].append((sample, photo))
                    perceptual.append((sample_id, split, difference_hash(photo)))
    manifest = {
        "schema_version": 1, "dataset_id": "DATA-002", "status": "FROZEN_FOR_PROJECT_LEAD_REVIEW",
        "source_repository": "yikaiwang/FaceSketches-HairStyle40",
        "source_revision": SOURCE_REVISION,
        "source_license_declared": "apache-2.0",
        "source_archive_filename": ARCHIVE.name,
        "source_archive_sha256": archive_hash,
        "base_model_id": "black-forest-labs/FLUX.2-klein-base-4B",
        "base_model_revision": BASE_REVISION,
        "generation": {"method": "v1_global", "width": 512, "height": 512,
                       "steps": 20, "guidance": 4.0, "seed": 1977,
                       "precision": "float16", "cpu_offload": True,
                       "retry_policy": "REGENERATE review permits one seed-only retry at seed+1"},
        "styles": styles, "samples": samples,
    }
    summary = plan(manifest)
    if (len(samples) != sum(len(value["train"]) + len(value["val"])
                            for value in curation["classes"].values())
            or any(summary["pair_counts"][split] != 2 * summary["identity_counts"][split]
                   for split in ("train", "val"))
            or len({s["identity_group_id"] for s in samples}) != len(samples)):
        raise ValueError("Selection/pairing did not meet calculated balance")
    near_matches = [
        {"a": left[0], "a_split": left[1], "b": right[0], "b_split": right[1],
         "difference_hash_distance": (left[2] ^ right[2]).bit_count()}
        for index, left in enumerate(perceptual) for right in perceptual[index + 1:]
        if (left[2] ^ right[2]).bit_count() <= 4
    ]
    return manifest, ledger, sheets, near_matches


def write_sheets(sheets: dict[str, list[tuple[dict, Image.Image]]]) -> None:
    SHEETS.mkdir(parents=True, exist_ok=True)
    for label, entries in sheets.items():
        sheet = Image.new("RGB", (4 * 260, ((len(entries) + 3) // 4) * 285), "white")
        draw = ImageDraw.Draw(sheet)
        for index, (sample, photo) in enumerate(entries):
            x, y = (index % 4) * 260, (index // 4) * 285
            thumb = ImageOps.contain(photo, (250, 250))
            sheet.paste(thumb, (x + (250 - thumb.width) // 2, y))
            draw.text((x + 4, y + 252), f"{sample['source_filename']} {sample['split']} -> {sample['target_style']}", fill="black")
        sheet.save(SHEETS / f"{label}.jpg", quality=90)


def main() -> None:
    manifest, ledger, sheets, near_matches = build()
    encoded = (json.dumps(manifest, indent=2) + "\n").encode("utf-8")
    digest = sha256_bytes(encoded)
    if MANIFEST.exists() and MANIFEST.read_bytes() != encoded:
        raise RuntimeError("Frozen manifest differs from curation; refusing overwrite")
    if HASH_FILE.exists() and HASH_FILE.read_text(encoding="utf-8").strip() != digest:
        raise RuntimeError("Frozen manifest checksum differs; refusing overwrite")
    MANIFEST.write_bytes(encoded)
    HASH_FILE.write_text(digest + "\n", encoding="utf-8")
    verified = load_manifest(MANIFEST)
    summary = plan(verified)
    write_sheets(sheets)
    report = {"status": manifest["status"], "manifest_sha256": digest,
              "source_archive_sha256": manifest["source_archive_sha256"],
              "selected_classes": list(STYLE_DEFINITIONS),
              "candidate_decisions": ledger,
              "identity_counts": summary["identity_counts"],
              "generation_jobs": len(summary["generation_jobs"]),
              "pair_counts": summary["pair_counts"],
              "target_distribution": summary["target_distribution"],
              "near_image_hash_matches_for_review": near_matches,
              "identity_uniqueness": "Manual contact-sheet screening plus exact source SHA-256; semantic identity duplicates cannot be ruled out automatically"}
    (ROOT / "docs/data/DATA-002-selection-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"manifest": str(MANIFEST), "sha256": digest,
                      "identity_counts": summary["identity_counts"],
                      "generation_jobs": len(summary["generation_jobs"]),
                      "pair_counts": summary["pair_counts"]}, indent=2))


if __name__ == "__main__":
    main()
