# Offline Makeup tone correction — 25 October 2026

**Implementation/execution DONE; technical invariants VERIFIED; appearance EXPERIMENTAL. Not integrated or deployed.**

## Result

Six existing saved results were compared: Natural Makeup, Classic Red Lip and experimental Berry on two reused development people. Four were adjusted; two fair-complexion results were intentionally unchanged because their neutral forehead lightness gaps were below the fixed 2 Lab-L guard.

The darker-complexioned subject has visibly warmer, less pale foundation after correction. Visible lip and eye Makeup remains. This is **partial improvement**, not a complete naturalness fix. Excessive blush, smoothed skin, facial/smile changes and some pale brow/perioral transition persist. The lighter-complexioned subject also shows that a result can look unnatural even when the sampled forehead is not much lighter.

No whole-dataset expansion, new images, external downloads, retraining, GPU generation or deployment was required. The same saved input/output files remain byte-identical.

## Exact method and evidence

- [Prototype](../../scripts/makeup_tone_correction.py), [original plan](../../data/makeup/MAKEUP-TONE-001/plan.json), [boundary-corrected plan](../../data/makeup/MAKEUP-TONE-001/plan-mask-v2.json).
- [Machine-readable verification/review](makeup-tone-correction-20261025.json).
- Cached jonathandinu/face-parsing weights/configuration hashes checked; CPU parsing used local_files_only. Eight maps: two originals and six raw results.
- Manually specified, visually inspected neutral forehead boxes; skin-only samples with highlight/shadow trimming. No validated automatic region-selection claim.
- Calculate source-minus-output Lab offset. Apply only for excess positive lightness gap, bounded to 16 L and chroma-vector length 8; no brightening when original is lighter.
- Operate on generated skin/nose geometry with inward feathering and semantic feature protection. Lip, eyebrow, eye, mouth/teeth and other protected pixels remain exactly raw RGB. Eyelid/cheek skin tones can change with the foundation correction; their entire cosmetic regions are not claimed pixel-identical.
- Fitted forehead gap reduction is an implementation diagnostic, not an independent skin-quality score or proof of generalization.

Private original/raw/corrected sheets and native PNGs: artifacts/makeup-tone-20261025/run-02.
Local review ZIP: artifacts/makeup-tone-20261025/beautycore-makeup-tone-review.zip. Includes source credits, raw/corrected files and verification; contains no model weights, secrets or deployment configuration.

## Initial mask failure and correction

run-01 retained the raw orbital regions with rectangular exclusion boxes. This caused conspicuous pale boxes and failed visual review. The failure, original plan and runner snapshot are preserved.

run-02 uses the same eight parser maps, six raw images, tone estimator and tone caps. It replaces rectangular exclusion with small semantic-feature margins and a smooth distance transition. Both full sheets, region overlays and two native corrected images were inspected. The boxes are gone; residual appearance problems are recorded rather than hidden. No further parameter sweep was run.

## Validation

Command: python -m pytest backend/tests/test_makeup_tone_correction.py backend/tests/test_makeup_corrective_review.py -q

**32 passed: 14 new tone checks + 18 existing audit checks.** Tests cover capped correction, no-op for matching/darker faces, protected pixels, invalid/insufficient regions, tampered inputs, offline-only flags and evidence overwrite refusal.

Independent saved-PNG checks across all six cases confirm:
- Zero changed pixels outside the allowed mask.
- Zero changed protected semantic-feature pixels.
- Both skipped cases are pixel-identical to raw results.
- Original source, raw outputs, input report and cached labels match frozen hashes.
- No diff in the four production Makeup inference/contract files checked.

No online performance benchmark or universally accurate mask is claimed.

## Review and next gate

The project owner should review both sheets and decide whether the change is a useful visual improvement. Existing accepted source images are reused development inputs; no untouched generalization acceptance is established.

Do not deploy this prototype directly. Its neutral regions are manually specified for these two people. If the appearance is worth pursuing, the next separately scoped task is automatic neutral-region reliability and broader representative evaluation before compatible serving integration. If it remains unacceptable, record the limit instead of continuing cosmetic parameter sweeps or silently retraining.


## Human review follow-up — 26 October 2026

The Supervisor explicitly rejects the displayed Natural054109 v2 output: the face still visibly resembles a mask and blends poorly. This supersedes pending acceptance for that case. Native raw/corrected inspection confirms that the raw model already produces a retouched face; the skin-only adjustment leaves pale feature-adjacent zones against warmer skin. Exact boundary invariants and improved fitted forehead statistics do not constitute appearance acceptance.

Hold serving integration of this prototype and do not automatically continue mask/strength sweeps. Other five cases have no new explicit human verdict. No image, model, serving or cloud change was made for this feedback. [Separate rejection record](makeup-tone-mask-rejection-20261026.json).
