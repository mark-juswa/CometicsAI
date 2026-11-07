"""MAKEUP-QA-001: twelve matched offline observations; no production endpoints."""
import argparse
from contextlib import contextmanager
import csv
from hashlib import sha256
import json
import math
import os
import shutil
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))
PLAN = ROOT / "data/makeup/MAKEUP-QA-001/plan.json"


def validate_plan(plan):
    if (plan.get("schema") != "beautycore-makeup-quality-v1" or plan.get("production_enabled") is not False
            or plan.get("styles") != ["natural_makeup", "classic_red_lip"]
            or [s["id"] for s in plan.get("subjects", [])] != ["054109", "056266"]
            or plan.get("conditions") != [
                {"id": "foundation_only", "adapter_weight": 0.0},
                {"id": "current_adapter", "adapter_weight": 1.0},
                {"id": "reduced_adapter", "adapter_weight": 0.5}]
            or plan.get("inference") != {"width": 512, "height": 512, "steps": 20, "guidance": 4.0, "seed": 1977}):
        raise ValueError("Diagnostic plan differs from the approved bounded comparison")


def planned_cases(plan):
    validate_plan(plan)
    return [{**condition, "subject_id": subject["id"], "style_id": style}
            for condition in plan["conditions"] for subject in plan["subjects"] for style in plan["styles"]]


def assert_plain_foundation(pipe):
    if any(pipe.get_list_adapters().values()) or pipe.get_active_adapters():
        raise RuntimeError("Foundation control has an active adapter")
    if any(".lora_A." in name or ".lora_B." in name for name, _ in pipe.transformer.named_parameters()):
        raise RuntimeError("Foundation control still contains LoRA tensors")


def layer_scaling(pipe, adapter_name):
    result = {}
    for name, module in pipe.transformer.named_modules():
        if hasattr(module, "lora_A"):
            if (set(module.lora_A) != {adapter_name} or set(module.lora_B) != {adapter_name}
                    or list(module.active_adapters) != [adapter_name] or module.disable_adapters or module.merged):
                raise RuntimeError("Uncertain adapter state during scale verification")
            value = float(module.scaling[adapter_name])
            if not math.isfinite(value) or value <= 0:
                raise RuntimeError("Invalid LoRA layer scaling")
            result[name] = value
    if not result:
        raise RuntimeError("No LoRA layers available to scale")
    return result


def verify_scaling(pipe, adapter_name, defaults, factor):
    actual = layer_scaling(pipe, adapter_name)
    if actual.keys() != defaults.keys() or any(
            not math.isclose(actual[name], defaults[name] * factor, rel_tol=1e-6, abs_tol=1e-9)
            for name in defaults):
        raise RuntimeError("Actual per-layer adapter influence does not match requested setting")
    return {"layer_count": len(actual), "relative_factor": factor,
            "actual_scaling_sha256": sha256(json.dumps(actual, sort_keys=True).encode()).hexdigest()}


@contextmanager
def adapter_condition(pipe, path, inspect, initial_state, defaults, factor, restorations):
    """Verify original tensors and effective scaling; always restore full influence."""
    if factor not in (1.0, 0.5):
        raise ValueError("Only the two approved adapter conditions are allowed")
    name = initial_state["library_adapter_name"]
    try:
        pipe.set_adapters(name, adapter_weights=factor)
        state = inspect(pipe, path, name)
        if state != initial_state:
            raise RuntimeError("Adapter tensors changed during scaling")
        yield verify_scaling(pipe, name, defaults, factor)
    finally:
        pipe.set_adapters(name, adapter_weights=1.0)
        state = inspect(pipe, path, name)
        scaling = verify_scaling(pipe, name, defaults, 1.0)
        if state != initial_state:
            raise RuntimeError("Original adapter tensor state was not restored")
        restorations.append({"after_factor": factor, "tensor_state_restored": True,
                             "scaling_restored": True, **scaling})


