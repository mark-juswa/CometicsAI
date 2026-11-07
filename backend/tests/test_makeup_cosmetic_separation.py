"""Regressions for highlight contamination and bounded cosmetic editing."""
from pathlib import Path
import sys

import cv2
import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.makeup_cosmetic_separation import blush_layer, eye_protection, transfer


def test_reproduced_pale_highlight_is_not_blush():
    # Actual failing coordinate162,245 from the previous version3 receipt.
    neutral = np.array([[[55.790623, 10.10895, 10.731907]]], np.float32)
    highlight = np.array([[[87.65259, 9.15625, 3.90625]]], np.float32)
    residual, alpha = blush_layer(highlight, neutral, np.ones((1, 1), np.float32))
    # Old magnitude-only confidence accepted this non-red residual as pigment.
    assert np.linalg.norm(residual[0, 0]) > 4
    assert alpha[0, 0] == 0


@pytest.mark.parametrize("lightness", [20, 50, 90])
def test_neutral_brightness_changes_cannot_create_blush(lightness):
    neutral = np.full((8, 8, 3), [50, 10, 10], np.float32)
    highlight = neutral.copy()
    highlight[:, :, 0] = lightness
    _, alpha = blush_layer(highlight, neutral, np.ones((8, 8), np.float32))
    assert not alpha.any()


def test_selected_rose_pigment_is_visible_and_keeps_signed_hue():
    neutral = np.full((8, 8, 3), [65, 12, 15], np.float32)
    makeup = neutral.copy()
    makeup += np.array([12, 18, -6], np.float32)
    residual, alpha = blush_layer(makeup, neutral, np.ones((8, 8), np.float32))
    assert np.all(alpha == 1)
    assert np.all(residual[:, :, 0] == 18)
    assert np.all(residual[:, :, 1] == -6)
    # The layer supplies only chroma; it cannot whiten the source luminance.
    assert residual.shape == (8, 8, 2)


def test_blush_has_no_effect_outside_support():
    neutral = np.full((8, 8, 3), [50, 10, 10], np.float32)
    makeup = neutral + np.array([15, 15, -5], np.float32)
    support = np.zeros((8, 8), np.float32)
    support[3:5, 3:5] = 1
    _, alpha = blush_layer(makeup, neutral, support)
    assert not alpha[support == 0].any()
    assert alpha[support > 0].min() == 1


def test_eye_rim_does_not_expose_iris_core_or_background():
    labels = np.zeros((512, 512), np.uint8)
    cv2.ellipse(labels, (200, 210), (30, 12), 0, 0, 360, 4, -1)
    core, rim = eye_protection(labels)
    assert core[210, 200] and not rim[210, 200]
    assert rim.any() and core.any()
    assert not (rim & core).any()
    assert np.array_equal(rim | core, labels == 4)
    assert not (rim | core)[labels == 0].any()


@pytest.mark.parametrize("invalid", [
    np.zeros((511, 512, 3), np.uint8),
    np.zeros((512, 512, 3), np.float32),
])
def test_invalid_input_is_rejected_before_any_edit(invalid):
    with pytest.raises(ValueError):
        transfer(invalid, invalid, np.zeros((512, 512), np.uint8),
                 np.zeros((512, 512), np.uint8), [], [])


def test_missing_face_is_rejected():
    image = np.full((512, 512, 3), 150, np.uint8)
    with pytest.raises(ValueError, match="primary face"):
        transfer(image, image.copy(), np.zeros((512, 512), np.uint8),
                 np.zeros((512, 512), np.uint8), [], [])


def test_identical_pigment_reference_does_not_double_existing_makeup():
    neutral = np.full((8, 8, 3), [50, 10, 10], np.float32)
    already_present = neutral + np.array([0, 12, -4], np.float32)
    own_residual = already_present[:, :, 1:] - neutral[:, :, 1:]
    delta, alpha = blush_layer(
        already_present, neutral, np.ones((8, 8), np.float32), own_residual
    )
    assert alpha.min() == 1
    assert not delta.any()


