# Makeup complexion-preservation audit — 25 October 2026

Status: issue/data/runtime inspection VERIFIED. Exact causal attribution and corrective settings NEED VERIFICATION.

## Findings
The latest raw output files visibly lighten and smooth the complexion; this exists before website display. The user reports the same issue in the deployed experience.

scripts/makeup_inference_server.py pads the source to 512x512 and generates a full frame at 20 steps, guidance 4.0 and seed 1977. It has no source-complexion lock or region mask. backend/app/generation/remote_makeup.py pads, sends and validates the PNG; the inspected path has no deliberate facial whitening operation. Light padding applies to borders, not a skin-color adjustment.

The inference prompts already request natural skin tone and texture preservation. More wording is not established as a fix.

The finalized DATA-M001 manifest has 50 training pairs from 10 distinct people and 10 validation pairs from 2 separate people. All source/target image hashes were reverified. One shared caption describes a general target makeup edit. Five examples per person are not five independent people; ten public presets are inference instructions, not ten labeled training classes.

All three original contact sheets were inspected. Several training groups, including 006553, 020867 and 022625, visibly retouch texture and change complexion/lighting. This is visual inspection, not a standardized lightness metric or a demographic distribution audit. Earlier MAKEUP-001-evaluation.md also records changes in complexion, skin tone, facial detail and overly glamorous Natural/No-Makeup results.

Retouched targets are a plausible contributor, not proof that the adapter alone caused whitening. Earlier Base results also reconstruct faces. A matched ablation is needed to distinguish foundation, adapter and setting effects.

## Recommended next diagnostic — PROPOSED, NOT RUN
Use two current held-out inputs and two existing presets (Natural Makeup, Classic Red Lip). Compare foundation only, current adapter and one reduced-adapter-influence setting with matched input/prompt/seed/resolution/steps/guidance: 12 observations.

Base-only is a control, not an approved replacement. Explicitly record any adapter scale and restore the original state; never report modified settings as the unchanged production contract. Lower influence fails if makeup simply disappears.

Review source complexion, skin texture, eye/nose/lip geometry, smile/teeth, intended cosmetic color and non-target regions. Quantitative color checks need aligned reviewed skin regions and stable lighting. Whole-frame brightness is not a skin-preservation score; no numeric threshold is invented here.

## Data correction
Re-review old targets before adding more. Prefer permissioned same-person examples with consistent framing/lighting and no unintended complexion lightening, aggressive smoothing or structure changes. Include varied complexions and capture conditions without guessing ethnicity or other identity categories from photos.

Use truthful visible makeup labels, subject-disjoint splits and untouched final evaluation people. Repeatedly tuning against the existing validation identities makes them diagnostic development inputs, not an untouched final test. Do not automatically train on the latest heavily retouched outputs.

If settings cannot achieve visible makeup with acceptable preservation, prepare a separately reviewed data/fine-tuning experiment. Merely appending more flawed examples is not a corrective strategy.

## Existing boundaries and current status
Historical prompt-only, preservation and inpainting dataset experiments failed their quality/style-control gates. No such route is reopened by this audit, and no new generation architecture is implemented.

Prioritize correcting Makeup before promoting more Makeup presets. This audit does not disable or change the deployed service. Hair/Nails work can remain independent. No application/model/settings changes, data downloads, GPU requests, training or deployment were performed.
