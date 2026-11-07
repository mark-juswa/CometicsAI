# Hair expansion comparison prepared — HAIR-EXP-002

Date: 30 October 2026  
Preparation: **DONE**  
GPU evaluation: **NOT STARTED**  
Appearance: **UNKNOWN**  
Production enablement: **0 new Hair styles**

The Supervisor says "lets proceed to haircut" after the approved Nail release is prepared. This continues the approved Hair expansion scope; it is not acceptance of earlier held Hair outputs.

## Evidence and comparison design

The earlier Butterfly trial used a short-bob source, which did not establish long-layer capability. Two-Block lacked convincing lower-side separation. Comma's later release test produced ring/U-shaped fringe and color changes; that later failure overrides the initial promising pilot. Wolf and French Bob had not been tested.

Inspected the existing DATA-002 source archive and a labeled contact sheet of its twenty historical validation photos. Selected d2_wavy_hair_25jpg and d2_wavy_hair_27jpg for visible loose long lengths, plus d2_side_part_undercut_28jpg and d2_side_part_undercut_9jpg for visible sides/three-quarter framing. The last source is grayscale: color fidelity remains unassessable there. These are reused development examples, not untouched final tests. Source revision, archive/member SHA256, declared license and unresolved original-photo-rights limitation are in the frozen plan. No new photos were fetched.

Exactly21calls:10candidate images,10nearest-baseline controls and1restoration control. Butterfly/Layered and French-Bob/Bob use TRAIN-001; Wolf/Shag, Two-Block/Side-Part and Comma/Curtain use TRAIN-002. These are bounded test choices, not selected production winners. Butterfly/Two-Block keep prior prompts on suitable inputs. Comma receives one strand/geometry-focused prompt correction. Wolf/French Bob are first tests.

Preserve original foundation/checkpoint bytes, exact training-label guards, full adapter influence, guidance4.0,20steps,seed1977 and512square generation. One foundation, serialized adapter switching and generic tensor/scale verification. The final control must reproduce its first pixels after TRAIN-001 → TRAIN-002 → TRAIN-001. Use no_grad to avoid the earlier lazy offload/inference-tensor switching failure. Candidate output truthfully identifies an experimental prompt using an existing adapter.

Prior roughly64second observations suggest about23minutes inference, plus setup/download. This is an estimate, not a benchmark result.

## Deliverable and verification

notebooks/hair_expansion_validation.ipynb embeds four photos and hash-checked runner/plan sources. It needs only the original capstone_train002_20260928_v1.bin input, a separate private pinned Kaggle T4 session and Internet. No CPU bundle, API Secrets, tunnel, registration or Render configuration.

The two-cell notebook retains exact original host/package/artifact preflight and scratch selection, streams image progress, bounds the process group to two hours and builds a ZIP even on failure. Results include original PNGs, reports/settings/timings/hashes, five comparison sheets, a self-contained embedded-image HTML gallery and manual review CSV.

**35 checks passed:**12new Hair checks and23related artifact/release checks. Real original GPU archive extraction and both checkpoint metadata/ownership guards pass in a new Python process, without GPU/model inference. Synthetic inference covers21cases, one foundation, three adapter states, exact-restoration check, corrupt-source refusal, failure evidence and self-contained reviews. Notebook source/asset hashes and timeout-group cleanup/partial ZIP pass. Existing catalog/generated-release checks pass.

The first real-artifact check caught local Windows versus frozen GPU registry byte differences. Fixed the plan to pin the original archive bytes; no guard was removed and no model file changed. The failed first draft is preserved under artifacts/hair-expansion-20261030/preflight-attempt-01.

Approved Nail manifest, generated evidence, business catalog and new release notebook hashes remain unchanged. No application serving code, trained weights, live database or cloud deployment changed. No GPU inference/training ran locally. Technical preparation does not establish haircut quality.

## Next

Run the private comparison and return beautycore-hair-expansion-results.zip. Review each style on both sources for fidelity, distinction from its baseline, face/expression, hair color and unwanted changes. Only individually accepted cuts can proceed to explicit production execution profiles and matching facade/GPU/application integration. All five Hair additions remain disabled until then.

[Run guide](../guides/hair-expansion-validation.md), [machine receipt](hair-expansion-preparation-20261030.json), [plan](../../data/style-expansion/HAIR-EXP-002/plan.json).
