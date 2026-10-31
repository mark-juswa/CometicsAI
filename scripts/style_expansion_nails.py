"""STYLE-EXP-001 renderer experiment. Never imported by production routes."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from app.nails.geometry import nail_components

STYLES = ("exp_raspberry_jelly", "exp_pink_aura", "exp_negative_space_microdots")


def render(source, mask_image, style_id):
    if style_id not in STYLES:
        raise ValueError("Unsupported experimental nail style")
    source = source.convert("RGB")
    if mask_image.size != source.size:
        raise ValueError("Mask dimensions differ")
    original = np.asarray(source)
    mask = np.asarray(mask_image.convert("L")) > 127
    components = nail_components(mask)
    if not 3 <= len(components) <= 5 or mask.sum() > mask.size * .12:
        raise ValueError("Use a reviewed mask with three to five separate nails")
    output = original.copy()
    edge = np.asarray(mask_image.convert("L").filter(ImageFilter.GaussianBlur(.8))) / 255.
    for component in components:
        yy, xx = component[:, 0], component[:, 1]
        coordinates = np.stack((xx, yy), axis=1).astype(float)
        centered = coordinates - coordinates.mean(axis=0)
        _, axes = np.linalg.eigh(centered.T @ centered)
        projected = centered @ axes
        extent = np.ptp(projected, axis=0)
        if np.any(extent < 2):
            raise ValueError("Degenerate nail component")
        uv = (projected - projected.min(axis=0)) / extent
        pixels = original[yy, xx].astype(float)
        luminance = pixels @ np.array([.2126, .7152, .0722])
        shade = np.clip((luminance - np.median(luminance)) * .55, -30, 40)[:, None]
        if style_id == "exp_raspberry_jelly":
            # A translucent tint preserves photographed nail detail.
            painted = np.clip(np.array([163, 28, 77]) + shade, 0, 255)
            alpha = (edge[yy, xx] * .48)[:, None]
        elif style_id == "exp_pink_aura":
            glow = np.exp(-(((uv[:, 0] - .5) / .32) ** 2 +
                            ((uv[:, 1] - .5) / .34) ** 2))[:, None]
            painted = np.clip(np.array([239, 193, 207]) * (1 - glow) +
                              np.array([205, 52, 122]) * glow + shade, 0, 255)
            alpha = (edge[yy, xx] * .88)[:, None]
        else:
            painted = pixels * .8 + np.array([236, 196, 208]) * .2
            dots = np.zeros(len(uv), dtype=bool)
            # Distances use physical pixels so dots remain round on long nails.
            for u, v in ((.35, .25), (.65, .50), (.40, .75)):
                distance = (uv - [u, v]) * extent
                dots |= (distance ** 2).sum(axis=1) <= (min(extent) * .065) ** 2
            painted[dots] = [74, 32, 57]
            alpha = (edge[yy, xx] * .95)[:, None]
        output[yy, xx] = np.clip(pixels * (1 - alpha) + painted * alpha, 0, 255).astype("uint8")
    if not np.array_equal(output[~mask], original[~mask]):
        raise RuntimeError("Experimental renderer changed pixels outside the mask")
    return Image.fromarray(output)


def run_suite(source_path, mask_path, output):
    source_path, mask_path, output = map(Path, (source_path, mask_path, output))
    if output.exists():
        raise ValueError("Use a new result folder; earlier evidence is preserved")
    with Image.open(source_path) as opened:
        source = opened.convert("RGB")
    with Image.open(mask_path) as opened:
        mask = opened.convert("L")
    output.mkdir(parents=True)
    source.save(output / "source.png")
    mask.save(output / "mask.png")
    report = {"status": "REQUIRES_VISUAL_REVIEW", "scope": "Reviewed-mask renderer ceiling only",
              "source_sha256": sha256(source_path.read_bytes()).hexdigest(),
              "mask_sha256": sha256(mask_path.read_bytes()).hexdigest(),
              "segmentation_tested": False, "trained_model": False, "production_enabled": False,
              "cases": [], "limitations": [
                  "One reused validation hand; no new dataset or generalization claim.",
                  "Manual mask bypasses live segmentation. Real upload/mask acceptance remains required.",
                  "Elapsed time measures this renderer only, not application latency."]}
    sheet = Image.new("RGB", (4 * 320, 280), "white")
    drawing = ImageDraw.Draw(sheet)
    sheet.paste(source.resize((320, 240)), (0, 40))
    drawing.text((10, 10), "Original (reused validation hand)", fill="black")
    for index, style in enumerate(STYLES, 1):
        begin = time.perf_counter()
        result = render(source, mask, style)
        elapsed = time.perf_counter() - begin
        path = output / (style + ".png")
        result.save(path)
        before, after = np.asarray(source), np.asarray(result)
        binary = np.asarray(mask) > 127
        edits = [int(np.any(before[c[:, 0], c[:, 1]] != after[c[:, 0], c[:, 1]], axis=1).sum())
                 for c in nail_components(binary)]
        row = {"candidate_id": style, "output": path.name, "renderer_seconds": elapsed,
               "rgb_sha256": sha256(result.tobytes()).hexdigest(),
               "png_sha256": sha256(path.read_bytes()).hexdigest(),
               "changed_outside_mask_pixels": int(np.any(before != after, axis=2)[~binary].sum()),
               "changed_pixels_per_component": edits, "visual_verdict": "NEEDS_REVIEW"}
        if row["changed_outside_mask_pixels"] or not all(edits):
            raise RuntimeError("Nail preservation/edit coverage check failed")
        report["cases"].append(row)
        sheet.paste(result.resize((320, 240)), (index * 320, 40))
        drawing.text((index * 320 + 8, 10), style.removeprefix("exp_"), fill="black")
    sheet.save(output / "comparison.jpg", quality=92)
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--mask", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run_suite(args.source, args.mask, args.output)))
