"""Prepare and execute one isolated 500-step DATA-002 hairstyle Edit-LoRA run.

The Supervisor runs --phase execute on Kaggle. This module never modifies TRAIN-001.
"""

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import shutil

from PIL import Image, ImageDraw, ImageOps

from train001_kaggle import (MODEL, MODEL_REV, digest, preflight_runtime,
                             run_training, save_json)


FROZEN_MANIFEST_SHA256 = "25a3200c9a79be85ce19f690ba81f564d57d55d86d36e6383b0cacd1188ec5ab"
STEPS = 500
JOB_NAME = "train002_500step"


def validate_dataset(dataset: Path, frozen_manifest: Path) -> dict:
    qa_path = dataset / "reports" / "qa.json"
    audit_path = dataset / "reports" / "generation_audit.json"
    pairs_path = dataset / "manifests" / "pairs.json"
    selection_path = dataset / "manifests" / "selection.json"
    reviews_path = dataset / "manifests" / "reviews.json"
    if not all(path.is_file() for path in (qa_path, audit_path, pairs_path, selection_path, reviews_path)):
        raise RuntimeError("STOP: finalized DATA-002 reports and manifests are incomplete")
    if digest(frozen_manifest) != FROZEN_MANIFEST_SHA256:
        raise RuntimeError("STOP: repository DATA-002 manifest differs from approved frozen SHA-256")
    qa = json.loads(qa_path.read_text(encoding="utf-8"))
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    rows = json.loads(pairs_path.read_text(encoding="utf-8"))
    selection = json.loads(selection_path.read_text(encoding="utf-8"))
    reviews = json.loads(reviews_path.read_text(encoding="utf-8"))
    if selection != json.loads(frozen_manifest.read_text(encoding="utf-8")):
        raise RuntimeError("STOP: dataset selection differs from the frozen DATA-002 manifest")
    if (qa.get("dataset_id") != "DATA-002" or qa.get("source_manifest_sha256") != FROZEN_MANIFEST_SHA256
            or qa.get("review_mode") != "automated_unreviewed" or qa.get("visual_qa", "").startswith("NOT PERFORMED") is False
            or qa.get("explicit_accepts") != 0 or qa.get("split_leakage") is not False
            or audit.get("manifest_sha256") != FROZEN_MANIFEST_SHA256
            or audit.get("review_mode") != "automated_unreviewed"
            or audit.get("severely_underrepresented")
            or audit.get("exact_hash_split_leakage")
            or audit.get("unexpected_sample_directories")
            or qa.get("identity_counts") != audit.get("actual_identity_counts")
            or qa.get("pair_counts") != audit.get("actual_pair_counts")
            or qa.get("target_distribution") != audit.get("actual_target_distribution")):
        raise RuntimeError("STOP: DATA-002 automated acceptance provenance or structural QA failed")
    expected_pairs = qa.get("pair_counts")
    if (not isinstance(expected_pairs, dict) or set(expected_pairs) != {"train", "val"}
            or len(rows) != sum(expected_pairs.values())
            or qa.get("automated_accepts") != audit.get("valid_generation_count")
            or len(rows) != 2 * audit.get("valid_generation_count", -1)):
        raise RuntimeError("STOP: DATA-002 pair counts differ from audited generated identities")
    styles = set(selection["styles"])
    if len(styles) != 10:
        raise RuntimeError("STOP: DATA-002 class definitions differ from the frozen ten-style manifest")
    valid_ids = set(audit["valid_sample_ids"])
    if set(reviews) != valid_ids or any(value.get("status") != "TECHNICAL_ACCEPT"
                                         or value.get("review_mode") != "automated_unreviewed"
                                         for value in reviews.values()):
        raise RuntimeError("STOP: automated review records do not match audited valid identities")
    groups = defaultdict(list)
    counts = Counter()
    stems = set()
    for row in rows:
        sample_id, split, style = row["sample_id"], row["split"], row["requested_style"]
        if sample_id not in valid_ids or split not in {"train", "val"} or style not in styles:
            raise RuntimeError(f"STOP: invalid pair provenance: {sample_id}")
        groups[sample_id].append(row)
        counts[f"{split}/{style}"] += 1
        reference = dataset / row["reference"]
        target = dataset / row["target"]
        caption = target.with_suffix(".txt")
        stem = (split, reference.stem)
        if (stem in stems or reference.stem != target.stem or target.stem != caption.stem
                or not reference.is_file() or not target.is_file() or not caption.is_file()
                or caption.read_text(encoding="utf-8").strip() != row["caption"]):
            raise RuntimeError(f"STOP: pair/caption alignment failed: {sample_id}")
        stems.add(stem)
        for path in (reference, target):
            with Image.open(path) as image:
                image.verify()
            with Image.open(path) as image:
                if image.mode != "RGB" or image.size != (512, 512):
                    raise RuntimeError(f"STOP: invalid DATA-002 image: {path}")
    for sample_id, directions in groups.items():
        if (len(directions) != 2 or {row["direction"] for row in directions} != {"to_alternate", "to_original"}
                or len({row["split"] for row in directions}) != 1):
            raise RuntimeError(f"STOP: reverse directions or split differ: {sample_id}")
    if dict(sorted(counts.items())) != qa.get("target_distribution"):
        raise RuntimeError("STOP: target class counts differ from DATA-002 QA")
    for split in ("train", "val"):
        if sum(row["split"] == split for row in rows) != expected_pairs[split]:
            raise RuntimeError(f"STOP: {split} pair count differs from QA")
    return {"dataset_id": "DATA-002", "review_mode": "automated_unreviewed",
            "frozen_manifest_sha256": FROZEN_MANIFEST_SHA256,
            "qa_sha256": digest(qa_path), "audit_sha256": digest(audit_path),
            "pairs_sha256": digest(pairs_path), "selection_sha256": digest(selection_path),
            "identity_counts": qa["identity_counts"], "pair_counts": expected_pairs,
            "target_distribution": qa["target_distribution"],
            "style_ids": sorted(styles), "excluded_generations": audit["issues"]}


