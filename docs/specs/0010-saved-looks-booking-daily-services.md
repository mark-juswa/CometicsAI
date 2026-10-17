# Saved looks, look-based bookings and stylist daily service monitoring

**Date:** 2026-10-17 (Asia/Manila). **Decision: CONFIRMED by “proceed on development”. Implementation: DONE locally; VERIFIED by 84 tests and production build. Production rollout: NOT STARTED.**

The original inspection and proposed design below are retained as the planning record; references to “proposed”, missing features and planning-only checks describe the pre-implementation audit. The Supervisor subsequently approved development. The implementation extends the existing tables as planned; it does not introduce a payment ledger, model change or new image provider. Source revision originally inspected: `9d18585`, branch `codex/render-kaggle-demo`. The actual project is `I:\HAIR`; the environment's `F:\HAIR` path is stale. Development now changes application code and adds explicit migration files. Live database data/schema, cloud configuration and AI runtime have not been changed. See the [rollout guide](../guides/saved-looks-booking-rollout.md) and [implementation evidence](../experiments/saved-looks-booking-development-20261017.json) for current behavior, limits and remaining release gates.

## Confirmed request and review assumptions

The Supervisor requests account-persistent saved AI looks, booking from a generated look, a daily admin view by stylist, and the selected look in stylist appointment details. During this audit the Supervisor confirmed **completed services and recorded amounts**, rather than a payment ledger, and requested a plan for Makeup booking services/prices.

Proposed first release targets BeautyCore's web client, admin and stylist portals. Existing mobile generation remains compatible; account-based mobile Save/Book screens are a follow-up unless included explicitly at review. Downloading to a phone currently means a device file, not an account save.

Proposed report day means the **scheduled appointment/service date in Asia/Manila**, filtered to completed services for the monetary total. It is not the booking creation date, the time an employee clicked Complete, or a payment receipt date. There is no completion timestamp or payment date in the current schema. If actual completion-day accounting is required, that needs a prospective completion timestamp and separate handling of unknown historical completion dates.

## Verified findings

| Area | Actual implementation | Missing or relevant limitation |
| --- | --- | --- |
| Database | Next.js uses Neon PostgreSQL through Drizzle. Read-only metadata matches `beautycore/db/schema.ts`. | No payment/transaction ledger, saved-look booking FK, or object-storage integration. |
| Appointments | `appointments` already records client, optional stylist, service name/type, scheduled date, status, price and notes. GET scopes clients to their bookings, stylists to assigned bookings, and admins to all. | No generated look reference. PATCH changes status/notes/date, but cannot currently assign a stylist or confirm a price. |
| Booking | `/booking` uses `lib/services.ts`, loads stylists and creates a pending booking. `?service=` preselects a group. | No look context. Service name/type and price are accepted from the request; the server needs catalog validation for reliable new reporting. No availability/collision scheduler was verified. |
| Current AI studios | Hair/Makeup/Nails use `studio-api.ts` -> `browser-client.ts` -> `/api/ai/*` -> FastAPI. Results contain PNG/JPEG data URLs and style metadata. | Results are React state, not account-persistent records. `ResultDialog` offers Close, Regenerate and Download only. |
| Consultation | Completed cards support Select and Download. Selection is written to the process-local consultation state. The page explicitly says that no booking has been made. | Select is not an account save. Consultation expiry is one hour; state is lost on API restart. |
| Hosted generation | The Kaggle facade retains a bounded number of jobs/results (default three), with a 30-minute expiry rule for finished jobs. | A later job may evict an earlier result sooner. Neither a job ticket nor a temporary tunnel is durable image storage. |
| Existing AI history | `ai_generations` already owns images by `client_id`; the older `/api/generate` writes there and `/api/generations` reads the caller's latest 24 records. | That older route is not the current studio generation path. Its style enum supports only `hair` and `nail`; source image and prompt are required. Default history responses can still include the full generated image data URL. |
| Services | One TypeScript catalog drives booking/public services/stylist services; prices include fixed, starting-from and consultation-only values. | No Makeup booking group exists. AI style IDs are not salon service IDs. Consultation demo estimates must not become booking charges. |
| Stylist appointments | Existing cards show client, service, date/time, amount, notes and status controls. | No attached preview or image-detail access policy. |
| Admin finance | `/api/admin/stats` sums completed appointments for headline totals. Finance displays aggregate totals/statuses/top services. | No date/stylist drilldown. `topServices.revenue` currently sums all statuses, unlike the headline total. Archived `_legacy_src/.../Finance.jsx` has hardcoded local transaction arrays, not live transaction data. |
| Time handling | Existing appointment timestamps are PostgreSQL `timestamp without time zone`; database timezone is GMT. Booking uses the browser's local date/time; display helpers do not specify a timezone. | An explicit salon timezone and verification of historical timestamp interpretation are needed for daily boundaries. Do not bulk-shift old dates based only on the database timezone. |
| Authorization | AI bridge checks the current database user/role. Ordinary appointment APIs use the signed cookie's role. | New image and report access must check current role plus record ownership/assignment, not only page navigation or a stale role claim. |

