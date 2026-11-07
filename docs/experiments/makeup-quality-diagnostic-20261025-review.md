# MAKEUP-QA-001 completed diagnostic review — 25 October 2026

**GPU continuation/artifact integrity VERIFIED; visual review DONE; corrective setting NOT ACCEPTED.** The review is qualitative Codex inspection, not salon approval.

The recovery succeeded. All12planned images are present:2reused people x2styles x foundation only/current adapter1.0/reduced adapter0.5. The additional current-adapter control reproduces both the saved PNG and decoded pixels exactly. Eight old report rows/images are retained intact;4missing reduced outputs complete. Both adapter groups restore the verified original tensors/full scaling, across100LoRA layers. The original failure log is preserved separately from the successful continuation log.

## What the images show

| Condition | Natural Makeup | Classic Red Lip | Decision |
|---|---|---|---|
| Foundation only: no project adapter | Both inputs receive stronger blush/brow/eye changes than requested, with smoothing and changed facial details. The darker source is closer to its original complexion than with the adapter, but is still visibly edited. | Closest source complexion in the darker input's matched trio. Lip pigment is very saturated and contour/smile details change; not a natural, accepted result. | Useful control; do not substitute it as a production fix. |
| Current adapter:1.0 | Strong pale highlights/lightening and retouching, especially on054109; heavy glam instead of restrained everyday makeup. | Red color appears, but strong additional blush/highlighting and skin/face retouching exceed the lip request. | Confirms existing preservation problem in these examples. |
| Reduced adapter:0.5 | Remains very similar to current; source complexion/texture are not reliably preserved. | Red lip remains visible, but lightening, smoothing and excessive cheek/highlight changes remain. | Hold; halving influence is not a sufficient correction here. |

The lighter input also shows smoothing, stronger cheeks/highlights and facial-detail changes; the darker input makes the lightening particularly clear. These descriptions concern visible image properties, not inferred identity categories.

On these fixed cases the adapter increases the lightened/retouched appearance compared with foundation only. However, foundation-only outputs also over-edit. Therefore the adapter is not the sole source of unwanted reconstruction, and this experiment does not isolate whether particular training targets caused it. The prior audit's retouched paired targets remain a plausible contributor, not a proven complete cause.

A prompt asking for preservation was already used for all conditions. More wording or more flawed examples cannot be presented as a verified solution. All three conditions fail the intended natural-preservation standard in this review; human/salon acceptance remains pending.

## Verification and timing

Archive SHA256:705953d79637dd149defabba4364e91247f67ea95547bf2e5afb8148f0c461c6;5,001,069bytes. CRC and duplicate-name checks pass. All12ordered cases match plan/settings/prompt hashes and the verified checkpoint/preset hashes. PNG/RGB hashes, original portrait pixels, original source inventory, recovery source hashes, effective adapter weights/tensors and exact installed GPU environment match local frozen records. Original report hash and first8rows match the retained partial report. No bundled code was executed for this review.

The recorded TeslaT4 continuation uses the existing pinned model and packages, with no reinstall/redownload. Five new forwards (one control plus4missing outputs) total310.96seconds, about5minutes11seconds. New child foundation loading is56.91seconds separately; other verification/encoding/packaging time is excluded. Foundation-only case median59.00s, original adapter64.51s, reduced63.66s. These are individual worker observations across two child processes/contexts, not a controlled speed benchmark or end-to-end website latency. There is no established speed improvement from reducing adapter influence.

## Recommended smallest next step — PROPOSED

1. Keep deployed settings unchanged and hold new Makeup preset promotion. Do not deploy0.5or replace MAKEUP-001with the foundation solely from this result.
2. Turn the prior target audit into a review list: retain acceptable same-person examples and reject targets that lighten complexion, erase texture, change face/smile geometry or add unrelated styling. Do not automatically reuse the latest generated images as targets.
3. Define a small corrected-data fine-tuning experiment only after reviewing actual available pairs and usage permissions. Keep framing/lighting consistent, add clear visible-style captions where supported, and include varied complexions/capture conditions. If usable pairs are insufficient, report the gap before collecting or generating replacements. This review starts no training/data acquisition.
4. Reserve untouched people for later acceptance, compare any candidate with both foundation/current baselines and require useful makeup together with complexion/identity preservation. The2reused identities now serve diagnostic development, not an untouched final test.
5. Validate an accepted candidate through the existing Makeup/consultation path before a separate deployment. Hair/Nails remain independent; prior failed preservation/inpainting routes are not reopened.

This review changes no application code, prompts, model weights, public catalog, Kaggle demo configuration or Render deployment.

## Private comparison evidence

Columns: **Original → Foundation only → Current1.0 → Reduced0.5**. The upper/lower rows are the2source portraits.

- [Natural Makeup](../../artifacts/makeup-quality-20261025/review-db42b690b2/results/natural_makeup-comparison.jpg)
- [Classic Red Lip](../../artifacts/makeup-quality-20261025/review-db42b690b2/results/classic_red_lip-comparison.jpg)
- [Per-case visual observations](../../artifacts/makeup-quality-20261025/review-db42b690b2/review-by-codex.csv)
- [Machine verification and review](makeup-quality-diagnostic-20261025-review.json)

The returned ZIP, exact reports, logs and images are preserved in the ignored private artifact directory. No image is added to Git.
