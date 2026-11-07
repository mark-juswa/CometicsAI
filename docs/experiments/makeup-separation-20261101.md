# Cosmetic separation repair, 1 November 2026

**Offline repair and comparisons DONE. Technical evidence VERIFIED. Appearance EXPERIMENTAL. Full selected makeup preservation remains IN PROGRESS. No deployment.**

**Later human feedback:** The user found this candidate too subtle. See the [visibility refinement](makeup-reference-visibility-20261101.md). Technical results below remain historical evidence.

## Plan and cause

The user authorized planning and implementing the repair. The [saved plan](makeup-separation-plan-20261101.md) fixes both references: original photo for person and texture, selected Makeup result for cosmetic style, color and intensity. It does not permit removing makeup.

The prior cyan failure reproduces exactly. A pale selected cheek highlight at162,245 was treated as blush because confidence measured color difference magnitude without distinguishing its direction. Channel reflectance ratios then mixed large brightness differences into color. The previous eye mask also excluded the whole parsed eye, including its lash boundary.

The first repair removes the cyan classification, but native review exposes hard dark eye plates and blush boundaries. That failed version is preserved. Local rather than whole complexion contrast, smooth correction fields and feathered source/reference brow boundaries remove those broad mask artifacts in the revised comparisons.

An identical photo regression then exposes five one-code RGB edits. These are color conversion round-trip errors, not real cosmetic differences. Applying only the requested RGB delta to the original fixes the regression. No special identity-image bypass was added.

## Implemented repair

[scripts/makeup_cosmetic_separation.py](../../scripts/makeup_cosmetic_separation.py) adds an isolated offline algorithm:

- Qualify rose/red blush by signed pigment excess, rejecting neutral pale highlights.
- Transfer incremental Lab color, not RGB channel ratios or a new preset palette.
- Subtract the original local color residual to avoid doubling already present cosmetic color.
- Smooth correction fields rather than the original photo. Blush does not borrow reference luminance.
- Use local eye contrast for dark cosmetic strokes rather than the model's whole complexion brightness.
- Permit a bounded parsed eye rim while copying original eye cores exactly.
- Keep source brow/lip outlines, with selected lip color and original fine surface detail.
- Preserve original RGB outside allowed edits, including nose, teeth, hair, neck and scene.

The code reuses alignment and numerical utilities from prior offline scripts. It does not invoke their rejected transfer pipelines. Existing live services do not import this module.

## Actual results and remaining limits

Six final native comparisons cover Natural Makeup, Classic Red Lip and Cloud/Berry Lips on two reused development people. The prior cyan cheek patches and broad dark eye plates are absent in these inspected comparisons. Original features, expression, texture, lighting, hair and scene remain visible. Cosmetic changes include eyelid pigment, lash/liner detail, cheek color and selected lipstick, rather than a nearly bare source photo.

This is a partial candidate, not a full appearance pass. Lash density and shape, brow fill, blush extent and cosmetic intensity do not exactly match the selected generated references. Strong lip edges and finish still merit review. The algorithm does not reconstruct true cosmetic layers from the flattened image. The rose/red blush qualification does not cover every possible blush family.

Source protected-pixel checks do not prove exact selected makeup preservation. No all-ten or expanded-thirteen style support, universal skin-tone accuracy or professional retouch quality is claimed.

## Verification

Nineteen focused checks pass, including the actual pale-highlight regression, visible cosmetic changes, no doubled pigment, identical real-photo no-op, invalid inputs, eye-core protection, unchanged inputs and all six exact RGB reproductions. Six output/input/landmark and source hashes are frozen.

The self-contained gallery loads48embedded images. Full-size viewer, original/candidate toggles, component masks,390pixel mobile layout and zero browser script errors pass. Original photo attribution is included.

Local correction takes approximately1.76to2.27seconds. This excludes parsing, landmark inference, model loading, file IO and generation. It is not a new end-to-end latency result.

Nine checked serving/release hashes remain unchanged. No new diffusion, model inference, training, photos, models, packages, paid requests, database, secrets, Git publication or cloud changes occurred.

## Review and next gate

Open the [embedded gallery](../../artifacts/makeup-separation-20261101/run-03/review-self-contained.html). Compare the third panel against the original for person and texture, and against the middle panel for makeup style and intensity. The original toggle helps reveal geometry and texture differences.

Human review of this partial candidate does not replace remaining technical work. Full cosmetic fidelity, other styles and fresh photos need separate validation. Production integration must supply source/reference parsing and landmark assets at runtime, replace reliance on saved maps, include all required helpers and measure Kaggle RAM and total latency. Those steps are not implemented by this offline experiment. Keep the existing Hair/Nail release separate.

Evidence: [structured record](makeup-separation-20261101.json), [frozen plan](../../data/makeup/MAKEUP-SEPARATION-001/plan.json), [tests](../../backend/tests/test_makeup_cosmetic_separation.py).
