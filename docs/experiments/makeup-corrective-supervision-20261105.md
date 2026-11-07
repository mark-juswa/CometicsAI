# Corrective Makeup supervision, 5 November 2026

**IN PROGRESS complete Makeup. VERIFIED data and compatibility implementation. 13 representative target appearances approved. 78 candidates prepared, zero formally admitted. Corrective training and production integration NOT STARTED.**

The Supervisor accepted the revised Rosy Pink, Matte Nude and Manga-Lash appearances. This completes the thirteen representative appearances, following ten acceptances in the returned review. All thirteen exact target images and captions are retained. It does not approve the other sixty five targets or establish the quality of our own adapter.

## Current architecture and demonstrated defect

The original FFHQ-Makeup archive and audited paired selection supply originals and provenance. Archived makeup variant positions are not catalog classes. Historical target auditing established that the targets can lighten skin, smooth texture and reconstruct features. None of the rejected sixty targets is admitted for unchanged corrective reuse.

The active application selects one of ten serving Makeup IDs. Its worker, `scripts/makeup_inference_server.py`, supplies the original portrait and `PROMPTS[style_id]` to the existing FLUX pipeline and returns its complete generated image. It has no enforced identity or complexion lock. Hair and Nails use their existing separate controls.

Inspection of the actual sixty historical training rows finds **one identical generic caption and zero style IDs**. The inference catalog therefore did not provide style specific training supervision. This is a demonstrated labeling gap, not proof of the causal share of Base versus adapter behavior. The historical caption audit is saved in the corrective workspace. The returned two reference GPU results prove that the old adapter and verified Kaggle configuration still whiten/reconstruct faces, despite a better cosmetic guide. They do not isolate Kaggle, Base or adapter causality. That inference proposal remains rejected.

## Complete inventory

| Style ID | Catalog name | Existing release status |
|---|---|---|
| natural_makeup | Natural Makeup | Serving |
| no_makeup_makeup | No-Makeup Makeup | Serving |
| soft_glam | Soft Glam | Serving |
| smoky_glam | Smoky Glam | Serving |
| dewy_peach | Dewy Peach | Serving |
| rosy_pink | Rosy Pink | Serving |
| bronze_golden_glam | Bronze / Golden Glam | Serving |
| matte_nude | Matte Nude | Serving |
| classic_red_lip | Classic Red Lip | Serving |
| bold_evening_glam | Bold Evening Glam | Serving |
| exp_cloud_berry_lips | Cloud Berry Lips | Held |
| exp_manga_lash | Manga-Lash | Held |
| exp_icy_silver | Icy Silver | Held |

The catalog builder reads the existing inference presets and release candidates and requires all thirteen IDs. No style was removed or silently enabled. Each style has eyes, lips, blush, complexion finish, brows, contour/highlight and the same identity/complexion preservation instruction. Exact catalog names remain in `catalog.json`; this table uses readable labels.

## Coherent correction

Correct the supervision before another model run. A single frozen component catalog now drives photographic teacher requests, distinct paired captions and Base versus new adapter evaluation. Original portraits supply identity, anatomy, complexion and scene. External teacher edits supply candidate complete cosmetic appearances. They are explicitly synthetic, not archived FFHQ variants, artist assets, or our model outputs.

Preparation reuses the existing CPU parser, MediaPipe landmarks and dense registration. It fits the teacher to original anatomy, restores original eye cores, mouth/teeth, nostril core and scene, and returns bounded source skin detail. It does not globally darken or match every generated pixel. Complete foundation, eyes, cheeks, lips and finishes remain visible for review. This is target preparation, not a deployed inference correction.

Additional target inspection found that v4 scalar brow density over inpainted skin can make flat/gray brow plates. Removing the density cap and a local RGB ratio probe did not resolve the plate; neither probe was adopted. The retained v5 correction fits original RGB brow gradients to the surrounding foundation with the already installed OpenCV Poisson solver. Original spatial brow detail supplies the patch, with exact protected write boundaries. A regression test exposed OpenCV mutating its mask scratch buffer; keeping an independent write support fixed it. Original brow RGB is not an exact invariant in v5. The original eye cores and scene remain exact. The approved thirteen v3 targets remain byte identical. Earlier v3/v4 candidates and probe evidence remain intact.

This addresses a real supervision gap and a demonstrated preparation defect. It does not prove that teacher complexion/texture is universally correct or that training will reproduce source protection.

## Implementation

| File | Responsibility |
|---|---|
| `scripts/makeup_corrective_catalog.py` | Complete catalog, cosmetic components, style captions and teacher instructions |
| `scripts/makeup_corrective_data.py` | Frozen source assignment, lossless pairs, provenance, coverage, quality admission and finalization |
| `scripts/prepare_makeup_sources.py` | Pinned CPU anatomy with verified reusable caches |
| `scripts/prepare_makeup_teacher.py` | Existing source fit extended with valid support, bounded detail, cached anatomy and versioned brow preparation |
| `notebooks/train_m001_kaggle.py` | Corrective schema support, separate fresh Base configuration and thirteen style evaluation; legacy behavior retained |
| `scripts/data_m001_package_training.py` | Standalone corrective validation and compatible packaging |
| `backend/tests/test_makeup_corrective_data.py` | Positive/negative data, runner, standalone package and preparation regressions |

