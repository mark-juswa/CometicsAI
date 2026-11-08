# BeautyCore Runpod setup and Kaggle backup

This is the preparation guide for release `styles-20261106-01`, 18 Hair, 13 Makeup and 8 Nails styles. The Linux image is built, checked and published. The Runpod GPU profile remains a candidate until actual GPU/application checks pass. Kaggle remains unchanged as backup. No retraining is required for this provider migration.

## RTX A6000 alternative candidate

If selecting the reported Community RTX A6000 offer, change the image to:

```
markuos/beautycore-runpod@sha256:614bddb4352ef3127251583f062240ef1fb749e08a7cb137027f3c1cbf090ffa
```

Select exactly **NVIDIA RTX A6000 (48 GB)**. This separate candidate retains the same model/release/settings and enforces at least 44 GiB visible VRAM, 30 GiB allocated host RAM, the exact reviewed packages and compute capability 8.6 or newer. The original 3090 image below remains available for 3090 hardware. All local Linux checks and 30 tests pass; real A6000 GPU acceptance remains open. [Candidate evidence](../experiments/runpod-a6000-candidate-20261108.md).

Keep the existing secrets, disks, HTTP8888 and default notebook startup. The upload/stage/start steps below are identical. Leave the website URL empty until real validation. The reported USD0.33/hour is a catalog GPU quote with allocation unconfirmed, not a promise of capacity or total cost. Rebuild this candidate using `--profile rtx-a6000` with the packaging command and a new output directory; the default packaging profile remains 3090.

## Existing Pod login correction

The corrected A6000 image above includes the Runpod reverse proxy origin fix. In the existing Pod's Edit settings, replace the image digest and preserve the volume, private secrets, HTTP8888 and empty startup override. Keep the notebook password at 20+ characters. Apply the image update, then open the Pod HTTPS8888 URL at `/lab` without any `?token=` query and log in. Provider variable `RUNPOD_POD_ID` binds the allowed origin to this Pod. Do not disable XSRF checks or allow wildcard origins. [Reproduced failure and verification](../experiments/runpod-jupyter-proxy-fix-20261108.md).

The earlier A6000 image could serve login but reject its POST through the proxy. Local password auth alone did not establish Runpod proxy compatibility. The corrected image passes the actual proxy header regression as well as 31 unit tests and all earlier Linux checks. Live browser recovery still requires the Pod update. The Runpod readiness badge can continue probing with a token that this password protected server does not accept; the badge alone is not proof of browser login failure or success.

## Ready image (RTX 3090)

Docker work is complete on 8 November 2026. You can skip building and publishing the image and continue at **Configure the Pod** using:

```
markuos/beautycore-runpod@sha256:972550dfeb1cc8f08189ac5106cd8fd7cc58dd1c9443b2fcc5dfb0f386ca66c0
```

Version tag: `markuos/beautycore-runpod:styles-20261106-01-972550dfeb1c`. Public pull access, exact dependency checks, real private archive staging, both CPU vision model loads and password protected Jupyter login pass. The image includes support for all 18 Hair, 13 Makeup and 8 Nails styles, including expanded styles. Upload the two private `.bin` inputs separately. Weights and credentials are not in the public image. [Build evidence](../experiments/runpod-docker-build-20261108.md).

Use at least 30 GB container disk and 75 GB persistent storage mounted at `/workspace`. Actual GPU generation and website cutover remain separate acceptance steps. Kaggle backup remains intact.

## What is prepared

`scripts/package_runpod.py` creates a separate private ZIP with a public container build context and the two existing private model inputs. It derives release assembly from the exact reviewed final notebook and preserves all model/caption hashes. The foreground server uses the existing GPU worker, CPU facade, Nails environments, Cloudflare tunnel and HMAC website registration. Render source, database and URL policy do not change for this first migration.

The default container opens password protected JupyterLab for familiar browser file upload and a terminal. Jupyter lives in its own Python environment. GPU inference, the CPU API and CPU segmentation also have separate environments. Once validated, the image can start the AI directly instead of opening Jupyter.

## Prepare and build the image once

These commands are optional when using the current published A6000 image above. For rebuilding, generate a fresh context from the current checkout. Historical v1/v2 packages lack the MediaPipe native fix; v3 and the first A6000 package predate the Runpod proxy correction. Do not use those historical contexts to claim the current login fix.

