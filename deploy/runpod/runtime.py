"""Runpod orchestration. Existing model, release and application code is reused."""
import argparse
from contextlib import contextmanager
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import platform
import re
import signal
import socket
import subprocess
import sys
import time
from urllib.request import Request, HTTPRedirectHandler, build_opener, urlopen
from uuid import uuid4

HERE = Path(__file__).resolve().parent


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify_distribution(root=HERE):
    root = Path(root).resolve()
    manifest = json.loads((root / "build-manifest.json").read_text())
    if manifest.get("schema") != "beautycore-runpod-build-v1":
        raise ValueError("Wrong Runpod build manifest")
    for name, expected in manifest["files"].items():
        path = (root / name).resolve()
        if not path.is_relative_to(root) or sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError("Runpod distribution changed: " + name)
    return manifest


def assemble(inputs, work, *, root=HERE):
    verify_distribution(root)
    setup = load_module("release_setup", Path(root) / "release_setup.py")
    inputs, work = Path(inputs), Path(work)
    if work.exists():
        raise ValueError("Run directory must be new")
    # Check both private archives before extracting either one.
    for name, expected, _, _ in setup.BUNDLES:
        path = inputs / name
        if not path.is_file() or sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError("Private input missing or changed: " + name)
    work.mkdir(parents=True, mode=0o700)
    for name, expected, directory, manifest in setup.BUNDLES:
        setup.extract(inputs / name, expected, work / directory, manifest)
    setup.verify_release_pair(work, setup.STYLE_RELEASE_EXPECTED)
    cpu = json.loads((work / "cpu-src/demo_bundle.json").read_text())
    if cpu.get("worker_sources") != {name: row["sha256"] for name, row in setup.OPTIMIZED_SOURCES.items()}:
        raise ValueError("CPU and worker source pair differs")
    setup.stage_overlay(work, setup.OPTIMIZED_SOURCES)
    return setup


def usable_memory(proc=Path("/proc/meminfo"), cgroup=Path("/sys/fs/cgroup")):
    memory = int(re.search(r"MemTotal:\s+(\d+)", proc.read_text())[1]) * 1024
    for relative in ("memory.max", "memory/memory.limit_in_bytes"):
        path = cgroup / relative
        if path.is_file():
            value = path.read_text().strip()
            if value.isdigit():
                memory = min(memory, int(value))
    return memory


def check_profile(actual, reviewed, profile, memory):
    if profile.get("schema") != "beautycore-runpod-profile-v1":
        raise ValueError("Wrong Runpod runtime profile")
    for key in ("python", "torch", "cuda", "gpu"):
        if actual.get(key) != profile[key]:
            raise ValueError("Runpod runtime differs: " + key)
    for key in ("packages", "diffusers_commit"):
        if actual.get(key) != reviewed.get(key):
            raise ValueError("Reviewed GPU dependencies differ: " + key)
    if (not actual.get("cuda_available") or memory < profile["minimum_ram_bytes"]
            or actual.get("gpu_total_bytes", 0) < profile["minimum_vram_bytes"]
            or tuple(actual.get("compute_capability", ())) < tuple(profile["minimum_compute_capability"])):
        raise ValueError("Runpod CUDA or allocated RAM/VRAM is insufficient")
    return actual


def check_readiness(readiness, expected, catalog):
    if not isinstance(readiness, dict):
        raise ValueError("Malformed Runpod readiness")
    cap = readiness.get("style_capabilities", {})
    if not isinstance(cap, dict) or not isinstance(cap.get("model_styles"), dict):
        raise ValueError("Malformed Runpod catalog")
    models = cap.get("model_styles", {})
    if (not readiness.get("ready") or readiness.get("foundation_load_count") != 1
            or cap.get("release_id") != expected["release_id"]
            or cap.get("manifest_sha256") != expected["manifest_sha256"]):
        raise ValueError("Runpod facade release/readiness differs")
    for feature, count in (("hairstyle", 18), ("makeup", 13), ("nails", 2)):
        values = models.get(feature, [])
        if not isinstance(values, list) or len(values) != count or len(set(values)) != count:
            raise ValueError("Runpod model catalog differs: " + feature)
    rendered = cap.get("renderer_styles", [])
    if not isinstance(rendered, list) or len(rendered) != 6 or len(set(rendered)) != 6:
        raise ValueError("Runpod rendered Nails catalog differs")
    installed = rendered + models["hairstyle"] + models["makeup"]
    if not set(expected["enabled_style_ids"]).issubset(installed):
        raise ValueError("Runpod expansion catalog incomplete")
    if ({key: sorted(value) for key, value in models.items()} != catalog["model_styles"]
            or sorted(rendered) != catalog["renderer_styles"]):
        raise ValueError("Runpod catalog IDs differ from the matching Render release")
    return cap


