"""DATA-001 controlled photo-to-alternate generation on a Kaggle GPU.

Run after the EXP-001 inference dependencies are available in this kernel.
Default is one candidate per class (three outputs) for a visual pilot.
Use --all only after reviewing that pilot; --retry STYLE/NAME once per failed output.
No result is automatically accepted and this script never starts training.
"""

import argparse
from datetime import datetime, timezone
from io import BytesIO
import json
import math
import os
from pathlib import Path
import shutil
import sys
import time
from zipfile import ZipFile


REPO = "yikaiwang/FaceSketches-HairStyle40"
REVISION = "45de974926fe64551fc2d0b80973335e20ca10e2"
MODEL = "black-forest-labs/FLUX.2-klein-base-4B"
SOURCE = Path(__file__).resolve().parents[1] / "docs/data/DATA-001-selection.json"
OUT = Path("/kaggle/working/data001")
SCRATCH = Path("/tmp")  # Reuse EXP-001's ephemeral /tmp/hf-cache when present.
SIZE, STEPS, GUIDANCE = 512, 20, 4.0
SEED = 1977
PHRASES = {"CrewCut": "a crew cut", "BobHair": "a bob hairstyle", "LayeredHair": "layered hair"}


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--all", action="store_true", help="Generate the remaining 27 candidates after visual pilot review")
    group.add_argument("--retry", metavar="STYLE/FILENAME", help="One controlled second generation of a reviewed failure")
    args = parser.parse_args()

    if not SOURCE.exists():
        raise RuntimeError(f"Selection file missing: {SOURCE}. Upload or clone the repository with this script.")
    selection = json.loads(SOURCE.read_text(encoding="utf-8"))
    assert selection["source_revision"] == REVISION
    assert set(selection["styles"]) == set(PHRASES)
    assert [(s, selection["styles"][s]["alternate_style"]) for s in PHRASES] == [
        ("CrewCut", "BobHair"), ("BobHair", "LayeredHair"), ("LayeredHair", "CrewCut")]
    for style, config in selection["styles"].items():
        assert len(config["train"]) == 8 and len(config["val"]) == 2
        assert len(set(config["train"] + config["val"])) == 10

    os.environ["CUDA_VISIBLE_DEVICES"] = "0"
    os.environ["HF_HOME"] = str(SCRATCH / "hf-cache")
    os.environ["HF_HUB_CACHE"] = str(SCRATCH / "hf-cache/hub")
    SCRATCH.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    import torch
    from PIL import Image, ImageDraw, ImageOps
    from huggingface_hub import HfApi, hf_hub_download
    from diffusers import Flux2KleinPipeline

    if not torch.cuda.is_available():
        raise RuntimeError(f"STOP: {sys.executable} has no CUDA; no download attempted")
    print("CUDA:", torch.__version__, torch.version.cuda, torch.cuda.get_device_name(0), flush=True)
    api = HfApi()
    info = api.dataset_info(REPO, revision=REVISION)
    if info.sha != REVISION or str(info.card_data.license) != "apache-2.0":
        raise RuntimeError(f"STOP: source revision/license changed: {info.sha}, {info.card_data.license}")
    model_info = api.model_info(MODEL, files_metadata=True)
    model_bytes = sum(item.size or 0 for item in model_info.siblings or [])
    scratch_free = shutil.disk_usage(SCRATCH).free
    working_free = shutil.disk_usage(OUT).free
    if model_bytes <= 0 or scratch_free < math.ceil(model_bytes * 1.4) + 2 * 1024**3:
        raise RuntimeError(f"STOP: model size/scratch headroom insufficient: model={model_bytes}, free={scratch_free}")
    if working_free < 2 * 1024**3:
        raise RuntimeError(f"STOP: /kaggle/working free space too small for review artifacts: {working_free}")
    save_json(OUT / "environment_and_source.json", {
        "utc": datetime.now(timezone.utc).isoformat(), "python": sys.version,
        "torch": torch.__version__, "torch_cuda": torch.version.cuda,
        "gpu": torch.cuda.get_device_name(0), "gpu_vram_bytes": torch.cuda.get_device_properties(0).total_memory,
        "dataset_repository": REPO, "dataset_revision": info.sha, "dataset_license_declared": str(info.card_data.license),
        "model": MODEL, "model_revision": model_info.sha, "model_repository_bytes": model_bytes,
        "scratch_free_before_bytes": scratch_free,
        "working_free_before_bytes": working_free,
    })
    archive_path = hf_hub_download(REPO, "FaceSketches-HairStyle40.zip", repo_type="dataset", revision=REVISION, cache_dir=str(SCRATCH / "hf-cache/hub"))

    jobs = [(style, name, config["alternate_style"], split)
            for style, config in selection["styles"].items()
            for split in ("train", "val") for name in config[split]]
    if args.retry:
        style, name = args.retry.split("/", 1)
        jobs = [job for job in jobs if job[:2] == (style, name)]
        if len(jobs) != 1:
            raise RuntimeError(f"Retry item not selected: {args.retry}")
    elif not args.all:
        jobs = [next(job for job in jobs if job[0] == style) for style in PHRASES]
    if not jobs:
        raise RuntimeError("No jobs selected")

    prepared = []
    with ZipFile(archive_path) as archive:
        for style, name, target, split in jobs:
            member = f"FaceSketches-HairStyle40/image/{style}/{name}"
            with Image.open(BytesIO(archive.read(member))) as raw:
                photo = ImageOps.exif_transpose(raw).convert("RGB")
                if min(photo.size) < 256:
                    raise RuntimeError(f"STOP: source too small {member} {photo.size}")
                # Contain avoids cropping hair or face; the same square framing is used for the edit pair.
                normalized = ImageOps.pad(photo, (SIZE, SIZE), method=Image.Resampling.LANCZOS,
                                           color=(245, 245, 245), centering=(0.5, 0.5))
            key = f"{style}_{Path(name).stem}"
            path = OUT / "original" / f"{key}.png"
            path.parent.mkdir(parents=True, exist_ok=True)
            normalized.save(path)
            prepared.append((key, path, style, name, target, split))

    pipe = Flux2KleinPipeline.from_pretrained(MODEL, torch_dtype=torch.float16, cache_dir=os.environ["HF_HUB_CACHE"])
    pipe.enable_model_cpu_offload(gpu_id=0)
    print("Base pipeline loaded with FP16 and CPU offload on GPU 0", flush=True)
    for key, source, style, name, target, split in prepared:
        primary = OUT / "generated" / f"{key}.png"
        retry = OUT / "generated" / f"{key}_r2.png"
        if args.retry:
            if not primary.exists() or retry.exists():
                raise RuntimeError(f"Retry requires exactly one previous output: {primary}")
            dest, attempt = retry, 2
        else:
            if primary.exists():
                print("Already generated:", primary, flush=True)
                continue
            dest, attempt = primary, 1
        prompt = (f"Change the person's hairstyle to {PHRASES[target]} while preserving their identity, "
                  "face, expression, pose, clothing, lighting, framing, and background. Only change the hairstyle.")
        seed = SEED + attempt - 1
        torch.cuda.reset_peak_memory_stats(0)
        start = time.monotonic()
        try:
            result = pipe(prompt=prompt, image=Image.open(source).convert("RGB"),
                          width=SIZE, height=SIZE, num_inference_steps=STEPS,
                          guidance_scale=GUIDANCE,
                          generator=torch.Generator(device="cuda").manual_seed(seed)).images[0]
            dest.parent.mkdir(parents=True, exist_ok=True)
            result.save(dest)
            save_json(dest.with_suffix(".json"), {
                "source_class": style, "source_filename": name, "requested_class": target,
                "split": split, "source": str(source), "output": str(dest),
                "prompt": prompt, "seed": seed, "attempt": attempt,
                "steps": STEPS, "guidance": GUIDANCE, "width": SIZE, "height": SIZE,
                "runtime_seconds": time.monotonic() - start,
                "peak_gpu_allocated_bytes": torch.cuda.max_memory_allocated(0),
                "qa_status": "PENDING_VISUAL_REVIEW",
            })
            print(f"{key} -> {target}: {dest} ({time.monotonic() - start:.1f}s)", flush=True)
        except Exception:
            import traceback
            (OUT / "generation_error.txt").write_text(traceback.format_exc(), encoding="utf-8")
            raise
    metadata_files = sorted((OUT / "generated").glob("*.json"))
    sheet = Image.new("RGB", (510, max(1, len(metadata_files)) * 290), "white")
    draw = ImageDraw.Draw(sheet)
    for index, metadata_file in enumerate(metadata_files):
        meta = json.loads(metadata_file.read_text(encoding="utf-8"))
        source = Path(meta["source"])
        generated = Path(meta["output"])
        with Image.open(source) as a, Image.open(generated) as b:
            sheet.paste(ImageOps.contain(a.convert("RGB"), (245, 245)), (0, index * 290))
            sheet.paste(ImageOps.contain(b.convert("RGB"), (245, 245)), (255, index * 290))
        draw.text((0, index * 290 + 250), f"{meta['source_class']}/{meta['source_filename']} -> {meta['requested_class']}", fill="black")
        draw.text((0, index * 290 + 267), f"{meta['split']} / attempt {meta['attempt']} / PENDING VISUAL QA", fill="black")
    sheet.save(OUT / "generation_review_sheet.jpg", quality=90)
    print("Generation finished. Review", OUT / "generation_review_sheet.jpg", "; no outputs accepted automatically.")


if __name__ == "__main__":
    main()
