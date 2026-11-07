"""Offline coverage for experimental styles; no GPU or public inference."""
from contextlib import nullcontext
from hashlib import sha256
import json
from pathlib import Path
from types import SimpleNamespace
from zipfile import ZipFile

import numpy as np
from PIL import Image, ImageDraw
import pytest

ROOT = Path(__file__).resolve().parents[2]
import sys
sys.path.insert(0, str(ROOT))
from scripts.style_expansion_nails import render, run_suite, STYLES
from scripts.style_expansion_pilot import cases, runtime_case
from scripts.style_expansion_bootstrap import clean_environment
from scripts import package_style_expansion_pilot as package


def fixture(count=5):
    image = Image.new("RGB", (400, 400), (142, 105, 90))
    mask = Image.new("L", image.size)
    drawing = ImageDraw.Draw(mask)
    for x in range(count):
        drawing.ellipse((30 + x * 70, 150, 54 + x * 70, 192), fill=255)
    return image, mask


@pytest.mark.parametrize("style", STYLES)
def test_renderer_preserves_all_outside_pixels_and_edits_each_nail(style):
    image, mask = fixture()
    old_source, old_mask = image.tobytes(), mask.tobytes()
    result = render(image, mask, style)
    from app.nails.geometry import nail_components
    binary = np.asarray(mask) > 127
    changed = np.any(np.asarray(image) != np.asarray(result), axis=2)
    assert not changed[~binary].any()
    assert all(changed[c[:, 0], c[:, 1]].any() for c in nail_components(binary))
    assert render(image, mask, style).tobytes() == result.tobytes()
    assert image.tobytes() == old_source and mask.tobytes() == old_mask


def test_new_nail_designs_are_distinct_and_require_suitable_masks():
    image, mask = fixture()
    assert len({render(image, mask, style).tobytes() for style in STYLES}) == 3
    with pytest.raises(ValueError, match="Unsupported"):
        render(image, mask, "classic_red")
    with pytest.raises(ValueError, match="dimensions"):
        render(image, Image.new("L", (10, 10)), STYLES[0])
    with pytest.raises(ValueError, match="three to five"):
        render(image, Image.new("L", image.size), STYLES[0])
    with pytest.raises(ValueError, match="three to five"):
        render(image, Image.new("L", image.size, 255), STYLES[0])
    image, mask = fixture(2)
    with pytest.raises(ValueError, match="three to five"):
        render(image, mask, STYLES[0])


def test_renderer_rotated_masks_keep_background_and_require_no_hand_detector():
    image, mask = fixture()
    image, mask = image.rotate(31), mask.rotate(31)
    outside = np.asarray(mask) <= 127
    for style in STYLES:
        result = render(image, mask, style)
        assert np.array_equal(np.asarray(result)[outside], np.asarray(image)[outside])


def test_renderer_evidence_stays_unaccepted_and_cannot_overwrite(tmp_path):
    image, mask = fixture()
    source, mask_path = tmp_path / "hand.png", tmp_path / "mask.png"
    image.save(source)
    mask.save(mask_path)
    result = run_suite(source, mask_path, tmp_path / "output")
    assert result["status"] == "REQUIRES_VISUAL_REVIEW"
    assert not result["segmentation_tested"] and not result["trained_model"]
    assert all(row["changed_outside_mask_pixels"] == 0 for row in result["cases"])
    with pytest.raises(ValueError, match="new result"):
        run_suite(source, mask_path, tmp_path / "output")


