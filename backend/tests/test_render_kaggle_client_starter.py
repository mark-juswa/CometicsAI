"""Client starter guards: immutable inputs, safe extraction and pinned host refusal."""
from pathlib import Path
from hashlib import sha256
from zipfile import ZipFile
import importlib.util
import json
import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("client_setup", ROOT / "notebooks/render_kaggle_client_setup.py")
setup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup)


def bundle(tmp_path, name="safe/file.txt", contents=b"known source", member_digest=None):
    archive = tmp_path / "fixture.bin"
    manifest = {"files": {name: member_digest or sha256(contents).hexdigest()}}
    with ZipFile(archive, "w") as zipfile:
        zipfile.writestr("manifest.json", json.dumps(manifest))
        zipfile.writestr(name, contents)
    return archive, sha256(archive.read_bytes()).hexdigest()


def test_verified_source_extracts_without_overwrite(tmp_path):
    archive, digest = bundle(tmp_path)
    target = tmp_path / "source"
    setup.extract(archive, digest, target, "manifest.json")
    assert (target / "safe/file.txt").read_bytes() == b"known source"
    with pytest.raises(RuntimeError, match="new directory"):
        setup.extract(archive, digest, target, "manifest.json")
    assert (target / "safe/file.txt").read_bytes() == b"known source"


def test_outer_hash_rejected_before_write(tmp_path):
    archive, _ = bundle(tmp_path)
    target = tmp_path / "source"
    with pytest.raises(RuntimeError, match="Bundle hash differs"):
        setup.extract(archive, "0" * 64, target, "manifest.json")
    assert not target.exists()


@pytest.mark.parametrize("name", ["../escape", "/absolute", "bad:drive", "bad\\path"])
def test_unsafe_paths_rejected_before_write(tmp_path, name):
    archive, digest = bundle(tmp_path, name)
    target = tmp_path / "source"
    with pytest.raises(RuntimeError):
        setup.extract(archive, digest, target, "manifest.json")
    assert not target.exists()


def test_member_hash_rejected_before_write(tmp_path):
    archive, digest = bundle(tmp_path, member_digest="0"*64)
    target = tmp_path / "source"
    with pytest.raises(RuntimeError, match="member hash"):
        setup.extract(archive, digest, target, "manifest.json")
    assert not target.exists()


@pytest.mark.parametrize("key", ["python", "torch", "cuda", "gpu"])
def test_changed_host_is_refused(key):
    expected = {"python":"3.12.13", "torch":"2.10.0+cu128", "cuda":"12.8", "gpu":"Tesla T4"}
    setup.check_host(expected, expected)
    with pytest.raises(RuntimeError, match="image differs"):
        setup.check_host({**expected, key:"different"}, expected)


def test_notebook_embeds_corrected_runner_and_has_no_outputs():
    notebook = json.loads((ROOT / "notebooks/render_kaggle_client_demo.ipynb").read_text())
    cells = [cell for cell in notebook["cells"] if cell["cell_type"] == "code"]
    assert len(cells) == 3
    for cell in cells:
        assert cell["execution_count"] is None and cell["outputs"] == []
        compile("".join(cell["source"]), "<client-notebook>", "exec")
    runner = "".join(cells[1]["source"])
    assert 'WORK = CLIENT_WORK' in runner
    assert '--without-pip' in runner and '"MPLBACKEND": "Agg"' in runner
    # The embedded runner constructs the GPU output inside the fresh client directory.
    assert "Path({str(WORK / 'gpu-session')!r})" in runner
    assert "An AI service is already running" in runner
    assert "use a fresh notebook session" in runner
