"""Package approved Nail renderers without replacing the working demo inputs.

Uses the unchanged reviewed GPU archive and a new immutable CPU archive.
The separate notebook retains the existing Nails-only performance overlay,
model/environment checks and authenticated automatic website registration.
"""
import ast
import base64
from hashlib import sha256
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from scripts.optimized_demo_overlay import FILES, validated

ROOT = Path(__file__).resolve().parents[1]
CPU_NAME = "render_kaggle_cpu_styles_20261030_01.bin"
GPU_NAME = "capstone_train002_20260928_v1.bin"
GPU_SHA = "f0d1fed52e00b6c5a1da2cade3731237675cdebbfc0b2cde3b2dbda99a4019ac"
OLD_CPU_SHA = "f391050851519e9cc1080830b615a6cc457b6dd1e21fde156522bb959fad9ede"
NOTEBOOK = "notebooks/render_kaggle_expanded_nails_demo.ipynb"
REPORT = "docs/experiments/expanded-nails-package-20261030.json"

PAIR_CHECK = r'''
def verify_release_pair(work, expected):
    gpu = json.loads((work / "gpu-src/gate3_bundle.json").read_text(encoding="utf-8"))
    cpu = json.loads((work / "cpu-src/demo_bundle.json").read_text(encoding="utf-8"))
    release = json.loads((work / "cpu-src/backend/app/style_release.json").read_text(encoding="utf-8"))
    canonical = json.dumps(release, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode()
    installed = sorted(c["id"] for c in release["candidates"] if c["enabled"])
    if (gpu.get("schema") != "unified-kaggle-gate3-v1"
            or cpu.get("schema") != "render-kaggle-cpu-v1"
            or cpu.get("gpu_bundle_sha256") != BUNDLES[0][1]
            or cpu.get("style_release") != expected
            or release.get("release_id") != expected["release_id"]
            or sha256(canonical).hexdigest() != expected["manifest_sha256"]
            or installed != expected["enabled_style_ids"]):
        raise RuntimeError("CPU/GPU style release pair differs; use the matching release notebook and inputs")
    return expected
'''


def required_replace(source, before, after):
    if source.count(before) != 1:
        raise ValueError("Reviewed startup anchor changed: " + before)
    return source.replace(before, after)


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def immutable(path, raw):
    if path.exists():
        if path.read_bytes() != raw:
            raise ValueError("Refuse to replace an existing release artifact: " + str(path))
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as output:
        output.write(raw)


