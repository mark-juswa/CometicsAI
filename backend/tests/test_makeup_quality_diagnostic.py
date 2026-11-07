"""Offline tests for matched Makeup diagnostics; no real diffusion/GPU calls."""
import ast
import base64
from contextlib import nullcontext
from hashlib import sha256
import json
from pathlib import Path
import sys
from types import SimpleNamespace
from zipfile import ZipFile

from PIL import Image
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))
from scripts import makeup_quality_diagnostic as diagnostic
from scripts import package_makeup_quality_diagnostic as package


def plan():
    return json.loads((ROOT / "data/makeup/MAKEUP-QA-001/plan.json").read_text(encoding="utf-8"))


def test_matrix_is_twelve_matched_cases_with_both_original_styles_and_people():
    matrix = diagnostic.planned_cases(plan())
    assert len(matrix) == 12
    for subject in ("054109", "056266"):
        for style in ("natural_makeup", "classic_red_lip"):
            rows = [r for r in matrix if r["subject_id"] == subject and r["style_id"] == style]
            assert [r["adapter_weight"] for r in rows] == [0., 1., .5]
    for condition in ("foundation_only", "current_adapter", "reduced_adapter"):
        assert len([r for r in matrix if r["id"] == condition]) == 4


@pytest.mark.parametrize("field,value", [
    ("production_enabled", True), ("styles", ["soft_glam"]),
    ("conditions", [{"id": "current_adapter", "adapter_weight": .25}]),
    ("inference", {"steps": 10})])
def test_plan_rejects_changed_scope_or_unmatched_settings(field, value):
    candidate = plan()
    candidate[field] = value
    with pytest.raises(ValueError, match="differs"):
        diagnostic.planned_cases(candidate)


class Layer:
    def __init__(self, name="default_0"):
        self.lora_A, self.lora_B = {name: object()}, {name: object()}
        self.active_adapters, self.disable_adapters, self.merged = [name], False, False
        self.scaling = {name: 2.0}


class FakePipe:
    def __init__(self):
        self.loaded, self.calls = False, []
        self.layer, self.weight = Layer(), 1.
        self.transformer = SimpleNamespace(
            named_modules=lambda: [("layer", self.layer)] if self.loaded else [],
            named_parameters=lambda: [("layer.lora_A.default_0.weight", None)] if self.loaded else [])
        self.last_seed = None
        self.fail_on = None
    def get_list_adapters(self):
        return {"transformer": ["default_0"]} if self.loaded else {}
    def get_active_adapters(self):
        return ["default_0"] if self.loaded else []
    def set_adapters(self, name, adapter_weights):
        assert name == "default_0"
        self.weight = adapter_weights
        self.layer.scaling[name] = 2.0 * adapter_weights
    def load_lora_weights(self, *args, **kwargs):
        assert kwargs["weight_name"] == "adapter.safetensors"
        self.loaded = True
    def enable_model_cpu_offload(self, gpu_id):
        assert gpu_id == 0
    def __call__(self, **kwargs):
        self.calls.append(kwargs)
        if self.fail_on == len(self.calls):
            raise RuntimeError("synthetic inference failure")
        return SimpleNamespace(images=[Image.new("RGB", (512, 512), (int(self.weight * 100), 80, 90))])


STATE = {"library_adapter_name": "default_0", "tensor_equality_verified": True}


def test_effective_scaling_is_checked_relative_to_original_nonunit_values():
    pipe = FakePipe()
    pipe.loaded = True
    defaults = diagnostic.layer_scaling(pipe, "default_0")
    pipe.set_adapters("default_0", adapter_weights=.5)
    result = diagnostic.verify_scaling(pipe, "default_0", defaults, .5)
    assert result["relative_factor"] == .5 and result["layer_count"] == 1
    pipe.layer.scaling["default_0"] = .5  # Wrong: original default was 2.0.
    with pytest.raises(RuntimeError, match="does not match"):
        diagnostic.verify_scaling(pipe, "default_0", defaults, .5)


