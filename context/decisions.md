# Decision history

Source for all entries: Supervisor's CODEX HANDOFF 001. Decision dates before this record: UNKNOWN. Recorded 2026-09-21.

| Decision | Status | Evidence | Rationale and authority |
| --- | --- | --- | --- |
| Project-trained hairstyle Edit-LoRA on FLUX.2 Klein 4B generates a draft, then plain pretrained FLUX.2 Klein refines it | CONFIRMED | NEEDS VERIFICATION | Supervisor-approved active $0 direction; custom model must directly generate pixels. |
| Free Kaggle GPU as training target | CONFIRMED | NEEDS VERIFICATION | Supervisor's $0 constraint; actual hardware and limits uninspected. |
| Roughly six styles and 60 train plus 12 validation pairs | PROPOSED | NEEDS VERIFICATION | Preliminary dataset scale, not inspected data. |
| Synthetic source paired with real hairstyle target | PROPOSED | NEEDS VERIFICATION | Possible way to obtain paired edits under deadline. |
| Next.js/Vercel Hobby frontend and Gradio/Hugging Face Space with ZeroGPU if eligible | PROPOSED | NEEDS VERIFICATION | Free deployment direction; access and compatibility unproven. |
| SDXL Inpainting + trained LoRA + BiSeNet parsing + adaptive mask + IP-Adapter | DEPRECATED | UNKNOWN | Superseded by the more direct FLUX editing direction with fewer critical components. |
| FLUX.2 Klein + trained LoRA, paid FLUX.2 Pro API refinement, RunPod GPU | DEPRECATED | UNKNOWN | Superseded when Supervisor selected the $0 direction. |

Do not restore a deprecated architecture or silently change the confirmed one. Gather evidence and seek Supervisor approval for a new major decision.