Authoring orchestration, raw requests, failed candidates, review bindings, galleries and CPU logs are under `artifacts/makeup-corrective-supervision-20261105/`. The active workspace is **data-candidate-04**. Earlier candidate workspaces remain intact.

## Concrete data and validation

All **78 real candidate pairs** are present: 52 training and 26 validation pairs, four distinct training people and both validation people for every style. There are twelve training identities and the unchanged two development validation identities, 054109 and 056266. Two audited originals, 003025 and 027921, were added to training for broader complexion coverage. Their original archive membership, archive hash, metadata hash and photo credits are retained. These are existing project sources, not invented subjects. Some source photographs already wear makeup; draft annotations explicitly retain uncertainty about product use.

The 63 request worker pool completed all 63 requests without a generation error, in addition to the first two added complexion cases. All sixty five raw images and exact requests are saved. The tool's accumulated image display exceeded its IPC frame limit after completion; the saved records and final worker outcome establish that no generation or saved result was lost. No request was restarted because of that display failure.

The independent audit verifies original decoded training pixels, all source/target file hashes, complete planned coverage, split/provenance bindings, original protected pixel regions in all seventy eight outputs, and unchanged eight serving/release controls. The real candidate set reaches the mandatory human admission gate and is correctly refused there. It is not marked FINALIZED.

**38 focused checks passed** after the final preparation change, including both brow regression tests and existing data/quality checks. An earlier broader eighty check run passed before the final brow change; those counts overlap and are not additive. The standalone CPU package/prepare path is tested on synthetic reviewed fixtures, not falsely admitted real targets. The 78 actual image scope checks are separate from those software tests.

The offline gallery embeds 210 lossless image assets, including actual earlier CPU results where available. Browser verification covers all thirteen style groups and seventy eight pairs, 312 displayed image slots, native enlargement, exact review export bindings, no script errors and no page overflow at desktop and 390 pixel mobile width. The QA export stays entirely PENDING and does not admit data. Initial sandbox Edge profile failure and lazy loading test timeout were resolved for verification; neither was a model failure.

## Visual evidence and coverage limits

The original thirteen comparisons already include Original, raw Makeup reference, previous rejected CPU output and prepared target. The new full review shows **Original | Approved style representative | New raw teacher | Prepared target**, with a button to show a previous rejected CPU output only when that exact source/style result exists. It does not invent missing historical results for new people.

All thirteen six-person sheets were inspected, covering subtle, medium, strong eye/lip, warm and cool styles. Full looks and style color changes are visible, unlike the earlier lip dominated compositor. Strong red/berry lips, charcoal/plum smoky lids, bronze/gold and silver lids, dewy versus matte finishes and lash variants are represented. Original source features/scene remain anchored by fitting. The additional portraits expose variation that the four-person representative set could not establish.

**Remaining concerns:** some teachers warm or darken foundation, soften original texture, and vary in lash cluster strength. Soft/Natural/No-Makeup separation and blush blending depend on identity. Skin median Lab differences are diagnostic only; they are not a quality score, shade correction, or proof of matched undertone. Whole-sheet inspection is not exhaustive native skin/edge acceptance. The gallery exposes native images and editable annotations for that review. The thirteen previous approvals stand; the additional sixty five appearances and complete training admission remain pending. No claim of catalog wide model quality is supported yet.

Review: [complete target review](../../artifacts/makeup-corrective-supervision-20261105/full-data-review-01/review-self-contained.html), [independent audit](../../artifacts/makeup-corrective-supervision-20261105/full-data-review-01/independent-audit.json), [browser receipt](../../artifacts/makeup-corrective-supervision-20261105/full-data-review-01/browser-verification.json), [focused tests](../../artifacts/makeup-corrective-supervision-20261105/corrective-tests-final.log).

## Preservation and next milestone

Existing datasets, teacher proofs, raw generations, rejected results, trained adapter and releases are preserved. Eight captured serving/release controls match their baseline hashes. No Hair, Nail, application UI, backend contract, serving model or cloud deployment change was made in this correction. The existing prepared combined release still has eighteen Hair, ten Makeup and eight Nail styles. Its prepared state is not a fresh live acceptance claim.

The next gate is **individual training target admission**, using the existing eight criterion policy at `data/makeup/MAKEUP-CORRECTION-001/quality-policy.json`. Appearance approval alone did not admit the original thirteen, and cannot admit unseen pairs. The full gallery provides actual candidates, original credits, criterion notes and draft source/target annotations before asking for that review. Failed pairs must be corrected or explicitly rejected, without weakening completeness requirements to permit training.

After admission: finalize a new corrective DATA copy, prepare the existing compatible Kaggle package, train the separately named fresh Base candidate, evaluate all thirteen styles on Base versus the new adapter, compare old model evidence, and then validate real application generation. The known 250 step configuration is a bounded initial run, not a guarantee of sufficient training or deployment readiness. Validation people are reused development identities, not an untouched final test set. Only validated real generation should be integrated with matching catalog instructions and the existing API/UI contracts. Production remains subject to the Project Lead's separate review. **We cannot proceed to real corrective training or deploy this as a model fix yet.**
