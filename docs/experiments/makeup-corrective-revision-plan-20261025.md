# Makeup corrective revision plan — 25 October 2026

**PROPOSED corrective work; existing inspection and comparison evidence VERIFIED. No new training, serving changes or deployment performed by this plan.**

## Objective

Correct the shared Makeup generator used by existing and expanded styles. A candidate must show the requested cosmetics while preserving the original person's complexion, undertone, plausible skin texture and recognizable face/smile. A smaller guidance value or successful HTTP response is not this acceptance criterion.

The displayed new Berry output has been explicitly rejected. The earlier preference for guidance2.5is a relative visual selection, not approval of whitening or every new preset.

## What the project evidence establishes

- scripts/makeup_inference_server.py regenerates a full512square image with FLUX.2KleinBase+MAKEUP-001. The inspected preprocessing pads aspect ratio; no deliberate facial whitening filter was found in it or backend/app/generation/remote_makeup.py. The defect is visible in raw generated outputs before UI display.
- Foundation-only also over-edits. The current adapter makes visible retouching/lightening stronger on the fixed diagnostic examples; the exact contribution of specific training pairs is not isolated.
- FinalizedDATA-M001contains50trainpairs/10people and10validationpairs/2people, one general caption. Several paired targets visibly alter complexion/texture. Ten public presets are inference instructions, not10separately trained style classes.
- Reducing adapter influence, guidance4->3->2.5and adding source-complexion wording have not established a complete preservation fix.
- Earlier source-aligned preservationV3/V4and source-anchored inpaintV1/V2failed style/preservation gates. Their CPU invariants/technical GPU completion were insufficient. Do not restart those experiments unchanged.

## Phase1 — Concrete target review, before another GPU run

Produce a per-pair KEEP / REJECT / NEEDS_REPLACEMENT manifest and private review sheets for the existing60source/target pairs. Preserve old files and hashes. For each pair record:

1. Source/target subject and alignment consistency.
2. Natural complexion/undertone and lighting consistency, outside intended cosmetic regions.
3. Plausible retained skin texture and unchanged face, eyes, lip outline, teeth and expression.
4. Requested cosmetic features clearly visible and localized, with truthful style/strength labels.
5. Unrelated hair/background/clothing edits and permission/source provenance.
6. Reason for decision and reviewer.

Do not convert earlier broad pair approvals into current quality acceptance. Do not count five variants of one person as five new people. Rejected current outputs must not become automatic replacement targets. Report usable counts and gaps instead of inventing a dataset size.

Use permissioned real same-person before/after references or separately reviewed suitable targets for gaps. Controlled lighting/framing is needed so a brighter photo is not mislabeled as makeup. Vary complexion/capture conditions and avoid whole-image retouching/whitening filters. No image acquisition is started by this plan.

## Phase2 — One bounded corrected-data candidate

After the reviewed dataset can support the requested edits, define a versioned corrected-data training/fine-tuning plan for one new adapter candidate. Preserve the current adapter and notebooks. Compare against both the current adapter and foundation-only controls using fixed source/prompt/seed/frame; record actual training configuration/target hashes rather than claiming a settings tweak created a new trained model.

Start with controlled Natural/SoftGlam/RedLip evidence before extending all preset directions. Captions must describe actual visible cosmetics; do not relabel identical heavy looks as different styles. Distinct style data is needed only where review establishes it, not arbitrary generated class counts.

If adequate targets are unavailable, stop before spending GPU quota on unsupported training. Fine-tuning may fail because foundation reconstruction also contributes; do not promise it will fix all skin tones.

## Phase3 — Preservation and visible-makeup acceptance

Use untouched final-test people beyond the2repeated diagnostic identities, with varied complexion, lighting, expressions and smiles. Compare side-by-side with originals at identical settings. Client/salon reviewers should reject:

- Source complexion noticeably lightened or changed outside intended cosmetics.
- Plastic/erased skin texture, changed face geometry or damaged teeth/lip boundary.
- Missing/weak requested cosmetics.
- Strong cheek/eye/lip edits beyond a named subtle style.
- Different names producing indistinguishable looks.

Require both preservation and useful visible cosmetics on the same result. Record failures rather than select one attractive output. No invented numeric skin score or guaranteed universal quality threshold.

If a corrected-data candidate still reconstructs/whitens faces, do not continue a long parameter sweep. Prepare a separately reviewed design for a method that constrains edits more directly to cosmetic regions. It must address the concrete failure modes of the previous closed preservation/inpaint routes and prove style visibility at the same time; no such method is implemented or selected here.

## Phase4 — One compatible rollout for both existing and new styles

After acceptance, version the Makeup execution profile/checkpoint/prompt manifest together across scripts/makeup_inference_server.py, scripts/unified_gate3_server.py, backend/app/makeup_contract.py and backend/app/generation/remote_makeup.py. Preserve historical artifact/hash guards and existing style IDs; do not claim altered settings are the frozen original profile.

The same corrected generator should serve direct Makeup requests and consultation previews. Test all supported presets, visible descriptions and truthful pricing/service mapping, saving and selected-look booking, adapter switching with Hair/Nails, and guest preview where enabled.

Package matching Kaggle/application updates, retain old bundles as rollback, then perform authorized coordinated rollout and end-to-end rehearsal. The old raw saved images remain historical records, not silently modified evidence.

Do not deployguidance2.5as a proven corrective fix now. Hold new Makeup looks pending correction/acceptance. Existing live service is not disabled by this plan. Hair/Nails can proceed independently.

## Concrete next deliverable

The next useful deliverable is the60pair review manifest with usable/rejected counts, examples and a replacement-data gap list, followed by a bounded training proposal if usable material supports it. No new generation notebook is needed before this review.


## Phase 1 receipt — 25 October 2026

Concrete 60-pair audit and replacement-data research are now DONE. Codex screen: 0 KEEP, 60 REJECT for unchanged corrective reuse; original data and historical human approvals preserved. New human/salon acceptance is pending. Eighteen integrity checks plus actual dataset/ledger revalidation pass. Supervisor explicitly selected replacement-dataset investigation. No candidate yet passes pairing, quality and permission gates together; Phase 2 training has not started. [Audit](makeup-corrective-review-20261025.md), [research and unsent access inquiry](../research/makeup-replacement-datasets-20261025.md).
