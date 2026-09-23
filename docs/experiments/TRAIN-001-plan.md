# TRAIN-001 BF16 hairstyle Edit-LoRA handoff

**Prepared, not executed.** Real hairstyle training requires DATA-001 `reports/qa.json`, 30 explicit ACCEPT reviews, 60 validated directional pairs, and human inspection of both final contact sheets. The three-image masked pilot and remaining generation are still pending. The EXP-001 T4 smoke test verified finite BF16 training for 20 steps at approximately 32.808 seconds/step and 13,531 MiB peak, not long-run stability or hairstyle quality.

## Configuration and expected output

[`train001_kaggle.py`](../../notebooks/train001_kaggle.py) revalidates the final dataset and writes `train_config.yaml` from the EXP-001-confirmed settings: `black-forest-labs/FLUX.2-klein-base-4B`, `flux2_klein_4b`, one GPU, 512 resolution, batch 1, BF16 training, FP16 checkpoint save, LoRA linear rank/alpha 16/16 and conv 8/8, `adamw8bit`, LR `1e-4`, `flowmatch`, weighted timesteps, gradient checkpointing, qfloat8 quantization, and `low_vram`. It pins AI Toolkit at `a8dfcf7d7e2b38ccc7b2fb68ece9c6358e61e7a7`. The train split uses `target/` captions with matching `reference/` control images. VAL is held out of training.

The first planned run is **250 steps**, saving at 125 and 250; a **separate 500-step** configuration is available only after the first run is reviewed. These durations are planned checkpoints, not a claim that 250 steps yields quality or that the 500-step command resumes the 250-step weights. EXP-001 projects about 2.28 hours for 250 and 4.56 hours for 500 from the short smoke test, excluding setup, checkpoint, contention, and evaluation. Actual timing must be measured. Preserve `train_config.yaml`, `dataset_evidence.json`, `runtime.json`, `command.json`, `train.log`, `training_summary.json`, and `.safetensors` checkpoints under `/kaggle/working/train001_250/` (or `train001_500/`). Model/cache assets stay under `/tmp/hf-cache`.

## Supervisor Kaggle commands, after DATA-001 passes

Upload/extract the final DATA-001 directory to `/kaggle/working/data001_final` with its `train/`, `val/`, `manifests/`, `reports/`, and `contact_sheets/` directories intact. Use the notebook kernel's CUDA interpreter; do not use a CPU-only system Python. Clone or update `/kaggle/working/CometicsAI` and prepare only the already pinned trainer dependencies if the current session lacks them:

```python
import subprocess, sys
repo = "/kaggle/working/CometicsAI"
subprocess.run(["git", "-C", repo, "pull", "--ff-only"], check=True)
subprocess.run([sys.executable, "-c", "import torch; assert torch.cuda.is_available()"], check=True)
subprocess.run([sys.executable, f"{repo}/notebooks/exp001_flux2_klein_kaggle_smoke.py", "--phase", "prepare"], check=True)
```

Restart the kernel if packages changed, repeat the CUDA check, then prepare the exact dataset-bound config:

```python
base = [sys.executable, f"{repo}/notebooks/train001_kaggle.py",
        "--dataset", "/kaggle/working/data001_final",
        "--out", "/kaggle/working/train001_250",
        "--steps", "250"]
subprocess.run(base + ["--phase", "prepare"], check=True)
```

Inspect `/kaggle/working/train001_250/train_config.yaml` and `dataset_evidence.json`. The Supervisor then starts the authorized real job:

```python
subprocess.run(base + ["--phase", "execute"], check=True)
```

If and only if training finishes with finite logged loss and a checkpoint, evaluate the latest **final** `.safetensors` checkpoint on all 12 held-out directional VAL pairs:

```python
from pathlib import Path
checkpoints = list(Path("/kaggle/working/train001_250/checkpoints").rglob("*.safetensors"))
assert checkpoints, "No checkpoint saved"
checkpoint = max(checkpoints, key=lambda p: p.stat().st_mtime)
subprocess.run(base + ["--phase", "evaluate", "--checkpoint", str(checkpoint)], check=True)
```

Evaluation creates `evaluation/reference_base_adapter_target.jpg`, 12 Base PNGs, 12 adapter PNGs, and `evaluation/metadata.json` with input, target, output hashes, seed, prompt, checkpoint hash, runtime, and GPU memory. Base and adapter use the same 12 held-out inputs, prompts, seed, and inference settings. These images require human review of hairstyle correctness and identity/scene preservation. The paired target is partly synthetic and is a comparison reference, not objective proof of model quality. No automatic quality verdict or app integration follows.

If the Project Lead later authorizes a separate 500-step run, use the same three commands with `--out /kaggle/working/train001_500 --steps 500`. It starts fresh unless a documented resume mechanism is explicitly approved; do not assume continuation.

Before ending the Kaggle session, download the output directory or package it:

```python
import shutil
shutil.make_archive("/kaggle/working/train001_250_artifacts", "zip", root_dir="/kaggle/working", base_dir="train001_250")
```

## Stop conditions

Stop before training for missing QA/reviews, split leakage, missing captions/images, changed dataset hashes, wrong AI Toolkit commit, unavailable CUDA, or insufficient disk. Stop during training for OOM, dependency/model error, non-finite loss, trainer nonzero exit, missing final-step evidence, or missing checkpoint. Retain the exact log/config/checkpoints and report the failure; do not random-patch the real run. Do not run the 500-step plan or test distilled compatibility without separate review. No hairstyle quality claim is made until validation outputs are inspected.