def test_approved_pilot_has_exactly_fifteen_calls_and_does_not_enable_catalog():
    plan = json.loads((ROOT / "data/style-expansion/STYLE-EXP-001/pilot.json").read_text())
    sequence = cases(plan)
    assert plan["selection_approved"] and not plan["production_enabled"]
    assert len(sequence) == plan["expected_diffusion_outputs"] == 15
    proposed = [row for row in sequence if row["kind"] == "candidate"]
    assert len(proposed) == 8  # Six Hair adapter trials, two Makeup prompts.
    assert {row["adapter"] for row in proposed} == {"hairstyle:train001", "hairstyle:train002", "makeup"}
    assert len([row for row in sequence if row["kind"] == "restoration"]) == 2
    public = json.loads((ROOT / "beautycore/lib/business/style-catalog.json").read_text())
    from app.style_release import RELEASE
    accepted = {(c.feature, c.id) for c in RELEASE.candidates if c.review_status == "accepted"}
    # The pilot remains non-production; later explicit approvals may add its styles.
    assert all(row["style_id"] not in public[row["feature"]]
               or (row["feature"], row["style_id"]) in accepted for row in proposed)
    assert all(row["prompt"] for row in proposed)


def test_private_candidate_inference_uses_fixed_settings_and_verified_adapter():
    image = Image.new("RGB", (250, 400))
    events, calls = [], []
    class Generator:
        def __init__(self, device):
            assert device == "cuda"
        def manual_seed(self, seed):
            assert seed == 1977
            return self
    def pipe(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(images=[Image.new("RGB", (512, 512))])
    owner = SimpleNamespace(
        switch=lambda key: events.append(("switch", key)),
        assert_active=lambda key: events.append(("assert", key)) or {"verified": True},
        synchronize=lambda: events.append(("sync",)),
        pipe=pipe, torch=SimpleNamespace(Generator=Generator, inference_mode=nullcontext))
    case = {"kind": "candidate", "adapter": "hairstyle:train001", "prompt": "experimental instruction"}
    output, state = runtime_case(SimpleNamespace(owner=owner), None, case, image)
    assert output.size == (512, 512) and state["verified"]
    assert calls[0]["num_inference_steps"] == 20 and calls[0]["guidance_scale"] == 4.0
    assert calls[0]["image"].size == (512, 512)
    assert events[0] == ("switch", "hairstyle:train001")
    assert events[-1] == ("assert", "hairstyle:train001")


def test_pilot_child_removes_serving_keys_cache_and_stale_runtime_overrides():
    old = {key: "should-not-propagate" for key in (
        "AI_BACKEND_API_KEY", "AI_REMOTE_API_KEY", "GEMINI_API_KEY", "AI_MODEL_DIR",
        "HAIRCAPSTONE_STYLE_REGISTRY_PATH", "PYTHONPATH", "AI_PROMPT_CACHE", "LD_PRELOAD")}
    env = clean_environment(old)
    assert not set(old) & set(env)
    assert env["MPLBACKEND"] == "Agg" and env["CUDA_VISIBLE_DEVICES"] == "0"


def cell_namespace():
    code = package.preparation_cell({}, {})
    code = code.rsplit("\nSTYLE_WORK = prepare()", 1)[0]
    ns = {}
    exec(compile(code, "pilot-preparation", "exec"), ns)
    return ns


def synthetic_bundle(tmp_path, members=None, corrupt=False):
    members = members or {"safe/source.py": b"# fixture\n"}
    manifest = {"files": {name: sha256(raw).hexdigest() for name, raw in members.items()}}
    if corrupt:
        manifest["files"][next(iter(members))] = "0" * 64
    path = tmp_path / "synthetic.bin"
    with ZipFile(path, "w") as archive:
        for name, raw in members.items():
            archive.writestr(name, raw)
        archive.writestr("gate3_bundle.json", json.dumps(manifest))
    return path, sha256(path.read_bytes()).hexdigest()


def test_gpu_extraction_validates_bundle_members_and_preserves_original(tmp_path):
    ns = cell_namespace()
    bundle, digest = synthetic_bundle(tmp_path)
    original = bundle.read_bytes()
    ns["extract_gpu"](bundle, tmp_path / "output", digest)
    assert (tmp_path / "output/safe/source.py").read_bytes() == b"# fixture\n"
    assert bundle.read_bytes() == original
    with pytest.raises(ValueError, match="Fresh"):
        ns["extract_gpu"](bundle, tmp_path / "output", digest)
    with pytest.raises(ValueError, match="differs"):
        ns["extract_gpu"](bundle, tmp_path / "other", "0" * 64)


@pytest.mark.parametrize("name", ["../escaped.py", "/absolute.py", "C:/escape.py", "bad\\escape.py"])
def test_gpu_extraction_rejects_unsafe_member_paths(tmp_path, name):
    bundle, digest = synthetic_bundle(tmp_path, {name: b"invalid"})
    with pytest.raises(ValueError, match="Unsafe|inventory differs"):
        cell_namespace()["extract_gpu"](bundle, tmp_path / "output", digest)
    assert not (tmp_path / "escaped.py").exists()


def test_gpu_extraction_rejects_wrong_member_hash(tmp_path):
    bundle, digest = synthetic_bundle(tmp_path, corrupt=True)
    with pytest.raises(ValueError, match="member differs"):
        cell_namespace()["extract_gpu"](bundle, tmp_path / "output", digest)


@pytest.mark.parametrize("count", [0, 2])
def test_input_failure_reports_actual_count_before_any_extraction(tmp_path, count, capsys):
    ns = cell_namespace()
    class Connection:
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def settimeout(self, value): pass
        def connect_ex(self, address): return 1
    ns["sys"] = SimpleNamespace(platform="linux")
    ns["socket"] = SimpleNamespace(socket=Connection)
    inputs = tmp_path / "input"
    inputs.mkdir()
    for number in range(count):
        folder = inputs / str(number)
        folder.mkdir()
        (folder / ns["BUNDLE"]).write_bytes(b"duplicate fixture")
    working = tmp_path / "working"
    working.mkdir()
    with pytest.raises(ValueError, match="exactly ONE"):
        ns["prepare"](inputs, working)
    assert f"GPU bundle matches: {count}" in capsys.readouterr().out
    assert not list(working.iterdir())


def test_notebook_embeds_only_expected_files_and_starts_no_public_service(tmp_path, monkeypatch):
    fixtures = {}
    for name in ("hand.png", "mask.png"):
        path = tmp_path / name
        Image.new("RGB", (8, 8)).save(path)
        fixtures[name] = (path, sha256(path.read_bytes()).hexdigest())
    monkeypatch.setattr(package, "ASSETS", fixtures)
    path = tmp_path / "pilot.ipynb"
    report = package.build(path)
    book = json.loads(path.read_text())
    assert report["includes_private_fixture"] and not report["includes_weights"] and not report["includes_secrets"]
    assert len(book["cells"]) == 3
    for cell in book["cells"][1:]:
        compile("".join(cell["source"]), str(path), "exec")
        assert cell["outputs"] == [] and cell["execution_count"] is None
    assert all(Path(name).suffix in (".py", ".json") for name in package.FILES)
    with pytest.raises(ValueError, match="overwrite"):
        package.build(path)
    bootstrap = (ROOT / "scripts/style_expansion_bootstrap.py").read_text()
    assert "Popen" in bootstrap
    assert "uvicorn" not in bootstrap and "cloudflared" not in bootstrap and "register_runtime" not in bootstrap


def test_preparation_refuses_an_active_worker_before_creating_workspaces(tmp_path):
    ns = cell_namespace()
    class Busy:
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def settimeout(self, value): pass
        def connect_ex(self, address): return 0
    ns["sys"] = SimpleNamespace(platform="linux")
    ns["socket"] = SimpleNamespace(socket=Busy)
    with pytest.raises(RuntimeError, match="service is running"):
        ns["prepare"](tmp_path, tmp_path / "working")
    assert not (tmp_path / "working").exists()


def test_execution_preserves_partial_results_and_never_packages_model_files(tmp_path, monkeypatch):
    import subprocess
    work = tmp_path / "pilot"
    work.mkdir()
    (work / "candidate.json").write_text("{}")
    (work / "weights.safetensors").write_bytes(b"never export")
    def fake_child(args, cwd, check):
        assert check and str(args[-1]).endswith("style_expansion_bootstrap.py")
        folder = work / "results/portraits"
        folder.mkdir(parents=True)
        (folder / "report.json").write_text('{"status":"FAILED"}')
        raise subprocess.CalledProcessError(1, args)
    monkeypatch.setattr(subprocess, "run", fake_child)
    with pytest.raises(subprocess.CalledProcessError):
        exec(compile(package.EXECUTION_CELL, "pilot-execution", "exec"), {"STYLE_WORK": work, "sys": sys})
    with ZipFile(work / "beautycore-style-expansion-results.zip") as archive:
        assert set(archive.namelist()) == {"results/portraits/report.json", "candidate.json"}
    with pytest.raises(RuntimeError, match="already ran"):
        exec(compile(package.EXECUTION_CELL, "pilot-execution", "exec"), {"STYLE_WORK": work, "sys": sys})


def test_scratch_cache_uses_a_volume_with_enough_space_and_preserves_other_files(tmp_path):
    from scripts.style_expansion_bootstrap import select_cache_home, MIN_SCRATCH_BYTES
    small, large = tmp_path / "small", tmp_path / "large"
    small.mkdir()
    large.mkdir()
    marker = large / "existing.txt"
    marker.write_text("keep")
    def usage(path):
        return SimpleNamespace(free=MIN_SCRATCH_BYTES - 1 if path == small else MIN_SCRATCH_BYTES + 1)
    home, observations = select_cache_home(tmp_path / "beautycore-styles-test",
                                           bases=(small, large), disk_usage=usage)
    assert home.is_relative_to(large)
    assert observations[0]["reason"] == "insufficient_space"
    assert observations[1]["usable"]
    assert marker.read_text() == "keep"
    assert not list(home.glob("write-probe-*"))
    assert not (small / "beautycore-style-pilot-hf").exists()


def test_insufficient_scratch_never_lowers_the_original_guard(tmp_path):
    from scripts.style_expansion_bootstrap import select_cache_home, MIN_SCRATCH_BYTES
    with pytest.raises(RuntimeError, match="30 GiB") as error:
        select_cache_home(tmp_path / "work", bases=(tmp_path,),
                          disk_usage=lambda path: SimpleNamespace(free=MIN_SCRATCH_BYTES - 1))
    assert error.value.observations[0]["reason"] == "insufficient_space"
    assert not (tmp_path / "beautycore-style-pilot-hf").exists()


def test_scratch_resume_requires_the_exact_failure_and_no_existing_results(tmp_path):
    from scripts.style_expansion_bootstrap import validate_scratch_resume, SCRATCH_FAILURE
    with pytest.raises(RuntimeError, match="only"):
        validate_scratch_resume(tmp_path)
    (tmp_path / "setup-evidence").mkdir()
    (tmp_path / "setup-evidence/base_download.log").write_text("network failed")
    with pytest.raises(RuntimeError, match="only"):
        validate_scratch_resume(tmp_path)
    (tmp_path / "setup-evidence/base_download.log").write_text(SCRATCH_FAILURE)
    (tmp_path / "candidate.json").write_text("{}")
    (tmp_path / "overlay").mkdir()
    assert validate_scratch_resume(tmp_path).name == "base_download.log"
    (tmp_path / "results").mkdir()
    with pytest.raises(RuntimeError, match="Results already exist"):
        validate_scratch_resume(tmp_path)


def test_scratch_resume_rechecks_host_and_dependencies_without_reinstalling(tmp_path, monkeypatch):
    from scripts import style_expansion_bootstrap as bootstrap
    work, root = tmp_path / "beautycore-styles-test", tmp_path / "beautycore-styles-test/gpu-src"
    root.mkdir(parents=True)
    (work / "setup-evidence").mkdir()
    old = work / "setup-evidence/base_download.log"
    old.write_text(bootstrap.SCRATCH_FAILURE)
    (work / "candidate.json").write_text("{}")
    (work / "overlay").mkdir()
    expected = {"python": "reviewed", "torch": "reviewed", "cuda": "reviewed", "gpu": "reviewed",
                "packages": {}, "diffusers_commit": "reviewed"}
    monkeypatch.setattr(bootstrap, "ROOT", root)
    monkeypatch.setattr(bootstrap, "check_ports", lambda: None)
    monkeypatch.setattr(bootstrap.original, "verify_bundle", lambda: ({}, {"environment": expected}))
    monkeypatch.setattr(bootstrap.subprocess, "run", lambda *a, **k: SimpleNamespace(stdout=json.dumps(expected)))
    home = tmp_path / "scratch/model-cache"
    home.mkdir(parents=True)
    monkeypatch.setattr(bootstrap, "select_cache_home", lambda work: (home, [{"usable": True}]))
    stages = []
    def fake_stage(args, output, name, env):
        stages.append(name)
        if name == "environment.log":
            (output / name).write_text(json.dumps(expected))
        elif name == "base_download.log":
            assert env["HF_HOME"] == str(home)
            raise RuntimeError("stop before model download")
        elif name != "artifact_preflight.log":
            raise AssertionError("Unexpected stage or reinstall")
    monkeypatch.setattr(bootstrap.original, "run", fake_stage)
    with pytest.raises(RuntimeError, match="stop before model download"):
        bootstrap.bootstrap(resume=True)
    assert stages == ["environment.log", "artifact_preflight.log", "base_download.log"]
    assert old.read_text() == bootstrap.SCRATCH_FAILURE
    assert len(list((work / "setup-evidence").glob("scratch-recovery-*"))) == 1


def test_recovery_payload_hashes_current_fix_and_requires_old_workspace():
    import ast
    import base64
    code = package.recovery_cell()
    values = {n.targets[0].id: ast.literal_eval(n.value) for n in ast.parse(code).body
              if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name)
              and n.targets[0].id in ("SOURCE", "EXPECTED")}
    raw = base64.b64decode(values["SOURCE"], validate=True)
    assert sha256(raw).hexdigest() == values["EXPECTED"]
    assert raw == (ROOT / "scripts/style_expansion_bootstrap.py").read_bytes()
    with pytest.raises(RuntimeError, match="workspace is unavailable"):
        exec(compile(code, "scratch-recovery", "exec"), {})


