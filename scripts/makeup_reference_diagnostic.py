"""Two fixed MAKEUP-001 generations with separate identity and cosmetic guides.

Raw model output only. No recoloring, source compositor, training or deployment.
"""
import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))
PLAN = ROOT / "data/makeup/MAKEUP-GUIDED-001/plan.json"
FIXED = [("054109", "soft_glam", "006553"), ("056266", "bold_evening_glam", "035149")]
INFERENCE = {"width": 512, "height": 512, "steps": 20, "guidance": 4.0, "seed": 1977}


def validate_plan(plan):
    if (plan.get("schema") != "makeup-reference-diagnostic-v1" or plan.get("production_enabled") is not False
            or plan.get("training") is not False or plan.get("inference") != INFERENCE
            or [(r["source_id"], r["style_id"], r["guide_identity_id"]) for r in plan.get("cases", [])] != FIXED):
        raise ValueError("Expected the two bounded separate-identity reference cases")
    for row in plan["cases"]:
        if row.get("source_split") != "validation" or row.get("guide_source_split") != "train":
            raise ValueError("Cosmetic guides must come from training identities")
        if row.get("guide_kind") != "external-editor-synthetic-source-protected":
            raise ValueError("Guide provenance is missing")
        for key in ("source_filename", "guide_filename", "previous_filename"):
            if Path(row[key]).name != row[key] or "/" in row[key] or "\\" in row[key]:
                raise ValueError("Fixture name must be a single filename")


def effective_prompt(style_id):
    from app.makeup_contract import PROMPTS
    return ("Edit image 1 only. Image 1 is the sole identity, original skin complexion and undertone, face geometry, "
            "expression, teeth, hair, lighting and background reference. Image 2 is a cosmetic style guide of a DIFFERENT "
            "person. Transfer only its coordinated eye makeup, blush, lip colour and complete foundation finish, "
            "with foundation and concealer shade matched to image 1. Do not transfer image 2's skin colour, face, "
            "features or lighting. Produce a visibly complete naturally blended makeup look with original pores "
            "and photographic texture. " + PROMPTS[style_id])


def load_fixtures(plan, fixtures):
    from PIL import Image
    loaded = []
    for row in plan["cases"]:
        pictures = {}
        for kind in ("source", "guide", "previous"):
            path = fixtures / row[kind + "_filename"]
            if sha256(path.read_bytes()).hexdigest() != row[kind + "_sha256"]:
                raise ValueError("Changed diagnostic fixture: " + kind)
            with Image.open(path) as image:
                if image.size != (512, 512):
                    raise ValueError("Expected the normalized 512 square input")
                pictures[kind] = image.convert("RGB")
        loaded.append((row, pictures))
    return loaded


