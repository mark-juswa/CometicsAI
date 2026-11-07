"""Reference visibility, color fidelity and original-photo protection regressions."""
from pathlib import Path
from hashlib import sha256
import json
import sys

import cv2
import numpy as np
from PIL import Image
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.makeup_reference_application import (
    transfer, blush_layer, full_core_support, cosmetic_chroma_field,
    stroke_coverage, reference_dark_target, eye_protection, eyelid_support,
)


def test_reference_pigment_core_is_not_attenuated_by_placement_prior():
    radial = np.array([[0.0, 0.5, 1.0, 2.0, 4.0, 5.0]], np.float32)
    alpha = full_core_support(radial)
    assert np.all(alpha[0, :3] == 1)
    assert 0 < alpha[0, 3] < 1
    assert np.all(alpha[0, 4:] == 0)


def test_selected_color_does_not_add_warm_source_skin_to_pigment_hue():
    source = np.full((16, 16, 3), [50, 30, 35], np.float32)
    selected = np.full((16, 16, 3), [80, 20, 5], np.float32)
    original = source.copy()
    field = cosmetic_chroma_field(source, selected, np.ones((16, 16), np.float32), 1.5)
    result_ab = source[:, :, 1:] + field
    assert np.allclose(result_ab, selected[:, :, 1:], atol=1e-4)
    assert np.array_equal(source, original)
    assert field.shape == (16, 16, 2)


def test_same_selected_color_is_noop_without_removing_source_detail():
    yy, xx = np.mgrid[:32, :32]
    image = np.full((32, 32, 3), [60, 15, 12], np.float32)
    image[:, :, 1] += (xx % 3) * 0.2
    field = cosmetic_chroma_field(image, image.copy(), np.ones((32, 32), np.float32), 1.5)
    assert np.max(np.abs(field)) < 1e-5


def test_actual_narrow_reference_lash_can_retain_full_coverage():
    selected = np.full((64, 64), 70, np.float32)
    selected[20:40, 32] = 10
    coverage = stroke_coverage(selected)
    assert coverage[30, 32] == 1
    assert not coverage[5:10, 5:10].any()


def test_dark_stroke_target_matches_reference_without_whitening_source():
    source = np.full((64, 64, 3), [60, 15, 12], np.float32)
    selected = np.full((64, 64, 3), [80, 15, 12], np.float32)
    selected[20:40, 32, 0] = 10
    stroke = stroke_coverage(selected[:, :, 0])
    src_base, ref_base = source.copy(), selected.copy()
    ref_base[:, :, 0] = 80
    target = reference_dark_target(source, selected, src_base, ref_base, stroke)
    assert target[30, 32] == pytest.approx(7.5)
    assert np.max(target) <= 60.001


def test_eye_color_stops_before_brow_bone_and_keeps_soft_crease():
    upper = np.array([[170, 210], [200, 205], [230, 210]], np.float32)
    lower = np.array([[170, 210], [200, 222], [230, 210]], np.float32)
    brow = np.array([[170, 165], [200, 160], [230, 165]], np.float32)
    alpha = eyelid_support(None, upper, lower, brow)
    assert alpha[200, 200] > 0.8
    assert alpha[160, 200] == 0
    assert alpha[235, 200] == 0
    assert alpha[200, 50] == 0
    assert 0 <= alpha.min() <= alpha.max() <= 1


def test_previous_pale_highlight_is_still_not_blush():
    neutral = np.array([[[55.790623, 10.10895, 10.731907]]], np.float32)
    highlight = np.array([[[87.65259, 9.15625, 3.90625]]], np.float32)
    _, alpha = blush_layer(highlight, neutral, np.ones((1, 1), np.float32))
    assert alpha[0, 0] == 0


def fixture(case_index=0):
    folder = ROOT / "artifacts/makeup-reference-20261101/run-05"
    if not (folder / "report.json").is_file():
        pytest.skip("Private offline reference images are not available")
    plan = json.loads((folder / "plan.json").read_text(encoding="utf-8"))
    report = json.loads((folder / "report.json").read_text(encoding="utf-8"))
    row = report["cases"][case_index]
    subject = {s["id"]: s for s in plan["sources"]}[row["subject_id"]]
    rgb = lambda p: np.asarray(Image.open(p).convert("RGB")).copy()
    original, selected = rgb(ROOT / subject["source"]), rgb(ROOT / row["raw"])
    labels = np.asarray(Image.open(ROOT / subject["source_labels"])).copy()
    ref_labels = np.asarray(Image.open(ROOT / row["raw_labels"])).copy()
    point_folder = ROOT / "artifacts/makeup-cosmetic-layers-20261101"
    point = lambda key: json.loads((point_folder / row[key]).read_text(encoding="utf-8"))["points"]
    return folder, plan, row, subject, original, selected, labels, ref_labels, point("source_landmarks"), point("reference_landmarks")


def test_identical_actual_photo_is_exact_noop():
    _, _, _, _, original, _, labels, _, points, _ = fixture()
    result, _, _ = transfer(original, original.copy(), labels, labels.copy(), points, points)
    assert np.array_equal(original, result)


@pytest.mark.parametrize("case_index", range(6))
def test_all_actual_references_reproduce_and_keep_original_protected(case_index):
    folder, plan, row, subject, original, selected, labels, ref_labels, sp, rp = fixture(case_index)
    digest = lambda p: sha256(p.read_bytes()).hexdigest()
    for name, expected in plan["source_sha256"].items():
        assert digest(ROOT / name) == expected
    for record, pairs in [
        (subject, [("source", "source_sha256"), ("source_labels", "source_labels_sha256")]),
        (row, [("raw", "raw_sha256"), ("raw_labels", "raw_labels_sha256")]),
    ]:
        for key, expected_key in pairs:
            assert digest(ROOT / record[key]) == record[expected_key]
    points_folder = ROOT / "artifacts/makeup-cosmetic-layers-20261101"
    for key in ("source_landmarks", "reference_landmarks"):
        assert digest(points_folder / row[key]) == plan["landmark_sha256"][row[key]]
    before, reference_before = original.copy(), selected.copy()
    result, masks, metrics = transfer(original, selected, labels, ref_labels, sp, rp)
    stored = np.asarray(Image.open(folder / row["output"]).convert("RGB"))
    assert digest(folder / row["output"]) == row["png_sha256"]
    assert np.array_equal(stored, result)
    assert sha256(result.tobytes()).hexdigest() == row["rgb_sha256"]
    assert np.array_equal(original, before) and np.array_equal(selected, reference_before)
    core, _ = eye_protection(labels)
    protected = ~np.isin(labels, (1, 4, 5, 6, 7, 11, 12)) | core
    assert np.array_equal(result[protected], original[protected])
    brow = np.isin(labels, (6, 7))
    assert np.all(result[brow] <= original[brow])
    # Already prominent lipstick is unchanged by the visibility refinement.
    old = np.asarray(Image.open(ROOT / "artifacts/makeup-separation-20261101/run-03" / (row["id"] + "-corrected.png")).convert("RGB"))
    lips = np.isin(labels, (11, 12))
    assert np.array_equal(result[lips], old[lips])
    assert metrics["new_diffusion_calls"] == 0


def test_warp_padding_cannot_tint_an_identical_face_boundary():
    source = np.full((32, 32, 3), [60, 18, 22], np.float32)
    reference = source.copy()
    valid = np.zeros((32, 32), bool)
    valid[4:28, 4:28] = True
    reference[~valid] = 0
    field = cosmetic_chroma_field(
        source, reference, valid.astype(np.float32), 1.5, valid
    )
    assert np.max(np.abs(field[valid])) < 1e-4
