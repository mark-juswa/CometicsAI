# AI/ML

Source: Supervisor's CODEX HANDOFF 001, EXP-001, and reported TRAIN-001 execution. Intended method decision: CONFIRMED; T4 training mechanics and 250-step completion: VERIFIED; hairstyle quality: UNKNOWN.

The custom contribution is a domain-adapted hairstyle image-editing model: pretrained FLUX.2 Klein 4B plus hairstyle Edit-LoRA parameters trained by this project. It must generate a transformed image, rather than only labels, scores, or prompts. The intended training task is paired image editing from an original or altered hairstyle to a desired one, with an instruction to preserve identity and non-hair regions.

At inference, compare plain pretrained generation, generation with the project LoRA, and the custom draft followed by plain pretrained refinement. The second stage is intended to improve appearance without removing the first stage's hairstyle change.

The [EXP-001 smoke test](../docs/experiments/EXP-001.md) verified Base image-edit inference, 20 finite-loss BF16 Edit-LoRA steps on one Kaggle T4, checkpoint serialization, and a fresh Base adapter load. FP16 produced NaN loss. The Supervisor's [TRAIN-001 run](../docs/experiments/TRAIN-001.md) then completed 250 finite-loss steps on DATA-001 with one conditional LoRA and saved final/intermediate adapters and optimizer state. The held-out 12-pair visual review found some hairstyle changes but unreliable face preservation and limited improvement over Base, so the checkpoint is not demo-ready. A hair-region image-composite probe on existing outputs is prepared to test a minimal preservation fix without retraining. Base-trained adapter compatibility with distilled Klein, multi-image refinement, and free deployment remain NEEDS VERIFICATION and are outside the current critical path.

For Makeup, the 2026-09-26 Supervisor decision is one general bare-to-makeup edit LoRA, trained on reviewed real FFHQ-Makeup pairs without artificial style classes. Ten application styles are fixed inference prompt presets, so prompt responsiveness remains NEEDS VERIFICATION after training. DATA-M001 is finalized at 50 TRAIN and 10 held-out VALIDATION pairs. An isolated 250-step BF16 T4 runner based on the proven Hair training settings is prepared, but MAKEUP-001 training, checkpoint quality and Base comparison are NOT STARTED. See [training handoff](../docs/experiments/MAKEUP-001-plan.md).

For Nails, the 2026-09-27 Supervisor decision freezes further training and uses a hybrid try-on system. `NAILS-001-LOCAL-v1` step 50 is the production-selected custom FLUX.2 Klein edit LoRA for Classic Red and Glossy Black only. Nude Pink, French Tip and Pink Ombre use deterministic rendering from the approved DATA-N001 logic. The same final nail-only compositor preserves the original hand outside the mask for every style. The adapter artifact and earlier held-out Red/Black evidence are verified; new live GPU serving and full five-nail requests remain NEEDS VERIFICATION. See [hybrid integration](../docs/experiments/NAILS-001-hybrid-integration.md).


## AI-assisted Makeup renderer experiment, 2026-10-26

Supervisor accepts AI-assisted rendering as an alternative method. Offline MAKEUP-RENDER-001 now combines pretrained SegFormer facial parsing with project-coded source-coordinate cosmetic profiles, without inference from MAKEUP-001 or a replacement generated face. All12outputs carry non-LoRA/generator metadata. Source preservation technical checks pass; cosmetic realism and coverage remain EXPERIMENTAL/human pending. Production still uses its existing trained model path. Do not describe the new renderer as a newly trained generative model or replace historical model contribution claims silently. [Evidence](../docs/experiments/makeup-source-render-pilot-20261026.md).


2026-10-26 MAKEUP-RENDER-002 source-based rendering nowprovidesexperimental7additionalexistingprofiles,40examplesacrossall10withbaselinecontrols. Fourcachedpretrainedsourceparsemaps reused; no newAIinference, trainedweights or datasets in this extension. Profileeffectsarecustomdeterministiccolor/finishlogic, notMAKEUP001generativeinference. Local matte/dewy/gold and lower-eye effects have recordedfidelitylimits; no full-facefoundation orfalse-lashsupport, nohumanreleaseacceptance. Productionmodelpath unchanged. [Evidence](../docs/experiments/makeup-seven-styles-20261026.md).


## External pretrained Makeup feasibility trial, 2026-10-30

