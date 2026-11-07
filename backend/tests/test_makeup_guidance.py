"""Five-call guidance follow-up; synthetic CPU checks, no real GPU generation."""
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
from scripts import makeup_guidance_diagnostic as adjustment
from scripts import makeup_adjustment_diagnostic as previous
from scripts import package_makeup_guidance as package
from test_makeup_adjustment import prepared as prepare_previous
from test_makeup_quality_diagnostic import FakePipe, install_offload_reproduction


def plan():
    return json.loads((ROOT / "data/makeup/MAKEUP-QA-003/plan.json").read_text())


def prepared(tmp_path, monkeypatch):
    oldconfig, oldreference, _, loader = prepare_previous(tmp_path, monkeypatch)
    reference = tmp_path / "results-adjustment-original"
    previous.run(reference, oldconfig, oldreference)
    config = plan()
    old = json.loads((reference / "report.json").read_text())
    config["subjects"] = old["subjects"]
    config["reference_report_sha256"] = sha256((reference / "report.json").read_bytes()).hexdigest()
    config["reference_plan_sha256"] = old["plan_sha256"]
    path = tmp_path / "gpu-src/data/makeup/MAKEUP-QA-003/plan-test.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(config))
    monkeypatch.setattr(adjustment, "ROOT", tmp_path / "gpu-src")
    pipe = FakePipe()
    loader.calls = 0
    def load(cls, *args, **kwargs):
        cls.calls += 1
        assert kwargs["local_files_only"]
        return pipe
    monkeypatch.setattr(loader, "from_pretrained", classmethod(load))
    return path, reference, pipe, loader


@pytest.mark.parametrize("field,value", [
    ("production_enabled", True), ("new_training", True),
    ("inference", {"steps": 10}), ("conditions", [{"guidance": 2.0}])])
def test_rejects_scope_and_unapproved_guidance(field, value):
    candidate = plan()
    candidate[field] = value
    with pytest.raises(ValueError, match="differs"):
        adjustment.validate_plan(candidate)


def test_only_guidance_changes_and_original_prompts_remain():
    from app.makeup_contract import PROMPTS
    cases = adjustment.matrix(plan())
    assert len(cases) == 12
    assert [x["guidance"] for x in cases] == [4.] * 4 + [3.] * 4 + [2.5] * 4
    assert {x["adapter_weight"] for x in cases} == {1.0}
    assert {x["prompt_variant"] for x in cases} == {"original"}
    for style in plan()["styles"]:
        assert adjustment.prompt_for(style, "original") == PROMPTS[style]
    with pytest.raises(ValueError, match="Only the original"):
        adjustment.prompt_for("natural_makeup", "matched_foundation")


def test_five_calls_keep_eight_controls_and_restore_full_adapter(tmp_path, monkeypatch):
    config, reference, pipe, loader = prepared(tmp_path, monkeypatch)
    originals = {p.name: sha256(p.read_bytes()).hexdigest() for p in reference.iterdir() if p.is_file()}
    output = tmp_path / "results-guidance-new"
    adjustment.run(output, config, reference)
    r = json.loads((output / "report.json").read_text())
    assert r["status"] == "DIAGNOSTIC_COMPLETE_REQUIRES_VISUAL_REVIEW"
    assert r["new_inference_calls"] == len(pipe.calls) == 5 and loader.calls == 1
    assert len(r["cases"]) == 12 and sum(x["retained"] for x in r["cases"]) == 8
    assert r["continuity_check"]["pixels_match"] and r["continuity_check"]["guidance"] == 3.
    assert [x["guidance_scale"] for x in pipe.calls] == [3.] + [2.5] * 4
    assert all(x["num_inference_steps"] == 20 for x in pipe.calls)
    assert pipe.weight == 1. and r["restorations"][0]["scaling_restored"]
    for name, digest in originals.items():
        assert sha256((reference / name).read_bytes()).hexdigest() == digest
    for row in r["cases"][:8]:
        assert (output / row["output"]).read_bytes() == (reference / row["output"]).read_bytes()
    assert len(list(output.glob("*comparison.jpg"))) == 2
    with pytest.raises(ValueError, match="new output"):
        adjustment.run(output, config, reference)


def test_control_mismatch_stops_before_guidance25(tmp_path, monkeypatch):
    config, reference, pipe, _ = prepared(tmp_path, monkeypatch)
    original = FakePipe.__call__
    def changed(self, **kwargs):
        result = original(self, **kwargs)
        result.images = [Image.new("RGB", (512, 512), (1, 2, 3))]
        return result
    monkeypatch.setattr(FakePipe, "__call__", changed)
    output = tmp_path / "results-guidance-new"
    with pytest.raises(RuntimeError, match="Continuity pixels differ"):
        adjustment.run(output, config, reference)
    r = json.loads((output / "report.json").read_text())
    assert r["new_inference_calls"] == len(pipe.calls) == 1
    assert len(r["cases"]) == 8 and pipe.weight == 1.
    assert r["restorations"][0]["tensor_state_restored"]


