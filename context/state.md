# Current state

As of 2026-09-22. Source: repository inspection, Supervisor's CODEX HANDOFF 002, and [EXP-001](../docs/experiments/EXP-001.md).

| Item | Status | Evidence / next check |
| --- | --- | --- |
| Phase | IN PROGRESS | One controlled EXP-001 BF16 numerical stability test is authorized. No application phase is authorized. |
| Active architecture | CONFIRMED decision; NEEDS VERIFICATION feasibility | See [architecture](architecture.md). |
| Last verified milestone | VERIFIED | A 46,223,600-byte LoRA checkpoint serialized, loaded into a fresh Base pipeline, and completed one 512×512 adapter inference. |
| Current blocker | BLOCKED | The corrected 20-step flow-matching run logged `loss is nan` for every step; the saved adapter cannot count as valid training evidence. |
| Current experiment | IN PROGRESS | [EXP-001](../docs/experiments/EXP-001.md) will run 3 BF16 steps first, then 20 steps and fresh reload only if all three losses are finite. |
| Dataset | NOT STARTED | No source, license, images, or split verified. |
| Training | EXPERIMENTAL / FAILED | 20 optimizer-loop steps ran at median 2.007 s/step and 10,779 MiB peak VRAM, but loss was non-finite throughout. |
| Deployment | NOT STARTED | No app or service deployed. |
| Next approved task | CONFIRMED | Execute only the BF16 stability probe and its conditional 20-step confirmation. |

Highest-priority verification gaps: FLUX.2 Klein edit-LoRA compatibility, memory, and speed on T4; Base-trained adapter loading on distilled Klein; suitable licensed paired data; plain-Klein refinement with portrait plus draft; ZeroGPU eligibility and runtime. The approximately three-day deadline makes these early feasibility gates important. Detailed next build sequence is in [scope](../docs/scope/roadmap.md).