def test_recovery_zip_preserves_the_old_failure_and_packages_new_progress(tmp_path, monkeypatch):
    import subprocess
    work = tmp_path / "beautycore-styles-test"
    (work / "gpu-src/scripts").mkdir(parents=True)
    (work / "setup-evidence").mkdir()
    from scripts.style_expansion_bootstrap import SCRATCH_FAILURE
    original_log = work / "setup-evidence/base_download.log"
    original_log.write_text(SCRATCH_FAILURE)
    (work / "candidate.json").write_text("{}")
    old_zip = work / "beautycore-style-expansion-results.zip"
    old_zip.write_bytes(b"preserve original evidence")
    def fake_run(args, cwd, check):
        assert "--resume-after-scratch-failure" in args
        report = work / "results/portraits"
        report.mkdir(parents=True)
        (report / "report.json").write_text('{"status":"synthetic"}')
    monkeypatch.setattr(subprocess, "run", fake_run)
    code = package.recovery_cell().replace("Path('/kaggle/working')", repr(tmp_path))
    # repr WindowsPath is not executable without its constructor in scope; use Path literal.
    code = code.replace(repr(tmp_path), "Path(" + repr(str(tmp_path)) + ")")
    exec(compile(code, "scratch-recovery", "exec"), {"STYLE_WORK": work})
    archives = list(work.glob("beautycore-style-expansion-recovery-results-*.zip"))
    assert len(archives) == 1
    with ZipFile(archives[0]) as archive:
        assert "setup-evidence/base_download.log" in archive.namelist()
        assert "results/portraits/report.json" in archive.namelist()
    assert old_zip.read_bytes() == b"preserve original evidence"
    assert original_log.read_text() == SCRATCH_FAILURE
