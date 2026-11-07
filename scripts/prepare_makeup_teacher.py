"""Fit a labeled external teacher proof to its original portrait, offline only.

This prepares a review candidate, never admits training data or runs MAKEUP-001.
"""
import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import sys

os.environ.setdefault("USE_TF", "0")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def restore_brow_gradients(original, target, brow_region, allowed):
    """Fit original hair gradients to foundation, confined to source anatomy.

    A scalar darkening of inpainted skin flattens brow hairs. Poisson fitting
    retains the original RGB gradients and solves their boundary colour offset.
    The original RGB values need not remain exact under a changed foundation.
    """
    import cv2
    import numpy as np

    mask = cv2.dilate(brow_region.astype(np.uint8), np.ones((9, 9), np.uint8))
    mask = ((mask > 0) & allowed).astype(np.uint8) * 255
    if not np.any(mask):
        raise ValueError("Source brow gradient support unavailable")
    support = mask > 0
    result = target.copy()
    x, y, width, height = cv2.boundingRect(mask)
    # OpenCV may modify its mask scratch buffer. Keep the anatomical write
    # support independent, including protected holes within the brow vicinity.
    cloned = cv2.seamlessClone(original, target.copy(), mask.copy(),
                               (x + width // 2, y + height // 2), cv2.NORMAL_CLONE)
    result[support] = cloned[support]
    return result


def fit(original, labels, points, teacher, reference_labels, reference_points, *, version="v2"):
    import cv2
    import numpy as np
    from scripts.makeup_selected_cosmetics import warp_reference, inside, polygon, linear, srgb
    from scripts.makeup_materials import eye_curves, smoothstep
    from scripts.makeup_source_faithful_retouch import primary_face

    if original.shape != (512, 512, 3) or teacher.shape != original.shape:
        raise ValueError("Teacher fitting requires the recorded 512 square canvas")
    if version not in ("v2", "v3", "v4", "v5"):
        raise ValueError("Unknown teacher fit version")
    aligned, mapped, valid = warp_reference(teacher, reference_labels, points, reference_points)
    if version in ("v3", "v4", "v5"):
        # Reuse the frozen registration on an all-one support image. Its warped
        # support is one only where interpolation samples the reference image;
        # the source mesh hull alone also includes invalid black-padding samples.
        support, _, _ = warp_reference(np.ones_like(teacher, dtype=np.float32), reference_labels, points, reference_points)
        valid &= support[..., 0] >= 1 - 1e-6
    source_xy = np.asarray(points, np.float32)[:468, :2] * 512
    target_xy = np.asarray(reference_points, np.float32)[:468, :2] * 512
    affine, _ = cv2.estimateAffinePartial2D(target_xy, source_xy, method=cv2.LMEDS)
    if affine is None:
        raise ValueError("Teacher registration failed")
    fallback = cv2.warpAffine(teacher, affine, (512, 512), flags=cv2.INTER_LINEAR,
                              borderMode=cv2.BORDER_REFLECT_101)
    fallback_labels = cv2.warpAffine(reference_labels, affine, (512, 512), flags=cv2.INTER_NEAREST)
    yy = np.mgrid[:512, :512][0]
    if version in ("v3", "v4", "v5"):
        # Similarity alignment is needed above the dense forehead mesh. Along
        # the jaw it can import a clothing edge from a differently framed edit.
        forehead = yy < np.mean(source_xy[[70, 300], 1])
        fallback = np.where(forehead[..., None], fallback, original)
        fallback_labels = np.where(forehead, fallback_labels, labels)
    weight = inside(valid, 10)
    aligned = np.rint(aligned * weight[..., None] + fallback * (1 - weight[..., None])).clip(0, 255).astype(np.uint8)
    mapped = np.where(valid, mapped, fallback_labels)
    if version in ("v3", "v4", "v5"):
        # Remove the edited brow before restoring original hairs. Copying the
        # original skin over an unwanted extra brow leaves an unpainted stripe.
        # Only estimate the tiny underlying foundation area from this teacher.
        edited_brow = cv2.dilate(np.isin(mapped, [6, 7]).astype(np.uint8), np.ones((3, 3), np.uint8))
        aligned = cv2.inpaint(aligned, edited_brow, 3, cv2.INPAINT_TELEA)
    face = primary_face(labels)
    alpha = inside(face, 8) * inside(np.isin(mapped, [1, 2, 4, 5, 6, 7, 10, 11, 12]), 5)
    core = np.zeros((512, 512), np.uint8)
    for upper, lower, _ in eye_curves(points, 478):
        core |= polygon(np.vstack((upper, lower[::-1]))).astype(np.uint8)
    core = cv2.erode(core, np.ones((3, 3), np.uint8)) > 0
    brow_region = np.isin(labels, [6, 7])
    brows = brow_region.copy()
    source_lab = cv2.cvtColor(original.astype(np.float32) / 255, cv2.COLOR_RGB2LAB)
    if version in ("v3", "v4", "v5"):
        # Parser brow labels also include intervening bare skin. Copying that
        # whole region creates a visible unpainted stripe under foundation.
        skin = (labels == 1).astype(np.float32)
        weight = cv2.GaussianBlur(skin, (0, 0), 6)
        context = cv2.GaussianBlur(source_lab[..., 0] * skin, (0, 0), 6) / np.maximum(weight, 1e-5)
        brows = brow_region & (weight > .05) & (source_lab[..., 0] < context - 6)
        if brows.sum() < 10:
            raise ValueError("Source brow hair separation uncertain")
    nose = labels == 2
    if not nose.any():
        raise ValueError("Source nose labels unavailable")
    nostril = nose & (source_lab[..., 0] <= np.quantile(source_lab[..., 0][nose], .06))
    protected = core | brows | (labels == 10) | nostril | (labels == 3)
    if version in ("v4", "v5"):
        # A photographed brow pixel includes the old underlying skin and light.
        # Preserve its source hair density/shape below, rather than stamping that
        # old RGB pixel into a differently finished foundation.
        protected = core | (labels == 10) | nostril | (labels == 3)
    if version == "v2":
        protected |= np.isin(mapped, [6, 7]) & ~brow_region
    protected |= (mapped == 10) & (labels != 10)
    alpha *= smoothstep(cv2.distanceTransform((~protected).astype(np.uint8), cv2.DIST_L2, 5) / 3)
    alpha[~face | protected] = 0
    target_lab = cv2.cvtColor(aligned.astype(np.float32) / 255, cv2.COLOR_RGB2LAB)
    source_high = source_lab[..., 0] - cv2.GaussianBlur(source_lab[..., 0], (0, 0), .7)
    neutral = (labels == 1) & (yy > np.asarray(points)[[145, 374], 1].max() * 512 + 14)
    if version in ("v3", "v4", "v5"):
        # A source high-pass at the jaw edge is an edge, not pore texture. Adding
        # it over an already aligned edge draws a bright duplicate contour.
        neutral &= cv2.erode((face & ~protected).astype(np.uint8), np.ones((9, 9), np.uint8)) > 0
        source_high = np.clip(source_high, -1.5, 1.5)
    target_lab[..., 0][neutral] = (cv2.GaussianBlur(target_lab[..., 0], (0, 0), .7) + source_high)[neutral]
    restored = np.clip(cv2.cvtColor(target_lab, cv2.COLOR_LAB2RGB), 0, 1)
    if version == "v4":
        original_linear = linear(original.astype(np.float32) / 255)
        luma = original_linear @ np.array([.2126, .7152, .0722], np.float32)
        skin = (labels == 1).astype(np.float32)
        support = cv2.GaussianBlur(skin, (0, 0), 6)
        skin_luma = cv2.GaussianBlur(luma * skin, (0, 0), 6) / np.maximum(support, 1e-5)
        density = np.clip(-np.log(np.maximum(luma, 1e-5) / np.maximum(skin_luma, 1e-5)), 0, 1.8)
        density *= inside(brow_region, 1.5) * np.minimum(support / .05, 1)
        # Scalar attenuation retains foundation-compatible brow colour and the
        # original spatial hair contrast; no teacher brow geometry is retained.
        restored = srgb(linear(restored) * np.exp(-density[..., None]))
    rgb = linear(original.astype(np.float32) / 255) * (1 - alpha[..., None]) + linear(restored) * alpha[..., None]
    result = original.copy()
    allowed = alpha > 0
    result[allowed] = np.rint(np.clip(srgb(rgb[allowed]), 0, 1) * 255).astype(np.uint8)
    if version == "v5":
        result = restore_brow_gradients(original, result, brow_region, allowed & ~protected & face)
    if not np.array_equal(result[protected | ~face], original[protected | ~face]):
        raise AssertionError("Source feature or scene restoration failed")
    difference = cv2.cvtColor(result.astype(np.float32) / 255, cv2.COLOR_RGB2LAB) - source_lab
    return result, alpha, {
        "fit_version": version,
        "source_eye_core_brow_teeth_nostril_scene_changed_pixels": 0 if version == "v2" else None,
        "source_eye_core_brow_hair_teeth_nostril_scene_changed_pixels": 0 if version not in ("v4", "v5") else None,
        "source_eye_core_teeth_nostril_scene_changed_pixels": 0,
        "brow_preservation": ("source spatial RGB gradients, boundary fitted to foundation" if version == "v5" else
            "source spatial hair optical density; foundation-compatible colour" if version == "v4" else "source RGB cores"),
        "protected_brow_pixels": int(brows.sum()), "parser_brow_region_pixels": int(brow_region.sum()),
        "skin_median_delta_lab": np.median(difference[labels == 1], axis=0).tolist(),
        "limit": "Registration and protected pixels do not establish complete geometry, texture or realism quality.",
    }


def analyze_images(images, plan, *, allow_small_secondary=False):
    """Reuse the same pinned CPU models for original and teacher anatomy."""
    import cv2
    import numpy as np
    from PIL import Image
    import torch
    import mediapipe as mp
    from mediapipe.tasks import python
    from mediapipe.tasks.python import vision
    from transformers import SegformerImageProcessor, SegformerForSemanticSegmentation
    from scripts.makeup_source_faithful_retouch import primary_face
    parser_dir = ROOT / plan["parser"]["directory"]
    for name, expected in plan["parser"]["files"].items():
        if sha256((parser_dir / name).read_bytes()).hexdigest() != expected:
            raise ValueError("Pinned parser asset differs")
    model = json.loads((ROOT / "artifacts/makeup-render-20261030/alignment-01/plan.json").read_text(encoding="utf-8"))["model"]
    if sha256((ROOT / model["path"]).read_bytes()).hexdigest() != model["sha256"]:
        raise ValueError("Recorded landmark model differs")
    torch.set_num_threads(4)
    processor = SegformerImageProcessor.from_pretrained(str(parser_dir), local_files_only=True)
    parser = SegformerForSemanticSegmentation.from_pretrained(str(parser_dir), local_files_only=True, use_safetensors=True).eval()
    options = vision.FaceLandmarkerOptions(base_options=python.BaseOptions(model_asset_path=str(ROOT / model["path"]),
        delegate=python.BaseOptions.Delegate.CPU), running_mode=vision.RunningMode.IMAGE, num_faces=2,
        min_face_detection_confidence=.6, min_face_presence_confidence=.6)
    result = []
    with vision.FaceLandmarker.create_from_options(options) as detector:
        for image in images:
            with torch.inference_mode():
                logits = parser(**processor(images=Image.fromarray(image), return_tensors="pt")).logits
                labels = torch.nn.functional.interpolate(logits, size=(512, 512), mode="bilinear", align_corners=False).argmax(1)[0].byte().numpy()
            detected = detector.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(image)))
            points = [np.array([[p.x, p.y, p.z] for p in face], np.float32) for face in detected.face_landmarks]
            if not points or (len(points) != 1 and not allow_small_secondary):
                raise ValueError("Portrait face missing or ambiguous")
            points.sort(key=lambda p: float(np.ptp(p[:, 0]) * np.ptp(p[:, 1])), reverse=True)
            if len(points) > 1 and np.prod(np.ptp(points[1][:, :2], axis=0)) > .15 * np.prod(np.ptp(points[0][:, :2], axis=0)):
                raise ValueError("Multiple comparable portrait faces")
            face = primary_face(labels)
            center = np.rint(points[0][:468, :2].mean(axis=0) * 512).clip(0, 511).astype(int)
            if not face[center[1], center[0]]:
                raise ValueError("Landmark face and primary semantic face disagree")
            result.append((labels, points[0]))
    return result


