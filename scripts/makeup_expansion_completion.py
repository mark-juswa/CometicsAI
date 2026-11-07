"""Complete only the missing Manga Lash expansion test; reuse verified prior looks."""
import argparse
import base64
from hashlib import sha256
import html
import json
import os
from pathlib import Path
import shutil
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "backend")]
PLAN = ROOT / "data/style-expansion/MAKEUP-EXP-002/plan.json"


def cases(plan):
    if (plan.get("schema") != "beautycore-makeup-expansion-completion-v1"
            or plan.get("experiment") != "MAKEUP-EXP-002"
            or any(plan.get(k) is not False for k in ("production_enabled", "automatic_promotion", "training", "white_cast_fix_claimed"))
            or plan.get("expected_new_calls") != 3
            or plan.get("inference") != {"width": 512, "height": 512, "steps": 20, "seed": 1977,
                                          "guidance": 2.5, "adapter_weight": 1.0}
            or [s.get("id") for s in plan.get("subjects", [])] != ["054109", "056266"]
            or not isinstance(plan.get("manga_prompt"), str) or not 30 <= len(plan["manga_prompt"]) <= 1800
            or len(plan.get("retained_outputs", [])) != 6):
        raise ValueError("Makeup completion scope differs")
    from app.makeup_contract import PROMPTS
    return [{"kind": "continuity", "subject_id": "054109", "style_id": "soft_glam", "prompt": PROMPTS["soft_glam"]},
            *[{"kind": "candidate", "subject_id": sid, "style_id": "exp_manga_lash", "prompt": plan["manga_prompt"]}
              for sid in ("054109", "056266")]]


def retain(output, plan):
    from PIL import Image
    fixture = ROOT.parent / "fixtures"
    report_path = fixture / plan["reference_report_filename"]
    if sha256(report_path.read_bytes()).hexdigest() != plan["reference_report_sha256"]:
        raise ValueError("Saved Makeup reference report differs")
    old = json.loads(report_path.read_text(encoding="utf-8"))
    result = []
    for ref in plan["retained_outputs"]:
        if Path(ref["filename"]).name != ref["filename"]:
            raise ValueError("Unsafe saved image path")
        original = next(r for r in old["cases"] if r["feature"] == "makeup" and r["kind"] != "restoration"
                        and r["subject_id"] == ref["subject_id"] and r["style_id"] == ref["style_id"])
        if (original["png_sha256"] != ref["png_sha256"] or original["rgb_sha256"] != ref["rgb_sha256"]
                or original["prompt_sha256"] != ref["prompt_sha256"] or original["guidance"] != 2.5
                or original["adapter_sha256"] != plan["adapter_sha256"]):
            raise ValueError("Saved Makeup case differs")
        source = fixture / ref["filename"]
        if sha256(source.read_bytes()).hexdigest() != ref["png_sha256"]:
            raise ValueError("Saved Makeup PNG differs")
        with Image.open(source) as image:
            if image.format != "PNG" or image.size != (512, 512) or sha256(image.convert("RGB").tobytes()).hexdigest() != ref["rgb_sha256"]:
                raise ValueError("Saved Makeup pixels differ")
        target = output / ref["filename"]
        shutil.copyfile(source, target)
        result.append({**ref, "output": target.name, "retained": True, "new_inference": False})
    return result


