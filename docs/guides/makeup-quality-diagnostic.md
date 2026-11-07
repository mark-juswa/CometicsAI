# BeautyCore: private Makeup complexion diagnostic

Prepared 25 October 2026. Local preparation VERIFIED; GPU comparison and visual acceptance pending.

## Purpose

Investigate the unwanted complexion lightening and smoothing before adding Makeup styles or replacing the deployed model.

Two reused test portraits and two existing presets (Natural Makeup and Classic Red Lip) are compared under three conditions:

| Condition | Meaning | Images |
|---|---|---:|
| Foundation only | No project adapter is loaded | 4 |
| Current adapter | Existing MAKEUP-001 at its ordinary influence | 4 |
| Reduced adapter | Same checkpoint with influence set to 0.5 | 4 |

Total: 12 images. The same source, prompt, seed1977, 512x512 frame, 20 steps and guidance4.0 are used across each matched trio. Adapter influence is the controlled factor.0.5 is a diagnostic setting, not a proven fix or 50-percent cosmetic opacity.

## Exact steps for the fresh Kaggle session

1. Import [beautycore_makeup_quality_diagnostic_v2.ipynb](../../artifacts/makeup-quality-20261025/beautycore_makeup_quality_diagnostic_v2.ipynb) into a NEW PRIVATE Kaggle notebook. Keep the working demo notebook intact.
2. Use the tested T4 configuration/environment and enable Internet.
3. Attach exactly one dataset containing capstone_train002_20260928_v1.bin. The CPU bundle and API Secrets are not required. The two original evaluation portraits are embedded privately in the notebook.
4. Run the first code cell. Check GPU bundle matches:1 and MAKEUP_QA_WORKSPACE. Duplicate/missing input messages report the count; fix attachments rather than deleting guards.
5. Run the second code cell once. It verifies the original bundle/environment/adapter artifacts, selects writable scratch with at least30GiB free, installs pinned dependencies, downloads the pinned model and prints MAKEUP_QA START/DONE for12cases.
6. Download beautycore-makeup-quality-results.zip from the unique directory printed after DOWNLOAD_MAKEUP_RESULTS.
7. Return that ZIP. Keep it private: it includes the reused portraits and outputs. If a stage fails, download the same partial ZIP instead of adding old recovery cells.

At the previous style-pilot pace (roughly65seconds per portrait),12calls would be about13minutes of generation, plus installation/download/model loading. This is an estimate from that earlier observation, not a guarantee.

A host mismatch stops before generation. Do not remove model/environment checks or change Torch to force it through. The earlier pilot's disk-space fix is included; the original30GiB downloader guard remains.

## What is checked automatically

The original model/adapter/preset hashes remain. Foundation-only verifies there are no active or residual adapter tensors. Adapter cases verify the same checkpoint tensors and the actual multiplier on every loaded LoRA layer. Full influence is restored and verified after both adapter groups, including when inference raises an error.

Restoration here checks tensors/scaling; it does not generate extra restoration images. The run loads one foundation and creates no server, public tunnel, website registration or Render change.

