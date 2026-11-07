# Evaluation

Source: Supervisor's CODEX HANDOFF 001. Comparison design: CONFIRMED intent; results and thresholds: UNKNOWN.

Use the same held-out inputs and hairstyle requests for three conditions:

1. BASE: plain pretrained FLUX.2 Klein.
2. CUSTOM: FLUX.2 Klein plus the project-trained hairstyle Edit-LoRA.
3. HYBRID: CUSTOM draft followed by plain pretrained refinement.

Assess hairstyle match, identity and face preservation, realism, unwanted non-hair edits, artifacts, reliability, and inference time where relevant. Record prompts, seeds, versions, settings, hardware, images, and judging method so the comparison is reproducible. A claim that the LoRA contributes meaningfully needs direct BASE versus CUSTOM evidence; a HYBRID image alone is insufficient. Report a lack of improvement honestly.

Acceptance thresholds, metrics, evaluator, sample size, and scores are UNKNOWN. Actual experiment records belong in `docs/experiments/`, with only evidence-backed conclusions summarized here.


## STYLE-EXP-001 completed pilot, 2026-10-25

**VERIFIED from supplied archive:**15portrait outputs/prompt-adapter provenance, original input pixels, one foundation and both restoration pixel matches; three manual-mask Nail outputs independently have zero outside-mask pixel changes. Visual AI review, not human/salon acceptance: new Comma shape promising, Butterfly/Two-Block inconclusive or weak on short frontal input; Makeup adds intended colors but substantial complexion lightening/smoothing and excess pigment. Existing Makeup controls exhibit similar preservation issues; include baseline controls in future quality review. Trials remain single-input worker observations, not new independent generalization tests or application speed measurements. Source figures and exact limits: docs/experiments/style-expansion-pilot-20261025-review.md.


2026-10-25 Makeup quality concern: raw outputs and original target sheets visibly show complexion/texture drift; source/target hashes and50/10pairs across10/2people verified. Treat current retouched outputs as unaccepted correction targets. Proposed12case matched foundation/adapter-influence diagnostic is not run; causal contribution and corrective settings remain unknown. Skin metrics need aligned reviewed regions/calibrated thresholds; reused validation subjects require a separate untouched final test. See docs/experiments/makeup-complexion-audit-20261025.md.


2026-10-25 MAKEUP-QA-001 prepared:12matched conditions on reused2validation subjects, Natural/Red Lip, Base/adapter1.0/adapter0.5. Record effective per-layer scale, tensors, original source/output hashes and fixed settings; restore full state after weighted groups. SyntheticCPU tests and artifact checks pass but no corrective image/skin-quality evidence yet. Full-state restoration is not an added image-equivalence check. New final test people required after diagnostic tuning. [Guide](../docs/guides/makeup-quality-diagnostic.md).


2026-10-25 MAKEUP-QA-001 failure boundary VERIFIED from supplied child log: after8outputs, full-scale restoration fails because PEFT reactivates an inference tensor. Local real-Torch reproduction confirms context restriction; no_grad correction and guarded continuation ready. Eight output images themselves have not been supplied/reviewed. Continuation requires one identical current control, then4reduced outputs, preserving original partial report. Do not claim reduced influence improves complexion or assume control will match before GPU execution. [Evidence](../docs/experiments/makeup-quality-inference-recovery-20261025.json).


2026-10-25 MAKEUP-QA-001 GPU comparison VERIFIED and visually reviewed:0.5does not resolve complexion lightening/smoothing on2reused subjects x2old styles. Base also over-edits Natural/brows/cheeks; Red Lip Base closer to source complexion but unaccepted saturation/geometry. Current adapter increases retouched/lightened appearance on these fixed cases; dataset contribution is not isolated. One current control pixel-identical across inference contexts; no claim all4were rerun. Hold all corrective setting promotion; require reviewed preserved targets/untouched final people for later candidate evaluation. No standardized skin/identity score or human/salon acceptance. [Review](../docs/experiments/makeup-quality-diagnostic-20261025-review.md).


2026-10-25 MAKEUP-QA-002 prepared after Supervisor approval: compare current1.0/guidance4 original against1.0/guidance3 original and1.0/guidance4 +foundation-specific instructions. Reuse4current examples, require one pixel-identical continuity control, then8candidates. Visual acceptance needs visible requested cosmetics together with source complexion/texture/geometry preservation; no numeric score or weakening-only success.85local focused tests pass; actual GPU candidate outputs pending. [Guide](../docs/guides/makeup-adjustment-comparison.md).


