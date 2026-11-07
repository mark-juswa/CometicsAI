# Makeup architecture review and bounded correction

4 November 2026. **Implementation DONE for the source material and data admission slice; full Makeup correction IN PROGRESS; visual appearance EXPERIMENTAL; production integration NOT STARTED.**

The Supervisor selected artist/salon authored cosmetic layers fitted to the original portrait. This task implements that input and material boundary plus corrective data admission. It does not claim a completed realistic full look. No approved full look artist assets exist in the inspected repository. Replacing their absence with another extraction or procedural lash sweep would repeat rejected work.

## 1. Actual current architecture

`backend/app/makeup_styles.py` exposes the ten original IDs. `data/makeup/DATA-M001-paired/inference_presets.json` contains the frozen serving/evaluation instructions and shared preservation prompt. These are inference presets, not ten learned training classes. Three additional Makeup definitions are held in `backend/app/style_release.json`.

`scripts/makeup_inference_server.py`, `MakeupRuntime.generate`, pads the original to a 512 square, supplies that image and selected text instruction to FLUX.2 Klein Base plus MAKEUP-001, then returns the whole generated frame. The shared worker in `scripts/unified_gate3_server.py` uses this same runtime under exclusive adapter ownership. `backend/app/generation/remote_makeup.py` checks model identity, style and result format. There is no source pixel or geometry lock in this return path. The production worker does not accept a separate makeup reference image.

Offline comparison guides called makeup references are mostly earlier generated style outputs. Their pale foundation, reconstructed features and altered illumination are not independent cosmetic ground truth. The source portrait remains the identity and complexion authority.

The selected FFHQ pairs use `scripts/data_m001_paired.py`, frozen selection and identity separation, historical human reviews and truthful generic captions. Variant positions makeup_01 to makeup_05 have no semantic style labels. `scripts/data_m001_package_training.py` builds the private input for `notebooks/train_m001_kaggle.py`. The runner uses the existing pinned FLUX/AI Toolkit LoRA foundation and Base versus adapter evaluation.

MAKEUP-001 already completed 250 steps. The retained checkpoint and 40 evaluation outputs were verified historically. Saying training has not started would be **DOCUMENTATION DRIFT**. Corrective retraining has not started. The original model remains unchanged.

## 2. Root cause assessment

| Boundary | Demonstrated finding | What is not established |
|---|---|---|
| Selected FFHQ targets | The stricter 60 pair screen rejected all targets for unchanged corrective reuse, with individual observations of complexion, texture, facial or scene drift | This does not reject all upstream FFHQ images or isolate the dataset as the sole causal source |
| Model | Matched diagnostics show full adapter amplifies pale highlights/retouching; foundation only also over edits | New data alone is not proved sufficient to eliminate reconstruction |
| Serving | Whole generated face is returned; prompt preservation provides no pixel lock | No website whitening operation was found in the inspected path |
| Earlier transfer | Coarse lip support, imported reference lip lightness, direct pale reference chroma and deliberate brow changes are present in rejected methods | Exact nonmask equality never established natural blending or complete style fidelity |
| Separation | Six selected comparisons still had pasted lips/cheeks and missing eye details despite technical tests | Another strength value is not supported as a systemic repair |
| Admission | Existing finalizer, package and training validator checked old approval/integrity without consuming the stricter rejection review | This gap does not itself explain every generated defect |

Evidence: [target review](makeup-corrective-review-20261025.md), [matched model diagnostic](makeup-quality-diagnostic-20261025-review.md), [realism audit](makeup-realism-audit-20261102.md), [failed full source proof](makeup-source-surface-20261102.md), [preferred lip review](makeup-retained-review-20261103.md). Global Base edits, preservation compositors and masked inpainting were previously unsuccessful or insufficient; no unchanged variant is promoted here. No unresolved implementation conflict with the approved FLUX/LoRA and shared serving architecture was introduced.

## 3. Complete inventory and coverage

