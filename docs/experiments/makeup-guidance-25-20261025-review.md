# MAKEUP-QA-003 guidance 2.5 review — 25 October 2026

**GPU execution/provenance VERIFIED; visual review DONE; no release setting selected.**

Guidance 2.5 keeps lipstick, lashes, brows and cheek color clearly visible. It does not make the makeup disappear. Its appearance is very close to 3.0, with small changes in tone/details; this review finds no consistent additional naturalness or complexion-preservation win across the four comparisons. The face remains much lighter and smoother than the darker source, and the lighter source retains glossy retouching and altered facial details.

The Supervisor's earlier observation that guidance 3.0 looks softer/more natural than matched-foundation wording is valid as a relative preference. It does not establish that either 3.0 or 2.5 fixes whitening. This narrower comparison gives no clear reason to automatically replace 3.0 with 2.5.

## Comparison

| Guidance | Result on the reviewed cases |
|---|---|
| 4.0 | Strong existing glam/retouched appearance with pale highlights, smoothing and heavy cheek styling. |
| 3.0 | Some softer detail relative to 4.0 and prior human preference over matched-foundation text. Still materially altered complexion/texture. Provisional comparison candidate, not release acceptance. |
| 2.5 | Makeup remains clear. Very similar to 3.0; minor changes do not consistently restore original complexion/texture or establish a better setting. |

Both Natural Makeup and Classic Red Lip remain visibly made up. Red Lip retains a vivid lip color, but full-face smoothing/lightening and extra cheek/highlight edits persist. Natural still looks like heavier glam rather than the restrained everyday request.

These are qualitative Codex observations, not a quantitative skin/identity score or salon acceptance. All four new RGB hashes differ from the corresponding 3.0 reference; output files are new, but file/pixel differences are not quality improvements.

## Verified execution

The 4,771,605-byte ZIP passes CRC, duplicate/path guards, exact source/plan hashes, prior report byte/hash matching, all 12 case settings/prompt/PNG/RGB/source-image checks and exact pinned environment checks. Archive SHA256: 01832128682ba72b9f3935f4186ea413da154693fe516431f8fa7b04ba528c07.

All eight retained 4.0/3.0 rows and image files match earlier verified results byte-for-byte, with recorded condition remapping. The one repeated guidance 3.0 control matches both the saved PNG and decoded pixels exactly. This is not a rerun of all eight references.

The same checkpoint and verified tensor state remain; 100 loaded LoRA layers keep full 1.0 influence and restore successfully. Original prompts, seed 1977, 20 steps and 512 x 512 framing are unchanged. No masks, blending or recoloring were introduced. No bundled code was executed during this review.

Five new forwards (one control plus four at 2.5) total 312.94 seconds, about 5 minutes 13 seconds. New child foundation loading is 48.13 seconds separately. Environment checks, encoding, sheets and ZIP creation are excluded. The model/packages were reused without download/reinstall. Median 2.5 case time is 63.75 seconds versus retained 3.0 median 63.79 seconds; these single observations across processes do not establish a speed improvement.

## Recommendation — PROPOSED

End this bounded guidance comparison here; do not automatically continue to 2.0, 1.5 or a combined parameter sweep. Keep the existing deployed settings unchanged. Guidance 3.0 can remain the human-preferred comparison candidate; 2.5 has not established a clear further benefit or a complexion fix.

If further correction is desired, review the existing paired targets and make a concrete keep/reject/replacement list before additional GPU experiments. Require visible intended makeup together with original complexion/undertone, plausible texture and recognizable face/smile geometry. Only then propose a bounded corrected-data fine-tuning experiment and preserve the current checkpoint as baseline/fallback. Foundation-only also over-edited, so retraining success is not guaranteed.

No training, dataset change, serving code change, deployment, automatic selection or additional image generation starts from this review.

## Private visual evidence

Columns: **Original / Guidance 4.0 / Guidance 3.0 / Guidance 2.5**. Each sheet has the same two source people in separate rows.

- [Natural Makeup comparison](../../artifacts/makeup-quality-20261025/guidance-review-d2f303a097/results/natural_makeup-comparison.jpg)
- [Classic Red Lip comparison](../../artifacts/makeup-quality-20261025/guidance-review-d2f303a097/results/classic_red_lip-comparison.jpg)
- [Per-case visual observations](../../artifacts/makeup-quality-20261025/guidance-review-d2f303a097/review-by-codex.csv)
- [Verification receipt](makeup-guidance-25-20261025-review.json)

The exact input ZIP, source reports, logs and raw PNGs remain in the ignored private artifact directory. Render and the deployed model are unchanged.


## Human selection after review

On25October2026the Supervisor reports the latest result looks much better and explicitly chooses **guidance2.5** when asked2.5versus3.0. This supersedes the provisional3.0candidate preference. Earlier independent visual findings remain recorded; they do not override this explicit selection. Production code/settings and deployment remain unchanged. [Selection receipt](makeup-guidance-selection-20261025.json).
