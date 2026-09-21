# Architecture

Source: Supervisor's CODEX HANDOFF 001. Decision status: CONFIRMED. Implementation feasibility: NEEDS VERIFICATION.

Approved conceptual path:

1. Portrait plus selected hairstyle enters FLUX.2 Klein 4B with the project's trained hairstyle image-edit LoRA.
2. That custom generative stage produces a hairstyle-transformed draft.
3. Plain pretrained FLUX.2 Klein 4B, without the project LoRA, receives the original portrait and custom draft for refinement.
4. The final output should improve realism, hair integration, identity preservation, and consistency while retaining the custom transformation.

The refinement stage must not intentionally bypass the custom stage. The project-trained LoRA must participate directly in pixel generation. Exact model identifiers, framework, interface, two-image capability, memory needs, and output quality are NEEDS VERIFICATION.

Intended free deployment direction: Next.js frontend, likely Vercel Hobby; Gradio inference on a Hugging Face Space, using ZeroGPU only if actually available. These are targets, not deployed or eligibility facts. No endpoint, package layout, or runtime is established. Training targets a free Kaggle GPU session; actual GPU, limits, and viability require session evidence. The local machine handles ordinary development, not presumed heavy FLUX workloads.

Approved superseded approaches are recorded in [decisions](decisions.md). Any replacement of this architecture needs Supervisor approval supported by evidence.
