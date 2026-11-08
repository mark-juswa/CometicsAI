# 0019. Runpod serving with Kaggle fallback

**Date**: 2026-11-08
**Status**: In Progress

## Summary

Prepare a Runpod Pod serving package for the existing shared Hair, Makeup and Nails system. Keep the Render website and every Kaggle notebook and private input intact. Local preparation does not establish a working Runpod GPU deployment.

## Context

The Supervisor selects Runpod after the provider comparison and explicitly retains Kaggle as backup. Current application evidence validates the corrective Makeup checkpoint on T4. The fresh Kaggle notebook has separate environment/input failures. The migration must preserve the tested generation implementation and avoid another runtime assembled from an unspecified latest image.

## Requirements

AC-1: Verify the two existing private serving archives and every extracted member before use. Preserve release `styles-20261106-01` and all 18 Hair, 13 Makeup and 8 Nails styles. Reuse the exact final serving notebook's release assembly helpers and source payload, bound to its recorded SHA256.

AC-2: Keep the same Base revision, four adapters, captions, settings, serialization, tensor checks and Nails CPU separation. No training, new compositor or application UI change.

AC-3: Define a separate candidate Runpod RTX 3090 profile with Python 3.12.13, Torch 2.10.0+cu128, CUDA 12.8 and the reviewed GPU package versions/Diffusers commit. Enforce the expected GPU name, at least 20 GiB GPU memory and at least 30 GiB usable system/container RAM. Historical Kaggle review files and guards remain unchanged. A candidate profile is not evidence of approved output quality.

AC-4: Provide a container recipe and one foreground start command, environment based secrets, configurable input/work paths, persistent Base cache and logs. Model binaries and credentials never enter the public container build context. The container recipe can be built without GPU; Linux build and real GPU acceptance remain separate gates.

AC-5: Reuse the authenticated facade on loopback 8800, private GPU on loopback 8765, current Cloudflare tunnel and HMAC registration. This first bounded migration requires no Render source or URL policy change. Native Runpod proxy support is deferred. Empty website URL means validation only, no production registration.

AC-6: Refuse duplicate local startup, stop owned children when the foreground owner exits, preserve logs on failure and never retry a generation. Existing active Kaggle registration must win until the operator stops that session and lets its lease expire. No automatic provider failover, forced takeover or database change.

AC-7: Package source, exact private inputs, hashes and an operator guide into a separately named local private ZIP. Preserve original Kaggle files byte for byte. Verify staging against real archives and test failure boundaries with synthetic processes/HTTP, without buying GPU time.

AC-8: Document required build, image publication, real environment checks, cross feature real generation, full catalog readiness and restart/cutover/rollback evidence before calling Runpod live. No paid resource creation or website cutover in this preparation task.

## Options considered

One long running Pod retains existing temporary process state and requires the fewest behavior changes. Native provider endpoints would require changing the Render URL policy. Serverless would also require new state ownership/routing. The first option is selected for this preparation; later endpoint and lifecycle changes remain separate decisions.

## Decision

CONFIRMED provider direction: Runpod preparation alongside Kaggle, as requested by the Supervisor. Reuse current artifact verification, model download, worker start, release overlays, authenticated CPU facade and registrar through a small Runpod orchestration entry point. Use Python 3.12.13 with the registry verified base image index digest `sha256:4766d8b510c428e595d74b9cc5bbb2fae8e26316fffb4adc89908d79aacd58a2` and reviewed dependency pins; after a successful build, deploy the full server image's immutable digest. Pinning the base does not establish a completed server image build.

Implementation skills: architect and develop. User authorization covers preparation; paid launch and real acceptance are not inferred from local tests. No additional product choice is needed to prepare the bounded candidate. An independent review is optional and does not substitute for real GPU acceptance.

## Value sourcing

| Value | Source |
| --- | --- |
| Archive names/hashes, release and overlays | Final notebook SHA `b4a4e1c1482fd060d194f19f5570b6221131379e8214d18c064a713452ab08fd` |
| Model and package contract | Unmodified reviewed GPU archive and Gate 2 environment |
| New GPU identity | Candidate profile, NVIDIA GeForce RTX 3090, not historical T4 evidence |
| Secrets | `AI_BACKEND_API_KEY`, `AI_REMOTE_API_KEY`, `GEMINI_API_KEY`, optional `HF_TOKEN`, environment only |
| Website | Explicit `BEAUTYCORE_PUBLIC_URL`; empty means no registration |
| Persistent data | Operator mounted workspace, default `/workspace/beautycore` |
| CPU environment pins | Existing CPU archive requirement/constraint files |
| Readiness | Actual authenticated facade readiness and exact assembled release membership |

## Build plan

1. Extract reusable setup definitions/payload from the hash bound final notebook without executing its Kaggle startup. Verify real archive assembly locally. AC-1, AC-2.
2. Add Runpod runtime/profile checks and orchestration using existing worker primitives. Keep the original worker sources and evidence immutable. AC-3, AC-5, AC-6.
3. Prepare the container build context, isolated CPU/GPU environments and persistent paths. AC-4.
4. Package the private handoff, operator commands and rollback guide, then exercise meaningful offline checks. AC-7, AC-8.

## Migration plan

Strategy: parallel preparation, deliberate cutover. First build/publish the image and validate Runpod without website registration. Then stop the serving Kaggle process only after its admitted work finishes, allow normal lease expiry, and start the validated Runpod configuration with the website URL. Confirm registration and real website requests. To roll back, stop Runpod and start the preserved Kaggle notebook using its own verified environment and normal registration. Temporary process state is not transferred; start fresh consultations after a restart.

## Rationale

The worker, model artifacts and external API already solve generation. Provider startup and environment coupling are the gap. Reusing them keeps migration evidence interpretable. The current tunnel is a deliberate compatibility bridge, with the same temporary availability limits as before. This does not claim durable unattended hosting or automatic recovery.

## Consequences

Client operations can become a prepared image plus two private inputs, secrets and one start command. The Pod bills while running and storage bills while retained. New hardware quality, timing, memory and availability remain unverified. The local Docker CLI exists but its Linux engine is currently unavailable, so the image build must be reported separately from source/package checks.