2026-10-25 MAKEUP-QA-002 completed visual review:guidance3 and added complexion/foundation instruction both retain pale smoothed faces/heavy styling on2reused people x2styles; makeup is clearly visible, preservation still fails.8candidate files differ from references but no quality setting accepted. Exact continuity control and original4controls verified. Hold production promotion and unbounded settings sweeps; corrected-target curation/fine-tuning planning proposed, not performed. Base itself also over-edits; no guaranteed retraining outcome or generalized all-user claim. [Review](../docs/experiments/makeup-adjustment-20261025-review.md).


2026-10-25 Supervisor visual preference: guidance3.0 looks relatively more natural than matched-foundation text in supplied crop; distinguish that improvement from fixing source-complexion drift. Authorized QA-003 tests2.5against retained3.0/4.0at fixed original prompts/full adapter. One3.0control must match pixels;4candidate cases remain GPU-pending.15new/100focused tests pass locally. Accept only visible intended makeup AND complexion/texture/face preservation; no next parameter sweep or final release acceptance inferred. [Guide](../docs/guides/makeup-guidance-25-comparison.md).


2026-10-25 MAKEUP-QA-003 reviewed:2.5keeps visible Natural/RedLip cosmetics, but closely resembles3.0and does not consistently restore complexion/texture across2reused people x2styles. Human relative preference3.0overmatched-foundation remains; no clear overall2.5winner, numeric quality rank or salon release acceptance. Bounded guidance test complete; no automatic next sweep. Corrected-target curation/planning remains proposed; Base reconstruction limitations still apply. [Review](../docs/experiments/makeup-guidance-25-20261025-review.md).


2026-10-25 human follow-up CONFIRMED: Supervisor prefers latest guidance2.5output to3.0and reports it looks much better. Record this as selected visual candidate, superseding provisional3.0preference; retain independent artifact checks and small-sample complexion/texture limitations. Selection is not an all-user quality claim and no live setting changed. [Evidence](../docs/experiments/makeup-guidance-selection-20261025.json).


2026-10-25 firstreleasevalidation stage:4reusedNailsvalidationhands run actualautomatic5nailmasks/refinement,3patterns=12outputs with independently0outside-refined-maskchanges and5editedcomponents each. Sheet/fullresreview shows distinctfinishes, but masktrueboundary/appearance requireclientreview; no calibratedmanualgroundtruth or variedcapturegeneralization claim. Fresh29callportraitcheck pending across all10existingMakeup+2newatselected2.5 and2Hairvalidationinputs/Commaat4.0, prior4controls/finalrestore. No newtraining/untouchedsubjects. [Evidence](../docs/experiments/style-release-validation-20261025.json).


2026-10-25 STYLE-VAL-001review:all10existingMakeupatselected2.5executeon2developmentpeople;4priorcontrols pixel/byte-identical. Recognizablepresetcolordirections but No-Makeuptooheavy/Mattehighlighted and knowncomplexiondriftpersist;explicituser2.5selectionretained. Berry/Icydistinct but blurred/subtle-lipclaimsnotfullysupported;clientreviewneeded. NewCommaheld duegraphicforeheadloopandweakdistinctshapevsCurtainon2suitablehistoricalinputs. No numericmetric/generalization/salonacceptanceclaimed. [Review](../docs/experiments/style-release-validation-20261025-review.md).


2026-10-25 Supervisor rejects newBerry2.5output as unnatural/too white/poorlyblended. This supersedes pending visual acceptance forBerry; no extrapolation from preferredexisting2.5Natural/Redtoallstyles. HoldnewMakeuppromotion; retouchedtargetaudit+Baseoverediting inform next concrete targetreview, not a guaranteed trainingfix or furtherguidancesweep. [Evidence](../docs/experiments/makeup-berry-quality-rejection-20261025.json).


## Makeup corrective screen, 2026-10-25

