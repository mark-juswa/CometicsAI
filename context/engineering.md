# Engineering facts

As inspected 2026-09-21. Evidence status: VERIFIED for observed filesystem and tool output; all unbuilt application details UNKNOWN.

Before context setup, `F:\HAIR` contained no files. EXP-001 setup initialized local Git on `main` and committed the accepted context baseline as `78c8c64e20fdfe19c956a62cc044f9b095590a07`, including `.gitignore`. `origin` is the Supervisor-supplied `https://github.com/mark-juswa/CometicsAI.git`. Remote push status must be checked separately.

Observed local command availability during setup: Node.js `v24.7.0`, npm/npx `11.5.1`, Git `2.46.0.windows.1`. These are machine observations, not selected application runtime versions. Python version, package manager for the future application, dependencies, source tree, commands, environment variable names, data/checkpoint paths, and tests are UNKNOWN / NOT SCAFFOLDED.

JSM skills were installed with `npx --yes skills@latest add jsmastery-pro/skills -a codex -y` into `.agents/skills/`; `skills-lock.json` was created. The nine folders are architect, audit, check, debug, develop, document, scope, sync, and test. Each has `SKILL.md`. These generic skills may mention agent tools or review modes that differ from this Codex session; follow available tools and project authority, and do not run a skill merely because it exists.

EXP-001 harness: `notebooks/exp001_flux2_klein_kaggle_smoke.py`. Local verification: Python 3.11.5 compiled its syntax. Kaggle Python, packages, CUDA, training command success, and runtime remain UNKNOWN until [EXP-001](../docs/experiments/EXP-001.md) runs on an actual Kaggle GPU. The script records the AI Toolkit commit and exact installed dependencies at run time; neither has yet been observed from Kaggle.
