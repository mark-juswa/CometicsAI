# Render + Kaggle scheduled demonstration

2026-10-09. **Decision CONFIRMED by Supervisor; implementation IN PROGRESS; online acceptance NEEDS VERIFICATION.**

The Supervisor explicitly chose Render + Kaggle after reviewing hosting limitations and accepted the necessary deployment changes. Scope is a temporary scheduled capstone demo. Existing local START/STOP, working Kaggle notebooks, weights, prompts and model settings remain the rollback path.

## Component placement

- Render free Node web service runs `beautycore/`: full Next.js, authentication/business API, and authenticated `/api/ai/*` bridge. Neon remains the database; no database migration or seeding is performed.
- A NEW private Kaggle notebook runs the unchanged expanded GPU bundle on `127.0.0.1:8765`, an isolated FastAPI CPU environment, an isolated CPU Torch/YOLO segmentation environment, and one Cloudflare tunnel to the authenticated API facade on `127.0.0.1:8800`.
- `app.demo_server` wraps `app.main` inside the same CPU process. Do not expose `app.main`, the GPU port, or a development frontend publicly.
- Gemini remains a text-only recommendation provider, called from the Kaggle CPU environment. Web and Expo mobile continue calling only BeautyCore.

## Trust and generation contracts

Existing client identity, current database role, same-origin mutations, opaque signed consultation handles, upload validation, and model response/provenance checks stay active. Remote mode is opt-in (`AI_BACKEND_MODE=kaggle`). The bridge accepts an exact HTTPS `*.trycloudflare.com` root, supplies `x-ai-backend-key` from a server-only environment variable, and derives `x-ai-user-id` from the current database user. Incoming browser identity/key headers are ignored. The facade authenticates every private operation and binds consultation/job access to that identity.

Generation POSTs in the facade immediately return HTTP 202 with a random job UUID. One background task executes the original handler. A second concurrent generation receives 429 before dispatch. GET `/jobs/{id}` reports `generating/completed/failed`; GET `/jobs/{id}/result` returns the original handler's JSON and HTTP status. No automatic generation retry, no new AI implementation, and no hosted job database are introduced. The clients understand both this contract and unchanged local synchronous responses.

Public requests use bounded short reads; the longest inference happens internally between two Kaggle processes. `AI_GPU_LOOPBACK=1` allows ONLY HTTP `127.0.0.1:8765` and the three feature paths. Existing remote configurations continue requiring HTTPS. This removes a public tunnel timeout from individual GPU crop calls.

The facade retains at most three jobs, evicts the oldest finished job when accepting a new one, and removes finished jobs after 30 minutes from creation. Results have a 96 MiB serialized limit; consultations retain their existing bounded state/results. Restarting the notebook loses photos, jobs and consultations. User IDs authenticate ownership only when supplied by the trusted bridge; they are never accepted without the shared server key.

## Acceptance gates

1. Local security/job tests, existing backend/web/mobile regressions, type checks, Next production build, and private bundle inventory checks.
2. Fresh Kaggle Linux installation: pinned CPU packages, CPU-only Torch, YOLO and MediaPipe asset loading; original exact GPU environment/artifact checks; authenticated public readiness. Combined host RAM and process peaks NEED VERIFICATION; runner requires at least 30 GiB total RAM.
3. Render free runtime: build/start, cookies/login, catalogs, Gemini, and representative real Hair, Makeup, model Nails, renderer Nails, and return-to-Hair generation. Check result downloads, unchanged outside-mask pixels, measured memory, browser/mobile result rendering and failure behavior. Free 512 MiB Render runtime fit is unproven until this gate.
4. Refresh a changed Kaggle URL, restart/expiry recovery, busy/auth failure, anonymous/cross-user denial, and manual mobile login/generation/logout acceptance. No remote phone taps are authorized.

A successful build, mocked result or health check does not satisfy online or visual acceptance. There is no claim of 24/7 uptime or permanent production readiness.
