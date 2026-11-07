"""Kaggle-only isolated setup watchdog for the four-image Stable-Makeup trial."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import traceback

from stable_makeup_trial import validate


def stage(args,cwd,env,log,timeout):
    started=time.monotonic();last=started
    print("TRIAL_STAGE",log.stem,flush=True)
    with log.open("w",encoding="utf-8") as stream:
        process=subprocess.Popen(args,cwd=cwd,env=env,stdout=stream,stderr=subprocess.STDOUT)
        try:
            while process.poll() is None:
                now=time.monotonic()
                if now-started>timeout:raise TimeoutError(log.stem+" exceeded its time limit")
                if now-last>20:
                    print("STILL_RUNNING",log.stem,round(now-started),"seconds;",log.stat().st_size,"log bytes",flush=True)
                    last=now
                time.sleep(1)
            if process.returncode:
                tail=log.read_text(encoding="utf-8",errors="replace")[-5500:]
                print(tail,flush=True)
                raise RuntimeError(log.stem+" failed; results archive contains its log")
        finally:
            if process.poll() is None:
                process.terminate()
                try:process.wait(timeout=10)
                except subprocess.TimeoutExpired:process.kill();process.wait()


def bootstrap(root,result):
    root=Path(root).resolve();result=Path(result).resolve()
    result.mkdir(parents=True,exist_ok=True)
    plan=validate(root)
    if (result/"attempted.json").exists():raise RuntimeError("Trial already attempted. Download results before another run.")
    if not sys.platform.startswith("linux"):raise RuntimeError("This bootstrap is for a fresh Kaggle notebook")
    gpu=subprocess.run(["nvidia-smi","--query-gpu=name,memory.total","--format=csv,noheader"],
        capture_output=True,text=True,check=True)
    if "T4" not in gpu.stdout:raise RuntimeError("Select Kaggle GPU T4 before running")
    (result/"attempted.json").write_text(json.dumps({"experiment":plan["experiment"],"production_enabled":False})+"\n")
    shutil.copyfile(root/"plan.json",result/"plan.json")
    shutil.copyfile(root/"source-credits.json",result/"source-credits.json")
    env=os.environ.copy()
    for key in ("HF_TOKEN","HUGGING_FACE_HUB_TOKEN","HUGGINGFACEHUB_API_TOKEN","PYTHONPATH"):
        env.pop(key,None)
    env.update(USE_TF="0",MPLBACKEND="Agg",PYTHONIOENCODING="utf-8",
               HF_HUB_DISABLE_IMPLICIT_TOKEN="1",HF_HUB_DISABLE_TELEMETRY="1",
               UV_CACHE_DIR=str(root/"cache/uv"),UV_PYTHON_INSTALL_DIR=str(root/"runtimes"),
               UV_LINK_MODE="copy",HF_HOME=str(root/"cache/hf"))
    boot=root/"bootstrap";venv=root/"env";python=venv/"bin/python"
    started=time.monotonic()
    try:
        stage([sys.executable,"-m","pip","install","--disable-pip-version-check","--no-deps",
               "--target",str(boot),"uv==0.10.12"],root,env,result/"01-bootstrap.log",600)
        uv_env={**env,"PYTHONPATH":str(boot),"UV_PYTHON_PREFERENCE":"only-managed"}
        stage([sys.executable,"-m","uv","venv","--python","3.10.20",str(venv)],
               root,uv_env,result/"02-python.log",600)
        stage([sys.executable,"-m","uv","pip","install","--python",str(python),"-r",str(root/"requirements.txt")],
               root,uv_env,result/"03-dependencies.log",1800)
        import_env={**env,"PYTHONPATH":str(root/"vendor/stable")}
        stage([str(python),"-c",
            "import torch,diffusers;from pipeline_sd15 import StableDiffusionControlNetPipeline;from detail_encoder.encoder_plus import detail_encoder;"
            "assert torch.cuda.is_available();print('IMPORTS_PASS',torch.__version__,diffusers.__version__,torch.cuda.get_device_name(0))"],
            root,import_env,result/"04-imports.log",120)
        remaining=max(1,plan["max_seconds"]-(time.monotonic()-started))
        stage([str(python),str(root/"stable_makeup_trial.py"),"--root",str(root),"--result",str(result),"--stage","download"],
              root,env,result/"05-downloads.log",min(3600,remaining))
        remaining=max(1,plan["max_seconds"]-(time.monotonic()-started))
        stage([str(python),str(root/"stable_makeup_trial.py"),"--root",str(root),"--result",str(result),"--stage","infer"],
              root,import_env,result/"06-inference.log",min(1800,remaining))
        status={"status":"COMPLETE_REQUIRES_VISUAL_REVIEW","seconds":time.monotonic()-started,"production_enabled":False}
    except Exception as exc:
        (result/"traceback.txt").write_text(traceback.format_exc(),encoding="utf-8")
        status={"status":"FAILED_NO_DEPLOYMENT","error":str(exc),"type":type(exc).__name__,
                "seconds":time.monotonic()-started,"production_enabled":False}
        print("TRIAL_STOPPED",str(exc),flush=True)
    (result/"status.json").write_text(json.dumps(status,indent=2)+"\n")
    print(status["status"],flush=True)


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root",required=True,type=Path);parser.add_argument("--result",required=True,type=Path)
    args=parser.parse_args();bootstrap(args.root,args.result)
