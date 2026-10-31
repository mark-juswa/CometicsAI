"""Stage one matched Hair/Nails worker release in a fresh verified GPU workspace."""
import base64
from hashlib import sha256
import json
from pathlib import Path
import socket

FILES = frozenset({
    "scripts/unified_gate3_server.py", "scripts/inference_performance.py", "scripts/hair_release_worker.py",
    "backend/app/hair_profiles.py", "backend/app/hair_profile.json",
    "backend/app/hair_profile_butterfly_cut.json", "backend/app/hair_profile_wolf_cut.json",
    "backend/app/hair_profile_korean_two_block.json", "backend/app/hair_profile_comma_hair.json",
    "backend/app/style_release.py", "backend/app/style_release.json",
})


def validated(payload):
    if not isinstance(payload, dict) or set(payload) != FILES:
        raise ValueError("Unexpected Hair/Nails worker source inventory")
    sources = {}
    for name, item in payload.items():
        if not isinstance(item, dict) or set(item) != {"data", "sha256"}:
            raise ValueError("Invalid release source record")
        raw = base64.b64decode(item["data"], validate=True)
        if sha256(raw).hexdigest() != item["sha256"]:
            raise ValueError("Release source hash differs: " + name)
        if name.endswith(".py"):
            compile(raw, name, "exec")
        else:
            json.loads(raw)
        sources[name] = raw
    return sources


def stage_overlay(work, payload):
    validated(payload)
    target = Path(work) / "optimized-worker.json"
    with target.open("x", encoding="utf-8") as file:
        json.dump(payload, file)
    return target


def install_overlay(root, payload_file, output):
    root, output = Path(root), Path(output)
    for port in (8765, 8800):
        with socket.socket() as connection:
            connection.settimeout(1)
            if connection.connect_ex(("127.0.0.1", port)) == 0:
                raise RuntimeError("Do not change a running AI service")
    record = output / "hair-nails-worker-release.json"
    if record.exists():
        raise RuntimeError("Worker release already installed; use a fresh session")
    sources = validated(json.loads(Path(payload_file).read_text(encoding="utf-8")))
    manifest_path = root / "gate3_bundle.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    # Full original bundle verification is also required by the startup hook.
    # Never rewrite the original manifest or any model/registry/checkpoint.
    for name in FILES:
        target = root / name
        if name in manifest["files"]:
            if sha256(target.read_bytes()).hexdigest() != manifest["files"][name]:
                raise ValueError("Original worker source changed before release install")
        elif target.exists():
            raise ValueError("Unexpected preexisting worker extension: " + name)
    for name, raw in sources.items():
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    evidence = {"schema": "beautycore-hair-nails-worker-v1",
                "original_manifest_sha256": sha256(manifest_path.read_bytes()).hexdigest(),
                "source_sha256": {name: sha256(raw).hexdigest() for name, raw in sources.items()},
                "model_parameters_changed": False,
                "hair_profile": "hair-expanded-v1", "optimization": "nails-only"}
    record.write_bytes((json.dumps(evidence, indent=2) + "\n").encode())
    print("WORKER RELEASE: approved Hair profiles and existing Nails-only optimization.", flush=True)
    return evidence
