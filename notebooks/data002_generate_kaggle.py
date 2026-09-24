"""Generate DATA-002 counterparts from the frozen manifest; never auto-accept.

The Supervisor runs --all on Kaggle. --plan is CPU-only and performs no download.
Completed, verified outputs are skipped on rerun. A reviewed REGENERATE permits
one seed-only retry; there is no third attempt.
"""

import argparse
from datetime import datetime, timezone
import faulthandler
import hashlib
from io import BytesIO
import json
import os
from pathlib import Path
import shutil
import sys
import time
from threading import Event, Thread
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from paired_dataset import contact_sheets, instruction, load_manifest, plan  # noqa: E402

DEFAULT_MANIFEST = ROOT / "docs/data/DATA-002-manifest.json"
DEFAULT_OUTPUT = Path("/kaggle/working/data002")
CACHE = Path("/tmp/data002-hf-cache")


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def save_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def manifest_hash(path: Path) -> str:
    actual = digest(path)
    checksum = path.with_suffix(".sha256")
    if not checksum.is_file() or checksum.read_text(encoding="utf-8").strip() != actual:
        raise RuntimeError("Frozen manifest SHA-256 sidecar is missing or differs")
    return actual


def require_retry_review(path: Path | None, sample_id: str) -> None:
    if path is None or not path.is_file():
        raise RuntimeError("Retry requires a review JSON with explicit REGENERATE")
    decision = json.loads(path.read_text(encoding="utf-8")).get(sample_id)
    if (not isinstance(decision, dict) or decision.get("status") != "REGENERATE"
            or decision.get("attempt") != 1 or not str(decision.get("notes", "")).strip()):
        raise RuntimeError(f"Retry requires REGENERATE of attempt 1 with notes: {sample_id}")


def check_existing(sample: dict, manifest: dict, folder: Path, attempt: int) -> bool:
    suffix = "_r2" if attempt == 2 else ""
    output = folder / f"generated{suffix}.png"
    sidecar = output.with_suffix(".json")
    if not output.exists() and not sidecar.exists():
        return False
    if not output.is_file() or not sidecar.is_file():
        raise RuntimeError(f"Partial result for {sample['sample_id']}; inspect before rerun")
    meta = json.loads(sidecar.read_text(encoding="utf-8"))
    expected = {"sample_id": sample["sample_id"], "source_member": sample["source_member"],
                "source_member_sha256": sample["source_sha256"],
                "source_style": sample["source_style"], "target_style": sample["target_style"],
                "split": sample["split"], "attempt": attempt,
                "seed": manifest["generation"]["seed"] + attempt - 1,
                "source_revision": manifest["source_revision"],
                "base_model_id": manifest["base_model_id"],
                "base_model_revision": manifest["base_model_revision"],
                "prompt": instruction(manifest["styles"], sample["target_style"]),
                "steps": manifest["generation"]["steps"],
                "guidance": manifest["generation"]["guidance"],
                "width": manifest["generation"]["width"],
                "height": manifest["generation"]["height"],
                "method": manifest["generation"]["method"],
                "generated_sha256": digest(output)}
    if any(meta.get(key) != value for key, value in expected.items()):
        raise RuntimeError(f"Existing result failed provenance/hash check: {output}")
    return True


def review_sheets(output: Path, manifest: dict) -> list[str]:
    rows = []
    for sample in manifest["samples"]:
        folder = output / "generated" / sample["sample_id"]
        original = folder / "original.png"
        if not original.is_file():
            continue
        for attempt, suffix in ((1, ""), (2, "_r2")):
            result = folder / f"generated{suffix}.png"
            if result.is_file():
                rows.append((original, result, f"{sample['sample_id']} | {sample['split']} | "
                             f"{sample['source_style']} -> {sample['target_style']} | attempt {attempt}"))
    return contact_sheets(rows, output / "review_sheets", "generation_review") if rows else []


