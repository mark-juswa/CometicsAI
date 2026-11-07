"""Automatic cosmetic coverage and source lighting materials, offline only.

No face generation, source warp or artist assets. Probability and reference
texture inputs require their original image/model provenance at the runner.
"""
import cv2
import numpy as np

from scripts.makeup_surface_application import lip_coverage, palette
from scripts.makeup_source_faithful_retouch import validate, primary_face
from scripts.makeup_source_render import gamut_safe
from scripts.makeup_selected_cosmetics import linear, srgb, polygon
from scripts.makeup_alignment_pilot import CHAINS

# Additional material intent, shared across all original people. Color and
# pigment doses remain in the existing catalog application. These are review
# defaults, not externally authored assets or an expansion of supported styles.
# Lip finish, observed lash amount, eyelid reflection amount, skin shine deltaL.
STYLE_MATERIALS = {
    "natural_makeup": ("satin", .10, 0., 0.),
    "no_makeup_makeup": ("satin", 0., 0., 0.),
    "soft_glam": ("satin", .25, 0., 0.),
    "smoky_glam": ("satin", .65, 0., 0.),
    "dewy_peach": ("gloss", .1, 0., 3.),
    "rosy_pink": ("satin", .1, 0., 0.),
    "bronze_golden_glam": ("satin", .35, .6, 0.),
    "matte_nude": ("matte", .1, 0., -3.),
    "classic_red_lip": ("satin", .1, 0., 0.),
    "bold_evening_glam": ("satin", .75, 0., 0.),
    "exp_cloud_berry_lips": ("blurred_matte", .1, 0., -2.),
    "exp_manga_lash": ("gloss", .95, 0., 0.),
    "exp_icy_silver": ("satin", .5, .9, 0.),
}


def smoothstep(value):
    t = np.clip(value, 0, 1)
    return t * t * (3 - 2 * t)


def guided_probability(image, probability, radius=3, epsilon=(5 / 255) ** 2):
    """Local RGB regression refines a field, never blurs the source canvas."""
    if (image.shape != (512, 512, 3) or image.dtype != np.uint8
            or probability.shape != (512, 512) or not np.isfinite(probability).all()
            or np.any((probability < 0) | (probability > 1))):
        raise ValueError("Expected source RGB and finite source probability")
    guide = image.astype(np.float32) / 255
    p = probability.astype(np.float32)
    window = (radius * 2 + 1, radius * 2 + 1)
    mean = lambda value: cv2.boxFilter(value, -1, window, borderType=cv2.BORDER_REFLECT)
    mean_i, mean_p = mean(guide), mean(p)
    covariance = np.empty((512, 512, 3, 3), np.float32)
    for i in range(3):
        for j in range(3):
            covariance[:, :, i, j] = mean(guide[:, :, i] * guide[:, :, j]) - mean_i[:, :, i] * mean_i[:, :, j]
        covariance[:, :, i, i] += epsilon
    ip = mean(guide * p[:, :, None]) - mean_i * mean_p[:, :, None]
    a = np.linalg.solve(covariance, ip[..., None])[..., 0]
    b = mean_p - np.sum(a * mean_i, axis=2)
    result = np.sum(mean(a) * guide, axis=2) + mean(b)
    return np.clip(result, 0, 1).astype(np.float32)


def source_lip_matte(original, labels, points, probability, blurred=False):
    _, support, agreement = lip_coverage(labels, points)
    refined = guided_probability(original, probability)
    distance = cv2.distanceTransform(support.astype(np.uint8), cv2.DIST_L2, 5)
    # Confidence plus a photographic edge replaces the old one pixel hole and
    # fixed three pixel erosion, which consumed much of a narrow upper lip.
    edge = smoothstep(distance / (3.0 if blurred else 1.5))
    alpha = refined * edge
    alpha[~support] = 0
    if np.count_nonzero(alpha > .7) < 40:
        raise ValueError("Insufficient confident source lip surface")
    return alpha.astype(np.float32), support, agreement


