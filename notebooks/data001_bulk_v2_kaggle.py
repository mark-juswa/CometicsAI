"""Guarded remaining-27 DATA-001 generation. This file never accepts outputs.

Only run after three masked pilot results have explicit ACCEPT reviews and a
separate Supervisor/Project Lead approval. --plan is read-only and default.
"""

import argparse
from datetime import datetime, timezone
from io import BytesIO
import inspect
import json
import os
from pathlib import Path
import shutil
import sys
import time
from zipfile import ZipFile

import data001_pilot_v2_masked_kaggle as v2


def jobs_from_selection():
    selection = json.loads(v2.SELECTION.read_text(encoding="utf-8"))
    if selection["source_revision"] != "45de974926fe64551fc2d0b80973335e20ca10e2":
        raise RuntimeError("STOP: source selection revision changed")
    jobs = []
    for source_class in ("CrewCut", "BobHair", "LayeredHair"):
        entry = selection["styles"][source_class]
        for split in ("train", "val"):
            for filename in entry[split]:
                sample = f"{source_class}_{Path(filename).stem}"
                if sample not in v2.IDS:
                    jobs.append({"sample_id": sample, "source_class": source_class,
                                 "requested_class": entry["alternate_style"], "source_filename": filename,
                                 "source_revision": selection["source_revision"], "split": split,
                                 "source_archive_path": f"FaceSketches-HairStyle40/image/{source_class}/{filename}"})
    if len(jobs) != 27 or sum(j["split"] == "train" for j in jobs) != 21 or sum(j["split"] == "val" for j in jobs) != 6:
        raise RuntimeError("STOP: expected 21 remaining TRAIN and six VAL identities")
    return jobs


def require_approval(path, reviews, output, pilot_only=True):
    approval = json.loads(path.read_text(encoding="utf-8"))
    if (approval.get("decision") != "APPROVE_V2_BULK" or approval.get("pilot_sample_ids") != list(v2.IDS)
            or not approval.get("reviewer") or not approval.get("approved_utc")):
        raise RuntimeError("STOP: separate named V2 pilot approval is required")
    if (pilot_only and set(reviews) != set(v2.IDS)) or not set(v2.IDS).issubset(reviews):
        raise RuntimeError("STOP: review manifest must contain all three approved pilot identities")
    for sample in v2.IDS:
        review = reviews[sample]
        if review.get("status") != "ACCEPT" or review.get("attempt") != 1 or not str(review.get("notes", "")).strip():
            raise RuntimeError(f"STOP: explicit V2 ACCEPT with notes required for {sample}")
        folder = output / sample
        metadata = json.loads((folder / "generation.json").read_text(encoding="utf-8"))
        if (metadata.get("sample_id") != sample or metadata.get("method") != "pilot_v2_masked"
                or metadata.get("review_status") != "PENDING"
                or metadata.get("output_sha256") != v2.sha(folder / "result.png")
                or metadata.get("source_sha256") != v2.sha(folder / "source.png")
                or metadata.get("final_mask_sha256") != v2.sha(folder / "editable_mask.png")):
            raise RuntimeError(f"STOP: V2 pilot artifact provenance failed for {sample}")
    return approval


def prompt_for(target):
    return (f"Change only the hairstyle shape, cut, and length to {v2.PHRASES[target]}. "
            "Preserve the person's exact identity, facial structure, facial features, expression, skin tone, "
            "pose, clothing, jewelry, lighting, camera framing, and background. "
            "Preserve the original hair color and overall hair texture. Do not recolor the hair. "
            "Only alter what is necessary for the hairstyle transformation.")


