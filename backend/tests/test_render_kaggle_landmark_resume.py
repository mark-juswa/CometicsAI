"""Reuse installed CPU envs while fixing plotting only; refuse unsafe resume."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import json
import pytest

ROOT = Path(__file__).resolve().parents[2]
CELL = (ROOT / "notebooks/render_kaggle_cell2_resume.py").read_text(encoding="utf-8")

def prepare(tmp_path):
    (tmp_path/"demo-session.json").write_text(json.dumps({"status":"starting","host_ram_bytes":32000000000}))
    (tmp_path/"landmark-load.log").write_text("ModuleNotFoundError: No module named 'wrapt'\nValueError: Key backend: 'module://matplotlib_inline.backend_inline' is not a valid value")
    for name in ("backend-env","segment-env"):
        interpreter=tmp_path/name/"bin/python"
        interpreter.parent.mkdir(parents=True)
        interpreter.touch()

def execute_cell(tmp_path, *, live=False, fail_landmark=False):
    calls=[]
    notebook_env={"MPLBACKEND":"module://matplotlib_inline.backend_inline","OTHER":"preserved"}
    cpu_env=dict(notebook_env)
    def command(args,cwd,env,stage):
        calls.append((stage,dict(env)))
        if stage == "landmark-load" and fail_landmark:
            raise RuntimeError("landmark-load failed")
    def main():
        stages=("backend-env-create","segment-env-create","backend-env-pip-bootstrap",
                "segment-env-pip-bootstrap","backend-install","segment-torch-install",
                "segment-install","backend-pip-check","segment-pip-check","segment-load","landmark-load")
        for stage in stages:
            demo.command(["fixture"],tmp_path,cpu_env,stage)
        demo.command(["original-gpu-command"],tmp_path,notebook_env,"gpu-bootstrap")
        calls.append(("api-environment",dict(cpu_env)))
    demo=SimpleNamespace(command=command,main=main)
    spec=SimpleNamespace(loader=SimpleNamespace(exec_module=lambda module:None))
    connection=SimpleNamespace(settimeout=lambda value:None,connect_ex=lambda endpoint:0 if live else 1)
    with patch("socket.socket") as socket_mock, \
         patch("importlib.util.spec_from_file_location",return_value=spec), \
         patch("importlib.util.module_from_spec",return_value=demo):
        socket_mock.return_value.__enter__.return_value=connection
        source=CELL.replace('Path("/kaggle/working/render-kaggle")',"Path("+repr(str(tmp_path))+")")
        exec(compile(source,"<resume-test>","exec"),{})
    return calls

def test_reuses_installs_rechecks_models_and_keeps_api_agg_gpu_unchanged(tmp_path):
    prepare(tmp_path)
    calls=execute_cell(tmp_path)
    assert [stage for stage,env in calls] == ["backend-pip-check","segment-pip-check","segment-load","landmark-load","gpu-bootstrap","api-environment"]
    for stage,env in calls:
        assert env["MPLBACKEND"] == ("module://matplotlib_inline.backend_inline" if stage=="gpu-bootstrap" else "Agg")
        assert env["OTHER"]=="preserved"
    assert len(list(tmp_path.glob("failed-before-landmark-*.json")))==1
    assert not (tmp_path/"demo-session.json").exists()

@pytest.mark.parametrize("reason",["live","gpu","ready","unknown","missing-env","missing-marker"])
def test_unsafe_or_unrelated_resume_stops_before_marker_move(tmp_path,reason):
    prepare(tmp_path)
    if reason=="gpu": (tmp_path/"gpu-session").mkdir()
    if reason=="ready": (tmp_path/"demo-session.json").write_text('{"status":"READY_FOR_REHEARSAL"}')
    if reason=="unknown": (tmp_path/"landmark-load.log").write_text("Different failure")
    if reason=="missing-env": (tmp_path/"segment-env/bin/python").unlink()
    if reason=="missing-marker": (tmp_path/"demo-session.json").unlink()
    with pytest.raises(RuntimeError): execute_cell(tmp_path,live=reason=="live")
    assert not list(tmp_path.glob("failed-before-landmark-*.json"))

def test_failed_model_recheck_prints_actual_log_and_does_not_start_gpu(tmp_path,capsys):
    prepare(tmp_path)
    with pytest.raises(RuntimeError,match="landmark-load failed"):
        execute_cell(tmp_path,fail_landmark=True)
    assert "ValueError: Key backend:" in capsys.readouterr().out
