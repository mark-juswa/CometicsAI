# Current state

As of 2026-09-21. Source: repository inspection, Supervisor's CODEX HANDOFF 002, and [EXP-001](../docs/experiments/EXP-001.md).

| Item | Status | Evidence / next check |
| --- | --- | --- |
| Phase | BLOCKED | EXP-001 stopped after the kernel-bound retry also exposed CPU-only Torch and no CUDA. No application phase authorized. |
| Active architecture | CONFIRMED decision; NEEDS VERIFICATION feasibility | See [architecture](architecture.md). |
| Last verified milestone | VERIFIED | EXP-001 environment audit: two independent Tesla T4 GPUs with 14.56 GB usable VRAM each; GPU 0 is selected for the experiment. |
| Current blocker | BLOCKED | The kernel-selected child `/usr/bin/python3` exposes Torch `2.10.0+cpu`, CUDA `None`, and no GPU despite the earlier CUDA-enabled notebook audit evidence. |
| Current experiment | BLOCKED / RED environment outcome | [EXP-001](../docs/experiments/EXP-001.md) stopped under its retry rule. FLUX model feasibility remains UNKNOWN because no CUDA process could start the model stage. |
| Dataset | NOT STARTED | No source, license, images, or split verified. |
| Training | NOT STARTED | No GPU session, code, weights, or logs verified. |
| Deployment | NOT STARTED | No app or service deployed. |
| Next approved task | NONE | The Supervisor and Project Lead must resolve the contradictory Kaggle GPU allocation before another EXP-001 execution is justified. |

Highest-priority verification gaps: FLUX.2 Klein edit-LoRA compatibility, memory, and speed on T4; Base-trained adapter loading on distilled Klein; suitable licensed paired data; plain-Klein refinement with portrait plus draft; ZeroGPU eligibility and runtime. The approximately three-day deadline makes these early feasibility gates important. Detailed next build sequence is in [scope](../docs/scope/roadmap.md).