Choose a new package output directory when rebuilding. The path below is an example; do not overwrite an existing artifact. Add `--profile rtx-a6000` for A6000 hardware. The unchanged default is RTX3090, whose older published image does not include this new proxy fix.

From the repository root, with the original private `.bin` inputs in local `client/`:

```powershell
python scripts/package_runpod.py --output artifacts/beautycore-runpod-20261108-v3
```

Use a new output name for another build. Keep the resulting ZIP private. The `build-context/` subfolder contains source and requirements only, with an explicit Docker allowlist. It contains no portraits, adapters or credentials. Do not build with the full repository or the private input folder as context.

On a machine with a running Linux Docker engine:

```powershell
docker build --platform linux/amd64 -t YOUR_DOCKER_USERNAME/beautycore-runpod:styles-20261106-01 artifacts/beautycore-runpod-20261108-v3/build-context
docker login
docker push YOUR_DOCKER_USERNAME/beautycore-runpod:styles-20261106-01
docker image inspect YOUR_DOCKER_USERNAME/beautycore-runpod:styles-20261106-01 --format '{{json .RepoDigests}}'
```

Replace `YOUR_DOCKER_USERNAME` with your own registry account. No password belongs in these commands, Dockerfile or Git. Use the resulting `username/image@sha256:...` digest in Runpod, rather than a mutable latest tag. The source recipe pins Python 3.12.13 by registry digest and the reviewed GPU dependency versions. The official base digest was resolved through the registry on 8 November. The completed server image and its independent public registry verification are recorded above. Image build does not require a local GPU. The first image exposed missing MediaPipe native libraries during real model load; the published image includes the correction and passed the same check.

## Configure the Pod

Use an on demand Linux amd64 Pod. The first prepared candidate accepts exactly **NVIDIA GeForce RTX 3090**, at least 20 GiB VRAM and 30 GiB allocated system RAM. Choose at least 32 GiB usable RAM, preferably a listing advertising 48 GB or more. Do not choose an inexpensive offer with only 25 GB host RAM. Another GPU requires a separate reviewed profile; changing a name to bypass the guard is not validation.

Use the built image digest. Mount persistent storage at `/workspace`. Use 75 GB persistent storage for Base/model cache, private inputs and run artifacts, plus at least 30 GB container disk for the image and temporary libraries. The measured source/dependency filesystem uses about 9.7 GiB before model cache and runtime data. The existing Base download checks for 30 GiB available cache disk space before downloading, so verify free space on the mounted volume. Persistent storage continues billing while compute is stopped.

Expose HTTP port **8888 only** for notebook setup. Leave 8765 and 8800 private. The existing authenticated CPU facade is exposed through a temporary Cloudflare tunnel, not an unprotected GPU proxy. Keep the default container command `notebook` for the initial setup.

Configure these Runpod environment variables privately:

| Name | Purpose |
| --- | --- |
| `JUPYTER_PASSWORD` | At least 16 characters, password for browser setup |
| `AI_BACKEND_API_KEY` | At least 32 characters, must match the existing Render service |
| `AI_REMOTE_API_KEY` | At least 24 characters, private local GPU authentication |
| `GEMINI_API_KEY` | Existing Consultation provider key |
| `HF_TOKEN` | Optional, if required to download the pinned model under the account |
| `RUNPOD_WORKSPACE` | Optional, defaults to `/workspace/beautycore` |
| `BEAUTYCORE_PUBLIC_URL` | Leave empty for initial validation; later use the deployed website URL |

The notebook password is stored only as a private hash in the mounted workspace. Do not expose the notebook publicly without that password or share your provider account password. No actual credentials are in the package.

## Upload and first start

Open the Pod's Jupyter HTTP service, log in with the configured notebook password and upload the **two `.bin` files** into `/workspace/beautycore/inputs/`. The filenames must remain:

1. `capstone_train002_20260928_v1.bin`
2. `beautycore_makeup_release_20261106.bin`

Upload the extracted files, not the enclosing ZIP. The files and expected hashes are in the ZIP manifest/build manifest. No Kaggle dataset attachment is used on Runpod. Keep the original inputs and Kaggle notebooks intact.