Read-only live aggregates on 2026-10-17: 15 appointments (6 completed, 1 unassigned), 51 legacy AI-generation records (21 with non-null result), largest existing generated-image text value 472,554 bytes. These are current database aggregates, not counts of approved tests or evidence that current model outputs fit that size. No names, photos, credentials or individual transaction amounts were retrieved.

## Proposed user experience

1. On every **completed** standalone result and completed Consultation look, show **Save Look** and **Book This Look**, while preserving Download and existing result/status actions. A development placeholder must not be presented as a completed AI look.
2. Save Look persists the chosen generated preview to the signed-in client's account. Only acknowledge Saved after the database confirms success. A save failure must not erase the generated preview or request another generation.
3. Book This Look first saves the look if needed, then opens `/booking?look=<saved-id>` with the image and style visible. It does not itself create an appointment. The client still chooses the actual salon service, time and stylist and confirms the booking.
4. Add **My Saved Looks** to the client sidebar, with feature/date filters, paginated cards, full image view, Download, Book and Remove from Saved. Reload, sign out/in and a second device must show the same saved records.
5. Client appointment cards and assigned stylist appointment cards show a thumbnail and **View Requested Look**, with style, service, date/time and notes together. Admins can inspect the same booking context.
6. Add a **Daily Services** section to the existing Admin Finance page: date/date-range, stylist and status controls; summary per stylist; and expandable service/appointment rows. Include an Unassigned bucket so totals reconcile.

## Database changes: extend existing records

Do not add a second appointment table, a copied transaction table, or a separate duplicate image-history table.

| Existing structure | Proposed change | Compatibility rule |
| --- | --- | --- |
| `style_type` enum | Add `makeup`; keep `hair` and `nail`. | Map current feature names `hairstyle -> hair`, `nails -> nail`, `makeup -> makeup`. Do not rename old values. |
| `ai_generations` | Add nullable `style_id`, `style_name`, `saved_at`, `result_hash` and descriptive source kind (manual/consultation/legacy). | Old records remain readable and are not silently marked user-saved. Add integrity constraints for new saved records. |
| Legacy required fields | Allow source image/prompt to be absent for a new saved preview. | Preserve existing values. New saving must not require storing the original portrait or inventing the exact model prompt. Update nullable types/legacy consumers. |
| `generated_image_url` | Initially reuse its existing private data-URL storage for a bounded demo collection. | Store the generated preview once; do not copy it into appointments or notes. See capacity gate below. |
| `appointments` | Add nullable `ai_generation_id` FK to the existing generation record. | Existing appointments keep null and work normally. One booking has one selected look; a saved look may be reused for later bookings. |
| Indexes | Client/saved-date pagination; appointment look FK; stylist/date and report date/status paths as justified by query plans. | Add only indexes used by the implemented queries. |

