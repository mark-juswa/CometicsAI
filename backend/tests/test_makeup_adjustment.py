"""MAKEUP-QA-002 bounded comparison tests; no GPU or network requests."""
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
from scripts import makeup_adjustment_diagnostic as adjustment
from scripts import makeup_quality_diagnostic as quality
from scripts import package_makeup_adjustment as package
from test_makeup_quality_diagnostic import setup_fake_runtime, FakePipe, install_offload_reproduction


def plan():
    return json.loads((ROOT / "data/makeup/MAKEUP-QA-002/plan.json").read_text())


@pytest.mark.parametrize("field,value", [
    ("production_enabled", True), ("new_training", True),
    ("inference", {"steps": 10}), ("foundation_instruction", "make skin lighter")])
def test_rejects_scope_or_settings_changes(field, value):
    candidate = plan()
    candidate[field] = value
    with pytest.raises(ValueError, match="differs"):
        adjustment.validate_plan(candidate)


def test_matrix_changes_exactly_one_factor_and_retains_full_adapter():
    cases = adjustment.matrix(plan())
    assert len(cases) == 12
    assert {x["adapter_weight"] for x in cases} == {1.0}
    assert [(x["guidance"], x["prompt_variant"]) for x in cases[::4]] == [
        (4.0, "original"), (3.0, "original"), (4.0, "matched_foundation")]
    from app.makeup_contract import PROMPTS
    for style in plan()["styles"]:
        assert adjustment.prompt_for(style, "original") == PROMPTS[style]
        assert adjustment.prompt_for(style, "matched_foundation") == PROMPTS[style] + " " + adjustment.INSTRUCTION
    assert plan()["inference"] == {"width": 512, "height": 512, "steps": 20, "seed": 1977}


def prepared(tmp_path, monkeypatch):
    _, loader, old_plan = setup_fake_runtime(tmp_path, monkeypatch)
    reference = tmp_path / "results-resume-original"
    quality.run(reference, old_plan)
    config = plan()
    old = json.loads((reference / "report.json").read_text())
    config["subjects"] = old["subjects"]
    config["reference_report_sha256"] = sha256((reference / "report.json").read_bytes()).hexdigest()
    config["reference_plan_sha256"] = old["plan_sha256"]
    config_path = tmp_path / "gpu-src/data/makeup/MAKEUP-QA-002/plan-test.json"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(json.dumps(config))
    monkeypatch.setattr(adjustment, "ROOT", tmp_path / "gpu-src")
    pipe = FakePipe()
    loader.calls = 0
    def load(cls, *args, **kwargs):
        cls.calls += 1
        assert kwargs["local_files_only"]
        return pipe
    monkeypatch.setattr(loader, "from_pretrained", classmethod(load))
    return config_path, reference, pipe, loader


def test_nine_calls_retain_four_controls_and_preserve_originals(tmp_path, monkeypatch):
    config, reference, pipe, loader = prepared(tmp_path, monkeypatch)
    hashes = {p.name: sha256(p.read_bytes()).hexdigest() for p in reference.iterdir() if p.is_file()}
    output = tmp_path / "results-adjustment-new"
    adjustment.run(output, config, reference)
    report = json.loads((output / "report.json").read_text())
    assert report["status"] == "DIAGNOSTIC_COMPLETE_REQUIRES_VISUAL_REVIEW"
    assert report["new_inference_calls"] == len(pipe.calls) == 9 and loader.calls == 1
    assert len(report["cases"]) == 12 and sum(r["retained"] for r in report["cases"]) == 4
    assert report["continuity_check"]["pixels_match"] and pipe.weight == 1.0
    assert len(report["restorations"]) == 1
    assert [c["guidance_scale"] for c in pipe.calls] == [4.] + [3.] * 4 + [4.] * 4
    assert all(c["num_inference_steps"] == 20 for c in pipe.calls)
    assert all(adjustment.INSTRUCTION not in c["prompt"] for c in pipe.calls[:5])
    assert all(c["prompt"].endswith(adjustment.INSTRUCTION) for c in pipe.calls[5:])
    for name, value in hashes.items():
        assert sha256((reference / name).read_bytes()).hexdigest() == value
    for row in report["cases"][:4]:
        assert (output / row["output"]).read_bytes() == (reference / row["output"]).read_bytes()
    assert len(list(output.glob("*comparison.jpg"))) == 2
    with pytest.raises(ValueError, match="new output"):
        adjustment.run(output, config, reference)


