"""Create the two-cell Kaggle notebook for the frozen private input bundle."""
import argparse
from hashlib import sha256
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def build(workspace):
    workspace=Path(workspace)
    receipt=json.loads((workspace/"package-receipt.json").read_text())
    first=r'''
from pathlib import Path
from hashlib import sha256
from zipfile import ZipFile
import json, shutil, sys, tempfile

if not sys.platform.startswith("linux"):
    raise RuntimeError("Run this notebook on Kaggle, not on the client computer.")
EXPECTED = "__BUNDLE_SHA__"
matches = list(Path("/kaggle/input").rglob("beautycore-stable-makeup-pilot.bin"))
valid = [p for p in matches if sha256(p.read_bytes()).hexdigest() == EXPECTED]
if not valid:
    raise RuntimeError("Add the NEW beautycore-stable-makeup-pilot.bin as a private input. No old bundles or secrets are needed.")
if shutil.disk_usage("/tmp").free < 30 * 1024**3:
    raise RuntimeError("The trial needs 30 GiB of temporary free space.")
WORK = Path(tempfile.mkdtemp(prefix="beautycore-stable-", dir="/tmp"))
RESULT = Path("/kaggle/working") / WORK.name
RESULT.mkdir()
with ZipFile(valid[0]) as archive:
    names = archive.namelist()
    if len(names) != len(set(names)) or len(names) > 1000:
        raise RuntimeError("Duplicate/oversized bundle listing.")
    manifest = json.loads(archive.read("bundle-manifest.json"))
    if set(names) != set(manifest["files"]) | {"bundle-manifest.json"}:
        raise RuntimeError("Bundle members differ.")
    if sum(item.file_size for item in archive.infolist()) > 100 * 1024**2:
        raise RuntimeError("Bundle exceeds the small input limit.")
    for name in names:
        target = (WORK / name).resolve()
        if "\\" in name or ":" in name or not target.is_relative_to(WORK):
            raise RuntimeError("Unsafe input member.")
        raw = archive.read(name)
        if name != "bundle-manifest.json" and sha256(raw).hexdigest() != manifest["files"][name]:
            raise RuntimeError("Bundle file hash differs.")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
print("TRIAL_WORKSPACE:", WORK)
print("4 source photos, 4 prepared controls, 1 makeup reference verified.")
print("Select GPU T4 and enable Internet, then run Cell 2 ONCE.")
print("No training, secrets, website connection, or Render changes.")
from IPython.display import Image, display
display(Image(filename=str(WORK / "inputs/makeup-reference.png")))
'''.replace("__BUNDLE_SHA__",receipt["bundle_sha256"]).strip()
    second=r'''
import os, signal, subprocess, threading, time, traceback
from zipfile import ZipFile, ZIP_DEFLATED
from IPython.display import FileLink, display

if "WORK" not in globals():
    raise RuntimeError("Run Cell 1 first.")
marker = WORK / "notebook-attempted.json"
if marker.exists():
    raise RuntimeError("This workspace already attempted the trial. Download its result ZIP; do not repeat generations.")
marker.write_text('{"production_enabled":false}')
for name in ("plan.json", "source-credits.json"):
    shutil.copyfile(WORK / name, RESULT / name)
(RESULT / "READ-ME.txt").write_text(
    "Offline pretrained-model test. No deployment. Inspect raw outputs for whitening, identity changes, visible makeup and natural lashes. "
    "Source/reference credits and logs included. No human quality approval is implied.")
process = None
timer = None
expired = {"value": False}
started = time.monotonic()
try:
    process = subprocess.Popen(
        [sys.executable, str(WORK / "stable_makeup_bootstrap.py"), "--root", str(WORK), "--result", str(RESULT)],
        cwd=WORK, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1, start_new_session=True)
    def timeout_trial():
        if process.poll() is None:
            expired["value"] = True
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
    timer = threading.Timer(7200, timeout_trial)
    timer.daemon = True
    timer.start()
    with (RESULT / "notebook-console.log").open("w") as log:
        for line in process.stdout:
            print(line, end="", flush=True)
            log.write(line)
            log.flush()
    process.wait()
    if not (RESULT / "status.json").exists():
        (RESULT / "status.json").write_text(json.dumps({
            "status": "TIME_LIMIT_STOPPED" if expired["value"] else "FAILED_BEFORE_STATUS",
            "exit_code": process.returncode, "production_enabled": False}, indent=2))
except Exception:
    (RESULT / "notebook-error.txt").write_text(traceback.format_exc())
finally:
    if timer:
        timer.cancel()
    if process is not None and process.poll() is None:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait()
    ZIP = RESULT.with_suffix(".zip")
    with ZipFile(ZIP, "w", ZIP_DEFLATED) as archive:
        for path in sorted(RESULT.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(RESULT).as_posix())
    with ZipFile(ZIP) as archive:
        if archive.testzip() is not None:
            raise RuntimeError("Result archive CRC check failed.")
    print("\nDOWNLOAD_RESULTS:", ZIP)
    print("Elapsed:", round((time.monotonic() - started) / 60, 1), "minutes")
    display(FileLink(str(ZIP)))
    if (RESULT / "status.json").exists():
        print((RESULT / "status.json").read_text())
    print("Download this ZIP and send it for review, even if setup failed. Then Stop the Kaggle session.")
'''.strip()
    def cell(kind,text):
        return {"id":sha256(text.encode()).hexdigest()[:12],"cell_type":kind,"metadata":{},"source":[line+"\n" for line in text.splitlines()],
                **({"execution_count":None,"outputs":[]} if kind=="code" else {})}
    note="""# BeautyCore — isolated pretrained Makeup test

Use a NEW PRIVATE Kaggle notebook. Upload beautycore-stable-makeup-pilot.bin as a private Input.
Enable Internet and GPU T4. Run the two cells in order. No old datasets, API keys or Render settings are required.

This evaluates an external pretrained Stable-Makeup model with your reference on four fixed photos.
It does not train a model or replace the deployed Makeup service. Quality and T4 inference remain to be verified.
It downloads about6.4GB of model assets plus the isolated Python/PyTorch runtime. Temporary files stay under /tmp.
One configuration:512px,30steps,guidance1.6,seed1977,FP16. Two-hour hard stop.
Download the result ZIP even if a stage fails; do not keep rerunning the notebook.
"""
    notebook={"nbformat":4,"nbformat_minor":5,
       "metadata":{"kernelspec":{"display_name":"Python 3","language":"python","name":"python3"},
                   "language_info":{"name":"python"},"kaggle":{"language":"python","sourceType":"notebook","isInternetEnabled":True}},
       "cells":[cell("markdown",note),cell("code",first),cell("code",second)]}
    target=ROOT/"notebooks/stable_makeup_trial.ipynb"
    target.write_text(json.dumps(notebook,indent=2)+"\n",encoding="utf-8")
    for item in notebook["cells"]:
        if item["cell_type"]=="code":compile("".join(item["source"]),str(target),"exec")
    print("NOTEBOOK_READY",target)


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--workspace",required=True,type=Path)
    args=parser.parse_args();build(args.workspace)
