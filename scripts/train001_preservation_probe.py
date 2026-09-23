"""CPU-only diagnostic: keep original pixels outside the parsed hair edit region.

Uses the already generated TRAIN-001 validation images. It neither runs FLUX
nor changes DATA-001, checkpoints, reviews, or the existing evaluation.
"""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys


REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "notebooks"))
from data001_pilot_v2_masked_kaggle import PARSER, PARSER_REV, make_mask  # noqa: E402


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def image_rgb(path):
    from PIL import Image

    with Image.open(path) as image:
        if image.size != (512, 512):
            raise RuntimeError(f"STOP: expected 512x512 image: {path}")
        return image.convert("RGB")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--training-out", type=Path, required=True)
    args = parser.parse_args()

    summary = json.loads((args.training_out / "training_summary.json").read_text(encoding="utf-8"))
    if summary.get("success") is not True or summary.get("highest_loss_step") != 250:
        raise RuntimeError("STOP: completed TRAIN-001 summary required")
    evaluation = args.training_out / "evaluation"
    metadata = json.loads((evaluation / "metadata.json").read_text(encoding="utf-8"))
    if metadata.get("column_order") != ["reference", "base_output", "adapter_output", "target"]:
        raise RuntimeError("STOP: unknown evaluation sheet contract")
    adapter_rows = metadata.get("pairs", {}).get("adapter", [])
    rows = [r for r in json.loads((args.dataset / "manifests" / "pairs.json").read_text(encoding="utf-8"))
            if r["split"] == "val"]
    if len(rows) != 12 or len(adapter_rows) != 12:
        raise RuntimeError("STOP: expected 12 validation directions and adapter outputs")
    if {Path(r["target"]).stem for r in rows} != {r["pair"] for r in adapter_rows}:
        raise RuntimeError("STOP: adapter outputs do not match validation manifest")
    adapter_evidence = {r["pair"]: r for r in adapter_rows}

    out = evaluation / "preservation_probe"
    if out.exists() and any(out.iterdir()):
        raise RuntimeError(f"STOP: refusing to overwrite existing probe: {out}")
    out.mkdir(parents=True, exist_ok=True)

    import torch
    from PIL import Image, ImageDraw, ImageOps
    from transformers import SegformerForSemanticSegmentation, SegformerImageProcessor

    cache = "/tmp/hf-cache/hub"
    processor = SegformerImageProcessor.from_pretrained(PARSER, revision=PARSER_REV, cache_dir=cache)
    model = SegformerForSemanticSegmentation.from_pretrained(
        PARSER, revision=PARSER_REV, use_safetensors=True, cache_dir=cache
    ).eval()
    sheet = Image.new("RGB", (5 * 256, len(rows) * 286), "white")
    draw = ImageDraw.Draw(sheet)
    records = []
    for index, row in enumerate(rows):
        stem = Path(row["target"]).stem
        source_path = args.dataset / row["reference"]
        target_path = args.dataset / row["target"]
        adapter_path = evaluation / "adapter" / f"{stem}.png"
        if digest(adapter_path) != adapter_evidence[stem]["output_sha256"]:
            raise RuntimeError(f"STOP: adapter output hash changed: {adapter_path}")
        source, target, adapter = [image_rgb(path) for path in (source_path, target_path, adapter_path)]
        semantic, raw, mask, mask_metrics = make_mask(source, processor, model, torch)
        # White mask pixels take the trained LoRA output; black pixels stay
        # exactly equal to the source, including central face and background.
        preserved = Image.composite(adapter, source, mask)
        folder = out / stem
        folder.mkdir()
        for name, image in (("semantic.png", semantic), ("raw_hair_mask.png", raw),
                            ("edit_mask.png", mask), ("preserved.png", preserved)):
            image.save(folder / name)
        for column, image in enumerate((source, adapter, mask.convert("RGB"), preserved, target)):
            sheet.paste(ImageOps.contain(image, (256, 256)), (column * 256, index * 286))
        draw.text((5, index * 286 + 260), f"{stem} → {row['requested_style']} | PENDING REVIEW", fill="black")
        records.append({"pair": stem, "identity_group": row["identity_group"],
                        "requested_style": row["requested_style"], "source": str(source_path),
                        "source_sha256": digest(source_path), "adapter_output": str(adapter_path),
                        "adapter_sha256": digest(adapter_path), "mask": str(folder / "edit_mask.png"),
                        "mask_sha256": digest(folder / "edit_mask.png"),
                        "preserved_output": str(folder / "preserved.png"),
                        "preserved_sha256": digest(folder / "preserved.png"),
                        "mask_metrics": mask_metrics, "review_status": "PENDING"})
        print(f"{index + 1}/12 {stem}: editable={mask_metrics['editable_pixels']} pixels", flush=True)
    sheet_path = out / "source_global_mask_preserved_target.jpg"
    sheet.save(sheet_path, quality=92)
    (out / "metadata.json").write_text(json.dumps({"method": "hair_region_composite_probe",
        "parser": PARSER, "parser_revision": PARSER_REV,
        "source_evaluation_sha256": digest(evaluation / "metadata.json"),
        "column_order": ["source", "global_adapter", "edit_mask", "hair_only_composite", "target"],
        "created_utc": datetime.now(timezone.utc).isoformat(), "rows": records}, indent=2) + "\n",
        encoding="utf-8")
    print(f"PROBE READY: {sheet_path}", flush=True)
    print("No output is accepted or integrated automatically.", flush=True)


if __name__ == "__main__":
    main()