def test_failure_keeps_partial_results_and_restores_adapter(tmp_path, monkeypatch):
    config, reference, pipe, _ = prepared(tmp_path, monkeypatch)
    pipe.fail_on = 3
    output = tmp_path / "results-guidance-new"
    with pytest.raises(RuntimeError, match="synthetic"):
        adjustment.run(output, config, reference)
    r = json.loads((output / "report.json").read_text())
    assert r["status"] == "FAILED" and r["new_inference_calls"] == 3
    assert len(r["cases"]) == 9 and pipe.weight == 1.


@pytest.mark.parametrize("target", ["report", "guidance3_image"])
def test_altered_reference_rejected_before_model_load(tmp_path, monkeypatch, target):
    config, reference, pipe, loader = prepared(tmp_path, monkeypatch)
    if target == "report":
        with (reference / "report.json").open("a") as stream:
            stream.write(" ")
    else:
        report = json.loads((reference / "report.json").read_text())
        row = next(r for r in report["cases"] if r["id"] == "lower_guidance")
        (reference / row["output"]).write_bytes(b"changed")
    with pytest.raises(ValueError, match="differs"):
        adjustment.run(tmp_path / "new", config, reference)
    assert not pipe.calls and loader.calls == 0


def test_real_torch_no_grad_restores_materialized_adapter(tmp_path, monkeypatch):
    import torch as real_torch
    config, reference, pipe, _ = prepared(tmp_path, monkeypatch)
    install_offload_reproduction(monkeypatch, real_torch)
    sys.modules["torch"].no_grad = real_torch.no_grad
    adjustment.run(tmp_path / "new", config, reference)
    assert len(pipe.calls) == 5 and pipe.weight == 1.


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
    config = root / "data/makeup/MAKEUP-QA-003/plan-test.json"
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
        return SimpleNamespace(stdout=iter(["MAKEUP_GUIDANCE DONE 5 / 5\n"]), wait=lambda: 0)
    monkeypatch.setattr(adjustment.subprocess, "Popen", popen)
    args = SimpleNamespace(output=tmp_path / "results-guidance-new", plan=config,
                           reference=tmp_path / "results-adjustment-original", evidence=evidence_root / "guidance-test")
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
                   and n.targets[0].id in ("QA3_FILES", "QA3_ORIGINAL")}
    for name, row in assignments["QA3_FILES"].items():
        raw = base64.b64decode(row["data"], validate=True)
        assert raw == (ROOT / name).read_bytes()
        assert sha256(raw).hexdigest() == row["sha256"]
    work = tmp_path / "beautycore-makeup-quality-test"
    (work / "gpu-src").mkdir(parents=True)
    (work / "setup-evidence").mkdir()
    (work / "candidate.json").write_text(json.dumps(assignments["QA3_ORIGINAL"]))
    oldbook = json.loads((ROOT / "artifacts/makeup-quality-20261025/beautycore_makeup_quality_diagnostic.ipynb").read_text())
    oldcode = "".join(oldbook["cells"][1]["source"])
    files = next(ast.literal_eval(n.value) for n in ast.parse(oldcode).body
                 if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name) and n.targets[0].id == "FILES")
    for name, row in files.items():
        target = work / "gpu-src" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(base64.b64decode(row["data"]))
    reference = work / "results-adjustment-original"
    reference.mkdir()
    raw = (ROOT / "artifacts/makeup-quality-20261025/adjustment-review-ebdbe64f35/results/report.json").read_bytes()
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
        (evidence / "guidance.log").write_text("synthetic failure")
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
    busy_lock = work / ".makeup-adjustment.lock"
    busy_lock.write_text("synthetic")
    with pytest.raises(RuntimeError, match="Another diagnostic"):
        exec(compiled, namespace)
    assert not calls
    busy_lock.unlink()
    with pytest.raises(subprocess.CalledProcessError):
        exec(compiled, namespace)
    assert len(calls) == 1
    zip_path = next(work.glob("beautycore-makeup-guidance-results-*.zip"))
    with ZipFile(zip_path) as archive:
        assert "results/report.json" in archive.namelist()
        assert "experiment-sources/data/makeup/MAKEUP-QA-003/plan.json" in archive.namelist()
        assert any(name.endswith("guidance.log") for name in archive.namelist())
    for name, digest in hashes.items():
        assert sha256((work / name).read_bytes()).hexdigest() == digest
    with pytest.raises(RuntimeError, match="already attempted"):
        exec(compiled, namespace)
    assert len(calls) == 1
    output_cell = tmp_path / "prepared.py"
    assert package.build(output_cell)["expected_new_calls"] == 5
    assert output_cell.read_text() == code
    with pytest.raises(ValueError, match="overwrite"):
        package.build(output_cell)

