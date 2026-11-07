# BeautyCore fresh validation notebook — STYLE-VAL-001

**Local preparation and original-bundle preflight VERIFIED. GPU portrait outputs NEED VERIFICATION. Automatic Nail checks ran locally; client visual acceptance remains.**

## Exact Kaggle steps

1. Create a **new private** Kaggle notebook and import [beautycore_release_validation_v1.ipynb](../../artifacts/style-expansion-20261025/beautycore_release_validation_v1.ipynb).
2. Enable Internet and choose the reviewed **GPU T4** configuration. Keep the working demo notebook/bundles intact.
3. Attach exactly **one input containing capstone_train002_20260928_v1.bin**. No CPU bundle or API Secrets are needed. The notebook embeds four existing private research portraits.
4. Run the first code cell once. Check **GPU bundle matches: 1** and **RELEASE_VALIDATION_WORKSPACE**. If missing/duplicated, fix notebook input attachments; do not remove guards.
5. Run the second code cell once. Fresh package installation, environment/artifact checks and the pinned Base download happen before inference. Writable /tmp or /kaggle/temp must retain at least30GiBfree.
6. Wait for **STYLE_VALIDATION START/DONE 1 / 29 through 29 / 29**.
7. Download **beautycore-release-validation-results.zip** from the unique folder printed after **DOWNLOAD_RELEASE_VALIDATION_RESULTS**. Return it for review. Failures also produce a partial ZIP; return it rather than mixing earlier recovery cells into this notebook.

At the earlier roughly64seconds per image,29calls suggest about31minutes of generation plus setup/download/model loading. This is an estimate, not a measured runtime for this run. Starting a fresh session requires download/install again; do not confuse that with per-image generation time.

The exact reviewed Python/Torch/CUDA/T4 host is checked. A host mismatch stops rather than altering dependencies to force a run. The notebook creates no public API, tunnel, Gemini request, Render update or website registration.

## What this batch tests

| Part | Calls | Purpose |
|---|---:|---|
| All10existing Makeup presets x2people | 20 | Check the selected2.5setting beyond Natural/Red Lip |
| Berry Lips and Icy Silver x2people | 4 | Reassess expansion prompts at2.5 |
| Curtain baseline and Comma x2Hair inputs | 4 | Evaluate visible shape on more suitable sources with TRAIN-002at4.0 |
| Final repeated Makeup control | 1 | Check pixel restoration after adapter switching |
| Total | **29** | One foundation, full adapter influence |

The four Natural/Red Lip2.5outputs must reproduce prior reviewed pixel hashes. The final Makeup image must match the first new image exactly. Failure preserves evidence and stops. Experimental prompts are recorded as experimental, not fabricated supported preset IDs.

All portraits use20steps,seed1977,512square. Makeup guidance is2.5, Hair4.0; no new guidance sweep. Source/prompt/adapter hashes, active tensors/effective scaling, output hashes, elapsed time and memory are recorded. Four per-subject sheets and an unfilled visual-review CSV are included.

The Hair sources are existing DATA-002validation members with visible medium/short tops, rather than the initial bob-only pilot. They are reused historical source photographs with documented rights limitations, not newly collected salon examples. The two Makeup people are also reused diagnostic cases. No generalization or final held-out evaluation claim follows from this batch.

## Automatic Nails results already available

The actual existing MediaPipe/YOLO pipeline, including source-resolution fingertip refinement, completed on4historical validation hands. All5nails per hand were found, and3styles x4hands=12outputs were rendered. Independent pixel checks confirm no change outside the actual refined mask and edits in all5nail components per output.

Review these sheets:

- [Hand0000045](../../artifacts/style-expansion-20261025/automatic-mask-validation-02/0000045/comparison.jpg)
- [Hand0000088](../../artifacts/style-expansion-20261025/automatic-mask-validation-02/0000088/comparison.jpg)
- [Hand0001030](../../artifacts/style-expansion-20261025/automatic-mask-validation-02/0001030/comparison.jpg)
- [Hand0001593](../../artifacts/style-expansion-20261025/automatic-mask-validation-02/0001593/comparison.jpg)

Columns:Original / Raspberry Jelly / Pink Aura / Micro-Dots. These ran locally on CPU; there are no Nail GPU calls in the notebook. Look at nail-edge alignment and the finish in full-resolution PNGs too. Zero outside-mask changes do not prove a mask cannot include skin.

The styles remain experimental until visual acceptance/integration. No changes to production Nails routing or existing styles have been made.

## After the returned ZIP

Accept only outputs with recognizable identity, intended style, acceptable complexion/texture and restrained unrelated changes. Distinct lipstick/eyeshadow does not by itself clear a Makeup candidate. A curved isolated strand does not automatically clear Comma Hair. Hold failures rather than silently enabling the entire shortlist.

Then wire only accepted entries through the [integration map](../experiments/style-release-integration-map-20261025.md) and prepare matching application/Kaggle packages. Render and the original demo remain unchanged until a subsequent authorized rollout.

78focused local tests, including12new runner/packager checks, pass. Original GPU bundle CRC/allmemberhashes, fresh notebook compilation, all embedded source/portrait hashes and no overlay collisions pass. No local CUDA portrait inference was run.

[Machine evidence](../experiments/style-release-validation-20261025.json).


## Returned result, 25 October 2026

The29callGPUrunis nowcomplete and independentlyverified. Fourprior2.5controls and finaladapterrestore matchPNGbytes/pixels. Existing10Makeuppresets execute;newBerry/Icyrequireactual-outputreview,Comma isheldforartifacts/weakfidelity. Do notrerunthiscompletedbatch automatically. See [completed review](../experiments/style-release-validation-20261025-review.md). No publicstyle/profile/cloudchangehasbeenperformed.
