"""New scheduled-demo runner. Existing notebooks and GPU bundle are not modified."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from urllib.request import Request, urlopen

WORK = Path("/kaggle/working/render-kaggle")
GPU_ROOT = WORK / "gpu-src"
CPU_ROOT = WORK / "cpu-src"
PORT = 8800


def command(args, cwd, env, stage):
    print("DEMO STAGE:", stage, flush=True)
    log = WORK / (stage + ".log")
    with log.open("w") as output:
        process = subprocess.Popen(args, cwd=cwd, env=env, stdout=output, stderr=subprocess.STDOUT)
        while process.poll() is None:
            try:
                process.wait(timeout=30)
            except subprocess.TimeoutExpired:
                print(stage, "still running; log bytes:", log.stat().st_size, flush=True)
    if process.returncode:
        raise RuntimeError(stage + " failed; inspect its log")


def read_json(url, key=None):
    headers = {"x-ai-backend-key": key, "x-ai-user-id": "demo-operator"} if key else {}
    with urlopen(Request(url, headers=headers), timeout=40) as response:
        return json.load(response)


def main():
    if sys.platform != "linux":
        raise RuntimeError("Run in the new Kaggle Linux GPU notebook")
    if (WORK / "demo-session.json").exists():
        raise RuntimeError("Refuse duplicate startup; use a fresh notebook session")
    # Total RAM, not VRAM. Old GPU evidence peaked near 23 GiB before CPU vision.
    memory = int(re.search(r"MemTotal:\s+(\d+)", Path("/proc/meminfo").read_text())[1]) * 1024
    if memory < 30 * 1024**3:
        raise RuntimeError("At least 30 GiB host RAM required for this unverified combined workload")
    from kaggle_secrets import UserSecretsClient
    secrets = UserSecretsClient()
    backend_key = secrets.get_secret("AI_BACKEND_API_KEY") or ""
    gpu_key = secrets.get_secret("AI_REMOTE_API_KEY") or ""
    gemini_key = secrets.get_secret("GEMINI_API_KEY") or ""
    if len(backend_key) < 32 or len(gpu_key) < 24 or not gemini_key:
        raise RuntimeError("Enable the three required Kaggle Secrets; never put keys into cells")
    # Reserve the session before starting any subprocess; failed sessions need a fresh restart.
    (WORK / "demo-session.json").write_text(json.dumps({"status": "starting", "host_ram_bytes": memory}))
    env = {**os.environ, "PYTHONUNBUFFERED": "1"}
    cpu_env = {**env, "CUDA_VISIBLE_DEVICES": "", "OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1"}
    import ctypes.util
    if not ctypes.util.find_library("portaudio"):
        command(["apt-get", "update"], CPU_ROOT, env, "portaudio-index")
        command(["apt-get", "install", "-y", "libportaudio2"], CPU_ROOT, env, "portaudio-install")
    for name in ("backend-env", "segment-env"):
        command([sys.executable, "-m", "venv", str(WORK / name)], CPU_ROOT, cpu_env, name + "-create")
    api_python = WORK / "backend-env/bin/python"
    seg_python = WORK / "segment-env/bin/python"
    command([str(api_python), "-m", "pip", "install", "-r", "backend/requirements-nails.txt", "--constraint", "backend/requirements-demo-constraints.txt"],
            CPU_ROOT, cpu_env, "backend-install")
    command([str(seg_python), "-m", "pip", "install", "torch==2.10.0", "torchvision==0.25.0", "--index-url", "https://download.pytorch.org/whl/cpu"],
            CPU_ROOT, cpu_env, "segment-torch-install")
    command([str(seg_python), "-m", "pip", "install", "-r", "backend/requirements-nails-segmenter.txt"],
            CPU_ROOT, cpu_env, "segment-install")
    for name, interpreter in (("backend", api_python), ("segment", seg_python)):
        command([str(interpreter), "-m", "pip", "check"], CPU_ROOT, cpu_env, name + "-pip-check")
    checkpoint = CPU_ROOT / "data/nails/checkpoints/mnemic/nails_seg_s_yolov8_v1.pt"
    command([str(seg_python), "-c", "import torch, torchvision; from ultralytics import YOLO; assert torchvision.extension._has_ops(); assert '+cpu' in torch.__version__; YOLO(" + repr(str(checkpoint)) + ")"],
            CPU_ROOT, cpu_env, "segment-load")
    landmark = CPU_ROOT / "data/nails/checkpoints/mediapipe/hand_landmarker.task"
    cpu_env["PYTHONPATH"] = str(CPU_ROOT / "backend")
    command([str(api_python), "-c", "from pathlib import Path; from app.nails.geometry import MediaPipeHandLocalizer; MediaPipeHandLocalizer(Path(" + repr(str(landmark)) + "))"],
            CPU_ROOT, cpu_env, "landmark-load")
    gpu_code = """from pathlib import Path
