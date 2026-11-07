# Makeup deployment recovery plan — 26 October 2026

**PROPOSED implementation; AI-assisted cosmetic rendering acceptable CONFIRMED by Supervisor. No renderer implemented or deployed by this plan.**

## Recommendation and honest method description

Keep the original photograph as the output base. Use AI face-region detection/parsing to place cosmetic rendering in source facial coordinates. Change cosmetic pigment/finish within lips, eyelids and small cheek regions; do not generate a replacement face or apply a new whole-face foundation layer.

This is an **AI-assisted virtual Makeup try-on**, not inference from the current generative MAKEUP-001 adapter. The Supervisor explicitly says this method is acceptable. Retain the trained adapter and historical evaluation as project development history/rollback, with truthful generator metadata. Do not claim a renderer used that adapter or silently set lora_active=true.

No replacement training dataset is needed for this approach. Existing photographs are for visual evaluation; pretrained parsing weights remain external technology with their own provenance. Capstone documentation must distinguish the AI detector/parser, custom renderer/profile logic and the earlier trained generative model.

## Why this is different from the rejected attempts

- Whole-frame Makeup currently reconstructs skin, face and expression; subsequent skin-only Lab correction leaves an artificial relationship between adjusted skin and protected features.
- Closed DATA-M001 preservation V3/V4 transferred appearance/statistics from generated targets onto source anatomy. Spatial cosmetic detail was lost or contaminated by generated facial reconstruction.
- Base-only inpainting V1/V2 failed distinct visible Natural/Soft/Smoky effects.
- This proposal does not transfer a regenerated face, its broad complexion, or generated-minus-source maps. Cosmetic profiles explicitly define localized pigment, spatial gradients and intensity on the original photo. Style visibility and boundary quality must still pass real review; this difference is a hypothesis, not a quality result.
- Existing localized Nails renderer routing is an inspected integration precedent (backend/app/nails/hybrid.py, render.py, contract.py), not proof that face rendering is solved.

## Phase 1 — One bounded visual pilot

Prepare **three profiles on four existing original portraits = 12 outputs**: Natural Makeup, Soft Glam, Classic Red Lip. Freeze source hashes/credits, selected subjects, masks, profile parameters and renderer version before evaluation. Include a smiling/open-mouth input and varied visible complexions using existing consent/permission records; do not infer protected demographics or claim a representative population.

Use automatic source-relative region proposals from the cached face parser first. Inspect their overlays. Derive pigment placement from the person's own lip/eye/brow geometry. There must be no per-photo hand-painted correction passed off as an automatic system capability. Stop if reliable regions cannot be obtained for the chosen inputs.

Rendering design:
- Lips: source contour, inner mouth/teeth exclusion, a feathered pigment edge and retained local shading.
- Eyes: cosmetic placement on eyelid skin; protect eyeball/iris, lashes where appropriate, and original eye geometry. Use a spatially varying eyeshadow/liner profile, not a full rectangular patch.
- Cheeks: conservative transparent blush with a broad natural falloff. Preserve source skin illumination/texture; no whole-face color replacement.
- Start without foundation or complexion whitening/smoothing. This first scope is lip/eye/blush try-on, not full foundation shade simulation.
- Never paste a generated face or change jaw, neck, hair, clothes/background.

Retain all failed outputs. No broad GPU benchmark or new training notebook is needed. Do not spend another iteration only lowering global strength until styles become indistinguishable.

### Pass/fail gate

Both project owner/salon visual approval and technical checks are required.

Visual: visible intended cosmetics, Natural/Soft/Red genuinely distinct, no visible mask or pale halos, believable lip/eye boundaries, no painted teeth, preserved original complexion/texture, no obviously flat pigment.

Technical: exact source pixels outside permitted cosmetic regions; protected eye/mouth pixels and source geometry retained by construction; reproducible profiles; invalid/unsupported images produce a clear error rather than a misplaced cosmetic result.

