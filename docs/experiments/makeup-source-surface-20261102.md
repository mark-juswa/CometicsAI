# Source based Makeup correction attempt, 2 November 2026

**Bounded lip component DONE / technical checks VERIFIED / lip appearance EXPERIMENTAL / full Makeup NOT SOLVED / combined proof REJECTED / production integration NOT STARTED.**

## Request and actual pipeline

The user authorizes implementation, testing and comparison of the smallest reliable correction, preserving the original person and the working application. Recognizable selected makeup and natural source appearance remain joint requirements. This does not approve replacing the full look with lipstick alone.

The live path is verified in scripts/makeup_inference_server.py: MakeupRuntime.generate pads the original to 512 square, passes it with a fixed style prompt to the FLUX pipeline and returns the generated image. The prompt requests preservation, but there is no source pixel lock, original geometry mask or source texture reconstruction in that return path. scripts/unified_gate3_server.py uses this same MakeupRuntime view under the shared adapter owner. The remote engine validates model identity, style and PNG shape, not facial preservation. The raw generation may therefore change the whole face despite the text instruction.

The previously rejected offline transfer had separate defects: parser masks with inaccurate visible lip edges, reference lip lightness and highlight transfer, approximate cosmetic separation, direct pale reference chroma targets and modified brows. No inference setting sweep was used in this work.

The six examples are Natural Makeup, Classic Red Lip and Cloud/Berry Lips on two reused development portraits. The alleged reference panels are previous generated outputs for those style IDs, not clean real cosmetic layers or a separate reference photograph supplied to the live model.

## Implemented bounded correction

New scripts/makeup_surface_application.py implements apply_lipstick as an isolated component. It never imports or starts a generation service.

The original RGB photo is the only output canvas. Source lip parser labels and source outer/inner landmark contours determine coverage. The generated reference cannot change lip geometry. The contour agreement guard rejects uncertain estimates. The 0.65 threshold is a development guard covering these two cases, not a validated probability of anatomical correctness.

Coverage is zero on the outermost supported pixel and fades inward across three pixels. Previously the distance transform assigned distance one at the boundary, so a short feather still put substantial color on the first edge pixel. The repair changes the boundary condition, not a global makeup strength.

The method reads one robust lip palette from the reference interior. It never transfers the generated mouth texture, highlight position, facial shading or spatial lip color image. A constant Lab color offset in the fully covered source interior preserves source lightness differences rather than multiplying away surface contrast. The lightness offset is limited to avoid crushed source shadows or clipped highlights. Existing gamut compression reduces unsupported chroma while preserving target lightness. The RGB delta is applied relative to original RGB, avoiding unintended color conversion changes outside the requested effect.

The source and reference palette samplers now use the same support rule. This gives exact no change when source and reference are the same image; two actual photo checks pass.

This is not a finished Makeup application. The module applies lipstick only. No blush, eyeshadow, new lashes or brows are changed. These component images are not a proposed reduced finished look and are not connected to live requests.

## Evidence and failed probes

All final six lip comparisons were inspected at native size. They retain original skin, eyes, brows, nose, teeth, face geometry, hair and scene exactly outside the small lip effect. Source lip surface variation is more visible than in the rejected dark material probes. There can still be conservative edge underfill and an obvious tint transition on smiling lips. Human acceptance has not been recorded.

Classic Red is lighter and warmer than the generated dark red guide. The shadow guard prevents a close absolute dark shade at the expense of source lip detail. Natural on the lighter portrait changes little because its selected lip palette is close to the source. Berry remains a visible tint. These are limits, not evidence of exact style fidelity.

The intermediate lip probes are preserved:
1. lip-proof-01 left lightness unchanged, so dark red became coral.
2. lip-proof-02 scaled lightness to the dark palette, flattening surface contrast.
3. lip-proof-03 used material channel gains. A generated reference had median green equal to zero, and copying this material suppressed source channel detail.
4. lip-proof-04 used a bounded constant source color offset and a zero edge. An inconsistent source/reference palette support was then corrected in v4.1, lip-final.

A separate full-proof-01 attempted to remove reference complexion and transfer smooth pigment effects to source cheeks and eyelids. All six saved comparisons were inspected. They preserve original features but produce orange cheek patches and inadequate selected eye makeup. All six are **REJECTED**, not candidate release images. The full application function was removed from the retained module. Its exact code snapshot, outputs and measurements remain only with failed experiment evidence. No additional full look variants or intensity sweeps were pursued after this failure.

