"""Offline automatic-mask validation for three experimental Nail renderers."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys
import time
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "backend")]


def run(output, root=ROOT):
    import numpy as np
    from PIL import Image, ImageChops, ImageDraw, ImageOps
    from app.nails.geometry import MediaPipeHandLocalizer, NailCrop, composite_nails, nail_components, validate_nail_mask
    from app.nails.segmentation import IsolatedYoloNailSegmenter
    from app.nails.hybrid import normalized_hand, _to_original, _to_normalized_mask
    from scripts.style_expansion_nails import render, STYLES
    from zipfile import ZipFile
    output = Path(output)
    if output.exists():
        raise ValueError("New evidence folder required")
    output.mkdir(parents=True)
    report = {"status": "IN_PROGRESS", "production_enabled": False, "segmentation_tested": True,
              "trained_model": False, "scope": "Four reused historical validation hands; automatic pipeline, not new final test.",
              "inputs": [], "cases": [], "failures": []}
    def save():
        (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    save()
    try:
        selection_path = root / "data/nails/work/source-frozen-v4/source_selection.json"
        selection = json.loads(selection_path.read_text(encoding="utf-8"))
        source_archive = root / "data/nails/source/11k-hands/Hands-original.zip"
        checkpoint = root / "data/nails/checkpoints/mnemic/nails_seg_s_yolov8_v1.pt"
        landmark = root / "data/nails/checkpoints/mediapipe/hand_landmarker.task"
        if sha256(checkpoint.read_bytes()).hexdigest() != "99b7d1c6ceb4bde32d80fe7ae8c8eb809c27d99b55cf9db54b6692afe68f4070":
            raise ValueError("Segmentation checkpoint differs")
        report["assets"] = {"selection_sha256": sha256(selection_path.read_bytes()).hexdigest(),
                            "segmenter_sha256": sha256(checkpoint.read_bytes()).hexdigest(),
                            "landmarker_sha256": sha256(landmark.read_bytes()).hexdigest()}
        localizer = MediaPipeHandLocalizer(landmark)
        segmenter = IsolatedYoloNailSegmenter(
            root / "data/nails/work/seg-venv/Scripts/python.exe", checkpoint, root / "scripts/nails_segment_once.py")
        rows = [r for r in selection["candidates"] if r["split"] == "validation" and r["selection_status"] == "ACCEPT"]
        if [r["identity_id"] for r in rows] != ["0000045", "0000088", "0001030", "0001593"]:
            raise ValueError("Unexpected validation source selection")
        with ZipFile(source_archive) as archive:
            for row in rows:
                sid = row["identity_id"]
                try:
                    begin = time.perf_counter()
                    raw = archive.read(row["source_member"])
                    if sha256(raw).hexdigest() != row["source_sha256"]:
                        raise ValueError("Hand source hash differs")
                    from io import BytesIO
                    with Image.open(BytesIO(raw)) as image:
                        original = image.convert("RGB")
                    normalized, content_box = normalized_hand(original)
                    hand = localizer.locate(normalized)
                    coarse = segmenter.segment(normalized, hand)
                    validate_nail_mask(coarse, hand)
                    refined, fingers = segmenter.segment_fingertips(original, coarse, hand, content_box)
                    proposal = ImageChops.lighter(coarse, _to_normalized_mask(refined, content_box))
                    preparation = time.perf_counter() - begin
                    folder = output / sid
                    folder.mkdir()
                    original.save(folder / "source.png")
                    normalized.save(folder / "normalized.png")
                    coarse.save(folder / "coarse-mask.png")
                    refined.save(folder / "refined-mask.png")
                    mask = np.asarray(refined) > 127
                    before = np.asarray(original)
                    components = nail_components(mask)
                    if not 3 <= len(fingers) <= 5 or len(components) != len(fingers):
                        raise ValueError("Refined mask component/finger mismatch")
                    report["inputs"].append({"subject_id": sid, "original_sha256": row["source_sha256"],
                        "source_member": row["source_member"], "credit": "Afifi, 11K Hands (2019)",
                        "license": selection.get("usage_terms"), "original_size": original.size,
                        "nails": len(fingers), "preparation_seconds": preparation,
                        "coarse_mask_sha256": sha256((folder / "coarse-mask.png").read_bytes()).hexdigest(),
                        "refined_mask_sha256": sha256((folder / "refined-mask.png").read_bytes()).hexdigest(),
                        "mask_quality": "NEEDS_VISUAL_REVIEW; outside-mask preservation alone does not prove correct segmentation"})
                    sheet = Image.new("RGB", (1280, 365), "white")
                    draw = ImageDraw.Draw(sheet)
                    sheet.paste(ImageOps.contain(original, (320, 320)), (0, 40))
                    draw.text((5, 8), "Original " + sid, fill="black")
                    for index, style in enumerate(STYLES, 1):
                        start = time.perf_counter()
                        rendered = render(normalized, proposal, style)
                        mapped = _to_original(rendered, content_box, original.size)
                        result = composite_nails(original, mapped, NailCrop(
                            (0, 0, original.width, original.height), original, refined))
                        after = np.asarray(result)
                        outside = int(np.any(before != after, axis=2)[~mask].sum())
                        edits = [int(np.any(before[c[:, 0], c[:, 1]] != after[c[:, 0], c[:, 1]], axis=1).sum()) for c in components]
                        if outside or not all(edits):
                            raise RuntimeError("Preservation or edit coverage check failed")
                        path = folder / (style + ".png")
                        result.save(path)
                        report["cases"].append({"subject_id": sid, "style_id": style,
                            "output": path.relative_to(output).as_posix(),
                            "png_sha256": sha256(path.read_bytes()).hexdigest(),
                            "rgb_sha256": sha256(result.tobytes()).hexdigest(),
                            "changed_outside_refined_mask_pixels": outside,
                            "changed_pixels_per_nail_component": edits,
                            "render_and_composite_seconds": time.perf_counter() - start,
                            "visual_verdict": "NEEDS_REVIEW"})
                        sheet.paste(ImageOps.contain(result, (320, 320)), (index * 320, 40))
                        draw.text((index * 320 + 5, 8), style.removeprefix("exp_"), fill="black")
                    sheet.save(folder / "comparison.jpg", quality=94)
                    print("NAIL_VALIDATION DONE", sid, len(fingers), "nails", flush=True)
                except Exception as exc:
                    report["failures"].append({"subject_id": sid, "exception": type(exc).__name__, "message": str(exc)})
                    print("NAIL_VALIDATION HOLD", sid, type(exc).__name__, str(exc), flush=True)
                save()
        report["status"] = "REQUIRES_VISUAL_REVIEW" if not report["failures"] else "PARTIAL_REQUIRES_REVIEW"
    except BaseException as exc:
        report.update(status="FAILED", exception=type(exc).__name__, message=str(exc))
        raise
    finally:
        save()
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args.output)