Four existing development portraits are not an untouched generalization test. Before deployment, confirm accepted profiles on additional existing suitable photos and actual client uploads with permission, including expression/pose/lighting variation. Publish actual pass/fail coverage. No universal all-skin-tone or pose claim.

**If the pilot fails, hold integration and review the specific failure.** A successful test or no changed protected pixels is not automatic visual approval.

## Phase 2 — Accepted profile/catalog contract

After pilot approval, map only genuinely supported existing style IDs to the renderer. Validate further styles individually before expanding the catalog; do not present three similar templates as ten distinct looks.

If a name requires a whole-face foundation/finish the renderer does not provide, agree on accurate availability/description before release. Existing saved/booking snapshots and historical images stay intact. Do not relabel old generated images or invent service prices.

Create a separate versioned renderer/profile contract with parser/profile provenance. Preserve the frozen MAKEUP-001 contract and its model/hash checks; add deliberate dispatch/validation rather than weakening those guards.

Inspected integration points:
- backend/app/makeup_styles.py: catalog and truthful statuses.
- backend/app/main.py: currently marks remote Makeup as trained_preset; new mode must be identified honestly.
- backend/app/generation/remote_makeup.py and makeup_contract.py: current client requires MAKEUP-001/LoRA metadata. New mode needs its own explicit contract; pretending to be the old adapter would fail validation.
- scripts/unified_gate3_server.py and scripts/makeup_inference_server.py: current shared worker routes Makeup through the adapter owner. Do not put a CPU renderer through a false LoRA activation cycle.
- Existing demo API/job routes, BeautyCore AI proxy, trial proxy and consultation orchestration: retain request/ownership/authentication/job semantics and share the accepted Makeup capability.
- Client cards, descriptions/actual price mapping, saved looks and booking snapshots: exercise with the new renderer mode.

These are planning inspection facts; no serving file changed.

## Phase 3 — Kaggle/Render integration and rehearsal

Keep Render for the existing website/backend. Run face processing/rendering on the Kaggle side, behind the existing authenticated API and dynamic endpoint registration. First verify dependencies, CPU memory and processing time within the actual Kaggle environments alongside Hair/Nails. Do not move a large parser onto free Render compute or assume new dependencies are compatible.

Preserve the current single-job admission/ownership behavior; no unrelated concurrency redesign. Keep Hair/Nails model paths and old demo bundles unchanged. No new secret, account or per-run Render endpoint editing should be required by this method change.

Release matching Kaggle and application versions. Test:
1. Standalone Makeup for every enabled profile.
2. Consultation recommendations, generation and selected-look details.
3. Guest one-image allowance and limit handling.
4. Save/reopen/book; client and stylist see the same selected image/details.
5. Hair and Nails after Makeup use, busy/error behavior, restart/dynamic registration.
6. Actual CPU/RAM/latency and maximum image size, using the real deployed path.
7. Original snapshots/profile version compatibility and rollback.

Deploy the accepted subset only after this rehearsal; keep old artifacts as rollback. A failed new mode must not silently fall back to the already-rejected full-face behavior.

## First concrete deliverable

Twelve source-based cosmetic previews plus source/region overlays, per-case results and reproducible profile configuration. Human appearance approval comes before product integration. No claim of a guaranteed fix or deployment date until those images pass.


## Phase 1 receipt — 26 October 2026

The authorized12output offline pilot is complete. Source/protected pixels and input hashes pass independent checks;24focused tests pass. One pigment gamut defect was corrected with old evidence preserved. Cosmetic appearance remains pending human review, including strong lip edges/intensity and subtle eye/cheek effects. No production integration or cloud change. [Actual evidence](makeup-source-render-pilot-20261026.md).


## Existing-catalog extension receipt — 26 October 2026

Supervisor authorizes proceeding with the remaining7existing styles. Twenty-eight further source-based previews are complete;12baselinecontrols remain pixel-identical. All10existing styles now have offline examples, with51focused checks passing. This is not all-style appearance acceptance:localizedfinish/lip-boundary/intensity and description limits require review. No integration/cloud rollout. [Evidence and all-ten review gallery](makeup-seven-styles-20261026.md).
