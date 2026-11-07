# Retained lip correction review, 3 November 2026

**Review DONE / source preservation VERIFIED on the saved cases / positive visual direction feedback CONFIRMED / no rendering change justified / full Makeup still IN PROGRESS.**

## Confirmed result

The user reports that the latest result looks much better and explicitly identifies the panel labeled Lip correction ONLY. This positive feedback applies to the retained source_surface_lip_v4_1 component. It is not acceptance of the older generated faces, rejected combined cheek/eye proof, all catalog styles or a production release.

No new photograph was supplied in this turn. All six saved component comparisons were reviewed against their original photos. The matrix remains three selected lip guides on two reused development portraits.

## What is working

The original photo remains the canvas. All checked source skin, eyebrows, eye interiors, nose, mouth interior, hair and scene pixels outside the allowed lip effect remain exact. There is no face warp, smoothing operation or generated facial surface in the retained result.

Within full lip coverage, the original lightness differences remain, rather than importing reference highlight positions or scaling away contrast. The measured range of the interior lightness offset is at most 0.4761 Lab units across these examples, consistent with conversion and RGB rounding. This is a technical source contrast check, not a human texture or realism score.

Coverage falls to zero at the outer supported pixel. The large pasted dark lip treatment from earlier probes is not the retained output. Bright original lip detail remains visible. The source photo and output checksums confirm that the reviewed version has not changed.

## Remaining issues

The parser and landmark intersection is conservative. Native lip crops show small unpainted edge or corner areas on smiling mouths. Those estimates are not hand labeled anatomical truth. The current evidence cannot establish that enlarging their intersection would color only real lip surface.

Classic Red is lighter and warmer than its deeply saturated generated guide. The actual safe lightness offset is limited by original shadows. The guide also contains artificial facial lighting and skin treatment, so matching its absolute shade is not itself proof of a more realistic result.

Natural on the lighter portrait stays close to the original lip color because the sampled shade is similar. Berry is a visible tint, but this one palette method does not reproduce an independently designed gloss, shimmer, multicolor lip or newly placed highlight.

This is still a lip component. It does not apply blush, eyeshadow, eyeliner, lashes or brow makeup. The failed combined proof remains rejected. Keeping this result is not a proposal to remove those cosmetics from the eventual full feature.

## Refinement decision

The user authorizes only necessary, evidence based refinements that preserve the progress. No safe cosmetic change is established by this review.

Widening the mask without more accurate source boundaries could restore lipstick spill. Deepening the shade by bypassing the source shadow guard could crush original lip detail. Copying generated shine could reintroduce a pasted or regenerated surface. Returning to cheek and eye extraction would revive a separately rejected method.

Accordingly, the rendering implementation, masks, settings, original images and retained results are unchanged. This is not a claim that the current method is theoretically optimal. It is a decision that further automatic refinement is not justified by the available examples and uncertain cosmetic boundaries. Better boundary evidence or an independently validated material model would be needed for a targeted next change.

## Verification

Command:

    python -m pytest backend/tests/test_makeup_surface_application.py -q

Result: **17 passed in 6.93 seconds.**

The checks cover all six exact output reproductions, original protection and input immutability, zero boundary coverage, retained interior source contrast, two identical photo no change cases, absence of reference facial pixel transfer, reference lip texture permutation invariance and invalid input refusal.

Forty two prior implementation/input/output/release hashes were rechecked unchanged. All six retained PNG hashes also match their saved report. No new model or image generation call occurred.

The new comparison gallery contains 24 embedded panels: original and current full photo plus exact original/current lip crops for every case. Only the retained result is shown. Microsoft Edge verifies all images load, the native size viewer opens, 390 pixel mobile layout fits and no script errors occur. The crops are diagnostic copies of existing pixels, not new makeup application results.

## Scope and artifacts

No algorithm, test source, serving contract, model, dependency, database, credential, Git publication or cloud deployment was changed. Hairstyle, Nails and the current online Makeup path remain unchanged. The lip component is still local and not integrated into live generation.

[Original and retained result gallery](../../artifacts/makeup-retained-review-20261103/review-self-contained.html)

[Structured review and measurements](../../artifacts/makeup-retained-review-20261103/review.json)

[Prior implementation and unresolved full feature findings](makeup-source-surface-20261102.md)
