"""MAKEUP-QA-002: nine cached-session calls, no serving/model/preset changes."""
import argparse
import csv
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "backend")]
from scripts.makeup_quality_diagnostic import adapter_condition, layer_scaling, verify_scaling

INSTRUCTION = ("Foundation and concealer must match this person's original visible skin depth and undertone. "
               "Keep the same skin depth, undertone, exposure and natural skin texture as the supplied photo. "
               "Keep the requested lip color, eye definition and cheek color clearly visible.")
CONDITIONS = [
    {"id": "current_reference", "adapter_weight": 1.0, "guidance": 4.0, "prompt_variant": "original"},
    {"id": "lower_guidance", "adapter_weight": 1.0, "guidance": 3.0, "prompt_variant": "original"},
    {"id": "matched_foundation", "adapter_weight": 1.0, "guidance": 4.0, "prompt_variant": "matched_foundation"},
]


def validate_plan(plan):
    if (plan.get("schema") != "beautycore-makeup-adjustment-v1"
            or plan.get("experiment") != "MAKEUP-QA-002"
            or plan.get("production_enabled") is not False or plan.get("automatic_promotion") is not False
            or plan.get("new_training") is not False
            or plan.get("styles") != ["natural_makeup", "classic_red_lip"]
            or [s["id"] for s in plan.get("subjects", [])] != ["054109", "056266"]
            or [s["filename"] for s in plan["subjects"]] != ["054109.jpg", "056266.jpg"]
            or plan.get("conditions") != CONDITIONS or plan.get("foundation_instruction") != INSTRUCTION
            or plan.get("inference") != {"width": 512, "height": 512, "steps": 20, "seed": 1977}
            or (plan.get("retained_cases"), plan.get("new_inference_calls"),
                plan.get("expected_comparison_cases")) != (4, 9, 12)):
        raise ValueError("Adjustment plan differs from the approved bounded comparison")


def prompt_for(style, variant):
    from app.makeup_contract import PROMPTS
    if variant == "original":
        return PROMPTS[style]
    if variant == "matched_foundation":
        return PROMPTS[style] + " " + INSTRUCTION
    raise ValueError("Unknown prompt variant")


def matrix(plan):
    validate_plan(plan)
    return [{**condition, "subject_id": subject["id"], "style_id": style}
            for condition in plan["conditions"] for subject in plan["subjects"] for style in plan["styles"]]


def read_reference(reference, plan):
    from PIL import Image
    from app.makeup_contract import ADAPTER_SHA256, PRESETS_SHA256, INFERENCE
    reference = Path(reference)
    raw = (reference / "report.json").read_bytes()
    if sha256(raw).hexdigest() != plan["reference_report_sha256"]:
        raise ValueError("Reference report differs from the reviewed completed diagnostic")
    old = json.loads(raw)
    if (old.get("status") != "DIAGNOSTIC_COMPLETE_REQUIRES_VISUAL_REVIEW"
            or old.get("experiment") != "MAKEUP-QA-001" or len(old.get("cases", [])) != 12
            or old.get("adapter_sha256") != ADAPTER_SHA256 or old.get("presets_sha256") != PRESETS_SHA256
            or old.get("plan_sha256") != plan["reference_plan_sha256"]
            or old.get("settings") != INFERENCE or old.get("subjects") != plan["subjects"]):
        raise ValueError("Reference contract differs")
    rows = [r for r in old["cases"] if r["id"] == "current_adapter"]
    expected = matrix(plan)[:4]
    if len(rows) != 4:
        raise ValueError("Expected four current-adapter references")
    for row, want in zip(rows, expected):
        if (row["subject_id"] != want["subject_id"] or row["style_id"] != want["style_id"]
                or row["adapter_weight"] != 1.0 or row["prompt"] != prompt_for(want["style_id"], "original")
                or row["prompt_sha256"] != sha256(row["prompt"].encode()).hexdigest()
                or row["active_tensor_state"] != old["initial_adapter_tensor_state"]
                or row["scale_verification"]["relative_factor"] != 1.0):
            raise ValueError("Reference case differs")
        name = row["output"]
        if Path(name).name != name or "\\" in name or ":" in name:
            raise ValueError("Unsafe reference image path")
        image_raw = (reference / name).read_bytes()
        if sha256(image_raw).hexdigest() != row["png_sha256"]:
            raise ValueError("Reference image file hash differs")
        with Image.open(reference / name) as image:
            if (image.format != "PNG" or image.size != (512, 512)
                    or sha256(image.convert("RGB").tobytes()).hexdigest() != row["rgb_sha256"]):
                raise ValueError("Reference image pixels differ")
    return old, rows


