# Makeup expansion review and missing Manga Lash test

Date: 31 October 2026  
Status: saved gallery ready; Manga pilot prepared, GPU run not started

## Review the existing results now

Open artifacts/makeup-expansion-review-20261031/review-self-contained.html in Edge or Chrome.

The page contains64embedded images:

- Expanded Berry and Icy Silver beside the source and existing Soft Glam baseline.
- Original versus saved guidance4.0,3.0and2.5 comparisons for Natural and Red Lip.
- All ten existing looks at the previously selected experimental2.5 setting.
- An explicit empty Manga Lash slot, because it has not been generated.

These are verified saved project outputs, not newly generated or recolored images. All24saved STYLE-VAL-001 Makeup outputs were checked against their PNG/RGB hashes. The gallery's64images, enlargement and390pxmobile layout pass an Edge browser check.

The original white-cast, smoothing and facial-detail changes remain visible. Lower guidance did not establish a fix. Original deployed settings remain pinned at4.0;2.5is the earlier selected experimental candidate, not a silently deployed change. No Makeup appearance approval is inferred from the separate Hair/Nail approval.

Makeup Application pricing remains **Price to be confirmed**.

## Why the new test is short

Berry and Icy Silver already have two verified examples each. Repeating them at identical settings would not add new evidence. The new notebook reuses those four images and two existing Soft Glam images.

It runs only three new forwards:

1. Reproduce saved Soft Glam on054109exactly. A mismatch stops before Manga generation.
2. Generate Manga Lash on054109.
3. Generate Manga Lash on056266.

The same existing MAKEUP-001 adapter is used at full1.0,20steps,seed1977,512square and experimental guidance2.5. There is one fixed Manga prompt, no settings sweep, new dataset, retraining, replacement model, tone recoloring or mask correction. This is a style-capability test, **not a white-cast fix**.

Earlier forwards were roughly64seconds each. Expect about3minutes15seconds inference, with setup/model download additional; this is an estimate.

## Kaggle steps

1. Make a separate private copy of the tested pinned Kaggle notebook. Preserve the working website/demo notebook.
2. Import notebooks/makeup_expansion_completion.ipynb.
3. Attach exactly one existing input containing capstone_train002_20260928_v1.bin.
4. Select the reviewed T4 GPU and enable Internet. No CPU bundle, API Secrets or Render configuration is needed.
5. Run Cell1 once, then Cell2 once.
6. Download beautycore-makeup-expansion-results.zip after DOWNLOAD_MAKEUP_EXPANSION_RESULTS, including on failure.
7. Return the ZIP for review, then stop this test session.

The notebook embeds two reused research portraits, their author/license metadata, six verified saved images and the frozen reference report. Keep it/results private. These sources are development evidence, not untouched final evaluation.

If host/package/model/continuity checks fail, preserve the error and ZIP; do not bypass guards or repeatedly rerun setup. A two-hour process-group limit and finally archive preserve partial evidence.

## What to review

Open results/review-self-contained.html from the returned ZIP. It compares source, Soft Glam, Berry, Icy Silver and Manga on both sources. Click any image to enlarge.

Assess separated lash clusters, unchanged eye/face geometry, visible intended cosmetics, complexion/texture and unwanted edits. Successful generation alone does not establish good makeup or acceptable skin-tone preservation.

No application/model/deployment changes are made by this notebook. A Makeup profile still requires explicit appearance selection and matching production integration before rollout.
