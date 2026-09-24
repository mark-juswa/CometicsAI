# Coarse build scope

Source: Supervisor's CODEX HANDOFF 001. This is planning scope, not implementation evidence. It is owned by the Supervisor with Project Lead advice; Codex updates progress only from inspected work.

| Sequence | Slice | Progress | Gate |
| --- | --- | --- | --- |
| 1 | Persistent context and generic workflow skills | DONE | Repository context and installed files verified. |
| 2 | FLUX.2 Klein free-GPU feasibility smoke test | DONE | Base edit inference, finite BF16 Edit-LoRA training, checkpoint save, and fresh Base adapter load were verified on Kaggle T4. Overall YELLOW due to measured training-time risk. Distilled compatibility remains a separate verification gap. See [experiment record](../experiments/EXP-001.md). |
| 3 | Licensed paired-data preparation | IN PROGRESS | The downloaded final archive passed integrity and automated QA checks for 30 accepted identity groups and 48 train/12 validation directional pairs. Manual inspection of both final contact sheets found material identity or clothing drift in some accepted counterparts; visual quality is not cleared. Masked V2 is optional fallback. See [DATA-001](../data/DATA-001.md). |
| 4 | Train custom hairstyle Edit-LoRA and compare with BASE | IN PROGRESS | The Supervisor's BF16 250-step run and 12-pair Base-versus-adapter inference completed. Visual review found unreliable face preservation; the checkpoint is not demo-ready. A CPU-only hair-region preservation probe on saved outputs is prepared. Do not assume 500 more steps will correct the issue. See [TRAIN-001 evidence](../experiments/TRAIN-001.md). |
| 5 | Test pretrained refinement and HYBRID comparison | NOT STARTED | Confirm draft is preserved and quality effect is measured. |
| 6 | Local System MVP with mock generation | DONE | Next.js frontend and FastAPI backend complete portrait upload, prototype style selection, mock generation, result, and reset. The optional real-model remote path is implemented separately and awaits live Kaggle verification. |
| 8 | Temporary Kaggle real-model demo runtime | IN PROGRESS | Bootstrap, GPU server, private adapter bundle contract, Quick Tunnel public health check, and local RemoteFluxEngine are implemented. Local API contract, frontend build, and mock browser checks pass. A Supervisor-run Kaggle GPU and public end-to-end request remain the completion gate. See [demo guide](../guides/kaggle-real-model-demo.md). |
| 7 | Improve visual quality and UI | NOT STARTED | Prioritize only after the custom contribution and end-to-end path work. |

The Supervisor authorized and supplied acceptance criteria for the System MVP after EXP-001. It was built ahead of the hairstyle data and model slices so the local application flow can be exercised now. Load-bearing implementation choices belong in `docs/specs/`; experiment evidence belongs in `docs/experiments/`.