def secret_environment(env):
    for key, minimum in (("AI_BACKEND_API_KEY", 32), ("AI_REMOTE_API_KEY", 24), ("GEMINI_API_KEY", 1)):
        if len(env.get(key, "")) < minimum:
            raise ValueError("Configure private environment variable: " + key)


def write_record(path, record):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def request_json(url, key=None):
    headers = {"x-ai-backend-key": key, "x-ai-user-id": "demo-operator"} if key else {}
    with build_opener(NoRedirect()).open(Request(url, headers=headers), timeout=30) as response:
        raw = response.read(65537)
        if len(raw) > 65536:
            raise ValueError("Readiness response too large")
        return json.loads(raw)


@contextmanager
def exclusive_lock(path):
    import fcntl
    with Path(path).open("a") as file:
        try:
            fcntl.flock(file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError("A Runpod startup/server already owns this workspace") from None
        try:
            yield
        finally:
            fcntl.flock(file, fcntl.LOCK_UN)


def stop_process(process):
    if process.poll() is None:
        os.killpg(process.pid, signal.SIGTERM)
        try:
            process.wait(timeout=15)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()


def wait_for(url, children, *, key=None, seconds=900, read=request_json, sleep=time.sleep, now=time.monotonic):
    deadline = now() + seconds
    while now() < deadline:
        if any(child.poll() is not None for child in children):
            raise RuntimeError("Owned service exited; inspect private run logs")
        try:
            response = read(url, key)
            if response.get("ready") or response.get("status") in ("ready", "ok"):
                return response
        except (OSError, ValueError):
            pass
        sleep(3)
    raise RuntimeError("Service readiness timed out; inspect private run logs")


def gpu_worker(work, cache):
    work, cache = Path(work).resolve(), Path(cache).resolve()
    gpu = work / "gpu-src"
    sys.path[:0] = [str(gpu), str(gpu / "backend")]
    from scripts import unified_gate3_bootstrap as original
    from scripts import unified_gate1_bootstrap as downloader
    from scripts import unified_gate2
    from scripts.capstone_train002_bootstrap import worker_environment
    setup = load_module("release_setup_gpu", HERE / "release_setup.py")
    output = work / "gpu-session"
    output.mkdir()
    pid = None
    try:
        _, review = original.verify_bundle()
        actual = original.gate.environment()
        import torch
        actual["compute_capability"] = list(torch.cuda.get_device_capability(0))
        check_profile(actual, review["environment"], json.loads((HERE / "profile.json").read_text()), usable_memory())
        write_record(output / "runpod-environment.json", actual)
        # Historical evidence is checked BEFORE applying the reviewed release overlays.
        unified_gate2.verify_experiment()
        cache.mkdir(parents=True, exist_ok=True)
        downloader.download_model(output / "model.json", cache)
        model = json.loads((output / "model.json").read_text())
        if model["model_index_sha256"] != review["base_model_index_sha256"]:
            raise ValueError("Pinned Base index differs")
        setup.install_overlay(gpu, work / "optimized-worker.json", output)
        setup.install_candidate(gpu, work / "cpu-src", output)
        env = worker_environment(dict(os.environ, AI_MODEL_DIR=model["snapshot"], HF_HOME=str(cache.parent),
                                     AI_PROMPT_CACHE="1", AI_PROMPT_CACHE_SCOPE="nails", AI_INFERENCE_PROFILE="0"))
        original.start_server(output, env)
        pid = json.loads((output / "server_process.json").read_text())["pid"]
        while True:
            if os.waitpid(pid, os.WNOHANG)[0] == pid:
                raise RuntimeError("GPU worker stopped")
            time.sleep(3)
    finally:
        record = output / "server_process.json"
        if record.is_file():
            pid = json.loads(record.read_text())["pid"]
            try:
                os.killpg(pid, signal.SIGTERM)
            except ProcessLookupError:
                pass


def serve(workspace, inputs):
    workspace = Path(workspace).resolve()
    workspace.mkdir(parents=True, exist_ok=True, mode=0o700)
    manifest = verify_distribution()
    secret_environment(os.environ)
    registrar = load_module("registrar", HERE / "registration.py")
    website = os.environ.get("BEAUTYCORE_PUBLIC_URL", "").strip()
    if website:
        registrar.website_root(website)
    if sys.platform != "linux" or platform.machine() not in ("x86_64", "AMD64"):
        raise RuntimeError("The Runpod candidate requires Linux amd64")
    profile = json.loads((HERE / "profile.json").read_text())
    if usable_memory() < profile["minimum_ram_bytes"]:
        raise ValueError("At least 30 GiB allocated system RAM is required")
    with exclusive_lock(workspace / "server.lock"):
        for port in (8765, 8800):
            with socket.socket() as connection:
                if connection.connect_ex(("127.0.0.1", port)) == 0:
                    raise RuntimeError("An AI service is already running")
        work = workspace / "runs" / uuid4().hex
        setup = assemble(inputs, work)
        record_path = work / "session.json"
        record = {"status": "STARTING", "provider": "runpod", "session_id": str(uuid4()),
                  "started_at": int(time.time()), "release_id": setup.STYLE_RELEASE_EXPECTED["release_id"],
                  "gpu_validated": False, "full_generation_verified": False}
        write_record(record_path, record)
        (workspace / "latest-run.txt").write_text(str(work), encoding="utf-8")
        children, logs = [], []
        def spawn(args, name, cwd, env):
            log = (work / (name + ".log")).open("w")
            logs.append(log)
            process = subprocess.Popen(args, cwd=cwd, env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            children.append(process)
            return process
        try:
            env = dict(os.environ, PYTHONUNBUFFERED="1")
            cpu = work / "cpu-src"
            cpu_env = dict(env, CUDA_VISIBLE_DEVICES="", OMP_NUM_THREADS="1", MKL_NUM_THREADS="1", MPLBACKEND="Agg",
                PYTHONPATH=str(cpu / "backend"), AI_GPU_LOOPBACK="1", AI_REMOTE_URL="http://127.0.0.1:8765",
                GENERATION_ENGINE="remote_flux", MAKEUP_GENERATION_ENGINE="remote_makeup", NAILS_PREVIEW_MODE="hybrid",
                NAILS_INFERENCE_STEPS="8", NAILS_SEGMENT_PYTHON="/opt/segment/bin/python",
                NAILS_HAND_LANDMARKER_PATH=str(cpu / "data/nails/checkpoints/mediapipe/hand_landmarker.task"),
                NAILS_SEGMENT_CHECKPOINT=str(cpu / "data/nails/checkpoints/mnemic/nails_seg_s_yolov8_v1.pt"),
                CONSULTATION_PROVIDER="gemini", CONSULTATION_GEMINI_MODEL="gemini-3.5-flash-lite",
                HAIRCAPSTONE_STYLE_REGISTRY_PATH=str(cpu / "backend/app/style_registry_train002_smoke.json"), FRONTEND_ORIGINS="")
            probes = [
                (["/opt/segment/bin/python", "-c", "import torch, torchvision; from ultralytics import YOLO; "
                  "assert torchvision.extension._has_ops(); assert '+cpu' in torch.__version__; YOLO(" +
                  repr(cpu_env["NAILS_SEGMENT_CHECKPOINT"]) + ")"], "segment-load"),
                (["/opt/api/bin/python", "-c", "from pathlib import Path; from app.nails.geometry import MediaPipeHandLocalizer; "
                  "MediaPipeHandLocalizer(Path(" + repr(cpu_env["NAILS_HAND_LANDMARKER_PATH"]) + "))"], "landmark-load")]
            for command, name in probes:
                with (work / (name + ".log")).open("w") as log:
                    subprocess.run(command, cwd=cpu, env=cpu_env, stdout=log, stderr=subprocess.STDOUT,
                                   check=True, timeout=180)
            gpu = spawn([sys.executable, str(HERE / "runtime.py"), "gpu", "--work", str(work),
                         "--cache", str(workspace / "hf-cache/hub")], "gpu", work / "gpu-src", env)
            wait_for("http://127.0.0.1:8765/health", children)
            api = spawn(["/opt/api/bin/python", "-m", "uvicorn", "app.demo_server:app", "--host", "127.0.0.1",
                         "--port", "8800", "--workers", "1"], "api", cpu, cpu_env)
            readiness = wait_for("http://127.0.0.1:8800/deployment/readiness", children,
                                 key=env["AI_BACKEND_API_KEY"], seconds=180)
            check_readiness(readiness, setup.STYLE_RELEASE_EXPECTED, manifest["catalog"])
            record.update(status="LOCAL_READY", api_pid=api.pid, gpu_pid=gpu.pid, readiness=readiness)
            write_record(record_path, record)
            # Same endpoint type already accepted by Render. GPU port remains private.
            binary = workspace / "cloudflared"
            if not binary.exists():
                with urlopen("https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64", timeout=90) as response:
                    temporary = binary.with_suffix(".download")
                    temporary.write_bytes(response.read())
                    temporary.chmod(0o700)
                    temporary.replace(binary)
            tunnel = spawn([str(binary), "tunnel", "--url", "http://127.0.0.1:8800"], "tunnel", work, env)
            deadline = time.monotonic() + 240
            while True:
                if any(p.poll() is not None for p in children):
                    raise RuntimeError("Owned service exited")
                match = re.search(r"https://[a-z0-9-]+\.trycloudflare\.com", (work / "tunnel.log").read_text())
                if match:
                    break
                if time.monotonic() >= deadline:
                    raise RuntimeError("Tunnel address timed out")
                time.sleep(2)
            endpoint = match[0]
            public = wait_for(endpoint + "/deployment/readiness", children, key=env["AI_BACKEND_API_KEY"], seconds=120)
            check_readiness(public, setup.STYLE_RELEASE_EXPECTED, manifest["catalog"])
            record.update(url=endpoint, tunnel_pid=tunnel.pid, status="READY_FOR_RUNPOD_VALIDATION")
            write_record(record_path, record)
            if website:
                ack = registrar.register(website, record, env["AI_BACKEND_API_KEY"])
                record.update(status="CONNECTED_TO_WEBSITE", registration_expires_at=ack["expires_at"])
                write_record(record_path, record)
                spawn([sys.executable, str(HERE / "registration.py"), website, str(record_path)], "registration", work, env)
            print(record["status"], "Release:", record["release_id"], "Run:", work, flush=True)
            print("Catalog: 18 Hair, 13 Makeup, 8 Nails. No real generation acceptance is implied.", flush=True)
            while True:
                if any(p.poll() is not None for p in children):
                    raise RuntimeError("An owned service stopped; lease will expire")
                time.sleep(3)
        except BaseException:
            record["status"] = "STOPPED_OR_FAILED"
            write_record(record_path, record)
            raise
        finally:
            for child in reversed(children):
                stop_process(child)
            worker_record = work / "gpu-session/server_process.json"
            if worker_record.is_file():
                # The GPU helper's child has its own process group. Also clean it
                # up if the helper had to be killed before reaching its finally.
                pid = json.loads(worker_record.read_text())["pid"]
                if isinstance(pid, int) and pid > 1 and pid != os.getpid():
                    try:
                        os.killpg(pid, signal.SIGTERM)
                    except ProcessLookupError:
                        pass
            for log in logs:
                log.close()


def notebook(workspace):
    password = os.environ.get("JUPYTER_PASSWORD", "")
    if len(password) < 16:
        raise ValueError("Set JUPYTER_PASSWORD of at least 16 characters for browser setup")
    workspace = Path(workspace).resolve()
    workspace.mkdir(parents=True, exist_ok=True, mode=0o700)
    # Hash the password in the isolated notebook interpreter. Never put it in argv/logs.
    result = subprocess.run(["/opt/notebook/bin/python", "-c",
        "import os; from jupyter_server.auth import passwd; print(passwd(os.environ['JUPYTER_PASSWORD']))"],
        capture_output=True, text=True, check=True)
    config = workspace / ".jupyter-config.py"
    config.write_text("from jupyter_server.auth.identity import PasswordIdentityProvider\n"
        "c.ServerApp.identity_provider_class = PasswordIdentityProvider\n"
        "c.PasswordIdentityProvider.hashed_password = " + repr(result.stdout.strip()) + "\n"
        "c.ServerApp.root_dir = '/workspace'\n", encoding="utf-8")
    config.chmod(0o600)
    os.execv("/opt/notebook/bin/jupyter-lab", ["jupyter-lab", "--config", str(config), "--ip=0.0.0.0",
             "--port=8888", "--no-browser", "--allow-root", "--log-level=WARN"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("notebook", "start", "stage", "gpu"))
    parser.add_argument("--workspace", type=Path, default=Path(os.environ.get("RUNPOD_WORKSPACE", "/workspace/beautycore")))
    parser.add_argument("--inputs", type=Path)
    parser.add_argument("--work", type=Path)
    parser.add_argument("--cache", type=Path)
    args = parser.parse_args()
    if args.mode in ("start", "gpu"):
        def handle_stop(*_):
            raise KeyboardInterrupt()
        signal.signal(signal.SIGTERM, handle_stop)
    if args.mode == "notebook":
        notebook(args.workspace)
    elif args.mode == "stage":
        assemble(args.inputs or args.workspace / "inputs", args.work or args.workspace / "stage-check")
        print("Release inputs verified and staged. No GPU started.")
    elif args.mode == "gpu":
        gpu_worker(args.work, args.cache)
    else:
        serve(args.workspace, args.inputs or args.workspace / "inputs")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as error:
        # Do not echo arbitrary provider exceptions or credentials.
        print("Runpod startup stopped:", type(error).__name__, ". Inspect the private run logs and setup guide.", file=sys.stderr)
        sys.exit(1)
