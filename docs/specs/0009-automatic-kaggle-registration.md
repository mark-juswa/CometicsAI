# Automatic Kaggle endpoint registration

**2026-10-10 — CONFIRMED by Supervisor; implementation, local/Neon checks and LIVE automatic registration VERIFIED.** The Supervisor requests eliminating manual Render environment changes after every Kaggle restart. The Supervisor approved implementation. One additive metadata table has been applied and verified against the actual Neon database. Account/business tables are unchanged. Fresh startup and changed-tunnel replacement passed on the owner account; full provider restart and client image-generation acceptance are tracked separately.

## Outcome

After a one-time application/notebook update, the operator starts the tested Kaggle notebook and waits for readiness. The notebook registers its current tunnel with the deployed website automatically. Render resolves the current registered endpoint at request time. No per-session `AI_FASTAPI_URL` edit or Render deployment is needed.

AI still requires a running Kaggle session. Automatic endpoint discovery does not preserve process-local jobs/photos/consultations after restart or provide always-on compute.

## Inspected facts

- `beautycore/app/api/ai/[...path]/route.ts` currently supplies `process.env.AI_FASTAPI_URL` to the bridge on every request.
- `beautycore/lib/ai/adapter-core.ts` restricts remote destinations to HTTPS roots under `*.trycloudflare.com` and forwards the server-side backend key and authenticated user ID.
- `beautycore/db/index.ts` already uses Neon via Drizzle; the current schema has no runtime endpoint registry.
- `scripts/render_kaggle_bootstrap.py` already checks protected readiness before printing the generated URL. This is the appropriate registration point.
- `scripts/capstone_discovery.py` implements a signed expiring ntfy mailbox for the older local GPU launcher. It cannot be reused unchanged: its keys, bundle/readiness contract and published destination represent the GPU worker rather than the Render-facing CPU facade. Its signing/expiry approach is a useful precedent.
- Render Free can restart and loses its local filesystem. An in-memory variable or local file is unsuitable as the durable endpoint record.

## Recommended design: registration in the existing Neon database

1. Add one small table, `ai_runtime_endpoints`, dedicated to operational metadata. Do not reuse user/image/history tables for this purpose.
2. Add a server-to-server route, proposed `POST /api/internal/ai-runtime/register`.
3. The Kaggle startup verifies its protected public facade readiness, then posts its session identity and current URL to the fixed BeautyCore website URL.
4. Render authenticates the registration, validates the destination and verifies its protected facade readiness before making it active.
5. The existing AI bridge resolves that active, unexpired record for Kaggle mode. It keeps the existing client authentication, role, Origin, handle, upload and response validation.
6. A lightweight Kaggle process sends authenticated heartbeats while the API, worker and tunnel processes remain alive. Renewals operate only on the current session's row. Lease expiry means the service is unavailable; do not silently route to an older address.

Proposed row fields: fixed deployment slot, session UUID, normalized HTTPS root, last heartbeat and server-issued expiry. No image, API secret or Gemini conversation is stored in this table. Runtime logs must not contain secret values.

## Authentication and replacement rules

- Use a domain-separated HMAC signature derived from the existing shared `AI_BACKEND_API_KEY`, so this design does not require the client to manage another secret. Signing canonical JSON covers operation, session ID, URL and timestamp. Verify in constant time and enforce bounded clock skew/replay rules. Implemented lease: 180 seconds; heartbeat: 60 seconds; signed timestamp skew: 90 seconds. Equal signed timestamps acknowledge without extending a lease. Strictly older timestamps are rejected; session birth ordering prevents an older notebook reclaiming the slot.
- Registration is not an ordinary Client UI endpoint. It must authenticate independently, without weakening the existing same-origin checks on `/api/ai/*`.
- Keep the existing strict `https://<host>.trycloudflare.com` root validation. Reject credentials, ports, paths, queries and fragments. Disable redirects during readiness checks so credentials cannot be forwarded to an unexpected destination.
- Bound registration bodies, HTTP timeouts and readiness response sizes. Authenticate before expensive work and add bounded abuse handling.
- Require the expected facade/readiness shape, all feature support and selected runtime configuration. A plain public health response is insufficient. No GPU generation is performed during registration.
- Use database transactions/conditional writes for lease replacement. An unexpired different session must not be silently replaced by a second notebook. A heartbeat from an old session must never reactivate its URL after a replacement.
- New registration after expiry must repeat readiness validation. A replay of an earlier signed registration must not restore an old session.
- Renewal/readiness must not reject a healthy service solely because it is busy with generation.
- If registration is rejected or cannot be acknowledged, print that the GPU is running but the website connection is not confirmed. Do not report full website readiness.

