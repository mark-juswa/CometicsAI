# Hair expansion comparison — HAIR-EXP-002

Date: 30 October 2026  
Preparation: **DONE locally**  
GPU evaluation: **NOT STARTED**  
Public Hair additions: **0**

## Purpose

Test the five selected Hair candidates before adding them to the application:

| Candidate | Compared with | Existing adapter | What must be visible |
|---|---|---|---|
| Butterfly Cut | Layered Hair | TRAIN-001 | Shorter face-framing upper layers with long lower lengths retained |
| Textured French Bob with Wispy Bangs | Bob Hair | TRAIN-001 | Jaw-length texture and thin, separated fringe |
| Wolf Cut | Shag Hair | TRAIN-002 | Clearly shorter/choppy crown and longer wispy back |
| Korean Two-Block | Side-Part Undercut | TRAIN-002 | A longer top visibly separated from shorter sides/nape |
| Korean Comma Hair | Curtain Hair | TRAIN-002 | Natural inward-curving fringe strands without a detached ring/U-shaped loop |

These adapter choices are test profiles, not established winners. There is one prompt/adapter per style in this batch. Butterfly and Two-Block retain their prior prompts on more suitable inputs. Comma receives one correction aimed at the previously observed loop-shaped fringe. Wolf and French Bob have not previously been tested.

Four existing source photos are embedded: two with loose long hair, and two with visible sides in three-quarter views. One short-hair source is grayscale, so hair-color preservation cannot be assessed on that image. Compare color on the other source.

The photos come from the existing frozen DATA-002 historical validation manifest. This reuses them for private development, so the batch is not untouched final evaluation. Archive/member hashes, source revision and declared dataset license are retained. Original photo rights were not independently verified. Keep this notebook and its outputs private.

## What runs

The batch produces exactly **21 images**:

- 10 candidate images: five cuts on two sources each.
- 10 corresponding existing-style controls.
- 1 repeated control after switching adapters, which must reproduce its first pixels exactly.

It uses one existing FLUX foundation with the original TRAIN-001 and TRAIN-002 checkpoints, full adapter influence, guidance4.0,20steps,seed1977 and512x512 generation. It preserves exact original training-label/checkpoint checks. New prompts are explicitly experimental; no new training labels or checkpoint claims are fabricated.

No Makeup or Nail generation, new training, public server, API Secrets, tunnel, website registration or Render changes are involved. Accepted Nail release files and the working demo remain separate.

Earlier observations were roughly64seconds per image. Inference may therefore take about23minutes, with environment setup and model download additional. This is an estimate, not a new performance result. The notebook has a two-hour safety timeout and preserves partial results.

## Exact Kaggle steps

1. Open a **separate private copy of the tested pinned Kaggle notebook**. Preserve its reviewed image. Do not run this in the active website/demo notebook.
2. Import **notebooks/hair_expansion_validation.ipynb** from the project.
3. Attach exactly one input containing **capstone_train002_20260928_v1.bin**, the existing unchanged GPU bundle. No new dataset upload or CPU bundle is needed; the four source photos are embedded.
4. Select the reviewed **T4 GPU** configuration and enable **Internet**. No application API Secrets are needed.
5. Run **Cell1 once**. It verifies/extracts the original bundle, validates embedded sources and prints HAIR_WORKSPACE.
6. Run **Cell2 once**. It performs host/package/model checks and prints progress as HAIR_VALIDATION START/DONE1through21. Do not rerun while active.
7. Download the file printed after **DOWNLOAD_HAIR_RESULTS**: **beautycore-hair-expansion-results.zip**. Return the ZIP even if the run fails.
8. After downloading, stop this test session to conserve GPU quota.

A fresh Latest-image notebook may differ from the tested environment. If a guard fails, preserve the error and ZIP; do not remove the guard or install arbitrary replacement package versions.

The archive must appear exactly once under /kaggle/input. Remove duplicate notebook attachments if needed; do not delete the original datasets.

## Reviewing results

Extract the ZIP and open **results/review-self-contained.html** in Edge or Chrome. The original PNGs are embedded, avoiding the earlier broken relative image links. Click any image to enlarge it.

Each style shows the source, its current baseline and its candidate on both selected sources. Five comparison JPEGs are also included. Review:

- Is the promised haircut visible and distinct from the existing style?
- Are the face, expression and original hair color retained?
- Are the hairline, fringe, eyes and background believable?
- Does the result satisfy the style-specific criterion above?

The results include visual-review.csv, source photos/metadata, settings, prompt/checkpoint/output hashes, timings and adapter-state/restoration evidence. Completed inference and exact restoration do not prove appearance quality.

The next step is per-style visual review. Only accepted cuts can advance to explicit production execution profiles, compatible facade/GPU routing, descriptions/prices/save-book checks and matching deployment packages. This notebook does not enable any Hair addition automatically.
