"""Offline cosmetic separation repair. Never imported by the live Makeup service.

The current proof covers rose or red blush references only. Its masks are
estimates, not ground truth cosmetic layers. Appearance still requires review.
"""
import time

import cv2
import numpy as np

from scripts.makeup_alignment_pilot import CHAINS
from scripts.makeup_selected_cosmetics import warp_reference, normalized, inside, polygon
from scripts.makeup_source_faithful_retouch import validate, primary_face
from scripts.makeup_source_render import gamut_safe

CONFIG = {
    "neutral_sigma": 30.0,
    "minimum_neutral_pixels": 1000,
    "blush_transition_sigma": 3.0,
    "eyelid_transition_sigma": 5.0,
    "local_contrast_sigma": 12.0,
    "eye_rim_pixels": 2.0,
    "lip_feather_pixels": 1.5,
    "texture_sigma": 1.4,
    "color_transfer": "signed-Lab-pigment-residual",
    "rgb_update": "delta-relative-to-original-conversion",
    "blush_scope": "positive-red-excess-only",
    "new_diffusion_calls": 0,
}


def ramp(values, full):
    return np.clip(values / full, 0.0, 1.0)


def blush_layer(reference_lab, neutral_lab, support, source_residual=None):
    """Pale or neutral highlights must not become colored blush.

    A magnitude-only mask confuses lost yellow/red complexion with cosmetic
    pigment. The selected references have rose/red blush, so only positive
    red-axis excess qualifies. Other blush families are outside this proof.
    Source lightness is never changed by this layer.
    """
    residual = reference_lab[:, :, 1:] - neutral_lab[:, :, 1:]
    red = residual[:, :, 0]
    alpha = support * ramp(np.maximum(red, 0.0), 4.0)
    if source_residual is not None:
        residual = residual - source_residual
    return residual, alpha.astype(np.float32)


def eye_protection(labels):
    eye = np.isin(labels, (4, 5))
    distance = cv2.distanceTransform(eye.astype(np.uint8), cv2.DIST_L2, 5)
    core = distance > CONFIG["eye_rim_pixels"]
    return core, eye & ~core