**Coverage/integrity VERIFIED; qualitative findings EXPERIMENTAL.** All 60 frozen targets screened against complexion/texture/identity/scene preservation; 0 KEEP / 60 REJECT for unchanged corrective reuse, with specific reasons in the separate ledger. Twelve identity sheets and five native-resolution checks viewed. Human/salon acceptance remains pending; historical broad pair ACCEPT decisions are preserved. No measured quality score, full-upstream rejection or causal claim. Foundation-only drift remains a separate limitation. No replacement source yet verified for pairing + quality + applicable permissions. [Audit](../docs/experiments/makeup-corrective-review-20261025.md), [research](../docs/research/makeup-replacement-datasets-20261025.md).


2026-10-25 MAKEUP-TONE-001 DONE offline:6cases,4adjusted/2unchanged by guard. V1 fails pale rectangular orbital patches; boundary-only v2 removes boxes and partially reduces whitening on darker subject. Protected RGB/outside-mask invariants independently0changed, input/provenance pins intact;32focusedpass. Fitted patch gaps are not independent skin-quality accuracy. Heavy blush/texture/geometry and residual transition/undertone remain;0humanaccepted, no release readiness or untouched test population. User review of actual comparisons is next. [Review](../docs/experiments/makeup-tone-correction-20261025.md).


2026-10-26 human visual REJECT for MAKEUP-TONE-001 v2 054109Natural: visible mask and poor blending. Native raw/corrected comparison shows pre-existing retouching and residual pale brow/mouth zones against warmer adjusted skin. Exact protected pixels/forehead fit remain technically valid but fail to establish acceptable appearance. Hold this route for release; no further image changes or tests run for this feedback-only record. [Evidence](../docs/experiments/makeup-tone-mask-rejection-20261026.json).


2026-10-26 MAKEUP-RENDER-001 pilot DONE:4existingdevelopmentpeople x3profiles=12outputs, no newGPUgeneration/training. Automatic source regions reviewed; initial pigment clipping corrected once with unchanged masks/opacities and preserved original version.24focused tests and independent12PNG invariants/reproduction pass. Source preservation promising; Natural/Soft eye/cheek effects modest, RedLip strong/possibly painted and lip edge fit needs user/salon appearance review.0humanaccepted, no deployment or all10style/generalization claim. [Review](../docs/experiments/makeup-source-render-pilot-20261026.md).


2026-10-26 MAKEUP-RENDER-002 DONE offline:7remainingexistingstyles x4reused originals=28newpreviews, plus12retainedpixel-identicalbaseline examples.51tests/independent28PNGchecks pass,0outside/protected changes. All4region/result sheets and2native-detail sheets reviewed. Source preservation promising; style visibility/fidelity varies and lipmask/intensity stillneedsactualhumanreview. Local matte/dewy/gold doesnot establishfull-facefinish/false-lashsupport.0humanaccepted, noall10release-readiness/generalization claim. [Evidence](../docs/experiments/makeup-seven-styles-20261026.md).


## Non-lip visibility comparison, 2026-10-26

**Technical VERIFIED; appearance EXPERIMENTAL:**12outputs/4reusedportraits;19new+51regression=70pass,12exact reproductions,0mouth/protected/outsideallowed changes. Previous mouth fixed to isolate eye/cheek changes. Codex sees stronger eyes, restrained cheeks, potentially excessive Rosy crease saturation. No human ACCEPT/all-input claim. Local color distances do not score realism. [Review](../docs/experiments/makeup-visibility-20261026.md).


## Makeup visibility comparison not accepted, 2026-10-27

**CONFIRMED user feedback:** latest source-rendered comparison still does not look sufficiently made up. MAKEUP-VISIBILITY-001 is not accepted as a solution; no per-case judgments inferred. Historical70technicalchecks/12exactreproductions do not prove appearance quality. Inspected current code implements localized pigment/darkening/finish; brows remain protected, full lash/foundation/contour capability is absent. Missing components are verified; their causal contribution to this rejection is not.

**PROPOSED / NOT STARTED:** stop opacity-only sweeps. Establish an explicit visual target, ideally a user reference, then one complete Soft Glam prototype with shaped lid shading, defined lash line and coordinated cheek/lip effects. Brow/lash details require deliberate anatomy/protection review, not drawing over protected regions blindly. Preserve source complexion/identity. Validate a small comparison before all-style expansion or versioned integration. No new images, rendering code, dependencies, inference, training or cloud changes this turn. Current output is not release-ready. [Rejection](../docs/experiments/makeup-visibility-rejection-20261027.json).


## Complete-look visual failure, 2026-10-27

