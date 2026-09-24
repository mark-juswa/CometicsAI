"""Inspect real source photographs without extracting the full source ZIP."""

import argparse
from collections import Counter
from io import BytesIO
import json
from pathlib import Path, PurePosixPath
from zipfile import ZipFile

from PIL import Image, ImageDraw, ImageOps


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CLASSES = (
    "CurtainedHair", "undercutSidepart", "Fauxhawk", "UndercutPompadour",
    "PonyTail", "PixieCut", "ShoulderLenHair", "WaveHair", "shag", "Bun",
)


def original_members(archive: ZipFile) -> dict[str, list[str]]:
    members = {}
    for info in archive.infolist():
        parts = PurePosixPath(info.filename.replace("\\", "/")).parts
        if (info.is_dir() or "image" not in parts or "__MACOSX" in parts
                or parts[-1].startswith("._") or not parts[-1].lower().endswith((".jpg", ".jpeg", ".png"))):
            continue
        index = parts.index("image")
        if len(parts) == index + 3:
            members.setdefault(parts[index + 1], []).append(info.filename)
    return {key: sorted(value) for key, value in members.items()}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, default=ROOT / "data/source/FaceSketches-HairStyle40.zip")
    parser.add_argument("--output", type=Path, default=ROOT / "docs/data/DATA-002-audit")
    parser.add_argument("--classes", nargs="+", default=list(DEFAULT_CLASSES))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    records = []
    with ZipFile(args.archive) as archive:
        inventory = original_members(archive)
        missing = set(args.classes) - set(inventory)
        if missing:
            raise RuntimeError(f"Source classes missing: {sorted(missing)}")
        for style in args.classes:
            files = inventory[style]
            sheet = Image.new("RGB", (6 * 160, ((len(files) + 5) // 6) * 168), "white")
            draw = ImageDraw.Draw(sheet)
            for index, member in enumerate(files):
                col, row = index % 6, index // 6
                try:
                    with Image.open(BytesIO(archive.read(member))) as image:
                        image.load()
                        normalized = ImageOps.exif_transpose(image).convert("RGB")
                    width, height = normalized.size
                    thumb = ImageOps.contain(normalized, (150, 139))
                    sheet.paste(thumb, (col * 160 + (150 - thumb.width) // 2, row * 168))
                    error = None
                except (OSError, ValueError) as exc:
                    width = height = 0
                    error = f"{type(exc).__name__}: {exc}"
                    draw.rectangle((col * 160, row * 168, col * 160 + 150, row * 168 + 139), fill="#f4cccc")
                    draw.text((col * 160 + 5, row * 168 + 10), "DECODE ERROR", fill="black")
                draw.text((col * 160 + 3, row * 168 + 140), f"{Path(member).name} {width}x{height}", fill="black")
                records.append({"class": style, "member": member, "filename": Path(member).name,
                                "width": width, "height": height, "short_side": min(width, height),
                                "decode_error": error})
            sheet.save(args.output / f"{style}.jpg", quality=88)
    (args.output / "inventory.json").write_text(json.dumps({"source_archive": str(args.archive),
        "source_revision": "45de974926fe64551fc2d0b80973335e20ca10e2",
        "class_counts": dict(sorted(Counter(row["class"] for row in records).items())),
        "candidates": records}, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"classes": len(args.classes), "candidate_counts": dict(sorted(Counter(row["class"] for row in records).items())),
                      "contact_sheets": str(args.output)}, indent=2))


if __name__ == "__main__":
    main()
