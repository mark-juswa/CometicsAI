# AI/ML

Source: Supervisor's CODEX HANDOFF 001, EXP-001, and reported TRAIN-001 execution. Intended method decision: CONFIRMED; T4 training mechanics and 250-step completion: VERIFIED; hairstyle quality: UNKNOWN.

The custom contribution is a domain-adapted hairstyle image-editing model: pretrained FLUX.2 Klein 4B plus hairstyle Edit-LoRA parameters trained by this project. It must generate a transformed image, rather than only labels, scores, or prompts. The intended training task is paired image editing from an original or altered hairstyle to a desired one, with an instruction to preserve identity and non-hair regions.

At inference, compare plain pretrained generation, generation with the project LoRA, and the custom draft followed by plain pretrained refinement. The second stage is intended to improve appearance without removing the first stage's hairstyle change.

The [EXP-001 smoke test](../docs/experiments/EXP-001.md) verified Base image-edit inference, 20 finite-loss BF16 Edit-LoRA steps on one Kaggle T4, checkpoint serialization, and a fresh Base adapter load. FP16 produced NaN loss. The Supervisor's [TRAIN-001 run](../docs/experiments/TRAIN-001.md) then completed 250 finite-loss steps on DATA-001 with one conditional LoRA and saved final/intermediate adapters and optimizer state. The held-out 12-pair visual review found some hairstyle changes but unreliable face preservation and limited improvement over Base, so the checkpoint is not demo-ready. A hair-region image-composite probe on existing outputs is prepared to test a minimal preservation fix without retraining. Base-trained adapter compatibility with distilled Klein, multi-image refinement, and free deployment remain NEEDS VERIFICATION and are outside the current critical path.
