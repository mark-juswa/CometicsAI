# Current state

As of 2026-09-22. Source: repository inspection, Supervisor's CODEX HANDOFF 002, and [EXP-001](../docs/experiments/EXP-001.md).

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
| Dataset | NOT STARTED | No source, license, images, or split verified. |
| Training | VERIFIED SMOKE | FP16 failed with NaN loss. BF16 produced 20/20 finite losses, with observed optimizer steps and checkpoint serialization; no real hairstyle training occurred. |
| Real hairstyle model quality | UNKNOWN | No real hairstyle LoRA has been trained or evaluated. |
| Base-trained adapter on distilled Klein | NEEDS VERIFICATION | No compatibility run has been performed. |
| System MVP | DONE | Next.js portrait upload, preview, prototype style selection, FastAPI request, MockEngine result, and reset flow passed local Edge browser tests. |
| Generation engine | VERIFIED / MOCK | FastAPI delegates to `MockEngine` through `GenerationEngine`; the result is the normalized source image and is labeled as a development preview. |
| Real model integration | NOT STARTED | No FLUX weights or real LoRA are loaded by the local application. |
| Deployment | NOT STARTED | The application runs locally; no external service is deployed. |
| Next approved task | NONE | The Supervisor asked to stop after System MVP. No further numerical-stability experiment is authorized absent a new real-training failure. |

Highest-priority verification gaps: FLUX.2 Klein edit-LoRA compatibility, memory, and speed on T4; Base-trained adapter loading on distilled Klein; suitable licensed paired data; plain-Klein refinement with portrait plus draft; ZeroGPU eligibility and runtime. The approximately three-day deadline makes these early feasibility gates important. Detailed next build sequence is in [scope](../docs/scope/roadmap.md).
