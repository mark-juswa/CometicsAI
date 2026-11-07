"""Build a separate matching approved French Bob + Nails release; preserve older artifacts."""
import base64
from hashlib import sha256
import json
from pathlib import Path
from zipfile import ZipFile

from scripts import package_expanded_nails_release as prior
from scripts.hair_nails_release_overlay import FILES, validated

ROOT = Path(__file__).resolve().parents[1]
CPU_NAME = "render_kaggle_cpu_hair_nails_20261031_01.bin"
NOTEBOOK = "notebooks/render_kaggle_hair_nails_demo.ipynb"
REPORT = "docs/experiments/hair-nails-package-20261031.json"
HOOK = b"\n# Verified release extension; original registry/checkpoint claims remain unchanged.\nfrom scripts.hair_release_worker import install as _install_hair_release\n_install_hair_release(sys.modules[__name__])\n"


def worker_payload():
    payload = {}
    for name in sorted(FILES):
        raw = (ROOT / name).read_bytes()
        if name == "scripts/unified_gate3_server.py":
            raw += HOOK
        payload[name] = {"data": base64.b64encode(raw).decode(), "sha256": sha256(raw).hexdigest()}
    validated(payload)
    return payload


def notebook(cpu_sha, evidence, payload):
    raw, previous_payload = prior.build_notebook(cpu_sha, evidence)
    book = json.loads(raw)
    preparation = "".join(book["cells"][1]["source"])
    old_installer = (ROOT / "scripts/optimized_demo_overlay.py").read_text(encoding="utf-8")
    installer = (ROOT / "scripts/hair_nails_release_overlay.py").read_text(encoding="utf-8")
    preparation = prior.required_replace(preparation, old_installer, installer)
    preparation = prior.required_replace(preparation, repr(old_installer), repr(installer))
    preparation = prior.required_replace(preparation, repr(previous_payload), repr(payload))
    # prior.build_notebook uses the Nail-only CPU filename. Bind the new file/hash.
    preparation = prior.required_replace(preparation, repr(prior.CPU_NAME), repr(CPU_NAME))
    preparation += """
cpu_manifest = json.loads((CLIENT_WORK/'cpu-src/demo_bundle.json').read_text(encoding='utf-8'))
if cpu_manifest.get('worker_sources') != {name: row['sha256'] for name, row in OPTIMIZED_SOURCES.items()}:
    raise RuntimeError('CPU and worker release source pair differs')
print('French Bob + Nails release staged. Run Cell 2 once.')
"""
    startup = "".join(book["cells"][2]["source"])
    startup = prior.required_replace(startup,
        'capabilities.get("renderer_styles", [])',
        'capabilities.get("renderer_styles", []) + capabilities.get("model_styles", {}).get("hairstyle", [])')
    book["cells"][0]["source"] = ["""# BeautyCore approved French Bob + Nails release — rehearsal starter

Use a separate private copy of the tested pinned Kaggle notebook, reviewed T4 and Internet.
Attach exactly one capstone_train002_20260928_v1.bin and one render_kaggle_cpu_hair_nails_20261031_01.bin.
Enable the existing three Kaggle Secrets. Keep their values private; the backend key must match Render.
Run the three code cells once, in order, after matching Render code is deployed.
French Bob uses its reviewed TRAIN-001 prompt/settings; the approved preview is curly and may change hair color.
The three approved Nail designs and existing Nails-only optimization are included. Other new Hair styles stay held.
Original checkpoints, training metadata, registry files and original fallback notebooks/bundles are preserved.
Registration is automatic; no routine Render endpoint edit. Fresh GPU/website rehearsal is still required.
"""]
    book["cells"][1]["source"] = preparation.splitlines(keepends=True)
    book["cells"][2]["source"] = startup.splitlines(keepends=True)
    book["cells"][3]["source"] = "".join(book["cells"][3]["source"]).replace("Added Nails:", "Added styles:").splitlines(keepends=True)
    for i, cell in enumerate(book["cells"]):
        cell["id"] = "hair-nails-release-" + str(i)
        if cell["cell_type"] == "code":
            compile("".join(cell["source"]), cell["id"], "exec")
    return (json.dumps(book, ensure_ascii=False, indent=1) + "\n").encode()


