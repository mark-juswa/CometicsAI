# Runpod server preparation, 8 November 2026

Follow up: the [Docker build and publication receipt](runpod-docker-build-20261108.md) records the later completed image, native dependency correction and Linux acceptance. This original preparation record is preserved below.

**DONE local source, private package and offline preparation. NEEDS VERIFICATION Linux image build and Runpod GPU acceptance. NOT STARTED registry image publication, paid provider launch or website cutover.**

VERIFIED public source publication: commit `f4b947f20e77ae427376114cc7f3a6577e8f1df6` is on `main`, `codex/render-kaggle-demo` and `codex/runpod-serving`, confirmed by an independent remote head read after a normal atomic push. Nineteen selected public source/report files were published through an isolated index; the active local branch/index and private artifacts remain intact. This publishes the server recipe, not a built container image or live endpoint.

The Supervisor selects Runpod preparation with Kaggle backup, then chooses local verification rather than independent architecture review. Spec `0019-runpod-serving.md` records the migration boundary. The existing Render/API contracts, generation methods, models, prompts, tensor checks and all 39 styles are preserved. The first candidate targets one NVIDIA GeForce RTX 3090. No new hardware quality or speed is claimed.

`scripts/package_runpod.py` binds the exact final serving notebook and extracts its reusable definitions/payload without executing Kaggle startup. It verifies both private archives and the matching Render catalog, then creates a public Docker context with the model inputs kept separate. `deploy/runpod/runtime.py` adds provider paths, environment secrets, host/container RAM guards, duplicate startup lock, CPU vision checks, original artifact preflight, persistent Base download, approved overlays and existing worker/facade/registration. It monitors and cleans up owned processes and never submits or replays a generation. Empty website URL means no production registration. An existing Kaggle lease conflict is not overridden.

The recipe isolates GPU, CPU API, CPU segmentation and notebook dependencies. It provides password protected Jupyter setup and foreground serving modes. The official Python 3.12.13 base index digest was resolved through Docker registry inspection and pinned: `sha256:4766d8b510c428e595d74b9cc5bbb2fae8e26316fffb4adc89908d79aacd58a2`. The completed server image will need its own build/publication digest.

## Local validation

28 Runpod tests pass, covering notebook binding, safe helper export, missing archives, changed distribution, path traversal, exact dependency/hardware rejection, container memory, exact catalog membership, secret errors, child death, validation only startup, lease conflict, process cleanup and the container allowlist. Thirty existing Makeup API/runtime/startup checks and all 44 Kaggle starter/recovery/registration/resume checks pass. Three sandbox temporary file rename denials disappear when the unchanged Kaggle tests run outside that restriction. These 102 focused passing checks do not resolve the previously documented historical full suite failures.

Both actual private archives were extracted and checked. The original bundle and Gate 2 artifact preflight pass. Approved Hair/Nails and corrective Makeup overlays install onto a fresh tree, with all six corrective overlay members matching their manifest. No Base/GPU was loaded and no generation was requested. Original Kaggle notebook and archive hashes remain unchanged. Final build context file hashes pass, contains no model binaries, and contains none of the inspected actual local credential values. The assembly helper bytes in the initial staging proof match the final context.

## Private handoff

Final package: `artifacts/beautycore-runpod-20261108-v2.zip`, 246,741,306 bytes, SHA256 `228cd016dfdc2660350d50248e0e586f895aede69dc5a1ad811efb7e20ba47f7`. It contains `build-context/`, both unchanged `.bin` inputs under `inputs/`, and `START-HERE.md`. Keep this ZIP private. Only the source context belongs in the public container build. The initial local package is preserved; the final package pins the registry verified base and includes the complete context allowlist. No prior experiment, dataset, checkpoint or Kaggle artifact was overwritten.

## Remaining gate

Docker CLI exists but its Linux engine was initially unavailable. One bounded Desktop start timed out. The attempt outside the sandbox and subsequent engine probe did not become responsive during verification, and the waiting CLI commands were interrupted. No Windows/WSL configuration was changed. No image build completed or registry image was pushed. The cause of the engine startup problem is UNKNOWN. This is not an automatic approval review rejection or a demonstrated model/server failure.

Next, build/check/publish the context using a working Linux Docker engine and record the full image digest. Then launch one matching Runpod Pod, verify the actual environment, real model/application results and all catalog coverage without website registration, followed by deliberate cutover and restart/rollback checks. No paid resource, cloud setting, credential or website connection was changed. Preserving Kaggle backup files does not establish that a new Kaggle session's environment/input problems are resolved.

Operator guide: [Runpod setup](../guides/runpod-serving.md). Structured evidence: [local receipt](runpod-preparation-20261108.json).
