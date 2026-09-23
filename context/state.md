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
| Dataset | IN PROGRESS | DATA-001 pinned the source revision and card-declared Apache-2.0 license; all three exact folders contain 30 usable original photos each. Ten per class are provisionally selected with an 8/2 identity-group split. V1 visual review found one potentially suitable output and two with material drift. The masked three-image V2 runner and approval-gated bulk/finalization handoff are prepared, but V2 has not run on Kaggle. No official V2 acceptance or directional pair exists. See [V1 review](../docs/data/DATA-001-pilot-review.md), [V2 pilot](../docs/data/DATA-001-pilot-v2.md), and [bulk handoff](../docs/data/DATA-001-bulk-handoff.md). |
| Training | VERIFIED SMOKE; REAL RUN PREPARED | FP16 failed with NaN loss. BF16 produced 20/20 finite losses, with observed optimizer steps and checkpoint serialization. TRAIN-001 250/500-step configuration and held-out evaluation are prepared but blocked by incomplete DATA-001 and not executed. |
| Real hairstyle model quality | UNKNOWN | No real hairstyle LoRA has been trained or evaluated. |
| Base-trained adapter on distilled Klein | NEEDS VERIFICATION | No compatibility run has been performed. |
| System MVP | DONE | Next.js portrait upload, preview, prototype style selection, FastAPI request, MockEngine result, and reset flow passed local Edge browser tests. |
| Generation engine | VERIFIED / MOCK | FastAPI delegates to `MockEngine` through `GenerationEngine`; the result is the normalized source image and is labeled as a development preview. |
| Real model integration | NOT STARTED | No FLUX weights or real LoRA are loaded by the local application. |
| Deployment | NOT STARTED | The application runs locally; no external service is deployed. |
| Next approved task | DATA-001 PILOT V2 | Supervisor runs only `CrewCut_1`, `BobHair_1`, and `LayeredHair_4` through the masked pilot and returns evidence for visual review. Bulk generation and real training workflows are prepared but execution stays behind the V2 pilot and completed-dataset gates. |

Highest-priority verification gaps: FLUX.2 Klein edit-LoRA compatibility, memory, and speed on T4; Base-trained adapter loading on distilled Klein; suitable licensed paired data; plain-Klein refinement with portrait plus draft; ZeroGPU eligibility and runtime. The approximately three-day deadline makes these early feasibility gates important. Detailed next build sequence is in [scope](../docs/scope/roadmap.md).
