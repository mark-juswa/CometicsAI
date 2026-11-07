"""Offline source fitted cosmetic application. Never called by serving code.

Accepts reviewed explicit assets or automatic local feature fields. Optional
source confidence and observed material detail refine the automatic route.
Technical source preservation and full look appearance remain separate gates.
"""
from hashlib import sha256
import json
from pathlib import Path
import sys

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.makeup_source_faithful_retouch import validate, primary_face
from scripts.makeup_source_render import gamut_safe
from scripts.makeup_surface_application import palette
from scripts.makeup_surface_application import apply_lipstick
from scripts.makeup_alignment_pilot import CHAINS
from scripts.makeup_selected_cosmetics import polygon, inside, linear, srgb

VERSION = "source-fitted-material-v1"
KINDS = {"lip", "eyeshadow", "liner", "blush", "contour", "highlight"}

# Cosmetic color families come from the existing style instructions. These are
# engineering defaults for review, not artist approved or learned style labels.
# Eye/cheek pigment RGB, then eye, cheek and lip dose factors. The three
# previously reviewed lip styles retain dose1 and their exact component pixels.
STYLE_PIGMENTS = {
    "natural_makeup": ([120, 83, 64], [175, 77, 83], .5, .4, 1.),
    "no_makeup_makeup": ([125, 92, 75], [178, 86, 90], .25, .2, .25),
    "soft_glam": ([137, 88, 65], [181, 89, 82], 1., .7, .75),
    "smoky_glam": ([91, 78, 69], [170, 83, 79], 1., .3, .65),
    "dewy_peach": ([190, 115, 80], [211, 111, 81], .8, .7, .65),
    "rosy_pink": ([152, 65, 102], [190, 71, 113], .9, .85, .55),
    "bronze_golden_glam": ([173, 110, 53], [184, 101, 66], 1., .6, .7),
    "matte_nude": ([126, 94, 75], [163, 93, 82], .7, .25, .7),
    "classic_red_lip": ([125, 94, 78], [178, 89, 85], .35, .3, 1.),
    "bold_evening_glam": ([119, 57, 91], [176, 70, 99], 1., .7, 1.),
    "exp_cloud_berry_lips": ([137, 91, 106], [180, 85, 106], .6, .4, 1.),
    "exp_manga_lash": ([154, 91, 109], [194, 94, 116], .7, .5, .5),
    "exp_icy_silver": ([116, 146, 179], [176, 91, 113], 1., .25, .65),
}


def pigment_projection(density, color):
    """Fit only the selected pigment, rejecting incompatible foundation color.

    Centered log density removes common lighting gain. A nonnegative pigment
    coefficient cannot turn a warm cheek design into a cyan/gray color removal.
    The source complexion supplies the substrate beneath this transparent dye.
    """
    pigment = linear(np.asarray(color, np.float32) / 255)
    basis = -np.log(np.maximum(pigment / pigment.max(), 1e-5))
    basis /= max(float(basis.max()), 1e-5)
    centered = basis - basis.mean()
    chromatic = density - density.mean(axis=2, keepdims=True)
    coefficient = np.maximum(0, np.sum(chromatic * centered, axis=2) / max(float(np.sum(centered ** 2)), 1e-5))
    return coefficient[:, :, None] * basis


def eyelid_taper(points478):
    """Fade shadow into the ORIGINAL crease/brow gap, rather than a box edge."""
    points = np.asarray(points478, np.float32)[:, :2] * 512
    yy, xx = np.mgrid[:512, :512]
    field = np.zeros((512, 512), np.float32)
    for side in ("right", "left"):
        upper = points[CHAINS[side + "_upper"]]
        lower = points[CHAINS[side + "_lower"]]
        brow = points[CHAINS[side + "_brow_lower"]]
        upper, lower, brow = [values[np.argsort(values[:, 0])] for values in (upper, lower, brow)]
        lid = np.interp(np.arange(512), upper[:, 0], upper[:, 1])[None, :]
        brow_edge = np.interp(np.arange(512), brow[:, 0], brow[:, 1])[None, :]
        gap = np.maximum(lid - brow_edge, 6)
        t = np.clip((lid - yy) / gap, 0, 1)
        fade = 1 - t * t * (3 - 2 * t)
        above = (yy <= lid) & (yy >= brow_edge)
        width = max(float(upper[-1, 0] - upper[0, 0]), 1)
        x = np.clip((xx - upper[0, 0] + .08 * width) / (1.16 * width), 0, 1)
        horizontal = np.sin(np.pi * x) ** .6
        bottom = np.interp(np.arange(512), lower[:, 0], lower[:, 1])[None, :]
        under = np.clip(1 - (yy - bottom) / 5, 0, 1) * ((yy >= bottom) & (yy < bottom + 5))
        field = np.maximum(field, (np.maximum(fade * above, under * .5) * horizontal).astype(np.float32))
    return field