def test_adapter_influence_is_restored_even_when_a_generation_fails():
    pipe = FakePipe()
    pipe.loaded = True
    defaults = diagnostic.layer_scaling(pipe, "default_0")
    restorations = []
    with pytest.raises(RuntimeError, match="synthetic"):
        with diagnostic.adapter_condition(pipe, Path("adapter"), lambda *a: STATE, STATE,
                                           defaults, .5, restorations):
            assert pipe.layer.scaling["default_0"] == 1.
            raise RuntimeError("synthetic")
    assert pipe.layer.scaling["default_0"] == 2.
    assert restorations[-1]["tensor_state_restored"] and restorations[-1]["scaling_restored"]


def test_tensor_corruption_fails_before_the_weighted_condition_can_run():
    pipe = FakePipe()
    pipe.loaded = True
    initial = diagnostic.layer_scaling(pipe, "default_0")
    with pytest.raises(RuntimeError, match="tensor"):
        with diagnostic.adapter_condition(pipe, Path("adapter"), lambda *a: {"corrupt": True},
                                           STATE, initial, .5, []):
            raise AssertionError("Unverified adapter reached generation")


def test_plain_foundation_rejects_loaded_adapter_and_residual_lora_parameters():
    pipe = FakePipe()
    diagnostic.assert_plain_foundation(pipe)
    pipe.loaded = True
    with pytest.raises(RuntimeError, match="active adapter"):
        diagnostic.assert_plain_foundation(pipe)
    pipe.loaded = False
    pipe.transformer.named_parameters = lambda: [("layer.lora_A.ghost.weight", None)]
    with pytest.raises(RuntimeError, match="LoRA tensors"):
        diagnostic.assert_plain_foundation(pipe)


def setup_fake_runtime(tmp_path, monkeypatch, fail_on=None):
    from scripts import unified_gate1 as gate
    from scripts import unified_gate2 as adapters
    from app import makeup_contract
    root = tmp_path / "gpu-src"
    root.mkdir()
    (tmp_path / "fixtures").mkdir()
    candidate = plan()
    for index, subject in enumerate(candidate["subjects"]):
        photo = tmp_path / "fixtures" / subject["filename"]
        Image.new("RGB", (512, 512), (100 + index * 50, 80, 60)).save(photo)
        subject["sha256"] = sha256(photo.read_bytes()).hexdigest()
    config = tmp_path / "plan.json"
    config.write_text(json.dumps(candidate))
    model = tmp_path / gate.REVISION
    model.mkdir()
    (model / "model_index.json").write_text("{}")
    review = root / "docs/experiments/unified-kaggle-gate1-review.json"
    review.parent.mkdir(parents=True)
    review.write_text(json.dumps({"base_model_index_sha256": gate.digest(model / "model_index.json")}))
    monkeypatch.setattr(diagnostic, "ROOT", root)
    monkeypatch.setenv("AI_MODEL_DIR", str(model))
    monkeypatch.setattr(makeup_contract, "verify_adapter", lambda directory: {})
    monkeypatch.setattr(adapters, "fingerprint", lambda pipe: {"pipeline": id(pipe)})
    monkeypatch.setattr(adapters, "inspect_adapter", lambda *a: dict(STATE))
    pipe = FakePipe()
    pipe.fail_on = fail_on
    class Loader:
        calls = 0
        @classmethod
        def from_pretrained(cls, *args, **kwargs):
            cls.calls += 1
            assert kwargs["local_files_only"]
            return pipe
    monkeypatch.setitem(sys.modules, "diffusers", SimpleNamespace(Flux2KleinPipeline=Loader))
    class Generator:
        def __init__(self, device):
            assert device == "cuda"
        def manual_seed(self, seed):
            assert seed == 1977
            return self
    fake_torch = SimpleNamespace(float16="float16", Generator=Generator, inference_mode=nullcontext, no_grad=nullcontext,
                                  cuda=SimpleNamespace(is_available=lambda: True,
                                  get_device_name=lambda device: "SYNTHETIC_TEST_NOT_GPU",
                                  synchronize=lambda device: None, reset_peak_memory_stats=lambda device: None,
                                  max_memory_allocated=lambda device: 1))
    monkeypatch.setitem(sys.modules, "torch", fake_torch)
    return pipe, Loader, config


