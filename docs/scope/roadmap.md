# Coarse build scope

Source: Supervisor's CODEX HANDOFF 001. This is planning scope, not implementation evidence. It is owned by the Supervisor with Project Lead advice; Codex updates progress only from inspected work.

| Sequence | Slice | Progress | Gate |
| --- | --- | --- | --- |
| 1 | Persistent context and generic workflow skills | DONE | Repository context and installed files verified. |
| 2 | FLUX.2 Klein free-GPU feasibility smoke test | DONE | Base edit inference, finite BF16 Edit-LoRA training, checkpoint save, and fresh Base adapter load were verified on Kaggle T4. Overall YELLOW due to measured training-time risk. Distilled compatibility remains a separate verification gap. See [experiment record](../experiments/EXP-001.md). |
| 3 | Licensed paired-data preparation | IN PROGRESS | The Supervisor's Kaggle finalizer reported 30 accepted identity groups and 48 train/12 validation directional pairs with automated QA passing. Manual inspection of the two final contact sheets remains before DATA-001 is DONE. Masked V2 is optional fallback. See [completion handoff](../data/DATA-001-practical-completion.md). |
| 4 | Train custom hairstyle Edit-LoRA and compare with BASE | IN PROGRESS | The Supervisor's BF16 250-step real run completed with finite losses, a final adapter, and optimizer state. The held-out 12-pair Base-versus-adapter evaluation remains. Any same-run continuation toward 500 requires separate verification after evaluation. See [TRAIN-001 evidence](../experiments/TRAIN-001.md). |
| 5 | Test pretrained refinement and HYBRID comparison | NOT STARTED | Confirm draft is preserved and quality effect is measured. |
| 6 | Local System MVP with mock generation | DONE | Next.js frontend and FastAPI backend complete the portrait upload, prototype style selection, mock generation, result, and reset flow. Four Edge browser tests and six API tests passed. Real model integration remains NOT STARTED. |
| 7 | Improve visual quality and UI | NOT STARTED | Prioritize only after the custom contribution and end-to-end path work. |

The Supervisor authorized and supplied acceptance criteria for the System MVP after EXP-001. It was built ahead of the hairstyle data and model slices so the local application flow can be exercised now. Load-bearing implementation choices belong in `docs/specs/`; experiment evidence belongs in `docs/experiments/`.
