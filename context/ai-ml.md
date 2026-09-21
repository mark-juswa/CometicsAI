# AI/ML

Source: Supervisor's CODEX HANDOFF 001. Intended method decision: CONFIRMED; technical feasibility: NEEDS VERIFICATION.

The custom contribution is a domain-adapted hairstyle image-editing model: pretrained FLUX.2 Klein 4B plus hairstyle Edit-LoRA parameters trained by this project. It must generate a transformed image, rather than only labels, scores, or prompts. The intended training task is paired image editing from an original or altered hairstyle to a desired one, with an instruction to preserve identity and non-hair regions.

At inference, compare plain pretrained generation, generation with the project LoRA, and the custom draft followed by plain pretrained refinement. The second stage is intended to improve appearance without removing the first stage's hairstyle change.

NEEDS VERIFICATION: exact model variant and license; whether its image-edit and multi-image paths support this pipeline; a compatible LoRA trainer and target modules; rank, alpha, resolution, optimizer, steps, memory, runtime, base/distilled compatibility, Kaggle feasibility, and refinement quality. No trained weights, checkpoint, performance measurement, or experiment record is currently known. See [evaluation](evaluation.md) and [data](data.md).
