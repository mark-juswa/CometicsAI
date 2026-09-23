# Architecture

Source: Supervisor's CODEX HANDOFF 001, EXP-001, and later critical-path direction. Decision status: CONFIRMED for first demo. Real hairstyle model integration: NOT STARTED.

Approved first-demo path:

1. Portrait plus selected hairstyle enters FLUX.2 Klein 4B with the project's trained hairstyle image-edit LoRA.
2. That custom generative stage produces the displayed hairstyle result.
3. The existing `GenerationEngine` boundary selects `MockEngine` or, after checkpoint evaluation, `FluxEngine` without adding FLUX-specific frontend logic.

[EXP-001](../docs/experiments/EXP-001.md) verifies Base image editing, finite BF16 Edit-LoRA smoke training on free Kaggle T4, checkpoint serialization, and fresh Base adapter loading. It does not verify a real hairstyle LoRA, Base-trained adapter compatibility with distilled Klein, or end-to-end application inference. These implementation claims have distinct evidence statuses.

The project-trained LoRA must participate directly in pixel generation. Refinement and distilled inference are deferred beyond the first demo by the Supervisor's later direction; neither is a DATA-001, TRAIN-001, or demo gate. Exact real checkpoint behavior, memory needs, and output quality remain NEEDS VERIFICATION.

Intended free deployment direction: Next.js frontend, likely Vercel Hobby; Gradio inference on a Hugging Face Space, using ZeroGPU only if actually available. These are targets, not deployed or eligibility facts. The local System MVP uses Next.js and FastAPI with a mock generator; deployment and real model service architecture remain undecided. EXP-001 verified finite BF16 smoke training on one free Kaggle T4 but did not establish guaranteed future GPU allocation or long-run limits. The local machine handles ordinary development, not presumed heavy FLUX workloads.

The local System MVP now has a Next.js frontend and FastAPI backend. `POST /generate` accepts a portrait and `style_id`, validates them, and delegates image behavior to `GenerationEngine`. Its current `MockEngine` returns a normalized copy of the portrait with `generator: mock`; the UI labels it as a development preview. The API response contains the selected style and image data URL, so a later real engine can preserve the frontend contract. No FLUX code, model weights, or refinement stage are in this local application. See [README](../README.md).

Approved superseded approaches are recorded in [decisions](decisions.md). Any replacement of this first-demo architecture needs Supervisor approval supported by evidence.
