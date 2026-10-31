"""Approved French Bob profile, worker, facade and package integration without GPU."""
import ast
import asyncio
import base64
from copy import deepcopy
from contextlib import nullcontext
from hashlib import sha256
import importlib.util
from io import BytesIO
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
from unittest.mock import patch
from zipfile import ZipFile

import httpx
from PIL import Image
import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "backend")]
from app import main, hair_profiles as hair
from app.style_release import RELEASE, load_release
from app.style_capabilities import checked_capabilities, model_styles
from app.generation.remote_flux import RemoteFluxEngine, RemoteGenerationError
from scripts import package_all_hair_nails_release as package
from scripts import hair_nails_release_overlay as overlay
from scripts import capstone_kaggle
from scripts.capstone_train002_bootstrap import worker_environment
from test_unified_gate3 import fake_server, KEY, post
from hair_inference_fixture import FakePipe as InferencePipe


def release_server():
    name = "verified_hair_worker_fixture"
    path = ROOT / "scripts/unified_gate3_server.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    exec(compile(path.read_bytes() + package.HOOK, str(path), "exec"), module.__dict__)
    return module


def test_profile_is_exactly_the_reviewed_candidate_and_not_a_training_label():
    plan = json.loads((ROOT / "data/style-expansion/HAIR-EXP-002/plan.json").read_text())
    candidate = next(g for g in plan["groups"] if g["style_id"] == hair.STYLE_ID)
    assert hair.PROFILE["prompt"] == candidate["candidate_prompt"]
    assert hair.PROFILE["settings"] == plan["inference"]
    assert hair.PROFILE["adapter_sha256"] == plan["adapter_hashes"]["train001"]
    assert {c.id for c in RELEASE.enabled("hairstyle")} == hair.STYLE_IDS
    assert all(c.id not in {s["style_id"] for s in __import__("app.styles", fromlist=["REGISTRY"]).REGISTRY["styles"]}
               for c in hair.hair_candidates())
    previous = load_release(ROOT / "backend/app/style_releases/styles-20261030-01.json")
    assert not hair.hair_candidates(previous)
    with pytest.raises(ValueError):
        hair.expected_contract("exp_not_approved")


def test_changed_profile_cannot_load_under_the_approved_hash(tmp_path, monkeypatch):
    changed = deepcopy(hair.PROFILE)
    changed["prompt"] = "unapproved prompt"
    path = tmp_path / "hair.json"
    path.write_text(json.dumps(changed))
    monkeypatch.setattr(hair, "PATH", path)
    with pytest.raises(ValueError, match="profile differs"):
        hair.hair_candidates()


@pytest.mark.parametrize("fault", ["missing", "legacy", "wrong_profile", "wrong_hash", "wrong_models"])
def test_enabled_hair_rejects_old_or_incompatible_worker(fault):
    worker = hair.worker_capabilities(model_styles())
    if fault == "missing":
        health = {}
    else:
        if fault == "legacy": worker["model_profile"] = "legacy-baseline"
        if fault == "wrong_profile": worker["profile_sha256"] = {}
        if fault == "wrong_hash": worker["manifest_sha256"] = "0" * 64
        if fault == "wrong_models": worker["model_styles"] = {}
        health = {"style_capabilities": worker}
    with pytest.raises(ValueError, match="capabilities differ"):
        checked_capabilities(health, health)


def metadata():
    from app.styles import REGISTRY
    definition = REGISTRY["adapters"]["train001"]
    return {"checkpoint_sha256": definition["checkpoint_sha256"], "training_steps": definition["training_steps"],
            "base_model_id": REGISTRY["base_model_id"], "base_model_revision": REGISTRY["base_model_revision"],
            "supported_style_ids": ["crew_cut", "bob_hair", "layered_hair"]}


