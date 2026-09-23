"""DATA-001 pilot V2: exactly three masked FLUX.2 Klein hairstyle edits.

Run on the existing Kaggle CUDA environment. V1 evidence is required either at
/kaggle/working/data001 or via --v1-zip. No output is accepted automatically.
"""

import argparse
from datetime import datetime, timezone
import hashlib
import inspect
import json
import os
from pathlib import Path
import shutil
import sys
import time
from zipfile import ZipFile


ROOT = Path("/kaggle/working/data001")
OUT = ROOT / "pilot_v2_masked"
SELECTION = Path(__file__).resolve().parents[1] / "docs/data/DATA-001-selection.json"
PARSER = "jonathandinu/face-parsing"
PARSER_REV = "758b82e15a0178c9db39c1ff666a8b56e3a550c8"
MODEL = "black-forest-labs/FLUX.2-klein-base-4B"
MODEL_REV = "a3b4f4849157f664bdbc776fd7453c2783562f4d"
IDS = ("CrewCut_1", "BobHair_1", "LayeredHair_4")
PHRASES = {"BobHair": "a bob hairstyle", "LayeredHair": "a layered hairstyle", "CrewCut": "a crew cut"}
SEED, SIZE, STEPS, GUIDANCE, STRENGTH = 1977, 512, 20, 4.0, 0.8


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def source_files(args):
    if args.v1_zip:
        base = OUT / "v1_input"
        with ZipFile(args.v1_zip) as archive:
            for sample in IDS:
                for rel in (f"original/{sample}.png", f"generated/{sample}.png", f"generated/{sample}.json"):
                    matches = [n for n in archive.namelist() if n.endswith("/" + rel) or n == rel]
                    if len(matches) != 1:
                        raise RuntimeError(f"STOP: V1 ZIP must contain exactly one {rel}; found {matches}")
                    dest = base / rel
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    payload = archive.read(matches[0])
                    if dest.exists() and dest.read_bytes() != payload:
                        raise RuntimeError(f"STOP: refusing to overwrite different V1 evidence: {dest}")
                    if not dest.exists():
                        dest.write_bytes(payload)
        return base
    return args.v1_root


def validate_inputs(base):
    selection = json.loads(SELECTION.read_text(encoding="utf-8"))
    jobs = []
    for sample in IDS:
        style, stem = sample.rsplit("_", 1)
        entry = selection["styles"][style]
        names = [n for n in entry["train"] if Path(n).stem == stem]
        if len(names) != 1:
            raise RuntimeError(f"STOP: {sample} is not a unique TRAIN identity in selection")
        source = base / "original" / f"{sample}.png"
        v1 = base / "generated" / f"{sample}.png"
        sidecar = base / "generated" / f"{sample}.json"
        if not all(p.is_file() for p in (source, v1, sidecar)):
            raise RuntimeError(f"STOP: missing V1 evidence for {sample} under {base}")
        meta = json.loads(sidecar.read_text(encoding="utf-8"))
        if any((meta.get("sample_id") != sample, meta.get("source_class") != style,
                meta.get("requested_class") != entry["alternate_style"], meta.get("split") != "train",
                meta.get("source_sha256") != sha(source), meta.get("output_sha256") != sha(v1))):
            raise RuntimeError(f"STOP: V1 provenance mismatch for {sample}")
        jobs.append((sample, style, entry["alternate_style"], source, v1))
    return jobs


def make_mask(image, processor, parser_model, torch):
    """Hair plus growth margin, minus protected anatomy and apparel.

    Parser mask and final binary mask are saved for visual inspection. No
    automatic QA score can authorize a generated counterpart.
    """
    import numpy as np
    from PIL import Image, ImageFilter

    inputs = processor(images=image, return_tensors="pt")
    with torch.inference_mode():
        logits = parser_model(**inputs).logits
        logits = torch.nn.functional.interpolate(logits, size=(SIZE, SIZE), mode="bilinear", align_corners=False)
    labels = logits.argmax(1)[0].byte().cpu().numpy()
    raw = Image.fromarray((labels == 13).astype("uint8") * 255, "L")
    hair_count = int((labels == 13).sum())
    if not 2000 <= hair_count <= 110000:
        raise RuntimeError(f"STOP: implausible hair segmentation size {hair_count}")

    # A 32-pixel radius permits growth near the current hairstyle; original
    # long-hair pixels remain fully editable. Protect facial parts, jewelry,
    # neck, and clothing, expanding their boundary by four pixels.
    grown = np.asarray(raw.filter(ImageFilter.MaxFilter(65))) > 0
    protected_labels = np.isin(labels, list(range(1, 13)) + [14, 15, 16, 17, 18])
    protected = Image.fromarray(protected_labels.astype("uint8") * 255, "L")
    protected = np.asarray(protected.filter(ImageFilter.MaxFilter(9))) > 0
    editable = grown & ~protected
    # Fail closed if a parser or mask bug removes almost all source hair.
    retained_hair = (editable & (labels == 13)).sum() / hair_count
    if retained_hair < 0.8 or editable.mean() > 0.48:
        raise RuntimeError(f"STOP: unsafe mask: source hair retained={retained_hair:.3f}, editable area={editable.mean():.3f}")
    final = Image.fromarray(editable.astype("uint8") * 255, "L")
    return Image.fromarray(labels, "L"), raw, final, {"hair_pixels": hair_count, "editable_pixels": int(editable.sum()), "retained_hair_fraction": float(retained_hair)}


