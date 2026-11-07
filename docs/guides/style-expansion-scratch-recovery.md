# STYLE-EXP-001: recover the confirmed model-cache disk failure

Date: 25 October 2026. Original ZIP inspection VERIFIED; corrected Kaggle execution still NEEDS VERIFICATION.

## Confirmed cause

The supplied ZIP passed CRC. Its log states: Less than 30 GiB scratch available for pinned Base, no model download started.

Python 3.12.13, Torch 2.10.0+cu128, CUDA 12.8, Tesla T4, the pinned dependencies and Gate 2 adapter-artifact preflight passed. There are no results in the archive. No new style was generated, so it provides no model quality evidence.

The v1 pilot configured its Hugging Face cache inside the working volume. The original model downloader checks the selected volume for at least 30 GiB free before downloading. The archive does not record the exact free-byte count. Do not infer a GPU memory or network failure from this trace.

## Same-session recovery (preferred if still open)

1. Keep the failed pilot session open. Do not restart or rerun the original cells.
2. Open [style_expansion_scratch_recovery.py](../../notebooks/style_expansion_scratch_recovery.py) locally. Copy its entire contents into one NEW code cell at the bottom of the SAME failed Kaggle notebook.
3. Run only that recovery cell once.
4. It prints the actual free GiB for /tmp and, if needed, /kaggle/temp. The first writable candidate with at least 30 GiB is selected. The original threshold and model revision remain unchanged.
5. Recovery reuses the installed packages while rechecking the host, exact package versions and original artifact hashes. It resumes at model download, then runs the same 3 renderer cases and 15 portrait cases.
6. Download the NEW ZIP printed after DOWNLOAD_RECOVERY_RESULTS and return it for review. The original failure ZIP/logs remain intact.

This recovery is restricted to this exact pre-download scratch failure. It refuses an active API/worker, missing original inventory or an existing results folder. It has atomic ownership against a second recovery process. New recovery source has an independent hash receipt; the original candidate inventory is preserved.

If neither volume has enough space, it stops before the model download and records actual disk observations in a new scratch.json inside the recovery evidence directory. Send the newly printed partial ZIP. Do not remove the guard or delete shared caches/datasets to force it through.

## If the session has already ended

Use the corrected [beautycore_style_expansion_pilot_v2.ipynb](../../artifacts/style-expansion-20261025/beautycore_style_expansion_pilot_v2.ipynb) in a separate private Kaggle notebook with the reviewed T4 environment, Internet and exactly one input containing capstone_train002_20260928_v1.bin. No CPU bundle, new API Secrets or Render changes. Run its preparation and execution cells once.

## Verification

49 focused tests passed, including actual-space selection, refusal below 30 GiB, no reinstall during resume, exact environment recheck, preservation of old evidence and partial ZIP packaging. The saved recovery cell hashes the corrected source, and the v2 notebook embeds that source. Existing public catalog checks pass. These are local/CPU checks; successful model download and generated looks still require the operator's Kaggle run.
