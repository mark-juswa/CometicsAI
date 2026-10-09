"""Verified private bundles and early host preflight for the client demo notebook."""
from pathlib import Path
from hashlib import sha256
from zipfile import ZipFile
import json, platform, socket, sys, uuid

BUNDLES = (
    ("capstone_train002_20260928_v1.bin", "f0d1fed52e00b6c5a1da2cade3731237675cdebbfc0b2cde3b2dbda99a4019ac", "gpu-src", "gate3_bundle.json"),
    ("render_kaggle_cpu_20261009.bin", "f391050851519e9cc1080830b615a6cc457b6dd1e21fde156522bb959fad9ede", "cpu-src", "demo_bundle.json"),
)

def extract(source, expected, target, manifest_name):
    if sha256(source.read_bytes()).hexdigest() != expected:
        raise RuntimeError("Bundle hash differs: " + source.name)
    if target.exists():
        raise RuntimeError("Extraction requires a new directory; existing source is never overwritten")
    with ZipFile(source) as archive:
        manifest = json.loads(archive.read(manifest_name))
        names = archive.namelist()
        if len(names) != len(set(names)) or set(names) != set(manifest["files"]) | {manifest_name}:
            raise RuntimeError("Bundle member list differs")
        if archive.testzip() is not None:
            raise RuntimeError("Bundle archive integrity failed")
        # Validate every member before writing any of the archive contents.
        members = []
        for name in names:
            destination = (target / name).resolve()
            if ":" in name or chr(92) in name or not destination.is_relative_to(target.resolve()):
                raise RuntimeError("Unsafe bundle member path")
            raw = archive.read(name)
            if name != manifest_name and sha256(raw).hexdigest() != manifest["files"][name]:
                raise RuntimeError("Bundle member hash differs: " + name)
            members.append((destination, raw))
        for destination, raw in members:
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(raw)

def check_host(observed, expected):
    if any(observed.get(key) != expected.get(key) for key in ("python", "torch", "cuda", "gpu")):
        raise RuntimeError("Kaggle image differs from the reviewed GPU image. Expected "
                           + json.dumps(expected) + "; observed " + json.dumps(observed)
                           + ". Use the tested pinned notebook; do not change the model guards.")

def prepare(inputs=Path("/kaggle/input"), working=Path("/kaggle/working")):
    if sys.platform != "linux":
        raise RuntimeError("Run this starter inside Kaggle, not on the client device")
    for port in (8765, 8800):
        with socket.socket() as connection:
            connection.settimeout(1)
            if connection.connect_ex(("127.0.0.1", port)) == 0:
                raise RuntimeError("An AI service is already running. Do not run setup again.")
    work = working / ("render-kaggle-client-" + uuid.uuid4().hex)
    for name, digest, directory, manifest in BUNDLES:
        matches = list(inputs.rglob(name))
        if len(matches) != 1:
            raise RuntimeError("Attach exactly one private input containing " + name)
        extract(matches[0], digest, work / directory, manifest)
    import torch
    observed = {"python": platform.python_version(), "torch": torch.__version__,
                "cuda": torch.version.cuda,
                "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None}
    review = json.loads((work / "gpu-src/docs/experiments/unified-kaggle-gate2-review.json").read_text())
    expected = {key: review["environment"][key] for key in observed}
    check_host(observed, expected)
    print("Private bundles and reviewed GPU host verified.", flush=True)
    print("Working directory:", work, flush=True)
    print("Run Cell 2 once. Keep this Kaggle session running during the demo.", flush=True)
    return work