def sheets(output, subjects, rows, styles):
    from PIL import Image, ImageDraw, ImageOps
    for style in styles:
        sheet = Image.new("RGB", (4 * 320, len(subjects) * 365), "white")
        draw = ImageDraw.Draw(sheet)
        for y, (subject_id, source) in enumerate(subjects.items()):
            tiles = [("Original " + subject_id, source)]
            for condition in ("foundation_only", "current_adapter", "reduced_adapter"):
                match = next((r for r in rows if r["subject_id"] == subject_id
                              and r["style_id"] == style and r["id"] == condition), None)
                if match:
                    with Image.open(output / match["output"]) as opened:
                        tiles.append((condition + " / " + str(match["adapter_weight"]), opened.convert("RGB")))
                else:
                    tiles.append(("Pending", Image.new("RGB", (512, 512), "#eeeeee")))
            for x, (label, image) in enumerate(tiles):
                draw.text((x * 320 + 6, y * 365 + 8), label, fill="black")
                sheet.paste(ImageOps.contain(image, (320, 320)), (x * 320, y * 365 + 35))
        sheet.save(output / (style + "-comparison.jpg"), quality=94)


def save_review_csv(output, rows):
    with (output / "visual-review.csv").open("w", encoding="utf-8", newline="") as stream:
        fields = ["subject_id", "style_id", "condition", "adapter_weight", "output",
                  "complexion_preserved", "texture_preserved", "face_geometry_preserved",
                  "makeup_visible_and_plausible", "non_target_changes", "reviewer", "verdict", "notes"]
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({"subject_id": row["subject_id"], "style_id": row["style_id"],
                             "condition": row["id"], "adapter_weight": row["adapter_weight"],
                             "output": row["output"], "verdict": "NEEDS_REVIEW"})



INFERENCE_TENSOR_FAILURE = "Setting requires_grad=True on inference tensor outside InferenceMode is not allowed."


def read_completed_prefix(previous, plan):
    """Accept only this eight-image failure; verify every retained PNG and prompt."""
    from PIL import Image
    from app.makeup_contract import PROMPTS, ADAPTER_SHA256, PRESETS_SHA256
    previous = Path(previous)
    log = previous.parent / "setup-evidence/diagnostic.log"
    if not log.is_file() or INFERENCE_TENSOR_FAILURE not in log.read_text(encoding="utf-8"):
        raise ValueError("Continuation requires the confirmed inference-tensor restoration failure")
    old = json.loads((previous / "report.json").read_text(encoding="utf-8"))
    if (old.get("status") != "FAILED" or old.get("error_type") != "RuntimeError"
            or old.get("experiment") != "MAKEUP-QA-001" or old.get("settings") != plan["inference"]
            or old.get("adapter_sha256") != ADAPTER_SHA256 or old.get("presets_sha256") != PRESETS_SHA256
            or len(old.get("cases", [])) != 8):
        raise ValueError("Partial report is not the expected eight-image diagnostic")
    expected = planned_cases(plan)[:8]
    for want, row in zip(expected, old["cases"]):
        if any(row.get(key) != value for key, value in want.items()):
            raise ValueError("Retained case order/conditions differ")
        if row["prompt"] != PROMPTS[row["style_id"]] or row["prompt_sha256"] != sha256(row["prompt"].encode()).hexdigest():
            raise ValueError("Retained prompt differs")
        filename = row["output"]
        if Path(filename).name != filename or "\\" in filename or ":" in filename:
            raise ValueError("Unsafe retained result path")
        path = previous / filename
        if sha256(path.read_bytes()).hexdigest() != row["png_sha256"]:
            raise ValueError("Retained output file hash differs")
        with Image.open(path) as opened:
            if opened.format != "PNG" or opened.size != (512, 512):
                raise ValueError("Invalid retained output image")
            if sha256(opened.convert("RGB").tobytes()).hexdigest() != row["rgb_sha256"]:
                raise ValueError("Retained output pixels differ")
    return old


