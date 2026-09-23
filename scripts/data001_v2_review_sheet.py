"""Render DATA-001 V2 human-review evidence; never assigns ACCEPT status."""

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--generation-dir", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    selection = json.loads((Path(__file__).resolve().parents[1] / "docs/data/DATA-001-selection.json").read_text(encoding="utf-8"))
    rows = []
    for source_class, entry in selection["styles"].items():
        for split in ("train", "val"):
            for filename in entry[split]:
                sample = f"{source_class}_{Path(filename).stem}"
                folder = args.generation_dir / sample
                paths = [folder / name for name in ("source.png", "raw_hair_mask.png", "editable_mask.png", "result.png")]
                if all(path.is_file() for path in paths):
                    rows.append((sample, source_class, entry["alternate_style"], split, paths))
    if not rows:
        raise RuntimeError("STOP: no complete V2 output folders found")
    side = 240
    sheet = Image.new("RGB", (4 * side, len(rows) * 280 + 25), "white")
    draw = ImageDraw.Draw(sheet)
    for col, label in enumerate(("SOURCE", "RAW HAIR", "FINAL EDIT MASK", "RESULT")):
        draw.text((col * side + 3, 4), label, fill="black")
    for i, (sample, source_class, target, split, paths) in enumerate(rows):
        top = 25 + i * 280
        for col, path in enumerate(paths):
            with Image.open(path) as image:
                sheet.paste(ImageOps.contain(image.convert("RGB"), (side, side)), (col * side, top))
        draw.text((3, top + 245), f"{sample}: {source_class} -> {target} / {split} / PENDING HUMAN REVIEW", fill="black")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(args.output, quality=91)
    print(f"Review sheet: {args.output}; complete samples shown: {len(rows)}/30")


if __name__ == "__main__":
    main()
