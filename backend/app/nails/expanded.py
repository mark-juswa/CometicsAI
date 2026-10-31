"""Source-preserving Nails finishes ported from STYLE-EXP-001.

Implementation does not imply appearance approval. Public availability is owned
by the versioned style release; these functions never call a generative model.
"""

import numpy as np
from PIL import Image, ImageFilter

from app.nails.geometry import nail_components

PROFILE_ID = "nails-expanded-v1"
STYLE_IDS = frozenset(("exp_raspberry_jelly", "exp_pink_aura", "exp_negative_space_microdots"))


def render_expanded(source, mask_image, style_id):
    if style_id not in STYLE_IDS:
        raise ValueError("Unsupported expanded nail style")
    source = source.convert("RGB")
    if mask_image.size != source.size:
        raise ValueError("Mask dimensions differ")
    original = np.asarray(source)
    mask = np.asarray(mask_image.convert("L")) > 127
    components = nail_components(mask)
    if not 3 <= len(components) <= 5 or mask.sum() > mask.size * .12:
        raise ValueError("Use a mask with three to five separate nails")
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
        raise RuntimeError("Expanded renderer changed pixels outside the mask")
    return Image.fromarray(output)
