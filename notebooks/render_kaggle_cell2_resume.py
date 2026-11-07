# Replacement Cell 2 for the recorded MediaPipe/Matplotlib startup failure.
from pathlib import Path
import importlib.util, json, socket, uuid

WORK = Path("/kaggle/working/render-kaggle")
marker = WORK / "demo-session.json"
log = WORK / "landmark-load.log"
if not marker.is_file() or not log.is_file():
    raise RuntimeError("Expected failed landmark startup record is missing.")
record = json.loads(marker.read_text())
if record.get("status") != "starting" or set(record) != {"status", "host_ram_bytes"}:
    raise RuntimeError("This session is not a failed startup; resume stopped.")
error = log.read_text()
if "ValueError: Key backend:" not in error or "matplotlib_inline.backend_inline" not in error:
    raise RuntimeError("This is a different landmark failure; inspect its log.")

for port in (8765, 8800):
    with socket.socket() as connection:
        connection.settimeout(1)
        if connection.connect_ex(("127.0.0.1", port)) == 0:
            raise RuntimeError("An AI service is already running; resume stopped.")
if any((WORK / name).exists() for name in ("gpu-bootstrap.log", "gpu-session", "api.log", "tunnel.log")):
    raise RuntimeError("GPU/API startup was already attempted; resume stopped.")
for name in ("backend-env", "segment-env"):
    if not (WORK / name / "bin/python").is_file():
        raise RuntimeError("An installed CPU environment is missing.")

path = WORK / "cpu-src/scripts/render_kaggle_bootstrap.py"
spec = importlib.util.spec_from_file_location("demo_landmark_resume", path)
demo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(demo)
original_command = demo.command
completed_installs = {
    "backend-env-create", "segment-env-create",
    "backend-env-pip-bootstrap", "segment-env-pip-bootstrap",
    "backend-install", "segment-torch-install", "segment-install",
}

def resume_command(args, cwd, env, stage):
    # Change only the CPU environment; GPU host settings stay intact.
    if stage not in ("gpu-bootstrap", "portaudio-index", "portaudio-install"):
        env["MPLBACKEND"] = "Agg"
    if stage in completed_installs:
        print("REUSING INSTALLED ENVIRONMENT:", stage, flush=True)
        return
    try:
        original_command(args, cwd, env, stage)
    except RuntimeError:
        # Display this known CPU error log, without dumping environment variables.
        if stage == "landmark-load":
            print((WORK / "landmark-load.log").read_text()[-12000:], flush=True)
        raise

demo.command = resume_command
marker.rename(WORK / ("failed-before-landmark-" + uuid.uuid4().hex + ".json"))
print("Rechecking installed CPU packages and models with MPLBACKEND=Agg, then continuing startup.", flush=True)
demo.main()
