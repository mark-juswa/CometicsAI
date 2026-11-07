"""Offline reference makeup application. Never imported by the live Makeup service.

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
    "stroke_sigma": 2.0,
    "stroke_contrast_start": 3.0,
    "stroke_contrast_full": 8.0,
    "placement": "full-core-soft-boundary",
    "local_contrast_sigma": 12.0,
    "eye_rim_pixels": 2.0,
    "lip_feather_pixels": 1.5,
    "texture_sigma": 1.4,
    "color_transfer": "selected-cosmetic-chroma-source-texture",
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



def full_core_support(radial):
    """Preserve the pigment interior; only its outer placement boundary fades."""
    t = np.clip((radial - 1.0) / 3.0, 0.0, 1.0)
    return (1.0 - t * t * (3.0 - 2.0 * t)).astype(np.float32)


def stroke_coverage(reference_lightness):
    """Read actual narrow dark reference strokes; do not invent new lashes."""
    background = cv2.GaussianBlur(
        reference_lightness, (0, 0), CONFIG["stroke_sigma"]
    )
    contrast = np.maximum(0.0, background - reference_lightness)
    span = CONFIG["stroke_contrast_full"] - CONFIG["stroke_contrast_start"]
    return ramp(contrast - CONFIG["stroke_contrast_start"], span)


def reference_dark_target(source_lab, reference_lab, source_neutral,
                          reference_neutral, stroke):
    """Transfer local dark cosmetic contrast without importing pale complexion.

    Broad cosmetic shading retains source fine detail. Actual opaque strokes
    use reference detail. Identical inputs give the original lightness.
    """
    ratio = source_neutral[:, :, 0] / np.maximum(reference_neutral[:, :, 0], 1.0)
    # Preserve existing source eye depth. Borrowing the entire selected
    # shadow relative to clean skin darkened already shaded eyelids twice.
    local_sigma = CONFIG["local_contrast_sigma"]
    reference_contrast = np.maximum(
        0.0, cv2.GaussianBlur(reference_lab[:, :, 0], (0, 0), local_sigma)
        - reference_lab[:, :, 0],
    )
    source_contrast = np.maximum(
        0.0, cv2.GaussianBlur(source_lab[:, :, 0], (0, 0), local_sigma)
        - source_lab[:, :, 0],
    )
    broad = source_lab[:, :, 0] - np.maximum(0.0, reference_contrast - source_contrast)
    fine = reference_lab[:, :, 0] * ratio
    return broad * (1.0 - stroke) + fine * stroke


def cosmetic_chroma_field(source_lab, reference_lab, alpha, transition_sigma, valid=None):
    """Match selected cosmetic hue while retaining source fine color detail.

    Adding a pigment residual to warm source skin shifted the chosen hue.
    Cosmetic coverage now mixes the actual selected chroma, not a new palette.
    This function never changes source lightness.
    """
    sigma = CONFIG["texture_sigma"]
    src_ab = source_lab[:, :, 1:]
    ref_ab = reference_lab[:, :, 1:]
    if valid is None:
        source_smooth = cv2.GaussianBlur(src_ab, (0, 0), sigma)
        reference_smooth = cv2.GaussianBlur(ref_ab, (0, 0), sigma)
    else:
        # Warp padding is not cosmetic data. Compare both references over the
        # same valid face domain so black padding cannot tint its boundary.
        if valid.shape != alpha.shape or not np.any(valid):
            raise ValueError("Missing valid reference domain")
        source_smooth = normalized(src_ab, valid, sigma)
        reference_smooth = normalized(ref_ab, valid, sigma)
    target = reference_smooth + (src_ab - source_smooth)
    return cv2.GaussianBlur(
        (target - src_ab) * alpha[:, :, None], (0, 0), transition_sigma
    )


def eyelid_support(points, upper, lower, brow):
    """Confine pigment to the eyelid and crease, fading before the brow bone."""
    yy, xx = np.mgrid[:512, :512]
    x = np.arange(512)
    upper_y = np.interp(x, upper[:, 0], upper[:, 1])[None, :]
    lower_y = np.interp(x, lower[:, 0], lower[:, 1])[None, :]
    brow_y = np.interp(x, brow[:, 0], brow[:, 1])[None, :]
    gap = np.maximum(upper_y - brow_y, 5.0)
    height = (upper_y - yy) / gap
    fade = np.clip((height - 0.40) / 0.45, 0.0, 1.0)
    vertical = 1.0 - fade * fade * (3.0 - 2.0 * fade)
    below = np.clip((lower_y + 4.0 - yy) / 4.0, 0.0, 1.0)
    width = float(upper[-1, 0] - upper[0, 0])
    center = float((upper[0, 0] + upper[-1, 0]) / 2)
    side = np.clip((np.abs(xx - center) / max(width / 2, 1) - 0.80) / 0.45, 0.0, 1.0)
    horizontal = 1.0 - side * side * (3.0 - 2.0 * side)
    return (vertical * below * horizontal).astype(np.float32)

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
        support = full_core_support(radial) * skin
        cheek_support = np.maximum(cheek_support, support)
    source_color_residual = src[:, :, 1:] - src_base[:, :, 1:]
    color, alpha = blush_layer(ref, ref_base, cheek_support, source_color_residual)
    pigment_field = cosmetic_chroma_field(
        src, ref, alpha, CONFIG["blush_transition_sigma"], valid
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
    actual_strokes = stroke_coverage(ref[:, :, 0])
    for upper, lower, brow in eyes:
        boundary = np.vstack((brow + [0, 2], (lower + [0, 3])[::-1]))
        geometry = polygon(boundary)
        outer = cv2.dilate(
            geometry.astype(np.uint8),
            cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11)),
        ) > 0
        # Eyelid cosmetics do not fill the entire gap up to the eyebrow.
        # Taper across the crease before reaching the natural brow bone.
        matte = eyelid_support(points, upper, lower, brow)
        eligible = face & valid & ~eye_core & np.isin(source_labels, (1, 4, 5))
        matte[~eligible] = 0
        # Neutral samples surround the cosmetic extent rather than borrowing
        # the shaded jaw as the eyelid's underlying complexion.
        exclusion = cv2.dilate(outer.astype(np.uint8), np.ones((17, 17), np.uint8)) > 0
        local_neutral = common & ~exclusion
        local_ref = normalized(ref, local_neutral, 12.0)
        local_src = normalized(src, local_neutral, 12.0)
        incremental_color = (ref[:, :, 1:] - local_ref[:, :, 1:]) - (src[:, :, 1:] - local_src[:, :, 1:])
        # For these selected rose/brown shadows, red-axis excess identifies
        # pigment. A pale foundation patch must not fill the whole eye region.
        selected_pigment = np.maximum(0.0, ref[:, :, 1] - local_ref[:, :, 1])
        color_alpha = matte * skin * ramp(selected_pigment, 4.0)
        field = cosmetic_chroma_field(src, ref, color_alpha, 1.5, valid)
        field[~skin] = 0
        output[:, :, 1:] += field
        # Fine cosmetic cores need not share the color field's edge fade.
        # Their locations and coverage come from the selected reference.
        stroke = actual_strokes * inside(outer, 1.0)
        stroke[~eligible] = 0
        target_lightness = reference_dark_target(src, ref, local_src, local_ref, stroke)
        extra_dark = np.maximum(0.0, src[:, :, 0] - target_lightness)
        dark_alpha = np.maximum(matte, stroke) * ramp(extra_dark, 2.0)
        output[:, :, 0] -= extra_dark * dark_alpha
        masks["eyeshadow"] = np.maximum(masks["eyeshadow"], color_alpha)
        masks["lash_liner"] = np.maximum(masks["lash_liner"], dark_alpha)

    # Brow outline remains the source outline. Pigment is bounded inward.
    brow = np.isin(source_labels, (6, 7)) & face & valid
    # Feather both source and reference boundaries, not a hard intersection.
    alpha = inside(brow, 3) * inside(np.isin(ref_labels, (6, 7)), 3)
    ref_brow = np.isin(ref_labels, (6, 7)) & valid
    source_brow = normalized(src, brow, 1.0)
    reference_brow = normalized(ref, ref_brow, 1.0)
    target_brow = reference_brow + (src - source_brow)
    # Do not brighten source brows or paint a pale selected boundary. Deposit
    # the selected dark pigment only where it actually increases brow density.
    darker = np.maximum(0.0, src[:, :, 0] - target_brow[:, :, 0])
    alpha *= ramp(darker, 8.0)
    target_brow[:, :, 0] = np.minimum(src[:, :, 0], target_brow[:, :, 0])
    # Source brow hairs retain their hue. Only their selected dark pigment
    # density changes; copying pale/cool edge color created a grey outline.
    density = np.clip(target_brow[:, :, 0] / np.maximum(src[:, :, 0], 1.0), 0, 1)
    brow_rgb = original.astype(np.float32) / 255 * density[:, :, None]
    target_brow = cv2.cvtColor(brow_rgb, cv2.COLOR_RGB2LAB)
    output = output * (1 - alpha[:, :, None]) + target_brow * alpha[:, :, None]
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
    # A final one-code RGB conversion error must not brighten a brow edge.
    result[brow] = np.minimum(result[brow], original[brow])
    if np.any(result[~allowed] != original[~allowed]):
        raise RuntimeError("Protected source pixels changed")
    return result, masks, {
        "generator": "beautycore_reference_makeup_application_v4_1",
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
