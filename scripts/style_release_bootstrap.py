"""Fresh private STYLE-VAL-001 setup with original model/environment guards."""
from importlib import metadata
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import unified_gate3_bootstrap as original


def bootstrap():
    # Helper is hash-checked by notebook preparation; it creates no service.
    from scripts.style_expansion_bootstrap import check_ports, clean_environment, select_cache_home
    check_ports()
    output = ROOT.parent / "setup-evidence"
    output.mkdir(exist_ok=False)
    _, review = original.verify_bundle()
    expected = review["environment"]
    env = clean_environment(os.environ)
    probe = "import json,platform,torch;print(json.dumps({'python':platform.python_version(),'torch':torch.__version__,'cuda':torch.version.cuda,'gpu':torch.cuda.get_device_name(0) if torch.cuda.is_available() else None}))"
    observed = subprocess.run([sys.executable, "-c", probe], cwd=ROOT, env=env,
                              capture_output=True, text=True, check=True)
    host = json.loads(observed.stdout.strip().splitlines()[-1])
    (output / "host.json").write_text(json.dumps(host, indent=2) + "\n")
    if any(host[k] != expected[k] for k in ("python", "torch", "cuda", "gpu")):
        raise RuntimeError("Host differs from reviewed image; preserve pins and inspect host.json")
    home, observations = select_cache_home(ROOT.parent)
    env["HF_HOME"] = str(home)
    (output / "scratch.json").write_text(json.dumps({"cache_home": str(home), "volumes": observations}, indent=2) + "\n")
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
        original.run([sys.executable, "-m", "pip", "uninstall", "-y", "torchao"], output, "optional_torchao.log", env)
    original.run([sys.executable, "-m", "pip", "install", "--constraint", str(path),
                  "-r", str(ROOT / "scripts/unified_gate3_requirements.txt")], output, "dependency_install.log", env)
    original.run([sys.executable, str(ROOT / "scripts/unified_gate2.py"), "--environment-only"],
                 output, "environment.log", env)
    resolved = json.loads((output / "environment.log").read_text().strip().splitlines()[-1])
    if any(resolved.get(k) != expected.get(k) for k in ("python", "packages", "diffusers_commit", "torch", "cuda", "gpu")):
        raise RuntimeError("Installed environment differs; no diagnostic run")
    original.run([sys.executable, str(ROOT / "scripts/unified_gate2.py"), "--verify-only"],
                 output, "artifact_preflight.log", env)
    # Recheck free bytes after installing dependencies.
    home, observations = select_cache_home(ROOT.parent)
    env["HF_HOME"] = str(home)
    (output / "scratch.json").write_text(json.dumps({"cache_home": str(home), "volumes": observations}, indent=2) + "\n")
    cache = home / "hub"
    cache.mkdir(parents=True, exist_ok=True)
    original.run([sys.executable, str(ROOT / "scripts/unified_gate1_bootstrap.py"), "--download-only",
                  "--output", str(output / "model.json"), "--cache", str(cache)], output, "base_download.log", env)
    model = json.loads((output / "model.json").read_text())
    if model["model_index_sha256"] != review["base_model_index_sha256"]:
        raise RuntimeError("Pinned model index differs")
    inventory = json.loads((ROOT.parent / "candidate.json").read_text())
    for name, row in inventory.items():
        raw = original.gate.safe_path(ROOT.parent / "overlay", name).read_bytes()
        if sha256(raw).hexdigest() != row["sha256"]:
            raise RuntimeError("Diagnostic source integrity failed")
        target = original.gate.safe_path(ROOT, name)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    env["AI_MODEL_DIR"] = model["snapshot"]
    with (output / "diagnostic.log").open("w", encoding="utf-8") as log:
        process = subprocess.Popen([sys.executable, str(ROOT / "scripts/style_release_validation.py"),
                                    "--output", str(ROOT.parent / "results")],
                                   cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in process.stdout:
            log.write(line)
            log.flush()
            if line.startswith("STYLE_VALIDATION"):
                print(line.rstrip(), flush=True)
        if process.wait():
            raise RuntimeError("Release validation failed; inspect partial results and diagnostic.log")
    print("STYLE_VALIDATION FINISHED: review styles, preservation and existing presets before enabling options.", flush=True)


if __name__ == "__main__":
    bootstrap()
