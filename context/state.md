# Current state

As of 2026-09-21. Source: repository inspection, Supervisor's CODEX HANDOFF 002, and [EXP-001](../docs/experiments/EXP-001.md).

| Item | Status | Evidence / next check |
| --- | --- | --- |
| Phase | IN PROGRESS | EXP-001 environment gate passed on a later Kaggle T4 ×2 allocation. No application phase authorized. |
| Active architecture | CONFIRMED decision; NEEDS VERIFICATION feasibility | See [architecture](architecture.md). |
| Last verified milestone | VERIFIED | EXP-001 environment audit: two independent Tesla T4 GPUs with 14.56 GB usable VRAM each; GPU 0 is selected for the experiment. |
| Current blocker | IN PROGRESS diagnosis | The first harness launch used `/usr/bin/python3` with CPU-only Torch and no `nvidia-smi`, conflicting with the earlier CUDA-enabled notebook audit. |
| Current experiment | IN PROGRESS | [EXP-001](../docs/experiments/EXP-001.md) environment gate passed earlier; the model run stopped safely before dependencies or downloads because its process had no CUDA. |
| Dataset | NOT STARTED | No source, license, images, or split verified. |
| Training | NOT STARTED | No GPU session, code, weights, or logs verified. |
| Deployment | NOT STARTED | No app or service deployed. |
| Next approved task | CONFIRMED | Launch the harness through the active notebook kernel's `sys.executable`; proceed only if that process reports CUDA. |

Highest-priority verification gaps: FLUX.2 Klein edit-LoRA compatibility, memory, and speed on T4; Base-trained adapter loading on distilled Klein; suitable licensed paired data; plain-Klein refinement with portrait plus draft; ZeroGPU eligibility and runtime. The approximately three-day deadline makes these early feasibility gates important. Detailed next build sequence is in [scope](../docs/scope/roadmap.md).