Open a Jupyter terminal and run:

```bash
python /opt/server/runtime.py stage
python /opt/server/runtime.py start
```

The first command verifies archives and stages a disposable source check without loading models. It uses a separate `stage-check` directory and refuses overwrite. For another check, supply a new explicit `--work` directory. `start` uses a new private run directory each time and one workspace lock. Keep that terminal/process running. The Base cache persists under `/workspace/beautycore/hf-cache`; weights and adapters are not loaded into the public image.

Startup verifies the image distribution, both complete archives, source pair, exact GPU environment and original artifact evidence. It checks both CPU vision model loads, starts one foundation with the approved overlays, verifies all catalog counts and the release hash, and exposes the authenticated facade. With no website URL it reports **READY_FOR_RUNPOD_VALIDATION**, without registering or replacing the Kaggle lease. The environment report remains a candidate; readiness is not a visual quality approval.

Logs, environment/readiness records and per run status are under `RUNPOD_WORKSPACE/runs/`. `latest-run.txt` records the latest run directory. Share only the needed sanitized failure stage, not environment dumps, secrets or portrait files. Startup never submits a generation request and never automatically retries one.

## Run the existing generation comparisons

After READY_FOR_RUNPOD_VALIDATION, keep the server terminal running. Upload the current repository file `scripts/makeup_corrective_application_probe.py` to `/workspace/makeup_corrective_application_probe.py` in Jupyter. Open a second Terminal and run:

```bash
python /workspace/makeup_corrective_application_probe.py runpod
```

Run once. This reuses the accepted13 Makeup comparisons, two Hair cases and one Nails crop switching case, with environment secrets and private persistent results. Download `/workspace/beautycore/validation/runpod_application_results.zip` through Jupyter and review the images before website connection. On failure or uncertain completion, preserve results and do not replay the command. It never registers the website. The crop does not validate full-hand Nails. [Preparation and test evidence](../experiments/runpod-validation-preparation-20261109.md).

## Real validation and cutover

Before calling this a completed migration, capture the image digest, actual GPU profile/environment, Base and adapter readiness, all 39 style IDs and actual representative Hair, corrective Makeup and full hand Nails results. Check a new portrait for identity/complexion/style fidelity, including the accepted strong complete Makeup direction. Check cross feature adapter restoration, Consultation, save/booking as applicable, then a full stop/start using the persistent cache. Reuse existing reviewed comparisons; do not replace visual inspection with health or tensor checks. No real Runpod quality or speed is established by local tests.

After these checks, wait for in progress work to finish. Stop the active Kaggle serving session, allow its existing lease to expire normally (up to 180 seconds), and stop the validation Runpod server with Ctrl+C. Set `BEAUTYCORE_PUBLIC_URL=https://beautycore-demo.onrender.com` through the private Pod environment and start again. Confirm **CONNECTED_TO_WEBSITE**, the exact new release and real signed in website generation. A 409 registration conflict means another live session owns the lease; do not force an endpoint/database change or replay generation.

For later automatic server startup, change the container command from `notebook` to `start` using the same image and persistent volume, with the website URL and three AI secrets configured. The image entry point already invokes the runtime. You can omit the notebook password if notebook mode is not used. Capture a successful restart before giving this operating mode to the client. Keep the Pod running while serving; closing the browser is not a compute stop, and stopped compute cannot answer customer requests.

The server monitors its owned processes. A failure or termination stops its children, preserves run logs and lets the website lease expire. It does not restart a generation or silently switch providers. In memory photos/jobs/consultations do not survive process restart; begin a new consultation afterward. Retained run folders can contain private staging/review assets, so treat the volume as private.

## Kaggle rollback

Wait for admitted work to finish, then stop Runpod compute. Wait for its website lease to expire, start the original Kaggle notebook with its two matching private inputs and reviewed environment, and wait for its normal website connection acknowledgement. No database rewrite, model conversion, frontend redesign or new API contract is required. The original Kaggle startup version/input issues still need their own verified environment and attachment correction; preserving backup files does not establish that a fresh Kaggle session works.

The Docker image is built and publicly published. No paid Pod, website cutover or GPU generation was performed during preparation or local image verification. Provider environment acceptance and real application validation remain separate milestones.
