# MOBILE-02C Consultation integration

Inspected 2026-10-03 from `6ce58fb`, `codex/mobile-02`. The Supervisor authorizes the existing Consultation system, preserving the mobile Service → Direction → Your Looks presentation. No authentication architecture change is needed. Standalone Android Makeup visual acceptance and standalone Android Nails generation acceptance are explicitly deferred, outside this gate.

## Reused contracts

Mobile uses its existing credentialed SDK 57 fetch client and BeautyCore Client session. Every mutation supplies the application's canonical Origin. The unchanged adapter checks the current database Client role and verifies the signed, user bound, at most one hour consultation handle. Mobile keeps the opaque handle in memory and sends it only in `x-ai-consultation-handle`; it does not decode it, construct raw consultation IDs or address the private API.

| Mobile application route | Method | Existing FastAPI operation |
| --- | --- | --- |
| `/api/ai/mode`, `/api/ai/catalog` | GET | `/consultations/mode`, `/consultations/catalog` |
| `/api/ai/consultations` | POST | Create with `primary_service`; adapter replaces raw state ID with signed handle |
| `/api/ai/consultations/photo` | PUT | Upload `image` multipart, JPEG/PNG up to 8 MiB |
| `/api/ai/consultations/state` | PATCH / GET | Structured preferences / bounded consultation state |
| `/api/ai/consultations/turn` | POST | `{message}` user description/reply, at most 500 characters; the server also supports an empty opening request, which the mobile flow does not use |
| `/api/ai/consultations/recommendations` | POST | Read existing validated recommendation set in Gemini mode |
| `/api/ai/consultations/recommendations/{recommendation}/generation` | POST / GET | Existing dispatcher / saved status and result |
| `/api/ai/consultations/recommendations/{recommendation}/select` | POST | Record completed selected look, no booking/payment |

The adapter alone maps handles to FastAPI consultation IDs. All upstream routes and hosts remain allowlisted. BeautyCore and FastAPI remain private loopback development processes reached from Android by the existing USB reverse launcher.

## Source authority and local state

`conversation_status` is `not_started`, `more_information` or `ready_for_recommendation`. `stage` is `collecting` or `recommended`. Readiness comes only from the validated backend response with exactly three unique recommendations. The mobile validator checks response shape and every primary/complement against the active catalog; no missing or unavailable style can become an actionable recommendation. Service price/duration come from backend `demo_only` metadata and are labelled estimates, not salon booking prices.

Gemini receives structured text preferences and conversation messages, **not the uploaded photo**. The image is validated and temporarily held by the existing bounded FastAPI consultation store for later generation. The mobile gallery reference, direction, public session, opaque handle and results stay in memory; no new database/photo persistence is introduced.

`store/consultation-session.ts` owns asynchronous lifecycle state separately from the existing local draft. Structured fields map to the existing occasion/vibe/avoids/notes and service specific preference enums. Mobile creates the consultation, uploads the photo and saves structured preferences, then asks the user for a first text description before the first Gemini turn. This avoids the observed empty-turn rejection by the existing backend validator. Subsequent assistant questions are rendered as returned and answered naturally. An ambiguous/lost turn requires a state read before another turn; no turn is automatically repeated. The existing provider configuration and 35 second backend Gemini deadline are unchanged; the mobile turn request is not cut off by the normal 12 second read deadline.

## Generation safety

Every recommendation requires an explicit Generate action. Custom and Consultation share one in memory generation guard. Pending → generating → completed or failed follows server status. Real elapsed time is displayed with no invented percentage. There is no short mobile GPU timeout and no automatic generation POST retry.

A lost response triggers GET status, with further safe status reads while the focused screen is awaiting an outcome. Only a confirmed completed/failed outcome releases ambiguous work. A pending status after ambiguous transport loss remains locked rather than assuming the POST was not received. A definitive predispatch authorization/validation rejection may release only after status and current state prove no generation is active. An unavailable status does not clear the lock. Reset, sign out and another feature cannot bypass it. Keep Expo Go open and do not reload during GPU work; this is the existing temporary session architecture, not durable jobs.

Completed cards show the returned image. The dedicated consultation result route compares the original with the real result and sends Select through the existing adapter. Custom hands off the local photo to the selected service's existing style stage, clearing any unrelated old style selection. No extra upload or persistence is needed for that navigation.

## Validation boundary

Local fixture tests and exports do not establish native acceptance or live Gemini/Kaggle output. MOBILE-02C requires one manually operated Android Hair conversation, exactly three validated recommendations, one real recommended Hair generation, display, Select and Custom photo handoff, plus green regressions and bundle scan. No remote phone taps or captures are authorized. Evidence belongs in `docs/experiments/mobile-02c.md`.