def write_reviews(output, subjects, rows, plan):
    from PIL import Image, ImageDraw, ImageOps
    fields = ["subject_id", "style_id", "condition", "output", "complexion_preserved", "texture_preserved",
              "face_geometry_preserved", "makeup_visible_and_plausible", "non_target_changes", "verdict", "notes"]
    with (output / "visual-review.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({**{k: row[k] for k in ("subject_id", "style_id", "output")},
                             "condition": row["id"], "verdict": "NEEDS_REVIEW"})
    for style in plan["styles"]:
        sheet = Image.new("RGB", (1280, 730), "white")
        draw = ImageDraw.Draw(sheet)
        for y, (sid, source) in enumerate(subjects.items()):
            tiles = [("Original " + sid, source)]
            for condition in CONDITIONS:
                row = next((r for r in rows if r["subject_id"] == sid and r["style_id"] == style
                            and r["id"] == condition["id"]), None)
                if row:
                    with Image.open(output / row["output"]) as image:
                        tiles.append((condition["id"], image.convert("RGB")))
                else:
                    tiles.append(("Pending", Image.new("RGB", (512, 512), "#eeeeee")))
            for x, (label, image) in enumerate(tiles):
                draw.text((x * 320 + 6, y * 365 + 8), label, fill="black")
                sheet.paste(ImageOps.contain(image, (320, 320)), (x * 320, y * 365 + 35))
        sheet.save(output / (style + "-comparison.jpg"), quality=94)


