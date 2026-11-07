# MAKEUP-QA-002 completed adjustment review — 25 October 2026

**GPU execution and returned provenance VERIFIED; visual review DONE; neither adjustment accepted for release.**

The cached-session experiment completed9new forwards:1current-control repeat plus8candidates. Its4saved controls are byte-identical to the prior reviewed outputs. The repeated control matches both saved PNG and decoded RGB hashes exactly. This supports continuity for that case, not independent reruns of all4controls.

## What changed and what the images show

| Condition | Intended change | Observed result on these inputs |
|---|---|---|
| Current reference | Original prompt, guidance4.0, adapter1.0 | Existing pale, smoothed, heavily retouched face and exaggerated cosmetics. |
| Lower guidance | Original prompt, guidance3.0, adapter1.0 | Small tonal/detail changes; complexion lightening and smoothing remain. Lip/eye makeup stays visible. Not an acceptable preservation correction. |
| Matched foundation | Original prompt plus frozen complexion/foundation instruction, guidance4.0, adapter1.0 | Still close to the current retouched appearance. Original complexion/texture are not reliably recovered. The requested visible makeup remains. |

On054109 the contrast between the original complexion and all3generated conditions is especially clear. Both presets still have a much lighter and smoother face. On056266 smoothing, highlights and heavy cheek/brow styling remain; the Natural result is still a glam retouch rather than restrained everyday makeup. Facial/smile details are not preserved exactly.

All8candidate RGB hashes differ from their corresponding current reference, so the comparisons are not merely duplicate output files. That difference is not a quality score. Both individual factors were actually recorded in the frozen source and output provenance; neither visibly meets the intended acceptance standard in this review.

We cannot claim that every possible prompt or guidance value will fail. However, the tested adapter reduction, lower guidance and extra complexion instructions have now failed to establish a deployable correction. There is no evidence here for replacing production settings or proceeding with arbitrary further reductions.

## Independent verification

The4,796,110byte archive has SHA256f898ab3ce27aec9d3778ecb728f77724eb3170251c91ab27c827d8f9e1cf7261. CRC, duplicate-name/path guards, exact embedded source/plan hashes, prior reference report bytes/hash, all12ordered case prompts/settings, source portrait pixels, PNG/RGB hashes and original/recovery source ownership pass. Tensor hashes match prior/current state;100LoRA layers retain1.0effective influence and restore successfully. Exact pinned Python/Torch/CUDA/dependency environment matches the reviewed image. No bundled code was executed during review.

The model/package cache was reused with no reinstall/download. Nine forward calls total566.36seconds (9minutes26seconds), plus43.15seconds of child foundation loading. Verification, encoding, chart writing and packaging time are excluded. Lower-guidance case median63.79seconds; matched-foundation median63.67seconds. Retained controls came from the older child; these observations are not a paired speed benchmark or website-latency measurement.

## Recommendation — PROPOSED next phase

Keep current production settings and the original demo fallback unchanged. Do not deployguidance3or the new prompt as a complexion fix based on this result.

Before another GPU experiment, review the existing paired targets and prepare a concrete keep/reject/replacement list. Accept targets only if makeup is clearly visible while original complexion/undertone, plausible texture and facial geometry remain. Do not treat these newly generated retouched faces as automatically suitable training targets.

Once usable pairs and truthful style captions are reviewed, propose a bounded corrected-data fine-tuning run and preserve the old adapter as baseline/fallback. Evaluate any new checkpoint on useful cosmetics AND preservation, with untouched people and varied complexion/capture conditions reserved for later acceptance. Foundation-only also over-edited in MAKEUP-QA-001, so training alone cannot be guaranteed to solve the full problem.

This review starts no curation, new image generation, data acquisition, training, masks/compositing/recoloring or architecture change. Prior failed preservation routes remain closed. Hair/Nails and the live Render/Kaggle serving system are unchanged.

## Private evidence

Columns: **Original / Current reference / Lower guidance / Matched foundation**.

- [Natural Makeup comparison](../../artifacts/makeup-quality-20261025/adjustment-review-ebdbe64f35/results/natural_makeup-comparison.jpg)
- [Classic Red Lip comparison](../../artifacts/makeup-quality-20261025/adjustment-review-ebdbe64f35/results/classic_red_lip-comparison.jpg)
- [Per-case visual review](../../artifacts/makeup-quality-20261025/adjustment-review-ebdbe64f35/review-by-codex.csv)
- [Verification and conclusions](makeup-adjustment-20261025-review.json)

All reports, logs, exact input ZIP and images are preserved in the ignored private artifact directory. The original ZIP remains untouched.
