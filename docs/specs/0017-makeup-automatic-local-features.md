# Automatic source anchored Makeup correction

4 November 2026. Scope **CONFIRMED by the Supervisor's renewed original task**. Offline algorithm selected by engineering within that scope; production adoption remains **PROPOSED**. Bounded implementation **DONE**; full Makeup fidelity **IN PROGRESS**. Appearance **EXPERIMENTAL**. No training or production approval.

## Constraint correction

Supervisor has no makeup artist and requests completion of the original engineering task. The artist asset dependency introduced in spec0016 is not a feasible critical path. Keep its useful source material operator and target review gates; do not require an artist or fabricate their approval. Supervisor/Project Lead can review actual outputs. This document changes the input mechanism for the bounded correction, not the existing FLUX/LoRA training or application architecture.

## Evidence and method

Previous methods extracted ambiguous pigment from flattened generated RGB and failed. The bounded alternative uses the pretrained EleGANt generator's local reference feature transfer. Its strict checkpoint load passes locally on CPU, and its self reconstruction plus transfer complete in the local feasibility check. Raw full transfer still lightens skin and must not be adopted directly.

For each original, encode original content once. Decode both self reference and locally mixed reference features against the SAME content. Compare their linear light densities, cancelling common reconstruction bias, then apply cosmetic absorption to the untouched original surface. Retain the previously preferred lipstick function, with declared style intensity for other catalog looks. Original landmarks and parser maps supply automatic eyelid/cheek support, with source eyes/brows/nose/teeth/scene protection. The cheek substrate remains original; pigment may darken it naturally. Small legitimate silver eye highlights remain region and style bounded. No source warp, procedural lash strokes, face replacement, external artist or Kaggle generation.

The first Lab application demonstrated that unchanged lightness alone can still make warm skin look pale by removing its chroma. Unconstrained absorption also permitted a cyan/gray pigment direction. Final application projects centered density onto a nonnegative pigment basis for each catalog color family, then applies it to source reflectance. Eye neutral absorption supplies dark definition. Material color and per region intensity are explicit engineering defaults derived from catalog intent, not artist approvals. Existing Natural/Red/Berry lip dose1 retains all six earlier component outputs. Sheer and soft styles have lower declared lip coverage. Shadow fades within the source crease/brow gap, preventing the earlier hard orbital plate edge. These changes address observed color direction, finish and support failures; they are not an inference setting sweep.

Inputs are original512RGB, source labels, true SPIGA68 and source MediaPipe478 anatomy, selected catalog ID, existing saved style guide and its parser/SPIGA68. Original controls exist for four development people; all13guides exist. Use one guide per style across identities, rather than fitting materials to each person. Preserve all catalog IDs and differences. Existing guides are imperfect AI style guides, not real cosmetic truth. New automatic fields remain estimates.

The author generator is pinned at d033d3398751684eb8c4b5aef54c74b84f3a3ef8; its author linked41,123,601byte checkpoint has observedSHA71473aa3abad4f66536cef89ab179851547811f1153e846333fa167655776737. Keep source/license/receipts isolated. CPU only, existing environment, no package installation. Author code documents CC BY-NC-SA4.0; no commercial deployment/target rights conclusion follows from technical feasibility.

Preprocessing explicitly adapts existing Segformer19 labels to the author's two model masks and uses true68point SPIGA topology, not a fabricated478to68 map. This differs from the author dlib/BiSeNet pipeline and must remain recorded as a compatibility limit.

## Build and verification

1. Extend the reusable source application with automatic counterfactual fields, preserving its lip component and mandatory target gates.
2. Add one offline CPU feature provider with strict source/checkpoint validation, bounded caches and cloned decoder inputs. The author decoder mutates feature lists; cached content must remain intact.
3. Freeze representative/full catalog inputs and controls before outputs. First inspect a complete look, then cover four available development people and thirteenstyles without new diffusion. Refuse missing/uncertain anatomy instead of lowering guards.
4. Verify source protection, same reference no change, cache independence, numerical safety and exact retained lip reproduction. Inspect full photos and native eye/lip crops, assessing visibility, blending, identity, complexion and style differences together.
5. Report actual successes/failures and preserve comparisons. Do not create training targets or integrate an unaccepted result. New own adapter data, training, Base evaluation and application rollout remain separate milestones.

No additional service or model is loaded into serving. The prototype provider is an offline correction candidate, not a replacement for the required project trained generative component. If visual quality fails, record failure honestly rather than claiming masks or tests solve realism.

## Bounded implementation result

Four sources by thirteen styles produce52comparisons using one shared guide per style across all identities.95focusedchecks plus27unchangedruntimechecks pass.52source protection checks, four neural identical reference controls and a full catalog cache restoration check pass. The final material/edge review uses saved neural fields without further model generation. Full photos and native eye/lip sheets were inspected. Source preservation improves visibly; metallic finish, Manga lash shape, subtle style separation and some lip edges remain incomplete or unverified. Zero training targets are auto accepted. [Result and exact limits](../experiments/makeup-automatic-correction-20261104.md).

## Bounded source material refinement, 5 November 2026

**CONFIRMED local continuation authorization; implementation DONE; complete fidelity IN PROGRESS; appearance EXPERIMENTAL.** Supervisor requests proceeding with the identified remaining defects. Extend the existing automatic application through optional source materials, preserving its default baseline and preferred historical lip function. No serving/model/provider replacement, artist prerequisite or new diffusion is authorized by this refinement.

Value sources are explicit: source lip coverage comes from the cached source parser probability constrained by the existing parser/contour agreement; color comes from the selected catalog guide; lightness/shadows and highlights come from the original portrait. The original photo is never spatially filtered or warped. A bounded local shadow guard replaces reference mouth reconstruction and one dark pixel limiting the whole lip. Constant pigment chroma corrects retained cool source hue variations. These changes apply through one reusable operator and the full catalog configuration.

The selected Manga guide contains artificial spikes. Existing user provided `stable-makeup-pilot/inputs/makeup-reference.png` supplies observed finer lash and reflective alpha detail only. Source eye anatomy determines fitting. Manga cluster spacing still comes from the selected style guide; no procedural lash drawing or donor face RGB is used. Silver/gold reflection is limited to the source mobile lid. Source existing shine evidence supplies Dewy/Matte/Cloud finish changes bounded to three Lab units. No smoothing or new foundation is introduced. This source reuse is an engineering choice for local review, not approval for training or production; donor author/license is UNKNOWN and remains in provenance.

Acceptance requires preserved original eye opening cores, brows/nose/teeth/scene and natural, recognizable selected cosmetics together. One pixel lid rim occlusion by mascara is explicit and measured separately from protected eye cores. Positive source checks do not excuse artificial lashes or metallic patches. New material inputs are hash bound and optional; old calls remain reproducible. Human target admission and the existing FLUX/LoRA training/inference architecture remain separate gates.

Nine representative combinations precede the full 52 case matrix, reusing saved neural fields. New exact native comparisons, masks, provenance and failed diagnostics are preserved in a new directory.119distinctchecks,52independentsourcechecks and208imagebrowserverification pass. Lip hue/coverage improves and lash/reflection detail becomes visible; some comb-like lashes, uncertain Manga clusters, identity dependent metal texture and modest finish distinctions remain. No new target is accepted and no new adapter is trained. [Actual result and unresolved criteria](../experiments/makeup-material-refinement-20261105.md).