## One-time implementation/configuration

- Add the registry schema and a reviewed, additive migration creating only this table. Do not run broad `db:push`, seed, or alter existing account/business tables.
- Implement/test registration, authenticated renewal, record resolution and clear unavailable responses.
- Add an explicit switch such as `AI_ENDPOINT_MODE=registered`, configured once on Render. Preserve static `AI_FASTAPI_URL` mode for deliberate rollback; do not automatically fall back to a stale static URL.
- Put the stable public website root in the notebook configuration, e.g. `https://beautycore-demo.onrender.com`. It is public configuration, not a secret and not a changing tunnel address.
- Integrate publication after startup readiness and a monitored heartbeat subprocess into the corrected client starter. Keep both private archives, old notebooks, CPU isolation, original GPU guards and selected model settings unchanged.
- Deploy Render once, rehearse against the new notebook, and update the client guide only after acceptance. No Render API token is required in Kaggle, because the notebook calls the application route rather than the Render deployment API.

## Resulting operator workflow

1. Start the private tested Kaggle notebook.
2. Wait for model/API/tunnel readiness and automatic registration acknowledgement.
3. Open the website and test the desired feature.
4. Keep Kaggle running for the demo; stop it afterward.

A heartbeat is availability metadata, not proof that a particular generation completed. After a Kaggle restart, start a new consultation and upload the photo again. Existing jobs must never be automatically replayed; old status/result reads should fail clearly when their session no longer exists.

## Alternatives considered

| Option | Assessment for this project |
| --- | --- |
| Existing Neon registration | Recommended: persistent record, no additional hosting service/account, direct authentication/readiness acknowledgement |
| Adapt older signed ntfy discovery | Possible and avoids a database table, but adds a public mailbox dependency to hosted request routing and needs different facade/key/readiness contracts |
| Named Cloudflare tunnel with stable hostname | Suitable if the owner already has an appropriate Cloudflare-managed domain; requires account/domain/token setup and deliberate bridge allowlist changes |
| Change Render environment through its API | Automates clicks but retains deployment churn and requires a Render account-management token in Kaggle |
| Store the latest URL only in memory/a local Render file | Does not survive service replacement/restart; unsuitable |

The recommended design adds operational code and one small database row. It uses existing infrastructure; provider quotas and runtime availability still apply. This is not a claim of unlimited free hosting.

## Required validation before calling it dynamic

- Missing/wrong signature, malformed/tampered/replayed body, stale timestamp and unsafe destination are rejected without changing the active row.
- Redirects and unready/wrong services cannot receive/activate backend credentials through registration.
- Registration, duplicate notebook, renewal, lease expiry and old-session heartbeat races pass with controlled fixtures.
- Render process restart still resolves the current record from Neon.
- Registration accommodates Render Free cold starts with bounded idempotent metadata retries. Never retry generation automatically.
- Stop/start Kaggle, obtain a different tunnel URL, and demonstrate a new real generation without changing Render environment or deploying it again.
- Hair, Makeup, model Nails, renderer Nails and all three Consultation looks complete through the selected active facade.
- Existing local/static mode, client Origin checks, job ownership and opaque handles pass regression checks.

**Current status:** implementation, typecheck, production build, 54 BeautyCore tests, 44 Python startup/heartbeat checks and actual Neon atomic-query smoke passed. Render commit `2bba523` is Live in registered mode. Fresh pinned Kaggle startup, signed registration, changed-tunnel replacement without Render edits/redeploy, lease renewal and signed-in website discovery passed. Private notebook Version 1 is saved with its normal status cell restored. The API/GPU stayed loaded during the address-change rehearsal: complete provider stop/restart, client-account operation and real all-feature generation remain Needs verification. [Live evidence](../experiments/automatic-kaggle-registration-20261010.json).

Sources: [Cloudflare Quick Tunnels](https://developers.cloudflare.com/tunnel/get-started/quick-tunnels/) (temporary URL and changing hostname); [Render Free](https://render.com/docs/free) (ephemeral filesystem and service restart behavior).