def payload():
    stream = BytesIO()
    Image.new("RGB", (512, 512), "red").save(stream, "PNG")
    contract = hair.expected_contract(hair.STYLE_ID)
    return {"status": "completed", "generator": contract["generator"],
            "metadata": {k: v for k, v in contract.items() if k != "generator"},
            "image": {"width": 512, "height": 512, "content_type": "image/png",
                      "data_url": "data:image/png;base64," + base64.b64encode(stream.getvalue()).decode()}}


@pytest.mark.parametrize("field,value", [
    ("execution_profile_sha256", "0" * 64), ("adapter_sha256", "0" * 64),
    ("style_id", "bob_hair"), ("steps", 8), ("guidance", 2.5), ("seed", 999),
    ("trained_style", True), ("style_release_id", "old"), ("prompt_sha256", "0" * 64),
])
def test_remote_result_requires_exact_profile_provenance(field, value):
    result = payload()
    result["metadata"][field] = value
    with pytest.raises(ValueError, match="provenance"):
        hair.validate_remote_result(result, hair.STYLE_ID)


def test_actual_profile_generation_uses_reviewed_arguments_and_no_postprocessing():
    worker = release_server()
    runtime = worker.FluxRuntime()
    pipe = InferencePipe()
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
    runtime.metadata = metadata()
    runtime.adapters = {"train001": (Path("SYNTHETIC_FIXTURE"), runtime.metadata)}
    runtime.active_adapter = "train001"
    image = Image.new("RGB", (350, 620), "white")
    result = runtime.generate(image, hair.STYLE_ID)
    hair.validate_remote_result(result, hair.STYLE_ID)
    call = pipe.calls[0]
    assert call["prompt"] == hair.PROFILE["prompt"]
    assert call["width"] == call["height"] == 512
    assert call["num_inference_steps"] == 20 and call["guidance_scale"] == 4.0
    assert call["image"].size == (512, 512) and pipe.weight == 1.0
    assert result["metadata"]["trained_style"] is False
    with Image.open(BytesIO(base64.b64decode(result["image"]["data_url"].split(",")[1]))) as im:
        assert im.getpixel((0, 0)) == (100, 80, 90)  # unchanged synthetic pipeline result


@pytest.mark.parametrize("fake_server", [release_server], indirect=True)
def test_real_http_worker_routes_french_bob_and_keeps_shared_switching(fake_server, monkeypatch):
    owner, pipe, views, paths = fake_server
    import test_unified_gate3 as fixture
    worker = fixture.server
    path = paths["hairstyle:train001"]
    real_digest = worker.gate.digest
    expected_hash = metadata()["checkpoint_sha256"]
    monkeypatch.setattr(worker.gate, "digest", lambda p: expected_hash if Path(p) == path else real_digest(p))
    owner.specs["hairstyle:train001"]["expected"]["adapter_sha256"] = expected_hash
    owner.hair_adapters["train001"] = (path.parent, metadata())
    views["hairstyle"].hair_adapters = owner.hair_adapters
    owner.load_verified("hairstyle:train001")
    client = TestClient(worker.app)
    result = post(client, "hairstyle", hair.STYLE_ID)
    assert result.status_code == 200, result.text
    hair.validate_remote_result(result.json(), hair.STYLE_ID)
    assert post(client, "hairstyle", "exp_wolf_cut").status_code == 400
    assert post(client, "makeup", "natural_makeup").status_code == 200
    assert post(client, "nails", "classic_red").status_code == 200
    assert post(client, "hairstyle", "crew_cut").status_code == 200
    assert owner.active == "hairstyle:train001"
    assert owner.foundation_load_count == 1


