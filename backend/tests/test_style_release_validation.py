"""Private release-validation regression checks. No GPU/network calls."""
import ast
import base64
from hashlib import sha256
import json
from pathlib import Path
import sys
from types import SimpleNamespace
from zipfile import ZipFile
import pytest
from PIL import Image
ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "backend")]
from scripts import style_release_validation as validation
from scripts import package_style_release_validation as package
from scripts import makeup_quality_diagnostic as quality
from test_makeup_quality_diagnostic import setup_fake_runtime, FakePipe, install_offload_reproduction


def plan():
    return json.loads((ROOT / "data/style-expansion/STYLE-VAL-001/plan.json").read_text())


@pytest.mark.parametrize("key,value", [
    ("makeup_guidance", 3.0), ("adapter_weight", .5), ("production_enabled", True),
    ("expected_calls", 30), ("makeup_styles", ["natural_makeup"]), ("training", True)])
def test_validation_rejects_scope_changes(key, value):
    candidate = plan()
    candidate[key] = value
    with pytest.raises(ValueError, match="scope"):
        validation.cases(candidate)


def test_all_presets_and_candidates_use_correct_adapter_guidance_and_sources():
    rows = validation.cases(plan())
    assert len(rows) == 29
    assert sum(x["feature"] == "makeup" and x["kind"] == "existing" for x in rows) == 20
    assert sum(x["feature"] == "makeup" and x["kind"] == "candidate" for x in rows) == 4
    assert sum(x["feature"] == "hairstyle" for x in rows) == 4
    assert rows[-1] == {**rows[0], "kind": "restoration"}
    assert all(x["guidance"] == 2.5 and x["adapter"] == "makeup" for x in rows if x["feature"] == "makeup")
    assert all(x["guidance"] == 4. and x["adapter"] == "train002" for x in rows if x["feature"] == "hairstyle")
    assert [x["kind"] for x in rows[24:28]] == ["existing", "candidate"] * 2


def prepared(tmp_path, monkeypatch):
    from scripts import unified_gate1 as gate
    from scripts import unified_gate2 as adapters
    pipe, loader, config = setup_fake_runtime(tmp_path, monkeypatch)
    root = tmp_path / "gpu-src"
    candidate = plan()
    prior = json.loads(config.read_text())
    candidate["makeup_subjects"] = prior["subjects"]
    for index, row in enumerate(candidate["hair_subjects"]):
        path = tmp_path / "fixtures" / row["filename"]
        Image.new("RGB", (400, 517), (40 + index, 50, 60)).save(path)
        row["sha256"] = sha256(path.read_bytes()).hexdigest()
    paths = {}
    for key, dirname in (("makeup", "makeup"), ("train002", "hairstyle_train002")):
        folder = root / "gate1/adapters" / dirname
        folder.mkdir(parents=True)
        (folder / "adapter.safetensors").write_bytes(key.encode())
        paths[key] = str(folder / "adapter.safetensors")
    original_digest = gate.digest
    monkeypatch.setattr(gate, "digest", lambda path: candidate["adapter_hashes"][next(k for k,v in paths.items() if str(path) == v)]
                        if str(path) in paths.values() else original_digest(path))
    hair = root / "gate1/adapters/hairstyle_train002/metadata.json"
    hair.write_text(json.dumps({"checkpoint_sha256": candidate["adapter_hashes"]["train002"],
                               "base_model_revision": gate.REVISION, "training_steps": 500}))
    pixel_hash = sha256(Image.new("RGB", (512,512), (100,80,90)).tobytes()).hexdigest()
    candidate["expected_prior_pixels"] = {key:pixel_hash for key in candidate["expected_prior_pixels"]}
    conf = tmp_path / "validation-plan.json"
    conf.write_text(json.dumps(candidate))
    monkeypatch.setattr(validation, "ROOT", root)
    def unload(self):
        self.loaded = False
    monkeypatch.setattr(FakePipe, "unload_lora_weights", unload, raising=False)
    return pipe, loader, conf


