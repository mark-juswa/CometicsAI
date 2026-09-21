# Evaluation

Source: Supervisor's CODEX HANDOFF 001. Comparison design: CONFIRMED intent; results and thresholds: UNKNOWN.

Use the same held-out inputs and hairstyle requests for three conditions:

1. BASE: plain pretrained FLUX.2 Klein.
2. CUSTOM: FLUX.2 Klein plus the project-trained hairstyle Edit-LoRA.
3. HYBRID: CUSTOM draft followed by plain pretrained refinement.

Assess hairstyle match, identity and face preservation, realism, unwanted non-hair edits, artifacts, reliability, and inference time where relevant. Record prompts, seeds, versions, settings, hardware, images, and judging method so the comparison is reproducible. A claim that the LoRA contributes meaningfully needs direct BASE versus CUSTOM evidence; a HYBRID image alone is insufficient. Report a lack of improvement honestly.

Acceptance thresholds, metrics, evaluator, sample size, and scores are UNKNOWN. Actual experiment records belong in `docs/experiments/`, with only evidence-backed conclusions summarized here.
