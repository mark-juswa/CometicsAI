# 0021. AI methodology and camera photo entry

**Date**: 2026-11-09
**Decision**: CONFIRMED requested by Supervisor. Native browser capture and existing page conventions are local implementation choices.
**Progress**: DONE local implementation, verification, publication and Render production integration on 10 November 2026. Real device acceptance remains NEEDS VERIFICATION. [Release receipt](../experiments/camera-deployment-20261110.md).

## Requirements

1. Add a public How our AI works page, linked from About and every AI studio, explaining training separately from client generation. Ground claims in inspected training reports and serving code. Distinguish pretrained FLUX, project trained LoRA, text consultation and the hybrid Nails paths. Do not claim training from scratch, automatic training on client uploads, perfect identity preservation or one trained model per style.
2. Add an explicit Use camera option to Hair, Makeup, Nails and consultation, including guest consultation. Keep file upload and existing image selection. Profile and product inventory uploads are outside this AI scope.
3. Use one reusable capture component. Request video only after a click, never audio. Offer live preview, camera switching, capture, review, retake and Use photo. Convert the selected frame to a bounded JPEG File and reuse existing validation. No upload or generation happens just from opening or taking a picture.
4. Stop media tracks on capture, dismissal, route departure, disabled state or late permission response. Handle denied permission, missing hardware, unsupported browser and capture failure. Offer the device camera picker as a fallback on supporting phones; ordinary upload stays available.
5. Keep generation recovery, guest allowances, model settings, catalog, API and database unchanged. Test success, cancellation, permission failure, late streams, cleanup, resizing, and source integration. Real hardware/browser permission acceptance is separate from synthetic verification.

## Implementation

Use built in getUserMedia, video and canvas with no new dependency. The published HTTPS site meets the secure context requirement. Use ideal facing mode, front for portraits and rear for hands. Limit the longest captured edge to1600 pixels and enforce the existing8MB JPG/PNG input limit. A native capture input remains a best effort fallback, not a promise that every desktop file picker opens a camera.

The methodology reuses the existing public layout and design tokens. Its training summary is based on the accepted corrective Makeup report, released style manifests, and the inspected project defense guide. Expanded options are prompt profiles or rendering configurations where applicable, not additional independently trained models.

## References

[MediaDevices.getUserMedia](https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia) documents user permission, secure context and releasing camera resources. [Corrective training evidence](../experiments/makeup-corrective-model-results-20261106.md) records the actual Makeup run and validation limits.

## Verification

163 focused checks, TypeScript and the default production build pass. Built methodology page and the actual camera component with a synthetic MediaStream were visually checked. Real camera hardware, native phone picker and mobile browser layout remain NEEDS VERIFICATION. [Evidence and boundaries](../experiments/ai-methodology-camera-20261109.md).
