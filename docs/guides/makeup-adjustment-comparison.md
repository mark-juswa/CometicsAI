# BeautyCore Makeup adjustment comparison — MAKEUP-QA-002

**Local implementation/reference checks VERIFIED. Kaggle execution and quality acceptance NEED VERIFICATION.**

This comparison tests whether the existing makeup can stay visible with less pale foundation/retouching. It changes one factor at a time:

| Column | Guidance | Prompt | Adapter |
|---|---:|---|---:|
| Current reference | 4.0 | Original | 1.0 |
| Lower guidance | 3.0 | Original | 1.0 |
| Matched foundation | 4.0 | Original plus specific source-complexion/foundation instructions | 1.0 |

All keep seed1977,20steps,512x512, the same two source portraits and Natural Makeup/Classic Red Lip. Four saved current controls are retained. One extra current control must reproduce the saved pixels before the8candidate images run: **9new calls,12main comparison images plus1separate control.**

## Run in the still-open completed diagnostic session

1. Keep the completed private Makeup diagnostic notebook/session open. Keep its original cells and results unchanged.
2. Open [makeup_adjustment_cell.py](../../notebooks/makeup_adjustment_cell.py) on this computer.
3. Copy the entire file into **ONE NEW code cell** below the earlier cells in that SAME notebook.
4. Run only that new cell once. Do not rerun setup, the old12case diagnostic, or the recovery cell.
5. Expect environment/artifact checks, one foundation load from the existing cache, then MAKEUP_ADJUST START/DONE messages for9calls. The repeated control must print MAKEUP_ADJUST CONTINUITY PASSED.
6. Download the NEW ZIP printed after **DOWNLOAD_MAKEUP_ADJUSTMENT_RESULTS**. Its name starts beautycore-makeup-adjustment-results-. It appears under the same printed working directory in Kaggle's Output panel.
7. Return that ZIP for review. If it fails, download/return the partial ZIP too; do not remove checks or repeatedly run the cell.

At the previous roughly64seconds per call, expect around10–12minutes including model loading, but this is only an estimate. There is no package reinstall or model download. A missing cache or environment mismatch stops instead of silently rebuilding.

This cell is specifically tied to the reviewed completed report from beautycore-makeup-quality-resumed-db42b690b2.zip. Original source inventory, source/result hashes and adapter ownership are checked. It writes new uniquely named source/plan/result/evidence files and preserves all earlier files. Once attempted, its replay guard directs you to return the existing ZIP.

If the session has ended, do not rerun the old notebook to recover this experiment automatically. Report that the cached session ended so a fresh adjustment notebook can be prepared. Do not place this cell in the working production demo notebook.

## Review the results

Each sheet shows **Original / Current reference / Lower guidance / Matched foundation**, with both people on separate rows. Review complexion, texture, recognizable facial geometry/smile, intended lip/eye/cheek color and unrelated changes. The ZIP includes individual PNGs, source portraits, exact prompt/settings/adapter provenance, the old reference report, an unfilled visual-review.csv and setup logs.

A candidate fails if it merely fades the makeup, loses requested colors, darkens the whole face, changes identity or keeps the same pale/retouched skin. No automatic skin score or quality pass is assigned. Reduced guidance and added wording may both fail; the experiment is intended to establish that honestly.

There is no new training, full-image darkening/blending, mask, recoloring or production deployment. Existing public presets remain hash-pinned; new prompts live only inside this experiment. Hair/Nails/consultation serving behavior is unchanged.

The two people are reused diagnostic development examples; success here would still require varied untouched people and salon review before release.

## Local evidence

16new checks plus prior regressions =85passing tests. Actual reviewed report/current PNGs pass preflight; frozen Kaggle helper functions match locally tested helpers. Cell compilation/payload hashes, a partial-ZIP failure simulation, duplicate-run rejection, no-grad lazy-tensor restoration, environment/cache drift guards and public catalog consistency pass. No real CUDA generation ran locally.

[Machine receipt](../experiments/makeup-adjustment-20261025.json). Rebuild only to a new filename with:
python -m scripts.package_makeup_adjustment --output notebooks/another_makeup_adjustment_cell.py


## Returned result, 25 October 2026

GPU run and control/artifact checks are now VERIFIED.9calls completed; both tested adjustments still exhibit whitening/smoothing in visual review. Do not repeat or deploy them as a proven fix. [Completed findings](../experiments/makeup-adjustment-20261025-review.md). No production settings changed.
