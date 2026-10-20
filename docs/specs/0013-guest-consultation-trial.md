# Guest AI Consultation trial: feasibility and proposed minimum scope

Date: 2026-10-20 (Asia/Manila)
Source inspected: `ccd17d55233be292dbb6e21d12cca52880dc730e`
Status: inspection **DONE**; findings **VERIFIED from source**; design **PROPOSED**; implementation **NOT STARTED**.

The user requested inspection and a recommendation only. This document does not authorize coding, migrations, deployment, guest GPU traffic or changes to the running Render/Kaggle system. The user has deferred the existing release's real-user acceptance testing.

## Recommendation

The trial is feasible as a small web/API extension. Keep existing client authentication, model settings, Kaggle registration and the registered consultation unchanged. Add a public trial page, a narrowly restricted guest gateway and a durable Neon allowance record.

The defensible promise is **one generation allowance per recognized guest browser within an agreed period**, with additional abuse throttling. An unsigned visitor cannot be reliably identified as one real person after deleting cookies, changing devices or using a different network. Do not advertise a technically unenforceable lifetime one-per-person guarantee.

Proposed experience:

Guest opens trial -> provides preferences/photo -> receives the existing three text recommendations -> chooses one -> generates one image -> sees signup/login invitation for the full experience.

Generating three images and hiding two would waste GPU time and violate the intended limit. Registered users keep their current three-look workflow. Existing description/pricing helpers should be reused; no invented trial prices.

## 1. Verified implementation

| Area | Existing behavior and evidence | Implication |
| --- | --- | --- |
| Authentication | `beautycore/lib/auth.ts` issues a seven-day signed login JWT in an HttpOnly cookie, Secure in production, SameSite=Lax. `app/api/auth/session/route.ts` reads the user from the database. | Use a separate guest cookie; do not manufacture client login sessions or account rows. |
| Client pages | `app/client/layout.tsx` wraps its subtree in `ProtectedRoute`. The guard is browser UX; API authorization remains necessary. | A public trial belongs outside `/client`. |
| AI authorization | `app/api/ai/[...path]/route.ts` and `lib/ai/adapter-core.ts` check the session and fresh database role. Missing users receive401; non-clients403. Server-derived ownership, same-origin mutation checks, operation/body restrictions and private backend authentication are already present. | Keep this existing gateway client-only. A new trial route needs its own explicit, narrower permission policy. |
| Consultation ownership | `lib/ai/consultation-handle.ts` signs an expiring handle bound to the current user. Current audience is client-consultation; maximum lifetime is one hour. | Guest handles need a separate purpose/audience and server-derived guest identity. Never accept browser-supplied owner IDs. |
| Three-look behavior | `app/client/ai-consultation/page.tsx` calls `generatePending` sequentially for the recommendation cards. `backend/app/consultation/models.py` requires exactly three recommendations. | Reuse that recommendation contract but add a guest UI mode that submits only one chosen card. |
| Browser jobs | `lib/ai/browser-client.ts` uses `/api/ai/`, accepts async job tickets and polls with GET. Ambiguous failures are not automatically reposted. | Add a guest transport while preserving member defaults and retry protections. |
| Hosted inference | `backend/app/demo_gateway.py` requires the private backend key, validates an owner string and checks ownership of consultations/jobs. It does not require that owner to exist in the users table. | A server-derived namespaced guest owner can reuse inference without fake database users or model changes. All anonymous access must pass the new Render policy. |
| Runtime capacity | The hosted facade has one shared generation slot, default three retained jobs and a30-minute job lifetime; new admissions may evict old results sooner. Consultation state is process-local, default maximum ten sessions, with a sliding one-hour expiry and a12-message conversation bound. | Guests compete with paying/registered clients for the same resources. Bound trial creation/chat, not only image POSTs. |
| Current limits | No durable guest credit, anonymous-trial API, guest throttling or CAPTCHA was found in the inspected paths. The per-consultation conversation bound resets with a new consultation. | A UI disable button or existing session limits cannot enforce the proposed allowance. |
| Saving/booking | `db/schema.ts` requires an existing client FK on `ai_generations`. Saved-look/business endpoints require an account. | Keep guest results temporary in v1. Save/Book requires login; automatically transferring the exact result would be additional work. |
| Other generation routes | Inspected legacy `/api/analyze`, `/api/generate` and generation history routes require a session. | Keep those checks. Do not open a bypass around the trial gateway. |

These are source findings, not a fresh live-browser, account or load test.

## 2. Minimum proposed changes

### Public page and shared consultation presentation