MAKEUP-COMPLETE-0014source previews match frozen runner and preserve protected/outside pixels. All4sheets visually inspected: drawn-on regular lash strokes/placement, incomplete whole-look finish, potentially painted lips. **Codex visual REJECT; zero human ACCEPT.** User supplied reference defines the desired direction but did not approve candidate images. Technical success is not aesthetic acceptance. Do not expand/deploy this candidate. [Review](../docs/experiments/makeup-complete-look-20261027.md).


## MAKEUP-ALIGN-001, 2026-10-30

**Technical VERIFIED / appearance EXPERIMENTAL, rejected by Codex for release.** 4localpretrained CPUdetections and4rendered comparisons,20new+86prior=106pass.4actualPNGs exactreproductions,0outside/protected/eye-interior changes, explicit narrow semantic eye-rim edits43/28/0/71. All4overlays/comparisons inspected. Finer roots help placement; procedural lashes still artificial, fullreferencefinish missing. No human ACCEPT or detector generalization claim. Reassess method; do not repeat strength sweeps. [Evidence](../docs/experiments/makeup-alignment-20261030.md).


## STABLE-MAKEUP-001 return, 2026-10-30

**Runtime VERIFIED; appearance EXPERIMENTAL / Codex rejects release.** Four actual T4 images at10.29–12.24seconds, standalone4.91GiBpeakreserved;265.04secondtotal. All32archiveentriesCRC/frozenplan/source/control/reference/output/assetreceipt checks pass. Fullmakeupvisible, but substantial source-face/expression/complexion changes in all4qualitative comparisons. No human acceptance or calibrated identity score, no simultaneous Hair/Nails fit claim, no direct quality-equivalent speedup claim. [Evidence](../docs/experiments/stable-makeup-trial-20261030-review.md).


## Supervisor resets Makeup scope to original white-cast problem, 2026-10-30

**CONFIRMED correction and human rejection:** Supervisor says latest result looks worse and asks why work drifted from initial whiteness issue. Original goal remains reducing excessive pale/white skin in existing BeautyCore Makeup while retaining visible cosmetics and the same person. Codex acknowledges scope drift into replacement rendering/full-face reference generation. STABLE-MAKEUP-001 is now explicitly human-rejected, not only a Codex rejection.

Stop the replacement/full-look expansion branch under the current task. Return to original deployed pipeline and accumulated diagnostic evidence before proposing a targeted white-cast correction. Do not restart GPU/parameter/model/training sweeps or deploy rejected candidates. Earlier skin-only MAKEUP-TONE-001 correction also failed with a visible mask; it is not a valid accepted fallback. No accepted fix exists yet, and no promise of a safe single-setting solution is justified. No code/images/GPU/deployment change in this reset. [Scope reset](../docs/experiments/makeup-scope-reset-20261030.json).


## MAKEUP-EXP-002 result, 2026-10-31

**Technical VERIFIED; appearance EXPERIMENTAL; Codex white-cast goal FAIL; human acceptance NOT RECORDED.** Three actual T4 calls/six retained outputs verified against frozen plan/source/fixtures/PNG/RGB/prompt/environment/model-index. Soft Glam control exact PNG/RGB. Two Manga outputs show separated lashes and pink cosmetics but strong complexion/texture/facial detail changes. Coverage complete for three expanded styles on two reused portraits, not quality/generalization proof or whitening fix. Timings62.81/62.23/63.96seconds,189.00total; load43.96; max allocated8304.31MiB. Trusted embedded gallery10images/browser checks pass. No serving/deployment change. [Review](../docs/experiments/makeup-expansion-results-20261031-review.md).


## Source-referenced complexion pilot, 2026-11-01

**Technical VERIFIED / appearance EXPERIMENTAL / no human acceptance.** One revised spatial field on ten saved images from two repeated subjects: four current-guidance4.0 and six earlier2.5. White cast visibly reduced with visible cosmetics; possible excess warmth, lip/brow color shifts and residual edge transitions remain. Existing smoothing/geometry not fixed.23tests/tenexactRGBreproductions;30imageEdgegallery/mobile/viewer/noJSerrorspass. Numeric fitting is not independent skin-tone accuracy. Failed boundary-only and hard-island versions preserved. No new diffusion/training/photos/deployment. [Review](../docs/experiments/makeup-complexion-20261101.md).


## MAKEUP-FAITHFUL-001, 2026-11-01

