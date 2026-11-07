# Corrective Makeup target review â€” 25 October 2026

**Review coverage/integrity VERIFIED; appearance judgments EXPERIMENTAL; independent human acceptance NEEDS VERIFICATION. Review DONE; model correction IN PROGRESS.**

The unchanged targets of all 60 finalized pairs were inspected against the stricter complexion-preservation criteria. **0 KEEP, 60 REJECT, 0 NEEDS_REPLACEMENT decisions; all 60 rejected targets need replacement before corrective reuse.** Counts are 50 rejected training pairs / 10 rejected validation pairs, representing 10 / 2 people respectively. Five variants are not five independent people.

REJECT means unsuitable for unchanged reuse in this correction trial under this Codex visual screen. It does not mean the source photos are unusable, erase historical approvals, prove the dataset caused every failure, or establish that all other images in the upstream collection fail.

## Evidence

- [Complete per-pair ledger](../../data/makeup/MAKEUP-CORRECTION-001/review.json): exact source/target hashes, identity/split, original credits/terms, historical review and specific new observation for each pair.
- [Machine-readable receipt](makeup-corrective-review-20261025.json): ledger/original manifest hashes, counts, evidence locations and checks.
- Private local comparisons: artifacts/makeup-correction-20261025/review-01; 12 source-plus-five-target sheets and five native-resolution pair comparisons. These photos remain private ignored artifacts, not copied into this document or released.
- Frozen source manifest SHA256: d75bbb096ca2dcc797dd26c9782104dde1952f637c4947246752b0acc4a802f4.
- [Preparation/validation utility](../../scripts/makeup_corrective_review.py) and [18 focused regression checks](../../backend/tests/test_makeup_corrective_review.py).

Original image hashes and captions were rechecked before recording decisions. Historical Project Lead ACCEPT entries remain intact under historical_review and the original manifest. That approval explicitly allowed minor smoothing under an earlier practical gate; it is not evidence that the targets pass the new stricter correction requirement.

## Method and findings

All 12 identity sheets were viewed. Five less-clear comparisons were additionally inspected at original 512-square size: 003681_makeup_04, 059106_makeup_05, 022625_makeup_05, 054109_makeup_01, 056266_makeup_04.

Targets have visible lip/eye/cheek cosmetics, but also complexion or illumination drift, erased skin texture, face/smile details changed, or unrelated clothing/hair edits. Some introduce freckles not present in the source. Even softer variants retain unwanted changes at native resolution. The ledger gives the individual observations; there is no invented numerical skin-quality score.

These visual findings support replacing the targets for corrective training. They do not isolate training causality: previous foundation-only results also over-edit. New data and fine-tuning remain a hypothesis to test, not a guaranteed fix.

## Gaps and next action

- Unchanged usable targets for the stricter correction trial: **0**.
- Existing 12 subjects cannot supply an untouched final acceptance set; the two validation identities have already been used repeatedly for development comparisons.
- Actual style labels and captions need review against new photos; historical makeup_01...05 positions are not style classes.
- No new train/validation counts or training schedule is invented before intake.

Supervisor chose **investigate replacement datasets** rather than salon photo collection. [Primary-source research and access-request draft](../research/makeup-replacement-datasets-20261025.md) are complete. No source yet passes pairing, quality and permission gates together.

No training, dataset replacement, source-image correction, serving-profile change or deployment occurred. Current Hair/Makeup/Nails models and Render/Kaggle packages are unchanged.
