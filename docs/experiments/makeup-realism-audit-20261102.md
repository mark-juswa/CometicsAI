# Makeup realism review, 2 November 2026

**Audit DONE / evidence VERIFIED for the saved cases / current appearance REJECTED / correction IN PROGRESS / production integration NOT STARTED.**

## Scope and image roles

The user rejects pasted cosmetics and regenerated facial appearance. This is the same standing requirement: recognizable selected makeup on the original person, natural complexion and texture, with unrelated regions preserved. Increasing or decreasing a global intensity is not an accepted remedy.

All six saved final comparisons in MAKEUP-REFERENCE-001 v4.1 were inspected at native size. They cover Natural Makeup, Classic Red Lip and Cloud/Berry Lips on the same two reused development portraits. No new image was attached to this message. Findings refer to this existing matrix, not an unseen new photograph.

The original photograph is the only acceptable face canvas. The style selection is the intended cosmetic design. The saved middle panels called selected existing makeup are previous AI generated outputs for those style IDs, not independent photographs of real makeup. They contain changed facial shading, texture and other detail. They are imperfect guides, not an approved face or ground truth cosmetic layer.

The frozen plan records those raw generated output paths. The Makeup worker currently takes a portrait and a style ID and uses fixed text presets. It does not take a separate reference photograph. Consequently, exact matching to an independently chosen reference has not been implemented or verified. If the user means another reference photograph, its identity remains NEEDS VERIFICATION. No new reference or model is assumed.

## Observed defects

The darker portrait shows a conspicuous pale or magenta lip rim, sharp mouth boundary and cool cheek/eyelid patches. Classic Red has an especially solid lip treatment. The lighter portrait retains its skin detail but has noticeably darker filled brows and rigid lipstick boundaries. Cloud/Berry has obvious magenta pigment on the cheeks. All three styles on both portraits remain rejected for naturalness. No successful subset is inferred.

The generated guides show the alternative failure: very smooth, pale, altered faces. They are not suitable replacement canvases. The offline transfer does use the original photograph as its canvas; source fidelity alone did not make the applied cosmetics realistic.

## Code and numerical evidence

The current lip layer in scripts/makeup_reference_application.py uses parser lip labels 11 and 12, a 1.5 pixel inward feather and smoothed reference Lab plus source fine detail. Lab includes lightness as well as color. It therefore imports broad reference lip shading and shine, not only pigment. Its overlap guard only checks reference lip coverage above 0.65. Neither this guard nor an inward feather proves that the mask follows the visible source lip boundary.

The two source parser masks and cached landmark lip rings disagree. Their intersection over union is 0.7280 and 0.6915. Respectively, 617 and 61 candidate lip mask pixels lie more than two pixels beyond the estimated outer landmark contour; 274 and 171 lie more than two pixels inside the estimated open mouth contour. These are disagreements between imperfect estimates, not hand labeled proof of exactly where real lipstick spills. Blindly intersecting the estimates could remove legitimate lip pixels. The boundary requires visual validation against the original pixels.

Mean absolute source lip lightness changes range from 7.562 to 26.402 Lab units across the six cases. Some lightness change can be legitimate lipstick. These values alone do not measure artificiality. They confirm that this code does more than transfer color while preserving original lip shading.

For cheeks, cosmetic_chroma_field directly approaches selected reference chroma at high coverage while keeping source lightness. The references have pale foundation and altered lighting. Matching their chroma is not equivalent to recovering a cosmetic pigment that blends naturally on a different underlying complexion. The previous lower chroma error result is not a realism improvement claim.

The red excess heuristic estimates blush from neutral samples and an approximate cheek support. It does not identify a true cosmetic alpha layer. Nonzero saved blush masks cover about 65.5 to 71.6 percent of parser skin, including very small blurred values. This is not a claim that all those pixels have equally visible blush. The visible patch extent must be assessed separately.

The brow branch deliberately deposits selected dark density. The saved outputs change 1,609 to 2,214 source brow pixels. That conflicts with the user's current explicit eyebrow preservation requirement. Earlier tests allowed darker brows and therefore did not enforce this requirement.

