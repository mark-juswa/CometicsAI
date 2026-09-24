# Decision history

Source for all entries: Supervisor's CODEX HANDOFF 001. Decision dates before this record: UNKNOWN. Recorded 2026-09-21.

| Decision | Status | Evidence | Rationale and authority |
| --- | --- | --- | --- |
| Project-trained conditional hairstyle Edit-LoRA on FLUX.2 Klein Base 4B directly generates the first demo result | CONFIRMED | EXP-001 mechanics VERIFIED; real model NOT STARTED | Supervisor's current critical-path direction requires one LoRA for three approved styles and direct pixel generation through the existing engine boundary. |
| Plain pretrained Klein refinement after custom generation | PROPOSED | NEEDS VERIFICATION | Earlier direction deferred beyond the first working demo by the Supervisor; it is not a DATA-001, TRAIN-001, or demo gate. |
| Free Kaggle GPU as training target | CONFIRMED | VERIFIED for EXP-001 smoke test | Supervisor's $0 constraint; one Kaggle T4 completed 20 finite-loss BF16 Edit-LoRA steps. Training-time risk remains. |
| Roughly six styles and 60 train plus 12 validation pairs | PROPOSED | NEEDS VERIFICATION | Preliminary dataset scale, not inspected data. |
| Synthetic source paired with real hairstyle target | PROPOSED | NEEDS VERIFICATION | Possible way to obtain paired edits under deadline. |
| Next.js/Vercel Hobby frontend and Gradio/Hugging Face Space with ZeroGPU if eligible | PROPOSED | NEEDS VERIFICATION | Free deployment direction; access and compatibility unproven. |
| Local System MVP using Next.js, TypeScript, Tailwind CSS, FastAPI, and a replaceable MockEngine | CONFIRMED | VERIFIED local MVP | Supervisor-approved System MVP; frontend does not know about FLUX, and the API delegates generation to the engine boundary. No deployment or real model integration is implied. |
| Temporary Kaggle GPU inference service for the first real-model demo, reached by the local FastAPI `RemoteFluxEngine` through a session tunnel | CONFIRMED | Implementation and local contract tests VERIFIED; live Kaggle and public endpoint NEEDS VERIFICATION | Supervisor's 2026-09-24 instruction. Base plus the project-trained TRAIN-001 LoRA stays loaded once per Kaggle session. A private Kaggle Dataset stores the adapter; the public Base snapshot is fetched into ephemeral scratch. Cloudflare Quick Tunnel is a testable temporary exposure mechanism, not permanent deployment. |
| DATA-001 V1/global FLUX.2 Klein Base editing for all 30 selected identities; masked V2 optional fallback | CONFIRMED | 30-image generation, sidecar integrity, and automated pair QA VERIFIED; final sheets show visual quality concerns | Supervisor's critical-path direction supersedes the earlier strict pilot/V2 prerequisite. The practical review standard accepts minor hair-color, lighting, clothing-detail, and accessory drift. Only a wrong hairstyle, major identity drift, severe artifacts, or major scene/pose change warrants one bounded retry. No output is auto-accepted. |
| One conditional Edit-LoRA for CrewCut, BobHair, and LayeredHair; evaluate at 250 steps and continue the same run toward 500 only if learning but underfit | CONFIRMED | Real 250-step run VERIFIED; held-out evaluation finds the checkpoint not visually cleared | Supervisor's model and training direction. The 250-step run preserved checkpoint and optimizer state. The Supervisor paused model-quality research and did not authorize 500 steps in this runtime task. |
| SDXL Inpainting + trained LoRA + BiSeNet parsing + adaptive mask + IP-Adapter | DEPRECATED | UNKNOWN | Superseded by the more direct FLUX editing direction with fewer critical components. |
| FLUX.2 Klein + trained LoRA, paid FLUX.2 Pro API refinement, RunPod GPU | DEPRECATED | UNKNOWN | Superseded when Supervisor selected the $0 direction. |

Do not restore a deprecated architecture or silently change the confirmed one. Gather evidence and seek Supervisor approval for a new major decision.