def run(output, plan_path, reference):
    import torch
    from PIL import Image, ImageOps
    from diffusers import Flux2KleinPipeline
    from scripts import unified_gate1 as gate
    from scripts.unified_gate2 import fingerprint, inspect_adapter
    from app.makeup_contract import verify_adapter, ADAPTER_SHA256, PRESETS_SHA256
    plan_path, output, reference = map(Path, (plan_path, output, reference))
    plan = json.loads(plan_path.read_text())
    cases = matrix(plan)
    old, retained = read_reference(reference, plan)
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is required; no CPU diffusion")
    if output.exists():
        raise ValueError("Use a new output directory; old results are preserved")
    output.mkdir(parents=True)
    report = {"experiment": "MAKEUP-QA-002", "status": "IN_PROGRESS", "production_enabled": False,
              "new_training": False, "plan_sha256": sha256(plan_path.read_bytes()).hexdigest(),
              "reference_report_sha256": plan["reference_report_sha256"], "subjects": plan["subjects"],
              "base_model_id": gate.MODEL_ID, "base_revision": gate.REVISION,
              "adapter_sha256": ADAPTER_SHA256, "presets_sha256": PRESETS_SHA256,
              "adapter_weight": 1.0, "settings": plan["inference"], "conditions": CONDITIONS,
              "generation_context": "torch.no_grad", "foundation_load_count": 0,
              "gpu": torch.cuda.get_device_name(0), "retained_cases": 4, "new_inference_calls": 0,
              "cases": [], "restorations": [], "limits": plan["limits"]}
    def save():
        (output / "report.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    save()
    try:
        subjects = {}
        for subject in plan["subjects"]:
            path = ROOT.parent / "fixtures" / subject["filename"]
            if sha256(path.read_bytes()).hexdigest() != subject["sha256"]:
                raise ValueError("Source portrait hash differs")
            with Image.open(path) as image:
                if image.size != (512, 512):
                    raise ValueError("Source dimensions differ")
                subjects[subject["id"]] = image.convert("RGB")
            source_name = subject["id"] + "-source.png"
            with Image.open(reference / source_name) as retained_source:
                if retained_source.convert("RGB").tobytes() != subjects[subject["id"]].tobytes():
                    raise ValueError("Retained source pixels differ")
            subjects[subject["id"]].save(output / source_name)
        shutil.copyfile(reference / "report.json", output / "original-reference-report.json")
        for want, row in zip(cases[:4], retained):
            shutil.copyfile(reference / row["output"], output / row["output"])
            report["cases"].append({**row, **want, "retained": True, "original_condition": row["id"]})
        save()
        write_reviews(output, subjects, report["cases"], plan)
        model = Path(os.environ["AI_MODEL_DIR"])
        reviewed = json.loads((ROOT / "docs/experiments/unified-kaggle-gate1-review.json").read_text())
        if model.name != gate.REVISION or gate.digest(model / "model_index.json") != reviewed["base_model_index_sha256"]:
            raise ValueError("Pinned model snapshot/index differs")
        directory = ROOT / "gate1/adapters/makeup"
        verify_adapter(directory)
        path = directory / "adapter.safetensors"
        begin = time.perf_counter()
        pipe = Flux2KleinPipeline.from_pretrained(str(model), torch_dtype=torch.float16, local_files_only=True)
        pipe.enable_model_cpu_offload(gpu_id=0)
        report.update(foundation_load_count=1, startup_seconds=time.perf_counter() - begin)
        foundation = fingerprint(pipe)
        pipe.load_lora_weights(str(directory), weight_name="adapter.safetensors")
        state = inspect_adapter(pipe, path, None)
        if state != old["initial_adapter_tensor_state"]:
            raise ValueError("Reference and new adapter tensors differ")
        defaults = layer_scaling(pipe, state["library_adapter_name"])
        if defaults != old["default_layer_scaling"]:
            raise ValueError("Reference and new layer scaling differ")
        report["initial_adapter_tensor_state"], report["default_layer_scaling"] = state, defaults
        with adapter_condition(pipe, path, inspect_adapter, state, defaults, 1.0, report["restorations"]) as scaling:
            for index, case in enumerate([cases[0]] + cases[4:]):
                continuity = index == 0
                print("MAKEUP_ADJUST START", index + 1, "/ 9", case["subject_id"], case["style_id"],
                      "continuity" if continuity else case["id"], flush=True)
                if fingerprint(pipe) != foundation:
                    raise RuntimeError("Foundation object changed")
                prompt = prompt_for(case["style_id"], case["prompt_variant"])
                source = ImageOps.pad(subjects[case["subject_id"]], (512, 512),
                                      method=Image.Resampling.LANCZOS, color=(245, 245, 245))
                torch.cuda.synchronize(0)
                torch.cuda.reset_peak_memory_stats(0)
                begin = time.perf_counter()
                report["new_inference_calls"] += 1
                with torch.no_grad():
                    result = pipe(prompt=prompt, image=source, width=512, height=512,
                                  num_inference_steps=20, guidance_scale=case["guidance"],
                                  generator=torch.Generator(device="cuda").manual_seed(1977)).images[0].convert("RGB")
                torch.cuda.synchronize(0)
                elapsed = time.perf_counter() - begin
                if result.size != (512, 512) or inspect_adapter(pipe, path, state["library_adapter_name"]) != state:
                    raise RuntimeError("Output dimensions or adapter tensors changed")
                verify_scaling(pipe, state["library_adapter_name"], defaults, 1.0)
                name = f"{case['subject_id']}-{case['style_id']}-{case['id']}.png"
                if continuity:
                    name = "continuity-" + name
                result.save(output / name)
                row = {**case, "output": name, "prompt": prompt,
                       "prompt_sha256": sha256(prompt.encode()).hexdigest(), "adapter_id": "MAKEUP-001",
                       "active_tensor_state": state, "scale_verification": scaling,
                       "png_sha256": sha256((output / name).read_bytes()).hexdigest(),
                       "rgb_sha256": sha256(result.tobytes()).hexdigest(),
                       "wall_seconds": elapsed, "peak_gpu_allocated_mib": torch.cuda.max_memory_allocated(0) / 1024**2,
                       "retained": False, "visual_verdict": "NEEDS_REVIEW"}
                if continuity:
                    report["continuity_check"] = {**row, "expected_rgb_sha256": retained[0]["rgb_sha256"],
                                                  "pixels_match": row["rgb_sha256"] == retained[0]["rgb_sha256"]}
                    save()
                    if not report["continuity_check"]["pixels_match"]:
                        raise RuntimeError("Continuity pixels differ; stop before candidate calls")
                    print("MAKEUP_ADJUST CONTINUITY PASSED", flush=True)
                else:
                    report["cases"].append(row)
                    save()
                    write_reviews(output, subjects, report["cases"], plan)
                print("MAKEUP_ADJUST DONE", index + 1, "/ 9", round(elapsed, 2), "seconds", flush=True)
        if len(report["cases"]) != 12 or report["new_inference_calls"] != 9 or fingerprint(pipe) != foundation:
            raise RuntimeError("Adjustment matrix incomplete or foundation changed")
        report["status"] = "DIAGNOSTIC_COMPLETE_REQUIRES_VISUAL_REVIEW"
    except BaseException as exc:
        report.update(status="FAILED", error_type=type(exc).__name__, error=str(exc))
        raise
    finally:
        save()


def bootstrap(args):
    from scripts import unified_gate3_bootstrap as original
    from scripts.style_expansion_bootstrap import check_ports, clean_environment
    check_ports()
    work = ROOT.parent.resolve()
    if (args.output.resolve().parent != work or args.output.exists()
            or args.plan.resolve().parent != (ROOT / "data/makeup/MAKEUP-QA-002").resolve()
            or args.reference.resolve().parent != work):
        raise ValueError("Expected owned cached-session paths")
    args.evidence.resolve().relative_to(work / "setup-evidence")
    args.evidence.mkdir(exist_ok=False)
    _, review = original.verify_bundle()
    env = clean_environment(os.environ)
    original.run([sys.executable, str(ROOT / "scripts/unified_gate2.py"), "--environment-only"],
                 args.evidence, "environment.log", env)
    current = json.loads((args.evidence / "environment.log").read_text().strip().splitlines()[-1])
    if any(current.get(k) != review["environment"].get(k)
           for k in ("python", "packages", "diffusers_commit", "torch", "cuda", "gpu")):
        raise RuntimeError("Installed environment changed; no reinstall or generation attempted")
    original.run([sys.executable, str(ROOT / "scripts/unified_gate2.py"), "--verify-only"],
                 args.evidence, "artifact_preflight.log", env)
    model = json.loads((work / "setup-evidence/model.json").read_text())
    snapshot = Path(model["snapshot"])
    if snapshot.name != original.gate.REVISION or original.gate.digest(snapshot / "model_index.json") != review["base_model_index_sha256"]:
        raise RuntimeError("Cached snapshot/index differs; no new download attempted")
    env["AI_MODEL_DIR"] = str(snapshot)
    (args.evidence / "cache-reuse.json").write_text(json.dumps({
        "snapshot": str(snapshot), "downloaded_again": False, "reinstalled_packages": False}, indent=2) + "\n")
    with (args.evidence / "adjustment.log").open("w", encoding="utf-8") as log:
        process = subprocess.Popen([sys.executable, str(Path(__file__).resolve()),
                                    "--output", str(args.output), "--plan", str(args.plan),
                                    "--reference", str(args.reference)], cwd=ROOT, env=env,
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in process.stdout:
            log.write(line)
            log.flush()
            if line.startswith("MAKEUP_ADJUST"):
                print(line.rstrip(), flush=True)
        if process.wait():
            raise RuntimeError("Adjustment failed; return partial result ZIP and adjustment.log")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--evidence", type=Path)
    parser.add_argument("--bootstrap", action="store_true")
    args = parser.parse_args()
    if args.bootstrap:
        if args.evidence is None:
            parser.error("--bootstrap requires --evidence")
        lock = ROOT.parent / ".makeup-adjustment.lock"
        with lock.open("x") as stream:
            stream.write(str(os.getpid()))
        try:
            bootstrap(args)
        finally:
            lock.unlink()
    else:
        run(args.output, args.plan, args.reference)