Source teeth/mouth interior, nose, checked eye cores, hair and other protected parser regions have zero changed pixels in the saved transfer outputs. This proves exact equality in those checked regions only. It does not prove natural cosmetic boundaries, preserved texture everywhere or reference fidelity. Landmark lip estimates and parser labels are not ground truth.

## Method limitation

A flattened generated RGB image mixes foundation, pigment, lighting, smoothing and regenerated detail. The existing parser labels skin, eyes and lips, but does not return separate reliable blush, eyeshadow and foundation layers. Landmarks locate features approximately and do not identify the exact visible cosmetic edge. This implementation cannot reliably separate all those effects and has not met the requested realism.

The source canvas can be preserved. Realistic, faithful cosmetic separation and application remain unverified. Another face generation or global intensity sweep would not establish either. No full face regeneration was attempted.

## Smallest next correction plan

1. Freeze the original canvas and reference identities. Keep source eyebrows, eye interiors, teeth, nose, hair, lighting and background protected. Cosmetic coloring may change lip or eyelid pixels, but may not relocate the original feature geometry.
2. Prove source lip boundaries first, using one fixed Classic Red look on both existing portraits. Compare parser and landmark estimates against enlarged original lip edges and the open mouth. Establish an inward soft coverage map with no teeth or surrounding skin changes. Reject uncertain alignment rather than silently clipping to an arbitrary contour.
3. Test pigment application separately from generated shading. Retain original lip creases, highlights and shadow structure. Do not paste the generated lip lightness or specular highlight. Any intentional pigment darkening must be separated from copied reference illumination. A manually confirmed contour is diagnostic evidence only, not proof of an automatic production method.
4. Only after the lip proof passes, isolate cheek and eyelid placement and color from foundation and broad facial shading. Test spatial boundaries and source texture separately from pigment visibility. Do not use closer absolute reference chroma as the acceptance target or revive a rejected global opacity, ellipse or reflectance preset.
5. Review all three fixed looks on both portraits. Acceptance requires recognizable makeup plus natural boundaries at native size. Pixel checks protect the source, but cannot replace this visual gate. Add explicit unchanged brow and noncosmetic pixel checks, lip boundary checks and original texture/light tests appropriate to the revised method.
6. If reliable cosmetic separation still cannot be demonstrated, report that limitation and review a materially different method before further work. No automatic promotion, all style claim or full face regeneration is authorized by a failed proof. Production asset integration, fresh inputs and Kaggle memory/latency tests follow only an accepted local method.

This plan addresses a boundary and material separation problem. It is not a promise that another strength value will solve realism.

## Artifacts and preservation

The self contained audit gallery contains original, generated guide and rejected candidate for each case, plus exact source/candidate lip crops. Crops are existing pixels, not new corrected results. Source attribution is retained. audit.json contains the reproducible measurements and metric limitations.

No algorithm, model, original image, frozen plan, historical output, serving configuration, dependency, database, credential or cloud service was changed. No new inference, generation, download or paid call occurred. Thirty nine checked source, input, output and serving/release hashes remain unchanged, including the nine prior serving/release checks.

Previous 34 technical test passes remain historical evidence of their stated invariants, not acceptance of these images. The previous appearance record is now explicitly superseded by this user rejection.

Evidence: [audit gallery](../../artifacts/makeup-realism-audit-20261102/review-self-contained.html), [measurements](../../artifacts/makeup-realism-audit-20261102/audit.json), [prior code](../../scripts/makeup_reference_application.py), [frozen image roles](../../data/makeup/MAKEUP-REFERENCE-001/plan.json), [worker](../../scripts/makeup_inference_server.py).

Gallery verification passed in headless Microsoft Edge: all 30 embedded photo/crop panels load across six cases, desktop and 390 pixel mobile layouts have no horizontal overflow, and no script errors were observed. This verifies presentation only, not makeup appearance. Browser receipt is preserved beside the audit.
