# BeautyCore: researched style expansion shortlist

> Current release architecture: [0015 expanded styles deployment plan](0015-expanded-styles-release.md). All 13 candidates are selected targets; per-style quality acceptance and integration remain required. Later failures supersede earlier promotion recommendations. Design is confirmed for implementation; deployment is incomplete.

Date: 25 October 2026. Status: **CONFIRMED for the recommended first-batch pilot**. Remaining candidates and public release remain proposed; data collection and model quality acceptance are pending.

The earlier generic batch is superseded. These are specific looks supported by current salon, brand or beauty reporting. Evidence of online interest does not establish Philippine demand, salon capability or our model's ability to generate the look. Composite names below are BeautyCore's proposed labels; sources support the underlying techniques.

## Hairstyle candidates

| Candidate | Visible difference to require | Existing option to compare against | Reference |
|---|---|---|---|
| Butterfly Cut | Prominent face-framing upper layers while retaining length | Layered Hair | [Redken](https://www.redken.com/blog/best-winter-haircuts-trends.html) |
| Wolf Cut | Choppy crown and longer back | Shag Hair | [Redken](https://www.redken.com/blog/best-winter-haircuts-trends.html) |
| Korean Two-Block | Longer upper hair over a visibly shorter lower section | Curtain / Side-Part Undercut | [Hongdae salon](https://www.hongdaehairstudio.com/blog/trending-korean-hairstyles-for-men-2026-edition), [GQ, 3 October 2026](https://www.gq-magazine.co.uk/article/two-block-haircut) |
| Korean Comma Hair | A clearly curved front lock | Curtain Hair | [Hongdae salon](https://www.hongdaehairstudio.com/blog/trending-korean-hairstyles-for-men-2026-edition) |
| Textured French Bob with Wispy Bangs | Fringe plus a textured short outline | Bob Hair | [Pinterest, 6 October 2026](https://newsroom.pinterest.com/news/beauty-trend-report-2026/) |

Overlap is intentional to test: do not sell a new label if outputs are indistinguishable from an existing style. Test either verified Hair adapter where appropriate; a proposed style is not an approved training label.

## Makeup candidates

| Candidate | Visible difference to require | Main quality risk | Reference |
|---|---|---|---|
| Cloud-Skin Makeup with Blurred Berry Lips | Diffused lip color and a soft base | Excess smoothing or altered lip geometry | [Vogue](https://www.vogue.com/article/blurred-makeup-trend-2026), [Pinterest](https://newsroom.pinterest.com/news/beauty-trend-report-2026/) |
| Manga-Lash Makeup | Clearly separated lash groups | Unwanted eye or eyelid reshaping | [Pinterest](https://newsroom.pinterest.com/news/beauty-trend-report-2026/) |
| Icy Silver Eye Makeup | Cool silver-blue eyelid accents | Metallic pigment bleeding beyond makeup regions | [Pinterest](https://newsroom.pinterest.com/news/beauty-trend-report-2026/) |

These are custom-prompt experiments with MAKEUP-001 first. The production ten-preset file and its integrity checks stay intact. Strong visual differences matter more than collecting extra labels for similar pink, peach or neutral looks.

## Nails candidates

| Candidate | Visible difference to require | Proposed experiment | Reference |
|---|---|---|---|
| Raspberry Jelly | Translucency, not opaque red | Renderer alpha/transparency treatment | [Pinterest](https://newsroom.pinterest.com/news/beauty-trend-report-2026/) |
| Pink Aura Ombré | Color concentrated at the centre | Radial gradient in each nail mask | [Adore Beauty](https://www.adorebeauty.com.au/beautyiq/make-up/best-nail-art-trends/) |
| Negative-Space Micro-Dots | Sparse dots over visible nail | Pattern placement in per-nail coordinates | [OPI](https://www.opi.com/blog/nail-trends/now-trending-polka-dot-nails) |
| Milky Pearl Chrome | Pearlescent overlay, not ordinary gloss | New finish rendering/model comparison | [Adore Beauty](https://www.adorebeauty.com.au/beautyiq/make-up/best-nail-art-trends/) |
| Dark-Red Velvet Cat-Eye | A distinct luminous band | New finish rendering/model comparison | [Pinterest](https://newsroom.pinterest.com/news/beauty-trend-report-2026/), [Adore Beauty](https://www.adorebeauty.com.au/beautyiq/make-up/best-nail-art-trends/) |

All five are currently unsupported candidate IDs. Renderer routes are engineering proposals, not finished capabilities. Preserve the uploaded nail shape and length. Do not promise extensions, 3D charms, physical magnetic behavior or changing reflections from one still photo.

## Proposed first test order

Start with Butterfly, Two-Block and Comma Hair; Blurred Berry and Icy Silver Makeup; Raspberry Jelly, Pink Aura and Micro-Dots Nails. Then evaluate Wolf, French Bob, Manga Lashes, Pearl Chrome and Velvet Cat-Eye. The second group has greater overlap or fine-detail/finish challenges. This ordering is an engineering judgment, not a popularity ranking.

Keep the same foundation model and reviewed inference settings initially. Compare each candidate on the same input and seed with its nearest existing option. Record source/prompt/adapter hashes, output, elapsed time, peak memory and human review separately. Check identity, skin/background preservation and requested visual details. Do not describe a style as supported until real results pass review. Repeat approved old looks after the experimental sequence to check regression.

## Data collection and training boundary

Trend-page photos are **visual references**, not an approved training dataset. No images were downloaded and no reuse permissions are implied by the links. Prefer salon-owned consented examples or sources with explicitly recorded permissions.

For each real sample, record feature, proposed style ID, anonymized subject ID, source/target file and hash, origin/author, permission/license evidence, capture conditions, split and reviewer. Keep a subject entirely in one split and check duplicates. Matching source/target examples must represent the same subject where the existing edit-training method requires that pairing. Never pair unrelated people simply because one has the desired hairstyle.

Hair/Makeup prompt trials determine whether further data and fine-tuning are necessary. Nails renderer experiments require independently reviewed masks and visual examples; they do not themselves constitute new AI training. Final data counts and GPU time depend on the accepted shortlist and pilot quality; no unsupported minimum image count or runtime promise is made.

## Booking and price mapping

Proposed haircut mappings reuse Men's Cut and Women's Cut & Blowdry. Makeup reuses Makeup Application; its current catalog price is **Price to be confirmed**. Nails can reuse Classic Manicure or Gel Manicure with salon confirmation of any additional design charge. Existing Nail Art is charged per nail and must not be shown as a complete-manicure price. Do not copy a reference salon's prices.

These are proposed service mappings; local service availability and any style-specific surcharge still require the client's salon. Public style IDs, consultation tags, descriptions and saved-look/booking mapping will be added together after acceptance. Preserve old IDs and saved booking snapshots.

## Deliverables and next action

- Candidate metadata: data/style-expansion/STYLE-EXP-001/candidates.json.
- Empty image intake template: data/style-expansion/STYLE-EXP-001/image-intake.csv.
- Empty evaluation template: data/style-expansion/STYLE-EXP-001/evaluation.csv.
- Confirm/revise this researched shortlist, then source permissioned evaluation photos and run an isolated pilot. No live Render/Kaggle changes are part of this research stage.

Source dates are recorded where verified; undated brand pages are not presented as newly published in 2026. International trend reports are inspiration, not measured local customer preferences.


## First-batch pilot receipt, 25 October 2026

The recommended eight-style batch is approved for isolated testing.43focused tests, original GPU bundle and embedded-source preflight passed locally; three renderer prototypes were checked on a reused manual-mask hand with zero outside-mask changes. GPU inference is pending the separate Kaggle run. [Exact run guide](../guides/style-expansion-pilot.md). No training or production support is claimed.


## Current verified status after pilot and Makeup comparison, 25 October 2026

The first-batch GPU pilot is now complete; the earlier pending-GPU receipt is historical. See the [pilot review](../experiments/style-expansion-pilot-20261025-review.md). Comma and3Nail renderer directions still require varied-input/automatic-mask validation; Butterfly/Two-Block are held. Makeup guidance2.5is explicitly selected by the Supervisor after diagnostic comparison, but the new Makeup styles have not been validated at that setting and serving configuration remains unchanged. No new training data/weights or expanded public catalogs were delivered. Overall expansion remains IN PROGRESS. [Consolidated status](../experiments/style-expansion-status-20261025.md).


## First-release validation phase authorized, 25 October 2026

Supervisor approves proceeding. PreviousGPUended, so freshprivateSTYLE-VAL-001notebook nowreadyfor29portraitcalls. FourhistoricalNailvalidationhands havecompletedactualautomaticmask/refinementand12rendererlookswith0outside-maskchanges;clientappearanceacceptancepending.78localtestsandoriginalbundle/notebookpreflightpass. Integrationwaitsforactualcandidateacceptance; no publicstyle/contract/cloudchange. [Guide](../guides/style-release-validation.md), [integration map](../experiments/style-release-integration-map-20261025.md).


## Completed first-release GPU evidence, 25 October 2026

STYLE-VAL-00129callscomplete;prior4selectedMakeup2.5controls/finalrestore independentlymatch. ExistingMakeupselectedsetting remainschosen;newBerry/Icyneedclientreviewforpartialpromptfidelity. Comma isheldbasedon2suitable-inputfailures. ThreeNailpatterns haveactualautomaticmask/4handCPUevidence;clientvisualacceptancepending. Nextacceptedsubsetintegration ratherthanblanketshortlistenablement. [Review](../experiments/style-release-validation-20261025-review.md).


## Makeup correction gate after expanded validation, 25 October 2026

The user's explicit rejection of Berry for whitening holds new Makeup promotion. The selected guidance 2.5 remains a relative preference, not a preservation fix. The stricter 60-pair audit now has zero unchanged usable targets in the Codex screen; original files and historical approvals remain intact. Replacement-data research is complete but no source is accepted for training. Do not enable expanded Makeup IDs or repeat GPU sweeps while corrective targets are unresolved. Hair/Nails status remains independent. [Audit](../experiments/makeup-corrective-review-20261025.md), [replacement investigation](../research/makeup-replacement-datasets-20261025.md).


2026-10-25 replacement sample access is authorized but not complete: pinned BMS metadata/range probes passed, larger intake failed on network/DNS. No new image targets or corrected model; Makeup expansion remains held. [Concrete provider request](../research/makeup-data-access-request-20261025.md).


2026-10-25 existing-photo MAKEUP-TONE-001 prototype completed separately: partial white-cast improvement in4/6results,2guarded no-ops; not a complete naturalness fix or approved expanded Makeup rollout. Manual neutral-box sampling is not an automatic product capability. Await human review, then separately scope reliable automatic regions if useful. Current public IDs/models/Render/Kaggle unchanged. [Results](../experiments/makeup-tone-correction-20261025.md).


2026-10-26 Supervisor rejects shown tone-corrected Natural output as visibly masked/poorly blended. Current color correction is not accepted for shared Makeup or expanded styles; existing Makeup expansion hold remains. No deployed behavior changed. [Evidence](../experiments/makeup-tone-mask-rejection-20261026.json).


2026-10-26 method choice:Supervisor accepts AI-assisted cosmetic rendering for Makeup. Proposed recovery leaves original complexion intact and tests source-local lip/eye/blush profiles; it is not current MAKEUP-001 generation and must have truthful metadata/availability. Existing and expanded style labels require individual acceptance, no automatic catalog promotion. Proposed12output pilot precedes implementation integration/deployment. [Plan](../experiments/makeup-deployment-recovery-plan-20261026.md).


2026-10-26 approved AI-assisted source-rendering pilot implemented separately:3profiles x4existing originals=12previews. No whole-face reconstruction/whitening, no trainedMAKEUP001 inference.24technical tests/source invariants pass; RedLip edge/intensity and modest Natural/Soft effects require human acceptance. Current10stylecatalog/expandedstyles unchanged and not automatically supported by this3profile experiment. [Review](../experiments/makeup-source-render-pilot-20261026.md).


2026-10-26 approved existing-catalog extension DONE offline:No-Makeup/Smoky/Dewy/Rosy/Bronze/Matte/Evening generate28experimentalpreviews on4originals,12baselinecontrols unchanged. All10existingstyles haveofflineexamples; no publicsupport/promotion. Color/finishlimitations mustbereflectedinfuturedescriptions:localmatte/dewy/gold, nofalse-lashes/fullfacefoundation. ThreeexpandedMakeupcandidatesremainseparate.51focusedtests pass; actualappearanceacceptance/broadercoveragepending. [Review](../experiments/makeup-seven-styles-20261026.md).


2026-10-26 Supervisor reports inadequate non-lip Makeup visibility. Separate12case Soft/Smoky/Rosy revision strengthens eye/cheek layers with previous mouth pixels fixed.70focusedtests/12saved reproductions pass; appearance pending, Rosy strength/cheek subtlety unresolved. No serving/catalog/cloud changes or other-profile/expansion promotion. [Review](../experiments/makeup-visibility-20261026.md).


2026-10-27 human feedback does not accept MAKEUP-VISIBILITY-001 as sufficiently visible makeup. Hold appearance approval/integration; no further opacity-only sweep or automatic all-style promotion. Proposed next scope is one complete Soft Glam appearance target/small prototype, with actual eye/cheek/lip coordination and any new brow/lash anatomy/protection explicitly evaluated. No code/rendering/cloud change. [Evidence](../experiments/makeup-visibility-rejection-20261027.json).


2026-10-27 user supplies warm/glowy Soft Glam visual target. MAKEUP-COMPLETE-0014case offline prototype adds coordinated local layers but fails Codex realism review (procedural lashes/finish). Hold rollout/all-style expansion; proposed next anatomical alignment review precedes any further complete-look revision. No serving/cloud changes. [Evidence](../experiments/makeup-complete-look-20261027.md).


2026-10-30 authorized alignment/one-style4case correction DONE offline.106focusedchecks/4exactoutputs pass; appearance still fails (procedural lashes/finish), so agreed method reassessment is reached. No all-style promotion/deployment. Read-only Stable-Makeup source audit finds entry/dependency/asset/memory gates; candidate remains proposed/unexecuted, no replacement adopted. [Experiment](../experiments/makeup-alignment-20261030.md), [next feasibility plan](../research/makeup-method-reassessment-20261030.md).

2026-10-30 deadline update:within24hours/freeonly. No paidAPI/training/customstrokesweep. Proposed single bounded isolated reference-transfer feasibility trial after assetspreflight; expansion/release still held, honest demo limitation if it fails. [Constraints](../experiments/makeup-deadline-triage-20261030.json).


2026-10-30 singlefree pretrained reference-transfer trial preparationDONE; four CPU controls+private3.77MBinput+two-cell notebook ready,23newchecks pass. Actual T4 loading/generation/appearance NOT STARTED; noacceptednewstyle/service replacement. Separate evaluation uses ownenvironment/watchdog/resultZIP and leaves demo untouched. [Run guide](../guides/stable-makeup-trial.md), [receipt](../experiments/stable-makeup-trial-20261030.json).


2026-10-30 free pretrained trial completes4outputs in4.42min, proving standaloneT4runtime. Visual source-face preservation fails; no style/service promotion or new automatic experiment. Preserve demo and deadline fallback. [Review](../experiments/stable-makeup-trial-20261030-review.md).

2026-10-30 Supervisor explicitly rejects Stable-Makeup output and resets scope to the original excessive whiteness problem. Replacement/full-look experiments are not the current path; no deployment. Any next correction must target original Makeup white cast while preserving person, visible cosmetics and natural transitions, accounting for the prior masked-tone failure. [Decision](../experiments/makeup-scope-reset-20261030.json).


## Expansion release readiness clarified, 2026-10-30

Supervisor asks why the Hair, Makeup and Nails expansion has not deployed while Makeup remains defective. Read-only audit confirms tested candidates have not been wired into production catalogs/routes or packaged for release. Three Nails renderer candidates (Raspberry Jelly, Pink Aura Ombre, Negative-Space Micro-Dots) have 12 automatic-mask validation outputs across four reused hands; source-preservation checks passed, but client appearance/edge acceptance is not recorded. They are candidates for an independent partial release, not live features. New Hair candidates remain held or untested: later release validation holds Comma despite its earlier promising pilot; Butterfly and Two-Block need suitable-input retests; Wolf and French Bob were not tested. Expanded Makeup remains held after user rejection, and the current correction scope remains the original white-cast problem, not replacement-model experiments. Recommended sequencing is to select visually accepted Nails, complete catalog/consultation/renderer integration and matching release bundles, then rehearse before rollout independently of Makeup. This recommendation is not approval of the appearance of any candidate or evidence of deployment. No code, model, cloud, GPU, or production data changes in this audit. Evidence: docs/experiments/style-release-validation-20261025-review.md and docs/experiments/style-release-integration-map-20261025.md.


## Full expansion target selected; release remains gated, 2026-10-30

**CONFIRMED scope:** Supervisor wants all proposed Hair, Nails and Makeup expansion styles considered for use, with Makeup tested before rollout. This selects the target scope; it does not establish that previously failed or untested styles work or approve rejected appearances. Existing catalogs remain intact. **IN PROGRESS / NEEDS VERIFICATION:** complete per-style validation, compatible production catalog/consultation/renderer/model-profile integration, actual service-price mapping, save/book regressions, matching versioned Kaggle packages and application rehearsal. Makeup remains on the original white-cast correction scope. No blanket production enablement, new training or replacement-model adoption is inferred. Current expanded release is not deployment-ready; no production changes made by this clarification.


2026-10-30 first release milestone implemented locally: manifest/capability gate and three new renderer paths verified, but0newstylesenabled pending user image review. Original12Nailoutputs reproduce exactly; fullbackend773/application108/typecheck/build pass. GPU/Makeup contracts, notebooks and live system unchanged. Packaging/rehearsal and remaining candidates still pending. See [evidence](../experiments/expanded-style-milestone1-20261030.md).


## Three Nail additions accepted and packaged — 30 October 2026

Supervisor approves the repaired review gallery. Raspberry Jelly, Pink Aura Ombré and Negative-Space Micro-Dots are accepted/enabled in the local manifest and generated metadata. Eight Nail styles are now configured locally. New immutable CPU input and a separate optimized Kaggle starter are prepared with matching capability checks; original GPU/model settings and fallback notebooks remain intact. Cloud rehearsal/rollout is still pending. The remaining ten candidates and unresolved Makeup white cast are not promoted. See [release guide](../guides/expanded-nails-release-20261030.md) and [approval record](../experiments/expanded-nails-approval-20261030.json).


## French Bob approved and integrated locally — 31 October 2026

Supervisor approves French Bob, the sole candidate singled out for review. Exact HAIR-EXP-002 prompt/TRAIN-001/settings are now an additional inference profile with truthful provenance and original training-label/checkpoint guards preserved. Four other Hair candidates stay held. Combined Hair/Nails release preparation retains the prior Nail-only package as fallback. Local metadata now14Hair/10Makeup/8Nails. Existing Makeup limitations remain. Cloud rehearsal/deployment still pending. [Guide](../guides/hair-nails-release-20261031.md).
