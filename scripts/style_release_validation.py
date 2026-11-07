"""Fresh private STYLE-VAL-001 validation, no production routes or preset mutations."""
import argparse
import csv
from hashlib import sha256
import json
import os
from pathlib import Path
import sys
import time
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "backend")]
from scripts.makeup_quality_diagnostic import assert_plain_foundation, layer_scaling, verify_scaling


def cases(plan):
    from app.makeup_contract import PROMPTS
    expected = ("exp_comma_hair", "exp_cloud_berry_lips", "exp_icy_silver")
    if (plan.get("schema") != "beautycore-style-release-validation-v1"
            or plan.get("experiment") != "STYLE-VAL-001" or plan.get("production_enabled") is not False
            or plan.get("automatic_promotion") is not False or plan.get("training") is not False
            or plan.get("makeup_styles") != list(PROMPTS)
            or plan.get("makeup_guidance") != 2.5 or plan.get("hair_guidance") != 4.0
            or plan.get("adapter_weight") != 1.0
            or plan.get("inference") != {"width": 512, "height": 512, "steps": 20, "seed": 1977}
            or plan.get("expected_calls") != 29 or set(plan.get("candidate_prompts", {})) != set(expected)
            or [s["id"] for s in plan.get("makeup_subjects", [])] != ["054109", "056266"]
            or [s["id"] for s in plan.get("hair_subjects", [])] != ["d2_curtain_hair_4jpg", "d2_side_part_undercut_28jpg"]):
        raise ValueError("Unexpected validation scope")
    rows = []
    for style in plan["makeup_styles"]:
        for subject in plan["makeup_subjects"]:
            rows.append({"feature": "makeup", "adapter": "makeup", "subject_id": subject["id"],
                         "style_id": style, "guidance": 2.5, "kind": "existing",
                         "prompt": PROMPTS[style]})
    for style in expected[1:]:
        for subject in plan["makeup_subjects"]:
            rows.append({"feature": "makeup", "adapter": "makeup", "subject_id": subject["id"],
                         "style_id": style, "guidance": 2.5, "kind": "candidate",
                         "prompt": plan["candidate_prompts"][style]})
    for subject in plan["hair_subjects"]:
        for style, prompt in (("curtain_hair", plan["hair_baseline_prompt"]),
                              ("exp_comma_hair", plan["candidate_prompts"]["exp_comma_hair"])):
            rows.append({"feature": "hairstyle", "adapter": "train002", "subject_id": subject["id"],
                         "style_id": style, "guidance": 4.0,
                         "kind": "candidate" if style.startswith("exp_") else "existing", "prompt": prompt})
    rows.append({**rows[0], "kind": "restoration"})
    return rows


