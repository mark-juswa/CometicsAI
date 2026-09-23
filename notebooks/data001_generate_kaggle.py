"""DATA-001 controlled photo-to-alternate generation on a Kaggle GPU.

Run after the EXP-001 inference dependencies are available in this kernel.
Default is one candidate per class (three outputs) for a visual pilot.
Use --all for the remaining selected 27 after the existing V1 pilot artifacts
are restored. --retry STYLE/NAME requires an explicit REGENERATE review.
No result is automatically accepted and this script never starts training.
"""

import argparse
import hashlib
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
MODEL_REVISION = "a3b4f4849157f664bdbc776fd7453c2783562f4d"
SOURCE = Path(__file__).resolve().parents[1] / "docs/data/DATA-001-selection.json"
OUT = Path("/kaggle/working/data001")
SCRATCH = Path("/tmp")  # Reuse EXP-001's ephemeral /tmp/hf-cache when present.
SIZE, STEPS, GUIDANCE = 512, 20, 4.0
SEED = 1977
PHRASES = {"CrewCut": "a crew cut", "BobHair": "a bob hairstyle", "LayeredHair": "a layered hairstyle"}
PILOT_STYLES = ("CrewCut", "BobHair", "LayeredHair")


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def build_jobs(selection):
    jobs = []
    for style in PILOT_STYLES:
        config = selection["styles"][style]
        for split in ("train", "val"):
            for name in config[split]:
                sample_id = f"{style}_{Path(name).stem}"
                jobs.append({"sample_id": sample_id, "source_class": style,
                             "source_filename": name, "requested_class": config["alternate_style"],
                             "split": split, "source_archive_path": f"FaceSketches-HairStyle40/image/{style}/{name}"})
    return jobs


def pilot_jobs(jobs):
    pilot = [next(job for job in jobs if job["source_class"] == style and job["split"] == "train")
             for style in PILOT_STYLES]
    assert len({job["sample_id"] for job in pilot}) == 3
    return pilot


def make_plan(jobs, retry=False):
    plan = []
    for job in jobs:
        attempt = 2 if retry else 1
        prompt = (f"Change the person's hairstyle to {PHRASES[job['requested_class']]} while preserving their identity, "
                  "facial features, expression, pose, clothing, lighting, framing, and background. Only change the hairstyle.")
        plan.append({**job, "prompt": prompt, "seed": SEED + attempt - 1, "attempt": attempt,
                     "source_path": (OUT / "original" / f"{job['sample_id']}.png").as_posix(),
                     "output_path": (OUT / "generated" / f"{job['sample_id']}{'_r2' if retry else ''}.png").as_posix()})
    return plan


def require_review(path, sample_id, expected):
    if not path or not path.is_file():
        raise RuntimeError(f"STOP: a review manifest is required for {sample_id}")
    reviews = json.loads(path.read_text(encoding="utf-8"))
    review = reviews.get(sample_id)
    if (not isinstance(review, dict) or review.get("status") != expected
            or review.get("attempt") != 1
            or not str(review.get("notes", "")).strip()):
        raise RuntimeError(f"STOP: {sample_id} needs an explicit {expected} review of attempt 1; got {review}")
    return review


def import_pilot_zip(path, pilot):
    """Restore only the known V1 pilot files from the Supervisor's ZIP."""
    if not path.is_file():
        raise RuntimeError(f"STOP: pilot ZIP missing: {path}")
    with ZipFile(path) as archive:
        names = archive.namelist()
        for job in pilot:
            sample = job["sample_id"]
            for relative in (f"original/{sample}.png", f"generated/{sample}.png",
                             f"generated/{sample}.json"):
                matches = [name for name in names if name == relative or name.endswith("/" + relative)]
                if len(matches) != 1:
                    raise RuntimeError(f"STOP: pilot ZIP must have exactly one {relative}; found {matches}")
                dest = OUT / relative
                payload = archive.read(matches[0])
                dest.parent.mkdir(parents=True, exist_ok=True)
                if dest.exists() and dest.read_bytes() != payload:
                    raise RuntimeError(f"STOP: existing pilot file differs: {dest}")
                if not dest.exists():
                    dest.write_bytes(payload)


