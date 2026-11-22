# Consultation relevance and local photo checks

Date: 13 November 2026. Progress: IN PROGRESS, local implementation and bounded validation complete, production rollout NOT STARTED.

## Existing features and diagnosed gaps

VERIFIED: The existing public training explanation describes paired source/target/instruction data, pretrained FLUX.2 Klein Base 4B, project LoRA adapters and the corrective Makeup run. It truthfully reports 52 training pairs across 12 identities, 26 validation pairs across two identities and 250 updates. Those validation identities were reused during development and are not an untouched final test. No uploaded customer photo retrains the model. A public HTTP check of `/how-ai-works` returned 200 and the expected training/privacy text. CameraCapture already serves Hair, Makeup, Nails and normal/guest Consultation. Ten camera/methodology tests pass. Physical camera acceptance on each client device remains separate.

VERIFIED: Gemini's consultation request is text only. It receives preferences, messages and catalog information. It does not inspect photos. The old recommendation boundary checked supported IDs and exclusions but did not require a stronger preference match. Its fallback selected three sorted IDs and could attach unrelated complementary services. Existing general upload checks covered file readability, size and dimensions, but did not establish a face for Makeup/Hair. Nails already had a local hand and nail preparation pipeline before GPU dispatch.

## Confirmed correction

Supervisor selected local photo checks, keeping photos out of Gemini. This is input suitability and recommendation logic, not retraining or a new beauty model.

`backend/app/photo_suitability.py` uses the installed MediaPipe stack. Hair and Makeup require exactly one detected face with minimum size and limited clipping. Nails reuses the existing hand localizer. Checks run before attaching a consultation photo, before consultant/recommendation calls, before consultation generation and inside direct feature generation handlers. Missing or broken detector assets return a controlled 503. Incorrect subjects return service specific 422 retake guidance. The original generation image is preserved; only an analysis copy is resized. The website maps exact public messages without relaying arbitrary upstream details.

`backend/app/consultation/recommend.py` normalizes synonyms such as office/everyday and dramatic/bold. It ranks against stated occasion, likes and service specific preferences, respects explicit Makeup intensity/finish and exclusions, and replaces weaker valid Gemini choices with stronger catalog matches. Reasons are derived from actual tags. Unmatched complementary suggestions are omitted. Fewer than three compatible choices asks the user to adjust preferences rather than silently breaking constraints. Gemini's prompt requests useful missing preferences and remains text only.

The face model is the official MediaPipe BlazeFace short range float16 asset, 229746 bytes, SHA256 `b4578f35940bf5a1a655214a1cce5cab13eba73c1297cd78e1a04c2380b0152f`. The preparation script downloads this fixed URL and verifies its hash. Reference: [Google Face Detector](https://developers.google.com/edge/mediapipe/solutions/vision/face_detector).

## Packaging and preservation

The original private CPU/GPU archives, model weights and earlier outputs remain unchanged. `scripts/package_runpod.py` inventories five updated CPU application files and the pinned face asset. `deploy/runpod/runtime.py` verifies the historical source pair first, then installs only hash checked CPU updates into a new disposable staging directory. GPU/model payloads are untouched. A real Linux staging attempt exposed a build manifest variable being shadowed by a bundle manifest; this was corrected and covered by regression tests. Earlier failed staging evidence remains intact.

Final local candidate: `beautycore-runpod:photo-guard-a40-20261113-03`, built from `artifacts/photo-suitability-20261113/package-03/build-context`. This is a local tag, not a public image reference. No image publication, paid GPU run, Pod modification, Kaggle change or Render deployment was performed. The previously published serving image does not contain these checks. Client commits through `a005550` were fast forwarded without conflict, preserving updated hairstyle prices. No adapter, catalog style or camera flow was removed.

## Verification

Evidence is retained under `artifacts/photo-suitability-20261113/` (ignored local artifacts, not a public dataset).

* 113 focused backend tests pass, covering API boundaries, old consultation rechecks, detector failure, preference constraints, valid but irrelevant provider proposals and immutable package staging. See `backend-tests-final.log`.
* 57 focused website tests pass, including controlled error relay, guest trials and the ten camera/methodology checks. TypeScript passes. Production Next build passes. An initial build failed fetching existing Google Fonts; the network enabled retry succeeded without font or application changes.
* 33 tests covering the client's merged business/price changes pass.
* Eleven real native detector cases pass without GPU or network: four existing portraits accepted for Makeup and rejected for Nails, blank/nail crop/multiple faces rejected for Makeup. Available portraits cover differing complexions and styling; this is bounded evidence, not a representative detector benchmark.
* Final Docker candidate distribution and staging pass with network/GPU disabled. The staged CPU API rejects blank wrong subject images for all three services, rejects attachment of an incorrect consultation photo, accepts an existing real portrait, and returns Matte Nude/Natural Makeup/No-Makeup Makeup for office plus natural preferences. Native detectors are real; generation engines in this check are mocks. No new real generation acceptance is claimed.

## Limits and next milestone

NEEDS VERIFICATION: a full hand positive case in the new gate, real client camera/browser behavior, broader lighting/pose/accessibility and false rejection coverage, real Gemini dialogue quality and production website requests after rollout. The hand gate establishes a usable hand; existing nail segmentation still decides whether nail regions can be edited. Face detection does not prove hair visibility, liveness, identity or cosmetic suitability. It cannot make recommendations based on face shape, complexion or undertone, and no such claim is made.

Next prepare an authorized release of the final CPU serving image and website, validate on the actual A40 Pod with the website URL unset, exercise correct and incorrect photos, then register to Render and verify ordinary client requests. This requires an explicit production rollout; deploying only the website cannot add the server checks. Kaggle backup remains on its previous serving source until separately prepared. Dataset/paper delivery and model retraining are outside this change.
