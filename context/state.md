# Current state

As of 2026-09-21. Source: repository inspection, Supervisor's CODEX HANDOFF 002, and [EXP-001](../docs/experiments/EXP-001.md).

| Item | Status | Evidence / next check |
| --- | --- | --- |
| Phase | IN PROGRESS | EXP-001 environment gate passed on a later Kaggle T4 ×2 allocation. No application phase authorized. |
| Active architecture | CONFIRMED decision; NEEDS VERIFICATION feasibility | See [architecture](architecture.md). |
| Last verified milestone | VERIFIED | EXP-001 environment audit: two independent Tesla T4 GPUs with 14.56 GB usable VRAM each; GPU 0 is selected for the experiment. |
| Current blocker | NONE for Stage 1 | Model loading, edit inference, tiny training, checkpoint reload, and distilled compatibility still require execution in the live Kaggle session. |
| Current experiment | IN PROGRESS | [EXP-001](../docs/experiments/EXP-001.md) environment gate GREEN; execution harness updated for T4 FP16 and `/tmp` cache. |
| Dataset | NOT STARTED | No source, license, images, or split verified. |
| Training | NOT STARTED | No GPU session, code, weights, or logs verified. |
| Deployment | NOT STARTED | No app or service deployed. |
| Next approved task | CONFIRMED | Run the remaining EXP-001 stages only, beginning with dependency preparation and the Base load. |

Highest-priority verification gaps: FLUX.2 Klein edit-LoRA compatibility, memory, and speed on T4; Base-trained adapter loading on distilled Klein; suitable licensed paired data; plain-Klein refinement with portrait plus draft; ZeroGPU eligibility and runtime. The approximately three-day deadline makes these early feasibility gates important. Detailed next build sequence is in [scope](../docs/scope/roadmap.md).