def verify_existing_pilot(pilot):
    """Require the three V1 pilot artifacts, but leave quality to final review."""
    planned = {job["sample_id"]: job for job in make_plan(pilot)}
    for job in pilot:
        metadata = OUT / "generated" / f"{job['sample_id']}.json"
        image = metadata.with_suffix(".png")
        source = OUT / "original" / f"{job['sample_id']}.png"
        if not metadata.is_file() or not image.is_file() or not source.is_file():
            raise RuntimeError(f"STOP: restore the V1 pilot image, metadata, and original for {job['sample_id']}")
        evidence = json.loads(metadata.read_text(encoding="utf-8"))
        if (evidence.get("sample_id") != job["sample_id"] or evidence.get("attempt") != 1
                or evidence.get("source_class") != job["source_class"]
                or evidence.get("source_filename") != job["source_filename"]
                or evidence.get("requested_class") != job["requested_class"]
                or evidence.get("split") != "train" or evidence.get("model") != MODEL
                or evidence.get("model_revision") != MODEL_REVISION
                or evidence.get("source_revision") != REVISION
                or evidence.get("prompt") != planned[job["sample_id"]]["prompt"]
                or evidence.get("seed") != SEED
                or evidence.get("source_sha256") != hashlib.sha256(source.read_bytes()).hexdigest()
                or evidence.get("output_sha256") != hashlib.sha256(image.read_bytes()).hexdigest()):
            raise RuntimeError(f"STOP: V1 pilot metadata/hash mismatch for {job['sample_id']}")


def render_review_sheet():
    from PIL import Image, ImageDraw, ImageOps
    metadata_files = sorted((OUT / "generated").glob("*.json"))
    if not metadata_files:
        return
    sheet = Image.new("RGB", (510, len(metadata_files) * 290), "white")
    draw = ImageDraw.Draw(sheet)
    for index, metadata_file in enumerate(metadata_files):
        meta = json.loads(metadata_file.read_text(encoding="utf-8"))
        source, generated = Path(meta["source"]), Path(meta["output"])
        with Image.open(source) as a, Image.open(generated) as b:
            sheet.paste(ImageOps.contain(a.convert("RGB"), (245, 245)), (0, index * 290))
            sheet.paste(ImageOps.contain(b.convert("RGB"), (245, 245)), (255, index * 290))
        draw.text((0, index * 290 + 250), f"{meta['sample_id']}: {meta['source_class']} -> {meta['requested_class']}", fill="black")
        draw.text((0, index * 290 + 267), f"{meta['split']} / attempt {meta['attempt']} / PENDING VISUAL QA", fill="black")
    sheet.save(OUT / "generation_review_sheet.jpg", quality=90)


