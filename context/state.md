# Current state

As of 2026-09-21. Source: repository inspection, Supervisor's CODEX HANDOFF 002, and [EXP-001](../docs/experiments/EXP-001.md).

| Item | Status | Evidence / next check |
| --- | --- | --- |
| Phase | IN PROGRESS | EXP-001 reached tiny LoRA training on Kaggle T4; only the scheduler blocker and 20-step save/reload proof remain. No application phase authorized. |
| Active architecture | CONFIRMED decision; NEEDS VERIFICATION feasibility | See [architecture](architecture.md). |
| Last verified milestone | VERIFIED | FLUX.2 Klein Base loads, completes a 512×512 edit, discovers the paired dataset, and initializes LoRA modules on the Kaggle T4 runtime. |
| Current blocker | IN PROGRESS fix | AI Toolkit used its default `ddpm` training route and called the dynamic scheduler without `mu`. The config now explicitly selects its maintained `flowmatch` route. |
| Current experiment | IN PROGRESS | [EXP-001](../docs/experiments/EXP-001.md) is ready for the same 20-step retry and fresh Base adapter reload. |
| Dataset | NOT STARTED | No source, license, images, or split verified. |
| Training | NOT STARTED | No GPU session, code, weights, or logs verified. |
| Deployment | NOT STARTED | No app or service deployed. |
| Next approved task | CONFIRMED | Run only the corrected 20-step training, save the adapter, and verify fresh Base reload plus one inference. |

Highest-priority verification gaps: FLUX.2 Klein edit-LoRA compatibility, memory, and speed on T4; Base-trained adapter loading on distilled Klein; suitable licensed paired data; plain-Klein refinement with portrait plus draft; ZeroGPU eligibility and runtime. The approximately three-day deadline makes these early feasibility gates important. Detailed next build sequence is in [scope](../docs/scope/roadmap.md).
