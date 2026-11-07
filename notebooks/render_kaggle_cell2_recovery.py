# Replacement Cell 2: recover only the recorded early ensurepip failure.
from pathlib import Path
import importlib.util, json, socket, sys, uuid

WORK = Path("/kaggle/working/render-kaggle")
marker = WORK / "demo-session.json"
log = WORK / "backend-env-create.log"

for port in (8765, 8800):
    with socket.socket() as connection:
        connection.settimeout(1)
        if connection.connect_ex(("127.0.0.1", port)) == 0:
            raise RuntimeError("An AI service is already running; recovery stopped.")

later = ("segment-env-create.log", "backend-install.log", "segment-torch-install.log",
         "segment-install.log", "gpu-bootstrap.log", "api.log", "tunnel.log", "gpu-session")
if any((WORK / name).exists() for name in later):
    raise RuntimeError("Startup progressed beyond this recovery; keep the current session and inspect its logs.")

if marker.exists():
    record = json.loads(marker.read_text())
    if (record.get("status") != "starting"
        or set(record) != {"status", "host_ram_bytes"}
        or not log.exists() or "ensurepip" not in log.read_text()):
        raise RuntimeError("This is not the recorded early ensurepip failure; recovery stopped.")

# Verify host pip supports installing into a separate Python environment.
import pip
version = tuple(int(part) for part in pip.__version__.split(".")[:2])
if version < (22, 3):
    raise RuntimeError("Host pip is too old for --python; report its version.")

path = WORK / "cpu-src/scripts/render_kaggle_bootstrap.py"
spec = importlib.util.spec_from_file_location("demo_recovery", path)
demo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(demo)
original_command = demo.command

def recovered_command(args, cwd, env, stage):
    if stage in ("backend-env-create", "segment-env-create"):
        name = stage.removesuffix("-create")
        target = WORK / name
        expected = [sys.executable, "-m", "venv", str(target)]
        if list(args) != expected:
            raise RuntimeError("Unexpected environment command; recovery stopped.")
        original_command([sys.executable, "-m", "venv", "--without-pip", str(target)], cwd, env, stage)
        original_command([sys.executable, "-m", "pip", "--python", str(target),
                          "install", "pip==25.3"], cwd, env, name + "-pip-bootstrap")
    else:
        original_command(args, cwd, env, stage)

demo.command = recovered_command
if marker.exists():
    marker.rename(WORK / ("failed-before-env-" + uuid.uuid4().hex + ".json"))
print("Resuming startup with isolated pip installation. Existing bundles are unchanged.", flush=True)
demo.main()
