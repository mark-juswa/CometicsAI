# Coarse build scope

Source: Supervisor's CODEX HANDOFF 001. This is planning scope, not implementation evidence. It is owned by the Supervisor with Project Lead advice; Codex updates progress only from inspected work.

| Sequence | Slice | Progress | Gate |
| --- | --- | --- | --- |
| 1 | Persistent context and generic workflow skills | DONE | Repository context and installed files verified. |
| 2 | FLUX.2 Klein free-GPU feasibility smoke test | IN PROGRESS | Base load/edit and LoRA initialization passed on T4; retrying the same 20 steps with the corrected flow-matching scheduler route. See [experiment record](../experiments/EXP-001.md). |
| 3 | Licensed paired-data preparation | NOT STARTED | Source/license, provenance, quality, and held-out split verified. |
| 4 | Train custom hairstyle Edit-LoRA and compare with BASE | NOT STARTED | Reproducible experiment evidence shows whether custom weights contribute. |
| 5 | Test pretrained refinement and HYBRID comparison | NOT STARTED | Confirm draft is preserved and quality effect is measured. |
| 6 | Connect minimal web prototype to inference | NOT STARTED | End-to-end generation works within free resources. |
| 7 | Improve visual quality and UI | NOT STARTED | Prioritize only after the custom contribution and end-to-end path work. |

Load-bearing implementation choices should be recorded as future specs in `docs/specs/`. Record ML runs in `docs/experiments/`. No spec or experiment is claimed to exist yet.
