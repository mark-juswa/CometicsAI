# Coarse build scope

Source: Supervisor's CODEX HANDOFF 001. This is planning scope, not implementation evidence. It is owned by the Supervisor with Project Lead advice; Codex updates progress only from inspected work.

| Sequence | Slice | Progress | Gate |
| --- | --- | --- | --- |
| 1 | Persistent context and generic workflow skills | DONE | Repository context and installed files verified. |
| 2 | FLUX.2 Klein free-GPU feasibility smoke test | DONE | Base edit inference, finite BF16 Edit-LoRA training, checkpoint save, and fresh Base adapter load were verified on Kaggle T4. Overall YELLOW due to measured training-time risk. Distilled compatibility remains a separate verification gap. See [experiment record](../experiments/EXP-001.md). |
| 3 | Licensed paired-data preparation | IN PROGRESS | The received V1/global archive contains all 30 selected originals and generated counterparts with matching sidecars. Practical visual review, two proposed bounded retries, and guarded finalization remain. Masked V2 is optional fallback. See [completion handoff](../data/DATA-001-practical-completion.md). |
| 4 | Train custom hairstyle Edit-LoRA and compare with BASE | NOT STARTED | BF16 smoke mechanics are proven and the first 250-step TRAIN-001 configuration is prepared. Real training waits for reviewed 48/12 data and Supervisor execution. Checkpoint and optimizer state will be preserved; any same-run continuation toward 500 requires separate verification after evaluation. |
| 5 | Test pretrained refinement and HYBRID comparison | NOT STARTED | Confirm draft is preserved and quality effect is measured. |
| 6 | Local System MVP with mock generation | DONE | Next.js frontend and FastAPI backend complete the portrait upload, prototype style selection, mock generation, result, and reset flow. Four Edge browser tests and six API tests passed. Real model integration remains NOT STARTED. |
| 7 | Improve visual quality and UI | NOT STARTED | Prioritize only after the custom contribution and end-to-end path work. |

The Supervisor authorized and supplied acceptance criteria for the System MVP after EXP-001. It was built ahead of the hairstyle data and model slices so the local application flow can be exercised now. Load-bearing implementation choices belong in `docs/specs/`; experiment evidence belongs in `docs/experiments/`.
