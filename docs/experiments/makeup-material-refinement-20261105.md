# Makeup source material refinement

5 November 2026. **Bounded implementation DONE. Source protection VERIFIED on 52 cases. Appearance EXPERIMENTAL. Complete Makeup realism IN PROGRESS. Production integration NOT STARTED.**

The Supervisor authorized proceeding with the remaining lip, lash, metallic and finish defects. No artist, new photo, package installation, diffusion run or Kaggle GPU was required. This is an extension of the existing automatic application, not a replacement face generator. The results improve specific defects, but do not establish the complete catalog as ready for training or production.

[All 52 four panel comparisons](../../artifacts/makeup-refinement-20261105/catalog-review/review-self-contained.html) show **Original | selected makeup guide | actual November 4 automatic result | material correction**. Every previous panel exists. The guides are prior AI outputs, not independent ground truth. [Machine receipt](makeup-material-refinement-20261105.json), [independent source checks](../../artifacts/makeup-refinement-20261105/catalog-review/independent-source-checks.json), and [visual review](../../artifacts/makeup-refinement-20261105/visual-review.json) retain the limits.

## 1. Current architecture

Serving still uses `backend/app/makeup_styles.py`, `makeup_contract.py`, `generation/remote_makeup.py`, `scripts/makeup_inference_server.py` and `scripts/inference_performance.py`. It sends the original portrait and selected style to whole frame FLUX with the already trained MAKEUP-001 adapter. It has no original pixel protection stage. Those files and the UI contracts were not changed.

The ten active style instructions come from `data/makeup/DATA-M001-paired/inference_presets.json`. Three held styles come from `backend/app/style_release.json`. The offline evaluator freezes source photos, guide images, parser outputs and source anatomy. `makeup_local_features.py` supplies the previously saved self versus local reference transfer fields. `makeup_source_layers.py` applies their cosmetic absorption to original pixels. Optional `makeup_materials.py` now handles source lip confidence, pigment hue, observed lash/reflection detail and source shine. Default calls still reproduce the November 4 route and preferred historical lip component.

Target selection/finalization remains in `data_m001_paired.py`, packaging in `data_m001_package_training.py`, mandatory individual admission in `makeup_target_quality.py`, and training in `notebooks/train_m001_kaggle.py`. None was bypassed or used to accept these outputs.

## 2. Root cause assessment

**Previously demonstrated:** historical FFHQ targets contain whitening, smoothing and reconstructed features; all 60 were rejected for unchanged corrective reuse. Serving returns the generated face. Base also over edits, so the training dataset is not proved the sole cause of model behavior. Direct face color subtraction confused cosmetics with foundation/illumination. The November 4 source substrate approach reduced whitening without face reconstruction. See [architecture audit](makeup-architecture-review-20261104.md) and [automatic correction](makeup-automatic-correction-20261104.md).

**Demonstrated this cycle:**

* A constant source to target chroma offset retains original lip hue variations. Cool blue/purple ridges were visible in saved lip crops. A constant pigment chroma removes much of this error without copying reference mouth shading.
* The old one pixel empty boundary followed by a three pixel ramp consumes a disproportionate amount of a narrow upper lip. Cached source parser probabilities reproduce all four previous hard label maps exactly. Their photographic confidence supports soft coverage inside the same parser/contour intersection. There is still no hand labeled boundary truth.
* Directly matching the very dark guide lip produced an inky result. That prototype was rejected. Final code uses a bounded local shadow preserving lightness offset and original highlights instead. The preferred historical function is untouched.
* The expanded Manga guide itself contains rigid lash spikes. Copying those shapes more accurately reproduces a source defect. A previously supplied user photo contains finer observed lash and reflective detail. Only foreground alpha texture is extracted from it, never its face color or geometry.
* Reflection fitted across the full lid to brow gap created a patch near the brow bone. Restriction to the mobile eyelid and soft lateral/vertical taper reduce that placement defect. Early diagnostics are preserved.
* Smoky/Bold neural eye density is already stronger than Natural across all four sources, including after masking. Further global opacity amplification is not justified. Missing fine detail and style fidelity are separate problems.

The last three findings explain specific rendering failures. They do not prove that the new lash/metal materials are universally natural.

## 3. Complete catalog and visual coverage

One shared style guide and one shared detail donor serve all four existing development people: **054109, 056266, 006553, 035149**. There are 52 final cases, with all thirteen distinct output hashes per person. These are reused development inputs, not untouched generalization or representative coverage of every complexion/pose.

| Style | Status | Observed result / remaining gap |
|---|---|---|
| Natural Makeup | Active | Lip hue/coverage improves; muted versus stronger rose appearance still varies by original |
| No-Makeup Makeup | Active | Sheer lip and minimal definition retained; complexion evening intentionally limited to avoid smoothing |
| Soft Glam | Active | Satin lip and fine definition visible; separation from Natural remains modest on some originals |
| Smoky Glam | Active | Stronger shadow and added lash detail; fine lash fringe can look comb-like |
| Dewy Peach | Active | Warm tint and bounded existing shine enhancement; full face dewy distinction remains modest |
| Rosy Pink | Active | Rose eye/cheek/lip family remains visibly different from warm styles |
| Bronze / Golden Glam | Active | Small gold reflection is now visible; finish varies with original lid/lighting |
| Matte Nude | Active | Nude lip and existing shine attenuation; matte distinction remains modest |
| Classic Red Lip | Active | Rich red and fuller source fitted edges; conspicuous strong color borders still need human review |
| Bold Evening Glam | Active | Berry lip hue more consistent, visible shadow/lashes; some fringe still artificial |
| Cloud-Skin Makeup with Blurred Berry Lips | Held | Berry lip with softer edges and source shine reduction; no pore blur or reconstructed cloud base |
| Manga-Lash Makeup | Held | Observed fine lashes and selected guide cluster spacing; convincing separated convergent clusters remain unresolved |
| Icy Silver Eye Makeup | Held | Local silver-blue reflection visibly improves the former matte blue look; sparkle/stripe appearance is identity dependent |

