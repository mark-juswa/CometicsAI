# TRAIN-001 — first conditional hairstyle Edit-LoRA

Source: Supervisor's Kaggle console excerpt and `training_summary.json` fields reported on 2026-09-23. The full training artifact ZIP remains on the Supervisor's machine/Kaggle; it has not been inspected in this workspace. Configuration and execution procedure: [TRAIN-001 plan](TRAIN-001-plan.md).

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

The next gate is held-out evaluation of the final adapter against unadapted Base on the same 12 validation directions. Neither visible hairstyle quality nor improvement over Base has been established. The final DATA-001 contact sheets also still need a reported manual check. Do not start 500 steps or app integration from the training log alone.