| Style | Intended distinction from actual presets | Serving state | Corrected evidence |
|---|---|---|---|
| Natural Makeup | Light lash definition, neutral blush, muted rose lip | Active | Two retained lip component cases only |
| No-Makeup Makeup | Extremely subtle flush, sheer tint, minimal lashes, complexion evening | Active | Full look unverified |
| Soft Glam | Warm shadow, fine liner, gentle sculpting, satin nude rose lip | Active | Full look unverified |
| Smoky Glam | Brown/charcoal eye gradient and liner, restrained cheeks, nude lip | Active | Full look unverified |
| Dewy Peach | Peach cheeks/eyes/lips and restrained cheekbone glow | Active | Full look unverified |
| Rosy Pink | Rose blush/eyelids and pink lip | Active | Full look unverified |
| Bronze / Golden Glam | Bronze eyes, localized gold, warm cheeks and nude lip | Active | Full look unverified |
| Matte Nude | Neutral eyes, light contour, matte nude lip, natural texture | Active | Full look unverified |
| Classic Red Lip | Rich red lip on original outlines, minimal eyes, restrained cheeks | Active | Two retained lip component cases only |
| Bold Evening Glam | Brown/plum eyes, defined lash lines, sculpted cheeks, berry red lip | Active | Full look unverified |
| Cloud-Skin Makeup with Blurred Berry Lips | Diffused berry lip, restrained cheeks, soft base | Held, disabled | Two retained lip component cases only |
| Manga-Lash Makeup | Separated lash clusters, delicate liner, soft blush, restrained lip | Held, disabled | Full look unverified |
| Icy Silver Eye Makeup | Localized silver/blue shimmer, subdued cheeks/lips | Held, disabled | Full look unverified |

All 13 are read from the actual catalogs by the new inventory function. No IDs, descriptions or release flags changed. No style has catalog wide corrected appearance acceptance. Existing expansion coverage on two development people is not quality approval. Pigment tinting does not implement lashes, sparkle or a calibrated matte/dewy finish.

## 4. Chosen correction and implementation

Use explicit source fitted coverage and materials, with the original image as the canvas. Apply source anchored, bounded Lab material offsets, retaining the source variation inside uniform coverage. Blush keeps source lightness; unsafe shadow/highlight ranges are refused. Gamut compression limits clipping. There is no generated spatial illumination, face warp or smoothing. This is a bounded source color mechanism, not a calibrated physical skin or undertone model.

The materially different input is artist authored cosmetic information with native source boundary review. The algorithm no longer claims to recover blush, shadow or highlights from a pale flattened generated face. Artist masks still require real review; the implementation does not automatically fit arbitrary uploads. Its appropriate first use is **offline target preparation**, followed by separate model learning/evaluation. It is not adopted as an inference only substitute for corrective training.

Actual files:

| File | Responsibility |
|---|---|
| `scripts/makeup_source_layers.py` | Shared material operator, source/mask hashes, parser protection, overlap refusal, artist review attestation, lossless offline file entry point |
| `scripts/makeup_target_quality.py` | Individual quality review template/validation, truthful source/target annotations, identity/hash binding, target rejection policy |
| `data/makeup/MAKEUP-CORRECTION-001/quality-policy.json` | Hash pinned projection of the preserved rejection ledger, including decoded target RGB and known reused development IDs |
| `scripts/data_m001_paired.py` | Pending quality template and mandatory separate quality admission before finalization |
| `scripts/data_m001_package_training.py` | Refusal before ZIP creation and bundled shared validator/policy |
| `notebooks/train_m001_kaggle.py` | Revalidation before preparation and GPU preflight; quality evidence bound to prepared run |
| `scripts/review_makeup_architecture.py` | Frozen input verification, six component reproductions, four column comparisons and complete catalog report |
| Three focused test files | Source material, target admission and paired training/package regression coverage |

The retained lip implementation and its frozen helpers are unchanged. Prechange copies of the three training tools are preserved under `artifacts/makeup-architecture-20261104/before-source`. The existing model, data and old experimental algorithms are not overwritten.

## 5. Validation and limits

The comparison matrix is Natural, Classic Red and Cloud/Berry on the two reused development portraits, which visibly differ in complexion. Every row shows **Original | Existing AI guide | Rejected previous transfer | Retained lip component**. Existing guides are explicitly labeled defective generated faces. The last column is lip only, not a corrected full selected look.