def test_mismatched_control_stops_before_any_candidate(tmp_path, monkeypatch):
    config, reference, pipe, _ = prepared(tmp_path, monkeypatch)
    original = FakePipe.__call__
    def changed(self, **kwargs):
        result = original(self, **kwargs)
        result.images = [Image.new("RGB", (512, 512), (1, 2, 3))]
        return result
    monkeypatch.setattr(FakePipe, "__call__", changed)
    output = tmp_path / "results-adjustment-new"
    with pytest.raises(RuntimeError, match="Continuity pixels differ"):
        adjustment.run(output, config, reference)
    report = json.loads((output / "report.json").read_text())
    assert report["new_inference_calls"] == len(pipe.calls) == 1
    assert len(report["cases"]) == 4 and pipe.weight == 1.
    assert report["restorations"][0]["scaling_restored"]


def test_failure_retains_partial_outputs_and_restores_adapter(tmp_path, monkeypatch):
    config, reference, pipe, _ = prepared(tmp_path, monkeypatch)
    pipe.fail_on = 4
    output = tmp_path / "results-adjustment-new"
    with pytest.raises(RuntimeError, match="synthetic"):
        adjustment.run(output, config, reference)
    report = json.loads((output / "report.json").read_text())
    assert report["status"] == "FAILED" and report["new_inference_calls"] == 4
    assert len(report["cases"]) == 6 and pipe.weight == 1.
    assert report["restorations"][0]["tensor_state_restored"]


@pytest.mark.parametrize("target", ["report", "image"])
def test_tampered_reference_rejected_before_model_load(tmp_path, monkeypatch, target):
    config, reference, pipe, loader = prepared(tmp_path, monkeypatch)
    if target == "report":
        with (reference / "report.json").open("a") as stream:
            stream.write(" ")
    else:
        old = json.loads((reference / "report.json").read_text())
        row = next(r for r in old["cases"] if r["id"] == "current_adapter")
        (reference / row["output"]).write_bytes(b"changed")
    with pytest.raises(ValueError, match="differs"):
        adjustment.run(tmp_path / "new", config, reference)
    assert loader.calls == 0 and not pipe.calls


def test_real_torch_no_grad_allows_lazy_adapter_restoration(tmp_path, monkeypatch):
    import torch as real_torch
    config, reference, pipe, _ = prepared(tmp_path, monkeypatch)
    install_offload_reproduction(monkeypatch, real_torch)
    sys.modules["torch"].no_grad = real_torch.no_grad
    adjustment.run(tmp_path / "new", config, reference)
    assert len(pipe.calls) == 9 and pipe.weight == 1.0


@pytest.mark.parametrize("drift", [None, "environment", "cache"])
def test_bootstrap_reuses_cache_and_rejects_drift(tmp_path, monkeypatch, drift):
    from scripts import unified_gate3_bootstrap as original
    from scripts import style_expansion_bootstrap as helpers
    root = tmp_path / "gpu-src"
    (root / "scripts").mkdir(parents=True)
    evidence_root = tmp_path / "setup-evidence"
    evidence_root.mkdir()
    snapshot = tmp_path / original.gate.REVISION
    snapshot.mkdir()
    (snapshot / "model_index.json").write_text("{}")
    (evidence_root / "model.json").write_text(json.dumps({"snapshot": str(snapshot)}))
    config = root / "data/makeup/MAKEUP-QA-002/plan-test.json"
    config.parent.mkdir(parents=True)
    config.write_text("{}")
    expected = {k: "pinned" for k in ("python", "packages", "diffusers_commit", "torch", "cuda", "gpu")}
    review = {"environment": expected, "base_model_index_sha256": sha256(b"{}").hexdigest()}
    monkeypatch.setattr(adjustment, "ROOT", root)
    monkeypatch.setattr(helpers, "check_ports", lambda: None)
    monkeypatch.setattr(original, "verify_bundle", lambda: ({}, review))
    commands = []
    def run(args, output, name, env):
        commands.append(args)
        if name == "environment.log":
            observed = dict(expected)
            if drift == "environment":
                observed["torch"] = "changed"
            (output / name).write_text(json.dumps(observed))
    monkeypatch.setattr(original, "run", run)
    if drift == "cache":
        (snapshot / "model_index.json").write_text("changed")
    started = []
    def popen(args, **kwargs):
        started.append((args, kwargs))
        return SimpleNamespace(stdout=iter(["MAKEUP_ADJUST DONE 9 / 9\n"]), wait=lambda: 0)
    monkeypatch.setattr(adjustment.subprocess, "Popen", popen)
    args = SimpleNamespace(output=tmp_path / "results-adjustment-new", plan=config,
                           reference=tmp_path / "results-resume-original", evidence=evidence_root / "adjustment-test")
    if drift:
        with pytest.raises(RuntimeError, match="changed|differs"):
            adjustment.bootstrap(args)
        assert not started
    else:
        adjustment.bootstrap(args)
        assert len(started) == 1 and started[0][1]["env"]["AI_MODEL_DIR"] == str(snapshot)
        assert "--reference" in started[0][0]
        assert json.loads((args.evidence / "cache-reuse.json").read_text())["downloaded_again"] is False
    assert all("pip" not in args and "--download-only" not in args for args in commands)


