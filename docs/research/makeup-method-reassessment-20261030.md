# Makeup method reassessment — 30 October 2026

Status: **source audit VERIFIED; alternative quality/runtime UNKNOWN; replacement PROPOSED / NOT STARTED.**

## Why reassess

MAKEUP-ALIGN-001 corrects source eye placement and makes procedural hairs finer, yet all four comparisons still fall short of the user's reference. Better coordinates do not provide realistic lash/cosmetic material rendering. Stop this custom-stroke branch rather than iterate strength indefinitely. Current trained MAKEUP-001 and failed transfer/inpaint/tone experiments remain historical evidence, not automatic fallback candidates.

The target remains visible reference-like cosmetics with source identity/complexion retained. A new full-image generator can reintroduce whitening, so it must be tested against that failure explicitly. No model has passed that gate.

## First source-audit candidate: Stable-Makeup

[Official repository](https://github.com/Xiaojiu-z/Stable-Makeup) documents source-image, makeup-reference and facial-structure conditioning, Stable Diffusion1.5, SPIGA/facelib, pretrained weights linked through Google Drive, and Apache2.0 code licensing. Those are upstream descriptions, not our measured results. All checkpoint/base/encoder terms and access still require verification.

Read-only snapshot pinned to commit88c8ca512261e1f9125684178423e6355ed5ad0a under artifacts/makeup-render-20261030/method-reassessment with original file hashes. Nothing executed or installed; no candidate weights downloaded.

Concrete blockers in pinned source:
- infer_kps.py fails Python AST parsing at line43, with an extra period after the model-path string.
- It imports utils.pipeline_sd15, but the published tree has pipeline_sd15.py at repository root and no utils/pipeline_sd15.py.
- It explicitly constructs two ControlNets plus UNet/detail encoder and loads float32 on CUDA. T4 memory and full startup cost are not verified.
- Its requirements snapshot contains old Torch2.0.1/diffusers0.25.1/transformers4.34.0 and many unrelated packages. Do not install that file into the working environment or assume Python3.12 compatibility.
- Auxiliary image encoder, facial detector/SPIGA assets, learned components and base model all need a complete inventory. A Drive link is not proof that all assets are accessible.
- SPIGA structure conditioning is part of the upstream method. Do not substitute MediaPipe landmarks merely because our local pilot now has them.

Sources: [pinned inference](https://github.com/Xiaojiu-z/Stable-Makeup/blob/88c8ca512261e1f9125684178423e6355ed5ad0a/infer_kps.py), [pinned requirements](https://github.com/Xiaojiu-z/Stable-Makeup/blob/88c8ca512261e1f9125684178423e6355ed5ad0a/requirements.txt).

## Alternative inspected, not selected

[EleGANt official repository](https://github.com/Chenyu-Yang-2000/EleGANt) documents trained checkpoints and locally editable transfer, but specifies CC BY-NC-SA4.0. It is not proposed as an unrestricted client-salon deployment replacement. Runtime/appearance were not tested. This is a documented code-license distinction, not a legal determination for the entire downstream system.

## Smallest next feasibility plan

1. Complete Stable-Makeup's checkpoint/auxiliary asset inventory, access/terms and dependency closure; pin actual revisions/hashes. If assets cannot be verified, stop this candidate before GPU setup.
2. Create an isolated source snapshot and minimal evaluation runner; repair confirmed entry syntax/import issues with a preserved patch. No changes to working demo notebooks, global packages or BeautyCore contracts.
3. Validate Python/CUDA compatibility separately. Measure peak RAM/VRAM and initial/warm latency in an isolated Kaggle session; do not assume it fits T4. Offload/precision changes require correctness checks, not silent speed shortcuts.
4. At most four source portraits with one approved reference and frozen inference settings. Compare source/reference/raw output; assess skin-tone drift, identity/expression/texture, lashes, edge blending and visible makeup. No training required for this feasibility test, but pretrained results can still fail.
5. Only after runtime and human appearance acceptance propose a versioned Makeup service replacement, catalog/description compatibility and Render/Kaggle rehearsal. Preserve snapshots and Hair/Nails/consultation ownership controls.

This is a proposed change of Makeup method. Neither source-code availability nor upstream sample images establish client-ready quality. Existing deployment remains unchanged.

## Deadline update

User confirms within24hours and free only. Paid API path ruled out. Public author-linked Drive folder now inspected and visibly lists pytorch_model.bin, pytorch_model_1.bin, pytorch_model_2.bin; this establishes public listing only, not complete accessible/verified assets. Any next trial needs a strict setup/appearance cutoff and an honest fallback. No further custom-stroke sweeps or new training.