def run(output, plan_path=PLAN):
    from PIL import Image, ImageDraw
    from scripts import unified_gate1 as gate
    from scripts.unified_gate2 import inspect_adapter, fingerprint, verify_environment
    from app.makeup_contract import verify_adapter, ADAPTER_SHA256, MODEL_REVISION, PRESETS_SHA256
    from scripts.makeup_quality_diagnostic import layer_scaling, verify_scaling
    import torch
    from diffusers import Flux2KleinPipeline

    plan = json.loads(Path(plan_path).read_text())
    validate_plan(plan)
    fixtures = load_fixtures(plan, ROOT.parent / "fixtures")
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    report = {"schema": plan["schema"], "status": "IN_PROGRESS", "production_enabled": False,
              "training": False, "plan_sha256": sha256(Path(plan_path).read_bytes()).hexdigest(),
              "adapter_id": "MAKEUP-001", "adapter_sha256": ADAPTER_SHA256,
              "prompt_presets_sha256": PRESETS_SHA256, "cases": [], "expected_calls": 2,
              "postprocessing": None, "foundation_load_count": 0,
              "limits": ["Two reused development portraits, not an untouched final evaluation.",
                         "Previous comparison is explicitly a rejected CPU compositor, not the same model's baseline.",
                         "Synthetic guides are not accepted training pairs; no catalog wide quality claim."]}

    def save():
        (output / "report.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")

    save()
    try:
        review = json.loads((ROOT / "docs/experiments/unified-kaggle-gate2-review.json").read_text())
        report["environment"] = verify_environment(gate.environment(), review["environment"])
        model = Path(os.environ["AI_MODEL_DIR"])
        if model.name != MODEL_REVISION or gate.digest(model / "model_index.json") != review["base_model_index_sha256"]:
            raise ValueError("Pinned Base snapshot differs")
        directory = ROOT / "gate1/adapters/makeup"
        verify_adapter(directory)
        started = time.monotonic()
        pipe = Flux2KleinPipeline.from_pretrained(str(model), torch_dtype=torch.float16, local_files_only=True)
        pipe.enable_model_cpu_offload(gpu_id=0)
        report["foundation_load_count"] = 1
        pipe.load_lora_weights(str(directory), weight_name="adapter.safetensors")
        state = inspect_adapter(pipe, directory / "adapter.safetensors")
        scaling = layer_scaling(pipe, state["library_adapter_name"])
        foundation = fingerprint(pipe)
        report.update(startup_seconds=time.monotonic() - started, active_tensor_state=state)
        save()
        for number, (row, pictures) in enumerate(fixtures, 1):
            label = row["source_id"] + "-" + row["style_id"]
            if inspect_adapter(pipe, directory / "adapter.safetensors") != state or fingerprint(pipe) != foundation:
                raise RuntimeError("Adapter tensors or shared foundation changed")
            verified_scaling = verify_scaling(pipe, state["library_adapter_name"], scaling, 1.0)
            prompt = effective_prompt(row["style_id"])
            print("MAKEUP_REFERENCE START", number, "of 2", label, flush=True)
            torch.cuda.reset_peak_memory_stats(0)
            started = time.monotonic()
            with torch.no_grad():
                result = pipe(image=[pictures["source"], pictures["guide"]], prompt=prompt, width=512, height=512,
                              num_inference_steps=20, guidance_scale=4.0,
                              generator=torch.Generator(device="cuda").manual_seed(1977)).images[0].convert("RGB")
            torch.cuda.synchronize(0)
            if result.size != (512, 512):
                raise RuntimeError("Unexpected output dimensions")
            seconds = time.monotonic() - started
            result_path = output / (label + "-raw.png")
            result.save(result_path)
            board = Image.new("RGB", (2048, 544), "white")
            draw = ImageDraw.Draw(board)
            for i, (title, image) in enumerate(zip(("Original", "Different-person cosmetic guide",
                    "Previous REJECTED CPU result", "Actual MAKEUP-001 raw, needs review"),
                    (pictures["source"], pictures["guide"], pictures["previous"], result))):
                draw.text((i * 512 + 5, 8), title, fill="black")
                board.paste(image, (i * 512, 32))
            board.save(output / (label + "-comparison.png"))
            record = {**row, "output": result_path.name, "png_sha256": gate.digest(result_path),
                "rgb_sha256": sha256(result.tobytes()).hexdigest(), "prompt": prompt, "inference": INFERENCE,
                "runtime_seconds": seconds, "peak_gpu_mib": torch.cuda.max_memory_allocated(0) / 1024**2,
                "input_order": ["original_identity_complexion", "different_person_cosmetics_only"],
                "adapter_scaling": verified_scaling, "visual_review": "NEEDS VERIFICATION"}
            report["cases"].append(record)
            save()
            print("MAKEUP_REFERENCE SAVED", label, round(seconds, 2), "seconds", flush=True)
        if inspect_adapter(pipe, directory / "adapter.safetensors") != state or fingerprint(pipe) != foundation:
            raise RuntimeError("Final model preservation check failed")
        report["status"] = "GENERATED_REQUIRES_VISUAL_REVIEW"
        save()
    except Exception as error:
        report.update(status="FAILED", error_type=type(error).__name__, error=str(error))
        save()
        raise


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--output", required=True, type=Path)
    args = cli.parse_args()
    run(args.output)
