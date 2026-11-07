"""Ensurepip recovery must target only isolated CPU envs and refuse live/later sessions."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import json
import sys
import pytest

ROOT = Path(__file__).resolve().parents[2]
CELL = (ROOT / "notebooks/render_kaggle_cell2_recovery.py").read_text(encoding="utf-8")

def execute_cell(tmp_path, *, listening=False, unexpected=False):
    calls = []
    def command(args, cwd, env, stage):
        calls.append((args, stage))
    def main():
        for name in ("backend-env", "segment-env"):
            args = [sys.executable, "-m", "venv", str(tmp_path / name)]
            if unexpected:
                args[-1] = str(tmp_path / "wrong-env")
            demo.command(args, tmp_path, {}, name + "-create")
        demo.command(["unchanged"], tmp_path, {}, "gpu-bootstrap")
    demo = SimpleNamespace(command=command, main=main)
    spec = SimpleNamespace(loader=SimpleNamespace(exec_module=lambda module: None))
    connection = SimpleNamespace(settimeout=lambda seconds: None,
                                 connect_ex=lambda endpoint: 0 if listening else 1)
    # MagicMock implements context management; no real sockets/processes are opened.
    with patch("socket.socket") as socket_mock, \
         patch("importlib.util.spec_from_file_location", return_value=spec), \
         patch("importlib.util.module_from_spec", return_value=demo):
        socket_mock.return_value.__enter__.return_value = connection
        source = CELL.replace('Path("/kaggle/working/render-kaggle")', "Path(" + repr(str(tmp_path)) + ")")
        exec(compile(source, "<recovery-test>", "exec"), {})
    return calls

def failed_marker(tmp_path, status="starting"):
    (tmp_path / "demo-session.json").write_text(json.dumps({"status":status,"host_ram_bytes":32000000000}))
    (tmp_path / "backend-env-create.log").write_text("Error: ensurepip returned non-zero exit status 1.")

def test_recorded_early_failure_preserved_and_both_envs_targeted(tmp_path):
    failed_marker(tmp_path)
    calls = execute_cell(tmp_path)
    assert not (tmp_path / "demo-session.json").exists()
    assert len(list(tmp_path.glob("failed-before-env-*.json"))) == 1
    assert len(calls) == 5
    for offset, name in ((0,"backend-env"),(2,"segment-env")):
        assert "--without-pip" in calls[offset][0]
        assert calls[offset+1][0] == [sys.executable,"-m","pip","--python",str(tmp_path/name),"install","pip==25.3"]
    assert calls[-1] == (["unchanged"],"gpu-bootstrap")

def test_fresh_session_supported(tmp_path):
    assert len(execute_cell(tmp_path)) == 5

@pytest.mark.parametrize("failure", ["live", "later", "ready", "unknown"])
def test_unsafe_recovery_refused_before_marker_move(tmp_path, failure):
    failed_marker(tmp_path, "READY_FOR_REHEARSAL" if failure == "ready" else "starting")
    if failure == "later":
        (tmp_path / "backend-install.log").touch()
    if failure == "unknown":
        (tmp_path / "backend-env-create.log").write_text("Different failure")
    with pytest.raises(RuntimeError):
        execute_cell(tmp_path, listening=failure == "live")
    assert (tmp_path / "demo-session.json").exists()
    assert not list(tmp_path.glob("failed-before-env-*.json"))

def test_unexpected_env_command_refused(tmp_path):
    with pytest.raises(RuntimeError, match="Unexpected environment"):
        execute_cell(tmp_path, unexpected=True)
