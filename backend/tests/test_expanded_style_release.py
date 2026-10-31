"""Release safety and real renderer integration without GPU/cloud requests."""

import asyncio
from copy import deepcopy
from dataclasses import replace
from io import BytesIO
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image, ImageChops
import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from app import main, style_release
from app.style_release import RELEASE, PATH, load_release, parse_release
from app.style_capabilities import installed_candidates, style_capabilities, checked_capabilities
from app.nails.expanded import STYLE_IDS, render_expanded
from app.nails.styles import NAIL_STYLES, active_nail_styles
from app.nails.render import render_target
from app.nails.geometry import ReviewedMaskSegmenter, NailCrop, composite_nails
from app.nails.hybrid import HybridNailsPipeline, normalized_hand, _to_normalized_mask, _to_original
from test_nails_hybrid import hand_fixture
from scripts.generate_style_release import outputs, model_catalogs


def approved_release():
    return replace(RELEASE, candidates=tuple(
        replace(c, enabled=True, review_status="accepted") if c.id in STYLE_IDS else c
        for c in RELEASE.candidates))


def raw():
    return json.loads(PATH.read_text(encoding="utf-8"))


def test_only_three_tested_nails_and_five_approved_hair_are_enabled():
    assert len(RELEASE.candidates) == 13
    assert {c.id for c in RELEASE.enabled()} == STYLE_IDS | __import__("app.hair_profiles", fromlist=["STYLE_IDS"]).STYLE_IDS
    assert all(c.review_status == "accepted" for c in RELEASE.enabled())
    assert len(active_nail_styles()) == 8
    assert len(installed_candidates(approved_release())) == 5
    assert {s.id for s in active_nail_styles(approved_release())} == (
        {s.id for s in NAIL_STYLES} | STYLE_IDS)


@pytest.mark.parametrize("fault", [
    "duplicate_id", "unreviewed_enabled", "held_enabled", "missing_evidence",
    "unknown_field", "wrong_route", "missing_profile", "partial_profile", "bad_hash",
    "baseline_id", "wrong_enabled_type",
])
def test_invalid_manifest_never_becomes_executable(fault):
    value = raw()
    candidate = next(c for c in value["candidates"] if c["id"] in STYLE_IDS)
    if fault == "duplicate_id": value["candidates"].append(deepcopy(candidate))
    if fault == "unreviewed_enabled": candidate.update(enabled=True, review_status="pending_visual")
    if fault == "held_enabled": candidate.update(enabled=True, review_status="held")
    if fault == "missing_evidence":
        candidate.update(enabled=True, review_status="accepted", evidence=[])
    if fault == "unknown_field": candidate["prompt_from_browser"] = "unsafe"
    if fault == "wrong_route": candidate["route"] = "makeup_profile"
    if fault == "missing_profile":
        candidate.update(enabled=True, review_status="accepted", profile_id=None, profile_sha256=None)
    if fault == "partial_profile": candidate["profile_id"] = None
    if fault == "bad_hash": candidate["profile_sha256"] = "0" * 63
    if fault == "baseline_id": candidate["id"] = "nude_pink"
    if fault == "wrong_enabled_type": candidate["enabled"] = "false"
    with pytest.raises(ValueError):
        parse_release(value)


def test_duplicate_json_keys_fail_before_parsing_a_release(tmp_path):
    path = tmp_path / "release.json"
    path.write_text('{"schema":"one","schema":"two"}')
    with pytest.raises(ValueError, match="Duplicate"):
        load_release(path)


def test_changed_renderer_source_hash_cannot_be_approved():
    release = approved_release()
    release = replace(release, candidates=tuple(
        replace(c, profile_sha256="0" * 64) if c.id in STYLE_IDS else c for c in release.candidates))
    with pytest.raises(ValueError, match="hash differs"):
        installed_candidates(release)


def test_new_model_profile_cannot_be_claimed_before_implementation():
    release = replace(RELEASE, candidates=tuple(
        replace(c, enabled=True, review_status="accepted", profile_id="unimplemented-model-v1",
                profile_sha256="0" * 64, evidence=("review.md",))
        if c.id == "exp_wolf_cut" else c for c in RELEASE.candidates))
    with pytest.raises(ValueError, match="profile differs"):
        installed_candidates(release)


@pytest.mark.parametrize("style_id", sorted(STYLE_IDS))
def test_renderer_dispatch_is_exact_to_the_experiment_and_never_uses_gpu(style_id):
    source, mask, hand = hand_fixture()
    from scripts.style_expansion_nails import render as experimental_render
    result = render_target(source, mask, style_id, hand, production_palette=True)
    assert np.array_equal(np.asarray(result), np.asarray(experimental_render(source, mask, style_id)))
    assert np.array_equal(np.asarray(result)[np.asarray(mask) == 0],
                          np.asarray(source)[np.asarray(mask) == 0])

    class Localizer:
        def locate(self, image): return hand

    class NoModel:
        async def generate(self, *args): pytest.fail("Rendered design reached the GPU")

    style = next(s for s in active_nail_styles(approved_release()) if s.id == style_id)
    output = asyncio.run(HybridNailsPipeline(Localizer(), ReviewedMaskSegmenter(mask), NoModel())
                         .run(source, style))
    assert output.path == "renderer" and output.model_seconds is None
    assert output.nail_count == 5 and output.image.size == source.size
    assert np.array_equal(np.asarray(output.image)[np.asarray(mask) == 0],
                          np.asarray(source)[np.asarray(mask) == 0])