The cause is not resolved by stronger or weaker makeup: the flattened generated face still does not provide reliable separate pigment, foundation, lighting and texture layers.

## Tests

Command:

    python -m pytest backend/tests/test_makeup_surface_application.py backend/tests/test_makeup_reference_application.py backend/tests/test_makeup_cosmetic_separation.py -q

Result: **51 passed in 13.86 seconds**, with17new checks and34existing regression checks. No tests were skipped in this local run.

The new checks cover six exact output reproductions and frozen code/input/landmark hashes, unchanged input arrays, zero edits outside the source lip support, original mouth opening and feature protection, zero boundary coverage, preserved interior source lightness gradients within RGB rounding, two actual identical image no change cases, refusal of uncertain/invalid contours, missing lip samples and invalid images.

Changing all generated face pixels outside the selected lip samples has no effect on output. Reordering the selected reference lip pixels, including highlight positions, has no effect on output. These tests prove this component cannot paste generated face detail or spatial lip texture. They do not prove realistic appearance, exact shade match, complete original lip texture preservation after gamut compression, or full Makeup fidelity.

The full proof pixel protection checks passed but its appearance failed. This distinction remains explicit.

## What remains and practical alternative

The requested full fix remains **IN PROGRESS**. There is no accepted automatic full Makeup correction to deploy. The existing generator and simple pigment extraction from its output have not produced faithful, natural cheeks and eye cosmetics on the fixed examples.

**PROPOSED practical alternative:** keep original source rendering, but define the cosmetic layers explicitly with an artist or salon review. Each supported style needs a real approved lip shade, cheek pigment and blended coverage, eye colors and placement, and any intended liner/lash treatment. Fit those cosmetic layers to source geometry. Do not infer them from the pale, smoothed generated face.

This would use AI for facial localization and source based cosmetic rendering, a direction the user previously allowed. It does not mean earlier rejected faint procedural defaults, generic ellipses or guessed palettes are now acceptable. One concrete authored look must first pass these same original photos with visible eyes and cheeks and natural boundaries. The purpose of authoring is to remove ambiguous layer extraction, not adjust an overall opacity again. No existing approved authored layers are claimed.

If exact automatic arbitrary reference transfer is required, a different makeup transfer method would need a separate evidence based evaluation. No replacement model, new training data or paid API is adopted or promised here. The user must review a material method change before production integration. Retain existing image transport, saving/booking data, authentication and Hair/Nail behavior regardless of a future Makeup method.

## Files and preservation

Retained implementation: [component](../../scripts/makeup_surface_application.py), [evaluator](../../scripts/evaluate_makeup_surface_application.py), [tests](../../backend/tests/test_makeup_surface_application.py). Frozen plan: [MAKEUP-SURFACE-001](../../data/makeup/MAKEUP-SURFACE-001/plan.json).

Evidence: [comparison gallery](../../artifacts/makeup-surface-20261102/review-self-contained.html), [verification receipt](../../artifacts/makeup-surface-20261102/verification.json), [final component report](../../artifacts/makeup-surface-20261102/lip-final/report.json), [rejected full proof](../../artifacts/makeup-surface-20261102/full-proof-01/report.json).

Thirty nine prior code/input/output/release hashes were rechecked unchanged, including all nine prior serving/release assets. No live module imports the new code. No Hair/Nail/business UI/DB/API change, model inference, training, model download, dependency install, Git commit/push, new secret, Render deployment or Kaggle session occurred. Actual Kaggle memory and total request latency are untested. This is a partial implementation with preserved failed evidence, not a completed or deployed full Makeup fix.

Gallery verification passed in Microsoft Edge:36embeddedpanels across6cases, native512viewer, original/result toggle,390pixelmobile with no horizontal overflow and zero script errors. Final implementation/frozen-plan hashes and39prior hashes pass. This checks evidence presentation and integrity, not full Makeup appearance.

The rejected full proof can be reproduced separately with its own archived module, not the retained lip module: python artifacts/makeup-surface-20261102/full-proof-01/evaluate_full_proof.py --output artifacts/makeup-surface-20261102/full-reproduction. The command refuses an existing output directory. Reproduction is optional and would still be a rejected diagnostic, not a deployment route.