def build(destination=ROOT):
    import sys
    sys.path.insert(0, str(ROOT / "backend"))
    from app.style_release import RELEASE
    from scripts.generate_style_release import outputs, BUSINESS, GENERATED
    destination = Path(destination)
    current = json.loads(BUSINESS.read_text(encoding="utf-8"))
    business, expected = outputs(current)
    if current != business or json.loads(GENERATED.read_text(encoding="utf-8")) != expected:
        raise ValueError("Generated Hair/Nails release metadata is stale")
    ids = sorted(c.id for c in RELEASE.enabled())
    if ids != ["exp_french_bob_wispy", "exp_negative_space_microdots", "exp_pink_aura", "exp_raspberry_jelly"]:
        raise ValueError("Unexpected approved Hair/Nails release scope")
    if prior.digest(ROOT / "artifacts" / prior.GPU_NAME) != prior.GPU_SHA:
        raise ValueError("Original GPU archive differs")
    with ZipFile(ROOT / "artifacts" / prior.GPU_NAME) as gpu:
        for name in ("backend/app/style_registry_train002_smoke.json",
                     "data/makeup/DATA-M001-paired/inference_presets.json"):
            if json.loads(gpu.read(name)) != json.loads((ROOT / name).read_text(encoding="utf-8")):
                raise ValueError("CPU/GPU frozen catalogs differ")
    payload = worker_payload()
    evidence = {"release_id": RELEASE.release_id, "manifest_sha256": RELEASE.manifest_sha256,
                "enabled_style_ids": ids}
    files = prior.release_sources()
    approval = "docs/experiments/french-bob-approval-20261031.json"
    files[approval] = (ROOT / approval).read_bytes()
    manifest = {"schema": "render-kaggle-cpu-v1", "gpu_bundle_sha256": prior.GPU_SHA,
                "style_release": evidence, "worker_sources": {k: v["sha256"] for k, v in payload.items()},
                "files": {name: sha256(raw).hexdigest() for name, raw in files.items()}}
    files["demo_bundle.json"] = (json.dumps(manifest, indent=2) + "\n").encode()
    for name, raw in files.items():
        if name.endswith(".py"):
            compile(raw, name, "exec")
    archive = prior.archive_bytes(files)
    cpu_sha = sha256(archive).hexdigest()
    book = notebook(cpu_sha, evidence, payload)
    receipt = {
        "date": "2026-10-31", "status": "PREPARED_REQUIRES_GPU_AND_WEBSITE_REHEARSAL",
        "style_release": evidence,
        "cpu": {"name": CPU_NAME, "bytes": len(archive), "sha256": cpu_sha},
        "gpu": {"name": prior.GPU_NAME, "sha256": prior.GPU_SHA, "unchanged": True},
        "notebook": {"path": NOTEBOOK, "bytes": len(book), "sha256": sha256(book).hexdigest()},
        "worker_overlay": manifest["worker_sources"], "cpu_members": manifest["files"],
        "optimization": "existing Nails-only public-prompt cache; Hair baseline plus explicit approved profile",
        "fallback": {name: prior.digest(ROOT / name) for name in (
            "notebooks/render_kaggle_client_demo.ipynb", "notebooks/render_kaggle_optimized_demo.ipynb",
            "notebooks/render_kaggle_expanded_nails_demo.ipynb",
            "artifacts/render_kaggle_cpu_20261009.bin", "artifacts/" + prior.CPU_NAME)},
        "render_metadata_sha256": prior.digest(GENERATED),
        "business_catalog_sha256": prior.digest(BUSINESS),
        "deployed": False, "live_generation_verified": False,
    }
    prior.immutable(destination / "artifacts" / CPU_NAME, archive)
    prior.immutable(destination / NOTEBOOK, book)
    prior.immutable(destination / REPORT, (json.dumps(receipt, indent=2) + "\n").encode())
    return receipt


if __name__ == "__main__":
    result = build()
    print(json.dumps({k: result[k] for k in ("status", "style_release", "cpu", "gpu", "notebook")}, indent=2))