def gallery(output, report):
    def tile(label, path):
        if not path.is_file():
            return "<figure><figcaption>" + html.escape(label) + " — pending</figcaption></figure>"
        uri = "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode()
        return '<figure><figcaption>' + html.escape(label) + '</figcaption><button onclick="enlarge(this)"><img alt="' + html.escape(label, quote=True) + '" src="' + uri + '"></button></figure>'
    rows = report["retained"] + report["new_cases"]
    body = []
    for sid in ("054109", "056266"):
        body.append("<h2>" + sid + "</h2><div class=grid>" + tile("Original", output / (sid + "-source.png")))
        for style in ("soft_glam", "exp_cloud_berry_lips", "exp_icy_silver", "exp_manga_lash"):
            row = next((r for r in rows if r["subject_id"] == sid and r["style_id"] == style and r.get("kind") != "continuity"), None)
            body.append(tile(style + (" — saved reference" if style != "exp_manga_lash" else " — new"),
                             output / row["output"] if row else output / "not-generated.png"))
        body.append("</div>")
    page = """<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>Makeup expansion — not deployed</title><style>
body{font:16px system-ui;margin:24px auto;padding:0 16px;max-width:1700px;background:#f6f6fa}
.grid{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:12px}figure{margin:0;min-width:0}figcaption{overflow-wrap:anywhere;min-height:48px}
button{border:0;background:none;padding:0;cursor:zoom-in;width:100%}img{max-width:100%;display:block}dialog{max-width:95vw;max-height:95vh}dialog img{max-height:85vh;object-fit:contain}dialog button{cursor:pointer;width:auto;padding:8px}@media(max-width:700px){.grid{grid-template-columns:1fr}}
</style><h1>Makeup expansion — not deployed</h1><p>Manga Lash is new. Soft Glam, Berry and Icy Silver are verified saved outputs at the same experimental guidance2.5.
This is not a white-cast correction. Review the source complexion, face details, visible makeup and style fidelity.</p>""" + "".join(body) + """
<dialog id=viewer><button onclick="this.parentElement.close()">Close</button><img alt="Original-size result"></dialog>
<script>function enlarge(button){const d=document.getElementById('viewer');d.querySelector('img').src=button.querySelector('img').src;d.showModal();}</script>"""
    (output / "review-self-contained.html").write_bytes(page.encode())


