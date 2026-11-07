"""Reproduce pinned private style pilot. No servers, tunnels or cloud changes."""
import argparse
from hashlib import sha256
from importlib import metadata
import json
import os
from pathlib import Path
import secrets
import shutil
import socket
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import unified_gate3_bootstrap as original


def check_ports():
    for port in (8765, 8800):
        with socket.socket() as connection:
            connection.settimeout(1)
            if connection.connect_ex(("127.0.0.1", port)) == 0:
                raise RuntimeError("An AI worker/API is running. Use a separate notebook session.")


def clean_environment(source):
    env = {**source, "CUDA_VISIBLE_DEVICES": "0", "PYTHONUNBUFFERED": "1",
           "HF_HOME": str(Path("/tmp") / "beautycore-style-pilot-hf" / ROOT.parent.name), "MPLBACKEND": "Agg", "PYTHONNOUSERSITE": "1"}
    for key in ("PYTHONPATH", "PYTHONSTARTUP", "PYTHONUSERBASE", "LD_PRELOAD",
                "AI_INFERENCE_PROFILE", "AI_PROMPT_CACHE", "AI_PROMPT_CACHE_SCOPE",
                "HAIRCAPSTONE_STYLE_REGISTRY_PATH", "AI_HAIR_ADAPTER_DIRS", "AI_MODEL_DIR",
                "AI_BACKEND_API_KEY", "AI_REMOTE_API_KEY", "GEMINI_API_KEY",
                "HF_HUB_CACHE", "HUGGINGFACE_HUB_CACHE", "TRANSFORMERS_CACHE"):
        env.pop(key, None)
    return env



MIN_SCRATCH_BYTES = 30 * 1024 ** 3
SCRATCH_FAILURE = "Less than 30 GiB scratch available for pinned Base, no model download started"


def select_cache_home(work, bases=None, disk_usage=shutil.disk_usage):
    """Probe actual volumes; never lower the original downloader's space guard."""
    bases = tuple(bases) if bases is not None else (Path("/tmp"), Path("/kaggle/temp"))
    observations = []
    for base in bases:
        base = Path(base)
        row = {"base": str(base), "usable": False}
        observations.append(row)
        try:
            if not base.is_dir():
                row["reason"] = "missing"
                continue
            row["free_bytes"] = disk_usage(base).free
            print("STYLE_PILOT SCRATCH", base, round(row["free_bytes"] / 1024 ** 3, 2),
                  "GiB free; minimum 30 GiB", flush=True)
            if row["free_bytes"] < MIN_SCRATCH_BYTES:
                row["reason"] = "insufficient_space"
                continue
            home = base / "beautycore-style-pilot-hf" / Path(work).name
            home.mkdir(parents=True, exist_ok=True)
            # Confirm writability without removing or moving anyone else's cache.
            probe = home / ("write-probe-" + uuid.uuid4().hex)
            with probe.open("xb") as stream:
                stream.write(b"")
            probe.unlink()
            row["usable"] = True
            return home, observations
        except OSError as exc:
            row["reason"] = type(exc).__name__
    message = "No writable scratch volume has 30 GiB free. No model download started; do not remove the guard."
    error = RuntimeError(message)
    error.observations = observations
    raise error


def validate_scratch_resume(work):
    work = Path(work)
    log = work / "setup-evidence/base_download.log"
    if not log.is_file() or SCRATCH_FAILURE not in log.read_text(encoding="utf-8"):
        raise RuntimeError("Resume is allowed only for the confirmed pre-download scratch failure.")
    if (work / "results").exists():
        raise RuntimeError("Results already exist; refuse to rerun or replace an inference experiment.")
    if not (work / "candidate.json").is_file() or not (work / "overlay").is_dir():
        raise RuntimeError("Original pilot source inventory is missing.")
    return log