def pixel_hash(array):
    return sha256(np.ascontiguousarray(array).tobytes()).hexdigest()


def catalog():
    """Read serving and held catalogs without enabling or relabeling styles."""
    presets = json.loads((ROOT / "data/makeup/DATA-M001-paired/inference_presets.json").read_text())
    release = json.loads((ROOT / "backend/app/style_release.json").read_text())
    rows = [{**row, "serving": True} for row in presets["styles"]]
    rows += [{"id": row["id"], "name": row["name"], "instruction": row["description"],
              "serving": row["enabled"], "review_status": row["review_status"]}
             for row in release["candidates"] if row["feature"] == "makeup"]
    if len({row["id"] for row in rows}) != len(rows):
        raise ValueError("Duplicate Makeup catalog IDs")
    return rows


def apply_material(original, alpha, selected, anchor, kind):
    """Preserve source surface differences under a bounded constant Lab offset.

    Low level development primitive, not an approval or mask fitting function.
    Chroma and lightness are color coordinates, not a calibrated skin model.
    """
    if original.dtype != np.uint8 or original.shape != (512, 512, 3):
        raise ValueError("Expected original 512 RGB")
    if (alpha.shape != (512, 512) or not np.issubdtype(alpha.dtype, np.floating)
            or not np.isfinite(alpha).all() or np.any((alpha < 0) | (alpha > 1))):
        raise ValueError("Expected finite float coverage in 0..1")
    if kind not in KINDS:
        raise ValueError("Unsupported cosmetic material")
    selected, anchor = np.asarray(selected, np.float32), np.asarray(anchor, np.float32)
    for value in (selected, anchor):
        if (value.shape != (3,) or not np.isfinite(value).all()
                or not 0 <= value[0] <= 100 or np.any(np.abs(value[1:]) > 128)):
            raise ValueError("Expected finite Lab material and source anchor")
    allowed = alpha > 0
    if not allowed.any():
        return original.copy(), {"changed_pixels": 0, "offset_lab": [0., 0., 0.]}
    source_lab = cv2.cvtColor(original.astype(np.float32) / 255, cv2.COLOR_RGB2LAB)
    delta = selected - anchor
    if kind == "blush":
        delta[0] = 0  # A cheek pigment cannot become a whitening foundation.
    minimum = np.max((1.0 - source_lab[:, :, 0][allowed]) / alpha[allowed])
    maximum = np.min((99.0 - source_lab[:, :, 0][allowed]) / alpha[allowed])
    if minimum > maximum:
        raise ValueError("Source lightness cannot be preserved safely")
    if kind == "blush":
        if not minimum <= 0 <= maximum:
            raise ValueError("Source cheek lightness outside safe pigment range")
    else:
        delta[0] = np.clip(delta[0], minimum, maximum)
    target, compressed = gamut_safe(source_lab + delta * alpha[:, :, None], allowed)
    converted = cv2.cvtColor(target, cv2.COLOR_LAB2RGB)
    baseline = cv2.cvtColor(source_lab, cv2.COLOR_LAB2RGB)
    proposed = original.astype(np.float32) / 255 + converted - baseline
    result = original.copy()
    result[allowed] = np.rint(np.clip(proposed[allowed], 0, 1) * 255).astype(np.uint8)
    return result, {"changed_pixels": int(np.any(result != original, axis=2).sum()),
                    "offset_lab": delta.tolist(), "gamut_compressed_pixels": compressed}


