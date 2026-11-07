# Complete Makeup and same day release

5 November 2026. **CONFIRMED implementation authorization. Complete look and release NEEDS VERIFICATION.** Supervisor rejects the Nov5 lipstick heavy full result and approves a complete look correction followed by actual application validation and matching deployment with expanded Hair/Nails. Existing MAKEUP-001 remains the trained generative stage. New corrective training is a separate milestone, not a claimed same day result.

## Current evidence and next gate

## Corrective supervision, authorized 5 November

**CONFIRMED development authorization:** Supervisor says “lets develop the fix for it” after the failed real model review. Keep the existing FLUX/LoRA foundation and protected serving/release contracts. Implement corrected training supervision before another GPU test. This supersedes the two reference inference proposal for promotion.

**Demonstrated labeling gap:** all60historicalpairs share one generic caption and zero rows have a catalog style ID. The ten catalog presets were inference controls, not trained style labels. Together with rejected whole face targets, this is a concrete supervision defect. It does not establish the complete causal share of Base versus adapter whitening.

**Decision:** reuse source fitted external teacher preparation as candidate target creation, not a live generation replacement. One frozen catalog covers all10existingand3heldstyles with explicit cosmetic components. Use it to generate target requests, pair captions and evaluation prompts. Keep lossless source/targetPNG pairs with equal stems and original source photo/FFHQ provenance, generation request, raw teacher and preparation hashes. Archive variant positions remain positions, never style labels. Keep actual source cosmetic annotations separate from the requested target style.

Prepare a balanced identity selection using the existing10train/2validation split: four distinct training identities per style and both validation identities per style,78plannedpairs. This is a planned count, not an accepted dataset or a claim of adequate training scale. First produce one review target per13styles on the four already inspected people, beginning with subtle, warm and cool strong cases. Reuse approved035149Bold and existing006553Soft teacher proofs transparently; their records still require individual target admission. Additional identities follow only after the complete target direction is credible. Previously reused validation identities remain development validation, not an untouched test set.

Extend the existing quality and training entry points with an explicit corrective schema. Keep historical validation unchanged. Require complete style coverage, source identity separation, exact image/caption/provenance bindings and existing individual human quality admission. No fake FFHQ variant or old FINALIZED status may admit a new target. The new candidate adapter starts from pinned Base with the existing proven training configuration, not from the rejected adapter. Separate run/output names preserve every checkpoint. Keep250stepsas a known bounded first run, without claiming it will establish quality.

Evaluation uses the same selected style instructions with original portrait conditioning. Compare Base and the new adapter, retain raw results, and separately compare against the old MAKEUP-001 where available. Both identity/complexion and complete cosmetic fidelity must pass before serving integration. No new model family, provider infrastructure, mask loss or large dependency is introduced. The existing teacher fitter's source protection is not proof that training will learn it.

**Acceptance:** (AC1) one frozen13stylecatalog drives target requests/captions/evaluation; (AC2) source fitted candidates preserve declared original features and have truthful synthetic provenance plus visible complete looks under visual review; (AC3) finalized corrective data cannot leak identities, reuse rejected targets, omit styles or bypass individual review; (AC4) the compatible runner prepares a fresh candidate config and all13styleBase/adapterevaluation without changing historical behavior; (AC5) existing serving/Hair/Nails/model/release controls remain unchanged. The complete fix remains IN PROGRESS until actual new model and application acceptance, even when these local code checks pass.

**Build order:** catalog and historical caption audit (AC1), representative then13targetreview using existing fitter (AC2), corrective manifest/admission and runner compatibility (AC3/4), focused tests/preservation (AC5), then data review before any training. Target review and production review remain distinct user decisions. No speculative GPU sweep or automatic acceptance.

## Earlier evidence

**Returned GPU gate, 5 November: technical VERIFIED, both guided MAKEUP-001 outputs REJECTED by engineering.** Original archive, exact source/guide inputs, environment, model/adapter assertions, settings and raw output hashes match the prepared two call test. Soft Glam severely whitens the deeper source complexion. Both faces become plastic with reconstructed features and exaggerated cosmetics. Stop promotion and any full catalog run of this approach. No serving integration or new target admission. Complete photographic targets and a separately evaluated corrective adapter remain the next unresolved data/model milestone; no training success is implied. [Returned evidence and limits](../experiments/makeup-guided-gpu-review-20261105.md).

