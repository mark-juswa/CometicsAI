# Style expansion status — 25 October 2026

**Overall: IN PROGRESS. Research/initial pilot and preferred Makeup setting selection are complete; public expansion and deployment are not complete.**

## Verified completed work

- Researched 13 candidates: 5 Hair, 3 Makeup and 5 Nails.
- Tested the first 8 distinct styles in isolation: Butterfly, Two-Block, Comma; Blurred Berry, Icy Silver; Raspberry Jelly, Pink Aura and Negative-Space Micro-Dots.
- Pilot produced 15 portrait calls including old-style controls/restorations, plus 3 nail-renderer prototypes. This is not 15 new public styles.
- Comma with TRAIN-002 is the most promising Hair direction, still partial and needing suitable varied inputs. Butterfly/Two-Block are held for appropriate-input/fidelity testing.
- Three Nails prototypes preserve all pixels outside one supplied manual mask. Automatic masking and varied hands are not yet accepted.
- Makeup quality investigation tested Base/current/reduced-adapter, guidance changes and foundation instructions. Supervisor explicitly selects latest guidance 2.5; full adapter, original prompts/steps/seed/frame retained.
- Guidance 2.5 is a selected inference setting, not a new trained checkpoint. The correction tests used two existing presets on two reused diagnostic people; expanded Makeup presets were not validated at 2.5.
- Latest relevant focused suite has 100 local tests passing. Returned diagnostic archives independently verify GPU controls/provenance.

## What remains

1. Prepare a compatible versioned serving configuration for selected Makeup guidance 2.5; validate other supported Makeup presets and standalone/consultation behavior. No further guidance sweep is automatically needed.
2. Validate Comma and the 3 Nail designs on varied appropriate inputs, with actual automatic nail masks. Confirm visual acceptance before new catalog support. Hold unsuccessful styles.
3. Integrate accepted entries consistently across generation routing/allowlists, selection UI, consultation catalog/tags, descriptions, actual service/price mappings and saved-look/booking snapshots. Preserve old style IDs.
4. Package an updated Kaggle bundle/notebook and any required matching application changes, perform regressions and then a separately authorized Render/Kaggle rollout. Keep existing notebook/bundles as fallback.

The shortlist's other 5 candidates remain untested. No new training dataset or adapter fine-tuning was completed in this expansion. The image-intake CSV is still header-only; style generation outputs are diagnostic evidence, not automatically accepted training samples.

## Current implementation boundary

The repository's public metadata catalog contains 13 Hair, 10 Makeup and 5 Nail entries, with no experimental IDs. These are repository metadata counts, not an independently verified live-website availability check. Production Makeup source contract/inference still uses guidance 4.0; the selected 2.5 remains experimental until integration. Public catalog consistency checker passes. Neither new styles nor the selected setting were deployed by this work.

No code/model/data/cloud change or new GPU generation is performed by this status report.

Evidence: [initial pilot review](style-expansion-pilot-20261025-review.md), [Makeup guidance review](makeup-guidance-25-20261025-review.md), [human selection](makeup-guidance-selection-20261025.json).
