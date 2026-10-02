# MOBILE-00 integration inspection

Date: 2026-10-02. Evidence: inspected source at `e05b832`. This is a focused mobile contract inspection, not a project audit. Source confirmation does not imply native runtime verification.

## Application boundary

CONFIRMED: root `START.bat` runs `beautycore/` (Next.js App Router) and the existing private FastAPI `backend/app/main.py` (`app.main:app`). Original `frontend/` is the Next.js rollback frontend. The active Client AI screens are `beautycore/app/client/{ai-consultation,hair-studio,makeup-studio,nail-studio}/page.tsx`, adapted from `frontend/app/{consultation,page,makeup,nails}` and shared `ai-studio` components/CSS.

CONFIRMED Supervisor decision: MOBILE-01 connects to existing FastAPI for development only. BeautyCore authentication integration is deferred to MOBILE-02. The app must never connect to the Kaggle worker. FastAPI health indicates API connectivity, not GPU readiness.

## Active FastAPI routes

| Method and route | Request | Response |
| --- | --- | --- |
| GET `/health` | none | `{status: "ok", generator: string}` |
| GET `/features` | none | array of `{id, name, description}`; IDs `hairstyle`, `makeup`, `nails` |
| GET `/features/{feature}/styles` | none | array of `{id, name, description, status}` |
| POST `/features/{feature}/generate` | multipart `image` file and `style_id` string | `{status, generator, style, image: {data_url, content_type, width, height}, metadata}` |

CONFIRMED: unknown feature returns 404; invalid style returns 400. Hair catalog derives from the active engine/registry (mock or real registry); Makeup status depends on configured engine; Nails status depends on preview mode. Do not hardcode style IDs/counts or infer generated quality from status. Generated data URLs contain PNG/JPEG base64. Mock responses are `placeholder`; live responses are `completed`. Manual/Custom pages use this same generation route, with no separate Custom endpoint. Legacy `/styles`, `/generate`, `/makeup/styles`, `/makeup/generate`, `/nails/styles`, `/nails/generate`, and service health routes remain.

## Consultation contracts (later phase)

| Method and route under `/consultations` | Behavior |
| --- | --- |
| GET `/mode` | `{provider: deterministic or gemini, model: string or null}` |
| GET `/catalog` | service estimates and styles keyed by feature, with tags and optional model/renderer nail path |
| POST base | JSON `{primary_service}`; 201 full state |
| GET `/{id}` | full state; missing/expired 404 |
| PUT `/{id}/photo` | multipart `image`; full state |
| PATCH `/{id}` | JSON `{preferences?, message?}`; full state |
| POST `/{id}/turn` | JSON `{message?}`; state, assistant message, conversation status and optional recommendations |
| POST `/{id}/recommendations` | exactly three validated recommendations |
| GET or POST `/{id}/recommendations/{recommendation_id}/generation` | read status/result or explicitly generate one look |
| POST `/{id}/recommendations/{recommendation_id}/select` | select completed result; full state |

CONFIRMED: state starts `collecting`, becomes `recommended`. Conversation progresses `not_started` → `more_information` → `ready_for_recommendation`. Generation rows progress `pending` → `generating` → `completed` or `failed`, with attempts, error and result availability. One generation per consultation at a time; conflicts return 409. Exactly three unique active primary styles are backend validated; complements do not trigger images. State holds metadata rather than image bytes; generation detail supplies saved result. Ten process-local sessions, one-hour expiry, lost on restart. Photo/preference changes invalidate results; mutations during active work conflict. Gemini mode requires conversation before recommendations; deterministic mode needs a photo. Generation is sequential and explicit, with manual failure retry and status reads after ambiguous responses. No generation idempotency or automatic retry exists.

## Authentication and browser assumptions

CONFIRMED: FastAPI has no user authentication. It is a private application service in current BeautyCore deployment. Do not expose it as a public production mobile API.

BeautyCore `/api/auth/login` accepts JSON email/password and sets `beautycore_session`, a signed seven-day HttpOnly cookie (Secure in production, SameSite Lax). `/api/auth/session` returns `{user}` or `{user:null}` from a fresh database read; logout clears the cookie. `/api/ai/[...path]` checks a fresh Client role. GET `features`, `features/{id}/styles`, `catalog`, `mode`; POST `features/{id}/generate`, `consultations`; consultation state/photo/turn/recommendation operations map to FastAPI. Non-GET requests require same-origin `Origin`. Consultation UUIDs become user-bound signed `x-ai-consultation-handle` values. Adapter permits only loopback upstream, never arbitrary mobile-selected worker URLs. No adapter health route exists.

NEEDS VERIFICATION for MOBILE-02: native cookie persistence and expiry/logout on Android, native Origin compatibility under the current guard, deployed HTTPS reachability. Preserve role and consultation ownership checks. Do not bypass these by making generation public. DOM File, file inputs, blob/object URLs, dialog/download anchors, session cookies, relative fetch paths, window timers and in-memory browser photo handoff need native equivalents.

## Uploads and errors

CONFIRMED in `validated_image`: MIME and decoded format must match JPEG or PNG; nonempty, ≤8 MiB; width/height each 64–4096; ≤16,777,216 pixels; readable image. EXIF orientation is applied and input converted to RGB. Unsupported 415, empty/corrupt 400, oversized 413, dimensions 422. BeautyCore also limits multipart to 8 MiB + 64 KiB, JSON to 32 KiB, style IDs to safe 1–80-character IDs. Nails additionally validates usable hand geometry through unchanged processing.

FastAPI errors use `{detail: string}` or Pydantic `{detail: [{loc, msg, type, ...}]}`. Controlled generation/provider failures include 409, 429, 502, 503, 504. BeautyCore uses sanitized `{error: string}`, including 401/403; never forward HTML or internal diagnostic bodies into mobile UI.

## Timeouts, configuration and verification

CONFIRMED source defaults: remote Hair/Makeup timeout 180 seconds; Nails 300 seconds, configurable server side. Remote clients perform one attempt. Existing browser clients have no fixed fetch deadline; consultation UI reads status after response loss. The BeautyCore adapter forwards once and has no built-in fixed deadline. MOBILE-01 uses bounded read-only health/catalog requests and explicit retry buttons; it exposes no generation API action.

Client requires only `EXPO_PUBLIC_API_BASE_URL`, an application API origin. No default localhost/LAN address. Server variables (`AI_REMOTE_*`, service remote keys/URLs, Gemini keys, `SESSION_SECRET`, database URL, consultation handle secret, asset paths) stay server side. `NEXT_PUBLIC_API_BASE_URL` belongs to the original web frontend, not mobile. Native networking does not use browser CORS; Expo web preview needs an allowed `FRONTEND_ORIGINS` entry on its separate development API.

NEEDS VERIFICATION: real device selection/preview/reset, Android network transport and authenticated MOBILE-02 workflow. No live GPU generation belongs to this inspection or MOBILE-01.
