# Project

Source: Supervisor's CODEX HANDOFF 001. Decision status: CONFIRMED. Evidence status for product behavior: NEEDS VERIFICATION.

HAIR CAPSTONE is a web-based AI hairstyle transformation system. A user uploads a portrait and selects a hairstyle; a project-trained generative model creates a hairstyle draft; a pretrained generative refinement stage improves it; the user receives the transformed portrait. The selected style should be recognizable while identity, face, pose, clothing, and background are preserved as much as possible. The output should be realistic enough for a capstone demonstration.

The project must train a legitimate custom generative component that directly produces image pixels. Classification, recommendation, or prompt generation alone cannot satisfy this requirement.

The Supervisor is the final decision-maker and approves major architecture changes. ChatGPT as Project Lead/AI-ML Architect sets technical direction and reviews evidence. Codex implements approved work and independently verifies technical claims.

Constraints: approximately three days of development, target monetary cost $0, and a Ryzen 5 5600G machine with integrated graphics and no suitable local CUDA GPU. Local work may cover repository, web, scripts, documentation, and light preprocessing. Heavy FLUX training or inference cannot be assumed locally. Priorities, in order: working custom generation; evidence of its contribution; working end-to-end prototype; visual quality; UI polish.

Current task boundary: context and skills setup only. Application scaffolding, dataset generation/downloads, model downloads, training, GPU experiments, and deployment are outside this assignment. The exact calendar deadline is UNKNOWN.