def review_sheet(jobs):
    from PIL import Image, ImageDraw, ImageOps
    sheet = Image.new("RGB", (4 * 512, 3 * 552), "white")
    draw = ImageDraw.Draw(sheet)
    for row, (sample, source_class, target_class, source, v1) in enumerate(jobs):
        paths = [v1, source, OUT / sample / "editable_mask.png", OUT / sample / "result.png"]
        for col, path in enumerate(paths):
            with Image.open(path) as img:
                shown = img.convert("RGB")
                sheet.paste(ImageOps.contain(shown, (512, 512)), (col * 512, row * 552))
        draw.text((8, row * 552 + 518), f"{sample}  {source_class} -> {target_class}  TRAIN  PENDING REVIEW", fill="black")
    for col, label in enumerate(("V1 RESULT", "SOURCE", "V2 EDIT MASK (WHITE=EDIT)", "V2 RESULT")):
        draw.text((col * 512 + 8, 3 * 552 - 18), label, fill="black")
    sheet.save(OUT / "v1_v2_comparison.jpg", quality=92)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--v1-root", type=Path, default=ROOT)
    p.add_argument("--v1-zip", type=Path, help="Pilot V1 ZIP if Kaggle's prior working directory is unavailable")
    args = p.parse_args()
    os.environ["CUDA_VISIBLE_DEVICES"] = "0"
    os.environ["HF_HOME"] = "/tmp/hf-cache"
    os.environ["HF_HUB_CACHE"] = "/tmp/hf-cache/hub"
    OUT.mkdir(parents=True, exist_ok=True)
    base = source_files(args)
    jobs = validate_inputs(base)
    if any((OUT / sample / "result.png").exists() for sample in IDS):
        raise RuntimeError("STOP: V2 result already exists; refusing to overwrite pilot evidence")

    import torch
    import diffusers
    import transformers
    from PIL import Image
    from huggingface_hub import HfApi
    from transformers import SegformerImageProcessor, SegformerForSemanticSegmentation

    if not torch.cuda.is_available():
        raise RuntimeError(f"STOP: {sys.executable} has no CUDA")
    pipe_class = getattr(diffusers, "Flux2KleinInpaintPipeline", None)
    if pipe_class is None:
        raise RuntimeError(f"STOP: installed diffusers {diffusers.__version__} lacks Flux2KleinInpaintPipeline")
    needed = {"image", "mask_image", "strength", "guidance_scale", "num_inference_steps"}
    if not needed.issubset(inspect.signature(pipe_class.__call__).parameters):
        raise RuntimeError("STOP: installed Klein inpaint call signature lacks required arguments")
    api = HfApi()
    if api.model_info(PARSER, revision=PARSER_REV).sha != PARSER_REV:
        raise RuntimeError("STOP: parser revision mismatch")
    if api.model_info(MODEL, revision=MODEL_REV).sha != MODEL_REV:
        raise RuntimeError("STOP: FLUX revision mismatch")
    free = shutil.disk_usage("/tmp").free
    if free < 30 * 1024**3 or shutil.disk_usage(OUT).free < 2 * 1024**3:
        raise RuntimeError(f"STOP: insufficient disk headroom: /tmp={free}")
    save_json(OUT / "environment.json", {
        "utc": datetime.now(timezone.utc).isoformat(), "python": sys.version, "torch": torch.__version__,
        "cuda": torch.version.cuda, "diffusers": diffusers.__version__, "transformers": transformers.__version__,
        "gpu": torch.cuda.get_device_name(0), "gpu_vram_bytes": torch.cuda.get_device_properties(0).total_memory,
        "inpaint_signature": str(inspect.signature(pipe_class.__call__)), "method": "pilot_v2_masked",
        "parser": PARSER, "parser_revision": PARSER_REV, "parser_license": "not declared in pinned model card",
        "model": MODEL, "model_revision": MODEL_REV, "tmp_free_before_bytes": free,
    })

    # Parse on CPU, then release model RAM before loading the much larger FLUX pipeline.
    processor = SegformerImageProcessor.from_pretrained(PARSER, revision=PARSER_REV, cache_dir=os.environ["HF_HUB_CACHE"])
    parser_model = SegformerForSemanticSegmentation.from_pretrained(
        PARSER, revision=PARSER_REV, use_safetensors=True, cache_dir=os.environ["HF_HUB_CACHE"]
    ).eval()
    for sample, source_class, target_class, source, v1 in jobs:
        folder = OUT / sample
        folder.mkdir(parents=True, exist_ok=True)
        with Image.open(source) as img:
            image = img.convert("RGB")
        if image.size != (SIZE, SIZE):
            raise RuntimeError(f"STOP: {sample} source size is {image.size}, expected 512x512")
        semantic, raw, mask, metrics = make_mask(image, processor, parser_model, torch)
        for name, obj in (("semantic_labels.png", semantic), ("raw_hair_mask.png", raw), ("editable_mask.png", mask)):
            obj.save(folder / name)
        save_json(folder / "mask_metrics.json", metrics)
    del parser_model, processor

    pipe = pipe_class.from_pretrained(MODEL, revision=MODEL_REV, torch_dtype=torch.float16,
                                      cache_dir=os.environ["HF_HUB_CACHE"])
    pipe.enable_model_cpu_offload(gpu_id=0)
    for sample, source_class, target_class, source, v1 in jobs:
        folder = OUT / sample
        with Image.open(source) as img:
            image = img.convert("RGB")
        with Image.open(folder / "editable_mask.png") as img:
            mask = img.convert("L")
        prompt = (f"Change only the hairstyle shape, cut, and length to {PHRASES[target_class]}. "
                  "Preserve the person's exact identity, facial structure, facial features, expression, skin tone, "
                  "pose, clothing, jewelry, lighting, camera framing, and background. "
                  "Preserve the original hair color and overall hair texture. Do not recolor the hair. "
                  "Only alter what is necessary for the hairstyle transformation.")
        torch.cuda.reset_peak_memory_stats(0)
        started = time.monotonic()
        try:
            result = pipe(prompt=prompt, image=image, mask_image=mask, width=SIZE, height=SIZE,
                          strength=STRENGTH, num_inference_steps=STEPS, guidance_scale=GUIDANCE,
                          generator=torch.Generator(device="cuda").manual_seed(SEED)).images[0]
            # The pipeline blends in latent space; restore original pixels outside
            # the mask after VAE decoding to make preservation exact there.
            result = Image.composite(result.convert("RGB"), image, mask)
            result.save(folder / "result.png")
            save_json(folder / "generation.json", {
                "sample_id": sample, "source_class": source_class, "requested_class": target_class, "split": "train",
                "method": "pilot_v2_masked", "attempt": 1, "source_path": str(source), "v1_path": str(v1),
                "source_sha256": sha(source), "v1_sha256": sha(v1), "output_path": str(folder / "result.png"),
                "output_sha256": sha(folder / "result.png"), "semantic_sha256": sha(folder / "semantic_labels.png"),
                "raw_mask_sha256": sha(folder / "raw_hair_mask.png"), "final_mask_sha256": sha(folder / "editable_mask.png"),
                "parser_model": PARSER, "parser_revision": PARSER_REV, "model": MODEL, "model_revision": MODEL_REV,
                "pipeline": "Flux2KleinInpaintPipeline", "dtype": "float16", "cpu_offload": True,
                "prompt": prompt, "seed": SEED, "width": SIZE, "height": SIZE, "steps": STEPS,
                "guidance": GUIDANCE, "strength": STRENGTH, "outside_mask_pixel_policy": "copy exact source RGB",
                "runtime_seconds": time.monotonic() - started,
                "peak_gpu_allocated_bytes": torch.cuda.max_memory_allocated(0),
                "generated_utc": datetime.now(timezone.utc).isoformat(), "review_status": "PENDING",
            })
            print(f"V2 {sample}: {time.monotonic() - started:.1f}s, {torch.cuda.max_memory_allocated(0)} peak bytes", flush=True)
        except Exception:
            import traceback
            (OUT / "error.txt").write_text(traceback.format_exc(), encoding="utf-8")
            raise
    review_sheet(jobs)
    print("PILOT STOP: three V2 results generated; visual review is required. No ACCEPT decision recorded.", flush=True)
    print("Review:", OUT / "v1_v2_comparison.jpg", flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        import traceback
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / "error.txt").write_text(traceback.format_exc(), encoding="utf-8")
        raise