def run(output, plan_path=PLAN, resume_from=None):
    import torch
    from PIL import Image, ImageOps
    from diffusers import Flux2KleinPipeline
    from scripts import unified_gate1 as gate
    from scripts.unified_gate2 import fingerprint, inspect_adapter
    from app.makeup_contract import PROMPTS, PRESETS_SHA256, verify_adapter, ADAPTER_SHA256
    plan = json.loads(Path(plan_path).read_text(encoding="utf-8"))
    sequence = planned_cases(plan)
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is required; do not run diffusion on CPU")
    if output.exists():
        raise ValueError("Use a new output directory; previous results are preserved")
    prior = read_completed_prefix(resume_from, plan) if resume_from is not None else None
    output.mkdir(parents=True)
    report = {"status": "IN_PROGRESS", "experiment": "MAKEUP-QA-001", "production_enabled": False,
              "new_training": False, "foundation_load_count": 0,
              "settings": plan["inference"], "base_model_id": gate.MODEL_ID, "base_revision": gate.REVISION,
              "presets_sha256": PRESETS_SHA256, "adapter_sha256": ADAPTER_SHA256,
              "plan_sha256": sha256(Path(plan_path).read_bytes()).hexdigest(),
              "gpu": torch.cuda.get_device_name(0), "cases": [], "restorations": [],
              "new_inference_calls": 0, "generation_context": "torch.no_grad",
              "limits": ["Two reused evaluation people now serve as diagnostic development cases, not an untouched final test.",
                         "0.5 is a diagnostic setting, not an established fix or 50-percent makeup opacity.",
                         "No masks, compositing, image-wide recoloring, architecture changes or production rollout.",
                         "No standardized skin-color or identity score computed. Visual review is required.",
                         "Single observation per case; timings are not a speed benchmark."]}
    def save():
        (output / "report.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    save()
    try:
        subjects = {}
        for subject in plan["subjects"]:
            path = ROOT.parent / "fixtures" / subject["filename"]
            if sha256(path.read_bytes()).hexdigest() != subject["sha256"]:
                raise ValueError("Source portrait differs from reviewed manifest")
            with Image.open(path) as opened:
                if opened.size != (512, 512):
                    raise ValueError("Expected the original 512x512 portrait")
                subjects[subject["id"]] = opened.convert("RGB")
            subjects[subject["id"]].save(output / (subject["id"] + "-source.png"))
        report["subjects"] = plan["subjects"]
        if prior is not None:
            if prior["plan_sha256"] != report["plan_sha256"] or prior["subjects"] != plan["subjects"]:
                raise ValueError("Continuation input plan differs from original")
            for subject in plan["subjects"]:
                filename = subject["id"] + "-source.png"
                with Image.open(Path(resume_from) / filename) as original_source:
                    if original_source.convert("RGB").tobytes() != subjects[subject["id"]].tobytes():
                        raise ValueError("Retained source portrait differs")
            for row in prior["cases"]:
                shutil.copyfile(Path(resume_from) / row["output"], output / row["output"])
            report["cases"] = prior["cases"]
            shutil.copyfile(Path(resume_from) / "report.json", output / "original-partial-report.json")
            report["continuation"] = {
                "retained_cases": 8, "original_report_sha256": sha256((Path(resume_from) / "report.json").read_bytes()).hexdigest(),
                "old_generation_context": "torch.inference_mode", "new_generation_context": "torch.no_grad",
                "expected_new_calls": 5, "note": "One continuity control plus four missing outputs; original files untouched."}
            save()
        model = Path(os.environ["AI_MODEL_DIR"])
        review = json.loads((ROOT / "docs/experiments/unified-kaggle-gate1-review.json").read_text())
        if model.name != gate.REVISION or gate.digest(model / "model_index.json") != review["base_model_index_sha256"]:
            raise RuntimeError("Pinned model snapshot/index differs")
        directory = ROOT / "gate1/adapters/makeup"
        verify_adapter(directory)
        path = directory / "adapter.safetensors"
        begin = time.perf_counter()
        pipe = Flux2KleinPipeline.from_pretrained(str(model), torch_dtype=torch.float16, local_files_only=True)
        pipe.enable_model_cpu_offload(gpu_id=0)
        report.update(foundation_load_count=1, startup_seconds=time.perf_counter() - begin)
        foundation = fingerprint(pipe)
        state, defaults = None, None
        def generate(case, verification, continuity=False):
            if fingerprint(pipe) != foundation:
                raise RuntimeError("Foundation object changed")
            source = ImageOps.pad(subjects[case["subject_id"]], (512, 512),
                                  method=Image.Resampling.LANCZOS, color=(245, 245, 245))
            torch.cuda.synchronize(0)
            torch.cuda.reset_peak_memory_stats(0)
            begin = time.perf_counter()
            report["new_inference_calls"] += 1
            with torch.no_grad():
                result = pipe(prompt=PROMPTS[case["style_id"]], image=source, width=512, height=512,
                              num_inference_steps=20, guidance_scale=4.0,
                              generator=torch.Generator(device="cuda").manual_seed(1977)).images[0].convert("RGB")
            torch.cuda.synchronize(0)
            elapsed = time.perf_counter() - begin
            if result.size != (512, 512):
                raise RuntimeError("Unexpected diagnostic output dimensions")
            if case["adapter_weight"] == 0:
                assert_plain_foundation(pipe)
            else:
                if inspect_adapter(pipe, path, state["library_adapter_name"]) != state:
                    raise RuntimeError("Adapter tensors changed after generation")
                verify_scaling(pipe, state["library_adapter_name"], defaults, case["adapter_weight"])
            name = f"{case['subject_id']}-{case['style_id']}-{case['id']}.png"
            if continuity:
                name = "continuity-" + name
            result.save(output / name)
            row = {**case, "output": name, "prompt": PROMPTS[case["style_id"]],
                   "prompt_sha256": sha256(PROMPTS[case["style_id"]].encode()).hexdigest(),
                   "adapter_id": None if case["adapter_weight"] == 0 else "MAKEUP-001",
                   "active_tensor_state": None if case["adapter_weight"] == 0 else state,
                   "scale_verification": verification,
                   "png_sha256": sha256((output / name).read_bytes()).hexdigest(),
                   "rgb_sha256": sha256(result.tobytes()).hexdigest(),
                   "wall_seconds": elapsed, "peak_gpu_allocated_mib": torch.cuda.max_memory_allocated(0) / 1024 ** 2,
                   "visual_verdict": "NEEDS_REVIEW"}
            if continuity:
                original = next(r for r in report["cases"] if r["id"] == case["id"]
                                and r["subject_id"] == case["subject_id"] and r["style_id"] == case["style_id"])
                report["continuity_check"] = {**row, "expected_rgb_sha256": original["rgb_sha256"],
                                              "pixels_match": row["rgb_sha256"] == original["rgb_sha256"]}
                save()
                if not report["continuity_check"]["pixels_match"]:
                    raise RuntimeError("Continuity control pixels differ; do not mix unmatched comparison conditions")
                print("MAKEUP_QA CONTINUITY PASSED: saved current-adapter pixels reproduced.", flush=True)
                return
            report["cases"].append(row)
            save()
            save_review_csv(output, report["cases"])
            sheets(output, subjects, report["cases"], plan["styles"])
            print("MAKEUP_QA DONE", len(report["cases"]), "/ 12", round(elapsed, 2), "seconds", flush=True)
        for condition in plan["conditions"]:
            group = [c for c in sequence if c["id"] == condition["id"]]
            if condition["adapter_weight"] == 0:
                if prior is not None:
                    continue
                assert_plain_foundation(pipe)
                for case in group:
                    print("MAKEUP_QA START", len(report["cases"]) + 1, "/ 12",
                          case["subject_id"], case["style_id"], case["id"], flush=True)
                    generate(case, {"no_adapter_loaded": True})
            else:
                if state is None:
                    pipe.load_lora_weights(str(directory), weight_name="adapter.safetensors")
                    state = inspect_adapter(pipe, path, None)
                    defaults = layer_scaling(pipe, state["library_adapter_name"])
                    report["default_layer_scaling"] = defaults
                    report["initial_adapter_tensor_state"] = state
                with adapter_condition(pipe, path, inspect_adapter, state, defaults,
                                       condition["adapter_weight"], report["restorations"]) as verification:
                    if prior is not None and condition["adapter_weight"] == 1.0:
                        print("MAKEUP_QA CONTINUITY: one current-adapter control before four missing images.", flush=True)
                        generate(group[0], verification, continuity=True)
                    for case in group:
                        if any(all(row[key] == case[key] for key in ("id", "subject_id", "style_id")) for row in report["cases"]):
                            continue
                        print("MAKEUP_QA START", len(report["cases"]) + 1, "/ 12",
                              case["subject_id"], case["style_id"], case["id"], flush=True)
                        generate(case, verification)
        if fingerprint(pipe) != foundation or len(report["cases"]) != 12:
            raise RuntimeError("Diagnostic sequence incomplete or foundation changed")
        report["status"] = "DIAGNOSTIC_COMPLETE_REQUIRES_VISUAL_REVIEW"
    except BaseException as exc:
        report["status"], report["error_type"] = "FAILED", type(exc).__name__
        raise
    finally:
        save()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--resume-from", type=Path)
    args = parser.parse_args()
    run(args.output.resolve(), resume_from=args.resume_from)
