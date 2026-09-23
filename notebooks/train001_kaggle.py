"""TRAIN-001 handoff: validate DATA-001, write BF16 config, run only on --execute.

No installation or model download occurs during --prepare. Evaluation requires
an existing checkpoint and never trains. Designed for the Supervisor's Kaggle
CUDA interpreter and the EXP-001-pinned AI Toolkit checkout.
"""

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time


TOOLKIT_COMMIT = "a8dfcf7d7e2b38ccc7b2fb68ece9c6358e61e7a7"
MODEL = "black-forest-labs/FLUX.2-klein-base-4B"
MODEL_REV = "a3b4f4849157f664bdbc776fd7453c2783562f4d"
EXPECTED = {"train": 48, "val": 12}
STYLE_COUNTS = {"train": 16, "val": 4}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def validate_dataset(dataset):
    from PIL import Image
    if not (dataset / "reports" / "qa.json").is_file():
        raise RuntimeError(f"STOP: DATA-001 QA report missing under {dataset}")
    qa = json.loads((dataset / "reports" / "qa.json").read_text(encoding="utf-8"))
    manifest = json.loads((dataset / "manifests" / "pairs.json").read_text(encoding="utf-8"))
    reviews = json.loads((dataset / "manifests" / "reviews.json").read_text(encoding="utf-8"))
    if len(manifest) != 60 or len(reviews) != 30 or any(r.get("status") != "ACCEPT" or not r.get("notes") for r in reviews.values()):
        raise RuntimeError("STOP: DATA-001 lacks 60 pairs and 30 explicit ACCEPT reviews")
    if qa.get("directional_pairs") != 60 or qa.get("identity_groups") != {"train": 24, "val": 6}:
        raise RuntimeError("STOP: DATA-001 QA report does not certify expected pair/identity counts")
    if qa.get("split_leakage") != "NONE" or qa.get("caption_reference_target_alignment") != "PASS":
        raise RuntimeError("STOP: DATA-001 QA report failed split or pairing")
    groups = {"train": set(), "val": set()}
    distribution = Counter()
    for row in manifest:
        split = row["split"]
        if split not in EXPECTED or row["identity_group"] not in reviews:
            raise RuntimeError("STOP: unknown split or review identity")
        groups[split].add(row["identity_group"])
        distribution[(split, row["requested_style"])] += 1
        stem = Path(row["target"]).stem
        if Path(row["reference"]).stem != stem:
            raise RuntimeError("STOP: pair filename mismatch")
        for key in ("reference", "target"):
            path = dataset / row[key]
            if not path.is_file():
                raise RuntimeError(f"STOP: missing {key}: {path}")
            with Image.open(path) as image:
                if image.mode != "RGB" or image.size != (512, 512):
                    raise RuntimeError(f"STOP: invalid image: {path}")
        caption = dataset / split / "target" / f"{stem}.txt"
        if caption.read_text(encoding="utf-8").strip() != row["caption"]:
            raise RuntimeError(f"STOP: caption mismatch: {caption}")
    if groups["train"] & groups["val"] or len(groups["train"]) != 24 or len(groups["val"]) != 6:
        raise RuntimeError("STOP: identity group split invalid")
    for split, count in EXPECTED.items():
        if sum(r["split"] == split for r in manifest) != count:
            raise RuntimeError(f"STOP: wrong {split} count")
        for style in ("CrewCut", "BobHair", "LayeredHair"):
            if distribution[(split, style)] != STYLE_COUNTS[split]:
                raise RuntimeError(f"STOP: wrong {split}/{style} distribution")
    return {"qa_sha256": digest(dataset / "reports" / "qa.json"),
            "manifest_sha256": digest(dataset / "manifests" / "pairs.json"),
            "reviews_sha256": digest(dataset / "manifests" / "reviews.json"),
            "identity_counts": {key: len(value) for key, value in groups.items()},
            "pair_counts": EXPECTED}


def config_text(dataset, out, steps):
    # EXP-001 BF16-confirmed configuration; only duration/save interval differ.
    checkpoint_interval = 125 if steps == 250 else 250
    return f'''job: "extension"
config:
  name: "train001_{steps}step"
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
        save_every: {checkpoint_interval}
        max_step_saves_to_keep: 2
      datasets:
        - folder_path: "{(dataset / 'train' / 'target').as_posix()}"
          control_path: "{(dataset / 'train' / 'reference').as_posix()}"
          caption_ext: "txt"
          resolution: [512]
      train:
        batch_size: 1
        steps: {steps}
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
  name: "train001_{steps}step"
  version: "1.0"
'''