def lip_material(original, reference, labels, ref_labels, points, probability, finish="satin"):
    """A single pigment hue with source tone order and existing highlight detail.

    Local shadow protection avoids both one dark pixel limiting the whole lip
    and direct reproduction of an unnaturally dark reference mouth.
    No reference shading or lip geometry is imported.
    """
    validate(original, labels)
    validate(reference, ref_labels)
    if finish not in {"satin", "gloss", "matte", "blurred_matte"}:
        raise ValueError("Unknown lip finish")
    alpha, support, agreement = source_lip_matte(original, labels, points, probability, finish == "blurred_matte")
    selected = palette(reference, ref_labels)
    source_color = palette(original, labels)
    if np.array_equal(selected, source_color) and finish == "satin":
        return original.copy(), alpha, {"method": "source-guided-material-v1", "palette_no_change": True,
                                         "contour_agreement": agreement, "finish": finish}
    source_lab = cv2.cvtColor(original.astype(np.float32) / 255, cv2.COLOR_RGB2LAB)
    core = alpha > .7
    anchor = float(np.median(source_lab[:, :, 0][core]))
    chosen_lightness = float(np.clip(selected[0], .5, 99.5))
    target = source_lab.copy()
    # No source spatial filtering: retain the lightness gradient except where
    # the local shadow guard prevents a dark target from crushing lip detail.
    offset = float(np.clip(chosen_lightness - source_color[0], -20, 12))
    delta = np.maximum(offset, -.4 * source_lab[:, :, 0])
    target[:, :, 0] += delta
    target[:, :, 1:] = selected[1:]
    chroma = np.linalg.norm(source_lab[:, :, 1:], axis=2)
    median_c = max(float(np.median(chroma[core])), 1)
    q80, q98 = np.quantile(source_lab[:, :, 0][core], [.8, .98])
    existing_shine = smoothstep((source_lab[:, :, 0] - q80) / max(q98 - q80, 3))
    existing_shine *= smoothstep((median_c - chroma) / median_c)
    if finish in {"matte", "blurred_matte"}:
        target[:, :, 0] -= np.minimum(6, np.maximum(target[:, :, 0] - chosen_lightness, 0) * .3) * existing_shine
    else:
        preserve = existing_shine * (1.0 if finish == "satin" else 1.3)
        preserve = np.minimum(preserve, 1)
        target[:, :, 0] += preserve * (source_lab[:, :, 0] - target[:, :, 0])
        target[:, :, 1:] *= (1 - preserve[:, :, None])
        if finish == "gloss":
            target[:, :, 0] += 3 * existing_shine
    allowed = alpha > 0
    target, compressed = gamut_safe(target, allowed)
    # Blend the requested material in Lab without transferring reference skin.
    lab = source_lab * (1 - alpha[:, :, None]) + target * alpha[:, :, None]
    lab, compressed_blend = gamut_safe(lab, allowed)
    converted = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
    baseline = cv2.cvtColor(source_lab, cv2.COLOR_LAB2RGB)
    proposed = original.astype(np.float32) / 255 + converted - baseline
    result = original.copy()
    result[allowed] = np.rint(np.clip(proposed[allowed], 0, 1) * 255).astype(np.uint8)
    return result, alpha, {"method": "source-guided-material-v3", "contour_agreement": agreement,
                           "finish": finish, "selected_palette_lab": selected.tolist(),
                           "source_anchor_lightness": anchor, "bounded_lightness_offset": offset,
                           "gamut_compressed_pixels": compressed + compressed_blend,
                           "reference_spatial_shading_used": False, "source_texture_blurred": False,
                           "outside_lip_changed_pixels": int(np.any(result != original, axis=2)[~support].sum())}