All four full catalog sheets, all four native eye before/after boards and all four native lip before/after boards were inspected. Nine representative native full comparisons were reviewed first. The full gallery is available for Project Lead review. Codex observations are not human acceptance. No style has been silently removed, enabled or relabeled.

## 4. Smallest correction and reused components

The original photograph remains the canvas. Source labels plus MediaPipe contours keep the previous validated lip support. A guided filter refines the source probability field, not the photo. It replaces the fixed boundary hole with confidence weighted feathering. Lip pigment uses the selected guide's median color, source lightness/shadows and existing highlights. It imports no spatial guide mouth texture.

Reference dark foreground attached to observed lash roots supplies detail. Original eye openings determine fitting; the source RGB is never warped. Manga uses the selected guide's cluster spacing to select existing finer donor strands, rather than drawing new hairs. Reflection uses observed donor surface detail, the selected silver/gold family and source mobile lid placement. This remains an estimated material, not an artist approved cosmetic layer.

Dewy/Matte/Cloud change only evidenced existing source shine. Their local lightness change is bounded to three Lab units, with soft coverage in the upper tenth of the eligible shine evidence. They never blur source pores, fill facial features, globally match skin color or paint a new foundation. Lack of strong source shine limits how visibly these finishes can differ.

The eroded original eye opening core, brows, nose, mouth opening/teeth, hair, clothing and background remain exact in all checked outputs. Mascara may occlude the one pixel eyelid rim, including **3 to 80 parser eye pixels at most per identity**; this is explicitly measured, not a claim that every semantic eye pixel stays exact.

## 5. Implementation

* `scripts/makeup_materials.py`: reusable source confidence matte, lip pigment/finish, observed detail extraction/fitting and source shine; one material configuration for all thirteen styles.
* `scripts/makeup_source_layers.py`: optional `materials` argument on the existing automatic function. Original default behavior remains available.
* `scripts/evaluate_makeup_automatic.py`: `refine` phase binds input hashes, reuses saved neural fields, refuses overwriting earlier output directories, writes actual baseline comparisons/masks/provenance and the existing self contained gallery.
* `backend/tests/test_makeup_materials.py`: meaningful source protection, hue, boundary confidence, no change, input mutation, finish bound and exact saved result regressions.

Preparation/diagnostic/inspection scripts and failed prototypes remain under `artifacts/makeup-refinement-20261105/`. No serving import or backend/UI redesign was introduced.

## 6. Verification and before/after evidence

**119 distinct checks pass:** 70 existing focused tests, 22 new material tests and 27 unchanged mocked runtime/API/package tests. Three representative final outputs reproduce exactly from the current helper; all 52 final PNG/RGB hashes and source scope are independently checked. All 52 eye core, brow, nose, teeth/scene and outside scope checks pass. Skin median deltaL is zero in every case; this is preservation evidence, not an appearance score. Local cosmetic reflections may legitimately brighten eyelids.

Measured median interior lip hue errors against the selected palette:

| Case | November 4 | Material correction |
|---|---:|---:|
| 035149 / Bold Evening | 5.575 degrees | 0.412 degrees |
| 006553 / Classic Red | 1.829 degrees | 0.712 degrees |
| 054109 / Natural | 2.705 degrees | 0.395 degrees |

These measurements do not measure blending quality, and sheer styles deliberately retain some original hue. Native crops show the actual edge and finish tradeoffs.

Headless Edge verifies all **208 embedded images / 52 cases**, identity/style filters, native viewer, desktop 1440 and mobile 390 layouts without overflow or page errors. The gallery is local and self contained. No communication/publication occurred.

The initial freeze covers 94 files. **92 are unchanged**; the two intended existing changes are the evaluator and source application. All 52 November 4 output PNGs, frozen inputs/numerical helpers and eight captured serving/release controls remain unchanged. Original datasets, rejected evidence, pretrained weights and own adapter artifacts remain intact.

There were five cached CPU parser calls (four source confidence maps plus the existing detail donor), one CPU donor face detection and two SPIGA passes. Final representative and catalog application reuse the 52 saved neural fields, with zero additional EleGANt/diffusion/GPU/training calls. No new dependency or model download.

## 7. Training compatibility and next milestone

**Zero new pairs are accepted. DATA-M001 corrective finalization remains BLOCKED by target acceptance; corrective adapter training NOT STARTED.** The existing MAKEUP-001 is already trained and remains the serving baseline. Do not overwrite or describe this CPU material stage as that trained model.

Catalog wide fidelity is not established: Manga cluster shape, natural fine lash attachment on all originals, consistent metallic texture and stronger finish separation remain incomplete. Fresh identities, non smiling/closed eyes, glasses/occlusion, runtime fitting/latency and target distribution are unverified. Lip boundaries still use model estimates.

The user supplied detail donor has **UNKNOWN author/license**, retained in its provenance. Visual use does not establish permission to derive training data or production assets. The existing third party feature provider also retains its recorded license limits. Individual target provenance, truthful cosmetic annotations and separate quality review remain mandatory.

Before any new corrective adapter run: resolve these material quality gaps on the same fixed comparisons, admit usable source bound targets individually, retain identity separated train/validation, then run the existing compatible FLUX/LoRA trainer under a distinct preserved run ID. Compare Base versus the resulting adapter on held out originals. Production integration follows separate real generation validation and Supervisor approval. Passing technical tests or this local preview does not meet those gates. Hair, Nails and application contracts are unaffected.
