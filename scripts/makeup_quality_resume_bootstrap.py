"""Guarded same-session continuation of the exact MAKEUP-QA-001 tensor failure."""
import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import unified_gate3_bootstrap as original


def resume(runner, output, evidence):
    from scripts.style_expansion_bootstrap import check_ports, clean_environment
    check_ports()
    runner, output, evidence = map(lambda p: Path(p).resolve(), (runner, output, evidence))
    work = ROOT.parent.resolve()
    if runner.parent != (ROOT / "scripts").resolve() or output.parent != work or output.exists():
        raise RuntimeError("Continuation paths are not fresh owned paths")
    evidence.relative_to(work / "setup-evidence")
    evidence.mkdir(exist_ok=False)
    _, review = original.verify_bundle()
    env = clean_environment(os.environ)
    original.run([sys.executable, str(ROOT / "scripts/unified_gate2.py"), "--environment-only"],
                 evidence, "environment.log", env)
    current = json.loads((evidence / "environment.log").read_text().strip().splitlines()[-1])
    expected = review["environment"]
    if any(current.get(k) != expected.get(k) for k in
           ("python", "packages", "diffusers_commit", "torch", "cuda", "gpu")):
        raise RuntimeError("Environment changed since the failed run; stop without reinstalling")
    original.run([sys.executable, str(ROOT / "scripts/unified_gate2.py"), "--verify-only"],
                 evidence, "artifact_preflight.log", env)
    model = json.loads((work / "setup-evidence/model.json").read_text())
    snapshot = Path(model["snapshot"])
    if (snapshot.name != original.gate.REVISION or
            original.gate.digest(snapshot / "model_index.json") != review["base_model_index_sha256"]):
        raise RuntimeError("Cached model snapshot is missing or differs")
    env["AI_MODEL_DIR"] = str(snapshot)
    (evidence / "resume-model.json").write_text(json.dumps({
        "snapshot": str(snapshot), "downloaded_again": False, "reinstalled_packages": False}, indent=2) + "\n")
    with (evidence / "diagnostic-resume.log").open("w", encoding="utf-8") as log:
        process = subprocess.Popen([sys.executable, str(runner), "--output", str(output),
                                    "--resume-from", str(work / "results")],
                                   cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in process.stdout:
            log.write(line)
            log.flush()
            if line.startswith("MAKEUP_QA"):
                print(line.rstrip(), flush=True)
        if process.wait():
            raise RuntimeError("Continuation failed; preserve new partial ZIP and diagnostic-resume.log")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runner", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    args = parser.parse_args()
    lock = ROOT.parent / ".makeup-quality-continuation.lock"
    with lock.open("x", encoding="utf-8") as stream:
        stream.write(str(os.getpid()))
    try:
        resume(args.runner, args.output, args.evidence)
    finally:
        lock.unlink()
