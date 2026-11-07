# Focused white-cast correction proposal — 25 October 2026

**PROPOSED / NOT STARTED.** This is a processing experiment requiring review before implementation, not a deployed fix or a claim that output recoloring can repair all model defects.

## Goal

Use existing originals and saved Makeup outputs to test whether excess foundation lightness/undertone can be reduced while retaining useful lip, eye and cheek cosmetics. No new training photos, foundation download or Kaggle GPU run is necessary to evaluate a CPU post-processing hypothesis.

## Evidence and difference from prior attempts

The current runtime generates a whole portrait; its inspected path has no deliberate skin-whitening filter or source-complexion lock. Lower guidance and prompt wording retain drift on some styles. These findings do not establish an available settings-only fix.

Closed preservation V3/V4 transferred generated cosmetic appearance onto original geometry and failed due to spatial-feature loss and reconstruction contamination. The proposed experiment would keep the generated canvas and apply a bounded photometric adjustment to reviewed neutral-skin regions. It does not transfer whole facial structures, reconstruct makeup on the source, or repeat inpainting. This specific method has not been built or visually tested.

## Small comparison before integration

1. Identify existing saved source/output pairs covering a subtler look and a stronger/new look on the two development subjects. Record exact files and hashes before any manipulation.
2. Inspect corresponding neutral-skin regions, excluding eye/lip cosmetics, hair, teeth and specular highlights. Use reviewed regions for this feasibility stage; do not invent a validated automatic mask.
3. Derive a bounded source-referenced lightness/color adjustment. Preserve the output's spatial detail and colored cosmetic regions; do not globally darken the photograph or manufacture a ground-truth target.
4. Compare original / raw / corrected at native size. Reject gray/orange casts, patch boundaries, flattened texture, diminished makeup or new face-detail artifacts.
5. Only after successful visual review, propose how reliable region detection and serving integration would work. A manual feasibility check is not a deployable automatic feature.

## Limits and release gate

This cannot recover lost source pores, facial geometry or teeth details. No guaranteed improvement or universal complexion threshold is claimed. A reduction in white cast alone is insufficient if other unnatural changes remain. Final acceptance requires useful visible cosmetics plus preservation; otherwise hold the candidate and explicitly review data/model alternatives.

No production change, external image acquisition, training or generation has occurred under this proposal.


## Execution receipt — 25 October 2026

Supervisor authorized proceeding. The six-case offline experiment and one mask-boundary defect correction are complete; original v1 failure is preserved. V2 shows partial whitening reduction but remaining unnatural appearance, with four adjusted and two guarded no-op results. Thirty-two focused checks pass. No product integration or deployment. [Actual results and limitations](makeup-tone-correction-20261025.md).
