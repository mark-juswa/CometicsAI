"""Build an isolated application candidate from the accepted corrective GPU return.

The original release is verified first. The existing worker overlay then installs
the candidate in a fresh workspace. No website registration or production change.
"""
import base64
from hashlib import sha256
import json
from pathlib import Path
from zipfile import ZipFile

from scripts import package_all_hair_nails_release as hair
from scripts import package_expanded_nails_release as common

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "artifacts/makeup-corrective-supervision-20261105"
RETURN = WORK / "gpu-return-01"
DATA = ROOT / ".tmp/data_m001/corrective_selection/final_v1"
OUTPUT = WORK / "application-candidate-01"
CHECKPOINT_SHA = "991a1037cc892c1a62e1a731be577ed1aec2f331d9568b4586ff3829a4ee32c3"
CATALOG_SHA = "770292968c600fffc3bc330ba30caf7ab6429b8ec365d0a9896a783128e6cc56"
REVIEW_SHA = "7db6666beb345275462d3358bac1e3db8f431f441caeb2db6f4235c0b573f3df"
OLD_CPU_SHA = "dfb5fc35f2c9c446fb8fdcc4439650c5f8a72941db864db1e9045cadae73082f"
CPU_NAME = "makeup_corrective001_application_candidate_20261106.bin"
CONTRACT_PATH = "backend/app/makeup_contract.py"
PRESETS_PATH = "data/makeup/DATA-M001-corrective/inference_presets.json"
ADAPTER_PATH = "gate1/adapters/makeup-corrective001"


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()


def check_review(review, bindings):
    if (review.get("schema") != "makeup-corrective-model-review-v1"
            or review.get("checkpoint_sha256") != CHECKPOINT_SHA
            or review.get("production_approved") is not False or not review.get("reviewer")):
        raise ValueError("Wrong model review or approval scope")
    cases = review.get("cases", [])
    expected = {row["case_id"]: row for row in bindings}
    if len(cases) != 26 or len(expected) != 26 or {r["case_id"] for r in cases} != set(expected):
        raise ValueError("Model review omits or duplicates cases")
    for row in cases:
        if (row.get("verdict") != "ACCEPT_FOR_APPLICATION_VALIDATION"
                or any(row.get(k) != v for k, v in expected[row["case_id"]].items() if k != "images")):
            raise ValueError("Model review binding or verdict differs")


def candidate_contract(catalog):
    presets = encoded({"schema": "MAKEUP-001-corrective-inference-presets-v1",
                       "styles": [{"id": s["id"], "caption": s["caption"]} for s in catalog["styles"]]})
    text = (ROOT / CONTRACT_PATH).read_text(encoding="utf-8")
    changes = {
        'ADAPTER_ID = "MAKEUP-001"': 'ADAPTER_ID = "MAKEUP-001-CORRECTIVE-001"',
        'ADAPTER_SHA256 = "f6f0419e4259a75102f08a450222ad806e3aec1c2ae50ff89f875139084ae510"': f'ADAPTER_SHA256 = "{CHECKPOINT_SHA}"',
        'ADAPTER_BYTES = 46223600': 'ADAPTER_BYTES = 46223632',
        'PRESETS_SHA256 = "8e6e244f6174dc70f33cb15a037f5e67e2a245f15278967f4d2f85bc909cd5f5"': f'PRESETS_SHA256 = "{sha256(presets).hexdigest()}"',
        'data/makeup/DATA-M001-paired/inference_presets.json': PRESETS_PATH,
        'GENERATOR = "flux2_klein_base_makeup001"': 'GENERATOR = "flux2_klein_base_makeup001_corrective001"',
        'MAKEUP-001-inference-presets-v1': 'MAKEUP-001-corrective-inference-presets-v1',
        'len(styles) != 10': 'len(styles) != 13',
        'len({style["id"] for style in styles}) != 10': 'len({style["id"] for style in styles}) != 13',
        'the ten reviewed Makeup inference presets': 'the thirteen reviewed corrective Makeup captions',
        'style["instruction"] + " " + presets["preservation_instruction"]': 'style["caption"]',
        '"control_method": "fixed_inference_prompt_presets"': '"control_method": "fixed_corrective_catalog_captions"',
    }
    for before, after in changes.items():
        text = common.required_replace(text, before, after)
    return text.encode(), presets


