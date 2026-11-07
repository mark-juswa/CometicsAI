# Makeup expansion result review — 31 October 2026

**Pilot DONE; technical evidence VERIFIED; visual quality EXPERIMENTAL. No Makeup appearance approval or deployment is inferred.**

## What completed

MAKEUP-EXP-002 returned all three planned calls: one Soft Glam control and Manga Lash on two reused source portraits. The control matches the saved PNG bytes and decoded RGB pixels exactly. The six saved Soft Glam, Berry and Icy Silver images are unchanged.

The 7,955,678-byte ZIP has 39 unique, safe members and passes CRC checks. Its SHA256 is 581f1c2abb2ddfb4812e6829c3e8206b0e1c648320d79f3fbada238949f59478. Frozen experiment source files, plan, source photographs, retained report, output PNG/RGB hashes, case matrix and prompts match. Reported adapter tensor equality and full scaling match the expected contract. Returned Python/package/CUDA/T4 environment and foundation model-index hash match the pinned records. Returned code was read as evidence, not executed.

The trusted local gallery function reproduces the returned HTML exactly. Edge loads all ten images, opens the original-size viewer, fits a 390px viewport and reports no script errors. Open [the self-contained review gallery](../../artifacts/makeup-expansion-20261031/review-01/results/review-self-contained.html).

## Appearance findings

Both Manga outputs show separated upper lashes, pink eye/cheek makeup and rose lips. The requested style produces a visible cosmetic difference.

However, the original problem remains. On source 054109, the generated face is substantially paler and smoother, with exaggerated lash spikes and retouched brows/facial details. Source 056266 also loses skin texture/freckling and receives a cooler, smoother complexion with changed facial details. These are qualitative comparisons against the same source photos, not calibrated complexion or biometric scores.

The retained Berry and Icy Silver outputs show the previously recorded complexion/retouching limitations. Adding the missing Manga test completes the three-style expansion's development test coverage; it does not establish acceptable quality or fix whitening. The previous Berry rejection is not superseded by submission of this ZIP.

## Performance and limits

- Soft Glam control: 62.81 seconds.
- Manga on 054109: 62.23 seconds.
- Manga on 056266: 63.96 seconds.
- Total three-call time: 189.00 seconds, about 3 minutes 9 seconds.
- Separate foundation load: 43.96 seconds.
- Maximum reported allocated GPU memory: 8,304.31 MiB, excluding reserved and other process/system memory.

One foundation was loaded. Existing MAKEUP-001 adapter at weight1.0, 20steps, seed1977, 512square and experimental guidance2.5 were used. The serving contract remains guidance4.0. These times exclude installation/download, web requests, queueing and application overhead. Two repeatedly reused portraits cannot establish generalization across clients.

## Release recommendation

Hold the new Makeup styles from public release until explicit client review. No accepted complexion-preserving fix has been demonstrated. Do not represent this style-coverage pilot as a successful whitening correction or start another parameter/model/rendering sweep automatically.

All five reviewed Hair appearances remain approved. All five Nail designs remain approved scope; Pearl Chrome and Cat-Eye still need implementation/testing. Their independent technical integration can continue without waiting for a Makeup correction. The sealed French Bob plus three Nails package and notebook remain byte-unchanged.

No serving code, catalog, weights, database, Git publication, Render deployment or live Kaggle server was changed during this review. Evidence and original ZIP are preserved under artifacts/makeup-expansion-20261031/review-01.