def archive_bytes(files):
    from io import BytesIO
    output = BytesIO()
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        for name, raw in sorted(files.items()):
            info = ZipInfo(name, date_time=(2026, 10, 30, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            archive.writestr(info, raw)
    return output.getvalue()


def release_sources():
    # This original inventory includes only application source and explicitly
    # named assets. No credentials, user database, generated photos or experiments.
    names = {p.relative_to(ROOT).as_posix() for p in (ROOT / "backend/app").rglob("*")
             if p.suffix in {".py", ".json"} and "__pycache__" not in p.parts}
    names.update({
        "backend/requirements-demo-constraints.txt", "backend/requirements.txt",
        "backend/requirements-nails.txt", "backend/requirements-nails-segmenter.txt",
        "scripts/nails_segment_once.py", "scripts/render_kaggle_bootstrap.py",
        "data/makeup/DATA-M001-paired/inference_presets.json",
        "data/nails/checkpoints/mediapipe/hand_landmarker.task",
        "data/nails/checkpoints/mnemic/nails_seg_s_yolov8_v1.pt",
        "docs/experiments/expanded-nails-approval-20261030.json",
    })
    return {name: (ROOT / name).read_bytes() for name in sorted(names)}


def build_notebook(cpu_sha, evidence):
    payload = {name: {"data": base64.b64encode((ROOT / name).read_bytes()).decode("ascii"),
                      "sha256": digest(ROOT / name)} for name in sorted(FILES)}
    validated(payload)
    setup = (ROOT / "notebooks/render_kaggle_client_setup.py").read_text(encoding="utf-8")
    setup = required_replace(setup, '"render_kaggle_cpu_20261009.bin"', repr(CPU_NAME))
    setup = required_replace(setup, '"' + OLD_CPU_SHA + '"', repr(cpu_sha))
    setup = setup.replace('Attach exactly one private input containing ',
                          'Attach exactly one input containing ')
    installer = (ROOT / "scripts/optimized_demo_overlay.py").read_text(encoding="utf-8")
    runner = (ROOT / "scripts/render_kaggle_bootstrap.py").read_text(encoding="utf-8")
    runner = required_replace(runner, 'WORK = Path("/kaggle/working/render-kaggle")',
                              "WORK = CLIENT_WORK")
    runner = runner.rsplit('if __name__ == "__main__":', 1)[0]
    anchor = "original.start_server = lambda output, env: start(output, worker_environment(env))"
    hook = """import importlib.util
spec = importlib.util.spec_from_file_location('optimized_overlay', Path({str(WORK / 'worker_overlay.py')!r}))
release_overlay = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release_overlay)

def start_optimized(output, env):
    original.verify_bundle()
    release_overlay.install_overlay(original.ROOT, Path({str(WORK / 'optimized-worker.json')!r}), output)
    return start(output, worker_environment(dict(env, AI_PROMPT_CACHE='1', AI_PROMPT_CACHE_SCOPE='nails', AI_INFERENCE_PROFILE='0')))
original.start_server = start_optimized"""
    runner = required_replace(runner, anchor, hook)
    anchor = '    # Bootstrap already downloaded cloudflared; point only at the authenticated facade.'
    check = """    capabilities = readiness.get("style_capabilities", {})
    expected_release = STYLE_RELEASE_EXPECTED
    if (capabilities.get("release_id") != expected_release["release_id"]
            or capabilities.get("manifest_sha256") != expected_release["manifest_sha256"]
            or not set(expected_release["enabled_style_ids"]).issubset(capabilities.get("renderer_styles", []))):
        raise RuntimeError("Loaded facade does not match the approved Nail release")
""" + anchor
    runner = required_replace(runner, anchor, check)
    registrar = (ROOT / "scripts/render_kaggle_registration.py").read_text(encoding="utf-8")
    preparation = (setup + "\n" + PAIR_CHECK + "\nSTYLE_RELEASE_EXPECTED = " + repr(evidence)
                   + "\nCLIENT_WORK = prepare()\nverify_release_pair(CLIENT_WORK, STYLE_RELEASE_EXPECTED)\n"
                   + installer + "\nOPTIMIZED_SOURCES = " + repr(payload)
                   + "\nstage_overlay(CLIENT_WORK, OPTIMIZED_SOURCES)\n"
                   + "(CLIENT_WORK/'worker_overlay.py').write_text(" + repr(installer) + ", encoding='utf-8')\n"
                   + "print('Approved Nail release verified. Run Cell 2 once.')\n")
    prefix = ("import os\nBEAUTYCORE_PUBLIC_URL = 'https://beautycore-demo.onrender.com'\n"
              "os.environ['BEAUTYCORE_PUBLIC_URL'] = BEAUTYCORE_PUBLIC_URL\n"
              "(CLIENT_WORK/'runtime_registration.py').write_text(" + repr(registrar) + ", encoding='utf-8')\n")
    status = """record = json.loads((CLIENT_WORK/'demo-session.json').read_text())
print('Status:', record['status'])
print('Website:', BEAUTYCORE_PUBLIC_URL)
print('Release:', STYLE_RELEASE_EXPECTED['release_id'])
print('Added Nails:', ', '.join(STYLE_RELEASE_EXPECTED['enabled_style_ids']))
print('Connected status still requires the website rehearsal. Keep this session running.')
"""
    intro = ("# BeautyCore approved Nail expansion — rehearsal starter\n\n"
             "Not yet live-validated. Preserve the working optimized notebook as fallback. "
             "Use a private copy of the tested pinned Kaggle image, T4 GPU and Internet. "
             "Attach exactly one " + GPU_NAME + " and exactly one " + CPU_NAME + ". "
             "Remove duplicate inputs containing either filename. The old CPU dataset is unnecessary here. "
             "Enable AI_BACKEND_API_KEY, AI_REMOTE_API_KEY and GEMINI_API_KEY in Kaggle Secrets. "
             "Do not paste keys into cells. Run the three code cells once in order. "
             "Start only during a planned demo gap after the matching Render release is live. "
             "Registration is automatic; no routine Render URL edit. "
             "Only Raspberry Jelly, Pink Aura Ombré and Negative-Space Micro-Dots are added. "
             "Hair/Makeup settings and model weights stay unchanged; Makeup's white-cast limitation remains. "
             "Existing Nails-only prompt reuse is retained. No new training or paid provider.\n")
    cells = []
    for i, (kind, source) in enumerate((("markdown", intro), ("code", preparation),
                                        ("code", prefix + runner + "\nmain()\n"), ("code", status))):
        cell = {"cell_type": kind, "id": "nails-release-" + str(i),
                "metadata": {}, "source": source.splitlines(keepends=True)}
        if kind == "code":
            compile(source, "nails-release-cell-" + str(i), "exec")
            cell.update(execution_count=None, outputs=[])
        cells.append(cell)
    book = {"nbformat": 4, "nbformat_minor": 5,
            "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}},
            "cells": cells}
    return (json.dumps(book, ensure_ascii=False, indent=1) + "\n").encode(), payload


def build():
    import sys
    sys.path.insert(0, str(ROOT / "backend"))
    from app.style_release import RELEASE
    from scripts.generate_style_release import outputs, BUSINESS, GENERATED
    current = json.loads(BUSINESS.read_text(encoding="utf-8"))
    business, expected = outputs(current)
    if current != business or json.loads(GENERATED.read_text(encoding="utf-8")) != expected:
        raise ValueError("Generated release metadata is stale")
    ids = sorted(c.id for c in RELEASE.enabled())
    if ids != ["exp_negative_space_microdots", "exp_pink_aura", "exp_raspberry_jelly"]:
        raise ValueError("This package supports only the three visually approved Nail designs")
    if digest(ROOT / "artifacts" / GPU_NAME) != GPU_SHA:
        raise ValueError("Approved GPU archive differs")
    with ZipFile(ROOT / "artifacts" / GPU_NAME) as gpu:
        for name in ("backend/app/style_registry_train002_smoke.json",
                     "data/makeup/DATA-M001-paired/inference_presets.json"):
            if json.loads(gpu.read(name)) != json.loads((ROOT / name).read_text(encoding="utf-8")):
                raise ValueError("CPU and GPU model catalogs differ")
    evidence = {"release_id": RELEASE.release_id, "manifest_sha256": RELEASE.manifest_sha256,
                "enabled_style_ids": ids}
    files = release_sources()
    manifest = {"schema": "render-kaggle-cpu-v1", "gpu_bundle_sha256": GPU_SHA,
                "style_release": evidence,
                "files": {name: sha256(raw).hexdigest() for name, raw in files.items()}}
    files["demo_bundle.json"] = (json.dumps(manifest, indent=2) + "\n").encode()
    archive = archive_bytes(files)
    cpu_sha = sha256(archive).hexdigest()
    notebook, payload = build_notebook(cpu_sha, evidence)
    # Validate all source before any immutable artifact is published.
    for name, raw in files.items():
        if name.endswith(".py"):
            compile(raw, name, "exec")
    immutable(ROOT / "artifacts" / CPU_NAME, archive)
    immutable(ROOT / NOTEBOOK, notebook)
    report = {
        "date": "2026-10-30", "status": "PREPARED_REQUIRES_KAGGLE_AND_WEBSITE_REHEARSAL",
        "style_release": evidence,
        "cpu": {"name": CPU_NAME, "sha256": cpu_sha, "bytes": len(archive)},
        "gpu": {"name": GPU_NAME, "sha256": GPU_SHA, "unchanged": True},
        "notebook": {"path": NOTEBOOK, "sha256": sha256(notebook).hexdigest(), "bytes": len(notebook)},
        "worker_overlay": {name: item["sha256"] for name, item in payload.items()},
        "cpu_members": manifest["files"],
        "fallback": {name: digest(ROOT / name) for name in (
            "artifacts/render_kaggle_cpu_20261009.bin",
            "notebooks/render_kaggle_client_demo.ipynb",
            "notebooks/render_kaggle_optimized_demo.ipynb")},
        "optimization": "nails-only public-prompt cache; unchanged model settings",
        "render_metadata_sha256": digest(GENERATED),
        "business_catalog_sha256": digest(BUSINESS),
        "deployed": False, "live_generation_verified": False,
    }
    immutable(ROOT / REPORT, (json.dumps(report, indent=2) + "\n").encode())
    return {key: report[key] for key in ("status", "style_release", "cpu", "gpu", "notebook")}


if __name__ == "__main__":
    print(json.dumps(build(), indent=2))
