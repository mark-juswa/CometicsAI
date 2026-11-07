# Reference-guided Soft Glam prototype — 27 October 2026

**Offline prototype DONE; visual screen FAILED; integration NOT STARTED.**

The Supervisor supplies a portrait as the approximate target. This establishes appearance direction: warm rose-bronze eyelids, dark defined lashes, fuller defined brows, visible rosy blush, localized cheek glow, glossy rose-brown lips. It does not approve earlier images or authorize copying the reference person's complexion, identity, studio light or face geometry.

## Actual implementation

One new isolated script and frozen MAKEUP-COMPLETE-001 plan render four existing development photos, reusing cached source parsing maps and unchanged baseline/visibility helpers. Adds layered warm eyelids, procedural lash accents, definition within existing brows, outward blush, local cheek/eyelid light and source-highlight-driven lip gloss. No whole-face foundation/smoothing or full-frame face reconstruction.

Unlike earlier pilots, eyebrow labels6/7 are deliberately editable. Protected regions are all labels except skin1, brows6/7 and lips11/12. Eye interiors, nose, mouth interior, hair, neck, clothing/background remain exact source. Do not compare the prior all-protected definition without explaining this scope change.

Source/helper/map/previous hashes are frozen. Four outputs reproduce exactly with zero changes outside explicit cosmetic support/protected regions. Sixteen new safety tests plus70prior regression tests are run; results recorded separately. Technical tests do not certify appearance.

## Visual result

All four original/previous/new comparison sheets inspected. Warm palette moves toward the reference, but procedural lash strokes look drawn on, regularly spaced and sometimes above the natural lash line. Brow change is modest; lips may look flat/painted. Cheek/skin finish is still short of the reference. **Codex rejects this prototype for release.** It is not presented as a completed fix; no further opacity sweep was performed.

Evidence: artifacts/makeup-render-20261027/complete-01, including plan, report, four comparison sheets, region overlays, independent verification and visual-review.json. Previous failed pilots remain intact. The reference itself is not bundled, trained on, or treated as a paired target.

## Next narrow gate

First verify automatic eyelid/lash-line, brow and lip alignment on the existing source photos, with landmark/semantic overlays and explicit rejection of unsupported inputs. A pretrained face landmarker is a candidate addition, not an implemented capability. [Official Python documentation](https://developers.google.com/edge/mediapipe/solutions/vision/face_landmarker/python) confirms facial coordinates can support effects placement; it does not establish realistic cosmetics.

Only after actual alignment review should one revised complete look be evaluated. Better alignment alone may not solve cosmetic material/lash realism; do not promise a reference-grade result. No mass expansion, training run, dependency/model download or Render/Kaggle change.

## Verification receipt

86 focused tests pass (16 new +70 prior), 83.42 seconds. Four saved outputs independently reproduce. Installed MediaPipe0.10.33 is available, but no Face Landmarker asset is present; official docs checked only. No new model downloaded or landmark inference run. This is preflight, not a placement or realism result.