def retry_one(job, reviews, approval, out):
    """One reviewed seed-only retry; never replaces attempt 1."""
    require_approval(approval, reviews, out, pilot_only=False)
    sample = job["sample_id"]
    review = reviews.get(sample, {})
    if (review.get("status") != "REGENERATE" or review.get("attempt") != 1
            or not str(review.get("notes", "")).strip()):
        raise RuntimeError(f"STOP: {sample} needs explicit REGENERATE for attempt 1 with notes")
    folder = out / sample
    first_meta = json.loads((folder / "generation.json").read_text(encoding="utf-8"))
    if (first_meta.get("sample_id") != sample or first_meta.get("attempt") != 1
            or first_meta.get("output_sha256") != v2.sha(folder / "result.png")
            or first_meta.get("source_sha256") != v2.sha(folder / "source.png")
            or first_meta.get("final_mask_sha256") != v2.sha(folder / "editable_mask.png")):
        raise RuntimeError(f"STOP: attempt-1 provenance mismatch for {sample}")
    dest = folder / "result_r2.png"
    meta_dest = folder / "generation_r2.json"
    if dest.exists() or meta_dest.exists():
        raise RuntimeError(f"STOP: attempt 2 already exists for {sample}")
    os.environ["CUDA_VISIBLE_DEVICES"] = "0"
    os.environ["HF_HOME"] = "/tmp/hf-cache"
    os.environ["HF_HUB_CACHE"] = "/tmp/hf-cache/hub"
    import torch
    import diffusers
    from PIL import Image
    if not torch.cuda.is_available():
        raise RuntimeError(f"STOP: {sys.executable} has no CUDA")
    cls = getattr(diffusers, "Flux2KleinInpaintPipeline", None)
    if cls is None or "mask_image" not in inspect.signature(cls.__call__).parameters:
        raise RuntimeError("STOP: installed Klein inpaint API unavailable")
    pipe = cls.from_pretrained(v2.MODEL, revision=v2.MODEL_REV, torch_dtype=torch.float16,
                               cache_dir=os.environ["HF_HUB_CACHE"])
    pipe.enable_model_cpu_offload(gpu_id=0)
    with Image.open(folder / "source.png") as im:
        source = im.convert("RGB")
    with Image.open(folder / "editable_mask.png") as im:
        mask = im.convert("L")
    torch.cuda.reset_peak_memory_stats(0)
    start = time.monotonic()
    result = pipe(prompt=first_meta["prompt"], image=source, mask_image=mask, width=v2.SIZE, height=v2.SIZE,
                  strength=v2.STRENGTH, num_inference_steps=v2.STEPS, guidance_scale=v2.GUIDANCE,
                  generator=torch.Generator(device="cuda").manual_seed(v2.SEED + 1)).images[0]
    Image.composite(result.convert("RGB"), source, mask).save(dest)
    v2.save_json(meta_dest, {**first_meta, "attempt": 2, "seed": v2.SEED + 1,
                             "retry_change": {"field": "seed", "from": v2.SEED, "to": v2.SEED + 1},
                             "output_path": str(dest), "output_sha256": v2.sha(dest),
                             "runtime_seconds": time.monotonic() - start,
                             "peak_gpu_allocated_bytes": torch.cuda.max_memory_allocated(0),
                             "generated_utc": datetime.now(timezone.utc).isoformat(), "review_status": "PENDING"})
    print(f"RETRY STOP: {sample} attempt 2 generated; human review required", flush=True)


