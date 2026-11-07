"""HAIR-EXP-002: fixed offline Hair comparisons; no production profile mutation."""
import argparse
import base64
import csv
from hashlib import sha256
import html
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "backend")]
PLAN = ROOT / "data/style-expansion/HAIR-EXP-002/plan.json"
TARGETS = {
    "exp_butterfly_cut": ("layered_hair", "train001"),
    "exp_french_bob_wispy": ("bob_hair", "train001"),
    "exp_wolf_cut": ("shag_hair", "train002"),
    "exp_korean_two_block": ("side_part_undercut", "train002"),
    "exp_comma_hair": ("curtain_hair", "train002"),
}
SUBJECTS = ("d2_wavy_hair_25jpg", "d2_wavy_hair_27jpg",
            "d2_side_part_undercut_28jpg", "d2_side_part_undercut_9jpg")


def cases(plan):
    settings = {"width": 512, "height": 512, "steps": 20,
                "guidance": 4.0, "seed": 1977, "adapter_weight": 1.0}
    if (plan.get("schema") != "beautycore-hair-expansion-validation-v1"
            or plan.get("experiment") != "HAIR-EXP-002"
            or any(plan.get(key) is not False for key in ("production_enabled", "automatic_promotion", "training"))
            or plan.get("inference") != settings or plan.get("expected_calls") != 21
            or [s.get("id") for s in plan.get("subjects", [])] != list(SUBJECTS)
            or [g.get("style_id") for g in plan.get("groups", [])] != list(TARGETS)):
        raise ValueError("Hair comparison scope differs")
    rows = []
    for group in plan["groups"]:
        if (TARGETS[group["style_id"]] != (group.get("baseline_style_id"), group.get("adapter"))
                or group.get("subject_ids") != list(SUBJECTS[:2] if group["adapter"] == "train001"
                                                   or group["style_id"] == "exp_wolf_cut" else SUBJECTS[2:])
                or any(not isinstance(group.get(key), str) or not 20 <= len(group[key]) <= 2000
                       for key in ("baseline_prompt", "candidate_prompt", "acceptance"))):
            raise ValueError("Hair group contract differs")
        for subject in group["subject_ids"]:
            for kind in ("baseline", "candidate"):
                rows.append({"candidate_id": group["style_id"], "kind": kind,
                             "style_id": group["baseline_style_id"] if kind == "baseline" else group["style_id"],
                             "subject_id": subject, "adapter": group["adapter"],
                             "prompt": group[kind + "_prompt"]})
    rows.append({**rows[0], "kind": "restoration"})
    return rows


def verify_hair_contract(plan):
    """Use original checkpoint/style-ownership checks; never add candidate labels."""
    from scripts.kaggle_inference_server import read_adapter_metadata, REGISTRY
    path = ROOT / "backend/app/style_registry_train002_smoke.json"
    if sha256(path.read_bytes()).hexdigest() != plan["registry_sha256"]:
        raise ValueError("Expanded Hair registry hash differs")
    registry = json.loads(path.read_text(encoding="utf-8"))
    if REGISTRY != registry:
        raise RuntimeError("Run with the verified expanded Hair worker environment")
    configuration = json.loads((ROOT / "capstone_train002.json").read_text(encoding="utf-8"))
    paths = {key: ROOT / value for key, value in configuration["adapter_directories"].items()}
    if set(paths) != {"train001", "train002"} or set(plan["adapter_hashes"]) != set(paths):
        raise ValueError("Hair adapter inventory differs")
    for key, path in paths.items():
        metadata = read_adapter_metadata(path, key)
        if metadata["checkpoint_sha256"] != plan["adapter_hashes"][key]:
            raise ValueError("Hair checkpoint differs: " + key)
    styles = {s["style_id"]: s for s in registry["styles"]}
    for group in plan["groups"]:
        baseline = styles[group["baseline_style_id"]]
        if (baseline["adapter_id"] != group["adapter"]
                or baseline["prompt"] != group["baseline_prompt"]
                or group["style_id"] in styles):
            raise ValueError("Baseline ownership/prompt differs or candidate relabels training")
    return paths


