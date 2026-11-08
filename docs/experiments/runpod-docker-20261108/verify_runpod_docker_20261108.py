"""Local Docker acceptance checks, no GPU inference or provider launch."""
from pathlib import Path
import json
import os
import secrets
import subprocess
import time
from uuid import uuid4
import httpx

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/runpod-build-20261108"
IMAGE = "beautycore-runpod:styles-20261106-01-build-20261108"
PROOF = OUT / "linux-proof"
PROOF.mkdir(exist_ok=False)
REPORT = {"image": IMAGE, "real_gpu_generation": False, "checks": {}}


def command(args, name, env=None):
    result = subprocess.run(["docker", *args], capture_output=True, env=env)
    (OUT / (name + ".log")).write_bytes(result.stdout + result.stderr)
    if result.returncode:
        raise RuntimeError(name + " failed, inspect its log")
    return result.stdout.decode("utf-8", errors="replace").strip()


def container_code(interpreter, code, name, extra=()):
    return command(["run", "--rm", *extra, "--entrypoint", interpreter, IMAGE, "-c", code], name)


try:
    text = container_code("python", "import sys,json,platform,importlib.metadata as m; "
        "sys.path.insert(0,'/opt/server'); import runtime; runtime.verify_distribution(); "
        "import torch; from diffusers import Flux2KleinPipeline; "
        "d=json.loads(m.distribution('diffusers').read_text('direct_url.json')); "
        "assert platform.python_version()=='3.12.13'; assert torch.__version__=='2.10.0+cu128'; "
        "assert torch.version.cuda=='12.8'; "
        "assert d['vcs_info']['commit_id']=='c943837899b16cbae2f619b8dd4f7bb6f07dd81a'; "
        "print(json.dumps({'python':platform.python_version(),'torch':torch.__version__,"
        "'cuda':torch.version.cuda,'cuda_available':torch.cuda.is_available(),'source_inventory':'PASS'}))",
        "image-imports")
    REPORT["checks"]["image_imports"] = json.loads(text)
    for name, interpreter in (("gpu", "python"), ("api", "/opt/api/bin/python"),
                              ("segment", "/opt/segment/bin/python"), ("notebook", "/opt/notebook/bin/python")):
        REPORT["checks"][name + "_pip_check"] = command(
            ["run", "--rm", "--entrypoint", interpreter, IMAGE, "-m", "pip", "check"], name + "-pip-check")
    mounts = ["--mount", f"type=bind,source={ROOT / 'client'},target=/inputs,readonly",
              "--mount", f"type=bind,source={PROOF},target=/proof"]
    command(["run", "--rm", *mounts, "--entrypoint", "python", IMAGE,
             "/opt/server/runtime.py", "stage", "--inputs", "/inputs", "--work", "/proof/staged"], "linux-stage")
    REPORT["checks"]["real_linux_archive_assembly"] = "PASS"
    container_code("python", "import sys,json; from pathlib import Path; "
        "sys.path[:0]=['/proof/staged/gpu-src','/proof/staged/gpu-src/backend','/opt/server']; "
        "from scripts import unified_gate3_bootstrap as original; "
        "_,review=original.verify_bundle(); actual=original.gate.environment(require_cuda=False); "
        "assert all(actual[k]==review['environment'][k] for k in ['python','packages','diffusers_commit','torch','cuda']); "
        "import release_setup as setup; output=Path('/proof/staged/overlay-proof'); output.mkdir(); "
        "setup.install_overlay(Path('/proof/staged/gpu-src'),Path('/proof/staged/optimized-worker.json'),output); "
        "setup.install_candidate(Path('/proof/staged/gpu-src'),Path('/proof/staged/cpu-src'),output); "
        "print('ARTIFACT_AND_GPU_PACKAGE_CONTRACT_PASS_NO_GPU_LOADED')",
        "linux-artifacts", mounts)
    REPORT["checks"]["original_artifacts_gpu_packages_and_overlays"] = "PASS"
    common = [*mounts, "-e", "CUDA_VISIBLE_DEVICES=", "-e", "MPLBACKEND=Agg",
              "-e", "PYTHONPATH=/proof/staged/cpu-src/backend", "-e", "OMP_NUM_THREADS=1"]
    container_code("/opt/segment/bin/python", "import torch,torchvision; from ultralytics import YOLO; "
        "assert '+cpu' in torch.__version__; assert torchvision.extension._has_ops(); "
        "YOLO('/proof/staged/cpu-src/data/nails/checkpoints/mnemic/nails_seg_s_yolov8_v1.pt'); print('YOLO_CPU_LOAD_PASS')",
        "linux-segment-model", common)
    REPORT["checks"]["real_cpu_segmenter_load"] = "PASS"
    container_code("/opt/api/bin/python", "from pathlib import Path; "
        "from app.nails.geometry import MediaPipeHandLocalizer; "
        "MediaPipeHandLocalizer(Path('/proof/staged/cpu-src/data/nails/checkpoints/mediapipe/hand_landmarker.task')); "
        "print('MEDIAPIPE_CPU_LOAD_PASS')", "linux-landmark-model", common)
    REPORT["checks"]["real_cpu_landmarker_load"] = "PASS"

    name = "beautycore-jupyter-proof-" + uuid4().hex[:10]
    password = secrets.token_urlsafe(24)
    env = dict(os.environ, JUPYTER_PASSWORD=password)
    created = False
    try:
        command(["run", "-d", "--name", name, "-p", "127.0.0.1::8888", "-e", "JUPYTER_PASSWORD", IMAGE],
                "notebook-container-start", env)
        created = True
        port = command(["port", name, "8888/tcp"], "notebook-port").splitlines()[0]
        base = "http://" + port
        with httpx.Client(base_url=base, timeout=10, follow_redirects=False) as client:
            deadline = time.monotonic() + 90
            while True:
                try:
                    login = client.get("/login")
                    if login.status_code == 200:
                        break
                except httpx.HTTPError:
                    pass
                if time.monotonic() > deadline:
                    raise RuntimeError("Jupyter login did not become available")
                time.sleep(2)
            anonymous = client.get("/api/contents")
            assert anonymous.status_code in (302, 401, 403)
            response = client.post("/login", data={"password": password, "_xsrf": client.cookies.get("_xsrf")},
                                   headers={"Referer": base + "/login"})
            assert response.status_code in (302, 303)
            authenticated = client.get("/api/contents")
            assert authenticated.status_code == 200
        REPORT["checks"]["jupyter_password_auth"] = {"anonymous_status": anonymous.status_code,
                                                     "authenticated_status": authenticated.status_code,
                                                     "password_not_logged": True}
    finally:
        if created:
            try:
                logs = command(["logs", name], "notebook-container")
                assert password not in logs
            finally:
                command(["rm", "-f", name], "notebook-container-cleanup")
    REPORT["status"] = "LOCAL_LINUX_IMAGE_PASS_GPU_ACCEPTANCE_PENDING"
except Exception as error:
    REPORT["status"] = "FAILED"
    REPORT["error"] = str(error)
    raise
finally:
    (OUT / "linux-verification.json").write_text(json.dumps(REPORT, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(REPORT, indent=2))
