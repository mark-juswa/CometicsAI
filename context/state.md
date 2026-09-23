# Current state

As of 2026-09-23. Source: repository inspection, Supervisor's CODEX HANDOFF 002, [EXP-001](../docs/experiments/EXP-001.md), and [DATA-001](../docs/data/DATA-001.md).

| Item | Status | Evidence / next check |
| --- | --- | --- |
| Phase | DONE | The approved local System MVP is implemented and verified with MockEngine. No real hairstyle model is integrated. |
| Active architecture | CONFIRMED decision; PARTIALLY VERIFIED feasibility | Free-GPU Base editing and finite Edit-LoRA training are verified; distilled compatibility and refinement remain unverified. See [architecture](architecture.md). |
| FLUX.2 Klein free-GPU feasibility | VERIFIED | Kaggle T4 Base load, 512×512 image edit, and finite Edit-LoRA smoke training completed. Overall EXP-001 classification is YELLOW due to time risk. |
| Finite Edit-LoRA training | VERIFIED | BF16 produced 3/3 finite probe losses and 20/20 finite confirmation losses; 32.808 seconds/step and 13,531 MiB peak. |
| Checkpoint serialization | VERIFIED | The BF16 training run saved a 46,223,600-byte LoRA adapter. |
| Fresh Base plus adapter loading | VERIFIED | The BF16-trained adapter loaded into a fresh FLUX.2 Klein Base pipeline. This retry did not run adapter inference. |
| Current blocker | NEEDS VERIFICATION | Longer-run stability, schedule fit, and Base-trained adapter compatibility with distilled Klein remain unverified. NaN loss is resolved in the BF16 smoke test. |
| Current experiment | VERIFIED / YELLOW | [EXP-001](../docs/experiments/EXP-001.md): free-GPU feasibility, 3/3 and 20/20 finite BF16 losses, checkpoint serialization, and fresh Base adapter load verified; training-time risk remains. |
| Dataset | IN PROGRESS | DATA-001 has 30 selected originals with an 8/2 split per class. The Supervisor's V1/global bulk run exited 0. The received archive contains 30 originals, 30 generated PNGs, and 30 matching JSON sidecars; inspected hashes, sample IDs, class mappings, attempts, and 8/2 splits match the approved selection. All 60 images decode as RGB 512×512 with no exact duplicate hashes. All 30 review entries remain PENDING. Visual review flagged `LayeredHair_4` and `LayeredHair_9` for likely major identity/clothing changes, with `LayeredHair_10`, `_11`, and `_15` needing closer human review. Explicit decisions, finalization QA, and directional pairs remain pending. Masked V2 is optional fallback only. See [active handoff](../docs/data/DATA-001-v1-bulk-handoff.md). |
| Training | PREPARED; REAL RUN NOT STARTED | FP16 failed with NaN loss; BF16 produced 20/20 finite smoke losses. The first 250-step TRAIN-001 configuration is prepared with saves at 125/250, non-finite-loss stop, final-step/checkpoint/optimizer checks, and preserved state for potential continuation. A fresh 500-step run is disabled; a same-run continuation procedure would need verification after 250-step evaluation. No real hairstyle training has run. |
| Real hairstyle model quality | UNKNOWN | No real hairstyle LoRA has been trained or evaluated. |
| Base-trained adapter on distilled Klein | NEEDS VERIFICATION | No compatibility run has been performed. |
| System MVP | DONE | Next.js portrait upload, preview, prototype style selection, FastAPI request, MockEngine result, and reset flow passed local Edge browser tests. |
| Generation engine | VERIFIED / MOCK | FastAPI delegates to `MockEngine` through `GenerationEngine`; the result is the normalized source image and is labeled as a development preview. |
| Real model integration | NOT STARTED | No FLUX weights or real LoRA are loaded by the local application. |
| Deployment | NOT STARTED | The application runs locally; no external service is deployed. |
| Next approved task | DATA-001 REVIEW AND FINALIZATION | Supervisor records 30 explicit practical V1 review decisions, runs at most one retry each for `LayeredHair_4` and `LayeredHair_9` if their current outputs fail review, then finalizes and checks 48 train/12 validation pairs. The prepared 250-step TRAIN-001 run may start only after DATA-001 QA passes. Codex does not run long Kaggle jobs or real training. |

Highest-priority verification gaps: FLUX.2 Klein edit-LoRA compatibility, memory, and speed on T4; Base-trained adapter loading on distilled Klein; suitable licensed paired data; plain-Klein refinement with portrait plus draft; ZeroGPU eligibility and runtime. The approximately three-day deadline makes these early feasibility gates important. Detailed next build sequence is in [scope](../docs/scope/roadmap.md).