def review(output, plan, rows):
    """Embedded original PNGs avoid broken file links when results are shared."""
    from PIL import Image, ImageDraw, ImageOps
    sections = []
    def tile(label, path):
        if not path.is_file():
            return "<figure><figcaption>" + html.escape(label) + " — pending</figcaption></figure>"
        data = "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode()
        return ('<figure><figcaption>' + html.escape(label) + '</figcaption><button onclick="enlarge(this)">'
                '<img alt="' + html.escape(label, quote=True) + '" src="' + data + '"></button></figure>')
    for group in plan["groups"]:
        cards = []
        sheet = Image.new("RGB", (3 * 512, 2 * 555), "white")
        draw = ImageDraw.Draw(sheet)
        for y, sid in enumerate(group["subject_ids"]):
            paths = [("Original", output / (sid + "-source.png"))]
            for kind in ("baseline", "candidate"):
                row = next((r for r in rows if r["candidate_id"] == group["style_id"]
                            and r["subject_id"] == sid and r["kind"] == kind), None)
                paths.append((group["baseline_style_id"] if kind == "baseline" else group["style_id"],
                              output / row["output"] if row else output / "missing.png"))
            cards.append("<h3>" + html.escape(sid) + "</h3><div class=grid>"
                         + "".join(tile(label, path) for label, path in paths) + "</div>")
            for x, (label, path) in enumerate(paths):
                draw.text((x * 512 + 5, y * 555 + 5), label, fill="black")
                if path.is_file():
                    with Image.open(path) as image:
                        im = ImageOps.contain(image.convert("RGB"), (512, 512))
                        sheet.paste(im, (x * 512 + (512 - im.width) // 2, y * 555 + 35))
        sheet.save(output / (group["style_id"] + "-comparison.jpg"), quality=94)
        sections.append("<section><h2>" + html.escape(group["style_id"]) + "</h2><p>"
                        + html.escape(group["acceptance"]) + "</p>" + "".join(cards) + "</section>")
    page = """<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Hair expansion comparison — not deployed</title>
<style>body{font:16px system-ui;background:#f5f5fa;color:#191921;margin:24px auto;max-width:1600px;padding:0 16px}
section{background:white;padding:20px;margin:20px 0;border-radius:12px}.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}
figure{margin:0;min-width:0}figcaption{overflow-wrap:anywhere;margin:6px 0}button{border:0;padding:0;background:transparent;cursor:zoom-in;width:100%}
img{display:block;max-width:100%;height:auto}dialog{max-width:95vw;max-height:95vh}dialog img{max-height:85vh;object-fit:contain}
dialog button{cursor:pointer;width:auto;padding:8px}@media(max-width:700px){.grid{grid-template-columns:1fr}}</style>
<h1>Hair comparison — not deployed</h1><p>Original, current baseline and candidate. Click an image to enlarge.
Review hairstyle distinction, face/expression, color and unwanted edits. Completed inference is not appearance approval.</p>
""" + "".join(sections) + """
<dialog id="viewer"><button onclick="this.parentElement.close()">Close</button><img alt="Original-size comparison"></dialog>
<script>function enlarge(button){const d=document.getElementById('viewer');d.querySelector('img').src=button.querySelector('img').src;d.showModal();}</script>"""
    (output / "review-self-contained.html").write_bytes(page.encode())
    with (output / "visual-review.csv").open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["candidate_id", "subject_id", "output", "style_fidelity",
                            "face_expression_preserved", "hair_color_preserved", "unwanted_changes",
                            "reviewer", "verdict", "notes"])
        writer.writeheader()
        for row in rows:
            if row["kind"] == "candidate":
                writer.writerow({**{key: row[key] for key in ("candidate_id", "subject_id", "output")},
                                 "verdict": "NEEDS_REVIEW"})


def run(output, plan_path=PLAN):
    import torch
    from PIL import Image, ImageOps
    from diffusers import Flux2KleinPipeline
    from scripts import unified_gate1 as gate
    from scripts.unified_gate2 import fingerprint, inspect_adapter
    # These generic tensor-state helpers are shared with the prior diagnostics.
    # No Makeup source photo, prompt, adapter or generation is used here.
    from scripts.makeup_quality_diagnostic import assert_plain_foundation, layer_scaling, verify_scaling
    output, plan_path = Path(output), Path(plan_path)
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    sequence = cases(plan)
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA required; no CPU diffusion")
    if output.exists():
        raise ValueError("Use a new output directory; preserve previous evidence")
    output.mkdir(parents=True)
    report = {"experiment": "HAIR-EXP-002", "status": "IN_PROGRESS", "production_enabled": False,
              "training": False, "plan_sha256": sha256(plan_path.read_bytes()).hexdigest(),
              "settings": plan["inference"], "cases": [], "switches": [], "subjects": plan["subjects"],
              "foundation_load_count": 0, "new_inference_calls": 0,
              "gpu": torch.cuda.get_device_name(0), "limits": plan["limits"]}
    def save():
        (output / "report.json").write_bytes((json.dumps(report, indent=2, allow_nan=False) + "\n").encode())
    save()
    try:
        subjects = {}
        for subject in plan["subjects"]:
            path = ROOT.parent / "fixtures" / subject["filename"]
            if sha256(path.read_bytes()).hexdigest() != subject["sha256"]:
                raise ValueError("Source photo differs: " + subject["id"])
            with Image.open(path) as image:
                subjects[subject["id"]] = image.convert("RGB")
            subjects[subject["id"]].save(output / (subject["id"] + "-source.png"))
        paths = verify_hair_contract(plan)
        model = Path(os.environ["AI_MODEL_DIR"])
        frozen = json.loads((ROOT / "docs/experiments/unified-kaggle-gate1-review.json").read_text(encoding="utf-8"))
        if model.name != gate.REVISION or gate.digest(model / "model_index.json") != frozen["base_model_index_sha256"]:
            raise ValueError("Pinned foundation model differs")
        started = time.perf_counter()
        pipe = Flux2KleinPipeline.from_pretrained(str(model), torch_dtype=torch.float16, local_files_only=True)
        pipe.enable_model_cpu_offload(gpu_id=0)
        report.update(foundation_load_count=1, model_load_seconds=time.perf_counter() - started)
        foundation = fingerprint(pipe)
        active, state, defaults = None, None, None
        states = {}
        for index, case in enumerate(sequence, 1):
            if active != case["adapter"]:
                if active is not None:
                    pipe.unload_lora_weights()
                assert_plain_foundation(pipe)
                directory = paths[case["adapter"]]
                pipe.load_lora_weights(str(directory), weight_name="adapter.safetensors")
                state = inspect_adapter(pipe, directory / "adapter.safetensors", None)
                defaults = layer_scaling(pipe, state["library_adapter_name"])
                pipe.set_adapters(state["library_adapter_name"], adapter_weights=1.0)
                verify_scaling(pipe, state["library_adapter_name"], defaults, 1.0)
                if case["adapter"] in states and states[case["adapter"]] != state:
                    raise RuntimeError("Reloaded Hair tensor state differs")
                states[case["adapter"]] = state
                active = case["adapter"]
                report["switches"].append({"before_call": index, "adapter": active, "state": state})
            if fingerprint(pipe) != foundation:
                raise RuntimeError("Foundation object changed")
            source = ImageOps.pad(subjects[case["subject_id"]], (512, 512),
                                  method=Image.Resampling.LANCZOS, color=(245, 245, 245), centering=(.5, .5))
            print("HAIR_VALIDATION START", index, "/ 21", case["subject_id"], case["style_id"], case["kind"], flush=True)
            torch.cuda.synchronize(0)
            torch.cuda.reset_peak_memory_stats(0)
            started = time.perf_counter()
            report["new_inference_calls"] += 1
            # no_grad is intentional: offloaded modules may materialize parameters
            # lazily; inference_mode caused a prior adapter-switch failure.
            with torch.no_grad():
                result = pipe(prompt=case["prompt"], image=source, width=512, height=512,
                              num_inference_steps=20, guidance_scale=4.0,
                              generator=torch.Generator(device="cuda").manual_seed(1977)).images[0].convert("RGB")
            torch.cuda.synchronize(0)
            if (result.size != (512, 512) or fingerprint(pipe) != foundation
                    or inspect_adapter(pipe, paths[active] / "adapter.safetensors", state["library_adapter_name"]) != state):
                raise RuntimeError("Hair output or tensor/foundation state differs")
            scaling = verify_scaling(pipe, state["library_adapter_name"], defaults, 1.0)
            path = output / f"{index:02}-{case['subject_id']}-{case['style_id']}.png"
            result.save(path)
            row = {**case, "output": path.name, "adapter_sha256": plan["adapter_hashes"][active],
                   "active_tensor_state": state, "scale_verification": scaling,
                   "execution_mode": "experimental_prompt_existing_hair_adapter" if case["kind"] == "candidate" else "original_hair_profile",
                   "prompt_sha256": sha256(case["prompt"].encode()).hexdigest(),
                   "normalized_source_rgb_sha256": sha256(source.tobytes()).hexdigest(),
                   "png_sha256": sha256(path.read_bytes()).hexdigest(), "rgb_sha256": sha256(result.tobytes()).hexdigest(),
                   "wall_seconds": time.perf_counter() - started,
                   "peak_gpu_allocated_mib": torch.cuda.max_memory_allocated(0) / 1024**2,
                   "visual_verdict": "NEEDS_REVIEW"}
            if case["kind"] == "restoration":
                row["restoration_pixel_match"] = row["rgb_sha256"] == report["cases"][0]["rgb_sha256"]
            report["cases"].append(row)
            save()
            if row.get("restoration_pixel_match") is False:
                raise RuntimeError("Hair restoration pixels differ; preserve results")
            print("HAIR_VALIDATION DONE", index, "/ 21", round(row["wall_seconds"], 2), "seconds", flush=True)
        report["status"] = "COMPLETE_REQUIRES_VISUAL_REVIEW"
    except BaseException as exc:
        report.update(status="FAILED", error_type=type(exc).__name__, error=str(exc))
        raise
    finally:
        save()
        review(output, plan, report["cases"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--plan", type=Path, default=PLAN)
    args = parser.parse_args()
    run(args.output, args.plan)