def run(output, plan_path=PLAN):
    import torch
    from PIL import Image, ImageOps
    from diffusers import Flux2KleinPipeline
    from scripts import unified_gate1 as gate
    from scripts.unified_gate2 import inspect_adapter, fingerprint
    from scripts.makeup_quality_diagnostic import layer_scaling, verify_scaling
    from app.makeup_contract import verify_adapter, ADAPTER_SHA256, PRESETS_SHA256
    output, plan_path = Path(output), Path(plan_path)
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    sequence = cases(plan)
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA required; no CPU diffusion")
    if output.exists():
        raise ValueError("Use a fresh output; previous evidence is never overwritten")
    output.mkdir(parents=True)
    report = {"experiment": "MAKEUP-EXP-002", "status": "IN_PROGRESS", "production_enabled": False,
              "training": False, "white_cast_fix_claimed": False, "plan_sha256": sha256(plan_path.read_bytes()).hexdigest(),
              "settings": plan["inference"], "retained": [], "new_cases": [], "new_inference_calls": 0,
              "foundation_load_count": 0, "subjects": plan["subjects"], "limits": plan["limits"]}
    def save():
        (output / "report.json").write_bytes((json.dumps(report, indent=2, allow_nan=False) + "\n").encode())
    save()
    try:
        subjects = {}
        for subject in plan["subjects"]:
            path = ROOT.parent / "fixtures" / subject["filename"]
            if sha256(path.read_bytes()).hexdigest() != subject["sha256"]:
                raise ValueError("Makeup source differs")
            with Image.open(path) as image:
                subjects[subject["id"]] = image.convert("RGB")
            subjects[subject["id"]].save(output / (subject["id"] + "-source.png"))
        report["retained"] = retain(output, plan)
        if plan["adapter_sha256"] != ADAPTER_SHA256 or plan["presets_sha256"] != PRESETS_SHA256:
            raise ValueError("Original Makeup contract differs")
        adapter = ROOT / "gate1/adapters/makeup"
        verify_adapter(adapter)
        model = Path(os.environ["AI_MODEL_DIR"])
        frozen = json.loads((ROOT / "docs/experiments/unified-kaggle-gate1-review.json").read_text(encoding="utf-8"))
        if model.name != gate.REVISION or gate.digest(model / "model_index.json") != frozen["base_model_index_sha256"]:
            raise ValueError("Pinned foundation differs")
        started = time.perf_counter()
        pipe = Flux2KleinPipeline.from_pretrained(str(model), torch_dtype=torch.float16, local_files_only=True)
        pipe.enable_model_cpu_offload(gpu_id=0)
        report.update(foundation_load_count=1, model_load_seconds=time.perf_counter() - started)
        foundation = fingerprint(pipe)
        pipe.load_lora_weights(str(adapter), weight_name="adapter.safetensors")
        state = inspect_adapter(pipe, adapter / "adapter.safetensors", None)
        defaults = layer_scaling(pipe, state["library_adapter_name"])
        pipe.set_adapters(state["library_adapter_name"], adapter_weights=1.0)
        for i, case in enumerate(sequence, 1):
            if fingerprint(pipe) != foundation or inspect_adapter(pipe, adapter / "adapter.safetensors", state["library_adapter_name"]) != state:
                raise RuntimeError("Makeup foundation/adapter state differs")
            scaling = verify_scaling(pipe, state["library_adapter_name"], defaults, 1.0)
            source = ImageOps.pad(subjects[case["subject_id"]], (512, 512),
                                  method=Image.Resampling.LANCZOS, color=(245, 245, 245))
            print("MAKEUP_EXPANSION START", i, "/ 3", case["style_id"], case["subject_id"], flush=True)
            torch.cuda.synchronize(0)
            torch.cuda.reset_peak_memory_stats(0)
            started = time.perf_counter()
            report["new_inference_calls"] += 1
            with torch.no_grad():
                result = pipe(prompt=case["prompt"], image=source, width=512, height=512,
                              num_inference_steps=20, guidance_scale=2.5,
                              generator=torch.Generator(device="cuda").manual_seed(1977)).images[0].convert("RGB")
            torch.cuda.synchronize(0)
            if result.size != (512, 512) or fingerprint(pipe) != foundation or inspect_adapter(pipe, adapter / "adapter.safetensors", state["library_adapter_name"]) != state:
                raise RuntimeError("Makeup output/adapter state differs")
            verify_scaling(pipe, state["library_adapter_name"], defaults, 1.0)
            path = output / f"{i:02}-{case['subject_id']}-{case['style_id']}.png"
            result.save(path)
            row = {**case, "output": path.name, "png_sha256": sha256(path.read_bytes()).hexdigest(),
                   "rgb_sha256": sha256(result.tobytes()).hexdigest(),
                   "prompt_sha256": sha256(case["prompt"].encode()).hexdigest(),
                   "adapter_sha256": ADAPTER_SHA256, "active_tensor_state": state, "scale_verification": scaling,
                   "wall_seconds": time.perf_counter() - started,
                   "peak_allocated_mib": torch.cuda.max_memory_allocated(0) / 1024**2,
                   "retained": False, "visual_verdict": "NEEDS_REVIEW"}
            if case["kind"] == "continuity":
                row["continuity_pixels_match"] = row["rgb_sha256"] == plan["continuity"]["rgb_sha256"]
            report["new_cases"].append(row)
            save()
            if row.get("continuity_pixels_match") is False:
                raise RuntimeError("Soft Glam continuity differs; stop before generating Manga")
            print("MAKEUP_EXPANSION DONE", i, "/ 3", round(row["wall_seconds"], 2), "seconds", flush=True)
        report["status"] = "COMPLETE_REQUIRES_VISUAL_REVIEW"
    except BaseException as exc:
        report.update(status="FAILED", error_type=type(exc).__name__, error=str(exc))
        raise
    finally:
        save()
        gallery(output, report)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--plan", type=Path, default=PLAN)
    args = parser.parse_args()
    run(args.output, args.plan)
