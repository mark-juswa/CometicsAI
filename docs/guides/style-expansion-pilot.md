# BeautyCore private style expansion pilot

Prepared: 25 October 2026. Stage: isolated feasibility testing; production availability is unchanged.

## What is ready

The approved first batch is Butterfly Cut, Korean Two-Block, Korean Comma Hair, Cloud Skin with Blurred Berry Lips, Icy Silver Eye Makeup, Raspberry Jelly, Pink Aura and Negative-Space Micro-Dots.

The new notebook contains 15 diffusion calls: five old-style controls, six Hair trials (three prompts across both existing Hair adapters), two Makeup trials and two old-style restoration checks. It also renders the three Nail candidates against a historical manual mask. It does not train a model.

Local checks: 43 focused tests passed. The actual generated notebook source hashes, original GPU archive and nested adapter/registry integrity passed CPU preflight. One existing 1600x1200 validation hand was rendered locally; all five nail components were edited and zero pixels outside the supplied mask changed. Local CUDA is unavailable, so portrait generation and the Kaggle installation/runtime remain **Needs verification**.

## Exact Kaggle steps

1. Open/import this file into a **separate private Kaggle notebook**:
   [beautycore_style_expansion_pilot_v2.ipynb](../../artifacts/style-expansion-20261025/beautycore_style_expansion_pilot_v2.ipynb).
   Preserve the existing working demo notebook. Use the reviewed notebook environment; importing alone does not establish that Kaggle retained it.
2. Enable Internet and the tested T4 GPU configuration.
3. Attach **one** dataset input containing `capstone_train002_20260928_v1.bin`. Use the original unchanged GPU bundle. The CPU bundle is not needed. No API Secrets are required.
4. Run the first code cell. It prints the bundle match count and a unique STYLE_PILOT_WORKSPACE. If the count is zero, attach the correct GPU dataset; if greater than one, detach duplicate inputs. Visibility can be public or private if accessible. No source is overwritten.
5. Run the second code cell once. It checks the original bundle and reviewed environment, installs pinned dependencies, downloads the pinned foundation, then runs the renderer and portrait experiments. It prints STYLE_PILOT START/DONE for each of 15 portrait calls.
6. Wait for completion. Download `beautycore-style-expansion-results.zip` from the unique folder printed as DOWNLOAD_RESULTS. The notebook also packages partial evidence if setup or generation fails.
7. Return that ZIP for review. It contains comparison sheets, outputs, prompts/adapter provenance, timings, peak GPU allocations, setup diagnostics and restoration results. Keep the notebook and ZIP private: they contain reused evaluation imagery.

Setup and model downloads take time. The case count is bounded, but there is no completion-time guarantee. Do not start another copy or repeatedly run the execution cell. A new run needs a new preparation workspace; the script refuses to overwrite earlier evidence.

## If a check fails

- Active service detected: use a separate session; do not stop the client's working demo merely to test.
- Host mismatch: preserve the check and inspect `setup-evidence/host.json`. Expected reviewed host is Python 3.12.13, Torch 2.10.0+cu128, CUDA 12.8 and Tesla T4. Do not upgrade/downgrade packages blindly or remove the guard.
- Installation/model failure: note the last printed stage; send the partial ZIP. Do not add old recovery cells from the demo notebook.
- Portrait failure: already completed cases and report remain in the partial ZIP. No automatic retry or service restart is performed.
- Restoration mismatch: do not promote the candidate; compare initial and final old-style outputs and inspect adapter state.

This notebook creates no public tunnel, registers no endpoint and makes no Render changes.

## How results will be judged

Compare each candidate with the original input and closest old styles. Check recognizable identity, face proportions, source hair color, background preservation, intended style details and visible distinction from the existing catalog. Candidate Hair prompts run on both verified adapters without pretending either was trained for a new label.

Nail prototypes use manual masks to isolate rendering quality. They do not test automatic hand localization, segmentation, uploaded photos or the full live Nails route. Raspberry Jelly must retain nail detail, Pink Aura needs a central glow, and Micro-Dots must stay inside each nail.

Fifteen calls are feasibility observations, not a statistical speed benchmark. One reused portrait per feature and one reused hand cannot establish generalization. The earlier identity-held-out origin of a fixture does not turn this pilot into an independent new evaluation set. After obvious failures are addressed, repeat accepted designs on varied consented photos and the actual masking pipeline.

## After review

Choose prompt/adapter combinations that visibly work. Collect correctly labeled, permissioned paired examples only for remaining gaps, then decide whether fine-tuning is necessary. No new training images were collected in this step. All training rights, salon-specific offerings and design surcharges still need confirmation.

Only accepted candidates will later receive public style IDs, consultation tags, service/price mappings and a versioned deployment package. Existing saved looks, model contracts, Nails-only caching and the working deployment remain intact.

Maintainer checks: `python -m pytest backend/tests/test_style_expansion.py backend/tests/test_registry_expansion.py backend/tests/test_nails_hybrid.py backend/tests/test_generation_benchmark.py -q`. The private packager is `scripts/package_style_expansion_pilot.py`; choose a new output filename for a new version.


## Confirmed v1 scratch failure and recovery

The returned v1 ZIP confirms setup/artifact checks passed, then a 30 GiB free-space guard stopped before any model download. The cache had been placed on the working volume. Use the guarded [same-session recovery](style-expansion-scratch-recovery.md) to preserve installed dependencies and old logs, or the v2 notebook for a new session. Scratch location is now chosen by actual free-space checks; the original threshold/model guards remain.49focused tests pass; new GPU results remain pending.
