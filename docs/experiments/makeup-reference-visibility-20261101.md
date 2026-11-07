# More visible selected makeup, 1 November 2026

**Local refinement DONE. Technical evidence VERIFIED. Appearance EXPERIMENTAL and human review pending. No deployment.**

The user reviewed the previous separation result and found the cosmetics too subtle. The requirement remains original person plus visibly recognizable selected makeup, with closer color, intensity and placement. This is not permission to apply a different palette, smooth the face or replace the person.

## Cause and implemented changes

The previous placement mask retained only about40to56percent of the detected blush effect at typical confident reference-blush pixels. Its Gaussian falloff weakened cosmetic interiors. Fine lashes also shared a soft shadow mask.

The new isolated [reference application](../../scripts/makeup_reference_application.py) keeps full cosmetic interiors and feathers their boundaries. It uses selected cosmetic chroma with original fine color texture. Adding a residual to warm source skin caused orange drift in an intermediate test, so the final method matches the actual selected chroma inside cosmetic coverage instead.

An anatomical eyelid support fades at the crease before the brow bone. Actual narrow selected lash and liner strokes have separate coverage. Source eye depth is retained, transferring only additional cosmetic contrast. A stronger intermediate version copied too much broad shadow; this was corrected without lowering a global cosmetic strength slider.

Brow pigment darkens original hairs without importing a cool pale outline. No final brow RGB channel can brighten. Original brow geometry stays. Lipstick was already prominent and its final RGB remains exactly equal to the previous candidate in all six cases.

A new identical-photo check found seven one-code color edits within1to2.2pixels of the reference warp boundary. Black padding contaminated smoothing. Both photos now use the same valid sampling domain. The real-photo no-op and a dedicated synthetic boundary check pass. Previous outputs and failing evidence are preserved.

## Actual comparison

The final matrix has Natural Makeup, Classic Red Lip and Cloud/Berry Lips on the same two reused portraits. All six final comparisons were inspected at native size.

Blush and eyelid colors are more visible than in the prior subtle candidate. Actual selected lash detail and denser brows remain visible on the original photo. Source geometry, expression, skin detail, hair and scene remain. No new person or full face image is generated.

A fixed aligned reference-blush region has lower chroma error in all six cases. Mean error falls from8.356to21.309previously to0.989to1.561now. These are color-space diagnostic values, not realism or perceived style scores. Original cheek lightness changes by only about0.065to0.069Lab units on average in those regions. Eyelid color edit magnitude increases in all six cases, with varying amounts. See the [raw metrics](../../artifacts/makeup-reference-20261101/run-05/comparison-metrics.json).

The result is a stronger review candidate, not a guaranteed exact reference match. Apparent shadow hue varies with source lightness and looks more plum/mauve on the darker portrait. Lash density, brow shape and placement are not exact reference copies. Existing strong lip edges remain unchanged. Those details and overall naturalness need explicit human review.

## Verification

Thirty-four checks pass:15new variant checks plus19previous separation regressions. This includes six exact latest output reproductions, unchanged input arrays, original eye cores/teeth/hair/scene, no brow brightening, unchanged lipstick, pale-highlight rejection, selected hue transfer, opaque actual reference strokes, anatomical crease limits and identical-photo/padding checks.

The self-contained gallery contains54embedded images. Full-size viewer, original toggle, component masks,390pixel mobile layout and zero script errors pass. Each section compares original, selected reference, previous subtle result and latest candidate. Original photo attribution is included.

Nine checked serving-source/release hashes remain unchanged. No new diffusion, model inference, training, photos, models, packages, paid requests, database, secrets, Git publication or cloud changes occurred.

## Review and release boundary

Open the [four-panel gallery](../../artifacts/makeup-reference-20261101/run-05/review-self-contained.html). The direct before/after images show visibility changes; the selected reference panel is required to judge actual style fidelity.

The current code remains offline and depends on existing alignment/numerical helpers and cached parser/landmark evidence. Human appearance acceptance, broader fresh inputs and styles, runtime model assets, production provenance/fallback and Kaggle RAM/total latency checks remain required before a versioned integration. No all-style or deployment readiness is inferred.

Implementation evidence: [frozen plan](../../data/makeup/MAKEUP-REFERENCE-001/plan.json), [structured record](makeup-reference-visibility-20261101.json), [tests](../../backend/tests/test_makeup_reference_application.py). The original [repair plan](makeup-reference-visibility-plan-20261101.md) and all intermediate versions remain available.