INSTALL_EXTRA = '''
def install_candidate(root, cpu_root, output):
    root, cpu_root = Path(root), Path(cpu_root)
    manifest = json.loads((cpu_root/'candidate/worker-manifest.json').read_text())
    if manifest.get('schema') != 'makeup-corrective-worker-overlay-v1':
        raise ValueError('Wrong corrective worker overlay')
    # Parent CPU archive and all its files were hash checked before this hook.
    prepared = []
    for name, digest in manifest['files'].items():
        target = (root/name).resolve()
        if not target.is_relative_to(root.resolve()) or ':' in name or chr(92) in name:
            raise ValueError('Unsafe corrective overlay path')
        raw = (cpu_root/'candidate/worker'/name).read_bytes()
        if sha256(raw).hexdigest() != digest:
            raise ValueError('Corrective worker source/checkpoint hash differs')
        if name.endswith('.py'):
            compile(raw, name, 'exec')
        prepared.append((target, raw))
    record = Path(output)/'makeup-corrective-worker-overlay.json'
    if record.exists():
        raise RuntimeError('Candidate already installed, use a fresh session')
    for target, raw in prepared:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    record.write_text(json.dumps(manifest, indent=2))
'''


def build(destination=OUTPUT):
    destination = Path(destination)
    review_path = RETURN / "human-model-review-01/makeup-corrective-model-review.json"
    if common.digest(review_path) != REVIEW_SHA or common.digest(DATA / "catalog.json") != CATALOG_SHA:
        raise ValueError("Accepted catalog/review changed")
    review = json.loads(review_path.read_text(encoding="utf-8-sig"))
    bindings = json.loads((RETURN / "model-review/bindings.json").read_text())
    check_review(review, bindings)
    checkpoint = RETURN / "raw/checkpoints/makeup001_corrective001_250step/makeup001_corrective001_250step.safetensors"
    if checkpoint.stat().st_size != 46223632 or common.digest(checkpoint) != CHECKPOINT_SHA:
        raise ValueError("Candidate checkpoint changed")
    old_cpu = ROOT / "artifacts" / hair.CPU_NAME
    if common.digest(old_cpu) != OLD_CPU_SHA:
        raise ValueError("Preserved Hair/Nails release changed")
    catalog = json.loads((DATA / "catalog.json").read_text())
    if len(catalog["styles"]) != 13 or len({s["id"] for s in catalog["styles"]}) != 13:
        raise ValueError("Expected complete catalog")
    contract, presets = candidate_contract(catalog)
    metadata = {"schema_version": 1, "artifact_type": "project_trained_lora",
        "adapter_id": "MAKEUP-001-CORRECTIVE-001", "experiment": "MAKEUP-001-CORRECTIVE-001",
        "training_steps": 250, "base_model_id": "black-forest-labs/FLUX.2-klein-base-4B",
        "base_model_revision": "a3b4f4849157f664bdbc776fd7453c2783562f4d",
        "checkpoint_file": "adapter.safetensors", "checkpoint_sha256": CHECKPOINT_SHA,
        "checkpoint_bytes": 46223632, "prompt_presets_sha256": sha256(presets).hexdigest(),
        "control_method": "fixed_corrective_catalog_captions",
        "inference": {"width": 512, "height": 512, "steps": 20, "guidance": 4.0, "seed": 1977},
        "inference_style_ids": [s["id"] for s in catalog["styles"]],
        "dataset": "DATA-M001-corrective-final-v1", "train_pairs": 52, "validation_pairs": 26,
        "train_identities": 12, "validation_identities": ["054109", "056266"],
        "model_review_sha256": REVIEW_SHA, "production_approved": False}
    extras = {CONTRACT_PATH: contract, PRESETS_PATH: presets,
              ADAPTER_PATH + "/adapter.safetensors": checkpoint.read_bytes(),
              ADAPTER_PATH + "/metadata.json": encoded(metadata)}
    payload = hair.worker_payload()
    server = base64.b64decode(payload["scripts/unified_gate3_server.py"]["data"]).decode()
    server = common.required_replace(server, "makeup = ROOT / 'gate1/adapters/makeup'",
                                     f"makeup = ROOT / '{ADAPTER_PATH}'")
    server = common.required_replace(server, "'http_requests': list(HTTP_RECORDS),",
        "'http_requests': list(HTTP_RECORDS),\n"
        "                'active_adapter_verification': self.owner.active_state if self.owner else None,")
    raw = server.encode()
    payload["scripts/unified_gate3_server.py"] = {"data": base64.b64encode(raw).decode(), "sha256": sha256(raw).hexdigest()}
    # Existing tensor equality checks remain. Check full ordinary PEFT scaling too.
    runtime = (ROOT / "scripts/makeup_inference_server.py").read_text()
    anchor = '        source = ImageOps.pad(portrait, (512, 512),'
    assertion = '''        import math
        active = self.pipe.get_active_adapters()
        if len(active) != 1:
            raise RuntimeError("Corrective Makeup requires one active adapter")
        name, layers = active[0], 0
        for module in self.pipe.transformer.modules():
            if hasattr(module, 'lora_A'):
                layers += 1
                expected = module.lora_alpha[name] / module.r[name]
                if (module.disable_adapters or module.merged or list(module.active_adapters) != [name]
                        or not math.isclose(float(module.scaling[name]), expected, rel_tol=1e-6)):
                    raise RuntimeError("Corrective Makeup requires full loaded adapter scaling")
        if not layers:
            raise RuntimeError("Corrective Makeup has no active LoRA layers")
'''
    runtime = common.required_replace(runtime, anchor, assertion + anchor)
    extras["scripts/makeup_inference_server.py"] = runtime.encode()
    with ZipFile(old_cpu) as archive:
        files = {n: archive.read(n) for n in archive.namelist()}
    manifest = json.loads(files.pop("demo_bundle.json"))
    files[CONTRACT_PATH], files[PRESETS_PATH] = contract, presets
    style_text = files["backend/app/makeup_styles.py"].decode()
    held = [s for s in catalog["styles"] if s["serving_status"] == "held"]
    additions = "\n# Controlled candidate catalog only, production release remains held.\nMAKEUP_STYLES += (\n"
    for s in held:
        additions += f"    MakeupStyle({s['id']!r}, {s['name']!r}, 'Corrective application validation candidate.', {s['caption']!r}),\n"
    additions += ")\nMAKEUP_STYLE_BY_ID = {style.id: style for style in MAKEUP_STYLES}\n"
    files["backend/app/makeup_styles.py"] = (style_text + additions).encode()
    for name, raw in extras.items():
        files["candidate/worker/" + name] = raw
    worker_manifest = {"schema": "makeup-corrective-worker-overlay-v1", "checkpoint_sha256": CHECKPOINT_SHA,
                       "production_approved": False, "files": {k: sha256(v).hexdigest() for k, v in extras.items()}}
    files["candidate/worker-manifest.json"] = encoded(worker_manifest)
    files["candidate/model-review.json"] = review_path.read_bytes()
    # Two real development sources, never targets, are the application fixtures.
    for identity in ("054109", "056266"):
        files[f"candidate/fixtures/{identity}.png"] = (DATA / f"validation/reference/{identity}-natural_makeup.png").read_bytes()
    for i, style in enumerate(catalog["styles"]):
        identity = ("054109", "056266")[i % 2]
        case = next(b for b in bindings if b["case_id"] == identity + "-" + style["id"])
        raw = (RETURN / f"raw/evaluation/adapter/{identity}/{style['id']}.png").read_bytes()
        if sha256(raw).hexdigest() != case["corrective_sha256"]:
            raise ValueError("Accepted raw comparison image changed")
        files[f"candidate/accepted/{case['case_id']}.png"] = raw
    files["candidate/application_probe.py"] = (ROOT / "scripts/makeup_corrective_application_probe.py").read_bytes()
    manifest.update(worker_sources={k: v["sha256"] for k, v in payload.items()},
                    makeup_candidate=metadata,
                    files={k: sha256(v).hexdigest() for k, v in files.items()})
    files["demo_bundle.json"] = encoded(manifest)
    for name, raw in files.items():
        if name.endswith(".py"):
            compile(raw, name, "exec")
    cpu = common.archive_bytes(files)
    # Extend the existing matched release notebook, retaining original preflight.
    book = json.loads((ROOT / hair.NOTEBOOK).read_text(encoding="utf-8"))
    installer = (ROOT / "scripts/hair_nails_release_overlay.py").read_text()
    replacement = installer + INSTALL_EXTRA
    preparation = "".join(book["cells"][1]["source"])
    for before, after in [(hair.CPU_NAME, CPU_NAME), (OLD_CPU_SHA, sha256(cpu).hexdigest()),
                          (installer, replacement), (repr(installer), repr(replacement)),
                          (repr(hair.worker_payload()), repr(payload))]:
        preparation = common.required_replace(preparation, before, after)
    startup = "".join(book["cells"][2]["source"])
    startup = common.required_replace(startup,
        '    release_overlay.install_overlay(original.ROOT, Path({str(WORK / \'optimized-worker.json\')!r}), output)',
        '    release_overlay.install_overlay(original.ROOT, Path({str(WORK / \'optimized-worker.json\')!r}), output)\n'
        '    release_overlay.install_candidate(original.ROOT, Path({str(CPU_ROOT)!r}), output)')
    stop = '    # Bootstrap already downloaded cloudflared; point only at the authenticated facade.'
    # Readiness is complete. End here before any public tunnel or registration.
    startup = common.required_replace(startup, stop, '''    record = {"status": "CONTROLLED_APPLICATION_READY", "url": f"http://127.0.0.1:{PORT}",
              "api_pid": api.pid, "readiness": readiness, "production_registered": False}
    (WORK / "demo-session.json").write_text(json.dumps(record, indent=2))
    print("CONTROLLED APPLICATION READY. Run Cell 3. Website connection unchanged.", flush=True)
    return
''' + stop)
    book["cells"][0]["source"] = ["# Corrective MAKEUP application validation\n\n"
        "Private copy of the existing pinned Kaggle notebook, T4 and Internet. Attach the unchanged "
        f"{common.GPU_NAME} and the new {CPU_NAME}. Enable the existing three secrets. "
        "Run the three code cells in order. No training. No website registration or production enablement. "
        "This tests the existing authenticated application API, shared worker and original Hair/Nails. "
        "All 13 Makeup styles are candidate catalog entries in this workspace only.\n"]
    book["cells"][1]["source"] = preparation.splitlines(keepends=True)
    book["cells"][2]["source"] = startup.splitlines(keepends=True)
    book["cells"][3]["source"] = [
        "import runpy\n"
        "probe = runpy.run_path(str(CLIENT_WORK/'cpu-src/candidate/application_probe.py'))\n"
        "probe['run'](CLIENT_WORK)\n"]
    for i, cell in enumerate(book["cells"]):
        if cell["cell_type"] == "code":
            compile("".join(cell["source"]), f"candidate-cell-{i}", "exec")
            cell["outputs"], cell["execution_count"] = [], None
    report = {"schema": "makeup-corrective-application-package-v1", "status": "PREPARED_NOT_GPU_VALIDATED",
              "cpu": {"name": CPU_NAME, "bytes": len(cpu), "sha256": sha256(cpu).hexdigest()},
              "gpu": {"name": common.GPU_NAME, "sha256": common.GPU_SHA, "unchanged": True},
              "checkpoint_sha256": CHECKPOINT_SHA, "review_sha256": REVIEW_SHA,
              "catalog_counts": {"hairstyle": 18, "makeup": 13, "nails": 8},
              "model_review_cases_accepted": 26, "production_approved": False,
              "production_registered": False, "worker_overlay": worker_manifest,
              "preserved_cpu_sha256": OLD_CPU_SHA}
    common.immutable(destination / CPU_NAME, cpu)
    common.immutable(destination / "makeup_corrective001_application.ipynb", encoded(book))
    common.immutable(destination / "package.json", encoded(report))
    return report


if __name__ == "__main__":
    report = build()
    print(json.dumps({k: report[k] for k in ("status", "cpu", "catalog_counts", "production_registered")}, indent=2))
