# Makeup source layers and corrective target admission

Date: 4 November 2026
Artist dependency: **DEPRECATED as a required path** after the Supervisor states no artist is available and reaffirms the original engineering task. The source application and data quality gates remain useful. See [automatic correction](0017-makeup-automatic-local-features.md).
Decision: **CONFIRMED** for isolated implementation by the Supervisor's task and explicit choice of artist/salon authored layers.
Progress: **DONE** for the bounded implementation below. Full Makeup correction remains **IN PROGRESS**; full look assets and visual acceptance are still required.
Evidence: **EXPERIMENTAL** for appearance. No production integration authorization is inferred.

## Decision and rationale

Keep the original portrait as the canvas. Consume explicit cosmetic coverage and material descriptions fitted to that source, rather than attempting to recover makeup from a flattened generated face. Retain the positively reviewed lip component unchanged. Reuse its constant Lab offset, source shadow guard and gamut compression for the bounded material operator. This preserves source variation inside uniform coverage, without copying generated shading or smoothing the source.

The existing full face FLUX output reconstructs the person. Prior chroma extraction, procedural lashes and full pigment probes failed visual review. Another opacity or prompt sweep has no supporting evidence. Artist authored layers were selected by the Supervisor on 4 November. Their availability is an asset requirement, not permission to fabricate salon approval. Real paired photographs remain a possible later data source, not a parallel implementation in this slice.

This operator handles pigment. It cannot yet create new realistic lashes, sparkle, gloss or a physically calibrated finish. Those must be declared as missing, not silently represented by simple tinting. Preserve all ten serving and three held styles and their original descriptions.

## Value sourcing and boundaries

| Value | Source |
|---|---|
| Person, complexion, texture, geometry, lighting and scene | Original RGB portrait, never a generated face |
| Layer placement | Explicit source fitted alpha map, bound to source pixel hash and parser hash |
| Cosmetic material | Explicit reviewed Lab palette and source anchor; no spatial reference illumination |
| Permitted region | Source parser plus primary face check; authored coverage must lie within it, otherwise refuse |
| Style and intended cosmetics | Actual inference presets and held Makeup entries in style_release.json |
| Layer acceptance | Named artist/salon reviewer, evidence and explicit approval; development proof stays unapproved |
| Training target eligibility | New per pair quality review bound to image hashes, caption, identity and split |
| Rejected historical targets | Hash pinned policy derived from the unchanged 60 pair corrective ledger |

No new service, GPU model, dependency, UI, database or production contract. Source fitted maps are not an automatic fitting solution for arbitrary uploads. Existing lip maps are parser/landmark development estimates, not artist assets.

## Requirements

1. Apply bounded source material layers through one reusable operator, without warping or smoothing the original. Protect eyes, brows, teeth, nose, hair and scene. Cheek pigment cannot change source lightness. Reject uncertain, overlapping or out of region layers rather than silently repairing them.
2. Reproduce the retained six lip outputs exactly through the shared operator. Show Original, existing generated guide, rejected previous transfer and retained component. Explicitly label the last column as lip only. No invented full look output.
3. Inventory all 13 styles from the real catalogs, with full look acceptance remaining unverified until actual layer assets and representative visual review exist.
4. Refuse corrective finalization, packaging and training preparation when the new quality review is absent, incomplete, bound to different inputs, or contains rejected targets. Preserve original source metadata and unlabeled archive variants. Human attestations are review records, not automatic appearance scores.
5. Package the quality validator and pinned policy with the standalone runner. Revalidate before training and bind its evidence to preparation. No GPU time for incomplete data.
6. Preserve all historical outputs, frozen implementations, checkpoint bytes and Hair/Nails/serving assets. Save checks, comparisons and limitations before updating context.

## Build plan

- [x] Implement source layer input and pigment application, with existing numerical helpers (1).
- [x] Add mandatory target quality admission to the paired finalizer, packaging and runner (4, 5).
- [x] Produce reproducible six case component comparison and all catalog coverage report (2, 3).
- [x] Run meaningful regression checks, preserve receipts and document open full look requirements (1 to 6).

Implementation receipt: [4 November review](../experiments/makeup-architecture-review-20261104.md). No full look or production acceptance follows from these completed implementation tasks.

## Milestone gates

Implementation of the operator is separate from acquiring artist assets. Full look appearance must pass representative complexion, subtle/medium/strong eye/lip and warm/cool reviews before creating corrective targets. All target annotations, rights and identity split require independent review. Repeatedly used development people cannot become untouched final acceptance subjects. Data finalization, new adapter training, Base comparison and production integration remain separate gates. Existing MAKEUP-001 is already trained; corrective training must use a new run/output and must not overwrite it.