def real_case():
    import json
    from PIL import Image
    path = ROOT / "data/makeup/MAKEUP-LAYERS-001/plan-v3.json"
    if not path.is_file():
        pytest.skip("Private offline correction inputs are not available")
    plan = json.loads(path.read_text(encoding="utf-8"))
    source = plan["sources"][0]
    row = plan["cases"][0]
    folder = ROOT / "artifacts/makeup-cosmetic-layers-20261101"
    rgb = lambda p: np.asarray(Image.open(ROOT / p).convert("RGB")).copy()
    label = lambda p: np.asarray(Image.open(ROOT / p)).copy()
    points = lambda name: json.loads((folder / name).read_text(encoding="utf-8"))["points"]
    return (
        rgb(source["source"]), rgb(row["raw"]),
        label(source["source_labels"]), label(row["raw_labels"]),
        points(row["source_landmarks"]), points(row["reference_landmarks"]),
    )


def test_identical_real_photo_is_noop_including_skin_and_lips():
    original, _, labels, _, points, _ = real_case()
    output, _, _ = transfer(original, original.copy(), labels, labels.copy(), points, points)
    assert np.array_equal(output, original)


def test_real_transfer_keeps_inputs_eye_core_teeth_hair_and_scene():
    original, reference, labels, ref_labels, sp, rp = real_case()
    original_before, reference_before = original.copy(), reference.copy()
    output, masks, receipt = transfer(original, reference, labels, ref_labels, sp, rp)
    assert np.array_equal(original, original_before)
    assert np.array_equal(reference, reference_before)
    core, _ = eye_protection(labels)
    protected = ~np.isin(labels, (1, 4, 5, 6, 7, 11, 12)) | core
    assert np.array_equal(output[protected], original[protected])
    assert receipt["eye_core_changed_pixels"] == 0
    # This cannot pass by returning the nearly bare source photo.
    lip = masks["lip"] > 0.8
    eye = masks["lash_liner"] > 0.5
    assert np.mean(np.abs(output[lip].astype(float) - original[lip])) > 10
    assert np.any(output[eye] != original[eye])


@pytest.mark.parametrize("case_index", range(6))
def test_frozen_real_case_reproduces_without_protected_pixel_edits(case_index):
    import json
    from hashlib import sha256
    from PIL import Image
    folder = ROOT / "artifacts/makeup-separation-20261101/run-03"
    if not (folder / "report.json").is_file():
        pytest.skip("Private six-case offline results are not available")
    plan = json.loads((folder / "plan.json").read_text(encoding="utf-8"))
    report = json.loads((folder / "report.json").read_text(encoding="utf-8"))
    row = report["cases"][case_index]
    source = {r["id"]: r for r in plan["sources"]}[row["subject_id"]]
    for path, expected in plan["source_sha256"].items():
        assert sha256((ROOT / path).read_bytes()).hexdigest() == expected
    for record, pairs in [
        (source, [("source", "source_sha256"), ("source_labels", "source_labels_sha256")]),
        (row, [("raw", "raw_sha256"), ("raw_labels", "raw_labels_sha256")]),
    ]:
        for key, hash_key in pairs:
            assert sha256((ROOT / record[key]).read_bytes()).hexdigest() == record[hash_key]
    points_folder = ROOT / "artifacts/makeup-cosmetic-layers-20261101"
    for key in ("source_landmarks", "reference_landmarks"):
        assert sha256((points_folder / row[key]).read_bytes()).hexdigest() == plan["landmark_sha256"][row[key]]
    points = lambda key: json.loads((points_folder / row[key]).read_text(encoding="utf-8"))["points"]
    original = np.asarray(Image.open(ROOT / source["source"]).convert("RGB")).copy()
    reference = np.asarray(Image.open(ROOT / row["raw"]).convert("RGB")).copy()
    labels = np.asarray(Image.open(ROOT / source["source_labels"])).copy()
    ref_labels = np.asarray(Image.open(ROOT / row["raw_labels"])).copy()
    result, _, metrics = transfer(original, reference, labels, ref_labels,
                                  points("source_landmarks"), points("reference_landmarks"))
    stored = np.asarray(Image.open(folder / row["output"]).convert("RGB"))
    assert sha256((folder / row["output"]).read_bytes()).hexdigest() == row["png_sha256"]
    assert sha256(result.tobytes()).hexdigest() == row["rgb_sha256"]
    assert np.array_equal(result, stored)
    core, _ = eye_protection(labels)
    protected = ~np.isin(labels, (1, 4, 5, 6, 7, 11, 12)) | core
    assert np.array_equal(result[protected], original[protected])
    assert metrics["new_diffusion_calls"] == 0
