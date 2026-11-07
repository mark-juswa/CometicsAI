# Automatic Makeup correction without an artist

4 November 2026. **Bounded implementation DONE; source preservation VERIFIED on52cases; appearance EXPERIMENTAL; full catalog fidelity IN PROGRESS; production integration NOT STARTED.**

The Supervisor has no makeup artist and reaffirms the original engineering task. The earlier artist requirement was an assistant introduced blocker. It is removed from the critical path. There is now an automatic local implementation and concrete complete face comparisons, beyond the prior lip only regression work. This does not declare every style ready or ask the user to obtain an artist.

## Actual correction

The original RGB photograph is the output canvas. The existing saved AI face is a style guide only. The new offline provider uses the [author's EleGANt local feature architecture](https://github.com/Chenyu-Yang-2000/EleGANt/tree/d033d3398751684eb8c4b5aef54c74b84f3a3ef8) on CPU. It encodes source content once, decodes both self reference and locally mixed reference features, and compares those results. The final output never becomes either reconstructed face. Source eye interiors, brows, nose, teeth, hair and scene remain exact in checked support.

The material stage compares linear light density, excludes negative whitening density, and fits nonnegative pigment in the selected style's cosmetic color family. Original source reflectance supplies skin tone, detail and shading beneath that pigment. Neutral dark absorption supplies eye definition. The previously preferred lip function remains unchanged, with declared per style intensity for sheer/soft looks. Automatic source landmarks provide placement, and a source eyelid taper fades the field before the brow. The same implementation and catalog configuration serve every identity and style.

The [author inference implementation](https://github.com/Chenyu-Yang-2000/EleGANt/blob/d033d3398751684eb8c4b5aef54c74b84f3a3ef8/training/inference.py) supports local feature mixing; that is an upstream mechanism, not a quality claim for our outputs. Source revision and all36downloadedsourcefilehashes are retained. The author linked41,123,601byte checkpoint loads strictly, with observedSHA71473aa3abad4f66536cef89ab179851547811f1153e846333fa167655776737. Only existing Python packages, cached parser, MediaPipe and true SPIGA68 inputs are used. No dlib install or invented478to68 mapping. Segformer19/SPIGA68 adaptation differs from author BiSeNet/dlib preprocessing, so equivalence/generalization is not claimed. Author source records CC BY-NC-SA4.0; training target reuse or production rights are not inferred from loading it.

This does not replace the intended FLUX/LoRA foundation. The existing trained MAKEUP-001 is the historical serving baseline. The new pretrained provider is an isolated offline correction/target preparation candidate. No pretrained third party checkpoint is described as our trained MAKEUP model.

## Demonstrated causes and corrections

Earlier inspection established that current serving returns a whole generated face and the selected historical FFHQ targets have unwanted retouching. Previous direct RGB/Lab extraction failed to distinguish pigment from foundation/illumination. Base also over edits, so the dataset is not proved the sole cause. [Earlier architecture audit](makeup-architecture-review-20261104.md) retains the serving map, catalog and source rejection evidence.

This cycle reproduced further concrete failures:

| Finding | Bounded correction and evidence |
|---|---|
| Raw local feature output still lightens/smooths the person | Use it only as an intermediate field against the same source self reconstruction; apply the difference to original pixels |
| Keeping Lab lightness still removed warm skin chroma and made cheeks look pale | Replace additive chroma with a source substrate absorption model |
| Unconstrained density can still remove red more than blue, producing gray/cyan cheeks without increasing RGB | Fit density only to the selected catalog pigment direction, rejecting incompatible complexion removal |
| Uniform lip strength overstated sheer/soft looks | Declare style specific lip intensity while keeping preferred Natural/Red/Berry components at exact original strength |
| Broad orbital support made the silver eye look like a hard plate | Fade the effect inside each source crease/brow gap; retain original eye interiors |
| A proposed scalar diffuse/specular lip material still looked pasted in three local proofs | Reject it and retain the existing lip component; do not promote mathematical plausibility as appearance acceptance |

Initial failures, source snapshots, raw/self model fields, intermediate material results and the rejected lip proof remain intact. The final material and support revisions reuse the same52savedneuralfields. No parameter search or new diffusion follows those failures.

## Scope and actual artifacts

Four existing portraits are054109,056266,006553and035149. Their originals visibly differ in complexion and lighting; they are reused development inputs, not calibrated skin categories or untouched final acceptance people. Some originals already contain makeup. Source photo credits and dataset terms are retained per image.

Every source uses the same guide for a selected style, rather than identity specific tuning. Thirteen guides come from the actual ten preset and three held expansion results. They are imperfect prior AI outputs, not independent cosmetic truth or accepted targets. All52combinations are complete. For26cases on the original two comparison people, a matched generated or rejected transfer baseline is available. The other26panels explicitly say no matched previous result exists. No baseline image is invented or substituted.

Canonical review: `artifacts/makeup-local-transfer-20261104/catalog-review/`. It contains a self contained182imagegallery, source/guide/previous/corrected comparisons, four full catalog sheets and native eye/lip sheets, frozen plan, copied implementation, output hashes, source checks and browser receipt. Earlier results stay in catalog-01, catalog-final and catalog-reviewed; only catalog-review is the current candidate. The prototype files elsewhere are diagnostic history.

## Complete catalog observations

| Style | What the current candidate shows | Remaining limit |
|---|---|---|
| Natural Makeup | Restrained eye definition and rose lip with original skin | Lip can still read stronger than everyday natural on a darker original lip; review required |
| No-Makeup Makeup | Lowest declared eye/cheek/lip intensity, source texture visible | Does not remove existing cosmetics or implement foundation evening |
| Soft Glam | Warm eye tint and softer nude/rose lip | Lash volume and full salon finish incomplete; close to other subtle presets in some portraits |
| Smoky Glam | Deeper dark eye definition with restrained lip/cheek treatment | Less dramatic than the generated guide, especially on035149 |
| Dewy Peach | Warm peach colors and softer lip | True dewy complexion/specular finish not implemented |
| Rosy Pink | Distinct rose eyelids/lip without broad white foundation | Some lip boundaries and pigmentation remain artificial at native size |
| Bronze / Golden Glam | Warm bronze eye color and nude lip | Gold metallic reflection is not established |
| Matte Nude | Restrained neutral eye/lip color | Full matte finish and contour not established |
| Classic Red Lip | Clearly distinct red lip within source shape | Can be warmer/lighter than the guide; conservative contour may underfill corners |
| Bold Evening Glam | Plum eye color and berry lip | Full lash/contour intensity incomplete; cool lip edge patches remain on035149 |
| Cloud-Skin Makeup with Blurred Berry Lips | Distinct berry color with original complexion | No cloud skin replacement; blur/edge fidelity incomplete; stays held |
| Manga-Lash Makeup | Restrained tint/eye definition | Separated lash clusters are not reproduced; stays held |
| Icy Silver Eye Makeup | Blue/silver family eye tint with softened anatomical fade | Appears matte blue rather than true silver shimmer; stays held |

All13outputhashesdiffer on each person, confirming pixel variation only. This does **not** establish full cosmetic style fidelity. The ten serving names/descriptions and three held entries are unchanged. No missing capability is silently redefined as supported.

## Validation and visual conclusion

95focusedtests pass, covering the new automatic controls, source material/lip regressions and corrective data gates.27unchangedMakeupruntime/API/packagechecks also pass, for122distinctchecks. Four actual neural identical reference controls leave original pixels exact. Repeating the first case after the complete style sequence reproduces its output, confirming that decoder list mutation does not corrupt cached content.

All52outputs pass independent original pixel checks outside actual cosmetic support and for protected semantic regions. Red channel increases in checked warm cheek support are zero. These are narrowly defined numeric checks, not calibrated perceptual skin scores. The saved guides, masks and original images are hash bound. All four complete catalog sheets and native eye sheets were viewed; native lip sheets exposed remaining corner/edge/color problems. Representative full512comparisons were also inspected.

The original person's complexion, expression, geometry, natural texture and scene are visibly retained compared with the pale reconstructed guides and earlier pasted transfer. Gray cheek patches and hard upper orbital plate transitions identified during this cycle are reduced in the final candidate. Eye/cheek/lip cosmetics are present, with especially clear pink, bronze, red, berry and cool eye color differences. This is meaningful broader progress beyond lip only.

**Complete full catalog realism is not established.** Strong lash shape, finish/metallic effects, some style separation and lip edge fidelity fail or remain unverified. No case is automatically human accepted or eligible for training. There is no biometric identity measurement or arbitrary new upload/generalization proof. Source skin preservation alone does not close the style gate.

The local Edge check verifies all182galleryimages across52cases, working person/style filters, native image viewer, desktop and390pixellayout without horizontal overflow, and zero page errors.95focusedchecks run normally; unchanged asynchronous runtime checks and headless Edge run outside the known Windows sandbox startup limitation. No new package install was needed.

Recorded initial CPU feature calls span0.766to1.446seconds, median0.825seconds, using saved preparation and cached sources/references. This excludes parsing, landmark preparation, source encoding/startup, queue, network and full application work. It is not a Kaggle or website latency claim. No new diffusion, Kaggle GPU, model training, API billing or cloud generation occurred. The one new pretrained checkpoint and source snapshot are isolated local downloads.

## Files and preservation

- `scripts/makeup_source_layers.py`: extends the existing source application with automatic anatomy support, counterfactual density, style pigment configuration and anatomical feathering; keeps the prior asset API and lip function intact.
- `scripts/makeup_local_features.py`: one CPU provider, strict checkpoint/source verification, explicit preprocessing adaptation, bounded caches and protected decode inputs.
- `scripts/evaluate_makeup_automatic.py`: frozen preparation, all catalog execution, saved field reapplication and truthful comparison gallery.
- `backend/tests/test_makeup_automatic.py`: same reference, foundation rejection, wrong color direction, source protection, lip compatibility, style intensity and neural cache controls.

Forty checked historical/input/output/servingreleasehashes remain unchanged, including the nine serving/release controls. The current Makeup worker, contracts, model/preset hashes, Hair/Nails, shared worker, CPU release bundle/notebook, UI, database and dependencies are unchanged. No Git publication or deployment. The earlier three training tool changes and target quality policy remain intact from the prior bounded task.

## Next milestone

The next milestone is project lead review of **these actual automatic outputs**, followed by resolution of the listed cosmetic fidelity gaps. An external makeup artist is not a prerequisite. This is a concrete result for review, not a request for the user to implement masks or obtain assets.

Corrective DATA finalization remains **BLOCKED by appearance/target acceptance**, with zero newly accepted pairs. MAKEUP corrective training is **NOT STARTED**. Existing MAKEUP-001 is already trained and preserved. After appearance acceptance, truthful source and cosmetic annotations, rights/provenance and identity separation still precede a new distinct adapter run, Base comparison and reviewed real application integration. Do not retrain on this unaccepted matrix or present the pretrained teacher as the project model.

Evidence: [structured receipt](makeup-automatic-correction-20261104.json), [current gallery](../../artifacts/makeup-local-transfer-20261104/catalog-review/review-self-contained.html), [source checks](../../artifacts/makeup-local-transfer-20261104/catalog-review/independent-source-checks.json), [95focusedchecks](../../artifacts/makeup-local-transfer-20261104/verification.log), [27runtimechecks](../../artifacts/makeup-local-transfer-20261104/runtime-regression.log), [spec0017](../specs/0017-makeup-automatic-local-features.md).
