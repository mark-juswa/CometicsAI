"""Offline source-referenced complexion field; no serving or new diffusion."""
from pathlib import Path
import time

import cv2
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve

CONFIG = {"grid_size": 64, "anchor_weight": 2.0, "minimum_anchor_cells": 24,
          "maximum_lightness_reduction": 35.0, "maximum_lightness_increase": 15.0,
          "maximum_chroma_offset": 22.0, "field_blur_sigma": 4.0,
          "domain_margin_pixels": 8, "boundary_blur_sigma": 3.0,
          "protection": "inner-eyes-and-neutral-teeth-only"}
EDIT_LABELS = (1, 2, 6, 7)
PROTECTED_LABELS = (0, 3, 4, 5, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18)


def validate(rgb, labels):
    if (rgb.dtype != np.uint8 or rgb.shape != (512, 512, 3)
            or labels.shape != (512, 512) or not np.issubdtype(labels.dtype, np.integer)
            or labels.min() < 0 or labels.max() > 18):
        raise ValueError("Expected uint8 RGB and integer 512-square labels0..18")


def centers(labels):
    points = []
    for ids in ((4,), (5,), (10, 11, 12)):
        yy, xx = np.where(np.isin(labels, ids))
        if len(xx) < 20:
            raise ValueError("Missing eye/mouth alignment region")
        points.append([float(np.median(xx)), float(np.median(yy))])
    if points[0][0] > points[1][0]:
        points[0], points[1] = points[1], points[0]
    if points[2][1] <= max(points[0][1], points[1][1]) + 20:
        raise ValueError("Invalid facial region ordering")
    return np.asarray(points, np.float32)


def normalized_skin_blur(values, skin):
    weight = cv2.GaussianBlur(skin.astype(np.float32), (0, 0), 3)
    result = cv2.GaussianBlur(values * skin[:, :, None], (0, 0), 3)
    return result / np.maximum(weight[:, :, None], 1e-5)