def main():
    p = argparse.ArgumentParser()
    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--plan", action="store_true", help="Print remaining jobs; no model or data download")
    mode.add_argument("--execute", action="store_true", help="Actually generate the remaining 27 after approval")
    mode.add_argument("--retry", metavar="SAMPLE_ID", help="One seed-only retry after explicit REGENERATE review")
    p.add_argument("--reviews", type=Path)
    p.add_argument("--approval", type=Path)
    args = p.parse_args()
    jobs = jobs_from_selection()
    if not args.execute and not args.retry:
        print(json.dumps({"count": len(jobs), "jobs": jobs}, indent=2))
        return
    if not args.reviews or not args.approval:
        raise RuntimeError("STOP: generation requires --reviews and --approval")
    out = v2.OUT
    reviews = json.loads(args.reviews.read_text(encoding="utf-8"))
    if args.retry:
        selected = [job for job in jobs if job["sample_id"] == args.retry]
        if len(selected) != 1:
            raise RuntimeError("STOP: retry must name one of the 27 selected non-pilot identities")
        retry_one(selected[0], reviews, args.approval, out)
        return
    require_approval(args.approval, reviews, out)
    if any((out / job["sample_id"]).exists() for job in jobs):
        raise RuntimeError("STOP: a remaining-job folder already exists; inspect before rerunning")
    os.environ["CUDA_VISIBLE_DEVICES"] = "0"
    os.environ["HF_HOME"] = "/tmp/hf-cache"
    os.environ["HF_HUB_CACHE"] = "/tmp/hf-cache/hub"
    import torch
    import diffusers
    from PIL import Image, ImageOps
    from huggingface_hub import HfApi, hf_hub_download
    from transformers import SegformerImageProcessor, SegformerForSemanticSegmentation
    if not torch.cuda.is_available():
        raise RuntimeError(f"STOP: {sys.executable} has no CUDA")
    cls = getattr(diffusers, "Flux2KleinInpaintPipeline", None)
    if cls is None or "mask_image" not in inspect.signature(cls.__call__).parameters:
        raise RuntimeError(f"STOP: installed Diffusers {diffusers.__version__} lacks supported Klein inpaint")
    api = HfApi()
    dataset = api.dataset_info("yikaiwang/FaceSketches-HairStyle40", revision=jobs[0]["source_revision"])
    if dataset.sha != jobs[0]["source_revision"] or str(dataset.card_data.license) != "apache-2.0":
        raise RuntimeError("STOP: source dataset revision/license mismatch")
    if api.model_info(v2.MODEL, revision=v2.MODEL_REV).sha != v2.MODEL_REV:
        raise RuntimeError("STOP: FLUX model revision mismatch")
    if api.model_info(v2.PARSER, revision=v2.PARSER_REV).sha != v2.PARSER_REV:
        raise RuntimeError("STOP: parser model revision mismatch")
    if shutil.disk_usage("/tmp").free < 30 * 1024**3 or shutil.disk_usage(out).free < 2 * 1024**3:
        raise RuntimeError("STOP: insufficient /tmp or /kaggle/working storage")
    v2.save_json(out / "bulk_environment.json", {
        "utc": datetime.now(timezone.utc).isoformat(), "python": sys.version,
        "torch": torch.__version__, "torch_cuda": torch.version.cuda,
        "diffusers": diffusers.__version__, "gpu": torch.cuda.get_device_name(0),
        "model_revision": v2.MODEL_REV, "parser_revision": v2.PARSER_REV,
        "dataset_revision": dataset.sha, "dataset_card_license": str(dataset.card_data.license),
        "tmp_free_bytes": shutil.disk_usage("/tmp").free,
        "working_free_bytes": shutil.disk_usage(out).free,
    })
    v2.save_json(out / "bulk_plan.json", {"method": "pilot_v2_masked", "jobs": jobs,
                                         "pilot_approval": json.loads(args.approval.read_text(encoding="utf-8"))})
    archive_path = hf_hub_download("yikaiwang/FaceSketches-HairStyle40", "FaceSketches-HairStyle40.zip",
                                   repo_type="dataset", revision=dataset.sha, cache_dir=os.environ["HF_HUB_CACHE"])
    processor = SegformerImageProcessor.from_pretrained(v2.PARSER, revision=v2.PARSER_REV,
                                                         cache_dir=os.environ["HF_HUB_CACHE"])
    parser_model = SegformerForSemanticSegmentation.from_pretrained(
        v2.PARSER, revision=v2.PARSER_REV, use_safetensors=True, cache_dir=os.environ["HF_HUB_CACHE"]
    ).eval()
    with ZipFile(archive_path) as archive:
        for job in jobs:
            folder = out / job["sample_id"]
            folder.mkdir(parents=True, exist_ok=False)
            with Image.open(BytesIO(archive.read(job["source_archive_path"]))) as raw:
                source = ImageOps.pad(ImageOps.exif_transpose(raw).convert("RGB"), (v2.SIZE, v2.SIZE),
                                      method=Image.Resampling.LANCZOS, color=(245, 245, 245), centering=(0.5, 0.5))
            source.save(folder / "source.png")
            semantic, hair, mask, metrics = v2.make_mask(source, processor, parser_model, torch)
            for name, image in (("semantic_labels.png", semantic), ("raw_hair_mask.png", hair),
                                ("editable_mask.png", mask)):
                image.save(folder / name)
            v2.save_json(folder / "mask_metrics.json", metrics)
    del parser_model, processor
    pipe = cls.from_pretrained(v2.MODEL, revision=v2.MODEL_REV, torch_dtype=torch.float16,
                               cache_dir=os.environ["HF_HUB_CACHE"])
    pipe.enable_model_cpu_offload(gpu_id=0)
    for job in jobs:
        folder = out / job["sample_id"]
        with Image.open(folder / "source.png") as im:
            source = im.convert("RGB")
        with Image.open(folder / "editable_mask.png") as im:
            mask = im.convert("L")
        prompt = prompt_for(job["requested_class"])
        torch.cuda.reset_peak_memory_stats(0)
        start = time.monotonic()
        result = pipe(prompt=prompt, image=source, mask_image=mask, width=v2.SIZE, height=v2.SIZE,
                      strength=v2.STRENGTH, num_inference_steps=v2.STEPS, guidance_scale=v2.GUIDANCE,
                      generator=torch.Generator(device="cuda").manual_seed(v2.SEED)).images[0]
        result = Image.composite(result.convert("RGB"), source, mask)
        result.save(folder / "result.png")
        v2.save_json(folder / "generation.json", {
            **job, "method": "pilot_v2_masked", "attempt": 1, "source_path": str(folder / "source.png"),
            "source_sha256": v2.sha(folder / "source.png"), "output_path": str(folder / "result.png"),
            "output_sha256": v2.sha(folder / "result.png"), "raw_mask_sha256": v2.sha(folder / "raw_hair_mask.png"),
            "semantic_sha256": v2.sha(folder / "semantic_labels.png"),
            "final_mask_sha256": v2.sha(folder / "editable_mask.png"), "model": v2.MODEL,
            "model_revision": v2.MODEL_REV, "parser_model": v2.PARSER, "parser_revision": v2.PARSER_REV,
            "pipeline": "Flux2KleinInpaintPipeline", "dtype": "float16", "cpu_offload": True,
            "prompt": prompt, "seed": v2.SEED, "width": v2.SIZE, "height": v2.SIZE,
            "steps": v2.STEPS, "guidance": v2.GUIDANCE, "strength": v2.STRENGTH,
            "outside_mask_pixel_policy": "copy exact source RGB", "runtime_seconds": time.monotonic() - start,
            "peak_gpu_allocated_bytes": torch.cuda.max_memory_allocated(0),
            "generated_utc": datetime.now(timezone.utc).isoformat(), "review_status": "PENDING",
        })
        print(f"{job['sample_id']} generated; PENDING VISUAL REVIEW", flush=True)
    print("BULK STOP: 27 results need individual human review. No finalization or training was started.")


if __name__ == "__main__":
    main()
