# HAIR CAPSTONE

The local application supports a CPU friendly `MockEngine` development preview and a `RemoteFluxEngine` that forwards portraits to a temporary Kaggle GPU server. The remote service loads FLUX.2 Klein Base 4B and our TRAIN-001 250-step conditional hairstyle LoRA. No upload is stored permanently by either server. The real model is experimental and can distort facial details.

The 250-step training run and held-out evaluation are documented in [TRAIN-001](docs/experiments/TRAIN-001.md). For the one-time checkpoint upload and fresh Kaggle session setup, follow the [real-model demo guide](docs/guides/kaggle-real-model-demo.md). A live Kaggle tunnel and full application request remain to be verified by the Supervisor.

## Run locally on Windows

The verified development machine has Node.js 24 and Python 3.11. Use two PowerShell terminals.

Terminal 1, backend:

```powershell
cd F:\HAIR\backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Terminal 2, frontend:

```powershell
cd F:\HAIR\frontend
npm ci
Copy-Item .env.example .env.local
npm run dev
```

Open [http://127.0.0.1:3000](http://127.0.0.1:3000). The backend listens at `http://127.0.0.1:8000`. If you change the backend address, edit `frontend/.env.local` and restart Next.js. `GENERATION_ENGINE` defaults to `mock`. For real mode, copy `backend/.env.example` to `backend/.env` and set `GENERATION_ENGINE=remote_flux`, the current `FLUX_REMOTE_URL`, and `FLUX_REMOTE_API_KEY`. The backend reads this file at startup. `FRONTEND_ORIGINS` defaults to both `localhost:3000` and `127.0.0.1:3000`.

## API contract

| Route | Purpose |
| --- | --- |
| `GET /health` | Returns local API status and the configured generator. |
| `GET /styles` | Returns six prototype styles in mock mode or the three trained style IDs in remote mode. |
| `POST /generate` | Accepts multipart fields `image` and `style_id`; returns status, generator, chosen style, and an image data URL with MIME type and dimensions. |

The API accepts JPG and PNG files up to 8 MB. Each image dimension must be 64 to 4096 pixels, with no more than 16,777,216 total pixels. It checks the decoded format, corrects EXIF orientation, and converts to RGB. The generator interface in `backend/app/generation/base.py` accepts the validated image and selected style and returns image bytes. `RemoteFluxEngine` implements that interface without loading FLUX on the local PC.

## Verify

With both servers running:

```powershell
cd F:\HAIR\backend
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
```

```powershell
cd F:\HAIR\frontend
npm run lint
npm run build
npm run test:e2e
```

The browser tests use the locally installed Microsoft Edge and a synthetic portrait in `frontend/e2e/fixtures/`. They cover the mock flow and a remote-mode flow with mocked GPU API responses. They do not run the real FLUX model.
