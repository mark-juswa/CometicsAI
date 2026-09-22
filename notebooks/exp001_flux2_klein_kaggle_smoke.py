"""EXP-001: run inside a signed-in Kaggle GPU notebook, not on the local PC.

Notebook cell: !python /kaggle/input/<uploaded-source>/exp001_flux2_klein_kaggle_smoke.py
Alternatively paste/upload this file into /kaggle/working and run it there.
No model or dataset weights are bundled with this source file.
"""

from __future__ import annotations

import argparse
import datetime as dt
import importlib.metadata
import json
import math
import os
import platform
import re
import shutil
import statistics
import subprocess
import sys
import threading
import time
import traceback
from pathlib import Path


BASE = "black-forest-labs/FLUX.2-klein-base-4B"
DISTILLED = "black-forest-labs/FLUX.2-klein-4B"
PROMPT = "Change the blue square in the center to bright red; keep the white background and black circle unchanged."
SEED = 1977
SIZE = 512
STEPS = 20
AI_TOOLKIT_COMMIT = "a8dfcf7d7e2b38ccc7b2fb68ece9c6358e61e7a7"
OUT = Path("/kaggle/working/exp001")
DATA = OUT / "synthetic_pairs"
TOOLKIT = Path("/tmp/exp001-ai-toolkit")
CACHE = Path("/tmp/hf-cache")
TRAIN_OUT = OUT / "training"
CONFIG = OUT / "train_config.yaml"
RESULT = OUT / "result.json"


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def write_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, default=str) + "\n", encoding="utf-8")