def sheets(output, subjects, rows):
    from PIL import Image, ImageDraw, ImageOps
    groups = {}
    for row in rows:
        groups.setdefault((row["feature"], row["subject_id"]), []).append(row)
    for (feature, sid), items in groups.items():
        tiles = [("Original " + sid, subjects[sid])]
        for row in items:
            with Image.open(output / row["output"]) as image:
                tiles.append((row["kind"] + " / " + row["style_id"], image.convert("RGB")))
        sheet = Image.new("RGB", (3 * 384, ((len(tiles) + 2) // 3) * 320), "white")
        draw = ImageDraw.Draw(sheet)
        for index, (label, image) in enumerate(tiles):
            x, y = index % 3 * 384, index // 3 * 320
            for line, offset in enumerate(range(0, len(label), 48)):
                draw.text((x + 5, y + 5 + line * 13), label[offset:offset + 48], fill="black")
            sheet.paste(ImageOps.contain(image, (384, 270)), (x, y + 45))
        sheet.save(output / (feature + "-" + sid + "-comparison.jpg"), quality=94)
    with (output / "visual-review.csv").open("w", encoding="utf-8", newline="") as stream:
        fields = ["feature", "subject_id", "style_id", "kind", "output", "style_fidelity",
                  "complexion_texture_geometry_preserved", "non_target_changes", "reviewer", "verdict", "notes"]
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({**{k: row[k] for k in fields[:5]}, "verdict": "NEEDS_REVIEW"})


def run(output, plan_path):
    import torch
    from PIL import Image, ImageOps
    from diffusers import Flux2KleinPipeline
    from scripts import unified_gate1 as gate
    from scripts.unified_gate2 import fingerprint, inspect_adapter
    from app.makeup_contract import verify_adapter, ADAPTER_SHA256, PRESETS_SHA256
    output, plan_path = Path(output), Path(plan_path)
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    sequence = cases(plan)
    if len(sequence) != 29 or not torch.cuda.is_available():
        raise RuntimeError("Expected29calls and CUDA; no CPU diffusion")
    if output.exists():
        raise ValueError("Use a new output directory")
    output.mkdir(parents=True)
    report = {"experiment": "STYLE-VAL-001", "status": "IN_PROGRESS", "production_enabled": False,
              "training": False, "plan_sha256": sha256(plan_path.read_bytes()).hexdigest(),
              "settings": plan["inference"], "presets_sha256": PRESETS_SHA256, "cases": [],
              "new_inference_calls": 0, "foundation_load_count": 0, "switches": [],
              "gpu": torch.cuda.get_device_name(0), "limits": plan["limits"]}
    def save():
        (output / "report.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    save()
    try:
        subjects = {}
        for subject in plan["makeup_subjects"] + plan["hair_subjects"]:
            path = ROOT.parent / "fixtures" / subject["filename"]
            if sha256(path.read_bytes()).hexdigest() != subject["sha256"]:
                raise ValueError("Source portrait differs: " + subject["id"])
            with Image.open(path) as image:
                subjects[subject["id"]] = image.convert("RGB")
            subjects[subject["id"]].save(output / (subject["id"] + "-source.png"))
        report["subjects"] = plan["makeup_subjects"] + plan["hair_subjects"]
        model = Path(os.environ["AI_MODEL_DIR"])
        review = json.loads((ROOT / "docs/experiments/unified-kaggle-gate1-review.json").read_text())
        if model.name != gate.REVISION or gate.digest(model / "model_index.json") != review["base_model_index_sha256"]:
            raise RuntimeError("Pinned model differs")
        makeup = ROOT / "gate1/adapters/makeup"
        hair = ROOT / "gate1/adapters/hairstyle_train002"
        verify_adapter(makeup)
        for key, directory in (("makeup", makeup), ("train002", hair)):
            if gate.digest(directory / "adapter.safetensors") != plan["adapter_hashes"][key]:
                raise ValueError("Checkpoint differs: " + key)
        meta = json.loads((hair / "metadata.json").read_text())
        if (meta.get("checkpoint_sha256") != plan["adapter_hashes"]["train002"]
                or meta.get("base_model_revision") != gate.REVISION or meta.get("training_steps") != 500):
            raise ValueError("Hair metadata differs")
        if plan["adapter_hashes"]["makeup"] != ADAPTER_SHA256 or plan["presets_sha256"] != PRESETS_SHA256:
            raise ValueError("Makeup contract differs")
        started = time.perf_counter()
        pipe = Flux2KleinPipeline.from_pretrained(str(model), torch_dtype=torch.float16, local_files_only=True)
        pipe.enable_model_cpu_offload(gpu_id=0)
        report.update(foundation_load_count=1, startup_seconds=time.perf_counter() - started)
        foundation = fingerprint(pipe)
        active, state, defaults = None, None, None
        states = {}
        for index, case in enumerate(sequence, 1):
            if active != case["adapter"]:
                if active is not None:
                    pipe.unload_lora_weights()
                assert_plain_foundation(pipe)
                directory = makeup if case["adapter"] == "makeup" else hair
                pipe.load_lora_weights(str(directory), weight_name="adapter.safetensors")
                state = inspect_adapter(pipe, directory / "adapter.safetensors", None)
                defaults = layer_scaling(pipe, state["library_adapter_name"])
                pipe.set_adapters(state["library_adapter_name"], adapter_weights=1.0)
                verify_scaling(pipe, state["library_adapter_name"], defaults, 1.0)
                if case["adapter"] in states and states[case["adapter"]] != state:
                    raise RuntimeError("Reloaded adapter tensors differ")
                states[case["adapter"]] = state
                active = case["adapter"]
                report["switches"].append({"before_call": index, "adapter": active, "state": state})
            if fingerprint(pipe) != foundation:
                raise RuntimeError("Foundation object changed")
            print("STYLE_VALIDATION START", index, "/ 29", case["feature"], case["subject_id"],
                  case["style_id"], flush=True)
            source = ImageOps.pad(subjects[case["subject_id"]], (512, 512),
                                  method=Image.Resampling.LANCZOS, color=(245, 245, 245))
            torch.cuda.synchronize(0)
            torch.cuda.reset_peak_memory_stats(0)
            started = time.perf_counter()
            report["new_inference_calls"] += 1
            with torch.no_grad():
                result = pipe(prompt=case["prompt"], image=source, width=512, height=512,
                              num_inference_steps=20, guidance_scale=case["guidance"],
                              generator=torch.Generator(device="cuda").manual_seed(1977)).images[0].convert("RGB")
            torch.cuda.synchronize(0)
            directory = makeup if active == "makeup" else hair
            if result.size != (512, 512) or inspect_adapter(pipe, directory / "adapter.safetensors",
                                                         state["library_adapter_name"]) != state:
                raise RuntimeError("Output dimensions or active tensors differ")
            scaling = verify_scaling(pipe, state["library_adapter_name"], defaults, 1.0)
            path = output / f"{index:02}-{case['subject_id']}-{case['style_id']}.png"
            result.save(path)
            row = {**case, "output": path.name, "adapter_sha256": plan["adapter_hashes"][active],
                   "adapter_weight": 1.0, "active_tensor_state": state, "scale_verification": scaling,
                   "prompt_sha256": sha256(case["prompt"].encode()).hexdigest(),
                   "png_sha256": sha256(path.read_bytes()).hexdigest(),
                   "rgb_sha256": sha256(result.tobytes()).hexdigest(),
                   "wall_seconds": time.perf_counter() - started,
                   "peak_gpu_allocated_mib": torch.cuda.max_memory_allocated(0) / 1024**2,
                   "visual_verdict": "NEEDS_REVIEW"}
            key = case["subject_id"] + "/" + case["style_id"]
            if case["kind"] == "existing" and key in plan["expected_prior_pixels"]:
                row["prior_control_match"] = row["rgb_sha256"] == plan["expected_prior_pixels"][key]
            if case["kind"] == "restoration":
                row["restoration_pixel_match"] = row["rgb_sha256"] == report["cases"][0]["rgb_sha256"]
            report["cases"].append(row)
            save()
            sheets(output, subjects, report["cases"])
            if row.get("prior_control_match") is False or row.get("restoration_pixel_match") is False:
                raise RuntimeError("Saved control or adapter restoration pixels differ; return evidence")
            print("STYLE_VALIDATION DONE", index, "/ 29", round(row["wall_seconds"], 2), "seconds", flush=True)
        report["status"] = "COMPLETE_REQUIRES_VISUAL_REVIEW"
    except BaseException as exc:
        report.update(status="FAILED", error_type=type(exc).__name__, error=str(exc))
        raise
    finally:
        save()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--plan", type=Path, default=ROOT / "data/style-expansion/STYLE-VAL-001/plan.json")
    args = parser.parse_args()
    run(args.output, args.plan)

