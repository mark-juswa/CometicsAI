"""Offline subtle photo retouch: original pixels and luma, bounded skin chroma only."""
from pathlib import Path
import time

import cv2
import numpy as np

CONFIG = {"strength": 0.20, "chroma_sigma_pixels": 16.0, "maximum_chroma_code_units": 2.0,
          "inside_feather_pixels": 4.0, "minimum_common_skin": 10000,
           "maximum_rgb_code_change": 4, "maximum_luma_code_error": 0.501,
          "minimum_face_component_pixels": 15000, "maximum_secondary_face_fraction": 0.15}
LUMA = np.array([.299, .587, .114], np.float64)


def validate(image, labels):
    if (image.dtype != np.uint8 or image.shape != (512, 512, 3)
            or labels.shape != (512, 512) or not np.issubdtype(labels.dtype, np.integer)
            or labels.min() < 0 or labels.max() > 18):
        raise ValueError("Expected uint8 512-square RGB and integer labels0..18")


def primary_face(labels):
    binary=np.isin(labels,(1,2,3,4,5,6,7,10,11,12)).astype(np.uint8)
    count,components,stats,_=cv2.connectedComponentsWithStats(binary,8)
    if count<2:
        raise ValueError("No primary face")
    sizes=stats[1:,cv2.CC_STAT_AREA]
    largest=1+int(np.argmax(sizes))
    area=int(stats[largest,cv2.CC_STAT_AREA])
    if area<CONFIG["minimum_face_component_pixels"]:
        raise ValueError("Primary face too small")
    secondary=np.delete(sizes,largest-1)
    if len(secondary) and secondary.max()>area*CONFIG["maximum_secondary_face_fraction"]:
        raise ValueError("Multiple comparable face regions")
    return components==largest


def points(labels):
    result = []
    for ids in ((4,), (5,), (10, 11, 12)):
        yy, xx = np.where(np.isin(labels, ids))
        if len(xx) < 20:
            raise ValueError("Missing original/reference facial regions")
        result.append([float(np.median(xx)), float(np.median(yy))])
    if result[0][0] > result[1][0]:
        result[0], result[1] = result[1], result[0]
    if result[2][1] <= max(result[0][1], result[1][1]) + 20:
        raise ValueError("Uncertain face alignment")
    return np.asarray(result, np.float32)


def chroma(image):
    values = image.astype(np.float64)
    y = values @ LUMA
    return np.stack(((values[:, :, 0]-y)*.713, (values[:, :, 2]-y)*.564), axis=2)


def smooth_color(values, mask):
    weight = cv2.GaussianBlur(mask.astype(np.float64), (0, 0), CONFIG["chroma_sigma_pixels"])
    values = cv2.GaussianBlur(values*mask[:, :, None], (0, 0), CONFIG["chroma_sigma_pixels"])
    return values/np.maximum(weight[:, :, None], 1e-8)