def preflight_runtime(toolkit):
    os.environ["CUDA_VISIBLE_DEVICES"] = "0"
    os.environ["HF_HOME"] = "/tmp/hf-cache"
    os.environ["HF_HUB_CACHE"] = "/tmp/hf-cache/hub"
    import torch
    if not torch.cuda.is_available():
        raise RuntimeError(f"STOP: {sys.executable} has no CUDA")
    if shutil.disk_usage("/tmp").free < 30 * 1024**3:
        raise RuntimeError("STOP: insufficient /tmp model-cache headroom")
    sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=toolkit, capture_output=True, text=True, check=True).stdout.strip()
    if sha != TOOLKIT_COMMIT:
        raise RuntimeError(f"STOP: AI Toolkit commit is {sha}; expected {TOOLKIT_COMMIT}")
    from huggingface_hub import HfApi
    model_sha = HfApi().model_info(MODEL, revision=MODEL_REV).sha
    if model_sha != MODEL_REV:
        raise RuntimeError(f"STOP: Base model revision is {model_sha}; expected {MODEL_REV}")
    return {"python": sys.version, "torch": torch.__version__, "cuda": torch.version.cuda,
            "gpu": torch.cuda.get_device_name(0), "ai_toolkit_commit": sha,
            "base_model_revision": model_sha, "tmp_free_bytes": shutil.disk_usage("/tmp").free,
            "timestamp_utc": datetime.now(timezone.utc).isoformat()}


def run_training(out, toolkit, steps):
    from exp001_flux2_klein_kaggle_smoke import GpuMemorySampler
    config = out / "train_config.yaml"
    command = [sys.executable, "run.py", str(config)]
    save_json(out / "command.json", {"command": command, "cwd": str(toolkit), "config_sha256": digest(config)})
    loss_rows = []
    start = time.monotonic()
    stop_reason = None
    with GpuMemorySampler() as sampler:
        with (out / "train.log").open("w", encoding="utf-8") as log:
            proc = subprocess.Popen(command, cwd=toolkit, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                    text=True, bufsize=1)
            assert proc.stdout is not None
            for line in proc.stdout:
                log.write(line)
                log.flush()
                print(line, end="", flush=True)
                if re.search(r"(?:loss\s+is|loss\s*:)\s*[+-]?(?:nan|inf)\b", line, re.I):
                    stop_reason = "non-finite training loss"
                    proc.terminate()
                    break
                for m in re.finditer(rf"\b(\d+)/{steps}\b[^\r\n]*?loss:\s*([+-]?\d+(?:\.\d+)?e[+-]?\d+)", line, re.I):
                    loss_rows.append({"step": int(m.group(1)), "loss": float(m.group(2)), "elapsed_s": time.monotonic() - start})
            try:
                code = proc.wait(timeout=30 if stop_reason else None)
            except subprocess.TimeoutExpired:
                proc.kill()
                code = proc.wait()
    summary = {"exit_code": code, "elapsed_seconds_including_load": time.monotonic() - start,
               "whole_gpu_peak_mib_observed": sampler.peak_mib, "stop_reason": stop_reason,
               "highest_loss_step": max((row["step"] for row in loss_rows), default=None), "losses": loss_rows}
    if len(loss_rows) >= 10:
        recent = sorted({row["step"]: row for row in loss_rows}.values(), key=lambda x: x["step"])[-10:]
        summary["seconds_per_step_recent"] = ((recent[-1]["elapsed_s"] - recent[0]["elapsed_s"])
                                               / (recent[-1]["step"] - recent[0]["step"]))
    save_json(out / "training_summary.json", summary)
    if stop_reason or code != 0 or summary["highest_loss_step"] != steps:
        raise RuntimeError("STOP: training failed or did not log the final step; inspect train.log")
    if not list((out / "checkpoints").rglob("*.safetensors")):
        raise RuntimeError("STOP: no .safetensors checkpoint found")
    return summary