Enforce same-client ownership when attaching a look, ideally with a compatible composite database constraint as well as API validation. The booking's selected generation is immutable through ordinary client/status updates. Saved content is immutable; regenerating creates a new reference rather than replacing a booked image.

**Retention:** Remove from Saved hides the look from the gallery but preserves any booked reference and its image. Physical deletion is not an ordinary gallery action. The assigned stylist can view the booked reference even after the client removes it from Saved; explain this in the UI. Do not change the existing account-deletion policy as an incidental part of this feature.

### Image storage and capacity gate

For the first capstone release, use the existing Neon-backed storage with explicit limits instead of relying on Render/Kaggle files or adding another provider immediately. This is a proposed demo tradeoff, not a scalable image-hosting claim.

- Save only the generated PNG/JPEG reference, with validated bytes/type/dimensions; do not persist the source photo by default.
- Proposed starting bound: 8 MiB decoded per saved image. Confirm it against real Hair, Makeup, model Nails and renderer Nails outputs before rollout; legacy image sizes are not a substitute for that test.
- Confirm remaining database capacity, set a small per-client saved-look limit and a deployment-wide storage budget before enabling saves. Limits and rejection messages must be explicit; over-limit saves must not claim success or trigger inference again.
- Account save submits the already displayed image to an authenticated endpoint. Treat submitted image/metadata as client input: derive owner from the session, validate actual image bytes, resolve style names from the feature catalog and ignore browser-supplied prices/owners. Do not fetch arbitrary image URLs. This is saving a client-selected preview, not cryptographic attestation of model provenance.
- Use a checksum plus owner/style identity or an equivalent idempotency key to make repeated Save/Book clicks return the same record. Do not deduplicate across client accounts in a way that reveals another client's data.
- Lists return metadata and protected image links, not every full data URL. Load the selected image through an authorized image endpoint with private/no-store responses.
- Verify bounded memory/concurrency on the actual Render instance. If representative images/expected volume cannot fit the reviewed budget, select private object storage before enabling the feature; do not silently omit valid generated looks or claim unbounded free storage.

A saved look must be viewable/bookable from Neon while Kaggle is stopped. An unsaved result that was never persisted cannot be recovered after its browser/backend state is lost.

## Backend/API plan

Names below are proposed new application routes, not existing endpoints.

| Route/change | Responsibility |
| --- | --- |
| `POST /api/saved-looks` | Current-client authentication; bounded image/style validation; idempotent persistence; return durable ID and safe metadata. No new inference. |
| `GET /api/saved-looks` | Owner-only paginated metadata list, optional feature filter; omit source images/full image bodies. |
| `GET /api/saved-looks/:id` | Owner-only saved-look details. |
| `PATCH /api/saved-looks/:id` | Owner-only remove/restore saved state; preserve booked image content. |
| `GET /api/saved-looks/:id/image` | Private image response; owner/admin allowed; assigned stylist allowed only through an appointment linking that exact look. Do not expose the client's whole gallery. |
| Existing appointment POST | Accept optional `lookId`; validate owner, compatible service group, stylist and service/price server-side. Persist only FK, not another image. Reject invalid references rather than silently dropping them. |
| Existing appointment GET/details | Include safe attached-look metadata/image endpoint within existing client/stylist/admin scopes. Avoid image duplication in list JSON. Add details GET if needed for the detail panel. |
| Existing appointment PATCH | Keep client changes tightly limited; staff status changes cannot swap the look. Add admin-only validated stylist assignment and recorded-price confirmation so unassigned/unquoted bookings can be managed. |
| `GET /api/admin/daily-services` | Current-admin guard; validated bounded date range/stylist/status; server-side aggregates and paginated details from appointments joined to existing user names. |
| Existing admin stats | Make completed-service monetary filters consistent between headline and service breakdown; preserve booking counts as separately labeled counts. |