def retouch(original, reference, original_labels, reference_labels):
    validate(original, original_labels)
    validate(reference, reference_labels)
    started = time.perf_counter()
    original_face, reference_face = primary_face(original_labels), primary_face(reference_labels)
    source_regions=np.where(original_face,original_labels,0).astype(np.uint8)
    reference_regions=np.where(reference_face,reference_labels,0).astype(np.uint8)
    source_points, reference_points = points(source_regions), points(reference_regions)
    matrix = cv2.getAffineTransform(source_points, reference_points)
    determinant = float(np.linalg.det(matrix[:, :2]))
    if not .5 <= determinant <= 1.8:
        raise ValueError("Unsafe color-reference alignment")
    # WARP_INVERSE_MAP samples reference coordinates for each original coordinate.
    # It never warps the original canvas or transfers regenerated texture/features.
    aligned = cv2.warpAffine(reference, matrix, (512, 512),
        flags=cv2.WARP_INVERSE_MAP | cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT_101)
    labels = cv2.warpAffine(reference_regions, matrix, (512, 512),
        flags=cv2.WARP_INVERSE_MAP | cv2.INTER_NEAREST, borderMode=cv2.BORDER_CONSTANT)
    skin = (original_labels == 1) & original_face
    common = skin & (labels == 1)
    if common.sum() < CONFIG["minimum_common_skin"]:
        raise ValueError("Insufficient common skin")
    source_color = smooth_color(chroma(original), skin)
    reference_color = smooth_color(chroma(aligned), labels == 1)
    difference = reference_color-source_color
    yy, xx = np.mgrid[:512, :512]
    sy, sx = np.where(skin)
    height = int(sy.max()-sy.min()+1)
    eye_y = float(source_points[:2, 1].mean())
    mouth_y = float(source_points[2, 1])
    neutral = common & ((yy < eye_y-.10*height) | (yy > mouth_y+.06*height))
    if neutral.sum() < 1000:
        raise ValueError("Insufficient original complexion anchors")
    # Remove the global cast. The person's overall undertone remains the baseline.
    baseline = np.median(difference[neutral], axis=0)
    difference = (difference-baseline)*CONFIG["strength"]
    magnitude = np.linalg.norm(difference, axis=2)
    difference *= np.minimum(1, CONFIG["maximum_chroma_code_units"]/np.maximum(magnitude, 1e-12))[:, :, None]
    distance = cv2.distanceTransform(skin.astype(np.uint8), cv2.DIST_L2, 5)
    t = np.clip(distance/CONFIG["inside_feather_pixels"], 0, 1)
    alpha = t*t*(3-2*t)
    alpha[~common] = 0
    difference *= alpha[:, :, None]
    # Construct an RGB color-only delta orthogonal to source luma exactly.
    red = difference[:, :, 0]/.713
    blue = difference[:, :, 1]/.564
    green = -(.299*red+.114*blue)/.587
    rgb_delta = np.stack((red, green, blue), axis=2)
    values = original.astype(np.float64)
    # Shrink only the proposed delta near gamut boundaries; never clip the original.
    scale = np.ones((512, 512), np.float64)
    for channel in range(3):
        d = rgb_delta[:, :, channel]
        upper = np.divide(255-values[:, :, channel], d, out=np.ones_like(d), where=d>0)
        lower = np.divide(values[:, :, channel], -d, out=np.ones_like(d), where=d<0)
        scale = np.minimum(scale, np.where(d>0, upper, np.where(d<0, lower, 1)))
    rgb_delta *= np.clip(scale, 0, 1)[:, :, None]
    result = original.copy()
    allowed = (alpha > 0) & (np.max(np.abs(rgb_delta), axis=2) > 1e-8)
    proposed = np.rint(values+rgb_delta)
    if not np.isfinite(proposed).all() or proposed.min() < 0 or proposed.max() > 255:
        raise RuntimeError("Invalid subtle retouch color")
    result[allowed] = proposed.astype(np.uint8)[allowed]
    difference_rgb = result.astype(np.int16)-original.astype(np.int16)
    changed = np.any(difference_rgb != 0, axis=2)
    luma_error = np.abs(difference_rgb.astype(np.float64) @ LUMA)
    if (np.any(changed & ~skin) or np.any(result[~allowed] != original[~allowed])
            or np.max(np.abs(difference_rgb)) > CONFIG["maximum_rgb_code_change"]
            or luma_error.max() > CONFIG["maximum_luma_code_error"]):
        raise RuntimeError("Original fidelity constraint violated")
    return result, allowed, {
        "generator": "beautycore_source_faithful_retouch_pilot_v2",
        "original_is_canvas": True, "generated_pixels_are_canvas": False,
        "reference_used_for": "small low-frequency chroma differences only",
        "display_geometry_warped": False, "smoothing_or_glow_applied": False,
        "changed_pixels": int(changed.sum()),
        "protected_source_pixels_changed": int((changed & ~skin).sum()),
        "non_primary_face_pixels_changed": int((changed & ~original_face).sum()),
        "maximum_rgb_code_change": int(np.abs(difference_rgb).max()),
        "maximum_luma_code_error": float(luma_error.max()),
        "mean_luma_code_error": float(luma_error.mean()),
        "global_reference_cast_removed": baseline.tolist(),
        "common_skin_pixels": int(common.sum()),
        "alignment_matrix_color_reference_only": matrix.tolist(),
        "cpu_seconds": time.perf_counter()-started,
        "limit": "Luma differs only by final8bit rounding; skin color can change slightly. Original skin RGB is not claimed identical."
    }