def bootstrap(resume=False):
    check_ports()
    if resume:
        validate_scratch_resume(ROOT.parent)
        output = ROOT.parent / "setup-evidence" / ("scratch-recovery-" + uuid.uuid4().hex[:10])
        print("STYLE_PILOT RECOVERY: reuse installed packages; recheck host/artifacts; preserve old logs.", flush=True)
    else:
        output = ROOT.parent / "setup-evidence"
    output.mkdir(exist_ok=False)
    # Check original archives/artifacts before experimental source overlays.
    _, review = original.verify_bundle()
    expected = review["environment"]
    env = clean_environment(os.environ)
    probe = "import json,platform,torch;print(json.dumps({'python':platform.python_version(),'torch':torch.__version__,'cuda':torch.version.cuda,'gpu':torch.cuda.get_device_name(0) if torch.cuda.is_available() else None}))"
    check = subprocess.run([sys.executable, "-c", probe], cwd=ROOT, env=env,
                           capture_output=True, text=True, check=True)
    host = json.loads(check.stdout.strip().splitlines()[-1])
    (output / "host.json").write_text(json.dumps(host, indent=2) + "\n")
    if any(host[k] != expected[k] for k in ("python", "torch", "cuda", "gpu")):
        raise RuntimeError("Host differs from reviewed image. Keep pins; inspect setup-evidence/host.json.")
    if not resume:
        constraints = [f"torch=={expected['torch']}"]
        for name in ("torchvision", "torchaudio"):
            try:
                constraints.append(f"{name}=={metadata.version(name)}")
            except metadata.PackageNotFoundError:
                pass
        path = output / "torch_constraints.txt"
        path.write_text("\n".join(constraints) + "\n")
        try:
            metadata.version("torchao")
        except metadata.PackageNotFoundError:
            pass
        else:
            original.run([sys.executable, "-m", "pip", "uninstall", "-y", "torchao"],
                         output, "optional_torchao.log", env)
        original.run([sys.executable, "-m", "pip", "install", "--constraint", str(path),
                      "-r", str(ROOT / "scripts/unified_gate3_requirements.txt")],
                     output, "dependency_install.log", env)
    original.run([sys.executable, str(ROOT / "scripts/unified_gate2.py"), "--environment-only"],
                 output, "environment.log", env)
    observed = json.loads((output / "environment.log").read_text().strip().splitlines()[-1])
    if any(observed.get(k) != expected.get(k) for k in ("python", "packages", "diffusers_commit", "torch", "cuda", "gpu")):
        raise RuntimeError("Resolved environment differs; stop rather than force the model to run.")
    original.run([sys.executable, str(ROOT / "scripts/unified_gate2.py"), "--verify-only"],
                 output, "artifact_preflight.log", env)
    try:
        cache_home, space = select_cache_home(ROOT.parent)
    except RuntimeError as exc:
        (output / "scratch.json").write_text(json.dumps(
            {"status": "INSUFFICIENT_SCRATCH", "volumes": getattr(exc, "observations", [])}, indent=2) + "\n")
        raise
    env["HF_HOME"] = str(cache_home)
    cache = cache_home / "hub"
    cache.mkdir(parents=True, exist_ok=True)
    (output / "scratch.json").write_text(json.dumps(
        {"status": "SELECTED", "cache": str(cache), "minimum_free_bytes": MIN_SCRATCH_BYTES,
         "volumes": space}, indent=2) + "\n")
    original.run([sys.executable, str(ROOT / "scripts/unified_gate1_bootstrap.py"),
                  "--download-only", "--output", str(output / "model.json"), "--cache", str(cache)],
                 output, "base_download.log", env)
    model = json.loads((output / "model.json").read_text())
    if model["model_index_sha256"] != review["base_model_index_sha256"]:
        raise RuntimeError("Pinned model index differs")
    inventory = json.loads((ROOT.parent / "candidate.json").read_text())
    for name, record in inventory.items():
        raw = original.gate.safe_path(ROOT.parent / "overlay", name).read_bytes()
        if sha256(raw).hexdigest() != record["sha256"]:
            raise ValueError("Pilot source differs")
        target = original.gate.safe_path(ROOT, name)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    original.run([sys.executable, str(ROOT / "scripts/style_expansion_nails.py"),
                  "--source", str(ROOT.parent / "fixtures/hand.png"),
                  "--mask", str(ROOT.parent / "fixtures/mask.png"),
                  "--output", str(ROOT.parent / "results/nails")],
                 output, "nails_renderer.log", env)
    from scripts.capstone_train002_bootstrap import worker_environment
    env = worker_environment({**env, "AI_MODEL_DIR": model["snapshot"],
                              "AI_REMOTE_API_KEY": secrets.token_hex(32)})
    # No HTTP process: keep all inference inside this single private child.
    log_path = output / "pilot.log"
    with log_path.open("w", encoding="utf-8") as log:
        process = subprocess.Popen([sys.executable, str(ROOT / "scripts/style_expansion_pilot.py"),
                                    "--output", str(ROOT.parent / "results/portraits")],
                                   cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in process.stdout:
            log.write(line)
            log.flush()
            if line.startswith("STYLE_PILOT"):
                print(line.rstrip(), flush=True)
        if process.wait():
            raise RuntimeError("Portrait pilot failed; inspect pilot.log and partial results.")
    print("STYLE_PILOT FINISHED: inspect images; no styles have been enabled.", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resume-after-scratch-failure", action="store_true")
    args = parser.parse_args()
    if args.resume_after_scratch_failure:
        lock = ROOT.parent / ".style-expansion-scratch-recovery.lock"
        # Atomic ownership: a second recovery cannot start over this one.
        with lock.open("x", encoding="utf-8") as stream:
            stream.write(str(os.getpid()))
        try:
            bootstrap(resume=True)
        finally:
            lock.unlink()
    else:
        bootstrap()
