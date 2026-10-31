"""Synthetic pipeline for Hair profile arguments and scaling tests; no model loading."""
from types import SimpleNamespace
from PIL import Image

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
