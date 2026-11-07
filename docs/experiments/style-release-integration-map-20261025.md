# First expanded release integration map — 25 October 2026

**Inspection VERIFIED. Runtime integration NOT STARTED; candidate acceptance awaits returned portrait evidence/client Nail review.**

The approved next phase is validation followed by integration of accepted entries. This file records the actual coupling that must be handled together. It does not approve every shortlist entry or start deployment.

| Area | Verified files | Required accepted-release change |
|---|---|---|
| Makeup inference | backend/app/makeup_contract.py; scripts/makeup_inference_server.py | Existing contract/meta verifier still pins original guidance4.0; generation/returned metadata also state4.0. Introduce explicit revised execution contract/profile for selected2.5and accepted prompts without rewriting frozen historical checkpoint provenance or disabling hash checks. |
| Unified GPU routing | scripts/unified_gate3_server.py; scripts/unified_gate1.py | Prompt/style allowlists and outgoing result validators currently own original presets/settings. Keep old experiment validation intact; validate revised execution settings explicitly, rather than pretending2.5is unchanged4.0. Preserve Hair/Nails profiles. |
| Remote Makeup client | backend/app/generation/remote_makeup.py | Allow only accepted matching style/prompt profile and validate compatible response provenance. Old supported styles and response format remain stable. |
| Hair registry | backend/app/style_registry.json; backend/app/style_registry_train002_smoke.json; scripts/kaggle_inference_server.py | New Comma ID must be intentional experimental prompt support on verifiedTRAIN-002, not a false new training label. The metadata verifier compares claimed style sets exactly; simply appending an ID breaks ownership checks. Add explicit tested ownership/profile without rewriting old artifact or broadening to arbitrary client prompts. |
| Nails routing/rendering | backend/app/nails/styles.py; contract.py; render.py; hybrid.py | Add accepted renderer IDs and reuse checked algorithm/automatic-mask/compositing path. No new Nails model training. Preserve existing5styles, source nail geometry and all outside-mask pixels. |
| Nail runtime construction | backend/app/main.py configured_nails_pipeline; segmentation.py; geometry.py; scripts/nails_segment_once.py | Existing automatic detector/isolatedCPUenvironment and checkpoint paths stay. Validation wrapper mirrors normalization/refinement/inward-composite; route integration still needs real upload checks. |
| Consultation | backend/app/consultation/catalog.py; metadata.py | New active IDs require tags; missing tags fail consultation. Nail IDs also require explicit model/renderer classification. Use only active accepted catalog entries. |
| Frontend/save/book metadata | beautycore/lib/business/style-catalog.json; look-information.ts; beautycore/lib/services.ts; saved-look/booking APIs | Add public names/descriptions and actual existing service mappings together, retain legacy IDs/snapshots and durable saved-look images. Screens should discover available catalog styles rather than show unsupported results. |
| Price estimates | beautycore/lib/services.ts and business/look-information.ts | Makeup Application is currently Price to be confirmed. Do not treat backend consultation metadata's500demo amount as actual salon pricing. Nail Art per-nail charge is not a full-manicure cost. Confirm extra design charges; invent none. |
| Deployment handoff | Original GPU/CPU bundle and existing demo notebook packagers | New versioned compatible bundles/notebook, matching API/catalog client and tests; keep old bundle/notebook as rollback. No database change inherently needed for adding accepted style metadata; verify existing service/save snapshot handling during implementation. |

## Release gates

1. Review STYLE-VAL-00129portrait outputs,4prior selectedMakeup pixel controls and final adapter restoration. Review automaticNail masks/finishes on4hands.
2. Implement only accepted subset using explicit versioned runtime contracts. No arbitrary free-text style path and no broad weakening of artifact validators.
3. Run catalog consistency, generation profile/response tests, consultation recommendations and save/book mapping checks; confirm both direct generation and consultation show the same accepted options.
4. Build matching private Kaggle package, validate all3features and consultation, preserve fallback, then perform authorized rollout and end-to-end rehearsal.

There is no new training dataset/weights in this phase. Broader variety and untouched final subjects remain later quality work. A candidate may be held without blocking reliable existing styles.
