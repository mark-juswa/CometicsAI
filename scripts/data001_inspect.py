"""Extract only approved original photos and make labeled selection contact sheets."""

from collections import Counter
from io import BytesIO
import json
from pathlib import Path
from zipfile import ZipFile

from PIL import Image, ImageDraw, ImageOps


CLASSES = ("CrewCut", "BobHair", "LayeredHair")
ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "data/source/FaceSketches-HairStyle40.zip"
OUT = ROOT / "data/dataset_v1"
PHOTOS = OUT / "original_candidates"
SHEETS = OUT / "contact_sheets"
THUMB_W, THUMB_H = 180, 220


def main():
    PHOTOS.mkdir(parents=True, exist_ok=True)
    SHEETS.mkdir(parents=True, exist_ok=True)
    records = []
    with ZipFile(ARCHIVE) as archive:
        for style in CLASSES:
            members = sorted(
                (m for m in archive.infolist() if not m.is_dir() and m.filename.startswith(f"FaceSketches-HairStyle40/image/{style}/")),
                key=lambda m: m.filename,
            )
            if len(members) != 30:
                raise ValueError(f"Expected 30 originals for {style}, found {len(members)}")
            cells = []
            for member in members:
                raw = archive.read(member)
                try:
                    with Image.open(BytesIO(raw)) as input_image:
                        image = ImageOps.exif_transpose(input_image).convert("RGB")
                        size = image.size
                        thumb = ImageOps.contain(image, (THUMB_W, THUMB_H))
                except Exception as error:
                    records.append({"style": style, "source": member.filename, "error": str(error)})
                    continue
                path = PHOTOS / style / Path(member.filename).name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
                records.append({"style": style, "source": member.filename, "path": str(path.relative_to(ROOT)), "width": size[0], "height": size[1]})
                cells.append((Path(member.filename).name, thumb))
            width, height = 8 * (THUMB_W + 12), 8 * (THUMB_H + 36)
            sheet = Image.new("RGB", (width, height), "white")
            draw = ImageDraw.Draw(sheet)
            for index, (name, thumb) in enumerate(cells):
                x = (index % 8) * (THUMB_W + 12)
                y = (index // 8) * (THUMB_H + 36)
                sheet.paste(thumb, (x, y))
                draw.text((x + 2, y + THUMB_H + 3), name, fill="black")
            sheet.save(SHEETS / f"candidates_{style}.jpg", quality=88)
    (OUT / "candidate_inventory.json").write_text(json.dumps(records, indent=2), encoding="utf-8")
    print("Valid candidates:", dict(Counter(r["style"] for r in records if "error" not in r)))
    print("Errors:", len([r for r in records if "error" in r]))
    print("Contact sheets:", SHEETS)


if __name__ == "__main__":
    main()