def evaluate(dataset, out, checkpoint):
    import torch
    from PIL import Image, ImageDraw, ImageOps
    from diffusers import Flux2KleinPipeline
    preflight = out / "runtime.json"
    if not preflight.exists():
        raise RuntimeError("STOP: run --prepare before evaluation")
    pipe = Flux2KleinPipeline.from_pretrained(MODEL, revision=MODEL_REV, torch_dtype=torch.float16,
                                              cache_dir="/tmp/hf-cache/hub")
    pipe.enable_model_cpu_offload(gpu_id=0)
    rows = [r for r in json.loads((dataset / "manifests" / "pairs.json").read_text(encoding="utf-8")) if r["split"] == "val"]
    if len(rows) != 12:
        raise RuntimeError("STOP: expected 12 held-out validation pairs")
    eval_dir = out / "evaluation"
    eval_dir.mkdir(parents=True, exist_ok=True)
    records = {"base": [], "adapter": []}
    for mode in ("base", "adapter"):
        if mode == "adapter":
            pipe.load_lora_weights(str(checkpoint.parent), weight_name=checkpoint.name)
        (eval_dir / mode).mkdir(exist_ok=True)
        for row in rows:
            stem = Path(row["target"]).stem
            dest = eval_dir / mode / f"{stem}.png"
            if dest.exists():
                raise RuntimeError(f"STOP: refusing to overwrite evaluation output {dest}")
            with Image.open(dataset / row["reference"]) as im:
                source = im.convert("RGB")
            start = time.monotonic()
            torch.cuda.reset_peak_memory_stats(0)
            result = pipe(prompt=row["caption"], image=source, width=512, height=512,
                          num_inference_steps=20, guidance_scale=4.0,
                          generator=torch.Generator(device="cuda").manual_seed(1977)).images[0]
            result.save(dest)
            records[mode].append({"pair": stem, "identity_group": row["identity_group"],
                                  "requested_style": row["requested_style"], "prompt": row["caption"],
                                  "seed": 1977, "steps": 20, "guidance": 4.0,
                                  "checkpoint_sha256": digest(checkpoint) if mode == "adapter" else None,
                                  "output": str(dest), "output_sha256": digest(dest),
                                  "runtime_seconds": time.monotonic() - start,
                                  "peak_gpu_allocated_bytes": torch.cuda.max_memory_allocated(0),
                                  "review_status": "PENDING"})
    sheet = Image.new("RGB", (4 * 256, len(rows) * 300), "white")
    draw = ImageDraw.Draw(sheet)
    for i, row in enumerate(rows):
        stem = Path(row["target"]).stem
        for j, path in enumerate((dataset / row["reference"], eval_dir / "base" / f"{stem}.png",
                                  eval_dir / "adapter" / f"{stem}.png", dataset / row["target"])):
            with Image.open(path) as im:
                sheet.paste(ImageOps.contain(im.convert("RGB"), (256, 256)), (j * 256, i * 300))
        draw.text((4, i * 300 + 261), f"{stem} / {row['requested_style']} / PENDING HUMAN EVALUATION", fill="black")
    sheet.save(eval_dir / "reference_base_adapter_target.jpg", quality=90)
    save_json(eval_dir / "metadata.json", {"model": MODEL, "model_revision": MODEL_REV,
                                           "checkpoint": str(checkpoint), "pairs": records,
                                           "column_order": ["reference", "base_output", "adapter_output", "target"]})


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--phase", choices=("prepare", "execute", "evaluate"), required=True)
    p.add_argument("--dataset", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--toolkit", type=Path, default=Path("/tmp/exp001-ai-toolkit"))
    p.add_argument("--steps", type=int, choices=(250, 500), required=True)
    p.add_argument("--checkpoint", type=Path)
    args = p.parse_args()
    if args.phase == "evaluate" and not args.checkpoint:
        raise RuntimeError("STOP: --evaluate requires --checkpoint")
    evidence = validate_dataset(args.dataset)
    if args.phase == "prepare":
        args.out.mkdir(parents=True, exist_ok=True)
        config = config_text(args.dataset.resolve(), args.out.resolve(), args.steps)
        path = args.out / "train_config.yaml"
        if path.exists() and path.read_text(encoding="utf-8") != config:
            raise RuntimeError("STOP: existing TRAIN-001 config differs; do not overwrite")
        path.write_text(config, encoding="utf-8")
        save_json(args.out / "dataset_evidence.json", evidence)
        save_json(args.out / "runtime.json", preflight_runtime(args.toolkit))
        print(f"PREPARED {path}; training has not started")
        return
    if json.loads((args.out / "dataset_evidence.json").read_text(encoding="utf-8")) != evidence:
        raise RuntimeError("STOP: DATA-001 inputs changed after TRAIN-001 preparation")
    if args.phase == "execute":
        if (args.out / "train.log").exists():
            raise RuntimeError("STOP: existing train.log; do not overwrite a previous run")
        preflight_runtime(args.toolkit)
        run_training(args.out, args.toolkit, args.steps)
    else:
        if not args.checkpoint.is_file() or args.checkpoint.suffix != ".safetensors":
            raise RuntimeError("STOP: checkpoint missing or wrong format")
        summary_path = args.out / "training_summary.json"
        if not summary_path.exists():
            raise RuntimeError("STOP: successful training summary required before evaluation")
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        if summary.get("exit_code") != 0 or summary.get("highest_loss_step") != args.steps or summary.get("stop_reason"):
            raise RuntimeError("STOP: training summary does not verify completed finite run")
        preflight_runtime(args.toolkit)
        evaluate(args.dataset, args.out, args.checkpoint)


if __name__ == "__main__":
    main()
