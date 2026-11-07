# Makeup guidance 3.0 versus 2.5 — MAKEUP-QA-003

**Local preparation and reference checks VERIFIED. Kaggle execution and visual quality NEED VERIFICATION.**

The client sees guidance 3.0 as more natural than the matched-foundation wording. This is a relative preference, not acceptance of the remaining whitening. This follow-up tests only guidance 2.5 while keeping the original prompts and adapter strength 1.0.

## Run once in the same completed diagnostic session

1. Keep the private notebook that produced beautycore-makeup-adjustment-results-ebdbe64f35.zip open and running. Leave all earlier cells/results unchanged.
2. Open [makeup_guidance_25_cell.py](../../notebooks/makeup_guidance_25_cell.py) on this computer and copy its **entire contents**.
3. Paste into **one new code cell** below the earlier cells in that same notebook.
4. Run only the new cell once. Do not rerun the previous setup, diagnostic, recovery or adjustment cells.
5. Expect environment/artifact checks, cached model loading, then **MAKEUP_GUIDANCE START/DONE 1 / 5 through 5 / 5**. The repeated guidance 3.0 control must print **MAKEUP_GUIDANCE CONTINUITY PASSED** before the four new images.
6. Download the new ZIP printed after **DOWNLOAD_MAKEUP_GUIDANCE_RESULTS**. Its name starts **beautycore-makeup-guidance-results-**. Find it in Kaggle's Output panel under the printed working directory.
7. Send that ZIP for comparison. If anything fails, return the partial ZIP; do not remove checks or rerun repeatedly.

At the previous roughly 64 seconds per call, five calls plus model loading suggest around **6–7 minutes**. This is an estimate. No package reinstall or model download is performed.

If the session/cache is gone, stop and report that it ended. This cell is specifically for the still-running completed session; placing it in the production demo notebook or rerunning old setup is not a recovery method.

## What runs and what is kept

| Setting | Treatment |
|---|---|
| Guidance 4.0, original prompts | Four previous images retained |
| Guidance 3.0, original prompts | Four previous images retained, plus one repeated consistency control |
| Guidance 2.5, original prompts | Four new images |

Total: eight retained images, five new forward calls, twelve main comparison cases and one separate consistency image. Both people and both styles (Natural Makeup and Classic Red Lip) remain. All conditions use adapter 1.0, 20 steps, seed 1977 and 512 x 512.

The cell validates frozen source inventory, exact prior report hash, original source/PNG/RGB hashes, installed environment, checkpoint/tensor/scaling state and cached model index. It writes new source/plan/result/evidence names. Earlier files and ZIPs are preserved. It rejects competing diagnostic locks and repeat attempts.

## How we will choose

Sheets show **Original / Guidance 4.0 / Guidance 3.0 / Guidance 2.5**. Compare the same person and style across columns.

A candidate must show the intended lipstick/eye/cheek makeup clearly while preserving the original complexion, natural texture and recognizable face/smile. A less intense result is not automatically better. Reject a result that loses the requested style or merely replaces whitening with another unwanted face change.

The ZIP contains raw PNGs, source portraits, exact prompt/settings/source provenance, the original reference report, a visual-review CSV, both comparison sheets and setup logs. No numeric skin-quality score, automatic promotion or new training is performed. These are reused diagnostic inputs, not an untouched final test.

This is one narrow follow-up, not an automatic sequence of progressively lower settings. After reviewing it we decide whether any setting is worth broader validation. Render and the deployed model remain unchanged.

[Preparation evidence](../experiments/makeup-guidance-25-20261025.json): 15 new checks, 100 focused tests, real eight-control preflight and exact compiled payload hashes pass locally; no local CUDA image generation.


## Returned result, 25 October 2026

GPU execution and artifact/control checks are now VERIFIED. Five calls completed; eight saved references and the repeated 3.0 control match. Guidance 2.5 keeps the makeup visible but looks close to 3.0 without consistent further preservation benefit. Do not repeat this completed experiment or deploy it automatically. See [completed review](../experiments/makeup-guidance-25-20261025-review.md).
