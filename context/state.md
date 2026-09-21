# Current state

As of 2026-09-21. Source: repository inspection, Supervisor's CODEX HANDOFF 002, and [EXP-001](../docs/experiments/EXP-001.md).

| Item | Status | Evidence / next check |
| --- | --- | --- |
| Phase | BLOCKED | EXP-001 harness prepared; the reached Kaggle notebook has no selectable GPU. No application phase authorized. |
| Active architecture | CONFIRMED decision; NEEDS VERIFICATION feasibility | See [architecture](architecture.md). |
| Last verified milestone | VERIFIED | Git baseline committed; EXP-001 script passes local Python syntax check. |
| Current blocker | BLOCKED | Kaggle accelerator menu shows `None` selected and `GPU T4 ×2` disabled; `nvidia-smi` is absent. Cause unknown. |
| Current experiment | BLOCKED | [EXP-001](../docs/experiments/EXP-001.md) reached a CPU notebook but no model or GPU stage ran. |
| Dataset | NOT STARTED | No source, license, images, or split verified. |
| Training | NOT STARTED | No GPU session, code, weights, or logs verified. |
| Deployment | NOT STARTED | No app or service deployed. |
| Next approved task | CONFIRMED | Complete EXP-001 after Kaggle GPU eligibility is resolved, starting with the audit-only command. |

Highest-priority verification gaps: actual free Kaggle GPU and limits; FLUX.2 Klein edit-LoRA training compatibility and memory; base/distilled variant compatibility; suitable licensed paired data; plain-Klein refinement with portrait plus draft; ZeroGPU eligibility and runtime. The approximately three-day deadline makes these early feasibility gates important. Detailed next build sequence is in [scope](../docs/scope/roadmap.md).
