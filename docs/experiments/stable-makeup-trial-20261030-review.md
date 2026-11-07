# Stable-Makeup trial return — 30 October 2026

**Runtime VERIFIED / visual screen FAILED / production unchanged.** Supervisor returns beautycore-stable-i3gf100o.zip. Archive is6,739,783bytes/32members, CRC passes, SHA25690d6a5ec5de34f3a3673d2a0d38fb22bbe49b6b80a161f7094228e4d1a2b0e86.

## Verified execution

All4outputs complete on TeslaT4, Torch2.0.1+cu117/CUDA11.7, vendoredDiffusers0.23.1, FP16,30steps,guidance1.6,seed1977. Returned plan equals frozen plan. All source/control/reference/output hashes and512RGBPNG dimensions pass independent checks. Six downloaded-asset receipts match the expected sizes and base-model hashes; observed full author-weight hashes are preserved in the JSON review for future pinning.

Per-image times12.2438,10.2944,10.4397,10.7007seconds; mean10.9197, median10.5702. These include generation and PNG/comparison writing, not website queue/network or request preprocessing. Model load17.5864seconds. Whole trial265.0430seconds (4.42minutes), including setup/download. Maximum allocated4.69186GiB, reserved4.90820GiB. This proves standalone T4 feasibility for this case only, not simultaneous memory fit with Hair/Nails or application speed.

No missing/unexpected-weight exception occurred with strict loading. Author source/control paths inspected; no concrete runner mismatch identified in this review. That does not establish causality for the appearance failure.

## Visual review

All4original/reference/output sheets inspected. Makeup is clearly visible, with coordinated eyeshadow, eyeliner, blush/highlight and lips; material rendering is fuller than the earlier custom-stroke experiment.

However, eyes, noses, lips/teeth display, expressions, face proportions and texture change substantially. Cases056266and035149 show pronounced reconstruction;054109and006553 also alter source features. Source complexion/lighting is not reliably retained. Reference-feature influence is suspected visually, not proven by ablation or biometric scoring.

**Codex release rejection on face/complexion preservation. Zero human appearance acceptances.** This is not an accepted personal virtual try-on result, all-style capability or a newly trained BeautyCore model.

The existing source/pretrained controls are correctly matched to the submitted portraits. Cosmetic visibility and runtime success do not compensate for altered identity/expression. Do not deploy raw results or silently revive old masked/tone/strength fixes.

## Next

Keep the live system and working demo unchanged. No automatic new GPU sweep, training, model/provider integration or catalog promotion. The agreed bounded test is complete and within its time budget. Any next corrective proposal must address source-feature preservation explicitly and account for the user's remaining deadline/free-only constraint. If no accepted correction is available, report the Makeup limitation honestly in the demo.

Raw/private evidence:artifacts/makeup-render-20261030/stable-results-i3gf100o, including independent-verification.json and visual-review.json. Original ZIP and frozen trial input remain intact.