def config_text(dataset: Path, out: Path) -> str:
    return f'''job: "extension"
config:
  name: "{JOB_NAME}"
  process:
    - type: "diffusion_trainer"
      training_folder: "{(out / 'checkpoints').as_posix()}"
      device: "cuda:0"
      performance_log_every: 5
      network:
        type: "lora"
        linear: 16
        linear_alpha: 16
        conv: 8
        conv_alpha: 8
      save:
        dtype: "float16"
        save_every: 250
        max_step_saves_to_keep: 2
      datasets:
        - folder_path: "{(dataset / 'train' / 'target').as_posix()}"
          control_path: "{(dataset / 'train' / 'reference').as_posix()}"
          caption_ext: "txt"
          resolution: [512]
      train:
        batch_size: 1
        steps: {STEPS}
        lr: 0.0001
        optimizer: "adamw8bit"
        noise_scheduler: "flowmatch"
        gradient_checkpointing: true
        dtype: "bf16"
        train_unet: true
        train_text_encoder: false
        timestep_type: "weighted"
        content_or_style: "balanced"
      model:
        arch: "flux2_klein_4b"
        name_or_path: "{MODEL}"
        quantize: true
        low_vram: true
meta:
  name: "{JOB_NAME}"
  version: "1.0"
'''


def package_adapter(out: Path, dataset_evidence: dict, summary: dict, runtime: dict) -> dict:
    from safetensors import safe_open

    checkpoint = out / "checkpoints" / JOB_NAME / f"{JOB_NAME}.safetensors"
    if not checkpoint.is_file() or not summary.get("success") or summary.get("highest_loss_step") != STEPS:
        raise RuntimeError("STOP: final TRAIN-002 checkpoint or successful step evidence is missing")
    with safe_open(str(checkpoint), framework="pt", device="cpu") as data:
        raw = data.metadata() or {}
        training_info = json.loads(raw.get("training_info", "{}"))
        if training_info.get("step") != STEPS or not any("lora" in key.lower() for key in data.keys()):
            raise RuntimeError("STOP: checkpoint metadata does not prove the final LoRA step")
    bundle = out / "adapter"
    if bundle.exists() and any(bundle.iterdir()):
        raise RuntimeError("STOP: TRAIN-002 adapter bundle already exists; refusing to overwrite")
    bundle.mkdir(parents=True, exist_ok=True)
    saved = bundle / "adapter.safetensors"
    shutil.copyfile(checkpoint, saved)
    metadata = {
        "schema_version": 1, "artifact_type": "project_trained_lora", "experiment": "TRAIN-002",
        "training_steps": STEPS, "dataset_version": "DATA-002",
        "dataset_manifest_sha256": FROZEN_MANIFEST_SHA256,
        "dataset_pair_manifest_sha256": dataset_evidence["pairs_sha256"],
        "dataset_qa_sha256": dataset_evidence["qa_sha256"],
        "review_mode": "automated_unreviewed", "visual_qa": "NOT PERFORMED",
        "supported_style_ids": dataset_evidence["style_ids"],
        "dataset_identity_counts": dataset_evidence["identity_counts"],
        "dataset_pair_counts": dataset_evidence["pair_counts"],
        "dataset_target_distribution": dataset_evidence["target_distribution"],
        "base_model_id": MODEL, "base_model_revision": MODEL_REV,
        "ai_toolkit_commit": runtime["ai_toolkit_commit"],
        "training_config_sha256": digest(out / "train_config.yaml"),
        "lora": {"linear": 16, "linear_alpha": 16, "conv": 8, "conv_alpha": 8},
        "training": {"dtype": "bf16", "save_dtype": "float16", "steps": STEPS,
                     "optimizer": "adamw8bit", "lr": 0.0001, "noise_scheduler": "flowmatch",
                     "batch_size": 1, "resolution": 512, "gradient_checkpointing": True,
                     "quantize": True, "low_vram": True},
        "checkpoint_file": "adapter.safetensors", "checkpoint_bytes": saved.stat().st_size,
        "checkpoint_sha256": digest(saved),
        "status": "UNVALIDATED_FOR_RUNTIME",
    }
    save_json(bundle / "metadata.json", metadata)
    return metadata


