# Full-hand and Consultation generation comparison

2026-10-18, Asia/Manila. **Execution and output preservation VERIFIED. Global cache performance acceptance FAILED for the supplied sequence.** No production change was made during this review.

The user returned the completed private application ZIP, SHA-256 `ff67ec497d3181594db154fae1bbffbf486577b862e6fe32b9285c324cb938b5`. Its source overlay hashes exactly match the prepared notebook. Returned host/resolved packages/Diffusers commit and model-index hash match the reviewed runtime. Approved input hashes match the immutable bundle and reviewed1600×1200 hand.

## Actual observations

Each row is **one paired observation**, not a median or universal service-level promise.

| Case | Baseline | Candidate | Observed outcome |
| --- | ---: | ---: | --- |
| Bob Hair | 64.10s | 70.12s | 9.38% slower |
| Bun | 62.11s | 72.12s | 16.12% slower |
| Crew Cut | 64.11s | 70.13s | 9.39% slower |
| Natural Makeup | 64.11s | 72.13s | 12.51% slower |
| Crew Cut restored after Makeup | 66.13s | 62.11s | 6.08% faster |
| Classic Red, full five-nail hand | 196.35s | 172.31s | 24.04s /12.24% faster |
| Glossy Black, full five-nail hand | 194.35s | 162.31s | 32.04s /16.49% faster |
| French Tip | 10.02s | 10.02s | Approximately unchanged |
| Nude Pink | 10.02s | 10.02s | Approximately unchanged |
| Pink Ombre | 10.02s | 10.02s | Approximately unchanged |

Hair Consultation's time to all three results rose190.40→212.46s (22.05s slower). Its first result rose64.13→70.15s. Nails Consultation's Red/French/Black sequence fell401.16→345.06s (56.10s /13.99% faster); first result fell196.50→172.45s. These intervals include the local polling/checks in the test driver, not a live browser or Gemini conversation.

The total supplied sequence fell741.32→711.28s, but that aggregate hides Hair/Makeup regressions and is not a valid reason to enable the cache everywhere. Earlier worker-only medians describe repeated uses of one fixed prompt; these new results show why they do not predict every new-style application request.

## What passed independently

- ZIP CRC, exact source attestation, reported environment/model-index and approved source hashes.
- All20 result PNG hashes and decoded RGB hashes. All10 paired generated images are byte-for-byte and pixel-for-pixel identical; all five pairs of full-hand masks are byte-identical.
- All10 full-hand results preserve every pixel outside their actual final mask. Each mask has five separate nail components, and all five contain changed pixels. Independent component edit counts match the reported finger counts as multisets.
- Expected30 model calls: five per Red/Black full hand, one per Hair/Makeup request, none for renderer styles. Both modes report one loaded foundation and ready state at the end.
- Hair restoration after Makeup returns the same Crew Cut PNG within both modes. Both Hair/Nails three-look consultations completed and selected a completed result. The known attested script also contains mandatory missing-auth, wrong-owner and busy-admission assertions before completing.
- Completion and graceful shutdown of the owned worker appear in the returned logs. CPU requirements checks report no broken requirements; an inherited sitecustomize/wrapt warning is nonfatal and is not evidence for the timing difference.

Original, Red, Black and French full-hand images were opened for inspection. All five nails show the requested changes. The existing soft/smooth model finish and angular thumb mask remain visible; caching preserves the baseline exactly rather than improving its aesthetics. Private image bytes and raw setup logs are not committed. See [raw non-image report](application-rehearsal-20261018-report.json) and [structured review](application-rehearsal-20261018-review.json).

## Decision

**Do not enable global prompt caching.** Recommend a scoped opt-in policy for model-based Nails only, leaving Hair/Makeup on their original path. This also benefits model-based Nails when invoked by Consultation. Renderer styles bypass the model and should retain their existing behavior.

The reason is concrete: new Bob/Bun/Makeup requests each missed both prompt encodings and were slower; restored Crew hit both and was faster. A full Red hand populated encodings on the first crop, then had two cache hits for each of the next four crops. Black reused its negative encoding on the first crop and both encodings on the next four. This is consistent with reuse benefiting consecutive nail crops. The fixed-order single pair cannot isolate all CPU-copy/offload/hardware/load effects or establish an exact cause for every slower sample.

The scoped policy is a recommendation in this review, not an implemented or newly GPU-tested serving change. The current working demo's flags, notebook/bundles, Render deployment and live database remain unchanged. The previous no-Render-deploy instruction remains active. No additional full benchmark is required merely to interpret these results.

Still Needs verification: broader hand/style/photo coverage, any future scoped-policy integration/activation, live Next.js/browser/client-device acceptance and Gemini conversation flow. The returned rehearsal uses the existing deterministic recommendation provider and does not test three-look Makeup Consultation or the new saved-look/pricing database/UI changes live. Those limits must remain explicit in a release handover.
