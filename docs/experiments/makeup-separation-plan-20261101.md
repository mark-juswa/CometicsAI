# Makeup separation repair plan, 1 November 2026

Status: CONFIRMED user authorization to plan and implement locally. Production promotion is not authorized by technical checks.

## Fixed requirement

Preserve original person, expression, geometry, texture, lighting and scene. Preserve selected makeup style, hue and visible intensity. Do not substitute a bare photo, generic cosmetics or a regenerated face. Test Natural Makeup, Cloud/Berry Lips and Classic Red Lip on the same two existing development sources.

## Reproduced causes

The saved version 3 failure reproduces exactly. On the first Natural case, 3,786 confident cheek pixels shift in the negative red direction. At source coordinate 162,245, the mapped reference is a pale highlight (RGB241,214,213). Its estimated neutral is darker and warmer. The residual has negative red and yellow components, yet magnitude-only confidence treats it as blush with alpha0.945. Ratios2.57,3.17,3.84 mix reference lightness with chroma. This is not cosmetic pigment. These numbers diagnose this implementation, not every original model defect.

Eye masks also zero all parsed eye pixels. That protects irises but excludes lash and liner boundary pixels. Lash omission needs a bounded rim rather than editing the eye core.

## Smallest repair

1. Preserve prior scripts, plans and failures. Add an isolated separation module.
2. Replace channel ratio transfer with Lab chromatic residuals. Cheek pigment must have positive red excess over its reference complexion, not merely a large color difference. Neutral pale highlights must not become blush.
3. Retain source luminance for blush. Use actual reference pigment hue, not a replacement palette. Smooth inward support and emit component masks for audit.
4. Handle eyelid pigment and dark strokes separately. Use source and reference local contrast to avoid importing whole skin brightness. Permit a narrow source eye rim while copying original eye core exactly. Preserve original mouth and teeth.
5. Keep source brow/lip geometry. Do not interpret numeric strength as visual preservation.
6. Add regression checks for pale highlight rejection, visible blush and lipstick, no cosmetic color swap, protected regions, unchanged inputs, identical reference no-op and malformed or ambiguous inputs.
7. Freeze one six-case evaluation, view full-size comparisons and component masks, preserve hashes and reproduce outputs. No automatic parameter sweep or quality pass.
8. Only a useful human-reviewed result can justify broader skin-tone, pose and service integration checks. Existing ten styles and expanded additions require their own coverage before production.

## Limits and release boundary

Positive red excess is appropriate only for the rose/red blush in these selected references. It does not establish a universal cosmetic segmentation method. The existing flattened PNG has no ground-truth makeup layers. Exact cosmetic RGB, extracted pigments and visual intensity remain unverified until inspected. Original contrast and source texture must be assessed separately from cosmetic visibility.

No new generation, GPU session, training, photo acquisition, dependencies, model download, paid provider, database migration, Git publication or Render/Kaggle change. Existing Hair/Nail release is independent.
