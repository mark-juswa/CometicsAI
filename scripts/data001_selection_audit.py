"""Audit the 90 source photos and the hand-reviewed 30-photo selection."""

from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps


ROOT = Path(__file__).resolve().parents[1]
SELECTION = json.loads((ROOT / "docs/data/DATA-001-selection.json").read_text(encoding="utf-8"))
INPUT = ROOT / "data/dataset_v1/original_candidates"
OUTPUT = ROOT / "docs/data/DATA-001-candidates.json"
SHEETS = ROOT / "data/dataset_v1/contact_sheets"

# Specific reasons for obvious exclusions; other valid images remain reserve candidates.
EXCLUSIONS = {
    "CrewCut": {
        "2.jpg": "Distant event framing; small face and hair",
        "3.jpg": "Strong side angle and monochrome photograph",
        "4.jpg": "Repeated subject also shown in candidate 23.jpg",
        "6.jpg": "Extreme profile view",
        "8.jpg": "Repeated subject also shown in candidate 27.jpg",
        "12.jpg": "Strong three-quarter angle with source watermark",
        "14.jpg": "Colored glasses partially obscure face",
        "19.jpg": "Strong three-quarter angle",
        "22.jpg": "Strong three-quarter angle",
        "29.jpg": "Distant full-body framing; small face and hair",
    },
    "BobHair": {
        "3.jpg": "Visible source watermark across lower portrait",
        "5.jpg": "Profile angle and hand partially occludes portrait",
        "6.jpg": "Side/back view; face not sufficiently visible",
        "7.jpg": "Strong side angle",
        "8.jpg": "Repeated subject also shown in candidate 14.jpg",
        "9.jpg": "Rear view; face not visible",
        "10.jpg": "Longer hair makes bob class less distinct",
        "12.jpg": "Strong side angle",
        "14.jpg": "Repeated subject also shown in candidate 8.jpg",
        "17.jpg": "Sunglasses hide the eyes",
        "18.jpg": "Sunglasses hide the eyes",
        "19.jpg": "Low light and strong shadow across face",
        "21.jpg": "Large source watermark across lower portrait",
        "22.jpg": "Strong side angle",
        "24.jpg": "Eyes obscured by fringe",
        "25.jpg": "Highly retouched portrait; less representative of source photographs",
        "27.PNG": "Dark face and low contrast; identity review more difficult",
    },
    "LayeredHair": {
        "1.jpg": "Strong profile view",
        "5.jpg": "Rear view; face not visible",
        "6.jpg": "Strong side angle",
        "13.jpg": "Shorter hairstyle; layers less visually distinct",
        "16.jpeg": "Distant full-body framing; small face and hair",
        "17.jpg": "Portrait includes another person/partial figure",
        "20.jpg": "Face partly covered by hair and strong profile pose",
        "21.jpg": "Dark source and face partly obscured",
        "26.jpg": "Shorter hairstyle; layers less visually distinct",
        "29.jpg": "Back view; face not visible",
    },
}


def main():
    records = []
    hashes = defaultdict(list)
    selected_thumbs = []
    for style, config in SELECTION["styles"].items():
        files = sorted((INPUT / style).iterdir(), key=lambda p: p.name)
        assert len(files) == 30, (style, len(files))
        chosen = {name: split for split in ("train", "val") for name in config[split]}
        assert len(chosen) == 10 and all((INPUT / style / name).is_file() for name in chosen)
        for path in files:
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            hashes[digest].append(f"{style}/{path.name}")
            with Image.open(path) as original:
                image = ImageOps.exif_transpose(original).convert("RGB")
                width, height = image.size
                if path.name in chosen:
                    thumb = ImageOps.contain(image, (200, 220))
                    selected_thumbs.append((style, path.name, chosen[path.name], thumb))
            records.append({"class": style, "filename": path.name, "source": f"image/{style}/{path.name}",
                            "sha256": digest, "dimensions": [width, height],
                            "decision": "SELECT" if path.name in chosen else "REJECT_FROM_V1",
                            "split": chosen.get(path.name),
                            "reason": "Selected for visible, representative hairstyle and identity variety"
                            if path.name in chosen else EXCLUSIONS.get(style, {}).get(
                                path.name, "Valid reserve candidate; lower relative fit or variety than the chosen ten")})
    collisions = [paths for paths in hashes.values() if len(paths) > 1]
    assert len(records) == 90
    assert Counter(r["decision"] for r in records) == {"SELECT": 30, "REJECT_FROM_V1": 60}
    OUTPUT.write_text(json.dumps({"source": SELECTION["source_repository"],
                                  "revision": SELECTION["source_revision"],
                                  "duplicate_sha256_groups": collisions,
                                  "candidates": records}, indent=2) + "\n", encoding="utf-8")
    sheet = Image.new("RGB", (5 * 212, 6 * 250), "white")
    draw = ImageDraw.Draw(sheet)
    for i, (style, filename, split, thumb) in enumerate(selected_thumbs):
        x, y = (i % 5) * 212, (i // 5) * 250
        sheet.paste(thumb, (x, y))
        draw.text((x, y + 222), f"{style}/{filename} {split}", fill="black")
    SHEETS.mkdir(parents=True, exist_ok=True)
    sheet.save(SHEETS / "selected_originals.jpg", quality=90)
    print("Selected:", dict(Counter(r["class"] for r in records if r["decision"] == "SELECT")))
    print("Excluded from V1:", dict(Counter(r["class"] for r in records if r["decision"] != "SELECT")))
    print("Exact SHA256 duplicate groups:", collisions)
    print("Selected sheet:", SHEETS / "selected_originals.jpg")


if __name__ == "__main__":
    main()