def eye_curves(points, topology):
    """Return left to right source/reference upper opening, lower and brow."""
    if topology not in {68, 478}:
        raise ValueError("Unknown landmark topology")
    points = np.asarray(points, np.float32)
    if topology == 68:
        if points.shape != (68, 2) or not np.isfinite(points).all():
            raise ValueError("Expected true68landmarks")
        chains = [([36, 37, 38, 39], [36, 41, 40, 39], [17, 18, 19, 20, 21]),
                  ([42, 43, 44, 45], [42, 47, 46, 45], [22, 23, 24, 25, 26])]
    else:
        if points.shape != (478, 3) or not np.isfinite(points).all():
            raise ValueError("Expected source478landmarks")
        points = points[:, :2] * 512
        chains = [(CHAINS[side + "_upper"], CHAINS[side + "_lower"], CHAINS[side + "_brow_lower"])
                  for side in ("right", "left")]
    result = []
    for indexes in chains:
        curves = [points[chain].copy() for chain in indexes]
        curves = [curve[np.argsort(curve[:, 0])] for curve in curves]
        if np.ptp(curves[0][:, 0]) < 18:
            raise ValueError("Insufficient eye anatomy")
        result.append(curves)
    return sorted(result, key=lambda row: row[0][:, 0].mean())


def register_lash_root(image, upper):
    """Find a continuous dark lid margin near the supplied anatomical curve."""
    intensity = image.astype(np.float32).mean(axis=2) / 255
    xs = np.arange(int(np.ceil(upper[0, 0])), int(np.floor(upper[-1, 0])) + 1)
    expected = np.interp(xs, upper[:, 0], upper[:, 1])
    shifts = np.arange(-3, 4)
    ys = np.clip(np.rint(expected[:, None] + shifts).astype(int), 0, 511)
    unary = intensity[ys, xs[:, None]] + .055 * shifts[None, :] ** 2
    cost = unary[0].copy()
    parents = []
    transition = .12 * (shifts[:, None] - shifts[None, :]) ** 2
    for row in unary[1:]:
        alternatives = cost[:, None] + transition
        parent = np.argmin(alternatives, axis=0)
        cost = row + alternatives[parent, np.arange(len(shifts))]
        parents.append(parent)
    path = [int(np.argmin(cost))]
    for parent in parents[::-1]:
        path.append(int(parent[path[-1]]))
    path = path[::-1]
    return np.column_stack((xs, expected + shifts[path])).astype(np.float32)


def reference_eye_materials(reference, labels, ref_points):
    """Matte actual reference strokes/glints, never draw synthetic lash hairs."""
    validate(reference, labels)
    y = linear(reference.astype(np.float32) / 255) @ np.array([.2126, .7152, .0722], np.float32)
    yy, xx = np.mgrid[:512, :512]
    lash = np.zeros((512, 512), np.float32)
    glint = np.zeros_like(lash)
    eyes = eye_curves(ref_points, 68)
    for upper, lower, brow in eyes:
        upper = register_lash_root(reference, upper)
        width = float(np.ptp(upper[:, 0]))
        top = np.interp(np.arange(512), upper[:, 0], upper[:, 1])[None, :]
        brow_line = np.interp(np.arange(512), brow[:, 0], brow[:, 1])[None, :]
        horizontal = (xx > upper[0, 0] - width * .12) & (xx < upper[-1, 0] + width * .12)
        band = horizontal & (yy < top + 2) & (yy > np.maximum(brow_line + 3, top - width * .4))
        band &= ~np.isin(labels, (0, 6, 7, 10, 11, 12, 13))
        size = max(5, int(round(width * .08)) | 1)
        close = cv2.morphologyEx(y, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (size, size)))
        dark = np.clip((close - y) / np.maximum(close, .015), 0, 1).astype(np.float32)
        dark *= band
        # Attached observed foreground only. Isolated dark skin/eyeshadow specks
        # cannot become free floating lashes.
        count, components = cv2.connectedComponents((dark > .12).astype(np.uint8), 8)
        attached = np.zeros_like(band)
        roots = np.abs(yy - top) < 3
        for component in range(1, count):
            region = components == component
            if np.any(region & roots) and np.count_nonzero(region) >= 3:
                attached |= region
        lash = np.maximum(lash, dark * cv2.dilate(attached.astype(np.uint8), np.ones((3, 3), np.uint8)))
        # Small bright details are sampled from the existing guide's cosmetic
        # surface. The spatial base/foundation and entire face are not copied.
        opening = cv2.morphologyEx(y, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (13, 13)))
        shine = np.clip((y - opening) / np.maximum(1 - opening, .05), 0, 1)
        lid = horizontal & (yy < top - 1) & (yy > brow_line + 4) & (labels == 1)
        glint = np.maximum(glint, (shine * lid).astype(np.float32))
    return {"lash": lash.astype(np.float32), "glint": glint.astype(np.float32)}


