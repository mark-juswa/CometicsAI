# Engineering facts

As inspected 2026-09-21. Evidence status: VERIFIED for observed filesystem and tool output; all unbuilt application details UNKNOWN.

Before context setup, `F:\HAIR` contained no files. EXP-001 setup initialized local Git on `main` and committed the accepted context baseline as `78c8c64e20fdfe19c956a62cc044f9b095590a07`, including `.gitignore`. `origin` is the Supervisor-supplied `https://github.com/mark-juswa/CometicsAI.git`; the baseline and prepared harness commits were pushed to `origin/main`.

Observed local command availability during setup: Node.js `v24.7.0`, npm/npx `11.5.1`, Git `2.46.0.windows.1`. These are machine observations, not selected application runtime versions. Python version, package manager for the future application, dependencies, source tree, commands, environment variable names, data/checkpoint paths, and tests are UNKNOWN / NOT SCAFFOLDED.

JSM skills were installed with `npx --yes skills@latest add jsmastery-pro/skills -a codex -y` into `.agents/skills/`; `skills-lock.json` was created. The nine folders are architect, audit, check, debug, develop, document, scope, sync, and test. Each has `SKILL.md`. These generic skills may mention agent tools or review modes that differ from this Codex session; follow available tools and project authority, and do not run a skill merely because it exists.

EXP-001 harness: `notebooks/exp001_flux2_klein_kaggle_smoke.py`. Local verification: Python 3.11.5 compiles its syntax, and the Pillow generator produced three matching synthetic pairs in a temporary directory. The harness pins AI Toolkit commit `a8dfcf7d7e2b38ccc7b2fb68ece9c6358e61e7a7`, constrains dependency resolution to the Kaggle-provided Torch build, uses `/tmp/hf-cache`, and stops if Torch/CUDA changes. AI Toolkit dependencies and all model/training behavior remain NEEDS VERIFICATION until the harness runs in Kaggle.

The Supervisor's later EXP-001 audit reported a working Kaggle allocation with two independent Tesla T4 GPUs, each with 14.56 GB usable VRAM and compute capability 7.5; 31.35 GB system RAM; Python 3.12.13; PyTorch 2.10.0+cu128; Torch CUDA 12.8; NVIDIA driver 580.159.04; and `torch.cuda.is_available() == true`. Torch reports BF16 support, but compute capability 7.5 has no native BF16 Tensor Core path, so the harness selects FP16. Reported free disk was approximately 1,024 GB on `/` and `/tmp`, and 19.5 GB on `/kaggle/working`. These are EXP-001 observations, not guaranteed Kaggle specifications. The earlier CPU session without `nvidia-smi` remains recorded as a failed allocation attempt.
