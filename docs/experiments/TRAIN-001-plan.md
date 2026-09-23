# TRAIN-001 BF16 hairstyle Edit-LoRA handoff

**Prepared for the first 250-step run after DATA-001 finalization.** Real hairstyle training requires DATA-001 `reports/qa.json`, 30 explicit ACCEPT reviews, 60 validated directional pairs, and human inspection of both final contact sheets. The active DATA-001 path is V1/global generation and practical visual review. The EXP-001 T4 smoke test verified finite BF16 training for 20 steps at approximately 32.808 seconds/step and 13,531 MiB peak, not long-run stability or hairstyle quality. Any later 500-step continuation must use the **same** run; the script now rejects a fresh `--steps 500` job. The 250-step checkpoint and `optimizer.pt` are preserved for a separately reviewed continuation.

## Configuration and expected output

[`train001_kaggle.py`](../../notebooks/train001_kaggle.py) revalidates the final dataset and writes `train_config.yaml` from the EXP-001-confirmed settings: `black-forest-labs/FLUX.2-klein-base-4B`, `flux2_klein_4b`, one GPU, 512 resolution, batch 1, BF16 training, FP16 checkpoint save, LoRA linear rank/alpha 16/16 and conv 8/8, `adamw8bit`, LR `1e-4`, `flowmatch`, weighted timesteps, gradient checkpointing, qfloat8 quantization, and `low_vram`. It pins AI Toolkit at `a8dfcf7d7e2b38ccc7b2fb68ece9c6358e61e7a7`. The train split uses `target/` captions with matching `reference/` control images. VAL is held out of training.

The first planned run is **250 steps**, saving at 125 and 250. A same-run continuation mechanism must be verified before proceeding toward 500. These durations are planned checkpoints, not a claim that 250 steps yields quality. EXP-001 projects about 2.28 hours for 250 and 4.56 hours for 500 from the short smoke test, excluding setup, checkpoint, contention, and evaluation. Actual timing must be measured. Preserve `train_config.yaml`, `dataset_evidence.json`, `runtime.json`, `command.json`, `train.log`, `training_summary.json`, `.safetensors` checkpoints, and `optimizer.pt` under `/kaggle/working/train001_250/`. The summary reports success only with finite final-step evidence, a checkpoint, and optimizer state. Model/cache assets stay under `/tmp/hf-cache`.

## Supervisor Kaggle commands, after DATA-001 passes

Use the finalized DATA-001 directory at `/kaggle/working/data001/final` with its `train/`, `val/`, `manifests/`, `reports/`, and `contact_sheets/` directories intact. In a later session restore the same directory from the saved final archive. Use the notebook kernel's CUDA interpreter; do not use a CPU-only system Python. Pull the updated `/kaggle/working/CometicsAI` checkout and prepare the already pinned trainer dependencies only if the current session lacks them:

```python
import subprocess, sys
repo = "/kaggle/working/CometicsAI"
subprocess.run(["git", "-C", repo, "pull", "--ff-only"], check=True)
subprocess.run([sys.executable, "-c", "import torch; assert torch.cuda.is_available()"], check=True)
from pathlib import Path
if not Path("/tmp/exp001-ai-toolkit").is_dir():
    subprocess.run([sys.executable, f"{repo}/notebooks/exp001_flux2_klein_kaggle_smoke.py", "--phase", "prepare"], check=True)
```

Restart the kernel if packages changed, repeat the CUDA check, then prepare the exact dataset-bound config:

```python
base = [sys.executable, f"{repo}/notebooks/train001_kaggle.py",
        "--dataset", "/kaggle/working/data001/final",
        "--out", "/kaggle/working/train001_250",
        "--steps", "250"]
subprocess.run(base + ["--phase", "prepare"], check=True)
```

Inspect `/kaggle/working/train001_250/train_config.yaml` and `dataset_evidence.json`. The Supervisor then starts the authorized real job with notebook output redirected to a file, because the DATA-001 session showed that live model-import logging can stall in the Kaggle output stream:

```python
from pathlib import Path
out = Path("/kaggle/working/train001_250")
with (out / "launcher.log").open("w", encoding="utf-8") as log:
    train_job = subprocess.Popen(base + ["--phase", "execute"],
                                 stdout=log, stderr=subprocess.STDOUT,
                                 start_new_session=True)
print("TRAIN-001 PID:", train_job.pid)
```

Monitor without starting another copy:

```python
print("Exit code (None = running):", train_job.poll())
log = out / "train.log"
print(log.read_text(encoding="utf-8", errors="replace")[-3000:] if log.exists() else "Trainer has not opened train.log yet")
summary = out / "training_summary.json"
print(summary.read_text(encoding="utf-8") if train_job.poll() is not None and summary.exists() else "")
```

Success requires `training_summary.json` to report `success: true`, `highest_loss_step: 250`, `exit_code: 0`, `stop_reason: null`, a `.safetensors` checkpoint, and `optimizer.pt`. If and only if that succeeds, evaluate the final `.safetensors` checkpoint on all 12 held-out directional VAL pairs:

```python
from pathlib import Path
checkpoints = list(Path("/kaggle/working/train001_250/checkpoints").rglob("*.safetensors"))
assert checkpoints, "No checkpoint saved"
checkpoint = max(checkpoints, key=lambda p: p.stat().st_mtime)
subprocess.run(base + ["--phase", "evaluate", "--checkpoint", str(checkpoint)], check=True)
```

Evaluation creates `evaluation/reference_base_adapter_target.jpg`, 12 Base PNGs, 12 adapter PNGs, and `evaluation/metadata.json` with input, target, output hashes, seed, prompt, checkpoint hash, runtime, and GPU memory. Base and adapter use the same 12 held-out inputs, prompts, seed, and inference settings. These images require human review of hairstyle correctness and identity/scene preservation. The paired target is partly synthetic and is a comparison reference, not objective proof of model quality. No automatic quality verdict or app integration follows.

The script rejects `--steps 500` to prevent a fresh run. Preserve the 250-step checkpoint and optimizer state; verify the pinned trainer's same-run continuation procedure only if the 250-step evaluation warrants more training.

Before ending the Kaggle session, download the output directory or package it:

```python
import shutil
shutil.make_archive("/kaggle/working/train001_250_artifacts", "zip", root_dir="/kaggle/working", base_dir="train001_250")
```

## Stop conditions

Stop before training for missing QA/reviews, split leakage, missing captions/images, changed dataset hashes, wrong AI Toolkit commit, unavailable CUDA, or insufficient disk. Stop during training for OOM, dependency/model error, non-finite loss, trainer nonzero exit, missing final-step evidence, or missing checkpoint. Retain the exact log/config/checkpoints and report the failure; do not random-patch the real run. Do not run the 500-step plan or test distilled compatibility without separate review. No hairstyle quality claim is made until validation outputs are inspected.