def fit_eye_material(field, source_points, reference_points, source_labels, kind,
                     source_image=None, reference_image=None):
    """Fit an alpha ribbon to the original opening. Source RGB never warps."""
    if (field.shape != (512, 512) or not np.isfinite(field).all()
            or np.any((field < 0) | (field > 1)) or kind not in {"lash", "glint"}):
        raise ValueError("Invalid reference material matte")
    yy, xx = np.mgrid[:512, :512]
    result = np.zeros((512, 512), np.float32)
    core = np.zeros((512, 512), np.uint8)
    for source, reference in zip(eye_curves(source_points, 478), eye_curves(reference_points, 68)):
        upper, lower, brow = source
        ref_upper, _, ref_brow = reference
        original_upper = upper.copy()
        if source_image is not None:
            upper = register_lash_root(source_image, upper)
        if reference_image is not None:
            ref_upper = register_lash_root(reference_image, ref_upper)
        width, ref_width = float(np.ptp(upper[:, 0])), float(np.ptp(ref_upper[:, 0]))
        u = (xx - upper[0, 0]) / width
        mapped_x = ref_upper[0, 0] + u * ref_width
        src_y = np.interp(np.arange(512), upper[:, 0], upper[:, 1])[None, :]
        ref_y = np.interp(mapped_x.ravel(), ref_upper[:, 0], ref_upper[:, 1]).reshape(512, 512)
        if kind == "lash":
            mapped_y = ref_y + (yy - src_y) * ref_width / width
        else:
            src_brow = np.interp(np.arange(512), brow[:, 0], brow[:, 1])[None, :]
            ref_brow_y = np.interp(mapped_x.ravel(), ref_brow[:, 0], ref_brow[:, 1]).reshape(512, 512)
            t = (yy - src_y) / np.minimum(src_brow - src_y, -5)
            mapped_y = ref_y + t * (ref_brow_y - ref_y)
        warped = cv2.remap(field, mapped_x.astype(np.float32), mapped_y.astype(np.float32), cv2.INTER_LINEAR,
                           borderMode=cv2.BORDER_CONSTANT)
        brow_line = np.interp(np.arange(512), brow[:, 0], brow[:, 1])[None, :]
        valid = (u > -.1) & (u < 1.1) & (yy <= src_y + .5) & (yy > brow_line + 2)
        if kind == "glint":
            # Reflective material belongs on the mobile lid, not the brow bone.
            gap = np.maximum(src_y - brow_line, 6)
            height = (src_y - yy) / gap
            warped *= smoothstep((.58 - height) / .22) * smoothstep((height - .03) / .1)
            warped *= smoothstep((u + .02) / .14) * smoothstep((1.02 - u) / .14)
        warped *= valid
        result = np.maximum(result, warped)
        core |= polygon(np.vstack((original_upper, lower[::-1]))).astype(np.uint8)
    # Explicit opening protection is independent of parser rim disagreements.
    if kind == "lash":
        # Mascara may occlude the original lid margin, not the inner eye.
        core = cv2.erode(core, np.ones((3, 3), np.uint8)) > 0
    else:
        core = cv2.dilate(core, np.ones((3, 3), np.uint8)) > 0
    result[core | ~np.isin(source_labels, (1, 4, 5))] = 0
    result[~primary_face(source_labels)] = 0
    return result.astype(np.float32), core


