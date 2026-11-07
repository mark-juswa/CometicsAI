"""Manga-only completion scope, retained controls and partial evidence without GPU."""
import ast
import base64
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import sys
from PIL import Image
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "backend")]
from scripts import makeup_expansion_completion as runner
from scripts import package_makeup_expansion_completion as package
from test_makeup_quality_diagnostic import setup_fake_runtime


def plan():
    return json.loads((ROOT / package.FILES[-1]).read_text(encoding="utf-8"))


@pytest.mark.parametrize("field,value", [
    ("production_enabled", True), ("training", True), ("automatic_promotion", True),
    ("white_cast_fix_claimed", True), ("expected_new_calls", 4),
    ("inference", {"width": 512, "height": 512, "steps": 20, "seed": 1977, "guidance": 4.0, "adapter_weight": 1.0}),
])
def test_fixed_scope_rejects_extra_calls_production_and_false_fix_claim(field, value):
    p = plan()
    p[field] = value
    with pytest.raises(ValueError, match="scope differs"):
        runner.cases(p)


def fixture(tmp_path, monkeypatch):
    pipe, loader, _ = setup_fake_runtime(tmp_path, monkeypatch)
    p = plan()
    root = tmp_path / "gpu-src"
    folder = tmp_path / "fixtures"
    for i, subject in enumerate(p["subjects"]):
        path = folder / subject["filename"]
        Image.new("RGB", (512, 512), (80 + i * 20, 90, 100)).save(path)
        subject["sha256"] = sha256(path.read_bytes()).hexdigest()
    old = {"cases": []}
    for ref in p["retained_outputs"]:
        path = folder / ref["filename"]
        image = Image.new("RGB", (512, 512), (100, 80, 90))
        image.save(path)
        ref.update(png_sha256=sha256(path.read_bytes()).hexdigest(), rgb_sha256=sha256(image.tobytes()).hexdigest())
        old["cases"].append({**ref, "feature": "makeup", "kind": "existing" if ref["style_id"] == "soft_glam" else "candidate"})
    report = folder / p["reference_report_filename"]
    report.write_bytes(json.dumps(old).encode())
    p["reference_report_sha256"] = sha256(report.read_bytes()).hexdigest()
    p["continuity"]["rgb_sha256"] = p["retained_outputs"][0]["rgb_sha256"]
    adapter = root / "gate1/adapters/makeup"
    adapter.mkdir(parents=True)
    (adapter / "adapter.safetensors").write_bytes(b"synthetic-not-model-weights")
    config = tmp_path / "completion-plan.json"
    config.write_bytes(json.dumps(p).encode())
    monkeypatch.setattr(runner, "ROOT", root)
    return pipe, loader, config, p


def test_exact_three_calls_reuses_six_outputs_and_keeps_no_fix_claim(tmp_path, monkeypatch):
    pipe, loader, config, p = fixture(tmp_path, monkeypatch)
    output = tmp_path / "results"
    runner.run(output, config)
    report = json.loads((output / "report.json").read_text())
    assert report["status"] == "COMPLETE_REQUIRES_VISUAL_REVIEW"
    assert loader.calls == report["foundation_load_count"] == 1
    assert len(pipe.calls) == report["new_inference_calls"] == 3
    assert len(report["retained"]) == 6 and len(report["new_cases"]) == 3
    assert report["new_cases"][0]["continuity_pixels_match"]
    assert [r["style_id"] for r in report["new_cases"]] == ["soft_glam", "exp_manga_lash", "exp_manga_lash"]
    assert all(c["num_inference_steps"] == 20 and c["guidance_scale"] == 2.5 for c in pipe.calls)
    assert all(r["visual_verdict"] == "NEEDS_REVIEW" for r in report["new_cases"])
    assert report["white_cast_fix_claimed"] is False and report["production_enabled"] is False
    assert (output / "review-self-contained.html").read_text().count("src=\"data:image/png;base64,") == 10
    with pytest.raises(ValueError, match="fresh output"):
        runner.run(output, config)


def test_continuity_mismatch_stops_before_manga_and_retains_references(tmp_path, monkeypatch):
    pipe, _, config, p = fixture(tmp_path, monkeypatch)
    p["continuity"]["rgb_sha256"] = "0" * 64
    config.write_bytes(json.dumps(p).encode())
    with pytest.raises(RuntimeError, match="stop before generating Manga"):
        runner.run(tmp_path / "results", config)
    report = json.loads((tmp_path / "results/report.json").read_text())
    assert report["status"] == "FAILED" and len(pipe.calls) == 1
    assert len(report["retained"]) == 6 and not report["new_cases"][0]["continuity_pixels_match"]
    assert (tmp_path / "results/review-self-contained.html").is_file()


def test_corrupt_retained_png_stops_before_model_load(tmp_path, monkeypatch):
    pipe, loader, config, p = fixture(tmp_path, monkeypatch)
    (tmp_path / "fixtures" / p["retained_outputs"][0]["filename"]).write_bytes(b"wrong")
    with pytest.raises(ValueError, match="PNG differs"):
        runner.run(tmp_path / "results", config)
    assert loader.calls == 0 and not pipe.calls


def test_generation_failure_keeps_control_and_partial_images(tmp_path, monkeypatch):
    pipe, _, config, p = fixture(tmp_path, monkeypatch)
    pipe.fail_on = 3
    with pytest.raises(RuntimeError, match="synthetic"):
        runner.run(tmp_path / "results", config)
    report = json.loads((tmp_path / "results/report.json").read_text())
    assert report["status"] == "FAILED" and len(report["new_cases"]) == 2
    assert report["new_cases"][0]["continuity_pixels_match"]
    assert (tmp_path / "results/review-self-contained.html").is_file()


def test_notebook_hashes_embedded_assets_and_partial_archive_wrapper(tmp_path):
    target = tmp_path / "makeup.ipynb"
    receipt = package.build(target)
    assert receipt["new_inference_calls"] == 3 and receipt["retained_outputs"] == 6
    assert receipt["white_cast_fix_claimed"] is False
    book = json.loads(target.read_text())
    code = [c for c in book["cells"] if c["cell_type"] == "code"]
    assert len(code) == 2
    for cell in code:
        compile("".join(cell["source"]), "<completion-cell>", "exec")
        assert cell["execution_count"] is None and cell["outputs"] == []
    tree = ast.parse("".join(code[0]["source"]))
    values = {n.targets[0].id: ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign)
              and isinstance(n.targets[0], ast.Name) and n.targets[0].id in {"FILES", "ASSETS"}}
    assert len(values["ASSETS"]) == 9
    for name, row in values["FILES"].items():
        raw = base64.b64decode(row["data"], validate=True)
        assert sha256(raw).hexdigest() == row["sha256"] and raw == (ROOT / name).read_bytes()
    for row in values["ASSETS"].values():
        assert sha256(base64.b64decode(row["data"], validate=True)).hexdigest() == row["sha256"]
    assert "finally:" in "".join(code[1]["source"])
    assert "beautycore-makeup-expansion-results.zip" in "".join(code[1]["source"])
    assert "os.killpg" in "".join(code[1]["source"])
    with pytest.raises(ValueError, match="overwrite"):
        package.build(target)