def render_layers(original, labels, document, masks, *, development_only=False):
    """Apply a source bound layer document. No automatic fitting or release path.

    Reviewed mode requires an explicit artist/salon attestation. This is not a
    cryptographic proof that a person reviewed it, or an appearance classifier.
    """
    validate(original, labels)
    if (document.get("schema") != "makeup-source-layers-v1"
            or document.get("production_enabled") is not False
            or document.get("style_id") not in {row["id"] for row in catalog()}
            or document.get("source_rgb_sha256") != pixel_hash(original)
            or document.get("labels_sha256") != pixel_hash(labels)
            or document.get("scope") not in {"component", "full_look"}):
        raise ValueError("Invalid or stale source layer document")
    review = document.get("artist_review", {})
    reviewed = (review.get("decision") == "ACCEPT" and review.get("role") in {"artist", "salon"}
                and isinstance(review.get("reviewer"), str) and review["reviewer"].strip()
                and isinstance(review.get("evidence"), str) and review["evidence"].strip())
    if not reviewed and not development_only:
        raise ValueError("Artist/salon layer review required")
    layers = document.get("layers", [])
    if not layers or len(layers) > 32 or len({row["id"] for row in layers}) != len(layers):
        raise ValueError("Expected unique explicit cosmetic layers")
    if set(masks) != {row["id"] for row in layers}:
        raise ValueError("Layer masks do not match document")
    face = primary_face(labels)
    union = np.zeros(labels.shape, bool)
    result = original.copy()
    metrics = []
    for layer in layers:
        kind, alpha = layer["kind"], masks[layer["id"]]
        if kind not in KINDS or pixel_hash(alpha) != layer.get("alpha_sha256"):
            raise ValueError("Unsupported or stale cosmetic coverage")
        if (alpha.shape != labels.shape or alpha.dtype != np.float32 or not np.isfinite(alpha).all()
                or np.any((alpha < 0) | (alpha > 1))):
            raise ValueError("Expected source fitted float32 coverage")
        support = (np.isin(labels, (11, 12)) if kind == "lip" else labels == 1) & face
        allowed = alpha > 0
        if np.any(allowed & ~support):
            raise ValueError("Cosmetic coverage crosses protected source region")
        if np.any(allowed & union):
            raise ValueError("Overlapping materials require an explicitly resolved artist layer")
        if np.count_nonzero(alpha >= .999) < 40:
            raise ValueError("Insufficient source anchor interior")
        anchor = (palette(original, labels) if kind == "lip" else
                  np.median(cv2.cvtColor(original.astype(np.float32) / 255,
                                         cv2.COLOR_RGB2LAB)[alpha >= .999], axis=0))
        painted, info = apply_material(original, alpha, layer["palette_lab"], anchor, kind)
        result[allowed] = painted[allowed]
        union |= allowed
        metrics.append({"id": layer["id"], "kind": kind, **info})
    if np.any(np.any(result != original, axis=2) & ~union):
        raise RuntimeError("Original protected pixels changed")
    return result, {"version": VERSION, "production_enabled": False,
                    "artist_review_present": bool(reviewed), "scope": document["scope"],
                    "full_look_quality": "NEEDS VERIFICATION", "layers": metrics,
                    "protected_changed_pixels": 0, "source_is_canvas": True}


def render_files(portrait, labels_path, layers_path, output, *, development_only=False):
    """Offline artist asset entry point. Masks are source sized NPY or grayscale PNG.

    Asset paths are local to the layer document. Refuse replacement of any input
    or earlier output. This does not enable styles in the application.
    """
    from PIL import Image
    portrait, labels_path, layers_path, output = map(Path, (portrait, labels_path, layers_path, output))
    receipt = output.with_suffix(output.suffix + ".json")
    if output.exists() or receipt.exists():
        raise ValueError("Refusing to overwrite existing image or receipt")
    if output.suffix.lower() != ".png":
        raise ValueError("Lossless PNG output required")
    original = np.array(Image.open(portrait))
    labels = np.array(Image.open(labels_path))
    document = json.loads(layers_path.read_text(encoding="utf-8"))
    folder = layers_path.resolve().parent
    masks, asset_hashes = {}, {}
    for layer in document["layers"]:
        mask_path = (folder / layer["alpha_path"]).resolve()
        if not mask_path.is_relative_to(folder):
            raise ValueError("Layer asset escapes its document directory")
        if mask_path.suffix.lower() == ".npy":
            alpha = np.load(mask_path, allow_pickle=False)
        elif mask_path.suffix.lower() == ".png":
            with Image.open(mask_path) as mask_image:
                if mask_image.mode != "L":
                    raise ValueError("Coverage PNG must be grayscale")
                alpha = np.array(mask_image).astype(np.float32) / 255
        else:
            raise ValueError("Coverage must be NPY or grayscale PNG")
        masks[layer["id"]] = alpha
        asset_hashes[layer["id"]] = sha256(mask_path.read_bytes()).hexdigest()
    result, metrics = render_layers(original, labels, document, masks, development_only=development_only)
    metrics.update({"document_sha256": sha256(layers_path.read_bytes()).hexdigest(),
                    "mask_file_sha256": asset_hashes, "rgb_sha256": pixel_hash(result),
                    "appearance": "EXPERIMENTAL", "training_target_approved": False})
    output.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(result).save(output)
    receipt.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    return metrics