def command(args: list[str], *, cwd: Path | None = None, log: Path | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    shown = " ".join(args)
    print("$", shown, flush=True)
    start = time.monotonic()
    try:
        proc = subprocess.run(args, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    except FileNotFoundError as exc:
        proc = subprocess.CompletedProcess(args, 127, f"{type(exc).__name__}: {exc}\n")
    if log:
        log.parent.mkdir(parents=True, exist_ok=True)
        log.write_text(proc.stdout, encoding="utf-8", errors="replace")
    print(proc.stdout[-6000:], flush=True)
    print(f"exit={proc.returncode} elapsed_s={time.monotonic() - start:.1f}", flush=True)
    if check and proc.returncode:
        raise RuntimeError(f"Command failed ({proc.returncode}): {shown}; full output: {log}")
    return proc


def version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def disk_info(path: Path) -> dict:
    if not path.exists():
        return {"path": str(path), "exists": False}
    d = shutil.disk_usage(path)
    return {"path": str(path), "exists": True, "total_bytes": d.total, "free_bytes": d.free,
            "device_id": path.stat().st_dev}


def memory_info(torch=None) -> dict:
    try:
        import psutil
        process = psutil.Process()
        system = psutil.virtual_memory()
        cpu = {"process_rss_bytes": process.memory_info().rss,
               "system_available_bytes": system.available,
               "system_used_bytes": system.used}
    except Exception as exc:
        cpu = {"error": f"{type(exc).__name__}: {exc}"}
    gpu = None
    if torch is not None and torch.cuda.is_available():
        gpu = {"allocated_bytes": torch.cuda.memory_allocated(0),
               "reserved_bytes": torch.cuda.memory_reserved(0),
               "peak_allocated_bytes": torch.cuda.max_memory_allocated(0),
               "peak_reserved_bytes": torch.cuda.max_memory_reserved(0)}
    return {"utc": utc_now(), "cpu": cpu, "gpu0": gpu}


class GpuMemorySampler:
    """Samples whole-device memory so subprocess training is measurable."""
    def __init__(self, interval_s: float = 0.5):
        self.interval_s = interval_s
        self.values_mib: list[int] = []
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def _sample(self) -> None:
        while not self._stop.is_set():
            proc = subprocess.run(
                ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits", "-i", "0"],
                text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            )
            if proc.returncode == 0:
                try:
                    self.values_mib.append(int(proc.stdout.strip().splitlines()[0]))
                except (ValueError, IndexError):
                    pass
            self._stop.wait(self.interval_s)

    def __enter__(self):
        self._thread = threading.Thread(target=self._sample, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, *_):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2)

    @property
    def peak_mib(self) -> int | None:
        return max(self.values_mib, default=None)


def audit() -> tuple[dict, object]:
    print("SECTION A: ENVIRONMENT AUDIT", flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    smi = command(["nvidia-smi", "-q"], log=OUT / "nvidia-smi.txt", check=False)
    mounts = command(["df", "-hT"], log=OUT / "mounts.txt", check=False)
    try:
        import psutil
        ram = psutil.virtual_memory().total
        mount_rows = [m._asdict() for m in psutil.disk_partitions(all=True)]
    except ImportError:
        ram = os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES")
        mount_rows = None
    try:
        import torch
    except ImportError as exc:
        raise RuntimeError("PyTorch is missing from this runtime") from exc
    cuda = torch.cuda.is_available()
    devices = []
    if cuda:
        for i in range(torch.cuda.device_count()):
            p = torch.cuda.get_device_properties(i)
            devices.append({"index": i, "name": p.name, "vram_bytes": p.total_memory,
                            "capability": list(torch.cuda.get_device_capability(i)),
                            "native_bf16": bool(torch.cuda.get_device_capability(i)[0] >= 8),
                            "torch_bf16_supported": bool(torch.cuda.is_bf16_supported()) if i == 0 and hasattr(torch.cuda, "is_bf16_supported") else None})
    env = {"utc": utc_now(), "python": sys.version, "python_executable": sys.executable,
           "platform": platform.platform(),
           "torch": torch.__version__, "torch_cuda_runtime": torch.version.cuda,
           "cuda_available": cuda, "gpu_count": len(devices), "gpus": devices,
           "system_ram_bytes": ram, "disks": [disk_info(Path(p)) for p in (Path("/"), Path("/tmp"), Path("/kaggle/temp"), Path("/kaggle/working"))],
           "mounts": mount_rows, "nvidia_smi_exit": smi.returncode, "df_exit": mounts.returncode,
           "packages_before": {p: version(p) for p in ("torch", "diffusers", "transformers", "accelerate", "peft", "huggingface-hub", "pillow", "bitsandbytes")}}
    write_json(OUT / "environment.json", env)
    print(json.dumps(env, indent=2, default=str), flush=True)
    if not cuda or not devices:
        if "+cpu" in torch.__version__:
            raise RuntimeError(
                f"STOP: CPU-only PyTorch {torch.__version__} under {sys.executable}; "
                "launch this script with the active notebook kernel's sys.executable, then verify the accelerator if CUDA is still unavailable"
            )
        raise RuntimeError("STOP: no CUDA GPU was allocated; enable a free GPU session before model downloads")
    return env, torch


def choose_precision(env: dict) -> str:
    # NVIDIA documents native BF16 at compute capability >=8; Turing/T4 (7.5) uses FP16.
    cap = env["gpus"][0]["capability"]
    precision = "bf16" if cap[0] >= 8 and env["gpus"][0]["torch_bf16_supported"] else "float16"
    print(f"Selected precision for cuda:0: {precision}; capability={cap}", flush=True)
    return precision


def model_preflight() -> dict:
    global TOOLKIT, CACHE
    print("MODEL ACCESS AND STORAGE PREFLIGHT", flush=True)
    from huggingface_hub import HfApi
    token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")
    if not token:
        try:
            from kaggle_secrets import UserSecretsClient
            token = UserSecretsClient().get_secret("HF_TOKEN")
        except Exception:
            pass
    if token:
        os.environ["HF_TOKEN"] = token  # never print or serialize this value
    api = HfApi(token=token)
    metadata = {}
    for model in (BASE, DISTILLED):
        info = api.model_info(model, files_metadata=True)
        size = sum((f.size or 0) for f in info.siblings or [])
        metadata[model] = {"revision": info.sha, "repo_bytes": size}
    # /kaggle/working is saved output. The Supervisor measured /tmp as the large disposable mount.
    scratch = next((p for p in (Path("/tmp"), Path("/kaggle/temp")) if p.exists() and os.access(p, os.W_OK)), None)
    if scratch is None:
        raise RuntimeError("STOP: no writable ephemeral scratch directory")
    base_size = metadata[BASE]["repo_bytes"]
    if base_size <= 0:
        raise RuntimeError("STOP: model file sizes unavailable; inspect storage manually before downloading")
    required = math.ceil(base_size * 1.4) + 8 * 1024**3
    free = shutil.disk_usage(scratch).free
    preflight = {"models": metadata, "scratch": str(scratch), "scratch_free_bytes": free,
                 "base_download_headroom_bytes": required,
                 "working_free_bytes": shutil.disk_usage("/kaggle/working").free,
                 "token_present": bool(token)}
    write_json(OUT / "preflight.json", preflight)
    if free < required:
        raise RuntimeError(f"STOP: scratch free {free} < conservative Base download need {required}; no weights downloaded")
    CACHE = scratch / "hf-cache"
    CACHE.mkdir(exist_ok=True)
    TOOLKIT = scratch / "exp001-ai-toolkit"
    os.environ["HF_HOME"] = str(CACHE)
    os.environ["HF_HUB_CACHE"] = str(CACHE / "hub")
    return preflight


def make_pairs() -> None:
    print("SYNTHETIC DATASET: 3 deterministic paired edits", flush=True)
    from PIL import Image, ImageDraw
    ref, target = DATA / "reference", DATA / "target"
    ref.mkdir(parents=True, exist_ok=True)
    target.mkdir(parents=True, exist_ok=True)
    for i, x in enumerate((128, 192, 256), 1):
        for color, folder in (("blue", ref), ("red", target)):
            image = Image.new("RGB", (SIZE, SIZE), "white")
            draw = ImageDraw.Draw(image)
            draw.ellipse((25, 25, 100, 100), outline="black", width=8)
            draw.rectangle((x, 190, x + 100, 290), fill=color)
            image.save(folder / f"{i:03d}.png")
        (target / f"{i:03d}.txt").write_text(PROMPT + "\n", encoding="utf-8")
    stems = sorted(p.stem for p in ref.glob("*.png"))
    assert len(stems) == 3
    assert all((target / f"{s}.png").exists() and (target / f"{s}.txt").exists() for s in stems)
    write_json(OUT / "dataset_manifest.json", {"pairs": len(stems), "stems": stems, "caption": PROMPT,
                                                   "source": "Pillow deterministic shapes; no real hairstyle images"})


def pipeline(model_id: str, dtype, torch):
    from diffusers import Flux2KleinPipeline
    torch.cuda.reset_peak_memory_stats(0)
    t0 = time.monotonic()
    with GpuMemorySampler() as sampler:
        pipe = Flux2KleinPipeline.from_pretrained(model_id, torch_dtype=dtype, cache_dir=os.environ["HF_HUB_CACHE"])
        pipe.enable_model_cpu_offload(gpu_id=0)
    elapsed = time.monotonic() - t0
    observation = {"model": model_id, "load_seconds": elapsed, "dtype": str(dtype),
                   "strategy": "Diffusers enable_model_cpu_offload on cuda:0",
                   "whole_gpu_peak_mib": sampler.peak_mib, "memory_after_load": memory_info(torch)}
    print(f"Loaded {model_id} with CPU offload in {elapsed:.1f}s", flush=True)
    return pipe, observation


def generate(pipe, torch, source: Path, dest: Path, model_id: str, steps: int, guidance: float) -> dict:
    from PIL import Image
    torch.cuda.reset_peak_memory_stats(0)
    start = time.monotonic()
    image = pipe(prompt=PROMPT, image=Image.open(source).convert("RGB"), height=SIZE, width=SIZE,
                 num_inference_steps=steps, guidance_scale=guidance,
                 generator=torch.Generator(device="cuda").manual_seed(SEED)).images[0]
    image.save(dest)
    result = {"model": model_id, "source": str(source), "output": str(dest), "prompt": PROMPT,
              "seed": SEED, "width": SIZE, "height": SIZE, "steps": steps, "guidance": guidance,
              "runtime_s": time.monotonic() - start, "peak_allocated_bytes": torch.cuda.max_memory_allocated(0),
              "peak_reserved_bytes": torch.cuda.max_memory_reserved(0)}
    write_json(dest.with_suffix(".json"), result)
    return result


def install_toolkit() -> tuple[str, dict]:
    print("TRAINER INSTALL AND VERSION CAPTURE", flush=True)
    if not TOOLKIT.exists():
        TOOLKIT.mkdir(parents=True)
        command(["git", "init"], cwd=TOOLKIT, log=OUT / "trainer_git_init.log")
        command(["git", "remote", "add", "origin", "https://github.com/ostris/ai-toolkit.git"], cwd=TOOLKIT)
        command(["git", "fetch", "--depth", "1", "origin", AI_TOOLKIT_COMMIT], cwd=TOOLKIT,
                log=OUT / "trainer_fetch.log")
        command(["git", "checkout", "--detach", "FETCH_HEAD"], cwd=TOOLKIT)
    sha = command(["git", "rev-parse", "HEAD"], cwd=TOOLKIT).stdout.strip()
    if sha != AI_TOOLKIT_COMMIT:
        raise RuntimeError(f"STOP: AI Toolkit revision {sha} does not match pinned {AI_TOOLKIT_COMMIT}")
    torch_before = version("torch")
    import torch
    cuda_before = torch.version.cuda
    constraints = OUT / "kaggle_torch_constraints.txt"
    pinned = [f"torch=={torch_before}"]
    for package in ("torchvision", "torchaudio"):
        observed = version(package)
        if observed:
            pinned.append(f"{package}=={observed}")
    constraints.write_text("\n".join(pinned) + "\n", encoding="utf-8")
    install_args = [sys.executable, "-m", "pip", "install", "--constraint", str(constraints),
                    "-r", str(TOOLKIT / "requirements.txt")]
    command(install_args,
            log=OUT / "trainer_install.log")
    torch_after = version("torch")
    check_code = (
        "import json, torch; print(json.dumps({"
        "'torch': torch.__version__, 'torch_cuda_runtime': torch.version.cuda, "
        "'cuda_available': torch.cuda.is_available(), "
        "'gpu0': torch.cuda.get_device_name(0) if torch.cuda.is_available() else None}))"
    )
    checked = command([sys.executable, "-c", check_code], log=OUT / "torch_after_install.log")
    runtime_check = json.loads(checked.stdout.strip().splitlines()[-1])
    if torch_after != torch_before or runtime_check["torch_cuda_runtime"] != cuda_before:
        raise RuntimeError(f"STOP: dependency install changed PyTorch/CUDA from {torch_before}/{cuda_before} "
                           f"to {torch_after}/{runtime_check['torch_cuda_runtime']}; do not continue")
    if not runtime_check["cuda_available"]:
        raise RuntimeError("STOP: CUDA became unavailable after dependency installation")
    packages = {p: version(p) for p in ("torch", "diffusers", "transformers", "accelerate", "peft", "huggingface-hub", "bitsandbytes", "optimum-quanto")}
    write_json(OUT / "dependencies.json", {"ai_toolkit_commit": sha, "packages": packages,
                                             "runtime_check_after_install": runtime_check,
                                             "constraints": pinned,
                                             "install_command": " ".join(install_args)})
    return sha, packages


def train_config(precision: str) -> None:
    # Based on BFL's AI Toolkit Klein YAML plus its documented control_path edit dataset.
    # Deliberately tiny: tests optimizer/checkpoint plumbing, not hairstyle quality.
    training_path = TRAIN_OUT.as_posix()
    target_path = (DATA / "target").as_posix()
    reference_path = (DATA / "reference").as_posix()
    yaml = f'''job: "extension"
config:
  name: "exp001_tiny_edit"
  process:
    - type: "diffusion_trainer"
      training_folder: "{training_path}"
      device: "cuda:0"
      performance_log_every: 5
      network:
        type: "lora"
        linear: 16
        linear_alpha: 16
        conv: 8
        conv_alpha: 8
      save:
        dtype: "{precision}"
        save_every: {STEPS}
        max_step_saves_to_keep: 1
      datasets:
        - folder_path: "{target_path}"
          control_path: "{reference_path}"
          caption_ext: "txt"
          resolution: [{SIZE}]
      train:
        batch_size: 1
        steps: {STEPS}
        lr: 0.0001
        optimizer: "adamw8bit"
        noise_scheduler: "flowmatch"
        gradient_checkpointing: true
        dtype: "{precision}"
        train_unet: true
        train_text_encoder: false
        timestep_type: "weighted"
        content_or_style: "balanced"
      model:
        arch: "flux2_klein_4b"
        name_or_path: "{BASE}"
        quantize: true
        low_vram: true
meta:
  name: "exp001_tiny_edit"
  version: "1.0"
'''
    CONFIG.write_text(yaml, encoding="utf-8")


def run_training() -> dict:
    print("STAGE 3: TINY EDIT LORA TRAINING", flush=True)
    cmd = [sys.executable, "run.py", str(CONFIG)]
    start = time.monotonic()
    print("$", " ".join(cmd), flush=True)
    progress_times: dict[int, float] = {}
    with GpuMemorySampler() as sampler:
        with (OUT / "train.log").open("w", encoding="utf-8") as log:
            proc = subprocess.Popen(cmd, cwd=TOOLKIT, text=True, stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT, bufsize=1)
            assert proc.stdout is not None
            for line in proc.stdout:
                log.write(line)
                log.flush()
                print(line, end="", flush=True)
                for match in re.finditer(r"\b(\d+)/" + str(STEPS) + r"\b", line):
                    step = int(match.group(1))
                    if step > 0:
                        progress_times.setdefault(step, time.monotonic())
            proc.wait()
    elapsed = time.monotonic() - start
    logs = (OUT / "train.log").read_text(encoding="utf-8", errors="replace")
    progress = [int(x) for x in re.findall(r"\b(\d+)/" + str(STEPS) + r"\b", logs)]
    loss_lines = [line for line in logs.splitlines() if re.search(r"\bloss\b", line, re.I)]
    nonfinite_loss_lines = [line for line in loss_lines if re.search(
        r"(?:loss\s+is|loss\s*:)\s*[+-]?(?:nan|inf)", line, re.I
    )]
    result = {"command": " ".join(cmd), "exit_code": proc.returncode, "wall_s_including_load": elapsed,
              "configured_steps": STEPS, "highest_step_seen": max(progress, default=None),
              "loss_line_count": len(loss_lines), "last_loss_lines": loss_lines[-5:],
              "nonfinite_loss_line_count": len(nonfinite_loss_lines),
              "last_nonfinite_loss_lines": nonfinite_loss_lines[-5:],
              "whole_gpu_peak_mib": sampler.peak_mib}
    write_json(OUT / "training_result.json", result)
    if proc.returncode:
        raise RuntimeError("STOP: trainer failed; preserve train.log and do not start an unrelated fix chain")
    if result["highest_step_seen"] != STEPS:
        raise RuntimeError("STOP: trainer exited without log evidence that all configured steps completed")
    if not loss_lines:
        raise RuntimeError("STOP: trainer exited but no loss evidence was found in train.log")
    # Use only observed progress intervals, excluding startup and first few steps.
    timed_steps = sorted((s, t) for s, t in progress_times.items() if s >= 5)
    intervals = [(timed_steps[i][1] - timed_steps[i-1][1]) / (timed_steps[i][0] - timed_steps[i-1][0])
                 for i in range(1, len(timed_steps)) if timed_steps[i][0] > timed_steps[i-1][0]]
    if len(intervals) >= 5:
        seconds_per_step = statistics.median(intervals[-10:])
        result["measured_median_seconds_per_step"] = seconds_per_step
        result["projections_hours_from_smoke_timing"] = {str(n): seconds_per_step * n / 3600 for n in (500, 1000, 1500)}
    else:
        result["measured_median_seconds_per_step"] = None
        result["projections_hours_from_smoke_timing"] = None
        result["timing_limitation"] = "Fewer than five post-warmup progress intervals; do not use wall time as stable step timing"
    # Retain an all-in wall-time figure separately; it is not the requested projection.
    result["wall_seconds_per_configured_step_including_load"] = elapsed / STEPS
    write_json(OUT / "training_result.json", result)
    if nonfinite_loss_lines:
        raise RuntimeError("STOP: trainer produced non-finite loss; preserve train.log and do not treat the checkpoint as valid training")
    return result


def find_checkpoint() -> Path:
    candidates = sorted(TRAIN_OUT.rglob("*.safetensors"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not candidates:
        raise RuntimeError("STOP: training finished without a .safetensors checkpoint")
    return candidates[0]


def main() -> None:
    global TOOLKIT
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit-only", action="store_true", help="Inspect machine without downloads or training")
    parser.add_argument("--phase", choices=("all", "prepare", "execute", "retry-training"), default="all")
    args = parser.parse_args()
    if args.phase == "all" and not args.audit_only:
        first = command([sys.executable, __file__, "--phase", "prepare"], log=OUT / "prepare.log", check=False)
        if first.returncode:
            raise SystemExit(first.returncode)
        second = command([sys.executable, __file__, "--phase", "execute"], log=OUT / "execute.log", check=False)
        raise SystemExit(second.returncode)
    result = {"experiment": "EXP-001", "started_utc": utc_now(), "status": "IN PROGRESS"}
    write_json(RESULT, result)
    try:
        if args.phase == "prepare" or args.audit_only:
            env, _ = audit()
            result["environment"] = str(OUT / "environment.json")
            if args.audit_only:
                result["status"] = "AUDIT ONLY"
                return
            result["precision"] = choose_precision(env)
            model_preflight()
            make_pairs()
            install_toolkit()
            result["status"] = "PREPARED"
            return
        # Execute in a fresh Python process after dependency installation.
        # Hide GPU 1 before importing torch so neither Diffusers nor AI Toolkit can use it.
        os.environ["CUDA_VISIBLE_DEVICES"] = "0"
        import torch
        env = json.loads((OUT / "environment.json").read_text(encoding="utf-8"))
        precision = choose_precision(env)
        result["precision"] = precision
        meta = json.loads((OUT / "preflight.json").read_text(encoding="utf-8"))
        scratch = Path(meta["scratch"])
        TOOLKIT = scratch / "exp001-ai-toolkit"
        if shutil.disk_usage(scratch).free < meta["base_download_headroom_bytes"]:
            raise RuntimeError("STOP: scratch capacity fell below Base download headroom after trainer installation")
        CACHE = scratch / "hf-cache"
        os.environ["HF_HOME"] = str(CACHE)
        os.environ["HF_HUB_CACHE"] = str(CACHE / "hub")
        dtype = torch.bfloat16 if precision == "bf16" else torch.float16
        import gc
        if args.phase != "retry-training":
            print("STAGE 1: BASE LOAD", flush=True)
            write_json(OUT / "storage_before_model_load.json", {"scratch": disk_info(scratch), "cache": disk_info(CACHE),
                                                                   "working": disk_info(Path("/kaggle/working"))})
            pipe, load_observation = pipeline(BASE, dtype, torch)
            result["base_load"] = load_observation
            write_json(OUT / "storage_after_base_load.json", {"scratch": disk_info(scratch), "cache": disk_info(CACHE),
                                                                 "working": disk_info(Path("/kaggle/working"))})
            print("STAGE 2: BASE IMAGE EDIT", flush=True)
            source = OUT / "source.png"
            shutil.copy2(DATA / "reference/001.png", source)
            result["base_edit"] = generate(pipe, torch, source, OUT / "result_base.png", BASE, 20, 4.0)
            write_json(OUT / "base_inference_config.json", result["base_edit"])
            del pipe
            gc.collect()
            torch.cuda.empty_cache()
        train_config(precision)
        result["training"] = run_training()
        checkpoint = find_checkpoint()
        result["checkpoint"] = {"path": str(checkpoint), "bytes": checkpoint.stat().st_size}
        print("STAGE 4: FRESH BASE LOAD + ADAPTER + EDIT", flush=True)
        pipe, result["base_reload"] = pipeline(BASE, dtype, torch)
        pipe.load_lora_weights(str(checkpoint.parent), weight_name=checkpoint.name)
        result["base_lora_edit"] = generate(pipe, torch, DATA / "reference/001.png", OUT / "base_lora_edit.png", BASE, 20, 4.0)
        result["status"] = "TECHNICAL GATES PASSED"  # Schedule classification requires timing review.
    except Exception as exc:
        result["status"] = "STOPPED"
        result["error"] = f"{type(exc).__name__}: {exc}"
        (OUT / "error.txt").write_text(traceback.format_exc(), encoding="utf-8")
        print(traceback.format_exc(), flush=True)
    finally:
        result["finished_utc"] = utc_now()
        write_json(RESULT, result)
        print("RESULT:", json.dumps(result, indent=2, default=str), flush=True)
    if result["status"] == "STOPPED":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
