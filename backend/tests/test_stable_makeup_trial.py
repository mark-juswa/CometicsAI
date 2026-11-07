"""Trial integrity and failure handling. No network, model download or GPU."""
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import sys
import zipfile

import pytest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"scripts"))
from scripts import stable_makeup_trial as trial
from scripts import stable_makeup_bootstrap as bootstrap


@pytest.fixture
def package(tmp_path):
    files={}
    def add(name,data):
        path=tmp_path/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
        files[name]=sha256(data).hexdigest()
        return files[name]
    source=add("inputs/source.png",b"frozen-source")
    control=add("inputs/control.png",b"frozen-control")
    reference=add("inputs/reference.png",b"frozen-reference")
    plan={"experiment":"STABLE-MAKEUP-001","training":False,"production_enabled":False,
      "steps":30,"guidance":1.6,"seed":1977,"dtype":"float16","max_seconds":7200,"assets":[],
      "cases":[{"id":str(i),"source":"inputs/source.png","source_sha256":source,
                "control":"inputs/control.png","control_sha256":control} for i in range(4)],
      "reference":{"file":"inputs/reference.png","sha256":reference}}
    add("plan.json",json.dumps(plan).encode())
    (tmp_path/"bundle-manifest.json").write_text(json.dumps({"files":files}))
    return tmp_path,plan,files


def rewrite_plan(root,plan,files):
    (root/"plan.json").write_text(json.dumps(plan))
    files["plan.json"]=trial.digest(root/"plan.json")
    (root/"bundle-manifest.json").write_text(json.dumps({"files":files}))


def test_frozen_package_validates(package):
    root,_,_=package
    assert len(trial.validate(root)["cases"])==4


@pytest.mark.parametrize("field,value",[
    ("training",True),("production_enabled",True),("steps",31),("guidance",2),
    ("seed",1),("dtype","float32"),("max_seconds",999999)])
def test_trial_scope_cannot_silently_expand(package,field,value):
    root,plan,files=package;plan[field]=value;rewrite_plan(root,plan,files)
    with pytest.raises(ValueError,match="scope"):trial.validate(root)


def test_duplicate_people_rejected(package):
    root,plan,files=package;plan["cases"][1]=plan["cases"][0].copy()
    rewrite_plan(root,plan,files)
    with pytest.raises(ValueError,match="scope"):trial.validate(root)


@pytest.mark.parametrize("name",["inputs/source.png","inputs/control.png","inputs/reference.png","plan.json"])
def test_input_or_code_tamper_rejected(package,name):
    root,_,_=package;(root/name).write_bytes(b"changed")
    with pytest.raises((ValueError,json.JSONDecodeError)):trial.validate(root)


@pytest.mark.parametrize("name",["../outside","C:/outside","folder\\outside","/absolute"])
def test_path_escape_rejected(tmp_path,name):
    with pytest.raises(ValueError):trial.owned(tmp_path,name)


def test_asset_size_and_hash_both_verified(tmp_path):
    path=tmp_path/"weight.bin";path.write_bytes(b"actual")
    good={"path":"weight.bin","size":6,"sha256":trial.digest(path)}
    assert trial.verify_asset(path,good)==good["sha256"]
    with pytest.raises(ValueError,match="size"):trial.verify_asset(path,{**good,"size":5})
    with pytest.raises(ValueError,match="hash"):trial.verify_asset(path,{**good,"sha256":"0"*64})


def test_checkpoint_metadata_must_match_without_executing_pickle(tmp_path):
    path=tmp_path/"weight.bin";payload=b"metadata checked as bytes; never executed"
    with zipfile.ZipFile(path,"w") as z:
        z.writestr("archive/data.pkl",payload);z.writestr("archive/data/0",b"tensors")
    good={"path":"weight.bin","size":path.stat().st_size,"pickle_sha256":sha256(payload).hexdigest()}
    assert len(trial.verify_asset(path,good))==64
    with pytest.raises(ValueError,match="metadata differs"):
        trial.verify_asset(path,{**good,"pickle_sha256":"0"*64})


def test_duplicate_checkpoint_metadata_fails_closed(tmp_path):
    path=tmp_path/"weight.bin"
    with zipfile.ZipFile(path,"w") as z:
        z.writestr("one/data.pkl",b"x");z.writestr("two/data.pkl",b"x")
    with pytest.raises(ValueError,match="Unexpected checkpoint metadata"):
        trial.verify_asset(path,{"path":"weight.bin","size":path.stat().st_size,"pickle_sha256":sha256(b"x").hexdigest()})


def test_failed_stage_has_actionable_log(tmp_path):
    log=tmp_path/"failure.log"
    with pytest.raises(RuntimeError,match="results archive"):
        bootstrap.stage([sys.executable,"-c","print('specific test failure');raise SystemExit(3)"],tmp_path,None,log,10)
    assert "specific test failure" in log.read_text()


def test_stage_timeout_stops_child(tmp_path):
    with pytest.raises(TimeoutError,match="time limit"):
        bootstrap.stage([sys.executable,"-c","import time;time.sleep(30)"],tmp_path,None,tmp_path/"timeout.log",.01)


def test_linux_only_bootstrap_rejects_host_and_no_gpu_start(package,tmp_path,monkeypatch):
    root,_,_=package
    monkeypatch.setattr(bootstrap.sys,"platform","win32")
    with pytest.raises(RuntimeError,match="fresh Kaggle"):
        bootstrap.bootstrap(root,tmp_path/"result")
