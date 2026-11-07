"""Private STYLE-EXP-001 portrait prompt pilot. No routes or production catalog mutation."""
import argparse
import asyncio
import base64
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))
PLAN = ROOT / "data/style-expansion/STYLE-EXP-001/pilot.json"


def cases(plan):
    result = []
    for feature, styles in (("hairstyle", ("layered_hair", "curtain_hair", "side_part_undercut")),
                            ("makeup", ("matte_nude", "bronze_golden_glam"))):
        result.extend({"kind": "baseline", "feature": feature, "style_id": style} for style in styles)
    for item in plan["portrait_candidates"]:
        for adapter in item["adapters"]:
            result.append({"kind": "candidate", "feature": item["feature"],
                           "style_id": item["candidate_id"], "adapter": adapter,
                           "prompt": item["prompt"]})
    result += [{"kind": "restoration", "feature": "hairstyle", "style_id": "layered_hair"},
               {"kind": "restoration", "feature": "makeup", "style_id": "matte_nude"}]
    return result


def contact_sheet(output, rows, sources, feature):
    from PIL import Image, ImageDraw, ImageOps
    selected = [r for r in rows if r["feature"] == feature]
    tiles = [("Original: reused fixture", sources[feature])]
    for row in selected:
        with Image.open(output / row["output"]) as opened:
            tiles.append((row["kind"] + " / " + row["style_id"] + " / " + row["adapter"], opened.convert("RGB")))
    sheet = Image.new("RGB", (3 * 384, ((len(tiles) + 2) // 3) * 310), "white")
    draw = ImageDraw.Draw(sheet)
    for index, (label, image) in enumerate(tiles):
        x, y = index % 3 * 384, index // 3 * 310
        # Wrap long labels without requiring downloaded fonts.
        for line, offset in enumerate(range(0, len(label), 52)):
            draw.text((x + 5, y + line * 13 + 4), label[offset:offset + 52], fill="black")
        sheet.paste(ImageOps.contain(image, (384, 260)), (x, y + 45))
    sheet.save(output / (feature + "-comparison.jpg"), quality=92)


def runtime_case(runtime, server, case, source):
    """Synchronous, private process only. Never patch production prompt dictionaries."""
    from PIL import Image, ImageOps
    owner = runtime.owner
    if case["kind"] != "candidate":
        raise ValueError("Candidate path only")
    owner.switch(case["adapter"])
    active = owner.assert_active(case["adapter"])
    image = ImageOps.pad(source, (512, 512), method=Image.Resampling.LANCZOS,
                         color=(245, 245, 245), centering=(.5, .5))
    # Explicitly experimental inference: no fabricated supported_style_ids or preset provenance.
    with owner.torch.inference_mode():
        result = owner.pipe(prompt=case["prompt"], image=image, width=512, height=512,
                            num_inference_steps=20, guidance_scale=4.0,
                            generator=owner.torch.Generator(device="cuda").manual_seed(1977)).images[0]
    owner.synchronize()
    owner.assert_active(case["adapter"])
    if result.size != (512, 512):
        raise ValueError("Unexpected pilot output dimensions")
    return result.convert("RGB"), active


async def run(output, plan_path=PLAN):
    import torch
    from PIL import Image
    from scripts import unified_gate3_server as server
    plan = json.loads(Path(plan_path).read_text(encoding="utf-8"))
    if plan["schema"] != "beautycore-style-expansion-pilot-v1" or plan["production_enabled"]:
        raise ValueError("Wrong experimental plan")
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA GPU required. Do not run diffusion on CPU.")
    if output.exists():
        raise ValueError("Use a new output folder; evidence is never replaced")
    output.mkdir(parents=True)
    report = {"status": "IN_PROGRESS", "production_enabled": False, "trained_model": False,
              "scope": "One reused portrait per feature; prompt/adapter feasibility only",
              "settings": {"width": 512, "height": 512, "steps": 20, "guidance": 4.0, "seed": 1977},
              "plan_sha256": sha256(Path(plan_path).read_bytes()).hexdigest(),
              "gpu": torch.cuda.get_device_name(0), "torch": torch.__version__,
              "cuda": torch.version.cuda, "cases": [],
              "limits": ["No new training, no new portrait dataset, no human quality acceptance.",
                         "The input was previously held out for a feature experiment; not a new independent test set.",
                         "One observation per case; cold/switch timing is included, not a speed comparison.",
                         "Experimental prompts are not production supported presets.",
                         "No Render, Gemini, public tunnel, website registration, or browser test."]}
    def save():
        (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    save()
    sources = {}
    try:
        # Gate's original manifest owns source image hashes; all checks run before any model load.
        gate_plan = server.gate.verify_bundle()
        for feature in ("hairstyle", "makeup"):
            item = gate_plan["features"][feature]
            path = server.gate.safe_path(ROOT, item["input"])
            if server.gate.digest(path) != item["input_sha256"]:
                raise ValueError("Pilot fixture differs from reviewed bundle")
            with Image.open(path) as opened:
                sources[feature] = opened.convert("RGB")
            sources[feature].save(output / (feature + "-source.png"))
            report.setdefault("inputs", {})[feature] = {
                "sha256": item["input_sha256"], "origin": item["reference_context"]}
        runtime = server.UnifiedRuntime()
        begin = time.perf_counter()
        runtime.load()
        report.update(startup_seconds=time.perf_counter() - begin,
                      foundation_load_count=runtime.foundation_load_count,
                      base_revision=server.gate.REVISION)
        if runtime.foundation_load_count != 1:
            raise RuntimeError("Expected one foundation")
        # Pilot leaves the accepted production Nails-only cache untouched. Portrait cache stays off.
        runtime.owner.performance = None
        planned = cases(plan)
        for number, case in enumerate(planned, 1):
            print("STYLE_PILOT START", number, "/", len(planned), case["kind"], case["style_id"],
                  case.get("adapter", "verified baseline"), flush=True)
            torch.cuda.synchronize(0)
            torch.cuda.reset_peak_memory_stats(0)
            begin = time.perf_counter()
            if case["kind"] == "candidate":
                image, active = runtime_case(runtime, server, case, sources[case["feature"]])
                adapter = case["adapter"]
                prompt = case["prompt"]
                adapter_sha = runtime.owner.specs[adapter]["expected"]["adapter_sha256"]
            else:
                adapter = server.selected_adapter(case["feature"], case["style_id"])
                payload = await runtime.owner.generate(adapter, "style-pilot-" + str(number),
                                                       image=sources[case["feature"]], style_id=case["style_id"])
                raw = base64.b64decode(payload["image"]["data_url"].split(",", 1)[1], validate=True)
                with Image.open(BytesIO(raw)) as opened:
                    if opened.format != "PNG":
                        raise ValueError("Expected a PNG baseline")
                    image = opened.convert("RGB")
                active = runtime.owner.assert_active(adapter)
                prompt = (server.HAIR_STYLES[case["style_id"]]["prompt"] if case["feature"] == "hairstyle"
                          else server.MAKEUP_PROMPTS[case["style_id"]])
                adapter_sha = payload["metadata"]["adapter_sha256"]
            torch.cuda.synchronize(0)
            elapsed = time.perf_counter() - begin
            name = f"{number:02d}-{case['feature']}-{case['kind']}-{case['style_id']}-{adapter.replace(':', '-')}.png"
            image.save(output / name)
            row = {**{k: v for k, v in case.items() if k != "prompt"}, "adapter": adapter,
                   "adapter_sha256": adapter_sha, "adapter_state": active,
                   "prompt": prompt, "prompt_sha256": sha256(prompt.encode()).hexdigest(),
                   "output": name, "png_sha256": sha256((output / name).read_bytes()).hexdigest(),
                   "rgb_sha256": sha256(image.tobytes()).hexdigest(), "wall_seconds": elapsed,
                   "peak_gpu_allocated_mib": torch.cuda.max_memory_allocated(0) / 1024 ** 2,
                   "visual_verdict": "NEEDS_REVIEW"}
            report["cases"].append(row)
            save()
            print("STYLE_PILOT DONE", number, "/", len(planned), round(elapsed, 2), "seconds", flush=True)
            contact_sheet(output, report["cases"], sources, case["feature"])
        report["restoration"] = []
        for row in report["cases"]:
            if row["kind"] == "restoration":
                initial = next(r for r in report["cases"] if r["kind"] == "baseline" and
                               r["feature"] == row["feature"] and r["style_id"] == row["style_id"])
                report["restoration"].append({"feature": row["feature"],
                                              "pixels_match": row["rgb_sha256"] == initial["rgb_sha256"]})
        if not all(r["pixels_match"] for r in report["restoration"]):
            raise RuntimeError("Baseline changed after experimental adapter sequence; inspect report")
        report["status"] = "PILOT_FINISHED_REQUIRES_VISUAL_REVIEW"
    except BaseException as exc:
        report["status"], report["error_type"] = "FAILED", type(exc).__name__
        raise
    finally:
        save()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    asyncio.run(run(args.output.resolve()))
