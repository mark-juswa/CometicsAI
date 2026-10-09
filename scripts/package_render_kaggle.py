"""Build a separate private CPU deployment overlay; preserve the accepted GPU bundle."""
from hashlib import sha256
import json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
GPU_NAME = "capstone_train002_20260928_v1.bin"
GPU_SHA = "f0d1fed52e00b6c5a1da2cade3731237675cdebbfc0b2cde3b2dbda99a4019ac"
NAME = "render_kaggle_cpu_20261009.bin"


def build():
    if sha256((ROOT / "artifacts" / GPU_NAME).read_bytes()).hexdigest() != GPU_SHA:
        raise ValueError("Approved expanded GPU bundle differs")
    with ZipFile(ROOT / "artifacts" / GPU_NAME) as gpu:
        registry = "backend/app/style_registry_train002_smoke.json"
        if json.loads(gpu.read(registry)) != json.loads((ROOT / registry).read_text()):
            raise ValueError("CPU and GPU expanded registries differ")
        presets = "data/makeup/DATA-M001-paired/inference_presets.json"
        if gpu.read(presets) != (ROOT / presets).read_bytes():
            raise ValueError("CPU and GPU Makeup presets differ")
    names = [p.relative_to(ROOT).as_posix() for p in (ROOT / "backend/app").rglob("*")
             if p.suffix in {".py", ".json"} and "__pycache__" not in p.parts]
    names += ["backend/requirements-demo-constraints.txt", "backend/requirements.txt", "backend/requirements-nails.txt", "backend/requirements-nails-segmenter.txt",
              "scripts/nails_segment_once.py", "scripts/render_kaggle_bootstrap.py",
              "data/makeup/DATA-M001-paired/inference_presets.json",
              "data/nails/checkpoints/mediapipe/hand_landmarker.task",
              "data/nails/checkpoints/mnemic/nails_seg_s_yolov8_v1.pt"]
    files = {name: (ROOT / name).read_bytes() for name in names}
    manifest = {"schema": "render-kaggle-cpu-v1", "gpu_bundle_sha256": GPU_SHA,
                "files": {name: sha256(raw).hexdigest() for name, raw in files.items()}}
    files["demo_bundle.json"] = (json.dumps(manifest, indent=2) + "\n").encode()
    output = ROOT / "artifacts" / NAME
    if output.exists():
        raise ValueError("Refuse to overwrite private overlay; remove only the previous generated file intentionally")
    with ZipFile(output, "x", ZIP_DEFLATED) as archive:
        for name, raw in sorted(files.items()):
            archive.writestr(name, raw)
    report = {"name": NAME, "bytes": output.stat().st_size, "sha256": sha256(output.read_bytes()).hexdigest(), **manifest}
    (ROOT / "docs/experiments/render-kaggle-bundle.json").write_text(json.dumps(report, indent=2) + "\n")
    extraction = """from pathlib import Path
from hashlib import sha256
from zipfile import ZipFile
import json, sys, subprocess
WORK = Path('/kaggle/working/render-kaggle')

def extract(name, expected, target, manifest_name):
    matches = list(Path('/kaggle/input').rglob(name))
    assert len(matches) == 1, 'Attach exactly one private input with ' + name
    source = matches[0]
    assert sha256(source.read_bytes()).hexdigest() == expected, 'Bundle hash differs'
    assert not target.exists(), 'Use a fresh notebook session; do not replace running source'
    with ZipFile(source) as archive:
        manifest = json.loads(archive.read(manifest_name))
        names = archive.namelist()
        assert len(names) == len(set(names)) and set(names) == set(manifest['files']) | {manifest_name}
        assert archive.testzip() is None
        for name in names:
            destination = (target / name).resolve()
            assert ':' not in name and chr(92) not in name and destination.is_relative_to(target.resolve())
            raw = archive.read(name)
            if name != manifest_name:
                assert sha256(raw).hexdigest() == manifest['files'][name], 'Member hash differs'
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(raw)
"""
    extraction += f"extract({GPU_NAME!r}, {GPU_SHA!r}, WORK / 'gpu-src', 'gate3_bundle.json')\n"
    extraction += f"extract({NAME!r}, {report['sha256']!r}, WORK / 'cpu-src', 'demo_bundle.json')\n"
    extraction += "print('Private bundles verified. Enable Internet, select T4 GPU, and run Cell 2.')\n"
    startup = """# Starts one local GPU worker, one authenticated API facade and one public API tunnel.
# Keys come from Kaggle Secrets, never notebook source.
subprocess.run([sys.executable, str(WORK / 'cpu-src/scripts/render_kaggle_bootstrap.py')], check=True)
"""
    status = """record = json.loads((WORK / 'demo-session.json').read_text())
print(json.dumps(record, indent=2))
# This is readiness evidence only. No AI generation is started by this cell.
"""
    for source in (extraction, startup, status):
        compile(source, '<demo-cell>', 'exec')
    notebook = {"nbformat": 4, "nbformat_minor": 5, "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}},
                "cells": [{"cell_type": "code", "id": "demo-" + str(i), "execution_count": None, "metadata": {}, "outputs": [],
                           "source": source.splitlines(keepends=True)} for i, source in enumerate((extraction, startup, status))]}
    (ROOT / "notebooks/render_kaggle_demo.ipynb").write_text(json.dumps(notebook, indent=1) + "\n")
    return {key: report[key] for key in ("name", "bytes", "sha256")}


if __name__ == "__main__":
    print(json.dumps(build(), indent=2))