from scripts import unified_gate3_bootstrap as original
from scripts.capstone_train002_bootstrap import worker_environment
start = original.start_server
original.start_server = lambda output, env: start(output, worker_environment(env))
report = original.bootstrap(Path('/kaggle/working/render-kaggle/gpu-session'), local_only=True)
assert report['status'] == 'READY_FOR_LIVE_ACCEPTANCE', 'GPU bootstrap failed'
"""
    # Preserves exact host/package/model/adapter checks; one GPU load, no public GPU tunnel.
    command([sys.executable, "-c", gpu_code], GPU_ROOT,
            {**env, "AI_REMOTE_API_KEY": gpu_key}, "gpu-bootstrap")
    cpu_env.update(AI_BACKEND_API_KEY=backend_key, AI_GPU_LOOPBACK="1",
                   AI_REMOTE_URL="http://127.0.0.1:8765", AI_REMOTE_API_KEY=gpu_key,
                   GENERATION_ENGINE="remote_flux", MAKEUP_GENERATION_ENGINE="remote_makeup",
                   NAILS_PREVIEW_MODE="hybrid", NAILS_INFERENCE_STEPS="8",
                   NAILS_HAND_LANDMARKER_PATH=str(landmark), NAILS_SEGMENT_CHECKPOINT=str(checkpoint),
                   NAILS_SEGMENT_PYTHON=str(seg_python), CONSULTATION_PROVIDER="gemini",
                   CONSULTATION_GEMINI_MODEL="gemini-3.5-flash-lite", GEMINI_API_KEY=gemini_key,
                   HAIRCAPSTONE_STYLE_REGISTRY_PATH=str(CPU_ROOT / "backend/app/style_registry_train002_smoke.json"),
                   FRONTEND_ORIGINS="")
    with (WORK / "api.log").open("w") as log:
        api = subprocess.Popen([str(api_python), "-m", "uvicorn", "app.demo_server:app",
                                "--host", "127.0.0.1", "--port", str(PORT), "--workers", "1"],
                               cwd=CPU_ROOT, env=cpu_env, stdout=log, stderr=subprocess.STDOUT,
                               start_new_session=True)
    deadline = time.monotonic() + 120
    while True:
        if api.poll() is not None:
            raise RuntimeError("API exited; inspect api.log")
        try:
            if read_json(f"http://127.0.0.1:{PORT}/health")["status"] == "ok":
                break
        except Exception:
            pass
        if time.monotonic() >= deadline:
            raise RuntimeError("API did not start; inspect api.log")
        time.sleep(2)
    readiness = read_json(f"http://127.0.0.1:{PORT}/deployment/readiness", backend_key)
    if not readiness.get("ready"):
        raise RuntimeError("AI readiness failed; inspect API and GPU logs")
    # Bootstrap already downloaded cloudflared; point only at the authenticated facade.
    binary = WORK / "gpu-session/cloudflared"
    if not binary.exists():
        import shutil
        with urlopen("https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64", timeout=90) as source, binary.open("wb") as target:
            shutil.copyfileobj(source, target)
        binary.chmod(0o700)
    with (WORK / "tunnel.log").open("w") as log:
        tunnel = subprocess.Popen([str(binary), "tunnel", "--url", f"http://127.0.0.1:{PORT}"],
                                  cwd=WORK, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    deadline = time.monotonic() + 240
    while True:
        if tunnel.poll() is not None:
            raise RuntimeError("API tunnel exited; inspect tunnel.log")
        match = re.search(r"https://[a-z0-9-]+\.trycloudflare\.com", (WORK / "tunnel.log").read_text())
        if match:
            try:
                if read_json(match[0] + "/deployment/readiness", backend_key).get("ready"):
                    break
            except Exception:
                pass
        if time.monotonic() >= deadline:
            raise RuntimeError("Public API readiness failed; inspect tunnel.log")
        time.sleep(3)
    record = {"status": "READY_FOR_REHEARSAL", "url": match[0], "api_pid": api.pid,
              "tunnel_pid": tunnel.pid, "readiness": readiness, "host_ram_bytes": memory,
              "full_generation_verified": False}
    (WORK / "demo-session.json").write_text(json.dumps(record, indent=2))
    print("Render AI_FASTAPI_URL:", match[0], flush=True)
    print("READY_FOR_REHEARSAL: run the full application checklist before the defense.", flush=True)


if __name__ == "__main__":
    main()