@pytest.mark.parametrize("style_id", sorted(STYLE_IDS))
def test_pending_design_is_absent_and_rejected_before_upload_decoding(style_id, monkeypatch):
    pending = replace(RELEASE, candidates=tuple(
        replace(c, enabled=False, review_status="pending_visual") if c.id in STYLE_IDS else c
        for c in RELEASE.candidates))
    monkeypatch.setattr(style_release, "RELEASE", pending)
    client = TestClient(main.app)
    assert style_id not in {s["id"] for s in client.get("/features/nails/styles").json()}
    response = client.post("/features/nails/generate", data={"style_id": style_id},
                           files={"image": ("bad.png", b"not-an-image", "image/png")})
    assert response.status_code == 400
    assert "valid nail style" in response.json()["detail"]
    catalog = client.get("/consultations/catalog")
    assert catalog.status_code == 200
    assert style_id not in json.dumps(catalog.json())


def test_approved_release_runs_through_real_api_and_consultation_catalog(monkeypatch):
    source, mask, hand = hand_fixture()

    class Localizer:
        def locate(self, image): return hand

    monkeypatch.setenv("NAILS_PREVIEW_MODE", "hybrid")
    pipeline = HybridNailsPipeline(Localizer(), ReviewedMaskSegmenter(mask), None)
    monkeypatch.setattr(main, "nails_pipeline", lambda: pipeline)
    client = TestClient(main.app)
    assert len(client.get("/features/nails/styles").json()) == 8
    catalog = client.get("/consultations/catalog")
    assert all(sid in json.dumps(catalog.json()) for sid in STYLE_IDS)
    image = BytesIO()
    source.save(image, format="PNG")
    for sid in STYLE_IDS:
        response = client.post("/features/nails/generate", data={"style_id": sid},
                               files={"image": ("hand.png", image.getvalue(), "image/png")})
        assert response.status_code == 200, response.text
        result = response.json()
        assert result["status"] == "completed"
        assert result["metadata"]["inference_path"] == "renderer"
        assert result["metadata"]["renderer_profile"] == "nails-expanded-v1"
        assert result["metadata"]["trained_model"] is False
        assert "adapter_sha256" not in result["metadata"]


def test_generated_metadata_is_reversible_and_does_not_invent_prices():
    business = json.loads((ROOT / "beautycore/lib/business/style-catalog.json").read_text(encoding="utf-8"))
    staged, expected = outputs(business, approved_release())
    assert len(staged["nails"]) == 8
    for sid in STYLE_IDS:
        assert staged["nails"][sid]["services"] == ["Classic Manicure", "Gel Manicure", "Nail Art (per nail)"]
        assert "price" not in staged["nails"][sid]
    disabled_release = replace(approved_release(), candidates=tuple(
        replace(c, enabled=False) for c in approved_release().candidates))
    disabled, disabled_capabilities = outputs(staged, disabled_release)
    assert disabled == staged  # Saved-look metadata survives disabling generation.
    assert len(disabled_capabilities["renderer_styles"]) == 3
    assert not (STYLE_IDS & {s.id for s in active_nail_styles(disabled_release)})
    current, _ = outputs(business, RELEASE)
    assert current == business
    assert len(expected["renderer_styles"]) == 6
    assert {len(c["hairstyle"]) for c in model_catalogs()} == {3, 13}


def test_capabilities_remain_bounded_and_do_not_claim_gpu_renderer_support():
    capabilities = style_capabilities(approved_release())
    assert len(json.dumps({"ready": True, "style_capabilities": capabilities}).encode()) < 8192
    assert all(sid not in json.dumps(capabilities["model_styles"]) for sid in STYLE_IDS)
    assert STYLE_IDS <= set(capabilities["renderer_styles"])
    previous = load_release(ROOT / "backend/app/style_releases/styles-20261030-01.json")
    legacy = checked_capabilities({}, {}, previous)
    assert legacy["model_profile"] == "legacy-baseline"
    worker = {"style_capabilities": {"model_profile": "legacy-baseline",
                                    "model_styles": legacy["model_styles"]}}
    assert checked_capabilities(worker, worker, previous) == legacy
    worker["style_capabilities"]["model_styles"] = {}
    with pytest.raises(ValueError, match="capabilities differ"):
        checked_capabilities(worker, worker, previous)
    with pytest.raises(ValueError, match="capabilities differ"):
        checked_capabilities({"style_capabilities": None}, {"style_capabilities": None}, previous)
    with pytest.raises(ValueError, match="inconsistent"):
        checked_capabilities(worker, {}, previous)


@pytest.mark.parametrize("subject", ["0000045", "0000088", "0001030", "0001593"])
def test_port_reproduces_all_saved_automatic_mask_results(subject):
    folder = ROOT / "artifacts/style-expansion-20261025/automatic-mask-validation-02" / subject
    if not folder.exists():
        pytest.skip("Private historical hand outputs are not included in source control")
    source = Image.open(folder / "source.png").convert("RGB")
    normalized = Image.open(folder / "normalized.png").convert("RGB")
    coarse = Image.open(folder / "coarse-mask.png").convert("L")
    refined = Image.open(folder / "refined-mask.png").convert("L")
    _, box = normalized_hand(source)
    proposal = ImageChops.lighter(coarse, _to_normalized_mask(refined, box))
    for sid in STYLE_IDS:
        rendered = render_target(normalized, proposal, sid, None, production_palette=True)
        mapped = _to_original(rendered, box, source.size)
        result = composite_nails(source, mapped, NailCrop((0, 0, *source.size), source, refined))
        expected = Image.open(folder / (sid + ".png")).convert("RGB")
        assert np.array_equal(np.asarray(result), np.asarray(expected)), (subject, sid)
