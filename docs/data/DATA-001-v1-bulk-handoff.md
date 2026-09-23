# DATA-001 V1/global generation: Supervisor Kaggle handoff

**Current method:** pretrained FLUX.2 Klein Base global image edit, the same path that produced the three V1 pilot images. Masked V2 is optional fallback and is not a prerequisite. This handoff generates only the 27 selected identities missing from the V1 pilot; it never accepts an image or starts LoRA training.

The pinned [selection](DATA-001-selection.json) stays at ten originals per `CrewCut`, `BobHair`, and `LayeredHair`, split eight TRAIN/two VAL per class. The cycle remains `CrewCut → BobHair → LayeredHair → CrewCut`.

## 1. Prepare Kaggle

Use a GPU notebook with Internet enabled. In a Python cell, use the kernel interpreter so the child process sees the same CUDA-enabled PyTorch:

```python
import pathlib, subprocess, sys
repo = pathlib.Path("/kaggle/working/CometicsAI")
if not repo.exists():
    subprocess.run(["git", "clone", "https://github.com/mark-juswa/CometicsAI.git", str(repo)], check=True)
else:
    subprocess.run(["git", "-C", str(repo), "pull", "--ff-only"], check=True)
subprocess.run([sys.executable, "-c", "import torch; assert torch.cuda.is_available(); print(torch.__version__, torch.version.cuda, torch.cuda.get_device_name(0))"], check=True)
subprocess.run([sys.executable, str(repo / "notebooks/data001_generate_kaggle.py"), "--plan-all"], check=True)
```

The plan must list exactly **27 jobs: 21 TRAIN and six VAL**. Do not run if it differs. If the session lacks the pinned EXP-001 Diffusers stack, run its dependency-only preparation, restart the notebook kernel if packages changed, and repeat the CUDA check:

```python
subprocess.run([sys.executable, str(repo / "notebooks/exp001_flux2_klein_kaggle_smoke.py"), "--phase", "prepare"], check=True)
```

The V1 pilot files must exist under `/kaggle/working/data001/original/` and `/kaggle/working/data001/generated/`. In a fresh session, upload the previously supplied `data001_pilot.zip` as a Kaggle input, then set `pilot_zip` in the next cell to its actual Kaggle path. The `--pilot-zip` option restores only the three expected pilot originals, outputs, and JSON sidecars and verifies their hashes. In the original session, omit `--pilot-zip`.

## 2. Run remaining generation

```python
from datetime import datetime, timezone
out = pathlib.Path("/kaggle/working/data001")
out.mkdir(parents=True, exist_ok=True)
pilot_zip = None  # Or pathlib.Path("/kaggle/input/<your-upload>/data001_pilot.zip") in a fresh session.
cmd = [sys.executable, str(repo / "notebooks/data001_generate_kaggle.py"), "--all"]
if pilot_zip is not None:
    cmd += ["--pilot-zip", str(pilot_zip)]
log_path = out / f"v1_bulk_run_{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}.log"
with log_path.open("w", encoding="utf-8") as log:
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for line in process.stdout:
        log.write(line)
        log.flush()
        print(line, end="")
    assert process.wait() == 0, f"Generation stopped; preserve {log_path} and current artifacts"
```

No V2 review or approval file is required. The runner verifies the restored V1 pilot evidence and the fixed source/model revisions, uses GPU 0, FP16 CPU offload, 512×512, 20 steps, guidance 4.0, seed 1977, and `/tmp/hf-cache`. It never generates the three pilot identities again. Existing output files are skipped only after their sidecar hashes match. A structural error or mismatched existing artifact stops the run; inspect before rerunning.

Expected `/kaggle/working/data001/` artifacts after success:

```text
original/                    30 normalized source PNGs
generated/                   30 attempt-1 PNGs + 30 JSON provenance sidecars
full_plan.json               exact remaining 27 jobs
environment_and_source.json  observed runtime and pinned revisions
generation_review_sheet.jpg  source/result review sheet
v1_bulk_run_<UTC>.log        full console output, never overwritten on a later run
```

The result count is **not** an ACCEPT count. Each output still needs a human decision.

## 3. Review and bounded retry

Generate a 30-key manifest with `PENDING` entries and no automatic acceptance:

```python
subprocess.run([sys.executable, str(repo / "scripts/data001_v1_review_template.py"),
                "--generation-dir", str(out),
                "--output", str(out / "reviews.json")], check=True)
```

Inspect `generation_review_sheet.jpg` and the full-resolution images. Set each entry to `ACCEPT`, `REGENERATE`, or `REJECT`, with the actual attempt number and a short reason. ACCEPT means the requested hairstyle is clear, identity remains recognizable, and there are no major artifacts or major scene/pose changes. Minor hair-color, lighting, clothing-detail, or accessory-detail drift may be accepted for Dataset V1. A wrong hairstyle, major identity drift, serious artifact, or major scene/pose change warrants REGENERATE or REJECT.

One reviewed failure may receive **one** deterministic seed-only retry. Example for `LayeredHair_4` if its review is `REGENERATE`:

```python
subprocess.run([sys.executable, str(repo / "notebooks/data001_generate_kaggle.py"),
                "--retry", "LayeredHair/4.jpg", "--reviews", str(out / "reviews.json")], check=True)
```

This writes `generated/LayeredHair_4_r2.png` and `.json`, preserves attempt 1, and changes seed 1977 → 1978. Inspect attempt 2 and update its review entry to attempt 2 only if accepted. A second failure remains REJECT; reserve replacement requires a documented selection change, not silent dropping. The finalizer will refuse fewer than 30 accepted identity groups.

## 4. Finalize after 30 actual ACCEPT decisions

```python
subprocess.run([sys.executable, str(repo / "scripts/data001_finalize.py"),
                "--generation-format", "v1", "--generation-dir", str(out),
                "--reviews", str(out / "reviews.json"),
                "--output", str(out / "final")], check=True)
```

The finalizer verifies all 30 reviews and generation sidecars, selected source paths and hashes, RGB 512×512 decoding, exact 24/6 identity split, no duplicate hashes or split leakage, aligned captions/reference/target names, 16/4 target-class counts per style, and **48 TRAIN + 12 VAL directional pairs**. It writes `final/manifests/pairs.json`, `final/manifests/reviews.json`, `final/reports/qa.json`, `final/contact_sheets/identity_generation.jpg`, `final/contact_sheets/all_pairs.jpg`, and the paired `train/` and `val/` folders. It refuses a nonempty final output directory so prior results cannot be silently overwritten.

Preserve the generated evidence and final dataset before the Kaggle session ends:

```python
import shutil
shutil.make_archive("/kaggle/working/data001_v1_evidence", "zip", root_dir="/kaggle/working", base_dir="data001")
shutil.make_archive("/kaggle/working/data001_final", "zip", root_dir="/kaggle/working/data001/final", base_dir=".")
```

Return the review manifest, QA report, contact sheets, pair manifest, logs, and generated image archive for audit. DATA-001 is not training-ready until that review and finalizer pass. The source card declares Apache-2.0, but individual upstream photograph rights were not independently documented; retain this provenance limitation in the capstone record.
