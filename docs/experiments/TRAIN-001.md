# TRAIN-001 — first conditional hairstyle Edit-LoRA

Source: Supervisor's Kaggle console excerpt and `training_summary.json` fields reported on 2026-09-23, plus the supplied held-out comparison sheet and local evaluation ZIP. Configuration and execution procedure: [TRAIN-001 plan](TRAIN-001-plan.md).

The Supervisor trained one BF16 conditional Edit-LoRA for `CrewCut`, `BobHair`, and `LayeredHair` on the 48 DATA-001 training directions using FLUX.2 Klein Base 4B and the pinned AI Toolkit workflow. The process exited 0, reached 250/250 steps, and `training_summary.json` passed the runner's `success is True` and `highest_loss_step == 250` assertions. The final console loss was `2.749e-01`; late examples include `2.460e-01`, `3.372e-01`, `5.878e-01`, and `3.102e-01`. These are finite loss observations, not a quality evaluation.

| Observation | Reported value |
| --- | ---: |
| Wall time including model load | 8,531.202 s (2 h 22 m 11 s) |
| Final progress-bar average | 31.84 s/step |
| Whole-GPU peak | 13,531 MiB |
| Final adapter | `/kaggle/working/train001_250/checkpoints/train001_250step/train001_250step.safetensors` — 46,223,600 bytes |
| Intermediate adapter | `/kaggle/working/train001_250/checkpoints/train001_250step/train001_250step_000000125.safetensors` — 46,223,600 bytes |
| Optimizer state | `/kaggle/working/train001_250/checkpoints/train001_250step/optimizer.pt` — 47,115,531 bytes |
| Artifact archive | `/kaggle/working/train001_250_artifacts.zip` |

The Supervisor subsequently ran the held-out evaluation phase. Its progress output reached 12/12 Base and 12/12 adapter images, exited 0, and reported `/kaggle/working/train001_250/evaluation/reference_base_adapter_target.jpg`. The Supervisor supplied that sheet and `train001_250_with_evaluation.zip`; the latter contains `evaluation/metadata.json`, the 24 individual outputs, and the training summary. Metadata confirms column order `reference | base_output | adapter_output | target`, the final 250-step checkpoint, and the same validation pair IDs across modes.

## Visual gate: NOT DEMO READY

Codex inspected the full-resolution 12-row sheet and the six validation identity pairs from the earlier V1 archive. Hair changes occur in some adapter outputs, but identity preservation is unreliable and the adapter often resembles unadapted Base. In the `CrewCut_26` and `CrewCut_30` directions, both Base and adapter substantially reconstruct the face while changing the hair. `BobHair_28_to_original` shows a blue-tinted adapter hairstyle absent from the reference/target; `LayeredHair_23_to_original` ends with much shorter hair than the long-hair target. The generated validation counterparts themselves contain some appearance drift, but the sheet does not establish that data drift alone caused the inference failure. This is a visual judgment, not an automated identity score. It blocks app integration and gives no basis to assume 500 steps will fix face preservation.

The smallest discriminating follow-up is an **image-only preservation probe** on the already generated 12 adapter outputs. [`train001_preservation_probe.py`](../../scripts/train001_preservation_probe.py) reuses the existing pinned face parser and DATA-001 mask construction, then copies the original source pixels outside the editable hair region. It runs no FLUX inference or training and does not change the dataset, reviews, or checkpoint. Its output sheet compares `source | global adapter | mask | hair-only composite | target`. Human review must decide whether the composite keeps identity while still delivering the requested hairstyle. A failed parser/mask or visible seam is a stop signal, not permission for random tuning.

The final DATA-001 archive was subsequently downloaded and both contact sheets inspected. Some accepted generated counterparts show material identity or clothing drift despite passing automated QA; see [DATA-001](../data/DATA-001.md). Do not start 500 steps or app integration from execution success alone.