def evaluate(dataset: Path, out: Path, evidence: dict) -> None:
    """One held-out direction per style, same settings for Base and adapter."""
    import time
    import torch
    from diffusers import Flux2KleinPipeline

    summary = json.loads((out / "training_summary.json").read_text(encoding="utf-8"))
    adapter = out / "adapter" / "adapter.safetensors"
    adapter_meta = json.loads((out / "adapter" / "metadata.json").read_text(encoding="utf-8"))
    if (not summary.get("success") or summary.get("highest_loss_step") != STEPS
            or not adapter.is_file() or adapter_meta.get("checkpoint_sha256") != digest(adapter)):
        raise RuntimeError("STOP: successful TRAIN-002 bundle is required before evaluation")
    if not torch.cuda.is_available():
        raise RuntimeError("STOP: evaluation requires the Kaggle GPU")
    rows = json.loads((dataset / "manifests" / "pairs.json").read_text(encoding="utf-8"))
    chosen = {}
    for row in rows:
        if row["split"] == "val" and row["requested_style"] not in chosen:
            chosen[row["requested_style"]] = row
    if set(chosen) != set(evidence["style_ids"]):
        raise RuntimeError("STOP: at least one DATA-002 style lacks a held-out direction")
    folder = out / "evaluation"
    if folder.exists() and any(folder.iterdir()):
        raise RuntimeError("STOP: evaluation output exists; refusing to overwrite")
    folder.mkdir(parents=True, exist_ok=True)
    pipe = Flux2KleinPipeline.from_pretrained(MODEL, revision=MODEL_REV,
        torch_dtype=torch.float16, cache_dir="/tmp/hf-cache/hub")
    pipe.enable_model_cpu_offload(gpu_id=0)
    records = []
    for mode in ("base", "adapter"):
        if mode == "adapter":
            pipe.load_lora_weights(str(adapter.parent), weight_name=adapter.name)
        (folder / mode).mkdir()
        for style in sorted(chosen):
            row = chosen[style]
            with Image.open(dataset / row["reference"]) as image:
                source = image.convert("RGB")
            torch.cuda.reset_peak_memory_stats(0)
            started = time.monotonic()
            result = pipe(prompt=row["caption"], image=source, width=512, height=512,
                          num_inference_steps=20, guidance_scale=4.0,
                          generator=torch.Generator(device="cuda").manual_seed(1977)).images[0]
            path = folder / mode / f"{style}.png"
            result.convert("RGB").save(path)
            records.append({"mode": mode, "style_id": style, "sample_id": row["sample_id"],
                            "reference": row["reference"], "target": row["target"],
                            "prompt": row["caption"], "seed": 1977, "steps": 20, "guidance": 4.0,
                            "runtime_seconds": time.monotonic() - started,
                            "peak_gpu_allocated_bytes": torch.cuda.max_memory_allocated(0),
                            "output": str(path), "output_sha256": digest(path)})
    sheet = Image.new("RGB", (4 * 256, len(chosen) * 280), "white")
    draw = ImageDraw.Draw(sheet)
    for index, style in enumerate(sorted(chosen)):
        row = chosen[style]
        paths = (dataset / row["reference"], folder / "base" / f"{style}.png",
                 folder / "adapter" / f"{style}.png", dataset / row["target"])
        for column, path in enumerate(paths):
            with Image.open(path) as image:
                sheet.paste(ImageOps.contain(image.convert("RGB"), (250, 250)),
                            (column * 256, index * 280))
        draw.text((4, index * 280 + 254), f"{style} | source / Base / TRAIN-002 / target", fill="black")
    sheet.save(folder / "reference_base_adapter_target.jpg", quality=90)
    save_json(folder / "metadata.json", {"dataset_id": "DATA-002", "checkpoint_sha256": digest(adapter),
                                         "review_mode": "automated_unreviewed", "records": records,
                                         "column_order": ["reference", "base", "adapter", "target"],
                                         "visual_review": "PENDING"})


