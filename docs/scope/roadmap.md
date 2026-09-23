# Coarse build scope

Source: Supervisor's CODEX HANDOFF 001. This is planning scope, not implementation evidence. It is owned by the Supervisor with Project Lead advice; Codex updates progress only from inspected work.

| Sequence | Slice | Progress | Gate |
| --- | --- | --- | --- |
| 1 | Persistent context and generic workflow skills | DONE | Repository context and installed files verified. |
| 2 | FLUX.2 Klein free-GPU feasibility smoke test | DONE | Base edit inference, finite BF16 Edit-LoRA training, checkpoint save, and fresh Base adapter load were verified on Kaggle T4. Overall YELLOW due to measured training-time risk. Distilled compatibility remains a separate verification gap. See [experiment record](../experiments/EXP-001.md). |
| 3 | Licensed paired-data preparation | IN PROGRESS | Pinned source, card-declared license, exact classes/counts, and provisional 8/2 per-class identity split inspected. V1 visual review found one potentially suitable output and two with material drift. A masked V2 three-image runner plus approval-gated 27-image/finalization handoff are prepared; no V2 output exists yet. See [DATA-001 bulk handoff](../data/DATA-001-bulk-handoff.md). |
| 4 | Train custom hairstyle Edit-LoRA and compare with BASE | NOT STARTED; PREPARED | BF16 250/500-step config, logging, checkpoint, and held-out evaluation workflow are prepared in [TRAIN-001 plan](../experiments/TRAIN-001-plan.md). Real training waits for a completed, reviewed DATA-001 dataset and Supervisor execution. |
| 5 | Test pretrained refinement and HYBRID comparison | NOT STARTED | Confirm draft is preserved and quality effect is measured. |
| 6 | Local System MVP with mock generation | DONE | Next.js frontend and FastAPI backend complete the portrait upload, prototype style selection, mock generation, result, and reset flow. Four Edge browser tests and six API tests passed. Real model integration remains NOT STARTED. |
| 7 | Improve visual quality and UI | NOT STARTED | Prioritize only after the custom contribution and end-to-end path work. |

The Supervisor authorized and supplied acceptance criteria for the System MVP after EXP-001. It was built ahead of the hairstyle data and model slices so the local application flow can be exercised now. Load-bearing implementation choices belong in `docs/specs/`; experiment evidence belongs in `docs/experiments/`.
