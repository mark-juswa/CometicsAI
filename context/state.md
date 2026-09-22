# Current state

As of 2026-09-22. Source: repository inspection, Supervisor's CODEX HANDOFF 002, and [EXP-001](../docs/experiments/EXP-001.md).

| Item | Status | Evidence / next check |
| --- | --- | --- |
| Phase | IN PROGRESS | The authorized EXP-001 BF16 numerical stability gate passed. No application phase is authorized. |
| Active architecture | CONFIRMED decision; NEEDS VERIFICATION feasibility | See [architecture](architecture.md). |
| Last verified milestone | VERIFIED | A 46,223,600-byte LoRA checkpoint serialized, loaded into a fresh Base pipeline, and completed one 512×512 adapter inference. |
| Current blocker | NEEDS VERIFICATION | BF16 20-step loss is finite, but longer-run stability, schedule fit, and Base-trained adapter compatibility with distilled Klein remain unverified. |
| Current experiment | EXPERIMENTAL / YELLOW | [EXP-001](../docs/experiments/EXP-001.md): 3/3 and 20/20 BF16 losses finite; 32.808 seconds/step and 13,531 MiB peak; checkpoint saved and loaded into a fresh Base pipeline. |
| Dataset | NOT STARTED | No source, license, images, or split verified. |
| Training | EXPERIMENTAL / VERIFIED SMOKE | FP16 failed with NaN loss. BF16 produced 20/20 finite losses, with observed optimizer steps and checkpoint serialization; no real hairstyle training occurred. |
| Deployment | NOT STARTED | No app or service deployed. |
| Next approved task | NONE | The Project Lead should review measured BF16 speed and the distilled compatibility gap before authorizing another experiment. |

Highest-priority verification gaps: FLUX.2 Klein edit-LoRA compatibility, memory, and speed on T4; Base-trained adapter loading on distilled Klein; suitable licensed paired data; plain-Klein refinement with portrait plus draft; ZeroGPU eligibility and runtime. The approximately three-day deadline makes these early feasibility gates important. Detailed next build sequence is in [scope](../docs/scope/roadmap.md).