The adapter weight control is supported by the [pinned Diffusers loader](https://raw.githubusercontent.com/huggingface/diffusers/c943837899b16cbae2f619b8dd4f7bb6f07dd81a/src/diffusers/loaders/lora_base.py) and its behavior is checked against actual layer scaling rather than trusting a label. [Pinned PEFT source](https://raw.githubusercontent.com/huggingface/peft/v0.18.1/src/peft/tuners/lora/layer.py).

## What to review

The ZIP contains natural_makeup-comparison.jpg and classic_red_lip-comparison.jpg, original portraits, all12output PNGs, report.json, an unfilled visual-review.csv and setup evidence. Each sheet shows Original / Foundation / Current / Reduced for both people.

Judge complexion preservation, natural texture, recognizable face geometry, plausible and visible makeup, teeth/smile, hair and background. Reduced influence fails if it only removes the makeup. Foundation-only is a control and is not automatically a replacement for MAKEUP-001.

No automatic skin-color or identity-quality score is supplied. Whole-frame brightness would mix lighting, background and cosmetic regions and is not a calibrated complexion score.

These people were previously validation subjects. Repeatedly tuning against them makes them diagnostic development cases; a later final generalization test needs untouched people and varied complexions/capture conditions.

## Release boundary

All conditions are experimental. Production code, style catalogs, prompts, model checkpoint files and existing sessions remain unchanged. No retraining, color-filter workaround, masking/compositing, changed architecture or deployment is included.

Initial v1 verification:13 diagnostic tests and60focused tests passed; the later GPU run exposed the adapter-restoration bug below. Corrected v2/recovery now pass22diagnostic tests and69focused tests. Original GPU archive/nested artifact and notebook/source/portrait hashes pass CPU preflight. Those checks do not establish that0.5improves the images.

Rebuild with a NEW output filename: python -m scripts.package_makeup_quality_diagnostic --output artifacts/makeup-quality-20261025/another_private_copy.ipynb. The packager refuses to overwrite existing evidence.

## Recovery for the failure after image 8

The supplied child log confirms a runner bug during restoration of the current adapter: PEFT attempts to reactivate a parameter and PyTorch rejects an inference tensor. This occurs before the reduced group starts. The experimental runner now uses torch.no_grad instead of torch.inference_mode. The exact lazy allocation inside the GPU offload hook was not separately traced.

A real CPU Torch parameter-materialization reproduction fails after8simulated cases with the old context and completes12with the corrected context. The official [inference-mode documentation](https://docs.pytorch.org/docs/2.10/generated/torch.autograd.grad_mode.inference_mode.html) describes the restrictions and suggests [no_grad](https://docs.pytorch.org/docs/2.10/generated/torch.no_grad.html) where later autograd interaction is required. This correction remains GPU-unverified until the continuation runs.

If the SAME failed session is still open:

1. Keep its two original cells and MAKEUP_WORK unchanged. Do not rerun setup or execution.
2. Open [makeup_quality_resume_cell.py](../../notebooks/makeup_quality_resume_cell.py) locally. Copy its entire contents into ONE NEW code cell at the bottom of that same private Kaggle notebook.
3. Run the new cell once. It verifies frozen source hashes, exact prior failure, saved report and8PNG hashes, installed environment and cached model. It launches a fresh child process without reinstalling dependencies or downloading the model again.
4. Expect5new generation calls: one repeated current-adapter control, then the4missing reduced-adapter images. The control must match the saved control pixels exactly before it continues. If it differs, the runner stops and keeps the evidence; do not remove this comparison guard.
5. Download the NEW ZIP shown after DOWNLOAD_RESUMED_MAKEUP_RESULTS. Its filename begins beautycore-makeup-quality-resumed-. Find it under the same printed working directory in Kaggle's Output panel.
6. Return that new ZIP, even if the continuation fails. The old ZIP/report/8images/source files remain untouched.

At roughly64seconds per prior call,5calls suggest about5–6minutes of inference, plus model loading and verification. This is an estimate, not a measured recovery time.

If the session ended, its cached model/files may be gone. Import the corrected v2 notebook using the fresh-session steps above; it runs the full12case comparison. Do not rerun frozen v1.

A successful continuation combines the retained8outputs and4new outputs into the usual12case comparison, and records its extra control separately. Reports identify the mixed generation contexts and preserve the original partial report. No result currently proves reduced influence fixes complexion drift. Render, deployed models, prompts, presets and the working demo notebook are unchanged.

Recovery evidence: [local checks and artifact hashes](../experiments/makeup-quality-inference-recovery-20261025.json).


## Returned continuation result, 25 October 2026

GPU recovery is now VERIFIED from the returned resumed ZIP:12cases complete,8retained images intact, one extra control pixel-identical, both groups restored. Reduced0.5does not resolve whitening/smoothing in visual review; no setting is promoted. Do not repeat this experiment as though it remains pending. See [completed review](../experiments/makeup-quality-diagnostic-20261025-review.md). Model/website settings remain unchanged.
