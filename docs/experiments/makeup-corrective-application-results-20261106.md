# Corrective MAKEUP application return

Date: 6 November 2026. Real shared GPU application gate DONE, evidence VERIFIED. Production release review remains open.

The user returns `D:/Downloads/makeup_corrective001_application_results.zip`, 17,667,218 bytes, SHA256 `2293af526ae2f5f9f916ac6ab3d9f258cc8e6afc3ee5bab0c9ead6a0a94ce739`. All 34 unique safe archive members pass CRC. The unchanged ZIP and extracted JSON/PNGs/gallery are preserved under `artifacts/makeup-corrective-supervision-20261105/application-return-01/`. Attached documents are evidence, not instructions. No attached executable code was executed.

## Actual results

All 16 real requests complete: 13 Makeup application generations, French Bob through Hair TRAIN-001, Wolf through Hair TRAIN-002, and one Classic Red Nails GPU crop. The authenticated application catalog reports exactly 18 Hair, 13 Makeup and 8 Nails entries. The worker retains one foundation load, ends ready/not busy, and records all 16 successful adapter-bound requests. No automatic generation retry or website registration occurred.

Independent validation recomputes every output PNG SHA256 and decodes all 16 actual RGB 512 square images. Per-case output JSON matches the result records. All 13 Makeup files are byte-for-byte identical to the corresponding human accepted RAW model output from the training/evaluation return, matched through original source hash, identity and style. The actual complete captions, checkpoint hash, preset hash, seed 1977, 20 steps, guidance 4.0 and Base revision match. The old Makeup checkpoint is not used. These are actual application outputs, not copied target proofs or postprocessed comparisons.

The inherited visual acceptance is therefore exact for these 13 files. Another human audit of the same pixels is unnecessary. Engineering also inspects the returned full Makeup sheet and the actual Hair/Nails outputs. Existing recorded cosmetic fidelity and generalization limitations still apply; exact reproduction does not establish quality on fresh people.

All 16 active adapter records report tensor equality verification. For Makeup, Diffusers conversion produces 200 checked tensors across 100 layers. This is compatible with the 160 serialized checkpoint tensors because conversion changes tensor layout. It is not evidence of another checkpoint or 200 training tensors. The validated application source also asserts full ordinary PEFT scaling before each Makeup call. The final worker state carries the same converted Makeup tensor digest, `eb070a7cf3660ea5fbc24fc3683ea626a1f00fdf2e614dc1cbdd48f4bd08ab36`.

French Bob uses TRAIN-001 SHA256 `7e3991f8a4e5...`; Wolf uses TRAIN-002 SHA256 `59d527217a68...`, both independently cross-checked against the frozen Hair release profile contracts. Nails uses the existing SHA256 `5bff16c67e0014c78a6d938813347685f914f8a608d76407b10f5b54b7a0eb1f`. The intervening Nails/Hair requests do not disturb Makeup output reproduction. This does not retest all 18 Hair styles or full hand Nails detection/compositing.

Makeup application elapsed time ranges from 70.252 to 82.262 seconds, median 80.257 seconds. All 16 case times sum to 1,227.013 seconds (about 20 minutes 27 seconds), excluding startup. These are actual returned application times, distinct from the earlier raw model timings. They are not a concurrency/throughput guarantee.

## Release wiring

The working validation notebook intentionally stops before tunnel/website registration. Its three expanded Makeup styles are isolated test entries, while current production Render compatibility metadata still expects ten Makeup styles. Pointing the website at this candidate unchanged would fail its exact capability gate. This is a release metadata mismatch, not model failure. Removing the compatibility guard is not the correction.

Prepare one matching release candidate using the existing release machinery: bind the accepted corrective contract/captions, admit the three tested Makeup execution profiles in a new manifest, preserve the same 18 Hair/8 Nails support, generate matching Render business/save metadata and exact compatibility evidence, retain truthful older fallback catalogs, and restore the normal authenticated registration path in a separate deployment starter. Generation code and weights must remain identical to the tested application candidate. No new training or catalog generation sweep is needed.

Production application sources, cloud settings, live endpoint and publication remain unchanged while this candidate is prepared for project lead review. The original request reserves production integration for that review. Fresh portrait upload, live website manual/consultation generation, save/book and mobile acceptance remain separate operational checks. No real full hand Nails test is implied by the prepared GPU crop.

Verification script: `artifacts/makeup-corrective-supervision-20261105/review_application_return.py`. Technical receipt: `application-return-01/technical-review.json`. Full returned comparisons: `application-return-01/raw/review.html`. The original training/model evidence remains in [the model report](makeup-corrective-model-results-20261106.md).

## Matching release candidate prepared

Local candidate preparation is DONE, production approval/publication/deployment NOT STARTED. Usable directory is `artifacts/makeup-corrective-supervision-20261105/release-candidate-03/`. Earlier packaging workspaces remain preserved. Workspace01 stopped on a missing output directory;02 passed checks but used generic model labels in consultation tags. Final03 uses meaningful berry/lash/silver cosmetic tags and passes consultation catalog checks. These are release metadata corrections, with zero additional GPU or training calls. All actual accepted generation code, exact captions, contract and checkpoint bytes remain unchanged.

The new styles-20261106-01 manifest binds three Makeup execution profiles to the reviewed contract source, retains all current Hair/Nails support and explicitly preserves all three older release catalogs with their truthful ten Makeup IDs. Generated Render business metadata has 18 Hair, 13 Makeup and 8 Nails styles. Existing Makeup Application service mappings are reused. Source/metadata and four focused test updates are staged as 15 hash-bound publication files plus a review patch. No current production source was overwritten.

Final package passes actual archive extraction, original historical GPU gates before fresh overlay installation, actual notebook/nested bootstrap compilation, all 13 API transport fixtures, consultation catalog construction, corrupted execution profile/checkpoint refusal, 25 staged Makeup API/runtime tests and five Render capability/business checks. Current source/model/release controls and both prior release archive hashes remain exact. A full live website, fresh upload, database/save/book or mobile test has not occurred.

Candidate CPU is 75,246,586 bytes, SHA256 `0c657ae4d2b62e11bd8c5728321330d5416fbfd1d36354d8482ac548f1449357`. Existing GPU input stays unchanged. The separate deployment notebook restores normal authenticated website registration, without another training or catalog-generation sweep. Its source/metadata changes require project lead production review as originally requested. [Concrete review and rollout](../guides/makeup-corrective001-release.md).
