"""CPU-only compatibility checks for the frozen adapter and future switching."""

from pathlib import Path
import sys

from app.registry import enabled_styles, load_registry, styles_for_adapter
from app.styles import REAL_STYLE_PROMPTS


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.kaggle_inference_server import FluxRuntime, read_adapter_metadata  # noqa: E402


def test_train001_registry_and_bundle_remain_unchanged():
    registry = load_registry()
    assert [item["style_id"] for item in enabled_styles(registry)] == [
        "crew_cut", "bob_hair", "layered_hair"]
    assert styles_for_adapter(registry, "train001") == set(REAL_STYLE_PROMPTS)
    metadata = read_adapter_metadata(ROOT / "artifacts/train001_adapter_bundle", "train001")
    assert metadata["checkpoint_sha256"] == registry["adapters"]["train001"]["checkpoint_sha256"]
    assert metadata["training_steps"] == 250


class FakePipe:
    def __init__(self, fail=None):
        self.active = "train001"
        self.fail = fail
        self.calls = []

    def unload_lora_weights(self):
        self.calls.append("unload")
        self.active = None

    def load_lora_weights(self, directory, **kwargs):
        adapter = kwargs.get("adapter_name", "train001")
        self.calls.append(("load", adapter))
        if adapter == self.fail:
            raise RuntimeError("simulated adapter failure")
        self.active = adapter

    def set_adapters(self, adapter):
        self.calls.append(("set", adapter))


def test_switch_has_one_active_adapter_and_returns_to_frozen_train001():
    runtime = FluxRuntime()
    runtime.pipe = FakePipe()
    runtime.adapters = {name: (Path(name), {}) for name in ("train001", "train002")}
    runtime.active_adapter = "train001"
    runtime.activate_adapter("train002")
    assert runtime.pipe.active == runtime.active_adapter == "train002"
    runtime.activate_adapter("train001")
    assert runtime.pipe.active == runtime.active_adapter == "train001"
    assert runtime.pipe.calls == ["unload", ("load", "train002"), ("set", "train002"),
                                  "unload", ("load", "train001")]


def test_failed_switch_restores_train001():
    runtime = FluxRuntime()
    runtime.pipe = FakePipe(fail="train002")
    runtime.adapters = {name: (Path(name), {}) for name in ("train001", "train002")}
    runtime.active_adapter = "train001"
    runtime.ready = True
    try:
        runtime.activate_adapter("train002")
    except RuntimeError:
        pass
    else:
        raise AssertionError("Expected simulated switch failure")
    assert runtime.ready is True
    assert runtime.pipe.active == runtime.active_adapter == "train001"