def test_facade_catalog_consultation_and_strict_remote_client(monkeypatch):
    engine = RemoteFluxEngine("https://profile.inference.invalid", "test-not-a-secret")
    monkeypatch.setattr(main, "engine", engine)
    client = TestClient(main.app)
    styles = client.get("/features/hairstyle/styles").json()
    assert hair.STYLE_ID in {s["id"] for s in styles}
    assert "Preview may change hair color" in next(s["description"] for s in styles if s["id"] == hair.STYLE_ID)
    assert hair.STYLE_ID in json.dumps(client.get("/consultations/catalog").json())
    response = payload()
    real_client = httpx.AsyncClient
    calls = []
    def transport(request):
        calls.append(request)
        assert request.headers["X-API-Key"] == "test-not-a-secret"
        return httpx.Response(200, json=response)
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: real_client(**kwargs, transport=httpx.MockTransport(transport)))
    image = BytesIO()
    Image.new("RGB", (512, 512), "white").save(image, "PNG")
    result = client.post("/features/hairstyle/generate", data={"style_id": hair.STYLE_ID},
                         files={"image": ("portrait.png", image.getvalue(), "image/png")})
    assert result.status_code == 200, result.text
    assert result.json()["metadata"]["execution_profile"] == hair.PROFILE_ID
    response["metadata"]["steps"] = 8
    with pytest.raises(RemoteGenerationError):
        asyncio.run(engine.generate(Image.new("RGB", (512, 512)), hair.active_hair_style_by_id()[hair.STYLE_ID]))
    assert len(calls) == 2  # one request each; no automatic retries


def test_real_package_extraction_overlay_and_original_metadata_contract(tmp_path):
    receipt = package.build(tmp_path / "release")
    archive = tmp_path / "release/artifacts" / package.CPU_NAME
    with ZipFile(archive) as cpu:
        manifest = json.loads(cpu.read("demo_bundle.json"))
        assert cpu.testzip() is None
        assert manifest["style_release"] == receipt["style_release"]
        for name, digest in manifest["files"].items():
            assert sha256(cpu.read(name)).hexdigest() == digest
    book = json.loads((tmp_path / "release" / package.NOTEBOOK).read_text(encoding="utf-8"))
    tree = ast.parse("".join(book["cells"][1]["source"]))
    values = {n.targets[0].id: ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign)
              and isinstance(n.targets[0], ast.Name) and n.targets[0].id in {"OPTIMIZED_SOURCES", "BUNDLES"}}
    sources = overlay.validated(values["OPTIMIZED_SOURCES"])
    assert manifest["worker_sources"] == {k: sha256(v).hexdigest() for k, v in sources.items()}
    assert values["BUNDLES"][1][:2] == (package.CPU_NAME, receipt["cpu"]["sha256"])
    root = tmp_path / "gpu-src"
    capstone_kaggle.extract(ROOT / "artifacts" / package.prior.GPU_NAME, root, package.prior.GPU_SHA)
    before = (root / "gate3_bundle.json").read_bytes()
    staged = overlay.stage_overlay(tmp_path, values["OPTIMIZED_SOURCES"])
    output = tmp_path / "session"
    output.mkdir()
    with patch("scripts.hair_nails_release_overlay.socket.socket") as factory:
        factory.return_value.__enter__.return_value.connect_ex.return_value = 1
        overlay.install_overlay(root, staged, output)
    assert (root / "gate3_bundle.json").read_bytes() == before
    env = worker_environment({**os.environ, "PYTHONPATH": str(root) + os.pathsep + str(root / "backend")}, root)
    code = """from scripts import unified_gate3_server as s
from app.hair_profiles import STYLE_ID
a=s.adapter_configuration()
assert STYLE_ID not in a['train001'][1]['supported_style_ids']
assert s.selected_adapter('hairstyle',STYLE_ID)=='hairstyle:train001'
assert len(s.runtime.health()['style_capabilities']['model_styles']['hairstyle'])==18
assert s.runtime.health()['foundation_load_count']==0
print('Real original checkpoint metadata and new profile routing verified without model load')
"""
    result = subprocess.run([sys.executable, "-c", code], cwd=root, env=env, capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stderr
    package.build(tmp_path / "release")  # deterministic immutable repeat