def automatic_support(labels, points478, points68):
    """Source anatomy estimates for automatic local features, not artist masks."""
    points = np.asarray(points478, np.float32)
    coarse = np.asarray(points68, np.float32)
    if (points.shape != (478, 3) or not np.isfinite(points).all()
            or np.any((points[:, :2] < 0) | (points[:, :2] > 1))
            or coarse.shape != (68, 2) or not np.isfinite(coarse).all()):
        raise ValueError("Uncertain automatic source anatomy")
    face = primary_face(labels)
    skin = (labels == 1) & face
    pixels = points[:, :2] * 512
    eye = np.zeros(labels.shape, np.float32)
    for side in ("right", "left"):
        upper = pixels[CHAINS[side + "_upper"]]
        lower = pixels[CHAINS[side + "_lower"]]
        brow = pixels[CHAINS[side + "_brow_lower"]]
        for values in (upper, lower, brow):
            values[:] = values[np.argsort(values[:, 0])]
        # One source fitted orbital region, with its own visible eye protected.
        region = polygon(np.vstack((brow + [0, 3], (lower + [0, 5])[::-1])))
        alpha = inside(region, 4) * inside(skin, 2)
        eye = np.maximum(eye, alpha)
    # Mesh based cheek support spans the source eye/nose/mouth/jaw anatomy.
    # The neural field determines actual color placement within this support.
    cheeks = np.zeros_like(eye)
    for indexes in ([36, 41, 40, 31, 48, 4, 2], [42, 47, 46, 45, 14, 12, 54, 35]):
        ring = coarse[indexes].copy()
        eye_indexes = np.asarray(indexes) < 48
        eye_indexes &= np.asarray(indexes) >= 36
        ring[eye_indexes, 1] += 7
        region = polygon(ring)
        cheeks = np.maximum(cheeks, inside(region, 12) * inside(skin, 4))
    # These are disjoint source supports. Do not double apply orbital pigment.
    cheeks *= (1 - eye)
    if (eye > .5).sum() < 100 or (cheeks > .5).sum() < 100:
        raise ValueError("Insufficient automatic cosmetic support")
    return {"eye": eye.astype(np.float32), "cheek": cheeks.astype(np.float32)}


