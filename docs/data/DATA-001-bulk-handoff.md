# DATA-001 masked bulk generation and finalization handoff

**Prepared only.** No long generation has run. The three-image V2 masked pilot remains pending Kaggle execution and Supervisor/Project Lead visual review. Every command below that uses `--execute` is conditional on that review. Do not use V1 pilot reviews as V2 approval.

## Gate 1: approve the V2 pilot

Run the [three-image V2 pilot](DATA-001-pilot-v2.md), inspect `v1_v2_comparison.jpg` and each sample's raw/final masks, source, and result. If all three pass, the Supervisor/Project Lead writes two separate files under `/kaggle/working/data001/`:

`pilot_v2_reviews.json` must contain exactly `CrewCut_1`, `BobHair_1`, and `LayeredHair_4`, each with `{"status":"ACCEPT","attempt":1,"notes":"<actual visual finding>"}`. Enter actual review findings, never placeholder text.

`pilot_v2_approval.json` must contain `{"decision":"APPROVE_V2_BULK","pilot_sample_ids":["CrewCut_1","BobHair_1","LayeredHair_4"],"reviewer":"<actual name>","approved_utc":"<actual UTC timestamp>"}`. The runner checks the explicit decision, identity list, artifact hashes, and reviewer information before model/data download. If any pilot output fails, **stop**; these commands do not authorize substitution, a different method, or full generation.

## Gate 2: generate the remaining 27

In a CUDA-enabled Kaggle notebook, use the active kernel interpreter `sys.executable`. Pull the repository after the committed handoff has been pushed. Keep the three pilot folders in `/kaggle/working/data001/pilot_v2_masked/`. On a new Kaggle session, upload and extract the V2 pilot archive to that same directory first. Run the read-only plan before executing:

```python
import subprocess, sys
repo = "/kaggle/working/CometicsAI"
subprocess.run(["git", "-C", repo, "pull", "--ff-only"], check=True)
subprocess.run([sys.executable, f"{repo}/notebooks/data001_bulk_v2_kaggle.py", "--plan"], check=True)
subprocess.run([sys.executable, "-c", "import torch; assert torch.cuda.is_available()"], check=True)
```

If the pinned AI Toolkit/Diffusers environment is absent, prepare dependencies only:

```python
subprocess.run([sys.executable, f"{repo}/notebooks/exp001_flux2_klein_kaggle_smoke.py", "--phase", "prepare"], check=True)
```

Then restart the notebook kernel if installation changed imported packages, repeat the CUDA check, and execute only after Gate 1 is signed:

```python
cmd = [
    sys.executable, f"{repo}/notebooks/data001_bulk_v2_kaggle.py", "--execute",
    "--reviews", "/kaggle/working/data001/pilot_v2_reviews.json",
    "--approval", "/kaggle/working/data001/pilot_v2_approval.json",
]
with open("/kaggle/working/data001/pilot_v2_masked/bulk_run.log", "w", encoding="utf-8") as log:
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for line in process.stdout:
        log.write(line)
        log.flush()
        print(line, end="")
    assert process.wait() == 0, "Bulk run stopped; preserve bulk_run.log and generated folders"
```

The runner uses only GPU 0, the pinned FLUX.2 Klein Base and face parser, the selected 21 remaining TRAIN plus six VAL identities, and the V2 512×512 masked edit settings. It writes each `source.png`, semantic/raw/final mask, result, and JSON provenance under `/kaggle/working/data001/pilot_v2_masked/<sample_id>/`. It labels results `PENDING` and does not finalize or train. Do not tune prompts against the VAL identities. If the process fails, retain its outputs/logs and report the exact failure; inspect incomplete folders before any rerun.

Create the review sheet:

```python
subprocess.run([
    sys.executable, f"{repo}/scripts/data001_v2_review_sheet.py",
    "--generation-dir", "/kaggle/working/data001/pilot_v2_masked",
    "--output", "/kaggle/working/data001/pilot_v2_masked/all_review_sheet.jpg",
], check=True)
```

Review all 30 identity groups for hairstyle correctness, identity, facial features, hair color, jewelry, clothing, background, and mask quality. Save a 30-key `/kaggle/working/data001/all_reviews.json` with each actual `ACCEPT`, `REGENERATE`, or `REJECT` decision and notes. Current V2 finalization supports accepted **attempt 1** only. A failed output blocks finalization; a controlled attempt-2 path must be separately prepared and reviewed if needed.

## Gate 3: finalize only 30 accepted identity groups

After all 30 have explicit `ACCEPT` reviews with notes, run:

```python
subprocess.run([
    sys.executable, f"{repo}/scripts/data001_finalize.py",
    "--generation-format", "v2",
    "--generation-dir", "/kaggle/working/data001/pilot_v2_masked",
    "--reviews", "/kaggle/working/data001/all_reviews.json",
    "--output", "/kaggle/working/data001/final",
], check=True)
```

Expected output: 24 TRAIN/6 VAL identity groups, 48 TRAIN/12 VAL directional pairs, 16/4 target pairs per style, aligned reference/target/caption filenames, `manifests/pairs.json`, `manifests/reviews.json`, `reports/qa.json`, and both identity and directional contact sheets. The finalizer validates hashes, dimensions, provenance, protected pixels, split isolation, and duplicate hashes. Human visual judgment is represented by the signed review entries, not by automated metrics.

Package both directories before the session ends:

```python
import shutil
shutil.make_archive("/kaggle/working/data001_v2_outputs", "zip", root_dir="/kaggle/working/data001", base_dir="pilot_v2_masked")
shutil.make_archive("/kaggle/working/data001_final", "zip", root_dir="/kaggle/working/data001/final", base_dir=".")
```

The final image dataset and generated artifacts remain outside Git. Return the review sheet, all reviews, QA report, pair manifest, and relevant logs to Codex for audit. **TRAIN-001 execution stays closed until DATA-001 has actually passed this gate.**
