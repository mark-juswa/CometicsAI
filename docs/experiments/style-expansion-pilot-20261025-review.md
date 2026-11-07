# STYLE-EXP-001 completed pilot review — 25 October 2026

**Execution and artifact integrity VERIFIED. Visual findings are an AI-assisted review, not salon approval. No candidate is approved for production.**

## What the completed ZIP establishes

The 8,772,403-byte supplied archive passes CRC and its source inventory matches the corrected pilot source. All 15 PNG/file/pixel hashes, ordered cases, prompt hashes and adapter IDs/checkpoint hashes match the configured plan. The two source portraits match the original GPU bundle pixels. Reported active-adapter tensor checks are true for every portrait case.

The scratch correction worked in this run: the model cache was selected on /tmp with about 1048.46 GiB free. Model download, dependency/environment checks and original artifact preflight completed. One foundation was loaded on the recorded Tesla T4.

All 15 portrait calls completed in 967.26 seconds combined (about 16 minutes 7 seconds). Per-call range was 62.07–66.66 seconds, with median 64.76 seconds. Foundation startup was 53.00 seconds separately. These numbers exclude dependency installation, model download and image-sheet generation. They are single-case worker observations, not website timing or a speed improvement measurement. Peak allocated CUDA tensor memory reported was 8311.68 MiB; this is not total device/reserved memory.

Both final old-style restoration images match their initial baseline pixel hashes exactly. This supports adapter restoration for these two controls; it does not validate every existing style's visual quality.

## Visual findings

| Candidate | Observation on this input | Recommended disposition |
|---|---|---|
| Butterfly / TRAIN-001 | Output remains close to the starting short bob; the requested long lower lengths and distinct upper layers are absent. | Hold. Retest on a suitable long-haired input before deciding whether new training is necessary. |
| Butterfly / TRAIN-002 | Some fringe/layer changes, but it remains a short rounded style rather than a clear Butterfly cut. | Hold. No suitable adapter selected from this one case. |
| Two-Block / TRAIN-001 | Little visible distinction from the starting bob. | Hold. |
| Two-Block / TRAIN-002 | A fuller straight fringe is visible, but the short lower section/disconnection is not clearly established. | Retest with front and three-quarter inputs where the sides can be judged. |
| Comma / TRAIN-001 | No clear comma-shaped fringe. | Do not choose this adapter from current evidence. |
| Comma / TRAIN-002 | A distinct curved front strand appears. The curl is rather isolated/elongated; the whole fringe needs stylist review. | Best Hair candidate for the next validation batch, still partial fidelity. |
| Blurred Berry / MAKEUP-001 | Berry color appears, but lip edges look defined and cheek color is strong. Complexion looks substantially lighter and smoother. | Hold for preservation/restraint improvements; do not call this a successful subtle cloud/blurred look. |
| Icy Silver / MAKEUP-001 | Distinct cool metallic eyelids. Lips are vivid red rather than the requested subtle neutral. Complexion is lighter and heavily smoothed. | Style direction achieved in the eyes, but hold until unintended face/skin/lip changes are controlled. |
| Raspberry Jelly / renderer | A restrained raspberry tint retains some source nail detail. | Advance to varied-hand and automatic-mask testing. |
| Pink Aura / renderer | A central pink glow is visibly distinct from a tip gradient. | Advance to varied-hand and automatic-mask testing. |
| Negative-Space Micro-Dots / renderer | Sparse small dark dots are visible over a light/sheered base. | Advance to varied-hand and automatic-mask testing. |

These observations describe this small pilot, not model capability across all users. The Makeup baseline outputs also show smoothing and a lighter complexion; those preservation problems are not specific to the new preset names. The existing side-part undercut control visibly changes facial appearance too. Include those old controls in future preservation review rather than treating their current appearance as a quality target.

## Independent Nails checks

Recomputed from the returned source, mask and output pixels: all three designs changed zero pixels outside the supplied mask and edited all five nail components. All three output pixel hashes also match the earlier local renderer run.

Renderer-only durations were about 0.27–0.34 seconds. This excludes hand detection, automatic segmentation, uploads, image encoding, backend/Render and browser work. The pilot used a historical manual mask; automatic masking is not verified by this result. No Nails adapter was trained or used for these three effects.

## Recommended next step

1. Advance Comma Hair with TRAIN-002 and the three Nail renderer designs to a small varied-input validation batch. Keep all entries experimental.
2. Retest Butterfly on long-haired input and Two-Block on inputs with visible sides. Distinguish unsuitable test framing from an actual training gap; do not conclude that a model cannot produce a cut from a single image.
3. Prepare permissioned same-subject examples for new Hair cuts if prompt/adapter trials remain unreliable. Labels and desired shape must be reviewed by the salon.
4. Prioritize Makeup examples that preserve natural complexion, skin texture and facial geometry. Explicitly review paired-source consistency and the difference between blurred lip edges and heavy outlined lipstick. Do not reuse these heavily retouched outputs as automatically approved training targets.
5. Train/fine-tune only after data review establishes a gap and appropriate examples are available. No new training images were acquired or weights updated in this pilot.
6. Integrate only accepted candidates through the generation catalog, consultation tags, descriptions, actual service estimates and saved-look/booking flow together. No Render/Kaggle demo deployment is performed by this review.

## Private visual evidence

The full source/output images remain outside Git in the ignored private artifact directory.

- [Hair comparison](../../artifacts/style-expansion-20261025/pilot-review-01/portraits/hairstyle-comparison.jpg)
- [Makeup comparison](../../artifacts/style-expansion-20261025/pilot-review-01/portraits/makeup-comparison.jpg)
- [Nails comparison](../../artifacts/style-expansion-20261025/pilot-review-01/nails/comparison.jpg)

Machine evidence: [review JSON](style-expansion-pilot-20261025-review.json). Original supplied archive SHA256: 76a86c97ce2fdd0f5ac38e9f8fe3f1286a5275b54892dfe26fc441529b387bf4.
