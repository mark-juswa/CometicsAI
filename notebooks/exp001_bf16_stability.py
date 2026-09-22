"""EXP-001 controlled BF16 numerical stability test for the existing Kaggle session."""

from __future__ import annotations

import importlib.util
import json
import math
import os
import re
import shutil
import sys
import traceback
from pathlib import Path


OUT = Path("/kaggle/working/exp001")
RESULT = OUT / "bf16_stability_result.json"
HARNESS = Path(__file__).with_name("exp001_flux2_klein_kaggle_smoke.py")


def load_harness():
    spec = importlib.util.spec_from_file_location("exp001_harness", HARNESS)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load harness from {HARNESS}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_result(value: dict) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    RESULT.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def raw_step_losses(log_path: Path, steps: int) -> list[dict]:
    text = log_path.read_text(encoding="utf-8", errors="replace")
    nonfinite = re.findall(r"loss\s+is\s+([+-]?(?:nan|inf))", text, re.I)
    if nonfinite:
        return [
            {"step": index + 1, "raw": raw.lower(), "finite": False}
            for index, raw in enumerate(nonfinite[:steps])
        ]

    pattern = re.compile(
        rf"\b(\d+)/{steps}\b[^\r\n]*?loss:\s*"
        r"([+-]?(?:(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?|nan|inf))",
        re.I,
    )
    by_step: dict[int, str] = {}
    for match in pattern.finditer(text):
        step = int(match.group(1))
        if 1 <= step <= steps and step not in by_step:
            by_step[step] = match.group(2)

    losses = []
    for step in range(1, steps + 1):
        if step not in by_step:
            raise RuntimeError(f"Missing raw loss for BF16 step {step} in {log_path}")
        raw = by_step[step]
        losses.append({"step": step, "raw": raw, "finite": math.isfinite(float(raw))})
    return losses


def seconds_per_step(log_path: Path) -> float | None:
    text = log_path.read_text(encoding="utf-8", errors="replace")
    timer_rows = re.findall(r"([0-9]+(?:\.[0-9]+)?)s avg - train_loop, num = (\d+)", text)
    if timer_rows:
        total_steps = sum(int(count) for _, count in timer_rows)
        if total_steps:
            return sum(float(average) * int(count) for average, count in timer_rows) / total_steps
    tqdm_rows = re.findall(r"\b\d+/\d+\b[^\r\n]*?([0-9]+(?:\.[0-9]+)?)s/it", text)
    return float(tqdm_rows[-1]) if tqdm_rows else None


def run_attempt(harness, steps: int, label: str) -> tuple[dict, list[dict], Path, Exception | None]:
    harness.STEPS = steps
    harness.TRAIN_OUT = OUT / f"training_{label}"
    harness.CONFIG = OUT / f"train_config_{label}.yaml"
    harness.train_config("bf16")
    config_text = harness.CONFIG.read_text(encoding="utf-8")
    save_block = '      save:\n        dtype: "bf16"'
    if config_text.count(save_block) != 1:
        raise RuntimeError("Could not preserve the verified float16 checkpoint save dtype")
    harness.CONFIG.write_text(
        config_text.replace(save_block, '      save:\n        dtype: "float16"', 1),
        encoding="utf-8",
    )

    source_log = OUT / "train.log"
    source_result = OUT / "training_result.json"
    saved_log = OUT / f"train_{label}.log"
    saved_result = OUT / f"training_result_{label}.json"

    training_error = None
    try:
        training = harness.run_training()
    except Exception as exc:
        training_error = exc
        training = {}
    finally:
        if source_log.exists():
            shutil.copy2(source_log, saved_log)
        if source_result.exists():
            shutil.copy2(source_result, saved_result)

    if saved_result.exists():
        training = json.loads(saved_result.read_text(encoding="utf-8"))
    elif training_error is not None:
        raise training_error
    try:
        losses = raw_step_losses(saved_log, steps)
    except Exception as loss_error:
        if training_error is not None:
            raise RuntimeError(f"{training_error}; loss evidence error: {loss_error}") from training_error
        raise
    training["observed_seconds_per_step"] = seconds_per_step(saved_log)
    return training, losses, harness.TRAIN_OUT, training_error


def main() -> None:
    result = {
        "experiment": "EXP-001",
        "test": "BF16 numerical stability",
        "classification": "BF16 DID NOT SOLVE NaN",
        "bf16_executed": False,
    }
    write_result(result)

    try:
        os.environ["CUDA_VISIBLE_DEVICES"] = "0"
        harness = load_harness()
        import torch

        environment = json.loads((OUT / "environment.json").read_text(encoding="utf-8"))
        metadata = json.loads((OUT / "preflight.json").read_text(encoding="utf-8"))
        scratch = Path(metadata["scratch"])
        harness.TOOLKIT = scratch / "exp001-ai-toolkit"
        harness.CACHE = scratch / "hf-cache"
        os.environ["HF_HOME"] = str(harness.CACHE)
        os.environ["HF_HUB_CACHE"] = str(harness.CACHE / "hub")

        if not torch.cuda.is_available():
            raise RuntimeError("BF16 test cannot execute because CUDA is unavailable")
        if environment["gpus"][0]["capability"] != [7, 5]:
            raise RuntimeError(f"BF16 test expected the verified T4 capability [7, 5], got {environment['gpus'][0]['capability']}")

        probe_training, probe_losses, _, probe_error = run_attempt(harness, 3, "bf16_3step")
        result["bf16_executed"] = True
        result["first_3_steps"] = {
            "losses": probe_losses,
            "seconds_per_step": probe_training.get("observed_seconds_per_step"),
            "peak_vram_mib": probe_training.get("whole_gpu_peak_mib"),
        }
        write_result(result)

        if probe_error is not None:
            raise probe_error
        if len(probe_losses) != 3 or not all(item["finite"] for item in probe_losses):
            raise RuntimeError(f"BF16 produced a non-finite loss in the 3-step probe: {probe_losses}")

        full_training, full_losses, full_training_out, full_error = run_attempt(harness, 20, "bf16_20step")
        result["twenty_steps"] = {
            "completed": full_training.get("highest_step_seen") == 20,
            "losses": full_losses,
            "seconds_per_step": full_training.get("observed_seconds_per_step"),
            "peak_vram_mib": full_training.get("whole_gpu_peak_mib"),
        }
        write_result(result)
        if full_error is not None:
            raise full_error
        if len(full_losses) != 20 or not all(item["finite"] for item in full_losses):
            raise RuntimeError("BF16 produced a non-finite loss in the 20-step confirmation")

        checkpoint_candidates = sorted(
            full_training_out.rglob("*.safetensors"),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
        if not checkpoint_candidates:
            raise RuntimeError("BF16 20-step run did not create a .safetensors checkpoint")
        checkpoint = checkpoint_candidates[0]
        result["checkpoint"] = {"path": str(checkpoint), "bytes": checkpoint.stat().st_size}

        pipe, load_observation = harness.pipeline(harness.BASE, torch.float16, torch)
        pipe.load_lora_weights(str(checkpoint.parent), weight_name=checkpoint.name)
        result["fresh_adapter_reload"] = {"succeeded": True, "base_load": load_observation}
        result["classification"] = "FINITE TRAINING VERIFIED"
    except Exception as exc:
        result["exact_error"] = f"{type(exc).__name__}: {exc}"
        (OUT / "bf16_stability_error.txt").write_text(traceback.format_exc(), encoding="utf-8")
    finally:
        write_result(result)
        print(json.dumps(result, indent=2))

    if result["classification"] != "FINITE TRAINING VERIFIED":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