def test_cell_payloads_and_partial_download_preserve_previous_files(tmp_path, monkeypatch):
    import subprocess
    code = package.cell()
    assignments = {n.targets[0].id: ast.literal_eval(n.value) for n in ast.parse(code).body
                   if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name)
                   and n.targets[0].id in ("QA2_FILES", "QA2_ORIGINAL")}
    for name, row in assignments["QA2_FILES"].items():
        raw = base64.b64decode(row["data"], validate=True)
        assert raw == (ROOT / name).read_bytes()
        assert sha256(raw).hexdigest() == row["sha256"]
    work = tmp_path / "beautycore-makeup-quality-test"
    (work / "gpu-src").mkdir(parents=True)
    (work / "setup-evidence").mkdir()
    (work / "candidate.json").write_text(json.dumps(assignments["QA2_ORIGINAL"]))
    oldbook = json.loads((ROOT / "artifacts/makeup-quality-20261025/beautycore_makeup_quality_diagnostic.ipynb").read_text())
    oldcode = "".join(oldbook["cells"][1]["source"])
    files = next(ast.literal_eval(n.value) for n in ast.parse(oldcode).body
                 if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name) and n.targets[0].id == "FILES")
    for name, row in files.items():
        target = work / "gpu-src" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(base64.b64decode(row["data"]))
    reference = work / "results-resume-original"
    reference.mkdir()
    raw = (ROOT / "artifacts/makeup-quality-20261025/review-db42b690b2/results/report.json").read_bytes()
    (reference / "report.json").write_bytes(raw)
    hashes = {str(p.relative_to(work)): sha256(p.read_bytes()).hexdigest()
              for p in work.rglob("*") if p.is_file()}
    calls = []
    def fail(args, cwd, check):
        calls.append(args)
        output = Path(args[args.index("--output") + 1])
        output.mkdir()
        (output / "report.json").write_text('{"status":"FAILED"}')
        evidence = Path(args[args.index("--evidence") + 1])
        evidence.mkdir()
        (evidence / "adjustment.log").write_text("synthetic failure")
        raise subprocess.CalledProcessError(1, args)
    monkeypatch.setattr(subprocess, "run", fail)
    # Redirect only the strict Kaggle parent literal for the local execution test.
    tree = ast.parse(code)
    class Redirect(ast.NodeTransformer):
        def visit_Constant(self, node):
            if node.value == "/kaggle/working":
                return ast.copy_location(ast.Constant(value=str(tmp_path)), node)
            return node
    compiled = compile(ast.fix_missing_locations(Redirect().visit(tree)), "adjustment-cell", "exec")
    namespace = {"MAKEUP_WORK": work}
    with pytest.raises(subprocess.CalledProcessError):
        exec(compiled, namespace)
    assert len(calls) == 1
    zip_path = next(work.glob("beautycore-makeup-adjustment-results-*.zip"))
    with ZipFile(zip_path) as archive:
        assert "results/report.json" in archive.namelist()
        assert "experiment-sources/data/makeup/MAKEUP-QA-002/plan.json" in archive.namelist()
        assert any(name.endswith("adjustment.log") for name in archive.namelist())
    for name, digest in hashes.items():
        assert sha256((work / name).read_bytes()).hexdigest() == digest
    with pytest.raises(RuntimeError, match="already attempted"):
        exec(compiled, namespace)
    assert len(calls) == 1
    output_cell = tmp_path / "prepared.py"
    assert package.build(output_cell)["expected_new_calls"] == 9
    assert output_cell.read_text() == code
    with pytest.raises(ValueError, match="overwrite"):
        package.build(output_cell)



def test_shared_adapter_helpers_match_frozen_kaggle_diagnostic():
    book = json.loads((ROOT / "artifacts/makeup-quality-20261025/beautycore_makeup_quality_diagnostic.ipynb").read_text())
    files = next(ast.literal_eval(n.value) for n in ast.parse("".join(book["cells"][1]["source"])).body
                 if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name) and n.targets[0].id == "FILES")
    frozen = base64.b64decode(files["scripts/makeup_quality_diagnostic.py"]["data"]).decode()
    current = (ROOT / "scripts/makeup_quality_diagnostic.py").read_text()
    def helpers(code):
        return {n.name: ast.dump(n, include_attributes=False) for n in ast.parse(code).body
                if isinstance(n, ast.FunctionDef) and n.name in ("adapter_condition", "layer_scaling", "verify_scaling")}
    assert len(helpers(frozen)) == 3 and helpers(frozen) == helpers(current)

