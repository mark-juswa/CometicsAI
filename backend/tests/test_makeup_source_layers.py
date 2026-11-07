"""Source material invariants and exact retained lip compatibility, not realism scores."""
import copy
from pathlib import Path
import sys

import cv2
import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.makeup_source_layers import apply_material, render_layers, catalog, pixel_hash
from scripts.makeup_source_layers import render_files
import json
from scripts.makeup_surface_application import lip_coverage, palette
from test_makeup_surface_application import fixture


def document(original, labels, alpha, selected, kind="lip"):
    return {"schema": "makeup-source-layers-v1", "production_enabled": False,
            "source_rgb_sha256": pixel_hash(original), "labels_sha256": pixel_hash(labels),
            "style_id": "classic_red_lip", "scope": "component",
            "artist_review": {"decision": "PENDING"},
            "layers": [{"id": "pigment", "kind": kind, "palette_lab": selected.tolist(),
                        "alpha_sha256": pixel_hash(alpha)}]}


@pytest.mark.parametrize("index", range(6))
def test_shared_operator_reproduces_retained_lip_without_retouch(index):
    _, _, case, _, original, reference, labels, ref_labels, points = fixture(index)
    alpha, _, _ = lip_coverage(labels, points)
    doc = document(original, labels, alpha, palette(reference, ref_labels))
    output, evidence = render_layers(original, labels, doc, {"pigment": alpha}, development_only=True)
    assert pixel_hash(output) == case["rgb_sha256"]
    assert np.array_equal(output[alpha == 0], original[alpha == 0])
    assert evidence["artist_review_present"] is False
    assert evidence["full_look_quality"] == "NEEDS VERIFICATION"


@pytest.mark.parametrize("level", [45, 110, 190])
def test_blush_preserves_source_shading_across_different_source_levels(level):
    # Synthetic material invariant only, not an available-person result.
    yy, xx = np.mgrid[:512, :512]
    rgb = np.empty((512, 512, 3), np.uint8)
    detail = ((xx + yy) % 7).astype(np.uint8)
    for channel, shift in enumerate([15, 2, 0]):
        rgb[:, :, channel] = level + detail + shift
    alpha = np.zeros((512, 512), np.float32)
    alpha[200:260, 200:260] = 1
    lab = cv2.cvtColor(rgb.astype(np.float32) / 255, cv2.COLOR_RGB2LAB)
    anchor = np.median(lab[alpha == 1], axis=0)
    selected = anchor + [25, 8, 3]  # Bright reference L must be ignored for blush.
    selected[0] = min(99, selected[0])
    output, info = apply_material(rgb, alpha, selected, anchor, "blush")
    assert info["offset_lab"][0] == 0
    changed_l = cv2.cvtColor(output.astype(np.float32) / 255, cv2.COLOR_RGB2LAB)[:, :, 0]
    assert np.max(np.abs(changed_l[alpha == 1] - lab[:, :, 0][alpha == 1])) < .5
    assert np.array_equal(output[alpha == 0], rgb[alpha == 0])
    assert np.any(output != rgb)


def test_unreviewed_layer_pack_cannot_be_used_as_artist_accepted_asset():
    _, _, _, _, original, reference, labels, refs, points = fixture()
    alpha, _, _ = lip_coverage(labels, points)
    doc = document(original, labels, alpha, palette(reference, refs))
    with pytest.raises(ValueError, match="review required"):
        render_layers(original, labels, doc, {"pigment": alpha})


def test_source_shadow_guard_never_brightens_black_cheek_pixels():
    original = np.zeros((512, 512, 3), np.uint8)
    alpha = np.ones((512, 512), np.float32)
    with pytest.raises(ValueError, match="cheek lightness"):
        apply_material(original, alpha, [30, 12, 3], [0, 0, 0], "blush")


@pytest.mark.parametrize("failure", ["source", "labels", "mask", "protected", "overlap", "style", "nan"])
def test_stale_unsafe_or_ambiguous_assets_are_refused(failure):
    _, _, _, _, original, reference, labels, refs, points = fixture()
    alpha, _, _ = lip_coverage(labels, points)
    doc = document(original, labels, alpha, palette(reference, refs))
    masks = {"pigment": alpha.copy()}
    if failure in {"source", "labels"}:
        doc["source_rgb_sha256" if failure == "source" else "labels_sha256"] = "0" * 64
    elif failure == "style":
        doc["style_id"] = "invented_style"
    elif failure == "mask":
        masks["pigment"][0, 0] = .5
    elif failure in {"protected", "nan"}:
        masks["pigment"][0, 0] = 1 if failure == "protected" else np.nan
        doc["layers"][0]["alpha_sha256"] = pixel_hash(masks["pigment"])
    elif failure == "overlap":
        extra = copy.deepcopy(doc["layers"][0])
        extra["id"] = "second"
        doc["layers"].append(extra)
        masks["second"] = alpha.copy()
    with pytest.raises(ValueError):
        render_layers(original, labels, doc, masks, development_only=True)


def test_inventory_preserves_ten_serving_and_three_held_styles():
    rows = catalog()
    assert len(rows) == 13
    assert sum(row["serving"] for row in rows) == 10
    assert {row["id"] for row in rows if not row["serving"]} == {
        "exp_cloud_berry_lips", "exp_manga_lash", "exp_icy_silver"}


def test_offline_file_workflow_is_lossless_source_bound_and_refuses_replacement(tmp_path):
    from PIL import Image
    _, _, case, _, original, reference, labels, refs, points = fixture()
    alpha, _, _ = lip_coverage(labels, points)
    doc = document(original, labels, alpha, palette(reference, refs))
    doc["layers"][0]["alpha_path"] = "coverage.npy"
    Image.fromarray(original).save(tmp_path / "source.png")
    Image.fromarray(labels).save(tmp_path / "labels.png")
    np.save(tmp_path / "coverage.npy", alpha, allow_pickle=False)
    path = tmp_path / "layers.json"
    path.write_text(json.dumps(doc), encoding="utf-8")
    output = tmp_path / "result.png"
    with pytest.raises(ValueError, match="review required"):
        render_files(tmp_path / "source.png", tmp_path / "labels.png", path, output)
    assert not output.exists()
    receipt = render_files(tmp_path / "source.png", tmp_path / "labels.png", path, output, development_only=True)
    assert pixel_hash(np.array(Image.open(output))) == case["rgb_sha256"]
    assert receipt["training_target_approved"] is False
    with pytest.raises(ValueError, match="overwrite"):
        render_files(tmp_path / "source.png", tmp_path / "labels.png", path, output, development_only=True)
