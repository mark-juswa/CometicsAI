"""Five approved Hair profiles: exact artifact routing, shared worker, and response guards."""
from contextlib import nullcontext
from copy import deepcopy
from io import BytesIO
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "backend")]

from app import hair_profiles as hair, styles
from app.style_release import RELEASE
from app.style_capabilities import model_styles, checked_capabilities
from scripts.generate_style_release import model_catalogs
from test_french_bob_release import release_server
from test_unified_gate3 import fake_server, post
from hair_inference_fixture import FakePipe

ROOT = Path(__file__).resolve().parents[2]
FULL = json.loads((ROOT / "backend/app/style_registry_train002_smoke.json").read_text(encoding="utf-8"))
PLAN = json.loads((ROOT / "data/style-expansion/HAIR-EXP-002/plan.json").read_text(encoding="utf-8"))


def metadata(adapter):
    info = FULL["adapters"][adapter]
    return {"checkpoint_sha256": info["checkpoint_sha256"], "training_steps": info["training_steps"],
            "base_model_id": FULL["base_model_id"], "base_model_revision": FULL["base_model_revision"],
            "supported_style_ids": [s["style_id"] for s in FULL["styles"] if s["adapter_id"] == adapter]}


@pytest.mark.parametrize("group", PLAN["groups"], ids=lambda g: g["style_id"])
def test_each_profile_reproduces_reviewed_prompt_adapter_and_native_arguments(group, monkeypatch):
    monkeypatch.setattr(styles, "REGISTRY", FULL)
    sid = group["style_id"]
    candidate, profile = hair.profile(style_id=sid)
    assert profile["prompt"] == group["candidate_prompt"]
    assert profile["settings"] == PLAN["inference"]
    assert profile["adapter_id"] == group["adapter"]
    contract = hair.expected_contract(sid, metadata(group["adapter"]))
    assert contract["adapter_sha256"] == PLAN["adapter_hashes"][group["adapter"]]
    assert contract["adapter_steps"] == FULL["adapters"][group["adapter"]]["training_steps"]
    assert contract["trained_style"] is False
    worker = release_server()
    runtime = worker.FluxRuntime()
    pipe = FakePipe()
    pipe.loaded = True
    class Generator:
        def __init__(self, device): assert device == "cuda"
        def manual_seed(self, seed):
            assert seed == 1977
            return self
    runtime.pipe = pipe
    runtime.torch = SimpleNamespace(Generator=Generator, no_grad=nullcontext,
        cuda=SimpleNamespace(reset_peak_memory_stats=lambda _: None, synchronize=lambda _: None,
                             max_memory_allocated=lambda _: 0))
    runtime.metadata = metadata(group["adapter"])
    runtime.adapters = {group["adapter"]: (Path("SYNTHETIC"), runtime.metadata)}
    runtime.active_adapter = group["adapter"]
    result = runtime.generate(Image.new("RGB", (300, 640)), sid)
    hair.validate_remote_result(result, sid)
    call = pipe.calls[0]
    assert call["prompt"] == group["candidate_prompt"] and call["num_inference_steps"] == 20
    assert call["guidance_scale"] == 4.0 and call["width"] == call["height"] == 512
    assert pipe.weight == 1.0
    for field, value in (("adapter_id", "wrong"), ("adapter_sha256", "0"*64),
                         ("execution_profile", "wrong"), ("trained_style", True)):
        invalid = deepcopy(result)
        invalid["metadata"][field] = value
        with pytest.raises(ValueError, match="provenance"):
            hair.validate_remote_result(invalid, sid)
    wrong = metadata("train002" if group["adapter"] == "train001" else "train001")
    with pytest.raises(ValueError, match="metadata"):
        hair.expected_contract(sid, wrong)


def test_registry_without_train002_cannot_advertise_its_profiles():
    baseline = json.loads((ROOT / "backend/app/style_registry.json").read_text(encoding="utf-8"))
    assert {c.id for c in hair.hair_candidates(registry=baseline)} == {"exp_butterfly_cut", hair.STYLE_ID}
    assert {c.id for c in hair.hair_candidates(registry=FULL)} == hair.STYLE_IDS
    assert {len(c["hairstyle"]) for c in model_catalogs(RELEASE)} == {5, 18}


@pytest.mark.parametrize("fake_server", [{"factory": release_server}], indirect=True)
def test_all_five_http_routes_share_one_foundation_and_switch_back_after_makeup_nails(fake_server, monkeypatch):
    owner, pipe, views, paths = fake_server
    import test_unified_gate3 as fixture
    worker = fixture.server
    original_digest = worker.gate.digest
    pinned = {paths["hairstyle:" + adapter]: FULL["adapters"][adapter]["checkpoint_sha256"]
              for adapter in ("train001", "train002")}
    monkeypatch.setattr(worker.gate, "digest", lambda p: pinned.get(Path(p), original_digest(p)))
    for adapter in ("train001", "train002"):
        path = paths["hairstyle:" + adapter]
        owner.specs["hairstyle:" + adapter]["expected"]["adapter_sha256"] = pinned[path]
        owner.hair_adapters[adapter] = (path.parent, metadata(adapter))
    views["hairstyle"].hair_adapters = owner.hair_adapters
    owner.load_verified("hairstyle:train001")
    client = TestClient(worker.app)
    for group in PLAN["groups"]:
        result = post(client, "hairstyle", group["style_id"])
        assert result.status_code == 200, result.text
        hair.validate_remote_result(result.json(), group["style_id"])
        assert owner.active == "hairstyle:" + group["adapter"]
    for feature, sid in (("makeup", "natural_makeup"), ("nails", "classic_red"), ("hairstyle", hair.STYLE_ID)):
        result = post(client, feature, sid)
        assert result.status_code == 200, result.text
    assert owner.foundation_load_count == 1 and owner.active == "hairstyle:train001"
    assert post(client, "hairstyle", "exp_unknown").status_code == 400