def complexion(source, raw, source_labels, raw_labels):
    validate(source, source_labels)
    validate(raw, raw_labels)
    started = time.perf_counter()
    original_points, generated_points = centers(source_labels), centers(raw_labels)
    matrix = cv2.getAffineTransform(original_points, generated_points)
    determinant = float(np.linalg.det(matrix[:, :2]))
    if not 0.5 <= determinant <= 1.8:
        raise ValueError("Face alignment scale is unsafe")
    # Warp only the color reference and its labels. The output geometry is never warped.
    reference = cv2.warpAffine(source, matrix, (512, 512), flags=cv2.INTER_LINEAR,
                               borderMode=cv2.BORDER_REFLECT_101)
    reference_labels = cv2.warpAffine(source_labels.astype(np.uint8), matrix, (512, 512),
                                      flags=cv2.INTER_NEAREST, borderMode=cv2.BORDER_CONSTANT)
    original_skin = np.isin(reference_labels, (1, 2, 8, 9, 17))
    generated_skin = np.isin(raw_labels, (1, 2, 8, 9, 17))
    yy, xx = np.mgrid[:512, :512]
    sy, sx = np.where(np.isin(raw_labels, (1, 2)))
    if len(sx) < 5000:
        raise ValueError("Insufficient generated skin")
    left, right, top, bottom = sx.min(), sx.max(), sy.min(), sy.max()
    width, height = right-left+1, bottom-top+1
    eye_y = float(generated_points[:2, 1].mean())
    mouth_y = float(generated_points[2, 1])
    forehead = yy < eye_y - .10*height
    temples = ((xx < left + .16*width) | (xx > right - .16*width)) & (yy < mouth_y - .10*height)
    jaw = yy > mouth_y + .06*height
    neutral = original_skin & generated_skin & (forehead | temples | jaw | (raw_labels == 17))
    # Exclude small feature-boundary contamination from estimation only. This does
    # not create the wide uncorrected output rings of the rejected skin-only mask.
    joint = cv2.erode((original_skin & generated_skin).astype(np.uint8),
                      np.ones((3, 3), np.uint8)) > 0
    neutral &= joint
    if neutral.sum() < 1000:
        raise ValueError("Insufficient common neutral skin")
    original_lab = cv2.cvtColor(reference.astype(np.float32)/255, cv2.COLOR_RGB2LAB)
    raw_lab = cv2.cvtColor(raw.astype(np.float32)/255, cv2.COLOR_RGB2LAB)
    original_base = normalized_skin_blur(original_lab, original_skin)
    raw_base = normalized_skin_blur(raw_lab, generated_skin)
    delta = original_base - raw_base
    # Trim extremes in each source, rather than fitting highlights/black shadows.
    for values in (original_lab[:, :, 0], raw_lab[:, :, 0]):
        low, high = np.quantile(values[neutral], (.10, .90))
        neutral &= (values >= low) & (values <= high)
    size = CONFIG["grid_size"]
    # A filled face hull includes skin misclassified as hair. Include neck/ears
    # as their own color anchors so the field tends to their measured near-zero
    # offset, instead of stopping abruptly at the jaw. No separate lip island.
    face_points = np.column_stack(np.where(np.isin(raw_labels, (1, 2, 4, 5, 6, 7, 10, 11, 12))))[:, ::-1]
    face = np.zeros((512,512), np.uint8)
    cv2.fillConvexPoly(face, cv2.convexHull(face_points.astype(np.int32)), 1)
    face[np.isin(raw_labels, (8, 9, 17))] = 1
    margin = CONFIG["domain_margin_pixels"]
    face = cv2.dilate(face, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2*margin+1,2*margin+1)))
    alpha = cv2.GaussianBlur(face.astype(np.float32), (0,0), CONFIG["boundary_blur_sigma"])
    # Protection fades inside actual eye interiors, not across surrounding skin.
    eye_core = cv2.erode(np.isin(raw_labels,(4,5)).astype(np.uint8),np.ones((3,3),np.uint8))
    eye_guard = cv2.GaussianBlur(eye_core.astype(np.float32),(0,0),.6)
    alpha *= 1-eye_guard
    teeth = (raw_labels==10).astype(np.float32)
    chroma = np.linalg.norm(raw_lab[:,:,1:],axis=2)
    teeth *= np.clip((raw_lab[:,:,0]-55)/20,0,1)*np.clip((18-chroma)/8,0,1)
    alpha *= 1-teeth
    allowed = alpha > 1e-6
    coarse = cv2.resize(face, (size, size), interpolation=cv2.INTER_AREA) > 0
    indices = np.full((size, size), -1, np.int32)
    indices[coarse] = np.arange(int(coarse.sum()))
    anchor = np.zeros((size, size, 3), np.float64)
    weights = np.zeros((size, size), np.float64)
    stride = 512 // size
    for y, x in zip(*np.where(coarse)):
        region = neutral[y*stride:(y+1)*stride, x*stride:(x+1)*stride]
        if region.sum() >= 8:
            values = delta[y*stride:(y+1)*stride, x*stride:(x+1)*stride][region]
            anchor[y, x] = np.median(values, axis=0)
            weights[y, x] = CONFIG["anchor_weight"] * float(region.mean())
    if np.count_nonzero(weights) < CONFIG["minimum_anchor_cells"]:
        raise ValueError("Insufficient spatial anchors")
    rows, cols, values = [], [], []
    rhs = np.zeros((int(coarse.sum()), 3), np.float64)
    for y, x in zip(*np.where(coarse)):
        i = indices[y, x]
        neighbors = [(ny, nx) for ny, nx in ((y-1,x),(y+1,x),(y,x-1),(y,x+1))
                     if 0 <= ny < size and 0 <= nx < size and coarse[ny,nx]]
        for ny, nx in neighbors:
            rows.append(i); cols.append(indices[ny,nx]); values.append(-1.0)
        weight = weights[y,x]
        rows.append(i); cols.append(i); values.append(len(neighbors)+weight)
        rhs[i] = weight*anchor[y,x]
    system = coo_matrix((values,(rows,cols)), shape=(len(rhs),len(rhs))).tocsr()
    solved = spsolve(system, rhs)
    if not np.isfinite(solved).all():
        raise ValueError("Complexion field could not be solved")
    field = np.zeros((size,size,3), np.float32)
    field[coarse] = solved
    validity = cv2.resize(coarse.astype(np.float32), (512,512), interpolation=cv2.INTER_LINEAR)
    field = cv2.resize(field, (512,512), interpolation=cv2.INTER_LINEAR)
    field = cv2.GaussianBlur(field, (0,0), CONFIG["field_blur_sigma"])
    validity = cv2.GaussianBlur(validity, (0,0), CONFIG["field_blur_sigma"])
    field /= np.maximum(validity[:,:,None], 1e-5)
    uncapped = field.copy()
    field[:,:,0] = np.clip(field[:,:,0], -CONFIG["maximum_lightness_reduction"], CONFIG["maximum_lightness_increase"])
    magnitude = np.linalg.norm(field[:,:,1:], axis=2)
    field[:,:,1:] *= np.minimum(1, CONFIG["maximum_chroma_offset"]/np.maximum(magnitude,1e-6))[:,:,None]
    result = raw.copy()
    if np.max(np.abs(field[allowed])) > 0.1:
        # Very dark hair/liner/brows receive less color shift; cosmetic lips
        # remain part of the continuous correction rather than an unblended island.
        dark_weight = np.clip(raw_lab[:,:,0]/35,0,1)
        converted = cv2.cvtColor(raw_lab + field*(alpha*dark_weight)[:,:,None], cv2.COLOR_LAB2RGB)
        edited = np.rint(np.clip(converted,0,1)*255).astype(np.uint8)
        result[allowed] = edited[allowed]
    if np.any(result[~allowed] != raw[~allowed]):
        raise RuntimeError("Protected raw pixels changed")
    return result, allowed, {"cpu_seconds":time.perf_counter()-started,
        "alignment_matrix":matrix.tolist(),"alignment_determinant":determinant,
        "neutral_pixels":int(neutral.sum()),"anchor_cells":int(np.count_nonzero(weights)),
        "edit_pixels":int(allowed.sum()),"protected_changed_pixels":0, "whole_lips_hard_protected":False,
        "median_lab_offset":np.median(field[allowed],axis=0).tolist(),
        "capped_pixels":int(np.any(np.abs(field-uncapped)>.001,axis=2)[allowed].sum()),
        "note":"Source-based color reference, not geometry/texture reconstruction or calibrated skin-tone proof.",
        "brows_may_change_color":True}, reference, field, neutral
