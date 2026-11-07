# Hair expansion result review — HAIR-EXP-002

Date: 31 October 2026  
Execution/integrity: **VERIFIED**  
Visual review: **DONE by Codex; client acceptance PENDING**  
New Hair styles enabled: **0**

## Verified run

All21image calls completed on the reviewed Tesla T4 environment using one foundation. Frozen experiment sources, plan/settings, four original JPEGs/decoded source PNGs, all21output PNG/RGB hashes and normalized-source hashes match. The checkpoint claims, active200tensors across100LoRA layers and full1.0scaling are consistent with the original runner/plan. TRAIN-001 → TRAIN-002 → TRAIN-001 restoration reproduces the first control exactly, including PNG bytes. No runner/profile mismatch was identified.

The16,571,514byte ZIP has54members, passes CRC/path/duplicate guards and SHA2563e3474b98823247b471964de173223ae6eb314af34cdaafc486012ee88cae1db. Original ZIP/source/log/report/image evidence is preserved under artifacts/hair-expansion-20261031/review-01.

Total per-image processing was1367.76seconds, about22minutes48seconds; range61.57–66.13seconds, median65.46seconds. Foundation load was51.83seconds separately. Peak allocated CUDA memory8304.31MiB is not total/reserved device memory. These observations exclude setup/download and are not a website benchmark or a before/after speed comparison.

## Appearance findings

| Style | Observed result | Disposition |
|---|---|---|
| Butterfly Cut | Long sources become smooth short bobs with bangs. Long lower lengths and Butterfly layers are absent. Blonde source becomes black. | Hold. |
| Textured French Bob with Wispy Bangs | A distinct curly rounded bob with separated fringe appears on both inputs. Stronger curl interpretation and blonde-to-black change remain. | Closest candidate for client/stylist review; keep disabled pending acceptance/limits. |
| Wolf Cut | Longer back and short crown appear, but hair becomes extremely spiky/stiff and scene/punk-like. Blonde source becomes black. | Hold. |
| Korean Two-Block | Dense rounded fringe, including eye coverage; clear shorter lower-side separation is not established. | Hold. |
| Korean Comma Hair | Previous detached loop is reduced. Still close to Curtain Hair; color example crosses eyes/nose and distinct comma styling is inconsistent. | Hold. |

These are qualitative visual findings on two reused sources per style, not salon approval or numeric biometric/skin measurements. Several baseline results also recolor/smooth the source. Those are broader existing preservation limits, not solely new-prompt defects. Correct runtime/tensor checks do not establish appearance success.

Do not silently relabel the failed Butterfly or treat the French Bob's curly interpretation as approved. Current tested profiles fail or remain qualified; this does not prove that every possible prompt/adapter must fail or that retraining is now mandatory.

## Review files and next step

[Open the self-contained gallery](../../artifacts/hair-expansion-20261031/review-01/results/review-self-contained.html) in Edge or Chrome. It contains original/baseline/candidate comparisons for all five styles. Returned HTML reproduced exactly from trusted local gallery code; Edge loads all30images, opens enlarged images, fits390pxviewport and reports0script errors. The original30PNGdata references are embedded; there are no sibling-image dependencies.

[French Bob comparison](../../artifacts/hair-expansion-20261031/review-01/results/exp_french_bob_wispy-comparison.jpg), [per-case Codex review](../../artifacts/hair-expansion-20261031/review-01/review-by-codex.csv), [machine receipt](hair-expansion-results-20261031-review.json).

Recommended next step: review the exact French Bob results and their limits with the client/stylist; keep the other four held. No automatic production enablement, new GPU sweep or training is started by this review. The accepted three Nail designs can continue their independent release path without claiming Hair expansion is complete.

No application/model/preset/checkpoint changes, new inference/training or deployment were performed in this review. The approved Nail manifest, generated evidence, business catalog and prepared notebook hashes are unchanged. The Hair evidence is recorded separately so the already-built immutable Nail package is not invalidated by a review-status edit.
