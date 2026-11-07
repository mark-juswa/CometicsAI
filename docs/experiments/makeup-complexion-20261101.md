# Source-referenced Makeup complexion correction — 1 November 2026

**Offline implementation DONE; technical evidence VERIFIED; appearance EXPERIMENTAL. Human review and serving integration remain pending.**

## Requirement and why earlier work failed

The requirement is to retain visible makeup while blending it with the original person's complexion. Existing raw Makeup PNGs are already pale before website display. The current pipeline generates a full face and does not enforce source complexion. Retouched training targets are a plausible contributor, but existing base-only results also over-edit; the adapter is not established as the sole cause.

Earlier guidance/adapter/prompt comparisons were diagnostics, not a verified correction. The rejected Lab prototype estimated one forehead offset and changed selected skin while leaving broad feature-adjacent areas protected. It had manual sample boxes and visible pale transitions. Its successful pixel checks did not make it visually acceptable.

## What was developed now

A boundary-only Poisson blend was first evaluated on the same six saved images. It warmed some areas but did not sufficiently correct internal facial color. Its first attempted run also stopped on cropped-forehead border handling; that failure was preserved before supplying explicit solver padding. It was not promoted.

The new complexion prototype aligns a color-only copy of the original using parsed eye/mouth locations. The displayed generated geometry is never warped. It measures neutral original/generated skin at automatically selected forehead, temple and jaw regions, plus neck skin where available. It solves a smooth spatial Lab color-correction field instead of applying one global offset. This field can adapt brightness and color across the face without changing the model or regenerating cosmetics.

An initial field version still hard-protected the complete lips and stopped at semantic skin edges. It produced conspicuous lip/jaw/hairline cutouts and was rejected locally. The revised version covers contiguous facial cosmetics and head/neck transitions, uses source-measured neck anchors, reduces shifts in very dark colors and narrowly protects inner eyes/neutral teeth.

**Protection changed deliberately:** lip, brow, ear/neck, narrow hairline and nearby background colors may change. Only pixels outside the actual edit influence are guaranteed raw-identical. This is not the earlier claim of exact protection for all semantic non-skin pixels. The field does not repair pre-existing face reshaping, smoothing or missing skin texture.

## Evidence

The fixed revised algorithm was checked against ten saved outputs from two reused development people:

- Four Natural/Classic Red Lip outputs at the existing guidance4.0 contract.
- Six Natural/Classic Red Lip/Berry outputs at earlier experimental guidance2.5.

No new photos, diffusion/GPU calls, training, paid requests, packages or online model downloads were needed. Six existing parser maps were reused; four current-setting raw outputs were parsed locally with the previously cached, hash-verified face parser. These are repeated development inputs, not untouched evaluation across skin tones.

All ten native comparison sheets were inspected. White cast is visibly reduced and makeup remains visible; the revised transition removes the gross pasted lip/face edges in its first version. Possible excessive warmth/orange shading, lip/brow color changes and residual hairline/jaw/neck transitions still need human assessment. The original model's strong smoothing/geometry changes remain. No claim of a universal or accepted complexion fix is made.

Twenty-three targeted checks pass. They verify reduction of a known synthetic cast with visible cosmetic contrast, no-op on a matching reference, input preservation, narrow eye/white-teeth protection, rejection of invalid/missing evidence and exact RGB reproduction of all ten saved corrected outputs. Thirty embedded gallery images load, enlarge and fit a390pxviewport in Edge without script errors. Numeric fitting and technical tests do not replace appearance acceptance.

Local saved-label correction is approximately0.2seconds per image. Four new raw parser passes took about2.0–2.2seconds each; original-source maps were reused. This is not a full two-parser Kaggle latency/memory measurement or a promised deployment overhead.

## Review and next gate

Open [the self-contained source/raw/corrected gallery](../../artifacts/makeup-complexion-20261101/review/review-self-contained.html). The first four comparisons use the deployed inference setting; the remaining six use earlier experimental2.5.

First review whether complexion blending is useful, makeup remains visible and transitions look natural. If accepted as a useful direction, validate additional permitted inputs, face/pose/parser failures, excessive-correction cases and the actual Kaggle CPU memory/time before integrating a versioned post-processing stage. The source/segmentation models, dependencies, result provenance and raw fallback must be explicit. No existing MAKEUP-001 checkpoint or guidance contract is silently rewritten.

Hair/Nails release63fc851, its manifest, CPU archive and notebook are unchanged. No serving/frontend/database/dependency/secret/deployment changes or Git publication occurred in this task.

## Technical references

[OpenCV seamless cloning](https://docs.opencv.org/4.10.0/df/da0/group__photo__clone.html) and [Poisson Image Editing](https://www.cs.jhu.edu/~misha/Fall07/Papers/Perez03.pdf) support the boundary-blending feasibility investigation. The final spatial field is a project-specific adaptation, not an implementation of a proven published Makeup-quality result. [SciPy sparse solver](https://docs.scipy.org/doc/scipy/reference/generated/scipy.sparse.linalg.spsolve.html) documents the linear solver used. These references do not prove this prototype's appearance or generalization.