**Superseded interpretation / later human rejection:** Source-only subtlety removed the required makeup. Preserve original person AND selected makeup together; see the latest correction below.

**Technical VERIFIED; appearance EXPERIMENTAL.** New user brief favors source-photo subtlety. Two reused512square originals remain canvas; previous corrected AI face contributes low-frequency color only.18checks/twoexactreproductions; original protected/nonprimaryRGB0changes; maxRGB4/3andluma0.484code. Source texture/features/expression visually retained; change intentionally faint. Native/toggle/mobilegalleryverified. This is not universal identity/professional-quality proof or all-Makeup style acceptance. [Review](../docs/experiments/makeup-source-faithful-20261101.md).

## MAKEUP-LAYERS-001 and corrected acceptance, 2026-11-01

**Technical VERIFIED; appearance EXPERIMENTAL_FAILED / Codex REJECT.** V3 all-three-reference/two-person matrix has six exact RGB reproductions, verified input/landmark provenance and zero changes outside allowed source regions; nine serving/release hashes unchanged. Native comparisons show colored cheek patches, cutout transitions and incomplete eye makeup. V1/v2 also rejected, preserved separately. Parameter strength 1.0 is not preserved appearance. No user approval inferred.

MAKEUP-FAITHFUL-001 is now explicitly HUMAN-REJECTED for removing selected makeup; earlier technical passes remain factual but do not satisfy the requirement. Original-person fidelity and selected cosmetic preservation must pass together. No Makeup release readiness. [Evidence](../docs/experiments/makeup-selected-cosmetics-20261101.md).

## MAKEUP-SEPARATION-001, 2026-11-01

**Technical VERIFIED; appearance EXPERIMENTAL; release HOLD.** Six final v2.1 comparisons inspected: previous cyan patches and broad dark eye plates removed, original person/visible texture retained, lipstick/eye/cheek edits remain. Lash density/shape, brow fill and blush strength are not exact selected-reference matches.19focusedchecks/sixexactRGBreproductions pass, including actual pale-highlight rejection and a five-pixel Lab-round-trip no-op regression. Original eye cores and other protected areas remain exact.48imageembeddedgallery/viewer/toggles/masks/mobile390/noJSerrorspass. Two reused people only; no all-style, calibrated skin accuracy or new end-to-end speed claim. Nine serving/release hashes unchanged. [Evidence](../docs/experiments/makeup-separation-20261101.md).

## MAKEUP-REFERENCE-001 v4.1, 2026-11-01

**Technical VERIFIED; appearance EXPERIMENTAL; human acceptance pending.** Six native fixed-reference comparisons show more visible cosmetic color than the rejected-as-too-subtle prior version. Blush reference chroma error decreases in all six (diagnostic only); source cheek lightness stays nearly original. Actual lash detail separated from shadow; source eye core protected; brows cannot brighten; lip RGB equals prior in all six.34checks(15new+19prior)/sixlatestexactRGBreproductions pass. Dedicated seven-pixel warp-padding no-op regression fixed.54embeddedimagegallery/viewer/toggle/masks/mobile390/noJSerrorspass. Darker-source plum appearance, lash/brow fidelity and lip edges remain review limits. No universal/calibrated/all-style or deployment pass. [Evidence](../docs/experiments/makeup-reference-visibility-20261101.md).


## Makeup boundary and realism audit, 2026-11-02

**VERIFIED audit / REJECTED current appearance.** Six stored comparisons reviewed. Source protected pixel equality remains true, but brow edits violate the newest explicit preservation requirement. Source lip parser versus landmark IoU0.7280/0.6915 is an uncertainty diagnostic, not ground truth or an appearance score. Copying reference lip lightness and matching selected chroma did not produce acceptable natural makeup. Historical34checks did not test those perceptual requirements. Thirty nine hashes rechecked unchanged; no new corrected images or model calls. Next bounded gate is lip contour/pigment proof before cheeks/eyes and broader acceptance. [Audit](../docs/experiments/makeup-realism-audit-20261102.md).


## Source lip component and failed full proof, 2026-11-02

