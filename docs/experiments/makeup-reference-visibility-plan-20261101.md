# Reference makeup visibility repair, 1 November 2026

Authorization: The user requests visibly recognizable selected makeup, closer color, intensity and placement, while preserving source person, texture, light, hair and scene. This refines the existing requirement. It does not authorize deployment.

## Reproduced attenuation

On the same six saved comparisons, confidently detected reference-blush pixels have median prior alpha0.404to0.561. Approximately44to67percent of these pixels are below0.5alpha. The Gaussian placement prior attenuates even the center of the cosmetic color, rather than feathering just its edge. Eye shadow and narrow lash strokes share a soft mask, weakening opaque cosmetic strokes.

## Targeted implementation

Preserve all prior scripts, frozen plans and outputs. A separate local reference-application variant will:

1. Use a full-strength inner cheek support and a continuous outer transition. Existing signed pigment validation still rejects pale highlights as blush. Derive color from the selected reference.
2. Give eyelid color a full interior with a soft boundary rather than weakening the whole area.
3. Handle actual narrow reference lash/liner strokes separately. A confident stroke can retain opacity without increasing the whole eye shadow. No procedural new lashes.
4. Match dark cosmetic contrast to the source's local skin illumination. Only darkening is allowed; no RGB channel ratios or reference skin whitening.
5. Fill within original brow support using the selected brow color and source fine detail, with both boundaries feathered.
6. Keep existing lipstick handling unchanged, since the user identifies the overall weak application rather than a need to intensify already prominent lipstick.

## Verification and acceptance

Evaluate all three fixed looks on both existing subjects. Compare previous and new application at the same pixels. Measure masked blush-pigment error relative to the selected reference, lash contrast and protected-source edits. These are diagnostic proxies, not human realism or calibrated skin scores.

Regression checks must retain pale-highlight rejection, identical-photo no-op, exact original eye cores/teeth/hair/scene, unchanged input bytes and prior lip output. Verify all six actual outputs reproduce. Inspect full-size images and masks for strong edges, exaggerated dark eyes, misplaced pigment or texture loss.

If observed artifacts appear, keep the failed evidence and repair their demonstrated cause rather than sweeping global strength. No full-look pass without visual review. Three looks/two reused people do not establish all styles or fresh-photo generalization.

No serving, database, cloud, package, training, new model inference, new photo acquisition, paid request or Git publication. Existing Hair/Nail release stays separate.
