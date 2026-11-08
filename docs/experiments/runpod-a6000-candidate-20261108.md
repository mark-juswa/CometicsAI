# Runpod RTX A6000 candidate, 8 November 2026

DONE local profile preparation, Linux image verification and public publication. VERIFIED anonymous manifest access. NEEDS VERIFICATION actual RTX A6000 allocation, environment and real generation. No paid resource was created.

The user supplied agent report identifies Community RTX A6000 catalog pricing at USD0.33/hour with Low inventory signals in EU-SE-1 and US-TX-1. Allocation is not established. The reported 4090 has no signal; A40 and Blackwell MIG signals were not inspected. They are not confirmed alternatives.

NVIDIA documents the RTX A6000 as Ampere with 48 GB VRAM and compute capability 8.6. Sources: [product](https://www.nvidia.com/en-us/products/workstations/rtx-a6000/), [CUDA GPU table](https://developer.nvidia.com/cuda/gpus). This supports a candidate using the existing compiled stack, not a claim of tested model output on this GPU.

## Image

```
markuos/beautycore-runpod@sha256:ced910be7e93b84f178c8841aefc5bf47099f4442948d7538664c04fe84b0dd4
```

Tag: `markuos/beautycore-runpod:styles-20261106-01-a6000-ced910be7e93`.

The separate profile requires exactly `NVIDIA RTX A6000`, at least 44 GiB CUDA visible VRAM (allowing capacity overhead on a nominal 48 GB card), compute capability at least 8.6 and at least 30 GiB usable host/container RAM. Python 3.12.13, Torch 2.10.0+cu128, compiled CUDA 12.8, reviewed dependencies and Diffusers commit remain exact. The 3090 image and default profile remain intact. Runtime enforcement code is unchanged.

`scripts/package_runpod.py --profile rtx-a6000` selects this profile at package creation and binds its actual ID and bytes into the manifest. Default `rtx3090` remains unchanged; unknown choices fail before output creation. Comparing the actual new context with the verified v3 context shows only `profile.json` differs among inventoried files; the manifest consequently differs too. All generation code, release assembly, package requirements, model/input hashes and 18 Hair/13 Makeup/8 Nails catalog are identical. No template, website, Kaggle, model or dataset changed.

## Verification

All 30 focused Runpod tests pass, including cross profile GPU rejection, insufficient A6000 VRAM, insufficient system RAM, wrong dependencies and invalid profile refusal. The full Linux image passes all four pip checks, exact source/GPU package imports, real private archive assembly, original artifact/overlay checks, real YOLO and MediaPipe model loads and Jupyter password authentication (anonymous 403, signed in 200). Test password is absent from logs. A separate image check confirms its manifest ID matches the actual embedded A6000 profile. No GPU was available locally; CUDA compiled package checks are not hardware inference checks.

Build exit code is zero. Public registry manifest is independently readable without account credentials, HTTP 200, with the exact published digest. Logs and structured receipts are retained under `docs/experiments/runpod-docker-20261108/a6000/` and `runpod-a6000-candidate-20261108.json`. Existing packages/images/logs are preserved. No image generation, training or website registration occurred.

## Next step

Change the private template image to this digest and select one Community RTX A6000. Keep the same secrets, /workspace mount, 30 GB container disk, 75 GB persistent disk, HTTP8888 and empty startup override. Keep BEAUTYCORE_PUBLIC_URL absent. Deployment requires an explicit spending ceiling that allows the reported USD0.33/hour GPU, plus storage. An inventory signal can still fail allocation.

Before downloading Base, verify the actual GPU, CUDA initialization, at least 44 GiB VRAM, at least 30 GiB allocated system/container RAM and workspace free space. Then use the two original inputs, `runtime.py stage`, and `runtime.py start`. Capture READY_FOR_RUNPOD_VALIDATION. Real output quality, switching, restart and website acceptance remain open. Do not edit a running profile to bypass checks or assume the original 3090 image accepts this GPU.

## User supplied first Pod logs

User supplied extraction output shows layer 2e32012bcceb reaching Pull complete and layer c25a9771eda7 extracting. Screenshot additionally shows repeated start container/begin entries at 11:34:03, 11:34:19, 11:34:35 and 11:34:51 PM. These may indicate repeated startup attempts; a restart loop is a hypothesis, not a confirmed root cause. No application stdout/stderr or exit code is supplied. Need actual container logs after startup before attributing failure to extraction, secrets, command overrides or platform. Local notebook proof remains valid but does not establish this Pod startup.

Container log follow up: user supplied screenshot confirms repeated `Runpod startup stopped: ValueError . Inspect the private run logs and setup guide.` This confirms failed application startup with retry, not only extraction. In the unchanged default notebook path, the explicit ValueError checks JUPYTER_PASSWORD length below 16 (including absent/empty). The runtime catches arbitrary exception text to avoid leaking secrets, so the public log omits this known actionable reason. Missing/short notebook password is the leading code-supported hypothesis; actual existing Pod environment and CMD are not yet inspected. Recommend correcting the existing Pod variable and confirming default notebook command before any image/model changes. No successful restart is established.

Root cause localized from existing Pod edit screenshot: JUPYTER_PASSWORD value is visibly shorter than the enforced 16 character minimum. Workspace path matches /workspace/beautycore and no start-command override is configured. This matches the explicit notebook ValueError and repeated sanitized container log. Recommend replacing the notebook password with a private 20+ character value and saving the existing Pod. Successful recovery remains unverified until new logs/login. Screenshot contains credentials; no credential values are retained or echoed in this record.
