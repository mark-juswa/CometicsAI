# STYLE-VAL-001 completed release validation — 25 October 2026

**GPU execution, provenance and controls VERIFIED. Visual review DONE. Accepted-style application integration and deployment remain IN PROGRESS.**

## Verified outcome

All **29 calls completed**:20existing Makeup preset cases,4new Makeup cases,4Hair cases and1restoration image. Every source/prompt/checkpoint/PNG/RGB hash matches the frozen plan and source inventory. Exact Python/Torch/CUDA/dependency environment matches the reviewed T4 setup.

The4Natural/Red Lip controls reproduce earlier selected guidance2.5outputs exactly: independent PNG byte and decoded pixel checks pass. The final Natural image is byte-identical to the first one after switching Makeup → TRAIN-002 → Makeup. Both adapter states verify200tensors across100LoRA layers at full1.0influence. One foundation was loaded. Existing public catalogs and live settings were not changed.

The Supervisor's selected2.5setting remains the chosen Makeup candidate. This run establishes compatibility across all10existing presets on these two development inputs. It does not override that selection, nor prove exact style fidelity or source-complexion preservation for every user.

## Visual findings

| Item | Observation | Recommended disposition |
|---|---|---|
| Existing10Makeup presets at2.5 | All execute. Smoky, peach, pink, bronze, red and evening directions are visibly distinguishable. Natural/Red exactly reproduce the selected earlier controls. No-Makeup is much heavier than its label, and Matte Nude retains strong shiny highlights. Earlier retouching/complexion limitations remain. | Selected2.5profile can proceed to compatible serving integration/regression, with these limitations recorded. Do not claim all10visually perfect. |
| Cloud/Blurred Berry Lips | Berry lips/cheeks are visible on both people. Lips look sharply outlined/glossy rather than reliably blurred, while cheeks/eyes are strong rather than understated. | Show actual outputs for client review. Hold the original blurred/subtle claims; no automatic rename/enablement. |
| Icy Silver Eye Makeup | Clear silver/blue metallic lids on both people. Lips remain vivid pink/red rather than the requested subtle natural lip, and eyelid effect is broad/strong. | Visually distinct candidate for client review. Do not promise the original restrained styling or enable automatically. |
| Comma, curtain-source input | Obvious thick outlined loop/U shapes sit on forehead rather than convincing strands; source auburn hair becomes black. Existing Curtain baseline also changes color/appearance. | **Hold new Comma style.** |
| Comma, side-part-source input | Curved rounded fringe is present but stays close to the Curtain baseline and obscures eyes. A reliably distinct Comma result is not established. | **Hold new Comma style.** |
| Three Nail designs | Separate prior CPU experiment used real automatic masks/refinement on4hands with5nails each and12renderer outputs; zero outside-mask changes independently verified. | Continue client appearance/edge review and accepted-design integration. This evidence is not part of the29portrait calls. |

The Comma result is weaker than the initial single-image promise suggested; preserving the failed outputs prevents a misleading new public style. Existing Hair baseline preservation limits are also recorded rather than attributed solely to the new prompt.

## Practical first release

1. Prepare the explicit compatible serving profile for the **selected Makeup guidance2.5**, preserving the old4.0notebook/bundle fallback and frozen checkpoint provenance.
2. Show the **three Nail designs and the two new Makeup looks** for client visual acceptance. Add only accepted designs. Berry/Icy have recognizable color directions, but they should not receive labels promising details they did not produce; any revised naming/scope needs agreement.
3. Keep **Comma Hair held**. Do not add a style selector entry for an unreliable new look merely to increase the count.
4. Integrate accepted entries through generation allowlists/profile metadata, consultation tags, descriptions, actual service mapping, saved looks and booking. Preserve previous IDs/snapshots and do not invent Makeup prices.
5. Build matching versioned Kaggle/application packages, run direct-generation/consultation/save-book regressions and then an authorized rollout. No further GPU sweep, training, relabeling or rollout is started by this result review.

A useful partial expansion is preferable to enabling every candidate despite artifacts. The overall13candidate expansion is not complete; this batch has now supplied the evidence needed to choose the first subset.

## Timing and evidence limits

Recorded forward wall time totals **1863.77seconds (31minutes4seconds)**. Range60.38–67.49seconds, median64.24seconds. Foundation load44.48seconds separately. Peak allocated CUDA tensor memory8304.31MiB; this is not total/reserved device memory. Setup, Base download, sheets and ZIP overhead are excluded. These are worker observations, not website performance or a controlled before/after speed result.

The10,369,659byte ZIP has SHA256:
52aa504b1d5fd91d43fef65460bd4c5d3c3e2a8c7e3ff9218b0cfb1d84d58302.
CRC, duplicate/path guards, original source inventory, compiled-source/plan equality,29case ordering/settings, allPNG/RGB/source checks and exact runtime pass. No bundled code was executed during review.

Two reused Makeup subjects and two historical Hair validation inputs are development evidence, not an untouched final test or representative all-user coverage. This is qualitative Codex review; no numeric skin/style score or new salon approval is supplied.

## Private review sheets

- [Makeup — subject054109](../../artifacts/style-expansion-20261025/release-review-01/results/makeup-054109-comparison.jpg)
- [Makeup — subject056266](../../artifacts/style-expansion-20261025/release-review-01/results/makeup-056266-comparison.jpg)
- [Hair — curtain source](../../artifacts/style-expansion-20261025/release-review-01/results/hairstyle-d2_curtain_hair_4jpg-comparison.jpg)
- [Hair — side-part source](../../artifacts/style-expansion-20261025/release-review-01/results/hairstyle-d2_side_part_undercut_28jpg-comparison.jpg)
- [Per-case review](../../artifacts/style-expansion-20261025/release-review-01/review-by-codex.csv)
- [Machine verification](style-release-validation-20261025-review.json)

The exact source ZIP, raw reports/logs/PNGs are preserved under ignored private artifacts. Render, application code, deployed model/parameters and old demo notebooks remain unchanged.


## Supervisor rejection after visual review

The Supervisor explicitly rejects the displayed Berry result at2.5as unnatural, too white and poorly blended with the source complexion. **Hold new Makeup expansion promotion.** Runtime completion and prior relative preference for2.5are not proof of a skin-preservation fix or acceptance of this new look. No live configuration was changed. [Rejection record](makeup-berry-quality-rejection-20261025.json).