def cluster_reference_lashes(donor, donor_points, style_field, style_points):
    """Select observed donor strands using the selected look's cluster spacing.

    No new hair strokes are drawn. Failed AI guide lash shapes are not copied.
    This does not guarantee faithful Manga cluster convergence.
    """
    result = donor.copy()
    for detail, style in zip(eye_curves(donor_points, 68), eye_curves(style_points, 68)):
        upper, _, _ = detail
        guide, _, _ = style
        xs = np.arange(512)
        profile = style_field.sum(axis=0)
        # Small photographic antialiasing, not a density or opacity sweep.
        profile = cv2.GaussianBlur(profile[None, :], (0, 0), .8)[0]
        selected = (xs >= guide[0, 0]) & (xs <= guide[-1, 0])
        scale = max(float(np.quantile(profile[selected], .9)), 1e-5)
        mapped = guide[0, 0] + (xs - upper[0, 0]) / np.ptp(upper[:, 0]) * np.ptp(guide[:, 0])
        modulation = .35 + .65 * np.clip(np.interp(mapped, xs, profile) / scale, 0, 1)
        region = (xs >= upper[0, 0] - .1 * np.ptp(upper[:, 0])) & (xs <= upper[-1, 0] + .1 * np.ptp(upper[:, 0]))
        result[:, region] *= modulation[region]
    return result


def source_finish(original, current, labels, region, delta_lightness):
    """Change only evidenced existing shine; no pore filtering or foundation."""
    validate(original, labels)
    validate(current, labels)
    if (region.shape != (512, 512) or not np.isfinite(region).all()
            or np.any((region < 0) | (region > 1))
            or not np.isfinite(delta_lightness) or abs(delta_lightness) > 3):
        raise ValueError("Invalid source finish coverage or strength")
    eligible = (labels == 1) & primary_face(labels) & (region > 0)
    if np.count_nonzero(eligible) < 100 or delta_lightness == 0:
        return current.copy(), np.zeros((512, 512), np.float32)
    source = original.astype(np.float32) / 255
    luminance = linear(source) @ np.array([.2126, .7152, .0722], np.float32)
    broad = cv2.GaussianBlur(luminance, (0, 0), 5)
    surrounding = cv2.GaussianBlur(luminance, (0, 0), 20)
    saturation = (source.max(axis=2) - source.min(axis=2)) / np.maximum(source.max(axis=2), .01)
    score = np.maximum(broad - surrounding, 0) * (1 - saturation)
    lower, upper = np.quantile(score[eligible], [.9, .995])
    weight = smoothstep((score - lower) / max(float(upper - lower), .005))
    distance = cv2.distanceTransform(eligible.astype(np.uint8), cv2.DIST_L2, 5)
    weight *= smoothstep(distance / 4) * np.clip(region, 0, 1)
    weight[~eligible] = 0
    lab = cv2.cvtColor(current.astype(np.float32) / 255, cv2.COLOR_RGB2LAB)
    target = lab.copy(); target[:, :, 0] += weight * delta_lightness
    allowed = weight > 0
    target, _ = gamut_safe(target, allowed)
    converted = cv2.cvtColor(target, cv2.COLOR_LAB2RGB)
    baseline = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
    result = current.copy()
    delta = converted - baseline
    result[allowed] = np.rint(np.clip(current[allowed].astype(np.float32) / 255 + delta[allowed], 0, 1) * 255).astype(np.uint8)
    return result, weight.astype(np.float32)


