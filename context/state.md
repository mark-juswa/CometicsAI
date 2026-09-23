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
| Current blocker | VERIFIED QUALITY FAILURE | The 12-pair held-out sheet shows unreliable face preservation and limited adapter improvement over Base. The 250-step checkpoint is not demo-ready. A short, image-only hair-region preservation probe is prepared; final DATA-001 contact sheets still need reported manual inspection. Distilled compatibility remains outside the current critical path. |
| Current experiment | VERIFIED / YELLOW | [EXP-001](../docs/experiments/EXP-001.md): free-GPU feasibility, 3/3 and 20/20 finite BF16 losses, checkpoint serialization, and fresh Base adapter load verified; training-time risk remains. |
| Dataset | IN PROGRESS | The Supervisor completed 30 explicit ACCEPT reviews, including bounded second attempts for `LayeredHair_4` and `LayeredHair_9`, and ran the V1 finalizer in Kaggle. Reported QA: 24 train/6 validation identity groups, 48 train/12 validation directional pairs, balanced target classes, aligned captions/images, no unexpected duplicate SHA-256 groups, and no split leakage. `/kaggle/working/data001_final.zip` was created. The two final contact sheets still require manual inspection before DATA-001 is marked DONE. Masked V2 remains optional and unexecuted. |
| Training | 250-STEP RUN DONE; EVALUATION IMAGES GENERATED | The Supervisor's Kaggle run exited 0 and the summary passed `success is True` and step 250 checks. Measured wall time including load: 8,531.202 s; peak GPU memory: 13,531 MiB. Finite late losses, 125/250 adapter files, and optimizer state were reported. The held-out evaluation process exited 0 after generating 12 Base and 12 adapter images. Human comparison remains pending. See [TRAIN-001 evidence](../docs/experiments/TRAIN-001.md). A 500-step continuation is not authorized or verified. |
| Real hairstyle model quality | EXPERIMENTAL; NOT DEMO READY | Full-resolution held-out review found hairstyle changes in some rows but unreliable face identity and limited improvement over Base. See [TRAIN-001 visual review](../docs/experiments/TRAIN-001.md). |
| Base-trained adapter on distilled Klein | NEEDS VERIFICATION | No compatibility run has been performed. |
| System MVP | DONE | Next.js portrait upload, preview, prototype style selection, FastAPI request, MockEngine result, and reset flow passed local Edge browser tests. |
| Generation engine | VERIFIED / MOCK | FastAPI delegates to `MockEngine` through `GenerationEngine`; the result is the normalized source image and is labeled as a development preview. |
| Real model integration | NOT STARTED | No FLUX weights or real LoRA are loaded by the local application. |
| Deployment | NOT STARTED | The application runs locally; no external service is deployed. |
| Next approved task | IDENTITY-PRESERVATION PROBE | Run the prepared image-only hair-region composite on the 12 saved validation adapter outputs, inspect its contact sheet, and inspect DATA-001's final sheets. Do not integrate the 250-step model or run 500 more steps based on current visual evidence. Codex does not run long Kaggle jobs or real training. |

Highest-priority verification gaps: FLUX.2 Klein edit-LoRA compatibility, memory, and speed on T4; Base-trained adapter loading on distilled Klein; suitable licensed paired data; plain-Klein refinement with portrait plus draft; ZeroGPU eligibility and runtime. The approximately three-day deadline makes these early feasibility gates important. Detailed next build sequence is in [scope](../docs/scope/roadmap.md).
