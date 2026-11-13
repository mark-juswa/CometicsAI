# 0022. Relevant recommendations and local photo suitability

**Date**: 2026-11-13
**Status**: In Progress
**Decision**: CONFIRMED Supervisor selects local photo checks and retains text only Gemini.

## Summary

Improve recommendations within the existing catalog and reject photos that lack the requested editing subject. Keep the existing trained adapters, camera entry and training explanation. Photos stay on the application server and are not sent to Gemini.

## Requirements

AC-1: Recheck the existing training explanation and camera integration. Do not rebuild these features or describe inference as training.

AC-2: Rank supported styles using normalized user preferences and service specific fields. Respect explicit exclusions and structured intensity/finish preferences. Gemini cannot bypass compatibility by choosing arbitrary valid catalog IDs. Reasons must cite actual preference matches. When there are too few compatible styles, ask for adjustment rather than silently selecting incompatible looks. Preserve expanded styles.

AC-3: Makeup and Hair require one clearly visible, sufficiently large face. Nails reuse the existing local hand and nail validation. A wrong or uncertain photo returns a retake message before any Gemini turn or GPU dispatch. Check direct feature routes, consultation photo upload and generation of older consultations. Do not trust a browser validation flag.

AC-4: Use the installed MediaPipe CPU stack and a separately pinned official BlazeFace asset. Missing assets or detector failure fail closed with a service error, distinct from an incorrect photo. Do not infer identity, ethnicity, attractiveness or skin tone, or claim liveness verification. Check modest pose/lighting variation during real image validation. Preserve original image bytes for generation; detection may use a reduced analysis copy.

AC-5: Retain guest/auth/ownership and API response contracts. Show controlled validation errors in the website. No automatic generation retries and no change to working adapter output logic. Preserve immutable private archives; serving updates require a new reviewed package/image, not a Render only deployment.

## Decision and rationale

Extend the current consultation filtering and validation boundaries. Local MediaPipe detection preserves the current explicit privacy promise and reuses the Nails environment. Gemini image analysis was offered and declined. Browser only validation is insufficient because clients can call the API directly. A face detector is an input suitability check, not proof of identity or a guarantee of cosmetic quality. Hair visibility remains a separate limitation; a face detector alone cannot establish suitable hair framing.

## Build plan

1. Record existing feature verification (AC-1).
2. Add normalized service specific compatibility/ranking and adversarial recommendation tests (AC-2).
3. Add local detector, pinned asset preparation, shared server enforcement and rejection tests (AC-3, AC-4).
4. Map only known public photo errors, update deployment preparation and run offline/real image checks (AC-5).
5. Package and validate the updated CPU serving source separately before authorized production rollout. GPU style generation quality is unchanged but live wrong subject rejection needs explicit verification.

## References

[Official MediaPipe Face Detector](https://developers.google.com/edge/mediapipe/solutions/vision/face_detector) supplies face bounding boxes and keypoints. Existing sources: backend/app/consultation/{gemini,recommend,api}.py, backend/app/main.py, backend/app/nails/geometry.py and docs/specs/0021-ai-methodology-camera.md.