Add a route such as `app/(public)/try-consultation/page.tsx`. Extract enough of the current consultation presentation to support explicit member/trial modes rather than copying its entire implementation.

Trial mode keeps the service picker, preferences, image validation, three text recommendations and existing generated-look metadata. It allows selection before image generation, submits one recommendation and replaces further generation/Save/Book actions with signup/login invitations. Switching service, reloading or restarting consultation must not reset the allowance.

Update the public homepage's two current links to `/client/ai-consultation` to direct guests to the trial. Existing authenticated clients should still reach the full consultation.

### Dedicated, restricted guest API

Add a route such as `/api/ai-trial/[...path]` and small guest policy/storage helpers. Share low-level forwarding, validation and job parsing where safe; retain the existing member authorization boundary and tests.

Allow only bounded consultation creation, preferences/photo upload, conversational turns/recommendations, one chosen recommendation-generation submission and reads of that guest's own state/job/result. Do not expose standalone feature generation, arbitrary upstream paths, account history, saved looks, bookings, staff APIs or runtime registration.

Apply the same production-origin, image/body-size and backend-key protections. All owner identities and upstream consultation/job bindings come from trusted server records. Use purpose-separated guest consultation handles. A guest token must never authenticate a member route, and another guest must not read the result.

### One durable allowance ledger

Add one small Neon table through an explicit additive migration. Conceptual fields:

- Hash of a high-entropy opaque guest cookie token, internal namespaced guest owner, created/expiry timestamps.
- Allowance state, attempt ID and submission timestamp.
- Bound consultation/recommendation/job identifiers needed for ownership and status recovery.
- Bounded consultation/chat counters and a keyed, time-bounded network tag for abuse controls.

No photo, generated image, chat content, password or real-client row belongs in this ledger. The guest cookie is persistent, HttpOnly, Secure in production and SameSite=Lax; JavaScript/localStorage is not the authority. Its lifetime and the ledger retention period require a product decision. Expiry must not silently create a new allowance within the stated trial period.

Use an atomic database reservation before forwarding the generation request. Two tabs must not both observe an unused credit. Commit the short reservation transaction before calling Kaggle; never hold a database transaction while waiting for inference.

Proposed state policy:

| Event | Allowance behavior |
| --- | --- |
| Same attempt submitted twice | Return known job/status, or an in-progress/uncertain status; never dispatch another job. |
| Kaggle returns an accepted202 job | Mark spent and store the job binding. Polling/reading does not spend another credit. |
| Existing trusted pre-admission `AI_BUSY` response | Release the reservation because the facade explicitly confirms no generation started. |
| Validation failure before submission or no available endpoint before forwarding | Do not spend the credit. |
| Timeout, dropped connection, server crash or ambiguous upstream failure | Keep reserved/spent until reconciled. Do not automatically grant a replacement. |
| Kaggle restarts or result is evicted | Allowance remains recorded; the temporary result may be unavailable. |

A Render failure after Kaggle admission but before saving the job ID can leave an uncertain attempt without a recoverable ticket. This is a limitation of the current cross-service protocol. Guaranteeing exactly one successful delivered image with free automatic retries would require stronger upstream idempotency/reconciliation and expands the minimum scope.

For v1, recommend **one admitted generation attempt** rather than promising one successful image under every network/model failure. This difference requires user approval before implementation.

## 3. Abuse controls and limitations

A cookie plus Neon prevents ordinary refresh, reopening the same browser with retained cookies, repeat API calls, concurrent tabs and Render/Kaggle process restarts from refilling a recognized guest allowance.

It cannot identify a person who clears cookies, uses incognito, another browser/device or a different network. Add modest durable limits on trial issuance, consultation starts, conversational activity and generation submissions, plus a global guest budget and a guest-only kill switch. These checks must be server-side and concurrency-safe; process memory alone is inadequate. Reuse Neon for the demo-scale counters rather than introducing Redis or a queue without evidence of need.

Network tags should be keyed hashes, retained briefly and based on a verified trusted proxy chain. Shared salon/school Wi-Fi can cause false positives; rotating IPs can evade limits. Exact Render proxy/header behavior is **Needs verification** before an implementation relies on it. Do not trust arbitrary client-supplied forwarded-header values.

