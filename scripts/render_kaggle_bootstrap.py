"""New scheduled-demo runner. Existing notebooks and GPU bundle are not modified."""
import argparse
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
import time
from uuid import uuid4
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
    for port in (8765, PORT):
        with socket.socket() as connection:
            connection.settimeout(1)
            if connection.connect_ex(("127.0.0.1", port)) == 0:
                raise RuntimeError("An AI service is already running; do not start another worker")
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
    session_id = str(uuid4())
    started_at = int(time.time())
    # Reserve the session before starting any subprocess; failed sessions need a fresh restart.
    (WORK / "demo-session.json").write_text(json.dumps({"status": "starting", "host_ram_bytes": memory}))
    env = {**os.environ, "PYTHONUNBUFFERED": "1"}
    # CPU services do not use Kaggle's inline-notebook plotting backend.
    cpu_env = {**env, "CUDA_VISIBLE_DEVICES": "", "OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1", "MPLBACKEND": "Agg"}
    import ctypes.util
    if not ctypes.util.find_library("portaudio"):
        command(["apt-get", "update"], CPU_ROOT, env, "portaudio-index")
        command(["apt-get", "install", "-y", "libportaudio2"], CPU_ROOT, env, "portaudio-install")
    for name in ("backend-env", "segment-env"):
        # Kaggle ensurepip can fail even on the reviewed Python image.
        # Use host pip only as an installer targeting the isolated CPU environment.
        command([sys.executable, "-m", "venv", "--without-pip", str(WORK / name)], CPU_ROOT, cpu_env, name + "-create")
        command([sys.executable, "-m", "pip", "--python", str(WORK / name), "install", "pip==25.3"],
                CPU_ROOT, cpu_env, name + "-pip-bootstrap")
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
    gpu_code = f"""from pathlib import Path
from scripts import unified_gate3_bootstrap as original
from scripts.capstone_train002_bootstrap import worker_environment
start = original.start_server
original.start_server = lambda output, env: start(output, worker_environment(env))
report = original.bootstrap(Path({str(WORK / 'gpu-session')!r}), local_only=True)
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
    website = os.environ.get("BEAUTYCORE_PUBLIC_URL", "").strip()
    if website:
        import importlib.util
        registrar_path = WORK / "runtime_registration.py"
        if not registrar_path.is_file():
            raise RuntimeError("Automatic registration helper is missing; use the corrected client notebook")
        spec = importlib.util.spec_from_file_location("demo_registrar", registrar_path)
        registrar = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(registrar)
        record.update(session_id=session_id, started_at=started_at, status="AI_READY_CONNECTION_PENDING")
        (WORK / "demo-session.json").write_text(json.dumps(record, indent=2))
        try:
            ack = registrar.register(website, record, backend_key)
        except registrar.RegistrationError:
            print("AI is running, but website registration was not acknowledged. Inspect registration status; do not rerun GPU startup.", flush=True)
            raise
        record.update(status="CONNECTED_FOR_REHEARSAL", registration_expires_at=ack["expires_at"])
        (WORK / "demo-session.json").write_text(json.dumps(record, indent=2))
        with (WORK / "registration.log").open("w") as log:
            heartbeat = subprocess.Popen([sys.executable, str(registrar_path), website, str(WORK / "demo-session.json")],
                env={**env, "AI_BACKEND_API_KEY": backend_key}, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        record["heartbeat_pid"] = heartbeat.pid
        (WORK / "demo-session.json").write_text(json.dumps(record, indent=2))
        print("CONNECTED TO WEBSITE:", website, flush=True)
        print("No Render URL edit is needed. Keep the Kaggle session running.", flush=True)
    else:
        print("Render AI_FASTAPI_URL:", match[0], flush=True)
    print("READY_FOR_REHEARSAL: run the full application checklist before the defense.", flush=True)


if __name__ == "__main__":
    main()
