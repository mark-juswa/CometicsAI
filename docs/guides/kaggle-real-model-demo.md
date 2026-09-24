# HAIR CAPSTONE real-model demo on Kaggle

This handoff prepares the trained model for the existing local web app. The code and API contract passed local tests. **A live Kaggle GPU load, Cloudflare tunnel, and end-to-end image request have not yet been run with this new runtime.** The first Supervisor run establishes those facts. The 250-step checkpoint has known visual weaknesses, including face drift; this setup does not claim that model quality is solved.

## One-time preparation on your PC

The TRAIN-001 backup has already been packaged into the local ignored folder `F:\HAIR\artifacts\train001_adapter_bundle` on the Supervisor's PC. This folder contains `adapter.safetensors` (46,223,600 bytes) and `metadata.json`. The expected SHA-256 is `7e3991f8a4e502573d3e82e9ac34c89fdf3f0b66fb337abb026a5b4c9ad080ff`. The metadata identifies TRAIN-001, 250 steps, the exact FLUX.2 Klein Base revision, and the three style IDs.

If that local folder is missing, recreate it from the downloaded TRAIN-001 backup:

```powershell
cd F:\HAIR
python scripts\package_train001_adapter.py --archive "D:\Downloads\train001_250_with_evaluation.zip" --output artifacts\train001_adapter_bundle
```

In Kaggle, create one **private Dataset**, upload the two files in `F:\HAIR\artifacts\train001_adapter_bundle`, then add that Dataset to the notebook through **Add Input**. Keep the files together in the same Dataset directory. The exact Kaggle Dataset slug does not matter: bootstrap searches `/kaggle/input` for one verified bundle. Do not upload the full training archive or optimizer state for inference. The model checkpoint is a project artifact, not a file committed to Git.

Create a random shared key locally, for example `python -c "import secrets; print(secrets.token_urlsafe(32))"`. Save it as a Kaggle Secret named `HAIRCAPSTONE_API_KEY` and enable that Secret for the notebook. Keep the same value for the local backend `.env`. Do not put it in the notebook, Git, or a screenshot. The Base model is public; `HF_TOKEN` is optional and only needed if Hub access/rate limits require it. If used, put it in Kaggle Secrets too.

The current code commit is local while this machine's GitHub DNS is unavailable. A small ignored code archive, `F:\HAIR\artifacts\haircapstone_runtime_code.zip`, is provided as a second Kaggle Input until `git push origin main` succeeds. Upload that ZIP as a Kaggle Dataset and attach it to the notebook. Kaggle may expose either the ZIP or its extracted files; the cell handles both. It prefers this code Input when present. Once GitHub contains this commit, the code Input is optional and the cell clones/pulls the repository instead. Never attach more than one code archive.

## Each fresh Kaggle GPU session

1. Open a Python notebook, select a T4 GPU, enable Internet, and attach your private adapter Dataset as an Input. Until GitHub is updated, also attach the source-code ZIP as a second Input. Make sure `HAIRCAPSTONE_API_KEY` is enabled in Kaggle Secrets.
2. Use the single code cell below, or import and run [`haircapstone_inference_kaggle.ipynb`](../../notebooks/haircapstone_inference_kaggle.ipynb). The cell uses the notebook kernel's `sys.executable`; it does not call a system Python that may lack CUDA.
3. Wait for `HAIR CAPSTONE GPU SERVER READY`. Copy only the printed `FLUX_REMOTE_URL` into the local backend `.env`. Keep the Kaggle session running while using the demo.

```python
from pathlib import Path
from zipfile import ZipFile
import shutil, subprocess, sys

repo = Path('/kaggle/working/CometicsAI')
url = 'https://github.com/mark-juswa/CometicsAI.git'
inputs = Path('/kaggle/input')
code_dirs = sorted({p.parent.parent for p in inputs.rglob('kaggle_inference_bootstrap.py') if (p.parent.parent / 'backend/app/styles.py').is_file()})
code_zips = sorted(inputs.rglob('haircapstone_runtime_code.zip'))
if len(code_dirs) > 1 or (not code_dirs and len(code_zips) > 1):
    raise RuntimeError('Attach only one HAIR CAPSTONE source-code Input')
if code_dirs:
    shutil.copytree(code_dirs[0], repo, dirs_exist_ok=True)
elif code_zips:
    repo.mkdir(parents=True, exist_ok=True)
    with ZipFile(code_zips[0]) as source:
        if any(not (repo / name).resolve().is_relative_to(repo.resolve()) for name in source.namelist()):
            raise RuntimeError('Unsafe path in code archive')
        source.extractall(repo)
elif (repo / '.git').is_dir():
    subprocess.run(['git', '-C', str(repo), 'pull', '--ff-only'], check=True)
elif repo.exists() and any(repo.iterdir()):
    raise RuntimeError(f'{repo} exists but is not the project checkout')
else:
    subprocess.run(['git', 'clone', '--depth', '1', url, str(repo)], check=True)
if not (repo / 'scripts/kaggle_inference_bootstrap.py').is_file():
    raise RuntimeError('Project source lacks the current inference bootstrap; attach the code ZIP Input')
subprocess.run([sys.executable, '-u', str(repo / 'scripts/kaggle_inference_bootstrap.py')], check=True)
```

Bootstrap checks Python, CUDA-enabled PyTorch, GPU model and VRAM, `/kaggle/working` and `/tmp` free space, Internet, and the Kaggle Secret. It installs only missing or incompatible inference packages from [`kaggle_inference_requirements.txt`](../../scripts/kaggle_inference_requirements.txt), constraining the **currently installed** CUDA PyTorch build and checking it again afterward. It verifies the adapter hash and metadata before downloading the pinned public Base snapshot `black-forest-labs/FLUX.2-klein-base-4B@a3b4f4849157f664bdbc776fd7453c2783562f4d` to `/tmp/haircapstone-hf-cache`. A fresh session must download this snapshot again unless Kaggle happens to retain the same scratch storage.