**5 November update: original local complexion proposal DEPRECATED after visual rejection. Full Makeup IN PROGRESS. Production integration NOT STARTED.** Supervisor rejected both the twelve case whole face review and the revised four case comparison as too weak. Stronger signed fields and gradient blending also failed engineering visual inspection. Their source, outputs and failure evidence remain under `artifacts/makeup-complexion-release-20261105/`; the added rejected branches were archived and the pre attempt helpers restored.

Supervisor approves the fourth panel of `teacher-proof/035149-comparison-v2.png` as the complete makeup direction. This is an external editor target proof, fitted to the original anatomy with original eye cores, brows, teeth, nostril core and scene restored. It is not MAKEUP-001 output. Approval is limited to visual direction. No training target or production capability is admitted by it.

## Current bounded decision

Test the existing MAKEUP-001 with two image inputs before considering any serving change. Image1 is the original identity, complexion, geometry, lighting and scene. Image2 is a labeled synthetic complete cosmetic guide from a different training identity. The exact pinned Diffusers implementation already supports multiple image references. Keep the foundation, adapter, seed1977,20steps,guidance4 and512square. Record the complete effective prompt separately from the unchanged frozen preset hash.

The absent visual cosmetic guide in current inference and defective pale historical targets motivate this hypothesis. A better guide may establish full look detail without copying an entire pale target appearance. The model can still transfer guide complexion or reconstruct features. This diagnostic must inspect raw output rather than conceal that failure with the rejected compositor. Passing the two cases would support a broader test, not catalog acceptance.

**Inputs and values:** `data/makeup/MAKEUP-GUIDED-001/plan.json` binds the exact two sources, guide images, earlier rejected comparison images, file hashes, author/license metadata and original inference settings. Soft Glam uses validation identity054109 and training guide006553. Bold Evening uses validation identity056266 and training guide035149. Guides are prepared external editor outputs. These are reused development subjects, not an untouched final evaluation. No guide uses the test portrait's identity.

**Implementation:** reuse private `makeup_quality_bootstrap.bootstrap`, with an explicit allowlisted diagnostic runner. `makeup_reference_diagnostic.py` verifies the pinned environment, model index, adapter file and actual active tensors/scaling. Load one foundation, make exactly two generations, save raw PNGs, actual prompts, memory/timing, four panel comparisons and partial results on failure. No server, tunnel, training, model replacement or Render change. `prepare_makeup_teacher.py` reuses the existing source fit and protection helpers. Its output remains a review candidate, with explicit synthetic provenance and no automatic admission.

**Acceptance for this gate:** local package and failure path checks must pass; then both actual GPU outputs need visible base, eyes, cheeks and lips with complexion, texture and identity retained. The human review must distinguish these from the synthetic guide. A failed case stops promotion. A passing result leads to all13catalog review and actual application validation before production. New paired data admission, corrective training and Base comparison remain separately required milestones for a corrected trained model.

**Rollback and preservation:** no live path changes in this gate. Existing standalone/unified Makeup contracts and the latest18Hair/8Nails prepared combined release remain unchanged. Existing10Makeup serving IDs and3held IDs remain explicit. Preserve old notebooks, datasets, adapters and experiment artifacts.