def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--all", action="store_true", help="Generate the remaining 27 selected identities using the V1 method")
    group.add_argument("--plan-all", action="store_true", help="Print the remaining 27 jobs without downloading or generating")
    group.add_argument("--retry", metavar="STYLE/FILENAME", help="One controlled second generation of a reviewed failure")
    parser.add_argument("--reviews", type=Path, help="JSON with explicit ACCEPT/REGENERATE/REJECT decisions")
    parser.add_argument("--pilot-zip", type=Path, help="Restore the three V1 pilot artifacts when Kaggle working storage was reset")
    args = parser.parse_args()
    if args.pilot_zip and not args.all:
        raise RuntimeError("STOP: --pilot-zip is only used with --all")

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
    jobs = build_jobs(selection)
    pilot = pilot_jobs(jobs)
    pilot_ids = {job["sample_id"] for job in pilot}
    if args.plan_all:
        remaining = [job for job in jobs if job["sample_id"] not in pilot_ids]
        assert len(remaining) == 27 and sum(job["split"] == "train" for job in remaining) == 21
        print(json.dumps({"method": "v1_global", "count": len(remaining), "jobs": remaining}, indent=2))
        return
    if args.retry:
        if "/" not in args.retry:
            raise RuntimeError("STOP: --retry must be STYLE/FILENAME, e.g. BobHair/2.jpg")
        style, name = args.retry.split("/", 1)
        jobs = [job for job in jobs if job["source_class"] == style and job["source_filename"] == name]
        if len(jobs) != 1:
            raise RuntimeError(f"STOP: retry item is not selected: {args.retry}")
        require_review(args.reviews, jobs[0]["sample_id"], "REGENERATE")
    elif args.all:
        if args.pilot_zip:
            import_pilot_zip(args.pilot_zip, pilot)
        verify_existing_pilot(pilot)
        jobs = [job for job in jobs if job["sample_id"] not in pilot_ids]
        if (len(jobs) != 27 or sum(job["split"] == "train" for job in jobs) != 21
                or sum(job["split"] == "val" for job in jobs) != 6):
            raise RuntimeError("STOP: V1 bulk plan must contain 21 TRAIN and six VAL identities")
    else:
        jobs = pilot
    if not jobs:
        raise RuntimeError("STOP: no jobs selected")
    OUT.mkdir(parents=True, exist_ok=True)
    plan = make_plan(jobs, retry=bool(args.retry))
    plan_path = OUT / ("pilot_plan.json" if not args.all and not args.retry else
                       "full_plan.json" if args.all else f"retry_plan_{jobs[0]['sample_id']}.json")
    if plan_path.exists() and json.loads(plan_path.read_text(encoding="utf-8")) != plan:
        raise RuntimeError(f"STOP: existing generation plan differs: {plan_path}")
    save_json(plan_path, plan)

    os.environ["CUDA_VISIBLE_DEVICES"] = "0"
    os.environ["HF_HOME"] = str(SCRATCH / "hf-cache")
    os.environ["HF_HUB_CACHE"] = str(SCRATCH / "hf-cache/hub")
    SCRATCH.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    import torch
    from PIL import Image, ImageOps
    from huggingface_hub import HfApi, hf_hub_download
    from diffusers import Flux2KleinPipeline

    if not torch.cuda.is_available():
        raise RuntimeError(f"STOP: {sys.executable} has no CUDA; no download attempted")
    print("CUDA:", torch.__version__, torch.version.cuda, torch.cuda.get_device_name(0), flush=True)
    api = HfApi()
    info = api.dataset_info(REPO, revision=REVISION)
    if info.sha != REVISION or str(info.card_data.license) != "apache-2.0":
        raise RuntimeError(f"STOP: source revision/license changed: {info.sha}, {info.card_data.license}")
    model_info = api.model_info(MODEL, revision=MODEL_REVISION, files_metadata=True)
    if model_info.sha != MODEL_REVISION:
        raise RuntimeError(f"STOP: FLUX Base revision changed: {model_info.sha}")
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

    prepared = []
    with ZipFile(archive_path) as archive:
        for job in plan:
            member = job["source_archive_path"]
            with Image.open(BytesIO(archive.read(member))) as raw:
                photo = ImageOps.exif_transpose(raw).convert("RGB")
                if min(photo.size) < 256:
                    raise RuntimeError(f"STOP: source too small {member} {photo.size}")
                # Contain avoids cropping hair or face; the same square framing is used for the edit pair.
                normalized = ImageOps.pad(photo, (SIZE, SIZE), method=Image.Resampling.LANCZOS,
                                           color=(245, 245, 245), centering=(0.5, 0.5))
            path = Path(job["source_path"])
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.exists():
                with Image.open(path) as existing:
                    if existing.convert("RGB").tobytes() != normalized.tobytes():
                        raise RuntimeError(f"STOP: existing normalized original differs: {path}")
            else:
                normalized.save(path)
            prepared.append((job, path))

    pipe = Flux2KleinPipeline.from_pretrained(MODEL, revision=MODEL_REVISION,
                                               torch_dtype=torch.float16, cache_dir=os.environ["HF_HUB_CACHE"])
    pipe.enable_model_cpu_offload(gpu_id=0)
    print("Base pipeline loaded with FP16 and CPU offload on GPU 0", flush=True)
    for job, source in prepared:
        key = job["sample_id"]
        primary = OUT / "generated" / f"{key}.png"
        retry = OUT / "generated" / f"{key}_r2.png"
        if args.retry:
            if not primary.exists() or retry.exists():
                raise RuntimeError(f"Retry requires exactly one previous output: {primary}")
            prior = json.loads(primary.with_suffix(".json").read_text(encoding="utf-8"))
            if (prior.get("sample_id") != key or prior.get("attempt") != 1
                    or prior.get("model") != MODEL or prior.get("model_revision") != MODEL_REVISION
                    or prior.get("source_revision") != REVISION or prior.get("split") != job["split"]
                    or prior.get("prompt") != job["prompt"] or prior.get("seed") != SEED
                    or prior.get("output_sha256") != hashlib.sha256(primary.read_bytes()).hexdigest()
                    or prior.get("source_sha256") != hashlib.sha256(source.read_bytes()).hexdigest()):
                raise RuntimeError(f"STOP: attempt-1 provenance mismatch for {key}")
            dest, attempt = retry, 2
        else:
            if primary.exists():
                prior = json.loads(primary.with_suffix(".json").read_text(encoding="utf-8"))
                if (prior.get("sample_id") != key or prior.get("attempt") != 1
                        or prior.get("model") != MODEL or prior.get("model_revision") != MODEL_REVISION
                        or prior.get("source_revision") != REVISION or prior.get("split") != job["split"]
                        or prior.get("prompt") != job["prompt"] or prior.get("seed") != SEED
                        or prior.get("output_sha256") != hashlib.sha256(primary.read_bytes()).hexdigest()
                        or prior.get("source_sha256") != hashlib.sha256(source.read_bytes()).hexdigest()):
                    raise RuntimeError(f"STOP: existing output lacks matching metadata: {primary}")
                print("Already generated:", primary, flush=True)
                continue
            dest, attempt = primary, 1
        prompt, seed = job["prompt"], job["seed"]
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
                "sample_id": key, "source_archive_path": job["source_archive_path"],
                "source_class": job["source_class"], "source_filename": job["source_filename"],
                "requested_class": job["requested_class"], "split": job["split"],
                "source": str(source), "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                "output": str(dest), "output_sha256": hashlib.sha256(dest.read_bytes()).hexdigest(),
                "model": MODEL, "model_revision": model_info.sha, "source_revision": info.sha,
                "generated_utc": datetime.now(timezone.utc).isoformat(),
                "prompt": prompt, "seed": seed, "attempt": attempt,
                "retry_change": {"field": "seed", "from": SEED, "to": seed} if attempt == 2 else None,
                "steps": STEPS, "guidance": GUIDANCE, "width": SIZE, "height": SIZE,
                "runtime_seconds": time.monotonic() - start,
                "peak_gpu_allocated_bytes": torch.cuda.max_memory_allocated(0),
                "qa_status": "PENDING_VISUAL_REVIEW",
            })
            render_review_sheet()
            print(f"{key} -> {job['requested_class']}: {dest} ({time.monotonic() - start:.1f}s)", flush=True)
        except Exception:
            import traceback
            (OUT / "generation_error.txt").write_text(traceback.format_exc(), encoding="utf-8")
            raise
    render_review_sheet()
    print("Generation finished. Review", OUT / "generation_review_sheet.jpg", "; no outputs accepted automatically.")


if __name__ == "__main__":
    main()
