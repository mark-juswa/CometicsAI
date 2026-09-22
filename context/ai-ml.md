# AI/ML

Source: Supervisor's CODEX HANDOFF 001. Intended method decision: CONFIRMED; technical feasibility: NEEDS VERIFICATION.

The custom contribution is a domain-adapted hairstyle image-editing model: pretrained FLUX.2 Klein 4B plus hairstyle Edit-LoRA parameters trained by this project. It must generate a transformed image, rather than only labels, scores, or prompts. The intended training task is paired image editing from an original or altered hairstyle to a desired one, with an instruction to preserve identity and non-hair regions.

At inference, compare plain pretrained generation, generation with the project LoRA, and the custom draft followed by plain pretrained refinement. The second stage is intended to improve appearance without removing the first stage's hairstyle change.

The [EXP-001 smoke test](../docs/experiments/EXP-001.md) verified Base image-edit inference, 20 finite-loss BF16 Edit-LoRA steps on one Kaggle T4, checkpoint serialization, and a fresh Base adapter load. This is technical pipeline evidence only; no hairstyle model or quality result exists. FP16 produced NaN loss. Measured BF16 timing was 32.808 seconds per step. Base-trained adapter compatibility with distilled Klein, long-run stability, hairstyle data and quality, multi-image refinement, and free deployment remain NEEDS VERIFICATION.
