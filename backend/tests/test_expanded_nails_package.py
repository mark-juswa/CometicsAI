"""Real release archive roundtrip and notebook checks without GPU/network access."""
import ast
import base64
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import runpy
from zipfile import ZipFile

import pytest

from scripts.package_expanded_nails_release import (
    CPU_NAME, GPU_NAME, GPU_SHA, NOTEBOOK, REPORT, PAIR_CHECK,
    ROOT, archive_bytes, build_notebook, immutable,
)
from scripts.optimized_demo_overlay import validated


def report():
    return json.loads((ROOT / REPORT).read_text(encoding="utf-8"))


def setup():
    return runpy.run_path(str(ROOT / "notebooks/render_kaggle_client_setup.py"))


def literal_assignment(tree, name):
    return ast.literal_eval(next(n.value for n in tree.body if isinstance(n, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == name for target in n.targets)))


def test_real_cpu_archive_inventory_roundtrip_and_pair(tmp_path):
    evidence = report()
    source = ROOT / "artifacts" / CPU_NAME
    assert sha256(source.read_bytes()).hexdigest() == evidence["cpu"]["sha256"]
    cpu = tmp_path / "cpu-src"
    setup()["extract"](source, evidence["cpu"]["sha256"], cpu, "demo_bundle.json")
    with ZipFile(source) as archive:
        assert archive.testzip() is None
        manifest = json.loads(archive.read("demo_bundle.json"))
        # This is a preserved immutable release, not the current Hair checkout.
        assert manifest["files"] == evidence["cpu_members"]
        assert len(archive.namelist()) == len(set(archive.namelist()))
        assert set(archive.namelist()) == set(manifest["files"]) | {"demo_bundle.json"}
        for name, digest in manifest["files"].items():
            assert not name.startswith("/") and ":" not in name and "\\" not in name
            assert sha256((cpu / name).read_bytes()).hexdigest() == digest
            assert not any(part.startswith(".") for part in Path(name).parts)
    gpu = tmp_path / "gpu-src"
    gpu.mkdir()
    with ZipFile(ROOT / "artifacts" / GPU_NAME) as archive:
        (gpu / "gate3_bundle.json").write_bytes(archive.read("gate3_bundle.json"))
    namespace = {"json": json, "sha256": sha256, "BUNDLES": [(GPU_NAME, GPU_SHA)]}
    exec(PAIR_CHECK, namespace)
    verify = namespace["verify_release_pair"]
    assert verify(tmp_path, evidence["style_release"]) == evidence["style_release"]
    altered = json.loads((cpu / "demo_bundle.json").read_text())
    altered["gpu_bundle_sha256"] = "0" * 64
    (cpu / "demo_bundle.json").write_text(json.dumps(altered))
    with pytest.raises(RuntimeError, match="pair differs"):
        verify(tmp_path, evidence["style_release"])


def test_archive_tampering_is_rejected_before_extracting(tmp_path):
    evidence = report()
    source = ROOT / "artifacts" / CPU_NAME
    target = tmp_path / "tampered.bin"
    with ZipFile(source) as archive:
        files = {name: archive.read(name) for name in archive.namelist()}
    files["backend/app/style_release.json"] += b" "
    raw = archive_bytes(files)
    target.write_bytes(raw)
    # Even a caller with the altered outer digest cannot bypass member hashes.
    with pytest.raises(RuntimeError, match="member hash differs"):
        setup()["extract"](target, sha256(raw).hexdigest(), tmp_path / "extracted", "demo_bundle.json")
    assert not (tmp_path / "extracted").exists()


def test_notebook_embeds_exact_pair_optimization_and_current_runner():
    evidence = report()
    path = ROOT / NOTEBOOK
    assert sha256(path.read_bytes()).hexdigest() == evidence["notebook"]["sha256"]
    rebuilt, _ = build_notebook(evidence["cpu"]["sha256"], evidence["style_release"])
    assert path.read_bytes() == rebuilt
    book = json.loads(path.read_text(encoding="utf-8"))
    cells = [cell for cell in book["cells"] if cell["cell_type"] == "code"]
    assert len(cells) == 3
    for cell in cells:
        assert cell["execution_count"] is None and cell["outputs"] == []
        compile("".join(cell["source"]), "<release-cell>", "exec")
    tree = ast.parse("".join(cells[0]["source"]))
    bundles = literal_assignment(tree, "BUNDLES")
    assert bundles[0][:2] == (GPU_NAME, GPU_SHA)
    assert bundles[1][:2] == (CPU_NAME, evidence["cpu"]["sha256"])
    embedded = validated(literal_assignment(tree, "OPTIMIZED_SOURCES"))
    for name, raw in embedded.items():
        assert raw == (ROOT / name).read_bytes()
        assert sha256(raw).hexdigest() == evidence["worker_overlay"][name]
    main = ast.parse("".join(cells[1]["source"]))
    node = next(n.value for n in ast.walk(main) if isinstance(n, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "gpu_code" for t in n.targets))
    worker = eval(compile(ast.Expression(node), "<worker>", "eval"),
                  {"WORK": Path("/kaggle/working/release")})
    compile(worker, "<gpu-startup>", "exec")
    assert worker.index("original.verify_bundle()") < worker.index("install_overlay") < worker.index("return start")
    assert "AI_PROMPT_CACHE_SCOPE='nails'" in worker and "AI_INFERENCE_PROFILE='0'" in worker
    assert "Loaded facade does not match the approved Nail release" in "".join(cells[1]["source"])
    for name, expected in evidence["fallback"].items():
        assert sha256((ROOT / name).read_bytes()).hexdigest() == expected
    assert sha256((ROOT / "artifacts" / GPU_NAME).read_bytes()).hexdigest() == GPU_SHA


def test_new_package_cannot_replace_a_published_release_artifact(tmp_path):
    path = tmp_path / "release.bin"
    immutable(path, b"original")
    immutable(path, b"original")
    with pytest.raises(ValueError, match="Refuse to replace"):
        immutable(path, b"different")
    assert path.read_bytes() == b"original"