def test_complete_synthetic_run_uses_one_foundation_twelve_calls_and_no_quality_pass(tmp_path, monkeypatch):
    pipe, loader, config = setup_fake_runtime(tmp_path, monkeypatch)
    output = tmp_path / "results"
    diagnostic.run(output, config)
    report = json.loads((output / "report.json").read_text())
    assert loader.calls == 1 and len(pipe.calls) == len(report["cases"]) == 12
    assert report["status"] == "DIAGNOSTIC_COMPLETE_REQUIRES_VISUAL_REVIEW"
    assert not report["production_enabled"] and not report["new_training"]
    assert len(report["restorations"]) == 2 and pipe.weight == 1.
    assert all(row["visual_verdict"] == "NEEDS_REVIEW" for row in report["cases"])
    assert all(call["num_inference_steps"] == 20 and call["guidance_scale"] == 4.0 for call in pipe.calls)
    for subject in ("054109", "056266"):
        for style in ("natural_makeup", "classic_red_lip"):
            rows = [r for r in report["cases"] if r["subject_id"] == subject and r["style_id"] == style]
            assert len({r["prompt_sha256"] for r in rows}) == 1
    with pytest.raises(ValueError, match="new output"):
        diagnostic.run(output, config)


def test_partial_failure_keeps_evidence_and_restores_full_influence(tmp_path, monkeypatch):
    pipe, _, config = setup_fake_runtime(tmp_path, monkeypatch, fail_on=9)
    output = tmp_path / "results"
    with pytest.raises(RuntimeError, match="synthetic"):
        diagnostic.run(output, config)
    report = json.loads((output / "report.json").read_text())
    assert report["status"] == "FAILED" and len(report["cases"]) == 8
    assert report["restorations"][-1]["after_factor"] == .5
    assert pipe.weight == 1.
    assert len(list(output.glob("*comparison.jpg"))) == 2


def test_sources_are_only_the_original_two_validation_people():
    assets = package.source_payloads(plan())
    assert set(assets) == {"054109.jpg", "056266.jpg"}
    for subject in plan()["subjects"]:
        raw = base64.b64decode(assets[subject["filename"]]["data"], validate=True)
        assert sha256(raw).hexdigest() == subject["sha256"]


def test_generated_notebook_sources_hashes_and_partial_archive(tmp_path, monkeypatch):
    import subprocess
    book_path = tmp_path / "private.ipynb"
    receipt = package.build(book_path)
    book = json.loads(book_path.read_text())
    assert receipt["expected_outputs"] == 12 and receipt["includes_private_portraits"]
    assert not receipt["includes_weights"] and not receipt["includes_secret_values"]
    code = "".join(book["cells"][1]["source"])
    assignments = {n.targets[0].id: ast.literal_eval(n.value) for n in ast.parse(code).body
                   if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name)
                   and n.targets[0].id in ("FILES", "ASSETS")}
    assert set(assignments["FILES"]) == set(package.FILES)
    for name, item in assignments["FILES"].items():
        raw = base64.b64decode(item["data"], validate=True)
        assert sha256(raw).hexdigest() == item["sha256"]
        assert raw == (ROOT / name).read_bytes()
    assert set(assignments["ASSETS"]) == {"054109.jpg", "056266.jpg"}
    for cell in book["cells"][1:]:
        compile("".join(cell["source"]), str(book_path), "exec")
        assert cell["outputs"] == []
    with pytest.raises(ValueError, match="overwrite"):
        package.build(book_path)
    work = tmp_path / "work"
    work.mkdir()
    (work / "candidate.json").write_text("{}")
    def fail(args, cwd, check):
        assert args[-1].endswith("makeup_quality_bootstrap.py")
        (work / "results").mkdir()
        (work / "results/report.json").write_text('{"status":"FAILED"}')
        raise subprocess.CalledProcessError(1, args)
    monkeypatch.setattr(subprocess, "run", fail)
    with pytest.raises(subprocess.CalledProcessError):
        exec(compile(package.EXECUTION_CELL, "makeup-diagnostic-execution", "exec"),
             {"MAKEUP_WORK": work, "sys": sys})
    with ZipFile(work / "beautycore-makeup-quality-results.zip") as archive:
        assert set(archive.namelist()) == {"results/report.json", "candidate.json"}


