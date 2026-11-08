# Runpod Docker image, 8 November 2026

**DONE image build, local Linux checks and Docker Hub publication. VERIFIED anonymous pull access. NEEDS VERIFICATION actual Runpod GPU and website acceptance.**

The Supervisor asked Codex to complete the Docker work after the local engine became available. Docker Engine 29.5.2 built the public source context for Linux amd64, with the exact reviewed Python 3.12.13, Torch 2.10.0+cu128, compiled CUDA 12.8 and Diffusers commit. The image contains public source and dependencies. Base weights, private model archives, portraits and credentials are supplied separately.

Use this immutable reference in Runpod:

```
markuos/beautycore-runpod@sha256:972550dfeb1cc8f08189ac5106cd8fd7cc58dd1c9443b2fcc5dfb0f386ca66c0
```

Readable version tag: `markuos/beautycore-runpod:styles-20261106-01-972550dfeb1c`. An independent anonymous registry manifest request returned HTTP 200 and the exact recorded digest. No Docker Hub pull credentials are required for this public image. Registry publication uses the existing signed in `markuos` account.

## Dependency correction

The first image built successfully but failed the real CPU hand landmark model load. Importing MediaPipe alone did not load its native task library. `ldd` showed missing `libGLESv2.so.2` and `libEGL.so.1`. The Dockerfile now installs Debian `libgles2` and `libegl1` and loads the native task library during the build. The same actual hand landmark model then loaded successfully. The old image, package and failure logs remain intact. No model, generation setting, prompt, mask or source archive changed.

The first console log wrapper also encountered a Windows encoding error. Docker continued building, and its complete log was recovered through BuildKit history. This wrapper failure did not establish an image build failure. Later logs were captured as bytes.

## Verified checks

All four environments pass `pip check`. The exact GPU package and source inventory checks pass without loading a GPU. Both actual private archives pass Linux extraction, member checks, original artifact preflight and approved overlay installation. The real CPU YOLO model and MediaPipe hand landmark model load. Jupyter returns 403 to an anonymous contents request and 200 after password login. The random test password does not appear in its logs. All owned temporary test containers were removed.

All 28 Runpod preparation tests pass. The unchanged tests first encountered two Windows sandbox temporary rename denials; running outside that restriction passed all 28. Existing historical full backend failures are not reclassified by this focused run.

The context manifest contains all 18 Hair, 13 Makeup and 8 Nails style definitions, including the expanded release. Exact private archive and final Kaggle notebook hashes remain unchanged. There was no training, GPU inference, paid resource creation, Render change, endpoint registration or website cutover.

## Build inputs and size

The corrected build used `artifacts/beautycore-runpod-20261108-v3/build-context`, bound by manifest SHA256 `8702c09cd4acb6adbe2ad09b7aef30f9523049ce9928abe4148f680ea35e29b0`. The separate private ZIP is `artifacts/beautycore-runpod-20261108-v3.zip`, 246,741,958 bytes, SHA256 `f4b39d8317e23313558b6d7b7add141ba9c4e54a4360bc6cb2125d43ae86eacd`. Older v1 and v2 artifacts are preserved. Preparation manifest booleans describe their creation time; this separate receipt establishes the completed build.

The final image reports 5,140,735,919 bytes through Docker image inspection. Direct filesystem checks measure about 9.7 GiB across `/usr/local`, `/opt` and `/usr/lib`, before Base cache, private inputs and runtime outputs. Provision at least 30 GB container disk and 75 GB persistent storage at `/workspace`; verify actual free space before the Base download. Resolved package versions are retained with the logs.

BuildKit VCS metadata names the preserved local branch revision. The actual build content is the separately hash verified context, not a claim that the dirty shared checkout is a clean release checkout. The source fix and receipt are published separately.

## Next acceptance gate

Use the [Runpod guide](../guides/runpod-serving.md), starting with Pod configuration. Select the exact candidate RTX 3090 with at least 30 GiB allocated host RAM, preserve the image entrypoint and default notebook command, configure private secrets, and upload the two original `.bin` files. Leave `BEAUTYCORE_PUBLIC_URL` empty for the first run.

Actual GPU/driver compatibility, Base and adapter load, new portrait realism, full hand Nails, feature switching, restart and signed in website acceptance remain open. Kaggle backup remains intact, with its previously documented fresh session issues still separate. No live migration or unattended availability claim follows from this image build.

Structured receipt: [JSON](runpod-docker-build-20261108.json). Sanitized build, CPU model and Jupyter logs plus resolved dependencies are under [evidence](runpod-docker-20261108/build-02.log).
