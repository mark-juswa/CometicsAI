"""Source surface cosmetic proof. Not imported by any serving runtime.

This module samples one cosmetic material color, never generated face pixels.
It currently supports a bounded lipstick proof on the saved development cases.
"""
import time

import cv2
import numpy as np

from scripts.makeup_alignment_pilot import CHAINS
from scripts.makeup_selected_cosmetics import inside, polygon
from scripts.makeup_source_faithful_retouch import validate, primary_face
from scripts.makeup_source_render import gamut_safe

CONFIG = {
    "version": "source_surface_lip_v4_1",
    "lip_feather_pixels": 3.0,
    "minimum_lip_contour_agreement": 0.65,
    "minimum_palette_pixels": 40,
    "generated_spatial_lightness_transfer": False,
    "lip_material": "source_gradient_plus_gamut_safe_palette_offset",
    "generated_texture_transfer": False,
    "production_enabled": False,
}


def lip_coverage(labels, points):
    """Use agreement of original feature estimates, never reference lip shape."""
    points = np.asarray(points, dtype=np.float64)
    if points.shape != (478, 3) or not np.isfinite(points).all():
        raise ValueError("Expected 478 finite source landmarks")
    if np.any((points[:, :2] < 0) | (points[:, :2] > 1)):
        raise ValueError("Source landmarks outside image")
    coordinates = points[:, :2] * 512
    outer = polygon(coordinates[CHAINS["lip_outer"]])
    inner = polygon(coordinates[CHAINS["lip_inner"]])
    ring = outer & ~inner
    semantic = np.isin(labels, (11, 12))
    union = semantic | ring
    agreement = float((semantic & ring).sum() / max(1, union.sum()))
    if agreement < CONFIG["minimum_lip_contour_agreement"]:
        raise ValueError("Uncertain original lip boundary")
    support = semantic & ring & primary_face(labels)
    if support.sum() < 100:
        raise ValueError("Insufficient original lip surface")
    distance = cv2.distanceTransform(support.astype(np.uint8), cv2.DIST_L2, 5)
    t = np.clip((distance - 1.0) / CONFIG["lip_feather_pixels"], 0, 1)
    alpha = (t * t * (3 - 2 * t)).astype(np.float32)
    return alpha, support, agreement


def palette(reference, reference_labels):
    """Read one lip material color, never a spatial generated shading map."""
    validate(reference, reference_labels)
    reference_lab = cv2.cvtColor(reference.astype(np.float32) / 255, cv2.COLOR_RGB2LAB)
    region = np.isin(reference_labels, (11, 12)) & primary_face(reference_labels)
    interior = inside(region, 3.0) >= 0.999
    if int(interior.sum()) < CONFIG["minimum_palette_pixels"]:
        raise ValueError("Insufficient reference lipstick samples")
    return np.median(reference_lab[interior], axis=0).astype(np.float32)



def apply_lipstick(original, reference, source_labels, reference_labels, source_points):
    """Keep source surface shading; apply a single reference lip material color."""
    started = time.perf_counter()
    validate(original, source_labels)
    validate(reference, reference_labels)
    alpha, support, agreement = lip_coverage(source_labels, source_points)
    selected = palette(reference, reference_labels)
    source_lab = cv2.cvtColor(original.astype(np.float32) / 255, cv2.COLOR_RGB2LAB)
    core = alpha >= 0.999
    if int(core.sum()) < CONFIG["minimum_palette_pixels"]:
        raise ValueError("Insufficient source lip interior")
    original_color = palette(original, source_labels)
    delta = selected - original_color
    allowed = support & (alpha > 0)
    # Constant interior offset preserves the source lightness gradient instead
    # of scaling away lip texture. Restrict it to avoid crushing any shadow.
    minimum_shift = np.max((1.0 - source_lab[:, :, 0][allowed]) / alpha[allowed])
    maximum_shift = np.min((99.0 - source_lab[:, :, 0][allowed]) / alpha[allowed])
    if minimum_shift > maximum_shift:
        raise ValueError("Source lip lightness cannot be preserved safely")
    delta[0] = np.clip(delta[0], minimum_shift, maximum_shift)
    target = source_lab + delta * alpha[:, :, None]
    target, compressed = gamut_safe(target, allowed)
    converted = cv2.cvtColor(target, cv2.COLOR_LAB2RGB)
    baseline = cv2.cvtColor(source_lab, cv2.COLOR_LAB2RGB)
    proposed = original.astype(np.float32) / 255 + converted - baseline
    output = original.copy()
    output[allowed] = np.rint(np.clip(proposed[allowed], 0, 1) * 255).astype(np.uint8)
    changed = np.any(output != original, axis=2)
    if np.any(changed & ~allowed):
        raise RuntimeError("Original protected pixels changed")
    return output, alpha, {
        "generator": CONFIG["version"],
        "original_is_canvas": True,
        "new_diffusion_calls": 0,
        "new_model_calls": 0,
        "lip_contour_agreement": agreement,
        "lip_pixels": int(allowed.sum()),
        "protected_changed_pixels": int((changed & ~allowed).sum()),
        "reference_lip_palette_lab": selected.tolist(),
        "source_lip_palette_lab": original_color.tolist(),
        "lip_material_offset_lab": delta.tolist(),
        "gamut_compressed_pixels": compressed,
        "seconds": time.perf_counter() - started,
    }

