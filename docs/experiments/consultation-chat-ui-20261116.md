# Consultation chat UI implementation, 16 November 2026

Progress: DONE local implementation. Decision: CONFIRMED approved prototype v3 implementation. Evidence below distinguishes the real application with controlled HTTP responses from live services. Release is not deployed.

## Source boundary

The implementation checkout is `C:/Users/Gigabyte/.codex/worktrees/consultation-chat-ui/HAIR`, branch `codex/consultation-chat-ui`, based on fetched client enhancements `23b2555a7e3b86acd2458ebeb865b782b37f0308`. The older, dirty `I:/HAIR` application source is preserved. This avoids dropping shared recovery, camera capture or the private reference image picker that already exist in the client branch.

Production source changes are limited to the consultation component, its stylesheet, one stylesheet import, a local preparation helper, and two lines that clear its journal through the existing account cleanup path. There is no backend, API contract, schema, provider, model, quota or booking handler change. Existing application dependencies and lockfiles are retained.

## Resulting flow

The welcome keeps the purple and gold brand, serif heading and gold display text. Chat and controls use the existing Inter font. The larger progress strip shows Your direction, Consultation and Your looks. The user can choose a service or describe an idea first. The description remains local, an ambiguous service is clarified, and photo upload, camera and existing source picker sit inside the composer. Service inference can be corrected before creating a session.

Continue creates or reuses the existing signed consultation, uploads the photo, then sends the retained initial description as the first real turn. The existing backend permits this without a separate empty opening turn. Suggested replies fill the reply field. Recommendation readiness reveals three looks beside the transcript, stacking below it on narrower screens with a disclosure. Members generate three sequential previews; guests generate only their chosen one. Selection, download, saving, Custom navigation and the existing save then booking route handoff retain their contracts. Opening the booking form is not an appointment.

## Recovery design

The same shared member owner retains photo, draft, transcript and generation state. A synchronous sessionStorage journal keeps only the initial local direction and one pending turn before its POST, scoped to this tab, account and signed consultation identity. It contains no image or canonical message history. A blocked write prevents a turn submission. Guest token renewal is matched by stable issuer, audience, subject and consultation identity for local recovery only; current server-issued signed handles still authorize requests.

An uncertain turn checks the canonical state and exact user message position, without resending. A new member mount locks mutations while hydration runs. Preview actions wait for actual result bytes. Failed photo setup retains its handle, and specific expired access enables an explicit fresh consultation. Account cleanup removes the journal centrally; an account lifetime counter rejects late asynchronous writes after logout or account change. Camera and generation guards remain in their existing handlers.

## Verification and evidence

VERIFIED 206 tests passed, zero failures, across 14 existing frontend API, component, recovery, guest, camera and business test files. This includes 34 consultation UI/recovery cases and 44 database-backed business UI cases. [Clean suite log](../../artifacts/consultation-implementation-20261116/final-clean-tests.log). Run from `beautycore/` using Node with `--experimental-test-module-mocks --import tsx --test --test-concurrency=1` and the fourteen files listed in that log: ai-adapter, ai-client-flow, ai-studio-integration, business-ui, business-workflows, camera-methodology, generation-auth, generation-navigation, generation-store, guest-trial-ui, guest-trial, look-information, saved-look-image and saved-look-retry.

VERIFIED normal Next16.2.6 Turbopack production build, including TypeScript and all47 static pages, using dummy local configuration. [Build log](../../artifacts/consultation-implementation-20261116/final-build.log). Package scripts and lockfiles are unchanged.

VERIFIED seven Chrome journeys against the actual production build: member Hair, mobile Makeup, guided Nails, guest chosen generation, member and guest pending-turn refresh, and long-message scroll retention. Zero page JavaScript errors. Widths1440/1287/1024/768/390/320 have no page overflow. Short430pixel viewport checks keep the composer and send action reachable. Sidebar, notification bar and parent layout are the actual application components. The rendered chat uses Inter. Photos/results are initially hidden and mobile disclosures work.

VERIFIED dashboard and all three manual studio routes have identical sampled computed styles with the consultation CSS rules present or removed. The script compares27 dashboard elements and23 elements on each studio route, and also checks that no consultation workspace is mounted there. These are focused style-isolation checks, not a claim to have manually exercised every unrelated feature. Existing business regressions provide additional coverage.

| Contract | Local evidence |
| --- | --- |
| AC-1 layout, brand and typography | Real application screenshots, hidden initial rail, progress strip and Inter font assertion. |
| AC-2 preparation and photo inputs | Local direction, explicit service correction, JPG/PNG/8MB checks, real camera and existing image picker tests; turn after photo only. |
| AC-3 conversation | Exact first message, quick replies fill only,500character input limit, Enter/ShiftEnter/IME, pending response and read-only reconciliation. |
| AC-4 recommendation and business actions | Three sequential member generations; actual select/download/save components; saved B books B while A is displayed; existing booking route opens with no appointment POST. |
| AC-5 failures | Lost committed/uncommitted turns, failed photo reuse, expired PUT/PATCH/403 access, uncertain generation GET and explicit continuation. |
| AC-6 recovery and isolation | Shared route state, cold result hydration, fresh-store/failed IndexedDB turn recovery, actual renewed signed guest handles, delayed GET lock, account cleanup and rejected late writes. |
| AC-7 guest | Three recommendations, one chosen generation, reserved/spent/unknown restrictions, modal and account links; no member save/book controls. |
| AC-8 guided mode | Occasion, vibe, service preference, avoids and notes; cleared notes remain empty; guest interrupted setup retains its direction. |
| AC-9 accessibility and responsive layout | Browser widths and short viewport, focusable controls, actual camera/dialog focus tests, long chat scroll and Latest message. Physical keyboard/device checks remain NEEDS VERIFICATION. |
| AC-10 boundary | Scoped CSS comparison, unchanged manual pages/dashboard/API/backend/schema/model/booking handlers; one layout import and two account-cleanup integration lines. |

Evidence directory: [local verification artifacts](../../artifacts/consultation-implementation-20261116/).

- [Browser script](../../artifacts/consultation-implementation-20261116/browser-verify.mjs) and [request traces](../../artifacts/consultation-implementation-20261116/browser-verification.json).
- [Final independent review](../../artifacts/consultation-implementation-20261116/independent-review-final.md), verdict Approve, no remaining findings. Earlier findings and follow-up reports are retained.
- [Desktop welcome](../../artifacts/consultation-implementation-20261116/desktop-welcome.png) and other desktop, mobile, photo and results screenshots in the artifact directory.

The first broader regression attempt exposed three obsolete UI expectations and a test assertion that caused Node to inspect a React DOM object excessively. The test harness was corrected. A subsequent run exposed a browser animation callback caused by a test-only requestAnimationFrame shim; that unnecessary shim was removed. Historical logs are preserved. These were not suppressed by changing production behavior.

The first isolated build attempts failed on the cross-drive dependency junction. Copying the existing dependencies into the worktree resolved the bundler path issue without installing or changing packages. Compilation then succeeded; page collection required configuration, so subsequent verification used clearly dummy loopback database and authentication settings. No real credentials or account database were loaded.

## Limits

All UI requests in browser verification use controlled HTTP fixtures. The database business tests use temporary local PGlite databases. This does not establish live AI/GPU availability, generated image quality, real account database behavior or a production booking. No appointment, live upload, GPU generation, migration, push or deployment was performed. Physical mobile software keyboard and device camera behavior remain NEEDS VERIFICATION; responsive and short viewport checks are browser emulation. Local status does not claim a deployed release.