def install_offload_reproduction(monkeypatch, real_torch):
    """Mimic lazy adapter parameter materialization during an offloaded forward."""
    original_call = FakePipe.__call__
    original_set = FakePipe.set_adapters
    def forward(self, **kwargs):
        if self.loaded:
            self.materialized = real_torch.nn.Parameter(real_torch.ones(2), requires_grad=False)
        return original_call(self, **kwargs)
    def set_adapter(self, name, adapter_weights):
        if hasattr(self, "materialized"):
            self.materialized.requires_grad_(True)
        return original_set(self, name, adapter_weights)
    monkeypatch.setattr(FakePipe, "__call__", forward)
    monkeypatch.setattr(FakePipe, "set_adapters", set_adapter)


@pytest.mark.parametrize("unsafe", [True, False])
def test_real_torch_materialization_reproduces_the_eighth_image_failure_and_fix(tmp_path, monkeypatch, unsafe):
    import torch as real_torch
    pipe, _, config = setup_fake_runtime(tmp_path, monkeypatch)
    install_offload_reproduction(monkeypatch, real_torch)
    sys.modules["torch"].no_grad = real_torch.inference_mode if unsafe else real_torch.no_grad
    output = tmp_path / "results"
    if unsafe:
        with pytest.raises(RuntimeError, match="inference tensor outside InferenceMode"):
            diagnostic.run(output, config)
        report = json.loads((output / "report.json").read_text())
        assert len(report["cases"]) == 8
    else:
        diagnostic.run(output, config)
        report = json.loads((output / "report.json").read_text())
        assert len(report["cases"]) == 12 and len(report["restorations"]) == 2
        assert pipe.weight == 1.


def original_eight_results(tmp_path, monkeypatch):
    pipe, loader, config = setup_fake_runtime(tmp_path, monkeypatch, fail_on=9)
    output = tmp_path / "results"
    with pytest.raises(RuntimeError):
        diagnostic.run(output, config)
    # This fixture models the independently supplied exact traceback, not a real GPU run.
    folder = tmp_path / "setup-evidence"
    folder.mkdir()
    (folder / "diagnostic.log").write_text(diagnostic.INFERENCE_TENSOR_FAILURE)
    fresh = FakePipe()
    def load(cls, *args, **kwargs):
        cls.calls += 1
        return fresh
    monkeypatch.setattr(loader, "from_pretrained", classmethod(load))
    return output, fresh, config


def test_continuation_retains_eight_runs_one_control_and_only_four_missing_cases(tmp_path, monkeypatch):
    old, pipe, config = original_eight_results(tmp_path, monkeypatch)
    original_hashes = {p.name: sha256(p.read_bytes()).hexdigest() for p in old.iterdir() if p.is_file()}
    output = tmp_path / "resumed"
    diagnostic.run(output, config, resume_from=old)
    report = json.loads((output / "report.json").read_text())
    assert len(report["cases"]) == 12 and report["continuity_check"]["pixels_match"]
    assert report["new_inference_calls"] == len(pipe.calls) == 5
    assert report["continuation"]["retained_cases"] == 8
    assert report["generation_context"] == "torch.no_grad"
    for name, digest in original_hashes.items():
        assert sha256((old / name).read_bytes()).hexdigest() == digest
    for row in report["cases"][:8]:
        assert (old / row["output"]).read_bytes() == (output / row["output"]).read_bytes()


def test_continuity_mismatch_stops_before_missing_images_are_generated(tmp_path, monkeypatch):
    old, pipe, config = original_eight_results(tmp_path, monkeypatch)
    original = FakePipe.__call__
    def changed_control(self, **kwargs):
        result = original(self, **kwargs)
        result.images = [Image.new("RGB", (512, 512), (1, 2, 3))]
        return result
    monkeypatch.setattr(FakePipe, "__call__", changed_control)
    output = tmp_path / "resumed"
    with pytest.raises(RuntimeError, match="Continuity control pixels differ"):
        diagnostic.run(output, config, resume_from=old)
    report = json.loads((output / "report.json").read_text())
    assert len(report["cases"]) == 8 and report["new_inference_calls"] == 1
    assert not report["continuity_check"]["pixels_match"]
    assert pipe.weight == 1.