Use existing role/session patterns with current database role lookup for new/touched protected operations. Include same-origin checks for browser mutations in the Render deployment, ID validation, parameterized queries, and clear 401/403/404/validation failures. Route labels/opaque IDs never grant image access by themselves.

Persisting a client-submitted preview does not require weakening the existing AI bridge, altering job ownership, replaying generation or retaining Kaggle results longer. Keep synchronous local and hosted asynchronous generation contracts unchanged.

## Booking/service integration

Use one existing service catalog. A generated style describes the intended appearance; a booking service describes salon work, so they must remain distinct fields.

- Hair look: preselect Hair Design and let the client choose an appropriate real service.
- Nails look: preselect Nail Studio and let the client choose manicure/pedicure/art as appropriate; do not assume a red preview always means a particular paid service.
- Proposed Makeup group: **Makeup**, service type `makeup`, with an initial **Makeup Application — price to be confirmed** option. This is a proposed catalog addition, not a verified current offering or invented fixed price. Obtain business approval for this label before release.
- Retain the service estimate or unknown price as such. Do not copy Consultation's demo-estimate price into a booking. A null amount displays Price to be confirmed, never free or paid.
- Validate actual catalog service/category and derive catalog pricing on the server. Admin confirmation may update the recorded amount for quoted/starting-from services; validate nonnegative amounts and preserve existing peso units rather than silently switching to centavos.
- Preserve the look across login redirects using only its authorized ID; never put photos or consultation capability tokens in URLs.
- Normal bookings without a look remain supported. Do not silently implement new slot-availability or multi-service appointment rules as part of this change.

## Daily service monitoring rules

The first release uses appointments as the source of truth, following the Supervisor's confirmation. No payment or transaction ledger is added.

- Default to today in the salon timezone, **Asia/Manila**, with a selected-date view and bounded range option.
- Group by stylist ID plus service day. Stylist names are display labels, not grouping keys. Show Unassigned, including historical cases.
- Display client, service, scheduled time, status and recorded amount in detail rows. Show separate completed/pending/confirmed/cancelled counts and an optional attached-look indicator.
- Monetary totals include **completed appointments only**, sum each appointment once, and explicitly count unpriced records rather than silently describing them as zero-value services.
- Label totals **Recorded completed-service amount**, not cash collected, profit, commissions or payment received.
- Preserve completed historical appointments without a look. Do not fabricate completion times or AI associations for old rows.
- Before implementation finalizes date SQL, verify the current stored timestamp convention against a known booking. Use one explicit timezone conversion for both filters and rendering and test midnight boundaries. Do not shift every historical timestamp based only on GMT metadata.
- Keep aggregate totals independent of pagination and avoid joins that multiply appointment rows.

## Implementation sequence after approval

1. **Persistence foundation:** finalize capacity/retention limits and date convention; additive Drizzle/SQL migration, saved-look service and ownership tests. Use a disposable database branch for mutation tests, not the live account database.
2. **Save UI:** reusable Save/Book action component for the three standalone dialogs and Consultation completed looks; client Saved Looks page/sidebar. Preserve Download, Select, Custom and status recovery. Make save errors recoverable without repeating generation.
3. **Booking + staff detail:** optional appointment FK, look-aware booking form, server catalog validation and Makeup proposed option, client/stylist/admin detail views and admin assignment/price confirmation.
4. **Daily admin view:** grouped query, Finance date/stylist UI and monetary-filter correction, with timezone and role tests.
5. **Regression and rollout:** production build/typecheck, existing AI tests, browser role flows, database migration validation and a scheduled live rehearsal. Deploy only after separate approval of the reviewed changes; do not edit notebooks/models/bundles for these features.

Use a reviewed migration, not broad schema push or reseeding. The existing seed script deletes data and currently deletes generations before appointments; it must not run against production, and fixture cleanup order must account for the new FK. Keep old app paths/data usable during rollout. New enum values need an explicit rollback strategy: retain the enum/schema additions rather than destructively dropping values or saved images. Disable new UI/endpoints if rolling the app back.

