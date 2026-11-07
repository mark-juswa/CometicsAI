"""Private diagnostic orchestration only; mocked pipeline is not model evidence."""
from hashlib import sha256
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts import makeup_reference_diagnostic as diagnostic


def setup_runner(tmp_path, monkeypatch, *, fail_second=False):
    import torch
    from scripts import unified_gate1 as gate, unified_gate2 as gate2, makeup_quality_diagnostic as quality
    from app import makeup_contract as contract

    root = tmp_path / "gpu-src"
    fixture_dir = tmp_path / "fixtures"
    fixture_dir.mkdir()
    plan = json.loads(diagnostic.PLAN.read_text())
    for number, row in enumerate(plan["cases"]):
        for kind in ("source", "guide", "previous"):
            path = fixture_dir / row[kind + "_filename"]
            Image.new("RGB", (512, 512), (number * 70, 30 if kind == "source" else 170, 50)).save(path)
            row[kind + "_sha256"] = sha256(path.read_bytes()).hexdigest()
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps(plan))
    model = tmp_path / contract.MODEL_REVISION
    model.mkdir()
    (model / "model_index.json").write_text("mock model index, not weights")
    review = {"environment": {"cuda_available": True},
              "base_model_index_sha256": sha256((model / "model_index.json").read_bytes()).hexdigest()}
    review_path = root / "docs/experiments/unified-kaggle-gate2-review.json"
    review_path.parent.mkdir(parents=True)
    review_path.write_text(json.dumps(review))
    monkeypatch.setattr(diagnostic, "ROOT", root)
    monkeypatch.setenv("AI_MODEL_DIR", str(model))
    monkeypatch.setattr(gate, "environment", lambda: review["environment"])
    monkeypatch.setattr(contract, "verify_adapter", lambda path: None)
    monkeypatch.setattr(gate2, "inspect_adapter", lambda *args: {"library_adapter_name": "verified_mock"})
    monkeypatch.setattr(gate2, "fingerprint", lambda pipe: {"pipeline": id(pipe)})
    monkeypatch.setattr(quality, "layer_scaling", lambda *args: {"mock": 1.0})
    factors = []
    monkeypatch.setattr(quality, "verify_scaling", lambda pipe, name, defaults, factor:
                        factors.append(factor) or {"relative_factor": factor})
    for name in ("reset_peak_memory_stats", "synchronize"):
        monkeypatch.setattr(torch.cuda, name, lambda *args: None)
    monkeypatch.setattr(torch.cuda, "max_memory_allocated", lambda *args: 0)
    monkeypatch.setattr(torch, "Generator", lambda **kwargs: SimpleNamespace(manual_seed=lambda seed: seed))
    calls = []
    loads = []

    class Pipeline:
        @classmethod
        def from_pretrained(cls, path, **kwargs):
            assert Path(path) == model and kwargs["local_files_only"] is True
            loads.append(path)
            return cls()

        def enable_model_cpu_offload(self, gpu_id):
            assert gpu_id == 0

        def load_lora_weights(self, path, weight_name):
            assert Path(path) == root / "gate1/adapters/makeup"
            assert weight_name == "adapter.safetensors"

        def __call__(self, **kwargs):
            calls.append(kwargs)
            if fail_second and len(calls) == 2:
                raise RuntimeError("controlled GPU-like failure")
            return SimpleNamespace(images=[Image.new("RGB", (512, 512), "purple")])

    monkeypatch.setitem(sys.modules, "diffusers", SimpleNamespace(Flux2KleinPipeline=Pipeline))
    return plan_path, plan, calls, loads, factors


def test_two_separate_identity_calls_and_raw_output(tmp_path, monkeypatch):
    plan_path, plan, calls, loads, factors = setup_runner(tmp_path, monkeypatch)
    output = tmp_path / "results"
    diagnostic.run(output, plan_path)
    report = json.loads((output / "report.json").read_text())
    assert len(calls) == 2 and len(loads) == 1 and factors == [1.0, 1.0]
    for number, call in enumerate(calls):
        assert len(call["image"]) == 2
        assert call["image"][0].getpixel((0, 0))[1] == 30
        assert call["image"][1].getpixel((0, 0))[1] == 170
        assert call["generator"] == 1977 and call["guidance_scale"] == 4.0
        assert call["num_inference_steps"] == 20
        assert "DIFFERENT person" in call["prompt"]
        assert report["cases"][number]["prompt"] == call["prompt"]
        image = Image.open(output / report["cases"][number]["output"]).convert("RGB")
        assert image.getpixel((0, 0)) == (128, 0, 128)
    assert report["status"] == "GENERATED_REQUIRES_VISUAL_REVIEW"
    assert report["postprocessing"] is None and report["production_enabled"] is False


def test_partial_result_survives_failure_without_retry(tmp_path, monkeypatch):
    plan_path, plan, calls, loads, factors = setup_runner(tmp_path, monkeypatch, fail_second=True)
    output = tmp_path / "results"
    with pytest.raises(RuntimeError, match="controlled GPU-like failure"):
        diagnostic.run(output, plan_path)
    report = json.loads((output / "report.json").read_text())
    assert len(calls) == 2 and len(loads) == 1
    assert report["status"] == "FAILED" and len(report["cases"]) == 1
    assert (output / report["cases"][0]["output"]).is_file()
    assert report["error_type"] == "RuntimeError"
