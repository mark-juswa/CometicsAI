# Selected makeup preservation check — 1 November 2026

**Offline comparison DONE. Technical integrity VERIFIED. Appearance EXPERIMENTAL and rejected by Codex for release. No deployment.**

## Requirement correction

The user rejected the source-only subtle retouch because it removed the desired makeup. The assistant incorrectly treated natural complexion and source fidelity as permission to reduce the makeup. Both requirements must hold together: preserve the original person and preserve the selected makeup style, intensity and color.

The user selected all three offered reference looks: Natural Makeup, Cloud/Berry Lips and Classic Red Lip. This test covers each on two existing development people. It does not prove coverage of every catalog style.

## Work performed

The original photo stays the display canvas. Cached MediaPipe landmarks align the existing selected Makeup image into original coordinates. A local experimental algorithm estimates eye pigment, narrow dark strokes, brow pigment, blush and lipstick. It applies these layers in source coordinates, with source detail retained where possible. There are no new diffusion calls, training runs, photos, dependencies, paid requests or model downloads.

Three versions are preserved. Versions 1 and 2 each tested three cases and failed on pasted edges, blush and incomplete lashes. Version 3 tested all six requested combinations using reference-relative linear-light color ratios. Its algorithm, plan, evaluation driver and verification driver are preserved with hashes.

## Actual result

All six full-size version 3 comparisons were inspected. The source person's geometry, expression, original teeth, background and texture remain visible, but the cosmetics do not match faithfully. Blue/cyan or orange cheek patches, cutout brow/lip transitions and incomplete eye makeup remain. Version 3 is rejected. No user approval is requested for these known failures.

A strength value of 1.0 describes an implementation parameter. It does not prove preserved cosmetic intensity. Zero protected-pixel changes is a source-integrity result, not a cosmetic-quality result.

The saved selected reference is a flattened photograph containing both cosmetics and unwanted complexion/lighting edits. Existing semantic labels do not distinguish foundation, blush, eyeshadow and individual lash strokes. The current estimated pigment/neutral-skin separation confuses some highlights with makeup. This is the remaining implementation bottleneck; it is not evidence that the user needs weaker makeup or a different look.

## Verification and limits

- Six exact RGB reproductions passed using the frozen algorithm.
- Source/reference/parser-map hashes and landmark provenance passed.
- All six cases have zero changes outside the computed allowed mask and zero changes in protected semantic source regions.
- Nine serving-source/release-artifact hashes remain unchanged, including the current Hair/Nail CPU bundle and starter notebook.
- Two reused development people only; no independent generalization, calibrated identity score or skin-tone accuracy claim.
- Local transfer timings exclude model loading and landmark inference. No Kaggle end-to-end speed or shared-memory claim.
- No Git publication, Render/Kaggle configuration, database, secret or live-model changes occurred.

## Next acceptance gate

A cosmetic-separation diagnostic must distinguish cosmetic pigment/strokes from unwanted foundation and lighting before another correction is credible. Keep the original and each selected reference locked. Check blush placement and hue, eyelid pigment, lashes/liner and lipstick separately, then check the combined original-person result. Do not substitute generic makeup, silently reduce intensity or call nearly bare source photos a fix.

Current evidence does not justify production integration. Hair/Nail rollout remains separate. This report does not establish that a reliable correction is impossible; it establishes that this implementation has not delivered it.

## Local evidence

- Frozen six-case plan: [plan-v3.json](../../data/makeup/MAKEUP-LAYERS-001/plan-v3.json).
- Preserved comparisons, algorithm and drivers: [run-03](../../artifacts/makeup-cosmetic-layers-20261101/run-03/).
- Independent receipt: [verification.json](../../artifacts/makeup-cosmetic-layers-20261101/run-03/verification.json).
- Structured review: [review record](makeup-selected-cosmetics-20261101.json).
