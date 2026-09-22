# HAIR CAPSTONE System MVP

This is a local, CPU friendly development preview. You can upload a portrait, choose a prototype hairstyle, and generate a result through the FastAPI backend. The active `MockEngine` returns the normalized portrait unchanged. It does not perform AI hairstyle editing. No upload is stored permanently.

The real hairstyle dataset, hairstyle LoRA, FLUX integration, refinement, and deployment have not started.

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

Open [http://127.0.0.1:3000](http://127.0.0.1:3000). The backend listens at `http://127.0.0.1:8000`. If you change the backend address, edit `frontend/.env.local` and restart Next.js. `GENERATOR_MODE` defaults to `mock`. `FRONTEND_ORIGINS` defaults to both `localhost:3000` and `127.0.0.1:3000`; set it as a comma separated environment variable if your frontend uses another origin.

## API contract

| Route | Purpose |
| --- | --- |
| `GET /health` | Returns `{"status":"ok","generator":"mock"}`. |
| `GET /styles` | Returns six centralized prototype hairstyle definitions. |
| `POST /generate` | Accepts multipart fields `image` and `style_id`; returns status, generator, chosen style, and an image data URL with MIME type and dimensions. |

The API accepts JPG and PNG files up to 8 MB. Each image dimension must be 64 to 4096 pixels, with no more than 16,777,216 total pixels. It checks the decoded format, corrects EXIF orientation, and converts to RGB. The generator interface in `backend/app/generation/base.py` accepts the validated image and selected style and returns image bytes. A future FLUX engine can implement that same interface without changing the frontend request or response shape.

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

The browser tests use the locally installed Microsoft Edge and a synthetic portrait in `frontend/e2e/fixtures/`. They cover upload validation, style selection, loading, generation, changing styles, reset, and backend failure messages.