**VERIFIED component checks / EXPERIMENTAL lip appearance / REJECTED full Makeup.**51tests pass in13.86seconds (17new,34prior), six frozen lip outputs reproduce, source eyes/brows/all nonlip pixels stay exact, interior lightness gradients remain within0.7Lab rounding range. Identical originals on two portraits are exact no change; permutation of reference lip texture has no effect. These are not full look quality scores. All six combined pigment probes inspected and rejected for orange cheek patches and poor eye style fidelity. Full function removed from retained code, failed snapshot remains.36embeddedgallerypanels/native512viewer/toggle/mobile390/noJSerrorspass.39prior hashes remain unchanged. No Kaggle or full request memory/time check. [Evidence](../docs/experiments/makeup-source-surface-20261102.md).


## Retained lip result reviewed, 2026-11-03

**VERIFIED source protection / CONFIRMED positive direction feedback on lip only / full appearance scope limited.** All six saved lip results inspected against originals. Seventeen focused tests pass in 6.93 seconds; zero source skin/eye/brow/mouth interior changes and unchanged output hashes. Fully covered lip lightness offset range is at most 0.4761 Lab units, a source contrast diagnostic, not a realism score. Forty two prior hashes remain unchanged. Twenty four panel original/current gallery loads fully and passes native viewer, mobile 390 pixel layout and zero script errors. No new rendering or model call. Conservative lip edge coverage and deep red shade accuracy remain unresolved. No new safe refinement established. [Review](../docs/experiments/makeup-retained-review-20261103.md).


## Automatic Makeup material cycle, 2026-11-04

**VERIFIED bounded technical checks / EXPERIMENTAL appearance / release HOLD.** All52originalsupport/protectedsemanticchecks,4actualneuralidenticalreferencecontrols andfullcatalogcacheindependencepass.95focused+27unchangedruntime=122tests pass. All13outputhashesdiffer per person, proving variation only.182imagegalleryfilters/nativeviewer/desktop/mobile390/0pageerrorspass. Full photos/catalog/native eye/lip sheets show original complexion/geometry/texture retained compared with pale reconstructed guides; final selected pigment directions remove initial gray skin patches and anatomical fade reduces orbital plate edges. Some subtle styles remain close; metallic/finish effects and Manga clusters are not reproduced, and lip edges/shades remain imperfect. No all style quality, biometric identity, untouched generalization, training readiness or application performance claim. Original preferred lip function and40priorinput/servingreleasehashes unchanged. [Review](../docs/experiments/makeup-automatic-correction-20261104.md).


## Corrective MAKEUP model and application milestone, 6 November 2026

VERIFIED: completed 250 step corrective adapter, compared with Base on both reused development validation people across all 13 styles, with matched original/caption/settings. Engineering observes reduced whitening/reconstruction and visible complete cosmetics, with residual subtle style/lash/finish limits. Supervisor accepts all 26 actual model cases for application validation; every review binding is verified. This does not establish untouched generalization. The forehead diagnostic supports reduced lightening, not identity/texture/undertone proof.

All 62 regressions and actual staged CPU application/API transport checks pass. Real GPU application, fresh upload, website/save/book/mobile and production acceptance remain unverified. [Full evidence](../docs/experiments/makeup-corrective-model-results-20261106.md).


## Real corrective application return, 6 November 2026

VERIFIED: 13 authenticated application Makeup generations are independently byte-equal to the corresponding previously accepted RAW model PNGs, with exact original/caption/model/settings bindings. Active tensors verify on all 16 requests spanning Makeup, Hair TRAIN-001/TRAIN-002 and a Nails crop; one foundation remains ready. Engineering inspects returned catalog and Hair/Nails sheets. No further review of those same Makeup pixels is required. Fresh identity, live website/consultation/save/book/mobile and full hand Nails remain unverified.

The new release metadata around unchanged tested generation code passes actual archive/overlay/API staging, 25 staged Makeup runtime/API tests, five Render capability/business tests and profile corruption guards. No live rollout claim. [Evidence](../docs/experiments/makeup-corrective-application-results-20261106.md).


## Actual web deployment, 6 November 2026

VERIFIED: approved release applied/published at578330d and matching Render deployment Live.25Makeup,56release/Hair/shared-worker/startup,33Render and55business tests plus typecheck/build pass locally. Public health200 and anonymousAI401 pass independently. These checks do not establish authenticated live Makeup generation. Kaggle remains signed out in connected browser, no new serving registration. Next authenticate and connect final notebook, then fresh portrait/manual/consultation/save/book/full hand/mobile acceptance. [Evidence](../docs/experiments/makeup-corrective-deployment-20261106.md).