The bootstrap then starts one FastAPI worker on `127.0.0.1:8765`, loads Base and LoRA once, starts an official [Cloudflare Quick Tunnel](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/do-more-with-tunnels/trycloudflare/), and checks `/health` through the public URL. It prints READY **only if that public check confirms the expected adapter hash**. Cloudflare describes Quick Tunnels as temporary development endpoints with no uptime guarantee. Kaggle tunnel connectivity is a live-run check, not an assumption.

Expected final block:

```text
=====================================
HAIR CAPSTONE GPU SERVER READY
GPU: Tesla T4
Base: black-forest-labs/FLUX.2-klein-base-4B@a3b4f4849157f664bdbc776fd7453c2783562f4d
Adapter: TRAIN-001 step 250
Styles: crew_cut, bob_hair, layered_hair
Health: https://<session>.trycloudflare.com/health
Local configuration:
GENERATION_ENGINE=remote_flux
FLUX_REMOTE_URL=https://<session>.trycloudflare.com
FLUX_REMOTE_API_KEY=<same value as your Kaggle HAIRCAPSTONE_API_KEY Secret>
=====================================
```

Logs and audit files are in `/kaggle/working/haircapstone_runtime/`: `environment.json`, `dependencies.json`, `dependency_install.log` if pip ran, `dependency_check.log`, `model.json`, `server.log`, `server_process.json`, `tunnel.log`, `endpoint.json`, and `tunnel_binary.json`. The adapter remains read only under `/kaggle/input`; only the Base cache and tunnel binary are temporary. The server keeps no generated portraits on disk.

The cell can be rerun in the **same** active session. It reuses healthy local and public services and skips package installation when versions already meet the constraints. After Kaggle expires, open a new session, attach the same private adapter Dataset, rerun the cell, and update the local `FLUX_REMOTE_URL` because the Quick Tunnel address changes.

## Connect the local application

Create `F:\HAIR\backend\.env` by copying `.env.example` if it does not exist, then edit it:

```powershell
cd F:\HAIR\backend
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

Use these values in `.env`:

```ini
GENERATION_ENGINE=remote_flux
FLUX_REMOTE_URL=https://<session>.trycloudflare.com
FLUX_REMOTE_API_KEY=<same secret value as Kaggle>
FRONTEND_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

The URL is session-specific. Do not put it in source code or `frontend/.env.local`. The browser talks only to local FastAPI. The backend forwards the validated portrait and style to Kaggle with the shared key. Only `crew_cut`, `bob_hair`, and `layered_hair` appear in the real-mode style list; the mock mode still has six prototype cards.

Start the backend in one PowerShell terminal:

```powershell
cd F:\HAIR\backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Start the frontend in another:

```powershell
cd F:\HAIR\frontend
npm ci
if (-not (Test-Path .env.local)) { Copy-Item .env.example .env.local }
npm run dev
```

Open `http://127.0.0.1:3000`. If the backend was already running, restart it after changing `.env` so it reads the new endpoint. `GET http://127.0.0.1:8000/health` should show `generator: remote_flux` and `/styles` should show exactly the three trained IDs.

## One independent smoke request

The following sends **one real inference request**, so run it only when the GPU server is READY. Use a portrait you are allowed to send to this temporary endpoint. From a PowerShell terminal with the backend dependencies installed:

```powershell
cd F:\HAIR
$env:FLUX_REMOTE_API_KEY = '<same secret value as Kaggle>'
backend\.venv\Scripts\python.exe scripts\test_remote_flux.py --url 'https://<session>.trycloudflare.com' --image 'frontend\e2e\fixtures\portrait.png' --style crew_cut --output 'artifacts\remote_flux_result.png'
```

The test prints the public health report and request metadata and saves the result. Then use the web app: upload a portrait, select one of the three styles, and press Generate. The page should show `generator: remote_flux` with the returned image. A second request should use the already loaded model. The GPU service serializes requests; a concurrent request receives HTTP 429 rather than exhausting T4 memory.

## If setup stops

- No CUDA: select a GPU and restart; do not install a different CUDA stack as a first fix.
- Missing adapter: attach the private Kaggle Dataset with both bundle files. The bootstrap refuses a wrong revision, missing metadata, hash mismatch, or more than one candidate bundle.
- Model download failure: inspect `environment.json`, Internet setting, and `/tmp` space. The Base cache is ephemeral.
- Server fails to load: inspect `server.log`. The bootstrap does not print READY.
- Tunnel URL or public health fails: inspect `tunnel.log`. This is a **Kaggle networking blocker** until a live public request succeeds. The local GPU server can still be checked at `http://127.0.0.1:8765/health` inside the notebook. For a one-off model demonstration, rerun bootstrap with `--local-only`, attach a portrait as a Kaggle Input, then run `test_remote_flux.py --url http://127.0.0.1:8765 --image <Kaggle portrait path> --style crew_cut` inside the notebook process with `FLUX_REMOTE_API_KEY` set from the Kaggle Secret. This proves model inference but does not connect the local web app. Do not assume the tunnel works because its binary installed.
- If a generation takes longer than the tunnel or proxy allows, the local app reports a timeout. Keep the warm server alive and preserve logs before changing the request protocol.

The Kaggle server and Quick Tunnel end with the session. This is a live demo runtime, not a permanent host. Public health exposes only model status; `/generate` requires the shared key. No browser request goes directly to Kaggle, so Kaggle does not need open CORS origins. Do not post private portraits through a tunnel unless their owners approve that transfer.
