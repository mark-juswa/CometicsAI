"""Hair expansion preparation checks. No real diffusion, network or service startup."""
import ast
import base64
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
from zipfile import ZipFile

import pytest
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "backend")]
from scripts import hair_expansion_validation as validation
from scripts import package_hair_expansion_validation as package
from scripts import capstone_kaggle, capstone_discovery
from scripts.capstone_train002_bootstrap import worker_environment
from test_makeup_quality_diagnostic import setup_fake_runtime, FakePipe, install_offload_reproduction


def plan():
    return json.loads((ROOT / package.FILES[-1]).read_text(encoding="utf-8"))


@pytest.mark.parametrize("key,value", [
    ("expected_calls", 22), ("production_enabled", True), ("automatic_promotion", True),
    ("training", True), ("inference", {"steps": 8}),
])
def test_scope_changes_do_not_reach_generation(key, value):
    candidate = plan()
    candidate[key] = value
    with pytest.raises(ValueError, match="scope"):
        validation.cases(candidate)


def test_exact_matrix_has_two_people_and_nearest_baselines_per_style():
    candidate = plan()
    rows = validation.cases(candidate)
    assert len(rows) == 21
    assert len([r for r in rows if r["kind"] == "candidate"]) == 10
    assert len([r for r in rows if r["kind"] == "baseline"]) == 10
    assert rows[-1] == {**rows[0], "kind": "restoration"}
    assert {r["adapter"] for r in rows} == {"train001", "train002"}
    for sid, (baseline, adapter) in validation.TARGETS.items():
        selected = [r for r in rows if r["candidate_id"] == sid and r["kind"] != "restoration"]
        assert len(selected) == 4 and len({r["subject_id"] for r in selected}) == 2
        assert {r["style_id"] for r in selected} == {sid, baseline}
        assert {r["adapter"] for r in selected} == {adapter}
    candidate["groups"][0]["adapter"] = "train002"
    with pytest.raises(ValueError, match="group contract"):
        validation.cases(candidate)


def prepared(tmp_path, monkeypatch):
    pipe, loader, _ = setup_fake_runtime(tmp_path, monkeypatch)
    root = tmp_path / "gpu-src"
    candidate = plan()
    for index, subject in enumerate(candidate["subjects"]):
        path = tmp_path / "fixtures" / subject["filename"]
        Image.new("RGB", (400, 580), (60 + index * 20, 80, 90)).save(path)
        subject["sha256"] = sha256(path.read_bytes()).hexdigest()
    conf = tmp_path / "hair-plan.json"
    conf.write_bytes(json.dumps(candidate).encode())
    paths = {}
    for key in ("train001", "train002"):
        paths[key] = root / "gate1/adapters" / key
        paths[key].mkdir(parents=True)
        (paths[key] / "adapter.safetensors").write_bytes(key.encode())
    monkeypatch.setattr(validation, "ROOT", root)
    monkeypatch.setattr(validation, "verify_hair_contract", lambda plan: paths)
    monkeypatch.setattr(FakePipe, "unload_lora_weights", lambda self: setattr(self, "loaded", False), raising=False)
    return pipe, loader, conf


def test_synthetic_full_run_one_foundation_restoration_and_embedded_review(tmp_path, monkeypatch):
    pipe, loader, config = prepared(tmp_path, monkeypatch)
    output = tmp_path / "results"
    validation.run(output, config)
    report = json.loads((output / "report.json").read_text())
    assert report["status"] == "COMPLETE_REQUIRES_VISUAL_REVIEW"
    assert not report["production_enabled"] and not report["training"]
    assert loader.calls == 1 and len(pipe.calls) == report["new_inference_calls"] == 21
    assert [s["adapter"] for s in report["switches"]] == ["train001", "train002", "train001"]
    assert report["cases"][-1]["restoration_pixel_match"]
    assert len({r["candidate_id"] for r in report["cases"]}) == 5
    assert all(r["visual_verdict"] == "NEEDS_REVIEW" for r in report["cases"])
    assert all(call["num_inference_steps"] == 20 and call["guidance_scale"] == 4.0 for call in pipe.calls)
    assert len(list(output.glob("*-comparison.jpg"))) == 5
    page = (output / "review-self-contained.html").read_text(encoding="utf-8")
    assert page.count("data:image/png;base64,") == 30
    assert "showModal()" in page and "src=\"../" not in page
    with pytest.raises(ValueError, match="new output"):
        validation.run(output, config)


def test_inference_failure_keeps_completed_outputs_and_partial_review(tmp_path, monkeypatch):
    pipe, _, config = prepared(tmp_path, monkeypatch)
    pipe.fail_on = 3
    output = tmp_path / "results"
    with pytest.raises(RuntimeError, match="synthetic"):
        validation.run(output, config)
    report = json.loads((output / "report.json").read_text())
    assert report["status"] == "FAILED" and len(report["cases"]) == 2
    assert len(list(output.glob("*-source.png"))) == 4
    assert (output / "review-self-contained.html").is_file()