**Primary implementation reference:** [the pinned Diffusers Klein source](https://github.com/huggingface/diffusers/blob/c943837899b16cbae2f619b8dd4f7bb6f07dd81a/src/diffusers/pipelines/flux2/pipeline_flux2_klein.py) accepts a list of image references and encodes their conditioning latents. This establishes API support, not makeup transfer quality.

## Original rejected decision

Extend the existing automatic source application with a complexion stage before cosmetic absorption. The prior function lacks foundation/concealer: leaving most skin unchanged prevents a finished base. Fix that responsibility in place, without a new provider or runtime architecture. Preserve existing default calls, artifacts, weights and Hair/Nails. An optional context flag selects the new stage, allowing truthful comparisons and rollback.

Foundation shade comes from the original skin, never generated foundation RGB. Existing source parser/primary face and original anatomy determine coverage. Source low frequency chroma supplies a local matched shade. Controlled coverage reduces uneven pigmentation. Source broad luminance supplies lighting; luminance correction is bounded and gated by source discoloration, with local under eye concealer. Retain fine source detail and original feature geometry. This intentionally changes skin appearance, without replacing its underlying complexion.

Source anatomical cheek regions supply bounded contour/dimension. Selected catalog identity continues to determine learned eye/cheek pigment, lip and finish. Do not erase makeup to satisfy preservation. Do not reuse the rejected comb-like detail overlay in the first complete look gate. Keep this omission explicit; Manga cluster fidelity remains a separate acceptance requirement, not an enabled success.

## Value sources and invariants

| Value | Source |
|---|---|
| Source image/labels/anatomy | Existing hash bound portraits, parser, source MediaPipe478/SPIGA68 |
| Foundation chroma/illumination/detail | Original source pixels at separated spatial scales; no generated complexion |
| Foundation/concealer/contour intensity | One declared configuration covering all13catalog IDs, scaled by look intent |
| Eye/blush appearance | Existing saved self versus local feature fields for the first proof; actual MAKEUP-001 generation must be tested separately before release |
| Lip color/coverage | Existing reviewed component/material and selected guide |
| Production model | Existing trained MAKEUP-001, unchanged checkpoint |
| Release | Matching existing Render/BeautyCore and Kaggle workflow, expanded Hair/Nails retained |

Complexion coverage may affect source skin/nose color, not eye opening cores, brows, nostril shape, mouth opening, teeth, hair or scene. Nose luminance is excluded from complexion correction. Foundation must not be a flat color fill, global pixel match, generated face blend or pore blur. Existing region protection assertions must distinguish intended skin coverage from feature reconstruction. Technical checks do not establish appearance acceptance.

## Build and gate

1. Preserve current source and canonical rejected results in a new workspace. Add reusable complexion coverage to existing materials; optional orchestration stays in the same automatic entry point. No new model/download/GPU call for this first proof.
2. First evaluate Natural, Soft Glam and Bold Evening on four existing people, with original, selected reference, actual prior and complete candidate. Inspect native face and skin detail. Do not run another full matrix before this complete look is visually credible.
3. If the whole face gate passes, verify all13styles and fresh arbitrary upload anatomy, then wire the same correction to actual MAKEUP-001 output with truthful model/postprocessing metadata. Cached fields are not live inference proof.
4. Test existing contracts, feature switching and real application generation. Prepare matching immutable CPU/notebook release around the original GPU bundle. Fresh GPU/website rehearsal and user visual approval precede production acceptance. No broad refactor, database redesign or unrelated release change.

## Limits and release status

Local quality, arbitrary input fitting, runtime latency/memory and fresh Kaggle availability remain unverified at design time. No deployment guarantee follows from a deadline. Catalog styles remain in scope and held IDs stay explicit. Record failures without mass rerendering, target auto acceptance or model retraining claims. Production adoption remains PROPOSED until these gates pass.


## Sampling and target review update, 5 November

The13representativeappearances are now explicitly approved after3requestedrevisions. Keep those exact images/captions. Inspection of existing source coverage motivates adding audited originals003025and027921to training, retaining all10originaltrainidentities and the same2validationidentities. The proposed52train/26validationpaircount and4/2identitycoverageperstyle remain unchanged. The source assignment now has12trainidentities, not the earlier10. Additional pairs require their own review; none is accepted by the representative approvals.

Absolute source brow RGB restoration creates gray patches on the added portraits. For additional targets, v4removes the teacher brow and reconstructs the original spatial hair contrast as optical density on the current foundation. Original brow RGB is therefore not an invariant for v4. Original eye cores, teeth/mouth, nostril core and scene remain protected. Keep the approved v3images and failed v3newsourceexamples as evidence. The actual new complexion v4examples have been inspected; broader output quality remains unverified until all cases are reviewed. No new training loss, model family, live editor replacement or production path is introduced.

## Full authoring and preparation correction, 5 November

The78candidateplanis now fully authored and prepared. Preserve the13approvedv3targets/captions. The additional65targetsusev5, superseding v4 after actual full batch inspection exposes flat/gray brow plates. Existing OpenCV Poisson fitting retains original RGB brow gradients and adjusts their boundary colour to the current foundation, rather than applying scalar density to an inpainted plate. Copy OpenCV mask scratch buffers and retain an independent anatomical write support so protected holes remain exact. No new model, provider, dependency, live pipeline or training loss is introduced. v2 remains the default and v3/v4 evidence remains reproducible/preserved.

Quality admission remains separate from appearance approval. The full review includes actual original/approvedstyleguide/rawteacher/preparedtarget panels, prior CPU results only where they exist, photo credits, eight criterion records and editable source/target annotations. It exports bound human decisions without finalizing or starting training. The real78pairsetcorrectlyfails pending human admission;38focusedchecks/78protectedregionchecks/8servingreleasehashesandgalleryQApass. Skin tone, texture and lash consistency remain under visual review. No new adapter or production acceptance follows from these checks. [Full evidence](../experiments/makeup-corrective-supervision-20261105.md).

## DATA admission and training handoff milestone, 6 November

Target admission is complete under the existing criteria: Supervisor explicitly confirms all 78 pairs on all eight criteria. The exact returned export and clarification are preserved with source/target/caption bindings. A separate final DATA copy and private training ZIP now pass the existing validators. The ready notebook reuses the existing pinned fresh Base/LoRA runner and separate 250 step candidate name, with 13 style Base/new evaluation and preserved partial results. CPU checks on actual accepted data pass; no GPU training, actual corrected model result or application integration is implied. AC3/data admission and AC4/local compatibility are verified at this milestone; model quality and production acceptance remain open. This advances the existing design without a new architecture or another target review requirement. [Handoff evidence](../experiments/makeup-corrective-training-handoff-20261106.md).


## Model acceptance and controlled application milestone, 6 November

Actual corrective training completes 250 steps and 52 Base/new outputs on the approved foundation. Supervisor accepts all 26 bound RAW model cases across 13 styles for application validation. This closes the model gate on two reused development people, not untouched generalization or production approval. No new algorithm, model family or target audit is selected.

Advance the existing application gate through an immutable candidate built from the preserved complete Hair/Nails release. CPU and GPU copies must bind checkpoint SHA256 `991a1037cc892c1a62e1a731be577ed1aec2f331d9568b4586ff3829a4ee32c3`, truthful corrective DATA/training metadata and exact 13 accepted captions. Original GPU bundle verification precedes a separately recorded fresh workspace overlay and adapter directory. Preserve original artifacts/manifests. Existing shared ownership, tensor equality, API contracts and Hair/Nails settings remain. Require full loaded scaling for corrective Makeup. Candidate exposes all 13 Makeup styles solely for testing and returns before website registration. Production catalog stays unchanged.

Actual local archive/staging/API transport checks and 62 regressions pass. Real application validation must compare authenticated facade outputs with accepted RAW results, verify model/prompt/settings and active tensors, and retain one foundation across both Hair adapter routes, Makeup and Nails. A prepared Nails crop is only a GPU switching check. Fresh uploads, website/consultation/save/book/mobile and project lead production review remain open. No deployment or another training run follows automatically from CPU preflight. [Evidence](../experiments/makeup-corrective-model-results-20261106.md).


## Real application and matching release checkpoint, 6 November

The actual application gate now passes all 13 Makeup styles with exact accepted RAW PNG bytes. All 16 real feature calls, active tensor checks and one foundation verify. This closes the controlled shared application gate on the existing subjects; fresh identity and website acceptance remain open. Do not repeat target/model audits on identical pixels.

The prepared production candidate extends the existing style release mechanism with three Makeup execution profiles bound to the accepted contract source hash. It uses the same checkpoint, captions and generation code as the successful application. New manifest ID is styles-20261106-01 with 18 Hair/13 Makeup/8 Nails; matching Render/business JSON comes from the existing generator in isolated staging. Historical releases retain their actual ten Makeup IDs. Normal authenticated registration is restored only in the separate deployment starter. No API/UI/database redesign or new model/dependency. Fifteen proposed source/test files are hash bound; actual archive/API preflight, 25 staged runtime/API tests, five Render checks and corrupted-profile refusal pass.

Production source application/publication and rollout remain PROPOSED pending the project lead review required in the original task. Existing production sources/defaults and cloud remain unchanged. Fresh website upload, manual/consultation generation, save/book, full hand Nails and mobile must still be recorded honestly. [Evidence](../experiments/makeup-corrective-application-results-20261106.md), [review and rollout](../guides/makeup-corrective001-release.md).


## Authorized deployment checkpoint, 6 November

Supervisor now authorizes deployment. The presented source/metadata is applied, and final serving notebook `notebooks/render_kaggle_makeup_corrective_demo.ipynb` corrects an existing startup guard that omitted Makeup model IDs. Actual gate tests require all enabled Hair, Makeup and renderer IDs and reject missing feature IDs or wrong digest. Accepted model/prompt/generation bytes remain unchanged. Source publication578330d and matching Render deployment are VERIFIED Live; source/index preservation and all focused checks are recorded in the deployment report.

Kaggle authentication/serving registration remains open. No new GPU session, image sweep, target audit or training occurred. The final notebook/new CPU/existing GPU must register normally before the model can be called live from the website. Fresh portrait, website/manual/consultation/save/book/full hand/mobile checks remain explicit. Production authorization persists; do not request it again for this same rollout. [Evidence](../experiments/makeup-corrective-deployment-20261106.md).
