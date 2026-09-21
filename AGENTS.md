# HAIR CAPSTONE agent entry point

Read [current state](context/state.md) first, then the context relevant to the task and the actual files involved. This repository began as an empty, unscaffolded directory. Do not infer implementation from the intended design or chat history.

- [Project](context/project.md): product, roles, constraints.
- [Architecture](context/architecture.md): approved direction and invariants.
- [AI/ML](context/ai-ml.md), [data](context/data.md), [evaluation](context/evaluation.md): intended methods and verification gaps.
- [Decisions](context/decisions.md): approvals and superseded options.
- [Engineering](context/engineering.md): repository and environment facts only.
- [Scope](docs/scope/roadmap.md): coarse build sequence. Future load-bearing specs belong in `docs/specs/`; experiment evidence belongs in `docs/experiments/`; detailed research may go in `docs/research/`.
- Generic JSM workflow skills are installed in `.agents/skills/`. Read a skill's `SKILL.md` when using it. Use only the stages the task needs. The current project context was established before scaffolding by explicit Supervisor instruction; a later implementation audit must derive commands and layout from real files.

The Supervisor approves major architecture changes. The Project Lead advises and reviews. Codex implements and verifies approved work. For **what exists**, actual files, configuration, runtime, data, and logs outrank synchronized context and memory. For **what should be built**, explicit Supervisor decisions outrank implementation. Report an implementation conflict with approved architecture as **ARCHITECTURAL DRIFT**; report a stale implementation claim as **DOCUMENTATION DRIFT**. Investigate before changing the authoritative record.

Use decision statuses `CONFIRMED`, `PROPOSED`, `DEPRECATED`; evidence statuses `VERIFIED`, `EXPERIMENTAL`, `NEEDS VERIFICATION`, `UNKNOWN`; progress statuses `NOT STARTED`, `IN PROGRESS`, `BLOCKED`, `DONE`. Never turn a plan into a verified result. Do not guess dataset counts, model capability, GPU availability, commands, or performance.

At task end, update `context/state.md`; change `context/engineering.md` only from inspected implementation; record real decisions in `context/decisions.md`; reconcile scope and specs. Preserve experiment configurations, logs, outputs, and conclusions in `docs/experiments/` before summarizing evidence in context. Stop and surface an unresolved major architectural choice to the Supervisor.