def prepare(source_id, style_id, raw, output, *, version="v2", source_plan=None, target_anatomy=None):
    import numpy as np
    from PIL import Image, ImageDraw

    output = Path(output)
    if output.exists():
        raise ValueError("Preserve earlier teacher proofs; choose a new output directory")
    plan = json.loads(Path(source_plan or ROOT / "artifacts/makeup-refinement-20261105/catalog-review/plan.json").read_text(encoding="utf-8"))
    source = next(s for s in plan["sources"] if s["id"] == source_id)
    for key, hash_key in (("source", "sha256"), ("labels", "labels_sha256"), ("points478", "points478_sha256")):
        if sha256((ROOT / source[key]).read_bytes()).hexdigest() != source[hash_key]:
            raise ValueError("Recorded source asset differs: " + key)
    original = np.array(Image.open(ROOT / source["source"]).convert("RGB"))
    labels = np.array(Image.open(ROOT / source["labels"]))
    points = json.loads((ROOT / source["points478"]).read_text(encoding="utf-8"))["points"]
    teacher = np.array(Image.open(raw).convert("RGB").resize((512, 512), Image.Resampling.LANCZOS))
    if target_anatomy is None:
        refs, rp = analyze_images([teacher], plan, allow_small_secondary=True)[0]
    else:
        if target_anatomy.get("normalized_rgb_sha256") != sha256(teacher.tobytes()).hexdigest():
            raise ValueError("Cached target anatomy belongs to a different teacher image")
        refs, rp = target_anatomy["labels"], target_anatomy["points"]
    result, alpha, checks = fit(original, labels, points, teacher, refs, rp, version=version)
    output.mkdir(parents=True)
    path = output / "prepared.png"
    Image.fromarray(result).save(path)
    Image.fromarray(np.rint(alpha * 255).astype(np.uint8)).save(output / "alpha.png")
    Image.fromarray(refs).save(output / "reference-labels.png")
    (output / "reference-points.json").write_text(json.dumps(rp.tolist()) + "\n")
    Image.fromarray(teacher).save(output / "normalized-raw.png")
    board = Image.new("RGB", (1536, 544), "white")
    draw = ImageDraw.Draw(board)
    for i, (title, pixels) in enumerate(zip(("Original", "External editor RAW", "Prepared teacher, NOT MAKEUP-001"), (original, teacher, result))):
        draw.text((i * 512 + 5, 8), title, fill="black")
        board.paste(Image.fromarray(pixels), (i * 512, 32))
    board.save(output / "comparison.png")
    record = {"schema": "external-teacher-target-proof-v1", "tool": "built-in image_gen", "model_id": "not provided by tool",
        "source_id": source_id, "style_id": style_id, "source": source["source"], "source_sha256": source["sha256"],
        "source_photo": source["source_photo"], "raw_sha256": sha256(Path(raw).read_bytes()).hexdigest(),
        "prepared_sha256": sha256(path.read_bytes()).hexdigest(), "prepared_rgb_sha256": sha256(result.tobytes()).hexdigest(),
        "not_our_makeup_model_output": True, "training_accepted": False, "production_enabled": False,
        "visual_review": "PENDING", **checks}
    record["preparation_code_sha256"] = sha256(Path(__file__).read_bytes()).hexdigest()
    (output / "report.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--source-id", required=True)
    cli.add_argument("--style-id", required=True)
    cli.add_argument("--raw", required=True, type=Path)
    cli.add_argument("--output", required=True, type=Path)
    cli.add_argument("--fit-version", choices=("v2", "v3", "v4", "v5"), default="v2")
    cli.add_argument("--source-plan", type=Path)
    args = cli.parse_args()
    prepare(args.source_id, args.style_id, args.raw, args.output, version=args.fit_version, source_plan=args.source_plan)
