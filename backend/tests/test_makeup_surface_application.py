"""Regressions for source lip placement and texture, not makeup realism scores."""
from hashlib import sha256
import json
from pathlib import Path
import sys

import cv2
import numpy as np
from PIL import Image
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.makeup_surface_application import apply_lipstick, lip_coverage, palette
from scripts.makeup_alignment_pilot import CHAINS
from scripts.makeup_selected_cosmetics import inside, polygon


def fixture(index=0):
    folder = ROOT / "artifacts/makeup-surface-20261102/lip-final"
    if not (folder / "report.json").is_file():
        pytest.skip("Private local Makeup proof is not available")
    plan = json.loads((folder / "plan.json").read_text(encoding="utf-8"))
    report = json.loads((folder / "report.json").read_text(encoding="utf-8"))
    case = report["cases"][index]
    source = {r["id"]: r for r in plan["sources"]}[case["subject_id"]]
    read = lambda path: np.array(Image.open(ROOT / path).convert("RGB"))
    original, reference = read(source["source"]), read(case["raw"])
    labels = np.array(Image.open(ROOT / source["source_labels"]))
    reference_labels = np.array(Image.open(ROOT / case["raw_labels"]))
    point_file = ROOT / "artifacts/makeup-cosmetic-layers-20261101" / case["source_landmarks"]
    points = json.loads(point_file.read_text(encoding="utf-8"))["points"]
    return folder, plan, case, source, original, reference, labels, reference_labels, points


@pytest.mark.parametrize("index", range(6))
def test_reproduces_frozen_example_and_preserves_source_surface(index):
    folder, plan, case, source, original, reference, labels, ref_labels, points = fixture(index)
    for name, expected in plan["source_sha256"].items():
        assert sha256((ROOT / name).read_bytes()).hexdigest() == expected
    for row, keys in [
        (source, [("source", "source_sha256"), ("source_labels", "source_labels_sha256")]),
        (case, [("raw", "raw_sha256"), ("raw_labels", "raw_labels_sha256")]),
    ]:
        for key, checksum in keys:
            assert sha256((ROOT / row[key]).read_bytes()).hexdigest() == row[checksum]
    point_file = ROOT / "artifacts/makeup-cosmetic-layers-20261101" / case["source_landmarks"]
    assert sha256(point_file.read_bytes()).hexdigest() == plan["landmark_sha256"][case["source_landmarks"]]
    before, ref_before = original.copy(), reference.copy()
    output, alpha, metrics = apply_lipstick(original, reference, labels, ref_labels, points)
    assert np.array_equal(original, before) and np.array_equal(reference, ref_before)
    assert sha256(output.tobytes()).hexdigest() == case["rgb_sha256"]
    assert sha256((folder / case["output"]).read_bytes()).hexdigest() == case["png_sha256"]
    assert np.array_equal(output, np.array(Image.open(folder / case["output"])))
    assert np.array_equal(output[alpha == 0], original[alpha == 0])
    assert np.array_equal(output[~np.isin(labels, (11, 12))],
                          original[~np.isin(labels, (11, 12))])
    xy = np.asarray(points)[:, :2] * 512
    exterior = ~polygon(xy[CHAINS["lip_outer"]])
    mouth = polygon(xy[CHAINS["lip_inner"]])
    assert np.array_equal(output[exterior | mouth], original[exterior | mouth])
    # These protect original eyes, brows, nose, teeth, skin, hair and scene.
    protected = ~np.isin(labels, (11, 12))
    assert not np.any(output[protected] != original[protected])
    # The source lightness gradient survives in the fully covered interior.
    lab = lambda rgb: cv2.cvtColor(rgb.astype(np.float32) / 255, cv2.COLOR_RGB2LAB)
    change = (lab(output) - lab(original))[:, :, 0][alpha >= 0.999]
    assert len(change) > 40
    assert np.ptp(change) < 0.7  # RGB rounding, not scaled or copied shading.
    assert metrics["new_diffusion_calls"] == metrics["new_model_calls"] == 0
    assert metrics["protected_changed_pixels"] == 0


@pytest.mark.parametrize("index", [0, 2])
def test_identical_original_is_exact_noop(index):
    _, _, _, _, original, _, labels, _, points = fixture(index)
    output, _, _ = apply_lipstick(original, original.copy(), labels, labels.copy(), points)
    assert np.array_equal(output, original)


def test_boundary_coverage_is_zero_on_the_outermost_supported_pixel():
    _, _, _, _, _, _, labels, _, points = fixture()
    alpha, support, _ = lip_coverage(labels, points)
    distance = cv2.distanceTransform(support.astype(np.uint8), cv2.DIST_L2, 5)
    boundary = support & (distance <= 1.0)
    assert boundary.any()
    assert np.all(alpha[boundary] == 0)
    assert np.all(alpha[~support] == 0)
    assert np.any(alpha == 1)


def test_reference_face_pixels_outside_lips_cannot_enter_output():
    _, _, _, _, original, reference, labels, ref_labels, points = fixture()
    changed_reference = reference.copy()
    changed_reference[~np.isin(ref_labels, (11, 12))] = 255 - changed_reference[~np.isin(ref_labels, (11, 12))]
    first, _, _ = apply_lipstick(original, reference, labels, ref_labels, points)
    second, _, _ = apply_lipstick(original, changed_reference, labels, ref_labels, points)
    assert np.array_equal(first, second)


def test_reference_lip_texture_and_highlight_positions_cannot_be_pasted():
    _, _, _, _, original, reference, labels, ref_labels, points = fixture()
    interior = inside(np.isin(ref_labels, (11, 12)), 3.0) >= 0.999
    changed = reference.copy()
    changed[interior] = reference[interior][::-1]
    assert np.any(changed != reference)
    assert np.array_equal(palette(changed, ref_labels), palette(reference, ref_labels))
    first, _, _ = apply_lipstick(original, reference, labels, ref_labels, points)
    second, _, _ = apply_lipstick(original, changed, labels, ref_labels, points)
    assert np.array_equal(first, second)


def test_uncertain_lip_outline_is_refused():
    _, _, _, _, _, _, labels, _, points = fixture()
    shifted = np.asarray(points).copy()
    shifted[CHAINS["lip_outer"], 0] += 0.15
    shifted[CHAINS["lip_inner"], 0] += 0.15
    with pytest.raises(ValueError, match="Uncertain original lip boundary"):
        lip_coverage(labels, shifted)


@pytest.mark.parametrize("bad", ["shape", "nonfinite", "outside"])
def test_invalid_source_landmarks_are_refused(bad):
    _, _, _, _, _, _, labels, _, points = fixture()
    points = np.asarray(points).copy()
    if bad == "shape":
        points = points[:400]
    elif bad == "nonfinite":
        points[0, 0] = np.nan
    else:
        points[0, 0] = -0.1
    with pytest.raises(ValueError):
        lip_coverage(labels, points)


def test_missing_reference_lips_are_refused():
    _, _, _, _, _, reference, _, ref_labels, _ = fixture()
    bad = ref_labels.copy()
    bad[np.isin(bad, (11, 12))] = 1
    with pytest.raises(ValueError, match="Insufficient reference lipstick samples"):
        palette(reference, bad)


def test_invalid_image_dtype_is_refused():
    _, _, _, _, original, reference, labels, ref_labels, points = fixture()
    with pytest.raises(ValueError, match="Expected uint8"):
        apply_lipstick(original.astype(np.float32), reference, labels, ref_labels, points)
