"""Initialization hook for verified approved Hair worker releases.

Installed only in a fresh, hash-verified worker workspace. Original training
registries, checkpoint metadata and original generation methods stay intact.
"""
import base64
from io import BytesIO
import math
import time
from PIL import Image, ImageOps

from app.hair_profiles import (STYLE_IDS, hair_candidates, expected_contract,
                               worker_capabilities)


def install(server):
    if getattr(server, "_hair_release_installed", False):
        raise RuntimeError("Hair release hook is already installed")
    if server.runtime.ready or server.runtime.base_loaded or server.runtime.owner is not None:
        raise RuntimeError("Do not change a running worker")
    additions = hair_candidates()
    if not additions:
        raise ValueError("Hair release requires approved installed Hair profiles")
    enabled_ids = {c.id for c in additions}
    original_runtime = server.FluxRuntime
    original_contract = server.expected_contract
    original_unified_runtime = server.UnifiedRuntime

    class ProfiledHairRuntime(original_runtime):
        def generate(self, image, style_id):
            if style_id not in enabled_ids:
                return super().generate(image, style_id)
            contract = expected_contract(style_id, self.metadata)
            if self.active_adapter != contract["adapter_id"] or self.active_adapter not in self.adapters:
                raise RuntimeError("Approved Hair requires its verified active adapter")
            pipe, torch = self.pipe, self.torch
            active = pipe.get_active_adapters()
            if len(active) != 1:
                raise RuntimeError("Approved Hair adapter state is uncertain")
            name = active[0]
            defaults = {}
            for key, module in pipe.transformer.named_modules():
                if hasattr(module, "lora_A"):
                    if (set(module.lora_A) != {name} or set(module.lora_B) != {name}
                            or module.disable_adapters or module.merged
                            or list(module.active_adapters) != [name]):
                        raise RuntimeError("Approved Hair LoRA layer is not isolated")
                    defaults[key] = float(module.scaling[name])
            if not defaults or any(not math.isfinite(v) or v <= 0 for v in defaults.values()):
                raise RuntimeError("Approved Hair has no valid LoRA scaling")
            pipe.set_adapters(name, adapter_weights=1.0)
            for key, module in pipe.transformer.named_modules():
                if key in defaults and not math.isclose(float(module.scaling[name]), defaults[key], rel_tol=1e-6):
                    raise RuntimeError("Approved Hair adapter influence differs from full loaded scaling")
            source = ImageOps.pad(image, (512, 512), method=Image.Resampling.LANCZOS,
                                  color=(245, 245, 245), centering=(.5, .5))
            torch.cuda.reset_peak_memory_stats(0)
            started = time.monotonic()
            with torch.no_grad():
                result = pipe(prompt=contract["prompt"], image=source, width=512, height=512,
                              num_inference_steps=20, guidance_scale=4.0,
                              generator=torch.Generator(device="cuda").manual_seed(1977)).images[0].convert("RGB")
            torch.cuda.synchronize(0)
            if result.size != (512, 512):
                raise RuntimeError("Approved Hair output dimensions differ")
            stream = BytesIO()
            result.save(stream, "PNG")
            return {"status": "completed", "generator": contract["generator"],
                    "image": {"data_url": "data:image/png;base64," + base64.b64encode(stream.getvalue()).decode(),
                              "content_type": "image/png", "width": 512, "height": 512},
                    "metadata": {**{k: v for k, v in contract.items() if k != "generator"},
                                 "runtime_seconds": round(time.monotonic() - started, 3),
                                 "peak_gpu_mib": round(torch.cuda.max_memory_allocated(0) / 1024**2, 1)}}

    def contract(feature, style_id, adapter_id=None, adapter_meta=None):
        if feature == "hairstyle" and style_id in enabled_ids:
            if adapter_id != expected_contract(style_id)["adapter_id"]:
                raise ValueError("Approved Hair was routed to the wrong adapter")
            return expected_contract(style_id, adapter_meta)
        return original_contract(feature, style_id, adapter_id, adapter_meta)

    class ReleaseRuntime(original_unified_runtime):
        def health(self):
            report = super().health()
            report["style_capabilities"] = worker_capabilities({
                "hairstyle": sorted(server.HAIR_STYLES),
                "makeup": sorted(server.MAKEUP_PROMPTS), "nails": sorted(server.MODEL_STYLES),
            })
            return report

    # This dictionary controls public routing only. REGISTRY and the checkpoint's
    # supported_style_ids remain unchanged and retain their original validators.
    server.HAIR_STYLES = {**server.HAIR_STYLES, **{c.id: {
        "adapter_id": expected_contract(c.id)["adapter_id"], "prompt": expected_contract(c.id)["prompt"],
    } for c in additions}}
    server.FluxRuntime = ProfiledHairRuntime
    server.expected_contract = contract
    server.UnifiedRuntime = ReleaseRuntime
    server.runtime = ReleaseRuntime()
    server._hair_release_installed = True
    return server