def refine_materials(original, reference, labels, ref_labels, points, previous,
                     masks, style_id, context, lip_dose):
    """Optional offline material stage on the existing automatic application."""
    if style_id not in STYLE_MATERIALS:
        raise ValueError("Unknown cosmetic material style")
    finish, lash_dose, reflection_dose, shine_delta = STYLE_MATERIALS[style_id]
    result, lip_alpha, lip_metrics = lip_material(original, reference, labels, ref_labels, points,
                                                context["lip_probability"], finish)
    result = np.rint(original.astype(np.float32) + lip_dose * (result.astype(np.float32) - original)).clip(0, 255).astype(np.uint8)
    # Retain the existing learned eye/blush application, replacing only lips.
    old_lip = masks["lip"] > 0
    new_lip = lip_alpha > 0
    result[~(old_lip | new_lip)] = previous[~(old_lip | new_lip)]
    detail, detail_labels, detail_points = context["detail_image"], context["detail_labels"], context["detail_points68"]
    observed = reference_eye_materials(detail, detail_labels, detail_points)
    if style_id == "exp_manga_lash":
        selected = reference_eye_materials(reference, ref_labels, context["reference_points68"])
        observed["lash"] = cluster_reference_lashes(observed["lash"], detail_points, selected["lash"], context["reference_points68"])
    lash, core = fit_eye_material(observed["lash"], points, detail_points, labels, "lash", original, detail)
    lash *= lash_dose
    rgb = linear(result.astype(np.float32) / 255)
    rgb *= 1 - lash[:, :, None]
    reflection = np.zeros_like(lash)
    if reflection_dose:
        reflection, reflection_core = fit_eye_material(observed["glint"], points, detail_points, labels, "glint", original, detail)
        reflection = cv2.GaussianBlur(reflection, (0, 0), .65)
        reflection[reflection_core | (labels != 1)] = 0
        reflection *= reflection_dose
        # Selected metallic family, not donor skin chroma or whole lid shading.
        color = np.array([.85, .9, 1] if style_id == "exp_icy_silver" else [1, .78, .4], np.float32)
        rgb = rgb * (1 - reflection[:, :, None]) + color * reflection[:, :, None]
    effect = (lash > 0) | (reflection > 0)
    converted = np.rint(np.clip(srgb(rgb), 0, 1) * 255).astype(np.uint8)
    result[effect] = converted[effect]
    region = masks["cheek"].copy() if shine_delta > 0 else np.ones((512, 512), np.float32)
    region[core | old_lip | new_lip] = 0
    result, shine = source_finish(original, result, labels, region, shine_delta)
    combined = {**masks, "lip": lip_alpha, "lash": lash, "reflection": reflection, "finish": shine}
    union = np.logical_or.reduce([mask > 0 for mask in combined.values()])
    changed = np.any(result != original, axis=2)
    protected = changed & (~union | np.isin(labels, (0, 2, 3, 6, 7, 8, 9, 10, 13, 14, 15, 16, 17, 18)) | core)
    if np.any(protected):
        raise RuntimeError("Cosmetic materials changed a protected source region")
    return result, combined, {"material_version": "automatic-source-material-v3",
        "production_enabled": False, "source_is_canvas": True,
        "artist_required": False, "lip_component": lip_metrics,
        "protected_changed_pixels": int(protected.sum()),
        "eye_core_changed_pixels": int((changed & core).sum()),
        "eye_semantic_rim_changed_pixels": int((changed & np.isin(labels, (4, 5))).sum()),
        "brow_changed_pixels": int((changed & np.isin(labels, (6, 7))).sum()),
        "lip_style_dose": lip_dose, "skin_shine_max_deltaL": shine_delta,
        "skin_shine_coverage_pixels": int((shine > 0).sum()),
        "source_spatially_smoothed": False, "donor_face_rgb_copied": False,
        "region_changed_pixels": {key: int((changed & (mask > 0)).sum()) for key, mask in combined.items()},
        "full_look_quality": "NEEDS VERIFICATION"}