All six new operator results exactly reproduce the already preferred lip pixels. Nonlip source skin, eyes, brows, nose, teeth, hair and scene remain exact. The images show the existing lip improvement over pale reconstruction and pasted transfer; **this task does not demonstrate a new full look visual improvement**. Conservative edge underfill, weaker/lighter warm red, and missing eye/cheek/lash/finish treatment remain. Those omissions cannot be scored as passing style fidelity. The six regression packs are not artist assets or usable training targets.

The new material checks cover finite data, protected boundaries, stale source/maps, overlap refusal, mandatory artist review and the lossless file workflow. Synthetic source levels test the blush lightness invariant, not real skin tone coverage. A guard found during review now refuses black cheek pixels rather than lifting their lightness into the safe range.

Local checks: 75 focused tests passed, followed by the final 20 test material suite (including the added shadow guard); 27 unchanged Makeup runtime/API/package tests passed. This covers 103 distinct checks. The training ZIP validator runs in a fresh subprocess. All 60 rejected file hashes and their decoded RGB are excluded. A lossless reencoded rejected target is also refused. Historical dataset preparation and execution refuse before GPU preflight, and the original data is not edited.

The initial broader test attempt stalled at Windows sandbox asyncio socketpair initialization. A bounded probe recorded the stack; rerunning the unchanged runtime tests outside the sandbox passed 27/27. The initial gallery launch also failed inside Edge's sandbox profile; the outside sandbox headless check passed 24 images, desktop/390 pixel layouts, native image download and zero page errors. These are environment/check records, not model quality results. Earlier failed test logs are retained; fixture Lab range and Windows UTF8 test issues were corrected without weakening product assertions.

There is no untouched person, strong eye correction, full medium/glam correction, warm/cool full palette review or all style appearance proof. No new parser/landmark model, diffusion inference, GPU generation, training, package installation or paid call occurred. Review attestations are not authenticated reviewer identity or automatic appearance scoring. Exact decoded hash refusal is not perceptual near duplicate detection.

## 6. Preservation and next milestone

Forty preexisting code/input/output/serving/release file hashes match the start receipt, including the nine serving/release controls. Hair/Nails, current Makeup runtime/contracts/catalog, unified worker, CPU release bundle and notebook remain unchanged. No application UI, database, secrets, dependency, Git publication or cloud change. Passing unchanged local Makeup contracts and exact release hashes supports isolation, not fresh live availability.

**DATA-M001 corrective finalization: BLOCKED by missing accepted targets. New usable corrective pairs: zero. MAKEUP corrective training: NOT STARTED and not ready.** The prior MAKEUP-001 is already trained and must remain a historical baseline. Any corrective run needs a distinct output identity and checkpoint. The current runner's 50/10 layout and source pin are preserved; a changed collection, count or training schedule requires its own reviewed configuration.

Next concrete milestone is one artist/salon reviewed **complete** asset set spanning the catalog families and representative original complexions. The same source layer mechanism can consume its coverage and pigment materials. Missing effects must be supplied and evaluated, not approximated silently. Only accepted complete results may become proposed paired targets. Finalization then requires truthful annotations/terms and identity separation, with separate untouched final acceptance people. Training, Base versus new adapter comparison, and reviewed real generation integration follow as independent milestones. Neither this renderer nor target approval proves the model will learn source preservation.

## Evidence

- [Specification](../specs/0016-makeup-source-layer-quality.md)
- [Offline asset and review contract](../guides/makeup-source-layers.md)
- [Four column comparison gallery](../../artifacts/makeup-architecture-20261104/review-validated/review-self-contained.html)
- [Source bound inputs, catalog and component results](../../artifacts/makeup-architecture-20261104/review-validated/review.json)
- [Preservation receipt](../../artifacts/makeup-architecture-20261104/preservation.json)
- [Focused checks](makeup-source-layer-tests-20261104-focused.log), [final material guard checks](makeup-source-layer-shadow-guard-20261104.log), [runtime checks](makeup-runtime-checks-20261104.log)