def resume_status(out: Path) -> dict:
    """Inspect retained state without claiming an unverified optimizer resume."""
    from safetensors import safe_open

    states = []
    for path in sorted((out / "checkpoints" / JOB_NAME).glob("*.safetensors")):
        with safe_open(str(path), framework="pt", device="cpu") as data:
            step = json.loads((data.metadata() or {}).get("training_info", "{}")).get("step")
        states.append({"path": str(path), "step": step, "bytes": path.stat().st_size,
                       "sha256": digest(path)})
    optimizer = out / "checkpoints" / JOB_NAME / "optimizer.pt"
    return {"job": JOB_NAME, "target_step": STEPS, "checkpoints": states,
            "optimizer_state_present": optimizer.is_file(),
            "optimizer_restore_verified": False,
            "next_action": "Preserve the full run directory; verify the pinned trainer's resume behavior before relaunching"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=("bootstrap", "prepare", "execute", "evaluate", "resume-check"), required=True)
    parser.add_argument("--dataset", type=Path, default=Path("/kaggle/working/data002/final"))
    parser.add_argument("--out", type=Path, default=Path("/kaggle/working/train002_500"))
    parser.add_argument("--toolkit", type=Path, default=Path("/tmp/exp001-ai-toolkit"))
    args = parser.parse_args()
    if args.phase == "bootstrap":
        from exp001_flux2_klein_kaggle_smoke import OUT as SETUP_OUT, install_toolkit
        SETUP_OUT.mkdir(parents=True, exist_ok=True)
        install_toolkit()
        print("TRAIN-002 trainer dependencies ready; restart the Kaggle kernel if packages changed")
        return
    if args.phase == "resume-check":
        print(json.dumps(resume_status(args.out), indent=2))
        return
    frozen = Path(__file__).resolve().parents[1] / "docs/data/DATA-002-manifest.json"
    evidence = validate_dataset(args.dataset, frozen)
    if args.phase == "prepare":
        args.out.mkdir(parents=True, exist_ok=True)
        config = config_text(args.dataset.resolve(), args.out.resolve())
        path = args.out / "train_config.yaml"
        if path.exists() and path.read_text(encoding="utf-8") != config:
            raise RuntimeError("STOP: existing TRAIN-002 config differs; refusing to overwrite")
        path.write_text(config, encoding="utf-8")
        existing = args.out / "dataset_evidence.json"
        if existing.exists() and json.loads(existing.read_text(encoding="utf-8")) != evidence:
            raise RuntimeError("STOP: DATA-002 evidence changed since preparation")
        save_json(existing, evidence)
        save_json(args.out / "runtime.json", preflight_runtime(args.toolkit))
        print(f"PREPARED {path}; TRAIN-002 has not started")
        return
    expected = args.out / "dataset_evidence.json"
    if not expected.is_file() or json.loads(expected.read_text(encoding="utf-8")) != evidence:
        raise RuntimeError("STOP: DATA-002 dataset changed after TRAIN-002 preparation")
    if args.phase == "evaluate":
        evaluate(args.dataset, args.out, evidence)
        print(f"EVALUATION READY: {args.out / 'evaluation' / 'reference_base_adapter_target.jpg'}")
        return
    if (args.out / "train.log").exists() or (args.out / "checkpoints").exists():
        raise RuntimeError("STOP: TRAIN-002 run already started; do not overwrite checkpoints or logs")
    runtime = preflight_runtime(args.toolkit)
    if runtime["ai_toolkit_commit"] != json.loads((args.out / "runtime.json").read_text())["ai_toolkit_commit"]:
        raise RuntimeError("STOP: AI Toolkit changed since preparation")
    summary = run_training(args.out, args.toolkit, STEPS)
    package_adapter(args.out, evidence, summary, runtime)
    print(f"TRAIN-002 COMPLETE: {args.out / 'adapter' / 'adapter.safetensors'}")


if __name__ == "__main__":
    main()