def test_full_29_calls_one_foundation_prior_controls_and_adapter_reload(tmp_path, monkeypatch):
    pipe, loader, config = prepared(tmp_path, monkeypatch)
    output = tmp_path / "results"
    validation.run(output, config)
    r = json.loads((output / "report.json").read_text())
    assert r["status"] == "COMPLETE_REQUIRES_VISUAL_REVIEW"
    assert loader.calls == 1 and r["new_inference_calls"] == len(pipe.calls) == 29
    assert [s["adapter"] for s in r["switches"]] == ["makeup", "train002", "makeup"]
    assert all(x["prior_control_match"] for x in r["cases"] if "prior_control_match" in x)
    assert sum("prior_control_match" in x for x in r["cases"]) == 4
    assert r["cases"][-1]["restoration_pixel_match"]
    assert [x["guidance_scale"] for x in pipe.calls] == [2.5]*24 + [4.]*4 + [2.5]
    assert all(x["num_inference_steps"] == 20 for x in pipe.calls)
    assert len(list(output.glob("*comparison.jpg"))) == 4
    assert not r["production_enabled"] and not r["training"]
    with pytest.raises(ValueError, match="new output"):
        validation.run(output, config)


def test_prior_pixel_mismatch_stops_after_first_case_and_keeps_report(tmp_path, monkeypatch):
    pipe, _, config = prepared(tmp_path, monkeypatch)
    p = json.loads(config.read_text())
    p["expected_prior_pixels"]["054109/natural_makeup"] = "different"
    config.write_text(json.dumps(p))
    output = tmp_path / "results"
    with pytest.raises(RuntimeError, match="Saved control"):
        validation.run(output, config)
    r = json.loads((output / "report.json").read_text())
    assert r["status"] == "FAILED" and len(pipe.calls) == 1
    assert r["cases"][0]["prior_control_match"] is False


def test_generation_failure_keeps_prior_completed_evidence(tmp_path, monkeypatch):
    pipe, _, config = prepared(tmp_path, monkeypatch)
    pipe.fail_on = 3
    output = tmp_path / "results"
    with pytest.raises(RuntimeError, match="synthetic"):
        validation.run(output, config)
    r = json.loads((output / "report.json").read_text())
    assert r["status"] == "FAILED" and len(r["cases"]) == 2
    assert len(list(output.glob("*source.png"))) == 4


def test_real_no_grad_allows_switches_after_lazy_tensor_materialization(tmp_path, monkeypatch):
    import torch as real_torch
    pipe, _, config = prepared(tmp_path, monkeypatch)
    install_offload_reproduction(monkeypatch, real_torch)
    sys.modules["torch"].no_grad = real_torch.no_grad
    # Image generation is exercised; sheet writes are covered by full run above.
    monkeypatch.setattr(validation, "sheets", lambda *args: None)
    validation.run(tmp_path / "results", config)
    assert len(pipe.calls) == 29


def test_package_has_four_verified_sources_and_partial_zip_on_failure(tmp_path, monkeypatch):
    import subprocess
    output = tmp_path / "validation.ipynb"
    receipt = package.build(output)
    assert receipt["expected_calls"] == 29 and receipt["includes_private_portraits"]
    assert not receipt["includes_weights"] and not receipt["includes_keys"]
    book = json.loads(output.read_text())
    for cell in book["cells"][1:]:
        compile("".join(cell["source"]), "validation-cell", "exec")
        assert cell["outputs"] == []
    assignments = {n.targets[0].id:ast.literal_eval(n.value) for n in ast.parse("".join(book["cells"][1]["source"])).body
                   if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id in ("FILES","ASSETS")}
    assert len(assignments["ASSETS"]) == 4
    for name,row in assignments["FILES"].items():
        raw=base64.b64decode(row["data"],validate=True)
        assert sha256(raw).hexdigest()==row["sha256"] and raw==(ROOT/name).read_bytes()
    for row in assignments["ASSETS"].values():
        assert sha256(base64.b64decode(row["data"],validate=True)).hexdigest()==row["sha256"]
    with pytest.raises(ValueError, match="overwrite"):
        package.build(output)
    work = tmp_path / "work"
    (work / "overlay").mkdir(parents=True)
    (work / "candidate.json").write_text("{}")
    for name,row in assignments["FILES"].items():
        path=work/"overlay"/name
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(base64.b64decode(row["data"]))
    def fail(args, cwd, check):
        (work/"results").mkdir()
        (work/"results/report.json").write_text('{"status":"FAILED"}')
        raise subprocess.CalledProcessError(1,args)
    monkeypatch.setattr(subprocess,"run",fail)
    with pytest.raises(subprocess.CalledProcessError):
        exec(package.EXECUTION, {"VALIDATION_WORK":work,"FILES":assignments["FILES"],"sys":sys})
    with ZipFile(work/"beautycore-release-validation-results.zip") as archive:
        assert "results/report.json" in archive.namelist()
        assert "experiment-sources/data/style-expansion/STYLE-VAL-001/plan.json" in archive.namelist()