def load_heartbeat(stop: Event, started: float, trace_path: Path) -> None:
    while not stop.wait(60):
        print(f"Base load still active after {time.monotonic() - started:.0f}s "
              f"(PID {os.getpid()}); traceback: {trace_path}", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--plan", action="store_true")
    group.add_argument("--all", action="store_true")
    group.add_argument("--retry", metavar="SAMPLE_ID")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--source-archive", type=Path, help="Optional pinned source ZIP already attached to Kaggle")
    parser.add_argument("--reviews", type=Path, help="Required for --retry")
    parser.add_argument("--approved-manifest-sha256", help="Explicit Project Lead approval of frozen manifest")
    args = parser.parse_args()
    frozen_hash = manifest_hash(args.manifest)
    manifest = load_manifest(args.manifest)
    if manifest["dataset_id"] != "DATA-002" or manifest.get("status") != "FROZEN_FOR_PROJECT_LEAD_REVIEW":
        raise RuntimeError("Expected the frozen DATA-002 selection manifest")
    jobs = plan(manifest)
    if args.plan:
        print(json.dumps({"manifest_sha256": frozen_hash, **jobs}, indent=2))
        return
    if args.approved_manifest_sha256 != frozen_hash:
        raise RuntimeError(f"Project Lead approval is required. Use --approved-manifest-sha256 {frozen_hash} only after review.")
    selected = manifest["samples"]
    if args.retry:
        selected = [sample for sample in selected if sample["sample_id"] == args.retry]
        if len(selected) != 1:
            raise RuntimeError("Retry sample ID is not in the frozen manifest")
        require_retry_review(args.reviews, args.retry)
    args.output.mkdir(parents=True, exist_ok=True)
    prior = args.output / "manifest.sha256"
    if prior.exists() and prior.read_text(encoding="utf-8").strip() != frozen_hash:
        raise RuntimeError("Output folder belongs to another manifest; refusing to mix runs")
    prior.write_text(frozen_hash + "\n", encoding="utf-8")

    os.environ["CUDA_VISIBLE_DEVICES"] = "0"
    os.environ["HF_HOME"] = str(CACHE)
    os.environ["HF_HUB_CACHE"] = str(CACHE / "hub")
    import torch
    from PIL import Image, ImageOps
    from huggingface_hub import hf_hub_download
    from diffusers import Flux2KleinPipeline

    if not torch.cuda.is_available():
        raise RuntimeError(f"CUDA is unavailable in {sys.executable}; select Kaggle T4 GPU")
    print("CUDA:", torch.__version__, torch.version.cuda, torch.cuda.get_device_name(0), flush=True)
    if shutil.disk_usage("/kaggle/working").free < 2 * 1024**3:
        raise RuntimeError("Less than 2 GiB free in /kaggle/working")
    if shutil.disk_usage("/tmp").free < 40 * 1024**3:
        raise RuntimeError("Less than 40 GiB scratch free for the Base model")
    if args.source_archive:
        archive_path = args.source_archive
    else:
        print("Downloading/reusing pinned source archive", flush=True)
        archive_path = Path(hf_hub_download(manifest["source_repository"],
            manifest["source_archive_filename"], repo_type="dataset",
            revision=manifest["source_revision"], cache_dir=str(CACHE / "hub")))
    if digest(archive_path) != manifest["source_archive_sha256"]:
        raise RuntimeError("Source archive hash differs from frozen DATA-002 selection")

    prepared = []
    with ZipFile(archive_path) as archive:
        for sample in selected:
            key = sample["sample_id"]
            raw = archive.read(sample["source_member"])
            if hashlib.sha256(raw).hexdigest() != sample["source_sha256"]:
                raise RuntimeError(f"Selected source hash differs: {key}")
            with Image.open(BytesIO(raw)) as source:
                photo = ImageOps.exif_transpose(source).convert("RGB")
            if photo.size != (sample["source_width"], sample["source_height"]):
                raise RuntimeError(f"Selected source dimensions differ: {key}")
            photo = ImageOps.pad(photo, (512, 512), method=Image.Resampling.LANCZOS,
                                 color=(245, 245, 245), centering=(0.5, 0.5))
            folder = args.output / "generated" / key
            folder.mkdir(parents=True, exist_ok=True)
            original = folder / "original.png"
            if original.exists():
                with Image.open(original) as existing:
                    if existing.convert("RGB").tobytes() != photo.tobytes():
                        raise RuntimeError(f"Existing normalized original differs: {key}")
            else:
                photo.save(original)
            attempt = 2 if args.retry else 1
            if attempt == 2 and not check_existing(sample, manifest, folder, 1):
                raise RuntimeError(f"Retry requires verified attempt 1: {key}")
            if check_existing(sample, manifest, folder, attempt):
                print("Already generated:", key, "attempt", attempt, flush=True)
                continue
            prepared.append((sample, original, folder, attempt))
    if not prepared:
        print("All selected jobs already have verified outputs.", flush=True)
        return

    print(f"Loading pinned Base for {len(prepared)} remaining generation jobs", flush=True)
    started = time.monotonic()
    trace_path = args.output / "base_load_trace.log"
    stop_heartbeat = Event()
    Thread(target=load_heartbeat, args=(stop_heartbeat, started, trace_path), daemon=True).start()
    with trace_path.open("a", encoding="utf-8") as trace:
        trace.write(f"Base load started {datetime.now(timezone.utc).isoformat()} "
                    f"PID {os.getpid()}\n")
        trace.flush()
        faulthandler.dump_traceback_later(180, repeat=True, file=trace)
        try:
            pipe = Flux2KleinPipeline.from_pretrained(
                manifest["base_model_id"], revision=manifest["base_model_revision"],
                torch_dtype=torch.float16, cache_dir=str(CACHE / "hub"))
            print(f"Base weights materialized after {time.monotonic() - started:.0f}s; "
                  "enabling CPU offload", flush=True)
            pipe.enable_model_cpu_offload(gpu_id=0)
        finally:
            stop_heartbeat.set()
            faulthandler.cancel_dump_traceback_later()
    print("Base ready with FP16 + CPU offload on cuda:0", flush=True)
    for index, (sample, original, folder, attempt) in enumerate(prepared):
        key = sample["sample_id"]
        suffix = "_r2" if attempt == 2 else ""
        result_path = folder / f"generated{suffix}.png"
        sidecar = result_path.with_suffix(".json")
        prompt = instruction(manifest["styles"], sample["target_style"])
        seed = manifest["generation"]["seed"] + attempt - 1
        torch.cuda.reset_peak_memory_stats(0)
        start = time.monotonic()
        try:
            with Image.open(original) as source:
                result = pipe(prompt=prompt, image=source.convert("RGB"),
                              width=manifest["generation"]["width"],
                              height=manifest["generation"]["height"],
                              num_inference_steps=manifest["generation"]["steps"],
                              guidance_scale=manifest["generation"]["guidance"],
                              generator=torch.Generator(device="cuda").manual_seed(seed)).images[0]
            result.convert("RGB").save(result_path)
            save_json(sidecar, {
                "sample_id": key, "identity_group_id": sample["identity_group_id"],
                "source_path": sample["source_path"], "source_member": sample["source_member"],
                "source_member_sha256": sample["source_sha256"],
                "source_style": sample["source_style"], "target_style": sample["target_style"],
                "split": sample["split"], "attempt": attempt,
                "method": manifest["generation"]["method"],
                "prompt": prompt, "seed": seed,
                "steps": manifest["generation"]["steps"],
                "guidance": manifest["generation"]["guidance"],
                "width": result.width, "height": result.height,
                "source_revision": manifest["source_revision"],
                "base_model_id": manifest["base_model_id"],
                "base_model_revision": manifest["base_model_revision"],
                "original_sha256": digest(original),
                "generated_sha256": digest(result_path),
                "runtime_seconds": round(time.monotonic() - start, 2),
                "peak_gpu_allocated_bytes": torch.cuda.max_memory_allocated(0),
                "generated_utc": datetime.now(timezone.utc).isoformat(),
                "qa_status": "PENDING_VISUAL_REVIEW",
                "retry_change": {"field": "seed", "from": manifest["generation"]["seed"],
                                 "to": seed} if attempt == 2 else None,
            })
            print(f"{key} {sample['source_style']} -> {sample['target_style']} "
                  f"attempt {attempt}: {result_path} ({time.monotonic() - start:.1f}s)", flush=True)
        except Exception:
            import traceback
            (args.output / "generation_error.txt").write_text(traceback.format_exc(), encoding="utf-8")
            raise
        if len(prepared) <= 3 or index % 10 == 0:
            review_sheets(args.output, manifest)
    sheets = review_sheets(args.output, manifest)
    print("Generation finished; no outputs accepted automatically. Review sheets:", sheets, flush=True)


if __name__ == "__main__":
    main()
