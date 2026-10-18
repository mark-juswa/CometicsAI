# GPU prompt-reuse comparison review

2026-10-18, Asia/Manila. **VERIFIED for the supplied bounded worker comparison; full application acceptance NEEDS VERIFICATION.** User returned the completed private benchmark ZIP. No additional GPU run, model/config change, migration or deployment was performed during this review.

## Observed results

| Approved case | Paired samples | Baseline median | Candidate median | Observed median reduction |
| --- | ---: | ---: | ---: | ---: |
| Crew Cut | 3 | 65.005 s | 56.642 s | 12.86% |
| Natural Makeup | 3 | 65.653 s | 56.431 s | 14.05% |
| Classic Red, one nail crop | 3 | 37.475 s | 29.055 s | 22.47% |
| Bun | 1 | 65.162 s | 65.708 s | -0.84% (slower) |
| Glossy Black, one nail crop | 1 | 37.929 s | 36.682 s | 3.29% |

The three-pair cases include one cold-cache candidate run and two runs reusing encodings. Candidate reuse times were Crew Cut 56.642/56.355 s, Makeup 56.431/56.361 s and Red crop 29.055/28.570 s. Each reused run recorded two cache hits and no misses. Cold candidate times were respectively 65.500, 65.238 and 37.207 s: there is no consistent first-use speed gain. Bun and Black have no reuse sample, so their one-pair observations are coverage rather than established speed conclusions. New clients/photos may use an already cached public prompt, but this fixed-input experiment does not establish other-photo quality or total website latency.

The artifact reports Tesla T4, Torch2.10.0+cu128, CUDA12.8, one foundation load and 70.650 s model startup. Both sides retain the approved model/adapter hashes, seed1977, guidance4, 512x512 inputs and 20 Hair/Makeup or8 Nails steps. No lower-quality settings were used to obtain these results.

## Independent validation and image review

The ZIP passed CRC and exact-inventory checks: one report and22 PNGs. All reported PNG and RGB hashes were recomputed. All eleven paired before/after PNG files are **byte-for-byte identical**, and independent decoded pixel comparisons also match exactly. Repeated baseline images for the three-sample cases are identical. Input hashes match the original private approved GPU bundle. Summary medians and percentages were independently recomputed.

Representative Crew Cut, Bun, Makeup, Red crop and Black crop outputs were opened for inspection. The candidate preserves these exact baseline results; that does not prove baseline aesthetics are ideal or generalize to other photos/styles. Nail crops remain soft/smooth and are not full-hand final composites. Raw portraits/generated images are not committed; the uploaded private ZIP remains the original evidence. The committed raw report contains timing/model metadata and image hashes, not image bytes.

Source ZIP SHA-256: `26e0775c09a687ecf0eba4beeb6e75aada04bc7114ce9c807d61525c812c5549`. See [raw report](generation-speed-benchmark-20261018-report.json) and [structured review](generation-speed-benchmark-20261018-review.json). The ZIP does not contain setup logs/host.json or executed overlay hashes, so those are not independently attested by this artifact.

## Bottleneck and limits

Separately synchronized diagnostic warm-ups attribute approximately73–85% of worker runtime to the model's repeated image-generation/denoising loop. Prompt encoding is approximately2.8–3.7 s in those warm-ups, while decode is approximately6.2–6.8 s. Cache-hit whole-runtime gains are about8–9 s in these samples; do not equate that entire gain to the isolated prompt timer or assume all offload/scheduling effects have been explained. Timed pairs omit per-phase synchronization barriers.

This is a useful bounded improvement, not instant generation. Twenty-two timed generations sum to1158.287 s (19.30 minutes), excluding five diagnostic warm-ups, model startup, downloads and other setup. Gross session duration was not measured by the report.

No five-nail complete hand, localization/refinement/compositing, renderer style, Render/browser/network time or three-look Consultation run is present. Do not call29 seconds a full Nails request, multiply it into a claimed five-nail result, or promise the same percentage to every request. There are no percentiles or broad statistical/generalization claims from three pairs.

## Adoption decision

**The candidate passes this worker output-equivalence and limited repeated-use timing comparison.** It is suitable for the next isolated application rehearsal. It is not yet enabled in the working demo. Before adoption, verify full-hand Red/Black masks/composites/all nails/outside-mask pixels, Hair restoration after adapter changes, Makeup, renderer styles and Consultation with actual time to first/all results. Existing tests and the production build passed in the implementation phase; no code changed during this report review, so they were not needlessly rerun.

The earlier instruction **do not deploy to Render** remains in force. No live database, Render settings, demo notebook/bundle or runtime flags were changed. The next application rehearsal should preserve the working fallback and does not require repeating this entire27-generation worker benchmark.
