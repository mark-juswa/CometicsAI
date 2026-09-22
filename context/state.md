# Current state

As of 2026-09-22. Source: repository inspection, Supervisor's CODEX HANDOFF 002, and [EXP-001](../docs/experiments/EXP-001.md).

| Item | Status | Evidence / next check |
| --- | --- | --- |
| Phase | IN PROGRESS | EXP-001 established free-GPU feasibility. The Supervisor authorized System MVP work; its acceptance criteria are being clarified before implementation. |
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
| Deployment | NOT STARTED | No app or service deployed. |
| Next approved task | CONFIRMED | System MVP is authorized by the Supervisor. No implementation brief or acceptance criteria are recorded in the repository; clarification requested. No further numerical-stability experiment is authorized absent a new real-training failure. |

Highest-priority verification gaps: FLUX.2 Klein edit-LoRA compatibility, memory, and speed on T4; Base-trained adapter loading on distilled Klein; suitable licensed paired data; plain-Klein refinement with portrait plus draft; ZeroGPU eligibility and runtime. The approximately three-day deadline makes these early feasibility gates important. Detailed next build sequence is in [scope](../docs/scope/roadmap.md).
