# Style expansion feasibility audit — 2026-10-25

Status: source inspection VERIFIED; proposed expansion PROPOSED; implementation NOT STARTED.

## Verified current source
- scripts/render_kaggle_bootstrap.py selects backend/app/style_registry_train002_smoke.json for the CPU facade. That registry enables 13 Hair styles across TRAIN-001 and TRAIN-002. The historical default registry enables three. Neither source configuration establishes the current client Kaggle session's active version.
- backend/app/makeup_styles.py lists ten Makeup options. backend/app/makeup_contract.py checks a fixed preset hash and exactly ten preset IDs. data/makeup/DATA-M001-paired/inference_presets.json explicitly says these are inference prompts, not training labels. Expansion requires a separately reviewed version of this contract/preset package, not removal of integrity checks.
- backend/app/nails/styles.py lists five styles. backend/app/nails/contract.py routes classic_red and glossy_black through the adapter, and nude_pink, french_tip and pink_ombre through the renderer. backend/app/nails/render.py defines fixed colors/tip/gradient behavior. Additional renderer styles require explicit code/routing and visual validation; arbitrary art or altered nail geometry is not supported by this inspection.
- backend/app/consultation/catalog.py fails on absent tags or unknown Nails routing; backend/app/consultation/metadata.py must cover additional recommendation styles.
- beautycore/lib/business/style-catalog.json maps look descriptions to bookable services. beautycore/lib/business/look-information.ts reads service prices; new prices must be salon-confirmed, not inferred from an image.
- python scripts/check_saved_look_catalog.py passed. This is catalog consistency only, not GPU generation or proof of new-style quality.

## Proposed smallest expansion
1. Agree an initial shortlist with the salon, including names, visual references, supported service mappings and missing prices.
2. Trial additional Hair/Makeup instructions with the existing adapters in a separate GPU notebook. Treat outputs as experimental; prompt success cannot be assumed and is not evidence of new training.
3. Extend straightforward Nail color/tip/gradient options through the existing renderer where they pass mask/lighting/skin-preservation checks. Keep complex art and geometry changes separate.
4. Where existing models fail, collect permissioned, correctly labeled data for an isolated training experiment. Use matching input/target images where required by that feature's existing training pipeline; separate evaluation identities from training and retain baseline examples.
5. Accept new styles only after visual checks across varied inputs plus regression checks for old looks, inference time and memory.
6. Update generation contracts, consultation metadata, look/service mappings and tests together. Preserve stable old IDs and existing saved/booking records. Publish versioned Kaggle bundles/notebook after approval; keep current demo artifacts for rollback.

## Unresolved
Desired styles, data sources/permissions, salon price mapping and GPU evaluation time remain to be agreed. Current live catalog and client startup are not checked by this audit. No datasets were downloaded, models trained, application code changed or cloud configuration/deployments performed.