Render's platform DDoS protection does not replace application limits against expensive valid-looking requests. See [Render's application-security guidance](https://render.com/articles/how-render-handles-ddos-attacks) and [MDN's X-Forwarded-For security guidance](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/X-Forwarded-For).

For an advertised public campaign, consider a server-verified anti-bot challenge if the expected exposure warrants it. This remains an optional provider integration, not proof of one-person identity. Avoid intrusive device fingerprinting.

One final model-generated Nails image can require five sequential nail-region model calls. One output is therefore not one cheap inference call. Hair, Makeup, Nails and consultation share the same slot; guest traffic can produce busy responses for registered clients. A small global budget reduces exposure but does not create member priority. Queuing/priorities would be additional backend scope.

The current login form displays demo-account autofill shortcuts. Whether those credentials work in production was not tested. Review those shortcuts before using the site for signup acquisition; preserve controlled demo access separately if needed. Public registration is client-only, but no email-verification step was found, so this proposal does not solve repeated-account signup abuse or add new member limits.

## 4. Signup, image retention and privacy

The smallest v1 ends the guest flow with signup/login and opens a **fresh full consultation** after authentication. Existing member saving/booking works unchanged after that. Use a fixed or allowlisted internal continuation path; the current login form reads a redirect parameter and registration returns to role home, so both CTA paths need deliberate handling.

Do not imply that signing up automatically saves or carries the exact guest image into an appointment. That requires an explicit, owner-validated handoff to the existing client-only saved-look system and should be separately approved if essential to the acquisition goal.

Allowance persistence is not result persistence. Current Kaggle jobs/images remain temporary and may disappear after restart, expiry or eviction. Clearly explain trial photo handling and temporary availability before upload. Users can copy/download a delivered image; account requirements can protect gallery/booking operations, not prevent copying.

## 5. Files and verification plan

Likely web changes:

- Public trial page/shared consultation component and `app/(public)/page.tsx`.
- New guest API/policy/store helpers; focused changes to shared adapter/handle/browser transport helpers without weakening member defaults.
- `db/schema.ts`, one additive migration and explicit migration checker/runner integration.
- Login/register continuation UI and trial completion invitation.
- A guest feature flag, proposed `AI_GUEST_TRIAL_ENABLED`, default disabled; server-side configurable trial period and budgets.

No planned changes to training, pretrained weights, inference parameters, GPU optimization scope, Kaggle notebook registration, booking tables or registered generation limits.

Required tests after approval:

1. Existing anonymous401/non-client403, handle ownership, payload validation and GET-only job polling tests remain passing.
2. Unused guest can complete preferences/recommendations and dispatch exactly one image; member still generates three.
3. Refresh, browser reopening, service changes, consultation resets and two simultaneous tabs cannot get another allowance.
4. Repeated generation request resumes the same attempt; foreign guest/member handles and job IDs are rejected.
5. Known busy does not consume credit; ambiguous timeout/crash does not produce a free retry; completed failure follows the approved refund policy.
6. Trial creation/chat/network/global budgets work under concurrency; forged forwarded headers cannot bypass trusted-IP extraction.
7. Render restart preserves quota; stopped/restarted Kaggle gives clear availability/result-loss messages.
8. Signup/login reaches the approved destination; no implicit guest-result transfer or fake user record.
9. Feature disabled leaves the current member system unchanged. Use synthetic fixtures first, then a small separately authorized scheduled Kaggle rehearsal; never use an unrestricted load test on the demo GPU.

## 6. Review items before coding

1. Approve one admitted attempt, or define the rules for a failed generation and any replacement.
2. Set the browser trial period, ledger retention and conservative network/global budgets.
3. Confirm whether a fresh member consultation after signup is sufficient or exact guest-image carryover is essential.
4. Confirm controlled-demo versus public-marketing exposure and whether an anti-bot challenge/demo-shortcut changes are needed.
5. Keep all three service choices unless a narrower trial is explicitly approved; do not silently exclude Nails because it costs more.

No source code, schema, deployment, credentials or notebook was changed for this audit. No fresh inference, load test or application regression suite was run.


## Development approval and implemented scope, 2026-10-20

**CONFIRMED:** User said "lets start with your recommendation". Local development DONE / verification VERIFIED; no production rollout. Defaults are fixed30-day browser identity, one admitted attempt, conservative server budgets and fresh full consultation after signup. Public page, restricted guest gateway, atomic additive0006 ledger, shared UI/transport, guest-specific handles, safe status reads and known-busy-only release implemented. Registered auth/three-look flow, models and working Kaggle unchanged.23guest +58AI +47business tests pass; production build/TypeScript pass. Actual trusted proxy chain and real scheduled GPU/browser acceptance remain Needs verification. New migration is NOT applied live and flag defaults OFF. No new dependencies or push. [Review/runbook](../guides/guest-consultation-trial.md), [evidence](../experiments/guest-consultation-trial-development-20261020.json).