def transfer(original, reference, source_labels, reference_labels,
             source_points, reference_points):
    validate(original, source_labels)
    validate(reference, reference_labels)
    started = time.perf_counter()
    face = primary_face(source_labels)
    primary_face(reference_labels)
    mapped, ref_labels, valid = warp_reference(
        reference, reference_labels, source_points, reference_points
    )
    points = np.asarray(source_points, np.float32)[:, :2] * 512
    src = cv2.cvtColor(original.astype(np.float32) / 255, cv2.COLOR_RGB2LAB)
    ref = cv2.cvtColor(mapped.astype(np.float32) / 255, cv2.COLOR_RGB2LAB)
    skin = (source_labels == 1) & face & valid
    common = skin & (ref_labels == 1)
    if int(common.sum()) < 10000:
        raise ValueError("Insufficient aligned facial skin")
    yy, xx = np.mgrid[:512, :512]
    eyes = []
    for side in ("right", "left"):
        upper = points[CHAINS[side + "_upper"]]
        lower = points[CHAINS[side + "_lower"]]
        brow = points[CHAINS[side + "_brow_lower"]]
        upper, lower, brow = [
            a[np.argsort(a[:, 0])] for a in (upper, lower, brow)
        ]
        eyes.append((upper, lower, brow))
    eye_y = float(np.mean([u[:, 1].mean() for u, _, _ in eyes]))
    mouth_top = float(points[CHAINS["lip_outer"], 1].min())
    face_height = float(np.ptp(points[:468, 1]))
    neutral = common & (
        (yy < eye_y - 0.10 * face_height)
        | (yy > mouth_top + 0.17 * face_height)
    )
    if int(neutral.sum()) < CONFIG["minimum_neutral_pixels"]:
        raise ValueError("Insufficient neutral complexion samples")
    src_base = normalized(src, neutral, CONFIG["neutral_sigma"])
    ref_base = normalized(ref, neutral, CONFIG["neutral_sigma"])
    delta = ref - ref_base
    output = src.copy()
    masks = {
        name: np.zeros((512, 512), np.float32)
        for name in ("blush", "eyeshadow", "lash_liner", "brow", "lip")
    }
    # Extract the incremental pigment effect, not source complexion or its
    # existing cheek redness. A smooth prior does not cut off the blush at an
    # ellipse edge. Only the correction field is filtered, never source pixels.
    cheek_support = np.zeros((512, 512), np.float32)
    for upper, lower, brow in eyes:
        width = float(upper[-1, 0] - upper[0, 0])
        cx = float(upper[:, 0].mean())
        outward = -1 if cx < float(points[:468, 0].mean()) else 1
        bottom = float(lower[:, 1].max())
        cy = bottom + 0.5 * (mouth_top - bottom)
        radial = (
            ((xx - (cx + outward * 0.20 * width)) / (width * 1.25)) ** 2
            + ((yy - cy) / max(20, (mouth_top - bottom) * 0.85)) ** 2
        )
        support = np.exp(-2 * radial).astype(np.float32) * skin
        cheek_support = np.maximum(cheek_support, support)
    source_color_residual = src[:, :, 1:] - src_base[:, :, 1:]
    color, alpha = blush_layer(ref, ref_base, cheek_support, source_color_residual)
    pigment_field = cv2.GaussianBlur(
        color * alpha[:, :, None], (0, 0), CONFIG["blush_transition_sigma"]
    )
    alpha = cv2.GaussianBlur(alpha, (0, 0), CONFIG["blush_transition_sigma"])
    alpha[~skin] = 0
    pigment_field[~skin] = 0
    output[:, :, 1:] += pigment_field
    masks["blush"] = alpha.astype(np.float32)

    # Whole complexion contrast is not eyelid pigment. Estimate local contrast
    # separately so the jaw/forehead brightness cannot paint a dark eye plate.
    # The source eye core remains exact; a narrow rim admits real lash strokes.
    eye_core, eye_rim = eye_protection(source_labels)
    sigma = CONFIG["local_contrast_sigma"]
    reference_dark = np.maximum(0, cv2.GaussianBlur(ref[:, :, 0], (0, 0), sigma) - ref[:, :, 0])
    original_dark = np.maximum(0, cv2.GaussianBlur(src[:, :, 0], (0, 0), sigma) - src[:, :, 0])
    extra_dark = np.maximum(0, reference_dark - original_dark)
    for upper, lower, brow in eyes:
        boundary = np.vstack((brow + [0, 2], (lower + [0, 3])[::-1]))
        geometry = polygon(boundary)
        matte = cv2.GaussianBlur(
            geometry.astype(np.float32), (0, 0), CONFIG["eyelid_transition_sigma"]
        )
        eligible = face & valid & ~eye_core & np.isin(source_labels, (1, 4, 5))
        matte[~eligible] = 0
        # Neutral samples surround the cosmetic extent rather than borrowing
        # the shaded jaw as the eyelid's underlying complexion.
        exclusion = cv2.dilate(geometry.astype(np.uint8), np.ones((17, 17), np.uint8)) > 0
        local_neutral = common & ~exclusion
        local_ref = normalized(ref, local_neutral, 12.0)
        local_src = normalized(src, local_neutral, 12.0)
        incremental_color = (ref[:, :, 1:] - local_ref[:, :, 1:]) - (src[:, :, 1:] - local_src[:, :, 1:])
        color_alpha = matte * skin
        field = cv2.GaussianBlur(
            incremental_color * color_alpha[:, :, None], (0, 0), 1.5
        )
        field[~skin] = 0
        output[:, :, 1:] += field
        dark_alpha = matte * ramp(extra_dark, 2.0)
        output[:, :, 0] -= extra_dark * dark_alpha
        masks["eyeshadow"] = np.maximum(masks["eyeshadow"], color_alpha)
        masks["lash_liner"] = np.maximum(masks["lash_liner"], dark_alpha)

    # Brow outline remains the source outline. Pigment is bounded inward.
    brow = np.isin(source_labels, (6, 7)) & face & valid
    # Feather both source and reference boundaries, not a hard intersection.
    alpha = inside(brow, 3) * inside(np.isin(ref_labels, (6, 7)), 3)
    output[:, :, 0] -= extra_dark * alpha
    masks["brow"] = alpha.astype(np.float32)

    # Keep the selected lipstick and source lip geometry/fine surface detail.
    lip = np.isin(source_labels, (11, 12)) & face & valid
    if int(lip.sum()) < 100:
        raise ValueError("Missing source lips")
    ref_lip = np.isin(ref_labels, (11, 12)) & valid
    coverage = float(ref_lip[lip].mean())
    if coverage < 0.65:
        raise ValueError("Lip reference alignment is uncertain")
    smooth_ref = normalized(ref, ref_lip, CONFIG["texture_sigma"])
    smooth_source = normalized(src, lip, CONFIG["texture_sigma"])
    target = smooth_ref + (src - smooth_source)
    alpha = inside(lip, CONFIG["lip_feather_pixels"])
    output = output * (1 - alpha[:, :, None]) + target * alpha[:, :, None]
    masks["lip"] = alpha.astype(np.float32)

    allowed = np.logical_or.reduce([m > 0 for m in masks.values()])
    allowed &= face & valid & ~eye_core
    result = original.copy()
    output, compressed = gamut_safe(output, allowed)
    converted = cv2.cvtColor(output, cv2.COLOR_LAB2RGB)
    baseline = cv2.cvtColor(src, cv2.COLOR_LAB2RGB)
    # Apply only the requested color delta to original RGB. An absolute Lab
    # round trip changed five source pixels by one code even with no makeup.
    rgb = original.astype(np.float32) / 255 + (converted - baseline)
    result[allowed] = np.rint(np.clip(rgb, 0, 1) * 255).astype(np.uint8)[allowed]
    if np.any(result[~allowed] != original[~allowed]):
        raise RuntimeError("Protected source pixels changed")
    return result, masks, {
        "generator": "beautycore_cosmetic_separation_repair_v2_1",
        "new_diffusion_calls": 0,
        "original_is_canvas": True,
        "display_source_warped": False,
        "neutral_pixels": int(neutral.sum()),
        "lip_alignment_coverage": coverage,
        "gamut_compressed_pixels": compressed,
        "protected_source_changed_pixels": 0,
        "eye_core_changed_pixels": int(np.any(result != original, axis=2)[eye_core].sum()),
        "eye_rim_changed_pixels": int(np.any(result != original, axis=2)[eye_rim].sum()),
        "region_pixels": {k: int((v > 0).sum()) for k, v in masks.items()},
        "cpu_seconds": time.perf_counter() - started,
        "scope_limit": "Three rose/red-blush references on two development people only. Cosmetic extraction and visual fidelity remain experimental.",
    }