def test_continuation_rejects_modified_old_output_before_model_load(tmp_path, monkeypatch):
    old, _, config = original_eight_results(tmp_path, monkeypatch)
    row = json.loads((old / "report.json").read_text())["cases"][0]
    (old / row["output"]).write_bytes(b"tampered")
    with pytest.raises(ValueError, match="file hash differs"):
        diagnostic.run(tmp_path / "resumed", config, resume_from=old)


def test_continuation_cell_payloads_match_sources_and_frozen_original_notebook():
    code = package.continuation_cell()
    compile(code, "makeup-continuation", "exec")
    assignments = {n.targets[0].id: ast.literal_eval(n.value) for n in ast.parse(code).body
                   if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name)
                   and n.targets[0].id in ("FILES", "ORIGINAL")}
    frozen = json.loads((ROOT / "docs/experiments/makeup-quality-diagnostic-20261025.json").read_text())
    assert {k: v["sha256"] for k, v in assignments["ORIGINAL"].items()} == frozen["source_hashes"]
    assert set(assignments["FILES"]) == {
        "scripts/makeup_quality_diagnostic.py", "scripts/makeup_quality_resume_bootstrap.py"}
    for name, row in assignments["FILES"].items():
        raw = base64.b64decode(row["data"], validate=True)
        assert sha256(raw).hexdigest() == row["sha256"]
        assert raw == (ROOT / name).read_bytes()
    assert (ROOT / "notebooks/makeup_quality_resume_cell.py").read_text() == code


@pytest.mark.parametrize("problem", [None, "environment", "cache"])
def test_resume_bootstrap_reuses_cache_without_install_and_rejects_drift(tmp_path, monkeypatch, problem):
    from scripts import makeup_quality_resume_bootstrap as bootstrap
    from scripts import style_expansion_bootstrap as helpers
    root = tmp_path / "gpu-src"
    (root / "scripts").mkdir(parents=True)
    evidence_parent = tmp_path / "setup-evidence"
    evidence_parent.mkdir()
    snapshot = tmp_path / "cache" / bootstrap.original.gate.REVISION
    snapshot.mkdir(parents=True)
    (snapshot / "model_index.json").write_text("{}")
    (evidence_parent / "model.json").write_text(json.dumps({"snapshot": str(snapshot)}))
    expected = {key: "pinned" for key in ("python", "packages", "diffusers_commit", "torch", "cuda", "gpu")}
    review = {"environment": expected, "base_model_index_sha256": sha256(b"{}").hexdigest()}
    monkeypatch.setattr(bootstrap, "ROOT", root)
    monkeypatch.setattr(helpers, "check_ports", lambda: None)
    monkeypatch.setattr(bootstrap.original, "verify_bundle", lambda: ({}, review))
    commands = []
    def run(args, output, name, env):
        commands.append(args)
        if name == "environment.log":
            observed = dict(expected)
            if problem == "environment":
                observed["torch"] = "different"
            (output / name).write_text(json.dumps(observed))
    monkeypatch.setattr(bootstrap.original, "run", run)
    if problem == "cache":
        (snapshot / "model_index.json").write_text("changed")
    started = []
    def popen(args, **kwargs):
        started.append((args, kwargs))
        return SimpleNamespace(stdout=iter(["MAKEUP_QA DONE 12 / 12\n"]), wait=lambda: 0)
    monkeypatch.setattr(bootstrap.subprocess, "Popen", popen)
    output = tmp_path / "results-resume-test"
    evidence = evidence_parent / "continuation-test"
    if problem:
        with pytest.raises(RuntimeError, match="Environment changed|Cached model"):
            bootstrap.resume(root / "scripts/runner.py", output, evidence)
        assert not started
    else:
        bootstrap.resume(root / "scripts/runner.py", output, evidence)
        assert len(started) == 1
        args, kwargs = started[0]
        assert args[-2:] == ["--resume-from", str(tmp_path / "results")]
        assert kwargs["env"]["AI_MODEL_DIR"] == str(snapshot)
        assert "--output" in args
        assert json.loads((evidence / "resume-model.json").read_text())["downloaded_again"] is False
    assert all("pip" not in args and "--download-only" not in args for args in commands)