def apply_counterfactual(original, reference, labels, ref_labels, points478,
                         baseline, edited, fields, style_id, *, materials=None):
    """Apply learned cosmetic change relative to SAME source reconstruction.

    Both decoder results are intermediate fields, never the face canvas.
    The default retained lipstick is unchanged. Optional offline materials
    refine its source coverage/hue without changing the baseline operator.
    No artist attestation is inferred.
    """
    validate(original, labels)
    validate(reference, ref_labels)
    if style_id not in {row["id"] for row in catalog()}:
        raise ValueError("Unknown Makeup style")
    for value in (baseline, edited):
        if value.shape != (256, 256, 3) or not np.isfinite(value).all():
            raise ValueError("Expected finite256RGB decoder fields")
    if set(fields) != {"eye", "cheek"}:
        raise ValueError("Missing automatic source fields")
    for field in fields.values():
        if (field.shape != (512, 512) or field.dtype != np.float32
                or not np.isfinite(field).all() or np.any((field < 0) | (field > 1))
                or np.any((field > 0) & (labels != 1))):
            raise ValueError("Automatic fields cross protected source")
    eye, cheek = fields["eye"] * eyelid_taper(points478), fields["cheek"]
    alpha = np.maximum(eye, cheek)
    safe = [np.clip(value, 1 / 255, 1).astype(np.float32) for value in (baseline, edited)]
    # A reference foundation can brighten/desaturate all channels. In log light
    # space this is a common density offset. Remove it before applying pigment,
    # rather than subtracting the original complexion's Lab chroma.
    density = np.log(np.maximum(linear(safe[0]), 1e-5)) - np.log(np.maximum(linear(safe[1]), 1e-5))
    density = cv2.resize(density, (512, 512), interpolation=cv2.INTER_LINEAR)
    if set(STYLE_PIGMENTS) != {row["id"] for row in catalog()}:
        raise ValueError("Cosmetic material coverage differs from actual catalog")
    eye_color, cheek_color, eye_dose, cheek_dose, lip_dose = STYLE_PIGMENTS[style_id]
    cheek_density = pigment_projection(density, cheek_color) * cheek[:, :, None] * cheek_dose
    colored_eye = pigment_projection(density, eye_color)
    # Positive neutral absorption supplies the learned liner/smoky depth.
    # Negative neutral density is foundation whitening and is excluded.
    neutral_eye = np.maximum(np.min(density - colored_eye, axis=2, keepdims=True), 0)
    eye_density = (colored_eye + neutral_eye) * eye[:, :, None] * eye_dose
    absorption = cheek_density + eye_density
    rgb = srgb(linear(original.astype(np.float32) / 255) * np.exp(-absorption))
    allowed = alpha > 0
    compressed = 0
    # Silver reflection is a localized cosmetic effect, not a new foundation.
    if style_id == "exp_icy_silver":
        small_lab = [cv2.cvtColor(np.clip(value, 0, 1).astype(np.float32), cv2.COLOR_RGB2LAB)
                     for value in (baseline, edited)]
        highlight = cv2.resize(np.maximum(small_lab[1][:, :, 0] - small_lab[0][:, :, 0], 0),
                               (512, 512), interpolation=cv2.INTER_LINEAR)
        lab = cv2.cvtColor(np.clip(rgb, 0, 1), cv2.COLOR_RGB2LAB)
        lab[:, :, 0] += np.minimum(highlight, 6) * eye
        lab, compressed = gamut_safe(lab, allowed)
        converted = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
        # Do not introduce color conversion changes outside silver coverage.
        rgb[eye > 0] = converted[eye > 0]
    result, lip_alpha, lip_metrics = apply_lipstick(original, reference, labels, ref_labels, points478)
    if lip_dose < 1:
        result = np.rint(original.astype(np.float32) + lip_dose * (result.astype(np.float32) - original)).clip(0, 255).astype(np.uint8)
    result[allowed] = np.rint(np.clip(rgb[allowed], 0, 1) * 255).astype(np.uint8)
    union = allowed | (lip_alpha > 0)
    changed = np.any(result != original, axis=2)
    if np.any(changed & ~union):
        raise RuntimeError("Source surface protection failed")
    masks = {"eye": eye, "cheek": cheek, "lip": lip_alpha}
    if materials is not None:
        from scripts.makeup_materials import refine_materials, STYLE_MATERIALS
        if set(STYLE_MATERIALS) != {row["id"] for row in catalog()}:
            raise ValueError("Source materials do not cover the actual catalog")
        return refine_materials(original, reference, labels, ref_labels, points478,
                                result, masks, style_id, materials, lip_dose)
    return result, masks, {"version": "automatic-local-pigment-v2_1", "production_enabled": False,
                           "source_is_canvas": True, "artist_required": False,
                           "protected_changed_pixels": int((changed & ~union).sum()),
                           "brow_changed_pixels": int((changed & np.isin(labels, (6, 7))).sum()),
                           "eye_interior_changed_pixels": int((changed & np.isin(labels, (4, 5))).sum()),
                           "region_changed_pixels": {key: int((changed & (mask > 0)).sum()) for key, mask in masks.items()},
                           "gamut_compressed_pixels": compressed, "lip_component": lip_metrics,
                           "lip_style_dose": lip_dose,
                           "maximum_cosmetic_density": float(absorption.max()),
                           "full_look_quality": "NEEDS VERIFICATION"}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--portrait", type=Path, required=True)
    parser.add_argument("--labels", type=Path, required=True)
    parser.add_argument("--layers", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--development-only", action="store_true", help="Explicit unapproved offline component proof")
    args = parser.parse_args()
    print(json.dumps(render_files(args.portrait, args.labels, args.layers, args.output,
                                  development_only=args.development_only), indent=2))
