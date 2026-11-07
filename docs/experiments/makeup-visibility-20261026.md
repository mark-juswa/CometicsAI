# Makeup eye/cheek visibility comparison — 26 October 2026

Status: **offline DONE / technical VERIFIED / appearance EXPERIMENTAL / user acceptance PENDING.** Integration NOT STARTED.

The Supervisor reports that the all-ten source-renderer examples look mostly like lipstick changes. Inspecting code and outputs supports an imbalance: eye pigment occupied a narrow band, and cheek tint was conservative. This does not prove that every style/input fails for the same reason.

## Bounded revision

MAKEUP-VISIBILITY-001 compares Soft Glam, Smoky Glam and Rosy Pink on four reused development portraits (12 new outputs). Originals, cached parser labels, baseline code and previous outputs are hash pinned. No new inference/GPU/download/training.

The runner uses actual source brow-to-lid space for a wider upper-lid field, soft crease and contour liner, plus bounded blush farther outward. All new layers stay on original skin pixels. A feathered exclusion preserves the entire previous mouth neighborhood **exactly**, so stronger lipstick cannot masquerade as improvement elsewhere.

Initial geometry overlays showed a sharp perioral exclusion edge. An inward fade was added before producing candidates; both overlay versions remain. Combined local Lab shifts are bounded to -16/+2 lightness and 40 chroma, with gamut compression. These are engineering bounds, not a guarantee of naturalness. Earlier baseline files remain unchanged.

## Actual evidence

- 19 new focused tests + 51 source-renderer regression tests: **70 pass**.
- All 12 saved PNGs reproduce exactly with the recorded runner.
- Zero changed previous mouth, protected-feature or outside-allowed pixels.
- Original/map/previous-code/output hashes match the frozen plan.
- Four complete comparison sheets inspected.
- Upper-eye pigment/definition stronger; cheeks restrained. Rosy Pink can appear saturated/high near the crease. Lip edge limitations intentionally unchanged.
- Zero client visual acceptances. No full-makeup, all-input or release success claim.

During test development, a missing-anatomy fixture incorrectly expected removal of just one lip label to fail; shared geometry accepts the combined lip region. The fixture now tests absence of both lips. Production geometry was not changed to satisfy that incorrect expectation.

## Review artifacts

artifacts/makeup-render-20261026/visibility-01/ID-comparison.png: Original / Previous / Non-lip revision. Rows: Soft / Smoky / Rosy. soft-glam-comparison.png is a compact single-row example.

artifacts/makeup-render-20261026/beautycore-makeup-visibility-review.zip: 43 members, CRC verified; includes candidates, previous images, originals, comparisons, plan, report, verification and source credits. SHA256: b03a4fb922322b23d08e11ce8ad3d4d01be6b1de643fd8516088b1c939ea5515.

Review eye intensity/placement, cheek visibility/edges and overall blend. Preservation checks cannot establish realism. Photos may already contain cosmetics and retain license restrictions; they are not bare-skin ground truth or representative customer testing.

## Scope and next gate

No serving/API/UI/catalog, dependency, model, price, Render or Kaggle changes. This is AI-assisted rendering, not a newly trained Makeup model. Remaining seven profiles and three trend candidates are not automatically revised/promoted.

Next: specific visual feedback, then broader suitable-input validation of accepted profiles before deliberate versioned integration and rehearsal. No unbounded strength sweep or declaration that all ten styles are fixed.