def test_source_corruption_stops_before_foundation_load(tmp_path, monkeypatch):
    pipe, loader, config = prepared(tmp_path, monkeypatch)
    person = plan()["subjects"][0]
    (tmp_path / "fixtures" / person["filename"]).write_bytes(b"changed")
    with pytest.raises(ValueError, match="Source photo differs"):
        validation.run(tmp_path / "results", config)
    assert loader.calls == 0 and not pipe.calls


def test_real_no_grad_supports_offloaded_adapter_switches(tmp_path, monkeypatch):
    import torch as real_torch
    pipe, _, config = prepared(tmp_path, monkeypatch)
    install_offload_reproduction(monkeypatch, real_torch)
    sys.modules["torch"].no_grad = real_torch.no_grad
    monkeypatch.setattr(validation, "review", lambda *args: None)
    validation.run(tmp_path / "results", config)
    assert len(pipe.calls) == 21


def test_real_frozen_gpu_hair_metadata_stays_valid_without_candidate_training_labels(tmp_path):
    archive = ROOT / "artifacts" / capstone_discovery.TRAIN002_BUNDLE_NAME
    if not archive.is_file():
        pytest.skip("Private original GPU archive is not included in source control")
    root = tmp_path / "gpu-src"
    capstone_kaggle.extract(archive, root, capstone_discovery.TRAIN002_BUNDLE_SHA)
    target = root / "scripts/hair_expansion_validation.py"
    target.write_bytes((ROOT / "scripts/hair_expansion_validation.py").read_bytes())
    config = tmp_path / "hair-plan.json"
    config.write_bytes((ROOT / package.FILES[-1]).read_bytes())
    env = worker_environment({**os.environ, "PYTHONPATH": str(root) + os.pathsep + str(root / "backend")}, root)
    code = """import json
from pathlib import Path
from scripts.hair_expansion_validation import verify_hair_contract
p=json.loads(Path(__import__('sys').argv[1]).read_text(encoding='utf-8'))
assert set(verify_hair_contract(p))=={'train001','train002'}
print('Original Hair adapter hashes, metadata, exact training claims and baseline prompts verified')
"""
    result = subprocess.run([sys.executable, "-c", code, str(config)], env=env, cwd=root,
                            capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stderr


def test_notebook_source_assets_and_timeout_failure_zip(tmp_path, monkeypatch):
    target = tmp_path / "hair.ipynb"
    receipt = package.build(target)
    assert receipt["expected_calls"] == 21 and receipt["includes_private_portraits"]
    assert not receipt["includes_weights"] and not receipt["includes_keys"]
    book = json.loads(target.read_text())
    cells = [c for c in book["cells"] if c["cell_type"] == "code"]
    for cell in cells:
        compile("".join(cell["source"]), "<hair-cell>", "exec")
        assert cell["outputs"] == [] and cell["execution_count"] is None
    tree = ast.parse("".join(cells[0]["source"]))
    values = {n.targets[0].id: ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign)
              and isinstance(n.targets[0], ast.Name) and n.targets[0].id in ("FILES", "ASSETS")}
    assert len(values["ASSETS"]) == 4
    for name, row in values["FILES"].items():
        raw = base64.b64decode(row["data"], validate=True)
        assert sha256(raw).hexdigest() == row["sha256"]
        assert raw == (ROOT / name).read_bytes()
    for row in values["ASSETS"].values():
        assert sha256(base64.b64decode(row["data"], validate=True)).hexdigest() == row["sha256"]
    with pytest.raises(ValueError, match="overwrite"):
        package.build(target)
    work = tmp_path / "work"
    (work / "overlay").mkdir(parents=True)
    (work / "candidate.json").write_text("{}")
    for name, row in values["FILES"].items():
        path = work / "overlay" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(base64.b64decode(row["data"]))
    class Process:
        pid = 123456
        args = ["SYNTHETIC_PROCESS_NO_SERVICE"]
        calls = 0
        status = None
        def wait(self, timeout=None):
            self.calls += 1
            if self.calls == 1:
                raise subprocess.TimeoutExpired(self.args, timeout)
            self.status = -15
            return self.status
        def poll(self):
            return self.status
    process = Process()
    signals = []
    monkeypatch.setattr(subprocess, "Popen", lambda *args, **kwargs: process)
    monkeypatch.setattr(os, "killpg", lambda *args: signals.append(args), raising=False)
    import signal
    with pytest.raises(RuntimeError, match="Two-hour safety"):
        exec(package.EXECUTION, {"HAIR_WORK": work, "FILES": values["FILES"]})
    assert signals == [(process.pid, signal.SIGTERM)]
    with ZipFile(work / "beautycore-hair-expansion-results.zip") as archive:
        assert "experiment-sources/data/style-expansion/HAIR-EXP-002/plan.json" in archive.namelist()
        assert "hair-attempted" in archive.namelist()