## Acceptance and regression tests

| Feature | Required evidence |
| --- | --- |
| Save a completed look | Hair, Makeup, model Nails, renderer Nails and Consultation previews can each be saved once and reopened with correct style/image. Incomplete/placeholder UI does not offer misleading saving/booking actions. |
| Persistence | Reload, logout/login and second browser/device show saved records; stopping Kaggle and restarting Render do not remove saved looks. |
| Duplicate/save failure | Double click, network response loss and repeat Book do not create duplicate looks. Save failure leaves the current result/download intact and sends no inference POST. |
| Bounds | Invalid image/type/dimensions, large uploads, quota full and malformed style are controlled; test representative real output sizes and bounded Render memory. |
| Client separation | Client A cannot list/read/book/remove Client B's looks, and cannot choose another owner or price in the request. |
| Booking linkage | Book from result or gallery uses one durable reference; normal no-look booking still works. Invalid/mismatched look/service is rejected; quoted/starting-from/unknown prices are labeled honestly. |
| Stylist access | Assigned stylist sees only the exact look on assigned booking; unrelated stylist and anonymous user cannot fetch it. Admin assignment change updates access; stale role sessions are checked. |
| Retention | Removing a saved look hides it from gallery while an existing booking's stylist can still view the immutable reference. |
| Reporting | Multiple stylists/dates/statuses, unassigned appointments, null/zero amounts, pagination and repeat loads reconcile to source appointments. Cancelled/pending values never inflate completed-service amounts. |
| Date boundaries | Asia/Manila midnight/month boundaries, a browser in another timezone and known historical bookings group consistently; no fabricated completion dates. |
| Compatibility | Legacy generation history/analytics, existing appointments/seed fixtures, auth/Origin/ownership, local synchronous and hosted asynchronous generation, 429/no-retry behavior and mobile contracts still pass. |
| Rollout | Migration on a disposable database copy preserves historical records/FKs; production Next build/typecheck and browser role walkthrough pass before deployment. |

No new feature tests or GPU generations were run during this planning-only audit, because no implementation was authorized. Existing test files were inspected; new booking/saved-look/report coverage is required rather than assuming the AI regression suite covers business workflows.

## Review boundary

Confirmed: completed-service reporting rather than payments; plan a Makeup booking option. Proposed for review: Neon-backed bounded saved images, generated-preview-only persistence, gallery remove-with-booking-retention behavior, one selected look per appointment, scheduled-service-day reporting in Asia/Manila, and the Makeup Application/price-to-be-confirmed entry. Storage limits, historical timestamp interpretation and client-device acceptance remain **Needs verification** before release.

## Source references

- `beautycore/db/schema.ts`; live Neon information-schema/enums/indexes/aggregate-only queries.
- `beautycore/app/api/appointments/route.ts` and `[id]/route.ts`.
- `beautycore/app/(public)/booking/booking-form.tsx`; `beautycore/lib/services.ts`.
- `beautycore/components/ai-studio.tsx`; all three current studio pages; `beautycore/app/client/ai-consultation/page.tsx`.
- `beautycore/lib/ai/browser-client.ts`, `studio-api.ts`, `studio-consultation-api.ts`, `adapter-core.ts`; `/api/ai/[...path]`.
- Legacy `/api/generate`, `/api/generations`, former AI-advisor redirect and Admin Market Trends.
- `beautycore/app/api/admin/stats/route.ts`; Admin Finance; stylist appointments/dashboard; client appointments/sidebar.
- `backend/app/demo_gateway.py`; `backend/app/consultation/store.py`; `backend/app/main.py`.
- `beautycore/lib/auth.ts`; `beautycore/components/ui.tsx`; `beautycore/db/seed.ts`; `render.yaml`.
- `mobile/app/result.tsx`, `consultation-result.tsx`, `settings.tsx` (compatibility boundary only).