STABLE-MAKEUP-001 is an authorized isolated evaluation, not a replacement trained adapter. Author Stable-Makeup combines SD1.5, learned makeup encoder and two ControlNets; pinned author checkpoints will be strictly loaded. Four source controls are actually precomputed onCPU via author SPIGA/RetinaFace. Newgeneration test will use one suppliedreference, FP16/T4,30steps,guidance1.6,seed1977; those are separate from BeautyCore's current FLUX/MAKEUP001 contract. Local preparation/import/key/integrity checks pass, but no newGPU makeup images or quality acceptance yet. No newly trained project weights or deployment change. [Trial](../docs/experiments/stable-makeup-trial-20261030.json).


2026-10-30 STABLE-MAKEUP-001 actualGPUevaluation DONE: externally pretrained SD1.5/learnedmakeup+2ControlNets works on T4/FP16,4visible-makeup outputs. Faces/expressions/skinfinish substantially change; Codex rejects release, zerohumanacceptances. This is not source-preserving virtual try-on or a newly trained BeautyCore model. Existing serving path unchanged. [Review](../docs/experiments/stable-makeup-trial-20261030-review.md).

## Selected Makeup reference separation, 2026-11-01

MAKEUP-LAYERS-001 is an offline project-coded transfer experiment, not new training or a replacement generative model. Cached pretrained MediaPipe detections align the selected reference only; original source remains the canvas. The parser has facial semantic classes but no ground-truth foundation/blush/eyeshadow/lash layers. Six v3 outputs fail cosmetic fidelity and natural blending despite original protected-pixel checks passing. No serving path changed. The source-only subtle retouch is user-rejected for removing makeup. [Evidence](../docs/experiments/makeup-selected-cosmetics-20261101.md).

## Incremental cosmetic separation repair, 2026-11-01

MAKEUP-SEPARATION-001 v2.1 is a local deterministic post-processing experiment using existing source and selected model outputs, not new model training or generation. Signed incremental Lab pigment replaces erroneous RGB ratios; local contrast/soft transitions and an original eye rim separate cosmetic detail from complexion. No new pretrained model inference occurred. Six outputs preserve visible original person and avoid previous cyan/eye-plate failures, but selected lash/brow/blush appearance is only partial. No current production model/output claim changed. [Evidence](../docs/experiments/makeup-separation-20261101.md).

## Reference color and visibility refinement, 2026-11-01

MAKEUP-REFERENCE-001 v4.1 is project-coded offline post-processing of existing selected Makeup outputs, with original photo as canvas. It uses selected cosmetic chroma/source fine detail, full-interior/soft-boundary placement, actual reference lash strokes and source local eye contrast. It does not train or run a new generative model. Color-space matching improves on the six fixed development cases but does not establish human realism or full style equivalence. Production Makeup model path remains unchanged. [Evidence](../docs/experiments/makeup-reference-visibility-20261101.md).


## Source surface proof does not solve full Makeup, 2026-11-02

**VERIFIED mechanics / EXPERIMENTAL component / REJECTED full look.** The live model returns a full generated face with textual identity instructions only. A new source lip component samples one cosmetic palette and retains original feature coordinates and interior lightness gradients; saturated shade fidelity is limited by source shadow protection. Reference pixels/shading cannot be pasted by that component. No new model training or inference. Explicit source mesh and masks still do not separate true blush/eye pigment from generated foundation; the six case combined attempt creates orange patches and remains rejected. Artist approved cosmetic layers are a PROPOSED alternative, not established capabilities or approved model replacement. [Evidence](../docs/experiments/makeup-source-surface-20261102.md).


## Makeup automatic offline candidate, 2026-11-04

The current own MAKEUP-001 is already trained and still serves unchanged. New scripts/makeup_local_features.py uses a pinned pretrained EleGANt CPU feature generator only for isolated automatic correction review. It is not our custom adapter, not a substitute claimed to satisfy the custom training requirement, and not integrated into the shared worker. Reference/self counterfactual features plus original surface pigment application produce52catalogcomparisons with no new diffusion or training. Source fidelity improves, but full cosmetic fidelity and target acceptance remain open. A corrected dataset does not prove future FLUX adapter behavior; finalization, new distinct training run, Base comparison and integration remain separate. [Evidence](../docs/experiments/makeup-automatic-correction-20261104.md).
